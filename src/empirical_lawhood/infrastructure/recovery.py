"""Bounded external run recovery and compact operational reconstruction."""

from __future__ import annotations

import hashlib
import json
from copy import copy
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Final

from empirical_lawhood.infrastructure.execution_resource_envelopes import DEFAULT_EXECUTION_RESOURCE_ENVELOPE_STATE_ROOT, ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict,
    ExternalArtifactPlane,
)
from empirical_lawhood.infrastructure.bounded_io import (
    BoundedFileIOError,
    read_bounded_bytes,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent
from empirical_lawhood.runtime.retained_e3_repair import RetainedE3RepairRecoveryIndex, RetainedE3RepairTerminalEvent, RetainedE3ContinuedRepairRecoveryIndex, RetainedE3ContinuedRepairTerminalEvent
from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex, DevelopmentOutputRepairTerminalEvent
from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairRecoveryIndex, DevelopmentControllerRepairTerminalEvent
from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationRecoveryIndex, DevelopmentNativeContinuationTerminalEvent
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    CanonicalizationError,
    validate_document_shape,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent,
    ArtifactManifest,
    ArtifactProfile,
    ArtifactWriteRequest,
    CanonicalTaskReceipt,
    lineage_parent_sort_key,
    most_restrictive_outcome_access,
)
from empirical_lawhood.runtime.execution import (
    OperationalFailureClass,
    OperationalAttempt,
    OperationalRepository,
    TaskAttemptDisposition,
    TaskBlockReason,
    TaskReceiptStore,
)
from empirical_lawhood.runtime.execution_envelope import ExecutionEnvelopeEvent, ExecutionEnvelopeSpec, ExecutionResourceEnvelopeEvent, ExecutionResourceEnvelopeSpec, JitGraphSignatureManifest, RunExecutionEnvelope, RunExecutionResourceEnvelope, reconstruct_execution_envelope, reconstruct_execution_resource_envelope
from empirical_lawhood.runtime.plans import ProtocolExecutionPlan, ProtocolExecutionTask
from empirical_lawhood.runtime.prepared_native_invocation import WorkerPreflightResult
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic, RecoveryTerminalAttempt, RecoveryTerminalDisposition, RecoveryAttemptCandidate, RecoveryTaskBinding, ProtocolRunRecoveryIndex, CandidateRunRecoveryIndex, EnvelopeRunRecoveryIndex, RunRecoveryIndex, RunRecoveryReport, ProtocolRunRecoveryTerminalEvent, CandidateRunRecoveryTerminalEvent, EnvelopeRunRecoveryTerminalEvent, RunRecoveryTerminalEvent, TaskRecoveryDisposition, ProtocolTaskRecoveryEvent, TaskRecoveryEvent


MAX_RECOVERY_INDEX_BYTES: Final[int] = 32 * 1024**2
MAX_RECOVERY_EVENT_BYTES: Final[int] = 2 * 1024**2
MAX_EXECUTION_ENVELOPE_EVENTS: Final[int] = 100_000


class RunRecoveryError(RuntimeError):
    """External recovery authority, custody or state is inconsistent."""


def recovery_error_types() -> tuple[type[BaseException], ...]:
    """Return the actual runtime custody error boundary."""
    return (RunRecoveryError,)


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise CanonicalizationError(f"{field_name} must be a string-keyed mapping")
    return value


def _record(
    value: object,
    record_type: type[CanonicalRecord],
    fields: frozenset[str],
) -> Mapping[str, object]:
    return validate_document_shape(
        _mapping(value, record_type.SCHEMA),
        expected_schema=record_type.SCHEMA,
        expected_version=record_type.VERSION,
        field_names=fields,
    )


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise CanonicalizationError(f"{field_name} must be a string")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    return None if value is None else _string(value, field_name)


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CanonicalizationError(f"{field_name} must be an integer")
    return value


def _optional_integer(value: object, field_name: str) -> int | None:
    return None if value is None else _integer(value, field_name)


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise CanonicalizationError(f"{field_name} must be a JSON array")
    return value


def _boolean(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise CanonicalizationError(f"{field_name} must be a boolean")
    return value


def _strings(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_string(item, field_name) for item in _list(value, field_name))


def _identity(document: object) -> ObjectIdentity:
    value = _record(
        document,
        ObjectIdentity,
        frozenset(
            {
                "object_id",
                "object_schema",
                "object_version",
                "object_fingerprint",
            }
        ),
    )
    return ObjectIdentity(
        object_id=_string(value["object_id"], "object_id"),
        object_schema=_string(value["object_schema"], "object_schema"),
        object_version=_string(value["object_version"], "object_version"),
        object_fingerprint=_string(value["object_fingerprint"], "object_fingerprint"),
    )


def _attempt_candidate(document: object) -> RecoveryAttemptCandidate:
    value = _record(
        document,
        RecoveryAttemptCandidate,
        frozenset(
            {
                "attempt_id",
                "ordinal",
                "receipt_relative_path",
                "event_relative_path",
                "receipt_schema",
                "event_schema",
            }
        ),
    )
    return RecoveryAttemptCandidate(
        attempt_id=_string(value["attempt_id"], "attempt_id"),
        ordinal=_integer(value["ordinal"], "ordinal"),
        receipt_relative_path=_string(
            value["receipt_relative_path"],
            "receipt_relative_path",
        ),
        event_relative_path=_string(value["event_relative_path"], "event_relative_path"),
        receipt_schema=_string(value["receipt_schema"], "receipt_schema"),
        event_schema=_string(value["event_schema"], "event_schema"),
    )


def _task_binding(document: object) -> RecoveryTaskBinding:
    value = _record(
        document,
        RecoveryTaskBinding,
        frozenset(
            {
                "task_id",
                "topological_ordinal",
                "dependency_task_ids",
                "maximum_attempts",
                "capability_key",
                "capability_version",
                "capability_implementation_sha256",
                "output_schema_ids",
                "attempts",
                "nonattempt_event_relative_path",
            }
        ),
    )
    return RecoveryTaskBinding(
        task_id=_string(value["task_id"], "task_id"),
        topological_ordinal=_integer(
            value["topological_ordinal"],
            "topological_ordinal",
        ),
        dependency_task_ids=_strings(
            value["dependency_task_ids"],
            "dependency_task_ids",
        ),
        maximum_attempts=_integer(value["maximum_attempts"], "maximum_attempts"),
        capability_key=_string(value["capability_key"], "capability_key"),
        capability_version=_string(value["capability_version"], "capability_version"),
        capability_implementation_sha256=_string(
            value["capability_implementation_sha256"],
            "capability_implementation_sha256",
        ),
        output_schema_ids=_strings(value["output_schema_ids"], "output_schema_ids"),
        attempts=tuple(_attempt_candidate(item) for item in _list(value["attempts"], "attempts")),
        nonattempt_event_relative_path=_string(
            value["nonattempt_event_relative_path"],
            "nonattempt_event_relative_path",
        ),
    )


def _json_document(payload: bytes, *, label: str, maximum_bytes: int | None) -> object:
    if not payload or (maximum_bytes is not None and len(payload) > maximum_bytes):
        raise CanonicalizationError(f"{label} violates its byte bound")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise CanonicalizationError(f"{label} is not UTF-8 JSON") from error


def decode_run_recovery_index(payload: bytes, *, maximum_bytes: int | None = None) -> ProtocolRunRecoveryIndex:
    document = _json_document(
        payload,
        label="run recovery index",
        maximum_bytes=maximum_bytes,
    )
    schema = _string(_mapping(document, "run recovery index").get("schema"), "schema")
    record_type: type[ProtocolRunRecoveryIndex]
    if schema == DevelopmentOutputRepairRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentOutputRepairRecoveryIndex, maximum_bytes=maximum_bytes)
    if schema == DevelopmentControllerRepairRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentControllerRepairRecoveryIndex, maximum_bytes=maximum_bytes)
    if schema == DevelopmentNativeContinuationRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentNativeContinuationRecoveryIndex, maximum_bytes=maximum_bytes)
    if schema == RetainedE3ContinuedRepairRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, RetainedE3ContinuedRepairRecoveryIndex, maximum_bytes=maximum_bytes)
    if schema == RetainedE3RepairRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, RetainedE3RepairRecoveryIndex, maximum_bytes=maximum_bytes)
    if schema == ProtocolRunRecoveryIndex.SCHEMA:
        record_type = ProtocolRunRecoveryIndex
    elif schema == DevelopmentRunRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentRunRecoveryIndex, maximum_bytes=maximum_bytes)
    elif schema == CandidateRunRecoveryIndex.SCHEMA:
        record_type = CandidateRunRecoveryIndex
    elif schema == EnvelopeRunRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(
            payload,
            EnvelopeRunRecoveryIndex,
            maximum_bytes=maximum_bytes,
        )
    elif schema == RunRecoveryIndex.SCHEMA:
        return decode_canonical_bytes(
            payload,
            RunRecoveryIndex,
            maximum_bytes=maximum_bytes,
        )
    else:
        raise CanonicalizationError("run recovery index schema is unsupported")
    value = _record(
        document,
        record_type,
        frozenset(
            {
                "recovery_index_id",
                "wave_id",
                "run_id",
                "execution_plan",
                "authority_identities",
                "registry_sha256",
                "implementation_commit",
                "index_relative_path",
                "terminal_event_relative_path",
                "terminal_event_schema",
                "tasks",
            }
        ),
    )
    result = record_type(
        recovery_index_id=_string(
            value["recovery_index_id"],
            "recovery_index_id",
        ),
        wave_id=_string(value["wave_id"], "wave_id"),
        run_id=_string(value["run_id"], "run_id"),
        execution_plan=_identity(value["execution_plan"]),
        authority_identities=tuple(
            _identity(item)
            for item in _list(
                value["authority_identities"],
                "authority_identities",
            )
        ),
        registry_sha256=_string(value["registry_sha256"], "registry_sha256"),
        implementation_commit=_string(
            value["implementation_commit"],
            "implementation_commit",
        ),
        index_relative_path=_string(
            value["index_relative_path"],
            "index_relative_path",
        ),
        terminal_event_relative_path=_string(
            value["terminal_event_relative_path"],
            "terminal_event_relative_path",
        ),
        terminal_event_schema=_string(
            value["terminal_event_schema"],
            "terminal_event_schema",
        ),
        tasks=tuple(_task_binding(item) for item in _list(value["tasks"], "tasks")),
    )
    if result.canonical_bytes() != payload:
        raise CanonicalizationError("run recovery index bytes are not canonical")
    return result


def _failure_diagnostic(document: object) -> OperationalFailureDiagnostic | None:
    if document is None:
        return None
    value = _record(
        document,
        OperationalFailureDiagnostic,
        frozenset(
            {
                "failure_class",
                "retryable",
                "sanitized_exception_type",
                "sanitized_message",
                "diagnostic_sha256",
                "scientific_evidence",
            }
        ),
    )
    try:
        failure_class = OperationalFailureClass(_string(value["failure_class"], "failure_class"))
    except ValueError as error:
        raise CanonicalizationError("operational failure class is unsupported") from error
    return OperationalFailureDiagnostic(
        failure_class=failure_class,
        retryable=_boolean(value["retryable"], "retryable"),
        sanitized_exception_type=_optional_string(
            value["sanitized_exception_type"],
            "sanitized_exception_type",
        ),
        sanitized_message=_optional_string(value["sanitized_message"], "sanitized_message"),
        diagnostic_sha256=_string(value["diagnostic_sha256"], "diagnostic_sha256"),
        scientific_evidence=_boolean(value["scientific_evidence"], "scientific_evidence"),
    )


def decode_task_recovery_event(payload: bytes, *, maximum_bytes: int | None = None) -> TaskRecoveryEvent:
    document = _json_document(
        payload,
        label="task recovery event",
        maximum_bytes=maximum_bytes,
    )
    schema = _string(_mapping(document, "task recovery event").get("schema"), "schema")
    if schema != TaskRecoveryEvent.SCHEMA:
        raise CanonicalizationError("task recovery event schema is unsupported")
    value = _record(
        document,
        TaskRecoveryEvent,
        frozenset(
            {
                "event_id",
                "recovery_index",
                "run_id",
                "task_id",
                "attempt_id",
                "attempt_ordinal",
                "disposition",
                "receipt_id",
                "receipt_relative_path",
                "receipt_sha256",
                "receipt_schema",
                "output_materialization_ids",
                "reason_codes",
                "failure",
            }
        ),
    )
    try:
        disposition = TaskRecoveryDisposition(_string(value["disposition"], "disposition"))
    except ValueError as error:
        raise CanonicalizationError("task recovery disposition is unsupported") from error
    result = TaskRecoveryEvent(
        event_id=_string(value["event_id"], "event_id"),
        recovery_index=_identity(value["recovery_index"]),
        run_id=_string(value["run_id"], "run_id"),
        task_id=_string(value["task_id"], "task_id"),
        attempt_id=_optional_string(value["attempt_id"], "attempt_id"),
        attempt_ordinal=_optional_integer(
            value["attempt_ordinal"],
            "attempt_ordinal",
        ),
        disposition=disposition,
        receipt_id=_optional_string(value["receipt_id"], "receipt_id"),
        receipt_relative_path=_optional_string(
            value["receipt_relative_path"],
            "receipt_relative_path",
        ),
        receipt_sha256=_optional_string(value["receipt_sha256"], "receipt_sha256"),
        receipt_schema=_optional_string(value["receipt_schema"], "receipt_schema"),
        output_materialization_ids=_strings(
            value["output_materialization_ids"],
            "output_materialization_ids",
        ),
        reason_codes=_strings(value["reason_codes"], "reason_codes"),
        failure=_failure_diagnostic(value["failure"]),
    )
    if result.canonical_bytes() != payload:
        raise CanonicalizationError("task recovery event bytes are not canonical")
    return result


def decode_execution_envelope_event(payload: bytes, *, maximum_bytes: int | None = None) -> ExecutionEnvelopeEvent:
    """Strictly decode one canonical, bounded execution-envelope event."""

    return decode_canonical_bytes(
        payload,
        ExecutionEnvelopeEvent,
        maximum_bytes=maximum_bytes,
    )


def decode_execution_resource_envelope_event(
    payload: bytes,
    *, maximum_bytes: int | None = None,
) -> ExecutionResourceEnvelopeEvent:
    """Strictly decode one canonical deadline-free resource event."""

    return decode_canonical_bytes(
        payload,
        ExecutionResourceEnvelopeEvent,
        maximum_bytes=maximum_bytes,
    )


