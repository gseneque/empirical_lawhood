#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Expose finite ancestry cache work; no native science or qualification.

Run with this checkout and its locked test environment on PYTHONPATH. `prepare`
uses the existing synthetic battery custody fixture, then attaches a disclosed
sparse opaque member to exercise large physical closure admission. `measure`
reads the exact same immutable fixture with the selected source checkout.
"""

import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import resource
import shutil
import time

import pytest

from empirical_lawhood.api import recursive_contributions as owner


def prepare(directory, payload_mib):
    from tests.test_recursive_contribution_custody import portable_a, _read_transport, _refresh_outer_census
    directory.mkdir(parents=True, exist_ok=False)
    with pytest.MonkeyPatch.context() as patch:
        *_, consumer, imported, _ = portable_a.__wrapped__(directory, patch)
    transport = _read_transport(imported)
    remaining, number = payload_mib * 1024**2, 0
    while remaining:
        size = min(remaining, 64 * 1024**2)
        payload = imported / 'custody' / transport.run_relative_path / f'exposed-ancestry-benchmark-{number}.bin'
        with payload.open('wb') as handle:
            handle.truncate(size)
        remaining -= size
        number += 1
    _refresh_outer_census(imported)
    # Distinct physical custody locators; hardlinks only avoid allocating a
    # duplicate opaque fixture body. All benchmark reads are strictly read-only.
    other = imported.with_name('second-imported-a')
    shutil.copytree(imported, other, copy_function=os.link)
    metadata = {'consumer_root': str(consumer.root.contract.canonical_path),
        'first': str(imported), 'second': str(other),
        'opaque_payload_bytes': payload_mib * 1024**2,
        'evidence_role': 'EXPOSED_SYNTHETIC_CUSTODY_CACHE_PROFILE_ONLY',
        'scientific_qualification': 'NOT_PERFORMED', 'native_contact_count': 0}
    (directory / 'fixture.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


def _io():
    path = Path('/proc/self/io')
    return {} if not path.exists() else {key: int(value) for key, value in
        (line.split(': ') for line in path.read_text().splitlines())}


def measure(directory, output, scenarios):
    from tests.test_recursive_projection_lifetime import _stock_plane
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.science.records import decoded_record_store
    from empirical_lawhood.storage.portable_closure import recursive_closure_limits
    from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
    metadata = json.loads((directory / 'fixture.json').read_text())
    root = metadata['consumer_root']
    contract = ExternalRootContract('recursive-software-fixture', 'Exposed test custody', root, root,
        'empirical-lawhood/testing/recursive-custody', 1)
    plane = _stock_plane(ExternalArtifactPlane(GuardedExternalRoot(contract),
        validators=integration_artifact_profile_validators()))
    first, second = Path(metadata['first']), Path(metadata['second'])
    reports = []
    for scenario in scenarios:
        reconstructions, censuses, identities, cache_weights = [], [], [], []
        selected_reader, census_reader = owner._authenticate_selected, owner._custody_members
        def reconstruct(selected, writer, **kwargs):
            reconstructions.append(str(selected))
            return selected_reader(selected, writer, **kwargs)
        def census(root, prefixes):
            censuses.append(str(root))
            return census_reader(root, prefixes)
        def read(path, reading):
            result = owner.authenticate_recursive_contribution(directory=path,
                artifact_writer=plane, include_draft=True)
            identities.append((result[1].fingerprint(), result[2].fingerprint(), result[-1].fingerprint(),
                tuple(sorted((task, output, record.fingerprint())
                    for task, outputs in result[4]['records'].items() for output, record in outputs.items()))))
            cache_weights.append({'entries': len(reading.entries), 'metadata_bytes': reading.bytes,
                'external_closure_bytes': sum(member.size_bytes for member in result[1].members)})
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(owner, '_authenticate_selected', reconstruct)
            patch.setattr(owner, '_custody_members', census)
            if scenario == 'cache_pressure':
                patch.setattr(decoded_record_store, 'MAX_SHARED_RECORDS', 1)
            before_io, before_usage, started = _io(), resource.getrusage(resource.RUSAGE_SELF), time.perf_counter()
            custom = (recursive_closure_limits(RecursiveClosureLimits(maximum_authentications=2,
                maximum_member_bytes=64 * 1024**2, maximum_total_bytes=1024**3,
                maximum_hashed_bytes=8 * 1024**3))
                if scenario == 'explicit_traversal' else nullcontext())
            with custom, owner.recursive_contribution_read_context() as reading:
                if scenario == 'fanout':
                    for _ in range(3):
                        read(first, reading)
                elif scenario == 'nested_owner':
                    read(first, reading)
                    with owner.recursive_contribution_read_context() as nested:
                        assert nested is reading
                        read(first, nested)
                elif scenario in ('multiple_copies', 'cache_pressure'):
                    for path in (first, second, first):
                        read(path, reading)
                elif scenario == 'explicit_traversal':
                    read(first, reading)
                    read(first, reading)
                    with pytest.raises(ValueError, match='depth or authentication bound'):
                        read(first, reading)
                else:
                    raise ValueError('unknown profile scenario')
                before_final = time.perf_counter()
            elapsed, after_io, after_usage = time.perf_counter() - started, _io(), resource.getrusage(resource.RUSAGE_SELF)
            assert not reading.active and not reading.entries and reading.bytes == 0
        assert all(identity == identities[0] for identity in identities)
        reports.append({'scenario': scenario, 'elapsed_seconds': elapsed,
            'consumer_seconds': before_final - started, 'final_guard_seconds': elapsed - (before_final - started),
            'process_cpu_seconds': (after_usage.ru_utime + after_usage.ru_stime)
                - (before_usage.ru_utime + before_usage.ru_stime),
            'peak_rss_bytes': after_usage.ru_maxrss * 1024,
            'process_io_delta': {key: after_io[key] - value for key, value in before_io.items()},
            'reconstruction_count': len(reconstructions), 'closure_census_count': len(censuses),
            'cache_observations': cache_weights,
            'unchanged_scientific_identities': identities[0], 'final_owner_released': True})
        result = {'source_module': owner.__file__, 'fixture': metadata, 'profiles': reports}
        output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'source_module': owner.__file__,
        'profiles': [{key: row[key] for key in ('scenario', 'elapsed_seconds', 'reconstruction_count',
            'closure_census_count', 'final_guard_seconds')} for row in reports]}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'measure'))
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--payload-mib', type=int, default=600)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--scenarios', nargs='+', default=('fanout', 'nested_owner',
        'multiple_copies', 'cache_pressure', 'explicit_traversal'))
    arguments = parser.parse_args()
    if arguments.mode == 'prepare':
        print(json.dumps(prepare(arguments.fixture, arguments.payload_mib), indent=2), flush=True)
    else:
        if arguments.output is None:
            parser.error('--output is required for measurement')
        measure(arguments.fixture, arguments.output, arguments.scenarios)
