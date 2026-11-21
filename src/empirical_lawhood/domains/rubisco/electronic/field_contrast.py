# SPDX-License-Identifier: MPL-2.0
"""Signed carbon and oxygen field contrasts on the same fixed host and hydration."""

from math import fsum, isfinite

HARTREE_KCAL_MOL = 627.5094740631
STATE_SIGNS = {"C-TS": 1, "C-P": -1, "O-II": -1, "O-I": 1}


def four_state_field_contrast(states):
    """Form (C-TS − C-P) − (O-II − O-I) with signed interval propagation."""
    if set(states) != set(STATE_SIGNS):
        raise ValueError("select the complete four-state field contrast")
    lo, hi, frozen = [], [], []
    for state, sign in STATE_SIGNS.items():
        row = states[state]
        a, b = row["variational_interval_Eh"]
        if not isfinite(a) or not isfinite(b) or a > b:
            raise ValueError("select ordered finite field endpoints")
        lo.append(a if sign > 0 else -b)
        hi.append(b if sign > 0 else -a)
        value = row["frozen_density_shift_Eh"]
        if value is not None:
            if not isfinite(value) or not a - 1e-8 <= value <= b + 1e-8:
                raise ValueError(
                    "the selected frozen-density work falls outside the state interval"
                )
            frozen.append(sign * value)
    interval = [fsum(lo) * HARTREE_KCAL_MOL, fsum(hi) * HARTREE_KCAL_MOL]
    return {
        "direction": "incoming field minus native at fixed host",
        "four_state_interval_kcal_mol": interval,
        "width_kcal_mol": interval[1] - interval[0],
        "frozen_four_state_shift_kcal_mol": fsum(frozen) * HARTREE_KCAL_MOL
        if len(frozen) == len(states)
        else None,
    }
