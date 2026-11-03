# SPDX-License-Identifier: MPL-2.0
"""New immutable numerical selections and receipt-referenced evidence contracts."""
from dataclasses import dataclass
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySource, SOURCE_MEMBERS, RECIPES, DEVELOPMENT_TEMPERATURES,
    LATER_TEMPERATURES, BatteryInquiryDelivery, BatteryInquiryInitializerAttempt,
    BatteryInquiryTransition, BACKEND_SOLVE_SCOPE, MAX_MODEL_CLOCK,
    UNIT as UNIT, scope as original_scope,
)
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import ADDITIONAL_SOURCE_MEMBERS
from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
HISTORY_SCHEMAS = ("empirical-lawhood/battery-dfn-precision-diagnostic/result", ObstructionAssessment.SCHEMA)

D = Decimal
REDUCED = ("chen-spme", "oregan-spme")
DFN_VIEWS = ("dfn-primary", "dfn-band", "dfn-refined")


def identity(record):
    for field in ("source_id", "policy_id", "config_id", "trace_id", "check_id", "product_id", "instance_id", "choice_id"):
        if hasattr(record, field):
            return ObjectIdentity.from_record(getattr(record, field), record)
    raise ValueError("refined record has no semantic identity")


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} requires an integer >= {minimum}")


