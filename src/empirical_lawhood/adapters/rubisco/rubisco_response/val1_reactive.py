# SPDX-License-Identifier: MPL-2.0
"""Amber parsing and observed-core preparation from already authenticated parent files."""

from fractions import Fraction
import json

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import (
    proper_rigid_fit,
)
from empirical_lawhood.domains.rubisco.rubisco_response.observed_core_partition import (
    ObservedCorePartition,
)
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import (
    read_prmtop_lines,
)
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


MATERIALS = ("V1-WT", "V1-I95M")


def stock_gas(gas, paths):
    """Get LJ coefficients and natural masses from the original source tokens."""
    prepi, frcmod = paths["gas-prepi"], paths["gas-frcmod"]
    masses, lj = {}, {}
    section = None
    for line in (
        read_bounded_bytes(frcmod, maximum_bytes=128 * 1024)
        .decode("ascii")
        .splitlines()
    ):
        tokens = line.split()
        if len(tokens) == 1:
            section = tokens[0]
        elif len(tokens) == 3 and section == "MASS":
            masses[tokens[0]] = float(tokens[1])
        elif len(tokens) == 3 and section == "NONBON":
            lj[tokens[0]] = (
                2 * float(tokens[1]) / 2 ** (1 / 6) / 10,
                float(tokens[2]) * 4.184,
            )
    rows = [
        line.split()
        for line in read_bounded_bytes(prepi, maximum_bytes=128 * 1024)
        .decode("ascii")
        .splitlines()
    ]
    species = ("C1", "O1", "O2") if gas == "CO2" else ("O1", "O2")
    result = []
    for name in species:
        (row,) = [r for r in rows if len(r) == 11 and r[1] == name]
        result.append((name[0], masses[row[2]], float(row[-1]), *lj[row[2]]))
    return result


def source_scales(prmtop):
    """Read Amber's effective proper torsions through OpenMM's original parser."""
    return {
        tuple(sorted((a, b))): Fraction(str(scee))
        for a, b, _, _, _, scee, _ in prmtop.get14Interactions()
    }


