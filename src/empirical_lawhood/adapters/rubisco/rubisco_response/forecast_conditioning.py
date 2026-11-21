# SPDX-License-Identifier: MPL-2.0
"""Read stock Amber files and run restrained, periodic OpenMM conditioning."""

from collections import Counter
import json
import math
import os
from pathlib import Path
import time

from .forecast_core import CASES, LSU, SSU, digest, observed_residues, write_json


def load_system(build):
    from openmm import app

    manifest = json.loads((build / "built.json").read_text())
    if manifest.get("selection_sha256") != digest(build / "selection.json"):
        raise ValueError("The frozen Amber source selection has changed")
    if manifest["case"] not in CASES or any(
        digest(build / f) != h for f, h in manifest["files"].items()
    ):
        raise ValueError("The selected native build or its inputs have changed")
    return (
        manifest,
        app.AmberPrmtopFile(str(build / "model.prmtop")),
        app.AmberInpcrdFile(str(build / "model.inpcrd")),
    )


def sites(topology, coords, box, build, case):
    import numpy as np
    from scipy.spatial import cKDTree

    inputs = observed_residues((build / "library-heavy.pdb").read_text())
    residues = list(topology.residues())
    if (
        len(inputs) != 4896
        or len(coords) != topology.getNumAtoms()
        or not np.isfinite(coords).all()
    ):
        raise ValueError("Unexpected solute population or coordinate array")
    sites_by_id, polymer, atom_index = {}, {}, {}
    equivalents = {"HID": "HIS", "HIE": "HIS", "HIP": "HIS", "CYX": "CYS"}
    for (key, _), res in zip(inputs, residues[: len(inputs)], strict=True):
        chain, number, ins, name = key
        if equivalents.get(name, name) != equivalents.get(res.name, res.name):
            raise ValueError(f"Residue order differs at {chain} {number} {ins}")
        by_name = {a.name: a.index for a in res.atoms()}
        sites_by_id[chain, number, ins] = by_name
        for a in res.atoms():
            atom_index[a.index] = f"{chain}/{res.name}{number}{ins.strip()}/{a.name}"
            if a.element.atomic_number > 1 and name not in ("RUB", "MG"):
                polymer.setdefault(chain, []).append(a.index)
    lengths = np.diag(box)
    if not np.allclose(box, np.diag(lengths)) or np.any(lengths <= 0):
        raise ValueError(
            "The selected LEaP protocol requires a rectangular periodic box"
        )

    def dist(i, j):
        v = coords[i] - coords[j]
        return float(np.linalg.norm(v - lengths * np.round(v / lengths)))

    waters = [
        a.index
        for r in residues
        if r.name == "HOH"
        for a in r.atoms()
        if a.element.atomic_number == 8
    ]
    water_tree = cKDTree(coords[waters] % lengths, boxsize=lengths)
    answer = {}
    for lc, sc in zip(LSU, SSU, strict=True):
        m = sites_by_id[lc, 490, " "]["MG"]
        metal, ligand = {}, sites_by_id[lc, 491, " "]
        for n in (201, 203, 204):
            atoms = sites_by_id[lc, n, " "]
            for an in ("OQ1", "OQ2", "OD1", "OD2", "OE1", "OE2"):
                if an in atoms:
                    metal[atom_index[atoms[an]]] = dist(m, atoms[an])
        for an in ("O2", "O3"):
            metal[atom_index[ligand[an]]] = dist(m, ligand[an])
        selected = sites_by_id[sc, 112, " "]
        met = case.endswith("I95M")
        distal = ("CG", "SD", "CE") if met else ("CG1", "CG2", "CD1")
        if not all(a in selected for a in distal) or ("SD" in selected) != met:
            raise ValueError("Wrong SSU95 native atom identity")
        first = sites_by_id[sc, 8, " "]
        if ("SD" in first) != case.startswith("M1") or not {"OXT"} <= sites_by_id[
            lc, 478, " "
        ].keys():
            raise ValueError(
                "Wrong small-subunit first residue or explicit cut terminus"
            )
        other = [
            i for chain, members in polymer.items() if chain != sc for i in members
        ]
        distances, near = cKDTree(coords[other] % lengths, boxsize=lengths).query(
            coords[[selected[a] for a in distal]] % lengths
        )
        j = int(np.argmin(distances))
        nearest_water, water_idx = water_tree.query(coords[m] % lengths, k=3)
        answer[sc] = {
            "LSU": lc,
            "SSU_first": "MET" if "SD" in first else "VAL",
            "SSU95": "MET" if met else "ILE",
            "closest_95_distal_other_chain_A": float(distances[j]),
            "interface_atoms": [
                atom_index[selected[distal[j]]],
                atom_index[other[int(near[j])]],
            ],
            "Mg_distances_A": metal,
            "nearest_water_oxygen_indices": [waters[int(i)] for i in water_idx],
            "nearest_water_oxygen_A": nearest_water.tolist(),
        }
    return answer


