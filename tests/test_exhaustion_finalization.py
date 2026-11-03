# SPDX-License-Identifier: MPL-2.0
"""Real scheduler/journal/custody controls with a named software runner double.

No public API, actual worker, native operation, science or genuine authority is
entered. The retained generic output and failure are exposed software fixtures.
"""

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from itertools import count
from pathlib import Path
from threading import RLock
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, FilesystemState, GuardedExternalRoot
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict, ArtifactInputLimitExceeded
from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator, ExecutionResourceCapacity, LocalScheduler, ProgressStalledError, ResourceAdmissionError, SchedulerConsistencyError
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ExternalRootContract, ReceiptCheck
from empirical_lawhood.runtime.execution import OperationalFailureClass, RunnerResult, TaskAttemptDisposition, TaskOutputPayload
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceEnvelopeState, ExecutionResourceTaskCellSpec, NonTimeResourceBudget, ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, CandidateExecutionPlan, ExecutionPlan, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.recovery import RunRecoveryIndex, TaskRecoveryDisposition


SCHEMA = "empirical-lawhood/testing/exhaustion-output"


def _identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _files(root):
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()}


class _Inspector:
    def __init__(self, path):
        self.path = path.resolve()

    def inspect(self, _contract):
        return FilesystemState(str(self.path), True, True, 100_000_000, False)


class _EventClock:
    def __init__(self):
        self.sequence = count()

    def now_utc(self):
        return (datetime(2026, 10, 16, tzinfo=UTC) + timedelta(seconds=2 * next(self.sequence))).isoformat().replace("+00:00", "Z")


