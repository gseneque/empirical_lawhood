# SPDX-License-Identifier: MPL-2.0
"""Ordinary process/scheduler finalization with literal software effects only."""

from dataclasses import replace
from decimal import Decimal
import multiprocessing
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.execution import (
    ExecutionResourceCapacity, LiveLeaseError, LocalProcessExecutor, LocalScheduler, ResourceAdmissionError,
)
from empirical_lawhood.infrastructure import execution as execution_owner
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_parent_finalization import NativeParentFinalizationPending
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.recursive_custody import read_recursive_products
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, ParentPreparedTaskRunner, RunnerRegistry, TaskAttemptDisposition, TaskBlockReason, VerifiedArtifactInput
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, PlanLane
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from tests.runtime_platform.test_execution_scheduler import FixedClock, StaticExternalInputResolver
from tests.runtime_platform.test_native_subwork import _plane, _publish
from tests.runtime_platform.test_native_parent_finalization import _census
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner, _case


class CurrentParentRunner(ExposedReadRunner):
    """Same recover-first producer on initial execution and completed assembly."""

    def __init__(self, definition, mode):
        super().__init__()
        self.definition = definition
        self.mode = mode

    def preflight(self, context):
        super().preflight(context)
        self.preflight_complete = True

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        assert self.preflight_complete
        work = context.prepared_invocation.native_work
        definition, = work.definitions
        native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
        if self.mode == "interrupt-before-begin":
            raise OSError("disclosed interruption after parent contact and before child entry")
        if self.mode != "nonentry":
            completed = native_subwork.recover(definition)
            if completed is None:
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)  # Literal disclosed control; no engine or randomness.
                if self.mode == "unknown":
                    raise ValueError("exposed loss after contact without known native return")
                def literal_call():
                    if self.mode in {"failed", "raw-failed-products-missing"}:
                        raise ValueError("disclosed literal native-call error")
                    return b"FALSIFIED"
                try:
                    payload = invoke_native_subwork(native_subwork, entry, literal_call)
                except ValueError:
                    if self.mode not in {"failed", "raw-failed-products-missing"}:
                        raise
                    payload = b"UNEVALUABLE"
                if self.mode in {"raw-products-missing", "raw-failed-products-missing"}:
                    raise OSError("disclosed product publication interruption after actual raw return")
                _publish(native_subwork, entry, payload)
                native_subwork.complete(entry,
                    operational_status=OperationalStatus.FAILED if self.mode == "failed" else OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(None, Decimal("0.125"), None),
                    cost_scope="literal software conformance; no scientific acquisition",
                    reason_codes=("exposed-known-error",) if self.mode == "failed" else ())
            if self.mode in {"refuse", "failed"}:
                raise ValueError("exposed scientific assembler refuses an ordinary result")
            assert b"".join(native_subwork.iter_completed_output(definition,
                definition.outputs[0].output_id)) == b"FALSIFIED"
        return super().execute(context)


def _prepared_work(*, runner, context, expected_parent):
    template = runner.prepare_callback.definition if isinstance(runner, ParentPreparedTaskRunner) else runner.definition
    definition = replace(template, parent_contact=expected_parent)
    return PreparedNativeWork(expected_parent, ("exposed.unit",), ("exposed.slot",), (definition,),
        (NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,)),))


