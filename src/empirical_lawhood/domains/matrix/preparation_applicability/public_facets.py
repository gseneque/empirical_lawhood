# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='preparation-applicability',
                                       title='Ordinary screens and constructed preparation applicability',
                                       kind='current D/E and Q/E authoring / independent diagnostic '
                                            'reductions',
                                       substrates=('ordinary and fixed-nominal six-matrix preparations',),
                                       methods=('original-F seven-conjunct validity',
                                                'constructor gate',
                                                'whole-root service',
                                                'retained entry readiness'),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'preparation-allocation-prepare',
                                                                     boundary='expand explicit '
                                                                              'ordinary/constructed purpose '
                                                                              'allocations',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-conformance',
                                                                     boundary='bounded current native '
                                                                              'software conformance',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/preparation-applicability/conformance-allocation.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-exposure-inspect',
                                                                     boundary='inspect actual prior numeric '
                                                                              'allocations',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-input-publish',
                                                                     boundary='outcome-blind fixed input '
                                                                              'publication',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-selection-prepare',
                                                                     boundary='prepare current stage/source '
                                                                              'from published inputs',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign preparation-result',
                                                                     boundary='actual current '
                                                                              'ordinary/constructed '
                                                                              'scientific result',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign preparation-q-bind',
                                                                     boundary='actual current qualified '
                                                                              'result selection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-panel-bind',
                                                                     boundary='exact current ordinary panel '
                                                                              'selection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-panel-export',
                                                                     boundary='export saved ordinary '
                                                                              'diagnostic operands',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign preparation-author',
                                                                     boundary='exact ordinary or constructed '
                                                                              'current selection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign integration-proof',
                                                                     boundary='no-contact full '
                                                                              'graph/provider proof',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign run',
                                                                     boundary='issued guarded acquisition '
                                                                              'and evaluation',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign preparation-screen',
                                                                     boundary='ordinary96 headroom and '
                                                                              'retrospective prefix '
                                                                              'forecasts',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign preparation-readiness',
                                                                     boundary='guarded saved current24 '
                                                                              'actual-failure entry screen',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign status',
                                                                     boundary='receipt and scientific '
                                                                              'disposition inspection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign resume',
                                                                     boundary='receipt-based bounded '
                                                                              'recovery',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/preparation-applicability/conformance-allocation.json',
                                                             role='exposed editable three-source conformance '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/kernel/matrix-allocation'),),
                                       input_availability='Select current OriginalF/exposure import '
                                                          'publications and actual source conformance; E '
                                                          'additionally requires exact completed currentQ '
                                                          'custody. No synthetic qualification is supplied.',
                                       scientific_ceiling='Ordinary96/readiness are exposed screens; '
                                                          'constructed E requires the fixed newQ gate before '
                                                          'prefix contact and evaluates all32 assigned '
                                                          'roots.',
                                       first_missing_prerequisite='Authenticate fixed OriginalF/current '
                                                                  'source conformance and exposure; missing '
                                                                  'or failedQ leaves constructedE unentered '
                                                                  'before native contact.',
                                       guide='programmes/foundations/emergent-structure/workflows/preparation-applicability/guide.md',
                                       verification_owners=('tests/test_preparation_applicability_reducers.py',
                                                            'tests/test_constructed_preparation_applicability_qualification.py',
                                                            'tests/test_current_preparation_readiness.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current phases; 🟡 Development screens',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=20),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='preparation-applicability',
                        python_version='3.11.14',
                        distribution_versions=(('numpy', '2.4.6'), ('scipy', '1.17.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=(),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='preparation-retained-result',
                          schema_id='empirical-lawhood/preparation-applicability/retained-result',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.result_access',
                          record_name='PreparationApplicabilityRetainedResult',
                          disposition='retained',
                          maximum_bytes=16777216,
                          requires_canonical=True,
                          command='campaign preparation-result',
                          owner='PreparationApplicabilityRetainedResult',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-native-conformance',
                          schema_id='empirical-lawhood/preparation-applicability/native-conformance',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.conformance',
                          record_name='PreparationApplicabilityNativeConformance',
                          disposition='retained',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign preparation-conformance',
                          owner='PreparationApplicabilityNativeConformance',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-exposure-inspection',
                          schema_id='empirical-lawhood/preparation-applicability/exposure-inspection',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.issued_inputs',
                          record_name='PreparationApplicabilityExposureInspection',
                          disposition='retained',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign preparation-exposure-inspect',
                          owner='PreparationApplicabilityExposureInspection',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-published-input',
                          schema_id='empirical-lawhood/preparation-applicability/published-input',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.issued_inputs',
                          record_name='PreparationApplicabilityPublishedInput',
                          disposition='retained',
                          maximum_bytes=16777216,
                          requires_canonical=True,
                          command='campaign preparation-input-publish',
                          owner='PreparationApplicabilityPublishedInput',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-panel-publication',
                          schema_id='empirical-lawhood/preparation-applicability/panel-publication',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.panel_inputs',
                          record_name='PreparationApplicabilityPanelPublication',
                          disposition='retained',
                          maximum_bytes=16777216,
                          requires_canonical=True,
                          command='campaign preparation-panel-bind',
                          owner='PreparationApplicabilityPanelPublication',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-applicability-stage',
                          schema_id='empirical-lawhood/preparation-applicability/stage',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.config',
                          record_name='PreparationApplicabilityStage',
                          disposition='editable',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign preparation-author',
                          owner='PreparationApplicabilityStage',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-applicability-source',
                          schema_id='empirical-lawhood/preparation-applicability/source',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.config',
                          record_name='PreparationApplicabilitySource',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign preparation-author',
                          owner='PreparationApplicabilitySource',
                          supplied_inputs=()))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='preparation-applicability',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.preparation_applicability',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Authenticate fixed OriginalF/current source '
                                                       'conformance and exposure; missing or failedQ leaves '
                                                       'constructedE unentered before native contact.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
