# SPDX-License-Identifier: MPL-2.0
"""Later Matrix selections reference original sources and frozen products.

These records convey no source eligibility, reservation chronology, independent
sampling, scientific admission or authority. Actual publications retain those
separate obligations. No recipe, margin or random seed is chosen here.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY, validate_declared_primary_family
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledForecastSeal, ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledReservation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id


PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")
PROTOCOL_ID = "matrix.later-programme.saved-assessment"
STANDING = "CONDITIONAL_CALCULATION_NOT_SCIENTIFIC_QUALIFICATION"
PACKAGE_ROLES = ("bridge", "calibration", "comparator", "comparator-calibration", "criterion", "model", "numerical-scope", "preprocessing", "support-rule")


def identity(record):
    for field in ("specification_id", "package_id", "roster_id", "case_id", "bank_id", "result_id", "record_id"):
        if hasattr(record, field):
            return ObjectIdentity.from_record(getattr(record, field), record)
    raise ValueError("later Matrix record lacks its owning identity")


def references(rows, field):
    if (type(rows) is not tuple or any(type(row) is not ObjectIdentity for row in rows)
            or tuple(row.object_id for row in rows) != tuple(sorted({row.object_id for row in rows}))):
        raise ValueError(field + " requires unique exact original record references")
    for row in rows:
        row.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixFrozenConsumerPackage(CanonicalRecord):
    """Exact unchanged payload and complete upstream whole-group use censuses.

    training_unit_ids covers all coefficient fits, including comparators;
    selection_unit_ids covers every other known upstream use, including
    calibration, numerical development and model/recipe selection. A producer
    must supply those original censuses. References grant no warrant that an
    unreported use or an exposure audit is complete.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/frozen-consumer-package"
    package_id: str
    upstream_freeze: ObjectIdentity
    components: tuple[tuple[str, ObjectIdentity], ...]
    reservation: ObjectIdentity
    training_unit_ids: tuple[str, ...]
    selection_unit_ids: tuple[str, ...]
    handoff_scope: str

    def __post_init__(self):
        validate_stable_id(self.package_id)
        if (type(self.components) is not tuple or tuple(name for name, _ in self.components) != PACKAGE_ROLES
                or any(type(value) is not ObjectIdentity for _, value in self.components)
                or type(self.upstream_freeze) is not ObjectIdentity or type(self.reservation) is not ObjectIdentity
                or self.reservation.object_schema != ScheduledReservation.SCHEMA
                or self.handoff_scope != "OBSERVATION_ASSISTED_SEALED_BEFORE_FUTURE"):
            raise ValueError("frozen consumer loses its complete unchanged payload, reservation or handoff scope")
        for rows in (self.training_unit_ids, self.selection_unit_ids):
            if type(rows) is not tuple or rows != tuple(sorted(set(rows))):
                raise ValueError("frozen consumer requires exact upstream whole-unit censuses")
            for value in rows:
                validate_stable_id(value)
        if not self.training_unit_ids:
            raise ValueError("frozen consumer omits its original training population")
        for value in (self.upstream_freeze, self.reservation, *(value for _, value in self.components)):
            value.__post_init__()

    @property
    def identity(self):
        return identity(self)

    def component(self, role):
        return dict(self.components)[role]


