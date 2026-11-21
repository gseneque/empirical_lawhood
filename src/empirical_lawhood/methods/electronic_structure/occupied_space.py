# SPDX-License-Identifier: MPL-2.0
"""Spin-resolved occupied-space continuity on supplied atomic-orbital overlaps."""

import numpy as np
from scipy.linalg import eigh, svdvals


def hermitian_matrix(value, quantity):
    """Require a nonempty finite Hermitian matrix in the selected basis."""
    metric = np.asarray(value)
    if (
        metric.ndim != 2
        or metric.shape[0] != metric.shape[1]
        or metric.shape[0] == 0
        or metric.dtype.kind not in "ifcu"
        or not np.isfinite(metric).all()
        or not np.allclose(metric, metric.T.conj(), atol=1e-10, rtol=0)
    ):
        raise ValueError(f"select a finite Hermitian {quantity}")
    return metric


def occupied_density_factors(density, overlap, counts):
    """Factor each determinant density into orbitals orthonormal under its original AO metric."""
    metric = hermitian_matrix(overlap, "atomic-orbital overlap")
    matrices = np.asarray(density)
    n = len(metric)
    counts = tuple(counts)
    if (
        matrices.shape != (2, n, n)
        or matrices.dtype.kind not in "ifcu"
        or not np.isfinite(matrices).all()
        or len(counts) != 2
        or any(
            isinstance(k, (bool, np.bool_))
            or not isinstance(k, (int, np.integer))
            or not 0 <= k <= n
            for k in counts
        )
    ):
        raise ValueError(
            "select two full density matrices and their original electron counts"
        )
    factors = []
    for matrix, count in zip(matrices, counts, strict=True):
        if not np.allclose(matrix, matrix.T.conj(), atol=1e-10, rtol=0):
            raise ValueError("the determinant density is not Hermitian")
        # Restrict the eigensolve to the occupied rank. Empty spin sectors have a valid zero-column factor.
        factor = np.empty((n, 0), dtype=matrix.dtype)
        if count:
            values, vectors = eigh(matrix, subset_by_index=(n - int(count), n - 1))
            if values[0] <= 0:
                raise ValueError(
                    "the declared occupied density factor has a nonpositive eigenvalue"
                )
            factor = vectors * np.sqrt(values)
            if not np.allclose(
                factor.T.conj() @ metric @ factor, np.eye(count), rtol=0, atol=1e-6
            ):
                raise ValueError(
                    "the occupied factor fails normalization under the original AO overlap"
                )
        if not np.allclose(factor @ factor.T.conj(), matrix, rtol=1e-7, atol=1e-8):
            raise ValueError(
                "the declared occupied rank does not reconstruct the original determinant"
            )
        factors.append(factor)
    return tuple(factors)


def opposite_spin_frontier_densities(triplet_alpha_coefficients, overlap, singlet_occupied_count):
    """Seed opposite real frontier combinations over the same doubly occupied core.

    Columns must be in donor orbital order and normalized in the selected
    AO metric. The singlet occupation per spin locates the two frontier columns.
    The two returned AO densities are starting guesses for a separate evaluation.
    """
    metric = hermitian_matrix(overlap, "atomic-orbital overlap")
    coefficients = np.asarray(triplet_alpha_coefficients)
    count = singlet_occupied_count
    if (coefficients.ndim != 2 or coefficients.shape[0] != len(metric)
            or coefficients.dtype.kind not in "ifu" or metric.dtype.kind not in "ifu"
            or isinstance(count, (bool, np.bool_)) or not isinstance(count, (int, np.integer))
            or not 0 < count < coefficients.shape[1]):
        raise ValueError("select real donor orbitals, the original overlap and both frontier columns")
    selected = coefficients[:, :count + 1].astype(float, copy=False)
    if (not np.isfinite(selected).all() or not np.allclose(
            selected.T @ metric @ selected, np.eye(count + 1), rtol=0, atol=1e-6)):
        raise ValueError("the selected donor orbitals must be normalized under the original AO overlap")
    core = selected[:, :count - 1] @ selected[:, :count - 1].T
    a, b = selected[:, count - 1], selected[:, count]
    mixed = ((a + b) / np.sqrt(2.0), (a - b) / np.sqrt(2.0))
    return np.stack([core + np.outer(v, v) for v in mixed])


def compare_occupied_spaces(left, right, cross_overlap, *, allow_spin_swap):
    """Compare the two geometries' orbitals using their cross-geometry AO overlap."""
    if type(allow_spin_swap) is not bool:
        raise TypeError(
            "select whether a global spin-label exchange is physically admissible"
        )
    if left is None or right is None:
        return {"disposition": "missing converged determinant"}
    cross = np.asarray(cross_overlap)
    if (
        cross.ndim != 2
        or cross.dtype.kind not in "ifcu"
        or not cross.size
        or not np.isfinite(cross).all()
    ):
        raise ValueError(
            "select the finite atomic-orbital overlap between the two actual geometries"
        )
    sides = []
    for spin_pair, n in zip((left, right), cross.shape, strict=True):
        blocks = tuple(np.asarray(s) for s in spin_pair)
        if len(blocks) != 2 or any(
            s.ndim != 2
            or s.shape[0] != n
            or s.shape[1] > n
            or s.dtype.kind not in "ifcu"
            or not np.isfinite(s).all()
            for s in blocks
        ):
            raise ValueError(
                "each geometry needs two complete spin-resolved occupied factors"
            )
        sides.append(blocks)
    left, right = sides
    counts = tuple(s.shape[1] for s in left)
    if counts != tuple(s.shape[1] for s in right) or (
        allow_spin_swap and counts[0] != counts[1]
    ):
        raise ValueError("the spin pairing changes occupied electron counts")
    choices = []
    for swap in (False, True) if allow_spin_swap else (False,):
        spectra = []
        for i, a in enumerate(left):
            b = right[1 - i if swap else i]
            squared = svdvals(a.T.conj() @ cross @ b) ** 2
            if squared.size and squared[0] > 1 + 1e-6:
                raise ValueError("cross-geometry occupied overlap exceeds unity")
            spectra.append(np.clip(squared, 0, 1))
        choices.append((sum(float((1 - s).sum()) for s in spectra), swap, spectra))
    loss, swap, spectra = min(choices, key=lambda item: item[0])
    return dict(
        projection_loss_e=loss,
        spin_swap=swap,
        losses_in_direct_then_swapped_order_e=[row[0] for row in choices],
        smallest_squared_overlap=min(
            (float(s[-1]) for s in spectra if s.size), default=None
        ),
        squared_singular_values=[s.tolist() for s in spectra],
    )
