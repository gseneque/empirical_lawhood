# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='response-method-reference',
                                       title='Physical scale-morphism reference',
                                       kind='truth-known method reference',
                                       substrates=('generated circuit reference worlds',),
                                       methods=('scale-morphism conformance',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'scale-morphism-reference-check',
                                                                     boundary='reference',
                                                                     inputs=('programmes/foundations/measurement-and-response/workflows/response-method-reference/config.json',)),),
                                       inputs=(WorkflowInput(path='programmes/foundations/measurement-and-response/workflows/response-method-reference/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/reference-worlds/physical-scale-morphism/physical-scale-morphism-truth-suite-config'),),
                                       input_availability='Public generated reference suite; no physical '
                                                          'records required.',
                                       scientific_ceiling='Thirty cases across fifteen fixtures with two '
                                                          'nested variants.',
                                       first_missing_prerequisite='No physical source, independent physical '
                                                                  'evidence or issued campaign.',
                                       guide='programmes/foundations/measurement-and-response/workflows/response-method-reference/guide.md',
                                       verification_owners=('tests/test_circuit_truth_known_development_input.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟡 Development check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=40),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='scale-morphism-reference',
                          schema_id='empirical-lawhood/reference-worlds/physical-scale-morphism/physical-scale-morphism-truth-suite-config',
                          record_module='empirical_lawhood.domains.reference_worlds.physical_scale_morphism.contracts',
                          record_name='PhysicalScaleMorphismTruthSuiteConfig',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign scale-morphism-reference-check',
                          owner='PhysicalScaleMorphismTruthSuiteConfig',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/response-method-reference/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='response-method-reference',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.reference_worlds.physical_scale_morphism',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('No physical source, independent physical evidence or '
                                                       'issued campaign.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
