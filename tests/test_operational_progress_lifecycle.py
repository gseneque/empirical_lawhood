# SPDX-License-Identifier: MPL-2.0
"""Live advisory counters preserve outcome authority and complete owner lifetimes."""

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import json
import os
import select
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.execution.progress import (
    active_progress, current_progress, progress_reporting, progress_step,
    report_progress, report_workflow_progress, run_with_progress,
)
from empirical_lawhood.storage import progress as storage


def test_heartbeat_keeps_real_counters_and_distinguishes_liveness(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(storage.time, 'monotonic', lambda: clock[0])
    stream = StringIO()
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'unit operation', stream=stream)
    reporter.update(phase='native.call', done=2, total=8, unit='iterations')
    clock[0] += 17
    reporter.heartbeat()
    row = storage.read_progress(reporter.path)
    assert (row['done'], row['total'], row['percent']) == (2, 8, 25.0)
    assert row['heartbeat'] is True and row['activity_age_seconds'] == 17
    assert row['phase_elapsed_seconds'] == 17 and row['elapsed_seconds'] == 17
    assert 'controller alive; work advancement unknown' in stream.getvalue()
    assert 'remaining=6' in stream.getvalue()
    reporter.finish()


def test_nested_steps_restore_parent_clock_and_record_partial_failure(tmp_path, monkeypatch):
    clock = [10.0]
    monkeypatch.setattr(storage.time, 'monotonic', lambda: clock[0])
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'nested', minimum_interval=0)
    with progress_reporting(reporter):
        report_workflow_progress(done=1, total=5)
        with progress_step('parent', total=3) as parent:
            parent.advance()
            clock[0] += 2
            with pytest.raises(ValueError), progress_step('child', total=4) as child:
                child.advance(2)
                clock[0] += 3
                raise ValueError('scientific refusal remains original')
            row = storage.read_progress(reporter.path)
            assert row['phase'] == 'parent' and row['phase_elapsed_seconds'] == 5
            assert (row['done'], row['total'], row['workflow_done'], row['workflow_total']) == (1, 3, 1, 5)
        reporter.finish()
    row = storage.read_progress(reporter.path)
    assert [(r['phase'], r['done'], r['status']) for r in row['completed_steps']] == [
        ('child', 2, 'FAILED'), ('parent', 1, 'RETURNED')]
    assert row['completed_steps'][0]['elapsed_seconds'] == 3
    assert row['completed_steps'][1]['elapsed_seconds'] == 5
    assert row['done'] == 1  # Successful return never invents 3/3.


def test_completed_step_retention_is_bounded_and_omission_is_explicit(tmp_path):
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'bounded')
    with progress_reporting(reporter):
        for index in range(100):
            with progress_step('step', total=1) as step:
                step.advance()
        reporter.finish()
    row = storage.read_progress(reporter.path)
    assert len(row['completed_steps']) == storage.MAX_COMPLETED_STEPS
    assert row['completed_steps_total'] == 100 and row['completed_steps_omitted'] == 36
    assert reporter.path.stat().st_size <= storage.MAX_PROGRESS_BYTES


def test_application_nested_sink_fans_out_without_second_heartbeat(tmp_path):
    console = StringIO()
    outer = storage.OperationalProgressReporter(tmp_path / 'cli.json', 'CLI', minimum_interval=0, stream=console)
    inner = storage.OperationalProgressReporter(tmp_path / 'application.json', 'application', minimum_interval=0)
    with outer:
        thread = outer._thread
        with inner:
            assert inner._thread is None and inner._parent is outer
            report_progress(phase='actual.inner', done=3, total=7, task_id='task.2')
            assert storage.read_progress(outer.path)['done'] == 3
            assert storage.read_progress(inner.path)['done'] == 3
            outer.heartbeat()
            assert storage.read_progress(inner.path)['heartbeat']
        assert outer._followers == [] and outer._thread is thread
        report_progress(phase='actual.outer', done=1, total=1)
    assert not thread.is_alive()
    assert storage.read_progress(outer.path)['status'] == 'RETURNED'
    assert storage.read_progress(inner.path)['status'] == 'RETURNED'
    assert 'actual.inner' in console.getvalue() and 'task=task.2' in console.getvalue()


def test_selected_worker_thread_gets_only_explicit_telemetry(tmp_path):
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'parallel', minimum_interval=0)
    with reporter, ThreadPoolExecutor(max_workers=2) as pool:
        assert pool.submit(active_progress).result() is False
        captured = current_progress()
        pool.submit(run_with_progress, captured, report_progress,
            phase='worker.progress', done=2, total=9).result()
        assert storage.read_progress(reporter.path)['done'] == 2
        assert pool.submit(active_progress).result() is False
    assert not active_progress()


