# SPDX-License-Identifier: MPL-2.0
"""Independent finite-state, finite-frame and path-accounting controls."""
from itertools import combinations
import json
import math

import numpy as np
import pytest

from empirical_lawhood.methods.model_free import (
    ObservationContract, assess_first_passage, assess_root_memory, discretize,
    finite_population_difference, memory_diagnostics, root_lag_counts,
)
from empirical_lawhood.methods.model_free.controls import (
    CONTROL_NAMES, control_diagnostics, hidden_memory_joint,
)
from empirical_lawhood.methods.model_free.uncertainty import (
    allocate_alpha, conditional_bands, hoeffding_halfwidth, root_mean_bands,
    whole_root_bootstrap, zero_failure_upper,
)


@pytest.mark.numerical(oracle="Exact binary Markov three-time probabilities and matrix Chapman-Kolmogorov identity")
def test_markov_joint_has_zero_history_and_ck():
    transition = np.array([[.8, .2], [.3, .7]])
    stationary = np.array([.6, .4])
    joint = np.zeros((2, 2, 2))
    for i in range(2):
        for j in range(2):
            for k in range(2):
                joint[i, j, k] = stationary[i]*transition[i, j]*transition[j, k]
    result = memory_diagnostics(joint)
    assert abs(result["conditional_mutual_information"]) < 1e-14
    assert result["maximum_supported_history_tv"] < 1e-14
    np.testing.assert_allclose(result["ck"]["composed"], transition@transition, atol=1e-14)


@pytest.mark.numerical(oracle="Published proposal's exact hidden binary-state emission law, independently enumerated finite-state control")
def test_zero_linear_correlation_does_not_remove_memory():
    result = memory_diagnostics(hidden_memory_joint(1))
    values = np.array([-1., 0., 1.])
    pair = hidden_memory_joint(1).sum(axis=1)
    assert abs(values@pair@values) < 1e-15
    assert result["ck"]["weighted_kl"] == pytest.approx(.031563670056796465, abs=1e-14)
    assert result["ck"]["maximum_supported_row_tv"] == pytest.approx(.11063808, abs=1e-14)
    assert result["conditional_mutual_information"] == pytest.approx(.05592535187511453, abs=1e-14)
    for lag in (1, 2, 8, 64):
        result = memory_diagnostics(hidden_memory_joint(lag))
        assert result["ck"]["weighted_kl"] <= result["conditional_mutual_information"]+1e-14


def test_streaming_counts_preserve_missing_anchors_and_literal_triples():
    sequence = [0, 1, 0, -1, 1, 0]
    result = root_lag_counts(iter(sequence), [1], alphabet_size=2, root_id="r")
    row = result["lags"]["1"]
    assert row["attempted_anchors"] == 4
    assert row["missing_anchors"] == 3
    assert row["observed_anchors"] == 1
    expected = np.zeros((2, 2, 2), dtype=int)
    expected[0, 1, 0] = 1
    np.testing.assert_array_equal(row["joint_counts"], expected)
    assert result["maximum_retained_samples"] == 3
    with pytest.raises(ValueError, match="outside"):
        root_lag_counts([0, 2, 0], [1], alphabet_size=2)


def test_higher_history_cap_is_unresolved_not_silently_shortened():
    result = root_lag_counts([0, 1]*100, [1, 4], alphabet_size=2, history_order=30, max_cells=100)
    assert result["status"] == "UNRESOLVED"
    assert result["history_order"] == 30
    result = root_lag_counts([0, 1, 1, 0], [1], alphabet_size=2, history_order=2)
    assert np.asarray(result["lags"]["1"]["joint_counts"]).shape == (4, 2, 2)
    assert result["lags"]["1"]["joint_counts"][1][1][0] == 1


def test_transient_protocol_law_cannot_pool_unmatched_ages():
    with pytest.raises(ValueError, match="frozen future-anchor"):
        root_lag_counts([0, 1, 0, 1], [1], alphabet_size=2, record_scope="protocol_age")
    row = root_lag_counts([0, 1, 0, 1], [1], alphabet_size=2, record_scope="protocol_age", anchor_indices=(2,))
    assert row["lags"]["1"]["attempted_anchors"] == 1
    assert row["lags"]["1"]["joint_counts"][0][1][0] == 1


