# SPDX-License-Identifier: MPL-2.0
"""Independent finite-frame enumeration and paired finite-event oracles."""
from itertools import combinations
import json

import numpy as np
import pytest

from empirical_lawhood.methods.model_free.events import assess_first_passage, assess_paired_first_passage
from empirical_lawhood.methods.model_free.finite_population import compare_finite_population_estimators


@pytest.mark.numerical(oracle="Enumerate all ten size-two samples of a five-member frame, including joint estimator moments")
def test_direct_and_auxiliary_comparison_matches_exhaustive_design_moments():
    native = np.array([-1., 2., 4., 7., 9.])
    auxiliary = np.array([10., -8., 0., 12., -4.])
    estimates, covariances, differences = [], [], []
    for selected in combinations(range(5), 2):
        result = compare_finite_population_estimators(auxiliary, selected, native[list(selected)],
            full_native_values=native, acquisition_mode="reveal_all")
        estimates.append([result["residual_correction"]["estimate"], result["direct_sampling"]["estimate"]])
        covariances.append(result["paired_estimator_covariance_estimate"])
        differences.append(result["paired_estimator_difference_variance_estimate"])
        benchmark = result["full_frame_benchmark"]
        assert benchmark["actual_native_calls_omitted"] == 0
        assert benchmark["counterfactual_calls_omitted"] == 3
        assert benchmark["corrected_design_variance"] == pytest.approx(30.51)
        assert benchmark["direct_design_variance"] == pytest.approx(4.71)
    np.testing.assert_allclose(np.mean(estimates, axis=0), [4.2, 4.2], atol=1e-14)
    joint = np.cov(np.array(estimates).T, ddof=0)
    assert np.mean(covariances) == pytest.approx(joint[0, 1])
    assert np.mean(differences) == pytest.approx(np.var(np.diff(estimates, axis=1)))
    assert benchmark["paired_design_covariance"] == pytest.approx(joint[0, 1])
    assert benchmark["variance_ratio_corrected_over_direct"] > 1


@pytest.mark.numerical(oracle="An arbitrary constant cancels algebraically; a complete census has zero randomization variance")
def test_constant_auxiliary_is_direct_srs_and_census_is_exact():
    values = [1., 3., 8.]
    for selected in combinations(range(3), 2):
        result = compare_finite_population_estimators([17.] * 3, selected, [values[i] for i in selected])
        assert result["residual_correction"]["estimate"] == pytest.approx(result["direct_sampling"]["estimate"])
        assert result["paired_estimator_difference_variance_estimate"] == 0
    census = compare_finite_population_estimators([9., -2., 3.], [0, 1, 2], values,
        full_native_values=values, acquisition_mode="reveal_all")
    assert census["residual_correction"]["estimate"] == pytest.approx(4.)
    assert census["direct_sampling"]["estimate"] == pytest.approx(4.)
    assert census["full_frame_benchmark"]["corrected_design_variance"] == 0
    assert census["full_frame_benchmark"]["paired_design_covariance"] == 0


def test_comparison_retains_sampled_failures_and_refuses_changed_revealed_values():
    result = compare_finite_population_estimators([1., 2., 3.], [0, 2], [1., None],
        full_native_values=[1., 2., None], acquisition_mode="reveal_all", value_bounds=(0, 4))
    assert result["status"] == "UNRESOLVED"
    assert result["direct_sampling"]["missing_sampled_indices"] == [2]
    assert result["residual_correction"]["estimate"] is None
    assert result["full_frame_benchmark"]["missing_frame_indices"] == [2]
    with pytest.raises(ValueError, match="disagree"):
        compare_finite_population_estimators([0., 0.], [0], [1.], full_native_values=[2., 3.], acquisition_mode="reveal_all")
    with pytest.raises(ValueError, match="reveal-all"):
        compare_finite_population_estimators([0., 0.], [0], [1.], full_native_values=[1., 2.])
    with pytest.raises(ValueError, match="alpha"):
        compare_finite_population_estimators([0., 0.], [0], [1.], alpha=1.5)
    json.dumps(result, allow_nan=False)


def _event(root, replica, history, time, name, *, weight=.5):
    return dict(root_id=root, replica=replica, entry_history=history, weight=weight,
        status="administrative_censor" if name is None else "event", observed_until=4.,
        event_time=time, event=name)


