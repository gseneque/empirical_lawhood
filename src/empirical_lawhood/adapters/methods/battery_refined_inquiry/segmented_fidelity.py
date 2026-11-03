# SPDX-License-Identifier: MPL-2.0
"""Independent full-state controls over original, authenticated native returns.

An interval control is a local numerical comparison, not a forecast supplier.
Every RHS/algebraic row is compared on the union of both original native knots,
integer seconds and the declared boundaries. Cubic Hermite values are DERIVED
from observed state/derivative bits. Directed Decimal arithmetic retains its
comparison uncertainty; absent derivatives never acquire invented values.
"""

from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction
from hashlib import sha256
from itertools import chain
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from . import preparation_contracts as pc
from . import preparation_science as ps
from . import segmented_contracts as sc
from . import segmented_science as ss

D = Decimal
PRECISION = 80


@dataclass(frozen=True, slots=True)
class FullStateControlProtocol(CanonicalRecord):
    """Prospective comparison weights, without a physical accuracy claim.

    Solver weights are taken unchanged from the exact common native config.
    Derivative absolute weights use the declared one-second time scale. These
    are componentwise convergence budgets, not a global solver error bound or
    a numerical choice derived from the interrupted diagnostic.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-control-protocol"
    control_id: str
    receiver_spacing_s: Decimal = D(1)
    derivative_time_scale_s: Decimal = D(1)
    arithmetic_precision: int = PRECISION
    query_grid: str = "BOTH_COMPLETE_NATIVE_KNOTS;ALL_INTEGER_SECONDS;DECLARED_INTERVAL_BOUNDARIES"
    clock_alignment: str = "ACTUAL_GLOBAL_CLOCK;SAME_REGIME;NO_EXTRAPOLATION"
    interpolation: str = "DERIVED_CUBIC_HERMITE_FROM_EXACT_OBSERVED_BINARY64_STATE_AND_DERIVATIVE"
    state_weights: str = "COMMON_SELECTED_NATIVE_ATOL_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_SCALED_COMPONENT"
    derivative_weights: str = "NATIVE_ATOL_OVER_ONE_SECOND_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_RETURNED_DERIVATIVE"
    scope: str = "LOCAL_OVERLAP_CONTROL;COMPLETE_FORECAST_AND_EVENT_CONTROLS_REMAIN_SEPARATE"
    derivative_accuracy: str = "CONVERGENCE_ONLY;NO_NATIVE_EQUATION_RESIDUAL_OR_PHYSICAL_ACCURACY_CLAIM"
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    physical_qualification: bool = False
    whole_time_certified: bool = False
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.control_id)
        for name in ("receiver_spacing_s", "derivative_time_scale_s"):
            validate_decimal(getattr(self, name), field_name=name)
        if (self.receiver_spacing_s != D(1) or self.derivative_time_scale_s != D(1)
                or type(self.arithmetic_precision) is not int or self.arithmetic_precision != PRECISION
                or self.query_grid != "BOTH_COMPLETE_NATIVE_KNOTS;ALL_INTEGER_SECONDS;DECLARED_INTERVAL_BOUNDARIES"
                or self.clock_alignment != "ACTUAL_GLOBAL_CLOCK;SAME_REGIME;NO_EXTRAPOLATION"
                or self.interpolation != "DERIVED_CUBIC_HERMITE_FROM_EXACT_OBSERVED_BINARY64_STATE_AND_DERIVATIVE"
                or self.state_weights != "COMMON_SELECTED_NATIVE_ATOL_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_SCALED_COMPONENT"
                or self.derivative_weights != "NATIVE_ATOL_OVER_ONE_SECOND_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_RETURNED_DERIVATIVE"
                or self.scope != "LOCAL_OVERLAP_CONTROL;COMPLETE_FORECAST_AND_EVENT_CONTROLS_REMAIN_SEPARATE"
                or self.derivative_accuracy != "CONVERGENCE_ONLY;NO_NATIVE_EQUATION_RESIDUAL_OR_PHYSICAL_ACCURACY_CLAIM"
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
                or type(self.physical_qualification) is not bool or self.physical_qualification
                or type(self.whole_time_certified) is not bool or self.whole_time_certified
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("full-state control changes its declared numerical operands or scientific scope")


@dataclass(frozen=True, slots=True)
class FullStateOperand:
    """A transient original segment, never a stored full-history accumulator."""
    configuration: sc.SegmentedNativeConfig
    protocol: pc.PreparationProtocol
    layout: pc.ProcessedInitialStateLayout | None
    summary: sc.SegmentSummary
    frame: object
    previous_terminal: pc.StateObservation | None = None


def _assess_operand(operand):
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry.evidence_stream import SegmentEvidenceFrame
    from .segmented_native import FullStateSegment, RawReturnedSegment
    if type(operand) is not FullStateOperand or type(operand.frame) is not SegmentEvidenceFrame:
        raise ValueError("full-state control requires an original typed segment evidence frame")
    config, protocol = operand.configuration, operand.protocol
    if type(config) is not sc.SegmentedNativeConfig or type(protocol) is not pc.PreparationProtocol:
        raise ValueError("full-state control requires exact selected configuration and preparation protocol")
    config.__post_init__()
    protocol.__post_init__()
    if (protocol.configuration != ss.identity(config, "config_id") or protocol.source != config.preparation.source
            or protocol.parameter_source != config.preparation.parameter_source
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or (protocol.electrode_points, protocol.particle_points) != (config.numerical_view.electrode_points, config.numerical_view.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k
            or not set(ps.PREPARATION_SOURCE_MEMBERS).issubset(protocol.source_members)):
        raise ValueError("full-state control changes actual source, physics, mesh, initial temperature or source pins")
    if operand.layout is not None and (type(operand.layout) is not pc.ProcessedInitialStateLayout
            or not operand.layout.observed_from_built_model or ps._layout_reasons(protocol, operand.layout)):
        raise ValueError("full-state control changes the complete source state layout or physical scaling")
    frame = operand.frame
    frame.__post_init__()
    returned_records = tuple(value for name, value in frame.records.items() if name != "request" and value is not None)
    schemas = {record_type.SCHEMA for record_type in (RawReturnedSegment, FullStateSegment, pc.StateObservation)}
    actual = {(row.payload_schema, row.content_sha256) for row in frame.native_receipt.output_logical_artifacts if row.payload_schema in schemas}
    if actual != {(record.SCHEMA, record.fingerprint()) for record in returned_records if record.SCHEMA in schemas}:
        raise ValueError("full-state control hides a materialized native output from its original receipt census")
    ss.authenticate_request_custody(operand.summary, frame.request, frame.definition,
        frame.native_receipt, frame.request_receipt)
    if operand.summary.disposition == "TECHNICAL_FAILURE":
        return ss.assess_failed_segment(operand.configuration, operand.protocol, operand.summary,
            frame.native_receipt, **frame.records)
    if operand.layout is None:
        raise ValueError("returned full-state control omits its actual processed state layout")
    return ss.assess_segment(operand.configuration, operand.protocol, operand.layout, operand.summary,
        frame.native_receipt, previous_terminal=operand.previous_terminal, **frame.records)


@dataclass(frozen=True, slots=True)
class FullStateIntervalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-interval-assessment"
    assessment_id: str
    control: ObjectIdentity
    left_configuration: ObjectIdentity
    right_configuration: ObjectIdentity
    left_summary: ObjectIdentity
    right_summary: ObjectIdentity
    left_definition: ObjectIdentity
    right_definition: ObjectIdentity
    left_receipt: ObjectIdentity
    right_receipt: ObjectIdentity
    left_segment_assessment: ss.SegmentAssessment
    right_segment_assessment: ss.SegmentAssessment
    exact_interval_start: tuple[int, int] | None
    exact_interval_end: tuple[int, int] | None
    interval_start_s: Decimal | None
    interval_end_s: Decimal | None
    query_grid_sha256: str
    query_count: int
    original_native_knots_in_interval: tuple[int, int]
    integer_seconds_in_interval: int
    rhs_rows_per_query: int
    algebraic_rows_per_query: int
    checked_rhs_components: int
    checked_algebraic_components: int
    checked_derivative_components: int
    derived_state_components: int
    derived_derivative_components: int
    uncertain_state_components: int
    uncertain_derivative_components: int
    maximum_scaled_state_residual_lower: Decimal | None
    maximum_scaled_state_residual_upper: Decimal | None
    maximum_scaled_derivative_residual_lower: Decimal | None
    maximum_scaled_derivative_residual_upper: Decimal | None
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "LOCAL_OVERLAP_CONTROL;NOT_A_LATER_USE_SUPPLIER"
    whole_time_certified: bool = False
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        validate_sha256(self.query_grid_sha256)
        for value, schema in ((self.control, FullStateControlProtocol.SCHEMA),
                *((row, sc.SegmentedNativeConfig.SCHEMA) for row in (self.left_configuration, self.right_configuration)),
                *((row, sc.SegmentSummary.SCHEMA) for row in (self.left_summary, self.right_summary)),
                *((row, NativeSubworkDefinition.SCHEMA) for row in (self.left_definition, self.right_definition)),
                *((row, CanonicalTaskReceipt.SCHEMA) for row in (self.left_receipt, self.right_receipt))):
            if value.object_schema != schema:
                raise ValueError("full-state assessment substitutes an original control/custody operand")
        if (type(self.left_segment_assessment) is not ss.SegmentAssessment or type(self.right_segment_assessment) is not ss.SegmentAssessment
                or self.left_segment_assessment.summary != self.left_summary or self.right_segment_assessment.summary != self.right_summary
                or self.left_segment_assessment.native_receipt != self.left_receipt or self.right_segment_assessment.native_receipt != self.right_receipt):
            raise ValueError("full-state assessment changes independently assessed original segment custody")
        for name in ("query_count", "integer_seconds_in_interval", "rhs_rows_per_query", "algebraic_rows_per_query", "checked_rhs_components", "checked_algebraic_components",
                "checked_derivative_components", "derived_state_components", "derived_derivative_components",
                "uncertain_state_components", "uncertain_derivative_components"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("full-state assessment changes the complete component denominator")
        if (len(self.original_native_knots_in_interval) != 2
                or any(type(n) is not int or n < 0 for n in self.original_native_knots_in_interval)):
            raise ValueError("full-state assessment loses original native-knot counts")
        total = self.checked_rhs_components + self.checked_algebraic_components
        if (self.checked_rhs_components > self.query_count * self.rhs_rows_per_query
                or self.checked_algebraic_components > self.query_count * self.algebraic_rows_per_query
                or self.checked_derivative_components > total
                or self.derived_state_components > total or self.uncertain_state_components > total
                or self.derived_derivative_components > self.checked_derivative_components
                or self.uncertain_derivative_components > self.checked_derivative_components):
            raise ValueError("full-state assessment contradicts its exact compared component denominator")
        for name in ("interval_start_s", "interval_end_s", "maximum_scaled_state_residual_lower", "maximum_scaled_state_residual_upper",
                "maximum_scaled_derivative_residual_lower", "maximum_scaled_derivative_residual_upper"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
                if value < 0:
                    raise ValueError("full-state clocks/residuals cannot be negative")
        for kind in ("state", "derivative"):
            low, high = (getattr(self, "maximum_scaled_" + kind + "_residual_" + part) for part in ("lower", "upper"))
            if (low is None) != (high is None) or low is not None and low > high:
                raise ValueError("full-state residual uncertainty interval is invalid")
        for exact, projected, rounding in ((self.exact_interval_start, self.interval_start_s, ROUND_FLOOR),
                (self.exact_interval_end, self.interval_end_s, ROUND_CEILING)):
            if exact is None:
                if projected is not None:
                    raise ValueError("full-state boundary projection invents an unavailable exact operand")
            elif (type(exact) is not tuple or len(exact) != 2 or any(type(n) is not int for n in exact)
                    or exact[1] <= 0 or exact[0] < 0
                    or (Fraction(*exact).numerator, Fraction(*exact).denominator) != exact
                    or projected != _decimal(Fraction(*exact), rounding)):
                raise ValueError("full-state boundary loses exact rational operands or changes its outward projection")
        if ((self.interval_start_s is None) != (self.interval_end_s is None)
                or self.interval_start_s is not None and self.interval_end_s < self.interval_start_s
                or type(self.disposition) is not A or self.scope != "LOCAL_OVERLAP_CONTROL;NOT_A_LATER_USE_SUPPLIER"
                or type(self.whole_time_certified) is not bool or self.whole_time_certified
                or type(self.physical_qualification) is not bool or self.physical_qualification
                or self.disposition is not A.SATISFIED and not self.reason_codes):
            raise ValueError("local full-state assessment invents a complete forecast or physical qualification")
        if self.disposition is A.SATISFIED and (not self.query_count or self.reason_codes
                or self.exact_interval_start is None or self.exact_interval_end is None
                or any(getattr(self, "maximum_scaled_" + kind + "_residual_upper") is None
                    or getattr(self, "maximum_scaled_" + kind + "_residual_upper") > 1 for kind in ("state", "derivative"))
                or self.left_segment_assessment.disposition is not A.SATISFIED or self.right_segment_assessment.disposition is not A.SATISFIED
                or min(self.rhs_rows_per_query, self.algebraic_rows_per_query) < 1
                or self.checked_rhs_components != self.query_count * self.rhs_rows_per_query
                or self.checked_algebraic_components != self.query_count * self.algebraic_rows_per_query
                or any(check.full_state_components != check.retained_native_knots * (self.rhs_rows_per_query + self.algebraic_rows_per_query)
                    for check in (self.left_segment_assessment, self.right_segment_assessment))
                or self.checked_derivative_components != self.checked_rhs_components + self.checked_algebraic_components
                or self.uncertain_state_components or self.uncertain_derivative_components):
            raise ValueError("satisfied full-state control omits independently assessed state/derivative components")


def _binary_fraction(value):
    return Fraction.from_float(float.fromhex(value))


def _decimal(value, rounding):
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, rounding
        return D(value.numerator) / D(value.denominator)


def _coefficient(value):
    return _decimal(value, ROUND_FLOOR), _decimal(value, ROUND_CEILING)


def _exact(value):
    return D.from_float(float.fromhex(value))


def _weighted(coefficients, values):
    """Outward enclosure of a linear combination of exact binary64 values."""
    results = []
    for rounding, bound in ((ROUND_FLOOR, 0), (ROUND_CEILING, 1)):
        with localcontext() as context:
            context.prec, context.rounding = PRECISION, rounding
            result = D(0)
            for coefficient, value in zip(coefficients, values, strict=True):
                result += coefficient[bound if value >= 0 else 1 - bound] * value
            results.append(result)
    return tuple(results)


def _spline_coefficients(start, end, clock):
    h = end - start
    u = (clock - start) / h
    state = (2 * u**3 - 3 * u**2 + 1, (u**3 - 2 * u**2 + u) * h,
        -2 * u**3 + 3 * u**2, (u**3 - u**2) * h)
    derivative = ((6 * u**2 - 6 * u) / h, 3 * u**2 - 4 * u + 1,
        (-6 * u**2 + 6 * u) / h, 3 * u**2 - 2 * u)
    return tuple(map(_coefficient, state)), tuple(map(_coefficient, derivative))


def _snapshot(full_state, clock):
    """Yield all original rows at one clock; no full-grid state accumulation."""
    for block in full_state.blocks:
        clocks = tuple(map(_binary_fraction, block.clock_binary64))
        if clocks[0] <= clock <= clocks[-1]:
            at = bisect_left(clocks, clock)
            width = len(clocks)
            if at < width and clocks[at] == clock:
                for row in range(block.state_rows):
                    state = _exact(block.state_binary64[row * width + at])
                    derivative = None if block.derivative_binary64 is None else _exact(block.derivative_binary64[row * width + at])
                    yield (state, state), None if derivative is None else (derivative, derivative), False
                return
            if block.derivative_binary64 is None:
                return
            state_coefficients, derivative_coefficients = _spline_coefficients(clocks[at - 1], clocks[at], clock)
            for row in range(block.state_rows):
                first, last = row * width + at - 1, row * width + at
                values = tuple(_exact(bits) for bits in (block.state_binary64[first], block.derivative_binary64[first],
                    block.state_binary64[last], block.derivative_binary64[last]))
                yield _weighted(state_coefficients, values), _weighted(derivative_coefficients, values), True
            return


def _absolute(interval):
    low, high = interval
    return (D(0) if low <= 0 <= high else min(low.copy_abs(), high.copy_abs()), max(low.copy_abs(), high.copy_abs()))


def _residual(left, right, atol, rtol):
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, ROUND_FLOOR
        low = left[0] - right[1]
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, ROUND_CEILING
        high = left[1] - right[0]
    low, high = _absolute((low, high))
    a, b = _absolute(left), _absolute(right)
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, ROUND_FLOOR
        budget_low = atol + rtol * max(a[0], b[0])
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, ROUND_CEILING
        budget_high = atol + rtol * max(a[1], b[1])
        residual_high = high / budget_low
    with localcontext() as context:
        context.prec, context.rounding = PRECISION, ROUND_FLOOR
        residual_low = low / budget_high
    return residual_low, residual_high, A.FALSIFIED if low > budget_high else A.SATISFIED if high <= budget_low else A.UNEVALUABLE


def _clocks(full):
    return tuple(_binary_fraction(bits) for block in full.blocks for bits in block.clock_binary64)


def _same_layout(left, right):
    names = ("model_expression_sha256", "initial_conditions_sha256", "differential_count", "algebraic_count", "blocks", "electrolyte_child_slices")
    return all(getattr(left, name) == getattr(right, name) for name in names)


def assess_interval(control, left, right, *, start_s=None, end_s=None):
    """Recompute independent original segment checks, then compare every row.

    Only this pair of full segment frames and scalar/clock working data are
    retained. The returned canonical record contains custody, complete counts
    and residual bounds, with no full state arrays. Scientific/native entry and
    authentic ordinary input receipts are the caller's separate boundaries.
    """
    if type(control) is not FullStateControlProtocol:
        raise ValueError("full-state comparison requires its explicit prospective control protocol")
    control.__post_init__()
    checks = tuple(map(_assess_operand, (left, right)))
    a, b = left.configuration, right.configuration
    if (a.native != b.native or a.preparation != b.preparation or a.preparation_assessment != b.preparation_assessment
            or (a.method.maximum_segment_horizon_s, b.method.maximum_segment_horizon_s) not in ((D(60), D(30)), (D(30), D(15)))):
        raise ValueError("full-state comparison changes its isolated native/root/half-segment operands")
    reasons, adverse = set(), set()
    if any(check.disposition is not A.SATISFIED for check in checks):
        reasons.add("independent-original-full-segment-integrity-unresolved")
    if left.summary.regime != right.summary.regime:
        reasons.add("actual-hybrid-regimes-differ;one-sided-event-control-required")
    if left.layout is None or right.layout is None:
        reasons.add("actual-full-state-layout-unavailable")
    elif not _same_layout(left.layout, right.layout):
        raise ValueError("full-state comparison substitutes model equations, full layout or physical scaling")
    full = (left.frame.full_state, right.frame.full_state)
    start, end, grid = None, None, ()
    original_counts = (0, 0)
    integers = 0
    if all(record is not None for record in full):
        clocks = tuple(map(_clocks, full))
        start = max(rows[0] for rows in clocks) if start_s is None else Fraction(start_s)
        end = min(rows[-1] for rows in clocks) if end_s is None else Fraction(end_s)
        if start < 0 or end < start:
            raise ValueError("full-state comparison requires a nonnegative ordered overlap interval")
        if any(start < rows[0] or end > rows[-1] for rows in clocks):
            raise ValueError("full-state comparison cannot extrapolate beyond an original native segment")
        original_counts = tuple(sum(start <= clock <= end for clock in rows) for rows in clocks)
        first_integer, last_integer = -(-start.numerator // start.denominator), end.numerator // end.denominator
        integers = max(0, last_integer - first_integer + 1)
        grid = tuple(sorted({start, end, *chain.from_iterable((clock for clock in rows if start <= clock <= end) for rows in clocks),
            *(Fraction(n) for n in range(first_integer, last_integer + 1))}))
    else:
        reasons.add("actual-full-state-payload-unavailable")
    rhs, algebraic, derivative_count, derived_state, derived_derivative, uncertain_state, uncertain_derivative = (0,) * 7
    maximums = [None, None, None, None]
    digest = sha256()
    blocked = bool(reasons)
    for clock in grid:
        digest.update(canonical_json_bytes((clock.numerator, clock.denominator)))
        if blocked:
            continue
        snapshots = tuple(_snapshot(record, clock) for record in full)
        rows = left.layout.differential_count + left.layout.algebraic_count
        for index in range(rows):
            pair = tuple(next(snapshot, None) for snapshot in snapshots)
            if any(value is None for value in pair):
                reasons.add("native-derivative-or-covered-interpolation-block-unavailable")
                break
            (y_a, dy_a, interp_a), (y_b, dy_b, interp_b) = pair
            low, high, disposition = _residual(y_a, y_b, a.atol, a.rtol)
            maximums[0] = low if maximums[0] is None else max(maximums[0], low)
            maximums[1] = high if maximums[1] is None else max(maximums[1], high)
            if index < left.layout.differential_count:
                rhs += 1
            else:
                algebraic += 1
            derived_state += int(interp_a or interp_b)
            if disposition is A.FALSIFIED:
                adverse.add("componentwise-full-state-convergence-budget-missed")
            elif disposition is A.UNEVALUABLE:
                uncertain_state += 1
                reasons.add("full-state-comparison-rounding-enclosure-straddles-budget")
            if dy_a is None or dy_b is None:
                reasons.add("actual-returned-derivative-unavailable")
                continue
            low, high, disposition = _residual(dy_a, dy_b, a.atol / control.derivative_time_scale_s, a.rtol)
            maximums[2] = low if maximums[2] is None else max(maximums[2], low)
            maximums[3] = high if maximums[3] is None else max(maximums[3], high)
            derivative_count += 1
            derived_derivative += int(interp_a or interp_b)
            if disposition is A.FALSIFIED:
                adverse.add("componentwise-returned-derivative-convergence-budget-missed")
            elif disposition is A.UNEVALUABLE:
                uncertain_derivative += 1
                reasons.add("derivative-comparison-rounding-enclosure-straddles-budget")
        if all(value is not None for value in pair) and any(next(snapshot, None) is not None for snapshot in snapshots):
            raise ValueError("full-state comparison omits or changes its complete original row denominator")
    return FullStateIntervalAssessment("assessment.full-state." + left.summary.summary_id + "." + right.summary.summary_id,
        ss.identity(control, "control_id"), ss.identity(a, "config_id"), ss.identity(b, "config_id"),
        ss.identity(left.summary, "summary_id"), ss.identity(right.summary, "summary_id"), left.summary.native_definition, right.summary.native_definition,
        left.summary.native_receipt, right.summary.native_receipt, *checks,
        None if start is None else (start.numerator, start.denominator), None if end is None else (end.numerator, end.denominator),
        None if start is None else _decimal(start, ROUND_FLOOR), None if end is None else _decimal(end, ROUND_CEILING),
        digest.hexdigest(), len(grid), original_counts, integers,
        0 if left.layout is None else left.layout.differential_count, 0 if left.layout is None else left.layout.algebraic_count,
        rhs, algebraic, derivative_count,
        derived_state, derived_derivative, uncertain_state, uncertain_derivative, *maximums,
        A.FALSIFIED if adverse else A.UNEVALUABLE if reasons else A.SATISFIED, tuple(sorted(reasons | adverse)))
