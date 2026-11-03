# SPDX-License-Identifier: MPL-2.0
"""A genuinely changed preparation/continuation method, with complete custody.

The source-derived electrode supplier changes preparation operands. Prospective
segments change each native continuation request. Neither change establishes
the fate of historical uncertain work, numerical fidelity, or qualification.
Dense native arrays remain separate durable payloads; this trace holds their
identities and the complete selected receiver and native-clock census.
"""

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquiryDelivery, CONTROL_RULE, MAX_MODEL_CLOCK, TARGET_CHARGE,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_sha256, validate_stable_id,
)
from . import contracts as c
from . import preparation_contracts as pc
from .source_derived_preparation import SourceRootAssessment, SourceRootPreparation

D = Decimal


def _identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def _nonnegative(value, field):
    validate_decimal(value, field_name=field)
    if value < 0:
        raise ValueError(f"{field} cannot be negative")


@dataclass(frozen=True, slots=True)
class SegmentedMethodProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/method-protocol"
    method_id: str
    maximum_segment_horizon_s: Decimal
    maximum_model_clock_s: Decimal = MAX_MODEL_CLOCK
    receiver_spacing_s: Decimal = D(1)
    target_charge_ah: Decimal = TARGET_CHARGE
    control_rule: str = CONTROL_RULE
    preparation_method: str = "INDEPENDENTLY_ASSESSED_SOURCE_ROOT_ASSIGNMENT;NO_NATIVE_ESOH"
    output_method: str = "ALL_NATIVE_KNOTS;ALL_FULL_RHS_AND_ALGEBRAIC_STATES;ALL_RETURNED_DERIVATIVES"
    continuation_method: str = "COMPLETE_TERMINAL_STATE_AND_INPUTS;GLOBAL_CLOCK;DERIVED_FINAL_TIME_CARRIER_AFTER_RETAINED_TIER_EVENT"
    derivative_claim: str = "RETAIN_IF_RETURNED;NOT_AN_ACCURACY_CLAIM"
    random_state: str = "NONE;DETERMINISTIC_SELECTED_METHOD"
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    fidelity: str = "UNQUALIFIED;INDEPENDENT_SEGMENT_AND_PRECISION_CONTROLS_REQUIRED"

    def __post_init__(self):
        validate_stable_id(self.method_id)
        for name in ("maximum_segment_horizon_s", "maximum_model_clock_s", "receiver_spacing_s", "target_charge_ah"):
            validate_decimal(getattr(self, name), field_name=name)
        if self.maximum_segment_horizon_s not in (D(60), D(30), D(15)):
            raise ValueError("segmentation changes its prospective primary/half/quarter fidelity operands")
        if (self.maximum_model_clock_s, self.receiver_spacing_s, self.target_charge_ah, self.control_rule) != (
                MAX_MODEL_CLOCK, D(1), TARGET_CHARGE, CONTROL_RULE):
            raise ValueError("segmentation cannot thin receivers or change the original scientific target")
        if (self.preparation_method != "INDEPENDENTLY_ASSESSED_SOURCE_ROOT_ASSIGNMENT;NO_NATIVE_ESOH"
                or self.output_method != "ALL_NATIVE_KNOTS;ALL_FULL_RHS_AND_ALGEBRAIC_STATES;ALL_RETURNED_DERIVATIVES"
                or self.continuation_method != "COMPLETE_TERMINAL_STATE_AND_INPUTS;GLOBAL_CLOCK;DERIVED_FINAL_TIME_CARRIER_AFTER_RETAINED_TIER_EVENT"
                or self.derivative_claim != "RETAIN_IF_RETURNED;NOT_AN_ACCURACY_CLAIM"
                or self.random_state != "NONE;DETERMINISTIC_SELECTED_METHOD"
                or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
                or self.fidelity != "UNQUALIFIED;INDEPENDENT_SEGMENT_AND_PRECISION_CONTROLS_REQUIRED"):
            raise ValueError("segmentation substitutes its scientific method or manufactures qualification")


