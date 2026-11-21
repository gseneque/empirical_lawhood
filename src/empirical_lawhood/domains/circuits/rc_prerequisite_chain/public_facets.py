# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rc-prerequisite-chain',
                                       title='RC measurement, preparation and response prerequisites',
                                       kind='bounded exposed numerical development experiment',
                                       substrates=('one-cell RC circuit',),
                                       methods=('admitted interval observation',
                                                'frozen discharge rule',
                                                'unchanged response package'),
                                       environment='locked base NumPy/SciPy',
                                       operations=(WorkflowOperation(command='campaign rc-chain-prove',
                                                                     boundary='no-contact design and work '
                                                                              'census',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json',)),
                                                   WorkflowOperation(command='campaign rc-chain-run',
                                                                     boundary='bounded numerical execution '
                                                                              'and receipt recovery',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json',)),
                                                   WorkflowOperation(command='campaign rc-chain-result',
                                                                     boundary='authenticated complete '
                                                                              'retained result',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json',))),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json',
                                                             role='editable exposed complete protocol and '
                                                                  'preparation roster',
                                                             schema_id='empirical-lawhood/methods/rc-prerequisite-chain/config'),),
                                       input_availability='Eleven distinct deterministic preparations and '
                                                          'all ten frozen observation/resource variants are '
                                                          'supplied; execution retains actual development '
                                                          'records separately.',
                                       scientific_ceiling='RC-M, RC-P and RC-J are assessed separately on '
                                                          'exposed numerical preparations. Controls and '
                                                          'solver views remain nested; no physical sensing, '
                                                          'population inference or qualification.',
                                       first_missing_prerequisite='Select the locked numerical environment, '
                                                                  'executing checkout and guarded storage. '
                                                                  'Authentic physical sensing and component '
                                                                  'metrology remain unsupported.',
                                       guide='programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/guide.md',
                                       verification_owners=('tests/test_rc_prerequisite_chain_falsifiers.py',
                                                            'tests/test_rc_chain_workflow.py'),
                                       output_retention='Exact input, producing provenance, per-unit results '
                                                        'and terminal summary are authenticated through '
                                                        'guarded manifests and completion receipts. '
                                                        'Repeating the run reuses completed units; uncertain '
                                                        'contact refuses repetition.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Exposed numerical development experiment',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=11),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rc-prerequisite-chain',
                          schema_id='empirical-lawhood/methods/rc-prerequisite-chain/config',
                          record_module='empirical_lawhood.domains.circuits.rc_prerequisite_chain.contracts',
                          record_name='RCPrerequisiteChainConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign rc-chain-run',
                          owner='RCPrerequisiteChainConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json',
                                           'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original-scientific.json',
                                           'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2-scientific.json',
                                           'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3-scientific.json')),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rc-prerequisite-chain',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.circuits.rc_prerequisite_chain',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select the locked numerical environment, executing '
                                                       'checkout and guarded storage. Authentic physical '
                                                       'sensing and component metrology remain '
                                                       'unsupported.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
