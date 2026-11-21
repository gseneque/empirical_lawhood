# SPDX-License-Identifier: MPL-2.0
"""Exposed full-census and electronic-conservation controls, no physical evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import gas_reactive_model as owner
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import prepare_catalytic_sites
from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import GasTopologyAugmentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import prepare_raw_sources
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import read_amber_periodic_cell
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests.rubisco_active_fixture import molecular_control
from tests.rubisco_response_molecular_fixture import raw_identity
from tests.test_rubisco_gas_stock import _stock
from tests.test_rubisco_periodic_probe_operation import engine
from tests.test_rubisco_preparation_integrity import amber_text, topology


def _sources(values):
    return tuple(sorted(set(values), key=lambda r: r.object_id))


def _topology(model, gas=None):
    """Explicit atom-table fixture; its arbitrary forces are never evaluated."""
    n = len(model.atoms)
    result = topology()
    residue_by_id = {r.residue_id: r for r in model.residues}
    starts = [i for i, a in enumerate(model.atoms) if i == 0 or a.residue_id != model.atoms[i-1].residue_id]
    result.update(ATOM_NAME=[a.name for a in model.atoms], AMBER_ATOM_TYPE=['CT']*n,
        ATOMIC_NUMBER=[a.atomic_number for a in model.atoms], MASS=[a.mass_dalton for a in model.atoms],
        CHARGE=[a.charge_native for a in model.atoms], ATOM_TYPE_INDEX=[1]*n,
        RESIDUE_LABEL=[residue_by_id[model.atoms[i].residue_id].component for i in starts],
        RESIDUE_POINTER=[i+1 for i in starts], NUMBER_EXCLUDED_ATOMS=[1]*n, EXCLUDED_ATOMS_LIST=[0]*n,
        BONDS_INC_HYDROGEN=[], BONDS_WITHOUT_HYDROGEN=[v for b in model.bonds for v in (b.first*3, b.second*3, 1)],
        BOX_DIMENSIONS=[D(90), D(1000), D(1000), D(1000)],
        HBOND_ACOEF=[], HBOND_BCOEF=[], HBCUT=[])
    result['POINTERS'][0] = n
    result['POINTERS'][2] = 0
    result['POINTERS'][3] = len(model.bonds)
    result['POINTERS'][10] = n
    result['POINTERS'][11] = len(starts)
    result['POINTERS'][27] = 1
    if gas:
        count = 3 if gas == 'CO2' else 2
        gas_table = owner.read_prmtop((Path(__file__).parent/'fixtures/rubisco/gas-topology'/(gas.lower()+'.prmtop')).read_text())
        for name in ('ATOM_NAME', 'AMBER_ATOM_TYPE', 'ATOMIC_NUMBER', 'MASS', 'CHARGE'):
            result[name].extend(gas_table[name][-count:])
        result['ATOM_TYPE_INDEX'].extend([1]*count)
        result['NUMBER_EXCLUDED_ATOMS'].extend([1]*count)
        result['EXCLUDED_ATOMS_LIST'].extend([0]*count)
        result['RESIDUE_LABEL'].append(gas)
        result['RESIDUE_POINTER'].append(n+1)
        for i in range(count-1):
            result['BONDS_WITHOUT_HYDROGEN'].extend((3*(n+i), 3*(n+i+1), 1))
        result['POINTERS'][0] += count
        result['POINTERS'][3] += count-1
        result['POINTERS'][10] += count
        result['POINTERS'][11] += 1
    return amber_text(result).encode('ascii')


def _prepared_host(tmp_path_factory, name):
    original, old_path, _, electronic, molecular, _, raw_xyz, coordinates, protocol = molecular_control(name)
    raw_top = _topology(original)
    top = raw_identity('source.exposed.gas-host.'+name, raw_top)
    model = replace(original, representation_id='molecular.exposed.gas-host.'+name, raw_topology=top,
        atoms=tuple(replace(a, parameter_type='CT') for a in original.atoms),
        arrays=replace(original.arrays, scientific_references=_sources((top, original.raw_coordinates))),
        sources=_sources((*original.sources, top)))
    path = replace(old_path, representation=model.identity, sources=_sources((*old_path.sources, *model.sources, model.identity)))
    cell = read_amber_periodic_cell(model, raw_top, raw_xyz)
    stock = engine(tmp_path_factory.mktemp('exposed-gas-engine')/'stock')
    prototype = prepare_periodic_probe_selection(representation=model, path=path, cell=cell,
        electronic=electronic, molecular=molecular, engine=stock)
    site = prepare_catalytic_sites(representation=model, prototype=prototype,
        coordinate_bytes=coordinates, protocol=protocol)[0]
    return model, site, cell, coordinates, prototype


@pytest.fixture(scope='module')
def host(tmp_path_factory):
    return _prepared_host(tmp_path_factory, 'm1-wt')


@pytest.fixture(scope='module')
def mutant_host(tmp_path_factory):
    return _prepared_host(tmp_path_factory, 'm1-i95m')


def operands(host, gas):
    model, site, cell, coordinates, prototype = host
    top = _topology(model, gas)
    points = ((1.123456789, 2.1, 3.), (2.1, 3.123456789, 4.))
    if gas == 'CO2':
        points += ((3.1, 4., 5.),)
    raw = coordinates+np.asarray(points, dtype='<f8').tobytes()
    pin = model.material.sources[0]
    n = len(model.atoms)
    mapping = (('O1', 63, n), ('C1', 57, n+1), ('O2', 64, n+2)) if gas == 'CO2' else (('O1', 162, n), ('O2', 168, n+1))
    augmentation = GasTopologyAugmentation(model.identity, pin, pin, site.identity, pin, _stock(gas),
        cell.identity, model.raw_topology, sha256(coordinates).hexdigest(), sha256(coordinates).hexdigest(),
        raw_identity('source.exposed.gas-topology.'+gas.lower(), top), raw_identity('source.exposed.gas-array.'+gas.lower(), raw),
        n, mapping, ObjectIdentity('product.exposed.gas.'+gas.lower(),
            'empirical-lawhood/rubisco-response/gas-parameter-unit-product', '1.0.0', '4'*64))
    return dict(representation=model, prepared_site=site, original_cell=cell, augmentation=augmentation,
        augmented_topology_bytes=top, augmented_coordinate_bytes=raw,
        electronic_settings=replace(prototype.electronic, settings_id='settings.exposed.'+gas.lower(),
            ks_flavour='RKS' if gas == 'CO2' else 'UKS'))


@pytest.mark.parametrize('gas,multiplicity,electrons_added', (('CO2', 1, 22), ('O2', 3, 16)))
def test_complete_gas_mapping_preserves_host_and_enters_existing_probe_inputs(host, gas, multiplicity, electrons_added, monkeypatch):
    values = operands(host, gas)
    result = owner.prepare_gas_reactive_candidate(**values)
    def forbidden(**kwargs):
        pytest.fail('model constructor replayed during independent read')
    monkeypatch.setattr(owner, 'prepare_gas_reactive_candidate', forbidden)
    monkeypatch.setattr(owner, 'encode_gas_amber_coordinates', forbidden)
    report = owner.assess_gas_reactive_candidate(candidate=result, **values)
    original, site, _, original_bytes, prototype = host
    assert values['augmented_coordinate_bytes'][:len(original_bytes)] == original_bytes
    assert result['representation'].atoms[:len(original.atoms)] == original.atoms
    assert result['path'].mm_atom_indices == site.path.mm_atom_indices
    assert result['path'].boundaries == site.path.boundaries
    before_electrons = sum(original.atoms[i].atomic_number for i in site.path.qm_atom_indices)+len(site.path.boundaries)-site.path.qm_formal_charge
    assert report['qm_electrons'] == before_electrons+electrons_added
    assert report['formal_charge'] == -2 and report['spin_multiplicity'] == multiplicity
    assert report['native_calls'] == 0 and not report['physical_or_chemical_admission']
    assert ('requirement.reactive.oxygenation-assumption' in report['required']) == (gas == 'O2')
    for name in ('encoding', 'electronic_selection', 'convention'):
        value = result[name]
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=2**20) == value
    selected = prepare_periodic_probe_selection(representation=result['representation'], path=result['path'],
        cell=result['cell'], electronic=result['electronic_settings'], molecular=prototype.molecular, engine=prototype.engine)
    retained = prepare_raw_sources(selected, values['augmented_topology_bytes'], result['raw_coordinate_bytes'])
    assert retained.coordinates_utf8.encode('ascii') == result['raw_coordinate_bytes']


@pytest.mark.parametrize('changed', ('host-atom', 'mm-partition', 'focal-site', 'coordinate-loss',
    'missing-requirement', 'convention', 'gas-residue'))
def test_independent_reader_refuses_changed_host_partition_and_disclosed_loss(host, changed):
    values = operands(host, 'O2')
    candidate = owner.prepare_gas_reactive_candidate(**values)
    if changed == 'host-atom':
        model = candidate['representation']
        candidate['representation'] = replace(model, atoms=(*model.atoms[:1],
            replace(model.atoms[1], charge_native=D('0.1')), *model.atoms[2:]))
    elif changed == 'coordinate-loss':
        candidate['encoding'] = replace(candidate['encoding'], maximum_binary64_change_angstrom=D('0.01'))
    elif changed == 'missing-requirement':
        candidate['required'] = ()
    elif changed == 'convention':
        candidate['convention'] = replace(candidate['convention'], host_parameter_model=values['representation'].raw_coordinates)
    elif changed == 'gas-residue':
        model = candidate['representation']
        old, = (r for r in model.residues if r.role == 'GAS')
        renamed = 'residue.exposed.changed-gas'
        candidate['representation'] = replace(model,
            residues=tuple(sorted((replace(r, residue_id=renamed) if r == old else r for r in model.residues), key=lambda r:r.residue_id)),
            atoms=tuple(replace(a, residue_id=renamed) if a.residue_id == old.residue_id else a for a in model.atoms))
    elif changed == 'focal-site':
        site = values['prepared_site']
        path = replace(site.path, selection_id='path.changed-site-label')
        values['prepared_site'] = replace(site, path=path, sources=_sources((*site.sources, path.identity)))
    else:
        path = candidate['path']
        move = path.mm_atom_indices[-1]
        candidate['path'] = replace(path, qm_atom_indices=tuple(sorted((*path.qm_atom_indices, move))),
            mm_atom_indices=path.mm_atom_indices[:-1])
    with pytest.raises(ValueError):
        owner.assess_gas_reactive_candidate(candidate=candidate, **values)


def test_coordinate_serialization_is_explicit_and_decimal_context_independent(host):
    values = operands(host, 'CO2')
    arguments = dict(augmentation=values['augmentation'], coordinate_bytes=values['augmented_coordinate_bytes'], original_cell=values['original_cell'])
    expected = owner.encode_gas_amber_coordinates(**arguments)
    with localcontext() as context:
        context.prec = 9
        actual = owner.encode_gas_amber_coordinates(**arguments)
    assert actual == expected
    raw, data, _, encoding = actual
    assert b'1.1234568' in raw and data != values['augmented_coordinate_bytes']
    assert encoding.changed_binary64_components == 2
    assert encoding.maximum_printing_error_angstrom <= D('0.00000005')
    assert encoding.maximum_binary64_change_angstrom > D('0.00000001')
    corrupted = bytearray(arguments['coordinate_bytes']); corrupted[-1] ^= 1
    with pytest.raises(ValueError, match='exact original array'):
        owner.encode_gas_amber_coordinates(**(arguments | {'coordinate_bytes': bytes(corrupted)}))


def test_triplet_oxygen_rejects_the_carbon_restricted_settings_before_model_mapping(host):
    values = operands(host, 'O2')
    values['electronic_settings'] = replace(values['electronic_settings'], ks_flavour='RKS')
    with pytest.raises(ValueError, match='explicitly selected unrestricted'):
        owner.prepare_gas_reactive_candidate(**values)


@pytest.mark.parametrize('changes', ({'gas_formal_charge': -1}, {'total_formal_charge': -3},
    {'total_multiplicity': 1}, {'host_multiplicity': 3}, {'gas_multiplicity': 1}))
def test_neutral_oxygen_record_cannot_be_relabelled_as_a_charge_transfer_or_singlet_state(host, changes):
    value = owner.prepare_gas_reactive_candidate(**operands(host, 'O2'))['electronic_selection']
    with pytest.raises(ValueError, match='neutral gas candidate'):
        replace(value, **changes)


@pytest.mark.parametrize('gas', ('CO2', 'O2'))
def test_paired_gas_candidates_retain_common_atoms_and_selected_parameter_convention(host, mutant_host, gas):
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import paired_case
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import derive_atomic_transformation
    left = owner.prepare_gas_reactive_candidate(**operands(host, gas))
    right = owner.prepare_gas_reactive_candidate(**operands(mutant_host, gas))
    before, after = left['representation'], right['representation']
    assert left['convention'] == right['convention']
    assert before.raw_topology != after.raw_topology
    case = paired_case(case_id='case.exposed.gas.'+gas.lower(), parent=before.material, mutant=after.material,
        case_role='CANDIDATE', exposure_group='exposed.gas-atom-correspondence', sources=before.material.sources)
    by_key = {(a.residue_id, a.name, a.atomic_number):i for i, a in enumerate(after.atoms)}
    common = tuple((i, by_key[key]) for i, a in enumerate(before.atoms)
        if (key := (a.residue_id, a.name, a.atomic_number)) in by_key)
    convention = left['convention'].identity
    change = derive_atomic_transformation(before, after, transformation_id='transformation.exposed.gas.'+gas.lower(),
        kind='FINITE_SEQUENCE_SUBSTITUTION', common_atoms=common, protocol=convention,
        sources=_sources((convention, before.identity, after.identity)), case=case)
    gas_pairs = tuple(zip(left['path'].gas_atom_indices, right['path'].gas_atom_indices, strict=True))
    assert all(i != j for i, j in gas_pairs)
    assert set(gas_pairs).issubset(change.common_atoms)
    assert not set(left['path'].gas_atom_indices).intersection(change.removed_atom_indices)
    assert not set(right['path'].gas_atom_indices).intersection(change.added_atom_indices)
    assert len(case.substitutions) == 8 and change.removed_atom_indices
