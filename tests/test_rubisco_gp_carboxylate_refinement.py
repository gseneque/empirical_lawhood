# SPDX-License-Identifier: MPL-2.0
"""Source, mobility and Amber phase controls for the separate common-parent protocol."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import math
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import (
    CARBOXYLATE_REPAIR_PROTOCOL, GpCarboxylateRepairInput, GpGeometryRepairInput, inherited_carboxylate_keys,
    prepare_geometry_repair_input,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import (
    CARBOXYLATE_ASSESSMENT_FILES, GpCarboxylateRepairAssessment, GpGeometryRepairAssessment, GpRepairPlanarityAssessment,
    _refined_displacement_assessment,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import (
    CAPABILITY, CARBOXYLATE_CAPABILITY, operation_declaration,
)
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import (
    AMBER_PLANARITY_BASIS, GeometryTerms, MolecularGeometryPolicy, assess_molecular_geometry,
    fixed_bond_feasibility, geometry_terms_from_amber,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from scripts.operate_gp_construction import FIELDS, validate_request
from tests.test_rubisco_preparation_integrity import amber_text, topology


def exposed_origins():
    records = []
    chains = [dict(chain=chain, subunit=('lsu' if chain in 'ACEGIKMO' else 'ssu')) for chain in 'ABCDEFGHIJKLMNOP']
    for chain in 'ACEGIKMO':
        for atom, element in (('CG', 'C'), ('CD', 'C'), ('OE1', 'O'), ('OE2', 'O')):
            ref = dict(chain=chain, position=213, atom=atom, source_component='GLU', model_component='GLU',
                       source=['1BWV', '1', 'exposed'], original_xyz_angstrom=['1.234', '2.345', '3.456'])
            records.append(dict(chain=chain, position=213, atom=atom, component='GLU', element=element,
                                status='INHERITED_OBSERVED_SOURCE', source_origin=ref))
    return dict(complete_chains=chains, complete_heavy_atoms=records,
                selected_atom_origins=[deepcopy(r['source_origin']) for r in records])


def test_only_eight_named_source_side_chains_can_move():
    origin = exposed_origins()
    parent = [dict(chain=r['chain'], position=r['position'], atom=r['atom'], xyz=tuple(
        map(Decimal, r['source_origin']['original_xyz_angstrom']))) for r in origin['complete_heavy_atoms']]
    keys = inherited_carboxylate_keys(origin, parent_atoms=parent)
    assert keys == tuple((chain, 213, atom) for chain in 'ACEGIKMO' for atom in ('CD', 'OE1', 'OE2'))
    assert all(key[2] != 'CG' for key in keys)
    parent[-1]['xyz'] = (Decimal('1.235'), Decimal('2.345'), Decimal('3.456'))
    with pytest.raises(ValueError, match='crystallographic coordinate'):
        inherited_carboxylate_keys(origin, parent_atoms=parent)


@pytest.mark.parametrize('change', ('chain', 'missing', 'duplicate', 'element', 'constructed', 'component', 'origin', 'copy'))
def test_missing_swapped_or_relabeled_source_atoms_are_refused(change):
    origin = exposed_origins()
    rows = origin['complete_heavy_atoms']
    if change == 'chain':
        origin['complete_chains'][0]['subunit'] = 'ssu'
    elif change == 'missing':
        rows.pop()
    elif change == 'duplicate':
        rows.append(deepcopy(rows[-1]))
    elif change == 'element':
        rows[-1]['element'] = 'C'
    elif change == 'constructed':
        rows[-1]['status'] = 'DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM'
    elif change == 'component':
        rows[-1]['source_origin']['source_component'] = 'GLN'
    elif change == 'origin':
        rows[-1]['source_origin']['source'][0] = '3ZXW'
    else:
        rows[-1]['source_origin']['source'][1] = '2'
    with pytest.raises(ValueError, match='Glu213'):
        inherited_carboxylate_keys(origin)


@pytest.mark.numerical(oracle='The unchangeable first bond has a 0.25-A deviation and z=0.025 sqrt(200000/RT)>6. Moving either endpoint removes exactly that bond from the fixed census.')
def test_fixed_bond_feasibility_uses_absolute_and_force_weighted_limits():
    terms = GeometryTerms((6, 8, 6, 8), ((0, 1, 1.25, 2e5), (2, 3, 1.25, 2e5)), (), ())
    xyz = ((0, 0, 0), (1, 0, 0), (0, 3, 0), (1.10, 3, 0))
    policy = MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS)
    original = fixed_bond_feasibility(xyz, terms, (), policy)
    assert original['fixed_bonds'] == 2
    assert original['disposition'] == 'INFEASIBLE_UNDER_SELECTED_FIXED_COORDINATES'
    assert [(r['atoms'], r['absolute_failure'], r['strain_failure']) for r in original['violations']] == [
        ([0, 1], True, True)]
    assert fixed_bond_feasibility(xyz, terms, (1,), policy) == dict(
        fixed_bonds=1, violations=[], disposition='FIXED_BOND_SCREEN_PASSED')
    tighter = replace(policy, maximum_harmonic_standard_deviations=Decimal(4))
    assert [r['absolute_failure'] for r in fixed_bond_feasibility(xyz, terms, (), tighter)['violations']] == [True, False]
    for invalid in ((1, 1), (-1,), (4,)):
        with pytest.raises(ValueError, match='atom census'):
            fixed_bond_feasibility(xyz, terms, invalid, policy)


@pytest.mark.numerical(oracle='The 3-4-5 exposed displacement vector has norm 0.5 angstrom and its signed Cartesian components come from a tenfold nm/A conversion.')
def test_independent_displacement_uses_native_signed_coordinates_and_strict_cap():
    keys = inherited_carboxylate_keys(exposed_origins())
    joined = {key: index for index, key in enumerate(keys)}
    first = np.zeros((len(keys), 3), dtype=float)
    final = first.copy()
    final[7, :2] = (.03, -.04)
    reported = [[list(key), [0., 0., 0.]] for key in keys]
    reported[7][1] = [.3, -.4, 0.]
    maximum, findings, rows = _refined_displacement_assessment(keys, joined, first, final, reported, Decimal('.50'))
    assert (maximum, findings) == (Decimal('.5'), ())
    assert tuple(row[:3] for row in rows) == keys and rows[7][3] == (Decimal('.3'), Decimal('-.4'), Decimal('0'))
    _, findings, _ = _refined_displacement_assessment(keys, joined, first, final, reported, Decimal('.49'))
    assert findings == ('refined-inherited-heavy-atom-displacement',)
    for forged in (reported[:-1], reported[::-1], [[key, [abs(x) for x in vector]] for key, vector in reported]):
        with pytest.raises(ValueError, match='displacements'):
            _refined_displacement_assessment(keys, joined, first, final, forged, Decimal(1))


@pytest.mark.numerical(oracle='Alternating square corners are exactly 0.2 A from z=0. The source Amber 180-degree serialization identifies the same planar minimum and the raw phase still determines energy.')
def test_actual_amber_phase_through_full_raw_parser_and_both_policy_revisions():
    raw = topology()
    raw['DIHEDRAL_PHASE'] = [Decimal('3.141594')]
    raw['DIHEDRAL_FORCE_CONSTANT'] = [Decimal('1.7')]
    terms = geometry_terms_from_amber(amber_text(raw).encode('ascii'))
    coords = [(1, 1, .2), (-1, 1, -.2), (-1, -1, .2), (1, -1, -.2)]
    old = assess_molecular_geometry(coords, terms, policy=MolecularGeometryPolicy())
    policy = MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS)
    new = assess_molecular_geometry(coords, terms, policy=policy)
    assert old['counts']['planar_impropers_checked'] == 0
    assert new['counts']['positive_amplitude_impropers'] == new['counts']['applicable_planar_impropers'] == 1
    assert new['counts']['planar_impropers_checked'] == new['counts']['violating_planar_impropers'] == 1
    assert new['metrics']['maximum_planar_improper_distance_angstrom'] == pytest.approx(.2)
    assert new['metrics']['torsion_energy_kj_mol'] == old['metrics']['torsion_energy_kj_mol']
    assert 'whole-molecule-planar-improper-deviation' in new['findings']
    census = GpRepairPlanarityAssessment.from_quality(new)
    assert census.checked_terms == census.violating_terms == 1
    with pytest.raises(ValueError):
        replace(census, exempt_terms=1)
    exempt = assess_molecular_geometry(coords, terms, policy=policy, exempt_bonded_atoms=(0, 1, 2, 3))
    assert exempt['counts']['exempt_planar_impropers'] == 1 and exempt['counts']['planar_impropers_checked'] == 0
    assert 'whole-molecule-planar-improper-coverage-empty' in exempt['findings']
    degenerate = assess_molecular_geometry([(i, 0, 0) for i in range(4)], terms, policy=policy)
    assert degenerate['counts']['undefined_planar_impropers'] == 1
    assert degenerate['counts']['planar_impropers_checked'] == 0


@pytest.mark.parametrize(('periodicity', 'phase', 'force', 'improper', 'expected'), (
    (2, math.pi, 5., True, 1), (2, -3.141594, 5., True, 1),
    (2, 3.141594 + .5e-7, 5., True, 1), (2, 3.141594 + 3e-7, 5., True, 0),
    (2, 0., -5., True, 1), (2, 0., 5., True, 0), (2, 1.1, 5., True, 0),
    (2, 3.141594, 0., True, 0), (1, 3.141594, 5., True, 0), (2, 3.141594, 5., False, 0),
))
def test_explicit_improper_periodicity_phase_amplitude_and_bounds(periodicity, phase, force, improper, expected):
    quartets = ((0, 1, 2, 3, periodicity, phase, force),)
    terms = GeometryTerms((6, 6, 6, 6), (), (), quartets, (0,) if improper else ())
    report = assess_molecular_geometry(((0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)), terms,
                                       policy=MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS))
    assert report['counts']['planar_impropers_checked'] == expected
    assert report['counts']['applicable_planar_impropers'] == expected
    assert report['counts']['zero_amplitude_impropers'] == int(improper and force == 0)
    assert ('whole-molecule-planar-improper-coverage-empty' in report['findings']) == (expected == 0)


def test_fresh_and_historical_native_selections_and_assessment_revisions_are_distinct():
    old, fresh = operation_declaration(), operation_declaration(carboxylates=True)
    assert old.manifest().registry_id == CAPABILITY + '@3.0.0'
    assert fresh.manifest().registry_id == CARBOXYLATE_CAPABILITY + '@4.0.0'
    assert old.manifest().fingerprint() == '5129936e9d81f092e5d8ed321c99f5b88f628b8bf8830bc47fa7b41e54c46a56'
    assert fresh.input_record_types == (GpCarboxylateRepairInput,)
    source = ObjectIdentity('input.exposed-parent', GpGeometryRepairInput.SCHEMA, '4.0.0', '4'*64)
    args = ('assessment.exposed', source, tuple((name, '5'*64) for name in CARBOXYLATE_ASSESSMENT_FILES),
            124, 80, 20, 90, Decimal(0), Decimal(0), Decimal(2), 0, 0, 0, 0, (), AssessmentDisposition.SATISFIED)
    keys = inherited_carboxylate_keys(exposed_origins())
    rows = tuple((*key, (Decimal('.2'), Decimal('0'), Decimal('0'))) for key in keys)
    result = GpCarboxylateRepairAssessment(*args, refined_inherited_heavy_atoms=24,
        largest_refined_displacement_angstrom=Decimal('.2'), refined_displacements_angstrom=rows, fixed_bonds_checked=80,
        planarity=GpRepairPlanarityAssessment(12, 10, 0, 2, 10, 10, 0, 0, 0, Decimal('.08')))
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=8192) == result
    with pytest.raises(ValueError):
        decode_canonical_bytes(result.canonical_bytes(), GpGeometryRepairAssessment, maximum_bytes=8192)
    for changes in (dict(refined_inherited_heavy_atoms=23), dict(fixed_heavy_atoms=104),
                    dict(largest_refined_displacement_angstrom=Decimal('NaN')),
                    dict(refined_displacements_angstrom=rows[:-1]), dict(fixed_bonds_checked=0),
                    dict(planarity=replace(result.planarity, violating_terms=1, maximum_residual_angstrom=Decimal('.12'))),
                    dict(source=replace(source, object_version='3.0.0'))):
        with pytest.raises(ValueError):
            replace(result, **changes)


def test_public_parent_selection_requires_matching_exact_decimal(tmp_path):
    request = {key: str(tmp_path / key) for key in ('output_directory', *FIELDS['prepare-parent'])}
    validate_request('prepare-parent', request)
    fresh = dict(parent_repair_protocol=CARBOXYLATE_REPAIR_PROTOCOL, maximum_refined_displacement_angstrom='0.50')
    validate_request('prepare-parent', {**request, **fresh})
    incorrect = [dict(parent_repair_protocol=CARBOXYLATE_REPAIR_PROTOCOL), dict(maximum_refined_displacement_angstrom='0.5'),
                 dict(parent_repair_protocol='any-site')]
    incorrect.extend({**fresh, 'maximum_refined_displacement_angstrom': invalid} for invalid in (0.5, '', 'NaN', 'Inf', '0', '-1'))
    for fields in incorrect:
        with pytest.raises(ValueError):
            validate_request('prepare-parent', {**request, **fields})


def test_fresh_protocol_cannot_relax_the_historical_absolute_or_force_weighted_limits():
    policy = MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS)
    named = dict(parent_repair_protocol=CARBOXYLATE_REPAIR_PROTOCOL, maximum_refined_displacement_angstrom=Decimal('.25'))
    unused = dict.fromkeys(('parent', 'parent_assessment', 'heavy_pdb', 'origin_json', 'amber_engine', 'numeric_engine'))
    for different in (MolecularGeometryPolicy(), replace(policy, maximum_bond_deviation_angstrom=Decimal('.24')),
                      replace(policy, maximum_harmonic_standard_deviations=Decimal(8)),
                      replace(policy, maximum_planar_improper_distance_angstrom=Decimal('.20'))):
        with pytest.raises(ValueError, match='unmodified nominal-Amber'):
            prepare_geometry_repair_input(**unused, **named, geometry_quality=different)


def test_child_prepare_reads_parent_once_and_preserves_prospective_geometry_policy(monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import initial_amber as api
    parent = MolecularGeometryPolicy(basis=AMBER_PLANARITY_BASIS)
    reads = []

    def retained(**kwargs):
        reads.append(kwargs['directory_relative_path'])
        return dict(parent_geometry_quality=parent, scaffolds=('four-exposed-scaffolds',), assessments=('correspondence',))

    monkeypatch.setattr(api, 'read_active_gp_scaffolds', retained)
    monkeypatch.setattr(api, 'read_rubp_template', lambda **kwargs: {'preparation': 'exposed-ligand'})
    monkeypatch.setattr(api, 'authenticate_engine', lambda engine: None)
    monkeypatch.setattr(api, 'prepare_initial_amber_input', lambda **kwargs: kwargs)
    request = dict(scaffold_relative_path='exposed-scaffolds', ligand_relative_path='exposed-ligand',
                   component_sha256='a'*64, parameter_sources=(), engine=None, numeric_engine=None,
                   artifact_writer=SimpleNamespace(read_manifest=lambda path: path), ligand_artifact_writer=None)
    produced = api.prepare_initial_gp_amber(**request)
    assert produced['geometry_quality'] is parent and len(produced['manifests']) == 4
    assert reads == ['exposed-scaffolds']
    with pytest.raises(ValueError, match='four Amber children'):
        api.prepare_initial_gp_amber(**request, geometry_quality=MolecularGeometryPolicy())
