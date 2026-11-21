# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='reactor-response',
                                       title='Reactor prefix and retained input routes',
                                       kind='development / authoring / input preflight / issued lifecycle',
                                       substrates=('chemical reactor',),
                                       methods=('paired response',),
                                       environment='reactor-example',
                                       operations=(WorkflowOperation(command='example reactor-prefix',
                                                                     boundary='development',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign reactor-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/profile.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'reactor-preissue-proof',
                                                                     boundary='no-contact proof',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'reactor-batch-input-check',
                                                                     boundary='held input preflight',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/batch-input.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'reactor-prepared-input-check',
                                                                     boundary='held input preflight',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/causal-response-study-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/feed-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/finite-control-frontier-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/local-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/matched-replay-history-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/regime-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/selected-action-response-input.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/reactor-response/staged-pulse-response-input.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/batch-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-batch-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/causal-response-study-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/feed-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/finite-control-frontier-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/local-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/matched-replay-history-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/profile.json',
                                                             role='authoring selector',
                                                             schema_id='empirical-lawhood/composition/reactor-prefix-response/fresh-reactor-authoring-profile'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/regime-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/selected-action-response-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/staged-pulse-response-input.json',
                                                             role='held source or parent selector',
                                                             schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/exposed-inventory.json',
                                                             role='illustrative nonpromotable exposure '
                                                                  'metadata',
                                                             schema_id='empirical-lawhood/examples/exposed-inventory'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/finite-response-prior-exposure.json',
                                                             role='illustrative nonpromotable exposure '
                                                                  'metadata',
                                                             schema_id='empirical-lawhood/methods/finite-response-law/native-exposure-metadata'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/prepared-response-prior-exposure.json',
                                                             role='illustrative nonpromotable exposure '
                                                                  'metadata',
                                                             schema_id='empirical-lawhood/composition/prepared-response/prepared-exposure-inspection'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/reactor-assigned-exposed.json',
                                                             role='retained assigned exposed profile',
                                                             schema_id='empirical-lawhood/composition/reactor-prefix-response/assigned-reactor-authoring-profile')),
                                       input_availability='Public prefix inputs; authentic held sources and '
                                                          'complete census for other routes.',
                                       scientific_ceiling='Five exposed demo units; held batch census is42 '
                                                          'units, not a fresh result.',
                                       first_missing_prerequisite='Issued work needs clean source, complete '
                                                                  'exposure census, storage and distinct '
                                                                  'authorities.',
                                       guide='programmes/foundations/measurement-and-response/workflows/reactor-response/guide.md',
                                       verification_owners=('tests/test_reactor_native_science.py',
                                                            'tests/test_reactor_held_native_science.py',
                                                            'tests/test_reactor_prepared_input.py',
                                                            'tests/test_reactor_port_store.py',
                                                            'tests/test_reactor_upstream_binding.py',
                                                            'tests/test_reactor_classical_selected_action.py',
                                                            'tests/test_reactor_empirical_synthetic_consumers.py',
                                                            'tests/test_reactor_distinct_transform_boundaries.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Assigned prefix lifecycle; 🔵 Development authoring; 🟠 Other input '
                                   'checks',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=22),)

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='reactor',
                        python_version='3.11.14',
                        distribution_versions=(('numpy', '2.4.6'),),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('reactor-example',),
                        supported_platforms=(('Linux', 'x86_64'),)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='reactor-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.reactor.reactor_prefix_response',
                                 adapter_version='1.0.0',
                                 controller_environment='reactor',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Issued work needs clean source, complete exposure '
                                                       'census, storage and distinct authorities.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