def reconstruct_execution_envelope_from_external_events(
    *,
    index: EnvelopeRunRecoveryIndex,
    envelope_id: str,
    spec: ExecutionEnvelopeSpec,
    execution_plan: ObjectIdentity,
    event_payloads: tuple[bytes, ...],
    maximum_events: int | None = None,
    maximum_event_bytes: int | None = None,
) -> RunExecutionEnvelope:
    "Reconstruct exact state from externally retained canonical event bytes."

    if maximum_events is not None and len(event_payloads) > maximum_events:
        raise RunRecoveryError("execution-envelope event count exceeds its bound")
    if (
        index.execution_envelope_spec != ObjectIdentity.from_record(spec.envelope_spec_id, spec)
        or index.execution_plan != execution_plan
        or spec.issued_study_extensions != index.issued_extension_set
    ):
        raise RunRecoveryError("execution-envelope recovery inputs differ from the index")
    try:
        events = tuple(decode_execution_envelope_event(value, maximum_bytes=maximum_event_bytes) for value in event_payloads)
        if tuple(value.sequence_number for value in events) != tuple(range(1, len(events) + 1)):
            raise ValueError("execution-envelope external events are incomplete or out of order")
        return reconstruct_execution_envelope(
            envelope_id=envelope_id,
            spec=spec,
            execution_plan=execution_plan,
            events=events,
        )
    except (CanonicalizationError, ValueError) as error:
        raise RunRecoveryError("execution-envelope external event reconstruction failed") from error


def reconstruct_execution_resource_envelope_from_external_events(
    *,
    index: RunRecoveryIndex,
    envelope_id: str,
    spec: ExecutionResourceEnvelopeSpec,
    execution_plan: ObjectIdentity,
    jit_graph_signature_manifest: JitGraphSignatureManifest | None,
    event_payloads: tuple[bytes, ...],
    maximum_events: int | None = None,
    maximum_event_bytes: int | None = None,
) -> RunExecutionResourceEnvelope:
    "Reconstruct exact state from externally retained event bytes."

    if maximum_events is not None and len(event_payloads) > maximum_events:
        raise RunRecoveryError("resource-envelope event count exceeds its bound")
    if (
        index.execution_resource_envelope_spec
        != ObjectIdentity.from_record(spec.envelope_spec_id, spec)
        or index.execution_plan != execution_plan
        or spec.issued_study_extensions != index.issued_extension_set
        or index.jit_graph_signature_manifest
        != (
            None
            if jit_graph_signature_manifest is None
            else ObjectIdentity.from_record(
                jit_graph_signature_manifest.manifest_id,
                jit_graph_signature_manifest,
            )
        )
    ):
        raise RunRecoveryError("resource-envelope recovery inputs differ from the index")
    try:
        events = tuple(
            decode_execution_resource_envelope_event(value, maximum_bytes=maximum_event_bytes) for value in event_payloads
        )
        if tuple(value.sequence_number for value in events) != tuple(range(1, len(events) + 1)):
            raise ValueError("resource-envelope external events are incomplete or out of order")
        return reconstruct_execution_resource_envelope(
            envelope_id=envelope_id,
            spec=spec,
            execution_plan=execution_plan,
            events=events,
            jit_graph_signature_manifest=jit_graph_signature_manifest,
        )
    except (CanonicalizationError, ValueError) as error:
        raise RunRecoveryError("resource-envelope external event reconstruction failed") from error


def _terminal_attempt(document: object) -> RecoveryTerminalAttempt:
    value = _record(
        document,
        RecoveryTerminalAttempt,
        frozenset(
            {
                "attempt_id",
                "task_id",
                "ordinal",
                "disposition",
                "reason_code",
                "receipt_id",
                "receipt_sha256",
            }
        ),
    )
    try:
        disposition = RecoveryTerminalDisposition(_string(value["disposition"], "disposition"))
    except ValueError as error:
        raise CanonicalizationError("terminal attempt disposition is unsupported") from error
    return RecoveryTerminalAttempt(
        attempt_id=_string(value["attempt_id"], "attempt_id"),
        task_id=_string(value["task_id"], "task_id"),
        ordinal=_integer(value["ordinal"], "ordinal"),
        disposition=disposition,
        reason_code=_optional_string(value["reason_code"], "reason_code"),
        receipt_id=_optional_string(value["receipt_id"], "receipt_id"),
        receipt_sha256=_optional_string(value["receipt_sha256"], "receipt_sha256"),
    )


def decode_run_recovery_terminal_event(payload: bytes, *, maximum_bytes: int | None = None) -> ProtocolRunRecoveryTerminalEvent:
    document = _json_document(
        payload,
        label="run recovery terminal event",
        maximum_bytes=maximum_bytes,
    )
    schema = _string(
        _mapping(document, "run recovery terminal event").get("schema"),
        "schema",
    )
    record_type: type[ProtocolRunRecoveryTerminalEvent]
    if schema == DevelopmentOutputRepairTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentOutputRepairTerminalEvent, maximum_bytes=maximum_bytes)
    if schema == DevelopmentControllerRepairTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentControllerRepairTerminalEvent, maximum_bytes=maximum_bytes)
    if schema == DevelopmentNativeContinuationTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentNativeContinuationTerminalEvent, maximum_bytes=maximum_bytes)
    if schema == RetainedE3ContinuedRepairTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, RetainedE3ContinuedRepairTerminalEvent, maximum_bytes=maximum_bytes)
    if schema == RetainedE3RepairTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, RetainedE3RepairTerminalEvent, maximum_bytes=maximum_bytes)
    if schema == ProtocolRunRecoveryTerminalEvent.SCHEMA:
        record_type = ProtocolRunRecoveryTerminalEvent
    elif schema == DevelopmentRunRecoveryTerminalEvent.SCHEMA:
        return decode_canonical_bytes(payload, DevelopmentRunRecoveryTerminalEvent, maximum_bytes=maximum_bytes)
    elif schema == CandidateRunRecoveryTerminalEvent.SCHEMA:
        record_type = CandidateRunRecoveryTerminalEvent
    elif schema == EnvelopeRunRecoveryTerminalEvent.SCHEMA:
        return decode_canonical_bytes(
            payload,
            EnvelopeRunRecoveryTerminalEvent,
            maximum_bytes=maximum_bytes,
        )
    elif schema == RunRecoveryTerminalEvent.SCHEMA:
        return decode_canonical_bytes(
            payload,
            RunRecoveryTerminalEvent,
            maximum_bytes=maximum_bytes,
        )
    else:
        raise CanonicalizationError("run recovery terminal event schema is unsupported")
    value = _record(
        document,
        record_type,
        frozenset(
            {
                "terminal_event_id",
                "recovery_index",
                "run_id",
                "operational_status",
                "attempts",
                "completed_task_ids",
                "failed_task_ids",
                "blocked_task_ids",
            }
        ),
    )
    result = record_type(
        terminal_event_id=_string(value["terminal_event_id"], "terminal_event_id"),
        recovery_index=_identity(value["recovery_index"]),
        run_id=_string(value["run_id"], "run_id"),
        operational_status=_string(
            value["operational_status"],
            "operational_status",
        ),
        attempts=tuple(_terminal_attempt(item) for item in _list(value["attempts"], "attempts")),
        completed_task_ids=_strings(
            value["completed_task_ids"],
            "completed_task_ids",
        ),
        failed_task_ids=_strings(value["failed_task_ids"], "failed_task_ids"),
        blocked_task_ids=_strings(value["blocked_task_ids"], "blocked_task_ids"),
    )
    if result.canonical_bytes() != payload:
        raise CanonicalizationError("run recovery terminal event bytes are not canonical")
    return result


def settled_recovery_tasks(index, attempts):
    """Classify exact frozen tasks without spending a candidate or publishing."""
    if not isinstance(index, ProtocolRunRecoveryIndex):
        raise TypeError("settled custody requires its exact typed recovery index")
    index.__post_init__()
    if type(attempts) is not tuple or any(type(row) is not OperationalAttempt for row in attempts):
        raise TypeError("settled custody requires exact operational attempts")
    for row in attempts:
        row.__post_init__()
    if (len({row.attempt_id for row in attempts}) != len(attempts)
            or len({(row.task_id, row.ordinal) for row in attempts}) != len(attempts)):
        raise RunRecoveryError("settled custody repeats an attempt or task-local ordinal")
    bindings = {row.task_id: row for row in index.tasks}
    if any(row.run_id != index.run_id or row.task_id not in bindings for row in attempts):
        raise RunRecoveryError("settled custody changes the original run or task scope")
    entered = {}
    operational = {}
    for row in sorted(attempts, key=lambda row: (row.task_id, row.ordinal)):
        binding = bindings[row.task_id]
        operational[row.task_id] = operational.get(row.task_id, 0) + 1
        if row.ordinal != operational[row.task_id]:
            raise RunRecoveryError("settled custody loses its complete task-local operational history")
        candidate = next((value for value in binding.attempts if value.attempt_id == row.attempt_id), None)
        if candidate is None:
            expected_block = f"{index.run_id}.{row.task_id}.block-{row.ordinal:03d}"
            if row.disposition is not TaskAttemptDisposition.BLOCKED or row.attempt_id != expected_block:
                raise RunRecoveryError("settled custody substitutes an entered candidate or known nonattempt identity")
        else:
            entered[row.task_id] = entered.get(row.task_id, 0) + 1
            if candidate.ordinal != entered[row.task_id]:
                raise RunRecoveryError("settled custody changes the original executable candidate ordinal")
    latest = {row.task_id: row for row in sorted(attempts, key=lambda row: (row.task_id, row.ordinal))}
    completed, closed, unreachable, pending = set(), set(), set(), set()
    dependency_reasons = {TaskBlockReason.DEPENDENCY_BLOCKED.value, TaskBlockReason.DEPENDENCY_FAILED.value}
    for binding in sorted(index.tasks, key=lambda row: row.topological_ordinal):
        row = latest.get(binding.task_id)
        if row is not None and row.disposition is TaskAttemptDisposition.SUCCEEDED:
            completed.add(binding.task_id)
            continue
        candidates = {candidate.attempt_id for candidate in binding.attempts}
        spent = sum(value.task_id == binding.task_id and value.attempt_id in candidates
            and value.disposition in (TaskAttemptDisposition.FAILED, TaskAttemptDisposition.BLOCKED)
            for value in attempts)
        if row is not None and row.disposition is TaskAttemptDisposition.RUNNING:
            pending.add(binding.task_id)
        elif row is not None and (row.disposition is TaskAttemptDisposition.BLOCKED
                and row.block_kind is not None and row.block_kind.value == "DURABLE"
                or row.attempt_id in candidates and spent >= binding.maximum_attempts):
            closed.add(binding.task_id)
        elif (row is None or row.disposition is TaskAttemptDisposition.BLOCKED
                and row.attempt_id not in candidates and row.reason_code in dependency_reasons) and any(
                dependency in closed for dependency in binding.dependency_task_ids):
            closed.add(binding.task_id)
            unreachable.add(binding.task_id)
        else:
            pending.add(binding.task_id)
    return tuple(sorted(completed)), tuple(sorted(closed)), tuple(sorted(unreachable)), tuple(sorted(pending))



def _require_catalog_dependency_causes(*, dependency_order, candidate_events, receipts,
        nonattempts, catalog_blocks):
    """Require every catalog dependency block's actual direct cause.

    A catalog row cannot establish its own cause. Resolve candidate events and
    durable nonattempts in topological order without manufacturing new events.
    """
    from empirical_lawhood.runtime.execution import TaskBlockKind, TaskBlockReason

    failed, blocked = set(), set()
    for binding in dependency_order:
        task_id = binding.task_id
        if task_id in receipts:
            continue
        latest = next((candidate_events[task_id, candidate.attempt_id]
            for candidate in reversed(binding.attempts)
            if (task_id, candidate.attempt_id) in candidate_events), None)
        if latest is not None:
            if task_id in catalog_blocks:
                raise RunRecoveryError("catalog block conflicts with consumed candidate history")
            if latest.disposition is TaskRecoveryDisposition.FAILED:
                failed.add(task_id)
            elif latest.disposition is TaskRecoveryDisposition.BLOCKED:
                blocked.add(task_id)
            else:
                raise RunRecoveryError("dependency cause lacks its canonical receipt")
            continue
        nonattempt = nonattempts.get(task_id)
        if nonattempt is not None:
            reason = TaskBlockReason(nonattempt.reason_codes[0])
            if reason.kind is not TaskBlockKind.DURABLE:
                raise RunRecoveryError("nonattempt is not a retained durable block")
        elif task_id in catalog_blocks:
            reason = TaskBlockReason(catalog_blocks[task_id])
        else:
            continue
        direct_failed = any(dependency in failed for dependency in binding.dependency_task_ids)
        direct_blocked = any(dependency in blocked for dependency in binding.dependency_task_ids)
        if (reason is TaskBlockReason.DEPENDENCY_FAILED and not direct_failed
                or reason is TaskBlockReason.DEPENDENCY_BLOCKED and (direct_failed or not direct_blocked)):
            raise RunRecoveryError("dependency block lacks its actual direct cause: " + task_id)
        blocked.add(task_id)

