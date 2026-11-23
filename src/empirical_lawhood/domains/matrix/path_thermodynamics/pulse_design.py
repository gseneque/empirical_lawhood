# SPDX-License-Identifier: MPL-2.0
"""Validate the two-clock source, physical pulse budget and independent allocations."""

from decimal import Decimal

from empirical_lawhood.methods.path_likelihood.forecast import validate_splits

FIELDS = {
    "splits",
    "burn_cycles",
    "cycle_ticks",
    "rise_ticks",
    "timestep",
    "alpha_x",
    "alpha_y",
    "jitter",
    "amplitude",
    "tapes",
    "oracle_tapes",
    "margin",
    "ridge",
}


def positive(value):
    return isinstance(value, str) and Decimal(value).is_finite() and Decimal(value) > 0


def validate_pulse(options, extra=()):
    if set(options) != FIELDS | set(extra):
        raise ValueError("matrix pulse design requires its complete registered choices")
    validate_splits(options)
    if any(
        type(options[k]) is not int
        for k in ("burn_cycles", "cycle_ticks", "rise_ticks", "tapes", "oracle_tapes")
    ):
        raise ValueError("matrix clocks and counts must be integers")
    if not (
        1 <= options["burn_cycles"] <= 64
        and 128 <= options["cycle_ticks"] <= 4096
        and 0 < options["rise_ticks"] < options["cycle_ticks"]
        and options["tapes"] >= 4
        and options["tapes"] % 2 == 0
        and options["oracle_tapes"] >= 2
    ):
        raise ValueError("unresolved matrix pulse clock or independent shooting panel")
    if not all(
        positive(options[k])
        for k in ("timestep", "alpha_x", "alpha_y", "jitter", "amplitude", "margin")
    ):
        raise ValueError(
            "matrix scientific scales require positive finite Decimal strings"
        )
    if not options["ridge"] or not all(positive(v) for v in options["ridge"]):
        raise ValueError("declare a positive ridge grid")
