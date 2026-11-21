"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Mapping
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_relative_locator, validate_sha256
from empirical_lawhood.domains.quantum.marked_record_identification.contracts import Verdict


_RESPONSE_CONTROL_PATHS = (
    "controls/freeze.json",
    "stages/source-compatibility/result.json",
    "stages/instrument-conformance/result.json",
    "stages/observation-order-evaluation/result.json",
    "stages/observation-order-evaluation/result.json.receipt.json",
    "closeout/result.json",
    "closeout/result.json.receipt.json",
    "controls/implementation-manifest.json",
)


_PREPARATION_QUALIFICATION_PATHS = ("closeout/result.json", "closeout/result.json.receipt.json")


@dataclass(frozen=True, slots=True)
class PredecessorInputs(CanonicalRecord):
    """Caller-frozen predecessor bytes, never a shipped historical authority."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/quantum-marked-record-identification/predecessor-inputs'
    response_control_root: str
    preparation_qualification_root: str
    payload_sha256s: tuple[tuple[str, str], ...]
    implementation_sha256: str

    def __post_init__(self) -> None:
        validate_relative_locator(self.response_control_root)
        validate_relative_locator(self.preparation_qualification_root)
        validate_sha256(self.implementation_sha256)
        expected = tuple(
            sorted(
                [f"{self.response_control_root}/{p}" for p in _RESPONSE_CONTROL_PATHS]
                + [f"{self.preparation_qualification_root}/{p}" for p in _PREPARATION_QUALIFICATION_PATHS]
            )
        )
        if tuple(path for path, _ in self.payload_sha256s) != expected:
            raise ValueError("predecessor input must bind every payload and receipt")
        for _, digest in self.payload_sha256s:
            validate_sha256(digest)


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    verdict: Verdict
    checked_sha256: Mapping[str, str]
    reason_codes: tuple[str, ...]
    field_classification: Mapping[str, str]
