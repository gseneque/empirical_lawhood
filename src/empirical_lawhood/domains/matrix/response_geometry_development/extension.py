# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import bundle, manifest
from empirical_lawhood.domains.matrix.six_matrix_response.response_development import DEVELOPMENT_PANEL_ID, DEVELOPMENT_HDF5_SCHEMA, ResponseGeometryDevelopmentNativeSegmentResult
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_projection import DEVELOPMENT_DATA_SCHEMA, ResponseGeometryDevelopmentProjectionConfig, ResponseGeometryDevelopmentViewReport
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_records import DEVELOPMENT_FIT_SCHEMA, ResponseGeometryDevelopmentMethodConfig, ResponseGeometryDevelopmentFitResult, ResponseGeometryDevelopmentCalibrationResult, ResponseGeometryDevelopmentSupportResult
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_terminal import ResponseGeometryDevelopmentQualificationConfig, DEVELOPMENT_VALIDATION_SCHEMA
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_geometry_assessment import ResponseGeometryDevelopmentGeometryReport
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_closeout import ResponseGeometryDevelopmentContextResult, ResponseGeometryDevelopmentDevelopmentResult, ResponseGeometryDevelopmentCloseoutConfig


_STAGE = LinkedCampaignStageEnvelope.SCHEMA
# Each manifest charges the complete task's scan/output ceilings. The exact
# derived-plan proof must sum these alongside every native segment.
_DEFINITIONS: tuple[
    tuple[
        str,
        type[CanonicalRecord],
        CapabilityKind,
        tuple[str, ...],
        tuple[str, ...],
        str | None,
        int,
        int,
    ],
    ...,
] = (
    (
        "projection",
        ResponseGeometryDevelopmentProjectionConfig,
        CapabilityKind.TRANSFORM,
        (ResponseGeometryDevelopmentNativeSegmentResult.SCHEMA, DEVELOPMENT_HDF5_SCHEMA),
        (ResponseGeometryDevelopmentViewReport.SCHEMA, DEVELOPMENT_DATA_SCHEMA),
        DEVELOPMENT_DATA_SCHEMA,
        120,
        32,
    ),
    (
        "development",
        ResponseGeometryDevelopmentMethodConfig,
        CapabilityKind.ANALYSIS,
        (
            ResponseGeometryDevelopmentViewReport.SCHEMA,
            DEVELOPMENT_DATA_SCHEMA,
            ResponseGeometryDevelopmentFitResult.SCHEMA,
            DEVELOPMENT_FIT_SCHEMA,
            ResponseGeometryDevelopmentCalibrationResult.SCHEMA,
        ),
        (ResponseGeometryDevelopmentFitResult.SCHEMA, DEVELOPMENT_FIT_SCHEMA, ResponseGeometryDevelopmentCalibrationResult.SCHEMA, ResponseGeometryDevelopmentSupportResult.SCHEMA),
        DEVELOPMENT_FIT_SCHEMA,
        28800,
        72,
    ),
    (
        "assessment",
        ResponseGeometryDevelopmentQualificationConfig,
        CapabilityKind.LAW_IDENTIFIER,
        (
            ResponseGeometryDevelopmentViewReport.SCHEMA,
            DEVELOPMENT_DATA_SCHEMA,
            ResponseGeometryDevelopmentFitResult.SCHEMA,
            DEVELOPMENT_FIT_SCHEMA,
            ResponseGeometryDevelopmentCalibrationResult.SCHEMA,
            ResponseGeometryDevelopmentSupportResult.SCHEMA,
        ),
        (ResponseGeometryDevelopmentContextResult.SCHEMA, DEVELOPMENT_VALIDATION_SCHEMA, ResponseGeometryDevelopmentGeometryReport.SCHEMA),
        DEVELOPMENT_VALIDATION_SCHEMA,
        28800,
        320,
    ),
    (
        "evaluation",
        ResponseGeometryDevelopmentCloseoutConfig,
        CapabilityKind.EVALUATOR,
        (ResponseGeometryDevelopmentContextResult.SCHEMA, DEVELOPMENT_VALIDATION_SCHEMA, ResponseGeometryDevelopmentGeometryReport.SCHEMA),
        (ResponseGeometryDevelopmentDevelopmentResult.SCHEMA, ScientificAdjudicationRecord.SCHEMA),
        None,
        120,
        8,
    ),
)

