# SPDX-License-Identifier: MPL-2.0
"""Exposed source/construction conformance copies; no retained scientific attempt."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from decimal import Context, Decimal, ROUND_DOWN, localcontext
import gzip
from hashlib import sha256
import io
import json
from math import sqrt
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_coupled_preparation as rr


FIXTURE = Path(__file__).parent / 'fixtures/rubisco/rr_coupled'
ARCHIVE_SHA = 'd1942a3aecd4f629d1ea8dd593f4eed00b0d34da70307e3749a766b26e7e6c98'
PROTOCOL_SHA = '00db4578dc01e1e4f53b978f332e54f04e1c80b27493d7c5e3e24266d7ebcb69'


@pytest.fixture(scope='module')
def operands():
    raw = (FIXTURE / 'source-operands.tar.gz').read_bytes()
    assert len(raw) == 1118756 and sha256(raw).hexdigest() == ARCHIVE_SHA
    expanded = gzip.decompress(raw)
    assert len(expanded) == 6000640 < 16 * 1024**2
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as archive:
        rows = archive.getmembers()
        assert len(rows) == 7 and all(m.isfile() and m.mtime == 0 for m in rows)
        result = {m.name: archive.extractfile(m).read() for m in rows}
    assert len(result) == 7
    for name, size, digest in rr.SOURCE_BINDINGS:
        assert len(result[name]) == size and sha256(result[name]).hexdigest() == digest
    return tuple(result[n] for n, _, _ in rr.SOURCE_BINDINGS)


def admit(values):
    return rr.decode_rr_coupled_source(*values[:4], values[4:])


@pytest.fixture(scope='module')
def source(operands):
    return admit(operands)


@pytest.fixture(scope='module')
def contexts(source):
    # Exactly six exposed software copies, after the protocol freeze. No effects,
    # source reacquisition, actual scientific packet, engine or endpoint labels.
    assert rr.PROTOCOL_SHA256 == PROTOCOL_SHA
    return {(v, p): rr.construct_rr_initial_context(source, variant=v, proton_view=p)
            for v in rr.VARIANTS for p in rr.PROTON_VIEWS}


def test_source_complete_native_rows_donors_and_deep_immutability(source, operands):
    core = json.loads(operands[0]); donors = json.loads(operands[1])
    assert len(source.atoms) == 13828 and len(source.native_bond_rows) == 13994
    assert len(source.donor_census) == 30
    assert tuple((r['chain'], r['author_residue'], r['residue_index'])
                 for r in donors['complete_eligible_roster']) == source.donor_census
    for atom, row in zip(source.atoms, core['atoms'], strict=True):
        assert atom.coordinates == tuple(Decimal(t) for t in row[10:13])
        assert atom.coordinate_tokens == tuple(row[10:13])
        assert atom.element == row[3]
        assert atom.index == row[0]
    assert Counter(a.element for a in source.atoms)['H'] == 6782
    assert sum(a.native_witness is not None for a in source.atoms) == 7028
    assert dict(source.donor_atom_indices)['A'] == tuple(range(115, 129))
    assert dict(source.donor_atom_indices)['B'] == tuple(range(7029, 7043))
    with pytest.raises(FrozenInstanceError):
        source.atoms = ()
    with pytest.raises(ValueError, match='init=False'):
        replace(source, atoms=())
    assert all(type(a.native_tokens) is tuple and (a.native_witness is None or type(a.native_witness) is tuple)
               for a in source.atoms)


def test_hash_first_full_roster_and_decimal_context_admission(operands, monkeypatch):
    with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
        other = admit(operands)
    assert len(other.atoms) == 13828
    def forbidden(raw):
        raise AssertionError('JSON parser entered before source seal')
    monkeypatch.setattr(rr, '_json', forbidden)
    for i in range(7):
        changed = list(operands); changed[i] = changed[i][:-1] + b'!'
        with pytest.raises(ValueError, match='pinned coupled source bytes differ'):
            admit(tuple(changed))
    with pytest.raises(ValueError, match='complete ordered'):
        rr.decode_rr_coupled_source(*operands[:4], operands[4:6])
    with pytest.raises(ValueError, match='byte type/bound'):
        rr.decode_rr_coupled_source(bytearray(operands[0]), *operands[1:4], operands[4:])


def coherent_software_pin_change(monkeypatch, operands, alter):
    """Deliberately replace ONLY software-fixture seals to test deeper joins."""
    values = list(operands); core = json.loads(values[0]); alter(core)
    values[0] = json.dumps(core, separators=(',', ':')).encode()
    core_sha = sha256(values[0]).hexdigest()
    donors = json.loads(values[1]); donors['source_projection_sha256'] = core_sha
    values[1] = json.dumps(donors, separators=(',', ':')).encode()
    register = json.loads(values[2])
    for member in register['registered_members_excluding_self']:
        if member['name'] in (rr.SOURCE_BINDINGS[0][0], rr.SOURCE_BINDINGS[1][0]):
            index = 0 if member['name'] == rr.SOURCE_BINDINGS[0][0] else 1
            member['bytes'] = len(values[index]); member['sha256'] = sha256(values[index]).hexdigest()
    values[2] = json.dumps(register, separators=(',', ':')).encode()
    pins = tuple((n, len(value), sha256(value).hexdigest()) for (n, _, _), value in zip(rr.SOURCE_BINDINGS, values, strict=True))
    monkeypatch.setattr(rr, 'SOURCE_BINDINGS', pins)
    return tuple(values)


@pytest.mark.parametrize('defect,message', [
    ('coordinate', 'translated coordinates'), ('duplicate-id', 'atom index/residue'),
    ('source-charge', 'scaled-charge'), ('source-bond', 'bond source join'),
])
def test_independent_source_joins_refuse_coherently_resealed_software_fixture(operands, monkeypatch, defect, message):
    def alter(core):
        if defect == 'coordinate':
            core['atoms'][0][10] = '  57.4521370'
        elif defect == 'duplicate-id':
            core['atoms'][1][0] = core['atoms'][0][0]
        elif defect == 'source-charge':
            core['atoms'][0][9] = '0.00000'
        else:
            core['bonds'][0][4] = '21'
    changed = coherent_software_pin_change(monkeypatch, operands, alter)
    with pytest.raises(ValueError, match=message):
        admit(changed)


def test_proper_rotation_independent_hand_arithmetic_and_reflection_refusal():
    donor = rr.proper_frame((0., 0., 0.), (2., 0., 0.), (1., 3., 0.))
    target = rr.proper_frame((10., 20., 30.), (10., 22., 30.), (7., 21., 30.))
    assert donor == ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    # Hand rotation sends +x to +y, +y to -x and preserves +z.
    point = rr.transplant_point((2., 3., 4.), (0., 0., 0.), donor, (10., 20., 30.), target)
    assert point == (7., 22., 34.)
    assert rr.distance(point, (10., 20., 30.)) == pytest.approx(sqrt(29))
    reflected = (donor[0], donor[1], (0., 0., -1.))
    with pytest.raises(ValueError, match='right-handed'):
        rr.transplant_point((1., 1., 1.), (0., 0., 0.), reflected, (0., 0., 0.), donor)
    with pytest.raises(ValueError, match='degenerate'):
        rr.proper_frame((0., 0., 0.), (1., 0., 0.), (2., 0., 0.))


def test_histidine_outward_bisector_proton_placement_and_zero_refusals():
    h = rr.place_histidine_proton((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    assert h == pytest.approx((-1.01 / sqrt(2), -1.01 / sqrt(2), 0.))
    assert rr.distance(h, (0., 0., 0.)) == pytest.approx(1.01)
    assert rr.place_toward((1., 2., 3.), (1., 2., 5.), bond_length=.97) == pytest.approx((1., 2., 3.97))
    with pytest.raises(ValueError, match='degenerate'):
        rr.place_histidine_proton((0., 0., 0.), (1., 0., 0.), (-1., 0., 0.))
    with pytest.raises(ValueError, match='degenerate'):
        rr.place_toward((0., 0., 0.), (0., 0., 0.), bond_length=.97)
    with pytest.raises(ValueError, match='nonfinite'):
        rr.place_histidine_proton((float('nan'), 0., 0.), (1., 0., 0.), (0., 1., 0.))


def ideal_enolate(*, trans=False, nonplanar=0., distance=1.35):
    h = sqrt(3) / 2
    return (('C1', (-.5, -h, nonplanar)), ('C2', (0., 0., 0.)),
            ('C3', (distance, 0., 0.)), ('C4', (distance + .5, -h, 0.)),
            ('O2', (-.5, h, 0.)), ('O3', (distance + .5, -h if trans else h, 0.)))


def test_enolate_independent_cis_trans_six_angles_plane_and_degeneracy():
    cis = rr.enolate_geometry(ideal_enolate())
    assert cis.passed and cis.c2_c3_angstrom == 1.35
    assert len(cis.trigonal_angles_degrees) == 6
    assert all(v == pytest.approx(120) for _, v in cis.trigonal_angles_degrees)
    assert max(abs(v) for _, v in cis.plane_displacements_angstrom) == 0
    assert cis.signed_o2_c2_c3_o3_dihedral_degrees == 0
    assert cis.cis_projected_dot_angstrom_squared == pytest.approx(.75)
    trans = rr.enolate_geometry(ideal_enolate(trans=True))
    assert trans.cis_projected_dot_angstrom_squared < 0 and 'not-cis-by-positive-projected-dot' in trans.failures
    assert abs(trans.signed_o2_c2_c3_o3_dihedral_degrees) == 180
    assert 'local-plane-displacement-above-0.20-A' in rr.enolate_geometry(ideal_enolate(nonplanar=.21)).failures
    assert 'C2-C3-outside-1.25-1.45-A' in rr.enolate_geometry(ideal_enolate(distance=1.60)).failures
    bad = dict(ideal_enolate()); bad['O2'] = (2., 0., 0.)
    with pytest.raises(ValueError, match='degenerate'):
        rr.enolate_geometry(tuple(bad.items()))


def model_atom(atom_id, name, point, *, component='TST', position=191, element='H'):
    return rr.PreparedAtomV1(atom_id, 'A', position, component, name, element,
                              tuple(Decimal(str(v)) for v in point), None, 'synthetic-test-only')


def test_completed_graph_neighbors_only_and_exact_own_cap_ca_exemption():
    atoms = (model_atom('cap', 'HL191', (0, 0, 0), component='CAP'),
             model_atom('ca', 'CA', (.4, 0, 0), element='C'),
             model_atom('cb', 'CB', (1.09, 0, 0), element='C'),
             model_atom('new', 'ND2', (.5, 0, 0), element='N'),
             model_atom('other', 'CA', (.2, 0, 0), position=263))
    contacts = rr.local_contacts(atoms, (('cap', 'cb'), ('cb', 'new')), ('cap', 'ca'), (('cap', 'ca'),))
    roles = {c.other_atom_id: c.category for c in contacts if c.changed_atom_id == 'cap'}
    assert roles == {'ca': 'own-omitted-CA-cap-exemption', 'cb': 'one-bond-neighbor',
                     'new': 'two-bond-neighbor', 'other': 'severe-nonbonded-overlap'}
    assert next(c.distance_angstrom for c in contacts if c.other_atom_id == 'ca') == .4
    reverse = next(c for c in contacts if c.changed_atom_id == 'ca' and c.other_atom_id == 'cap')
    assert reverse.category == 'own-omitted-CA-cap-exemption' and reverse.distance_angstrom == .4
    with pytest.raises(ValueError, match='cap own-CA'):
        rr.local_contacts(atoms, (('cap', 'cb'),), ('cap',), (('cap', 'other'),))
    # Old/deleted bonds are not supplied to the completed graph: new is now severe.
    changed = rr.local_contacts(atoms, (('cap', 'cb'),), ('cap',), (('cap', 'ca'),))
    assert next(c.category for c in changed if c.other_atom_id == 'new') == 'severe-nonbonded-overlap'


def test_internal_result_records_refuse_mutable_nested_fields(source):
    with pytest.raises(ValueError, match='deeply immutable'):
        rr.ContactV1('a', 'b', .9, [])
    with pytest.raises(ValueError, match='deeply immutable'):
        replace(model_atom('a', 'H', (0, 0, 0)), origin=['mutable'])
    with pytest.raises(ValueError, match='row shape'):
        tokens = list(source.atoms[0].native_tokens); tokens[2] = ['mutable']
        rr.CoreAtomV1(tuple(tokens), 'A', 2, 'ASP')


def test_independent_lewis_water_magnesium_formal_charge_not_partial_charge():
    atoms = (('o', 'O'), ('a', 'H'), ('b', 'H'), ('mg', 'Mg'))
    bonds = (('o', 'a', 1), ('o', 'b', 1))
    formula, q, ne = rr.validate_lewis_inventory(atoms, bonds, (('o', 0), ('a', 0), ('b', 0), ('mg', 2)))
    assert formula == (('H', 2), ('Mg', 1), ('O', 1)) and q == 2 and ne == 20
    with pytest.raises(ValueError, match='valence'):
        rr.validate_lewis_inventory(atoms, bonds, (('o', -1), ('a', 0), ('b', 0), ('mg', 2)))
    with pytest.raises(ValueError, match='census'):
        rr.validate_lewis_inventory(atoms, bonds + bonds[:1], (('o', 0), ('a', 0), ('b', 0), ('mg', 2)))


def test_all_six_formula_full_partitions_proton_conservation_and_unready_retention(source, contexts, record_property):
    expected = {'unedited-reference': (81, -6, 382, 13828), 'D263N': (83, -5, 382, 13832), 'H287N': (78, -6, 370, 13822)}
    parent = {a.index: a for a in source.atoms}
    assert tuple(contexts) == rr.CONTEXT_ROSTER
    record_property('exposed_software_six_case_outcomes', [(v, p, c.status, len([x for x in c.changed_atom_contacts
                    if x.category == 'severe-nonbonded-overlap'])) for (v, p), c in contexts.items()])
    for (variant, view), c in contexts.items():
        n, q, ne, physical_n = expected[variant]
        assert (len(c.quantum_atoms), c.formal_quantum_charge, c.electron_count, len(c.physical_atoms)) == (n, q, ne, physical_n)
        real = {a.atom_id for a in c.quantum_atoms if a.component != 'CAP'}
        env = {a.atom_id for a in c.environment_atoms}; phy = {a.atom_id for a in c.physical_atoms}
        assert not real & env and real | env == phy and len(c.caps) == 5
        assert set(c.removed_parent_atom_indices) == {i for i in parent if 'amber:' + str(i) not in phy}
        assert c.inventory_passed and not c.executable_mm_hamiltonian and not c.exact_assay_parent_admitted
        assert not c.ground_state_certified and c.native_effects == 0
        assert c.protocol_sha256 == PROTOCOL_SHA
        assert 'C2-C3-outside-1.25-1.45-A' in c.enolate_geometry.failures
        assert 'local-plane-displacement-above-0.20-A' in c.enolate_geometry.failures
        assert c.status in ('CONSTRUCTION_REFUSED', 'GEOMETRY_UNREADY')
        ligand_a = {a.name: a for a in source.atoms if a.chain == 'A' and a.component == 'RUB'}
        ids = {'H_a': 'amber:' + str(ligand_a['HC3'].index), 'H_b': 'amber:' + str(ligand_a['HO3'].index)}
        native_kcx = {a.name: a for a in source.atoms if a.chain == 'A' and a.component == 'KCX'}
        expected_attachment = {
            'H_a': 'amber:' + str((native_kcx['OQ1'] if view == 'V2' else ligand_a['O2']).index),
            'H_b': 'amber:' + str((ligand_a['O3'] if view == 'V2' else native_kcx['OQ1']).index),
        }
        for identity, atom_id in ids.items():
            actual_edges = {other for pair in c.candidate_bonds if atom_id in pair for other in pair if other != atom_id}
            assert actual_edges == {expected_attachment[identity]}
        if view == 'V2':
            assert next(a.coordinates for a in c.physical_atoms if a.atom_id == ids['H_b']) == ligand_a['HO3'].coordinates
        actual_h = {a.atom_id for a in c.physical_atoms if a.element == 'H'}
        assert set(ids.values()) <= actual_h
        for t in c.proton_transfers:
            assert t.atom_id in actual_h
            assert next(a.coordinates for a in c.physical_atoms if a.atom_id == t.atom_id) == t.new_coordinates
        # Derive the allowed physical movements from source and protocol, not
        # the constructor's self-reported origin strings.
        moved_indices = {ligand_a['HC3'].index}
        if view == 'V3':
            moved_indices.add(ligand_a['HO3'].index)
        if variant != 'H287N':
            moved_indices.update(a.index for a in source.atoms if a.author_position == 287 and a.name == 'HE2')
        for a in c.physical_atoms:
            if a.parent_atom_index is not None and a.parent_atom_index not in moved_indices:
                assert a.coordinates == parent[a.parent_atom_index].coordinates
        assert {a.atom_id for a in c.environment_atoms if a.chain == 'B' and a.component == 'RUB'} == {
            'amber:' + str(a.index) for a in source.atoms if a.chain == 'B' and a.component == 'RUB'}
    for variant in rr.VARIANTS:
        v2, v3 = contexts[variant, 'V2'], contexts[variant, 'V3']
        assert Counter(a.element for a in v2.physical_atoms) == Counter(a.element for a in v3.physical_atoms)
        assert {a.atom_id for a in v2.physical_atoms if a.element == 'H'} == {a.atom_id for a in v3.physical_atoms if a.element == 'H'}
        assert v2.enolate_geometry == v3.enolate_geometry


def test_source_donor_rigid_geometry_and_native_vs_modeled_cg(contexts, source):
    original = {a.index: a for a in source.atoms}
    for (variant, _), c in contexts.items():
        assert len(c.mutation_audits) == (0 if variant == 'unedited-reference' else 2)
        for m in c.mutation_audits:
            assert m.donor_author_position == 9 and m.target_component == 'ASN'
            assert len(m.internal_distance_checks_angstrom) == 10
            assert all(old == pytest.approx(new, abs=1e-10) for _, _, old, new in m.internal_distance_checks_angstrom)
            cg = next(a for a in c.physical_atoms if a.parent_atom_index == m.reassigned_cg_parent_index)
            assert cg.component == 'ASN' and cg.coordinates == original[m.reassigned_cg_parent_index].coordinates
            assert cg.origin.startswith('modeled-ASN-CG-assignment')
            assert all(a.donor_atom_index is not None and a.parent_atom_index is None for a in c.physical_atoms if a.atom_id in m.added_atom_ids)


def test_his287_physical_nucleus_identity_new_attachment_and_all_cap_witnesses(contexts, source):
    native = {(a.chain, a.author_position, a.name): a for a in source.atoms}
    for (variant, _), c in contexts.items():
        h_moves = [t for t in c.proton_transfers if t.identity.startswith('His287')]
        assert len(h_moves) == (0 if variant == 'H287N' else 2)
        for t in h_moves:
            chain = t.identity.split('-')[1]
            old = native[chain, 287, 'HE2']
            assert t.atom_id == 'amber:' + str(old.index)
            assert t.previous_donor_id == 'amber:' + str(native[chain, 287, 'NE2'].index)
            assert t.new_acceptor_id == 'amber:' + str(native[chain, 287, 'ND1'].index)
            atom = next(a for a in c.physical_atoms if a.atom_id == t.atom_id)
            assert atom.name == 'HD1' and atom.component == 'HID'
            assert rr.distance(atom.coordinates, native[chain, 287, 'ND1'].coordinates) == pytest.approx(1.01)
            assert tuple(sorted((t.atom_id, t.previous_donor_id))) not in c.candidate_bonds
            assert tuple(sorted((t.atom_id, t.new_acceptor_id))) in c.candidate_bonds
        for cap in c.caps:
            assert cap.cap_cb_distance_angstrom == pytest.approx(1.09)
            assert tuple(sorted((cap.quantum_cb_atom_id, cap.environment_ca_atom_id))) not in c.candidate_bonds
            contact = next(x for x in c.changed_atom_contacts if x.changed_atom_id == cap.cap_atom_id and x.other_atom_id == cap.environment_ca_atom_id)
            assert contact.category == 'own-omitted-CA-cap-exemption'
            assert contact.distance_angstrom == cap.cap_own_ca_distance_angstrom


def test_invalid_roster_and_injected_derived_outputs_refuse_before_reconstruction(source, contexts):
    with pytest.raises(ValueError, match='fixed coupled'):
        rr.construct_rr_initial_context(source, variant='arbitrary', proton_view='V2')
    with pytest.raises(ValueError, match='fixed coupled'):
        rr.construct_rr_initial_context(source, variant='unedited-reference', proton_view='arbitrary')
    with pytest.raises(ValueError, match='init=False'):
        replace(contexts['unedited-reference', 'V2'], formal_quantum_charge=99)


def test_cold_import_blocks_optional_native_and_numerical_families():
    script = r'''
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'Bio','openmm','parmed','pdbfixer','pyscf','numpy','scipy','h5py'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_coupled_preparation
assert len(rr_coupled_preparation.CONTEXT_ROSTER)==6
assert not any(n.split('.')[0] in {'Bio','openmm','parmed','pdbfixer','pyscf','numpy','scipy','h5py'} for n in sys.modules)
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, check=False)
    assert result.returncode == 0, result.stderr
