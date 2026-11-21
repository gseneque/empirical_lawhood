# SPDX-License-Identifier: MPL-2.0
"""Exposed bias arithmetic and refusals, not enzyme or sampling evidence."""

from dataclasses import replace
from decimal import Decimal as D
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention, evaluate_reference_umbrella_bias
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


KINDS = ('DISTANCE', 'DISTANCE_DIFFERENCE', 'IMPROPER_DIHEDRAL')
ATOMS = ('a', 'b', 'c', 'd', 'spectator')
CELL = np.diag((17., 19., 23.))
XYZ = np.array(((1.2, 2.3, 1.5), (2., 1., 2.), (3., 1.4, 1.3), (3.2, 2.5, 2.1), (6., 7., 8.)))


def selection(kinds=KINDS, **changes):
    sizes = dict(zip(KINDS, (2, 3, 4), strict=True))
    window = UmbrellaWindow('window.bias-exposed', 'model.bias-exposed', 'REACTANT',
        tuple(ATOMS[:sizes[k]] for k in kinds), kinds, tuple(D('.7') for k in kinds),
        tuple(D('3.25') for k in kinds), 3, 8, 2, 91, D('.01'))
    window = replace(window, **changes)
    convention = ReferenceBiasConvention('convention.bias-exposed',
        ObjectIdentity.from_record(window.window_id, window),
        tuple('RADIAN' if k == KINDS[2] else 'ANGSTROM' for k in kinds),
        tuple('KJ_PER_MOL_PER_RADIAN_SQUARED' if k == KINDS[2] else 'KJ_PER_MOL_PER_ANGSTROM_SQUARED' for k in kinds),
        'DISTANCE_12_MINUS_DISTANCE_23', 'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT',
        'ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND')
    return dict(window=window, convention=convention, physical_model_id=window.model_id,
        physical_atom_ids=ATOMS, coordinates_angstrom=XYZ.copy(), cell_vectors_angstrom=CELL.copy())


def oracle_values(selected, xyz):
    """Independent projections for the angle; no producer derivative helper."""
    values = []
    for ids, kind in zip(selected['window'].cv_atom_ids, selected['window'].cv_kinds, strict=True):
        points = xyz[[selected['physical_atom_ids'].index(a) for a in ids]]
        bonds = np.diff(points, axis=0)
        lengths = np.diag(selected['cell_vectors_angstrom'])
        bonds -= np.floor(bonds/lengths + .5)*lengths
        if kind == 'DISTANCE':
            value = math.sqrt(float(bonds[0] @ bonds[0]))
        elif kind == 'DISTANCE_DIFFERENCE':
            value = math.sqrt(float(bonds[0] @ bonds[0]))-math.sqrt(float(bonds[1] @ bonds[1]))
        else:
            axis = bonds[1]/np.linalg.norm(bonds[1])
            left = -bonds[0]+axis*np.dot(axis, bonds[0])
            right = bonds[2]-axis*np.dot(axis, bonds[2])
            value = math.atan2(np.dot(np.cross(axis, left), right), np.dot(left, right))
        values.append(value)
    return values


def oracle_energy(selected, xyz):
    values = oracle_values(selected, xyz)
    window = selected['window']
    total = 0.
    for value, center, constant, kind in zip(values, window.centers, window.force_constants, window.cv_kinds, strict=True):
        delta = value-float(center)
        if kind == 'IMPROPER_DIHEDRAL':
            delta = (delta+math.pi) % (2*math.pi)-math.pi
        total += .5*float(constant)*delta*delta
    return total


def test_convention_is_canonical_and_binds_unchanged_window():
    selected = selection()
    window = selected['window']
    original = window.canonical_bytes()
    convention = selected['convention']
    assert decode_canonical_bytes(convention.canonical_bytes(), ReferenceBiasConvention, maximum_bytes=4096) == convention
    returned = evaluate_reference_umbrella_bias(**selected)
    assert window.canonical_bytes() == original
    assert returned['reference_energy_included'] is False
    assert returned['equilibrium_admission'] == returned['rate_admission'] == 'UNEVALUABLE'
    assert returned['window'] == ObjectIdentity.from_record(window.window_id, window).to_document()
    assert returned['gradient_kind'] == 'ENERGY_DERIVATIVE_NOT_FORCE'
    assert returned['physical_atoms'] == 5


