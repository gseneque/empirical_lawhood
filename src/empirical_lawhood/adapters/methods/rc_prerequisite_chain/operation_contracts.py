# SPDX-License-Identifier: MPL-2.0
"""Typed ports for RC acquisition, policy, delivery and independent assessment."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.adapters.simulators.rc_ladder_response.contracts import (
    ResistorCapacitorLadderModelConfig, ResistorCapacitorLadderNativePanel,
    ResistorCapacitorLadderNumericalCheck,
)
from .contracts import (ARM_IDS, VARIANT_IDS, RCChainProtocol, RCPrerequisiteChainConfig,
    RCChainObservationExpectation, RCChainObservation, RCChainDecision, RCChainArmResult, _state, _reasons)


ARM_SLOTS = tuple((variant, arm) for variant in VARIANT_IDS
                  for arm in (ARM_IDS if variant == "adequate" else ("selected",)))
PREFIX = "empirical-lawhood/methods/rc-prerequisite-chain/operations/"
SOURCE_FAILURES = {(), ("NUMERICAL_EXECUTION_FAILED",), ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",)}


@dataclass(frozen=True, slots=True)
class RCSourceOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "source-config"
    config_id: str
    scientific_config: RCPrerequisiteChainConfig
    unit_id: str

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name="config_id")
        if self.unit_id not in {unit.unit_id for unit in self.scientific_config.units}:
            raise ValueError("RC operation changes its assigned scientific unit")


@dataclass(frozen=True, slots=True)
class RCDeliveryOperationConfig(RCSourceOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "delivery-config"


@dataclass(frozen=True, slots=True)
class RCMeasurementOperationConfig(RCSourceOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "measurement-config"


@dataclass(frozen=True, slots=True)
class RCUnitReductionConfig(RCSourceOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "unit-reduction-config"


@dataclass(frozen=True, slots=True)
class RCPolicyOperationConfig(CanonicalRecord):
    """Frozen constants and opaque bindings; no roster or native truth."""

    SCHEMA: ClassVar[str] = PREFIX + "policy-config"
    config_id: str
    scientific_config_sha256: str
    unit_id: str
    protocol: RCChainProtocol

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name="config_id")
        validate_stable_id(self.unit_id, field_name="unit_id")
        validate_sha256(self.scientific_config_sha256, field_name="scientific_config_sha256")


@dataclass(frozen=True, slots=True)
class RCObservationOperationConfig(RCPolicyOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "observations-config"


@dataclass(frozen=True, slots=True)
class RCAdmissionOperationConfig(RCPolicyOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "admission-config"


@dataclass(frozen=True, slots=True)
class RCCommitmentOperationConfig(RCPolicyOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "commitment-config"


@dataclass(frozen=True, slots=True)
class RCSupportOperationConfig(RCSourceOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "support-config"


@dataclass(frozen=True, slots=True)
class RCJoinedOperationConfig(RCSourceOperationConfig):
    SCHEMA: ClassVar[str] = PREFIX + "joined-config"


@dataclass(frozen=True, slots=True)
class RCSummaryOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "summary-config"
    config_id: str
    scientific_config: RCPrerequisiteChainConfig

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name="config_id")


@dataclass(frozen=True, slots=True)
class RCSourceEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "source-evidence"
    unit_id: str
    config_sha256: str
    measurement_source: ResistorCapacitorLadderModelConfig
    native_panels: tuple[ResistorCapacitorLadderNativePanel, ...]
    numerical_check: ResistorCapacitorLadderNumericalCheck | None
    failure_reason_codes: tuple[str, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        _panel_prefix(self.native_panels)
        if self.failure_reason_codes not in SOURCE_FAILURES:
            raise ValueError("RC source evidence has an undeclared failure")
        if not self.failure_reason_codes and (len(self.native_panels) != 2 or self.numerical_check is None):
            raise ValueError("RC completed source requires both native views")
        if self.failure_reason_codes == ("NUMERICAL_EXECUTION_FAILED",) and self.numerical_check is not None:
            raise ValueError("RC execution failure cannot invent a completed numerical check")
        if self.failure_reason_codes == ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",) and (
            len(self.native_panels) != 2 or self.numerical_check is None or self.numerical_check.converged):
            raise ValueError("RC source conformance failure requires its actual failed complete check")
        if not self.failure_reason_codes and not self.numerical_check.converged:
            raise ValueError("RC successful observer source requires numerical conformance")


@dataclass(frozen=True, slots=True)
class RCObserverExport(CanonicalRecord):
    """The acquisition's sensor export; never a selection-worker input."""

    SCHEMA: ClassVar[str] = PREFIX + "observer-export"
    expectation: RCChainObservationExpectation
    observed_sample_volts: Decimal | None
    source_failure_reason_codes: tuple[str, ...]

    def __post_init__(self):
        if self.source_failure_reason_codes not in SOURCE_FAILURES:
            raise ValueError("RC observer export has an undeclared source failure")
        if (self.observed_sample_volts is None) != bool(self.source_failure_reason_codes):
            raise ValueError("RC observer export confuses available sample and failed source")
        if self.observed_sample_volts is not None:
            validate_decimal(self.observed_sample_volts, field_name="observed_sample_volts")


