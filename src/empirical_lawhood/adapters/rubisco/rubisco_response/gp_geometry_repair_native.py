# SPDX-License-Identifier: MPL-2.0
"""Native fixed-coordinate minimization, entered only by the registered owner."""

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _parm_dat_sections, _frcmod_sections, scoped_boundary_stock, scoped_kcx_stock
from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import replace_heavy_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GpAmberFragmentRepairInput, GpCarboxylateRepairInput, inherited_carboxylate_keys
from empirical_lawhood.domains.rubisco.rubisco_response.gp_terminal_geometry import (
    TERMINAL_GEOMETRY_FILE, initial_terminal_geometry, require_initial_terminal_geometry, terminal_geometry_bytes,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import amber_command
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import _residues, read_initial_coordinates, solvent_last_residues


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write("\n")


def parameter_files(source):
    stock = {s.member_id:s.raw_utf8 for s in source.parent.original_source.source_members}
    existing = {line.split()[0] for sections in (_parm_dat_sections(stock["source.parm10-dat"]),
        _frcmod_sections(stock["source.ff14sb-frcmod"])) for line in sections["MASS"]}
    custom = scoped_kcx_stock(stock["source.kcx-prepin"],stock["source.kcx-frcmod"],existing_atom_types=existing)
    boundary = scoped_boundary_stock(stock["source.parm10-dat"],stock["source.ff14sb-frcmod"])
    return {"kcx-scoped.prepin":custom.scoped_prepi_utf8,"kcx-scoped.frcmod":custom.scoped_custom_frcmod_utf8,
        "kcx-boundaries.frcmod":boundary.scoped_boundary_frcmod_utf8,
        "cabp.prepi":stock["source.cabp-prepi"],"cabp.frcmod":stock["source.cabp-frcmod"]}


def join_heavy_atoms(heavy_text, census, coordinates):
    """Independent named/element/coordinate join before using a native reader."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
    original = {}
    for chain,position,component,name,element,xyz in heavy_pdb_rows(heavy_text):
        original.setdefault((chain,position,component),{})[name]=(element.upper(),xyz)
    original=solvent_last_residues(original)
    residues = _residues(census)
    if len(original) != len(residues):
        raise ValueError("constructed repair changes the full original Amber residue denominator")
    elements={"C":6,"N":7,"O":8,"P":15,"S":16,"MG":12}
    result=[]
    for (key,atoms),(name,indices) in zip(original.items(),residues,strict=True):
        chain,position,component=key
        expected={"HIS":"HIE","HID":"HIE","HOH":"WAT"}.get(component,component)
        if name.upper()!=expected.upper():
            raise ValueError("constructed repair changes the full original Amber residue sequence")
        heavy={n:i for n,i in indices.items() if census["atomic_numbers"][i]!=1}
        if set(heavy)!=set(atoms):
            raise ValueError("constructed repair changes a complete heavy atom census")
        for atom,(element,xyz) in atoms.items():
            index=heavy[atom]
            if (census["atomic_numbers"][index]!=elements[element]
                    or any(abs(a-b)>Decimal("0.000001") for a,b in zip(xyz,coordinates[index],strict=True))):
                raise ValueError("constructed repair changes an original heavy element or starting coordinate")
            result.append(((chain,position,atom),index))
    return tuple(sorted(result))


def bonded_pairs(census):
    return tuple(sorted({tuple(sorted(abs(i)//3 for i in row[:2]))
        for name,rows in census["indexed_bonded_terms"].items() if name.startswith("BONDS") for row in rows}))


def movable_atoms(census, heavy_join, constructed):
    heavy=dict(heavy_join)
    selected={heavy[key] for key in constructed}
    neighbours={i:set() for i in range(census["term_census"]["atoms"])}
    for a,b in bonded_pairs(census):
        neighbours[a].add(b);neighbours[b].add(a)
    # Amber's three-site water topology also stores the H1--H2 distance.
    # This edge does not create a second heavy parent for either hydrogen.
    water_partners={}
    if any(census["atomic_numbers"][a]==census["atomic_numbers"][b]==1 for a,b in bonded_pairs(census)):
        for name,atoms in _residues(census):
            if (name.upper()=="WAT" and set(atoms)=={"O","H1","H2"}
                    and tuple(census["atomic_numbers"][atoms[k]] for k in ("O","H1","H2"))==(8,1,1)):
                o,h1,h2=(atoms[k] for k in ("O","H1","H2"))
                if neighbours[o]=={h1,h2}:
                    water_partners[h1]={o,h2};water_partners[h2]={o,h1}
    for i,element in enumerate(census["atomic_numbers"]):
        if element==1:
            parents={j for j in neighbours[i] if census["atomic_numbers"][j]!=1}
            if len(parents)!=1 or (len(neighbours[i])!=1 and neighbours[i]!=water_partners.get(i)):
                raise ValueError("constructed repair loses a uniquely attached hydrogen")
            # Every newly added hydrogen is a construction degree of freedom.
            # Fixing hydrogens on observed heavy atoms preserved the severe
            # inter-residue H--H clash described in OPTIM.md.
            selected.add(i)
    return tuple(sorted(selected))


def execute_repair(source, directory):
    """Enter the selected common-parent initializer and bounded downstream work."""
    from empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics.native import _leap_script
    from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import complete_constructed_heavy_atoms, complete_amber_minimization, complete_force_assignment
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import assess_molecular_geometry, fixed_bond_feasibility, geometry_terms_from_amber
    import numpy as np
    from openmm import app, unit

    authenticate_numeric_engine(source.numeric_engine, loaded=True)
    origin = json.loads(source.origin_json)
    if type(source) is GpAmberFragmentRepairInput:
        from .amber_terminal_fragments import initialize_amber_terminal_fragments
        from empirical_lawhood.domains.rubisco.rubisco_response.terminal_fragment_placement import METHOD
        initialized, transformations, constructed = initialize_amber_terminal_fragments(source, directory)
        method = METHOD
    else:
        initialized, transformations, constructed = complete_constructed_heavy_atoms(source.heavy_pdb, origin, seed=source.construction_seed,
            platform_name=source.construction_platform, threads=source.construction_threads)
        method = "PDBFIXER_MISSING_HEAVY_ATOMS_AMBER_HYDROGENS_OPENMM_MINIMIZATION"
    amber_text = "\n".join(line[:17]+"HIE"+line[20:] if line.startswith(("ATOM  ", "HETATM"))
        and line[17:20] in {"HIS", "HID"} else line for line in initialized.splitlines())+"\n"
    script = _leap_script("scoped-kcx-aliases", origin).split("check model\n", 1)[0]
    script = script.replace("complete-heavy.pdb", "amber-heavy.pdb")+"check model\nsaveAmberParm model dry.prmtop dry.inpcrd\nquit\n"
    files = {**parameter_files(source), "parent-heavy.pdb": source.heavy_pdb, "initialized-heavy.pdb": initialized,
        "amber-heavy.pdb": amber_text, "atom-origin-provenance.json": source.origin_json, "build.leap": script}
    for name, text in files.items():
        with (directory/name).open("x", encoding="ascii") as stream:
            stream.write(text)
    write_json(directory/"initialization.json", dict(transformations=transformations, constructed_atoms=constructed,
        method=method,
        no_custom_terminal_search=True, no_custom_minimizer=True, physical_energy_or_ensemble_admission=False))
    if isinstance(source, GpCarboxylateRepairInput):
        terminal = initial_terminal_geometry(initialized, origin, origin_sha256=sha256(source.origin_json.encode()).hexdigest())
        with (directory/TERMINAL_GEOMETRY_FILE).open("xb") as stream:
            stream.write(terminal_geometry_bytes(terminal))
        require_initial_terminal_geometry(terminal)
    engine = source.amber_engine
    root = Path(engine.root)
    argv = amber_command(engine)
    for kind in ("prep", "lib", "parm", "cmd"):
        argv.extend(("-I", str(root/"toolchain/dat/leap"/kind)))
    argv.extend(("-f", "build.leap"))
    with (directory/"amber.stdout").open("xb") as out, (directory/"amber.stderr").open("xb") as err:
        subprocess.run(argv, cwd=directory, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "OMP_NUM_THREADS": "1",
            "AMBERHOME": str(root/"toolchain"), "LD_LIBRARY_PATH": str(root/engine.library_directory)},
            stdin=subprocess.DEVNULL, stdout=out, stderr=err, check=True)
    raw_topology = (directory/"dry.prmtop").read_bytes()
    census = assigned_census_supported_inactive14(read_prmtop(raw_topology.decode("ascii")))
    raw_coordinates, _ = read_initial_coordinates((directory/"dry.inpcrd").read_text(), census["term_census"]["atoms"], periodic=False)
    joined = join_heavy_atoms(initialized, census, raw_coordinates)
    refined = inherited_carboxylate_keys(origin) if isinstance(source, GpCarboxylateRepairInput) else ()
    movable_heavy = (*constructed, *refined)
    moving = movable_atoms(census, joined, movable_heavy)
    coordinates = np.array(raw_coordinates, float)/10
    terms = geometry_terms_from_amber(raw_topology)
    selection = dict(heavy_join=joined, movable=moving,
        constructed_heavy_count=len(constructed), fixed_heavy_count=len(joined)-len(movable_heavy),
        atom_count=census["term_census"]["atoms"], amber_term_census=census["term_census"],
        all_hydrogens_mobile=True)
    if refined:
        feasibility = fixed_bond_feasibility(coordinates*10, terms, moving, source.geometry_quality)
        selection.update(refined_inherited_heavy_atoms=refined, fixed_bond_feasibility=feasibility)
    write_json(directory/"atom-selection.json", selection)
    if refined and feasibility["violations"]:
        raise ValueError("fixed heavy bond violates the selected parent geometry screen before minimization")
    prmtop = app.AmberPrmtopFile(str(directory/"dry.prmtop"))
    system = prmtop.createSystem(nonbondedMethod=app.NoCutoff, constraints=None, rigidWater=False, removeCMMotion=False)
    write_json(directory/"force-assignment.json", complete_force_assignment(system, raw_topology, unit=unit))
    if system.getNumParticles() != len(coordinates):
        raise ValueError("native OpenMM parser changes the independently counted atom denominator")
    for actual, expected in zip((system.getParticleMass(i) for i in range(system.getNumParticles())), census["masses"], strict=True):
        if abs(actual.value_in_unit(unit.dalton)-float(expected)) > 1e-8:
            raise ValueError("native OpenMM parser changes natural atomic masses")
    initial_quality = assess_molecular_geometry(coordinates*10, terms, policy=source.geometry_quality)
    write_json(directory/"initial-whole-molecule-quality.json", initial_quality)
    started = time.monotonic()
    final, forces, result, initial_forces, system_xml = complete_amber_minimization(system, coordinates, moving,
        maximum_component=float(source.maximum_gradient_kj_mol_nm), maximum_iterations=source.maximum_iterations,
        platform_name=source.construction_platform, threads=source.construction_threads, progress_directory=directory)
    final_quality = assess_molecular_geometry(final*10, terms, policy=source.geometry_quality)
    write_json(directory/"final-whole-molecule-quality.json", final_quality)
    np.save(directory/"initial-coordinates-nm.npy", coordinates, allow_pickle=False)
    np.save(directory/"initial-forces-kj-mol-nm.npy", initial_forces, allow_pickle=False)
    np.save(directory/"final-coordinates-nm.npy", final, allow_pickle=False)
    np.save(directory/"final-forces-kj-mol-nm.npy", forces, allow_pickle=False)
    (directory/"original-system.xml").write_text(system_xml)
    heavy = dict(joined)
    repaired = replace_heavy_coordinates(source.heavy_pdb, {key: final[heavy[key]]*10 for key in movable_heavy}, movable_heavy)
    with (directory/"complete-heavy.pdb").open("x") as stream:
        stream.write(repaired)
    result.update(wall_seconds=time.monotonic()-started, interpretation=source.scope,
        whole_molecule_quality=final_quality["disposition"], no_ensemble_or_rate_admission=True)
    if refined:
        result["refined_inherited_displacements_angstrom"] = [
            [list(key), ((final[heavy[key]] - coordinates[heavy[key]])*10).tolist()] for key in refined]
    write_json(directory/"optimizer-return.json", result)
    write_json(directory/"loaded-engine-modules.json", authenticate_numeric_engine(source.numeric_engine, loaded=True))
    # Even a rejected endpoint is retained in full and independently assessed.
    return 0
