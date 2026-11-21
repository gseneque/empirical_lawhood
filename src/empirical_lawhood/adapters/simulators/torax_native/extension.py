# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



import hashlib

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.source_pipelines import SourcePipelineProfile
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from empirical_lawhood.execution.datasets import DatasetCapabilityLimits, DatasetCapabilityRegistry, DatasetTransformRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.profile_compilation import SourceProfileCompilerBinding


_PLANNING_IMPLEMENTATION_SHA256 = (
    "7d91f9feacc1e490242e2a5f6d59d28fdcc3fd4b559ae2f8c5a1b5c2a463f565"
)
_RUNTIME_IMPLEMENTATION_SHA256 = (
    "21787c7629fd4d6a5ae8e42a268e7d38c17dfec36793cae3c7b2da538a36831e"
)
_CONFIG_SCHEMA = 'empirical-lawhood/simulators/torax-native/source-normalization'


SOURCE_PIPELINE_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    registration_id="profile-registration.source-pipeline",
    profile_key="source-pipeline",
    profile_version="1.0.0",
    kind=ExtensionProfileKind.SOURCE_PIPELINE,
    profile_schema=SourcePipelineProfile.SCHEMA,
    profile_schema_sha256=hashlib.sha256(
        SourcePipelineProfile.SCHEMA.encode()
    ).hexdigest(),
    implementation_sha256=_PLANNING_IMPLEMENTATION_SHA256,
)

SOURCE_TRANSFORM_MANIFEST = CapabilityManifest(
    capability_key="source-pipeline.registered-transform",
    capability_version="1.0.0",
    kind=CapabilityKind.TRANSFORM,
    config_schema=_CONFIG_SCHEMA,
    config_schema_sha256=hashlib.sha256(_CONFIG_SCHEMA.encode()).hexdigest(),
    input_schema_ids=('empirical-lawhood/evidence/native-source',),
    output_schema_ids=('empirical-lawhood/evidence/canonical-source',),
    permissions=(
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.OUTCOME_BLIND,
    resource_ceiling=ResourceBudget(
        cpu_cores=4,
        memory_bytes=8 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=3_600,
        source_scan_bytes=8 * 1024**3,
        output_bytes=8 * 1024**3,
    ),
    deterministic=True,
    seed_required=False,
    language_id="python",
    runtime_id="cpython-source-pipeline",
    requires_clean_commit=True,
    requires_active_mount=True,
    requires_network=False,
    conformance_check_ids=(
        "bounded-registered-edge-chain",
        "native-coordinate-preservation",
        "physical-unit-and-invalid-row-accounting",
        "receipt-first-recovery",
    ),
    implementation_sha256=_RUNTIME_IMPLEMENTATION_SHA256,
)

TORAX_SIMULATED_SOURCE_MANIFEST = CapabilityManifest(
    capability_key="torax-native.simulated-source",
    capability_version="1.0.0",
    kind=CapabilityKind.SOURCE,
    config_schema=_CONFIG_SCHEMA,
    config_schema_sha256=hashlib.sha256(_CONFIG_SCHEMA.encode()).hexdigest(),
    input_schema_ids=(),
    output_schema_ids=('empirical-lawhood/evidence/native-source',),
    permissions=(),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.OUTCOME_BLIND,
    resource_ceiling=SOURCE_TRANSFORM_MANIFEST.resource_ceiling,
    deterministic=False,
    seed_required=True,
    language_id="python",
    runtime_id="torax-native-source",
    requires_clean_commit=True,
    requires_active_mount=False,
    requires_network=False,
    conformance_check_ids=(
        "adapter-owned-realization",
        "native-clock-unit-frame-preservation",
    ),
    implementation_sha256=_RUNTIME_IMPLEMENTATION_SHA256,
)

SOURCE_DATASET_CAPABILITY_REGISTRY = DatasetCapabilityRegistry(
    registry_id="dataset-registry.backbone-source-pipeline",
    providers=(),
    inspectors=(),
    transforms=(
        DatasetTransformRegistration(
            capability=SOURCE_TRANSFORM_MANIFEST,
            accepted_media_types=("application/octet-stream",),
            produced_media_types=("application/vnd.apache.parquet",),
            source_format_profile_ids=("native-source",),
            destination_format_profile_ids=('canonical-source',),
            limits=DatasetCapabilityLimits(
                max_input_bytes=8 * 1024**3,
                max_output_bytes=8 * 1024**3,
                max_records=10_000_000,
                max_files=10_000,
                max_archive_members=100_000,
            ),
        ),
    ),
    binding_compilers=(),
    storage_verifiers=(),
    evidence_verifiers=(),
)

SOURCE_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.source-pipeline-config-decoder",
    component_key="source-pipeline-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(SourcePipelineProfile.SCHEMA,),
    output_schema_ids=(SourcePipelineProfile.SCHEMA,),
    implementation_sha256=_PLANNING_IMPLEMENTATION_SHA256,
)

