# SPDX-License-Identifier: MPL-2.0
"""Selected-event replay checks and conditional scientific interpretations."""

from empirical_lawhood.domains.matrix.six_matrix_response import shooting as native
from empirical_lawhood.domains.matrix.six_matrix_response.scientific_inputs import SixMatrixResponseScientificSeedInput


def _restart_exact(replay, *, member, view, protocol):
    import json
    import numpy as np
    from empirical_lawhood.domains.matrix.six_matrix_response.simulation import baoab_step, fast_receiver
    from empirical_lawhood.domains.matrix.six_matrix_response.spectral import spectral_receiver
    state, rng = native.state_from_shooting_checkpoint(replay.checkpoints[3])
    while state.step_index < protocol.parent_total_steps:
        state = baoab_step(state, member=member, numerical_view=view,
            next_alpha_tilde_x=float(protocol.target_alpha_tilde_x), next_alpha_tilde_y=float(protocol.target_alpha_tilde_y), rng=rng)
        if state.step_index > 768 and state.step_index % 16 == 0:
            fast_receiver(state=state, member=member)
        if state.step_index > 768 and state.step_index % 256 == 0:
            spectral_receiver(receiver_prefix=f"spectrum.{protocol.parent_rollout_id}.restart.{state.step_index}", q=2, positions=state.positions)
    return bool(np.array_equal(state.positions, replay.final_state.positions)
        and np.array_equal(state.momenta, replay.final_state.momenta)
        and json.dumps(rng.bit_generator.state, sort_keys=True, separators=(",", ":")) == replay.final_rng_state_json)



def _typed_seed(seed, *, role, root_id, context, source, receipt):
    return SixMatrixResponseScientificSeedInput(role, root_id, context, seed.stream_index,
        seed.full_seed_sha256, source.object_fingerprint, source, receipt)



def _validate_branch(branch, checkpoint, seed):
    if (branch.checkpoint_id, branch.checkpoint_step, branch.branch_index, branch.seed_document_sha256) != (
        checkpoint.checkpoint_id, checkpoint.parent_step, seed.stream_index, seed.full_seed_sha256):
        raise ValueError("Selected branch changes its checkpoint or allocated effective driver")



def _validate_replay(transport, config, parent, implementation_commit):
    result = transport.replay_result
    if (result.config_fingerprint, result.implementation_commit, result.parent_implementation_commit,
        result.parent_report_sha256, result.parent_rollout_id, result.derived_rng_seed_sha256,
        result.expected_final_state_sha256) != (
        config.protocol.fingerprint(), implementation_commit, parent.implementation_commit,
        parent.fingerprint(), parent.rollout.rollout_id, parent.rollout.rng_seed_sha256,
        parent.rollout.final_state_sha256):
        raise ValueError("Selected replay changes its actual parent, code or protocol")
    if transport.rng_stream.derived_seed_sha256 != parent.rollout.rng_seed_sha256:
        raise ValueError("Selected replay transport changes its actual parent driver")



def selected_event_summary(report, parent):
    return {"report_sha256": report.fingerprint(), "conditional_source_instance": parent.conditional_source_instance,
        "independent_selected_events": 1, "requested_conditional_futures": 448,
        "numerical_axis": report.numerical_axis, "committor_morphology_axis": report.committor_morphology_axis,
        "residence_axis": report.residence_axis, "stability_axis": report.stability_axis,
        "amplitude_null_axis": report.amplitude_null_axis, "combined_interpretation": report.combined_interpretation,
        "scientific_terminal": report.scientific_terminal, "reason_codes": report.reason_codes,
        "condition_false_descendants": report.condition_false_descendants,
        "selection_exposed": True, "evidence_ceiling": "NON_PROMOTABLE"}

