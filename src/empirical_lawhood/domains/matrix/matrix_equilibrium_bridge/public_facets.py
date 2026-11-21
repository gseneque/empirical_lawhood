# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-paired-equilibrium-bridge',
                                       title='SCI02-D paired equilibrium estimator bridge',
                                       kind='finite new numerical development and confirmation experiment',
                                       substrates=('complete six-matrix Hamiltonians',),
                                       methods=('canonical zero-mean controls',
                                                'frozen signed-integral covariance fit',
                                                'independent sampling and cost assessment'),
                                       environment='existing locked main environment; four workers and one '
                                                   'numerical thread each',
                                       operations=(WorkflowOperation(command='campaign experiment-prepare',
                                                                     boundary='derive the complete new '
                                                                              'allocation and frozen tranche',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='freeze exact native source '
                                                                              'and scientific ports',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='acquire original bundles and '
                                                                              'independently assess retained '
                                                                              'forces',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='authenticate all findings and '
                                                                              'original native receipts',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='reuse completed receipts '
                                                                              'without native replay',
                                                                     inputs=())),
                                       inputs=(),
                                       input_availability='Use the public new-allocation constructor and '
                                                          'authenticated frozen-fit continuation.',
                                       scientific_ceiling='Finite Matrix estimator evidence; canonical mean '
                                                          'identity does not establish equilibrium coverage '
                                                          'or molecular qualification.',
                                       first_missing_prerequisite='Frozen protocol, installed source, actual '
                                                                  'campaign, operator profile and explicit '
                                                                  'input/artifact destinations.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-equilibrium-bridge/guide.md',
                                       verification_owners=('tests/test_matrix_sci02d_kernels.py',
                                                            'tests/test_matrix_sci02d_workflow.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Frozen finite estimator experiment; 🟠 Equilibrium accuracy, practical '
                                   'saving and molecular supply require separate findings',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=0),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-paired-equilibrium-bridge',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_equilibrium_bridge',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Frozen protocol, installed source, actual campaign, '
                                                       'operator profile and explicit input/artifact '
                                                       'destinations.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
