# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



from hashlib import sha256

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.domains.matrix.six_matrix_response.reactive_entrance import REACTIVE_ENTRANCE_HDF5_SCHEMA, SixMatrixResponseReactiveEntrancePrecursorResult
from empirical_lawhood.domains.matrix.six_matrix_response.prospective_reactive_source import SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA, SixMatrixResponseProspectiveReactiveSourceLawHistoryResult
from empirical_lawhood.domains.matrix.matrix_response_study.authoring.causal_intersection_residence_design import MatrixResponseCausalIntersectionResidenceStudyConfig

from empirical_lawhood.domains.matrix.matrix_response_study.contracts import MatrixResponseLawMethodConfig, MatrixResponsePairedPanelReducerConfig, MatrixResponseRoleEquivarianceConfig, MatrixResponseStructuralFacePlan
from empirical_lawhood.domains.matrix.matrix_response_study.reactive_entrance_provider import REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY_KEY, REACTIVE_ENTRANCE_METHOD_CAPABILITY_VERSION, REACTIVE_ENTRANCE_PROJECTION_CAPABILITY_KEY
from empirical_lawhood.domains.matrix.matrix_response_study.reactive_entrance_source import MatrixResponseReactiveEntranceAggregate, MatrixResponseReactiveEntranceMethodConfig, MatrixResponseReactiveEntranceProjection
from empirical_lawhood.domains.matrix.matrix_response_study.prospective_reactive_source_provider import PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY_KEY, PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CAPABILITY_VERSION, PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY_KEY
from empirical_lawhood.domains.matrix.matrix_response_study.prospective_reactive_source_law import MatrixResponseProspectiveReactiveSourceLawAggregate, MatrixResponseProspectiveReactiveSourceLawMethodConfig, MatrixResponseProspectiveReactiveSourceLawProjection
from empirical_lawhood.domains.matrix.matrix_response_study.history_conditioned_geometry import HistoryViewTrace
from empirical_lawhood.domains.matrix.matrix_response_study.observation_order import MatrixObservationOrderEvaluationConfig, MatrixObservationOrderEvaluation, MatrixObservationOrderProjectionConfig, MatrixObservationOrderViewReport
from empirical_lawhood.domains.matrix.matrix_response_study.observation_order_provider import OBSERVATION_ORDER_EVALUATION_CAPABILITY_KEY, OBSERVATION_ORDER_METHOD_CAPABILITY_VERSION, OBSERVATION_ORDER_PROJECTION_CAPABILITY_KEY
from empirical_lawhood.domains.matrix.six_matrix_response.observation_order import MatrixObservationOrderPairedHistoryResult, OBSERVATION_ORDER_HDF5_SCHEMA


_IMPLEMENTATION_SHA256 = sha256(b"matrix-response-study:method-config-reconstruction").hexdigest()
REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256 = sha256(
    b"matrix-response-reactive-entrance-causal-projection-and-single-terminal"
).hexdigest()
PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256 = sha256(
    b"matrix-response-prospective-reactive-source-law-causal-source-projection-and-terminal"
).hexdigest()
OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256 = sha256(
    b"matrix-observation-order-geometry-interval-transition-adjudication"
).hexdigest()


OBSERVATION_ORDER_PROJECTION_CAPABILITY = CapabilityManifest(
    capability_key=OBSERVATION_ORDER_PROJECTION_CAPABILITY_KEY,
    capability_version=OBSERVATION_ORDER_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.TRANSFORM,
    config_schema=MatrixObservationOrderProjectionConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixObservationOrderProjectionConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                OBSERVATION_ORDER_HDF5_SCHEMA,
                MatrixObservationOrderPairedHistoryResult.SCHEMA,
                LinkedCampaignStageEnvelope.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted((HistoryViewTrace.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))
    ),
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(
        cpu_cores=1,
        memory_bytes=2 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=7_200,
        source_scan_bytes=16 * 1024**2,
        output_bytes=512 * 1024,
    ),
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="matrix-observation-order-method",
    requires_clean_commit=True,
    requires_active_mount=True,
    requires_network=False,
    conformance_check_ids=(
        "dense-frozen-receiver-lattice",
        "one-pure-projection-per-view",
        "primitive-overlap-preserved",
    ),
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)

OBSERVATION_ORDER_EVALUATION_CAPABILITY = CapabilityManifest(
    capability_key=OBSERVATION_ORDER_EVALUATION_CAPABILITY_KEY,
    capability_version=OBSERVATION_ORDER_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.EVALUATOR,
    config_schema=MatrixObservationOrderEvaluationConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixObservationOrderEvaluationConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted((HistoryViewTrace.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))
    ),
    output_schema_ids=tuple(
        sorted(
            (
                MatrixObservationOrderEvaluation.SCHEMA,
                MatrixObservationOrderViewReport.SCHEMA,
                LinkedCampaignStageEnvelope.SCHEMA,
                ScientificAdjudicationRecord.SCHEMA,
            )
        )
    ),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_OUTCOME_VISIBLE,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            )
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=ResourceBudget(
        cpu_cores=1,
        memory_bytes=8 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=21_600,
        source_scan_bytes=5 * 1024**3,
        output_bytes=32 * 1024**2,
    ),
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="matrix-observation-order-method",
    requires_clean_commit=True,
    requires_active_mount=True,
    requires_network=False,
    conformance_check_ids=(
        "family-stratified-history-bootstrap",
        "grouped-interval-censored-npmle",
        "noncompensating-two-view-terminal",
        "single-immutable-adjudication",
    ),
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)


PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY = CapabilityManifest(
    capability_key=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY_KEY,
    capability_version=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.TRANSFORM,
    config_schema=MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(sorted((SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA, SixMatrixResponseProspectiveReactiveSourceLawHistoryResult.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))),
    output_schema_ids=tuple(sorted((MatrixResponseProspectiveReactiveSourceLawProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))),
    permissions=(CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(cpu_cores=1, memory_bytes=8 * 1024**3, gpu_devices=0, wall_time_seconds=14_400, source_scan_bytes=1024**3, output_bytes=16 * 1024**2),
    deterministic=True, seed_required=False, language_id="python", runtime_id="matrix-response-prospective-reactive-source-law-method",
    requires_clean_commit=True, requires_active_mount=True, requires_network=False,
    conformance_check_ids=("exact-reactive-entrance-outcomes", "past-only-prefix-recomputation", "routing-digest-verification"),
    implementation_sha256=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256,
)

PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY = CapabilityManifest(
    capability_key=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY_KEY,
    capability_version=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.EVALUATOR,
    config_schema=MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(sorted((MatrixResponseProspectiveReactiveSourceLawProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))),
    output_schema_ids=tuple(sorted((MatrixResponseProspectiveReactiveSourceLawAggregate.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA, ScientificAdjudicationRecord.SCHEMA))),
    permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_OUTCOME_VISIBLE, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=ResourceBudget(cpu_cores=1, memory_bytes=8 * 1024**3, gpu_devices=0, wall_time_seconds=14_400, source_scan_bytes=4 * 1024**3, output_bytes=32 * 1024**2),
    deterministic=True, seed_required=False, language_id="python", runtime_id="matrix-response-prospective-reactive-source-law-method",
    requires_clean_commit=True, requires_active_mount=True, requires_network=False,
    conformance_check_ids=("complete-256-plus-64-roster", "history-clustered-intervals", "single-frozen-terminal"),
    implementation_sha256=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256,
)


REACTIVE_ENTRANCE_PROJECTION_CAPABILITY = CapabilityManifest(
    capability_key=REACTIVE_ENTRANCE_PROJECTION_CAPABILITY_KEY,
    capability_version=REACTIVE_ENTRANCE_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.TRANSFORM,
    config_schema=MatrixResponseReactiveEntranceMethodConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixResponseReactiveEntranceMethodConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                REACTIVE_ENTRANCE_HDF5_SCHEMA,
                SixMatrixResponseReactiveEntrancePrecursorResult.SCHEMA,
                LinkedCampaignStageEnvelope.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted((MatrixResponseReactiveEntranceProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA))
    ),
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(
        cpu_cores=1,
        memory_bytes=4 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=7_200,
        source_scan_bytes=32 * 1024**2,
        output_bytes=4 * 1024**2,
    ),
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="matrix-response-reactive-entrance-method",
    requires_clean_commit=True,
    requires_active_mount=True,
    requires_network=False,
    conformance_check_ids=(
        "causal-competing-risk-entry",
        "complete-causal-intersection-residence-preparation-scheduling-response-geometric-conjunction",
        "one-projection-per-issued-view",
        "persisted-hdf5-custody-before-method",
    ),
    implementation_sha256=REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256,
)

REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY = CapabilityManifest(
    capability_key=REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY_KEY,
    capability_version=REACTIVE_ENTRANCE_METHOD_CAPABILITY_VERSION,
    kind=CapabilityKind.EVALUATOR,
    config_schema=MatrixResponseReactiveEntranceMethodConfig.SCHEMA,
    config_schema_sha256=sha256(MatrixResponseReactiveEntranceMethodConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                MatrixResponseReactiveEntranceAggregate.SCHEMA,
                MatrixResponseReactiveEntranceProjection.SCHEMA,
                LinkedCampaignStageEnvelope.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                MatrixResponseReactiveEntranceAggregate.SCHEMA,
                LinkedCampaignStageEnvelope.SCHEMA,
                ScientificAdjudicationRecord.SCHEMA,
            )
        )
    ),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_OUTCOME_VISIBLE,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            )
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.ORDER_RELATION,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=ResourceBudget(
        cpu_cores=1,
        memory_bytes=4 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=3_600,
        source_scan_bytes=4 * 1024**3,
        output_bytes=16 * 1024**2,
    ),
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="matrix-response-reactive-entrance-method",
    requires_clean_commit=True,
    requires_active_mount=True,
    requires_network=False,
    conformance_check_ids=(
        "exact-512-plus-128-roster",
        "five-way-reactive-entrance-terminal",
        "no-law-qualification",
        "single-frozen-terminal",
    ),
    implementation_sha256=REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256,
)


def _component(
    record_type: type[CanonicalRecord],
    suffix: str,
    kind: ExtensionComponentKind,
) -> ExtensionComponentRegistration:
    return ExtensionComponentRegistration(
        registration_id=f"component.matrix-response-study.{suffix}",
        component_key=f"matrix-response-study-{suffix}",
        component_version="1.0.0",
        kind=kind,
        input_schema_ids=(record_type.SCHEMA,),
        output_schema_ids=(record_type.SCHEMA,),
        implementation_sha256=_IMPLEMENTATION_SHA256,
    )


