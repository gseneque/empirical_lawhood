# SPDX-License-Identifier: MPL-2.0
"""Closed thermal-service operands; historical battery contracts are unchanged."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id

MAX_PRODUCT_BYTES = None
QUESTION = "Does ordinary standard-rate charging supply the selected 900 s top-up in both 23 C and 27 C preparations?"
SOURCE_VERSION = "26.6.2.0"
PARAMETER_SHA256 = "7c360a546a76492585e147231caee2f8f4fe29222b893cb12091dc4d158f62f0"
GEOMETRY_SHA256 = "4609bf6e420494d76e58102fbc43222778ceaa10bc167a2b054c642df436aff9"
DENOMINATOR = "denominator.pybamm.spme.lumped.arbitrary.chen2020.casadi-safe-v1"
PROTOCOL_SHA256 = "dca5201fbcffbf7c1955dfeacf8458b253d43fb7620ca069d16051c51cbc7d41"
EVENTS = ("Maximum voltage [V]", "Minimum voltage [V]", "Service maximum volume-mean temperature [K]", "Service minimum volume-mean temperature [K]")
MODEL_MEMBERS = (
    ("models/full_battery_models/base_battery_model.py", "5391e6db1e13fac3746f5317c27830df2d4cb3bf96295161c22ca439ba3777ec"),
    ("models/full_battery_models/lithium_ion/spme.py", "3a5a1b870be8f88cdd510f3dc131731029d89b304c68b5d2f4b7084781304543"),
    ("models/submodels/thermal/base_thermal.py", "4e66ef69411b6233a456d43c134abca30b321ef290806c193ddad0a1c07b825d"),
    ("models/submodels/thermal/lumped.py", "f4c03e752281b8089a1b98fbb8e4a09670f618b24ce2317a1dcb99dcb3422609"),
    ("models/submodels/thermal/surface/ambient.py", "b3b5c42e8065d97e9c525fcfc025c8f68309f8931f963ebed54b43323a5d1f11"),
    ("parameters/thermal_parameters.py", "605ea7d30bfe10ea5418d4fe3a2ce4705782fc6e631c01e436d031c8ba02083a"),
)


@dataclass(frozen=True, slots=True)
class BatteryThermalSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-service/source"
    source_version: str = SOURCE_VERSION
    parameter_set: str = "Chen2020"
    parameter_sha256: str = PARAMETER_SHA256
    geometry_sha256: str = GEOMETRY_SHA256
    denominator_id: str = DENOMINATOR
    model_members: tuple[tuple[str, str], ...] = MODEL_MEMBERS

    def __post_init__(self):
        if (self.source_version, self.parameter_set, self.parameter_sha256, self.geometry_sha256, self.denominator_id) != (SOURCE_VERSION, "Chen2020", PARAMETER_SHA256, GEOMETRY_SHA256, DENOMINATOR):
            raise ValueError("thermal service changes its separately frozen source denominator")
        if self.model_members != MODEL_MEMBERS:
            raise ValueError("thermal service changes its selected native model/options members")


@dataclass(frozen=True, slots=True)
class BatteryThermalConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-service/config"
    config_id: str
    operation: str
    protocol_sha256: str
    unit_id: str
    initial_temperature_k: Decimal
    word: str = "standard-cc900"
    view: str = "primary"
    initial_soc: Decimal = Decimal("0.30")
    source: BatteryThermalSource = BatteryThermalSource()

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_stable_id(self.unit_id)
        validate_sha256(self.protocol_sha256)
        if self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("thermal service changes its pre-output selection")
        validate_decimal(self.initial_temperature_k, field_name="initial_temperature_k")
        if self.operation not in {"acquire", "assess"} or self.word not in {"standard-cc900", "native-hold900"}:
            raise ValueError("thermal service operation or finite word differs")
        if self.view not in {"primary", "tighter"} or self.initial_soc != Decimal("0.30") or self.initial_temperature_k not in {Decimal("296.15"), Decimal("300.15")}:
            raise ValueError("thermal service preparation or numerical view differs")
        if self.view == "tighter" and self.initial_temperature_k != Decimal("296.15"):
            raise ValueError("tighter view is nested only in the selected 23 C preparation")
        token = "23c" if self.initial_temperature_k == Decimal("296.15") else "27c"
        if self.unit_id != f"unit.battery-thermal-service.{token}":
            raise ValueError("thermal preparation unit cannot be relabeled as fresh evidence")

    @property
    def current_a(self):
        return Decimal("-1.455") if self.word == "standard-cc900" else Decimal(0)


@dataclass(frozen=True, slots=True)
class BatteryThermalTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-service/native-trace"
    config: BatteryThermalConfig
    source_sha256: str
    implementation_sha256: str
    disposition: str
    termination: str
    reason_codes: tuple[str, ...]
    requested_current_a: Decimal
    accepted_current_a: Decimal | None
    applied_current_a: Decimal | None
    times_s: tuple[Decimal, ...]
    current_a: tuple[Decimal, ...]
    voltage_v: tuple[Decimal, ...]
    discharge_capacity_ah: tuple[Decimal, ...]
    volume_mean_temperature_k: tuple[Decimal, ...]
    event_names: tuple[str, ...]
    processed_event_expressions: tuple[str, ...] = ()
    solver_dt_max_s: Decimal = Decimal(10)
    requested_model_clock_s: Decimal = Decimal(0)
    accepted_model_clock_s: Decimal | None = None
    applied_model_clock_s: Decimal | None = None

    def __post_init__(self):
        if self.config.operation != "acquire" or self.source_sha256 != self.config.source.fingerprint():
            raise ValueError("thermal trace changes its producing config/source")
        validate_sha256(self.implementation_sha256)
        if self.disposition not in {"COMPLETE", "SIMULATOR_TERMINATED", "TECHNICAL_OBSERVATION_FAILURE"}:
            raise ValueError("thermal trace disposition differs")
        if self.requested_current_a != self.config.current_a:
            raise ValueError("thermal trace requested word differs")
        for value in (self.requested_current_a, self.accepted_current_a, self.applied_current_a):
            if value is not None:
                validate_decimal(value, field_name="native_delivery_stage")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        columns = (self.times_s, self.current_a, self.voltage_v, self.discharge_capacity_ah, self.volume_mean_temperature_k)
        if any(len(column) != len(self.times_s) for column in columns):
            raise ValueError("thermal trace receiver denominator differs")
        for column in columns:
            for value in column:
                validate_decimal(value, field_name="native_receiver")
        if self.times_s and (self.times_s[0] != 0 or any(a >= b for a, b in zip(self.times_s, self.times_s[1:])) or self.times_s[-1] > 900):
            raise ValueError("thermal trace native clock differs")
        if self.disposition == "COMPLETE" and (not self.times_s or self.times_s[-1] != 900 or self.termination != "final time"):
            raise ValueError("thermal complete trace lacks its final receiver")
        if self.event_names and self.event_names != EVENTS:
            raise ValueError("thermal trace event denominator differs")
        if self.processed_event_expressions and len(self.processed_event_expressions) != len(EVENTS):
            raise ValueError("thermal processed event expression denominator differs")
        if self.solver_dt_max_s != Decimal(10):
            raise ValueError("thermal solver maximum step differs")
        if self.requested_model_clock_s != 0:
            raise ValueError("thermal request must precede its origin preparation")
        for value in (self.accepted_model_clock_s, self.applied_model_clock_s):
            if value is not None:
                validate_decimal(value, field_name="native_stage_clock")


@dataclass(frozen=True, slots=True)
class BatteryThermalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-thermal-service/assessment"
    config_sha256: str
    trace_sha256: str
    disposition: str
    reason_codes: tuple[str, ...]
    realized_charge_ah: Decimal | None
    capacity_charge_ah: Decimal | None
    charge_discrepancy_ah: Decimal | None
    sampled_envelope_pass: bool
    numerical_event_guarded: bool
    whole_time_certified: bool = False
    physical_independent_units: int = 0
    simulated_parameter_families: int = 1

    def __post_init__(self):
        validate_sha256(self.config_sha256)
        validate_sha256(self.trace_sha256)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        for value in (self.realized_charge_ah, self.capacity_charge_ah, self.charge_discrepancy_ah):
            if value is not None:
                validate_decimal(value, field_name="charge_assessment")
        if (self.realized_charge_ah is None) != (self.capacity_charge_ah is None) or (self.capacity_charge_ah is None) != (self.charge_discrepancy_ah is None):
            raise ValueError("thermal charge assessment receiver denominator differs")
        if self.realized_charge_ah is not None and self.charge_discrepancy_ah != abs(self.realized_charge_ah - self.capacity_charge_ah):
            raise ValueError("thermal charge assessment discrepancy differs")
        if self.whole_time_certified or self.physical_independent_units != 0 or self.simulated_parameter_families != 1:
            raise ValueError("numerical thermal assessment cannot grant continuous certification or physical units")
        if self.disposition not in {"NUMERICAL_SERVICE_PASS_CONTINUOUS_CERTIFICATE_ABSENT", "SERVICE_FAIL", "UNEVALUABLE"}:
            raise ValueError("thermal assessment disposition differs")
