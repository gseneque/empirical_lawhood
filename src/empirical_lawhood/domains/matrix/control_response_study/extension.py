# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.



from hashlib import sha256

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.controller_study import AdmissionControllerStudy
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionComponentRegistration, ExtensionContributionKind

from empirical_lawhood.domains.matrix.control_response_study.contracts import MatrixResponseOuterStudyAuthoringConfig, MatrixResponseProspectiveEvaluationTopology, ProtectedObservableAccessManifest
from empirical_lawhood.domains.matrix.control_response_study.prospective import MatrixResponseOuterProspectiveUmbrella
from empirical_lawhood.domains.matrix.control_response_study.protected_access import MatrixResponseProtectedFieldProjection


_IMPLEMENTATION_SHA256 = sha256(b"six-matrix-response-control-compatibility-services").hexdigest()


def _decoder(
    record_type: type[CanonicalRecord],
    suffix: str,
) -> ExtensionComponentRegistration:
    return ExtensionComponentRegistration(
        registration_id=f"component.six-matrix-response.{suffix}-decoder",
        component_key=f"six-matrix-response-{suffix}-decoder",
        component_version="1.0.0",
        kind=ExtensionComponentKind.CONFIG_DECODER,
        input_schema_ids=(record_type.SCHEMA,),
        output_schema_ids=(record_type.SCHEMA,),
        implementation_sha256=_IMPLEMENTATION_SHA256,
    )


MATRIX_RESPONSE_PROGRAMME_CONFIG_DECODER = _decoder(
    MatrixResponseOuterStudyAuthoringConfig,
    "outer-programme-authoring-config",
)
MATRIX_RESPONSE_PROSPECTIVE_CONFIG_DECODER = _decoder(
    MatrixResponseProspectiveEvaluationTopology,
    "prospective-evaluation-topology",
)
MATRIX_RESPONSE_PROTECTED_CONFIG_DECODER = _decoder(
    ProtectedObservableAccessManifest,
    "protected-observable-access-manifest",
)

MATRIX_RESPONSE_PROGRAMME_AUTHOR = ExtensionComponentRegistration(
    registration_id="component.six-matrix-response.arbitrary-chart-programme-author",
    component_key="six-matrix-response-arbitrary-chart-programme-author",
    component_version="1.0.0",
    kind=ExtensionComponentKind.PROGRAMME_AUTHOR,
    input_schema_ids=(MatrixResponseOuterStudyAuthoringConfig.SCHEMA,),
    output_schema_ids=(AdmissionControllerStudy.SCHEMA,),
    implementation_sha256=_IMPLEMENTATION_SHA256,
)
MATRIX_RESPONSE_PROSPECTIVE_COORDINATOR = ExtensionComponentRegistration(
    registration_id="component.six-matrix-response.prospective-evaluation-coordinator",
    component_key="six-matrix-response-prospective-evaluation-coordinator",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=(MatrixResponseProspectiveEvaluationTopology.SCHEMA,),
    output_schema_ids=(MatrixResponseOuterProspectiveUmbrella.SCHEMA,),
    implementation_sha256=_IMPLEMENTATION_SHA256,
)
MATRIX_RESPONSE_PROTECTED_FIELD_PROJECTOR = ExtensionComponentRegistration(
    registration_id="component.six-matrix-response.protected-field-projector",
    component_key="six-matrix-response-protected-field-projector",
    component_version="1.0.0",
    kind=ExtensionComponentKind.RUNTIME_PROVIDER,
    input_schema_ids=(ProtectedObservableAccessManifest.SCHEMA,),
    output_schema_ids=(MatrixResponseProtectedFieldProjection.SCHEMA,),
    implementation_sha256=_IMPLEMENTATION_SHA256,
)


_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    contribution_id="extension-contribution.six-matrix-response-control-compatibility",
    contribution_version="1.0.0",
    kind=ExtensionContributionKind.CAMPAIGN,
    evidence_profile_registries=(),
    capability_manifests=(),
    candidate_capability_registrations=(),
    dataset_capability_registries=(),
    profile_registrations=(),
    method_registrations=(),
    config_decoders=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in sorted(
            (
                MATRIX_RESPONSE_PROGRAMME_CONFIG_DECODER,
                MATRIX_RESPONSE_PROSPECTIVE_CONFIG_DECODER,
                MATRIX_RESPONSE_PROTECTED_CONFIG_DECODER,
            ),
            key=lambda value: value.registration_id,
        )
    ),
    artifact_validators=(),
    runtime_providers=tuple(
        ObjectIdentity.from_record(value.registration_id, value)
        for value in sorted(
            (MATRIX_RESPONSE_PROSPECTIVE_COORDINATOR, MATRIX_RESPONSE_PROTECTED_FIELD_PROJECTOR),
            key=lambda value: value.registration_id,
        )
    ),
    study_authors=(
        ObjectIdentity.from_record(MATRIX_RESPONSE_PROGRAMME_AUTHOR.registration_id, MATRIX_RESPONSE_PROGRAMME_AUTHOR),
    ),
    grants_authority=False,
    embeds_scientific_payload=False,
)





