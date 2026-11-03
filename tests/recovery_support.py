# SPDX-License-Identifier: MPL-2.0
"""Ordinary frozen recovery fixtures; disclosed software records only."""

from dataclasses import fields, replace


from pathlib import Path


from types import SimpleNamespace


import pytest


from empirical_lawhood.kernel.decoding import decode_canonical_bytes


from empirical_lawhood.kernel.provenance import ObjectIdentity


from empirical_lawhood.kernel.status import OperationalStatus


from empirical_lawhood.runtime.artifacts import (
    CanonicalTaskReceipt,
    ReceiptCheck,
)


from empirical_lawhood.runtime.execution import OperationalFailureClass


from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec,
    NonTimeResourceBudget, RunExecutionResourceEnvelopeMachine,
)


from empirical_lawhood.runtime.plans import CandidateExecutionPlan, ExecutionPlan


from empirical_lawhood.runtime.recovery import (
    OperationalFailureDiagnostic, RecoveryTerminalAttempt, RecoveryTerminalDisposition,
    RunRecoveryIndex, RunRecoveryTerminalEvent, TaskRecoveryDisposition, TaskRecoveryEvent,
)




def _identity(record, attribute):
    return ObjectIdentity.from_record(getattr(record, attribute), record)


@pytest.fixture
def case():
    # Typed public fixture, with unpublished synthetic resources and histories.
    candidate = decode_canonical_bytes(
        (Path(__file__).parent / "fixtures/authoring-execution-plan.json").read_bytes(),
        CandidateExecutionPlan, maximum_bytes=1024**2)
    extension = ObjectIdentity("extensions.software.history",
        "empirical-lawhood/runtime/issued-extension-set", "1.0.0", "a" * 64)
    cells = tuple(ExecutionResourceTaskCellSpec("cell." + task.task_id, task.task_id,
        "child.software", None, None, task.maximum_attempts, 0, 0, False,
        NonTimeResourceBudget("budget." + task.task_id, 1, 1024, 1024, 0, 0), None, None, None)
        for task in candidate.tasks)
    spec = ExecutionResourceEnvelopeSpec("resources.software.history", extension, cells,
        (ChildResourceTokenLimit("child.software", 0, 0),), (), (), ("software-stop",),
        None, None, 1, 1024, (), (), "b" * 64, True, True, True, True)
    plan = ExecutionPlan(**{row.name: getattr(candidate, row.name) for row in fields(candidate)},
        issued_extension_set=extension, execution_resource_envelope_spec=_identity(spec, "envelope_spec_id"),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    index = RunRecoveryIndex.from_execution_plan(plan, run_id=plan.source_plan.object_id,
        wave_id="wave.software.original", authority_identities=(extension,))
    failed, blocked, unused = plan.tasks
    attempt = index.task(failed.task_id).attempts[0]
    failure = OperationalFailureDiagnostic.create(OperationalFailureClass.RETRY_EXHAUSTION,
        sanitized_exception_type="SoftwareFailure", sanitized_message="Synthetic pre-worker failure")
    failed_event = TaskRecoveryEvent("recovery-event." + attempt.attempt_id + ".failed",
        _identity(index, "recovery_index_id"), index.run_id, failed.task_id, attempt.attempt_id,
        attempt.ordinal, TaskRecoveryDisposition.FAILED, None, None, None, None, (), ("retry-exhaustion",), failure)
    block_event = TaskRecoveryEvent("recovery-event." + index.run_id + "." + blocked.task_id + ".not-attempted",
        _identity(index, "recovery_index_id"), index.run_id, blocked.task_id, None, None,
        TaskRecoveryDisposition.NOT_ATTEMPTED, None, None, None, None, (), ("dependency-failed",))
    summaries = (
        RecoveryTerminalAttempt(attempt.attempt_id, failed.task_id, 1,
            RecoveryTerminalDisposition.FAILED, "retry-exhaustion", None, None),
        RecoveryTerminalAttempt(f"{index.run_id}.{blocked.task_id}.block-001", blocked.task_id, 1,
            RecoveryTerminalDisposition.BLOCKED, "dependency-failed", None, None))
    terminal = RunRecoveryTerminalEvent("terminal.software.original", _identity(index, "recovery_index_id"),
        index.run_id, "FAILED", tuple(sorted(summaries, key=lambda row: (row.task_id, row.ordinal))),
        (), (failed.task_id,), (blocked.task_id,))
    envelope = RunExecutionResourceEnvelopeMachine.initial(envelope_id="run-resource-envelope." + index.run_id,
        spec=spec, execution_plan=_identity(plan, "execution_plan_id"))
    return SimpleNamespace(plan=plan, index=index, terminal=terminal, envelope=envelope,
        events=tuple(sorted((failed_event, block_event), key=lambda row: row.event_id)), receipts=(),
        failed=failed, blocked=blocked, unused=unused, failed_event=failed_event)




from hashlib import sha256




import pytest


from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, FilesystemState, GuardedExternalRoot


from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore


from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore


from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog


from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore


from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling




from empirical_lawhood.kernel.serialization import canonical_json_bytes




from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteRequest, ExternalRootContract


from empirical_lawhood.runtime.execution import OperationalAttempt, TaskAttemptDisposition










class _Inspector:
    def __init__(self, path):
        self.path = path.resolve()

    def inspect(self, _contract):
        return FilesystemState(str(self.path), True, True, 100_000_000, False)


def _files(root):
    return {row.relative_to(root).as_posix(): sha256(row.read_bytes()).hexdigest()
        for row in root.rglob("*") if row.is_file()}


def _publish_receipt(value, task, commit):
    writes = []
    for output in task.outputs:
        parents = tuple(ArtifactLineageParent(_identity(value.plan, "execution_plan_id"), ceiling,
            OutcomeAccess.OUTCOME_BLIND) for ceiling in output.parent_visibility_ceilings)
        writes.append(value.plane.write(ArtifactWriteRequest(
            logical_artifact_id=output.logical_artifact_id, relative_path=output.relative_path,
            payload_schema=output.payload_schema, profile=output.profile, media_type=output.media_type,
            publication_scope_id="software.outputs." + task.task_id,
            publication_scope_relative_root=output.relative_path.rsplit("/", 1)[0],
            payload=canonical_json_bytes({"schema": output.payload_schema, "version": "1.0.0",
                "value": {"disclosed_software_fixture": True}}),
            visibility_ceiling=output.visibility_ceiling,
            parent_visibility_ceilings=output.parent_visibility_ceilings, outcome_access=output.outcome_access,
            lineage_parents=parents)))
    writes.sort(key=lambda row: row.materialization.materialization_id)
    attempt = value.index.task(task.task_id).attempts[0]
    receipt = CanonicalTaskReceipt("receipt." + attempt.attempt_id, value.index.run_id,
        task.task_id, attempt.attempt_id, commit, (), tuple(row.materialization for row in writes),
        tuple(row.logical for row in writes), (ReceiptCheck("software.fixture", True, ()),), OperationalStatus.SUCCEEDED, ())
    value.receipt_store.commit(receipt, visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.EVALUATION_SEALED)
    return receipt


def _write_terminal(value):
    attempts = tuple(OperationalAttempt(row.attempt_id, value.index.run_id, row.task_id, row.ordinal,
        TaskAttemptDisposition(row.disposition.value), row.reason_code, None, None) for row in value.terminal.attempts)
    value.recovery.record_terminal(value.index, status=OperationalStatus(value.terminal.operational_status),
        attempts=attempts, receipts=value.receipts)
    value.terminal = value.recovery.read_terminal(value.index)


@pytest.fixture
def custody(case, tmp_path, request):
    root = tmp_path / "guarded-custody"
    root.mkdir()
    contract = ExternalRootContract("storage.software.history", "Synthetic history", str(root.resolve()),
        str(root.resolve()), "empirical-lawhood/testing/current-history-mount", 1)
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract, _Inspector(root)))
    value = SimpleNamespace(**(vars(case) | {"plane": plane, "root": root,
        "recovery": ExternalRunRecoveryStore(plane), "receipt_store": ExternalTaskReceiptStore(plane)}))
    value.recovery.freeze(value.index)
    if getattr(request, "param", None) == "blocked":
        event = replace(value.failed_event, disposition=TaskRecoveryDisposition.BLOCKED,
            reason_codes=("resource-computability-unavailable",))
        value.events = tuple(event if row == value.failed_event else row for row in value.events)
        value.terminal = replace(value.terminal, operational_status="BLOCKED", failed_task_ids=(),
            blocked_task_ids=tuple(sorted((value.failed.task_id, value.blocked.task_id))),
            attempts=tuple(replace(row, disposition=RecoveryTerminalDisposition.BLOCKED,
                reason_code=event.reason_codes[0]) if row.task_id == value.failed.task_id else row
                for row in value.terminal.attempts))
    if getattr(request, "param", None) in {"success", "wrong-historical-producer"}:
        commit = "f" * 40 if request.param == "wrong-historical-producer" else value.plan.implementation_commit
        receipt = _publish_receipt(value, value.unused, commit)
        value.receipts = (receipt,)
        value.events = tuple(sorted((*value.events, TaskRecoveryEvent.from_receipt(value.index, receipt)),
            key=lambda row: row.event_id))
        summary = RecoveryTerminalAttempt(receipt.attempt_id, receipt.task_id, 1,
            RecoveryTerminalDisposition.SUCCEEDED, None, receipt.receipt_id, receipt.fingerprint())
        value.terminal = replace(value.terminal, completed_task_ids=(receipt.task_id,),
            attempts=tuple(sorted((*value.terminal.attempts, summary), key=lambda row: (row.task_id, row.ordinal))))
    for event in value.events:
        value.recovery.append_event(value.index, event)
    # A real guarded journal retaining reservation, launch, failure and stop.
    machine = RunExecutionResourceEnvelopeMachine
    common = dict(occurred_at_utc="2026-10-16T00:00:00Z",
        cell_id=value.envelope.spec.cell_for_task(value.failed.task_id).cell_id)
    envelope = machine.reserve(value.envelope, event_id="resource.software.reserve",
        attempt_id=value.failed_event.attempt_id, **common)
    envelope = machine.launch(envelope, event_id="resource.software.launch",
        attempt_id=value.failed_event.attempt_id, **common)
    envelope = machine.observe_operational_failure(envelope, event_id="resource.software.failure",
        attempt_id=value.failed_event.attempt_id, reason_code="retry-exhaustion", **common)
    value.envelope = machine.stop(envelope, event_id="resource.software.stop", reason_code="software-stop", **common)
    value.journal = ExternalExecutionResourceEnvelopeStore(plane.root)
    value.journal.create(value.envelope)
    _write_terminal(value)
    return value


