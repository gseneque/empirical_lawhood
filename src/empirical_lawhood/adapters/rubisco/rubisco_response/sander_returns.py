# SPDX-License-Identifier: MPL-2.0
"""Validate SANDER controls, restart ancestry and original native job outcomes."""

from hashlib import sha256
import json
from pathlib import Path
import re

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.precursor_geometry import oxygen_motif
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def _namelist(text, group):
    # A control value may contain a comma-separated atom list or an Amber atom mask.
    block = re.search(r"(?ims)^\s*&" + group + r"\b(.*?)/", text)
    if block is None:
        raise ValueError(f"missing SANDER {group} namelist")
    body = block[1]
    fields = list(re.finditer(r"\b([a-z]\w*)\s*=\s*", body, flags=re.I))
    values = {}
    for i, match in enumerate(fields):
        name = match[1].lower()
        if name in values:
            raise ValueError(f"duplicate SANDER setting {name}")
        stop = fields[i + 1].start() if i + 1 < len(fields) else len(body)
        values[name] = "".join(body[match.end():stop].split()).strip(",")
    return values


def _original_controls(directory, job, spec):
    text = read_bounded_bytes(directory / "mdin", maximum_bytes=1024**2).decode("ascii")
    control, qm = _namelist(text, "cntrl"), _namelist(text, "qmmm")
    quantum = spec["QM_native_zero_based"]
    if (len(quantum) != 121 or len(set(quantum)) != len(quantum)
            or min(quantum) < 0 or max(quantum) >= spec["atom_count"]
            or list(map(int, qm["iqmatoms"].split(","))) != [i + 1 for i in quantum]):
        raise ValueError("SANDER input differs from the material's selected quantum atoms")
    if (qm["qm_theory"].strip("'").upper() != "DFTB3" or int(qm["qmcharge"]) != -2
            or int(qm["spin"]) != 1 or int(qm["qmshake"]) != 0
            or int(qm["qm_ewald"]) != 1 or int(qm["qm_pme"]) != 1 or float(qm["qmcut"]) != 8):
        raise ValueError("SANDER quantum Hamiltonian differs from the selected precursor")
    electronic = job.get("electronic_temperature_K")
    if ((electronic is None) != ("dftb_telec" not in qm)
            or electronic is not None and float(qm["dftb_telec"]) != electronic
            or int(qm["dftb_maxiter"]) != (200 if electronic is None else 500)):
        raise ValueError("SANDER electronic occupation differs from the selected execution")
    stage = job["stage"]
    steps, stride = job["steps"], job["stride"]
    if (stage not in {"condition", "condition_local", "probe", "forcecheck", "release", "release_mmshake"}
            or type(steps) is not int or type(stride) is not int or not 1 <= stride <= steps
            or type(job["continuation"]) is not bool or type(job["seed"]) is not int):
        raise ValueError("invalid SANDER stage, seed or output interval")
    expected = dict(ntb=1, ifqnt=1, cut=8, ntpr=1 if stage == "probe" else stride,
                    ntx=5 if job["continuation"] else 1, irest=int(job["continuation"]))
    if stage in ("condition", "condition_local", "probe"):
        expected.update(imin=1, nmropt=1, maxcyc=steps)
        if job["files"].get("conditioning.RST") != spec["conditioning_files"][job["origin"]]["conditioning.RST"]:
            raise ValueError("SANDER minimization differs from the original restraints")
    else:
        bond_mode = 1 if stage == "release" else 2
        expected.update(imin=0, dt=0.0005, ntc=bond_mode, ntf=bond_mode, ioutfm=1,
                        nstlim=steps, ntwx=stride, ntt=3, gamma_ln=2, tempi=298.15,
                        temp0=298.15, nmropt=0, ntr=0, ntwf=min(steps, 5 * stride))
    if any(float(control[k]) != v for k, v in expected.items()):
        raise ValueError("SANDER control input differs from its declared numerical settings")
    return control, qm


def _release_settings(settings):
    control, quantum = settings
    segment_fields = {"ntx", "irest", "ig", "nstlim", "ntwf"}
    return {"control": {k: v for k, v in control.items() if k not in segment_fields}, "quantum": quantum}


