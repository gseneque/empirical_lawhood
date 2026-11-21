"""Original atom identities survive ion insertion, never missing waters."""
from copy import deepcopy
from decimal import Decimal as D

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import exclusion_signature, retained_bonded_signature, solvation_atom_correspondence


def census(rows):
    names, starts, elements, points, labels = [], [], [], [], []
    for label, atoms in rows:
        labels.append(label)
        starts.append(len(names)+1)
        for name, z, xyz in atoms:
            names.append(name)
            elements.append(z)
            points.append(tuple(map(D, xyz)))
    return dict(residue_names=tuple(labels), residue_starts=tuple(starts), atom_names=tuple(names),
        atomic_numbers=tuple(elements), term_census={'atoms': len(names)}), tuple(points)


def example():
    # Exposed correspondence geometry only, with no enzyme/chemical admission.
    solute = ('GLY', (('CA', 6, ('0', '0', '0')), ('HA', 1, ('1', '0', '0'))))
    water1 = ('WAT', (('O', 8, ('2', '3', '4')), ('H1', 1, ('2.9', '3', '4')),
                     ('H2', 1, ('2', '3.9', '4'))))
    water2 = ('WAT', (('O', 8, ('5', '6', '7')), ('H1', 1, ('5.9', '6', '7')),
                     ('H2', 1, ('5', '6.9', '7'))))
    added = ('WAT', (('O', 8, ('12', '13', '14')), ('H1', 1, ('12.9', '13', '14')),
                    ('H2', 1, ('12', '13.9', '14'))))
    ion = ('Na+', (('Na+', 11, ('20', '20', '20')),))
    dry, before = census((solute, water1, water2))
    wet, untranslated = census((ion, solute, water2, added, water1))
    shift = tuple(map(D, ('10.0000001', '11.2', '-15.7')))
    after = tuple(tuple(v+s for v, s in zip(point, shift, strict=True)) for point in untranslated)
    return dry, wet, before, after, shift


def test_named_original_atoms_survive_ion_insertion_and_solvent_reordering():
    dry, wet, before, after, shift = example()
    result = solvation_atom_correspondence(dry, wet, before, after)
    assert result.original_to_solvated_atoms == (1, 2, 9, 10, 11, 3, 4, 5)
    assert result.original_to_solvated_residues == (1, 4, 2)
    assert result.translation_angstrom == shift
    assert result.maximum_coordinate_residual_angstrom == 0


@pytest.mark.parametrize('kind', ('water-oxygen', 'water-hydrogen', 'solute', 'water-name', 'water-element'))
def test_changed_original_atoms_cannot_be_relabelled_as_reordered(kind):
    dry, wet, before, after, _ = example()
    after = list(after)
    if kind in {'water-oxygen', 'water-hydrogen', 'solute'}:
        index = {'water-oxygen': 9, 'water-hydrogen': 10, 'solute': 2}[kind]
        after[index] = (after[index][0]+D('.001'), *after[index][1:])
    elif kind == 'water-name':
        wet['atom_names'] = (*wet['atom_names'][:10], 'H3', wet['atom_names'][11])
    else:
        wet['atomic_numbers'] = (*wet['atomic_numbers'][:10], 6, wet['atomic_numbers'][11])
    with pytest.raises(ValueError, match='solvation correspondence'):
        solvation_atom_correspondence(dry, wet, before, tuple(after))


def test_duplicate_complete_water_refuses_ambiguous_identity():
    dry, wet, before, after, _ = example()
    after = list(after)
    after[6:9] = after[9:12]
    with pytest.raises(ValueError, match='ambiguously'):
        solvation_atom_correspondence(dry, wet, before, tuple(after))


def test_mapped_bonded_parameters_retain_coefficients_and_native_signs():
    fields = {'BOND_FORCE_CONSTANT': (D(10),), 'BOND_EQUIL_VALUE': (D(1),),
        'DIHEDRAL_FORCE_CONSTANT': (D(20),), 'DIHEDRAL_PERIODICITY': (D(3),),
        'DIHEDRAL_PHASE': (D('.2'),), 'SCEE_SCALE_FACTOR': (D('1.2'),), 'SCNB_SCALE_FACTOR': (D(2),)}
    dry = {'indexed_bonded_terms': {'BONDS_INC_HYDROGEN': ((0, 3, 1),),
        'DIHEDRALS_INC_HYDROGEN': ((0, 3, -6, -9, 1),)}}
    wet = {'indexed_bonded_terms': {'BONDS_INC_HYDROGEN': ((3, 6, 1), (0, 9, 1)),
        'DIHEDRALS_INC_HYDROGEN': ((3, 6, -15, -12, 1),)}}
    mapping = (1, 2, 5, 4)
    reference = retained_bonded_signature(fields, dry, 4)
    assert retained_bonded_signature(fields, wet, 4, atom_indices=mapping) == reference
    changed = deepcopy(wet)
    changed['indexed_bonded_terms']['DIHEDRALS_INC_HYDROGEN'] = ((3, 6, 15, -12, 1),)
    assert retained_bonded_signature(fields, changed, 4, atom_indices=mapping) != reference
    changed['indexed_bonded_terms']['BONDS_INC_HYDROGEN'] += ((3, 0, 1),)
    with pytest.raises(ValueError, match='boundary'):
        retained_bonded_signature(fields, changed, 4, atom_indices=mapping)


def test_exclusions_map_both_ends_and_reject_any_original_added_pair():
    # Original atoms 0,1,2 become native 3,1,4, with two wholly added atoms.
    dry = {'exclusion_counts': (2, 1, 1), 'exclusions': (2, 3, 0, 0)}
    wet = {'exclusion_counts': (1, 1, 1, 1, 1), 'exclusions': (3, 4, 0, 5, 0)}
    mapping = (3, 1, 4)
    assert exclusion_signature(dry, 3) == exclusion_signature(wet, 3, atom_indices=mapping)
    # The newly added atom has a smaller native index than an original atom.
    # Scanning only original rows would miss this forbidden exclusion.
    wet['exclusions'] = (4, 4, 0, 5, 0)
    with pytest.raises(ValueError, match='boundary'):
        exclusion_signature(wet, 3, atom_indices=mapping)
