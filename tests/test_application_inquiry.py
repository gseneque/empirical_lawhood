# SPDX-License-Identifier: MPL-2.0
"""Focused inquiry client boundaries using existing exposed software fixtures."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import application_inquiry as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, MAX_RESPONSE_BYTES, load_application_json, response_bytes
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigins
from tests.test_robust_inquiry_service import ROOT, missing_request
from tests.test_recursive_public_service import _plane


@pytest.fixture
def selected(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    inputs = root / "inputs"
    inputs.mkdir()
    context = ApplicationContext("inquiry", "Exposed software inquiry", Path("/selected/python"),
        project_root=ROOT, operator_profile=Path("/selected/profile"), input_root=inputs)
    profile = SimpleNamespace(to_document=lambda: {"selection": "software-control"})
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: (ROOT, profile, plane))
    source = owner.owner.implementation_binding(ROOT)
    monkeypatch.setattr(owner.owner, "implementation_binding", lambda root: source)
    request = missing_request(plane)
    path = inputs / "request.json"
    path.write_bytes(request.canonical_bytes())
    return SimpleNamespace(root=root, context=context, plane=plane, request=request, input=path)


def run(selected, operation, **values):
    return execute_application(selected.context, ApplicationRequest("inquiry.control", "inquiry", operation, tuple(values.items())))


def wire(result):
    assert result.succeeded, result
    return load_application_json(response_bytes(result), maximum_bytes=MAX_RESPONSE_BYTES)["payload"]


def review(selected):
    return wire(run(selected, "inquiry.review", input=str(selected.input), output_dir=str(selected.root / "decision")))


def test_review_has_no_publication_and_commit_preserves_current_unresolved_frontier(selected):
    reviewed = review(selected)
    assert reviewed["status"] == "REVIEWED_NOT_COMMITTED" and reviewed["decision"]["selected_action"] == "HOLD"
    assert not (selected.root / "decision").exists()
    report = wire(run(selected, "inquiry.commit", **reviewed["selection"], expected_review_sha256=reviewed["review_sha256"]))
    assert report["status"] == "COMMITTED" and report["packet_sha256"] == reviewed["decision"]["packet_sha256"]
    result = wire(run(selected, "inquiry.read", directory=report["decision_directory"]))
    assert result["summary"]["unresolved_target_requirement_ids"] == ["condition", "instrument"]
    assert result["summary"]["unresolved_target_claim_ids"] == ["claim.target"]
    assert result["inquiry"]["records"] == report["records"] and result["inquiry"]["successor"] is None
    assert result["inquiry"]["scientific_authority"] == "NONE"


@pytest.mark.parametrize("change", ("destination", "context", "input"))
def test_changed_review_refuses_before_decision_publication(selected, change):
    reviewed = review(selected)
    values = dict(reviewed["selection"])
    if change == "destination":
        values["output_dir"] = str(selected.root / "another")
    elif change == "context":
        selected.context = replace(selected.context, maximum_parallel_tasks=2)
    else:
        selected.input.write_bytes(replace(selected.request, actor_id="unrelated-actor").canonical_bytes())
    result = run(selected, "inquiry.commit", **values, expected_review_sha256=reviewed["review_sha256"])
    assert not result.succeeded and result.payload is None
    assert not (selected.root / "decision").exists() and not (selected.root / "another").exists()


def test_hold_cannot_author_a_successor_and_missing_admission_cannot_be_invented(selected):
    reviewed = review(selected)
    committed = wire(run(selected, "inquiry.commit", **reviewed["selection"], expected_review_sha256=reviewed["review_sha256"]))
    origins = selected.context.input_root / "origins.json"
    origins.write_bytes(RecursiveInputOrigins(()).canonical_bytes())
    result = run(selected, "inquiry.review-author", directory=committed["decision_directory"],
        origins=str(origins), output_dir=str(selected.root / "forbidden"))
    assert result.reason_codes == ("OWNER_CONTRACT_REFUSED",) and not (selected.root / "forbidden").exists()
    missing = run(selected, "inquiry.successor", directory=committed["decision_directory"])
    assert not missing.succeeded and missing.payload is None


def test_final_read_mutation_refuses_entire_original_decision_view(selected, monkeypatch):
    reviewed = review(selected)
    committed = wire(run(selected, "inquiry.commit", **reviewed["selection"], expected_review_sha256=reviewed["review_sha256"]))
    path = Path(committed["decision_directory"]) / "state.json"
    original = owner.projection
    def mutate(**kwargs):
        result = original(**kwargs)
        path.write_bytes(path.read_bytes() + b' ')
        return result
    monkeypatch.setattr(owner, "projection", mutate)
    result = run(selected, "inquiry.read", directory=committed["decision_directory"])
    assert not result.succeeded and result.payload is None


def test_protected_and_escaped_input_selection_refuse_before_owners(selected, monkeypatch):
    selected.context = replace(selected.context, read_access_paths=(Path("/protected/access"),))
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: pytest.fail("protected route opened storage"))
    assert run(selected, "inquiry.read", directory="/protected/decision").reason_codes == ("UNSUPPORTED_ACCESS_SELECTION",)
    for text in ("same=/one\nsame=/two", "id=relative", "id=/one/../two", "no-separator"):
        with pytest.raises(ValueError):
            owner.input_bindings({"text": text})


def test_bound_input_locations_cannot_overlap_invocation_custody(tmp_path, monkeypatch):
    from empirical_lawhood.api import invocation_retention
    from empirical_lawhood.api.application_invocation import run_application_invocation
    context = ApplicationContext("inquiry", "Software paths", Path("/selected/python"))
    directory = tmp_path / "invocation"
    request = ApplicationRequest("overlap", "inquiry", "inquiry.author", (("text", "source=" + str(directory / "attempt/source")),))
    monkeypatch.setattr(invocation_retention, "start_attempt", lambda *a, **k: pytest.fail("overlapping input started invocation"))
    with pytest.raises(ValueError, match="must be disjoint"):
        run_application_invocation(context, request, directory=directory, handle="overlap")
    assert not directory.exists()
