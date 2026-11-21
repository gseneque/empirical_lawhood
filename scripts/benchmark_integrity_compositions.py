#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Bounded public preparation and real local custody compositions; no native work.

Run in a fresh interpreter with --repo pointing to the exact checkout. Timed
samples exclude fixture construction, imports and profiling. Counter passes are
separate, so their tracing overhead is never included in the timing comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import statistics
import sys
import tempfile
import time


def io_counters():
    try:
        return {k: int(v.strip()) for k, v in
                (line.split(':', 1) for line in Path('/proc/self/io').read_text().splitlines())}
    except (FileNotFoundError, PermissionError):
        return {}


def sample(callback, repeats):
    rows = []
    for _ in range(repeats):
        before_io = io_counters()
        before_self = resource.getrusage(resource.RUSAGE_SELF)
        before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        value = callback()
        wall = time.perf_counter() - start
        after_self = resource.getrusage(resource.RUSAGE_SELF)
        after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
        after_io = io_counters()
        rows.append({'wall_s': wall,
                     'cpu_self_s': after_self.ru_utime + after_self.ru_stime - before_self.ru_utime - before_self.ru_stime,
                     'cpu_waited_children_s': after_child.ru_utime + after_child.ru_stime - before_child.ru_utime - before_child.ru_stime,
                     'process_rchar_bytes': after_io.get('rchar', 0) - before_io.get('rchar', 0),
                     'storage_read_bytes': after_io.get('read_bytes', 0) - before_io.get('read_bytes', 0),
                     'process_high_water_rss_kib': after_self.ru_maxrss,
                     'result': value})
    return {'samples': rows, 'median': {key: statistics.median(row[key] for row in rows)
             for key in ('wall_s', 'cpu_self_s', 'cpu_waited_children_s', 'process_rchar_bytes', 'storage_read_bytes')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    root = args.repo.resolve(strict=True)
    sys.path[:0] = [str(root / 'src'), str(root)]
    from tests.runtime_platform.test_artifact_verification_scope import _publication
    from tests.test_artifact_read_context import _work
    from tests.test_experiment_preparation_public import _specification
    from empirical_lawhood.api.experiment_preparation import prepare_experiment, experiment_preparation_report
    from empirical_lawhood.storage import artifacts
    from empirical_lawhood.science.records import serialization

    result = {'label': args.label, 'python': sys.version, 'repo': str(root),
              'modules': {'artifacts': artifacts.__file__, 'serialization': serialization.__file__},
              'semantics': 'Exposed software workloads. No native acquisition, outcome access, remote connection or qualification.',
              'timing': 'Three fresh finite owners per sample group; filesystem cache not controlled. rchar is process-read traffic, not physical disk or network bytes. RSS is cumulative process high water.',
              'scenarios': []}
    for members, physical_form in ((8, 'expanded'), (64, 'expanded'), (8, 'compact'), (64, 'compact')):
        with tempfile.TemporaryDirectory(prefix='el-integrity-custody-') as directory:
            plane, manifests = _publication(Path(directory), members)
            if physical_form == 'expanded':
                # Explicit closed-record software fixture. Production writes
                # only references; this creates no alternative writer route.
                for manifest in manifests:
                    plane.root.resolve(manifest.materialization.relative_path + '.manifest.json',
                        for_write=False).write_bytes(manifest.canonical_bytes())
            identity = hashlib.sha256(b''.join(value.logical.canonical_bytes() for value in manifests)).hexdigest()
            sidecar_bytes = sum(plane.root.resolve(value.materialization.relative_path + '.manifest.json', for_write=False).stat().st_size
                                for value in manifests)
            for mode in ('separate-owners', 'shared-read-owner'):
                def run():
                    if mode == 'separate-owners':
                        for _ in range(3):
                            plane.verify_manifests(manifests)
                    else:
                        with plane.read_context() as reading:
                            for _ in range(3):
                                reading.verify_manifests(manifests)
                    return {'logical_records_sha256': identity, 'members': members, 'consumers': 3}
                measured = sample(run, args.repeats)
                with _work() as counts:
                    run()
                result['scenarios'].append({'name': 'publication-' + physical_form + '-' + mode, 'members': members,
                    'physical_form': physical_form, 'sidecar_bytes': sidecar_bytes,
                    'consumers': 3, 'work_counts': dict(counts), **measured})
    for alternative in (False, True):
        specification = _specification(alternative)
        def prepare():
            report = experiment_preparation_report(prepare_experiment(specification))
            assert report['native_contact'] == 'NONE' and report['scientific_execution_performed'] is False
            assert report['scientific_authority'] == 'NONE' and report['executable'] is False
            raw = json.dumps(report, sort_keys=True, separators=(',', ':')).encode()
            return {'report_sha256': hashlib.sha256(raw).hexdigest(), 'dependencies': len(report['dependencies']),
                    'roles': report['census']['roles']}
        result['scenarios'].append({'name': 'declarative-preparation-' + ('exposed12-20-8' if alternative else 'selected64'),
                                    **sample(prepare, args.repeats)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(args.output), 'scenarios': [
        {'name': row['name'], 'members': row.get('members'), **row['median']} for row in result['scenarios']]}, indent=2))


if __name__ == '__main__':
    main()
