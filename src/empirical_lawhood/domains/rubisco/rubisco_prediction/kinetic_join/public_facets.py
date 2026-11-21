# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rubisco-kinetic-join',
                                       title='Supplied Rubisco kinetics and conditional joint assessment',
                                       kind='exposed conditional numerical software example',
                                       substrates=('supplied apparent Rubisco kinetics',),
                                       methods=('stationary product assay',
                                                'independent flux/product assessment',
                                                'exact joint endpoint support'),
                                       environment='selected locked main numerical or installed '
                                                   'rubisco-prediction profile; no molecular environment',
                                       operations=(WorkflowOperation(command='campaign recursive-explain',
                                                                     boundary='inspect selected analytical '
                                                                              'operands; no execution',
                                                                     inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json',)),
                                                   WorkflowOperation(command='campaign recursive-author',
                                                                     boundary='strict source-bound closed '
                                                                              'wave; no acquisition',
                                                                     inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json',
                                                                             'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/supply.json',
                                                                             'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/query.json',
                                                                             'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/comparison.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'recursive-development-run',
                                                                     boundary='registered assay and '
                                                                              'independent numerical '
                                                                              'consumer through the shared '
                                                                              'scheduler',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'recursive-development-result',
                                                                     boundary='authenticate complete '
                                                                              'retained products and '
                                                                              'receipts without '
                                                                              'reacquisition',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json',
                                                             role='editable closed conditional development '
                                                                  'wave',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment.json',
                                                             role='editable conditional kinetic experiment '
                                                                  'specification',
                                                             schema_id='empirical-lawhood/rubisco-kinetic-experiment/specification'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment-sources.json',
                                                             role='explicit copied scientific and '
                                                                  'operational input selector',
                                                             schema_id='empirical-lawhood/experiment-inputs/selection'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/campaign.json',
                                                             role='explicit exposed development campaign '
                                                                  'selection',
                                                             schema_id='empirical-lawhood/planning/campaign-spec'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/supply.json',
                                                             role='exact disclosed supplied, partial and '
                                                                  'rejected kinetic members',
                                                             schema_id='empirical-lawhood/rubisco/kinetic-supply/joint-supply'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/query.json',
                                                             role='exact stationary clamped dissolved-gas '
                                                                  'action',
                                                             schema_id='empirical-lawhood/simulators/rubisco-assay/query'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/comparison.json',
                                                             role='conditional displayed reference bounds; '
                                                                  'not challenge controls',
                                                             schema_id='empirical-lawhood/rubisco/kinetic-supply/target-comparison'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/assumptions.json',
                                                             role='informational synthetic source witness; '
                                                                  'no measured biological units',
                                                             schema_id='empirical-lawhood/examples/disclosed-rubisco-kinetic-assumption')),
                                       input_availability='Complete disclosed three-member roster and exact '
                                                          'external input bindings supplied; missing '
                                                          'oxygenation and rejected members remain in the '
                                                          'denominator.',
                                       scientific_ceiling='Conditional numerical software conformance, '
                                                          'unknown covariance, zero fresh biological units; '
                                                          'no mutant prediction, probability, nomination or '
                                                          'challenge success.',
                                       first_missing_prerequisite='Select exact copied inputs, selected '
                                                                  'producing checkout/environment and '
                                                                  'guarded output storage. Real biological '
                                                                  'use additionally requires assessed '
                                                                  'kinetics, domain/assay joins and '
                                                                  'uncertainty.',
                                       guide='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/guide.md',
                                       verification_owners=('tests/test_rubisco_kinetic_supply.py',
                                                            'tests/test_rubisco_kinetic_join.py',
                                                            'tests/test_rubisco_kinetic_public.py'),
                                       output_retention='Complete supported-member outcomes, actual solver '
                                                        'calls and independent numerical assessment bind '
                                                        'primary receipts. Completed recovery performs no '
                                                        'new assay work.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Exposed conditional software; 🟠 Biological prediction unresolved',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=9),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rubisco-kinetic-assumptions',
                          schema_id='empirical-lawhood/examples/disclosed-rubisco-kinetic-assumption',
                          record_module='empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.disclosed_examples',
                          record_name='DisclosedAssumption',
                          disposition='retained',
                          maximum_bytes=None,
                          requires_canonical=True,
                          command='campaign recursive-author',
                          owner='DisclosedAssumption',
                          supplied_inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/assumptions.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rubisco-kinetic-join',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select exact copied inputs, selected producing '
                                                       'checkout/environment and guarded output storage. '
                                                       'Real biological use additionally requires assessed '
                                                       'kinetics, domain/assay joins and uncertainty.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
