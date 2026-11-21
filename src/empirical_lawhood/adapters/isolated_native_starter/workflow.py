# SPDX-License-Identifier: MPL-2.0
"""Adapter-owned inert discovery facts for the editable isolated starter."""

from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowOperation

WORKFLOW_DECLARATIONS = (WorkflowDeclaration(Workflow(
    workflow_id="isolated-native-starter", title="Editable isolated native development starter",
    kind="bounded exposed isolated calculation", substrates=("exposed finite integer sequence",),
    methods=("NumPy sum of squares", "independent integer formula"), environment="base and selected isolated worker",
    operations=tuple(WorkflowOperation("campaign experiment-" + name, boundary, ()) for name, boundary in (
        ("prepare", "resolve exact original inputs and operational selections"),
        ("author", "derive the complete exposed native design"),
        ("run", "execute one bounded calculation in the selected interpreter"),
        ("read", "present the original authenticated result and its independent comparison"),
        ("recover", "reuse completed bytes and refuse uncertain native contact"))),
    inputs=(), input_availability="Prepare explicit exposed integer, source, worker and external scratch selections with the input helper.",
    scientific_ceiling="Exposed Linux software acceptance only; no fresh physical observation or scientific qualification.",
    first_missing_prerequisite="Select the locked controller and worker, source, operator profile and new external input, artifact and scratch paths.",
    guide="docs/development/isolated-native-starter.md", verification_owners=("tests/test_isolated_native_starter.py",)),
    "🟡 Exposed Linux starter; selected interpreter, independent formula and original recovery boundaries"),)
