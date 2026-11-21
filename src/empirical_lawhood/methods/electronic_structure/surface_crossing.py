# SPDX-License-Identifier: MPL-2.0
"""Conditional single-passage transition and classical momentum adjustment."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from numbers import Real
from typing import Generic, TypeVar

import numpy as np
from numpy.typing import ArrayLike, NDArray


_State = TypeVar("_State")


@dataclass(frozen=True, slots=True)
class BracketedEnergyGap(Generic[_State]):
    """The actual accepted probe on the straight segment between two geometries."""

    fraction: float
    gap_hartree: float
    probes: int
    state: _State


def locate_bracketed_energy_gap(
    *, left_gap_hartree: float, right_gap_hartree: float, gap_tolerance_hartree: float,
    maximum_probes: int, probe: Callable[[float], tuple[float, _State]],
) -> BracketedEnergyGap[_State]:
    """Bisect a signed energy gap using the two original endpoint evaluations.

    Each callback evaluates the selected pair at a fraction of the segment
    and returns its gap and associated electronic state. Only a probe whose
    energy residual meets the selected tolerance can supply that state.
    """
    for value in (left_gap_hartree, right_gap_hartree, gap_tolerance_hartree):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError("select finite endpoint gaps and a finite energy tolerance")
    if (left_gap_hartree < 0) == (right_gap_hartree < 0):
        raise ValueError("the endpoint energy gaps must bracket a change in sign")
    if gap_tolerance_hartree <= 0 or type(maximum_probes) is not int or maximum_probes < 1:
        raise ValueError("select a positive gap tolerance and probe limit")
    lower, upper = 0.0, 1.0
    for count in range(1, maximum_probes + 1):
        fraction = (lower + upper) / 2
        if fraction in (lower, upper):
            break
        gap, state = probe(fraction)
        if isinstance(gap, bool) or not isinstance(gap, Real) or not math.isfinite(gap):
            raise ValueError("the evaluated energy gap must be finite")
        if abs(gap) <= gap_tolerance_hartree:
            return BracketedEnergyGap(fraction, float(gap), count, state)
        if (gap < 0) == (left_gap_hartree < 0):
            lower = fraction
        else:
            upper = fraction
    raise ValueError("the crossing was not located within the selected energy tolerance")


def landau_zener_probability(
    adiabaticity: float, *, donor_components: int = 1
) -> float:
    """Average one bright channel over equally populated, degenerate donor components.

    Adiabaticity is donor-averaged squared coupling divided by hbar times
    absolute gap speed, in consistent units. Positive infinity gives the
    saturated limit. The single-component expression also applies to a
    specified two-level channel.
    """
    if (
        type(donor_components) is not int
        or donor_components < 1
        or isinstance(adiabaticity, bool)
        or not isinstance(adiabaticity, Real)
        or math.isnan(adiabaticity)
        or adiabaticity < 0
    ):
        raise ValueError(
            "select nonnegative adiabaticity and a positive donor multiplicity"
        )
    return (
        -math.expm1(-2 * math.pi * adiabaticity * donor_components) / donor_components
    )


def rescale_crossing_velocity(
    *,
    velocity_nm_ps: ArrayLike,
    masses_dalton: ArrayLike,
    gap_gradient: ArrayLike,
    energy_change_kj_mol: float,
) -> tuple[NDArray[np.float64], bool]:
    """Exchange kinetic and potential energy along the mass-weighted Cartesian gap gradient.

    The forward energy change is the destination potential minus the incoming
    potential. The gradient supplies the direction only and may use any single
    consistent unit. A frustrated hop returns a copy of the incoming velocity.
    """
    velocity, masses, gradient = map(
        np.asarray, (velocity_nm_ps, masses_dalton, gap_gradient)
    )
    if any(a.dtype.kind not in "iuf" for a in (velocity, masses, gradient)):
        raise ValueError("select real numerical velocities, masses and gap gradients")
    with np.errstate(over="ignore", invalid="ignore"):
        velocity = np.array(velocity, dtype=np.float64, copy=True)
        masses = np.asarray(masses, dtype=np.float64)
        gradient = np.asarray(gradient, dtype=np.float64)
    if (
        velocity.ndim != 2
        or velocity.shape[1] != 3
        or not len(velocity)
        or gradient.shape != velocity.shape
        or masses.shape != (len(velocity),)
        or any(not np.isfinite(a).all() for a in (velocity, masses, gradient))
        or np.any(masses <= 0)
        or isinstance(energy_change_kj_mol, bool)
        or not isinstance(energy_change_kj_mol, Real)
        or not math.isfinite(energy_change_kj_mol)
    ):
        raise ValueError(
            "select all finite Cartesian velocities and gap gradients, positive masses and a finite energy change"
        )
    energy_change_kj_mol = float(energy_change_kj_mol)
    magnitude = float(np.max(np.abs(gradient)))
    if magnitude == 0:
        return velocity, False
    # Scaling the direction does not change the adjusted velocity. Rationalize
    # the small root of the kinetic-energy quadratic to avoid cancellation.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        direction = gradient / magnitude
        mass_weighted = direction / masses[:, None]
        a = float(np.sum(direction * mass_weighted))
        b = float(np.sum(velocity * direction))
        discriminant = b * b - 2 * a * energy_change_kj_mol
        if not math.isfinite(discriminant) or not (0 < a < math.inf):
            raise ValueError(
                "the selected crossing impulse is outside finite numerical support"
            )
        if discriminant < 0:
            return velocity, False
        if energy_change_kj_mol == 0:
            return velocity, True
        denominator = 0.5 * b + 0.5 * math.copysign(math.sqrt(discriminant), b)
        if denominator == 0 or not math.isfinite(denominator):
            raise ValueError(
                "the selected crossing impulse is outside finite numerical support"
            )
        velocity -= (energy_change_kj_mol / denominator) * mass_weighted
    if not np.isfinite(velocity).all():
        raise ValueError("crossing produced an unrepresentable velocity")
    return velocity, True
