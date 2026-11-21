# SPDX-License-Identifier: MPL-2.0
"""Read-local indexes over complete, already authenticated Matrix rosters."""

from empirical_lawhood.api.recursive_read_indexes import product_record_index as product_record_index, unique_index as _unique_index


def unique_index(rows, key, *, label):
    """Index the complete roster once; never silently choose a duplicate."""
    return _unique_index(rows, key, label='Matrix original ' + label)
