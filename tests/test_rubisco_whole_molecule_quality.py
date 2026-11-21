# SPDX-License-Identifier: MPL-2.0
"""Independent geometry/norm controls and refusal composition; no molecular run."""
from dataclasses import replace
from decimal import Decimal as D
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import (
    GeometryTerms, MolecularGeometryPolicy, assess_molecular_geometry,
    geometry_terms_from_amber, geometry_terms_from_snapshot, gradient_statistics,
)


def assess(xyz, terms, **kwargs):
    return assess_molecular_geometry(xyz, terms, policy=MolecularGeometryPolicy(), **kwargs)


@pytest.mark.numerical(oracle='Independent Euclidean distance of OPTIM-reported unbonded H-H pair; no heavy atoms are present.')
def test_reported_subangstrom_hydrogen_contact_is_no_longer_invisible():
    terms = GeometryTerms((1, 1), (), (), ())
    report = assess(((0., 0., 0.), (.348895, 0., 0.)), terms)
    assert report['disposition'] == 'REJECTED'
    assert report['gross_contact_pairs'] == 1 and report['counts']['hydrogens'] == 2
    assert report['diagnostics'][0]['value'] == .348895


def test_heavy_contact_guard_is_preserved_and_qm_bond_exemption_cannot_hide_nuclear_contact():
    report = assess(((0., 0., 0.), (.8, 0., 0.)), GeometryTerms((6, 8), (), (), ()))
    assert report['gross_contact_pairs'] == 1
    bonded_qm = GeometryTerms((6, 1), ((0, 1, 1.09, 300000.),), (), ())
    report = assess(((0., 0., 0.), (.3, 0., 0.)), bonded_qm, exempt_bonded_atoms=(0, 1))
    assert report['counts']['exempt_bonds'] == 1 and report['gross_contact_pairs'] == 1
    unbonded_hydrogens = assess(((0., 0., 0.), (.8, 0., 0.)), GeometryTerms((1, 1), (), (), ()))
    assert unbonded_hydrogens['gross_contact_pairs'] == 1
    normal_qm_oh = GeometryTerms((8, 1), ((0, 1, 1., 300000.),), (), ())
    assert assess(((0., 0., 0.), (.96, 0., 0.)), normal_qm_oh,
        exempt_bonded_atoms=(0, 1))['disposition'] == 'SCREEN_PASSED'


def test_declared_transferred_qm_proton_is_covalent_only_for_exact_authored_pair():
    terms = GeometryTerms((8, 1, 6), (), (), ())
    xyz = ((0., 0., 0.), (.98, 0., 0.), (5., 0., 0.))
    assert assess(xyz, terms, exempt_bonded_atoms=(0, 1))['disposition'] == 'REJECTED'
    policy = replace(MolecularGeometryPolicy(), reactive_hydrogen_bond_pairs=((0, 1),))
    selected = assess_molecular_geometry(xyz, terms, policy=policy, exempt_bonded_atoms=(0, 1))
    assert selected['disposition'] == 'SCREEN_PASSED'
    assert selected['counts']['reactive_hydrogen_bonds'] == 1
    assert selected['policy'] == policy.to_document()
    compressed = ((0., 0., 0.), (.533, 0., 0.), (5., 0., 0.))
    assert assess_molecular_geometry(compressed, terms, policy=policy,
        exempt_bonded_atoms=(0, 1))['disposition'] == 'REJECTED'
    with pytest.raises(ValueError, match='both actual selected QM'):
        assess_molecular_geometry(xyz, terms, policy=policy, exempt_bonded_atoms=(0,))


@pytest.mark.parametrize('pairs', (((0, 2),), ((1, 3),), ((0, 1), (0, 1)), ((1, 0),)))
def test_reactive_contact_selection_rejects_nonhydrogen_missing_repeated_or_unordered_atoms(pairs):
    with pytest.raises(ValueError):
        policy = replace(MolecularGeometryPolicy(), reactive_hydrogen_bond_pairs=pairs)
        assess_molecular_geometry(((0., 0., 0.), (.98, 0., 0.), (5., 0., 0.)),
            GeometryTerms((8, 1, 6), (), (), ()), policy=policy, exempt_bonded_atoms=(0, 1, 2))


@pytest.mark.numerical(oracle='C-H displacement 1.09-0.532982=0.557018 Angstrom, compared with the actual topology equilibrium; z=sqrt(2E/RT).')
def test_reported_compressed_carbon_hydrogen_bond_fails_whole_topology_gate():
    terms = GeometryTerms((6, 1), ((0, 1, 1.09, 300000.),), (), ())
    report = assess(((0., 0., 0.), (.532982, 0., 0.)), terms)
    assert report['disposition'] == 'REJECTED'
    assert report['metrics']['maximum_bond_deviation_angstrom'] == pytest.approx(.557018)
    energy = .5*300000*(.557018/10)**2
    expected_z = math.sqrt(2*energy/(.00831446261815324*298.15))
    assert report['metrics']['maximum_bond_harmonic_z'] == pytest.approx(expected_z)
    assert 'whole-molecule-bond-deviation' in report['findings']
    assert 'whole-molecule-bond-strain' in report['findings']