def _restart(directory, job, jobs, settings, spec, root, engine_digest, material_digest):
    start = Path(job["start"])
    if (job["engine_manifest_sha256"] != engine_digest or job["material_sha256"] != material_digest
            or job["topology_sha256"] != spec["parent"]["checked_inputs"][spec["topology"]]
            or job["origin"] not in spec["conditioning_files"]):
        raise ValueError("SANDER job changes engine, material, topology or initial preparation")
    prior_steps = 0
    if start.name == "start.rst7":
        origin = root / job["case"] / job["origin"]
        if (job["continuation"] or start.parent != origin
                or job["start_sha256"] != spec["conditioning_files"][job["origin"]][start.name]):
            raise ValueError("SANDER job substitutes its original authored start")
    elif start.name == "final.ncrst" and start.parent in jobs and start.parent != directory:
        parent = jobs[start.parent]
        scope = ("case", "origin", "material_sha256", "topology_sha256", "engine_manifest_sha256")
        if (any(job[k] != parent[k] for k in scope) or parent["exit"] != 0
                or parent["files"].get(start.name) != job["start_sha256"]
                or parent["ended_unix"] > job["started_unix"]):
            raise ValueError("SANDER restart changes its original parent or custody")
        if job["continuation"]:
            if (job["stage"] not in ("release", "release_mmshake")
                    or any(job[k] != parent[k] for k in ("stage", "seed", "stride"))
                    or job.get("electronic_temperature_K") != parent.get("electronic_temperature_K")):
                raise ValueError("SANDER continuation changes parent stage, seed, stride or occupation")
            if _release_settings(settings[directory]) != _release_settings(settings[start.parent]):
                raise ValueError("SANDER continuation changes the parent's numerical settings")
            prior_steps = parent.get("cumulative_steps", parent["steps"])
    else:
        raise ValueError("SANDER job lacks its original authored start or issued parent")
    thermostat = job["seed"] + 100003 + prior_steps if job["continuation"] else job["seed"]
    control = settings[directory][0]
    if (job.get("cumulative_steps", job["steps"]) != prior_steps + job["steps"]
            or job.get("thermostat_seed", job["seed"]) != thermostat
            or "ig" in control and int(control["ig"]) != thermostat):
        raise ValueError("SANDER continuation changes cumulative steps or derived thermostat seed")
    return prior_steps


def _completion(directory, job, spec):
    output = read_bounded_bytes(directory / "mdout", maximum_bytes=64 * 1024**2).decode("ascii", errors="replace")
    converged = "convergence could not be achieved" not in output.lower()
    normal_completion = "5.  TIMINGS" in output and "final.ncrst" in job["files"]
    diagnostic = None
    if job["stage"] == "forcecheck":
        atom = spec["labels"]["ligand.HO3"] + 1
        rms = re.search(r"RMS force error\s*=\s*([0-9.Ee+-]+)", output)
        components = re.search(r"from atom\s+" + str(atom) + r"\b\s*\n((?:\s*[123]\s+[-+\d.Ee]+\s+[-+\d.Ee]+\s+[-+\d.Ee]+\s*\n){3})", output)
        force_pass = bool(rms and float(rms[1]) < 0.01 and re.search(rf"from atom\s+{atom}\b", output))
        diagnostic = dict(atom_one_based=atom, relative_rms_error=float(rms[1]) if rms else None,
                          components_numeric_analytic_difference=([[float(x) for x in row.split()[1:]] for row in components[1].splitlines()] if components else []),
                          force_check_passed=job["native_exit"] == 0 and converged and force_pass)
        # Early wrappers required an MD restart even when the debug driver returned its numerical forces.
        complete = normal_completion if job["exit"] and not normal_completion else force_pass
    else:
        complete = normal_completion
    if type(job["native_exit"]) is not int or job["exit"] != int(not (complete and converged and job["native_exit"] == 0)):
        raise ValueError("SANDER receipt status disagrees with the native completion or failure")
    usage = read_bounded_bytes(directory / "resources", maximum_bytes=64 * 1024).decode("ascii").splitlines()[-1].split()
    user, system, memory, wall = map(float, usage)
    if (abs(user + system - job["actual_cpu_s"]) > 1e-8 or memory != job["peak_RSS_KiB"]
            or wall != job["wall_s"] or min(user, system, memory, wall) < 0):
        raise ValueError("SANDER resource receipt differs from measured native work")
    return output, diagnostic


