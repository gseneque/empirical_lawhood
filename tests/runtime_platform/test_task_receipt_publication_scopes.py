# SPDX-License-Identifier: MPL-2.0
"""Actual software custody under a bounded control directory; no fresh science."""
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from tests.runtime_platform.test_execution_scheduler import _runtime


def _scope_for(receipt):
    return f'runs/{receipt.run_id}/receipts/{receipt.task_id}'


def _inventory(root):
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


@pytest.mark.parametrize('legacy', (False, True))
def test_new_receipts_do_not_exhaust_one_shared_control_directory(tmp_path, protocol_fixture, monkeypatch, legacy):
    scheduler, repository, plane, store, _ = _runtime(tmp_path, protocol_fixture)
    original = plane._write_staged_bytes
    observed = []
    refused = []

    def bounded_directory(path, payload):
        if 'receipts' in path.parts and '.publication-batches' in path.parts:
            occupied = sum(1 for _ in path.parent.iterdir())
            if occupied >= 4:
                refused.append(path.parent)
                raise OSError('software fixture control directory is full')
            observed.append(path.parent)
        return original(path, payload)

    monkeypatch.setattr(plane, '_write_staged_bytes', bounded_directory)
    if legacy:
        monkeypatch.setattr(store, '_publication_request', lambda request: replace(request,
            publication_scope_relative_root=request.publication_scope_relative_root.rsplit('/', 1)[0]))
    try:
        result = scheduler.execute(protocol_fixture.run_plan.run_plan_id, protocol_fixture.execution_plan)
        if legacy:
            assert result.status is OperationalStatus.FAILED
            assert refused and 0 < len(result.receipts) < 6
            assert len(set(observed)) < 6
            return
        assert result.status is OperationalStatus.SUCCEEDED
        assert not refused and len(result.receipts) == 6 and len(set(observed)) == 6
        for receipt in result.receipts:
            relative = store._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
            manifest = decode_artifact_manifest((tmp_path / (relative + '.manifest.json')).read_bytes())
            assert manifest.publication.publication_scope.relative_root == _scope_for(receipt)
            assert manifest.logical.content_sha256 == receipt.fingerprint()
            assert (tmp_path / relative).read_bytes() == receipt.canonical_bytes()
            assert store.read(receipt.run_id, receipt.task_id, receipt.attempt_id) == receipt
    finally:
        repository.engine.dispose()


@pytest.mark.parametrize('legacy', (False, True))
def test_committed_receipts_retain_exact_original_scope_and_bytes(tmp_path, protocol_fixture, monkeypatch, legacy):
    scheduler, repository, _, store, _ = _runtime(tmp_path, protocol_fixture)
    try:
        with monkeypatch.context() as patch:
            if legacy:
                patch.setattr(store, '_publication_request', lambda request: replace(request,
                    publication_scope_relative_root=request.publication_scope_relative_root.rsplit('/', 1)[0]))
            result = scheduler.execute(protocol_fixture.run_plan.run_plan_id, protocol_fixture.execution_plan)
        assert result.status is OperationalStatus.SUCCEEDED
        root = tmp_path / 'runs' / result.run_id / 'receipts'
        before = _inventory(root)
        for receipt in result.receipts:
            relative = store._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
            manifest = decode_artifact_manifest((tmp_path / (relative + '.manifest.json')).read_bytes())
            committed = store.commit(receipt, visibility_ceiling=manifest.logical.visibility_ceiling,
                                     outcome_access=manifest.logical.outcome_access)
            assert committed.created is False
            assert committed.logical == manifest.logical
            assert committed.materialization == manifest.materialization
            assert store.read(receipt.run_id, receipt.task_id, receipt.attempt_id) == receipt
        assert _inventory(root) == before
    finally:
        repository.engine.dispose()


@pytest.mark.parametrize('legacy', (False, True))
def test_interrupted_receipt_intent_keeps_its_original_scope(tmp_path, protocol_fixture, monkeypatch, legacy):
    scheduler, repository, plane, store, _ = _runtime(tmp_path, protocol_fixture)
    try:
        result = scheduler.execute(protocol_fixture.run_plan.run_plan_id, protocol_fixture.execution_plan)
        receipt = result.receipts[0]
        relative = store._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
        manifest = decode_artifact_manifest((tmp_path / (relative + '.manifest.json')).read_bytes())
        # Remove only this disposable fixture receipt's publication. Original
        # output custody remains authentic; no provider is called by commit.
        (tmp_path / relative).unlink()
        (tmp_path / (relative + '.manifest.json')).unlink()
        (tmp_path / manifest.publication.commit_marker_relative_path).unlink()
        original_intent = plane._write_publication_intent

        def interrupted_intent(path, intent):
            original_intent(path, intent)
            raise KeyboardInterrupt('software fixture crash after exact intent publication')

        with monkeypatch.context() as patch:
            if legacy:
                patch.setattr(store, '_publication_request', lambda request: replace(request,
                    publication_scope_relative_root=request.publication_scope_relative_root.rsplit('/', 1)[0]))
            patch.setattr(plane, '_write_publication_intent', interrupted_intent)
            with pytest.raises(KeyboardInterrupt, match='exact intent'):
                store.commit(receipt, visibility_ceiling=manifest.logical.visibility_ceiling,
                             outcome_access=manifest.logical.outcome_access)
        root = tmp_path / 'runs' / result.run_id / 'receipts'
        intents = tuple(root.rglob('*.intent.json'))
        assert len(intents) == 1
        retained_intent = intents[0].read_bytes()
        assert retained_intent
        committed = store.commit(receipt, visibility_ceiling=manifest.logical.visibility_ceiling,
                                 outcome_access=manifest.logical.outcome_access)
        assert committed.created is True
        received = decode_artifact_manifest((tmp_path / (relative + '.manifest.json')).read_bytes())
        expected = _scope_for(receipt).rsplit('/', 1)[0] if legacy else _scope_for(receipt)
        assert received.publication.publication_scope.relative_root == expected
        assert store.read(receipt.run_id, receipt.task_id, receipt.attempt_id) == receipt
        assert not intents[0].exists()
        assert (tmp_path / relative).read_bytes() == receipt.canonical_bytes()
    finally:
        repository.engine.dispose()


def test_long_valid_receipt_names_publish_and_replay_exactly(tmp_path, protocol_fixture):
    """Receipt targets fit NAME_MAX even when the former staging suffix did not."""
    scheduler, repository, plane, store, _ = _runtime(tmp_path, protocol_fixture)
    try:
        result = scheduler.execute(protocol_fixture.run_plan.run_plan_id, protocol_fixture.execution_plan)
        original = result.receipts[0]
        receipt = replace(original, receipt_id='receipt.disclosed.long-name', attempt_id='a' * 217)
        original_path = store._relative_path(original.run_id, original.task_id, original.attempt_id)
        manifest = plane.read_manifest(original_path)
        written = store.commit(receipt, visibility_ceiling=manifest.logical.visibility_ceiling,
            outcome_access=manifest.logical.outcome_access)
        assert written.created
        assert store.read(receipt.run_id, receipt.task_id, receipt.attempt_id) == receipt
        before = _inventory(tmp_path)
        replay = store.commit(receipt, visibility_ceiling=manifest.logical.visibility_ceiling,
            outcome_access=manifest.logical.outcome_access)
        assert not replay.created
        assert _inventory(tmp_path) == before
        assert not tuple(tmp_path.rglob('*.partial'))
    finally:
        repository.engine.dispose()
