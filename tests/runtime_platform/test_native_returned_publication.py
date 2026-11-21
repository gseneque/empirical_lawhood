# SPDX-License-Identifier: MPL-2.0
"""Recover full returned streams after publication failure, without native replay."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.native_subwork import NativeSubworkOutput, NativeSubworkPartialOutput, NativeSubworkRoster
from tests.runtime_platform.test_native_effect_facts import ENTRY_TIME, RETURN_TIME, _snapshot
from tests.runtime_platform.test_native_subwork import ExposedInput
from tests.runtime_platform.test_worker_preflight import _case


@pytest.fixture
def retained(tmp_path):
    plane, bundle, _, _, contract, parent = _case(tmp_path, native=True)
    definition, = contract.native_definitions
    definition = replace(definition, outputs=tuple(sorted((*definition.outputs,
        NativeSubworkOutput("return.metadata", ExposedInput.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json")), key=lambda row: row.output_id)))
    roster = NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,))
    contract = replace(contract, native_work=replace(contract.native_work,
        definitions=(definition,), rosters=(roster,)))
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    contacts.begin(parent)
    with contacts.execution_lock(parent.run_id):
        pass
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=bundle.manifests, prepared_invocation=contract)
    store.freeze_roster(roster, definitions=(definition,))
    entry = store.begin(definition)
    store.contact(entry)
    store.call_entry(entry, at_utc=ENTRY_TIME)
    try:
        yield store, definition, entry
    finally:
        bundle.close()


def _retain(store, definition, entry, *, prefix=b"FALSIFIED", expected=b"FALSIFIED", returned=True):
    if returned:
        store.call_return(entry, at_utc=RETURN_TIME)
    record = NativeSubworkPartialOutput(definition.identity, store._contact_identity(entry),
        "result.output.native", len(expected), len(expected), sha256(expected).hexdigest(),
        len(prefix), sha256(prefix).hexdigest(), ("native-output-publication-refused",))
    store.retain_partial_output(entry, record, (prefix,))
    store.parent_contacts.retire_live_creator(definition.parent_contact)
    return record


def test_exact_returned_publication_keeps_failure_bytes_and_never_enters_again(retained, monkeypatch):
    store, definition, entry = retained
    record = _retain(store, definition, entry)
    before = _snapshot(store)
    metadata = ExposedInput("original.result", "FALSIFIED")
    def forbidden(*args, **kwargs):
        pytest.fail("publication recovery requested native entry")
    for name in ("begin", "contact", "call_entry", "call_return"):
        monkeypatch.setattr(ExternalNativeSubworkStore, name, forbidden)
    result = store.recover_returned_publication(definition,
        canonical_outputs=(("return.metadata", metadata),))
    assert result.receipt is not None and result.completion.omitted_output_ids == ()
    assert result.completion.cost.cpu_seconds is None and result.completion.cost.wall_seconds is None
    assert result.completion.peak_rss_bytes is None and result.partial_output_records == (record,)
    assert result.call_entry.entered_at_utc == ENTRY_TIME and result.call_return.returned_at_utc == RETURN_TIME
    assert b"".join(store.iter_completed_output(definition, "result.output.native")) == b"FALSIFIED"
    assert all(_snapshot(store)[path] == raw for path, raw in before.items())
    after = _snapshot(store)
    assert store.recover_returned_publication(definition,
        canonical_outputs=(("return.metadata", metadata),)) == result
    assert _snapshot(store) == after
    with pytest.raises(ValueError, match="existing original"):
        store.recover_returned_publication(definition,
            canonical_outputs=(("return.metadata", ExposedInput("original.result", "changed")),))
    assert _snapshot(store) == after


@pytest.mark.parametrize("change", ("prefix", "hash", "unknown-return", "missing-metadata"))
def test_incomplete_or_unobserved_return_refuses_before_publication(retained, change):
    store, definition, entry = retained
    _retain(store, definition, entry, prefix=b"FA" if change == "prefix" else b"FALSIFIED",
        expected=b"different" if change == "hash" else b"FALSIFIED", returned=change != "unknown-return")
    before = _snapshot(store)
    outputs = () if change == "missing-metadata" else (("return.metadata", ExposedInput("result", "FALSIFIED")),)
    with pytest.raises(ValueError, match="successful raw return|complete hash-bound|required original output"):
        store.recover_returned_publication(definition, canonical_outputs=outputs)
    assert _snapshot(store) == before
