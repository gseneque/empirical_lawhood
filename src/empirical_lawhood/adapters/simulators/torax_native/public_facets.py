# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='tokamak-heat-response',
                                       title='Tokamak heat response',
                                       kind='native development',
                                       substrates=('TORAX tokamak',),
                                       methods=('bounded heat response',),
                                       environment='open-simulators',
                                       operations=(WorkflowOperation(command='campaign torax-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/energy/fusion/workflows/tokamak-heat-response/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/energy/fusion/workflows/tokamak-heat-response/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/torax-native/native-torax-quickstart'),),
                                       input_availability='Public bounded heat config; optional TORAX stack '
                                                          'required.',
                                       scientific_ceiling='One preparation and two nested 40 ms actions; no '
                                                          'qualified source.',
                                       first_missing_prerequisite='Candidate/source qualification is not '
                                                                  'supplied.',
                                       guide='programmes/energy/fusion/workflows/tokamak-heat-response/guide.md',
                                       verification_owners=('tests/test_torax_native_quickstart.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=32),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='tokamak-heat',
                          schema_id='empirical-lawhood/simulators/torax-native/native-torax-quickstart',
                          record_module='empirical_lawhood.adapters.simulators.torax_native.native_quickstart',
                          record_name='NativeToraxQuickstart',
                          disposition='editable',
                          maximum_bytes=32768,
                          requires_canonical=False,
                          command='campaign torax-native-check',
                          owner='NativeToraxQuickstart',
                          supplied_inputs=('programmes/energy/fusion/workflows/tokamak-heat-response/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='tokamak-heat-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.torax_native',
                                 adapter_version='1.0.0',
                                 controller_environment='open-simulators',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Candidate/source qualification is not supplied.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
