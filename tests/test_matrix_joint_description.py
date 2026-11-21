"""Focused conformance and independent mathematics for fresh matrix mechanisms.

No released experiment population, historical result replay, CI suite or remote
execution is performed here. Tiny supplied-operand tests exercise the kernels.
"""
from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.joint_description import experiments
from empirical_lawhood.domains.matrix.joint_description.instruments import (
    causal_passive_transfer, describe_prefix,
)
from empirical_lawhood.domains.matrix.joint_description.mechanisms import radial_forecast
from empirical_lawhood.domains.matrix.joint_description.native import (
    MatrixSettings, causal_tangent_forecast, force_direction, native_path, noise_tape, realized_tangent,
)
from empirical_lawhood.domains.matrix.six_matrix_response.model import hermitian_part, ideal_state
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.science.joint_description import TrialRequest


def _state():
    return ideal_state(q=2, alpha_tilde_x=1.0, alpha_tilde_y=2.0, constitution="11")


def test_fresh_family_catalogue_has_complete_declarations():
    declared = experiments.presets()
    assert tuple(p["family_id"] for p in declared) == tuple(f"R{i:02d}" for i in range(3, 13))
    for preset in declared:
        assert set(preset["receiver_policies"]) == set(preset["receivers"])
        assert preset["calibration_units"] > 0 and preset["evaluation_units"] > 0
        assert len({d["id"] for d in preset["descriptions"]}) == len(preset["descriptions"])
        assert any(d["memory_samples"] > 0 for d in preset["descriptions"])


def test_local_description_does_not_read_hidden_sector_but_interface_does():
    settings = MatrixSettings(prefix_steps=2, history_stride=1)
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    direction = force_direction(origin, "x-coordinate")
    before = describe_prefix(history, settings, direction=direction, memory_depth=2)
    positions = origin.positions.copy()
    positions[1, 0] += 0.2 * hermitian_basis(4)[4]
    altered = tuple(replace(state, positions=hermitian_part(positions)) for state in history)
    after = describe_prefix(altered, settings, direction=direction, memory_depth=2)
    np.testing.assert_array_equal(before.local, after.local)
    np.testing.assert_array_equal(before.memory, after.memory)
    assert not np.array_equal(before.interface, after.interface)
    assert not np.array_equal(before.joint, after.joint)


def test_memory_changes_only_when_declared_past_changes():
    settings = MatrixSettings(prefix_steps=2, history_stride=1)
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    direction = force_direction(origin, "x-radial")
    before = describe_prefix(history, settings, direction=direction, memory_depth=2)
    positions = origin.positions.copy()
    positions[0, 0] += 0.2 * hermitian_basis(4)[4]
    changed = (replace(history[0], positions=hermitian_part(positions)), *history[1:])
    after = describe_prefix(changed, settings, direction=direction, memory_depth=2)
    np.testing.assert_array_equal(before.local, after.local)
    np.testing.assert_array_equal(before.interface, after.interface)
    np.testing.assert_array_equal(before.joint, after.joint)
    assert not np.array_equal(before.memory, after.memory)
    with pytest.raises(ValueError, match="HISTORY_UNAVAILABLE"):
        describe_prefix(history, settings, direction=direction, memory_depth=3)


@pytest.mark.numerical(oracle="Closed geometric-series solution of a zero-Hessian B-A-O-A-B tangent: p*=dt(1+c)/(2(1-c)); sum p_j=p*(N-(1-c**N)/(1-c))")
def test_frozen_zero_hessian_tangent_matches_closed_geometric_sum():
    settings = MatrixSettings(alpha_x=0.0, alpha_y=0.0, dt=0.01, prefix_steps=2)
    origin = ideal_state(q=2, alpha_tilde_x=0.0, alpha_tilde_y=0.0, constitution="00")
    direction = force_direction(origin, "x-trace")
    steps, decay = 5, np.exp(-settings.friction * settings.dt)
    stationary = settings.dt * (1 + decay) / (2 * (1 - decay))
    summed_momenta = stationary * (steps - (1 - decay**steps) / (1 - decay))
    expected = settings.dt * (1 + decay) / 2 * (summed_momenta + steps * settings.dt / 2)
    for scalar in (False, True):
        actual = causal_tangent_forecast(origin, settings, direction=direction, steps=steps, scalar_curvature=scalar)
        np.testing.assert_allclose(actual, expected * direction, atol=1e-14, rtol=1e-12)


