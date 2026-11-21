# SPDX-License-Identifier: MPL-2.0
"""Analytical mechanics controls, not enzyme trajectories or rate evidence."""

from decimal import Decimal as D, localcontext

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings, propagate_reference_trajectory
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import ReferenceTrajectoryCriteria, assess_reference_trajectory_frames
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import VAL1_MEASURE, sample_tagged_flux_host
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


class AnalyticalOperator:
    def __init__(self, potential, *, failure=None, fail_call=2):
        self.potential = potential
        self.failure, self.fail_call = failure, fail_call
        self.calls = []

    def evaluate(self, coordinates):
        self.calls.append(coordinates.copy())
        if self.failure == 'native' and len(self.calls) == self.fail_call:
            raise RuntimeError('exposed-force-failure')
        energy, gradient = self.potential(coordinates / 10)
        bohr = .52917721092
        hartree = COULOMB_KJ_NM_PER_MOL_E2 / (bohr / 10)
        result = dict(energy_hartree=energy / hartree,
            gradient_hartree_per_bohr=np.asarray(gradient) * bohr / (10 * hartree),
            bohr_angstrom=bohr, hartree_kj_mol=hartree, gradient_unit=GRADIENT_UNIT)
        if len(self.calls) == self.fail_call:
            if self.failure == 'unit':
                result['gradient_unit'] = 'WRONG_FORCE_UNIT'
            elif self.failure == 'short':
                result['gradient_hartree_per_bohr'] = result['gradient_hartree_per_bohr'][:-1]
            elif self.failure == 'nonfinite':
                result['energy_hartree'] = float('nan')
            elif self.failure == 'mutated-input':
                coordinates[0, 0] += 1
        return result


def run(operator, xyz, velocities, masses, *, steps=40, dt=D('5e-16'), capture=None):
    frames, events = [], []
    settings = ReferenceDynamicsSettings('settings.exposed.reference-dynamics', dt, steps)
    result = propagate_reference_trajectory(operator=operator, initial_angstrom=xyz,
        initial_velocity_nm_per_ps=velocities, physical_masses_dalton=masses,
        settings=settings, observe=events.append, capture=frames.append if capture is None else capture)
    return (*result, frames, events)


def harmonic(x):
    return 20000 * float(np.sum(x ** 2)), 40000 * x


def test_free_host_chain_matches_seeded_natural_mass_drift_through_capture_mutation():
    positions = np.array([[.3, -.2, .4], [.8, .5, -.6]])
    masses = np.array([1., 16.])
    settings = ReferenceDynamicsSettings('settings.control.free-host', D('5e-16'), 3)
    operator = AnalyticalOperator(lambda x: (0., np.zeros_like(x)))
    retained = []

    def capture(record, coordinates):
        retained.append((record, coordinates.copy()))
        coordinates.fill(np.nan)

    summary = sample_tagged_flux_host(initial_angstrom=positions, masses_dalton=masses,
        evaluate=operator.evaluate, dynamics=settings, burn_in=2, draws=5, relaxation_evaluations=0,
        random_seed=21, capture=capture)
    expected = positions.copy()
    reference_rng = np.random.Generator(np.random.PCG64(21))
    kbt = .00831446261815324 * 298.15
    for index, (record, observed) in enumerate(retained):
        velocity = reference_rng.normal(size=positions.shape) * np.sqrt(kbt / masses[:, None])
        expected += velocity * .0005 * 10 * 3
        np.testing.assert_allclose(observed, expected, rtol=0, atol=2e-15)
        assert record['uniform_draw'] == reference_rng.uniform()
        assert record['accepted'] and record['delta_h_kj_mol'] == 0.
        assert record['index'] == index and record['burn_in'] == (index < 2)
        assert record['completed_force_evaluations'] == 1 + 3 * (index + 1)
    assert len(retained) == summary['accepted_moves'] == 7
    assert summary['initialization_force_evaluations'] == 1
    assert len(operator.calls) == summary['completed_force_evaluations'] == 22
    assert summary['random_seed'] == 21 and summary['random_generator'] == 'PCG64'
    assert summary['dynamics'] == settings.identity.to_document()
    assert summary['temperature_kelvin'] == str(VAL1_MEASURE.temperature_kelvin)


