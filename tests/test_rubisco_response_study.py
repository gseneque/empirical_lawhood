# SPDX-License-Identifier: MPL-2.0
"""Complete source-bound selections and independent scientific prerequisite graph."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import RubiscoRequirementGraph, response_requirement_graph, validate_connection_assessment_census
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def test_backward_graph_keeps_both_milestone_halves_and_all_rate_suppliers():
    study = disclosed_study()
    graph = response_requirement_graph(study)
    records = {row.requirement_id: row for row in graph.requirements}
    root = records[graph.root_requirement_id]
    assert set(root.further_requirement_ids) == {
        "requirement.study.disclosed.response.validated-prediction",
        "requirement.study.disclosed.response.computational-benefit"}
    for supply in study.supplies:
        for scenario in supply.scenarios:
            for row in scenario.ledger.bindings:
                assert "requirement.study.disclosed.response." + supply.case.case_id + "." + scenario.scenario_id + ".rate." + row.parameter in records
    assert study.acceptance.matrix_handoff_requirement_id in records
    assert study.acceptance.gp_applicability_requirement_id in records
    assert len(graph.connection_assessment_plans[0].phases) == 4
    assert decode_canonical_bytes(graph.canonical_bytes(), RubiscoRequirementGraph, maximum_bytes=500_000) == graph
    assert decode_canonical_bytes(study.canonical_bytes(), type(study), maximum_bytes=2_000_000) == study
    assert all(row.nominated_turnover_log_ratio_interval is None for row in study.nominated_predictions)


def test_scientific_cycle_and_missing_supplier_are_rejected_even_without_execution_dag_edges():
    graph = response_requirement_graph(disclosed_study())
    row = next(row for row in graph.requirements if row.requirement_id == graph.conditional_requirement_id)
    cycle = replace(row, further_requirement_ids=(graph.root_requirement_id,))
    with pytest.raises(ValueError, match="cycle"):
        replace(graph, requirements=tuple(cycle if item == row else item for item in graph.requirements))
    absent = replace(row, further_requirement_ids=("requirement.missing-supplier",))
    with pytest.raises(ValueError, match="unresolved prerequisites"):
        replace(graph, requirements=tuple(absent if item == row else item for item in graph.requirements))
    with pytest.raises(ValueError, match="four-phase"):
        validate_connection_assessment_census(graph, ())


def test_complete_case_census_and_exposure_roles_cannot_be_relabeled():
    study = disclosed_study()
    assert len(study.allocation.units) == 1
    assert len(study.allocation.units[0].numerical_view_ids) >= 2
    assert study.independent_biological_units == 0
    with pytest.raises(ValueError, match="selected paired case"):
        replace(study, supplies=study.supplies[:1])
    with pytest.raises(ValueError, match="held-out"):
        replace(study, allocation=replace(study.allocation,
            roles=(replace(study.allocation.roles[0], role="validation"),)))
    with pytest.raises(ValueError, match="held-out"):
        replace(study, allocation=replace(study.allocation,
            units=(replace(study.allocation.units[0], exposed=False),)))
    with pytest.raises(ValueError, match="candidate prediction"):
        replace(study, nominated_predictions=())


@pytest.mark.parametrize("change", ["abstain", "probability", "missing-endpoint", "refinement", "native-ceiling"])
def test_acceptance_requires_joint_criteria_and_a_finite_zero_acquisition_software_lane(change):
    study = disclosed_study()
    with pytest.raises(ValueError):
        if change == "abstain":
            replace(study.acceptance, minimum_useful_service=D(0))
        elif change == "probability":
            replace(study.acceptance, joint_coverage_level=D("0.95"))
        elif change == "missing-endpoint":
            replace(study.acceptance, paired_log_endpoint_tolerances=(D("0.05"),))
        elif change == "refinement":
            replace(study.acceptance, maximum_refinements=1)
        else:
            replace(study, acceptance=replace(study.acceptance, maximum_native_acquisitions=1))


def test_complete_study_readout_keeps_nomination_decision_and_milestone_separate(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, assess_response_study, predict_response_study
    study = disclosed_study()
    prediction = replace(study.nominated_predictions[0], nominated_turnover_log_ratio_interval=(D("0.1"), D("0.2")))
    study = replace(study, nominated_predictions=(prediction,))
    product = predict_response_study(study, prediction_id="predictions.exposed.study")
    def forbidden(*args, **kwargs):
        raise AssertionError("retained study assessment invoked a producer")
    with monkeypatch.context() as patch:
        patch.setattr("empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction.predict_paired_rates", forbidden)
        result = assess_response_study(study, product, assessment_id="assessment.exposed.study")
    assert result.conditional_candidate_action == "ADVANCE"
    assert result.nomination_findings[0].joint_direction == "CONDITIONAL_SUPPORT"
    assert result.nomination_findings[0].nominated_magnitude == "CONDITIONAL_CONTRADICTION"
    assert result.combined_milestone == "OPEN" and result.biological_predictive_calibration == "NOT_ESTABLISHED"
    assert study.acceptance.matrix_handoff_requirement_id in result.remaining_requirement_ids
    assert all(row.disposition.value == "SATISFIED" for row in result.connection_assessments)
    assert decode_canonical_bytes(result.canonical_bytes(), ResponseAssessment, maximum_bytes=2_000_000) == result


def test_missing_control_case_prevents_advancement_and_retains_complete_failure_denominator():
    from empirical_lawhood.domains.rubisco.rubisco_response.study_science import assess_response_study, predict_response_study
    study = disclosed_study()
    product = predict_response_study(study, prediction_id="predictions.missing-control")
    result = assess_response_study(study, replace(product, predictions=product.predictions[:1]),
                                  assessment_id="assessment.missing-control")
    assert result.conditional_candidate_action == "HOLD" and not result.complete_case_census
    assert result.connection_assessments[1].disposition.value == "FALSIFIED"
    assert result.graph.conditional_requirement_id in result.remaining_requirement_ids
    with pytest.raises(ValueError, match="finite menu"):
        assess_response_study(study, product, assessment_id="assessment.undeclared",
                              permitted_refinement_id="refinement.undeclared")
