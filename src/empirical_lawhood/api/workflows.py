"""Closed public workflow facts. Discovery neither opens inputs nor builds providers.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from empirical_lawhood.execution.workflow_descriptors import (
    RetainedManifestInput as RetainedManifestInput,
    Workflow as Workflow,
    WorkflowInput as WorkflowInput,
    WorkflowOperation as WorkflowOperation,
)
from empirical_lawhood.adapters.composition.generated_workflows import WORKFLOW_DECLARATIONS




WORKFLOWS = tuple(row.workflow for row in WORKFLOW_DECLARATIONS)
if len({row.workflow_id for row in WORKFLOWS}) != len(WORKFLOWS):
    raise ValueError("workflow declarations have duplicate legacy or adapter owners")


def list_workflows() -> tuple[Workflow, ...]:
    """Return the closed task inventory; inspect no environment or source input."""
    return WORKFLOWS


def show_workflow(workflow_id: str) -> Workflow:
    """Look up an exact public identifier, never an import path or expression."""
    for workflow in WORKFLOWS:
        if workflow.workflow_id == workflow_id:
            return workflow
    raise ValueError(f"Unknown workflow: {workflow_id}. Use workflow list.")


def installation_profiles(workflow_id: str) -> tuple[dict, ...]:
    """List software selections without loading manifests or inspecting an environment."""
    from empirical_lawhood.adapters.composition.generated_public_facets import WORKFLOW_INSTALLATIONS

    show_workflow(workflow_id)
    return tuple({"profile_id": row.profile_id, "controller_environment": row.controller_environment,
        "workers": tuple({"role_id": worker.role_id, "environment_id": worker.environment_id,
                          "selection": worker.selection} for worker in row.workers)}
        for row in WORKFLOW_INSTALLATIONS if row.workflow_id == workflow_id)
