# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation  # noqa: F401
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(workflow=Workflow(workflow_id='matrix-programme',
                                       title='Matrix E1–E6 researcher programme',
                                       kind='C-backed result frontier over ordinary installed experiment '
                                            'services',
                                       substrates=('six-matrix stochastic response',),
                                       methods=('independent E1/E2', 'native TRAIN and E3-E6'),
                                       environment='existing locked main environment; selected four workers '
                                                   'and one numerical thread each',
                                       operations=(WorkflowOperation(command='campaign experiment-explain',
                                                                     boundary='original C and explicit '
                                                                              'operational prerequisites; no '
                                                                              'contact',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json',)),
                                                   WorkflowOperation(command='campaign experiment-prepare',
                                                                     boundary='retain the selected '
                                                                              'preparation report; no issue '
                                                                              'or acquisition',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json',)),
                                                   WorkflowOperation(command='campaign '
                                                                             'experiment-derive-inputs',
                                                                     boundary='derive eligible inputs, '
                                                                              'source continuations or CAL '
                                                                              'closeout while retaining '
                                                                              'original completed work and '
                                                                              'unknown contacts',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-programme/retained-training-continuation.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-programme/retained-e3-continuation.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-programme/e3-cal-closeout.example.json')),
                                                   WorkflowOperation(command='campaign experiment-author',
                                                                     boundary='retain one original C-pinned '
                                                                              'programme',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-run',
                                                                     boundary='advance eligible ordinary '
                                                                              'children through current '
                                                                              'authority checks; return '
                                                                              'operational progress with '
                                                                              'full scientific reads '
                                                                              'deferred where unnecessary',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-read',
                                                                     boundary='reopen actual ordinary child '
                                                                              'receipts and preserve adverse '
                                                                              'outcomes',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign experiment-recover',
                                                                     boundary='delegate receipt reuse and '
                                                                              'original source/contact '
                                                                              'refusal',
                                                                     inputs=()),
                                                   WorkflowOperation(command='campaign '
                                                                             'experiment-export-products',
                                                                     boundary='retain every phase readout '
                                                                              'and original product '
                                                                              'references, with an '
                                                                              'explicitly selected portable '
                                                                              'byte copy; no reacquisition',
                                                                     inputs=('programmes/foundations/emergent-structure/workflows/matrix-programme/product-export.example.json',
                                                                             'programmes/foundations/emergent-structure/workflows/matrix-programme/portable-product-export.example.json'))),
                                       inputs=(WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json',
                                                             role='current C publication, one programme home '
                                                                  'and explicit operational settings; '
                                                                  'exposed unwritten example handles require '
                                                                  'replacement',
                                                             schema_id='empirical-lawhood/matrix-programme/specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/scientific-design.example.json',
                                                             role='complete E1-E6 scientific design D; '
                                                                  'exposed streams and unwritten templates '
                                                                  'require genuine inputs before commitment',
                                                             schema_id='empirical-lawhood/matrix-programme/scientific-design'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/sources.example.json',
                                                             role='empty outer selector for the current '
                                                                  'C-pinned programme',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/product-export.example.json',
                                                             role='original programme identity and selected '
                                                                  'product-reference delivery directory; '
                                                                  'replace the unwritten example identity',
                                                             schema_id='empirical-lawhood/matrix-programme/product-export-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/portable-product-export.example.json',
                                                             role='original programme identity, disjoint '
                                                                  'mounted replica root and explicit copy '
                                                                  'bounds; replace all unwritten selections',
                                                             schema_id='empirical-lawhood/matrix-programme/portable-product-export-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.example.json',
                                                             role='completed original E1/E2 programme '
                                                                  'publication and a separate continuation '
                                                                  'home before any TRAIN execution; replace '
                                                                  'the unwritten original handle',
                                                             schema_id='empirical-lawhood/matrix-programme/source-continuation-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.sources.example.json',
                                                             role='empty selector for original-custody '
                                                                  'source continuation',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/retained-training-continuation.example.json',
                                                             role='complete original E1/E2/TRAIN programme '
                                                                  'publication and disjoint continued home '
                                                                  'before any later child authoring; replace '
                                                                  'the unwritten handle',
                                                             schema_id='empirical-lawhood/matrix-programme/retained-training-continuation-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/retained-training-continuation.sources.example.json',
                                                             role='empty selector for completed-TRAIN source '
                                                                  'continuation',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/retained-e3-continuation.example.json',
                                                             role='original retained-TRAIN programme with '
                                                                  'closed partial E3 before future response '
                                                                  'entry, original reveal and distinct '
                                                                  'target home/run; replace the unwritten '
                                                                  'handle',
                                                             schema_id='empirical-lawhood/matrix-programme/retained-e3-continuation-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/retained-e3-continuation.sources.example.json',
                                                             role='empty selector for entered-E3 source '
                                                                  'continuation',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e3-cal-closeout.example.json',
                                                             role='original entered CAL and untouched CONF, '
                                                                  'original reveal and separate target '
                                                                  'directory/run; replace the unwritten '
                                                                  'handle',
                                                             schema_id='empirical-lawhood/matrix-programme/e3-cal-closeout-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e3-cal-closeout.sources.example.json',
                                                             role='empty selector for authenticated CAL '
                                                                  'closeout',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.example.json',
                                                             role='prospective E1 allocation and criterion '
                                                                  'binding before D; select actual '
                                                                  'scientific inputs',
                                                             schema_id='empirical-lawhood/matrix-programme/e1-allocation-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.request.example.json',
                                                             role='E1 coordinates, criterion choices and '
                                                                  'explicit stream material before D',
                                                             schema_id='empirical-lawhood/matrix-programme/e1-allocation-request'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.census.example.json',
                                                             role='disclosed exposure and exclusion facts; '
                                                                  'select the settled census before fresh '
                                                                  'allocation',
                                                             schema_id='empirical-lawhood/matrix-factor-response/exposure-census'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.sources.example.json',
                                                             role='copied E1 request and exposure-census '
                                                                  'file bindings',
                                                             schema_id='empirical-lawhood/experiment-inputs/file-selection'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/compact-specification.json',
                                                             role='compact E1 full-history selector; genuine '
                                                                  'inputs remain required',
                                                             schema_id='empirical-lawhood/matrix-factor-confirmation/compact-experiment-specification'),
                                               WorkflowInput(path='programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/specification.json',
                                                             role='E1 selector; actual four-family inputs '
                                                                  'remain required',
                                                             schema_id='empirical-lawhood/matrix-factor-confirmation/experiment-specification')),
                                       input_availability='Exposed copied scaffolding supplied; select the '
                                                          'actual C and operational settings, then genuine '
                                                          'later entry and issued authority operands.',
                                       scientific_ceiling='Composition, schema acceptance and development '
                                                          'completion create no qualification, issue or '
                                                          'outcome authority.',
                                       first_missing_prerequisite='Bind the actual prospective E1 allocation '
                                                                  'in D, publish whole C, and select current '
                                                                  'operational settings before programme '
                                                                  'authoring.',
                                       guide='programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md',
                                       verification_owners=('tests/test_matrix_researcher_programme.py',),
                                       output_retention="See each command's current effects and guide for "
                                                        'explicit development export or closed authoring '
                                                        'outputs. Discovery writes nothing.',
                                       resources='Guide and input paths belong to the selected source '
                                                 'checkout/distribution, not the installed wheel. No current '
                                                 'directory is assumed.'),
                     display_state='🔵 Finite installed composition; 🟠 Full scientific acceptance pending',
                     descriptor_version='1.0.0',
                     operations_available=True,
                     catalogue_order=5),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='matrix-programme',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.domains.matrix.matrix_researcher_programme',
                                 adapter_version='1.0.0',
                                 controller_environment='base',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Bind the actual prospective E1 allocation in D, '
                                                       'publish whole C, and select current operational '
                                                       'settings before programme authoring.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
