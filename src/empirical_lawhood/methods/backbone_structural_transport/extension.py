# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass


# Scientific registration and configuration.



from hashlib import sha256

from empirical_lawhood.methods.structural_bootstrap_inputs import StructuralBootstrapInputCensus
from empirical_lawhood.methods.prospective_structural_recurrence import StructuralRecurrenceFrozenLawTransportForecasts, PROSPECTIVE_STRUCTURAL_RECURRENCE_IMPLEMENTATION_SHA256, PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_KEY, PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_VERSION, StructuralRecurrenceMetricDynamicalForecast, ProspectiveStructuralRecurrenceAdjudication, ProspectiveStructuralRecurrenceFaceTerminal, ProspectiveStructuralRecurrenceMethodSpec, ProspectiveStructuralRecurrencePlan, ProspectiveStructuralRecurrenceRosterIssue, ProspectiveStructuralRecurrenceTargetObservation, ProspectiveStructuralRecurrenceTargetTerminal
from empirical_lawhood.methods.structural_recurrence_targets import StructuralRecurrenceStageEvidence
from empirical_lawhood.methods.structural_recurrence import StructuralObservation, StructuralPredictionInput
from empirical_lawhood.methods.interval_property_comparison import INTERVAL_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256, INTERVAL_PROPERTY_COMPARISON_METHOD_KEY, INTERVAL_PROPERTY_COMPARISON_METHOD_VERSION, IntervalPropertyComparisonMethodSpec, IntervalPropertyComparisonOperands, IntervalPropertyComparisonResult
from empirical_lawhood.methods.transformed_property_comparison import TRANSFORMED_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256, TRANSFORMED_PROPERTY_COMPARISON_METHOD_KEY, TRANSFORMED_PROPERTY_COMPARISON_METHOD_VERSION, TransformedPropertyComparisonMethodSpec, TransformedPropertyComparisonOperands, TransformedPropertyComparisonResult
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.response.laws import ResponseLaw
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.contrasting_objectives import StructuralFaceHandoffProfile
from empirical_lawhood.design.metatheory_campaign import MetatheoryCampaignProfile, MetatheoryCampaignStageRole
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.response_experiment import ResponseStageTerminal

from empirical_lawhood.methods.backbone_structural_transport.campaign import StructuralDevelopmentBridgeConfig, StructuralDevelopmentInputs, StructuralPredictionFreezeReceipt, StructuralRecurrenceTransportConfig, StructuralReporterConfig, StructuralTargetBridgeConfig
from empirical_lawhood.methods.backbone_structural_transport.provider import STRUCTURAL_TRANSPORT_MEDIA_TYPE
from empirical_lawhood.methods.backbone_structural_transport.metatheory_conformance import EXECUTABLE_METATHEORY_ACQUISITION_KEY, EXECUTABLE_METATHEORY_CONFORMANCE_IMPLEMENTATION_SHA256, EXECUTABLE_METATHEORY_CONFORMANCE_VERSION, EXECUTABLE_METATHEORY_DEVELOPMENT_KEY, EXECUTABLE_METATHEORY_EVALUATOR_KEY, EXECUTABLE_METATHEORY_PREDICTION_KEY, EXECUTABLE_METATHEORY_QUALIFICATION_KEY, EXECUTABLE_METATHEORY_REPORTER_KEY, METATHEORY_CONFORMANCE_TERMINAL_TYPE_BY_ROLE, MetatheoryConformanceAcquisitionConfig, MetatheoryConformanceDevelopmentConfig, MetatheoryConformanceEvaluatorConfig, MetatheoryConformanceFixture, MetatheoryConformancePredictionConfig, MetatheoryConformanceQualificationConfig, MetatheoryConformanceReporterConfig
from empirical_lawhood.methods.backbone_structural_transport.source_free_property_transport_contracts import source_free_property_transport_capability_registry
from empirical_lawhood.methods.backbone_structural_transport.source_free_property_transport_records import SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPE_BY_ROLE


STRUCTURAL_TRANSPORT_PROVIDER_IMPLEMENTATION_SHA256 = sha256(
    b"empirical-lawhood/backbone-structural-transport-provider"
).hexdigest()
_MAXIMUM_CONFIG_BYTES = 4 * 1024 * 1024
_RESOURCE = ResourceBudget(
    cpu_cores=2,
    memory_bytes=2 * 1024**3,
    gpu_devices=0,
    wall_time_seconds=600,
    source_scan_bytes=256 * 1024**2,
    output_bytes=256 * 1024**2,
)
_PERMISSIONS = tuple(
    sorted(
        (
            CapabilityPermission.READ_DEVELOPMENT,
            CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_OUTCOME_VISIBLE,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        )
    )
)


