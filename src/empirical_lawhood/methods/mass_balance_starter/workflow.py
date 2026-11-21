# SPDX-License-Identifier: MPL-2.0
"""Adapter-owned public facts for the small editable exposed starter."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowOperation

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(Workflow(
    workflow_id="mass-balance-starter", title="Editable mass-balance development starter",
    kind="small pure exposed development experiment", substrates=("supplied typed mass observations",),
    methods=("initial-plus-added forecast", "independent final-observation falsifier"), environment="base",
    operations=tuple(WorkflowOperation("campaign experiment-" + name, boundary, ()) for name, boundary in (
        ("explain", "describe selected exposed inputs and complete independent-unit census"),
        ("prepare", "resolve exact inputs and operational prerequisites without execution"),
        ("author", "freeze the original two-operation design and scientific consumer"),
        ("run", "calculate the forecast and compare independent supplied observations"),
        ("read", "present actual retained findings without recalculation or providers"),
        ("recover", "reuse completed receipts through the ordinary recovery owner"))),
    inputs=(), input_availability="Copy the exposed examples, or select your own typed exposed evidence, with the documented input helper.",
    scientific_ceiling="Exposed arithmetic development only; neither fresh confirmation nor physical mass-balance qualification.",
    first_missing_prerequisite="Select canonical evidence, tolerance in kg, locked source, operator profile and explicit external destinations.",
    guide="docs/development/mass-balance-starter.md", verification_owners=("tests/test_mass_balance_starter.py",)),
    "🟡 Exposed editable development; independent falsifier retains adverse and missing observations",
    catalogue_order=48),)