def _runtime(tmp_path, monkeypatch, *, parallel, stop_codes, error, with_dependent=True,
        retry_codes=("WORKER_PROGRESS_STALLED",)):
    candidate = decode_canonical_bytes((Path(__file__).parent / "fixtures/authoring-execution-plan.json").read_bytes(),
        CandidateExecutionPlan, maximum_bytes=1024**2)
    template = next(task for task in candidate.tasks if not task.dependency_task_ids)
    requirement = replace(template.capability, required_input_schema_ids=(), required_output_schema_ids=(SCHEMA,),
        required_permissions=(), requested_outcome_access=OutcomeAccess.OUTCOME_BLIND,
        requested_resources=ResourceBudget(cpu_cores=1, memory_bytes=1024, gpu_devices=0,
            wall_time_seconds=10, source_scan_bytes=1024, output_bytes=1024))
    tasks = []
    task_names = ("task.prefix", "task.failure", "task.blocked") if with_dependent else ("task.prefix", "task.failure")
    for name in task_names:
        output = ArtifactOutputSpec("output." + name, "artifact." + name,
            (("outside-run/" if error is None and name == "task.failure" else
                "runs/" + candidate.source_plan.object_id + "/outputs/") + name + "/value.json"), SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        prior = None if not tasks else tasks[-1]
        edge = () if prior is None else (ScientificInputSpec("edge." + name, "input." + name,
            ScientificInputRole.PARENT_RECEIPT, prior.task_id, prior.outputs[0].output_id, None,
            prior.outputs[0].logical_artifact_id, prior.outputs[0].logical_artifact_id, SCHEMA,
            "application/json", 1024, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BarrierKind.NONE),)
        tasks.append(replace(template, task_id=name, stage=ScientificStage.DEVELOP, capability=requirement,
            dependency_task_ids=() if prior is None else (prior.task_id,), external_inputs=(), outputs=(output,),
            resource_lock_ids=(), barrier=BarrierKind.NONE, maximum_attempts=1,
            obligation_ids=("obligation.software",), scientific_inputs=edge))
    tasks.sort(key=lambda task: task.task_id)
    extension = ObjectIdentity("extensions.software.exhaustion", "empirical-lawhood/runtime/issued-extension-set", "1.0.0", "a" * 64)
    liveness = ProgressLivenessContract("progress.software", ProgressHeartbeat.SCHEMA, "software-work", Decimal(1), True, True)
    cells = tuple(ExecutionResourceTaskCellSpec("cell." + task.task_id, task.task_id, "child.software", None,
        None, 1, 0, 0, False, NonTimeResourceBudget("budget." + task.task_id, 1, 1024, 1024, 0, 1024),
        liveness, None, None) for task in tasks)
    spec = ExecutionResourceEnvelopeSpec("resources.software.exhaustion", extension, cells,
        (ChildResourceTokenLimit("child.software", 0, 0),), (), retry_codes, stop_codes,
        None, None, parallel, 4096, (), (), "b" * 64, True, True, True, True)
    plan = ExecutionPlan(**({row.name: getattr(candidate, row.name) for row in fields(candidate)} | {"tasks": tuple(tasks)}),
        issued_extension_set=extension, execution_resource_envelope_spec=_identity(spec, "envelope_spec_id"),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    index = RunRecoveryIndex.from_execution_plan(plan, run_id=plan.source_plan.object_id,
        wave_id="wave.software.exhaustion", authority_identities=(extension,))
    root = tmp_path / "guarded"
    root.mkdir()
    contract = ExternalRootContract("storage.software.exhaustion", "Software fixture", str(root.resolve()),
        str(root.resolve()), "empirical-lawhood/testing/exhaustion-mount", 1)
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract, _Inspector(root)))
    recovery = ExternalRunRecoveryStore(plane)
    receipt_store = ExternalTaskReceiptStore(plane)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(ExternalExecutionResourceEnvelopeStore(plane.root))
    envelope_id = "run-resource-envelope." + index.run_id
    coordinator.initialize(envelope_id=envelope_id, spec=spec, execution_plan=_identity(plan, "execution_plan_id"),
        jit_graph_signature_manifest=None)
    engines = []
    def repository(name):
        engine = create_catalog_engine("sqlite+pysqlite:///" + str(tmp_path / name))
        engines.append(engine)
        upgrade_catalog(engine)
        return SQLiteOperationalRepository(engine)
    registry = SimpleNamespace(registry_sha256=plan.registry_sha256, resolve=lambda _task: object())
    scheduler = LocalScheduler(operational_repository=repository("catalog.sqlite3"), artifact_writer=plane,
        receipt_store=receipt_store, recovery_index=index, recovery_store=recovery, runner_registry=registry,
        implementation_commit=plan.implementation_commit, input_port_factory=plane, executor=object(),
        maximum_parallel_tasks=parallel, parallel_resource_capacity=(None if parallel == 1 else
            ExecutionResourceCapacity(2, 4096, 0, True, True, False)),
        execution_resource_envelope_coordinator=coordinator, execution_resource_envelope_id=envelope_id,
        execution_envelope_event_clock=_EventClock())
    state = SimpleNamespace(plan=plan, index=index, spec=spec, scheduler=scheduler, coordinator=coordinator,
        recovery=recovery, receipt_store=receipt_store, root=root, engines=engines, repository=repository, calls=[])
    def software_runner(_run, task, _attempt, *_inputs, **_execution_context):
        state.calls.append(task.task_id)
        if task.task_id == "task.failure":
            state.before_failure = _files(root)
            state.resource_prefix = coordinator.current(envelope_id).events
            if error is not None:
                raise error("disclosed software failure")
        return RunnerResult(tuple(TaskOutputPayload(output.output_id,
            canonical_json_bytes({"schema": SCHEMA, "version": "1.0.0", "value": {"software_only": True}}))
            for output in task.outputs), (ReceiptCheck("software.fixture", True, ()),))
    monkeypatch.setattr(scheduler, "_execute_runner", software_runner)
    return state


