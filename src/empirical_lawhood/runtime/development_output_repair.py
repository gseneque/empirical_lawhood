# SPDX-License-Identifier: MPL-2.0
"""Additive output reservations for exhausted PURE development calculations.

The authored plan, native attempts and original terminal remain immutable.
Only a separately authenticated repair may dispatch a larger output allowance;
the scientific task, worker, inputs and every other resource field stay exact.
"""
from dataclasses import dataclass, fields, replace
from pathlib import PurePath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from .artifacts import CanonicalTaskReceipt
from .plans import DevelopmentExecutionPlan
from .prepared_native_invocation import PreparedWorkerEnvironment
from .recursive_handoff import RecursiveImplementationBinding
from .recovery import DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, TaskRecoveryEvent


@dataclass(frozen=True, slots=True)
class DevelopmentOutputBudgetRepair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-output-budget-repair'

    repair_id: str
    owner_instruction_sha256: str
    execution_plan: ObjectIdentity
    original_index: ObjectIdentity
    original_terminal: ObjectIdentity
    refused_tasks: tuple[tuple[str, ObjectIdentity], ...]
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    unstarted_task_ids: tuple[str, ...]
    output_bytes: int
    controller: RecursiveImplementationBinding
    worker: RecursiveImplementationBinding
    worker_environment: PreparedWorkerEnvironment
    worker_source_root: str

    def __post_init__(self):
        validate_stable_id(self.repair_id)
        validate_sha256(self.owner_instruction_sha256)
        for value, kind in ((self.execution_plan, DevelopmentExecutionPlan),
                (self.original_index, DevelopmentRunRecoveryIndex),
                (self.original_terminal, DevelopmentRunRecoveryTerminalEvent)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('development output repair changes its original record contract')
        for rows, kind in ((self.refused_tasks, TaskRecoveryEvent), (self.completed_receipts, CanonicalTaskReceipt)):
            ids = tuple(key for key, _ in rows)
            if not ids or ids != tuple(sorted(set(ids))):
                raise ValueError('development output repair requires exact nonempty sorted task sets')
            for key, value in rows:
                validate_stable_id(key)
                if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                    raise ValueError('development output repair changes original failure or receipt identity')
        if self.unstarted_task_ids != tuple(sorted(set(self.unstarted_task_ids))):
            raise ValueError('development output repair repeats unstarted work')
        sets = tuple(set(values) for values in (dict(self.refused_tasks), dict(self.completed_receipts), self.unstarted_task_ids))
        if any(sets[i].intersection(sets[j]) for i in range(3) for j in range(i)):
            raise ValueError('development output repair task sets must be disjoint')
        for key in self.unstarted_task_ids:
            validate_stable_id(key)
        if type(self.output_bytes) is not int or not 0 < self.output_bytes <= 256 * 1024**2:
            raise ValueError('development output repair needs a bounded in-memory output reservation')
        for source in (self.controller, self.worker):
            if type(source) is not RecursiveImplementationBinding:
                raise TypeError('development output repair requires exact observed source bindings')
            source.__post_init__()
        if (self.controller.observed_git_head == self.worker.observed_git_head
                or self.controller.dependency_lock_sha256 != self.worker.dependency_lock_sha256):
            raise ValueError('development output repair needs a distinct controller and unchanged dependency lock')
        if type(self.worker_environment) is not PreparedWorkerEnvironment:
            raise TypeError('development output repair requires the original isolated worker environment')
        self.worker_environment.__post_init__()
        path = PurePath(self.worker_source_root)
        if not path.is_absolute() or '..' in path.parts:
            raise ValueError('development output repair needs an exact original worker source path')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)

    def task(self, original):
        """Only the selected output limit differs from the original task."""
        if original.task_id not in dict(self.refused_tasks):
            return original
        budget = original.capability.requested_resources
        if budget.output_bytes is None or budget.output_bytes >= self.output_bytes:
            raise ValueError('development output repair must increase a finite refused output allowance')
        return replace(original, capability=replace(original.capability,
            requested_resources=replace(budget, output_bytes=self.output_bytes)))

    def validate_plan(self, plan):
        if (type(plan) is not DevelopmentExecutionPlan
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != self.execution_plan
                or plan.implementation_commit != self.worker.observed_git_head
                or {row.task_id for row in plan.tasks} != {
                    *dict(self.refused_tasks), *dict(self.completed_receipts), *self.unstarted_task_ids}):
            raise ValueError('development output repair changes its complete original plan/source census')
        for task_id in dict(self.refused_tasks):
            original = plan.task(task_id)
            if original.maximum_attempts != 1:
                raise ValueError('development output repair requires an exhausted single-attempt calculation')
            self.task(original)


@dataclass(frozen=True, slots=True)
class DevelopmentOutputRepairRecoveryIndex(DevelopmentRunRecoveryIndex):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-output-repair-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-output-repair-terminal-event'
    REPAIR_TYPE: ClassVar[type] = DevelopmentOutputBudgetRepair

    repair: DevelopmentOutputBudgetRepair
    predecessor: DevelopmentRunRecoveryIndex

    @classmethod
    def derive(cls, plan, predecessor, repair):
        if type(predecessor) is not DevelopmentRunRecoveryIndex or type(repair) is not cls.REPAIR_TYPE:
            raise TypeError('development output repair requires its original development recovery index')
        predecessor.validate_plan(plan)
        repair.validate_plan(plan)
        if ObjectIdentity.from_record(predecessor.recovery_index_id, predecessor) != repair.original_index:
            raise ValueError('development output repair substitutes its original recovery wave')
        fresh = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=predecessor.run_id,
            wave_id='wave.' + repair.repair_id)
        completed = dict(repair.completed_receipts)
        bindings = []
        for binding in fresh.tasks:
            if binding.task_id in completed:
                binding = predecessor.task(binding.task_id)
            else:
                if binding.maximum_attempts != 1:
                    raise ValueError('development repair admits one attempt per pending task')
                candidate, = binding.attempts
                attempt = candidate.attempt_id.removesuffix('.attempt-001') + '.' + repair.repair_id + '.attempt-001'
                candidate = replace(candidate, attempt_id=attempt,
                    receipt_relative_path=f'runs/{fresh.run_id}/receipts/{binding.task_id}/{attempt}.json')
                binding = replace(binding, attempts=(candidate,))
            bindings.append(binding)
        values = {field.name: getattr(fresh, field.name) for field in fields(DevelopmentRunRecoveryIndex)}
        return cls(**{**values, 'tasks': tuple(bindings), 'terminal_event_schema': cls.TERMINAL_EVENT_SCHEMA},
            repair=repair, predecessor=predecessor)

    def validate_plan(self, plan):
        if self != type(self).derive(plan, self.predecessor, self.repair):
            raise ValueError('development output repair index changes its owning derivation')

    def event_owner(self, task_id):
        return self.predecessor if task_id in dict(self.repair.completed_receipts) else self


@dataclass(frozen=True, slots=True)
class DevelopmentOutputRepairTerminalEvent(DevelopmentRunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = DevelopmentOutputRepairRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = DevelopmentOutputRepairRecoveryIndex.SCHEMA
