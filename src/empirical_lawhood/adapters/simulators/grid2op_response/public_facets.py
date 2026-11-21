# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='grid-response-inputs',
                                       title='Offline grid response',
                                       kind='held native development',
                                       substrates=('Grid2Op electrical grid',),
                                       methods=('bounded grid action response',),
                                       environment='grid2op-held',
                                       operations=(WorkflowOperation(command='campaign grid2op-native-check',
                                                                     boundary='development with held input',
                                                                     inputs=('programmes/energy/electricity-grids/workflows/grid-response-inputs/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/energy/electricity-grids/workflows/grid-response-inputs/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/grid2op-response/grid2-op-development-input'),),
                                       input_availability='Public selector; researcher must supply the '
                                                          'declared offline chronic/source.',
                                       scientific_ceiling='One independent grid unit; no download, candidate '
                                                          'or qualification.',
                                       first_missing_prerequisite='Held source/path bindings must pass '
                                                                  'before native contact.',
                                       guide='programmes/energy/electricity-grids/workflows/grid-response-inputs/guide.md',
                                       verification_owners=('tests/test_grid2op_native_quickstart.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=37),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='grid2op',
                        python_version='3.11.14',
                        distribution_versions=(('grid2op', '1.12.5'), ('lightsim2grid', '0.13.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('grid2op-held',),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='grid-development',
                          schema_id='empirical-lawhood/simulators/grid2op-response/grid2-op-development-input',
                          record_module='empirical_lawhood.adapters.simulators.grid2op_response.native_quickstart',
                          record_name='Grid2OpDevelopmentInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign grid2op-native-check',
                          owner='Grid2OpDevelopmentInput',
                          supplied_inputs=('programmes/energy/electricity-grids/workflows/grid-response-inputs/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='grid-response-inputs',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.grid2op_response',
                                 adapter_version='1.0.0',
                                 controller_environment='grid2op',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Held source/path bindings must pass before native '
                                                       'contact.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