MATRIX_RESPONSE_LAW_CONFIG_DECODER = _component(
    MatrixResponseLawMethodConfig,
    "law-method-config-decoder",
    ExtensionComponentKind.CONFIG_DECODER,
)
MATRIX_RESPONSE_LAW_CONFIG_RECONSTRUCTOR = _component(
    MatrixResponseLawMethodConfig,
    "law-method-config-reconstructor",
    ExtensionComponentKind.RUNTIME_PROVIDER,
)
MATRIX_RESPONSE_REDUCER_CONFIG_DECODER = _component(
    MatrixResponsePairedPanelReducerConfig,
    "paired-panel-reducer-config-decoder",
    ExtensionComponentKind.CONFIG_DECODER,
)
MATRIX_RESPONSE_REDUCER_CONFIG_RECONSTRUCTOR = _component(
    MatrixResponsePairedPanelReducerConfig,
    "paired-panel-reducer-config-reconstructor",
    ExtensionComponentKind.RUNTIME_PROVIDER,
)
MATRIX_RESPONSE_ROLE_CONFIG_DECODER = _component(
    MatrixResponseRoleEquivarianceConfig,
    "role-equivariance-config-decoder",
    ExtensionComponentKind.CONFIG_DECODER,
)
MATRIX_RESPONSE_ROLE_CONFIG_RECONSTRUCTOR = _component(
    MatrixResponseRoleEquivarianceConfig,
    "role-equivariance-config-reconstructor",
    ExtensionComponentKind.RUNTIME_PROVIDER,
)
MATRIX_RESPONSE_STRUCTURAL_CONFIG_DECODER = _component(
    MatrixResponseStructuralFacePlan,
    "structural-face-plan-decoder",
    ExtensionComponentKind.CONFIG_DECODER,
)
MATRIX_RESPONSE_STRUCTURAL_CONFIG_RECONSTRUCTOR = _component(
    MatrixResponseStructuralFacePlan,
    "structural-face-plan-reconstructor",
    ExtensionComponentKind.RUNTIME_PROVIDER,
)
MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_DECODER = _component(
    MatrixResponseCausalIntersectionResidenceStudyConfig,
    "causal-intersection-residence-study-config-decoder",
    ExtensionComponentKind.CONFIG_DECODER,
)
MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_RECONSTRUCTOR = _component(
    MatrixResponseCausalIntersectionResidenceStudyConfig,
    "causal-intersection-residence-study-config-reconstructor",
    ExtensionComponentKind.RUNTIME_PROVIDER,
)
REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-reactive-entrance.method-config-decoder",
    component_key="matrix-response-reactive-entrance-method-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(MatrixResponseReactiveEntranceMethodConfig.SCHEMA,),
    output_schema_ids=(MatrixResponseReactiveEntranceMethodConfig.SCHEMA,),
    implementation_sha256=REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256,
)
REACTIVE_ENTRANCE_PROJECTION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-reactive-entrance.projection-provider",
    component_key="matrix-response-reactive-entrance-projection-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=REACTIVE_ENTRANCE_PROJECTION_CAPABILITY.input_schema_ids,
    output_schema_ids=REACTIVE_ENTRANCE_PROJECTION_CAPABILITY.output_schema_ids,
    implementation_sha256=REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256,
)
REACTIVE_ENTRANCE_FINALIZATION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-reactive-entrance.finalization-provider",
    component_key="matrix-response-reactive-entrance-finalization-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY.input_schema_ids,
    output_schema_ids=REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY.output_schema_ids,
    implementation_sha256=REACTIVE_ENTRANCE_METHOD_IMPLEMENTATION_SHA256,
)
PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-prospective-reactive-source-law.method-config-decoder",
    component_key="matrix-response-prospective-reactive-source-law-method-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,),
    output_schema_ids=(MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,),
    implementation_sha256=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256,
)
PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-prospective-reactive-source-law.projection-provider",
    component_key="matrix-response-prospective-reactive-source-law-projection-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY.input_schema_ids,
    output_schema_ids=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY.output_schema_ids,
    implementation_sha256=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256,
)
PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-response-prospective-reactive-source-law.finalization-provider",
    component_key="matrix-response-prospective-reactive-source-law-finalization-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY.input_schema_ids,
    output_schema_ids=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY.output_schema_ids,
    implementation_sha256=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_IMPLEMENTATION_SHA256,
)
OBSERVATION_ORDER_PROJECTION_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.matrix-observation-order.projection-config-decoder",
    component_key="matrix-observation-order-projection-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(MatrixObservationOrderProjectionConfig.SCHEMA,),
    output_schema_ids=(MatrixObservationOrderProjectionConfig.SCHEMA,),
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)
OBSERVATION_ORDER_EVALUATION_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.matrix-observation-order.evaluation-config-decoder",
    component_key="matrix-observation-order-evaluation-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(MatrixObservationOrderEvaluationConfig.SCHEMA,),
    output_schema_ids=(MatrixObservationOrderEvaluationConfig.SCHEMA,),
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)
OBSERVATION_ORDER_PROJECTION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-observation-order.projection-provider",
    component_key="matrix-observation-order-projection-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=OBSERVATION_ORDER_PROJECTION_CAPABILITY.input_schema_ids,
    output_schema_ids=OBSERVATION_ORDER_PROJECTION_CAPABILITY.output_schema_ids,
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)
OBSERVATION_ORDER_EVALUATION_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.matrix-observation-order.evaluation-provider",
    component_key="matrix-observation-order-evaluation-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=OBSERVATION_ORDER_EVALUATION_CAPABILITY.input_schema_ids,
    output_schema_ids=OBSERVATION_ORDER_EVALUATION_CAPABILITY.output_schema_ids,
    implementation_sha256=OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)
OBSERVATION_ORDER_PROJECTION_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    OBSERVATION_ORDER_PROJECTION_CAPABILITY,
    OBSERVATION_ORDER_PROJECTION_PROVIDER.component_key,
    OBSERVATION_ORDER_PROJECTION_PROVIDER.component_version,
    "application/vnd.empirical-lawhood.canonical+json",
    4 * 1024**2,
)
OBSERVATION_ORDER_EVALUATION_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    OBSERVATION_ORDER_EVALUATION_CAPABILITY,
    OBSERVATION_ORDER_EVALUATION_PROVIDER.component_key,
    OBSERVATION_ORDER_EVALUATION_PROVIDER.component_version,
    "application/vnd.empirical-lawhood.canonical+json",
    4 * 1024**2,
)
OBSERVATION_ORDER_OBSERVATION_METHOD_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    "profile-registration.matrix-observation-order-observation-methods",
    "matrix-observation-order-observation-methods",
    "1.0.0",
    ExtensionProfileKind.OBJECTIVE_TERMINAL,
    ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    OBSERVATION_ORDER_METHOD_IMPLEMENTATION_SHA256,
)


