# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-geometry',
                                       title='Six-matrix geometry scan',
                                       kind='fresh explicit native development scan',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Six-matrix geometry scan',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'matrix-geometry-prepare',
                                                                     boundary='explicit complete numerical '
                                                                              'allocation',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign matrix-geometry-prove',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-geometry-qualification',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-geometry-bind-qualification',
                                                                     boundary='exact numerical prerequisite '
                                                                              'binding',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-geometry-conformance',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),
                                                   WorkflowOperation(command='campaign matrix-geometry-run',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'matrix-geometry-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',
                                                             role='editable complete '
                                                                  'source/allocation/resource declaration',
                                                             schema_id='empirical-lawhood/matrix-geometry/scan-input'),),
                                       input_availability='Complete source-preserving baseline and exposed '
                                                          'explicit allocation supplied; actual cells are '
                                                          'acquired separately.',
                                       scientific_ceiling='Development scan and numerical prerequisites; '
                                                          'negative selection is a valid terminal; no issued '
                                                          'grant.',
                                       first_missing_prerequisite='Select guarded storage, actual '
                                                                  'source/lock and sufficient declared '
                                                                  'resources before native cells.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-geometry/guide.md',
                                       verification_owners=('tests/test_matrix_geometry_integration.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current operation',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=12),
 WorkflowDeclaration(workflow=Workflow(workflow_id='selected-events',
                                       title='Selected conditional events',
                                       kind='authenticated nominated or alternate parent and new conditional '
                                            'branches',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('Selected conditional events',),
                                       environment='base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'selected-parent-reconstruct',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'selected-parent-alternate',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'selected-events-prepare',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign selected-events-prove',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'selected-events-conformance',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign selected-events-run',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'selected-events-result',
                                                                     boundary='explicit current input/result '
                                                                              'contract',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',
                                                             role='editable fixed nominated-parent '
                                                                  'reconstruction request',
                                                             schema_id='empirical-lawhood/selected-events/parent-request'),),
                                       input_availability='Nominated reconstruction request supplied; event '
                                                          'input is prepared from its authenticated parent '
                                                          'and a complete current null-reference scan.',
                                       scientific_ceiling='Development conditional experiment; checkpoint '
                                                          'futures are nested under one parent, not '
                                                          'independent parents.',
                                       first_missing_prerequisite='Reconstruct nominated parent, or select '
                                                                  'an explicit current alternate; acquire a '
                                                                  'complete P03 null reference with no '
                                                                  'recurrence-success gate.',
                                       guide='programmes/foundations/emergent-structure/workflows/selected-events/guide.md',
                                       verification_owners=('tests/test_matrix_geometry_integration.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟢 Current operation',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=13))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-geometry',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_response_study',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select guarded storage, actual source/lock and '
                                                       'sufficient declared resources before native cells.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),
 WorkflowInstallationDeclaration(workflow_id='selected-events',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_response_study',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Reconstruct nominated parent, or select an explicit '
                                                       'current alternate; acquire a complete P03 null '
                                                       'reference with no recurrence-success gate.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'))