def test_harmonic_host_rejections_repeat_the_previous_state_with_no_extra_force():
    stiffness = 9e6
    operator = AnalyticalOperator(lambda x: (.5 * stiffness * np.sum(x*x), stiffness*x))
    current = np.zeros((1, 3))
    retained = []
    summary = sample_tagged_flux_host(initial_angstrom=current, masses_dalton=(1.,),
        evaluate=operator.evaluate, dynamics=ReferenceDynamicsSettings('settings.control.harmonic-host', D('5e-16'), 1),
        burn_in=3, draws=20, relaxation_evaluations=0, random_seed=15,
        capture=lambda row, coordinates: retained.append((row, coordinates)))
    for (record, observed), proposed in zip(retained, operator.calls[1:], strict=True):
        if record['accepted']:
            current = proposed
        np.testing.assert_array_equal(observed, current)
        assert record['proposed_energy_hartree'] == operator.potential(proposed / 10)[0] / (
            COULOMB_KJ_NM_PER_MOL_E2 / (.52917721092 / 10))
        assert record['energy_hartree'] == operator.potential(current / 10)[0] / (
            COULOMB_KJ_NM_PER_MOL_E2 / (.52917721092 / 10))
    assert 0 < summary['accepted_moves'] < 23
    assert summary['accepted_moves'] + summary['rejected_moves'] == 23
    assert len(operator.calls) == summary['completed_force_evaluations'] == 24


@pytest.mark.parametrize('limit', (1, 2, 6))
def test_bounded_host_relaxation_keeps_the_lowest_energy_actually_evaluated(limit):
    operator = AnalyticalOperator(harmonic)
    retained = []
    summary = sample_tagged_flux_host(initial_angstrom=[[.13, -.22, .45]], masses_dalton=[2.],
        evaluate=operator.evaluate, dynamics=ReferenceDynamicsSettings('settings.control.relax-host', D('5e-16'), 3),
        burn_in=0, draws=0, relaxation_evaluations=limit, random_seed=10,
        capture=lambda row, coordinates: retained.append((row, coordinates)))
    assert 1 <= len(operator.calls) <= limit
    assert summary['relaxation_evaluation_limit'] == limit
    assert summary['initialization_force_evaluations'] == summary['completed_force_evaluations'] == len(operator.calls)
    assert len(retained) == 1
    record, coordinates = retained[0]
    assert record['stage'] == 'initial-relaxation' and record['evaluations'] == len(operator.calls)
    best = min(operator.calls, key=lambda x: harmonic(x / 10)[0])
    np.testing.assert_array_equal(coordinates, best)


@pytest.mark.parametrize('failure', ('native', 'unit', 'short', 'nonfinite', 'mutated-input'))
def test_host_failed_force_preserves_the_completed_prefix_without_a_rejection(failure):
    operator = AnalyticalOperator(harmonic, failure=failure, fail_call=4)
    captured = []
    with pytest.raises((RuntimeError, ValueError)):
        sample_tagged_flux_host(initial_angstrom=[[.1, 0, 0]], masses_dalton=[4.], evaluate=operator.evaluate,
            dynamics=ReferenceDynamicsSettings('settings.control.failed-host', D('5e-16'), 1),
            burn_in=1, draws=6, relaxation_evaluations=0, random_seed=7,
            capture=lambda row, coordinates: captured.append(row))
    assert [row['index'] for row in captured] == [0, 1]
    assert len(operator.calls) == 4


def test_host_refuses_invalid_mass_before_entry_and_stops_at_failed_capture():
    operator = AnalyticalOperator(harmonic)
    def capture(row, coordinates):
        raise OSError("host capture failed")
    selection = dict(initial_angstrom=[[.1, 0, 0]], evaluate=operator.evaluate,
        dynamics=ReferenceDynamicsSettings('settings.control.invalid-host', D('5e-16'), 1),
        burn_in=0, draws=2, relaxation_evaluations=0, random_seed=0, capture=capture)
    with pytest.raises(ValueError, match='positive mass'):
        sample_tagged_flux_host(**selection, masses_dalton=[-1.])
    assert len(operator.calls) == 0
    with pytest.raises(OSError, match='host capture failed'):
        sample_tagged_flux_host(**selection, masses_dalton=[1.])
    assert len(operator.calls) == 2


