# SPDX-License-Identifier: MPL-2.0
"""Explicit invocation-local RSS allowance for Matrix metadata controllers."""

from contextlib import contextmanager
from contextvars import ContextVar


_selection = ContextVar("metadata_rss_selection", default=None)


@contextmanager
def metadata_rss_operation(*, limit_bytes=None):
    """Select controller RSS admission without rewriting scientific budgets."""
    if limit_bytes is not None and (type(limit_bytes) is not int or limit_bytes <= 0):
        raise ValueError("metadata RSS allowance requires a positive integer byte count")
    record = {"selected_limit_bytes": limit_bytes, "limits": {}, "check_count": 0,
        "unretained_limits": 0, "scientific_authority": "NONE"}
    token = _selection.set(record)
    try:
        yield record
    finally:
        _selection.reset(token)


def metadata_rss_limit(declared_limit):
    """Return and retain the effective controller-only current-RSS ceiling."""
    selected = _selection.get()
    if selected is None:
        return declared_limit
    effective = selected["selected_limit_bytes"]
    if effective is None:
        effective = declared_limit
    selected["check_count"] += 1
    key = str(declared_limit)
    if key in selected["limits"] or len(selected["limits"]) < 16:
        selected["limits"][key] = {"declared_limit_bytes": declared_limit,
            "effective_limit_bytes": effective}
    else:
        selected["unretained_limits"] += 1
    return effective
