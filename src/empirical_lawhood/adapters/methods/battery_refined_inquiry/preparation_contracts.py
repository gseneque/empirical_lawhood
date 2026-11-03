# SPDX-License-Identifier: MPL-2.0
"""Additive initial-preparation records; historical thermal records stay exact."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import math
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_strings,
    validate_decimal,
    validate_sha256,
    validate_stable_id,
)

D = Decimal


class ObservationKind(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class PreparationProtocol(CanonicalRecord):
    """Prospective full-output preparation contract, separate from precision gates.

    These weights concern initial preparation and numerical representation. They
    neither change the retained 1 s / 1 mV / .01 K qualification gates nor supply
    evidence about an earlier unobserved initializer.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/protocol"
    protocol_id: str
    configuration: ObjectIdentity
    source: ObjectIdentity
    producing_provenance: ObjectIdentity
    parameter_source: str
    model_family: str
    electrode_points: int
    particle_points: int
    initial_temperature_k: Decimal
    source_members: tuple[tuple[str, str], ...]
    requested_soc: Decimal = D("0.30")
    initial_clock_s: Decimal = D(0)
    capacity_origin_ah: Decimal = D(0)
    throughput_origin_ah: Decimal = D(0)
    reference_temperature_k: Decimal = D("298.15")
    ocp_clipping_tolerance: Decimal = D("1e-10")
    endpoint_residual_tolerance_v: Decimal = D("1e-7")
    scalar_atol: Decimal = D("1e-8")
    state_atol: Decimal = D("1e-8")
    state_rtol: Decimal = D("1e-7")
    derived_initial_state_allowed: bool = False
    derivative_requirement: str = "RETAIN_IF_RETURNED;NOT_AN_ACCURACY_CLAIM"

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if self.parameter_source not in {"Chen2020", "ORegan2022"} or self.model_family not in {"SPMe", "DFN"}:
            raise ValueError("preparation protocol changes its supported source/family")
        if self.producing_provenance.object_schema != "empirical-lawhood/kernel/numerical-producing-provenance":
            raise ValueError("preparation requires actual producing provenance")
        if any(type(n) is not int or n < 2 for n in (self.electrode_points, self.particle_points)):
            raise ValueError("preparation requires the complete selected mesh")
        if self.source_members != tuple(sorted(set(self.source_members))) or not self.source_members:
            raise ValueError("preparation source members are missing or reordered")
        if len({name for name, _ in self.source_members}) != len(self.source_members):
            raise ValueError("preparation source member names overlap")
        for name, digest in self.source_members:
            if not name or name.startswith("/") or ".." in name.split("/"):
                raise ValueError("preparation source member is not relative")
            validate_sha256(digest)
        for name in ("requested_soc", "initial_clock_s", "capacity_origin_ah", "throughput_origin_ah",
                     "reference_temperature_k", "initial_temperature_k", "ocp_clipping_tolerance",
                     "endpoint_residual_tolerance_v", "scalar_atol", "state_atol", "state_rtol"):
            validate_decimal(getattr(self, name), field_name=name)
        if (self.requested_soc != D("0.30") or self.initial_clock_s != 0
                or self.capacity_origin_ah != 0 or self.throughput_origin_ah != 0
                or self.reference_temperature_k != D("298.15") or self.ocp_clipping_tolerance != D("1e-10")):
            raise ValueError("preparation changes selected SOC/origins/reference/OCP semantics")
        if min(self.endpoint_residual_tolerance_v, self.scalar_atol, self.state_atol, self.state_rtol) <= 0:
            raise ValueError("preparation numerical weights must be positive")
        if type(self.derived_initial_state_allowed) is not bool or self.derived_initial_state_allowed:
            raise ValueError("this method requires an observed full-output initial state")
        if self.derivative_requirement != "RETAIN_IF_RETURNED;NOT_AN_ACCURACY_CLAIM":
            raise ValueError("derivative accuracy requires its own assessed method")


