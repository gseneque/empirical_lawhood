# SPDX-License-Identifier: MPL-2.0
"""Disclosed source contracts only; no source, store, lease grant or effect exists."""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.science.inquiry.continuing_source import ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveObservation, LiveScientificWindow, LiveSequenceGap
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.time import AvailabilitySpec, CausalPhase, ClockCoordinate, ClockLabelSemantics, ClockSpec, CoordinateOrigin, HoldSemantics, HorizonSpec, InformationCutoff, SamplingSemantics
from empirical_lawhood.execution.extension_conformance import ConformanceCall as Call, ConformanceCase as Case, ConformanceProfile as Profile, ExtensionConformanceSelection


def coordinate(value):
    return ClockCoordinate('disclosed.source.clock', Decimal(value), 'tick', 'disclosed-source', CoordinateOrigin.ABSOLUTE)


def identity(name):
    return ObjectIdentity(name, 'empirical-lawhood/disclosed-source/absent-payload', '1.0.0', 'a' * 64)


class UnavailableAccess:
    def require_owner(self, session):
        raise AssertionError('no source access selected')

    def require_actor(self, lease, *, effect_key):
        raise AssertionError('no actor access selected')


class UnavailableEffect:
    def submit(self, operation, prepared_payload):
        raise AssertionError('no source effect selected')

    def observe(self, operation):
        raise AssertionError('no source observer selected')


clock = ClockSpec('disclosed.source.clock', 'Disclosed source ticks', 'tick', 'disclosed-source',
    SamplingSemantics.REGULAR, HoldSemantics.ZERO_ORDER, ClockLabelSemantics.INSTANT, Decimal(1))
session = ContinuingSourceSession('disclosed.source.session', identity('disclosed.source'), identity('disclosed.root'),
    'disclosed.owner', 1, clock, CoordinateOrigin.ABSOLUTE, (), VisibilityCeiling.DEVELOPMENT_ONLY,
    OutcomeAccess.DEVELOPMENT_VISIBLE, 2, 4, 4, 4)
lease = LiveActorLease(session.identity, 'disclosed.actor', 1, 1, 1, coordinate(100),
    ('state',), ('increment',), 4, 2, Decimal(20), Decimal(5))
window = LiveScientificWindow('disclosed.window', session.identity, session.dependence_root, coordinate(0), coordinate(50))
operation = FiniteLiveOperation('disclosed.request', 'disclosed.run', window, lease, identity('disclosed.package'),
    identity('disclosed.commitment'), 'increment', (),
    InformationCutoff('disclosed.cutoff', clock.clock_id, CausalPhase.PRE_ACTION, Decimal(10)),
    coordinate(10), coordinate(10), coordinate(20),
    HorizonSpec('disclosed.horizon', clock.clock_id, Decimal(40), 'tick'), Decimal('0.1'), 'a' * 40)
event = LiveObservation(session.identity, 3, lease.identity, 'state', coordinate(8), coordinate(8), coordinate(9),
    AvailabilitySpec(clock.clock_id, CausalPhase.PRE_ACTION, OutcomeAccess.DEVELOPMENT_VISIBLE, Decimal(9)),
    coordinate(25), identity('disclosed.payload'), ())
application = dict(operation=operation, session=session, current_lease=lease, at=coordinate(11))
CONFORMANCE_SELECTION = ExtensionConformanceSelection('disclosed-source', 'empirical-lawhood/disclosed-source/', (),
    imported_record_types=(ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveObservation),
    profile=Profile.CONTINUING_SOURCE_CONTRACTS,
    source_access=UnavailableAccess(), effect_ports=(('increment', UnavailableEffect()),),
    cases=(Case('source.current-application', Call.LIVE_APPLICATION, application, None),
        Case('source.stale-generation', Call.LIVE_APPLICATION,
            {**application, 'current_lease': replace(lease, connection_generation=2)}, 'PermissionError', 'stale'),
        Case('source.expired', Call.LIVE_APPLICATION, {**application, 'at': coordinate(20)}, 'PermissionError', 'schedule'),
        Case('source.original-gap', Call.LIVE_EVENT_GAPS, dict(previous_sequence=0, events=(event,)), (LiveSequenceGap(1, 2),)),
        Case('source.repeated-event', Call.LIVE_EVENT_GAPS, dict(previous_sequence=3, events=(event,)), 'ValueError', 'advance')))
