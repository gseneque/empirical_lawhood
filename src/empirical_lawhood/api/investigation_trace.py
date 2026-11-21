# SPDX-License-Identifier: MPL-2.0
"""Trace authored scientific choices to generated operations without execution."""
from __future__ import annotations

from functools import partial

from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.science import ObjectIdentity


def authored_operation_trace(draft: RecursiveStudyDraft, *, specification: ObjectIdentity | None = None,
                             operation_ids: tuple[str, ...] | None = None) -> tuple[dict, ...]:
    """Return the complete authored-operation census and installed implementation.

    Unselected operations remain visible. A changed or unavailable implementation
    is labelled explicitly; the function never substitutes the current source for
    an original producer. It reads static installed declarations only.
    """
    if type(draft) is not RecursiveStudyDraft:
        raise TypeError("operation tracing requires its original recursive draft")
    operations = draft.operations
    if operation_ids is not None:
        if (type(operation_ids) is not tuple or any(type(value) is not str for value in operation_ids)
                or len(set(operation_ids)) != len(operation_ids)
                or not set(operation_ids) <= {operation.node_id for operation in operations}):
            raise ValueError("operation trace selection must name unique authored operations")
        selected_ids = frozenset(operation_ids)
        operations = tuple(operation for operation in operations if operation.node_id in selected_ids)
    from .recursive_operations import selected_operation_factories
    from .recursive_operation_index import UnknownOperationSelection

    selections = tuple(sorted({operation.selection.selection_id for operation in operations}))
    try:
        factories = selected_operation_factories(selections)
    except UnknownOperationSelection:
        # Historical/uninstalled selections remain inspectable without guessing.
        found = []
        for selection in selections:
            try:
                found.extend(selected_operation_factories((selection,)))
            except UnknownOperationSelection:
                pass
        factories = tuple(found)
    by_selection = {factory.registration.selection.selection_id: factory for factory in factories}
    links = {}
    for edge in draft.links:
        links.setdefault(edge.consumer_node_id, []).append(edge)
    selected = frozenset(draft.selected_operation_ids)
    rows = []
    for operation in operations:
        implementation = {
            "capability_key": operation.selection.capability_key,
            "capability_version": operation.selection.capability_version,
            "implementation_sha256": operation.selection.implementation_sha256,
            "status": "UNAVAILABLE_IN_SELECTED_INSTALLATION",
            "module": None, "callable": None,
        }
        factory = by_selection.get(operation.selection.selection_id)
        if factory is not None:
            if factory.registration.selection == operation.selection:
                runner = factory.runner_factory
                while isinstance(runner, partial):
                    runner = runner.func
                implementation.update(status="EXACT_INSTALLED_DECLARATION",
                    module=getattr(runner, "__module__", type(runner).__module__),
                    callable=getattr(runner, "__qualname__", type(runner).__qualname__))
            else:
                implementation["status"] = "INSTALLED_IMPLEMENTATION_DIFFERS"
        rows.append({
            "authored_object": None if specification is None else specification.to_document(),
            "authored_draft_id": draft.draft_id,
            "authored_configuration": operation.config_identity.to_document(),
            "operation_id": operation.node_id,
            "selected": operation.node_id in selected,
            "obligation_ids": list(operation.obligation_ids),
            "implementation": implementation,
            "input_edges": [{"edge_id": edge.edge_id,
                "input": edge.consumer_input_id, "producer_operation": edge.producer_node_id,
                "producer_output": edge.producer_output_id, "external_input": edge.external_input_id,
                "requirement": edge.requirement_id, "connection": edge.connection_id}
                for edge in links.get(operation.node_id, ())],
            "remediation_owner": "investigation",
        })
    return tuple(rows)
