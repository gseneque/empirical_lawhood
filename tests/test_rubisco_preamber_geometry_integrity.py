# SPDX-License-Identifier: MPL-2.0
"""Exposed lexical/origin cases; none is an authentic molecular preparation."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preamber_geometry_integrity import (
    PreAmberGeometryIntegrity, assess, validate_geometry_origins,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_heavy_pdb import (
    read_heavy_pdb, read_serialized_heavy_pdb,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition
from tests.test_rubisco_preparation_integrity import full_exposed_origins


def atom(serial, atom_name="CA", chain="A", position=1, component="ALA"):
    return f"ATOM  {serial:5d} {atom_name:^4} {component:>3} {chain}{position:4d}       1.000   2.000   3.000  1.00  0.00           C  \n"


def ter(serial, chain="A", position=1, component="ALA"):
    return f"TER   {serial:5d}      {component:>3} {chain}{position:4d}\n"


def tiny():
    return atom(1) + atom(2, "CB") + ter(3) + atom(4, chain="B") + ter(5, chain="B")


def test_original_serials_ter_scope_and_directed_bond_multiplicity_are_retained():
    raw = tiny() + "CONECT    1    2    2\nCONECT    2    1    1\nEND\n"
    parsed = read_serialized_heavy_pdb(raw)
    assert tuple(row["serial"] for row in parsed.atoms) == (1, 2, 4)
    assert tuple(row["serial"] for row in parsed.ters) == (3, 5)
    assert parsed.directed_bonds == ((1, 2), (1, 2), (2, 1), (2, 1))
    assert read_heavy_pdb(raw) == parsed.atoms
    assert raw.endswith("CONECT    2    1    1\nEND\n")


@pytest.mark.parametrize("raw", (
    atom(1) + atom(3, "CB"),
    atom(2),
    atom(1) + atom(1, "CB"),
    atom(1) + ter(2, chain="B"),
    atom(1) + ter(2) + ter(3),
    atom(1) + ter(2) + atom(3, "CB"),
    atom(1) + ter(2, position=2),
    atom(1) + ter(2, component="GLY"),
    ter(1) + atom(2),
    atom(1) + atom(2),
    atom(1, chain="B") + atom(2),
    atom(1, position=2) + atom(2),
    atom(1) + "CONECT    1    2\n",
    tiny() + "CONECT    1    3\n",
    tiny() + "CONECT    1    1\n",
    tiny() + "CONECT    1\n",
    tiny() + "CONECT 1 2\n",
    atom(1) + "MODEL        2\n",
    atom(1) + "ENDMDL\n",
    atom(1) + "END\n" + atom(2, "CB"),
    tiny() + "CONECT    1    2\n" + atom(6, chain="C"),
    atom(1).replace("1.000", "  NaN"),
    atom(1).replace("1.000", "  Inf"),
    atom(1).replace(" C  ", " H  "),
    atom(1).replace(" C  ", "    "),
    atom(1)[:16] + "A" + atom(1)[17:],
    atom(1)[:26] + "A" + atom(1)[27:],
))
def test_missing_duplicate_reordered_ambiguous_and_foreign_references_refuse(raw):
    with pytest.raises(ValueError):
        read_serialized_heavy_pdb(raw)


def exposed_full_geometry():
    """Reuse exposed 5048 one-CA residues, no chemistry-completeness claim."""
    model, _, origin, raw, atoms, chains = full_exposed_origins()
    for source_atom in atoms:
        source_atom.element = "C"
    origin.pop("amber_realization")
    origin["joint_view_id"] = model.joint_view_id
    for declared in origin["complete_chains"]:
        declared["actual_residue_names"] = [row["component"] for row in origin["complete_heavy_atoms"] if row["chain"] == declared["chain"]]
    rows, serial = [], 0
    raw_lines = raw.splitlines()
    for index, line in enumerate(raw_lines):
        serial += 1
        rows.append(line[:6] + f"{serial:5d}" + line[11:] + "\n")
        if index == len(raw_lines) - 1 or line[21] != raw_lines[index + 1][21]:
            serial += 1
            rows.append(ter(serial, line[21], int(line[22:26]), line[17:20]))
    return model.construct, model.joint_view_id, origin, "".join(rows), atoms, chains


def test_full_l8s8_source_genotype_and_origins_without_fictitious_amber_data():
    args = exposed_full_geometry()
    counts = validate_geometry_origins(*args, set())
    assert counts == dict(atom_count=5048, protein_residue_count=5048, residue_count=5048,
        inherited_atom_count=16, constructed_atom_count=5032, ter_count=16,
        conect_row_count=0, directed_conect_term_count=0, source_disulfide_count=0)
    assert "amber_realization" not in args[2]


@pytest.mark.parametrize("change", (
    "joint", "chain", "sequence", "actual-residue", "source-token", "selected-missing",
    "constructed-observed", "inherited-role", "origin-element", "origin-order",
    "origin-missing", "raw-missing", "raw-genotype", "source-element", "disulfide-added", "extra-intervention",
))
def test_pre_amber_source_genotype_origin_full_denominator_falsifiers(change):
    construct, joint, origin, raw, atoms, chains = exposed_full_geometry()
    if change == "joint": origin["joint_view_id"] = "joint-02"
    if change == "chain": origin["complete_chains"][0]["source_chain"] = "foreign"
    if change == "sequence": origin["complete_chains"][0]["sequence"] = "G" + origin["complete_chains"][0]["sequence"][1:]
    if change == "actual-residue": origin["complete_chains"][0]["actual_residue_names"][0] = "GLY"
    if change == "source-token": origin["selected_atom_origins"][0]["original_xyz_angstrom"][0] = "1.000"
    if change == "selected-missing": origin["selected_atom_origins"].pop()
    if change == "constructed-observed": origin["complete_heavy_atoms"][1]["source_origin"] = deepcopy(origin["selected_atom_origins"][0])
    if change == "inherited-role": origin["complete_heavy_atoms"][0]["status"] = "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM"
    if change == "origin-element": origin["complete_heavy_atoms"][0]["element"] = "N"
    if change == "origin-order": origin["complete_heavy_atoms"][:2] = reversed(origin["complete_heavy_atoms"][:2])
    if change == "origin-missing": origin["complete_heavy_atoms"].pop()
    if change == "raw-missing": raw = "\n".join(raw.splitlines()[1:]) + "\n"
    if change == "raw-genotype": raw = raw[:17] + "GLY" + raw[20:]
    if change == "source-element": atoms[0].element = "N"
    if change == "disulfide-added": origin["authenticated_disulfides"] = [{"partners": [["A", 1], ["B", 1]]}]
    if change == "extra-intervention": construct = replace(construct, lsu_sequence="G" + construct.lsu_sequence[1:])
    with pytest.raises(ValueError):
        validate_geometry_origins(construct, joint, origin, raw, atoms, chains, set())


def selected_assessment():
    import json

    construct, joint, origin, raw, atoms, chains = exposed_full_geometry()
    heavy, provenance = raw.encode(), json.dumps(origin).encode()
    geometry = "geometry." + construct.construct_id + "." + joint
    def identity(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, "1.0.0", sha256(name.encode()).hexdigest())
    return assess(product_id="assessment.exposed.pre-amber", source=identity("source.exposed", c.PreparationSelection),
        geometry_definition=identity(geometry, NativeSubworkDefinition), geometry_completion=identity("completion.exposed", NativeSubworkCompletion),
        geometry_receipt=identity("receipt.exposed", CanonicalTaskReceipt), construct=construct, joint_view_id=joint,
        heavy_file=c.FileEvidence(geometry + "/complete-heavy.pdb", len(heavy), sha256(heavy).hexdigest()),
        origin_file=c.FileEvidence(geometry + "/atom-origin-provenance.json", len(provenance), sha256(provenance).hexdigest()),
        heavy_bytes=heavy, origin_bytes=provenance, source_atoms=atoms, source_chains=chains, expected_disulfides=set())


def test_typed_reuse_result_preserves_parents_and_denominators_but_no_downstream_claims():
    result = selected_assessment()
    assert result.source_origin_disposition is A.SATISFIED
    assert result.physical_geometry_disposition is result.amber_assignment_disposition is A.UNEVALUABLE
    assert decode_canonical_bytes(result.canonical_bytes(), PreAmberGeometryIntegrity, maximum_bytes=len(result.canonical_bytes())) == result
    for changes in (
        dict(constructed_atom_count=0), dict(protein_residue_count=1), dict(atom_count=-1),
        dict(physical_geometry_disposition=A.SATISFIED), dict(amber_assignment_disposition=A.SATISFIED),
        dict(covalent_completeness_disposition=A.SATISFIED), dict(physical_independent_units=1),
        dict(joint_view_id="joint-02"), dict(geometry_receipt=None),
    ):
        with pytest.raises(ValueError):
            replace(result, **changes)
