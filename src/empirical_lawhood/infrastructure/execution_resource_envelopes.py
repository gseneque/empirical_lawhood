"""Guarded incremental state for deadline-free execution resource envelopes."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.file_locks import exclusive_file_lock
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    canonical_json_bytes,
    validate_relative_locator,
    validate_sha256,
    validate_stable_id,
)
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult, lineage_parent_sort_key
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeEvent, ExecutionResourceEnvelopeEventKind, ExecutionResourceEnvelopeSpec, ExecutionResourceEnvelopeState, JitGraphSignatureManifest, reconstruct_execution_resource_envelope, replay_execution_resource_event, RunExecutionResourceEnvelope
from empirical_lawhood.runtime.execution_envelope import _IndexedResourceEnvelope, _ResourceEnvelopeDelta
from empirical_lawhood.runtime.plans import ExecutionPlan

from empirical_lawhood.runtime.recovery import RESOURCE_ENVELOPE_JOURNAL_ROOT

MAX_EXECUTION_RESOURCE_ENVELOPE_STATE_BYTES: Final[int] = 256 * 1024 * 1024
DEFAULT_EXECUTION_RESOURCE_ENVELOPE_STATE_ROOT: Final[str] = RESOURCE_ENVELOPE_JOURNAL_ROOT


def _materialize(envelope):
    return envelope.materialize() if isinstance(envelope, _IndexedResourceEnvelope) else envelope


def execution_launch_relative_path(*, run_id: str, task_id: str, attempt_id: str) -> str:
    """Exact lookup of one retained task launch, without a journal scan."""
    for value in (run_id, task_id, attempt_id):
        validate_stable_id(value)
    return f"runs/{run_id}/execution-facts/{task_id}/{attempt_id}/launch.json"


def _launch_parents(execution_plan: ObjectIdentity, spec: ExecutionResourceEnvelopeSpec):
    if (execution_plan.object_schema != ExecutionPlan.SCHEMA
            or execution_plan.object_version != ExecutionPlan.VERSION):
        raise PermissionError("execution launch requires the current execution-plan contract")
    return tuple(sorted((ArtifactLineageParent(identity, VisibilityCeiling.PROSPECTIVE,
        OutcomeAccess.OUTCOME_BLIND) for identity in (
            execution_plan, ObjectIdentity.from_record(spec.envelope_spec_id, spec))), key=lineage_parent_sort_key))


def _require_launch_event(event, *, spec, task_id, attempt_id):
    if type(event) is not ExecutionResourceEnvelopeEvent or type(spec) is not ExecutionResourceEnvelopeSpec:
        raise PermissionError("execution launch requires exact current event/resource contracts")
    try:
        cell = spec.cell(event.cell_id) if event.cell_id is not None else None
    except KeyError:
        cell = None
    if (cell is None or cell.task_id != task_id or event.event_id != f"resource-envelope-event.{attempt_id}.launch"
            or event.kind is not ExecutionResourceEnvelopeEventKind.LAUNCH
            or event.attempt_id != attempt_id or event.from_state is not ExecutionResourceEnvelopeState.RESERVED
            or event.to_state is not ExecutionResourceEnvelopeState.LAUNCHED or event.affected_cell_ids
            or any(getattr(event, name) is not None for name in ("reason_code", "receipt", "artifact",
                "recovery_proof", "heartbeat", "roster_decision", "valid_receipt", "scientific_terminal"))):
        raise PermissionError("execution launch changes its exact task/attempt transition")
    projection = event.jit_projection
    if ((projection is None) != (cell.jit_cell_id is None)
            or projection is not None and (projection.cell_id != cell.jit_cell_id
                or projection.signature_sha256 != cell.jit_signature_sha256)):
        raise PermissionError("execution launch changes its frozen JIT resource binding")


def read_execution_launch_event(*, artifact_plane: ExternalArtifactPlane, execution_plan: ExecutionPlan,
        resource_spec: ExecutionResourceEnvelopeSpec, run_id: str, task_id: str,
        attempt_id: str) -> ExecutionResourceEnvelopeEvent:
    """Authenticate one immutable derivative of the actual primary LAUNCH event.

    The existing journal remains the operational history. Its writer publishes
    these exact event bytes after committing the journal head. Reading this
    publication requires neither a current execution grant nor a journal replay.
    No timestamp is inferred from issue, preparation, receipt or file metadata.
    LAUNCH is the task dispatch boundary, before worker BEGIN/native contact.
    """
    if (not isinstance(artifact_plane, ExternalArtifactPlane) or type(execution_plan) is not ExecutionPlan
            or type(resource_spec) is not ExecutionResourceEnvelopeSpec
            or execution_plan.source_plan.object_id != run_id
            or execution_plan.execution_plan_id != f"execution.{run_id}"
            or execution_plan.execution_resource_envelope_spec != ObjectIdentity.from_record(resource_spec.envelope_spec_id, resource_spec)
            or resource_spec.issued_study_extensions != execution_plan.issued_extension_set):
        raise PermissionError("execution launch substitutes its current run/plan/resource contract")
    try:
        execution_plan.task(task_id)
    except KeyError as error:
        raise PermissionError("execution launch substitutes its current run/plan/resource contract") from error
    relative = execution_launch_relative_path(run_id=run_id, task_id=task_id, attempt_id=attempt_id)
    manifest = artifact_plane.read_manifest(relative)
    logical, physical, publication = manifest.logical, manifest.materialization, manifest.publication
    parents = _launch_parents(ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan), resource_spec)
    if (publication is None or len(publication.members) != 1
            or logical.logical_artifact_id != f"execution-launch.{attempt_id}"
            or logical.payload_schema != ExecutionResourceEnvelopeEvent.SCHEMA
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
            or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND or logical.lineage_parents != parents
            or physical.relative_path != relative or physical.storage_root_id != artifact_plane.root.contract.storage_root_id
            or physical.compression != "none" or physical.partition_selector is not None
            or publication.publication_scope.publication_scope_id != f"execution-launch.{attempt_id}"
            or publication.publication_scope.relative_root != relative.rsplit("/", 1)[0]
            or publication.publication_scope.storage_root_id != physical.storage_root_id
            or any(artifact_plane.custody_limits.exceeds(name, physical.size_bytes)
                for name in ("control_record_bytes", "in_memory_payload_bytes"))):
        raise PermissionError("execution launch differs from its exact immutable publication")
    artifact_plane.verify_manifest(manifest)
    raw = read_bounded_bytes(artifact_plane.root.resolve(relative, for_write=False), maximum_bytes=physical.size_bytes)
    event = decode_canonical_bytes(raw, ExecutionResourceEnvelopeEvent, maximum_bytes=physical.size_bytes)
    if (event.canonical_bytes() != raw or len(raw) != physical.size_bytes
            or event.fingerprint() != logical.content_sha256
            or hashlib.sha256(raw).hexdigest() != physical.physical_sha256):
        raise PermissionError("execution launch changes its committed event bytes")
    _require_launch_event(event, spec=resource_spec, task_id=task_id, attempt_id=attempt_id)
    return event


@dataclass(frozen=True, slots=True)
class _JournalOrigin(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/infrastructure/resource-envelope-journal-origin'
    envelope: RunExecutionResourceEnvelope
    jit_manifest: JitGraphSignatureManifest | None

    def __post_init__(self) -> None:
        initial = reconstruct_execution_resource_envelope(
            envelope_id=self.envelope.envelope_id,
            spec=self.envelope.spec,
            execution_plan=self.envelope.execution_plan,
            events=(),
            jit_graph_signature_manifest=self.jit_manifest,
        )
        if self.envelope != initial:
            raise ValueError("resource-envelope journal must start at the issued initial state")


@dataclass(frozen=True, slots=True)
class _JournalCheckpoint(_JournalOrigin):
    """An additive origin whose entire retained prefix is replay-verified."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/infrastructure/resource-envelope-journal-checkpoint'

    def __post_init__(self) -> None:
        replayed = reconstruct_execution_resource_envelope(
            envelope_id=self.envelope.envelope_id,
            spec=self.envelope.spec,
            execution_plan=self.envelope.execution_plan,
            events=self.envelope.events,
            jit_graph_signature_manifest=self.jit_manifest,
        )
        if replayed != self.envelope:
            raise ValueError("resource-envelope checkpoint differs from its complete event replay")


