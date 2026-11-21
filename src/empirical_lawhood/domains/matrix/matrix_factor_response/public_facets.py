# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-retained-refresh',
                                       title='SCI01 retained fixed-basis refresh',
                                       kind='separate exposed retained-analysis successor',
                                       substrates=('original E4 development responses',),
                                       methods=('FULL',
                                                'FULL_REFRESH32',
                                                'INPUT_KRYLOV48',
                                                'INPUT_KRYLOV48_REFRESH32',
                                                'FACTOR'),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'matrix-retained-refresh',
                                                                     boundary='publish protocol before '
                                                                              'deterministic continuation',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-retained-refresh-assess',
                                                                     boundary='independent equations and '
                                                                              'complete original custody',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-retained-matched',
                                                                     boundary='three matched retained '
                                                                              'analyses and signed array '
                                                                              'export',
                                                                     inputs=())),
                                       inputs=(),
                                       input_availability='Original completed E4 directory, current original '
                                                          'access and explicit guarded destinations.',
                                       scientific_ceiling='144 assigned cases, 108 NO_ORIGIN, four usable '
                                                          'independent groups; no molecular admission or new '
                                                          'acquisition.',
                                       first_missing_prerequisite='Select the original complete E4 '
                                                                  'publication and locked source before '
                                                                  'calculation.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-retained-refresh/guide.md',
                                       verification_owners=('tests/test_matrix_retained_refresh.py',
                                                            'tests/test_matrix_refresh_matched.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Exposed retained analysis; 🟠 Molecular transfer requires its own '
                                   'evidence',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=4),
 WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-native-utility',
                                       title='Native Matrix factor-response utility',
                                       kind='declared independent native E2 assessment',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('paired native odd response',
                                                'origin-mechanical comparator utility'),
                                       environment='existing locked main numerical environment; four '
                                                   'selected workers and one numerical thread each',
                                       operations=(WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='freeze independent sources '
                                                                              'and scientific choices before '
                                                                              'contact',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-native-utility/specification.example.json',)),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='retain the exact source-bound '
                                                                              'native utility graph',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='execute declared paired '
                                                                              'prefix and response work',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate custody and '
                                                                              'replay complete utility '
                                                                              'science',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='reuse receipts without '
                                                                              'repeating completed native '
                                                                              'work',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-native-utility/specification.example.json',
                                                             role='editable E2 design; replacement '
                                                                  'identities and missing utility criterion '
                                                                  'stop acquisition',
                                                             schema_id='empirical-lawhood/matrix-factor-response/native-utility-specification'),),
                                       input_availability='Select the actual independent root census, exact '
                                                          'request, protocol, criterion and template files.',
                                       scientific_ceiling='Conditional finite-dt utility arithmetic; '
                                                          'sampling warrant and scientific qualification '
                                                          'remain unestablished.',
                                       first_missing_prerequisite='Freeze the E2 scientific utility '
                                                                  'criterion and bind actual independent '
                                                                  'sources before native contact.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-native-utility/guide.md',
                                       verification_owners=('tests/test_matrix_native_utility.py',
                                                            'tests/test_matrix_native_utility_read.py'),
                                       output_retention='Complete assigned roots, paired scores, adverse '
                                                        'outcomes, nonuse, original receipts and strict '
                                                        'scientific read replay.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Declared native E2 route; 🟠 Scientific selections and workflow '
                                   'acceptance required',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=7))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-retained-refresh',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_factor_response',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select the original complete E4 publication and '
                                                       'locked source before calculation.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='matrix-native-utility',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_factor_response',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Freeze the E2 scientific utility criterion and bind '
                                                       'actual independent sources before native contact.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
