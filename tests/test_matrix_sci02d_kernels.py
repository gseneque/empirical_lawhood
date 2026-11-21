# SPDX-License-Identifier: MPL-2.0
"""Exposed SCI02-D conformance controls, never scientific study evidence."""
from dataclasses import replace
from decimal import Decimal
import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import physics, science, assessment
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BridgeDesign, BridgeSelection
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters, analytic_gradient_terms, reference_action_terms


def design(): return BridgeDesign('test.sci02d.design', 'a'*64)


def test_new_allocation_and_exact_operands():
    d = design()
    selection = BridgeSelection('test.sci02d.selection', d, 'b'*64)
    roots = [selection.root(bank, i) for bank, count in [('TRAINING', 16), ('CONFIRMATION', 64), ('REFERENCE', 8)] for i in range(count)]
    assert len({v.group_id for v in roots}) == 88
    assert len({p.object_fingerprint for v in roots for p in v.streams}) == 264
    with pytest.raises(ValueError): selection.root('CONFIRMATION', 64)
    with pytest.raises(ValueError): replace(d, alpha_y=Decimal('7.333333333333333333333333333'))
    with pytest.raises(ValueError): replace(d, temperature=1.)


def test_batch_force_against_literal_action_and_scalar_owner():
    d = design(); rng = np.random.default_rng(4381)
    positions = physics.initial_positions(d, 2)+physics.lift(.07*rng.normal(size=(2, 2, 2, 96)))
    couplings = np.broadcast_to(np.array([.5, 2.])[None, :, None], (2, 2, 2))
    centers = np.broadcast_to(np.array([.8, 1.2]), (2, 2, 2))
    result = physics.gradient(d, positions, couplings, centers)
    for index in np.ndindex(2, 2, 2):
        q, c, s = positions[index], couplings[index], centers[index]
        parameters = SixMatrixParameters(2, .5, .5, c, float(d.alpha_x), float(d.alpha_y))
        expected = analytic_gradient_terms(q, parameters).total
        expected[1] += float(d.stiffness)*(physics.receiver(d, q)-s)*q[1]/(6*physics.radial_scale(d))
        np.testing.assert_allclose(result[index], expected, atol=2e-13, rtol=1e-13)
        direction = physics.lift(rng.normal(size=96)); direction /= np.linalg.norm(direction)
        def potential(x):
            return reference_action_terms(x, parameters).total+.5*float(d.stiffness)*(physics.receiver(d, x)-s)**2
        eps = 2e-5
        derivative = (potential(q+eps*direction)-potential(q-eps*direction))/(2*eps)
        assert derivative == pytest.approx(np.vdot(direction, result[index]).real, abs=2e-6)


def test_stein_divergence_from_independent_cartesian_stencil():
    d = design(); rng = np.random.default_rng(782)
    q = physics.coordinates(physics.initial_positions(d, 1)[1, 0, 0])+.1*rng.normal(size=96)
    center, coupling, eps = .9, 2., 1e-5
    scale = physics.radial_scale(d)
    def vectors(x):
        xi, chi = x[48:]@x[48:]/(12*scale), x[:48]@x[:48]/12
        ydir = np.r_[np.zeros(48), x[48:]/(6*scale)]
        xdir = np.r_[x[:48]/6, np.zeros(48)]
        return np.stack((ydir, (xi-center)*ydir, chi*ydir, (xi-center)*xdir))
    div = np.zeros(4)
    for j in range(96):
        direction = np.eye(96)[j]*eps
        div += (vectors(q+direction)[:, j]-vectors(q-direction)[:, j])/(2*eps)
    matrix = physics.lift(q); grad = physics.gradient(d, matrix, coupling, center)
    direct = float(d.temperature)*div-vectors(q)@physics.coordinates(grad)
    actual = physics.fields(d, matrix, grad, center)[1:]
    np.testing.assert_allclose(actual, direct, atol=1e-8, rtol=1e-8)
    bare = physics.native_gradient(d, matrix, coupling)
    assert np.max(abs(physics.fields(d, matrix, bare, center)[1:]-actual)) > .01


def test_recorded_baoab_is_independently_reconstructed():
    d = design(); rng = np.random.default_rng(12)
    q = physics.initial_positions(d, 1)
    p = physics.lift(rng.normal(size=(2, 2, 1, 96)))
    noise = physics.lift(rng.normal(size=(2, 2, 1, 96)))
    c = np.broadcast_to(np.array([.5, 2.])[None, :, None], (2, 2, 1)); s = np.ones((2, 2, 1))
    g = physics.gradient(d, q, c, s)
    after = physics.step(d, q, p, g, noise, float(d.timestep), c, s)
    witness = np.stack([physics.coordinates(v) for v in (q, p, g, *after, noise)])[None]
    assert assessment.transition_check(d, witness) < 1e-14
    witness[0, 3, 0, 0, 0, 0] += 1e-4
    assert assessment.transition_check(d, witness) > 1e-5


def test_solvable_means_and_finite_restraint_connection():
    result = science.controls()
    assert result.disposition == 'AVAILABLE'
    q_discrete, q_restrained, q_pmf, correction, quadrature = result.arrays['connections']
    assert q_pmf == pytest.approx(-np.log(2)/2)
    assert q_restrained+correction == pytest.approx(q_pmf)
    assert q_discrete+quadrature == pytest.approx(q_restrained)
    assert abs(correction) > .01
    assert np.max(abs(result.arrays['zero_means'])) < 1e-10


def test_disclosed_short_native_path_and_independent_assessment():
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import sampling
    d = design(); selection = BridgeSelection('test.short.selection', d, 'c'*64)
    # The immutable public BridgeDesign refuses these shortened horizons. This
    # unregistered fixture exercises code only and cannot become a study input.
    fixture_design = SimpleNamespace(**{name:getattr(d,name) for name in d.__dataclass_fields__ if name != 'SCHEMA'})
    fixture_design.burn_steps, fixture_design.production_steps, fixture_design.block_samples = 1024,1024,4
    fixture_design.grid = d.grid
    root = selection.root('TRAINING',0)
    config = SimpleNamespace(design=fixture_design,root=root,fitted=None)
    result = sampling.acquire(config,selection.streams('TRAINING',0))
    checked = assessment.assess(config,result.arrays)
    assert checked.disposition == 'AVAILABLE'
    assert np.max(checked.arrays['reconstruction_residuals']) < 1e-10
    assert checked.arrays['node_means'].shape == (2,2,2,5,5)
    assert checked.arrays['correlation_diagnostics'].shape == (2,2,3,2,3)
    for view in range(2):
        for prep in range(2):
            direct = checked.arrays['series'][view,prep,:,0].reshape(-1,4).mean(axis=1)
            assert checked.arrays['paired_block_variance'][view,prep,0] == pytest.approx(np.var(direct,ddof=1),abs=1e-12)
    changed = dict(result.arrays); changed['sample_ticks'] = changed['sample_ticks']+1
    with pytest.raises(ValueError,match='clocks'): assessment.assess(config,changed)
