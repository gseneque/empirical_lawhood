# SPDX-License-Identifier: MPL-2.0
"""Compose selected application custody without any process-global CLI state."""

from pathlib import Path

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError


def application_storage(context: ApplicationContext, *, for_write=False):
    if type(context) is not ApplicationContext or type(for_write) is not bool:
        raise TypeError("Application storage requires its exact context and write selection")
    if context.operator_profile is None:
        raise ApplicationError("PROFILE_REQUIRED", "Select the operator profile for this retained object.", field="operator_profile")
    if for_write and context.project_root is None:
        raise ApplicationError("SOURCE_REQUIRED", "Select the executing source before authoring or execution.", field="project_root")
    from empirical_lawhood.api.codecs import load_registered_authoring
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    from empirical_lawhood.execution.operator_profile import OperatorStorageProfile, resolve_external_root_contract
    from empirical_lawhood.execution.experiment_preparation import select_experiment_workers

    root = Path.cwd() if context.project_root is None else context.project_root
    if for_write:
        from empirical_lawhood.storage.source_origin import require_selected_implementation
        require_selected_implementation(root)
    profile = load_registered_authoring(context.operator_profile,
        root_schemas={OperatorStorageProfile.SCHEMA: OperatorStorageProfile})
    selected = None if context.artifact_root_contract is None else load_registered_authoring(
        context.artifact_root_contract, root_schemas={ExternalRootContract.SCHEMA: ExternalRootContract})
    contract = resolve_external_root_contract(profile, repo_root=root, home_root=Path.home(),
        for_write=for_write, selected_contract=selected)
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract), integration_artifact_profile_validators(),
        maximum_parallel_verifications=select_experiment_workers(
            context.maximum_parallel_tasks, profile_maximum=profile.maximum_parallel_tasks),
        artifact_verification=context.artifact_verification)
    plane.root.verify(for_write=for_write)
    return root, profile, plane


def application_read_access(context, *, directory, artifact_writer):
    if not context.read_access_paths:
        return None
    from empirical_lawhood.api.experiment_read_access import experiment_read_access_protocol, load_experiment_read_access
    protocol = experiment_read_access_protocol(directory=directory, artifact_writer=artifact_writer)
    return load_experiment_read_access(context.read_access_paths, protocol_id=protocol)


def application_programme(context, *, root, profile, plane):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    return ExperimentProgrammeService(project_root=root, artifact_writer=plane, storage_profile=profile,
        catalog_relative_path=context.catalog_relative_path, approval_checker_trust_path=context.approval_checker_trust,
        operator_artifact_root_contract=plane.root.contract)
