# SPDX-License-Identifier: MPL-2.0
"""Public receipt-only recovery of exposed, deliberately interrupted work.

Credentials, source observations and inline effects are disclosed fixtures.
No actual native acquisition or scientific qualification is claimed here.
"""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring
from empirical_lawhood.api.results import ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, InjectedSchedulerCrash, LocalScheduler
from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
from tests.execution_support import ENFORCING_TEST_EXECUTOR_CAPABILITY
from tests.runtime_platform import test_recursive_prospective_workflow as fixtures
from tests.test_issued_worker_preparation import _binding


def _census(plane):
    root = plane.root.verify(for_write=False)
    return {path.relative_to(root).as_posix(): (sha256(path.read_bytes()).hexdigest(), path.stat().st_size)
            for path in root.rglob("*") if path.is_file()}


@pytest.fixture(scope="module")
def interrupted(tmp_path_factory, request):
    patch = pytest.MonkeyPatch()
    request.addfinalizer(patch.undo)
    root = tmp_path_factory.mktemp("reconcile-public-history")
    original = fixtures.prospective_fixture

    def single_attempt(**options):
        compiled, authoring, context = original(**options)
        draft = replace(compiled.draft, operations=tuple(replace(row, maximum_attempts=1)
            for row in compiled.draft.operations))
        return replace(compiled, draft=draft), authoring, context

    patch.setattr(fixtures, "prospective_fixture", single_attempt)
    parts = list(fixtures._public_issued_handoff_fixture(root, patch))
    package = parts[5]
    package = replace(package, execution_resource_envelope_spec=replace(
        package.execution_resource_envelope_spec, allowlisted_resource_stop_reason_codes=()))
    parts[5] = package
    control = fixtures._run_public_handoff(root, issued_parts=tuple(parts), prepare_only=True)
    patch.setattr(control.service, "_check_identity", lambda *_args, **_kwargs: None)
    patch.setattr(recursive_authoring, "implementation_binding", lambda _root: _binding(package.implementation_commit))

    class InlineExecutor:
        enforcement_capability = ENFORCING_TEST_EXECUTOR_CAPABILITY
        calls = []

        def execute_deadline_free(self, runner, context, *, prepared_contract=None, **_kwargs):
            self.calls.append((context.task_id, context.attempt_id))
            if context.task_id == "develop-a":
                raise OSError("disclosed pre-terminal PURE failure")
            if prepared_contract is not None:
                context = replace(context, prepared_invocation=prepared_contract)
            return DirectTaskExecutor().execute(runner, context, timeout_seconds=60)

    executor = InlineExecutor()
    control.service.executor = executor
    stop = LocalScheduler._stop_failed_envelope_task

    def interrupt(self, task_id, **options):
        if task_id == "develop-a":
            raise InjectedSchedulerCrash("disclosed interruption after durable failed attempt")
        return stop(self, task_id, **options)

    with patch.context() as transient:
        transient.setattr(LocalScheduler, "_stop_failed_envelope_task", interrupt)
        result = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True,
            reveal_authority_id=control.reveal.authority_id))
    assert not result.succeeded
    plan, index, store = control.service._load_status_index(package.run_plan_id)
    assert store.read_terminal(index) is None
    assert [task for task, _ in executor.calls] == ["prepare", "develop-a"]
    original_catalog = (control.catalog.read_bytes(), control.catalog.stat().st_mtime_ns)
    private_catalog = root / "private-reconciled.sqlite3"

    def engine_factory():
        engine = create_catalog_engine("sqlite+pysqlite:///" + str(private_catalog))
        upgrade_catalog(engine)
        return engine

    control.service.engine_factory = engine_factory
    def forbidden(*_args, **_kwargs):
        pytest.fail("receipt-only reconciliation entered compilation, provider or execution")
    patch.setattr(control.api, "_compile_package", forbidden)
    patch.setattr(control.api, "_conditional_execution_records", forbidden)
    patch.setattr(control.service, "execute", forbidden)
    patch.setattr(control.service, "_resolve_campaign_provider", forbidden)
    return SimpleNamespace(control=control, package=package, plan=plan, index=index, store=store,
        plane=parts[3], executor=executor, original_catalog=original_catalog,
        private_catalog=private_catalog, before=_census(parts[3]))


@pytest.mark.parametrize("changes", (
    {"reconcile_only": "true"}, {"parent_input_binding_paths": ("unused",)},
))
def test_reconcile_rejects_execution_options_before_entry(interrupted, changes):
    case = interrupted
    options = dict(run_id=case.index.run_id, confirmed=True, reconcile_only=True,
        reveal_authority_id=case.control.reveal.authority_id)
    options.update(changes)
    result = case.control.api.resume_campaign(ResumeCampaignRequest(**options))
    assert not result.succeeded
    assert _census(case.plane) == case.before
    assert not case.private_catalog.exists()


def test_receipt_only_preview_has_no_execution_effects(interrupted):
    case = interrupted
    result = case.control.api.resume_campaign(ResumeCampaignRequest(case.index.run_id,
        reconcile_only=True, reveal_authority_id=case.control.reveal.authority_id))
    assert result.reason_codes == ("WRITE_CONFIRMATION_REQUIRED",)
    assert _census(case.plane) == case.before
    assert not case.private_catalog.exists()


def test_public_reconciliation_closes_actual_history_and_leaves_independent_work_unused(interrupted, monkeypatch):
    case = interrupted
    actual_validator = case.control.service._validate_issued_execution_authority
    authority_times = []

    def authenticate_stored_authority(package, *, at_utc):
        authority_times.append(at_utc)
        return actual_validator(package, at_utc=at_utc)

    monkeypatch.setattr(case.control.service, "_validate_issued_execution_authority", authenticate_stored_authority)
    request = ResumeCampaignRequest(case.index.run_id, confirmed=True, reconcile_only=True,
        reveal_authority_id=case.control.reveal.authority_id)
    result = case.control.api.resume_campaign(request)
    assert result.succeeded, (result.reason_codes, result.errors)
    assert result.reason_codes == ("FAILED_HISTORY_RECONCILED_WITHOUT_EXECUTION",)
    summary = result.payload
    assert summary.operational_status == "FAILED" and summary.assigned_task_count == 5
    assert summary.completed_task_ids == ("prepare",) and summary.failed_task_ids == ("develop-a",)
    assert summary.blocked_task_ids == ()
    assert set(summary.pending_task_ids) == {"develop-b", "freeze", "evaluate"}
    assert summary.closure_only and summary.worker_entries == 0
    assert [task for task, _ in case.executor.calls] == ["prepare", "develop-a"]
    after = _census(case.plane)
    assert all(after.get(name) == value for name, value in case.before.items())
    terminal = case.store.read_terminal(case.index)
    assert {row.task_id for row in terminal.attempts} == {"prepare", "develop-a"}
    assert (case.control.catalog.read_bytes(), case.control.catalog.stat().st_mtime_ns) == case.original_catalog
    case.private_catalog.unlink()
    repeated = case.control.api.resume_campaign(request)
    assert repeated.succeeded and repeated.payload == summary
    assert _census(case.plane) == after
    assert [task for task, _ in case.executor.calls] == ["prepare", "develop-a"]
    assert authority_times == [None, None]