@pytest.mark.parametrize("parallel", (1, 2), ids=("serial", "parallel"))
@pytest.mark.parametrize("error", (OSError, ProgressStalledError), ids=("operation-failure", "stalled"))
@pytest.mark.parametrize("stop_codes", ((), ("RETRY_BUDGET_EXHAUSTED",), ("RETRY_EXHAUSTION",)),
    ids=("no-stop-declared", "budget-stop", "diagnostic-stop"))
@pytest.mark.parametrize("retry_codes", ((), ("WORKER_PROGRESS_STALLED",)), ids=("no-retry", "allowlisted-retry"))
def test_exhaustion_retains_failed_terminal_and_replays_without_entry(
    tmp_path, monkeypatch, parallel, error, stop_codes, retry_codes,
):
    case = _runtime(tmp_path, monkeypatch, parallel=parallel, stop_codes=stop_codes, error=error,
        retry_codes=retry_codes)
    try:
        result = case.scheduler.execute(case.index.run_id, case.plan)
        assert result.status is OperationalStatus.FAILED
        assert result.completed_task_ids == ("task.prefix",)
        assert result.failed_task_ids == ("task.failure",)
        assert result.blocked_task_ids == ("task.blocked",)
        assert case.calls == ["task.prefix", "task.failure"]
        failure_task = case.index.task("task.failure")
        event = case.recovery.read_event(case.index, failure_task.attempts[0].event_relative_path)
        assert event.disposition is TaskRecoveryDisposition.FAILED
        assert event.reason_codes == ("retry-exhaustion",)
        assert event.failure.failure_class is OperationalFailureClass.RETRY_EXHAUSTION
        assert event.failure.scientific_evidence is False
        terminal = case.recovery.read_terminal(case.index)
        assert terminal.operational_status == "FAILED"
        assert next(row for row in terminal.attempts if row.task_id == "task.failure").reason_code == "retry-exhaustion"
        envelope = case.coordinator.load(case.scheduler.execution_resource_envelope_id)
        assert envelope.events[:len(case.resource_prefix)] == case.resource_prefix
        actual = _files(case.root)
        assert all(actual[path] == digest for path, digest in case.before_failure.items()
            if not path.startswith("operational/execution-resource-envelopes/"))
        events = tuple(row for row in envelope.events if row.cell_id == "cell.task.failure")
        assert [row.kind.value for row in events] == ["RESERVATION", "LAUNCH",
            "OPERATIONAL_FAILURE" if error is OSError else "PROGRESS_STALLED", *(["RESOURCE_STOP"] if stop_codes else [])]
        observation = events[2]
        assert observation.valid_receipt is False
        assert observation.scientific_terminal is False
        assert observation.reason_code == ("RETRY_EXHAUSTION" if error is OSError else "WORKER_PROGRESS_STALLED")
        assert envelope.cell("cell.task.failure").first_valid_receipt is None
        assert envelope.cell("cell.task.failure").state is (ExecutionResourceEnvelopeState.RESOURCE_STOP
            if stop_codes else ExecutionResourceEnvelopeState.RECEIPT_OBSERVED)
        if stop_codes:
            assert events[-1].reason_code == stop_codes[0]
        elif error is ProgressStalledError:
            before_retry = _files(case.root)
            refusal = "maximum attempts are exhausted" if retry_codes else "retry is not allowlisted"
            with pytest.raises(ValueError, match=refusal):
                case.coordinator.reserve(envelope_id=case.scheduler.execution_resource_envelope_id,
                    event_id="exposed.forbidden-retry", occurred_at_utc=case.scheduler.execution_envelope_event_clock.now_utc(),
                    cell_id="cell.task.failure", attempt_id="exposed.attempt.second",
                    retry_reason_code="WORKER_PROGRESS_STALLED")
            assert case.coordinator.load(case.scheduler.execution_resource_envelope_id) == envelope
            assert _files(case.root) == before_retry
        # Real terminal/index/receipt/journal reconstruction into an empty catalog.
        # No new attempt or worker can make this replay succeed.
        before_replay = _files(case.root)
        case.scheduler.operational_repository = case.repository("rebuilt.sqlite3")
        monkeypatch.setattr(case.scheduler, "_execute_runner", lambda *_args: pytest.fail("terminal replay entered a worker"))
        replay = case.scheduler.execute(case.index.run_id, case.plan)
        assert replay == result
        assert _files(case.root) == before_replay
        assert tuple(row.disposition for row in case.scheduler.operational_repository.attempts(case.index.run_id)
            if row.task_id == "task.failure") == (TaskAttemptDisposition.FAILED,)
    finally:
        for engine in case.engines:
            engine.dispose()


