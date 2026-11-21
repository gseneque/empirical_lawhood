# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='tokamak-control-response',
                                       title='Tokamak control response',
                                       kind='native development',
                                       substrates=('Gym-TORAX tokamak',),
                                       methods=('paired selected-action control',),
                                       environment='open-simulators',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'gym-torax-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/energy/fusion/workflows/tokamak-control-response/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/energy/fusion/workflows/tokamak-control-response/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/gym-torax-native/gym-torax-native-quickstart'),),
                                       input_availability='Public quickstart; optional stack and selected '
                                                          'source checkout required.',
                                       scientific_ceiling='Two nested 120-request episodes of one '
                                                          'preparation; fixed canary limits.',
                                       first_missing_prerequisite='Controlled snapshot/provider integration '
                                                                  'remains unavailable.',
                                       guide='programmes/energy/fusion/workflows/tokamak-control-response/guide.md',
                                       verification_owners=('tests/test_gym_torax_native_quickstart.py',
                                                            'tests/test_gym_torax_native_contract.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=33),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='tokamak-control',
                          schema_id='empirical-lawhood/simulators/gym-torax-native/gym-torax-native-quickstart',
                          record_module='empirical_lawhood.adapters.simulators.gym_torax_native.native_quickstart',
                          record_name='GymToraxNativeQuickstart',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign gym-torax-native-check',
                          owner='GymToraxNativeQuickstart',
                          supplied_inputs=('programmes/energy/fusion/workflows/tokamak-control-response/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='tokamak-control-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.gym_torax_native',
                                 adapter_version='1.0.0',
                                 controller_environment='open-simulators',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Controlled snapshot/provider integration remains '
                                                       'unavailable.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
