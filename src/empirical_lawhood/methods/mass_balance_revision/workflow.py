# SPDX-License-Identifier: MPL-2.0
"""Public record-upgrade route with original custody and explicit evidence limits."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowOperation

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(Workflow(
    workflow_id='mass-balance-record-upgrade', title='Explicit retained mass-forecast record upgrade',
    kind='bounded retained record conversion', substrates=('retained exposed mass forecasts',),
    methods=('exact kg-to-g representation conversion', 'independent rational unit check'), environment='base',
    operations=tuple(WorkflowOperation('campaign experiment-' + name, boundary, ()) for name, boundary in (
        ('explain', 'describe the exact retained source and explicit supported conversion'),
        ('prepare', 'validate the original source census and selected operational prerequisites'),
        ('author', 'freeze a separate derivative operation with original custody'),
        ('run', 'publish a version-2 gram representation with its original kg evidence'),
        ('read', 'read the exact retained version and original adverse or missing findings'),
        ('recover', 'reuse original completion receipts without another conversion'))),
    inputs=(), input_availability='Use the documented helper to authenticate and copy the original retained source.',
    scientific_ceiling='Exposed derivative representation only; no new observation, freshness or scientific qualification.',
    first_missing_prerequisite='Select the complete retained version-1 run, current access profile and explicit derivative destinations.',
    guide='docs/development/record-revisions.md', verification_owners=('tests/test_mass_forecast_revision.py',)),
    '🟡 Explicit retained derivative; both original and converted record revisions remain readable', catalogue_order=50),)
