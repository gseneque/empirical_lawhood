# SPDX-License-Identifier: MPL-2.0
"""Independent source tangent, signed cancellation and fixed basis controls."""
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import (
    MECHANISM_READOUT_RULE, hessian_action_batch, hold_tangent_response, input_krylov_basis, signed_cell,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermitian_part
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import hessian_image, tangent_step
from empirical_lawhood.adapters.simulators.six_matrix_response.preparation_differential import NativeStateDifferential
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def test_batched_HOLD_matches_each_source_owned_Hessian_and_both_kick_tangent():
    rng = np.random.default_rng(451)
    state = hermitian_part(rng.normal(size=(129, 2, 3, 4, 4)) + 1j * rng.normal(size=(129, 2, 3, 4, 4))) * .02
    forces = hermitian_part(rng.normal(size=(4, 2, 3, 4, 4)) + 1j * rng.normal(size=(4, 2, 3, 4, 4)))
    receivers = hermitian_part(rng.normal(size=(48, 2, 2, 3, 4, 4)) + 1j * rng.normal(size=(48, 2, 2, 3, 4, 4)))
    alphas = np.column_stack((np.linspace(.2, .3, 129), np.linspace(.8, .6, 129)))
    member = SimpleNamespace(mass_x=.03, mass_y=.07, cross_coupling_gamma=.4)
    view = SimpleNamespace(timestep=Decimal('.001'), friction_gamma=Decimal('1.7'))
    parameters = SixMatrixParameters(2, .03, .07, .4, .2, .8)
    batch = hessian_action_batch(state[0], forces, parameters)
    for index in range(4):
        np.testing.assert_allclose(batch[index], hessian_image(state[0], forces[index], parameters), rtol=2e-14, atol=2e-14)
    expected = []
    for index, force in enumerate(forces):
        differential = NativeStateDifferential(np.zeros_like(force), np.zeros_like(force))
        samples = []
        for tick in range(128):
            before, after = (SixMatrixState(2, state[j], np.zeros_like(force), j, *alphas[j]) for j in (tick, tick + 1))
            differential = tangent_step(before, after, differential, direction=force,
                force_derivative=.01 if tick < 16 else 0., member=member, numerical_view=view)
            samples.append(np.einsum('rpsjab,psjab->r', receivers.conj(),
                np.stack((differential.positions, differential.momenta))).real)
        expected.append(samples)
    actual = hold_tangent_response(state, alphas, forces, receivers, member=member, numerical_view=view, pulse_steps=16)
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-15)


def test_fixed_Krylov_captures_the_input_orbit_and_reports_actual_slow_fallback():
    # Six directed shifts per input yield exactly 24 position directions.
    transition = np.zeros((192, 192))
    for chain in range(4):
        for power in range(5):
            transition[4 * (power + 1) + chain, 4 * power + chain] = 1.
    inputs = np.zeros((192, 4))
    inputs[:4] = np.eye(4)
    spectrum, eigenvectors = np.arange(96, dtype=float), np.eye(96)
    basis, ranks = input_krylov_basis(transition, inputs, spectrum, eigenvectors, native_horizon=128)
    np.testing.assert_array_equal(basis @ basis.T, np.diag([1.] * 24 + [0.] * 72))
    assert (ranks['input_dimensions'], ranks['krylov_dimensions'], ranks['slow_fallback_dimensions']) == (4, 20, 0)
    fallback, ranks = input_krylov_basis(np.eye(192), inputs, spectrum, eigenvectors, native_horizon=256)
    np.testing.assert_array_equal(fallback @ fallback.T, basis @ basis.T)
    assert (ranks['input_dimensions'], ranks['krylov_dimensions'], ranks['slow_fallback_dimensions']) == (4, 0, 20)
    assert decode_canonical_bytes(MECHANISM_READOUT_RULE.canonical_bytes(), type(MECHANISM_READOUT_RULE), maximum_bytes=None) == MECHANISM_READOUT_RULE


def test_signed_accounting_keeps_cancellation_actual_magnitude_and_unavailable_cells():
    native, hold, full, factor = (np.full(24, value, dtype=float) for value in (.02, -.01, .015, 0.))
    cell = signed_cell(native, hold, full, factor, scale=.1)
    assert cell['status'] == 'AVAILABLE'
    assert cell['twice_signed_cross_terms_01_02_12'][0] < 0
    assert float(cell['total_squared_error']) == pytest.approx(.96)
    assert float(sum(cell['term_squared_norms']) + sum(cell['twice_signed_cross_terms_01_02_12'])) == pytest.approx(.96)
    assert float(cell['actual_response_norm']) == pytest.approx(np.sqrt(24) * .02)
    assert len(cell['signed_task_vectors']) == 3 and all(len(row) == 24 for row in cell['signed_task_vectors'])
    native[0] = np.nan
    assert signed_cell(native, hold, full, factor, scale=.1)['status'] == 'UNAVAILABLE'


