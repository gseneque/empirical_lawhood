# SPDX-License-Identifier: MPL-2.0
"""A reviewable census for a proposed continuation, never execution authority."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from .artifacts import CanonicalTaskReceipt, validate_relative_locator
from .native_subwork import NativeSubworkState
from .plans import DevelopmentExecutionPlan
from .prepared_native_invocation import PreparedInvocationContract, PreparedWorkerEnvironment
from .recovery import DevelopmentRunRecoveryIndex
from .recursive_handoff import RecursiveImplementationBinding


def _controls(rows):
    paths = tuple(path for path, _, _ in rows)
    if not paths or paths != tuple(sorted(set(paths))):
        raise ValueError('continuation proposal requires its complete sorted control census')
    for path, size, digest in rows:
        validate_relative_locator(path)
        if size is None:
            if digest is not None:
                raise ValueError('absent continuation controls cannot carry a digest')
        else:
            if type(size) is not int or size < 0:
                raise ValueError('continuation controls require their exact nonnegative size')
            validate_sha256(digest)


@dataclass(frozen=True, slots=True)
class NativeContinuationCandidate(CanonicalRecord):
    """The original invocation and its observed unfinished nested census."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/native-continuation-candidate'
    invocation: PreparedInvocationContract
    subwork_states: tuple[tuple[ObjectIdentity, NativeSubworkState], ...]
    original_controls: tuple[tuple[str, int | None, str | None], ...]

    def __post_init__(self):
        if type(self.invocation) is not PreparedInvocationContract:
            raise TypeError('continuation candidate requires the exact original prepared invocation')
        self.invocation.require_complete()
        work = self.invocation.native_work
        if not self.invocation.native_effect or work is None or not work.definitions:
            raise ValueError('continuation candidate lacks its original complete native denominator')
        if tuple(pin for pin, _ in self.subwork_states) != tuple(row.identity for row in work.definitions):
            raise ValueError('continuation candidate changes its complete original nested denominator')
        if any(state not in (NativeSubworkState.BEGUN, NativeSubworkState.UNKNOWN_COMPLETION)
                for _, state in self.subwork_states):
            raise ValueError('continuation candidate cannot relabel completed or unselected work')
        _controls(self.original_controls)

    @property
    def task_id(self):
        return self.invocation.task_id


@dataclass(frozen=True, slots=True)
class DevelopmentNativeContinuationProposal(CanonicalRecord):
    """An explicit proposal for original incomplete DEV cases; no retry grant."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-native-continuation-proposal'
    proposal_id: str
    preparation_instruction_sha256: str
    original_run_id: str
    execution_plan: ObjectIdentity
    original_index: ObjectIdentity
    task_ids: tuple[str, ...]
    native_task_ids: tuple[str, ...]
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    completed_native_task_ids: tuple[str, ...]
    candidates: tuple[NativeContinuationCandidate, ...]
    original_controls: tuple[tuple[str, int | None, str | None], ...]
    worker: RecursiveImplementationBinding
    controller: RecursiveImplementationBinding
    worker_environment: PreparedWorkerEnvironment
    worker_source_root: str
    pure_output_bytes: int
    execution_authorized: bool = False
    additional_independent_observations: int = 0

    def __post_init__(self):
        from pathlib import PurePath
        validate_stable_id(self.proposal_id)
        validate_sha256(self.preparation_instruction_sha256)
        validate_stable_id(self.original_run_id)
        for pin, kind in ((self.execution_plan, DevelopmentExecutionPlan),
                (self.original_index, DevelopmentRunRecoveryIndex)):
            if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('continuation proposal substitutes its original development contracts')
        if not self.task_ids or not self.native_task_ids or not self.candidates:
            raise ValueError('continuation proposal requires original tasks and incomplete native candidates')
        for ids in (self.task_ids, self.native_task_ids, self.completed_native_task_ids,
                tuple(key for key, _ in self.completed_receipts), tuple(row.task_id for row in self.candidates)):
            if ids != tuple(sorted(set(ids))):
                raise ValueError('continuation proposal requires sorted unique original task censuses')
            for key in ids:
                validate_stable_id(key)
        completed = set(dict(self.completed_receipts))
        candidates = {row.task_id for row in self.candidates}
        if (not set(self.native_task_ids) <= set(self.task_ids) or not completed <= set(self.task_ids)
                or set(self.completed_native_task_ids) != completed & set(self.native_task_ids)
                or not candidates <= set(self.native_task_ids) or candidates & completed):
            raise ValueError('continuation proposal changes its complete original task partition')
        for _, pin in self.completed_receipts:
            if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION):
                raise ValueError('continuation proposal changes a retained original receipt')
        for source in (self.worker, self.controller):
            if type(source) is not RecursiveImplementationBinding:
                raise TypeError('continuation proposal requires its original and preparation source bindings')
            source.__post_init__()
        if self.worker.dependency_lock_sha256 != self.controller.dependency_lock_sha256:
            raise ValueError('continuation proposal changes the original dependency lock')
        if type(self.worker_environment) is not PreparedWorkerEnvironment:
            raise TypeError('continuation proposal requires its observed frozen worker environment')
        self.worker_environment.__post_init__()
        root = PurePath(self.worker_source_root)
        if not root.is_absolute() or '..' in root.parts:
            raise ValueError('continuation proposal requires an absolute original worker source root')
        for candidate in self.candidates:
            if type(candidate) is not NativeContinuationCandidate:
                raise TypeError('continuation proposal requires exact typed original candidates')
            candidate.__post_init__()
            invocation = candidate.invocation
            if (invocation.run_id != self.original_run_id or invocation.execution_plan != self.execution_plan or invocation.implementation != self.worker
                    or invocation.environment != self.worker_environment):
                raise ValueError('continuation candidate substitutes its original plan, worker or environment')
        if type(self.pure_output_bytes) is not int or not 0 < self.pure_output_bytes <= 256 * 1024**2:
            raise ValueError('continuation proposal requires a bounded PURE output selection')
        if (self.execution_authorized is not False or type(self.additional_independent_observations) is not int
                or self.additional_independent_observations != 0):
            raise ValueError('a continuation proposal grants no execution or independent observations')
        _controls(self.original_controls)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.proposal_id, self)

