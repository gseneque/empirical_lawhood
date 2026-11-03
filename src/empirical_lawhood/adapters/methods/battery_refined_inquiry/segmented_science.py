# SPDX-License-Identifier: MPL-2.0
"""Independent assessment of source assignment, full segments and receivers.

This checker never reconstructs a fictitious native SOH result or a historical
trace. Full states/derivatives are inspected one completed segment at a time.
Receipts bind actual payload bytes; authority to enter native work is separate.
"""

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
import json
import math
import struct
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    CONTROL_RULE, INTEGRAL_TOLERANCE, REQUIRED_EVENT_NAMES, TARGET_CHARGE,
    TIER_EVENT, TIER_TEMPERATURE,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from . import preparation_contracts as pc
from . import preparation_science as ps
from . import segmented_contracts as sc
from .source_derived_preparation import assess_source_roots

D = Decimal


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def authenticate_payloads(receipt, records):
    """Require every independently loaded payload in its actual completed receipt."""
    if type(receipt) is not CanonicalTaskReceipt:
        raise ValueError("segment assessment needs an actual canonical producing receipt")
    receipt.__post_init__()
    for record in records:
        record.__post_init__()
        if sum(row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint()
                for row in receipt.output_logical_artifacts) != 1:
            raise ValueError("assessed segment operand differs from actual receipt payload bytes")


def authenticate_request_custody(summary, request, definition, receipt, request_receipt):
    """Join the actual request publisher to the stored consuming definition.

    The ordinary reader obtains original records through authenticated custody.
    A request belongs to the preceding carrier; checking only its scientific
    values would omit this materialization and decision provenance join.
    """
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
    if type(definition) is not NativeSubworkDefinition or type(receipt) is not CanonicalTaskReceipt:
        raise ValueError("segment custody requires the actual stored definition")
    definition.__post_init__()
    receipt.__post_init__()
    authenticate_payloads(request_receipt, (request,))
    matches = tuple(row for row in request_receipt.output_logical_artifacts
        if row.payload_schema == request.SCHEMA and row.content_sha256 == request.fingerprint())
    materializations = tuple(row for row in request_receipt.output_materializations
        if row.logical_artifact_id == matches[0].logical_artifact_id)
    if (definition.identity != summary.native_definition or definition.configuration != request.identity
            or definition.operation_id != "battery.segmented-native.segment"
            or not set(definition.input_materialization_ids).issubset(receipt.input_materialization_ids)
            or identity(receipt, "receipt_id") != summary.native_receipt
            or len(materializations) != 1
            or materializations[0].materialization_id not in definition.input_materialization_ids):
        raise ValueError("segment request publisher/actual definition/input receipt custody disagrees")


