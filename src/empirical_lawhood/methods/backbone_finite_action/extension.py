# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



import hashlib

from empirical_lawhood.methods.finite_action_identification import FiniteActionIdentificationConfig, FiniteActionIdentificationResult
from empirical_lawhood.methods.finite_action_registration import FINITE_ACTION_CONFIG_MEDIA_TYPE, FINITE_ACTION_IDENTIFICATION_KEY, FINITE_ACTION_IDENTIFICATION_VERSION, FINITE_ACTION_MAXIMUM_CONFIG_BYTES, FINITE_ACTION_PROVIDER_KEY, finite_action_identification_manifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile, build_observation_evidence_world_registry
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration


_IDENTIFICATION_IMPLEMENTATION_SHA256 = (
    "ec0fecc4fec007aa0e8909d677235f07bcd3107195960a9d38caccd6127197a8"
)
_REGISTRATION_IMPLEMENTATION_SHA256 = (
    "068565658890e6c6960417d4485d415cfd313e7450a4d3bd02b271e35584ef52"
)
_PROFILE_IMPLEMENTATION_SHA256 = (
    "1838a6f708feee9554c0465610ccb7c1771bb37e77cc44ab1b5415a963966baa"
)


FINITE_ACTION_MANIFEST = finite_action_identification_manifest(
    implementation_sha256=_IDENTIFICATION_IMPLEMENTATION_SHA256
)

FINITE_ACTION_CANDIDATE_REGISTRATION = CandidateCapabilityRegistration(
    manifest=FINITE_ACTION_MANIFEST,
    provider_key=FINITE_ACTION_PROVIDER_KEY,
    provider_version=FINITE_ACTION_IDENTIFICATION_VERSION,
    config_media_type=FINITE_ACTION_CONFIG_MEDIA_TYPE,
    maximum_config_bytes=FINITE_ACTION_MAXIMUM_CONFIG_BYTES,
)

LAW_CONTROL_OBJECTIVE_PROFILE_REGISTRATION = ExtensionProfileRegistration(
    registration_id='profile-registration.law-controller-use',
    profile_key='law-controller-use',
    profile_version="1.0.0",
    kind=ExtensionProfileKind.OBJECTIVE_TERMINAL,
    profile_schema=ExperimentObjectiveProfile.SCHEMA,
    profile_schema_sha256=hashlib.sha256(
        ExperimentObjectiveProfile.SCHEMA.encode()
    ).hexdigest(),
    implementation_sha256=_PROFILE_IMPLEMENTATION_SHA256,
)

FINITE_ACTION_METHOD = ExtensionComponentRegistration(
    registration_id="component.finite-action-identification",
    component_key=FINITE_ACTION_IDENTIFICATION_KEY,
    component_version=FINITE_ACTION_IDENTIFICATION_VERSION,
    kind=ExtensionComponentKind.METHOD,
    input_schema_ids=FINITE_ACTION_MANIFEST.input_schema_ids,
    output_schema_ids=FINITE_ACTION_MANIFEST.output_schema_ids,
    implementation_sha256=_IDENTIFICATION_IMPLEMENTATION_SHA256,
)

FINITE_ACTION_CONFIG_DECODER = ExtensionComponentRegistration(
    registration_id="component.finite-action-config-decoder",
    component_key="finite-action-config-decoder",
    component_version="1.0.0",
    kind=ExtensionComponentKind.CONFIG_DECODER,
    input_schema_ids=(FiniteActionIdentificationConfig.SCHEMA,),
    output_schema_ids=(FiniteActionIdentificationConfig.SCHEMA,),
    implementation_sha256=_REGISTRATION_IMPLEMENTATION_SHA256,
)

FINITE_ACTION_ARTIFACT_VALIDATOR = ExtensionComponentRegistration(
    registration_id="component.finite-action-artifact-validator",
    component_key="finite-action-artifact-validator",
    component_version="1.0.0",
    kind=ExtensionComponentKind.ARTIFACT_VALIDATOR,
    input_schema_ids=(FiniteActionIdentificationResult.SCHEMA,),
    output_schema_ids=('empirical-lawhood/runtime/artifact-generic-validation',),
    implementation_sha256=_REGISTRATION_IMPLEMENTATION_SHA256,
)

_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.finite-action",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.METHOD,
    evidence_profile_registries=(build_observation_evidence_world_registry(),),
    capability_manifests=(FINITE_ACTION_MANIFEST,),
    candidate_capability_registrations=(FINITE_ACTION_CANDIDATE_REGISTRATION,),
    dataset_capability_registries=(),
    profile_registrations=(LAW_CONTROL_OBJECTIVE_PROFILE_REGISTRATION,),
    method_registrations=(
        ObjectIdentity.from_record(
            FINITE_ACTION_METHOD.registration_id,
            FINITE_ACTION_METHOD,
        ),
    ),
    config_decoders=(
        ObjectIdentity.from_record(
            FINITE_ACTION_CONFIG_DECODER.registration_id,
            FINITE_ACTION_CONFIG_DECODER,
        ),
    ),
    artifact_validators=(
        ObjectIdentity.from_record(
            FINITE_ACTION_ARTIFACT_VALIDATOR.registration_id,
            FINITE_ACTION_ARTIFACT_VALIDATOR,
        ),
    ),
    runtime_providers=(),
    study_authors=(),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
import hashlib

