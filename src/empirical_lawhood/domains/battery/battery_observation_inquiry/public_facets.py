# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='battery-initial-window-observation',
                                       title='Inspect battery initial-window preparation observations',
                                       kind='installed ordinary operations; concise programme protocol '
                                            'remains unavailable',
                                       substrates=('PyBaMM initial-window observations',),
                                       methods=('segmented native observation',
                                                'complete state/derivative comparison',
                                                'receipt-based recovery'),
                                       environment='locked battery-recursion profile; original acquisition '
                                                   'holds remain binding',
                                       operations=(),
                                       inputs=(),
                                       input_availability='The guide identifies original parent, frozen '
                                                          'observation/preparation/entry/source records and '
                                                          'actual storage prerequisites.',
                                       scientific_ceiling='Initial-window observations do not complete full '
                                                          'forecasts, supplier admission or later use; '
                                                          'original negative comparisons remain retained.',
                                       first_missing_prerequisite='SOFTWARE: implement the concise public '
                                                                  'programme protocol and its supported '
                                                                  'preparation route before claiming '
                                                                  'researcher workflow acceptance.',
                                       guide='programmes/energy/battery-charging/workflows/battery-initial-window-observation/guide.md',
                                       verification_owners=('tests/test_battery_observation_graph.py',
                                                            'tests/test_battery_segmented_observation.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟠 Concise programme software remains unavailable',
                     descriptor_version='1.0.0',
                     operations_available=False,
                     catalogue_order=47),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='battery-initial-window-observation',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.battery.battery_observation_inquiry',
                                 adapter_version='1.0.0',
                                 controller_environment='battery-recursion',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('SOFTWARE: implement the concise public programme '
                                                       'protocol and its supported preparation route before '
                                                       'claiming researcher workflow acceptance.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
