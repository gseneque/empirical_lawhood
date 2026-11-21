# SPDX-License-Identifier: MPL-2.0
"""Decode original periodic SANDER coordinates and forces up to the last reported step."""

import re
from pathlib import Path

import numpy as np
from scipy.io import netcdf_file

from empirical_lawhood.domains.rubisco.rubisco_response.precursor_geometry import CUTOFFS, geometry, summarize


def _clock(netcdf, expected, *, complete):
    field = netcdf.variables["time"]
    times = field[:].astype(float) * 1000
    if (field.units != b"picosecond" or (complete and len(times) != len(expected))
            or len(times) < len(expected) or not np.allclose(times[:len(expected)], expected, atol=0.002, rtol=0)):
        raise ValueError("SANDER output changes its assigned femtosecond sample grid")


def _box(netcdf, spec, index=Ellipsis):
    lengths, angles = netcdf.variables["cell_lengths"], netcdf.variables["cell_angles"]
    box = lengths[index].astype(float)
    if (lengths.units != b"angstrom" or angles.units != b"degree" or box.shape != (3,)
            or not np.allclose(box, spec["box_A"], atol=1e-4, rtol=0)
            or not np.allclose(angles[index], [90., 90., 90.], atol=1e-4, rtol=0)):
        raise ValueError("SANDER output changes the original orthorhombic NVT cell")
    return box


def _restart_geometry(path, spec, waters, owners):
    with netcdf_file(path, "r", mmap=False) as nc:
        coords = nc.variables["coordinates"]
        if coords.units != b"angstrom":
            raise ValueError("SANDER restart coordinates must be in angstrom")
        return geometry(coords[:].astype(float), _box(nc, spec), spec, waters, owners)


def verify_dynamics_restart(path, spec, cumulative_steps):
    """Check the native NVT state before continuation and after its successor returns."""
    with netcdf_file(path, "r", mmap=True) as nc:
        if (nc.Conventions != b"AMBERRESTART" or nc.variables["time"].units != b"picosecond"
                or nc.variables["time"].shape != ()
                or not np.isclose(float(nc.variables["time"].data), cumulative_steps * 0.0005, atol=2e-6, rtol=0)):
            raise ValueError("SANDER continuation restart changes its physical clock")
        _box(nc, spec)
        for name, units in (("coordinates", b"angstrom"), ("velocities", b"angstrom/picosecond")):
            field = nc.variables[name]
            try:
                if (field.units != units or field.shape != (spec["atom_count"], 3)
                        or not np.isfinite(field[:]).all()):
                    raise ValueError("SANDER continuation has an incomplete final physical state")
            finally:
                del field


def _released_settings(native):
    return all(re.search(pattern, native) for pattern in (
        r"nquant\s*=\s*121", r"nlink\s*=\s*7", r"qmcharge\s*=\s*-2", r"qmshake\s*=\s*0",
        r"qm_ewald\s*=\s*1 qm_pme = True", r"DFTB3 method citation", r"qmqmdx = Analytical",
        r"nmropt\s*=\s*0", r"ibelly\s*=\s*0, ntr\s*=\s*0",
    ))


def read_release(directory, job, native, spec, waters, owners, *, prefix, prior_steps):
    before = re.split("convergence could not be achieved", native, maxsplit=1, flags=re.I)[0]
    complete = job["exit"] == 0
    if prefix is not None and prefix["status"] != "complete":
        raise ValueError("SANDER continuation requires a complete authenticated prefix")
    if complete:
        steps = job["steps"]
    else:
        steps = int((re.findall(r"NSTEP\s*=\s*(\d+)", before) or ["0"])[-1])
        if before == native or "trajectory.nc" not in job["files"]:
            return {"status": "native failure", "segment_observed_steps": 0, "frames": list(prefix["frames"]) if prefix else []}
    if not 0 <= steps <= job["steps"] or not _released_settings(native):
        raise ValueError("SANDER output changes the unrestrained Hamiltonian or assigned step count")
    restraint = [float(v) for v in re.findall(r"RESTRAINT\s*=\s*([-+\d.Ee]+)", before)]
    if (steps and not restraint) or any(restraint):
        raise ValueError("SANDER unrestrained release retained restraint energy")
    start = Path(job["start"])
    root = _restart_geometry(directory / "entry.ncrst" if start.suffix == ".rst7" else start, spec, waters, owners)
    frames = list(prefix["frames"]) if prefix else [dict(time_fs=0., **root)]
    forces = list(prefix["forces_kcal_mol_A"]) if prefix else []
    temperatures = list(prefix["temperature_K"]) if prefix else []
    offset = prior_steps * 0.5
    if frames[-1]["time_fs"] != offset:
        raise ValueError("SANDER continuation starts outside the parent's measured frame grid")
    coordinate_times = offset + np.arange(job["stride"], steps + 1, job["stride"]) * 0.5
    if len(coordinate_times):
        with netcdf_file(directory / "trajectory.nc", "r", mmap=True) as nc:
            _clock(nc, coordinate_times, complete=complete)
            coords = nc.variables["coordinates"]
            if coords.units != b"angstrom" or coords.shape[1:] != (spec["atom_count"], 3):
                raise ValueError("SANDER trajectory changes its coordinate units or atom census")
            try:
                for i, t in enumerate(coordinate_times):
                    observation = geometry(coords[i].astype(float), _box(nc, spec, i), spec, waters, owners)
                    frames.append(dict(time_fs=float(t), **observation))
            finally:
                del coords
    if complete:
        final = _restart_geometry(directory / "final.ncrst", spec, waters, owners)
        for k in ("maximum_contact_A", "C2_C3_A", "protons_A", "mg_donors_A", "nearest_water_A"):
            if not np.allclose(frames[-1][k], final[k], rtol=0, atol=2e-5):
                raise ValueError("SANDER final restart and last trajectory frame disagree")
    interval = min(job["steps"], job["stride"] * 5)
    force_times = offset + np.arange(interval, steps + 1, interval) * 0.5
    if len(force_times):
        with netcdf_file(directory / "forces.nc", "r", mmap=True) as nc:
            _clock(nc, force_times, complete=complete)
            force = nc.variables["forces"]
            if force.units != b"kilocalorie/mole/angstrom" or force.shape[1:] != (spec["atom_count"], 3):
                raise ValueError("SANDER forces change their units or atom census")
            try:
                for i, t in enumerate(force_times):
                    norm = np.linalg.norm(force[i], axis=1)
                    if not np.isfinite(norm).all():
                        raise ValueError("nonfinite SANDER force observation")
                    forces.append(dict(time_fs=float(t), peak_all=float(norm.max()),
                                       peak_QM=float(norm[spec["QM_native_zero_based"]].max())))
            finally:
                del force
    series = re.findall(r"NSTEP\s*=\s*(\d+)\s+TIME\(PS\)\s*=\s*[.\d]+\s+TEMP\(K\)\s*=\s*([.\d]+)", before)
    prints_entry = bool(series and int(series[0][0]) == 0)
    count = len(coordinate_times) + int(prints_entry)
    if len(series) < count:
        raise ValueError("SANDER temperatures omit an assigned observed time")
    values = [float(temp) for _, temp in series[:count]]
    # A failed segment before its first scheduled frame supplies no new temperature observation.
    if complete or len(coordinate_times):
        temperatures.extend(values[int(prints_entry):] if prefix else values)
    return dict(status="complete" if complete else "truncated", segment_observed_steps=steps, frames=frames,
                temperature_K=temperatures, forces_kcal_mol_A=forces,
                cutoffs_A={str(k): summarize(frames, k) for k in CUTOFFS})
