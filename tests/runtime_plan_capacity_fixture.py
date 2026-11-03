# SPDX-License-Identifier: MPL-2.0
"""Disclosed operational byte-capacity fixture; never executable evidence."""

from dataclasses import replace


def expanded_plan_metadata(plan):
    """Retain typed graph edges and expand one task's descriptive obligations.

    These literal software labels test actual canonical bodies above the former
    64 MiB ceiling. They do not represent scientific obligations, an issued plan,
    executable work or a source-authenticated scientific result.
    """
    obligations = tuple(f"software-capacity-{index:05d}-" + "x" * 2_024 for index in range(34_000))
    return replace(plan, tasks=(replace(plan.tasks[0], obligation_ids=obligations), *plan.tasks[1:]))