def test_observation_contract_preserves_units_clock_and_tails():
    contract = ObservationContract("q", ("q",), ("length",), ((-1., 0., 1.),), .1, "fixed")
    result = discretize([-1, -.2, 0, 1, 2, float("nan")], contract)
    assert result["symbols"] == [0, 0, 1, 1, -1, -1]
    assert result["out_of_range_rows"] == result["nonfinite_rows"] == 1
    with pytest.raises(ValueError, match="stationarity"):
        ObservationContract("q", ("q",), ("x",), ((-1., 1.),), .1, "p", target_law="stationary")
    clock = ObservationContract("q", ("q",), ("x",), ((-1., 1.),), 1., "p", clock="optimizer")
    with pytest.raises(ValueError, match="physical time"):
        clock.require_physical_time()


@pytest.mark.numerical(oracle="Hoeffding union bound for bounded independent roots, exact zero-failure binomial tail")
def test_root_inference_uses_roots_not_overlapping_origins():
    assert hoeffding_halfwidth(80, 8, .05) == pytest.approx(.1898736585830459)
    roots = [root_lag_counts([0, 1]*1000, [1], alphabet_size=2, root_id=f"r{i}") for i in range(2)]
    result = assess_root_memory(roots)
    assert result["independent_roots"] == 2
    assert result["lags"]["1"]["root_band_halfwidth"] == 1
    assert result["lags"]["1"]["status"] == "UNRESOLVED"
    json.dumps(result, allow_nan=False)
    assert zero_failure_upper(58) > .05
    assert zero_failure_upper(59) < .05
    assert sum(allocate_alpha(.05, comparisons=2, look_index=j, looks=3) for j in range(3))*2 == pytest.approx(.05)


def test_memory_missingness_and_root_identity_cannot_be_discarded():
    roots = [root_lag_counts([0, 1, -1, 0, 1], [1], alphabet_size=2, root_id=f"r{i}") for i in range(3)]
    result = assess_root_memory(roots)
    assert result["lags"]["1"]["status"] == "UNRESOLVED"
    assert result["lags"]["1"]["missing_anchors"] == [3, 3, 3]
    with pytest.raises(ValueError, match="distinct identity"):
        assess_root_memory([roots[0], roots[0]])


@pytest.mark.numerical(oracle="Uniform finite anchor law: an order-three binary de Bruijn cycle enumerates all eight triples once")
def test_supported_task_equivalence_has_an_attainable_positive_control():
    base = root_lag_counts([0, 0, 0, 1, 0, 1, 1, 1, 0, 0], [1], alphabet_size=2, root_id="base")
    assert np.all(np.asarray(base["lags"]["1"]["joint_counts"]) == 1)
    roots = [{**base, "root_id": str(i)} for i in range(3000)]
    result = assess_root_memory(roots, tolerance=.5)
    assert result["lags"]["1"]["status"] == "EQUIVALENT"
    assert all(row["conditioning_probability_lower"] > 0 for row in result["lags"]["1"]["cells"])
    assert result["duration"]["extent"] == "UNRESOLVED"
    assert result["duration"]["equivalent_lags"] == [1]
    json.dumps(result, allow_nan=False)


@pytest.mark.numerical(oracle="Uniform four-triple law has future equal to reversed older bit: conditional TV is exactly one half while a small-oscillation receiver remains equivalent")
def test_detected_memory_survives_task_equivalence_in_duration_report():
    base = root_lag_counts([0, 0, 1, 1, 0, 0], [1], alphabet_size=2, root_id="base")
    point = memory_diagnostics(base["lags"]["1"]["joint_counts"])
    assert point["maximum_supported_history_tv"] == pytest.approx(.5)
    roots = [{**base, "root_id": str(i)} for i in range(3000)]
    result = assess_root_memory(roots, receiver_oscillation=.01, tolerance=.01)
    lag = result["lags"]["1"]
    assert lag["status"] == "EQUIVALENT"
    assert lag["distributional_dependence_detected"] and lag["task_equivalent"]
    assert result["duration"]["detected_lags"] == [1]
    assert result["duration"]["equivalent_lags"] == [1]
    assert result["duration"]["extent"] == "RIGHT_CENSORED"


