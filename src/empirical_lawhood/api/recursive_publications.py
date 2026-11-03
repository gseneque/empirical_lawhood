# SPDX-License-Identifier: MPL-2.0
"""Selected registered publication predicates; domain science stays in adapters."""


def authenticate_draft_publications(*, draft, registrations, artifact_writer) -> None:
    """Recheck registered premises from the exact retained selected configs."""
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, project_recursive_config_inputs

    by_selection = {value.selection.selection_id: value for value in registrations}
    if len(by_selection) != len(registrations):
        raise ValueError("publication validation has duplicate operation registrations")
    selected = set(draft.selected_operation_ids)
    operations = tuple(value for value in draft.operations if value.node_id in selected)
    resolved = []
    for operation in operations:
        registration = by_selection.get(operation.selection.selection_id)
        if registration is None or registration.selection != operation.selection:
            raise ValueError("publication validation substitutes a selected operation/configuration")
        resolved.append((operation, registration))
    if not any(registration.publication_requirements for _, registration in resolved):
        return
    config_inputs = project_recursive_config_inputs(tuple(decode_recursive_config_input(operation, registration)
        for operation, registration in resolved), {operation.node_id: registration for operation, registration in resolved})
    authenticate_registered_publications(draft=draft, config_inputs=config_inputs,
        registrations=registrations, artifact_writer=artifact_writer)


def authenticate_registered_publications(*, draft, config_inputs, registrations,
                                         artifact_writer) -> None:
    """Dispatch each requirement once within this boundary's verification scope.

    The next authoring/read/transport boundary authenticates again. This scope
    creates no issue, outcome access, qualification or retry authority.
    """
    from empirical_lawhood.runtime.recursive_compiler import validate_recursive_config_input
    by_selection = {value.selection.selection_id: value for value in registrations}
    if len(by_selection) != len(registrations):
        raise ValueError("publication validation has duplicate operation registrations")
    selected = set(draft.selected_operation_ids)
    operations = {value.node_id: value for value in draft.operations if value.node_id in selected}
    groups = {}
    seen_nodes = set()
    all_config_records = tuple(sorted(((row.node_id, row.record) for row in config_inputs), key=lambda value: value[0]))
    for row in config_inputs:
        if row.node_id in seen_nodes:
            raise ValueError("publication validation repeats a frozen configuration")
        seen_nodes.add(row.node_id)
        operation = operations.get(row.node_id)
        registration = (None if operation is None else by_selection.get(operation.selection.selection_id))
        if (registration is None or registration.selection != operation.selection
                or type(row.record) is not registration.config_record_type):
            raise ValueError("publication validation substitutes a selected operation/configuration")
        validate_recursive_config_input(operation=operation, registration=registration, config_input=row,
            all_config_records=all_config_records)
        for requirement in registration.publication_requirements:
            group = groups.setdefault(requirement.requirement_id, (requirement, []))
            if group[0] != requirement:
                raise ValueError("registered publication requirement ID has conflicting validators")
            group[1].append(row)
    if seen_nodes != set(operations):
        raise ValueError("publication validation omits a selected frozen configuration")
    for _, (requirement, rows) in sorted(groups.items()):
        if requirement.validate(artifact_writer, tuple(sorted(rows, key=lambda row: row.node_id))) is not None:
            raise ValueError("publication validator must raise on refusal and return None on success")
