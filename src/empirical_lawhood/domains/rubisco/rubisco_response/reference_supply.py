# SPDX-License-Identifier: MPL-2.0
"""Independent reference readout with complete finite support and work costs."""

from dataclasses import dataclass
from decimal import localcontext
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model_assessment import FourStateAssessment
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import AcquisitionEvent, InquiryAttempt, InquiryCost, summarize_cost
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.science.models.time import CausalPhase
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import PairedPrediction
from empirical_lawhood.domains.rubisco.rubisco_response.prediction_assessment import PairedPredictionAssessment, assess_paired_prediction
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import PairedRateSupply
from empirical_lawhood.domains.rubisco.rubisco_response.rate_suppliers import RateSupplierCensus, assess_rate_suppliers
from empirical_lawhood.domains.rubisco.rubisco_response.reference_analysis import EndpointIdentifiability, assess_endpoint_identifiability


def _cost(events):
    # The shared service owns deduplication and unknown-value propagation.
    # Use enough Decimal precision for exact addition of the original decimals.
    if not events:
        return InquiryCost(None, None, None)
    values = [value for event in events for value in
              (event.cost.cpu_seconds, event.cost.wall_seconds, event.cost.retained_bytes) if value is not None]
    integer_digits = max((max(1, value.adjusted() + 1) for value in values), default=1)
    fractional_digits = max((max(0, -value.as_tuple().exponent) for value in values), default=0)
    with localcontext() as context:
        context.prec = integer_digits + fractional_digits + len(str(len(events))) + 2
        return summarize_cost(events)


@dataclass(frozen=True, slots=True)
class ReferenceWorkCost(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-work-cost"
    method: ObjectIdentity | None
    attempts: tuple[InquiryAttempt, ...]
    events: tuple[AcquisitionEvent, ...]
    measured_cost: InquiryCost

    def __post_init__(self):
        if self.method is not None:
            exact(self.method, ObjectIdentity)
        if type(self.attempts) is not tuple or not self.attempts or type(self.events) is not tuple:
            raise ValueError("reference cost group requires the complete nonempty original attempt census")
        require_sorted_unique_ids(self.attempts, attribute="attempt_id", field_name="attempts")
        require_sorted_unique_ids(self.events, attribute="event_id", field_name="events")
        for row in self.attempts:
            exact(row, InquiryAttempt)
        for row in self.events:
            if type(row) is not AcquisitionEvent:
                raise TypeError("reference expense needs the original shared acquisition-event record")
            validate_stable_id(row.event_id)
            validate_stable_id(row.attempt_id)
            exact(row.receipt, ObjectIdentity)
            exact(row.cost, InquiryCost)
        attempts = {row.attempt_id: row.receipt for row in self.attempts}
        if len(self.events) != len(attempts) or {row.attempt_id: row.receipt for row in self.events} != attempts:
            raise ValueError("reference costs omit or substitute an actual failed/unknown attempt receipt")
        exact(self.measured_cost, InquiryCost)
        if self.measured_cost != _cost(self.events):
            raise ValueError("reference cost profile changes actual measured or unknown expense")


@dataclass(frozen=True, slots=True)
class ReferenceCostCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-cost-census"
    census_id: str
    original_state: ObjectIdentity
    expected_attempt_ids: tuple[str, ...]
    groups: tuple[ReferenceWorkCost, ...]
    total: InquiryCost
    interpretation: str = "COMPLETE_RETAINED_OPERATION_COSTS_NOT_A_MOLECULAR_SUPPLIER_PROFILE"

    def __post_init__(self):
        validate_stable_id(self.census_id)
        exact(self.original_state, ObjectIdentity)
        if (self.original_state.object_schema, self.original_state.object_version) != (WorkBoundInquiryState.SCHEMA, WorkBoundInquiryState.VERSION):
            raise ValueError("reference cost census changes its actual work-bound source state")
        require_sorted_unique_strings(self.expected_attempt_ids, field_name="expected_attempt_ids")
        if type(self.groups) is not tuple:
            raise ValueError("reference cost census must retain all method and unknown-work groups")
        for row in self.groups:
            exact(row, ReferenceWorkCost)
        methods = tuple("" if row.method is None else row.method.object_id for row in self.groups)
        if methods != tuple(sorted(set(methods))):
            raise ValueError("reference cost census duplicates or reorders method groups")
        if tuple(sorted(row.attempt_id for group in self.groups for row in group.attempts)) != self.expected_attempt_ids:
            raise ValueError("reference cost census drops or duplicates an original attempt")
        exact(self.total, InquiryCost)
        if self.total != _cost(tuple(row for group in self.groups for row in group.events)):
            raise ValueError("reference total changes unknown or complete campaign expense")
        if self.interpretation != "COMPLETE_RETAINED_OPERATION_COSTS_NOT_A_MOLECULAR_SUPPLIER_PROFILE":
            raise ValueError("analysis-task expense cannot establish expensive molecular work avoided")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.census_id, self)