@pytest.mark.numerical(oracle='An independent right triangle has a pi/2 angle and a 45-degree mismatch with a pi/4 equilibrium.')
def test_angle_units_and_harmonic_strain_are_not_bond_only_checks():
    terms = GeometryTerms((6, 6, 1), ((0, 1, 1., 100.), (1, 2, 1., 100.)),
                          ((0, 1, 2, math.pi/4, 100.),), ())
    report = assess(((1., 0., 0.), (0., 0., 0.), (0., 1., 0.)), terms)
    assert report['metrics']['maximum_angle_deviation_degrees'] == pytest.approx(45)
    assert report['metrics']['maximum_angle_harmonic_z'] == pytest.approx(math.pi/4*math.sqrt(100/(.00831446261815324*298.15)))
    assert 'whole-molecule-angle-deviation' in report['findings']


@pytest.mark.numerical(oracle='Orthogonal planes have a signed right-angle dihedral; 2[1+cos(pi/2-pi/2)]=4 kJ/mol.')
def test_complete_torsion_diagnostics_preserve_selected_periodicity_and_phase():
    terms = GeometryTerms((6, 6, 6, 6), (), (), ((0, 1, 2, 3, 1, math.pi/2, 2.),))
    report = assess(((0., 0., 0.), (1., 0., 0.), (1., 1., 0.), (1., 1., 1.)), terms)
    assert report['counts']['torsions'] == 1
    assert report['metrics']['torsion_energy_kj_mol'] == pytest.approx(4)
    assert not report['findings']
    failed = assess(((0., 0., 0.), (1., 0., 0.), (2., 0., 0.), (3., 0., 0.)), terms)
    assert failed['metrics']['undefined_torsions'] == 1
    assert 'whole-molecule-undefined-torsion' in failed['findings']


@pytest.mark.numerical(oracle='Four symmetric square corners with alternating z=+/-0.2 have best-fit plane z=0 and maximum orthogonal residual0.2 Angstrom, since z variance is smaller than x/y variance.')
def test_source_planar_improper_checks_planarity_without_rejecting_proper_rotamers():
    torsions = ((0, 1, 2, 3, 2, math.pi, 5.),)
    xyz = ((1., 1., .2), (-1., 1., -.2), (-1., -1., .2), (1., -1., -.2))
    source_improper = GeometryTerms((6,)*4, (), (), torsions, (0,))
    report = assess(xyz, source_improper)
    assert report['counts']['planar_impropers_checked'] == 1
    assert report['metrics']['maximum_planar_improper_distance_angstrom'] == pytest.approx(.2)
    assert 'whole-molecule-planar-improper-deviation' in report['findings']
    proper = assess(xyz, GeometryTerms((6,)*4, (), (), torsions))
    assert proper['counts']['planar_impropers_checked'] == 0 and not proper['findings']
    planar = assess(tuple((x, y, 0.) for x, y, _ in xyz), source_improper)
    assert planar['disposition'] == 'SCREEN_PASSED'
    negative_amplitude = replace(source_improper, torsions=((0, 1, 2, 3, 2, 0., -5.),))
    assert assess(xyz, negative_amplitude)['counts']['planar_impropers_checked'] == 1


@pytest.mark.numerical(oracle='Amber E=k dr_A^2 kcal/mol equals OpenMM .5*(2*4.184*100*k)*dr_nm^2; angle coefficient2*4.184, torsion coefficient4.184 with sign retained.')
def test_raw_amber_harmonic_convention_and_signed_improper_conversion():
    from tests.test_rubisco_preparation_integrity import topology, amber_text
    raw = topology()
    raw['BOND_FORCE_CONSTANT'] = [D(100)]
    raw['ANGLE_EQUIL_VALUE'] = [D('1.5')]
    terms = geometry_terms_from_amber(amber_text(raw).encode('ascii'))
    assert terms.atomic_numbers == (6, 7, 6, 1)
    assert terms.bonds[0][2:] == pytest.approx((1.379, 83680.))
    assert terms.angles[0][3:] == pytest.approx((1.5, 552.288))
    assert terms.torsions == ((0, 1, 2, 3, 2, 0., -1.7*4.184),)
    assert terms.improper_torsion_indices == (0,)


@pytest.mark.numerical(oracle='Minimum image: points at x=.1 and x=9.9 in a length10 cell are .2 Angstrom apart.')
def test_periodic_all_atom_contacts_use_original_minimum_image():
    report = assess(((.1, 0., 0.), (9.9, 0., 0.)), GeometryTerms((1, 1), (), (), ()), cell_angstrom=(10., 10., 10.))
    assert report['gross_contact_pairs'] == 1
    assert report['diagnostics'][0]['value'] == pytest.approx(.2)


