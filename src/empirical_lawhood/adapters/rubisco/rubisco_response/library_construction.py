# SPDX-License-Identifier: MPL-2.0
"""Pinned-library construction and minimization at an authenticated native port.

PDBFixer supplies missing heavy coordinates; Amber supplies all hydrogens and
force parameters; OpenMM supplies the complete molecular minimizer. None of
these operations supplies physical-ensemble or kinetic admission.
"""

from io import StringIO
import math
import os
from threading import RLock

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import origin_mobility, replace_heavy_coordinates


_FIXER_PLATFORM_LOCK = RLock()


def construction_platform(platform_name, threads):
    """Select explicit CPU kernels; Reference is an opt-in small-system oracle."""
    from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import validate_construction_platform
    import openmm as mm
    validate_construction_platform(platform_name, threads)
    if threads > len(os.sched_getaffinity(0)):
        raise ValueError("construction thread selection exceeds the actual CPU affinity")
    properties = {"Threads": str(threads), "DeterministicForces": "true"} if platform_name == "CPU" else {}
    return mm.Platform.getPlatformByName(platform_name), properties


def _add_missing_atoms(fixer, *, seed, platform_name, threads):
    # PDBFixer 1.11 accepts a Platform but has no Context property argument.
    # Its internal Contexts therefore need scoped defaults. Serialize this port
    # and restore every value, including on a library failure. Ordinary OpenMM
    # contexts below always receive explicit properties.
    platform, properties = construction_platform(platform_name, threads)
    with _FIXER_PLATFORM_LOCK:
        previous = {name: platform.getPropertyDefaultValue(name) for name in properties}
        try:
            for name, value in properties.items():
                platform.setPropertyDefaultValue(name, value)
            fixer.addMissingAtoms(seed=seed)
        finally:
            for name, value in previous.items():
                platform.setPropertyDefaultValue(name, value)


def authenticated_missing_residues(topology, atoms, constructed):
    """Map complete missing residues to insertion slots using original numbering.

    Repeated sequences cannot select a different terminus. Every inserted atom
    must belong to the authenticated construction scope, and every chain needs
    an observed anchor. PDBFixer retains these exact observed residue numbers.
    """
    expected = {}
    for atom in atoms:
        if atom["chain"] != "Z":
            expected.setdefault(atom["chain"], {}).setdefault(atom["position"], []).append(atom)
    permitted, seen, plan = set(constructed), set(), {}
    for chain in topology.chains():
        if chain.id == "Z":
            continue
        if chain.id in seen or chain.id not in expected:
            raise ValueError("PDBFixer changed an authenticated protein chain")
        seen.add(chain.id)
        residues = list(chain.residues())
        numbers = [int(residue.id) for residue in residues]
        if not numbers or numbers != sorted(set(numbers)) or any(getattr(r, "insertionCode", "").strip() for r in residues):
            raise ValueError("construction needs unique ordered residue numbers and an observed anchor")
        selected = expected[chain.id]
        if not set(numbers) <= set(selected):
            raise ValueError("PDBFixer changed an authenticated residue number")
        for slot, (left, right) in enumerate(zip([0]+numbers, numbers+[max(selected)+1], strict=True)):
            missing = list(range(left+1, right))
            if missing:
                if any((chain.id, p, atom["atom"]) not in permitted for p in missing for atom in selected[p]):
                    raise ValueError("missing-residue completion would replace an observed atom")
                plan[chain.index, slot] = [selected[p][0]["component"] for p in missing]
    if seen != set(expected):
        raise ValueError("missing-residue completion lacks an observed anchor for a selected chain")
    return plan