DEVELOPMENT_CAPABILITIES = tuple(
    manifest(
        role,
        config,
        kind,
        (config.SCHEMA, *inputs, _STAGE),
        (*outputs, _STAGE),
        EvidenceCeiling.LOCAL_LAW
        if role in ("assessment", "evaluation")
        else EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_REVEALED
        if role == "evaluation"
        else OutcomeAccess.DEVELOPMENT_VISIBLE,
        seconds,
        namespace=DEVELOPMENT_PANEL_ID,
        resources=ResourceBudget(
            1,
            8 * 1024**3,
            0,
            seconds,
            (2 if role in ("development", "assessment") else 1) * 1024**3,
            output_mib * 1024**2,
        ),
        read_permission=CapabilityPermission.READ_DEVELOPMENT,
        implementation_id="response-geometry-development-methods",
        conformance_ids=(
            "exact-d-root-role-cutoff",
            "no-native-effect-in-method",
            "retain-unavailable-models-and-independent-roots",
        ),
    )
    for role, config, kind, inputs, outputs, _, seconds, output_mib in _DEFINITIONS
)
_BUILT = tuple(
    bundle(
        role, ExtensionContributionKind.METHOD, capability, (config,), hdf5, namespace=DEVELOPMENT_PANEL_ID
    )
    for (role, config, _, _, _, hdf5, _, _), capability in zip(
        _DEFINITIONS, DEVELOPMENT_CAPABILITIES, strict=True
    )
)
DEVELOPMENT_COMPONENTS = tuple(components for _, components in _BUILT)
DEVELOPMENT_CONFIG_TYPES = tuple(definition[1] for definition in _DEFINITIONS)
DEVELOPMENT_ROLES = tuple(definition[0] for definition in _DEFINITIONS)
_CONTRIBUTIONS = tuple(value for value, _ in _BUILT)
_DISCOVERY_CONTRIBUTION = replace(
    _CONTRIBUTIONS[0],
    contribution_id=f"extension-contribution.{DEVELOPMENT_PANEL_ID}.methods",
    capability_manifests=tuple(sorted(DEVELOPMENT_CAPABILITIES, key=lambda v: v.registry_id)),
    candidate_capability_registrations=tuple(
        sorted(
            (v for c in _CONTRIBUTIONS for v in c.candidate_capability_registrations),
            key=lambda v: v.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (v for c in _CONTRIBUTIONS for v in c.profile_registrations),
            key=lambda v: v.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted((v for c in _CONTRIBUTIONS for v in c.config_decoders), key=lambda v: v.object_id)
    ),
    artifact_validators=tuple(
        sorted(
            (v for c in _CONTRIBUTIONS for v in c.artifact_validators), key=lambda v: v.object_id
        )
    ),
    runtime_providers=tuple(
        sorted((v for c in _CONTRIBUTIONS for v in c.runtime_providers), key=lambda v: v.object_id)
    ),
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.candidate_payloads import CandidatePayloadPlane
from empirical_lawhood.execution.providers import CampaignRuntimeProvider
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import executable
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_projection import ResponseGeometryDevelopmentProjectionConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_records import ResponseGeometryDevelopmentMethodConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_provider import ResponseGeometryDevelopmentDevelopmentProvider
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_terminal import ResponseGeometryDevelopmentQualificationConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_closeout import ResponseGeometryDevelopmentCloseoutConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_assessment_provider import ResponseGeometryDevelopmentAssessmentProvider, DEVELOPMENT_CANDIDATE_PAYLOAD_PORT


DEVELOPMENT_BINDINGS = tuple(
    replace(
        executable(capability, components, (kind,)),
        required_platform_port_keys=(DEVELOPMENT_CANDIDATE_PAYLOAD_PORT,)
        if kind is ResponseGeometryDevelopmentQualificationConfig
        else (),
    )
    for capability, components, kind in zip(
        DEVELOPMENT_CAPABILITIES, DEVELOPMENT_COMPONENTS, DEVELOPMENT_CONFIG_TYPES, strict=True
    )
)


@dataclass(frozen=True, slots=True)
class ResponseGeometryDevelopmentDevelopmentFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        index = DEVELOPMENT_BINDINGS.index(self.binding)
        if (
            len(records) != 1
            or type(records[0]) is not DEVELOPMENT_CONFIG_TYPES[index]
            or tuple(p.port_key for p in platform_ports) != self.binding.required_platform_port_keys
        ):
            raise ValueError("D method factory requires its one exact issued config")
        config = records[0]
        if isinstance(config, ResponseGeometryDevelopmentQualificationConfig):
            plane = platform_ports[0].port
            if not all(
                callable(getattr(plane, method, None))
                for method in ("publish_candidate_payload", "read_candidate_payload")
            ):
                raise TypeError("D assessment requires its bounded candidate publication/read port")
            return ResponseGeometryDevelopmentAssessmentProvider(
                registry, DEVELOPMENT_CAPABILITIES[index], config, cast(CandidatePayloadPlane, plane)
            )
        if isinstance(config, ResponseGeometryDevelopmentCloseoutConfig):
            return ResponseGeometryDevelopmentAssessmentProvider(registry, DEVELOPMENT_CAPABILITIES[index], config)
        assert isinstance(config, (ResponseGeometryDevelopmentProjectionConfig, ResponseGeometryDevelopmentMethodConfig))
        return ResponseGeometryDevelopmentDevelopmentProvider(registry, DEVELOPMENT_CAPABILITIES[index], config, DEVELOPMENT_ROLES[index])


_EXECUTABLE_BINDINGS = tuple(sorted(DEVELOPMENT_BINDINGS, key=lambda v: v.binding_id))
_EXECUTABLE_ID = "executable-contribution.response-geometry-development.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(
    ResponseGeometryDevelopmentDevelopmentFactory(b) for b in _EXECUTABLE_BINDINGS
)
_ISSUED_RECORD_TYPES = tuple(sorted(set(DEVELOPMENT_CONFIG_TYPES), key=lambda v: v.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['DEVELOPMENT_BINDINGS', 'DEVELOPMENT_CAPABILITIES', 'DEVELOPMENT_CONFIG_TYPES', 'DEVELOPMENT_ROLES', 'EXTENSION']

_EXECUTION_CONTRIBUTION = EXTENSION.executable