def test_constant_force_matches_exact_newtonian_motion_and_natural_mass_response():
    xyz = np.asarray(((.31, -.2, .1), (1.2, .3, -.4)))
    velocity = np.asarray(((.21, -.11, .04), (-.09, .18, .31)))
    masses = np.asarray((1.008, 15.999))
    force = np.asarray(((5., -2., 7.), (-5., 2., -7.)))
    original = (xyz.copy(), velocity.copy(), masses.copy())
    operator = AnalyticalOperator(lambda x: (-float(np.sum(x * force)), -force))
    final_x, final_v, summary, frames, events = run(operator, xyz, velocity, masses, steps=200)
    elapsed_ps = .1
    acceleration = force / masses[:, None]
    expected_x = xyz / 10 + velocity * elapsed_ps + .5 * acceleration * elapsed_ps ** 2
    expected_v = velocity + acceleration * elapsed_ps
    np.testing.assert_allclose(final_x / 10, expected_x, rtol=0, atol=4e-15)
    np.testing.assert_allclose(final_v, expected_v, rtol=0, atol=1e-14)
    assert len(frames) == len(operator.calls) == summary['completed_evaluations'] == 201
    assert summary['operator_invocations'] == summary['operator_returns'] == 201
    assert D(summary['physical_time_seconds']) == D('1e-13')
    assert summary['maximum_momentum_component_change_dalton_nm_ps'] < 1e-12
    for actual, before in zip((xyz, velocity, masses), original, strict=True):
        assert np.array_equal(actual, before)
    assert np.array_equal(operator.calls[0], xyz)
    assert [frame['step'] for frame in frames] == list(range(201))
    assert [row['evaluation'] for row in events if row['event'] == 'trajectory-evaluation-entry'] == list(range(1, 202))
    assert summary['numerical_accuracy'] == summary['initial_ensemble_admission'] == summary['rate_admission'] == 'UNEVALUABLE'


def test_harmonic_motion_and_energy_converge_at_second_order_at_equal_physical_time():
    xyz = np.asarray(((.3, .2, -.1),))
    velocity = np.asarray(((.2, -.04, .1),))
    mass = np.asarray((4.,))
    coarse = run(AnalyticalOperator(harmonic), xyz, velocity, mass)
    fine = run(AnalyticalOperator(harmonic), xyz, velocity, mass, steps=80, dt=D('2.5e-16'))
    omega, elapsed_ps = 100., .02
    expected_x_nm = xyz / 10 * np.cos(omega * elapsed_ps) + velocity / omega * np.sin(omega * elapsed_ps)
    expected_v = velocity * np.cos(omega * elapsed_ps) - xyz / 10 * omega * np.sin(omega * elapsed_ps)
    position_errors = [float(np.max(np.abs(result[0] / 10 - expected_x_nm))) for result in (coarse, fine)]
    velocity_errors = [float(np.max(np.abs(result[1] - expected_v))) for result in (coarse, fine)]
    assert 0 < position_errors[1] < .26 * position_errors[0] < 1e-5
    assert 0 < velocity_errors[1] < .26 * velocity_errors[0] < 1e-3
    assert D(coarse[2]['physical_time_seconds']) == D(fine[2]['physical_time_seconds'])
    assert 0 < fine[2]['maximum_absolute_energy_drift_kj_mol'] < .26 * coarse[2]['maximum_absolute_energy_drift_kj_mol']
    for frame in coarse[3]:
        potential = harmonic(frame['coordinates_angstrom'] / 10)[0]
        kinetic = .5 * float(np.sum(mass[:, None] * frame['velocities_nm_per_ps'] ** 2))
        event = next(row for row in coarse[4] if row['event'] == 'trajectory-frame-return' and row['step'] == frame['step'])
        assert abs(event['total_energy_kj_mol'] - (potential + kinetic)) < 1e-13


def test_velocity_verlet_is_time_reversible_without_velocity_rescaling():
    xyz = np.asarray(((.3, .2, -.1),))
    velocity = np.asarray(((.2, -.04, .1),))
    forward = run(AnalyticalOperator(harmonic), xyz, velocity, (4.,))
    backward = run(AnalyticalOperator(harmonic), forward[0], -forward[1], (4.,))
    np.testing.assert_allclose(backward[0], xyz, rtol=0, atol=2e-14)
    np.testing.assert_allclose(backward[1], -velocity, rtol=0, atol=2e-13)
    assert forward[2]['thermostat'] == forward[2]['constraints'] == forward[2]['bias'] == 'NONE'
    assert not any(forward[2][key] for key in ('mass_repartitioning', 'velocity_rescaling', 'coordinate_wrapping'))


def test_exact_physical_clock_and_strict_settings_ignore_decimal_context_rounding():
    with localcontext() as context:
        context.prec = 3
        settings = ReferenceDynamicsSettings('settings.exposed.long-clock', D('5e-16'), 123456789012345678901234567890)
        assert settings.time_at_step(settings.steps) == D('61728394506172.839450617283945')
        assert settings.step_picoseconds == .0005
    assert decode_canonical_bytes(settings.canonical_bytes(), ReferenceDynamicsSettings, maximum_bytes=4096) == settings
    for step in (-1, True, settings.steps + 1):
        with pytest.raises(ValueError, match='actual step'):
            settings.time_at_step(step)


