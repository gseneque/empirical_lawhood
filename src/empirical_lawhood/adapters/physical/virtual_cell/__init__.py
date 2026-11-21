# SPDX-License-Identifier: MPL-2.0
"""Virtual Cell external formats, dataset access and native publication."""

from importlib import import_module

_EXPORTS = {'H5ADStructuralInspection': ('.dataset', 'H5ADStructuralInspection'), 'SegmentedBinaryReader': ('.dataset', 'SegmentedBinaryReader'), 'decode_official_final_top100': ('.leaderboard', 'decode_official_final_top100'), 'inspect_h5ad': ('.dataset', 'inspect_h5ad'), 'summarize_h5ad': ('.dataset', 'summarize_h5ad')}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute = _EXPORTS[name]
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
