# SPDX-License-Identifier: MPL-2.0
"""Independent retained bias controls; no enzyme or sampling qualification."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal as D
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_bias as producer
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria, assess_reference_bias_geometry
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.test_rubisco_periodic_bias import selection, KINDS, XYZ


def criteria(convention, ncv, **changes):
    return replace(ReferenceBiasGeometryCriteria('criteria.bias-geometry.exposed', convention.identity, D('1e-4'),
        (D('1e-11'),)*ncv, (D('2e-8'),)*ncv, (D('6e-8'),)*ncv,
        D('1e-10'), D('2e-7'), D('6e-7')), **changes)


def assess(selected, returned, **changes):
    return assess_reference_bias_geometry(**selected, returned=returned,
        criteria=criteria(selected['convention'], len(selected['window'].cv_kinds), **changes))


@pytest.mark.parametrize('kinds', [(kind,) for kind in KINDS]+[KINDS])
@pytest.mark.parametrize('imaged', (False, True))
def test_original_bias_geometry_independent_of_producer_and_periodic_images(kinds, imaged, monkeypatch):
    selected = selection(kinds)
    if imaged:
        selected['coordinates_angstrom'] += np.array(((17.,-19.,0.), (0.,38.,-23.), (-17.,0.,46.), (34.,19.,0.), (0.,0.,0.)))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    original = selected['coordinates_angstrom'].copy()
    monkeypatch.setattr(producer, 'evaluate_reference_umbrella_bias', lambda **k:pytest.fail('reader called producer'))
    result = assess(selected, returned)
    assert result['selected_bias_geometry_criteria'] == 'SATISFIED'
    assert result['new_operator_evaluations'] == result['producer_bias_evaluations'] == 0
    assert result['equilibrium_admission'] == result['physical_rate_admission'] == 'UNEVALUABLE'
    assert result['spectator_gradient_error_kj_mol_per_angstrom'] == 0
    np.testing.assert_array_equal(selected['coordinates_angstrom'], original)


def test_exact_distance_control_has_manual_original_return_and_known_sign():
    selected = selection(('DISTANCE',), centers=(D(1),), force_constants=(D(2),))
    selected['coordinates_angstrom'] = np.array(((0.,0.,0.), (2.,0.,0.), (3.,2.,1.), (4.,4.,5.), (5.,7.,9.)))
    convention = selected['convention']
    returned = dict(window=convention.window.to_document(), convention=convention.identity.to_document(),
        physical_model_id=selected['physical_model_id'], physical_atoms=5, cv_units=('ANGSTROM',),
        cv_values=(2.,), cv_displacements=(1.,), cv_atom_indices=((0,1),),
        cv_cartesian_derivatives=(np.array(((-1.,0.,0.), (1.,0.,0.))),),
        term_energies_kj_mol=(1.,), energy_kj_mol=1.,
        gradient_kj_mol_per_angstrom=np.array(((-2.,0.,0.), (2.,0.,0.), (0.,0.,0.), (0.,0.,0.), (0.,0.,0.))),
        gradient_kind='ENERGY_DERIVATIVE_NOT_FORCE', reference_energy_included=False,
        equilibrium_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
    assert assess(selected, returned)['selected_bias_geometry_criteria'] == 'SATISFIED'
    returned['gradient_kj_mol_per_angstrom'] *= -1
    assert assess(selected, returned)['selected_bias_geometry_criteria'] == 'FALSIFIED'


@pytest.mark.parametrize('change', ('value', 'displacement', 'term-energy', 'total-energy', 'local-derivative', 'gradient', 'spectator'))
def test_finite_original_bias_error_is_a_negative_not_an_unassessed_result(change):
    selected = selection()
    returned = deepcopy(producer.evaluate_reference_umbrella_bias(**selected))
    names = dict(value='cv_values', displacement='cv_displacements', **{'term-energy':'term_energies_kj_mol'})
    if change in names:
        values = list(returned[names[change]]);values[0] += .1;returned[names[change]] = values
    elif change == 'total-energy':returned['energy_kj_mol'] += .1
    elif change == 'local-derivative':returned['cv_cartesian_derivatives'][0][0,0] += .1
    elif change == 'gradient':returned['gradient_kj_mol_per_angstrom'][0,0] += .1
    else:returned['gradient_kj_mol_per_angstrom'][-1,0] = .1
    assert assess(selected, returned)['selected_bias_geometry_criteria'] == 'FALSIFIED'


def test_zero_bias_at_center_still_checks_original_cv_derivative():
    selected = selection(('DISTANCE',))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    selected = selection(('DISTANCE',), centers=(D(str(returned['cv_values'][0])),))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    assert returned['energy_kj_mol'] == 0
    returned['cv_cartesian_derivatives'][0][:] = 0
    assert assess(selected, returned)['selected_bias_geometry_criteria'] == 'FALSIFIED'


def test_geometry_limit_keeps_exact_decimal_at_binary64_boundary():
    selected = selection(('DISTANCE',),centers=(D(1),),force_constants=(D(2),))
    selected['coordinates_angstrom'] = np.array(((0.,0.,0.),(2.,0.,0.),(3.,2.,1.),(4.,4.,5.),(5.,7.,9.)))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    returned['energy_kj_mol'] += .5
    result = assess(selected,returned,maximum_energy_error_kj_mol=D('.4999999999999999999999999999'))
    assert result['energy_error_kj_mol']==.5
    assert result['selected_bias_geometry_criteria']=='FALSIFIED'


@pytest.mark.parametrize('theta', (math.pi-1e-7, -math.pi+1e-7))
def test_signed_torsion_branch_can_be_crossed_by_a_smooth_restraint_stencil(theta):
    selected = selection(('IMPROPER_DIHEDRAL',), centers=(D('3.0'),))
    selected['coordinates_angstrom'] = np.array(((1.,0.,0.), (0.,0.,0.), (0.,0.,1.),
        (math.cos(theta),math.sin(theta),1.), (5.,5.,5.)))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    assert assess(selected, returned)['selected_bias_geometry_criteria'] == 'SATISFIED'


@pytest.mark.parametrize('boundary', ('image', 'cusp', 'coincident', 'collinear', 'unresolved-step'))
def test_unresolved_geometries_cannot_pass_selected_derivative_criteria(boundary):
    kind = 'IMPROPER_DIHEDRAL' if boundary in ('cusp', 'collinear') else 'DISTANCE'
    selected = selection((kind,), centers=(D(0),))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    if boundary == 'image':
        selected['coordinates_angstrom'][:2] = ((0.,0.,0.), (8.5-1e-6,1.,0.))
    elif boundary == 'cusp':
        theta = math.pi-1e-6
        selected['coordinates_angstrom'][:4] = ((1.,0.,0.), (0.,0.,0.), (0.,0.,1.), (math.cos(theta),math.sin(theta),1.))
    elif boundary == 'coincident':selected['coordinates_angstrom'][1] = selected['coordinates_angstrom'][0]
    elif boundary == 'collinear':selected['coordinates_angstrom'][:4] = ((0.,0.,0.), (1.,0.,0.), (2.,0.,0.), (2.,1.,0.))
    if boundary in ('image', 'cusp'):
        returned = producer.evaluate_reference_umbrella_bias(**selected)
    changes = {'derivative_step_angstrom':D('1e-30')} if boundary == 'unresolved-step' else {}
    result = assess(selected, returned, **changes)
    assert result['selected_bias_geometry_criteria'] == 'UNEVALUABLE'
    assert result['terms'][0]['unresolved_geometry']
    assert result['gradient_error_kj_mol_per_angstrom'] is None


def test_finite_violation_dominates_an_unresolved_stencil():
    selected = selection(('DISTANCE',))
    selected['coordinates_angstrom'][:2] = ((0.,0.,0.), (8.5-1e-6,1.,0.))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    returned['energy_kj_mol'] += 1
    result = assess(selected, returned)
    assert result['terms'][0]['unresolved_geometry'] == 'stencil_crosses_periodic_image'
    assert result['selected_bias_geometry_criteria'] == 'FALSIFIED'


def test_step_refinement_is_an_explicit_additional_numerical_criterion():
    selected = selection(('DISTANCE',))
    returned = producer.evaluate_reference_umbrella_bias(**selected)
    result = assess(selected, returned, derivative_step_angstrom=D('.2'),
        maximum_cv_derivative_errors_per_angstrom=(D(10),), maximum_gradient_error_kj_mol_per_angstrom=D(10))
    assert result['selected_bias_geometry_criteria'] == 'FALSIFIED'
    assert result['terms'][0]['derivative_refinement_error_per_angstrom'] > 1e-5


def test_geometry_criteria_canonical_exact_identity_and_complete_tuple_limits():
    selected = selection()
    value = criteria(selected['convention'], 3)
    assert decode_canonical_bytes(value.canonical_bytes(), ReferenceBiasGeometryCriteria, maximum_bytes=8192) == value
    wrong = replace(value, convention=replace(value.convention, object_fingerprint='0'*64))
    with pytest.raises(ValueError, match='substitutes'):
        assess_reference_bias_geometry(**selected, returned=producer.evaluate_reference_umbrella_bias(**selected), criteria=wrong)
    with pytest.raises(ValueError, match='per-CV'):
        replace(value, maximum_cv_value_errors=(D(1),))


@pytest.mark.parametrize('value', (D(0), D('-1'), D('1e400'), D('1e-400'), D('NaN'), D('Infinity'), 1.0))
def test_invalid_numerical_steps_refused(value):
    with pytest.raises((ValueError, TypeError)):
        criteria(selection()['convention'], 3, derivative_step_angstrom=value)


@pytest.mark.parametrize('change', ('model', 'atoms', 'cell', 'complex', 'missing-cv', 'gradient-shape', 'nan', 'units', 'convention', 'angle'))
def test_missing_or_substituted_inputs_refused(change):
    selected = selection()
    returned = deepcopy(producer.evaluate_reference_umbrella_bias(**selected))
    if change == 'model':selected['physical_model_id'] = 'different'
    elif change == 'atoms':selected['physical_atom_ids'] = ('a','a','c','d','spectator')
    elif change == 'cell':selected['cell_vectors_angstrom'][0,1] = 1
    elif change == 'complex':selected['coordinates_angstrom'] = XYZ.astype(complex)+1j
    elif change == 'missing-cv':returned['cv_cartesian_derivatives'] = returned['cv_cartesian_derivatives'][:-1]
    elif change == 'gradient-shape':returned['gradient_kj_mol_per_angstrom'] = np.zeros((4,3))
    elif change == 'nan':returned['gradient_kj_mol_per_angstrom'][0,0] = math.nan
    elif change == 'units':returned['cv_units'] = ('ANGSTROM',)*3
    elif change == 'convention':returned['convention'] = {}
    else:returned['cv_values'] = (*returned['cv_values'][:2], 10.)
    with pytest.raises(ValueError):assess(selected, returned)
