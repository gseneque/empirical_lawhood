# SPDX-License-Identifier: MPL-2.0
"""Disclosed mathematical controls for dependent support and alternative models."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_assessment import PairedDecisionAssessment, _clip_hull, assess_paired_support
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import ANCHORED_LOG_AXES, RAW_LOG_AXES, ConservativeScenarioCompletion, EndpointValues, JointEndpointRegion, JointLogCovariance, PairedDecisionRegion, PairedJointValue, PairedKineticSupport, PairedScenarioSupport, anchor_joint_value, anchored_log_covariance
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, ConditionRole, ContributionRole, RequirementSupplyAssessment, ScientificConnectionSpec, ScientificRequirementSpec

SOURCE = ObjectIdentity("source.disclosed", "empirical-lawhood/rubisco-response/disclosed", "1.0.0", "a" * 64)
CASE = ObjectIdentity("case.disclosed", "empirical-lawhood/rubisco-response/paired-case", "1.0.0", "b" * 64)
CONTEXT = ObjectIdentity("context.disclosed", "empirical-lawhood/rubisco-response/assay-context", "1.0.0", "c" * 64)


def value(name="point.a", mutant=(2, 2), wt=(1, 1)):
    return PairedJointValue(name, EndpointValues.of(*wt), EndpointValues.of(*mutant))


def region(*points, geometry="FINITE_POINTS", **kwargs):
    return JointEndpointRegion("region.disclosed", points, geometry, "FINITE_JOINT_SUPPORT", (SOURCE,), **kwargs)


def scenario(name="scenario.a", *points, geometry="FINITE_POINTS"):
    return PairedScenarioSupport(name, "AVAILABLE", region(*points, geometry=geometry), (SOURCE,), ())


def support(*rows, prerequisites=()):
    return PairedKineticSupport("support.disclosed", CASE, CONTEXT, tuple(row.scenario_id for row in rows),
                                rows, (SOURCE,), prerequisites)


def decision(**kwargs):
    return replace(PairedDecisionRegion("decision.disclosed", CASE, CONTEXT, D(1), D(1), None, None,
                   "RAW", "Choose the next disclosed control", (SOURCE,), strict_turnover_increase=True), **kwargs)


def assess(*rows, refinement=None, **kwargs):
    return assess_paired_support(support(*rows, **kwargs), decision(),
                                assessment_id="assessment.disclosed", permitted_refinement_id=refinement)


@pytest.mark.parametrize(("points", "action"), [
    ((value(),), "ADVANCE"),
    ((value(mutant=(F(1, 2), 2)),), "DEPRIORITIZE"),
    ((value(mutant=(2, F(1, 2))),), "DEPRIORITIZE"),
    ((value(mutant=(1, 2)),), "DEPRIORITIZE"),
    ((value("point.a"), value("point.b", mutant=(F(1, 2), 2))), "HOLD"),
    ((), "HOLD"),
])
def test_joint_threshold_and_nonempty_support(points, action):
    result = assess(scenario("scenario.a", *points))
    assert result.conditional_action == action
    assert result.probability_of_joint_success is None
    assert result.biological_predictive_calibration == "NOT_ESTABLISHED"
    assert decode_canonical_bytes(result.canonical_bytes(), PairedDecisionAssessment, maximum_bytes=100_000) == result


def test_conflicting_alternatives_do_not_apply_any_member_fails_rule_or_average():
    good, bad = scenario("scenario.a", value()), scenario("scenario.b", value(mutant=(F(1, 2), 2)))
    result = assess(good, bad)
    assert result.conditional_action == "HOLD"
    assert tuple(row.finding for row in result.findings) == ("SUPPORTED", "ADVERSE")
    assert assess(good, bad, refinement="refinement.selected").conditional_action == "REFINE"
    assert assess(bad).conditional_action == "DEPRIORITIZE"
    assert assess(good, prerequisites=("requirement.chemistry",)).conditional_action == "HOLD"


@pytest.mark.parametrize("state", ["UNKNOWN", "FAILED"])
def test_unknown_and_failed_alternatives_are_kept_in_the_denominator(state):
    unresolved = PairedScenarioSupport("scenario.b", state, None, (SOURCE,), ("requirement.missing",))
    result = assess(scenario("scenario.a", value()), unresolved, refinement="refinement.selected")
    assert result.conditional_action == "HOLD"
    assert result.unresolved_requirement_ids == ("requirement.missing",)
    assert result.findings[1].original_state == state and result.findings[1].region is None


def test_continuous_hull_can_intersect_while_every_declared_vertex_is_adverse():
    points = (value("point.a", mutant=(3, F(1, 2))), value("point.b", mutant=(F(1, 2), 3)))
    # The midpoint is (1.75, 1.75), so a convex region crosses the joint boundary.
    assert assess(scenario("scenario.a", *points)).conditional_action == "DEPRIORITIZE"
    continuous = assess(scenario("scenario.a", *points, geometry="CONVEX_HULL"))
    assert continuous.findings[0].finding == "OVERLAP"
    assert continuous.conditional_action == "HOLD"


def test_strict_boundary_and_finite_complexity_stop_are_not_admission():
    points = ((F(0), F(1)), (F(1), F(0)))
    strict = (((F(1), F(0)), F(1), True),)
    assert _clip_hull(points, strict) == ()
    assert _clip_hull(points, (((F(1), F(0)), F(1, 2), False),), vertex_limit=1) is None


def test_anchor_keeps_raw_outputs_and_applies_the_same_paired_effect():
    raw = value(mutant=(6, 36), wt=(3, 40))
    anchored = anchor_joint_value(raw, EndpointValues.of(10, 100))
    assert anchored.wild_type == raw.wild_type and anchored.mutant == raw.mutant
    assert anchored.anchored_mutant == EndpointValues.of(20, 90)
    assert anchored.turnover_ratio == 2 and anchored.specificity_ratio == F(9, 10)
    with pytest.raises(ValueError, match="twice"):
        anchor_joint_value(anchored, EndpointValues.of(10, 100))
    with pytest.raises(ValueError, match="paired raw"):
        replace(anchored, anchored_mutant=EndpointValues.of(25, 100))


def test_anchored_absolute_floor_and_missing_reference_have_different_results():
    raw = value(mutant=(2, 2))
    selected = decision(endpoint_view="ANCHORED", absolute_turnover_floor_s_inv=D(15))
    original = support(scenario("scenario.a", raw))
    assert assess_paired_support(original, selected, assessment_id="assessment.raw").conditional_action == "HOLD"
    anchored = anchor_joint_value(raw, EndpointValues.of(10, 10))
    bound_region = region(anchored, anchor_source=SOURCE)
    supplied = support(PairedScenarioSupport("scenario.a", "AVAILABLE", bound_region, (SOURCE,), ()))
    assert assess_paired_support(supplied, selected, assessment_id="assessment.anchored").conditional_action == "ADVANCE"


def test_shared_reference_covariance_cancels_common_error_without_assuming_independence():
    # A single shared scalar drives all six log coordinates: exact rank one.
    covariance = JointLogCovariance(ANCHORED_LOG_AXES, tuple((D(1),) * 6 for _ in range(6)), (SOURCE,))
    result = anchored_log_covariance(covariance)
    assert all(item.fraction == 1 for row in result for item in row)
    independent = JointLogCovariance(ANCHORED_LOG_AXES,
        tuple(tuple(D(int(i == j)) for j in range(6)) for i in range(6)), (SOURCE,))
    transformed = anchored_log_covariance(independent)
    assert transformed[2][2].fraction == 3 and transformed[0][2].fraction == 1
    assert region(value()).covariance is None  # Unknown is not a zero covariance matrix.
    with pytest.raises(ValueError, match="reference axes"):
        anchored_log_covariance(JointLogCovariance(RAW_LOG_AXES, tuple((D(0),) * 4 for _ in range(4)), (SOURCE,)))


@pytest.mark.parametrize("entries", [
    ((-1, 0), (0, 1)), ((0, 1), (1, 1)), ((1, 2), (2, 1)), ((1, 0), (1, 1)),
])
def test_impossible_covariance_cannot_be_declared(entries):
    matrix = tuple(tuple(D(entries[i][j]) if i < 2 and j < 2 else D(int(i == j))
                         for j in range(4)) for i in range(4))
    with pytest.raises(ValueError, match="symmetric|semidefinite"):
        JointLogCovariance(RAW_LOG_AXES, matrix, (SOURCE,))


def completion(original, *, extra_requirement=False):
    requirement = ScientificRequirementSpec("requirement.missing", "rubisco-response.assess",
        ConditionRole.EVIDENTIAL, "Complete a missing mathematical support",
        "Conservative enclosure covers the missing scenario", None, "rubisco-response.enclosure-assess",
        "A support member lies outside the enclosure", (ContributionRole.RETAINED_ANALYSIS_INPUT,))
    connection = ScientificConnectionSpec("connection.enclosure", requirement.requirement_id,
        "rubisco-response.enclosure", "product", "support", requirement.assessment_operation_id,
        "claim.enclosure", ContributionRole.RETAINED_ANALYSIS_INPUT, requirement.falsifier)
    enclosure = replace(region(value()), uncertainty_kind="CONSERVATIVE_ERROR_SET")
    assessment = RequirementSupplyAssessment("assessment.enclosure",
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), AssessmentPhase.ADMISSION,
        AssessmentDisposition.SATISFIED, original.scenario_id,
        tuple(sorted((enclosure.identity, SOURCE), key=lambda row: row.object_id)), ())
    phases = tuple(replace(assessment, assessment_id="assessment.enclosure." + phase.value.lower(), phase=phase)
                   for phase in (AssessmentPhase.PROCEDURE, AssessmentPhase.INSTANCE, AssessmentPhase.JOINED))
    selected = ConservativeScenarioCompletion(enclosure, requirement, connection, assessment, phases, CASE, CONTEXT)
    pending = ("requirement.missing", "requirement.other") if extra_requirement else ("requirement.missing",)
    return replace(original, completion=selected, unresolved_requirement_ids=pending)


def test_conservative_completion_retains_failed_history_and_only_discharges_its_requirement():
    failed = PairedScenarioSupport("scenario.a", "FAILED", None, (SOURCE,), ("requirement.missing",))
    completed = completion(failed)
    result = assess(completed)
    assert result.conditional_action == "ADVANCE"
    assert result.findings[0].original_state == "FAILED" and result.findings[0].completed_conservatively
    still_pending = assess(completion(failed, extra_requirement=True))
    assert still_pending.conditional_action == "HOLD"
    assert still_pending.unresolved_requirement_ids == ("requirement.other",)
    with pytest.raises(ValueError, match="unresolved scenario"):
        replace(completed, scenario_id="scenario.substituted")
    with pytest.raises(ValueError, match="all four"):
        replace(completed.completion, other_phase_assessments=())
    with pytest.raises(ValueError, match="paired case or context"):
        support(replace(completed, completion=replace(completed.completion, context=replace(CONTEXT, object_id="context.other"))))
    with pytest.raises(ValueError, match="conservative region"):
        replace(completed.completion, assessment=replace(completed.completion.assessment, phase=AssessmentPhase.PROCEDURE))


def test_declared_coverage_is_not_probability_of_success_or_model_weight():
    declared = replace(region(value()), uncertainty_kind="DECLARED_PROBABILISTIC_JOINT_REGION",
                       declared_coverage=D("0.9"), coverage_source=SOURCE)
    row = PairedScenarioSupport("scenario.a", "AVAILABLE", declared, (SOURCE,), ())
    assert assess(row).probability_of_joint_success is None
    with pytest.raises(ValueError, match="probability level"):
        replace(declared, uncertainty_kind="CONSERVATIVE_ERROR_SET")
    with pytest.raises(ValueError, match="source closure"):
        replace(declared, coverage_source=replace(SOURCE, object_id="source.unbound"))


def test_scope_census_and_claim_substitutions_are_refused():
    supplied = support(scenario("scenario.a", value()))
    with pytest.raises(ValueError, match="declared alternative"):
        replace(supplied, expected_scenario_ids=("scenario.a", "scenario.b"))
    with pytest.raises(ValueError, match="assay context"):
        assess_paired_support(supplied, decision(context=replace(CONTEXT, object_fingerprint="d" * 64)),
                              assessment_id="assessment.wrong-context")
    with pytest.raises(ValueError, match="preservation"):
        decision(minimum_specificity_ratio=D("0.9"))
    with pytest.raises(ValueError, match="slower turnover"):
        decision(minimum_turnover_ratio=D("0.9"))
    with pytest.raises(ValueError, match="biological calibration"):
        replace(supplied, biological_predictive_calibration="VALIDATED")