class ExternalRunRecoveryStore:
    """One external, scan-free recovery stream for a frozen execution wave."""

    def __init__(self, plane: ExternalArtifactPlane, *, minimum_free_bytes: int=0) -> None:
        if minimum_free_bytes < 0:
            raise ValueError('recovery free-space floor must be nonnegative')
        self.plane = plane
        self.minimum_free_bytes = minimum_free_bytes
        self._resource_read_journal = None

    @staticmethod
    def _index_parents(index: ProtocolRunRecoveryIndex) -> tuple[ArtifactLineageParent, ...]:
        development = isinstance(index, DevelopmentRunRecoveryIndex)
        values = (
            ArtifactLineageParent(
                identity=index.execution_plan,
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if development else VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE if development else OutcomeAccess.OUTCOME_BLIND,
            ),
            *(
                ArtifactLineageParent(
                    identity=authority,
                    visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                    outcome_access=OutcomeAccess.OUTCOME_BLIND,
                )
                for authority in index.authority_identities
            ),
        )
        return tuple(sorted(values, key=lineage_parent_sort_key))

    def _validate_index_limits(self, index: ProtocolRunRecoveryIndex) -> None:
        limits = self.plane.custody_limits
        if (limits.exceeds("recovery_tasks", len(index.tasks))
                or limits.exceeds("recovery_candidates", sum(len(t.attempts) for t in index.tasks))
                or any(limits.exceeds("recovery_attempts_per_task", t.maximum_attempts) for t in index.tasks)
                or limits.exceeds("recovery_index_bytes", len(index.canonical_bytes()))):
            raise RunRecoveryError("recovery index exceeds its selected custody allowance")

    def freeze(self, index: ProtocolRunRecoveryIndex) -> None:
        self._validate_index_limits(index)
        parents = self._index_parents(index)
        self.plane.write(
            ArtifactWriteRequest(
                logical_artifact_id=index.recovery_index_id,
                relative_path=index.index_relative_path,
                payload_schema=index.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json",
                publication_scope_id=f"run-recovery.{index.run_id}.{index.wave_id}",
                publication_scope_relative_root=(f"runs/{index.run_id}/recovery/{index.wave_id}"),
                payload=index.canonical_bytes(),
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if isinstance(index, DevelopmentRunRecoveryIndex) else VisibilityCeiling.PROSPECTIVE,
                parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE if isinstance(index, DevelopmentRunRecoveryIndex) else OutcomeAccess.OUTCOME_BLIND,
                logical_content_sha256=index.fingerprint(),
                lineage_parents=parents,
                minimum_free_bytes=self.minimum_free_bytes,
            )
        )
        observed = self.read_index(
            index.index_relative_path,
            expected_schema=index.SCHEMA,
        )
        if observed != index:
            raise RunRecoveryError("persisted run recovery index differs after freeze")

    def _read_payload(
        self,
        relative_path: str,
        *,
        expected_schema: str,
        maximum_bytes: int | None,
    ) -> bytes | None:
        selected = self._read_payload_envelope(relative_path,
            expected_schema=expected_schema, maximum_bytes=maximum_bytes)
        if selected is None:
            return None
        path, manifest = selected
        try:
            self.plane.verify_manifest(manifest)
        except (
            ArtifactIdentityConflict,
            BoundedFileIOError,
            OSError,
            ValueError,
        ) as error:
            raise RunRecoveryError("recovery artifact custody is invalid") from error
        return self._read_payload_body(path, manifest)

    def _read_payload_envelope(self, relative_path, *, expected_schema, maximum_bytes, _paths=None):
        """Resolve the original bounded recovery pair without carrying a proof."""
        path = (self.plane.root.resolve(relative_path, for_write=False)
            if _paths is None else _paths[relative_path])
        manifest_path = (self.plane.root.resolve(f"{relative_path}.manifest.json", for_write=False)
            if _paths is None else _paths[relative_path + '.manifest.json'])
        if not path.exists() and not manifest_path.exists():
            return None
        if not path.is_file() or not manifest_path.is_file():
            raise RunRecoveryError("recovery artifact/manifest pair is partial")
        try:
            manifest = decode_artifact_manifest(
                read_bounded_bytes(
                    manifest_path,
                    maximum_bytes=self.plane.custody_limits.manifest_bytes,
                ),
                maximum_bytes=self.plane.custody_limits.manifest_bytes,
            )
            if (
                manifest.materialization.relative_path != relative_path
                or (maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes)
                or manifest.logical.payload_schema != expected_schema
                or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or manifest.logical.media_type != "application/json"
            ):
                raise RunRecoveryError("recovery artifact violates its bounded contract")
        except (
            ArtifactIdentityConflict,
            BoundedFileIOError,
            OSError,
            ValueError,
        ) as error:
            raise RunRecoveryError("recovery artifact custody is invalid") from error
        return path, manifest

    def _read_payload_body(self, path, manifest):
        """Consume the exact body under its live member verification callback."""
        try:
            payload = read_bounded_bytes(path, maximum_bytes=manifest.materialization.size_bytes)
        except (
            ArtifactIdentityConflict,
            BoundedFileIOError,
            OSError,
            ValueError,
        ) as error:
            raise RunRecoveryError("recovery artifact custody is invalid") from error
        if (
            len(payload) != manifest.materialization.size_bytes
            or hashlib.sha256(payload).hexdigest() != manifest.logical.content_sha256
        ):
            raise RunRecoveryError("recovery artifact bytes differ from their manifest")
        return payload

    def read_index(
        self,
        relative_path: str,
        *,
        expected_schema: str,
    ) -> ProtocolRunRecoveryIndex:
        if expected_schema not in {
            ProtocolRunRecoveryIndex.SCHEMA,
            CandidateRunRecoveryIndex.SCHEMA,
            EnvelopeRunRecoveryIndex.SCHEMA,
            RunRecoveryIndex.SCHEMA,
            DevelopmentRunRecoveryIndex.SCHEMA,
            RetainedE3RepairRecoveryIndex.SCHEMA,
            RetainedE3ContinuedRepairRecoveryIndex.SCHEMA,
            DevelopmentOutputRepairRecoveryIndex.SCHEMA,
            DevelopmentControllerRepairRecoveryIndex.SCHEMA,
            DevelopmentNativeContinuationRecoveryIndex.SCHEMA,
        }:
            raise RunRecoveryError("run recovery index schema is unsupported")
        payload = self._read_payload(
            relative_path,
            expected_schema=expected_schema,
            maximum_bytes=self.plane.custody_limits.recovery_index_bytes,
        )
        if payload is None:
            raise RunRecoveryError("run recovery index is missing")
        try:
            index = decode_run_recovery_index(payload, maximum_bytes=self.plane.custody_limits.recovery_index_bytes)
        except (CanonicalizationError, ValueError) as error:
            raise RunRecoveryError("run recovery index is invalid") from error
        self._validate_index_limits(index)
        if index.index_relative_path != relative_path:
            raise RunRecoveryError("run recovery index path identity differs")
        return index

    def _event_visibility(
        self,
        receipt: CanonicalTaskReceipt | None,
    ) -> tuple[VisibilityCeiling, OutcomeAccess]:
        if receipt is None or not receipt.output_logical_artifacts:
            return VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND
        return (
            VisibilityCeiling.most_restrictive(
                VisibilityCeiling.PROSPECTIVE,
                *(value.visibility_ceiling for value in receipt.output_logical_artifacts),
            ),
            most_restrictive_outcome_access(
                OutcomeAccess.OUTCOME_BLIND,
                *(value.outcome_access for value in receipt.output_logical_artifacts),
            ),
        )

    def append_event(
        self,
        index: ProtocolRunRecoveryIndex,
        event: ProtocolTaskRecoveryEvent,
        *,
        receipt: CanonicalTaskReceipt | None = None,
    ) -> None:
        if self.plane.custody_limits.exceeds("recovery_event_bytes", len(event.canonical_bytes())):
            raise RunRecoveryError("recovery event exceeds its selected byte allowance")
        path = self._event_path(index, event)
        visibility, outcome_access = self._event_visibility(receipt)
        if isinstance(index, DevelopmentRunRecoveryIndex):
            visibility = VisibilityCeiling.most_restrictive(VisibilityCeiling.DEVELOPMENT_ONLY, visibility)
            outcome_access = most_restrictive_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE, outcome_access)
        parents = [
            ArtifactLineageParent(
                identity=ObjectIdentity.from_record(index.recovery_index_id, index),
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if isinstance(index, DevelopmentRunRecoveryIndex) else VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE if isinstance(index, DevelopmentRunRecoveryIndex) else OutcomeAccess.OUTCOME_BLIND,
            )
        ]
        if receipt is not None:
            parents.append(
                ArtifactLineageParent(
                    identity=ObjectIdentity.from_record(receipt.receipt_id, receipt),
                    visibility_ceiling=visibility,
                    outcome_access=outcome_access,
                )
            )
        lineage = tuple(sorted(parents, key=lineage_parent_sort_key))
        self.plane.write(
            ArtifactWriteRequest(
                logical_artifact_id=event.event_id,
                relative_path=path,
                payload_schema=event.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json",
                publication_scope_id=f"run-recovery-events.{index.run_id}.{index.wave_id}",
                publication_scope_relative_root=(
                    f"runs/{index.run_id}/recovery/{index.wave_id}/events"
                ),
                payload=event.canonical_bytes(),
                visibility_ceiling=visibility,
                parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in lineage),
                outcome_access=outcome_access,
                logical_content_sha256=event.fingerprint(),
                lineage_parents=lineage,
                minimum_free_bytes=self.minimum_free_bytes,
            )
        )

    @staticmethod
    def _envelope_event_path(
        index: EnvelopeRunRecoveryIndex,
        event: ExecutionEnvelopeEvent,
    ) -> str:
        return (
            f"{index.envelope_event_root_relative_path}/"
            f"{event.sequence_number:09d}.{event.event_id}.json"
        )

    def append_envelope_event(
        self,
        index: EnvelopeRunRecoveryIndex,
        event: ExecutionEnvelopeEvent,
        *,
        visibility_ceiling: VisibilityCeiling,
        outcome_access: OutcomeAccess,
    ) -> str:
        """Persist one immutable envelope event before it is trusted for recovery."""

        relative_path = self._envelope_event_path(index, event)
        parent = ArtifactLineageParent(
            identity=ObjectIdentity.from_record(index.recovery_index_id, index),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND,
        )
        self.plane.write(
            ArtifactWriteRequest(
                logical_artifact_id=event.event_id,
                relative_path=relative_path,
                payload_schema=ExecutionEnvelopeEvent.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json",
                publication_scope_id=(f"run-envelope-events.{index.run_id}.{index.wave_id}"),
                publication_scope_relative_root=index.envelope_event_root_relative_path,
                payload=event.canonical_bytes(),
                visibility_ceiling=visibility_ceiling,
                parent_visibility_ceilings=(parent.visibility_ceiling,),
                outcome_access=outcome_access,
                logical_content_sha256=event.fingerprint(),
                lineage_parents=(parent,),
                minimum_free_bytes=self.minimum_free_bytes,
            )
        )
        observed = self.read_envelope_event(index, relative_path)
        if observed != event:
            raise RunRecoveryError("persisted execution-envelope event differs")
        return relative_path

    def read_envelope_event(
        self,
        index: EnvelopeRunRecoveryIndex,
        relative_path: str,
    ) -> ExecutionEnvelopeEvent:
        expected_prefix = f"{index.envelope_event_root_relative_path}/"
        if not relative_path.startswith(expected_prefix):
            raise RunRecoveryError("execution-envelope event lies outside its root")
        payload = self._read_payload(
            relative_path,
            expected_schema=ExecutionEnvelopeEvent.SCHEMA,
            maximum_bytes=self.plane.custody_limits.recovery_event_bytes,
        )
        if payload is None:
            raise RunRecoveryError("execution-envelope event is missing")
        try:
            event = decode_execution_envelope_event(payload, maximum_bytes=self.plane.custody_limits.recovery_event_bytes)
        except (CanonicalizationError, ValueError) as error:
            raise RunRecoveryError("execution-envelope event is invalid") from error
        if self._envelope_event_path(index, event) != relative_path:
            raise RunRecoveryError("execution-envelope event path identity differs")
        return event

    def reconstruct_execution_envelope(
        self,
        *,
        index: EnvelopeRunRecoveryIndex,
        envelope_id: str,
        spec: ExecutionEnvelopeSpec,
        execution_plan: ObjectIdentity,
        event_relative_paths: tuple[str, ...],
    ) -> RunExecutionEnvelope:
        """Read an exact caller-bound event roster; never scan or infer missing events."""

        if self.plane.custody_limits.exceeds("recovery_events", len(event_relative_paths)):
            raise RunRecoveryError("execution-envelope event count exceeds its bound")
        events = tuple(
            self.read_envelope_event(index, relative_path) for relative_path in event_relative_paths
        )
        return reconstruct_execution_envelope_from_external_events(
            index=index,
            envelope_id=envelope_id,
            spec=spec,
            execution_plan=execution_plan,
            event_payloads=tuple(value.canonical_bytes() for value in events),
            maximum_events=self.plane.custody_limits.recovery_events,
            maximum_event_bytes=self.plane.custody_limits.recovery_event_bytes,
        )

    def reconstruct_execution_resource_envelope(
        self,
        *,
        index: RunRecoveryIndex,
        envelope_id: str,
        spec: ExecutionResourceEnvelopeSpec,
        execution_plan: ObjectIdentity,
        jit_graph_signature_manifest: JitGraphSignatureManifest | None,
    ) -> RunExecutionResourceEnvelope:
        """Authenticate the same journal used for durable reservation admission."""

        if (
            (index.resource_envelope_event_root_relative_path
                != DEFAULT_EXECUTION_RESOURCE_ENVELOPE_STATE_ROOT
                and not isinstance(index, RetainedE3RepairRecoveryIndex))
            or envelope_id != f"run-resource-envelope.{index.run_id}"
            or index.execution_resource_envelope_spec
            != ObjectIdentity.from_record(spec.envelope_spec_id, spec)
            or index.execution_plan != execution_plan
            or spec.issued_study_extensions != index.issued_extension_set
            or index.jit_graph_signature_manifest != spec.jit_graph_signature_manifest
            or spec.jit_graph_signature_manifest
            != (
                None
                if jit_graph_signature_manifest is None
                else ObjectIdentity.from_record(
                    jit_graph_signature_manifest.manifest_id, jit_graph_signature_manifest
                )
            )
        ):
            raise RunRecoveryError("resource-envelope recovery inputs differ from the index")
        try:
            owned = getattr(self, "_failed_history_resource_journal", None)
            if owned is None:
                journal = self._resource_read_journal
                if (journal is None or journal.root is not self.plane.root
                        or journal.state_root_relative_path != index.resource_envelope_event_root_relative_path):
                    journal = ExternalExecutionResourceEnvelopeStore(self.plane.root,
                        state_root_relative_path=index.resource_envelope_event_root_relative_path)
                    self._resource_read_journal = journal
                # load() still authenticates every origin/journal byte. The
                # owner can reuse only the replay of an identical full prefix.
                envelope = journal.load(envelope_id)
            else:
                verification = getattr(self.plane, "_read_verification", None)
                if (type(owned) is not ExternalExecutionResourceEnvelopeStore
                        or owned.root is not self.plane.root
                        or verification is None or not verification.active):
                    raise RunRecoveryError("failed-history resource owner escaped its active verification lifetime")
                # The first current() authenticates the full committed prefix.
                # Every later call rechecks actual head/origin/journal stamps;
                # a change invalidates it and replays the original owner.
                envelope = owned.current(envelope_id)
        except (KeyError, OSError, ValueError) as error:
            raise RunRecoveryError("resource-envelope journal recovery failed") from error
        if envelope.spec != spec or envelope.execution_plan != execution_plan:
            raise RunRecoveryError("resource-envelope journal substitutes the issued plan")
        return envelope

    @staticmethod
    def _event_path(index: ProtocolRunRecoveryIndex, event: ProtocolTaskRecoveryEvent) -> str:
        task = index.task(event.task_id)
        if event.disposition is TaskRecoveryDisposition.NOT_ATTEMPTED:
            return task.nonattempt_event_relative_path
        assert event.attempt_id is not None
        for candidate in task.attempts:
            if candidate.attempt_id == event.attempt_id:
                return candidate.event_relative_path
        raise RunRecoveryError("task recovery event lies outside its index")

    def read_event(
        self,
        index: ProtocolRunRecoveryIndex,
        relative_path: str,
    ) -> TaskRecoveryEvent | None:
        payload = self._read_payload(
            relative_path,
            expected_schema=index.TASK_EVENT_SCHEMA,
            maximum_bytes=self.plane.custody_limits.recovery_event_bytes,
        )
        return self._decode_event_payload(index, relative_path, payload)

    def _decode_event_payload(self, index, relative_path, payload):
        if isinstance(index, (RetainedE3RepairRecoveryIndex, DevelopmentOutputRepairRecoveryIndex)):
            owners = tuple(index.event_owner(row.task_id) for row in index.tasks
                if relative_path in (row.nonattempt_event_relative_path,
                    *(candidate.event_relative_path for candidate in row.attempts)))
            if len(owners) != 1:
                raise RunRecoveryError('repair event has no unique frozen task owner')
            index, = owners
        return self._decode_event_payload_at_identity(index, relative_path, payload,
            ObjectIdentity.from_record(index.recovery_index_id, index))

    def _decode_event_payload_at_identity(self, index, relative_path, payload, index_identity):
        """Decode under an identity prepared by this invocation's exact owner."""
        if payload is None:
            return None
        try:
            event = decode_task_recovery_event(payload, maximum_bytes=self.plane.custody_limits.recovery_event_bytes)
        except (CanonicalizationError, ValueError) as error:
            raise RunRecoveryError("task recovery event is invalid") from error
        if (
            event.recovery_index != index_identity
            or event.run_id != index.run_id
            or self._event_path(index, event) != relative_path
        ):
            raise RunRecoveryError("task recovery event differs from its index")
        return event

    def record_receipt(self, index: ProtocolRunRecoveryIndex, receipt: CanonicalTaskReceipt) -> None:
        event = TaskRecoveryEvent.from_receipt(index, receipt)
        self.append_event(index, event, receipt=receipt)







    def record_failure(self, index: ProtocolRunRecoveryIndex, *, task_id: str, attempt_id: str, reason_code: str, failure: OperationalFailureDiagnostic, blocked: bool=False) -> None:
        task = index.task(task_id)
        candidate = next((value for value in task.attempts if value.attempt_id == attempt_id), None)
        if candidate is None:
            raise RunRecoveryError('failed attempt lies outside its recovery index')
        event = TaskRecoveryEvent(event_id=f'recovery-event.{attempt_id}.failed', recovery_index=ObjectIdentity.from_record(index.recovery_index_id, index), run_id=index.run_id, task_id=task_id, attempt_id=attempt_id, attempt_ordinal=candidate.ordinal, disposition=TaskRecoveryDisposition.BLOCKED if blocked else TaskRecoveryDisposition.FAILED, receipt_id=None, receipt_relative_path=None, receipt_sha256=None, receipt_schema=None, output_materialization_ids=(), reason_codes=(reason_code,), failure=failure)
        self.append_event(index, event)

    def record_native_failure_diagnostic(self, index: ProtocolRunRecoveryIndex, *, task_id: str, attempt_id: str, contact: NativeEffectContact, diagnostic: OperationalFailureDiagnostic, visibility_ceiling: VisibilityCeiling, outcome_access: OutcomeAccess) -> str:
        """Retain the initiating cause without changing an UNKNOWN event.

            The scheduler supplies the contact it has just authenticated. This
            operational record creates no completion, retry or native authority.
            """
        task = index.task(task_id)
        candidate = next((value for value in task.attempts if value.attempt_id == attempt_id), None)
        if candidate is None or type(contact) is not NativeEffectContact or type(diagnostic) is not OperationalFailureDiagnostic or (contact.run_id != index.run_id) or (contact.task_id != task_id) or (contact.attempt_id != attempt_id) or (contact.execution_plan != index.execution_plan):
            raise RunRecoveryError('native failure diagnostic changes its actual contacted attempt')
        contact.__post_init__()
        diagnostic.__post_init__()
        expected_commit = index.implementation_commit
        if contact.implementation_commit != expected_commit:
            raise RunRecoveryError('native failure diagnostic changes its actual producing source')
        raw = diagnostic.canonical_bytes()
        if self.plane.custody_limits.exceeds('recovery_event_bytes', len(raw)):
            raise RunRecoveryError('native failure diagnostic exceeds its selected recovery allowance')
        token = hashlib.sha256(attempt_id.encode()).hexdigest()
        relative = candidate.event_relative_path.removesuffix('.json') + '.native-failure-diagnostic.json'
        development = isinstance(index, DevelopmentRunRecoveryIndex)
        parent_ceiling = VisibilityCeiling.DEVELOPMENT_ONLY if development else VisibilityCeiling.PROSPECTIVE
        parent_access = OutcomeAccess.DEVELOPMENT_VISIBLE if development else OutcomeAccess.OUTCOME_BLIND
        ceiling = VisibilityCeiling.most_restrictive(visibility_ceiling, parent_ceiling)
        access = most_restrictive_outcome_access(outcome_access, parent_access)
        contact_id = 'native-contact.' + index.run_id + '.' + hashlib.sha256(task_id.encode()).hexdigest()
        parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(index.recovery_index_id, index), parent_ceiling, parent_access), ArtifactLineageParent(ObjectIdentity.from_record(contact_id, contact), ceiling, access)), key=lineage_parent_sort_key))
        self.plane.write(ArtifactWriteRequest(logical_artifact_id='native-failure-diagnostic.' + token, relative_path=relative, payload_schema=diagnostic.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', publication_scope_id='native-failure-diagnostic.' + token, publication_scope_relative_root=relative.rsplit('/', 1)[0], payload=raw, visibility_ceiling=ceiling, parent_visibility_ceilings=tuple((value.visibility_ceiling for value in parents)), outcome_access=access, logical_content_sha256=diagnostic.fingerprint(), lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes))
        observed = self._read_payload(relative, expected_schema=diagnostic.SCHEMA, maximum_bytes=self.plane.custody_limits.recovery_event_bytes)
        if observed != raw:
            raise RunRecoveryError('persisted native failure diagnostic differs')
        return relative

    def record_worker_preflight(self, index: ProtocolRunRecoveryIndex, *, task_id: str, attempt_id: str, result: WorkerPreflightResult, visibility_ceiling: VisibilityCeiling, outcome_access: OutcomeAccess) -> str:
        """Retain the actual refused prerequisite census at its input ceiling.

            The ordinary failure event stays small and historically unchanged.
            Reasons remain in this guarded diagnostic, never in public log text.
            """
        task = index.task(task_id)
        if type(result) is not WorkerPreflightResult or result.ready or result.invocation.object_id != 'prepared.' + attempt_id or (attempt_id not in {value.attempt_id for value in task.attempts}):
            raise RunRecoveryError('worker preflight diagnostic changes its actual refused attempt')
        raw = result.canonical_bytes()
        if self.plane.custody_limits.exceeds('recovery_event_bytes', len(raw)):
            raise RunRecoveryError('worker preflight diagnostic exceeds its selected recovery allowance')
        token = hashlib.sha256(attempt_id.encode()).hexdigest()
        relative = f'runs/{index.run_id}/recovery/{index.wave_id}/preflight/{token}.json'
        development = isinstance(index, DevelopmentRunRecoveryIndex)
        parent = ArtifactLineageParent(identity=ObjectIdentity.from_record(index.recovery_index_id, index), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if development else VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE if development else OutcomeAccess.OUTCOME_BLIND)
        self.plane.write(ArtifactWriteRequest(logical_artifact_id='worker-preflight.' + token, relative_path=relative, payload_schema=result.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', publication_scope_id=f'run-recovery.{index.run_id}.{index.wave_id}', publication_scope_relative_root=f'runs/{index.run_id}/recovery/{index.wave_id}', payload=raw, visibility_ceiling=VisibilityCeiling.most_restrictive(visibility_ceiling, parent.visibility_ceiling), parent_visibility_ceilings=(parent.visibility_ceiling,), outcome_access=most_restrictive_outcome_access(outcome_access, parent.outcome_access), logical_content_sha256=result.fingerprint(), lineage_parents=(parent,), minimum_free_bytes=self.minimum_free_bytes))
        return relative

    def record_not_attempted(
        self,
        index: ProtocolRunRecoveryIndex,
        *,
        task_id: str,
        reason: TaskBlockReason,
    ) -> None:
        if reason.kind.value != "DURABLE":
            return
        event = TaskRecoveryEvent(
            event_id=f"recovery-event.{index.run_id}.{task_id}.not-attempted",
            recovery_index=ObjectIdentity.from_record(index.recovery_index_id, index),
            run_id=index.run_id,
            task_id=task_id,
            attempt_id=None,
            attempt_ordinal=None,
            disposition=TaskRecoveryDisposition.NOT_ATTEMPTED,
            receipt_id=None,
            receipt_relative_path=None,
            receipt_sha256=None,
            receipt_schema=None,
            output_materialization_ids=(),
            reason_codes=(reason.value,),
            failure=None,
        )
        self.append_event(index, event)

    def read_terminal(
        self,
        index: ProtocolRunRecoveryIndex,
    ) -> ProtocolRunRecoveryTerminalEvent | None:
        payload = self._read_payload(
            index.terminal_event_relative_path,
            expected_schema=index.terminal_event_schema,
            maximum_bytes=self.plane.custody_limits.recovery_index_bytes,
        )
        if payload is None:
            return None
        try:
            event = decode_run_recovery_terminal_event(payload, maximum_bytes=self.plane.custody_limits.recovery_index_bytes)
        except (CanonicalizationError, ValueError) as error:
            raise RunRecoveryError("run recovery terminal event is invalid") from error
        if (
            event.recovery_index != ObjectIdentity.from_record(index.recovery_index_id, index)
            or event.run_id != index.run_id
        ):
            raise RunRecoveryError("run recovery terminal event differs from its index")
        return event

    def record_terminal(self, index: ProtocolRunRecoveryIndex, *, status: OperationalStatus, attempts: tuple[OperationalAttempt, ...], receipts: tuple[CanonicalTaskReceipt, ...]) -> None:
        derivative_slots = frozenset()
        if status not in {OperationalStatus.SUCCEEDED, OperationalStatus.FAILED, OperationalStatus.BLOCKED}:
            raise RunRecoveryError('run recovery closure requires a terminal status')
        latest_operational = {attempt.task_id: attempt for attempt in sorted(attempts, key=lambda value: (value.task_id, value.ordinal))}
        unreachable = ()
        if isinstance(index, DevelopmentRunRecoveryIndex):
            _, _, unreachable, pending = settled_recovery_tasks(index, attempts)
            complete_scope = not pending and set(latest_operational) == {binding.task_id for binding in index.tasks}
            if status is OperationalStatus.BLOCKED and (not complete_scope):
                return
            if not complete_scope:
                unreachable = ()
        elif status is OperationalStatus.BLOCKED:
            for attempt in latest_operational.values():
                if attempt.task_id in derivative_slots:
                    continue
                if attempt.disposition is not TaskAttemptDisposition.BLOCKED or attempt.block_kind is None or attempt.block_kind.value != 'RETRYABLE':
                    continue
                binding = index.task(attempt.task_id)
                candidate_ids = {value.attempt_id for value in binding.attempts}
                consumed = sum((value.task_id == attempt.task_id and value.attempt_id in candidate_ids and (value.disposition in {TaskAttemptDisposition.FAILED, TaskAttemptDisposition.BLOCKED}) for value in attempts))
                if attempt.attempt_id not in candidate_ids or consumed < binding.maximum_attempts:
                    return
        dependency_events = []
        for task_id in unreachable:
            attempt = latest_operational[task_id]
            event = TaskRecoveryEvent(event_id=f'recovery-event.{index.run_id}.{task_id}.not-attempted', recovery_index=ObjectIdentity.from_record(index.recovery_index_id, index), run_id=index.run_id, task_id=task_id, attempt_id=None, attempt_ordinal=None, disposition=TaskRecoveryDisposition.NOT_ATTEMPTED, receipt_id=None, receipt_relative_path=None, receipt_sha256=None, receipt_schema=None, output_materialization_ids=(), reason_codes=(attempt.reason_code,), failure=None)
            dependency_events.append(event)
        receipts_by_attempt = {receipt.attempt_id: receipt for receipt in receipts}
        terminal_attempts: list[RecoveryTerminalAttempt] = []
        for attempt in sorted(attempts, key=lambda value: (value.task_id, value.ordinal)):
            if attempt.disposition is TaskAttemptDisposition.RUNNING:
                raise RunRecoveryError('terminal recovery closure contains a live attempt')
            if attempt.disposition is TaskAttemptDisposition.SUCCEEDED:
                receipt = receipts_by_attempt.get(attempt.attempt_id)
                if receipt is None:
                    raise RunRecoveryError('successful terminal attempt lacks its receipt')
                disposition = RecoveryTerminalDisposition.SUCCEEDED
                reason_code = None
                receipt_id = receipt.receipt_id
                receipt_sha256 = receipt.fingerprint()
            else:
                if attempt.reason_code is None:
                    raise RunRecoveryError('non-success terminal attempt lacks its reason')
                disposition = RecoveryTerminalDisposition(attempt.disposition.value)
                reason_code = attempt.reason_code
                receipt_id = None
                receipt_sha256 = None
            terminal_attempts.append(RecoveryTerminalAttempt(attempt_id=attempt.attempt_id, task_id=attempt.task_id, ordinal=attempt.ordinal, disposition=disposition, reason_code=reason_code, receipt_id=receipt_id, receipt_sha256=receipt_sha256))
        if set(receipts_by_attempt) != {value.attempt_id for value in terminal_attempts if value.disposition is RecoveryTerminalDisposition.SUCCEEDED}:
            raise RunRecoveryError('terminal receipt set differs from successful attempts')
        latest = {attempt.task_id: attempt.disposition for attempt in terminal_attempts}
        event_type = DevelopmentNativeContinuationTerminalEvent if type(index) is DevelopmentNativeContinuationRecoveryIndex else DevelopmentControllerRepairTerminalEvent if type(index) is DevelopmentControllerRepairRecoveryIndex else DevelopmentOutputRepairTerminalEvent if type(index) is DevelopmentOutputRepairRecoveryIndex else RetainedE3ContinuedRepairTerminalEvent if type(index) is RetainedE3ContinuedRepairRecoveryIndex else RetainedE3RepairTerminalEvent if type(index) is RetainedE3RepairRecoveryIndex else DevelopmentRunRecoveryTerminalEvent if isinstance(index, DevelopmentRunRecoveryIndex) else RunRecoveryTerminalEvent if isinstance(index, RunRecoveryIndex) else EnvelopeRunRecoveryTerminalEvent if isinstance(index, EnvelopeRunRecoveryIndex) else CandidateRunRecoveryTerminalEvent if isinstance(index, CandidateRunRecoveryIndex) else ProtocolRunRecoveryTerminalEvent
        event = event_type(terminal_event_id=f'recovery-terminal.{index.run_id}.{index.wave_id}', recovery_index=ObjectIdentity.from_record(index.recovery_index_id, index), run_id=index.run_id, operational_status=status.value, attempts=tuple(terminal_attempts), completed_task_ids=tuple(sorted((task_id for task_id, disposition in latest.items() if disposition is RecoveryTerminalDisposition.SUCCEEDED))), failed_task_ids=tuple(sorted((task_id for task_id, disposition in latest.items() if disposition is RecoveryTerminalDisposition.FAILED))), blocked_task_ids=tuple(sorted((task_id for task_id, disposition in latest.items() if disposition is RecoveryTerminalDisposition.BLOCKED))))
        visibility, outcome_access = self._event_visibility(next(iter(receipts), None))
        if receipts:
            visibility = VisibilityCeiling.most_restrictive(VisibilityCeiling.PROSPECTIVE, *(logical.visibility_ceiling for receipt in receipts for logical in receipt.output_logical_artifacts))
            outcome_access = most_restrictive_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(logical.outcome_access for receipt in receipts for logical in receipt.output_logical_artifacts))
        if isinstance(index, DevelopmentRunRecoveryIndex):
            visibility = VisibilityCeiling.most_restrictive(VisibilityCeiling.DEVELOPMENT_ONLY, visibility)
            outcome_access = most_restrictive_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE, outcome_access)
        parents = (ArtifactLineageParent(identity=ObjectIdentity.from_record(index.recovery_index_id, index), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if isinstance(index, DevelopmentRunRecoveryIndex) else VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE if isinstance(index, DevelopmentRunRecoveryIndex) else OutcomeAccess.OUTCOME_BLIND),)
        if self.plane.custody_limits.exceeds('recovery_index_bytes', len(event.canonical_bytes())):
            raise RunRecoveryError('recovery terminal exceeds its selected byte allowance')
        for dependency_event in dependency_events:
            self.append_event(index, dependency_event)
        self.plane.write(ArtifactWriteRequest(logical_artifact_id=event.terminal_event_id, relative_path=index.terminal_event_relative_path, payload_schema=event.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', publication_scope_id=f'run-recovery.{index.run_id}.{index.wave_id}', publication_scope_relative_root=f'runs/{index.run_id}/recovery/{index.wave_id}', payload=event.canonical_bytes(), visibility_ceiling=visibility, parent_visibility_ceilings=tuple((parent.visibility_ceiling for parent in parents)), outcome_access=outcome_access, logical_content_sha256=event.fingerprint(), lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes))
        if self.read_terminal(index) != event:
            raise RunRecoveryError('persisted terminal recovery event differs')

    @staticmethod
    def _validate_receipt_static(index: ProtocolRunRecoveryIndex, task: ProtocolExecutionTask, candidate: RecoveryAttemptCandidate, receipt: CanonicalTaskReceipt) -> None:
        logical = tuple(sorted(((value.logical_artifact_id, value.payload_schema) for value in receipt.output_logical_artifacts)))
        expected = tuple(sorted(((value.logical_artifact_id, value.payload_schema) for value in task.outputs)))
        if receipt.run_id != index.run_id or receipt.task_id != task.task_id or receipt.attempt_id != candidate.attempt_id or (receipt.implementation_commit != index.implementation_commit) or (receipt.operational_status is not OperationalStatus.SUCCEEDED) or (not receipt.checks) or any((not check.passed for check in receipt.checks)) or receipt.reason_codes or (logical != expected) or (len(receipt.output_materializations) != len(task.outputs)):
            raise RunRecoveryError('task receipt differs from the frozen recovery index')

    @staticmethod
    def _restore_attempt(
        repository: OperationalRepository,
        *,
        run_id: str,
        attempt_id: str,
        task_id: str,
        disposition: TaskAttemptDisposition,
        reason_code: str | None,
        existing: dict[str, OperationalAttempt],
    ) -> None:
        prior = existing.get(attempt_id)
        if prior is not None:
            if prior.task_id != task_id or prior.run_id != run_id:
                raise RunRecoveryError("operational attempt identity conflicts with recovery")
            if prior.disposition is TaskAttemptDisposition.RUNNING:
                if disposition is TaskAttemptDisposition.SUCCEEDED:
                    repository.complete_attempt(attempt_id)
                elif disposition is TaskAttemptDisposition.FAILED:
                    assert reason_code is not None
                    repository.fail_attempt(attempt_id, reason_code)
                else:
                    assert reason_code is not None
                    repository.block_attempt(attempt_id, TaskBlockReason(reason_code))
                return
            if prior.disposition is not disposition or prior.reason_code != reason_code:
                raise RunRecoveryError("operational attempt differs from external recovery")
            return
        repository.start_attempt(
            run_id=run_id,
            task_id=task_id,
            attempt_id=attempt_id,
            lease_id=f"lease.recovered.{attempt_id}",
            owner_id="external-run-recovery",
            expires_epoch_seconds=1,
        )
        if disposition is TaskAttemptDisposition.SUCCEEDED:
            repository.complete_attempt(attempt_id)
        elif disposition is TaskAttemptDisposition.FAILED:
            assert reason_code is not None
            repository.fail_attempt(attempt_id, reason_code)
        else:
            assert reason_code is not None
            repository.block_attempt(attempt_id, TaskBlockReason(reason_code))

    def reconcile(self, index: ProtocolRunRecoveryIndex, plan: ProtocolExecutionPlan, repository: OperationalRepository, receipt_store: TaskReceiptStore, *, repair_missing_events: bool=True) -> RunRecoveryReport:
        """Rebuild bounded run/task state without directory scans or workers."""
        if type(repair_missing_events) is not bool:
            raise TypeError('repair_missing_events must be an exact bool')
        try:
            index.validate_plan(plan)
        except ValueError as error:
            raise RunRecoveryError('run recovery index does not authorize this plan') from error
        if self.read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
            raise RunRecoveryError('external recovery index differs from the supplied index')
        repository.register_run(index.run_id, plan.fingerprint())
        existing = {attempt.attempt_id: attempt for attempt in repository.attempts(index.run_id)}
        tasks = {task.task_id: task for task in plan.tasks}
        self._validate_index_limits(index)
        candidate_count = sum((len(task.attempts) for task in index.tasks))
        terminal = self.read_terminal(index)
        if terminal is not None:
            return self._reconcile_terminal(index=index, plan=plan, terminal=terminal, repository=repository, receipt_store=receipt_store, existing=existing, candidate_count=candidate_count, require_complete_events=not repair_missing_events)
        receipt_probes = 0
        event_probes = 0
        recovered_attempts = 0
        recovered_tasks: set[str] = set()
        recovered_receipts: dict[str, CanonicalTaskReceipt] = {}
        completed: set[str] = set()
        exhausted: set[str] = set()
        durable_blocked: set[str] = set()
        closed_non_success: set[str] = set()
        for task_id in plan.topological_task_ids():
            binding = index.task(task_id)
            task = tasks[task_id]
            failed = 0
            terminal_attempts = 0
            observed_attempt = False
            success_seen = False
            for candidate in binding.attempts:
                receipt_probes += 1
                event_probes += 1
                try:
                    receipt = receipt_store.read(index.run_id, task_id, candidate.attempt_id)
                    event = self.read_event(index, candidate.event_relative_path)
                    event_owner = index.event_owner(task_id) if isinstance(index, (RetainedE3RepairRecoveryIndex, DevelopmentOutputRepairRecoveryIndex)) else index
                except (ArtifactIdentityConflict, OSError, ValueError) as error:
                    raise RunRecoveryError('bounded task recovery probe failed') from error
                if receipt is not None:
                    if success_seen or candidate.ordinal != terminal_attempts + 1:
                        raise RunRecoveryError('successful receipt has a missing or later terminal predecessor')
                    self._validate_receipt_static(index, task, candidate, receipt)
                    expected_event = TaskRecoveryEvent.from_receipt(event_owner, receipt)
                    if event is None:
                        if not repair_missing_events:
                            raise RunRecoveryError('custody-only recovery requires the original exact success event')
                        self.append_event(index, expected_event, receipt=receipt)
                    elif event != expected_event:
                        raise RunRecoveryError('task receipt conflicts with its recovery event')
                    self._restore_attempt(repository, run_id=index.run_id, attempt_id=candidate.attempt_id, task_id=task_id, disposition=TaskAttemptDisposition.SUCCEEDED, reason_code=None, existing=existing)
                    recovered_attempts += 1
                    recovered_tasks.add(task_id)
                    recovered_receipts[receipt.receipt_id] = receipt
                    completed.add(task_id)
                    observed_attempt = True
                    success_seen = True
                    terminal_attempts += 1
                    continue
                if event is None:
                    continue
                if event.disposition not in {TaskRecoveryDisposition.FAILED, TaskRecoveryDisposition.BLOCKED}:
                    raise RunRecoveryError('receipt-free attempt has a nonterminal event')
                if success_seen or candidate.ordinal != terminal_attempts + 1:
                    raise RunRecoveryError('failed recovery event has a missing or successful predecessor')
                reason_code = event.reason_codes[0]
                disposition = TaskAttemptDisposition.BLOCKED if event.disposition is TaskRecoveryDisposition.BLOCKED else TaskAttemptDisposition.FAILED
                self._restore_attempt(repository, run_id=index.run_id, attempt_id=candidate.attempt_id, task_id=task_id, disposition=disposition, reason_code=reason_code, existing=existing)
                if disposition is TaskAttemptDisposition.FAILED:
                    failed += 1
                elif TaskBlockReason(reason_code).kind.value == 'DURABLE':
                    durable_blocked.add(task_id)
                recovered_attempts += 1
                recovered_tasks.add(task_id)
                observed_attempt = True
                terminal_attempts += 1
            if not success_seen and (task_id in durable_blocked or terminal_attempts >= binding.maximum_attempts):
                closed_non_success.add(task_id)
            event_probes += 1
            nonattempt, _ = (self.read_event(index, binding.nonattempt_event_relative_path), index)
            if nonattempt is not None and (not observed_attempt):
                reason = TaskBlockReason(nonattempt.reason_codes[0])
                if reason.kind.value != 'DURABLE' and (not (reason in (TaskBlockReason.DEPENDENCY_BLOCKED, TaskBlockReason.DEPENDENCY_FAILED) and any((dependency in closed_non_success for dependency in binding.dependency_task_ids)))):
                    raise RunRecoveryError('nonattempt recovery event lacks a closed unsuccessful dependency')
                prior_blocks = tuple((attempt for attempt in existing.values() if attempt.task_id == task_id and attempt.disposition is TaskAttemptDisposition.BLOCKED))
                if prior_blocks:
                    if any((attempt.reason_code != reason.value for attempt in prior_blocks)):
                        raise RunRecoveryError('operational block differs from external recovery')
                else:
                    repository.block_task(index.run_id, task_id, reason)
                    recovered_attempts += 1
                    recovered_tasks.add(task_id)
                durable_blocked.add(task_id)
                closed_non_success.add(task_id)
            if failed >= binding.maximum_attempts:
                exhausted.add(task_id)
        if len(completed) == len(index.tasks):
            status = OperationalStatus.SUCCEEDED
        elif exhausted:
            status = OperationalStatus.FAILED
        elif durable_blocked:
            status = OperationalStatus.BLOCKED
        else:
            status = OperationalStatus.PENDING
        repository.set_run_status(index.run_id, status)
        return RunRecoveryReport(candidate_count=candidate_count, receipt_probe_count=receipt_probes, event_probe_count=event_probes, recovered_attempt_count=recovered_attempts, recovered_task_ids=tuple(sorted(recovered_tasks)), recovered_receipt_ids=tuple(sorted(recovered_receipts)), recovered_receipts=tuple((recovered_receipts[receipt_id] for receipt_id in sorted(recovered_receipts))), terminal_status=None, completed_task_ids=(), failed_task_ids=(), blocked_task_ids=())


    def reconcile_failed_history(self, *, plan, index: RunRecoveryIndex, receipt_store: TaskReceiptStore, repository: OperationalRepository, resource_spec: ExecutionResourceEnvelopeSpec, jit_graph_signature_manifest: JitGraphSignatureManifest | None=None) -> RunRecoveryTerminalEvent:
        """Serialize receipt-only failed closure with the existing execution owner."""
        from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
        from empirical_lawhood.infrastructure import publication_metadata as publication_owner
        supports_closed_publication_access = getattr(publication_owner, 'supports_closed_publication_access', None)
        from empirical_lawhood.runtime.plans import ExecutionPlan
        from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
        if type(plan) is not ExecutionPlan or type(index) is not RunRecoveryIndex:
            raise TypeError('failed-history reconciliation requires exact current plan and index')
        if not callable(supports_closed_publication_access):
            raise RunRecoveryError('failed-history closure is unsupported by the selected SDK publication owner')
        if not supports_closed_publication_access(self.plane):
            raise RunRecoveryError('failed-history reconciliation requires unchanged stock custody hooks')
        if not isinstance(receipt_store, ExternalTaskReceiptStore) or receipt_store.plane is not self.plane:
            raise RunRecoveryError('failed-history receipt store must use its exact artifact plane')
        contacts = ExternalNativeEffectContactStore(plane=self.plane, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan), visibility_ceiling=VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for task in plan.tasks for row in task.outputs)), outcome_access=most_restrictive_outcome_access(*(row.outcome_access for task in plan.tasks for row in task.outputs)))
        try:
            with contacts.execution_lock(index.run_id):
                with self.plane.verification_scope() as plane:
                    scoped = copy(self)
                    scoped.plane = plane
                    scoped._failed_history_resource_journal = ExternalExecutionResourceEnvelopeStore(plane.root) if _has_stock_failed_history_resource_reads(scoped) else None
                    scoped_receipts = copy(receipt_store)
                    scoped_receipts.plane = plane
                    return scoped._reconcile_failed_history_locked(plan=plan, index=index, receipt_store=scoped_receipts, repository=repository, resource_spec=resource_spec, jit_graph_signature_manifest=jit_graph_signature_manifest)
        except BlockingIOError as error:
            raise RunRecoveryError('another execution owns failed-history reconciliation') from error

    def _reconcile_failed_history_locked(
        self,
        *,
        plan,
        index: RunRecoveryIndex,
        receipt_store: TaskReceiptStore,
        repository: OperationalRepository,
        resource_spec: ExecutionResourceEnvelopeSpec,
        jit_graph_signature_manifest: JitGraphSignatureManifest | None = None,
    ) -> RunRecoveryTerminalEvent:
        """Close a failed invocation from custody, without scheduling its pending work.

        The API authenticates existing authority, protected-read scope and live
        ownership first. All primary history is checked before reconstruction
        in the caller's private catalog. Only its actual retained attempts enter
        the existing FAILED terminal; an unlaunched reservation stays reserved
        and pending, without becoming an operational attempt.
        """
        from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
        from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
        from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
        from empirical_lawhood.infrastructure.native_parent_finalization import inspect_native_parent_return
        from empirical_lawhood.runtime.execution_envelope import (
            ExecutionResourceEnvelopeEventKind, ExecutionResourceEnvelopeState,
            RunExecutionResourceEnvelopeMachine,
        )
        from empirical_lawhood.runtime.native_effects import NativeEffectContact
        from empirical_lawhood.runtime.native_subwork import NativeSubworkState
        from empirical_lawhood.runtime.plans import ExecutionPlan

        if type(plan) is not ExecutionPlan or type(index) is not RunRecoveryIndex:
            raise TypeError("failed-history reconciliation requires exact current plan and index")
        index.validate_plan(plan)
        self._validate_index_limits(index)
        if self.read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
            raise RunRecoveryError("failed-history index differs from retained custody")
        # Keep the exact original projection through the complete read-only
        # preflight. An expired RUNNING success may be closed from its existing
        # accepted receipt only after all native/resource/publication checks.
        catalog_before = tuple(repository.attempts(index.run_id))
        terminal = self.read_terminal(index)
        if terminal is not None and terminal.operational_status != "FAILED":
            raise RunRecoveryError("failed-history closure cannot replace another terminal disposition")
        plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
        envelope = self.reconstruct_execution_resource_envelope(index=index,
            envelope_id=f"run-resource-envelope.{index.run_id}", spec=resource_spec,
            execution_plan=plan_pin, jit_graph_signature_manifest=jit_graph_signature_manifest)
        original_envelope = envelope
        resource_updates = []
        recovered_at_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

        def stage_resource_transition(transition, **arguments):
            nonlocal envelope
            updated = transition(envelope, occurred_at_utc=recovered_at_utc, **arguments)
            resource_updates.append((envelope, updated))
            envelope = updated

        def stage_receipt_completion(cell, receipt):
            """Use the scheduler's existing receipt-as-proof transitions only."""
            identity = ObjectIdentity.from_record(receipt.receipt_id, receipt)
            if cell.current_attempt_id != receipt.attempt_id:
                raise RunRecoveryError("failed history successful resource attempt differs from its receipt")
            state = ExecutionResourceEnvelopeState
            expected = {
                state.LAUNCHED: (None, None, None, None),
                state.RECEIPT_OBSERVED: (identity, None, None, None),
                state.RECOVERY_PUBLICATION: (identity, None, identity, identity),
                state.PUBLISHED: (identity, identity, None, None),
                state.TERMINAL: (identity, identity, None, None),
            }
            if (cell.state not in expected or
                    (cell.first_valid_receipt, cell.published_artifact,
                     cell.recovery_candidate_artifact, cell.recovery_proof) != expected[cell.state]):
                raise RunRecoveryError("failed history successful resource completion is inconsistent")
            machine = RunExecutionResourceEnvelopeMachine
            common = {"cell_id": cell.cell_id}
            prefix = f"resource-envelope-event.{receipt.attempt_id}."
            if cell.state is state.LAUNCHED:
                stage_resource_transition(machine.recover_artifact_before_receipt,
                    event_id=prefix + "artifact-before-receipt", attempt_id=receipt.attempt_id,
                    receipt=identity, artifact=identity, recovery_proof=identity, **common)
            elif cell.state is state.RECEIPT_OBSERVED:
                stage_resource_transition(machine.begin_recovery_publication,
                    event_id=prefix + "recovery-publication-start", artifact=identity,
                    recovery_proof=identity, **common)
            if envelope.cell(cell.cell_id).state is state.RECOVERY_PUBLICATION:
                stage_resource_transition(machine.finish_recovery_publication,
                    event_id=prefix + "publication", **common)
            if envelope.cell(cell.cell_id).state is state.PUBLISHED:
                stage_resource_transition(machine.terminal, event_id=prefix + "terminal", **common)

        tasks = {task.task_id: task for task in plan.tasks}
        events: dict[tuple[str, str], TaskRecoveryEvent] = {}
        receipts: dict[str, CanonicalTaskReceipt] = {}
        nonattempts: dict[str, TaskRecoveryEvent] = {}
        missing_receipt_events = []
        manifests: list[ArtifactManifest] = []
        absent_paths = []
        physical_snapshots = {}

        def retain_absence(relative):
            absent_paths.extend((relative, relative + ".manifest.json"))

        def require_absences(*, allow_created_events=False, allow_created_terminal=False):
            created = set()
            if allow_created_terminal:
                created.update((index.terminal_event_relative_path, index.terminal_event_relative_path + ".manifest.json"))
            if allow_created_events:
                for receipt in missing_receipt_events:
                    event = TaskRecoveryEvent.from_receipt(index, receipt)
                    relative = self._event_path(index, event)
                    created.update((relative, relative + ".manifest.json"))
            for relative in absent_paths:
                if relative not in created and self.plane.root.resolve(relative, for_write=False).exists():
                    raise RunRecoveryError("failed history absent custody appeared during reconciliation")

        if terminal is None:
            retain_absence(index.terminal_event_relative_path)
        resource_failures_by_attempt = {}
        for row in envelope.events:
            if row.kind is ExecutionResourceEnvelopeEventKind.OPERATIONAL_FAILURE:
                resource_failures_by_attempt.setdefault((row.cell_id, row.attempt_id), []).append(row)
        exhausted = False
        for binding in index.tasks:
            task = tasks[binding.task_id]
            consumed = []
            success_seen = False
            for candidate in binding.attempts:
                event = self.read_event(index, candidate.event_relative_path)
                receipt = receipt_store.read(index.run_id, task.task_id, candidate.attempt_id)
                if event is None:
                    retain_absence(candidate.event_relative_path)
                if receipt is None:
                    retain_absence(candidate.receipt_relative_path)
                if event is None and receipt is None:
                    continue
                if (success_seen or candidate.ordinal != len(consumed) + 1
                        or event is not None and event.attempt_ordinal != candidate.ordinal):
                    raise RunRecoveryError("failed history has an incomplete or noncontiguous candidate pair")
                if receipt is not None:
                    self._validate_receipt_static(index, task, candidate, receipt)
                    expected_event = TaskRecoveryEvent.from_receipt(index, receipt)
                    if event is not None and event != expected_event:
                        raise RunRecoveryError("failed history receipt conflicts with its existing success event")
                    if event is None:
                        missing_receipt_events.append(receipt)
                    # The existing reconcile owner publishes this exact event
                    # only after the entire history has passed preflight.
                    event = expected_event
                    manifests.append(self.plane.read_manifest(candidate.receipt_relative_path))
                    output_specs = {output.logical_artifact_id: output for output in task.outputs}
                    for logical, physical in zip(receipt.output_logical_artifacts, receipt.output_materializations, strict=True):
                        output = output_specs[logical.logical_artifact_id]
                        if ((logical.payload_schema, logical.profile, logical.media_type, logical.visibility_ceiling,
                                logical.outcome_access, physical.relative_path)
                                != (output.payload_schema, output.profile, output.media_type, output.visibility_ceiling,
                                    output.outcome_access, output.relative_path)):
                            raise RunRecoveryError("failed history changes a static output contract")
                        manifests.append(ArtifactManifest(logical, physical))
                    receipts[task.task_id] = receipt
                    success_seen = True
                elif (event.disposition not in {TaskRecoveryDisposition.FAILED, TaskRecoveryDisposition.BLOCKED}
                        or event.failure is None or event.failure.scientific_evidence):
                    raise RunRecoveryError("failed history lacks an actual typed operational failure")
                events[task.task_id, candidate.attempt_id] = event
                consumed.append(event)
            nonattempt = self.read_event(index, binding.nonattempt_event_relative_path)
            if nonattempt is None:
                retain_absence(binding.nonattempt_event_relative_path)
            if nonattempt is not None:
                if consumed or nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED:
                    raise RunRecoveryError("failed history has conflicting candidate and nonattempt custody")
                if TaskBlockReason(nonattempt.reason_codes[0]).kind.value != "DURABLE":
                    raise RunRecoveryError("failed history nonattempt is not a retained durable block")
                nonattempts[task.task_id] = nonattempt
            if (len(consumed) == binding.maximum_attempts and consumed
                    and consumed[-1].disposition is TaskRecoveryDisposition.FAILED):
                exhausted = True
            cell = envelope.cell(resource_spec.cell_for_task(task.task_id).cell_id)
            if not consumed and cell.state is ExecutionResourceEnvelopeState.RESERVED:
                first = binding.attempts[0].attempt_id
                if (nonattempt is not None or cell.attempt_ids != (first,)
                        or cell.current_attempt_id != first or cell.first_valid_receipt is not None
                        or cell.published_artifact is not None or cell.recovery_candidate_artifact is not None
                        or cell.recovery_proof is not None):
                    raise RunRecoveryError("failed history changes its unlaunched reservation")
                # Preserve this reservation/token cost exactly. No candidate
                # event, catalog attempt or new launch is inferred from it.
                continue
            if cell.attempt_ids != tuple(row.attempt_id for row in consumed):
                raise RunRecoveryError("failed history resource attempts differ from candidate custody")
            receipt = receipts.get(task.task_id)
            if receipt is not None:
                stage_receipt_completion(cell, receipt)
            elif consumed:
                failure = consumed[-1].failure
                resource_failures = resource_failures_by_attempt.get((cell.cell_id, consumed[-1].attempt_id), ())
                if (cell.state not in {ExecutionResourceEnvelopeState.RECEIPT_OBSERVED, ExecutionResourceEnvelopeState.RESOURCE_STOP}
                        or cell.first_valid_receipt is not None or cell.published_artifact is not None
                        or cell.recovery_candidate_artifact is not None or len(resource_failures) != 1
                        or resource_failures[0].reason_code != failure.failure_class.value
                        or resource_failures[0].scientific_terminal is not False):
                    raise RunRecoveryError("failed history has an outstanding or inconsistent resource attempt")
            elif cell.state not in {ExecutionResourceEnvelopeState.ISSUED,
                    ExecutionResourceEnvelopeState.PENDING_BRANCH, ExecutionResourceEnvelopeState.ZERO_CALL_SKIPPED}:
                raise RunRecoveryError("unused failed-history candidate has outstanding resource custody")
        if not exhausted:
            raise RunRecoveryError("failed-history closure requires a genuinely exhausted failed task")
        from empirical_lawhood.runtime.execution import VerifiedArtifactInput, dependency_artifact_inputs

        outputs = {task_id: tuple(VerifiedArtifactInput(logical, physical)
            for logical, physical in zip(receipt.output_logical_artifacts,
                receipt.output_materializations, strict=True)) for task_id, receipt in receipts.items()}
        for task_id, receipt in receipts.items():
            task = tasks[task_id]
            if any(dependency not in receipts for dependency in task.dependency_task_ids):
                raise RunRecoveryError("failed history successful task lacks an exact dependency receipt")
            required = dependency_artifact_inputs(task, outputs)
            if not {row.materialization.materialization_id for row in required}.issubset(
                    receipt.input_materialization_ids):
                raise RunRecoveryError("failed history receipt omits its selected dependency products")
        # This operation authenticates custody of already accepted products;
        # semantic providers and scientific re-adjudication are outside it.
        verified_batches = set()
        for manifest in manifests:
            original = self.plane.read_manifest(manifest.materialization.relative_path,
                maximum_bytes=self.plane.custody_limits.manifest_bytes)
            if (original.logical, original.materialization) != (manifest.logical, manifest.materialization):
                raise RunRecoveryError("failed history output differs from its exact original sidecar")
            batch = original.publication
            if batch not in verified_batches:
                actual = read_publication_metadata(self.plane, manifest)
                for member in actual.publication.members:
                    for relative in (member.relative_path, member.relative_path + ".manifest.json",
                            actual.publication.commit_marker_relative_path):
                        self.plane._track_verification_snapshot(
                            self.plane.root.resolve(relative, for_write=False), physical_snapshots)
                    sibling = decode_artifact_manifest(read_bounded_bytes(
                        self.plane.root.resolve(member.relative_path + ".manifest.json", for_write=False),
                        maximum_bytes=self.plane.custody_limits.manifest_bytes),
                        maximum_bytes=self.plane.custody_limits.manifest_bytes)
                    self.plane.verify(sibling.materialization)
                verified_batches.add(batch)
        consumed_tasks = {key[0] for key in events}
        native_subworks = {}
        native_roster_roots = {}
        native_contact_files = set()
        native_checks = []
        for task in plan.tasks:
            visibility = VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for row in task.outputs))
            access = most_restrictive_outcome_access(task.capability.requested_outcome_access,
                *(row.outcome_access for row in task.outputs))
            contacts = ExternalNativeEffectContactStore(plane=self.plane, execution_plan=plan_pin,
                visibility_ceiling=visibility, outcome_access=access)
            contact = contacts.read(index.run_id, task.task_id)
            native = resource_spec.cell_for_task(task.task_id).native_simulator_launch
            receipt = receipts.get(task.task_id)
            if contact is None:
                if native and task.task_id in consumed_tasks:
                    raise RunRecoveryError("consumed native history has no exact root contact")
                continue
            if not native or receipt is None or any(dependency not in receipts for dependency in task.dependency_task_ids):
                raise RunRecoveryError("failed history has native contact without ordinary completion")
            expected = NativeEffectContact(index.run_id, task.task_id, receipt.attempt_id, plan_pin,
                ObjectIdentity.from_record(task.task_id, task), plan.implementation_commit,
                receipt.input_materialization_ids,
                tuple(sorted(receipts[dependency].receipt_id for dependency in task.dependency_task_ids)))
            if contact != expected:
                raise RunRecoveryError("failed history native contact substitutes original attempt or inputs")
            native_contact_files.add(hashlib.sha256(task.task_id.encode()).hexdigest() + ".json")
            subwork = ExternalNativeSubworkStore(plane=self.plane, parent_contacts=contacts, parent_contact=contact)
            invocation = subwork.read_prepared_invocation(contact)
            native_observation = (inspect_native_parent_return(store=subwork, work=invocation.native_work)
                if invocation is not None and invocation.native_work is not None
                    and invocation.native_work.definitions else None)
            inspected = ({} if native_observation is None else
                {row.definition.identity: row for row in native_observation.inspections})
            roster_files = set()
            selected_inspections = []
            for roster in subwork.iter_rosters(contact):
                roster_files.add(subwork._roster_key(contact, roster.roster_id) + ".json")
                for definition in subwork.iter_roster_definitions(contact, roster.roster_id):
                    inspection = inspected.get(definition.identity)
                    if inspection is None:
                        inspection = subwork.inspect(definition)
                    selected_inspections.append(inspection)
                    native_checks.append((subwork, definition, inspection))
                    key = subwork._key(definition)
                    if key in native_subworks:
                        raise RunRecoveryError("failed history repeats a native subwork definition")
                    native_subworks[key] = definition
            # Whole-census uncertainty precedes a sibling's known return whose
            # products remain unpublished. Neither condition permits replay or
            # writes during this read-only failed-history admission.
            if any(row.has_uncertain_contact for row in selected_inspections):
                raise RunRecoveryError("failed history native subwork has a contacted child without a known return")
            if any(row.native_return_status is not None and row.state is not NativeSubworkState.COMPLETED
                    for row in selected_inspections):
                raise RunRecoveryError("failed history known native return has incomplete durable publication")
            if any(row.state not in {NativeSubworkState.NOT_ENTERED, NativeSubworkState.COMPLETED}
                    for row in selected_inspections):
                raise RunRecoveryError("failed history uncontacted native subwork has incomplete progress")
            native_roster_roots[hashlib.sha256(task.task_id.encode()).hexdigest()] = roster_files
        # The roster owner validates selected definitions and progress. Join
        # its bounded namespaces as well, so lost rosters cannot hide retained
        # definition/contact/completion or leaf-receipt custody.
        def children(relative):
            root = self.plane.root.resolve(relative, for_write=False)
            if not root.exists():
                return
            for path in root.iterdir():
                if not path.name.startswith("."):
                    yield self.plane.root.resolve(path.relative_to(self.plane.root.contract.canonical_path).as_posix(),
                        for_write=False)

        def require_native_namespaces():
            expected_contacts = native_contact_files | {name + ".manifest.json" for name in native_contact_files}
            for path in children(f"runs/{index.run_id}/native-contacts"):
                if path.name not in expected_contacts or not path.is_file():
                    raise RunRecoveryError("failed history has an orphaned native root contact")
            for directory in children(f"runs/{index.run_id}/native-subwork-rosters"):
                expected_files = native_roster_roots.get(directory.name)
                if expected_files is None or not directory.is_dir():
                    raise RunRecoveryError("failed history has orphaned native roster custody")
                expected = expected_files | {name + ".manifest.json" for name in expected_files}
                observed = set()
                for path in children(directory.relative_to(self.plane.root.contract.canonical_path).as_posix()):
                    if path.name not in expected:
                        raise RunRecoveryError("failed history native roster publication has orphaned custody")
                    observed.add(path.name)
                if observed != expected:
                    raise RunRecoveryError("failed history native roster publication is partial or orphaned")
            for directory in children(f"runs/{index.run_id}/native-subwork"):
                if directory.name not in native_subworks or not directory.is_dir():
                    raise RunRecoveryError("failed history has orphaned native subwork custody")
            for directory in children(f"runs/{index.run_id}/receipts"):
                if directory.name.startswith("native-subwork.") and directory.name.removeprefix("native-subwork.") not in native_subworks:
                    raise RunRecoveryError("failed history has an orphaned native subwork receipt")

        require_native_namespaces()
        terminal_only_blocks = {}
        if terminal is not None:
            candidate_summaries = set()
            nonattempt_summaries = set()
            candidate_ids = {row.attempt_id for binding in index.tasks for row in binding.attempts}
            for summary in terminal.attempts:
                key = summary.task_id, summary.attempt_id
                event = events.get(key)
                if event is not None:
                    if summary.ordinal != event.attempt_ordinal:
                        raise RunRecoveryError("failed-history terminal changes candidate ordinals")
                    candidate_summaries.add(key)
                else:
                    block = nonattempts.get(summary.task_id)
                    if block is None:
                        # Older terminals own retryable, unentered projection
                        # blocks themselves. Preserve these existing records;
                        # this operation never creates them for pending work.
                        if (summary.task_id not in tasks or summary.task_id in consumed_tasks
                                or summary.task_id in terminal_only_blocks or summary.attempt_id in candidate_ids
                                or summary.ordinal != 1 or summary.disposition is not RecoveryTerminalDisposition.BLOCKED
                                or TaskBlockReason(summary.reason_code).kind.value != "RETRYABLE"):
                            raise RunRecoveryError("failed-history terminal contains an unretained attempt")
                        terminal_only_blocks[summary.task_id] = summary
                    elif (summary.task_id in nonattempt_summaries or summary.ordinal != 1
                            or summary.disposition is not RecoveryTerminalDisposition.BLOCKED
                            or summary.reason_code != block.reason_codes[0]):
                        raise RunRecoveryError("failed-history terminal contains an unretained attempt")
                    else:
                        nonattempt_summaries.add(summary.task_id)
            if candidate_summaries != set(events) or nonattempt_summaries != set(nonattempts):
                raise RunRecoveryError("failed-history terminal omits retained attempts")
            self._reconcile_terminal(index=index, plan=plan, terminal=terminal, repository=None,
                receipt_store=receipt_store, existing={},
                candidate_count=sum(len(row.attempts) for row in index.tasks))
        # Reconcile must not discover additional projection-only history that
        # could be mistaken for an actual retained attempt in the new terminal.
        existing_nonattempts = set()
        catalog_blocks = {}
        expired_successes = {}

        def require_catalog_preflight():
            # The run lock excludes supported schedulers. Still refuse changed
            # projection/lease custody at every pre-effect boundary.
            current = tuple(repository.attempts(index.run_id))
            if current != catalog_before:
                if any(row.disposition is TaskAttemptDisposition.RUNNING for row in current):
                    raise RunRecoveryError("failed-history catalog acquired or changed a running attempt")
                raise RunRecoveryError("failed-history catalog changed during preflight")
            now_epoch = int(datetime.now(timezone.utc).timestamp())
            if any(row.lease_expires_epoch_seconds > now_epoch for row in expired_successes.values()):
                raise RunRecoveryError("failed-history successful custody still has a live lease")

        require_catalog_preflight()
        catalog_clock = int(datetime.now(timezone.utc).timestamp())
        if len({row.attempt_id for row in catalog_before}) != len(catalog_before):
            raise RunRecoveryError("failed-history catalog repeats an attempt identity")
        for attempt in catalog_before:
            if attempt.run_id != index.run_id or attempt.task_id not in tasks:
                raise RunRecoveryError("failed-history catalog changes the original run/task census")
            event = events.get((attempt.task_id, attempt.attempt_id))
            block = nonattempts.get(attempt.task_id)
            terminal_block = terminal_only_blocks.get(attempt.task_id)
            block_reason = (block.reason_codes[0] if block is not None
                else terminal_block.reason_code if terminal_block is not None and terminal_block.attempt_id == attempt.attempt_id else None)
            running = attempt.disposition is TaskAttemptDisposition.RUNNING
            if running:
                receipt = receipts.get(attempt.task_id)
                if (event is None or event.disposition is not TaskRecoveryDisposition.SUCCEEDED
                        or receipt is None or receipt.attempt_id != attempt.attempt_id
                        or attempt.reason_code is not None
                        or attempt.lease_id != "lease." + attempt.attempt_id
                        or type(attempt.lease_expires_epoch_seconds) is not int
                        or attempt.lease_expires_epoch_seconds <= 0
                        or attempt.lease_expires_epoch_seconds > catalog_clock):
                    raise RunRecoveryError("failed-history running attempt lacks exact expired successful custody")
                expired_successes[attempt.attempt_id] = attempt
            elif attempt.lease_id is not None or attempt.lease_expires_epoch_seconds is not None:
                raise RunRecoveryError("failed-history terminal catalog row retains a lease")
            if event is not None:
                reason = None if event.disposition is TaskRecoveryDisposition.SUCCEEDED else event.reason_codes[0]
                disposition = TaskAttemptDisposition.SUCCEEDED if running else attempt.disposition
                if (disposition.value, attempt.reason_code, attempt.ordinal) != (
                        event.disposition.value, reason, event.attempt_ordinal):
                    raise RunRecoveryError("failed-history catalog differs from its retained candidate")
            elif block_reason is not None:
                if (attempt.task_id in existing_nonattempts or attempt.ordinal != 1
                        or attempt.disposition is not TaskAttemptDisposition.BLOCKED or attempt.reason_code != block_reason):
                    raise RunRecoveryError("failed-history catalog contains an unretained attempt")
                existing_nonattempts.add(attempt.task_id)
            elif (attempt.task_id not in existing_nonattempts and attempt.task_id not in consumed_tasks
                    and attempt.task_id not in nonattempts and attempt.ordinal == 1
                    and attempt.disposition is TaskAttemptDisposition.BLOCKED
                    and attempt.attempt_id == f"{index.run_id}.{attempt.task_id}.block-001"
                    and attempt.reason_code == "dependency-blocked"):
                catalog_blocks[attempt.task_id] = attempt.reason_code
                existing_nonattempts.add(attempt.task_id)
            else:
                raise RunRecoveryError("failed-history catalog contains an unretained attempt")
        _require_catalog_dependency_causes(
            dependency_order=tuple(sorted(index.tasks, key=lambda row: row.topological_ordinal)),
            candidate_events=events, receipts=receipts, nonattempts=nonattempts,
            catalog_blocks=catalog_blocks)

        # Expected projection after the existing recovery owner restores exact
        # canonical primary events. Existing catalog-only blocks remain their
        # actual original rows; no new nonattempt publication is manufactured.
        expected_catalog = {row.attempt_id: row for row in catalog_before}
        for event in events.values():
            reason = None if event.disposition is TaskRecoveryDisposition.SUCCEEDED else event.reason_codes[0]
            expected_catalog[event.attempt_id] = OperationalAttempt(event.attempt_id, index.run_id,
                event.task_id, event.attempt_ordinal, TaskAttemptDisposition(event.disposition.value),
                reason, None, None)
        for task_id, block in nonattempts.items():
            if task_id not in existing_nonattempts:
                attempt_id = f"{index.run_id}.{task_id}.block-001"
                expected_catalog[attempt_id] = OperationalAttempt(attempt_id, index.run_id,
                    task_id, 1, TaskAttemptDisposition.BLOCKED, block.reason_codes[0], None, None)
        for summary in terminal_only_blocks.values():
            if summary.attempt_id not in expected_catalog:
                expected_catalog[summary.attempt_id] = OperationalAttempt(summary.attempt_id,
                    index.run_id, summary.task_id, summary.ordinal, TaskAttemptDisposition.BLOCKED,
                    summary.reason_code, None, None)

        def require_catalog_result():
            actual = tuple(repository.attempts(index.run_id))
            if (len({row.attempt_id for row in actual}) != len(actual)
                    or {row.attempt_id: row for row in actual} != expected_catalog):
                raise RunRecoveryError("failed-history reconstruction changes its authenticated catalog census")

        # Everything above is a read or an in-memory transition. Close every
        # positive and absent custody observation before the first append.
        for subwork, definition, inspection in native_checks:
            if subwork.inspect(definition) != inspection:
                raise RunRecoveryError("failed history native completion changed during preflight")
        require_native_namespaces()
        require_absences()
        self.plane.require_verification_snapshot()
        self.plane._require_verification_snapshot_paths(physical_snapshots,
            reason="failed history output changed during preflight")
        if self.reconstruct_execution_resource_envelope(index=index, envelope_id=original_envelope.envelope_id,
                spec=resource_spec, execution_plan=plan_pin,
                jit_graph_signature_manifest=jit_graph_signature_manifest) != original_envelope:
            raise RunRecoveryError("failed-history resource prefix changed before reconciliation")
        require_catalog_preflight()
        journal = getattr(self, "_failed_history_resource_journal", None)
        if journal is None:
            journal = ExternalExecutionResourceEnvelopeStore(self.plane.root)
        for expected, updated in resource_updates:
            require_catalog_preflight()
            journal.compare_and_append(expected=expected, updated=updated)
            require_absences()
        for receipt in missing_receipt_events:
            require_catalog_preflight()
            self.record_receipt(index, receipt)
        require_absences(allow_created_events=True)
        require_catalog_preflight()
        # A pre-existing terminal may itself own historical retryable blocks
        # without nonattempt events. Its original read path never appends
        # candidate events; all exact candidate successes were staged above.
        report = self.reconcile(index, plan, repository, receipt_store,
            repair_missing_events=bool(terminal_only_blocks))
        attempts = repository.attempts(index.run_id)
        if any(row.disposition is TaskAttemptDisposition.RUNNING for row in attempts):
            raise RunRecoveryError("failed-history reconstruction contains a running attempt")
        require_catalog_result()
        if {row.task_id: row for row in report.recovered_receipts} != receipts:
            raise RunRecoveryError("failed-history reconstruction changes its preflight receipt census")
        require_absences(allow_created_events=True)
        if self.reconstruct_execution_resource_envelope(index=index, envelope_id=envelope.envelope_id,
                spec=resource_spec, execution_plan=plan_pin, jit_graph_signature_manifest=jit_graph_signature_manifest) != envelope:
            raise RunRecoveryError("failed-history resource prefix changed during reconciliation")
        for subwork, definition, inspection in native_checks:
            if subwork.inspect(definition) != inspection:
                raise RunRecoveryError("failed history native completion changed during reconciliation")
        require_native_namespaces()
        self.plane.require_verification_snapshot()
        self.plane._require_verification_snapshot_paths(physical_snapshots,
            reason="failed history output changed during reconciliation")
        require_absences(allow_created_events=True)
        require_catalog_result()
        if terminal is None:
            self.record_terminal(index, status=OperationalStatus.FAILED, attempts=attempts,
                receipts=report.recovered_receipts)
            terminal = self.read_terminal(index)
        if terminal is None or terminal.operational_status != "FAILED":
            raise RunRecoveryError("failed-history terminal publication is incomplete")
        # A failed final guard preserves any already-committed custody but
        # cannot return it as a successful reconciliation.
        for subwork, definition, inspection in native_checks:
            if subwork.inspect(definition) != inspection:
                raise RunRecoveryError("failed history native completion changed during terminal publication")
        require_native_namespaces()
        require_absences(allow_created_events=True, allow_created_terminal=True)
        require_catalog_result()
        self.plane._require_verification_snapshot_paths(physical_snapshots,
            reason="failed history output changed during terminal publication")
        return terminal





    def _reconcile_terminal(self, *, index: ProtocolRunRecoveryIndex, plan: ProtocolExecutionPlan, terminal: ProtocolRunRecoveryTerminalEvent, repository: OperationalRepository | None, receipt_store: TaskReceiptStore, existing: dict[str, OperationalAttempt], candidate_count: int, require_complete_events: bool=False, _recovery_controls=None) -> RunRecoveryReport:
        if _recovery_controls is None and repository is None and _can_batch_recovery_controls(self, receipt_store, index):
            return _reconcile_recovery_control_batch(self, receipt_store, index, lambda controls: self._reconcile_terminal(index=index, plan=plan, terminal=terminal, repository=None, receipt_store=receipt_store, existing=existing, candidate_count=candidate_count, require_complete_events=require_complete_events, _recovery_controls=controls))
        if _recovery_controls is not None:
            _recovery_controls.require_open(self, receipt_store, index)
        summaries = {attempt.attempt_id: attempt for attempt in terminal.attempts}
        consumed: set[str] = set()
        recovered_receipts: dict[str, CanonicalTaskReceipt] = {}
        tasks = {task.task_id: task for task in plan.tasks}
        receipt_probes = 0
        event_probes = 0
        for binding in index.tasks:
            task = tasks[binding.task_id]
            for candidate in binding.attempts:
                receipt_probes += 1
                event_probes += 1
                try:
                    if _recovery_controls is None:
                        receipt = receipt_store.read(index.run_id, binding.task_id, candidate.attempt_id)
                        event = self.read_event(index, candidate.event_relative_path)
                        event_owner = index.event_owner(binding.task_id) if isinstance(index, (RetainedE3RepairRecoveryIndex, DevelopmentOutputRepairRecoveryIndex)) else index
                    else:
                        receipt = _recovery_controls.receipts[binding.task_id, candidate.attempt_id]
                        event = _recovery_controls.events[candidate.event_relative_path]
                        event_owner = index
                except (ArtifactIdentityConflict, OSError, ValueError) as error:
                    raise RunRecoveryError('terminal task recovery custody is invalid') from error
                summary = summaries.get(candidate.attempt_id)
                if summary is None:
                    if event is not None or receipt is not None:
                        raise RunRecoveryError('terminal recovery closure omits a persisted attempt')
                    continue
                consumed.add(candidate.attempt_id)
                if require_complete_events and event is None:
                    raise RunRecoveryError('custody-only terminal lacks an original candidate event')
                if summary.task_id != binding.task_id:
                    raise RunRecoveryError('terminal attempt differs from its bounded candidate')
                if summary.disposition is RecoveryTerminalDisposition.SUCCEEDED:
                    if receipt is None:
                        raise RunRecoveryError('terminal task receipt is missing')
                    self._validate_receipt_static(index, task, candidate, receipt)
                    expected_event = TaskRecoveryEvent.from_receipt(event_owner, receipt) if _recovery_controls is None else _recovery_controls.receipt_event(receipt)
                    if event != expected_event or summary.receipt_id != receipt.receipt_id or summary.receipt_sha256 != receipt.fingerprint():
                        raise RunRecoveryError('terminal task receipt or recovery event was substituted')
                    recovered_receipts[receipt.receipt_id] = receipt
                elif summary.disposition is RecoveryTerminalDisposition.FAILED:
                    if receipt is not None or event is None or event.disposition is not TaskRecoveryDisposition.FAILED or (event.reason_codes != (summary.reason_code,)):
                        raise RunRecoveryError('terminal failed attempt lacks exact external evidence')
                elif receipt is not None or (event is not None and (event.disposition is not TaskRecoveryDisposition.BLOCKED or event.reason_codes != (summary.reason_code,))):
                    raise RunRecoveryError('terminal blocked attempt has conflicting evidence')
            event_probes += 1
            try:
                if _recovery_controls is None:
                    nonattempt, _ = (self.read_event(index, binding.nonattempt_event_relative_path), index)
                else:
                    nonattempt = _recovery_controls.events[binding.nonattempt_event_relative_path]
            except (ArtifactIdentityConflict, OSError, ValueError) as error:
                raise RunRecoveryError('terminal nonattempt recovery custody is invalid') from error
            candidate_ids = {candidate.attempt_id for candidate in binding.attempts}
            if require_complete_events and nonattempt is None and any((summary.task_id == binding.task_id and summary.attempt_id not in candidate_ids for summary in terminal.attempts)):
                raise RunRecoveryError('custody-only terminal lacks its exact original nonattempt event')
            if nonattempt is not None:
                matching = tuple((attempt for attempt in terminal.attempts if attempt.task_id == binding.task_id and attempt.disposition is RecoveryTerminalDisposition.BLOCKED and (attempt.reason_code == nonattempt.reason_codes[0])))
                if not matching:
                    raise RunRecoveryError('terminal recovery closure omits its nonattempt event')
        candidate_ids = {candidate.attempt_id for binding in index.tasks for candidate in binding.attempts}
        if consumed != {attempt.attempt_id for attempt in terminal.attempts if attempt.attempt_id in candidate_ids}:
            raise RunRecoveryError('terminal recovery closure contains unknown attempts')
        for summary in terminal.attempts:
            if summary.task_id not in tasks:
                raise RunRecoveryError('terminal recovery closure names an unknown task')
            disposition = TaskAttemptDisposition(summary.disposition.value)
            if repository is not None:
                self._restore_attempt(repository, run_id=index.run_id, attempt_id=summary.attempt_id, task_id=summary.task_id, disposition=disposition, reason_code=summary.reason_code, existing=existing)
        if repository is not None:
            repository.set_run_status(index.run_id, OperationalStatus(terminal.operational_status))
        report = RunRecoveryReport(candidate_count=candidate_count, receipt_probe_count=receipt_probes, event_probe_count=event_probes, recovered_attempt_count=len(terminal.attempts), recovered_task_ids=tuple(sorted({*terminal.completed_task_ids, *terminal.failed_task_ids, *terminal.blocked_task_ids})), recovered_receipt_ids=tuple(sorted(recovered_receipts)), recovered_receipts=tuple((recovered_receipts[receipt_id] for receipt_id in sorted(recovered_receipts))), terminal_status=terminal.operational_status, completed_task_ids=terminal.completed_task_ids, failed_task_ids=terminal.failed_task_ids, blocked_task_ids=terminal.blocked_task_ids)
        if _recovery_controls is not None:
            _recovery_controls.require_open(self, receipt_store, index)
        return report


