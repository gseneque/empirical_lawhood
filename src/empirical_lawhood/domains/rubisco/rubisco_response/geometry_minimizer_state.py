# SPDX-License-Identifier: MPL-2.0
"""Accepted optimizer state, separate from tentative native evaluations.

The molecular owner supplies authenticated objective and array custody. This
in-memory state does not identify a physical source or authorize continuation.
"""

from dataclasses import dataclass
import math

import numpy as np
from empirical_lawhood.methods.binary64_reduction import dot


@dataclass(frozen=True, slots=True)
class GeometryMinimizerState:
    coordinates: np.ndarray
    energy: float
    gradient: np.ndarray
    initial_energy: float
    history: tuple[tuple[np.ndarray, np.ndarray, float], ...]
    phase: str
    iterations: int
    evaluations: int
    invalid_trials: int
    curvature_skips: int
    descent_iterations: int
    maximum_gradient: float
    proposal_filter_contract: str | None

    def __post_init__(self):
        arrays = (self.coordinates, self.gradient)
        if (any(type(a) is not np.ndarray or a.dtype != np.dtype('float64')
                or a.ndim != 1 or not a.size or a.size % 3 or not np.isfinite(a).all() for a in arrays)
                or arrays[0].shape != arrays[1].shape
                or any(type(x) is not float or not math.isfinite(x)
                       for x in (self.energy, self.initial_energy, self.maximum_gradient))
                or self.maximum_gradient <= 0
                or self.phase not in {'initial-scaled-descent', 'domain-lbfgs'}
                or type(self.history) is not tuple or len(self.history) > 20
                or self.proposal_filter_contract not in (None, 'LOCAL_CONSTRUCTION_DOMAIN_V1')):
            raise ValueError('optimizer checkpoint changes its finite variables, algorithm or settings')
        counts = (self.iterations, self.evaluations, self.invalid_trials,
                  self.curvature_skips, self.descent_iterations)
        if (any(type(n) is not int or n < 0 for n in counts)
                or self.evaluations < self.iterations + 1
                or self.descent_iterations + self.curvature_skips > self.iterations
                or len(self.history) > self.iterations - self.descent_iterations
                or self.phase == 'initial-scaled-descent' and self.history):
            raise ValueError('optimizer checkpoint changes accepted-step or evaluation accounting')
        history = []
        for row in self.history:
            if type(row) is not tuple or len(row) != 3:
                raise ValueError('optimizer checkpoint loses its ordered curvature history')
            s, y, rho = row
            if (any(type(a) is not np.ndarray or a.shape != arrays[0].shape
                    or a.dtype != np.dtype('float64') or not np.isfinite(a).all() for a in (s, y))
                    or type(rho) is not float or not math.isfinite(rho) or rho <= 0):
                raise ValueError('optimizer checkpoint has incomplete curvature operands')
            sy = dot(s, y)
            if sy <= 0 or not math.isclose(rho * sy, 1.0, rel_tol=32 * math.ulp(1.0)):
                raise ValueError('optimizer checkpoint substitutes curvature normalization')
            history.append((_frozen_copy(s), _frozen_copy(y), rho))
        object.__setattr__(self, 'coordinates', _frozen_copy(self.coordinates))
        object.__setattr__(self, 'gradient', _frozen_copy(self.gradient))
        object.__setattr__(self, 'history', tuple(history))


def _frozen_copy(array):
    result = np.array(array, dtype='float64', copy=True)
    result.setflags(write=False)
    return result
