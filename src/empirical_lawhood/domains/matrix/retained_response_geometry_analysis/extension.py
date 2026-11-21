# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.domains.matrix.response_geometry_prospective.development_continuation import RETAINED_ANALYSIS_RUN, ResponseGeometryDevelopmentAnalysisContinuationConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_records import DEVELOPMENT_FIT_SCHEMA
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_terminal import DEVELOPMENT_VALIDATION_SCHEMA
from empirical_lawhood.domains.matrix.response_geometry_development.extension import DEVELOPMENT_CAPABILITIES, DEVELOPMENT_CONFIG_TYPES, DEVELOPMENT_ROLES
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionComponentKind, ExtensionContributionKind

RETAINED_ANALYSIS_ROLES = ("development", "assessment", "evaluation")
RETAINED_ANALYSIS_CONFIG_TYPES = tuple(
    DEVELOPMENT_CONFIG_TYPES[DEVELOPMENT_ROLES.index(role)] for role in RETAINED_ANALYSIS_ROLES
)
RETAINED_ANALYSIS_CAPABILITIES = tuple(
    replace(
        DEVELOPMENT_CAPABILITIES[DEVELOPMENT_ROLES.index(role)],
        capability_key=f"{RETAINED_ANALYSIS_RUN}.{role}",
        runtime_id=f"{RETAINED_ANALYSIS_RUN}.{role}",
        input_schema_ids=tuple(
            sorted(
                (
                    *DEVELOPMENT_CAPABILITIES[DEVELOPMENT_ROLES.index(role)].input_schema_ids,
                    *(
                        (ResponseGeometryDevelopmentAnalysisContinuationConfig.SCHEMA,)
                        if role in ("development", "assessment")
                        else ()
                    ),
                )
            )
        ),
        implementation_sha256=sha256(
            f"{RETAINED_ANALYSIS_RUN}.{role}.retained-measurement-bindings".encode()
        ).hexdigest(),
        conformance_check_ids=(
            "exact-retained-development-custody-and-splits",
            "no-native-capability-or-task",
            "separate-analysis-input-publication",
            "unchanged-development-scientific-owners",
        ),
    )
    for role in RETAINED_ANALYSIS_ROLES
)
_BUILT = tuple(
    bundle(
        role,
        ExtensionContributionKind.METHOD,
        capability,
        (ResponseGeometryDevelopmentAnalysisContinuationConfig,),
        hdf5,
        namespace=RETAINED_ANALYSIS_RUN,
    )
    for role, capability, kind, hdf5 in zip(
        RETAINED_ANALYSIS_ROLES,
        RETAINED_ANALYSIS_CAPABILITIES,
        RETAINED_ANALYSIS_CONFIG_TYPES,
        (DEVELOPMENT_FIT_SCHEMA, DEVELOPMENT_VALIDATION_SCHEMA, None),
        strict=True,
    )
)
_SHARED_DECODER = next(
    value
    for value in _BUILT[0][1]
    if value.kind is ExtensionComponentKind.CONFIG_DECODER
)
RETAINED_ANALYSIS_COMPONENTS = tuple(
    (
        _SHARED_DECODER,
        *(
            value
            for value in components
            if value.kind is not ExtensionComponentKind.CONFIG_DECODER
        ),
    )
    for _, components in _BUILT
)
_CONTRIBUTIONS = tuple(
    replace(
        contribution, config_decoders=contribution.config_decoders if i == 0 else ()
    )
    for i, (contribution, _) in enumerate(_BUILT)
)
_DISCOVERY_CONTRIBUTION = replace(
    _CONTRIBUTIONS[0],
    contribution_id=f"extension-contribution.{RETAINED_ANALYSIS_RUN}.methods",
    capability_manifests=tuple(
        sorted(RETAINED_ANALYSIS_CAPABILITIES, key=lambda value: value.registry_id)
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                value
                for c in _CONTRIBUTIONS
                for value in c.candidate_capability_registrations
            ),
            key=lambda value: value.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (value for c in _CONTRIBUTIONS for value in c.profile_registrations),
            key=lambda value: value.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            (value for c in _CONTRIBUTIONS for value in c.config_decoders),
            key=lambda value: value.object_id,
        )
    ),
    artifact_validators=tuple(
        sorted(
            (value for c in _CONTRIBUTIONS for value in c.artifact_validators),
            key=lambda value: value.object_id,
        )
    ),
    runtime_providers=tuple(
        sorted(
            (value for c in _CONTRIBUTIONS for value in c.runtime_providers),
            key=lambda value: value.object_id,
        )
    ),
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.domains.matrix.response_geometry_prospective.development_assessment_provider import DEVELOPMENT_CANDIDATE_PAYLOAD_PORT, ResponseGeometryDevelopmentAssessmentProvider
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_closeout import ResponseGeometryDevelopmentCloseoutConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_continuation import RETAINED_ANALYSIS_RUN, ResponseGeometryDevelopmentAnalysisContinuationConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_continuation_provider import DEVELOPMENT_RETAINED_PROJECTION_SOURCE_PORT, ResponseGeometryDevelopmentAnalysisAssessmentProvider, ResponseGeometryDevelopmentAnalysisContinuationProvider, ResponseGeometryDevelopmentRetainedProjectionSourceFactory
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_records import ResponseGeometryDevelopmentMethodConfig
from empirical_lawhood.domains.matrix.response_geometry_prospective.development_terminal import ResponseGeometryDevelopmentQualificationConfig
from empirical_lawhood.domains.matrix.response_geometry_development.extension import DEVELOPMENT_BINDINGS
from empirical_lawhood.domains.matrix.response_geometry_development.extension import DEVELOPMENT_ROLES
from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.candidate_payloads import CandidatePayloadPlane
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.extension_bundles import ExtensionComponentKind
from empirical_lawhood.execution.providers import CampaignRuntimeProvider




