# SPDX-License-Identifier: MPL-2.0
"""Advisory telemetry controls: no scientific work, records or authority."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import Context
import errno
import json
import os
from pathlib import Path
import stat

import pytest

from empirical_lawhood.infrastructure import progress as owner
from empirical_lawhood.runtime.progress import active_progress, progress_reporting, report_progress


class Capture:
    def __init__(self):
        self.rows = []

    def update(self, **kwargs):
        self.rows.append(kwargs)


def test_reporting_is_opt_in_nested_exception_safe_and_context_local():
    first, second = Capture(), Capture()
    assert not active_progress()
    report_progress(phase='ignored')
    with progress_reporting(first):
        report_progress(phase='outer', done=1, total=2)
        with pytest.raises(RuntimeError), progress_reporting(second):
            report_progress(phase='inner')
            raise RuntimeError('exposed job failure')
        assert active_progress()
        assert Context().run(active_progress) is False
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(active_progress).result() is False
        report_progress(phase='restored', failed=0)
        with progress_reporting(None):
            assert not active_progress()
    assert not active_progress()
    assert [row['phase'] for row in first.rows] == ['outer', 'restored']
    assert second.rows == [{'phase': 'inner', 'done': None, 'total': None, 'failed': 0}]


def test_reporter_exception_does_not_change_job_result_or_exception():
    class Broken:
        def update(self, **_kwargs):
            raise OSError('telemetry-only failure')
    failure = RuntimeError('original job failure')
    with progress_reporting(Broken()):
        report_progress(phase='work', done=1, total=1)
        with pytest.raises(RuntimeError) as caught:
            report_progress(phase='work')
            raise failure
    assert caught.value is failure and not active_progress()


def test_initial_snapshot_and_phase_changes_precede_work_but_same_phase_is_throttled(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(owner.time, 'monotonic', lambda: clock[0])
    path = tmp_path / 'progress.json'
    reporter = owner.JsonProgressReporter(path, 'campaign experiment-run', minimum_interval=1)
    initial = owner.read_progress(path)
    assert initial['phase'] == 'starting' and initial['status'] == 'RUNNING'
    assert initial['done'] is initial['total'] is initial['percent'] is None
    assert initial['elapsed_seconds'] == 0 and initial['pid'] == os.getpid()
    reporter.update(phase='workers', done=0, total=4)
    before = path.read_bytes()
    reporter.update(phase='workers', done=1, total=4)
    assert path.read_bytes() == before
    clock[0] += 1
    reporter.update(phase='workers', done=2, total=4, failed=1)
    current = owner.read_progress(path)
    assert (current['done'], current['total'], current['failed'], current['percent']) == (2, 4, 1, 50.0)
    assert current['elapsed_seconds'] == 1
    reporter.update(phase='assess', done=None, total=None)
    assert owner.read_progress(path)['phase'] == 'assess'


@pytest.mark.parametrize('done,total', [(None, None), (3, None), (None, 8), (0, 0)])
def test_unknown_or_empty_denominator_never_invents_a_percent(tmp_path, done, total):
    path = tmp_path / 'unknown.json'
    reporter = owner.JsonProgressReporter(path, 'software fixture')
    reporter.update(phase='work', done=done, total=total)
    reporter.finish('RETURNED')
    current = owner.read_progress(path)
    assert (current['done'], current['total'], current['percent']) == (done, total, None)
    assert current['status'] == 'RETURNED'


def test_finish_forces_last_partial_count_and_future_updates_are_ignored(tmp_path):
    path = tmp_path / 'partial.json'
    reporter = owner.JsonProgressReporter(path, 'test', minimum_interval=1000)
    reporter.update(phase='members', done=0, total=8)
    reporter.update(phase='members', done=3, total=8, failed=1)
    assert owner.read_progress(path)['done'] == 0
    reporter.finish('FAILED')
    finished = path.read_bytes()
    current = owner.read_progress(path)
    assert (current['done'], current['total'], current['failed'], current['percent']) == (3, 8, 1, 37.5)
    assert current['status'] == 'FAILED'
    reporter.update(phase='not-a-retry', done=8, total=8)
    reporter.finish('RETURNED')
    assert path.read_bytes() == finished


@pytest.mark.parametrize('failure,status', [(None, 'RETURNED'), (RuntimeError('original'), 'FAILED'),
    (KeyboardInterrupt(), 'INTERRUPTED'), (SystemExit(7), 'INTERRUPTED')])
def test_context_manager_binds_finishes_and_preserves_job_exception(tmp_path, failure, status):
    path = tmp_path / 'context.json'
    outer = Capture()
    with progress_reporting(outer):
        try:
            with owner.JsonProgressReporter(path, operation='software fixture') as reporter:
                assert active_progress()
                report_progress(phase='test.work', done=1, total=2)
                if failure is not None:
                    raise failure
        except BaseException as caught:
            assert caught is failure
        assert active_progress()
        report_progress(phase='outer-restored')
    assert reporter.error is None and not active_progress()
    assert owner.read_progress(path)['status'] == status
    assert [row['phase'] for row in outer.rows] == ['outer-restored']


def test_initial_claim_refuses_existing_file_directory_missing_parent_and_ancestor_link(tmp_path):
    occupied = tmp_path / 'original.json'
    occupied.write_bytes(b'original scientific-looking bytes remain unchanged')
    original = occupied.read_bytes()
    with pytest.raises(FileExistsError):
        owner.JsonProgressReporter(occupied, 'job')
    assert occupied.read_bytes() == original
    with pytest.raises(OSError):
        owner.JsonProgressReporter(tmp_path, 'job')
    with pytest.raises(FileNotFoundError):
        owner.JsonProgressReporter(tmp_path / 'missing' / 'status.json', 'job')
    # Existing Linux proc links exercise real no-follow directory opens without
    # creating links or any output on the removable filesystem or root disk.
    with pytest.raises(OSError):
        owner.JsonProgressReporter(Path('/proc/self/cwd') / 'not-created-status.json', 'job')
    assert not tuple(tmp_path.glob('.el-progress.*'))


def test_initial_destination_race_is_exclusive_and_cleans_own_stage(tmp_path, monkeypatch):
    path = tmp_path / 'raced.json'
    original = owner.rename_noreplace

    def racing(source, target, **kwargs):
        path.write_bytes(b'concurrent destination')
        return original(source, target, **kwargs)

    monkeypatch.setattr(owner, 'rename_noreplace', racing)
    with pytest.raises(FileExistsError):
        owner.JsonProgressReporter(path, 'job')
    assert path.read_bytes() == b'concurrent destination'
    assert not tuple(tmp_path.glob('.el-progress.*'))


def test_atomic_replace_exposes_only_complete_snapshots_and_does_not_fsync(tmp_path, monkeypatch):
    path = tmp_path / 'atomic.json'
    reporter = owner.JsonProgressReporter(path, 'job', minimum_interval=0)
    old = path.read_bytes()
    replace = owner.os.replace
    observed = []

    def replace_snapshot(source, destination, **kwargs):
        assert owner.read_progress(path)['phase'] == 'starting'
        staged = json.loads((tmp_path / source).read_bytes())
        assert staged['phase'] == 'work' and staged['done'] == 2
        assert path.read_bytes() == old
        observed.append((kwargs['src_dir_fd'], kwargs['dst_dir_fd']))
        return replace(source, destination, **kwargs)

    monkeypatch.setattr(owner.os, 'replace', replace_snapshot)
    monkeypatch.setattr(owner.os, 'fsync', lambda *_args: pytest.fail('advisory progress must not fsync'))
    reporter.update(phase='work', done=2, total=4)
    assert observed and owner.read_progress(path)['percent'] == 50
    assert not tuple(tmp_path.glob('.el-progress.*'))


@pytest.mark.parametrize('entry', ['write', 'replace'])
def test_update_failure_retains_previous_snapshot_disables_and_warns_once(tmp_path, monkeypatch, capsys, entry):
    path = tmp_path / 'failure.json'
    reporter = owner.JsonProgressReporter(path, 'job', minimum_interval=0)
    before = path.read_bytes()

    def fail(*_args, **_kwargs):
        raise OSError(errno.ENOSPC, 'do not expose this arbitrary sensitive message')

    monkeypatch.setattr(owner.os, entry, fail)
    with progress_reporting(reporter):
        report_progress(phase='work', done=1, total=2)
        report_progress(phase='later')
    reporter.finish('FAILED')
    assert path.read_bytes() == before and reporter.error == 'OSError'
    assert not tuple(tmp_path.glob('.el-progress.*'))
    assert capsys.readouterr().err == 'Progress reporting disabled (OSError).\n'


def test_external_destination_replacement_or_symlink_is_not_overwritten(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'owned.json'
    reporter = owner.JsonProgressReporter(path, 'job', minimum_interval=0)
    path.unlink()
    path.write_bytes(b'changed destination')
    reporter.update(phase='work')
    assert path.read_bytes() == b'changed destination' and reporter.error == 'FileExistsError'
    second_path = tmp_path / 'link.json'
    second = owner.JsonProgressReporter(second_path, 'job')
    before = second_path.read_bytes()
    original_stat = owner.os.stat

    def substituted(name, *args, **kwargs):
        result = original_stat(name, *args, **kwargs)
        if name == second_path.name and kwargs.get('follow_symlinks') is False:
            fields = list(result)
            fields[0] = stat.S_IFLNK | 0o777
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(owner.os, 'stat', substituted)
    second.update(phase='work')
    assert second_path.read_bytes() == before and second.error == 'FileExistsError'
    assert capsys.readouterr().err.count('Progress reporting disabled') == 2


@pytest.mark.parametrize('values', [dict(phase='invalid message\n'), dict(phase='x' * 129),
    dict(phase='work', done=True), dict(phase='work', done=-1), dict(phase='work', done=2**63),
    dict(phase='work', done=2, total=1), dict(phase='work', done=1, failed=2),
    dict(phase='work', total=1, failed=2), dict(phase='work', failed=None)])
def test_counter_and_phase_validation_refuses_without_changing_snapshot(tmp_path, values):
    path = tmp_path / 'validation.json'
    reporter = owner.JsonProgressReporter(path, 'job')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        reporter.update(**values)
    assert path.read_bytes() == before


@pytest.mark.parametrize('changes', [{'schema': 'foreign'}, {'status': []}, {'percent': 100},
    {'done': True}, {'elapsed_seconds': float('nan')}, {'pid': False},
    {'updated_at_utc': '2026-10-16T00:00:00'}, {'phase': 'unbounded message'}, {'extra': 'field'}])
def test_bounded_reader_rejects_invalid_schema_counts_status_and_time(tmp_path, changes):
    path = tmp_path / 'invalid.json'
    owner.JsonProgressReporter(path, 'job')
    document = json.loads(path.read_bytes())
    document.update(changes)
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        owner.read_progress(path)


def test_reader_refuses_oversize_duplicates_and_nonregular_input(tmp_path):
    path = tmp_path / 'bounded.json'
    path.write_bytes(b' ' * (owner.MAX_PROGRESS_BYTES + 1))
    with pytest.raises(RuntimeError):
        owner.read_progress(path)
    path.write_bytes(b'{"schema":1,"schema":2}')
    with pytest.raises(ValueError, match='duplicate'):
        owner.read_progress(path)
    with pytest.raises((RuntimeError, OSError)):
        owner.read_progress(tmp_path)


def test_shared_reporter_serializes_concurrent_updates_without_disabling(tmp_path):
    path = tmp_path / 'threads.json'
    reporter = owner.JsonProgressReporter(path, 'job', minimum_interval=0)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda n: reporter.update(phase='members', done=n, total=32), range(33)))
    reporter.finish('RETURNED')
    current = owner.read_progress(path)
    assert reporter.error is None and current['status'] == 'RETURNED'
    assert 0 <= current['done'] <= 32 and not tuple(tmp_path.glob('.el-progress.*'))


@pytest.mark.parametrize('failure', [None, RuntimeError('original job error')])
def test_final_write_failure_restores_scope_without_masking_job(tmp_path, monkeypatch, capsys, failure):
    path = tmp_path / 'final-write.json'
    reporter = owner.JsonProgressReporter(path, 'job')
    outer = Capture()
    before = path.read_bytes()

    def fail(*_args, **_kwargs):
        raise OSError(errno.ENOSPC, 'private telemetry detail')

    with progress_reporting(outer):
        try:
            with reporter:
                monkeypatch.setattr(owner.os, 'replace', fail)
                if failure is not None:
                    raise failure
        except RuntimeError as caught:
            assert caught is failure
        assert active_progress()
        report_progress(phase='restored')
    assert [row['phase'] for row in outer.rows] == ['restored']
    assert not active_progress() and path.read_bytes() == before and reporter.error == 'OSError'
    assert capsys.readouterr().err == 'Progress reporting disabled (OSError).\n'