@dataclass(frozen=True, slots=True)
class StateBlock(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/state-block"
    role: str
    variable_name: str
    start: int
    stop: int
    scale: Decimal
    reference: Decimal
    domains: tuple[str, ...]

    def __post_init__(self):
        if (not self.role or not self.variable_name or type(self.start) is not int or type(self.stop) is not int
                or self.start < 0 or self.stop <= self.start):
            raise ValueError("state block loses its complete ordered owning slice")
        validate_decimal(self.scale, field_name="scale")
        validate_decimal(self.reference, field_name="reference")
        if self.scale <= 0:
            raise ValueError("state scale must be positive")


@dataclass(frozen=True, slots=True)
class ProcessedInitialStateLayout(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/processed-state-layout"
    layout_id: str
    protocol: ObjectIdentity
    model_expression_sha256: str
    initial_conditions_sha256: str
    differential_count: int
    algebraic_count: int
    blocks: tuple[StateBlock, ...]
    electrolyte_child_slices: tuple[tuple[str, int, int], ...]
    observed_from_built_model: bool

    def __post_init__(self):
        validate_stable_id(self.layout_id)
        validate_sha256(self.model_expression_sha256)
        validate_sha256(self.initial_conditions_sha256)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA:
            raise ValueError("layout substitutes its preparation protocol")
        if (type(self.differential_count) is not int or type(self.algebraic_count) is not int
                or min(self.differential_count, self.algebraic_count) < 1):
            raise ValueError("layout omits complete RHS/algebraic dimensions")
        if type(self.observed_from_built_model) is not bool:
            raise ValueError("layout observation kind is required")
        previous = 0
        roles = set()
        for block in self.blocks:
            if type(block) is not StateBlock or block.start != previous or block.role in roles:
                raise ValueError("layout owning rows overlap, reorder or omit state")
            previous = block.stop
            roles.add(block.role)
        if previous != self.differential_count + self.algebraic_count:
            raise ValueError("layout owning slices omit the full state denominator")
        electrolyte = next((b for b in self.blocks if b.role == "electrolyte"), None)
        if electrolyte is None or tuple(row[0] for row in self.electrolyte_child_slices) != ("negative", "separator", "positive"):
            raise ValueError("layout omits the complete electrolyte alias census")
        previous = electrolyte.start
        for _, start, stop in self.electrolyte_child_slices:
            if type(start) is not int or type(stop) is not int or start != previous or stop <= start:
                raise ValueError("electrolyte aliases overlap, reorder or omit state")
            previous = stop
        if previous != electrolyte.stop:
            raise ValueError("electrolyte aliases change the owning denominator")


@dataclass(frozen=True, slots=True)
class StateObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/state-observation"
    observation_id: str
    protocol: ObjectIdentity
    layout: ObjectIdentity
    role: str
    kind: ObservationKind
    model_clock_s: Decimal | None
    scaled_values: tuple[Decimal, ...]
    binary64_hex: tuple[str, ...]
    producing_evidence: tuple[ObjectIdentity, ...]
    derivation: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.observation_id)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA or self.layout.object_schema != ProcessedInitialStateLayout.SCHEMA:
            raise ValueError("state observation substitutes its protocol/layout")
        if self.role not in {"requested-initial", "actual-initial", "actual-terminal", "initial-derivative", "terminal-derivative"}:
            raise ValueError("state observation changes its scientific role")
        if type(self.kind) is not ObservationKind:
            raise ValueError("state observation must retain its availability")
        if self.kind is ObservationKind.UNAVAILABLE:
            if self.scaled_values or self.binary64_hex or self.model_clock_s is not None or self.derivation is not None:
                raise ValueError("unavailable observation invents a state or clock")
            return
        if not self.scaled_values or len(self.scaled_values) != len(self.binary64_hex) or not self.producing_evidence:
            raise ValueError("state observation omits values, binary representation or custody")
        validate_decimal(self.model_clock_s, field_name="model_clock_s")
        for value, bits in zip(self.scaled_values, self.binary64_hex, strict=True):
            validate_decimal(value, field_name="scaled_state")
            observed = float.fromhex(bits)
            if not math.isfinite(observed) or float(value).hex() != bits or observed.hex() != bits:
                raise ValueError("state observation substitutes its observed binary64 values")
        if (self.kind is ObservationKind.DERIVED) != (self.derivation is not None):
            raise ValueError("derived state requires its explicit derivation; observed state cannot invent one")


@dataclass(frozen=True, slots=True)
class InitialElectrodePreparationWitness(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/electrode-witness"
    witness_id: str
    protocol: ObjectIdentity
    initializer_dispositions: tuple[str, ...]
    initializer_evidence: tuple[ObjectIdentity, ...]
    particle_lithium_capacity_ah: Decimal
    negative_electrode_capacity_ah: Decimal
    positive_electrode_capacity_ah: Decimal
    usable_capacity_ah: Decimal
    faraday_constant: Decimal
    x0: Decimal
    x100: Decimal
    y0: Decimal
    y100: Decimal
    assigned_negative_concentration: Decimal
    assigned_positive_concentration: Decimal
    pre_soc_negative_concentration: Decimal
    pre_soc_positive_concentration: Decimal
    reference_temperature_k: Decimal
    lower_voltage_v: Decimal
    upper_voltage_v: Decimal
    ocp_clipping_tolerance: Decimal
    exact_min_max: bool
    known_value: str = "cyclable lithium capacity"
    direction: str = "NONE"

    def __post_init__(self):
        validate_stable_id(self.witness_id)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA:
            raise ValueError("electrode witness substitutes its protocol")
        if len(self.initializer_dispositions) != len(self.initializer_evidence):
            raise ValueError("electrode witness loses initializer/fallback evidence census")
        if any(value not in {"RETURNED", "TECHNICAL_FAILURE", "UNKNOWN_COMPLETION", "NOT_ENTERED"} for value in self.initializer_dispositions):
            raise ValueError("electrode witness invents initializer completion")
        for name in ("particle_lithium_capacity_ah", "negative_electrode_capacity_ah", "positive_electrode_capacity_ah",
                     "usable_capacity_ah", "faraday_constant", "x0", "x100", "y0", "y100", "assigned_negative_concentration",
                     "assigned_positive_concentration", "pre_soc_negative_concentration", "pre_soc_positive_concentration",
                     "reference_temperature_k", "lower_voltage_v", "upper_voltage_v", "ocp_clipping_tolerance"):
            validate_decimal(getattr(self, name), field_name=name)
        if type(self.exact_min_max) is not bool:
            raise ValueError("electrode witness omits actual min/max settings")


@dataclass(frozen=True, slots=True)
class PreparedTraceJoin(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/trace-join"
    join_id: str
    trace: ObjectIdentity
    protocol: ObjectIdentity
    witness: ObjectIdentity
    layout: ObjectIdentity
    requested_initial: ObjectIdentity
    actual_initial: ObjectIdentity
    producing_receipt_sha256: str

    def __post_init__(self):
        validate_stable_id(self.join_id)
        validate_sha256(self.producing_receipt_sha256)
        if (self.protocol.object_schema != PreparationProtocol.SCHEMA
                or self.witness.object_schema != InitialElectrodePreparationWitness.SCHEMA
                or self.layout.object_schema != ProcessedInitialStateLayout.SCHEMA
                or any(row.object_schema != StateObservation.SCHEMA for row in (self.requested_initial, self.actual_initial))):
            raise ValueError("preparation join substitutes its exact operand roles")


@dataclass(frozen=True, slots=True)
class InitialPreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/assessment"
    assessment_id: str
    trace: ObjectIdentity
    join: ObjectIdentity | None
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]
    checked_state_components: int
    maximum_scaled_state_residual: Decimal | None
    algorithm: str = "independent-source-OCP-ball-proof-and-pointwise-initial-state-v1"
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if type(self.disposition) is not AssessmentDisposition or (self.disposition is not AssessmentDisposition.SATISFIED and not self.reason_codes):
            raise ValueError("preparation assessment loses an adverse or uncertain outcome")
        if type(self.checked_state_components) is not int or self.checked_state_components < 0:
            raise ValueError("preparation assessment loses pointwise denominator")
        if self.maximum_scaled_state_residual is not None:
            validate_decimal(self.maximum_scaled_state_residual, field_name="maximum_scaled_state_residual")
        if self.algorithm != "independent-source-OCP-ball-proof-and-pointwise-initial-state-v1" or self.physical_qualification:
            raise ValueError("preparation assessment changes its algorithm or evidence ceiling")


def identity(record, object_id):
    return ObjectIdentity.from_record(object_id, record)
