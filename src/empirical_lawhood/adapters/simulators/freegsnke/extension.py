# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



import hashlib

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope

from empirical_lawhood.adapters.simulators.freegsnke.parameterised_provider import FREEGSNKE_PARAMETERISED_PROJECTION_KEY, FREEGSNKE_PARAMETERISED_PROVIDER_KEY, FREEGSNKE_PARAMETERISED_VERSION, FreeGsnkeParameterisedEpisodeResult, FreeGsnkeParameterisedProjectionConfig, FreeGsnkeParameterisedProjection, FreeGsnkeParameterisedProviderConfig


FREEGSNKE_PARAMETERISED_IMPLEMENTATION_SHA256 = hashlib.sha256(
    b"freegsnke-neutral-parameterised-provider"
).hexdigest()


def _capability(
    *,
    key: str,
    kind: CapabilityKind,
    config_schema: str,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    deterministic: bool,
) -> CapabilityManifest:
    return CapabilityManifest(
        capability_key=key,
        capability_version=FREEGSNKE_PARAMETERISED_VERSION,
        kind=kind,
        config_schema=config_schema,
        config_schema_sha256=hashlib.sha256(config_schema.encode()).hexdigest(),
        input_schema_ids=tuple(sorted(inputs)),
        output_schema_ids=tuple(sorted(outputs)),
        permissions=(
            CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        ),
        maximum_evidence_ceiling=EvidenceCeiling.LOCAL_LAW,
        maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
        resource_ceiling=ResourceBudget(
            8,
            64 * 1024**3,
            0,
            14_400,
            16 * 1024**3,
            2 * 1024**3,
        ),
        deterministic=deterministic,
        seed_required=False,
        language_id="python",
        runtime_id="freegsnke-parameterised",
        requires_clean_commit=True,
        requires_active_mount=True,
        requires_network=False,
        conformance_check_ids=tuple(
            sorted(
                (
                    "many-views-one-episode",
                    "numerical-failure-preserved",
                    "one-execution-per-acquisition-group",
                    "plural-native-clocks-and-receivers",
                    "requested-accepted-applied-realized-distinct",
                )
            )
        ),
        implementation_sha256=FREEGSNKE_PARAMETERISED_IMPLEMENTATION_SHA256,
    )


FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY = _capability(
    key=FREEGSNKE_PARAMETERISED_PROVIDER_KEY,
    kind=CapabilityKind.SIMULATOR,
    config_schema=FreeGsnkeParameterisedProviderConfig.SCHEMA,
    inputs=(FreeGsnkeParameterisedProviderConfig.SCHEMA,),
    outputs=(FreeGsnkeParameterisedEpisodeResult.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    deterministic=False,
)
FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY = _capability(
    key=FREEGSNKE_PARAMETERISED_PROJECTION_KEY,
    kind=CapabilityKind.TRANSFORM,
    config_schema=FreeGsnkeParameterisedProjectionConfig.SCHEMA,
    inputs=(FreeGsnkeParameterisedEpisodeResult.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    outputs=(FreeGsnkeParameterisedProjection.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    deterministic=True,
)


def _decoder(label: str, schema: str) -> ExtensionComponentRegistration:
    return ExtensionComponentRegistration(
        registration_id=f"component.freegsnke-{label}-decoder",
        component_key=f"freegsnke-{label}-decoder",
        component_version="1.0.0",
        kind=ExtensionComponentKind.CONFIG_DECODER,
        input_schema_ids=(schema,),
        output_schema_ids=(schema,),
        implementation_sha256=FREEGSNKE_PARAMETERISED_IMPLEMENTATION_SHA256,
    )


FREEGSNKE_PARAMETERISED_CONFIG_DECODER = _decoder(
    "parameterised-provider-config",
    FreeGsnkeParameterisedProviderConfig.SCHEMA,
)
FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER = _decoder(
    "parameterised-projection-config",
    FreeGsnkeParameterisedProjectionConfig.SCHEMA,
)


def _provider(label: str, manifest: CapabilityManifest) -> ExtensionComponentRegistration:
    return ExtensionComponentRegistration(
        registration_id=f"component.freegsnke-{label}-provider",
        component_key=f"freegsnke-{label}-provider",
        component_version="1.0.0",
        kind=ExtensionComponentKind.RUNTIME_PROVIDER,
        input_schema_ids=manifest.input_schema_ids,
        output_schema_ids=manifest.output_schema_ids,
        implementation_sha256=FREEGSNKE_PARAMETERISED_IMPLEMENTATION_SHA256,
    )


FREEGSNKE_PARAMETERISED_ACQUISITION_PROVIDER = _provider(
    "parameterised-acquisition",
    FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY,
)
FREEGSNKE_PARAMETERISED_PROJECTION_PROVIDER = _provider(
    "parameterised-projection",
    FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY,
)


_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.freegsnke-parameterised",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.SOURCE,
    evidence_profile_registries=(),
    capability_manifests=tuple(
        sorted(
            (
                FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY,
                FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY,
            ),
            key=lambda value: value.registry_id,
        )
    ),
    candidate_capability_registrations=(),
    dataset_capability_registries=(),
    profile_registrations=(),
    method_registrations=(),
    config_decoders=tuple(
        sorted(
            (
                ObjectIdentity.from_record(value.registration_id, value)
                for value in (
                    FREEGSNKE_PARAMETERISED_CONFIG_DECODER,
                    FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER,
                )
            ),
            key=lambda value: value.object_id,
        )
    ),
    artifact_validators=(),
    runtime_providers=tuple(
        sorted(
            (
                ObjectIdentity.from_record(value.registration_id, value)
                for value in (
                    FREEGSNKE_PARAMETERISED_ACQUISITION_PROVIDER,
                    FREEGSNKE_PARAMETERISED_PROJECTION_PROVIDER,
                )
            ),
            key=lambda value: value.object_id,
        )
    ),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
import hashlib
from typing import cast

from empirical_lawhood.science.evidence.evidence import VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.design.response_experiment import ResponseExperimentExtensionSet
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableFactory, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.response_experiment_ports import ResponseSubstrateBinding
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.providers import CampaignRuntimeProvider
from empirical_lawhood.execution.plans import BarrierKind, OutputTemplate, ProtocolStepTemplate, ProtocolTemplate, ScientificStage


from empirical_lawhood.adapters.simulators.freegsnke.parameterised_provider import FreeGsnkeParameterisedAcquisitionProvider, FreeGsnkeParameterisedEpisodeResult, FreeGsnkeParameterisedExecutorPort, FreeGsnkeParameterisedProjectionConfig, FreeGsnkeParameterisedProjection, FreeGsnkeParameterisedProjectionProvider, FreeGsnkeParameterisedProviderConfig


def _decoder_registration(
    component: ExtensionComponentRegistration,
    record_type: type[CanonicalRecord],
) -> StudyExtensionDecoderRegistration:
    return StudyExtensionDecoderRegistration(
        registration_id=f"decoder-registration.{component.component_key}",
        decoder_key=component.component_key,
        decoder_version=component.component_version,
        payload_schema=record_type.SCHEMA,
        payload_version=record_type.VERSION,
        config_sha256=hashlib.sha256(
            canonical_json_bytes(
                {
                    "decoder_key": component.component_key,
                    "decoder_version": component.component_version,
                    "mode": "exact-canonical-record",
                    "payload_schema": record_type.SCHEMA,
                }
            )
        ).hexdigest(),
        implementation_sha256=component.implementation_sha256,
        maximum_payload_bytes=64 * 1024 * 1024,
    )


FREEGSNKE_PARAMETERISED_CONFIG_DECODER_REGISTRATION = _decoder_registration(
    FREEGSNKE_PARAMETERISED_CONFIG_DECODER,
    FreeGsnkeParameterisedProviderConfig,
)
FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER_REGISTRATION = _decoder_registration(
    FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER,
    FreeGsnkeParameterisedProjectionConfig,
)


def _binding(
    *,
    binding_id: str,
    capability: CapabilityManifest,
    provider: ExtensionComponentRegistration,
    config_type: type[CanonicalRecord],
    decoder_component: ExtensionComponentRegistration,
    decoder_registration: StudyExtensionDecoderRegistration,
    authenticated_types: tuple[type[CanonicalRecord], ...] = (),
    port_keys: tuple[str, ...] = (),
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=capability.capability_key,
        capability_version=capability.capability_version,
        capability_implementation_sha256=capability.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=provider.component_key,
        provider_version=provider.component_version,
        provider_implementation_sha256=provider.implementation_sha256,
        capability_backed=True,
        discovery_components=tuple(
            sorted(
                (decoder_component, provider),
                key=lambda value: value.registration_id,
            )
        ),
        accepted_profile_types=(),
        accepted_config_types=tuple(
            sorted(
                (
                    ExecutableRecordTypeBinding(value.SCHEMA, value.VERSION)
                    for value in (config_type, *authenticated_types)
                ),
                key=lambda value: value.record_schema,
            )
        ),
        required_issued_payload_schemas=(config_type.SCHEMA,),
        required_authenticated_record_schemas=tuple(
            sorted(value.SCHEMA for value in authenticated_types)
        ),
        codec_registration_identities=(
            ObjectIdentity.from_record(decoder_component.registration_id, decoder_component),
        ),
        issued_decoder_registrations=(decoder_registration,),
        input_schema_ids=capability.input_schema_ids,
        output_schema_ids=capability.output_schema_ids,
        artifact_validator_identities=(),
        required_platform_port_keys=port_keys,
        may_require_active_mount=True,
        may_require_source_qualification=True,
        may_require_network=False,
        may_require_authority=True,
    )


FREEGSNKE_PARAMETERISED_ACQUISITION_EXECUTABLE_BINDING = _binding(
    binding_id="binding.freegsnke-parameterised-acquisition",
    capability=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY,
    provider=FREEGSNKE_PARAMETERISED_ACQUISITION_PROVIDER,
    config_type=FreeGsnkeParameterisedProviderConfig,
    decoder_component=FREEGSNKE_PARAMETERISED_CONFIG_DECODER,
    decoder_registration=FREEGSNKE_PARAMETERISED_CONFIG_DECODER_REGISTRATION,
    authenticated_types=(ResponseExperimentExtensionSet, ResponseSubstrateBinding),
    port_keys=("freegsnke-parameterised-executor",),
)
FREEGSNKE_PARAMETERISED_PROJECTION_EXECUTABLE_BINDING = _binding(
    binding_id="binding.freegsnke-parameterised-projection",
    capability=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY,
    provider=FREEGSNKE_PARAMETERISED_PROJECTION_PROVIDER,
    config_type=FreeGsnkeParameterisedProjectionConfig,
    decoder_component=FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER,
    decoder_registration=FREEGSNKE_PARAMETERISED_PROJECTION_CONFIG_DECODER_REGISTRATION,
)


@dataclass(frozen=True, slots=True)
class FreeGsnkeParameterisedAcquisitionProviderFactory:
    binding: ExecutableCapabilityBinding = FREEGSNKE_PARAMETERISED_ACQUISITION_EXECUTABLE_BINDING

    def expand_parameterised_protocol(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        template: ProtocolTemplate,
    ) -> ProtocolTemplate:
        """Supply FreeGSNKE episode/view contracts to neutral fan-out."""

        from empirical_lawhood.execution.linked_campaigns import expand_linked_study_acquisition_views

        extension = next(
            (value for value in records if isinstance(value, ResponseExperimentExtensionSet)),
            None,
        )
        substrate = next(
            (value for value in records if isinstance(value, ResponseSubstrateBinding)),
            None,
        )
        provider_config = next(
            (
                value
                for value in records
                if isinstance(value, FreeGsnkeParameterisedProviderConfig)
            ),
            None,
        )
        projection_config = next(
            (
                value
                for value in records
                if isinstance(value, FreeGsnkeParameterisedProjectionConfig)
            ),
            None,
        )
        if not all(
            value is not None
            for value in (extension, substrate, provider_config, projection_config)
        ):
            raise ValueError("FreeGSNKE protocol expansion lacks its exact adapter records")
        assert isinstance(extension, ResponseExperimentExtensionSet)
        assert isinstance(substrate, ResponseSubstrateBinding)
        assert isinstance(provider_config, FreeGsnkeParameterisedProviderConfig)
        assert isinstance(projection_config, FreeGsnkeParameterisedProjectionConfig)
        if substrate.installed_executable_binding != ObjectIdentity.from_record(
            self.binding.binding_id,
            self.binding,
        ):
            raise ValueError("FreeGSNKE protocol substrate selects another executable binding")

        def config_ref(
            record: CanonicalRecord,
            manifest: CapabilityManifest,
        ) -> CapabilityConfigRef:
            config_id = cast(str, getattr(record, "config_id"))
            return CapabilityConfigRef(
                config_id=config_id,
                config_schema=record.SCHEMA,
                config_schema_sha256=manifest.config_schema_sha256,
                content_sha256=record.fingerprint(),
                artifact_id=f"config-artifact.{config_id}",
            )

        def output(output_id: str, schema: str) -> OutputTemplate:
            return OutputTemplate(
                output_id=output_id,
                payload_schema=schema,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/vnd.empirical-lawhood.canonical+json",
                filename_suffix=".canonical.json",
            )

        source = ProtocolStepTemplate(
            step_id="freegsnke-source-prototype",
            stage=ScientificStage.PREPARE,
            capability_key=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY.capability_key,
            capability_version=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY.capability_version,
            config=config_ref(provider_config, FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY),
            dependency_step_ids=(),
            outputs=tuple(
                sorted(
                    (
                        output(
                            "episode-result",
                            FreeGsnkeParameterisedEpisodeResult.SCHEMA,
                        ),
                        output("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                    ),
                    key=lambda value: value.output_id,
                )
            ),
            required_permissions=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY.permissions,
            requested_outcome_access=OutcomeAccess.EVALUATION_SEALED,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            resource_budget=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY.resource_ceiling,
            resource_lock_ids=("lock.freegsnke-executor",),
            barrier=BarrierKind.NONE,
            maximum_attempts=2,
            obligation_ids=("freegsnke-native-episode",),
        )
        projection = ProtocolStepTemplate(
            step_id="freegsnke-projection-prototype",
            stage=ScientificStage.TRANSFORM,
            capability_key=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY.capability_key,
            capability_version=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY.capability_version,
            config=config_ref(projection_config, FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY),
            dependency_step_ids=(),
            outputs=tuple(
                sorted(
                    (
                        output("projection", FreeGsnkeParameterisedProjection.SCHEMA),
                        output("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                    ),
                    key=lambda value: value.output_id,
                )
            ),
            required_permissions=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY.permissions,
            requested_outcome_access=OutcomeAccess.EVALUATION_SEALED,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            resource_budget=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY.resource_ceiling,
            resource_lock_ids=(),
            barrier=BarrierKind.NONE,
            maximum_attempts=2,
            obligation_ids=("freegsnke-view-projection",),
        )
        return expand_linked_study_acquisition_views(
            template=template,
            identification_config=extension.identification_config,
            source_task_prefix=provider_config.source_task_prefix,
            projection_task_prefix=projection_config.projection_task_prefix,
            source_step_template=source,
            projection_step_template=projection,
        )

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        by_type = {type(value): value for value in records}
        if len(by_type) != 3 or set(by_type) != {
            ResponseExperimentExtensionSet,
            ResponseSubstrateBinding,
            FreeGsnkeParameterisedProviderConfig,
        }:
            raise ValueError("FreeGSNKE acquisition factory requires exact records")
        if (
            len(platform_ports) != 1
            or platform_ports[0].port_key != "freegsnke-parameterised-executor"
            or not isinstance(platform_ports[0].port, FreeGsnkeParameterisedExecutorPort)
        ):
            raise ValueError("FreeGSNKE acquisition factory requires one executor port")
        substrate = cast(ResponseSubstrateBinding, by_type[ResponseSubstrateBinding])
        if substrate.installed_executable_binding != ObjectIdentity.from_record(
            self.binding.binding_id,
            self.binding,
        ):
            raise ValueError("FreeGSNKE substrate differs from installed acquisition")
        return FreeGsnkeParameterisedAcquisitionProvider(
            registry=registry,
            manifest=FREEGSNKE_PARAMETERISED_ACQUISITION_CAPABILITY,
            extension_set=cast(
                ResponseExperimentExtensionSet,
                by_type[ResponseExperimentExtensionSet],
            ),
            substrate_binding=substrate,
            config=cast(
                FreeGsnkeParameterisedProviderConfig,
                by_type[FreeGsnkeParameterisedProviderConfig],
            ),
            executor=platform_ports[0].port,
        )


@dataclass(frozen=True, slots=True)
class FreeGsnkeParameterisedProjectionProviderFactory:
    binding: ExecutableCapabilityBinding = FREEGSNKE_PARAMETERISED_PROJECTION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        if (
            len(records) != 1
            or not isinstance(records[0], FreeGsnkeParameterisedProjectionConfig)
            or platform_ports
        ):
            raise ValueError("FreeGSNKE projection factory requires one config")
        return FreeGsnkeParameterisedProjectionProvider(
            registry=registry,
            manifest=FREEGSNKE_PARAMETERISED_PROJECTION_CAPABILITY,
            config=records[0],
        )


_EXECUTABLE_ID = "executable-contribution.freegsnke-parameterised"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES: tuple[ExecutableFactory, ...] = tuple(
    sorted(
        cast(
            tuple[ExecutableFactory, ...],
            (
                FreeGsnkeParameterisedAcquisitionProviderFactory(),
                FreeGsnkeParameterisedProjectionProviderFactory(),
            ),
        ),
        key=lambda value: value.binding.binding_id,
    )
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (
    FreeGsnkeParameterisedProjectionConfig,
    FreeGsnkeParameterisedProviderConfig,
)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
