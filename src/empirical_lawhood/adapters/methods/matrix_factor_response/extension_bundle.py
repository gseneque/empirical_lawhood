# SPDX-License-Identifier: MPL-2.0
"""Static declarations for exposed response development and prospective eligibility."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from .response_error_joint_bindings_v2 import operation_declaration as joint_declaration
from .response_error_pooled_bindings import operation_declaration as pooled_declaration
from .experiment_bindings import operation_declarations as experiment_declarations
from .configured_bindings import operation_declarations as configured_declarations
from .protected_composition import operation_declarations as protected_declarations
from .configured_protected_composition import operation_declarations as configured_protected_declarations
from .configured_retained_bindings import retained_output_record_types
from .native_training_bindings import operation_declarations as native_training_declarations
from .native_utility_bindings import operation_declarations as native_utility_declarations
from empirical_lawhood.adapters.methods.matrix_sampling_bindings import sampling_declaration


OPERATION_DECLARATIONS = (
    joint_declaration(), joint_declaration(True), pooled_declaration(), pooled_declaration(True),
    *experiment_declarations(), *configured_declarations(), *protected_declarations(),
    *configured_protected_declarations(), *native_training_declarations(), *native_utility_declarations(),
    sampling_declaration("E3"))
MANIFESTS = tuple(sorted((declaration.manifest() for declaration in OPERATION_DECLARATIONS),
    key=lambda manifest: manifest.registry_id))
_BUILT = tuple(bundle(m.capability_key.rsplit('.', 1)[-1], ExtensionContributionKind.METHOD,
    m, (), None, namespace=m.capability_key.rsplit('.', 1)[0], maximum_config_bytes=None)
    for m in MANIFESTS)
COMPONENTS = {c.capability_manifests[0].registry_id: tuple(sorted(parts, key=lambda p: p.registration_id))
    for c, parts in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    'method.matrix-factor-response', '1.0.0', ExtensionContributionKind.METHOD, (), MANIFESTS,
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)

# Domain protocols are cold projections alongside the existing operation bundle.
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration
from .experiment_preparation import prepare_matrix_response_error, validate_matrix_response_instance
from .experiment_specification import MatrixResponseErrorSpecification
from .experiment_inputs import bind_matrix_response_inputs, input_record_types
from .experiment_methods import MatrixE3FeatureBank, MatrixE3OutcomeBank
from .native_training_records import NativeTrainingFeatureBank, NativeTrainingOutcomeBank
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from .native_utility_acquisition import (
    PROTOCOL_ID as NATIVE_UTILITY_PROTOCOL_ID, bind_inputs as bind_native_utility,
    prepare as prepare_native_utility, validate_instance as validate_native_utility,
)
from .native_utility_records import NativeUtilitySpecification, NativeUtilityRequest

EXPERIMENT_PROTOCOL_DECLARATIONS = (ExperimentProtocolDeclaration(
    "matrix.response-error.origin-only", MatrixResponseErrorSpecification,
    prepare_matrix_response_error, "matrix-response-experiment",
    ("programmes/foundations/emergent-structure/workflows/matrix-response-experiment/alternative.json",
     "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/specification.json"),
    input_record_types=input_record_types(), bind_inputs=bind_matrix_response_inputs,
    validate_instance=validate_matrix_response_instance, input_storage_codecs=MATRIX_STORAGE_CODECS,
    input_file_record_types=(MatrixE3FeatureBank, MatrixE3OutcomeBank),
    requires_prospective_runtime_binding=True),)

EXPERIMENT_PROTOCOL_DECLARATIONS += (ExperimentProtocolDeclaration(
    NATIVE_UTILITY_PROTOCOL_ID, NativeUtilitySpecification, prepare_native_utility,
    "matrix-native-utility", maximum_config_bytes=None,
    example_paths=("programmes/foundations/emergent-structure/workflows/matrix-native-utility/specification.example.json",),
    input_record_types=(NativeUtilityRequest,), bind_inputs=bind_native_utility,
    validate_instance=validate_native_utility, input_storage_codecs=MATRIX_STORAGE_CODECS),)

from .configured_specification import ConfiguredMatrixResponseErrorSpecification, ConfiguredE3Resources, PAIRED15_MEASUREMENT_CAPABILITY, SOURCEBOUND_MEASUREMENT_CAPABILITY
from .configured_preparation import prepare_matrix_response_error as prepare_configured, validate_matrix_response_instance as validate_configured
from .configured_inputs import bind_matrix_response_inputs as bind_configured, input_record_types as configured_input_types
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputConfigurationDeclaration

EXPERIMENT_PROTOCOL_DECLARATIONS = (*EXPERIMENT_PROTOCOL_DECLARATIONS, ExperimentProtocolDeclaration(
    "matrix.response-error.origin-only.configured-v2", ConfiguredMatrixResponseErrorSpecification,
    prepare_configured, "matrix-response-experiment-v2",
    configuration_capabilities=(PAIRED15_MEASUREMENT_CAPABILITY,),
    example_paths=("programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-v2.json",),
    input_record_types=configured_input_types(),
    bind_inputs=bind_configured, validate_instance=validate_configured,
    configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-response-e3-resources-v2", ConfiguredE3Resources, 4 * 1024**2),)))


from .configured_protected_specification import ConfiguredProtectedE3Specification
from .configured_protected_exports import ConfiguredProtectedE3ProductExportSelection
from .configured_protected_preparation import (
    configured_preparation_types, prepare_protected_e3 as prepare_configured_protected,
    bind_protected_e3_experiment_inputs as bind_configured_protected,
    validate_protected_e3_experiment_instance as validate_configured_protected,
)
from .configured_secondary_readout import MatrixE3SecondaryTarget
from .configured_closeout_execution import ConfiguredE3MissingOutcomeProducts
from .configured_protected_methods import ConfiguredProtectedE3PairedOutcome
EXPERIMENT_PROTOCOL_DECLARATIONS += (ExperimentProtocolDeclaration(
    "matrix.response-error.configured-protected-v2", ConfiguredProtectedE3Specification,
    prepare_configured_protected, "matrix-configured-protected-e3",
    configuration_capabilities=(SOURCEBOUND_MEASUREMENT_CAPABILITY,),
    example_paths=("programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-protected-v2.json",),
    maximum_config_bytes=128 * 1024**2,
    configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-configured-secondary-target", MatrixE3SecondaryTarget, 128 * 1024**2,
            ("programmes/foundations/emergent-structure/workflows/matrix-response-experiment/secondary-response-target.example.json",)),
        ExperimentInputConfigurationDeclaration("matrix-configured-protected-product-export",
            ConfiguredProtectedE3ProductExportSelection, 1024**2,
            ("programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-protected-export.example.json",))),
    input_record_types=(*configured_preparation_types(), MatrixE3SecondaryTarget, ConfiguredProtectedE3ProductExportSelection), bind_inputs=bind_configured_protected,
    validate_instance=validate_configured_protected, input_storage_codecs=MATRIX_STORAGE_CODECS,
    input_file_record_types=tuple(sorted((NativeTrainingFeatureBank, NativeTrainingOutcomeBank, ConfiguredE3MissingOutcomeProducts, ConfiguredProtectedE3PairedOutcome,
        *retained_output_record_types(OPERATION_DECLARATIONS)), key=lambda kind: (kind.SCHEMA, kind.VERSION))),
    requires_prospective_runtime_binding=True),)


from .native_training_records import NativeTrainingAcquisitionSpecification, NativeTrainingAcquisitionRequest
from .native_training_exports import NativeTrainingBankExportSelection
from .native_training_acquisition import PROTOCOL_ID as NATIVE_TRAINING_PROTOCOL_ID, prepare as prepare_native_training, bind_inputs as bind_native_training, validate_instance as validate_native_training

EXPERIMENT_PROTOCOL_DECLARATIONS += (ExperimentProtocolDeclaration(
    NATIVE_TRAINING_PROTOCOL_ID, NativeTrainingAcquisitionSpecification, prepare_native_training,
    "matrix-native-training-acquisition", configuration_capabilities=(SOURCEBOUND_MEASUREMENT_CAPABILITY,),
    input_record_types=(NativeTrainingAcquisitionRequest,NativeTrainingBankExportSelection),
    configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-native-training-bank-export',NativeTrainingBankExportSelection,1024**2,
        ('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-export.example.json',)),),
    bind_inputs=bind_native_training, validate_instance=validate_native_training,
    input_storage_codecs=MATRIX_STORAGE_CODECS),)


from .native_training_assembly import (PROTOCOL_ID as NATIVE_ASSEMBLY_PROTOCOL_ID,NativeTrainingAssemblyRequest,
    NativeTrainingAssemblySpecification,input_record_types as native_assembly_input_types,
    bind_inputs as bind_native_assembly,prepare as prepare_native_assembly)

from .native_training_protocol import NativeTrainingScientificProtocol
from .exposure import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay

EXPERIMENT_PROTOCOL_DECLARATIONS+=(ExperimentProtocolDeclaration(NATIVE_ASSEMBLY_PROTOCOL_ID,NativeTrainingAssemblySpecification,
    prepare_native_assembly,'matrix-native-training-input-assembly',maximum_config_bytes=None,
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-assembly.example.json',),
    input_record_types=native_assembly_input_types(),bind_inputs=bind_native_assembly,bind_input_locations=True,
    configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-native-training-assembly-request',NativeTrainingAssemblyRequest,128*1024**2,
            example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-request.example.json',)),
        ExperimentInputConfigurationDeclaration('matrix-native-training-scientific-protocol',NativeTrainingScientificProtocol,128*1024**2,
            example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-scientific-protocol.example.json',)),
        ExperimentInputConfigurationDeclaration('matrix-native-training-response-assay',ScheduledResponseAssay,128*1024**2,
            example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-assay.example.json',)),
        ExperimentInputConfigurationDeclaration('matrix-factor-exposure-census',MatrixFactorExposureCensus,128*1024**2,
            example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/exposure-census.example.json',))),),)

from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection

from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from .configured_protected_assembly import (PROTOCOL_ID as CONFIGURED_ASSEMBLY_PROTOCOL_ID,ConfiguredProtectedE3AssemblyRequest,
    ConfiguredProtectedE3AssemblySpecification,bind_inputs as bind_configured_assembly,prepare as prepare_configured_assembly)

from .configured_primary_amendment import MatrixE3PrimaryFamilyAmendment

EXPERIMENT_PROTOCOL_DECLARATIONS+=(ExperimentProtocolDeclaration(CONFIGURED_ASSEMBLY_PROTOCOL_ID,ConfiguredProtectedE3AssemblySpecification,
    prepare_configured_assembly,'matrix-configured-protected-input-assembly',maximum_config_bytes=128*1024**2,
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-scientific-assembly.example.json',),
    input_record_types=(ConfiguredProtectedE3AssemblyRequest,NativeTrainingScientificProtocol,MatrixE3PrimaryFamilyAmendment,ExperimentFileInputSelection,NativeTrainingExportAdoptionSelection,MatrixProgrammePublishedInput),bind_inputs=bind_configured_assembly,bind_input_locations=True,
    configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-configured-protected-assembly-request',ConfiguredProtectedE3AssemblyRequest,1024**2,
        ('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-scientific-assembly.request.example.json',)),
        ExperimentInputConfigurationDeclaration('matrix-configured-primary-family-amendment',MatrixE3PrimaryFamilyAmendment,1024**2),
        ExperimentInputConfigurationDeclaration('matrix-configured-protected-assembly-sources',ExperimentFileInputSelection,1024**2,
        ('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-scientific-assembly.sources.example.json',)),)),)
