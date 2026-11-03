# SPDX-License-Identifier: MPL-2.0
"""Exact native contact commitments, distinct from completion and authority."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import ClassVar, Protocol

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id


class NativeEntryRefused(RuntimeError):
    """Current permission or the original live attempt refused before effect entry.

    This is an operational prerequisite, not an observed native failure or an
    unknown contact. The scheduler drains admitted work without inventing a
    scientific result, completion receipt or permission to repeat acquisition.
    """


@dataclass(frozen=True, slots=True)
class NativeEffectContact(CanonicalRecord):
    """Durable evidence that a task may have contacted its native effect."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-effect-contact"
    run_id: str
    task_id: str
    attempt_id: str
    execution_plan: ObjectIdentity
    execution_task: ObjectIdentity
    implementation_commit: str
    input_materialization_ids: tuple[str, ...]
    dependency_receipt_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("run_id", "task_id", "attempt_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.execution_task.object_id != self.task_id:
            raise ValueError("native contact substitutes its exact execution task")
        if len(self.implementation_commit) != 40 or any(c not in "0123456789abcdef" for c in self.implementation_commit):
            raise ValueError("native contact requires the actual producing commit")
        require_sorted_unique_strings(self.input_materialization_ids, field_name="input_materialization_ids")
        require_sorted_unique_strings(self.dependency_receipt_ids, field_name="dependency_receipt_ids")


class NativeEffectContactStore(Protocol):
    """External custody survives catalog loss and never grants repeat permission."""

    def read(self, run_id: str, task_id: str) -> NativeEffectContact | None: ...

    def begin(self, contact: NativeEffectContact) -> None: ...

    def execution_lock(self, run_id: str) -> AbstractContextManager[None]: ...
