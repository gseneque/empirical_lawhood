# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rc-information',
                                       title='Analytical RC information loss',
                                       kind='analytical calculation',
                                       substrates=('two-branch RC circuit',),
                                       methods=('identical-input minimax bound',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='example rc-information',
                                                                     boundary='analytical calculation',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-information/input.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-information/input.json',
                                                             role='editable analytical operands',
                                                             schema_id='empirical-lawhood/methods/rc-information/config'),),
                                       input_availability='Supplied canonical baseline; positive voltage '
                                                          'scaling is editable.',
                                       scientific_ceiling='Analytical construction and independent equation '
                                                          'check; no sampled qualification.',
                                       first_missing_prerequisite='Prepare edited operands if their bytes '
                                                                  'are not canonical.',
                                       guide='programmes/foundations/measurement-and-response/workflows/rc-information/guide.md',
                                       verification_owners=('tests/test_rc_information.py',
                                                            'tests/test_rc_information_workflow.py'),
                                       output_retention='Optional --output-dir retains the input, report and '
                                                        'bounded attempt diagnostics.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Analytical operation',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=21),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rc-information',
                          schema_id='empirical-lawhood/methods/rc-information/config',
                          record_module='empirical_lawhood.domains.circuits.rc_information.contracts',
                          record_name='RCInformationConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='example rc-information',
                          owner='RCInformationConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-information/input.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rc-information',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.circuits.rc_information',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Prepare edited operands if their bytes are not '
                                                       'canonical.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