def test_qm_exemption_is_exact_bonded_subset_and_never_hides_nuclear_contact():
    terms = GeometryTerms((6, 1, 1), ((0, 1, 1., 300000.), (0, 2, 1., 300000.)), (), ())
    report = assess(((0., 0., 0.), (.5, 0., 0.), (.6, 0., 0.)), terms, exempt_bonded_atoms=(0, 1))
    assert report['counts']['exempt_bonds'] == 1
    assert 'whole-molecule-bond-deviation' in report['findings']
    assert 'whole-molecule-gross-all-atom-contact' in report['findings']


def test_complete_contact_capacity_failure_cannot_be_presented_as_a_pass():
    report = assess_molecular_geometry(np.zeros((5, 3)), GeometryTerms((1,)*5, (), (), ()),
        policy=replace(MolecularGeometryPolicy(), maximum_contact_candidates=2))
    assert report['disposition'] == 'REJECTED' and not report['contact_census_complete']
    assert 'whole-molecule-contact-census-capacity-exceeded' in report['findings']


@pytest.mark.parametrize('changes', ({'maximum_bond_deviation_angstrom': D('NaN')},
    {'maximum_angle_deviation_degrees': D(180)}, {'minimum_unbonded_distance_angstrom': D(0)},
    {'reference_temperature_kelvin': D(-1)}, {'basis': ''}))
def test_authored_geometry_policy_refuses_undefined_thresholds(changes):
    with pytest.raises((ValueError, TypeError)):
        replace(MolecularGeometryPolicy(), **changes)


@pytest.mark.numerical(oracle='Vector (3,4,0) has norm5; six Cartesian components have mean square25/6; two atom-vector norms have mean square25/2.')
def test_force_norm_conventions_are_explicit_and_noninterchangeable():
    report = gradient_statistics(((3., 4., 0.), (0., 0., 0.)), unit='kJ/mol/nm')
    assert report['maximum_cartesian_component'] == 4
    assert report['maximum_atom_vector_norm'] == 5
    assert report['rms_cartesian_component'] == pytest.approx(5/math.sqrt(6))
    assert report['rms_atom_vector_norm'] == pytest.approx(5/math.sqrt(2))
    assert report['rms_atom_vector_norm'] == pytest.approx(math.sqrt(3)*report['rms_cartesian_component'])


@pytest.mark.numerical(oracle='Positive homogeneity of Euclidean norms: scale*(3,4,0) has norm5*scale even when unscaled squares would overflow binary64.')
def test_force_norms_use_scaled_squares_instead_of_spurious_overflow():
    report = gradient_statistics(((3e200, 4e200, 0.),), unit='kJ/mol/nm')
    assert report['maximum_atom_vector_norm'] == pytest.approx(5e200)
    assert report['rms_cartesian_component'] == pytest.approx(5e200/math.sqrt(3))


@pytest.mark.numerical(oracle='Chain rule dE/dx_nm=(dE/dx_Bohr)*(10/Bohr_A)*Hartree_kJmol, using separately specified units.')
def test_hartree_bohr_gradient_conversion_has_no_angstrom_nanometer_ambiguity():
    unit = 'Eh/PySCF-Bohr-0.52917721092-A'
    bohr, hartree = .52917721092, 2625.5
    report = gradient_statistics(((1., 0., 0.),), unit=unit, bohr_angstrom=bohr, hartree_kj_mol=hartree)
    assert report['maximum_cartesian_component'] == pytest.approx(hartree/(bohr/10))
    with pytest.raises(ValueError, match='exact Bohr'):
        gradient_statistics(((1., 0., 0.),), unit=unit, bohr_angstrom=bohr/10, hartree_kj_mol=hartree)


def test_native_snapshot_geometry_conversion_preserves_all_term_denominators():
    snapshot = dict(bonds=((0, 1, .109, 300000.),), angles=(), torsions=())
    terms = geometry_terms_from_snapshot((6, 1), snapshot)
    assert terms.bonds == ((0, 1, 1.09, 300000.),)
    assert assess(((0., 0., 0.), (1.09, 0., 0.)), terms)['disposition'] == 'SCREEN_PASSED'


def test_bad_geometry_refuses_before_a_complete_reference_call_or_budget_charge():
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_native import InvalidRelaxationGeometry
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_native import minimize_reference_prefix
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
    class Operator:
        def evaluate(self, coordinates):
            pytest.fail('invalid geometry reached the reference operator')
    def guard(coordinates):
        report = assess(coordinates, GeometryTerms((1, 1), (), (), ()))
        if report['findings']:
            raise InvalidRelaxationGeometry('gross all-atom contact')
    events = []
    with pytest.raises(InvalidRelaxationGeometry):
        minimize_reference_prefix(operator=Operator(), initial_angstrom=np.zeros((2, 3)),
            settings=ActiveRelaxationSettings('test.invalid-molecule'), complete_return_allowance=5,
            observe=events.append, retain_evaluation=lambda *args:pytest.fail('invalid evaluation published'),
            retain_checkpoint=lambda *args:pytest.fail('invalid checkpoint published'), geometry_guard=guard)
    assert not events
