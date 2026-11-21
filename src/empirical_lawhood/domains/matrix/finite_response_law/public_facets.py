# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-inputs',
                                       title='Current matrix sources and reusable finite operands',
                                       kind='explicit native development source / saved-operand analysis',
                                       substrates=('six-matrix Q2/CIR1 preparations',),
                                       methods=('bounded current source transport',
                                                'mechanical transient bridge',
                                                'fixed original numerical F'),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign matrix-source-config',
                                                                     boundary='derive source identities from '
                                                                              'edited allocations',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign original-f-export',
                                                                     boundary='fixed operand delivery with '
                                                                              'provenance',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign original-f-check',
                                                                     boundary='bounded authentication',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign matrix-source-export',
                                                                     boundary='declared bounded native '
                                                                              'roster',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-inputs/allocation.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-source-export',
                                                                     boundary='fixed24 native development '
                                                                              'source',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-inputs/allocation.json')),
                                                   WorkflowOperation(command='campaign '
                                                                             'preparation-operands-export',
                                                                     boundary='guarded saved-fit operands '
                                                                              'and actual numerical '
                                                                              'provenance',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-inputs/allocation.json',
                                                             role='exposed editable root/purpose/split '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/kernel/matrix-allocation'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json',
                                                             role='editable generic source selector',
                                                             schema_id='empirical-lawhood/methods/finite-response-law/matrix-preparation-source-config'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json',
                                                             role='editable fixed24 source selector',
                                                             schema_id='empirical-lawhood/methods/finite-response-law/current-preparation-source-config')),
                                       input_availability='Supplied exposed source/allocation examples and '
                                                          'installed exact original-F provenance; realised '
                                                          'arrays must be explicitly acquired or '
                                                          'authenticated.',
                                       scientific_ceiling='Development/transfer operands, qualification '
                                                          'NONE; declared split roles do not grant '
                                                          'scientific eligibility.',
                                       first_missing_prerequisite='Select an explicit guarded storage '
                                                                  'profile before native contact; saved fits '
                                                                  'require complete authenticated native '
                                                                  'arrays.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-inputs/guide.md',
                                       verification_owners=('tests/test_matrix_operand_transport.py',
                                                            'tests/test_current_preparation_source.py',
                                                            'tests/test_transient_bridge.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current source export; 🟠 Operand checks / transforms',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=19),
 WorkflowDeclaration(workflow=Workflow(workflow_id='finite-response-law',
                                       title='Finite response law current calibration and composition',
                                       kind='current authoring / issued lifecycle / exposed diagnostics',
                                       substrates=('six-matrix medium',),
                                       methods=('finite response law', 'response-composition power'),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'finite-response-allocation',
                                                                     boundary='expand explicit current '
                                                                              'numeric allocation',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign nomination-export',
                                                                     boundary='fixed nominated coefficients '
                                                                              'with provenance',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign nomination-check',
                                                                     boundary='fixed nomination '
                                                                              'authentication',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-packet',
                                                                     boundary='prepare current typed stage '
                                                                              'operands',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-parent',
                                                                     boundary='join actual current native '
                                                                              'and qualification '
                                                                              'publications',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-result',
                                                                     boundary='actual current protected '
                                                                              'scientific readout',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-author',
                                                                     boundary='current '
                                                                              'calibration/qualification/evaluation '
                                                                              'candidate authoring',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/finite-response-law/rerun-calibration.json',)),
                                                   WorkflowOperation(command='campaign integration-proof',
                                                                     boundary='full-size no-contact '
                                                                              'graph/provider proof',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-bind-runtime',
                                                                     boundary='actual current post-issue '
                                                                              'authority binding',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign run',
                                                                     boundary='issued guarded execution',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign status',
                                                                     boundary='current receipt/scientific '
                                                                              'disposition inspection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign resume',
                                                                     boundary='receipt-based bounded '
                                                                              'recovery',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/finite-response-law/finite-canary.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'response-composition-power',
                                                                     boundary='design diagnostic',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-input-check',
                                                                     boundary='assignment preflight',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/finite-response-law/finite-calibration-input.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'finite-response-stage-input-check',
                                                                     boundary='guarded stage preflight',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-stage-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/informative-composition-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/preparation-screen-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-continuation-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-evaluation-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/finite-response-law/supplemental-development-input.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/rerun-calibration.json',
                                                             role='exposed editable current calibration '
                                                                  'packet',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/rerun-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/current-calibration-allocation.json',
                                                             role='exposed editable32-root current '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/current-allocation'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/current-evaluation-allocation.json',
                                                             role='exposed editable64-root current '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/current-allocation'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/current-exposure.json',
                                                             role='authenticated original/public allocation '
                                                                  'census',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/current-exposure'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-stage-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/finite-calibration-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-calibration-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/finite-canary.json',
                                                             role='native canary',
                                                             schema_id='empirical-lawhood/simulators/finite-response-law/finite-response-law-canary'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/informative-composition-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/preparation-screen-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-continuation-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-evaluation-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/finite-response-law/supplemental-development-input.json',
                                                             role='retained stage selector',
                                                             schema_id='empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input')),
                                       input_availability='Supplied exposed current32/64 allocation and '
                                                          'fixed nomination examples; authentic current '
                                                          'parent publications and grants are selected after '
                                                          'execution.',
                                       scientific_ceiling='Full-size current '
                                                          'calibration/qualification/evaluation authoring; '
                                                          'public examples remain exposed and software proof '
                                                          'is not scientific qualification.',
                                       first_missing_prerequisite='A clean source commit, guarded storage '
                                                                  'and current issue/execution/reveal '
                                                                  'authority; evaluation requires an actual '
                                                                  'qualified current parent.',
                                       guide='programmes/foundations/emergent-structure/workflows/finite-response-law/guide.md',
                                       verification_owners=('tests/test_finite_response_native_quickstart.py',
                                                            'tests/test_finite_response_assignment.py',
                                                            'tests/test_finite_response_assigned_native.py',
                                                            'tests/test_finite_response_assigned_factory.py',
                                                            'tests/test_finite_response_assigned_method_records.py',
                                                            'tests/test_finite_response_assigned_evaluation_binding.py',
                                                            'tests/test_finite_response_native_input.py',
                                                            'tests/test_finite_response_consumer_binding.py',
                                                            'tests/test_finite_response_retained_development_input.py',
                                                            'tests/test_finite_response_stage_input.py',
                                                            'tests/test_finite_response_method_counterexamples.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current C32/E64 phases; 🟡 Development diagnostics; 🟠 Input checks',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=26))

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='finite-response-law',
                        python_version='3.11.14',
                        distribution_versions=(('numpy', '2.4.6'), ('scipy', '1.17.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=(),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='original-f',
                          schema_id='empirical-lawhood/methods/finite-response-law/original-finite-response-law',
                          record_module='empirical_lawhood.domains.matrix.finite_response_law.original_f',
                          record_name='OriginalFiniteResponseLaw',
                          disposition='retained',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign original-f-check',
                          owner='OriginalFiniteResponseLaw',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='current-nomination',
                          schema_id='empirical-lawhood/methods/finite-response-law/current-nomination-operand',
                          record_module='empirical_lawhood.domains.matrix.finite_response_law.nominated_package',
                          record_name='CurrentNominationOperand',
                          disposition='retained',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign nomination-check',
                          owner='CurrentNominationOperand',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='preparation-source',
                          schema_id='empirical-lawhood/methods/finite-response-law/current-preparation-source-config',
                          record_module='empirical_lawhood.domains.matrix.finite_response_law.transient_bridge_source_records',
                          record_name='CurrentPreparationSourceConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign preparation-source-export',
                          owner='CurrentPreparationSourceConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json',)),
 ConfigurationDeclaration(consumer='matrix-source',
                          schema_id='empirical-lawhood/methods/finite-response-law/matrix-preparation-source-config',
                          record_module='empirical_lawhood.domains.matrix.finite_response_law.transient_bridge_source_records',
                          record_name='MatrixPreparationSourceConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign matrix-source-export',
                          owner='MatrixPreparationSourceConfig',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json',)))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-inputs',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.finite_response_law',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select an explicit guarded storage profile before '
                                                       'native contact; saved fits require complete '
                                                       'authenticated native arrays.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='finite-response-law',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.finite_response_law',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('A clean source commit, guarded storage and current '
                                                       'issue/execution/reveal authority; evaluation '
                                                       'requires an actual qualified current parent.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
