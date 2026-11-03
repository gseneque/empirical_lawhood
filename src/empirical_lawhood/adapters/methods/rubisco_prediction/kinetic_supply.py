# SPDX-License-Identifier: MPL-2.0
"""Typed joint kinetic supplies for LOOP W1, separate from frozen predictors.

A finite supported set is not a probability distribution. A partial apparent
kinetic family remains unidentified; no KO, covariance or missing outcome is
filled from a default. These first supplies have a conditional evidence ceiling.
Biological calibration and final nomination require later assessed suppliers.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_nonempty, validate_stable_id,
)

CONSTANT_ORDER = ("kcat_c_s_inv", "kc_um", "kcat_o_s_inv", "ko_um")
OUTCOMES = ("AVAILABLE", "FALSIFIED", "UNEVALUABLE", "NOT_ENTERED", "UNKNOWN")
ROLES = ("DISCLOSED_SYNTHETIC", "HISTORICAL_SOURCE_CONDITIONED", "CONDITIONAL_MODEL")
CONTEXT = Context(prec=50)


def _positive(value: Decimal) -> None:
    validate_decimal(value, field_name="kinetic_quantity")
    if value <= 0:
        raise ValueError("kinetic quantities must be strictly positive")


def _identities(values: tuple[ObjectIdentity, ...]) -> None:
    if (type(values) is not tuple or not values
            or any(type(item) is not ObjectIdentity for item in values)
            or len({item.object_id for item in values}) != len(values)):
        raise ValueError("kinetic supply needs distinct exact source identities")


@dataclass(frozen=True, slots=True)
class KineticSupportInterval(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/support-interval"
    lower: Decimal | None
    upper: Decimal | None

    def __post_init__(self):
        for value in (self.lower, self.upper):
            if value is not None:
                validate_decimal(value, field_name="support_bound", minimum=Decimal(0))
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError("kinetic support bounds are reversed")

    def contains(self, value: Decimal) -> bool:
        _positive(value)
        return ((self.lower is None or value >= self.lower)
                and (self.upper is None or value <= self.upper))


@dataclass(frozen=True, slots=True)
class ApparentKineticConstants(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/apparent-constants"
    kcat_c_s_inv: Decimal
    kc_um: Decimal
    kcat_o_s_inv: Decimal
    ko_um: Decimal

    def __post_init__(self):
        for name in CONSTANT_ORDER:
            _positive(getattr(self, name))

    @property
    def specificity(self) -> Decimal:
        with localcontext(CONTEXT):
            return self.kcat_c_s_inv * self.ko_um / (self.kc_um * self.kcat_o_s_inv)


@dataclass(frozen=True, slots=True)
class KineticSupplyContext(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/context"
    context_id: str
    material: ObjectIdentity
    assay_conditions: ObjectIdentity
    temperature_k: Decimal
    interpretation: str = "APPARENT_CONSTANTS_ACTIVATED_SATURATING_RUBP_STATIONARY_CLAMPED_DISSOLVED_GASES"

    def __post_init__(self):
        validate_stable_id(self.context_id)
        if type(self.material) is not ObjectIdentity or type(self.assay_conditions) is not ObjectIdentity:
            raise ValueError("kinetic context requires exact material and assay identities")
        _positive(self.temperature_k)
        if self.interpretation != "APPARENT_CONSTANTS_ACTIVATED_SATURATING_RUBP_STATIONARY_CLAMPED_DISSOLVED_GASES":
            raise ValueError("kinetic context changes its apparent-rate interpretation")


@dataclass(frozen=True, slots=True)
class KineticSupplyMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/member"
    member_id: str
    outcome: str
    turnover_s_inv: KineticSupportInterval
    specificity: KineticSupportInterval
    constants: ApparentKineticConstants | None
    unresolved_terms: tuple[str, ...]
    source_parents: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.member_id)
        if self.outcome not in OUTCOMES:
            raise ValueError("kinetic member has an unknown disposition")
        for bounds in (self.turnover_s_inv, self.specificity):
            if type(bounds) is not KineticSupportInterval:
                raise ValueError("kinetic member requires typed endpoint support")
            bounds.__post_init__()
        require_sorted_unique_strings(self.unresolved_terms, field_name="unresolved_terms")
        _identities(self.source_parents)
        if self.constants is not None:
            if type(self.constants) is not ApparentKineticConstants or self.outcome != "AVAILABLE":
                raise ValueError("adverse/unentered kinetic member cannot supply admitted constants")
            self.constants.__post_init__()
            if (not self.turnover_s_inv.contains(self.constants.kcat_c_s_inv)
                    or not self.specificity.contains(self.constants.specificity)):
                raise ValueError("kinetic constants contradict the joint endpoint support")
        elif self.outcome == "AVAILABLE" and not self.unresolved_terms:
            raise ValueError("partial kinetic family must identify its unresolved terms")


def _covariance(matrix: tuple[tuple[Decimal, ...], ...] | None) -> None:
    """Exact rational PSD check; no rounding a negative variance into zero."""
    if matrix is None:
        return
    if (type(matrix) is not tuple or len(matrix) != 4
            or any(type(row) is not tuple or len(row) != 4 for row in matrix)):
        raise ValueError("kinetic covariance must use the declared four-constant order")
    for row in matrix:
        for value in row:
            validate_decimal(value, field_name="kinetic_covariance")
    if any(matrix[i][j] != matrix[j][i] for i in range(4) for j in range(4)):
        raise ValueError("kinetic covariance must be symmetric")
    residual = [[Fraction(value) for value in row] for row in matrix]
    for pivot in range(4):
        diagonal = residual[pivot][pivot]
        if diagonal < 0 or (diagonal == 0 and any(residual[pivot][j] != 0 for j in range(pivot + 1, 4))):
            raise ValueError("kinetic covariance must be positive semidefinite")
        if diagonal:
            for i in range(pivot + 1, 4):
                for j in range(pivot + 1, 4):
                    residual[i][j] -= residual[i][pivot] * residual[pivot][j] / diagonal


@dataclass(frozen=True, slots=True)
class JointKineticSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/joint-supply"
    supply_id: str
    context: KineticSupplyContext
    expected_member_ids: tuple[str, ...]
    members: tuple[KineticSupplyMember, ...]
    evidence_role: str
    constant_covariance: tuple[tuple[Decimal, ...], ...] | None
    uncertainty_sources: tuple[str, ...]
    domain_limitations: tuple[str, ...]
    independent_biological_units: int | None
    dependence_interpretation: str = "JOINT_SUPPORTED_MEMBERS_WITHOUT_PROBABILITY_WEIGHTS"
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        if type(self.context) is not KineticSupplyContext:
            raise ValueError("kinetic supply has no typed material/assay context")
        self.context.__post_init__()
        require_sorted_unique_strings(self.expected_member_ids, field_name="expected_member_ids", allow_empty=False)
        if (type(self.members) is not tuple or any(type(row) is not KineticSupplyMember for row in self.members)
                or tuple(row.member_id for row in self.members) != self.expected_member_ids):
            raise ValueError("kinetic supply drops/reorders its complete committed denominator")
        for row in self.members:
            row.__post_init__()
        if self.evidence_role not in ROLES:
            raise ValueError("kinetic supply changes its conditional evidence ceiling")
        _covariance(self.constant_covariance)
        for name in ("uncertainty_sources", "domain_limitations"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if self.independent_biological_units is not None and (
                type(self.independent_biological_units) is not int or self.independent_biological_units < 0):
            raise ValueError("biological unit count must be known nonnegative or explicitly unknown")
        if self.evidence_role == "DISCLOSED_SYNTHETIC" and self.independent_biological_units != 0:
            raise ValueError("synthetic kinetic members are not biological units")
        if (self.dependence_interpretation != "JOINT_SUPPORTED_MEMBERS_WITHOUT_PROBABILITY_WEIGHTS"
                or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("unqualified kinetic support cannot manufacture probability/calibration")


@dataclass(frozen=True, slots=True)
class KineticTargetComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/target-comparison"
    comparison_id: str
    candidate_context: ObjectIdentity
    maize_turnover_s_inv: KineticSupportInterval
    gp_specificity: KineticSupportInterval
    reference_sources: tuple[ObjectIdentity, ...]
    assay_compatibility: str
    practical_relative_margin: Decimal
    comparator: str = "AT_LEAST"
    authority_url: str = "https://millenniumproblems.bio/"

    def __post_init__(self):
        validate_stable_id(self.comparison_id)
        if (type(self.candidate_context) is not ObjectIdentity
                or self.candidate_context.object_schema != KineticSupplyContext.SCHEMA):
            raise ValueError("target comparison substitutes its exact candidate context")
        for bounds in (self.maize_turnover_s_inv, self.gp_specificity):
            if type(bounds) is not KineticSupportInterval:
                raise ValueError("target references need their source-conditioned support bounds")
            bounds.__post_init__()
            if any(value is not None and value <= 0 for value in (bounds.lower, bounds.upper)):
                raise ValueError("identified reference endpoint bounds must be positive")
        _identities(self.reference_sources)
        if self.assay_compatibility not in ("DECLARED_CONDITIONAL_MATCH", "UNRESOLVED", "INCOMPATIBLE"):
            raise ValueError("target comparison lacks an explicit assay compatibility disposition")
        validate_decimal(self.practical_relative_margin, field_name="practical_relative_margin", minimum=Decimal(0))
        if self.comparator != "AT_LEAST" or self.authority_url != "https://millenniumproblems.bio/":
            raise ValueError("target comparison changes the official comparative requirements")
        validate_nonempty(self.authority_url, field_name="authority_url")