SOURCE_ARTIFACT_VALIDATOR = ExtensionComponentRegistration(
    registration_id="component.source-pipeline-artifact-validator",
    component_key="source-pipeline-artifact-validator",
    component_version="1.0.0",
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    input_schema_ids=('empirical-lawhood/evidence/canonical-source',),
    output_schema_ids=('empirical-lawhood/runtime/artifact-generic-validation',),
    implementation_sha256=_RUNTIME_IMPLEMENTATION_SHA256,
)

TORAX_SIMULATED_SOURCE_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.torax-simulated-source-provider",
    component_key="torax-simulated-source-provider",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=(SourcePipelineProfile.SCHEMA,),
    output_schema_ids=TORAX_SIMULATED_SOURCE_MANIFEST.output_schema_ids,
    implementation_sha256=_RUNTIME_IMPLEMENTATION_SHA256,
)

TORAX_SOURCE_PROFILE_COMPILER = ExtensionComponentRegistration(
    registration_id="component.torax-source-profile-compiler",
    component_key="torax-source-profile-compiler",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=(),
    output_schema_ids=(SourceProfileCompilerBinding.SCHEMA,),
    implementation_sha256=_RUNTIME_IMPLEMENTATION_SHA256,
)

_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.torax-native-source",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.SOURCE,
    evidence_profile_registries=(),
    capability_manifests=(SOURCE_TRANSFORM_MANIFEST, TORAX_SIMULATED_SOURCE_MANIFEST),
    candidate_capability_registrations=(),
    dataset_capability_registries=(SOURCE_DATASET_CAPABILITY_REGISTRY,),
    profile_registrations=(SOURCE_PIPELINE_PROFILE_REGISTRATION,),
    method_registrations=(),
    config_decoders=(
        ObjectIdentity.from_record(
            SOURCE_CONFIG_DECODER.registration_id,
            SOURCE_CONFIG_DECODER,
        ),
    ),
    artifact_validators=(
        ObjectIdentity.from_record(
            SOURCE_ARTIFACT_VALIDATOR.registration_id,
            SOURCE_ARTIFACT_VALIDATOR,
        ),
    ),
    runtime_providers=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in (TORAX_SIMULATED_SOURCE_PROVIDER, TORAX_SOURCE_PROFILE_COMPILER)
    ),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
import hashlib
from typing import cast

from empirical_lawhood.science.identity.authority import ResourceBudget, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.design.source_pipelines import SourcePipelineProfile
from empirical_lawhood.execution.datasets import DatasetCapabilityRegistry, DatasetTransformRegistration
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableFactory, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.profile_compilation import SourceProfileCompilerBinding
from empirical_lawhood.execution.sources import SourceCapabilityManifest, SourceMode




