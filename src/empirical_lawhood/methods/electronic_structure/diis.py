# SPDX-License-Identifier: Apache-2.0
# Extrapolation formulas derive from PySCF 2.14.0 lib/diis.py (Apache-2.0).
"""Checked DIIS weights on a supplied finite Hermitian augmented error matrix.

This numerical procedure has no mean-field object, disk vectors, native SCF
cycle or retry behavior. The caller chooses when its original eigensolver
failure permits this calculation. The dependence threshold remains 1e-14.
"""
import numpy as np
import scipy.linalg


def checked_diis_weights(matrix):
    if (matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 1
            or matrix.dtype.kind not in 'fc' or not np.isfinite(matrix).all()
            or not np.array_equal(matrix, matrix.T.conj())):
        raise ValueError('DIIS eigensolver recovery requires the original finite Hermitian matrix')
    number = matrix.shape[0] - 1
    eigenvalues, eigenvectors = scipy.linalg.eigh(matrix, driver='ev')
    residual = float(np.linalg.norm(matrix@eigenvectors-eigenvectors*eigenvalues, ord=np.inf))
    orthogonality = float(np.linalg.norm(eigenvectors.T.conj()@eigenvectors-np.eye(number+1), ord=np.inf))
    tolerance = 64*np.finfo(matrix.real.dtype).eps*(number+1)
    scale = max(1., float(np.linalg.norm(matrix, ord=np.inf)))
    if (not np.isfinite(eigenvalues).all() or not np.isfinite(eigenvectors).all()
            or residual > tolerance*scale or orthogonality > tolerance):
        raise ValueError('DIIS symmetric-QR eigenpairs fail their residual or orthogonality check')
    rhs = np.zeros(number+1, matrix.dtype)
    rhs[0] = 1
    if np.any(abs(eigenvalues) < 1e-14):
        selected = abs(eigenvalues) > 1e-14
        weights = np.dot(eigenvectors[:, selected]*(1./eigenvalues[selected]),
            np.dot(eigenvectors[:, selected].T.conj(), rhs))
    else:
        weights = np.linalg.solve(matrix, rhs)
    return weights, dict(eigenpair_residual=residual, orthogonality_residual=orthogonality,
                        eigenpair_residual_limit=tolerance*scale, orthogonality_limit=tolerance,
                        original_dependence_threshold=1e-14)


def accumulate_diis_block(output, vector, weight):
    """Apply one supplied vector block; the caller owns storage and block order."""
    output += vector * weight
