# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='recursive-inquiry',
                                       title='Investigate prerequisites and reuse assessed contributions',
                                       kind='bounded human-authored scientific programme',
                                       substrates=('registered numerical sources',
                                                   'one-cell RC',
                                                   'PyBaMM SPMe battery'),
                                       methods=('explicit requirement connections',
                                                'registered assessments',
                                                'exact-version contribution reuse'),
                                       environment='locked base; battery-recursion for PyBaMM acquisition',
                                       operations=(WorkflowOperation(command='campaign recursive-explain',
                                                                     boundary='partial design and '
                                                                              'selected-wave explanation; no '
                                                                              'contact',
                                                                     inputs=('programmes/materials/superconductivity/workflows/recursive-materials/materials-partial.json',)),
                                                   WorkflowOperation(command='campaign recursive-author',
                                                                     boundary='frozen closed wave and '
                                                                              'source/plan correspondence',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2.json',
                                                                             'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3.json',
                                                                             'programmes/energy/battery-charging/workflows/recursive-battery/battery-wave-a.json',
                                                                             'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json')),
                                                   WorkflowOperation(command='campaign check-readiness',
                                                                     boundary='no-contact prospective '
                                                                              'handoff proof',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'recursive-development-run',
                                                                     boundary='shared scheduler, registered '
                                                                              'numerical tasks and custody',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'recursive-development-result',
                                                                     boundary='authenticated complete '
                                                                              'results; no acquisition',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'recursive-contribution',
                                                                     boundary='inspect or export exact '
                                                                              'scientific content for a '
                                                                              'later wave',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original.json',
                                                             role='editable general authoring form of '
                                                                  'unchanged RC design',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2.json',
                                                             role='editable general authoring form of '
                                                                  'separately frozen expanded-menu design',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3.json',
                                                             role='editable general authoring form of '
                                                                  'separately frozen expanded-deadline '
                                                                  'design',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original-scientific.json',
                                                             role='exact original RC scientific operands for '
                                                                  'comparison',
                                                             schema_id='empirical-lawhood/methods/rc-prerequisite-chain/config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2-scientific.json',
                                                             role='exact separately frozen expanded-menu '
                                                                  'scientific operands',
                                                             schema_id='empirical-lawhood/methods/rc-prerequisite-chain/config'),
                                               WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3-scientific.json',
                                                             role='exact separately frozen expanded-deadline '
                                                                  'scientific operands',
                                                             schema_id='empirical-lawhood/methods/rc-prerequisite-chain/config'),
                                               WorkflowInput(path='programmes/energy/battery-charging/workflows/recursive-battery/battery-wave-a.json',
                                                             role='editable exposed supplier investigation',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/materials/superconductivity/workflows/recursive-materials/materials-partial.json',
                                                             role='partial physical programme with '
                                                                  'unresolved leaves',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft'),
                                               WorkflowInput(path='programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json',
                                                             role='disclosed conditional Rubisco kinetic '
                                                                  'roster with partial and rejected members; '
                                                                  'zero fresh biological units',
                                                             schema_id='empirical-lawhood/planning/recursive-study-draft')),
                                       input_availability='Bounded RC and battery development designs are '
                                                          'supplied. Later-wave bindings select actual prior '
                                                          'contribution identities; physical materials '
                                                          'requirements remain unresolved.',
                                       scientific_ceiling='Development findings, software conformance and '
                                                          'prospective qualification have distinct '
                                                          'contracts. Exposed native results remain '
                                                          'non-promotable; an imported manifest grants no '
                                                          'authority.',
                                       first_missing_prerequisite='Explain the draft, select a closed wave '
                                                                  'and explicit guarded storage. PyBaMM '
                                                                  'execution requires its locked '
                                                                  'battery-recursion profile; prospective '
                                                                  'work requires its own eligible source and '
                                                                  'authority.',
                                       guide='docs/using/recursive-inquiry.md',
                                       verification_owners=('tests/runtime_platform/test_recursive_compiler.py',
                                                            'tests/test_recursive_public_service.py',
                                                            'tests/test_recursive_contribution_custody.py',
                                                            'tests/test_recursive_rc_operations.py',
                                                            'tests/test_battery_recursive_construction.py'),
                                       output_retention='Exact draft, plans, commitments, effects, '
                                                        'assessments and scientific terminals bind primary '
                                                        'receipts. Completed recovery and result reading '
                                                        'acquire no observations.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Exposed development; 🟠 Unresolved physical premises',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=10),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='recursive-inquiry',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.api.domain_composition.shared_inquiry',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Explain the draft, select a closed wave and explicit '
                                                       'guarded storage. PyBaMM execution requires its '
                                                       'locked battery-recursion profile; prospective work '
                                                       'requires its own eligible source and authority.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='recursive-inquiry',
                                 profile_id='battery',
                                 adapter_module='empirical_lawhood.api.domain_composition.shared_inquiry',
                                 adapter_version='1.0.0',
                                 controller_environment='battery-recursion',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Explain the draft, select a closed wave and explicit '
                                                       'guarded storage. PyBaMM execution requires its '
                                                       'locked battery-recursion profile; prospective work '
                                                       'requires its own eligible source and authority.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