# Executable roles.



from dataclasses import dataclass
from hashlib import sha256

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.controller_study import AdmissionControllerStudy
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.extension_bundles import ExtensionComponentRegistration
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration

from empirical_lawhood.domains.matrix.control_response_study.contracts import MatrixResponseOuterStudyAuthoringConfig, MatrixResponseProspectiveEvaluationTopology, ProtectedObservableAccessManifest

from empirical_lawhood.domains.matrix.control_response_study.study_authoring import MatrixResponseArbitraryChartStudyAuthor
from empirical_lawhood.domains.matrix.control_response_study.prospective import MatrixResponseOuterProspectiveUmbrella, MatrixResponseProspectiveEvaluationCoordinator
from empirical_lawhood.domains.matrix.control_response_study.protected_access import MatrixResponseProtectedFieldProjection, MatrixResponseProtectedFieldProjector, build_matrix_response_study_procedural_blindness_projector


_MAXIMUM_PAYLOAD_BYTES = 4 * 1024 * 1024


def _executable_decoder(
    *,
    registration_id: str,
    component: ExtensionComponentRegistration,
    record_type: type[CanonicalRecord],
) -> StudyExtensionDecoderRegistration:
    return StudyExtensionDecoderRegistration(
        registration_id=registration_id,
        decoder_key=component.component_key,
        decoder_version=component.component_version,
        payload_schema=record_type.SCHEMA,
        payload_version=record_type.VERSION,
        config_sha256=sha256(
            canonical_json_bytes(
                {
                    "decoder_key": component.component_key,
                    "decoder_version": component.component_version,
                    "mode": "exact-canonical-record",
                    "payload_schema": record_type.SCHEMA,
                }
            )
        ).hexdigest(),
        implementation_sha256=_IMPLEMENTATION_SHA256,
        maximum_payload_bytes=_MAXIMUM_PAYLOAD_BYTES,
    )


MATRIX_RESPONSE_PROGRAMME_DECODER_REGISTRATION = _executable_decoder(
    registration_id="decoder-registration.six-matrix-response-outer-programme-authoring-config",
    component=MATRIX_RESPONSE_PROGRAMME_CONFIG_DECODER,
    record_type=MatrixResponseOuterStudyAuthoringConfig,
)
MATRIX_RESPONSE_PROSPECTIVE_DECODER_REGISTRATION = _executable_decoder(
    registration_id="decoder-registration.six-matrix-response-prospective-evaluation-topology",
    component=MATRIX_RESPONSE_PROSPECTIVE_CONFIG_DECODER,
    record_type=MatrixResponseProspectiveEvaluationTopology,
)
MATRIX_RESPONSE_PROTECTED_DECODER_REGISTRATION = _executable_decoder(
    registration_id="decoder-registration.six-matrix-response-protected-observable-access-manifest",
    component=MATRIX_RESPONSE_PROTECTED_CONFIG_DECODER,
    record_type=ProtectedObservableAccessManifest,
)


def _binding(
    *,
    binding_id: str,
    role: ExecutableBindingRole,
    decoder_component: ExtensionComponentRegistration,
    product_component: ExtensionComponentRegistration,
    decoder: StudyExtensionDecoderRegistration,
    record_type: type[CanonicalRecord],
    output_schema: str,
) -> ExecutableCapabilityBinding:
    return ExecutableCapabilityBinding(
        binding_id=binding_id,
        capability_key=product_component.component_key,
        capability_version=product_component.component_version,
        capability_implementation_sha256=_IMPLEMENTATION_SHA256,
        role=role,
        provider_key=product_component.component_key,
        provider_version=product_component.component_version,
        provider_implementation_sha256=_IMPLEMENTATION_SHA256,
        capability_backed=False,
        discovery_components=tuple(
            sorted(
                (decoder_component, product_component),
                key=lambda value: value.registration_id,
            )
        ),
        accepted_profile_types=(),
        accepted_config_types=(
            ExecutableRecordTypeBinding(record_type.SCHEMA, record_type.VERSION),
        ),
        required_issued_payload_schemas=(record_type.SCHEMA,),
        codec_registration_identities=(
            ObjectIdentity.from_record(decoder_component.registration_id, decoder_component),
        ),
        issued_decoder_registrations=(decoder,),
        input_schema_ids=(record_type.SCHEMA,),
        output_schema_ids=(output_schema,),
        artifact_validator_identities=(),
        required_platform_port_keys=(),
        may_require_active_mount=False,
        may_require_source_qualification=False,
        may_require_network=False,
        may_require_authority=False,
    )