def _repository(path):
    engine = create_catalog_engine("sqlite+pysqlite:///" + path.as_posix())
    upgrade_catalog(engine)
    return SQLiteOperationalRepository(engine)





from decimal import Decimal






import pytest

from empirical_lawhood.api import recursive_authoring

from empirical_lawhood.api.results import RunCampaignRequest

from empirical_lawhood.infrastructure.execution import DirectTaskExecutor










from empirical_lawhood.runtime.execution_envelope import ProgressHeartbeat, ProgressLivenessContract


from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork





from tests.execution_support import ENFORCING_TEST_EXECUTOR_CAPABILITY

from tests.runtime_platform import test_recursive_prospective_workflow as fixture_owner

from tests.test_issued_worker_preparation import _binding

def _public_failed_history(tmp_path, monkeypatch):
    original_fixture = fixture_owner.prospective_fixture

    def single_attempt(**arguments):
        compiled, authoring, context = original_fixture(**arguments)
        draft = replace(compiled.draft, operations=tuple(replace(row, maximum_attempts=1) for row in compiled.draft.operations))
        return replace(compiled, draft=draft), authoring, context

    monkeypatch.setattr(fixture_owner, "prospective_fixture", single_attempt)
    parts = list(fixture_owner._public_issued_handoff_fixture(tmp_path, monkeypatch))
    package = parts[5]
    resources = package.execution_resource_envelope_spec
    native_ids = {"prepare", "freeze"}
    cells = tuple(replace(row, physical_execution_cost=1, retry_token_cost=1, native_simulator_launch=True,
        progress_liveness=ProgressLivenessContract("liveness.software.source-" + row.task_id,
            ProgressHeartbeat.SCHEMA, "disclosed-software-operation", Decimal(30), True, True))
        if row.task_id in native_ids else row for row in resources.task_cells)
    resources = replace(resources, task_cells=cells,
        allowlisted_resource_stop_reason_codes=(),
        child_token_limits=tuple(replace(row,
        physical_execution_token_limit=sum(cell.physical_execution_cost for cell in cells if cell.child_id == row.child_id))
        for row in resources.child_token_limits))
    package = replace(package, execution_resource_envelope_spec=resources)
    parts[5] = package
    control = fixture_owner._run_public_handoff(tmp_path, issued_parts=tuple(parts), prepare_only=True)
    service, plane = control.service, parts[3]
    monkeypatch.setattr(service, "_check_identity", lambda *_args, **_options: None)
    original_resolve = service._resolve_campaign_provider

    def prepare_native(*, runner, context, expected_parent):
        cell = resources.cell_for_task(context.task_id)
        return PreparedNativeWork(expected_parent, (cell.physical_independent_unit_id,),
                                  ("disclosed.software-effect." + context.task_id,))

    class NativeProvider:
        def __init__(self, delegate):
            self.delegate = delegate

        def __getattr__(self, name):
            return getattr(self.delegate, name)

        def worker_preparations(self, registry, execution_plan=None):
            keys = {task.capability.capability_key for task in execution_plan.tasks if task.task_id in native_ids}
            return tuple(replace(row, native_effect=True, native_work_preparer=prepare_native)
                if row.selection.capability_key in keys else row
                for row in self.delegate.worker_preparations(registry, execution_plan))

        def runners(self, registry, source_records=()):
            runners = self.delegate.runners(registry, source_records)
            keys = {step.capability_key for step in package.protocol.steps if step.step_id in native_ids}
            for runner in runners:
                if runner.manifest.capability_key in keys:
                    runner.execute_with_progress = lambda context, progress, selected=runner: selected.execute(context)
            return runners

    def provider(*arguments, **options):
        resolved = original_resolve(*arguments, **options)
        return replace(resolved, provider=NativeProvider(resolved.provider))

    monkeypatch.setattr(service, "_resolve_campaign_provider", provider)
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda _root: _binding(package.implementation_commit))

    class InlineExecutor:
        enforcement_capability = ENFORCING_TEST_EXECUTOR_CAPABILITY

        def __init__(self):
            self.calls = []
            self.native_entries = []
            self.repaired = False

        def execute_deadline_free(self, runner, context, *, prepared_contract=None, native_entry=None, **_options):
            self.calls.append((context.task_id, context.attempt_id, prepared_contract))
            if native_entry is not None:
                native_entry()
                self.native_entries.append(context.task_id)
            if not self.repaired and context.task_id == "develop-a":
                raise OSError("disclosed software operational failure")
            if prepared_contract is not None:
                context = replace(context, prepared_invocation=prepared_contract)
            return DirectTaskExecutor().execute(runner, context, timeout_seconds=60)

    executor = InlineExecutor()
    service.executor = executor
    result = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True,
        reveal_authority_id=control.reveal.authority_id))
    assert not result.succeeded
    try:
        plan, index, recovery, terminal = service._load_status_recovery(package.run_plan_id)
    except KeyError:
        pytest.fail(f"initial disclosed failure has no terminal: {result.reason_codes!r}, {result.errors!r}; "
                    f"executor tasks: {[row[0] for row in executor.calls]!r}")
    assert terminal is not None
    receipt_store = ExternalTaskReceiptStore(plane)
    receipts = tuple(receipt for task in index.tasks for candidate in task.attempts
        if (receipt := receipt_store.read(index.run_id, task.task_id, candidate.attempt_id)) is not None)
    events = []
    for task in index.tasks:
        for relative in (*(row.event_relative_path for row in task.attempts), task.nonattempt_event_relative_path):
            event = recovery.read_event(index, relative)
            if event is not None:
                events.append(event)
    events = tuple(sorted(events, key=lambda row: row.event_id))
    envelope_store = ExternalExecutionResourceEnvelopeStore(plane.root)
    envelope = envelope_store.load("run-resource-envelope." + index.run_id)
    return SimpleNamespace(control=control, package=package, plane=plane, service=service,
        executor=executor, plan=plan, index=index, recovery=recovery, terminal=terminal,
        receipt_store=receipt_store, receipts=receipts, events=events, envelope=envelope,
        envelope_store=envelope_store)
