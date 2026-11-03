# SPDX-License-Identifier: MPL-2.0
"""Independent checks over complete exposed old products, not qualification."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
    contracts as c,
    independent_assessment as independent,
    science,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_structure.independent_cif import read_cif
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.rubisco_nomination_fixture import nominee, structural_source
from tests.rubisco_structure_fixture import historical_products


@pytest.fixture(scope="module")
def exposed():
    source = structural_source()
    _, dossier = nominee()
    return source, dossier, historical_products()


def forbidden(*_args, **_kwargs):
    pytest.fail("independent assessment/recovery must not execute producer")


def test_separate_cif_state_machine_keeps_quoted_controls_comments_and_text():
    tables = read_cif('data_fixture\n_note.text\n;first\nsecond\n;\nloop_\n_atom.a\n_atom.b\n1 "O5\'"\n2 \'loop_\' # ignored\n3 "_reserved"\n')
    assert tables["_note"] == [{"text":"first\nsecond"}]
    assert tables["_atom"] == [{"a":"1", "b":"O5'"}, {"a":"2", "b":"loop_"}, {"a":"3", "b":"_reserved"}]


@pytest.mark.parametrize("text", [
    "data_f\nloop_\n_a.x\n_a.y\n1\n", "data_f\n_a.x 1\n_a.x 2\n",
    "data_f\n_a.x\n;unterminated\n", "data_f\n_a.x 'unfinished\n",
    "data_f\n_a.x 1\ndata_other\n", "data_f\nloop_\n_a.x\n_b.x\n1 2\n",
    "data_f\n_a.x\nloop_\n", "data_f\nloop_\n_a.x\n_a.x\n1 2\n",
])
def test_independent_parser_refuses_incomplete_or_ambiguous_source(text):
    with pytest.raises(ValueError, match="independent CIF"):
        read_cif(text)


def test_complete_historical_source_and_export_assess_without_producer(exposed, monkeypatch):
    source, dossier, products = exposed
    for name in ("cif_tables", "expand", "analyze", "neighborhoods"):
        monkeypatch.setattr(science, name, forbidden)
    assessor = ObjectIdentity("source.exposed-independent-assessor", "empirical-lawhood/source-snapshot", "1.0.0", "7"*64)
    result = independent.assess(source, dossier, products["inventory"], assessor_source=assessor, coordinates=products["coordinates"])
    assert len(result.chain_coverage) == 32
    assert all(count > 0 for _, count in result.atom_census)
    assert all(length in (493, 138, 475, 118) for _, length, _, _ in result.chain_coverage)
    assert any(missing for _, _, _, missing in result.chain_coverage)
    assert result.mutant_comparison_disposition is c.A.UNEVALUABLE
    assert result.preparation_disposition is c.A.NOT_ATTEMPTED
    assert result.kinetic_disposition is c.A.UNEVALUABLE
    assert result.physical_independent_units == 0
    assert result.maximum_distance_residual_angstrom <= D("1e-10")
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    # Legacy canonical assessment remains exact, while its algorithm is now
    # independent. The old receipt continues to describe the old execution.
    assert science.assess(source, dossier, products["inventory"]).canonical_bytes() == products["assessment"].canonical_bytes()


@pytest.mark.parametrize("field,value", [
    ("occupancy", D("0")), ("alternate_id", "SUBSTITUTED"), ("auth_seq_id", "113"),
    ("insertion_code", "A"), ("component_id", "LYS"), ("atom_id", "SUBSTITUTED"),
    ("element", "O"), ("xyz_angstrom", (D(999), D(0), D(0))),
])
def test_actual_atom_source_operator_occupancy_and_alternates_cannot_be_substituted(exposed, field, value):
    source, dossier, products = exposed
    old = products["inventory"]
    changed = replace(old, atoms=(replace(old.atoms[0], **{field:value}), *old.atoms[1:]))
    with pytest.raises(ValueError, match="independent source atom"):
        independent.validate_observed_inventory(source, dossier, changed)


@pytest.mark.parametrize("kind", ["missing_atom", "missing_chain", "missing_residue", "operator", "chemical", "sequence"])
def test_complete_assembly_and_source_denominators_are_mandatory(exposed, kind):
    source, dossier, products = exposed
    old = products["inventory"]
    if kind == "missing_atom":
        changed = replace(old, atoms=old.atoms[:-1])
    elif kind == "missing_chain":
        changed = replace(old, chains=old.chains[:-1])
    elif kind == "missing_residue":
        with pytest.raises(ValueError, match="complete sequence positions"):
            replace(old.chains[0], residues=old.chains[0].residues[:-1])
        return
    elif kind == "operator":
        changed = replace(old, operators=old.operators[:-1])
    elif kind == "chemical":
        changed = replace(old, chemical_census=old.chemical_census[:-1])
    else:
        changed = replace(old, proposed_sequences=old.proposed_sequences[:-1])
    with pytest.raises(ValueError, match="independent"):
        independent.validate_observed_inventory(source, dossier, changed)


@pytest.mark.parametrize("kind", ["missing_view", "distance", "shell", "query_count"])
def test_independent_distances_and_full_shells_falsify_corrupt_products(exposed, kind):
    source, dossier, products = exposed
    old = products["inventory"]
    first = old.neighborhoods[0]
    if kind == "missing_view":
        changed = replace(old, neighborhoods=old.neighborhoods[:-1])
    elif kind == "distance":
        name, distance = first.other_chain_minima_angstrom[0]
        assert distance is not None
        altered = replace(first, other_chain_minima_angstrom=((name, distance+D(1)), *first.other_chain_minima_angstrom[1:]))
        changed = replace(old, neighborhoods=(altered, *old.neighborhoods[1:]))
    elif kind == "shell":
        radius, members = first.shells[0]
        altered = replace(first, shells=((radius, members+("fake.atom",)), *first.shells[1:]))
        changed = replace(old, neighborhoods=(altered, *old.neighborhoods[1:]))
    else:
        changed = replace(old, neighborhoods=(replace(first, query_atom_count=first.query_atom_count+1), *old.neighborhoods[1:]))
    with pytest.raises(ValueError, match="independent"):
        independent.validate_observed_inventory(source, dossier, changed)


def test_exact_historical_decimal_export_recovery_has_no_analysis_replay(exposed, monkeypatch):
    source, dossier, products = exposed
    inventory = products["inventory"]
    for name in ("analyze", "expand", "neighborhoods"):
        monkeypatch.setattr(science, name, forbidden)
    reconstructed, _, _, _ = independent.validate_observed_inventory(source, dossier, inventory)
    assert reconstructed == inventory and reconstructed.fingerprint() == inventory.fingerprint()
    recovered = science.assembly_coordinates(source, reconstructed)
    assert recovered.canonical_bytes() == products["coordinates"].canonical_bytes()
    independent.validate_coordinate_export(source, reconstructed, recovered)
    # Same numerical coordinate and rehashed file is not exact historical token
    # recovery; original spelling is retained, never normalized into new bytes.
    name, _, text = recovered.files[0]
    old_token = str(reconstructed.atoms[0].xyz_angstrom[0])
    normalized = str(D(old_token).normalize())
    assert old_token != normalized
    changed_text = text.replace(old_token, normalized, 1)
    changed = replace(recovered, files=((name, sha256(changed_text.encode()).hexdigest(), changed_text), recovered.files[1]))
    with pytest.raises(ValueError, match="coordinate export"):
        independent.validate_coordinate_export(source, reconstructed, changed)


def test_original_bytes_and_historical_canonical_records_remain_exact(exposed):
    source, _, products = exposed
    assert tuple((row.filename, row.sha256) for row in source.source_members) == c.ORIGINALS
    assert products["inventory"].fingerprint() == "a6d7af1a6f0e772ad857e5d3f9d313e2ff77c26bae0912a60b4740bedc966d8c"
    assert products["coordinates"].fingerprint() == "95d9f2237457e55fa11499b4bccf3d7a67b74b09f16e6a2747ebb03b9f799b8f"
    assert products["assessment"].fingerprint() == "a6e3c37015f4572ac8c971c1e6dc505e60b7849ed70f8cc2e8fc99333e79786c"
