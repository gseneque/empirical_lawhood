"""Independent mathematical controls for fresh R01/R02 producers."""

import numpy as np
import pytest

from empirical_lawhood.domains.circuits.joint_description import (
    action_response_panel,
    affine_flow,
    ladder_circuit,
    mean_receiver,
    parallel_branches,
    reconstruct_information,
)


@pytest.mark.numerical(oracle="independent scalar integrating-factor RC solution")
def test_constant_input_flow_matches_separate_scalar_branches():
    circuit = parallel_branches((1.0, 4.0))
    state = np.asarray([0.2, 0.9])
    transition, forced = affine_flow(circuit, 2.5)
    obtained = transition @ state + forced[:, 0] * 0.6
    expected = 0.6 + (state - 0.6) * np.exp(-2.5 / np.asarray([1.0, 4.0]))
    np.testing.assert_allclose(obtained, expected, rtol=1e-13, atol=1e-14)


@pytest.mark.numerical(oracle="analytic two-mode observability determinant and exact earliest preparation")
def test_past_mean_observations_recover_hidden_contrast_without_future_data():
    circuit = parallel_branches((1.0, 4.0))
    earliest = np.asarray([0.9, 0.2])
    memory = reconstruct_information(
        circuit, earliest, description="memory", partitions=1,
        history_depth=2, history_lag_s=0.2,
    )
    expected = earliest * np.exp(-0.2 / np.asarray([1.0, 4.0]))
    assert memory.observable_rank == 2
    assert memory.memory_scalars == 1
    np.testing.assert_allclose(memory.state_estimate_v, expected, rtol=1e-12, atol=1e-13)


@pytest.mark.numerical(oracle="same mean implies same reduced prediction, while direct exponentials separate unequal time constants")
def test_mean_only_identical_input_collision_and_interface_repair():
    circuit = parallel_branches((1.0, 4.0))
    states = (np.asarray([0.8, 0.2]), np.asarray([0.2, 0.8]))
    partition = [
        reconstruct_information(circuit, state, description="partitioned", partitions=1,
                                history_depth=1, history_lag_s=0.1)
        for state in states
    ]
    np.testing.assert_allclose(partition[0].state_estimate_v, partition[1].state_estimate_v)
    repaired = [
        reconstruct_information(circuit, state, description="interface", partitions=1,
                                history_depth=1, history_lag_s=0.1)
        for state in states
    ]
    for actual, expected in zip(repaired, states, strict=True):
        np.testing.assert_allclose(actual.state_estimate_v, expected, atol=2e-16)
        assert actual.interface_scalars == 1
    t = 4 * np.log(4) / 3
    exact_gap = 0.3 * abs(np.exp(-t) - np.exp(-t / 4))
    response = [action_response_panel(circuit, state, np.asarray([[0.4]]), (t,),
                                     mean_receiver(circuit))[0, 0, 0] for state in states]
    assert abs(response[0] - response[1]) == pytest.approx(exact_gap, rel=2e-14)


@pytest.mark.numerical(oracle="Kirchhoff charge balance C*dV/dt plus boundary currents")
def test_extracted_ladder_operator_preserves_charge_balance():
    circuit = ladder_circuit((1.0, 2.0, 3.0, 4.0), (0.5, 1.5, 2.0),
                             source_resistance_ohm=2.0, termination_resistance_ohm=3.0)
    voltages = np.asarray([0.1, 0.7, 0.4, 0.9])
    boundary = np.asarray([1.0, 0.2])
    derivative = circuit.state_matrix_per_s @ voltages + circuit.input_matrix_per_s @ boundary
    independent_current = (boundary[0] - voltages[0]) / 2 + (boundary[1] - voltages[-1]) / 3
    assert circuit.capacitances_f @ derivative == pytest.approx(independent_current, abs=1e-14)


def test_information_channel_rejects_wrong_noise_census():
    circuit = parallel_branches((1.0, 4.0))
    with pytest.raises(ValueError, match="noise"):
        reconstruct_information(circuit, np.asarray([0.2, 0.4]), description="memory",
                                partitions=1, history_depth=2, history_lag_s=0.1,
                                observation_noise_v=np.zeros(3))


@pytest.mark.parametrize("family", ["R01", "R02"])
def test_tiny_producer_preserves_complete_pairs_and_all_description_features(family):
    from dataclasses import replace
    from empirical_lawhood.domains.circuits.joint_description import presets, produce
    from empirical_lawhood.science.joint_description import TrialRequest

    preset = next(p for p in presets() if p["family_id"] == family)
    request = TrialRequest(family, 1007, ("fixture-root-a", "fixture-root-b"), "evaluation",
                           (0.0, 1.0), (0.25, 0.5), preset["parameters"])
    batch = produce(request)
    batch.validate_census(request, preset["receivers"])
    expected_features = set().union(*(d["features"] for d in preset["descriptions"]))
    assert all(expected_features <= dict(row.features).keys() for row in batch.rows)
    assert all(row.status == "supported" for row in batch.rows)
    assert len(batch.rows) == 16
    subset = (preset["receivers"][0],)
    restricted = replace(request, parameters={**request.parameters, "receivers": subset})
    restricted_batch = produce(restricted)
    restricted_batch.validate_census(restricted, subset)
    assert len(restricted_batch.rows) == 8


def test_fractional_history_depth_is_rejected_instead_of_silently_reauthored():
    from empirical_lawhood.domains.circuits.joint_description import produce
    from empirical_lawhood.science.joint_description import TrialRequest

    request = TrialRequest("R01", 7, ("root-one",), "evaluation", (0.0,), (1.0,),
                           {"history_depth": 2.5})
    with pytest.raises(ValueError, match="integer"):
        produce(request)


def test_predictor_preparation_does_not_evaluate_truth_or_analytical_verdict(monkeypatch):
    from empirical_lawhood.domains.circuits import joint_description
    from empirical_lawhood.domains.circuits.rc_information import analytic
    from empirical_lawhood.science.joint_description import TrialRequest

    request = TrialRequest("R01", 7, ("root-one",), "evaluation", (0.0,), (1.0,), {})
    def forbidden(*_args, **_kwargs):
        raise AssertionError("evaluator-only analytical bound entered predictor stage")
    monkeypatch.setattr(analytic, "evaluate_rc_information", forbidden)
    prepared = joint_description.prepare_predictors(request)
    assert all(row.outcome is None and row.reason == "not-yet-acquired" and not row.diagnostics
               for row in prepared.rows)
    frozen = {row.key: row.features for row in prepared.rows}
    monkeypatch.undo()
    acquired = joint_description.produce(request)
    assert {row.key: row.features for row in acquired.rows} == frozen
