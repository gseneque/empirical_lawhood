# SPDX-License-Identifier: MPL-2.0
"""Current parent publication from exposed completed custody; no native science."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_parent_finalization import (
    NativeParentFinalizationPending, authenticate_native_parent_return, completed_native_parent_scope,
    inspect_native_parent_return,
)
from empirical_lawhood.infrastructure.native_subwork_ipc import (
    NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from tests.runtime_platform.test_native_subwork import _complete, _publish, _selected, _store
from tests.runtime_platform.test_worker_preflight import _case


def _work(store, first):
    definitions = (first, replace(first, subwork_id="forecast.three"), replace(first, subwork_id="forecast.two"))
    return PreparedNativeWork(first.parent_contact, ("exposed.unit",), ("exposed.slot",), definitions,
        (store.read_roster(first.parent_contact),))


def _finish(store, definition, *, failed=False):
    entry = store.begin(definition)
    store.contact(entry)
    _publish(store, entry, b"UNEVALUABLE" if failed else b"FALSIFIED")
    return _complete(store, entry, failed=failed)


def _census(store):
    root = Path(store.plane.root.contract.canonical_path)
    return {str(path.relative_to(root)): (path.stat().st_mtime_ns, path.read_bytes())
        for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize("failed", (False, True))
def test_whole_current_census_preserves_exact_known_returns_without_live_creator(tmp_path, failed):
    store, first, inputs = _selected(tmp_path)
    work = _work(store, first)
    before = tuple(_finish(store, row, failed=failed and index == 1)
        for index, row in enumerate(work.definitions))
    fresh = _store(store.plane, first.parent_contact, inputs)
    snapshot = _census(store)
    observed = authenticate_native_parent_return(store=fresh, work=work)
    assert observed.inspections == before and observed.pending_definition_ids == ()
    assert observed.operational_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    assert _census(store) == snapshot and not fresh.parent_contacts.is_live_creator(first.parent_contact)
    assert inspect_native_parent_return(store=fresh, work=work) == observed
    assert _census(store) == snapshot


@pytest.mark.parametrize("failed", (False, True))
def test_uncontacted_units_remain_in_denominator_and_never_become_success(tmp_path, failed):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    _finish(store, first, failed=failed)
    store.begin(work.definitions[1])
    before = _census(store)
    observed = authenticate_native_parent_return(store=store, work=work)
    assert tuple(row.state for row in observed.inspections) == (
        NativeSubworkState.COMPLETED, NativeSubworkState.BEGUN, NativeSubworkState.NOT_ENTERED)
    assert observed.pending_definition_ids == tuple(row.identity for row in work.definitions[1:])
    assert observed.operational_status is (OperationalStatus.FAILED if failed else None)
    assert _census(store) == before


def test_read_only_parent_census_keeps_missing_receipt_and_unknown_sibling_separate(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    entry = store.begin(first); store.contact(entry); _publish(store, entry, b"UNEVALUABLE")
    monkeypatch.setattr(store.receipts, "commit", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("interrupted")))
    with pytest.raises(OSError):
        _complete(store, entry, failed=True)
    unknown = store.begin(work.definitions[1]); store.contact(unknown)
    def forbidden(*args, **kwargs):
        pytest.fail("a current read must not finalize child receipt publication")
    monkeypatch.setattr(type(store), "recover", forbidden)
    before = _census(store)
    observed = inspect_native_parent_return(store=store, work=work)
    assert observed.operational_status is None
    assert observed.pending_publication_definition_ids == (first.identity,)
    assert observed.failed_return_definition_ids == (first.identity,)
    assert observed.uncertain_contact_definition_ids == (work.definitions[1].identity,)
    assert observed.uncontacted_definition_ids == (work.definitions[2].identity,)
    assert observed.inspections[0].completion is not None and observed.inspections[0].receipt is None
    assert _census(store) == before


def test_read_only_parent_census_refuses_bytes_changed_after_last_child_inspection(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    completed = _finish(store, first)
    output, = completed.outputs
    path = store.plane.root.resolve(output.materialization.relative_path, for_write=False)
    original = type(store).inspect
    def inspect(reader, definition):
        observed = original(reader, definition)
        if definition == work.definitions[-1]:
            path.write_bytes(b"X" * output.materialization.size_bytes)
        return observed
    monkeypatch.setattr(type(store), "inspect", inspect)
    with pytest.raises(ArtifactIdentityConflict):
        inspect_native_parent_return(store=store, work=work)


def test_unknown_contacted_sibling_refuses_even_after_known_failed_return_and_checks_full_census(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    _finish(store, first, failed=True)
    entry = store.begin(work.definitions[1]); store.contact(entry)
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    original = ExternalNativeSubworkStore.inspect
    seen = []
    def inspect(self, definition):
        seen.append(definition.identity)
        return original(self, definition)
    monkeypatch.setattr(ExternalNativeSubworkStore, "inspect", inspect)
    before = _census(store)
    with pytest.raises(NativeSubworkUncertainContact, match="without a durable known return"):
        authenticate_native_parent_return(store=store, work=work)
    assert seen == [row.identity for row in work.definitions] and _census(store) == before


def test_carrier_unknown_refuses_even_when_all_conditional_leaves_completed(tmp_path):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    carrier = store.begin(first); store.contact(carrier)
    child = replace(first, subwork_id="forecast.one.segment", roster_id="conditional.segments")
    roster = NativeSubworkRoster(child.roster_id, first.parent_contact, (child.identity,), first.identity)
    store.freeze_roster(roster, carrier, definitions=(child,))
    _finish(store, child)
    for definition in work.definitions[1:]:
        _finish(store, definition)
    with pytest.raises(NativeSubworkUncertainContact, match="without a durable known return"):
        authenticate_native_parent_return(store=store, work=work)


def test_known_conditional_failure_cannot_hide_unknown_descendant(tmp_path):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    carrier = store.begin(first); store.contact(carrier)
    child = replace(first, subwork_id="forecast.one.segment", roster_id="conditional.segments")
    store.freeze_roster(NativeSubworkRoster(child.roster_id, first.parent_contact, (child.identity,), first.identity),
        carrier, definitions=(child,))
    leaf = store.begin(child); store.contact(leaf)
    _complete(store, carrier, failed=True)
    with pytest.raises(NativeSubworkUncertainContact, match="without a durable known return"):
        authenticate_native_parent_return(store=store, work=work)


def test_durable_child_receipt_interruption_finishes_before_read_only_parent_assembly(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    entry = store.begin(first); store.contact(entry); _publish(store, entry, b"FALSIFIED")
    def interrupted(*args, **kwargs):
        raise OSError("exposed publication interruption")
    monkeypatch.setattr(store.receipts, "commit", interrupted)
    with pytest.raises(OSError):
        _complete(store, entry)
    assert store.inspect(first).completion is not None and store.inspect(first).receipt is None
    with completed_native_parent_scope(store=store, work=work) as (reader, observed):
        assert reader.completed_only
        assert observed.inspections[0].state is NativeSubworkState.COMPLETED
        assert b"".join(reader.iter_completed_output(first, first.outputs[0].output_id)) == b"FALSIFIED"
    assert store.inspect(first).receipt is not None


def test_unknown_sibling_prevents_even_known_child_receipt_publication(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    entry = store.begin(first); store.contact(entry); _publish(store, entry, b"FALSIFIED")
    monkeypatch.setattr(store.receipts, "commit", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("interrupted")))
    with pytest.raises(OSError):
        _complete(store, entry)
    entry = store.begin(work.definitions[1]); store.contact(entry)
    before = _census(store)
    with pytest.raises(NativeSubworkUncertainContact):
        authenticate_native_parent_return(store=store, work=work)
    assert store.inspect(first).receipt is None and _census(store) == before


def test_child_receipt_write_failure_is_parent_pending_only_after_whole_known_census(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    entry = store.begin(first); store.contact(entry); _publish(store, entry, b"FALSIFIED")
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    def interrupted(*args, **kwargs):
        raise OSError("exposed repeated child receipt publication failure")
    monkeypatch.setattr(ExternalTaskReceiptStore, "commit", interrupted)
    with pytest.raises(OSError):
        _complete(store, entry)
    before = _census(store)
    with pytest.raises(NativeParentFinalizationPending):
        authenticate_native_parent_return(store=store, work=work)
    assert store.inspect(first).completion is not None and store.inspect(first).receipt is None
    assert _census(store) == before


def test_unknown_deferred_sibling_precedes_known_child_receipt_publication_pending(tmp_path, monkeypatch):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    entry = store.begin(first); store.contact(entry); _publish(store, entry, b"FALSIFIED")
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    def interrupted(*args, **kwargs):
        raise OSError("exposed repeated child receipt publication failure")
    monkeypatch.setattr(ExternalTaskReceiptStore, "commit", interrupted)
    with pytest.raises(OSError):
        _complete(store, entry)
    unknown = work.definitions[1]
    entry = store.begin(unknown); store.contact(entry)
    # A partial receipt pair forces the unknown sibling through the deferred
    # read-conflict branch. It still has no native completion or usable product.
    relative = store.receipts._relative_path(*store._receipt_locator(unknown))
    path = store.plane.root.resolve(relative, for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"exposed interrupted receipt without any native return")
    before = _census(store)
    with pytest.raises(ArtifactIdentityConflict):
        authenticate_native_parent_return(store=store, work=work)
    assert store.inspect(first).receipt is None and _census(store) == before


def test_missing_initial_roster_is_not_scientific_nonentry_proof(tmp_path):
    store, first, _ = _selected(tmp_path, freeze=False)
    definitions = (first,)
    work = PreparedNativeWork(first.parent_contact, ("exposed.unit",), ("exposed.slot",), definitions,
        (NativeSubworkRoster("selected.native-subwork", first.parent_contact, (first.identity,)),))
    with pytest.raises(NativeSubworkUncertainContact, match="exact frozen initial roster"):
        authenticate_native_parent_return(store=store, work=work)


@pytest.mark.parametrize("substitution", ("source", "denominator", "parent"))
def test_prepared_work_substitution_refuses_without_mutation(tmp_path, substitution):
    store, first, _ = _selected(tmp_path)
    work = _work(store, first)
    if substitution == "source":
        definitions = (replace(first, code_sources_sha256="f" * 64), *work.definitions[1:])
        work = replace(work, definitions=definitions, rosters=(replace(work.rosters[0],
            subworks=tuple(row.identity for row in definitions)),))
    elif substitution == "denominator":
        work = replace(work, definitions=(first,), rosters=(replace(work.rosters[0], subworks=(first.identity,)),))
    else:
        foreign = replace(first.parent_contact, implementation_commit="f" * 40)
        definitions = tuple(replace(row, parent_contact=foreign) for row in work.definitions)
        work = replace(work, expected_parent=foreign, definitions=definitions,
            rosters=(replace(work.rosters[0], parent_contact=foreign, subworks=tuple(row.identity for row in definitions)),))
    before = _census(store)
    with pytest.raises(ValueError):
        authenticate_native_parent_return(store=store, work=work)
    assert _census(store) == before


def _pipe(store, context, work, tmp_path):
    service = NativeSubworkPipeService(store, context, tmp_path, completed_work=work)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    return PipeNativeSubworkProgress(Connection()), service


def _prepared(tmp_path):
    plane, bundle, runner, context, contract, parent = _case(tmp_path, native=True)
    store = _store(plane, parent, bundle.manifests)
    store.parent_contacts.begin(parent)
    work = contract.native_work
    store.freeze_roster(work.rosters[0], definitions=work.definitions)
    return bundle, replace(context, prepared_invocation=contract), store, work


def test_completed_pipe_reuses_original_prepared_contract_and_exact_existing_roster(tmp_path):
    bundle, context, store, work = _prepared(tmp_path)
    definition, = work.definitions
    expected = _finish(store, definition)
    store.parent_contacts.retire_live_creator(work.expected_parent)
    before = _census(store)
    try:
        with completed_native_parent_scope(store=store, work=work) as (reader, _):
            progress, service = _pipe(reader, context, work, tmp_path)
            assert progress.parent_contact == work.expected_parent
            progress.freeze_roster(work.rosters[0], definitions=work.definitions)
            assert progress.recover(definition) == expected
            assert progress.resolve_completed_definition(definition.identity) == definition
            assert b"".join(progress.iter_completed_output(definition, definition.outputs[0].output_id,
                maximum_chunk_bytes=2)) == b"FALSIFIED"
            service.close()
        assert _census(store) == before and not store.parent_contacts.is_live_creator(work.expected_parent)
    finally:
        bundle.close()


@pytest.mark.parametrize("operation", ("begin", "contact", "output-open", "output-chunk", "output-abort",
    "output-close", "complete", "retain-partial-output"))
def test_completed_pipe_denies_every_mutation_before_dispatch(tmp_path, operation):
    bundle, context, store, work = _prepared(tmp_path)
    before = _census(store)
    try:
        with completed_native_parent_scope(store=store, work=work) as (reader, _):
            progress, service = _pipe(reader, context, work, tmp_path)
            with pytest.raises(NativeSubworkUncertainContact, match="prohibits acquisition and mutation"):
                progress._call(operation)
            assert progress.recover(work.definitions[0]) is None
            service.close()
        assert _census(store) == before
    finally:
        bundle.close()


@pytest.mark.parametrize("change", ("new", "changed", "definitions"))
def test_completed_pipe_refuses_new_or_changed_frozen_roster(tmp_path, change):
    bundle, context, store, work = _prepared(tmp_path)
    roster, definitions = work.rosters[0], work.definitions
    if change == "new":
        roster = replace(roster, roster_id="another.roster", parent_subwork=definitions[0].identity)
    elif change == "changed":
        roster = replace(roster, subworks=(replace(definitions[0].identity, object_fingerprint="f" * 64),))
    else:
        definitions = ()
    before = _census(store)
    try:
        with completed_native_parent_scope(store=store, work=work) as (reader, _):
            progress, service = _pipe(reader, context, work, tmp_path)
            with pytest.raises(NativeSubworkUncertainContact, match="cannot create or change"):
                progress.freeze_roster(roster, definitions=definitions)
            service.close()
        assert _census(store) == before
    finally:
        bundle.close()


def test_completed_pipe_refuses_foreign_definition_before_store_lookup_and_expired_scope(tmp_path, monkeypatch):
    bundle, context, store, work = _prepared(tmp_path)
    try:
        with completed_native_parent_scope(store=store, work=work) as (reader, _):
            progress, service = _pipe(reader, context, work, tmp_path)
            def forbidden(*args):
                raise AssertionError("foreign custody lookup")
            monkeypatch.setattr(reader, "resolve_completed_definition", forbidden)
            with pytest.raises(ValueError, match="outside its exact selected census"):
                progress.resolve_completed_definition(replace(work.definitions[0].identity, object_fingerprint="f" * 64))
        with pytest.raises(ValueError, match="scope has ended"):
            progress.inspect(work.definitions[0])
        service.close()
    finally:
        bundle.close()


def test_completed_store_never_republishes_receipt_deleted_during_assembly(tmp_path):
    bundle, _, store, work = _prepared(tmp_path)
    definition, = work.definitions
    completion = _finish(store, definition)
    receipt = completion.receipt
    try:
        with pytest.raises(ArtifactIdentityConflict):
            with completed_native_parent_scope(store=store, work=work) as (reader, _):
                run, task, attempt = reader._receipt_locator(definition)
                relative = reader.receipts._relative_path(run, task, attempt)
                path = reader.plane.root.resolve(relative, for_write=False)
                path.unlink()
                with pytest.raises(ArtifactIdentityConflict):
                    reader.recover(definition)
                assert not path.exists()
        assert receipt is not None and not path.exists()
    finally:
        bundle.close()