_DECODERS = tuple(
    sorted(
        (
            MATRIX_RESPONSE_LAW_CONFIG_DECODER,
            OBSERVATION_ORDER_EVALUATION_CONFIG_DECODER,
            OBSERVATION_ORDER_PROJECTION_CONFIG_DECODER,
            PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER,
            REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER,
            MATRIX_RESPONSE_REDUCER_CONFIG_DECODER,
            MATRIX_RESPONSE_ROLE_CONFIG_DECODER,
            MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_DECODER,
            MATRIX_RESPONSE_STRUCTURAL_CONFIG_DECODER,
        ),
        key=lambda value: value.registration_id,
    )
)
_RECONSTRUCTORS = tuple(
    sorted(
        (
            MATRIX_RESPONSE_LAW_CONFIG_RECONSTRUCTOR,
            OBSERVATION_ORDER_EVALUATION_PROVIDER,
            OBSERVATION_ORDER_PROJECTION_PROVIDER,
            PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_PROVIDER,
            PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_PROVIDER,
            REACTIVE_ENTRANCE_FINALIZATION_PROVIDER,
            REACTIVE_ENTRANCE_PROJECTION_PROVIDER,
            MATRIX_RESPONSE_REDUCER_CONFIG_RECONSTRUCTOR,
            MATRIX_RESPONSE_ROLE_CONFIG_RECONSTRUCTOR,
            MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_RECONSTRUCTOR,
            MATRIX_RESPONSE_STRUCTURAL_CONFIG_RECONSTRUCTOR,
        ),
        key=lambda value: value.registration_id,
    )
)


_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.matrix-response-study-method-config",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.METHOD,
    evidence_profile_registries=(),
    capability_manifests=tuple(
        sorted(
            (
                PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY,
                PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY,
                REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY,
                REACTIVE_ENTRANCE_PROJECTION_CAPABILITY,
                OBSERVATION_ORDER_EVALUATION_CAPABILITY,
                OBSERVATION_ORDER_PROJECTION_CAPABILITY,
            ),
            key=lambda value: value.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                OBSERVATION_ORDER_EVALUATION_CANDIDATE_REGISTRATION,
                OBSERVATION_ORDER_PROJECTION_CANDIDATE_REGISTRATION,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    dataset_capability_registries=(),
    profile_registrations=(OBSERVATION_ORDER_OBSERVATION_METHOD_PROFILE_REGISTRATION,),
    method_registrations=(),
    config_decoders=tuple(
        ObjectIdentity.from_record(value.registration_id, value) for value in _DECODERS
    ),
    artifact_validators=(),
    runtime_providers=tuple(
        ObjectIdentity.from_record(value.registration_id, value) for value in _RECONSTRUCTORS
    ),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
from hashlib import sha256
from typing import cast

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableFactory, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.extension_bundles import ExtensionComponentRegistration
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.capabilities import CapabilityManifest, CapabilityRegistry
from empirical_lawhood.domains.matrix.matrix_response_study.authoring.causal_intersection_residence_design import MatrixResponseCausalIntersectionResidenceStudyConfig
from empirical_lawhood.domains.matrix.six_matrix_response.reactive_entrance import SixMatrixResponseReactiveEntranceSourceConfig
from empirical_lawhood.domains.matrix.six_matrix_response.prospective_reactive_source import SixMatrixResponseProspectiveReactiveSourceLawSourceConfig

from empirical_lawhood.domains.matrix.matrix_response_study.contracts import MatrixResponseLawMethodConfig, MatrixResponsePairedPanelReducerConfig, MatrixResponseRoleEquivarianceConfig, MatrixResponseStructuralFacePlan

from empirical_lawhood.domains.matrix.matrix_response_study.observation_order import MatrixObservationOrderEvaluationConfig, MatrixObservationOrderProjectionConfig
from empirical_lawhood.domains.matrix.matrix_response_study.observation_order_provider import MatrixObservationOrderEvaluationProvider, MatrixObservationOrderProjectionProvider
from empirical_lawhood.domains.matrix.matrix_response_study.reactive_entrance_provider import MatrixResponseReactiveEntranceFinalizationProvider, MatrixResponseReactiveEntranceProjectionProvider
from empirical_lawhood.domains.matrix.matrix_response_study.reactive_entrance_source import MatrixResponseReactiveEntranceMethodConfig
from empirical_lawhood.domains.matrix.matrix_response_study.prospective_reactive_source_law import MatrixResponseProspectiveReactiveSourceLawMethodConfig
from empirical_lawhood.domains.matrix.matrix_response_study.prospective_reactive_source_provider import MatrixResponseProspectiveReactiveSourceLawFinalizationProvider, MatrixResponseProspectiveReactiveSourceLawProjectionProvider


_MAXIMUM_PAYLOAD_BYTES = 4 * 1024 * 1024


def _decoder(
    *,
    registration_id: str,
    component: ExtensionComponentRegistration,
    record_type: type[CanonicalRecord],
) -> StudyExtensionDecoderRegistration:
    return StudyExtensionDecoderRegistration(
        registration_id=registration_id,
        decoder_key=component.component_key,
        decoder_version=component.component_version,
        payload_schema=record_type.SCHEMA,
        payload_version=record_type.VERSION,
        config_sha256=sha256(
            canonical_json_bytes(
                {
                    "decoder_key": component.component_key,
                    "decoder_version": component.component_version,
                    "mode": "exact-canonical-record",
                    "payload_schema": record_type.SCHEMA,
                }
            )
        ).hexdigest(),
        implementation_sha256=component.implementation_sha256,
        maximum_payload_bytes=_MAXIMUM_PAYLOAD_BYTES,
    )


MATRIX_RESPONSE_LAW_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-study-law-method-config",
    component=MATRIX_RESPONSE_LAW_CONFIG_DECODER,
    record_type=MatrixResponseLawMethodConfig,
)
MATRIX_RESPONSE_REDUCER_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-study-paired-panel-reducer-config",
    component=MATRIX_RESPONSE_REDUCER_CONFIG_DECODER,
    record_type=MatrixResponsePairedPanelReducerConfig,
)
MATRIX_RESPONSE_ROLE_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-study-role-equivariance-config",
    component=MATRIX_RESPONSE_ROLE_CONFIG_DECODER,
    record_type=MatrixResponseRoleEquivarianceConfig,
)
MATRIX_RESPONSE_STRUCTURAL_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-study-structural-face-plan",
    component=MATRIX_RESPONSE_STRUCTURAL_CONFIG_DECODER,
    record_type=MatrixResponseStructuralFacePlan,
)
MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-study-causal-intersection-residence-study-config",
    component=MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_DECODER,
    record_type=MatrixResponseCausalIntersectionResidenceStudyConfig,
)
REACTIVE_ENTRANCE_METHOD_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-reactive-entrance-method-config",
    component=REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER,
    record_type=MatrixResponseReactiveEntranceMethodConfig,
)
PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-response-prospective-reactive-source-law-method-config",
    component=PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER,
    record_type=MatrixResponseProspectiveReactiveSourceLawMethodConfig,
)
OBSERVATION_ORDER_PROJECTION_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-observation-order-projection-config",
    component=OBSERVATION_ORDER_PROJECTION_CONFIG_DECODER,
    record_type=MatrixObservationOrderProjectionConfig,
)
OBSERVATION_ORDER_EVALUATION_DECODER_REGISTRATION = _decoder(
    registration_id="decoder-registration.matrix-observation-order-evaluation-config",
    component=OBSERVATION_ORDER_EVALUATION_CONFIG_DECODER,
    record_type=MatrixObservationOrderEvaluationConfig,
)