INTERVAL_PROPERTY_COMPARISON_MANIFEST = CapabilityManifest(
    capability_key=INTERVAL_PROPERTY_COMPARISON_METHOD_KEY,
    capability_version=INTERVAL_PROPERTY_COMPARISON_METHOD_VERSION,
    kind=CapabilityKind.TRANSPORT_TESTER,
    config_schema=IntervalPropertyComparisonMethodSpec.SCHEMA,
    config_schema_sha256=sha256(IntervalPropertyComparisonMethodSpec.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(IntervalPropertyComparisonOperands.SCHEMA,),
    output_schema_ids=(IntervalPropertyComparisonResult.SCHEMA,),
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id='cpython-3.11-interval-property-comparison',
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "eight-kind-method-owned-falsifiers",
        "no-caller-preservation-verdict",
        "source-target-face-identity",
    ),
    implementation_sha256=INTERVAL_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256,
)
TRANSFORMED_PROPERTY_COMPARISON_MANIFEST = CapabilityManifest(
    capability_key=TRANSFORMED_PROPERTY_COMPARISON_METHOD_KEY,
    capability_version=TRANSFORMED_PROPERTY_COMPARISON_METHOD_VERSION,
    kind=CapabilityKind.TRANSPORT_TESTER,
    config_schema=TransformedPropertyComparisonMethodSpec.SCHEMA,
    config_schema_sha256=sha256(TransformedPropertyComparisonMethodSpec.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(TransformedPropertyComparisonOperands.SCHEMA,),
    output_schema_ids=(TransformedPropertyComparisonResult.SCHEMA,),
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id='cpython-3.11-transformed-property-comparison',
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=tuple(
        sorted(
            (
                "eight-distinct-kind-local-algorithms",
                "typed-unit-frame-direction-map-applied",
                "boundary-uncertainty-and-falsifier-owned",
                "no-caller-preservation-verdict",
            )
        )
    ),
    implementation_sha256=TRANSFORMED_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256,
)

_PROSPECTIVE_STRUCTURAL_RECURRENCE_INPUT_SCHEMAS = tuple(
    sorted(
        (
            StructuralBootstrapInputCensus.SCHEMA,
            ProspectiveStructuralRecurrencePlan.SCHEMA,
            ProspectiveStructuralRecurrenceRosterIssue.SCHEMA,
            StructuralRecurrenceMetricDynamicalForecast.SCHEMA,
            StructuralRecurrenceStageEvidence.SCHEMA,
            IntervalPropertyComparisonResult.SCHEMA,
            StructuralObservation.SCHEMA,
            StructuralPredictionInput.SCHEMA,
        )
    )
)
_PROSPECTIVE_STRUCTURAL_RECURRENCE_OUTPUT_SCHEMAS = tuple(
    sorted(
        (
            ProspectiveStructuralRecurrenceAdjudication.SCHEMA,
            ProspectiveStructuralRecurrenceFaceTerminal.SCHEMA,
            ProspectiveStructuralRecurrenceRosterIssue.SCHEMA,
            ProspectiveStructuralRecurrenceTargetObservation.SCHEMA,
            ProspectiveStructuralRecurrenceTargetTerminal.SCHEMA,
        )
    )
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST = CapabilityManifest(
    capability_key=PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_KEY,
    capability_version=PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_VERSION,
    kind=CapabilityKind.HYPOTHESIS_ADJUDICATOR,
    config_schema=ProspectiveStructuralRecurrenceMethodSpec.SCHEMA,
    config_schema_sha256=sha256(ProspectiveStructuralRecurrenceMethodSpec.SCHEMA.encode()).hexdigest(),
    input_schema_ids=_PROSPECTIVE_STRUCTURAL_RECURRENCE_INPUT_SCHEMAS,
    output_schema_ids=_PROSPECTIVE_STRUCTURAL_RECURRENCE_OUTPUT_SCHEMAS,
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id='cpython-3.11-structural-recurrence-prospective',
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "arbitrary-target-roster",
        'facewise-measurement-through-law-qualification',
        "no-cross-target-pooling",
        "prospective-issue-before-target-outcomes",
    ),
    implementation_sha256=PROSPECTIVE_STRUCTURAL_RECURRENCE_IMPLEMENTATION_SHA256,
)


STRUCTURAL_DEVELOPMENT_BRIDGE_KEY = "method.structural-development-bridge"
STRUCTURAL_RECURRENCE_TRANSPORT_KEY = 'method.structural-recurrence-transport'
STRUCTURAL_TARGET_BRIDGE_KEY = "method.structural-target-bridge"
STRUCTURAL_REPORTER_KEY = "method.structural-reporter"
STRUCTURAL_CAMPAIGN_IMPLEMENTATION_SHA256 = sha256(
    b"empirical-lawhood/backbone-structural-transport-campaign"
).hexdigest()

STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST = CapabilityManifest(
    capability_key=STRUCTURAL_DEVELOPMENT_BRIDGE_KEY,
    capability_version="1.0.0",
    kind=CapabilityKind.ANALYSIS,
    config_schema=StructuralDevelopmentBridgeConfig.SCHEMA,
    config_schema_sha256=sha256(StructuralDevelopmentBridgeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(StructuralDevelopmentInputs.SCHEMA,),
    output_schema_ids=tuple(
        sorted(
            (
                StructuralBootstrapInputCensus.SCHEMA,
                ProspectiveStructuralRecurrencePlan.SCHEMA,
                StructuralRecurrenceStageEvidence.SCHEMA,
                StructuralPredictionInput.SCHEMA,
            )
        )
    ),
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="cpython-3.11-structural-development-bridge",
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "authenticated-development-inputs",
        "development-products-only",
        "zero-target-outcome-access",
    ),
    implementation_sha256=STRUCTURAL_CAMPAIGN_IMPLEMENTATION_SHA256,
)

_STRUCTURAL_RECURRENCE_TRANSPORT_INPUT_SCHEMAS = tuple(
    sorted(
        (
            StructuralBootstrapInputCensus.SCHEMA,
            ResponseStageTerminal.SCHEMA,
            ResponseLaw.SCHEMA,
            ProspectiveStructuralRecurrenceMethodSpec.SCHEMA,
            ProspectiveStructuralRecurrencePlan.SCHEMA,
            StructuralRecurrenceFrozenLawTransportForecasts.SCHEMA,
            ProspectiveStructuralRecurrenceRosterIssue.SCHEMA,
            StructuralRecurrenceStageEvidence.SCHEMA,
            IntervalPropertyComparisonResult.SCHEMA,
            StructuralObservation.SCHEMA,
            StructuralPredictionInput.SCHEMA,
        )
    )
)
_STRUCTURAL_RECURRENCE_TRANSPORT_OUTPUT_SCHEMAS = tuple(
    sorted((*_PROSPECTIVE_STRUCTURAL_RECURRENCE_OUTPUT_SCHEMAS, StructuralPredictionFreezeReceipt.SCHEMA))
)
STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST = CapabilityManifest(
    capability_key=STRUCTURAL_RECURRENCE_TRANSPORT_KEY,
    capability_version="1.0.0",
    kind=CapabilityKind.HYPOTHESIS_ADJUDICATOR,
    config_schema=StructuralRecurrenceTransportConfig.SCHEMA,
    config_schema_sha256=sha256(StructuralRecurrenceTransportConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=_STRUCTURAL_RECURRENCE_TRANSPORT_INPUT_SCHEMAS,
    output_schema_ids=_STRUCTURAL_RECURRENCE_TRANSPORT_OUTPUT_SCHEMAS,
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id='cpython-3.11-structural-recurrence-transport',
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "complete-five-parent-law-transport",
        'facewise-structural-recurrence-adjudication',
        "no-cross-target-pooling",
        "prediction-freeze-before-target",
    ),
    implementation_sha256=STRUCTURAL_CAMPAIGN_IMPLEMENTATION_SHA256,
)

STRUCTURAL_TARGET_BRIDGE_MANIFEST = CapabilityManifest(
    capability_key=STRUCTURAL_TARGET_BRIDGE_KEY,
    capability_version="1.0.0",
    kind=CapabilityKind.EVALUATOR,
    config_schema=StructuralTargetBridgeConfig.SCHEMA,
    config_schema_sha256=sha256(StructuralTargetBridgeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(StructuralPredictionFreezeReceipt.SCHEMA,),
    output_schema_ids=tuple(
        sorted(
            (
                StructuralRecurrenceStageEvidence.SCHEMA,
                StructuralObservation.SCHEMA,
                IntervalPropertyComparisonOperands.SCHEMA,
            )
        )
    ),
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="cpython-3.11-structural-target-bridge",
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "eight-kind-typed-operands",
        "prediction-freeze-before-target-contact",
        "single-target-source-effect",
    ),
    implementation_sha256=STRUCTURAL_CAMPAIGN_IMPLEMENTATION_SHA256,
)

STRUCTURAL_REPORTER_MANIFEST = CapabilityManifest(
    capability_key=STRUCTURAL_REPORTER_KEY,
    capability_version="1.0.0",
    kind=CapabilityKind.REPORTER,
    config_schema=StructuralReporterConfig.SCHEMA,
    config_schema_sha256=sha256(StructuralReporterConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(ProspectiveStructuralRecurrenceAdjudication.SCHEMA,),
    output_schema_ids=(ScientificAdjudicationRecord.SCHEMA,),
    permissions=_PERMISSIONS,
    maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    resource_ceiling=_RESOURCE,
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="cpython-3.11-structural-reporter",
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=('sole-structural-recurrence-adjudication-input',),
    implementation_sha256=STRUCTURAL_CAMPAIGN_IMPLEMENTATION_SHA256,
)


def _metatheory_manifest(
    *,
    capability_key: str,
    kind: CapabilityKind,
    config_type: type[CanonicalRecord],
    input_schema_ids: tuple[str, ...],
    output_schema_ids: tuple[str, ...],
    maximum_outcome_access: OutcomeAccess,
    permissions: tuple[CapabilityPermission, ...],
) -> CapabilityManifest:
    return CapabilityManifest(
        capability_key=capability_key,
        capability_version=EXECUTABLE_METATHEORY_CONFORMANCE_VERSION,
        kind=kind,
        config_schema=config_type.SCHEMA,
        config_schema_sha256=sha256(config_type.SCHEMA.encode()).hexdigest(),
        input_schema_ids=tuple(sorted(input_schema_ids)),
        output_schema_ids=tuple(sorted(output_schema_ids)),
        permissions=permissions,
        maximum_evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        maximum_outcome_access=maximum_outcome_access,
        resource_ceiling=_RESOURCE,
        deterministic=True,
        seed_required=False,
        language_id="python",
        runtime_id=f"cpython-3.11-{capability_key}",
        requires_clean_commit=True,
        requires_active_mount=False,
        requires_network=False,
        conformance_check_ids=(
            "closed-stage-role-roster",
            "contract-conformance-ceiling-only",
            "freeze-authority-reveal-ordering",
            "plumbing-only-scientific-adjudication",
        ),
        implementation_sha256=(EXECUTABLE_METATHEORY_CONFORMANCE_IMPLEMENTATION_SHA256),
    )


def _metatheory_terminal_schemas(
    *roles: MetatheoryCampaignStageRole,
) -> tuple[str, ...]:
    return tuple(
        sorted(METATHEORY_CONFORMANCE_TERMINAL_TYPE_BY_ROLE[value].SCHEMA for value in roles)
    )


EXECUTABLE_METATHEORY_ACQUISITION_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_ACQUISITION_KEY,
    kind=CapabilityKind.SOURCE,
    config_type=MetatheoryConformanceAcquisitionConfig,
    input_schema_ids=(
        MetatheoryConformanceFixture.SCHEMA,
        *_metatheory_terminal_schemas(
            MetatheoryCampaignStageRole.PREDICTION_ISSUE,
        ),
    ),
    output_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.SOURCE_PIPELINE,
        MetatheoryCampaignStageRole.TARGET_ACQUISITION,
    ),
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_DEVELOPMENT_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_DEVELOPMENT_KEY,
    kind=CapabilityKind.ANALYSIS,
    config_type=MetatheoryConformanceDevelopmentConfig,
    input_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.SCIENTIFIC_SOURCE_QUALIFICATION,
        MetatheoryCampaignStageRole.REVEAL_AND_ADJUDICATION,
    ),
    output_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.COORDINATE_CONSTRUCTION,
        MetatheoryCampaignStageRole.OBSTRUCTION_CLOSEOUT,
    ),
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.READ_OUTCOME_VISIBLE,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_QUALIFICATION_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_QUALIFICATION_KEY,
    kind=CapabilityKind.NUMERICAL_QUALIFIER,
    config_type=MetatheoryConformanceQualificationConfig,
    input_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.SOURCE_PIPELINE,
        MetatheoryCampaignStageRole.COORDINATE_CONSTRUCTION,
        MetatheoryCampaignStageRole.COORDINATE_EVALUATION,
        MetatheoryCampaignStageRole.ATLAS_QUALIFICATION_OPTIONAL,
        MetatheoryCampaignStageRole.DECISION_ASSURANCE_OPTIONAL,
    ),
    output_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.SCIENTIFIC_SOURCE_QUALIFICATION,
        MetatheoryCampaignStageRole.COORDINATE_EVALUATION,
        MetatheoryCampaignStageRole.ATLAS_QUALIFICATION_OPTIONAL,
        MetatheoryCampaignStageRole.DECISION_ASSURANCE_OPTIONAL,
        MetatheoryCampaignStageRole.PROPERTY_SURVIVAL_OPTIONAL,
    ),
    maximum_outcome_access=OutcomeAccess.OUTCOME_BLIND,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_EVALUATOR_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_EVALUATOR_KEY,
    kind=CapabilityKind.EVALUATOR,
    config_type=MetatheoryConformanceEvaluatorConfig,
    input_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.TARGET_ACQUISITION,
    ),
    output_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.REVEAL_AND_ADJUDICATION,
    ),
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_PREDICTION_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_PREDICTION_KEY,
    kind=CapabilityKind.EVALUATOR,
    config_type=MetatheoryConformancePredictionConfig,
    input_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.PROPERTY_SURVIVAL_OPTIONAL,
    ),
    output_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.PREDICTION_ISSUE,
    ),
    maximum_outcome_access=OutcomeAccess.OUTCOME_BLIND,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_REPORTER_MANIFEST = _metatheory_manifest(
    capability_key=EXECUTABLE_METATHEORY_REPORTER_KEY,
    kind=CapabilityKind.REPORTER,
    config_type=MetatheoryConformanceReporterConfig,
    input_schema_ids=_metatheory_terminal_schemas(
        MetatheoryCampaignStageRole.OBSTRUCTION_CLOSEOUT,
    ),
    output_schema_ids=(ScientificAdjudicationRecord.SCHEMA,),
    maximum_outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.READ_OUTCOME_VISIBLE,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
)
EXECUTABLE_METATHEORY_CONFORMANCE_MANIFESTS = tuple(
    sorted(
        (
            EXECUTABLE_METATHEORY_ACQUISITION_MANIFEST,
            EXECUTABLE_METATHEORY_DEVELOPMENT_MANIFEST,
            EXECUTABLE_METATHEORY_EVALUATOR_MANIFEST,
            EXECUTABLE_METATHEORY_PREDICTION_MANIFEST,
            EXECUTABLE_METATHEORY_QUALIFICATION_MANIFEST,
            EXECUTABLE_METATHEORY_REPORTER_MANIFEST,
        ),
        key=lambda value: value.registry_id,
    )
)


