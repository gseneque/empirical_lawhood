"""Immutable operands and complete results for the bounded numerical RC chain.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_EVEN, localcontext
from functools import wraps
from typing import Callable, ClassVar, ParamSpec, TypeVar

from empirical_lawhood.adapters.simulators.rc_ladder_response.contracts import (
    ResistorCapacitorLadderModelConfig,
    ResistorCapacitorLadderNativePanel,
    ResistorCapacitorLadderNumericalCheck,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
)

VARIANT_IDS = (
    "adequate", "biased", "coarsened", "late", "missing", "physical-stop",
    "resource-conflict", "wrong-binding", "wrong-receiver", "wrong-units",
)
ARM_IDS = ("insufficient", "selected", "unchanged", "wrong")
CLAIM_IDS = ("rc-j", "rc-m", "rc-p")
OUTCOME_STATES = ("FAILED", "PASSED", "REFUSED", "UNEVALUABLE", "UNSUPPORTED")
EVIDENCE_ROLE = "EXPOSED_NUMERICAL_DEVELOPMENT_NONPROMOTABLE"
UNSUPPORTED_PREREQUISITES = (
    "AUTHENTIC_COMPONENT_METROLOGY", "AUTHENTIC_PHYSICAL_SENSOR_CALIBRATION",
    "FRESH_PHYSICAL_PREPARATIONS", "PHYSICAL_STATE_MEASUREMENT",
    "REAL_ISSUE_EXECUTION_REVEAL_AUTHORITY", "SCIENTIFIC_QUALIFICATION",
)

_Args = ParamSpec("_Args")
_Return = TypeVar("_Return")


def _arithmetic_context() -> Context:
    return Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
        capitals=1, clamp=0, flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])


def fixed_decimal_context(function: Callable[_Args, _Return]) -> Callable[_Args, _Return]:
    """Keep this numerical protocol independent of a caller's decimal context."""
    @wraps(function)
    def evaluate(*args: _Args.args, **kwargs: _Args.kwargs) -> _Return:
        with localcontext(_arithmetic_context()):
            return function(*args, **kwargs)
    return evaluate


def decay_factor(rate: Decimal, duration: Decimal) -> Decimal:
    """Declared scalar relation evaluated in a fixed decimal context."""
    with localcontext(_arithmetic_context()):
        return (-rate * duration).exp()


def _reasons(values: tuple[str, ...]) -> None:
    if tuple(sorted(set(values))) != values:
        raise ValueError("RC reason codes must be sorted and unique")


def _state(value: str) -> None:
    if value not in OUTCOME_STATES:
        raise ValueError("RC result has an unknown terminal state")


