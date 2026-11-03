# SPDX-License-Identifier: MPL-2.0
"""Source-derived root supplier with a separate complete-domain falsifier.

No native initializer is contacted. The supplied scalars are DERIVED operands,
not observed roots, native initialized states or evidence of earlier completion.
The independent checker verifies brackets and physics directly; it does not
rerun the producer's bisection. Later use still needs observed assignment, full
processed state, actual current/clock/origins and independent continuation.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from . import preparation_science as ps

D = Decimal
SOURCE_FARADAY = D("96485.33212331001")
SCALARS = tuple(sorted(("particle_lithium_capacity_ah", "negative_electrode_capacity_ah", "positive_electrode_capacity_ah", "usable_capacity_ah",
    "faraday_constant", "x0", "x100", "y0", "y100", "assigned_negative_concentration", "assigned_positive_concentration",
    "pre_soc_negative_concentration", "pre_soc_positive_concentration")))


def _binary(value):
    return Fraction.from_float(float(value))


def _derived_decimal(value):
    return D(str(float(value)))


@dataclass(frozen=True, slots=True)
class SourceRootPreparation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/source-derived-electrodes"
    preparation_id: str
    source: ObjectIdentity
    parameter_source: str
    source_members: tuple[tuple[str, str], ...]
    roots: tuple[ps.RootEnclosure, ...]
    particle_lithium_capacity_ah: Decimal
    negative_electrode_capacity_ah: Decimal
    positive_electrode_capacity_ah: Decimal
    usable_capacity_ah: Decimal
    faraday_constant: Decimal
    x0: Decimal
    x100: Decimal
    y0: Decimal
    y100: Decimal
    assigned_negative_concentration: Decimal
    assigned_positive_concentration: Decimal
    pre_soc_negative_concentration: Decimal
    pre_soc_positive_concentration: Decimal
    binary64_operands: tuple[tuple[str, str], ...]
    requested_soc: Decimal = D("0.30")
    reference_temperature_k: Decimal = D("298.15")
    lower_voltage_v: Decimal = D("2.5")
    upper_voltage_v: Decimal = D("4.2")
    ocp_clipping_tolerance: Decimal = D("1e-10")
    observation_kind: str = "DERIVED_SOURCE_MATHEMATICS"
    native_initializer_contacts: int = 0
    observed_native_state: bool = False
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"

    def __post_init__(self):
        validate_stable_id(self.preparation_id)
        if self.parameter_source not in {"Chen2020", "ORegan2022"} or self.source.object_schema != "empirical-lawhood/battery-refined-inquiry/source":
            raise ValueError("derived preparation changes its exact supported stock/source")
        if self.source_members != ps.PREPARATION_SOURCE_MEMBERS or len(self.roots) != 2 or any(type(root) is not ps.RootEnclosure for root in self.roots):
            raise ValueError("derived preparation loses its complete source/root denominator")
        if tuple(root.target_voltage_v for root in self.roots) != (D("2.5"), D("4.2")):
            raise ValueError("derived preparation reorders its voltage endpoint roots")
        for name in (*SCALARS, "requested_soc", "reference_temperature_k", "lower_voltage_v", "upper_voltage_v", "ocp_clipping_tolerance"):
            validate_decimal(getattr(self, name), field_name=name)
        if (self.requested_soc, self.reference_temperature_k, self.lower_voltage_v, self.upper_voltage_v, self.ocp_clipping_tolerance) != (
                D("0.30"), D("298.15"), D("2.5"), D("4.2"), D("1e-10")):
            raise ValueError("derived preparation changes its declared source SOC/OCP semantics")
        if self.binary64_operands != tuple((name, float(getattr(self, name)).hex()) for name in SCALARS):
            raise ValueError("derived preparation substitutes its exact assigned binary64 operands")
        if (self.observation_kind != "DERIVED_SOURCE_MATHEMATICS" or self.native_initializer_contacts != 0
                or self.observed_native_state or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"):
            raise ValueError("derived preparation cannot manufacture native observation or old completion")


@dataclass(frozen=True, slots=True)
class SourceRootAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/source-root-assessment"
    assessment_id: str
    preparation: ObjectIdentity
    disposition: A
    reason_codes: tuple[str, ...]
    complete_endpoint_denominator: int
    source_theorem: str = "complete-feasible-domain-strict-monotonicity-and-endpoint-brackets"
    native_preparation: str = "UNOBSERVED"
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (self.preparation.object_schema != SourceRootPreparation.SCHEMA or type(self.disposition) is not A
                or self.complete_endpoint_denominator != 2 or self.source_theorem != "complete-feasible-domain-strict-monotonicity-and-endpoint-brackets"
                or self.native_preparation != "UNOBSERVED" or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
                or self.disposition is not A.SATISFIED and not self.reason_codes):
            raise ValueError("source-root assessment changes its scope or complete denominator")


def supply_source_roots(source_identity, parameter_source):
    """Producer supplies explicit nearest-binary64 scalar operands and brackets."""
    roots = ps.source_root_enclosures(parameter_source)
    xn = tuple(_binary(_derived_decimal((root.lower + root.upper) / 2)) for root in roots)
    qn, qp, lithium = ps.capacity_factors(parameter_source)
    yp = tuple(_binary(_derived_decimal((lithium - qn * x) / qp)) for x in xn)
    cn, cp, stock_n, stock_p = ps.source_stock(parameter_source)
    common = _binary(SOURCE_FARADAY) * _binary(".065") * _binary("1.58") / 3600
    qn_actual, qp_actual, lithium_actual = (_binary(_derived_decimal(common * factor)) for factor in (qn, qp, lithium))
    soc = _binary(".30")
    values = {"particle_lithium_capacity_ah": _derived_decimal(lithium_actual), "negative_electrode_capacity_ah": _derived_decimal(qn_actual),
        "positive_electrode_capacity_ah": _derived_decimal(qp_actual), "usable_capacity_ah": _derived_decimal(qn_actual * (xn[1] - xn[0])),
        "faraday_constant": SOURCE_FARADAY, "x0": _derived_decimal(xn[0]), "x100": _derived_decimal(xn[1]),
        "y0": _derived_decimal(yp[0]), "y100": _derived_decimal(yp[1]),
        "assigned_negative_concentration": _derived_decimal(_binary(cn) * (xn[0] + soc * (xn[1] - xn[0]))),
        "assigned_positive_concentration": _derived_decimal(_binary(cp) * (yp[0] + soc * (yp[1] - yp[0]))),
        "pre_soc_negative_concentration": stock_n, "pre_soc_positive_concentration": stock_p}
    return SourceRootPreparation("preparation.source-derived." + parameter_source.lower(), source_identity, parameter_source,
        ps.PREPARATION_SOURCE_MEMBERS, roots, **values, binary64_operands=tuple((name, float(values[name]).hex()) for name in SCALARS))


def assess_source_roots(preparation):
    """Independent falsifier: source theorem/brackets and noncompensating physics."""
    from flint import ctx
    if type(preparation) is not SourceRootPreparation:
        raise ValueError("source-root assessment requires the exact typed DERIVED supplier")
    preparation.__post_init__()
    reasons = set()
    cn, cp, stock_n, stock_p = ps.source_stock(preparation.parameter_source)
    qn, qp, lithium = ps.capacity_factors(preparation.parameter_source)
    epsilon = _binary("1e-6")
    feasible_lo, feasible_hi = max(epsilon, (lithium - qp * (1 - epsilon)) / qn), min(1 - epsilon, (lithium - qp * epsilon) / qn)
    margin = ps.monotonicity_margin()
    if feasible_lo >= feasible_hi or margin <= 0:
        reasons.add("complete-source-feasible-domain-theorem-unresolved")
    with ctx.workprec(256):
        for root, x, y in zip(preparation.roots, (preparation.x0, preparation.x100), (preparation.y0, preparation.y100), strict=True):
            if not feasible_lo <= root.lower < root.upper <= feasible_hi or root.upper - root.lower > Fraction(1, 10**12):
                reasons.add("source-root-bracket-not-complete-feasible-or-precise")
            def voltage(at):
                return ps._positive_ocp(ps._ball((lithium - qn * at) / qp)) - ps._negative_ocp(ps._ball(at))
            if not voltage(root.lower) < ps._ball(root.target_voltage_v) or not voltage(root.upper) > ps._ball(root.target_voltage_v):
                reasons.add("independent-source-endpoint-bracket-does-not-cross")
            if not root.lower <= _binary(x) <= root.upper:
                reasons.add("assigned-source-root-outside-proved-bracket")
            if not abs(ps._ball((lithium - qn * _binary(x)) / qp) - ps._ball(y)) < ps._ball("1e-12"):
                reasons.add("independent-source-root-lithium-balance-disagrees")
            if not abs(ps._positive_ocp(ps._ball(y)) - ps._negative_ocp(ps._ball(x)) - ps._ball(root.target_voltage_v)) < ps._ball("1e-7"):
                reasons.add("independent-source-root-voltage-residual-unresolved")
        common = _binary(SOURCE_FARADAY) * _binary(".065") * _binary("1.58") / 3600
        for actual, factor in zip((preparation.negative_electrode_capacity_ah, preparation.positive_electrode_capacity_ah,
                preparation.particle_lithium_capacity_ah), (qn, qp, lithium), strict=True):
            if not abs(ps._ball(actual) - ps._ball(common * factor)) < ps._ball("1e-10"):
                reasons.add("independent-source-particle-capacity-disagrees")
        for expected in (_binary(preparation.negative_electrode_capacity_ah) * (_binary(preparation.x100) - _binary(preparation.x0)),
                _binary(preparation.positive_electrode_capacity_ah) * (_binary(preparation.y0) - _binary(preparation.y100))):
            if not abs(ps._ball(preparation.usable_capacity_ah) - ps._ball(expected)) < ps._ball("1e-10"):
                reasons.add("independent-source-usable-capacity-disagrees")
        soc = _binary(preparation.requested_soc)
        for actual, scale, left, right in ((preparation.assigned_negative_concentration, cn, preparation.x0, preparation.x100),
                (preparation.assigned_positive_concentration, cp, preparation.y0, preparation.y100)):
            exact = _binary(scale) * (_binary(left) + soc * (_binary(right) - _binary(left)))
            if not abs(ps._ball(actual) - ps._ball(exact)) < ps._ball("1e-8"):
                reasons.add("independent-source-SOC-assignment-disagrees")
    if preparation.faraday_constant != SOURCE_FARADAY or (preparation.pre_soc_negative_concentration, preparation.pre_soc_positive_concentration) != (stock_n, stock_p):
        reasons.add("independent-source-stock-or-constant-changed")
    if preparation.x0 >= preparation.x100 or preparation.y0 <= preparation.y100 or preparation.usable_capacity_ah <= 0:
        reasons.add("independent-source-usable-ordering-disagrees")
    return SourceRootAssessment("assessment.source-derived." + preparation.parameter_source.lower(),
        ObjectIdentity.from_record(preparation.preparation_id, preparation), A.FALSIFIED if reasons else A.SATISFIED, tuple(sorted(reasons)), 2)


def require_assessed_source_roots(preparation, assessment):
    """Recompute independently before assigning any DERIVED native operand."""
    if type(assessment) is not SourceRootAssessment or assessment != assess_source_roots(preparation) or assessment.disposition is not A.SATISFIED:
        raise ValueError("source-derived native preparation requires its authentic independently assessed supplier")
    return preparation
