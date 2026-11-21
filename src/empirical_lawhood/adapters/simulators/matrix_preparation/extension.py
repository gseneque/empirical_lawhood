# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.declaration_helpers import bundle, manifest
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import DEVELOPMENT, NATIVE_SCHEMA, PreparationNativeResult, PreparationSourceConfig, PREFIX_BUNDLE_SCHEMA
from empirical_lawhood.domains.matrix.matrix_preparation.native_continuation import PreparationDevelopmentContinuation


SOURCE_CAPABILITY = manifest(
    "source",
    PreparationSourceConfig,
    CapabilityKind.SIMULATOR,
    (PreparationSourceConfig.SCHEMA, PREFIX_BUNDLE_SCHEMA),
    (PreparationNativeResult.SCHEMA, NATIVE_SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.DEVELOPMENT_VISIBLE,
    3600,
    namespace=DEVELOPMENT,
    resources=ResourceBudget(1, 2 * 1024**3, 0, 3600, 8 * 1024**2, 98 * 1024**2),
    read_permission=CapabilityPermission.READ_DEVELOPMENT,
    implementation_id="matrix-preparation-native-root-bundles-and-custodied-development-completion",
    conformance_ids=(
        "common-preparent-mode",
        "exact-parent-audit-task-view-roster",
        "exposed-root-prefix-custody",
        "independent-audit-task-purposes",
        "no-scientific-retry",
    ),
)
_DISCOVERY_CONTRIBUTION, SOURCE_COMPONENTS = bundle(
    "source",
    ExtensionContributionKind.SOURCE,
    SOURCE_CAPABILITY,
    (PreparationSourceConfig, PreparationDevelopmentContinuation),
    NATIVE_SCHEMA,
    namespace=DEVELOPMENT,
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.native_source import NativeLawQualificationConfig, NativeLawQualificationExperiment, NativeSourceProfile
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.response_experiment_ports import ResponseSubstrateBinding
from empirical_lawhood.execution.plans import ProtocolTemplate
from empirical_lawhood.methods.control.backbone_linked_campaign.extension import RESPONSE_SUBSTRATE_BINDING_DECODER_REGISTRATION
from empirical_lawhood.methods.control.backbone_linked_campaign.extension import NATIVE_RESPONSE_LAW_QUALIFICATION_DECODERS as NATIVE_LAW_DECODERS, NATIVE_RESPONSE_LAW_QUALIFICATION_DECODER_REGISTRATIONS as NATIVE_LAW_DECODER_REGISTRATIONS, RESPONSE_SUBSTRATE_BINDING_DECODER
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import DEVELOPMENT, PreparationSourceConfig
from empirical_lawhood.domains.matrix.matrix_preparation.native_continuation import PreparationDevelopmentContinuation, preparation_continuation

from empirical_lawhood.adapters.simulators.matrix_preparation.provider import PREFIX_SOURCE_PORT, PreparationPrefixSourceFactory, PreparationSourceProvider


_SOURCE_RECORDS = (
    PreparationSourceConfig,
    NativeSourceProfile,
    NativeLawQualificationConfig,
    NativeLawQualificationExperiment,
    ResponseSubstrateBinding,
)
_SHARED_DECODERS = (*NATIVE_LAW_DECODERS, RESPONSE_SUBSTRATE_BINDING_DECODER)
_BASE = executable(
    SOURCE_CAPABILITY,
    SOURCE_COMPONENTS,
    (PreparationSourceConfig, PreparationDevelopmentContinuation),
)
SOURCE_BINDING = replace(
    _BASE,
    discovery_components=tuple(
        sorted((*SOURCE_COMPONENTS, *_SHARED_DECODERS), key=lambda d: d.registration_id)
    ),
    accepted_config_types=tuple(
        sorted(
            (
                ExecutableRecordTypeBinding(t.SCHEMA, t.VERSION)
                for t in (*_SOURCE_RECORDS, PreparationDevelopmentContinuation)
            ),
            key=lambda t: t.type_id,
        )
    ),
    required_issued_payload_schemas=tuple(sorted(t.SCHEMA for t in _SOURCE_RECORDS)),
    codec_registration_identities=tuple(
        sorted(
            (
                *_BASE.codec_registration_identities,
                *(ObjectIdentity.from_record(d.registration_id, d) for d in _SHARED_DECODERS),
            ),
            key=lambda r: r.object_id,
        )
    ),
    issued_decoder_registrations=tuple(
        sorted(
            (
                *_BASE.issued_decoder_registrations,
                *NATIVE_LAW_DECODER_REGISTRATIONS,
                RESPONSE_SUBSTRATE_BINDING_DECODER_REGISTRATION,
            ),
            key=lambda r: r.registration_id,
        )
    ),
    required_platform_port_keys=(PREFIX_SOURCE_PORT,),
)


@dataclass(frozen=True, slots=True)
class PreparationSourceFactory:
    binding: ExecutableCapabilityBinding = SOURCE_BINDING

    def expand_parameterised_protocol(
        self, *, records: tuple[CanonicalRecord, ...], template: ProtocolTemplate
    ) -> ProtocolTemplate:
        from empirical_lawhood.domains.matrix.matrix_preparation.native_protocol import expand_preparation_protocol

        return expand_preparation_protocol(
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
    ) -> PreparationSourceProvider:
        from empirical_lawhood.domains.matrix.matrix_preparation.native_protocol import validate_preparation_source_records

        continuation = preparation_continuation(records)
        expected = (
            *_SOURCE_RECORDS,
            *((PreparationDevelopmentContinuation,) if continuation else ()),
        )
        if (
            len(records) != len(expected)
            or {type(r) for r in records} != set(expected)
            or tuple(p.port_key for p in platform_ports) != (PREFIX_SOURCE_PORT,)
        ):
            raise ValueError(
                "preparation source factory requires its exact typed records and retained-input port"
            )
        source = validate_preparation_source_records(
            records, ObjectIdentity.from_record(self.binding.binding_id, self.binding)
        )
        port = platform_ports[0].port
        if (
            not hasattr(port, "prefixes")
            or not hasattr(port, "prefix_bundles")
            or not callable(getattr(port, "create_source", None))
        ):
            raise TypeError("preparation source requires bounded lazy prefix discovery")
        if continuation is not None:
            continuation.validate_source(source)
        return PreparationSourceProvider(
            registry,
            SOURCE_CAPABILITY,
            source,
            cast(PreparationPrefixSourceFactory, port),
            continuation=continuation,
        )


_EXECUTABLE_ID = f"executable-contribution.{DEVELOPMENT}.source"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (PreparationSourceFactory(),)
_ISSUED_RECORD_TYPES = (PreparationSourceConfig, PreparationDevelopmentContinuation)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'SOURCE_BINDING', 'SOURCE_CAPABILITY']
