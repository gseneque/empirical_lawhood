"""Scientific authored inputs, independent of retained-file and native access."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class FiniteResponseLawCalibrationInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/finite-response-law/finite-response-law-calibration-input'
    config_id: str
    stage: str = "calibration"
    evidence_role: str = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if (
            not self.config_id.startswith("empirical-lawhood-finite-response-law-calibration-")
            or self.stage != "calibration"
            or self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
        ):
            raise ValueError(
                "finite response-law calibration input changes its target development role"
            )