@dataclass(frozen=True, slots=True)
class SegmentedNativeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/native-config"
    config_id: str
    native: c.NativeConfig
    preparation: SourceRootPreparation
    preparation_assessment: SourceRootAssessment
    method: SegmentedMethodProtocol

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.native) is not c.NativeConfig or type(self.preparation) is not SourceRootPreparation
                or type(self.preparation_assessment) is not SourceRootAssessment or type(self.method) is not SegmentedMethodProtocol):
            raise ValueError("segmented config requires complete typed native, supplier and method operands")
        for record in (self.native, self.preparation, self.preparation_assessment, self.method):
            record.__post_init__()
        if (self.preparation.source != c.identity(self.native.source)
                or self.preparation.parameter_source != ("Chen2020" if self.native.model_view.startswith("chen-") else "ORegan2022")
                or self.preparation_assessment.preparation != _identity(self.preparation, "preparation_id")
                or self.preparation_assessment.disposition is not A.SATISFIED):
            raise ValueError("segmented config changes its independently assessed source/stock join")

    @property
    def source(self):
        return self.native.source

    @property
    def model_view(self):
        return self.native.model_view

    @property
    def numerical_view(self):
        return self.native.numerical_view

    @property
    def initial_temperature_k(self):
        return self.native.initial_temperature_k

    @property
    def chamber_temperature_k(self):
        return self.native.chamber_temperature_k

    @property
    def localization_epsilon_k(self):
        return self.native.localization_epsilon_k

    @property
    def rtol(self):
        return self.native.rtol

    @property
    def atol(self):
        return self.native.atol


@dataclass(frozen=True, slots=True)
class ActualSourceAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/actual-source-assignment"
    assignment_id: str
    configuration: ObjectIdentity
    protocol: ObjectIdentity
    supplied_preparation: ObjectIdentity
    assigned_negative_concentration: Decimal
    assigned_positive_concentration: Decimal
    pre_soc_negative_concentration: Decimal
    pre_soc_positive_concentration: Decimal
    binary64_operands: tuple[tuple[str, str], ...]
    observation_kind: str = "OBSERVED_PARAMETER_ASSIGNMENT;SOURCE_ROOTS_REMAIN_DERIVED"
    native_initializer_contacts: int = 0

    def __post_init__(self):
        validate_stable_id(self.assignment_id)
        if (self.configuration.object_schema != SegmentedNativeConfig.SCHEMA or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.supplied_preparation.object_schema != SourceRootPreparation.SCHEMA
                or self.observation_kind != "OBSERVED_PARAMETER_ASSIGNMENT;SOURCE_ROOTS_REMAIN_DERIVED"
                or self.native_initializer_contacts != 0):
            raise ValueError("actual assignment cannot relabel the derived roots or historical native work")
        names = tuple(sorted(("assigned_negative_concentration", "assigned_positive_concentration", "pre_soc_negative_concentration", "pre_soc_positive_concentration")))
        for name in names:
            validate_decimal(getattr(self, name), field_name=name)
        if self.binary64_operands != tuple((name, float(getattr(self, name)).hex()) for name in names):
            raise ValueError("actual source assignment changes its complete binary64 operand census")


