# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='lattice-pairing-method',
                                       title='Synthetic lattice pairing method',
                                       kind='method candidate authoring',
                                       substrates=('synthetic lattice inputs',),
                                       methods=('disclosed pairing evaluator',),
                                       environment='locked base',
                                       operations=(WorkflowOperation(command='campaign '
                                                                             'synthetic-material-author',
                                                                     boundary='candidate authoring',
                                                                     inputs=('programmes/materials/superconductivity/workflows/lattice-pairing-method/authoring.json',)),
                                                   WorkflowOperation(command='campaign check-readiness',
                                                                     boundary='no-contact proof',
                                                                     inputs=())),
                                       inputs=(WorkflowInput(path='programmes/materials/superconductivity/workflows/lattice-pairing-method/authoring.json',
                                                             role='authoring selector',
                                                             schema_id='empirical-lawhood/simulators/ambient-pressure-superconductor/synthetic-material-response-method-config'),),
                                       input_availability='Synthetic method config supplied; physical '
                                                          'Hamiltonian/position/pairing records are '
                                                          'separate.',
                                       scientific_ceiling='Synthetic producer/evaluator conformance; no '
                                                          'superconducting material result.',
                                       first_missing_prerequisite='Authentic material records and source '
                                                                  'qualification remain missing.',
                                       guide='programmes/materials/superconductivity/workflows/lattice-pairing-method/guide.md',
                                       verification_owners=('tests/test_synthetic_material_response_method.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Development authoring',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=30),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='lattice-pairing-method',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.materials.synthetic_material_method',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Authentic material records and source qualification '
                                                       'remain missing.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
