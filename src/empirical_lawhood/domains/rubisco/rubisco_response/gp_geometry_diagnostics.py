# SPDX-License-Identifier: MPL-2.0
"""Pure supplied-array diagnostics for the declared constructed-geometry repair.

The original potential, construction barrier and fixed-coordinate denominator
remain distinct. These values supply diagnostics, never molecular admission.
"""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def mobile_force_diagnostics(
    *, forces: NDArray[np.float64], moving: tuple[int, ...],
    barrier_gradient: NDArray[np.float64], energy: float, barrier_energy: float,
) -> dict[str, float]:
    selected = forces[list(moving)]
    return {
        "maximum_mobile_gradient_kj_mol_nm": float(np.max(np.abs(selected))),
        "mobile_gradient_rms_kj_mol_nm": float(np.sqrt(np.mean(selected**2))),
        "augmented_energy_kj_mol": float(energy) + barrier_energy,
        "maximum_augmented_mobile_gradient_kj_mol_nm": float(
            np.max(np.abs(-selected + barrier_gradient[list(moving)]))
        ),
    }


def optimizer_force_diagnostics(
    *, gradient: NDArray[np.float64], barrier_gradient: NDArray[np.float64],
    moving: tuple[int, ...], optimizer_gradient: NDArray[np.float64],
    initial_coordinates: NDArray[np.float64], final_coordinates: NDArray[np.float64],
) -> dict[str, float | bool]:
    moving_set = set(moving)
    fixed = [i for i in range(len(final_coordinates)) if i not in moving_set]
    return {
        "maximum_final_construction_barrier_gradient_kj_mol_nm": float(np.max(np.abs(barrier_gradient))),
        "maximum_final_augmented_mobile_gradient_kj_mol_nm": float(np.max(np.abs(optimizer_gradient))),
        "maximum_final_original_vs_optimizer_gradient_error_kj_mol_nm": float(np.max(np.abs(
            gradient + barrier_gradient[list(moving)].reshape(-1) - optimizer_gradient
        ))),
        "maximum_mobile_gradient_kj_mol_nm": float(np.max(np.abs(gradient))),
        "mobile_gradient_rms_kj_mol_nm": float(np.sqrt(np.mean(gradient**2))),
        "fixed_coordinates_bitwise_unchanged": bool(np.array_equal(
            final_coordinates[fixed], initial_coordinates[fixed]
        )),
    }