MATRIX_RESPONSE_PROGRAMME_AUTHOR_BINDING = _binding(
    binding_id="binding.six-matrix-response-arbitrary-chart-programme-author",
    role=ExecutableBindingRole.PROGRAMME_AUTHOR,
    decoder_component=MATRIX_RESPONSE_PROGRAMME_CONFIG_DECODER,
    product_component=MATRIX_RESPONSE_PROGRAMME_AUTHOR,
    decoder=MATRIX_RESPONSE_PROGRAMME_DECODER_REGISTRATION,
    record_type=MatrixResponseOuterStudyAuthoringConfig,
    output_schema=AdmissionControllerStudy.SCHEMA,
)
MATRIX_RESPONSE_PROSPECTIVE_COORDINATOR_BINDING = _binding(
    binding_id="binding.six-matrix-response-prospective-evaluation-coordinator",
    role=ExecutableBindingRole.LINKED_CAMPAIGN_COORDINATOR,
    decoder_component=MATRIX_RESPONSE_PROSPECTIVE_CONFIG_DECODER,
    product_component=MATRIX_RESPONSE_PROSPECTIVE_COORDINATOR,
    decoder=MATRIX_RESPONSE_PROSPECTIVE_DECODER_REGISTRATION,
    record_type=MatrixResponseProspectiveEvaluationTopology,
    output_schema=MatrixResponseOuterProspectiveUmbrella.SCHEMA,
)
MATRIX_RESPONSE_PROTECTED_PROJECTOR_BINDING = _binding(
    binding_id="binding.six-matrix-response-protected-field-projector",
    role=ExecutableBindingRole.PROFILE_COMPILER,
    decoder_component=MATRIX_RESPONSE_PROTECTED_CONFIG_DECODER,
    product_component=MATRIX_RESPONSE_PROTECTED_FIELD_PROJECTOR,
    decoder=MATRIX_RESPONSE_PROTECTED_DECODER_REGISTRATION,
    record_type=ProtectedObservableAccessManifest,
    output_schema=MatrixResponseProtectedFieldProjection.SCHEMA,
)


def _one(
    records: tuple[CanonicalRecord, ...],
    record_type: type[CanonicalRecord],
    platform_ports: tuple[ExecutablePlatformPort, ...],
) -> CanonicalRecord:
    if platform_ports or len(records) != 1 or not isinstance(records[0], record_type):
        raise ValueError("Six-matrix response control factory requires one exact issued record and no ports")
    return records[0]


@dataclass(frozen=True, slots=True)
class MatrixResponseStudyAuthorFactory:
    binding: ExecutableCapabilityBinding = MATRIX_RESPONSE_PROGRAMME_AUTHOR_BINDING

    def build_study_author(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseArbitraryChartStudyAuthor:
        config = _one(records, MatrixResponseOuterStudyAuthoringConfig, platform_ports)
        assert isinstance(config, MatrixResponseOuterStudyAuthoringConfig)
        return MatrixResponseArbitraryChartStudyAuthor(config)


@dataclass(frozen=True, slots=True)
class MatrixResponseProspectiveCoordinatorFactory:
    binding: ExecutableCapabilityBinding = MATRIX_RESPONSE_PROSPECTIVE_COORDINATOR_BINDING

    def build_coordinator(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseProspectiveEvaluationCoordinator:
        topology = _one(records, MatrixResponseProspectiveEvaluationTopology, platform_ports)
        assert isinstance(topology, MatrixResponseProspectiveEvaluationTopology)
        return MatrixResponseProspectiveEvaluationCoordinator(topology)


@dataclass(frozen=True, slots=True)
class MatrixResponseProtectedProjectorFactory:
    binding: ExecutableCapabilityBinding = MATRIX_RESPONSE_PROTECTED_PROJECTOR_BINDING

    def build_compiler(
        self,
        *,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> MatrixResponseProtectedFieldProjector:
        manifest = _one(records, ProtectedObservableAccessManifest, platform_ports)
        assert isinstance(manifest, ProtectedObservableAccessManifest)
        return build_matrix_response_study_procedural_blindness_projector(manifest)


_EXECUTABLE_ID = "executable-contribution.six-matrix-response-control-compatibility"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (
    MatrixResponseStudyAuthorFactory(),
    MatrixResponseProspectiveCoordinatorFactory(),
    MatrixResponseProtectedProjectorFactory(),
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = tuple(
    sorted(
        (
            MatrixResponseOuterStudyAuthoringConfig,
            MatrixResponseProspectiveEvaluationTopology,
            ProtectedObservableAccessManifest,
        ),
        key=lambda value: value.SCHEMA,
    )
)





from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
