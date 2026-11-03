# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound reads of compiled scientific products, without provider contact."""

from collections.abc import Mapping
from bisect import bisect_left
from hashlib import sha256
import json
import os
from types import MappingProxyType, MethodType, SimpleNamespace
from weakref import ref

from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (ArtifactLineageParent, ArtifactManifest,
    lineage_parent_sort_key)
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec


# Operational read state; exact custody does not complete binary domain joins.
RAW_BYTES_CONSUMER_JOIN_DEFERRED = "COMPLETE_CANONICAL_RAW_BYTES_CONSUMER_JOIN_DEFERRED"

_STOCK_RECEIPT_VALIDATOR = ExternalRunRecoveryStore._validate_receipt_static


def read_recursive_bootstrap_record(plane, relative_path, kind, *, maximum_bytes=None, expected=None):
    """Read one closed, locator-only metadata member, never its sibling bodies.

    The API selects ``kind`` only from fixed packet/instance codecs and the
    exact installed owner's closed bootstrap roster. This is a partial metadata
    proof; the complete publication and scientific packet still authenticate
    after the original-parent permission check.
    """
    with plane.verification_scope() as scoped:
        manifest = scoped.read_manifest(relative_path)
        from empirical_lawhood.runtime.artifacts import artifact_custody_limits
        limits = artifact_custody_limits(scoped)
        if (limits.exceeds('in_memory_payload_bytes', manifest.materialization.size_bytes)
                or limits.exceeds('control_record_bytes', manifest.materialization.size_bytes)):
            raise ValueError('recursive bootstrap exceeds its selected in-memory or control byte bound')
        if (manifest.logical.payload_schema != kind.SCHEMA
                or manifest.logical.media_type != 'application/json'
                or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or manifest.logical.lineage_parents
                or maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes):
            raise PermissionError('recursive bootstrap requires exact unprivileged locator metadata')
        if expected is not None and (manifest.materialization.size_bytes != expected.size_bytes
                or manifest.logical.content_sha256 != expected.identity.object_fingerprint
                or manifest.materialization.physical_sha256 != expected.identity.object_fingerprint
                or (kind.SCHEMA, kind.VERSION) != (expected.identity.object_schema, expected.identity.object_version)):
            raise PermissionError('recursive bootstrap changes its exact packet-pinned locator member')
        raw = read_bounded_bytes(scoped.root.resolve(relative_path, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes)
        record = decode_canonical_bytes(raw, kind, maximum_bytes=manifest.materialization.size_bytes)
        if (record.canonical_bytes() != raw or len(raw) != manifest.materialization.size_bytes
                or sha256(raw).hexdigest() != manifest.logical.content_sha256
                or sha256(raw).hexdigest() != manifest.materialization.physical_sha256
                or expected is not None and ObjectIdentity.from_record(expected.identity.object_id, record) != expected.identity):
            raise PermissionError('recursive bootstrap changes its exact canonical locator bytes')
        scoped.verify(manifest.materialization)
        scoped.require_verification_snapshot()
    return record


def read_exposed_recursive_payload(plane, manifest, *, maximum_bytes, original_input_access=None):
    """Read an already exposed exact member; never open sealed native evidence."""
    pair = (manifest.logical.outcome_access, manifest.logical.visibility_ceiling)
    if original_input_access is not None:
        original_input_access.require_member(manifest)
    elif pair not in {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
                      (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)}:
        raise PermissionError("recursive payload is not in an exact exposed access pair")
    if maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes:
        raise ValueError("recursive payload exceeds its selected byte bound")
    plane.verify_manifest(manifest,
        **({} if original_input_access is None else {'before_member': original_input_access.require_member}))
    if original_input_access is not None:
        original_input_access.require_member(manifest)
    raw = read_bounded_bytes(plane.root.resolve(manifest.materialization.relative_path, for_write=False),
                             maximum_bytes=manifest.materialization.size_bytes)
    digest = sha256(raw).hexdigest()
    if (len(raw) != manifest.materialization.size_bytes
            or digest != manifest.materialization.physical_sha256
            or digest != manifest.logical.content_sha256):
        raise ValueError("recursive payload changed after exact publication authentication")
    if original_input_access is not None:
        original_input_access.require_current()
    return raw


def iter_exact_custody_file_chunks(path, *, size_bytes, expected_sha256, maximum_chunk_bytes=65536,
        read_guard=None):
    """Consume an exact descriptor twice; memory follows the working chunk size."""
    from empirical_lawhood.infrastructure.bounded_io import _open_regular, _regular_chunks, _stable_descriptor

    if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes <= 0:
        raise ValueError("custody stream requires a positive working chunk size")
    if read_guard is not None and not callable(read_guard):
        raise TypeError('custody stream requires a callable current read guard')
    def require_current():
        if read_guard is not None and read_guard() is not None:
            raise ValueError('custody stream read guard must return None or raise on refusal')
    require_current()
    descriptor, before = _open_regular(path, maximum_bytes=size_bytes)
    digest, count = sha256(), 0
    with _stable_descriptor(descriptor, before, operation="exact custody streaming"):
        for chunk in _regular_chunks(descriptor, before, maximum_bytes=size_bytes,
                chunk_bytes=maximum_chunk_bytes, opened_size_bound=True, operation="exact custody streaming"):
            digest.update(chunk)
            count += len(chunk)
            yield chunk
        if count != size_bytes or digest.hexdigest() != expected_sha256:
            raise ValueError("custody stream differs from its committed identity")
        # Coarse timestamps cannot conceal an edit to an already read chunk.
        require_current()
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = sha256()
        for chunk in _regular_chunks(descriptor, before, maximum_bytes=size_bytes,
                chunk_bytes=maximum_chunk_bytes, opened_size_bound=True, operation="exact custody recheck"):
            second.update(chunk)
        if second.digest() != digest.digest():
            raise ValueError("custody member changed during its streamed read")


def _can_batch_authored_members(plane, member_count):
    """Select only the stock policy path within the caller's request allowance.

    This is an implementation choice, never a verification or authority token.
    Custom hooks retain their original per-member/fresh-load admission.
    """
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _ScopedArtifactPlane
    from empirical_lawhood.runtime.artifacts import artifact_custody_limits
    return (type(plane) in (ExternalArtifactPlane, _ScopedArtifactPlane)
        and not any(name in vars(plane) for name in ("verify_manifest", "verify_manifests",
            "verify_manifest_members", "verify_manifests_members", "_verify_manifests",
            "_consume_verified_manifest_members", "_consume_verified_manifests_members",
            "write", "write_stream", "write_batch", "write_compact_batch"))
        and not artifact_custody_limits(plane).exceeds("publication_members", member_count))


class AuthenticatedRecursivePayloads(Mapping):
    """Receipt-bound authored members; a read retains only its selected bytes.

    Construction authenticates the complete source census and canonical record
    headers incrementally. Strict scientific decoding still belongs to each
    typed consumer; this mapping does not claim scientific assessment.
    """

    def __init__(self, *, plane, directory, members, original_input_access=None):
        from .artifacts import _has_stock_manifest_reads
        if _can_batch_authored_members(plane, len(members)) and _has_stock_manifest_reads(plane):
            with plane.read_context() as reading:
                self._initialize(plane=reading, directory=directory, members=members,
                    original_input_access=original_input_access)
            self.plane = plane
        else:
            self._initialize(plane=plane, directory=directory, members=members,
                original_input_access=original_input_access)

    def _initialize(self, *, plane, directory, members, original_input_access):
        self.plane, self.directory = plane, directory
        self.original_input_access = original_input_access
        if original_input_access is not None and (not callable(getattr(original_input_access, 'require_current', None))
                or not callable(getattr(original_input_access, 'require_member', None))):
            raise TypeError('authored protected inputs require their code-owned current access guard')
        self._members = {member.filename: member for member in members}
        if len(self._members) != len(members):
            raise ValueError("authored wave repeats a member")
        self._manifests = {}
        self._json_headers = {}
        selected = {name: self._member_manifest(name, member) for name, member in self._members.items()}
        for manifest in selected.values():
            self._require_member(manifest)
        self._selected_manifests = MappingProxyType({manifest.materialization.relative_path: manifest
            for manifest in selected.values()})
        # Request size is distinct from each publication's sibling census.
        batch = _can_batch_authored_members(plane, len(self._members))
        if not batch or not self._members:
            for name, member in self._members.items():
                self._manifests[name] = self._authenticate(name, member)
            self._json_headers = MappingProxyType(self._json_headers)
            self.require_current()
            return

        def authenticate(authenticated):
            for name, member in self._members.items():
                expected = selected[name]
                actual = authenticated[expected.materialization.relative_path]
                if actual != expected:
                    raise ValueError("authored wave member changes its exact current manifest")
                self._manifests[name] = self._inspect_member(name, member, actual)

        plane.verify_manifests_members(tuple(selected.values()), validate_members=authenticate,
            **({} if original_input_access is None else {'before_member': self._member_preflight()}))
        self._json_headers = MappingProxyType(self._json_headers)
        self.require_current()

    def require_current(self):
        if self.original_input_access is not None and self.original_input_access.require_current() is not None:
            raise ValueError('original input access guard must return None or raise on refusal')

    def _require_member(self, manifest):
        if self.original_input_access is not None and self.original_input_access.require_member(manifest) is not None:
            raise ValueError('original input member guard must return None or raise on refusal')

    def _before_member(self, actual):
        expected = self._selected_manifests.get(actual.materialization.relative_path)
        if expected is None:
            self._require_member(actual)
        elif (actual.logical, actual.materialization) != (expected.logical, expected.materialization):
            raise PermissionError('authored member changes its exact preflight custody')
        else:
            self.require_current()

    def _member_preflight(self):
        """Keep one callback identity, never its current access result.

        Repeated bound-method lookup creates different callback objects. The
        custody owner correctly retains distinct guards, so passing each new
        object would accumulate the same check on every publication sibling.
        A changed function or owner remains a distinct, freshly invoked guard.
        """
        from .artifacts import ConcurrentArtifactMemberPreflight

        callback = self._before_member
        read_scope = getattr(self.original_input_access, 'member_read_scope', None)
        if read_scope is not None and not callable(read_scope):
            raise TypeError('original input member read scope requires a callable')
        previous_ref = getattr(self, '_retained_member_preflight', None)
        previous = None if previous_ref is None else previous_ref()
        previous_callback = (previous.callback
            if type(previous) is ConcurrentArtifactMemberPreflight else previous)
        previous_scope = (previous.read_scope
            if type(previous) is ConcurrentArtifactMemberPreflight else None)
        same_scope = (read_scope is previous_scope
            or type(read_scope) is MethodType and type(previous_scope) is MethodType
            and read_scope.__self__ is previous_scope.__self__
            and read_scope.__func__ is previous_scope.__func__)
        if (type(callback) is MethodType and type(previous_callback) is MethodType
                and callback.__self__ is previous_callback.__self__
                and callback.__func__ is previous_callback.__func__
                and same_scope):
            return previous
        if read_scope is not None:
            callback = ConcurrentArtifactMemberPreflight(callback, read_scope)
        # The live custody scope owns the strong guard reference. This lookup
        # must not create a self-cycle after that scope releases its census.
        self._retained_member_preflight = (ref(callback)
            if type(callback) in (MethodType, ConcurrentArtifactMemberPreflight) else None)
        return callback

    def member_identity(self, name):
        return self._members[name].identity

    def _member_manifest(self, name, member):
        from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads
        from empirical_lawhood.infrastructure.artifact_sidecars import decode_artifact_sidecar
        from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
        from empirical_lawhood.runtime.artifacts import artifact_custody_limits

        limits = artifact_custody_limits(self.plane)
        path = self.directory / name
        relative = path.relative_to(self.plane.root.contract.canonical_path).as_posix()
        if _has_stock_manifest_reads(self.plane):
            # Keep the owning reader's exact sidecar/commit census instead of
            # decoding a second copy of an already authenticated publication.
            manifest = self.plane.read_manifest(relative, maximum_bytes=limits.manifest_bytes)
        else:
            manifest = decode_artifact_sidecar(
                read_bounded_bytes(self.directory / (name + ".manifest.json"), maximum_bytes=limits.manifest_bytes),
                maximum_bytes=limits.manifest_bytes)
            if type(manifest) is ArtifactManifestReference:
                manifest = self.plane.read_manifest(relative, maximum_bytes=limits.manifest_bytes)
        if (manifest.materialization.relative_path != relative
                or manifest.materialization.size_bytes != member.size_bytes
                or manifest.logical.payload_schema != member.identity.object_schema
                or manifest.logical.content_sha256 != member.identity.object_fingerprint
                or manifest.materialization.physical_sha256 != member.identity.object_fingerprint):
            raise ValueError("authored wave member differs from its committed identity")
        return manifest

    def _authenticate(self, name, member):
        manifest = self._member_manifest(name, member)
        self._require_member(manifest)
        self.plane.verify_manifest(manifest,
            **({} if self.original_input_access is None else {'before_member': self._member_preflight()}))
        return self._inspect_member(name, member, manifest)

    def _inspect_member(self, name, member, manifest):
        from empirical_lawhood.infrastructure.artifact_validation import _CanonicalJsonFileInspector
        from empirical_lawhood.infrastructure.bounded_io import _open_regular, _stable_descriptor
        from empirical_lawhood.runtime.artifacts import artifact_custody_limits

        self._require_member(manifest)
        limits = artifact_custody_limits(self.plane)
        path = self.directory / name
        storage = resolve_storage_codec(self.plane.validators.binary_codecs,
            payload_schema=manifest.logical.payload_schema, profile=manifest.logical.profile,
            media_type=manifest.logical.media_type)
        if storage is not None:
            if member.identity.object_version != storage.record_version:
                raise ValueError("authored binary member changes its exact registered revision")
            size, digest = bounded_file_sha256(path, maximum_bytes=member.size_bytes)
            if size != member.size_bytes or digest != member.identity.object_fingerprint:
                raise ValueError("authored wave member differs from its committed identity")
            return manifest
        # The complete current profile scan already inspected these exact
        # bytes. Reuse only its structural facts inside that still-live byte
        # guard, never an access decision or a caller-supplied header.
        header = self.plane.verified_canonical_header(manifest)
        if header is not None:
            if (header.top_level_keys != ('schema', 'value', 'version')
                    or header.schema != member.identity.object_schema
                    or header.version != member.identity.object_version):
                raise ValueError('authored canonical member changes its exact document header')
            self._json_headers[name] = (member.identity, member.size_bytes)
            return manifest
        descriptor, before = _open_regular(path, maximum_bytes=member.size_bytes)
        digest, count = sha256(), 0

        class Reader:
            def read(self, amount):
                nonlocal count
                raw = handle.read(amount)
                digest.update(raw)
                count += len(raw)
                if count > member.size_bytes:
                    raise ValueError("authored wave member grew during its streamed read")
                return raw

        request = SimpleNamespace(payload_schema=member.identity.object_schema,
            semantic_validation=SimpleNamespace(top_level_keys=("schema", "value", "version"),
                value_keys=(), field_bindings=(("version", member.identity.object_version),)))
        with _stable_descriptor(descriptor, before, operation="authored canonical header inspection"):
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                _CanonicalJsonFileInspector(Reader(), request, custody_limits=limits).validate()
        if count != member.size_bytes or digest.hexdigest() != member.identity.object_fingerprint:
            raise ValueError("authored wave member differs from its committed identity")
        # Only this exact JSON body passed the complete header/version scanner.
        # A constructor-binary member has no such proof if codecs later change.
        self._json_headers[name] = (member.identity, member.size_bytes)
        return manifest

    def manifest(self, name):
        return self._manifests[name]

    def chunks(self, name, *, maximum_chunk_bytes=65536):
        """Consume one complete immutable member without allocating its population."""
        member = self._members[name]
        self._require_member(self._manifests[name])
        self.plane.verify_manifest(self._manifests[name],
            **({} if self.original_input_access is None else {'before_member': self._member_preflight()}))
        self._require_member(self._manifests[name])
        yield from iter_exact_custody_file_chunks(self.directory / name, size_bytes=member.size_bytes,
            expected_sha256=member.identity.object_fingerprint, maximum_chunk_bytes=maximum_chunk_bytes,
            **({} if self.original_input_access is None else
                {'read_guard': lambda: self._require_member(self._manifests[name])}))
        self.require_current()

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def __contains__(self, name):
        return name in self._members

    def __getitem__(self, name):
        member = self._members[name]
        self._require_member(self._manifests[name])
        self.plane.verify_manifest(self._manifests[name],
            **({} if self.original_input_access is None else {'before_member': self._member_preflight()}))
        self._require_member(self._manifests[name])
        raw = read_bounded_bytes(self.directory / name, maximum_bytes=member.size_bytes)
        if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.identity.object_fingerprint:
            raise ValueError("authored wave member differs from its committed identity")
        manifest = self._manifests[name]
        self.require_current()
        if resolve_storage_codec(self.plane.validators.binary_codecs,
                payload_schema=manifest.logical.payload_schema, profile=manifest.logical.profile,
                media_type=manifest.logical.media_type) is not None:
            return raw
        if self._json_headers.get(name) == (member.identity, member.size_bytes):
            return raw
        document = json.loads(raw)
        if (document.get("schema"), document.get("version")) != (
                member.identity.object_schema, member.identity.object_version):
            raise ValueError("authored wave member changes its record schema or revision")
        return raw


def _validate_terminal_nonattempt(row, *, tasks, indexed_tasks, run_id):
    """One original pure admission predicate before any terminal-derived path."""
    if (row.task_id not in tasks or row.task_id not in indexed_tasks or row.disposition.value != "BLOCKED"
        or type(row.ordinal) is not int or row.ordinal <= 0
        or row.attempt_id != f"{run_id}.{row.task_id}.block-{row.ordinal:03d}"
        or row.receipt_id is not None or row.receipt_sha256 is not None):
        raise ValueError("recursive terminal changes its exact nonattempt identity or receipt")


def _consume_original_control(*, plane, selected, original_input_access, read_body):
    """Read one frozen operational control under an exact sibling guard."""
    if selected is None:
        return None
    _, expected = selected

    def before_member(actual):
        if actual.materialization.relative_path == expected.materialization.relative_path:
            if (actual.logical, actual.materialization) != (expected.logical, expected.materialization):
                raise PermissionError('original operational control changes its exact selected custody')
            original_input_access.require_current()
        else:
            original_input_access.require_member(actual)

    def consume(authenticated):
        actual = authenticated.get(expected.materialization.relative_path)
        if actual is None or (actual.logical, actual.materialization) != (expected.logical, expected.materialization):
            raise PermissionError('original operational control changes its authenticated member')
        original_input_access.require_current()
        result = read_body(*selected)
        original_input_access.require_current()
        return result

    original_input_access.require_current()
    return plane.verify_manifest_members(expected, validate_members=consume, before_member=before_member)


def _original_receipt(store, run_id, task_id, attempt_id, original_input_access):
    selected = store._read_envelope(run_id, task_id, attempt_id)
    return _consume_original_control(plane=store.plane, selected=selected,
        original_input_access=original_input_access,
        read_body=lambda path, manifest: store._read_body(run_id, task_id, attempt_id, path, manifest))


def _original_recovery_payload(recovery, relative_path, *, schema, maximum_bytes, original_input_access):
    selected = recovery._read_payload_envelope(relative_path,
        expected_schema=schema, maximum_bytes=maximum_bytes)
    return _consume_original_control(plane=recovery.plane, selected=selected,
        original_input_access=original_input_access, read_body=recovery._read_payload_body)


def _original_event(recovery, index, relative_path, original_input_access):
    raw = _original_recovery_payload(recovery, relative_path, schema=index.TASK_EVENT_SCHEMA,
        maximum_bytes=recovery.plane.custody_limits.recovery_event_bytes,
        original_input_access=original_input_access)
    return recovery._decode_event_payload(index, relative_path, raw)


def _operational_census(*, recovery, store, plan, index, terminal,
                        decode_products=True, allow_partial=False, _read_policy=None,
                        original_input_access=None):
    """Read all frozen candidates, retaining failure diagnostics independently."""
    from empirical_lawhood.runtime.execution import TaskBlockKind, TaskBlockReason
    from empirical_lawhood.runtime.recovery import TaskRecoveryEvent

    summaries = {row.attempt_id: row for row in terminal.attempts}
    if len(summaries) != len(terminal.attempts):
        raise ValueError("recursive terminal duplicates an attempt identity")
    # Immutable reference indices are local to this verified custody read.
    # Preserve original per-task order and retain every diagnostic row.
    task_summaries = {}
    for row in terminal.attempts:
        task_summaries.setdefault(row.task_id, []).append(row)
    consumed = set()
    events, attempt_receipts = {}, {}
    tasks = {task.task_id: task for task in plan.tasks}
    indexed_tasks = {binding.task_id for binding in index.tasks}
    candidate_ids = {candidate.attempt_id for binding in index.tasks for candidate in binding.attempts}
    nonattempts = tuple(row for row in terminal.attempts if row.attempt_id not in candidate_ids)
    control_count = (sum(len(binding.attempts) for binding in index.tasks) * 2
        + len(index.tasks) + len(nonattempts))
    batch_controls = _can_batch_compact_control_custody(plane=store.plane, store=store, recovery=recovery,
        decode_products=decode_products, allow_partial=allow_partial, control_count=control_count,
        policy=_read_policy)
    read_receipt, read_event = store.read, recovery.read_event
    if original_input_access is not None:
        from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads
        batch_controls = batch_controls and _has_stock_manifest_reads(store.plane)
        read_receipt = lambda run_id, task_id, attempt_id: _original_receipt(
            store, run_id, task_id, attempt_id, original_input_access)
        read_event = lambda selected_index, relative_path: _original_event(
            recovery, selected_index, relative_path, original_input_access)
    for row in nonattempts:
        _validate_terminal_nonattempt(row, tasks=tasks, indexed_tasks=indexed_tasks, run_id=index.run_id)
        if not batch_controls and read_receipt(index.run_id, row.task_id, row.attempt_id) is not None:
            raise ValueError("recursive terminal changes its exact nonattempt identity or receipt")
    nonattempt_ordinals = {}
    for row in nonattempts:
        nonattempt_ordinals.setdefault(row.task_id, []).append(row.ordinal)
    for ordinals in nonattempt_ordinals.values():
        ordinals.sort()
    for task_id in tasks:
        ordinals = tuple(sorted(row.ordinal for row in task_summaries.get(task_id, ())))
        if ordinals != tuple(range(1, len(ordinals) + 1)):
            raise ValueError("recursive terminal changes its contiguous operational attempt ordinals")
    if batch_controls:
        # Only compact stock custody moves receipt-absence checks after the
        # original pure terminal identities/ordinals and the closed body read.
        controls = _read_compact_control_census(plane=store.plane, store=store, recovery=recovery,
            index=index, nonattempts=nonattempts, control_count=control_count, policy=_read_policy,
            **({} if original_input_access is None else {"original_input_access": original_input_access}))
        if controls is not None:
            read_receipt = lambda run_id, task_id, attempt_id: controls[("receipt", run_id, task_id, attempt_id)]
            read_event = lambda selected_index, relative_path: controls[("event", relative_path)]
        for row in nonattempts:
            if read_receipt(index.run_id, row.task_id, row.attempt_id) is not None:
                raise ValueError("recursive terminal changes its exact nonattempt identity or receipt")
    for binding in index.tasks:
        for candidate in binding.attempts:
            receipt = read_receipt(index.run_id, binding.task_id, candidate.attempt_id)
            event = read_event(index, candidate.event_relative_path)
            summary = summaries.get(candidate.attempt_id)
            if summary is None:
                if receipt is not None or event is not None:
                    raise ValueError("recursive terminal omits a retained attempt")
                continue
            consumed.add(summary.attempt_id)
            # Candidate/event ordinals count entered attempts; the terminal also
            # counts earlier nonattempt blocks retained across explicit resumes.
            prior_blocks = bisect_left(nonattempt_ordinals.get(binding.task_id, ()), summary.ordinal)
            if (summary.task_id != binding.task_id or summary.ordinal != candidate.ordinal + prior_blocks
                or event is None or event.task_id != binding.task_id
                or event.attempt_id != candidate.attempt_id or event.attempt_ordinal != candidate.ordinal):
                raise ValueError("recursive terminal changes its exact attempt identity or ordinal")
            if summary.disposition.value == "SUCCEEDED":
                if receipt is None:
                    raise ValueError("recursive terminal lacks its completed receipt")
                ExternalRunRecoveryStore._validate_receipt_static(index, tasks[binding.task_id], candidate, receipt)
                if (receipt.receipt_id != summary.receipt_id or receipt.fingerprint() != summary.receipt_sha256
                    or event != TaskRecoveryEvent.from_receipt(index, receipt)):
                    raise ValueError("recursive terminal changes its exact receipt or recovery event")
                attempt_receipts[summary.attempt_id] = receipt
            elif (receipt is not None or event is None or event.disposition.value != summary.disposition.value
                  or event.reason_codes != (summary.reason_code,)):
                raise ValueError("recursive failed or blocked attempt lacks its exact recovery event")
            events[summary.attempt_id] = event
        nonattempt = read_event(index, binding.nonattempt_event_relative_path)
        if nonattempt is not None:
            matches = tuple(row for row in task_summaries.get(binding.task_id, ())
                            if row.disposition.value == "BLOCKED" and row.reason_code == nonattempt.reason_codes[0]
                            and row.attempt_id not in consumed)
            if len(matches) != 1:
                raise ValueError("recursive terminal omits or ambiguously owns a nonattempt event")
            row = matches[0]
            if (row.attempt_id != f"{index.run_id}.{binding.task_id}.block-{row.ordinal:03d}"
                or nonattempt.task_id != binding.task_id or nonattempt.attempt_id is not None
                or nonattempt.attempt_ordinal is not None or nonattempt.disposition.value != "NOT_ATTEMPTED"):
                raise ValueError("recursive terminal changes its exact nonattempt identity or ordinal")
            consumed.add(matches[0].attempt_id)
            events[matches[0].attempt_id] = nonattempt
    for row in nonattempts:
        if row.attempt_id in consumed:
            continue
        try:
            reason = TaskBlockReason(row.reason_code)
        except ValueError as error:
            raise ValueError("recursive terminal has an unknown nonattempt block reason") from error
        if reason.kind is not TaskBlockKind.RETRYABLE:
            raise ValueError("recursive durable nonattempt lacks its exact recovery event")
        # Retryable block observations are owned by the authenticated terminal.
        # They consume no frozen executable candidate and have no invented event.
        consumed.add(row.attempt_id)
    if consumed != set(summaries):
        raise ValueError("recursive terminal contains an unauthenticated attempt")
    rows = tuple({"task_id": row.task_id, "attempt_id": row.attempt_id, "ordinal": row.ordinal,
                  "operational_status": row.disposition.value, "reason_code": row.reason_code,
                  "receipt_id": row.receipt_id, "receipt_sha256": row.receipt_sha256,
                  "recovery_event": (events[row.attempt_id].to_document()
                                     if row.attempt_id in events else None),
                  "recovery_event_status": ("AUTHENTICATED" if row.attempt_id in events
                                            else "MISSING_TERMINAL_PRIMARY_NONATTEMPT"),
                  "actual_cpu_seconds": None, "actual_wall_seconds": None, "actual_peak_rss_bytes": None}
                 for row in terminal.attempts)
    return rows, events, attempt_receipts


def _partial_operational_census(*, recovery, store, plan, index, original_input_access=None):
    """Inspect completion custody without inventing a terminal or re-entering work."""
    from empirical_lawhood.runtime.recovery import TaskRecoveryEvent

    rows, events, receipts, summaries = [], {}, {}, {}
    tasks = {task.task_id: task for task in plan.tasks}
    read_receipt = store.read if original_input_access is None else (
        lambda run_id, task_id, attempt_id: _original_receipt(store, run_id, task_id, attempt_id, original_input_access))
    read_event = recovery.read_event if original_input_access is None else (
        lambda selected_index, relative_path: _original_event(recovery, selected_index, relative_path, original_input_access))
    for binding in index.tasks:
        for candidate in binding.attempts:
            receipt = read_receipt(index.run_id, binding.task_id, candidate.attempt_id)
            event = read_event(index, candidate.event_relative_path)
            if receipt is None and event is None:
                continue
            if receipt is not None:
                ExternalRunRecoveryStore._validate_receipt_static(index, tasks[binding.task_id], candidate, receipt)
                expected = TaskRecoveryEvent.from_receipt(index, receipt)
                if event is not None and event != expected:
                    raise ValueError("recursive partial receipt changes its exact recovery event")
                status, reason = receipt.operational_status.value, None
                receipts[candidate.attempt_id] = receipt
            else:
                if (event.task_id != binding.task_id or event.attempt_id != candidate.attempt_id
                        or event.attempt_ordinal != candidate.ordinal or event.disposition.value == "SUCCEEDED"):
                    raise ValueError("recursive partial recovery event lacks its exact completion receipt")
                status, reason = event.disposition.value, event.reason_codes[0]
            summary = SimpleNamespace(task_id=binding.task_id, attempt_id=candidate.attempt_id,
                ordinal=candidate.ordinal, disposition=SimpleNamespace(value=status), reason_code=reason,
                receipt_id=None if receipt is None else receipt.receipt_id,
                receipt_sha256=None if receipt is None else receipt.fingerprint())
            summaries[binding.task_id] = summary
            if event is not None:
                events[candidate.attempt_id] = event
            rows.append({"task_id": binding.task_id, "attempt_id": candidate.attempt_id,
                "ordinal": candidate.ordinal, "operational_status": status, "reason_code": reason,
                "receipt_id": summary.receipt_id, "receipt_sha256": summary.receipt_sha256,
                "recovery_event": None if event is None else event.to_document(),
                "recovery_event_status": "MISSING" if event is None else "AUTHENTICATED",
                "actual_cpu_seconds": None, "actual_wall_seconds": None, "actual_peak_rss_bytes": None})
        event = read_event(index, binding.nonattempt_event_relative_path)
        if event is not None:
            if (event.task_id != binding.task_id or event.attempt_id is not None
                    or event.attempt_ordinal is not None or event.disposition.value != "NOT_ATTEMPTED"):
                raise ValueError("recursive partial nonattempt event changes its exact task identity")
            if binding.task_id in summaries:
                raise ValueError("recursive partial task has both entered and nonattempt custody")
            summaries[binding.task_id] = SimpleNamespace(task_id=binding.task_id,
                disposition=SimpleNamespace(value="BLOCKED"), reason_code=event.reason_codes[0])
            events[binding.task_id] = event
            rows.append({"task_id": binding.task_id, "attempt_id": None, "ordinal": None,
                "operational_status": "NOT_ATTEMPTED", "reason_code": event.reason_codes[0],
                "receipt_id": None, "receipt_sha256": None, "recovery_event": event.to_document(),
                "recovery_event_status": "AUTHENTICATED", "actual_cpu_seconds": None,
                "actual_wall_seconds": None, "actual_peak_rss_bytes": None})
    return tuple(rows), events, receipts, summaries


def _can_batch_output_custody(*, plane, store, output_count, policy):
    """Use only this call's API-owned stock root/inspector/registry selection.

    The tuple is a local implementation selection, not a cached custody or
    authority proof. Unknown/custom policy keeps the original serial route.
    """
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane, _has_stock_artifact_plane_state
    from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits

    if type(policy) is not tuple or len(policy) != 6:
        return False
    root, inspector, contract, validators, semantics, limits = policy
    return (output_count > 2
        and type(plane) is _ScopedArtifactPlane and plane._read_verification.active
        and _has_stock_artifact_plane_state(plane)
        and plane.root is root and root.inspector is inspector and root.contract is contract
        and plane.validators is validators and plane.semantic_validations is semantics
        and type(limits) is ArtifactCustodyLimits and plane.custody_limits is limits
        and set(vars(root)) == {"contract", "inspector"} and set(vars(inspector)) == {"_bound"}
        and _can_batch_authored_members(plane, output_count)
        and type(store) is ExternalTaskReceiptStore and store.plane is plane
        and set(vars(store)) == {"plane", "minimum_free_bytes"})


def _can_batch_compact_output_custody(*, decode_products, **options):
    return decode_products is False and _can_batch_output_custody(**options)


def _can_batch_compact_control_custody(*, plane, store, recovery, decode_products,
                                       allow_partial, control_count, policy):
    from empirical_lawhood.infrastructure.task_receipts import _has_stock_task_receipt_reads
    from empirical_lawhood.infrastructure.recovery import _has_stock_recovery_reads
    return (allow_partial is False
        and _can_batch_compact_output_custody(plane=plane, store=store,
            decode_products=decode_products, output_count=control_count, policy=policy)
        and _has_stock_task_receipt_reads(store) and _has_stock_recovery_reads(recovery)
        and recovery.plane is plane)


def _read_compact_control_census(*, plane, store, recovery, index, nonattempts, control_count, policy,
                               original_input_access=None):
    """Read only this frozen canonical roster under two existing plural guards.

    Receipt and event batches preserve their separate error translations.
    The returned map owns decoded controls/None, never a reusable custody proof.
    """
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, _has_stock_manifest_reads
    from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
    from empirical_lawhood.infrastructure.recovery import RunRecoveryError
    receipt_keys = tuple((index.run_id, row.task_id, row.attempt_id) for row in nonattempts) + tuple(
        (index.run_id, binding.task_id, candidate.attempt_id)
        for binding in index.tasks for candidate in binding.attempts)
    event_paths = tuple(path for binding in index.tasks
        for path in (*(candidate.event_relative_path for candidate in binding.attempts),
            binding.nonattempt_event_relative_path))
    receipt_envelopes = tuple((key, store._read_envelope(*key)) for key in receipt_keys)
    event_envelopes = tuple((path, recovery._read_payload_envelope(path,
        expected_schema=index.TASK_EVENT_SCHEMA, maximum_bytes=plane.custody_limits.recovery_event_bytes))
        for path in event_paths)
    for _, selected in (*receipt_envelopes, *event_envelopes):
        if selected is not None:
            _, manifest = selected
            # Other/legacy sibling sets retain the original complete reader.
            if (manifest.publication is None or len(manifest.publication.members) != 1
                    or manifest.publication.members[0].relative_path != manifest.materialization.relative_path):
                return None
    absent_receipts = tuple(store._relative_path(*key) for key, value in receipt_envelopes if value is None)
    absent_events = tuple(path for path, value in event_envelopes if value is None)

    def require_current():
        if original_input_access is not None:
            original_input_access.require_current()

    def member_options(envelopes):
        if original_input_access is None:
            return {}
        expected = {selected[1].materialization.relative_path: selected[1]
            for _, selected in envelopes if selected is not None}

        def before_member(actual):
            selected = expected.get(actual.materialization.relative_path)
            if selected is None:
                original_input_access.require_member(actual)
            elif (actual.logical, actual.materialization) != (selected.logical, selected.materialization):
                raise PermissionError('original operational control changes its exact selected custody')
            else:
                require_current()

        return {"before_member": before_member}

    def require_route():
        if not _can_batch_compact_control_custody(plane=plane, store=store, recovery=recovery,
                decode_products=False, allow_partial=False, control_count=control_count, policy=policy) or (
                original_input_access is not None and not _has_stock_manifest_reads(plane)):
            raise ValueError("compact control read changes its selected stock custody policy")

    def require_absences(kind=None):
        for tag, paths, error, message in (
                ("receipt", absent_receipts, ArtifactIdentityConflict, "task receipt appeared during compact custody read"),
                ("event", absent_events, RunRecoveryError, "recovery artifact appeared during compact custody read")):
            if kind is None or tag == kind:
                for relative in paths:
                    if any(plane.root.resolve(name, for_write=False).exists()
                            for name in (relative, relative + ".manifest.json")):
                        raise error(message)

    def consume_receipts(authenticated):
        require_route()
        require_current()
        require_absences("receipt")
        values = {}
        for key, selected in receipt_envelopes:
            if selected is None:
                values[("receipt", *key)] = None
                continue
            path, manifest = selected
            if authenticated.get(manifest.materialization.relative_path) != manifest:
                raise ArtifactIdentityConflict("task receipt manifest changed during compact custody read")
            require_current()
            require_route()
            values[("receipt", *key)] = store._read_body(*key, path, manifest)
            require_current()
            require_route()
        require_absences("receipt")
        require_route()
        require_current()
        return values

    def consume_events(authenticated):
        require_route()
        require_current()
        require_absences("event")
        values = {}
        for relative, selected in event_envelopes:
            if selected is None:
                values[("event", relative)] = None
                continue
            path, manifest = selected
            if authenticated.get(manifest.materialization.relative_path) != manifest:
                raise RunRecoveryError("recovery artifact custody is invalid")
            require_current()
            require_route()
            payload = recovery._read_payload_body(path, manifest)
            values[("event", relative)] = recovery._decode_event_payload(index, relative, payload)
            require_current()
            require_route()
        require_absences("event")
        require_route()
        require_current()
        return values

    require_route()
    require_current()
    require_absences()
    receipt_manifests = tuple(selected[1] for _, selected in receipt_envelopes if selected is not None)
    event_manifests = tuple(selected[1] for _, selected in event_envelopes if selected is not None)
    values = (plane.verify_manifests_members(receipt_manifests, validate_members=consume_receipts,
        **member_options(receipt_envelopes))
        if receipt_manifests else consume_receipts({}))
    require_absences()
    try:
        values.update(plane.verify_manifests_members(event_manifests, validate_members=consume_events,
            **member_options(event_envelopes))
            if event_manifests else consume_events({}))
    except (ArtifactIdentityConflict, BoundedFileIOError, OSError, ValueError) as error:
        if original_input_access is not None and isinstance(error, PermissionError):
            raise
        raise RunRecoveryError("recovery artifact custody is invalid") from error
    require_absences()
    require_route()
    if original_input_access is not None:
        # Both plural consumers have finished. Close their union before any
        # decoded control can be used as product admission; a read_context's
        # later outer guard must not be their first post-consumer byte check.
        plane.require_verification_snapshot()
    require_current()
    return values

def _verified_product_path(*, plane, logical, material):
    """Independently hash one exact body without retaining its population."""
    path = plane.root.resolve(material.relative_path, for_write=False)
    observed_size, observed_digest = bounded_file_sha256(path, maximum_bytes=material.size_bytes)
    if observed_size != material.size_bytes or observed_digest != material.physical_sha256 or observed_digest != logical.content_sha256:
        raise ValueError("recursive scientific bytes differ from their completion receipt")
    return path, observed_digest


_STOCK_VERIFIED_PRODUCT_PATH = _verified_product_path


def _require_no_orphaned_native_custody(*, plane, run_id, task_id, contacts=None):
    """Check only this task's deterministic invocation and direct roster paths."""
    task_key = sha256(task_id.encode()).hexdigest()
    root = f'runs/{run_id}' if contacts is None else contacts.custody_root(run_id, task_id)
    if contacts is not None:
        task_key = contacts.storage_key(run_id, task_id, task_key)
    invocation = f'{root}/native-invocations/{task_key}.json'
    for relative in (invocation, invocation + ".manifest.json"):
        if plane.root.resolve(relative, for_write=False).exists():
            raise ValueError("native observation has orphaned native invocation custody without its root contact")
    rosters = plane.root.resolve(f'{root}/native-subwork-rosters/{task_key}', for_write=False)
    if rosters.exists() and (not rosters.is_dir() or next(rosters.iterdir(), None) is not None):
        raise ValueError("native observation has orphaned native roster custody without its root contact")


def _inspect_native_observations(*, plane, plan, index, external_by_id, receipts, original_input_access=None):
    """Project current native facts beside, never over, original attempt history."""
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_parent_finalization import inspect_native_parent_return
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.runtime.artifacts import most_restrictive_outcome_access
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput, dependency_artifact_inputs
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    from empirical_lawhood.runtime.native_continuation_execution import native_continuation_scopes

    observations, unavailable = {}, {}
    continuation_scopes = {row.task_id: (row,) for row in native_continuation_scopes(index)}
    dependency_outputs = {task_id: tuple(VerifiedArtifactInput(logical, material)
        for logical, material in zip(receipt.output_logical_artifacts,
            receipt.output_materializations, strict=True)) for task_id, receipt in receipts.items()}
    for task in plan.tasks:
        if original_input_access is not None:
            original_input_access.require_current()
        visibility = VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for row in task.outputs))
        access = most_restrictive_outcome_access(task.capability.requested_outcome_access,
            *(row.outcome_access for row in task.outputs))
        contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=index.execution_plan,
            visibility_ceiling=visibility, outcome_access=access,
            continuation_scopes=continuation_scopes.get(task.task_id, ()))
        parent = contacts.read(index.run_id, task.task_id)
        if parent is None:
            _require_no_orphaned_native_custody(plane=plane, run_id=index.run_id, task_id=task.task_id, contacts=contacts)
            continue
        if parent.attempt_id not in {row.attempt_id for row in index.task(task.task_id).attempts}:
            raise ValueError("native observation changes its frozen original attempt")
        required = dependency_artifact_inputs(task, dependency_outputs)
        external = tuple(external_by_id[row.logical_artifact_id] for row in task.external_inputs)
        inputs = tuple(ArtifactManifest(row.logical, row.materialization) for row in (*external, *required))
        expected = NativeEffectContact(index.run_id, task.task_id, parent.attempt_id, index.execution_plan,
            ObjectIdentity.from_record(task.task_id, task), plan.implementation_commit,
            tuple(sorted(row.materialization.materialization_id for row in inputs)),
            tuple(sorted(receipts[dependency].receipt_id for dependency in task.dependency_task_ids)))
        if parent != expected:
            raise ValueError("native observation substitutes its original task, source or input custody")
        subwork = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts,
            parent_contact=parent, parent_inputs=inputs, completed_only=True)
        invocation = subwork.read_prepared_invocation(parent)
        if invocation is None:
            unavailable[parent.attempt_id] = "ORIGINAL_PREPARED_NATIVE_CENSUS_UNAVAILABLE"
            continue
        actual_inputs = {row.logical.logical_artifact_id: row for row in inputs}
        if len(actual_inputs) != len(inputs) or len(invocation.inputs) != len(inputs):
            raise ValueError("native observation changes its complete original input census")
        for row in invocation.inputs:
            actual = actual_inputs.get(row.artifact_id)
            if actual is None or (row.logical, row.binding.materialization_id, row.binding.size_bytes,
                    row.physical_sha256) != (actual.logical, actual.materialization.materialization_id,
                    actual.materialization.size_bytes, actual.materialization.physical_sha256):
                raise ValueError("native observation substitutes an original prepared input")
        if any(row.receipt_id != receipts[row.task_id].receipt_id
                or not set(row.output_materialization_ids).issubset(
                    value.materialization_id for value in receipts[row.task_id].output_materializations)
                for row in invocation.dependency_receipts):
            raise ValueError("native observation substitutes an original dependency receipt")
        if invocation.native_work is None or not invocation.native_work.definitions:
            unavailable[parent.attempt_id] = "ORIGINAL_PREPARED_NATIVE_CENSUS_UNAVAILABLE"
            continue
        if original_input_access is not None:
            original_input_access.require_current()
        observations[parent.attempt_id] = inspect_native_parent_return(store=subwork, work=invocation.native_work)
    return observations, unavailable


