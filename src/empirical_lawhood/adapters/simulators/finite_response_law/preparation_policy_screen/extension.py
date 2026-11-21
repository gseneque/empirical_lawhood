# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from empirical_lawhood.adapters.simulators.finite_response_law.preparation_policy_screen.discovery import EXTENSION_BUNDLE_CONTRIBUTION as _DISCOVERY_CONTRIBUTION


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.domains.matrix.finite_response_law.preparation_policy_projection import FiniteResponseLawPreparationPolicyProjectionConfig
from empirical_lawhood.domains.matrix.finite_response_law.preparation_policy_provider import FiniteResponseLawPreparationPolicyEvidenceSources, FiniteResponseLawPreparationPolicyMethodProvider, PREPARATION_POLICY_EVIDENCE_PORT
from empirical_lawhood.domains.matrix.finite_response_law.preparation_screen_results import FiniteResponseLawPreparationPolicyScreenConfig
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.source_qualification import PredecessorBoundSourceQualificationExperiment
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.extension_bundles import ExtensionComponentKind
from empirical_lawhood.execution.plans import ProtocolTemplate
from empirical_lawhood.execution.source_qualification import PredecessorBoundSourceQualificationSubstrateBinding

from empirical_lawhood.domains.matrix.finite_response_law.preparation_policy_contracts import FiniteResponseLawPreparationPolicyNativeConfig
from empirical_lawhood.adapters.simulators.finite_response_law.preparation_policy_provider import FiniteResponseLawPreparationPolicyRetainedSources, FiniteResponseLawPreparationPolicySourceProvider, PREPARATION_POLICY_RETAINED_SOURCE_PORT
from empirical_lawhood.adapters.simulators.finite_response_law.extension import SOURCE_BINDING as COMMON_SOURCE_BINDING
from empirical_lawhood.adapters.simulators.finite_response_law.preparation_policy_screen.discovery import EVALUATION_CAPABILITY, EVALUATION_COMPONENTS, NAMESPACE, PROJECTION_CAPABILITY, PROJECTION_COMPONENTS, SOURCE_CAPABILITY, SOURCE_COMPONENTS, SOURCE_RECORDS
from empirical_lawhood.adapters.simulators.finite_response_law.preparation_policy_screen.protocol import preparation_policy_protocol_steps, validate_preparation_policy_source_records

_new_source = executable(SOURCE_CAPABILITY, SOURCE_COMPONENTS, (FiniteResponseLawPreparationPolicyNativeConfig,))
_shared_schemas = {
    PredecessorBoundSourceQualificationExperiment.SCHEMA,
    PredecessorBoundSourceQualificationSubstrateBinding.SCHEMA,
}
_shared_components = tuple(
    component
    for component in COMMON_SOURCE_BINDING.discovery_components
    if component.kind is ExtensionComponentKind.CONFIG_DECODER
    and set(component.input_schema_ids) <= _shared_schemas
)
SOURCE_BINDING = replace(
    _new_source,
    discovery_components=tuple(
        sorted(
            (*_new_source.discovery_components, *_shared_components),
            key=lambda component: component.registration_id,
        )
    ),
    accepted_config_types=tuple(
        sorted(
            (
                *_new_source.accepted_config_types,
                *(
                    record
                    for record in COMMON_SOURCE_BINDING.accepted_config_types
                    if record.record_schema in _shared_schemas
                ),
            ),
            key=lambda record: record.record_schema,
        )
    ),
    required_issued_payload_schemas=tuple(
        sorted((*_new_source.required_issued_payload_schemas, *_shared_schemas))
    ),
    codec_registration_identities=tuple(
        sorted(
            (
                *_new_source.codec_registration_identities,
                *(
                    ObjectIdentity.from_record(component.registration_id, component)
                    for component in _shared_components
                ),
            ),
            key=lambda identity: identity.object_id,
        )
    ),
    issued_decoder_registrations=tuple(
        sorted(
            (
                *_new_source.issued_decoder_registrations,
                *(
                    decoder
                    for decoder in COMMON_SOURCE_BINDING.issued_decoder_registrations
                    if decoder.payload_schema in _shared_schemas
                ),
            ),
            key=lambda decoder: decoder.registration_id,
        )
    ),
    required_platform_port_keys=(PREPARATION_POLICY_RETAINED_SOURCE_PORT,),
)
PROJECTION_BINDING = executable(
    PROJECTION_CAPABILITY, PROJECTION_COMPONENTS, (FiniteResponseLawPreparationPolicyProjectionConfig,)
)
EVALUATION_BINDING = replace(
    executable(EVALUATION_CAPABILITY, EVALUATION_COMPONENTS, (FiniteResponseLawPreparationPolicyScreenConfig,)),
    required_platform_port_keys=(PREPARATION_POLICY_EVIDENCE_PORT,),
)