def test_undeclared_general_stop_stays_strict_and_unrelated_code_is_not_selected(tmp_path, monkeypatch):
    case = _runtime(tmp_path, monkeypatch, parallel=1, stop_codes=("OTHER_DECLARED_STOP",), error=OSError)
    try:
        assert case.scheduler.execute(case.index.run_id, case.plan).status is OperationalStatus.FAILED
        before = _files(case.root)
        with pytest.raises(ValueError, match="resource stop reason is not predeclared"):
            case.scheduler._stop_envelope_task("task.failure", reason_code="RETRY_EXHAUSTION")
        assert _files(case.root) == before
        assert case.coordinator.current(case.scheduler.execution_resource_envelope_id).cell("cell.task.failure").state is ExecutionResourceEnvelopeState.RECEIPT_OBSERVED
    finally:
        for engine in case.engines:
            engine.dispose()


@pytest.mark.parametrize("reason", ("RETRY_EXHAUSTION", "RETRY_BUDGET_EXHAUSTED"))
def test_legacy_exhaustion_keeps_exact_original_reason(reason):
    calls = []
    scheduler = object.__new__(LocalScheduler)
    scheduler.execution_resource_envelope_coordinator = None
    scheduler.execution_resource_envelope_id = None
    scheduler._stop_envelope_task = lambda task_id, **values: calls.append((task_id, values))
    scheduler._stop_failed_envelope_task("task.software",
        failure_class=OperationalFailureClass.RETRY_EXHAUSTION, reason_code=reason)
    assert calls == [("task.software", {"reason_code": reason})]


@pytest.mark.parametrize("reason", ("RETRY_EXHAUSTION", "RETRY_BUDGET_EXHAUSTED"))
def test_exhaustion_helper_prefers_exact_declared_spelling(reason):
    calls = []
    scheduler = object.__new__(LocalScheduler)
    scheduler.execution_resource_envelope_coordinator = SimpleNamespace(current=lambda _identity:
        SimpleNamespace(spec=SimpleNamespace(allowlisted_resource_stop_reason_codes=(
            "RETRY_BUDGET_EXHAUSTED", "RETRY_EXHAUSTION"))))
    scheduler.execution_resource_envelope_id = "envelope.software"
    scheduler._resource_envelope_transition_lock = RLock()
    scheduler._stop_envelope_task = lambda task_id, **values: calls.append((task_id, values))
    scheduler._stop_failed_envelope_task("task.software",
        failure_class=OperationalFailureClass.RETRY_EXHAUSTION, reason_code=reason)
    assert calls == [("task.software", {"reason_code": reason})]


def test_exhaustion_helper_refuses_nonexhaustion_reason_before_any_stop():
    scheduler = object.__new__(LocalScheduler)
    scheduler._stop_envelope_task = lambda *_args, **_values: pytest.fail("non-exhaustion mapped to resource stop")
    with pytest.raises(SchedulerConsistencyError, match="differs from its failure class"):
        scheduler._stop_failed_envelope_task("task.software",
            failure_class=OperationalFailureClass.RETRY_EXHAUSTION, reason_code="OTHER_DECLARED_STOP")


