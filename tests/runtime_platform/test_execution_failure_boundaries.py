"""Current scheduler error classification, diagnostics and admitted worker drain."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import threading
import pytest
from empirical_lawhood.infrastructure import execution as sdk
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.execution import OperationalFailureClass, RunnerRegistry, RunnerResult, TaskAttemptDisposition, TaskBlockReason
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, WorkerPreflightMismatch, WorkerPreflightResult
from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic
from tests.runtime_platform.test_execution_scheduler import _runtime

@pytest.mark.parametrize('name', ('SchedulerConsistencyError', 'LiveLeaseError', 'InjectedSchedulerCrash', 'ResourceLockUnavailable', 'TaskProcessError', 'ResourceAdmissionError', 'WorkerPreflightError', 'ProgressStalledError', 'CampaignElapsedBoundaryReached'))
def test_closed_error_families_use_actual_classes(name):
    assert sdk.execution_error_types(name) == (getattr(sdk, name),)

def test_error_family_and_child_diagnostic_do_not_trust_names_or_messages():
    with pytest.raises(ValueError, match='closed SDK contract'):
        sdk.execution_error_types('RuntimeError')
    forged = type('ResourceAdmissionError', (RuntimeError,), {})
    assert sdk.operational_failure_diagnostic(forged('PRIVATE')).failure_class is OperationalFailureClass.PROVIDER_RUNNER_DEFECT
    for owner in (sdk,):
        error = owner.TaskProcessError('PRIVATE', child_exception_type='ValueError', child_message='PRIVATE scientific outcome: 42')
        diagnostic = sdk.operational_failure_diagnostic(error)
        assert diagnostic.failure_class is OperationalFailureClass.CHILD_PROCESS_FAILURE
        assert diagnostic.sanitized_exception_type == 'ValueError'
        assert diagnostic.sanitized_message == 'child process rejected a value'
        assert b'PRIVATE' not in diagnostic.canonical_bytes()
        assert diagnostic.scientific_evidence is False
        assert sdk.operational_failure_diagnostic(owner.ResourceAdmissionError('PRIVATE')).failure_class is OperationalFailureClass.RESOURCE_REFUSAL

@pytest.mark.parametrize('name,expected', (('SchedulerConsistencyError', 'CampaignValidationError'), ('LiveLeaseError', 'CampaignConcurrencyError'), ('ResourceAdmissionError', 'CampaignPrerequisiteError'), ('TaskProcessError', 'CampaignTaskError')))
def test_api_boundary_classifies_actual_errors(monkeypatch, name, expected):
    from empirical_lawhood.api import execution as api
    monkeypatch.setattr(api, 'execution_error_types', sdk.execution_error_types)
    service = object.__new__(api.CampaignExecutionService)
    error = getattr(sdk, name)('PRIVATE')

    def refuse(*_args, **_kwargs):
        raise error
    service._check_identity = refuse
    with pytest.raises(getattr(api, expected)) as caught:
        service.execute(package=None, run_plan=None, execution_plan=None)
    assert caught.value.__cause__ is error
    assert 'PRIVATE' not in str(caught.value)

def test_api_boundary_does_not_treat_named_runtime_error_as_sdk_error(monkeypatch):
    from empirical_lawhood.api import execution as api
    monkeypatch.setattr(api, 'execution_error_types', sdk.execution_error_types)
    service = object.__new__(api.CampaignExecutionService)
    error = type('TaskProcessError', (RuntimeError,), {})('PRIVATE')

    def refuse(*_args, **_kwargs):
        raise error
    service._check_identity = refuse
    with pytest.raises(api.CampaignInternalError):
        service.execute(package=None, run_plan=None, execution_plan=None)

class FailingChildRunner:

    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, _context):
        raise ValueError('PRIVATE scientific detail')

class RecordingProcessExecutor:

    def __init__(self, root):
        self.delegate = sdk.LocalProcessExecutor(scratch_root=root)
        self.observed_error = None

    def execute(self, *args, **kwargs):
        try:
            return self.delegate.execute(*args, **kwargs)
        except sdk.TaskProcessError as error:
            self.observed_error = error
            raise

def test_actual_sdk_child_failure_keeps_typed_cause_through_scheduler(tmp_path, protocol_fixture):
    fixture = _fixture(protocol_fixture, count=1)
    task, = fixture.execution_plan.tasks
    task = replace(task, capability=replace(task.capability, requested_resources=replace(task.capability.requested_resources, wall_time_seconds=60, memory_bytes=4 * 1024 ** 3)))
    registry = replace(fixture.registry, capabilities=tuple((replace(row, resource_ceiling=replace(row.resource_ceiling, wall_time_seconds=60, memory_bytes=4 * 1024 ** 3)) for row in fixture.registry.capabilities)))
    fixture = replace(fixture, registry=registry, execution_plan=replace(fixture.execution_plan, registry_sha256=registry.fingerprint(), tasks=(task,)))
    scheduler, repository, plane, _, _ = _scheduler(tmp_path, fixture, sdk.DirectTaskExecutor(), 1)
    executor = RecordingProcessExecutor(plane.root)
    scheduler.executor = executor
    scheduler.runner_registry = RunnerRegistry(tuple((FailingChildRunner(row) for row in fixture.registry.capabilities)), registry_sha256=fixture.registry.fingerprint())
    try:
        result = scheduler.execute(fixture.run_plan.run_plan_id, fixture.execution_plan)
        assert result.status is OperationalStatus.FAILED
        assert type(executor.observed_error) is sdk.TaskProcessError
        candidate, = scheduler.recovery_index.tasks[0].attempts
        event = scheduler.recovery_store.read_event(scheduler.recovery_index, candidate.event_relative_path)
        assert event.failure.sanitized_exception_type == 'ValueError'
        assert event.failure.sanitized_message == 'child process rejected a value'
        assert b'PRIVATE' not in event.canonical_bytes()
    finally:
        repository.engine.dispose()

def _fixture(protocol_fixture, count=12):
    template = next((row for row in protocol_fixture.execution_plan.tasks if row.task_id == 'prepare'))
    run_id = protocol_fixture.run_plan.run_plan_id
    tasks = tuple((replace(template, task_id='failure-control.' + str(index).zfill(4), maximum_attempts=1, dependency_task_ids=(), resource_lock_ids=(), outputs=tuple((replace(output, output_id=output.output_id + '.' + str(index), logical_artifact_id=output.logical_artifact_id + '.' + str(index), relative_path=f'runs/{run_id}/outputs/failure-control.{index}/{output.output_id}.json') for output in template.outputs))) for index in range(count)))
    plan = replace(protocol_fixture.execution_plan, tasks=tasks)
    return replace(protocol_fixture, execution_plan=plan)

def _scheduler(path, fixture, executor, workers, *, native=False):
    scheduler, repository, plane, receipts, runners = _runtime(path, fixture, executor=executor, maximum_parallel_tasks=workers, parallel_resource_capacity=sdk.ExecutionResourceCapacity(workers, 4000000, 0, True, True, False) if workers > 1 else None)
    if native:
        scheduler.native_effect_capability_keys = (fixture.execution_plan.tasks[0].capability.capability_key,)
        scheduler.native_effect_contact_store = ExternalNativeEffectContactStore(plane=plane, execution_plan=ObjectIdentity.from_record(fixture.execution_plan.execution_plan_id, fixture.execution_plan), visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    return (scheduler, repository, plane, receipts, runners)

class SdkFailureExecutor:

    def __init__(self, first_wave, *, preflight=False):
        self.first_wave, self.preflight = (first_wave, preflight)
        self.ready = threading.Barrier(len(first_wave))
        self.release = threading.Event()
        self.calls = []

    def execute(self, runner, context, *, timeout_seconds, **_kwargs):
        self.calls.append(context.task_id)
        if context.task_id in self.first_wave:
            self.ready.wait(timeout=20)
        if context.task_id == self.first_wave[0]:
            if self.preflight:
                result = WorkerPreflightResult(ObjectIdentity('prepared.' + context.attempt_id, PreparedInvocationContract.SCHEMA, PreparedInvocationContract.VERSION, 'a' * 64), None, None, (WorkerPreflightMismatch('sdk.missing-operand', 'PRIVATE scientific detail'),))
                raise sdk.WorkerPreflightError(result)
            raise sdk.TaskProcessError('PRIVATE', child_exception_type='ValueError', child_message='PRIVATE 42')
        if context.task_id in self.first_wave:
            assert self.release.wait(timeout=20), 'admitted sibling was not drained'
        return sdk.DirectTaskExecutor().execute(runner, context, timeout_seconds=timeout_seconds)

@pytest.mark.parametrize('workers', (1, 4))
@pytest.mark.parametrize('diagnostic_storage', ('available', 'refused'))
def test_native_failure_retains_cause_and_admitted_workers_drain(tmp_path, protocol_fixture, caplog, workers, diagnostic_storage):
    owner = sdk
    fixture = _fixture(protocol_fixture)
    first_wave = tuple((row.task_id for row in fixture.execution_plan.tasks[:workers]))
    executor = SdkFailureExecutor(first_wave)
    scheduler, repository, plane, receipts, _ = _scheduler(tmp_path, fixture, executor, workers, native=True)
    if diagnostic_storage == 'refused':

        def refuse_diagnostic(*_args, **_kwargs):
            raise OSError('PRIVATE disk detail')
        scheduler.recovery_store.record_native_failure_diagnostic = refuse_diagnostic
    original_block = scheduler._block_native_failure

    def block(*args, **kwargs):
        try:
            return original_block(*args, **kwargs)
        finally:
            executor.release.set()
    scheduler._block_native_failure = block
    run_id = fixture.run_plan.run_plan_id
    try:
        if diagnostic_storage == 'refused':
            reason = 'native failure diagnostic could not be retained' if diagnostic_storage == 'refused' else 'native closeout failed'
            with pytest.raises(owner.SchedulerConsistencyError, match=reason):
                scheduler.execute(run_id, fixture.execution_plan)
            expected = set(first_wave)
            assert scheduler.recovery_store.read_terminal(scheduler.recovery_index) is None
        else:
            result = scheduler.execute(run_id, fixture.execution_plan)
            expected = {row.task_id for row in fixture.execution_plan.tasks}
            assert result.status is OperationalStatus.BLOCKED
        attempts = repository.attempts(run_id)
        assert {row.task_id for row in attempts} == expected == set(executor.calls)
        assert all((row.disposition is not TaskAttemptDisposition.RUNNING for row in attempts))
        failed, = (row for row in attempts if row.task_id == first_wave[0])
        assert failed.reason_code == TaskBlockReason.UNKNOWN_COMPLETION.value
        successful = [row for row in attempts if row.disposition is TaskAttemptDisposition.SUCCEEDED]
        assert len(successful) == len(expected) - 1
        for row in successful:
            assert receipts.read(run_id, row.task_id, row.attempt_id) is not None
        candidate, = scheduler.recovery_index.task(failed.task_id).attempts
        event = scheduler.recovery_store.read_event(scheduler.recovery_index, candidate.event_relative_path)
        assert event.failure == owner.operational_failure_diagnostic(owner.SchedulerConsistencyError('native contact has uncertain completion'), failure_class=OperationalFailureClass.RECOVERY_OBSTRUCTION)
        assert event.failure.diagnostic_sha256 == '68c43e09deb127ab9df4608db52b6ebfc67259c4f77a7e0d4d598497ec70f2e6'
        paths = tuple(tmp_path.rglob('*.native-failure-diagnostic.json'))
        if diagnostic_storage == 'refused':
            assert paths == ()
        else:
            assert len(paths) == 1
            diagnostic = decode_canonical_bytes(paths[0].read_bytes(), OperationalFailureDiagnostic, maximum_bytes=plane.custody_limits.recovery_event_bytes)
            assert diagnostic.sanitized_exception_type == 'ValueError'
            assert diagnostic.failure_class is OperationalFailureClass.CHILD_PROCESS_FAILURE
            assert diagnostic.scientific_evidence is False
            assert b'PRIVATE' not in paths[0].read_bytes()
            manifest = decode_artifact_manifest(Path(str(paths[0]) + '.manifest.json').read_bytes())
            assert manifest.logical.content_sha256 == diagnostic.fingerprint()
            assert manifest.logical.outcome_access == fixture.execution_plan.tasks[0].capability.requested_outcome_access
            assert any((row.identity.object_schema == 'empirical-lawhood/runtime/native-effect-contact' for row in manifest.logical.lineage_parents))
        assert 'PRIVATE' not in caplog.text
    finally:
        repository.engine.dispose()

def test_sdk_preflight_refusal_is_retained_by_scheduler_and_stops_dispatch(tmp_path, protocol_fixture, caplog):
    fixture = _fixture(protocol_fixture)
    first_wave = tuple((row.task_id for row in fixture.execution_plan.tasks[:4]))
    executor = SdkFailureExecutor(first_wave, preflight=True)
    scheduler, repository, _, _, _ = _scheduler(tmp_path, fixture, executor, 4)
    original_stop = scheduler._stop_refused_worker_dispatch

    def stop(error):
        original_stop(error)
        executor.release.set()
    scheduler._stop_refused_worker_dispatch = stop
    try:
        result = scheduler.execute(fixture.run_plan.run_plan_id, fixture.execution_plan)
        assert result.status is OperationalStatus.BLOCKED
        assert set(executor.calls) == set(first_wave)
        assert len(result.receipts) == 3
        refused, = (row for row in repository.attempts(result.run_id) if row.task_id == first_wave[0])
        token = sha256(refused.attempt_id.encode()).hexdigest()
        path = tmp_path / f'runs/{result.run_id}/recovery/{scheduler.recovery_index.wave_id}/preflight/{token}.json'
        record = decode_canonical_bytes(path.read_bytes(), WorkerPreflightResult, maximum_bytes=None)
        assert record.mismatches[0].operand_id == 'sdk.missing-operand'
        assert 'PRIVATE' not in caplog.text
    finally:
        repository.engine.dispose()

class NegativeResultExecutor:

    def execute(self, runner, context, *, timeout_seconds, **_kwargs):
        result = sdk.DirectTaskExecutor().execute(runner, context, timeout_seconds=timeout_seconds)
        outputs = []
        for output in result.outputs:
            value = json.loads(output.payload)
            value = {key: tuple(item) if isinstance(item, list) else item for key, item in value.items()}
            value.update(scientific_disposition='OPPOSED', scientific_qualification='NOT_ESTABLISHED')
            outputs.append(replace(output, payload=canonical_json_bytes(value)))
        return RunnerResult(tuple(outputs), result.checks)

def test_negative_scientific_products_do_not_stop_dispatch(tmp_path, protocol_fixture):
    fixture = _fixture(protocol_fixture)
    scheduler, repository, _, _, _ = _scheduler(tmp_path, fixture, NegativeResultExecutor(), 4, native=True)
    try:
        result = scheduler.execute(fixture.run_plan.run_plan_id, fixture.execution_plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert len(result.receipts) == len(fixture.execution_plan.tasks)
        assert not tuple(tmp_path.rglob('*.native-failure-diagnostic.json'))
    finally:
        repository.engine.dispose()