__all__ = [
    "ExternalRunRecoveryStore",
    "settled_recovery_tasks",
    "RunRecoveryError",
    "decode_run_recovery_index",
    "decode_run_recovery_terminal_event",
    "decode_task_recovery_event",
    "decode_execution_envelope_event",
    'decode_execution_resource_envelope_event',
    "reconstruct_execution_envelope_from_external_events",
    'reconstruct_execution_resource_envelope_from_external_events',
]


# Method identity chooses this owned optimization, never custody or authority.
_STOCK_FAILED_HISTORY_RECONSTRUCT = ExternalRunRecoveryStore.reconstruct_execution_resource_envelope
_STOCK_FAILED_HISTORY_JOURNAL = ExternalExecutionResourceEnvelopeStore
_STOCK_FAILED_HISTORY_JOURNAL_METHODS = tuple((name, getattr(ExternalExecutionResourceEnvelopeStore, name))
    for name in ("load", "current", "compare_and_append", "_read", "_current", "_head", "_stamps", "_locked"))


def _has_stock_failed_history_resource_reads(store):
    return (type(store) is ExternalRunRecoveryStore
        and "reconstruct_execution_resource_envelope" not in vars(store)
        and type(store).reconstruct_execution_resource_envelope is _STOCK_FAILED_HISTORY_RECONSTRUCT
        and ExternalExecutionResourceEnvelopeStore is _STOCK_FAILED_HISTORY_JOURNAL
        and all(getattr(ExternalExecutionResourceEnvelopeStore, name) is method
            for name, method in _STOCK_FAILED_HISTORY_JOURNAL_METHODS))


