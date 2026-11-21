# SPDX-License-Identifier: MPL-2.0
"""Independent retained-result assessment; never invokes the kinetic producer."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model_assessment import FourStateAssessment, assess_four_state
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_assessment import PairedDecisionAssessment, assess_paired_support
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import PairedPrediction, source_union
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import PairedRateSupply

CHECKS = ("complete-paired-census", "exact-context-and-sources", "joint-endpoint-support", "rate-and-query-correspondence")


@dataclass(frozen=True, slots=True)
class PairedPredictionAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-prediction-assessment"
    assessment_id: str
    supply: ObjectIdentity
    prediction: ObjectIdentity
    disposition: AssessmentDisposition
    checks: tuple[tuple[str, bool], ...]
    kinetic_assessments: tuple[FourStateAssessment, ...]
    decision: PairedDecisionAssessment | None
    reason_codes: tuple[str, ...]
    biological_accuracy: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for record, kind in ((self.supply, PairedRateSupply), (self.prediction, PairedPrediction)):
            exact(record, ObjectIdentity)
            if record.object_schema != kind.SCHEMA or record.object_version != kind.VERSION:
                raise ValueError("prediction assessment changes its exact source identities")
        if (type(self.checks) is not tuple or tuple(name for name, _ in self.checks) != CHECKS
                or any(type(value) is not bool for _, value in self.checks)):
            raise ValueError("prediction assessment loses an independent correspondence check")
        if type(self.kinetic_assessments) is not tuple:
            raise TypeError("kinetic assessment census must be immutable")
        for assessment in self.kinetic_assessments:
            exact(assessment, FourStateAssessment)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        passed = all(value for _, value in self.checks) and all(
            row.disposition is AssessmentDisposition.SATISFIED for row in self.kinetic_assessments)
        if self.disposition is not (AssessmentDisposition.SATISFIED if passed else AssessmentDisposition.FALSIFIED):
            raise ValueError("prediction disposition differs from its actual independent checks")
        if passed != (self.decision is not None) or bool(self.reason_codes) == passed:
            raise ValueError("a falsified prediction cannot acquire a candidate decision")
        if self.decision is not None:
            exact(self.decision, PairedDecisionAssessment)
        if self.biological_accuracy != "NOT_ESTABLISHED":
            raise ValueError("conditional kinetic assessment cannot establish biological accuracy")

    @property
    def conditional_action(self):
        return "HOLD" if self.decision is None else self.decision.conditional_action


def assess_paired_prediction(supply, prediction, decision, *, assessment_id, permitted_refinement_id=None):
    exact(supply, PairedRateSupply)
    exact(prediction, PairedPrediction)
    exact(decision, PairedDecisionRegion)
    if (decision.case, decision.context) != (supply.case.identity, supply.context.identity):
        raise ValueError("decision changes the exact selected material or assay context")
    expected = {(scenario.scenario_id, point.point_id): point
                for scenario in supply.scenarios for point in scenario.points}
    actual = {(point.scenario_id, point.point_id): point for point in prediction.points}
    complete = tuple(actual) == tuple(expected)
    correspondence = complete and all(
        result.rates == getattr(expected[key], arm) and result.query == supply.query
        for key, point in actual.items() for arm in ("wild_type", "mutant") for result in (getattr(point, arm),))
    independent = tuple(assess_four_state(getattr(point, arm),
        assessment_id=f"{assessment_id}.{point.scenario_id}.{point.point_id}.{arm}")
        for point in prediction.points for arm in ("wild_type", "mutant"))
    supported = prediction.support
    pending = tuple(sorted(set(supply.prerequisite_requirement_ids)
                           | set(supply.context.chemistry.unresolved_requirement_ids)))
    exact_sources = (prediction.supply == supply.identity
        and supported.case == supply.case.identity and supported.context == supply.context.identity
        and supported.expected_scenario_ids == supply.expected_scenario_ids
        and supported.prerequisite_requirement_ids == pending
        and supported.shared_sources == source_union(supply.shared_sources, (supply.identity,)))
    joint = complete and tuple(row.scenario_id for row in supported.scenarios) == supply.expected_scenario_ids
    if joint:
        for original, row in zip(supply.scenarios, supported.scenarios, strict=True):
            sources = source_union(original.sources, (original.ledger.identity,),
                                   *(point.sources for point in original.points))
            unresolved = tuple(sorted(set(original.unresolved_requirement_ids)
                                      | set(original.ledger.unresolved_requirement_ids)))
            exact_sources &= (row.sources == sources and row.unresolved_requirement_ids == unresolved
                              and row.original_state == original.original_state and row.completion is None)
            region = row.region
            if original.original_state != "AVAILABLE":
                joint &= region is None
                continue
            if region is None:
                joint = False
                continue
            exact_sources &= region.sources == sources
            joint &= (region.geometry == "FINITE_POINTS" and region.uncertainty_kind == "FINITE_JOINT_SUPPORT"
                and region.covariance is None and region.declared_coverage is None
                and region.anchor_source == (None if not original.points else original.points[0].anchor_source)
                and tuple(value.value_id for value in region.values) == tuple(point.point_id for point in original.points))
            if tuple(value.value_id for value in region.values) != tuple(point.point_id for point in original.points):
                continue
            for rates, value in zip(original.points, region.values, strict=True):
                outputs = actual[(original.scenario_id, rates.point_id)]
                joint &= (value.anchor_wild_type == rates.anchor_wild_type)
                # Anchored arithmetic is independently required by the value's
                # strict constructor; raw values must equal separately checked outputs.
                for arm in ("wild_type", "mutant"):
                    endpoint = getattr(outputs, arm).intrinsic
                    retained = getattr(value, arm)
                    joint &= retained.kcat_c_s_inv == endpoint.kcat_c and retained.specificity == endpoint.specificity
    checks = tuple(zip(CHECKS, (complete, bool(exact_sources), bool(joint), correspondence), strict=True))
    reasons = tuple(sorted((*("FAILED_" + name.upper() for name, passed in checks if not passed),
        *(("FAILED_INDEPENDENT_KINETICS",) if any(row.disposition is not AssessmentDisposition.SATISFIED
                                                for row in independent) else ()))))
    assessed_decision = None if reasons else assess_paired_support(supported, decision,
        assessment_id=assessment_id + ".decision", permitted_refinement_id=permitted_refinement_id)
    return PairedPredictionAssessment(assessment_id, supply.identity,
        ObjectIdentity.from_record(prediction.prediction_id, prediction),
        AssessmentDisposition.FALSIFIED if reasons else AssessmentDisposition.SATISFIED,
        checks, independent, assessed_decision, reasons)
