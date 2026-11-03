# SPDX-License-Identifier: MPL-2.0
"""Native source/scaffold conformance; no atom completion or kinetic assessment."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_preparation as rr


FIXTURE = Path(__file__).parent / "fixtures/rubisco/rr9rub"
PINNED = (
    ("9RUB.cif", 774540, "33242f8e519c2e032c5a83de33a6350eb5c38cef42b5a14e1f8ecfb9230575dd"),
    ("9RUB.pdb", 634878, "80dcc3cfdcd12154f1d7c21e9438b9e6b0e9d887381aeeef6f2350b3e1b41fd5"),
    ("P04718.fasta", 581, "d7edfcdad62964ce96ec766ca4bd83e115c19ee257585c9014f07b7d325e48d0"),
)


@pytest.fixture(scope="module")
def originals():
    values = tuple((FIXTURE / name).read_bytes() for name, _, _ in PINNED)
    for value, (_, size, digest) in zip(values, PINNED, strict=True):
        assert len(value) == size and sha256(value).hexdigest() == digest
    return values


@pytest.fixture(scope="module")
def source(originals):
    return rr.decode_rr_source(*originals)


def pdb_rows(raw):
    """Independent fixed-column read, with no production lexer or source parser."""
    return tuple(line for line in raw.decode("ascii").splitlines()
                 if line.startswith(("ATOM  ", "HETATM")))


def substitute_pin(monkeypatch, index, value):
    """Only deliberate software-fixture pins change; actual retained bytes do not."""
    pins = list(rr.SOURCE_PINS)
    pins[index] = (pins[index][0], len(value), sha256(value).hexdigest())
    monkeypatch.setattr(rr, "SOURCE_PINS", tuple(pins))


def test_exact_native_full_census_and_independent_coordinate_correspondence(source, originals):
    rows = pdb_rows(originals[1])
    assert rr.SOURCE_PINS == PINNED and source.source_bindings == PINNED
    assert len(rows) == len(source.atoms) == 7044
    assert Counter(line[17:20].strip() for line in rows if line.startswith("HETATM")) == {
        "FMT": 6, "MG": 2, "RUB": 36,
    }
    for atom, line in zip(source.atoms, rows, strict=True):
        assert atom.pdb_line == line
        assert atom.pdb_serial == line[6:11].strip()
        assert atom.coordinate_tokens == tuple(line[a:b].strip() for a, b in ((30, 38), (38, 46), (46, 54)))
        assert atom.coordinates_angstrom == tuple(Decimal(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54)))
    assert not source.native_water_atoms and not source.exact_assay_parent_admitted


def test_native_bonds_are_actual_covalent_k191_fmt_and_mg_rubp_joins(source, originals):
    independent = {(line[21], int(line[22:26]), line[17:20].strip(), line[12:16].strip()): line
                   for line in pdb_rows(originals[1])}
    by_id = {a.source_id: a for a in source.atoms}
    assert len(source.bonds) == 11
    joins = []
    for bond in source.bonds:
        if bond.kind != "covale":
            continue
        a, b = by_id[bond.first_source_id], by_id[bond.second_source_id]
        assert (a.component, a.author_position, a.atom_name, b.component, b.atom_name) == (
            "LYS", 191, "NZ", "FMT", "C",
        )
        assert a.author_chain == b.author_chain
        for atom in (a, b):
            native = independent[(atom.author_chain, atom.author_position, atom.component, atom.atom_name)]
            assert atom.coordinates_angstrom == tuple(Decimal(native[start:stop])
                                                     for start, stop in ((30, 38), (38, 46), (46, 54)))
        joins.append(a.author_chain)
    assert sorted(joins) == ["A", "B"]
    assert source.sequence_conflicts == ((91, "H", "D"),)
    assert source.reference_sequence[90] == "H" and source.native_sequence[90] == "D"
    assert {dict(row)["details"] for row in source.native_conflict_rows} == {"conflict"}


def test_hash_first_and_original_size_refusal_before_any_parser(originals, monkeypatch):
    def forbidden(*args):
        raise AssertionError("parser entered before source seal")
    monkeypatch.setattr(rr, "_source_facts", forbidden)
    for index in range(3):
        tampered = list(originals)
        tampered[index] = originals[index][:-1] + b"!"
        with pytest.raises(ValueError, match="original source bytes differ"):
            rr.decode_rr_source(*tampered)
    with pytest.raises(ValueError, match="byte bound"):
        rr.decode_rr_source(b"x" * (rr.SOURCE_MAXIMUM_BYTES + 1), originals[1], originals[2])
    with pytest.raises(ValueError, match="byte bound or type"):
        rr.decode_rr_source(bytearray(originals[0]), originals[1], originals[2])


@pytest.mark.parametrize("defect", ["serial", "coordinate", "missing-atom", "atom-identity"])
def test_independent_pdb_witness_defects_refuse_even_under_software_fixture_pin(originals, monkeypatch, defect):
    lines = originals[1].decode("ascii").splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.startswith(("ATOM  ", "HETATM"))]
    first, second = indices[:2]
    if defect == "serial":
        lines[second] = lines[second][:6] + lines[first][6:11] + lines[second][11:]
        message = "duplicate native PDB atom serial"
    elif defect == "coordinate":
        lines[first] = lines[first][:30] + "  43.288" + lines[first][38:]
        message = "exact coordinate tokens mismatch"
    elif defect == "missing-atom":
        del lines[first]
        message = "atom census differs"
    else:
        lines[first] = lines[first][:12] + "  CA" + lines[first][16:]
        message = "atom identity mismatch"
    altered = "".join(lines).encode("ascii")
    substitute_pin(monkeypatch, 1, altered)
    with pytest.raises(ValueError, match=message):
        rr.decode_rr_source(originals[0], altered, originals[2])


def test_duplicate_missing_and_corrupt_native_connections_refuse(source):
    atoms = source.atoms
    rows = tuple(a.native_tokens for a in atoms)
    pdb_atoms = tuple((a.pdb_line_number, a.pdb_line) for a in atoms)
    duplicate = list(rows)
    duplicate[1] = tuple((k, atoms[0].source_id if k == "id" else v) for k, v in duplicate[1])
    with pytest.raises(ValueError, match="duplicate native CIF atom ID"):
        rr._crossmap(tuple(duplicate), pdb_atoms)
    with pytest.raises(ValueError, match="atom census differs"):
        rr._crossmap(rows[:-1], pdb_atoms)
    bad_element = tuple((k, "H" if k == "type_symbol" else v) for k, v in rows[0])
    with pytest.raises(ValueError, match="heavy-element census"):
        rr.RrNativeAtomV1(bad_element, atoms[0].pdb_line_number, atoms[0].pdb_line)


def test_native_covalent_endpoint_corruption_refuses(originals, monkeypatch):
    lines = originals[0].decode("ascii").splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.startswith("covale1 ")]
    assert len(matches) == 1
    i = matches[0]
    fields = lines[i].split()
    tables, _ = rr._tables(originals[0])
    columns = tuple(k for k, _ in tables["_struct_conn"][0])
    assert fields[columns.index("ptnr2_label_atom_id")] == "C"
    fields[columns.index("ptnr2_label_atom_id")] = "O1"
    lines[i] = " ".join(fields) + "\n"
    altered = "".join(lines).encode("ascii")
    substitute_pin(monkeypatch, 0, altered)
    with pytest.raises(ValueError, match="covalent activation join differs"):
        rr.decode_rr_source(altered, originals[1], originals[2])


@pytest.mark.parametrize("payload", [
    b"data_9RUB\n_entry.id 9RUB\n_entry.id 9RUB\n",
    b"data_9RUB\nloop_\n_atom_site.id\n_atom_site.id\n1 2\n",
    b"data_9RUB\nloop_\n_atom_site.id\n_atom_site.type_symbol\n1 C 2\n",
    b"data_9RUB\n_entry.id\n;unterminated\n",
])
def test_bounded_native_lexical_shape_errors_refuse(payload):
    with pytest.raises(ValueError):
        rr._tables(payload)


def test_source_facts_and_scaffold_derivations_cannot_be_injected(source):
    with pytest.raises(FrozenInstanceError):
        source.atoms = ()
    with pytest.raises(ValueError, match="init=False"):
        replace(source, atoms=())
    scaffold = rr.project_rr_scaffold(source, reference_choice="deposited-D91", variant="unedited-reference")
    with pytest.raises(ValueError, match="init=False"):
        replace(scaffold, atoms=())
    with pytest.raises(ValueError, match="selection differs"):
        rr.project_rr_scaffold(source, reference_choice="WT-by-assertion", variant="unedited-reference")
    with pytest.raises(ValueError, match="selection differs"):
        rr.project_rr_scaffold(source, reference_choice="deposited-D91", variant="M100T")


def test_common_scaffold_complete_source_partition_and_independent_boundary_counts(source, originals):
    scaffold = rr.project_rr_scaffold(source, reference_choice="deposited-D91", variant="unedited-reference")
    independent = pdb_rows(originals[1])
    positive = [line for line in independent if Decimal(line[54:60]) == 1]
    expected = [line for line in positive if line.startswith("HETATM") or 2 <= int(line[22:26]) <= 459]
    assert len(scaffold.atoms) == len(expected) == 7034
    assert scaffold.protein_residues == 916
    assert len(scaffold.omitted_atoms) == 10 and not scaffold.removed_atoms
    assert Counter(a.reason for a in scaffold.omitted_atoms) == {
        "native-zero-occupancy": 9, "outside-common-author-interval-2-through-459": 1,
    }
    partition = [a.source_atom.source_id for a in scaffold.atoms]
    partition += [a.source_atom.source_id for a in scaffold.omitted_atoms + scaffold.removed_atoms]
    assert len(partition) == len(set(partition)) == 7044
    assert set(partition) == {a.source_id for a in source.atoms}
    assert scaffold.outside_boundary_polymer_positions == tuple(
        (chain, position) for chain in ("A", "B") for position in (1, 460, 461, 462, 463, 464, 465, 466)
    )
    assert len(source.missing_residue_rows) == 15
    assert source.missing_heavy_atoms == (rr.RrMissingHeavyAtomsV1("A", 460, "THR", ("CB", "CG2", "OG1")),)


def test_kcx_rename_retains_every_source_coordinate_and_both_full_ligands(source):
    scaffold = rr.project_rr_scaffold(source, reference_choice="deposited-D91", variant="unedited-reference")
    for chain in ("A", "B"):
        kcx = [a for a in scaffold.atoms if a.chain == chain and a.component == "KCX"]
        assert len(kcx) == 12
        fmt = {a.source_atom.atom_name: a for a in kcx if a.source_atom.component == "FMT"}
        assert {k: a.atom_name for k, a in fmt.items()} == {"C": "CX", "O1": "OQ1", "O2": "OQ2"}
        assert all(a.author_position == 191 for a in kcx)
        assert Counter(a.source_atom.element for a in scaffold.atoms if a.chain == chain and a.component == "RUB") == {
            "C": 5, "O": 11, "P": 2,
        }
        assert len([a for a in scaffold.atoms if a.chain == chain and a.component == "MG" and a.author_position == 601]) == 1
    assert len(scaffold.renamed_source_ids) == 44
    for atom in scaffold.atoms:
        assert atom.coordinate_tokens == atom.source_atom.coordinate_tokens
        assert atom.coordinates_angstrom == atom.source_atom.coordinates_angstrom
    assert scaffold.inferred_quantum_region_charge is scaffold.inferred_spin is None
    assert not scaffold.added_atom_coordinates and not scaffold.exact_assay_parent_admitted
    assert scaffold.completed_qm_contexts == 0 and len(scaffold.later_context_roster) == 6


@pytest.mark.parametrize("variant,position,removed_count,kept_count", [
    ("D263N", 263, 6, 7022), ("H287N", 287, 10, 7018),
])
def test_real_mutant_removals_and_required_asn_atoms_in_both_chains(source, variant, position, removed_count, kept_count):
    scaffold = rr.project_rr_scaffold(source, reference_choice="modeled-H91", variant=variant)
    edits = [r for r in scaffold.sidechain_constructions if r.author_position == position]
    assert {r.chain for r in edits} == {"A", "B"}
    assert all(r.required_component == "ASN" and r.required_new_heavy_atoms == (
        ("CG", "C"), ("ND2", "N"), ("OD1", "O"),
    ) for r in edits)
    assert sum(len(r.removed_source_ids) for r in edits) == removed_count
    assert len(scaffold.atoms) == kept_count
    assert len(scaffold.removed_atoms) == removed_count + 6
    for chain in ("A", "B"):
        selected = [a for a in scaffold.atoms if a.chain == chain and a.author_position == position]
        assert {a.atom_name for a in selected} == {"N", "CA", "C", "O", "CB"}
        assert {a.component for a in selected} == {"ASN"}
        assert all(a.coordinate_tokens == a.source_atom.coordinate_tokens for a in selected)
    assert not scaffold.added_atom_coordinates


def test_h91_reconstruction_is_explicit_incomplete_and_no_histidine_proton_state_is_assigned(source):
    deposited = rr.project_rr_scaffold(source, reference_choice="deposited-D91", variant="unedited-reference")
    modeled = rr.project_rr_scaffold(source, reference_choice="modeled-H91", variant="unedited-reference")
    assert {a.component for a in deposited.atoms if a.author_position == 91} == {"ASP"}
    assert {a.component for a in modeled.atoms if a.author_position == 91} == {"HIS"}
    assert len(modeled.atoms) == 7028 and len(modeled.removed_atoms) == 6
    assert {s.chain for s in modeled.sidechain_constructions} == {"A", "B"}
    assert all(s.required_new_heavy_atoms == (("CD2", "C"), ("CE1", "C"), ("CG", "C"),
                                             ("ND1", "N"), ("NE2", "N"))
               for s in modeled.sidechain_constructions)
    assert not {a.component for a in modeled.atoms} & {"HID", "HIE", "HIP"}
    assert not modeled.exact_assay_parent_admitted


def test_native_decimal_tokens_do_not_depend_on_ambient_rounding(source):
    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        scaffold = rr.project_rr_scaffold(source, reference_choice="modeled-H91", variant="D263N")
        assert scaffold.atoms[0].coordinates_angstrom == (Decimal("43.287"), Decimal("-13.458"), Decimal("4.470"))
        assert scaffold.atoms[0].coordinate_tokens == ("43.287", "-13.458", "4.470")


def test_cold_import_does_not_load_optional_physical_or_array_dependencies():
    code = '''
import importlib.abc
import sys
blocked = {"Bio", "openmm", "parmed", "pdbfixer", "pyscf", "numpy", "scipy", "h5py", "pyarrow"}
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise AssertionError("optional import: " + fullname)
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_preparation
assert len(rr_preparation.LATER_CONTEXT_ROSTER) == 6
assert not blocked.intersection(sys.modules)
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