@dataclass(frozen=True, slots=True)
class MatrixFunctionalCriterion(CanonicalRecord):
    """Explicit response endpoint and inference; no external task is implied."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/functional-criterion"
    VERSION: ClassVar[str] = "2.0.0"
    predictor: str
    horizon_tick: int
    normalized_error_maximum: Decimal
    paired_view_discrepancy_maximum: Decimal
    minimum_usable_groups: int
    minimum_admitted_groups: int
    maximum_false_admissions: int
    null_success_numerator: int
    null_success_denominator: int
    alpha_numerator: int
    alpha_denominator: int
    family_slots: tuple[str, ...]
    sampling_assumptions: tuple[ObjectIdentity, ...]
    effort_unit: str
    familywise_alpha_numerator: int
    familywise_alpha_denominator: int
    multiplicity_rule: str
    procedure: str
    missing_policy: str = "RETAIN_ALL_ASSIGNED_GROUPS_AS_NONSUCCESS"

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS

        if (self.predictor not in PREDICTORS or self.horizon_tick not in (16, 64, 128)
                or type(self.horizon_tick) is not int):
            raise ValueError("functional criterion changes its endpoint, complete primary family or missing denominator")
        validate_declared_primary_family(self.family_slots, required=AMENDED_PRIMARY_FAMILY if self.is_matched else FAMILY_IDS)
        for name in ("normalized_error_maximum", "paired_view_discrepancy_maximum"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ("minimum_usable_groups", "minimum_admitted_groups", "maximum_false_admissions"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("functional criterion needs explicit exact whole-group thresholds")
        if not self.is_matched and (self.minimum_usable_groups < 1 or self.minimum_admitted_groups < 1):
            raise ValueError("universal refusal cannot satisfy useful functional coverage")
        for n, d in ((self.null_success_numerator, self.null_success_denominator), (self.alpha_numerator, self.alpha_denominator)):
            if type(n) is not int or type(d) is not int or not 0 < n < d:
                raise ValueError("functional criterion requires explicit exact probability operands")
        n, d = self.familywise_alpha_numerator, self.familywise_alpha_denominator
        if (type(n) is not int or type(d) is not int or not 0 < n < d
                or self.multiplicity_rule != "BONFERRONI_FIXED_FULL_PRIMARY_FAMILY"
                or self.alpha > Fraction(n, d) / len(self.family_slots)):
            raise ValueError("functional criterion drops or reallocates the full declared testing family")
        if self.is_matched:
            if (self.predictor != "FACTOR" or self.horizon_tick != 64
                    or self.normalized_error_maximum != Decimal(".01")
                    or self.paired_view_discrepancy_maximum != Decimal(".0001")
                    or (self.minimum_usable_groups, self.minimum_admitted_groups, self.maximum_false_admissions) != (0, 0, 0)
                    or self.family_slots != AMENDED_PRIMARY_FAMILY or self.alpha != Fraction(1, 160)
                    or Fraction(n, d) != Fraction(1, 20) or self.null_probability != Fraction(1, 2)
                    or self.missing_policy != "ALL_ASSIGNED_PAIRED_WORST_CASE_AND_TRANSFER_NONSUCCESS"):
                raise ValueError("matched adequacy changes the frozen64 epsilon.01 endpoint, eight tests or complete paired denominator")
        elif (self.procedure != "EXACT_BINOMIAL_ALL_ASSIGNED_GROUPS"
                or self.missing_policy != "RETAIN_ALL_ASSIGNED_GROUPS_AS_NONSUCCESS"):
            raise ValueError("functional criterion changes its declared inference or missing denominator")
        references(self.sampling_assumptions, "sampling assumptions")
        validate_stable_id(self.effort_unit)

    @property
    def is_matched(self):
        return self.procedure == "EXACT_PAIRED_E5_AND_ASSIGNED_DURATION_WIN_E6" or self.is_curve_primary

    @property
    def is_curve_primary(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_TRANSFER_PROCEDURE
        return self.procedure == CURVE_TRANSFER_PROCEDURE

    @property
    def alpha(self):
        return Fraction(self.alpha_numerator, self.alpha_denominator)

    @property
    def null_probability(self):
        return Fraction(self.null_success_numerator, self.null_success_denominator)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCase(CanonicalRecord):
    """Original source coordinates with explicit matched-start and cost evidence."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/case"
    case_id: str
    arm_id: str
    recipe: ObjectIdentity
    public_source: ScheduledPublicSource
    initial_state: ArtifactIdentity
    preparation_duration: Decimal
    preparation_effort: Decimal | None
    restored_context: ObjectIdentity
    assay: ObjectIdentity
    native_assessments: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.case_id)
        validate_stable_id(self.arm_id)
        if (type(self.public_source) is not ScheduledPublicSource or type(self.initial_state) is not ArtifactIdentity
                or any(type(value) is not ObjectIdentity for value in (self.recipe, self.restored_context, self.assay))):
            raise TypeError("programme case requires exact original source, recipe, state, restored context and assay")
        self.public_source.__post_init__()
        self.initial_state.__post_init__()
        validate_decimal(self.preparation_duration, field_name="actual preparation duration", minimum=Decimal(0))
        if self.preparation_effort is not None:
            validate_decimal(self.preparation_effort, field_name="declared effort integral", minimum=Decimal(0))
        references(self.native_assessments, "independent native assessments")

    @property
    def unit_id(self):
        return self.public_source.root.independent_group_id


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRoster(CanonicalRecord):
    """Allocation owners occur once; cases contain no repeated population."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/roster"
    roster_id: str
    phase: str
    allocations: tuple[ScheduledAllocation, ...]
    reservation: ScheduledReservation
    cases: tuple[MatrixProgrammeCase, ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity

        validate_stable_id(self.roster_id)
        if (self.phase not in PHASES or type(self.reservation) is not ScheduledReservation
                or type(self.allocations) is not tuple or not self.allocations
                or any(type(row) is not ScheduledAllocation for row in self.allocations)
                or tuple(row.allocation_id for row in self.allocations) != tuple(sorted({row.allocation_id for row in self.allocations}))
                or type(self.cases) is not tuple or not self.cases or any(type(row) is not MatrixProgrammeCase for row in self.cases)
                or tuple(row.case_id for row in self.cases) != tuple(sorted({row.case_id for row in self.cases}))):
            raise ValueError("later programme requires its complete original allocation/case roster")
        self.reservation.__post_init__()
        allocations = {original_identity(row): row for row in self.allocations}
        for row in self.allocations:
            row.__post_init__()
        cells = set()
        for case in self.cases:
            case.__post_init__()
            public = case.public_source
            source_allocation = allocations.get(public.allocation)
            if source_allocation is None or public.reservation != original_identity(self.reservation):
                raise ValueError("programme case substitutes original allocation or pre-fit reservation")
            actual = tuple(row for row in source_allocation.roots if row.root.root_id == public.root.root_id)
            if (len(actual) != 1 or actual[0].root != public.root
                    or public.coordinate not in source_allocation.coordinates or actual[0].coordinate !=
                        ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate)):
                raise ValueError("programme case changes original root/coordinate/clock membership")
            key = case.unit_id, case.arm_id
            if key in cells:
                raise ValueError("programme roster duplicates an independent-group/arm cell")
            cells.add(key)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/observation"
    case_id: str
    forecast: ScheduledForecastSeal | None
    score: ScheduledResponseScore | None
    source_support: str
    supplier_assessments: tuple[ObjectIdentity, ...]
    comparator_forecast: ScheduledForecastSeal | None = None

    def __post_init__(self):
        validate_stable_id(self.case_id)
        if (self.forecast is not None and type(self.forecast) is not ScheduledForecastSeal
                or self.score is not None and type(self.score) is not ScheduledResponseScore
                or self.source_support not in ("SUPPORTED", "UNSUPPORTED", "UNESTABLISHED")):
            raise ValueError("programme observation changes original products or declared source support")
        if self.forecast is not None:
            self.forecast.__post_init__()
        if self.score is not None:
            self.score.__post_init__()
        if self.comparator_forecast is not None:
            if type(self.comparator_forecast) is not ScheduledForecastSeal:
                raise TypeError("same-information comparator requires its actual original forecast seal")
            self.comparator_forecast.__post_init__()
        references(self.supplier_assessments, "original supplier assessments")


@dataclass(frozen=True, slots=True)
class MatrixProgrammeEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/evidence"
    bank_id: str
    roster: ObjectIdentity
    package: ObjectIdentity
    rows: tuple[MatrixProgrammeObservation, ...]

    def __post_init__(self):
        validate_stable_id(self.bank_id)
        if (type(self.roster) is not ObjectIdentity or self.roster.object_schema != MatrixProgrammeRoster.SCHEMA
                or type(self.package) is not ObjectIdentity or self.package.object_schema != MatrixFrozenConsumerPackage.SCHEMA
                or type(self.rows) is not tuple or any(type(row) is not MatrixProgrammeObservation for row in self.rows)
                or tuple(row.case_id for row in self.rows) != tuple(sorted({row.case_id for row in self.rows}))):
            raise ValueError("programme evidence aliases original source/product rows")
        for row in self.rows:
            row.__post_init__()

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixLaterExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/specification"
    specification_id: str
    phase: str
    roster: ObjectIdentity
    package: ObjectIdentity
    evidence: ObjectIdentity
    campaign: ObjectIdentity
    criterion: MatrixFunctionalCriterion
    expected_groups: int
    arm_ids: tuple[str, ...]
    hold_arm_id: str
    nomination: ObjectIdentity | None
    minimum_recoverable_groups: int
    tie_policy: str
    transfer_regime_ids: tuple[str, ...]
    transfer_domain_claims: tuple[str, ...]
    mode: str
    future_noise_policy: str

    def __post_init__(self):
        from empirical_lawhood.planning.campaigns import CampaignSpec

        validate_stable_id(self.specification_id)
        for value, kind in ((self.roster, MatrixProgrammeRoster), (self.package, MatrixFrozenConsumerPackage),
                (self.evidence, MatrixProgrammeEvidence), (self.campaign, CampaignSpec)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("later specification changes an exact original record type/revision")
        if (self.phase not in PHASES or type(self.criterion) is not MatrixFunctionalCriterion
                or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.arm_ids) is not tuple or self.arm_ids != tuple(sorted(set(self.arm_ids))) or not self.arm_ids
                or self.hold_arm_id not in self.arm_ids or type(self.minimum_recoverable_groups) is not int
                or self.minimum_recoverable_groups < 1 or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")
                or self.mode not in ("RETAINED_CONDITIONAL_ASSESSMENT", "ACQUIRE_AND_ASSESS")
                or type(self.transfer_regime_ids) is not tuple or type(self.transfer_domain_claims) is not tuple
                or self.future_noise_policy != "COMMON_COUNTERFACTUAL_MENU_AND_PURPOSE_STREAMS"):
            raise ValueError("later specification omits an explicit functional, population, selection or noise rule")
        self.criterion.__post_init__()
        for name in (*self.arm_ids, *self.transfer_regime_ids):
            validate_stable_id(name)
        if (self.phase != "E5_OPPORTUNITY" and (self.criterion.minimum_usable_groups > self.expected_groups
                or self.criterion.minimum_admitted_groups > self.expected_groups)):
            raise ValueError("functional coverage requirement exceeds its complete assigned census")
        if self.phase == "E5_OPPORTUNITY":
            if len(self.arm_ids) != 3 or self.nomination is not None or self.transfer_regime_ids or self.transfer_domain_claims:
                raise ValueError("E5 opportunity requires HOLD and two prespecified recipes before nomination")
        elif self.phase == "E5_CONFIRMATION":
            if len(self.arm_ids) != 2 or type(self.nomination) is not ObjectIdentity or self.transfer_regime_ids or self.transfer_domain_claims:
                raise ValueError("E5 confirmation requires the frozen original nomination and two matched arms")
            from .science import MatrixPreparationNomination
            if (self.nomination.object_schema != MatrixPreparationNomination.SCHEMA
                    or self.nomination.object_version != MatrixPreparationNomination.VERSION):
                raise ValueError("E5 confirmation substitutes its original recipe-nomination type/revision")
        elif (len(self.arm_ids) != 1 or self.nomination is not None or len(self.transfer_regime_ids) != 2
                or len(set(self.transfer_regime_ids)) != 2 or type(self.transfer_domain_claims) is not tuple
                or len(self.transfer_domain_claims) != 2 or any(value not in (
                    "INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") for value in self.transfer_domain_claims)):
            raise ValueError("E6 requires two distinct complete untouched regimes and one unchanged package")

    @property
    def identity(self):
        return identity(self)