_STOCK_RECOVERY_READ_METHODS = tuple((name, getattr(ExternalRunRecoveryStore, name))
    for name in ("read_event", "_read_payload", "_read_payload_envelope", "_read_payload_body",
        "_decode_event_payload", "_decode_event_payload_at_identity", "_event_path"))


def _has_stock_recovery_reads(store):
    """Keep class and instance read customizations on their original route."""
    return (type(store) is ExternalRunRecoveryStore
        and set(vars(store)) == {"plane", "minimum_free_bytes", "_resource_read_journal"}
        and all(getattr(type(store), name) is original
            for name, original in _STOCK_RECOVERY_READ_METHODS))


def _can_batch_recovery_controls(recovery, receipts, index):
    """Select stock recovery metadata reads, retaining custom serial hooks."""
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane, _has_stock_manifest_reads
    from empirical_lawhood.infrastructure.task_receipts import _has_stock_task_receipt_reads

    plane = recovery.plane
    count = sum(2 * len(row.attempts) + 1 for row in index.tasks)
    return (not isinstance(index, (RetainedE3RepairRecoveryIndex, DevelopmentOutputRepairRecoveryIndex))
        and type(plane) is _ScopedArtifactPlane and plane._read_verification.active
        and _has_stock_manifest_reads(plane) and _has_stock_task_receipt_reads(receipts)
        and _has_stock_recovery_reads(recovery) and receipts.plane is plane
        and not plane.custody_limits.exceeds("publication_members", count))