_MAXIMUM_SOURCE_PROFILE_BYTES = 4 * 1024 * 1024
_DECODER_CONFIG_SHA256 = hashlib.sha256(
    canonical_json_bytes(
        {
            "decoder_key": SOURCE_CONFIG_DECODER.component_key,
            "decoder_version": SOURCE_CONFIG_DECODER.component_version,
            "mode": "exact-canonical-record",
            "payload_schema": SourcePipelineProfile.SCHEMA,
        }
    )
).hexdigest()

SOURCE_PIPELINE_PROFILE_DECODER_REGISTRATION = StudyExtensionDecoderRegistration(
    registration_id="decoder-registration.source-pipeline-profile",
    decoder_key=SOURCE_CONFIG_DECODER.component_key,
    decoder_version=SOURCE_CONFIG_DECODER.component_version,
    payload_schema=SourcePipelineProfile.SCHEMA,
    payload_version=SourcePipelineProfile.VERSION,
    config_sha256=_DECODER_CONFIG_SHA256,
    implementation_sha256=SOURCE_CONFIG_DECODER.implementation_sha256,
    maximum_payload_bytes=_MAXIMUM_SOURCE_PROFILE_BYTES,
)

SOURCE_TRANSFORM_EXECUTABLE_BINDING = ExecutableCapabilityBinding(
    binding_id="binding.source-pipeline-registered-transform",
    capability_key=SOURCE_TRANSFORM_MANIFEST.capability_key,
    capability_version=SOURCE_TRANSFORM_MANIFEST.capability_version,
    capability_implementation_sha256=SOURCE_TRANSFORM_MANIFEST.implementation_sha256,
    role=ExecutableBindingRole.SOURCE_PROVIDER,
    provider_key="source-pipeline.registered-transform-selection",
    provider_version="1.0.0",
    provider_implementation_sha256=SOURCE_TRANSFORM_MANIFEST.implementation_sha256,
    capability_backed=True,
    discovery_components=tuple(
        sorted(
            (SOURCE_ARTIFACT_VALIDATOR, SOURCE_CONFIG_DECODER),
            key=lambda value: value.registration_id,
        )
    ),
    accepted_profile_types=(
        ExecutableRecordTypeBinding(
            record_schema=SourcePipelineProfile.SCHEMA,
            record_version=SourcePipelineProfile.VERSION,
        ),
    ),
    accepted_config_types=(
        ExecutableRecordTypeBinding(
            record_schema=SOURCE_TRANSFORM_MANIFEST.config_schema,
            record_version="1.0.0",
        ),
    ),
    required_issued_payload_schemas=(SourcePipelineProfile.SCHEMA,),
    codec_registration_identities=(
        ObjectIdentity.from_record(
            SOURCE_CONFIG_DECODER.registration_id,
            SOURCE_CONFIG_DECODER,
        ),
    ),
    issued_decoder_registrations=(SOURCE_PIPELINE_PROFILE_DECODER_REGISTRATION,),
    input_schema_ids=SOURCE_TRANSFORM_MANIFEST.input_schema_ids,
    output_schema_ids=SOURCE_TRANSFORM_MANIFEST.output_schema_ids,
    artifact_validator_identities=(
        ObjectIdentity.from_record(
            SOURCE_ARTIFACT_VALIDATOR.registration_id,
            SOURCE_ARTIFACT_VALIDATOR,
        ),
    ),
    required_platform_port_keys=(),
    may_require_active_mount=True,
    may_require_source_qualification=True,
    may_require_network=False,
    may_require_authority=True,
)

