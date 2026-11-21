# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



import hashlib

from empirical_lawhood.methods.confirmatory_finite_action import ConfirmatoryFiniteActionConfig, ConfirmatoryFiniteActionResult
from empirical_lawhood.methods.geometry.composite_gate_margin import CompositeGateMarginResult, CompositeGateMarginSpec
from empirical_lawhood.methods.confirmatory_finite_action_registration import CONFIRMATORY_FINITE_ACTION_CONFIG_MEDIA_TYPE, CONFIRMATORY_FINITE_ACTION_MAXIMUM_CONFIG_BYTES, CONFIRMATORY_FINITE_ACTION_PROVIDER_KEY, confirmatory_finite_action_manifest
from empirical_lawhood.methods.qualification_profiles import ComponentQualificationProfile
from empirical_lawhood.methods.confirmatory_finite_action import CONFIRMATORY_FINITE_ACTION_KEY, CONFIRMATORY_FINITE_ACTION_VERSION
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.nested_controller_evaluation import RepeatedDeliveryControllerEvaluationPlan
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.controller_compiler import CompiledAdmissionControllerStudy
from empirical_lawhood.execution.controller_evaluation_nested import RepeatedDeliveryControllerCohortAdjudication, RevealedRepeatedDeliveryControllerBundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration


_METHOD_IMPLEMENTATION_SHA256 = (
    "afd00527769340fd4b3c375a4223958871d7f4f164e267014382692575e50acc"
)
_REGISTRATION_IMPLEMENTATION_SHA256 = (
    "b207067e90fba2905e36a9bf1159428b040e30793e5c1ec33fedb15dc111d5c9"
)
_NESTED_CONTROLLER_EVALUATION_IMPLEMENTATION_SHA256 = (
    "9b74f17ce642e655097db6180d69d0d9a8fe269f1ca41142e6572774a4a21292"
)
_COMPOSITE_GATE_MARGIN_IMPLEMENTATION_SHA256 = (
    "b82ef6b60a1b9d6187e0e113e3b143af3523d42c402df5ee8113c0415bd803a4"
)
_PROFILE_IMPLEMENTATION_SHA256 = (
    "9ebfec90d816bfbe92cd33c01014019b9561cb83d22b3d3aeb8b4d08af165ab7"
)


CONFIRMATORY_FINITE_ACTION_MANIFEST = confirmatory_finite_action_manifest(
    implementation_sha256=_METHOD_IMPLEMENTATION_SHA256
)

CONFIRMATORY_FINITE_ACTION_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=CONFIRMATORY_FINITE_ACTION_MANIFEST,
    provider_key=CONFIRMATORY_FINITE_ACTION_PROVIDER_KEY,
    provider_version=CONFIRMATORY_FINITE_ACTION_VERSION,
    config_media_type=CONFIRMATORY_FINITE_ACTION_CONFIG_MEDIA_TYPE,
    maximum_config_bytes=CONFIRMATORY_FINITE_ACTION_MAXIMUM_CONFIG_BYTES,
)

CONFIRMATORY_FINITE_ACTION_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    registration_id="profile-registration.confirmatory-finite-action",
    profile_key="confirmatory-finite-action",
    profile_version="1.0.0",
    kind=ExtensionProfileKind.OBJECTIVE_TERMINAL,
    profile_schema=ComponentQualificationProfile.SCHEMA,
    profile_schema_sha256=hashlib.sha256(
        ComponentQualificationProfile.SCHEMA.encode()
    ).hexdigest(),
    implementation_sha256=_PROFILE_IMPLEMENTATION_SHA256,
)

CONFIRMATORY_FINITE_ACTION_METHOD = ExtensionComponentRegistration(
    registration_id="component.confirmatory-finite-action",
    component_key=CONFIRMATORY_FINITE_ACTION_KEY,
    component_version=CONFIRMATORY_FINITE_ACTION_VERSION,
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.input_schema_ids,
    output_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.output_schema_ids,
    implementation_sha256=_METHOD_IMPLEMENTATION_SHA256,
)

CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.confirmatory-finite-action-config-decoder",
    component_key="confirmatory-finite-action-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(ConfirmatoryFiniteActionConfig.SCHEMA,),
    output_schema_ids=(ConfirmatoryFiniteActionConfig.SCHEMA,),
    implementation_sha256=_REGISTRATION_IMPLEMENTATION_SHA256,
)

CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR = ExtensionComponentRegistration(
    registration_id="component.confirmatory-finite-action-artifact-validator",
    component_key="confirmatory-finite-action-artifact-validator",
    component_version="1.0.0",
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    input_schema_ids=(ConfirmatoryFiniteActionResult.SCHEMA,),
    output_schema_ids=('empirical-lawhood/runtime/artifact-generic-validation',),
    implementation_sha256=_REGISTRATION_IMPLEMENTATION_SHA256,
)

CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER = ExtensionComponentRegistration(
    registration_id="component.confirmatory-finite-action-runtime-provider",
    component_key=CONFIRMATORY_FINITE_ACTION_PROVIDER_KEY,
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.input_schema_ids,
    output_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.output_schema_ids,
    implementation_sha256=_REGISTRATION_IMPLEMENTATION_SHA256,
)

CONFIRMATORY_NESTED_CONTROLLER_EVALUATOR = ExtensionComponentRegistration(
    registration_id="component.confirmatory-nested-controller-evaluator",
    component_key="controller.confirmatory-nested-controller-evaluation",
    component_version="1.0.0",
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=tuple(
        sorted(
            (
                CompiledAdmissionControllerStudy.SCHEMA,
                RepeatedDeliveryControllerEvaluationPlan.SCHEMA,
                RevealedRepeatedDeliveryControllerBundle.SCHEMA,
            )
        )
    ),
    output_schema_ids=(RepeatedDeliveryControllerCohortAdjudication.SCHEMA,),
    implementation_sha256=_NESTED_CONTROLLER_EVALUATION_IMPLEMENTATION_SHA256,
)

COMPOSITE_GATE_MARGIN_METHOD = ExtensionComponentRegistration(
    registration_id="component.composite-gate-margin",
    component_key="geometry.composite-gate-margin",
    component_version="1.0.0",
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=(CompositeGateMarginSpec.SCHEMA,),
    output_schema_ids=(CompositeGateMarginResult.SCHEMA,),
    implementation_sha256=_COMPOSITE_GATE_MARGIN_IMPLEMENTATION_SHA256,
)

_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.confirmatory-replication",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.METHOD,
    evidence_profile_registries=(),
    capability_manifests=(CONFIRMATORY_FINITE_ACTION_MANIFEST,),
    candidate_capability_registrations=(
        CONFIRMATORY_FINITE_ACTION_CANDIDATE_REGISTRATION,
    ),
    dataset_capability_registries=(),
    profile_registrations=(CONFIRMATORY_FINITE_ACTION_PROFILE_REGISTRATION,),
    method_registrations=tuple(
        sorted(
            (
                ObjectIdentity.from_record(
                    CONFIRMATORY_FINITE_ACTION_METHOD.registration_id,
                    CONFIRMATORY_FINITE_ACTION_METHOD,
                ),
                ObjectIdentity.from_record(
                    CONFIRMATORY_NESTED_CONTROLLER_EVALUATOR.registration_id,
                    CONFIRMATORY_NESTED_CONTROLLER_EVALUATOR,
                ),
                ObjectIdentity.from_record(
                    COMPOSITE_GATE_MARGIN_METHOD.registration_id,
                    COMPOSITE_GATE_MARGIN_METHOD,
                ),
            ),
            key=lambda value: value.object_id,
        )
    ),
    config_decoders=(
        ObjectIdentity.from_record(
            CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.registration_id,
            CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER,
        ),
    ),
    artifact_validators=(
        ObjectIdentity.from_record(
            CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR.registration_id,
            CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR,
        ),
    ),
    runtime_providers=(
        ObjectIdentity.from_record(
            CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER.registration_id,
            CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER,
        ),
    ),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass, replace
