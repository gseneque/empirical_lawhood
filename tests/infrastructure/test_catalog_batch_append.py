# SPDX-License-Identifier: MPL-2.0
"""Bounded SQL batches preserve exact projection rows and atomic conflicts."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import pytest
from sqlalchemy import event

from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.sql import repository as owner
from empirical_lawhood.runtime.catalog import (
    CatalogSnapshot, ExplorationAttemptRecord, KnowledgeEdgeRecord, MetricDefinitionRecord,
    MetricObservationRecord, ReceiptLocatorRecord,
)
from tests.api.test_catalog_facade import _snapshot


def _complete_snapshot(path, count):
    base = _snapshot(path)
    keys = tuple(f'{i:04d}' for i in range(count))
    root = base.storage_roots[0]
    return replace(base,
        logical_artifacts=tuple(replace(base.logical_artifacts[0], logical_artifact_id='logical.' + k) for k in keys),
        artifact_locators=tuple(replace(base.artifact_locators[0], materialization_id='artifact.' + k,
            logical_artifact_id='logical.' + k, relative_path='artifacts/' + k + '.json') for k in keys),
        receipts=tuple(ReceiptLocatorRecord('receipt.' + k, 'run.disclosed.' + k, root.storage_root_id,
            'receipts/' + k + '.json', '2' * 64, 'empirical-lawhood/testing/catalog-receipt',
            root.verification_status) for k in keys),
        scientific_objects=tuple(replace(base.scientific_objects[0], scientific_object_id='object.' + k,
            object_sha256=sha256(('object.' + k).encode()).hexdigest(),
            artifact_materialization_id='artifact.' + k, receipt_id='receipt.' + k) for k in keys),
        knowledge_edges=tuple(KnowledgeEdgeRecord('edge.' + k, 'supports', 'object.' + keys[0],
            'object.' + k, None if i % 2 else 'object.' + k, 'scope.disclosed') for i, k in enumerate(keys)),
        metric_definitions=(MetricDefinitionRecord('metric.disclosed', 'error', 'dataset.disclosed',
            'relation.disclosed', 'denominator.disclosed', 'response.disclosed', 'horizon.disclosed',
            'm', 'mean', 'lower'),),
        metric_observations=tuple(MetricObservationRecord('observation.' + k, 'metric.disclosed',
            'object.' + k, Decimal('0.12345678901234567890123456789'), None, None, 7, 21) for k in keys),
        exploration_attempts=tuple(ExplorationAttemptRecord('attempt.' + k, 'object.' + k,
            'unevaluable', ('incomplete', 'retained'), ('artifact.' + k,)) for k in keys))


@pytest.mark.parametrize('count', (12, 64))
def test_append_uses_one_batch_per_table_and_bounded_identity_censuses(tmp_path, count):
    snapshot = _complete_snapshot(tmp_path, count)
    engine = create_catalog_engine(f'sqlite+pysqlite:///{tmp_path / "catalog.sqlite"}')
    try:
        upgrade_catalog(engine)
        repository = owner.SQLiteCatalogRepository(engine)
        statements = []

        def observe(_connection, _cursor, statement, parameters, _context, executemany):
            statements.append((statement.split()[0], len(parameters) if executemany else 1))

        event.listen(engine, 'before_cursor_execute', observe)
        repository.append_snapshot(snapshot)
        event.remove(engine, 'before_cursor_execute', observe)
        assert sum(kind == 'INSERT' for kind, _ in statements) == 12
        assert sum(kind == 'SELECT' for kind, _ in statements) == 11
        assert max(size for _, size in statements) <= owner._CATALOG_BATCH_ROWS
        assert repository.snapshot().canonical_bytes() == snapshot.canonical_bytes()
        assert repository.integrity_check() == ()
        before = repository.snapshot()
        conflicting = replace(CatalogSnapshot.empty(),
            storage_roots=(replace(snapshot.storage_roots[0], storage_root_id='new-root-before-conflict'),),
            logical_artifacts=(snapshot.logical_artifacts[0],))
        with pytest.raises(owner.CatalogWriteConflict):
            repository.append_snapshot(conflicting)
        assert repository.snapshot() == before  # Earlier inserts rolled back with the conflict.
    finally:
        engine.dispose()


def test_small_batches_split_without_losing_reasons_edges_or_decimal_precision(tmp_path, monkeypatch):
    monkeypatch.setattr(owner, '_CATALOG_BATCH_ROWS', 3)
    snapshot = _complete_snapshot(tmp_path, 8)
    engine = create_catalog_engine(f'sqlite+pysqlite:///{tmp_path / "small.sqlite"}')
    try:
        upgrade_catalog(engine)
        repository = owner.SQLiteCatalogRepository(engine)
        repository.append_snapshot(snapshot)
        assert repository.snapshot().canonical_bytes() == snapshot.canonical_bytes()
    finally:
        engine.dispose()
