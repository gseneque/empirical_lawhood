# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='causal-response',
                                       title='Causal response library',
                                       kind='authoring / outcome-visible method',
                                       substrates=('six-matrix medium',),
                                       methods=('fitted causal contrasts',),
                                       environment='reactor-example',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'matrix-response-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/causal-response/causal-author.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/causal-response/causal-author.json',
                                                             role='authoring selector',
                                                             schema_id='empirical-lawhood/composition/prepared-response/prepared-response-native-authoring-input'),),
                                       input_availability='Selector shipped; held source, plan, design, '
                                                          'census and matching causal bank are required.',
                                       scientific_ceiling='Candidate compilation without native tasks; no '
                                                          'fresh qualification.',
                                       first_missing_prerequisite='Matching fitted bank and genuine '
                                                                  'exposure/custody remain required.',
                                       guide='programmes/foundations/emergent-structure/workflows/causal-response/guide.md',
                                       verification_owners=('tests/test_causal_contrasts_held_source.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Development authoring',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=25),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='causal-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.causal_response',
                                 adapter_version='1.0.0',
                                 controller_environment='reactor',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Matching fitted bank and genuine exposure/custody '
                                                       'remain required.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
