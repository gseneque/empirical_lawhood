# SPDX-License-Identifier: MPL-2.0
"""One continuing-source owner with bounded, separately authorized actor ports.

This trusted in-process boundary is not a sandbox for arbitrary Python. Actor
ports have no historical-store reader. Native adapters must enforce the same
generation and expiry guard at actual application, including queued commands.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
from fractions import Fraction
from threading import RLock
from typing import Callable, Protocol

from empirical_lawhood.science.inquiry.continuing_source import MAX_LIVE_PAYLOAD_BYTES, ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveBoundaryKind, LiveEffectReceipt, LiveEventSegment, LiveObservation, LiveSessionBoundary, source_sequence_gaps
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.models.time import ClockCoordinate, InformationCutoff


class LiveRetentionLost(RuntimeError):
    """The external source may continue; this session cannot support new science."""


class LiveBackpressure(RuntimeError):
    """No unbounded queue is created; dropped source sequences must remain gaps."""


@dataclass(frozen=True, slots=True)
class LiveObservationPacket:
    observation: LiveObservation
    payload: bytes

    def __post_init__(self):
        if type(self.observation) is not LiveObservation:
            raise TypeError("source packet requires the exact observation contract")
        require_live_payload(self.observation.payload, self.payload)


def require_live_payload(reference: ObjectIdentity, payload: bytes) -> None:
    if (type(reference) is not ObjectIdentity or type(payload) is not bytes
            or not 0 < len(payload) <= MAX_LIVE_PAYLOAD_BYTES
            or sha256(payload).hexdigest() != reference.object_fingerprint):
        raise ValueError("live domain payload differs from its bounded original bytes")
    # Domain schemas remain with their decoder. The generic boundary checks the
    # exact envelope, without importing a domain or selecting executable code.
    from empirical_lawhood.science.records.serialization import canonical_json_bytes
    import json
    document = json.loads(payload)
    if (not isinstance(document, dict) or set(document) != {"schema", "version", "value"}
            or (document["schema"], document["version"]) != (reference.object_schema, reference.object_version)
            or canonical_json_bytes(document) != payload):
        raise ValueError("live payload is not its exact canonical domain document")


class ContinuingSourceCustody(Protocol):
    """The lifecycle owner alone receives this historical and effect-custody port."""

    def initialize(self, package: ObjectIdentity, payload: bytes) -> None: ...
    def publish_package(self, package: ObjectIdentity, payload: bytes) -> None: ...
    def publish_boundary(self, boundary: LiveSessionBoundary, selected: CanonicalRecord | None = None) -> None: ...
    def publish_segment(self, segment: LiveEventSegment, packets: tuple[LiveObservationPacket, ...]) -> None: ...
    def publish_operation(self, operation: FiniteLiveOperation, prepared_payload: bytes) -> None: ...
    def read_operation(self, request_id: str) -> FiniteLiveOperation | None: ...
    def has_contact(self, operation: FiniteLiveOperation) -> bool: ...
    def begin_contact(self, operation: FiniteLiveOperation) -> None: ...
    def retire_contact(self, operation: FiniteLiveOperation) -> None: ...
    def read_effect(self, operation: FiniteLiveOperation) -> LiveEffectReceipt | None: ...
    def publish_effect(self, operation: FiniteLiveOperation, receipt: LiveEffectReceipt, result_payload: bytes | None) -> None: ...


class LiveSourceAccess(Protocol):
    """Actual current source/access authority remains with the injected owner."""

    def require_owner(self, session: ContinuingSourceSession) -> None: ...
    def require_actor(self, lease: LiveActorLease, *, effect_key: str | None) -> None: ...


class LiveEffectPort(Protocol):
    """Source-owned finite submission and separate read-only reconciliation.

