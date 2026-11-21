# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='neuron-current-response',
                                       title='Neuron current response',
                                       kind='native development',
                                       substrates=('Brian2 LIF neuron',),
                                       methods=('current/spike response',),
                                       environment='separate Brian2 locked environment',
                                       operations=(WorkflowOperation(command='campaign brian2-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/biology/cell-responses/workflows/neuron-current-response/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/biology/cell-responses/workflows/neuron-current-response/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/brian2-neuron-current-response/brian2-lif-native-config'),),
                                       input_availability='Public config; explicit native Python from the '
                                                          'separate locked environment.',
                                       scientific_ceiling='Two reset arms of one block; no population '
                                                          'prevalence or issued candidate.',
                                       first_missing_prerequisite='Shared native binding/provider '
                                                                  'integration is absent.',
                                       guide='programmes/biology/cell-responses/workflows/neuron-current-response/guide.md',
                                       verification_owners=('tests/test_brian2_native_science.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=34),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='brian2-worker',
                        python_version='3.11.14',
                        distribution_versions=(('brian2', '2.9.0'), ('numpy', '1.26.4')),
                        lock_path='programmes/biology/cell-responses/workflows/neuron-current-response/native-env/uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=(),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='brian2-current',
                          schema_id='empirical-lawhood/simulators/brian2-neuron-current-response/brian2-lif-native-config',
                          record_module='empirical_lawhood.domains.biology.neuron_current_response.contracts',
                          record_name='Brian2LIFNativeConfig',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=True,
                          command='campaign brian2-native-check',
                          owner='Brian2LIFNativeConfig',
                          supplied_inputs=('programmes/biology/cell-responses/workflows/neuron-current-response/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='neuron-current-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.brian2_neuron_current_response',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(WorkerEnvironment(role_id='brian2',
                                                            environment_id='brian2-worker',
                                                            selection='explicit'),),
                                 external_software=(),
                                 source_prerequisites=('Shared native binding/provider integration is '
                                                       'absent.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
