# SPDX-License-Identifier: MPL-2.0
from empirical_lawhood.domains.matrix.path_thermodynamics.pulse_design import (
    validate_pulse,
)


def validate(options):
    validate_pulse(options)
    if options["splits"]["select"]:
        raise ValueError(
            "the orientation pilot selects its penalty on the declared calibration split"
        )