@pytest.mark.numerical(oracle="Independent samples of exact normalized probability rows lie inside interval-normalization enclosure")
def test_conditional_interval_encloses_simplex_samples():
    lo, hi = np.array([.1, .2, .3]), np.array([.2, .4, .5])
    lower, upper = conditional_bands(lo, hi)
    for bits in range(8):
        x = np.array([hi[i] if bits & (1 << i) else lo[i] for i in range(3)])
        p = x/x.sum()
        assert np.all(lower <= p+1e-14) and np.all(p <= upper+1e-14)
    assert conditional_bands([0, 0], [.1, .1]) is None
    with pytest.raises(ValueError, match="probability mass"):
        root_mean_bands([[.2, .3]])


@pytest.mark.numerical(oracle="Exhaustive enumeration of all ten simple random samples of size two from a five-unit finite frame")
def test_finite_population_unbiasedness_and_adverse_auxiliary_variance():
    values = np.array([-1., 2., 4., 7., 9.])
    auxiliary = np.array([10., -8., 0., 12., -4.])
    estimates, estimated_variances, direct = [], [], []
    for sample in combinations(range(5), 2):
        result = finite_population_difference(auxiliary, sample, values[list(sample)])
        estimates.append(result["estimate"])
        estimated_variances.append(result["variance_estimate"])
        direct.append(values[list(sample)].mean())
    assert np.mean(estimates) == pytest.approx(4.2)
    assert np.var(estimates) == pytest.approx(30.51)
    assert np.mean(estimated_variances) == pytest.approx(np.var(estimates))
    assert np.var(direct) == pytest.approx(4.71)


def test_finite_frame_missing_returns_and_actual_savings():
    result = finite_population_difference([0, 0, 0], [0, 2], [1, None], value_bounds=(0, 2))
    assert result["status"] == "UNRESOLVED"
    assert result["estimate"] is None
    assert result["missing_sampled_indices"] == [2]
    assert result["missing_return_estimator_bounds"] == pytest.approx([.5, 1.5])
    assert result["actual_native_calls_omitted"] == 1
    revealed = finite_population_difference([0, 0, 0], [0, 2], [1, 2], acquisition_mode="reveal_all")
    assert revealed["actual_native_calls_omitted"] == 0
    with pytest.raises(ValueError, match="positive inclusion"):
        finite_population_difference([0, 0], [0], [1], inclusion_probabilities=[.5, 0])


@pytest.mark.numerical(oracle="Exact enumeration of independent unequal-probability Bernoulli sampling over three finite-frame units")
def test_unequal_probability_residual_correction_and_variance():
    values, auxiliary, probabilities = np.array([1., 4., 9.]), np.array([2., 1., 6.]), np.array([.2, .5, .8])
    mean, second, variance_estimate = 0., 0., 0.
    for mask in range(8):
        selected = [i for i in range(3) if mask & (1 << i)]
        probability = math.prod(probabilities[i] if i in selected else 1-probabilities[i] for i in range(3))
        result = finite_population_difference(auxiliary, selected, values[selected],
            inclusion_probabilities=probabilities, sampling_design="independent_bernoulli")
        mean += probability*result["estimate"]
        second += probability*result["estimate"]**2
        variance_estimate += probability*result["variance_estimate"]
    assert mean == pytest.approx(values.mean())
    assert variance_estimate == pytest.approx(second-mean**2)


def event(root, status, observed, event_time=None, name=None, **other):
    return dict(root_id=root, status=status, observed_until=observed, event_time=event_time, event=name, **other)


@pytest.mark.numerical(oracle="Literal finite population of one target event, one competing event, one full censor and one unresolved path")
def test_events_account_for_competing_failures_and_restricted_time():
    records = [event("a", "event", 2, 2, "target"), event("b", "event", 4, 4, "other"),
               event("c", "administrative_censor", 10), event("d", "failed", 3)]
    result = assess_first_passage(records, horizon=10, time_grid=(0, 2, 5, 10))
    assert result["commitment_bounds"] == [.25, .5]
    assert result["restricted_mean_bounds"] == [4.75, 6.5]
    assert result["unresolved_weight_fraction"] == .25
    assert result["status"] == "UNRESOLVED"
    assert result["independent_roots"] == 4
    assert result["survival"][2]["completion_bounds"] == [.25, .5]
    with pytest.raises(ValueError, match="full horizon"):
        assess_first_passage([event("a", "administrative_censor", 9)], horizon=10)


