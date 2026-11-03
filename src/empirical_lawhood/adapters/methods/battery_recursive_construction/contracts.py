"""Closed scientific records for the separately executed battery development waves."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
import math
import struct
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition, RequirementSupplyAssessment, ScientificConnectionSpec,
    ScientificConditionScope, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)

D = Decimal
PROTOCOL_SHA256 = "ee41e58c038f34029a1d29073507e196ceb8cbf5853eb2978a02f15a06945ce3"
MAX_PRODUCT_BYTES = 4 * 1024**2
REQUIRED_CHANNELS = ("internal-state-f8", "source-input-ledger")
OBSERVABLE_CHANNELS = ("capacity-Ah", "soc", "temperature-K")


class BatteryOperation(StrEnum):
    CHECKPOINT = "CHECKPOINT"
    PROJECT = "PROJECT"
    REFERENCE = "REFERENCE"
    FULL = "FULL"
    SOC = "SOC"
    TIGHTER = "TIGHTER"
    ASSESS = "ASSESS"
    PROCEDURE = "PROCEDURE"
    IMPORT = "IMPORT"
    ADMIT_C1 = "ADMIT_C1"
    ADMIT_C2 = "ADMIT_C2"
    VOLTAGE = "VOLTAGE"


@dataclass(frozen=True, slots=True)
class BatterySourceContract(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-source"
    source_id: str = "pybamm-26.6.2.0-chen2020-spme-casadi"
    pybamm_version: str = "26.6.2.0"
    casadi_version: str = "3.7.2"
    numpy_version: str = "2.4.6"
    scipy_version: str = "1.17.1"
    parameter_sha256: str = "7c360a546a76492585e147231caee2f8f4fe29222b893cb12091dc4d158f62f0"
    model_sha256: str = "3a5a1b870be8f88cdd510f3dc131731029d89b304c68b5d2f4b7084781304543"
    solver_sha256: str = "bfcf0f76e01e8f613b66064af3374cb793801aed4a3d1c7230ee94824dd1009a"
    mesh_points: int = 20
    coarse_rtol: Decimal = D("0.00001")
    coarse_atol: Decimal = D("0.000001")
    tighter_rtol: Decimal = D("0.0000001")
    tighter_atol: Decimal = D("0.00000001")
    integrator_max_steps: int = 100000
    max_step_decreases: int = 5

    def __post_init__(self):
        expected = {
            "source_id": "pybamm-26.6.2.0-chen2020-spme-casadi", "pybamm_version": "26.6.2.0",
            "casadi_version": "3.7.2", "numpy_version": "2.4.6", "scipy_version": "1.17.1",
            "parameter_sha256": "7c360a546a76492585e147231caee2f8f4fe29222b893cb12091dc4d158f62f0",
            "model_sha256": "3a5a1b870be8f88cdd510f3dc131731029d89b304c68b5d2f4b7084781304543",
            "solver_sha256": "bfcf0f76e01e8f613b66064af3374cb793801aed4a3d1c7230ee94824dd1009a",
            "mesh_points": 20, "coarse_rtol": D("0.00001"), "coarse_atol": D("0.000001"),
            "tighter_rtol": D("0.0000001"), "tighter_atol": D("0.00000001"),
            "integrator_max_steps": 100000, "max_step_decreases": 5,
        }
        if any(getattr(self, name) != value for name, value in expected.items()):
            raise ValueError("battery source or numerical operands differ from the frozen protocol")


@dataclass(frozen=True, slots=True)
class BatteryOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-operation-config"
    config_id: str
    operation: BatteryOperation
    wave: str
    history: str = "early"
    future_word: str = "hold"
    source: BatterySourceContract = BatterySourceContract()
    protocol_sha256: str = PROTOCOL_SHA256
    requirement: ScientificRequirementSpec | None = None
    connection: ScientificConnectionSpec | None = None
    contribution_sha256: str | None = None

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name="config_id")
        if not isinstance(self.operation, BatteryOperation):
            raise ValueError("battery operation must use its registered closed grammar")
        if self.wave not in {"A", "B"} or self.history not in {"early", "late"}:
            raise ValueError("unassigned battery preparation or history")
        if self.wave == "B" and self.history != "early":
            raise ValueError("Wave B has one declared early history")
        if self.future_word not in {"hold", "early1", "late1", "early3"}:
            raise ValueError("unassigned future current word")
        if self.wave == "A" and self.future_word != "hold":
            raise ValueError("Wave A evidence is scoped to hold continuation")
        if self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("scientific protocol identity differs")
        if (self.requirement is None) != (self.connection is None):
            raise ValueError("assessment requires both exact requirement and connection")
        if self.requirement is not None and self.connection.requirement_id != self.requirement.requirement_id:
            raise ValueError("battery connection names another scientific requirement")
        if self.operation in {BatteryOperation.ASSESS, BatteryOperation.ADMIT_C1,
                              BatteryOperation.ADMIT_C2, BatteryOperation.VOLTAGE} and self.requirement is None:
            raise ValueError("battery assessment requires exact scientific claim operands")
        if self.contribution_sha256 is not None:
            validate_sha256(self.contribution_sha256)
        if self.operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2} and self.contribution_sha256 is None:
            raise ValueError("Wave B admission requires its actual imported contribution digest")

    @property
    def initial_soc(self):
        return D("0.60") if self.wave == "A" else D("0.70")

    @property
    def unit_id(self):
        return f"battery-preparation-{self.wave.lower()}"


@dataclass(frozen=True, slots=True)
class BatteryCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-checkpoint"
    checkpoint_id: str
    source: BatterySourceContract
    unit_id: str
    history: str
    initial_soc: Decimal
    checkpoint_seconds: Decimal
    capacity_Ah: Decimal
    temperature_K: Decimal
    source_current_A: Decimal
    source_input_ledger: tuple[tuple[str, Decimal], ...]
    state_layout_sha256: str
    model_sha256: str
    state_hex: str
    native_phase_calls: int

    def __post_init__(self):
        for name in ("checkpoint_id", "unit_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        for name in ("state_layout_sha256", "model_sha256"):
            validate_sha256(getattr(self, name))
        if self.history not in {"early", "late"} or self.checkpoint_seconds != D(300):
            raise ValueError("checkpoint has the wrong history or causal cutoff")
        if self.initial_soc not in {D("0.60"), D("0.70")} or self.native_phase_calls != 2:
            raise ValueError("checkpoint differs from assigned preparation or phase census")
        for name in ("initial_soc", "capacity_Ah", "temperature_K", "source_current_A"):
            validate_decimal(getattr(self, name), field_name=name)
        if self.source_current_A != (D(0) if self.history == "early" else D(1)):
            raise ValueError("checkpoint source-input ledger differs from history")
        if self.source_input_ledger != (("Ambient temperature [K]", D("293.15")), ("Current function [A]", self.source_current_A)):
            raise ValueError("checkpoint source-input ledger must retain exact sorted names, units and values")
        try:
            payload = bytes.fromhex(self.state_hex)
        except ValueError as error:
            raise ValueError("checkpoint state is not binary-exact f8 hex") from error
        if self.state_hex != payload.hex() or not payload or len(payload) % 8 or len(payload) > 4096 * 8:
            raise ValueError("checkpoint state encoding or bounded entry census differs")
        if any(not math.isfinite(value[0]) for value in struct.iter_unpack("<d", payload)):
            raise ValueError("checkpoint state contains nonfinite entries")


@dataclass(frozen=True, slots=True)
class BatteryCheckpointSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-checkpoint-summary"
    summary_id: str
    checkpoint: ObjectIdentity
    source: BatterySourceContract
    unit_id: str
    history: str
    checkpoint_seconds: Decimal
    soc: Decimal
    capacity_Ah: Decimal
    temperature_K: Decimal
    state_layout_sha256: str
    model_sha256: str
    offered_channels: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.summary_id, field_name="summary_id")
        if self.checkpoint.object_schema != BatteryCheckpoint.SCHEMA or self.checkpoint_seconds != D(300):
            raise ValueError("observable projection has the wrong source or cutoff")
        for name in ("state_layout_sha256", "model_sha256"):
            validate_sha256(getattr(self, name))
        if self.offered_channels != tuple(sorted((*REQUIRED_CHANNELS, *OBSERVABLE_CHANNELS))):
            raise ValueError("checkpoint metadata changes the declared channel census")
        for name in ("soc", "capacity_Ah", "temperature_K"):
            validate_decimal(getattr(self, name), field_name=name)


@dataclass(frozen=True, slots=True)
class BatteryTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-trace"
    trace_id: str
    checkpoint: ObjectIdentity
    unit_id: str
    history: str
    future_word: str
    route: str
    numerical_view: str
    clocks_seconds: tuple[Decimal, ...]
    voltage_V: tuple[Decimal, ...]
    capacity_Ah: tuple[Decimal, ...]
    temperature_K: tuple[Decimal, ...]
    exact_state_roundtrip: bool
    completed: bool
    reason_codes: tuple[str, ...]
    native_phase_calls: int
    source: BatterySourceContract

    def __post_init__(self):
        validate_stable_id(self.trace_id, field_name="trace_id")
        if self.checkpoint.object_schema != BatteryCheckpoint.SCHEMA:
            raise ValueError("trace must bind an actual checkpoint")
        if self.route not in {"REFERENCE", "FULL", "SOC", "TIGHTER"}:
            raise ValueError("trace has an unregistered reconstruction route")
        if self.numerical_view not in {"coarse", "tighter"}:
            raise ValueError("trace has an unregistered numerical view")
        if self.numerical_view != ("tighter" if self.route == "TIGHTER" else "coarse"):
            raise ValueError("trace numerical view differs from its registered route")
        if self.history not in {"early", "late"} or self.future_word not in {"hold", "early1", "late1", "early3"}:
            raise ValueError("trace contains an unassigned history or current word")
        if len({len(self.clocks_seconds), len(self.voltage_V), len(self.capacity_Ah), len(self.temperature_K)}) != 1:
            raise ValueError("battery trace channel census differs")
        if len(self.clocks_seconds) > 31 or tuple(sorted(set(self.clocks_seconds))) != self.clocks_seconds:
            raise ValueError("battery trace clocks are unordered or exceed their bound")
        for values in (self.clocks_seconds, self.voltage_V, self.capacity_Ah, self.temperature_K):
            for value in values:
                validate_decimal(value, field_name="battery_trace_quantity")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.completed and self.clocks_seconds != tuple(D(t) for t in range(300, 601, 10)):
            raise ValueError("complete battery trace is missing assigned clocks")
        if not self.completed and not self.reason_codes:
            raise ValueError("incomplete native result requires preserved reasons")
        if not 0 <= self.native_phase_calls <= 5:
            raise ValueError("native phase census exceeds declared prefix and future work")
        if self.completed and self.native_phase_calls != (5 if self.route == "REFERENCE" else 3):
            raise ValueError("complete trace has the wrong actual native phase census")


@dataclass(frozen=True, slots=True)
class BatteryRestartAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-restart-assessment"
    assessment_id: str
    supply: RequirementSupplyAssessment
    reference: ObjectIdentity
    full: ObjectIdentity
    soc: ObjectIdentity | None
    maximum_voltage_error_V: Decimal | None
    maximum_capacity_error_Ah: Decimal | None
    maximum_temperature_error_K: Decimal | None
    soc_maximum_voltage_error_V: Decimal | None
    soc_disposition: str
    capacity_control_passed: bool
    temperature_control_passed: bool
    soc_capacity_control_passed: bool | None = None
    soc_temperature_control_passed: bool | None = None

    def __post_init__(self):
        validate_stable_id(self.assessment_id, field_name="assessment_id")
        for name in ("maximum_voltage_error_V", "maximum_capacity_error_Ah", "maximum_temperature_error_K", "soc_maximum_voltage_error_V"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
                if value < 0:
                    raise ValueError("maximum discrepancy cannot be negative")
        if self.soc_disposition not in {"INADEQUATE", "ADEQUATE_WITHIN_TESTED_SCOPE", "UNEVALUABLE", "NOT_ASSIGNED"}:
            raise ValueError("SOC-only assessment must retain a declared scientific state")


@dataclass(frozen=True, slots=True)
class BatteryProcedureContribution(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-procedure-contribution"
    procedure_id: str
    disposition: AssessmentDisposition
    scope: ScientificConditionScope
    source: BatterySourceContract
    state_layout_sha256: str
    model_sha256: str
    required_channels: tuple[str, ...]
    assessed_future_words: tuple[str, ...]
    assessments: tuple[ObjectIdentity, ...]
    remaining_obligations: tuple[str, ...]
    finding: str

    def __post_init__(self):
        validate_stable_id(self.procedure_id, field_name="procedure_id")
        for name in ("state_layout_sha256", "model_sha256"):
            validate_sha256(getattr(self, name))
        if self.required_channels != REQUIRED_CHANNELS or self.assessed_future_words != ("hold",):
            raise ValueError("procedure silently changes channels or assessed future scope")
        require_sorted_unique_ids(self.assessments, attribute="object_id", field_name="assessments")
        if len(self.assessments) != 2:
            raise ValueError("procedure requires both assigned history assessments")
        if self.remaining_obligations != ("changed-future-fidelity", "new-instance-supply"):
            raise ValueError("development procedure must retain new-use obligations")


@dataclass(frozen=True, slots=True)
class BatteryAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-admission"
    admission_id: str
    supply: RequirementSupplyAssessment
    contribution_sha256: str
    procedure: ObjectIdentity
    checkpoint_summary: ObjectIdentity
    consumer_id: str
    permitted_channels: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.admission_id, field_name="admission_id")
        validate_sha256(self.contribution_sha256)
        if self.consumer_id not in {"C1", "C2"}:
            raise ValueError("unregistered scientific consumer")
        expected = tuple(sorted((*REQUIRED_CHANNELS, *OBSERVABLE_CHANNELS))) if self.consumer_id == "C1" else OBSERVABLE_CHANNELS
        if self.permitted_channels != expected:
            raise ValueError("consumer changes its allowed scientific channels")


@dataclass(frozen=True, slots=True)
class BatteryVoltageContrast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-voltage-contrast"
    contrast_id: str
    coarse_V: Decimal | None
    tighter_V: Decimal | None
    material_boundary_V: Decimal
    finding: str

    def __post_init__(self):
        validate_stable_id(self.contrast_id, field_name="contrast_id")
        for name in ("coarse_V", "tighter_V", "material_boundary_V"):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if self.material_boundary_V <= 0 or (self.finding != "UNEVALUABLE" and (self.coarse_V is None or self.tighter_V is None)):
            raise ValueError("an assessed voltage finding requires actual quantities and a positive frozen boundary")
        if self.finding not in {"RESOLVED_POSITIVE", "RESOLVED_NEGATIVE", "BOUNDED_NULL_OR_NONDISCRIMINATING", "UNEVALUABLE"}:
            raise ValueError("voltage contrast must retain a declared finding")


@dataclass(frozen=True, slots=True)
class BatteryFurtherProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/methods/battery-recursive-further-product"
    product_id: str
    supply: RequirementSupplyAssessment
    c1_admission: ObjectIdentity
    c2_admission: ObjectIdentity
    c1_path_disposition: AssessmentDisposition
    c1_c2_joint_disposition: AssessmentDisposition
    contrast_results: tuple[BatteryVoltageContrast, ...]
    maximum_forward_disagreement_V: Decimal | None
    assigned_unit_ids: tuple[str, ...]
    assigned_word_ids: tuple[str, ...]
    trace_census: tuple[ObjectIdentity, ...]
    restart_assessment_census: tuple[ObjectIdentity, ...]
    native_phase_calls: int
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.product_id, field_name="product_id")
        if self.assigned_unit_ids != ("battery-preparation-b",) or self.assigned_word_ids != ("early1", "early3", "hold", "late1"):
            raise ValueError("further product changes its exposed denominator or future census")
        require_sorted_unique_ids(self.contrast_results, attribute="contrast_id", field_name="contrast_results")
        require_sorted_unique_ids(self.trace_census, attribute="object_id", field_name="trace_census")
        require_sorted_unique_ids(self.restart_assessment_census, attribute="object_id", field_name="restart_assessment_census")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.maximum_forward_disagreement_V is not None:
            validate_decimal(self.maximum_forward_disagreement_V, field_name="maximum_forward_disagreement_V")
        if not 0 <= self.native_phase_calls <= 96:
            raise ValueError("further product exceeds frozen native phase census")