INTERVAL_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=INTERVAL_PROPERTY_COMPARISON_MANIFEST,
    provider_key='structural-transport.interval-property-comparison-provider',
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
TRANSFORMED_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST,
    provider_key='structural-transport.transformed-property-comparison-provider',
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST,
    provider_key='structural-transport.structural-recurrence-prospective-provider',
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
STRUCTURAL_DEVELOPMENT_BRIDGE_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST,
    provider_key="structural-transport.development-bridge-provider",
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
STRUCTURAL_RECURRENCE_TRANSPORT_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST,
    provider_key='structural-transport.structural-recurrence-transport-provider',
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
STRUCTURAL_TARGET_BRIDGE_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=STRUCTURAL_TARGET_BRIDGE_MANIFEST,
    provider_key="structural-transport.target-bridge-provider",
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
STRUCTURAL_REPORTER_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=STRUCTURAL_REPORTER_MANIFEST,
    provider_key="structural-transport.reporter-provider",
    provider_version="1.0.0",
    config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
    maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
)
EXECUTABLE_METATHEORY_CONFORMANCE_CANDIDATE_REGISTRATIONS = tuple(
    CandidateCapabilityRegistration(
        manifest=value,
        provider_key=f"structural-transport.{value.capability_key}-provider",
        provider_version="1.0.0",
        config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
        maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
    )
    for value in EXECUTABLE_METATHEORY_CONFORMANCE_MANIFESTS
)

STRUCTURAL_FACE_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    registration_id="profile-registration.structural-face-handoff",
    profile_key="structural-face-handoff",
    profile_version="1.0.0",
    kind=ExtensionProfileKind.OBJECTIVE_TERMINAL,
    profile_schema=StructuralFaceHandoffProfile.SCHEMA,
    profile_schema_sha256=sha256(StructuralFaceHandoffProfile.SCHEMA.encode()).hexdigest(),
    implementation_sha256=STRUCTURAL_TRANSPORT_PROVIDER_IMPLEMENTATION_SHA256,
)
EXECUTABLE_METATHEORY_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    registration_id="profile-registration.executable-metatheory-campaign",
    profile_key="executable-metatheory-campaign",
    profile_version="1.0.0",
    kind=ExtensionProfileKind.LINKED_CAMPAIGN,
    profile_schema=MetatheoryCampaignProfile.SCHEMA,
    profile_schema_sha256=sha256(MetatheoryCampaignProfile.SCHEMA.encode()).hexdigest(),
    implementation_sha256=STRUCTURAL_TRANSPORT_PROVIDER_IMPLEMENTATION_SHA256,
)


def _component(
    *,
    registration_id: str,
    component_key: str,
    kind: ExtensionComponentKind,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    component_version: str = "1.0.0",
    implementation_sha256: str = STRUCTURAL_TRANSPORT_PROVIDER_IMPLEMENTATION_SHA256,
) -> ExtensionComponentRegistration:
    return ExtensionComponentRegistration(
        registration_id=registration_id,
        component_key=component_key,
        component_version=component_version,
        kind=kind,
        input_schema_ids=tuple(sorted(inputs)),
        output_schema_ids=tuple(sorted(outputs)),
        implementation_sha256=implementation_sha256,
    )


INTERVAL_PROPERTY_COMPARISON_METHOD = ExtensionComponentRegistration(
    registration_id="component.interval-property-comparison",
    component_key=INTERVAL_PROPERTY_COMPARISON_METHOD_KEY,
    component_version=INTERVAL_PROPERTY_COMPARISON_METHOD_VERSION,
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=INTERVAL_PROPERTY_COMPARISON_MANIFEST.input_schema_ids,
    output_schema_ids=INTERVAL_PROPERTY_COMPARISON_MANIFEST.output_schema_ids,
    implementation_sha256=INTERVAL_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256,
)
INTERVAL_PROPERTY_COMPARISON_CONFIG_DECODER = _component(
    registration_id='component.interval-property-comparison-method-spec-decoder',
    component_key='interval-property-comparison-method-spec-decoder',
    kind=ExtensionComponentKind.CONFIG_DECODER,
    inputs=(IntervalPropertyComparisonMethodSpec.SCHEMA,),
    outputs=(IntervalPropertyComparisonMethodSpec.SCHEMA,),
)
INTERVAL_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR = _component(
    registration_id='component.interval-property-comparison-result-validator',
    component_key='interval-property-comparison-result-validator',
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    inputs=(IntervalPropertyComparisonResult.SCHEMA,),
    outputs=('empirical-lawhood/runtime/artifact-generic-validation',),
)
INTERVAL_PROPERTY_COMPARISON_RUNTIME_PROVIDER = _component(
    registration_id='component.interval-property-comparison-runtime-provider',
    component_key=INTERVAL_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION.provider_key,
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    inputs=INTERVAL_PROPERTY_COMPARISON_MANIFEST.input_schema_ids,
    outputs=INTERVAL_PROPERTY_COMPARISON_MANIFEST.output_schema_ids,
)
TRANSFORMED_PROPERTY_COMPARISON_METHOD = ExtensionComponentRegistration(
    registration_id="component.transformed-property-comparison",
    component_key=TRANSFORMED_PROPERTY_COMPARISON_METHOD_KEY,
    component_version=TRANSFORMED_PROPERTY_COMPARISON_METHOD_VERSION,
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST.input_schema_ids,
    output_schema_ids=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST.output_schema_ids,
    implementation_sha256=TRANSFORMED_PROPERTY_COMPARISON_IMPLEMENTATION_SHA256,
)
TRANSFORMED_PROPERTY_COMPARISON_CONFIG_DECODER = _component(
    registration_id='component.transformed-property-comparison-method-spec-decoder',
    component_key='transformed-property-comparison-method-spec-decoder',
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    inputs=(TransformedPropertyComparisonMethodSpec.SCHEMA,),
    outputs=(TransformedPropertyComparisonMethodSpec.SCHEMA,),
)
TRANSFORMED_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR = _component(
    registration_id='component.transformed-property-comparison-result-validator',
    component_key='transformed-property-comparison-result-validator',
    component_version="1.0.0",
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    inputs=(TransformedPropertyComparisonResult.SCHEMA,),
    outputs=('empirical-lawhood/runtime/artifact-generic-validation',),
)
TRANSFORMED_PROPERTY_COMPARISON_RUNTIME_PROVIDER = _component(
    registration_id='component.transformed-property-comparison-runtime-provider',
    component_key=TRANSFORMED_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION.provider_key,
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    inputs=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST.input_schema_ids,
    outputs=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST.output_schema_ids,
)

PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD = ExtensionComponentRegistration(
    registration_id='component.structural-recurrence-prospective-method',
    component_key=PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_KEY,
    component_version=PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD_VERSION,
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST.input_schema_ids,
    output_schema_ids=PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST.output_schema_ids,
    implementation_sha256=PROSPECTIVE_STRUCTURAL_RECURRENCE_IMPLEMENTATION_SHA256,
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_CONFIG_DECODER = _component(
    registration_id='component.structural-recurrence-prospective-method-spec-decoder',
    component_key='structural-recurrence-prospective-method-spec-decoder',
    kind=ExtensionComponentKind.CONFIG_DECODER,
    inputs=(ProspectiveStructuralRecurrenceMethodSpec.SCHEMA,),
    outputs=(ProspectiveStructuralRecurrenceMethodSpec.SCHEMA,),
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_ARTIFACT_VALIDATOR = _component(
    registration_id='component.structural-recurrence-prospective-artifact-validator',
    component_key='structural-recurrence-prospective-artifact-validator',
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    inputs=_PROSPECTIVE_STRUCTURAL_RECURRENCE_OUTPUT_SCHEMAS,
    outputs=('empirical-lawhood/runtime/artifact-generic-validation',),
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_RUNTIME_PROVIDER = _component(
    registration_id='component.structural-recurrence-prospective-runtime-provider',
    component_key=PROSPECTIVE_STRUCTURAL_RECURRENCE_CANDIDATE_REGISTRATION.provider_key,
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    inputs=_PROSPECTIVE_STRUCTURAL_RECURRENCE_INPUT_SCHEMAS,
    outputs=_PROSPECTIVE_STRUCTURAL_RECURRENCE_OUTPUT_SCHEMAS,
)


def _campaign_components(
    *,
    token: str,
    manifest: CapabilityManifest,
    candidate: CandidateCapabilityRegistration,
) -> tuple[
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
]:
    method = _component(
        registration_id=f"component.{token}-method",
        component_key=manifest.capability_key,
        kind=ExtensionComponentKind.METHOD,
        inputs=manifest.input_schema_ids,
        outputs=manifest.output_schema_ids,
        implementation_sha256=manifest.implementation_sha256,
    )
    decoder = _component(
        registration_id=f"component.{token}-config-decoder",
        component_key=f"{token}-config-decoder",
        kind=ExtensionComponentKind.CONFIG_DECODER,
        inputs=(manifest.config_schema,),
        outputs=(manifest.config_schema,),
    )
    validator = _component(
        registration_id=f"component.{token}-artifact-validator",
        component_key=f"{token}-artifact-validator",
        kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
        inputs=manifest.output_schema_ids,
        outputs=('empirical-lawhood/runtime/artifact-generic-validation',),
    )
    provider = _component(
        registration_id=f"component.{token}-runtime-provider",
        component_key=candidate.provider_key,
        kind=ExtensionComponentKind.RUNTIME_PROVIDER,
        inputs=manifest.input_schema_ids,
        outputs=manifest.output_schema_ids,
    )
    return method, decoder, validator, provider


(
    STRUCTURAL_DEVELOPMENT_BRIDGE_METHOD,
    STRUCTURAL_DEVELOPMENT_BRIDGE_CONFIG_DECODER,
    STRUCTURAL_DEVELOPMENT_BRIDGE_ARTIFACT_VALIDATOR,
    STRUCTURAL_DEVELOPMENT_BRIDGE_RUNTIME_PROVIDER,
) = _campaign_components(
    token="structural-development-bridge",
    manifest=STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST,
    candidate=STRUCTURAL_DEVELOPMENT_BRIDGE_CANDIDATE_REGISTRATION,
)
(
    STRUCTURAL_RECURRENCE_TRANSPORT_METHOD,
    STRUCTURAL_RECURRENCE_TRANSPORT_CONFIG_DECODER,
    STRUCTURAL_RECURRENCE_TRANSPORT_ARTIFACT_VALIDATOR,
    STRUCTURAL_RECURRENCE_TRANSPORT_RUNTIME_PROVIDER,
) = _campaign_components(
    token='structural-recurrence-transport',
    manifest=STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST,
    candidate=STRUCTURAL_RECURRENCE_TRANSPORT_CANDIDATE_REGISTRATION,
)
(
    STRUCTURAL_TARGET_BRIDGE_METHOD,
    STRUCTURAL_TARGET_BRIDGE_CONFIG_DECODER,
    STRUCTURAL_TARGET_BRIDGE_ARTIFACT_VALIDATOR,
    STRUCTURAL_TARGET_BRIDGE_RUNTIME_PROVIDER,
) = _campaign_components(
    token="structural-target-bridge",
    manifest=STRUCTURAL_TARGET_BRIDGE_MANIFEST,
    candidate=STRUCTURAL_TARGET_BRIDGE_CANDIDATE_REGISTRATION,
)
(
    STRUCTURAL_REPORTER_METHOD,
    STRUCTURAL_REPORTER_CONFIG_DECODER,
    STRUCTURAL_REPORTER_ARTIFACT_VALIDATOR,
    STRUCTURAL_REPORTER_RUNTIME_PROVIDER,
) = _campaign_components(
    token="structural-reporter",
    manifest=STRUCTURAL_REPORTER_MANIFEST,
    candidate=STRUCTURAL_REPORTER_CANDIDATE_REGISTRATION,
)


def _metatheory_components(
    token: str,
    manifest: CapabilityManifest,
) -> tuple[
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
    ExtensionComponentRegistration,
]:
    candidate = next(
        value
        for value in EXECUTABLE_METATHEORY_CONFORMANCE_CANDIDATE_REGISTRATIONS
        if value.manifest == manifest
    )
    return _campaign_components(token=token, manifest=manifest, candidate=candidate)


(
    EXECUTABLE_METATHEORY_ACQUISITION_METHOD,
    EXECUTABLE_METATHEORY_ACQUISITION_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_ACQUISITION_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_ACQUISITION_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-acquisition",
    EXECUTABLE_METATHEORY_ACQUISITION_MANIFEST,
)
(
    EXECUTABLE_METATHEORY_DEVELOPMENT_METHOD,
    EXECUTABLE_METATHEORY_DEVELOPMENT_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_DEVELOPMENT_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_DEVELOPMENT_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-development",
    EXECUTABLE_METATHEORY_DEVELOPMENT_MANIFEST,
)
(
    EXECUTABLE_METATHEORY_EVALUATOR_METHOD,
    EXECUTABLE_METATHEORY_EVALUATOR_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_EVALUATOR_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_EVALUATOR_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-evaluator",
    EXECUTABLE_METATHEORY_EVALUATOR_MANIFEST,
)
(
    EXECUTABLE_METATHEORY_PREDICTION_METHOD,
    EXECUTABLE_METATHEORY_PREDICTION_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_PREDICTION_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_PREDICTION_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-prediction",
    EXECUTABLE_METATHEORY_PREDICTION_MANIFEST,
)
(
    EXECUTABLE_METATHEORY_QUALIFICATION_METHOD,
    EXECUTABLE_METATHEORY_QUALIFICATION_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_QUALIFICATION_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_QUALIFICATION_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-qualification",
    EXECUTABLE_METATHEORY_QUALIFICATION_MANIFEST,
)
(
    EXECUTABLE_METATHEORY_REPORTER_METHOD,
    EXECUTABLE_METATHEORY_REPORTER_CONFIG_DECODER,
    EXECUTABLE_METATHEORY_REPORTER_ARTIFACT_VALIDATOR,
    EXECUTABLE_METATHEORY_REPORTER_RUNTIME_PROVIDER,
) = _metatheory_components(
    "executable-metatheory-reporter",
    EXECUTABLE_METATHEORY_REPORTER_MANIFEST,
)
EXECUTABLE_METATHEORY_CONFORMANCE_COMPONENTS = tuple(
    value
    for group in (
        (
            EXECUTABLE_METATHEORY_ACQUISITION_METHOD,
            EXECUTABLE_METATHEORY_ACQUISITION_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_ACQUISITION_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_ACQUISITION_RUNTIME_PROVIDER,
        ),
        (
            EXECUTABLE_METATHEORY_DEVELOPMENT_METHOD,
            EXECUTABLE_METATHEORY_DEVELOPMENT_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_DEVELOPMENT_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_DEVELOPMENT_RUNTIME_PROVIDER,
        ),
        (
            EXECUTABLE_METATHEORY_EVALUATOR_METHOD,
            EXECUTABLE_METATHEORY_EVALUATOR_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_EVALUATOR_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_EVALUATOR_RUNTIME_PROVIDER,
        ),
        (
            EXECUTABLE_METATHEORY_PREDICTION_METHOD,
            EXECUTABLE_METATHEORY_PREDICTION_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_PREDICTION_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_PREDICTION_RUNTIME_PROVIDER,
        ),
        (
            EXECUTABLE_METATHEORY_QUALIFICATION_METHOD,
            EXECUTABLE_METATHEORY_QUALIFICATION_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_QUALIFICATION_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_QUALIFICATION_RUNTIME_PROVIDER,
        ),
        (
            EXECUTABLE_METATHEORY_REPORTER_METHOD,
            EXECUTABLE_METATHEORY_REPORTER_CONFIG_DECODER,
            EXECUTABLE_METATHEORY_REPORTER_ARTIFACT_VALIDATOR,
            EXECUTABLE_METATHEORY_REPORTER_RUNTIME_PROVIDER,
        ),
    )
    for value in group
)

SOURCE_FREE_PROPERTY_TRANSPORT_MANIFESTS = source_free_property_transport_capability_registry().capabilities
SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_REGISTRATIONS = tuple(
    CandidateCapabilityRegistration(
        manifest=manifest,
        provider_key=f"structural-transport.{manifest.capability_key}-provider",
        provider_version="1.0.0",
        config_media_type=STRUCTURAL_TRANSPORT_MEDIA_TYPE,
        maximum_config_bytes=_MAXIMUM_CONFIG_BYTES,
    )
    for manifest in SOURCE_FREE_PROPERTY_TRANSPORT_MANIFESTS
)
_SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_BY_ID = {
    value.manifest.registry_id: value for value in SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_REGISTRATIONS
}
SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_COMPONENTS = tuple(
    (
        role,
        manifest,
        SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPE_BY_ROLE[role],
        *_campaign_components(
            token=f"source-free-property-transport-{role.value.lower().replace('_', '-')}",
            manifest=manifest,
            candidate=_SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_BY_ID[manifest.registry_id],
        ),
    )
    for role in MetatheoryCampaignStageRole
    if role in SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPE_BY_ROLE
    for manifest in (
        next(
            value
            for value in SOURCE_FREE_PROPERTY_TRANSPORT_MANIFESTS
            if value.config_schema == SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPE_BY_ROLE[role].SCHEMA
        ),
    )
)
SOURCE_FREE_PROPERTY_TRANSPORT_COMPONENTS = tuple(
    component
    for _, _, _, method, decoder, validator, provider in SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_COMPONENTS
    for component in (method, decoder, validator, provider)
)

_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.structural-transport",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.METHOD,
    evidence_profile_registries=(),
    capability_manifests=tuple(
        sorted(
            (
                INTERVAL_PROPERTY_COMPARISON_MANIFEST,
                TRANSFORMED_PROPERTY_COMPARISON_MANIFEST,
                *EXECUTABLE_METATHEORY_CONFORMANCE_MANIFESTS,
                *SOURCE_FREE_PROPERTY_TRANSPORT_MANIFESTS,
                PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST,
                STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST,
                STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST,
                STRUCTURAL_REPORTER_MANIFEST,
                STRUCTURAL_TARGET_BRIDGE_MANIFEST,
            ),
            key=lambda value: value.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                INTERVAL_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION,
                TRANSFORMED_PROPERTY_COMPARISON_CANDIDATE_REGISTRATION,
                *EXECUTABLE_METATHEORY_CONFORMANCE_CANDIDATE_REGISTRATIONS,
                *SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_REGISTRATIONS,
                PROSPECTIVE_STRUCTURAL_RECURRENCE_CANDIDATE_REGISTRATION,
                STRUCTURAL_DEVELOPMENT_BRIDGE_CANDIDATE_REGISTRATION,
                STRUCTURAL_RECURRENCE_TRANSPORT_CANDIDATE_REGISTRATION,
                STRUCTURAL_REPORTER_CANDIDATE_REGISTRATION,
                STRUCTURAL_TARGET_BRIDGE_CANDIDATE_REGISTRATION,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    dataset_capability_registries=(),
    profile_registrations=tuple(
        sorted(
            (
                EXECUTABLE_METATHEORY_PROFILE_REGISTRATION,
                STRUCTURAL_FACE_PROFILE_REGISTRATION,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    method_registrations=tuple(
        sorted(
            (
                ObjectIdentity.from_record(
                    INTERVAL_PROPERTY_COMPARISON_METHOD.registration_id,
                    INTERVAL_PROPERTY_COMPARISON_METHOD,
                ),
                ObjectIdentity.from_record(
                    TRANSFORMED_PROPERTY_COMPARISON_METHOD.registration_id,
                    TRANSFORMED_PROPERTY_COMPARISON_METHOD,
                ),
                *(
                    ObjectIdentity.from_record(value.registration_id, value)
                    for value in EXECUTABLE_METATHEORY_CONFORMANCE_COMPONENTS
                    if value.kind is ExtensionComponentKind.METHOD
                ),
                *(
                    ObjectIdentity.from_record(value.registration_id, value)
                    for value in SOURCE_FREE_PROPERTY_TRANSPORT_COMPONENTS
                    if value.kind is ExtensionComponentKind.METHOD
                ),
                ObjectIdentity.from_record(
                    PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD.registration_id,
                    PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD,
                ),
                *(
                    ObjectIdentity.from_record(value.registration_id, value)
                    for value in (
                        STRUCTURAL_DEVELOPMENT_BRIDGE_METHOD,
                        STRUCTURAL_RECURRENCE_TRANSPORT_METHOD,
                        STRUCTURAL_REPORTER_METHOD,
                        STRUCTURAL_TARGET_BRIDGE_METHOD,
                    )
                ),
            ),
            key=lambda value: value.object_id,
        )
    ),
    config_decoders=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in sorted(
            (
                INTERVAL_PROPERTY_COMPARISON_CONFIG_DECODER,
                TRANSFORMED_PROPERTY_COMPARISON_CONFIG_DECODER,
                *(
                    value
                    for value in EXECUTABLE_METATHEORY_CONFORMANCE_COMPONENTS
                    if value.kind is ExtensionComponentKind.CONFIG_DECODER
                ),
                *(
                    value
                    for value in SOURCE_FREE_PROPERTY_TRANSPORT_COMPONENTS
                    if value.kind is ExtensionComponentKind.CONFIG_DECODER
                ),
                PROSPECTIVE_STRUCTURAL_RECURRENCE_CONFIG_DECODER,
                STRUCTURAL_DEVELOPMENT_BRIDGE_CONFIG_DECODER,
                STRUCTURAL_RECURRENCE_TRANSPORT_CONFIG_DECODER,
                STRUCTURAL_REPORTER_CONFIG_DECODER,
                STRUCTURAL_TARGET_BRIDGE_CONFIG_DECODER,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    artifact_validators=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in sorted(
            (
                INTERVAL_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR,
                TRANSFORMED_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR,
                *(
                    value
                    for value in EXECUTABLE_METATHEORY_CONFORMANCE_COMPONENTS
                    if value.kind is ExtensionComponentKind.ARTIFACT_VALIDATOR
                ),
                *(
                    value
                    for value in SOURCE_FREE_PROPERTY_TRANSPORT_COMPONENTS
                    if value.kind is ExtensionComponentKind.ARTIFACT_VALIDATOR
                ),
                PROSPECTIVE_STRUCTURAL_RECURRENCE_ARTIFACT_VALIDATOR,
                STRUCTURAL_DEVELOPMENT_BRIDGE_ARTIFACT_VALIDATOR,
                STRUCTURAL_RECURRENCE_TRANSPORT_ARTIFACT_VALIDATOR,
                STRUCTURAL_REPORTER_ARTIFACT_VALIDATOR,
                STRUCTURAL_TARGET_BRIDGE_ARTIFACT_VALIDATOR,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    runtime_providers=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in sorted(
            (
                INTERVAL_PROPERTY_COMPARISON_RUNTIME_PROVIDER,
                TRANSFORMED_PROPERTY_COMPARISON_RUNTIME_PROVIDER,
                *(
                    value
                    for value in EXECUTABLE_METATHEORY_CONFORMANCE_COMPONENTS
                    if value.kind is ExtensionComponentKind.RUNTIME_PROVIDER
                ),
                *(
                    value
                    for value in SOURCE_FREE_PROPERTY_TRANSPORT_COMPONENTS
                    if value.kind is ExtensionComponentKind.RUNTIME_PROVIDER
                ),
                PROSPECTIVE_STRUCTURAL_RECURRENCE_RUNTIME_PROVIDER,
                STRUCTURAL_DEVELOPMENT_BRIDGE_RUNTIME_PROVIDER,
                STRUCTURAL_RECURRENCE_TRANSPORT_RUNTIME_PROVIDER,
                STRUCTURAL_REPORTER_RUNTIME_PROVIDER,
                STRUCTURAL_TARGET_BRIDGE_RUNTIME_PROVIDER,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
from hashlib import sha256

from empirical_lawhood.methods.prospective_structural_recurrence import StructuralRecurrenceFrozenLawTransportForecasts, ProspectiveStructuralRecurrenceMethodSpec, ProspectiveStructuralRecurrencePlan
from empirical_lawhood.methods.interval_property_comparison import IntervalPropertyComparisonMethodSpec
from empirical_lawhood.methods.transformed_property_comparison import TransformedPropertyComparisonMethodSpec
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.metatheory_campaign import MetatheoryCampaignStageRole
from empirical_lawhood.execution.capabilities import CapabilityManifest, CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.extension_bundles import ExtensionComponentRegistration
from empirical_lawhood.execution.conditional_children import FrozenParentInputBinding
from empirical_lawhood.execution.law_transport_handoff import AuthenticatedLawTransportHandoff, authenticate_law_transport_handoff
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.providers import CampaignRuntimeProvider

from empirical_lawhood.methods.backbone_structural_transport.campaign import STRUCTURAL_TARGET_SOURCE_PORT_KEY, StructuralDevelopmentBridgeConfig, StructuralDevelopmentInputs, StructuralRecurrenceTransportConfig, StructuralReporterConfig, StructuralTargetBridgeConfig
from empirical_lawhood.methods.backbone_structural_transport.metatheory_conformance import METATHEORY_CONFORMANCE_EXECUTABLE_CONFIG_TYPES, MetatheoryConformanceAcquisitionConfig, MetatheoryConformanceDevelopmentConfig, MetatheoryConformanceEvaluatorConfig, MetatheoryConformancePredictionConfig, MetatheoryConformanceQualificationConfig, MetatheoryConformanceReporterConfig
from empirical_lawhood.methods.backbone_structural_transport.source_free_property_transport_records import SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPES

from empirical_lawhood.methods.backbone_structural_transport.metatheory_provider import metatheory_conformance_provider
from empirical_lawhood.methods.backbone_structural_transport.source_free_property_transport_provider import source_free_property_transport_provider


_MAXIMUM_CONFIG_BYTES = 4 * 1024 * 1024


def _decoder(
    component: object,
    record_type: type[CanonicalRecord],
    registration_id: str,
) -> StudyExtensionDecoderRegistration:
    decoder_key = getattr(component, "component_key")
    decoder_version = getattr(component, "component_version")
    implementation_sha256 = getattr(component, "implementation_sha256")
    return StudyExtensionDecoderRegistration(
        registration_id=registration_id,
        decoder_key=decoder_key,
        decoder_version=decoder_version,
        payload_schema=record_type.SCHEMA,
        payload_version=record_type.VERSION,
        config_sha256=sha256(
            canonical_json_bytes(
                {
                    "decoder_key": decoder_key,
                    "decoder_version": decoder_version,
                    "mode": "exact-canonical-record",
                    "payload_schema": record_type.SCHEMA,
                }
            )
        ).hexdigest(),
        implementation_sha256=implementation_sha256,
        maximum_payload_bytes=_MAXIMUM_CONFIG_BYTES,
    )


INTERVAL_PROPERTY_COMPARISON_DECODER_REGISTRATION = _decoder(
    INTERVAL_PROPERTY_COMPARISON_CONFIG_DECODER,
    IntervalPropertyComparisonMethodSpec,
    'decoder-registration.property-comparison-method-spec',
)
TRANSFORMED_PROPERTY_COMPARISON_DECODER_REGISTRATION = _decoder(
    TRANSFORMED_PROPERTY_COMPARISON_CONFIG_DECODER,
    TransformedPropertyComparisonMethodSpec,
    "decoder-registration.transformed-property-comparison-method-spec",
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_DECODER_REGISTRATION = _decoder(
    PROSPECTIVE_STRUCTURAL_RECURRENCE_CONFIG_DECODER,
    ProspectiveStructuralRecurrenceMethodSpec,
    'decoder-registration.structural-recurrence-prospective-method-spec',
)
STRUCTURAL_DEVELOPMENT_BRIDGE_DECODER_REGISTRATION = _decoder(
    STRUCTURAL_DEVELOPMENT_BRIDGE_CONFIG_DECODER,
    StructuralDevelopmentBridgeConfig,
    "decoder-registration.structural-development-bridge-config",
)
STRUCTURAL_RECURRENCE_TRANSPORT_DECODER_REGISTRATION = _decoder(
    STRUCTURAL_RECURRENCE_TRANSPORT_CONFIG_DECODER,
    StructuralRecurrenceTransportConfig,
    'decoder-registration.structural-recurrence-transport-config',
)
STRUCTURAL_REPORTER_DECODER_REGISTRATION = _decoder(
    STRUCTURAL_REPORTER_CONFIG_DECODER,
    StructuralReporterConfig,
    "decoder-registration.structural-reporter-config",
)
STRUCTURAL_TARGET_BRIDGE_DECODER_REGISTRATION = _decoder(
    STRUCTURAL_TARGET_BRIDGE_CONFIG_DECODER,
    StructuralTargetBridgeConfig,
    "decoder-registration.structural-target-bridge-config",
)
EXECUTABLE_METATHEORY_ACQUISITION_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_ACQUISITION_CONFIG_DECODER,
    MetatheoryConformanceAcquisitionConfig,
    "decoder-registration.executable-metatheory-acquisition-config",
)
EXECUTABLE_METATHEORY_DEVELOPMENT_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_DEVELOPMENT_CONFIG_DECODER,
    MetatheoryConformanceDevelopmentConfig,
    "decoder-registration.executable-metatheory-development-config",
)
EXECUTABLE_METATHEORY_EVALUATOR_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_EVALUATOR_CONFIG_DECODER,
    MetatheoryConformanceEvaluatorConfig,
    "decoder-registration.executable-metatheory-evaluator-config",
)
EXECUTABLE_METATHEORY_PREDICTION_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_PREDICTION_CONFIG_DECODER,
    MetatheoryConformancePredictionConfig,
    "decoder-registration.executable-metatheory-prediction-config",
)
EXECUTABLE_METATHEORY_QUALIFICATION_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_QUALIFICATION_CONFIG_DECODER,
    MetatheoryConformanceQualificationConfig,
    "decoder-registration.executable-metatheory-qualification-config",
)
EXECUTABLE_METATHEORY_REPORTER_DECODER_REGISTRATION = _decoder(
    EXECUTABLE_METATHEORY_REPORTER_CONFIG_DECODER,
    MetatheoryConformanceReporterConfig,
    "decoder-registration.executable-metatheory-reporter-config",
)


def _binding(
    *,
    binding_id: str,
    manifest: CapabilityManifest,
    method: ExtensionComponentRegistration,
    decoder_component: ExtensionComponentRegistration,
    runtime_provider: ExtensionComponentRegistration,
    validator: ExtensionComponentRegistration,
    record_type: type[CanonicalRecord],
    decoder: StudyExtensionDecoderRegistration,
    authenticated_record_types: tuple[type[CanonicalRecord], ...] = (),
    required_platform_port_keys: tuple[str, ...] = (),
    capability_backed: bool = True,
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=manifest.capability_key,
        capability_version=manifest.capability_version,
        capability_implementation_sha256=manifest.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=runtime_provider.component_key,
        provider_version=runtime_provider.component_version,
        provider_implementation_sha256=runtime_provider.implementation_sha256,
        capability_backed=capability_backed,
        discovery_components=tuple(
            sorted(
                (method, decoder_component, runtime_provider, validator),
                key=lambda value: value.registration_id,
            )
        ),
        accepted_profile_types=(),
        accepted_config_types=tuple(
            sorted(
                (
                    ExecutableRecordTypeBinding(record_type.SCHEMA, record_type.VERSION),
                    *(
                        ExecutableRecordTypeBinding(value.SCHEMA, value.VERSION)
                        for value in authenticated_record_types
                    ),
                ),
                key=lambda value: value.type_id,
            )
        ),
        required_issued_payload_schemas=(record_type.SCHEMA,),
        codec_registration_identities=(
            ObjectIdentity.from_record(
                decoder_component.registration_id,
                decoder_component,
            ),
        ),
        issued_decoder_registrations=(decoder,),
        input_schema_ids=manifest.input_schema_ids,
        output_schema_ids=manifest.output_schema_ids,
        artifact_validator_identities=(
            ObjectIdentity.from_record(validator.registration_id, validator),
        ),
        required_platform_port_keys=required_platform_port_keys,
        may_require_active_mount=False,
        may_require_source_qualification=False,
        may_require_network=False,
        may_require_authority=True,
        required_authenticated_record_schemas=tuple(
            sorted(value.SCHEMA for value in authenticated_record_types)
        ),
    )


SOURCE_FREE_PROPERTY_TRANSPORT_DECODER_REGISTRATIONS = tuple(
    (
        role,
        _decoder(
            decoder_component,
            record_type,
            f"decoder-registration.source-free-property-transport-{role.value.lower().replace('_', '-')}",
        ),
    )
    for (
        role,
        _,
        record_type,
        _,
        decoder_component,
        _,
        _,
    ) in SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_COMPONENTS
)
_SOURCE_FREE_PROPERTY_TRANSPORT_DECODER_BY_ROLE = dict(SOURCE_FREE_PROPERTY_TRANSPORT_DECODER_REGISTRATIONS)
SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_BINDINGS = tuple(
    sorted(
        (
            _binding(
                binding_id=(f"binding.source-free-property-transport-{role.value.lower().replace('_', '-')}"),
                manifest=manifest,
                method=method,
                decoder_component=decoder_component,
                runtime_provider=runtime_provider,
                validator=validator,
                record_type=record_type,
                decoder=_SOURCE_FREE_PROPERTY_TRANSPORT_DECODER_BY_ROLE[role],
            )
            for (
                role,
                manifest,
                record_type,
                method,
                decoder_component,
                validator,
                runtime_provider,
            ) in SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_COMPONENTS
        ),
        key=lambda value: value.binding_id,
    )
)


INTERVAL_PROPERTY_COMPARISON_EXECUTABLE_BINDING = _binding(
    binding_id='binding.property-comparison-method',
    manifest=INTERVAL_PROPERTY_COMPARISON_MANIFEST,
    method=INTERVAL_PROPERTY_COMPARISON_METHOD,
    decoder_component=INTERVAL_PROPERTY_COMPARISON_CONFIG_DECODER,
    runtime_provider=INTERVAL_PROPERTY_COMPARISON_RUNTIME_PROVIDER,
    validator=INTERVAL_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR,
    record_type=IntervalPropertyComparisonMethodSpec,
    decoder=INTERVAL_PROPERTY_COMPARISON_DECODER_REGISTRATION,
)
TRANSFORMED_PROPERTY_COMPARISON_EXECUTABLE_BINDING = _binding(
    binding_id="binding.transformed-property-comparison-method",
    manifest=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST,
    method=TRANSFORMED_PROPERTY_COMPARISON_METHOD,
    decoder_component=TRANSFORMED_PROPERTY_COMPARISON_CONFIG_DECODER,
    runtime_provider=TRANSFORMED_PROPERTY_COMPARISON_RUNTIME_PROVIDER,
    validator=TRANSFORMED_PROPERTY_COMPARISON_ARTIFACT_VALIDATOR,
    record_type=TransformedPropertyComparisonMethodSpec,
    decoder=TRANSFORMED_PROPERTY_COMPARISON_DECODER_REGISTRATION,
)
PROSPECTIVE_STRUCTURAL_RECURRENCE_EXECUTABLE_BINDING = _binding(
    binding_id='binding.structural-recurrence-prospective-method',
    manifest=PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST,
    method=PROSPECTIVE_STRUCTURAL_RECURRENCE_METHOD,
    decoder_component=PROSPECTIVE_STRUCTURAL_RECURRENCE_CONFIG_DECODER,
    runtime_provider=PROSPECTIVE_STRUCTURAL_RECURRENCE_RUNTIME_PROVIDER,
    validator=PROSPECTIVE_STRUCTURAL_RECURRENCE_ARTIFACT_VALIDATOR,
    record_type=ProspectiveStructuralRecurrenceMethodSpec,
    decoder=PROSPECTIVE_STRUCTURAL_RECURRENCE_DECODER_REGISTRATION,
)
STRUCTURAL_DEVELOPMENT_BRIDGE_EXECUTABLE_BINDING = _binding(
    binding_id="binding.structural-development-bridge",
    manifest=STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST,
    method=STRUCTURAL_DEVELOPMENT_BRIDGE_METHOD,
    decoder_component=STRUCTURAL_DEVELOPMENT_BRIDGE_CONFIG_DECODER,
    runtime_provider=STRUCTURAL_DEVELOPMENT_BRIDGE_RUNTIME_PROVIDER,
    validator=STRUCTURAL_DEVELOPMENT_BRIDGE_ARTIFACT_VALIDATOR,
    record_type=StructuralDevelopmentBridgeConfig,
    decoder=STRUCTURAL_DEVELOPMENT_BRIDGE_DECODER_REGISTRATION,
    authenticated_record_types=(StructuralDevelopmentInputs,),
)
STRUCTURAL_RECURRENCE_TRANSPORT_EXECUTABLE_BINDING = _binding(
    binding_id='binding.structural-recurrence-transport',
    manifest=STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST,
    method=STRUCTURAL_RECURRENCE_TRANSPORT_METHOD,
    decoder_component=STRUCTURAL_RECURRENCE_TRANSPORT_CONFIG_DECODER,
    runtime_provider=STRUCTURAL_RECURRENCE_TRANSPORT_RUNTIME_PROVIDER,
    validator=STRUCTURAL_RECURRENCE_TRANSPORT_ARTIFACT_VALIDATOR,
    record_type=StructuralRecurrenceTransportConfig,
    decoder=STRUCTURAL_RECURRENCE_TRANSPORT_DECODER_REGISTRATION,
)
STRUCTURAL_REPORTER_EXECUTABLE_BINDING = _binding(
    binding_id="binding.structural-reporter",
    manifest=STRUCTURAL_REPORTER_MANIFEST,
    method=STRUCTURAL_REPORTER_METHOD,
    decoder_component=STRUCTURAL_REPORTER_CONFIG_DECODER,
    runtime_provider=STRUCTURAL_REPORTER_RUNTIME_PROVIDER,
    validator=STRUCTURAL_REPORTER_ARTIFACT_VALIDATOR,
    record_type=StructuralReporterConfig,
    decoder=STRUCTURAL_REPORTER_DECODER_REGISTRATION,
)
STRUCTURAL_TARGET_BRIDGE_EXECUTABLE_BINDING = _binding(
    binding_id="binding.structural-target-bridge",
    manifest=STRUCTURAL_TARGET_BRIDGE_MANIFEST,
    method=STRUCTURAL_TARGET_BRIDGE_METHOD,
    decoder_component=STRUCTURAL_TARGET_BRIDGE_CONFIG_DECODER,
    runtime_provider=STRUCTURAL_TARGET_BRIDGE_RUNTIME_PROVIDER,
    validator=STRUCTURAL_TARGET_BRIDGE_ARTIFACT_VALIDATOR,
    record_type=StructuralTargetBridgeConfig,
    decoder=STRUCTURAL_TARGET_BRIDGE_DECODER_REGISTRATION,
    required_platform_port_keys=(STRUCTURAL_TARGET_SOURCE_PORT_KEY,),
)
EXECUTABLE_METATHEORY_ACQUISITION_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-acquisition",
    manifest=EXECUTABLE_METATHEORY_ACQUISITION_MANIFEST,
    method=EXECUTABLE_METATHEORY_ACQUISITION_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_ACQUISITION_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_ACQUISITION_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_ACQUISITION_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformanceAcquisitionConfig,
    decoder=EXECUTABLE_METATHEORY_ACQUISITION_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_DEVELOPMENT_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-development",
    manifest=EXECUTABLE_METATHEORY_DEVELOPMENT_MANIFEST,
    method=EXECUTABLE_METATHEORY_DEVELOPMENT_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_DEVELOPMENT_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_DEVELOPMENT_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_DEVELOPMENT_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformanceDevelopmentConfig,
    decoder=EXECUTABLE_METATHEORY_DEVELOPMENT_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_EVALUATOR_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-evaluator",
    manifest=EXECUTABLE_METATHEORY_EVALUATOR_MANIFEST,
    method=EXECUTABLE_METATHEORY_EVALUATOR_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_EVALUATOR_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_EVALUATOR_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_EVALUATOR_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformanceEvaluatorConfig,
    decoder=EXECUTABLE_METATHEORY_EVALUATOR_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_PREDICTION_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-prediction",
    manifest=EXECUTABLE_METATHEORY_PREDICTION_MANIFEST,
    method=EXECUTABLE_METATHEORY_PREDICTION_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_PREDICTION_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_PREDICTION_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_PREDICTION_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformancePredictionConfig,
    decoder=EXECUTABLE_METATHEORY_PREDICTION_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_QUALIFICATION_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-qualification",
    manifest=EXECUTABLE_METATHEORY_QUALIFICATION_MANIFEST,
    method=EXECUTABLE_METATHEORY_QUALIFICATION_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_QUALIFICATION_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_QUALIFICATION_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_QUALIFICATION_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformanceQualificationConfig,
    decoder=EXECUTABLE_METATHEORY_QUALIFICATION_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_REPORTER_EXECUTABLE_BINDING = _binding(
    binding_id="binding.executable-metatheory-reporter",
    manifest=EXECUTABLE_METATHEORY_REPORTER_MANIFEST,
    method=EXECUTABLE_METATHEORY_REPORTER_METHOD,
    decoder_component=EXECUTABLE_METATHEORY_REPORTER_CONFIG_DECODER,
    runtime_provider=EXECUTABLE_METATHEORY_REPORTER_RUNTIME_PROVIDER,
    validator=EXECUTABLE_METATHEORY_REPORTER_ARTIFACT_VALIDATOR,
    record_type=MetatheoryConformanceReporterConfig,
    decoder=EXECUTABLE_METATHEORY_REPORTER_DECODER_REGISTRATION,
)
EXECUTABLE_METATHEORY_CONFORMANCE_EXECUTABLE_BINDINGS = tuple(
    sorted(
        (
            EXECUTABLE_METATHEORY_ACQUISITION_EXECUTABLE_BINDING,
            EXECUTABLE_METATHEORY_DEVELOPMENT_EXECUTABLE_BINDING,
            EXECUTABLE_METATHEORY_EVALUATOR_EXECUTABLE_BINDING,
            EXECUTABLE_METATHEORY_PREDICTION_EXECUTABLE_BINDING,
            EXECUTABLE_METATHEORY_QUALIFICATION_EXECUTABLE_BINDING,
            EXECUTABLE_METATHEORY_REPORTER_EXECUTABLE_BINDING,
        ),
        key=lambda value: value.binding_id,
    )
)


@dataclass(frozen=True, slots=True)
class IntervalPropertyComparisonProviderFactory:
    binding: ExecutableCapabilityBinding = INTERVAL_PROPERTY_COMPARISON_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import interval_property_comparison_provider
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], IntervalPropertyComparisonMethodSpec)
        ):
            raise ValueError("property-comparison factory requires one exact issued method spec")
        return interval_property_comparison_provider(
            registry=registry,
            manifest=INTERVAL_PROPERTY_COMPARISON_MANIFEST,
            spec=records[0],
        )


@dataclass(frozen=True, slots=True)
class TransformedPropertyComparisonProviderFactory:
    binding: ExecutableCapabilityBinding = TRANSFORMED_PROPERTY_COMPARISON_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import transformed_property_comparison_provider
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], TransformedPropertyComparisonMethodSpec)
        ):
            raise ValueError('transformed property comparison factory requires one exact issued spec')
        return transformed_property_comparison_provider(
            registry=registry,
            manifest=TRANSFORMED_PROPERTY_COMPARISON_MANIFEST,
            spec=records[0],
        )


@dataclass(frozen=True, slots=True)
class ProspectiveStructuralRecurrenceProviderFactory:
    binding: ExecutableCapabilityBinding = PROSPECTIVE_STRUCTURAL_RECURRENCE_EXECUTABLE_BINDING

    def authenticate_parent_inputs(
        self,
        *,
        target_candidate: ObjectIdentity,
        scientific_graph_sha256: str,
        bindings: tuple[FrozenParentInputBinding, ...],
    ) -> AuthenticatedLawTransportHandoff:
        """Authenticate the complete donor-law handoff before provider construction."""

        return authenticate_law_transport_handoff(
            target_candidate=target_candidate,
            scientific_graph_sha256=scientific_graph_sha256,
            bindings=bindings,
            forecast_method_spec_type=ProspectiveStructuralRecurrenceMethodSpec,
            forecast_method_config_type=ProspectiveStructuralRecurrencePlan,
            frozen_forecasts_type=StructuralRecurrenceFrozenLawTransportForecasts,
        )

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import structural_recurrence_prospective_provider
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], ProspectiveStructuralRecurrenceMethodSpec)
        ):
            raise ValueError('structural recurrence prospective factory requires one exact issued method spec')
        return structural_recurrence_prospective_provider(
            registry=registry,
            manifest=PROSPECTIVE_STRUCTURAL_RECURRENCE_MANIFEST,
            spec=records[0],
        )


@dataclass(frozen=True, slots=True)
class StructuralDevelopmentBridgeProviderFactory:
    binding: ExecutableCapabilityBinding = STRUCTURAL_DEVELOPMENT_BRIDGE_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import structural_development_bridge_provider
        configs = tuple(
            value for value in records if isinstance(value, StructuralDevelopmentBridgeConfig)
        )
        inputs = tuple(
            value for value in records if isinstance(value, StructuralDevelopmentInputs)
        )
        if platform_ports or len(configs) != 1 or len(inputs) != 1 or len(records) != 2:
            raise ValueError(
                "structural development factory requires issued config and authenticated inputs"
            )
        return structural_development_bridge_provider(
            registry=registry,
            manifest=STRUCTURAL_DEVELOPMENT_BRIDGE_MANIFEST,
            config=configs[0],
            development_inputs=inputs[0],
        )


@dataclass(frozen=True, slots=True)
class StructuralRecurrenceTransportProviderFactory:
    binding: ExecutableCapabilityBinding = STRUCTURAL_RECURRENCE_TRANSPORT_EXECUTABLE_BINDING

    def authenticate_parent_inputs(
        self,
        *,
        target_candidate: ObjectIdentity,
        scientific_graph_sha256: str,
        bindings: tuple[FrozenParentInputBinding, ...],
    ) -> AuthenticatedLawTransportHandoff:
        return authenticate_law_transport_handoff(
            target_candidate=target_candidate,
            scientific_graph_sha256=scientific_graph_sha256,
            bindings=bindings,
            forecast_method_spec_type=ProspectiveStructuralRecurrenceMethodSpec,
            forecast_method_config_type=ProspectiveStructuralRecurrencePlan,
            frozen_forecasts_type=StructuralRecurrenceFrozenLawTransportForecasts,
        )

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import structural_structural_recurrence_transport_provider
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], StructuralRecurrenceTransportConfig)
        ):
            raise ValueError('structural structural recurrence factory requires one exact issued config')
        return structural_structural_recurrence_transport_provider(
            registry=registry,
            manifest=STRUCTURAL_RECURRENCE_TRANSPORT_MANIFEST,
            config=records[0],
        )