def profile_reference_costs(state, *, census_id):
    """Group every actual attempt by its shared work identity; launch nothing."""
    exact(state, WorkBoundInquiryState)
    if state.information_cutoff.phase is not CausalPhase.POST_OUTCOME:
        raise ValueError("retained reference expense requires its post-outcome information cutoff")
    grouped = {}
    by_attempt = {row.attempt_id: row for row in state.operational_census}
    by_event = {row.attempt_id: row for row in state.cost_events}
    for binding in state.attempt_work_bindings:
        method = None if binding.work is None else binding.work.method
        grouped.setdefault(method, []).append(binding.attempt_id)
    groups = tuple(ReferenceWorkCost(method, tuple(by_attempt[key] for key in keys),
        tuple(sorted((by_event[key] for key in keys), key=lambda row: row.event_id)),
        _cost(tuple(by_event[key] for key in keys)))
        for method, keys in sorted(grouped.items(), key=lambda row: "" if row[0] is None else row[0].object_id))
    return ReferenceCostCensus(census_id, ObjectIdentity.from_record(state.state_id, state),
        tuple(by_attempt), groups, _cost(state.cost_events))


@dataclass(frozen=True, slots=True)
class ReferencePointFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-point-finding"
    scenario_id: str
    point_id: str
    arm: str
    numerical: FourStateAssessment
    identifiability: EndpointIdentifiability | None

    def __post_init__(self):
        validate_stable_id(self.scenario_id)
        validate_stable_id(self.point_id)
        if self.arm not in {"wild_type", "mutant"}:
            raise ValueError("reference analysis loses a paired endpoint")
        exact(self.numerical, FourStateAssessment)
        if (self.numerical.disposition is A.SATISFIED) != (self.identifiability is not None):
            raise ValueError("reference analysis cannot drop usable or invent failed rank evidence")
        if self.identifiability is not None:
            exact(self.identifiability, EndpointIdentifiability)
            if (self.identifiability.retained_result != self.numerical.result
                    or self.identifiability.observed_endpoints != ("kcat_c", "specificity")
                    or self.identifiability.free_parameters != PARAMETER_ORDER):
                raise ValueError("reference rank analysis substitutes another retained rate realization")


@dataclass(frozen=True, slots=True)
class ReferenceSensitivity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-sensitivity"
    parameter: str
    maximum_absolute_derivatives: tuple[Exact, Exact] | None
    maximum_absolute_elasticities: tuple[Exact, Exact] | None
    zero_rate_endpoint_count: int | None
    interpretation: str = "LOCAL_FINITE_POINT_DIAGNOSTIC_NOT_A_GLOBAL_OR_PAIRED_ERROR_BOUND"

    def __post_init__(self):
        if self.parameter not in PARAMETER_ORDER:
            raise ValueError("reference sensitivity changes a kinetic parameter")
        if (self.maximum_absolute_derivatives is None) != (self.maximum_absolute_elasticities is None):
            raise ValueError("reference sensitivity cannot drop zero-rate derivative meaning")
        for values in (self.maximum_absolute_derivatives, self.maximum_absolute_elasticities):
            if values is not None:
                if type(values) is not tuple or len(values) != 2:
                    raise ValueError("reference sensitivity must retain both target endpoints")
                for value in values:
                    exact(value, Exact)
                    if value.fraction < 0:
                        raise ValueError("maximum absolute sensitivity cannot be negative")
        if self.maximum_absolute_derivatives is None:
            if self.zero_rate_endpoint_count is not None:
                raise ValueError("unusable reference cannot invent an evaluated zero-rate census")
        elif type(self.zero_rate_endpoint_count) is not int or self.zero_rate_endpoint_count < 0:
            raise ValueError("reference sensitivity drops its exact zero-rate denominator")
        if self.interpretation != "LOCAL_FINITE_POINT_DIAGNOSTIC_NOT_A_GLOBAL_OR_PAIRED_ERROR_BOUND":
            raise ValueError("local sensitivity cannot become a finite-mutation or independent-uncertainty bound")