@dataclass(frozen=True, slots=True)
class FiniteResponseLawPreparationPolicySourceFactory:
    binding: ExecutableCapabilityBinding = SOURCE_BINDING

    def _records(
        self, records: tuple[CanonicalRecord, ...]
    ) -> tuple[
        FiniteResponseLawPreparationPolicyNativeConfig,
        PredecessorBoundSourceQualificationExperiment,
        PredecessorBoundSourceQualificationSubstrateBinding,
    ]:
        by_type = {type(record): record for record in records}
        if (
            self.binding != SOURCE_BINDING
            or len(by_type) != len(records)
            or set(by_type) != set(SOURCE_RECORDS)
        ):
            raise ValueError("preparation-policy development source requires its exact decoded record roster")
        config = cast(FiniteResponseLawPreparationPolicyNativeConfig, by_type[FiniteResponseLawPreparationPolicyNativeConfig])
        carrier = cast(PredecessorBoundSourceQualificationExperiment, by_type[PredecessorBoundSourceQualificationExperiment])
        association = cast(
            PredecessorBoundSourceQualificationSubstrateBinding,
            by_type[PredecessorBoundSourceQualificationSubstrateBinding],
        )
        validate_preparation_policy_source_records(
            config,
            carrier,
            association,
            ObjectIdentity.from_record(SOURCE_BINDING.binding_id, SOURCE_BINDING),
        )
        return config, carrier, association

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteResponseLawPreparationPolicySourceProvider:
        if tuple(port.port_key for port in platform_ports) != (PREPARATION_POLICY_RETAINED_SOURCE_PORT,):
            raise ValueError("preparation-policy development source lacks its exact retained-prefix port")
        config, carrier, _ = self._records(records)
        sources = cast(FiniteResponseLawPreparationPolicyRetainedSources, platform_ports[0].port)
        expected = tuple(
            sorted(
                (
                    artifact
                    for row in config.retained_prefixes
                    for artifact in (*row.declaration.artifacts, row.declaration.task_receipt)
                ),
                key=lambda artifact: artifact.artifact_id,
            )
        )
        if sources.artifacts != expected:
            raise ValueError("preparation-policy development source port changes the retained-prefix inventory")
        return FiniteResponseLawPreparationPolicySourceProvider(
            registry, SOURCE_CAPABILITY, config, carrier, sources
        )

    def expand_parameterised_protocol(
        self, *, records: tuple[CanonicalRecord, ...], template: ProtocolTemplate
    ) -> ProtocolTemplate:
        by_type = {type(record): record for record in records}
        required = {
            *SOURCE_RECORDS,
            FiniteResponseLawPreparationPolicyProjectionConfig,
            FiniteResponseLawPreparationPolicyScreenConfig,
        }
        if len(by_type) != len(records) or set(by_type) != required:
            raise ValueError("preparation-policy development expansion requires its exact source and method records")
        config, carrier, _ = self._records(
            tuple(record for record in records if type(record) in SOURCE_RECORDS)
        )
        projection = cast(FiniteResponseLawPreparationPolicyProjectionConfig, by_type[FiniteResponseLawPreparationPolicyProjectionConfig])
        evaluation = cast(FiniteResponseLawPreparationPolicyScreenConfig, by_type[FiniteResponseLawPreparationPolicyScreenConfig])
        return replace(
            template,
            template_id=f"{template.template_id}.{carrier.fingerprint()[:16]}",
            steps=preparation_policy_protocol_steps(config, carrier, projection, evaluation),
            requires_model_set=False,
            requests_controller=False,
            nonactuating=True,
        )


@dataclass(frozen=True, slots=True)
class FiniteResponseLawPreparationPolicyMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteResponseLawPreparationPolicyMethodProvider:
        if len(records) != 1:
            raise ValueError("preparation-policy development method requires one exact issued configuration")
        config = records[0]
        if self.binding == PROJECTION_BINDING and type(config) is FiniteResponseLawPreparationPolicyProjectionConfig:
            if platform_ports:
                raise ValueError("preparation-policy development projection accepts no additional platform port")
            return FiniteResponseLawPreparationPolicyMethodProvider(registry, PROJECTION_CAPABILITY, config)
        if self.binding == EVALUATION_BINDING and type(config) is FiniteResponseLawPreparationPolicyScreenConfig:
            if tuple(port.port_key for port in platform_ports) != (PREPARATION_POLICY_EVIDENCE_PORT,):
                raise ValueError("preparation-policy development screen lacks its exact lower/finite response-law evaluation evidence port")
            return FiniteResponseLawPreparationPolicyMethodProvider(
                registry,
                EVALUATION_CAPABILITY,
                config,
                cast(FiniteResponseLawPreparationPolicyEvidenceSources, platform_ports[0].port),
            )
        raise ValueError("preparation-policy development method changes its registered binding/configuration")


_EXECUTABLE_ID = f"executable-contribution.{NAMESPACE}"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (
    FiniteResponseLawPreparationPolicySourceFactory(),
    FiniteResponseLawPreparationPolicyMethodFactory(PROJECTION_BINDING),
    FiniteResponseLawPreparationPolicyMethodFactory(EVALUATION_BINDING),
)
_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (
    FiniteResponseLawPreparationPolicyNativeConfig,
    FiniteResponseLawPreparationPolicyProjectionConfig,
    FiniteResponseLawPreparationPolicyScreenConfig,
)
_ISSUED_RECORD_TYPES = tuple(sorted(_RECORD_TYPES, key=lambda record: record.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EVALUATION_BINDING', 'EXTENSION', 'PROJECTION_BINDING', 'SOURCE_BINDING']
