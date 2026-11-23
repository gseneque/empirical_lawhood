# SPDX-License-Identifier: MPL-2.0
"""Immutable observations of the original kick/drift/OU/drift/kick map."""

from dataclasses import dataclass, replace

import numpy as np


def immutable(array):
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


@dataclass(frozen=True, slots=True)
class BAOABSubsteps:
    tick: int
    couplings_before: tuple[float, float]
    couplings_after: tuple[float, float]
    q_start: np.ndarray
    p_start: np.ndarray
    q_mid: np.ndarray
    p_minus: np.ndarray
    p_plus: np.ndarray
    q_end: np.ndarray
    p_end: np.ndarray
    gradient_start: np.ndarray
    gradient_end: np.ndarray

    @classmethod
    def capture(cls, start, end, midpoint, minus, plus, first, last):
        return cls(
            start.step_index,
            (start.alpha_tilde_x, start.alpha_tilde_y),
            (end.alpha_tilde_x, end.alpha_tilde_y),
            *(
                immutable(a)
                for a in (
                    start.positions,
                    start.momenta,
                    midpoint,
                    minus,
                    plus,
                    end.positions,
                    end.momenta,
                    first,
                    last,
                )
            ),
        )

    def with_external_force(self, start, end, force):
        return replace(
            self,
            p_start=immutable(start.momenta),
            p_end=immutable(end.momenta),
            gradient_start=immutable(self.gradient_start - force),
            gradient_end=immutable(self.gradient_end - force),
        )
