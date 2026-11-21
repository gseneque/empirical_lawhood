# SPDX-License-Identifier: MPL-2.0
"""Compose operational UI storage through the existing selected scratch policy."""

from pathlib import Path

from empirical_lawhood.api.application_contracts import ApplicationError


def operational_state_store(context, *, path=None):
    from empirical_lawhood.api.codecs import load_registered_authoring
    from empirical_lawhood.storage.artifacts import GuardedExternalRoot
    from empirical_lawhood.storage.workbench_state import WorkbenchStateStore
    from empirical_lawhood.execution.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile, resolve_scientific_scratch_contract

    selected_profile = context.operational_profile or context.operator_profile
    if selected_profile is None:
        raise ApplicationError("PROFILE_REQUIRED", "Select the operator profile for operational storage.")
    if path is None:
        path = context.collection_path
    if path is None:
        raise ApplicationError("COLLECTION_NOT_SELECTED", "Select an operational collection in this context.")
    profile = load_registered_authoring(selected_profile,
        root_schemas={OperatorStorageProfile.SCHEMA: OperatorStorageProfile})
    contract = resolve_scientific_scratch_contract(profile,
        repo_root=context.project_root or Path.cwd(), home_root=Path.home(), for_write=False)
    return WorkbenchStateStore(GuardedExternalRoot(contract), path,
        writable=profile.access_mode is OperatorStorageAccessMode.READ_WRITE)
