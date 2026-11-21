# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-selected-e4-revision',
                                       title='Fit and freeze the declared Matrix revision',
                                       kind='original DEV acquisition to declared fit/freeze programme',
                                       substrates=('six-matrix scheduled DEV responses',),
                                       methods=('whole-group cross-validation',
                                                'declared ridge candidates',
                                                'frozen revision and baseline'),
                                       environment='existing locked main numerical environment',
                                       operations=(WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='derive declared census and '
                                                                              'explicit dependencies; no '
                                                                              'native contact',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-prepare',
                                                                     boundary='retain selected preparation '
                                                                              'report; no authority',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='derive immutable components '
                                                                              'and original input bindings',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='execute eligible declared '
                                                                              'components through existing '
                                                                              'services',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate complete '
                                                                              'findings or explicit partial '
                                                                              'custody',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='reuse original receipts and '
                                                                              'refuse uncertain contact',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/acquisition-source.json',
                                                             role='exact retained original DEV acquisition '
                                                                  'and allocation selection',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/revision-acquisition-source'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/resources.json',
                                                             role='explicit revision phase resource '
                                                                  'selection',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/method-resources'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json',
                                                             role='editable declared scientific '
                                                                  'specification',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/revision-acquisition-specification')),
                                       input_availability='Copied specifications and resources are supplied; '
                                                          'original complete DEV acquisition custody and '
                                                          'allocation must be selected.',
                                       scientific_ceiling='Exposed revision fitting creates no protected '
                                                          'qualification or cross-regime coverage.',
                                       first_missing_prerequisite='Select the complete original DEV '
                                                                  'acquisition, declared candidates/folds, '
                                                                  'operational resources and guarded EL '
                                                                  'output.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/guide.md',
                                       verification_owners=('tests/test_matrix_selected_e4_methods.py',
                                                            'tests/test_matrix_selected_e4_revision_transition.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Declared researcher route; 🟠 Current workflow acceptance required',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=42),
 WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-selected-e4-protected',
                                       title='Calibrate and confirm the declared Matrix revision',
                                       kind='phase-separated native waves and complete scientific tail',
                                       substrates=('six-matrix scheduled protected responses',),
                                       methods=('whole-group allocation',
                                                'forecast before future',
                                                'complete calibration and confirmation'),
                                       environment='existing locked main numerical environment; selected '
                                                   'operator concurrency',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'experiment-derive-inputs',
                                                                     boundary='derive exact banks, '
                                                                              'scientific root and access '
                                                                              'from authenticated originals; '
                                                                              'no issue or native contact',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-calibration.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-confirmation.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-sources.example.json')),
                                                   WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='derive declared census and '
                                                                              'explicit dependencies; no '
                                                                              'native contact',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-prepare',
                                                                     boundary='retain selected preparation '
                                                                              'report; no authority',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='derive immutable components '
                                                                              'and original input bindings',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='execute eligible declared '
                                                                              'components through existing '
                                                                              'services',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate complete '
                                                                              'findings or explicit partial '
                                                                              'custody',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='reuse original receipts and '
                                                                              'refuse uncertain contact',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-calibration.example.json',
                                                             role='editable CAL intent with an exact bank or '
                                                                  'explicit new bank recipe; placeholders do '
                                                                  'not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/declarative-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-confirmation.example.json',
                                                             role='editable CONF intent with complete '
                                                                  'original CAL and DEV dependencies',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/declarative-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-sources.example.json',
                                                             role='copied request/bank or recipe-input '
                                                                  'selector; plans and task maps are '
                                                                  'code-owned',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/calibration.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/protected-programme-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/confirmation.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/protected-programme-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/native-budgets.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/native-budgets'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/request.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/programme-request'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources-calibration.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/operational-resources'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources-confirmation.example.json',
                                                             role='explicit phase specification or '
                                                                  'operational resource/request selection; '
                                                                  'placeholders do not execute',
                                                             schema_id='empirical-lawhood/matrix-selected-e4/operational-resources'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources.example.json',
                                                             role='selected protected programme operational '
                                                                  'resources; scientific inputs remain '
                                                                  'separately required',
                                                             schema_id='empirical-lawhood/matrix-experimental-programme/selected-operational-resources')),
                                       input_availability='Copied phase specifications, resources and '
                                                          'request examples are supplied with intentionally '
                                                          'nonexecutable placeholder identities.',
                                       scientific_ceiling='Original E3 uncertainty remains in its original '
                                                          'scope; source/issue/reveal custody does not '
                                                          'establish exchangeability or transport.',
                                       first_missing_prerequisite='Select original E3/DEV producers, an '
                                                                  'explicit bank or recipe, actual source '
                                                                  'qualification, issue/execution/reveal and '
                                                                  'operational resources.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/guide.md',
                                       verification_owners=('tests/test_matrix_selected_e4_native.py',
                                                            'tests/test_matrix_selected_e4_native_workers.py',
                                                            'tests/test_matrix_selected_e4_public.py',
                                                            'tests/test_matrix_selected_e4_declarative.py',
                                                            'tests/test_matrix_selected_e4_public_programme.py',
                                                            'tests/test_matrix_selected_e4_bank_recipe.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Declared researcher route; 🟠 Current workflow acceptance required',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=43))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-selected-e4-revision',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_scheduled_history',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select the complete original DEV acquisition, '
                                                       'declared candidates/folds, operational resources and '
                                                       'guarded EL output.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='matrix-selected-e4-protected',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_scheduled_history',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select original E3/DEV producers, an explicit bank '
                                                       'or recipe, actual source qualification, '
                                                       'issue/execution/reveal and operational resources.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