_RECOVERY_CONTROL_SEAL = object()


class _RecoveryControlBatch:
    """Decoded controls borrowed only inside one plural verification callback."""

    def __init__(self, recovery, receipts, index, index_identity, values, events, seal):
        from types import MappingProxyType
        if seal is not _RECOVERY_CONTROL_SEAL:
            raise TypeError('recovery controls require their exact verification owner')
        self.recovery, self.receipt_store, self.index = (recovery, receipts, index)
        self.index_identity, self.receipts, self.events = (index_identity, MappingProxyType(values), MappingProxyType(events))
        self.active = True

    def require_open(self, recovery, receipts, index):
        if (not self.active or self.recovery is not recovery
                or self.receipt_store is not receipts or self.index is not index
                or not _can_batch_recovery_controls(recovery, receipts, index)):
            raise RunRecoveryError("recovery controls escaped their exact stock verification callback")

    def receipt_event(self, receipt):
        """Use the one exact index pin, preserving every ordinary event field."""
        self.require_open(self.recovery, self.receipt_store, self.index)
        index = self.index
        candidate = next(row for row in index.task(receipt.task_id).attempts
            if row.attempt_id == receipt.attempt_id)
        return TaskRecoveryEvent(event_id=f"recovery-event.{receipt.attempt_id}.succeeded",
            recovery_index=self.index_identity, run_id=index.run_id,
            task_id=receipt.task_id, attempt_id=receipt.attempt_id,
            attempt_ordinal=candidate.ordinal, disposition=TaskRecoveryDisposition.SUCCEEDED,
            receipt_id=receipt.receipt_id, receipt_relative_path=candidate.receipt_relative_path,
            receipt_sha256=receipt.fingerprint(), receipt_schema=receipt.SCHEMA,
            output_materialization_ids=tuple(sorted(row.materialization_id
                for row in receipt.output_materializations)), reason_codes=())


