"""Development-only analysis for the FSM empirical slice."""

from __future__ import annotations


from empirical_lawhood.domains.optics.fine_steering_mirror.contracts import FineSteeringMirrorBlockResponse
from empirical_lawhood.domains.optics.fine_steering_mirror.observation import fit_development_model, reduce_block


class FineSteeringMirrorDevelopmentError(ValueError):
    """Development inputs violate their frozen identities or scientific gates."""


def analyze_development_arrays(*, action_arrays, receiver_arrays, protocol):
    """Fit and qualify development response from already-authenticated arrays."""
    blocks: list[FineSteeringMirrorBlockResponse] = []
    for action_index, level in enumerate(protocol.action_levels_volts):
        actions = action_arrays[action_index]
        receivers = receiver_arrays[action_index]
        for block_index, start in enumerate((0, 3), start=1):
            blocks.append(
                reduce_block(
                    block_id=(f"fsm-development-{int(level * 1000)}mv-block-{block_index}"),
                    action_level_volts=level,
                    actions=actions,
                    receivers=receivers,
                    realization_start=start,
                    operator=protocol.observation_operator,
                )
            )
    ordered = tuple(sorted(blocks, key=lambda block: block.block_id))
    model = fit_development_model(ordered, protocol.action_levels_volts)
    if any(
        block.maximum_input_matrix_condition > protocol.maximum_input_matrix_condition
        for block in ordered
    ):
        raise FineSteeringMirrorDevelopmentError("development input matrix condition gate failed")
    if any(
        block.period_relative_difference > protocol.maximum_period_relative_difference
        for block in ordered
    ):
        raise FineSteeringMirrorDevelopmentError("development period recurrence gate failed")
    if not all(value < 0 for value in model.slope_hz_per_v):
        raise FineSteeringMirrorDevelopmentError("development slopes do not all have the registered sign")
    if (
        model.slope_hz_per_v[protocol.primary_receiver_index]
        > protocol.maximum_primary_slope_hz_per_v
    ):
        raise FineSteeringMirrorDevelopmentError("primary development slope does not clear the frozen gate")
    return ordered, model
