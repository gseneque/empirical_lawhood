# SPDX-License-Identifier: MPL-2.0
"""Indexes over complete authenticated rosters; none supplies read authority."""

from types import MappingProxyType

from empirical_lawhood.science.identity.provenance import ObjectIdentity


def unique_index(rows, key, *, label):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result:
            raise PermissionError(label + ' roster contains a duplicate identity')
        result[identity] = row
    return MappingProxyType(result)


def grouped_index(rows, key):
    """Keep every occurrence, including duplicates that a unique join refuses."""
    grouped = {}
    for row in rows:
        grouped.setdefault(key(row), []).append(row)
    return MappingProxyType({key: tuple(values) for key, values in grouped.items()})


def product_record_index(products):
    return grouped_index(products['product_index'], lambda row: (row['task_id'], row['schema']))


class ReceiptProductIndex:
    """Exact producing receipt joins, preserving repeated and ambiguous products."""

    def __init__(self, products):
        rows = []
        for receipt in products['receipts'].values():
            identity = ObjectIdentity.from_record(receipt.receipt_id, receipt)
            for logical in receipt.output_logical_artifacts:
                key = (identity, logical.logical_artifact_id, logical.content_sha256, logical.payload_schema)
                rows.append((key, products['outputs'][logical.logical_artifact_id]))
        self.by_receipt = grouped_index(rows, lambda row: row[0])
        self.by_content = grouped_index(products['outputs'].values(), lambda row: row.logical.content_sha256)

    def matches(self, receipt, artifact):
        key = (receipt, artifact.artifact_id, artifact.sha256, artifact.payload_schema)
        return tuple(row[1] for row in self.by_receipt.get(key, ()))


class AncestryIndex:
    """Complete immutable predecessor graph with one cycle check and depth pass."""

    def __init__(self, rows):
        parents = {}
        for identity, predecessors in rows:
            if len(set(predecessors)) != len(predecessors):
                raise ValueError('contribution ancestry repeats a predecessor')
            if identity in parents and parents[identity] != predecessors:
                raise ValueError('contribution ancestry changes one exact predecessor census')
            parents[identity] = predecessors
        if any(parent not in parents for values in parents.values() for parent in values):
            raise ValueError('contribution ancestry omits an exact predecessor')
        # Iterative DFS supports deep retained histories without Python recursion.
        depths, active = {}, set()
        for root in parents:
            pending = [(root, False)]
            while pending:
                node, returning = pending.pop()
                if returning:
                    active.remove(node)
                    depths[node] = 1 + max((depths[parent] for parent in parents[node]), default=0)
                elif node not in depths:
                    if node in active:
                        raise ValueError('contribution ancestry cycles')
                    active.add(node)
                    pending.append((node, True))
                    pending.extend((parent, False) for parent in reversed(parents[node]))
        self.parents, self.depths = MappingProxyType(parents), MappingProxyType(depths)

    def depth(self, identity):
        return self.depths[identity]
