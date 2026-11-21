# SPDX-License-Identifier: MPL-2.0
"""Full conditional report denominators and explicit scientific evidence ceilings."""

import csv
from dataclasses import replace
from decimal import Decimal as D, localcontext
import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues
from empirical_lawhood.domains.rubisco.rubisco_response.biological_support import assess_predictive_support, selection_from_study
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import COMPONENTS, ReferenceFindingReport, build_reference_finding_report
from empirical_lawhood.domains.rubisco.rubisco_response.report_rendering import render_attempt_csv, render_endpoint_csv, render_parameter_csv, render_reference_report
from empirical_lawhood.domains.rubisco.rubisco_response.study import exposed_source_allocation
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import predict_response_study
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from tests.test_recursive_inquiry_policy import work_bound_case


def report(study=None, predictions=None, *, state=None):
    study = study or disclosed_study()
    predictions = predictions or predict_response_study(study, prediction_id="prediction.report.exposed")
    biology = assess_predictive_support(selection_from_study(study), assessment_id="biology.report.exposed")
    specification = None
    if state is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import response_draft
        from empirical_lawhood.domains.rubisco.rubisco_response.retained_inquiry import retained_inquiry_specification
        specification = retained_inquiry_specification(response_draft(study))
        state = replace(state, specification=ObjectIdentity.from_record(specification.specification_id, specification),
            information_cutoff=replace(state.information_cutoff, clock_id=specification.target.scope.clock_id))
    return build_reference_finding_report(study, predictions, biology, report_id="report.exposed",
        inquiry_specification=specification, work_state=state)


def test_report_keeps_nomination_magnitude_candidate_action_and_milestone_separate():
    study = disclosed_study()
    nomination = replace(study.nominated_predictions[0], nominated_turnover_log_ratio_interval=(D("0.1"), D("0.2")))
    result = report(replace(study, nominated_predictions=(nomination,)))
    assert result.conditional_assessment.nomination_findings[0].joint_direction == "CONDITIONAL_SUPPORT"
    assert result.conditional_assessment.nomination_findings[0].nominated_magnitude == "CONDITIONAL_CONTRADICTION"
    assert result.action.conditional_action == "ADVANCE" and result.action.biological_action == "HOLD"
    assert result.milestone.status == "OPEN" and tuple(row.component for row in result.milestone.components) == COMPONENTS
    assert result.milestone.components[0].disposition is A.UNEVALUABLE
    assert result.milestone.components[3].disposition is A.NOT_ATTEMPTED
    text = render_reference_report(result)
    assert text.splitlines()[0].endswith("biological action is HOLD and the combined milestone is OPEN.")
    assert "nominated magnitude=CONDITIONAL_CONTRADICTION" in text
    assert "not confidence bounds" in text and "specificity=18/5 (dimensionless)" in text
    assert "No-change equality control: MATCHED" in text
    assert "absolute floors=(NOT_SELECTED s^-1, NOT_SELECTED)" in text
    assert "Decimal(" not in text
    assert decode_canonical_bytes(result.canonical_bytes(), ReferenceFindingReport, maximum_bytes=3_000_000) == result
    with pytest.raises(ValueError, match="before every"):
        replace(result.milestone, status="COMPLETE")


def test_criterion_only_change_deprioritizes_without_turning_adversity_into_math_failure():
    study = disclosed_study()
    study = replace(study, decisions=(replace(study.decisions[0], minimum_turnover_ratio=D(2)), study.decisions[1]))
    result = report(study)
    assert result.action.conditional_action == "DEPRIORITIZE"
    assert result.conditional_assessment.nomination_findings[0].joint_direction == "CONDITIONAL_SUPPORT"
    assert all(row.numerical_assessment is A.SATISFIED for row in result.endpoints)
    assert result.milestone.components[0].disposition is A.UNEVALUABLE
    assert "candidate action is DEPRIORITIZE" in render_reference_report(result).splitlines()[0]


def test_missing_and_failed_alternatives_survive_every_projection():
    study = disclosed_study()
    supplies = (disclosed_supply(scenario_states=("AVAILABLE", "FAILED", "UNKNOWN")), study.supplies[1])
    study = replace(study, supplies=supplies, allocation=exposed_source_allocation(study.cases, supplies))
    result = report(study)
    assert result.action.conditional_action == "HOLD"
    assert len(result.endpoints) == 4 and tuple(row.original_state for row in result.endpoints[:3]) == ("AVAILABLE", "FAILED", "UNKNOWN")
    rows = list(csv.DictReader(io.StringIO(render_endpoint_csv(result))))
    assert len(rows) == 4 and rows[1]["wt_kcat_c_s_inv"] == rows[2]["turnover_ratio"] == "UNKNOWN"
    assert rows[1]["reason_codes"] == "ORIGINAL_SCENARIO_FAILED"
    parameters = list(csv.DictReader(io.StringIO(render_parameter_csv(result))))
    assert len(parameters) == 32 and sum(row["wt_value"] == "UNKNOWN" for row in parameters) == 16
    assert "original=FAILED" in render_reference_report(result) and "original=UNKNOWN" in render_reference_report(result)
    with pytest.raises(ValueError, match="drops a selected"):
        replace(result, endpoints=(result.endpoints[0], result.endpoints[-1]))


def test_absent_control_prediction_keeps_its_row_and_falsifies_complete_numerical_claim():
    study = disclosed_study()
    predictions = predict_response_study(study, prediction_id="prediction.missing")
    result = report(study, replace(predictions, predictions=predictions.predictions[:1]))
    assert len(result.endpoints) == 2 and result.endpoints[1].retained_value is None
    assert "MISSING_RETAINED_ENDPOINT" in result.endpoints[1].reason_codes
    assert result.action.conditional_action == "HOLD" and result.milestone.components[0].disposition is A.FALSIFIED
    assert result.milestone.components[2].disposition is A.UNEVALUABLE


