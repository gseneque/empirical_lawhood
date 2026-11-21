# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='electron-gas-response',
                                       title='Uniform electron-gas reference',
                                       kind='reference / candidate authoring',
                                       substrates=('analytic uniform electron gas',),
                                       methods=('finite-q transverse response',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'electron-gas-reference-check',
                                                                     boundary='reference',
                                                                     inputs=('programmes/materials/superconductivity/workflows/electron-gas-response/config.json',)),
                                                   WorkflowOperation(command='campaign electron-gas-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/materials/superconductivity/workflows/electron-gas-response/config.json',)),
                                                   WorkflowOperation(command='campaign check-readiness',
                                                                     boundary='no-contact proof',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/materials/superconductivity/workflows/electron-gas-response/config.json',
                                                             role='native development or import config',
                                                             schema_id='empirical-lawhood/simulators/uniform-electron-gas-response/analytic-reference-config'),),
                                       input_availability='Public analytic reference config; no qualified '
                                                          'physical material source.',
                                       scientific_ceiling='Synthetic analytic reference and candidate; no '
                                                          'physical independent unit.',
                                       first_missing_prerequisite='Physical material inputs and '
                                                                  'qualification are separate.',
                                       guide='programmes/materials/superconductivity/workflows/electron-gas-response/guide.md',
                                       verification_owners=('tests/test_uniform_electron_gas_native_science.py',
                                                            'tests/test_uniform_electron_gas_candidate.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Development authoring; 🟡 Reference check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=29),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='electron-gas-reference',
                          schema_id='empirical-lawhood/simulators/uniform-electron-gas-response/analytic-reference-config',
                          record_module='empirical_lawhood.domains.materials.electron_gas.native_quickstart',
                          record_name='UniformElectronGasAnalyticReferenceConfig',
                          disposition='editable',
                          maximum_bytes=32768,
                          requires_canonical=True,
                          command='campaign electron-gas-reference-check',
                          owner='UniformElectronGasAnalyticReferenceConfig',
                          supplied_inputs=('programmes/materials/superconductivity/workflows/electron-gas-response/config.json',)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='electron-gas-response',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.uniform_electron_gas_response',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Physical material inputs and qualification are '
                                                       'separate.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
