# SPDX-License-Identifier: MPL-2.0
"""Exposed software custody controls; no execution or scientific authority."""

import pytest
import sys

from empirical_lawhood.infrastructure import recovery as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.recovery_support import case as case, custody as custody


def _replay(value, recovery, receipts):
    return recovery._reconcile_terminal(index=value.index, plan=value.plan,
        terminal=value.terminal, repository=None, receipt_store=receipts, existing={},
        candidate_count=sum(len(row.attempts) for row in value.index.tasks))


def _census(value, recovery, receipts):
    from empirical_lawhood.infrastructure.recursive_custody import _execution_operational_census
    return _execution_operational_census(recovery=recovery, store=receipts,
        plan=value.plan, index=value.index, terminal=value.terminal)


@pytest.mark.parametrize("custody", ("success", "blocked"), indirect=True)
def test_execution_census_batch_matches_the_ordinary_complete_serial_census(custody, monkeypatch):
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    expected = _census(custody, custody.recovery, custody.receipt_store)
    hashes, batches = [], []
    original_pin, original_batch = ObjectIdentity.from_record, owner._reconcile_recovery_control_batch

    def pin(cls, identifier, record):
        if record is custody.index:
            hashes.append(identifier)
        return original_pin(identifier, record)

    def batch(*args):
        batches.append(1)
        return original_batch(*args)

    monkeypatch.setattr(ObjectIdentity, "from_record", classmethod(pin))
    monkeypatch.setattr(owner, "_reconcile_recovery_control_batch", batch)
    with custody.plane.read_context() as plane:
        actual = _census(custody, owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane))
    assert actual == expected
    assert canonical_json_document_bytes(actual[0]) == canonical_json_document_bytes(expected[0])
    for actual_records, expected_records in zip(actual[1:], expected[1:], strict=True):
        assert {key: value.canonical_bytes() for key, value in actual_records.items()} == {
            key: value.canonical_bytes() for key, value in expected_records.items()}
    assert batches == [1] and hashes == [custody.index.recovery_index_id]


@pytest.mark.parametrize("custody", ("success",), indirect=True)
def test_history_batches_actual_controls_and_hashes_full_index_once(custody, monkeypatch):
    hashes, batches = [], []
    original_pin = ObjectIdentity.from_record
    original_event = owner._RecoveryControlBatch.receipt_event

    def pin(cls, identifier, record):
        if record is custody.index:
            hashes.append(identifier)
        return original_pin(identifier, record)

    def event(self, receipt, **arguments):
        batches.append(self)
        return original_event(self, receipt, **arguments)

    monkeypatch.setattr(ObjectIdentity, "from_record", classmethod(pin))
    monkeypatch.setattr(owner._RecoveryControlBatch, "receipt_event", event)
    with custody.plane.verification_scope() as plane:
        recovery, receipts = owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
        report = _replay(custody, recovery, receipts)
        assert report.recovered_receipts == custody.receipts
        assert hashes == [custody.index.recovery_index_id]
        assert len(batches) == len(custody.receipts)
        with pytest.raises(owner.RunRecoveryError, match="escaped"):
            batches[0].require_open(recovery, receipts, custody.index)


@pytest.mark.parametrize("custody", ("success",), indirect=True)
def test_custom_receipt_reader_retains_ordinary_serial_hook(custody, monkeypatch):
    reads = []

    class SelectedReceiptStore(ExternalTaskReceiptStore):
        def read(self, run_id, task_id, attempt_id):
            reads.append((task_id, attempt_id))
            return super().read(run_id, task_id, attempt_id)

    def forbidden(*args, **kwargs):
        pytest.fail("custom receipt reader entered the stock batch")

    monkeypatch.setattr(owner, "_reconcile_recovery_control_batch", forbidden)
    with custody.plane.verification_scope() as plane:
        report = _replay(custody, owner.ExternalRunRecoveryStore(plane), SelectedReceiptStore(plane))
        assert report.recovered_receipts == custody.receipts
    assert len(reads) == sum(len(row.attempts) for row in custody.index.tasks)


