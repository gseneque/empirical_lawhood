# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='prepared-response',
                                       title='Prepared matrix response',
                                       kind='development / authoring / parent preflight',
                                       substrates=('six-matrix medium',),
                                       methods=('paired prepared response',),
                                       environment='reactor-example',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'prepared-response-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-canary.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-response-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-source-qualification-author.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'dependent-response-input-check',
                                                                     boundary='guarded parent preflight',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-dependent-refinement-input.json',
                                                                             'programmes/foundations/emergent-structure/workflows/prepared-response/prepared-fresh-response-calibration-input.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/prepared-response/prepared-canary.json',
                                                             role='native canary',
                                                             schema_id='empirical-lawhood/simulators/prepared-response/prepared-response-prepared-canary'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/prepared-response/prepared-dependent-refinement-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/composition/prepared-response/prepared-response-dependent-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/prepared-response/prepared-fresh-response-calibration-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/composition/prepared-response/prepared-response-dependent-input'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/prepared-response/prepared-source-qualification-author.json',
                                                             role='authoring selector',
                                                             schema_id='empirical-lawhood/composition/prepared-response/prepared-response-native-authoring-input')),
                                       input_availability='Public canary; held plan/design/census and '
                                                          'qualified parents are not supplied.',
                                       scientific_ceiling='One exposed canary; candidate is '
                                                          'EXPOSED_DEVELOPMENT_NONPROMOTABLE.',
                                       first_missing_prerequisite='Dependent stages need authentic qualified '
                                                                  'parents and separate reveal/analysis '
                                                                  'authority.',
                                       guide='programmes/foundations/emergent-structure/workflows/prepared-response/guide.md',
                                       verification_owners=('tests/test_prepared_response_development_input.py',
                                                            'tests/test_prepared_response_held_source.py',
                                                            'tests/test_response_parent_custody.py',
                                                            'tests/test_response_dependent_binding.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Development authoring; 🟡 Native check; 🟠 Parent preflight',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=23),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='prepared-response',
                        python_version='3.11.14',
                        distribution_versions=(('numpy', '2.4.6'),),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('reactor-example',),
                        supported_platforms=(('Linux', 'x86_64'),)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='prepared-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.prepared_response',
                                 adapter_version='1.0.0',
                                 controller_environment='prepared-response',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Dependent stages need authentic qualified parents '
                                                       'and separate reveal/analysis authority.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
