# SPDX-License-Identifier: MPL-2.0
"""Current read lifetimes, access closure and explicit retired-layout refusals."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import protected_e3_read_custody as owner


class ReadPlane:
    def __init__(self, *, retired=None):
        self.retired = retired
        self.open_scopes = 0
        self.snapshot_current = True
        self.root = SimpleNamespace(resolve=self.resolve)

    def resolve(self, relative, *, for_write):
        assert for_write is False
        return SimpleNamespace(exists=lambda: relative.endswith('/' + self.retired)
            if self.retired is not None else False)

    @contextmanager
    def read_context(self):
        self.open_scopes += 1
        try:
            yield self
        finally:
            try:
                self.require_verification_snapshot()
            finally:
                self.open_scopes -= 1

    def require_verification_snapshot(self):
        if not self.snapshot_current:
            raise PermissionError('actual evidence changed during read')


def test_missing_reveal_refuses_before_publication_or_scientific_access(monkeypatch):
    monkeypatch.setattr(owner, '_publication', lambda *args: pytest.fail('absent reveal inspected custody'))
    with pytest.raises(PermissionError, match='REVEAL_AUTHORITY_REQUIRED'):
        owner.authorize(object(), None, None)


@pytest.mark.parametrize('retired', ('source-continuation', 'native-parent-closeout'))
def test_retired_layout_refuses_before_authority_or_receipt_decoding(monkeypatch, retired):
    def forbidden(*args, **kwargs):
        pytest.fail('retired layout reached current authority or scientific custody')

    monkeypatch.setattr(owner, 'authorize', forbidden)
    monkeypatch.setattr(owner, 'completed_receipts', forbidden)
    with pytest.raises(PermissionError, match='RETIRED_LAYOUT_UNSUPPORTED'):
        with owner.configured_receipt_read(ReadPlane(retired=retired),
                SimpleNamespace(run_plan_id='run.current'), object(), reveal_authority_id='reveal.current'):
            pytest.fail('retired layout entered a read scope')


def scope_case(monkeypatch):
    plane = ReadPlane()
    package = SimpleNamespace(run_plan_id='run.current')
    receipts, terminal = {'task.current': object()}, object()
    calls = []
    expired = {'value': False}

    def access(writer, selected, reveal):
        assert writer is plane and selected is package and reveal == 'reveal.current'
        calls.append(plane.open_scopes)
        if expired['value']:
            raise PermissionError('actual reveal expired')

    monkeypatch.setattr(owner, 'authorize', access)
    monkeypatch.setattr(owner, '_current_read_grants', access)
    monkeypatch.setattr(owner, 'completed_receipts', lambda *args, **kwargs: (receipts, terminal))
    return plane, package, receipts, terminal, calls, expired


def test_receipt_scope_expires_and_final_access_follows_the_closed_snapshot(monkeypatch):
    plane, package, receipts, terminal, calls, _ = scope_case(monkeypatch)
    with owner.configured_receipt_read(plane, package, object(), reveal_authority_id='reveal.current') as read:
        assert (read.writer, read.receipts, read.terminal) == (plane, receipts, terminal)
        read.require_active()
        read.require_current()
    assert calls == [0, 1, 0]
    assert plane.open_scopes == 0
    for check in (read.require_active, read.require_current, read.require_access):
        with pytest.raises(PermissionError, match='SCOPE_EXPIRED'):
            check()


def test_per_item_access_does_not_rehash_the_snapshot_and_still_refuses_revocation(monkeypatch):
    plane, package, _, _, _, expired = scope_case(monkeypatch)
    snapshots = []
    original = plane.require_verification_snapshot
    def snapshot():
        snapshots.append(1)
        original()
    monkeypatch.setattr(plane, 'require_verification_snapshot', snapshot)
    with owner.configured_receipt_read(plane, package, object(), reveal_authority_id='reveal.current') as read:
        for _ in range(20):
            read.require_access()
        assert snapshots == []
        expired['value'] = True
        with pytest.raises(PermissionError, match='reveal expired'):
            read.require_access()
        expired['value'] = False
        read.require_current()
        assert len(snapshots) == 1
    assert len(snapshots) == 3


def test_reveal_expiring_while_products_are_read_refuses_the_return(monkeypatch):
    plane, package, _, _, calls, expired = scope_case(monkeypatch)
    with pytest.raises(PermissionError, match='actual reveal expired'):
        with owner.configured_receipt_read(plane, package, object(), reveal_authority_id='reveal.current') as read:
            expired['value'] = True
    assert calls == [0, 0]
    with pytest.raises(PermissionError, match='SCOPE_EXPIRED'):
        read.require_current()


def test_mutation_during_products_refuses_before_final_access(monkeypatch):
    plane, package, _, _, calls, _ = scope_case(monkeypatch)
    with pytest.raises(PermissionError, match='evidence changed'):
        with owner.configured_receipt_read(plane, package, object(), reveal_authority_id='reveal.current'):
            plane.snapshot_current = False
    assert calls == [0]


def test_completed_consumer_requires_the_actual_parent_materialization():
    parent_task = SimpleNamespace(task_id='parent', scientific_inputs=())
    edge = SimpleNamespace(producer_task_id='parent', operational_logical_artifact_id='parent.product')
    consumer = SimpleNamespace(task_id='consumer', scientific_inputs=(edge,))
    material = SimpleNamespace(logical_artifact_id='parent.product', materialization_id='parent.actual')
    receipts = {'parent': SimpleNamespace(output_materializations=(material,)),
        'consumer': SimpleNamespace(input_materialization_ids=('parent.actual',))}
    plan = SimpleNamespace(tasks=(parent_task, consumer))
    owner._require_consumed_parents(plan, receipts, {'parent', 'consumer'})
    receipts['consumer'] = SimpleNamespace(input_materialization_ids=('substituted.material',))
    with pytest.raises(PermissionError, match='EXACT_CONSUMED_PARENT'):
        owner._require_consumed_parents(plan, receipts, {'parent', 'consumer'})
