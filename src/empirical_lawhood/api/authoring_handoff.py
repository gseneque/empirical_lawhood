"""Shared application mechanics for typed native authoring handoffs.

SPDX-License-Identifier: MPL-2.0
"""

import os
from pathlib import Path
import pwd

from empirical_lawhood.adapters.composition.generated_executable_bindings import (
    EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY,
    EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
)
from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ExternalRootContract, artifact_custody_limits
from empirical_lawhood.runtime.candidate_composition import CandidateCapabilityCatalog, CandidateContextProvider
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract
from empirical_lawhood.runtime.plans import CandidateExecutionPlan


def write_exclusive_record(directory: Path, name: str, record: CanonicalRecord) -> Path:
    path = directory / name
    with path.open("xb") as handle:
        handle.write(record.canonical_bytes())
        handle.flush()
    return path


def create_authoring_api(
    *, repo_root: Path, candidate_context_provider: CandidateContextProvider,
    candidate_capability_catalog: CandidateCapabilityCatalog,
) -> EmpiricalLawhoodApi:
    return EmpiricalLawhoodApi(
        repo_root=repo_root,
        external_root=None,
        candidate_context_provider=candidate_context_provider,
        candidate_capability_catalog=candidate_capability_catalog,
        extension_bundle_aggregate=GENERATED_EXTENSION_BUNDLE_AGGREGATE,
        executable_binding_aggregate=EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.aggregate,
        executable_factory_registry=EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
        study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY,
    )


def preflight_output_directory(
    *, directory: Path,
    allow_existing_empty: bool = False,
) -> Path:
    """Check a fresh real-directory destination without creating it or reading inputs."""
    if ".." in directory.parts or any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError("authoring output refuses parent traversal and symbolic links")
    selected = directory.absolute()
    if selected.exists() and (
        not allow_existing_empty or not selected.is_dir() or any(selected.iterdir())
    ):
        raise FileExistsError("authoring output must be a fresh directory")
    if any(parent.exists() and not parent.is_dir() for parent in selected.parents):
        raise NotADirectoryError("authoring output has a non-directory parent")
    return selected


def preflight_authoring_output_directory(
    *, directory: Path, repo_root: Path, artifact_writer,
    allow_existing_empty: bool = False,
) -> Path:
    """Validate a guarded output before upstream reads; create no directory."""
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane

    if not isinstance(artifact_writer, ExternalArtifactPlane):
        raise TypeError("current authoring requires its actual guarded external artifact plane")
    selected = preflight_output_directory(directory=directory,
        allow_existing_empty=allow_existing_empty)
    guarded = Path(artifact_writer.root.contract.canonical_path)
    resolved = selected.resolve(strict=False)
    if not selected.is_relative_to(guarded) or not resolved.is_relative_to(guarded.resolve(strict=True)):
        raise ValueError("authoring output must be under the selected guarded external root")
    if resolved.is_relative_to(repo_root.resolve(strict=True)):
        raise ValueError("authoring output must be outside the selected checkout")
    artifact_writer.root.verify(for_write=True)
    artifact_writer.root.resolve(selected.relative_to(guarded).as_posix(), for_write=True)
    return selected


def resolve_authoring_directory(
    directory: Path, *, repo_root: Path, storage_profile: OperatorStorageProfile,
    escape_message: str, for_write: bool = True,
) -> tuple[Path, ExternalRootContract]:
    if type(for_write) is not bool:
        raise TypeError("authoring directory access mode requires an exact bool")
    directory = directory.resolve(strict=True)
    contract = resolve_external_root_contract(
        storage_profile, repo_root=repo_root,
        home_root=Path(pwd.getpwuid(os.geteuid()).pw_dir), for_write=for_write,
    )
    if not directory.is_relative_to(Path(contract.canonical_path)):
        raise ValueError(escape_message)
    return directory, contract


def load_authoring_execution_projection(directory: Path, *, artifact_writer=None) -> CandidateExecutionPlan:
    limits = artifact_custody_limits(artifact_writer)
    selected = tuple(value for value in (limits.control_record_bytes, limits.in_memory_payload_bytes)
        if value is not None)
    raw = read_bounded_bytes(directory / "preissue-execution-plan.json",
        maximum_bytes=min(selected) if selected else None)
    return decode_canonical_bytes(raw, CandidateExecutionPlan, maximum_bytes=len(raw))


