# SPDX-License-Identifier: MPL-2.0
"""Scientific declaration and causal lifecycle of the matrix orientation and signed laboratory response investigation."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.methods.path_likelihood.protocol import extension
from empirical_lawhood.methods.path_likelihood.records import PathSpecification


@dataclass(frozen=True, slots=True)
class Specification(PathSpecification):
    FAMILY: ClassVar[str] = "matrix-orientation-response"
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/matrix-orientation-response/specification"
    )
    TITLE: ClassVar[str] = "Matrix orientation and signed laboratory response"
    QUESTION: ClassVar[str] = (
        "Does one global lift distinguish materially different signed pulse responses, and can an advance forecast use that bit?"
    )
    POPULATION: ClassVar[str] = (
        "Independent q=2 path family with two global lifts, paired pulse signs, four future innovations and two numerical clocks."
    )
    ISSUED_FORECAST: ClassVar[bool] = True

    @staticmethod
    def validate_parameters(options):
        from .design import validate

        validate(options)


def acquire(*args):
    from empirical_lawhood.methods.path_likelihood.forecast import batch
    from . import experiment

    return batch(*args, source=experiment)


def evaluate(*args):
    from empirical_lawhood.methods.path_likelihood.forecast import reduce
    from . import experiment

    return reduce(*args, source=experiment)


EXTENSION = extension(
    Specification,
    acquire,
    evaluate,
    "programmes/foundations/emergent-structure/workflows/matrix-orientation-response/guide.md",
    81,
)
