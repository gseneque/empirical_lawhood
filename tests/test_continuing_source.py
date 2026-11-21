# SPDX-License-Identifier: MPL-2.0
"""Bounded exposed source/access/custody controls; no scientific acquisition."""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from threading import Event, Thread
from typing import ClassVar

import pytest

from empirical_lawhood.api.continuing_source import read_continuing_operation, reconcile_continuing_operation
from empirical_lawhood.storage.continuing_source import ExternalContinuingSourceStore
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.science.inquiry.continuing_source import ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveEffectReceipt, LiveEffectStage, LiveObservation, LiveScientificWindow, LiveSequenceGap
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.models.time import AvailabilitySpec, CausalPhase, ClockCoordinate, ClockLabelSemantics, ClockSpec, CoordinateOrigin, HoldSemantics, HorizonSpec, InformationCutoff, SamplingSemantics
from empirical_lawhood.execution.continuing_source import ContinuingSourceOwner, LiveBackpressure, LiveObservationPacket, LiveRetentionLost, require_live_application
from tests.test_recursive_public_service import _plane


@dataclass(frozen=True, slots=True)
class FixtureRecord(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/live-record'
    record_id: str
    value: int

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def coordinate(value):
    return ClockCoordinate('test.live.clock', Decimal(value), 'tick', 'source', CoordinateOrigin.ABSOLUTE)


class Access:
    revoked = False

    def require_owner(self, session):
        if self.revoked:
            raise PermissionError('actual source access revoked')

    def require_actor(self, lease, *, effect_key):
        if self.revoked:
            raise PermissionError('actual actor access revoked')


class Effect:
    def __init__(self):
        self.calls = []
        self.observed = None
        self.before = None
        self.failure = None

    def submit(self, operation, payload):
        self.calls.append(operation)
        if self.before:
            self.before(operation)
        if self.failure:
            raise self.failure
        return self.observed or (LiveEffectReceipt(operation.identity, LiveEffectStage.ACCEPTED,
            coordinate(10), None, None, None), None)

    def observe(self, operation):
        return self.observed


@contextmanager
def case(tmp_path, *, segments=16, memory=3):
    from types import SimpleNamespace
    source = FixtureRecord('test.live.source', 1)
    root = FixtureRecord('test.live.dependence', 1)
    package = FixtureRecord('test.live.package', 1)
    clock = ClockSpec('test.live.clock', 'Software source ticks', 'tick', 'source',
        SamplingSemantics.REGULAR, HoldSemantics.ZERO_ORDER, ClockLabelSemantics.INSTANT, Decimal(1))
    session = ContinuingSourceSession('test.live.session', source.identity, root.identity, 'test.live.owner',
        1, clock, CoordinateOrigin.ABSOLUTE, (), VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, 2, segments, 8, 8)
    plane = _plane(tmp_path / 'custody')
    store = ExternalContinuingSourceStore(plane=plane, session=session, relative_root='selected/live')
    access, effect, now = Access(), Effect(), [10]
    owner = ContinuingSourceOwner(session=session, custody=store, clock=lambda: coordinate(now[0]),
        effect_ports={'increment': effect}, current_access=access)
    with store.owner_lock():
        owner.start(package.identity, package.canonical_bytes())
        a = LiveActorLease(session.identity, 'actor.a', 1, 1, 1, coordinate(100),
            ('state',), ('increment',), memory, min(3, memory), Decimal(20), Decimal(5))
        b = replace(a, actor_id='actor.b')
        first, second = owner.bind_actor(a), owner.bind_actor(b)
        selected = SimpleNamespace(owner=owner, store=store, plane=plane, session=session,
            access=access, effect=effect, now=now, a=first, b=second, package=package)
        try:
            yield selected
        finally:
            owner.close()


def packet(selected, sequence, actor=None, *, sampled=8, available=9, retained=25, parents=()):
    actor = actor or selected.a
    payload = FixtureRecord(f'test.live.payload.{sequence}', sequence)
    event = LiveObservation(selected.session.identity, sequence, actor.lease.identity, 'state',
        coordinate(sampled), coordinate(sampled), coordinate(available),
        AvailabilitySpec('test.live.clock', CausalPhase.PRE_ACTION, OutcomeAccess.DEVELOPMENT_VISIBLE, Decimal(available)),
        coordinate(retained), payload.identity, parents)
    return LiveObservationPacket(event, payload.canonical_bytes())


def cutoff(value=10):
    return InformationCutoff('test.live.cutoff', 'test.live.clock', CausalPhase.PRE_ACTION, Decimal(value))


def operation(selected, actor=None, *, name='request.first', inputs=(), package=None):
    actor = actor or selected.a
    prepared = FixtureRecord('test.live.prepared.' + name, 1)
    window = LiveScientificWindow('test.live.window', selected.session.identity,
        selected.session.dependence_root, coordinate(0), coordinate(50))
    op = FiniteLiveOperation(name, 'test.live.run', window, actor.lease,
        package or selected.package.identity, prepared.identity, 'increment',
        tuple(sorted(inputs, key=lambda value: value.object_id)), cutoff(), coordinate(10), coordinate(10),
        coordinate(20), HorizonSpec('test.live.horizon', 'test.live.clock', Decimal(40), 'tick'), Decimal('0.1'), 'a' * 40)
    return op, prepared.canonical_bytes()


def observed(op):
    result = FixtureRecord('test.live.result.' + op.request_id, 2)
    return LiveEffectReceipt(op.identity, LiveEffectStage.OBSERVED, coordinate(10), coordinate(11),
        coordinate(12), result.identity), result.canonical_bytes()


def test_actor_views_current_access_and_cutoffs_do_not_recover_other_actor_records(tmp_path):
    with case(tmp_path) as selected:
        first, second = packet(selected, 1), packet(selected, 2, selected.b)
        selected.owner.ingest((first, second))
        view = selected.a.read((1, 2), cutoff=cutoff())
        assert view.packets == (first,) and view.missing_sequences == (2,) and not view.complete
        assert selected.b.read((1, 2), cutoff=cutoff()).packets == (second,)
        assert selected.a.read((1,), cutoff=cutoff(8)).missing_sequences == (1,)
        with pytest.raises(PermissionError, match='cutoff'):
            selected.a.read((1,), cutoff=cutoff(11))
        selected.access.revoked = True
        with pytest.raises(PermissionError, match='revoked'):
            selected.a.read((1,), cutoff=cutoff())
        with pytest.raises(PermissionError, match='revoked'):
            selected.a.execute(*operation(selected))
        selected.access.revoked = False
        assert not selected.effect.calls


def test_memory_eviction_cascades_to_derived_records_without_ledger_backdoor(tmp_path):
    with case(tmp_path, memory=2) as selected:
        first = packet(selected, 1)
        derived = packet(selected, 2, parents=(first.observation.identity,))
        selected.owner.ingest((first, derived))
        assert selected.a.read((1, 2), cutoff=cutoff()).complete
        selected.owner.ingest((packet(selected, 3),))
        assert selected.a.read((1, 2), cutoff=cutoff()).missing_sequences == (1, 2)
        assert selected.store.read_segment(1).events == (first.observation, derived.observation)
        with pytest.raises(PermissionError, match='discarded'):
            selected.owner.ingest((packet(selected, 4, parents=(first.observation.identity,)),))
        with pytest.raises(PermissionError, match='discarded'):
            selected.a.execute(*operation(selected, inputs=(first.observation.identity,)))
        selected.now[0] = 25
        assert selected.a.read((3,), cutoff=cutoff(25)).missing_sequences == (3,)


@pytest.mark.parametrize('field', ('connection_generation', 'allocation_generation', 'life_generation'))
def test_each_actor_generation_invalidates_only_its_own_handles_and_native_effect(tmp_path, field):
    with case(tmp_path) as selected:
        selected.owner.ingest((packet(selected, 1), packet(selected, 2, selected.b)))
        op, _ = operation(selected)
        changed = replace(selected.a.lease, **{field: 2})
        fresh = selected.owner.bind_actor(changed)
        with pytest.raises(PermissionError, match='stale'):
            selected.a.read((1,), cutoff=cutoff())
        assert fresh.read((1,), cutoff=cutoff()).missing_sequences == (1,)
        assert selected.b.read((2,), cutoff=cutoff()).complete
        with pytest.raises(PermissionError, match='stale'):
            require_live_application(op, session=selected.session, current_lease=changed, at=coordinate(11))
        with pytest.raises(PermissionError, match='advance'):
            selected.owner.bind_actor(changed)
        assert selected.session.dependence_root == op.window.dependence_root


def test_exact_commitment_and_contact_precede_submission_and_duplicates_do_not_apply_twice(tmp_path):
    with case(tmp_path) as selected:
        first = packet(selected, 1)
        selected.owner.ingest((first,))
        op, payload = operation(selected, inputs=(first.observation.identity,))
        def before(actual):
            assert selected.store.read_operation(op.request_id) == op
            assert selected.store.has_contact(op)
            require_live_application(actual, session=selected.session, current_lease=selected.a.lease, at=coordinate(11))
        selected.effect.before = before
        selected.effect.observed = observed(op)
        result = selected.a.execute(op, payload)
        assert result.disposition == 'OBSERVED' and result.contacted
        assert selected.a.execute(op, payload) == result
        assert len(selected.effect.calls) == 1
        with pytest.raises(ValueError, match='deduplication'):
            selected.a.execute(replace(op, run_id='foreign.run'), payload)
        original = op.canonical_bytes()
        recovered = read_continuing_operation(session=selected.session, artifact_plane=selected.plane,
            relative_root='selected/live', request_id=op.request_id, current_access=selected.access)
        assert recovered == result and recovered.operation.canonical_bytes() == original


def test_lost_reply_retains_unknown_contact_and_read_only_reconciliation_never_submits(tmp_path):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        selected.effect.failure = TimeoutError('reply lost after possible application')
        result = selected.a.execute(op, payload)
        assert result.disposition == 'UNKNOWN_EFFECT_DO_NOT_REPEAT'
        assert selected.a.execute(op, payload) == result and len(selected.effect.calls) == 1
        selected.effect.observed = observed(op)
        restored = reconcile_continuing_operation(session=selected.session, artifact_plane=selected.plane,
            relative_root='selected/live', request_id=op.request_id, current_access=selected.access,
            effect_observer=selected.effect.observe)
        assert restored.disposition == 'OBSERVED' and len(selected.effect.calls) == 1
        with pytest.raises(ValueError, match='rewrites'):
            selected.store.publish_effect(op, replace(restored.receipt, applied_at=coordinate(12)), selected.effect.observed[1])


def test_acceptance_application_and_observed_result_remain_distinct(tmp_path):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        accepted = selected.a.execute(op, payload)
        assert accepted.disposition == 'ACCEPTED' and accepted.receipt.applied_at is None
        selected.effect.observed = LiveEffectReceipt(op.identity, LiveEffectStage.APPLIED,
            coordinate(10), coordinate(11), None, None), None
        assert selected.owner.reconcile(op.request_id).disposition == 'APPLIED'
        selected.effect.observed = observed(op)
        assert selected.owner.reconcile(op.request_id).disposition == 'OBSERVED'
        assert len(selected.effect.calls) == 1
        assert op.request_timeout_seconds == Decimal('0.1') and op.scientific_horizon.duration == 40
        assert op.action_expires_at.coordinate == 20


def test_interrupted_segment_publication_is_not_actor_memory_or_complete_history(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        selected.owner.ingest((packet(selected, 1),))
        original = selected.plane.write
        def interrupt(request):
            if request.relative_path.endswith('/segments/0002.json'):
                path = selected.plane.root.resolve(request.relative_path, for_write=True)
                path.write_bytes(request.payload[:32])
                raise OSError('disclosed interrupted member before sidecar')
            return original(request)
        monkeypatch.setattr(selected.plane, 'write', interrupt)
        with pytest.raises(OSError, match='interrupted'):
            selected.owner.ingest((packet(selected, 2),))
        assert selected.owner.scientific_disposition == 'UNEVALUABLE_EVENT_HISTORY'
        assert selected.store.retained_disposition() == 'UNEVALUABLE_EVENT_HISTORY'
        with pytest.raises(LiveRetentionLost):
            selected.a.read((1,), cutoff=cutoff())
        with pytest.raises(ArtifactIdentityConflict):
            selected.store.read_event_window(1, 2)
        with pytest.raises(LiveRetentionLost):
            selected.a.execute(*operation(selected))
        assert not selected.effect.calls


def test_failed_commitment_persistence_prevents_any_contact_or_submission(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        def fail(*args):
            raise OSError('disclosed persistence refusal')
        monkeypatch.setattr(selected.store, 'publish_operation', fail)
        with pytest.raises(OSError, match='persistence'):
            selected.a.execute(op, payload)
        assert not selected.effect.calls and selected.store.read_operation(op.request_id) is None
        assert not tuple((tmp_path / 'custody').glob('runs/**/native-contacts/*.json'))


def test_actual_access_revocation_during_publication_prevents_contact(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        original = selected.store.publish_operation
        def revoke(*args):
            original(*args)
            selected.access.revoked = True
        monkeypatch.setattr(selected.store, 'publish_operation', revoke)
        with pytest.raises(PermissionError, match='revoked'):
            selected.a.execute(op, payload)
        assert not selected.effect.calls and selected.store.read_operation(op.request_id) == op
        assert not selected.store.has_contact(op)
        selected.access.revoked = False


def test_operation_readback_verifies_original_input_payload_custody(tmp_path):
    with case(tmp_path) as selected:
        first = packet(selected, 1)
        selected.owner.ingest((first,))
        op, payload = operation(selected, inputs=(first.observation.identity,))
        selected.a.execute(op, payload)
        path = selected.store._path(selected.store._record_path(first.observation.payload))
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'"value":1', b'"value":9'))
        with pytest.raises((ArtifactIdentityConflict, ValueError)):
            selected.store.read_operation(op.request_id)
        assert len(selected.effect.calls) == 1


def test_delayed_event_preserves_times_and_sequence_gap_prevents_scientific_effect(tmp_path):
    with case(tmp_path) as selected:
        first, third = packet(selected, 1, sampled=5, available=9), packet(selected, 3)
        segment = selected.owner.ingest((first, third))
        assert segment.gaps == (LiveSequenceGap(2, 2),)
        assert selected.store.read_segment(1) == segment
        assert not selected.a.read((1, 3), cutoff=cutoff()).complete
        with pytest.raises(LiveRetentionLost, match='gaps'):
            selected.a.execute(*operation(selected, inputs=(third.observation.identity,)))
        assert first.observation.sampled_at.coordinate == 5 and first.observation.available_at.coordinate == 9


def test_package_replacement_is_durable_while_inflight_work_keeps_original_package(tmp_path):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        entered, release = Event(), Event()
        results = []
        def before(actual):
            entered.set()
            assert release.wait(5)
        selected.effect.before = before
        selected.effect.observed = observed(op)
        thread = Thread(target=lambda: results.append(selected.a.execute(op, payload)))
        thread.start()
        assert entered.wait(5)
        new_package = FixtureRecord('test.live.package.second', 2)
        selected.owner.replace_package(new_package.identity, new_package.canonical_bytes())
        assert selected.store.read_boundaries(1, 4)[-1].selected == new_package.identity
        release.set()
        thread.join(5)
        assert not thread.is_alive() and results[0].operation.package == selected.package.identity
        with pytest.raises(PermissionError, match='package'):
            selected.a.execute(*operation(selected, name='request.second'))
        assert len(selected.effect.calls) == 1


def test_native_guard_enforces_expiry_and_session_generation_after_queue_delay(tmp_path):
    with case(tmp_path) as selected:
        op, _ = operation(selected)
        for time in (9, 20, 100):
            with pytest.raises(PermissionError, match='schedule'):
                require_live_application(op, session=selected.session, current_lease=selected.a.lease, at=coordinate(time))
        with pytest.raises(PermissionError, match='stale'):
            require_live_application(op, session=replace(selected.session, source_generation=2),
                current_lease=selected.a.lease, at=coordinate(11))
        with pytest.raises(ValueError, match='clock mapping'):
            selected.session.coordinate(replace(coordinate(11), clock_id='unmapped.clock'))


def test_existing_explicit_clock_transport_preserves_exact_decimal_and_refuses_bounded_alignment(tmp_path):
    from empirical_lawhood.science.models.time import ClockTransportKind
    from tests.kernel.test_time_validation import _coordinate, _transport
    with case(tmp_path) as selected:
        mapping = replace(_transport(), target_clock_id='test.live.clock', target_time_unit='tick',
            target_coordinate_frame='source', kind=ClockTransportKind.AFFINE_EXACT, tolerance=Decimal(0))
        session = replace(selected.session, clock_transports=(mapping,))
        with localcontext() as context:
            context.prec = 2
            assert session.coordinate(replace(_coordinate(), coordinate=Decimal('1.23456789'))) == Decimal('3.46913578')
        bounded = replace(mapping, kind=ClockTransportKind.AFFINE_BOUNDED, tolerance=Decimal('0.01'))
        with pytest.raises(ValueError, match='exact clock mapping'):
            replace(session, clock_transports=(bounded,)).coordinate(_coordinate())
        with pytest.raises(ValueError, match='exact clock mapping'):
            session.coordinate(replace(_coordinate(), coordinate=Decimal(11)))


def test_bounded_windows_batches_backpressure_and_owner_reacquisition(tmp_path):
    with case(tmp_path) as selected:
        with pytest.raises(ValueError, match='bounded'):
            selected.a.read((1, 2, 3, 4), cutoff=cutoff())
        with pytest.raises(ValueError, match='bounded batch'):
            selected.owner.ingest(tuple(packet(selected, index) for index in range(1, 10)))
        ready, release = Event(), Event()
        def held():
            with selected.owner._lock:
                ready.set()
                assert release.wait(5)
        thread = Thread(target=held)
        thread.start()
        assert ready.wait(5)
        try:
            with pytest.raises(LiveBackpressure):
                selected.owner.ingest((packet(selected, 1),))
        finally:
            release.set()
            thread.join(5)
        other = ExternalContinuingSourceStore(plane=selected.plane, session=selected.session, relative_root='selected/live')
        with pytest.raises(BlockingIOError):
            with other.owner_lock():
                pytest.fail('two live lifecycle owners')
    with other.owner_lock():
        with pytest.raises(PermissionError, match='historical'):
            other.initialize(selected.package.identity, selected.package.canonical_bytes())


@pytest.mark.parametrize('change', ('delay', 'privileged', 'foreign-parent', 'future'))
def test_information_contract_refusals_precede_retention_and_actor_visibility(tmp_path, change):
    with case(tmp_path) as selected:
        selected.owner.ingest((packet(selected, 1, selected.b),))
        value = packet(selected, 2)
        if change == 'delay':
            value = packet(selected, 2, sampled=1)
        elif change == 'privileged':
            value = replace(value, observation=replace(value.observation,
                availability=replace(value.observation.availability, outcome_access=OutcomeAccess.PRIVILEGED_TRUTH)))
        elif change == 'foreign-parent':
            value = packet(selected, 2, parents=(packet(selected, 1, selected.b).observation.identity,))
        else:
            value = packet(selected, 2, available=11)
        with pytest.raises(PermissionError):
            selected.owner.ingest((value,))
        assert selected.a.read((2,), cutoff=cutoff()).missing_sequences == (2,)
        assert selected.owner.last_event_sequence == 1