@dataclass(frozen=True, slots=True)
class StructuralReporterProviderFactory:
    binding: ExecutableCapabilityBinding = STRUCTURAL_REPORTER_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import structural_reporter_provider
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], StructuralReporterConfig)
        ):
            raise ValueError("structural reporter factory requires one exact issued config")
        return structural_reporter_provider(
            registry=registry,
            manifest=STRUCTURAL_REPORTER_MANIFEST,
            config=records[0],
        )


@dataclass(frozen=True, slots=True)
class StructuralTargetBridgeProviderFactory:
    binding: ExecutableCapabilityBinding = STRUCTURAL_TARGET_BRIDGE_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        from empirical_lawhood.methods.backbone_structural_transport.provider import StructuralTargetSourcePort, structural_target_bridge_provider
        source = platform_ports[0].port if len(platform_ports) == 1 else None
        if (
            len(records) != 1
            or not isinstance(records[0], StructuralTargetBridgeConfig)
            or len(platform_ports) != 1
            or platform_ports[0].port_key != STRUCTURAL_TARGET_SOURCE_PORT_KEY
            or not isinstance(source, StructuralTargetSourcePort)
        ):
            raise ValueError(
                "structural target factory requires issued config and exact target-source port"
            )
        return structural_target_bridge_provider(
            registry=registry,
            manifest=STRUCTURAL_TARGET_BRIDGE_MANIFEST,
            config=records[0],
            source=source,
        )