@dataclass(frozen=True, slots=True)
class SegmentSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/segment-summary"
    summary_id: str
    configuration: ObjectIdentity
    protocol: ObjectIdentity
    segment_index: int
    regime: str
    requested_start_clock_s: Decimal
    requested_horizon_s: Decimal
    request: ObjectIdentity
    returned: ObjectIdentity
    native_receipt: ObjectIdentity
    disposition: str
    termination: str
    error_type: str | None
    error_message: str | None
    cpu_seconds: Decimal
    wall_seconds: Decimal
    process_peak_rss_bytes: int
    native_times_s: tuple[Decimal, ...]
    start_receivers: tuple[Decimal, ...]
    end_receivers: tuple[Decimal, ...]
    full_state: ObjectIdentity | None
    requested_initial: ObjectIdentity | None
    actual_initial: ObjectIdentity | None
    initial_derivative: ObjectIdentity | None
    actual_terminal: ObjectIdentity | None
    terminal_derivative: ObjectIdentity | None
    native_definition: ObjectIdentity
    raw_return: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.summary_id)
        if (self.configuration.object_schema != SegmentedNativeConfig.SCHEMA or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.request.object_schema != "empirical-lawhood/battery-segmented/native-request"
                or self.returned.object_schema != "empirical-lawhood/battery-segmented/native-return"
                or self.native_receipt.object_schema != "empirical-lawhood/runtime/canonical-task-receipt"
                or self.native_definition.object_schema != "empirical-lawhood/runtime/native-subwork-definition"):
            raise ValueError("segment summary changes its actual request/return/completed receipt joins")
        if type(self.segment_index) is not int or self.segment_index < 1 or self.regime not in {"LOW", "HIGH"}:
            raise ValueError("segment summary loses the actual segment/regime census")
        if (self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
                or (self.disposition == "TECHNICAL_FAILURE") != (self.error_type is not None and self.error_message is not None)):
            raise ValueError("segment summary loses actual failure/return status")
        for name in ("requested_start_clock_s", "requested_horizon_s", "cpu_seconds", "wall_seconds"):
            _nonnegative(getattr(self, name), name)
        if self.requested_horizon_s <= 0 or type(self.process_peak_rss_bytes) is not int or self.process_peak_rss_bytes < 0:
            raise ValueError("segment summary loses its genuine request or measured resource cost")
        for value in (*self.native_times_s, *self.start_receivers, *self.end_receivers):
            validate_decimal(value, field_name="segment_observation")
        allowed_start = (self.requested_start_clock_s, D(str(math.nextafter(float(self.requested_start_clock_s), math.inf))))
        actual_requested_endpoint = D(str(float(self.requested_start_clock_s) + float(self.requested_horizon_s)))
        if self.native_times_s and (self.native_times_s[0] not in allowed_start
                or any(a >= b for a, b in zip(self.native_times_s, self.native_times_s[1:]))
                or self.native_times_s[-1] > actual_requested_endpoint):
            raise ValueError("segment summary omits or resets actual native clocks")
        state_ids = (self.requested_initial, self.actual_initial, self.initial_derivative, self.actual_terminal, self.terminal_derivative)
        if any(row is not None and row.object_schema != pc.StateObservation.SCHEMA for row in state_ids):
            raise ValueError("segment summary substitutes a full-state observation")
        if self.full_state is not None and self.full_state.object_schema != "empirical-lawhood/battery-segmented/full-state-segment":
            raise ValueError("segment summary substitutes its complete native payload")
        if self.raw_return is not None and self.raw_return.object_schema != "empirical-lawhood/battery-segmented/raw-returned-segment":
            raise ValueError("segment summary substitutes its lossless adverse/raw native return")
        if self.disposition == "RETURNED" and (not self.native_times_s or len(self.start_receivers) != 4 or len(self.end_receivers) != 4
                or self.full_state is None or self.raw_return is None or any(row is None for row in state_ids)):
            raise ValueError("returned segment omits its complete payload/boundary denominator")