def construction_input_pdb(heavy_text, origin):
    """Discard constructed proposals and expose the complete selected sequence.

    Nonstandard residues and crystallographic waters/ions are retained. This
    deliberately never calls replaceNonstandardResidues or removeHeterogens.
    """
    atoms, constructed = origin_mobility(heavy_text, origin)
    permitted = set(constructed)
    residues = {}
    for atom in atoms:
        if atom["chain"] != "Z":
            residues.setdefault(atom["chain"], {})[atom["position"]] = atom["component"]
    lines = []
    for chain, positions in sorted(residues.items()):
        if tuple(sorted(positions)) != tuple(range(1, max(positions)+1)):
            raise ValueError("library construction requires the full declared protein sequence")
        sequence = [positions[i] for i in sorted(positions)]
        for start in range(0, len(sequence), 13):
            lines.append(f"SEQRES {start//13+1:3d} {chain} {len(sequence):4d}  " + " ".join(sequence[start:start+13]))
    for line in heavy_text.splitlines():
        if line.startswith(("ATOM  ", "HETATM")):
            key = line[21], int(line[22:26]), line[12:16].strip()
            if key not in permitted:
                lines.append(line)
        elif line.startswith("TER"):
            lines.append(line)
    lines.append("END")
    return "\n".join(lines)+"\n", atoms, constructed


def complete_constructed_heavy_atoms(heavy_text, origin, *, seed=20261114, platform_name="CPU", threads=1):
    """Use PDBFixer's native completion, then verify the exact chemical census.

    Call only inside registered native contact with the selected package files
    authenticated. Missing libraries or a changed atom population fail closed.
    There is no terminal-search, template-frame or best-score fallback.
    """
    from pdbfixer import PDBFixer
    from openmm import unit

    raw, atoms, constructed = construction_input_pdb(heavy_text, origin)
    platform, _ = construction_platform(platform_name, threads)
    fixer = PDBFixer(pdbfile=StringIO(raw), platform=platform)
    fixer.missingResidues = authenticated_missing_residues(fixer.topology, atoms, constructed)
    fixer.findMissingAtoms()
    # PDBFixer normally adds OXT to every uncapped chain. Only the selected
    # chemical census may acquire terminal atoms; the final exact census check
    # independently refuses any other alteration.
    permitted = set(constructed)
    fixer.missingTerminals = {residue: [name for name in names
        if (residue.chain.id, int(residue.id), name) in permitted]
        for residue, names in fixer.missingTerminals.items()}
    _add_missing_atoms(fixer, seed=seed, platform_name=platform_name, threads=threads)
    coordinates = np.asarray(fixer.positions.value_in_unit(unit.angstrom), dtype=float)
    if coordinates.ndim != 2 or coordinates.shape[1:] != (3,) or not np.isfinite(coordinates).all():
        raise ValueError("PDBFixer returned nonfinite or incomplete heavy coordinates")
    observed = {}
    for atom in fixer.topology.atoms():
        key = atom.residue.chain.id, int(atom.residue.id), atom.name
        if key in observed or atom.element is None or atom.element.atomic_number == 1:
            raise ValueError("PDBFixer duplicated an atom or changed the heavy-only contract")
        observed[key] = atom.residue.name, atom.element.symbol.upper(), coordinates[atom.index]
    expected = {(a["chain"], a["position"], a["atom"]): a for a in atoms}
    if set(observed) != set(expected):
        raise ValueError("PDBFixer changed the complete selected heavy atom census")
    permitted = set(constructed)
    for key, (component, element, point) in observed.items():
        atom = expected[key]
        normalized = "HIS" if component in {"HIS", "HID", "HIE"} else component
        expected_component = "HIS" if atom["component"] in {"HIS", "HID", "HIE"} else atom["component"]
        if normalized != expected_component or element != atom["element"]:
            raise ValueError("PDBFixer changed a protected residue, ligand or element")
        if key not in permitted and not np.allclose(point, np.asarray(atom["xyz"], float), atol=1e-6, rtol=0):
            raise ValueError("PDBFixer moved an observed anchor outside the construction scope")
    result = replace_heavy_coordinates(heavy_text, {key: observed[key][2] for key in constructed}, constructed)
    return result, ({"kind": "pdbfixer-complete-selected-missing-heavy-atoms", "seed": seed,
        "platform": platform_name, "threads": threads,
        "constructed_heavy_atoms": len(constructed), "protected_heavy_atoms": len(atoms)-len(constructed),
        "replace_nonstandard_residues": False, "remove_heterogens": False},), constructed


