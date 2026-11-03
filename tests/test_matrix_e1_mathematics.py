# SPDX-License-Identifier: MPL-2.0
"""Exposed mathematical falsifiers, never programme samples or qualification."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import _independent_leakage
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import (
    causal_observations, lifetime, measure_sector, validate_trace,
)
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_derivatives
from empirical_lawhood.adapters.simulators.six_matrix_response.model import su2_generators
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import hermitian_noise
from tests.test_matrix_factor_lifetime import spec
from tests.test_matrix_parameter_native import REGIMES, coordinate, corpus


def test_initial_presence_is_an_explicit_exception_without_invented_trailing_history():
    rule = spec(risk_start_tick=0, trailing_persistence_ticks=32)
    exact = measure_sector(algebra.RIGHT, rule)
    measured = {tick: exact for tick in rule.lattice}
    observed, _ = causal_observations(rule, measured, initial_presence=True)
    historical, _ = causal_observations(rule, measured)
    assert tuple(row.causal_admitted for row in observed) == (True, False, True, True)
    assert tuple(row.causal_admitted for row in historical) == (False, False, True, True)
    assert lifetime(observed, rule).origin_tick == 0
    assert lifetime(historical, rule).origin_tick == 32
    record = SimpleNamespace(rule=rule.identity, sector='Y', observations=observed,
        moving_lifetime=lifetime(observed, rule), origin_fixed_lifetime=lifetime(observed, rule, origin_fixed=True))
    validate_trace(record, rule, initial_presence=True)
    with pytest.raises(ValueError, match='causal past'):
        validate_trace(record, rule)
    with pytest.raises(ValueError, match='time-zero risk'):
        causal_observations(replace(rule, risk_start_tick=16), measured, initial_presence=True)
    # Initial admission keeps the original origin even if a later projector
    # differs; complete later data cannot revise the initial measurement.
    poisoned = measured | {48: replace(exact, associative_leakage=Decimal('.9'))}
    alternate, _ = causal_observations(rule, poisoned, initial_presence=True)
    assert alternate[:3] == observed[:3]
    assert lifetime(alternate, rule).origin_tick == 0
    assert lifetime(alternate, rule).disposition == 'EXIT_INTERVAL'


@pytest.mark.parametrize('seed', (14, 173, 2001))
def test_complex_associative_identity_closure_distinguishes_factor_lie_only_and_generic(seed):
    rng = np.random.default_rng(seed)
    unitary, _ = np.linalg.qr(rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4)))
    factor = unitary @ algebra.LEFT @ unitary.conj().T
    spin = unitary @ (su2_generators(4) / np.sqrt(5)) @ unitary.conj().T
    generic, _ = np.linalg.qr(rng.normal(size=(15, 3)))
    values = []
    for basis in (algebra.coords(factor).T, algebra.coords(spin).T, generic):
        metrics, _ = algebra.algebra(basis)
        independent = _independent_leakage(basis)
        np.testing.assert_allclose(independent,
            (metrics['associative_leakage'], metrics['lie_leakage']), rtol=1e-12, atol=1e-25)
        values.append(independent)
    assert values[0][0] < 1e-25 and values[0][1] < 1e-25
    assert values[1][1] < 1e-25 and values[1][0] > .05
    assert values[2][0] > .05
    # The complex span must retain the imaginary Pauli product. Projecting
    # onto a real span would wrongly reject this exact associative algebra.
    product = factor[0] @ factor[1]
    basis = (algebra.IDENTITY / 2, *factor)
    assert any(abs(np.vdot(axis, product).imag) > .1 for axis in basis)
    np.testing.assert_allclose(product, sum(np.vdot(axis, product) * axis for axis in basis), atol=1e-14)


def test_common_conjugation_preserves_native_state_force_receiver_noise_and_odd_response():
    rng, state, direction, _, _ = corpus(18703)
    selected = coordinate(REGIMES[1])
    unitary, _ = np.linalg.qr(rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4)))
    transform = lambda values: np.asarray(unitary @ values @ unitary.conj().T, dtype='<c16')
    receivers = np.asarray([hermitian_noise(rng=rng, q=2) for _ in range(4)])
    innovations = tuple(hermitian_noise(rng=rng, q=2) for _ in range(8))
    initial = replace(state, positions=transform(state.positions), momenta=transform(state.momenta))
    responses = []
    for changed in (False, True):
        branches = []
        for sign in (-1, 0, 1):
            current = initial if changed else state
            for index, noise in enumerate(innovations):
                current = parameter_derivatives.scheduled_force_step(current,
                    direction=transform(direction) if changed else direction,
                    amplitude=sign * .01 if index < 4 else 0., member=selected.member,
                    numerical_view=selected.primary_view, next_alpha_tilde_x=.45 + index * .002,
                    next_alpha_tilde_y=.8 + index * .003,
                    standardized_noise=transform(noise) if changed else noise)
            branches.append(current)
        responses.append(branches)
    for original, changed in zip(*responses, strict=True):
        np.testing.assert_allclose(changed.positions, transform(original.positions), rtol=1e-12, atol=1e-13)
        np.testing.assert_allclose(changed.momenta, transform(original.momenta), rtol=1e-12, atol=1e-13)
    for name in ('positions', 'momenta'):
        original = (getattr(responses[0][2], name) - getattr(responses[0][0], name)) / 2
        changed = (getattr(responses[1][2], name) - getattr(responses[1][0], name)) / 2
        expected_readout = np.asarray([np.vdot(receiver, original).real for receiver in receivers])
        actual_readout = np.asarray([np.vdot(receiver, changed).real for receiver in transform(receivers)])
        assert np.linalg.norm(expected_readout) > 1e-10
        np.testing.assert_allclose(actual_readout, expected_readout, rtol=1e-8, atol=1e-13)
