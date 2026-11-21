# SPDX-License-Identifier: MPL-2.0
"""Tiny atom-table controls. These are deliberately not molecular models."""

from decimal import Decimal as D
from hashlib import sha256
import json
import struct

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.coordinate_plan import THREE
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularAtom, MolecularBond, MolecularRepresentation, MolecularResidue, MolecularSite
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_selection import ReactiveBoundary, ReactiveSelection
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests.test_rubisco_preparation_integrity import amber_text, topology
from tests.test_rubisco_physical_preparation_geometry import inpcrd


def raw_identity(name, raw):
    return ObjectIdentity(name, "empirical-lawhood/source/capture-assured-uninterpreted-public-bytes", "1.0.0", sha256(raw).hexdigest())


def representation(material, chemistry, *, name, gas="CO2", coincident=False):
    source = material.sources[0]
    residues, atoms, bonds = [], [], []
    site_chains = {row.lsu_chain_id: row.site_id for row in chemistry.sites}
    author_chains = {row.chain_id: chr(ord("A") + i) for i, row in enumerate(material.chains)}

    def add_residue(residue_id, component, role, names, numbers, *, chain=None, position=None, letter=None, site=None):
        author_chain, author_number = (author_chains[chain], position) if chain is not None else ("Z", len(residues) + 1)
        residues.append(MolecularResidue(residue_id, component, role, chain, position, letter,
            author_chain, author_number, "", source, site))
        result = []
        for atom_name, number in zip(names, numbers, strict=True):
            index = len(atoms)
            result.append(index)
            atom_id = residue_id + "." + atom_name.lower()
            atoms.append(MolecularAtom(atom_id, residue_id, atom_name, number,
                D({6: 12, 7: 14, 8: 16, 12: 24, 16: 32}[number]),
                D("0.12345678") if index == 0 else D(0), D("18.2223"), "CT", source, atom_id))
        bonds.extend(MolecularBond(a, b, D(1)) for a, b in zip(result[:-1], result[1:], strict=True))
        return tuple(result)

    for chain in material.chains:
        backbone = []
        for position, letter in enumerate(chain.sequence, 1):
            residue_id = f"residue.{chain.chain_id}.{position}"
            site = site_chains.get(chain.chain_id) if letter == "K" else None
            component = "KCX" if site and next(row for row in chemistry.sites if row.site_id == site).carbamylated else THREE[letter]
            names, numbers = ["CA"], [6]
            if chain.subunit == "SSU" and position == 2:
                names.append("SD" if letter == "M" else "CG2")
                numbers.append(16 if letter == "M" else 6)
            added = add_residue(residue_id, component, "PROTEIN", names, numbers,
                chain=chain.chain_id, position=position, letter=letter, site=site)
            backbone.append(added[0])
        bonds.extend(MolecularBond(a, b, D(1)) for a, b in zip(backbone[:-1], backbone[1:], strict=True))
    sites = []
    for selected in chemistry.sites:
        magnesium = add_residue("residue." + selected.site_id + ".mg", "MG", "MAGNESIUM", ("MG",), (12,), site=selected.site_id)
        ligand = add_residue("residue." + selected.site_id + ".ligand", "CAB" if selected.ligand_state == "CABP" else "RBP",
            "LIGAND", ("C", "O"), (6, 8), site=selected.site_id)
        gas_atoms = ()
        if selected == chemistry.sites[0]:
            gas_atoms = add_residue("residue." + selected.site_id + ".gas", gas, "GAS",
                ("C", "O1", "O2") if gas == "CO2" else ("O1", "O2"), (6, 8, 8) if gas == "CO2" else (8, 8), site=selected.site_id)
        sites.append(MolecularSite(selected.site_id,
            f"residue.{selected.lsu_chain_id}.{selected.catalytic_lysine_position_1based}",
            magnesium, ligand, gas_atoms, (), selected.ligand_chemical_graph))
    bonds = tuple(sorted(bonds, key=lambda row: (row.first, row.second)))
    sections = topology()
    n = len(atoms)
    sections["POINTERS"][0] = n
    sections["POINTERS"][2] = 0
    sections["POINTERS"][3] = len(bonds)
    sections["POINTERS"][10] = n
    sections["POINTERS"][11] = len(residues)
    sections["POINTERS"][27] = 1
    starts = [i + 1 for i, atom in enumerate(atoms) if i == 0 or atom.residue_id != atoms[i - 1].residue_id]
    sections.update(ATOM_NAME=[atom.name for atom in atoms], AMBER_ATOM_TYPE=[atom.parameter_type for atom in atoms],
        ATOMIC_NUMBER=[atom.atomic_number for atom in atoms], MASS=[atom.mass_dalton for atom in atoms],
        CHARGE=[atom.charge_native for atom in atoms], ATOM_TYPE_INDEX=[1] * n,
        RESIDUE_LABEL=[row.component for row in residues], RESIDUE_POINTER=starts,
        NUMBER_EXCLUDED_ATOMS=[1] * n, EXCLUDED_ATOMS_LIST=[0] * n,
        BOX_DIMENSIONS=[D(90), D(1000), D(1000), D(1000)],
        BONDS_INC_HYDROGEN=[], BONDS_WITHOUT_HYDROGEN=[value for row in bonds for value in (3 * row.first, 3 * row.second, 1)])
    raw_topology = amber_text(sections).encode("ascii")
    points = tuple((D(i), D(i % 2), D(i % 3)) for i in range(n))
    if coincident:
        points = (points[0], points[0], *points[2:])
    coordinates = inpcrd(points, box=(1000, 1000, 1000, 90, 90, 90)).encode("ascii")
    array_bytes = b"".join(struct.pack("<ddd", *(float(value) for value in point)) for point in points)
    top = raw_identity(name + ".topology", raw_topology)
    xyz = raw_identity(name + ".coordinates", coordinates)
    arrays = ArrayDatasetManifest(name + ".arrays",
        (ArrayDatasetMember("coordinates-angstrom", "<f8", (n, 3), sha256(array_bytes).hexdigest()),),
        tuple(sorted((top, xyz), key=lambda row: row.object_id)))
    result = MolecularRepresentation(name, material, chemistry, D("298.15"), source, source, top, xyz,
        tuple(sorted(residues, key=lambda row: row.residue_id)), tuple(atoms), bonds, tuple(sites), arrays,
        tuple(sorted({source, top, xyz, *chemistry.sources}, key=lambda row: row.object_id)))
    return result, raw_topology, coordinates