def _assemble_read_products(*, plane, plan, index, store, external_by_id, output_codecs,
                            decode_products, terminal, summaries, allow_partial, operational_census,
                            recovery_events, attempt_receipts, issued,
                            _read_policy=None, original_input_access=None):
    """Assemble exact products after the caller's plan/source/census admission.

    The private issued flag retains the two existing issued receipt rules.
    Current authority and operational-census admission remain with each caller.
    """
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane, _has_stock_manifest_reads
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.infrastructure.task_receipts import _has_stock_task_receipt_reads

    reuse_attempt_receipts = (type(plane) is _ScopedArtifactPlane
        and _can_batch_authored_members(plane, 0)
        and type(store) is ExternalTaskReceiptStore and store.plane is plane
        and "read" not in vars(store))
    task_by_id = {task.task_id: task for task in plan.tasks}
    output_count = 0
    if _can_batch_output_custody(plane=plane, store=store,
            output_count=3, policy=_read_policy):
        output_count = sum(len(task.outputs) for task in plan.tasks
            if (summary := summaries.get(task.task_id)) is not None and summary.disposition.value == "SUCCEEDED")
    batch_compact = output_count > 2 and _can_batch_compact_output_custody(plane=plane, store=store,
        decode_products=decode_products, output_count=output_count, policy=_read_policy)
    stock_compact_window = (batch_compact and _has_stock_manifest_reads(plane)
        and _has_stock_task_receipt_reads(store)
        and ExternalRunRecoveryStore._validate_receipt_static is _STOCK_RECEIPT_VALIDATOR
        and _verified_product_path is _STOCK_VERIFIED_PRODUCT_PATH)
    batch_receipt_snapshot = stock_compact_window and reuse_attempt_receipts
    full_receipt_window = (decode_products and reuse_attempt_receipts
        and plane._read_verification.context_depth and _has_stock_manifest_reads(plane)
        and _has_stock_task_receipt_reads(store)
        and ExternalRunRecoveryStore._validate_receipt_static is _STOCK_RECEIPT_VALIDATOR
        and _verified_product_path is _STOCK_VERIFIED_PRODUCT_PATH)
    batch_full = (full_receipt_window and _can_batch_output_custody(plane=plane, store=store,
        output_count=output_count, policy=_read_policy))
    batch_outputs = batch_compact or batch_full
    def require_output_batch():
        require_stock_full_window()
        require_stock_compact_window()
        selected = (_can_batch_output_custody(plane=plane, store=store,
            output_count=output_count, policy=_read_policy) if batch_full else
            _can_batch_compact_output_custody(plane=plane, store=store,
                decode_products=decode_products, output_count=output_count, policy=_read_policy))
        if not selected:
            raise ValueError('output read policy changed during its bounded consumption')
    def require_stock_full_window():
        if full_receipt_window and (not _has_stock_manifest_reads(plane)
                or not _has_stock_task_receipt_reads(store)
                or ExternalRunRecoveryStore._validate_receipt_static is not _STOCK_RECEIPT_VALIDATOR
                or _verified_product_path is not _STOCK_VERIFIED_PRODUCT_PATH):
            raise ValueError("full receipt/byte policy changed during its bounded read")
    def require_stock_compact_window():
        if stock_compact_window and (not _has_stock_task_receipt_reads(store)
                or ExternalRunRecoveryStore._validate_receipt_static is not _STOCK_RECEIPT_VALIDATOR
                or _verified_product_path is not _STOCK_VERIFIED_PRODUCT_PATH):
            raise ValueError("compact receipt/byte policy changed during its bounded read")
    if batch_receipt_snapshot or full_receipt_window:
        require_stock_compact_window()
        require_stock_full_window()
        plane.require_verification_snapshot()
    pending, pending_decodes = [], []
    outputs, receipts, records, dispositions, product_index = {}, {}, {}, [], []
    known_members = {value.materialization.relative_path: value for value in external_by_id.values()}
    def before_product_member(actual):
        expected = known_members.get(actual.materialization.relative_path)
        if expected is None:
            original_input_access.require_member(actual)
        elif (actual.logical, actual.materialization) != (expected.logical, expected.materialization):
            raise PermissionError('recursive product sibling changes its exact frozen custody')
        else:
            original_input_access.require_current()
    partial_census = allow_partial and (terminal is None or terminal.operational_status in ("BLOCKED", "FAILED"))
    for task_id in plan.topological_task_ids():
        if original_input_access is not None:
            original_input_access.require_current()
        task = task_by_id[task_id]
        summary = summaries.get(task_id)
        if summary is None:
            if partial_census:
                dispositions.append({"task_id": task_id, "operational_status": "NO_COMPLETION_RECEIPT",
                                     "reason_code": "ENTRY_OR_PROCESS_STATE_NOT_INFERRED"})
                continue
            raise ValueError("recursive terminal omits a task in its assigned census")
        dispositions.append({"task_id": task_id, "operational_status": summary.disposition.value,
                             "reason_code": summary.reason_code})
        if summary.disposition.value != "SUCCEEDED":
            continue
        candidate = next(value for value in index.task(task_id).attempts if value.attempt_id == summary.attempt_id)
        if reuse_attempt_receipts:
            # The operational census already authenticated this exact receipt.
            # Stock full reads close the union before and after assembly.
            # Each output still receives its independent hash and typed read;
            # current permission remains eager for every task and member.
            require_stock_full_window()
            if full_receipt_window:
                plane.require_verification_context()
            elif not batch_receipt_snapshot:
                plane.require_verification_snapshot()
            receipt = attempt_receipts.get(candidate.attempt_id)
            if (type(receipt) is not CanonicalTaskReceipt
                    or (receipt.run_id, receipt.task_id, receipt.attempt_id)
                    != (index.run_id, task_id, candidate.attempt_id)):
                raise ValueError("scoped product receipt differs from its authenticated attempt census")
        else:
            receipt = (store.read(index.run_id, task_id, candidate.attempt_id)
                if original_input_access is None else _original_receipt(
                    store, index.run_id, task_id, candidate.attempt_id, original_input_access))
        if receipt is None or receipt.fingerprint() != summary.receipt_sha256 or receipt.receipt_id != summary.receipt_id:
            raise ValueError("recursive terminal substitutes a completed receipt")
        ExternalRunRecoveryStore._validate_receipt_static(index, task, candidate, receipt)
        if receipt.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError("completed scientific products require a successful operational receipt")
        wanted_inputs = set()
        input_logicals = {}
        for external in task.external_inputs:
            value = external_by_id.get(external.logical_artifact_id)
            if value is None:
                raise ValueError("recursive receipt lacks an authenticated external input")
            wanted_inputs.add(value.materialization.materialization_id)
            input_logicals[value.logical.logical_artifact_id] = value.logical
        for edge in task.scientific_inputs:
            if edge.producer_task_id is not None:
                value = outputs.get(edge.operational_logical_artifact_id)
                if value is None:
                    raise ValueError("completed consumer has a missing producer receipt")
                wanted_inputs.add(value.materialization.materialization_id)
                input_logicals[value.logical.logical_artifact_id] = value.logical
        expected_parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(value.logical_artifact_id, value),
                                                              value.visibility_ceiling, value.outcome_access)
                                        for value in input_logicals.values()), key=lineage_parent_sort_key))
        if tuple(sorted(wanted_inputs)) != receipt.input_materialization_ids:
            raise ValueError("recursive receipt changes its exact input materialization census")
        logical_by_id = {value.logical_artifact_id: value for value in receipt.output_logical_artifacts}
        materials = {value.logical_artifact_id: value for value in receipt.output_materializations}
        if issued or original_input_access is not None:
            if set(logical_by_id)!={v.logical_artifact_id for v in task.outputs} or set(materials)!=set(logical_by_id):
                raise ValueError("issued scientific receipt changes exact output census")
        if original_input_access is not None:
            # Authenticate every sibling's scientific metadata before storage
            # may hash any member of the task's committed output publication.
            for spec in task.outputs:
                logical, material = logical_by_id[spec.logical_artifact_id], materials[spec.logical_artifact_id]
                if ((logical.payload_schema, logical.profile, logical.media_type,
                        logical.visibility_ceiling, logical.outcome_access) !=
                        (spec.payload_schema, spec.profile, spec.media_type,
                            spec.visibility_ceiling, spec.outcome_access)
                        or logical.lineage_parents != expected_parents):
                    raise PermissionError('recursive product sibling changes its frozen scientific role or lineage')
                manifest = ArtifactManifest(logical, material)
                previous = known_members.setdefault(material.relative_path, manifest)
                if (previous.logical, previous.materialization) != (logical, material):
                    raise PermissionError('recursive product siblings alias distinct frozen inputs or outputs')
        task_records = {}
        for spec in task.outputs:
            logical, material = logical_by_id[spec.logical_artifact_id], materials[spec.logical_artifact_id]
            if (logical.payload_schema != spec.payload_schema or logical.profile is not spec.profile
                or logical.media_type != spec.media_type
                or logical.visibility_ceiling is not spec.visibility_ceiling
                or logical.outcome_access is not spec.outcome_access):
                raise ValueError("recursive output changes its frozen scientific role")
            if logical.lineage_parents != expected_parents:
                raise ValueError("recursive output changes its exact scientific input lineage")
            manifest = ArtifactManifest(logical, material)
            if original_input_access is not None:
                # Actual plan, successful receipt, materialization census and
                # exact direct scientific lineage have all joined above.
                original_input_access.require_current()
            if not batch_outputs:
                if original_input_access is None:
                    plane.verify_manifest(manifest)
                else:
                    plane.verify_manifest_members(manifest, validate_members=lambda _: None,
                        before_member=before_product_member)
            codec = output_codecs.get(logical.payload_schema)
            opaque_binary = resolve_storage_codec(plane.validators.binary_codecs,
                payload_schema=logical.payload_schema, profile=logical.profile, media_type=logical.media_type) is not None
            if codec is None and not opaque_binary:
                raise ValueError("recursive output lacks its registered strict record codec")
            from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
            output_task = index.repair.task(task) if isinstance(index, DevelopmentOutputRepairRecoveryIndex) else task
            limit = output_task.capability.requested_resources.output_bytes
            if limit is not None and material.size_bytes > limit:
                raise ValueError("recursive output exceeds its committed byte allocation")
            if batch_outputs:
                # This is only a private metadata plan until the batch returns.
                # In particular, it does not assert that any body was verified.
                pending.append(manifest)
            else:
                if original_input_access is not None:
                    original_input_access.require_current()
                path, observed_digest = _verified_product_path(plane=plane, logical=logical, material=material)
            if batch_full and not opaque_binary:
                pending_decodes.append((task_records, spec.output_id, manifest, codec, limit))
            elif decode_products and not opaque_binary:
                if original_input_access is not None:
                    original_input_access.require_current()
                raw = read_bounded_bytes(path, maximum_bytes=material.size_bytes)
                if len(raw) != material.size_bytes or sha256(raw).hexdigest() != observed_digest:
                    raise ValueError("recursive scientific bytes changed before their typed read")
                task_records[spec.output_id] = decode_canonical_bytes(raw, codec, maximum_bytes=limit)
                if original_input_access is not None:
                    original_input_access.require_current()
            product_index.append({"task_id": task_id, "output_id": spec.output_id,
                "logical_artifact_id": logical.logical_artifact_id, "schema": logical.payload_schema,
                "sha256": logical.content_sha256, "size_bytes": material.size_bytes,
                "relative_path": material.relative_path,
                "producing_receipt": ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document(),
                "outcome_access": logical.outcome_access.value,
                "visibility_ceiling": logical.visibility_ceiling.value})
            outputs[logical.logical_artifact_id] = manifest
        receipts[task_id] = receipt
        records[task_id] = task_records
    if set(summaries) - set(task_by_id) or (terminal is not None and not partial_census
            and set(summaries) != set(task_by_id)):
        raise ValueError("recursive terminal contains unknown tasks")
    if pending:
        if original_input_access is not None:
            original_input_access.require_current()
        def consume(authenticated):
            require_output_batch()
            # No domain/typed/user consumer runs in this read-only boundary.
            # Later metadata faults can precede earlier body faults; callers
            # requiring inter-output consumer admission retain the serial route.
            for manifest in pending:
                require_output_batch()
                actual = authenticated.get(manifest.materialization.relative_path)
                if actual is None or (actual.logical, actual.materialization) != (manifest.logical, manifest.materialization):
                    raise ValueError("recursive output changes its actual publication metadata")
                if original_input_access is not None:
                    original_input_access.require_current()
                if stock_compact_window or batch_full:
                    if not _has_stock_manifest_reads(plane):
                        raise ValueError("stock byte verification policy changed during its bounded read")
                    if actual.materialization.physical_sha256 == actual.logical.content_sha256:
                        # Exact owner-authenticated metadata plus freshly scanned
                        # physical bytes need no second hash of the same body.
                        continue
                _verified_product_path(plane=plane, logical=manifest.logical, material=manifest.materialization)
        require_output_batch()
        if stock_compact_window and not _has_stock_manifest_reads(plane):
            raise ValueError("compact stock byte verification policy changed before its bounded read")
        plane.verify_manifests_members(tuple(pending), validate_members=consume,
            **({} if original_input_access is None else {'before_member': before_product_member}))
        require_output_batch()
        if stock_compact_window and not _has_stock_manifest_reads(plane):
            raise ValueError("compact stock byte verification policy changed before its result")
        # The existing callback owner has checked the complete member/sidecar/
        # marker/ancestor snapshot before any result row can escape this call.
    # Full reads authenticate the complete output census before typed decoding.
    # This lets independent format checks fill the bounded CPU pool instead of
    # submitting one large product and immediately waiting for it. Retain the
    # original decoding order and one transient raw body; no scientific consumer
    # receives products before the complete closing guard below.
    for task_records, output_id, manifest, codec, limit in pending_decodes:
        require_output_batch()
        if original_input_access is not None:
            original_input_access.require_current()
        material = manifest.materialization
        path = plane.root.resolve(material.relative_path, for_write=False)
        raw = read_bounded_bytes(path, maximum_bytes=material.size_bytes)
        if len(raw) != material.size_bytes or sha256(raw).hexdigest() != material.physical_sha256:
            raise ValueError('recursive scientific bytes changed before their typed read')
        task_records[output_id] = decode_canonical_bytes(raw, codec, maximum_bytes=limit)
        del raw
        if original_input_access is not None:
            original_input_access.require_current()
    if batch_receipt_snapshot and not pending:
        plane.require_verification_snapshot()
        raise ValueError("compact receipt window lacks its declared output custody batch")
    if full_receipt_window:
        require_stock_full_window()
        # No native inspection or scientific consumer can receive the typed
        # products until the complete receipt/member union is rechecked.
        plane.require_verification_snapshot()
    native_observations, native_unavailable = _inspect_native_observations(plane=plane, plan=plan,
        index=index, external_by_id=external_by_id, receipts=receipts, original_input_access=original_input_access)
    if original_input_access is not None:
        original_input_access.require_current()
    return {"terminal": terminal, "receipts": receipts, "records": records,
            "outputs": outputs, "dispositions": dispositions, "operational_census": operational_census,
            "recovery_events": recovery_events, "attempt_receipts": attempt_receipts,
            "native_observations": native_observations, "native_observation_unavailable": native_unavailable,
            "product_index": tuple(sorted(product_index, key=lambda row: (row["task_id"], row["output_id"]))),
            "typed_product_validation": ("DEFERRED" if not decode_products else
                RAW_BYTES_CONSUMER_JOIN_DEFERRED if any(
                    resolve_storage_codec(plane.validators.binary_codecs, payload_schema=value.logical.payload_schema,
                        profile=value.logical.profile, media_type=value.logical.media_type) is not None for value in outputs.values())
                else "COMPLETE")}