def construct_i95m_sidechains(heavy_text, mutation_chains, *, seed=20261114, platform_name="CPU", threads=1):
    """Realize all selected I95M side chains with PDBFixer.applyMutations.

    The source scaffold's custom Met pose is a proposal, not a native operand:
    remove CG/SD/CE, retain the inherited N/CA/C/O/CB anchor, declare ILE→MET,
    and let the selected library construct the missing mutant atoms. Every
    nonmutated atom and all protected chemical residues must remain exact.
    """
    from openmm import unit
    from pdbfixer import PDBFixer
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows

    mutation_chains = tuple(mutation_chains)
    if not mutation_chains:
        return heavy_text, {"method": "WT_NO_MUTATION", "mutations": [], "seed": seed}
    if len(mutation_chains) != 8 or len(set(mutation_chains)) != 8:
        raise ValueError("I95M construction requires the declared all-eight SSU mutation census")
    rows = heavy_pdb_rows(heavy_text)
    expected = {(c, p, name): (component, element.upper(), np.asarray(xyz, float)) for c, p, component, name, element, xyz in rows}
    mutable = {(chain, 95, name) for chain in mutation_chains for name in ("CG", "SD", "CE")}
    if not mutable <= set(expected) or any(expected[key][0] != "MET" for key in mutable):
        raise ValueError("I95M construction lacks a complete declared Met proposal in each SSU")
    lines = []
    for line in heavy_text.splitlines():
        if line.startswith(("ATOM  ", "HETATM")):
            key = line[21], int(line[22:26]), line[12:16].strip()
            if key in mutable:
                continue
            if key[0] in mutation_chains and key[1] == 95:
                line = line[:17]+"ILE"+line[20:]
            lines.append(line)
        elif line.startswith("TER"):
            lines.append(line)
    lines.append("END")
    platform, _ = construction_platform(platform_name, threads)
    fixer = PDBFixer(pdbfile=StringIO("\n".join(lines)+"\n"), platform=platform)
    fixer.missingResidues = {}
    for chain in mutation_chains:
        fixer.applyMutations(["ILE-95-MET"], chain)
    fixer.findMissingAtoms()
    fixer.missingTerminals = {}
    _add_missing_atoms(fixer, seed=seed, platform_name=platform_name, threads=threads)
    points = np.asarray(fixer.positions.value_in_unit(unit.angstrom), float)
    observed = {}
    for atom in fixer.topology.atoms():
        key = atom.residue.chain.id, int(atom.residue.id), atom.name
        if key in observed or atom.element is None or atom.element.atomic_number == 1:
            raise ValueError("PDBFixer mutation changed the heavy-only complete atom census")
        observed[key] = atom.residue.name, atom.element.symbol.upper(), points[atom.index]
    if set(observed) != set(expected) or not np.isfinite(points).all():
        raise ValueError("PDBFixer mutation added, omitted or invalidated a selected atom")
    for key, (component, element, xyz) in observed.items():
        old_component, old_element, old_xyz = expected[key]
        normalized = "HIS" if component in {"HIS", "HID", "HIE"} else component
        expected_component = "HIS" if old_component in {"HIS", "HID", "HIE"} else old_component
        if normalized != expected_component or element != old_element:
            raise ValueError("PDBFixer mutation changed a protected chemical identity")
        if key not in mutable and not np.allclose(xyz, old_xyz, atol=1e-6, rtol=0):
            raise ValueError("PDBFixer mutation moved an inherited anchor")
    return replace_heavy_coordinates(heavy_text, {key: observed[key][2] for key in mutable}, mutable), {
        "method": "PDBFIXER_APPLY_MUTATIONS_ILE95MET", "mutations": [(chain, "ILE-95-MET") for chain in mutation_chains],
        "seed": seed, "constructed_sidechain_atom_count": len(mutable), "protected_atom_count": len(expected)-len(mutable),
        "platform": platform_name, "threads": threads,
        "replace_nonstandard_residues": False, "remove_heterogens": False}