def test_event_replicas_do_not_manufacture_independent_roots():
    one = assess_first_passage([event("a", "event", 1, 1, "target")], horizon=2)
    many = assess_first_passage([event("a", "event", 1, 1, "target")]*100, horizon=2)
    assert one["root_hoeffding_halfwidth"] == many["root_hoeffding_halfwidth"]
    assert many["independent_roots"] == 1
    assert many["assigned_paths"] == 100
    json.dumps(many, allow_nan=False)


@pytest.mark.parametrize("name", CONTROL_NAMES)
def test_every_mechanism_uses_actual_common_observation_pipeline(name):
    result = control_diagnostics(name, length=128, seed=19, lags=(1, 4))
    assert result["counts"]["record_length"] == 128
    assert result["counts"]["lags"]["4"]["attempted_anchors"] == 120
    assert "disclosed synthetic" in result["scientific_scope"]
    json.dumps(result, allow_nan=False)


def test_approximate_root_bootstrap_label_and_single_root_refusal():
    result = whole_root_bootstrap([[1, 2], [3, 4]], repetitions=100, seed=3)
    assert "approximate" in result["meaning"]
    assert result["independent_roots"] == 2
    with pytest.raises(ValueError, match="two"):
        whole_root_bootstrap([1])
    assert math.isfinite(result["lower"][0])


@pytest.mark.numerical(oracle="Mixture of two exact symmetric binary Markov laws: conditional laws factorize, whereas averaging their products differs from the product of averaged transitions")
def test_heterogeneous_population_memory_is_a_mixture_not_within_kernel_memory():
    from empirical_lawhood.methods.model_free.controls import binary_markov_joint, population_control

    laws = [binary_markov_joint(p, p) for p in (.55, .995)]
    for law in laws:
        assert memory_diagnostics(law)['maximum_supported_history_tv'] < 1e-14
    pooled = memory_diagnostics(np.mean(laws, axis=0))
    # For uniform symmetric marginals, CK row-TV equals Var(p)*2.
    assert pooled['ck']['weighted_tv'] == pytest.approx(2*np.var([.55, .995]), abs=1e-14)
    result = population_control('heterogeneous', length=128, seed=9, roots=4, lags=(1, 4))
    assert result['independent_roots'] == 4
    assert {row['latent_persistence'] for row in result['root_roster']} == {.55, .995}
    assert result['pooled']['assessment']['independent_roots'] == 4
    assert [row['assessment']['independent_roots'] for row in result['conditioned']] == [2, 2]
    assert all(row['counts'] if 'counts' in row else row['root_counts'] for row in result['conditioned'])
    json.dumps(result, allow_nan=False)


@pytest.mark.numerical(oracle="Time-ordered product of known inhomogeneous two-state transition matrices, including a triple spanning the deterministic protocol switch")
def test_nonstationary_control_has_a_time_aware_markov_null():
    from empirical_lawhood.methods.model_free.controls import population_control, protocol_age_joint

    for age in (15, 31, 32, 34, 48):
        lag, length = 2, 64
        first, second = np.eye(2), np.eye(2)
        for tick in range(age-2*lag+1, age-lag+1):
            p = .99 if tick < length//2 else .60
            first = first @ np.array([[p, 1-p], [1-p, p]])
        for tick in range(age-lag+1, age+1):
            p = .99 if tick < length//2 else .60
            second = second @ np.array([[p, 1-p], [1-p, p]])
        independent = .5*np.einsum('ij,jk->ijk', first, second)
        np.testing.assert_allclose(protocol_age_joint(length=length, lag=lag, future_anchor=age), independent, atol=1e-15)
        assert memory_diagnostics(independent)['maximum_supported_history_tv'] < 1e-14
    result = population_control('nonstationary', length=128, seed=11, roots=4, lags=(1, 4))
    assert result['exact_known_laws']['1']['pooled']['ck']['weighted_tv'] > .05
    for conditioned in result['conditioned']:
        assert conditioned['assessment']['record_scope'] == 'protocol_age'
        assert conditioned['assessment']['independent_roots'] == 4
        assert all(row['lags']['1']['attempted_anchors'] == 1 for row in conditioned['root_counts'])
    for row in result['exact_known_laws']['4']['conditioned']:
        assert row['diagnostics']['maximum_supported_history_tv'] < 1e-14
    json.dumps(result, allow_nan=False)