def read_recursive_products(*, plane, plan, index, external_inputs, output_codecs,
                            decode_products=True, allow_partial=False, _read_policy=None,
                            original_input_access=None):
    """Authenticate the complete frozen task census and all completed byte products.

    Scientific negatives are products of operationally successful tasks. Missing
    products retain their recovery dispositions; no native runner is constructed.
    """
    index.validate_plan(plan)
    if original_input_access is not None:
        original_input_access.require_current()
    store = ExternalTaskReceiptStore(plane)
    recovery = ExternalRunRecoveryStore(plane)
    if original_input_access is None:
        retained_index = recovery.read_index(index.index_relative_path, expected_schema=index.SCHEMA)
        terminal = recovery.read_terminal(index)
    else:
        from empirical_lawhood.infrastructure.recovery import (
            RunRecoveryError, decode_run_recovery_index, decode_run_recovery_terminal_event,
        )
        raw = _original_recovery_payload(recovery, index.index_relative_path, schema=index.SCHEMA,
            maximum_bytes=plane.custody_limits.recovery_index_bytes, original_input_access=original_input_access)
        if raw is None:
            raise RunRecoveryError('run recovery index is missing')
        retained_index = decode_run_recovery_index(raw, maximum_bytes=plane.custody_limits.recovery_index_bytes)
        recovery._validate_index_limits(retained_index)
        raw = _original_recovery_payload(recovery, index.terminal_event_relative_path,
            schema=index.terminal_event_schema, maximum_bytes=plane.custody_limits.recovery_index_bytes,
            original_input_access=original_input_access)
        terminal = None if raw is None else decode_run_recovery_terminal_event(raw,
            maximum_bytes=plane.custody_limits.recovery_index_bytes)
        if terminal is not None and (terminal.recovery_index != ObjectIdentity.from_record(index.recovery_index_id, index)
                or terminal.run_id != index.run_id):
            raise RunRecoveryError('run recovery terminal event differs from its index')
    if retained_index != index:
        raise ValueError("recursive retained recovery index changes its exact assigned census")
    if terminal is None and not allow_partial:
        raise ValueError("recursive result lacks its complete operational terminal; inspect partial receipts "
                         "and native-contact custody before any continuation")
    external_by_id = {value.logical.logical_artifact_id: value for value in external_inputs}
    if terminal is None:
        operational_census, recovery_events, attempt_receipts, summaries = _partial_operational_census(
            recovery=recovery, store=store, plan=plan, index=index, original_input_access=original_input_access)
    else:
        operational_census, recovery_events, attempt_receipts = _operational_census(
            recovery=recovery, store=store, plan=plan, index=index, terminal=terminal,
            decode_products=decode_products, allow_partial=allow_partial, _read_policy=_read_policy,
            original_input_access=original_input_access)
        summaries = {}
        for value in terminal.attempts:
            if value.task_id not in summaries or value.ordinal > summaries[value.task_id].ordinal:
                summaries[value.task_id] = value
    return _assemble_read_products(plane=plane, plan=plan, index=index, store=store,
        external_by_id=external_by_id, output_codecs=output_codecs, decode_products=decode_products,
        terminal=terminal, summaries=summaries, allow_partial=allow_partial, operational_census=operational_census,
        recovery_events=recovery_events, attempt_receipts=attempt_receipts, issued=False,
        _read_policy=_read_policy, original_input_access=original_input_access)