def _reference_requirements(assessment_id, supply, checked, suppliers, points):
    required = {*supply.prerequisite_requirement_ids, *supply.context.chemistry.unresolved_requirement_ids,
        "requirement." + assessment_id + ".justified-reduction-target",
        "requirement." + assessment_id + ".actual-molecular-supplier-costs",
        "requirement." + assessment_id + ".closure-and-lumping-applicability",
        "requirement." + assessment_id + ".biological-reference-validity"}
    for row in suppliers:
        required.update(row.unresolved_requirement_ids)
    for scenario in supply.scenarios:
        required.update(scenario.unresolved_requirement_ids)
        if scenario.original_state != "AVAILABLE" or not scenario.points:
            required.add("requirement." + assessment_id + "." + scenario.scenario_id + ".reference-supply")
    if checked.disposition is not A.SATISFIED:
        required.add("requirement." + assessment_id + ".correct-retained-reference-arithmetic")
    if any(row.identifiability is not None and row.identifiability.local_unconstrained_nullity for row in points):
        required.add("requirement." + assessment_id + ".microscopic-rate-identification-or-supported-set")
    return tuple(sorted(required))


@dataclass(frozen=True, slots=True)
class ReferenceKineticAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/reference-kinetic-assessment"
    assessment_id: str
    supply: PairedRateSupply
    retained_prediction: ObjectIdentity
    independent_prediction_assessment: PairedPredictionAssessment
    supplier_censuses: tuple[RateSupplierCensus, ...]
    point_findings: tuple[ReferencePointFinding, ...]
    sensitivities: tuple[ReferenceSensitivity, ...]
    mechanism_findings: tuple[tuple[str, str], ...]
    unresolved_requirement_ids: tuple[str, ...]
    biological_reference_validity: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.supply, PairedRateSupply)
        exact(self.retained_prediction, ObjectIdentity)
        exact(self.independent_prediction_assessment, PairedPredictionAssessment)
        checked = self.independent_prediction_assessment
        if (checked.supply, checked.prediction) != (self.supply.identity, self.retained_prediction):
            raise ValueError("reference assessment changes its actual supplied/retained operands")
        if (type(self.supplier_censuses) is not tuple or len(self.supplier_censuses) != len(self.supply.scenarios)
                or tuple(row.ledger for row in self.supplier_censuses) != tuple(row.ledger for row in self.supply.scenarios)):
            raise ValueError("reference assessment loses a scenario's full supplier census")
        for row in self.supplier_censuses:
            exact(row, RateSupplierCensus)
            if row.context != self.supply.context:
                raise ValueError("reference supplier changes the selected assay context")
        if type(self.point_findings) is not tuple or tuple(row.numerical for row in self.point_findings) != checked.kinetic_assessments:
            raise ValueError("reference assessment drops a retained failed or paired numerical result")
        for row in self.point_findings:
            exact(row, ReferencePointFinding)
        expected_keys = tuple((row.scenario_id, point.point_id, arm) for row in self.supply.scenarios
            for point in row.points for arm in ("wild_type", "mutant"))
        if checked.disposition is A.SATISFIED and tuple((row.scenario_id, row.point_id, row.arm)
                for row in self.point_findings) != expected_keys:
            raise ValueError("reference analysis changes a retained point's exact scenario or endpoint")
        if type(self.sensitivities) is not tuple or tuple(row.parameter for row in self.sensitivities) != PARAMETER_ORDER:
            raise ValueError("reference assessment drops a consequential rate sensitivity")
        for row in self.sensitivities:
            exact(row, ReferenceSensitivity)
        if self.sensitivities != _reference_sensitivities(self.supply, checked, self.point_findings):
            raise ValueError("reference sensitivity differs from independent rank matrices and original rate scope")
        if (self.mechanism_findings != _mechanism_findings(self.supply)
                or self.unresolved_requirement_ids != _reference_requirements(self.assessment_id, self.supply,
                    checked, self.supplier_censuses, self.point_findings)):
            raise ValueError("reference assessment changes mechanism scope or remaining scientific requirements")
        if self.biological_reference_validity is not A.UNEVALUABLE or type(self.new_native_calls) is not int or self.new_native_calls != 0:
            raise ValueError("retained reference analysis cannot admit biology or enter native acquisition")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def _mechanism_findings(supply):
    rows = []
    for scenario in supply.scenarios:
        changed = {name for point in scenario.points for name in PARAMETER_ORDER
                   if getattr(point.wild_type, name) != getattr(point.mutant, name)}
        meaning = ("UNRESOLVED_REFERENCE" if scenario.original_state != "AVAILABLE" or not scenario.points else
                   "NO_FINITE_RATE_EFFECT" if not changed else
                   "GATING_ONLY_SPECIFICITY_INVARIANT_BY_CONSTRUCTION" if changed.issubset({"a", "b"}) else
                   "BRANCH_DISCRIMINATION_OR_COMMITMENT_DEPENDENCE_PRESENT")
        rows.append((scenario.scenario_id, meaning))
    return tuple(rows)