@pytest.mark.parametrize("custody", ("success",), indirect=True)
@pytest.mark.parametrize("reader", (_replay, _census))
def test_history_rejects_receipt_mutation_before_final_batch_guard(custody, monkeypatch, reader):
    original = owner._RecoveryControlBatch.receipt_event

    def mutate(self, receipt, **arguments):
        result = original(self, receipt, **arguments)
        path = custody.plane.root.resolve(
            custody.receipt_store._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id),
            for_write=True)
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'"SUCCEEDED"', b'"SUCCEEDEd"', 1))
        return result

    monkeypatch.setattr(owner._RecoveryControlBatch, "receipt_event", mutate)
    with pytest.raises((owner.RunRecoveryError, ArtifactIdentityConflict)):
        with custody.plane.verification_scope() as plane:
            reader(custody, owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane))


@pytest.mark.parametrize("custody", ("success",), indirect=True)
@pytest.mark.parametrize("reader", (_replay, _census))
def test_history_rejects_new_control_in_previously_absent_candidate(custody, monkeypatch, reader):
    original = owner._RecoveryControlBatch.receipt_event
    absent = next(row for row in custody.index.tasks
        if custody.receipt_store.read(custody.index.run_id, row.task_id, row.attempts[0].attempt_id) is None)
    relative = custody.receipt_store._relative_path(
        custody.index.run_id, absent.task_id, absent.attempts[0].attempt_id)

    def appear(self, receipt, **arguments):
        result = original(self, receipt, **arguments)
        path = custody.plane.root.resolve(relative, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"uncommitted exposed test control")
        return result

    monkeypatch.setattr(owner._RecoveryControlBatch, "receipt_event", appear)
    with pytest.raises(owner.RunRecoveryError, match="appeared|path changed"):
        with custody.plane.verification_scope() as plane:
            reader(custody, owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane))


@pytest.mark.parametrize("custody", ("success", "blocked"), indirect=True)
def test_complete_control_paths_share_one_live_resolution_census(custody):
    from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot
    expected = {name for row in custody.index.tasks
        for relative in (row.nonattempt_event_relative_path,
            *(name for candidate in row.attempts
                for name in (candidate.receipt_relative_path, candidate.event_relative_path)))
        for name in (relative, relative + '.manifest.json')}
    batches, repeated = [], []

    def observe(frame, event, _value):
        if event != 'call':
            return
        if frame.f_code is owner._consume_recovery_control_paths.__code__:
            batches.append(set(frame.f_locals['paths']))
        if (frame.f_code is GuardedExternalRoot.resolve.__code__ and frame.f_back.f_code.co_name
                in ('_read_envelope', '_read_payload_envelope', 'require_absences')):
            repeated.append(frame.f_locals['relative_path'])

    with custody.plane.read_context() as plane:
        assert sys.getprofile() is None
        sys.setprofile(observe)
        try:
            _census(custody, owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane))
        finally:
            sys.setprofile(None)
    assert batches == [expected]
    # Nonattempt block IDs are authenticated separately by the unchanged
    # terminal reader; none of the frozen candidate paths is resolved again.
    candidates = {candidate.attempt_id for row in custody.index.tasks for candidate in row.attempts}
    nonattempts = tuple(row for row in custody.terminal.attempts if row.attempt_id not in candidates)
    assert repeated == [name for row in nonattempts
        for relative in (custody.receipt_store._relative_path(custody.index.run_id, row.task_id, row.attempt_id),)
        for name in (relative, relative + '.manifest.json')]
    assert not set(repeated) & expected


@pytest.mark.parametrize("custody", ("success",), indirect=True)
def test_control_path_batch_refuses_an_ancestor_replaced_during_consumption(custody, monkeypatch):
    from empirical_lawhood.infrastructure.artifacts import ExternalRootUnavailable
    original = owner._RecoveryControlBatch.receipt_event
    changed = []

    def replace_ancestor(self, receipt, **arguments):
        result = original(self, receipt, **arguments)
        if not changed:
            directory = custody.root / 'runs' / custody.index.run_id / 'receipts'
            retained = directory.with_name('original-receipts')
            directory.rename(retained)
            directory.symlink_to(retained, target_is_directory=True)
            changed.append(True)
        return result

    monkeypatch.setattr(owner._RecoveryControlBatch, 'receipt_event', replace_ancestor)
    with pytest.raises((owner.RunRecoveryError, ArtifactIdentityConflict, ExternalRootUnavailable)):
        with custody.plane.read_context() as plane:
            _census(custody, owner.ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane))
    assert changed == [True]
