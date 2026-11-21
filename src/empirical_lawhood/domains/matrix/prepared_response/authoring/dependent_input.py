"""Scientific authored inputs, independent of retained-file and native access."""
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.domains.matrix.prepared_response.development_selection import PreparedResponseDevelopmentCandidateCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.domains.matrix.prepared_response.authoring.exposure import PreparedExposureInspection


@dataclass(frozen=True, slots=True)
class PreparedResponseDependentInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/prepared-response/prepared-response-dependent-input'
    config_id: str
    route: str
    target_prefix: str
    seed_label: str
    evidence_role: str
    source_seed_sha256: str

    def __post_init__(self) -> None:
        validate_sha256(self.source_seed_sha256, field_name="source_seed_sha256")
        for name in ("config_id", "target_prefix", "seed_label"):
            validate_stable_id(getattr(self, name), field_name=name)
        if (
            self.route not in ("dependent-refinement", "fresh-response-calibration")
            or not self.config_id.startswith(
                f"empirical-lawhood-prepared-response-{self.route}-"
            )
            or not self.target_prefix.startswith(
                f"empirical-lawhood.prepared-response.{self.route}."
            )
            or not self.seed_label.startswith("empirical-lawhood-prepared-response-")
            or self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
        ):
            raise ValueError("PREPARED_RESPONSE_DEPENDENT_INPUT_INVALID: route or development role")


@dataclass(frozen=True, slots=True)
class PreparedResponseDependentAuthoring(CanonicalRecord):
    """Explicit plan/design bytes, inspected native roster and measured refinement costs.

    This is a development specification, not authority or proof of fresh units.
    A genuine candidate still needs independent inspection before any issue.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/prepared-response/prepared-response-dependent-authoring'
    plan_text: str
    design_text: str
    exposure: PreparedExposureInspection
    candidate_costs: tuple[PreparedResponseDevelopmentCandidateCost, ...]

    def __post_init__(self) -> None:
        if any(
            not 0 < len(value.encode()) <= 1024**2
            for value in (self.plan_text, self.design_text)
        ):
            raise ValueError("PREPARED_RESPONSE_DEPENDENT_PLAN_OR_DESIGN_INVALID")
        if (
            self.exposure.source_config.implementation_plan_sha256
            != sha256(self.plan_text.encode()).hexdigest()
            or self.exposure.source_config.stage not in ('development', 'calibration')
            or not self.exposure.units_and_seeds_unexposed
        ):
            raise ValueError("PREPARED_RESPONSE_DEPENDENT_SOURCE_OR_EXPOSURE_INVALID")
        if self.exposure.source_config.stage == 'calibration' and self.candidate_costs:
            raise ValueError("FRESH_RESPONSE_CALIBRATION_CANNOT_RESELECT_DEPENDENT_REFINEMENT_COSTS")

