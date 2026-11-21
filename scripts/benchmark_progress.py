# SPDX-License-Identifier: MPL-2.0
"""Focused advisory-telemetry overhead, against an explicitly selected checkout.

Run each source in its own process. No native engines, scientific workload,
network or full test suite is executed. The original reporter name is selected
only to measure an unmodified baseline, never provided as a runtime alias.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve() / 'src'))
    from empirical_lawhood.storage import progress
    from empirical_lawhood.execution.progress import report_progress
    reporter = getattr(progress, 'OperationalProgressReporter', None)
    if reporter is None:
        reporter = progress.JsonProgressReporter
    rows = []
    with tempfile.TemporaryDirectory(prefix='progress-benchmark-') as root:
        for case, count in (('changing-phase', 3000), ('same-phase', 100000), ('unselected-port', 100000)):
            for repeat in range(args.repeats):
                writes = []
                selected = None
                if case != 'unselected-port':
                    selected = reporter(Path(root) / f'{case}-{repeat}.json', 'benchmark')
                    install = selected._install
                    def counting_install(raw):
                        writes.append(len(raw))
                        return install(raw)
                    selected._install = counting_install
                wall, cpu = time.perf_counter(), time.process_time()
                for index in range(count):
                    phase = 'phase.' + str(index) if case == 'changing-phase' else 'phase.same'
                    if case == 'unselected-port':
                        report_progress(phase=phase, done=index + 1, total=count)
                    else:
                        selected.update(phase=phase, done=index + 1, total=count)
                if selected is not None:
                    selected.finish()
                rows.append(dict(case=case, repeat=repeat, calls=count,
                    wall_seconds=time.perf_counter()-wall, cpu_seconds=time.process_time()-cpu,
                    atomic_writes=len(writes), published_bytes=sum(writes),
                    returned='NOT_SELECTED' if selected is None else progress.read_progress(selected.path)['status']))
    summary = {}
    for case in ('changing-phase', 'same-phase', 'unselected-port'):
        chosen = [row for row in rows if row['case'] == case]
        summary[case] = {key: statistics.median(row[key] for row in chosen)
            for key in ('wall_seconds', 'cpu_seconds', 'atomic_writes', 'published_bytes')}
    document = dict(source=str(args.source.resolve()), python=sys.version, reporter=reporter.__name__,
        source_sha256={str(path.relative_to(args.source)):sha256(path.read_bytes()).hexdigest()
            for path in (args.source/'src/empirical_lawhood/storage/progress.py', args.source/'src/empirical_lawhood/execution/progress.py')},
        boundary='Reporter update/finish only; initial creation excluded; no native workload or real callback overhead qualification',
        rows=rows, median=summary)
    args.destination.write_text(json.dumps(document, indent=2)+'\n')
    print(json.dumps(document['median'], indent=2))


if __name__ == '__main__':
    main()
