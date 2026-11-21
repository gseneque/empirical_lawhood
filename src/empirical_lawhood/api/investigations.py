# SPDX-License-Identifier: MPL-2.0
"""Supported investigation authoring, execution, inspection and workspace entry.

The scientific specification is the editable input. The existing programme
service owns compilation, scheduling, result custody and recovery. This module
composes those owners from explicit paths and exposes their supported contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

from empirical_lawhood.science import ObjectIdentity
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection, ExperimentPreparation, select_experiment_workers
from empirical_lawhood.execution.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile, resolve_external_root_contract

from .experiment_preparation import (
    experiment_preparation_report, load_experiment_inputs, load_experiment_specification,
)
from .experiment_programme import ExperimentProgrammeService
from .recursive_authoring import implementation_binding
from .investigation_trace import authored_operation_trace


@dataclass(frozen=True, slots=True)
class LocalWorkspace:
    """Derived operational paths beneath one explicitly selected local root."""
    profile_path: Path
    artifact_root: Path
    scratch_root: Path


def create_local_workspace(root: Path, *, project_root: Path, profile_id: str = "local.research",
                           maximum_parallel_tasks: int | None = None,
                           minimum_free_bytes: int = 1024 * 1024) -> LocalWorkspace:
    """Create one new local workspace using the existing contained storage policy.

    No source inputs, scientific evidence or permissions are invented. Existing
    roots and symbolic links are refused; a profile grants no operation authority.
    Explicit operational limits remain supported and are checked by their owner.
    """
    root, source = Path(root).absolute(), Path(project_root).absolute()
    if ".." in root.parts or any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("local workspace refuses parent traversal and symbolic links")
    if root.exists():
        raise FileExistsError("local workspace requires a new explicitly selected directory")
    workers = (min(64, select_experiment_workers(None)) if maximum_parallel_tasks is None
        else select_experiment_workers(maximum_parallel_tasks))
    from empirical_lawhood.storage.workspaces import containing_mount
    mount = containing_mount(root)
    profile = OperatorStorageProfile(
        profile_id=profile_id, backend_key="external-filesystem", backend_version="1.0.0",
        external_root_locator=str(root), required_mount_path=str(mount), artifact_namespace="artifacts",
        scientific_scratch_namespace="scratch", access_mode=OperatorStorageAccessMode.READ_WRITE,
        expected_mount_source=None, expected_volume_identity=None, allowed_filesystem_types=(),
        containment_policy_key="explicit-local-contained-no-symlink", minimum_free_bytes=minimum_free_bytes,
        read_only_mirror_ids=(), maximum_parallel_tasks=workers, authority_granted=False,
    )
    # Validate the same forbidden roots and custody separation used at entry,
    # before creating any directory or publishing the profile.
    resolve_external_root_contract(profile, repo_root=source, home_root=Path.home(), for_write=False)
    root.mkdir(parents=True, exist_ok=False)
    artifact, scratch = root / "artifacts", root / "scratch"
    artifact.mkdir()
    scratch.mkdir()
    path = root / "operator-storage.json"
    with path.open("xb") as stream:
        stream.write(profile.canonical_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    return LocalWorkspace(path, artifact, scratch)


def create_investigation_service(*, project_root: Path, operator_profile: Path,
                                artifact_root_contract: Path | None = None) -> ExperimentProgrammeService:
    """Compose the ordinary shared lifecycle from source and operator selections."""
    from .application_contracts import ApplicationContext
    from .application_context import application_storage, application_programme

    context = ApplicationContext(
        context_id="investigation.public", label="Selected investigation",
        python_executable=Path(sys.executable).absolute(), project_root=Path(project_root).absolute(),
        operator_profile=Path(operator_profile).absolute(),
        artifact_root_contract=None if artifact_root_contract is None else Path(artifact_root_contract).absolute(),
        maximum_parallel_tasks=None,
    )
    root, profile, plane = application_storage(context)
    return application_programme(context, root=root, profile=profile, plane=plane)


def prepare_investigation(service: ExperimentProgrammeService, *, specification_path: Path,
                          source_selection_path: Path, environment_id: str,
                          protocol_path: Path | None = None, read_access=None) -> ExperimentPreparation:
    """Derive a plan from the selected scientific definition and original inputs.

    Source and configuration identities are calculated here; callers do not
    construct them. Preparation retains unresolved scientific dependencies and
    starts no worker. Authoring and run repeat their original entry checks.
    """
    if type(service) is not ExperimentProgrammeService:
        raise TypeError("preparation requires the public shared investigation service")
    specification = load_experiment_specification(Path(specification_path))
    selected = load_experiment_inputs(specification, Path(source_selection_path),
        artifact_writer=service.artifact_writer, read_access=read_access)
    source = implementation_binding(service.project_root)
    execution = ExecutionSelection(environment_id=environment_id,
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source),
        output_root=service.artifact_writer.root.contract.canonical_path)
    protocol = None
    if protocol_path is not None:
        from empirical_lawhood.storage.bounded_io import read_bounded_bytes
        protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024 * 1024)
    return service.prepare(specification, scientific_inputs=selected.scientific_inputs,
        method_inputs=selected.method_inputs, execution=execution, protocol_bytes=protocol)


__all__ = [
    "ExecutionSelection", "ExperimentPreparation", "ExperimentProgrammeService", "LocalWorkspace", "ObjectIdentity",
    "create_local_workspace", "create_investigation_service", "prepare_investigation",
    "authored_operation_trace", "experiment_preparation_report", "load_experiment_inputs", "load_experiment_specification", "implementation_binding",
]