from empirical_lawhood.methods.finite_action_identification import FiniteActionIdentificationConfig
from empirical_lawhood.methods.finite_action_registration import FINITE_ACTION_MAXIMUM_CONFIG_BYTES, FINITE_ACTION_PROVIDER_KEY, FiniteActionIdentificationComponents, compose_finite_action_identification
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration




_PUBLISHER_PORT_KEY = "candidate-payload-publisher"
_DECODER_CONFIG_SHA256 = hashlib.sha256(
    canonical_json_bytes(
        {
            "decoder_key": FINITE_ACTION_CONFIG_DECODER.component_key,
            "decoder_version": FINITE_ACTION_CONFIG_DECODER.component_version,
            "mode": "exact-canonical-record",
            "payload_schema": FiniteActionIdentificationConfig.SCHEMA,
        }
    )
).hexdigest()

FINITE_ACTION_DECODER_REGISTRATION = StudyExtensionDecoderRegistration(
    registration_id="decoder-registration.finite-action-identification",
    decoder_key=FINITE_ACTION_CONFIG_DECODER.component_key,
    decoder_version=FINITE_ACTION_CONFIG_DECODER.component_version,
    payload_schema=FiniteActionIdentificationConfig.SCHEMA,
    payload_version=FiniteActionIdentificationConfig.VERSION,
    config_sha256=_DECODER_CONFIG_SHA256,
    implementation_sha256=FINITE_ACTION_CONFIG_DECODER.implementation_sha256,
    maximum_payload_bytes=FINITE_ACTION_MAXIMUM_CONFIG_BYTES,
)

FINITE_ACTION_EXECUTABLE_BINDING = ExecutableCapabilityBinding(
    binding_id="binding.finite-action-identification",
    capability_key=FINITE_ACTION_MANIFEST.capability_key,
    capability_version=FINITE_ACTION_MANIFEST.capability_version,
    capability_implementation_sha256=FINITE_ACTION_MANIFEST.implementation_sha256,
    role=ExecutableBindingRole.PROFILE_COMPILER,
    provider_key=FINITE_ACTION_PROVIDER_KEY,
    provider_version=FINITE_ACTION_MANIFEST.capability_version,
    provider_implementation_sha256=FINITE_ACTION_CONFIG_DECODER.implementation_sha256,
    capability_backed=True,
    discovery_components=tuple(
        sorted(
            (
                FINITE_ACTION_ARTIFACT_VALIDATOR,
                FINITE_ACTION_CONFIG_DECODER,
                FINITE_ACTION_METHOD,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    accepted_profile_types=(),
    accepted_config_types=(
        ExecutableRecordTypeBinding(
            record_schema=FiniteActionIdentificationConfig.SCHEMA,
            record_version=FiniteActionIdentificationConfig.VERSION,
        ),
    ),
    required_issued_payload_schemas=(FiniteActionIdentificationConfig.SCHEMA,),
    codec_registration_identities=(
        ObjectIdentity.from_record(
            FINITE_ACTION_CONFIG_DECODER.registration_id,
            FINITE_ACTION_CONFIG_DECODER,
        ),
    ),
    issued_decoder_registrations=(FINITE_ACTION_DECODER_REGISTRATION,),
    input_schema_ids=FINITE_ACTION_MANIFEST.input_schema_ids,
    output_schema_ids=FINITE_ACTION_MANIFEST.output_schema_ids,
    artifact_validator_identities=(
        ObjectIdentity.from_record(
            FINITE_ACTION_ARTIFACT_VALIDATOR.registration_id,
            FINITE_ACTION_ARTIFACT_VALIDATOR,
        ),
    ),
    required_platform_port_keys=(_PUBLISHER_PORT_KEY,),
    may_require_active_mount=True,
    may_require_source_qualification=True,
    may_require_network=False,
    may_require_authority=True,
)


def _exact_config(records: tuple[CanonicalRecord, ...]) -> FiniteActionIdentificationConfig:
    if len(records) != 1 or not isinstance(records[0], FiniteActionIdentificationConfig):
        raise ValueError("finite-action factory requires one exact issued config")
    config = records[0]
    if (
        config.method_key != FINITE_ACTION_EXECUTABLE_BINDING.capability_key
        or config.method_version != FINITE_ACTION_EXECUTABLE_BINDING.capability_version
        or config.implementation_sha256
        != FINITE_ACTION_EXECUTABLE_BINDING.capability_implementation_sha256
    ):
        raise ValueError("finite-action issued config differs from the installed binding")
    return config


def _payload_publisher(platform_ports: tuple[ExecutablePlatformPort, ...]) -> object:
    if tuple(value.port_key for value in platform_ports) != (_PUBLISHER_PORT_KEY,):
        raise ValueError("finite-action factory requires its exact publisher port")
    publisher = platform_ports[0].port
    if not callable(getattr(publisher, "publish_candidate_payload", None)):
        raise TypeError("finite-action publisher port does not satisfy its protocol")
    return publisher


@dataclass(frozen=True, slots=True)
class FiniteActionProfileCompilerFactory:
    """Construct the existing adapter composition without claiming a runner."""

    binding: ExecutableCapabilityBinding = FINITE_ACTION_EXECUTABLE_BINDING

    def build_compiler(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteActionIdentificationComponents:
        config = _exact_config(records)
        publisher = _payload_publisher(platform_ports)
        return compose_finite_action_identification(
            config=config,
            payload_publisher=publisher,  # type: ignore[arg-type]
        )


_EXECUTABLE_ID = "executable-contribution.finite-action"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (FiniteActionProfileCompilerFactory(),)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (FiniteActionIdentificationConfig,)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'FINITE_ACTION_MANIFEST']
