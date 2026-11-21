# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='rc-challenges',
                                       title='RC history-depth challenges',
                                       kind='current four-phase authoring and issued lifecycle',
                                       substrates=('multiscale disordered RC ladder',),
                                       methods=('effective history rank',
                                                'independent generator adjudication',
                                                'whole-block recurrence'),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'rc-challenge-source-export',
                                                                     boundary='numeric source/export custody',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-challenges/source-export.json',)),
                                                   WorkflowOperation(command='campaign rc-challenge-author',
                                                                     boundary='current phase candidate '
                                                                              'authoring',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/rc-challenges/canary.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/rc-challenges/nomination.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/rc-challenges/development.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/rc-challenges/evaluation.json')),
                                                   WorkflowOperation(command='campaign integration-proof',
                                                                     boundary='no-contact full '
                                                                              'graph/provider proof',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign check-readiness',
                                                                     boundary='existing preissue integrity '
                                                                              'checks',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign run',
                                                                     boundary='issued guarded execution',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign rc-challenge-result',
                                                                     boundary='exact current scientific '
                                                                              'result and prerequisite '
                                                                              'selection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign status',
                                                                     boundary='receipt state inspection',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign resume',
                                                                     boundary='receipt-based bounded '
                                                                              'recovery',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-challenges/canary.json',
                                                             role='editable fixed phase design',
                                                             schema_id='empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-challenges/nomination.json',
                                                             role='editable fixed phase design',
                                                             schema_id='empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-challenges/development.json',
                                                             role='editable fixed phase design',
                                                             schema_id='empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-challenges/evaluation.json',
                                                             role='editable fixed phase design',
                                                             schema_id='empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/rc-challenges/source-export.json',
                                                             role='exposed editable source-export example',
                                                             schema_id='empirical-lawhood/simulator-morphism-challenges/source-export-config')),
                                       input_availability='Supplied phase configs and exposed development '
                                                          'source request; current dependent phases require '
                                                          'explicitly selected upstream receipts.',
                                       scientific_ceiling='Each phase is separately authored and issued; '
                                                          'software proof is not recurrence evidence or new '
                                                          'qualification.',
                                       first_missing_prerequisite='Select current guarded storage and a '
                                                                  'clean source commit; dependent phases '
                                                                  'require exact current source/export and '
                                                                  'upstream custody.',
                                       guide='programmes/foundations/measurement-and-response/workflows/rc-challenges/guide.md',
                                       verification_owners=('tests/test_rc_challenge_integration.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current issued phases',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=18),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='rc-challenges',
                        python_version='3.11.14',
                        distribution_versions=(('numpy', '2.4.6'), ('scipy', '1.17.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=(),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rc-challenge-result',
                          schema_id='empirical-lawhood/simulator-morphism-challenges/retained-result',
                          record_module='empirical_lawhood.domains.history.simulator_morphism_challenges.retained_results',
                          record_name='RCChallengeRetainedResult',
                          disposition='retained',
                          maximum_bytes=16777216,
                          requires_canonical=True,
                          command='campaign rc-challenge-result',
                          owner='RCChallengeRetainedResult',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='rc-challenge-result-authority',
                          schema_id='empirical-lawhood/simulator-morphism-challenges/result-authority-context',
                          record_module='empirical_lawhood.domains.history.simulator_morphism_challenges.retained_results',
                          record_name='RCChallengeResultAuthorityContext',
                          disposition='retained',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign rc-challenge-result',
                          owner='RCChallengeResultAuthorityContext',
                          supplied_inputs=()),
 ConfigurationDeclaration(consumer='rc-challenge-source',
                          schema_id='empirical-lawhood/simulator-morphism-challenges/source-export-config',
                          record_module='empirical_lawhood.domains.history.simulator_morphism_challenges.numeric_inputs',
                          record_name='RCChallengeSourceExportConfig',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign rc-challenge-source-export',
                          owner='RCChallengeSourceExportConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-challenges/source-export.json',)),
 ConfigurationDeclaration(consumer='rc-challenge-phase',
                          schema_id='empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config',
                          record_module='empirical_lawhood.domains.history.simulator_morphism_challenges.contracts',
                          record_name='SimulatorMorphismChallengeConfig',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='campaign rc-challenge-author',
                          owner='SimulatorMorphismChallengeConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/rc-challenges/canary.json',
                                           'programmes/foundations/measurement-and-response/workflows/rc-challenges/nomination.json',
                                           'programmes/foundations/measurement-and-response/workflows/rc-challenges/development.json',
                                           'programmes/foundations/measurement-and-response/workflows/rc-challenges/evaluation.json')))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='rc-challenges',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulator_morphism_challenges',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select current guarded storage and a clean source '
                                                       'commit; dependent phases require exact current '
                                                       'source/export and upstream custody.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
