# SPDX-License-Identifier: MPL-2.0
"""Select unfinished operations and import their exact completed inputs."""
from collections import Counter
from dataclasses import replace

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole


def select_unfinished(lowered, scope, *, assessment_task_id, fit_cutoff):
    """Derive the cut from the complete owner-produced graph, never a task list."""
    scope.__post_init__()
    draft = lowered.draft
    complete = {operation.node_id for operation in draft.operations}
    done = {task for task, _ in scope.completed_receipts}
    from .configured_closeout_execution import ConfiguredE3ClosedExecution
    closed = type(scope) is ConfiguredE3ClosedExecution
    excluded = set(scope.excluded_native_task_ids) if closed else set()
    pending = complete - done - excluded
    if tuple(sorted(pending)) != scope.unfinished_task_ids or not done <= complete:
        raise ValueError('unfinished E3 substitutes the complete original graph or completed census')
    imports = {row.key: row for row in scope.imported_outputs}
    links, external, records, files, used, consumers = [], {}, dict(lowered.input_records), dict(lowered.file_identities), set(), set()
    original_external = {row.input_id: row for row in draft.external_inputs}
    for link in draft.links:
        if link.consumer_node_id not in pending:
            continue
        if link.producer_node_id in done:
            key = link.producer_node_id, link.producer_output_id.rsplit('.', 1)[-1]
            if key not in imports:
                raise ValueError('unfinished E3 omits a completed boundary output')
            row = imports[key]
            logical, physical = row.logical, row.materialization
            input_id = 'external.' + logical.logical_artifact_id
            item = RecursiveExternalInput(input_id, logical.logical_artifact_id, logical.payload_schema,
                logical.media_type, physical.size_bytes, logical.outcome_access, logical.visibility_ceiling,
                logical.content_sha256, 'HISTORY')
            external[input_id] = item
            files[input_id] = ArtifactIdentity(logical.logical_artifact_id, 'completed-e3-input', logical.payload_schema,
                logical.content_sha256, logical.media_type, physical.size_bytes)
            link = replace(link, producer_node_id=None, producer_output_id=None,
                external_input_id=input_id, scientific_role='HISTORY')
            used.add(key)
            consumers.add(link.consumer_node_id)
        elif link.external_input_id is not None:
            external[link.external_input_id] = original_external[link.external_input_id]
        links.append(link)
    if used != set(imports):
        raise ValueError('unfinished E3 adds an unconsumed original output import')
    scope_input = 'external.input.matrix-e3.' + scope.fingerprint()
    external[scope_input] = RecursiveExternalInput(scope_input, 'input.matrix-e3.' + scope.fingerprint(),
        scope.SCHEMA, 'application/json', len(scope.canonical_bytes()), OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, scope.fingerprint(), 'SOURCE')
    records[scope_input] = scope
    name = 'closeout' if closed else 'unfinished'
    for node in sorted(consumers):
        links.append(RecursiveInputLink('edge.' + node + '.' + name, node, name,
            external_input_id=scope_input, scientific_role='SOURCE'))
    # Imported forecasts retain their original pre-future seals. The final
    # assessment owns the current wave's verification of those retained facts.
    retained_obligations = {key for operation in draft.operations if operation.node_id in done
        for key in operation.obligation_ids if not key.startswith('obligation.')}
    operations = tuple(replace(operation, obligation_ids=tuple(sorted(set(operation.obligation_ids) | retained_obligations)))
        if operation.node_id == assessment_task_id else operation for operation in draft.operations)
    root = draft.prospective_draft
    original_pin = root.design_inputs[0]
    scope_pin = DesignInputRecord('design.matrix-e3.' + scope.fingerprint(), scope.identity, scope.fingerprint(),
        fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, original_pin.operator_id)
    pins_by_id = {row.input_id: row for row in root.design_inputs}
    if pins_by_id.setdefault(scope_pin.input_id, scope_pin) != scope_pin:
        raise ValueError('unfinished E3 changes its original predecessor design binding')
    pins = tuple(pins_by_id[key] for key in sorted(pins_by_id))
    root = replace(root, design_inputs=pins,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(row.input_id for row in pins)))
    draft = replace(draft, operations=operations, selected_operation_ids=tuple(sorted(pending)), prospective_draft=root,
        links=tuple(sorted(links, key=lambda row: row.edge_id)),
        external_inputs=tuple(sorted(external.values(), key=lambda row: row.input_id)))
    keys = set(external)
    cells, removed_physical, removed_retries = [], Counter(), Counter()
    for cell in lowered.resource_selection.task_cells:
        if cell.task_id in pending:
            cells.append(cell)
        else:
            removed_physical[cell.child_id] += cell.physical_execution_cost * cell.maximum_attempts
            removed_retries[cell.child_id] += cell.retry_token_cost * (cell.maximum_attempts - 1)
    # Freeze only the new graph's prospective demand. The bound predecessor
    # retains all spent reservations and unknown-completion resource history.
    limits = tuple(replace(limit,
        physical_execution_token_limit=limit.physical_execution_token_limit - removed_physical[limit.child_id],
        retry_token_limit=limit.retry_token_limit - removed_retries[limit.child_id])
        for limit in lowered.resource_selection.child_token_limits)
    resources = replace(lowered.resource_selection, task_cells=tuple(cells), child_token_limits=limits)
    return replace(lowered, draft=draft, resource_selection=resources,
        input_records=tuple(sorted((key, value) for key, value in records.items() if key in keys)),
        file_identities=tuple(sorted((key, value) for key, value in files.items() if key in keys)))
