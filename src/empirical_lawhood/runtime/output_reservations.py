# SPDX-License-Identifier: MPL-2.0
"""Report frozen output allowances without treating them as disk requirements."""

from contextlib import contextmanager
from contextvars import ContextVar


_selection = ContextVar("output_reservation_selection", default=None)


@contextmanager
def output_reservation_operation(*, allow_overcommit=False):
    """Retain advisory arithmetic and the legacy option without changing limits."""
    if type(allow_overcommit) is not bool:
        raise TypeError("output reservation overcommit requires an explicit boolean")
    record = {"allow_overcommit": allow_overcommit, "policy": "ADVISORY_RESERVATIONS",
        "storage_admission": "OPERATOR_FLOOR_AND_ACTUAL_WRITES", "plans": {},
        "unretained_observation_calls": 0, "scientific_authority": "NONE"}
    token = _selection.set(record)
    try:
        yield record
    finally:
        _selection.reset(token)


def execution_output_floor(plan):
    """Observe allowances; actual storage admission belongs to guarded I/O.

    A task's output ceiling bounds what it can produce. It does not establish
    its scratch requirement or imply that every task will reach that ceiling.
    Neither the total nor the largest allowance is a free-space prerequisite.
    """
    amounts = tuple(task.capability.requested_resources.output_bytes or 0 for task in plan.tasks)
    declared = sum(amounts)
    selected = _selection.get()
    if selected is not None:
        key = plan.execution_plan_id
        plans = selected["plans"]
        if key in plans or len(plans) < 32:
            plans[key] = {"task_count": len(amounts), "declared_output_bytes": declared,
                "effective_plan_floor_bytes": 0}
        else:
            selected["unretained_observation_calls"] += 1
    return 0
