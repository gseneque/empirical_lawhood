# SPDX-License-Identifier: MPL-2.0
"""Compatibility observation exports and registered scientific admissibility."""

from empirical_lawhood.infrastructure.numerical_provenance import (
    authenticate_recorded_numerical_provenance,
    capture_numerical_provenance,
    immutable_json,
    numerical_package_code_sha256,
    numerical_package_sources,
    numerical_runtime_observation,
    selected_dependency_lock_sha256,
)

__all__ = (
    "authenticate_recorded_numerical_provenance", "capture_numerical_provenance",
    "immutable_json", "numerical_package_code_sha256", "numerical_package_sources",
    "numerical_runtime_observation", "selected_dependency_lock_sha256",
    "validate_registered_provenance",
)

def validate_registered_provenance(*, provenance, draft, registrations):
    """Run each selected scientific requirement once at this fresh boundary."""
    authenticate_recorded_numerical_provenance(provenance)
    by_selection = {value.selection.selection_id: value for value in registrations}
    if len(by_selection) != len(registrations):
        raise ValueError("numerical provenance repeats an operation registration")
    requirements = {}
    for operation in draft.operations:
        if operation.node_id not in draft.selected_operation_ids:
            continue
        registration = by_selection.get(operation.selection.selection_id)
        if registration is None or registration.selection != operation.selection:
            raise ValueError("numerical provenance substitutes a selected operation")
        for requirement in registration.provenance_requirements:
            previous = requirements.setdefault(requirement.requirement_id, requirement)
            if previous != requirement:
                raise ValueError("numerical provenance requirement has conflicting scientific validators")
    for _, requirement in sorted(requirements.items()):
        if requirement.validate_observation(provenance) is not None:
            raise ValueError("numerical validator must return None on success or raise on refusal")
