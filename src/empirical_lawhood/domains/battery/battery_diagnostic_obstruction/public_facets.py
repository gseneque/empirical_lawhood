# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='battery-obstruction-reassessment',
                                       title='Reassess retained battery obstruction history',
                                       kind='retained negative-history PURE reassessment',
                                       substrates=('retained PyBaMM obstruction custody',),
                                       methods=('independent obstruction assessment',
                                                'negative MODEL contribution reuse'),
                                       environment='existing locked main numerical environment; no native '
                                                   'trajectory',
                                       operations=(WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='derive declared census and '
                                                                              'explicit dependencies; no '
                                                                              'native contact',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-prepare',
                                                                     boundary='retain selected preparation '
                                                                              'report; no authority',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='derive immutable components '
                                                                              'and original input bindings',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='execute eligible declared '
                                                                              'components through existing '
                                                                              'services',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate complete '
                                                                              'findings or explicit partial '
                                                                              'custody',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='reuse original receipts and '
                                                                              'refuse uncertain contact',
                                                                     inputs=())),
                                       inputs=(),
                                       input_availability='Select the exact original obstruction source, '
                                                          'portable negative contribution and explicit '
                                                          'original custody selection.',
                                       scientific_ceiling='Retains UNKNOWN and acquisition HOLD; history '
                                                          'reassessment grants no numerical adequacy or '
                                                          'physical qualification.',
                                       first_missing_prerequisite='Authenticate original report/cost/member '
                                                                  'census and continued absence of '
                                                                  'diagnostic completion; select guarded '
                                                                  'output.',
                                       guide='programmes/energy/battery-charging/workflows/battery-obstruction-reassessment/guide.md',
                                       verification_owners=('tests/test_battery_obstruction_experiment.py',
                                                            'tests/test_battery_diagnostic_obstruction.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Declared researcher route; 🟠 Current workflow acceptance required',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=46),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='battery-obstruction-reassessment',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.battery.battery_diagnostic_obstruction',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Authenticate original report/cost/member census and '
                                                       'continued absence of diagnostic completion; select '
                                                       'guarded output.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
