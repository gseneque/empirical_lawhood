# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.declaration_helpers import bundle, manifest
from empirical_lawhood.adapters.simulators.prepared_response.native_pair import NATIVE_PAIR_SCHEMA
from empirical_lawhood.adapters.simulators.prepared_response.source_outputs import PreparedNativeTaskResult
from empirical_lawhood.domains.matrix.prepared_response.qualification_records import PreparedResponseSourceQualificationProjectionConfig, PreparedResponseSourceQualificationViewObservation
from empirical_lawhood.domains.matrix.prepared_response.qualification import PreparedResponseSourceQualificationEvaluationConfig, PreparedResponseSourceQualificationEvaluation
from empirical_lawhood.domains.matrix.prepared_response.development_projection import PreparedResponseDevelopmentProjectionConfig, PreparedResponseDevelopmentViewProjection
from empirical_lawhood.domains.matrix.prepared_response.development_fit import PreparedResponseDevelopmentFitConfig, PreparedResponseDevelopmentModelFit
from empirical_lawhood.domains.matrix.prepared_response.development_selection import PreparedResponseDevelopmentNominalLibrary, PreparedResponseDevelopmentSelectionConfig
from empirical_lawhood.domains.matrix.prepared_response.development_benchmarks import PreparedResponseDevelopmentConstantGainReport
from empirical_lawhood.domains.matrix.prepared_response.policy_decision import PreparedParentDecision, PreparedPolicyDecisionConfig
from empirical_lawhood.domains.matrix.prepared_response.calibration_records import PreparedResponseCalibrationCalibratedLibrary, PreparedResponseCalibrationCalibrationConfig, PreparedResponseCalibrationProjectionConfig, PreparedResponseCalibrationViewProjection
from empirical_lawhood.domains.matrix.prepared_response.policy_native import PreparedResponseCalibrationNativeTaskResult