@dataclass(frozen=True, slots=True)
class SourceFreePropertyTransportProviderFactory:
    binding: ExecutableCapabilityBinding
    manifest: CapabilityManifest
    role: MetatheoryCampaignStageRole
    record_type: type[CanonicalRecord]

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        if platform_ports or len(records) != 1 or not isinstance(records[0], self.record_type):
            raise ValueError("metatheory R1 factory requires one exact issued stage config")
        return source_free_property_transport_provider(
            registry=registry,
            manifest=self.manifest,
            role=self.role,
            config=records[0],
        )


SOURCE_FREE_PROPERTY_TRANSPORT_PROVIDER_FACTORIES = tuple(
    sorted(
        (
            SourceFreePropertyTransportProviderFactory(
                binding=next(
                    value
                    for value in SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_BINDINGS
                    if value.capability_key == manifest.capability_key
                ),
                manifest=manifest,
                role=role,
                record_type=record_type,
            )
            for role, manifest, record_type, *_ in SOURCE_FREE_PROPERTY_TRANSPORT_EXECUTABLE_COMPONENTS
        ),
        key=lambda value: value.binding.binding_id,
    )
)


@dataclass(frozen=True, slots=True)
class ExecutableMetatheoryConformanceProviderFactory:
    binding: ExecutableCapabilityBinding
    manifest: CapabilityManifest
    record_type: type[CanonicalRecord]

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(records[0], self.record_type)
            or not isinstance(records[0], METATHEORY_CONFORMANCE_EXECUTABLE_CONFIG_TYPES)
        ):
            raise ValueError("metatheory conformance factory requires one exact issued config")
        return metatheory_conformance_provider(
            registry=registry,
            manifest=self.manifest,
            config=records[0],
        )


