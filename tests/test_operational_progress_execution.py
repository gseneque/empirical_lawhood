# SPDX-License-Identifier: MPL-2.0
"""Operational execution progress reuses authenticated custody and task outcomes."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.api.execution import CampaignCapabilityError, CampaignExecutionService
from empirical_lawhood.infrastructure.execution import ExecutionResourceCapacity, InjectedSchedulerCrash
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.compiler import compile_run_plan, lower_run_plan
from empirical_lawhood.runtime.execution import TaskAttemptDisposition
from empirical_lawhood.runtime.progress import progress_reporting
from empirical_lawhood.runtime.providers import ExternalInputPayload
from tests.api.test_campaign_execution import PACKAGE
from tests.approval_support import approval_service_for_path
from tests.runtime_platform.conftest import build_protocol_fixture
from tests.runtime_platform.test_execution_scheduler import CrashAfterReceipt, _plane, _runner, _runtime


class CaptureProgress:
    def __init__(self):
        self.events = []

    def update(self, **event):
        self.events.append(event)

    def phase(self, name):
        return [event for event in self.events if event['phase'] == name]


@pytest.mark.parametrize('parallel', (1, 2))
def test_recovered_successes_advance_with_persisted_failures_but_not_blocked_tasks(tmp_path, parallel):
    fixture = build_protocol_fixture()
    scheduler, repository, _plane, store, runners = _runtime(
        tmp_path, fixture, failure_injector=CrashAfterReceipt('prepare'),
        runner_failures={'reference.develop-a': 2}, maximum_parallel_tasks=parallel,
        parallel_resource_capacity=ExecutionResourceCapacity(cpu_cores=2, memory_bytes=2_000_000,
            gpu_devices=0, enforced_cpu_limit=True, enforced_address_space_limit=True,
            enforced_no_network=False),
    )
    run_id = fixture.run_plan.run_plan_id
    try:
        with pytest.raises(InjectedSchedulerCrash, match='prepare'):
            scheduler.execute(run_id, fixture.execution_plan)
        attempt, = repository.attempts(run_id)
        original = store.read(run_id, attempt.task_id, attempt.attempt_id)
        assert original is not None
        original_bytes = original.canonical_bytes()
        observed = CaptureProgress()
        with progress_reporting(observed):
            result = scheduler.execute(run_id, fixture.execution_plan)
        rows = observed.phase('execution.tasks')
        assert rows[0] == {'phase': 'execution.tasks', 'done': 1, 'total': 6, 'failed': 0}
        assert [row['done'] for row in rows] == sorted(row['done'] for row in rows)
        assert rows[-1] == {'phase': 'execution.tasks', 'done': 3, 'total': 6, 'failed': 1}
        assert result.status is OperationalStatus.FAILED
        assert result.completed_task_ids == ('develop-b', 'prepare')
        assert result.failed_task_ids == ('develop-a',)
        assert result.blocked_task_ids == ('evaluate', 'freeze', 'report')
        failed_attempts = [a for a in repository.attempts(run_id)
                           if a.disposition is TaskAttemptDisposition.FAILED]
        assert len(failed_attempts) == 2 and {a.task_id for a in failed_attempts} == {'develop-a'}
        assert len(_runner(runners, 'reference.prepare').contexts) == 1
        assert store.read(run_id, attempt.task_id, attempt.attempt_id).canonical_bytes() == original_bytes
        calls = [len(runner.contexts) for runner in runners]
        terminal = CaptureProgress()
        with progress_reporting(terminal):
            replayed = scheduler.execute(run_id, fixture.execution_plan)
        assert replayed == result and [len(runner.contexts) for runner in runners] == calls
        assert terminal.phase('execution.tasks') == [rows[-1]]
    finally:
        repository.engine.dispose()


def test_failing_progress_callback_preserves_success_and_exact_terminal_receipts(tmp_path):
    class BrokenProgress:
        def update(self, **_event):
            raise OSError('advisory callback unavailable')

    fixture = build_protocol_fixture()
    scheduler, repository, _plane, _store, runners = _runtime(tmp_path, fixture)
    try:
        with progress_reporting(BrokenProgress()):
            result = scheduler.execute(fixture.run_plan.run_plan_id, fixture.execution_plan)
        assert result.status is OperationalStatus.SUCCEEDED
        before = {path.relative_to(tmp_path): path.read_bytes()
                  for path in tmp_path.glob(f'runs/{result.run_id}/receipts/**/*.json')}
        completed = CaptureProgress()
        with progress_reporting(completed):
            assert scheduler.execute(result.run_id, fixture.execution_plan) == result
        assert completed.phase('execution.tasks') == [
            {'phase': 'execution.tasks', 'done': 6, 'total': 6, 'failed': 0}]
        assert all(len(runner.contexts) == 1 for runner in runners)
        assert before == {path.relative_to(tmp_path): path.read_bytes()
                          for path in tmp_path.glob(f'runs/{result.run_id}/receipts/**/*.json')}
    finally:
        repository.engine.dispose()


def test_persistence_preamble_counts_preserve_input_and_plan_bytes(tmp_path):
    from empirical_lawhood.api import load_authoring

    # Exercise the owning finite persistence methods below full run admission.
    # No public/source-conformance or execution-authority claim is made here.
    external = tmp_path / 'external'
    external.mkdir()
    package = load_authoring(PACKAGE)
    run_plan = compile_run_plan(run_plan_id=package.run_plan_id, campaign=package.campaign,
        system=package.system, experiment=package.experiment, frozen_proposal=package.frozen_proposal,
        authorization=package.authorization, template=package.protocol, registry=package.registry,
        implementation_commit=package.implementation_commit, approval_service=approval_service_for_path(PACKAGE),
        model_set=package.model_set)
    execution_plan = lower_run_plan(run_plan, package.registry)
    service = SimpleNamespace(artifact_plane=_plane(external),
        _package_lineage_parents=CampaignExecutionService._package_lineage_parents,
        _most_restrictive_access=CampaignExecutionService._most_restrictive_access)

    def persist():
        CampaignExecutionService._persist_plans(service, package, run_plan, execution_plan,
            package_name='campaign-package', source_plan_name='run-plan', minimum_free_bytes=0)
        values = tuple(ExternalInputPayload.from_bytes(logical_artifact_id='progress.' + name,
            payload_schema='empirical-lawhood/testing/progress-input', profile=ArtifactProfile.TEXT_PARAMETERS,
            media_type='text/plain', payload=name.encode(), visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND, parent_visibility_ceilings=(), lineage_parents=())
            for name in ('first', 'second'))
        return CampaignExecutionService._persist_provider_inputs(service, run_plan.run_plan_id,
            values, minimum_free_bytes=0)

    ordinary = persist()
    before = {path.relative_to(external): path.read_bytes() for path in external.rglob('*') if path.is_file()}
    observed = CaptureProgress()
    with progress_reporting(observed):
        result = persist()
    assert result == ordinary
    assert before == {path.relative_to(external): path.read_bytes() for path in external.rglob('*') if path.is_file()}
    assert not list(tmp_path.rglob('*.sqlite3'))
    validation = observed.phase('execution.plan-validation')
    assert [row['done'] for row in validation] == [0, 1, 2]
    assert all(row['total'] == 2 for row in validation)
    for phase in ('execution.plan-publication', 'execution.inputs'):
        rows = observed.phase(phase)
        total = rows[0]['total']
        assert [row['done'] for row in rows] == list(range(total + 1))
        assert all(row['total'] == total and row['failed'] == 0 for row in rows)
    plan_files = [path for path in external.glob('runs/*/plans/*.json')
                  if not path.name.endswith('.manifest.json')]
    assert observed.phase('execution.plan-publication')[-1]['total'] == len(plan_files)
    assert observed.phase('execution.inputs')[-1]['total'] == len(list(external.glob('runs/*/inputs/**/*.bin')))


def test_provider_progress_does_not_advance_before_existing_identity_guard(tmp_path):
    class ChangedInputWriter:
        root = _plane(tmp_path).root

        def write_stream(self, request):
            return SimpleNamespace(
                logical=SimpleNamespace(logical_artifact_id=request.logical_artifact_id),
                materialization=SimpleNamespace(logical_artifact_id=request.logical_artifact_id,
                    relative_path=request.relative_path, size_bytes=1, physical_sha256='0' * 64))

    payload = ExternalInputPayload.from_bytes(logical_artifact_id='progress.input',
        payload_schema='empirical-lawhood/testing/progress-input', profile=ArtifactProfile.TEXT_PARAMETERS,
        media_type='text/plain', payload=b'x', visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.OUTCOME_BLIND, parent_visibility_ceilings=(), lineage_parents=())
    service = SimpleNamespace(artifact_plane=ChangedInputWriter())
    observed = CaptureProgress()
    with progress_reporting(observed), pytest.raises(CampaignCapabilityError, match='identity changed'):
        CampaignExecutionService._persist_provider_inputs(service, 'run.progress', (payload,), minimum_free_bytes=0)
    assert observed.phase('execution.inputs') == [
        {'phase': 'execution.inputs', 'done': 0, 'total': 1, 'failed': 0}]
