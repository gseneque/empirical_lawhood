"""Authorized sealed-receiver loading and reduction boundary."""
from pathlib import Path
from empirical_lawhood.domains.optics.fine_steering_mirror.contracts import FineSteeringMirrorProtocolSpec, FineSteeringMirrorBlockResponse
from empirical_lawhood.domains.optics.fine_steering_mirror.observation import reduce_block
from empirical_lawhood.adapters.physical.fine_steering_mirror.observation import load_safe_array

def reveal_evaluation_blocks(
    *,
    action_paths: tuple[Path, Path, Path],
    sealed_receiver_paths: tuple[Path, Path, Path],
    protocol: FineSteeringMirrorProtocolSpec,
) -> tuple[FineSteeringMirrorBlockResponse, ...]:
    """Open sealed receivers only inside the evaluator and reduce one block per action."""

    blocks: list[FineSteeringMirrorBlockResponse] = []
    for index, level in enumerate(protocol.action_levels_volts):
        actions = load_safe_array(
            action_paths[index],
            expected_realizations=3,
            operator=protocol.observation_operator,
        )
        receivers = load_safe_array(
            sealed_receiver_paths[index],
            expected_realizations=3,
            operator=protocol.observation_operator,
        )
        blocks.append(
            reduce_block(
                block_id=f"fsm-evaluation-{int(level * 1000)}mv-block-1",
                action_level_volts=level,
                actions=actions,
                receivers=receivers,
                realization_start=0,
                operator=protocol.observation_operator,
            )
        )
    return tuple(blocks)
