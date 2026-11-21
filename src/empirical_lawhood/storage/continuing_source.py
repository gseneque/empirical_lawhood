# SPDX-License-Identifier: MPL-2.0
"""Continuing-source custody composed over the existing guarded artifact plane."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256

from empirical_lawhood.science.inquiry.continuing_source import MAX_LIVE_RECORD_BYTES, ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveBoundaryKind, LiveEffectReceipt, LiveEffectStage, LiveEventSegment, LiveObservation, LiveSessionBoundary
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.continuing_source import LiveObservationPacket, require_live_payload
from empirical_lawhood.execution.native_effects import NativeEffectContact

from empirical_lawhood.storage.artifacts import ExternalArtifactPlane
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_locks import exclusive_file_lock
from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore


class ExternalContinuingSourceStore:
    """Immutable bounded segments; the catalogue is never the primary history.

Only a new session can acquire live ownership. After owner loss, historical
inspection and actual-effect reconciliation remain possible; old bytes grant
no resumed lease or effect entry. Source reattachment needs a new generation
and the original dependence root in a separately authored session.
    """

    def __init__(self, *, plane: ExternalArtifactPlane, session: ContinuingSourceSession,
                 relative_root: str, minimum_free_bytes: int = 0):
        if type(session) is not ContinuingSourceSession or not isinstance(plane, ExternalArtifactPlane):
            raise TypeError("continuing source requires existing guarded artifact custody")
        validate_relative_locator(relative_root)
        if type(minimum_free_bytes) is not int or minimum_free_bytes < 0:
            raise ValueError("continuing source free-space floor must be nonnegative")
        self.plane, self.session = plane, session
        self.relative_root = relative_root.rstrip('/') + '/' + sha256(session.session_id.encode()).hexdigest()
        self.minimum_free_bytes = minimum_free_bytes
        self._live_owner = False
        self._contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=session.identity,
            visibility_ceiling=session.visibility, outcome_access=session.outcome_access,
            minimum_free_bytes=minimum_free_bytes)

    def _path(self, relative, *, write=False):
        return self.plane.root.resolve(self.relative_root + '/' + relative, for_write=write,
            operation_minimum_free_bytes=self.minimum_free_bytes)

    @staticmethod
    def _token(value):
        validate_stable_id(value)
        if len(value) > 512:
            raise ValueError("live custody identifier exceeds its bound")
        return sha256(value.encode()).hexdigest()

    def _record_path(self, reference):
        return 'records/' + self._token(reference.object_id) + '.json'

    def _owner(self):
        if not self._live_owner:
            raise PermissionError("historical custody grants no continuing-source ownership")

    @contextmanager
    def owner_lock(self):
        if self._live_owner:
            raise PermissionError("continuing source owner cannot be acquired twice")
        path = self._path('owner.lock', write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path = self._path('owner.lock', write=True)
        with exclusive_file_lock(path, blocking=False):
            self._live_owner = True
            try:
                yield
            finally:
                self._live_owner = False

    def _exists(self, relative):
        # A member with only one half of its publication must reach the guarded
        # reader and fail. It must never be mistaken for an absent operation.
        path, sidecar = self._path(relative), self._path(relative + '.manifest.json')
        return path.exists() or path.is_symlink() or sidecar.exists() or sidecar.is_symlink()

    def _parents(self):
        return (ArtifactLineageParent(self.session.identity, self.session.visibility, self.session.outcome_access),)

    def _publish(self, relative, reference, raw, *, session_record=False):
        if type(raw) is not bytes or not 0 < len(raw) <= MAX_LIVE_RECORD_BYTES:
            raise ValueError("live custody record exceeds its explicit byte bound")
        if sha256(raw).hexdigest() != reference.object_fingerprint:
            raise ValueError("live custody bytes substitute the original identity")
        parents = () if session_record else self._parents()
        result = self.plane.write(ArtifactWriteRequest(
            logical_artifact_id='live.' + self._token(self.session.session_id) + '.' + self._token(reference.object_id),
            relative_path=self.relative_root + '/' + relative, payload_schema=reference.object_schema,
            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json',
            publication_scope_id='live.' + self._token(self.session.session_id),
            publication_scope_relative_root=self.relative_root, payload=raw,
            visibility_ceiling=self.session.visibility,
            parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
            outcome_access=self.session.outcome_access, lineage_parents=parents,
            minimum_free_bytes=self.minimum_free_bytes))
        if self._read_raw(relative, reference, session_record=session_record) != raw:
            raise ValueError("live publication did not survive exact custody verification")
        return result

    def _read_raw(self, relative, reference=None, *, session_record=False):
        manifest = self.plane.read_manifest(self.relative_root + '/' + relative)
        if (manifest.materialization.relative_path != self.relative_root + '/' + relative
                or not 0 < manifest.materialization.size_bytes <= MAX_LIVE_RECORD_BYTES
                or manifest.logical.payload_schema != (reference.object_schema if reference else manifest.logical.payload_schema)
                or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or manifest.logical.media_type != 'application/json'
                or manifest.logical.visibility_ceiling is not self.session.visibility
                or manifest.logical.outcome_access is not self.session.outcome_access
                or manifest.logical.lineage_parents != (() if session_record else self._parents())):
            raise ValueError("live manifest changes original path, scope, schema or byte bounds")
        if reference is not None and manifest.logical.logical_artifact_id != (
                'live.' + self._token(self.session.session_id) + '.' + self._token(reference.object_id)):
            raise ValueError("live manifest changes original logical record identity")
        self.plane.verify_manifest(manifest)
        raw = read_bounded_bytes(self._path(relative), maximum_bytes=MAX_LIVE_RECORD_BYTES)
        digest = sha256(raw).hexdigest()
        if (len(raw) != manifest.materialization.size_bytes or digest != manifest.logical.content_sha256
                or digest != manifest.materialization.physical_sha256
                or (reference is not None and digest != reference.object_fingerprint)):
            raise ValueError("live bytes differ from their authenticated original member")
        return raw

    def _read(self, relative, record_type):
        raw = self._read_raw(relative)
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=MAX_LIVE_RECORD_BYTES)
        return record

    def initialize(self, package: ObjectIdentity, payload: bytes):
        self._owner()
        if self._exists('session.json'):
            raise PermissionError("retained session is historical; it grants no renewed source owner")
        result = self._publish('session.json', self.session.identity, self.session.canonical_bytes(), session_record=True)
        if result.created is not True:
            raise PermissionError("only the creating session owner may enter")
        self.publish_package(package, payload)

    def authenticate_session(self):
        raw = self._read_raw('session.json', self.session.identity, session_record=True)
        if decode_canonical_bytes(raw, ContinuingSourceSession, maximum_bytes=MAX_LIVE_RECORD_BYTES) != self.session:
            raise ValueError("retained continuing session differs from its original contract")

    def publish_package(self, package, payload):
        self._owner()
        require_live_payload(package, payload)
        self._publish(self._record_path(package), package, payload)

    def publish_boundary(self, boundary, selected=None):
        self._owner()
        if (type(boundary) is not LiveSessionBoundary or boundary.session != self.session.identity
                or boundary.index > self.session.maximum_segments):
            raise ValueError("live lifecycle boundary changes its original session or bound")
        if selected is not None:
            if type(selected) is not LiveActorLease or selected.identity != boundary.selected:
                raise ValueError("actor lifecycle boundary changes its original lease record")
            self._publish(self._record_path(selected.identity), selected.identity, selected.canonical_bytes())
        if boundary.selected is not None:
            self._read_raw(self._record_path(boundary.selected), boundary.selected)
        self._publish(f'boundaries/{boundary.index:04}.json',
            ObjectIdentity.from_record(f'boundary.{self.session.session_id}.{boundary.index}', boundary), boundary.canonical_bytes())

    def publish_segment(self, segment, packets):
        self._owner()
        if (type(segment) is not LiveEventSegment or segment.session != self.session.identity
                or segment.index > self.session.maximum_segments
                or len(segment.events) > self.session.events_per_segment
                or type(packets) is not tuple or any(type(value) is not LiveObservationPacket for value in packets)
                or tuple(packet.observation for packet in packets) != segment.events):
            raise ValueError("source segment changes its original bounded event census")
        if segment.previous is not None:
            previous = self.read_segment(segment.index - 1)
            if previous.identity != segment.previous or previous.events[-1].sequence != segment.previous_sequence:
                raise ValueError("source segment loses its original immediate predecessor")
        for packet in packets:
            event = packet.observation
            self._read_raw(self._record_path(event.actor_lease), event.actor_lease)
            self._publish(self._record_path(event.payload), event.payload, packet.payload)
            self._publish(self._record_path(event.identity), event.identity, event.canonical_bytes())
        # The segment is the completion manifest of this bounded event census.
        # Partial earlier publications never enter an actor's memory.
        self._publish(f'segments/{segment.index:04}.json', segment.identity, segment.canonical_bytes())

    def read_segment(self, index):
        if type(index) is not int or not 1 <= index <= self.session.maximum_segments:
            raise ValueError("source segment read exceeds its original capacity")
        self.authenticate_session()
        segment = self._read(f'segments/{index:04}.json', LiveEventSegment)
        if (segment.index != index or segment.session != self.session.identity
                or len(segment.events) > self.session.events_per_segment):
            raise ValueError("source segment substitutes original index, session or capacity")
        self._read_raw(f'segments/{index:04}.json', segment.identity)
        for event in segment.events:
            original = self._read_raw(self._record_path(event.identity), event.identity)
            if decode_canonical_bytes(original, LiveObservation, maximum_bytes=MAX_LIVE_RECORD_BYTES) != event:
                raise ValueError("source segment changes an original event")
            self._read_raw(self._record_path(event.actor_lease), event.actor_lease)
            require_live_payload(event.payload, self._read_raw(self._record_path(event.payload), event.payload))
        return segment

    def read_event_window(self, first: int, count: int):
        """Owner/evaluator read; no actor handle receives this historical port."""
        if (type(first) is not int or type(count) is not int or first < 1
                or not 0 < count <= 16 or first + count - 1 > self.session.maximum_segments):
            raise ValueError("historical event read requires at most sixteen bounded segments")
        segments, missing = [], []
        predecessor = self.read_segment(first - 1) if first > 1 else None
        for index in range(first, first + count):
            if not self._exists(f'segments/{index:04}.json'):
                missing.append(index)
                predecessor = None
                continue
            segment = self.read_segment(index)
            if index > 1 and (predecessor is None or segment.previous != predecessor.identity
                    or segment.previous_sequence != predecessor.events[-1].sequence):
                raise ValueError("retained source event history has a missing or changed predecessor")
            segments.append(segment)
            predecessor = segment
        return {'segments': tuple(segments), 'missing_segment_indices': tuple(missing),
            'sequence_gaps': tuple(gap for segment in segments for gap in segment.gaps),
            'complete_selected_window': not missing and not any(segment.gaps for segment in segments),
            'whole_session_complete': False}

    def _operation_path(self, request_id):
        return 'operations/' + self._token(request_id) + '.json'

    def publish_operation(self, operation, prepared_payload):
        self._owner()
        if (type(operation) is not FiniteLiveOperation or operation.window.session != self.session.identity
                or operation.window.dependence_root != self.session.dependence_root):
            raise ValueError("live operation changes original source or dependence root")
        require_live_payload(operation.prepared_commitment, prepared_payload)
        self._read_raw(self._record_path(operation.package), operation.package)
        self._read_raw(self._record_path(operation.actor_lease.identity), operation.actor_lease.identity)
        for original in operation.inputs:
            self._read_raw(self._record_path(original), original)
        self._publish(self._record_path(operation.prepared_commitment), operation.prepared_commitment, prepared_payload)
        self._publish(self._operation_path(operation.request_id), operation.identity, operation.canonical_bytes())

    def read_operation(self, request_id):
        self.authenticate_session()
        relative = self._operation_path(request_id)
        if not self._exists(relative):
            return None
        operation = self._read(relative, FiniteLiveOperation)
        if (operation.request_id != request_id or operation.window.session != self.session.identity
                or operation.window.dependence_root != self.session.dependence_root):
            raise ValueError("retained operation changes original request, session or dependence root")
        self._read_raw(relative, operation.identity)
        for reference in (operation.package, operation.prepared_commitment, operation.actor_lease.identity, *operation.inputs):
            self._read_raw(self._record_path(reference), reference)
        for reference in operation.inputs:
            event = decode_canonical_bytes(self._read_raw(self._record_path(reference), reference), LiveObservation,
                maximum_bytes=MAX_LIVE_RECORD_BYTES)
            if event.actor_lease != operation.actor_lease.identity or event.session != self.session.identity:
                raise ValueError("retained operation input belongs to another actor or source")
            require_live_payload(event.payload, self._read_raw(self._record_path(event.payload), event.payload))
        return operation

    def _contact(self, operation):
        references = [operation.package, operation.prepared_commitment, operation.actor_lease.identity, *operation.inputs]
        for reference in operation.inputs:
            event = decode_canonical_bytes(self._read_raw(self._record_path(reference), reference), LiveObservation,
                maximum_bytes=MAX_LIVE_RECORD_BYTES)
            references.append(event.payload)
        manifests = tuple(self.plane.read_manifest(self.relative_root + '/' + self._record_path(reference)) for reference in references)
        return NativeEffectContact(operation.run_id, operation.request_id, 'live.attempt-001',
            self.session.identity, operation.identity, operation.implementation_commit,
            tuple(sorted({manifest.materialization.materialization_id for manifest in manifests})), ())

    def begin_contact(self, operation):
        self._owner()
        if self.read_operation(operation.request_id) != operation:
            raise ValueError("effect contact has no exact durable original commitment")
        self._contacts.begin(self._contact(operation))

    def retire_contact(self, operation):
        self._contacts.retire_live_creator(self._contact(operation))

    def has_contact(self, operation):
        contact = self._contacts.read(operation.run_id, operation.request_id)
        if contact is None:
            return False
        if contact != self._contact(operation):
            raise ValueError("live effect contact substitutes original inputs, package or operation")
        return True

    def _effect_path(self, request_id, stage):
        return f'effects/{self._token(request_id)}/{stage.value.lower()}.json'

    def _validate_receipt(self, operation, receipt):
        if type(receipt) is not LiveEffectReceipt or receipt.operation != operation.identity:
            raise ValueError("live effect receipt substitutes its original operation")
        committed = self.session.coordinate(operation.committed_at)
        if receipt.accepted_at is not None and self.session.coordinate(receipt.accepted_at) < committed:
            raise ValueError("native command acceptance precedes its retained commitment")
        if receipt.applied_at is not None and not (
                self.session.coordinate(operation.application_not_before) <= self.session.coordinate(receipt.applied_at)
                < self.session.coordinate(operation.action_expires_at)):
            raise ValueError("native application lies outside its original effect expiry")

    @staticmethod
    def _advance(previous, current):
        if previous is None or previous == current:
            return
        changed = any(getattr(previous, name) is not None and getattr(previous, name) != getattr(current, name)
            for name in ('accepted_at', 'applied_at', 'observed_at', 'result'))
        if previous.stage in (LiveEffectStage.OBSERVED, LiveEffectStage.REFUSED) or changed:
            raise ValueError("live effect reconciliation rewrites an original known outcome")

    def read_effect(self, operation):
        current = None
        for stage in (LiveEffectStage.ACCEPTED, LiveEffectStage.APPLIED, LiveEffectStage.OBSERVED, LiveEffectStage.REFUSED):
            relative = self._effect_path(operation.request_id, stage)
            if self._exists(relative):
                receipt = self._read(relative, LiveEffectReceipt)
                if receipt.stage is not stage:
                    raise ValueError("live receipt substitutes its original stage path")
                self._validate_receipt(operation, receipt)
                reference = ObjectIdentity.from_record('effect.' + self._token(operation.request_id) + '.' + stage.value.lower(), receipt)
                self._read_raw(relative, reference)
                self._advance(current, receipt)
                if receipt.result is not None:
                    require_live_payload(receipt.result, self._read_raw(self._record_path(receipt.result), receipt.result))
                current = receipt
        return current

    def publish_effect(self, operation, receipt, result_payload):
        if self.read_operation(operation.request_id) != operation or not self.has_contact(operation):
            raise ValueError("effect reconciliation lacks original commitment and possible-contact custody")
        self._validate_receipt(operation, receipt)
        lock = self._path('effects/' + self._token(operation.request_id) + '/reconcile.lock', write=True)
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock = self._path('effects/' + self._token(operation.request_id) + '/reconcile.lock', write=True)
        with exclusive_file_lock(lock):
            self._advance(self.read_effect(operation), receipt)
            if receipt.result is not None:
                require_live_payload(receipt.result, result_payload)
                self._publish(self._record_path(receipt.result), receipt.result, result_payload)
            elif result_payload is not None:
                raise ValueError("unobserved effect supplied an unbound result body")
            reference = ObjectIdentity.from_record('effect.' + self._token(operation.request_id) + '.' + receipt.stage.value.lower(), receipt)
            self._publish(self._effect_path(operation.request_id, receipt.stage), reference, receipt.canonical_bytes())

    def read_actor_lease(self, reference):
        """Read an original lease as history; never create a live actor handle."""
        if type(reference) is not ObjectIdentity or reference.object_schema != LiveActorLease.SCHEMA:
            raise ValueError("historical actor selection requires an exact lease identity")
        self.authenticate_session()
        raw = self._read_raw(self._record_path(reference), reference)
        lease = decode_canonical_bytes(raw, LiveActorLease, maximum_bytes=MAX_LIVE_RECORD_BYTES)
        if lease.identity != reference or lease.session != self.session.identity:
            raise ValueError("historical actor lease changes its original session or identity")
        return lease

    def read_boundaries(self, first: int, count: int):
        if (type(first) is not int or type(count) is not int or first < 1
                or not 0 < count <= 16 or first + count - 1 > self.session.maximum_segments):
            raise ValueError("lifecycle read requires at most sixteen bounded boundaries")
        self.authenticate_session()
        values = []
        for index in range(first, first + count):
            relative = f'boundaries/{index:04}.json'
            if not self._exists(relative):
                break
            boundary = self._read(relative, LiveSessionBoundary)
            if boundary.index != index or boundary.session != self.session.identity:
                raise ValueError("lifecycle boundary substitutes its original session or index")
            reference = ObjectIdentity.from_record(f'boundary.{self.session.session_id}.{index}', boundary)
            self._read_raw(relative, reference)
            if boundary.kind is LiveBoundaryKind.ACTOR:
                self.read_actor_lease(boundary.selected)
            elif boundary.selected is not None:
                self._read_raw(self._record_path(boundary.selected), boundary.selected)
            values.append(boundary)
        return tuple(values)

    def retained_disposition(self):
        """Finite metadata scan; an unclosed source is never silently complete."""
        for first in range(1, self.session.maximum_segments + 1, 16):
            values = self.read_boundaries(first, min(16, self.session.maximum_segments - first + 1))
            if any(value.kind is LiveBoundaryKind.RETENTION_LOSS for value in values):
                return 'UNEVALUABLE_EVENT_HISTORY'
            if any(value.kind is LiveBoundaryKind.CLOSED for value in values):
                return 'CLOSED_NOT_SCIENTIFICALLY_ASSESSED'
            if len(values) < 16:
                break
        return 'UNCLOSED_OR_OWNER_LOST_UNEVALUABLE'
