# SPDX-License-Identifier: MPL-2.0
"""Dependency blocks require actual direct failed or blocked custody."""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure.recovery import RunRecoveryError, _require_catalog_dependency_causes
from empirical_lawhood.runtime.execution import OperationalFailureClass
from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic, TaskRecoveryDisposition
from tests.recovery_support import case as case


def _chain(case):
    root = case.index.task(case.failed.task_id)
    direct = replace(case.index.task(case.blocked.task_id), dependency_task_ids=(root.task_id,))
    descendant = replace(case.index.task(case.unused.task_id), dependency_task_ids=(direct.task_id,))
    return root, direct, descendant


def _require(chain, events, blocks, *, nonattempts=None, receipts=None):
    _require_catalog_dependency_causes(
        dependency_order=chain, candidate_events=events,
        receipts={} if receipts is None else receipts,
        nonattempts={} if nonattempts is None else nonattempts,
        catalog_blocks=blocks,
    )


def test_direct_failure_then_transitive_catalog_blocks_use_the_actual_causal_chain(case):
    root, direct, descendant = chain = _chain(case)
    _require(chain, {(root.task_id, case.failed_event.attempt_id): case.failed_event},
        {direct.task_id: "dependency-failed", descendant.task_id: "dependency-blocked"})


@pytest.mark.parametrize("damage", ("missing-root", "wrong-direct-reason", "wrong-descendant-reason", "wrong-edge", "successful-root"))
def test_orphan_or_wrong_priority_dependency_blocks_refuse(case, damage):
    root, direct, descendant = chain = _chain(case)
    events = {(root.task_id, case.failed_event.attempt_id): case.failed_event}
    blocks = {direct.task_id: "dependency-failed", descendant.task_id: "dependency-blocked"}
    receipts = {}
    if damage == "missing-root":
        events.clear()
    elif damage == "wrong-direct-reason":
        blocks[direct.task_id] = "dependency-blocked"
    elif damage == "wrong-descendant-reason":
        blocks[descendant.task_id] = "dependency-failed"
    elif damage == "wrong-edge":
        chain = (root, direct, replace(descendant, dependency_task_ids=(root.task_id,)))
    else:
        receipts[root.task_id] = object()
    with pytest.raises(RunRecoveryError, match="actual direct cause"):
        _require(chain, events, blocks, receipts=receipts)


def test_durable_nonattempt_propagates_only_after_actual_failed_parent(case):
    root, direct, descendant = chain = _chain(case)
    nonattempt = next(row for row in case.events if row.task_id == direct.task_id)
    _require(chain, {(root.task_id, case.failed_event.attempt_id): case.failed_event},
        {descendant.task_id: "dependency-blocked"}, nonattempts={direct.task_id: nonattempt})
    with pytest.raises(RunRecoveryError, match="actual direct cause"):
        _require(chain, {}, {descendant.task_id: "dependency-blocked"},
            nonattempts={direct.task_id: nonattempt})


def test_actual_blocked_candidate_requires_blocked_dependency_reason(case):
    root, direct, descendant = chain = _chain(case)
    event = replace(case.failed_event, disposition=TaskRecoveryDisposition.BLOCKED,
        reason_codes=("unknown-completion",), failure=OperationalFailureDiagnostic.create(
            OperationalFailureClass.RECOVERY_OBSTRUCTION,
            sanitized_exception_type="SoftwareUnknown",
            sanitized_message="Disclosed unknown completion"))
    _require(chain, {(root.task_id, event.attempt_id): event},
        {direct.task_id: "dependency-blocked", descendant.task_id: "dependency-blocked"})
    with pytest.raises(RunRecoveryError, match="actual direct cause"):
        _require(chain, {(root.task_id, event.attempt_id): event},
            {direct.task_id: "dependency-failed", descendant.task_id: "dependency-blocked"})