def _rn0_runtime_binding(
    *,
    binding_id: str,
    capability: CapabilityManifest,
    provider: ExtensionComponentRegistration,
    owns_issued_method_config: bool,
) -> ExecutableCapabilityBinding:
    discovery_components = (
        (REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER, provider)
        if owns_issued_method_config
        else (provider,)
    )
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=capability.capability_key,
        capability_version=capability.capability_version,
        capability_implementation_sha256=capability.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=provider.component_key,
        provider_version=provider.component_version,
        provider_implementation_sha256=provider.implementation_sha256,
        capability_backed=True,
        discovery_components=tuple(
            sorted(
                discovery_components,
                key=lambda value: value.registration_id,
            )
        ),
        accepted_profile_types=(),
        accepted_config_types=tuple(
            sorted(
                (
                    ExecutableRecordTypeBinding(
                        MatrixResponseReactiveEntranceMethodConfig.SCHEMA,
                        MatrixResponseReactiveEntranceMethodConfig.VERSION,
                    ),
                    ExecutableRecordTypeBinding(
                        SixMatrixResponseReactiveEntranceSourceConfig.SCHEMA,
                        SixMatrixResponseReactiveEntranceSourceConfig.VERSION,
                    ),
                ),
                key=lambda value: value.record_schema,
            )
        ),
        required_issued_payload_schemas=(
            (MatrixResponseReactiveEntranceMethodConfig.SCHEMA,) if owns_issued_method_config else ()
        ),
        required_authenticated_record_schemas=tuple(
            sorted(
                (
                    SixMatrixResponseReactiveEntranceSourceConfig.SCHEMA,
                    *((MatrixResponseReactiveEntranceMethodConfig.SCHEMA,) if not owns_issued_method_config else ()),
                )
            )
        ),
        codec_registration_identities=(
            (
                ObjectIdentity.from_record(
                    REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER.registration_id,
                    REACTIVE_ENTRANCE_METHOD_CONFIG_DECODER,
                ),
            )
            if owns_issued_method_config
            else ()
        ),
        issued_decoder_registrations=(
            (REACTIVE_ENTRANCE_METHOD_DECODER_REGISTRATION,) if owns_issued_method_config else ()
        ),
        input_schema_ids=capability.input_schema_ids,
        output_schema_ids=capability.output_schema_ids,
        artifact_validator_identities=(),
        required_platform_port_keys=(),
        may_require_active_mount=True,
        may_require_source_qualification=True,
        may_require_network=False,
        may_require_authority=True,
    )


REACTIVE_ENTRANCE_PROJECTION_EXECUTABLE_BINDING = _rn0_runtime_binding(
    binding_id="binding.matrix-response-reactive-entrance-reactive-entrance-projection",
    capability=REACTIVE_ENTRANCE_PROJECTION_CAPABILITY,
    provider=REACTIVE_ENTRANCE_PROJECTION_PROVIDER,
    owns_issued_method_config=True,
)
REACTIVE_ENTRANCE_FINALIZATION_EXECUTABLE_BINDING = _rn0_runtime_binding(
    binding_id="binding.matrix-response-reactive-entrance-source-finalization",
    capability=REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY,
    provider=REACTIVE_ENTRANCE_FINALIZATION_PROVIDER,
    owns_issued_method_config=False,
)