TORAX_SIMULATED_SOURCE_EXECUTABLE_BINDING = ExecutableCapabilityBinding(
    binding_id="binding.torax-simulated-source",
    capability_key=TORAX_SIMULATED_SOURCE_MANIFEST.capability_key,
    capability_version=TORAX_SIMULATED_SOURCE_MANIFEST.capability_version,
    capability_implementation_sha256=TORAX_SIMULATED_SOURCE_MANIFEST.implementation_sha256,
    role=ExecutableBindingRole.SOURCE_PROVIDER,
    provider_key=TORAX_SIMULATED_SOURCE_PROVIDER.component_key,
    provider_version=TORAX_SIMULATED_SOURCE_PROVIDER.component_version,
    provider_implementation_sha256=TORAX_SIMULATED_SOURCE_PROVIDER.implementation_sha256,
    capability_backed=True,
    discovery_components=(TORAX_SIMULATED_SOURCE_PROVIDER,),
    accepted_profile_types=(
        ExecutableRecordTypeBinding(
            SourcePipelineProfile.SCHEMA,
            SourcePipelineProfile.VERSION,
        ),
    ),
    accepted_config_types=(
        ExecutableRecordTypeBinding(
            TORAX_SIMULATED_SOURCE_MANIFEST.config_schema,
            "1.0.0",
        ),
    ),
    required_issued_payload_schemas=(),
    codec_registration_identities=(),
    issued_decoder_registrations=(),
    input_schema_ids=TORAX_SIMULATED_SOURCE_MANIFEST.input_schema_ids,
    output_schema_ids=TORAX_SIMULATED_SOURCE_MANIFEST.output_schema_ids,
    artifact_validator_identities=(),
    required_platform_port_keys=(),
    may_require_active_mount=False,
    may_require_source_qualification=True,
    may_require_network=False,
    may_require_authority=True,
)

TORAX_SOURCE_PROFILE_COMPILER_EXECUTABLE_BINDING = ExecutableCapabilityBinding(
    binding_id="binding.torax-source-profile-compiler",
    capability_key=TORAX_SOURCE_PROFILE_COMPILER.component_key,
    capability_version=TORAX_SOURCE_PROFILE_COMPILER.component_version,
    capability_implementation_sha256=TORAX_SOURCE_PROFILE_COMPILER.implementation_sha256,
    role=ExecutableBindingRole.PROFILE_COMPILER,
    provider_key=TORAX_SOURCE_PROFILE_COMPILER.component_key,
    provider_version=TORAX_SOURCE_PROFILE_COMPILER.component_version,
    provider_implementation_sha256=TORAX_SOURCE_PROFILE_COMPILER.implementation_sha256,
    capability_backed=False,
    discovery_components=(TORAX_SOURCE_PROFILE_COMPILER,),
    accepted_profile_types=(),
    accepted_config_types=(),
    required_issued_payload_schemas=(),
    codec_registration_identities=(),
    issued_decoder_registrations=(),
    input_schema_ids=(),
    output_schema_ids=TORAX_SOURCE_PROFILE_COMPILER.output_schema_ids,
    artifact_validator_identities=(),
    required_platform_port_keys=(),
    may_require_active_mount=False,
    may_require_source_qualification=False,
    may_require_network=False,
    may_require_authority=False,
)


@dataclass(frozen=True, slots=True)
class RegisteredSourceTransformSelection:
    """Exact static transform selection; deliberately not a source adapter."""

    profile: SourcePipelineProfile
    transform: DatasetTransformRegistration
    dataset_registry: DatasetCapabilityRegistry
    source_read: bool = False
    executable_runner_installed: bool = False

    def __post_init__(self) -> None:
        if self.source_read or self.executable_runner_installed:
            raise ValueError("static source-transform selection overclaims execution")