import hashlib

from empirical_lawhood.methods.confirmatory_finite_action import ConfirmatoryFiniteActionConfig
from empirical_lawhood.methods.confirmatory_finite_action_registration import CONFIRMATORY_FINITE_ACTION_MAXIMUM_CONFIG_BYTES, ConfirmatoryFiniteActionCampaignRuntimeProvider, compose_confirmatory_finite_action
from empirical_lawhood.methods.finite_action_identification import FiniteActionCandidateScaffold
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.design.identification_evidence import IdentificationEvidenceProjection
from empirical_lawhood.design.identification_evidence_extensions import IdentificationEvidenceProjectionExtension
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.providers import CampaignRuntimeProvider




_PUBLISHER_PORT_KEY = "candidate-payload-publisher"
_DECODER_CONFIG_SHA256 = hashlib.sha256(
    canonical_json_bytes(
        {
            "decoder_key": CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.component_key,
            "decoder_version": (CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.component_version),
            "mode": "exact-canonical-record",
            "payload_schema": ConfirmatoryFiniteActionConfig.SCHEMA,
        }
    )
).hexdigest()

CONFIRMATORY_FINITE_ACTION_DECODER_REGISTRATION = StudyExtensionDecoderRegistration(
    registration_id="decoder-registration.confirmatory-finite-action",
    decoder_key=CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.component_key,
    decoder_version=CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.component_version,
    payload_schema=ConfirmatoryFiniteActionConfig.SCHEMA,
    payload_version=ConfirmatoryFiniteActionConfig.VERSION,
    config_sha256=_DECODER_CONFIG_SHA256,
    implementation_sha256=(CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.implementation_sha256),
    maximum_payload_bytes=CONFIRMATORY_FINITE_ACTION_MAXIMUM_CONFIG_BYTES,
)

