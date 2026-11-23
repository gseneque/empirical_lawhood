# SPDX-License-Identifier: MPL-2.0
from decimal import Decimal
from empirical_lawhood.domains.matrix.path_thermodynamics.pulse_design import (
    positive,
    validate_pulse,
)


def validate(options):
    validate_pulse(
        options,
        (
            "level_margin",
            "joint_margin",
            "coverage_floor",
            "predictive_draws",
            "lags",
            "kernel_lengths",
        ),
    )
    if (
        options["splits"]["select"] < 2
        or type(options["predictive_draws"]) is not int
        or options["predictive_draws"] < 2
        or options["lags"] != [0, 1, 4, 8, 16]
        or options["kernel_lengths"] != [1, 4, 8, 16, 128]
        or not all(
            positive(options[k])
            for k in ("level_margin", "joint_margin", "coverage_floor")
        )
        or Decimal(options["coverage_floor"]) > 1
    ):
        raise ValueError(
            "invalid measured history, kernel menu, calibration or trajectory tolerances"
        )
