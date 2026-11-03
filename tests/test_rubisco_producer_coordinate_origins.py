# SPDX-License-Identifier: MPL-2.0
"""Exposed origin permutations and falsifiers; no molecular/native evidence."""

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit import (
    realized_atom_origins,
    realized_atom_origins_from_coordinates,
)


def fixture():
    sources = [
        ("A", 1, "CA", "MET", "C", (0, 0, 0)),
        ("A", 1, "CB", "MET", "C", (1, 0, 0)),
        ("Z", 1, "O", "HOH", "O", (2, 0, 0)),
        ("Z", 2, "O", "HOH", "O", (4, 0, 0)),
    ]
    plan = dict(
        complete_chains=[dict(chain="A", sequence="M", subunit="ssu")],
        complete_heavy_atoms=[
            dict(chain=chain, position=position, atom=name, component=component,
                 element=element, source_origin=None)
            for chain, position, name, component, element, _ in sources
        ],
        authenticated_disulfides=[],
    )
    rows = [
        ("MET", [("CA", 6, (0, 0, 0)), ("CB", 6, (1, 0, 0)), ("H", 1, (0, 1, 0))]),
        ("WAT", [("O", 8, (4, 0, 0)), ("H1", 1, (4, 1, 0))]),
        ("WAT", [("O", 8, (2, 0, 0)), ("H1", 1, (2, 1, 0))]),
        ("Na+", [("NA", 11, (8, 0, 0))]),
    ]
    atoms, residues, points = [], [], []
    for residue_name, members in rows:
        residue = SimpleNamespace(idx=len(residues), name=residue_name, atoms=[])
        residues.append(residue)
        for name, number, xyz in members:
            atom = SimpleNamespace(idx=len(atoms), name=name, atomic_number=number, residue=residue)
            atoms.append(atom)
            residue.atoms.append(atom)
            points.append(tuple(Decimal(str(value)) + shift for value, shift in zip(xyz, (Decimal("10.1234567"), Decimal("20"), Decimal("30")), strict=True)))
    return SimpleNamespace(atoms=atoms, residues=residues, bonds=[]), plan, sources, points


def pdb(sources):
    return "".join(
        f"HETATM{index:5d} {name:>4s} {component:>3s} {chain}{position:4d}    "
        f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00          {element:>2s}\n"
        for index, (chain, position, name, component, element, xyz) in enumerate(sources, 1)
    ) + "END\n"


def restart(points):
    values = [value for point in points for value in point]
    text = f"EXPOSED ORIGIN JOIN ONLY\n{len(points):6d}\n"
    text += "".join("".join(f"{value:12.7f}" for value in values[start:start + 6]) + "\n" for start in range(0, len(values), 6))
    return text + "".join(f"{value:12.7f}" for value in (50, 50, 50, 90, 90, 90)) + "\n"


def assess(selected):
    structure, plan, sources, points = selected
    return realized_atom_origins_from_coordinates(structure, plan, pdb(sources), restart(points))


def add_atom(selected, residue_index, name, number, xyz, *, new_residue=None):
    structure, _, _, points = selected
    if new_residue is None:
        residue = structure.residues[residue_index]
    else:
        residue = SimpleNamespace(idx=len(structure.residues), name=new_residue, atoms=[])
        structure.residues.append(residue)
    atom = SimpleNamespace(idx=len(structure.atoms), name=name, atomic_number=number, residue=residue)
    structure.atoms.append(atom)
    residue.atoms.append(atom)
    points.append(xyz)


