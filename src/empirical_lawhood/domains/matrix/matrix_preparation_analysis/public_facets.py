# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-tangent',
                                       title='Coupled tangent preparation',
                                       kind='current declared preparations and retained tangent analysis',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Coupled tangent preparation',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign matrix-tangent-config',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-tangent-source-export',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-tangent-analyze',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-analysis-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',
                                                             role='editable full tangent roster and '
                                                                  'pre-outcome ranks',
                                                             schema_id='empirical-lawhood/methods/matrix-preparation-analysis/tangent-preparation-config'),),
                                       input_availability='Exposed full128-root source/rank recipe supplied; '
                                                          'realised preparations are separately acquired.',
                                       scientific_ceiling='Outcome-visible exploratory comparison; future '
                                                          'and numerical views remain nested whole-root '
                                                          'measurements.',
                                       first_missing_prerequisite='Select guarded storage; analysis needs '
                                                                  'exact current saved source arrays and '
                                                                  'manifests.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-tangent/guide.md',
                                       verification_owners=('tests/test_matrix_preparation_analysis.py',
                                                            'tests/test_matrix_preparation_differential.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current acquisition / analysis',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=15),
 WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-transient',
                                       title='Radial increments and baseline support',
                                       kind='retained current preparation transfer and support analysis',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Radial increments and baseline support',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'preparation-operands-export',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json')),
                                                   WorkflowOperation(command='campaign original-f-export',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-transient-analyze',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-baseline-analyze',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-analysis-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',
                                                             role='editable transient population selector',
                                                             schema_id='empirical-lawhood/methods/matrix-preparation-analysis/transient-analysis-config'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json',
                                                             role='editable baseline comparison selector',
                                                             schema_id='empirical-lawhood/methods/matrix-preparation-analysis/baseline-support-config')),
                                       input_availability='Selectors supplied; use current authenticated '
                                                          'native/bridge arrays and installed original '
                                                          'numerical F.',
                                       scientific_ceiling='Descriptive exploratory transfer; width estimates '
                                                          'confer no prospective qualification.',
                                       first_missing_prerequisite='Acquire current preparation source and '
                                                                  'export its saved kernels/fold fits; '
                                                                  'baseline reuses the retained transient '
                                                                  'result.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-transient/guide.md',
                                       verification_owners=('tests/test_matrix_preparation_analysis.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current retained analysis',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=16))

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='matrix-transient-analysis',
                          schema_id='empirical-lawhood/methods/matrix-preparation-analysis/transient-analysis-config',
                          record_module='empirical_lawhood.domains.matrix.matrix_preparation_analysis.records',
                          record_name='TransientAnalysisConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign matrix-transient-analyze',
                          owner='TransientAnalysisConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',)),
 ConfigurationDeclaration(consumer='matrix-baseline-analysis',
                          schema_id='empirical-lawhood/methods/matrix-preparation-analysis/baseline-support-config',
                          record_module='empirical_lawhood.domains.matrix.matrix_preparation_analysis.records',
                          record_name='BaselineSupportConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign matrix-baseline-analyze',
                          owner='BaselineSupportConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json',)),
 ConfigurationDeclaration(consumer='matrix-tangent',
                          schema_id='empirical-lawhood/methods/matrix-preparation-analysis/tangent-preparation-config',
                          record_module='empirical_lawhood.domains.matrix.matrix_preparation_analysis.tangent_records',
                          record_name='TangentPreparationConfig',
                          disposition='editable',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign matrix-tangent-source-export',
                          owner='TangentPreparationConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',)))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-tangent',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_preparation_analysis',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select guarded storage; analysis needs exact current '
                                                       'saved source arrays and manifests.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='matrix-transient',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_preparation_analysis',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Acquire current preparation source and export its '
                                                       'saved kernels/fold fits; baseline reuses the '
                                                       'retained transient result.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