@pytest.mark.numerical(oracle='Analytic harmonic distance restraint energy 1 with gradients -2 and +2')
def test_distance_energy_gradient_sign_and_zero_spectator():
    selected = selection(('DISTANCE',), centers=(D(1),), force_constants=(D(2),))
    selected['coordinates_angstrom'] = np.array(((0., 0., 0.), (2., 0., 0.), (0., 0., 3.), (0., 2., 0.), (1., 2., 4.)))
    original = selected['coordinates_angstrom'].copy()
    result = evaluate_reference_umbrella_bias(**selected)
    assert result['energy_kj_mol'] == 1
    np.testing.assert_array_equal(result['gradient_kj_mol_per_angstrom'], ((-2, 0, 0), (2, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)))
    np.testing.assert_array_equal(selected['coordinates_angstrom'], original)


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('seed', range(5))
@pytest.mark.numerical(oracle='Separately implemented geometric collective variables and central differences of their harmonic energy')
def test_complete_cartesian_gradient_against_independent_energy_differences(kind, seed):
    selected = selection((kind,))
    xyz = XYZ+np.random.default_rng(seed).normal(scale=.2, size=XYZ.shape)
    selected['coordinates_angstrom'] = xyz
    result = evaluate_reference_umbrella_bias(**selected)
    assert result['cv_values'] == pytest.approx(oracle_values(selected, xyz), abs=1e-13)
    assert result['energy_kj_mol'] == pytest.approx(oracle_energy(selected, xyz), abs=1e-13)
    gradient = np.zeros_like(xyz)
    for i in range(len(xyz)):
        for j in range(3):
            plus, minus = xyz.copy(), xyz.copy()
            plus[i, j] += 1e-5
            minus[i, j] -= 1e-5
            gradient[i, j] = (oracle_energy(selected, plus)-oracle_energy(selected, minus))/(2e-5)
    np.testing.assert_allclose(result['gradient_kj_mol_per_angstrom'], gradient, atol=3e-8, rtol=1e-8)
    np.testing.assert_allclose(result['gradient_kj_mol_per_angstrom'].sum(axis=0), 0, atol=1e-13)
    np.testing.assert_allclose(np.cross(xyz, result['gradient_kj_mol_per_angstrom']).sum(axis=0), 0, atol=1e-12)
    np.testing.assert_array_equal(result['gradient_kj_mol_per_angstrom'][-1], 0)


def test_overlapping_terms_sum_and_atom_order_is_explicit():
    selected = selection()
    result = evaluate_reference_umbrella_bias(**selected)
    parts = [evaluate_reference_umbrella_bias(**selection((kind,))) for kind in KINDS]
    assert result['energy_kj_mol'] == pytest.approx(sum(p['energy_kj_mol'] for p in parts), abs=1e-14)
    np.testing.assert_allclose(result['gradient_kj_mol_per_angstrom'], sum(p['gradient_kj_mol_per_angstrom'] for p in parts), atol=1e-14)
    order = np.array((3, 0, 4, 2, 1))
    selected['physical_atom_ids'] = tuple(ATOMS[i] for i in order)
    selected['coordinates_angstrom'] = XYZ[order]
    reordered = evaluate_reference_umbrella_bias(**selected)
    np.testing.assert_allclose(reordered['gradient_kj_mol_per_angstrom'], result['gradient_kj_mol_per_angstrom'][order], atol=1e-14)


def test_translation_rotation_and_separate_periodic_images_preserve_bias():
    selected = selection()
    result = evaluate_reference_umbrella_bias(**selected)
    shifted = XYZ+np.array(((17., -19., 0.), (0., 38., -23.), (-17., 0., 46.), (34., 19., 0.), (0., 0., 0.)))
    selected['coordinates_angstrom'] = shifted+np.array((.31, -.76, 1.7))
    imaged = evaluate_reference_umbrella_bias(**selected)
    assert imaged['energy_kj_mol'] == pytest.approx(result['energy_kj_mol'], abs=2e-13)
    np.testing.assert_allclose(imaged['gradient_kj_mol_per_angstrom'], result['gradient_kj_mol_per_angstrom'], atol=2e-13)
    angle = .41
    rotation = np.array(((math.cos(angle), -math.sin(angle), 0), (math.sin(angle), math.cos(angle), 0), (0, 0, 1)))
    selected['coordinates_angstrom'] = XYZ @ rotation.T
    rotated = evaluate_reference_umbrella_bias(**selected)
    assert rotated['energy_kj_mol'] == pytest.approx(result['energy_kj_mol'], abs=2e-13)
    np.testing.assert_allclose(rotated['gradient_kj_mol_per_angstrom'], result['gradient_kj_mol_per_angstrom'] @ rotation.T, atol=2e-13)