def conservative_rms_tolerance(maximum_component, atom_count):
    """RMS <= g/sqrt(3N) implies max Cartesian component <= g.

    OpenMM controls RMS; the caller independently reads the actual final
    maximum component. The inequality holds regardless of zero-mass atoms.
    """
    if not math.isfinite(maximum_component) or maximum_component <= 0 or type(atom_count) is not int or atom_count < 1:
        raise ValueError("minimization needs a positive force bound and complete atom count")
    return maximum_component/math.sqrt(3*atom_count)


def complete_amber_minimization(system, coordinates_nm, moving, *, maximum_component, maximum_iterations=None,
                                platform_name="CPU", threads=1, progress_directory=None):
    """Minimize all original force terms on the explicitly selected platform.

    Fixed particles receive zero integration mass; force constants, exclusions,
    charges, pair tables and every original force group remain untouched.
    A maximum iteration count is a work limit, never a convergence assertion.
    """
    import openmm as mm
    from openmm import unit

    coordinates = np.asarray(coordinates_nm, dtype=np.float64)
    count = system.getNumParticles()
    mobile = tuple(sorted(set(moving)))
    if (coordinates.shape != (count, 3) or not np.isfinite(coordinates).all() or not mobile
            or any(type(i) is not int or not 0 <= i < count for i in mobile)
            or (maximum_iterations is not None and (type(maximum_iterations) is not int or maximum_iterations < 1))):
        raise ValueError("Amber minimization changes its complete coordinate/mobile census")
    if system.getNumConstraints() or any(system.isVirtualSite(i) for i in range(count)):
        raise ValueError("construction minimization requires the declared unconstrained, nonvirtual Amber system")
    original_xml = mm.XmlSerializer.serialize(system)
    selected = mm.XmlSerializer.deserialize(original_xml)
    fixed = sorted(set(range(count))-set(mobile))
    for index in fixed:
        selected.setParticleMass(index, 0)
    integrator = mm.VerletIntegrator(0.001*unit.picosecond)
    integrator.setIntegrationForceGroups(-1)
    platform, properties = construction_platform(platform_name, threads)
    context = mm.Context(selected, integrator, platform, properties)
    progress = None
    try:
        context.setPositions(coordinates*unit.nanometer)
        initial = context.getState(getEnergy=True, getForces=True, getPositions=progress_directory is not None)
        initial_energy = initial.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        initial_forces = np.asarray(initial.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer), float)
        tolerance = conservative_rms_tolerance(maximum_component, count)
        from empirical_lawhood.adapters.rubisco.progress import minimization_reporter
        if progress_directory is not None:
            from .repair_progress import repair_evaluation_reporter
            progress = repair_evaluation_reporter(mm, unit, context, progress_directory, initial, initial_energy, initial_forces)
        mm.LocalEnergyMinimizer.minimize(context, tolerance=tolerance, maxIterations=maximum_iterations or 0,
            reporter=minimization_reporter(mm, progress))
        final_state = context.getState(getPositions=True, getEnergy=True, getForces=True)
        final = np.asarray(final_state.getPositions(asNumpy=True).value_in_unit(unit.nanometer), float)
        forces = np.asarray(final_state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer), float)
        energy = final_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        if progress is not None:
            progress.finish(final, energy, forces)
    finally:
        if progress is not None:
            progress.close()
        del context, integrator
    if not np.isfinite(final).all() or not np.isfinite(forces).all() or not math.isfinite(energy):
        raise ValueError("OpenMM construction returned a nonfinite energy, coordinate or force")
    if not np.array_equal(final[fixed], coordinates[fixed]):
        raise ValueError("OpenMM construction moved a fixed observed coordinate")
    gradient = float(np.max(np.abs(forces[list(mobile)])))
    return final, forces, {"success": gradient <= maximum_component,
        "numerical_method": "OPENMM_LOCAL_ENERGY_MINIMIZER_COMPLETE_AMBER_V1",
        "maximum_mobile_gradient_kj_mol_nm": gradient,
        "rms_mobile_gradient_kj_mol_nm": float(np.sqrt(np.mean(forces[list(mobile)]**2))),
        "requested_openmm_rms_tolerance_kj_mol_nm": tolerance,
        "maximum_iterations": maximum_iterations, "energy_kj_mol": float(energy),
        "initial_energy_kj_mol": float(initial_energy), "platform": platform_name, "threads": threads,
        "platform_properties": properties,
        "all_original_force_groups": True, "projected_pair_kernel": False,
        "iteration_limit_is_convergence": False}, initial_forces, original_xml