def _paired_example():
    assignments = [dict(root_id=root, replica=replica, weight=.5) for root in ("a", "b") for replica in range(2)]
    records = [_event("a", 0, "base", 1., "target"), _event("a", 1, "base", None, None),
        _event("a", 0, "prepared", 2., "target"), _event("a", 1, "prepared", 2., "target")]
    records += [_event("b", 0, history, 1., "competing") for history in ("base", "prepared")]
    records += [_event("b", 1, history, 3., "target") for history in ("base", "prepared")]
    return assignments, records


@pytest.mark.numerical(oracle="Literal two-root paired paths: probability gains (1/2,0), restricted-time differences (-1/2,0)")
def test_paired_events_preserve_sign_covariance_competing_risks_and_replicas():
    assignments, records = _paired_example()
    result = assess_paired_first_passage(records, assignments=assignments, histories=("base", "prepared"),
        horizon=4., time_grid=(0., 2., 4.))
    assert result["independent_roots"] == 2
    assert result["assigned_paired_paths"] == 4
    assert result["commitment"]["completion_bounds"] == pytest.approx([.25, .25])
    assert result["restricted_mean"]["completion_bounds"] == pytest.approx([-.25, -.25])
    assert result["survival"][1]["completion_bounds"] == pytest.approx([-.25, -.25])
    assert result["commitment"]["sample_paired_mean_variance"] == pytest.approx(.0625)
    competing = assess_paired_first_passage(records, assignments=assignments, histories=("base", "prepared"),
        horizon=4., target_event="competing")
    assert competing["commitment"]["completion_bounds"] == [0., 0.]
    json.dumps(result, allow_nan=False)


@pytest.mark.numerical(oracle="A wholly missing partner retains probability difference [-1/2,1/2] for its assigned root")
def test_missing_and_nonentered_history_mass_is_not_conditioned_away():
    assignments, records = _paired_example()
    records = [row for row in records if not (row["root_id"] == "a" and row["entry_history"] == "prepared")]
    result = assess_paired_first_passage(records, assignments=assignments, histories=("base", "prepared"), horizon=4.)
    assert result["status"] == "UNRESOLVED"
    assert result["independent_roots"] == 2
    assert len(result["missing_path_histories"]) == 2
    assert result["commitment"]["completion_bounds"] == pytest.approx([-.25, .25])
    assert result["commitment"]["sample_paired_mean_variance"] is None
    assert len(result["root_pairs"]) == 2


@pytest.mark.numerical(oracle="Identical common-future path pairs cancel exactly before root covariance is computed")
def test_identical_coupled_histories_have_zero_paired_variation():
    assignments, records = _paired_example()
    first = [row for row in records if row["entry_history"] == "base"]
    records = first + [{**row, "entry_history": "prepared"} for row in first]
    result = assess_paired_first_passage(records, assignments=assignments, histories=("base", "prepared"), horizon=4.)
    assert result["commitment"]["completion_bounds"] == [0., 0.]
    assert result["restricted_mean"]["completion_bounds"] == [0., 0.]
    assert result["restricted_mean"]["sample_paired_mean_variance"] == 0
    assert result["restricted_mean"]["sample_root_cross_covariance"] == pytest.approx(.125)


@pytest.mark.numerical(oracle="Frozen root weights 1:3 applied to literal paired probability differences 1/2 and zero")
def test_paired_events_preserve_unequal_assigned_root_weights():
    assignments, records = _paired_example()
    for row in [*assignments, *records]:
        row["weight"] = .25 if row["root_id"] == "a" else .75
    result = assess_paired_first_passage(records, assignments=assignments, histories=("base", "prepared"), horizon=4.)
    assert result["commitment"]["completion_bounds"] == pytest.approx([.125, .125])
    assert result["restricted_mean"]["completion_bounds"] == pytest.approx([-.125, -.125])
    assert result["commitment"]["sample_paired_mean_variance"] is None


def test_paired_paths_refuse_changed_weights_duplicates_and_unknown_roots():
    assignments, records = _paired_example()
    for broken in ([*records, records[0]], [{**records[0], "weight": 1.}, *records[1:]],
                   [{**records[0], "root_id": "other"}, *records[1:]]):
        with pytest.raises(ValueError):
            assess_paired_first_passage(broken, assignments=assignments, histories=("base", "prepared"), horizon=4.)


@pytest.mark.numerical(oracle="No event through an observed failure prefix gives survival one at the inclusive prefix endpoint")
def test_failed_path_prefix_endpoint_is_observed_not_missing():
    result = assess_first_passage([dict(root_id="a", status="failed", observed_until=2., event_time=None, event=None)],
        horizon=4., time_grid=(0., 2., 3.))
    assert result["survival"][1]["completion_bounds"] == [1., 1.]
    assert result["survival"][2]["completion_bounds"] == [0., 1.]