def test_complete_missing_future_read_keeps_all_cells_fine_features_and_instrument_contrasts():
    from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import same_bank_mechanism, instrument_change
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from tests.test_matrix_causal_hessian import causal_case

    protocol, causal, frozen = causal_case()
    for index, action in enumerate(protocol.actions):
        action.action_id = 'action.' + str(index)
    result = same_bank_mechanism(protocol, causal, frozen, {}, panel_ids=('panel.a', 'panel.b'),
        numerical_status='UNEVALUABLE', feature_disposition='AVAILABLE')
    assert len(result['signed_accounting']) == 128
    assert all(row['status'] == 'UNAVAILABLE' for row in result['signed_accounting'])
    assert tuple(row.view for row in result['causal_features']) == ('PRIMARY', 'FINE')
    assert all(row['sampled_duration'].count is None for row in result['INPUT_KRYLOV48'])
    assert not result['comparator_paired_numerically_usable']
    contrast = instrument_change(result['instrument'], result['instrument'])
    assert contrast['identical_forces'] and contrast['receiver_map_difference_frobenius'] == 0
    assert contrast['receiver_projector_difference_frobenius'] == 0
    assert canonical_json_bytes(result)


def test_complete_signed_read_maps_both_physical_clocks_and_original_action_cells():
    from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import same_bank_mechanism, instrument_summary
    from empirical_lawhood.adapters.methods.matrix_factor_response.science import native_position_lift
    from tests.test_matrix_causal_hessian import causal_case, time_varying_map

    protocol, causal, frozen = causal_case()
    maps = instrument_summary(frozen)
    force = np.asarray(maps['force_maps_real_Hermitian'], dtype=float).T * .01
    receiver = np.asarray(maps['receiver_maps_real_Hermitian'], dtype=float)
    received = {}
    for index, action in enumerate(protocol.actions):
        action.action_id = 'action.' + str(index)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = 128 * multiplier
        h = frozen[view + '_hessian']
        phase = time_varying_map(h, np.zeros_like(h), force, np.eye(192), .001 / multiplier,
            np.exp(-.001 / multiplier), 16 * multiplier, count, 0.)
        expected = phase[:, multiplier - 1::multiplier] @ receiver.T
        frozen[view + '_full_grid_full_coupled'] = expected
        frozen[view + '_full_grid_factor'] = expected
        q0 = causal[view + '_positions'][-1]
        for panel in ('panel.a', 'panel.b'):
            for index, action in enumerate(protocol.actions):
                response = np.concatenate((np.zeros((1, 192)), phase[index]))
                for sign, coefficient in (('hold', 0), ('minus', -1), ('plus', 1)):
                    stem = 'branch.' + view + '.' + panel + '.' + action.action_id + '.' + sign + '.'
                    received[stem + 'positions'] = q0 + coefficient * np.asarray([native_position_lift(row[:96]) for row in response])
                    received[stem + 'momenta'] = coefficient * np.asarray([native_position_lift(row[96:]) for row in response])
                    received[stem + 'ticks'] = np.arange(256 * multiplier, 256 * multiplier + count + 1)
                    received[stem + 'alpha_tilde'] = np.broadcast_to(causal[view + '_alpha_tilde'][-1], (count + 1, 2)).copy()
                    received[stem + 'innovations'] = np.zeros((count, 2, 3, 4, 4), dtype=complex)
    costs = []
    result = same_bank_mechanism(protocol, causal, frozen, received, panel_ids=('panel.a', 'panel.b'),
        numerical_status='SATISFIED', feature_disposition='AVAILABLE', observe_cost=costs.append)
    assert len(result['signed_accounting']) == 128
    assert all(row['status'] == 'AVAILABLE' for row in result['signed_accounting'])
    assert all(row['total_error_norm'] < Decimal('1e-8') for row in result['signed_accounting'])
    assert all(row['actual_response_norm'] > 0 for row in result['signed_accounting'])
    assert all(row['construction']['status'] == 'AVAILABLE' for row in result['INPUT_KRYLOV48'])
    assert result['cost']['native_calls'] == result['cost']['fit_bundles'] == 0
    assert len(costs) == 1 and costs[0]['total_read_seconds'] >= costs[0]['causal_Hessian_read_seconds'] > 0
    replay = same_bank_mechanism(protocol, causal, frozen, received, panel_ids=('panel.a', 'panel.b'),
        numerical_status='SATISFIED', feature_disposition='AVAILABLE')
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    assert canonical_json_bytes(replay) == canonical_json_bytes(result)
    from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import compact_instrument
    compact = compact_instrument(result['instrument'])
    assert compact['forces_sha256'] == result['instrument']['forces_sha256']
    assert 'force_maps_real_Hermitian' not in compact and 'receiver_maps_real_Hermitian' not in compact
