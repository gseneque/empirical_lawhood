# SPDX-License-Identifier: MPL-2.0
"""Ordered parallel subcalculations within an already admitted task budget.

This helper is not a second scheduler. The caller has one existing task and
supplies its declared CPU ceiling. Results remain in input order and every
thread is joined before returning or propagating an error. It performs no
custody, native retries, numerical-thread reconfiguration or publication.
"""
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from empirical_lawhood.execution.resources.capacity import observe_capacity

_Input = TypeVar("_Input")
_Result = TypeVar("_Result")


def ordered_task_map(function: Callable[[_Input], _Result], values: Iterable[_Input], *,
                     maximum_workers: int, thread_name_prefix: str) -> tuple[_Result, ...]:
    """Evaluate independent subproblems within the task and actual CPU bounds."""
    if type(maximum_workers) is not int or maximum_workers < 1:
        raise ValueError("task subcalculations require a positive declared worker ceiling")
    if not callable(function):
        raise TypeError("task subcalculations require a code-owned callable")
    if type(thread_name_prefix) is not str or not thread_name_prefix:
        raise ValueError("task subcalculations require a diagnostic thread name")
    workers = min(maximum_workers, observe_capacity().cpu_cores)
    if workers == 1:
        return tuple(map(function, values))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix=thread_name_prefix) as pool:
        return tuple(pool.map(function, values))