def read_case(build, condition=None):
    import numpy as np
    from openmm import unit

    manifest, topology, crd = load_system(build)
    coords = crd.getPositions(asNumpy=True).value_in_unit(unit.angstrom)
    box = np.array([v.value_in_unit(unit.angstrom) for v in crd.getBoxVectors()])
    census = Counter(res.name for res in topology.topology.residues())
    if (
        any(census[n] != 8 for n in ("KCX", "RUB", "MG"))
        or census["CAP"]
        or not census["HOH"]
    ):
        raise ValueError("Amber cofactor, substrate or solvent population differs")
    raw = topology._prmtop
    native_charge = np.asarray(raw.getCharges())
    residues = list(topology.topology.residues())
    native_bonds = {
        tuple(sorted((a.index, b.index))) for a, b in topology.topology.bonds()
    }
    active = []
    for k, res in enumerate(residues):
        if res.name not in ("KCX", "MG", "RUB"):
            continue
        group = list(res.atoms())
        q = float(native_charge[[a.index for a in group]].sum())
        wanted = {"KCX": -1.0, "RUB": -4.0, "MG": 2.0}[res.name]
        if abs(q - wanted) > 0.002:
            raise ValueError(f"Native charge differs for {res.name}: {q}")
        links = []
        if res.name == "KCX":
            for r1, n1, r2, n2 in ((k - 1, "C", k, "N"), (k, "C", k + 1, "N")):
                indices = [
                    next(a.index for a in residues[i].atoms() if a.name == name)
                    for i, name in ((r1, n1), (r2, n2))
                ]
                if tuple(sorted(indices)) not in native_bonds:
                    raise ValueError("Missing native KCX peptide link")
                links.append(indices)
        active.append(
            {
                "residue_index": k,
                "component": res.name,
                "charge_e": q,
                "peptide_links": links,
            }
        )
    total_q = float(native_charge.sum())
    if abs(total_q) > 0.01 or len(active) != 24:
        raise ValueError("Periodic system charge or active-site population differs")
    out = {
        "case": manifest["case"],
        "total_charge_e": total_q,
        "active_topology": active,
        "atoms": topology.topology.getNumAtoms(),
        "water": census["HOH"],
        "native_residue_census": dict(census),
        "initial_box_A": box.tolist(),
        "initial_sites": sites(topology.topology, coords, box, build, manifest["case"]),
    }
    if condition is not None:
        report = json.loads((condition / "conditioned.json").read_text())
        if (
            report["build_sha256"] != digest(build / "built.json")
            or digest(condition / "final.npz") != report["final_sha256"]
        ):
            raise ValueError(
                "The final state differs from the selected native build or result"
            )
        with np.load(condition / "final.npz", allow_pickle=False) as f:
            xyz, forces, box = f["coordinates_A"], f["forces_kJ_mol_nm"], f["box_A"]
            if forces.shape != coords.shape or not np.isfinite(forces).all():
                raise ValueError("Final forces are unavailable or non-finite")
            out.update(
                final_sites=sites(topology.topology, xyz, box, build, manifest["case"]),
                peak_force_component_kJ_mol_nm=float(np.abs(forces).max()),
                final_box_A=box.tolist(),
            )
    return out


