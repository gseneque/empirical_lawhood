# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='material-control-inputs',
                                       title='Material-control workflow inputs',
                                       kind='raw wrapping / input preflight',
                                       substrates=('five material control structures',),
                                       methods=('bounded solver-output inspection',),
                                       environment='locked base plus declared HDF5 tooling',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'material-workflow-wrap-raw',
                                                                     boundary='raw wrapping',
                                                                     inputs=('programmes/materials/superconductivity/workflows/material-control-inputs/control-inputs.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'material-workflow-input-check',
                                                                     boundary='held input preflight',
                                                                     inputs=('programmes/materials/superconductivity/workflows/material-control-inputs/control-inputs.json',))),
                                       inputs=(WorkflowInput(path='programmes/materials/superconductivity/workflows/material-control-inputs/control-inputs.json',
                                                             role='raw workflow manifest',
                                                             schema_id='empirical-lawhood/simulators/ambient-pressure-superconductor/material-control-input-preflight'),),
                                       input_availability='Control manifest shipped; ten authentic raw '
                                                          'solver-output envelopes must be supplied.',
                                       scientific_ceiling='Five structures and ten nested views; no solver '
                                                          'execution or physical validity certification.',
                                       first_missing_prerequisite='All raw members, exact profiles and '
                                                                  'custody remain researcher supplied.',
                                       guide='programmes/materials/superconductivity/workflows/material-control-inputs/guide.md',
                                       verification_owners=('tests/test_material_epw_coupling.py',
                                                            'tests/test_material_control_input_preflight.py',
                                                            'tests/test_material_mgb2_authentic_reference.py'),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🟠 Input check',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=38),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='material-control-input',
                          schema_id='empirical-lawhood/simulators/ambient-pressure-superconductor/material-control-input-preflight',
                          record_module='empirical_lawhood.adapters.simulators.ambient_pressure_superconductor.material_control_input_preflight',
                          record_name='MaterialControlInputPreflight',
                          disposition='editable',
                          maximum_bytes=32768,
                          requires_canonical=False,
                          command='campaign material-workflow-input-check',
                          owner='MaterialControlInputPreflight',
                          supplied_inputs=('programmes/materials/superconductivity/workflows/material-control-inputs/control-inputs.json',)),
 ConfigurationDeclaration(consumer='lattice-method-authoring',
                          schema_id='empirical-lawhood/simulators/ambient-pressure-superconductor/synthetic-material-response-method-config',
                          record_module='empirical_lawhood.domains.materials.synthetic_material_method.contracts',
                          record_name='SyntheticMaterialResponseMethodConfig',
                          disposition='editable',
                          maximum_bytes=131072,
                          requires_canonical=True,
                          command='campaign synthetic-material-author',
                          owner='SyntheticMaterialResponseMethodConfig',
                          supplied_inputs=('programmes/materials/superconductivity/workflows/lattice-pairing-method/authoring.json',)))

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='material-control-inputs',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.adapters.simulators.ambient_pressure_superconductor',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('All raw members, exact profiles and custody remain '
                                                       'researcher supplied.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
