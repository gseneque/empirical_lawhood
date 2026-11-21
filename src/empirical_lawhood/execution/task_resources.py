"""Shared progress-based reservations; scientific task assignments remain adapter-owned."""

from __future__ import annotations

from decimal import Decimal as D
from hashlib import sha256

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.execution.execution import OperationalFailureClass
from empirical_lawhood.execution.execution_envelope import ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec, NonTimeResourceBudget, ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.execution.plans import ProtocolTemplate


def progress_resource_envelope(
    *,
    prefix: str,
    design: CanonicalRecord,
    protocol: ProtocolTemplate,
    issued_extensions: ObjectIdentity,
    summed_wall_time_ceiling_seconds: int | None,
    native_preparations: tuple[tuple[str, str, str], ...],
    progress_counter: str,
    heartbeat_seconds: D,
    maximum_concurrency: int,
    maximum_memory_bytes: int,
    terminal_failure_codes: tuple[str, ...],
) -> ExecutionResourceEnvelopeSpec:
    """Assemble resources; the optional sum is a reservation, not CPU use.

    Parallelism does not shorten this sum, and core counts do not multiply it.
    It creates no runtime deadline. An unlimited step requires an unlimited sum.
    """
    if summed_wall_time_ceiling_seconds is not None:
        if (type(summed_wall_time_ceiling_seconds) is not int
                or summed_wall_time_ceiling_seconds < 0):
            raise ValueError("summed wall-time reservation ceiling must be nonnegative or unlimited")
        reservations = tuple(s.resource_budget.wall_time_seconds for s in protocol.steps)
        if None in reservations or sum(reservations) > summed_wall_time_ceiling_seconds:
            raise ValueError("summed task wall-time reservations exceed the frozen ceiling")
    native_by_task = {task: (unit, preparation) for task, unit, preparation in native_preparations}
    if len(native_by_task) != len(native_preparations) or not set(native_by_task) <= {
        s.step_id for s in protocol.steps
    }:
        raise ValueError("native resource census contains duplicate or absent tasks")
    cells = []
    for step in protocol.steps:
        assignment = native_by_task.get(step.step_id)
        native = assignment is not None
        root, preparation = (None, None) if assignment is None else assignment
        budget = step.resource_budget
        cells.append(
            ExecutionResourceTaskCellSpec(
                f"cell.{step.step_id}",
                step.step_id,
                prefix,
                root,
                preparation,
                1,
                int(native),
                int(native),
                native,
                NonTimeResourceBudget(
                    f"budget.{step.step_id}",
                    budget.cpu_cores,
                    budget.memory_bytes,
                    budget.output_bytes,
                    0,
                    budget.source_scan_bytes,
                ),
                None
                if not native
                else ProgressLivenessContract(
                    f"progress.{step.step_id}",
                    ProgressHeartbeat.SCHEMA,
                    progress_counter,
                    heartbeat_seconds,
                    True,
                    True,
                ),
                None,
                None,
            )
        )
    return ExecutionResourceEnvelopeSpec(
        f"{prefix}.resources",
        issued_extensions,
        tuple(sorted(cells, key=lambda v: v.cell_id)),
        (ChildResourceTokenLimit(prefix, len(native_by_task), 0),),
        (),
        (),
        tuple(
            sorted(
                {
                    *terminal_failure_codes,
                    *(v.value for v in OperationalFailureClass),
                }
            )
        ),
        None,
        None,
        maximum_concurrency,
        maximum_memory_bytes,
        (),
        (),
        sha256(
            canonical_json_bytes(
                {"protocol": protocol.fingerprint(), "design": design.fingerprint()}
            )
        ).hexdigest(),
        True,
        True,
        True,
        True,
    )
