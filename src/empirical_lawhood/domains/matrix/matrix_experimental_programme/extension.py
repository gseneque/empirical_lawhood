# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from hashlib import sha256

from empirical_lawhood.domains.matrix.matrix_experimental_programme import selected_prepared_choices as scientific_choices
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration

from empirical_lawhood.domains.matrix.matrix_experimental_programme.experiment_preparation import bind_later_inputs, input_record_types, prepare_later_experiment, validate_later_instance
from empirical_lawhood.domains.matrix.matrix_experimental_programme.operation_bindings import NAMESPACE, operation_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.prepared_functional_bindings import operation_declarations as prepared_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_protected_bindings import operation_declarations as selected_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_opportunity_bindings import operation_declarations as opportunity_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_revision_bindings import operation_declarations as revision_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_bindings import operation_declarations as sci02_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_bindings import operation_declarations as sci02b_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_bindings import operation_declarations as sci02c_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_reassessment import operation_declarations as sci02c_retained_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme import prepared_functional_experiment as prepared
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.domains.matrix.matrix_experimental_programme import selected_declarative_preparation as declarative
from empirical_lawhood.domains.matrix.matrix_source_evidence import source_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.records import PROTOCOL_ID, MatrixLaterExperimentSpecification
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS


MANIFESTS = tuple(sorted((row.manifest() for row in (*operation_declarations(), *prepared_declarations(), *selected_declarations(), *opportunity_declarations(), *revision_declarations(), *sci02_declarations(), *sci02b_declarations(), *sci02c_declarations(), *sci02c_retained_declarations(), *source_declarations())),
    key=lambda row: row.registry_id))
REGISTRATIONS = tuple(CandidateCapabilityRegistration(row, "recursive.provider." + row.capability_key,
    "1.0.0", "application/json", None) for row in MANIFESTS)
WORKFLOW_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".workflow",
    NAMESPACE + ".workflow", "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL,
    ExperimentObjectiveProfile.SCHEMA, sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(row.fingerprint() for row in MANIFESTS))).hexdigest())
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), MANIFESTS, REGISTRATIONS, (), (WORKFLOW_PROFILE,), (), (), (), (), (), False, False)

_PROTOCOLS = (
    ExperimentProtocolDeclaration(
        PROTOCOL_ID, MatrixLaterExperimentSpecification, prepare_later_experiment,
        "matrix-later-experiment", input_record_types=input_record_types(),
        bind_inputs=bind_later_inputs, validate_instance=validate_later_instance),
    ExperimentProtocolDeclaration(prepared.PROTOCOL_ID, prepared.MatrixPreparedFunctionalExperimentSpecification,
        prepared.prepare_functional_experiment, "matrix-prepared-functional-experiment",
        input_record_types=prepared.input_record_types(), bind_inputs=prepared.bind_functional_inputs,
        validate_instance=prepared.validate_functional_instance, input_storage_codecs=MATRIX_STORAGE_CODECS))

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_experiment as sci02
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import PROTOCOL_ID as SCI02_PROTOCOL_ID
_PROTOCOLS += (ExperimentProtocolDeclaration(SCI02_PROTOCOL_ID, sci02.Sci02Specification,
    sci02.prepare, 'matrix-sci02-h64', input_record_types=sci02.input_record_types(), bind_inputs=sci02.bind_inputs,
    validate_instance=sci02.validate_instance, input_storage_codecs=MATRIX_STORAGE_CODECS),)

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_experiment as sci02b
_PROTOCOLS += (ExperimentProtocolDeclaration(sci02b.PROTOCOL_ID, sci02b.Sci02BSpecification,
    sci02b.prepare, 'matrix-sci02b-paired-description', input_record_types=sci02b.input_record_types(), bind_inputs=sci02b.bind_inputs,
    validate_instance=sci02b.validate_instance, input_storage_codecs=MATRIX_STORAGE_CODECS),)


from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_experiment as sci02c
_PROTOCOLS += (ExperimentProtocolDeclaration(sci02c.PROTOCOL_ID, sci02c.Sci02CSpecification,
    sci02c.prepare, 'matrix-sci02c-consumer-prediction', input_record_types=sci02c.input_record_types(), bind_inputs=sci02c.bind_inputs,
    validate_instance=sci02c.validate_instance, input_storage_codecs=MATRIX_STORAGE_CODECS),)


