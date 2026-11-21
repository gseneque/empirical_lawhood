# SPDX-License-Identifier: MPL-2.0
"""Integrated exposed findings, full censuses and guarded atomic publication."""

import csv
from dataclasses import replace
import io
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.comparison_assessment import RetainedComparisonArm, assess_retained_comparison
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import ARMS
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import COMPONENTS
from empirical_lawhood.domains.rubisco.rubisco_response.integrated_report import IntegratedResponseReport, build_integrated_report
from empirical_lawhood.domains.rubisco.rubisco_response.integrated_rendering import render_comparison_csv, render_cost_csv, render_decision_csv, render_integrated_attempts, render_integrated_endpoints, render_integrated_parameters, render_integrated_report, render_requirement_csv
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import assess_reduction_target
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.rubisco_response_comparison_fixture import arm_report, decision, design


def comparison(selected, reports, decisions=()):
    return assess_retained_comparison(selected, tuple(RetainedComparisonArm(arm, reports.get(arm)) for arm in ARMS),
        decisions, assessment_id="comparison.integrated.exposed")


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


@pytest.fixture(scope="module")
def inputs():
    selected = design()
    reports = {arm: arm_report(selected, arm) for arm in ARMS}
    decisions = tuple(decision(selected, i) for i in range(2))
    return selected, reports, decisions


@pytest.fixture(scope="module")
def result(inputs):
    return build_integrated_report(comparison(*inputs), report_id="report.integrated.exposed")


