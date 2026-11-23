# SPDX-License-Identifier: MPL-2.0
"""Scientific declaration and causal lifecycle of the marked event consequences and compressed history investigation."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.methods.path_likelihood.protocol import extension
from empirical_lawhood.methods.path_likelihood.records import PathSpecification


@dataclass(frozen=True, slots=True)
class Specification(PathSpecification):
    FAMILY: ClassVar[str] = "marked-event-response"
    SCHEMA: ClassVar[str] = "empirical-lawhood/marked-event-response/specification"
    TITLE: ClassVar[str] = "Marked event consequences and compressed history"
    QUESTION: ClassVar[str] = (
        "How much early event-consequence information survives compressed histories for the late site count?"
    )
    POPULATION: ClassVar[str] = (
        "Independent four-site monitored-chain history with all active site marks at fixed early clock nodes."
    )
    ISSUED_FORECAST: ClassVar[bool] = True

    @staticmethod
    def diagnose(options, model, batches):
        from .diagnostics import marked_diagnostics

        return marked_diagnostics(options, batches("prefix"))

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
    "programmes/foundations/measurement-and-response/workflows/marked-event-response/guide.md",
    83,
)