def condition_case(build, protocol, output):
    import numpy as np
    import openmm as mm
    from openmm import app, unit

    for key in ("threads", "min_iterations", "nvt_steps", "npt_steps", "seed"):
        if type(protocol.get(key)) is not int or protocol[key] <= 0:
            raise ValueError(
                "Invalid positive integer in conditioning protocol: " + key
            )
    if protocol["threads"] > len(os.sched_getaffinity(0)):
        raise ValueError("Insufficient CPU affinity for the selected platform")
    start, cpu_start = time.monotonic(), time.process_time()
    manifest, top, crd = load_system(build)
    output.mkdir(exist_ok=False)
    write_json(output / "protocol.json", protocol)
    try:
        from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import (
            authenticate_numeric_engine,
        )
        from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import (
            GpRepairNumericEngine,
        )
        from empirical_lawhood.science.records.decoding import decode_canonical_bytes

        selection = json.loads((build / "selection.json").read_text())["numeric_engine"]
        numeric = Path(selection["path"])
        if digest(numeric) != selection["sha256"]:
            raise ValueError("Numerical engine selection changed")
        engine = decode_canonical_bytes(
            numeric.read_bytes(), GpRepairNumericEngine, maximum_bytes=2**21
        )
        authenticate_numeric_engine(engine)
        system = top.createSystem(
            nonbondedMethod=app.PME,
            nonbondedCutoff=1 * unit.nanometer,
            constraints=app.HBonds,
            rigidWater=True,
            ewaldErrorTolerance=0.0005,
        )
        xyz = crd.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
        restraint = mm.CustomExternalForce(
            "0.5*krest*periodicdistance(x,y,z,x0,y0,z0)^2"
        )
        restraint.addGlobalParameter("krest", 500)
        for name in ("x0", "y0", "z0"):
            restraint.addPerParticleParameter(name)
        for atom in top.topology.atoms():
            if atom.name == "CA" and atom.residue.name not in ("CA", "HOH"):
                restraint.addParticle(atom.index, xyz[atom.index])
        system.addForce(restraint)
        barostat = mm.MonteCarloBarostat(1 * unit.bar, 298.15 * unit.kelvin, 0)
        barostat.setRandomNumberSeed(protocol["seed"] + 1)
        system.addForce(barostat)
        integrator = mm.LangevinMiddleIntegrator(
            298.15 * unit.kelvin, 1 / unit.picosecond, 0.001 * unit.picoseconds
        )
        integrator.setRandomNumberSeed(protocol["seed"])
        platform = mm.Platform.getPlatformByName("CPU")
        properties = {
            "Threads": str(protocol["threads"]),
            "DeterministicForces": "true",
        }
        positions = crd.positions
        if protocol.get("flexible_min_iterations", 0):
            flexible = top.createSystem(
                nonbondedMethod=app.PME,
                nonbondedCutoff=1 * unit.nanometer,
                constraints=None,
                rigidWater=False,
                ewaldErrorTolerance=0.0005,
            )
            flexible.addForce(
                mm.XmlSerializer.deserialize(mm.XmlSerializer.serialize(restraint))
            )
            warm = app.Simulation(
                top.topology, flexible, mm.VerletIntegrator(0.001), platform, properties
            )
            warm.context.setPeriodicBoxVectors(*crd.boxVectors)
            warm.context.setPositions(positions)
            before = (
                warm.context.getState(getEnergy=True)
                .getPotentialEnergy()
                .value_in_unit(unit.kilojoules_per_mole)
            )
            warm.minimizeEnergy(
                tolerance=10 * unit.kilojoules_per_mole / unit.nanometer,
                maxIterations=protocol["flexible_min_iterations"],
            )
            relaxed = warm.context.getState(
                getPositions=True, getEnergy=True, getForces=True
            )
            positions = relaxed.getPositions()
            after = relaxed.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
            peak = float(
                np.max(
                    np.abs(
                        relaxed.getForces(asNumpy=True).value_in_unit(
                            unit.kilojoules_per_mole / unit.nanometer
                        )
                    )
                )
            )
            if not np.isfinite((before, after, peak)).all() or after >= before:
                raise ValueError(
                    "Native flexible minimization did not reduce a finite energy"
                )
            write_json(
                output / "flexible-minimization.json",
                {
                    "initial_kJ_mol": before,
                    "relaxed_kJ_mol": after,
                    "peak_force_component_kJ_mol_nm": peak,
                    "wall_s": time.monotonic() - start,
                },
            )
            del warm, flexible, relaxed
        sim = app.Simulation(top.topology, system, integrator, platform, properties)
        sim.context.setPeriodicBoxVectors(*crd.boxVectors)
        sim.context.setPositions(positions)
        log = output / "stages.jsonl"

        def observe(stage):
            state = sim.context.getState(getEnergy=True)
            energy = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
            kinetic = state.getKineticEnergy().value_in_unit(unit.kilojoules_per_mole)
            if not math.isfinite(energy) or not math.isfinite(kinetic):
                raise ValueError("Non-finite native energy")
            with log.open("a") as f:
                f.write(
                    json.dumps(
                        {
                            "stage": stage,
                            "step": sim.currentStep,
                            "potential_kJ_mol": energy,
                            "kinetic_kJ_mol": kinetic,
                            "volume_nm3": state.getPeriodicBoxVolume().value_in_unit(
                                unit.nanometer**3
                            ),
                            "wall_s": time.monotonic() - start,
                        },
                        allow_nan=False,
                    )
                    + "\n"
                )

        observe("initial")
        sim.minimizeEnergy(
            tolerance=10 * unit.kilojoules_per_mole / unit.nanometer,
            maxIterations=protocol["min_iterations"],
        )
        observe("minimized")
        sim.context.setVelocitiesToTemperature(
            298.15 * unit.kelvin, protocol["seed"] + 2
        )
        sim.step(protocol["nvt_steps"])
        observe("NVT")
        barostat.setFrequency(25)
        sim.context.reinitialize(preserveState=True)
        first = protocol["npt_steps"] // 2
        for k, steps in ((100, first), (0, protocol["npt_steps"] - first)):
            sim.context.setParameter("krest", k)
            sim.step(steps)
            observe(f"NPT_restraint_{k}")
        state = sim.context.getState(
            getPositions=True, getVelocities=True, getForces=True, getEnergy=True
        )
        arrays = {
            "coordinates_A": state.getPositions(asNumpy=True).value_in_unit(
                unit.angstrom
            ),
            "box_A": state.getPeriodicBoxVectors(asNumpy=True).value_in_unit(
                unit.angstrom
            ),
            "velocities_nm_ps": state.getVelocities(asNumpy=True).value_in_unit(
                unit.nanometer / unit.picosecond
            ),
            "forces_kJ_mol_nm": state.getForces(asNumpy=True).value_in_unit(
                unit.kilojoules_per_mole / unit.nanometer
            ),
        }
        if not all(np.isfinite(arr).all() for arr in arrays.values()):
            raise ValueError("Nonfinite final state")
        np.savez_compressed(output / "final.npz", **arrays)
        sim.saveCheckpoint(str(output / "final.chk"))
        write_json(
            output / "conditioned.json",
            {
                "case": manifest["case"],
                "build_sha256": digest(build / "built.json"),
                "engine_sha256": selection["sha256"],
                "protocol_sha256": digest(output / "protocol.json"),
                "affinity": sorted(os.sched_getaffinity(0)),
                "openmm": mm.version.version,
                "final_sha256": digest(output / "final.npz"),
                "checkpoint_sha256": digest(output / "final.chk"),
                "integrator_steps": sim.currentStep,
                "wall_s": time.monotonic() - start,
                "cpu_s": time.process_time() - cpu_start,
                "scope": "Initial conditioning only. Equilibrium and reactive rates unassessed.",
            },
        )
    except Exception as exc:
        write_json(
            output / "conditioning-failure.json",
            {
                "error": str(exc),
                "wall_s": time.monotonic() - start,
                "cpu_s": time.process_time() - cpu_start,
            },
        )
        raise