def _runtime(tmp_path, *, mode="complete", parallel=1, parent_prepared=False, recorded_provenance=None):
    plane, bundle, template, _, contract, _ = _case(tmp_path, actual=True, native=True,
        recorded_provenance=recorded_provenance)
    task = contract.execution_task_record
    task = replace(task, outputs=tuple(replace(row, relative_path="runs/exposed.run/outputs/" + row.relative_path)
        for row in task.outputs))
    registry_sha256 = "a" * 64
    plan = DevelopmentExecutionPlan("exposed.current-parent", PlanLane.DEVELOPMENT,
        ObjectIdentity("exposed.run", "empirical-lawhood/runtime/development-run-plan", "1.0.0", "b" * 64),
        registry_sha256, contract.implementation.observed_git_head, (task,), True)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id="exposed.run", wave_id="exposed.finalization")
    engine = create_catalog_engine("sqlite+pysqlite:///" + str(tmp_path / "catalog.sqlite3"))
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    recovery = ExternalRunRecoveryStore(plane)
    receipts = ExternalTaskReceiptStore(plane)
    clock = FixedClock(100)
    state = SimpleNamespace(plane=plane, bundle=bundle, task=task, plan=plan, index=index,
        repository=repository, recovery=recovery, receipts=receipts, clock=clock, mode=mode)
    def scheduler():
        contacts = ExternalNativeEffectContactStore(plane=plane,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        runner = CurrentParentRunner(template.selected_definitions[0], state.mode)
        if parent_prepared:
            plain = runner
            def prepare(context):
                assert context.prepared_invocation is not None
                context.prepared_invocation.require_complete()
                return plain
            prepare.definition = plain.definition
            runner = ParentPreparedTaskRunner(plain.manifest, prepare, native_effect=True)
        result = LocalScheduler(operational_repository=repository, artifact_writer=plane,
            receipt_store=receipts, recovery_index=index, recovery_store=recovery,
            runner_registry=RunnerRegistry((runner,), registry_sha256=registry_sha256),
            implementation_commit=plan.implementation_commit,
            external_input_resolver=StaticExternalInputResolver(bundle.verified_inputs),
            input_port_factory=plane, executor=LocalProcessExecutor(scratch_root=plane.root),
            implementation_binding=contract.implementation, clock=clock,
            authorized_barriers=(), lane=PlanLane.DEVELOPMENT,
            assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
            native_effect_contact_store=contacts, native_effect_capability_keys=(runner.manifest.capability_key,),
            native_work_preparers={runner.manifest.capability_key: _prepared_work},
            maximum_parallel_tasks=parallel,
            parallel_resource_capacity=ExecutionResourceCapacity(parallel, 8 * 1024**3, 0, True, True, False))
        return result, contacts
    state.scheduler = scheduler
    return state


def _event(state):
    task, = state.index.tasks
    candidate, = task.attempts
    return state.recovery.read_event(state.index, candidate.event_relative_path)


def _current_products(state):
    return read_recursive_products(plane=state.plane, plan=state.plan, index=state.index,
        external_inputs=state.bundle.verified_inputs, output_codecs={}, decode_products=False, allow_partial=True)


def _persisted_provenance(plane):
    manifest = plane.read_manifest("inputs/numerical.producing-provenance.json")
    port = plane.open(VerifiedArtifactInput(manifest.logical, manifest.materialization),
        maximum_bytes=manifest.materialization.size_bytes)
    try:
        raw = port.read()
    finally:
        port.close()
    provenance = decode_canonical_bytes(raw, NumericalProducingProvenance, maximum_bytes=len(raw))
    assert (manifest.logical.logical_artifact_id, manifest.logical.payload_schema, manifest.logical.profile,
        manifest.logical.media_type, manifest.logical.visibility_ceiling, manifest.logical.outcome_access,
        manifest.logical.content_sha256) == (provenance.identity.object_id, NumericalProducingProvenance.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, provenance.fingerprint())
    return manifest, raw, provenance


def _fresh_process_resume(path, queue):
    _, _, provenance = _persisted_provenance(_plane(Path(path) / "custody"))
    state = _runtime(Path(path), recorded_provenance=provenance)
    state.clock.value = 161
    try:
        scheduler, contacts = state.scheduler()
        result = scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        contact = contacts.read("exposed.run", state.task.task_id)
        queue.put((result.status.value, attempt.attempt_id, contacts.is_live_creator(contact)))
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("mode", ("raw-products-missing", "raw-failed-products-missing"))
@pytest.mark.parametrize("parallel", (1, 2))
def test_known_raw_return_without_products_preserves_original_attempt_and_resource_history(
        tmp_path, monkeypatch, mode, parallel):
    state = _runtime(tmp_path, mode=mode, parallel=parallel)
    scheduler, contacts = state.scheduler()
    unknown_transitions = []
    monkeypatch.setattr(scheduler, "_unknown_envelope_completion",
        lambda *args, **kwargs: unknown_transitions.append((args, kwargs)))
    try:
        with pytest.raises(NativeParentFinalizationPending, match="known native return.*incomplete durable"):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        assert attempt.disposition is TaskAttemptDisposition.RUNNING
        assert _event(state) is None and state.recovery.read_terminal(state.index) is None
        assert unknown_transitions == []
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        retained = native.inspect(definition)
        assert retained.state is NativeSubworkState.UNKNOWN_COMPLETION
        assert retained.call_return is not None and retained.completion is None and retained.receipt is None
        assert retained.call_return.error_type == ("ValueError" if mode == "raw-failed-products-missing" else None)
        assert retained.outputs == ()
        snapshot = _census(native)
        with monkeypatch.context() as reading:
            reading.setattr(ExternalNativeSubworkStore, "recover", lambda *args, **kwargs: pytest.fail(
                "a partial result read must not publish native receipts"))
            products = _current_products(state)
        observed = products["native_observations"][attempt.attempt_id]
        assert observed.pending_publication_definition_ids == (definition.identity,)
        assert observed.uncertain_contact_definition_ids == ()
        assert observed.failed_return_definition_ids == ((definition.identity,)
            if mode == "raw-failed-products-missing" else ())
        assert products["operational_census"] == () and products["attempt_receipts"] == {}
        assert products["native_observation_unavailable"] == {} and _census(native) == snapshot
        state.clock.value += scheduler.lease_seconds + 1
        resumed, fresh_contacts = state.scheduler()
        def forbidden(*args, **kwargs):
            pytest.fail("known returned work launched another attempt or native reservation")
        monkeypatch.setattr(resumed, "_start_attempt", forbidden)
        monkeypatch.setattr(resumed, "_launch_envelope_attempt", forbidden)
        monkeypatch.setattr(resumed, "_unknown_envelope_completion",
            lambda *args, **kwargs: unknown_transitions.append((args, kwargs)))
        with pytest.raises(NativeParentFinalizationPending, match="known native return.*incomplete durable"):
            resumed.execute("exposed.run", state.plan)
        remaining, = state.repository.attempts("exposed.run")
        assert remaining.attempt_id == attempt.attempt_id and remaining.disposition is TaskAttemptDisposition.RUNNING
        assert fresh_contacts.read("exposed.run", state.task.task_id) == contact
        assert not fresh_contacts.is_live_creator(contact)
        assert native.inspect(definition) == retained
        assert _event(state) is None and state.recovery.read_terminal(state.index) is None
        assert unknown_transitions == []
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


def test_late_original_raw_return_changes_only_current_read_observation(tmp_path, monkeypatch):
    """Delay visibility of actual original return bytes; never reconstruct a fact."""
    import os

    state = _runtime(tmp_path, mode="raw-products-missing")
    scheduler, contacts = state.scheduler()
    original = ExternalNativeSubworkStore.call_return
    retained = []
    def delay_visibility(store, entry, **kwargs):
        root = Path(store.plane.root.contract.canonical_path)
        before = {path for path in root.rglob("*") if path.is_file()}
        original(store, entry, **kwargs)
        created = {path for path in root.rglob("*") if path.is_file()} - before
        assert created
        for path in created:
            retained.append((path, path.read_bytes(), path.stat()))
            path.unlink()
    monkeypatch.setattr(ExternalNativeSubworkStore, "call_return", delay_visibility)
    try:
        result = scheduler.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.BLOCKED
        attempt, = state.repository.attempts("exposed.run")
        event, terminal = _event(state), state.recovery.read_terminal(state.index)
        assert attempt.reason_code == TaskBlockReason.UNKNOWN_COMPLETION.value
        before = _current_products(state)["native_observations"][attempt.attempt_id]
        assert before.uncertain_contact_definition_ids and before.pending_publication_definition_ids == ()
        for path, raw, stat in retained:
            path.write_bytes(raw)
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        parent = contacts.read("exposed.run", state.task.task_id)
        reader = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=parent, parent_inputs=state.bundle.manifests, completed_only=True)
        snapshot = _census(reader)
        with monkeypatch.context() as reading:
            reading.setattr(ExternalNativeSubworkStore, "recover", lambda *args, **kwargs: pytest.fail(
                "a late-fact read must not recover publication"))
            products = _current_products(state)
        current = products["native_observations"][attempt.attempt_id]
        assert current.uncertain_contact_definition_ids == ()
        assert current.pending_publication_definition_ids == before.uncertain_contact_definition_ids
        assert current.inspections[0].call_return is not None and current.inspections[0].receipt is None
        assert _event(state) == event and state.recovery.read_terminal(state.index) == terminal
        assert state.repository.attempts("exposed.run") == (attempt,) and _census(reader) == snapshot
        # Current facts never reopen the closed UNKNOWN attempt or permit entry.
        resumed, _ = state.scheduler()
        assert resumed.execute("exposed.run", state.plan).status is OperationalStatus.BLOCKED
        assert state.repository.attempts("exposed.run") == (attempt,)
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("residue", ("invocation", "roster"))
def test_current_native_read_refuses_retained_custody_after_entire_root_contact_is_removed(
        tmp_path, monkeypatch, residue):
    state = _runtime(tmp_path, mode="raw-products-missing")
    scheduler, contacts = state.scheduler()
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        parent = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=parent, parent_inputs=state.bundle.manifests)
        # Leave one authentic deterministic namespace independently of the
        # other, after deleting both root-contact components (not just corrupting
        # a sidecar that the contact reader already refuses).
        other = (native._roster_path(parent, "selected.native-subwork") if residue == "invocation"
            else native._invocation_path(parent))
        contact = contacts._path(parent.run_id, parent.task_id)
        for relative in (contact, contact + ".manifest.json", other, other + ".manifest.json"):
            state.plane.root.resolve(relative, for_write=False).unlink()
        before = _census(native)
        monkeypatch.setattr(ExternalNativeSubworkStore, "recover", lambda *args, **kwargs: pytest.fail(
            "an orphaned-custody read must not recover publication"))
        with pytest.raises(ValueError, match="orphaned native " + residue + " custody"):
            _current_products(state)
        assert _census(native) == before and state.repository.attempts("exposed.run") == (attempt,)
        assert _event(state) is None and state.recovery.read_terminal(state.index) is None
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("mode", ("complete", "nonentry"))
@pytest.mark.parametrize("parallel", (1, 2))
@pytest.mark.parametrize("parent_prepared", (False, True))
def test_parent_publication_interruption_resumes_same_attempt_without_acquisition(tmp_path, monkeypatch, mode, parallel,
        parent_prepared):
    state = _runtime(tmp_path, mode=mode, parallel=parallel, parent_prepared=parent_prepared)
    scheduler, contacts = state.scheduler()
    original = state.receipts.commit
    def interrupt(*args, **kwargs):
        raise OSError("exposed parent receipt publication interruption")
    monkeypatch.setattr(state.receipts, "commit", interrupt)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        assert attempt.disposition is TaskAttemptDisposition.RUNNING
        assert _event(state) is None
        contact = contacts.read("exposed.run", state.task.task_id)
        assert contact is not None
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        roster = native.read_roster(contact)
        definition = native.read_definition(roster.subworks[0])
        retained = native.inspect(definition)
        assert retained.state is (NativeSubworkState.NOT_ENTERED if mode == "nonentry" else NativeSubworkState.COMPLETED)
        before = retained
        monkeypatch.setattr(state.receipts, "commit", original)
        resumed, fresh_contacts = state.scheduler()
        with pytest.raises(LiveLeaseError):
            resumed.execute("exposed.run", state.plan)
        state.clock.value += scheduler.lease_seconds + 1
        result = resumed.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        complete, = state.repository.attempts("exposed.run")
        assert complete.attempt_id == attempt.attempt_id and complete.disposition is TaskAttemptDisposition.SUCCEEDED
        assert native.inspect(definition) == before
        assert fresh_contacts.read("exposed.run", state.task.task_id) == contact
        assert not fresh_contacts.is_live_creator(contact)
        receipt, = result.receipts
        assert receipt.attempt_id == attempt.attempt_id
        assert state.recovery.read_terminal(state.index).operational_status == OperationalStatus.SUCCEEDED.value
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("mode", ("unknown", "refuse", "failed"))
def test_current_native_return_and_unknown_dispositions_are_truthful(tmp_path, mode):
    state = _runtime(tmp_path, mode=mode)
    scheduler, contacts = state.scheduler()
    try:
        if mode == "refuse":
            with pytest.raises(NativeParentFinalizationPending):
                scheduler.execute("exposed.run", state.plan)
            assert _event(state) is None
            state.clock.value += scheduler.lease_seconds + 1
            resumed, _ = state.scheduler()
            with pytest.raises(NativeParentFinalizationPending):
                resumed.execute("exposed.run", state.plan)
            attempt, = state.repository.attempts("exposed.run")
            assert attempt.disposition is TaskAttemptDisposition.RUNNING and _event(state) is None
        else:
            result = scheduler.execute("exposed.run", state.plan)
            attempt, = state.repository.attempts("exposed.run")
            if mode == "unknown":
                assert result.status is OperationalStatus.BLOCKED
                assert attempt.reason_code == TaskBlockReason.UNKNOWN_COMPLETION.value
                assert _event(state).failure.failure_class.value == "RECOVERY_OBSTRUCTION"
                resumed, _ = state.scheduler()
                assert resumed.execute("exposed.run", state.plan).status is OperationalStatus.BLOCKED
            else:
                assert result.status is OperationalStatus.FAILED
                assert attempt.disposition is TaskAttemptDisposition.FAILED
                assert _event(state).failure.failure_class.value == "NATIVE_RETURN_FAILURE"
                resumed, _ = state.scheduler()
                assert resumed.execute("exposed.run", state.plan).status is OperationalStatus.FAILED
            assert state.receipts.read("exposed.run", state.task.task_id, attempt.attempt_id) is None
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("parallel", (1, 2))
@pytest.mark.parametrize("parent_prepared", (False, True))
def test_recovery_requiring_unentered_native_work_reports_obstruction(tmp_path, parallel, parent_prepared):
    state = _runtime(tmp_path, mode="interrupt-before-begin", parallel=parallel,
        parent_prepared=parent_prepared)
    scheduler, contacts = state.scheduler()
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        before = native.inspect(definition)
        assert before.state is NativeSubworkState.NOT_ENTERED
        state.mode = "complete"
        state.clock.value += scheduler.lease_seconds + 1
        resumed, _ = state.scheduler()
        result = resumed.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.BLOCKED
        blocked, = state.repository.attempts("exposed.run")
        assert blocked.attempt_id == attempt.attempt_id
        assert blocked.reason_code == TaskBlockReason.UNKNOWN_COMPLETION.value
        assert _event(state).failure.failure_class.value == "RECOVERY_OBSTRUCTION"
        assert native.inspect(definition) == before
        assert state.receipts.read("exposed.run", state.task.task_id, attempt.attempt_id) is None
        assert state.recovery.read_terminal(state.index).operational_status == OperationalStatus.BLOCKED.value
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


