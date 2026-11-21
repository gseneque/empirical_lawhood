# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rc-ladder-response',
                                       title='Numerical RC ladder',
                                       kind='development / candidate authoring',
                                       substrates=('numerical resistor-capacitor ladder',),
                                       methods=('numerical response conformance',),
                                       environment='reactor-example',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'rc-ladder-native-check',
                                                                     boundary='development',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json',)),
                                                   WorkflowOperation(command='campaign circuit-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/study.json',)),
                                                   WorkflowOperation(command='campaign check-readiness',
                                                                     boundary='no-contact proof',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json',
                                                             role='native model',
                                                             schema_id='empirical-lawhood/adapters/simulators/rc-ladder-response/resistor-capacitor-ladder-model-config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-ladder-response/study.json',
                                                             role='candidate study',
                                                             schema_id='empirical-lawhood/simulators/rc-ladder-response/resistor-capacitor-ladder-study-config')),
                                       input_availability='Public model and study; physical component '
                                                          'metrology is not supplied.',
                                       scientific_ceiling='Two nested solver views of one synthetic model '
                                                          'unit; no physical-board result.',
                                       first_missing_prerequisite='Fresh physical source/custody and broader '
                                                                  'circuit integration remain separate.',
                                       guide='programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md',
                                       verification_owners=('tests/test_resistor_capacitor_candidate.py',
                                                            'tests/test_resistor_capacitor_study.py',
                                                            'tests/test_resistor_capacitor_native_science.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Development authoring; 🟡 Native check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=28),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rc-ladder-model',
                          schema_id='empirical-lawhood/adapters/simulators/rc-ladder-response/resistor-capacitor-ladder-model-config',
                          record_module='empirical_lawhood.domains.circuits.rc_ladder.contracts',
                          record_name='ResistorCapacitorLadderModelConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign rc-ladder-native-check',
                          owner='ResistorCapacitorLadderModelConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json',)),
 ConfigurationDeclaration(consumer='rc-ladder-study',
                          schema_id='empirical-lawhood/simulators/rc-ladder-response/resistor-capacitor-ladder-study-config',
                          record_module='empirical_lawhood.domains.circuits.rc_ladder.contracts',
                          record_name='ResistorCapacitorLadderStudyConfig',
                          disposition='editable',
                          maximum_bytes=131072,
                          requires_canonical=True,
                          command='campaign circuit-author',
                          owner='ResistorCapacitorLadderStudyConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/study.json',)))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rc-ladder-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.rc_ladder_response',
                                 adapter_version='1.0.0',
                                 controller_environment='reactor',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Fresh physical source/custody and broader circuit '
                                                       'integration remain separate.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
