# SPDX-License-Identifier: MPL-2.0
"""Distinct diagnostic records: no reinterpretation of historical inquiry bytes."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    canonical_json_bytes,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
    require_sorted_unique_strings,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySource,
    BatteryInquiryDelivery,
    BatteryInquiryInitializerAttempt,
    BatteryInquiryTransition,
    MAX_MODEL_CLOCK,
    BACKEND_SOLVE_SCOPE,
)

D = Decimal
ADDITIONAL_SOURCE_MEMBERS = (
    (
        "expression_tree/operations/serialise.py",
        "ab8ab725e5e037ffbab4dd8c714e62f348e82bcceef83346455259e6b6e5c472",
    ),
)
PROTOCOL_SHA256 = "c450c87f4542321320e72858ffe6568e4b39ebf9dbab418772b95b2e7a2f901e"
PRIOR_SHA256 = "a79d5bf5ffdb4bc232615a445eb82f058ce3ac4c8137fbc5b3a94352eaabda6e"
PREPARATIONS = (
    (D("278.15"), "chamber-40c"),
    (D("298.15"), "original-ambient"),
    (D("308.15"), "original-ambient"),
)
NUMERICS = (
    ("A", 90, 120, D("1e-5"), D("1e-9"), D("1e-10")),
    ("B", 90, 120, D("1e-6"), D("1e-9"), D("1e-10")),
    ("C", 180, 240, D("1e-6"), D("1e-9"), D("1e-10")),
    ("D", 90, 120, D("1e-6"), D("1e-7"), D("1e-8")),
)
QUESTION = (
    "Finite DFN band, mesh and tolerance sensitivity under unchanged1s/1mV/.01K gates."
)


@dataclass(frozen=True, slots=True)
class DiagnosticSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-dfn-precision-diagnostic/source"
    source_id: str = "source.battery-dfn-precision-diagnostic"
    original: BatteryInquirySource = BatteryInquirySource()
    additional_source_members: tuple[tuple[str, str], ...] = ADDITIONAL_SOURCE_MEMBERS
    protocol_sha256: str = PROTOCOL_SHA256
    prior_supply_sha256: str = PRIOR_SHA256
    preparations: tuple[tuple[Decimal, str], ...] = PREPARATIONS
    numerics: tuple[tuple[str, int, int, Decimal, Decimal, Decimal], ...] = NUMERICS

    def __post_init__(self):
        if (
            self.source_id != "source.battery-dfn-precision-diagnostic"
            or self.original != BatteryInquirySource()
            or self.additional_source_members != ADDITIONAL_SOURCE_MEMBERS
            or self.protocol_sha256 != PROTOCOL_SHA256
            or self.prior_supply_sha256 != PRIOR_SHA256
            or self.preparations != PREPARATIONS
            or self.numerics != NUMERICS
        ):
            raise ValueError("diagnostic source changes selected finite question")


@dataclass(frozen=True, slots=True)
class DiagnosticNativeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/native-config"
    )
    config_id: str
    source: DiagnosticSource
    prior_supply: ObjectIdentity
    initial_temperature_k: Decimal
    recipe: str
    component_view: str
    electrode_points: int
    particle_points: int
    localization_epsilon_k: Decimal
    rtol: Decimal
    atol: Decimal
    phase: str = "diagnostic"
    model_view: str = "oregan-dfn"

    def __post_init__(self):
        self.source.__post_init__()
        validate_stable_id(self.config_id)
        if (
            self.config_id
            != f"config.battery-dfn-precision-diagnostic.{int(self.initial_temperature_k - D('273.15'))}c.{self.recipe}.{self.component_view.lower()}"
        ):
            raise ValueError(
                "diagnostic config label changes selected scientific identity"
            )
        if (
            self.phase != "diagnostic"
            or self.model_view != "oregan-dfn"
            or (self.initial_temperature_k, self.recipe) not in PREPARATIONS
            or (
                self.component_view,
                self.electrode_points,
                self.particle_points,
                self.localization_epsilon_k,
                self.rtol,
                self.atol,
            )
            not in NUMERICS
            or self.prior_supply.object_id != "product.battery-thermal-inquiry.supply"
            or self.prior_supply.object_schema
            != "empirical-lawhood/battery-thermal-inquiry/supply"
            or self.prior_supply.object_version != "1.1.0"
            or self.prior_supply.object_fingerprint != self.source.prior_supply_sha256
        ):
            raise ValueError(
                "diagnostic configuration changes actual outcome or finite numerics"
            )

    @property
    def chamber_temperature_k(self):
        return (
            D("313.15") if self.recipe == "chamber-40c" else self.initial_temperature_k
        )


@dataclass(frozen=True, slots=True)
class DiagnosticChargingAttempt(CanonicalRecord):
    """An actual event-segment solve; initializers are a separate census."""

    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/charging-attempt"
    )
    attempt_index: int
    regime: str
    localization_epsilon_k: Decimal
    requested_start_clock_s: Decimal
    solver_configuration_json: str
    model_expression_sha256: str
    control_expression: str
    input_values: tuple[tuple[str, Decimal], ...]
    requested_differential_state: tuple[Decimal, ...]
    disposition: str
    termination: str
    error_type: str | None
    error_message: str | None
    cpu_seconds: Decimal
    wall_seconds: Decimal
    native_times_s: tuple[Decimal, ...]
    start_differential_state: tuple[Decimal, ...]
    end_differential_state: tuple[Decimal, ...]
    start_receivers: tuple[Decimal, ...]
    end_receivers: tuple[Decimal, ...]
    consistent_initialization: str = "IDAKLU_INTERNAL_CALC_IC_REQUESTED"
    requested_state_sha256: str = ""
    realized_start_state_sha256: str = ""
    realized_end_state_sha256: str = ""
    configuration: DiagnosticNativeConfig | None = None

    def __post_init__(self):
        if type(self.configuration) is not DiagnosticNativeConfig:
            raise ValueError(
                "diagnostic subsolve omits exact numerical/source/prior-procedure config"
            )
        self.configuration.__post_init__()
        if self.localization_epsilon_k != self.configuration.localization_epsilon_k:
            raise ValueError("diagnostic subsolve changes configured localization")
        for name, values in (
            ("requested_state_sha256", self.requested_differential_state),
            ("realized_start_state_sha256", self.start_differential_state),
            ("realized_end_state_sha256", self.end_differential_state),
        ):
            expected = sha256(
                canonical_json_bytes({"scaled_differential_state": values})
            ).hexdigest()
            if getattr(self, name) not in {"", expected}:
                raise ValueError(
                    "charging state digest substitutes its actual requested/realized vector"
                )
            object.__setattr__(self, name, expected)
        if (
            self.attempt_index < 1
            or self.regime not in {"LOW", "HIGH"}
            or not all(
                (
                    self.solver_configuration_json,
                    self.control_expression,
                    self.termination,
                )
            )
        ):
            raise ValueError(
                "charging subsolve omits its actual numerical/control census"
            )
        validate_sha256(self.model_expression_sha256)
        if self.localization_epsilon_k not in {
            D("1e-5"),
            D("1e-6"),
        }:
            raise ValueError("charging subsolve substitutes a localization band")
        if self.consistent_initialization != "IDAKLU_INTERNAL_CALC_IC_REQUESTED":
            raise ValueError(
                "charging initialization request is not observed solver internals"
            )
        if (
            self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
            or (self.disposition == "TECHNICAL_FAILURE")
            != (self.error_type is not None and self.error_message is not None)
            or (
                self.disposition == "RETURNED"
                and (self.error_type is not None or self.error_message is not None)
            )
        ):
            raise ValueError("charging subsolve loses its return/error classification")
        for value in (
            self.requested_start_clock_s,
            self.cpu_seconds,
            self.wall_seconds,
            *self.native_times_s,
            *self.requested_differential_state,
            *self.start_differential_state,
            *self.end_differential_state,
            *self.start_receivers,
            *self.end_receivers,
            *(value for _, value in self.input_values),
        ):
            validate_decimal(value, field_name="charging_subsolve")
        if min(self.requested_start_clock_s, self.cpu_seconds, self.wall_seconds) < 0:
            raise ValueError("charging subsolve has negative clock or measured expense")
        if self.native_times_s and any(
            a >= b for a, b in zip(self.native_times_s, self.native_times_s[1:])
        ):
            raise ValueError("charging subsolve native clocks are omitted or reordered")
        if self.disposition == "RETURNED" and (
            not self.native_times_s
            or not self.start_differential_state
            or len(self.start_differential_state) != len(self.end_differential_state)
            or len(self.start_receivers) != 4
            or len(self.end_receivers) != 4
        ):
            raise ValueError(
                "returned charging subsolve lacks full differential boundary states/receivers"
            )


@dataclass(frozen=True, slots=True)
class DiagnosticTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/native-trace"
    )
    VERSION: ClassVar[str] = "1.0.0"
    trace_id: str
    config: DiagnosticNativeConfig
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
    event_names: tuple[str, ...]
    processed_event_expressions: tuple[str, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    wall_seconds: Decimal
    cpu_seconds: Decimal
    process_peak_rss_bytes: int
    initializer_attempts: tuple[BatteryInquiryInitializerAttempt, ...] = ()
    backend_solve_scope: str = BACKEND_SOLVE_SCOPE
    charging_attempts: tuple[DiagnosticChargingAttempt, ...] = ()
    transitions: tuple[BatteryInquiryTransition, ...] = ()
    temperature_regimes: tuple[str, ...] = ()

    def __post_init__(self):
        if (
            type(self.config) is not DiagnosticNativeConfig
            or self.trace_id != "trace." + self.config.config_id
        ):
            raise ValueError("diagnostic trace substitutes its typed numerical config")
        self.config.__post_init__()
        validate_stable_id(self.trace_id)
        validate_sha256(self.implementation_sha256)
        if self.disposition not in {
            "TARGET_REACHED",
            "SERVICE_TERMINATED",
            "TECHNICAL_FAILURE",
        }:
            raise ValueError("thermal trace changes its terminal interpretation")
        columns = (
            self.current_a,
            self.voltage_v,
            self.capacity_ah,
            self.mean_temperature_k,
            self.ambient_temperature_k,
            self.control_modes,
        )
        if any(len(values) != len(self.times_s) for values in columns):
            raise ValueError(
                "thermal trace has an incomplete native receiver denominator"
            )
        for values in (self.times_s, *columns[:-1]):
            for value in values:
                validate_decimal(value, field_name="native_receiver")
        if self.times_s and (
            self.times_s[0] != 0
            or any(a >= b for a, b in zip(self.times_s, self.times_s[1:]))
            or self.times_s[-1] > MAX_MODEL_CLOCK
        ):
            raise ValueError("thermal trace changes its native clock")
        if any(mode not in {"CC", "CV", "UNRESOLVED"} for mode in self.control_modes):
            raise ValueError("thermal trace changes current/voltage mode grammar")
        if self.delivery.requested_chamber_k != self.config.chamber_temperature_k:
            raise ValueError("thermal trace changes its actual chamber request")
        if len(self.event_names) != len(self.processed_event_expressions):
            raise ValueError("thermal trace event expression census differs")
        if len(set(self.event_names)) != len(self.event_names) or any(
            not name for name in self.event_names
        ):
            raise ValueError("thermal trace duplicates or empties native event names")
        if self.native_provider_attempts != 1 or self.backend_solve_calls != len(
            self.charging_attempts
        ):
            raise ValueError(
                "charging subsolve census cannot hide or invent numerical calls"
            )
        if len(self.temperature_regimes) != len(self.times_s) or any(
            mode not in {"LOW", "HIGH"} for mode in self.temperature_regimes
        ):
            raise ValueError("hybrid trace omits its receiver regime denominator")
        if tuple(row.attempt_index for row in self.charging_attempts) != tuple(
            range(1, len(self.charging_attempts) + 1)
        ):
            raise ValueError("charging subsolve attempts omit or reorder actual calls")
        if any(
            row.localization_epsilon_k != self.config.localization_epsilon_k
            for row in self.charging_attempts
        ):
            raise ValueError(
                "hybrid trace substitutes its selected primary/refined band"
            )
        if tuple(row.transition_index for row in self.transitions) != tuple(
            range(1, len(self.transitions) + 1)
        ):
            raise ValueError("hybrid transitions omit or reorder actual event roots")
        if any(row.configuration != self.config for row in self.charging_attempts):
            raise ValueError(
                "diagnostic trace substitutes call numerical configuration"
            )
        for row in self.transitions:
            if row.preceding_attempt > len(
                self.charging_attempts
            ) or row.following_attempt > len(self.charging_attempts):
                raise ValueError("hybrid transition invents an unentered charging call")
            before = self.charging_attempts[row.preceding_attempt - 1]
            if (
                before.regime != row.from_regime
                or before.end_receivers != row.left_receivers
                or before.end_differential_state != row.left_differential_state
                or not before.native_times_s
                or before.native_times_s[-1] != row.root_clock_s
            ):
                raise ValueError(
                    "hybrid transition relabels its actual native left root"
                )
            if row.following_attempt <= len(self.charging_attempts):
                after = self.charging_attempts[row.following_attempt - 1]
                if (
                    after.regime != row.to_regime
                    or after.requested_differential_state != row.left_differential_state
                ):
                    raise ValueError(
                        "hybrid transition loses its complete requested differential state"
                    )
                if row.right_clock_s is not None and (
                    after.start_receivers != row.right_receivers
                    or after.start_differential_state != row.right_differential_state
                    or after.native_times_s[0] != row.right_clock_s
                ):
                    raise ValueError(
                        "hybrid transition relabels its actual right native state"
                    )
        if self.backend_solve_scope != BACKEND_SOLVE_SCOPE:
            raise ValueError(
                "charging forecast count cannot disguise initializer solves"
            )
        if tuple(row.attempt_index for row in self.initializer_attempts) != tuple(
            range(1, len(self.initializer_attempts) + 1)
        ):
            raise ValueError(
                "initializer solve attempts omit or reorder actual fallback census"
            )
        for name in ("wall_seconds", "cpu_seconds"):
            validate_decimal(getattr(self, name), field_name=name)
            if getattr(self, name) < 0:
                raise ValueError("native measured expense cannot be negative")
        if self.process_peak_rss_bytes < 0:
            raise ValueError("process peak RSS cannot be negative")


@dataclass(frozen=True, slots=True)
class DiagnosticTraceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/trace-check"
    )
    VERSION: ClassVar[str] = "1.0.0"
    check_id: str
    trace: ObjectIdentity
    disposition: AssessmentDisposition
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
        if (
            self.trace.object_schema != DiagnosticTrace.SCHEMA
            or self.whole_time_certified
        ):
            raise ValueError(
                "trace check changes its retained source or grants continuous certification"
            )
        for name in (
            "realized_charge_ah",
            "capacity_charge_ah",
            "discrepancy_ah",
            "completion_time_s",
        ):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if (
            self.disposition is not AssessmentDisposition.SATISFIED
            and not self.reason_codes
        ):
            raise ValueError("negative or unevaluable trace check requires reasons")


@dataclass(frozen=True, slots=True)
class DiagnosticComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-dfn-precision-diagnostic/comparison"
    )
    check_id: str
    left: ObjectIdentity
    right: ObjectIdentity
    disposition: AssessmentDisposition
    terminal_time_difference_s: Decimal | None
    maximum_voltage_difference_v: Decimal | None
    maximum_temperature_difference_k: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.check_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if any(
            x.object_schema != DiagnosticTrace.SCHEMA for x in (self.left, self.right)
        ):
            raise ValueError("comparison substitutes diagnostic traces")
        for value in (
            self.terminal_time_difference_s,
            self.maximum_voltage_difference_v,
            self.maximum_temperature_difference_k,
        ):
            if value is not None:
                validate_decimal(value, field_name="comparison")
                if value < 0:
                    raise ValueError("negative sensitivity")
        if (self.disposition is AssessmentDisposition.SATISFIED) != (
            not self.reason_codes
        ):
            raise ValueError("comparison disposition disagrees with strict gates")


@dataclass(frozen=True, slots=True)
class DiagnosticResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-dfn-precision-diagnostic/result"
    product_id: str
    source: DiagnosticSource
    prior_supply: ObjectIdentity
    traces: tuple[DiagnosticTrace, ...]
    checks: tuple[DiagnosticTraceCheck, ...]
    comparisons: tuple[DiagnosticComparison, ...]
    disposition: AssessmentDisposition
    qualification: bool = False

    def __post_init__(self):
        from .science import validate_result

        validate_result(self)