@dataclass(frozen=True, slots=True)
class _JournalHead(CanonicalRecord):
    """Durable commit pointer for the one authoritative operational event log."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/infrastructure/resource-envelope-journal-head'
    base_sha256: str
    journal_sha256: str
    journal_bytes: int
    event_count: int
    materialized_bytes: int

    def __post_init__(self) -> None:
        for name in ("base_sha256", "journal_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        if min(self.journal_bytes, self.event_count, self.materialized_bytes) < 0:
            raise ValueError("resource-envelope journal head has invalid bounds")


@dataclass(frozen=True, slots=True)
class _JournalPaths:
    origin: Path
    journal: Path
    head: Path


class ExternalExecutionResourceEnvelopeStore:
    """One fsynced event append followed by an atomic, content-bound head.

    Initial load and explicit inspection authenticate and replay all committed
    bytes. An active operation retains that verified prefix and extends its hash
    with bytes it has itself fsynced. A head or file-identity change invalidates
    the prefix and forces full authentication. Filesystem metadata alone never
    establishes an authenticated prefix. Uncommitted tails are discarded on retry.
    """

    def __init__(
        self,
        root: GuardedExternalRoot,
        *,
        artifact_plane: ExternalArtifactPlane | None = None,
        state_root_relative_path: str = DEFAULT_EXECUTION_RESOURCE_ENVELOPE_STATE_ROOT,
        maximum_state_bytes: int = MAX_EXECUTION_RESOURCE_ENVELOPE_STATE_BYTES,
    ) -> None:
        validate_relative_locator(state_root_relative_path)
        if not 0 < maximum_state_bytes <= MAX_EXECUTION_RESOURCE_ENVELOPE_STATE_BYTES:
            raise ValueError("resource-envelope state byte limit is invalid")
        if artifact_plane is not None and artifact_plane.root is not root:
            raise ValueError("resource-envelope publication must use its exact guarded root")
        self.root = root
        self.artifact_plane = artifact_plane
        self.state_root_relative_path = state_root_relative_path
        self.maximum_state_bytes = maximum_state_bytes
        self.maximum_journal_bytes = maximum_state_bytes
        self._cached: (
            tuple[
                _JournalHead,
                RunExecutionResourceEnvelope | _IndexedResourceEnvelope,
                _JournalOrigin,
                tuple[tuple[int, ...], ...],
            ]
            | None
        ) = None
        self._journal_hasher = hashlib.sha256()
        self._cache_lock = threading.RLock()

    @staticmethod
    def _token(envelope_id: str) -> str:
        validate_stable_id(envelope_id, field_name="envelope_id")
        return hashlib.sha256(envelope_id.encode("utf-8")).hexdigest()

    def _relative_path(self, envelope_id: str, suffix: str) -> str:
        return f"{self.state_root_relative_path}/{self._token(envelope_id)}.{suffix}"

    def _path(self, envelope_id: str, suffix: str) -> Path:
        return self.root.resolve(self._relative_path(envelope_id, suffix), for_write=True)

    @contextmanager
    def _locked(self, envelope_id: str) -> Iterator[_JournalPaths]:
        state_path = self._path(envelope_id, "json")
        if not state_path.parent.exists():
            state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            state_path = self._path(envelope_id, "json")
        lock_path = self._path(envelope_id, "lock")
        # The cached prefix/hash belongs to one envelope at a time. Serialize
        # this instance as well as each external log so another run cannot
        # replace its cached origin between validation and append.
        with self._cache_lock, exclusive_file_lock(lock_path):
            paths = _JournalPaths(
                state_path, self._path(envelope_id, "journal"), self._path(envelope_id, "head")
            )
            try:
                # Resolve once per locked operation, never across operations.
                # Reads retain no-follow/type/identity checks; each writer below
                # also revalidates its path immediately before mutation.
                yield paths
            finally:
                # Detect mount/space loss and ancestor substitution even when
                # the final reads only used the transaction's resolved paths.
                self.root.resolve(self.state_root_relative_path, for_write=True)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _write_all(descriptor: int, payload: bytes) -> None:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("resource-envelope write made no progress")
            view = view[written:]

    def _write_atomic(self, path: Path, record: CanonicalRecord) -> None:
        payload = record.canonical_bytes()
        if len(payload) > self.maximum_state_bytes:
            raise ValueError("resource-envelope state exceeds its byte limit")
        token = hashlib.sha256(
            f"{os.getpid()}\0{threading.get_ident()}\0{record.fingerprint()}".encode()
        ).hexdigest()[:24]
        temporary = path.with_name(f".{path.name}.{token}.partial")
        descriptor: int | None = None
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                stat.S_IRUSR | stat.S_IWUSR,
            )
            self._write_all(descriptor, payload)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _stamp(path: Path) -> tuple[int, ...]:
        try:
            value = path.stat(follow_symlinks=False)
        except FileNotFoundError:
            return ()
        if not stat.S_ISREG(value.st_mode):
            raise ValueError("resource-envelope file is not regular")
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

    def _stamps(self, paths: _JournalPaths) -> tuple[tuple[int, ...], ...]:
        return self._stamp(paths.origin), self._stamp(paths.journal)

    def _head(self, paths: _JournalPaths) -> _JournalHead:
        try:
            head = decode_canonical_bytes(
                read_bounded_bytes(paths.head, maximum_bytes=4096),
                _JournalHead,
                maximum_bytes=4096,
            )
        except FileNotFoundError as error:
            raise ValueError("resource-envelope journal commit pointer is missing") from error
        if (
            head.journal_bytes > self.maximum_journal_bytes
            or head.materialized_bytes > self.maximum_state_bytes
        ):
            raise ValueError("resource-envelope journal bound differs")
        return head

    def _read(
        self, paths: _JournalPaths, envelope_id: str
    ) -> tuple[RunExecutionResourceEnvelope, str, bytes]:
        before = self._stamps(paths)
        base = read_bounded_bytes(paths.origin, maximum_bytes=self.maximum_state_bytes)
        base_sha = hashlib.sha256(base).hexdigest()
        head = self._head(paths)
        if head.base_sha256 != base_sha:
            raise ValueError("resource-envelope journal base differs")
        journal = b""
        if head.journal_bytes:
            journal = read_bounded_bytes(paths.journal, maximum_bytes=self.maximum_journal_bytes)[
                : head.journal_bytes
            ]
        if len(journal) != head.journal_bytes:
            raise ValueError("resource-envelope committed journal is truncated")
        hasher = hashlib.sha256(journal)
        if hasher.hexdigest() != head.journal_sha256:
            raise ValueError("resource-envelope journal digest differs")
        cached = self._cached
        if cached is not None and cached[0] == head and cached[1].envelope_id == envelope_id:
            # Both full byte digests above were freshly checked. Reuse the
            # deterministic replay of these exact bytes, never a stat-only
            # observation or an authority verdict. Keep the final change guard.
            if before != self._stamps(paths) or self._head(paths) != head:
                raise ValueError("resource-envelope journal changed during authentication")
            self._journal_hasher = hasher
            self._cached = (head, cached[1], cached[2], before)
            return _materialize(cached[1]), base_sha, journal
        origin = decode_canonical_bytes(
            base,
            _JournalCheckpoint
            if json.loads(base).get("schema") == _JournalCheckpoint.SCHEMA
            else _JournalOrigin,
            maximum_bytes=self.maximum_state_bytes,
        )
        envelope = origin.envelope
        journal_events = []
        for line in journal.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise ValueError("resource-envelope journal event is incomplete")
            event = decode_canonical_bytes(
                line, ExecutionResourceEnvelopeEvent, maximum_bytes=self.maximum_state_bytes
            )
            if event.canonical_bytes() != line:
                raise ValueError("resource-envelope journal event is noncanonical")
            journal_events.append(event)
        if len(journal_events) > 64:
            envelope = reconstruct_execution_resource_envelope(
                envelope_id=envelope.envelope_id, spec=envelope.spec,
                execution_plan=envelope.execution_plan,
                events=(*envelope.events, *journal_events),
                jit_graph_signature_manifest=origin.jit_manifest,
            )
        else:
            for event in journal_events:
                envelope = replay_execution_resource_event(
                    envelope, event, jit_graph_signature_manifest=origin.jit_manifest
                )
        if envelope.envelope_id != envelope_id or len(envelope.events) != head.event_count:
            raise ValueError("resource-envelope committed state identity differs")
        if envelope.canonical_size_bytes() != head.materialized_bytes:
            raise ValueError("resource-envelope materialized byte bound differs")
        if before != self._stamps(paths) or self._head(paths) != head:
            raise ValueError("resource-envelope journal changed during authentication")
        self._journal_hasher = hasher
        self._cached = (head, envelope, origin, before)
        return envelope, base_sha, journal

    def _current(self, paths: _JournalPaths, envelope_id: str) -> RunExecutionResourceEnvelope:
        cached = self._cached
        if cached is not None and cached[1].envelope_id == envelope_id:
            if self._head(paths) == cached[0] and self._stamps(paths) == cached[3]:
                return cached[1]
        return self._read(paths, envelope_id)[0]

    def create(
        self,
        envelope: RunExecutionResourceEnvelope,
        *,
        jit_graph_signature_manifest: JitGraphSignatureManifest | None = None,
    ) -> None:
        origin = (_JournalCheckpoint if envelope.events else _JournalOrigin)(
            envelope=envelope, jit_manifest=jit_graph_signature_manifest
        )
        if origin.canonical_size_bytes() > self.maximum_state_bytes:
            raise ValueError("resource-envelope origin exceeds its byte limit")
        head = _JournalHead(
            base_sha256=origin.fingerprint(),
            journal_sha256=hashlib.sha256(b"").hexdigest(),
            journal_bytes=0,
            event_count=len(envelope.events),
            materialized_bytes=envelope.canonical_size_bytes(),
        )
        with self._locked(envelope.envelope_id) as paths:
            if paths.origin.exists():
                current, _, _ = self._read(paths, envelope.envelope_id)
                if current == envelope and self._cached is not None and self._cached[2] == origin:
                    return
                raise ValueError("resource envelope already exists with different state")
            if paths.journal.exists():
                raise ValueError("resource-envelope checkpoint is missing for a committed journal")
            head_path = paths.head
            if head_path.exists():
                if self._head(paths) != head:
                    raise ValueError("resource-envelope initialization commit differs")
            else:
                # Commit the exact empty origin identity first. A crash before
                # origin publication can then finish that same initialization;
                # a missing head never masquerades as an unspent existing run.
                self._write_atomic(self._path(envelope.envelope_id, "head"), head)
            self._write_atomic(self._path(envelope.envelope_id, "json"), origin)
            self._journal_hasher = hashlib.sha256()
            self._cached = (head, envelope, origin, self._stamps(paths))

    def load(self, envelope_id: str) -> RunExecutionResourceEnvelope:
        """Authenticate the complete external prefix for explicit inspection."""
        with self._locked(envelope_id) as paths:
            if not paths.origin.is_file():
                raise KeyError(envelope_id)
            return self._read(paths, envelope_id)[0]

    def current(self, envelope_id: str) -> RunExecutionResourceEnvelope:
        """Read within the active operation, extending only a verified prefix."""
        with self._locked(envelope_id) as paths:
            if not paths.origin.is_file():
                raise KeyError(envelope_id)
            return _materialize(self._current(paths, envelope_id))

    def _operational_current(self, envelope_id):
        """Private mutable projection; only the scheduler's locked owner uses it."""
        with self._locked(envelope_id) as paths:
            current = self._current(paths, envelope_id)
            if not isinstance(current, _IndexedResourceEnvelope):
                current = _IndexedResourceEnvelope(current)
                head, _, origin, stamps = self._cached
                self._cached = (head, current, origin, stamps)
            return current

    def _supports_incremental(self):
        # Custom persistence/read hooks retain their existing full-record path.
        return type(self) is ExternalExecutionResourceEnvelopeStore and all(
            getattr(getattr(self, name), '__func__', None) is method
            for name, method in _INCREMENTAL_STORE_METHODS.items()) and not any(
                name in vars(self) for name in _INCREMENTAL_STORE_METHODS)

    def _publish_launch_event(self, envelope, event) -> ArtifactWriteResult:
        """Copy the primary event verbatim, only after its durable commit."""
        if self.artifact_plane is None:
            raise PermissionError("execution launch publication requires its guarded artifact plane")
        retained = ((envelope._event_index.get(event.event_id),) if isinstance(envelope, _IndexedResourceEnvelope)
            else tuple(value for value in envelope.events if value.event_id == event.event_id))
        if retained != (event,):
            raise PermissionError("execution launch publication differs from its committed primary event")
        plan = envelope.execution_plan
        run_id = plan.object_id.removeprefix("execution.")
        if (plan.object_id != f"execution.{run_id}"
                or envelope.envelope_id != f"run-resource-envelope.{run_id}"):
            raise PermissionError("execution launch requires the current run/envelope naming contract")
        try:
            cell = envelope.spec.cell(event.cell_id) if event.cell_id is not None else None
        except KeyError:
            cell = None
        if cell is None or event.attempt_id is None:
            raise PermissionError("execution launch lacks its exact task/attempt binding")
        task_id = cell.task_id
        _require_launch_event(event, spec=envelope.spec, task_id=task_id, attempt_id=event.attempt_id)
        relative = execution_launch_relative_path(run_id=run_id, task_id=task_id, attempt_id=event.attempt_id)
        parents = _launch_parents(plan, envelope.spec)
        return self.artifact_plane.write(ArtifactWriteRequest(
            logical_artifact_id=f"execution-launch.{event.attempt_id}", relative_path=relative,
            payload_schema=event.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON,
            media_type="application/json", publication_scope_id=f"execution-launch.{event.attempt_id}",
            publication_scope_relative_root=relative.rsplit("/", 1)[0], payload=event.canonical_bytes(),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
            outcome_access=OutcomeAccess.OUTCOME_BLIND, lineage_parents=parents))

    def ensure_launch_publication(self, *, envelope_id: str, task_id: str,
            attempt_id: str) -> ArtifactWriteResult:
        """Resume only derivative publication of one already committed launch.

        This does not reserve or launch an attempt, alter event time, or infer
        whether any native effect occurred after the original launch boundary.
        """
        with self._locked(envelope_id) as paths:
            envelope = self._current(paths, envelope_id)
            matches = tuple(event for event in envelope.events
                if event.kind is ExecutionResourceEnvelopeEventKind.LAUNCH and event.attempt_id == attempt_id)
            if len(matches) != 1:
                raise PermissionError("execution launch requires one exact committed primary event")
            event = matches[0]
            _require_launch_event(event, spec=envelope.spec, task_id=task_id, attempt_id=attempt_id)
            return self._publish_launch_event(envelope, event)

    @staticmethod
    def _state_byte_delta(
        current: RunExecutionResourceEnvelope, updated: RunExecutionResourceEnvelope
    ) -> int:
        # Cell/token rosters are fixed. Only changed records contribute bytes;
        # historical events and unchanged siblings are never serialized.
        delta = sum(
            new.canonical_size_bytes() - old.canonical_size_bytes()
            for old, new in (
                *zip(current.cells, updated.cells, strict=True),
                *zip(current.child_token_states, updated.child_token_states, strict=True),
            )
            if old != new
        )
        if current.roster_decisions != updated.roster_decisions:
            delta += len(canonical_json_bytes(updated.roster_decisions)) - len(
                canonical_json_bytes(current.roster_decisions)
            )
        return delta

    def compare_and_append(
        self, *, expected: RunExecutionResourceEnvelope, updated: RunExecutionResourceEnvelope
    ) -> None:
        with self._locked(updated.envelope_id) as paths:
            current = _materialize(self._current(paths, updated.envelope_id))
            if len(current.events) != len(expected.events) or current != expected:
                raise ValueError("resource-envelope compare-and-append conflict")
            if (
                len(updated.events) != len(current.events) + 1
                or updated.events[:-1] != current.events
            ):
                raise ValueError("resource-envelope update is not one event append")
            assert self._cached is not None
            _, _, origin, _ = self._cached
            event = updated.events[-1]
            replayed = replay_execution_resource_event(
                current, event, jit_graph_signature_manifest=origin.jit_manifest
            )
            if replayed != updated:
                raise ValueError("resource-envelope update differs from its replayed event")
            committed, stamps = self._append_event(paths, current, event, self._state_byte_delta(current, updated))
            self._cached = (committed, updated, origin, stamps)
            if self.artifact_plane is not None and event.kind is ExecutionResourceEnvelopeEventKind.LAUNCH:
                self._publish_launch_event(updated, event)

    def _compare_and_append_transition(self, *, expected, updated):
        if type(expected) is not _IndexedResourceEnvelope or type(updated) is not _ResourceEnvelopeDelta:
            raise TypeError('resource-envelope operational append requires its indexed projection')
        with self._locked(expected.envelope_id) as paths:
            current = self._current(paths, expected.envelope_id)
            if (current is not expected or updated.owner is not current
                    or updated.event.sequence_number != len(current.events) + 1):
                raise ValueError('resource-envelope compare-and-append conflict')
            _, _, origin, _ = self._cached
            # Reapply the original transition rules to this one delta. Never
            # trust a caller's proposed cells or substitute an aggregate check.
            replayed = replay_execution_resource_event(current, updated.event,
                jit_graph_signature_manifest=origin.jit_manifest)
            if replayed != updated:
                raise ValueError('resource-envelope update differs from its replayed event')
            byte_delta = sum(row.canonical_size_bytes() - current.cell(row.cell_id).canonical_size_bytes()
                for row in updated.cells)
            byte_delta += sum(row.canonical_size_bytes() - current._tokens[row.child_id].canonical_size_bytes()
                for row in updated.child_token_states)
            if updated.roster_decisions is not None:
                byte_delta += len(canonical_json_bytes(updated.roster_decisions)) - len(canonical_json_bytes(current.roster_decisions))
            committed, stamps = self._append_event(paths, current, updated.event, byte_delta)
            current.commit(updated)
            self._cached = (committed, current, origin, stamps)
            if self.artifact_plane is not None and updated.event.kind is ExecutionResourceEnvelopeEventKind.LAUNCH:
                self._publish_launch_event(current, updated.event)

    def _append_event(self, paths, current, event, state_byte_delta):
        head, _, _, stamps = self._cached
        payload = event.canonical_bytes()
        materialized_bytes = (
            head.materialized_bytes
            + len(payload)
            - 1
            + bool(current.events)
            + state_byte_delta
        )
        delta = payload
        if (
            materialized_bytes > self.maximum_state_bytes
            or head.journal_bytes + len(delta) > self.maximum_journal_bytes
        ):
            raise ValueError("resource-envelope journal or state exceeds its byte limit")
        hasher = self._journal_hasher.copy()
        hasher.update(delta)
        journal_path = self._path(current.envelope_id, "journal")
        descriptor = os.open(
            journal_path,
            os.O_RDWR
            | os.O_CREAT
            | (os.O_EXCL if not stamps[1] else 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            stat.S_IRUSR | stat.S_IWUSR,
        )
        try:
            value = os.fstat(descriptor)
            if not stat.S_ISREG(value.st_mode) or (
                stamps[1]
                and (
                    value.st_dev,
                    value.st_ino,
                    value.st_size,
                    value.st_mtime_ns,
                    value.st_ctime_ns,
                )
                != stamps[1]
            ):
                raise ValueError("resource-envelope journal changed before append")
            os.ftruncate(descriptor, head.journal_bytes)
            os.lseek(descriptor, head.journal_bytes, os.SEEK_SET)
            self._write_all(descriptor, delta)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._fsync_directory(journal_path.parent)
        committed = _JournalHead(
            base_sha256=head.base_sha256,
            journal_sha256=hasher.hexdigest(),
            journal_bytes=head.journal_bytes + len(delta),
            event_count=len(current.events) + 1,
            materialized_bytes=materialized_bytes,
        )
        self._write_atomic(self._path(current.envelope_id, "head"), committed)
        self._journal_hasher = hasher
        return committed, self._stamps(paths)


_INCREMENTAL_STORE_METHODS = {name: getattr(ExternalExecutionResourceEnvelopeStore, name)
    for name in ('current', 'load', 'compare_and_append', '_current', '_read', '_operational_current',
        '_compare_and_append_transition', '_append_event')}


__all__ = [
    "DEFAULT_EXECUTION_RESOURCE_ENVELOPE_STATE_ROOT",
    'ExternalExecutionResourceEnvelopeStore',
    "MAX_EXECUTION_RESOURCE_ENVELOPE_STATE_BYTES",
    "execution_launch_relative_path",
    "read_execution_launch_event",
]
