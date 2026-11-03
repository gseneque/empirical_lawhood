# SPDX-License-Identifier: MPL-2.0
"""Literal in-process native-boundary controls; no API, solver or acquisition."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_parent_finalization import (
    NativeParentFinalizationPending, authenticate_native_parent_return, inspect_native_parent_return,
)
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkPipeService, NativeSubworkReply, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_effects import NativeEntryRefused
from empirical_lawhood.runtime import native_subwork as native_owner
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkCallEntry, NativeSubworkCallReturn, NativeSubworkObservationPublicationError,
    NativeSubworkReceiptPublicationPending, NativeSubworkRoster, NativeSubworkState,
    NativeSubworkUncertainContact, invoke_native_subwork,
)
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from tests.runtime_platform.test_native_subwork import _complete, _publish, _selected
from tests.runtime_platform.test_worker_preflight import _case


ENTRY_TIME = "2026-10-21T01:00:00.123456Z"
RETURN_TIME = "2026-10-21T01:00:02.654321Z"


@pytest.fixture
def selected(tmp_path):
    plane, bundle, _runner, context, contract, parent = _case(tmp_path, native=True)
    definition, = contract.native_definitions
    definitions = tuple(replace(definition, subwork_id="exposed.work." + str(index)) for index in range(3))
    roster = NativeSubworkRoster("selected.native-subwork", parent, tuple(row.identity for row in definitions))
    contract = replace(contract, native_work=PreparedNativeWork(parent, ("exposed.unit",),
        ("exposed.slot",), definitions, (roster,)))
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    contacts.begin(parent)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=bundle.manifests, prepared_invocation=contract)
    store.freeze_roster(roster, definitions=definitions)
    try:
        yield store, definitions, bundle, replace(context, prepared_invocation=contract), contract
    finally:
        bundle.close()


def _fresh(store, *, completed_only=False, before_contact=None):
    parent = store.parent_contact
    plane = ExternalArtifactPlane(store.plane.root)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=store.visibility, outcome_access=store.access)
    return ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=store.parent_inputs, completed_only=completed_only, before_contact=before_contact)


def _clock(monkeypatch):
    readings = iter((ENTRY_TIME, RETURN_TIME))
    monkeypatch.setattr(native_owner, "native_call_utc_now", lambda: next(readings))


def _snapshot(store):
    root = Path(store.plane.root.contract.canonical_path)
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _pipe(store, context, tmp_path):
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, value):
            if type(value) is NativeSubworkRequest:
                service.handle(value, self)
            else:
                self.reply = value
        def recv(self):
            return self.reply
    return PipeNativeSubworkProgress(Connection()), service


@pytest.mark.parametrize("route", ("direct", "pipe"))
def test_raw_return_facts_precede_output_failure_and_survive_fresh_reader(selected, tmp_path, monkeypatch, route):
    store, definitions, _bundle, context, contract = selected
    first = definitions[0]
    port, service = (store, None) if route == "direct" else _pipe(store, context, tmp_path)
    parent_bytes = store.parent_contact.canonical_bytes()
    _clock(monkeypatch)
    try:
        entry = port.begin(first)
        port.contact(entry)
        assert store.inspect(first).has_uncertain_contact
        calls = []
        def native():
            calls.append("actual-call")
            assert store.inspect(first).call_entry.entered_at_utc == ENTRY_TIME
            assert store.inspect(first).call_return is None
            return b"actual-return"
        assert invoke_native_subwork(port, entry, native) == b"actual-return"
        raw = store.inspect(first)
        assert calls == ["actual-call"]
        assert raw.state is NativeSubworkState.UNKNOWN_COMPLETION and raw.completion is None
        assert raw.native_return_status is OperationalStatus.SUCCEEDED
        assert not raw.has_uncertain_contact
        assert raw.call_entry.invocation == contract.identity
        assert raw.call_return.returned_at_utc == RETURN_TIME and raw.call_return.error_type is None
        assert store.read_prepared_invocation(store.parent_contact) == contract
        assert store.parent_contact.canonical_bytes() == parent_bytes
        def failed_publication(*args, **kwargs):
            raise OSError("disclosed output interruption after actual native return")
        monkeypatch.setattr(store, "publish_output", failed_publication)
        with pytest.raises(OSError, match="output interruption"):
            store.publish_output(entry, first.outputs[0].output_id, (b"bytes",), maximum_bytes=5)
        fresh = _fresh(store)
        recovered = fresh.inspect(first)
        assert recovered == raw and recovered.receipt is None
        before = _snapshot(store)
        for action in (lambda: fresh.recover(first), lambda: fresh.begin(first)):
            with pytest.raises(NativeSubworkReceiptPublicationPending, match="no automatic retry"):
                action()
            assert _snapshot(store) == before
    finally:
        if service is not None:
            service.close()


@pytest.mark.parametrize("error_type", (ValueError, ArithmeticError, MemoryError))
def test_actual_native_error_time_is_retained_before_failure_classification(selected, monkeypatch, error_type):
    store, definitions, _bundle, _context, _contract = selected
    first = definitions[0]
    _clock(monkeypatch)
    entry = store.begin(first)
    store.contact(entry)
    def native():
        raise error_type("private native diagnostic is not a fact field")
    with pytest.raises(error_type, match="private native"):
        invoke_native_subwork(store, entry, native)
    raw = store.inspect(first)
    assert raw.native_return_status is OperationalStatus.FAILED and not raw.has_uncertain_contact
    assert raw.completion is raw.receipt is None
    assert raw.call_return.error_type == error_type.__name__
    assert raw.call_return.returned_at_utc == RETURN_TIME
    assert "private native" not in raw.call_return.canonical_bytes().decode()
    complete = _complete(store, entry, failed=True, unknown_stream=True)
    assert complete.call_return == raw.call_return
    assert _fresh(store).recover(first) == complete
    fact_ids = {store._manifest(store._root(first) + "/" + name + ".json").materialization.materialization_id
        for name in ("call-entry", "call-return")}
    assert fact_ids.issubset(complete.receipt.input_materialization_ids)


def test_post_return_failure_cannot_publish_a_native_error_completion(selected, monkeypatch):
    store, definitions, _bundle, _context, _contract = selected
    first = definitions[0]
    _clock(monkeypatch)
    entry = store.begin(first)
    store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"returned")
    before = _snapshot(store)
    with pytest.raises(ValueError, match="later publication failure"):
        _complete(store, entry, failed=True, unknown_stream=True)
    assert _snapshot(store) == before
    assert store.inspect(first).completion is None


@pytest.mark.parametrize("raw_failure", (None, "python-error", "process-exit"))
@pytest.mark.parametrize("published", (False, True))
def test_known_raw_return_without_completion_remains_pending_without_replay(
        selected, monkeypatch, raw_failure, published):
    store, definitions, _bundle, _context, contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0]); store.contact(entry)
    if raw_failure == "python-error":
        def native():
            raise ValueError("disclosed actual native error")
        with pytest.raises(ValueError, match="actual native error"):
            invoke_native_subwork(store, entry, native)
    elif raw_failure == "process-exit":
        store.call_entry(entry, at_utc=ENTRY_TIME)
        store.call_return(entry, at_utc=RETURN_TIME, return_code=-9)
    else:
        invoke_native_subwork(store, entry, lambda: b"actual returned bytes")
    if published:
        _publish(store, entry, b"FALSIFIED")
    retained = store.inspect(definitions[0])
    assert retained.native_return_status is (OperationalStatus.FAILED if raw_failure else OperationalStatus.SUCCEEDED)
    assert not retained.has_uncertain_contact
    before = _snapshot(store)
    for _ in range(2):
        observed = inspect_native_parent_return(store=_fresh(store, completed_only=True), work=contract.native_work)
        assert observed.pending_publication_definition_ids == (definitions[0].identity,)
        assert observed.uncertain_contact_definition_ids == ()
        assert observed.uncontacted_definition_ids == tuple(row.identity for row in definitions[1:])
        assert observed.failed_return_definition_ids == ((definitions[0].identity,) if raw_failure else ())
        assert observed.operational_status is None and _snapshot(store) == before
        with pytest.raises(NativeParentFinalizationPending, match="known native return.*incomplete durable") as pending:
            authenticate_native_parent_return(store=_fresh(store), work=contract.native_work)
        assert ("error/exit observations" in str(pending.value)) == (raw_failure is not None)
        assert _snapshot(store) == before
        assert store.inspect(definitions[0]) == retained
        with pytest.raises(NativeSubworkReceiptPublicationPending, match="no automatic retry"):
            _fresh(store).recover(definitions[0])
        assert _snapshot(store) == before
    assert retained.completion is None and retained.receipt is None
    assert retained.call_return is not None


def test_genuinely_unknown_sibling_precedes_known_raw_return_missing_products(selected, monkeypatch):
    store, definitions, _bundle, _context, contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0]); store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"actual returned bytes")
    unknown = store.begin(definitions[1]); store.contact(unknown)
    seen = []
    original = ExternalNativeSubworkStore.inspect
    def inspect(reader, definition):
        seen.append(definition.identity)
        return original(reader, definition)
    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inspect)
    before = _snapshot(store)
    with pytest.raises(NativeSubworkUncertainContact, match="without a durable known return"):
        authenticate_native_parent_return(store=_fresh(store), work=contract.native_work)
    assert seen == [row.identity for row in definitions]
    assert _snapshot(store) == before


def test_parent_inspection_refuses_a_late_authentic_conditional_unknown_sibling(selected, monkeypatch):
    store, definitions, _bundle, _context, contract = selected
    _clock(monkeypatch)
    carrier = store.begin(definitions[0]); store.contact(carrier)
    invoke_native_subwork(store, carrier, lambda: b"actual raw return before conditional publication")
    child = replace(definitions[0], subwork_id="exposed.work.late", roster_id="conditional.late")
    roster = NativeSubworkRoster(child.roster_id, store.parent_contact, (child.identity,), definitions[0].identity)
    original = ExternalNativeSubworkStore.inspect
    added = []
    def inspect(reader, definition):
        observed = original(reader, definition)
        if definition == definitions[-1] and not added:
            added.append(True)
            # This is the original live creator's ordinary conditional publish,
            # not a fabricated roster or a write through the inspection store.
            store.freeze_roster(roster, carrier, definitions=(child,))
            entry = store.begin(child); store.contact(entry)
            added.append(_snapshot(store))
        return observed
    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inspect)
    monkeypatch.setattr(ExternalNativeSubworkStore, "recover", lambda *args, **kwargs: pytest.fail(
        "parent inspection must not recover publication"))
    with pytest.raises(ValueError, match="changed its exact selected roster census"):
        inspect_native_parent_return(store=_fresh(store), work=contract.native_work)
    assert added[0] is True and _snapshot(store) == added[1]
    assert original(store, child).has_uncertain_contact


@pytest.mark.parametrize("failed_boundary", ("call_entry", "call_return"))
def test_fact_publication_failure_never_becomes_native_error_or_retry(selected, monkeypatch, failed_boundary):
    store, definitions, _bundle, _context, _contract = selected
    first = definitions[0]
    _clock(monkeypatch)
    entry = store.begin(first)
    store.contact(entry)
    calls = []
    def interrupted(*args, **kwargs):
        raise ValueError("disclosed fact publication interruption")
    monkeypatch.setattr(store, failed_boundary, interrupted)
    with pytest.raises(NativeSubworkObservationPublicationError, match="publication was not acknowledged"):
        invoke_native_subwork(store, entry, lambda: calls.append("native"))
    assert calls == ([] if failed_boundary == "call_entry" else ["native"])
    retained = _fresh(store).inspect(first)
    assert retained.state is NativeSubworkState.UNKNOWN_COMPLETION
    assert retained.has_uncertain_contact and retained.native_return_status is None
    assert retained.call_return is None and retained.completion is None
    with pytest.raises(NativeSubworkUncertainContact, match="no automatic retry"):
        _fresh(store).recover(first)


def test_lost_return_acknowledgement_preserves_durable_actual_return(selected, monkeypatch):
    store, definitions, _bundle, _context, _contract = selected
    first = definitions[0]
    _clock(monkeypatch)
    entry = store.begin(first)
    store.contact(entry)
    original = store.call_return
    calls = []
    def lost_acknowledgement(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("disclosed acknowledgement interruption after durable fact")
    monkeypatch.setattr(store, "call_return", lost_acknowledgement)
    with pytest.raises(NativeSubworkObservationPublicationError, match="not acknowledged"):
        invoke_native_subwork(store, entry, lambda: calls.append("actual-return"))
    retained = _fresh(store).inspect(first)
    assert calls == ["actual-return"]
    assert retained.call_return.returned_at_utc == RETURN_TIME
    assert retained.call_return.error_type is None
    assert retained.completion is None and retained.receipt is None
    assert retained.native_return_status is OperationalStatus.SUCCEEDED and not retained.has_uncertain_contact


@pytest.mark.parametrize("route", ("direct", "pipe"))
def test_each_later_leaf_rechecks_current_permission_before_contact(selected, tmp_path, monkeypatch, route):
    store, definitions, _bundle, context, _contract = selected
    permitted = True
    checked = []
    def guard(definition):
        checked.append(definition.identity)
        if not permitted:
            raise NativeEntryRefused("disclosed current authority or original lease refusal")
    store.before_contact = guard
    port, service = (store, None) if route == "direct" else _pipe(store, context, tmp_path)
    try:
        first = port.begin(definitions[0])
        port.contact(first)
        first_bytes = _snapshot(store)
        later = port.begin(definitions[1])
        permitted = False
        before = _snapshot(store)
        with pytest.raises(NativeEntryRefused, match="authority or original lease"):
            port.contact(later)
        assert checked == [row.identity for row in definitions[:2]]
        assert _snapshot(store) == before
        assert store.inspect(definitions[1]).state is NativeSubworkState.BEGUN
        permitted = True
        port.contact(later)
        assert checked == [definitions[0].identity, definitions[1].identity, definitions[1].identity]
        assert store.inspect(definitions[1]).state is NativeSubworkState.UNKNOWN_COMPLETION
        assert all(_snapshot(store)[name] == value for name, value in first_bytes.items())
    finally:
        if service is not None:
            service.close()


def test_worker_proxy_preserves_native_entry_refusal_type():
    class Connection:
        def send(self, value):
            self.sequence = value.sequence
        def recv(self):
            return NativeSubworkReply(self.sequence, error_type="NativeEntryRefused", error_message="live lease refused")
    with pytest.raises(NativeEntryRefused, match="live lease refused"):
        PipeNativeSubworkProgress(Connection())._call("contact", 1)


@pytest.mark.parametrize("route", ("direct", "pipe"))
def test_call_boundary_rechecks_after_contact_but_return_and_publication_need_no_new_grant(
        selected, tmp_path, monkeypatch, route):
    store, definitions, _bundle, context, _contract = selected
    permitted = True
    checked = []
    calls = []
    def guard(definition):
        checked.append(definition.identity)
        if not permitted:
            raise NativeEntryRefused("disclosed grant or lease expired after contact")
    store.before_contact = guard
    port, service = (store, None) if route == "direct" else _pipe(store, context, tmp_path)
    try:
        entry = port.begin(definitions[0])
        port.contact(entry)
        before = _snapshot(store)
        permitted = False
        with pytest.raises(NativeEntryRefused, match="expired after contact"):
            invoke_native_subwork(port, entry, lambda: calls.append("native"))
        assert calls == [] and _snapshot(store) == before
        assert store.inspect(definitions[0]).call_entry is None
        permitted = True
        _clock(monkeypatch)
        assert invoke_native_subwork(port, entry, lambda: calls.append("native")) is None
        permitted = False
        port.publish_output(entry, "result.output.native", (b"FALSIFIED",), maximum_bytes=9,
            expected_size_bytes=9, expected_physical_sha256=sha256(b"FALSIFIED").hexdigest())
        _complete(port, entry)
        assert calls == ["native"]
        assert checked == [definitions[0].identity] * 3
        assert _fresh(store).recover(definitions[0]).call_return.returned_at_utc == RETURN_TIME
    finally:
        if service is not None:
            service.close()


def test_actual_call_reauthenticates_retained_contact_before_observation(selected):
    store, definitions, _bundle, _context, _contract = selected
    entry = store.begin(definitions[0])
    store.contact(entry)
    path = store.plane.root.resolve(store._root(definitions[0]) + "/contact.json", for_write=False)
    path.unlink()
    Path(str(path) + ".manifest.json").unlink()
    calls = []
    with pytest.raises(NativeSubworkObservationPublicationError, match="entry observation"):
        invoke_native_subwork(store, entry, lambda: calls.append("native"))
    assert calls == [] and entry.call_entry_manifest is None


def test_completed_only_fact_reads_need_no_new_execution_guard_and_cannot_mutate(selected, monkeypatch):
    store, definitions, _bundle, _context, _contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0])
    store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"FALSIFIED")
    _publish(store, entry, b"FALSIFIED")
    complete = _complete(store, entry)
    def forbidden(*args, **kwargs):
        raise AssertionError("completed publication requested new execution or mutation")
    readonly = _fresh(store, completed_only=True, before_contact=forbidden)
    before = _snapshot(store)
    with readonly.plane.verification_scope() as scoped_plane:
        readonly.plane = scoped_plane
        assert readonly.inspect(definitions[0]) == complete
        for action in (lambda: readonly.contact(entry),
                lambda: readonly.call_entry(entry, at_utc=ENTRY_TIME),
                lambda: readonly.call_return(entry, at_utc=RETURN_TIME)):
            with pytest.raises(NativeSubworkUncertainContact, match="completed-only"):
                action()
    assert _snapshot(store) == before


@pytest.mark.parametrize("route", ("direct", "pipe"))
@pytest.mark.parametrize("return_code", (-9, 0, 17))
def test_literal_process_return_codes_retain_exact_status_without_fictional_error_type(
        selected, tmp_path, route, return_code):
    store, definitions, _bundle, context, _contract = selected
    port, service = (store, None) if route == "direct" else _pipe(store, context, tmp_path)
    try:
        entry = port.begin(definitions[0])
        port.contact(entry)
        port.call_entry(entry, at_utc=ENTRY_TIME)
        port.call_return(entry, at_utc=RETURN_TIME, return_code=return_code)
        observed = store.inspect(definitions[0])
        assert observed.call_return.return_code == return_code
        assert observed.call_return.error_type is None
        assert observed.completion is None
        assert observed.native_return_status is (OperationalStatus.SUCCEEDED if return_code == 0
            else OperationalStatus.FAILED)
        assert not observed.has_uncertain_contact and observed.receipt is None
        if return_code == 0:
            _publish(port, entry, b"FALSIFIED")
        completed = _complete(port, entry, failed=return_code != 0, unknown_stream=return_code != 0)
        assert _fresh(store).recover(definitions[0]) == completed
    finally:
        if service is not None:
            service.close()


def test_missing_original_invocation_refuses_observed_fact_join(selected, monkeypatch):
    store, definitions, _bundle, _context, _contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0])
    store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"returned")
    path = store.plane.root.resolve(store._invocation_path(store.parent_contact), for_write=False)
    path.unlink()
    Path(str(path) + ".manifest.json").unlink()
    with pytest.raises(ValueError, match="original prepared invocation"):
        _fresh(store).inspect(definitions[0])


@pytest.mark.parametrize("field", ("definition", "contact", "invocation"))
def test_authenticated_fact_cannot_substitute_same_schema_identity(selected, field):
    store, definitions, _bundle, _context, contract = selected
    first = definitions[0]
    entry = store.begin(first)
    store.contact(entry)
    original = NativeSubworkCallEntry(first.identity, store._contact_identity(entry), contract.identity, ENTRY_TIME)
    foreign = replace(getattr(original, field), object_id="foreign." + field, object_fingerprint="f" * 64)
    substitute = replace(original, **{field: foreign})
    # Authentic storage and matching declared lineage do not excuse substituted
    # embedded operands. This is disclosed corruption, not a producing fact.
    store._write_control(first, "call-entry", substitute,
        store._parents(original.definition, original.contact, original.invocation))
    with pytest.raises(ValueError, match="substitutes its exact definition"):
        _fresh(store).inspect(first)


def test_raw_return_without_original_entry_never_supplies_a_completion(selected, monkeypatch):
    store, definitions, _bundle, _context, _contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0])
    store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"returned")
    path = store.plane.root.resolve(store._root(definitions[0]) + "/call-entry.json", for_write=False)
    path.unlink()
    Path(str(path) + ".manifest.json").unlink()
    with pytest.raises(NativeSubworkUncertainContact, match="lost its original call entry"):
        _fresh(store).inspect(definitions[0])


def test_store_rejects_original_invocation_for_another_parent_attempt(selected):
    store, _definitions, _bundle, _context, contract = selected
    with pytest.raises(ValueError, match="changes its exact parent"):
        ExternalNativeSubworkStore(plane=store.plane, parent_contacts=store.parent_contacts,
            parent_contact=replace(store.parent_contact, attempt_id="foreign.attempt"),
            prepared_invocation=contract)


@pytest.mark.parametrize("failed", (False, True))
def test_prior_completion_does_not_infer_missing_call_times(tmp_path, failed):
    store, definition, inputs = _selected(tmp_path)
    entry = store.begin(definition, inputs)
    store.contact(entry)
    _publish(store, entry, b"FALSIFIED")
    prior = _complete(store, entry, failed=failed)
    assert prior.call_entry is None and prior.call_return is None
    assert prior.native_return_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    assert not prior.has_uncertain_contact
    assert _fresh(store).recover(definition) == prior


def test_fact_records_require_exact_typed_joins_and_utc(selected, monkeypatch):
    store, definitions, _bundle, _context, contract = selected
    _clock(monkeypatch)
    entry = store.begin(definitions[0])
    store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"returned")
    retained = store.inspect(definitions[0])
    for name in ("definition", "contact", "invocation"):
        with pytest.raises(ValueError, match="exact definition"):
            replace(retained.call_entry, **{name: contract.execution_plan})
    with pytest.raises(ValueError, match="UTC"):
        replace(retained.call_entry, entered_at_utc="2026-10-21T01:00:00+00:00")
    with pytest.raises(ValueError, match="exact observed entry"):
        replace(retained.call_return, entry=contract.identity)
    for code in (True, False, "17", 2**31, -(2**31)-1):
        with pytest.raises(ValueError, match="actual integer process code"):
            replace(retained.call_return, return_code=code)
    for record in (retained.call_entry, retained.call_return):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
        assert sha256(record.canonical_bytes()).hexdigest() == record.fingerprint()
    assert type(retained.call_entry) is NativeSubworkCallEntry
    assert type(retained.call_return) is NativeSubworkCallReturn
    assert ObjectIdentity.from_record(store._id(definitions[0], "call-entry"), retained.call_entry) == retained.call_return.entry
