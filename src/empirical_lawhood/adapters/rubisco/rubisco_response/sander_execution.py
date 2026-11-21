# SPDX-License-Identifier: MPL-2.0
"""Execute one inherited gas-free SANDER segment and bind the original returned native bytes."""

from hashlib import sha256
import re
import time

import numpy as np
from scipy.io import netcdf_file

from empirical_lawhood.adapters.rubisco.rubisco_response.sander_trajectory import (
    _box, _clock, _released_settings, verify_dynamics_restart,
)
from empirical_lawhood.execution.local.bounded_process import BoundedProcessError, run_bounded_command
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_census import FileHashCensus
from empirical_lawhood.storage.native_installation import real_path


def _files(directory):
    with FileHashCensus() as census:
        return {p.name: census.sha256(real_path(p), maximum_bytes=None)[1] for p in directory.iterdir()}


def _frame_count(path, variable, units, *, info, material, interval, complete):
    expected = info["steps"] // interval
    if not path.exists() and not complete:
        return 0
    with netcdf_file(path, "r", mmap=True) as nc:
        field = nc.variables[variable]
        try:
            count = field.shape[0]
            if (field.units != units or field.shape[1:] != (material["atom_count"], 3)
                    or count > expected or complete and count != expected):
                raise ValueError("SANDER continuation changes receiver units, frame count or atom count")
            times = (info["initial_step"] + interval * np.arange(1, count + 1)) * 0.5
            _clock(nc, times, complete=True)
            for i in range(count):
                if not np.isfinite(field[i]).all():
                    raise ValueError("SANDER continuation contains nonfinite measurements")
                if variable == "coordinates":
                    _box(nc, material, i)
            return count
        finally:
            del field


def _inspect(directory, info, material, status, failure):
    native = directory / "mdout"
    text = read_bounded_bytes(native, maximum_bytes=64 * 1024**2).decode("ascii", errors="replace") if native.exists() else ""
    converged = "convergence could not be achieved" not in text.lower()
    ended = "5.  TIMINGS" in text
    restart = directory / "final.ncrst"
    complete = status == 0 and converged and ended and restart.is_file()
    if complete:
        last_printed = info["steps"] // info["stride"] * info["stride"]
        if not _released_settings(text) or not re.search(r"\bNSTEP\s*=\s*" + str(last_printed) + r"\b", text):
            raise ValueError("SANDER continuation lacks its last scheduled observation or original Hamiltonian")
        restraint = [float(v) for v in re.findall(r"RESTRAINT\s*=\s*([-+\d.Ee]+)", text)]
        if not restraint or any(restraint):
            raise ValueError("SANDER continuation retained a restraint")
        verify_dynamics_restart(restart, material, info["cumulative_steps"])
    stride = info["stride"]
    force_interval = min(info["steps"], 5 * stride)
    coordinates = _frame_count(directory / "trajectory.nc", "coordinates", b"angstrom", info=info,
                               material=material, interval=stride, complete=complete)
    forces = _frame_count(directory / "forces.nc", "forces", b"kilocalorie/mole/angstrom", info=info,
                          material=material, interval=force_interval, complete=complete)
    elapsed = re.search(r"Elapsed\(s\)\s*=\s*([\d.]+)", text)
    return dict(status="complete" if complete else "failed", native_exit=status, process_failure=failure,
                reached_native_timing_section=ended, native_convergence_failure=not converged,
                expected_coordinate_frames=info["steps"] // stride, returned_coordinate_frames=coordinates,
                expected_force_frames=info["steps"] // force_interval, returned_force_frames=forces,
                native_reported_elapsed_s=float(elapsed[1]) if elapsed else None)


def execute_continuation(info, control, material, restart, engine, directory, timeout_seconds):
    """Consume only inside the application's active engine and original-parent verification."""
    if sha256(control).hexdigest() != info["control_sha256"]:
        raise ValueError("SANDER continuation changes its prepared controls")
    (directory / "mdin").write_bytes(control)
    command = [str(engine / "lib/ld-linux-x86-64.so.2"), "--library-path", str(engine / "lib"), str(engine / "bin/sander"),
               "-i", "mdin", "-o", "mdout", "-p", str(real_path(material["topology"])), "-c", str(restart),
               "-r", "final.ncrst", "-x", "trajectory.nc", "-frc", "forces.nc", "-inf", "mdinfo"]
    environment = {"AMBERHOME": str(engine), "LC_ALL": "C", "OMP_NUM_THREADS": "1",
                   "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    begin = time.monotonic()
    status, failure = None, None
    try:
        result = run_bounded_command(command, cwd=directory, environment=environment, timeout_seconds=timeout_seconds,
                                     maximum_stdout_bytes=4 * 1024**2, maximum_stderr_bytes=4 * 1024**2)
        status = result.returncode
        (directory / "stdout.txt").write_bytes(result.stdout)
        (directory / "stderr.txt").write_bytes(result.stderr)
    except BoundedProcessError as error:
        failure = str(error)
    wall = time.monotonic() - begin
    files = _files(directory)
    if files.get("mdin") != info["control_sha256"]:
        raise ValueError("SANDER native control file changed during execution")
    try:
        measurement = _inspect(directory, info, material, status, failure)
    finally:
        if _files(directory) != files:
            raise ValueError("SANDER native return changed during inspection")
    return dict(info, **measurement, files=files, native_wall_seconds=wall, deadline_seconds=timeout_seconds,
                scope="One gas-free conditional continuation of the selected original preparation.")
