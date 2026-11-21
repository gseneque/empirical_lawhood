# SPDX-License-Identifier: MPL-2.0
"""Independent finite-matrix falsifiers; no enzyme or GPU evidence."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.constrained_electronic_read import _array, assess_electronic_arrays
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_coupling_science import determinant_cofactors, pair_coupling, spin_orbit_spinor
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ConstrainedElectronicState, ElectronicPopulationConstraint, ElectronicStateCriteria, SpinOrbitMeanFieldSettings, constraint_groups
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def state(*, soc=False):
    pin = ObjectIdentity('exposed.model', 'empirical-lawhood/testing/exposed-model', '1.0.0', '0'*64)
    rows = (ElectronicPopulationConstraint('a.spin', 'ALPHA_MINUS_BETA_POPULATION', (4,), D(0)),
        ElectronicPopulationConstraint('b.charge', 'ELECTRON_POPULATION', (2,), D(2)))
    return ConstrainedElectronicState('state.exposed', pin, (2, 4), 0, 1, rows,
        D('1e-8'), D('1e-10'), 100, (D(0), D('.2')), pin,
        SpinOrbitMeanFieldSettings('soc.exposed', 100, D('1e-14')) if soc else None)


def criteria():
    return ElectronicStateCriteria('criteria.exposed', D('1e-8'), D('.001'), D('.999'), D('.0001'), 2**28)


def arrays_and_metadata():
    c = np.stack((np.eye(2), np.eye(2)))
    o = np.array([[1., 0.], [1., 0.]])
    p = np.array([[[1., 0.], [0., 0.]], [[0., 0.], [0., 1.]]])
    a = {'ao-overlap':np.eye(2), 'mo-coefficients':c, 'mo-occupations':o,
        'mo-energies':np.array([[-.5, .4], [-.5, .4]]),
        'density':np.array([[[1., 0.], [0., 0.]], [[1., 0.], [0., 0.]]]),
        'constraint-projectors':p, 'constraint-multipliers':np.array([.2, 0.]),
        'constraint-potential':np.array([[[.2, 0.], [0., 0.]], [[.2, 0.], [0., 0.]]])}
    m = {'alpha_beta_electrons':[1, 1], 'electrons':2, 'atom_charges':[1,1], 'ao_labels':['0 H 1s', '1 H 1s'],
        'diagnostics':{'observed_electrons':[2., 0.], 'spin_square':0.,
            'lagrange_multipliers_hartree':[.2, 0.], 'alpha_beta_electron_counts':[1., 1.]}}
    return a, m


def test_projected_constraints_keep_canonical_order_and_actual_physical_mapping():
    selected = state()
    assert constraint_groups(selected) == (([[0]], [2.]), ([[1]], [0.]))
    assert [r.constraint_id for r in selected.solver_order] == ['b.charge', 'a.spin']
    assert decode_canonical_bytes(selected.canonical_bytes(), ConstrainedElectronicState,
        maximum_bytes=2**20) == selected
    with pytest.raises(ValueError, match='actual QM'):
        replace(selected, constraints=(replace(selected.constraints[0], physical_atom_indices=(3,)),))


@pytest.mark.parametrize('rank_defect', (0, 1, 2))
def test_complex_cofactors_match_explicit_minors_even_at_zero_determinant(rank_defect):
    rng = np.random.default_rng(809)
    a = rng.normal(size=(4, 4))+1j*rng.normal(size=(4, 4))
    if rank_defect:
        a[-rank_defect:] = 0
    determinant, cofactor, _ = determinant_cofactors(a)
    oracle = np.array([[(-1)**(i+j)*np.linalg.det(np.delete(np.delete(a, i, axis=0), j, axis=1))
        for j in range(4)] for i in range(4)])
    assert determinant == pytest.approx(np.linalg.det(a), abs=1e-12)
    np.testing.assert_allclose(cofactor, oracle, atol=1e-12)
    if rank_defect == 1:
        assert np.linalg.norm(cofactor) > 1
    if rank_defect == 2:
        np.testing.assert_allclose(cofactor, 0, atol=1e-12)


def test_orthogonal_singlet_triplet_determinants_retain_one_body_spin_flip():
    c = np.stack((np.eye(2), np.eye(2)))
    imaginary = np.zeros((3, 2, 2)); imaginary[0, 0, 1] = .1; imaginary[0, 1, 0] = -.1
    soc = spin_orbit_spinor(imaginary)
    np.testing.assert_allclose(soc, soc.conj().T, atol=0)
    result = pair_coupling(overlap=np.eye(2), coefficients_a=c, occupations_a=np.array([[1, 0], [1, 0]]),
        energy_a=-2., potential_a=np.zeros((2, 2, 2)), coefficients_b=c,
        occupations_b=np.array([[1, 1], [0, 0]]), energy_b=-1.8,
        potential_b=np.zeros((2, 2, 2)), maximum_overlap=.99, soc_imaginary=imaginary)
    assert result['determinant_overlap'] == 0
    assert result['orthogonal_spin_free_coupling_hartree'] == 0
    assert result['orthogonal_spin_orbit_coupling_hartree'] == pytest.approx(.05j)
    assert result['orthogonal_energy_gap_hartree'] == pytest.approx(.2)


def test_nonorthogonal_coupling_is_invariant_to_energy_origin_and_determinant_phase():
    c = np.stack((np.eye(2), np.eye(2)))
    theta = .6
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    b = np.stack((rotation, rotation))
    args = dict(overlap=np.eye(2), coefficients_a=c, occupations_a=np.array([[1, 0], [0, 0]]),
        energy_a=-1., potential_a=np.array([[[.1, .2], [.2, .3]]]*2), coefficients_b=b,
        occupations_b=np.array([[1, 0], [0, 0]]), energy_b=-.7,
        potential_b=np.array([[[.3, .1], [.1, .4]]]*2), maximum_overlap=.99)
    result = pair_coupling(**args)
    shifted = pair_coupling(**{**args, 'energy_a':999., 'energy_b':999.3})
    np.testing.assert_allclose(result['spin_free_hamiltonian_hartree'], shifted['spin_free_hamiltonian_hartree'], atol=1e-12)
    b = b.astype(complex); b[0, :, 0] *= np.exp(.73j)
    phased = pair_coupling(**{**args, 'coefficients_b':b})
    assert abs(phased['orthogonal_spin_free_coupling_hartree']) == pytest.approx(
        abs(result['orthogonal_spin_free_coupling_hartree']))
    assert phased['orthogonal_energy_gap_hartree'] == pytest.approx(result['orthogonal_energy_gap_hartree'])
    assert result['directional_hamiltonian_defect_hartree'] > 0


def test_exact_original_matrices_reconstruct_density_populations_and_spin():
    arrays, metadata = arrays_and_metadata()
    r = assess_electronic_arrays(state=state(), metadata=metadata, arrays=arrays, criteria=criteria())
    assert r['selected_matrix_criteria'] == r['selected_spin_square_criteria'] == 'SATISFIED'
    assert r['spin_square'] == 0 and r['original_electrons'] == 2
    assert r['physical_diabat_admission'] == 'UNEVALUABLE'


@pytest.mark.parametrize('damage', ('density', 'potential', 'projector', 'spin-label', 'fractional-occupation', 'census', 'memory'))
def test_original_electronic_inconsistencies_are_adverse_or_refused(damage):
    a, m = arrays_and_metadata(); rule = criteria()
    if damage == 'density': a['density'][0, 1, 1] = .5
    elif damage == 'potential': a['constraint-potential'][0, 0, 0] = -.2
    elif damage == 'projector': a['constraint-projectors'][0, 0, 0] = .5
    elif damage == 'spin-label': m['diagnostics']['spin_square'] = 2.
    elif damage == 'fractional-occupation': a['mo-occupations'][0, 0] = .5
    elif damage == 'census': del a['mo-energies']
    elif damage == 'memory': rule = replace(rule, maximum_workspace_bytes=1)
    if damage in ('fractional-occupation', 'census', 'memory'):
        with pytest.raises(ValueError): assess_electronic_arrays(state=state(), metadata=m, arrays=a, criteria=rule)
    else:
        r = assess_electronic_arrays(state=state(), metadata=m, arrays=a, criteria=rule)
        assert r['selected_matrix_criteria'] == 'FALSIFIED'


def test_bounded_npy_reader_checks_exact_layout_and_payload_before_allocation():
    a = np.arange(9, dtype='<f8').reshape((3, 3)); f = BytesIO(); np.save(f, a, allow_pickle=False)
    raw = f.getvalue()
    description = dict(shape=[3, 3], dtype='<f8', sha256=sha256(a.tobytes()).hexdigest())
    np.testing.assert_array_equal(_array(raw, description=description, maximum_bytes=72), a)
    for altered, spec, bound in ((raw+b'x', description, 72), (raw, {**description, 'shape':[30000, 30000]}, 72),
            (raw, {**description, 'sha256':'0'*64}, 72), (raw, description, 71)):
        with pytest.raises(ValueError): _array(altered, description=spec, maximum_bytes=bound)