@dataclass(frozen=True, slots=True)
class DerivedPreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/preparation-assessment"
    assessment_id: str
    configuration: ObjectIdentity
    protocol: ObjectIdentity
    source_preparation: ObjectIdentity
    source_assessment: ObjectIdentity
    assignment: ObjectIdentity
    layout: ObjectIdentity
    requested_initial: ObjectIdentity
    actual_initial: ObjectIdentity
    disposition: A
    reason_codes: tuple[str, ...]
    checked_differential_components: int
    maximum_scaled_state_residual: Decimal | None
    algebraic_state: str = "COMPLETE_OBSERVED_VALUES_RETAINED;NUMERICAL_CONSISTENCY_AND_FIDELITY_REQUIRE_SEPARATE_ASSESSMENT"
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (self.configuration.object_schema != sc.SegmentedNativeConfig.SCHEMA or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.assignment.object_schema != sc.ActualSourceAssignment.SCHEMA or self.layout.object_schema != pc.ProcessedInitialStateLayout.SCHEMA
                or any(row.object_schema != pc.StateObservation.SCHEMA for row in (self.requested_initial, self.actual_initial))
                or type(self.disposition) is not A or type(self.checked_differential_components) is not int or self.checked_differential_components < 0
                or self.algebraic_state != "COMPLETE_OBSERVED_VALUES_RETAINED;NUMERICAL_CONSISTENCY_AND_FIDELITY_REQUIRE_SEPARATE_ASSESSMENT"
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED" or self.physical_qualification):
            raise ValueError("derived preparation assessment changes scope, denominator or old completion")
        if self.maximum_scaled_state_residual is not None:
            validate_decimal(self.maximum_scaled_state_residual, field_name="maximum_scaled_state_residual")
        if self.disposition is not A.SATISFIED and not self.reason_codes:
            raise ValueError("negative/missing derived preparation needs reasons")


@dataclass(frozen=True, slots=True)
class UnavailableDerivedPreparationAssessment(CanonicalRecord):
    """An actual returned forecast with missing preparation operands.

    Missing identity fields are not filled with placeholders. This separate
    record retains the known producing receipt and the exact missing census.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/unavailable-preparation-assessment"
    assessment_id: str
    configuration: ObjectIdentity
    protocol: ObjectIdentity
    source_preparation: ObjectIdentity
    source_assessment: ObjectIdentity
    native_receipt: ObjectIdentity
    missing_output_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    disposition: A = A.UNEVALUABLE
    checked_differential_components: int = 0
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.missing_output_ids, field_name="missing_output_ids")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        allowed = {"source-assignment", "layout", "requested-initial", "actual-initial"}
        if (self.configuration.object_schema != sc.SegmentedNativeConfig.SCHEMA
                or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.source_preparation.object_schema != "empirical-lawhood/battery-preparation/source-derived-electrodes"
                or self.source_assessment.object_schema != "empirical-lawhood/battery-preparation/source-root-assessment"
                or self.native_receipt.object_schema != CanonicalTaskReceipt.SCHEMA
                or not self.missing_output_ids or not set(self.missing_output_ids).issubset(allowed)
                or not self.reason_codes or self.disposition is not A.UNEVALUABLE
                or self.checked_differential_components != 0
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED" or self.physical_qualification):
            raise ValueError("unavailable preparation cannot invent missing operands or admission")


def assess_derived_preparation(config, protocol, assignment, layout, requested_initial, actual_initial):
    """Direct source falsifier plus actual assignment and pointwise full RHS checks.

    The registered caller authenticates each loaded record against its receipt.
    The DERIVED supplier is checked afresh without rerunning its root producer.
    No initializer disposition is invented or inferred from native state.
    """
    for record, expected in ((config, sc.SegmentedNativeConfig), (protocol, pc.PreparationProtocol),
            (assignment, sc.ActualSourceAssignment), (layout, pc.ProcessedInitialStateLayout),
            (requested_initial, pc.StateObservation), (actual_initial, pc.StateObservation)):
        if type(record) is not expected:
            raise ValueError("derived preparation substitutes its exact typed operands")
        record.__post_init__()
    config_id, protocol_id, layout_id = identity(config, "config_id"), identity(protocol, "protocol_id"), identity(layout, "layout_id")
    source_assessment = assess_source_roots(config.preparation)
    if (source_assessment != config.preparation_assessment or protocol.configuration != config_id
            or protocol.source != config.preparation.source or protocol.parameter_source != config.preparation.parameter_source
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or (protocol.electrode_points, protocol.particle_points) != (config.numerical_view.electrode_points, config.numerical_view.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k or layout.protocol != protocol_id
            or assignment.configuration != config_id or assignment.protocol != protocol_id
            or assignment.supplied_preparation != identity(config.preparation, "preparation_id")
            or any(row.protocol != protocol_id or row.layout != layout_id for row in (requested_initial, actual_initial))):
        raise ValueError("derived preparation changes source, independent assessment, mesh or actual-state joins")
    if not set(ps.PREPARATION_SOURCE_MEMBERS).issubset(protocol.source_members):
        raise ValueError("derived preparation changes independent source pins")
    if (requested_initial.role, actual_initial.role) != ("requested-initial", "actual-initial"):
        raise ValueError("derived preparation changes actual requested/returned roles")
    adverse, missing = set(), set()
    if source_assessment.disposition is not A.SATISFIED:
        adverse.update(source_assessment.reason_codes)
    for name in ("assigned_negative_concentration", "assigned_positive_concentration", "pre_soc_negative_concentration", "pre_soc_positive_concentration"):
        if float(getattr(assignment, name)).hex() != float(getattr(config.preparation, name)).hex():
            adverse.add("actual-parameter-assignment-differs-from-assessed-derived-operands")
    if not layout.observed_from_built_model:
        missing.add("actual-built-model-layout-unobserved")
    layout_reasons = ps._layout_reasons(protocol, layout)
    adverse.update(layout_reasons)
    count, maximum = 0, None
    if any(row.kind is not pc.ObservationKind.OBSERVED for row in (requested_initial, actual_initial)):
        missing.add("actual-full-initial-state-unobserved")
    elif any(row.model_clock_s != 0 for row in (requested_initial, actual_initial)):
        adverse.add("initial-global-clock-not-zero")
    elif any(len(row.scaled_values) != layout.differential_count + layout.algebraic_count for row in (requested_initial, actual_initial)):
        adverse.add("complete-initial-state-denominator-omitted")
    elif not layout_reasons:
        cn, cp, _, _ = ps.source_stock(protocol.parameter_source)
        expected = []
        for block in layout.blocks[:6]:
            if block.role == "electrolyte":
                expected.extend(value for porosity in (D(".25"), D(".47"), D(".335")) for value in (porosity,) * protocol.electrode_points)
            else:
                value = {"discharge-capacity": D(0), "throughput-capacity": D(0),
                    "negative-solid": assignment.assigned_negative_concentration / cn,
                    "positive-solid": assignment.assigned_positive_concentration / cp,
                    "temperature": config.initial_temperature_k / D("298.15")}[block.role]
                expected.extend((value,) * (block.stop - block.start))
        residuals = []
        for requested, actual, target in zip(requested_initial.scaled_values[:layout.differential_count],
                actual_initial.scaled_values[:layout.differential_count], expected, strict=True):
            count += 1
            residuals.extend((abs(requested - target), abs(actual - target), abs(actual - requested)))
            if not ps._close(requested, target, protocol.state_atol, protocol.state_rtol) or not ps._close(actual, target, protocol.state_atol, protocol.state_rtol):
                adverse.add("pointwise-full-derived-initial-state-disagrees")
            if not ps._close(actual, requested, protocol.state_atol, protocol.state_rtol):
                adverse.add("consistent-initialization-changed-initial-differential-state")
        maximum = max(residuals, default=D(0))
    return DerivedPreparationAssessment("assessment.derived." + config.config_id, config_id, protocol_id,
        identity(config.preparation, "preparation_id"), identity(source_assessment, "assessment_id"),
        identity(assignment, "assignment_id"), layout_id, identity(requested_initial, "observation_id"), identity(actual_initial, "observation_id"),
        A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED, tuple(sorted(adverse | missing)), count, maximum)


@dataclass(frozen=True, slots=True)
class SegmentAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/segment-assessment"
    assessment_id: str
    summary: ObjectIdentity
    native_receipt: ObjectIdentity
    disposition: A
    reason_codes: tuple[str, ...]
    full_state_components: int
    retained_native_knots: int
    retained_derivative_components: int
    differential_continuity_components: int
    derivative_claim: str = "EXACT_RETURNED_BITS_RETAINED;NO_ACCURACY_OR_AVAILABILITY_INFERENCE"
    physical_qualification: bool = False
    retained_raw_bytes: int = 0
    retained_raw_arrays: int = 0
    retained_raw_state_elements: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (self.summary.object_schema != sc.SegmentSummary.SCHEMA or self.native_receipt.object_schema != CanonicalTaskReceipt.SCHEMA
                or type(self.disposition) is not A or any(type(value) is not int or value < 0 for value in (
                    self.full_state_components, self.retained_native_knots, self.retained_derivative_components, self.differential_continuity_components,
                    self.retained_raw_bytes, self.retained_raw_arrays, self.retained_raw_state_elements))
                or self.derivative_claim != "EXACT_RETURNED_BITS_RETAINED;NO_ACCURACY_OR_AVAILABILITY_INFERENCE" or self.physical_qualification):
            raise ValueError("segment assessment changes complete payload scope or scientific claims")
        if self.disposition is not A.SATISFIED and not self.reason_codes:
            raise ValueError("negative/missing segment assessment needs reasons")


def _endpoint_bits(block, terminal, derivative=False):
    width = len(block.clock_binary64)
    values = block.derivative_binary64 if derivative else block.state_binary64
    if values is None:
        return None
    offset = width - 1 if terminal else 0
    return tuple(values[row * width + offset] for row in range(block.state_rows))


def _primitive_identity(record, name):
    bound = identity(record, name)
    return {"id": bound.object_id, "schema": bound.object_schema, "version": bound.object_version, "fingerprint": bound.object_fingerprint}


def _raw_counts(raw):
    if raw is None:
        return 0, 0, 0
    arrays = tuple(array for rows in (raw.clock_blocks, raw.state_blocks, raw.derivative_blocks) for array in rows or ())
    return (sum(len(array.bytes_hex) // 2 for array in arrays), len(arrays),
        sum(math.prod(array.shape) for array in raw.state_blocks or ()))


def _raw_bits(array, shape):
    if array.shape != shape or array.dtype not in {"<f8", ">f8"} or array.itemsize != 8 or array.order != "C":
        return None
    order = "<" if array.dtype == "<f8" else ">"
    values = tuple(value[0] for value in struct.iter_unpack(order + "d", bytes.fromhex(array.bytes_hex)))
    if any(not math.isfinite(value) for value in values):
        return None
    return tuple(value.hex() for value in values)


def _raw_reasons(raw, full):
    """Interpret every original byte independently, including shape/dtype joins."""
    reasons = set()
    if (raw.clock_blocks is None or raw.state_blocks is None or len(raw.clock_blocks) != len(full.blocks)
            or len(raw.state_blocks) != len(full.blocks) or not {"all_ts", "all_ys"}.issubset(raw.present_attributes)):
        return {"complete-raw-native-array-denominator-disagrees"}
    derivative_rows = raw.derivative_blocks
    if derivative_rows is not None and derivative_rows and len(derivative_rows) != len(full.blocks):
        return {"complete-raw-derivative-array-denominator-disagrees"}
    for index, (clock, state, block) in enumerate(zip(raw.clock_blocks, raw.state_blocks, full.blocks, strict=True)):
        shape = (block.state_rows, len(block.clock_binary64))
        if (_raw_bits(clock, (shape[1],)) != block.clock_binary64 or _raw_bits(state, shape) != block.state_binary64):
            reasons.add("raw-native-bits-shape-or-dtype-do-not-match-typed-interpretation")
        actual_derivative = None if not derivative_rows else _raw_bits(derivative_rows[index], shape)
        if actual_derivative != block.derivative_binary64 or derivative_rows and actual_derivative is None:
            reasons.add("raw-native-derivative-bits-or-availability-do-not-match-interpretation")
    return reasons


def _request_reasons(config, layout, summary, request, full_state, previous_terminal):
    """Check actual primitive operands directly, without calling the producer."""
    request_document = json.loads(request.primitive_json)
    bit = lambda value: {"binary64": float(value).hex()}
    expected_inputs = {"Inquiry active charging magnitude [A]": bit(D("1.455") if summary.regime == "LOW" else D("3.395")),
        "Inquiry tier threshold [K]": bit(TIER_TEMPERATURE + config.localization_epsilon_k / (D(1) if summary.regime == "LOW" else D(2))),
        "Inquiry tier direction": bit(D(-1) if summary.regime == "LOW" else D(1))}
    required = {"regime": summary.regime, "requested_start": bit(summary.requested_start_clock_s),
        "duration": bit(summary.requested_horizon_s), "source_computed_end": bit(float(summary.requested_start_clock_s) + float(summary.requested_horizon_s)),
        "inputs": expected_inputs, "model_expression_sha256": layout.model_expression_sha256,
        "initial_conditions_sha256": layout.initial_conditions_sha256, "method": _primitive_identity(config.method, "method_id"),
        "previous_terminal": None if previous_terminal is None else _primitive_identity(previous_terminal, "observation_id"),
        "continuation_metadata": "NONE" if previous_terminal is None else config.method.continuation_method,
        "save": False, "initial_soc_argument": None}
    reasons = set()
    if any(request_document.get(name) != value for name, value in required.items()):
        reasons.add("actual-native-request-changes-scientific-primitive-operands")
    solver = request_document.get("solver", {})
    if not isinstance(solver, dict) or solver.get("type") != "IDAKLUSolver" or solver.get("rtol") != bit(config.rtol) or solver.get("atol") != bit(config.atol):
        reasons.add("actual-native-solver-type-or-tolerances-disagree")
    returned_inputs = json.loads(full_state.returned_inputs_json)
    def same_inputs(row):
        if not isinstance(row, dict) or row.keys() != expected_inputs.keys():
            return False
        for name, expected in expected_inputs.items():
            observed = row[name]
            if observed != expected and observed not in (
                    {"shape": [1], "binary64": [expected["binary64"]]},
                    {"shape": [], "binary64": [expected["binary64"]]}):
                return False
        return True
    if not isinstance(returned_inputs, list) or not returned_inputs or any(not same_inputs(row) for row in returned_inputs):
        reasons.add("actual-native-returned-inputs-disagree-with-frozen-regime")
    return reasons


def assess_segment(config, protocol, layout, summary, receipt, *, request, returned, full_state, raw_return,
                   requested_initial, actual_initial, initial_derivative, actual_terminal, terminal_derivative,
                   previous_terminal=None):
    """Independently check one actual completed payload and exact continuation.

    At most this full payload and two terminal vectors are needed. Derivative
    absence remains explicit. Complete arrays are never collapsed to averages.
    """
    from .segmented_native import FullStateSegment, RawReturnedSegment, SegmentRequest, SegmentReturn
    if type(summary) is sc.SegmentSummary and summary.disposition == "TECHNICAL_FAILURE":
        return assess_failed_segment(config, protocol, summary, receipt, request=request, returned=returned,
            full_state=full_state, raw_return=raw_return, requested_initial=requested_initial, actual_initial=actual_initial,
            initial_derivative=initial_derivative, actual_terminal=actual_terminal, terminal_derivative=terminal_derivative)
    if (type(summary) is not sc.SegmentSummary or type(full_state) is not FullStateSegment or type(raw_return) is not RawReturnedSegment
            or type(request) is not SegmentRequest or type(returned) is not SegmentReturn):
        raise ValueError("segment assessment substitutes its actual payload/request/return types")
    records = (request, returned, full_state, requested_initial, actual_initial, initial_derivative, actual_terminal, terminal_derivative)
    # Request itself is published by the still-live previous carrier, rather
    # than its consuming child receipt. Its authenticated identity is frozen in
    # the child definition/input manifest by AR3; all returned outputs are here.
    authenticate_payloads(receipt, (*records[1:], raw_return))
    for record in (config, protocol, layout, summary, *records):
        record.__post_init__()
    protocol_id, layout_id = identity(protocol, "protocol_id"), identity(layout, "layout_id")
    if (summary.configuration != identity(config, "config_id") or protocol.configuration != summary.configuration
            or summary.protocol != protocol_id or layout.protocol != protocol_id or summary.request != request.identity
            or summary.returned != identity(returned, "return_id") or returned.request != request.identity
            or summary.native_receipt != identity(receipt, "receipt_id") or request.configuration != summary.configuration
            or request.protocol != protocol_id or request.ordinal != summary.segment_index or request.kind != "charging"
            or full_state.protocol != protocol_id or full_state.layout != layout_id or full_state.request != request.identity
            or full_state.returned != summary.returned or summary.full_state != identity(full_state, "segment_id")
            or summary.raw_return != identity(raw_return, "raw_id") or full_state.raw_return != summary.raw_return
            or raw_return.protocol != protocol_id or raw_return.request != request.identity or raw_return.returned != summary.returned
            or any(row.protocol != protocol_id or row.layout != layout_id for row in records[3:])):
        raise ValueError("segment assessment changes actual configuration/source/receipt/state joins")
    state_fields = ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")
    if any(getattr(summary, field) != identity(row, "observation_id") for field, row in zip(state_fields, records[3:], strict=True)):
        raise ValueError("segment summary substitutes its actual complete boundary identities")
    if tuple(row.role for row in records[3:]) != ("requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative"):
        raise ValueError("segment assessment changes observed boundary roles")
    adverse, missing = set(), set()
    adverse.update(_raw_reasons(raw_return, full_state))
    adverse.update(_request_reasons(config, layout, summary, request, full_state, previous_terminal))
    if summary.disposition != "RETURNED" or returned.disposition != "RETURNED" or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        missing.add("actual-native-segment-successful-return-unavailable")
    expected_horizon = min(config.method.maximum_segment_horizon_s, config.method.maximum_model_clock_s - summary.requested_start_clock_s)
    if summary.requested_horizon_s != expected_horizon:
        adverse.add("segment-request-changed-prospective-scientific-horizon")
    clocks = tuple(D(str(float.fromhex(value))) for block in full_state.blocks for value in block.clock_binary64)
    if clocks != summary.native_times_s or full_state.actual_termination != summary.termination:
        adverse.add("complete-native-clock-or-termination-denominator-disagrees")
    if not clocks or clocks[-1] > config.method.maximum_model_clock_s:
        adverse.add("native-segment-exceeds-global-scientific-clock")
    endpoint = D(str(float(summary.requested_start_clock_s) + float(summary.requested_horizon_s)))
    if summary.termination == "final time" and (not clocks or clocks[-1] != endpoint):
        adverse.add("final-time-return-misses-exact-source-binary64-endpoint")
    if any(block.state_rows != layout.differential_count + layout.algebraic_count for block in full_state.blocks):
        adverse.add("complete-native-state-row-denominator-disagrees")
    if any(digest != layout.model_expression_sha256 for digest in full_state.returned_model_expression_sha256):
        adverse.add("actual-returned-native-model-differs-from-observed-layout")
    derivative_count = sum(len(block.derivative_binary64 or ()) for block in full_state.blocks)
    for state, block, terminal, derivative in ((actual_initial, full_state.blocks[0], False, False),
            (actual_terminal, full_state.blocks[-1], True, False), (initial_derivative, full_state.blocks[0], False, True),
            (terminal_derivative, full_state.blocks[-1], True, True)):
        bits = _endpoint_bits(block, terminal, derivative)
        if bits is None:
            if state.kind is not pc.ObservationKind.UNAVAILABLE:
                adverse.add("absent-native-derivative-was-invented")
        elif (state.kind is not pc.ObservationKind.OBSERVED or state.binary64_hex != bits
                or state.model_clock_s != D(str(float.fromhex(block.clock_binary64[-1 if terminal else 0])))):
            adverse.add("native-full-array-boundary-or-derivative-bits-disagree")
    continuity_count = 0
    if requested_initial.kind is not pc.ObservationKind.OBSERVED:
        missing.add("actual-requested-full-initial-state-unobserved")
    elif requested_initial.model_clock_s not in (summary.requested_start_clock_s,
            D(str(math.nextafter(float(summary.requested_start_clock_s), math.inf)))):
        adverse.add("requested-full-state-global-clock-disagrees")
    if previous_terminal is not None:
        previous_terminal.__post_init__()
        if (previous_terminal.kind is not pc.ObservationKind.OBSERVED or previous_terminal.role != "actual-terminal"
                or previous_terminal.layout != layout_id or previous_terminal.protocol != protocol_id):
            raise ValueError("segment continuity substitutes its previous full terminal state")
        if (previous_terminal.model_clock_s != summary.requested_start_clock_s
                or requested_initial.binary64_hex != previous_terminal.binary64_hex):
            adverse.add("derived-continuation-changes-complete-terminal-state-or-clock")
        if len(actual_initial.scaled_values) != layout.differential_count + layout.algebraic_count:
            adverse.add("actual-reinitialized-full-state-denominator-omitted")
        else:
            continuity_count = layout.differential_count
            if any(not ps._close(left, right, config.atol, config.rtol) for left, right in zip(
                    previous_terminal.scaled_values[:layout.differential_count], actual_initial.scaled_values[:layout.differential_count], strict=True)):
                adverse.add("native-consistent-initialization-changes-differential-continuation")
    elif summary.segment_index != 1:
        missing.add("previous-complete-terminal-state-unavailable")
    return SegmentAssessment("assessment." + summary.summary_id, identity(summary, "summary_id"), summary.native_receipt,
        A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED, tuple(sorted(adverse | missing)),
        sum(len(block.state_binary64) for block in full_state.blocks), sum(len(block.clock_binary64) for block in full_state.blocks),
        derivative_count, continuity_count, retained_raw_bytes=_raw_counts(raw_return)[0],
        retained_raw_arrays=_raw_counts(raw_return)[1], retained_raw_state_elements=_raw_counts(raw_return)[2])


def assess_failed_segment(config, protocol, summary, receipt, *, request, returned, full_state=None, raw_return=None,
                          requested_initial=None, actual_initial=None, initial_derivative=None,
                          actual_terminal=None, terminal_derivative=None):
    """Known return/entered call with missing extraction remains UNEVALUABLE.

    A RETURNED native witness and a failed scientific extraction can coexist.
    Retain actual available payloads and the complete one-call denominator;
    never replace absent state/derivative arrays with zero or successful claims.
    """
    from .segmented_native import FullStateSegment, RawReturnedSegment, SegmentRequest, SegmentReturn
    if (type(config) is not sc.SegmentedNativeConfig or type(protocol) is not pc.PreparationProtocol
            or type(summary) is not sc.SegmentSummary or type(request) is not SegmentRequest or type(returned) is not SegmentReturn
            or summary.disposition != "TECHNICAL_FAILURE"):
        raise ValueError("adverse segment assessment changes actual typed failure operands")
    retained = tuple(row for row in (returned, full_state, raw_return, requested_initial, actual_initial, initial_derivative, actual_terminal, terminal_derivative) if row is not None)
    authenticate_payloads(receipt, retained)
    for record in (config, protocol, summary, request):
        record.__post_init__()
    if (summary.configuration != identity(config, "config_id") or protocol.configuration != summary.configuration
            or summary.protocol != identity(protocol, "protocol_id") or summary.request != request.identity
            or request.configuration != summary.configuration or request.ordinal != summary.segment_index
            or request.protocol != summary.protocol or summary.returned != identity(returned, "return_id")
            or returned.request != request.identity or summary.native_receipt != identity(receipt, "receipt_id")
            or receipt.operational_status is OperationalStatus.SUCCEEDED):
        raise ValueError("adverse segment changes exact actual return/completed failure receipt")
    state_rows = (requested_initial, actual_initial, initial_derivative, actual_terminal, terminal_derivative)
    for field, row in zip(("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"), state_rows, strict=True):
        if ((row is None) != (getattr(summary, field) is None)
                or row is not None and (type(row) is not pc.StateObservation or identity(row, "observation_id") != getattr(summary, field))):
            raise ValueError("adverse segment invents an unreturned full-state boundary")
    if full_state is not None:
        if type(full_state) is not FullStateSegment or identity(full_state, "segment_id") != summary.full_state:
            raise ValueError("adverse segment changes its retained native payload")
    elif summary.full_state is not None:
        raise ValueError("adverse segment hides a declared actual full-state payload")
    if raw_return is not None:
        if (type(raw_return) is not RawReturnedSegment or identity(raw_return, "raw_id") != summary.raw_return
                or raw_return.protocol != summary.protocol or raw_return.request != request.identity or raw_return.returned != summary.returned):
            raise ValueError("adverse segment substitutes its lossless raw native return")
    elif summary.raw_return is not None:
        raise ValueError("adverse segment hides a declared lossless raw native return")
    reasons = {"actual-segment-technical-failure"}
    if full_state is None:
        reasons.add("actual-full-native-payload-unavailable")
    if returned.disposition == "RETURNED" and raw_return is None:
        reasons.add("actual-returned-raw-array-custody-unavailable")
    if any(row is None for row in state_rows):
        reasons.add("complete-requested-and-returned-boundary-denominator-unavailable")
    return SegmentAssessment("assessment." + summary.summary_id, identity(summary, "summary_id"), summary.native_receipt,
        A.UNEVALUABLE, tuple(sorted(reasons)), 0 if full_state is None else sum(len(block.state_binary64) for block in full_state.blocks),
        0 if full_state is None else sum(len(block.clock_binary64) for block in full_state.blocks),
        0 if full_state is None else sum(len(block.derivative_binary64 or ()) for block in full_state.blocks), 0,
        retained_raw_bytes=_raw_counts(raw_return)[0], retained_raw_arrays=_raw_counts(raw_return)[1], retained_raw_state_elements=_raw_counts(raw_return)[2])


def check_receivers(trace, preparation, segment_assessments):
    """Unchanged independent integral, envelope and target tests on new schema."""
    if type(trace) is not sc.SegmentedTrace or type(preparation) not in (DerivedPreparationAssessment, UnavailableDerivedPreparationAssessment):
        raise ValueError("segmented receiver assessment requires actual successor operands")
    trace.__post_init__()
    preparation.__post_init__()
    if preparation.configuration != identity(trace.config, "config_id"):
        raise ValueError("receiver assessment substitutes its independent preparation")
    if (len(segment_assessments) != len(trace.segments) or any(type(row) is not SegmentAssessment for row in segment_assessments)
            or any(row.summary != identity(summary, "summary_id") for row, summary in zip(segment_assessments, trace.segments, strict=True))):
        raise ValueError("receiver assessment omits actual complete segment assessment census")
    adverse, missing = set(), set()
    realized = capacity = discrepancy = completion = None
    envelope = controlled = False
    if preparation.disposition is not A.SATISFIED or any(row.disposition is not A.SATISFIED for row in segment_assessments):
        missing.add("complete-independent-preparation-or-segment-assessment-unresolved")
    if trace.disposition == "TECHNICAL_FAILURE":
        missing.add("native-technical-failure")
    if not trace.times_s:
        missing.add("native-receivers-absent")
    else:
        if trace.capacity_ah[0] != 0:
            adverse.add("initial-capacity-origin-nonzero")
        if abs(trace.mean_temperature_k[0] - trace.config.initial_temperature_k) > D(".01"):
            adverse.add("initial-temperature-disagrees")
        realized = -sum(((a + b) * (end - start) / D(7200) for start, end, a, b in zip(
            trace.times_s, trace.times_s[1:], trace.current_a, trace.current_a[1:])), D(0))
        capacity = -(trace.capacity_ah[-1] - trace.capacity_ah[0])
        discrepancy = abs(realized - capacity)
        if discrepancy > INTEGRAL_TOLERANCE:
            missing.add("independent-current-capacity-disagreement")
        retained = frozenset(trace.times_s)
        if (any(D(second) not in retained for second in range(int(trace.times_s[-1]) + 1))
                or any(clock not in retained for segment in trace.segments for clock in segment.native_times_s)):
            adverse.add("complete-native-knot-or-one-second-receiver-grid-thinned")
        envelope = (all(D("2.499") <= value <= D("4.201") for value in trace.voltage_v)
            and all(D("273.14") <= value <= D("318.16") for value in trace.mean_temperature_k)
            and all(-(D("3.395") if temperature > TIER_TEMPERATURE else D("1.455")) - D("1e-6") <= current <= D("1e-6")
                for current, temperature in zip(trace.current_a, trace.mean_temperature_k, strict=True)))
        if not envelope:
            adverse.add("sampled-source-envelope-violation")
        delivery = trace.delivery
        delivery_present = (delivery.requested_rule == CONTROL_RULE and delivery.accepted_voltage_v == D("4.2")
            and delivery.accepted_chamber_k == trace.config.chamber_temperature_k and delivery.applied_model_clock_s == 0
            and delivery.applied_current_a == trace.current_a[0] and delivery.applied_voltage_v == trace.voltage_v[0]
            and delivery.applied_chamber_k == trace.ambient_temperature_k[0]
            and all(value == trace.config.chamber_temperature_k for value in trace.ambient_temperature_k)
            and all((delivery.accepted_control_expression, delivery.applied_control_expression, delivery.applied_current_expression,
                delivery.applied_voltage_expression, delivery.applied_chamber_expression))
            and set(REQUIRED_EVENT_NAMES).issubset(trace.event_names) and all(trace.processed_event_expressions))
        controlled = delivery_present and bool(trace.segments) and all(
            abs(min(D("4.2") - voltage, current + (D("1.455") if regime == "LOW" else D("3.395")))) <= D(".001")
            and (temperature > TIER_TEMPERATURE if regime == "HIGH" else temperature <= TIER_TEMPERATURE + trace.config.localization_epsilon_k * D("1.000001"))
            for current, voltage, temperature, regime in zip(trace.current_a, trace.voltage_v, trace.mean_temperature_k, trace.temperature_regimes, strict=True))
        if not delivery_present:
            missing.add("native-control-or-chamber-delivery-unresolved")
        elif not controlled:
            adverse.add("native-control-law-violated")
        for segment in trace.segments:
            for clock, receiver in ((segment.native_times_s[0], segment.start_receivers), (segment.native_times_s[-1], segment.end_receivers)) if segment.native_times_s else ():
                index = bisect_right(trace.times_s, clock) - 1
                if (index < 0 or trace.times_s[index] != clock or trace.temperature_regimes[index] != segment.regime
                        or tuple(column[index] for column in (trace.current_a, trace.voltage_v, trace.mean_temperature_k, trace.capacity_ah)) != receiver):
                    adverse.add("actual-native-boundary-receivers-or-regime-substituted")
        tier_segments = tuple(segment for segment in trace.segments[:-1] if TIER_EVENT in segment.termination)
        if len(trace.transitions) != len(tier_segments):
            missing.add("complete-tier-event-restart-census-unresolved")
        for transition in trace.transitions:
            expected = TIER_TEMPERATURE + trace.config.localization_epsilon_k / (D(1) if transition.from_regime == "LOW" else D(2))
            if (transition.root_threshold_k != expected or abs(transition.left_receivers[2] - expected) > trace.config.localization_epsilon_k / D("1000000")
                    or transition.right_requested is None or transition.right_initial is None):
                missing.add("actual-tier-root-or-complete-restart-unresolved")
        if trace.disposition != "TARGET_REACHED" or capacity < TARGET_CHARGE - INTEGRAL_TOLERANCE or realized < TARGET_CHARGE - INTEGRAL_TOLERANCE:
            adverse.add("operational-soc80-target-not-delivered")
        else:
            completion = trace.times_s[-1]
    return sc.SegmentedTraceCheck("check." + trace.trace_id, identity(trace, "trace_id"),
        A.FALSIFIED if adverse else A.UNEVALUABLE if missing else A.SATISFIED,
        realized, capacity, discrepancy, completion, tuple(sorted(adverse | missing)), envelope, controlled)

