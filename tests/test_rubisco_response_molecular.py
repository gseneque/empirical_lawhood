# SPDX-License-Identifier: MPL-2.0
"""Exposed finite atom/custody falsifiers; no enzyme or native qualification."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation, validate_amber_atom_correspondence
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import AtomicTransformation, derive_atomic_transformation, validate_atomic_transformation
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_selection import validate_reactive_selection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.rubisco_response_molecular_fixture import common_atoms, pair, reactive, representation


@pytest.fixture(scope="module")
def selected():
    return pair()


def transform(case, before, after):
    return derive_atomic_transformation(before, after, transformation_id="transformation.disclosed",
        kind="FINITE_SEQUENCE_SUBSTITUTION", common_atoms=common_atoms(before, after),
        protocol=case.sources[0], sources=case.sources, case=case)


def test_complete_raw_atom_census_exact_charge_and_roundtrip(selected):
    _, before, after = selected
    for model, raw, _ in (before, after):
        result = validate_amber_atom_correspondence(model, raw)
        assert result["term_census"]["atoms"] == len(model.atoms)
        assert len(model.sites) == 8
        assert len({row.chain_id for row in model.residues if row.role == "PROTEIN"}) == 16
        assert decode_canonical_bytes(model.canonical_bytes(), MolecularRepresentation, maximum_bytes=200_000) == model
    with localcontext() as context:
        context.prec = 3
        assert before[0].atoms[0].charge_electron == Fraction(D("0.12345678")) / Fraction(D("18.2223"))
        validate_amber_atom_correspondence(before[0], before[1])


def test_finite_mutation_retains_all_eight_sulfur_changes_and_full_common_atoms(selected):
    case, (before, _, _), (after, _, _) = selected
    result = transform(case, before, after)
    assert len(result.removed_atom_indices) == len(result.added_atom_indices) == 8
    assert all(before.atoms[i].atomic_number == 6 for i in result.removed_atom_indices)
    assert all(after.atoms[i].atomic_number == 16 for i in result.added_atom_indices)
    assert len(result.removed_bonds) == len(result.added_bonds) == 8
    assert len(result.common_atoms) + 8 == len(before.atoms)
    assert result.changed_site_ids == ()
    validate_atomic_transformation(result, before, after, case=case)
    assert decode_canonical_bytes(result.canonical_bytes(), AtomicTransformation, maximum_bytes=100_000) == result
    with pytest.raises(ValueError, match="complete independent"):
        validate_atomic_transformation(replace(result, added_atom_indices=result.added_atom_indices[:-1]), before, after, case=case)
    with pytest.raises(ValueError, match="shared physical atom"):
        derive_atomic_transformation(before, after, transformation_id="transform.omitted", kind=result.kind,
            common_atoms=result.common_atoms[:-1], protocol=result.protocol, sources=result.sources, case=case)
    with pytest.raises(ValueError, match="physical element|atom name"):
        derive_atomic_transformation(before, after, transformation_id="transform.false", kind=result.kind,
            common_atoms=tuple((i, i) for i in range(len(before.atoms))), protocol=result.protocol, sources=result.sources, case=case)


def test_all_changed_masses_charges_and_parameter_types_are_retained(selected):
    case, (before, _, _), (after, _, _) = selected
    changed = replace(after.atoms[0], mass_dalton=D("13.0001"), charge_native=D("0.23456789"), parameter_type="CX")
    current = replace(after, atoms=(changed, *after.atoms[1:]))
    result = transform(case, before, current)
    assert result.changed_parameter_pairs == ((0, 0),)
    with pytest.raises(ValueError, match="complete independent"):
        validate_atomic_transformation(replace(result, changed_parameter_pairs=()), before, current, case=case)
    with pytest.raises(ValueError, match="protocol.*temperature"):
        transform(case, before, replace(after, temperature_k=D("298")))


@pytest.mark.parametrize("change", ("site", "sequence", "author", "origin", "array", "chemical-label"))
def test_complete_mapping_rejects_thinning_aliases_and_relabeling(selected, change):
    model = selected[1][0]
    with pytest.raises(ValueError):
        if change == "site":
            replace(model, sites=model.sites[:-1])
        elif change == "sequence":
            replace(model, residues=model.residues[:-1])
        elif change == "author":
            rows = list(model.residues)
            rows[1] = replace(rows[1], author_chain=rows[0].author_chain, author_number=rows[0].author_number)
            replace(model, residues=tuple(rows))
        elif change == "origin":
            replace(model, atoms=(model.atoms[0], replace(model.atoms[1], source_atom_id=model.atoms[0].source_atom_id), *model.atoms[2:]))
        elif change == "array":
            member = replace(model.arrays.members[0], shape=(len(model.atoms) - 1, 3))
            replace(model, arrays=replace(model.arrays, members=(member,)))
        else:
            residue = next(row for row in model.residues if row.sequence_letter == "I")
            replace(residue, component="MET")


@pytest.mark.parametrize("change", ("raw", "mass", "charge", "type", "bonds"))
def test_raw_native_parameters_and_bonds_are_independent_of_the_producer_map(selected, change):
    model, raw, _ = selected[1]
    if change == "raw":
        raw += b"\n"
    elif change == "bonds":
        model = replace(model, bonds=model.bonds[:-1])
    else:
        field, value = {"mass": ("mass_dalton", D(13)), "charge": ("charge_native", D(1)), "type": ("parameter_type", "XX")}[change]
        model = replace(model, atoms=(replace(model.atoms[0], **{field: value}), *model.atoms[1:]))
    with pytest.raises(ValueError, match="raw topology|native element|native bonds"):
        validate_amber_atom_correspondence(model, raw)


def test_chemical_transformation_is_separate_and_retains_all_site_changes(selected):
    model = selected[1][0]
    inhibited = replace(model.chemistry, protocol_id="chemistry.inhibited-control",
        sites=tuple(replace(row, ligand_state="CABP") for row in model.chemistry.sites))
    old, _, _ = representation(model.material, inhibited, name="molecular.disclosed.inhibited")
    result = derive_atomic_transformation(old, model, transformation_id="transform.activation",
        kind="CHEMICAL_STATE_TRANSFORMATION", common_atoms=common_atoms(old, model),
        protocol=model.material.sources[0], sources=model.material.sources)
    assert result.changed_site_ids == tuple(row.site_id for row in model.sites)
    assert not old.chemistry.active_ensemble_selected and model.chemistry.active_ensemble_selected
    assert "NOT_OVERLAP_OR_CHEMICAL_ADMISSION" in result.interpretation
    validate_atomic_transformation(result, old, model)
    assert old.chemistry.sites[0].ligand_state == "CABP"


def test_complete_reactive_partition_charge_spin_and_missing_oxygenation(selected):
    model = selected[1][0]
    selection = reactive(model)
    gaps = validate_reactive_selection(selection, model)
    assert "requirement.reactive.selected-backend-support" in gaps
    assert len(selection.qm_atom_indices) + len(selection.mm_atom_indices) == len(model.atoms)
    with pytest.raises(ValueError, match="electron parity"):
        validate_reactive_selection(replace(selection, spin_multiplicity=selection.spin_multiplicity + 1), model)
    with pytest.raises(ValueError, match="cut bond"):
        validate_reactive_selection(replace(selection, boundaries=()), model)
    with pytest.raises(ValueError, match="full physical environment"):
        replace(selection, mm_atom_indices=selection.mm_atom_indices[:-1])
    oxygen, _, _ = representation(model.material, model.chemistry, name="molecular.disclosed.oxygen", gas="O2")
    assert "requirement.reactive.oxygenation-assumption" in validate_reactive_selection(reactive(oxygen, gas="O2"), oxygen)
    with pytest.raises(ValueError, match="magnesium"):
        omitted = selection.qm_atom_indices[1:]
        moved = tuple(sorted((*selection.mm_atom_indices, selection.qm_atom_indices[0])))
        validate_reactive_selection(replace(selection, qm_atom_indices=omitted, mm_atom_indices=moved, boundaries=()), model)
