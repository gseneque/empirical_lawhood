# SPDX-License-Identifier: MPL-2.0
"""Complete lookup rosters preserve ambiguity and exact predecessor graphs."""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api.recursive_read_indexes import AncestryIndex, ReceiptProductIndex, grouped_index, product_record_index, unique_index
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import LogicalArtifactIdentity
from tests.runtime_platform.test_artifact_verification_scope import _publication


@dataclass(frozen=True, slots=True)
class IndexReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/index-receipt'
    receipt_id: str
    output_logical_artifacts: tuple[LogicalArtifactIdentity, ...]


def test_complete_grouped_and_unique_indexes_keep_duplicate_meaning():
    rows = (('first', 1), ('second', 2), ('first', 3))
    assert grouped_index(rows, lambda row: row[0])['first'] == (rows[0], rows[2])
    with pytest.raises(PermissionError, match='duplicate'):
        unique_index(rows, lambda row: row[0], label='exposed')
    values = tuple(dict(task_id='exposed.task', schema='exposed.schema', ordinal=i) for i in range(3))
    grouped = product_record_index(dict(product_index=values))
    assert grouped['exposed.task', 'exposed.schema'] == values
    with pytest.raises(TypeError):
        grouped['new'] = ()


def test_receipt_index_preserves_exact_receipt_join_and_ambiguity(tmp_path):
    _, outputs = _publication(tmp_path, 2)
    receipt = IndexReceipt('exposed.receipt', tuple(row.logical for row in outputs))
    products = dict(receipts={'task': receipt}, outputs={row.logical.logical_artifact_id: row for row in outputs})
    row = outputs[0].logical
    artifact = SimpleNamespace(artifact_id=row.logical_artifact_id, sha256=row.content_sha256,
        payload_schema=row.payload_schema)
    exact = ObjectIdentity.from_record(receipt.receipt_id, receipt)
    assert ReceiptProductIndex(products).matches(exact, artifact) == (outputs[0],)
    foreign = ObjectIdentity.from_record('foreign.receipt', receipt)
    assert ReceiptProductIndex(products).matches(foreign, artifact) == ()
    products['receipts']['repeated-task'] = receipt
    assert ReceiptProductIndex(products).matches(exact, artifact) == (outputs[0], outputs[0])
    products['outputs']['second-copy'] = outputs[0]
    assert ReceiptProductIndex(products).by_content[row.content_sha256] == (outputs[0], outputs[0])


def test_ancestry_shared_diamond_and_deep_history_have_one_exact_depth():
    rows = [('root', ()), ('left', ('root',)), ('right', ('root',)),
        ('diamond', ('left', 'right')), ('root', ())]
    for number in range(1500):
        rows.append((number, ('diamond',) if number == 0 else (number - 1,)))
    indexed = AncestryIndex(rows)
    assert indexed.depth('diamond') == 3 and indexed.depth(1499) == 1503
    assert len(indexed.parents) == 1504
    with pytest.raises(TypeError):
        indexed.parents['root'] = ('diamond',)


@pytest.mark.parametrize('rows', (
    (('root', ('missing',)),),
    (('root', ('root',)),),
    (('left', ('right',)), ('right', ('left',))),
    (('root', ()), ('left', ('root', 'root'))),
    (('root', ()), ('left', ('root',)), ('left', ())),
))
def test_ancestry_refuses_incomplete_duplicate_conflicting_or_cyclic_graph(rows):
    with pytest.raises(ValueError):
        AncestryIndex(rows)