def test_complete_exposed_results_keep_candidate_and_all_scientific_requirements_separate(result, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    def forbidden(*args, **kwargs):
        pytest.fail("integrated report entered an original numerical producer")
    for name in ("solve_four_state", "intrinsic_constants", "endpoint_sensitivities"):
        monkeypatch.setattr(kinetic_model, name, forbidden)
    checked = build_integrated_report(result.comparison, report_id=result.report_id)
    assert checked == result
    assert result.reference.action.conditional_action == "ADVANCE" and result.reference.action.biological_action == "HOLD"
    assert result.comparison.reduced_conditional_fidelity is A.SATISFIED
    assert result.comparison.service.useful_service_disposition is A.SATISFIED
    assert result.milestone.status == "OPEN" and tuple(row.component for row in result.milestone.components) == COMPONENTS
    assert all(row.disposition is A.UNEVALUABLE for row in result.milestone.components)
    assert result.native_entry_status == "NOT_READY" and result.target_assessment.selected_target is None
    assert len(result.target_assessment.candidates) == 16 and result.new_native_calls == 0
    assert set(result.comparison.remaining_requirement_ids) <= set(result.remaining_requirement_ids)
    assert decode_canonical_bytes(result.canonical_bytes(), IntegratedResponseReport, maximum_bytes=24_000_000) == result
    with pytest.raises(ValueError, match="native entry prerequisite"):
        replace(result, native_entry_prerequisites=result.native_entry_prerequisites[:-1])
    with pytest.raises(ValueError, match="remaining scientific"):
        replace(result, remaining_requirement_ids=())
    with pytest.raises(ValueError, match="grant native"):
        replace(result, native_entry_status="READY")


def test_full_readable_and_tabular_projections_retain_methods_units_and_exact_unknown_costs(result):
    assert len(rows(render_integrated_endpoints(result))) == 6
    assert len(rows(render_integrated_parameters(result))) == 48
    compared = rows(render_comparison_csv(result))
    assert len(compared) == 24 and {row["normalized_absolute_upper"] for row in compared} == {"0"}
    assert {row["joint_error"] for row in compared} == {"WITHIN"}
    assert len(rows(render_decision_csv(result))) == 2
    assert len(rows(render_integrated_attempts(result))) == 3
    costs = rows(render_cost_csv(result))
    assert len(costs) == 13 and costs[0]["cpu_seconds"] == "30"
    assert {row["cpu_seconds"] for row in costs[1:]} == {"UNKNOWN"}
    assert len(rows(render_requirement_csv(result))) == len(result.remaining_requirement_ids)
    text = render_integrated_report(result)
    assert "Conditional candidate action: ADVANCE. Biological action: HOLD." in text
    assert "Assignments=6; cases=2; exposure groups=1; biological units=0" in text
    assert "conditional reduced fidelity=SATISFIED" in text and "approximation-fidelity: UNEVALUABLE" in text
    assert "PROJECTION=UNKNOWN" in text and "peak-memory-bytes" in text
    assert "no simulator speedup" in text and "Decimal(" not in text


def test_missing_arms_and_decisions_keep_all_rows_and_never_display_zero_error(inputs):
    selected, reports, _ = inputs
    result = build_integrated_report(comparison(selected, {"reference": reports["reference"]}), report_id="report.missing.arms")
    endpoints = rows(render_integrated_endpoints(result))
    assert len(endpoints) == 6 and sum(row["wt_kcat_c_s_inv"] == "UNKNOWN" for row in endpoints) == 4
    parameters = rows(render_integrated_parameters(result))
    assert len(parameters) == 48 and sum(row["wt_value"] == "UNKNOWN" for row in parameters) == 32
    assert {row["normalized_absolute_upper"] for row in rows(render_comparison_csv(result))} == {"UNKNOWN"}
    assert {row["actual_action"] for row in rows(render_decision_csv(result))} == {"UNKNOWN"}
    assert "original custody NOT_SUPPLIED" in render_integrated_report(result)
    absent = comparison(selected, {})
    with pytest.raises(ValueError, match="original reference finding"):
        build_integrated_report(absent, report_id="report.no.reference")


def test_known_bad_admission_survives_report_without_becoming_native_qualification(inputs):
    selected, reports, decisions = inputs
    bad = arm_report(selected, "reduced", bad=True)
    result = build_integrated_report(comparison(selected, {**reports, "reduced": bad}, decisions), report_id="report.bad.admission")
    assert result.comparison.reduced_conditional_fidelity is A.FALSIFIED
    assert result.comparison.service.false_admission_disposition is A.FALSIFIED
    assert result.milestone.components[3].disposition is A.UNEVALUABLE
    compared = rows(render_comparison_csv(result))
    bad_rows = [row for row in compared if row["arm"] == "reduced" and row["case_id"].endswith("candidate")]
    assert {row["joint_error"] for row in bad_rows} == {"FAILED"}
    assert {row["arithmetic_gate"] for row in bad_rows} == {"FALSIFIED"}
    text = render_integrated_report(result)
    assert "conditional reduced fidelity=FALSIFIED" in text and "criterion=FALSIFIED" in text
    other_target = assess_reduction_target(reports["conventional"], assessment_id="target.foreign")
    with pytest.raises(ValueError, match="another reference"):
        replace(result, target_assessment=other_target)


def test_actual_hold_census_reports_undefined_admitted_denominator_and_failed_service(inputs):
    selected, reports, _ = inputs
    decisions = tuple(decision(selected, i, hold=True) for i in range(2))
    result = build_integrated_report(comparison(selected, reports, decisions), report_id="report.all.hold")
    text = render_integrated_report(result)
    assert "Useful reduced service=[0, 0]; criterion=FALSIFIED" in text
    assert "admitted groups=UNDEFINED_NO_ADMISSIONS" in text
    assert {row["actual_action"] for row in rows(render_decision_csv(result))} == {"HOLD"}


def test_atomic_export_rechecks_all_original_custody_and_preserves_lineage(result, tmp_path, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import integrated_report as api
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    def forbidden(*args, **kwargs):
        pytest.fail("integrated report entered a worker")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    root = tmp_path / "integrated-custody"
    root.mkdir()
    mount = next(path for path in (root, *root.parents) if path.is_mount())
    writer = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract("integrated.exposed", "Disclosed integrated report fixture",
        str(root), str(mount), "empirical-lawhood/testing/integrated-report", 1)))
    calls = []
    def read(**kwargs):
        calls.append(kwargs)
        return result.comparison
    monkeypatch.setattr(api, "read_comparison_analysis", read)
    arguments = dict(design=result.comparison.design, arm_directories={arm: root/arm for arm in ARMS},
        information_cutoff=result.reference.work_state.information_cutoff, artifact_writer=writer,
        decision_directories={row.case.object_id: (root/row.case.object_id,) for row in result.comparison.cases})
    exported = api.export_integrated_report(output_relative_path="reports/accepted", **arguments)
    assert len(calls) == 2 and all(call == {**arguments, "source_audit": None,
        "nomination_dossier": None, "nomination_receipt": None} for call in calls)
    assert tuple(exported["paths"]) == api.REPORT_MEMBERS and len(exported["publications"]) == 10
    assert exported["combined_milestone"] == "OPEN" and exported["native_entry_status"] == "NOT_READY"
    readout = decode_canonical_bytes(Path(exported["paths"]["readout.json"]).read_bytes(), IntegratedResponseReport, maximum_bytes=24_000_000)
    assert readout.comparison == result.comparison
    for path in exported["paths"].values():
        assert Path(path).is_file() and Path(path + ".manifest.json").is_file()
    parents = api._parents(readout, None)
    pins = {row.identity for row in parents}
    assert {row.identity for row in result.comparison.decisions} <= pins
    assert len(parents) >= 10
    actual = result.comparison
    def changed(**kwargs):
        nonlocal actual
        value = actual
        actual = replace(actual, assessment_id="comparison.changed.before.write")
        return value
    monkeypatch.setattr(api, "read_comparison_analysis", changed)
    with pytest.raises(ValueError, match="changed before publication"):
        api.export_integrated_report(output_relative_path="reports/refused", **arguments)
    assert not (root/"reports/refused/readout.json").exists()
    with pytest.raises(ValueError):
        api.export_integrated_report(output_relative_path="../outside", **arguments)