SOURCE_QUALIFICATION_NAMESPACE = "prepared-response.source-qualification"
DEVELOPMENT_NAMESPACE = "prepared-response.dependent-refinement"
SOURCE_QUALIFICATION_PROJECTION_CAPABILITY = manifest(
    "projection",
    PreparedResponseSourceQualificationProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        PreparedResponseSourceQualificationProjectionConfig.SCHEMA,
        PreparedNativeTaskResult.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (PreparedResponseSourceQualificationViewObservation.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_SEALED,
    180,
    namespace=SOURCE_QUALIFICATION_NAMESPACE,
    resources=ResourceBudget(1, 1024**3, 0, 180, 2 * 1024**3, 1024**2),
    implementation_id="source-qualification-absolute-two-port-native-projection",
    conformance_ids=(
        "complete-assigned-root-census",
        "matched-innovation-preservation",
        "no-source-contact-in-projection",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'projection' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
SOURCE_QUALIFICATION_EVALUATION_CAPABILITY = manifest(
    "evaluation",
    PreparedResponseSourceQualificationEvaluationConfig,
    CapabilityKind.EVALUATOR,
    (
        PreparedResponseSourceQualificationEvaluationConfig.SCHEMA,
        PreparedResponseSourceQualificationViewObservation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        PreparedResponseSourceQualificationEvaluation.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_REVEALED,
    180,
    namespace=SOURCE_QUALIFICATION_NAMESPACE,
    resources=ResourceBudget(1, 1024**3, 0, 180, 128 * 1024**2, 2 * 1024**2),
    implementation_id="source-qualification-forty-eight-charter-both-context-nomination",
    conformance_ids=(
        "all-assigned-source-qualification-roots-retained",
        "both-context-charter-intersection",
        "fixed-parent-command-comparators",
        "valid-negative-and-unevaluable-q-stops",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'evaluation' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
DEVELOPMENT_PROJECTION_CAPABILITY = manifest(
    "projection",
    PreparedResponseDevelopmentProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        PreparedResponseDevelopmentProjectionConfig.SCHEMA,
        PreparedNativeTaskResult.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (PreparedResponseDevelopmentViewProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    300,
    namespace=DEVELOPMENT_NAMESPACE,
    resources=ResourceBudget(1, 3 * 1024**3, 0, 300, 2 * 1024**3, 2 * 1024**2),
    read_permission=CapabilityPermission.READ_OUTCOME_VISIBLE,
    implementation_id="dependent-refinement-absolute-two-port-per-view-projection",
    conformance_ids=(
        "complete-assigned-development-root-census",
        "no-source-contact-in-projection",
        "paired-acquisition-separate-view-products",
    ),
)
DEVELOPMENT_FIT_CAPABILITY = manifest(
    "fit",
    PreparedResponseDevelopmentFitConfig,
    CapabilityKind.ANALYSIS,
    (
        PreparedResponseDevelopmentFitConfig.SCHEMA,
        PreparedResponseDevelopmentViewProjection.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (PreparedResponseDevelopmentModelFit.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.LOCAL_LAW,
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    1800,
    namespace=DEVELOPMENT_NAMESPACE,
    resources=ResourceBudget(1, 4 * 1024**3, 0, 1800, 512 * 1024**2, 18 * 1024**2),
    read_permission=CapabilityPermission.READ_OUTCOME_VISIBLE,
    implementation_id="dependent-refinement-four-family-whole-root-nested-bilinear-fit",
    conformance_ids=(
        "all-assigned-development-roots-retained",
        "authored-whole-root-nested-crossfit",
        "nominal-products-do-not-qualify-a-law",
    ),
)
DEVELOPMENT_SELECTION_CAPABILITY = manifest(
    "selection",
    PreparedResponseDevelopmentSelectionConfig,
    CapabilityKind.HYPOTHESIS_ADJUDICATOR,
    (
        PreparedResponseDevelopmentSelectionConfig.SCHEMA,
        PreparedResponseDevelopmentViewProjection.SCHEMA,
        PreparedResponseDevelopmentModelFit.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        PreparedResponseDevelopmentNominalLibrary.SCHEMA,
        PreparedResponseDevelopmentConstantGainReport.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_REVEALED,
    1800,
    namespace=DEVELOPMENT_NAMESPACE,
    resources=ResourceBudget(1, 4 * 1024**3, 0, 1800, 1024**3, 32 * 1024**2),
    read_permission=CapabilityPermission.READ_OUTCOME_VISIBLE,
    implementation_id="dependent-refinement-two-context-selection-joint-handoff-scenarios-constant-gain",
    conformance_ids=(
        "all-failed-candidates-retained",
        "both-context-eligibility-intersection",
        "constant-gain-reuses-held-baselines-without-calibration-promotion",
        "nominal-library-grants-no-law-authority",
        "training-only-baseline-and-intervals",
    ),
)
CALIBRATION_POLICY_CAPABILITY = manifest(
    "policy",
    PreparedPolicyDecisionConfig,
    CapabilityKind.PROSPECTIVE_NOMINATOR,
    (
        PreparedPolicyDecisionConfig.SCHEMA,
        PreparedResponseCalibrationNativeTaskResult.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (PreparedParentDecision.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_SEALED,
    120,
    namespace="prepared-response.fresh-response-calibration",
    resources=ResourceBudget(1, 1024**3, 0, 120, 64 * 1024**2, 1024**2),
    implementation_id="development-frozen-target-blind-adequacy-constrained-parent",
    conformance_ids=(
        "four-development-frozen-policy-roles",
        "no-target-or-future-input",
        "preparent-primary-view-cutoff",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'policy' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
CALIBRATION_PROJECTION_CAPABILITY = manifest(
    "projection",
    PreparedResponseCalibrationProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        PreparedResponseCalibrationProjectionConfig.SCHEMA,
        PreparedResponseCalibrationNativeTaskResult.SCHEMA,
        PreparedParentDecision.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (PreparedResponseCalibrationViewProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_SEALED,
    300,
    namespace="prepared-response.fresh-response-calibration",
    resources=ResourceBudget(1, 3 * 1024**3, 0, 300, 256 * 1024**2, 2 * 1024**2),
    implementation_id="fresh-calibration-authenticated-policy-chart-parent-work-projection",
    conformance_ids=(
        "complete-policy-word-view-census",
        "exact-invocation-predecessor-common-start-parent-joins",
        "no-native-effect-in-projection",
        "same-innovation-hold-preservation",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'projection' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
CALIBRATION_CALIBRATION_CAPABILITY = manifest(
    "calibration",
    PreparedResponseCalibrationCalibrationConfig,
    CapabilityKind.EVALUATOR,
    (
        PreparedResponseCalibrationCalibrationConfig.SCHEMA,
        PreparedResponseCalibrationViewProjection.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        PreparedResponseCalibrationCalibratedLibrary.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_REVEALED,
    1800,
    namespace="prepared-response.fresh-response-calibration",
    resources=ResourceBudget(1, 4 * 1024**3, 0, 1800, 8 * 1024**3, 32 * 1024**2),
    read_permission=CapabilityPermission.READ_OUTCOME_VISIBLE,
    implementation_id="fresh-calibration-config-bound-root-maximum-split-conformal",
    conformance_ids=(
        "fixed-order-statistic-93",
        "invalid-coordinate-infinite-score",
        "ninety-six-root-context-census",
    ),
)
_projection, SOURCE_QUALIFICATION_PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    SOURCE_QUALIFICATION_PROJECTION_CAPABILITY,
    (PreparedResponseSourceQualificationProjectionConfig,),
    None,
    namespace=SOURCE_QUALIFICATION_NAMESPACE,
)
_evaluation, SOURCE_QUALIFICATION_EVALUATION_COMPONENTS = bundle(
    "evaluation",
    ExtensionContributionKind.METHOD,
    SOURCE_QUALIFICATION_EVALUATION_CAPABILITY,
    (PreparedResponseSourceQualificationEvaluationConfig,),
    None,
    namespace=SOURCE_QUALIFICATION_NAMESPACE,
)
_development_projection, DEVELOPMENT_PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    DEVELOPMENT_PROJECTION_CAPABILITY,
    (PreparedResponseDevelopmentProjectionConfig,),
    None,
    namespace=DEVELOPMENT_NAMESPACE,
)
_development_fit, DEVELOPMENT_FIT_COMPONENTS = bundle(
    "fit",
    ExtensionContributionKind.METHOD,
    DEVELOPMENT_FIT_CAPABILITY,
    (PreparedResponseDevelopmentFitConfig,),
    None,
    namespace=DEVELOPMENT_NAMESPACE,
)
_development_selection, DEVELOPMENT_SELECTION_COMPONENTS = bundle(
    "selection",
    ExtensionContributionKind.METHOD,
    DEVELOPMENT_SELECTION_CAPABILITY,
    (PreparedResponseDevelopmentSelectionConfig,),
    None,
    namespace=DEVELOPMENT_NAMESPACE,
)
_calibration_policy, CALIBRATION_POLICY_COMPONENTS = bundle(
    "policy",
    ExtensionContributionKind.METHOD,
    CALIBRATION_POLICY_CAPABILITY,
    (PreparedPolicyDecisionConfig,),
    None,
    namespace="prepared-response.fresh-response-calibration",
    maximum_config_bytes=16 * 1024**2,
)
_calibration_projection, CALIBRATION_PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    CALIBRATION_PROJECTION_CAPABILITY,
    (PreparedResponseCalibrationProjectionConfig,),
    None,
    namespace="prepared-response.fresh-response-calibration",
    maximum_config_bytes=16 * 1024**2,
)
_calibration_evaluation, CALIBRATION_CALIBRATION_COMPONENTS = bundle(
    "calibration",
    ExtensionContributionKind.METHOD,
    CALIBRATION_CALIBRATION_CAPABILITY,
    (PreparedResponseCalibrationCalibrationConfig,),
    None,
    namespace="prepared-response.fresh-response-calibration",
    maximum_config_bytes=16 * 1024**2,
)
_DISCOVERY_CONTRIBUTION = replace(
    _projection,
    contribution_id=f"extension-contribution.{SOURCE_QUALIFICATION_NAMESPACE}.methods",
    capability_manifests=tuple(
        sorted(
            (
                *_projection.capability_manifests,
                *_evaluation.capability_manifests,
                *_development_projection.capability_manifests,
                *_development_fit.capability_manifests,
                *_development_selection.capability_manifests,
                *_calibration_policy.capability_manifests,
                *_calibration_projection.capability_manifests,
                *_calibration_evaluation.capability_manifests,
            ),
            key=lambda value: value.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                *_projection.candidate_capability_registrations,
                *_evaluation.candidate_capability_registrations,
                *_development_projection.candidate_capability_registrations,
                *_development_fit.candidate_capability_registrations,
                *_development_selection.candidate_capability_registrations,
                *_calibration_policy.candidate_capability_registrations,
                *_calibration_projection.candidate_capability_registrations,
                *_calibration_evaluation.candidate_capability_registrations,
            ),
            key=lambda value: value.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (
                *_projection.profile_registrations,
                *_evaluation.profile_registrations,
                *_development_projection.profile_registrations,
                *_development_fit.profile_registrations,
                *_development_selection.profile_registrations,
                *_calibration_policy.profile_registrations,
                *_calibration_projection.profile_registrations,
                *_calibration_evaluation.profile_registrations,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            (
                *_projection.config_decoders,
                *_evaluation.config_decoders,
                *_development_projection.config_decoders,
                *_development_fit.config_decoders,
                *_development_selection.config_decoders,
                *_calibration_policy.config_decoders,
                *_calibration_projection.config_decoders,
                *_calibration_evaluation.config_decoders,
            ),
            key=lambda value: value.object_id,
        )
    ),
    runtime_providers=tuple(
        sorted(
            (
                *_projection.runtime_providers,
                *_evaluation.runtime_providers,
                *_development_projection.runtime_providers,
                *_development_fit.runtime_providers,
                *_development_selection.runtime_providers,
                *_calibration_policy.runtime_providers,
                *_calibration_projection.runtime_providers,
                *_calibration_evaluation.runtime_providers,
            ),
            key=lambda value: value.object_id,
        )
    ),
)


# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.declaration_helpers import executable

from empirical_lawhood.domains.matrix.prepared_response.development_fit import PreparedResponseDevelopmentFitConfig
from empirical_lawhood.domains.matrix.prepared_response.development_projection import PreparedResponseDevelopmentProjectionConfig
from empirical_lawhood.domains.matrix.prepared_response.development_provider import PreparedResponseDevelopmentMethodProvider
from empirical_lawhood.domains.matrix.prepared_response.development_selection import PreparedResponseDevelopmentSelectionConfig
from empirical_lawhood.domains.matrix.prepared_response.policy_decision import PreparedPolicyDecisionConfig
from empirical_lawhood.domains.matrix.prepared_response.policy_provider import PreparedPolicyDecisionProvider
from empirical_lawhood.domains.matrix.prepared_response.calibration_records import PreparedResponseCalibrationCalibrationConfig, PreparedResponseCalibrationProjectionConfig
from empirical_lawhood.domains.matrix.prepared_response.calibration_provider import PreparedResponseCalibrationMethodProvider
from empirical_lawhood.domains.matrix.prepared_response.qualification_records import PreparedResponseSourceQualificationProjectionConfig
from empirical_lawhood.domains.matrix.prepared_response.qualification import PreparedResponseSourceQualificationEvaluationConfig
from empirical_lawhood.domains.matrix.prepared_response.qualification_provider import PreparedResponseSourceQualificationMethodProvider


SOURCE_QUALIFICATION_PROJECTION_BINDING = executable(
    SOURCE_QUALIFICATION_PROJECTION_CAPABILITY, SOURCE_QUALIFICATION_PROJECTION_COMPONENTS, (PreparedResponseSourceQualificationProjectionConfig,)
)
SOURCE_QUALIFICATION_EVALUATION_BINDING = executable(
    SOURCE_QUALIFICATION_EVALUATION_CAPABILITY, SOURCE_QUALIFICATION_EVALUATION_COMPONENTS, (PreparedResponseSourceQualificationEvaluationConfig,)
)
DEVELOPMENT_PROJECTION_BINDING = executable(
    DEVELOPMENT_PROJECTION_CAPABILITY, DEVELOPMENT_PROJECTION_COMPONENTS, (PreparedResponseDevelopmentProjectionConfig,)
)
DEVELOPMENT_FIT_BINDING = executable(DEVELOPMENT_FIT_CAPABILITY, DEVELOPMENT_FIT_COMPONENTS, (PreparedResponseDevelopmentFitConfig,))
DEVELOPMENT_SELECTION_BINDING = executable(
    DEVELOPMENT_SELECTION_CAPABILITY, DEVELOPMENT_SELECTION_COMPONENTS, (PreparedResponseDevelopmentSelectionConfig,)
)
CALIBRATION_POLICY_BINDING = executable(
    CALIBRATION_POLICY_CAPABILITY, CALIBRATION_POLICY_COMPONENTS, (PreparedPolicyDecisionConfig,)
)
CALIBRATION_PROJECTION_BINDING = executable(
    CALIBRATION_PROJECTION_CAPABILITY, CALIBRATION_PROJECTION_COMPONENTS, (PreparedResponseCalibrationProjectionConfig,)
)
CALIBRATION_CALIBRATION_BINDING = executable(
    CALIBRATION_CALIBRATION_CAPABILITY, CALIBRATION_CALIBRATION_COMPONENTS, (PreparedResponseCalibrationCalibrationConfig,)
)
CALIBRATION_POLICY_BINDING, CALIBRATION_PROJECTION_BINDING, CALIBRATION_CALIBRATION_BINDING = tuple(
    replace(
        binding,
        issued_decoder_registrations=tuple(
            replace(decoder, maximum_payload_bytes=16 * 1024**2)
            for decoder in binding.issued_decoder_registrations
        ),
    )
    for binding in (CALIBRATION_POLICY_BINDING, CALIBRATION_PROJECTION_BINDING, CALIBRATION_CALIBRATION_BINDING)
)


@dataclass(frozen=True, slots=True)
class PreparedResponseSourceQualificationMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> PreparedResponseSourceQualificationMethodProvider:
        if platform_ports or len(records) != 1:
            raise ValueError(
                "prepared source qualification method factory requires one exact issued config and no source port"
            )
        config = records[0]
        if self.binding == SOURCE_QUALIFICATION_PROJECTION_BINDING and type(config) is PreparedResponseSourceQualificationProjectionConfig:
            return PreparedResponseSourceQualificationMethodProvider(registry, SOURCE_QUALIFICATION_PROJECTION_CAPABILITY, config)
        if self.binding == SOURCE_QUALIFICATION_EVALUATION_BINDING and type(config) is PreparedResponseSourceQualificationEvaluationConfig:
            return PreparedResponseSourceQualificationMethodProvider(registry, SOURCE_QUALIFICATION_EVALUATION_CAPABILITY, config)
        raise ValueError(
            "prepared source qualification method factory changed its installed binding/configuration type"
        )


@dataclass(frozen=True, slots=True)
class PreparedResponseDevelopmentMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> PreparedResponseDevelopmentMethodProvider:
        if platform_ports or len(records) != 1:
            raise ValueError(
                "prepared dependent refinement method factory requires one exact issued config and no source port"
            )
        config = records[0]
        if (
            self.binding == DEVELOPMENT_PROJECTION_BINDING
            and type(config) is PreparedResponseDevelopmentProjectionConfig
        ) or (
            self.binding == DEVELOPMENT_FIT_BINDING and type(config) is PreparedResponseDevelopmentFitConfig
        ) or (
            self.binding == DEVELOPMENT_SELECTION_BINDING and type(config) is PreparedResponseDevelopmentSelectionConfig
        ):
            return PreparedResponseDevelopmentMethodProvider(
                registry,
                DEVELOPMENT_PROJECTION_CAPABILITY
                if type(config) is PreparedResponseDevelopmentProjectionConfig
                else DEVELOPMENT_FIT_CAPABILITY
                if type(config) is PreparedResponseDevelopmentFitConfig
                else DEVELOPMENT_SELECTION_CAPABILITY,
                config,
            )
        raise ValueError(
            "prepared dependent refinement method factory changed its installed binding/configuration type"
        )


@dataclass(frozen=True, slots=True)
class PreparedResponseCalibrationMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> PreparedPolicyDecisionProvider | PreparedResponseCalibrationMethodProvider:
        if platform_ports or len(records) != 1:
            raise ValueError(
                "prepared fresh calibration method factory requires one exact issued config and no source port"
            )
        config = records[0]
        if self.binding == CALIBRATION_POLICY_BINDING and type(config) is PreparedPolicyDecisionConfig:
            return PreparedPolicyDecisionProvider(registry, CALIBRATION_POLICY_CAPABILITY, config)
        if self.binding == CALIBRATION_PROJECTION_BINDING and type(config) is PreparedResponseCalibrationProjectionConfig:
            return PreparedResponseCalibrationMethodProvider(registry, CALIBRATION_PROJECTION_CAPABILITY, config)
        if self.binding == CALIBRATION_CALIBRATION_BINDING and type(config) is PreparedResponseCalibrationCalibrationConfig:
            return PreparedResponseCalibrationMethodProvider(registry, CALIBRATION_CALIBRATION_CAPABILITY, config)
        raise ValueError(
            "prepared fresh calibration method factory changed its installed binding/configuration type"
        )


_EXECUTABLE_BINDINGS = tuple(
        sorted(
            (
                SOURCE_QUALIFICATION_PROJECTION_BINDING,
                SOURCE_QUALIFICATION_EVALUATION_BINDING,
                DEVELOPMENT_PROJECTION_BINDING,
                DEVELOPMENT_FIT_BINDING,
                DEVELOPMENT_SELECTION_BINDING,
                CALIBRATION_POLICY_BINDING,
                CALIBRATION_PROJECTION_BINDING,
                CALIBRATION_CALIBRATION_BINDING,
            ),
            key=lambda value: value.binding_id,
        )
    )
_EXECUTABLE_ID = "executable-contribution.prepared-response.source-qualification-dependent-refinement.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(
    PreparedResponseSourceQualificationMethodFactory(binding)
    if binding in (SOURCE_QUALIFICATION_PROJECTION_BINDING, SOURCE_QUALIFICATION_EVALUATION_BINDING)
    else PreparedResponseDevelopmentMethodFactory(binding)
    if binding in (DEVELOPMENT_PROJECTION_BINDING, DEVELOPMENT_FIT_BINDING, DEVELOPMENT_SELECTION_BINDING)
    else PreparedResponseCalibrationMethodFactory(binding)
    for binding in _EXECUTABLE_BINDINGS
)
_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (
    PreparedResponseSourceQualificationProjectionConfig,
    PreparedResponseSourceQualificationEvaluationConfig,
    PreparedResponseDevelopmentProjectionConfig,
    PreparedResponseDevelopmentFitConfig,
    PreparedResponseDevelopmentSelectionConfig,
    PreparedPolicyDecisionConfig,
    PreparedResponseCalibrationProjectionConfig,
    PreparedResponseCalibrationCalibrationConfig,
)
_ISSUED_RECORD_TYPES = tuple(sorted(_RECORD_TYPES, key=lambda value: value.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['CALIBRATION_CALIBRATION_BINDING', 'CALIBRATION_CALIBRATION_CAPABILITY', 'CALIBRATION_POLICY_BINDING', 'CALIBRATION_POLICY_CAPABILITY', 'CALIBRATION_PROJECTION_BINDING', 'CALIBRATION_PROJECTION_CAPABILITY', 'DEVELOPMENT_FIT_BINDING', 'DEVELOPMENT_FIT_CAPABILITY', 'DEVELOPMENT_PROJECTION_BINDING', 'DEVELOPMENT_PROJECTION_CAPABILITY', 'DEVELOPMENT_SELECTION_BINDING', 'DEVELOPMENT_SELECTION_CAPABILITY', 'EXTENSION', 'SOURCE_QUALIFICATION_EVALUATION_BINDING', 'SOURCE_QUALIFICATION_EVALUATION_CAPABILITY', 'SOURCE_QUALIFICATION_PROJECTION_BINDING', 'SOURCE_QUALIFICATION_PROJECTION_CAPABILITY']

_EXECUTION_CONTRIBUTION = EXTENSION.executable