def _psl_runtime_binding(
    *,
    binding_id: str,
    capability: CapabilityManifest,
    provider: ExtensionComponentRegistration,
    owns_issued_method_config: bool,
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=capability.capability_key,
        capability_version=capability.capability_version,
        capability_implementation_sha256=capability.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=provider.component_key,
        provider_version=provider.component_version,
        provider_implementation_sha256=provider.implementation_sha256,
        capability_backed=True,
        discovery_components=tuple(sorted(
            ((PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER, provider) if owns_issued_method_config else (provider,)),
            key=lambda value: value.registration_id,
        )),
        accepted_profile_types=(),
        accepted_config_types=tuple(sorted((
            ExecutableRecordTypeBinding(MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA, MatrixResponseProspectiveReactiveSourceLawMethodConfig.VERSION),
            ExecutableRecordTypeBinding(SixMatrixResponseProspectiveReactiveSourceLawSourceConfig.SCHEMA, SixMatrixResponseProspectiveReactiveSourceLawSourceConfig.VERSION),
        ), key=lambda value: value.record_schema)),
        required_issued_payload_schemas=((MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,) if owns_issued_method_config else ()),
        required_authenticated_record_schemas=tuple(sorted((
            SixMatrixResponseProspectiveReactiveSourceLawSourceConfig.SCHEMA,
            *((MatrixResponseProspectiveReactiveSourceLawMethodConfig.SCHEMA,) if not owns_issued_method_config else ()),
        ))),
        codec_registration_identities=((ObjectIdentity.from_record(PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER.registration_id, PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_CONFIG_DECODER),) if owns_issued_method_config else ()),
        issued_decoder_registrations=((PROSPECTIVE_REACTIVE_SOURCE_LAW_METHOD_DECODER_REGISTRATION,) if owns_issued_method_config else ()),
        input_schema_ids=capability.input_schema_ids,
        output_schema_ids=capability.output_schema_ids,
        artifact_validator_identities=(), required_platform_port_keys=(),
        may_require_active_mount=True, may_require_source_qualification=True,
        may_require_network=False, may_require_authority=True,
    )


PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_EXECUTABLE_BINDING = _psl_runtime_binding(
    binding_id="binding.matrix-response-prospective-reactive-source-law-causal-source-projection",
    capability=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY,
    provider=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_PROVIDER,
    owns_issued_method_config=True,
)
PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_EXECUTABLE_BINDING = _psl_runtime_binding(
    binding_id="binding.matrix-response-prospective-reactive-source-law-source-law-finalization",
    capability=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY,
    provider=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_PROVIDER,
    owns_issued_method_config=False,
)


def _observation_order_runtime_binding(
    *,
    binding_id: str,
    capability: CapabilityManifest,
    decoder_component: ExtensionComponentRegistration,
    provider: ExtensionComponentRegistration,
    decoder: StudyExtensionDecoderRegistration,
    record_type: type[CanonicalRecord],
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=capability.capability_key,
        capability_version=capability.capability_version,
        capability_implementation_sha256=capability.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=provider.component_key,
        provider_version=provider.component_version,
        provider_implementation_sha256=provider.implementation_sha256,
        capability_backed=True,
        discovery_components=tuple(
            sorted((decoder_component, provider), key=lambda value: value.registration_id)
        ),
        accepted_profile_types=(),
        accepted_config_types=(
            ExecutableRecordTypeBinding(record_type.SCHEMA, record_type.VERSION),
        ),
        required_issued_payload_schemas=(record_type.SCHEMA,),
        codec_registration_identities=(
            ObjectIdentity.from_record(decoder_component.registration_id, decoder_component),
        ),
        issued_decoder_registrations=(decoder,),
        input_schema_ids=capability.input_schema_ids,
        output_schema_ids=capability.output_schema_ids,
        artifact_validator_identities=(),
        required_platform_port_keys=(),
        may_require_active_mount=True,
        may_require_source_qualification=False,
        may_require_network=False,
        may_require_authority=True,
    )


OBSERVATION_ORDER_PROJECTION_EXECUTABLE_BINDING = _observation_order_runtime_binding(
    binding_id="binding.matrix-observation-order-geometry-projection",
    capability=OBSERVATION_ORDER_PROJECTION_CAPABILITY,
    decoder_component=OBSERVATION_ORDER_PROJECTION_CONFIG_DECODER,
    provider=OBSERVATION_ORDER_PROJECTION_PROVIDER,
    decoder=OBSERVATION_ORDER_PROJECTION_DECODER_REGISTRATION,
    record_type=MatrixObservationOrderProjectionConfig,
)
OBSERVATION_ORDER_EVALUATION_EXECUTABLE_BINDING = _observation_order_runtime_binding(
    binding_id="binding.matrix-observation-order-sealed-evaluation",
    capability=OBSERVATION_ORDER_EVALUATION_CAPABILITY,
    decoder_component=OBSERVATION_ORDER_EVALUATION_CONFIG_DECODER,
    provider=OBSERVATION_ORDER_EVALUATION_PROVIDER,
    decoder=OBSERVATION_ORDER_EVALUATION_DECODER_REGISTRATION,
    record_type=MatrixObservationOrderEvaluationConfig,
)


def _binding(
    *,
    binding_id: str,
    decoder_component: ExtensionComponentRegistration,
    reconstructor_component: ExtensionComponentRegistration,
    decoder: StudyExtensionDecoderRegistration,
    record_type: type[CanonicalRecord],
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=reconstructor_component.component_key,
        capability_version=reconstructor_component.component_version,
        capability_implementation_sha256=_IMPLEMENTATION_SHA256,
        role=ExecutableBindingRole.PROFILE_COMPILER,
        provider_key=reconstructor_component.component_key,
        provider_version=reconstructor_component.component_version,
        provider_implementation_sha256=_IMPLEMENTATION_SHA256,
        capability_backed=False,
        discovery_components=tuple(
            sorted(
                (decoder_component, reconstructor_component),
                key=lambda value: value.registration_id,
            )
        ),
        accepted_profile_types=(),
        accepted_config_types=(
            ExecutableRecordTypeBinding(record_type.SCHEMA, record_type.VERSION),
        ),
        required_issued_payload_schemas=(record_type.SCHEMA,),
        codec_registration_identities=(
            ObjectIdentity.from_record(decoder_component.registration_id, decoder_component),
        ),
        issued_decoder_registrations=(decoder,),
        input_schema_ids=(record_type.SCHEMA,),
        output_schema_ids=(record_type.SCHEMA,),
        artifact_validator_identities=(),
        required_platform_port_keys=(),
        may_require_active_mount=False,
        may_require_source_qualification=False,
        may_require_network=False,
        may_require_authority=False,
    )