def test_successor_recovers_same_named_water_permutation_without_mutating_inputs():
    selected = fixture()
    structure, plan, _, _ = selected
    original_plan = deepcopy(plan)
    old = realized_atom_origins(structure, plan)
    assert "chemical_residue_map" not in old
    # The old join passes this invisible same-WAT permutation but misattributes O.
    assert next(row for row in old["atoms"] if row["chain"] == "Z" and row["position"] == 1)["amber_residue_index"] == 1
    result = assess(selected)
    assert result["chemical_residue_map"] == [
        dict(chain="Z", position=1, amber_residue_index=2),
        dict(chain="Z", position=2, amber_residue_index=1),
    ]
    joined = next(row for row in result["atoms"] if row["chain"] == "Z" and row["position"] == 1 and row["atom"] == "O")
    assert joined["amber_atom_index"] == 5 and joined["source_heavy_pdb_serial"] == 3
    assert [row["amber_atom_index"] for row in result["atoms"]] == list(range(8))
    assert result["coordinate_origin_join"]["source_heavy_atoms"] == 4
    assert result["coordinate_origin_join"]["complete_heavy_count"] == 4
    assert result["coordinate_origin_join"]["complete_source_group_count"] == 3
    assert result["coordinate_origin_join"]["full_protein_heavy_anchors"] == 2
    assert result["coordinate_origin_join"]["native_nonhydrogen_atoms"] == 5
    assert any(row["status"] == "DECLARED_AMBER_ADDED_HYDROGEN" for row in result["atoms"])
    assert any(row["status"] == "DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION" for row in result["atoms"])
    assert plan == original_plan
    assert [residue.name for residue in structure.residues] == ["MET", "WAT", "WAT", "Na+"]


@pytest.mark.parametrize("fault", ["ambiguous", "element", "component", "absence", "extra-heavy", "undeclared-addition"])
def test_successor_refuses_ambiguous_wrong_missing_and_unselected_chemistry(fault):
    selected = fixture()
    structure, _, _, points = selected
    if fault == "ambiguous":
        add_atom(selected, None, "O", 8, points[5], new_residue="WAT")
    elif fault == "element":
        structure.atoms[5].atomic_number = 7
    elif fault == "component":
        structure.residues[2].name = "CAP"
    elif fault == "absence":
        points[5] = (points[5][0] + 1, *points[5][1:])
    elif fault == "extra-heavy":
        add_atom(selected, 2, "C1", 6, tuple(value + 1 for value in points[5]))
    else:
        structure.residues[3].name = "CAP"
    with pytest.raises(ValueError):
        assess(selected)


def test_successor_refuses_split_and_reused_source_groups():
    selected = fixture()
    structure, plan, sources, points = selected
    source = dict(chain="Z", position=1, atom="C1", component="HOH", element="C", source_origin=None)
    plan["complete_heavy_atoms"].append(source)
    sources.append(("Z", 1, "C1", "HOH", "C", (6, 0, 0)))
    add_atom(selected, 1, "C1", 6, (points[0][0] + 6, points[0][1], points[0][2]))
    with pytest.raises(ValueError, match="splits"):
        assess(selected)
    # Move C1 into the native group selected for Z1, then move Z2's O there too.
    atom = structure.residues[1].atoms.pop()
    atom.residue = structure.residues[2]
    structure.residues[2].atoms.append(atom)
    other = structure.residues[1].atoms.pop(0)
    other.residue = structure.residues[2]
    structure.residues[2].atoms.append(other)
    with pytest.raises(ValueError, match="reuses a native chemical residue"):
        assess(selected)


def test_successor_refines_all_source_atoms_in_one_common_translation():
    selected = fixture()
    _, _, _, points = selected
    points[3] = (points[3][0] - Decimal("0.0000001"), *points[3][1:])
    points[5] = (points[5][0] + Decimal("0.0000001"), *points[5][1:])
    with pytest.raises(ValueError, match="common source translation"):
        assess(selected)


@pytest.mark.parametrize("fault", ["protein", "pdb-element", "pdb-component", "pdb-absence", "count", "nonfinite", "velocity"])
def test_successor_checks_full_protein_pdb_and_restart_denominators(fault):
    selected = fixture()
    structure, plan, sources, points = selected
    heavy, raw = pdb(sources), restart(points)
    if fault == "protein":
        points[1] = (points[1][0] + 1, *points[1][1:])
        raw = restart(points)
    elif fault == "pdb-element":
        heavy = heavy.replace("           O\n", "           N\n", 1)
    elif fault == "pdb-component":
        heavy = heavy.replace(" HOH ", " CAP ", 1)
    elif fault == "pdb-absence":
        heavy = "\n".join(heavy.splitlines()[:-2]) + "\nEND\n"
    elif fault == "count":
        raw = raw.replace("     8\n", "     9\n", 1)
    elif fault == "nonfinite":
        raw = raw.replace("  10.1234567", "         NaN", 1)
    else:
        raw += "".join(f"{0:12.7f}" for _ in range(6)) + "\n"
    with pytest.raises(ValueError):
        realized_atom_origins_from_coordinates(structure, plan, heavy, raw)