def _reconcile_recovery_control_batch(recovery, receipt_store, index, reconcile):
    """Authenticate the complete frozen control roster under one existing guard.

    Only decoded control records survive inside the callback. The report is
    released after the ordinary plural owner's full final snapshot validation.
    Absences are checked before and after consumption. Nothing is cached across
    invocations, and no scientific output body is opened by this pass.
    """
    receipt_keys = tuple((row.task_id, candidate.attempt_id)
        for row in index.tasks for candidate in row.attempts)
    event_paths = tuple(path for row in index.tasks
        for path in (*(candidate.event_relative_path for candidate in row.attempts),
            row.nonattempt_event_relative_path))
    relative_paths = tuple(receipt_store._relative_path(index.run_id, *key) for key in receipt_keys) + event_paths
    # A finite path scope keeps every ancestor and destination check, without
    # re-inspecting the root and shared ancestors for each absent control.
    from empirical_lawhood.infrastructure.artifacts import ExternalRootUnavailable
    try:
        with recovery.plane.root.read_paths(tuple(name for relative in relative_paths
                for name in (relative, relative + '.manifest.json'))) as paths:
            return _consume_recovery_control_paths(recovery, receipt_store, index, reconcile,
                receipt_keys, event_paths, paths)
    except ExternalRootUnavailable as error:
        raise RunRecoveryError('recovery control path changed during verification') from error


