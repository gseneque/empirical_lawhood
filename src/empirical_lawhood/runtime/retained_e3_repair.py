# SPDX-License-Identifier: MPL-2.0
"""One explicit control-plane repair of a failed PURE retained-E3 adoption.

The scientific worker and issued plan stay frozen. This record supplies no new
scientific, reveal or native-repeat authority. Successful receipts remain the
original publications; a new wave owns only the failed pure adoption and work
that has never entered execution.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar
from pathlib import PurePath

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from .artifacts import ArtifactManifest, CanonicalTaskReceipt
from .plans import ExecutionPlan
from .prepared_native_invocation import PreparedWorkerEnvironment
from .recursive_handoff import RecursiveImplementationBinding
from .recovery import RunRecoveryIndex, RunRecoveryTerminalEvent, TaskRecoveryEvent


@dataclass(frozen=True, slots=True)
class RetainedE3ControlRepair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-control-repair'

    repair_id: str
    owner_instruction_sha256: str
    execution_plan: ObjectIdentity
    original_index: ObjectIdentity
    original_terminal: ObjectIdentity
    original_resource_envelope: ObjectIdentity
    failed_task_id: str
    original_failure: ObjectIdentity
    reveal_authority: ObjectIdentity
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    unstarted_task_ids: tuple[str, ...]
    controller: RecursiveImplementationBinding
    worker: RecursiveImplementationBinding
    worker_environment: PreparedWorkerEnvironment
    worker_source_root: str

    def __post_init__(self):
        validate_stable_id(self.repair_id)
        validate_stable_id(self.failed_task_id)
        validate_sha256(self.owner_instruction_sha256)
        for value, schema in ((self.execution_plan, ExecutionPlan.SCHEMA),
                (self.original_index, RunRecoveryIndex.SCHEMA),
                (self.original_terminal, RunRecoveryTerminalEvent.SCHEMA),
                (self.original_failure, TaskRecoveryEvent.SCHEMA),
                (self.reveal_authority, 'empirical-lawhood/planning/study-operation-authority'),
                (self.original_resource_envelope, 'empirical-lawhood/runtime/run-execution-resource-envelope')):
            if type(value) is not ObjectIdentity or value.object_schema != schema:
                raise ValueError('retained E3 repair changes its exact original custody contracts')
        ids = tuple(key for key, _ in self.completed_receipts)
        if (not ids or ids != tuple(sorted(set(ids)))
                or any(value.object_schema != CanonicalTaskReceipt.SCHEMA for _, value in self.completed_receipts)
                or self.unstarted_task_ids != tuple(sorted(set(self.unstarted_task_ids)))
                or set(ids).intersection(self.unstarted_task_ids)
                or self.failed_task_id in {*ids, *self.unstarted_task_ids}):
            raise ValueError('retained E3 repair loses its disjoint complete task selection')
        for key in (*ids, *self.unstarted_task_ids):
            validate_stable_id(key)
        for binding in (self.controller, self.worker):
            if type(binding) is not RecursiveImplementationBinding:
                raise TypeError('retained E3 repair requires exact observed installation bindings')
            binding.__post_init__()
        if self.controller == self.worker or self.controller.observed_git_head == self.worker.observed_git_head:
            raise ValueError('retained E3 repair must explicitly bind a distinct repaired controller')
        if type(self.worker_environment) is not PreparedWorkerEnvironment:
            raise TypeError('retained E3 repair requires its exact frozen worker interpreter')
        self.worker_environment.__post_init__()
        if not PurePath(self.worker_source_root).is_absolute() or '..' in PurePath(self.worker_source_root).parts:
            raise ValueError('retained E3 repair requires its explicit frozen worker source root')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)


@dataclass(frozen=True, slots=True)
class RetainedE3RepairRecoveryIndex(RunRecoveryIndex):
    """An additional single-attempt wave; the original index is never amended."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-repair-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-repair-terminal-event'

    repair: RetainedE3ControlRepair
    predecessor: RunRecoveryIndex

    @classmethod
    def derive(cls, plan, predecessor, repair):
        if (type(plan) is not ExecutionPlan or type(predecessor) is not RunRecoveryIndex
                or type(repair) is not RetainedE3ControlRepair):
            raise TypeError('retained E3 repair requires its original frozen plan and wave')
        predecessor.validate_plan(plan)
        if (ObjectIdentity.from_record(plan.execution_plan_id, plan) != repair.execution_plan
                or ObjectIdentity.from_record(predecessor.recovery_index_id, predecessor) != repair.original_index
                or plan.implementation_commit != repair.worker.observed_git_head
                or {row.task_id for row in plan.tasks} != {
                    *(key for key, _ in repair.completed_receipts), repair.failed_task_id, *repair.unstarted_task_ids}):
            raise ValueError('retained E3 repair changes its complete frozen task/source census')
        failed, = (task for task in plan.tasks if task.task_id == repair.failed_task_id)
        if failed.capability.capability_key != 'matrix-e3-configured-protected.retained-fit' or failed.maximum_attempts != 1:
            raise ValueError('retained E3 repair permits only the single failed retained-fit adoption')
        fresh = RunRecoveryIndex.from_execution_plan(plan, run_id=predecessor.run_id,
            wave_id='wave.' + repair.repair_id, authority_identities=predecessor.authority_identities)
        completed = {key for key, _ in repair.completed_receipts}
        bindings = []
        for binding in fresh.tasks:
            if binding.task_id in completed:
                binding = predecessor.task(binding.task_id)
            else:
                candidate, = binding.attempts
                attempt = candidate.attempt_id.removesuffix('.attempt-001') + '.' + repair.repair_id + '.attempt-001'
                candidate = replace(candidate, attempt_id=attempt,
                    receipt_relative_path=f'runs/{fresh.run_id}/receipts/{binding.task_id}/{attempt}.json')
                binding = replace(binding, attempts=(candidate,))
            bindings.append(binding)
        from dataclasses import fields
        values = {field.name: getattr(fresh, field.name) for field in fields(RunRecoveryIndex)}
        return cls(**{**values, 'tasks': tuple(bindings), 'terminal_event_schema': cls.TERMINAL_EVENT_SCHEMA,
            'resource_envelope_event_root_relative_path':
                f'runs/{fresh.run_id}/recovery/{fresh.wave_id}/resource-envelopes'},
            repair=repair, predecessor=predecessor)

    def validate_plan(self, plan):
        if self != type(self).derive(plan, self.predecessor, self.repair):
            raise ValueError('retained E3 repair index changes its owning derivation')

    def event_owner(self, task_id):
        return self.predecessor if task_id in {key for key, _ in self.repair.completed_receipts} else self

    @property
    def completed_receipts(self):
        return self.repair.completed_receipts

    @property
    def unstarted_task_ids(self):
        return self.repair.unstarted_task_ids

    @property
    def original_index(self):
        return self.predecessor