@dataclass(frozen=True, slots=True)
class NumericalView(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/numerical-view"
    view_id: str
    model_view: str
    electrode_points: int
    particle_points: int
    localization_epsilon_k: Decimal
    rtol: Decimal
    atol: Decimal

    def __post_init__(self):
        validate_stable_id(self.view_id)
        if self.model_view not in (*REDUCED, "oregan-dfn"):
            raise ValueError("numerical view changes selected model families")
        _integer(self.electrode_points, "electrode_points", 2)
        _integer(self.particle_points, "particle_points", 2)
        for field in ("localization_epsilon_k", "rtol", "atol"):
            validate_decimal(getattr(self, field), field_name=field)
            if getattr(self, field) <= 0:
                raise ValueError("numerical settings must be positive exact Decimals")


@dataclass(frozen=True, slots=True)
class NumericalSelection(CanonicalRecord):
    """Explicit prospective protocol bound to actual result or adverse history.

    Historical obstruction grants no numerical selection evidence or adequacy.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/numerical-selection"
    policy_id: str
    diagnostic: ObjectIdentity
    views: tuple[NumericalView, ...]
    development_preparations: tuple[tuple[Decimal, str], ...]
    later_preparations: tuple[tuple[str, Decimal, tuple[str, ...]], ...]
    tolerance_probe: bool
    scientific_gates: tuple[Decimal, ...] = (D(1), D("0.001"), D("0.01"), D("0.0001"), D("0.01"), D(2))

    def __post_init__(self):
        if self.scientific_gates != (D(1), D("0.001"), D("0.01"), D("0.0001"), D("0.01"), D(2)):
            raise ValueError("numerical selection changes unchanged precision/integral/admission/tie gates")
        # Reuse the exact complete roster/isolation checks; suppress only the
        # policy's digest check while validating this noncyclic protocol body.
        _validate_numerical_roster(self)


@dataclass(frozen=True, slots=True)
class NumericalPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/numerical-policy"
    policy_id: str
    diagnostic: ObjectIdentity
    protocol_sha256: str
    views: tuple[NumericalView, ...]
    development_preparations: tuple[tuple[Decimal, str], ...]
    later_preparations: tuple[tuple[str, Decimal, tuple[str, ...]], ...]
    tolerance_probe: bool

    def __post_init__(self):
        _validate_numerical_roster(self)
        validate_sha256(self.protocol_sha256)
        if self.protocol_sha256 != self.selection.fingerprint():
            raise ValueError("policy views/rosters do not match exact canonical selection protocol")

    @property
    def selection(self):
        return NumericalSelection(self.policy_id, self.diagnostic, self.views,
            self.development_preparations, self.later_preparations, self.tolerance_probe)

    @property
    def comparison_pairs(self):
        return (("dfn-band", "dfn-primary"), ("dfn-primary", "dfn-refined"),
                ("dfn-band", "dfn-refined")) + ((('dfn-refined', 'dfn-tolerance'),) if self.tolerance_probe else ())


def _validate_numerical_roster(self):
    validate_stable_id(self.policy_id)
    if self.diagnostic.object_schema not in HISTORY_SCHEMAS:
        raise ValueError("policy requires an actual result or explicit adverse-history identity")
    if type(self.tolerance_probe) is not bool:
        raise ValueError("tolerance probe declaration must be boolean")
    require_sorted_unique_ids(self.views, attribute="view_id", field_name="views")
    expected = {*REDUCED, *DFN_VIEWS} | ({"dfn-tolerance"} if self.tolerance_probe else set())
    rows = {v.view_id: v for v in self.views}
    if rows.keys() != expected or any(rows[v].model_view != "oregan-dfn" for v in expected - set(REDUCED)):
        raise ValueError("policy omits complete reduced and primary/band/mesh/combined DFN views")
    if any(rows[v].model_view != v for v in REDUCED):
        raise ValueError("policy renames a reduced parameter/model family")
    expected_development = tuple((t, r) for t in DEVELOPMENT_TEMPERATURES for r in RECIPES)
    if canonical_json_bytes(self.development_preparations) != canonical_json_bytes(expected_development):
        raise ValueError("policy requires all nine development preparations")
    expected_later = tuple((phase, LATER_TEMPERATURES[phase], RECIPES) for phase in ("use", "reuse"))
    if canonical_json_bytes(self.later_preparations) != canonical_json_bytes(expected_later):
        raise ValueError("policy changes exact later20/reuse30 full recipe rosters")
    a, b, c = (rows[v] for v in DFN_VIEWS)
    mesh = lambda v: (v.electrode_points, v.particle_points)
    tol = lambda v: (v.rtol, v.atol)
    if mesh(a) != mesh(b) or tol(a) != tol(b) or b.localization_epsilon_k <= a.localization_epsilon_k:
        raise ValueError("band probe must isolate a wider localization band")
    if (c.localization_epsilon_k != a.localization_epsilon_k or tol(b) != tol(c)
            or any(x <= y for x, y in zip(mesh(c), mesh(b), strict=True))):
        raise ValueError("primary/refined comparison must isolate a strictly refined mesh")
    if self.tolerance_probe:
        p = rows["dfn-tolerance"]
        if (mesh(p) != mesh(c) or p.localization_epsilon_k != c.localization_epsilon_k
                or p.rtol > c.rtol or p.atol > c.atol or tol(p) == tol(c)):
            raise ValueError("optional tolerance probe must isolate tighter tolerances")

@dataclass(frozen=True, slots=True)
class RefinedSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/source"
    source_id: str
    original: BatteryInquirySource
    policy: ObjectIdentity
    diagnostic: ObjectIdentity
    protocol_sha256: str
    source_members: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if type(self.original) is not BatteryInquirySource or self.original != BatteryInquirySource():
            raise ValueError("refined source changes immutable1.1 scientific stock")
        if self.policy.object_schema != NumericalPolicy.SCHEMA:
            raise ValueError("source requires exact numerical policy")
        if self.diagnostic.object_schema not in HISTORY_SCHEMAS:
            raise ValueError("source requires actual result or explicit adverse-history lineage")
        validate_sha256(self.protocol_sha256)
        if self.source_members != tuple(sorted((*SOURCE_MEMBERS, *ADDITIONAL_SOURCE_MEMBERS))):
            raise ValueError("source omits or changes exact native member pins")


def scope(source):
    """One existing numerical family, with a separately bound numerical source."""
    if type(source) is not RefinedSource:
        raise ValueError("refined scope requires its own exact source")
    source.__post_init__()
    return replace(original_scope(source.original), source_id=source.source_id,
        source_config_sha256=source.fingerprint(),
        coordinate_meaning="One exposed LGM50 family; all nine development5/25/35C preparations and three recipes at later20C/reuse30C. Two reduced models and the declared three-DFN band/mesh/combined triangle, with an optional explicitly selected tolerance probe, are nested views. Fixed finite-path conditional sampled numerical qualification; zero physical units, no full interaction, asymptotic convergence, whole-time, plating, degradation or global-optimality certificate.")


@dataclass(frozen=True, slots=True)
class NativeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/native-config"
    config_id: str
    source: RefinedSource
    policy: NumericalPolicy
    phase: str
    initial_temperature_k: Decimal
    recipe: str
    component_view: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_decimal(self.initial_temperature_k, field_name="initial_temperature_k")
        self.source.__post_init__()
        self.policy.__post_init__()
        expected_id = f"config.battery-refined-inquiry.{self.phase}.{self.initial_temperature_k}.{self.recipe}.{self.component_view}"
        if self.config_id != expected_id:
            raise ValueError("config label changes exact selected scientific effect identity")
        if self.source.policy != identity(self.policy) or self.source.diagnostic != self.policy.diagnostic or self.source.protocol_sha256 != self.policy.protocol_sha256:
            raise ValueError("config source/policy/diagnostic/protocol join differs")
        selected = (self.initial_temperature_k, self.recipe)
        allowed = self.policy.development_preparations if self.phase == "qualification" else (
            tuple((t, r) for p, t, recipes in self.policy.later_preparations if p == self.phase for r in recipes))
        if selected not in allowed or self.component_view not in {v.view_id for v in self.policy.views}:
            raise ValueError("config changes exact phase/preparation/numerical roster")
        canonical_temperature = next(t for t, r in allowed if (t, r) == selected)
        if self.initial_temperature_k.as_tuple() != canonical_temperature.as_tuple():
            raise ValueError("config relabels exact preparation temperature encoding")

    @property
    def numerical_view(self):
        return next(v for v in self.policy.views if v.view_id == self.component_view)

    @property
    def model_view(self):
        return self.numerical_view.model_view

    @property
    def localization_epsilon_k(self):
        return self.numerical_view.localization_epsilon_k

    @property
    def rtol(self):
        return self.numerical_view.rtol

    @property
    def atol(self):
        return self.numerical_view.atol

    @property
    def prior_supply(self):
        # Shared independent comparison joins the exact diagnostic lineage witness.
        return self.source.diagnostic

    @property
    def chamber_temperature_k(self):
        return D("308.15") if self.recipe == "chamber-35c" else D("313.15") if self.recipe == "chamber-40c" else self.initial_temperature_k


@dataclass(frozen=True, slots=True)
class ChargingAttempt(CanonicalRecord):
    """An actual event-segment solve; initializers are a separate census."""

    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-refined-inquiry/charging-attempt"
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
    configuration: NativeConfig | None = None

    def __post_init__(self):
        if type(self.configuration) is not NativeConfig:
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
class Trace(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-refined-inquiry/native-trace"
    )
    VERSION: ClassVar[str] = "1.0.0"
    trace_id: str
    config: NativeConfig
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
    charging_attempts: tuple[ChargingAttempt, ...] = ()
    transitions: tuple[BatteryInquiryTransition, ...] = ()
    temperature_regimes: tuple[str, ...] = ()

    def __post_init__(self):
        if (
            type(self.config) is not NativeConfig
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
class TraceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-refined-inquiry/trace-check"
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
            self.trace.object_schema != Trace.SCHEMA
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
class Comparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-refined-inquiry/comparison"
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
            x.object_schema != Trace.SCHEMA for x in (self.left, self.right)
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
class Qualification(CanonicalRecord):
    """Compact evidence projection; complete traces remain separate receipt outputs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/qualification"
    product_id: str
    source: ObjectIdentity
    policy: ObjectIdentity
    diagnostic: ObjectIdentity
    traces: tuple[ObjectIdentity, ...]
    checks: tuple[TraceCheck, ...]
    comparisons: tuple[Comparison, ...]
    admitted_models: tuple[str, ...]
    selected_model: str | None
    model_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    model_cpu_seconds: tuple[tuple[str, Decimal], ...]
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.product_id)
        require_sorted_unique_ids(self.traces, attribute="object_id", field_name="traces")
        require_sorted_unique_strings(self.admitted_models, field_name="admitted_models")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.source.object_schema != RefinedSource.SCHEMA or self.policy.object_schema != NumericalPolicy.SCHEMA:
            raise ValueError("qualification changes source/policy identities")
        if tuple(c.trace for c in self.checks) != self.traces:
            raise ValueError("qualification checks omit or duplicate traces")
        if self.selected_model is not None and self.selected_model not in (*REDUCED, "dfn-primary"):
            raise ValueError("qualification selects unsupported model")
        if self.selected_model in REDUCED and self.selected_model not in self.admitted_models:
            raise ValueError("qualification selects refused reduced model")
        if (self.disposition is AssessmentDisposition.SATISFIED) != (self.selected_model is not None):
            raise ValueError("qualification precision/disposition cannot invent admission")
        if self.selected_model is not None and any(c.disposition is not AssessmentDisposition.SATISFIED for c in self.comparisons):
            raise ValueError("even direct DFN requires complete reference precision")