def test_segment_counts_retain_missing_pairs_and_exclude_crossing_lags():
    from empirical_lawhood.methods.model_free.memory import root_segment_counts

    result = root_segment_counts(iter([0, 1, -1, 1, 0, 0]), [0, 3, 6],
        lags=[1, 2], alphabet_size=2, root_id='root', sample_interval=.25)
    first, second = result['segments']
    assert first['occupancy_counts'] == [1, 1] and first['missing_samples'] == 1
    assert first['transitions']['1']['attempted_pairs'] == 2
    assert first['transitions']['1']['missing_pairs'] == 1
    assert first['transitions']['2']['attempted_pairs'] == first['transitions']['2']['missing_pairs'] == 1
    assert second['transitions']['1']['joint_counts'] == [[1, 0], [1, 0]]
    assert second['transitions']['2']['joint_counts'] == [[0, 0], [1, 0]]
    assert second['transitions']['1']['boundary_crossing_pairs_excluded'] == 1
    assert second['transitions']['2']['boundary_crossing_pairs_excluded'] == 2
    assert second['first_sample_time'] == .75 and second['last_sample_time'] == 1.25
    for lag in (1, 2):
        assert sum(row['transitions'][str(lag)]['attempted_pairs'] + row['transitions'][str(lag)]['boundary_crossing_pairs_excluded']
                   for row in result['segments']) == 6-lag
    with pytest.raises(ValueError, match='shorter'):
        root_segment_counts([0], [0, 3, 6], lags=[1], alphabet_size=2, root_id='root')


@pytest.mark.numerical(oracle="Literal paired binary records: constant opposite segment occupancy yields exactly signed unit contrasts; identical segments cancel within every root")
def test_segment_comparisons_preserve_pairing_sign_and_missing_roots():
    from empirical_lawhood.methods.model_free.memory import assess_root_segments, root_segment_counts

    roots = [root_segment_counts([0, 0, 0, 1, 1, 1], [0, 3, 6], lags=[1], alphabet_size=2, root_id=str(i)) for i in range(4)]
    result = assess_root_segments(roots)
    pair = result['comparisons'][0]
    assert pair['occupancy']['mean_difference'] == [-1, 1]
    assert pair['occupancy']['estimated_mean_variance'] == [0, 0]
    assert pair['transitions']['1']['joint_frequency']['mean_difference'] == [-1, 0, 0, 1]
    assert all(row['status'] == 'UNRESOLVED' for row in pair['transitions']['1']['row_conditional'])
    identical = [root_segment_counts([0, 1, 0, 0, 1, 0], [0, 3, 6], lags=[1], alphabet_size=2, root_id=str(i)) for i in range(4)]
    same = assess_root_segments(identical)['comparisons'][0]
    assert same['occupancy']['root_differences'] == [[0, 0]]*4
    assert same['transitions']['1']['row_conditional'][0]['mean_difference'] == [0, 0]
    incomplete = [roots[0], {'root_id': 'missing', 'status': 'UNRESOLVED'}]
    assert assess_root_segments(incomplete)['unresolved_root_ids'] == ['missing']
    bad = root_segment_counts([0, -1, 0, 1, 1, 1], [0, 3, 6], lags=[1], alphabet_size=2, root_id='bad')
    missing = assess_root_segments([roots[0], bad])['comparisons'][0]
    assert missing['occupancy']['status'] == 'UNRESOLVED'
    assert missing['transitions']['1']['joint_frequency']['unresolved_root_ids'] == ['bad']
    json.dumps(result, allow_nan=False)


def test_segment_empty_transition_support_remains_unresolved():
    from empirical_lawhood.methods.model_free.memory import assess_root_segments, root_segment_counts

    result = root_segment_counts([0, 1, 0, 1], [0, 2, 4], lags=[2], alphabet_size=2, root_id='one')
    assert all(row['transitions']['2']['attempted_pairs'] == 0 for row in result['segments'])
    assessment = assess_root_segments([result])
    assert assessment['comparisons'][0]['transitions']['2']['joint_frequency']['status'] == 'UNRESOLVED'
    unresolved = root_segment_counts([0, 1, 0, 1], [0, 2, 4], lags=[1], alphabet_size=4, root_id='one', max_cells=8)
    assert unresolved['status'] == 'UNRESOLVED'


