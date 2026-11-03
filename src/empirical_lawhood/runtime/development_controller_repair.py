# SPDX-License-Identifier: MPL-2.0
"""Continue an interrupted DEV graph with its original numerical workers."""

from dataclasses import dataclass, replace
from pathlib import PurePath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from .artifacts import CanonicalTaskReceipt, validate_relative_locator
from .development_output_repair import DevelopmentOutputRepairRecoveryIndex
from .plans import DevelopmentExecutionPlan
from .prepared_native_invocation import PreparedWorkerEnvironment
from .recovery import DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, TaskRecoveryEvent
from .recursive_handoff import RecursiveImplementationBinding


@dataclass(frozen=True, slots=True)
class DevelopmentControllerRepair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-controller-repair'

    repair_id: str
    owner_instruction_sha256: str
    execution_plan: ObjectIdentity
    original_index: ObjectIdentity
    original_terminal: ObjectIdentity | None
    original_controls: tuple[tuple[str, int | None, str | None], ...]
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    completed_native_contacts: tuple[tuple[str, ObjectIdentity], ...]
    refused_tasks: tuple[tuple[str, ObjectIdentity], ...]
    pending_task_ids: tuple[str, ...]
    uncontacted_native_task_ids: tuple[str, ...]
    output_task_ids: tuple[str, ...]
    output_bytes: int
    controller: RecursiveImplementationBinding
    worker: RecursiveImplementationBinding
    worker_environment: PreparedWorkerEnvironment
    worker_source_root: str

    def __post_init__(self):
        from .native_effects import NativeEffectContact
        validate_stable_id(self.repair_id)
        validate_sha256(self.owner_instruction_sha256)
        for value, kind in ((self.execution_plan, DevelopmentExecutionPlan),
                (self.original_index, DevelopmentRunRecoveryIndex)):
            self._pin(value, kind)
        if self.original_terminal is not None:
            self._pin(self.original_terminal, DevelopmentRunRecoveryTerminalEvent)
        paths = tuple(row[0] for row in self.original_controls)
        if not paths or paths != tuple(sorted(set(paths))):
            raise ValueError('development controller repair requires its complete sorted original control census')
        for path, size, digest in self.original_controls:
            validate_relative_locator(path)
            if size is None:
                if digest is not None:
                    raise ValueError('absent original controls cannot carry a digest')
            else:
                if type(size) is not int or size <= 0:
                    raise ValueError('original controls require their exact positive size')
                validate_sha256(digest)
        for rows, kind in ((self.completed_receipts, CanonicalTaskReceipt),
                (self.completed_native_contacts, NativeEffectContact), (self.refused_tasks, TaskRecoveryEvent)):
            ids = tuple(key for key, _ in rows)
            self._ids(ids)
            for _, value in rows:
                self._pin(value, kind)
        for ids in (self.pending_task_ids, self.uncontacted_native_task_ids, self.output_task_ids):
            self._ids(ids)
        completed, refused, pending = set(dict(self.completed_receipts)), set(dict(self.refused_tasks)), set(self.pending_task_ids)
        if not completed or completed & refused or completed & pending or refused & pending:
            raise ValueError('development controller repair requires disjoint complete task categories')
        if not set(dict(self.completed_native_contacts)) <= completed:
            raise ValueError('development controller repair cannot retain an uncertain native contact')
        if not set(self.uncontacted_native_task_ids) <= pending or set(self.uncontacted_native_task_ids) & set(self.output_task_ids):
            raise ValueError('development controller repair cannot retry or resize entered native work')
        if not self.output_task_ids or not set(self.output_task_ids) <= refused | pending or not refused <= set(self.output_task_ids):
            raise ValueError('development controller repair must cover every refused PURE output calculation')
        if type(self.output_bytes) is not int or not 0 < self.output_bytes <= 256 * 1024**2:
            raise ValueError('development controller repair requires a bounded in-memory output allowance')
        for source in (self.controller, self.worker):
            if type(source) is not RecursiveImplementationBinding:
                raise TypeError('development controller repair requires exact observed source bindings')
            source.__post_init__()
        if (self.controller.observed_git_head == self.worker.observed_git_head
                or self.controller.dependency_lock_sha256 != self.worker.dependency_lock_sha256):
            raise ValueError('development controller repair requires a distinct controller and unchanged dependency lock')
        if type(self.worker_environment) is not PreparedWorkerEnvironment:
            raise TypeError('development controller repair requires its frozen worker environment')
        self.worker_environment.__post_init__()
        path = PurePath(self.worker_source_root)
        if not path.is_absolute() or '..' in path.parts:
            raise ValueError('development controller repair requires an exact absolute worker source path')

    @staticmethod
    def _pin(value, kind):
        if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
            raise ValueError('development controller repair changes an original record contract')

    @staticmethod
    def _ids(ids):
        if ids != tuple(sorted(set(ids))):
            raise ValueError('development controller repair requires sorted unique task identifiers')
        for key in ids:
            validate_stable_id(key)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)

    def task(self, original):
        if original.task_id not in self.output_task_ids:
            return original
        budget = original.capability.requested_resources
        if budget.output_bytes is None or budget.output_bytes >= self.output_bytes:
            raise ValueError('development controller repair must increase the selected output allowance')
        return replace(original, capability=replace(original.capability,
            requested_resources=replace(budget, output_bytes=self.output_bytes)))

    def validate_plan(self, plan):
        if (type(plan) is not DevelopmentExecutionPlan
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != self.execution_plan
                or plan.implementation_commit != self.worker.observed_git_head
                or {task.task_id for task in plan.tasks} != {
                    *dict(self.completed_receipts), *dict(self.refused_tasks), *self.pending_task_ids}):
            raise ValueError('development controller repair changes its complete original plan/source census')
        for task_id in (*dict(self.refused_tasks), *self.pending_task_ids):
            if plan.task(task_id).maximum_attempts != 1:
                raise ValueError('development controller repair requires a single original attempt')
        for task_id in self.output_task_ids:
            self.task(plan.task(task_id))


@dataclass(frozen=True, slots=True)
class DevelopmentControllerRepairRecoveryIndex(DevelopmentOutputRepairRecoveryIndex):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-controller-repair-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-controller-repair-terminal-event'
    REPAIR_TYPE: ClassVar[type] = DevelopmentControllerRepair

    repair: DevelopmentControllerRepair


@dataclass(frozen=True, slots=True)
class DevelopmentControllerRepairTerminalEvent(DevelopmentRunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = DevelopmentControllerRepairRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = DevelopmentControllerRepairRecoveryIndex.SCHEMA