def test_fresh_coordinator_process_finishes_original_parent_without_reacquiring(tmp_path, monkeypatch):
    state = _runtime(tmp_path)
    scheduler, contacts = state.scheduler()
    def interrupt(*args, **kwargs):
        raise OSError("exposed original parent receipt interruption")
    monkeypatch.setattr(state.receipts, "commit", interrupt)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        before = native.inspect(definition)
        original_provenance = _persisted_provenance(state.plane)
        process_context = multiprocessing.get_context("spawn")
        queue = process_context.Queue()
        process = process_context.Process(target=_fresh_process_resume, args=(str(tmp_path), queue))
        process.start()
        process.join(45)
        if process.is_alive():
            process.terminate()
            process.join(5)
            pytest.fail("exposed fresh coordinator did not finish its bounded software control")
        assert process.exitcode == 0
        assert queue.get(timeout=5) == ("SUCCEEDED", attempt.attempt_id, False)
        assert native.inspect(definition) == before
        assert _persisted_provenance(state.plane) == original_provenance
        complete, = state.repository.attempts("exposed.run")
        assert complete.attempt_id == attempt.attempt_id and complete.disposition is TaskAttemptDisposition.SUCCEEDED
        queue.close()
        queue.join_thread()
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("boundary", ("before-outputs", "before-receipt"))
def test_changed_child_custody_cannot_publish_a_finalized_parent_receipt(tmp_path, monkeypatch, boundary):
    state = _runtime(tmp_path)
    scheduler, contacts = state.scheduler()
    original_receipt_commit = state.receipts.commit
    def interrupted(*args, **kwargs):
        raise OSError("exposed parent receipt publication interruption")
    monkeypatch.setattr(state.receipts, "commit", interrupted)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        output, = native.inspect(definition).outputs
        path = state.plane.root.resolve(output.materialization.relative_path, for_write=False)
        changed = []
        def mutate():
            path.write_bytes(b"X" * output.materialization.size_bytes)
            changed.append(True)
        monkeypatch.setattr(state.receipts, "commit", original_receipt_commit)
        state.clock.value += scheduler.lease_seconds + 1
        resumed, _ = state.scheduler()
        if boundary == "before-outputs":
            original = resumed._commit_runner_result
            def commit(*args, **kwargs):
                mutate()
                return original(*args, **kwargs)
            monkeypatch.setattr(resumed, "_commit_runner_result", commit)
        else:
            original = state.plane.write_batch
            def write_batch(requests, *args, **kwargs):
                result = original(requests, *args, **kwargs)
                if not changed:
                    mutate()
                return result
            monkeypatch.setattr(state.plane, "write_batch", write_batch)
        try:
            result = resumed.execute("exposed.run", state.plan)
        except ArtifactIdentityConflict:
            pass
        else:
            assert result.status is not OperationalStatus.SUCCEEDED
        assert changed
        assert state.receipts.read("exposed.run", state.task.task_id, attempt.attempt_id) is None
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


