# SPDX-License-Identifier: MPL-2.0
from decimal import Decimal
from empirical_lawhood.methods.path_likelihood.forecast import validate_splits


def validate(options):
    if set(options) != {
        "splits",
        "sites",
        "particles",
        "j_xy",
        "j_z",
        "gamma",
        "nodes",
        "margin",
        "derivative_margin",
        "epsilon",
        "pooling",
        "shooting_tapes",
    }:
        raise ValueError("marked reference requires its complete physical choices")
    validate_splits(options)
    if (options["sites"], options["particles"]) != (4, 2) or options["splits"][
        "select"
    ]:
        raise ValueError("this reference uses the four-site, two-particle sector")
    if any(
        type(options[k]) is not int or not 1 <= options[k] <= 64
        for k in ("nodes", "shooting_tapes")
    ):
        raise ValueError("invalid marked clock grid or shooting allocation")
    values = [
        options[k] for k in ("j_xy", "j_z", "gamma", "margin", "derivative_margin")
    ] + options["epsilon"]
    if (
        not options["epsilon"]
        or not options["pooling"]
        or any(
            not isinstance(v, str) or not Decimal(v).is_finite() or Decimal(v) <= 0
            for v in values
        )
    ):
        raise ValueError(
            "interaction, clock and tolerance scales must be finite positive Decimals"
        )
    if any(
        not isinstance(v, str) or not Decimal(v).is_finite() or Decimal(v) < 0
        for v in options["pooling"]
    ):
        raise ValueError("pooling must be finite and nonnegative")
