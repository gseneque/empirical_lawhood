"""Exact typed scientific authoring selection for an electron-gas analytic inquiry."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id

@dataclass(frozen=True, slots=True)
class UniformElectronGasAnalyticAuthoringProfile(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/analytic-authoring-profile'

    profile_id: str
    experiment_id: str
    config_sha256: str

    def __post_init__(self) -> None:
        validate_stable_id(self.profile_id, field_name="profile_id")
        validate_stable_id(self.experiment_id, field_name="experiment_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
