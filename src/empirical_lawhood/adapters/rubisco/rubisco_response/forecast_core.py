# SPDX-License-Identifier: MPL-2.0
"""Standard Amber preparation of the observed Gp core for a separate forecast."""

from collections import Counter
from hashlib import file_digest, sha256
from io import StringIO
from itertools import groupby
import json
import os
import resource
from pathlib import Path
import subprocess
import time

from .initial_amber_native import select_gp_amber_parameters
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import (
    StructuralSourceMember,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import (
    proper_rigid_fit,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import (
    GpAmberEngine,
    initial_leap_script,
    initial_parameter_files,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import (
    amber_command,
    authenticate_engine,
)
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import (
    prepare_rubp_tetraanion,
)
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes

CASES = ("V1-WT", "V1-I95M", "M1-WT", "M1-I95M")
SSU, LSU = "BDFHJLNP", "ACEGIKMO"
SCAFFOLD_SHA256 = "c5c1f53ed33bdbb05b965e7b9502df1b6f54f2a28f437e1d3c76f0a8b759f258"
MET1_SHA256 = "17f21c59c901b6d03197e4937b73ccc4b8266bbf427b3f436bddaa0fb7d19a0f"


def digest(path):
    with Path(path).open("rb") as reader:
        return file_digest(reader, "sha256").hexdigest()


def write_json(path, value):
    with path.open("x") as output:
        json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)
        output.write("\n")


def residue_key(row):
    return row[21], int(row[22:26]), row[26], row[17:20].strip()


def observed_residues(pdb_text):
    rows = (
        row for row in pdb_text.splitlines() if row.startswith(("ATOM  ", "HETATM"))
    )
    return [(key, list(group)) for key, group in groupby(rows, residue_key)]


def xyz(row):
    return [float(row[i : i + 8]) for i in (30, 38, 46)]


def met_donors(raw):
    from openmm import app, unit

    if sha256(raw).hexdigest() != MET1_SHA256:
        raise ValueError(
            "The selected Met1 donor differs from the deposited 1IWA coordinates"
        )
    model = app.PDBxFile(StringIO(raw.decode("utf-8")))
    points = model.getPositions(asNumpy=True).value_in_unit(unit.angstrom)
    result = {}
    for chain in model.topology.chains():
        if chain.id in SSU:
            site = next(chain.residues())
            if (site.name, site.id) != ("MET", "8"):
                raise ValueError("1IWA donor lacks the designated SSU Met1")
            result[chain.id] = {atom.name: points[atom.index] for atom in site.atoms()}
    if set(result) != set(SSU):
        raise ValueError("Incomplete donor chain population")
    return result


def prepare_coordinates(pdb_text, case, donors, ligand):
    """Use the observed core, transfer measured Met1 and leave I95M completion to LEaP."""
    import numpy as np

    if (
        case not in CASES
        or sha256(pdb_text.encode("ascii")).hexdigest() != SCAFFOLD_SHA256
    ):
        raise ValueError("An unknown material or published 1BWV input was selected")
    ligand_atoms = {
        a.native_atom_name: a.atomic_number
        for a in ligand.chemical_graph.atoms
        if a.atomic_number > 1
    }
    template = {
        n: np.asarray(v, dtype=float) for n, v in ligand.template_coordinates_angstrom
    }
    output, substitutions, placements = [], [], []
    counts = Counter()
    previous = None
    for (chain, number, insertion, component), rows in observed_residues(pdb_text):
        counts[chain, "ligand" if component in ("MG", "CAP") else "protein"] += 1
        if previous and (previous != chain or component in ("MG", "CAP")):
            output.append("TER")
        previous = chain
        atoms = {r[12:16].strip(): r for r in rows if r[76:78].strip() != "H"}
        positions = {atom: xyz(row) for atom, row in atoms.items()}
        old = component
        if chain in SSU and insertion == " " and number in (8, 112):
            expected = "VAL" if number == 8 else "ILE"
            if component != expected:
                raise ValueError("Source sequence differs at a selected SSU position")
            if (number == 8 and case.startswith("M1")) or (
                number == 112 and case.endswith("I95M")
            ):
                component = "MET"
                keep = ("N", "CA", "C", "O", "CB")
                positions = {name: positions[name] for name in keep}
                if number == 8:
                    anchor = ("N", "CA", "C", "CB")
                    native = donors[chain]
                    rot, shift, _ = proper_rigid_fit(
                        [native[n] for n in anchor], [positions[n] for n in anchor]
                    )
                    positions.update(
                        {n: native[n] @ rot + shift for n in ("CG", "SD", "CE")}
                    )
                substitutions.append([chain, number, old, component])
        if component == "CAP":
            names = tuple(ligand_atoms)
            if set(positions) != set(names) | {"C", "O6", "O7"}:
                raise ValueError("Inhibitor to substrate atom mapping differs")
            rot, shift, rmsd = proper_rigid_fit(
                [template[n] for n in names], [positions[n] for n in names]
            )
            positions = {n: template[n] @ rot + shift for n in names}
            component = "RUB"
            placements.append([chain, float(rmsd)])
        for name, point in positions.items():
            row = atoms.get(name)
            elem = row[76:78].strip() if row else ("S" if name == "SD" else "C")
            label = name.rjust(4) if len(elem) == 2 else (" " + name).ljust(4)
            record = "HETATM" if component in ("MG", "RUB", "KCX") else "ATOM  "
            output.append(
                f"{record}{len(output) + 1:5d} {label} {component:3s} {chain}{number:4d}{insertion}   "
                + "".join(f"{v:8.3f}" for v in point)
                + f"  1.00  0.00          {elem:>2}  "
            )
    if (
        any(counts[c, "protein"] != 472 or counts[c, "ligand"] != 2 for c in LSU)
        or any(counts[c, "protein"] != 138 for c in SSU)
        or len(placements) != 8
    ):
        raise ValueError("Published observed-core population changed")
    return "\n".join([*output, "TER", "END", ""]), {
        "case": case,
        "substitutions": substitutions,
        "ligand_fit_rmsd_angstrom": placements,
        "LSU_linear_range": [15, 486],
        "cut_end_treatment": "charged Amber termini",
        "state": "keto-RuBP(4-), published histidine names",
    }


def build_case(selection, case, directory):
    """Write native products into an explicit fresh directory. Report any failed attempt."""

    start = time.monotonic()
    cpu_start = time.process_time()
    child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    directory.mkdir(parents=False, exist_ok=False)
    try:
        sources = {}
        for name in ("core", "met1", "rub", "amber_engine", "parameter_selection"):
            spec = selection[name]
            path = Path(spec["path"])
            raw = read_bounded_bytes(path, maximum_bytes=64 * 2**20)
            if sha256(raw).hexdigest() != spec["sha256"]:
                raise ValueError(f"Changed selected input {name}")
            sources[name] = raw
        engine = decode_canonical_bytes(
            sources["amber_engine"], GpAmberEngine, maximum_bytes=2**21
        )
        authenticate_engine(engine)
        members = json.loads(sources["parameter_selection"])["members"]
        params = select_gp_amber_parameters(members=members)
        source = StructuralSourceMember(
            "RUB.cif",
            "https://files.rcsb.org/ligands/download/RUB.cif",
            selection["rub"]["sha256"],
            sources["rub"].decode("utf-8"),
        )
        ligand = prepare_rubp_tetraanion(
            source, preparation_id="preparation.forecast-core.keto-rubp"
        )
        pdb, detail = prepare_coordinates(
            sources["core"].decode("ascii"), case, met_donors(sources["met1"]), ligand
        )
        write_json(directory / "selection.json", selection)
        write_json(directory / "coordinates.json", detail)
        (directory / "library-heavy.pdb").write_text(pdb)
        for name, raw in initial_parameter_files(params, ligand).items():
            (directory / name).write_text(raw)
        (directory / "build.leap").write_text(
            initial_leap_script(
                random_solvent_replacement=True, explicit_solvated_check=False
            )
        )
        stock = Path(engine.root) / "toolchain"
        argv = amber_command(engine)
        for part in ("prep", "lib", "parm", "cmd"):
            argv += ["-I", str(stock / "dat/leap" / part)]
        env = dict(
            PATH=os.defpath,
            AMBERHOME=str(stock),
            LC_ALL="C",
            OMP_NUM_THREADS="1",
            LD_LIBRARY_PATH=str(Path(engine.root) / engine.library_directory),
        )
        with (
            (directory / "leap.stdout").open("xb") as out,
            (directory / "leap.stderr").open("xb") as err,
        ):
            try:
                subprocess.run(
                    [*argv, "-f", "build.leap"],
                    cwd=directory,
                    env=env,
                    stdout=out,
                    stderr=err,
                    stdin=subprocess.DEVNULL,
                    check=True,
                )
            finally:
                authenticate_engine(engine)
        if "Errors = 0;" not in (directory / "leap.stdout").read_text():
            raise ValueError("Amber reported errors")
        files = {
            name: digest(directory / name)
            for name in (
                "dry.prmtop",
                "dry.inpcrd",
                "model.prmtop",
                "model.inpcrd",
                "library-heavy.pdb",
                "build.leap",
            )
        }
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        child_cpu = (usage.ru_utime - child_start.ru_utime) + (usage.ru_stime - child_start.ru_stime)
        write_json(
            directory / "built.json",
            {
                "case": case,
                "files": files,
                "wall_s": time.monotonic() - start,
                "cpu_s": time.process_time() - cpu_start + child_cpu,
                "selection_sha256": digest(directory / "selection.json"),
                "producer_sha256": digest(__file__),
            },
        )
    except Exception as exc:
        write_json(
            directory / "build-failure.json",
            {"case": case, "error": str(exc), "wall_s": time.monotonic() - start},
        )
        raise
