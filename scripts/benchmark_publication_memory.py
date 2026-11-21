#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Measure canonical publication scaling and active-reader lifetime, without science.

The same script runs against both checkouts via --repo. Publication timings include
the complete current publication owner, but exclude request construction. The
memory pass uses actual authored member readers and file/access guards; it adds no
synthetic payload padding. Tracemalloc is enabled only in the separate memory pass.
"""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import json
from pathlib import Path
import resource
import statistics
import sys
import tempfile
import time
import tracemalloc
from weakref import ref


def io_counters():
    return {key: int(value.strip()) for key, value in
        (line.split(':', 1) for line in Path('/proc/self/io').read_text().splitlines())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--counts', type=int, nargs='+', default=(16, 64, 256))
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--readers', type=int, default=16)
    parser.add_argument('--reader-members', type=int, default=64)
    args = parser.parse_args()
    root = args.repo.resolve(strict=True)
    sys.path[:0] = [str(root / 'src'), str(root)]
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.recursive_custody import AuthenticatedRecursivePayloads
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
    from empirical_lawhood.execution.recursive_handoff import RecursiveWaveMember

    def inputs(count):
        records = tuple(ObjectIdentity(f'exposed.subject.{number}', ObjectIdentity.SCHEMA,
            '1.0.0', 'a' * 64) for number in range(count))
        requests = tuple(ArtifactWriteRequest(f'exposed.member.{number}', f'outputs/member-{number}.json',
            ObjectIdentity.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
            'exposed.complete-batch', 'outputs', record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
            for number, record in enumerate(records))
        members = tuple(RecursiveWaveMember(f'member-{number}.json',
            ObjectIdentity.from_record(f'selected.member.{number}', record), len(record.canonical_bytes()))
            for number, record in enumerate(records))
        return requests, members

    def plane_at(directory):
        directory.mkdir()
        mount = next(parent for parent in directory.parents if parent.is_mount())
        return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
            'exposed.publication-memory', 'Software publication and memory probe', str(directory),
            str(mount), 'empirical-lawhood/testing/publication-memory', 1)))

    def published_metrics(plane, results):
        root_path = Path(plane.root.contract.canonical_path)
        sidecars = tuple(root_path / value.manifest_materialization.relative_path for value in results)
        schemas = sorted({json.loads(path.read_bytes())['schema'] for path in sidecars})
        payload_roster = tuple((value.logical.logical_artifact_id, value.materialization.relative_path,
            value.logical.content_sha256, value.materialization.physical_sha256,
            value.materialization.size_bytes) for value in results)
        physical_roster = [(path.relative_to(root_path).as_posix(), path.stat().st_size,
            sha256(path.read_bytes()).hexdigest()) for path in (*sidecars, *root_path.rglob('*.commit.json'))]
        return {'sidecar_bytes': sum(path.stat().st_size for path in sidecars),
            'physical_sidecar_schemas': schemas,
            'payload_content_roster_sha256': sha256(json.dumps(payload_roster, separators=(',', ':')).encode()).hexdigest(),
            'physical_metadata_roster_sha256': sha256(json.dumps(sorted(physical_roster), separators=(',', ':')).encode()).hexdigest(),
            'logical_records_sha256': sha256(b''.join(value.logical.canonical_bytes() for value in results)).hexdigest(),
            'commit_bytes': sum(path.stat().st_size for path in root_path.rglob('*.commit.json'))}

    output = {'label': args.label, 'python': sys.version, 'repo': str(root),
        'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_sha256': {name: sha256((root / 'src/empirical_lawhood' / name).read_bytes()).hexdigest()
            for name in ('storage/artifacts.py', 'storage/artifact_validation.py', 'storage/artifact_sidecars.py',
                'storage/bounded_io.py', 'storage/recursive_custody.py', 'api/recursive_inquiry_read.py')},
        'semantics': 'Exposed canonical ObjectIdentity software records. No native, remote, grant, scientific qualification or molecular computation.',
        'timing_scope': 'Complete default write_batch including final publication checks. Requests and imports excluded. Fresh filesystem directories, warm operating-system caches; tracemalloc disabled.',
        'memory_scope': 'Actual AuthenticatedRecursivePayloads readers in one live read_context; no synthetic metadata padding. Optional metadata caches not used. Final file/access checks remain active.',
        'publication': []}
    with tempfile.TemporaryDirectory(prefix='el-publication-memory-') as directory:
        directory = Path(directory)
        # First call initializes process-local profile metadata before timing.
        warm = plane_at(directory / 'warm')
        warm.write_batch(inputs(1)[0])
        for count in args.counts:
            requests, _ = inputs(count)
            samples = []
            for repetition in range(args.repeats):
                plane = plane_at(directory / f'publication-{count}-{repetition}')
                before_io, before_usage = io_counters(), resource.getrusage(resource.RUSAGE_SELF)
                started = time.perf_counter()
                results = plane.write_batch(requests)
                wall = time.perf_counter() - started
                after_usage, after_io = resource.getrusage(resource.RUSAGE_SELF), io_counters()
                metrics = published_metrics(plane, results)
                replay = plane.write_batch(requests)
                replay_metrics = published_metrics(plane, replay)
                assert all(not value.created for value in replay)
                assert metrics == replay_metrics
                assert tuple(value.manifest_materialization for value in results) == tuple(
                    value.manifest_materialization for value in replay)
                samples.append({'wall_s': wall,
                    'cpu_s': after_usage.ru_utime + after_usage.ru_stime - before_usage.ru_utime - before_usage.ru_stime,
                    'process_rchar_bytes': after_io['rchar'] - before_io['rchar'],
                    'process_wchar_bytes': after_io['wchar'] - before_io['wchar'],
                    'storage_read_bytes': after_io['read_bytes'] - before_io['read_bytes'],
                    'storage_write_bytes': after_io['write_bytes'] - before_io['write_bytes'],
                    'exact_replay_preserved': True, **metrics})
            output['publication'].append({'members': count, 'samples': samples,
                'median': {key: statistics.median(row[key] for row in samples)
                    for key in ('wall_s', 'cpu_s', 'sidecar_bytes', 'commit_bytes',
                        'process_rchar_bytes', 'process_wchar_bytes', 'storage_read_bytes', 'storage_write_bytes')}})

        class Access:
            def __init__(self):
                self.allowed, self.calls = True, 0

            def require_current(self):
                self.calls += 1
                if not self.allowed:
                    raise PermissionError('exposed software access revoked')

            def require_member(self, _manifest):
                self.require_current()

        requests, members = inputs(args.reader_members)
        plane = plane_at(directory / 'readers')
        plane.write_batch(requests)
        access, references, revoked_refused = Access(), [], False
        gc.collect()
        tracemalloc.start()
        start_bytes, _ = tracemalloc.get_traced_memory()
        started = time.perf_counter()
        try:
            with plane.read_context() as reading:
                for _ in range(args.readers):
                    payloads = AuthenticatedRecursivePayloads(plane=reading,
                        directory=Path(plane.root.contract.canonical_path) / 'outputs',
                        members=members, original_input_access=access)
                    references.append(ref(payloads))
                    del payloads
                gc.collect()
                retained_bytes, peak_bytes = tracemalloc.get_traced_memory()
                retained_readers = sum(value() is not None for value in references)
                before_checks = access.calls
                reading.require_full_verification_snapshot()
                final_access_checks = access.calls - before_checks
                # Revocation after consumer references have disappeared must
                # still refuse the enclosing owner's final exit.
                access.allowed = False
        except PermissionError as error:
            if 'exposed software access revoked' not in str(error):
                raise
            revoked_refused = True
        elapsed = time.perf_counter() - started
        gc.collect()
        after_close_bytes, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert revoked_refused and final_access_checks > 0
        output['readers'] = {'readers': args.readers, 'members_per_reader': len(members),
            'live_readers_after_consumer_release': retained_readers,
            'live_readers_after_owner_close': sum(value() is not None for value in references),
            'traced_retained_bytes_above_start': retained_bytes - start_bytes,
            'traced_peak_bytes_above_start': peak_bytes - start_bytes,
            'traced_bytes_after_close_above_start': after_close_bytes - start_bytes,
            'final_access_checks': final_access_checks, 'final_revocation_refused': revoked_refused,
            'wall_s_with_tracemalloc': elapsed}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(args.output), 'publication': [
        {'members': row['members'], **row['median']} for row in output['publication']],
        'readers': output['readers']}, indent=2))


if __name__ == '__main__':
    main()