@dataclass(frozen=True, slots=True)
class RCChainProtocol(CanonicalRecord):
    """Frozen scientific rule and resource bounds, with no unit state truths."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/protocol"

    protocol_id: str
    capacitance_farads: Decimal
    left_source_resistance_ohms: Decimal
    right_source_resistance_ohms: Decimal
    receiver_id: str
    quantity_id: str
    voltage_unit: str
    sample_seconds: Decimal
    available_seconds: Decimal
    decision_seconds: Decimal
    observation_error_volts: Decimal
    observation_radius_volts: Decimal
    maximum_observation_radius_volts: Decimal
    coarsened_radius_volts: Decimal
    biased_error_volts: Decimal
    late_available_seconds: Decimal
    preparation_durations_seconds: tuple[Decimal, ...]
    support_lower_volts: Decimal
    support_upper_volts: Decimal
    support_guard_volts: Decimal
    response_left_voltage_volts: Decimal
    response_right_voltage_volts: Decimal
    response_horizon_seconds: Decimal
    prediction_initial_voltage_volts: Decimal
    response_coefficient_a: Decimal
    response_coefficient_b_volts: Decimal
    maximum_task_error_volts: Decimal
    completion_deadline_seconds: Decimal
    conflict_deadline_seconds: Decimal
    output_step_seconds: Decimal
    backward_euler_maximum_step_seconds: Decimal
    maximum_view_defect_volts: Decimal
    maximum_charge_rate_defect_amperes: Decimal
    maximum_analytic_defect_volts: Decimal
    maximum_analytic_current_defect_amperes: Decimal
    maximum_elapsed_seconds: Decimal
    maximum_native_steps: int
    maximum_output_bytes: int
    maximum_aggregate_output_bytes: int
    minimum_free_bytes: int

    @fixed_decimal_context
    def __post_init__(self) -> None:
        validate_stable_id(self.protocol_id, field_name="protocol_id")
        if (self.receiver_id, self.quantity_id, self.voltage_unit) != (
            "capacitor-node-0", "capacitor-node-voltage", "V"
        ):
            raise ValueError("RC chain requires its complete one-cell voltage receiver in V")
        positive = (
            "capacitance_farads", "left_source_resistance_ohms", "right_source_resistance_ohms",
            "observation_radius_volts", "maximum_observation_radius_volts", "coarsened_radius_volts",
            "support_guard_volts", "response_horizon_seconds", "maximum_task_error_volts",
            "completion_deadline_seconds", "conflict_deadline_seconds", "output_step_seconds",
            "backward_euler_maximum_step_seconds", "maximum_view_defect_volts",
            "maximum_charge_rate_defect_amperes", "maximum_analytic_defect_volts", "maximum_analytic_current_defect_amperes",
            "maximum_elapsed_seconds",
        )
        for name, field in self.__dataclass_fields__.items():
            value = getattr(self, name)
            if field.type in {"Decimal", Decimal}:
                validate_decimal(value, field_name=name)
                if name in positive and value <= 0:
                    raise ValueError(f"RC {name} must be positive")
        if self.sample_seconds != 0 or self.decision_seconds <= 0 or not 0 <= self.available_seconds <= self.decision_seconds:
            raise ValueError("RC sample starts at zero and nominal information precedes the decision")
        if self.late_available_seconds <= self.decision_seconds:
            raise ValueError("RC late control must be unavailable at the decision cutoff")
        if (not self.preparation_durations_seconds
            or len(self.preparation_durations_seconds) > 16
            or self.preparation_durations_seconds[0] != 0
            or tuple(sorted(set(self.preparation_durations_seconds))) != self.preparation_durations_seconds):
            raise ValueError("RC preparation menu must be bounded, sorted, unique and begin at zero")
        for duration in self.preparation_durations_seconds:
            validate_decimal(duration, field_name="preparation_duration", minimum=Decimal(0))
        if (self.observation_radius_volts > self.maximum_observation_radius_volts
            or self.coarsened_radius_volts <= self.maximum_observation_radius_volts):
            raise ValueError("RC observation controls must straddle the consumer uncertainty bound")
        if self.support_lower_volts >= 0 or self.support_upper_volts <= 0:
            raise ValueError("RC discharge support must contain zero in its interior")
        if self.support_guard_volts >= min(-self.support_lower_volts, self.support_upper_volts):
            raise ValueError("RC support arithmetic guard consumes the entire support")
        if not self.support_lower_volts <= self.prediction_initial_voltage_volts <= self.support_upper_volts:
            raise ValueError("RC frozen predictor state is outside its own support")
        horizon = self.decision_seconds + self.preparation_durations_seconds[-1] + self.response_horizon_seconds
        if horizon > 16 or self.output_step_seconds > self.response_horizon_seconds:
            raise ValueError("RC chain horizon or output grid exceeds its bounded development contract")
        if self.backward_euler_maximum_step_seconds > self.output_step_seconds:
            raise ValueError("RC Euler step exceeds its output grid")
        if self.conflict_deadline_seconds >= self.completion_deadline_seconds:
            raise ValueError("RC conflict control requires a stricter completion deadline")
        for name, ceiling in (("maximum_native_steps", 10_000_000), ("maximum_output_bytes", 64 * 1024**2),
                              ("maximum_aggregate_output_bytes", 1024**3),
                              ("minimum_free_bytes", 1024**3)):
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= ceiling:
                raise ValueError(f"RC {name} exceeds its bounded work contract")
        if self.maximum_elapsed_seconds > 3600:
            raise ValueError("RC elapsed work bound exceeds one hour")
        a = decay_factor(self.decay_rate_per_second, self.response_horizon_seconds)
        b = self.response_equilibrium_volts * (1 - a)
        coefficient_defect = abs(self.response_coefficient_a - a) * max(abs(self.support_lower_volts), abs(self.support_upper_volts))
        coefficient_defect += abs(self.response_coefficient_b_volts - b)
        if coefficient_defect > self.support_guard_volts:
            raise ValueError("RC frozen coefficients disagree with the declared circuit and action")

    @property
    @fixed_decimal_context
    def decay_rate_per_second(self) -> Decimal:
        return (1 / self.left_source_resistance_ohms + 1 / self.right_source_resistance_ohms) / self.capacitance_farads

    @property
    @fixed_decimal_context
    def response_equilibrium_volts(self) -> Decimal:
        return (self.response_left_voltage_volts / self.left_source_resistance_ohms
                + self.response_right_voltage_volts / self.right_source_resistance_ohms) / (
                    1 / self.left_source_resistance_ohms + 1 / self.right_source_resistance_ohms)

    @property
    @fixed_decimal_context
    def predicted_endpoint_volts(self) -> Decimal:
        return self.response_coefficient_a * self.prediction_initial_voltage_volts + self.response_coefficient_b_volts


@dataclass(frozen=True, slots=True)
class RCChainUnit(CanonicalRecord):
    """One exposed numerical model preparation; its controls remain nested."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/unit"
    unit_id: str
    initial_voltage_volts: Decimal

    def __post_init__(self) -> None:
        validate_stable_id(self.unit_id, field_name="unit_id")
        validate_decimal(self.initial_voltage_volts, field_name="initial_voltage_volts")
        if abs(self.initial_voltage_volts) > 100:
            raise ValueError("RC development initial voltage exceeds its declared bounded domain")


