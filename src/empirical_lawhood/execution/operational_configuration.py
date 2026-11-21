# SPDX-License-Identifier: MPL-2.0
"""Invocation choices outside scientific records and storage identities."""

from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord


class ArtifactVerificationMode(StrEnum):
    REDUCED = "reduced"
    STRICT = "strict"


class ScientificReconstructionMode(StrEnum):
    OFF = "off"
    FULL = "full"


_scientific_reconstruction = ContextVar("scientific_reconstruction", default=ScientificReconstructionMode.OFF)


def scientific_reconstruction_enabled():
    """Retrospective work is independent of evidence and access authentication."""
    return _scientific_reconstruction.get() is ScientificReconstructionMode.FULL


@contextmanager
def scientific_reconstruction_operation(mode=ScientificReconstructionMode.OFF):
    """Select retrospective reconstruction for this invocation, without authority."""
    token = _scientific_reconstruction.set(ScientificReconstructionMode(mode))
    try:
        yield
    finally:
        _scientific_reconstruction.reset(token)


@dataclass(frozen=True, slots=True)
class OperationalConfigurationV1(CanonicalRecord):
    """Select repeated read checks; confer no access or execution authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/operational-configuration"

    artifact_verification: ArtifactVerificationMode = ArtifactVerificationMode.REDUCED

    def __post_init__(self) -> None:
        if type(self.artifact_verification) is not ArtifactVerificationMode:
            raise TypeError("artifact_verification requires reduced or strict")


@dataclass(frozen=True, slots=True)
class OperationalConfigurationV2(OperationalConfigurationV1):
    """Keep retrospective science optional, separately from artifact verification."""

    VERSION: ClassVar[str] = "2.0.0"
    scientific_reconstruction: ScientificReconstructionMode = ScientificReconstructionMode.OFF

    def __post_init__(self) -> None:
        super(OperationalConfigurationV2, self).__post_init__()
        if type(self.scientific_reconstruction) is not ScientificReconstructionMode:
            raise TypeError("scientific_reconstruction requires off or full")


@dataclass(frozen=True, slots=True)
class OperationalConfiguration(OperationalConfigurationV2):
    """Select optional acceleration without changing scientific inputs or authority."""

    VERSION: ClassVar[str] = "3.0.0"
    accelerated_compute: bool = False

    def __post_init__(self) -> None:
        super(OperationalConfiguration, self).__post_init__()
        if type(self.accelerated_compute) is not bool:
            raise TypeError("accelerated_compute requires a boolean")


_accelerated_compute = ContextVar("accelerated_compute", default=False)


def accelerated_compute_enabled() -> bool:
    """Return the requested selection, not a claim about an actual device."""
    return _accelerated_compute.get()


@contextmanager
def accelerated_compute_operation(enabled: bool = False):
    """Scope the operational choice; workers must receive an explicit selection."""
    if type(enabled) is not bool:
        raise TypeError("accelerated_compute requires a boolean")
    token = _accelerated_compute.set(enabled)
    try:
        yield
    finally:
        _accelerated_compute.reset(token)
