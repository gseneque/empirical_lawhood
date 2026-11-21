# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='battery-response-and-restart',
                                       title='Battery response, restart and reduction',
                                       kind='native development',
                                       substrates=('PyBaMM battery',),
                                       methods=('electrothermal response', 'restart', 'reduced observation'),
                                       environment='open-simulators',
                                       operations=(WorkflowOperation(command='campaign battery-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/energy/battery-charging/workflows/battery-response-and-restart/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/energy/battery-charging/workflows/battery-response-and-restart/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/py-ba-mm-development-input'),),
                                       input_availability='Public development config; optional numerical '
                                                          'stack required.',
                                       scientific_ceiling='Five preparations across three distinct '
                                                          'development contracts.',
                                       first_missing_prerequisite='No general issued battery '
                                                                  'campaign/provider route follows.',
                                       guide='programmes/energy/battery-charging/workflows/battery-response-and-restart/guide.md',
                                       verification_owners=('tests/test_battery_native_science.py',
                                                            'tests/test_battery_development_input.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=31),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='battery-recursion',
                        python_version='3.11.14',
                        distribution_versions=(('pybamm', '26.6.2.0'),
                                               ('numpy', '2.4.6'),
                                               ('scipy', '1.17.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('battery-recursion',),
                        supported_platforms=(('Linux', 'x86_64'),)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='battery-response-and-restart',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.pybamm',
                                 adapter_version='1.0.0',
                                 controller_environment='open-simulators',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('No general issued battery campaign/provider route '
                                                       'follows.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