@dataclass(frozen=True, slots=True)
class Supply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/supply"
    product_id: str
    source: RefinedSource
    policy: NumericalPolicy
    qualification: Qualification

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.source.policy != identity(self.policy) or self.source.diagnostic != self.policy.diagnostic
                or self.source.protocol_sha256 != self.policy.protocol_sha256
                or self.qualification.source != identity(self.source)
                or self.qualification.policy != identity(self.policy)
                or self.qualification.diagnostic != self.source.diagnostic):
            raise ValueError("supply changes original source/policy/qualification lineage")
        from .science import validate_qualification_projection
        validate_qualification_projection(self.source, self.policy, self.qualification)

    @property
    def disposition(self):
        return self.qualification.disposition


@dataclass(frozen=True, slots=True)
class Instance(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/instance"
    instance_id: str
    source: ObjectIdentity
    policy: ObjectIdentity
    supplier: ObjectIdentity
    phase: str
    initial_temperature_k: Decimal
    prior_use: ObjectIdentity | None

    def __post_init__(self):
        validate_stable_id(self.instance_id)
        if self.phase not in LATER_TEMPERATURES or self.initial_temperature_k != LATER_TEMPERATURES[self.phase]:
            raise ValueError("instance changes later20/reuse30 preparation")
        if self.supplier.object_schema != Supply.SCHEMA or self.source.object_schema != RefinedSource.SCHEMA or self.policy.object_schema != NumericalPolicy.SCHEMA:
            raise ValueError("instance substitutes original supplier/source/policy")
        if self.phase == "reuse":
            if self.prior_use is None or self.prior_use.object_schema != AssessedInstance.SCHEMA:
                raise ValueError("reuse requires actual prior-use instance product")
        elif self.prior_use is not None:
            raise ValueError("first use cannot invent prior use")


@dataclass(frozen=True, slots=True)
class ChoiceCommitment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/choice-commitment"
    choice_id: str
    supplier: ObjectIdentity
    instance: ObjectIdentity
    forecast_traces: tuple[ObjectIdentity, ...]
    forecast_checks: tuple[TraceCheck, ...]
    selected_recipe: str | None
    tie_recipes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.choice_id)
        require_sorted_unique_strings(self.tie_recipes, field_name="tie_recipes")
        if len(self.forecast_traces) != len(RECIPES) or len(set(self.forecast_traces)) != len(RECIPES):
            raise ValueError("choice omits full forecast recipe roster")
        if tuple(c.trace for c in self.forecast_checks) != self.forecast_traces:
            raise ValueError("choice check/forecast identities differ")
        from .science import best_recipes
        ties = best_recipes(dict(zip(RECIPES, self.forecast_checks, strict=True)))
        if self.tie_recipes != ties or self.selected_recipe != (ties[0] if ties else None):
            raise ValueError("choice differs from before-reveal forecast-only reduction")