def independent_force(build, condition, threads):
    """Re-evaluate the unbiased endpoint from its native Amber terms and full snapshot."""
    import numpy as np
    import openmm as mm
    from openmm import app, unit

    start = time.monotonic()
    manifest, prmtop, _ = load_system(build)
    report = json.loads((condition / "conditioned.json").read_text())
    if report["build_sha256"] != digest(build / "built.json") or report[
        "final_sha256"
    ] != digest(condition / "final.npz"):
        raise ValueError(
            "Independent force read needs the original paired native result"
        )
    if (
        sorted(os.sched_getaffinity(0)) != report["affinity"]
        or threads != json.loads((condition / "protocol.json").read_text())["threads"]
    ):
        raise ValueError("Reconstruct with the producer's CPU settings")
    system = prmtop.createSystem(
        nonbondedMethod=app.PME,
        nonbondedCutoff=1 * unit.nanometer,
        constraints=app.HBonds,
        rigidWater=True,
        ewaldErrorTolerance=0.0005,
    )
    context = mm.Context(
        system,
        mm.VerletIntegrator(0.001),
        mm.Platform.getPlatformByName("CPU"),
        {"Threads": str(threads), "DeterministicForces": "true"},
    )
    with np.load(condition / "final.npz", allow_pickle=False) as f:
        context.setPeriodicBoxVectors(
            *(mm.Vec3(*v) * unit.angstrom for v in f["box_A"])
        )
        context.setPositions(f["coordinates_A"] * unit.angstrom)
        state = context.getState(getForces=True, getEnergy=True)
        reconstructed = state.getForces(asNumpy=True).value_in_unit(
            unit.kilojoules_per_mole / unit.nanometer
        )
        reference = f["forces_kJ_mol_nm"]
        if (
            reference.shape != reconstructed.shape
            or not np.isfinite(reconstructed).all()
        ):
            raise ValueError("Independent force population differs")
        delta = reconstructed - reference
        energy = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
        original_energy = json.loads(
            (condition / "stages.jsonl").read_text().splitlines()[-1]
        )["potential_kJ_mol"]
        return {
            "case": manifest["case"],
            "particles": len(reference),
            "original_peak_abs_component": float(np.abs(reference).max()),
            "maximum_force_component_difference_kJ_mol_nm": float(np.abs(delta).max()),
            "rms_force_component_difference_kJ_mol_nm": float(
                np.sqrt(np.mean(delta**2))
            ),
            "relative_force_l2_difference": float(
                np.linalg.norm(delta) / np.linalg.norm(reference)
            ),
            "energy_difference_kJ_mol": energy - original_energy,
            "wall_s": time.monotonic() - start,
        }