SELECTED_RESOURCE_CONFIGURATION = (ExperimentInputConfigurationDeclaration("matrix-selected-phase-resources",
    MatrixSelectedOperationalResources, maximum_config_bytes=128 * 1024,
    example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources.example.json",
        "programmes/foundations/emergent-structure/workflows/matrix-selected-opportunity/resources.example.json")),)

DECLARATIVE_CURRENT_REQUEST_CONFIGURATION = ExperimentInputConfigurationDeclaration(
    "matrix-selected-declarative-request-v2", declarative.SelectedPreparedDerivationRequestV2,
    maximum_config_bytes=128 * 1024**2)
DECLARATIVE_TRANSPORT_REQUEST_CONFIGURATION = ExperimentInputConfigurationDeclaration(
    "matrix-selected-declarative-request-v3", declarative.SelectedPreparedDerivationRequestV3,
    maximum_config_bytes=128 * 1024**2)
_PROTOCOLS += (
    ExperimentProtocolDeclaration(declarative.DEVELOPMENT_PROTOCOL_ID, scientific_choices.SelectedPreparedDevelopmentSpecification,
        declarative.prepare, "matrix-selected-declarative-development",
        example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-revision/declarative-opportunity.example.json",),
        maximum_config_bytes=128 * 1024**2, input_record_types=declarative.input_record_types(),
        bind_inputs=declarative.bind_inputs, validate_instance=declarative.validate_instance,
        input_storage_codecs=MATRIX_STORAGE_CODECS,
        configuration_inputs=(*SELECTED_RESOURCE_CONFIGURATION, DECLARATIVE_CURRENT_REQUEST_CONFIGURATION, DECLARATIVE_TRANSPORT_REQUEST_CONFIGURATION),
        requires_development_runtime_binding=True),
    ExperimentProtocolDeclaration(declarative.PROTECTED_PROTOCOL_ID, scientific_choices.SelectedPreparedProtectedSpecification,
        declarative.prepare, "matrix-selected-declarative-protected",
        example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-revision/declarative-transfer.example.json",),
        maximum_config_bytes=128 * 1024**2, input_record_types=declarative.input_record_types(),
        bind_inputs=declarative.bind_inputs, validate_instance=declarative.validate_instance,
        input_storage_codecs=MATRIX_STORAGE_CODECS,
        configuration_inputs=(*SELECTED_RESOURCE_CONFIGURATION, DECLARATIVE_CURRENT_REQUEST_CONFIGURATION, DECLARATIVE_TRANSPORT_REQUEST_CONFIGURATION),
        requires_prospective_runtime_binding=True))


# Finite-dt instrument qualification is a source prerequisite, never E4 outcome
# acquisition or sampling/transport qualification.
from empirical_lawhood.domains.matrix import matrix_finite_dt_source_experiment as finite_dt_source

_PROTOCOLS += (ExperimentProtocolDeclaration(
    finite_dt_source.PROTOCOL_ID, finite_dt_source.MatrixFiniteDtSourceQualificationSpecification,
    finite_dt_source.prepare, "matrix-finite-dt-source-qualification",
    input_record_types=finite_dt_source.input_record_types(), bind_inputs=finite_dt_source.bind_inputs,
    validate_instance=finite_dt_source.validate_instance, requires_prospective_runtime_binding=True),)


# Prepared-source qualification retains its own exercised development path.
from empirical_lawhood.domains.matrix import matrix_prepared_source_experiment as prepared_source
_PROTOCOLS += (ExperimentProtocolDeclaration(
    prepared_source.PROTOCOL_ID, prepared_source.MatrixPreparedSourceQualificationSpecification,
    prepared_source.prepare, "matrix-prepared-finite-dt-source-qualification",
    maximum_config_bytes=128 * 1024**2,
    input_record_types=prepared_source.input_record_types(), bind_inputs=prepared_source.bind_inputs,
    validate_instance=prepared_source.validate_instance, requires_prospective_runtime_binding=True),)


from empirical_lawhood.domains.matrix import matrix_finite_dt_source_assembly as source_assembly

