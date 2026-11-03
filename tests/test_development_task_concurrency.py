# SPDX-License-Identifier: MPL-2.0
"""Eight caller custody and late refusal; exposed software evidence only."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from threading import Barrier, Lock, get_ident, local
import time

import pytest

from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict, ConcurrentArtifactMemberPreflight, ExternalArtifactPlane, GuardedExternalRoot,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.runtime_platform.test_current_development_receipted_inputs import _case as _receipt_case
from tests.test_reduced_artifact_verification import _mask_changed_stat


def _stock_plane(path):
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    path.mkdir()
    mount = next(parent for parent in path.parents if parent.is_mount())
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'exposed.concurrent-dev', 'Software custody, no scientific qualification', str(path), str(mount),
        'empirical-lawhood/testing/recursive-custody', 1)), validators=integration_artifact_profile_validators())


def _case(tmp_path):
    return _receipt_case(tmp_path, plane_factory=_stock_plane)


def test_eight_development_input_guards_run_without_the_global_plane_lock(tmp_path, monkeypatch):
    case = _case(tmp_path)
    custody = case.custody
    custody.initialize_task_reads()
    barrier, seen = Barrier(8), local()
    original = custody.require_input_member
    def guard(manifest):
        if not getattr(seen, 'entered', False):
            seen.entered = True
            barrier.wait(timeout=10)
        original(manifest)
    monkeypatch.setattr(custody, 'require_input_member', guard)
    selected = custody.member_preflight
    assert type(selected) is ConcurrentArtifactMemberPreflight
    def verify(_):
        case.plane.verify_manifest(case.manifest, before_member=selected)
        assert custody.writer is case.plane
    with ThreadPoolExecutor(max_workers=8) as pool:
        tuple(pool.map(verify, range(8)))
    assert (case.manifest.logical, case.manifest.materialization) in custody._original_member_facts


def test_concurrent_task_reads_have_separate_writers_facts_and_receipt_dags(tmp_path):
    case = _case(tmp_path)
    custody = case.custody
    custody.initialize_task_reads()
    barrier = Barrier(8)
    def consume(value):
        with custody.task_read_scope():
            state = custody._task_read()
            state.receipts['disclosed-test-only'] = value
            state.facts.add(value)
            barrier.wait(timeout=10)
            assert state.receipts == {'disclosed-test-only': value}
            assert {row for row in state.facts if type(row) is int} == {value}
            return state, custody.writer
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = tuple(pool.map(consume, range(8)))
    assert len({id(writer) for _, writer in results}) == 8
    assert all(not state.facts and not state.receipts for state, _ in results)
    assert custody.writer is case.plane and custody._task_read() is None
    for _, writer in results:
        with pytest.raises(ArtifactIdentityConflict, match='ended'):
            writer.require_verification_context()


@pytest.mark.parametrize('damage', ('receipt', 'body', 'sidecar', 'marker', 'access'))
@pytest.mark.parametrize('refusal', (False, True))
def test_finite_development_read_keeps_complete_final_bytes_and_current_access(tmp_path, monkeypatch, damage, refusal):
    case = _case(tmp_path)
    custody = case.custody
    custody.initialize_task_reads()
    fact = case.manifest.logical, case.manifest.materialization
    with pytest.raises((ArtifactIdentityConflict, PermissionError)):
        with custody.task_read_scope():
            custody._manifest(case.manifest.materialization.relative_path, expected=case.manifest)
            if damage == 'access':
                custody.original_input_access.current = False
            else:
                if damage == 'receipt':
                    attempt = custody.index.task('source').attempts[0]
                    relative = ExternalTaskReceiptStore._relative_path(custody.index.run_id, 'source', attempt.attempt_id)
                elif damage == 'body':
                    relative = case.manifest.materialization.relative_path
                elif damage == 'sidecar':
                    relative = case.manifest.materialization.relative_path + '.manifest.json'
                else:
                    relative = case.manifest.publication.commit_marker_relative_path
                path = case.plane.root.resolve(relative, for_write=False)
                raw = path.read_bytes()
                _mask_changed_stat(monkeypatch, path)
                path.write_bytes(b'[' + raw[1:])
            if refusal:
                raise LookupError('disclosed consumer refusal')
    assert custody._task_read() is None and custody.writer is case.plane
    assert fact not in custody._original_member_facts


def test_a_later_call_rejoins_original_receipts_instead_of_trusting_prior_facts(tmp_path):
    case = _case(tmp_path)
    custody = case.custody
    custody.initialize_task_reads()
    custody.member_preflight(case.manifest)
    assert (case.manifest.logical, case.manifest.materialization) in custody._original_member_facts
    attempt = custody.index.task('source').attempts[0]
    path = case.plane.root.resolve(ExternalTaskReceiptStore._relative_path(
        custody.index.run_id, 'source', attempt.attempt_id), for_write=False)
    path.unlink()
    with pytest.raises(ArtifactIdentityConflict, match='pair is partial'):
        custody.member_preflight(case.manifest)


def test_composed_independent_callbacks_keep_concurrency(tmp_path):
    plane, manifests = _publication(tmp_path, 1)
    barrier, seen = Barrier(8), local()
    def independent(_):
        if not getattr(seen, 'entered', False):
            seen.entered = True
            barrier.wait(timeout=10)
    callback = ConcurrentArtifactMemberPreflight(independent)
    with plane.read_context(before_member=callback) as reading:
        # Scope composition must preserve the explicit concurrent contract.
        composed = reading._operation_member_preflight(callback)
        assert type(composed) is ConcurrentArtifactMemberPreflight
        with ThreadPoolExecutor(max_workers=8) as pool:
            tuple(pool.map(lambda _: plane.verify_manifest(manifests[0], before_member=composed), range(8)))


def test_ordinary_callbacks_keep_their_serialized_policy(tmp_path):
    plane, manifests = _publication(tmp_path, 1)
    lock = Lock()
    active = peak = 0
    def ordinary(_):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.001)
        with lock:
            active -= 1
    with ThreadPoolExecutor(max_workers=8) as pool:
        tuple(pool.map(lambda _: plane.verify_manifest(manifests[0], before_member=ordinary), range(8)))
    assert peak == 1


def test_changed_reader_policy_refuses_a_previously_selected_concurrent_guard(tmp_path, monkeypatch):
    case = _case(tmp_path)
    case.custody.initialize_task_reads()
    selected = case.custody.member_preflight
    monkeypatch.setattr(case.plane, 'read_manifest', lambda *_a, **_kw: case.manifest)
    assert type(case.custody.member_preflight) is not ConcurrentArtifactMemberPreflight
    with pytest.raises(PermissionError, match='read policy'):
        selected(case.manifest)


def test_complete_publication_keeps_one_guard_scope_per_task_thread(tmp_path):
    original, manifests = _publication(tmp_path, 64)
    plane = ExternalArtifactPlane(original.root, maximum_parallel_verifications=8)
    current = ContextVar('exposed-publication-guard', default=None)
    entered, closed, seen = [], [], []
    @contextmanager
    def scope():
        if current.get() is not None:
            yield
            return
        identity = object()
        thread = get_ident()
        entered.append(identity)
        token = current.set((identity, thread))
        try:
            yield
        finally:
            closed.append(identity)
            current.reset(token)
    def guard(manifest):
        identity, thread = current.get()
        assert thread == get_ident(), 'a nested verifier inherited mutable guard state'
        seen.append((identity, manifest.materialization.relative_path))
    callback = ConcurrentArtifactMemberPreflight(guard, scope)
    rendezvous = Barrier(8)
    def read(_):
        rendezvous.wait(10)
        plane.verify_manifest(manifests[0], before_member=callback)
        assert current.get() is None
    with ThreadPoolExecutor(max_workers=8) as pool:
        tuple(pool.map(read, range(8)))
    assert len(entered) == len(closed) == 8 and set(entered) == set(closed)
    expected = {row.materialization.relative_path for row in manifests}
    for identity in entered:
        assert {relative for owner, relative in seen if owner is identity} == expected


def test_copied_task_thread_never_inherits_another_callers_mutable_custody(tmp_path):
    case = _case(tmp_path)
    custody = case.custody
    custody.initialize_task_reads()
    with custody.task_read_scope():
        original = custody._task_read()
        original.receipts['parent-only'] = object()
        copied = copy_context()
        def child():
            assert custody._task_read() is None
            with custody.task_read_scope():
                assert custody._task_read() is not original
                assert custody._task_read().receipts == {}
                custody.require_input_member(case.manifest)
            assert custody._task_read() is None
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(copied.run, child).result()
        assert custody._task_read() is original and set(original.receipts) == {'parent-only'}
