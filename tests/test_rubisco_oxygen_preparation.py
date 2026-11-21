# SPDX-License-Identifier: MPL-2.0
"""Disclosed arithmetic/grammar controls; no original paper geometry fixture."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import oxygen_source_geometry as source
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import assess_gas_encounter, fit_gas_encounter, fit_oxygen_encounter, selected_gas_free_target


def test_text_grammar_retains_tokens_page_boundaries_and_state_order():
    text = ('Preamble\nOptimized coordinates\nSyn pathway\n3\nSynthetic state\n'
            'C -0.0000 1.0000 2.0000\n\f S10\n\nO 1.2340 2.3450 3.4560\nH 2.0 3.0 4.0\n')
    rows = source._read_geometry_blocks(text)
    assert rows[0][:2] == ('Syn pathway', 'Synthetic state')
    assert rows[0][2][0].coordinate_tokens == ('-0.0000', '1.0000', '2.0000')
    assert rows[0][2][1].coordinate_tokens == ('1.2340', '2.3450', '3.4560')


@pytest.mark.parametrize('suffix', (
    'C 0.0 1.0 2.0\n',
    'C 0.0 1.0 2.0\n2\nnext\n',
    'C 0.0 NaN 2.0\nO 0.0 1.0 2.0\n',
    'C 0.0 1.0 2.0\nO 0.0 1.0 2.0\nO 1.0 2.0 3.0\n',
))
def test_text_grammar_refuses_missing_extra_and_nonfinite_atoms(suffix):
    with pytest.raises(ValueError):
        source._read_geometry_blocks('Optimized coordinates\nSyn pathway\n2\nSynthetic\n'+suffix)


def test_source_admission_refuses_unmatched_original_and_preserves_full_census(monkeypatch):
    with pytest.raises(ValueError, match='original SI'):
        source.prepare_oxygen_source_projection(original_pdf_bytes=b'fake', extracted_text_bytes=b'fake')
    # Explicitly disclosed synthetic pins test the public join without shipping
    # copyrighted coordinate data or presenting these bytes as physical evidence.
    atom = source.GeometryAtomV1('C', ('0.0', '1.0', '2.0'))
    pins = tuple(('Syn pathway', 'Synthetic', n, source.native_atom_projection_sha256((atom,)*n))
        for n in (248,)*23+(290,))
    monkeypatch.setattr(source, 'PDF_BYTES', 4)
    monkeypatch.setattr(source, 'PDF_SHA256', sha256(b'fake').hexdigest())
    monkeypatch.setattr(source, 'GEOMETRY_PINS', pins)
    # Default values in the immutable type deliberately stay on the original
    # witness. Test the text/token join separately, not a false original object.
    with pytest.raises(ValueError, match='original witness'):
        source.OxygenSourceProjection(tuple(source.OxygenSourceGeometry(i, p, label, (atom,)*n)
            for i, (p, label, n, _) in enumerate(pins, 1)), '0'*64, 100)
    geometry = source.OxygenSourceGeometry(1, 'Syn pathway', 'Synthetic', (atom,)*248)
    with pytest.raises(ValueError, match='exact native tokens'):
        replace(geometry, atoms=(replace(atom, coordinate_tokens=('0.00','1.0','2.0')),)+(atom,)*247)


def _operands():
    anchors = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.],[.2,.3,1.]])
    gas = np.array([[2.,3.,4.],[3.,3.,4.]])
    return anchors, gas


def test_transfer_preserves_known_proper_rotation_and_complete_contact_census():
    anchors, gas = _operands()
    rotation = np.array([[0.,1.,0.],[-1.,0.,0.],[0.,0.,1.]])
    translation = np.array([7.,8.,9.])
    target = anchors @ rotation + translation
    expected = gas @ rotation + translation
    environment = np.vstack((target, expected[0]+[.2,0.,0.], expected[0]+[.1,0.,0.]))
    result = fit_oxygen_encounter(source_anchors=anchors,target_anchors=target,source_gas=gas,
        environment=environment,atomic_numbers=(6,6,8,8,12,8,1),box=(100,100,100))
    r, t, rmsd, residuals, actual, contacts = result
    np.testing.assert_allclose(r,rotation,atol=1e-14)
    np.testing.assert_allclose(t,translation,atol=1e-14)
    np.testing.assert_allclose(actual,expected,atol=1e-14)
    assert rmsd < 1e-14 and max(residuals) < 1e-14
    assert contacts[0][0] == 6 and contacts[0][2] == 5
    assert abs(contacts[0][1]-Decimal('.1')) < Decimal('1e-13')
    assert abs(contacts[0][3]-Decimal('.2')) < Decimal('1e-13')


def test_contacts_use_periodic_images_and_include_the_last_environment_atom():
    anchors, gas = _operands()
    environment = np.vstack((anchors, gas[1]+[10.1,0.,0.]))
    result = fit_oxygen_encounter(source_anchors=anchors,target_anchors=anchors,source_gas=gas,
        environment=environment,atomic_numbers=(6,6,8,8,12,8),box=(10,10,10))
    contacts = result[-1]
    assert contacts[1][0] == contacts[1][2] == len(environment)-1
    assert abs(contacts[1][1]-Decimal('.1')) < Decimal('1e-13')


def test_reflection_is_not_accepted_as_a_proper_rotation_and_degenerate_fit_refuses():
    anchors, gas = _operands()
    reflected = anchors*np.array([-1,1,1])
    result = fit_oxygen_encounter(source_anchors=anchors,target_anchors=reflected,source_gas=gas,
        environment=reflected,atomic_numbers=(6,6,8,8,12),box=(20,20,20))
    assert np.linalg.det(result[0]) == pytest.approx(1)
    assert result[2] > .1
    with pytest.raises(ValueError, match='collinear'):
        fit_oxygen_encounter(source_anchors=anchors*0,target_anchors=anchors,source_gas=gas,
            environment=anchors,atomic_numbers=(6,6,8,8,12),box=(20,20,20))


def _independent_case():
    anchors, gas = _operands()
    target = anchors+2
    operands = dict(source_anchors=anchors, target_anchors=target, source_gas=gas,
        environment=np.vstack((target, gas[1]+[12.1,2,2])), atomic_numbers=(6,6,8,8,12,8), box=(10,10,10))
    return operands, fit_gas_encounter(**operands)


def test_independent_assessor_does_not_call_the_fit_or_nearest_contact_producer(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import oxygen_encounter as geometry
    operands, observation = _independent_case()
    def forbidden(*args, **kwargs):
        raise AssertionError('producer called by independent assessment')
    monkeypatch.setattr(geometry, 'proper_rigid_fit', forbidden)
    monkeypatch.setattr(geometry, 'fit_gas_encounter', forbidden)
    monkeypatch.setattr(geometry, 'minimum_image', forbidden)
    read = assess_gas_encounter(observation=observation, **operands)
    assert read['inspected_gas_environment_pairs'] == 12
    assert not read['physical_or_chemical_admission']


@pytest.mark.parametrize('changed', ('rotation', 'translation', 'rmsd', 'residual', 'gas', 'contact-index', 'contact-distance'))
def test_independent_assessor_refuses_changed_transform_or_contact(changed):
    operands, observation = _independent_case()
    r, t, rmsd, residuals, gas, contacts = observation
    if changed == 'rotation':
        r = r*np.array([-1,1,1])
    elif changed == 'translation':
        t = t+.01
    elif changed == 'rmsd':
        rmsd += .01
    elif changed == 'residual':
        residuals = residuals+.01
    elif changed == 'gas':
        gas = gas+.01
    else:
        first, *rest = contacts
        index, distance, heavy, heavy_distance = first
        first = ((index+1) % 6 if changed == 'contact-index' else index,
            distance+Decimal('.01') if changed == 'contact-distance' else distance, heavy, heavy_distance)
        contacts = (first, *rest)
    with pytest.raises(ValueError):
        assess_gas_encounter(observation=(r,t,rmsd,residuals,gas,contacts), **operands)


def test_shared_three_atom_transfer_keeps_oxygen_two_atom_contract():
    operands, _ = _independent_case()
    operands['source_gas'] = np.vstack((operands['source_gas'], [4,3,4]))
    with pytest.raises(ValueError, match='two source gas atoms'):
        fit_oxygen_encounter(**operands)
    observation = fit_gas_encounter(**operands)
    assert assess_gas_encounter(observation=observation, **operands)['inspected_gas_environment_pairs'] == 18


@pytest.fixture(scope='module')
def full_target(tmp_path_factory):
    from tests.rubisco_active_fixture import prepared_control
    from tests.test_rubisco_periodic_probe_operation import engine
    stock = engine(tmp_path_factory.mktemp('exposed-gas-target')/'stock')
    model, prototype, preparation, _, _, coordinates = prepared_control('m1-wt', stock)
    return dict(representation=model, preparation=preparation,
        coordinate_bytes=coordinates, cell=prototype.cell)


def _target_seed(full_target, state='reactive-enolate-kcxh-hie', water='UNOCCUPIED'):
    preparation = full_target['preparation']
    site = preparation.sites[0]
    return next(s for s in preparation.seeds if s.site == site.identity
        and (s.state_label, s.water_occupancy) == (state, water))


@pytest.mark.parametrize('state,water', (
    ('initial-enolate-kcxh-hie', 'AS_CONSTRUCTED'),
    ('reactive-enolate-kcxh-hie', 'UNOCCUPIED'),
))
def test_selected_gas_target_retains_complete_original_seed_overlay(full_target, state, water):
    seed = _target_seed(full_target, state, water)
    site, targets, operands = selected_gas_free_target(seed=seed, **full_target)
    expected = np.frombuffer(full_target['coordinate_bytes'], dtype='<f8').reshape(-1, 3).copy()
    for change in seed.coordinate_changes:
        expected[change.atom_index] = tuple(map(float, change.after_angstrom))
    assert seed.coordinate_changes and site.identity == seed.site
    np.testing.assert_array_equal(operands['environment'], expected)
    assert tuple(full_target['representation'].atoms[i].name for i in targets) == ('C2', 'C3', 'O2', 'O3', 'MG')
    assert len(operands['atomic_numbers']) == seed.physical_atom_count
    assert len(full_target['preparation'].seeds) == 96


@pytest.mark.parametrize('state,water', (
    ('keto-hie', 'AS_CONSTRUCTED'),
    ('reactive-enolate-kcxh-hie', 'OCCUPIED'),
))
def test_gas_target_refuses_unselected_original_chemical_alternatives(full_target, state, water):
    with pytest.raises(ValueError, match='enolate'):
        selected_gas_free_target(seed=_target_seed(full_target, state, water), **full_target)


@pytest.mark.parametrize('changed', ('membership', 'original-array', 'expanded-array', 'cell'))
def test_gas_target_refuses_changed_seed_geometry_and_original_bindings(full_target, changed):
    values = dict(full_target)
    seed = _target_seed(full_target)
    if changed == 'membership':
        seed = replace(seed, seed_id='seed.exposed.unbound')
    elif changed == 'original-array':
        xyz = np.frombuffer(values['coordinate_bytes'], dtype='<f8').copy()
        xyz[-1] += .01
        values['coordinate_bytes'] = xyz.tobytes()
    elif changed == 'cell':
        values['cell'] = replace(values['cell'], raw_coordinates=values['cell'].raw_topology)
    else:
        changed_seed = replace(seed, expanded_coordinate_sha256='0'*64)
        preparation = values['preparation']
        values['preparation'] = replace(preparation,
            seeds=tuple(changed_seed if s == seed else s for s in preparation.seeds),
            assessments=tuple(replace(a, seed=changed_seed.identity) if a.seed == seed.identity else a
                for a in preparation.assessments))
        seed = changed_seed
    with pytest.raises(ValueError):
        selected_gas_free_target(seed=seed, **values)
