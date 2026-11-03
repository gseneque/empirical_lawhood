# SPDX-License-Identifier: MPL-2.0
"""Receipt-only custody controls; synthetic software inputs, no real workers."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import NoResultFound

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore, RunRecoveryError
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelopeMachine
from empirical_lawhood.runtime.execution import OperationalAttempt, TaskAttemptDisposition
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.recovery import RunRecoveryIndex
from tests.recovery_support import _identity, case as case
from tests.recovery_support import _Inspector, _repository


def _census(root):
    return {path.relative_to(root).as_posix(): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file() and path.name != ".native-execution.lock"}


@pytest.fixture
def history(case, tmp_path):
    root = tmp_path / "history"
    root.mkdir()
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract("software.failed-history",
        "Disclosed synthetic history", str(root.resolve()), str(root.resolve()),
        "empirical-lawhood/testing/failed-history-mount", 1), _Inspector(root)))
    recovery = ExternalRunRecoveryStore(plane)
    recovery.freeze(case.index)
    task = next(row for row in case.plan.tasks if row.task_id == case.plan.topological_task_ids()[0])
    candidate = case.index.task(task.task_id).attempts[0]
    event = replace(case.failed_event, event_id="recovery-event." + candidate.attempt_id + ".failed",
        task_id=task.task_id, attempt_id=candidate.attempt_id, attempt_ordinal=candidate.ordinal)
    recovery.append_event(case.index, event)
    machine = RunExecutionResourceEnvelopeMachine
    common = dict(cell_id=case.envelope.spec.cell_for_task(task.task_id).cell_id,
        occurred_at_utc="2026-10-16T00:00:00Z", attempt_id=candidate.attempt_id)
    envelope = machine.reserve(case.envelope, event_id="history.reserve", **common)
    envelope = machine.launch(envelope, event_id="history.launch", **common)
    envelope = machine.observe_operational_failure(envelope, event_id="history.failure", reason_code="RETRY_EXHAUSTION", **common)
    journal = ExternalExecutionResourceEnvelopeStore(plane.root)
    journal.create(envelope)
    return SimpleNamespace(**vars(case), root=root, plane=plane, recovery=recovery,
        receipt_store=ExternalTaskReceiptStore(plane), journal=journal, retained_envelope=envelope,
        retained_event=event, retained_task=task, candidate=candidate)


def _close(value, repository, **changes):
    arguments = dict(plan=value.plan, index=value.index, receipt_store=value.receipt_store,
        repository=repository, resource_spec=value.retained_envelope.spec)
    return value.recovery.reconcile_failed_history(**(arguments | changes))


def test_real_failed_terminal_contains_only_retained_attempts_and_pending_stays_unused(history, tmp_path):
    before = _census(history.root)
    index_before = history.index.canonical_bytes()
    repository = _repository(tmp_path / "private.sqlite")
    try:
        terminal = _close(history, repository)
        assert terminal.operational_status == "FAILED"
        assert terminal.failed_task_ids == (history.retained_task.task_id,)
        assert terminal.completed_task_ids == terminal.blocked_task_ids == ()
        assert tuple(row.attempt_id for row in terminal.attempts) == (history.candidate.attempt_id,)
        assert tuple(row.attempt_id for row in repository.attempts(history.index.run_id)) == (history.candidate.attempt_id,)
        for task in history.index.tasks:
            if task.task_id != history.retained_task.task_id:
                assert history.recovery.read_event(history.index, task.nonattempt_event_relative_path) is None
                assert all(history.recovery.read_event(history.index, row.event_relative_path) is None for row in task.attempts)
        after = _census(history.root)
        assert all(after[path] == value for path, value in before.items())
        assert history.index.canonical_bytes() == index_before
        assert history.journal.load(history.retained_envelope.envelope_id) == history.retained_envelope
    finally:
        repository.engine.dispose()


def test_completed_closure_rebuilds_private_catalog_without_primary_changes(history, tmp_path):
    first = _repository(tmp_path / "first.sqlite")
    try:
        terminal = _close(history, first)
    finally:
        first.engine.dispose()
    before = _census(history.root)
    rebuilt = _repository(tmp_path / "rebuilt.sqlite")
    try:
        assert _close(history, rebuilt) == terminal
        assert _census(history.root) == before
    finally:
        rebuilt.engine.dispose()


@pytest.mark.parametrize('changed_member', ('json', 'journal'))
def test_repeated_resource_load_reuses_replay_but_rehashes_same_stamp_bytes(history, monkeypatch, changed_member):
    from empirical_lawhood.infrastructure import execution_resource_envelopes as owner
    envelope = history.retained_envelope
    task = history.unused
    attempt = history.index.task(task.task_id).attempts[0]
    updated = RunExecutionResourceEnvelopeMachine.reserve(envelope,
        event_id='history.additional.reserve', occurred_at_utc='2026-10-16T00:00:01Z',
        cell_id=envelope.spec.cell_for_task(task.task_id).cell_id, attempt_id=attempt.attempt_id)
    history.journal.compare_and_append(expected=envelope, updated=updated)
    cold = ExternalExecutionResourceEnvelopeStore(history.plane.root)
    assert cold.load(envelope.envelope_id) == updated
    def forbidden(*args, **kwargs):
        pytest.fail('identical fully hashed journal was decoded/replayed again')
    monkeypatch.setattr(owner, 'reconstruct_execution_resource_envelope', forbidden)
    monkeypatch.setattr(owner, 'replay_execution_resource_event', forbidden)
    assert cold.load(envelope.envelope_id) == updated
    stamps = cold._cached[3]
    monkeypatch.setattr(cold, '_stamps', lambda paths: stamps)
    path = cold._path(envelope.envelope_id, changed_member)
    raw = path.read_bytes()
    assert b'2026-10-16' in raw
    path.write_bytes(raw.replace(b'2026-10-16', b'2026-10-15', 1))
    with pytest.raises(ValueError, match='base differs|digest differs'):
        cold.load(envelope.envelope_id)


@pytest.mark.parametrize("target", ("event", "manifest"))
def test_partial_or_changed_event_refuses_before_catalog_or_terminal(history, tmp_path, target):
    path = history.root / history.candidate.event_relative_path
    if target == "event":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path.with_name(path.name + ".manifest.json").unlink()
    before = _census(history.root)
    repository = _repository(tmp_path / "refused.sqlite")
    try:
        with pytest.raises((RunRecoveryError, ValueError)):
            _close(history, repository)
        assert repository.attempts(history.index.run_id) == ()
        assert history.recovery.read_terminal(history.index) is None
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_running_catalog_attempt_refuses_without_reclassifying_it(history, tmp_path):
    repository = _repository(tmp_path / "live.sqlite")
    repository.register_run(history.index.run_id, history.plan.fingerprint())
    repository.start_attempt(run_id=history.index.run_id, task_id=history.retained_task.task_id,
        attempt_id=history.candidate.attempt_id, lease_id="lease.software", owner_id="owner.software", expires_epoch_seconds=1)
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError, match="running"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id)[0].disposition.value == "RUNNING"
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_foreign_index_refuses_without_projection(history, tmp_path):
    foreign = RunRecoveryIndex.from_execution_plan(history.plan, run_id=history.index.run_id,
        wave_id="wave.foreign", authority_identities=history.index.authority_identities)
    repository = _repository(tmp_path / "foreign.sqlite")
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError):
            _close(history, repository, index=foreign)
        assert repository.attempts(history.index.run_id) == ()
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_native_contact_without_ordinary_completion_refuses(history, tmp_path):
    task = history.retained_task
    contacts = ExternalNativeEffectContactStore(plane=history.plane,
        execution_plan=_identity(history.plan, "execution_plan_id"),
        visibility_ceiling=VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for row in task.outputs)),
        outcome_access=OutcomeAccess.OUTCOME_BLIND)
    contacts.begin(NativeEffectContact(history.index.run_id, task.task_id, history.candidate.attempt_id,
        _identity(history.plan, "execution_plan_id"), _identity(task, "task_id"), history.plan.implementation_commit, (), ()))
    repository = _repository(tmp_path / "native.sqlite")
    before = _census(history.root)
    try:
        with pytest.raises((RunRecoveryError, ValueError), match="native|contact"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id) == ()
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


@pytest.mark.parametrize("manifest_only", (False, True))
def test_unindexed_native_contact_or_sidecar_refuses_before_projection(history, tmp_path, manifest_only):
    contacts = ExternalNativeEffectContactStore(plane=history.plane,
        execution_plan=_identity(history.plan, "execution_plan_id"),
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    task_id = "software.unindexed-native-task"
    contacts.begin(NativeEffectContact(history.index.run_id, task_id, "software.unindexed-native-attempt",
        _identity(history.plan, "execution_plan_id"), replace(_identity(history.retained_task, "task_id"), object_id=task_id),
        history.plan.implementation_commit, (), ()))
    if manifest_only:
        (history.root / contacts._path(history.index.run_id, task_id)).unlink()
    repository = _repository(tmp_path / "foreign-contact.sqlite")
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError, match="orphaned native root"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id) == ()
        assert history.recovery.read_terminal(history.index) is None
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_existing_execution_lock_refuses_even_for_pure_plan(history, tmp_path):
    owner = ExternalNativeEffectContactStore(plane=history.plane,
        execution_plan=_identity(history.plan, "execution_plan_id"),
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    repository = _repository(tmp_path / "locked.sqlite")
    try:
        with owner.execution_lock(history.index.run_id):
            before = _census(history.root)
            with pytest.raises(RunRecoveryError, match="another execution"):
                _close(history, repository)
            assert _census(history.root) == before
            assert repository.attempts(history.index.run_id) == ()
    finally:
        repository.engine.dispose()


def test_running_catalog_inserted_during_preflight_refuses_before_projection(history, tmp_path, monkeypatch):
    repository = _repository(tmp_path / "raced.sqlite")
    repository.register_run(history.index.run_id, history.plan.fingerprint())
    read = history.recovery.reconstruct_execution_resource_envelope

    def changed(**arguments):
        result = read(**arguments)
        repository.start_attempt(run_id=history.index.run_id, task_id=history.retained_task.task_id,
            attempt_id=history.candidate.attempt_id, lease_id="lease.raced", owner_id="owner.raced", expires_epoch_seconds=1)
        return result

    monkeypatch.setattr(history.recovery, "reconstruct_execution_resource_envelope", changed)
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError, match="running"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id)[0].disposition.value == "RUNNING"
        assert history.recovery.read_terminal(history.index) is None
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_retained_terminal_cannot_add_a_block_for_an_unused_task(history, tmp_path):
    unused = next(row for row in history.plan.tasks if row.task_id != history.retained_task.task_id)
    failed = OperationalAttempt(history.candidate.attempt_id, history.index.run_id, history.retained_task.task_id,
        1, TaskAttemptDisposition.FAILED, history.retained_event.reason_codes[0], None, None)
    invented = OperationalAttempt(history.index.run_id + "." + unused.task_id + ".block-001",
        history.index.run_id, unused.task_id, 1, TaskAttemptDisposition.BLOCKED, "dependency-failed", None, None)
    history.recovery.record_terminal(history.index, status=OperationalStatus.FAILED,
        attempts=(failed, invented), receipts=())
    repository = _repository(tmp_path / "unretained-terminal.sqlite")
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError, match="unretained"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id) == ()
        with pytest.raises(NoResultFound):
            repository.run_status(history.index.run_id)
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def test_conflicting_private_catalog_candidate_refuses_before_other_rows_are_restored(history, tmp_path):
    repository = _repository(tmp_path / "conflicting.sqlite")
    repository.register_run(history.index.run_id, history.plan.fingerprint())
    repository.start_attempt(run_id=history.index.run_id, task_id=history.retained_task.task_id,
        attempt_id=history.candidate.attempt_id, lease_id="lease.old", owner_id="owner.old", expires_epoch_seconds=1)
    repository.fail_attempt(history.candidate.attempt_id, "different-failure")
    attempts = repository.attempts(history.index.run_id)
    before = _census(history.root)
    try:
        with pytest.raises(RunRecoveryError, match="catalog differs"):
            _close(history, repository)
        assert repository.attempts(history.index.run_id) == attempts
        assert history.recovery.read_terminal(history.index) is None
        assert _census(history.root) == before
    finally:
        repository.engine.dispose()


def _seed_native_subwork(monkeypatch, *, unknown_sibling=False):
    """One disclosed software leaf completion and one selected unentered leaf."""
    from tests.runtime_platform.test_native_subwork import ExposedInput

    original = ExternalNativeEffectContactStore.begin
    selected = []

    def begin(contacts, parent):
        original(contacts, parent)
        if parent.task_id != "prepare" or contacts._task_stores is not None:
            return
        source_files = (("src/disclosed_software.py", "4" * 64),)
        provenance = NumericalProducingProvenance(
            '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
            "5" * 64, source_files, sha256(canonical_json_bytes(source_files)).hexdigest(), parent.implementation_commit, False)
        configuration, stream = ExposedInput("software.config", "fixed"), ExposedInput("software.stream", "fixed")
        inputs = []
        for identity, record in ((ObjectIdentity.from_record(configuration.selected_id, configuration), configuration),
                (ObjectIdentity.from_record(stream.selected_id, stream), stream), (provenance.identity, provenance)):
            written = contacts.plane.write(ArtifactWriteRequest(identity.object_id,
                "software-native-inputs/" + identity.object_id + ".json", record.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", "software.native-inputs", "software-native-inputs",
                record.canonical_bytes(), contacts.visibility_ceiling, (), contacts.outcome_access))
            from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
            inputs.append(decode_artifact_manifest(contacts.plane.root.resolve(
                written.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
        definition = NativeSubworkDefinition("software.leaf-completed", "software.operation", parent,
            ObjectIdentity.from_record(configuration.selected_id, configuration), (provenance.identity,),
            provenance.code_sources_sha256, provenance.dependency_lock_sha256,
            tuple(sorted(row.materialization.materialization_id for row in inputs)),
            (ObjectIdentity.from_record(stream.selected_id, stream),),
            (NativeSubworkOutput("software.output", "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
                ArtifactProfile.RAW_SOURCE_BYTES, "text/plain"),))
        unentered = replace(definition, subwork_id="software.leaf-unentered")
        store = ExternalNativeSubworkStore(plane=contacts.plane, parent_contacts=contacts, parent_contact=parent)
        roster = NativeSubworkRoster("selected.native-subwork", parent, (definition.identity, unentered.identity))
        store.freeze_roster(roster, definitions=(definition, unentered))
        entry = store.begin(definition, tuple(inputs))
        store.contact(entry)
        payload = b"disclosed software output"
        store.publish_output(entry, "software.output", iter((payload,)), maximum_bytes=len(payload),
            maximum_chunk_bytes=len(payload), expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
        store.complete(entry, operational_status=OperationalStatus.SUCCEEDED, cost=InquiryCost(None, Decimal(0), None),
            cost_scope="software custody control", consumed_streams=definition.streams, unknown_streams=(), reason_codes=())
        if unknown_sibling:
            unknown = store.begin(unentered, tuple(inputs))
            store.contact(unknown)
        selected.append((store, roster, definition))

    monkeypatch.setattr(ExternalNativeEffectContactStore, "begin", begin)
    return selected


def test_real_disclosed_native_completion_and_ordinary_success_survive_read_only_replay(tmp_path, monkeypatch):
    from tests.recovery_support import _public_failed_history

    selected = _seed_native_subwork(monkeypatch)
    value = _public_failed_history(tmp_path, monkeypatch)
    value.retained_envelope = value.envelope
    root = Path(value.plane.root.contract.canonical_path)
    before = _census(root)
    repository = _repository(tmp_path / "native-completed.sqlite")
    calls = tuple(value.executor.calls)
    try:
        terminal = _close(value, repository)
        assert terminal == value.terminal
        assert set(terminal.completed_task_ids) == {"prepare", "develop-b"}
        assert tuple(value.executor.calls) == calls
        assert repository.run_status(value.index.run_id) is OperationalStatus.FAILED
        assert _census(root) == before
    finally:
        repository.engine.dispose()
    store, roster, definition = selected[0]
    roster_path = root / store._roster_path(roster.parent_contact, roster.roster_id)
    receipt_path = root / store.receipts._relative_path(*store._receipt_locator(definition))
    ordinary = next(row for row in value.receipts if row.task_id == "develop-b")
    output_path = root / ordinary.output_materializations[0].relative_path
    # Every refusal occurs against real frozen selected custody. The test
    # restores its synthetic fixture after each isolated corruption.
    for number, (paths, corrupt) in enumerate(((tuple((roster_path, roster_path.with_name(roster_path.name + ".manifest.json"))), False),
            ((roster_path,), False), ((receipt_path, receipt_path.with_name(receipt_path.name + ".manifest.json")), False),
            ((output_path,), True))):
        saved = [(path, path.read_bytes(), path.stat()) for path in paths]
        private = _repository(tmp_path / f"native-refusal-{number}.sqlite")
        try:
            for path in paths:
                if corrupt:
                    path.write_bytes(b"changed ordinary output")
                else:
                    path.unlink()
            changed = _census(root)
            with pytest.raises((RunRecoveryError, ArtifactIdentityConflict, ValueError)):
                _close(value, private)
            assert private.attempts(value.index.run_id) == ()
            assert _census(root) == changed
            assert tuple(value.executor.calls) == calls
        finally:
            private.engine.dispose()
            for path, payload, stat in saved:
                path.write_bytes(payload)
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert _census(root) == before


@pytest.mark.parametrize("unknown_sibling", (False, True))
def test_failed_history_distinguishes_known_publication_gap_and_unknown_sibling(tmp_path, monkeypatch, unknown_sibling):
    from tests.recovery_support import _public_failed_history

    selected = _seed_native_subwork(monkeypatch, unknown_sibling=unknown_sibling)
    value = _public_failed_history(tmp_path, monkeypatch)
    value.retained_envelope = value.envelope
    store, _roster, definition = selected[0]
    root = Path(value.plane.root.contract.canonical_path)
    receipt = root / store.receipts._relative_path(*store._receipt_locator(definition))
    receipt.unlink()
    receipt.with_name(receipt.name + ".manifest.json").unlink()
    before = _census(root)
    calls = tuple(value.executor.calls)
    repository = _repository(tmp_path / "pending-native-publication.sqlite")
    monkeypatch.setattr(ExternalNativeSubworkStore, "recover", lambda *args, **kwargs: pytest.fail(
        "failed-history read must not publish a missing native receipt"))
    try:
        reason = "contacted child without a known return" if unknown_sibling else "known native return.*incomplete durable publication"
        with pytest.raises(RunRecoveryError, match=reason):
            _close(value, repository)
        assert repository.attempts(value.index.run_id) == ()
        assert _census(root) == before and tuple(value.executor.calls) == calls
    finally:
        repository.engine.dispose()
