# SPDX-License-Identifier: MPL-2.0
"""Exposed two-actor counter process for continuing-source software acceptance.

This is a finite software fixture. It does not implement a scientific simulator,
Quake, a real-time guarantee, an investigator algorithm or qualification.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import select
import subprocess
import sys
from threading import Lock
import time
from typing import ClassVar

from empirical_lawhood.science.inquiry.continuing_source import ContinuingSourceSession, FiniteLiveOperation, LiveActorLease, LiveEffectReceipt, LiveEffectStage, LiveObservation, LiveScientificWindow
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.models.time import AvailabilitySpec, CausalPhase, ClockCoordinate, ClockLabelSemantics, ClockSpec, CoordinateOrigin, HoldSemantics, HorizonSpec, InformationCutoff, SamplingSemantics
from empirical_lawhood.execution.continuing_source import LiveObservationPacket, require_live_application


MAX_MESSAGE_BYTES = 256 * 1024


@dataclass(frozen=True, slots=True)
class CounterRecord(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/examples/continuing-counter-record'
    record_id: str
    kind: str
    value: int

    def __post_init__(self):
        from empirical_lawhood.science.records.serialization import validate_stable_id
        validate_stable_id(self.record_id)
        if self.kind not in ('source', 'package', 'sample', 'increment', 'held', 'expired', 'lost-reply', 'result'):
            raise ValueError('counter fixture record kind is unsupported')
        if type(self.value) is not int or abs(self.value) > 1_000_000:
            raise ValueError('counter fixture integer exceeds its bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def tick(value):
    return ClockCoordinate('counter.native-tick', Decimal(value), 'tick', 'counter-process', CoordinateOrigin.EPISODE_RELATIVE)


def encoded(record):
    return record.canonical_bytes().decode('utf-8')


def decode(raw, kind):
    return decode_canonical_bytes(raw.encode('utf-8'), kind, maximum_bytes=MAX_MESSAGE_BYTES)


def worker():
    """An independently advancing, bounded external source with no unsolicited queue."""
    started = time.monotonic_ns()
    session = None
    leases, offsets, outcomes, pending = {}, {}, {}, {}
    native_apply_count, processing_ns, commands = 0, 0, 0

    def current_tick():
        return (time.monotonic_ns() - started) // 10_000_000

    def apply(operation, prepared, accepted):
        nonlocal native_apply_count, processing_ns
        begin = time.process_time_ns()
        actual = tick(current_tick())
        try:
            require_live_application(operation, session=session,
                current_lease=leases[operation.actor_lease.actor_id], at=actual)
        except PermissionError as error:
            reason = 'stale-native-generation' if 'stale' in str(error) else 'effect-expired'
            result = LiveEffectReceipt(operation.identity, LiveEffectStage.REFUSED, accepted,
                None, None, None, (reason,))
            payload = None
        else:
            actor = operation.actor_lease.actor_id
            offsets[actor] += prepared.value
            native_apply_count += 1
            value = CounterRecord('counter.result.' + operation.request_id, 'result', current_tick() + offsets[actor])
            result = LiveEffectReceipt(operation.identity, LiveEffectStage.OBSERVED,
                accepted, actual, actual, value.identity)
            payload = encoded(value)
        outcomes[operation.request_id] = (encoded(result), payload)
        processing_ns += time.process_time_ns() - begin

    while time.monotonic_ns() - started < 120_000_000_000:
        for request_id, (operation, prepared, accepted, due) in tuple(pending.items()):
            if due is not None and current_tick() >= due:
                apply(operation, prepared, accepted)
                del pending[request_id]
        if not select.select([sys.stdin.buffer], [], [], 0.01)[0]:
            continue
        raw = sys.stdin.buffer.readline(MAX_MESSAGE_BYTES + 1)
        if not raw:
            return 0
        if len(raw) > MAX_MESSAGE_BYTES or not raw.endswith(b'\n'):
            raise ValueError('counter request exceeds its bounded line protocol')
        message = json.loads(raw)
        commands += 1
        if commands > 256:
            raise ValueError('counter fixture command census exhausted')
        command, answer, suppress = message['command'], None, False
        if command == 'initialize':
            if session is not None:
                raise ValueError('counter source cannot be initialized twice')
            session = decode(message['session'], ContinuingSourceSession)
            for raw_lease in message['leases']:
                lease = decode(raw_lease, LiveActorLease)
                leases[lease.actor_id] = lease
                offsets[lease.actor_id] = 0
            answer = {'initialized': True}
        elif command == 'state':
            actual = current_tick()
            answer = {'tick': actual, 'values': {actor: actual + value for actor, value in offsets.items()},
                'native_apply_count': native_apply_count, 'pending': len(pending),
                'processing_cpu_ns': processing_ns, 'whole_worker_cpu_ns': time.process_time_ns()}
        elif command == 'lease':
            lease = decode(message['lease'], LiveActorLease)
            previous = leases[lease.actor_id]
            if (lease.session != session.identity or lease.generations == previous.generations
                    or any(new < old for new, old in zip(lease.generations, previous.generations, strict=True))):
                raise ValueError('counter replacement is not an actual new source generation')
            leases[lease.actor_id] = lease
            answer = {'selected': lease.fingerprint()}
        elif command == 'submit':
            operation = decode(message['operation'], FiniteLiveOperation)
            prepared = decode(message['prepared'], CounterRecord)
            if operation.prepared_commitment != prepared.identity or abs(prepared.value) > 10:
                raise ValueError('counter command changes its original prepared integer')
            if operation.request_id in outcomes:
                # Native dedup is an additional boundary. The parent exercise
                # also verifies that its own custody never resends this request.
                answer = outcomes[operation.request_id]
            elif len(outcomes) >= 32 or len(pending) >= 4:
                raise ValueError('counter finite result or pending queue is exhausted')
            else:
                accepted = tick(current_tick())
                receipt = LiveEffectReceipt(operation.identity, LiveEffectStage.ACCEPTED,
                    accepted, None, None, None)
                outcomes[operation.request_id] = (encoded(receipt), None)
                if prepared.kind in ('held', 'expired'):
                    due = None if prepared.kind == 'held' else int(operation.action_expires_at.coordinate) + 1
                    pending[operation.request_id] = operation, prepared, accepted, due
                else:
                    apply(operation, prepared, accepted)
                answer = outcomes[operation.request_id]
                suppress = prepared.kind == 'lost-reply'
        elif command == 'release':
            operation, prepared, accepted, _ = pending.pop(message['request_id'])
            apply(operation, prepared, accepted)
            answer = {'released': True}
        elif command == 'observe':
            answer = outcomes.get(message['request_id'])
        elif command == 'stop':
            answer = {'tick': current_tick(), 'native_apply_count': native_apply_count,
                'pending': len(pending), 'processing_cpu_ns': processing_ns,
                'whole_worker_cpu_ns': time.process_time_ns(), 'commands': commands}
        else:
            raise ValueError('unknown counter command')
        if not suppress:
            response = (json.dumps({'sequence': message['sequence'], 'answer': answer}, separators=(',', ':')) + '\n').encode()
            if len(response) > MAX_MESSAGE_BYTES:
                raise ValueError('counter response exceeds its bounded line protocol')
            sys.stdout.buffer.write(response)
            sys.stdout.buffer.flush()
        if command == 'stop':
            return 0
    raise TimeoutError('counter fixture exceeded its independent 120-second lifetime')


class CounterPort:
    def __init__(self, output):
        self.stderr = (output / 'source.stderr.txt').open('xb')
        self.process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--worker'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, bufsize=0, start_new_session=True)
        self.sequence, self.submissions, self.requests = 0, 0, []
        self.lock = Lock()

    def rpc(self, command, *, timeout=10, **values):
        with self.lock:
            self.sequence += 1
            raw = (json.dumps({'sequence': self.sequence, 'command': command, **values}, separators=(',', ':')) + '\n').encode()
            if len(raw) > MAX_MESSAGE_BYTES:
                raise ValueError('counter parent request exceeds its bound')
            started = time.monotonic_ns()
            self.process.stdin.write(raw)
            self.process.stdin.flush()
            try:
                if not select.select([self.process.stdout], [], [], timeout)[0]:
                    raise TimeoutError('counter source reply not received; do not repeat effect')
                response = self.process.stdout.readline(MAX_MESSAGE_BYTES + 1)
                if not response or len(response) > MAX_MESSAGE_BYTES or not response.endswith(b'\n'):
                    raise RuntimeError('counter source ended or returned an unbounded response')
                decoded = json.loads(response)
                if decoded['sequence'] != self.sequence:
                    raise RuntimeError('counter source substituted response sequence')
                return decoded['answer']
            finally:
                self.requests.append({'command': command, 'elapsed_ns': time.monotonic_ns() - started})

    @staticmethod
    def _receipt(answer):
        if answer is None:
            return None
        receipt, payload = answer
        return decode(receipt, LiveEffectReceipt), None if payload is None else payload.encode()

    def submit(self, operation, prepared_payload):
        self.submissions += 1
        return self._receipt(self.rpc('submit', operation=encoded(operation), prepared=prepared_payload.decode(),
            timeout=float(operation.request_timeout_seconds)))

    def observe(self, operation):
        return self._receipt(self.rpc('observe', request_id=operation.request_id))

    def clock(self):
        return tick(self.rpc('state')['tick'])

    def close(self):
        try:
            final = self.rpc('stop') if self.process.poll() is None else None
            self.process.wait(timeout=10)
            return final
        finally:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
            self.stderr.close()


class ExposedCounterAccess:
    """Fixture-only actual local pipe ownership; no issue or scientific grant."""

    def __init__(self, session, leases):
        self.session, self.leases, self.active = session, {lease.actor_id: lease for lease in leases}, True

    def require_owner(self, session):
        if not self.active or session != self.session:
            raise PermissionError('counter fixture has no current local source ownership')

    def require_actor(self, lease, *, effect_key):
        self.require_owner(self.session)
        if self.leases.get(lease.actor_id) != lease or (effect_key is not None and effect_key not in lease.effect_keys):
            raise PermissionError('counter fixture actor is not currently authorized')


def exercise(*, project_root, operator_profile, output_directory):
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.application_contracts import ApplicationContext
    from empirical_lawhood.api.continuing_source import open_continuing_source, read_continuing_operation
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.storage.continuing_source import ExternalContinuingSourceStore
    from empirical_lawhood.execution.continuing_source import LiveRetentionLost

    root = Path(project_root).resolve(strict=True)
    _, _, plane = application_storage(ApplicationContext(context_id='continuing-counter.example',
        label='Exposed continuing counter fixture', python_executable=Path(sys.executable), project_root=root,
        operator_profile=Path(operator_profile)), for_write=True)
    output = Path(output_directory)
    if not output.is_absolute():
        raise ValueError('counter fixture requires an explicit absolute output directory')
    relative = output.relative_to(plane.root.contract.canonical_path).as_posix()
    output = plane.root.resolve(relative, for_write=True)
    if output.exists():
        raise FileExistsError('counter fixture requires a new output directory')
    output.mkdir(parents=True)
    source_identity = implementation_binding(root)
    (output / 'original-source.json').write_bytes(source_identity.canonical_bytes())
    source = CounterRecord('counter.source', 'source', 1)
    package = CounterRecord('counter.package.a', 'package', 1)
    clock = ClockSpec('counter.native-tick', 'Autonomous software counter', 'tick', 'counter-process',
        SamplingSemantics.REGULAR, HoldSemantics.ZERO_ORDER, ClockLabelSemantics.INSTANT, Decimal(1))
    session = ContinuingSourceSession('counter.session.' + sha256(str(output).encode()).hexdigest(),
        source.identity, source.identity, 'counter.single-owner', 1, clock, CoordinateOrigin.EPISODE_RELATIVE, (),
        VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, 2, 32, 4, 8)
    a_lease = LiveActorLease(session.identity, 'actor.a', 1, 1, 1, tick(50_000), ('state',), ('increment',),
        2, 2, Decimal(10_000), Decimal(10_000))
    b_lease = replace(a_lease, actor_id='actor.b')
    access = ExposedCounterAccess(session, (a_lease, b_lease))
    port, measurements, checks = CounterPort(output), [], {}
    persistence_ns = [0]
    write = plane.write
    def measured_write(request):
        began = time.monotonic_ns()
        try:
            return write(request)
        finally:
            persistence_ns[0] += time.monotonic_ns() - began
    plane.write = measured_write

    def timed(name, callback):
        begin = time.monotonic_ns()
        try:
            return callback()
        finally:
            measurements.append({'name': name, 'elapsed_ns': time.monotonic_ns() - begin})

    def sample(actor, sequence, original=None):
        state = original or port.rpc('state')
        now = port.clock()
        payload = CounterRecord(f'counter.sample.{sequence}', 'sample', state['values'][actor.lease.actor_id])
        observation = LiveObservation(session.identity, sequence, actor.lease.identity, 'state', tick(state['tick']),
            tick(state['tick']), now, AvailabilitySpec(clock.clock_id, CausalPhase.PRE_ACTION,
                session.outcome_access, now.coordinate), tick(now.coordinate + 10_000), payload.identity)
        return LiveObservationPacket(observation, payload.canonical_bytes())

    def operation(actor, name, *, kind='increment', package_ref=package.identity, expiry=5000):
        now = port.clock()
        prepared = CounterRecord('counter.command.' + name, kind, 1)
        window = LiveScientificWindow('counter.window.' + name, session.identity, session.dependence_root, tick(0), tick(50_000))
        cutoff = InformationCutoff('counter.cutoff.' + name, clock.clock_id, CausalPhase.PRE_ACTION, now.coordinate)
        value = FiniteLiveOperation(name, 'counter.run.' + session.fingerprint(), window, actor.lease, package_ref, prepared.identity,
            'increment', (), cutoff, now, now, tick(now.coordinate + expiry),
            HorizonSpec('counter.horizon.' + name, clock.clock_id, Decimal(200), 'tick'),
            Decimal('0.1') if kind == 'lost-reply' else Decimal(10), source_identity.observed_git_head)
        return value, prepared.canonical_bytes()

    try:
        port.rpc('initialize', session=encoded(session), leases=[encoded(a_lease), encoded(b_lease)])
        with open_continuing_source(session=session, artifact_plane=plane, relative_root=relative + '/history',
                package=package.identity, package_payload=package.canonical_bytes(), clock=port.clock,
                effect_ports={'increment': port}, current_access=access) as owner:
            a, b = owner.bind_actor(a_lease), owner.bind_actor(b_lease)
            before = port.rpc('state')
            time.sleep(0.15)  # Explicit client stall; source advances without a request.
            after = port.rpc('state')
            assert after['tick'] > before['tick']
            checks['source_continues_during_client_stall'] = [before['tick'], after['tick']]
            first, second = sample(a, 1, before), sample(b, 2)
            timed('event_persistence', lambda: owner.ingest((first, second)))
            cut = InformationCutoff('counter.current-cutoff', clock.clock_id, CausalPhase.PRE_ACTION, port.clock().coordinate)
            assert a.read((1, 2), cutoff=cut).missing_sequences == (2,)
            assert b.read((1, 2), cutoff=cut).missing_sequences == (1,)
            checks['separate_actor_views_and_delayed_availability'] = True
            def inquiry():
                begin = time.monotonic_ns()
                view = a.read((1,), cutoff=cut)
                result = sum(decode(packet.payload.decode(), CounterRecord).value for packet in view.packets)
                return {'elapsed_ns': time.monotonic_ns() - begin, 'input_sequences': [1], 'sum': result,
                    'complete': view.complete, 'scientific_qualification': False}
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(inquiry)
                port.rpc('state')
                inquiry_result = future.result(timeout=10)
            assert inquiry_result['complete']

            op, body = operation(a, 'counter.lost', kind='lost-reply')
            unknown = timed('lost_reply_control_request', lambda: a.execute(op, body))
            assert unknown.disposition == 'UNKNOWN_EFFECT_DO_NOT_REPEAT'
            count = port.submissions
            assert a.execute(op, body).disposition == 'UNKNOWN_EFFECT_DO_NOT_REPEAT' and port.submissions == count
            recovered = timed('read_only_reconciliation', lambda: owner.reconcile(op.request_id))
            assert recovered.disposition == 'OBSERVED'
            checks['lost_reply_no_repeat'] = True

            pending, body = operation(a, 'counter.stale', kind='held')
            assert a.execute(pending, body).disposition == 'ACCEPTED'
            new_lease = replace(a.lease, life_generation=2)
            port.rpc('lease', lease=encoded(new_lease))
            access.leases[new_lease.actor_id] = new_lease
            fresh = owner.bind_actor(new_lease)
            try:
                a.read((1,), cutoff=cut)
            except PermissionError:
                checks['stale_actor_handle_refused'] = True
            else:
                raise AssertionError('old actor handle survived life replacement')
            port.rpc('release', request_id=pending.request_id)
            refused = owner.reconcile(pending.request_id)
            assert refused.disposition == 'REFUSED' and refused.receipt.applied_at is None
            checks['native_stale_effect_refused_after_acceptance'] = True

            expired, body = operation(b, 'counter.expired', kind='expired', expiry=50)
            assert b.execute(expired, body).disposition == 'ACCEPTED'
            until = time.monotonic() + 5
            while port.clock().coordinate <= expired.action_expires_at.coordinate and time.monotonic() < until:
                time.sleep(0.02)
            assert owner.reconcile(expired.request_id).disposition == 'REFUSED'
            checks['native_action_expiry_distinct_from_request_timeout'] = True

            held, body = operation(b, 'counter.old-package', kind='held')
            assert b.execute(held, body).disposition == 'ACCEPTED'
            replacement = CounterRecord('counter.package.b', 'package', 2)
            owner.replace_package(replacement.identity, replacement.canonical_bytes())
            port.rpc('release', request_id=held.request_id)
            completed = owner.reconcile(held.request_id)
            assert completed.disposition == 'OBSERVED' and completed.operation.package == package.identity
            checks['inflight_original_package_preserved'] = True

            third, fourth, fifth = sample(fresh, 3), sample(fresh, 4), sample(fresh, 5)
            owner.ingest((third, fourth, fifth))
            cut = replace(cut, coordinate=port.clock().coordinate)
            assert fresh.read((3,), cutoff=cut).missing_sequences == (3,)
            checks['memory_eviction_without_ledger_read'] = True
            retained = read_continuing_operation(session=session, artifact_plane=plane,
                relative_root=relative + '/history', request_id=held.request_id, current_access=access)
            assert retained == completed

            # Actual partial segment publication exercises the ordinary artifact
            # reader, while the independently owned source keeps advancing.
            original_write = plane.write
            def interrupted(request):
                if '/segments/0003.json' in request.relative_path:
                    path = plane.root.resolve(request.relative_path, for_write=True)
                    path.write_bytes(request.payload[:32])
                    raise OSError('exposed fixture interrupted segment publication')
                return original_write(request)
            plane.write = interrupted
            before = port.rpc('state')['tick']
            try:
                owner.ingest((sample(fresh, 6),))
            except OSError:
                pass
            else:
                raise AssertionError('interrupted source segment was accepted')
            try:
                fresh.read((4, 5), cutoff=replace(cut, coordinate=port.clock().coordinate))
            except LiveRetentionLost:
                pass
            else:
                raise AssertionError('partial event history remained scientifically usable')
            time.sleep(0.05)
            after = port.rpc('state')['tick']
            assert after > before and owner.scientific_disposition == 'UNEVALUABLE_EVENT_HISTORY'
            checks['source_continues_after_retention_failure'] = [before, after]
            plane.write = original_write
        final = port.close()
        access.active = False
        store = ExternalContinuingSourceStore(plane=plane, session=session, relative_root=relative + '/history')
        assert store.retained_disposition() == 'UNEVALUABLE_EVENT_HISTORY'
        assert final['native_apply_count'] == 2 and port.submissions == 4 and final['pending'] == 0
        report = {'status': 'PASS', 'evidence_scope': 'EXPOSED_SOFTWARE_FIXTURE',
            'scientific_acquisitions': 0, 'scientific_qualification': 'NOT_ESTABLISHED',
            'source_processes': 1, 'actors': 2, 'finite_requests': 4, 'actual_counter_applications': 2,
            'checks': checks, 'session': session.to_document(), 'source_snapshot_sha256': source_identity.fingerprint(),
            'source_processing': final, 'control_measurements': measurements,
            'persistence_elapsed_ns': persistence_ns[0], 'asynchronous_inquiry': inquiry_result,
            'transport_requests': port.requests,
            'measurement_scope': 'Source processing CPU is a subset of whole-worker CPU. Control elapsed includes publication and transport; persistence elapsed overlaps it. Do not add these elapsed measurements. No whole-tree peak or bill is inferred.',
            'retained_disposition': store.retained_disposition()}
        (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        return {'status': 'PASS', 'output_directory': str(output), 'report': str(output / 'report.json'),
            'session_directory': str(plane.root.resolve(store.relative_root, for_write=False)),
            'counter_applications': 2, 'scientific_acquisitions': 0, 'qualification': 'NOT_ESTABLISHED'}
    finally:
        if port.process.poll() is None:
            port.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--operator-profile', type=Path)
    parser.add_argument('--output-directory', type=Path)
    args = parser.parse_args()
    if args.worker:
        return worker()
    if any(value is None for value in (args.project_root, args.operator_profile, args.output_directory)):
        parser.error('select project root, operator profile and a new output directory')
    print(json.dumps(exercise(project_root=args.project_root, operator_profile=args.operator_profile,
        output_directory=args.output_directory), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
