# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import bundle, manifest
from empirical_lawhood.domains.matrix.six_matrix_response.response_development import DEVELOPMENT_PANEL_ID, DEVELOPMENT_HDF5_SCHEMA, ResponseGeometryDevelopmentNativeConfig, ResponseGeometryDevelopmentNativeSegmentResult

DEVELOPMENT_SOURCE_CAPABILITY = manifest(
    "source",
    ResponseGeometryDevelopmentNativeConfig,
    CapabilityKind.SIMULATOR,
    (
        ResponseGeometryDevelopmentNativeConfig.SCHEMA,
        ResponseGeometryDevelopmentNativeSegmentResult.SCHEMA,
        DEVELOPMENT_HDF5_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (ResponseGeometryDevelopmentNativeSegmentResult.SCHEMA, DEVELOPMENT_HDF5_SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    1800,
    namespace=DEVELOPMENT_PANEL_ID,
    resources=ResourceBudget(1, 3 * 1024**3, 0, 1800, 32 * 1024**2, 17 * 1024**2),
    read_permission=CapabilityPermission.READ_DEVELOPMENT,
    implementation_id="response-geometry-development-short-pulse-native-panel",
    conformance_ids=(
        "exact-d-native-roster",
        "no-scientific-retry",
        "separate-root-view-action-clocks",
    ),
)
_DISCOVERY_CONTRIBUTION, DEVELOPMENT_SOURCE_COMPONENTS = bundle(
    "source",
    ExtensionContributionKind.SOURCE,
    DEVELOPMENT_SOURCE_CAPABILITY,
    (ResponseGeometryDevelopmentNativeConfig,),
    DEVELOPMENT_HDF5_SCHEMA,
    namespace=DEVELOPMENT_PANEL_ID,
)


# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.plans import ProtocolTemplate
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.design.native_source import NativeSourceProfile, NativeLawQualificationConfig, NativeLawQualificationExperiment
from empirical_lawhood.execution.response_experiment_ports import ResponseSubstrateBinding
from empirical_lawhood.methods.control.backbone_linked_campaign.extension import NATIVE_RESPONSE_LAW_QUALIFICATION_DECODERS, NATIVE_RESPONSE_LAW_QUALIFICATION_DECODER_REGISTRATIONS, RESPONSE_SUBSTRATE_BINDING_DECODER
from empirical_lawhood.methods.control.backbone_linked_campaign.extension import RESPONSE_SUBSTRATE_BINDING_DECODER_REGISTRATION
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import executable
from empirical_lawhood.adapters.simulators.response_geometry_prospective.development_provider import ResponseGeometryDevelopmentSourceProvider
from empirical_lawhood.domains.matrix.six_matrix_response.response_development import ResponseGeometryDevelopmentNativeConfig



DEVELOPMENT_SOURCE_BINDING = executable(DEVELOPMENT_SOURCE_CAPABILITY, DEVELOPMENT_SOURCE_COMPONENTS, (ResponseGeometryDevelopmentNativeConfig,))
_SOURCE_RECORDS = (
    ResponseGeometryDevelopmentNativeConfig,
    NativeSourceProfile,
    NativeLawQualificationConfig,
    NativeLawQualificationExperiment,
    ResponseSubstrateBinding,
)
_SHARED_DECODERS = (*NATIVE_RESPONSE_LAW_QUALIFICATION_DECODERS, RESPONSE_SUBSTRATE_BINDING_DECODER)
DEVELOPMENT_SOURCE_BINDING = replace(
    DEVELOPMENT_SOURCE_BINDING,
    discovery_components=tuple(
        sorted((*DEVELOPMENT_SOURCE_COMPONENTS, *_SHARED_DECODERS), key=lambda d: d.registration_id)
    ),
    accepted_config_types=tuple(
        sorted(
            (ExecutableRecordTypeBinding(t.SCHEMA, t.VERSION) for t in _SOURCE_RECORDS),
            key=lambda t: t.type_id,
        )
    ),
    required_issued_payload_schemas=tuple(sorted(t.SCHEMA for t in _SOURCE_RECORDS)),
    codec_registration_identities=tuple(
        sorted(
            (
                *DEVELOPMENT_SOURCE_BINDING.codec_registration_identities,
                *(ObjectIdentity.from_record(d.registration_id, d) for d in _SHARED_DECODERS),
            ),
            key=lambda d: d.object_id,
        )
    ),
    issued_decoder_registrations=tuple(
        sorted(
            (
                *DEVELOPMENT_SOURCE_BINDING.issued_decoder_registrations,
                *NATIVE_RESPONSE_LAW_QUALIFICATION_DECODER_REGISTRATIONS,
                RESPONSE_SUBSTRATE_BINDING_DECODER_REGISTRATION,
            ),
            key=lambda d: d.registration_id,
        )
    ),
)


@dataclass(frozen=True, slots=True)
class ResponseGeometryDevelopmentSourceProviderFactory:
    binding: ExecutableCapabilityBinding = DEVELOPMENT_SOURCE_BINDING

    def expand_parameterised_protocol(
        self, *, records: tuple[CanonicalRecord, ...], template: ProtocolTemplate
    ) -> ProtocolTemplate:
        from empirical_lawhood.adapters.simulators.response_geometry_prospective.development_protocol import expand_response_geometry_development_protocol

        return expand_response_geometry_development_protocol(
            records=records,
            template=template,
            binding=ObjectIdentity.from_record(self.binding.binding_id, self.binding),
        )

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ResponseGeometryDevelopmentSourceProvider:
        from empirical_lawhood.adapters.simulators.response_geometry_prospective.development_protocol import validate_response_geometry_development_source_records

        if (
            platform_ports
            or len(records) != 5
            or {type(r) for r in records} != set(_SOURCE_RECORDS)
        ):
            raise ValueError("D native factory requires its five exact issued source records")
        config = validate_response_geometry_development_source_records(
            records, ObjectIdentity.from_record(self.binding.binding_id, self.binding)
        )
        return ResponseGeometryDevelopmentSourceProvider(registry, DEVELOPMENT_SOURCE_CAPABILITY, config)


_EXECUTABLE_ID = "executable-contribution.response-geometry-development.source"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ResponseGeometryDevelopmentSourceProviderFactory(),)
_ISSUED_RECORD_TYPES = (ResponseGeometryDevelopmentNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['DEVELOPMENT_SOURCE_BINDING', 'DEVELOPMENT_SOURCE_CAPABILITY', 'EXTENSION']