def evaluate_complete_amber(system, coordinates_nm, *, platform_name="CPU", threads=1):
    """Re-evaluate the exact serialized endpoint with all original force groups."""
    import openmm as mm
    from openmm import unit
    points = np.asarray(coordinates_nm, dtype=np.float64)
    if points.shape != (system.getNumParticles(), 3) or not np.isfinite(points).all():
        raise ValueError("final Amber evaluation requires the complete finite endpoint")
    integrator = mm.VerletIntegrator(0.001*unit.picosecond)
    integrator.setIntegrationForceGroups(-1)
    platform, properties = construction_platform(platform_name, threads)
    context = mm.Context(system, integrator, platform, properties)
    try:
        context.setPositions(points*unit.nanometer)
        state = context.getState(getEnergy=True, getForces=True)
        energy = float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
        forces = np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer), dtype=float)
    finally:
        del context, integrator
    if not math.isfinite(energy) or not np.isfinite(forces).all():
        raise ValueError("serialized Amber endpoint has nonfinite energy or forces")
    return energy, forces


def amber_restart_text(coordinates_angstrom, box_angstrom):
    """Write an explicit Amber coordinate projection, without hidden velocity rows."""
    points = np.asarray(coordinates_angstrom, dtype=float)
    box = np.asarray(box_angstrom, dtype=float)
    if (points.ndim != 2 or points.shape[1:] != (3,) or not len(points) or box.shape != (6,)
            or not np.isfinite(points).all() or not np.isfinite(box).all()):
        raise ValueError("Amber restart projection requires complete finite coordinates and box")
    values = tuple(points.ravel())+tuple(box)
    fields = [f"{value:12.7f}" for value in values]
    if any(len(value) != 12 for value in fields):
        raise ValueError("Amber restart coordinate exceeds its fixed-width precision contract")
    return "EL Amber/OpenMM minimized construction; no ensemble admission\n"+f"{len(points):6d}\n"+"\n".join("".join(fields[i:i+6]) for i in range(0, len(fields), 6))+"\n"


def complete_force_assignment(system, raw_topology, *, unit):
    """Expose and compare the complete live parser assignment with raw Amber."""
    from empirical_lawhood.adapters.rubisco.rubisco_insilico_free_energy.native_coupling import inspect_force_snapshot
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_mm_assignment import assess_amber_force_assignment
    snapshot = inspect_force_snapshot(system, unit=unit)
    masses = [system.getParticleMass(i).value_in_unit(unit.dalton) for i in range(system.getNumParticles())]
    return {"snapshot": snapshot, "masses_dalton": masses,
        "assessment": assess_amber_force_assignment(raw_topology, snapshot, masses)}