_BINDING_INPUTS = (
    (
        "binding.matrix-response-study-law-method-config-reconstructor",
        MATRIX_RESPONSE_LAW_CONFIG_DECODER,
        MATRIX_RESPONSE_LAW_CONFIG_RECONSTRUCTOR,
        MATRIX_RESPONSE_LAW_DECODER_REGISTRATION,
        MatrixResponseLawMethodConfig,
    ),
    (
        "binding.matrix-response-study-paired-panel-reducer-config-reconstructor",
        MATRIX_RESPONSE_REDUCER_CONFIG_DECODER,
        MATRIX_RESPONSE_REDUCER_CONFIG_RECONSTRUCTOR,
        MATRIX_RESPONSE_REDUCER_DECODER_REGISTRATION,
        MatrixResponsePairedPanelReducerConfig,
    ),
    (
        "binding.matrix-response-study-role-equivariance-config-reconstructor",
        MATRIX_RESPONSE_ROLE_CONFIG_DECODER,
        MATRIX_RESPONSE_ROLE_CONFIG_RECONSTRUCTOR,
        MATRIX_RESPONSE_ROLE_DECODER_REGISTRATION,
        MatrixResponseRoleEquivarianceConfig,
    ),
    (
        "binding.matrix-response-study-causal-intersection-residence-study-config-reconstructor",
        MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_DECODER,
        MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_CONFIG_RECONSTRUCTOR,
        MATRIX_RESPONSE_CAUSAL_INTERSECTION_RESIDENCE_DECODER_REGISTRATION,
        MatrixResponseCausalIntersectionResidenceStudyConfig,
    ),
    (
        "binding.matrix-response-study-structural-face-plan-reconstructor",
        MATRIX_RESPONSE_STRUCTURAL_CONFIG_DECODER,
        MATRIX_RESPONSE_STRUCTURAL_CONFIG_RECONSTRUCTOR,
        MATRIX_RESPONSE_STRUCTURAL_DECODER_REGISTRATION,
        MatrixResponseStructuralFacePlan,
    ),
)
_BINDINGS = tuple(
    sorted(
        (
            _binding(
                binding_id=binding_id,
                decoder_component=decoder_component,
                reconstructor_component=reconstructor_component,
                decoder=decoder,
                record_type=record_type,
            )
            for (
                binding_id,
                decoder_component,
                reconstructor_component,
                decoder,
                record_type,
            ) in _BINDING_INPUTS
        ),
        key=lambda value: value.binding_id,
    )
)


