# SPDX-License-Identifier: MPL-2.0
"""Continuing source identities and finite operations, without I/O or authority.

Sessions, actor generations, windows, requests and retained runs have separate
identities. None of them creates another independent scientific unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.science.models.time import AvailabilitySpec, ClockCoordinate, ClockSpec, ClockTransport, ClockProjectionStatus, CoordinateOrigin, HorizonSpec, InformationCutoff


MAX_LIVE_ACTORS = 16
MAX_LIVE_SEGMENTS = 1024
MAX_LIVE_EVENTS = 64
MAX_LIVE_MEMORY = 128
MAX_LIVE_OPERATIONS = 256
MAX_LIVE_PAYLOAD_BYTES = 64 * 1024
MAX_LIVE_RECORD_BYTES = 1024 * 1024


def _id(value: str) -> None:
    validate_stable_id(value)
    if len(value) > 192:
        raise ValueError("live identifier exceeds its byte bound")


def _positive(value: int, maximum: int, name: str) -> None:
    if type(value) is not int or not 0 < value <= maximum:
        raise ValueError(name + " must be a positive bounded integer")


def _time_number(value: Decimal) -> None:
    validate_decimal(value, field_name="live clock quantity")
    if len(value.as_tuple().digits) > 96 or abs(value.as_tuple().exponent) > 96:
        raise ValueError("live clock quantity exceeds its exact arithmetic bound")


def _references(values: tuple[ObjectIdentity, ...], maximum: int) -> None:
    if (type(values) is not tuple or len(values) > maximum
            or any(type(value) is not ObjectIdentity for value in values)
            or len(set(values)) != len(values)):
        raise ValueError("live references require a bounded unique immutable census")
    if tuple(sorted(values, key=lambda value: value.object_id)) != values:
        raise ValueError("live references must be ordered by original object ID")


def same_clock(left: ClockCoordinate, right: ClockCoordinate) -> bool:
    return (left.clock_id, left.time_unit, left.coordinate_frame, left.origin) == (
        right.clock_id, right.time_unit, right.coordinate_frame, right.origin)


@dataclass(frozen=True, slots=True)
class ContinuingSourceSession(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/continuing-source-session"
    session_id: str
    source: ObjectIdentity
    dependence_root: ObjectIdentity
    lifecycle_owner_id: str
    source_generation: int
    clock: ClockSpec
    clock_origin: CoordinateOrigin
    clock_transports: tuple[ClockTransport, ...]
    visibility: VisibilityCeiling
    outcome_access: OutcomeAccess
    maximum_actors: int
    maximum_segments: int
    events_per_segment: int
    maximum_operations: int

    def __post_init__(self) -> None:
        for value in (self.session_id, self.lifecycle_owner_id):
            _id(value)
        if type(self.source) is not ObjectIdentity or type(self.dependence_root) is not ObjectIdentity:
            raise TypeError("session requires exact source and dependence identities")
        _positive(self.source_generation, 2**63 - 1, "source generation")
        _positive(self.maximum_actors, MAX_LIVE_ACTORS, "actor bound")
        _positive(self.maximum_segments, MAX_LIVE_SEGMENTS, "segment bound")
        _positive(self.events_per_segment, MAX_LIVE_EVENTS, "segment event bound")
        _positive(self.maximum_operations, MAX_LIVE_OPERATIONS, "operation bound")
        if type(self.clock) is not ClockSpec or type(self.clock_origin) is not CoordinateOrigin:
            raise TypeError("session requires its exact clock semantics")
        if (type(self.clock_transports) is not tuple or len(self.clock_transports) > 16
                or any(type(value) is not ClockTransport for value in self.clock_transports)
                or len({value.source_clock_id for value in self.clock_transports}) != len(self.clock_transports)):
            raise ValueError("session requires a bounded unambiguous clock mapping census")
        for mapping in self.clock_transports:
            for value in (mapping.scale, mapping.offset, mapping.tolerance,
                          mapping.valid_source_lower, mapping.valid_source_upper):
                if value is not None:
                    _time_number(value)
            if (mapping.target_clock_id, mapping.target_time_unit, mapping.target_coordinate_frame,
                    mapping.target_origin) != (self.clock.clock_id, self.clock.time_unit,
                    self.clock.coordinate_frame, self.clock_origin):
                raise ValueError("clock mapping targets another session clock")
        if ((self.outcome_access, self.visibility) not in (
                (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
                (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))):
            raise ValueError("live actor source cannot expose an evaluator or privileged ledger")

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(self.session_id, self)

    def coordinate(self, value: ClockCoordinate) -> Decimal:
        """Require an exact mapping; bounded alignment is not silently rounded."""
        if type(value) is not ClockCoordinate:
            raise TypeError("live time requires an exact ClockCoordinate")
        _time_number(value.coordinate)
        if (value.clock_id, value.time_unit, value.coordinate_frame, value.origin) == (
                self.clock.clock_id, self.clock.time_unit, self.clock.coordinate_frame, self.clock_origin):
            return value.coordinate
        for mapping in self.clock_transports:
            if mapping.source_clock_id == value.clock_id:
                with localcontext() as context:
                    context.prec = 768
                    projection = mapping.project(value)
                if projection.status is ClockProjectionStatus.EXACT and projection.target is not None:
                    _time_number(projection.target.coordinate)
                    return projection.target.coordinate
                raise ValueError("live boundary requires an available exact clock mapping")
        raise ValueError("live boundary lacks its explicit clock mapping")


@dataclass(frozen=True, slots=True)
class LiveActorLease(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-actor-lease"
    session: ObjectIdentity
    actor_id: str
    connection_generation: int
    allocation_generation: int
    life_generation: int
    expires_at: ClockCoordinate
    observation_channels: tuple[str, ...]
    effect_keys: tuple[str, ...]
    maximum_observations: int
    maximum_read_window: int
    retention_duration: Decimal
    maximum_delay: Decimal

    def __post_init__(self) -> None:
        _id(self.actor_id)
        if self.session.object_schema != ContinuingSourceSession.SCHEMA:
            raise ValueError("actor lease requires its exact continuing session")
        for value in self.generations:
            _positive(value, 2**63 - 1, "actor generation")
        if type(self.expires_at) is not ClockCoordinate:
            raise TypeError("actor lease requires its native expiry coordinate")
        for values in (self.observation_channels, self.effect_keys):
            if type(values) is not tuple or len(values) > 32:
                raise ValueError("actor permission census exceeds its bound")
            require_sorted_unique_strings(values, field_name="actor permissions")
            for value in values:
                _id(value)
        _positive(self.maximum_observations, MAX_LIVE_MEMORY, "actor memory bound")
        _positive(self.maximum_read_window, min(self.maximum_observations, MAX_LIVE_EVENTS), "actor window bound")
        for name in ("retention_duration", "maximum_delay"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            _time_number(getattr(self, name))
        if self.retention_duration == 0:
            raise ValueError("actor retention duration must be positive")

    @property
    def generations(self) -> tuple[int, int, int]:
        return self.connection_generation, self.allocation_generation, self.life_generation

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record("lease." + self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class LiveObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-observation"
    session: ObjectIdentity
    sequence: int
    actor_lease: ObjectIdentity
    channel: str
    occurred_at: ClockCoordinate
    sampled_at: ClockCoordinate
    available_at: ClockCoordinate
    availability: AvailabilitySpec
    retain_until: ClockCoordinate
    payload: ObjectIdentity
    derived_from: tuple[ObjectIdentity, ...] = ()

    def __post_init__(self) -> None:
        _positive(self.sequence, 2**63 - 1, "source event sequence")
        _id(self.channel)
        if (self.session.object_schema != ContinuingSourceSession.SCHEMA
                or self.actor_lease.object_schema != LiveActorLease.SCHEMA):
            raise ValueError("live observation substitutes its session or actor generation")
        for value in (self.occurred_at, self.sampled_at, self.available_at, self.retain_until):
            if type(value) is not ClockCoordinate:
                raise TypeError("observation requires four explicit clock coordinates")
        if (type(self.availability) is not AvailabilitySpec
                or self.availability.clock_id != self.available_at.clock_id
                or self.availability.available_at != self.available_at.coordinate):
            raise ValueError("observation availability differs from its actual time")
        if type(self.payload) is not ObjectIdentity:
            raise TypeError("observation requires its exact domain payload identity")
        _references(self.derived_from, MAX_LIVE_EVENTS)
        if any(parent.object_schema != self.SCHEMA for parent in self.derived_from):
            raise ValueError("derived observation lineage must name original live observations")

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(f"observation.{self.session.object_id}.{self.sequence}", self)


@dataclass(frozen=True, slots=True)
class LiveSequenceGap(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-sequence-gap"
    first: int
    last: int

    def __post_init__(self) -> None:
        _positive(self.first, 2**63 - 1, "gap start")
        _positive(self.last, 2**63 - 1, "gap end")
        if self.last < self.first:
            raise ValueError("source sequence gap is reversed")


def source_sequence_gaps(previous_sequence: int, events: tuple[LiveObservation, ...]) -> tuple[LiveSequenceGap, ...]:
    gaps = []
    for event in events:
        if event.sequence <= previous_sequence:
            raise ValueError("source events must advance the original global sequence")
        if event.sequence > previous_sequence + 1:
            gaps.append(LiveSequenceGap(previous_sequence + 1, event.sequence - 1))
        previous_sequence = event.sequence
    return tuple(gaps)


@dataclass(frozen=True, slots=True)
class LiveEventSegment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-event-segment"
    session: ObjectIdentity
    index: int
    previous: ObjectIdentity | None
    previous_sequence: int
    events: tuple[LiveObservation, ...]
    gaps: tuple[LiveSequenceGap, ...]

    def __post_init__(self) -> None:
        _positive(self.index, MAX_LIVE_SEGMENTS, "event segment index")
        if self.session.object_schema != ContinuingSourceSession.SCHEMA:
            raise ValueError("event segment requires its original session")
        if (type(self.previous_sequence) is not int or self.previous_sequence < 0
                or (self.index == 1) != (self.previous is None)
                or (self.index == 1 and self.previous_sequence != 0)
                or (self.previous is not None and self.previous.object_schema != self.SCHEMA)):
            raise ValueError("event segment has an invalid predecessor boundary")
        if (type(self.events) is not tuple or not 0 < len(self.events) <= MAX_LIVE_EVENTS
                or any(type(event) is not LiveObservation or event.session != self.session for event in self.events)):
            raise ValueError("event segment requires a bounded same-session event census")
        if self.gaps != source_sequence_gaps(self.previous_sequence, self.events):
            raise ValueError("event segment hides or invents original sequence gaps")

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(f"segment.{self.session.object_id}.{self.index}", self)


class LiveBoundaryKind(StrEnum):
    ACTOR = "ACTOR"
    PACKAGE = "PACKAGE"
    RETENTION_LOSS = "RETENTION_LOSS"
    CLOSED = "CLOSED"


@dataclass(frozen=True, slots=True)
class LiveSessionBoundary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-session-boundary"
    session: ObjectIdentity
    index: int
    kind: LiveBoundaryKind
    at: ClockCoordinate
    last_event_sequence: int
    previous: ObjectIdentity | None
    selected: ObjectIdentity | None

    def __post_init__(self) -> None:
        _positive(self.index, MAX_LIVE_SEGMENTS, "lifecycle boundary index")
        if (self.session.object_schema != ContinuingSourceSession.SCHEMA
                or type(self.kind) is not LiveBoundaryKind or type(self.at) is not ClockCoordinate
                or type(self.last_event_sequence) is not int or self.last_event_sequence < 0):
            raise ValueError("lifecycle boundary has invalid session, kind or time")
        if self.kind in (LiveBoundaryKind.ACTOR, LiveBoundaryKind.PACKAGE) and self.selected is None:
            raise ValueError("lifecycle selection requires its exact retained record")
        if self.kind is LiveBoundaryKind.ACTOR and self.selected.object_schema != LiveActorLease.SCHEMA:
            raise ValueError("actor boundary requires its selected generation")


@dataclass(frozen=True, slots=True)
class LiveScientificWindow(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-scientific-window"
    window_id: str
    session: ObjectIdentity
    dependence_root: ObjectIdentity
    starts_at: ClockCoordinate
    ends_at: ClockCoordinate

    def __post_init__(self) -> None:
        _id(self.window_id)
        if (self.session.object_schema != ContinuingSourceSession.SCHEMA
                or type(self.dependence_root) is not ObjectIdentity
                or not same_clock(self.starts_at, self.ends_at)
                or self.starts_at.coordinate >= self.ends_at.coordinate):
            raise ValueError("scientific window requires one finite native interval and dependence root")


@dataclass(frozen=True, slots=True)
class FiniteLiveOperation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/finite-live-operation"
    request_id: str
    run_id: str
    window: LiveScientificWindow
    actor_lease: LiveActorLease
    package: ObjectIdentity
    prepared_commitment: ObjectIdentity
    effect_key: str
    inputs: tuple[ObjectIdentity, ...]
    information_cutoff: InformationCutoff
    committed_at: ClockCoordinate
    application_not_before: ClockCoordinate
    action_expires_at: ClockCoordinate
    scientific_horizon: HorizonSpec
    request_timeout_seconds: Decimal
    implementation_commit: str

    def __post_init__(self) -> None:
        for value in (self.request_id, self.run_id, self.effect_key):
            _id(value)
        if (type(self.window) is not LiveScientificWindow or type(self.actor_lease) is not LiveActorLease
                or self.window.session != self.actor_lease.session
                or self.effect_key not in self.actor_lease.effect_keys):
            raise ValueError("finite operation requires the exact authorized actor and window")
        if type(self.package) is not ObjectIdentity or type(self.prepared_commitment) is not ObjectIdentity:
            raise TypeError("finite operation requires original package and prepared commitment")
        _references(self.inputs, MAX_LIVE_EVENTS)
        if any(value.object_schema != LiveObservation.SCHEMA for value in self.inputs):
            raise ValueError("finite operation inputs must name original live observations")
        if type(self.information_cutoff) is not InformationCutoff or self.information_cutoff.coordinate is None:
            raise ValueError("finite operation requires an explicit information cutoff")
        times = (self.committed_at, self.application_not_before, self.action_expires_at,
                 self.actor_lease.expires_at, self.window.starts_at, self.window.ends_at)
        if any(type(value) is not ClockCoordinate or not same_clock(times[0], value) for value in times):
            raise ValueError("finite operation schedule requires one exact mapped native clock")
        if not (self.window.starts_at.coordinate <= self.committed_at.coordinate
                <= self.application_not_before.coordinate < self.action_expires_at.coordinate
                <= self.actor_lease.expires_at.coordinate
                and self.committed_at.coordinate < self.window.ends_at.coordinate):
            raise ValueError("finite operation exceeds its original lease or scheduled envelope")
        if (self.information_cutoff.clock_id != self.committed_at.clock_id
                or self.information_cutoff.coordinate > self.committed_at.coordinate):
            raise ValueError("finite operation cutoff exceeds its commitment")
        if (type(self.scientific_horizon) is not HorizonSpec
                or self.scientific_horizon.clock_id != self.committed_at.clock_id
                or self.scientific_horizon.time_unit != self.committed_at.time_unit):
            raise ValueError("scientific horizon differs from the original native clock")
        validate_decimal(self.request_timeout_seconds, field_name="request timeout", minimum=Decimal(0))
        if self.request_timeout_seconds <= 0:
            raise ValueError("request timeout must be positive")
        if (type(self.implementation_commit) is not str or len(self.implementation_commit) != 40
                or any(value not in "0123456789abcdef" for value in self.implementation_commit)):
            raise ValueError("live effect requires its original producing source commit")

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(self.request_id, self)


class LiveEffectStage(StrEnum):
    ACCEPTED = "ACCEPTED"
    APPLIED = "APPLIED"
    OBSERVED = "OBSERVED"
    REFUSED = "REFUSED"


@dataclass(frozen=True, slots=True)
class LiveEffectReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/live-effect-receipt"
    operation: ObjectIdentity
    stage: LiveEffectStage
    accepted_at: ClockCoordinate | None
    applied_at: ClockCoordinate | None
    observed_at: ClockCoordinate | None
    result: ObjectIdentity | None
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.operation.object_schema != FiniteLiveOperation.SCHEMA or type(self.stage) is not LiveEffectStage:
            raise ValueError("live receipt requires an exact finite operation and effect stage")
        if type(self.reason_codes) is not tuple or len(self.reason_codes) > 16:
            raise ValueError("live receipt reason census exceeds its bound")
        require_sorted_unique_strings(self.reason_codes, field_name="live effect reasons")
        for reason in self.reason_codes:
            _id(reason)
        if self.stage is LiveEffectStage.REFUSED:
            if self.applied_at is not None or self.observed_at is not None or self.result is not None or not self.reason_codes:
                raise ValueError("refused effect cannot assert an application or observed result")
        elif self.accepted_at is None or self.reason_codes:
            raise ValueError("known live effect requires its actual command acceptance")
        if (self.stage in (LiveEffectStage.APPLIED, LiveEffectStage.OBSERVED)) != (self.applied_at is not None):
            raise ValueError("live effect stage differs from known native application")
        if (self.stage is LiveEffectStage.OBSERVED) != (self.observed_at is not None and self.result is not None):
            raise ValueError("live effect stage differs from the observed native result")
        if self.stage is not LiveEffectStage.OBSERVED and (self.observed_at is not None or self.result is not None):
            raise ValueError("unobserved effect cannot supply a result")
        times = tuple(value for value in (self.accepted_at, self.applied_at, self.observed_at) if value is not None)
        if any(type(value) is not ClockCoordinate for value in times):
            raise TypeError("effect receipt requires exact actual clock coordinates")
        if any(not same_clock(times[0], value) for value in times):
            raise ValueError("effect receipt changes its native clock")
        if tuple(value.coordinate for value in times) != tuple(sorted(value.coordinate for value in times)):
            raise ValueError("effect receipt reverses acceptance, application or observation")
