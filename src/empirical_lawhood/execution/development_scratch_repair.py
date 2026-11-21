# SPDX-License-Identifier: MPL-2.0
"""Additive attempts for PURE calculations refused by retained empty scratch.

The original task budgets, inputs, outcomes and receipt identities stay exact.
This record supplies no native-effect retry or scientific qualification.
"""
from dataclasses import dataclass
from pathlib import PurePath
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt, validate_relative_locator
from empirical_lawhood.execution.development_controller_repair import DevelopmentControllerRepair
from empirical_lawhood.execution.development_output_repair import DevelopmentOutputRepairRecoveryIndex
from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
from empirical_lawhood.execution.prepared_native_invocation import PreparedWorkerEnvironment
from empirical_lawhood.execution.recovery import DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, TaskRecoveryEvent
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding


@dataclass(frozen=True, slots=True)
class DevelopmentScratchRepair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-scratch-repair'

    repair_id: str
    owner_instruction_sha256: str
    execution_plan: ObjectIdentity
    original_index: ObjectIdentity
    original_terminal: ObjectIdentity
    original_controls: tuple[tuple[str, int | None, str | None], ...]
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    refused_tasks: tuple[tuple[str, ObjectIdentity], ...]
    pending_task_ids: tuple[str, ...]
    refused_scratch_paths: tuple[tuple[str, str], ...]
    controller: RecursiveImplementationBinding
    worker: RecursiveImplementationBinding
    worker_environment: PreparedWorkerEnvironment
    worker_source_root: str
    worker_package_root: str

    def __post_init__(self):
        validate_stable_id(self.repair_id)
        validate_sha256(self.owner_instruction_sha256)
        for pin, kind in ((self.execution_plan, DevelopmentExecutionPlan),
                (self.original_index, DevelopmentRunRecoveryIndex),
                (self.original_terminal, DevelopmentRunRecoveryTerminalEvent)):
            DevelopmentControllerRepair._pin(pin, kind)
        paths = tuple(row[0] for row in self.original_controls)
        if not paths or paths != tuple(sorted(set(paths))):
            raise ValueError('scratch repair requires its complete original control census')
        for path, size, digest in self.original_controls:
            validate_relative_locator(path)
            if size is None:
                if digest is not None:
                    raise ValueError('absent original controls cannot carry a digest')
            else:
                if type(size) is not int or size <= 0:
                    raise ValueError('original controls require an exact positive size')
                validate_sha256(digest)
        for rows, kind in ((self.completed_receipts, CanonicalTaskReceipt), (self.refused_tasks, TaskRecoveryEvent)):
            if not rows:
                raise ValueError('scratch repair requires retained success and original resource refusals')
            DevelopmentControllerRepair._ids(tuple(key for key, _ in rows))
            for _, pin in rows:
                DevelopmentControllerRepair._pin(pin, kind)
        DevelopmentControllerRepair._ids(self.pending_task_ids)
        completed, refused, pending = set(dict(self.completed_receipts)), set(dict(self.refused_tasks)), set(self.pending_task_ids)
        if completed & refused or completed & pending or refused & pending:
            raise ValueError('scratch repair task categories must be disjoint')
        if tuple(key for key, _ in self.refused_scratch_paths) != tuple(dict(self.refused_tasks)):
            raise ValueError('scratch repair must retain every refused original scratch path')
        for _, path in self.refused_scratch_paths:
            validate_relative_locator(path)
        for source in (self.controller, self.worker):
            if type(source) is not RecursiveImplementationBinding:
                raise TypeError('scratch repair requires exact original worker and controller sources')
            source.__post_init__()
        if (self.controller.observed_git_head == self.worker.observed_git_head
                or self.controller.dependency_lock_sha256 != self.worker.dependency_lock_sha256):
            raise ValueError('scratch repair requires a distinct controller and unchanged dependency lock')
        if type(self.worker_environment) is not PreparedWorkerEnvironment:
            raise TypeError('scratch repair requires its exact frozen worker environment')
        self.worker_environment.__post_init__()
        for value in (self.worker_source_root, self.worker_package_root):
            path = PurePath(value)
            if not path.is_absolute() or '..' in path.parts:
                raise ValueError('scratch repair requires absolute original worker paths')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)

    def task(self, original):
        """A scratch repair changes no scientific task or resource allowance."""
        return original

    def validate_plan(self, plan):
        if (type(plan) is not DevelopmentExecutionPlan
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != self.execution_plan
                or plan.implementation_commit != self.worker.observed_git_head
                or {task.task_id for task in plan.tasks} != {
                    *dict(self.completed_receipts), *dict(self.refused_tasks), *self.pending_task_ids}):
            raise ValueError('scratch repair changes its complete original plan or source')
        for task_id in (*dict(self.refused_tasks), *self.pending_task_ids):
            if plan.task(task_id).maximum_attempts != 1:
                raise ValueError('scratch repair requires one original attempt per unfinished calculation')


@dataclass(frozen=True, slots=True)
class DevelopmentScratchRepairRecoveryIndex(DevelopmentOutputRepairRecoveryIndex):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-scratch-repair-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-scratch-repair-terminal-event'
    REPAIR_TYPE: ClassVar[type] = DevelopmentScratchRepair

    repair: DevelopmentScratchRepair


@dataclass(frozen=True, slots=True)
class DevelopmentScratchRepairTerminalEvent(DevelopmentRunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = DevelopmentScratchRepairRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = DevelopmentScratchRepairRecoveryIndex.SCHEMA
