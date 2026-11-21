# SPDX-License-Identifier: MPL-2.0
"""Bounded optional comparator checks; no native science qualification."""
import json
import math

import numpy as np
import pytest

from empirical_lawhood.methods.model_free.comparators import (
    assess_discrete_gle_comparator, compression_diagnostic,
    fit_discrete_gle_comparator, nonlinear_response_diagnostic,
    path_reversal_diagnostic,
)


def discrete_control(initial):
    q, v = np.zeros(100), np.zeros(100)
    v[0], v[1] = initial
    q[1] = .1*v[0]
    for t in range(1, 99):
        v[t+1] = v[t]-.1*(.8*q[t]+.1*(2*v[t]+.5*v[t-1]))
        q[t+1] = q[t]+.1*v[t]
    return {"position": q.tolist(), "velocity": v.tolist()}


@pytest.mark.numerical(oracle="A separately generated deterministic Euler memory-force equation with exact two-tap kernel [2,0.5]")
def test_discrete_gle_is_explicitly_fitted_and_predicts_held_control():
    model = fit_discrete_gle_comparator({"train": discrete_control((.3, 1.))},
        sample_interval=.1, spring_constant=.8, history_order=2)
    assert model["status"] == "FITTED"
    assert model["phase"] == "FIT"
    assert model["physical_kernel_identified"] is False
    np.testing.assert_allclose(model["coefficients"], [2., .5], atol=1e-12)
    result = assess_discrete_gle_comparator(model, root_id="held", **discrete_control((-.7, .2)))
    assert result["mean_square_error"] < 1e-26
    with pytest.raises(ValueError, match="distinct"):
        assess_discrete_gle_comparator(model, root_id="train", **discrete_control((-.7, .2)))


def test_unidentifiable_gle_refuses_even_with_regularization():
    result = fit_discrete_gle_comparator({"r": {"position": [0.]*20, "velocity": [0.]*20}},
        sample_interval=1., spring_constant=1., history_order=2, ridge=1.)
    assert result["status"] == "UNRESOLVED"
    assert result["design_rank"] == 0


def test_compression_uses_fixed_encoding_and_preserves_shuffle_control():
    result = compression_diagnostic([0]*256, alphabet_size=2, prefix_lengths=(64, 256),
                                    shuffle_repetitions=2, seed=0)
    assert result["status"] == "DESCRIPTIVE"
    assert all(row["shuffle_mean_minus_observed_bits_per_symbol"] == 0 for row in result["prefixes"])
    assert result["fit_required"] is False
    json.dumps(result, allow_nan=False)


@pytest.mark.numerical(oracle="Exact reversal symmetry of the equal-root alternating two-state path law")
def test_reversible_word_law_and_explicit_parity():
    roots = {"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]}
    result = path_reversal_diagnostic(roots, alphabet_size=2, reversal_map=(0, 1), order=1,
        sample_interval=.2, stationarity_qualified=True, reversal_qualified=True, memory_order_qualified=True)
    assert result["observed_path_kl"] == 0
    assert result["entropy_production_claim"] is False
    assert result["status"] == "DESCRIPTIVE"
    with pytest.raises(ValueError, match="involution"):
        path_reversal_diagnostic(roots, alphabet_size=3, reversal_map=(1, 2, 0), order=1, sample_interval=1.)
    with pytest.raises(ValueError, match="physical"):
        path_reversal_diagnostic(roots, alphabet_size=2, reversal_map=(0, 1), order=1, sample_interval=1., clock="optimizer")


def test_missing_reverse_word_is_unresolved_not_pseudocount_entropy():
    result = path_reversal_diagnostic({"r": [0, 1, 2, 0]}, alphabet_size=3,
        reversal_map=(0, 1, 2), order=1, sample_interval=1.)
    assert result["status"] == "UNRESOLVED"
    assert result["observed_path_kl"] is None
    assert len(result["missing_reverse_words"]) == 3


@pytest.mark.numerical(oracle="Exact finite-state permutation pushforward: p_shift(j)=p(j-1), with explicitly enumerated probability masses")
def test_nonlinear_response_identity_does_not_self_normalize():
    p = np.array([.1, .2, .3, .4])
    values = np.array([-1., 0., 1., 2.])
    states = np.repeat(np.arange(4), [1, 2, 3, 4])
    baseline = values[states]
    changed = values[(states+1) % 4]
    logratio = np.log(p[(states-1) % 4]/p[states])
    result = nonlinear_response_diagnostic(baseline, changed, logratio,
        root_ids=[str(i) for i in range(len(states))], observable_bounds=(-1, 2),
        log_weight_upper=math.log(4), density_identity_qualified=True, intervention_qualified=True)
    assert result["signed_difference"] == pytest.approx(0., abs=1e-15)
    assert result["mean_weight"] == pytest.approx(1.)
    assert result["self_normalized"] is False
    assert result["confidence_interval"][0] <= 0 <= result["confidence_interval"][1]


def test_nonlinear_finite_variance_and_overflow_are_not_assumed():
    result = nonlinear_response_diagnostic([1, 2], [1, 2], [0, 0], root_ids=["a", "b"])
    assert result["status"] == "DESCRIPTIVE" and not result["finite_sample_certificate"]
    result = nonlinear_response_diagnostic([1, 2], [1, 2], [701, 0], root_ids=["a", "b"])
    assert result["status"] == "UNRESOLVED"
    result = nonlinear_response_diagnostic([1, 2], [1, 2], [-1000, -1000], root_ids=["a", "b"])
    assert result["descriptive_weight_ess"] == 2
    json.dumps(result, allow_nan=False)