_PROTOCOLS+=(ExperimentProtocolDeclaration(source_assembly.PROTOCOL_ID,
    source_assembly.MatrixFiniteDtSourceAssemblySpecification,source_assembly.prepare,'matrix-finite-dt-source-input-assembly',
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/finite-dt-source-assembly.example.json',),
    maximum_config_bytes=128*1024**2,input_record_types=source_assembly.input_record_types(),
    bind_inputs=source_assembly.bind_inputs,configuration_inputs=(ExperimentInputConfigurationDeclaration(
        'matrix-finite-dt-source-assembly-request',source_assembly.MatrixFiniteDtSourceAssemblyRequest,128*1024**2,
        example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/finite-dt-source-request.example.json',)),)),)

_PROTOCOLS += (ExperimentProtocolDeclaration(source_assembly.CONTINUED_PROTOCOL_ID,
    source_assembly.MatrixFiniteDtRetainedE3AssemblySpecification, source_assembly.prepare,
    'matrix-finite-dt-retained-e3-input-assembly', maximum_config_bytes=128 * 1024**2,
    input_record_types=(source_assembly.MatrixFiniteDtRetainedE3AssemblyRequest,),
    bind_inputs=source_assembly.bind_inputs, configuration_inputs=(ExperimentInputConfigurationDeclaration(
        'matrix-finite-dt-retained-e3-assembly-request', source_assembly.MatrixFiniteDtRetainedE3AssemblyRequest,
        128 * 1024**2),)),)

from empirical_lawhood.domains.matrix import matrix_prepared_source_assembly as prepared_source_assembly
_PROTOCOLS+=(ExperimentProtocolDeclaration(prepared_source_assembly.PROTOCOL_ID,
    prepared_source_assembly.MatrixPreparedSourceAssemblySpecification,prepared_source_assembly.prepare,
    'matrix-prepared-finite-dt-source-input-assembly',maximum_config_bytes=128*1024**2,
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/prepared-source-assembly.example.json',),
    input_record_types=prepared_source_assembly.input_record_types(),bind_inputs=prepared_source_assembly.bind_inputs,
    configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-prepared-finite-dt-source-assembly-request',
        prepared_source_assembly.MatrixPreparedSourceAssemblyRequest,128*1024**2),)),)

_PROTOCOLS += (ExperimentProtocolDeclaration(prepared_source_assembly.CONTINUED_PROTOCOL_ID,
    prepared_source_assembly.MatrixPreparedRetainedE3AssemblySpecification, prepared_source_assembly.prepare,
    'matrix-prepared-retained-e3-input-assembly', maximum_config_bytes=128 * 1024**2,
    input_record_types=(prepared_source_assembly.MatrixPreparedRetainedE3AssemblyRequest,
        *prepared_source_assembly.PROGRAMME_TYPES, *prepared_source_assembly.DEVELOPMENT_TYPES),
    bind_inputs=prepared_source_assembly.bind_inputs,
    configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-prepared-retained-e3-assembly-request',
        prepared_source_assembly.MatrixPreparedRetainedE3AssemblyRequest, 128 * 1024**2),)),)


from empirical_lawhood.domains.matrix.matrix_experimental_programme import preparation_initialization as initialization
_PROTOCOLS += (ExperimentProtocolDeclaration(initialization.PROTOCOL_ID,
    initialization.MatrixPreparationInitializationSpecification, initialization.prepare,
    "matrix-preparation-initialization-inputs", maximum_config_bytes=128 * 1024**2,
    example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-revision/initialization.example.json",),
    input_record_types=initialization.input_record_types(), bind_inputs=initialization.bind_inputs,
    input_storage_codecs=MATRIX_STORAGE_CODECS,
    configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-preparation-initialization-request",
        initialization.MatrixPreparationInitializationRequest, 128 * 1024**2),)),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.matrix.matrix_experimental_programme.operation_bindings import NAMESPACE, operation_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.prepared_functional_bindings import operation_declarations as prepared_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_protected_bindings import operation_declarations as selected_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_opportunity_bindings import operation_declarations as opportunity_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.selected_revision_bindings import operation_declarations as revision_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_bindings import operation_declarations as sci02_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_bindings import operation_declarations as sci02b_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_bindings import operation_declarations as sci02c_declarations
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_reassessment import operation_declarations as sci02c_retained_declarations
from empirical_lawhood.domains.matrix.matrix_source_evidence import source_declarations


_EXECUTABLE_FACTORIES = tuple(row.provider_factory() for row in sorted(
    (*operation_declarations(), *prepared_declarations(), *selected_declarations(), *opportunity_declarations(), *revision_declarations(), *sci02_declarations(), *sci02b_declarations(), *sci02c_declarations(), *sci02c_retained_declarations(), *source_declarations()),
    key=lambda row: (row.capability_key, row.capability_version)))
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