def _binding(index: int) -> ExecutableCapabilityBinding:
    capability, components, kind = (
        RETAINED_ANALYSIS_CAPABILITIES[index],
        RETAINED_ANALYSIS_COMPONENTS[index],
        RETAINED_ANALYSIS_CONFIG_TYPES[index],
    )
    current = executable(capability, components, (ResponseGeometryDevelopmentAnalysisContinuationConfig,))
    original = DEVELOPMENT_BINDINGS[DEVELOPMENT_ROLES.index(RETAINED_ANALYSIS_ROLES[index])]
    if index != 0:
        return replace(
            current,
            discovery_components=tuple(
                sorted(
                    (
                        *(
                            value
                            for value in current.discovery_components
                            if value.kind is not ExtensionComponentKind.CONFIG_DECODER
                        ),
                        *(
                            value
                            for value in original.discovery_components
                            if value.kind is ExtensionComponentKind.CONFIG_DECODER
                        ),
                    ),
                    key=lambda value: value.registration_id,
                )
            ),
            accepted_config_types=original.accepted_config_types,
            required_issued_payload_schemas=original.required_issued_payload_schemas,
            codec_registration_identities=original.codec_registration_identities,
            issued_decoder_registrations=original.issued_decoder_registrations,
            required_platform_port_keys=tuple(
                sorted(
                    (
                        DEVELOPMENT_CANDIDATE_PAYLOAD_PORT,
                        f"{DEVELOPMENT_RETAINED_PROJECTION_SOURCE_PORT}.assessment",
                    )
                )
            )
            if kind is ResponseGeometryDevelopmentQualificationConfig
            else (),
        )
    return replace(
        current,
        discovery_components=tuple(
            sorted(
                (
                    *current.discovery_components,
                    *(
                        value
                        for value in original.discovery_components
                        if value.kind is ExtensionComponentKind.CONFIG_DECODER
                    ),
                ),
                key=lambda value: value.registration_id,
            )
        ),
        accepted_config_types=tuple(
            sorted(
                (*current.accepted_config_types, *original.accepted_config_types),
                key=lambda value: value.type_id,
            )
        ),
        required_issued_payload_schemas=tuple(
            sorted(
                (
                    *current.required_issued_payload_schemas,
                    *original.required_issued_payload_schemas,
                )
            )
        ),
        codec_registration_identities=tuple(
            sorted(
                (
                    *current.codec_registration_identities,
                    *original.codec_registration_identities,
                ),
                key=lambda value: value.object_id,
            )
        ),
        issued_decoder_registrations=tuple(
            sorted(
                (
                    *current.issued_decoder_registrations,
                    *original.issued_decoder_registrations,
                ),
                key=lambda value: value.registration_id,
            )
        ),
        required_platform_port_keys=tuple(
            sorted(
                (
                    f"{DEVELOPMENT_RETAINED_PROJECTION_SOURCE_PORT}.development",
                    *(
                        (DEVELOPMENT_CANDIDATE_PAYLOAD_PORT,)
                        if kind is ResponseGeometryDevelopmentQualificationConfig
                        else ()
                    ),
                )
            )
        )
        if kind is not ResponseGeometryDevelopmentCloseoutConfig
        else (),
    )