@dataclass(frozen=True, slots=True)
class RCPrerequisiteChainConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/config"
    config_id: str
    protocol: RCChainProtocol
    units: tuple[RCChainUnit, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        require_sorted_unique_ids(self.units, attribute="unit_id", field_name="units")
        if not 1 <= len(self.units) <= 32:
            raise ValueError("RC chain requires a bounded complete unit roster")
        if len(set(unit.initial_voltage_volts for unit in self.units)) != len(self.units):
            raise ValueError("RC relabelled deterministic initial states do not supply new model preparations")


@dataclass(frozen=True, slots=True)
class RCChainObservationExpectation(CanonicalRecord):
    """Opaque source bindings and consumer requirements; no oracle state."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/observation-expectation"
    unit_id: str
    config_sha256: str
    model_sha256: str
    source_sha256: str
    source_binding_sha256: str
    receiver_id: str
    quantity_id: str
    voltage_unit: str
    sample_seconds: Decimal
    decision_seconds: Decimal
    maximum_radius_volts: Decimal

    def __post_init__(self) -> None:
        validate_stable_id(self.unit_id, field_name="unit_id")
        for name in ("config_sha256", "model_sha256", "source_sha256", "source_binding_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        for name in ("sample_seconds", "decision_seconds", "maximum_radius_volts"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class RCChainObservation(CanonicalRecord):
    """An exposed observer output, with declared source binding and uncertainty."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/observation"
    observation_id: str
    unit_id: str
    config_sha256: str
    model_sha256: str
    source_sha256: str
    source_binding_sha256: str
    receiver_id: str
    quantity_id: str
    voltage_unit: str
    sample_seconds: Decimal
    available_seconds: Decimal
    reported_voltage_volts: Decimal
    radius_volts: Decimal

    def __post_init__(self) -> None:
        for name in ("observation_id", "unit_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        for name in ("config_sha256", "model_sha256", "source_sha256", "source_binding_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        for name in ("sample_seconds", "available_seconds", "radius_volts"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        validate_decimal(self.reported_voltage_volts, field_name="reported_voltage_volts")


@dataclass(frozen=True, slots=True)
class RCChainDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/decision"
    observation_sha256: str | None
    disposition: str
    duration_seconds: Decimal | None
    sample_lower_volts: Decimal | None
    sample_upper_volts: Decimal | None
    prepared_lower_volts: Decimal | None
    prepared_upper_volts: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.observation_sha256 is not None:
            validate_sha256(self.observation_sha256, field_name="observation_sha256")
        if self.disposition not in {"ADMITTED", "REFUSED", "UNEVALUABLE", "UNSUPPORTED"}:
            raise ValueError("RC decision disposition is unknown")
        _reasons(self.reason_codes)
        if (self.disposition == "ADMITTED") != (self.duration_seconds is not None):
            raise ValueError("Only an admitted RC decision commits a finite preparation")
        for name in ("duration_seconds", "sample_lower_volts", "sample_upper_volts", "prepared_lower_volts", "prepared_upper_volts"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError("RC committed preparation duration cannot be negative")


@dataclass(frozen=True, slots=True)
class RCChainArmResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/arm-result"
    arm_id: str
    duration_seconds: Decimal | None
    left_voltage_volts: Decimal | None
    right_voltage_volts: Decimal | None
    prospective_lower_volts: Decimal | None
    prospective_upper_volts: Decimal | None
    prospective_support: bool | None
    actual_support: bool | None
    predicted_endpoint_volts: Decimal
    actual_endpoint_volts: Decimal | None
    endpoint_within_task: bool | None
    numerical_converged: bool | None
    preparation_state: str
    joined_state: str
    reason_codes: tuple[str, ...]
    completion_seconds: Decimal | None
    deadline_seconds: Decimal
    response_role: str
    native_model: ResistorCapacitorLadderModelConfig | None
    native_panels: tuple[ResistorCapacitorLadderNativePanel, ...]
    numerical_check: ResistorCapacitorLadderNumericalCheck | None

    def __post_init__(self) -> None:
        if self.arm_id not in ARM_IDS:
            raise ValueError("RC result has an unknown preparation arm")
        _state(self.preparation_state)
        _state(self.joined_state)
        _reasons(self.reason_codes)
        if self.response_role not in {"PROSPECTIVE_PACKAGE_USE", "DECLINED_DEVELOPMENT_ASSAY", "NO_RESPONSE"}:
            raise ValueError("RC response evidence role is unknown")
        for name in ("duration_seconds", "left_voltage_volts", "right_voltage_volts", "prospective_lower_volts",
                     "prospective_upper_volts", "predicted_endpoint_volts", "actual_endpoint_volts", "completion_seconds", "deadline_seconds"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        if self.native_model is None:
            if self.native_panels or self.numerical_check is not None or self.response_role != "NO_RESPONSE":
                raise ValueError("RC unexecuted arm cannot retain native response evidence")
        elif len(self.native_panels) != 2 or self.numerical_check is None:
            raise ValueError("RC executed arm requires its two nested views and numerical check")


@dataclass(frozen=True, slots=True)
class RCChainCaseResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/case-result"
    variant_id: str
    expectation: RCChainObservationExpectation
    observation: RCChainObservation | None
    decision: RCChainDecision
    measurement_state: str
    measurement_reason_codes: tuple[str, ...]
    arms: tuple[RCChainArmResult, ...]

    def __post_init__(self) -> None:
        if self.variant_id not in VARIANT_IDS:
            raise ValueError("RC result has an unknown observation variant")
        _state(self.measurement_state)
        _reasons(self.measurement_reason_codes)
        expected = ARM_IDS if self.variant_id == "adequate" else ("selected",)
        if tuple(arm.arm_id for arm in self.arms) != expected:
            raise ValueError("RC case result drops or reorders an assigned preparation arm")


@dataclass(frozen=True, slots=True)
class RCChainUnitResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/unit-result"
    unit_id: str
    config_sha256: str
    measurement_source: ResistorCapacitorLadderModelConfig
    source_panels: tuple[ResistorCapacitorLadderNativePanel, ...]
    cases: tuple[RCChainCaseResult, ...]
    evidence_role: str = EVIDENCE_ROLE
    source_failure_reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.unit_id, field_name="unit_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        if self.evidence_role != EVIDENCE_ROLE or tuple(case.variant_id for case in self.cases) != VARIANT_IDS:
            raise ValueError("RC unit result changes evidence role or omits an assigned observation variant")
        _reasons(self.source_failure_reason_codes)
        expected_views = 0 if self.source_failure_reason_codes == ("NUMERICAL_EXECUTION_FAILED",) else 2
        if self.source_failure_reason_codes not in {(), ("NUMERICAL_EXECUTION_FAILED",), ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",)}:
            raise ValueError("RC source failure reason is outside its closed numerical dispositions")
        if len(self.source_panels) != expected_views:
            raise ValueError("RC observation source requires two nested numerical views")


@dataclass(frozen=True, slots=True)
class RCChainOutcomeCount(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/outcome-count"
    variant_id: str
    arm_id: str
    claim_id: str
    state: str
    count: int

    def __post_init__(self) -> None:
        if self.variant_id not in VARIANT_IDS or self.arm_id not in ARM_IDS or self.claim_id not in CLAIM_IDS:
            raise ValueError("RC outcome census has unknown assigned keys")
        _state(self.state)
        if type(self.count) is not int or self.count < 0:
            raise ValueError("RC outcome count must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class RCChainSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/summary"
    config_sha256: str
    unit_ids: tuple[str, ...]
    unit_result_sha256s: tuple[str, ...]
    unit_count: int
    nested_variant_count: int
    nested_arm_count: int
    nested_view_count: int
    outcome_counts: tuple[RCChainOutcomeCount, ...]
    evidence_role: str = EVIDENCE_ROLE
    unsupported_prerequisites: tuple[str, ...] = UNSUPPORTED_PREREQUISITES

    def __post_init__(self) -> None:
        validate_sha256(self.config_sha256, field_name="config_sha256")
        if (tuple(sorted(set(self.unit_ids))) != self.unit_ids or self.unit_count != len(self.unit_ids)
            or len(self.unit_result_sha256s) != self.unit_count):
            raise ValueError("RC summary changes its complete unit census")
        for digest in self.unit_result_sha256s:
            validate_sha256(digest, field_name="unit_result_sha256s")
        if self.evidence_role != EVIDENCE_ROLE or self.unsupported_prerequisites != UNSUPPORTED_PREREQUISITES:
            raise ValueError("RC development summary cannot promote its evidence or close unsupported prerequisites")


@dataclass(frozen=True, slots=True)
class RCChainDesignProof(CanonicalRecord):
    """Pure design compilation: no observed outputs, issue or authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/rc-prerequisite-chain/design-proof"
    config_sha256: str
    unit_count: int
    variant_count: int
    maximum_nested_arm_count: int
    maximum_nested_view_count: int
    maximum_native_steps: int
    maximum_output_bytes: int
    maximum_aggregate_output_bytes: int
    evidence_role: str = EVIDENCE_ROLE
    unsupported_prerequisites: tuple[str, ...] = UNSUPPORTED_PREREQUISITES