def relax_solvated_amber(source, model, directory):
    """Whole-system post-LEaP repair; exact final restart is freshly evaluated."""
    import json
    from hashlib import sha256
    from openmm import app, unit
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import assess_molecular_geometry, geometry_terms_from_amber
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop

    raw_topology = (directory/"model.prmtop").read_bytes()
    census = assigned_census_supported_inactive14(read_prmtop(raw_topology.decode("ascii")))
    points, box = read_initial_coordinates((directory/"model.inpcrd").read_text(), census["term_census"]["atoms"], periodic=True)
    coordinates = np.asarray(points, dtype=float)/10
    prmtop = app.AmberPrmtopFile(str(directory/"model.prmtop"))
    inpcrd = app.AmberInpcrdFile(str(directory/"model.inpcrd"))
    system = prmtop.createSystem(nonbondedMethod=app.PME,
        nonbondedCutoff=float(source.minimization_nonbonded_cutoff_angstrom)/10*unit.nanometer,
        ewaldErrorTolerance=float(source.minimization_ewald_tolerance), constraints=None, rigidWater=False, removeCMMotion=False)
    if inpcrd.boxVectors is None or system.getNumParticles() != len(coordinates):
        raise ValueError("solvated Amber construction loses its periodic box or complete atom census")
    system.setDefaultPeriodicBoxVectors(*inpcrd.boxVectors)
    assignment = complete_force_assignment(system, raw_topology, unit=unit)
    (directory/"force-assignment.json").write_text(json.dumps(assignment, sort_keys=True, allow_nan=False)+"\n")
    terms = geometry_terms_from_amber(raw_topology)
    initial_quality = assess_molecular_geometry(np.asarray(points, float), terms, policy=source.geometry_quality, cell_angstrom=tuple(float(x) for x in box[:3]))
    final, _, result, initial_forces, system_xml = complete_amber_minimization(system, coordinates, tuple(range(len(coordinates))),
        maximum_component=float(source.maximum_minimization_gradient_kj_mol_nm), maximum_iterations=source.maximum_minimization_iterations,
        platform_name=source.construction_platform, threads=source.construction_threads)
    raw_final = amber_restart_text(final*10, box).encode("ascii")
    (directory/"relaxed.inpcrd").write_bytes(raw_final)
    exact_points, exact_box = read_initial_coordinates(raw_final.decode("ascii"), len(coordinates), periodic=True)
    exact_coordinates = np.asarray(exact_points, float)/10
    energy, forces = evaluate_complete_amber(system, exact_coordinates,
        platform_name=source.construction_platform, threads=source.construction_threads)
    final_quality = assess_molecular_geometry(np.asarray(exact_points, float), terms, policy=source.geometry_quality, cell_angstrom=tuple(float(x) for x in exact_box[:3]))
    maximum = float(np.max(np.abs(forces)))
    result.update(model=model.identity.to_document(), maximum_mobile_gradient_kj_mol_nm=maximum,
        rms_mobile_gradient_kj_mol_nm=float(np.sqrt(np.mean(forces**2))), energy_kj_mol=energy,
        success=maximum <= float(source.maximum_minimization_gradient_kj_mol_nm) and final_quality["disposition"] == "SCREEN_PASSED",
        initial_geometry=initial_quality, final_geometry=final_quality,
        relaxed_coordinates_sha256=sha256(raw_final).hexdigest(), final_force_coordinates="EXACT_RETAINED_RELAXED_INPCRD",
        nonbonded_cutoff_angstrom=str(source.minimization_nonbonded_cutoff_angstrom),
        ewald_error_tolerance=str(source.minimization_ewald_tolerance),
        atom_count=len(coordinates), all_atoms_mobile=True, constraints="NONE", rigid_water=False,
        ensemble_admission="UNEVALUABLE", force_accuracy_admission="UNEVALUABLE", rate_admission="UNEVALUABLE")
    np.save(directory/"final-forces-kj-mol-nm.npy", forces, allow_pickle=False)
    np.save(directory/"initial-forces-kj-mol-nm.npy", initial_forces, allow_pickle=False)
    (directory/"relaxation-system.xml").write_text(system_xml)
    (directory/"relaxation.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n")
    return result