def continuation_controls(root, directory, jobs, spec, engine_digest, material_digest, steps):
    """Validate the original chain and derive the new thermostat seed on its source clock."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.sander_trajectory import verify_dynamics_restart

    parent = jobs[directory]
    if (parent["stage"] not in ("release", "release_mmshake") or parent["exit"] != 0
            or "final.ncrst" not in parent["files"]):
        raise ValueError("SANDER continuation requires a successful released parent and its restart")
    if type(steps) is not int or not parent["stride"] <= steps < 2**31:
        raise ValueError("SANDER continuation length must include its inherited sampling interval")
    settings = {path: _original_controls(path, job, spec) for path, job in jobs.items()}
    for path, job in jobs.items():
        _restart(path, job, jobs, settings, spec, root, engine_digest, material_digest)
        _completion(path, job, spec)
    previous = parent.get("cumulative_steps", parent["steps"])
    verify_dynamics_restart(directory / "final.ncrst", spec, previous)
    thermostat_seed = parent["seed"] + 100003 + previous
    if not 0 < thermostat_seed < 2**31 or previous + steps >= 2**31:
        raise ValueError("SANDER continuation exceeds the native integer range")
    updates = dict(ntx=5, irest=1, ig=thermostat_seed, nstlim=steps, ntwf=min(steps, 5 * parent["stride"]))
    original = read_bounded_bytes(directory / "mdin", maximum_bytes=1024**2).decode("ascii")
    control_block = re.search(r"(?ims)^\s*&cntrl\b(.*?)/", original)
    text = control_block[1]
    for key, value in updates.items():
        text, count = re.subn(r"(\b" + key + r"\s*=\s*)[+-]?\d+(?=\s*,|\s*$)",
                              lambda match: match[1] + str(value), text, flags=re.I | re.M)
        if count != 1:
            raise ValueError(f"cannot bind original SANDER control {key} unambiguously")
    amended = original[:control_block.start(1)] + text + original[control_block.end(1):]
    before, quantum = settings[directory]
    if (_namelist(amended, "cntrl") != dict(before, **{k: str(v) for k, v in updates.items()})
            or _namelist(amended, "qmmm") != quantum):
        raise ValueError("SANDER continuation changes its original Hamiltonian or sampling")
    return amended.encode("ascii"), previous, thermostat_seed


def _material_frames(root, case, spec, reference):
    s = dict(spec)
    with (root / case / "all_water_oxygens.npy").open("rb") as stream:
        waters = np.load(stream, allow_pickle=False)
    atoms = json.loads(read_bounded_bytes(spec["atom_map"], maximum_bytes=128 * 1024**2))["atoms"]
    if (len(atoms) != spec["atom_count"] or waters.ndim != 1 or not np.issubdtype(waters.dtype, np.integer)
            or not len(waters) or len(set(waters.tolist())) != len(waters)
            or waters.min() < 0 or waters.max() + 2 >= len(atoms)
            or any([atoms[i + j][1] for j in range(3)] != ["O", "H1", "H2"] for i in waters)):
        raise ValueError("SANDER material changes the complete original atom or water mapping")
    s["heavy_native_indices"] = np.asarray([i for i, a in enumerate(atoms) if a[2] != "H"], dtype=int)
    s["reference_motif"] = reference
    owners = np.asarray([i for i, a in enumerate(atoms) if a[2] in {"C", "N", "O", "S", "P"}], dtype=int)
    return s, waters, owners


def read_sander_jobs(root, engine_digest, materials, material_digests, jobs, reference_root):
    """Consume only while the caller owns the complete original source verification scope."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.sander_trajectory import read_release

    settings = {path: _original_controls(path, job, materials[job["case"]]) for path, job in jobs.items()}
    frames, observations, references = {}, {}, {}
    for directory, job in sorted(jobs.items(), key=lambda item: item[1]["started_unix"]):
        case = job["case"]
        spec = materials[case]
        prior_steps = _restart(directory, job, jobs, settings, spec, root, engine_digest, material_digests[case])
        output, diagnostic = _completion(directory, job, spec)
        row = {"stage": job["stage"], "case": case, "origin": job["origin"], "seed": job["seed"],
               "native_exit": job["native_exit"], "exit": job["exit"], "cpu_s": job["actual_cpu_s"],
               "wall_s": job["wall_s"], "peak_RSS_KiB": job["peak_RSS_KiB"],
               "status": "complete" if job["exit"] == 0 else "native failure"}
        if diagnostic is not None:
            row["force_diagnostic"] = diagnostic
        if job["stage"] in ("release", "release_mmshake"):
            if case not in frames:
                sources = spec["inputs"]
                paths = tuple(next(reference_root / n for n in sources if n.endswith(ext)) for ext in (".pdf", ".txt"))
                if paths not in references:
                    references[paths] = oxygen_motif(*(read_bounded_bytes(p, maximum_bytes=128 * 1024**2) for p in paths))
                frames[case] = _material_frames(root, case, spec, references[paths])
            prefix = observations[Path(job["start"]).parent] if job["continuation"] else None
            row["assigned_post_entry_frames"] = (prefix["assigned_post_entry_frames"] if prefix else 0) + job["steps"] // job["stride"]
            row["frame_interval_fs"] = job["stride"] * 0.5
            row["release_settings_sha256"] = sha256(canonical_json_bytes(_release_settings(settings[directory]))).hexdigest()
            row.update(read_release(directory, job, output, *frames[case], prefix=prefix, prior_steps=prior_steps))
        observations[directory] = row
    return {str(p.relative_to(root)): row for p, row in observations.items()}
