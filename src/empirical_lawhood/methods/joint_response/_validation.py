# SPDX-License-Identifier: MPL-2.0
"""Shared finite-array validation for pure numerical response methods."""
from __future__ import annotations

import math
import numpy as np


def scalar(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, (bool, np.bool_)) or np.iscomplexobj(value):
        raise ValueError(f'{name} must be a finite real scalar')
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0) or (nonnegative and result < 0):
        raise ValueError(f'{name} is outside its finite real domain')
    return result


def integer(value, name, *, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def array(value, name, *, ndim=2, real=False):
    original = np.asarray(value)
    if original.ndim != ndim or original.dtype.kind not in 'iufc' or not original.size:
        raise ValueError(f'{name} must be a nonempty {ndim}-dimensional numerical array')
    if real and np.iscomplexobj(original):
        raise ValueError(f'{name} must be real')
    dtype = np.float64 if real or not np.iscomplexobj(original) else np.complex128
    result = np.asarray(original, dtype=dtype)
    if not np.isfinite(result).all():
        raise ValueError(f'{name} must be finite')
    return result


def hermitian(value, name):
    result = array(value, name)
    if result.shape[0] != result.shape[1]:
        raise ValueError(f'{name} must be square')
    tolerance = 256*np.finfo(float).eps*max(norm(result), np.finfo(float).tiny)
    if norm(result-result.conj().T) > tolerance:
        raise ValueError(f'{name} must be Hermitian')
    return (result+result.conj().T)/2


def spectral_point(z, *, upper=False):
    if isinstance(z, (bool, np.bool_)):
        raise ValueError('spectral point must have a finite nonzero imaginary part')
    z = complex(z)
    if not np.isfinite(z) or z.imag == 0 or (upper and z.imag <= 0):
        raise ValueError('spectral point must have a finite nonzero imaginary part in the requested half-plane')
    return z


def norm(value):
    return float(np.linalg.norm(value, 2))


def immutable(value):
    result = np.ascontiguousarray(value)
    return np.frombuffer(result.tobytes(), dtype=result.dtype).reshape(result.shape)


def square_map(value, name):
    result = array(value, name)
    if result.shape[0] != result.shape[1]:
        raise ValueError(f'{name} must be square')
    return result