def test_fork_cannot_acquire_inherited_locked_reporter(tmp_path):
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'fork owner')
    before = reporter.path.read_bytes()
    read_fd, write_fd = os.pipe()
    with progress_reporting(reporter):
        reporter._lock.acquire()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(read_fd)
                report_progress(phase='child.must-not-write', done=1, total=1)
                reporter.update(phase='direct.child')
                reporter.workflow_update(done=1, total=1)
                reporter.heartbeat()
                reporter.finish()
                os.write(write_fd, b'closed' if not active_progress() else b'bad')
            finally:
                os._exit(0)
        os.close(write_fd)
        try:
            readable, _, _ = select.select([read_fd], [], [], 2)
            assert readable, 'child blocked on an inherited telemetry lock'
            assert os.read(read_fd, 16) == b'closed'
        finally:
            reporter._lock.release()
            os.close(read_fd)
            if not readable:
                os.kill(pid, 9)
            os.waitpid(pid, 0)
    assert reporter.path.read_bytes() == before


def test_native_pipe_telemetry_reuses_ordered_ack_and_parent_task_identity(tmp_path):
    from empirical_lawhood.execution.local.native_subwork_ipc import (
        NativeSubworkPipeService, NativeSubworkReply, PipeNativeSubworkProgress,
    )
    service = object.__new__(NativeSubworkPipeService)
    service.parent = SimpleNamespace(task_id='task.real-parent')
    sent = []

    class Connection:
        def send(self, request):
            sent.append(request)
            service._dispatch(request.operation, request.arguments)

        def recv(self):
            return NativeSubworkReply(sent[-1].sequence)

    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'parent', minimum_interval=0)
    proxy = PipeNativeSubworkProgress(Connection())
    with progress_reporting(reporter):
        proxy.update(phase='child.decode', done=3, total=8, unit='bytes')
        proxy.update(phase='child.decode', done=4, total=8, unit='bytes')
        proxy.update(phase='child.native-call', detail='Opaque third-party library')
        proxy.step_completed(phase='child.decode', done=8, total=8, unit='bytes', elapsed_seconds=0.25, status='RETURNED')
        reporter.finish()
    assert [request.sequence for request in sent] == [1, 2, 3]
    assert [request.operation for request in sent] == ['advisory-progress', 'advisory-progress', 'advisory-step-completed']
    row = storage.read_progress(reporter.path)
    assert row['task_id'] == 'task.real-parent' and row['phase'] == 'child.native-call'
    assert row['done'] is row['total'] is row['percent'] is None
    assert row['completed_steps'][0]['done'] == 8


def test_default_cli_reports_and_quiet_keeps_json_identical(tmp_path):
    from empirical_lawhood.cli.app import app
    runner = CliRunner()
    normal = runner.invoke(app, ['workflow', 'list', '--format', 'json'])
    quiet = runner.invoke(app, ['--no-progress', 'workflow', 'list', '--format', 'json'])
    selected = tmp_path / 'progress.json'
    stored = runner.invoke(app, ['--no-progress', '--progress-file', str(selected), 'workflow', 'list', '--format', 'json'])
    assert normal.exit_code == quiet.exit_code == stored.exit_code == 0, stored.output
    assert json.loads(normal.stdout) == json.loads(quiet.stdout) == json.loads(stored.stdout)
    assert 'RUNNING |' in normal.stderr and 'RETURNED |' in normal.stderr
    assert quiet.stderr == stored.stderr == ''
    assert storage.read_progress(selected)['status'] == 'RETURNED'


def test_global_progress_refuses_every_repeated_input_path_before_work(tmp_path):
    from empirical_lawhood.cli.app import app
    first, second = tmp_path / 'missing-first.json', tmp_path / 'missing-second.json'
    result = CliRunner().invoke(app, ['--progress-file', str(first), 'campaign', 'experiment-run',
        '--authoring-dir', str(tmp_path / 'closed'), '--parent-input-binding', str(first), '--parent-input-binding', str(second)])
    assert result.exit_code == 2
    assert not first.exists()