@pytest.mark.numerical(oracle="SU(2) adjoint Casimir for Y_a=I2 tensor sigma_a/2: three zero traceless commutant modes and twelve eigenvalues2, hence tr(exp(-kT L))=3+12exp(-2kT)")
def test_passive_generator_retains_directional_spectrum():
    origin = ideal_state(q=2, alpha_tilde_x=0.0, alpha_tilde_y=3.0, constitution="01")
    transfer = causal_passive_transfer(origin, observed_sector=1, kappa=0.2, horizon=0.5, radius_only=False)
    expected = np.sort(np.r_[np.ones(3), np.repeat(np.exp(-0.2), 12)])
    np.testing.assert_allclose(np.linalg.eigvalsh(transfer), expected, atol=2e-14, rtol=0)
    radius = causal_passive_transfer(origin, observed_sector=1, kappa=0.2, horizon=0.5, radius_only=True)
    assert not np.allclose(transfer, radius)


@pytest.mark.numerical(oracle="Zero initial position/momentum has zero quartic gradient; first native position update under force F is dt**2*(1+exp(-gamma*dt))*F/4 independent of the final force kick")
def test_radial_first_position_step_has_independent_constant_force_reference():
    settings = MatrixSettings(alpha_x=0.0, alpha_y=0.0, dt=0.01, prefix_steps=2)
    origin = ideal_state(q=2, alpha_tilde_x=0.0, alpha_tilde_y=0.0, constitution="00")
    direction = force_direction(origin, "x-trace")
    path = radial_forecast(origin, settings, steps=1, direction=direction, observed_sector=0, amplitude=0.7)
    expected = 0.7 * settings.dt**2 * (1 + np.exp(-settings.friction * settings.dt)) / 4
    np.testing.assert_allclose(path[-1].positions, expected * direction, atol=1e-16, rtol=0)


@pytest.mark.numerical(oracle="Independent centered finite difference of the complete nonlinear same-innovation native map versus its differentiated force map, retaining both sectors and both kicks")
def test_realized_tangent_matches_two_native_force_branches():
    settings, origin = MatrixSettings(dt=0.001, prefix_steps=2), _state()
    direction = force_direction(origin, "x-coordinate")
    tape = np.zeros((2, 2, 3, 4, 4), dtype="<c16")
    baseline = native_path(origin, settings, tape)
    epsilon = 1e-4
    plus = native_path(origin, settings, tape, direction=direction, amplitude=epsilon)
    minus = native_path(origin, settings, tape, direction=direction, amplitude=-epsilon)
    expected = (plus[-1].positions - minus[-1].positions) / (2 * epsilon)
    derivative = realized_tangent(baseline, settings, direction=direction, pulse_steps=2)
    np.testing.assert_allclose(derivative, expected, atol=2e-12, rtol=2e-5)


