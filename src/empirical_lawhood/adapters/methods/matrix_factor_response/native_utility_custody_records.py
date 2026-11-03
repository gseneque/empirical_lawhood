# SPDX-License-Identifier: MPL-2.0
"""Distinct whole-roster E2 read products; missing roots never acquire a score."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recovery import (
    RecoveryTerminalAttempt, RecoveryTerminalDisposition, TaskRecoveryDisposition, TaskRecoveryEvent,
    DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent,
)


class _Identity:
    __slots__ = ()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class NativeUtilityCustodyGap(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/native-utility-custody-gap"
    task: ObjectIdentity
    terminal_attempt: RecoveryTerminalAttempt
    recovery_event: TaskRecoveryEvent
    native_contact: NativeEffectContact | None
    disposition: str

    def __post_init__(self):
        if (type(self.task) is not ObjectIdentity
                or type(self.terminal_attempt) is not RecoveryTerminalAttempt
                or type(self.recovery_event) is not TaskRecoveryEvent
                or self.native_contact is not None and type(self.native_contact) is not NativeEffectContact):
            raise TypeError("native E2 custody gap requires exact original typed custody")
        summary, event = self.terminal_attempt, self.recovery_event
        if (summary.task_id != self.task.object_id or event.task_id != self.task.object_id
                or summary.disposition not in (RecoveryTerminalDisposition.FAILED, RecoveryTerminalDisposition.BLOCKED)
                or summary.receipt_id is not None or summary.receipt_sha256 is not None
                or event.receipt_id is not None or event.output_materialization_ids
                or event.reason_codes != (summary.reason_code,)):
            raise ValueError("native E2 gap invents successful custody or changes its exact task/reason")
        if event.disposition is TaskRecoveryDisposition.NOT_ATTEMPTED:
            if (summary.disposition is not RecoveryTerminalDisposition.BLOCKED or event.attempt_id is not None
                    or self.disposition not in ("DEPENDENCY_BLOCKED", "NO_CONTACT_RESOURCE_REFUSAL", "NO_CONTACT_PRECONDITION_BLOCK")
                    or self.native_contact is not None):
                raise ValueError("native E2 nonattempt gap invents native contact or an entered attempt")
        elif (event.attempt_id != summary.attempt_id
                or event.disposition.value != summary.disposition.value):
            raise ValueError("native E2 entered gap substitutes its original attempt")
        if self.native_contact is not None:
            contact = self.native_contact
            if (self.disposition not in ("UNKNOWN_PARENT_COMPLETION", "CONTACTED_PARENT_NON_SUCCESS")
                    or (self.disposition == "UNKNOWN_PARENT_COMPLETION") != (summary.reason_code == "unknown-completion")
                    or contact.task_id != summary.task_id or contact.attempt_id != summary.attempt_id
                    or contact.run_id != event.run_id):
                raise ValueError("native E2 contacted gap changes its exact UNKNOWN ancestry")
        elif self.disposition in ("UNKNOWN_PARENT_COMPLETION", "CONTACTED_PARENT_NON_SUCCESS"):
            raise ValueError("native E2 UNKNOWN gap lacks its original authenticated native contact")
        if self.disposition == "NO_CONTACT_RESOURCE_REFUSAL":
            if (self.native_contact is not None or summary.reason_code != "resource-computability-unavailable"
                    or event.disposition not in (TaskRecoveryDisposition.BLOCKED, TaskRecoveryDisposition.NOT_ATTEMPTED)):
                raise ValueError("native E2 no-contact resource gap changes its actual refusal")
        elif self.disposition == "NO_CONTACT_OPERATIONAL_FAILURE":
            if self.native_contact is not None or event.disposition is not TaskRecoveryDisposition.FAILED:
                raise ValueError("native E2 failed gap changes its actual failed event")
        elif self.disposition == "NO_CONTACT_PRECONDITION_BLOCK":
            if (self.native_contact is not None or summary.disposition is not RecoveryTerminalDisposition.BLOCKED
                    or summary.reason_code in ("unknown-completion", "resource-computability-unavailable")):
                raise ValueError("native E2 precondition gap hides contact or changes its actual reason")
        elif self.disposition == "DEPENDENCY_BLOCKED":
            if summary.reason_code not in ("dependency-blocked", "dependency-failed", "dependency-not-succeeded"):
                raise ValueError("native E2 dependent gap changes its actual dependency reason")
        elif self.disposition not in ("UNKNOWN_PARENT_COMPLETION", "CONTACTED_PARENT_NON_SUCCESS"):
            raise ValueError("native E2 gap has no supported closed operational disposition")


@dataclass(frozen=True, slots=True)
class NativeUtilityMissingRoot(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/native-utility-missing-root"
    record_id: str
    specification: ObjectIdentity
    acquisition: ObjectIdentity
    root_id: str
    unit_id: str
    source: ObjectIdentity
    gaps: tuple[NativeUtilityCustodyGap, ...]
    usable: bool = False
    success: bool = False

    def __post_init__(self):
        for name in (self.record_id, self.root_id, self.unit_id):
            validate_stable_id(name)
        r.exact_reference(self.specification, r.NativeUtilitySpecification)
        r.exact_reference(self.acquisition, r.NativeUtilityAcquisitionSeal)
        r.exact_reference(self.source, r.ScheduledSource)
        if self.usable is not False or self.success is not False:
            raise ValueError("native E2 missing root can only be unusable and a nonsuccess")
        if (type(self.gaps) is not tuple or not self.gaps
                or any(type(value) is not NativeUtilityCustodyGap for value in self.gaps)
                or tuple(value.task.object_id for value in self.gaps) != tuple(sorted({value.task.object_id for value in self.gaps}))):
            raise ValueError("native E2 missing root omits or duplicates its closed custody gaps")
        for value in self.gaps:
            value.__post_init__()


@dataclass(frozen=True, slots=True)
class NativeUtilityCustodyAssessment(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/native-utility-custody-assessment"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    acquisition: ObjectIdentity
    run_id: str
    execution_plan: ObjectIdentity
    recovery_index: ObjectIdentity
    operational_terminal: ObjectIdentity
    operational_status: str
    outcomes: tuple[r.NativeUtilityOutcome, ...]
    missing_roots: tuple[NativeUtilityMissingRoot, ...]
    assigned_units: int
    usable_units: int
    successes: int
    tail_numerator: int
    tail_denominator: int
    conditional_criterion_met: bool
    scientific_status: str = "UNEVALUABLE"
    qualification: str = "NOT_ESTABLISHED"
    sampling_warrant: str = "NOT_ESTABLISHED"
    numerical_scope: str = "FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CONTINUUM_ERROR_ENCLOSURE"
    amended: r.NativeUtilityAmendedInference | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.run_id)
        r.exact_reference(self.specification, r.NativeUtilitySpecification)
        r.exact_reference(self.acquisition, r.NativeUtilityAcquisitionSeal)
        for value, kind in ((self.execution_plan, DevelopmentExecutionPlan),
                (self.recovery_index, DevelopmentRunRecoveryIndex),
                (self.operational_terminal, DevelopmentRunRecoveryTerminalEvent)):
            r.exact_reference(value, kind)
        if self.operational_status not in ("BLOCKED", "FAILED"):
            raise ValueError("native E2 custody-aware assessment requires closed unsuccessful operational custody")
        require_sorted_unique_ids(self.outcomes, attribute="unit_id", field_name="actual E2 outcomes")
        require_sorted_unique_ids(self.missing_roots, attribute="unit_id", field_name="missing E2 roots")
        if (any(type(value) is not r.NativeUtilityOutcome for value in self.outcomes)
                or any(type(value) is not NativeUtilityMissingRoot for value in self.missing_roots)):

            raise ValueError("native E2 custody assessment substitutes actual or missing root records")
        all_rows = (*self.outcomes, *self.missing_roots)
        if (not all_rows or len({value.root_id for value in all_rows}) != len(all_rows)
                or len({value.unit_id for value in all_rows}) != len(all_rows)
                or any((value.specification, value.acquisition) != (self.specification, self.acquisition) for value in all_rows)
                or type(self.assigned_units) is not int or self.assigned_units != len(all_rows)
                or type(self.usable_units) is not int or self.usable_units != sum(value.usable for value in self.outcomes)
                or type(self.successes) is not int or self.successes != sum(value.success for value in self.outcomes)
                or type(self.tail_numerator) is not int or type(self.tail_denominator) is not int
                or not 0 <= self.tail_numerator <= self.tail_denominator or self.tail_denominator < 1
                or type(self.conditional_criterion_met) is not bool
                or (self.scientific_status, self.qualification, self.sampling_warrant, self.numerical_scope) !=
                    ("UNEVALUABLE", "NOT_ESTABLISHED", "NOT_ESTABLISHED", "FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CONTINUUM_ERROR_ENCLOSURE")):
            raise ValueError("native E2 custody assessment thins its denominator, hides missingness or invents qualification")
        for row in all_rows:
            row.__post_init__()
        if self.amended is not None:
            if type(self.amended) is not r.NativeUtilityAmendedInference:
                raise TypeError('closed amended E2 requires its complete two-question inference')
            self.amended.__post_init__()
            self.amended.validate_outcomes(self.outcomes, tuple(row.unit_id for row in self.missing_roots))
            structural = self.amended.structural_advantage
            if ((self.successes, self.tail_numerator, self.tail_denominator, self.conditional_criterion_met) !=
                    (structural.successes, structural.tail_numerator, structural.tail_denominator, structural.criterion_met)):
                raise ValueError('closed amended E2 changes its complete assigned structural denominator')
        elif any(value.amended is not None for value in self.outcomes):
            raise ValueError('closed amended E2 drops one or both primary questions')
