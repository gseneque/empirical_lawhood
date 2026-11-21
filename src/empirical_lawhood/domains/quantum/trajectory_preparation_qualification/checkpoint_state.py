"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
import numpy as np
from empirical_lawhood.domains.quantum.trajectory_preparation_qualification.types import TrajectoryCheckpoint, TrajectoryResult


def checkpoint_from_result(
    result: TrajectoryResult,
    clock: float,
) -> TrajectoryCheckpoint:
    if clock not in result.snapshots:
        raise ValueError("requested checkpoint clock is absent")
    events = tuple(event for event in result.events if event.event_time < clock)
    diagnostics = tuple(row for row in result.diagnostics if row.event_time < clock)
    return TrajectoryCheckpoint(
        unit_id=result.unit_id,
        denominator=result.denominator,
        action=result.action,
        l_sites=result.l_sites,
        particles=result.particles,
        clock=clock,
        state=np.asarray(result.snapshots[clock], dtype=np.complex128),
        events=events,
        diagnostics=diagnostics,
        rng_state=result.checkpoint_rng_states[clock],
        rng_draw_count=result.checkpoint_rng_draw_counts[clock],
        maximum_propagator_norm_residual=max(
            (row.propagator_norm_residual for row in diagnostics),
            default=0.0,
        ),
        maximum_post_jump_norm_residual=max(
            (row.post_jump_norm_residual for row in diagnostics),
            default=0.0,
        ),
        maximum_projected_mass_identity_residual=max(
            (row.projected_mass_identity_residual for row in diagnostics),
            default=0.0,
        ),
        maximum_mark_probability_sum_residual=max(
            (row.mark_probability_sum_residual for row in diagnostics),
            default=0.0,
        ),
        maximum_particle_number_residual=max(
            (row.particle_number_residual for row in diagnostics),
            default=0.0,
        ),
    )
