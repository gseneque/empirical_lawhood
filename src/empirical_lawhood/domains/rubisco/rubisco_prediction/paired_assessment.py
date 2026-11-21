# SPDX-License-Identifier: MPL-2.0
"""Exact nonempty union decisions; no averaging or failed-scenario deletion."""

from dataclasses import dataclass
from fractions import Fraction as F
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion, PairedKineticSupport


@dataclass(frozen=True, slots=True)
class PairedScenarioFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-scenario-finding"
    scenario_id: str
    finding: str
    original_state: str
    completed_conservatively: bool
    region: ObjectIdentity | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.scenario_id)
        if self.finding not in {"SUPPORTED", "ADVERSE", "OVERLAP", "HOLD"}:
            raise ValueError("unknown regional finding")
        if self.original_state not in {"AVAILABLE", "UNKNOWN", "FAILED"}:
            raise ValueError("finding loses original outcome")
        if type(self.completed_conservatively) is not bool:
            raise TypeError("finding requires its conservative completion flag")
        if self.region is not None:
            exact(self.region, ObjectIdentity)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.finding == "HOLD" and not self.reason_codes:
            raise ValueError("HOLD needs the actual unresolved reason")


@dataclass(frozen=True, slots=True)
class PairedDecisionAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-decision-assessment"
    assessment_id: str
    support: ObjectIdentity
    decision: ObjectIdentity
    findings: tuple[PairedScenarioFinding, ...]
    conditional_action: str
    unresolved_requirement_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    permitted_refinement_id: str | None
    biological_predictive_calibration: str = "NOT_ESTABLISHED"
    probability_of_joint_success: None = None

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for value, kind in ((self.support, PairedKineticSupport), (self.decision, PairedDecisionRegion)):
            exact(value, ObjectIdentity)
            if value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("paired assessment substitutes its exact support or decision")
        if type(self.findings) is not tuple or not self.findings:
            raise ValueError("paired assessment requires the complete nonempty alternative census")
        require_sorted_unique_strings(tuple(row.scenario_id for row in self.findings), field_name="scenario_ids", allow_empty=False)
        for finding in self.findings:
            exact(finding, PairedScenarioFinding)
        if self.conditional_action not in {"ADVANCE", "DEPRIORITIZE", "REFINE", "HOLD"}:
            raise ValueError("unknown conditional action")
        for name in ("unresolved_requirement_ids", "reason_codes"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if self.permitted_refinement_id is not None:
            validate_stable_id(self.permitted_refinement_id)
        if self.conditional_action == "REFINE" and self.permitted_refinement_id is None:
            raise ValueError("refinement needs an actual permitted finite action")
        if (self.biological_predictive_calibration != "NOT_ESTABLISHED"
                or self.probability_of_joint_success is not None):
            raise ValueError("regional decisions cannot manufacture biological probability")



def _constraints(decision, width):
    # Each constraint is coefficients dot coordinates >= lower.
    base = 0 if decision.endpoint_view == "RAW" else 4
    if width < base + 4:
        return None
    constraints = []
    for endpoint, ratio in ((0, decision.minimum_turnover_ratio), (1, decision.minimum_specificity_ratio)):
        coefficients = [F(0)] * width
        coefficients[base + endpoint] = -F(ratio)
        coefficients[base + 2 + endpoint] = F(1)
        constraints.append((tuple(coefficients), F(0), endpoint == 0 and decision.strict_turnover_increase))
    for endpoint, floor in ((0, decision.absolute_turnover_floor_s_inv), (1, decision.absolute_specificity_floor)):
        if floor is not None:
            coefficients = [F(0)] * width
            coefficients[base + 2 + endpoint] = F(1)
            constraints.append((tuple(coefficients), F(floor), False))
    return tuple(constraints)


def _slack(point, constraint):
    coefficients, lower, _ = constraint
    return sum(a * b for a, b in zip(coefficients, point, strict=True)) - lower


def _inside(point, constraints):
    return all(_slack(point, c) > 0 if c[2] else _slack(point, c) >= 0 for c in constraints)


def _clip_hull(points, constraints, *, vertex_limit=4096):
    """Exact halfspace intersection, retaining all inside/outside pair cuts.

    All original polytope edges occur among these pairs. Extra pair cuts are
    inside the same polytope and cannot enlarge its clipped convex hull.
    A finite complexity stop is unknown, never evidence of empty support.
    """
    pair_count = 0
    for constraint in constraints:
        inside, outside = [], []
        for point in points:
            slack = _slack(point, constraint)
            (inside if slack >= 0 else outside).append((point, slack))
        if not inside:
            return ()
        retained = {point for point, _ in inside}
        for left, left_slack in inside:
            for right, right_slack in outside:
                pair_count += 1
                if pair_count > 32768:
                    return None
                fraction = left_slack / (left_slack - right_slack)
                retained.add(tuple(a + fraction * (b - a) for a, b in zip(left, right, strict=True)))
                if len(retained) > vertex_limit:
                    return None
        points = tuple(sorted(retained))
    # For each strict halfspace there must be a feasible point with positive
    # slack. Their average satisfies all strict inequalities simultaneously.
    if any(c[2] and not any(_slack(point, c) > 0 for point in points) for c in constraints):
        return ()
    return points


def _region_finding(region, decision):
    if not region.values:
        return "HOLD", ("EMPTY_SUPPORTED_REGION",)
    constraints = _constraints(decision, len(region.values[0].coordinates))
    if constraints is None:
        return "HOLD", ("ANCHORED_ENDPOINTS_UNAVAILABLE",)
    points = tuple(row.coordinates for row in region.values)
    if all(_inside(point, constraints) for point in points):
        return "SUPPORTED", ()
    if region.geometry == "FINITE_POINTS":
        intersects = any(_inside(point, constraints) for point in points)
    else:
        clipped = _clip_hull(points, constraints)
        if clipped is None:
            return "HOLD", ("EXACT_REGION_COMPLEXITY_LIMIT",)
        intersects = bool(clipped)
    return ("OVERLAP", ()) if intersects else ("ADVERSE", ())


def assess_paired_support(support, decision, *, assessment_id, permitted_refinement_id=None):
    exact(support, PairedKineticSupport)
    exact(decision, PairedDecisionRegion)
    if (support.case, support.context) != (decision.case, decision.context):
        raise ValueError("decision changes the exact paired material or assay context")
    if permitted_refinement_id is not None:
        validate_stable_id(permitted_refinement_id)
    findings, unresolved = [], set(support.prerequisite_requirement_ids)
    for scenario in support.scenarios:
        remaining = set(scenario.unresolved_requirement_ids)
        if scenario.completion is not None:
            remaining.remove(scenario.completion.requirement.requirement_id)
        unresolved.update(remaining)
        region = scenario.effective_region
        if region is None:
            finding, reasons = "HOLD", ("SCENARIO_SUPPORT_UNRESOLVED",)
        else:
            finding, reasons = _region_finding(region, decision)
            if scenario.completion is None and scenario.original_state != "AVAILABLE":
                raise ValueError("unresolved scenario cannot silently acquire a support region")
        findings.append(PairedScenarioFinding(scenario.scenario_id, finding, scenario.original_state,
            scenario.completion is not None, None if region is None else region.identity, reasons))
    states = {row.finding for row in findings}
    if unresolved or "HOLD" in states:
        action, reasons = "HOLD", ("UNRESOLVED_PREREQUISITE_OR_SUPPORT",)
    elif states == {"SUPPORTED"}:
        action, reasons = "ADVANCE", ()
    elif states == {"ADVERSE"}:
        action, reasons = "DEPRIORITIZE", ()
    else:
        action = "REFINE" if permitted_refinement_id is not None else "HOLD"
        reasons = ("JOINT_REGION_CROSSES_DECISION_BOUNDARY",)
    return PairedDecisionAssessment(assessment_id, ObjectIdentity.from_record(support.support_id, support),
        ObjectIdentity.from_record(decision.decision_id, decision), tuple(findings), action,
        tuple(sorted(unresolved)), reasons, permitted_refinement_id)
