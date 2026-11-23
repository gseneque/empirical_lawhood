# SPDX-License-Identifier: MPL-2.0
"""Scientific declaration and causal lifecycle of the matrix memory and composed pulse response investigation."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.methods.path_likelihood.protocol import extension
from empirical_lawhood.methods.path_likelihood.records import PathSpecification


@dataclass(frozen=True, slots=True)
class Specification(PathSpecification):
    FAMILY: ClassVar[str] = "matrix-projected-memory"
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-projected-memory/specification"
    TITLE: ClassVar[str] = "Matrix memory and composed pulse response"
    QUESTION: ClassVar[str] = (
        "Which available history or kernel delivers the signed and joint future of a blind two-pulse continuation?"
    )
    POPULATION: ClassVar[str] = (
        "Independent q=2 driven matrix preparation with two laboratory ports and matched single and composed pulse futures."
    )
    ISSUED_FORECAST: ClassVar[bool] = True

    @staticmethod
    def diagnose(options, model, batches):
        from .diagnostics import memory_diagnostics

        return memory_diagnostics(
            options, model, batches("develop"), batches("evaluate")
        )

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
    "programmes/foundations/emergent-structure/workflows/matrix-projected-memory/guide.md",
    82,
)
