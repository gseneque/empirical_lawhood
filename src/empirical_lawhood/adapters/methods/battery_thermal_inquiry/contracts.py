# SPDX-License-Identifier: MPL-2.0
"""Closed pre-output scientific operands and exact native receiver records."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    canonical_json_bytes,
    require_sorted_unique_strings,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
)

D = Decimal
PROTOCOL_SHA256 = "553b7c23587818892bba11894096aa95f68994f1163d5ed2e6d6fad8086829e3"
QUESTION = "Within the selected LGM50 numerical models, which temperature-dependent response procedure admits the least-time registered charging preparation to operational SOC 80%, and can its assessed model-selection procedure support later 20 C and subsequent 30 C decisions?"
UNIT = "unit.battery-thermal-inquiry.lgm50-family"
SOURCE_ID = "source.battery-thermal-inquiry.lgm50"
SOURCE_VERSION = "26.6.2.0"
RECIPES = ("chamber-35c", "chamber-40c", "original-ambient")
MODEL_VIEWS = ("chen-spme", "oregan-dfn", "oregan-dfn-refined", "oregan-spme")
DEVELOPMENT_TEMPERATURES = (D("278.15"), D("298.15"), D("308.15"))
LATER_TEMPERATURES = {"use": D("293.15"), "reuse": D("303.15")}
CONTROL_RULE = "conservative-hybrid-CCCV;min((4.2-V)/1V,(I+active_magnitude)/1A)=0;LOW=1.455A;HIGH=3.395A;LOW-to-HIGH-at-298.15K+epsilon;HIGH-to-LOW-at-298.15K+epsilon/2;HIGH-only-if-realized-T>298.15K"
TIER_TEMPERATURE = D("298.15")
PRIMARY_LOCALIZATION = D("0.001")
REFINED_LOCALIZATION = D("0.0001")
TIER_EVENT = "Inquiry conservative temperature tier [experiment]"
TARGET_CHARGE = D("2.5")
INTEGRAL_TOLERANCE = D("0.0001")
MAX_MODEL_CLOCK = D("180000")
TARGET_EVENT = "Inquiry operational SOC80 charge target [A.h]"
REQUIRED_EVENT_NAMES = (
    TARGET_EVENT,
    "Inquiry maximum mean temperature [K]",
    "Inquiry minimum mean temperature [K]",
    "Inquiry numerical maximum voltage [V]",
    "Inquiry source minimum charging magnitude [A]",
    "Minimum voltage [V]",
    TIER_EVENT,
)
BACKEND_SOLVE_SCOPE = "MAIN_CHARGING_SUBSOLVES_ONLY"

# Exact installed scientific/native sources. These hashes are initial stock,
# not output-dependent qualification or a new source distribution identity.
SOURCE_MEMBERS = (
    (
        "experiment/step/base_step.py",
        "529b13e48d47bde6dbe7568b77dfa9eb414bdfddcdfef41f10090c704ffa4c51",
    ),
    (
        "experiment/step/step_termination.py",
        "dec8604759478667d2b5b8bc27ce083ff765519aaa2d84600dd88c01bb4930a0",
    ),
    (
        "experiment/step/steps.py",
        "646840589957343587ab23916718dc5d3a5d645116d238c4fdfb23606e849d08",
    ),
    (
        "expression_tree/binary_operators.py",
        "0d63c767b0c19b0596a13bcb5ae35cfcba800e4e465aeb532f7ea6210b8199c4",
    ),
    (
        "expression_tree/input_parameter.py",
        "dca5228c35ed5dbae85e26ce2a7b6fb316e2a6260721372d10372b732d496bb0",
    ),
    (
        "input/parameters/lithium_ion/Chen2020.py",
        "7c360a546a76492585e147231caee2f8f4fe29222b893cb12091dc4d158f62f0",
    ),
    (
        "input/parameters/lithium_ion/ORegan2022.py",
        "c0c8111cb37fd4e79726f17e0d02f0aaac6d06532060a677efb5743c92a0b259",
    ),
    (
        "meshes/one_dimensional_submeshes.py",
        "26f6b8b86ea1d73c912de54c83dcf3f58f4c879cd7ed03d01f7827057c212e7a",
    ),
    (
        "models/full_battery_models/base_battery_model.py",
        "5391e6db1e13fac3746f5317c27830df2d4cb3bf96295161c22ca439ba3777ec",
    ),
    (
        "models/full_battery_models/lithium_ion/dfn.py",
        "84711c3ac78beac3c4de102f043549d8ffb11f6a1411c47ce47d0e4488c8a00c",
    ),
    (
        "models/full_battery_models/lithium_ion/electrode_soh.py",
        "55002481f8bd9750ebee05667a1e70382bbd7da1c3fb7a5327c8db0e9cf19d54",
    ),
    (
        "models/full_battery_models/lithium_ion/spme.py",
        "3a5a1b870be8f88cdd510f3dc131731029d89b304c68b5d2f4b7084781304543",
    ),
    (
        "models/submodels/external_circuit/explicit_control_external_circuit.py",
        "59d8387a084760b84f3084ef0176afb29db31a653103fa6d8842ec786442cdc5",
    ),
    (
        "models/submodels/external_circuit/function_control_external_circuit.py",
        "63a902b35a2228428ebc2a74934076e88420dd2e23158c2d675b362f8489f471",
    ),
    (
        "models/submodels/thermal/base_thermal.py",
        "4e66ef69411b6233a456d43c134abca30b321ef290806c193ddad0a1c07b825d",
    ),
    (
        "models/submodels/thermal/lumped.py",
        "f4c03e752281b8089a1b98fbb8e4a09670f618b24ce2317a1dcb99dcb3422609",
    ),
    (
        "models/submodels/thermal/surface/ambient.py",
        "b3b5c42e8065d97e9c525fcfc025c8f68309f8931f963ebed54b43323a5d1f11",
    ),
    (
        "parameters/electrical_parameters.py",
        "19a3b43c6aac04a60d3736cbf186e50ebf5b2515e3e76e496a6675447c0372c6",
    ),
    (
        "parameters/geometric_parameters.py",
        "4609bf6e420494d76e58102fbc43222778ceaa10bc167a2b054c642df436aff9",
    ),
    (
        "parameters/parameter_values.py",
        "869abd3bc55b40591859e45a6af822de976739a6b872782edf4c0874ba7966f6",
    ),
    (
        "parameters/thermal_parameters.py",
        "605ea7d30bfe10ea5418d4fe3a2ce4705782fc6e631c01e436d031c8ba02083a",
    ),
    (
        "simulation/base_simulation.py",
        "70e345a89433b001ebce742a3d6697ee3e7605557af99c86a146d9563618f1f4",
    ),
    (
        "simulation/simulation.py",
        "06544d81a67ca62d833a8c637e596c2dfe0a0fc205a35dc9ebf5942d107f7a23",
    ),
    (
        "solvers/algebraic_solver.py",
        "7eca13b6dc8daf8a8b23a79f2eaa3c45cdc170479fe19d37ee2ba3b4ca92a07f",
    ),
    (
        "solvers/base_solver.py",
        "6be19408156c28188fd5cafea3d95aa6b472efaa5f10a2e97e14cf8f84e450b0",
    ),
    (
        "solvers/composite_solver.py",
        "a540e804a83be9c476a52b30e4be8ca96faf4014f570565a9831fbed5bc5b239",
    ),
    (
        "solvers/idaklu_solver.py",
        "50eaece1875e98baea0fab51a59c1fcfcbf5d82e7b088dc65d11fad42b6081aa",
    ),
    (
        "solvers/nonlinear_solver.py",
        "edb602af017bbaf2c7f1d678fabb722831db7d1b71cf3e084430646ade7ef5ef",
    ),
    (
        "solvers/solution.py",
        "fdc7bfb8b2a251f95d9f139f9c434d64a8c45e9a8475d239767735cd947b161d",
    ),
)


@dataclass(frozen=True, slots=True)
class BatteryInquirySource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/source"
    VERSION: ClassVar[str] = "1.1.0"
    source_id: str = SOURCE_ID
    protocol_sha256: str = PROTOCOL_SHA256
    pybamm_version: str = SOURCE_VERSION
    source_members: tuple[tuple[str, str], ...] = SOURCE_MEMBERS
    manufacturer_document_sha256: str = (
        "a8d895143a55e0beae273f2c94eb4f3038857f19cc190ea2048f825e77a76f6a"
    )

    def __post_init__(self):
        if (
            self.source_id,
            self.protocol_sha256,
            self.pybamm_version,
            self.source_members,
            self.manufacturer_document_sha256,
        ) != (
            SOURCE_ID,
            PROTOCOL_SHA256,
            SOURCE_VERSION,
            SOURCE_MEMBERS,
            "a8d895143a55e0beae273f2c94eb4f3038857f19cc190ea2048f825e77a76f6a",
        ):
            raise ValueError(
                "thermal inquiry changes its separately frozen source/protocol"
            )


def scope(source):
    return ScientificConditionScope(
        "system.battery-thermal-inquiry.lgm50",
        "world.battery-thermal-inquiry.numerical",
        source.source_id,
        ("charge", "current", "mean-temperature", "time", "voltage"),
        ("A.h", "A", "K", "s", "V"),
        "receiver.battery-thermal-inquiry.realized-native",
        "clock.battery-thermal-inquiry.native-model",
        "One exposed LGM50 family; three registered guarded CC/CV chamber recipes, development5/25/35C, later20C and subsequent30C; all models/meshes/preparations nested, zero physical units. Conditional sampled numerical qualification only; no whole-time, physical, plating, degradation or global-optimality certificate.",
        source_config_sha256=source.fingerprint(),
        instance_id=UNIT,
    )


@dataclass(frozen=True, slots=True)
class BatteryInquiryNativeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/native-config"
    VERSION: ClassVar[str] = "1.1.0"
    config_id: str
    source: BatteryInquirySource
    phase: str
    initial_temperature_k: Decimal
    recipe: str
    model_view: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (
            self.phase not in {"supply", "use", "reuse"}
            or self.recipe not in RECIPES
            or self.model_view not in MODEL_VIEWS
        ):
            raise ValueError(
                "thermal native recipe/model/phase differs from selected finite roster"
            )
        allowed = (
            DEVELOPMENT_TEMPERATURES
            if self.phase == "supply"
            else (LATER_TEMPERATURES[self.phase],)
        )
        if self.initial_temperature_k not in allowed:
            raise ValueError(
                "thermal native preparation is outside its exact selected phase"
            )

    @property
    def chamber_temperature_k(self):
        return {"chamber-35c": D("308.15"), "chamber-40c": D("313.15")}.get(
            self.recipe, self.initial_temperature_k
        )

    @property
    def localization_epsilon_k(self):
        return (
            REFINED_LOCALIZATION
            if self.model_view == "oregan-dfn-refined"
            else PRIMARY_LOCALIZATION
        )


@dataclass(frozen=True, slots=True)
class BatteryInquiryDelivery(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/native-delivery"
    VERSION: ClassVar[str] = "1.1.0"
    requested_rule: str
    requested_voltage_v: Decimal
    accepted_voltage_v: Decimal | None
    requested_chamber_k: Decimal
    accepted_chamber_k: Decimal | None
    requested_model_clock_s: Decimal
    applied_model_clock_s: Decimal | None
    accepted_control_expression: str
    applied_control_expression: str
    applied_current_expression: str
    applied_voltage_expression: str
    applied_chamber_expression: str
    applied_current_a: Decimal | None
    applied_voltage_v: Decimal | None
    applied_chamber_k: Decimal | None

    def __post_init__(self):
        if (
            self.requested_rule != CONTROL_RULE
            or self.requested_voltage_v != D("4.2")
            or self.requested_model_clock_s != 0
        ):
            raise ValueError(
                "native delivery changes the selected request or native clock"
            )
        for name in (
            "requested_voltage_v",
            "accepted_voltage_v",
            "requested_chamber_k",
            "accepted_chamber_k",
            "requested_model_clock_s",
            "applied_model_clock_s",
            "applied_current_a",
            "applied_voltage_v",
            "applied_chamber_k",
        ):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if (
            self.accepted_voltage_v is not None
            and self.accepted_voltage_v != self.requested_voltage_v
        ):
            raise ValueError("accepted native voltage target differs")
        if (
            self.accepted_chamber_k is not None
            and self.accepted_chamber_k != self.requested_chamber_k
        ):
            raise ValueError("accepted native chamber target differs")


@dataclass(frozen=True, slots=True)
class BatteryInquiryInitializerAttempt(CanonicalRecord):
    """One actual initial-state algebraic solve, including internal fallbacks."""

    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-thermal-inquiry/initializer-attempt"
    )
    attempt_index: int
    solver_class: str
    solver_name: str
    solver_configuration_json: str
    model_name: str
    model_expression_sha256: str
    disposition: str
    error_type: str | None
    error_message: str | None
    cpu_seconds: Decimal
    wall_seconds: Decimal

    def __post_init__(self):
        if self.attempt_index < 1 or not all(
            (
                self.solver_class,
                self.solver_name,
                self.solver_configuration_json,
                self.model_name,
            )
        ):
            raise ValueError("initializer attempt lacks its actual solver/model census")
        validate_sha256(self.model_expression_sha256)
        if (
            self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
            or (
                self.disposition == "TECHNICAL_FAILURE"
                and (self.error_type is None or self.error_message is None)
            )
            or (
                self.disposition == "RETURNED"
                and (self.error_type is not None or self.error_message is not None)
            )
        ):
            raise ValueError(
                "initializer attempt changes actual return/error classification"
            )
        for name in ("cpu_seconds", "wall_seconds"):
            validate_decimal(getattr(self, name), field_name=name)
            if getattr(self, name) < 0:
                raise ValueError("initializer measured expense cannot be negative")


@dataclass(frozen=True, slots=True)
class BatteryInquiryChargingAttempt(CanonicalRecord):
    """An actual event-segment solve; initializers are a separate census."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/charging-attempt"
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

    def __post_init__(self):
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
            PRIMARY_LOCALIZATION,
            REFINED_LOCALIZATION,
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
class BatteryInquiryTransition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/transition"
    transition_index: int
    preceding_attempt: int
    following_attempt: int
    from_regime: str
    to_regime: str
    event_name: str
    threshold_k: Decimal
    root_clock_s: Decimal
    left_receivers: tuple[Decimal, ...]
    left_differential_state: tuple[Decimal, ...]
    right_clock_s: Decimal | None
    right_receivers: tuple[Decimal, ...]
    right_differential_state: tuple[Decimal, ...]

    def __post_init__(self):
        if (
            self.transition_index < 1
            or self.preceding_attempt < 1
            or self.following_attempt != self.preceding_attempt + 1
            or (self.from_regime, self.to_regime)
            not in {("LOW", "HIGH"), ("HIGH", "LOW")}
            or self.event_name != TIER_EVENT
        ):
            raise ValueError("transition changes native event or regime lineage")
        for value in (
            self.threshold_k,
            self.root_clock_s,
            *self.left_receivers,
            *self.left_differential_state,
            *self.right_receivers,
            *self.right_differential_state,
        ):
            validate_decimal(value, field_name="hybrid_transition")
        if len(self.left_receivers) != 4 or not self.left_differential_state:
            raise ValueError("native tier root lacks its actual left state")
        if self.right_clock_s is not None:
            validate_decimal(self.right_clock_s, field_name="right_clock_s")
            if (
                self.right_clock_s < self.root_clock_s
                or len(self.right_receivers) != 4
                or not self.right_differential_state
            ):
                raise ValueError(
                    "hybrid continuation omits its actual right differential state/clock"
                )
        elif self.right_receivers or self.right_differential_state:
            raise ValueError("unresolved continuation invents a right native state")


