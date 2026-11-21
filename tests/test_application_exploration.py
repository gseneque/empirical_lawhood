# SPDX-License-Identifier: MPL-2.0
"""Fresh original inspection, presentation compatibility and declared-source limits."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.api import application_context, application_exploration as explorer, application_presentations as presentations
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, response_bytes, load_application_json
from empirical_lawhood.api.application_exploration_contracts import EXPLORATION_SCHEMA, validate_exploration
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff


@pytest.fixture
def selected(monkeypatch):
    cutoff = InformationCutoff("cutoff.control", "clock.control", CausalPhase.PRE_ACTION, Decimal("0.10000000000000000001"), True)
    identity = ObjectIdentity.from_record(cutoff.cutoff_id, cutoff).to_document()
    view = {"schema": EXPLORATION_SCHEMA, "version": "1.0.0", "question": "Disclosed software question", "root_id": "root",
        "nodes": [{"id": "root", "label": "Original cutoff", "role": "root", "state": {"physical": "UNRESOLVED"},
            "source": identity, "record": cutoff.to_document(), "children": [], "method_ids": [], "group": "root"}],
        "edges": [], "summary": {"physical": "UNRESOLVED"}, "findings": [], "question_readouts": [], "work_coverage": {},
        "methods": [{"id": "fixture.method", "sources": [{"path": "api/application_exploration_contracts.py", "symbols": ["validate_exploration"]}]}],
        "layout": {"kind": "generic"}, "coverage": {"total_nodes": 1, "total_edges": 0}, "pending_bindings": []}
    data = presentations.PresentationData(identity, "DISCLOSED_SOFTWARE_CONTROL", {"physical": "UNRESOLVED"}, (),
        {"cutoff": cutoff.to_document()}, {"implementation": identity}, "No scientific qualification.", view)
    box = {"data": data, "reads": 0, "checks": 0, "refuse": False, "change_selection": False, "selection_reads": 0}

    class Plane:
        @contextmanager
        def read_context(self):
            yield self
        def require_verification_snapshot(self):
            box["checks"] += 1
            if box["refuse"]:
                raise PermissionError("original access or bytes revoked")

    plane = Plane()
    def read(context, directory, artifact_writer):
        assert directory == Path("/original/root") and artifact_writer is plane
        box["reads"] += 1
        return box["data"]
    declaration = presentations.ApplicationPresentation("fixture.root", "1.0.0", "Disclosed original", "fixture",
        "docs/using/research-workbench.md", ("value",), 16, read)
    monkeypatch.setattr(presentations, "application_presentations", lambda: (declaration,))
    monkeypatch.setattr(application_context, "application_storage", lambda *a, **k: (None, None, plane))
    entry = {"value": {"selection_id": "original", "investigation_id": "original", "context_id": "selected",
        "label": "Original", "question": "Original question", "identity": identity,
        "readers": [{"operation": "presentation.read", "directory": "/original/root", "panel_id": "fixture.root", "panel_version": "1.0.0"}],
        "classification": {}, "stages": [], "deployment": None, "companions": [], "links": []}}
    def selection(context, key):
        assert key == "original"
        box["selection_reads"] += 1
        return entry, "b" * 64 if box["change_selection"] and box["selection_reads"] > 1 else "a" * 64
    monkeypatch.setattr(explorer, "selected_entry", selection)
    return ApplicationContext("selected", "Selected", Path("/selected/python")), box, entry, cutoff


def call(selected, operation="exploration.read", **parameters):
    return execute_application(selected[0], ApplicationRequest("control", "selected", operation,
        tuple({"selection_id": "original", **parameters}.items())))


def test_original_identity_and_current_access_are_rechecked_for_exact_records(selected):
    _, box, _, cutoff = selected
    assert call(selected).succeeded
    record = call(selected, "exploration.record", record_id="root")
    assert record.succeeded and record.payload["canonical_text"].encode() == cutoff.canonical_bytes()
    assert record.payload["sha256"] == sha256(cutoff.canonical_bytes()).hexdigest()
    assert box["reads"] == box["checks"] == 2
    box["refuse"] = True
    refused = call(selected, "exploration.record", record_id="root")
    assert refused.payload is None and refused.reason_codes == ("CURRENT_CUSTODY_REFUSED",)


def test_changed_locator_identity_and_context_refuse_before_exposing_a_projection(selected):
    _, box, entry, _ = selected
    entry["value"]["identity"]["value"]["object_fingerprint"] = "f" * 64
    # The owning reader still returns its separately retained original identity.
    box["data"] = replace(box["data"], identity=deepcopy(box["data"].identity))
    box["data"].identity["value"]["object_fingerprint"] = "e" * 64
    assert call(selected).reason_codes == ("ORIGINAL_SELECTION_CHANGED",)
    entry["value"]["readers"][0]["context_id"] = "another.engine"
    reads = box["reads"]
    assert call(selected).reason_codes == ("CONTEXT_MISMATCH",) and box["reads"] == reads


def test_changed_collection_after_scientific_read_discards_response(selected):
    selected[1]["change_selection"] = True
    result = call(selected)
    assert result.payload is None and result.reason_codes == ("COLLECTION_CHANGED",)


def test_unsupported_panel_and_future_exploration_revision_use_original_generic_data(selected):
    _, box, entry, _ = selected
    entry["value"]["readers"][0]["panel_version"] = "99.0.0"
    fallback = call(selected)
    assert fallback.succeeded and fallback.payload["kind"] == "presentation-generic"
    assert "exploration" not in fallback.payload
    entry["value"]["readers"][0]["panel_version"] = "1.0.0"
    box["data"] = replace(box["data"], exploration={"schema": EXPLORATION_SCHEMA, "version": "99.0.0"})
    fallback = call(selected)
    assert fallback.succeeded and fallback.payload["kind"] == "presentation-generic"
    original = load_application_json(response_bytes(fallback))["payload"]["presentation"]["original_report"]
    assert original["cutoff"]["value"]["coordinate"] == {"decimal": "0.10000000000000000001"}


def test_source_inspection_is_declared_bounded_and_distinguishes_current_reader(selected):
    result = call(selected, "exploration.method", method_id="fixture.method", source_path="api/application_exploration_contracts.py")
    assert result.succeeded and result.payload["source_scope"] == "CURRENT_SELECTED_READER_IMPLEMENTATION"
    assert result.payload["original_native_runtime"] == "NOT_SUPPLIED_BY_THIS_SOURCE_READ"
    assert result.payload["symbols"][0]["name"] == "validate_exploration"
    assert call(selected, "exploration.method", method_id="fixture.method", source_path="../../private").reason_codes == ("UNDECLARED_METHOD_SOURCE",)
    assert call(selected, "exploration.method", method_id="fixture.method", source_path="api/application_exploration_contracts.py",
        expected_source_sha256="f" * 64).reason_codes == ("METHOD_SOURCE_CHANGED",)


def test_m50_contract_keeps_all_questions_and_nested_denominators_without_claiming_a_reader(selected):
    view = deepcopy(selected[1]["data"].exploration)
    view["question_readouts"] = [{"question_id": f"Q{index}", "label": "Disclosed pending question",
        "acquisition_state": "NOT_ENTERED", "authentication_state": "UNAVAILABLE", "assessment_state": "READER_UNAVAILABLE",
        "disposition": "UNANSWERED", "quantity": None, "uncertainty": None,
        "denominator": {"matched_constructions": 1, "nested_positions": 4, "independent_biological_units": 0},
        "evidence": [], "consequence": "Original domain reader and evidence required."} for index in range(1, 7)]
    validate_exploration(view)
    view["question_readouts"].pop()
    with pytest.raises(ValueError, match="six"):
        validate_exploration(view)


@pytest.mark.parametrize("values", ((2, 3, 1, 1), (1, 1, None, None), (2, 3, None, None)))
def test_rubisco_display_preserves_owning_outcomes_and_variable_complete_census(values):
    from tests.test_rubisco_initial_root_public import disclosed_analysis
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import calculate_initial_root, assess_initial_root
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import analysis_arguments, initial_root_requirement_graph
    from empirical_lawhood.api.domain_composition.rubisco_response.application_presentation import _exploration
    analysis = disclosed_analysis(values)
    result = calculate_initial_root(**analysis_arguments(analysis))
    assessment = assess_initial_root(result=result, **analysis_arguments(analysis))
    graph = initial_root_requirement_graph(analysis, result=result)
    science = {"question": "Disclosed software control", "biological_predictive_validity": "UNEVALUABLE",
        "independent_biological_units": 0, "new_native_calls": 0, "scientific_completion": "COMPLETED",
        "numerical_disposition": assessment.numerical_disposition.value}
    view = _exploration(science, graph, result, {"status": "SUCCEEDED", "task_count": 2})
    validate_exploration(view)
    assert view["findings"] == [case.to_document() for case in result.cases]
    assert view["summary"]["joint_outcome"] == result.joint_outcome
    assert view["summary"]["root_prerequisites"] == 1 + len(result.decision_requirement_ids)
    assert view["summary"]["selected_suppliers"] == 0
    assert {row["record"]["value"]["requirement_id"] for row in view["nodes"]} == {row.requirement_id for row in graph.requirements}