RETAINED_ANALYSIS_BINDINGS = tuple(_binding(index) for index in range(3))


@dataclass(frozen=True, slots=True)
class ResponseGeometryDevelopmentAnalysisContinuationFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        index = RETAINED_ANALYSIS_BINDINGS.index(self.binding)
        kind = RETAINED_ANALYSIS_CONFIG_TYPES[index]
        expected = {kind, ResponseGeometryDevelopmentAnalysisContinuationConfig} if index == 0 else {kind}
        if (
            len(records) != len(expected)
            or {type(record) for record in records} != expected
            or tuple(port.port_key for port in platform_ports)
            != self.binding.required_platform_port_keys
        ):
            raise ValueError(
                "development analysis factory requires exact scientific/custody records and bounded ports"
            )
        config = next(record for record in records if type(record) is kind)
        sources = plane = None
        ports = {port.port_key: port.port for port in platform_ports}
        if index in (0, 1):
            source_port = ports[
                f"{DEVELOPMENT_RETAINED_PROJECTION_SOURCE_PORT}.{RETAINED_ANALYSIS_ROLES[index]}"
            ]
            if not callable(getattr(source_port, "create_source", None)):
                raise TypeError(
                    "development analysis requires its nonexecuting retained-artifact source factory"
                )
            sources = cast(ResponseGeometryDevelopmentRetainedProjectionSourceFactory, source_port)
        if kind is ResponseGeometryDevelopmentQualificationConfig:
            candidate_port = ports[DEVELOPMENT_CANDIDATE_PAYLOAD_PORT]
            if not all(
                callable(getattr(candidate_port, name, None))
                for name in ("publish_candidate_payload", "read_candidate_payload")
            ):
                raise TypeError(
                    "development analysis requires the existing candidate artifact port"
                )
            plane = cast(CandidatePayloadPlane, candidate_port)
        assert isinstance(
            config, (ResponseGeometryDevelopmentMethodConfig, ResponseGeometryDevelopmentQualificationConfig, ResponseGeometryDevelopmentCloseoutConfig)
        )
        if isinstance(config, ResponseGeometryDevelopmentQualificationConfig):
            assert plane is not None and sources is not None
            return ResponseGeometryDevelopmentAnalysisAssessmentProvider(
                registry, RETAINED_ANALYSIS_CAPABILITIES[index], config, plane, sources
            )
        if isinstance(config, ResponseGeometryDevelopmentCloseoutConfig):
            return ResponseGeometryDevelopmentAssessmentProvider(
                registry, RETAINED_ANALYSIS_CAPABILITIES[index], config
            )
        continuation = next(
            record
            for record in records
            if isinstance(record, ResponseGeometryDevelopmentAnalysisContinuationConfig)
        )
        return ResponseGeometryDevelopmentAnalysisContinuationProvider(
            registry,
            RETAINED_ANALYSIS_CAPABILITIES[index],
            config,
            continuation,
            sources,
            plane,
        )


_EXECUTABLE_BINDINGS = tuple(sorted(RETAINED_ANALYSIS_BINDINGS, key=lambda value: value.binding_id))
_EXECUTABLE_ID = f"executable-contribution.{RETAINED_ANALYSIS_RUN}.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(
    ResponseGeometryDevelopmentAnalysisContinuationFactory(binding)
    for binding in _EXECUTABLE_BINDINGS
)
_ISSUED_RECORD_TYPES = (ResponseGeometryDevelopmentAnalysisContinuationConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'RETAINED_ANALYSIS_BINDINGS', 'RETAINED_ANALYSIS_CAPABILITIES', 'RETAINED_ANALYSIS_ROLES']

_EXECUTION_CONTRIBUTION = EXTENSION.executable