def test_repeated_child_receipt_publication_failure_preserves_original_parent_until_resume(tmp_path, monkeypatch):
    state = _runtime(tmp_path)
    scheduler, contacts = state.scheduler()
    original = ExternalTaskReceiptStore.commit
    def interrupted(self, receipt, *args, **kwargs):
        if receipt.task_id.startswith("native-subwork."):
            raise OSError("exposed repeated native child receipt publication failure")
        return original(self, receipt, *args, **kwargs)
    monkeypatch.setattr(ExternalTaskReceiptStore, "commit", interrupted)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        assert attempt.disposition is TaskAttemptDisposition.RUNNING and _event(state) is None
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        known = native.inspect(definition)
        assert known.completion is not None and known.receipt is None
        monkeypatch.setattr(ExternalTaskReceiptStore, "commit", original)
        state.clock.value += scheduler.lease_seconds + 1
        resumed, _ = state.scheduler()
        result = resumed.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        completed, = state.repository.attempts("exposed.run")
        assert completed.attempt_id == attempt.attempt_id and completed.disposition is TaskAttemptDisposition.SUCCEEDED
        final = native.inspect(definition)
        assert final.completion == known.completion and final.outputs == known.outputs
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


@pytest.mark.parametrize("prerequisite", ("worker-inputs", "prepared-invocation"))
def test_missing_finalization_prerequisite_keeps_original_attempt_pending_until_restored(tmp_path, monkeypatch,
        prerequisite):
    state = _runtime(tmp_path)
    scheduler, contacts = state.scheduler()
    original = state.receipts.commit
    def interrupted(*args, **kwargs):
        raise OSError("exposed original parent receipt interruption")
    monkeypatch.setattr(state.receipts, "commit", interrupted)
    try:
        with pytest.raises(NativeParentFinalizationPending):
            scheduler.execute("exposed.run", state.plan)
        attempt, = state.repository.attempts("exposed.run")
        contact = contacts.read("exposed.run", state.task.task_id)
        native = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=contact, parent_inputs=state.bundle.manifests)
        definition = native.read_definition(native.read_roster(contact).subworks[0])
        before = native.inspect(definition)
        monkeypatch.setattr(state.receipts, "commit", original)
        state.clock.value += scheduler.lease_seconds + 1
        resumed, _ = state.scheduler()
        def unavailable(*args, **kwargs):
            raise ResourceAdmissionError("exposed current finalization prerequisite unavailable")
        with monkeypatch.context() as temporary:
            if prerequisite == "worker-inputs":
                temporary.setattr(resumed, "_worker_inputs", unavailable)
            else:
                temporary.setattr(execution_owner, "prepare_worker_invocation", unavailable)
            with pytest.raises(NativeParentFinalizationPending):
                resumed.execute("exposed.run", state.plan)
            pending, = state.repository.attempts("exposed.run")
            assert pending.attempt_id == attempt.attempt_id and pending.disposition is TaskAttemptDisposition.RUNNING
            assert _event(state) is None and state.recovery.read_terminal(state.index) is None
            assert native.inspect(definition) == before
        result = resumed.execute("exposed.run", state.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        complete, = state.repository.attempts("exposed.run")
        assert complete.attempt_id == attempt.attempt_id and complete.disposition is TaskAttemptDisposition.SUCCEEDED
        assert native.inspect(definition) == before
    finally:
        state.bundle.close()
        state.repository.engine.dispose()