@dataclass(frozen=True, slots=True)
class Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/assessment"
    product_id: str
    supplier: ObjectIdentity
    instance: Instance
    choice: ChoiceCommitment
    persisted_choice: ObjectIdentity
    traces: tuple[ObjectIdentity, ...]
    checks: tuple[TraceCheck, ...]
    comparisons: tuple[Comparison, ...]
    reference_best_recipes: tuple[str, ...]
    instance_disposition: AssessmentDisposition
    admission_disposition: AssessmentDisposition
    joined_disposition: AssessmentDisposition
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]
    native_provider_attempts: int
    backend_solve_calls: int
    cpu_seconds: Decimal
    wall_seconds: Decimal
    physical_independent_units: int = 0
    whole_time_certified: bool = False

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if self.supplier != self.instance.supplier or self.choice.supplier != self.supplier or self.choice.instance != identity(self.instance):
            raise ValueError("assessment changes exact original supplier/instance")
        if self.persisted_choice != identity(self.choice):
            raise ValueError("assessment requires exact retained before-reveal choice witness")
        if self.physical_independent_units != 0 or self.whole_time_certified:
            raise ValueError("numerical instance cannot grant physical/whole-time qualification")
        require_sorted_unique_ids(self.traces, attribute="object_id", field_name="traces")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        require_sorted_unique_strings(self.reference_best_recipes, field_name="reference_best_recipes")
        if tuple(c.trace for c in self.checks) != self.traces:
            raise ValueError("assessment omits complete trace checks")
        for field in ("native_provider_attempts", "backend_solve_calls"):
            _integer(getattr(self, field), field)
        for field in ("cpu_seconds", "wall_seconds"):
            validate_decimal(getattr(self, field), field_name=field, minimum=D(0))


@dataclass(frozen=True, slots=True)
class AssessedInstance(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-refined-inquiry/assessed-instance"
    product_id: str
    supplier: Supply
    assessment: Assessment
    prior_use: Assessment | None

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if self.assessment.supplier != identity(self.supplier):
            raise ValueError("assessed instance substitutes original supplier")
        if self.assessment.instance.phase == "use":
            if self.prior_use is not None:
                raise ValueError("first assessed use cannot invent earlier use")
        elif self.prior_use is None or self.prior_use.instance.phase != "use" or self.prior_use.supplier != identity(self.supplier) or not self.prior_use.traces:
            raise ValueError("reuse must retain actual entered use of original supplier")
        if self.assessment.instance.phase == "reuse":
            prior = AssessedInstance("product.battery-refined-inquiry.assessed-use", self.supplier, self.prior_use, None)
            if self.assessment.instance.prior_use != identity(prior):
                raise ValueError("reuse wrapper changes exact actual prior-use identity")
