# SPDX-License-Identifier: MPL-2.0
"""Read-local indexes over complete, already authenticated Matrix rosters."""

from types import MappingProxyType


def unique_index(rows, key, *, label):
    """Index the complete roster once; never silently choose a duplicate."""
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result:
            raise PermissionError('Matrix original ' + label + ' roster contains a duplicate identity')
        result[identity] = row
    return MappingProxyType(result)


def product_record_index(products):
    # A task may publish several archives of the same schema. Preserve every
    # member; a consumer requiring one scientific record refuses ambiguity.
    grouped = {}
    for row in products['product_index']:
        grouped.setdefault((row['task_id'], row['schema']), []).append(row)
    return MappingProxyType({key: tuple(rows) for key, rows in grouped.items()})