def _reference_sensitivities(supply, checked, points):
    if checked.disposition is not A.SATISFIED or not points:
        return tuple(ReferenceSensitivity(parameter, None, None, None) for parameter in PARAMETER_ORDER)
    rates = tuple(getattr(point, arm) for scenario in supply.scenarios for point in scenario.points
                  for arm in ("wild_type", "mutant"))
    # Independent target formulas, paired with the already assessed exact
    # derivative matrices. Zero-rate derivatives survive without log(0).
    endpoints = []
    for row in rates:
        q = row.fractions
        endpoints.append((q["a"] * q["r_c"] / (q["a"] + q["r_c"]),
            q["c"] * q["r_c"] * (q["d_o"] + q["r_o"]) / (q["o"] * q["r_o"] * (q["d_c"] + q["r_c"]))))
    return tuple(ReferenceSensitivity(parameter,
        tuple(Exact.of(max(abs(point.identifiability.jacobian[e][p].fraction) for point in points)) for e in range(2)),
        tuple(Exact.of(max(abs(point.identifiability.jacobian[e][p].fraction * rate.fractions[parameter] / endpoint[e])
            for point, rate, endpoint in zip(points, rates, endpoints, strict=True))) for e in range(2)),
        sum(getattr(rate, parameter) == 0 for rate in rates)) for p, parameter in enumerate(PARAMETER_ORDER))


def assess_reference_supply(supply, prediction, decision, *, assessment_id, supplier_semantics=()):
    """Preserve finite joint support; never fit rates, replay producers or rank costs by convenience."""
    exact(supply, PairedRateSupply)
    exact(prediction, PairedPrediction)
    exact(decision, PairedDecisionRegion)
    if type(supplier_semantics) is not tuple:
        raise ValueError("reference supplier inputs must retain the complete selected immutable tuple")
    by_ledger = {}
    allowed = {row.ledger.identity for row in supply.scenarios}
    for row in supplier_semantics:
        if row.ledger not in allowed:
            raise ValueError("reference supplier semantics belong to another original ledger")
        by_ledger.setdefault(row.ledger, []).append(row)
    suppliers = tuple(assess_rate_suppliers(row.ledger, supply.context,
        tuple(by_ledger.get(row.ledger.identity, ())), census_id=assessment_id + "." + row.scenario_id + ".suppliers")
        for row in supply.scenarios)
    checked = assess_paired_prediction(supply, prediction, decision, assessment_id=assessment_id + ".prediction")
    points = []
    originals = tuple((point.scenario_id, point.point_id, arm, getattr(point, arm))
        for point in prediction.points for arm in ("wild_type", "mutant"))
    for (scenario, point, arm, result), numerical in zip(originals, checked.kinetic_assessments, strict=True):
        identified = None if numerical.disposition is not A.SATISFIED else assess_endpoint_identifiability(
            result, analysis_id=assessment_id + "." + scenario + "." + point + "." + arm + ".rank")
        points.append(ReferencePointFinding(scenario, point, arm, numerical, identified))
    points = tuple(points)
    return ReferenceKineticAssessment(assessment_id, supply, ObjectIdentity.from_record(prediction.prediction_id, prediction),
        checked, suppliers, points, _reference_sensitivities(supply, checked, points), _mechanism_findings(supply),
        _reference_requirements(assessment_id, supply, checked, suppliers, points))