@pytest.mark.parametrize("parallel", (1, 2), ids=("serial", "parallel"))
@pytest.mark.parametrize("error,failure_class", (
    (None, OperationalFailureClass.PROVIDER_RUNNER_DEFECT),
    (SchedulerConsistencyError, OperationalFailureClass.CONTRACT_REFUSAL),
    (ResourceAdmissionError, OperationalFailureClass.RESOURCE_REFUSAL),
    (ArtifactInputLimitExceeded, OperationalFailureClass.RESOURCE_REFUSAL),
), ids=("guarded-publication-defect", "contract-refusal", "resource-refusal", "input-limit"))
@pytest.mark.parametrize("stop_kind", ("none", "applicable", "unrelated"))
def test_failure_retains_cause_terminal_and_replays_without_entry(
    tmp_path, monkeypatch, parallel, error, failure_class, stop_kind,
):
    stop_codes = {"none": (), "applicable": (failure_class.value,),
        "unrelated": ("OTHER_DECLARED_STOP",)}[stop_kind]
    resource_refusal = failure_class is OperationalFailureClass.RESOURCE_REFUSAL
    case = _runtime(tmp_path, monkeypatch, parallel=parallel, stop_codes=stop_codes,
        error=error, with_dependent=not resource_refusal)
    disposition = TaskAttemptDisposition.BLOCKED if resource_refusal else TaskAttemptDisposition.FAILED
    reason = "resource-computability-unavailable" if resource_refusal else failure_class.reason_code
    try:
        result = case.scheduler.execute(case.index.run_id, case.plan)
        assert result.status is (OperationalStatus.BLOCKED if resource_refusal else OperationalStatus.FAILED)
        assert result.completed_task_ids == ("task.prefix",)
        assert result.failed_task_ids == (() if resource_refusal else ("task.failure",))
        assert result.blocked_task_ids == (("task.failure",) if resource_refusal else ("task.blocked",))
        assert case.calls == ["task.prefix", "task.failure"]
        candidate = case.index.task("task.failure").attempts[0]
        event = case.recovery.read_event(case.index, candidate.event_relative_path)
        assert event.disposition.value == disposition.value
        assert event.reason_codes == (reason,)
        assert event.failure.failure_class is failure_class
        assert event.failure.sanitized_exception_type == (ArtifactIdentityConflict.__name__ if error is None else error.__name__)
        assert event.failure.scientific_evidence is False
        assert event.failure.retryable is False
        terminal = case.recovery.read_terminal(case.index)
        assert terminal.operational_status == result.status.value
        terminal_attempt = next(row for row in terminal.attempts if row.task_id == "task.failure")
        assert terminal_attempt.reason_code == reason
        assert terminal_attempt.disposition.value == disposition.value
        assert case.receipt_store.read(case.index.run_id, "task.failure", candidate.attempt_id) is None
        envelope = case.coordinator.load(case.scheduler.execution_resource_envelope_id)
        assert envelope.events[:len(case.resource_prefix)] == case.resource_prefix
        after_failure = _files(case.root)
        assert all(after_failure[path] == digest for path, digest in case.before_failure.items()
            if not path.startswith("operational/execution-resource-envelopes/"))
        events = tuple(row for row in envelope.events if row.cell_id == "cell.task.failure")
        assert [row.kind.value for row in events] == ["RESERVATION", "LAUNCH", "OPERATIONAL_FAILURE",
            *(["RESOURCE_STOP"] if stop_kind == "applicable" else [])]
        assert events[2].reason_code == failure_class.value
        assert events[2].valid_receipt is False
        assert events[2].scientific_terminal is False
        assert envelope.cell("cell.task.failure").first_valid_receipt is None
        if stop_kind == "applicable":
            assert events[-1].reason_code == failure_class.value
        # Both failed and blocked terminals reconstruct into a fresh catalog;
        # the spent candidate, successful prefix and guarded bytes stay exact.
        before_replay = _files(case.root)
        case.scheduler.operational_repository = case.repository("rebuilt.sqlite3")
        monkeypatch.setattr(case.scheduler, "_execute_runner", lambda *_args: pytest.fail("terminal replay entered a worker"))
        assert case.scheduler.execute(case.index.run_id, case.plan) == result
        assert _files(case.root) == before_replay
        assert tuple(row.disposition for row in case.scheduler.operational_repository.attempts(case.index.run_id)
            if row.task_id == "task.failure") == (disposition,)
    finally:
        for engine in case.engines:
            engine.dispose()


