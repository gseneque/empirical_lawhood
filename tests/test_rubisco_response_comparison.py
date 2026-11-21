# SPDX-License-Identifier: MPL-2.0
"""Exposed comparison falsifiers; synthetic authority is never qualification."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_assessment import ARMS, RetainedComparisonArm, ResponseComparisonAssessment, assess_retained_comparison
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_cost import assess_comparison_costs
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import COST_ARMS, ComparisonWorkAllocation
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.study import exposed_source_allocation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryAttemptStatus as S
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.rubisco_response_comparison_fixture import arm_report, decision, design, state, work
from tests.test_recursive_inquiry_policy import obj


def assess(selected, reports, decisions=()):
    arms = tuple(RetainedComparisonArm(arm, reports.get(arm)) for arm in ARMS)
    return assess_retained_comparison(selected, arms, decisions, assessment_id="comparison.exposed.result")


@pytest.fixture(scope="module")
def complete():
    selected = design()
    reports = {arm: arm_report(selected, arm) for arm in ARMS}
    decisions = tuple(decision(selected, i) for i in range(len(selected.cases)))
    return selected, reports, decisions


def test_complete_retained_math_service_and_fidelity_cannot_become_prospective(complete, monkeypatch):
    selected, reports, decisions = complete
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    def forbidden(*args, **kwargs):
        pytest.fail("retained comparison entered an original numerical producer")
    for name in ("solve_four_state", "intrinsic_constants", "endpoint_sensitivities"):
        monkeypatch.setattr(kinetic_model, name, forbidden)
    result = assess(selected, reports, decisions)
    assert result.reduced_conditional_fidelity is result.conventional_conditional_fidelity is A.SATISFIED
    assert len(result.points) == 2 and len(result.cases) == 2 and len(result.service.units) == 1
    assert result.service.useful_service_bounds == (Exact.of(1), Exact.of(1))
    assert result.service.false_admission_assigned_bounds == (Exact.of(0), Exact.of(0))
    assert result.service.reference_coverage_disposition is A.SATISFIED
    assert all(row.causal_order is A.UNEVALUABLE for row in result.cases)
    assert result.prospective_qualification is A.UNEVALUABLE and result.biological_validation == "NOT_ESTABLISHED"
    assert result.new_native_calls == 0 and len(result.costs.attempts) == 3
    assert all(row.error.telescoping_product is None and row.error.total.ratio_factors == (Exact.of(1),) * 6 for row in result.points)
    assert result.costs.conditional_cost_criterion is A.UNEVALUABLE  # unclassified actual work
    assert decode_canonical_bytes(result.canonical_bytes(), ResponseComparisonAssessment, maximum_bytes=15_000_000) == result
    with pytest.raises(ValueError, match="prospective or biological"):
        replace(result, prospective_qualification=A.SATISFIED)


def test_bad_admitted_return_is_measured_even_when_its_numerical_claim_fails(complete):
    selected, reports, decisions = complete
    bad = arm_report(selected, "reduced", bad=True)
    assert bad.endpoints[0].numerical_assessment is A.FALSIFIED
    result = assess(selected, {**reports, "reduced": bad}, decisions)
    assert result.points[0].error.total.normalized_absolute_error_bounds[2][0].fraction > 1
    assert result.reduced_conditional_fidelity is A.FALSIFIED and result.cases[0].joint_error == "FAILED"
    assert result.service.useful_service_bounds == (Exact.of(0), Exact.of(0))
    assert result.service.false_admission_assigned_bounds == (Exact.of(1), Exact.of(1))
    assert result.service.false_admission_disposition is A.FALSIFIED
    assert result.conventional_conditional_fidelity is A.SATISFIED


def test_known_bad_point_survives_other_unknown_scenarios_in_same_exposure_unit():
    original = disclosed_study()
    supplies = (disclosed_supply(scenario_states=("AVAILABLE", "UNKNOWN")), original.supplies[1])
    original = replace(original, supplies=supplies, allocation=exposed_source_allocation(original.cases, supplies))
    selected = design(original=original)
    reports = {arm: arm_report(selected, arm, bad=arm == "reduced") for arm in ARMS}
    result = assess(selected, reports, tuple(decision(selected, i) for i in range(2)))
    assert len(result.points) == 3 and result.points[1].point_id is None
    assert result.cases[0].reference_state == "UNKNOWN" and result.cases[0].joint_error == "FAILED"
    assert result.service.false_admission_assigned_bounds == (Exact.of(1), Exact.of(1))
    assert result.service.reference_coverage_disposition is A.UNEVALUABLE


def test_failed_unknown_and_wrong_method_reference_never_count_as_correct(complete):
    selected, reports, decisions = complete
    for reference in (None, arm_report(selected, "reference", failed=True), arm_report(selected, "reference", known_method=False)):
        result = assess(selected, {**reports, "reference": reference}, decisions)
        assert result.reduced_conditional_fidelity is A.UNEVALUABLE
        assert result.service.useful_service_bounds == (Exact.of(0), Exact.of(1))
        assert result.service.false_admission_assigned_bounds == (Exact.of(0), Exact.of(1))
        assert result.service.reference_coverage_disposition is A.UNEVALUABLE
    # The same actual source cannot become three distinct methods by relabelling.
    result = assess(selected, {arm: reports["reference"] for arm in ARMS}, decisions)
    assert result.points[0].method_gates == (("reference", A.SATISFIED), ("conventional", A.FALSIFIED), ("reduced", A.FALSIFIED))
    assert result.reduced_conditional_fidelity is A.UNEVALUABLE and len(result.costs.attempts) == 1


def test_always_abstaining_fails_useful_service_and_keeps_refused_truth(complete):
    selected, reports, _ = complete
    decisions = tuple(decision(selected, i, hold=True) for i in range(2))
    result = assess(selected, reports, decisions)
    assert all(row.action == "HOLD" for row in result.cases)
    assert result.service.useful_service_disposition is A.FALSIFIED
    assert result.service.false_admission_conditional_bounds is None
    assert result.service.reference_coverage_disposition is A.SATISFIED
    missing = assess(selected, {**reports, "reference": None}, decisions)
    assert missing.service.useful_service_disposition is A.FALSIFIED
    assert missing.service.reference_coverage_disposition is A.UNEVALUABLE
    assert len(missing.service.units) == 1


def test_original_reference_already_seen_falsifies_prospective_order(complete):
    selected, reports, decisions = complete
    seen = decision(selected, 0, already_seen=reports["reference"].predictions.identity)
    result = assess(selected, reports, (seen, decisions[1]))
    assert result.cases[0].causal_order is A.FALSIFIED
    assert result.cases[0].causal_reason_codes == ("REFERENCE_ALREADY_IN_ORIGINAL_POLICY_INFORMATION",)
    assert result.prospective_qualification is A.UNEVALUABLE


def test_complete_decision_packets_and_frozen_selection_cannot_be_substituted(complete):
    selected, reports, decisions = complete
    with pytest.raises(ValueError, match="packet bytes"):
        replace(decisions[0], decision=replace(decisions[0].decision, reason="Changed after original commitment"))
    with pytest.raises(ValueError, match="frozen finite-policy"):
        replace(decisions[0], selection=replace(decisions[0].selection, policy_id="substituted.policy"))
    with pytest.raises(ValueError, match="checkpoint"):
        assess(selected, reports, (decisions[0], decisions[0], decisions[1]))
    with pytest.raises(ValueError, match="checkpoint order"):
        assess(selected, reports, tuple(reversed(decisions)))
    other = design(reuse_count=2)
    with pytest.raises(ValueError, match="exact frozen study"):
        assess(other, reports, ())
    result = assess(selected, reports, decisions)
    with pytest.raises(ValueError, match="original returns"):
        replace(result, points=result.points[:1])
    with pytest.raises(ValueError, match="borrows service"):
        replace(result, service=replace(result.service, design=replace(selected, design_id="other.design")))


def cost_case(*, reuse_count=30, failed_use=False, unknown_cost=False, unknown_work=False, missing_work=False):
    selected = design(reuse_count=reuse_count)
    names = ("c.setup", "c.use", "r.setup", "r.use", "shared.audit")
    works = {name: work(selected, name) for name in names}
    allocation = tuple(sorted((ComparisonWorkAllocation(works[name], "AUDIT" if name.endswith("audit") else "SETUP" if name.endswith("setup") else "USE",
        COST_ARMS if name == "shared.audit" else ("conventional",) if name.startswith("c.") else ("reduced",)) for name in names),
        key=lambda row: row.work.fingerprint()))
    selected = replace(selected, cost_work=allocation)
    rows = [(works[name], cpu, S.COMPLETED) for name, cpu in zip(names, (10, 6, 100, 2, 3), strict=True)]
    if failed_use:
        rows.append((works["r.use"], 1, S.FAILED))
    if unknown_cost:
        rows[3] = (works["r.use"], None, S.UNCERTAIN_CONTACT)
    if unknown_work:
        rows.append((None, 9, S.UNCERTAIN_CONTACT))
    if missing_work:
        rows = rows[1:]
    original = state(selected, "costs.exposed", rows)
    return selected, original


def test_campaign_equal_audit_and_amortized_accounts_match_independent_arithmetic():
    selected, original = cost_case()
    result = assess_comparison_costs(selected, (original,), assessment_id="cost.exposed")
    conventional, reduced = result.arms
    assert result.complete_campaign.cpu_seconds == D(121)
    assert conventional.frozen_policy_use.cpu_seconds == D(9) and reduced.frozen_policy_use.cpu_seconds == D(5)
    assert conventional.equivalent_audit.cpu_seconds == reduced.equivalent_audit.cpu_seconds == D(3)
    assert conventional.amortized_total.cpu_seconds == Exact.of(280)
    assert reduced.amortized_total.cpu_seconds == Exact.of(250)
    assert reduced.amortized_per_use.cpu_seconds == Exact.of(Fraction(25, 3))
    assert result.conditional_cost_criterion is A.SATISFIED and result.break_even_reuse_count == 23
    assert result.unmeasured_metric_ids == ("campaign-elapsed-wall-seconds", "gpu-seconds", "native-call-count", "peak-memory-bytes")
    # Re-reading the same original events through another selected state is not new cost.
    duplicate = replace(original, state_id=original.state_id + ".second-read")
    again = assess_comparison_costs(selected, (original, duplicate), assessment_id="cost.deduplicated")
    assert again.complete_campaign == result.complete_campaign and len(again.events) == 5


def test_failed_and_uncertain_work_cannot_be_removed_from_cost_or_service_claims():
    selected, original = cost_case(failed_use=True)
    result = assess_comparison_costs(selected, (original,), assessment_id="cost.failed-use")
    assert result.complete_campaign.cpu_seconds == D(122) and len(result.attempts) == 6
    assert result.arms[1].frozen_policy_use.cpu_seconds == D(6)
    assert result.arms[1].amortized_total.cpu_seconds == Exact.of(280)
    assert result.conditional_cost_criterion is A.FALSIFIED and result.break_even_reuse_count == 31
    for change in ("unknown_cost", "unknown_work", "missing_work"):
        selected, original = cost_case(**{change: True})
        result = assess_comparison_costs(selected, (original,), assessment_id="cost." + change)
        assert result.conditional_cost_criterion is A.UNEVALUABLE and result.break_even_reuse_count is None
        assert result.arms[1].amortized_total.cpu_seconds is None
        if change == "unknown_work":
            assert len(result.unclassified_attempt_ids) == 1 and result.complete_campaign.cpu_seconds == D(130)
        elif change == "missing_work":
            assert len(result.missing_work_fingerprints) == 1
        else:
            assert result.complete_campaign.cpu_seconds is None


def test_cost_exactness_conflicts_and_zero_entry_do_not_invent_savings():
    selected, original = cost_case()
    with localcontext() as context:
        context.prec = 2
        small = assess_comparison_costs(selected, (original,), assessment_id="cost.exact")
    assert small == assess_comparison_costs(selected, (original,), assessment_id="cost.exact")
    altered = replace(original, state_id=original.state_id + ".conflict", cost_events=(
        replace(original.cost_events[0], cost=replace(original.cost_events[0].cost, cpu_seconds=D(11))), *original.cost_events[1:]))
    with pytest.raises(ValueError, match="histories conflict"):
        assess_comparison_costs(selected, (original, altered), assessment_id="cost.conflict")
    empty = assess_comparison_costs(selected, (), assessment_id="cost.absent")
    assert empty.complete_campaign.cpu_seconds is None and empty.conditional_cost_criterion is A.UNEVALUABLE
    no_entry = state(selected, "unentered", ())
    empty = assess_comparison_costs(selected, (no_entry,), assessment_id="cost.zero-entries")
    assert empty.complete_campaign.cpu_seconds == D(0) and empty.conditional_cost_criterion is A.UNEVALUABLE
    with pytest.raises(ValueError, match="original attempt"):
        replace(small, events=small.events[:1])


def test_reference_producing_work_cannot_borrow_another_scientific_source(complete):
    selected, reports, decisions = complete
    original = reports["reference"]
    binding = original.work_state.attempt_work_bindings[0]
    state_value = replace(original.work_state, attempt_work_bindings=(replace(binding,
        work=replace(binding.work, scientific_operands=(obj("other.scientific.input"),))),))
    from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import build_reference_finding_report
    altered = build_reference_finding_report(original.study, original.predictions, original.biological_support,
        report_id="report.wrong-work", producing_receipts=original.producing_receipts,
        inquiry_specification=original.inquiry_specification, work_state=state_value)
    result = assess(selected, {**reports, "reference": altered}, decisions)
    assert result.points[0].method_gates[0][1] is A.FALSIFIED
    assert result.service.reference_coverage_disposition is A.UNEVALUABLE


def test_reference_fallback_and_complete_checkpoint_history_survive_comparison(complete):
    selected, reports, decisions = complete
    fallback = decision(selected, 0, reference=True)
    result = assess(selected, reports, (fallback, decisions[1]))
    assert result.cases[0].action == "REFERENCE" and result.service.fallback_bounds == (Exact.of(1), Exact.of(1))
    assert result.service.useful_service_disposition is A.FALSIFIED
    first = decision(selected, 0, hold=True)
    second = decision(selected, 0, hold=True, previous=(first,))
    result = assess(selected, reports, (first, second, decisions[1]))
    assert len(result.cases[0].decisions) == 2 and result.cases[0].action == "HOLD"
    with pytest.raises(ValueError, match="original decision checkpoint"):
        assess(selected, reports, (second, decisions[1]))


def test_unavailable_anchors_remain_unresolved_at_selected_anchored_scale(complete):
    selected, reports, _ = complete
    selected = replace(selected, scale="ANCHORED")
    result = assess(selected, reports)
    assert result.reduced_conditional_fidelity is A.UNEVALUABLE
    assert all(row.error is None and "MISSING_ORIGINAL_SHARED_WT_ANCHOR" in row.reason_codes for row in result.points)


def test_comparison_api_uses_current_original_readers_and_preflights_all_selectors(complete, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import comparison as api
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
    selected, reports, decisions = complete
    calls = []
    cutoff = InformationCutoff("cutoff.comparison.read", "clock.rubisco.physical-seconds", CausalPhase.POST_OUTCOME, D(100))
    def read_report(**kwargs):
        calls.append(("source", kwargs["directory"]))
        assert kwargs["information_cutoff"] == cutoff and kwargs["artifact_writer"] is writer
        return reports[kwargs["directory"]]
    def read_decision(**kwargs):
        calls.append(("decision", kwargs["directory"]))
        assert kwargs["artifact_writer"] is writer
        return decisions[int(kwargs["directory"])]
    def forbidden(*args, **kwargs):
        pytest.fail("comparison read entered a worker")
    writer = object()
    monkeypatch.setattr(api, "read_reference_report", read_report)
    monkeypatch.setattr(api, "read_finite_response_policy", read_decision)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    directories = {arm: arm for arm in ARMS}
    histories = {row.case.object_id: (str(i),) for i, row in enumerate(selected.cases)}
    result = api.read_comparison_analysis(design=selected, arm_directories=directories, information_cutoff=cutoff,
        artifact_writer=writer, decision_directories=histories)
    assert result.service.useful_service_disposition is A.SATISFIED
    assert calls == [("source", arm) for arm in ARMS] + [("decision", "0"), ("decision", "1")]
    calls.clear()
    for kwargs in ({"arm_directories": {"reference": "reference"}},
            {"decision_directories": {selected.cases[0].case.object_id: ["0"]}},
            {"decision_directories": {"foreign.case": ()}},
            {"information_cutoff": replace(cutoff, phase=CausalPhase.PRE_ACTION)}):
        options = dict(design=selected, arm_directories=directories, information_cutoff=cutoff,
            artifact_writer=writer, decision_directories=histories)
        options.update(kwargs)
        with pytest.raises(ValueError):
            api.read_comparison_analysis(**options)
        assert not calls
    with pytest.raises(ValueError, match="another case"):
        api.read_comparison_analysis(design=selected, arm_directories=directories, information_cutoff=cutoff,
            artifact_writer=writer, decision_directories={selected.cases[0].case.object_id: ("1",)})