@dataclass(frozen=True, slots=True)
class RCObservationVariant(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "observation-variant"
    variant_id: str
    observation: RCChainObservation | None

    def __post_init__(self):
        _variant(self.variant_id)


@dataclass(frozen=True, slots=True)
class RCObservationSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "observation-set"
    expectation: RCChainObservationExpectation
    reports: tuple[RCObservationVariant, ...]
    source_failure_reason_codes: tuple[str, ...]

    def __post_init__(self):
        _variants(self.reports)
        if self.source_failure_reason_codes not in SOURCE_FAILURES:
            raise ValueError("RC report set has an undeclared source failure")
        if self.source_failure_reason_codes and any(report.observation is not None for report in self.reports):
            raise ValueError("RC failed source cannot fabricate observer reports")


@dataclass(frozen=True, slots=True)
class RCAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "causal-admission"
    variant_id: str
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        _variant(self.variant_id)
        if self.disposition not in {"ADMITTED", "REFUSED", "UNEVALUABLE", "UNSUPPORTED"}:
            raise ValueError("RC causal admission has an unknown disposition")
        _reasons(self.reason_codes)
        if (self.disposition == "ADMITTED") != (not self.reason_codes):
            raise ValueError("RC causal admission must explain every refusal or unavailable input")


@dataclass(frozen=True, slots=True)
class RCAdmissionSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "admission-set"
    unit_id: str
    config_sha256: str
    observation_set_sha256: str
    admissions: tuple[RCAdmission, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.observation_set_sha256, field_name="observation_set_sha256")
        _variants(self.admissions)


@dataclass(frozen=True, slots=True)
class RCCommittedDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "committed-decision"
    variant_id: str
    decision: RCChainDecision

    def __post_init__(self):
        _variant(self.variant_id)


@dataclass(frozen=True, slots=True)
class RCCommitmentSet(CanonicalRecord):
    """All ten choices are one immutable product before any oracle assessment."""

    SCHEMA: ClassVar[str] = PREFIX + "commitment-set"
    unit_id: str
    config_sha256: str
    observation_set_sha256: str
    admission_set_sha256: str
    decisions: tuple[RCCommittedDecision, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.observation_set_sha256, field_name="observation_set_sha256")
        validate_sha256(self.admission_set_sha256, field_name="admission_set_sha256")
        _variants(self.decisions)


@dataclass(frozen=True, slots=True)
class RCNativeArmEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "native-arm-evidence"
    variant_id: str
    arm_id: str
    native_model: ResistorCapacitorLadderModelConfig | None
    native_panels: tuple[ResistorCapacitorLadderNativePanel, ...]
    numerical_check: ResistorCapacitorLadderNumericalCheck | None
    failure_reason_codes: tuple[str, ...]

    def __post_init__(self):
        _arm(self.variant_id, self.arm_id)
        _panel_prefix(self.native_panels)
        if self.failure_reason_codes not in {(), ("NUMERICAL_EXECUTION_FAILED",)}:
            raise ValueError("RC native arm has an undeclared numerical failure")
        if self.native_model is None:
            if self.native_panels or self.numerical_check is not None:
                raise ValueError("RC unexecuted native arm cannot fabricate completed views")
        elif self.failure_reason_codes:
            if self.numerical_check is not None:
                raise ValueError("RC numerical failure cannot invent a completed two-view check")
        elif len(self.native_panels) != 2 or self.numerical_check is None:
            raise ValueError("RC completed native arm requires both views and their numerical check")


@dataclass(frozen=True, slots=True)
class RCNativeDeliverySet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "native-delivery-set"
    unit_id: str
    config_sha256: str
    commitment_sha256: str
    arms: tuple[RCNativeArmEvidence, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.commitment_sha256, field_name="commitment_sha256")
        _arms(self.arms)


@dataclass(frozen=True, slots=True)
class RCMeasurementAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "measurement-assessment"
    variant_id: str
    state: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        _variant(self.variant_id)
        _state(self.state)
        _reasons(self.reason_codes)


@dataclass(frozen=True, slots=True)
class RCMeasurementAssessmentSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "measurement-assessment-set"
    unit_id: str
    config_sha256: str
    commitment_sha256: str
    assessments: tuple[RCMeasurementAssessment, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.commitment_sha256, field_name="commitment_sha256")
        _variants(self.assessments)


@dataclass(frozen=True, slots=True)
class RCSupportAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "support-assessment"
    variant_id: str
    arm_id: str
    prospective_lower_volts: Decimal | None
    prospective_upper_volts: Decimal | None
    prospective_support: bool | None
    actual_support: bool | None
    state: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        _arm(self.variant_id, self.arm_id)
        _state(self.state)
        _reasons(self.reason_codes)
        for name in ("prospective_lower_volts", "prospective_upper_volts"):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        for name in ("prospective_support", "actual_support"):
            if getattr(self, name) is not None and type(getattr(self, name)) is not bool:
                raise ValueError("RC support predicate must retain a typed Boolean")


@dataclass(frozen=True, slots=True)
class RCSupportAssessmentSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "support-assessment-set"
    unit_id: str
    config_sha256: str
    commitment_sha256: str
    assessments: tuple[RCSupportAssessment, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.commitment_sha256, field_name="commitment_sha256")
        _arms(self.assessments)


@dataclass(frozen=True, slots=True)
class RCJoinedAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "joined-assessment"
    variant_id: str
    arm_id: str
    result: RCChainArmResult

    def __post_init__(self):
        _arm(self.variant_id, self.arm_id)
        if self.result.arm_id != self.arm_id:
            raise ValueError("RC joined assessment substitutes its declared arm")


@dataclass(frozen=True, slots=True)
class RCJoinedAssessmentSet(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "joined-assessment-set"
    unit_id: str
    config_sha256: str
    commitment_sha256: str
    assessments: tuple[RCJoinedAssessment, ...]

    def __post_init__(self):
        _binding(self.unit_id, self.config_sha256)
        validate_sha256(self.commitment_sha256, field_name="commitment_sha256")
        _arms(self.assessments)


def _binding(unit_id, config_sha256):
    validate_stable_id(unit_id, field_name="unit_id")
    validate_sha256(config_sha256, field_name="config_sha256")


def _variants(values):
    if tuple(value.variant_id for value in values) != VARIANT_IDS:
        raise ValueError("RC operation drops, duplicates or reorders a declared variant")


def _variant(variant_id):
    if variant_id not in VARIANT_IDS:
        raise ValueError("RC operation changes its closed variant roster")


def _arm(variant_id, arm_id):
    if (variant_id, arm_id) not in ARM_SLOTS:
        raise ValueError("RC operation changes its closed arm roster")


def _panel_prefix(panels):
    if tuple(panel.view_id for panel in panels) not in {(), ("backward-euler",), ("backward-euler", "matrix-exponential")}:
        raise ValueError("RC raw native evidence changes its declared completed-view prefix")


def _arms(values):
    if tuple((value.variant_id, value.arm_id) for value in values) != ARM_SLOTS:
        raise ValueError("RC operation drops, duplicates or reorders a declared arm")
