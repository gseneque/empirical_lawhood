"""Scientific authored inputs, independent of retained-file and native access."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.domains.matrix.causal_response.authoring.authoring import CausalResponseAuthoringBundle, CausalResponseCandidateContextProvider
from empirical_lawhood.domains.matrix.causal_response.authoring.exposure import CausalResponseExposureInspection
from empirical_lawhood.domains.matrix.information_response.authoring.authoring import InformationResponseAuthoringBundle, InformationResponseCandidateContextProvider
from empirical_lawhood.domains.matrix.information_response.authoring.exposure import InformationResponseExposureInspection
from empirical_lawhood.domains.matrix.prepared_response.authoring.exposure import PreparedExposureInspection
from empirical_lawhood.domains.matrix.prepared_response.authoring.qualification_design import PreparedResponseSourceQualificationAuthoringBundle, PreparedResponseSourceQualificationCandidateContextProvider
from empirical_lawhood.domains.matrix.prepared_response.contracts import PreparedRootRandomness, validate_prepared_seed_census
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class PreparedResponseNativeAuthoringInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/prepared-response/prepared-response-native-authoring-input'
    config_id: str
    route: str
    target_prefix: str
    seed_label: str
    source_seed_sha256: str
    evidence_role: str = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
    root_seed_census: tuple[PreparedRootRandomness, ...] = ()

    def __post_init__(self) -> None:
        family = {"source-qualification": "prepared-response", "information-prediction": "information-response", "causal-response-prediction": "causal-response"}.get(self.route, "invalid")
        for name in ("config_id", "target_prefix", "seed_label"):
            validate_stable_id(getattr(self, name), field_name=name)
        if (
            self.route not in ROUTES
            or not self.config_id.startswith(f"empirical-lawhood-{family}-")
            or not self.target_prefix.startswith(f"empirical-lawhood.{family}.")
            or not self.seed_label.startswith(f"empirical-lawhood-{family}-")
            or self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
        ):
            raise ValueError(
                "prepared response authoring input requires a target development identity"
            )
        object.__setattr__(self, "root_seed_census", validate_prepared_seed_census(
            "qualification" if self.route == "source-qualification" else "prospective-evaluation",
            self.source_seed_sha256, self.root_seed_census,
        ))


@dataclass(frozen=True, slots=True)
class PreparedNativeAuthoring:
    """Scientific preparation handed to the application compiler without authority."""

    bundle: PreparedResponseSourceQualificationAuthoringBundle | InformationResponseAuthoringBundle | CausalResponseAuthoringBundle
    exposure: (
        PreparedExposureInspection | InformationResponseExposureInspection | CausalResponseExposureInspection
    )
    context_provider_type: (
        type[PreparedResponseSourceQualificationCandidateContextProvider]
        | type[InformationResponseCandidateContextProvider]
        | type[CausalResponseCandidateContextProvider]
    )
    selection_summary: dict[str, object]


ROUTES = ("source-qualification", "information-prediction", "causal-response-prediction")