@pytest.mark.parametrize(('step', 'count'), ((D(0), 2), (D('1e-15'), 2), (D('1e-400'), 2), (D('5e-16'), True), (D('5e-16'), 0)))
def test_invalid_physical_horizon_refuses(step, count):
    with pytest.raises(ValueError):
        ReferenceDynamicsSettings('settings.exposed.invalid', step, count)


@pytest.mark.parametrize('failure', ('native', 'unit', 'short', 'nonfinite', 'mutated-input'))
def test_failed_force_preserves_original_counts_and_never_retries(failure):
    operator = AnalyticalOperator(harmonic, failure=failure)
    frames, events = [], []
    with pytest.raises((ValueError, RuntimeError)):
        propagate_reference_trajectory(operator=operator, initial_angstrom=((.3, .2, -.1),),
            initial_velocity_nm_per_ps=((.2, -.04, .1),), physical_masses_dalton=(4.,),
            settings=ReferenceDynamicsSettings('settings.exposed.failure', D('5e-16'), 4),
            observe=events.append, capture=frames.append)
    assert len(operator.calls) == 2 and len(frames) == 1
    error = events[-1]
    assert error['event'] == 'trajectory-error' and error['step'] == 1
    assert error['operator_invocations'] == 2
    assert error['operator_returns'] == (1 if failure == 'native' else 2)
    assert error['completed_evaluations'] == error['captured_frames'] == 1


def test_capture_failure_stops_before_any_subsequent_force():
    operator = AnalyticalOperator(harmonic)
    events = []
    def capture(frame):
        if frame['step'] == 1:
            raise OSError('exposed-capture-failure')
    with pytest.raises(OSError, match='capture-failure'):
        propagate_reference_trajectory(operator=operator, initial_angstrom=((.3, .2, -.1),),
            initial_velocity_nm_per_ps=((.2, -.04, .1),), physical_masses_dalton=(4.,),
            settings=ReferenceDynamicsSettings('settings.exposed.capture', D('5e-16'), 4),
            observe=events.append, capture=capture)
    assert len(operator.calls) == 2
    assert events[-1]['operator_returns'] == events[-1]['completed_evaluations'] == 2
    assert events[-1]['captured_frames'] == 1


@pytest.mark.parametrize('mass', ((0.,), (-4.,), (float('inf'),), (4., 4.)))
def test_missing_or_nonphysical_mass_refuses_before_force_entry(mass):
    operator = AnalyticalOperator(harmonic)
    with pytest.raises(ValueError, match='positive mass'):
        run(operator, ((.3, .2, -.1),), ((.2, -.04, .1),), mass)
    assert not operator.calls


def test_unrepresentable_initial_kinetic_energy_refuses_before_any_force():
    operator = AnalyticalOperator(harmonic)
    with pytest.raises((ValueError, FloatingPointError)):
        run(operator, ((.3, .2, -.1),), ((1e308, 0., 0.),), (4.,))
    assert not operator.calls


def trajectory_fixture():
    xyz = np.asarray(((.3, .2, -.1),))
    velocity = np.asarray(((.2, -.04, .1),))
    operator = AnalyticalOperator(harmonic)
    result = run(operator, xyz, velocity, (4.,))
    selected = dict(initial_angstrom=xyz, initial_velocity_nm_per_ps=velocity,
        physical_masses_dalton=(4.,),
        settings=ReferenceDynamicsSettings('settings.exposed.reference-dynamics', D('5e-16'), 40),
        criteria=ReferenceTrajectoryCriteria('criteria.exposed.harmonic-trace',
            D('1e-12'), D('1e-11'), D('.1'), None))
    return operator, result, selected


def test_independent_reader_checks_complete_retained_equations_without_force_calls():
    operator, result, selected = trajectory_fixture()
    calls_before = len(operator.calls)
    assessment = assess_reference_trajectory_frames(iter(result[3]), **selected)
    assert len(operator.calls) == calls_before == 41
    assert assessment['new_operator_evaluations'] == 0
    assert assessment['retained_force_frames'] == 41 and assessment['completed_steps'] == 40
    assert assessment['selected_horizon_complete']
    assert assessment['selected_trace_criteria'] == 'SATISFIED' and assessment['findings'] == ()
    assert assessment['maximum_position_recurrence_error_nm'] < 1e-15
    assert assessment['maximum_velocity_recurrence_error_nm_ps'] < 1e-14
    assert D(assessment['observed_physical_time_seconds']) == D('2e-14')
    assert assessment['physical_rate_admission'] == assessment['numerical_step_convergence'] == 'UNEVALUABLE'
    assert decode_canonical_bytes(selected['criteria'].canonical_bytes(), ReferenceTrajectoryCriteria,
        maximum_bytes=4096) == selected['criteria']


