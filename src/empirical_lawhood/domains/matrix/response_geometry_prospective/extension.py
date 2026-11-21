# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.matrix.response_geometry_prospective.provider import ResponseGeometryAssayMethodProvider


# Scientific registration and configuration.

from dataclasses import replace

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import bundle, manifest
from empirical_lawhood.domains.matrix.six_matrix_response.response_qualification import ResponseGeometryAssayNativeSegmentResult
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import ASSAY_HDF5_SCHEMA

from empirical_lawhood.domains.matrix.response_geometry_prospective.projection import ASSAY_DIAGNOSTICS_SCHEMA
from empirical_lawhood.domains.matrix.response_geometry_prospective.qualification import ResponseGeometryAssayProjectionConfig, ResponseGeometryAssayEvaluationConfig, ResponseGeometryAssayViewReport, ResponseGeometryAssayEvaluation

ASSAY_PROJECTION_CAPABILITY = manifest(
    "projection",
    ResponseGeometryAssayProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        ResponseGeometryAssayProjectionConfig.SCHEMA,
        ResponseGeometryAssayNativeSegmentResult.SCHEMA,
        ASSAY_HDF5_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (ResponseGeometryAssayViewReport.SCHEMA, ASSAY_DIAGNOSTICS_SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_SEALED,
    120,
)
ASSAY_EVALUATION_CAPABILITY = manifest(
    "evaluation",
    ResponseGeometryAssayEvaluationConfig,
    CapabilityKind.EVALUATOR,
    (
        ResponseGeometryAssayEvaluationConfig.SCHEMA,
        ResponseGeometryAssayViewReport.SCHEMA,
        ASSAY_DIAGNOSTICS_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        ResponseGeometryAssayEvaluation.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_REVEALED,
    120,
)
_projection, ASSAY_PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    ASSAY_PROJECTION_CAPABILITY,
    (ResponseGeometryAssayProjectionConfig,),
    ASSAY_DIAGNOSTICS_SCHEMA,
)
_evaluation, ASSAY_EVALUATION_COMPONENTS = bundle(
    "evaluation",
    ExtensionContributionKind.METHOD,
    ASSAY_EVALUATION_CAPABILITY,
    (ResponseGeometryAssayEvaluationConfig,),
    None,
)
_DISCOVERY_CONTRIBUTION = replace(
    _projection,
    contribution_id="extension-contribution.response-geometry-assay.methods",
    capability_manifests=tuple(
        sorted(
            (*_projection.capability_manifests, *_evaluation.capability_manifests),
            key=lambda value: value.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                *_projection.candidate_capability_registrations,
                *_evaluation.candidate_capability_registrations,
            ),
            key=lambda value: value.manifest.registry_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            (*_projection.config_decoders, *_evaluation.config_decoders),
            key=lambda value: value.object_id,
        )
    ),
    runtime_providers=tuple(
        sorted(
            (*_projection.runtime_providers, *_evaluation.runtime_providers),
            key=lambda value: value.object_id,
        )
    ),
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import executable


from empirical_lawhood.domains.matrix.response_geometry_prospective.qualification import ResponseGeometryAssayProjectionConfig, ResponseGeometryAssayEvaluationConfig


ASSAY_PROJECTION_BINDING = executable(
    ASSAY_PROJECTION_CAPABILITY, ASSAY_PROJECTION_COMPONENTS, (ResponseGeometryAssayProjectionConfig,)
)
ASSAY_EVALUATION_BINDING = executable(
    ASSAY_EVALUATION_CAPABILITY, ASSAY_EVALUATION_COMPONENTS, (ResponseGeometryAssayEvaluationConfig,)
)


@dataclass(frozen=True, slots=True)
class ResponseGeometryAssayProjectionProviderFactory:
    binding: ExecutableCapabilityBinding = ASSAY_PROJECTION_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ResponseGeometryAssayMethodProvider:
        from empirical_lawhood.domains.matrix.response_geometry_prospective.provider import ResponseGeometryAssayMethodProvider
        if platform_ports or len(records) != 1 or not isinstance(records[0], ResponseGeometryAssayProjectionConfig):
            raise ValueError("assay projection factory requires its exact issued config")
        return ResponseGeometryAssayMethodProvider(registry, ASSAY_PROJECTION_CAPABILITY, records[0])


@dataclass(frozen=True, slots=True)
class ResponseGeometryAssayEvaluationProviderFactory:
    binding: ExecutableCapabilityBinding = ASSAY_EVALUATION_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ResponseGeometryAssayMethodProvider:
        from empirical_lawhood.domains.matrix.response_geometry_prospective.provider import ResponseGeometryAssayMethodProvider
        if platform_ports or len(records) != 1 or not isinstance(records[0], ResponseGeometryAssayEvaluationConfig):
            raise ValueError("assay evaluator factory requires its exact issued config")
        return ResponseGeometryAssayMethodProvider(registry, ASSAY_EVALUATION_CAPABILITY, records[0])


_EXECUTABLE_ID = "executable-contribution.response-geometry-assay.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ResponseGeometryAssayEvaluationProviderFactory(), ResponseGeometryAssayProjectionProviderFactory())
_ISSUED_RECORD_TYPES = tuple(
    sorted((ResponseGeometryAssayProjectionConfig, ResponseGeometryAssayEvaluationConfig), key=lambda value: value.SCHEMA)
)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['ASSAY_EVALUATION_BINDING', 'ASSAY_EVALUATION_CAPABILITY', 'ASSAY_PROJECTION_BINDING', 'ASSAY_PROJECTION_CAPABILITY', 'EXTENSION']
