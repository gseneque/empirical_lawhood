# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-history-analysis',
                                       title='Algebra persistence and passive prediction',
                                       kind='current history acquisition or exposed saved-array analysis',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Algebra persistence and passive prediction',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'matrix-history-allocation',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-history-source-config',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-history-source-export',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
                                                   WorkflowOperation(command='campaign matrix-history-import',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-history-analyze',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
                                                   WorkflowOperation(command='campaign matrix-history-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',
                                                             role='editable exposed complete256-root '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/matrix-history-analysis/allocation'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',
                                                             role='editable current source selector',
                                                             schema_id='empirical-lawhood/matrix-history-analysis/source-config'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                                             role='editable algebra analysis selector',
                                                             schema_id='empirical-lawhood/matrix-history-analysis/analysis-config'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json',
                                                             role='editable passive analysis selector',
                                                             schema_id='empirical-lawhood/matrix-history-analysis/analysis-config'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json',
                                                             role='retained descriptive programme selection',
                                                             schema_id='empirical-lawhood/matrix-history-analysis/programme-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme-sources.json',
                                                             role='descriptive programme input selector',
                                                             schema_id='empirical-lawhood/experiment-inputs/selection')),
                                       input_availability='Supplied source/allocation/analysis inputs; '
                                                          'acquire each history or explicitly import exposed '
                                                          'arrays.',
                                       scientific_ceiling='Whole stochastic histories are independent; '
                                                          'incomplete roots remain UNENTERED/UNEVALUABLE; no '
                                                          'inferred native or qualification attestation.',
                                       first_missing_prerequisite='Select guarded storage and current '
                                                                  'source/lock; missing history pairs retain '
                                                                  'the full requested denominator.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-history-analysis/guide.md',
                                       verification_owners=('tests/test_matrix_history_science.py',
                                                            'tests/test_matrix_history_public_api.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current acquisition / analysis; 🟠 Exposed-array import',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=14),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='matrix-history-allocation',
                          schema_id='empirical-lawhood/matrix-history-analysis/allocation',
                          record_module='empirical_lawhood.domains.matrix.matrix_history_analysis.records',
                          record_name='MatrixHistoryAllocation',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign matrix-history-allocation',
                          owner='MatrixHistoryAllocation',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',)),
 ConfigurationDeclaration(consumer='matrix-history-source',
                          schema_id='empirical-lawhood/matrix-history-analysis/source-config',
                          record_module='empirical_lawhood.domains.matrix.matrix_history_analysis.records',
                          record_name='MatrixHistorySourceConfig',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign matrix-history-source-export',
                          owner='MatrixHistorySourceConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',)),
 ConfigurationDeclaration(consumer='matrix-history-analysis',
                          schema_id='empirical-lawhood/matrix-history-analysis/analysis-config',
                          record_module='empirical_lawhood.domains.matrix.matrix_history_analysis.records',
                          record_name='MatrixHistoryAnalysisConfig',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign matrix-history-analyze',
                          owner='MatrixHistoryAnalysisConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json',
                                           'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-history-analysis',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_history_analysis',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select guarded storage and current source/lock; '
                                                       'missing history pairs retain the full requested '
                                                       'denominator.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
