# SPDX-License-Identifier: MPL-2.0
"""Pauli bounds and frozen-density work for a one-body perturbation in a nonorthogonal basis."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.linalg import cholesky, eigh, eigvalsh

from empirical_lawhood.methods.electronic_structure.occupied_space import (
    hermitian_matrix,
)


@dataclass(frozen=True)
class FieldEnergyBounds:
    lowest_orbital_shift: float
    highest_orbital_shift: float
    lower: float
    upper: float
    frozen: float | None


def field_energy_bounds(
    one_body_shift, overlap, nuclear_shift, spin_electrons, *, density=None
):
    """Bound the fixed-geometry energy shift in the supplied units over both spin sectors.

    A single density matrix represents a spin-summed closed shell. Two matrices
    describe the separate spin densities. Fractional natural occupations are allowed.
    """
    h = hermitian_matrix(one_body_shift, "one-body shift")
    s = hermitian_matrix(overlap, "orbital overlap")
    counts = tuple(spin_electrons)
    if (
        h.shape != s.shape
        or len(counts) != 2
        or any(
            isinstance(n, (bool, np.bool_))
            or not isinstance(n, (int, np.integer))
            or not 0 <= n <= len(s)
            for n in counts
        )
    ):
        raise ValueError("select two spin occupations within the shared orbital basis")
    if isinstance(nuclear_shift, (bool, np.bool_)) or not math.isfinite(nuclear_shift):
        raise ValueError("select a finite nuclear field shift")

    eigenvalues = eigh(h, s, eigvals_only=True, driver="gvd")
    lower = float(nuclear_shift + sum(eigenvalues[:n].sum() for n in counts))
    upper = float(nuclear_shift + sum(eigenvalues[len(s) - n :].sum() for n in counts))
    frozen = None
    if density is not None:
        dm = np.asarray(density)
        if dm.shape == s.shape and counts[0] == counts[1]:
            sectors = ((dm / 2, counts[0]),)
        elif dm.shape == (2, *s.shape):
            sectors = zip(dm, counts, strict=True)
        else:
            raise ValueError(
                "supply a closed-shell density or both spin-resolved densities"
            )
        metric_factor = cholesky(s, lower=True)
        for block, electrons in sectors:
            block = hermitian_matrix(block, "spin density")
            occupations = eigvalsh(metric_factor.conj().T @ block @ metric_factor)
            if (
                occupations[0] < -1e-7
                or occupations[-1] > 1 + 1e-7
                or abs(occupations.sum() - electrons) > 1e-6
            ):
                raise ValueError(
                    "spin density violates its Pauli or electron-count constraint"
                )
        work = np.einsum("ij,ji->", h, dm if dm.ndim == 2 else dm.sum(axis=0))
        if abs(work.imag) > 1e-8:
            raise ValueError("Hermitian field work must be real")
        frozen = float(nuclear_shift + work.real)
        if not lower - 1e-8 <= frozen <= upper + 1e-8:
            raise ValueError(
                "frozen-density field work lies outside its spectral bounds"
            )
    return FieldEnergyBounds(
        float(eigenvalues[0]), float(eigenvalues[-1]), lower, upper, frozen
    )