EXECUTABLE_METATHEORY_CONFORMANCE_PROVIDER_FACTORIES = tuple(
    sorted(
        (
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_ACQUISITION_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_ACQUISITION_MANIFEST,
                MetatheoryConformanceAcquisitionConfig,
            ),
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_DEVELOPMENT_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_DEVELOPMENT_MANIFEST,
                MetatheoryConformanceDevelopmentConfig,
            ),
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_EVALUATOR_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_EVALUATOR_MANIFEST,
                MetatheoryConformanceEvaluatorConfig,
            ),
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_PREDICTION_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_PREDICTION_MANIFEST,
                MetatheoryConformancePredictionConfig,
            ),
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_QUALIFICATION_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_QUALIFICATION_MANIFEST,
                MetatheoryConformanceQualificationConfig,
            ),
            ExecutableMetatheoryConformanceProviderFactory(
                EXECUTABLE_METATHEORY_REPORTER_EXECUTABLE_BINDING,
                EXECUTABLE_METATHEORY_REPORTER_MANIFEST,
                MetatheoryConformanceReporterConfig,
            ),
        ),
        key=lambda value: value.binding.binding_id,
    )
)


_EXECUTABLE_ID = "executable-contribution.structural-transport"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (
    *EXECUTABLE_METATHEORY_CONFORMANCE_PROVIDER_FACTORIES,
    *SOURCE_FREE_PROPERTY_TRANSPORT_PROVIDER_FACTORIES,
    IntervalPropertyComparisonProviderFactory(),
    TransformedPropertyComparisonProviderFactory(),
    ProspectiveStructuralRecurrenceProviderFactory(),
    StructuralDevelopmentBridgeProviderFactory(),
    StructuralRecurrenceTransportProviderFactory(),
    StructuralReporterProviderFactory(),
    StructuralTargetBridgeProviderFactory(),
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (
    *METATHEORY_CONFORMANCE_EXECUTABLE_CONFIG_TYPES,
    *SOURCE_FREE_PROPERTY_TRANSPORT_CONFIG_TYPES,
    ProspectiveStructuralRecurrenceMethodSpec,
    IntervalPropertyComparisonMethodSpec,
    TransformedPropertyComparisonMethodSpec,
    StructuralDevelopmentBridgeConfig,
    StructuralRecurrenceTransportConfig,
    StructuralReporterConfig,
    StructuralTargetBridgeConfig,
)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'SOURCE_FREE_PROPERTY_TRANSPORT_CANDIDATE_REGISTRATIONS', 'SOURCE_FREE_PROPERTY_TRANSPORT_DECODER_REGISTRATIONS']
