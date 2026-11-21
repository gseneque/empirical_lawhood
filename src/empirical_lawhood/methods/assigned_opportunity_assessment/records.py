# SPDX-License-Identifier: MPL-2.0
"""One original dependent source and complete finite assigned outcome records."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import NamedDecimal
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.science.models.time import AvailabilitySpec
from empirical_lawhood.design.inquiry_methods import DependentAssessmentContract, FrozenInquiryProcedure, InquiryAuthorContract, InquiryAuthoringMode, InquiryEvidenceRole, MissingOpportunityRule
from empirical_lawhood.design.study_authoring import CapabilitySelection


NAMESPACE = "assigned-opportunity"
PREFIX = "empirical-lawhood/" + NAMESPACE
MAX_BYTES = 512 * 1024
MAX_COUNT = 16
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE


def implementation(phase):
    return sha256((NAMESPACE + ".exact-finite-census." + phase + ".v1").encode()).hexdigest()


def method(phase):
    return CapabilitySelection(NAMESPACE + "." + phase, "1.0.0", implementation(phase))


def decimal(value):
    validate_decimal(value, field_name="finite_opportunity_value")
    if len(value.as_tuple().digits) > 64 or not -64 <= value.as_tuple().exponent <= 64:
        raise ValueError("opportunity values exceed the exact bounded decimal domain")


def identity(value):
    return ObjectIdentity.from_record(value.record_id, value)


@dataclass(frozen=True, slots=True)
class OpportunitySource(CanonicalRecord):
    """Disclosed fixture roster; all its opportunities share one original root."""

    SCHEMA: ClassVar[str] = PREFIX + "/source"
    record_id: str
    independent_unit_id: str
    clock_id: str
    opportunity_ids: tuple[str, ...]
    numerical_view_ids: tuple[str, ...]
    evidence_scope: str = "EXPOSED_DEPENDENT_SOFTWARE_FIXTURE"

    def __post_init__(self):
        for value in (self.record_id, self.independent_unit_id, self.clock_id):
            validate_stable_id(value)
        for name in ("opportunity_ids", "numerical_view_ids"):
            require_sorted_unique_strings(getattr(self, name), field_name=name, allow_empty=False)
        if (not 1 <= len(self.opportunity_ids) <= MAX_COUNT or len(self.numerical_view_ids) != 2
                or self.evidence_scope != "EXPOSED_DEPENDENT_SOFTWARE_FIXTURE"
                or self.independent_unit_id in (*self.opportunity_ids, *self.numerical_view_ids)
                or set(self.opportunity_ids) & set(self.numerical_view_ids)):
            raise ValueError("fixture source changes its dependent opportunity, view or exposure contract")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class OpportunityAuthorInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/author-input"
    record_id: str
    source: OpportunitySource
    requested_threshold: Decimal
    availability: AvailabilitySpec

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.source) is not OpportunitySource or type(self.availability) is not AvailabilitySpec:
            raise TypeError("author requires its exact original source and availability")
        self.source.__post_init__()
        self.availability.__post_init__()
        decimal(self.requested_threshold)
        if not 0 <= self.requested_threshold <= 1:
            raise ValueError("fixture threshold must remain within the unit outcome interval")
        if (self.availability.clock_id != self.source.clock_id
                or self.availability.outcome_access is not ACCESS or self.availability.available_at is None):
            raise ValueError("author input changes its exact exposed clock and availability")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class OpportunityOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcome"
    opportunity_id: str
    dependence_root: ObjectIdentity
    independent_unit_id: str
    availability: AvailabilitySpec
    status: str
    views: tuple[NamedDecimal, ...]

    def __post_init__(self):
        for value in (self.opportunity_id, self.independent_unit_id):
            validate_stable_id(value)
        if type(self.dependence_root) is not ObjectIdentity or type(self.availability) is not AvailabilitySpec:
            raise TypeError("outcome requires its original dependence root and availability")
        self.dependence_root.__post_init__()
        self.availability.__post_init__()
        if (self.status not in ("OBSERVED", "MISSING", "INTERRUPTED", "UNEVALUABLE")
                or type(self.views) is not tuple
                or self.availability.available_at is None or self.availability.outcome_access is not ACCESS):
            raise ValueError("outcome changes its status, exact values or evidence role")
        require_sorted_unique_ids(self.views, attribute="value_id", field_name="views")
        if (self.status == "OBSERVED" and len(self.views) != 2
                or self.status in ("MISSING", "INTERRUPTED") and self.views
                or len(self.views) > 2):
            raise ValueError("missing or interrupted opportunities cannot acquire invented observations")
        for view in self.views:
            if type(view) is not NamedDecimal or view.unit != "1":
                raise ValueError("fixture views require their original dimensionless units")
            decimal(view.value)


@dataclass(frozen=True, slots=True)
class OpportunityOutcomes(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcomes"
    record_id: str
    source: OpportunitySource
    rows: tuple[OpportunityOutcome, ...]
    availability: AvailabilitySpec

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.source) is not OpportunitySource or type(self.availability) is not AvailabilitySpec:
            raise TypeError("outcome table requires its original source and availability")
        self.source.__post_init__()
        self.availability.__post_init__()
        if (type(self.rows) is not tuple or any(type(r) is not OpportunityOutcome for r in self.rows)
                or tuple(r.opportunity_id for r in self.rows) != self.source.opportunity_ids):
            raise ValueError("outcome table must retain the complete assigned denominator")
        if (self.availability.clock_id != self.source.clock_id
                or self.availability.outcome_access is not ACCESS or self.availability.available_at is None):
            raise ValueError("outcomes change their original exposed clock or availability")
        for row in self.rows:
            row.__post_init__()
            if (row.dependence_root != self.source.identity or row.independent_unit_id != self.source.independent_unit_id
                    or row.availability.clock_id != self.source.clock_id
                    or not row.availability.phase.precedes_or_equals(self.availability.phase)
                    or row.availability.available_at > self.availability.available_at
                    or (row.views and tuple(v.value_id for v in row.views) != self.source.numerical_view_ids)):
                raise ValueError("outcome substitutes original dependence, nested views or availability")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class OpportunityConsumer(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/consumer"
    record_id: str
    source: ObjectIdentity
    predicate: str = "FINITE_ASSIGNED_MEAN_AT_LEAST_THRESHOLD"
    estimand: str = "EQUAL_WEIGHT_MEAN_OVER_ALL_ASSIGNED_OPPORTUNITIES"
    outcome_lower: Decimal = Decimal(0)
    outcome_upper: Decimal = Decimal(1)

    def __post_init__(self):
        validate_stable_id(self.record_id)
        decimal(self.outcome_lower)
        decimal(self.outcome_upper)
        if (type(self.source) is not ObjectIdentity or self.source.object_schema != OpportunitySource.SCHEMA
                or self.source.object_version != OpportunitySource.VERSION
                or self.predicate != "FINITE_ASSIGNED_MEAN_AT_LEAST_THRESHOLD"
                or self.estimand != "EQUAL_WEIGHT_MEAN_OVER_ALL_ASSIGNED_OPPORTUNITIES"
                or (self.outcome_lower, self.outcome_upper) != (Decimal(0), Decimal(1))):
            raise ValueError("consumer changes its exact finite estimand, original source or outcome bounds")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class OpportunityOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    phase: str
    source: OpportunitySource
    consumer: OpportunityConsumer
    author: InquiryAuthorContract
    parameters: tuple[NamedDecimal, ...]
    assessment: DependentAssessmentContract | None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.phase not in ("author", "assess") or self.config_id != "config." + NAMESPACE + "." + self.phase:
            raise ValueError("opportunity operation requires its original code-owned phase")
        for value, kind in ((self.source, OpportunitySource), (self.consumer, OpportunityConsumer),
                            (self.author, InquiryAuthorContract)):
            if type(value) is not kind:
                raise TypeError("operation substitutes exact scientific operands")
            value.__post_init__()
        self.author.frozen_consumer.require_parameters(self.parameters)
        for parameter in self.parameters:
            decimal(parameter.value)
        if (self.consumer.source != self.source.identity or self.author.mode is not InquiryAuthoringMode.INVESTIGATOR_RECIPE
                or self.author.author != method("author") or self.author.permitted_methods != (method("assess"),)
                or self.author.method_family_id != NAMESPACE + ".finite-assigned-enclosure"
                or self.author.maximum_composed_operations != 1
                or self.author.output_specification != self.consumer.identity
                or self.author.frozen_consumer.consumer != self.consumer.identity
                or tuple(p.value_id for p in self.parameters) != ("threshold",)
                or len(self.author.inputs) != 1
                or self.author.inputs[0].record.object_schema != OpportunityAuthorInput.SCHEMA
                or self.author.inputs[0].record.object_version != OpportunityAuthorInput.VERSION
                or self.author.inputs[0].role is not InquiryEvidenceRole.ACTOR_INPUT
                or self.author.cutoff.clock_id != self.source.clock_id):
            raise ValueError("extension refuses unsupported author mode, method, consumer or actor evidence")
        from empirical_lawhood.methods.assigned_opportunity_assessment.design import validate_author_contract
        validate_author_contract(self)
        if self.phase == "author":
            if self.assessment is not None:
                raise ValueError("author operation cannot receive evaluator evidence or diagnostics")
        else:
            if type(self.assessment) is not DependentAssessmentContract:
                raise TypeError("assessor requires its exact dependent assessment contract")
            self.assessment.__post_init__()
            from empirical_lawhood.methods.assigned_opportunity_assessment.design import validate_assessment_contract
            validate_assessment_contract(self)

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")


def finite_enclosure(contract, rows):
    """Sharp finite-census bounds; no independence or probability assertion."""
    lower, upper = Fraction(contract.outcome_bound.lower), Fraction(contract.outcome_bound.upper)
    observed, missing, interrupted, invalid = [], [], [], []
    for row in rows:
        if row.status == "INTERRUPTED":
            interrupted.append(row.opportunity_id)
        elif row.status == "MISSING":
            missing.append(row.opportunity_id)
        elif (row.status == "UNEVALUABLE" or len({v.value for v in row.views}) != 1
                or any(not lower <= Fraction(v.value) <= upper for v in row.views)):
            invalid.append(row.opportunity_id)
        else:
            observed.append(Fraction(row.views[0].value))
    unresolved = len(rows) - len(observed)
    lo = (sum(observed, Fraction(0)) + unresolved * lower) / len(rows)
    hi = (sum(observed, Fraction(0)) + unresolved * upper) / len(rows)
    return lo, hi, tuple(missing), tuple(interrupted), tuple(invalid)


@dataclass(frozen=True, slots=True)
class OpportunityAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/assessment"
    record_id: str
    config: OpportunityOperationConfig
    procedure: FrozenInquiryProcedure
    outcomes: OpportunityOutcomes
    lower_ratio: tuple[int, int]
    upper_ratio: tuple[int, int]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.config) is not OpportunityOperationConfig or self.config.phase != "assess":
            raise ValueError("assessment changes its actual producing configuration")
        self.config.__post_init__()
        if self.record_id != self.config.node_id + ".product":
            raise ValueError("assessment changes its producing operation identity")
        validate_assessment_inputs(self.config, self.procedure, self.outcomes)
        lo, hi, *_ = finite_enclosure(self.config.assessment, self.outcomes.rows)
        if (self.lower_ratio, self.upper_ratio) != ((lo.numerator, lo.denominator), (hi.numerator, hi.denominator)):
            raise ValueError("assessment substitutes exact independent finite-census arithmetic")
        if any(type(value) is not int for ratio in (self.lower_ratio, self.upper_ratio) for value in ratio):
            raise TypeError("assessment ratios require exact reduced integer fractions")

    @property
    def identity(self):
        return identity(self)

    @property
    def reason_codes(self):
        _, _, missing, interrupted, invalid = finite_enclosure(self.config.assessment, self.outcomes.rows)
        reasons = []
        if missing:
            reasons.append("MISSING_OPPORTUNITIES_RETAINED")
        if interrupted:
            reasons.append("INTERRUPTED_OPPORTUNITIES_RETAINED")
        if invalid:
            reasons.append("UNEVALUABLE_OPPORTUNITIES_RETAINED")
        if self.disposition == "UNEVALUABLE" and not invalid:
            reasons.append("INSUFFICIENT_FOR_FROZEN_PREDICATE")
        if self.disposition == "FALSIFIED":
            reasons.append("UPPER_BOUND_BELOW_FROZEN_THRESHOLD")
        return tuple(sorted(reasons))

    @property
    def disposition(self):
        _, _, missing, interrupted, invalid = finite_enclosure(self.config.assessment, self.outcomes.rows)
        if invalid or (self.config.assessment.missingness is MissingOpportunityRule.UNEVALUABLE and (missing or interrupted)):
            return "UNEVALUABLE"
        threshold = Fraction(self.procedure.parameters[0].value)
        if Fraction(*self.lower_ratio) >= threshold:
            return "SATISFIED"
        if Fraction(*self.upper_ratio) < threshold:
            return "FALSIFIED"
        return "UNEVALUABLE"


def validate_assessment_inputs(config, procedure, outcomes):
    from empirical_lawhood.methods.assigned_opportunity_assessment.science import frozen_procedure

    if type(procedure) is not FrozenInquiryProcedure or type(outcomes) is not OpportunityOutcomes:
        raise TypeError("assessment requires the frozen procedure and evaluator-only outcome table")
    procedure.__post_init__()
    outcomes.__post_init__()
    config.assessment.require_procedure(procedure)
    if (procedure != frozen_procedure(config) or outcomes.source != config.source
            or len(config.assessment.inputs) != 1 or config.assessment.inputs[0].record != outcomes.identity
            or config.assessment.inputs[0].availability != outcomes.availability):
        raise ValueError("assessment changes original procedure, parameters, complete source or outcome evidence")
