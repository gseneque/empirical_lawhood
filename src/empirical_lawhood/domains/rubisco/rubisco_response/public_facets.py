# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rubisco-response',
                                       title='Paired Rubisco response and conditional joint decision',
                                       kind='source-bound exposed conditional experiment',
                                       substrates=('paired WT/mutant rate evidence',),
                                       methods=('exact four-state kinetics',
                                                'independent scenario-union assessment'),
                                       environment='selected locked numerical environment or installed '
                                                   'rubisco-prediction profile; one worker',
                                       operations=(WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='inspect exact source and '
                                                                              'complete case/scenario census',
                                                                     inputs=('programmes/biology/photosynthesis/workflows/rubisco-response/experiment.json',
                                                                             'programmes/biology/photosynthesis/workflows/rubisco-response/experiment-sources.json')),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='freeze selected criteria and '
                                                                              'original source bindings',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='compute paired conditional '
                                                                              'predictions and independent '
                                                                              'assessments',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate retained '
                                                                              'products and original '
                                                                              'receipts',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='recover completed work '
                                                                              'without acquisition',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-response/experiment.json',
                                                             role='editable decision and acceptance criteria '
                                                                  'over exact original evidence',
                                                             schema_id='empirical-lawhood/rubisco-response/experiment-specification'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-response/experiment-sources.json',
                                                             role='exact original study selector',
                                                             schema_id='empirical-lawhood/experiment-inputs/selection'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-response/study.json',
                                                             role='immutable complete exposed cases, '
                                                                  'contexts, rates and allocation',
                                                             schema_id='empirical-lawhood/rubisco-response/study')),
                                       input_availability='Disclosed candidate and no-change control '
                                                          'supplied; real source evidence requires '
                                                          'separately identified complete records.',
                                       scientific_ceiling='Conditional numerical support with zero '
                                                          'biological units; predictive validity, Gp '
                                                          'applicability and computational benefit remain '
                                                          'unestablished.',
                                       first_missing_prerequisite='Bind exact original study, actual '
                                                                  'implementation/environment and guarded '
                                                                  'output custody; retain all reported '
                                                                  'scientific requirements.',
                                       guide='programmes/biology/photosynthesis/workflows/rubisco-response/guide.md',
                                       verification_owners=('tests/test_rubisco_response_public.py',
                                                            'tests/test_rubisco_response_study.py'),
                                       output_retention='Complete cases, scenarios, raw/anchored paired '
                                                        'values, independent decisions, open requirements '
                                                        'and original receipts.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Paired conditional software; 🟠 Prediction and benefit unresolved',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=8),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rubisco-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.rubisco.rubisco_response',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Bind exact original study, actual '
                                                       'implementation/environment and guarded output '
                                                       'custody; retain all reported scientific '
                                                       'requirements.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