CONFIRMATORY_FINITE_ACTION_EXECUTABLE_BINDING = ExecutableCapabilityBinding(
    binding_id="binding.confirmatory-finite-action",
    capability_key=CONFIRMATORY_FINITE_ACTION_MANIFEST.capability_key,
    capability_version=CONFIRMATORY_FINITE_ACTION_MANIFEST.capability_version,
    capability_implementation_sha256=(CONFIRMATORY_FINITE_ACTION_MANIFEST.implementation_sha256),
    role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
    provider_key=CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER.component_key,
    provider_version=CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER.component_version,
    provider_implementation_sha256=(
        CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER.implementation_sha256
    ),
    capability_backed=True,
    discovery_components=tuple(
        sorted(
            (
                CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR,
                CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER,
                CONFIRMATORY_FINITE_ACTION_METHOD,
                CONFIRMATORY_FINITE_ACTION_RUNTIME_PROVIDER,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    accepted_profile_types=(),
    accepted_config_types=(
        ExecutableRecordTypeBinding(
            record_schema=ConfirmatoryFiniteActionConfig.SCHEMA,
            record_version=ConfirmatoryFiniteActionConfig.VERSION,
        ),
    ),
    required_issued_payload_schemas=(ConfirmatoryFiniteActionConfig.SCHEMA,),
    codec_registration_identities=(
        ObjectIdentity.from_record(
            CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER.registration_id,
            CONFIRMATORY_FINITE_ACTION_CONFIG_DECODER,
        ),
    ),
    issued_decoder_registrations=(CONFIRMATORY_FINITE_ACTION_DECODER_REGISTRATION,),
    input_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.input_schema_ids,
    output_schema_ids=CONFIRMATORY_FINITE_ACTION_MANIFEST.output_schema_ids,
    artifact_validator_identities=(
        ObjectIdentity.from_record(
            CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR.registration_id,
            CONFIRMATORY_FINITE_ACTION_ARTIFACT_VALIDATOR,
        ),
    ),
    required_platform_port_keys=(_PUBLISHER_PORT_KEY,),
    may_require_active_mount=True,
    may_require_source_qualification=True,
    may_require_network=False,
    may_require_authority=True,
    required_authenticated_record_schemas=CONFIRMATORY_FINITE_ACTION_MANIFEST.input_schema_ids,
)


def _records_by_schema(
    records: tuple[CanonicalRecord, ...],
) -> dict[str, CanonicalRecord]:
    by_schema = {value.SCHEMA: value for value in records}
    expected = {
        ConfirmatoryFiniteActionConfig.SCHEMA,
        FiniteActionCandidateScaffold.SCHEMA,
        IdentificationEvidenceProjection.SCHEMA,
        IdentificationEvidenceProjectionExtension.SCHEMA,
    }
    if len(by_schema) != len(records) or set(by_schema) != expected:
        raise ValueError(
            "confirmatory factory requires exact config/projection/companion/scaffold records"
        )
    return by_schema


def _payload_publisher(platform_ports: tuple[ExecutablePlatformPort, ...]) -> object:
    if tuple(value.port_key for value in platform_ports) != (_PUBLISHER_PORT_KEY,):
        raise ValueError("confirmatory factory requires its exact publisher port")
    publisher = platform_ports[0].port
    if not callable(getattr(publisher, "publish_candidate_payload", None)):
        raise TypeError("confirmatory publisher port does not satisfy its protocol")
    return publisher


@dataclass(frozen=True, slots=True)
class ConfirmatoryFiniteActionProviderFactory:
    binding: ExecutableCapabilityBinding = CONFIRMATORY_FINITE_ACTION_EXECUTABLE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        named = tuple(
            value
            for value in registry.capabilities
            if value.capability_key == self.binding.capability_key
            and value.capability_version == self.binding.capability_version
            and value.implementation_sha256 == self.binding.capability_implementation_sha256
        )
        if len(named) != 1:
            raise ValueError(
                "confirmatory factory requires one exact manifest in the complete registry"
            )
        values = _records_by_schema(records)
        config = values[ConfirmatoryFiniteActionConfig.SCHEMA]
        projection = values[IdentificationEvidenceProjection.SCHEMA]
        extension = values[IdentificationEvidenceProjectionExtension.SCHEMA]
        scaffold = values[FiniteActionCandidateScaffold.SCHEMA]
        if not isinstance(config, ConfirmatoryFiniteActionConfig):
            raise TypeError("confirmatory factory config has another record type")
        if not isinstance(projection, IdentificationEvidenceProjection):
            raise TypeError("confirmatory factory projection has another record type")
        if not isinstance(extension, IdentificationEvidenceProjectionExtension):
            raise TypeError("confirmatory factory companion has another record type")
        if not isinstance(scaffold, FiniteActionCandidateScaffold):
            raise TypeError("confirmatory factory scaffold has another record type")
        if (
            config.method_key != self.binding.capability_key
            or config.method_version != self.binding.capability_version
            or config.implementation_sha256 != self.binding.capability_implementation_sha256
        ):
            raise ValueError("confirmatory issued config differs from the installed binding")
        components = compose_confirmatory_finite_action(
            config=config,
            payload_publisher=_payload_publisher(platform_ports),  # type: ignore[arg-type]
        )
        components = replace(components, capability_registry=registry)
        return ConfirmatoryFiniteActionCampaignRuntimeProvider(
            components=components,
            config=config,
            projection=projection,
            extension=extension,
            scaffold=scaffold,
        )


_EXECUTABLE_ID = "executable-contribution.confirmatory-replication"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ConfirmatoryFiniteActionProviderFactory(),)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (ConfirmatoryFiniteActionConfig,)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