def test_failed_numerical_output_is_visible_and_cannot_inherit_a_successful_decision():
    study = disclosed_study()
    predictions = predict_response_study(study, prediction_id="prediction.failed-math")
    first = predictions.predictions[0]
    point = first.points[0]
    point = replace(point, wild_type=replace(point.wild_type, carboxylation_events_per_site_s=Exact.of(100)))
    predictions = replace(predictions, predictions=(replace(first, points=(point,)), predictions.predictions[1]))
    result = report(study, predictions)
    assert result.endpoints[0].retained_value is not None and result.endpoints[0].numerical_assessment is A.FALSIFIED
    assert result.milestone.components[1].disposition is A.FALSIFIED
    assert "NUMERICAL_OUTPUT_NOT_ACCEPTED" in render_endpoint_csv(result)


def test_raw_and_anchored_values_keep_shared_dependence_and_exact_rounding_bounds():
    study = disclosed_study()
    first = study.supplies[0]
    scenario = first.scenarios[0]
    point = scenario.points[0]
    point = replace(point, anchor_wild_type=EndpointValues(Exact.of(10), Exact.of(238)), anchor_source=point.sources[0])
    first = replace(first, scenarios=(replace(scenario, points=(point,)),))
    study = replace(study, supplies=(first, study.supplies[1]))
    with localcontext() as context:
        context.prec = 2
        result = report(study)
    rows = list(csv.DictReader(io.StringIO(render_endpoint_csv(result))))
    assert rows[0]["anchor_wt_kcat_c_s_inv"] == "10" and rows[0]["anchored_mutant_kcat_c_s_inv"] == "15"
    assert rows[0]["turnover_ratio"] == "3/2" and rows[0]["specificity_ratio"] == "1"
    assert rows[0]["log_specificity_lower"] == rows[0]["log_specificity_upper"] == "0"
    assert "Shared anchor dependence is retained" in render_reference_report(result)
    assert len(result.biological_support.selection.anchor_uses[0]) == 1


def test_unknown_contact_and_costs_remain_in_complete_work_census():
    state = work_bound_case(known=False).state
    result = report(state=state)
    rows = list(csv.DictReader(io.StringIO(render_attempt_csv(result))))
    assert len(rows) == 1 and rows[0]["status"] == "UNCERTAIN_CONTACT" and rows[0]["method_id"] == "UNKNOWN"
    assert rows[0]["cpu_seconds"] == rows[0]["wall_seconds"] == rows[0]["retained_bytes"] == "UNKNOWN"
    assert "UNCERTAIN_CONTACT" in render_reference_report(result)
    with pytest.raises(ValueError, match="work and its complete cost"):
        replace(result, cost_census=None)
    with pytest.raises(ValueError, match="another scientific question"):
        replace(result, work_state=state)


def test_report_reassesses_original_results_without_invoking_any_producer(monkeypatch):
    study = disclosed_study()
    predictions = predict_response_study(study, prediction_id="prediction.no-replay")
    def forbidden(*args, **kwargs):
        pytest.fail("report entered original producer")
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    for name in ("solve_four_state", "intrinsic_constants", "endpoint_sensitivities"):
        monkeypatch.setattr(kinetic_model, name, forbidden)
    result = report(study, predictions)
    assert result.action.conditional_action == "ADVANCE" and result.new_native_calls == 0
    with pytest.raises(ValueError, match="independent nomination"):
        replace(result, conditional_assessment=replace(result.conditional_assessment, conditional_candidate_action="HOLD"))


def test_guarded_report_export_has_complete_atomic_members_and_rechecks_source(tmp_path, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import report as api
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    value = report()
    root = tmp_path / "report-custody"
    root.mkdir()
    mount = next(path for path in (root, *root.parents) if path.is_mount())
    writer = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract("report.exposed", "Disclosed report fixture",
        str(root), str(mount), "empirical-lawhood/testing/report-fixture", 1)))
    monkeypatch.setattr(api, "read_reference_report", lambda **kwargs: value)
    current = SimpleNamespace(study=value.study, predictions=value.predictions,
        producing_receipts=(), inquiry=SimpleNamespace(state=None, specification=None))
    calls = []
    def recheck(**kwargs):
        calls.append(kwargs["directory"])
        return current
    monkeypatch.setattr(api, "read_reference_analysis", recheck)
    cutoff = InformationCutoff("cutoff.report", "clock.rubisco.physical-seconds", CausalPhase.POST_OUTCOME, D(0))
    output = api.export_reference_report(directory=root/"original", output_relative_path="reports/one",
                                         information_cutoff=cutoff, artifact_writer=writer)
    assert calls == [root/"original"] and tuple(output["paths"]) == api.REPORT_MEMBERS
    assert len(output["publications"]) == 5
    for name, path in output["paths"].items():
        assert Path(path).is_file() and Path(path + ".manifest.json").is_file()
    assert decode_canonical_bytes(Path(output["paths"]["readout.json"]).read_bytes(), ReferenceFindingReport, maximum_bytes=3_000_000) == value
    current.predictions = replace(current.predictions, prediction_id="changed.before.publication")
    with pytest.raises(ValueError, match="changed before publication"):
        api.export_reference_report(directory=root/"original", output_relative_path="reports/two",
                                    information_cutoff=cutoff, artifact_writer=writer)
    assert not (root/"reports/two/readout.json").exists()
    with pytest.raises(ValueError):
        api.export_reference_report(directory=root/"original", output_relative_path="../outside",
                                    information_cutoff=cutoff, artifact_writer=writer)