def test_segment_assessment_refuses_changed_counts_and_denominators():
    from copy import deepcopy
    from empirical_lawhood.methods.model_free.memory import assess_root_segments, root_segment_counts

    original = root_segment_counts([0, 1, 0, 1, 0, 1], [0, 3, 6], lags=[1], alphabet_size=2, root_id='r')
    changed = deepcopy(original)
    changed['segments'][0]['occupancy_counts'][0] += 1
    with pytest.raises(ValueError, match='occupancy'):
        assess_root_segments([changed])
    changed = deepcopy(original)
    changed['segments'][1]['transitions']['1']['boundary_crossing_pairs_excluded'] = 0
    with pytest.raises(ValueError, match='transitions'):
        assess_root_segments([changed])
    changed = deepcopy(original)
    changed['segments'][0]['transitions']['1']['conditional_transition_probabilities'][0] = [1., 0.]
    with pytest.raises(ValueError, match='conditional transition'):
        assess_root_segments([changed])


@pytest.mark.numerical(oracle="Explicit six-sample binary segments with identical occupancy but transition counts (0,3,2,0) and (2,1,0,2)")
def test_segment_transition_changes_can_hide_from_mean_and_occupancy():
    from empirical_lawhood.methods.model_free.memory import assess_root_segments, root_segment_counts

    sequence = [0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1]
    roots = [root_segment_counts(sequence, [0, 6, 12], lags=[1], alphabet_size=2, root_id=str(i)) for i in range(3)]
    pair = assess_root_segments(roots)['comparisons'][0]
    assert pair['occupancy']['mean_difference'] == [0, 0]
    assert pair['transitions']['1']['joint_frequency']['mean_difference'] == pytest.approx([.4, -.4, -.4, .4])
    conditional = pair['transitions']['1']['row_conditional']
    assert conditional[0]['mean_difference'] == pytest.approx([2/3, -2/3])
    assert conditional[1]['mean_difference'] == [-1, 1]


@pytest.mark.numerical(oracle="Hoeffding union bound over 18 joint/marginal events, 24 comparisons, seven lags and three looks; conditioning probabilities sum to one")
def test_memory_precision_feasibility_exposes_impossible_eighty_root_equivalence():
    from empirical_lawhood.methods.model_free import memory_bound_feasibility

    result = memory_bound_feasibility(80, alphabet_size=2, history_order=1,
        alpha=.003125, comparison_groups=24, lag_count=7, looks=3)
    assert result['joint_and_marginal_event_count'] == 18
    assert result['per_lag_alpha'] == pytest.approx(6.200396825396825e-6)
    assert result['root_probability_halfwidth'] == pytest.approx(.311993751963894)
    assert result['largest_possible_minimum_conditioning_probability'] == .25
    assert result['necessary_independent_roots_for_positive_conditioning_bounds'] == 125
    assert result['all_conditioning_lower_bounds_can_be_positive'] is False
    boundary = memory_bound_feasibility(125, alphabet_size=2, history_order=1,
        alpha=.003125, comparison_groups=24, lag_count=7, looks=3)
    assert boundary['all_conditioning_lower_bounds_can_be_positive'] is True
    assert boundary['power_established'] is False
    large = memory_bound_feasibility(80, alphabet_size=8, history_order=2,
        alpha=.003125, comparison_groups=24, lag_count=7, looks=3)
    assert large['joint_cells'] == 4096 and large['conditioning_cells'] == 512
    assert large['necessary_independent_roots_for_positive_conditioning_bounds'] == 2770220
    assert large['root_probability_halfwidth'] == pytest.approx(.36344787997504524)
    unsupported = memory_bound_feasibility(80, alphabet_size=8, history_order=100000,
        alpha=.003125, comparison_groups=24, lag_count=7, looks=3)
    assert unsupported['status'] == 'IMPOSSIBLE_UNDER_DECLARED_ALPHABET_BUDGET'