@pytest.mark.numerical(oracle="Explicit half-grid coupling ramp and independently split OU noise, followed by two native lower branches from each resolution's own prepared state")
def test_r12_matches_both_clocks_across_the_preparation_handoff(monkeypatch):
    request = TrialRequest("R12", 91, ("root-0",), "evaluation", (-0.1, 0.1), (.02, .04),
        {"dt": .01, "prefix_steps": 2, "history_stride": 1, "memory_depth": 2,
         "handoff_steps": 3, "preparations": ("product",), "direction": "x-coordinate"})
    settings, parameters, _, _ = experiments._configuration(request)
    origin = _state()
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: tuple(replace(origin, step_index=i) for i in range(3)))
    result = experiments.produce(request)
    direction = force_direction(origin, "x-coordinate")
    half_settings = replace(settings, dt=settings.dt / 2)
    decay = np.exp(-settings.friction * half_settings.dt)

    def tapes(purpose, bridge_purpose, count):
        coarse = noise_tape(experiments._rng(request, "root-0", purpose), count)
        bridge = noise_tape(experiments._rng(request, "root-0", bridge_purpose), count)
        half = np.empty((2 * count, *coarse.shape[1:]), dtype=coarse.dtype)
        scale = np.hypot(1, decay)
        half[::2] = (decay * coarse + bridge) / scale
        half[1::2] = (coarse - decay * bridge) / scale
        np.testing.assert_allclose((decay * half[::2] + half[1::2]) / scale, coarse, rtol=0, atol=2e-15)
        return coarse, half

    upper, lower = tapes("parent-preparation", "parent-refinement", 3), tapes("lower-response", "lower-refinement", 4)
    assert sum(row.work_units for row in result.rows) == 2 * settings.prefix_steps + 2 * 3 * (3 + 2 * 4)
    for action in request.actions:
        responses, handoffs = [], []
        for resolution, step_settings in enumerate((settings, half_settings)):
            handoff = native_path(origin, step_settings, upper[resolution], coupling_delta=(action, 0))[-1]
            handoffs.append(handoff)
            assert handoff.alpha_tilde_x == origin.alpha_tilde_x + action
            baseline = native_path(handoff, step_settings, lower[resolution])
            forced = native_path(handoff, step_settings, lower[resolution], direction=direction,
                                 amplitude=parameters["downstream_amplitude"])
            responses.append({h: np.vdot(direction, forced[round(h / step_settings.dt)].positions
                - baseline[round(h / step_settings.dt)].positions).real for h in request.horizons})
        separation = np.linalg.norm(handoffs[1].positions - handoffs[0].positions)
        assert separation > 1e-8
        for row in result.rows:
            if row.action != action:
                continue
            diagnostic = dict(row.diagnostics)
            coarse, fine = (values[row.horizon] for values in responses)
            assert row.status == "supported"
            assert diagnostic["paired-handoff-position-discrepancy"] == pytest.approx(separation)
            assert diagnostic["primary-response"] == pytest.approx(coarse, abs=1e-14)
            assert diagnostic["paired-refinement-discrepancy"] == pytest.approx(abs(fine - coarse), abs=1e-14)
            assert diagnostic["primary-service"] == float(coarse >= parameters["service_threshold"])
            assert diagnostic["refined-service"] == float(fine >= parameters["service_threshold"])
            expected = fine if row.receiver_id == "signed-response" else diagnostic["refined-service"]
            assert row.outcome == pytest.approx(expected, abs=1e-14)


def test_r12_refinement_failure_retains_issued_features_and_complete_population(monkeypatch):
    request = TrialRequest("R12", 91, ("root-0",), "evaluation", (0.1,), (.004,),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2, "handoff_steps": 2, "preparations": ("product",)})
    issued = experiments.prepare_predictors(request)

    def fail_preparation(*args, **kwargs):
        assert "coupling_delta" in kwargs
        raise FloatingPointError("refined preparation exceeded admissible radius")

    monkeypatch.setattr(experiments, "paired_refinement", fail_preparation)
    outcome = experiments.produce(request)
    assert len(outcome.rows) == len(issued.rows) == 2
    for actual, forecast in zip(outcome.rows, issued.rows, strict=True):
        assert actual.features == forecast.features
        assert actual.outcome is None and actual.status == "failed"
        assert "refined preparation" in actual.reason


def test_two_past_samples_supply_exact_quadratic_derivative():
    settings = MatrixSettings(dt=0.1, prefix_steps=2, history_stride=1)
    origin = _state()
    axis = force_direction(origin, "x-trace")
    history = tuple(replace(origin, positions=hermitian_part(origin.positions + (3 * (i * .1) + 2 * (i * .1)**2) * axis), step_index=i) for i in range(3))
    memory = experiments._memory_origin(history, settings, 2)
    np.testing.assert_allclose(memory.momenta, (3 + 4 * .2) * axis, atol=1e-12, rtol=0)


