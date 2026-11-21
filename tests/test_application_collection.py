# SPDX-License-Identifier: MPL-2.0
"""Run handoffs retain original bindings without result reconstruction or contact."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api import application_collection as collection
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, transport_value
from empirical_lawhood.storage.artifacts import FilesystemState, GuardedExternalRoot
from empirical_lawhood.storage.workbench_state import WorkbenchStateStore
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract


def identity(name="original.wave", digest="a"):
    return ObjectIdentity(name, "empirical-lawhood/testing/original", "1.0.0", digest * 64).to_document()


def selection(name="selected.wave", original=None):
    return {"schema": collection.SELECTION_SCHEMA, "version": "1.0.0", "value": {
        "selection_id": name, "investigation_id": "investigation.original", "context_id": "selected.engine",
        "label": "A repeated descriptive label", "question": "Which original requirement remains unresolved?",
        "identity": identity() if original is None else original,
        "readers": [{"operation": "recursive.execution", "directory": "/original/returned/wave"}],
        "classification": {"programmes": [{"id": "biology", "label": "Biology"}],
            "disciplines": [{"id": "mechanics", "label": "Mechanics"}],
            "source": {"path": "/selected/programmes.json", "sha256": "b" * 64}},
        "companions": [], "stages": [], "deployment": None, "links": []}}


@pytest.fixture
def selected(tmp_path, monkeypatch):
    root = tmp_path / "scratch"
    root.mkdir()
    contract = ExternalRootContract("software.collection", "Collection fixture", str(root), str(root),
        "empirical-lawhood/testing/ui-state", 1, allowed_filesystem_types=("ext4",))

    class Inspector:
        def inspect(self, _contract):
            return FilesystemState(str(root), True, True, 10**9, False, None, None, "ext4")

    store = WorkbenchStateStore(GuardedExternalRoot(contract, Inspector()), root / "collection.json", writable=True)
    monkeypatch.setattr(collection, "operational_state_store", lambda context: store)
    from empirical_lawhood.api import application
    monkeypatch.setattr(application, "application_storage", lambda *a, **k: pytest.fail("collection opened scientific custody"))
    context = ApplicationContext("selected.engine", "Selected engine", Path("/selected/python"))
    return context, store


def call(selected, operation, **parameters):
    return execute_application(selected[0], ApplicationRequest("selection.request", "selected.engine", operation,
        tuple(sorted(parameters.items()))))


def register(selected, entry, digest=None):
    parameters = {"text": collection.document_bytes(entry).decode()}
    if digest is not None:
        parameters["expected_collection_sha256"] = digest
    return call(selected, "collection.register", **parameters)


def test_empty_read_is_not_an_empty_scientific_world_and_creates_nothing(selected):
    result = call(selected, "collection.list")
    assert result.succeeded and result.payload["summary"]["exists"] is False
    assert result.payload["scope"] == "OPERATOR_METADATA_NOT_AUTHENTICATED_FINDINGS"
    assert list(selected[1].path.parent.iterdir()) == []


def test_terminal_document_and_api_share_guarded_registration_after_restart(selected):
    entry = selection()
    request = ApplicationRequest("terminal.handoff", "selected.engine", "collection.register",
        (("text", collection.document_bytes(entry).decode()),))
    terminal = execute_application(selected[0], ApplicationRequest.from_document(request.to_document()))
    assert terminal.succeeded and terminal.payload["scientific_reads"] == terminal.payload["native_calls"] == 0
    context = ApplicationContext.from_document(selected[0].to_document())
    reopened = call((context, selected[1]), "collection.entry", selection_id="selected.wave")
    assert reopened.succeeded and transport_value(reopened.payload["entry"]) == entry
    second = register(selected, selection("second.wave", identity("different.wave", "c")), terminal.payload["collection_sha256"])
    assert second.succeeded
    listing = call(selected, "collection.list", limit=1)
    assert listing.payload["page"]["total"] == 2 and listing.payload["page"]["returned_count"] == 1
    assert listing.payload["page"]["next_cursor"] is not None


def test_duplicate_identity_keeps_alias_and_both_locators_but_equal_labels_do_not_merge(selected):
    first = register(selected, selection())
    alias = selection("returned.alias")
    alias["value"]["readers"][0]["directory"] = "/returned/local/wave"
    result = register(selected, alias, first.payload["collection_sha256"])
    assert result.succeeded and result.payload["entry_count"] == 1
    original = call(selected, "collection.entry", selection_id="returned.alias")
    assert original.payload["entry"]["value"]["selection_id"] == "selected.wave"
    assert len(original.payload["entry"]["value"]["readers"]) == 2
    second = register(selected, selection("same.label", identity("second.original", "c")), result.payload["collection_sha256"])
    assert second.succeeded and second.payload["entry_count"] == 2


def test_pending_remote_wave_accepts_later_return_without_claiming_a_result(selected):
    pending = selection()
    pending["value"]["identity"] = None
    pending["value"]["deployment"] = {"deployment_id": "remote.original", "allocation": {"path": "/selected/allocation.json", "sha256": "b" * 64},
        "job_card": {"path": "/selected/job-card.json", "sha256": "c" * 64}, "observation_path": "/selected/observation.json",
        "run_id": "run.original", "packet_sha256": "d" * 64, "controller_source_sha256": "e" * 64, "worker_source_sha256": "f" * 64}
    pending["value"]["stages"] = [{"id": "m50.09", "label": "Initial checkpoint", "revision": 1,
        "state": "AUTHORED", "depends_on": ["m50.07"], "source": {"path": "/selected/design.json", "sha256": "d" * 64},
        "decision": identity("decision", "e"), "intent": identity("intent", "f")}]
    result = register(selected, pending)
    assert result.succeeded
    returned = deepcopy(pending)
    returned["value"]["identity"] = identity()
    returned["value"]["readers"].append({"operation": "recursive.execution", "directory": "/returned/local/wave"})
    returned["value"]["stages"][0].update(revision=2, state="RETURNED")
    result = register(selected, returned, result.payload["collection_sha256"])
    assert result.succeeded
    read = call(selected, "collection.entry", selection_id="selected.wave").payload["entry"]["value"]
    assert read["stages"][0]["depends_on"] == ("m50.07",)
    assert read["identity"] == identity() and len(read["readers"]) == 2
    for target, field, replacement, reason in (
        ("deployment", "allocation", {"path": "/selected/another.json", "sha256": "d" * 64}, "DEPLOYMENT_SUBSTITUTION"),
        ("stage", "intent", identity("changed.intent", "d"), "STAGE_INTENT_SUBSTITUTION")):
        changed = deepcopy(returned)
        chosen = changed["value"]["deployment"] if target == "deployment" else changed["value"]["stages"][0]
        chosen[field] = replacement
        if target == "stage":
            chosen["revision"] += 1
        refusal = register(selected, changed, result.payload["collection_sha256"])
        assert refusal.reason_codes == (reason,)
    assert transport_value(call(selected, "collection.entry", selection_id="selected.wave").payload["entry"]) == returned


def test_stale_registration_locator_and_companion_substitution_preserve_original_bytes(selected):
    entry = selection()
    entry["value"]["companions"] = [{"role": "inquiry", "directory": "/original/decision", "identity": identity("hold", "d")}]
    result = register(selected, entry)
    before = selected[1].read()
    assert register(selected, selection("stale"), "b" * 64).reason_codes == ("COLLECTION_CHANGED",)
    changed = deepcopy(entry)
    changed["value"]["readers"][0]["directory"] = "/substituted/wave"
    assert register(selected, changed, result.payload["collection_sha256"]).reason_codes == ("ORIGINAL_LOCATOR_REMOVED",)
    changed = deepcopy(entry)
    changed["value"]["companions"][0]["identity"] = identity("substituted.hold", "e")
    assert register(selected, changed, result.payload["collection_sha256"]).reason_codes == ("COMPANION_SUBSTITUTION",)
    assert selected[1].read() == before


def test_context_and_scientific_relationship_substitution_refuse(selected):
    wrong = selection()
    wrong["value"]["context_id"] = "another.engine"
    assert register(selected, wrong).reason_codes == ("CONTEXT_MISMATCH",)
    wrong = selection()
    wrong["value"]["links"] = [{"target": "another.run", "kind": "SCIENTIFIC_SUPPLY", "label": "Unsupported supply",
        "source": {"path": "/selected/narrative.json", "sha256": "d" * 64}}]
    assert register(selected, wrong).reason_codes == ("SCIENTIFIC_EDGE_REQUIRES_OWNER",)
    assert selected[1].read() is None


def test_collection_census_and_current_profile_refuse_without_truncation(selected, monkeypatch):
    monkeypatch.setattr(collection, "MAX_ENTRIES", 1)
    first = register(selected, selection())
    original = selected[1].read()
    assert register(selected, selection("second", identity("second", "c")), first.payload["collection_sha256"]).reason_codes == ("COLLECTION_LIMIT",)
    assert selected[1].read() == original
    selected[1].writable = False
    assert register(selected, selection(), first.payload["collection_sha256"]).reason_codes == ("CURRENT_CUSTODY_REFUSED",)
    assert selected[1].read() == original


def test_optional_context_selections_preserve_legacy_fingerprint():
    old = ApplicationContext("original", "Original", Path("/original/python"))
    assert "collection_path" not in old.to_document()["value"] and "observation_root" not in old.to_document()["value"]
    current = replace(old, collection_path=Path("/selected/collection.json"), observation_root=Path("/selected/observations"))
    assert current.fingerprint() != old.fingerprint()
    assert ApplicationContext.from_document(current.to_document()) == current