def read_authoring_source_companion(*, writer, directory, name, expected_schema):
    """Authenticate the original prospective source publication before decoding."""
    from hashlib import sha256
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile

    relative = (directory/name).relative_to(Path(writer.root.contract.canonical_path)).as_posix()
    limits = artifact_custody_limits(writer)
    manifest_raw = read_bounded_bytes(writer.root.resolve(relative+'.manifest.json', for_write=False),
        maximum_bytes=limits.manifest_bytes)
    manifest = decode_artifact_manifest(manifest_raw, maximum_bytes=len(manifest_raw))
    logical, physical = manifest.logical, manifest.materialization
    if ((logical.payload_schema, logical.profile, logical.media_type, logical.outcome_access, logical.visibility_ceiling)
            != (expected_schema, ArtifactProfile.CANONICAL_JSON, 'application/json', OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
            or physical.relative_path != relative or physical.storage_root_id != writer.root.contract.storage_root_id
            or physical.compression != 'none' or physical.partition_selector is not None
            or physical.size_bytes <= 0 or manifest.publication is None):
        raise PermissionError('authoring source companion loses exact bounded public publication custody')
    if (limits.exceeds('control_record_bytes', physical.size_bytes)
            or limits.exceeds('in_memory_payload_bytes', physical.size_bytes)):
        raise ValueError('authoring source companion exceeds its selected custody byte allowance')
    read_publication_metadata(writer, manifest)
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=physical.size_bytes)
    if (len(raw) != physical.size_bytes or sha256(raw).hexdigest() != logical.content_sha256
            or sha256(raw).hexdigest() != physical.physical_sha256):
        raise PermissionError('authoring source companion changes original publication bytes')
    return raw



def require_authoring_source_kind_layout(*, directory, closure):
    """Do not downgrade retained selected-source provenance to legacy CLEAN."""
    from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind

    if type(closure) is not ImplementationSourceClosure:
        raise TypeError('authoring source kind requires its exact closure')
    closure.__post_init__()
    if closure.kind is SourceClosureKind.CLEAN_GIT_COMMIT:
        try:
            (Path(directory) / 'provenance').lstat()
        except FileNotFoundError:
            return
        raise PermissionError('selected-source provenance cannot be replaced by a historical CLEAN closure')

def authenticate_selected_authoring_source(*, directory, project_root, artifact_writer, closure):
    """Replay exact companions for an already decoded selected-source closure.

    Callers retain their original historical CLEAN branch. This function adds
    no fallback source, authority or cross-invocation proof cache.
    """
    from empirical_lawhood.api.recursive_prospective_authoring import _load_source_provenance
    from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
    from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind

    if type(closure) is not ImplementationSourceClosure or closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE:
        raise PermissionError('authoring requires its exact supported selected-source closure')
    closure.__post_init__()
    directory = Path(directory).resolve(strict=True)
    with artifact_writer.verification_scope() as writer:
        _load_source_provenance(directory=directory, closure=closure,
            read=lambda name, *, expected_schema: read_authoring_source_companion(
                writer=writer, directory=directory, name=name, expected_schema=expected_schema))
        writer.require_verification_snapshot()
    GitStudySourceClosureInspector(Path(project_root)).observe(closure)
    return closure


def authenticate_authoring_source(*, directory, project_root, artifact_writer):
    """Read source companions before provider composition; retain old CLEAN packets."""
    from empirical_lawhood.api.recursive_prospective_authoring import MAXIMUM_SPEC_BYTES
    from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind

    directory = Path(directory).resolve(strict=True)
    closure = decode_canonical_bytes(read_bounded_bytes(directory/'source-closure.json', maximum_bytes=MAXIMUM_SPEC_BYTES),
        ImplementationSourceClosure, maximum_bytes=MAXIMUM_SPEC_BYTES)
    require_authoring_source_kind_layout(directory=directory, closure=closure)
    if closure.kind is SourceClosureKind.CLEAN_GIT_COMMIT:
        return closure
    return authenticate_selected_authoring_source(directory=directory, project_root=project_root,
        artifact_writer=artifact_writer, closure=closure)