``submit`` must check current native generations/expiry immediately before
application, using ``require_live_application``. A timeout never grants retry.
``observe`` can inspect the original command, but must never submit it again.
    """

    def submit(self, operation: FiniteLiveOperation, prepared_payload: bytes) -> tuple[LiveEffectReceipt, bytes | None]: ...
    def observe(self, operation: FiniteLiveOperation) -> tuple[LiveEffectReceipt, bytes | None] | None: ...


def require_live_application(operation: FiniteLiveOperation, *, session: ContinuingSourceSession,
                             current_lease: LiveActorLease, at: ClockCoordinate) -> None:
    """Apply on the native side after a queue or delay, not only at submission."""
    if (operation.window.session != session.identity
            or operation.window.dependence_root != session.dependence_root
            or operation.actor_lease != current_lease
            or current_lease.session != session.identity):
        raise PermissionError("live application has a stale source, actor, connection, allocation or life generation")
    coordinate = session.coordinate(at)
    if not (session.coordinate(operation.application_not_before) <= coordinate
            < session.coordinate(operation.action_expires_at)
            and coordinate < session.coordinate(current_lease.expires_at)):
        raise PermissionError("live application is outside its original schedule or lease")


@dataclass(frozen=True, slots=True)
class LiveReadWindow:
    packets: tuple[LiveObservationPacket, ...]
    missing_sequences: tuple[int, ...]
    source_has_gaps: bool

    @property
    def complete(self):
        return not self.missing_sequences and not self.source_has_gaps


@dataclass(frozen=True, slots=True)
class LiveOperationReadout:
    operation: FiniteLiveOperation
    receipt: LiveEffectReceipt | None
    contacted: bool

    @property
    def disposition(self):
        if self.receipt is not None:
            return self.receipt.stage.value
        return "UNKNOWN_EFFECT_DO_NOT_REPEAT" if self.contacted else "COMMITTED_NOT_SUBMITTED"


class LiveActorHandle:
    """No store or evaluator-ledger API is exposed to the actor."""

    __slots__ = ("__owner", "__lease", "__token")

    def __init__(self, owner, lease, token):
        self.__owner, self.__lease, self.__token = owner, lease, token

    @property
    def lease(self):
        return self.__lease

    def read(self, sequences: tuple[int, ...], *, cutoff: InformationCutoff) -> LiveReadWindow:
        return self.__owner.read(self, self.__token, sequences, cutoff=cutoff)

    def execute(self, operation: FiniteLiveOperation, prepared_payload: bytes) -> LiveOperationReadout:
        return self.__owner.execute(self, self.__token, operation, prepared_payload)


class ContinuingSourceOwner:
    """Finite retention for a source whose process outlives individual requests.

