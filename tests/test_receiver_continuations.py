# SPDX-License-Identifier: MPL-2.0
"""Physical, causal and finite-sample controls for the receiver continuation workflows."""

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    PACK_SIGN,
    fold,
)
from empirical_lawhood.domains.matrix.projected_memory.linear import analytic_controls
from empirical_lawhood.domains.matrix.projected_memory.diagnostics import (
    harmonic_force_check,
)
from empirical_lawhood.methods.linear_memory.elimination import impulse_hankel
from empirical_lawhood.domains.quantum.marked_event_response.physics import (
    compressions,
    consequences,
    direct_late_count,
    receivers,
    replay,
    system,
)
from empirical_lawhood.methods.linear_memory.elimination import switched_elimination
from empirical_lawhood.methods.marked_process.consequences import (
    apply_projection,
    empirical_residual,
    paired_lower_contributions,
    projection,
)
from empirical_lawhood.methods.statistics.conditional_response import (
    fair_energy,
    paired_mean_loss,
)


def test_one_global_lift_preserves_same_prefix_and_opposite_orientation():
    raw = np.random.default_rng(3331).normal(size=(12, 2, 3, 16))
    canonical, bit, fixed = fold(raw)
    reversed_lift, other_bit, other_fixed = fold(raw * PACK_SIGN)
    np.testing.assert_array_equal(canonical, reversed_lift)
    assert not fixed and not other_fixed and bit + other_bit == 1
    different = raw.copy()
    different[6:] *= PACK_SIGN
    assert not np.array_equal(fold(different)[0], canonical)
    assert fold(np.zeros_like(raw))[2]


def test_switched_elimination_propagates_hidden_initial_force_and_noise():
    maps = np.array(
        [[[0.8, 0.4], [-0.3, 0.5]], [[0.7, -0.1], [0.2, 0.6]], [[0.6, 0.3], [0.1, 0.4]]]
    )
    initial = np.array([-0.7, 1.2])
    forcing = np.array([[0.0, 0.4], [0.2, -0.3], [-0.1, 0.5]])
    full = [initial]
    for matrix, force in zip(maps, forcing, strict=True):
        full.append(matrix @ full[-1] + force)
    np.testing.assert_allclose(
        switched_elimination(maps, forcing, initial, 1), np.array(full)[:, :1]
    )
    controls = analytic_controls()
    np.testing.assert_allclose(controls["static_stiffness"], [2.0, 2.0])
    assert controls["memory_error"] < 1e-12


def test_conditional_mean_and_fair_joint_scores():
    spectrum = impulse_hankel(
        np.diag([0.5, 0.75]), np.ones((2, 1)), np.ones((1, 2)), (1, 2, 4)
    )
    assert [row["numerical_rank"] for row in spectrum] == [1, 2, 2]
    assert harmonic_force_check() < 1e-13
    assert paired_mean_loss(1.0, np.array([0.0]), np.array([2.0]))[0] == -1.0
    rng = np.random.default_rng(554)
    truth = rng.multivariate_normal([0, 0], [[1, 0.92], [0.92, 1]], size=512)
    coherent = rng.multivariate_normal([0, 0], [[1, 0.92], [0.92, 1]], size=512)
    wrong = coherent.copy()
    wrong[:, 1] *= -1
    assert fair_energy(coherent, truth) < fair_energy(wrong, truth)


def test_event_left_limit_empty_history_full_replay_and_independent_density():
    args = (4, 2, 1.0, 0.4, 0.7)
    basis, _, unitary, _, initial = system(*args)
    clock, operators = receivers(args, 4)
    times, marks = np.array([clock[1]]), np.array([0])
    code = compressions(times, marks, clock, 4)
    assert np.all(code[:2] == 0) and code[2, 1] == 1
    states = replay(times, marks, clock, basis, unitary, initial)
    w, k = consequences(states, operators, basis, args[-1])
    np.testing.assert_allclose(w.sum(axis=1), 1.4, atol=1e-12)
    np.testing.assert_allclose(k[:, :, 1], 0.0, atol=1e-12)
    state = states[0]
    post = state * basis.occupations[:, 0]
    reference = direct_late_count(
        args, 0, start=clock[0], initial_state=post / np.linalg.norm(post)
    ) - direct_late_count(args, 0, start=clock[0], initial_state=state)
    assert k[0, 0, 0] == pytest.approx(reference, abs=1e-10)


def test_weighted_projection_unseen_cells_and_independent_pair_loss():
    codes = np.array([0, 0, 1, 1])
    activity = np.ones((4, 1))
    y = np.array([[1.0], [-1.0], [3.0], [3.0]])
    table = projection(codes, activity, y, 0.0)
    out, matched = apply_projection(np.array([0, 1, 10]), table)
    np.testing.assert_allclose(out[:, 0], [0.0, 3.0, 1.5])
    assert matched.tolist() == [True, True, False]
    assert empirical_residual(codes, activity, y) == pytest.approx(0.5)
    loss = paired_lower_contributions(codes, activity, y, maximum_rate=1.0)
    np.testing.assert_allclose(loss[:, 0], [2.0, 0.0])
