# SPDX-License-Identifier: MPL-2.0
"""Exact conditional four-state kinetics, with intrinsic and assay meanings.

The graph is a development closure, not an identified Rubisco mechanism.
Every input rate needs a separately assessed supplier before biological use.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact

PARAMETER_ORDER = ("a", "b", "c", "d_c", "d_o", "o", "r_c", "r_o")
STATE_ORDER = ("e0", "estar", "ec", "eo")
ENDPOINT_ORDER = ("kcat_c", "kc", "kcat_o", "ko", "specificity")
INTRINSIC_MEANING = "ZERO_COMPETING_GAS_SATURATING_RUBP_PER_ACTIVE_SITE"
GAS_CONVENTION = "FREE_DISSOLVED_BULK_MICROMOLAR"


def _typed(record, kind):
    if type(record) is not kind:
        raise TypeError(f"expected exact {kind.__name__}")
    record.__post_init__()


@dataclass(frozen=True, slots=True)
class FourStateRates(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/four-state-rates"
    a: Decimal
    b: Decimal
    c: Decimal
    d_c: Decimal
    d_o: Decimal
    o: Decimal
    r_c: Decimal
    r_o: Decimal
    concentration_convention: str = GAS_CONVENTION
    clock_unit: str = "s"
    closure: str = "E0_ESTAR_EC_EO_PRODUCT_RETURN_TO_E0"

    def __post_init__(self):
        for name in PARAMETER_ORDER:
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if name not in {"b", "d_c", "d_o"} and value == 0:
                raise ValueError("positive formation, capture and product rates are required")
        if (self.concentration_convention != GAS_CONVENTION or self.clock_unit != "s"
                or self.closure != "E0_ESTAR_EC_EO_PRODUCT_RETURN_TO_E0"):
            raise ValueError("four-state rates change concentration, physical clock or closure")

    @property
    def fractions(self):
        return {name: Fraction(getattr(self, name)) for name in PARAMETER_ORDER}

    @property
    def parameter_units(self):
        return tuple((name, "uM^-1 s^-1" if name in {"c", "o"} else "s^-1")
                     for name in PARAMETER_ORDER)


@dataclass(frozen=True, slots=True)
class DissolvedGasQuery(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/dissolved-gas-query"
    co2_um: Decimal
    o2_um: Decimal
    concentration_convention: str = GAS_CONVENTION

    def __post_init__(self):
        for name in ("co2_um", "o2_um"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.concentration_convention != GAS_CONVENTION:
            raise ValueError("total bicarbonate or local gas is not dissolved bulk gas")


@dataclass(frozen=True, slots=True)
class IntrinsicKineticConstants(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/intrinsic-kinetic-constants"
    kcat_c: Exact
    kc: Exact
    kcat_o: Exact
    ko: Exact
    specificity: Exact
    interpretation: str = INTRINSIC_MEANING

    def __post_init__(self):
        for name in ENDPOINT_ORDER:
            _typed(getattr(self, name), Exact)
            if getattr(self, name).fraction <= 0:
                raise ValueError("identified intrinsic endpoints must be positive")
        if self.interpretation != INTRINSIC_MEANING:
            raise ValueError("intrinsic constants cannot become apparent assay constants")
        if self.specificity.fraction != (
                self.kcat_c.fraction * self.ko.fraction / (self.kc.fraction * self.kcat_o.fraction)):
            raise ValueError("specificity differs from the joint efficiency ratio")


@dataclass(frozen=True, slots=True)
class EndpointSensitivity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/endpoint-sensitivity"
    parameter: str
    endpoint: str
    derivative: Exact
    elasticity: Exact
    positive_parameter: bool

    def __post_init__(self):
        if self.parameter not in PARAMETER_ORDER or self.endpoint not in ENDPOINT_ORDER:
            raise ValueError("sensitivity changes its complete parameter/endpoint meanings")
        for value in (self.derivative, self.elasticity):
            _typed(value, Exact)
        if type(self.positive_parameter) is not bool:
            raise TypeError("sensitivity requires its exact zero-parameter flag")
        if not self.positive_parameter and self.elasticity.fraction != 0:
            raise ValueError("zero-rate elasticity must retain zero, without taking log(0)")


@dataclass(frozen=True, slots=True)
class FourStateResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/four-state-result"
    result_id: str
    rates: FourStateRates
    query: DissolvedGasQuery
    populations: tuple[Exact, ...]
    carboxylation_events_per_site_s: Exact
    oxygenation_events_per_site_s: Exact
    intrinsic: IntrinsicKineticConstants
    sensitivities: tuple[EndpointSensitivity, ...]
    model_scope: str = "CONDITIONAL_FOUR_STATE_CLOSURE_NOT_BIOLOGICAL_VALIDATION"

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for record, kind in ((self.rates, FourStateRates), (self.query, DissolvedGasQuery),
                             (self.intrinsic, IntrinsicKineticConstants)):
            _typed(record, kind)
        if type(self.populations) is not tuple or len(self.populations) != len(STATE_ORDER):
            raise ValueError("four-state result changes its complete state census")
        for value in (*self.populations, self.carboxylation_events_per_site_s,
                      self.oxygenation_events_per_site_s):
            _typed(value, Exact)
            if value.fraction < 0:
                raise ValueError("state probabilities and event fluxes cannot be negative")
        if (type(self.sensitivities) is not tuple
                or tuple((row.parameter, row.endpoint) for row in self.sensitivities)
                != tuple((p, e) for p in PARAMETER_ORDER for e in ENDPOINT_ORDER)):
            raise ValueError("kinetic result omits a consequential parameter sensitivity")
        for row in self.sensitivities:
            _typed(row, EndpointSensitivity)
            if row.positive_parameter != (getattr(self.rates, row.parameter) > 0):
                raise ValueError("sensitivity changes its zero-rate interpretation")
        if self.model_scope != "CONDITIONAL_FOUR_STATE_CLOSURE_NOT_BIOLOGICAL_VALIDATION":
            raise ValueError("four-state mathematics cannot establish biological accuracy")


@dataclass(frozen=True, slots=True)
class FixedOxygenCarboxylationResponse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/fixed-oxygen-response"
    intrinsic: IntrinsicKineticConstants
    o2_um: Decimal
    apparent_kc_um: Exact
    interpretation: str = "APPARENT_KC_AT_FIXED_DISSOLVED_O2"

    def __post_init__(self):
        _typed(self.intrinsic, IntrinsicKineticConstants)
        _typed(self.apparent_kc_um, Exact)
        validate_decimal(self.o2_um, field_name="o2_um", minimum=Decimal(0))
        if (self.interpretation != "APPARENT_KC_AT_FIXED_DISSOLVED_O2"
                or self.apparent_kc_um.fraction != self.intrinsic.kc.fraction
                * (1 + Fraction(self.o2_um) / self.intrinsic.ko.fraction)):
            raise ValueError("apparent oxygen-dependent KC changes its intrinsic source")


class _Dual:
    """Exact forward derivatives of this small rational endpoint map."""

    def __init__(self, value, derivatives=None):
        self.value = Fraction(value)
        self.derivatives = dict(derivatives or {})

    @staticmethod
    def of(value):
        return value if isinstance(value, _Dual) else _Dual(value)

    def __add__(self, other):
        other = self.of(other)
        return _Dual(self.value + other.value,
                     {p: self.derivatives.get(p, 0) + other.derivatives.get(p, 0)
                      for p in PARAMETER_ORDER})

    __radd__ = __add__

    def __mul__(self, other):
        other = self.of(other)
        return _Dual(self.value * other.value,
                     {p: self.derivatives.get(p, 0) * other.value
                      + self.value * other.derivatives.get(p, 0) for p in PARAMETER_ORDER})

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.of(other)
        return _Dual(self.value / other.value,
                     {p: (self.derivatives.get(p, 0) * other.value
                          - self.value * other.derivatives.get(p, 0)) / other.value**2
                      for p in PARAMETER_ORDER})


def _intrinsic_map(q):
    a, b, c, o = (q[key] for key in ("a", "b", "c", "o"))
    dc, do, rc, ro = (q[key] for key in ("d_c", "d_o", "r_c", "r_o"))
    kc = (a + b) * (dc + rc) / (c * (a + rc))
    ko = (a + b) * (do + ro) / (o * (a + ro))
    vc, vo = a * rc / (a + rc), a * ro / (a + ro)
    return {"kcat_c": vc, "kc": kc, "kcat_o": vo, "ko": ko,
            "specificity": vc * ko / (kc * vo)}


def intrinsic_constants(rates: FourStateRates) -> IntrinsicKineticConstants:
    _typed(rates, FourStateRates)
    values = _intrinsic_map(rates.fractions)
    return IntrinsicKineticConstants(*(Exact.of(values[key]) for key in ENDPOINT_ORDER))


def endpoint_sensitivities(rates: FourStateRates) -> tuple[EndpointSensitivity, ...]:
    _typed(rates, FourStateRates)
    q = {name: _Dual(value, {name: Fraction(1)}) for name, value in rates.fractions.items()}
    outputs = _intrinsic_map(q)
    return tuple(EndpointSensitivity(parameter, endpoint,
        Exact.of(outputs[endpoint].derivatives[parameter]),
        Exact.of(q[parameter].value * outputs[endpoint].derivatives[parameter] / outputs[endpoint].value),
        q[parameter].value > 0) for parameter in PARAMETER_ORDER for endpoint in ENDPOINT_ORDER)


def solve_four_state(rates: FourStateRates, query: DissolvedGasQuery, *, result_id: str) -> FourStateResult:
    """Normalize the generator using the existing exact balance solver."""
    from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.science import stationary

    _typed(rates, FourStateRates)
    _typed(query, DissolvedGasQuery)
    q = rates.fractions
    edges = ((0, 1, q["a"]), (1, 0, q["b"]), (1, 2, q["c"] * Fraction(query.co2_um)),
             (2, 1, q["d_c"]), (2, 0, q["r_c"]), (1, 3, q["o"] * Fraction(query.o2_um)),
             (3, 1, q["d_o"]), (3, 0, q["r_o"]))
    populations = stationary(edges, 4)
    return FourStateResult(result_id, rates, query, tuple(Exact.of(p) for p in populations),
        Exact.of(q["r_c"] * populations[2]), Exact.of(q["r_o"] * populations[3]),
        intrinsic_constants(rates), endpoint_sensitivities(rates))


def fixed_oxygen_response(constants: IntrinsicKineticConstants, *, o2_um: Decimal):
    _typed(constants, IntrinsicKineticConstants)
    validate_decimal(o2_um, field_name="o2_um", minimum=Decimal(0))
    return FixedOxygenCarboxylationResponse(constants, o2_um,
        Exact.of(constants.kc.fraction * (1 + Fraction(o2_um) / constants.ko.fraction)))