@dataclass(frozen=True, slots=True)
class RetainedE3RepairTerminalEvent(RunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = RetainedE3RepairRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = RetainedE3RepairRecoveryIndex.SCHEMA


@dataclass(frozen=True, slots=True)
class RetainedE3ControllerAdmission(CanonicalRecord):
    """Legacy controller replacement, retained for decoding existing custody only.

    It changes no recovery candidate, task budget, scientific worker or receipt.
    The initial repair remains immutable, including its first controller binding.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-controller-admission'

    admission_id: str
    repair: ObjectIdentity
    recovery_index: ObjectIdentity
    controller: RecursiveImplementationBinding
    worker_package_root: str
    owner_instruction_sha256: str

    def __post_init__(self):
        validate_stable_id(self.admission_id)
        validate_sha256(self.owner_instruction_sha256)
        if (self.repair.object_schema != RetainedE3ControlRepair.SCHEMA
                or self.recovery_index.object_schema != RetainedE3RepairRecoveryIndex.SCHEMA
                or type(self.controller) is not RecursiveImplementationBinding
                or not PurePath(self.worker_package_root).is_absolute()
                or '..' in PurePath(self.worker_package_root).parts):
            raise ValueError('retained E3 controller admission changes its exact repair/source binding')
        self.controller.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.admission_id, self)


@dataclass(frozen=True, slots=True)
class RetainedE3ControllerInputReuseAdmission(RetainedE3ControllerAdmission):
    """One pre-entry correction preserving frozen input validation provenance."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-controller-input-reuse-admission'

    previous_controller_admission: ObjectIdentity

    def __post_init__(self):
        super(RetainedE3ControllerInputReuseAdmission, self).__post_init__()
        if (type(self.previous_controller_admission) is not ObjectIdentity
                or self.previous_controller_admission.object_schema != RetainedE3ControllerAdmission.SCHEMA):
            raise ValueError('retained E3 input reuse must preserve its original controller admission')


@dataclass(frozen=True, slots=True)
class RetainedE3ControllerRetainedScopeAdmission(RetainedE3ControllerAdmission):
    """Pre-entry correction selecting the actual retained-original grant owner."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-controller-retained-scope-admission'

    previous_controller_admission: ObjectIdentity

    def __post_init__(self):
        super(RetainedE3ControllerRetainedScopeAdmission, self).__post_init__()
        if (type(self.previous_controller_admission) is not ObjectIdentity
                or self.previous_controller_admission.object_schema != RetainedE3ControllerInputReuseAdmission.SCHEMA):
            raise ValueError('retained E3 scope correction must preserve its input-reuse controller admission')


@dataclass(frozen=True, slots=True)
class RetainedE3RepairContinuation(CanonicalRecord):
    """An explicit controller change after a failed PURE adoption repair.

    The same custody and nonentry checks apply regardless of the software
    defect. No record type, native retry or attempt-limit change is introduced
    for a particular exception. Previous waves remain immutable.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-repair-continuation'

    repair_id: str
    owner_instruction_sha256: str
    previous_repair: ObjectIdentity
    previous_index: ObjectIdentity
    previous_terminal: ObjectIdentity
    previous_failure: ObjectIdentity
    previous_resource_envelope: ObjectIdentity
    previous_controller: RecursiveImplementationBinding
    failed_task_id: str
    failed_output_manifests: tuple[ArtifactManifest, ...]
    controller: RecursiveImplementationBinding
    worker_package_root: str

    def __post_init__(self):
        validate_stable_id(self.repair_id)
        validate_stable_id(self.failed_task_id)
        validate_sha256(self.owner_instruction_sha256)
        for value, schema in (
                (self.previous_repair, RetainedE3ControlRepair.SCHEMA),
                (self.previous_failure, TaskRecoveryEvent.SCHEMA),
                (self.previous_resource_envelope, 'empirical-lawhood/runtime/run-execution-resource-envelope')):
            if type(value) is not ObjectIdentity or value.object_schema != schema:
                raise ValueError('repair continuation changes its exact failed repair custody')
            value.__post_init__()
        if (self.previous_index.object_schema, self.previous_terminal.object_schema) not in {
                (RetainedE3RepairRecoveryIndex.SCHEMA, RetainedE3RepairTerminalEvent.SCHEMA),
                (RetainedE3ContinuedRepairRecoveryIndex.SCHEMA, RetainedE3ContinuedRepairTerminalEvent.SCHEMA)}:
            raise ValueError('repair continuation changes its predecessor index/terminal contracts')
        paths = tuple(row.materialization.relative_path for row in self.failed_output_manifests)
        if (type(self.failed_output_manifests) is not tuple
                or paths != tuple(sorted(set(paths)))
                or any(type(row) is not ArtifactManifest for row in self.failed_output_manifests)):
            raise ValueError('repair continuation must retain every committed PURE output')
        for manifest in self.failed_output_manifests:
            manifest.__post_init__()
        if (type(self.controller) is not RecursiveImplementationBinding
                or type(self.previous_controller) is not RecursiveImplementationBinding
                or self.controller.observed_git_head == self.previous_controller.observed_git_head
                or not PurePath(self.worker_package_root).is_absolute()
                or '..' in PurePath(self.worker_package_root).parts):
            raise ValueError('repair continuation requires a separately installed repaired controller')
        self.previous_controller.__post_init__()
        self.controller.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)