def geometry_files(model, top, xyz):
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.physical_preparation_geometry import read_inpcrd
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_assessment import RetainedMolecularGeometry
    points, _, _ = read_inpcrd(xyz.decode(), len(model.atoms))
    residues = {row.residue_id: row for row in model.residues}
    lines, origin_rows, seen = [], [], {}
    for i, (atom, point) in enumerate(zip(model.atoms, points, strict=True)):
        residue = residues[atom.residue_id]
        seen.setdefault(residue.residue_id, len(seen))
        element = {6: "C", 7: "N", 8: "O", 12: "MG", 16: "S"}[atom.atomic_number]
        x, y, z = map(float, point)
        lines.append(f"ATOM  {i+1:5d} {atom.name:^4s} {residue.component:>3s} {residue.author_chain}{residue.author_number:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {element:>2s}  \n")
        origin_rows.append(dict(amber_atom_index=i, amber_residue_index=seen[residue.residue_id],
            atom=atom.name, residue_name=residue.component, chain=residue.author_chain, position=residue.author_number,
            status="REALIZED_COMPLETE_PREPARATION_ATOM", source_origin={"declared": "EXPOSED_SOFTWARE_ATOM_ONLY"}))
    raw = dict(topology=top, coordinates=xyz, heavy_atoms="".join(lines).encode("ascii"),
        origins=json.dumps({"amber_realization": {"atoms": origin_rows}}, sort_keys=True).encode("ascii"))
    evidence = [FileEvidence(key + ".raw", len(raw[key]), sha256(raw[key]).hexdigest())
                for key in ("topology", "coordinates", "heavy_atoms", "origins")]
    return RetainedMolecularGeometry(model.representation_id + ".geometry", model.identity, *evidence), raw


def chemical_graphs(chemistry):
    from dataclasses import replace
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import LigandAtom, LigandChemicalGraph
    source = chemistry.sources[0]
    graph = LigandChemicalGraph("graph.disclosed." + chemistry.sites[0].ligand_state.lower(),
        chemistry.sites[0].ligand_state, (LigandAtom("atom.c", "C", 6, 0), LigandAtom("atom.o", "O", 8, 0)),
        (MolecularBond(0, 1, D(1)),), 0, (source,))
    selected = replace(chemistry, sites=tuple(replace(row, ligand_chemical_graph=graph.identity) for row in chemistry.sites),
        sources=tuple(sorted({*chemistry.sources, graph.identity}, key=lambda row: row.object_id)))
    return selected, (graph,)


def ligand_bindings(model):
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import SiteLigandBinding
    return tuple(SiteLigandBinding(row.site_id, row.chemical_graph, row.ligand_atom_indices) for row in model.sites)


def pair():
    supplied = disclosed_supply()
    before = representation(supplied.case.parent, supplied.context.chemistry, name="molecular.disclosed.wt")
    after = representation(supplied.case.mutant, supplied.context.chemistry, name="molecular.disclosed.mutant")
    return supplied.case, before, after


def common_atoms(before, after):
    by_key = {(row.residue_id, row.name, row.atomic_number): i for i, row in enumerate(after.atoms)}
    return tuple((i, by_key[key]) for i, row in enumerate(before.atoms)
        if (key := (row.residue_id, row.name, row.atomic_number)) in by_key)


def reactive(model, *, gas="CO2"):
    site = model.sites[0]
    qm = {i for i, row in enumerate(model.atoms) if row.residue_id == site.catalytic_residue_id}
    qm.update((*site.magnesium_atom_indices, *site.ligand_atom_indices, *site.gas_atom_indices))
    cuts = sorted((row.first, row.second) if row.first in qm else (row.second, row.first)
        for row in model.bonds if (row.first in qm) != (row.second in qm))
    source = model.material.sources[0]
    boundaries = tuple(ReactiveBoundary(f"link.{i:02}", a, b, 1, D("1.09"), source) for i, (a, b) in enumerate(cuts))
    electrons = sum(model.atoms[i].atomic_number for i in qm) + len(boundaries)
    return ReactiveSelection("reactive.disclosed", model.identity, len(model.atoms), site.site_id,
        tuple(sorted(qm)), tuple(i for i in range(len(model.atoms)) if i not in qm), boundaries,
        gas, site.gas_atom_indices, 0, 1 + electrons % 2, source, None, source, source,
        "FIXED_FULL_ASSEMBLY_FIELD", (source,))