@dataclass(frozen=True, slots=True)
class SegmentTransition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/hybrid-transition"
    transition_id: str
    transition_index: int
    preceding_segment: int
    following_segment: int
    from_regime: str
    to_regime: str
    root_clock_s: Decimal
    root_threshold_k: Decimal
    localization_epsilon_k: Decimal
    left_terminal: ObjectIdentity
    right_requested: ObjectIdentity | None
    right_initial: ObjectIdentity | None
    left_receivers: tuple[Decimal, ...]
    right_receivers: tuple[Decimal, ...]
    restart_metadata: str = "DERIVED_FINAL_TIME_CARRIER;ORIGINAL_EVENT_RETAINED"

    def __post_init__(self):
        validate_stable_id(self.transition_id)
        if (type(self.transition_index) is not int or self.transition_index < 1
                or type(self.preceding_segment) is not int or self.preceding_segment < 1
                or self.following_segment != self.preceding_segment + 1
                or (self.from_regime, self.to_regime) not in {("LOW", "HIGH"), ("HIGH", "LOW")}
                or self.restart_metadata != "DERIVED_FINAL_TIME_CARRIER;ORIGINAL_EVENT_RETAINED"):
            raise ValueError("segmented tier transition changes its complete derived restart operands")
        for identity in (self.left_terminal, self.right_requested, self.right_initial):
            if identity is not None and identity.object_schema != pc.StateObservation.SCHEMA:
                raise ValueError("segmented transition omits its complete state lineage")
        for value in (self.root_clock_s, self.root_threshold_k, self.localization_epsilon_k, *self.left_receivers, *self.right_receivers):
            validate_decimal(value, field_name="segmented_transition")
        if self.root_clock_s < 0 or self.localization_epsilon_k <= 0 or len(self.left_receivers) != 4 or len(self.right_receivers) not in (0, 4):
            raise ValueError("segmented transition omits its actual clock/root/receiver denominator")
        if (self.right_initial is None) != (not self.right_receivers):
            raise ValueError("segmented transition invents an unobserved right state")