def test_family_randomness_separates_splits_and_keeps_purpose_stable():
    request = TrialRequest("R03", 10, ("root-0",), "calibration", (0.0,), (0.004,), {})
    first = experiments._rng(request, "root-0", "prefix").normal(size=4)
    repeated = experiments._rng(request, "root-0", "prefix").normal(size=4)
    heldout = experiments._rng(replace(request, split="evaluation"), "root-0", "prefix").normal(size=4)
    np.testing.assert_array_equal(first, repeated)
    assert not np.array_equal(first, heldout)


def test_native_failure_preserves_every_declared_cell(monkeypatch):
    def unavailable(*args, **kwargs):
        raise FloatingPointError("SUPPLIED_TEST_NONFINITE")
    monkeypatch.setattr(experiments, "acquire_prefix", unavailable)
    request = TrialRequest("R03", 10, ("root-0", "root-1"), "calibration", (-.1, .1), (.004, .008), {})
    batch = experiments.produce(request)
    receivers = next(p for p in experiments.presets() if p["family_id"] == "R03")["receivers"]
    batch.validate_census(request, receivers)
    assert len(batch.rows) == 56
    assert all(r.status == "failed" and r.outcome is None and "SUPPLIED_TEST_NONFINITE" in r.reason for r in batch.rows)


def test_one_failed_predictor_keeps_other_candidate_available():
    def failure():
        raise FloatingPointError("LOSY_MODEL_UNRESOLVED")
    values, reason = experiments._available_forecasts({"local": failure, "joint": lambda: 7.0})
    assert values == {"joint": 7.0}
    assert reason == "PREDICTOR_UNAVAILABLE:local:FloatingPointError"


def test_cpu_instrument_refuses_unsupported_device_and_archive():
    request = TrialRequest("R03", 10, ("root-0",), "calibration", (0.0,), (.004,), {}, device="gpu")
    with pytest.raises(ValueError, match="CPU"):
        experiments.produce(request)
    with pytest.raises(ValueError, match="q=2"):
        MatrixSettings(q=3)


@pytest.mark.parametrize("family", tuple(f"R{i:02d}" for i in range(3, 13)))
def test_predictor_phase_never_acquires_a_realized_response(monkeypatch, family):
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: history)

    def forbidden(*args, **kwargs):
        raise AssertionError("Actual future acquisition/evaluation entered during causal predictor preparation")

    for name in ("native_path", "noise_tape", "directional_passive_transfer", "realized_tangent", "paired_refinement"):
        monkeypatch.setattr(experiments, name, forbidden)
    request = TrialRequest(family, 10, ("root-0",), "evaluation", (0.0,), (.002,),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2, "handoff_steps": 1,
         "preparations": ("product",), "direction": "x-trace"})
    batch = experiments.prepare_predictors(request)
    receivers = next(p for p in experiments.presets() if p["family_id"] == family)["receivers"]
    batch.validate_census(request, receivers)
    assert all(row.outcome is None and row.diagnostics == () for row in batch.rows)
    assert all(row.reason == "not-yet-acquired" for row in batch.rows)
    assert all(row.features for row in batch.rows)


def test_outcome_failure_retains_previously_issued_features(monkeypatch):
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: history)
    request = TrialRequest("R07", 10, ("root-0",), "evaluation", (0.1,), (.002,),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2, "direction": "x-trace"})
    issued = experiments.prepare_predictors(request)

    def failed_future(*args, **kwargs):
        raise FloatingPointError("SUPPLIED_FUTURE_FAILURE")

    monkeypatch.setattr(experiments, "native_path", failed_future)
    observed = experiments.produce(request)
    assert tuple(r.features for r in observed.rows) == tuple(r.features for r in issued.rows)
    assert all(r.status == "failed" and r.outcome is None for r in observed.rows)