@dataclass(frozen=True, slots=True)
class BatteryInquiryTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/native-trace"
    VERSION: ClassVar[str] = "1.1.0"
    trace_id: str
    config: BatteryInquiryNativeConfig
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
    charging_attempts: tuple[BatteryInquiryChargingAttempt, ...] = ()
    transitions: tuple[BatteryInquiryTransition, ...] = ()
    temperature_regimes: tuple[str, ...] = ()

    def __post_init__(self):
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
class BatteryInquiryTraceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/trace-check"
    VERSION: ClassVar[str] = "1.1.0"
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
            self.trace.object_schema != BatteryInquiryTrace.SCHEMA
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
class BatteryInquiryReferenceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/reference-check"
    VERSION: ClassVar[str] = "1.1.0"
    check_id: str
    primary: ObjectIdentity
    refined: ObjectIdentity
    disposition: AssessmentDisposition
    completion_difference_s: Decimal | None
    voltage_difference_v: Decimal | None
    temperature_difference_k: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.check_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        for name in (
            "completion_difference_s",
            "voltage_difference_v",
            "temperature_difference_k",
        ):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if (
            self.disposition is not AssessmentDisposition.SATISFIED
            and not self.reason_codes
        ):
            raise ValueError("unresolved reference precision requires reasons")


@dataclass(frozen=True, slots=True)
class BatteryInquiryProcedure(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/procedure"
    VERSION: ClassVar[str] = "1.1.0"
    procedure_id: str
    selected_model: str | None
    admitted_models: tuple[str, ...]
    reference_checks: tuple[BatteryInquiryReferenceCheck, ...]
    model_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    model_cpu_seconds: tuple[tuple[str, Decimal], ...]
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.procedure_id)
        require_sorted_unique_strings(
            self.admitted_models, field_name="admitted_models"
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.selected_model is not None and self.selected_model not in {
            "chen-spme",
            "oregan-spme",
            "oregan-dfn",
        }:
            raise ValueError("supplier changes its selected model family")
        if (
            self.selected_model in {"chen-spme", "oregan-spme"}
            and self.selected_model not in self.admitted_models
        ):
            raise ValueError("supplier selects an unadmitted reduced model")
        if (
            self.disposition is AssessmentDisposition.SATISFIED
            and self.selected_model is None
        ):
            raise ValueError(
                "satisfied procedure requires an actual admitted/fallback model"
            )


@dataclass(frozen=True, slots=True)
class BatteryInquirySupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/supply"
    VERSION: ClassVar[str] = "1.1.0"
    product_id: str
    source: BatteryInquirySource
    traces: tuple[BatteryInquiryTrace, ...]
    trace_checks: tuple[BatteryInquiryTraceCheck, ...]
    check: BatteryInquiryProcedure
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (
            self.scope != scope(self.source)
            or self.disposition is not self.check.disposition
        ):
            raise ValueError(
                "supplier changes its original scope or procedure disposition"
            )
        expected = {
            (t, r, m)
            for t in DEVELOPMENT_TEMPERATURES
            for r in RECIPES
            for m in MODEL_VIEWS
        }
        if (
            len(self.traces) != len(expected)
            or {
                (v.config.initial_temperature_k, v.config.recipe, v.config.model_view)
                for v in self.traces
            }
            != expected
        ):
            raise ValueError(
                "supplier omits or duplicates a selected native recipe denominator"
            )
        if any(
            v.config.source != self.source or v.config.phase != "supply"
            for v in self.traces
        ):
            raise ValueError("supplier changes producing source/preparation phase")
        if len(self.trace_checks) != len(self.traces) or tuple(
            v.trace.object_fingerprint for v in self.trace_checks
        ) != tuple(v.fingerprint() for v in self.traces):
            raise ValueError(
                "supplier trace checks are not their exact retained trace census"
            )


@dataclass(frozen=True, slots=True)
class BatteryInquiryInstance(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/instance"
    VERSION: ClassVar[str] = "1.1.0"
    instance_id: str
    source: BatteryInquirySource
    supplier: ObjectIdentity
    phase: str
    initial_temperature_k: Decimal
    prior_use: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.instance_id)
        if (
            self.phase not in LATER_TEMPERATURES
            or self.initial_temperature_k != LATER_TEMPERATURES[self.phase]
        ):
            raise ValueError("recipient changes exact later/reuse preparation")
        if self.supplier.object_schema != BatteryInquirySupply.SCHEMA:
            raise ValueError("recipient lacks its actual supplier identity")
        if self.phase == "reuse":
            if (
                self.prior_use is None
                or self.prior_use.object_schema != BatteryInquiryAssessment.SCHEMA
            ):
                raise ValueError(
                    "subsequent reuse lacks its exact prior-use assessment"
                )
        elif self.prior_use is not None:
            raise ValueError("first later use cannot claim a previous use")


@dataclass(frozen=True, slots=True)
class BatteryInquiryAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/assessment"
    VERSION: ClassVar[str] = "1.1.0"
    assessment_id: str
    supplier: ObjectIdentity
    scope: ScientificConditionScope
    instance: BatteryInquiryInstance
    traces: tuple[BatteryInquiryTrace, ...]
    trace_checks: tuple[BatteryInquiryTraceCheck, ...]
    reference_checks: tuple[BatteryInquiryReferenceCheck, ...]
    selected_recipe: str | None
    reference_best_recipes: tuple[str, ...]
    direct_dfn_selected_recipe: str | None
    unsupplied_chen_selected_recipe: str | None
    instance_disposition: AssessmentDisposition
    admission_disposition: AssessmentDisposition
    joined_disposition: AssessmentDisposition
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    cache_hits: tuple[tuple[str, str], ...]
    comparative_disposition: str = "SHARED_COMPETENT_INQUIRY_NO_ADVANTAGE_CLAIM"
    physical_independent_units: int = 0
    simulated_parameter_families: int = 1

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        require_sorted_unique_strings(
            self.reference_best_recipes, field_name="reference_best_recipes"
        )
        if self.supplier != self.instance.supplier or self.scope != scope(
            self.instance.source
        ):
            raise ValueError(
                "recipient changes original supplied scope/source identity"
            )
        if self.selected_recipe is not None and self.selected_recipe not in RECIPES:
            raise ValueError("recipient selects outside the frozen finite menu")
        if (
            self.physical_independent_units != 0
            or self.simulated_parameter_families != 1
        ):
            raise ValueError(
                "numerical assessment cannot manufacture physical independence"
            )
        if self.native_provider_attempts != sum(
            v.native_provider_attempts for v in self.traces
        ) or self.backend_solve_calls != sum(
            v.backend_solve_calls for v in self.traces
        ):
            raise ValueError("recipient hides native attempt/solve census")


@dataclass(frozen=True, slots=True)
class BatteryInquiryCostAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-inquiry/cost-allocation"
    VERSION: ClassVar[str] = "1.1.0"
    allocation_id: str
    arm: str
    charged_traces: tuple[ObjectIdentity, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    forecast_cpu_seconds: Decimal
    forecast_wall_seconds: Decimal
    shared_computations: bool = True
    engineering_researcher_expense: str = "UNKNOWN"
    complete_total_cost_superiority: str = "UNEVALUABLE"
    initializer_solver_attempts: int = 0
    backend_solve_scope: str = BACKEND_SOLVE_SCOPE

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        if self.arm not in {
            "el-full-procedure",
            "matched-conventional-full-procedure",
            "direct-dfn",
        }:
            raise ValueError("cost allocation substitutes its selected whole inquiry")
        if (
            not self.shared_computations
            or self.engineering_researcher_expense != "UNKNOWN"
            or self.complete_total_cost_superiority != "UNEVALUABLE"
        ):
            raise ValueError(
                "shared numerical allocation cannot fabricate independent trials or known complete expense"
            )
        if (
            self.initializer_solver_attempts < 0
            or self.backend_solve_scope != BACKEND_SOLVE_SCOPE
        ):
            raise ValueError(
                "cost census cannot disguise initialization as charging forecasts"
            )
        for name in ("forecast_cpu_seconds", "forecast_wall_seconds"):
            validate_decimal(getattr(self, name), field_name=name)
