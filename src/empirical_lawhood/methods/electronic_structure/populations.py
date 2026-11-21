# SPDX-License-Identifier: MPL-2.0
"""Mulliken charge and spin populations of an explicitly selected atom group."""

import numpy as np


def spin_density_populations(
    density, overlap, ao_atom_indices, nuclear_charges, selected_atoms
):
    """Partition a full, real collinear density on the supplied atomic-orbital metric."""
    matrix, metric = np.asarray(density), np.asarray(overlap)
    atom_ids, charges, selected = map(
        np.asarray, (ao_atom_indices, nuclear_charges, selected_atoms)
    )
    if (
        metric.ndim != 2
        or not metric.size
        or metric.shape[0] != metric.shape[1]
        or metric.dtype.kind not in "iuf"
        or not np.isfinite(metric).all()
        or not np.allclose(metric, metric.T, rtol=0, atol=1e-10)
    ):
        raise ValueError("select a finite real symmetric atomic-orbital metric")
    if (
        matrix.shape not in (metric.shape, (2, *metric.shape))
        or matrix.dtype.kind not in "iuf"
        or not np.isfinite(matrix).all()
        or not np.allclose(matrix, matrix.swapaxes(-1, -2), rtol=0, atol=1e-10)
    ):
        raise ValueError("select the full real closed-shell or spin-resolved density")
    if (
        charges.ndim != 1
        or not charges.size
        or charges.dtype.kind not in "iuf"
        or not np.isfinite(charges).all()
        or np.any(charges < 0)
        or atom_ids.shape != (len(metric),)
        or atom_ids.dtype.kind not in "iu"
        or set(atom_ids) != set(range(len(charges)))
        or selected.ndim != 1
        or not selected.size
        or selected.dtype.kind not in "iu"
        or len(set(selected)) != len(selected)
        or np.any(selected < 0)
        or np.any(selected >= len(charges))
    ):
        raise ValueError(
            "select a complete AO-to-atom census, nuclear charges and distinct original atom indices"
        )
    rows = np.einsum("...ij,ji->...i", matrix, metric)
    if matrix.ndim == 2:
        total, spin = rows, np.zeros_like(rows)
    else:
        total, spin = rows[0] + rows[1], rows[0] - rows[1]
    populations = np.bincount(atom_ids, weights=total, minlength=len(charges))
    spins = np.bincount(atom_ids, weights=spin, minlength=len(charges))
    return dict(
        atom_populations_e=populations.tolist(),
        atom_spin_e=spins.tolist(),
        total_charge_e=float(charges.sum() - populations.sum()),
        selected_charge_e=float(charges[selected].sum() - populations[selected].sum()),
        selected_spin_e=float(spins[selected].sum()),
    )