@pytest.mark.parametrize('changed', ('gradient', 'velocity', 'energy', 'mass'))
def test_finite_dynamical_disagreement_is_a_retained_negative(changed):
    operator, result, selected = trajectory_fixture()
    frames = result[3]
    if changed == 'gradient':
        frames[20]['gradient_hartree_per_bohr'][0, 0] += .001
    elif changed == 'velocity':
        frames[20]['velocities_nm_per_ps'][0, 0] += 20
    elif changed == 'energy':
        frames[20]['energy_hartree'] += 1
    else:
        selected['physical_masses_dalton'] = (4.1,)
    assessment = assess_reference_trajectory_frames(iter(frames), **selected)
    assert assessment['selected_horizon_complete'] and assessment['selected_trace_criteria'] == 'FALSIFIED'
    assert assessment['findings'] and len(operator.calls) == 41
    assert assessment['physical_rate_admission'] == 'UNEVALUABLE'


@pytest.mark.parametrize('changed', ('clock', 'missing-middle', 'unit', 'energy-type', 'initial-position', 'initial-velocity', 'short-array'))
def test_changed_clock_census_initial_state_or_units_refuse(changed):
    operator, result, selected = trajectory_fixture()
    frames = result[3]
    if changed == 'clock':
        frames[20]['physical_time_seconds'] = '1.0000000000000000001e-14'
    elif changed == 'missing-middle':
        frames.pop(20)
    elif changed == 'unit':
        frames[20]['hartree_kj_mol'] *= 10
    elif changed == 'energy-type':
        frames[20]['energy_hartree'] = str(frames[20]['energy_hartree'])
    elif changed == 'initial-position':
        frames[0]['coordinates_angstrom'][0, 0] += 1
    elif changed == 'initial-velocity':
        frames[0]['velocities_nm_per_ps'][0, 0] += .1
    else:
        frames[20]['gradient_hartree_per_bohr'] = np.empty((0, 3), dtype='<f8')
    with pytest.raises(ValueError, match='trajectory frame'):
        assess_reference_trajectory_frames(iter(frames), **selected)
    assert len(operator.calls) == 41


@pytest.mark.parametrize('frame_count', (0, 1, 10))
def test_incomplete_prefix_keeps_its_observed_time_and_cannot_pass_whole_horizon(frame_count):
    operator, result, selected = trajectory_fixture()
    assessment = assess_reference_trajectory_frames(iter(result[3][:frame_count]), **selected)
    assert not assessment['selected_horizon_complete'] and assessment['selected_trace_criteria'] == 'UNEVALUABLE'
    assert assessment['retained_force_frames'] == frame_count
    assert assessment['completed_steps'] == max(0, frame_count - 1)
    assert assessment['findings'] == ('selected-physical-horizon-incomplete',)
    if frame_count:
        assert D(assessment['observed_physical_time_seconds']) == D(frame_count - 1) * D('5e-16')
    else:
        assert assessment['observed_physical_time_seconds'] is None
        assert assessment['maximum_energy_drift_kj_mol'] is None
    assert len(operator.calls) == 41


def test_absent_selected_criteria_returns_measurements_without_acceptance():
    _, result, selected = trajectory_fixture()
    selected['criteria'] = None
    assessment = assess_reference_trajectory_frames(iter(result[3]), **selected)
    assert assessment['selected_horizon_complete']
    assert assessment['selected_trace_criteria'] == 'UNEVALUABLE'
    assert assessment['criteria'] is None and assessment['maximum_energy_drift_kj_mol'] > 0


def test_captured_snapshots_do_not_alias_the_continued_state_or_caller_inputs():
    xyz = np.asarray(((.3, .2, -.1),))
    velocity = np.asarray(((.2, -.04, .1),))
    expected = run(AnalyticalOperator(harmonic), xyz, velocity, (4.,))
    def change_discarded_copy(frame):
        frame['coordinates_angstrom'][:] = 1e10
        frame['velocities_nm_per_ps'][:] = -1e10
        frame['gradient_hartree_per_bohr'][:] = 0
    actual = run(AnalyticalOperator(harmonic), xyz, velocity, (4.,), capture=change_discarded_copy)
    assert np.array_equal(actual[0], expected[0]) and np.array_equal(actual[1], expected[1])
    assert np.array_equal(expected[3][0]['coordinates_angstrom'], xyz)
    assert np.array_equal(expected[3][0]['velocities_nm_per_ps'], velocity)
    assert not np.shares_memory(expected[3][0]['coordinates_angstrom'], expected[3][-1]['coordinates_angstrom'])
