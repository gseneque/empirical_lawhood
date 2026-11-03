# SPDX-License-Identifier: MPL-2.0
"""Independent source mathematics and pointwise preparation assessment.

No PyBaMM import or initializer/charging call occurs here. A proved source root
is a derived mathematical operand; only an authentic separately joined native
witness can establish which preparation the producer actually used.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import SOURCE_MEMBERS
from .preparation_contracts import (
    InitialElectrodePreparationWitness, InitialPreparationAssessment, ObservationKind, PreparationProtocol,
    ProcessedInitialStateLayout, PreparedTraceJoin, StateObservation, identity,
)

D = Decimal
PREPARATION_SOURCE_MEMBERS = tuple(sorted(dict((*SOURCE_MEMBERS,
    ("models/full_battery_models/lithium_ion/initial_state.py", "77b28eab9ae8c44ed9f38408e08cea1ea7e292a5a8c6a277daf8b1da7afd7ce4"),
    ("parameters/geometric_parameters.py", "4609bf6e420494d76e58102fbc43222778ceaa10bc167a2b054c642df436aff9"),
    ("parameters/constants.py", "e347e9db3c6d452d0e40a9d33123f589ffeb9e15bbc21f9ed1fda3fa9575947d"),
    ("scipy/constants/_codata.py", "005317bcd5e11a7cf5c51420a0027399a5c6e39149f3a124e22382dc384cd102"),
)).items()))


def _fraction(value):
    """Exact producing binary64 representation of a source literal or return."""
    return Fraction.from_float(float(value))


def _ball(value):
    from flint import arb, fmpq
    value = value if isinstance(value, Fraction) else _fraction(value)
    return arb(fmpq(value.numerator, value.denominator))


def _rational(value):
    q = value.fmpq()
    return Fraction(int(q.numerator), int(q.denominator))


def _soft_asymptote(sto):
    # Original stoichiometry is used. Both admitted feasible intervals are
    # inside the source linear-continuation cutoff; no reciprocal substitute.
    amplitude, rate, center = map(_ball, ("205.0568621937484", "6910.192179565431", "-7.7e-4"))
    low = lambda x: amplitude * (1 + (-rate * (x - center)).exp()).log()
    return low(sto) - low(1 - sto)


def _negative_ocp(x):
    return (_ball("1.9793") * (-_ball("39.3631") * x).exp() + _ball("0.2482")
            - _ball("0.0909") * (_ball("29.8538") * (x - _ball("0.1234"))).tanh()
            - _ball("0.04478") * (_ball("14.9159") * (x - _ball("0.2769"))).tanh()
            - _ball("0.0205") * (_ball("30.4444") * (x - _ball("0.6103"))).tanh()
            + _soft_asymptote(x))


def _positive_ocp(y):
    return (-_ball("0.8090") * y + _ball("4.4875")
            - _ball("0.0428") * (_ball("18.5138") * (y - _ball("0.5542"))).tanh()
            - _ball("17.7326") * (_ball("15.7890") * (y - _ball("0.3117"))).tanh()
            + _ball("17.5842") * (_ball("15.9308") * (y - _ball("0.3120"))).tanh()
            + _soft_asymptote(y))


def source_stock(parameter_source):
    """Pinned pre-SOC stock literals; this function observes no runtime state."""
    if parameter_source == "Chen2020":
        return tuple(map(D, ("33133", "63104", "29866", "17038")))
    if parameter_source == "ORegan2022":
        return tuple(map(D, ("29583", "51765", "28866", "13975")))
    raise ValueError("unsupported source stock")


def capacity_factors(parameter_source):
    cn, cp, initial_n, initial_p = map(_fraction, source_stock(parameter_source))
    ln, lp, en, ep = map(_fraction, ("8.52e-5", "7.56e-5", ".75", ".665"))
    return ln * en * cn, lp * ep * cp, ln * en * initial_n + lp * ep * initial_p


def monotonicity_margin():
    """Global cancellation bound, not a sampled monotonicity test.

    sech²(sqrt(s)) is 1-Lipschitz on s>=0. The maximum squared-argument
    difference is b²d²h²/(d²-b²); the discarded remaining NMC term is negative.
    Graphite and both source asymptotes also have strictly negative derivatives.
    """
    b, d, c1, c2, beta, delta, linear = map(_fraction,
        ("15.7890", "15.9308", ".3117", ".3120", "17.7326", "17.5842", ".8090"))
    B, C = beta * b, delta * d
    maximum = b * b * d * d * (c2 - c1) ** 2 / (d * d - b * b)
    margin = linear - (C - B) - B * maximum
    if not d > b or not C > B or not margin > Fraction(3, 10):
        raise ValueError("pinned NMC coefficients do not establish the source theorem")
    return margin


@dataclass(frozen=True, slots=True)
class RootEnclosure(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/source-root-enclosure"
    target_voltage_v: Decimal
    lower_numerator: int
    lower_denominator: int
    upper_numerator: int
    upper_denominator: int
    unique_on_complete_feasible_interval: bool = True
    observation_kind: str = "DERIVED_SOURCE_MATHEMATICS"

    def __post_init__(self):
        if (self.target_voltage_v not in (D("2.5"), D("4.2"))
                or min(self.lower_denominator, self.upper_denominator) <= 0
                or self.lower >= self.upper or not self.unique_on_complete_feasible_interval
                or self.observation_kind != "DERIVED_SOURCE_MATHEMATICS"):
            raise ValueError("root enclosure loses complete domain, uniqueness or derived status")

    @property
    def lower(self):
        return Fraction(self.lower_numerator, self.lower_denominator)

    @property
    def upper(self):
        return Fraction(self.upper_numerator, self.upper_denominator)


def source_root_enclosures(parameter_source, *, width=Fraction(1, 10**12)):
    """Both unique roots of the real pinned binary64-coefficient source function.

    Arb rigorously encloses transcendental evaluations. This does not assert
    bitwise monotonicity or accuracy of the separate PyBaMM/libm calculation.
    """
    from flint import ctx
    if width <= 0 or width > Fraction(1, 10**6):
        raise ValueError("root uncertainty must be explicitly narrow and positive")
    qn, qp, lithium = capacity_factors(parameter_source)
    epsilon = _fraction("1e-6")
    left = max(epsilon, (lithium - qp * (1 - epsilon)) / qn)
    right = min(1 - epsilon, (lithium - qp * epsilon) / qn)
    if not left < right:
        raise ValueError("source has no complete physically feasible root interval")
    slope = monotonicity_margin() * qn / qp
    with ctx.workprec(256):
        voltage = lambda x: _positive_ocp(_ball((lithium - qn * x) / qp)) - _negative_ocp(_ball(x))
        roots = []
        for target in (D("2.5"), D("4.2")):
            target_ball = _ball(target)
            if not voltage(left) < target_ball or not voltage(right) > target_ball:
                raise ValueError("source endpoint crossing is unresolved")
            lo, hi = left, right
            while hi - lo > width:
                midpoint = (lo + hi) / 2
                residual = voltage(midpoint) - target_ball
                if residual < 0:
                    lo = midpoint
                elif residual > 0:
                    hi = midpoint
                else:
                    error = max(abs(_rational(residual.lower())), abs(_rational(residual.upper()))) / slope
                    new_lo, new_hi = max(lo, midpoint - error), min(hi, midpoint + error)
                    if new_hi - new_lo >= hi - lo:
                        raise ValueError("source root enclosure remains numerically unresolved")
                    lo, hi = new_lo, new_hi
            roots.append(RootEnclosure(target, lo.numerator, lo.denominator, hi.numerator, hi.denominator))
        if roots[0].upper >= roots[1].lower:
            raise ValueError("source usable capacity ordering is unresolved")
        return tuple(roots)


def trace_identity(trace):
    return ObjectIdentity.from_record(trace.trace_id, trace)


def _close(left, right, absolute, relative=D(0)):
    return abs(left - right) <= absolute + relative * max(abs(left), abs(right))


def _electrode_reasons(protocol, witness):
    from flint import ctx
    reasons = []
    cn, cp, stock_n, stock_p = source_stock(protocol.parameter_source)
    if (witness.known_value != "cyclable lithium capacity" or witness.direction != "NONE"
            or not witness.exact_min_max or witness.ocp_clipping_tolerance != protocol.ocp_clipping_tolerance
            or witness.reference_temperature_k != protocol.reference_temperature_k
            or (witness.lower_voltage_v, witness.upper_voltage_v) != (D("2.5"), D("4.2"))):
        return ["source-OCP-preparation-semantics-changed"]
    if (witness.pre_soc_negative_concentration, witness.pre_soc_positive_concentration) != (stock_n, stock_p):
        reasons.append("pre-SOC-particle-stock-changed")
    if not D("96485.33212") < witness.faraday_constant < D("96485.332124"):
        reasons.append("source-Faraday-constant-unresolved")
    factors = capacity_factors(protocol.parameter_source)
    common = _fraction(witness.faraday_constant) * _fraction(".065") * _fraction("1.58") / 3600
    for observed, factor in zip((witness.negative_electrode_capacity_ah, witness.positive_electrode_capacity_ah,
                                witness.particle_lithium_capacity_ah), factors, strict=True):
        exact = common * factor
        with localcontext() as decimal_context:
            decimal_context.prec = 80
            expected = D(exact.numerator) / D(exact.denominator)
        if not _close(observed, expected, protocol.scalar_atol):
            reasons.append("electrode-or-particle-lithium-capacity-disagrees")
    qn, qp, lithium = factors
    with ctx.workprec(256):
        for x, y, target in ((witness.x0, witness.y0, D("2.5")), (witness.x100, witness.y100, D("4.2"))):
            if not D("1e-6") <= x <= D(".999999") or not D("1e-6") <= y <= D(".999999"):
                reasons.append("endpoint-stoichiometry-outside-complete-feasible-domain")
            expected_y = _ball((lithium - qn * _fraction(x)) / qp)
            if not abs(expected_y - _ball(y)) < _ball(protocol.scalar_atol):
                reasons.append("endpoint-particle-lithium-balance-disagrees")
            residual = _positive_ocp(_ball(y)) - _negative_ocp(_ball(x)) - _ball(target)
            if not abs(residual) < _ball(protocol.endpoint_residual_tolerance_v):
                reasons.append("endpoint-source-voltage-residual-unresolved")
    if not witness.x100 > witness.x0 or not witness.y0 > witness.y100 or witness.usable_capacity_ah <= 0:
        reasons.append("usable-electrode-capacity-not-positive")
    else:
        for capacity in (witness.negative_electrode_capacity_ah * (witness.x100 - witness.x0),
                         witness.positive_electrode_capacity_ah * (witness.y0 - witness.y100)):
            if not _close(capacity, witness.usable_capacity_ah, protocol.scalar_atol):
                reasons.append("usable-electrode-capacity-disagrees")
    xn = witness.x0 + protocol.requested_soc * (witness.x100 - witness.x0)
    yp = witness.y0 - protocol.requested_soc * (witness.y0 - witness.y100)
    if not _close(witness.assigned_negative_concentration, cn * xn, protocol.scalar_atol, protocol.state_rtol):
        reasons.append("assigned-negative-SOC-disagrees")
    if not _close(witness.assigned_positive_concentration, cp * yp, protocol.scalar_atol, protocol.state_rtol):
        reasons.append("assigned-positive-SOC-disagrees")
    # Re-run the independent complete-domain proof, never the native initializer.
    source_root_enclosures(protocol.parameter_source)
    return reasons


def _layout_reasons(protocol, layout):
    cn, cp, _, _ = source_stock(protocol.parameter_source)
    nx, nr = protocol.electrode_points, protocol.particle_points
    particle_count = nr if protocol.model_family == "SPMe" else nx * nr
    particle_prefix = "X-averaged " if protocol.model_family == "SPMe" else ""
    expected = [
        ("discharge-capacity", "Discharge capacity [A.h]", 1, D(1)),
        ("throughput-capacity", "Throughput capacity [A.h]", 1, D(1)),
        ("negative-solid", particle_prefix + "negative particle concentration [mol.m-3]" if particle_prefix else "Negative particle concentration [mol.m-3]", particle_count, cn),
        ("positive-solid", particle_prefix + "positive particle concentration [mol.m-3]" if particle_prefix else "Positive particle concentration [mol.m-3]", particle_count, cp),
        ("electrolyte", "Porosity times concentration [mol.m-3]", 3 * nx, D(1000)),
        ("temperature", "Volume-averaged cell temperature [K]", 1, D("298.15")),
        ("current", "Current variable [A]", 1, D(5)),
    ]
    if protocol.model_family == "DFN":
        expected.extend((("negative-potential", "Negative electrode potential [V]", nx, D(1)),
                         ("positive-potential", "Positive electrode potential [V]", nx, D(1)),
                         ("electrolyte-potential", "Electrolyte potential [V]", 3 * nx, D(1))))
    if tuple((b.role, b.variable_name, b.stop - b.start, b.scale) for b in layout.blocks) != tuple(expected):
        return ["complete-source-state-layout-disagrees"]
    expected_rhs = 3 + 2 * particle_count + 3 * nx
    if layout.differential_count != expected_rhs or any(b.reference != 0 for b in layout.blocks[:6]):
        return ["source-state-dimensions-or-reference-disagrees"]
    electrolyte = layout.blocks[4]
    if tuple((start, stop) for _, start, stop in layout.electrolyte_child_slices) != tuple(
            (electrolyte.start + i * nx, electrolyte.start + (i + 1) * nx) for i in range(3)):
        return ["source-electrolyte-alias-dimensions-disagree"]
    return []


def assess_initial_preparation(trace, *, protocol=None, witness=None, layout=None,
                               requested_initial=None, actual_initial=None, join=None):
    """Assess known contradictions and retain missing evidence as UNEVALUABLE.

    The caller authenticates declared input materializations/producer receipts;
    this pure function checks their exact scientific identities and values.
    """
    trace.__post_init__()
    adverse, missing = set(), set()
    count, maximum = 0, None
    if not trace.times_s:
        missing.add("native-initial-receivers-absent")
    else:
        if abs(trace.mean_temperature_k[0] - trace.config.initial_temperature_k) > D(".01"):
            adverse.add("initial-temperature-disagrees")
        if trace.capacity_ah[0] != 0:
            adverse.add("initial-capacity-origin-nonzero")
        if trace.times_s[0] != 0:
            adverse.add("initial-global-clock-nonzero")
    if trace.charging_attempts and trace.charging_attempts[0].requested_start_clock_s != 0:
        adverse.add("initial-requested-global-clock-nonzero")
    operands = (protocol, witness, layout, requested_initial, actual_initial, join)
    if any(value is None for value in operands):
        missing.add("authentic-initial-preparation-witness-absent")
    else:
        for record, record_type in zip(operands, (PreparationProtocol, InitialElectrodePreparationWitness,
                ProcessedInitialStateLayout, StateObservation, StateObservation, PreparedTraceJoin), strict=True):
            if type(record) is not record_type:
                raise ValueError("preparation substitutes its typed scientific operands")
            record.__post_init__()
        config_identity = ObjectIdentity.from_record(trace.config.config_id, trace.config)
        selected_family = "DFN" if "dfn" in trace.config.model_view else "SPMe"
        selected_parameter = "Chen2020" if trace.config.model_view == "chen-spme" else "ORegan2022"
        if hasattr(trace.config, "numerical_view"):
            selected_mesh = (trace.config.numerical_view.electrode_points, trace.config.numerical_view.particle_points)
        elif hasattr(trace.config, "electrode_points"):
            selected_mesh = (trace.config.electrode_points, trace.config.particle_points)
        else:
            selected_mesh = (60, 80) if trace.config.model_view == "oregan-dfn-refined" else (30, 40)
        selected_source = ObjectIdentity.from_record(trace.config.source.source_id, trace.config.source)
        protocol_id = identity(protocol, protocol.protocol_id)
        layout_id = identity(layout, layout.layout_id)
        if (protocol.configuration != config_identity or protocol.source != selected_source
                or protocol.model_family != selected_family or protocol.parameter_source != selected_parameter
                or (protocol.electrode_points, protocol.particle_points) != selected_mesh
                or protocol.initial_temperature_k != trace.config.initial_temperature_k
                or join.trace != trace_identity(trace) or join.protocol != protocol_id
                or join.layout != layout_id or join.witness != identity(witness, witness.witness_id)
                or join.requested_initial != identity(requested_initial, requested_initial.observation_id)
                or join.actual_initial != identity(actual_initial, actual_initial.observation_id)
                or layout.protocol != protocol_id or witness.protocol != protocol_id
                or any(o.protocol != protocol_id or o.layout != layout_id for o in (requested_initial, actual_initial))):
            raise ValueError("preparation changes exact configuration/trace/witness/layout/custody joins")
        if not set(PREPARATION_SOURCE_MEMBERS).issubset(set(protocol.source_members)):
            raise ValueError("preparation substitutes pinned independent source mathematics")
        if not layout.observed_from_built_model:
            missing.add("built-model-layout-not-observed")
        if trace.charging_attempts and any(row.model_expression_sha256 != layout.model_expression_sha256 for row in trace.charging_attempts):
            raise ValueError("preparation changes the actual processed charging model")
        adverse.update(_layout_reasons(protocol, layout))
        if not witness.initializer_dispositions or any(s in {"NOT_ENTERED", "UNKNOWN_COMPLETION"} for s in witness.initializer_dispositions):
            missing.add("initializer-completion-census-unresolved")
        elif witness.initializer_dispositions[-1] != "RETURNED":
            missing.add("initializer-successful-return-absent")
        else:
            adverse.update(_electrode_reasons(protocol, witness))
        if (requested_initial.role, actual_initial.role) != ("requested-initial", "actual-initial"):
            raise ValueError("preparation substitutes requested and observed boundary roles")
        if any(o.kind is not ObservationKind.OBSERVED for o in (requested_initial, actual_initial)):
            missing.add("required-full-initial-state-not-observed")
        elif any(o.model_clock_s != 0 for o in (requested_initial, actual_initial)):
            adverse.add("initial-state-global-clock-nonzero")
        elif any(len(o.scaled_values) != layout.differential_count + layout.algebraic_count for o in (requested_initial, actual_initial)):
            adverse.add("full-initial-state-denominator-incomplete")
        elif not _layout_reasons(protocol, layout):
            cn, cp, _, _ = source_stock(protocol.parameter_source)
            xn, yp = witness.assigned_negative_concentration / cn, witness.assigned_positive_concentration / cp
            expected = []
            for b in layout.blocks[:6]:
                if b.role == "electrolyte":
                    expected.extend(value for porosity in (D(".25"), D(".47"), D(".335"))
                                    for value in (porosity,) * protocol.electrode_points)
                else:
                    value = {"discharge-capacity": D(0), "throughput-capacity": D(0),
                             "negative-solid": xn, "positive-solid": yp,
                             "temperature": protocol.initial_temperature_k / D("298.15")}[b.role]
                    expected.extend((value,) * (b.stop - b.start))
            residuals = []
            for requested, observed, target in zip(requested_initial.scaled_values, actual_initial.scaled_values, expected):
                count += 1
                residuals.extend((abs(requested - target), abs(observed - target), abs(requested - observed)))
                if not _close(requested, target, protocol.state_atol, protocol.state_rtol) or not _close(observed, target, protocol.state_atol, protocol.state_rtol):
                    adverse.add("pointwise-full-initial-state-disagrees")
                if not _close(requested, observed, protocol.state_atol, protocol.state_rtol):
                    adverse.add("consistent-initialization-changed-differential-state")
            maximum = max(residuals, default=D(0))
            if (not trace.charging_attempts or trace.charging_attempts[0].disposition != "RETURNED"):
                missing.add("actual-initial-charging-return-absent")
            elif trace.charging_attempts[0].start_differential_state != actual_initial.scaled_values[:layout.differential_count]:
                raise ValueError("preparation observation differs from actual charging boundary")
    disposition = A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED
    return InitialPreparationAssessment("assessment.preparation." + trace.trace_id, trace_identity(trace),
        None if join is None else identity(join, join.join_id), disposition,
        tuple(sorted(adverse | missing)), count, maximum)


def require_prepared_trace(trace, assessment):
    """Current fresh consumers call this before precision/model admission."""
    if type(assessment) is not InitialPreparationAssessment or assessment.trace != trace_identity(trace):
        raise ValueError("current trace admission substitutes its preparation assessment")
    assessment.__post_init__()
    if assessment.disposition is not A.SATISFIED or assessment.join is None or assessment.checked_state_components < 1:
        raise ValueError("current trace has no independently satisfied complete preparation")
    return trace
