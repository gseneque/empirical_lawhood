# SPDX-License-Identifier: MPL-2.0
"""Durable software dispatch controls; no scientific acquisition or authority."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, ApplicationRequest, application_result
from empirical_lawhood.storage.application_invocations import ApplicationInvocationStore, process_identity, record_bytes
from empirical_lawhood.workbench import worker
from empirical_lawhood.workbench.invocations import InvocationDelivery, inspect_invocation


@pytest.fixture
def selected(tmp_path, monkeypatch):
    # Physical mount availability is the disclosed seam. All directory, byte,
    # exclusive publication, process, request and retained-state checks are real.
    monkeypatch.setattr(ApplicationInvocationStore, '_check_mount', lambda self: None)
    root = tmp_path/'jobs'; root.mkdir()
    context = ApplicationContext('test.jobs', 'Disclosed invocation fixture', Path(sys.executable).absolute(), invocation_root=root)
    store = ApplicationInvocationStore(root, tmp_path)
    request = ApplicationRequest('one', context.context_id, 'matrix.inspect', (('directory', str(tmp_path/'original')),))
    return store, context, request


def claim(selected, *, request=None, context=None):
    store, initial_context, initial_request = selected
    context = initial_context if context is None else context
    request = initial_request if request is None else request
    return store.claim(context_id=context.context_id, context_sha256=context.fingerprint(), engine_sha256='a'*64,
        context=context.to_document(), request=request.to_document(), client='browser')


def command(store, handle):
    return {'root':str(store.root), 'required_mount':str(store.required_mount), 'handle':handle,
        'intent_sha256':sha256(record_bytes(store.intent(handle))).hexdigest(),
        'request':store.intent(handle)['binding']['request']}


def test_concurrent_identical_requests_claim_one_handle_and_changed_operands_refuse(selected):
    with ThreadPoolExecutor(2) as pool:
        rows = list(pool.map(lambda _: claim(selected), range(2)))
    assert rows[0][0] == rows[1][0] and sorted(row[1] for row in rows) == [False, True]
    _, context, request = selected
    with pytest.raises(ValueError, match='different operands'):
        claim(selected, request=replace(request, parameters=(('directory', '/different/original'),)))
    with pytest.raises(ValueError, match='different operands'):
        claim(selected, context=replace(context, maximum_parallel_tasks=2))


def test_restart_preserves_uncertain_intent_and_never_dispatches_it_again(selected):
    store, context, request = selected
    handle, fresh = claim(selected)
    assert fresh
    restarted = ApplicationInvocationStore(store.root, store.required_mount)
    assert inspect_invocation(context, handle, required_mount=store.required_mount)['state'] == 'UNCERTAIN'
    assert claim((restarted, context, request)) == (handle, False)
    with pytest.raises(RuntimeError, match='uncertain'):
        claim(selected, request=replace(request, request_id='different'))


def test_arbitrary_unsaved_text_is_hash_bound_without_general_log_copy(selected):
    store, _context, request = selected
    text='DO_NOT_RETAIN_INVALID_OR_SECRET_TEXT'
    request=replace(request,parameters=(('text',text),))
    handle,_=claim(selected,request=request)
    binding=store.intent(handle)['binding']
    assert binding['request']['parameters']['text']['sha256']==sha256(text.encode()).hexdigest()
    assert binding['request_sha256']==sha256(record_bytes(request.to_document())).hexdigest()
    assert text.encode() not in (store.path(handle)/'intent.json').read_bytes()


def test_entry_return_and_lost_reply_keep_metadata_without_scientific_body(selected, monkeypatch):
    store, context, request = selected
    handle, _ = claim(selected)
    monkeypatch.setattr(worker, 'describe_engine', lambda: {'identity_sha256':'a'*64})
    from empirical_lawhood.api import application
    calls = []
    def execute(ctx, req):
        calls.append((ctx, req))
        assert store.snapshot(handle)['entry_observed'] is True
        return application_result(req.operation, {'scientific_fixture_value':'DO_NOT_RETAIN_THIS_BODY'})
    monkeypatch.setattr(application, 'execute_application', execute)
    _, returned_handle, body = worker.execute(command(store, handle))
    assert returned_handle == handle and json.loads(body)['payload']['scientific_fixture_value'] == 'DO_NOT_RETAIN_THIS_BODY'
    assert len(calls) == 1
    with pytest.raises(FileExistsError):
        worker.execute(command(store, handle))
    assert len(calls) == 1
    after = inspect_invocation(context, handle, required_mount=store.required_mount)
    assert after['state'] == 'RETURNED' and after['return']['status'] == 'SUCCEEDED'
    assert after['return']['response_sha256'] == sha256(body).hexdigest()
    for path in store.path(handle).rglob('*'):
        if path.is_file():
            assert b'DO_NOT_RETAIN_THIS_BODY' not in path.read_bytes()
    assert claim(selected) == (handle, False)
    assert claim(selected, request=replace(request, request_id='next'))[1] is True


def test_engine_change_or_intent_substitution_refuses_before_entry(selected, monkeypatch):
    store, _, _ = selected
    handle, _ = claim(selected)
    original = command(store, handle)
    monkeypatch.setattr(worker, 'describe_engine', lambda: {'identity_sha256':'b'*64})
    with pytest.raises(ValueError, match='context or engine'):
        worker.execute(original)
    assert store.snapshot(handle)['entry_observed'] is False
    data = store.intent(handle); data['binding']['request']['parameters']['directory']='/changed'
    (store.path(handle)/'intent.json').write_bytes(record_bytes(data))
    with pytest.raises(ValueError, match='identity'):
        worker.execute(original)


def test_pid_reuse_and_failed_publication_after_entry_remain_uncertain(selected):
    store, _, _ = selected
    handle, _ = claim(selected)
    binding = store.intent(handle)['binding_sha256']
    observed = {**process_identity(), 'start_ticks':'0'}
    store.publish(handle, 'entered', {'handle':handle,'binding_sha256':binding,'process':observed})
    store.publish(handle, 'launch-failed', {'handle':handle,'binding_sha256':binding,'failure':{'exception_type':'OSError'}})
    assert store.snapshot(handle)['state'] == 'UNCERTAIN'
    assert store.snapshot(handle)['process_live'] is False


def test_storage_replacement_and_symlink_refuse(selected, tmp_path):
    store, _, _ = selected
    store.root.rename(tmp_path/'original-jobs')
    store.root.mkdir()
    with pytest.raises(OSError, match='identity changed'):
        claim(selected)
    store.root.rmdir(); store.root.symlink_to(tmp_path/'original-jobs', target_is_directory=True)
    with pytest.raises(OSError):
        ApplicationInvocationStore(store.root, store.required_mount)


def test_delivery_timeout_does_not_kill_or_repeat_a_detached_worker(tmp_path):
    marker = tmp_path/'literal-completed'
    # A literal delayed subprocess is a process-lifetime fixture, not an EL task.
    source = "import pathlib,sys,time;sys.stdin.buffer.read();time.sleep(.2);pathlib.Path(sys.argv[1]).write_text('once');print('{}')"
    process = subprocess.Popen((sys.executable, '-I', '-c', source, str(marker)), stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, start_new_session=True)
    delivery = InvocationDelivery(process, b'')
    delivery.reader.deadline = time.monotonic()+.03
    try:
        with pytest.raises(ApplicationError, match='original worker may still be running') as refused:
            delivery.result()
        assert refused.value.code == 'INVOCATION_DELIVERY_UNAVAILABLE'
        assert process.poll() is None
        process.wait(timeout=3)
        assert marker.read_text() == 'once'
    finally:
        if process.poll() is None:
            process.kill(); process.wait()


def test_progress_companion_preserves_old_reader_and_never_sets_execution_state(selected, tmp_path):
    from empirical_lawhood.execution.local.application_progress import ApplicationProgressReporter, invocation_progress
    from empirical_lawhood.storage.progress import read_progress
    store, _context, request = selected
    handle, _ = claim(selected)
    root=tmp_path/'progress';root.mkdir()
    path=root/(handle+'.json')
    with ApplicationProgressReporter(path,request.operation,store=store,handle=handle) as progress:
        progress.update(phase='disclosed_phase',done=1,total=2)
        first=invocation_progress(store,handle,progress_root=root)
        assert first['availability']=='OBSERVED' and first['binding']['sequence']==2
        assert first['binding']['task_id'] is None
        assert read_progress(path)['done']==1
    after=invocation_progress(store,handle,progress_root=root)
    assert after['binding']['sequence']==3 and after['snapshot']['status']=='RETURNED'
    assert store.snapshot(handle)['state']=='UNCERTAIN'
    # A reordered companion or foreign snapshot is advisory unavailability,
    # never a repair of the authenticated invocation or scientific receipt.
    binding=store._read(store.path(handle)/'progress.json');binding['snapshot_sha256']='f'*64
    store.publish(handle,'progress',binding)
    assert invocation_progress(store,handle,progress_root=root)['availability']=='UPDATING_OR_UNBOUND'
    assert store.snapshot(handle)['state']=='UNCERTAIN'


def test_progress_step_summaries_use_application_decimal_transport(selected, tmp_path):
    from decimal import Decimal
    from empirical_lawhood.execution.local.application_progress import ApplicationProgressReporter, invocation_progress
    from empirical_lawhood.execution.progress import progress_step
    store, _context, request = selected
    handle, _ = claim(selected)
    root = tmp_path / 'progress'
    root.mkdir()
    with ApplicationProgressReporter(root / (handle + '.json'), request.operation, store=store, handle=handle):
        with progress_step('actual.step', total=1) as step:
            step.advance()
    observed = invocation_progress(store, handle, progress_root=root)
    assert observed['availability'] == 'OBSERVED'
    summary = observed['snapshot']['completed_steps'][0]
    assert summary['done'] == 1 and isinstance(summary['elapsed_seconds'], Decimal)
    assert store.snapshot(handle)['state'] == 'UNCERTAIN'