def prepare_material(paths, case, meta, completion):
    import openmm as mm
    from openmm import app, unit

    if case not in MATERIALS:
        raise ValueError("Unknown observed core")
    states = json.loads(read_bounded_bytes(paths["states"], maximum_bytes=32 * 1024**2))
    (material,) = [m for m in states["materials"] if m["case"] == case]
    (card,) = [s for s in states["states"] if s["name"] == f"{case}-wet-O-I"]
    if (
        meta["case"] != case
        or material["case"] != card["case"]
        or card["hydration"] != "wet"
    ):
        raise ValueError("observed core material and physical state card disagree")
    top = app.AmberPrmtopFile(str(paths["topology"]))
    if (
        completion["steps"] != 20000
        or completion["timestep_ps"] != 0.001
        or completion["temperature_K"] != 298.15
        or completion["seed"] != 11031
    ):
        raise ValueError("observed core requires the original 20 ps hydrated parent")
    with np.load(paths["thermal"], allow_pickle=False) as f:
        xyz, cell = f["coordinates_A"].copy(), f["box_A"].copy()
    atoms = list(top.topology.atoms())
    n = len(atoms)
    if (
        n != completion["N"]
        or xyz.shape != (n, 3)
        or cell.shape != (3, 3)
        or xyz.dtype.kind != "f"
        or cell.dtype.kind != "f"
        or not np.isfinite(xyz).all()
    ):
        raise ValueError("Invalid conditioned Amber coordinates or periodic cell")
    box = np.diag(cell).copy()
    if not np.array_equal(cell, np.diag(box)) or not np.all(np.isfinite(box) & (box > 0)):
        raise ValueError("Invalid orthorhombic Amber cell")
    # The NPT parent changed the LEaP construction cell. Use its actual box.
    top.topology.setPeriodicBoxVectors(
        tuple(mm.Vec3(*row) for row in cell / 10) * unit.nanometer
    )
    # Supply the published enediolate geometry at the four atoms whose bond
    # orders change. An unrestrained host preparation precedes the gas draws.
    labels = dict(
        zip(card["core_labels"], material["core_native_indices"], strict=True)
    )
    if (
        len(labels) != len(card["core_labels"])
        or len(set(labels.values())) != len(labels)
        or any(type(i) is not int or not 0 <= i < n + 7 for i in labels.values())
    ):
        raise ValueError("observed core changes its source-mapped atoms or link labels")
    metal = labels["magnesium.MG"]
    core = np.asarray(card["xyz_A"]) + xyz[metal]
    reactive = ("ligand.C2", "ligand.C3", "ligand.O2", "ligand.O3")
    anchors = [*reactive, "magnesium.MG"]
    src = core[[card["core_labels"].index(k) for k in anchors]]
    dst = xyz[[labels[k] for k in anchors]]
    dst = dst - box * np.rint((dst - dst[-1]) / box)
    rot, trans, _ = proper_rigid_fit(src, dst)
    xyz[[labels[k] for k in reactive]] = src[:-1] @ rot + trans
    changed = {row[0] for row in material["reactive_proton_changes"]}
    if changed != {"ligand.HC3", "ligand.HO3", "protein.302.HE2"}:
        raise ValueError("Unexpected reactive proton census")
    for proton, _, acceptor in material["reactive_proton_changes"]:
        anchors = {
            "ligand.O2": ("ligand.O2", "ligand.C2", "ligand.C1"),
            "protein.210.OQ2": ("protein.210.OQ2", "protein.210.CX", "protein.210.OQ1"),
            "protein.302.NE2": (
                "protein.302.NE2",
                "protein.302.CE1",
                "protein.302.CD2",
            ),
        }[acceptor]
        target = xyz[[labels[k] for k in anchors]]
        target = target - box * np.rint((target - target[0]) / box)
        rot, _, _ = proper_rigid_fit(
            core[[card["core_labels"].index(k) for k in anchors]], target
        )
        direction = (
            core[card["core_labels"].index(proton)]
            - core[card["core_labels"].index(acceptor)]
        ) @ rot
        if not 0.85 < np.linalg.norm(direction) < 1.18:
            raise ValueError("Invalid native proton-transfer proposal")
        xyz[labels[proton]] = xyz[labels[acceptor]] + direction
    water = material["native_water_indices"]
    if water != meta["water_atoms"] or [atoms[i].name for i in water] != [
        "O",
        "H1",
        "H2",
    ]:
        raise ValueError("Hydration source substituted a different water molecule")
    if (
        np.linalg.norm(
            xyz[water[0]]
            - xyz[metal]
            - box * np.rint((xyz[water[0]] - xyz[metal]) / box)
        )
        > 3.0
    ):
        raise ValueError("Hydrated parent lost the native reactive water")
    bonds = tuple(
        sorted(tuple(sorted((a.index, b.index))) for a, b in top.topology.bonds())
    )
    qm = tuple(sorted([i for i in labels.values() if i < n] + water))
    qset = set(qm)
    cuts = sorted(
        (a, b) if a in qset else (b, a) for a, b in bonds if (a in qset) != (b in qset)
    )
    if sorted(b for a, b in cuts) != sorted(material["cap_CA_indices"]) or any(
        (atoms[a].name, atoms[b].name) != ("CB", "CA") for a, b in cuts
    ):
        raise ValueError("Observed QM core differs at a covalent boundary")
    if len(qm) != 121 or len(cuts) != 7 or len(np.unique(qm)) != len(qm):
        raise ValueError("Incomplete hydrated native QM selection")
    if (
        len(meta["sites"]) != 8
        or len({v["magnesium.MG"] for v in meta["sites"].values()}) != 8
    ):
        raise ValueError("Lost one of the eight active sites")
    water_o = meta["water_oxygen_native_indices"]
    excluded = {atoms[j].residue.index for j in water_o}
    solute = np.asarray(
        [
            a.index
            for a in atoms
            if a.element.atomic_number > 1
            and a.residue.index not in excluded
            and len(list(a.residue.atoms())) > 1
        ]
    )
    return dict(
        case=case,
        top=top,
        xyz=xyz,
        box=box,
        atoms=atoms,
        bonds=bonds,
        qm=qm,
        links=tuple((a, b, 1.09) for a, b in cuts),
        labels=labels,
        water=water,
        solute=solute,
        water_o=water_o,
        sites=meta["sites"],
        charge=card["charge"],
    )