def test_prepared_and_later_acquired_features_match_with_supplied_native_fixture(monkeypatch):
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: history)
    request = TrialRequest("R07", 10, ("root-0",), "evaluation", (0.1,), (.002,),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2, "direction": "x-trace"})
    issued = experiments.prepare_predictors(request)

    def supplied_path(initial, settings, innovations, **kwargs):
        return tuple(replace(initial, step_index=initial.step_index + i) for i in range(len(innovations) + 1))

    monkeypatch.setattr(experiments, "native_path", supplied_path)
    observed = experiments.produce(request)
    assert tuple(r.features for r in observed.rows) == tuple(r.features for r in issued.rows)
    assert all(r.status == "supported" for r in observed.rows)


@pytest.mark.numerical(oracle="Independent centered derivative of the literal native action along Z=rF, at radii/couplings distinct from coefficient extraction nodes, equals the reduced cubic radial force")
def test_radial_polynomial_matches_independent_literal_action_derivative():
    from empirical_lawhood.domains.matrix.joint_description.mechanisms import radial_force_polynomial
    from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters, reference_action_terms

    settings, origin = MatrixSettings(prefix_steps=2), _state()
    axis = force_direction(origin, "x-radial")[0]
    # Add a noncommuting frozen other-sector interface to make its force nonzero.
    positions = origin.positions.copy()
    positions[1, 0] += .17 * hermitian_basis(4)[4]
    origin = replace(origin, positions=hermitian_part(positions))
    for retained in (False, True):
        polynomial = radial_force_polynomial(origin, settings, axis=axis, observed_sector=0, retain_interface=retained)
        for radius, coupling in ((.37, .29), (1.41, 1.73), (-.31, 2.17)):
            potential_parameters = SixMatrixParameters(2, settings.mass, settings.mass, settings.cross_coupling, coupling, origin.alpha_tilde_y)
            def action(value):
                position = np.zeros_like(origin.positions)
                position[0] = value * axis
                if retained:
                    position[1] = origin.positions[1]
                return reference_action_terms(position, potential_parameters).total
            epsilon = 1e-5
            reference = (action(radius + epsilon) - action(radius - epsilon)) / (2 * epsilon)
            assert polynomial.evaluate(radius, coupling) == pytest.approx(reference, rel=2e-8, abs=2e-8)


def test_shared_prefix_description_is_computed_once_per_root(monkeypatch):
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: history)
    original, calls = experiments.describe_prefix, []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(experiments, "describe_prefix", counted)
    request = TrialRequest("R03", 10, ("root-0",), "evaluation", (-.1, 0.0, .1), (.002, .004),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2})
    batch = experiments.prepare_predictors(request)
    assert len(batch.rows) == 42
    assert len(calls) == 1
    assert sum(row.work_units for row in batch.rows) == 2
    assert sum(row.work_units > 0 for row in batch.rows) == 1


def test_preparation_assignment_is_invariant_under_single_root_worker_partitioning(monkeypatch):
    """The real runtime submits one root per subwork; batch position is not science."""
    origin = _state()
    history = tuple(replace(origin, step_index=i) for i in range(3))
    monkeypatch.setattr(experiments, "acquire_prefix", lambda *args: history)
    request = TrialRequest("R03", 10, tuple(f"root-{i:02d}" for i in range(16)), "evaluation", (0.0,), (.002,),
        {"prefix_steps": 2, "history_stride": 1, "memory_depth": 2, "receivers": ("x-gap",)})
    together = experiments.prepare_predictors(request)
    separate = tuple(row for unit in request.unit_ids
        for row in experiments.prepare_predictors(replace(request, unit_ids=(unit,))).rows)
    assert tuple(row.features for row in together.rows) == tuple(row.features for row in separate)
    assert {dict(row.features)["context.preparation"] for row in separate} == {0.0, 1.0, 2.0, 3.0}