@dataclass(frozen=True, slots=True)
class RegisteredSourceTransformFactory:
    """Authenticate profile selection without acquiring or transforming bytes."""

    binding: ExecutableCapabilityBinding = SOURCE_TRANSFORM_EXECUTABLE_BINDING

    def build_source_provider(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> RegisteredSourceTransformSelection:
        if platform_ports:
            raise ValueError("registered source-transform selection accepts no ports")
        if len(records) != 1 or not isinstance(records[0], SourcePipelineProfile):
            raise ValueError("source-transform factory requires one exact source profile")
        profile = records[0]
        transform = SOURCE_DATASET_CAPABILITY_REGISTRY.transforms[0]
        matching_edges = tuple(
            edge
            for edge in profile.transform_edges
            if edge.selection.capability_key == self.binding.capability_key
            and edge.selection.capability_version == self.binding.capability_version
            and edge.selection.implementation_sha256
            == self.binding.capability_implementation_sha256
            and edge.dataset_transform_registry_id == transform.registry_id
            and edge.config.object_schema == SOURCE_TRANSFORM_MANIFEST.config_schema
        )
        if not matching_edges:
            raise ValueError("source profile does not select the installed transform")
        return RegisteredSourceTransformSelection(
            profile=profile,
            transform=transform,
            dataset_registry=SOURCE_DATASET_CAPABILITY_REGISTRY,
        )


@dataclass(frozen=True, slots=True)
class RegisteredToraxSimulatedSourceSelection:
    profile: SourcePipelineProfile
    source_contacted: bool = False


@dataclass(frozen=True, slots=True)
class ToraxSimulatedSourceFactory:
    binding: ExecutableCapabilityBinding = TORAX_SIMULATED_SOURCE_EXECUTABLE_BINDING

    def build_source_provider(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> RegisteredToraxSimulatedSourceSelection:
        if (
            platform_ports
            or len(records) != 1
            or not isinstance(
                records[0],
                SourcePipelineProfile,
            )
        ):
            raise ValueError("TORAX source selection requires one exact profile and no ports")
        profile = records[0]
        selection = profile.source_selection
        if (
            profile.mode.value != "SIMULATED"
            or selection.capability_key != self.binding.capability_key
            or selection.capability_version != self.binding.capability_version
            or selection.implementation_sha256 != self.binding.capability_implementation_sha256
        ):
            raise ValueError("TORAX source profile changes the installed simulation binding")
        return RegisteredToraxSimulatedSourceSelection(profile)


@dataclass(frozen=True, slots=True)
class ToraxSourceProfileCompilerFactory:
    binding: ExecutableCapabilityBinding = TORAX_SOURCE_PROFILE_COMPILER_EXECUTABLE_BINDING

    def build_compiler(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> SourceProfileCompilerBinding:
        if records or platform_ports:
            raise ValueError("TORAX source compiler context is input-free")
        source = SourceCapabilityManifest(
            capability_key=TORAX_SIMULATED_SOURCE_MANIFEST.capability_key,
            capability_version=TORAX_SIMULATED_SOURCE_MANIFEST.capability_version,
            mode=SourceMode.SIMULATED,
            source_access=SourceAccessClass.NONE,
            output_schema_ids=TORAX_SIMULATED_SOURCE_MANIFEST.output_schema_ids,
            maximum_evidence=EvidenceCeiling.MEASUREMENT,
            maximum_outcome_access=OutcomeAccess.OUTCOME_BLIND,
            deterministic=True,
            implementation_sha256=TORAX_SIMULATED_SOURCE_MANIFEST.implementation_sha256,
            resource_budget=ResourceBudget(4, 8 * 1024**3, 0, 3600, 8 * 1024**3, 8 * 1024**3),
        )
        capabilities = CapabilityRegistry(
            registry_id="capability-registry.torax-source-context",
            capabilities=tuple(
                sorted(
                    (SOURCE_TRANSFORM_MANIFEST, TORAX_SIMULATED_SOURCE_MANIFEST),
                    key=lambda value: value.registry_id,
                )
            ),
        )
        return SourceProfileCompilerBinding(
            binding_id="source-profile-compiler.torax-simulated-source",
            source_manifest=source,
            capability_registry=capabilities,
            dataset_registry=SOURCE_DATASET_CAPABILITY_REGISTRY,
        )


_EXECUTABLE_ID = "executable-contribution.torax-native-source"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES: tuple[ExecutableFactory, ...] = tuple(
    sorted(
        cast(
            tuple[ExecutableFactory, ...],
            (
                RegisteredSourceTransformFactory(),
                ToraxSimulatedSourceFactory(),
                ToraxSourceProfileCompilerFactory(),
            ),
        ),
        key=lambda value: value.binding.binding_id,
    )
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (SourcePipelineProfile,)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
