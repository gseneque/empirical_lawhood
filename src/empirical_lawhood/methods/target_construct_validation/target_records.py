"""Scientific action, receiver and complete-unit records for target validation."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_nonempty, validate_stable_id

class TargetConstructValidationExecutionPhase(StrEnum):
    CANARY = "CANARY"
    DEVELOPMENT = "DEVELOPMENT"
    EVALUATION = "EVALUATION"


@dataclass(frozen=True, slots=True)
class TargetConstructValidationActionRealization(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/target-construct-validation/target-construct-validation-action-realization'

    realization_id: str
    native_action_id: str
    requested_value: Decimal
    accepted_value: Decimal
    applied_value: Decimal
    realized_value: Decimal
    requested_clock: Decimal
    accepted_clock: Decimal
    applied_clock: Decimal
    realized_clock: Decimal
    native_unit: str
    acceptance_rule: str

    def __post_init__(self) -> None:
        for name in ("realization_id", "native_action_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        for name in (
            "requested_value",
            "accepted_value",
            "applied_value",
            "realized_value",
            "requested_clock",
            "accepted_clock",
            "applied_clock",
            "realized_clock",
        ):
            validate_decimal(getattr(self, name), field_name=name)
        validate_nonempty(self.native_unit, field_name="native_unit")
        validate_nonempty(self.acceptance_rule, field_name="acceptance_rule")
        if not (
            self.requested_clock <= self.accepted_clock <= self.applied_clock <= self.realized_clock
        ):
            raise ValueError("action realization clocks are not causal")


@dataclass(frozen=True, slots=True)
class TargetConstructValidationReceiverValue(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/target-construct-validation/target-construct-validation-receiver-value'

    receiver_id: str
    value: Decimal
    native_unit: str
    finite: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.receiver_id, field_name="receiver_id")
        validate_decimal(self.value, field_name="value")
        validate_nonempty(self.native_unit, field_name="native_unit")
        if not self.finite:
            raise ValueError("nonfinite receiver values require a typed stopped condition")


@dataclass(frozen=True, slots=True)
class TargetConstructValidationNativeConditionResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/target-construct-validation/target-construct-validation-native-condition-result'

    condition_id: str
    denominator_value_id: str
    history_value_id: str
    native_action_id: str
    horizon_value_id: str
    action: TargetConstructValidationActionRealization
    receivers: tuple[TargetConstructValidationReceiverValue, ...]
    solver_step_count: int
    stopped: bool
    stop_code: str | None

    def __post_init__(self) -> None:
        for name in (
            "condition_id",
            "denominator_value_id",
            "history_value_id",
            "native_action_id",
            "horizon_value_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_ids(
            self.receivers,
            attribute="receiver_id",
            field_name="receivers",
        )
        if self.action.native_action_id != self.native_action_id:
            raise ValueError("condition and action ledger differ")
        if self.solver_step_count <= 0:
            raise ValueError("condition must report positive solver work")
        if self.stopped != (self.stop_code is not None):
            raise ValueError("condition stop status and code differ")


@dataclass(frozen=True, slots=True)
class TargetConstructValidationCompleteUnitResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/target-construct-validation/target-construct-validation-complete-unit-result'

    result_id: str
    target_id: str
    phase: TargetConstructValidationExecutionPhase
    complete_unit_id: str
    seed: int
    target_design: ObjectIdentity
    conditions: tuple[TargetConstructValidationNativeConditionResult, ...]
    condition_ids_sha256: str
    elapsed_seconds: Decimal
    simulator_version: str
    solver_id: str
    generator_response_count: int
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        for name in ("result_id", "target_id", "complete_unit_id", "solver_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.seed < 0:
            raise ValueError("complete-unit seed must be nonnegative")
        require_sorted_unique_ids(
            self.conditions,
            attribute="condition_id",
            field_name="conditions",
        )
        validate_nonempty(self.simulator_version, field_name="simulator_version")
        validate_decimal(self.elapsed_seconds, field_name="elapsed_seconds")
        expected_digest = sha256(
            ("\n".join(value.condition_id for value in self.conditions) + "\n").encode("ascii")
        ).hexdigest()
        if self.condition_ids_sha256 != expected_digest:
            raise ValueError("complete-unit condition digest differs")
        if self.generator_response_count != len(self.conditions):
            raise ValueError("generator response count is not condition-derived")
        expected_access = {
            TargetConstructValidationExecutionPhase.CANARY: OutcomeAccess.DEVELOPMENT_VISIBLE,
            TargetConstructValidationExecutionPhase.DEVELOPMENT: OutcomeAccess.DEVELOPMENT_VISIBLE,
            TargetConstructValidationExecutionPhase.EVALUATION: OutcomeAccess.EVALUATION_SEALED,
        }[self.phase]
        if self.outcome_access is not expected_access:
            raise ValueError("complete-unit phase and outcome access differ")


__all__ = ['TargetConstructValidationExecutionPhase', 'TargetConstructValidationActionRealization', 'TargetConstructValidationReceiverValue', 'TargetConstructValidationNativeConditionResult', 'TargetConstructValidationCompleteUnitResult']
