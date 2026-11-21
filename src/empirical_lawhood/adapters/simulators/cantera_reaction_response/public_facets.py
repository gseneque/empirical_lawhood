# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='reactor-flow-response',
                                       title='Flow-reactor response',
                                       kind='native development',
                                       substrates=('Cantera flow reactor',),
                                       methods=('flow/temperature response',),
                                       environment='reaction-response-simulators',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'reaction-response-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/reactor-flow-response/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-flow-response/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/reaction-diffusion-development/reaction-diffusion-development-input'),),
                                       input_availability='Public Cantera config; optional stack required.',
                                       scientific_ceiling='One complete development unit with 32 nested '
                                                          'cells.',
                                       first_missing_prerequisite='No selected shared provider or fresh '
                                                                  'source qualification.',
                                       guide='programmes/foundations/measurement-and-response/workflows/reactor-flow-response/guide.md',
                                       verification_owners=('tests/test_independent_substrate_native_contracts.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=35),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='reactor-flow-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.cantera_reaction_response',
                                 adapter_version='1.0.0',
                                 controller_environment='reaction-response',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('No selected shared provider or fresh source '
                                                       'qualification.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