def _consume_recovery_control_paths(recovery, receipt_store, index, reconcile,
        receipt_keys, event_paths, paths):
    plane = recovery.plane
    index_identity = ObjectIdentity.from_record(index.recovery_index_id, index)
    receipt_envelopes = tuple((key, receipt_store._read_envelope(index.run_id, *key, _paths=paths))
        for key in receipt_keys)
    event_envelopes = tuple((path, recovery._read_payload_envelope(path,
        expected_schema=index.TASK_EVENT_SCHEMA,
        maximum_bytes=plane.custody_limits.recovery_event_bytes, _paths=paths)) for path in event_paths)
    absent = tuple(receipt_store._relative_path(index.run_id, *key)
        for key, value in receipt_envelopes if value is None) + tuple(
        path for path, value in event_envelopes if value is None)
    manifests = tuple(value[1] for _, value in (*receipt_envelopes, *event_envelopes)
        if value is not None)

    def require_absences():
        for relative in absent:
            if any(paths[name].exists()
                    for name in (relative, relative + ".manifest.json")):
                raise RunRecoveryError("recovery control appeared during verification")

    def consume(authenticated):
        if not _can_batch_recovery_controls(recovery, receipt_store, index):
            raise RunRecoveryError("recovery changed its stock verification policy")
        require_absences()
        values, events = {}, {}
        for key, selected in receipt_envelopes:
            if selected is None:
                values[key] = None
            else:
                path, manifest = selected
                if authenticated.get(manifest.materialization.relative_path) != manifest:
                    raise RunRecoveryError("receipt changed its actual publication")
                values[key] = receipt_store._read_body(index.run_id, *key, path, manifest)
        for relative, selected in event_envelopes:
            if selected is None:
                events[relative] = None
            else:
                path, manifest = selected
                if authenticated.get(manifest.materialization.relative_path) != manifest:
                    raise RunRecoveryError("recovery event changed its actual publication")
                events[relative] = recovery._decode_event_payload_at_identity(index, relative,
                    recovery._read_payload_body(path, manifest), index_identity)
        controls = _RecoveryControlBatch(recovery, receipt_store, index,
            index_identity, values, events, _RECOVERY_CONTROL_SEAL)
        try:
            result = reconcile(controls)
            require_absences()
            controls.require_open(recovery, receipt_store, index)
            return result
        finally:
            controls.active = False

    try:
        require_absences()
        result = (plane.verify_manifests_members(manifests, validate_members=consume)
            if manifests else consume({}))
        require_absences()
        return result
    except (ArtifactIdentityConflict, BoundedFileIOError, OSError, ValueError) as error:
        raise RunRecoveryError("terminal task recovery custody is invalid") from error
