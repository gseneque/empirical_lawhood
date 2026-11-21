# SPDX-License-Identifier: MPL-2.0
"""Durable, process-local observations from an entered geometry minimization."""

import math
from numbers import Real
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from empirical_lawhood.storage.atomic_files import rename_noreplace


def retain_evaluation(directory, number, phase, coordinates, energy, forces, *, first=False):
    """Publish a complete finite state in the historical progress-file format."""
    coordinates = np.asarray(coordinates, dtype=np.float64)
    forces = np.asarray(forces, dtype=np.float64)
    if (type(number) is not int or number < 1 or type(phase) is not str or not phase
            or coordinates.ndim != 2 or coordinates.shape[1] != 3 or not len(coordinates)
            or forces.shape != coordinates.shape or not np.isfinite(coordinates).all()
            or not np.isfinite(forces).all() or not isinstance(energy, Real)
            or isinstance(energy, bool) or not math.isfinite(energy)):
        raise ValueError("retained repair evaluation requires complete finite coordinates, forces and identity")
    directory = Path(directory)
    destination = directory / "lowest-energy-evaluation.npz"
    temporary = NamedTemporaryFile(dir=directory, prefix=".repair-", suffix=".pending", delete=False)
    pending = Path(temporary.name)
    try:
        with temporary as stream:
            np.savez(stream, coordinates_nm=coordinates, forces_kj_mol_nm=forces,
                     energy_kj_mol=float(energy), evaluation=number, phase=phase, progress_only=True)
            stream.flush()
            os.fsync(stream.fileno())
        if first:
            rename_noreplace(pending, destination)
        else:
            os.replace(pending, destination)
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        pending.unlink(missing_ok=True)


def repair_evaluation_reporter(mm, unit, context, directory, initial_state, initial_energy, initial_forces):
    """Observe improving OpenMM callbacks on the active, complete force system."""
    points = initial_state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    retain_evaluation(directory, 1, "openmm-initial", points, initial_energy, initial_forces, first=True)

    class Reporter(mm.MinimizationReporter):
        def __init__(self, selected_context):
            super().__init__()
            self.context = selected_context
            self.ordinal = 1
            self.lowest_energy = initial_energy

        def retain_if_lower(self, phase, coordinates, energy, forces):
            if not math.isfinite(energy):
                raise ValueError("retained repair evaluation requires a finite system energy")
            if energy < self.lowest_energy:
                retain_evaluation(directory, self.ordinal, phase, coordinates, energy, forces)
                self.lowest_energy = energy

        def report(self, iteration, x, grad, args):
            self.ordinal += 1
            reported = args["system energy"]
            if not math.isfinite(reported):
                raise ValueError("OpenMM reported a nonfinite repair energy")
            if reported < self.lowest_energy:
                # The solver gradient zeros fixed particles. Only the physical
                # state supplies their true forces at the reported coordinates.
                state = self.context.getState(getPositions=True, getEnergy=True, getForces=True)
                coordinates = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
                if not np.array_equal(coordinates.ravel(), x):
                    raise ValueError("OpenMM repair callback and observed coordinates differ")
                energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
                forces = state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole / unit.nanometer)
                self.retain_if_lower("openmm-iteration", coordinates, energy, forces)
            return False

        def finish(self, coordinates, energy, forces):
            self.ordinal += 1
            self.retain_if_lower("openmm-final", coordinates, energy, forces)

        def close(self):
            self.context = None

    return Reporter(context)