@dataclass(frozen=True, slots=True)
class MatrixResponseExactRecordReconstructionFactory:
    binding: ExecutableCapabilityBinding
    record_type: type[CanonicalRecord]

    def build_compiler(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CanonicalRecord:
        if platform_ports or len(records) != 1 or not isinstance(records[0], self.record_type):
            raise ValueError("Six-matrix response reconstruction requires one exact issued record and no ports")
        return records[0]


@dataclass(frozen=True, slots=True)
class MatrixResponseReactiveEntranceProjectionProviderFactory:
    binding: ExecutableCapabilityBinding = REACTIVE_ENTRANCE_PROJECTION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseReactiveEntranceProjectionProvider:
        by_type = {type(value): value for value in records}
        if (
            platform_ports
            or len(by_type) != len(records)
            or set(by_type) != {MatrixResponseReactiveEntranceMethodConfig, SixMatrixResponseReactiveEntranceSourceConfig}
        ):
            raise ValueError("matrix response reactive entrance projection factory requires exact source/method records")
        return MatrixResponseReactiveEntranceProjectionProvider(
            registry=registry,
            manifest=REACTIVE_ENTRANCE_PROJECTION_CAPABILITY,
            source_config=cast(SixMatrixResponseReactiveEntranceSourceConfig, by_type[SixMatrixResponseReactiveEntranceSourceConfig]),
            method_config=cast(MatrixResponseReactiveEntranceMethodConfig, by_type[MatrixResponseReactiveEntranceMethodConfig]),
        )


@dataclass(frozen=True, slots=True)
class MatrixResponseReactiveEntranceFinalizationProviderFactory:
    binding: ExecutableCapabilityBinding = REACTIVE_ENTRANCE_FINALIZATION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseReactiveEntranceFinalizationProvider:
        by_type = {type(value): value for value in records}
        if (
            platform_ports
            or len(by_type) != len(records)
            or set(by_type) != {MatrixResponseReactiveEntranceMethodConfig, SixMatrixResponseReactiveEntranceSourceConfig}
        ):
            raise ValueError("matrix response reactive entrance finalizer factory requires exact source/method records")
        return MatrixResponseReactiveEntranceFinalizationProvider(
            registry=registry,
            manifest=REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY,
            source_config=cast(SixMatrixResponseReactiveEntranceSourceConfig, by_type[SixMatrixResponseReactiveEntranceSourceConfig]),
            method_config=cast(MatrixResponseReactiveEntranceMethodConfig, by_type[MatrixResponseReactiveEntranceMethodConfig]),
        )


@dataclass(frozen=True, slots=True)
class MatrixResponseProspectiveReactiveSourceLawProjectionProviderFactory:
    binding: ExecutableCapabilityBinding = PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseProspectiveReactiveSourceLawProjectionProvider:
        by_type = {type(value): value for value in records}
        if platform_ports or len(by_type) != len(records) or set(by_type) != {MatrixResponseProspectiveReactiveSourceLawMethodConfig, SixMatrixResponseProspectiveReactiveSourceLawSourceConfig}:
            raise ValueError("matrix response prospective reactive source law projection factory requires exact source/method records")
        return MatrixResponseProspectiveReactiveSourceLawProjectionProvider(
            registry=registry, manifest=PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY,
            source=cast(SixMatrixResponseProspectiveReactiveSourceLawSourceConfig, by_type[SixMatrixResponseProspectiveReactiveSourceLawSourceConfig]),
            method=cast(MatrixResponseProspectiveReactiveSourceLawMethodConfig, by_type[MatrixResponseProspectiveReactiveSourceLawMethodConfig]),
        )


@dataclass(frozen=True, slots=True)
class MatrixResponseProspectiveReactiveSourceLawFinalizationProviderFactory:
    binding: ExecutableCapabilityBinding = PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseProspectiveReactiveSourceLawFinalizationProvider:
        by_type = {type(value): value for value in records}
        if platform_ports or len(by_type) != len(records) or set(by_type) != {MatrixResponseProspectiveReactiveSourceLawMethodConfig, SixMatrixResponseProspectiveReactiveSourceLawSourceConfig}:
            raise ValueError("matrix response prospective reactive source law finalizer factory requires exact source/method records")
        return MatrixResponseProspectiveReactiveSourceLawFinalizationProvider(
            registry=registry, manifest=PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY,
            source=cast(SixMatrixResponseProspectiveReactiveSourceLawSourceConfig, by_type[SixMatrixResponseProspectiveReactiveSourceLawSourceConfig]),
            method=cast(MatrixResponseProspectiveReactiveSourceLawMethodConfig, by_type[MatrixResponseProspectiveReactiveSourceLawMethodConfig]),
        )


@dataclass(frozen=True, slots=True)
class MatrixObservationOrderProjectionProviderFactory:
    binding: ExecutableCapabilityBinding = OBSERVATION_ORDER_PROJECTION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixObservationOrderProjectionProvider:
        if platform_ports or len(records) != 1 or not isinstance(
            records[0], MatrixObservationOrderProjectionConfig
        ):
            raise ValueError("observation order projection provider requires its exact issued config")
        return MatrixObservationOrderProjectionProvider(
            registry=registry,
            manifest=OBSERVATION_ORDER_PROJECTION_CAPABILITY,
            config=records[0],
        )


@dataclass(frozen=True, slots=True)
class MatrixObservationOrderEvaluationProviderFactory:
    binding: ExecutableCapabilityBinding = OBSERVATION_ORDER_EVALUATION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixObservationOrderEvaluationProvider:
        if platform_ports or len(records) != 1 or not isinstance(
            records[0], MatrixObservationOrderEvaluationConfig
        ):
            raise ValueError("observation order evaluator provider requires its exact issued config")
        return MatrixObservationOrderEvaluationProvider(
            registry=registry,
            manifest=OBSERVATION_ORDER_EVALUATION_CAPABILITY,
            config=records[0],
        )


_EXECUTABLE_ID = "executable-contribution.matrix-response-study-method-config"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES: tuple[ExecutableFactory, ...] = tuple(
    sorted(
        (
            *(
                cast(
                    ExecutableFactory,
                    MatrixResponseExactRecordReconstructionFactory(
                        binding,
                        next(
                            record_type
                            for binding_id, _, _, _, record_type in _BINDING_INPUTS
                            if binding_id == binding.binding_id
                        ),
                    ),
                )
                for binding in _BINDINGS
            ),
            cast(ExecutableFactory, MatrixResponseReactiveEntranceFinalizationProviderFactory()),
            cast(ExecutableFactory, MatrixResponseReactiveEntranceProjectionProviderFactory()),
            cast(ExecutableFactory, MatrixResponseProspectiveReactiveSourceLawFinalizationProviderFactory()),
            cast(ExecutableFactory, MatrixResponseProspectiveReactiveSourceLawProjectionProviderFactory()),
            cast(ExecutableFactory, MatrixObservationOrderEvaluationProviderFactory()),
            cast(ExecutableFactory, MatrixObservationOrderProjectionProviderFactory()),
        ),
        key=lambda value: value.binding.binding_id,
    )
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = tuple(
    sorted(
        (
            MatrixResponseLawMethodConfig,
            MatrixObservationOrderEvaluationConfig,
            MatrixObservationOrderProjectionConfig,
            MatrixResponseReactiveEntranceMethodConfig,
            MatrixResponseProspectiveReactiveSourceLawMethodConfig,
            MatrixResponsePairedPanelReducerConfig,
            MatrixResponseRoleEquivarianceConfig,
            MatrixResponseCausalIntersectionResidenceStudyConfig,
            MatrixResponseStructuralFacePlan,
        ),
        key=lambda value: value.SCHEMA,
    )
)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'OBSERVATION_ORDER_EVALUATION_CAPABILITY', 'OBSERVATION_ORDER_EVALUATION_EXECUTABLE_BINDING', 'OBSERVATION_ORDER_PROJECTION_CAPABILITY', 'OBSERVATION_ORDER_PROJECTION_EXECUTABLE_BINDING', 'PROSPECTIVE_REACTIVE_SOURCE_LAW_FINALIZATION_CAPABILITY', 'PROSPECTIVE_REACTIVE_SOURCE_LAW_PROJECTION_CAPABILITY', 'REACTIVE_ENTRANCE_FINALIZATION_CAPABILITY', 'REACTIVE_ENTRANCE_PROJECTION_CAPABILITY']