@pytest.mark.parametrize("mapping", [
    {}, {("Z", 1): 2}, {("Z", 1): 2, ("Z", 2): 2},
    {("Z", 1): 0, ("Z", 2): 1}, {("Z", 1): 2, ("Z", 2): 4},
    {("Z", 1): 2, ("Z", 2): True},
    {("Z", 1): 2, ("Z", 2): 1, ("Q", 1): 3},
])
def test_explicit_map_is_complete_unique_in_range_and_never_coordinate_proof(mapping):
    structure, plan, _, _ = fixture()
    with pytest.raises(ValueError):
        realized_atom_origins(structure, plan, chemical_residue_map=mapping)


def test_supplied_map_retains_genotype_element_and_addition_guards():
    structure, plan, _, _ = fixture()
    mapping = {("Z", 1): 2, ("Z", 2): 1}
    result = realized_atom_origins(structure, plan, chemical_residue_map=mapping)
    assert "coordinate_origin_join" not in result
    structure.residues[0].name = "VAL"
    with pytest.raises(ValueError, match="genotype"):
        realized_atom_origins(structure, plan, chemical_residue_map=mapping)
    structure.residues[0].name = "MET"
    structure.atoms[5].atomic_number = 7
    with pytest.raises(ValueError, match="element"):
        realized_atom_origins(structure, plan, chemical_residue_map=mapping)
    structure.atoms[5].atomic_number = 8
    structure.residues[3].name = "CAP"
    with pytest.raises(ValueError, match="undeclared"):
        realized_atom_origins(structure, plan, chemical_residue_map=mapping)


def test_successor_retains_authenticated_disulfide_atom_pairs():
    selected = fixture()
    structure, plan, sources, points = selected
    structure.residues[0].name = "CYS"
    structure.atoms[0].name, structure.atoms[0].atomic_number = "SG", 16
    sources[0] = ("A", 1, "SG", "CYS", "S", (0, 0, 0))
    sources[1] = ("A", 1, "CB", "CYS", "C", (1, 0, 0))
    plan["complete_heavy_atoms"][0].update(atom="SG", component="CYS", element="S")
    plan["complete_heavy_atoms"][1]["component"] = "CYS"
    plan["complete_heavy_atoms"].append(dict(chain="A", position=2, atom="SG", component="CYS", element="S", source_origin=None))
    sources.insert(2, ("A", 2, "SG", "CYS", "S", (6, 0, 0)))
    add_atom(selected, None, "SG", 16, (points[0][0] + 6, *points[0][1:]), new_residue="CYS")
    new_residue = structure.residues.pop()
    structure.residues.insert(1, new_residue)
    for index, residue in enumerate(structure.residues):
        residue.idx = index
    plan["complete_chains"][0]["sequence"] = "CC"
    plan["authenticated_disulfides"] = [dict(partners=(("A", 1), ("A", 2)))]
    structure.bonds = [SimpleNamespace(atom1=structure.atoms[0], atom2=structure.atoms[8])]
    assert assess(selected)["authenticated_disulfide_atom_pairs"] == [(0, 8)]
    structure.bonds = []
    with pytest.raises(ValueError, match="disulfide"):
        assess(selected)


@pytest.mark.parametrize("fault", ["source-duplicate", "source-mixed-component", "native-index", "residue-duplicate"])
def test_explicit_map_refuses_incoherent_source_and_native_identities(fault):
    structure, plan, _, _ = fixture()
    if fault == "source-duplicate":
        plan["complete_heavy_atoms"].append(deepcopy(plan["complete_heavy_atoms"][2]))
    elif fault == "source-mixed-component":
        plan["complete_heavy_atoms"][1]["component"] = "VAL"
    elif fault == "native-index":
        structure.atoms[5].idx = 3
    else:
        structure.residues[1].atoms.append(structure.atoms[5])
    with pytest.raises(ValueError):
        realized_atom_origins(structure, plan, chemical_residue_map={("Z", 1): 2, ("Z", 2): 1})
