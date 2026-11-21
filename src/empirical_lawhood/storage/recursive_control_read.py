# SPDX-License-Identifier: MPL-2.0
"""Optional closed plan views; callers still authenticate original custody."""

from dataclasses import fields

from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
from empirical_lawhood.science.response.normalized_control import NormalizedCanonicalControl
from empirical_lawhood.science.records.serialization import CanonicalRecord

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
        if (size < MIN_VIEW_ORIGINAL_BYTES
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


def decode_authored_control(payloads, name, record_type, *, read_payload=None, maximum_bytes=None):
    """Use a selected view only after both ordinary authenticated byte reads.

    A corrupt selected view refuses. Packets without a selected view and other controls retain
    their original decoder. The payload owner supplies all current access,
    member, format, size and complete final custody checks for each read.
    """
    view_name = CONTROL_VIEWS.get(name)
    if read_payload is None and (view_name is None or view_name not in payloads):
        from empirical_lawhood.storage.recursive_custody import can_read_authored_record
        if can_read_authored_record(payloads):
            return payloads.read_record(name, record_type, maximum_bytes=maximum_bytes)
    read = payloads.__getitem__ if read_payload is None else read_payload
    raw = read(name)
    if maximum_bytes is not None and len(raw) > maximum_bytes:
        raise ValueError('authored control exceeds its selected byte bound')
    if view_name is None or view_name not in payloads.keys():
        return decode_scoped_canonical_bytes(raw, record_type,
            maximum_bytes=max(1, len(raw)) if maximum_bytes is None else maximum_bytes)
    view_raw = read(view_name)
    view = decode_scoped_canonical_bytes(view_raw, NormalizedCanonicalControl, maximum_bytes=len(view_raw))
    if view.original.object_id != 'recursive-member.' + name.removesuffix('.json'):
        raise ValueError('normalised control changes its original member identity')
    return view.restore(raw, record_type, maximum_bytes=max(1, len(raw)))
