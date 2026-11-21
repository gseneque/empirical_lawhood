# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='preparation-diagnostics',
                                       title='Applicability sensitivity diagnostics',
                                       kind='authenticated current Q8/E32 retained-result analysis',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Applicability sensitivity diagnostics',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'preparation-diagnostic-phase-prepare',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-diagnostics-prepare',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-diagnostics',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-diagnostics-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=())),
                                       inputs=(),
                                       input_availability='Derive exact Q8/E32 phase inputs from current '
                                                          'complete terminal indexes and explicitly selected '
                                                          'grants; no fabricated example receipts.',
                                       scientific_ceiling='Outcome-visible post-hoc sensitivity; original F '
                                                          'and original sealed choices remain unchanged; Q8 '
                                                          'is not E32 confirmation.',
                                       first_missing_prerequisite='Complete current constructed Q/E runs and '
                                                                  'retain actual issue/execution/reveal '
                                                                  'authority before protected reads.',
                                       guide='programmes/foundations/emergent-structure/workflows/preparation-diagnostics/guide.md',
                                       verification_owners=('tests/test_preparation_diagnostics.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current retained analysis',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=17),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='preparation-diagnostic-phase',
                          schema_id='empirical-lawhood/constructed-preparation-applicability/diagnostic-phase-input',
                          record_module='empirical_lawhood.domains.matrix.constructed_preparation_applicability.diagnostic_records',
                          record_name='PreparationDiagnosticPhaseInput',
                          disposition='retained',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign preparation-diagnostic-phase-prepare',
                          owner='PreparationDiagnosticPhaseInput',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-diagnostics',
                          schema_id='empirical-lawhood/constructed-preparation-applicability/diagnostic-input',
                          record_module='empirical_lawhood.domains.matrix.constructed_preparation_applicability.diagnostic_records',
                          record_name='PreparationDiagnosticInput',
                          disposition='editable',
                          maximum_bytes=8388608,
                          requires_canonical=True,
                          command='campaign preparation-diagnostics',
                          owner='PreparationDiagnosticInput',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='constructed-preparation-applicability-stage',
                          schema_id='empirical-lawhood/constructed-preparation-applicability/stage',
                          record_module='empirical_lawhood.domains.matrix.constructed_preparation_applicability.config',
                          record_name='ConstructedPreparationStage',
                          disposition='editable',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign preparation-author',
                          owner='ConstructedPreparationStage',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='constructed-preparation-applicability-source',
                          schema_id='empirical-lawhood/constructed-preparation-applicability/source',
                          record_module='empirical_lawhood.domains.matrix.constructed_preparation_applicability.config',
                          record_name='ConstructedPreparationSource',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign preparation-author',
                          owner='ConstructedPreparationSource',
                          supplied_inputs=()))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='preparation-diagnostics',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.constructed_preparation_applicability',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Complete current constructed Q/E runs and retain '
                                                       'actual issue/execution/reveal authority before '
                                                       'protected reads.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
