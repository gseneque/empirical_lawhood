# SPDX-License-Identifier: MPL-2.0
"""Complete parameter-table falsifiers; no physical preparation evidence."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import read_prmtop
from empirical_lawhood.adapters.rubisco.rubisco_response import gas_topology as topology
from empirical_lawhood.domains.rubisco.rubisco_response.gas_topology_assessment import _coordinate_assignment, assess_gas_parameter_tables
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests.test_rubisco_gas_stock import _stock
from tests.test_rubisco_preparation_integrity import amber_text


FIXTURES = Path(__file__).parent/'fixtures/rubisco/gas-topology'


def _read(name, raw=None):
    return assess_gas_parameter_tables(original_topology_bytes=(FIXTURES/'host.prmtop').read_bytes(),
        augmented_topology_bytes=(FIXTURES/(name.lower()+'.prmtop')).read_bytes() if raw is None else raw,
        stock=_stock(name))


@pytest.mark.parametrize('name,count', (('CO2', 3), ('O2', 2)))
def test_complete_raw_assignment_includes_unused_slots_and_inactive_zero_scales(name, count, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('topology producer entered during independent assessment')
    monkeypatch.setattr(topology, 'append_gas_parameter_tables', forbidden)
    result = _read(name)
    assert result['original_atoms'] == 4 and result['appended_atoms'] == count
    assert result['original_host_parameters'] == 'EXACT_PRINTED_VALUES_PRESERVED'
    assert result['force_evaluations'] == 0 and not result['physical_or_chemical_admission']
    original = read_prmtop((FIXTURES/'host.prmtop').read_text())
    added = read_prmtop((FIXTURES/(name.lower()+'.prmtop')).read_text())
    assert added['SCEE_SCALE_FACTOR'] == original['SCEE_SCALE_FACTOR'] == (D('1.2'), D(0))
    assert added['BOND_FORCE_CONSTANT'][:2] == original['BOND_FORCE_CONSTANT'] == (D(310), D('123.456'))


@pytest.mark.parametrize('name', ('CO2', 'O2'))
@pytest.mark.parametrize('change', ('host-charge', 'host-mass', 'unused-host-bond', 'unused-host-scale',
    'host-lj', 'host-exclusion', 'torsion-sign', 'gas-charge', 'gas-mass', 'gas-lj',
    'gas-bond', 'gas-exclusion', 'mixed-bond', 'unused-added-parameter', 'gas-type', 'gas-count'))
def test_complete_parameter_changes_are_refused(name, change):
    raw = read_prmtop((FIXTURES/(name.lower()+'.prmtop')).read_text())
    value = {key: list(rows) for key, rows in raw.items()}
    if change == 'host-charge': value['CHARGE'][3] = D('0.1')
    elif change == 'host-mass': value['MASS'][3] = D('12.02')
    elif change == 'unused-host-bond': value['BOND_FORCE_CONSTANT'][1] = D(0)
    elif change == 'unused-host-scale': value['SCEE_SCALE_FACTOR'][1] = D(1)
    elif change == 'host-lj': value['LENNARD_JONES_ACOEF'][0] *= 2
    elif change == 'host-exclusion': value['EXCLUDED_ATOMS_LIST'][0] = 0
    elif change == 'torsion-sign': value['DIHEDRALS_WITHOUT_HYDROGEN'][2] *= -1
    elif change == 'gas-charge': value['CHARGE'][-1] = D('0.5')
    elif change == 'gas-mass': value['MASS'][-1] = D(15)
    elif change == 'gas-lj': value['LENNARD_JONES_BCOEF'][-1] = D(0)
    elif change == 'gas-bond': value['BOND_FORCE_CONSTANT'][-1] = D(0)
    elif change == 'gas-exclusion': value['EXCLUDED_ATOMS_LIST'][-1] = 1
    elif change == 'mixed-bond': value['BONDS_WITHOUT_HYDROGEN'][-3] = 0
    elif change == 'unused-added-parameter':
        value['BOND_FORCE_CONSTANT'].append(D(2))
        value['BOND_EQUIL_VALUE'].append(D(3))
        value['POINTERS'][15] += 1
    elif change == 'gas-type': value['AMBER_ATOM_TYPE'][-1] = 'CT'
    elif change == 'gas-count': value['POINTERS'][0] += 1
    with pytest.raises(ValueError):
        _read(name, amber_text(value).encode('ascii'))


def test_coordinate_binding_preserves_prep_order_and_original_source_ordinals():
    def pin(name):
        return ObjectIdentity(name, 'empirical-lawhood/software-control/source', '1.0.0', '1'*64)
    result = topology.GasTopologyAugmentation(*(pin('source.'+str(i)) for i in range(5)),
        _stock('CO2'), pin('cell.original'), pin('topology.original'), '2'*64, '3'*64,
        pin('topology.added'), pin('coordinates.added'), 17,
        (('O1', 63, 17), ('C1', 57, 18), ('O2', 64, 19)),
        ObjectIdentity('product.exposed', 'empirical-lawhood/rubisco-response/gas-parameter-unit-product', '1.0.0', '4'*64))
    assert decode_canonical_bytes(result.canonical_bytes(), topology.GasTopologyAugmentation,
        maximum_bytes=2**16) == result
    with pytest.raises(ValueError, match='correspondence'):
        replace(result, gas_atom_correspondence=(('C1', 57, 17), ('O1', 63, 18), ('O2', 64, 19)))
    with pytest.raises(ValueError, match='denominator'):
        replace(result, original_atom_count=0)


def test_gas_only_numerical_angle_change_is_not_hidden_by_printing_tolerance():
    raw = {key: list(rows) for key, rows in read_prmtop((FIXTURES/'co2.prmtop').read_text()).items()}
    raw['ANGLE_EQUIL_VALUE'][-1] = D('3.14')
    with pytest.raises(ValueError, match='angle equilibrium'):
        _read('CO2', amber_text(raw).encode('ascii'))


@pytest.mark.parametrize('name', ('CO2', 'O2'))
def test_distinct_host_names_sharing_one_original_lj_index_keep_every_pair(name):
    directory = FIXTURES/'split-host-type'
    original_raw = (directory/'host.prmtop').read_bytes()
    added_raw = (directory/(name.lower()+'.prmtop')).read_bytes()
    original = read_prmtop(original_raw.decode('ascii'))
    added = read_prmtop(added_raw.decode('ascii'))
    assert len(set(original['ATOM_TYPE_INDEX'])) == 1
    assert len(set(original['AMBER_ATOM_TYPE'])) == 2
    assert len(set(added['ATOM_TYPE_INDEX'][:4])) == 2
    arguments = dict(original_topology_bytes=original_raw, stock=_stock(name))
    assert assess_gas_parameter_tables(augmented_topology_bytes=added_raw,
        **arguments)['original_host_parameters'] == 'EXACT_PRINTED_VALUES_PRESERVED'
    # Corrupt only the newly separated CX-to-CT interaction. Checking one
    # representative atom per original type would overlook this mutation.
    changed = {key: list(rows) for key, rows in added.items()}
    first, second = (added['ATOM_TYPE_INDEX'][i]-1 for i in (0, 1))
    slot = added['NONBONDED_PARM_INDEX'][first*added['POINTERS'][1]+second]-1
    changed['LENNARD_JONES_ACOEF'][slot] *= 2
    with pytest.raises(ValueError, match='original host LJ coefficient'):
        assess_gas_parameter_tables(augmented_topology_bytes=amber_text(changed).encode('ascii'), **arguments)


def test_periodic_cell_and_complete_molecule_census_are_preserved():
    original = {key: list(rows) for key, rows in read_prmtop((FIXTURES/'host.prmtop').read_text()).items()}
    added = {key: list(rows) for key, rows in read_prmtop((FIXTURES/'o2.prmtop').read_text()).items()}
    for value, count in ((original, 1), (added, 2)):
        value['POINTERS'][27] = 1
        value['BOX_DIMENSIONS'] = [D(90), D(30), D(31), D(32)]
        value['ATOMS_PER_MOLECULE'] = [4] if count == 1 else [4, 2]
        value['SOLVENT_POINTERS'] = [0, count, 1]
    arguments = dict(original_topology_bytes=amber_text(original).encode('ascii'), stock=_stock('O2'))
    assert assess_gas_parameter_tables(augmented_topology_bytes=amber_text(added).encode('ascii'),
        **arguments)['original_atoms'] == 4
    added['BOX_DIMENSIONS'][1] = D('30.1')
    with pytest.raises(ValueError, match='periodic cell'):
        assess_gas_parameter_tables(augmented_topology_bytes=amber_text(added).encode('ascii'), **arguments)


def _coordinate_control(name):
    def pin(label, digest='1'*64):
        return ObjectIdentity(label, 'empirical-lawhood/software-control/source', '1.0.0', digest)
    host = np.array([[1., 2., 3.], [7., 8., 9.]], dtype='<f8').tobytes()
    sources = {63: (0., 1., 0.), 57: (0., 0., 0.), 64: (0., -1., 0.)} if name == 'CO2' else {
        162: (0., 0., 0.), 168: (0., 1.15, 0.)}
    pairs = (('O1', 63), ('C1', 57), ('O2', 64)) if name == 'CO2' else (('O1', 162), ('O2', 168))
    raw = host+np.array([sources[ordinal] for _, ordinal in pairs], dtype='<f8').tobytes()
    result = topology.GasTopologyAugmentation(*(pin('source.'+str(i)) for i in range(5)),
        _stock(name), pin('cell.original'), pin('topology.original'), '2'*64, sha256(host).hexdigest(),
        pin('topology.added'), pin('coordinates.added', sha256(raw).hexdigest()), 2,
        tuple((label, ordinal, i+2) for i, (label, ordinal) in enumerate(pairs)),
        ObjectIdentity('product.exposed', 'empirical-lawhood/rubisco-response/gas-parameter-unit-product', '1.0.0', '4'*64))
    return result, raw, host, sources


@pytest.mark.parametrize('name', ('CO2', 'O2'))
def test_original_coordinate_prefix_and_named_gas_positions_are_independently_checked(name):
    result, raw, host, sources = _coordinate_control(name)
    assert _coordinate_assignment(result=result, augmented_coordinate_bytes=raw,
        host_prefix=host, original_gas=sources) == len(sources)


@pytest.mark.parametrize('name', ('CO2', 'O2'))
@pytest.mark.parametrize('change', ('host-position', 'gas-order', 'truncated', 'extra-atom', 'nonfinite', 'missing-source', 'old-digest'))
def test_coordinate_corruption_is_refused_even_with_updated_payload_digest(name, change):
    result, raw, host, sources = _coordinate_control(name)
    points = np.frombuffer(raw, dtype='<f8').copy().reshape((-1, 3))
    if change == 'host-position': points[1, 1] += .01
    elif change == 'gas-order': points[[2, 3]] = points[[3, 2]]
    elif change == 'truncated': points = points[:-1]
    elif change == 'extra-atom': points = np.vstack((points, [[0., 0., 0.]]))
    elif change == 'nonfinite': points[-1, 1] = float('nan')
    elif change == 'missing-source': sources.pop(next(iter(sources)))
    elif change == 'old-digest': points[-1, 0] += .01
    raw = points.astype('<f8').tobytes()
    if change != 'old-digest':
        result = replace(result, augmented_coordinates=replace(result.augmented_coordinates,
            object_fingerprint=sha256(raw).hexdigest()))
    with pytest.raises(ValueError):
        _coordinate_assignment(result=result, augmented_coordinate_bytes=raw,
            host_prefix=host, original_gas=sources)
