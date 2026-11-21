# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace

from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import NATIVE_PAIR_SCHEMA
from empirical_lawhood.adapters.simulators.finite_response_law.source_outputs import FiniteResponseLawNativeTaskResult
from empirical_lawhood.execution.declaration_helpers import bundle, manifest
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope

from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedCalibrationNativeEvaluation
from empirical_lawhood.domains.matrix.finite_response_law.calibration_operands import PREDICTION_SCHEMA
from empirical_lawhood.domains.matrix.finite_response_law.method_records import COEFFICIENT_SCHEMA, MANIFEST_SCHEMA, READOUT_SCHEMA, REPORT_SCHEMA, FiniteResponseLawAssignedCalibrationMethodConfig, FiniteResponseLawAssignedCalibrationReport, FiniteResponseLawAssignedQualificationReport
from empirical_lawhood.domains.matrix.finite_response_law.native_records import FiniteResponseLawNativeEvaluationConfig, FiniteResponseLawNativeEvaluation, FiniteResponseLawNativeViewObservation, FiniteResponseLawProjectionConfig
from empirical_lawhood.domains.matrix.finite_response_law.science import PROGRAMME

PROJECTION_CAPABILITY = manifest(
    "projection",
    FiniteResponseLawProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        FiniteResponseLawProjectionConfig.SCHEMA,
        FiniteResponseLawNativeTaskResult.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (FiniteResponseLawNativeViewObservation.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATION_SEALED,
    120,
    namespace=PROGRAMME,
    resources=ResourceBudget(1, 1024**3, 0, 120, 1024**3, 1024**2),
    implementation_id="exact-native-192-paired-hold-projection",
    conformance_ids=(
        "exact-flh-projection-census",
        "paired-hold-lineage",
        "preserved-native-response-reducer",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'projection' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
EVALUATION_CAPABILITY = manifest(
    "evaluation",
    FiniteResponseLawNativeEvaluationConfig,
    CapabilityKind.EVALUATOR,
    (
        FiniteResponseLawNativeEvaluationConfig.SCHEMA,
        FiniteResponseLawNativeViewObservation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        FiniteResponseLawNativeEvaluation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATION_REVEALED,
    120,
    namespace=PROGRAMME,
    resources=ResourceBudget(1, 1024**3, 0, 120, 64 * 1024**2, 8 * 1024**2),
    implementation_id="native-census-measurement-completion-only",
    conformance_ids=(
        "complete-native-census",
        "no-oracle-or-lawhood-promotion",
        "separate-source-adjudication",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'evaluation' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
_projection, PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    PROJECTION_CAPABILITY,
    (FiniteResponseLawProjectionConfig,),
    None,
    namespace=PROGRAMME,
)
_evaluation, EVALUATION_COMPONENTS = bundle(
    "evaluation",
    ExtensionContributionKind.METHOD,
    EVALUATION_CAPABILITY,
    (FiniteResponseLawNativeEvaluationConfig,),
    None,
    namespace=PROGRAMME,
)
METHOD_CAPABILITY = manifest(
    "calibration-qualification",
    FiniteResponseLawAssignedCalibrationMethodConfig,
    CapabilityKind.EVALUATOR,
    (
        FiniteResponseLawAssignedCalibrationMethodConfig.SCHEMA,
        FiniteResponseLawAssignedQualificationReport.SCHEMA,
        ObjectIdentity.SCHEMA,
        FiniteResponseLawAssignedCalibrationNativeEvaluation.SCHEMA,
        CanonicalTaskReceipt.SCHEMA,
        REPORT_SCHEMA,
        COEFFICIENT_SCHEMA,
        MANIFEST_SCHEMA,
        FiniteResponseLawAssignedCalibrationReport.SCHEMA,
        PREDICTION_SCHEMA,
        READOUT_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        FiniteResponseLawAssignedCalibrationReport.SCHEMA,
        FiniteResponseLawAssignedQualificationReport.SCHEMA,
        ObjectIdentity.SCHEMA,
        PREDICTION_SCHEMA,
        READOUT_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ),
    EvidenceCeiling.LOCAL_LAW,
    OutcomeAccess.EVALUATOR_REVEAL,
    120,
    namespace=PROGRAMME,
    resources=ResourceBudget(1, 1024**3, 0, 120, 32 * 1024**2, 8 * 1024**2),
    read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
    implementation_id="frozen-32-root-rank-30-four-singleton-joint-qualification-separate-adjudication",
    conformance_ids=(
        "committed-calibration-custody",
        "finite-nonfinite-unevaluable-truth-table",
        "sole-law-qualification-owner",
    ),
)
METHOD_CAPABILITY = replace(
    METHOD_CAPABILITY,
    permissions=tuple(
        sorted((*METHOD_CAPABILITY.permissions, CapabilityPermission.REVEAL_OUTCOMES))
    ),
)
_method, METHOD_COMPONENTS = bundle(
    "calibration-qualification",
    ExtensionContributionKind.METHOD,
    METHOD_CAPABILITY,
    (FiniteResponseLawAssignedCalibrationMethodConfig,),
    None,
    namespace=PROGRAMME,
)
_DISCOVERY_CONTRIBUTION = replace(
    _projection,
    contribution_id=f"extension-contribution.{PROGRAMME}.methods",
    capability_manifests=tuple(
        sorted(
            (
                *_projection.capability_manifests,
                *_evaluation.capability_manifests,
                *_method.capability_manifests,
            ),
            key=lambda v: v.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                *_projection.candidate_capability_registrations,
                *_evaluation.candidate_capability_registrations,
                *_method.candidate_capability_registrations,
            ),
            key=lambda v: v.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (
                *_projection.profile_registrations,
                *_evaluation.profile_registrations,
                *_method.profile_registrations,
            ),
            key=lambda v: v.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            (
                *_projection.config_decoders,
                *_evaluation.config_decoders,
                *_method.config_decoders,
            ),
            key=lambda v: v.object_id,
        )
    ),
    runtime_providers=tuple(
        sorted(
            (
                *_projection.runtime_providers,
                *_evaluation.runtime_providers,
                *_method.runtime_providers,
            ),
            key=lambda v: v.object_id,
        )
    ),
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.candidate_payloads import CandidatePayloadPlane
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.source_resolution import ContentAddressedInputResolver


from empirical_lawhood.domains.matrix.finite_response_law.method_provider import CANDIDATE_PAYLOAD_PORT, INPUT_RESOLVER_PORT, FiniteResponseLawCalibrationMethodProvider
from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedCalibrationMethodConfig
from empirical_lawhood.domains.matrix.finite_response_law.native_provider import FiniteResponseLawNativeMethodProvider
from empirical_lawhood.domains.matrix.finite_response_law.native_records import FiniteResponseLawNativeEvaluationConfig, FiniteResponseLawProjectionConfig
from empirical_lawhood.domains.matrix.finite_response_law.science import PROGRAMME

PROJECTION_BINDING = executable(
    PROJECTION_CAPABILITY, PROJECTION_COMPONENTS, (FiniteResponseLawProjectionConfig,)
)
EVALUATION_BINDING = executable(
    EVALUATION_CAPABILITY, EVALUATION_COMPONENTS, (FiniteResponseLawNativeEvaluationConfig,)
)
METHOD_BINDING = replace(
    executable(
        METHOD_CAPABILITY, METHOD_COMPONENTS, (FiniteResponseLawAssignedCalibrationMethodConfig,)
    ),
    required_platform_port_keys=tuple(
        sorted((CANDIDATE_PAYLOAD_PORT, INPUT_RESOLVER_PORT))
    ),
)


@dataclass(frozen=True, slots=True)
class FiniteResponseLawCalibrationQualificationFactory:
    binding: ExecutableCapabilityBinding = METHOD_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteResponseLawCalibrationMethodProvider:
        ports = {p.port_key: p.port for p in platform_ports}
        if (
            self.binding != METHOD_BINDING
            or len(records) != 1
            or type(records[0]) is not FiniteResponseLawAssignedCalibrationMethodConfig
            or len(ports) != len(platform_ports)
            or tuple(sorted(ports)) != self.binding.required_platform_port_keys
        ):
            raise ValueError(
                "Finite response-law qualification requires its exact issued configuration and existing I/O ports"
            )
        if (
            not callable(getattr(ports[INPUT_RESOLVER_PORT], "resolve", None))
            or not callable(
                getattr(
                    ports[CANDIDATE_PAYLOAD_PORT], "publish_candidate_payload", None
                )
            )
            or not callable(
                getattr(ports[CANDIDATE_PAYLOAD_PORT], "read_candidate_payload", None)
            )
        ):
            raise TypeError(
                "Finite response-law qualification requires working custody and payload ports"
            )
        return FiniteResponseLawCalibrationMethodProvider(
            registry,
            METHOD_CAPABILITY,
            records[0],
            cast(ContentAddressedInputResolver, ports[INPUT_RESOLVER_PORT]),
            cast(CandidatePayloadPlane, ports[CANDIDATE_PAYLOAD_PORT]),
        )


@dataclass(frozen=True, slots=True)
class FiniteResponseLawNativeMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteResponseLawNativeMethodProvider:
        if platform_ports or len(records) != 1:
            raise ValueError(
                "Finite response-law method factory requires one exact issued configuration"
            )
        config = records[0]
        if self.binding == PROJECTION_BINDING and type(config) is FiniteResponseLawProjectionConfig:
            return FiniteResponseLawNativeMethodProvider(registry, PROJECTION_CAPABILITY, config)
        if (
            self.binding == EVALUATION_BINDING
            and type(config) is FiniteResponseLawNativeEvaluationConfig
        ):
            return FiniteResponseLawNativeMethodProvider(registry, EVALUATION_CAPABILITY, config)
        raise ValueError("Finite response-law method factory changes its binding/configuration")


_EXECUTABLE_ID = f"executable-contribution.{PROGRAMME}.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (
    FiniteResponseLawNativeMethodFactory(PROJECTION_BINDING),
    FiniteResponseLawNativeMethodFactory(EVALUATION_BINDING),
    FiniteResponseLawCalibrationQualificationFactory(),
)
_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (
    FiniteResponseLawProjectionConfig,
    FiniteResponseLawNativeEvaluationConfig,
    FiniteResponseLawAssignedCalibrationMethodConfig,
)
_ISSUED_RECORD_TYPES = tuple(sorted(_RECORD_TYPES, key=lambda t: t.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EVALUATION_BINDING', 'EVALUATION_CAPABILITY', 'EXTENSION', 'METHOD_BINDING', 'METHOD_CAPABILITY', 'PROJECTION_BINDING', 'PROJECTION_CAPABILITY']