def iter_recursive_product_records(*, plane, products, output_codecs):
    """Strictly decode authenticated products one at a time without retaining them.

    The consumer controls whether to retain a yielded record. A scientific
    projection requiring several full records must account for that additional
    memory; compact custody is not an independent scientific assessment.
    """
    for row in products["product_index"]:
        manifest = products["outputs"][row["logical_artifact_id"]]
        plane.verify_manifest(manifest)
        if resolve_storage_codec(plane.validators.binary_codecs, payload_schema=manifest.logical.payload_schema,
                profile=manifest.logical.profile, media_type=manifest.logical.media_type) is not None:
            continue  # Exact raw arrays are consumed with their typed manifest through anonymous ports.
        raw = read_bounded_bytes(plane.root.resolve(row["relative_path"], for_write=False),
                                 maximum_bytes=row["size_bytes"])
        if len(raw) != row["size_bytes"] or sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("recursive scientific bytes changed before their lazy typed read")
        codec = output_codecs.get(row["schema"])
        if codec is None:
            raise ValueError("recursive output lacks its registered strict record codec")
        record = decode_canonical_bytes(raw, codec, maximum_bytes=row["size_bytes"])
        del raw
        yield row["task_id"], row["output_id"], record
        del record


def _execution_operational_census(*, recovery, store, plan, index, terminal, _recovery_controls=None):
    """Read all frozen candidates, retaining failure diagnostics independently."""
    from empirical_lawhood.infrastructure.recovery import (
        _can_batch_recovery_controls, _reconcile_recovery_control_batch,
    )
    from empirical_lawhood.runtime.execution import TaskBlockKind, TaskBlockReason
    from empirical_lawhood.runtime.recovery import TaskRecoveryEvent

    if _recovery_controls is None and _can_batch_recovery_controls(recovery, store, index):
        return _reconcile_recovery_control_batch(recovery, store, index,
            lambda controls: _execution_operational_census(recovery=recovery, store=store,
                plan=plan, index=index, terminal=terminal, _recovery_controls=controls))
    if _recovery_controls is not None:
        _recovery_controls.require_open(recovery, store, index)

    summaries = {row.attempt_id: row for row in terminal.attempts}
    if len(summaries) != len(terminal.attempts):
        raise ValueError("recursive terminal duplicates an attempt identity")
    # Immutable reference indices are local to this verified custody read.
    # Preserve original per-task order and retain every diagnostic row.
    task_summaries = {}
    for row in terminal.attempts:
        task_summaries.setdefault(row.task_id, []).append(row)
    consumed = set()
    events, attempt_receipts = {}, {}
    tasks = {task.task_id: task for task in plan.tasks}
    indexed_tasks = {binding.task_id for binding in index.tasks}
    candidate_ids = {candidate.attempt_id for binding in index.tasks for candidate in binding.attempts}
    nonattempts = tuple(row for row in terminal.attempts if row.attempt_id not in candidate_ids)
    for row in nonattempts:
        if (row.task_id not in tasks or row.task_id not in indexed_tasks or row.disposition.value != "BLOCKED"
            or type(row.ordinal) is not int or row.ordinal <= 0
            or row.attempt_id != f"{index.run_id}.{row.task_id}.block-{row.ordinal:03d}"
            or row.receipt_id is not None or row.receipt_sha256 is not None
            or store.read(index.run_id, row.task_id, row.attempt_id) is not None):
            raise ValueError("recursive terminal changes its exact nonattempt identity or receipt")
    nonattempt_ordinals = {}
    for row in nonattempts:
        nonattempt_ordinals.setdefault(row.task_id, []).append(row.ordinal)
    for ordinals in nonattempt_ordinals.values():
        ordinals.sort()
    for task_id in tasks:
        ordinals = tuple(sorted(row.ordinal for row in task_summaries.get(task_id, ())))
        if ordinals != tuple(range(1, len(ordinals) + 1)):
            raise ValueError("recursive terminal changes its contiguous operational attempt ordinals")
    for binding in index.tasks:
        for candidate in binding.attempts:
            if _recovery_controls is None:
                receipt = store.read(index.run_id, binding.task_id, candidate.attempt_id)
                event = recovery.read_event(index, candidate.event_relative_path)
            else:
                receipt = _recovery_controls.receipts[binding.task_id, candidate.attempt_id]
                event = _recovery_controls.events[candidate.event_relative_path]
            summary = summaries.get(candidate.attempt_id)
            if summary is None:
                if receipt is not None or event is not None:
                    raise ValueError("recursive terminal omits a retained attempt")
                continue
            consumed.add(summary.attempt_id)
            # Candidate/event ordinals count entered attempts; the terminal also
            # counts earlier nonattempt blocks retained across explicit resumes.
            prior_blocks = bisect_left(nonattempt_ordinals.get(binding.task_id, ()), summary.ordinal)
            if (summary.task_id != binding.task_id or summary.ordinal != candidate.ordinal + prior_blocks
                or event is None or event.task_id != binding.task_id
                or event.attempt_id != candidate.attempt_id or event.attempt_ordinal != candidate.ordinal):
                raise ValueError("recursive terminal changes its exact attempt identity or ordinal")
            if summary.disposition.value == "SUCCEEDED":
                if receipt is None:
                    raise ValueError("recursive terminal lacks its completed receipt")
                ExternalRunRecoveryStore._validate_receipt_static(index, tasks[binding.task_id], candidate, receipt)
                expected_event = (TaskRecoveryEvent.from_receipt(index, receipt) if _recovery_controls is None
                    else _recovery_controls.receipt_event(receipt))
                if (receipt.receipt_id != summary.receipt_id or receipt.fingerprint() != summary.receipt_sha256
                    or event != expected_event):
                    raise ValueError("recursive terminal changes its exact receipt or recovery event")
                attempt_receipts[summary.attempt_id] = receipt
            elif (receipt is not None or event is None or event.disposition.value != summary.disposition.value
                  or event.reason_codes != (summary.reason_code,)):
                raise ValueError("recursive failed or blocked attempt lacks its exact recovery event")
            events[summary.attempt_id] = event
        nonattempt = (recovery.read_event(index, binding.nonattempt_event_relative_path)
            if _recovery_controls is None else _recovery_controls.events[binding.nonattempt_event_relative_path])
        if nonattempt is not None:
            matches = tuple(row for row in task_summaries.get(binding.task_id, ())
                            if row.disposition.value == "BLOCKED" and row.reason_code == nonattempt.reason_codes[0]
                            and row.attempt_id not in consumed)
            if len(matches) != 1:
                raise ValueError("recursive terminal omits or ambiguously owns a nonattempt event")
            row = matches[0]
            if (row.attempt_id != f"{index.run_id}.{binding.task_id}.block-{row.ordinal:03d}"
                or nonattempt.task_id != binding.task_id or nonattempt.attempt_id is not None
                or nonattempt.attempt_ordinal is not None or nonattempt.disposition.value != "NOT_ATTEMPTED"):
                raise ValueError("recursive terminal changes its exact nonattempt identity or ordinal")
            consumed.add(matches[0].attempt_id)
            events[matches[0].attempt_id] = nonattempt
    for row in nonattempts:
        if row.attempt_id in consumed:
            continue
        try:
            reason = TaskBlockReason(row.reason_code)
        except ValueError as error:
            raise ValueError("recursive terminal has an unknown nonattempt block reason") from error
        if reason.kind is not TaskBlockKind.RETRYABLE:
            raise ValueError("recursive durable nonattempt lacks its exact recovery event")
        # Retryable block observations are owned by the authenticated terminal.
        # They consume no frozen executable candidate and have no invented event.
        consumed.add(row.attempt_id)
    if consumed != set(summaries):
        raise ValueError("recursive terminal contains an unauthenticated attempt")
    rows = tuple({"task_id": row.task_id, "attempt_id": row.attempt_id, "ordinal": row.ordinal,
                  "operational_status": row.disposition.value, "reason_code": row.reason_code,
                  "receipt_id": row.receipt_id, "receipt_sha256": row.receipt_sha256,
                  "recovery_event": (events[row.attempt_id].to_document()
                                     if row.attempt_id in events else None),
                  "recovery_event_status": ("AUTHENTICATED" if row.attempt_id in events
                                            else "MISSING_TERMINAL_PRIMARY_NONATTEMPT"),
                  "actual_cpu_seconds": None, "actual_wall_seconds": None, "actual_peak_rss_bytes": None}
                 for row in terminal.attempts)
    return rows, events, attempt_receipts

