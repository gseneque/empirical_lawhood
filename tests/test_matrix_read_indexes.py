# SPDX-License-Identifier: MPL-2.0
"""Complete roster lookup work and unchanged refusal boundaries."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_read_indexes import product_record_index, unique_index
from empirical_lawhood.api.matrix_selected_e3_e4_read import _record_bytes
from empirical_lawhood.api.matrix_full_factor_custody import _output
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus


class _Once:
    def __init__(self, rows):
        self.rows = rows
        self.reads = 0

    def __iter__(self):
        self.reads += 1
        assert self.reads == 1, 'repeated whole-roster scan'
        return iter(self.rows)


@pytest.mark.parametrize('count', (8, 64))
def test_product_lookup_scans_once_and_keeps_missing_and_ambiguous_records(count):
    rows = [{'task_id': 'task.' + str(n), 'schema': ObjectIdentity.SCHEMA} for n in range(count)]
    rows += [dict(rows[0])]
    products = {'product_index': _Once(rows), 'receipts': {}}
    index = product_record_index(products)
    for n in range(count):
        assert _record_bytes(None, products, 'missing.' + str(n), ObjectIdentity, product_lookup=index) is None
    with pytest.raises(ValueError, match='aliases'):
        _record_bytes(None, products, 'task.0', ObjectIdentity, product_lookup=index)
    with pytest.raises(ValueError, match='producer receipt'):
        _record_bytes(None, products, 'task.1', ObjectIdentity, product_lookup=index)
    assert len(index) == count and sum(map(len, index.values())) == count + 1


def test_task_index_keeps_foreign_and_duplicate_task_refusals():
    rows = _Once([SimpleNamespace(task_id='task.original', outputs=())])
    index = unique_index(rows, lambda row: row.task_id, label='task')
    plan = SimpleNamespace(tasks=rows)
    receipt = SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED)
    with pytest.raises(PermissionError, match='exact successful'):
        _output(None, {'receipts': {'task.foreign': receipt}}, plan, 'task.foreign', 'product', task_index=index)
    with pytest.raises(PermissionError, match='exact output'):
        _output(None, {'receipts': {'task.original': receipt}}, plan, 'task.original', 'product', task_index=index)
    with pytest.raises(PermissionError, match='duplicate'):
        unique_index([rows.rows[0], rows.rows[0]], lambda row: row.task_id, label='task')