def test_torsion_crosses_angle_branch_with_smooth_wrapped_restraint():
    selected = selection(('IMPROPER_DIHEDRAL',), centers=(D('3.0'),))
    results = []
    for theta in (math.pi-1e-7, -math.pi+1e-7):
        selected['coordinates_angstrom'] = np.array(((1., 0., 0.), (0., 0., 0.), (0., 0., 1.),
            (math.cos(theta), math.sin(theta), 1.), (4., 4., 4.)))
        result = evaluate_reference_umbrella_bias(**selected)
        assert result['cv_values'] == pytest.approx((theta,), abs=1e-14)
        assert result['cv_displacements'] == pytest.approx((math.pi-3+(theta-math.pi if theta>0 else theta+math.pi),), abs=1e-14)
        results.append(result)
    assert abs(results[0]['energy_kj_mol']-results[1]['energy_kj_mol']) < 1e-6
    np.testing.assert_allclose(results[0]['gradient_kj_mol_per_angstrom'], results[1]['gradient_kj_mol_per_angstrom'], atol=1e-6)


@pytest.mark.parametrize('change', [
    {'periodic_images':'UNWRAPPED'}, {'distance_difference':'DISTANCE_13_MINUS_DISTANCE_12'},
    {'dihedral':'UNSIGNED'}, {'center_units':('DEGREE',)*3},
    {'center_units':['ANGSTROM']*3}, {'force_constant_units':('KCAL_PER_MOL',)*3},
])
def test_undeclared_convention_or_unit_refusal(change):
    with pytest.raises(ValueError):
        replace(selection()['convention'], **change)


@pytest.mark.parametrize('field,value', [
    ('physical_model_id','different.model'), ('physical_atom_ids',('a', 'a', 'c', 'd', 'spectator')),
    ('physical_atom_ids',('a', 'b', 'c', 'foreign', 'spectator')), ('physical_atom_ids',list(ATOMS)),
    ('coordinates_angstrom',XYZ[:-1]), ('coordinates_angstrom',XYZ+float('nan')),
    ('coordinates_angstrom',XYZ.astype(complex)+1j),
    ('cell_vectors_angstrom',np.eye(3)*-10), ('cell_vectors_angstrom',CELL+np.ones((3,3))),
    ('cell_vectors_angstrom',np.diag((0., 19., 23.))),
])
def test_wrong_identity_census_coordinate_or_cell_refusal(field, value):
    selected = selection()
    selected[field] = value
    with pytest.raises(ValueError):
        evaluate_reference_umbrella_bias(**selected)


def test_changed_window_and_kind_specific_units_are_refused():
    selected = selection()
    selected['window'] = replace(selected['window'], centers=(D(1),)*3)
    with pytest.raises(ValueError, match='substitutes'):
        evaluate_reference_umbrella_bias(**selected)
    selected = selection()
    selected['convention'] = replace(selected['convention'], center_units=('ANGSTROM',)*3,
        force_constant_units=('KJ_PER_MOL_PER_ANGSTROM_SQUARED',)*3)
    with pytest.raises(ValueError, match='complete selected CV census'):
        evaluate_reference_umbrella_bias(**selected)


@pytest.mark.parametrize('kind,xyz', [
    ('DISTANCE', np.zeros((5,3))),
    ('DISTANCE', np.array(((0.,0.,0.), (8.5,1.,0.), (2.,1.,0.), (3.,2.,1.), (5.,5.,5.)))),
    ('IMPROPER_DIHEDRAL', np.array(((0.,0.,0.), (1.,0.,0.), (2.,0.,0.), (2.,1.,0.), (5.,5.,5.)))),
    ('IMPROPER_DIHEDRAL', np.array(((1.,0.,0.), (0.,0.,0.), (0.,0.,1.), (-1.,0.,1.), (5.,5.,5.)))),
])
def test_singular_bonds_planes_images_and_angular_cusp_refused(kind, xyz):
    selected = selection((kind,), centers=(D(0),))
    selected['coordinates_angstrom'] = xyz
    with pytest.raises(ValueError, match='unresolved|singular|cusp'):
        evaluate_reference_umbrella_bias(**selected)


@pytest.mark.parametrize('field,value', [('centers', D('1e400')), ('centers',D('1e-400')),
    ('force_constants',D('1e400')), ('force_constants',D('1e-400'))])
def test_numerical_parameter_overflow_or_underflow_refused(field, value):
    selected = selection(('DISTANCE',), **{field:(value,)})
    with pytest.raises(ValueError, match='representable'):
        evaluate_reference_umbrella_bias(**selected)


def test_torsion_center_is_principal_angle_not_degrees():
    with pytest.raises(ValueError, match='torsion centers'):
        evaluate_reference_umbrella_bias(**selection(('IMPROPER_DIHEDRAL',), centers=(D(180),)))