@dataclass(frozen=True, slots=True)
class RetainedE3RepairContinuationV2(RetainedE3RepairContinuation):
    """Retain progress made before a later PURE adoption fails.

    Revision one remains an exact historical codec. This revision binds the
    actual latest successful census instead of assuming no intervening work.
    """
    VERSION: ClassVar[str] = '2.0.0'

    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    unstarted_task_ids: tuple[str, ...]

    def __post_init__(self):
        super(RetainedE3RepairContinuationV2, self).__post_init__()
        ids = tuple(key for key, _ in self.completed_receipts)
        if (not ids or ids != tuple(sorted(set(ids)))
                or self.unstarted_task_ids != tuple(sorted(set(self.unstarted_task_ids)))
                or set(ids).intersection(self.unstarted_task_ids)
                or self.failed_task_id in {*ids, *self.unstarted_task_ids}):
            raise ValueError('repair continuation loses its disjoint successful and unstarted census')
        for key, receipt in self.completed_receipts:
            validate_stable_id(key)
            if type(receipt) is not ObjectIdentity or receipt.object_schema != CanonicalTaskReceipt.SCHEMA:
                raise ValueError('repair continuation requires exact successful receipt identities')
            receipt.__post_init__()
        for key in self.unstarted_task_ids:
            validate_stable_id(key)


