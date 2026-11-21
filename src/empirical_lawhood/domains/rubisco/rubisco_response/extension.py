# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_preparation import bind_response_inputs, prepare_response_experiment, validate_response_instance
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import PROTOCOL_ID, RubiscoResponseExperimentSpecification
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import MAX_INPUT_BYTES, NAMESPACE, operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_operation import operation_declaration as adoption_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import operation_declaration as initial_amber_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import operation_declaration as periodic_probe_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import operation_declaration as periodic_control_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import operation_declaration as trajectory_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import operation_declaration as equilibrium_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import operation_declaration as active_relaxation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import operation_declaration as active_preparation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import operation_declaration as preparation_response_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import operation_declaration as preparation_response_analysis_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import operation_declaration as preparation_supply_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_operation import operation_declaration as gas_parameter_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_operation import operation_declaration as gas_relaxation_declaration
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import operation_declaration as geometry_repair_declaration, CAPABILITY as GEOMETRY_REPAIR, AMBER_FRAGMENT_CAPABILITY, CARBOXYLATE_CAPABILITY, MAX_INPUT as REPAIR_MAX_INPUT
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_operation import operation_declarations as initial_root_declarations
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_experiment import PROTOCOL_ID as INITIAL_ROOT_PROTOCOL, InitialRootExperimentSpecification, bind_inputs as bind_initial_root_inputs, prepare as prepare_initial_root_experiment, validate_instance as validate_initial_root_instance
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs


_CONFIGURATIONS = (ConfigurationDeclaration(
    consumer='rubisco-preparation-response-design',
    schema_id='empirical-lawhood/rubisco-response/preparation-response-design',
    record_module='empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design',
    record_name='PreparationResponseDesign', disposition='editable', maximum_bytes=2**20,
    requires_canonical=True, command='scripts/operate_preparation_response.py prepare-prefix',
    owner='PreparationResponseDesign', supplied_inputs=()), ConfigurationDeclaration(
    consumer='rubisco-preparation-environment-design',
    schema_id='empirical-lawhood/rubisco-response/preparation-environment-design',
    record_module='empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design',
    record_name='EnvironmentalPreparationResponseDesign', disposition='editable', maximum_bytes=64 * 2**20,
    requires_canonical=True, command='scripts/operate_preparation_response.py prepare-prefix',
    owner='EnvironmentalPreparationResponseDesign', supplied_inputs=()),)


def installed_declarations():
    return (*operation_declarations(), *initial_root_declarations(), adoption_declaration(), initial_amber_declaration(), geometry_repair_declaration(),
        geometry_repair_declaration(carboxylates=True), geometry_repair_declaration(amber_fragments=True), gas_parameter_declaration(),
        gas_relaxation_declaration(), gas_relaxation_declaration(accelerated=True),
        periodic_probe_declaration(), periodic_probe_declaration(restart=True), active_relaxation_declaration(),
        periodic_probe_declaration(accelerated=True), periodic_probe_declaration(restart=True, accelerated=True),
        active_relaxation_declaration(conditional=True),
        active_relaxation_declaration(accelerated=True), active_relaxation_declaration(conditional=True, accelerated=True),
        active_preparation_declaration(), active_preparation_declaration(accelerated=True),
        active_preparation_declaration(continuation=True), active_preparation_declaration(accelerated=True, continuation=True),
        preparation_response_declaration(), preparation_response_declaration(accelerated=True),
        preparation_response_analysis_declaration(), preparation_response_analysis_declaration(environmental=True),
        preparation_supply_declaration(),
        periodic_control_declaration(), periodic_control_declaration(accelerated=True),
        periodic_control_declaration(force_actions=True), periodic_control_declaration(accelerated=True, force_actions=True),
        trajectory_declaration(), equilibrium_declaration(),
        trajectory_declaration(accelerated=True), equilibrium_declaration(accelerated=True),
        equilibrium_declaration(accelerated=True, observed=True))

from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy

_MANIFESTS = tuple(declaration.manifest() for declaration in installed_declarations())
_BUILT = tuple(bundle(manifest.capability_key.removeprefix(NAMESPACE + "."), ExtensionContributionKind.METHOD,
    manifest, (), None, namespace=NAMESPACE,
    maximum_config_bytes=(REPAIR_MAX_INPUT if manifest.capability_key in (GEOMETRY_REPAIR, CARBOXYLATE_CAPABILITY, AMBER_FRAGMENT_CAPABILITY) else
        64 * 2**20 if manifest.capability_key.startswith('rubisco-response.initial-root-') else MAX_INPUT_BYTES)) for manifest in _MANIFESTS)
COMPONENTS = {contribution.capability_manifests[0].registry_id: tuple(sorted(parts, key=lambda row: row.registration_id))
              for contribution, parts in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0",
    ExtensionContributionKind.METHOD, (), tuple(sorted(_MANIFESTS, key=lambda row: row.registry_id)),
    tuple(sorted((row for contribution, _ in _BUILT for row in contribution.candidate_capability_registrations),
                 key=lambda row: row.registration_id)), (),
    tuple(sorted((row for contribution, _ in _BUILT for row in contribution.profile_registrations),
                 key=lambda row: row.registration_id)), (), (), (),
    tuple(sorted((row for contribution, _ in _BUILT for row in contribution.runtime_providers),
                 key=lambda row: row.object_id)), (), False, False)

_PROTOCOLS = (ExperimentProtocolDeclaration(PROTOCOL_ID,
    RubiscoResponseExperimentSpecification, prepare_response_experiment, "rubisco-response-experiment",
    example_paths=("programmes/biology/photosynthesis/workflows/rubisco-response/experiment.json",), maximum_config_bytes=1024 * 1024,
    input_record_types=(RubiscoResponseStudy,), bind_inputs=bind_response_inputs,
    validate_instance=validate_response_instance,
    configuration_inputs=(ExperimentInputConfigurationDeclaration("rubisco-response-study", RubiscoResponseStudy,
        MAX_INPUT_BYTES, ("programmes/biology/photosynthesis/workflows/rubisco-response/study.json",)),)),
    ExperimentProtocolDeclaration(INITIAL_ROOT_PROTOCOL, InitialRootExperimentSpecification, prepare_initial_root_experiment,
        'rubisco-initial-root-experiment', maximum_config_bytes=1024 * 1024,
        input_record_types=(InitialRootAnalysisInputs,), bind_inputs=bind_initial_root_inputs,
        validate_instance=validate_initial_root_instance,
        configuration_inputs=(ExperimentInputConfigurationDeclaration('rubisco-initial-root-analysis',
            InitialRootAnalysisInputs, 64 * 2**20),)))


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import NAMESPACE

_EXECUTABLE_FACTORIES = tuple(declaration.provider_factory(
    components=COMPONENTS[declaration.manifest().registry_id]) for declaration in installed_declarations())
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
    configurations=_CONFIGURATIONS,
)

__all__ = ['EXTENSION']
