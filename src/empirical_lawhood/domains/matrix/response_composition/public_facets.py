# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='causal-transfer-audit',
                                       title='Outcome-visible response composition',
                                       kind='guarded input preflight',
                                       substrates=('qualified scalar parent outputs',),
                                       methods=('post-hoc response composition',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'response-composition-input-check',
                                                                     boundary='guarded parent preflight',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/causal-transfer-audit/analysis-input.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/causal-transfer-audit/analysis-input.json',
                                                             role='guarded analysis selector',
                                                             schema_id='empirical-lawhood/composition/response-composition/response-composition-input'),),
                                       input_availability='Analysis selector shipped; authentic qualified '
                                                          'parents, custody and grants must be supplied.',
                                       scientific_ceiling='No independent source or new native tasks.',
                                       first_missing_prerequisite='Separate reveal and analysis authority '
                                                                  'before outcome reads.',
                                       guide='programmes/foundations/emergent-structure/workflows/causal-transfer-audit/guide.md',
                                       verification_owners=('tests/test_response_parent_input.py',
                                                            'tests/test_causal_transfer_synthetic_development.py',
                                                            'tests/test_causal_transfer_scalar_input.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟠 Authenticated parent preflight',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=27),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='causal-transfer-audit',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.response_composition',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Separate reveal and analysis authority before '
                                                       'outcome reads.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
