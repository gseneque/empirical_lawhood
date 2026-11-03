# SPDX-License-Identifier: MPL-2.0
"""Optional closed plan views; callers still authenticate original custody."""

from dataclasses import fields

from empirical_lawhood.kernel.decoded_record_store import decode_scoped_canonical_bytes
from empirical_lawhood.kernel.normalized_control import MAX_CONTROL_BYTES, NormalizedCanonicalControl
from empirical_lawhood.kernel.serialization import CanonicalRecord

CONTROL_VIEWS = {
    'run-plan.json': 'run-plan.normalized.json',
    'execution-plan.json': 'execution-plan.normalized.json',
}
MIN_VIEW_ORIGINAL_BYTES = 256 * 1024


def _shared_operand_bytes(record):
    """Cheap conservative selection from already compiled immutable operands."""
    seen, pending, savings = set(), [record], 0
    while pending:
        value = pending.pop()
        if isinstance(value, CanonicalRecord):
            if id(value) in seen:
                savings += max(0, value.canonical_size_bytes() - 96)
                continue
            seen.add(id(value))
            pending.extend(getattr(value, field.name) for field in fields(value))
        elif type(value) in (tuple, frozenset):
            pending.extend(value)
    return savings


def normalized_plan_views(records, *, custody_limits=None):
    """Select only substantial savings; keep every original member unchanged."""
    views = {}
    for name, view_name in CONTROL_VIEWS.items():
        record = records[name]
        size = record.canonical_size_bytes()
        if (not MIN_VIEW_ORIGINAL_BYTES <= size <= MAX_CONTROL_BYTES
                or not record._is_cacheable() or _shared_operand_bytes(record) * 3 < size
                or custody_limits is not None and (custody_limits.canonical_json_depth is not None
                    or custody_limits.canonical_json_token_bytes is not None)):
            continue
        view = NormalizedCanonicalControl.from_record('recursive-member.' + name.removesuffix('.json'), record)
        view_size = view.canonical_size_bytes()
        if (view_size * 4 <= size * 3 and (custody_limits is None or not any(
                custody_limits.exceeds(limit, view_size) for limit in ('control_record_bytes', 'in_memory_payload_bytes')))):
            views[view_name] = view
    return views


def decode_authored_control(payloads, name, record_type, *, read_payload=None):
    """Use a selected view only after both ordinary authenticated byte reads.

    A corrupt selected view refuses. Legacy packets and other controls retain
    their original decoder. The payload owner supplies all current access,
    member, format, size and complete final custody checks for each read.
    """
    read = payloads.__getitem__ if read_payload is None else read_payload
    raw = read(name)
    view_name = CONTROL_VIEWS.get(name)
    if view_name is None or view_name not in payloads.keys():
        return decode_scoped_canonical_bytes(raw, record_type, maximum_bytes=max(1, len(raw)))
    view_raw = read(view_name)
    if len(view_raw) > MAX_CONTROL_BYTES:
        raise ValueError('normalised control exceeds its supported byte bound')
    view = decode_scoped_canonical_bytes(view_raw, NormalizedCanonicalControl, maximum_bytes=MAX_CONTROL_BYTES)
    if view.original.object_id != 'recursive-member.' + name.removesuffix('.json'):
        raise ValueError('normalised control changes its original member identity')
    return view.restore(raw, record_type, maximum_bytes=max(1, len(raw)))