def read_execution_products(*, plane, plan, index, external_inputs, output_codecs,
                            decode_products=True, _read_policy=None):
    """Bounded exact original plan/receipt custody; caller owns issue/reveal.

    Unlike the historical DEV reader this route derives every output lane from
    the exact supported frozen issued plan. A failed terminal retains every
    assigned task and actual attempt event; missing outputs are never success.
    """
    from empirical_lawhood.runtime.plans import ExecutionPlan
    from empirical_lawhood.runtime.recovery import RunRecoveryIndex
    if type(plan) is not ExecutionPlan or type(index) is not RunRecoveryIndex:
        raise TypeError("issued product custody requires exact supported plan/index records")
    allow_partial=False
    index.validate_plan(plan)
    store = ExternalTaskReceiptStore(plane)
    recovery = ExternalRunRecoveryStore(plane)
    retained_index = recovery.read_index(index.index_relative_path, expected_schema=index.SCHEMA)
    if retained_index != index:
        raise ValueError("recursive retained recovery index changes its exact assigned census")
    terminal = recovery.read_terminal(index)
    if terminal is None and not allow_partial:
        raise ValueError("recursive result lacks its complete operational terminal; inspect partial receipts "
                         "and native-contact custody before any continuation")
    external_by_id = {value.logical.logical_artifact_id: value for value in external_inputs}
    if terminal is None:
        operational_census, recovery_events, attempt_receipts, summaries = _partial_operational_census(
            recovery=recovery, store=store, plan=plan, index=index)
    else:
        operational_census, recovery_events, attempt_receipts = _execution_operational_census(
            recovery=recovery, store=store, plan=plan, index=index, terminal=terminal)
        summaries = {}
        for value in terminal.attempts:
            if value.task_id not in summaries or value.ordinal > summaries[value.task_id].ordinal:
                summaries[value.task_id] = value
    return _assemble_read_products(plane=plane, plan=plan, index=index, store=store,
        external_by_id=external_by_id, output_codecs=output_codecs, decode_products=decode_products,
        terminal=terminal, summaries=summaries, allow_partial=allow_partial, operational_census=operational_census,
        recovery_events=recovery_events, attempt_receipts=attempt_receipts, issued=True,
        _read_policy=_read_policy)
