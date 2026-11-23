# SPDX-License-Identifier: MPL-2.0
"""Reacquire a published finite-response root and compare every original native result."""

from empirical_lawhood.domains.matrix.finite_response_law.contracts import native_invocations
from empirical_lawhood.domains.matrix.finite_response_law.source import (
    execute_native_phase,
    frozen_prefix_frame,
)
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _encode
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from .native_artifact import encode_native_pair
from .provider import native_result_type


def verify_native_root(config, root, views):
    if tuple(v.root for v in views) != (root, root) or tuple(v.refinement for v in views) != (1, 2):
        raise ValueError("Select both published numerical views for this physical root")
    expected = {r.object_id: r for r in views[0].native_results}
    if views[0].native_results != views[1].native_results or len(expected) != 20:
        raise ValueError("Original views do not share the whole native task roster")
    tasks = sorted(
        (t for t in native_invocations(config) if t.root == root),
        key=lambda task: (("prefix", "parent", "future").index(task.phase), task.task_id),
    )
    results, checkpoints = {}, {}
    frame = None
    intervals = 0
    total_bytes = 0
    result_type = native_result_type(config)
    for task in tasks:
        parent = None if task.phase == "prefix" else tasks[0] if task.phase == "parent" else tasks[1]
        states = (None, None) if parent is None else checkpoints[parent.task_id]
        predecessors = () if parent is None else (results[parent.task_id],)
        operands = tuple(
            execute_native_phase(config, task, view, incoming=states[view - 1], frame=frame)
            for view in (1, 2)
        )
        if task.phase != "future":
            checkpoints[task.task_id] = tuple(v.checkpoint for v in operands)
        if task.phase == "prefix":
            frame = frozen_prefix_frame(operands[0].checkpoint)
        if frame is None:
            raise ValueError("Published native frame could not be recovered")
        pair, encoded = encode_native_pair(*operands)
        common = results[tasks[0].task_id] if predecessors else None
        record = result_type(task, predecessors, pair, common, _encode(frame.modes), None)
        identity = ObjectIdentity.from_record(record.result_id, record)
        if identity != expected[record.result_id]:
            raise ValueError("Reacquired checkpoints, native arrays or delivery differ for " + task.task_id)
        results[task.task_id] = identity
        intervals += sum(v.delivery.completed_intervals for v in operands)
        total_bytes += len(encoded)
    return {
        "root": root.stage_unit,
        "physical_unit": root.physical_unit_id,
        "native_phase_views": 2 * len(results),
        "native_intervals": intervals,
        "native_array_bytes": total_bytes,
    }