def test_native_output_generator_interleaves_advisory_messages_with_stream(tmp_path):
    from empirical_lawhood.execution.local.native_subwork_ipc import (
        NativeSubworkPipeService, NativeSubworkReply, PipeNativeSubworkProgress, _PipeEntry,
    )
    service = object.__new__(NativeSubworkPipeService)
    entry = SimpleNamespace(definition=SimpleNamespace(outputs=(SimpleNamespace(output_id='raw'),)), outputs={})
    service.parent = SimpleNamespace(task_id='task.publication')
    service._completed = None
    service._entries, service._stages, service._aborted = {1: entry}, {}, set()
    service.scratch = tmp_path
    service._output_budget = None
    service.output_bytes = service.ordinary_output_bytes = 0
    service.store = SimpleNamespace(_entry=lambda value: value,
        publish_output=lambda value, output, chunks, **options: b''.join(chunks))
    sent, responses = [], []
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'parent', minimum_interval=0)

    class Connection:
        def send(self, request):
            sent.append(request)
            with progress_reporting(reporter):
                responses.append(NativeSubworkReply(request.sequence,
                    service._dispatch(request.operation, request.arguments)))

        def recv(self):
            return responses.pop(0)

    proxy = PipeNativeSubworkProgress(Connection())
    selected = _PipeEntry(None, 1, proxy._owner)

    def chunks():
        with progress_step('child.compress', total=6, unit='bytes') as step:
            for chunk in (b'abc', b'def'):
                step.advance(len(chunk))
                yield chunk

    with progress_reporting(proxy):
        result = proxy.publish_output(selected, 'raw', chunks(), maximum_bytes=6, expected_size_bytes=6,
            expected_physical_sha256=__import__('hashlib').sha256(b'abcdef').hexdigest())
    reporter.finish()
    assert result == b'abcdef'
    assert service._stages == {}
    operations = [row.operation for row in sent]
    assert operations[0] == 'output-open' and operations[-1] == 'output-close'
    assert operations.count('output-chunk') == 2
    assert 'advisory-progress' in operations and 'advisory-step-completed' in operations
    assert [row.sequence for row in sent] == list(range(1, len(sent) + 1))
    assert storage.read_progress(reporter.path)['completed_steps'][0]['done'] == 6


def test_native_callbacks_keep_unknown_convergence_and_original_stop_decision(tmp_path):
    from empirical_lawhood.adapters.rubisco.progress import minimization_reporter, progress_observer
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'native', minimum_interval=0)
    original_rows = []
    observe = progress_observer(original_rows.append)
    original = SimpleNamespace(report=lambda *args: args[0] == 7)
    with progress_reporting(reporter):
        callback = minimization_reporter(SimpleNamespace(MinimizationReporter=object), original)
        row = {'event': 'scf-iteration', 'cycle': 2.0, 'evaluation': 4}
        observe(row)
        assert original_rows == [row] and original_rows[0] is row
        record = storage.read_progress(reporter.path)
        assert record['done'] == 3 and record['total'] is None
        assert callback.report(7, (), (), {}) is True
        assert callback.report(0, (), (), {}) is False
        record = storage.read_progress(reporter.path)
        assert record['done'] == 2 and record['unit'] == 'iteration-callbacks'
        assert record['total'] is record['percent'] is None
    reporter.finish()


def test_progress_destination_excludes_existing_directories_under_any_option_name(tmp_path):
    from empirical_lawhood.cli.progress import _check_destination
    original = tmp_path / 'original'
    original.mkdir()
    with pytest.raises(ValueError, match='separate'):
        _check_destination(original / 'status.json', {'unexpected_scientific_source_name': original})


def test_suspended_generator_preserves_each_explicit_step_clock(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(storage.time, 'monotonic', lambda: clock[0])
    reporter = storage.OperationalProgressReporter(tmp_path / 'status.json', 'stream composition', minimum_interval=0)

    def chunks():
        with progress_step('source.read', total=2, unit='bytes') as source:
            for body in (b'a', b'b'):
                clock[0] += 2
                source.advance(len(body))
                yield body  # The source scope stays active while its writer advances.

    with progress_reporting(reporter):
        with progress_step('publication.write', total=2, unit='bytes') as writer:
            for body in chunks():
                clock[0] += 1
                writer.advance(len(body))
                row = storage.read_progress(reporter.path)
                assert row['phase'] == 'publication.write'
                assert row['phase_elapsed_seconds'] == clock[0] - writer.started
        reporter.finish()
    summaries = storage.read_progress(reporter.path)['completed_steps']
    assert [row['phase'] for row in summaries] == ['source.read', 'publication.write']
    assert [row['elapsed_seconds'] for row in summaries] == [6, 6]
