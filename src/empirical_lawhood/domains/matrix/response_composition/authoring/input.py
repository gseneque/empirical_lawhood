"""Scientific authored inputs, independent of retained-file and native access."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class ResponseCompositionInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/response-composition/response-composition-input'
    config_id: str
    evidence_role: str

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if (
            not self.config_id.startswith("empirical-lawhood-response-composition-")
            or self.evidence_role != "EXPOSED_SOURCE_QUALIFICATION_DEVELOPMENT_NONPROMOTABLE"
        ):
            raise ValueError("RESPONSE_COMPOSITION_INPUT_INVALID: source qualification development role")