@dataclass(frozen=True, slots=True)
class SegmentedTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/native-trace"
    trace_id: str
    config: SegmentedNativeConfig
    implementation_sha256: str
    disposition: str
    termination: str
    error_type: str | None
    error_message: str | None
    delivery: BatteryInquiryDelivery
    times_s: tuple[Decimal, ...]
    current_a: tuple[Decimal, ...]
    voltage_v: tuple[Decimal, ...]
    capacity_ah: tuple[Decimal, ...]
    mean_temperature_k: tuple[Decimal, ...]
    ambient_temperature_k: tuple[Decimal, ...]
    control_modes: tuple[str, ...]
    temperature_regimes: tuple[str, ...]
    event_names: tuple[str, ...]
    processed_event_expressions: tuple[str, ...]
    segments: tuple[SegmentSummary, ...]
    transitions: tuple[SegmentTransition, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    wall_seconds: Decimal
    cpu_seconds: Decimal
    process_peak_rss_bytes: int
    native_initializer_contacts: int = 0
    initializer_status: str = "NOT_ENTERED;INDEPENDENTLY_ASSESSED_DERIVED_SOURCE_ASSIGNMENT"
    native_output_retention: str = "COMPLETE_NATIVE_ARRAYS_IN_AUTHENTICATED_SEGMENT_PAYLOADS;NO_THINNING"

    def __post_init__(self):
        validate_stable_id(self.trace_id)
        validate_sha256(self.implementation_sha256)
        if type(self.config) is not SegmentedNativeConfig or self.trace_id != "trace." + self.config.config_id:
            raise ValueError("segmented trace substitutes its genuinely changed configuration")
        self.config.__post_init__()
        if (self.disposition not in {"TARGET_REACHED", "SERVICE_TERMINATED", "TECHNICAL_FAILURE"}
                or (self.disposition == "TECHNICAL_FAILURE") != (self.error_type is not None and self.error_message is not None)):
            raise ValueError("segmented trace changes actual terminal/error status")
        columns = (self.current_a, self.voltage_v, self.capacity_ah, self.mean_temperature_k, self.ambient_temperature_k,
                   self.control_modes, self.temperature_regimes)
        if any(len(row) != len(self.times_s) for row in columns):
            raise ValueError("segmented trace loses complete receiver columns")
        for row in (self.times_s, *columns[:5]):
            for value in row:
                validate_decimal(value, field_name="segmented_receiver")
        if self.times_s and (self.times_s[0] != 0 or self.times_s[-1] > self.config.method.maximum_model_clock_s
                or any(a >= b for a, b in zip(self.times_s, self.times_s[1:]))):
            raise ValueError("segmented trace resets or reorders the global clock")
        if (any(mode not in {"CC", "CV", "UNRESOLVED"} for mode in self.control_modes)
                or any(mode not in {"LOW", "HIGH"} for mode in self.temperature_regimes)):
            raise ValueError("segmented trace changes control/regime grammar")
        if type(self.delivery) is not BatteryInquiryDelivery or self.delivery.requested_chamber_k != self.config.chamber_temperature_k:
            raise ValueError("segmented trace substitutes its actual chamber delivery")
        if (len(self.event_names) != len(self.processed_event_expressions) or len(set(self.event_names)) != len(self.event_names)
                or any(not event for event in self.event_names)):
            raise ValueError("segmented trace omits original event expressions")
        if (self.native_provider_attempts != 1 or self.backend_solve_calls != len(self.segments)
                or tuple(row.segment_index for row in self.segments) != tuple(range(1, len(self.segments) + 1))
                or any(type(row) is not SegmentSummary or row.configuration != _identity(self.config, "config_id") for row in self.segments)):
            raise ValueError("segmented trace invents, omits or relabels actual native segments")
        if tuple(row.transition_index for row in self.transitions) != tuple(range(1, len(self.transitions) + 1)):
            raise ValueError("segmented trace loses its complete tier-transition census")
        for transition in self.transitions:
            if type(transition) is not SegmentTransition or transition.preceding_segment > len(self.segments):
                raise ValueError("segmented trace invents an unentered tier root")
            before = self.segments[transition.preceding_segment - 1]
            if (before.regime != transition.from_regime or before.actual_terminal != transition.left_terminal
                    or before.end_receivers != transition.left_receivers or not before.native_times_s
                    or before.native_times_s[-1] != transition.root_clock_s):
                raise ValueError("segmented transition changes its actual left root")
            if transition.following_segment <= len(self.segments):
                after = self.segments[transition.following_segment - 1]
                if (after.regime != transition.to_regime or after.requested_initial != transition.right_requested
                        or transition.right_initial is not None and (after.actual_initial != transition.right_initial or after.start_receivers != transition.right_receivers)):
                    raise ValueError("segmented transition changes its actual right restart")
        for name in ("wall_seconds", "cpu_seconds"):
            _nonnegative(getattr(self, name), name)
        if (type(self.process_peak_rss_bytes) is not int or self.process_peak_rss_bytes < 0 or self.native_initializer_contacts != 0
                or self.initializer_status != "NOT_ENTERED;INDEPENDENTLY_ASSESSED_DERIVED_SOURCE_ASSIGNMENT"
                or self.native_output_retention != "COMPLETE_NATIVE_ARRAYS_IN_AUTHENTICATED_SEGMENT_PAYLOADS;NO_THINNING"):
            raise ValueError("segmented trace manufactures old initializer completion or drops full output")


@dataclass(frozen=True, slots=True)
class SegmentedTraceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/trace-check"
    check_id: str
    trace: ObjectIdentity
    disposition: A
    realized_charge_ah: Decimal | None
    capacity_charge_ah: Decimal | None
    discrepancy_ah: Decimal | None
    completion_time_s: Decimal | None
    reason_codes: tuple[str, ...]
    sampled_envelope_pass: bool
    native_control_checked: bool
    whole_time_certified: bool = False

    def __post_init__(self):
        validate_stable_id(self.check_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.trace.object_schema != SegmentedTrace.SCHEMA or type(self.disposition) is not A or self.whole_time_certified:
            raise ValueError("segmented receiver assessment changes scope or claims continuous certification")
        for name in ("realized_charge_ah", "capacity_charge_ah", "discrepancy_ah", "completion_time_s"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        if self.disposition is not A.SATISFIED and not self.reason_codes:
            raise ValueError("negative or missing segmented receiver evidence requires reasons")

