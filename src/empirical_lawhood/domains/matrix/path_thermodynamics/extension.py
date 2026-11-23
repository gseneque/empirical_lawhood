# SPDX-License-Identifier: MPL-2.0
"""Public definition of six-matrix dissipation and physical reversal."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.methods.path_likelihood.protocol import extension
from empirical_lawhood.methods.path_likelihood.records import PathSpecification


@dataclass(frozen=True, slots=True)
class Specification(PathSpecification):
    FAMILY: ClassVar[str] = "matrix-path-thermodynamics"
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-path-thermodynamics/specification"
    TITLE: ClassVar[str] = "Six-matrix dissipation and physical reversal"
    QUESTION: ClassVar[str] = (
        "Does the recorded underdamped matrix cycle distinguish physical time direction on its declared population?"
    )
    POPULATION: ClassVar[str] = (
        "Independent q=2 six-matrix path family with matched numerical views, transient temperatures and independent reverse initialization."
    )

    @staticmethod
    def validate_parameters(options):
        if options.get("panel", "complete") not in ("complete", "preparation"):
            raise ValueError("unknown matrix path panel")
        if set(options) - {"panel"} != {
            "burn_cycles",
            "cycle_ticks",
            "rise_ticks",
            "timestep",
            "alpha_x",
            "alpha_y",
            "jitter",
            "critic_bound",
        }:
            raise ValueError(
                "matrix thermal design requires its complete schedule, initial law and critic"
            )
        if (
            any(
                type(options[k]) is not int
                for k in ("burn_cycles", "cycle_ticks", "rise_ticks")
            )
            or not 2 <= options["burn_cycles"] <= 64
            or options["cycle_ticks"] < 32
            or not 0 < options["rise_ticks"] < options["cycle_ticks"]
            or options["cycle_ticks"] % 16
        ):
            raise ValueError(
                "matrix cycle needs a resolved asymmetric outward and return ramp"
            )
        for k in ("alpha_x", "alpha_y", "timestep", "jitter", "critic_bound"):
            if (
                not isinstance(options[k], str)
                or not Decimal(options[k]).is_finite()
                or Decimal(options[k]) <= 0
            ):
                raise ValueError(
                    "matrix physical choices require finite positive Decimal strings"
                )
        if Decimal(options["critic_bound"]) > 2:
            raise ValueError("bounded path critic exceeds the instrument range")


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
    "programmes/foundations/emergent-structure/workflows/matrix-path-thermodynamics/guide.md",
    80,
    additional_definitions=(("preparation-precision.json", "Independent preparation precision panel"),),
)
