# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='laser-archive-inspection',
                                       title='Laser archive inspection',
                                       kind='retrospective import / preview',
                                       substrates=('published laser burst archive',),
                                       methods=('bounded logged-burst inspection',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign glenn-import-check',
                                                                     boundary='retrospective import',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/laser-archive-inspection/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/laser-archive-inspection/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/physical/glenn/glenn-input-quickstart'),),
                                       input_availability='Public pinned selection; full import requires the '
                                                          'declared archive and burst table.',
                                       scientific_ceiling='Retrospective local inspection; no target guarded '
                                                          'publication.',
                                       first_missing_prerequisite='Preview does not supply archive bytes or '
                                                                  'prospective qualification.',
                                       guide='programmes/foundations/measurement-and-response/workflows/laser-archive-inspection/guide.md',
                                       verification_owners=('tests/test_glenn_authentic_source.py',
                                                            'tests/test_glenn_quickstart.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟠 Retrospective import / inspection',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=39),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='glenn-import-selection',
                          schema_id='empirical-lawhood/physical/glenn/glenn-input-quickstart',
                          record_module='empirical_lawhood.adapters.physical.glenn.quickstart',
                          record_name='GlennInputQuickstart',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign glenn-import-check',
                          owner='GlennInputQuickstart',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/laser-archive-inspection/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='laser-archive-inspection',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.physical.glenn',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Preview does not supply archive bytes or prospective '
                                                       'qualification.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