def bind_material(paths, identities, case, gas, multiplicity, meta, completion):
    """Build the source partition without an electronic calculation or an MM context."""
    material = prepare_material(paths, case, meta, completion)
    names = {
        "ATOMIC_NUMBER",
        "MASS",
        "CHARGE",
        "BONDS_INC_HYDROGEN",
        "BONDS_WITHOUT_HYDROGEN",
    }
    with paths["topology"].open("rt", encoding="ascii") as stream:
        raw = read_prmtop_lines(stream, selected_flags=names)
    numbers = raw["ATOMIC_NUMBER"]
    if numbers != tuple(a.element.atomic_number for a in material["atoms"]):
        raise ValueError(
            "observed topology atom numbers differ between the two readers"
        )
    native_bonds = []
    for flag in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN"):
        rows = raw[flag]
        if len(rows) % 3 or any(x < 0 or x % 3 for x in (*rows[::3], *rows[1::3])):
            raise ValueError("invalid fixed-column native Amber bond index")
        native_bonds.extend(
            tuple(sorted((a // 3, b // 3)))
            for a, b in zip(rows[::3], rows[1::3], strict=True)
        )
    # Amber encodes the H-H distance of each three-site water as an extra
    # bonded term. OpenMM keeps that term in its system but omits it from
    # the chemical topology. Compare both inventories with that distinction.
    water_distances = set()
    for residue in material["top"].topology.residues():
        if residue.name != "HOH":
            continue
        atoms = tuple(residue.atoms())
        if tuple(a.element.atomic_number for a in atoms) != (8, 1, 1):
            raise ValueError("observed material has a different native water model")
        water_distances.add(tuple(sorted((atoms[1].index, atoms[2].index))))
    native_set = set(native_bonds)
    if (
        len(native_set) != len(native_bonds)
        or not water_distances <= native_set
        or native_set - water_distances != set(material["bonds"])
    ):
        raise ValueError(
            "observed topology bonds differ between independent native readers"
        )
    extra = stock_gas(gas, paths) if gas is not None else []
    count = len(numbers)
    qm = (*material["qm"], *range(count, count + len(extra)))
    partition = ObservedCorePartition(
        material=case,
        gas=gas,
        source_digests=tuple(sorted(identities.items())),
        atomic_numbers=(*numbers, *({"C": 6, "O": 8}[x[0]] for x in extra)),
        masses_dalton=(*map(float, raw["MASS"]), *(x[1] for x in extra)),
        charges_electron=(
            *(float(x) / 18.2223 for x in raw["CHARGE"]),
            *(x[2] for x in extra),
        ),
        qm_atom_indices=qm,
        bonds=material["bonds"],
        links=material["links"],
        lengths_angstrom=tuple(map(float, material["box"])),
        qm_formal_charge=material["charge"],
        spin_multiplicity=multiplicity,
    )
    return partition, material, extra


def make_operator(
    partition,
    material,
    gas_atoms,
    *,
    settings,
    observe,
    accelerated_compute=False,
    device_memory_bytes=None,
    molecular_platform=None,
    host_memory_bytes=None,
):
    import openmm as mm
    from openmm import app, unit
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import (
        ObservedCorePeriodicOperator,
    )

    top = material["top"]
    system = top.createSystem(
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometer,
        constraints=None,
        rigidWater=False,
        removeCMMotion=False,
        ewaldErrorTolerance=1e-4,
    )
    (force,) = [f for f in system.getForces() if isinstance(f, mm.NonbondedForce)]
    force.setUseDispersionCorrection(False)
    force.setUseSwitchingFunction(False)
    for _, mass, charge, sigma, epsilon in gas_atoms:
        system.addParticle(mass)
        force.addParticle(charge, sigma, epsilon)
    return ObservedCorePeriodicOperator(
        partition=partition,
        settings=settings,
        original_system=system,
        source_scee=source_scales(top._prmtop),
        observe=observe,
        accelerated_compute=accelerated_compute,
        device_memory_bytes=device_memory_bytes,
        molecular_platform=molecular_platform,
        host_memory_bytes=host_memory_bytes,
    )