An infrastructure owner lock must enclose the complete lifetime. A restarted
reader can inspect custody, but cannot regain a live owner from old records.
    """

    def __init__(self, *, session: ContinuingSourceSession, custody: ContinuingSourceCustody,
                 clock: Callable[[], ClockCoordinate], effect_ports: Mapping[str, LiveEffectPort],
                 current_access: LiveSourceAccess):
        if type(session) is not ContinuingSourceSession or not callable(clock):
            raise TypeError("continuing owner requires a typed session and actual clock")
        self.session, self._custody, self._clock = session, custody, clock
        if (not callable(getattr(current_access, 'require_owner', None))
                or not callable(getattr(current_access, 'require_actor', None))):
            raise TypeError("continuing source requires its actual current access owner")
        self._access = current_access
        if (not isinstance(effect_ports, Mapping) or len(effect_ports) > 32
                or any(not callable(getattr(port, 'submit', None)) or not callable(getattr(port, 'observe', None))
                       for port in effect_ports.values())):
            raise TypeError("source owner requires bounded code-owned submission and observation ports")
        for key in effect_ports:
            validate_stable_id(key)
        self._effect_ports = dict(effect_ports)
        self._lock = RLock()
        self._active = False
        self._retention_lost = False
        self._package = None
        self._actors: dict[str, tuple[LiveActorHandle, object]] = {}
        self._memory: dict[str, OrderedDict[int, LiveObservationPacket]] = {}
        self._last_segment: LiveEventSegment | None = None
        self._boundary_count = 0
        self._operation_count = 0
        self._inflight: dict[str, str] = {}
        self._source_has_gaps = False

    @property
    def scientific_disposition(self):
        if self._retention_lost or self._source_has_gaps:
            return "UNEVALUABLE_EVENT_HISTORY"
        return "NOT_ASSESSED" if self._active else "CLOSED_OR_NOT_STARTED"

    @property
    def last_event_sequence(self):
        return 0 if self._last_segment is None else self._last_segment.events[-1].sequence

    def start(self, package: ObjectIdentity, payload: bytes) -> None:
        with self._lock:
            if self._active or self._package is not None:
                raise ValueError("continuing owner has already started")
            self._access.require_owner(self.session)
            require_live_payload(package, payload)
            self._custody.initialize(package, payload)
            self._boundary(LiveBoundaryKind.PACKAGE, selected=package)
            self._package, self._active = package, True

    def _usable(self):
        if self._retention_lost:
            raise LiveRetentionLost("event retention failed; source continuation is not scientific completion")
        if not self._active:
            raise PermissionError("continuing source owner is not active")

    def _lost(self):
        self._retention_lost = True
        # The native lease/fallback owner remains responsible for control loss.
        # Storage loss cannot authorize a new, unretained fallback submission.
        try:
            self._boundary(LiveBoundaryKind.RETENTION_LOSS)
        except (OSError, ValueError, RuntimeError):
            pass

    def _boundary(self, kind, *, previous=None, selected=None, record=None):
        if self._boundary_count >= self.session.maximum_segments:
            raise LiveRetentionLost("session lifecycle boundary capacity is exhausted")
        boundary = LiveSessionBoundary(self.session.identity, self._boundary_count + 1,
            kind, self._clock(), self.last_event_sequence, previous, selected)
        self.session.coordinate(boundary.at)
        self._custody.publish_boundary(boundary, record)
        self._boundary_count += 1

    def bind_actor(self, lease: LiveActorLease) -> LiveActorHandle:
        with self._lock:
            self._usable()
            self._access.require_owner(self.session)
            if type(lease) is not LiveActorLease or lease.session != self.session.identity:
                raise PermissionError("actor lease belongs to another source session")
            if not set(lease.effect_keys) <= set(self._effect_ports):
                raise PermissionError("actor effect permission names no source-owned port")
            self._access.require_actor(lease, effect_key=None)
            if self.session.coordinate(lease.expires_at) <= self.session.coordinate(self._clock()):
                raise PermissionError("actor lease has already expired")
            prior = self._actors.get(lease.actor_id)
            if prior is None:
                if len(self._actors) >= self.session.maximum_actors:
                    raise ValueError("continuing source actor capacity is exhausted")
            else:
                old = prior[0].lease
                if (any(new < previous for new, previous in zip(lease.generations, old.generations, strict=True))
                        or lease.generations == old.generations):
                    raise PermissionError("actor replacement must advance an actual generation without reversal")
            try:
                self._boundary(LiveBoundaryKind.ACTOR,
                    previous=None if prior is None else prior[0].lease.identity, selected=lease.identity, record=lease)
            except (OSError, ValueError, RuntimeError):
                self._lost()
                raise
            token = object()
            handle = LiveActorHandle(self, lease, token)
            self._actors[lease.actor_id] = handle, token
            self._memory[lease.actor_id] = OrderedDict()
            return handle

    def replace_package(self, package: ObjectIdentity, payload: bytes) -> None:
        with self._lock:
            self._usable()
            self._access.require_owner(self.session)
            require_live_payload(package, payload)
            # Package bytes use the same exact bounded custody path as startup.
            # The custody owner exposes no live-owner renewal in this operation.
            try:
                self._custody.publish_package(package, payload)
                self._boundary(LiveBoundaryKind.PACKAGE, previous=self._package, selected=package)
            except (OSError, ValueError, RuntimeError):
                self._lost()
                raise
            self._package = package

    def _handle(self, handle, token):
        self._usable()
        selected = self._actors.get(handle.lease.actor_id)
        if selected is None or selected[0] is not handle or selected[1] is not token:
            raise PermissionError("actor handle is stale or belongs to another lifecycle owner")
        if self.session.coordinate(self._clock()) >= self.session.coordinate(handle.lease.expires_at):
            raise PermissionError("actor handle lease expired; native fallback owns control loss")
        self._access.require_actor(handle.lease, effect_key=None)
        return handle.lease

    def _evict(self, memory, lease, now):
        for sequence, packet in tuple(memory.items()):
            if self.session.coordinate(packet.observation.retain_until) <= now:
                del memory[sequence]
        while len(memory) > lease.maximum_observations:
            memory.popitem(last=False)
        # Derived values cannot provide an evaluator-ledger or memory backdoor.
        while True:
            available = {packet.observation.identity for packet in memory.values()}
            removed = tuple(sequence for sequence, packet in memory.items()
                if not set(packet.observation.derived_from) <= available)
            if not removed:
                break
            for sequence in removed:
                del memory[sequence]

    def ingest(self, packets: tuple[LiveObservationPacket, ...]) -> LiveEventSegment:
        if (type(packets) is not tuple or not 0 < len(packets) <= self.session.events_per_segment
                or any(type(packet) is not LiveObservationPacket for packet in packets)):
            raise ValueError("source ingest exceeds its one bounded batch")
        if not self._lock.acquire(blocking=False):
            raise LiveBackpressure("source owner is busy; no unbounded input queue was created")
        try:
            self._usable()
            self._access.require_owner(self.session)
            index = 1 if self._last_segment is None else self._last_segment.index + 1
            if index > self.session.maximum_segments:
                self._lost()
                raise LiveRetentionLost("source event segment retention capacity is exhausted")
            events = tuple(packet.observation for packet in packets)
            segment = LiveEventSegment(self.session.identity, index,
                None if self._last_segment is None else self._last_segment.identity,
                self.last_event_sequence, events, source_sequence_gaps(self.last_event_sequence, events))
            memory = {actor: values.copy() for actor, values in self._memory.items()}
            now = self.session.coordinate(self._clock())
            for packet in packets:
                event = packet.observation
                found = tuple(handle.lease for handle, _ in self._actors.values() if handle.lease.identity == event.actor_lease)
                if len(found) != 1 or event.channel not in found[0].observation_channels:
                    raise PermissionError("source observation has no current separately authorized actor")
                lease = found[0]
                times = tuple(self.session.coordinate(value) for value in
                    (event.occurred_at, event.sampled_at, event.available_at, event.retain_until))
                occurred, sampled, available, retained = times
                if (event.availability.outcome_access is not self.session.outcome_access
                        or not occurred <= sampled <= available <= now
                        or not Fraction(available) < Fraction(retained) <= Fraction(available) + Fraction(lease.retention_duration)
                        or Fraction(available) - Fraction(sampled) > Fraction(lease.maximum_delay)
                        or available >= self.session.coordinate(lease.expires_at)):
                    raise PermissionError("observation violates availability, delay, retention or outcome permissions")
                selected = memory[lease.actor_id]
                self._evict(selected, lease, now)
                parents = {value.observation.identity: value.observation for value in selected.values()}
                if (not set(event.derived_from) <= set(parents)
                        or any(retained > self.session.coordinate(parents[parent].retain_until) for parent in event.derived_from)):
                    raise PermissionError("derived observation has discarded, foreign or extended-retention ancestors")
                selected[event.sequence] = packet
                self._evict(selected, lease, now)
            try:
                self._custody.publish_segment(segment, packets)
            except (OSError, ValueError, RuntimeError):
                self._lost()
                raise
            self._memory, self._last_segment = memory, segment
            self._source_has_gaps = self._source_has_gaps or bool(segment.gaps)
            return segment
        finally:
            self._lock.release()

    def read(self, handle, token, sequences, *, cutoff):
        with self._lock:
            lease = self._handle(handle, token)
            if (type(sequences) is not tuple or not 0 < len(sequences) <= lease.maximum_read_window
                    or any(type(value) is not int or value <= 0 for value in sequences)
                    or tuple(sorted(set(sequences))) != sequences):
                raise ValueError("actor read requires a bounded unique sequence window")
            now = self.session.coordinate(self._clock())
            if (type(cutoff) is not InformationCutoff or cutoff.coordinate is None
                    or cutoff.clock_id != self.session.clock.clock_id or cutoff.coordinate > now):
                raise PermissionError("actor read lacks a current exact native information cutoff")
            selected = self._memory[lease.actor_id]
            self._evict(selected, lease, now)
            packets, missing = [], []
            for sequence in sequences:
                packet = selected.get(sequence)
                if packet is None:
                    missing.append(sequence)
                    continue
                event = packet.observation
                available = replace(event.availability, clock_id=self.session.clock.clock_id,
                    available_at=self.session.coordinate(event.available_at))
                within = (available.available_at <= cutoff.coordinate if cutoff.includes_coordinate
                          else available.available_at < cutoff.coordinate)
                if not within or not cutoff.allows(available):
                    missing.append(sequence)
                else:
                    packets.append(packet)
            self._access.require_actor(lease, effect_key=None)
            return LiveReadWindow(tuple(packets), tuple(missing), self._source_has_gaps)

    def execute(self, handle, token, operation, prepared_payload):
        with self._lock:
            lease = self._handle(handle, token)
            if type(operation) is not FiniteLiveOperation or operation.actor_lease != lease:
                raise PermissionError("finite operation substitutes its actor handle")
            port = self._effect_ports[operation.effect_key]
            self._access.require_actor(lease, effect_key=operation.effect_key)
            require_live_payload(operation.prepared_commitment, prepared_payload)
            prior = self._custody.read_operation(operation.request_id)
            if prior is not None:
                if prior != operation:
                    raise ValueError("request deduplication cannot replace its original operation")
                if self._custody.has_contact(operation):
                    return self._readout(operation)
            if lease.actor_id in self._inflight.values():
                raise LiveBackpressure("actor already has one in-flight finite submission")
            if (operation.package != self._package
                    or operation.window.session != self.session.identity
                    or operation.window.dependence_root != self.session.dependence_root):
                raise PermissionError("new submission changes the current package, session or dependence root")
            now = self.session.coordinate(self._clock())
            if not self.session.coordinate(operation.committed_at) <= now < self.session.coordinate(operation.action_expires_at):
                raise PermissionError("finite commitment is future-dated or already expired")
            if self._source_has_gaps:
                raise LiveRetentionLost("source event gaps make this session history unevaluable")
            if operation.inputs:
                sequences = tuple(sorted(packet.observation.sequence for packet in self._memory[lease.actor_id].values()
                    if packet.observation.identity in operation.inputs))
                if not sequences:
                    raise PermissionError("finite operation consumes discarded or foreign observations")
                observed = self.read(handle, token, sequences, cutoff=operation.information_cutoff)
                if (not observed.complete or {packet.observation.identity for packet in observed.packets} != set(operation.inputs)):
                    raise PermissionError("finite operation consumes unavailable, discarded or foreign observations")
            if prior is None and self._operation_count >= self.session.maximum_operations:
                raise ValueError("continuing session finite-operation capacity is exhausted")
            try:
                # Both the actual prepared bytes and complete original scheduled
                # envelope must survive custody before the existing contact owner.
                self._custody.publish_operation(operation, prepared_payload)
                if prior is None:
                    self._operation_count += 1
            except (OSError, ValueError, RuntimeError):
                self._lost()
                raise
            self._access.require_actor(lease, effect_key=operation.effect_key)
            try:
                self._custody.begin_contact(operation)
            except (OSError, ValueError, RuntimeError):
                self._lost()
                raise
            self._inflight[operation.request_id] = lease.actor_id
        try:
            receipt, payload = port.submit(operation, prepared_payload)
            with self._lock:
                self._custody.publish_effect(operation, receipt, payload)
        except (OSError, ValueError, RuntimeError):
            # The existing contact is the retained uncertainty witness. A lost
            # reply or receipt is never a reason to repeat the effect.
            return self._readout(operation)
        finally:
            try:
                self._custody.retire_contact(operation)
            finally:
                with self._lock:
                    self._inflight.pop(operation.request_id, None)
        return self._readout(operation)

    def _readout(self, operation):
        return LiveOperationReadout(operation, self._custody.read_effect(operation), self._custody.has_contact(operation))

    def reconcile(self, request_id: str) -> LiveOperationReadout:
        """Owner-only actual observation of the original effect; never submit."""
        self._access.require_owner(self.session)
        operation = self._custody.read_operation(request_id)
        if operation is None or not self._custody.has_contact(operation):
            raise ValueError("reconciliation requires the original retained contact")
        observed = self._effect_ports[operation.effect_key].observe(operation)
        if observed is not None:
            receipt, payload = observed
            with self._lock:
                self._custody.publish_effect(operation, receipt, payload)
        return self._readout(operation)

    def close(self):
        with self._lock:
            if self._active:
                if self._inflight:
                    self._active = False
                    raise RuntimeError("live owner closed with in-flight effects; original contacts require reconciliation")
                try:
                    self._boundary(LiveBoundaryKind.CLOSED)
                finally:
                    self._active = False
                    self._memory.clear()
