"""Bounded precontact first-word screen and actual induced-seal transport."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import DEVELOPMENT_ROOTS
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.discovery import ClassicalBound
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import ClassicalInducedPrediction
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.nomination import first_opportunity


@dataclass(frozen=True, slots=True)
class ClassicalFirstScreen(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-staged-pulse-response/classical-first-screen'
    historical_parent: ObjectIdentity
    bound: ClassicalBound
    retained_preparations: tuple[ObjectIdentity, ...]
    retained_measurements: tuple[ObjectIdentity, ...]

    def __post_init__(self) -> None:
        if (
            len(self.retained_preparations) != len(DEVELOPMENT_ROOTS)
            or len(self.retained_measurements) != len(DEVELOPMENT_ROOTS)
            or self.bound.coordinate.kind != "first"
        ):
            raise ValueError("first screen changes the retained unconditional relation census")

    @property
    def entered(self) -> bool:
        return first_opportunity(self.bound)

    @property
    def record_id(self) -> str:
        return "reactor-staged-pulse-response.first-screen"


@dataclass(frozen=True, slots=True)
class ClassicalInducedBundle(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-staged-pulse-response/classical-induced-bundle'
    root: str
    seals: tuple[ClassicalInducedPrediction, ...]

    def __post_init__(self) -> None:
        if len(self.seals) > 1 or any(s.context.root != self.root for s in self.seals):
            raise ValueError("induced bundle changes its exact actual callback census")

    @property
    def record_id(self) -> str:
        return f"{self.root}.induced-bundle"
