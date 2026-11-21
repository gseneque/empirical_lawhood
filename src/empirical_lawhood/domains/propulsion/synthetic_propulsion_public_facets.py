# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='propulsion-reliability-reference',
                                       title='Propulsion reliability reference',
                                       kind='truth-known method reference',
                                       substrates=('generated propulsion worlds',),
                                       methods=('closure/reliability reference',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'propulsion-reference-check',
                                                                     boundary='reference',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/propulsion-reliability-reference/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/propulsion-reliability-reference/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/methods/synthetic-propulsion-development-input'),),
                                       input_availability='Public synthetic truth-known preparations.',
                                       scientific_ceiling='Reference worlds and nested decisions; no '
                                                          'physical propulsion evidence.',
                                       first_missing_prerequisite='Physical preparation, custody and '
                                                                  'prospective qualification are not '
                                                                  'supplied.',
                                       guide='programmes/foundations/measurement-and-response/workflows/propulsion-reliability-reference/guide.md',
                                       verification_owners=('tests/test_synthetic_propulsion_development_input.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=41),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='propulsion-reliability-reference',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.methods.synthetic_propulsion',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Physical preparation, custody and prospective '
                                                       'qualification are not supplied.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
