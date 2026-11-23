# SPDX-License-Identifier: MPL-2.0
"""Public definition of thermal rc dissipation and voltage memory."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.methods.path_likelihood.protocol import extension
from empirical_lawhood.methods.path_likelihood.records import PathSpecification


@dataclass(frozen=True, slots=True)
class Specification(PathSpecification):
    FAMILY: ClassVar[str] = "thermal-rc"
    SCHEMA: ClassVar[str] = "empirical-lawhood/thermal-rc/specification"
    TITLE: ClassVar[str] = "Thermal RC dissipation and voltage memory"
    QUESTION: ClassVar[str] = (
        "Which voltages preserve physical time direction and which predict the next voltage?"
    )
    POPULATION: ClassVar[str] = (
        "Independent three-branch thermal voltage triplet with paired observation grids and a separate reverse draw."
    )

    @staticmethod
    def validate_parameters(options):
        if (
            set(options) - {"panel"} != {"hidden_rate"}
            or options.get("panel", "complete") not in ("complete", "correlation")
            or not isinstance(options["hidden_rate"], str)
            or not Decimal(options["hidden_rate"]).is_finite()
            or Decimal(options["hidden_rate"]) <= 1
        ):
            raise ValueError(
                "thermal RC requires a finite distinct hidden rate above the unit branch rate"
            )


def acquire(*args):
    from .physics import acquire as sample

    return sample(*args)


def evaluate(*args):
    from .assessment import evaluate as assess

    return assess(*args)


EXTENSION = extension(
    Specification,
    acquire,
    evaluate,
    "programmes/foundations/measurement-and-response/workflows/thermal-rc/guide.md",
    79,
    additional_definitions=(("correlation-precision.json", "Independent correlation precision panel"),),
)