@dataclass(frozen=True, slots=True)
class RetainedE3ContinuedRepairRecoveryIndex(RetainedE3RepairRecoveryIndex):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-continued-repair-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retained-e3-continued-repair-terminal-event'

    predecessor: RetainedE3RepairRecoveryIndex | RetainedE3ContinuedRepairRecoveryIndex
    repair_continuation: RetainedE3RepairContinuation | RetainedE3RepairContinuationV2

    @classmethod
    def derive(cls, plan, predecessor, repair_continuation):
        from dataclasses import fields
        from hashlib import sha256
        from empirical_lawhood.kernel.serialization import canonical_json_bytes
        if (type(plan) is not ExecutionPlan or type(predecessor) not in (
                RetainedE3RepairRecoveryIndex, RetainedE3ContinuedRepairRecoveryIndex)
                or type(repair_continuation) not in (RetainedE3RepairContinuation, RetainedE3RepairContinuationV2)):
            raise TypeError('repair continuation requires its exact preceding retained-adoption repair')
        predecessor.validate_plan(plan)
        proof = repair_continuation
        if (proof.repair_id == predecessor.wave_id.removeprefix('wave.')
                or proof.previous_index != ObjectIdentity.from_record(predecessor.recovery_index_id, predecessor)
                or proof.previous_repair != predecessor.repair.identity
                or proof.owner_instruction_sha256 != predecessor.repair.owner_instruction_sha256):
            raise ValueError('repair continuation changes its original owner or predecessor')
        if type(proof) is RetainedE3RepairContinuation:
            if proof.failed_task_id != predecessor.repair.failed_task_id:
                raise ValueError('revision-one repair continuation changes its original failed task')
            retained = predecessor.repair.completed_receipts
            unstarted = predecessor.repair.unstarted_task_ids
        else:
            retained, unstarted = proof.completed_receipts, proof.unstarted_task_ids
            if not set(predecessor.completed_receipts) <= set(retained):
                raise ValueError('repair continuation drops or substitutes an earlier successful receipt')
        if {row.task_id for row in plan.tasks} != {*(key for key, _ in retained), proof.failed_task_id, *unstarted}:
            raise ValueError('repair continuation changes its complete frozen task census')
        failed, = (row for row in plan.tasks if row.task_id == proof.failed_task_id)
        if (failed.maximum_attempts != 1 or failed.capability.capability_key not in (
                'matrix-e3-configured-protected.retained-fit',
                'matrix-e3-configured-protected.retained-model-freeze',
                'matrix-e3-configured-protected.retained-forecast')):
            raise ValueError('repair continuation permits only a failed retained model adoption')
        fresh = RunRecoveryIndex.from_execution_plan(plan, run_id=predecessor.run_id,
            wave_id='wave.' + proof.repair_id, authority_identities=predecessor.authority_identities)
        completed = {key for key, _ in retained}
        bindings = []
        for binding in fresh.tasks:
            if binding.task_id in completed:
                binding = predecessor.task(binding.task_id)
            else:
                candidate, = binding.attempts
                digest = sha256(canonical_json_bytes((proof.identity, fresh.run_id,
                    fresh.execution_plan, binding.task_id, candidate.ordinal))).hexdigest()
                attempt = 'attempt.retained-e3.' + digest
                candidate = replace(candidate, attempt_id=attempt,
                    receipt_relative_path=f'runs/{fresh.run_id}/receipts/{binding.task_id}/{attempt}.json')
                binding = replace(binding, attempts=(candidate,))
            bindings.append(binding)
        values = {field.name: getattr(fresh, field.name) for field in fields(RunRecoveryIndex)}
        return cls(**{**values, 'tasks': tuple(bindings), 'terminal_event_schema': cls.TERMINAL_EVENT_SCHEMA,
            'resource_envelope_event_root_relative_path':
                f'runs/{fresh.run_id}/recovery/{fresh.wave_id}/resource-envelopes'},
            repair=predecessor.repair, predecessor=predecessor, repair_continuation=proof)

    def validate_plan(self, plan):
        if self != type(self).derive(plan, self.predecessor, self.repair_continuation):
            raise ValueError('repair continuation changes its bounded owning derivation')

    def event_owner(self, task_id):
        return (self.predecessor.event_owner(task_id)
            if task_id in {key for key, _ in self.completed_receipts} else self)

    @property
    def completed_receipts(self):
        proof = self.repair_continuation
        return proof.completed_receipts if type(proof) is RetainedE3RepairContinuationV2 else self.repair.completed_receipts

    @property
    def unstarted_task_ids(self):
        proof = self.repair_continuation
        return proof.unstarted_task_ids if type(proof) is RetainedE3RepairContinuationV2 else self.repair.unstarted_task_ids

    @property
    def original_index(self):
        return self.predecessor.original_index


@dataclass(frozen=True, slots=True)
class RetainedE3ContinuedRepairTerminalEvent(RunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = RetainedE3ContinuedRepairRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = RetainedE3ContinuedRepairRecoveryIndex.SCHEMA