@pytest.mark.parametrize("failure_class", tuple(OperationalFailureClass))
def test_failure_helper_selects_only_its_declared_class(failure_class):
    calls = []
    scheduler = object.__new__(LocalScheduler)
    declared = []
    scheduler.execution_resource_envelope_coordinator = SimpleNamespace(current=lambda _identity:
        SimpleNamespace(spec=SimpleNamespace(allowlisted_resource_stop_reason_codes=tuple(declared))))
    scheduler.execution_resource_envelope_id = "envelope.software"
    scheduler._resource_envelope_transition_lock = RLock()
    scheduler._stop_envelope_task = lambda task_id, **values: calls.append((task_id, values))
    for codes in ((), ("OTHER_DECLARED_STOP",), (failure_class.value, "OTHER_DECLARED_STOP")):
        declared[:] = codes
        scheduler._stop_failed_envelope_task("task.software", failure_class=failure_class)
    assert calls == [("task.software", {"reason_code": failure_class.value})]


def test_failure_helper_preserves_declared_stop_transition_errors(tmp_path, monkeypatch):
    case = _runtime(tmp_path, monkeypatch, parallel=1,
        stop_codes=("PROVIDER_RUNNER_DEFECT",), error=OSError)
    try:
        assert case.scheduler.execute(case.index.run_id, case.plan).status is OperationalStatus.FAILED
        before = _files(case.root)
        with pytest.raises(ValueError, match="outside a stoppable boundary"):
            case.scheduler._stop_failed_envelope_task("task.prefix",
                failure_class=OperationalFailureClass.PROVIDER_RUNNER_DEFECT)
        assert _files(case.root) == before
    finally:
        for engine in case.engines:
            engine.dispose()


@pytest.mark.parametrize("parallel", (1, 2), ids=("serial", "parallel"))
def test_resource_refusal_keeps_retryable_dependent_open_without_entry_on_replay(tmp_path, monkeypatch, parallel):
    case = _runtime(tmp_path, monkeypatch, parallel=parallel, stop_codes=(), error=ResourceAdmissionError)
    try:
        result = case.scheduler.execute(case.index.run_id, case.plan)
        assert result.status is OperationalStatus.BLOCKED
        assert result.completed_task_ids == ("task.prefix",)
        assert result.blocked_task_ids == ("task.blocked", "task.failure")
        assert case.calls == ["task.prefix", "task.failure"]
        # A retryable, unattempted dependent prevents whole-run closure. The
        # resource refusal still has its exact spent-candidate failure event.
        assert case.recovery.read_terminal(case.index) is None
        candidate = case.index.task("task.failure").attempts[0]
        event = case.recovery.read_event(case.index, candidate.event_relative_path)
        assert event.disposition is TaskRecoveryDisposition.BLOCKED
        assert event.failure.failure_class is OperationalFailureClass.RESOURCE_REFUSAL
        assert event.failure.sanitized_exception_type == ResourceAdmissionError.__name__
        before = _files(case.root)
        case.scheduler.operational_repository = case.repository("rebuilt.sqlite3")
        monkeypatch.setattr(case.scheduler, "_execute_runner", lambda *_args: pytest.fail("resource replay entered a worker"))
        assert case.scheduler.execute(case.index.run_id, case.plan) == result
        assert case.recovery.read_terminal(case.index) is None
        assert _files(case.root) == before
    finally:
        for engine in case.engines:
            engine.dispose()
