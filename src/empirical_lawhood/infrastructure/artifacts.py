"""Guarded, immutable external artifact plane and safe serializers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import stat
import threading
import time
from contextlib import ExitStack, contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol, TypeVar

import numpy as np
import numpy.typing as npt
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from .artifact_stream_primitives import (
    _anonymous_input_descriptor as _anonymous_input_descriptor,
    _seal_anonymous_input as _seal_anonymous_input,
    _PreopenedBoundedReader as _PreopenedBoundedReader,
)
from .atomic_files import rename_noreplace
from .canonical_record_read import current_canonical_record_read
from .artifact_verification import (
    artifact_verification_operation,
    force_full_verification,
    full_verification_forced,
)
from .artifact_sidecars import (
    decode_artifact_sidecar,
    encode_artifact_manifest_reference,
    read_artifact_sidecar,
    resolve_artifact_manifest_reference,
)
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference

from empirical_lawhood.kernel.serialization import (
    canonical_json_bytes,
)
from empirical_lawhood.runtime.artifacts import (
    ArtifactManifest,
    ArtifactMaterialization,
    ArtifactProfile,
    ArtifactPublicationBinding,
    ArtifactPublicationCommit,
    ArtifactPublicationIntent,
    ArtifactPublicationScope,
    ArtifactSemanticValidation,
    ArtifactSemanticValidationRegistry,
    artifact_publication_batch_id,
    artifact_publication_commit_relative_path,
    artifact_publication_intent_relative_path,
    artifact_publication_member,
    ArtifactCustodyLimits,
    ArtifactStreamWriteRequest,
    ArtifactWriteRequest,
    ArtifactWriteResult,
    ExternalRootContract,
    LogicalArtifactIdentity,
    MAX_ARTIFACT_PUBLICATION_PATH_BYTES,
    validate_relative_locator,
)
from empirical_lawhood.runtime.execution import (
    VerifiedArtifactInput,
    WorkerInputBinding,
    WorkerInputKind,
    WorkerInputPort,
)
from empirical_lawhood.runtime.progress import report_progress
from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode

from .bounded_io import (
    BoundedFileIOError,
    bounded_file_sha256,
    file_matches_bytes,
    read_bounded_bytes,
)
from .bounded_process import BoundedProcessError, run_bounded_command
from .file_locks import exclusive_file_lock
from .artifact_validation import (
    ArrowFieldContract as ArrowFieldContract,
    ArrowTableContract as ArrowTableContract,
    ArtifactIdentityConflict as ArtifactIdentityConflict,
    ArtifactInputLimitExceeded as ArtifactInputLimitExceeded,
    ArtifactPlaneError as ArtifactPlaneError,
    ArtifactProfileValidatorRegistry as ArtifactProfileValidatorRegistry,
    ExternalRootUnavailable as ExternalRootUnavailable,
    HDF5AttributeContract as HDF5AttributeContract,
    HDF5AttributeKind as HDF5AttributeKind,
    HDF5DatasetStorageContract as HDF5DatasetStorageContract,
    HDF5InventoryContract as HDF5InventoryContract,
    HDF5ObjectContract as HDF5ObjectContract,
    HDF5ObjectKind as HDF5ObjectKind,
    MAX_CANONICAL_JSON_DEPTH as MAX_CANONICAL_JSON_DEPTH,
    MAX_CANONICAL_JSON_TOKEN_BYTES as MAX_CANONICAL_JSON_TOKEN_BYTES,
    MAX_IN_MEMORY_ARTIFACT_BYTES as MAX_IN_MEMORY_ARTIFACT_BYTES,
    MAX_JSONL_RECORD_BYTES as MAX_JSONL_RECORD_BYTES,
    MAX_MODEL_PAYLOAD_BYTES as MAX_MODEL_PAYLOAD_BYTES,
    MAX_SAFETENSORS_HEADER_BYTES as MAX_SAFETENSORS_HEADER_BYTES,
    MAX_TEXT_PARAMETER_BYTES as MAX_TEXT_PARAMETER_BYTES,
    MAX_VALIDATOR_IMPLEMENTATION_SOURCE_BYTES as MAX_VALIDATOR_IMPLEMENTATION_SOURCE_BYTES,
    NumpyArrayContract as NumpyArrayContract,
    ParquetColumnContract as ParquetColumnContract,
    ParquetTableContract as ParquetTableContract,
    STREAM_CHUNK_BYTES as STREAM_CHUNK_BYTES,
    _CanonicalJsonFileInspector as _CanonicalJsonFileInspector,
    _decoded_json_bytes as _decoded_json_bytes,
    _metadata_json as _metadata_json,
    _strict_json as _strict_json,
    _validate_metadata_pairs as _validate_metadata_pairs,
    numpy_no_pickle_bytes as numpy_no_pickle_bytes,
    parquet_bytes as parquet_bytes,
    validate_numpy_no_pickle as validate_numpy_no_pickle,
)


_MemberValidationResult = TypeVar("_MemberValidationResult")
_VerificationSnapshot = tuple[int, int, int, int, int, str]
_read_dependency_selections = ContextVar('artifact_read_dependency_selections', default=())


@dataclass(slots=True)
class BoundedSerializedArtifact:
    """One verified external-scratch serialization, consumed as bounded bytes."""

    size_bytes: int
    physical_sha256: str
    _path: Path
    _consumed: bool = False

    def chunks(self, maximum_chunk_bytes: int = STREAM_CHUNK_BYTES) -> Iterator[bytes]:
        if maximum_chunk_bytes <= 0 or maximum_chunk_bytes > STREAM_CHUNK_BYTES:
            raise ValueError("serialized artifact chunk bound is invalid")
        if self._consumed:
            raise ArtifactIdentityConflict("serialized artifact was already consumed")
        observed_size, observed_sha256 = ExternalArtifactPlane._stream_identity(
            self._path,
            maximum_bytes=self.size_bytes,
        )
        if observed_size != self.size_bytes or observed_sha256 != self.physical_sha256:
            raise ArtifactIdentityConflict("serialized scratch identity drifted")
        self._consumed = True
        descriptor = os.open(
            self._path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        digest = hashlib.sha256()
        remaining = self.size_bytes
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size != self.size_bytes:
                raise ArtifactIdentityConflict("serialized scratch size or type drifted")
            while remaining:
                chunk = os.read(descriptor, min(maximum_chunk_bytes, remaining))
                if not chunk:
                    raise ArtifactIdentityConflict("serialized scratch was truncated")
                remaining -= len(chunk)
                digest.update(chunk)
                yield chunk
            if os.read(descriptor, 1):
                raise ArtifactIdentityConflict("serialized scratch exceeded its byte bound")
            after = os.fstat(descriptor)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if before_identity != after_identity or digest.hexdigest() != self.physical_sha256:
                raise ArtifactIdentityConflict(
                    "serialized scratch identity drifted during streaming"
                )
        finally:
            os.close(descriptor)

    def close(self) -> None:
        if self._path.exists():
            self._path.unlink()














@dataclass(frozen=True, slots=True)
class FilesystemState:
    canonical_root: str
    active_mount: bool
    writable: bool
    free_bytes: int
    path_is_symlink: bool
    mount_source: str | None = None
    volume_identity: str | None = None
    filesystem_type: str | None = None


@dataclass(frozen=True, slots=True)
class ExternalStorageDiagnostic:
    mount_active: bool
    canonical_contained: bool
    symlink_safe: bool
    mount_source: str | None
    mount_source_matches: bool
    volume_identity: str | None
    volume_identity_matches: bool
    filesystem_type: str | None
    filesystem_allowed: bool
    writable: bool
    observed_free_bytes: int
    effective_write_floor_bytes: int
    read_ready: bool
    write_ready: bool
    reason_codes: tuple[str, ...]


class FilesystemInspector(Protocol):
    def inspect(self, contract: ExternalRootContract) -> FilesystemState: ...


class LocalFilesystemInspector:
    def __init__(self) -> None:
        self._bound: tuple[FilesystemState, tuple[int, int], tuple[int, int]] | None = None

    def inspect_bound(self, contract: ExternalRootContract) -> FilesystemState:
        """Check the bound volume cheaply between full operation preflights."""
        if self._bound is None or self._bound[0].canonical_root != contract.canonical_path:
            return self.inspect(contract)
        state, root_identity, mount_identity = self._bound
        root, mount = Path(contract.canonical_path), Path(contract.required_mount_path)
        try:
            current_root, current_mount = root.stat(), mount.stat()
            if (
                (current_root.st_dev, current_root.st_ino) != root_identity
                or (current_mount.st_dev, current_mount.st_ino) != mount_identity
                or not os.path.ismount(mount)
                or root.resolve(strict=True) != root
                or mount.resolve(strict=True) != mount
            ):
                raise ExternalRootUnavailable("bound external volume was removed or replaced")
            return replace(
                state, writable=os.access(root, os.W_OK), free_bytes=shutil.disk_usage(root).free
            )
        except OSError as error:
            raise ExternalRootUnavailable("bound external volume is unavailable") from error

    def inspect(self, contract: ExternalRootContract) -> FilesystemState:
        root = Path(contract.canonical_path)
        mount = Path(contract.required_mount_path)
        resolved_root = root.resolve(strict=True)
        resolved_mount = mount.resolve(strict=True)
        try:
            resolved_root.relative_to(resolved_mount)
        except ValueError as error:
            raise ExternalRootUnavailable("external root escapes its required mount") from error
        usage = shutil.disk_usage(resolved_root)
        try:
            completed = run_bounded_command(
                [
                    "findmnt",
                    "--json",
                    "--target",
                    str(resolved_mount),
                    "--output",
                    "SOURCE,FSTYPE,UUID,TARGET",
                ],
                timeout_seconds=5,
                maximum_stdout_bytes=64 * 1024,
                maximum_stderr_bytes=16 * 1024,
            )
            if completed.returncode != 0:
                raise BoundedProcessError("findmnt returned a non-zero status")
            filesystems = json.loads(completed.stdout.decode("utf-8")).get("filesystems", [])
            mount_fact = filesystems[0] if len(filesystems) == 1 else {}
        except (
            BoundedProcessError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise ExternalRootUnavailable("cannot inspect the required mount identity") from error
        target = mount_fact.get("target")
        exact_mount = target == str(resolved_mount)
        state = FilesystemState(
            canonical_root=str(resolved_root),
            active_mount=os.path.ismount(resolved_mount) and exact_mount,
            writable=os.access(resolved_root, os.W_OK),
            free_bytes=usage.free,
            path_is_symlink=root.is_symlink() or mount.is_symlink(),
            mount_source=mount_fact.get("source"),
            volume_identity=mount_fact.get("uuid"),
            filesystem_type=mount_fact.get("fstype"),
        )
        root_stat, mount_stat = resolved_root.stat(), resolved_mount.stat()
        if root_stat.st_dev != mount_stat.st_dev:
            raise ExternalRootUnavailable("external root belongs to a different mounted volume")
        self._bound = (
            state,
            (root_stat.st_dev, root_stat.st_ino),
            (mount_stat.st_dev, mount_stat.st_ino),
        )
        return state


class GuardedExternalRoot:
    def __init__(
        self,
        contract: ExternalRootContract,
        inspector: FilesystemInspector | None = None,
    ) -> None:
        self.contract = contract
        self.inspector = inspector or LocalFilesystemInspector()

    def diagnostic(
        self,
        *,
        operation_minimum_free_bytes: int = 0,
    ) -> ExternalStorageDiagnostic:
        if operation_minimum_free_bytes < 0:
            raise ValueError("operation free-space floor must be nonnegative")
        state = self.inspector.inspect(self.contract)
        canonical_contained = state.canonical_root == self.contract.canonical_path
        symlink_safe = not state.path_is_symlink
        source_matches = (
            self.contract.expected_mount_source is None
            or state.mount_source == self.contract.expected_mount_source
        )
        volume_matches = (
            self.contract.expected_volume_identity is None
            or state.volume_identity == self.contract.expected_volume_identity
        )
        filesystem_allowed = (
            not self.contract.allowed_filesystem_types
            or state.filesystem_type in self.contract.allowed_filesystem_types
        )
        effective_floor = max(
            self.contract.minimum_free_bytes,
            operation_minimum_free_bytes,
        )
        reasons = []
        if not canonical_contained:
            reasons.append("EXTERNAL_ROOT_IDENTITY_DRIFT")
        if not state.active_mount:
            reasons.append("EXTERNAL_MOUNT_INACTIVE")
        if not symlink_safe:
            reasons.append("EXTERNAL_ROOT_SYMLINKED")
        if not source_matches:
            reasons.append("EXTERNAL_MOUNT_SOURCE_MISMATCH")
        if not volume_matches:
            reasons.append("EXTERNAL_VOLUME_IDENTITY_MISMATCH")
        if not filesystem_allowed:
            reasons.append("EXTERNAL_FILESYSTEM_NOT_ALLOWED")
        read_ready = not reasons
        if not state.writable:
            reasons.append("EXTERNAL_STORAGE_NOT_WRITABLE")
        if state.free_bytes < effective_floor:
            reasons.append("EXTERNAL_FREE_SPACE_BELOW_FLOOR")
        return ExternalStorageDiagnostic(
            mount_active=state.active_mount,
            canonical_contained=canonical_contained,
            symlink_safe=symlink_safe,
            mount_source=state.mount_source,
            mount_source_matches=source_matches,
            volume_identity=state.volume_identity,
            volume_identity_matches=volume_matches,
            filesystem_type=state.filesystem_type,
            filesystem_allowed=filesystem_allowed,
            writable=state.writable,
            observed_free_bytes=state.free_bytes,
            effective_write_floor_bytes=effective_floor,
            read_ready=read_ready,
            write_ready=read_ready and state.writable and state.free_bytes >= effective_floor,
            reason_codes=tuple(sorted(reasons)),
        )

    def verify(
        self,
        *,
        for_write: bool,
        operation_minimum_free_bytes: int = 0,
    ) -> Path:
        return self._verify(
            for_write=for_write,
            operation_minimum_free_bytes=operation_minimum_free_bytes,
            refresh_mount=True,
        )

    def _verify(
        self, *, for_write: bool, operation_minimum_free_bytes: int, refresh_mount: bool
    ) -> Path:
        if operation_minimum_free_bytes < 0:
            raise ValueError("operation free-space floor must be nonnegative")
        state = (
            self.inspector.inspect_bound(self.contract)
            if not refresh_mount and isinstance(self.inspector, LocalFilesystemInspector)
            else self.inspector.inspect(self.contract)
        )
        if state.canonical_root != self.contract.canonical_path:
            raise ExternalRootUnavailable("external root canonical identity drifted")
        if not state.active_mount:
            raise ExternalRootUnavailable("required external mount is not active")
        if state.path_is_symlink:
            raise ExternalRootUnavailable("external root or mount is symlinked")
        if (
            self.contract.expected_mount_source is not None
            and state.mount_source != self.contract.expected_mount_source
        ):
            raise ExternalRootUnavailable("external mount source identity differs")
        if (
            self.contract.expected_volume_identity is not None
            and state.volume_identity != self.contract.expected_volume_identity
        ):
            raise ExternalRootUnavailable("external volume identity differs")
        if self.contract.allowed_filesystem_types and (
            state.filesystem_type not in self.contract.allowed_filesystem_types
        ):
            raise ExternalRootUnavailable("external filesystem type is not allowed")
        if for_write:
            effective_floor = max(
                self.contract.minimum_free_bytes,
                operation_minimum_free_bytes,
            )
            if state.free_bytes < effective_floor:
                raise ExternalRootUnavailable("external root violates its free-space floor")
            if not state.writable:
                raise ExternalRootUnavailable("external root is not writable")
        return Path(state.canonical_root)

    def resolve(
        self,
        relative_path: str,
        *,
        for_write: bool,
        operation_minimum_free_bytes: int = 0,
    ) -> Path:
        validate_relative_locator(relative_path)
        root = self._verify(
            for_write=for_write,
            operation_minimum_free_bytes=operation_minimum_free_bytes,
            refresh_mount=False,
        )
        candidate = root.joinpath(*Path(relative_path).parts)
        current = root
        for part in Path(relative_path).parts:
            current = current / part
            try:
                observed = os.stat(current, follow_symlinks=False)
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(observed.st_mode):
                raise ExternalRootUnavailable("artifact path contains a symlink")
            if current != candidate and not stat.S_ISDIR(observed.st_mode):
                raise ExternalRootUnavailable("artifact parent is not a directory")
        return candidate

    @contextmanager
    def read_paths(self, relative_paths):
        """Resolve one finite read census with shared, live ancestor checks.

        This scope supplies paths, never a byte identity or access decision.
        It inspects each selected ancestor once on entry and again on return.
        The caller still reads every file and checks its own complete census.
        A custom resolver keeps its individual call boundaries.
        """
        selected = tuple(relative_paths)
        if (type(self) is not GuardedExternalRoot or 'resolve' in self.__dict__
                or type(self).resolve is not _STANDARD_ROOT_RESOLVE):
            paths = {relative: self.resolve(relative, for_write=False) for relative in selected}
            try:
                yield MappingProxyType(paths)
            finally:
                for relative in selected:
                    self.resolve(relative, for_write=False)
            return
        root = self._verify(for_write=False, operation_minimum_free_bytes=0, refresh_mount=False)
        parents, paths = {}, {}

        def directory_identity(path):
            try:
                value = os.stat(path, follow_symlinks=False)
            except FileNotFoundError:
                return None
            if not stat.S_ISDIR(value.st_mode):
                raise ExternalRootUnavailable('artifact read parent is not an ordinary directory')
            return value.st_dev, value.st_ino, value.st_mode

        for relative in selected:
            validate_relative_locator(relative)
            candidate = root / relative
            current, missing = candidate.parent, []
            # Build each distinct ancestor once for this finite census. Check
            # unseen ancestors from the root before touching a descendant.
            while current != root and current not in parents:
                missing.append(current)
                current = current.parent
            for parent in reversed(missing):
                parents[parent] = directory_identity(parent)
            try:
                value = os.stat(candidate, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                if stat.S_ISLNK(value.st_mode):
                    raise ExternalRootUnavailable('artifact read destination is a symlink')
            paths[relative] = candidate
        try:
            yield MappingProxyType(paths)
        finally:
            if self._verify(for_write=False, operation_minimum_free_bytes=0, refresh_mount=False) != root:
                raise ExternalRootUnavailable('artifact read root changed during its census')
            for path, identity in parents.items():
                if directory_identity(path) != identity:
                    raise ExternalRootUnavailable('artifact read parent changed during its census')
            for path in paths.values():
                try:
                    value = os.stat(path, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if stat.S_ISLNK(value.st_mode):
                    raise ExternalRootUnavailable('artifact read destination became a symlink')


_STANDARD_ROOT_RESOLVE = GuardedExternalRoot.resolve


def _resolved_read_path(root, relative, paths):
    """Use a path only while its complete live census is held by the caller."""
    if paths is None:
        return root.resolve(relative, for_write=False)
    try:
        return paths[relative]
    except KeyError as error:
        raise ArtifactIdentityConflict('artifact read escaped its selected publication paths') from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _materialization_id(logical_id: str, relative_path: str, sha256: str) -> str:
    digest = hashlib.sha256(f"{logical_id}\0{relative_path}\0{sha256}".encode()).hexdigest()
    return f"{logical_id}.{digest[:24]}"


@dataclass(frozen=True, slots=True)
class _StagedArtifactPublication:
    logical: LogicalArtifactIdentity
    materialization: ArtifactMaterialization
    manifest_materialization: ArtifactMaterialization
    artifact_path: Path
    sidecar_path: Path
    staged_artifact_path: Path
    staged_sidecar_path: Path


@dataclass(frozen=True, slots=True)
class _StagedArtifactBatch:
    members: tuple[_StagedArtifactPublication, ...]
    publication: ArtifactPublicationBinding
    commit_payload: bytes
    commit_path: Path
    intent_path: Path
    staged_commit_path: Path


@dataclass(frozen=True, slots=True)
class _PublicationPreflight:
    publication: ArtifactPublicationBinding
    commit_payload: bytes
    identities: tuple[tuple[LogicalArtifactIdentity, ArtifactMaterialization], ...]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class ConcurrentArtifactMemberPreflight:
    """A code-owned guard with independent read state for each caller.

    This supplies no permission or cached verdict. The callback must refresh
    actual access, own its mutable custody state, and return None or raise.
    Ordinary callbacks keep the plane's original serialized invocation.
    """

    callback: Callable[[ArtifactManifest], None]
    read_scope: Callable | None = None

    def __post_init__(self):
        if not callable(self.callback):
            raise TypeError('concurrent artifact preflight requires a callable')
        if self.read_scope is not None and not callable(self.read_scope):
            raise TypeError('concurrent artifact preflight requires a callable read scope')

    def __call__(self, manifest):
        if self.callback(manifest) is not None:
            raise ValueError('artifact member preflight must return None or raise')


def _invoke_member_preflight(plane, callback, manifest):
    if type(callback) is ConcurrentArtifactMemberPreflight:
        callback(manifest)
    else:
        with plane._verification_preflight_lock:
            callback(manifest)


@contextmanager
def _member_preflight_scopes(plane, *, before_member=None, member_preflights=None, paths=None):
    """Keep independent guard facts for one complete effect-free byte read."""
    callbacks = [plane._operation_member_preflight(before_member)]
    registered = member_preflights or {}
    rows_by_path = (registered.values() if paths is None
        else (registered.get(path, ()) for path in paths))
    for rows in rows_by_path:
        callbacks.extend(callback for _, callback in rows)
    scopes = {id(callback): callback.read_scope for callback in callbacks
        if type(callback) is ConcurrentArtifactMemberPreflight and callback.read_scope is not None}
    if not scopes:
        yield
        return
    from .parallel_verification import in_parallel_verification
    with ExitStack() as lifetime:
        for scope in scopes.values():
            lifetime.enter_context(scope())
        # The scheduler already owns concurrent task slots. Keep this
        # caller's mutable guard state on its own thread, without W x W
        # nested verification threads or copied permission-reader state.
        token = in_parallel_verification.set(True)
        try:
            yield
        finally:
            in_parallel_verification.reset(token)


class ExternalArtifactPlane:
    def __init__(
        self,
        root: GuardedExternalRoot,
        validators: ArtifactProfileValidatorRegistry | None = None,
        semantic_validations: ArtifactSemanticValidationRegistry | None = None,
        *,
        custody_limits: ArtifactCustodyLimits | None = None,
        maximum_parallel_verifications: int = 1,
        artifact_verification: ArtifactVerificationMode | str = ArtifactVerificationMode.REDUCED,
    ) -> None:
        if type(maximum_parallel_verifications) is not int or maximum_parallel_verifications < 1:
            raise ValueError("artifact verification requires a positive worker bound")
        self.maximum_parallel_verifications = maximum_parallel_verifications
        self.artifact_verification = ArtifactVerificationMode(artifact_verification)
        self._verification_preflight_lock = threading.RLock()
        self.root = root
        self.custody_limits = custody_limits or ArtifactCustodyLimits()
        self.validators = validators or ArtifactProfileValidatorRegistry()
        self.semantic_validations = semantic_validations or ArtifactSemanticValidationRegistry(
            registry_id="unregistered-artifact-semantics",
            registrations=(),
        )
        if self.custody_limits.exceeds("semantic_validation_registrations", len(self.semantic_validations.registrations)):
            raise ArtifactIdentityConflict("semantic validation registry exceeds its selected allowance")

    def with_semantic_validation_registry(
        self,
        registry: ArtifactSemanticValidationRegistry,
    ) -> ExternalArtifactPlane:
        """Return a plane view bound to one immutable semantic registry."""

        view = ExternalArtifactPlane(
            self.root,
            self.validators,
            registry,
            custody_limits=self.custody_limits,
            maximum_parallel_verifications=self.maximum_parallel_verifications,
            artifact_verification=self.artifact_verification,
        )
        view._verification_preflight_lock = self._verification_preflight_lock
        return view

    @contextmanager
    def verification_scope(self, *, before_member: Callable[[ArtifactManifest], None] | None = None,
            observe_manifest: Callable[[ArtifactManifest], None] | None = None) -> Iterator[ExternalArtifactPlane]:
        """Reuse exact committed batches during one explicit read operation.

        The view checks every previously observed member, sidecar and marker
        before reuse and before successful exit. It retains no authority verdict
        or decoded scientific population. Worker input delivery still uses its
        own fresh verification and sealed descriptors.
        """
        with self._verification_lifetime(before_member=before_member,
                observe_manifest=observe_manifest, verify_on_success=True) as view:
            yield view

    @contextmanager
    def _verification_lifetime(self, *, before_member=None, observe_manifest=None,
            verify_on_success):
        """Own cleanup; the stock read context can own its sole final guard."""
        if before_member is not None and not callable(before_member):
            raise TypeError("artifact context member preflight requires a callable")
        if observe_manifest is not None and not callable(observe_manifest):
            raise TypeError("artifact manifest observer requires a callable")
        inherited = getattr(getattr(self, "_read_verification", None), "context_preflights", ())
        callbacks = inherited + (() if before_member is None else (before_member,))
        observers = getattr(getattr(self, "_read_verification", None), "manifest_observers", ())
        observers += (() if observe_manifest is None else (observe_manifest,))
        from .parallel_verification import canonical_validation_scope
        from empirical_lawhood.kernel.decoding import record_validation_scope
        from empirical_lawhood.kernel.decoded_record_store import decoded_record_scope
        with decoded_record_scope(), record_validation_scope(), canonical_validation_scope(self.maximum_parallel_verifications) as pool, artifact_verification_operation() as ledger:
            view = _ScopedArtifactPlane(self, _ArtifactReadVerification(callbacks, observers, ledger=ledger))
            view._read_verification.canonical_pool = pool
            complete = False
            try:
                yield view
                complete = True
            finally:
                try:
                    if verify_on_success and (complete or self.artifact_verification is ArtifactVerificationMode.REDUCED):
                        view.require_full_verification_snapshot()
                finally:
                    view._read_verification.active = False
                    view._read_verification.canonical_pool = None
                    view._read_verification.snapshots.clear()
                    view._read_verification.member_preflights.clear()
                    view._read_verification.member_manifests.clear()
                    view._read_verification.composed_preflights.clear()
                    view._read_verification.composed_callbacks.clear()
                    view._read_verification.context_preflights = ()
                    view._read_verification.manifest_observers = ()
                    view._read_verification.batches.clear()
                    view._read_verification.publications.clear()
                    view._read_verification.context_manifests.clear()
                    view._read_verification.context_members.clear()
                    view._read_verification.context_censuses.clear()
                    view._read_verification.context_census_sizes.clear()
                    view._read_verification.profiled_members.clear()

    @contextmanager
    def read_context(self, *, before_member: Callable[[ArtifactManifest], None] | None = None,
            observe_manifest: Callable[[ArtifactManifest], None] | None = None) -> Iterator[ExternalArtifactPlane]:
        """Share immutable custody during one bounded, effect-free read.

        Intermediate projections may reuse the authenticated original bytes.
        The complete observed path census is checked before the context exits,
        including on consumer refusal. Reduced checkpoints check paths and
        metadata; strict checkpoints also hash bytes. Access remains current.
        Worker delivery and ordinary verification scopes stay separate.
        An observer receives metadata read during this lifetime, including
        cached metadata reads. It proves neither body acceptance nor access and
        does not inspect siblings or change raw materialization verification.
        """
        options = {} if before_member is None else {"before_member": before_member}
        if observe_manifest is not None:
            options["observe_manifest"] = observe_manifest
        stock_scope = (type(self) is ExternalArtifactPlane
            and _has_stock_manifest_reads(self) and _has_stock_artifact_plane_state(self))
        scope = (self._verification_lifetime(**options, verify_on_success=False)
            if stock_scope else self.verification_scope(**options))
        with scope as view:
            if _has_stock_manifest_reads(self):
                with view.read_context() as reading:
                    yield reading
            else:
                # Custom custody policies retain their original eager calls.
                yield view

    def require_active_verification_scope(self) -> None:
        """Require a live scope only; authenticate no bytes and grant no access."""
        raise ArtifactIdentityConflict("artifact projection reuse requires an active verification scope")

    def require_verification_context(self) -> None:
        """Require the owning finite custody lifetime, without granting access."""
        self.require_verification_snapshot()

    @contextmanager
    def verification_dependencies(self):
        """Name one pure consumer's observed dependencies within a live read.

        Custom policies keep their complete original checkpoint. This never
        changes ordinary publication, worker delivery or final union guards.
        """
        self.require_verification_context()
        checkpoint = _ReadDependencyCheckpoint(self, selected=False)
        try:
            yield checkpoint
        finally:
            try:
                checkpoint.require_current()
            finally:
                checkpoint.close()

    def _note_verification_dependency(self, path):
        verification = getattr(self, '_read_verification', None)
        if verification is not None:
            for selection in _read_dependency_selections.get():
                if selection.verification is verification:
                    selection.include_path(path)

    def _note_verified_publications(self, manifests, members):
        verification = getattr(self, '_read_verification', None)
        selections = tuple(value for value in _read_dependency_selections.get()
            if value.verification is verification)
        if verification is not None and selections:
            for manifest in manifests:
                actual = members[manifest.materialization.relative_path]
                for selection in selections:
                    selection.include_publication(actual.publication)

    def require_verification_snapshot(self) -> None:
        """Require an active explicit verification lifetime for projection reuse."""
        raise ArtifactIdentityConflict("artifact projection reuse requires an active verification scope")

    def require_full_verification_snapshot(self) -> None:
        """Force complete byte checks, including every current access callback."""
        with force_full_verification():
            self.require_verification_snapshot()
        from .read_checkpoint import observe_completed_read
        observe_completed_read(self)

    def _reduced_read_verification(self) -> bool:
        verification = getattr(self, '_read_verification', None)
        return (self.artifact_verification is ArtifactVerificationMode.REDUCED
            and not full_verification_forced() and verification is not None
            and verification.active and verification.context_depth > 0
            and verification.ledger is not None and verification.ledger.active
            and _has_stock_manifest_reads(self) and _has_stock_artifact_plane_state(self)
            and type(self.root) is GuardedExternalRoot
            and type(self.root.inspector) is LocalFilesystemInspector)

    def verified_canonical_header(self, manifest):
        """Return current scanner facts only inside their guarded read context."""
        verification = getattr(self, '_read_verification', None)
        if verification is None or not verification.context_depth or not _has_stock_manifest_reads(self):
            return None
        self.require_verification_context()
        selected = verification.profiled_members.get((self.validators, manifest.materialization.relative_path))
        if selected is None:
            return None
        original, header = selected
        if original != manifest:
            raise ArtifactIdentityConflict('canonical header changes its authenticated manifest')
        return header

    def _require_registered_semantics(
        self,
        logical_artifact_id: str,
        validation: ArtifactSemanticValidation | None,
    ) -> None:
        try:
            self.semantic_validations.resolve(logical_artifact_id, validation)
        except KeyError as error:
            raise ArtifactIdentityConflict(
                "artifact lacks an immutable registered semantic validator"
            ) from error
        except ValueError as error:
            raise ArtifactIdentityConflict(str(error)) from error

    def _serializer_path(
        self,
        suffix: str,
        *,
        maximum_bytes: int,
        minimum_free_bytes: int,
    ) -> Path:
        if maximum_bytes <= 0 or minimum_free_bytes < 0:
            raise ValueError("serializer bounds are invalid")
        token = hashlib.sha256(
            f"{os.getpid()}\0{threading.get_ident()}\0{time.time_ns()}".encode()
        ).hexdigest()[:24]
        path = self.root.resolve(
            f"scratch/artifact-serialization/{token}{suffix}",
            for_write=True,
            operation_minimum_free_bytes=max(maximum_bytes, minimum_free_bytes),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _finish_serialization(
        path: Path,
        *,
        maximum_bytes: int,
    ) -> BoundedSerializedArtifact:
        size_bytes, physical_sha256 = ExternalArtifactPlane._stream_identity(
            path,
            maximum_bytes=maximum_bytes,
        )
        if size_bytes > maximum_bytes:
            raise ArtifactIdentityConflict("serialized artifact exceeds its total byte limit")
        return BoundedSerializedArtifact(
            size_bytes=size_bytes,
            physical_sha256=physical_sha256,
            _path=path,
        )

    def serialize_numpy_chunks(
        self,
        *,
        payload_schema: str,
        chunks: Iterable[npt.NDArray[Any]],
        maximum_bytes: int,
        maximum_input_chunk_bytes: int = STREAM_CHUNK_BYTES,
        minimum_free_bytes: int = 0,
    ) -> BoundedSerializedArtifact:
        """Incrementally build one no-pickle NPY file in guarded scratch."""

        if maximum_input_chunk_bytes <= 0 or maximum_input_chunk_bytes > maximum_bytes:
            raise ValueError("NumPy input chunk bound is invalid")
        contract = self.validators.numpy_contract(payload_schema)
        dtype = np.dtype(contract.dtype)
        if dtype.hasobject or not contract.shape:
            raise ArtifactIdentityConflict(
                "incremental NumPy serialization requires a non-object array with rank"
            )
        if any(dimension is None for dimension in contract.shape):
            raise ArtifactIdentityConflict(
                "incremental NumPy serialization requires an exact registered shape"
            )
        exact_shape = tuple(dimension for dimension in contract.shape if dimension is not None)
        if math.prod(exact_shape) * dtype.itemsize > maximum_bytes:
            raise ArtifactIdentityConflict(
                "registered NumPy array exceeds the serializer byte limit"
            )
        path = self._serializer_path(
            ".npy",
            maximum_bytes=maximum_bytes,
            minimum_free_bytes=minimum_free_bytes,
        )
        try:
            target = np.lib.format.open_memmap(
                path,
                mode="w+",
                dtype=dtype,
                shape=exact_shape,
            )
            offset = 0
            try:
                for chunk in chunks:
                    if (
                        not isinstance(chunk, np.ndarray)
                        or chunk.dtype != dtype
                        or chunk.dtype.hasobject
                        or chunk.ndim != len(exact_shape)
                        or chunk.shape[1:] != exact_shape[1:]
                    ):
                        raise ArtifactIdentityConflict(
                            "NumPy input chunk differs from its registered contract"
                        )
                    if chunk.nbytes > maximum_input_chunk_bytes:
                        raise ArtifactIdentityConflict("NumPy input chunk exceeds its byte limit")
                    next_offset = offset + chunk.shape[0]
                    if next_offset > exact_shape[0]:
                        raise ArtifactIdentityConflict(
                            "NumPy input chunks exceed the registered shape"
                        )
                    target[offset:next_offset] = chunk
                    offset = next_offset
                if offset != exact_shape[0]:
                    raise ArtifactIdentityConflict(
                        "NumPy input chunks do not fill the registered shape"
                    )
                target.flush()
            finally:
                del target
            return self._finish_serialization(path, maximum_bytes=maximum_bytes)
        except Exception:
            if path.exists():
                path.unlink()
            raise

    def serialize_parquet_batches(
        self,
        *,
        payload_schema: str,
        schema: pa.Schema,
        batches: Iterable[pa.RecordBatch],
        maximum_bytes: int,
        maximum_rows: int,
        maximum_batch_rows: int = 65_536,
        maximum_input_batch_bytes: int = STREAM_CHUNK_BYTES,
        minimum_free_bytes: int = 0,
    ) -> BoundedSerializedArtifact:
        """Write bounded Arrow batches as uncompressed Parquet in external scratch."""

        self.validators.validate_table_schema(
            ArtifactProfile.PARQUET,
            payload_schema,
            schema,
        )
        if (
            min(maximum_rows, maximum_batch_rows, maximum_input_batch_bytes) <= 0
            or maximum_input_batch_bytes > maximum_bytes
        ):
            raise ValueError("Parquet batch bounds must be positive")
        path = self._serializer_path(
            ".parquet",
            maximum_bytes=maximum_bytes,
            minimum_free_bytes=minimum_free_bytes,
        )
        rows = 0
        try:
            with pa.OSFile(str(path), "wb") as sink:
                with pq.ParquetWriter(
                    sink,
                    schema,
                    compression="NONE",
                    use_dictionary=False,
                ) as writer:
                    for batch in batches:
                        self._validate_record_batch(
                            batch,
                            schema,
                            maximum_batch_rows=maximum_batch_rows,
                            maximum_input_batch_bytes=maximum_input_batch_bytes,
                        )
                        rows += batch.num_rows
                        if rows > maximum_rows:
                            raise ArtifactIdentityConflict(
                                "Parquet rows exceed the serializer limit"
                            )
                        writer.write_batch(batch)
                        if sink.tell() > maximum_bytes:
                            raise ArtifactIdentityConflict(
                                "Parquet serialization exceeds its byte limit"
                            )
            return self._finish_serialization(path, maximum_bytes=maximum_bytes)
        except Exception:
            if path.exists():
                path.unlink()
            raise

    def serialize_arrow_batches(
        self,
        *,
        payload_schema: str,
        schema: pa.Schema,
        batches: Iterable[pa.RecordBatch],
        maximum_bytes: int,
        maximum_rows: int,
        maximum_batch_rows: int = 65_536,
        maximum_input_batch_bytes: int = STREAM_CHUNK_BYTES,
        minimum_free_bytes: int = 0,
    ) -> BoundedSerializedArtifact:
        """Write bounded record batches as an Arrow IPC file in external scratch."""

        self.validators.validate_table_schema(
            ArtifactProfile.ARROW_IPC,
            payload_schema,
            schema,
        )
        if (
            min(maximum_rows, maximum_batch_rows, maximum_input_batch_bytes) <= 0
            or maximum_input_batch_bytes > maximum_bytes
        ):
            raise ValueError("Arrow batch bounds must be positive")
        path = self._serializer_path(
            ".arrow",
            maximum_bytes=maximum_bytes,
            minimum_free_bytes=minimum_free_bytes,
        )
        rows = 0
        try:
            with pa.OSFile(str(path), "wb") as sink:
                with pa.ipc.new_file(sink, schema) as writer:
                    for batch in batches:
                        self._validate_record_batch(
                            batch,
                            schema,
                            maximum_batch_rows=maximum_batch_rows,
                            maximum_input_batch_bytes=maximum_input_batch_bytes,
                        )
                        rows += batch.num_rows
                        if rows > maximum_rows:
                            raise ArtifactIdentityConflict("Arrow rows exceed the serializer limit")
                        writer.write_batch(batch)
                        if sink.tell() > maximum_bytes:
                            raise ArtifactIdentityConflict(
                                "Arrow serialization exceeds its byte limit"
                            )
            return self._finish_serialization(path, maximum_bytes=maximum_bytes)
        except Exception:
            if path.exists():
                path.unlink()
            raise

    @staticmethod
    def _validate_record_batch(
        batch: pa.RecordBatch,
        schema: pa.Schema,
        *,
        maximum_batch_rows: int,
        maximum_input_batch_bytes: int,
    ) -> None:
        if not isinstance(batch, pa.RecordBatch) or not batch.schema.equals(
            schema,
            check_metadata=True,
        ):
            raise ArtifactIdentityConflict("Arrow input batch differs from its declared schema")
        if batch.num_rows > maximum_batch_rows or batch.nbytes > maximum_input_batch_bytes:
            raise ArtifactIdentityConflict("Arrow input batch exceeds its bound")

    def write(self, request: ArtifactWriteRequest) -> ArtifactWriteResult:
        return self.write_batch((request,))[0]

    def preflight_write(self, request: ArtifactWriteRequest) -> None:
        """Admit exact new, committed or intent-owned bytes without any effects.

        This creates no reusable admission or publication authority. The normal
        immutable writer independently rechecks custody and owns recovery.
        """
        from .task_receipts import encode_artifact_manifest

        if type(request) is not ArtifactWriteRequest:
            raise TypeError("read-only write admission requires an exact in-memory request")
        request.__post_init__()
        preflight = self._preflight_publication((request,))
        self.validators.validate(request, custody_limits=self.custody_limits)
        publication = preflight.publication
        logical, materialization = preflight.identities[0]
        sidecars = tuple(payload for payload in (
            encode_artifact_manifest(logical, materialization, publication),
            encode_artifact_manifest_reference(logical, materialization, publication))
            if not self.custody_limits.exceeds("manifest_bytes", len(payload)))
        components = ((request.relative_path, (request.payload,)),
            (request.relative_path + ".manifest.json", sidecars))
        destinations = tuple(self.root.resolve(relative, for_write=True,
            operation_minimum_free_bytes=request.minimum_free_bytes) for relative, _ in components)
        commit = self.root.resolve(publication.commit_marker_relative_path, for_write=True)
        intent_path = self.root.resolve(artifact_publication_intent_relative_path(
            publication.publication_scope, publication.publication_batch_id), for_write=True)

        def state(path: Path) -> tuple[int, int, int, int, int] | None:
            try:
                value = os.stat(path, follow_symlinks=False)
            except FileNotFoundError:
                return None
            if not stat.S_ISREG(value.st_mode):
                raise ArtifactIdentityConflict("existing publication component is not a regular file")
            return self._descriptor_identity(value)

        try:
            snapshots = {path: state(path) for path in (*destinations, commit, intent_path)}
            committed = snapshots[commit] is not None
            if committed and not self._file_equals(commit, preflight.commit_payload):
                raise ArtifactIdentityConflict("immutable publication commit identity already exists")
            intent = self._read_publication_intent(intent_path) if snapshots[intent_path] is not None else None
            if intent is not None and (intent.publication_batch_id != publication.publication_batch_id
                    or intent.publication_scope != publication.publication_scope or intent.members != publication.members):
                raise ArtifactIdentityConflict("publication intent belongs to another exact batch")
            owned = set() if intent is None else set(intent.absent_relative_paths)
            if not committed and intent is None and any(snapshots[path] is not None for path in destinations):
                raise ArtifactIdentityConflict("existing uncommitted publication lacks its exact durable intent")
            for (relative, expected), path in zip(components, destinations, strict=True):
                if snapshots[path] is None:
                    if committed or (intent is not None and relative not in owned):
                        raise ArtifactIdentityConflict("pre-existing publication member disappeared")
                    continue
                observed = read_bounded_bytes(path, maximum_bytes=max(map(len, expected)))
                if observed not in expected and (committed or relative not in owned
                        or not any(payload.startswith(observed) for payload in expected)):
                    raise ArtifactIdentityConflict("existing publication component differs from its exact request")
            if any(state(path) != identity for path, identity in snapshots.items()):
                raise ArtifactIdentityConflict("artifact publication changed during read-only admission")
        except (OSError, BoundedFileIOError) as error:
            raise ArtifactIdentityConflict("existing artifact publication cannot be admitted safely") from error

    def write_stream(
        self,
        request: ArtifactStreamWriteRequest,
    ) -> ArtifactWriteResult:
        return self.write_batch((request,))[0]

    def write_batch(
        self,
        requests: tuple[ArtifactWriteRequest | ArtifactStreamWriteRequest, ...],
        *,
        compact_manifests: bool = False,
    ) -> tuple[ArtifactWriteResult, ...]:
        """Validate every member before publishing an immutable output batch.

        Staging is bounded by each request and occurs only in hidden files on
        the guarded external filesystem.  Publication then holds every member
        lock in deterministic order.  A caught publication failure removes
        only destinations created by this batch; matching pre-existing
        immutable pairs are never removed.
        """
        if isinstance(self, _ScopedArtifactPlane) and self._read_verification.context_depth:
            raise ArtifactIdentityConflict("artifact read context cannot publish effects")
        if not requests:
            raise ValueError("artifact publication batch cannot be empty")
        if type(compact_manifests) is not bool:
            raise TypeError("compact manifest selection must be a boolean")
        preflight = (self._preflight_publication(requests, compact_manifests=True)
            if compact_manifests else self._preflight_publication(requests))
        relative_paths = tuple(request.relative_path for request in requests)
        all_destinations = (*relative_paths, *(f"{path}.manifest.json" for path in relative_paths))
        if len(set(all_destinations)) != len(all_destinations):
            raise ArtifactIdentityConflict("artifact publication batch paths overlap")
        self._require_publication_descriptor_capacity(len(requests))
        replayed = self._replay_committed_publication(requests, preflight)
        if replayed is not None:
            return replayed
        token = hashlib.sha256(
            (
                f"{os.getpid()}\0{threading.get_ident()}\0{time.time_ns()}\0"
                + "\0".join(relative_paths)
            ).encode("utf-8")
        ).hexdigest()[:24]
        staged: list[_StagedArtifactPublication] = []
        batch: _StagedArtifactBatch | None = None
        try:
            for index, request in enumerate(requests):
                staged.append(self._stage_publication(request, token=token, index=index))
            batch = self._bind_staged_batch(
                tuple(staged),
                publication_scope=preflight.publication.publication_scope,
                token=token,
                compact_manifests=compact_manifests,
            )
            results = self._publish_staged_batch(batch)
        finally:
            for item in staged:
                self._unlink_if_present(item.staged_artifact_path)
                self._unlink_if_present(item.staged_sidecar_path)
            if batch is not None:
                self._unlink_if_present(batch.staged_commit_path)
        return results

    def write_compact_batch(
        self, requests: tuple[ArtifactWriteRequest | ArtifactStreamWriteRequest, ...],
    ) -> tuple[ArtifactWriteResult, ...]:
        """Publish issue metadata with one roster in the existing batch commit.

        Custom writers retain their established policy override unless they
        explicitly implement this hook themselves.
        """
        if type(self).write_batch is not ExternalArtifactPlane.write_batch:
            return self.write_batch(requests)
        return self.write_batch(requests, compact_manifests=True)

    def read_manifest(self, relative_path: str, *, maximum_bytes: int | None = None) -> ArtifactManifest:
        """Read publication metadata for a payload; payload verification is separate."""
        return self._observe_manifest_metadata(read_artifact_sidecar(self,
            relative_path + ".manifest.json", maximum_bytes=maximum_bytes))

    def _observe_manifest_metadata(self, manifest: ArtifactManifest) -> ArtifactManifest:
        """Project existing metadata without adding body access or a proof."""
        from .read_checkpoint import observe_checkpoint_manifest
        observe_checkpoint_manifest(self, manifest)
        verification = getattr(self, "_read_verification", None)
        if verification is not None:
            if _read_dependency_selections.get():
                root = Path(self.root.contract.canonical_path)
                metadata = (root / (manifest.materialization.relative_path + '.manifest.json'),)
                if manifest.publication is not None:
                    metadata += (root / manifest.publication.commit_marker_relative_path,)
                for path in metadata:
                    if path in verification.snapshots:
                        self._note_verification_dependency(path)
            for observe in verification.manifest_observers:
                if observe(manifest) is not None:
                    raise TypeError("artifact manifest observer must return None")
        return manifest

    def _preflight_publication(
        self,
        requests: tuple[ArtifactWriteRequest | ArtifactStreamWriteRequest, ...],
        *,
        compact_manifests: bool = False,
    ) -> _PublicationPreflight:
        """Reject unbounded or cross-authority batches before staging any bytes."""
        from .task_receipts import encode_artifact_manifest

        if self.custody_limits.exceeds("publication_members", len(requests)):
            raise ArtifactIdentityConflict("artifact publication exceeds its member-count bound")
        first = requests[0]
        publication_scope = ArtifactPublicationScope(
            publication_scope_id=first.publication_scope_id,
            storage_root_id=self.root.contract.storage_root_id,
            relative_root=first.publication_scope_relative_root,
            visibility_ceiling=first.visibility_ceiling,
            outcome_access=first.outcome_access,
        )
        declared_bytes = 0
        prospective: list[tuple[LogicalArtifactIdentity, ArtifactMaterialization]] = []
        for request in requests:
            self._validate_publication_request(request)
            if (
                request.publication_scope_id != publication_scope.publication_scope_id
                or request.publication_scope_relative_root != publication_scope.relative_root
            ):
                raise ArtifactIdentityConflict("artifact publication crosses explicit scopes")
            if (
                request.visibility_ceiling is not publication_scope.visibility_ceiling
                or request.outcome_access is not publication_scope.outcome_access
            ):
                raise ArtifactIdentityConflict("artifact publication mixes evidence classes")
            if not publication_scope.contains(request.relative_path):
                raise ArtifactIdentityConflict("artifact path lies outside its publication scope")
            if (
                any(
                    part.endswith(".manifest.json")
                    for part in PurePosixPath(request.relative_path).parts
                )
                or ".publication-batches" in PurePosixPath(request.relative_path).parts
                or len(f"{request.relative_path}.manifest.json".encode("utf-8"))
                > MAX_ARTIFACT_PUBLICATION_PATH_BYTES
            ):
                raise ArtifactIdentityConflict("artifact path violates publication path policy")
            declared_size = (
                len(request.payload)
                if isinstance(request, ArtifactWriteRequest)
                else request.maximum_bytes
            )
            declared_bytes += declared_size
            if self.custody_limits.exceeds("publication_aggregate_bytes", declared_bytes):
                raise ArtifactIdentityConflict(
                    "artifact publication exceeds its aggregate byte bound"
                )
            physical_sha256 = (
                _sha256(request.payload)
                if isinstance(request, ArtifactWriteRequest)
                else (
                    request.expected_physical_sha256 or request.logical_content_sha256 or ("0" * 64)
                )
            )
            if isinstance(request, ArtifactStreamWriteRequest):
                prospective_size = (request.maximum_bytes if request.expected_size_bytes is None
                                    else request.expected_size_bytes)
            else:
                prospective_size = len(request.payload)
            logical, materialization, _manifest, _payload = self._prepare_identity(
                request,
                physical_sha256=physical_sha256,
                size_bytes=prospective_size,
            )
            prospective.append((logical, materialization))
        members = tuple(
            sorted(
                (
                    artifact_publication_member(logical, materialization)
                    for logical, materialization in prospective
                ),
                key=lambda value: value.materialization_id,
            )
        )
        batch_id = artifact_publication_batch_id(publication_scope, members)
        commit = ArtifactPublicationCommit(
            publication_batch_id=batch_id,
            publication_scope=publication_scope,
            members=members,
        )
        commit_payload = commit.canonical_bytes()
        if self.custody_limits.exceeds("publication_marker_bytes", len(commit_payload)):
            raise ArtifactIdentityConflict("artifact publication marker exceeds its byte bound")
        binding = ArtifactPublicationBinding(
            publication_batch_id=batch_id,
            publication_scope=publication_scope,
            commit_marker_relative_path=artifact_publication_commit_relative_path(
                publication_scope,
                batch_id,
            ),
            commit_marker_sha256=_sha256(commit_payload),
            commit_marker_size_bytes=len(commit_payload),
            members=members,
        )
        for logical, materialization in prospective:
            manifest_payload = (encode_artifact_manifest_reference(logical, materialization, binding)
                if compact_manifests else encode_artifact_manifest(logical, materialization, binding))
            if self.custody_limits.exceeds("manifest_bytes", len(manifest_payload)):
                raise ArtifactIdentityConflict("artifact manifest exceeds its byte bound")
        intent = ArtifactPublicationIntent(
            publication_batch_id=batch_id,
            publication_scope=publication_scope,
            members=members,
            absent_relative_paths=tuple(
                sorted(
                    path
                    for member in members
                    for path in (
                        member.relative_path,
                        f"{member.relative_path}.manifest.json",
                    )
                )
            ),
        )
        if self.custody_limits.exceeds("publication_intent_bytes", len(intent.canonical_bytes())):
            raise ArtifactIdentityConflict("artifact publication intent exceeds its byte bound")
        return _PublicationPreflight(binding, commit_payload, tuple(prospective))

    @staticmethod
    def _require_publication_descriptor_capacity(member_count: int) -> None:
        """Admit the simultaneous locks plus bounded I/O before payload staging.

        Eight spare descriptors cover staging, two-file comparisons, profile
        verification and directory/control I/O. The observation includes its
        own directory descriptor conservatively. It is not an OS reservation;
        unrelated concurrent descriptor use can still change capacity.
        """
        try:
            import resource

            soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft == resource.RLIM_INFINITY or soft <= 0:
                raise ValueError("no finite descriptor observation bound")
            opened = 0
            with os.scandir("/proc/self/fd") as entries:
                for entry in entries:
                    if not entry.name.isdecimal():
                        raise ValueError("unsupported descriptor census")
                    opened += 1
                    if opened > soft:
                        raise ValueError("descriptor census exceeds its bound")
        except (ImportError, OSError, ValueError, NotImplementedError) as error:
            raise ExternalRootUnavailable(
                "artifact publication descriptor capacity cannot be observed safely"
            ) from error
        required = member_count + 1 + 8
        if opened + required > soft:
            raise ExternalRootUnavailable(
                f"artifact publication descriptor capacity is insufficient: "
                f"open={opened}, additional={required}, soft_limit={soft}"
            )

    def _replay_committed_publication(
        self,
        requests: tuple[ArtifactWriteRequest | ArtifactStreamWriteRequest, ...],
        preflight: _PublicationPreflight,
    ) -> tuple[ArtifactWriteResult, ...] | None:
        """Authenticate an exact committed batch without creating staged files.

        An undeclared stream identity can use an existing complete roster only
        as a candidate; its actual request chunks must still match every byte.
        Missing commits continue through the original interruption protocol.
        """
        publication = preflight.publication
        identities = preflight.identities
        commit_payload = preflight.commit_payload
        if any(isinstance(request, ArtifactStreamWriteRequest) and request.expected_size_bytes is None
               for request in requests):
            first_sidecar = self.root.resolve(requests[0].relative_path + ".manifest.json", for_write=True)
            if not first_sidecar.exists():
                return None
            try:
                first = decode_artifact_sidecar(read_bounded_bytes(
                    first_sidecar, maximum_bytes=self.custody_limits.manifest_bytes,
                ), maximum_bytes=self.custody_limits.manifest_bytes)
                if type(first) is ArtifactManifestReference:
                    if not self.root.resolve(first.commit_marker_relative_path, for_write=False).exists():
                        return None
                    first = resolve_artifact_manifest_reference(self, first)
            except (OSError, BoundedFileIOError) as error:
                raise ArtifactIdentityConflict("existing publication manifest is invalid") from error
            except ValueError:
                # An unfinished first sidecar cannot identify an unpinned
                # stream's committed batch. Recompute its actual identity via
                # staging; the existing publication protocol checks the exact
                # intent and rejects committed corruption before any repair.
                return None
            publication = first.publication
            if (publication is None or publication.publication_scope != preflight.publication.publication_scope
                    or {member.relative_path for member in publication.members}
                    != {request.relative_path for request in requests}):
                return None
            members = {member.relative_path: member for member in publication.members}
            actual = []
            for request in requests:
                member = members[request.relative_path]
                size = (len(request.payload) if isinstance(request, ArtifactWriteRequest)
                        else request.expected_size_bytes if request.expected_size_bytes is not None else member.size_bytes)
                digest = (_sha256(request.payload) if isinstance(request, ArtifactWriteRequest)
                          else request.expected_physical_sha256 or member.physical_sha256)
                if isinstance(request, ArtifactStreamWriteRequest) and size > request.maximum_bytes:
                    raise ArtifactIdentityConflict("committed artifact exceeds its requested stream bound")
                logical, materialization, _manifest, _payload = self._prepare_identity(
                    request, physical_sha256=digest, size_bytes=size,
                )
                actual.append((logical, materialization))
            identities = tuple(actual)
            if tuple(sorted((artifact_publication_member(*pair) for pair in identities),
                            key=lambda member: member.materialization_id)) != publication.members:
                return None
            commit_payload = ArtifactPublicationCommit(
                publication.publication_batch_id, publication.publication_scope, publication.members,
            ).canonical_bytes()
        commit_path = self.root.resolve(publication.commit_marker_relative_path, for_write=True)
        if not commit_path.exists():
            return None
        if (len(commit_payload) != publication.commit_marker_size_bytes
                or _sha256(commit_payload) != publication.commit_marker_sha256
                or self.custody_limits.exceeds("publication_marker_bytes", len(commit_payload))):
            raise ArtifactIdentityConflict("artifact publication binding differs from its commit")
        intent_path = self.root.resolve(artifact_publication_intent_relative_path(
            publication.publication_scope, publication.publication_batch_id,
        ), for_write=True)
        paths = tuple((self.root.resolve(request.relative_path, for_write=True,
                         operation_minimum_free_bytes=request.minimum_free_bytes),
                       self.root.resolve(request.relative_path + ".manifest.json", for_write=True,
                         operation_minimum_free_bytes=request.minimum_free_bytes)) for request in requests)
        snapshots: dict[Path, _VerificationSnapshot] = {}
        results = []
        try:
            with ExitStack() as locks:
                locks.enter_context(self._publication_batch_lock(commit_path))
                for artifact_path, sidecar_path in sorted(paths, key=lambda pair: str(pair[0])):
                    locks.enter_context(self._pair_lock(artifact_path, sidecar_path))
                if not commit_path.exists():
                    return None
                self._track_verification_snapshot(commit_path, snapshots,
                    expected_sha256=publication.commit_marker_sha256, maximum_bytes=len(commit_payload))
                if not self._file_equals(commit_path, commit_payload):
                    raise ArtifactIdentityConflict("immutable publication commit identity already exists")
                intent = None
                if intent_path.exists():
                    intent = self._read_publication_intent(intent_path)
                    if (intent.publication_batch_id != publication.publication_batch_id
                            or intent.publication_scope != publication.publication_scope
                            or intent.members != publication.members):
                        raise ArtifactIdentityConflict("publication intent belongs to another exact batch")
                for request, (logical, materialization), (artifact_path, sidecar_path) in zip(
                        requests, identities, paths, strict=True):
                    self._track_verification_snapshot(artifact_path, snapshots,
                        expected_sha256=materialization.physical_sha256, maximum_bytes=materialization.size_bytes)
                    self._track_verification_snapshot(sidecar_path, snapshots,
                        maximum_bytes=self.custody_limits.manifest_bytes)
                    manifest = ArtifactManifest(logical, materialization, publication)
                    payload = read_bounded_bytes(sidecar_path, maximum_bytes=self.custody_limits.manifest_bytes)
                    try:
                        persisted = decode_artifact_sidecar(payload, maximum_bytes=self.custody_limits.manifest_bytes,
                            publication=publication)
                    except ValueError as error:
                        raise ArtifactIdentityConflict("committed artifact publication is incomplete") from error
                    if persisted != manifest:
                        raise ArtifactIdentityConflict("committed artifact publication is incomplete")
                    self._verify_manifest_snapshot(manifest)
                    if isinstance(request, ArtifactWriteRequest):
                        self.validators.validate(request, custody_limits=self.custody_limits)
                        if not self._file_equals(artifact_path, request.payload):
                            raise ArtifactIdentityConflict("requested payload differs from its committed bytes")
                    else:
                        self._require_replayed_stream(request, materialization, artifact_path)
                    results.append(ArtifactWriteResult(logical, materialization,
                        self._manifest_materialization(logical_artifact_id=logical.logical_artifact_id,
                            relative_path=request.relative_path + ".manifest.json", payload=payload), False))
                self._require_verification_snapshot_paths(snapshots,
                    reason="artifact batch changed during replay verification")
                if intent is not None:
                    self._remove_publication_intent(intent_path)
        except (OSError, BoundedFileIOError) as error:
            raise ArtifactIdentityConflict("committed artifact publication is incomplete") from error
        return tuple(results)

    @staticmethod
    def _require_replayed_stream(request: ArtifactStreamWriteRequest,
                                 materialization: ArtifactMaterialization, path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size != materialization.size_bytes:
                raise ArtifactIdentityConflict("committed replay payload has an incompatible size or type")
            size = 0
            digest = hashlib.sha256()
            for chunk in request.chunks:
                if not isinstance(chunk, bytes) or len(chunk) > request.maximum_chunk_bytes:
                    raise ArtifactIdentityConflict("artifact stream chunks violate their byte contract")
                size += len(chunk)
                if size > request.maximum_bytes:
                    raise ArtifactIdentityConflict("artifact stream exceeds its total byte limit")
                digest.update(chunk)
                offset = 0
                while offset < len(chunk):
                    observed = os.read(descriptor, min(STREAM_CHUNK_BYTES, len(chunk) - offset))
                    if not observed or observed != chunk[offset:offset + len(observed)]:
                        raise ArtifactIdentityConflict("requested stream differs from its committed bytes")
                    offset += len(observed)
            if (size != materialization.size_bytes or digest.hexdigest() != materialization.physical_sha256
                    or os.read(descriptor, 1)):
                raise ArtifactIdentityConflict("requested stream differs from its committed identity")
            if (ExternalArtifactPlane._descriptor_identity(before)
                    != ExternalArtifactPlane._descriptor_identity(os.fstat(descriptor))):
                raise ArtifactIdentityConflict("committed replay payload changed during comparison")
        finally:
            os.close(descriptor)

    def _validate_publication_request(self, request: ArtifactWriteRequest | ArtifactStreamWriteRequest) -> None:
        if request.read_only_source_input:
            raise ArtifactIdentityConflict("historical artifact contracts are read-only")
        self._require_registered_semantics(request.logical_artifact_id, request.semantic_validation)
        if request.compression != "none" or request.partition_selector is not None:
            raise ArtifactIdentityConflict("compressed or partitioned artifacts require an equivalence proof contract")
        if isinstance(request, ArtifactWriteRequest) and self.custody_limits.exceeds("in_memory_payload_bytes", len(request.payload)):
            raise ArtifactIdentityConflict("in-memory artifact payload exceeds its convenience limit; use write_stream")

    def _bind_staged_batch(
        self,
        staged: tuple[_StagedArtifactPublication, ...],
        *,
        publication_scope: ArtifactPublicationScope,
        token: str,
        compact_manifests: bool = False,
    ) -> _StagedArtifactBatch:
        members = tuple(
            sorted(
                (
                    artifact_publication_member(item.logical, item.materialization)
                    for item in staged
                ),
                key=lambda value: value.materialization_id,
            )
        )
        publication_batch_id = artifact_publication_batch_id(publication_scope, members)
        commit = ArtifactPublicationCommit(
            publication_batch_id=publication_batch_id,
            publication_scope=publication_scope,
            members=members,
        )
        commit_payload = commit.canonical_bytes()
        if self.custody_limits.exceeds("publication_marker_bytes", len(commit_payload)):
            raise ArtifactIdentityConflict("artifact publication marker exceeds its byte bound")
        commit_relative_path = artifact_publication_commit_relative_path(
            publication_scope,
            publication_batch_id,
        )
        publication = ArtifactPublicationBinding(
            publication_batch_id=publication_batch_id,
            publication_scope=publication_scope,
            commit_marker_relative_path=commit_relative_path,
            commit_marker_sha256=_sha256(commit_payload),
            commit_marker_size_bytes=len(commit_payload),
            members=members,
        )
        rebound: list[_StagedArtifactPublication] = []
        for item in staged:
            manifest_payload = self._staged_manifest_payload(item, publication,
                compact_manifests=compact_manifests)
            if self.custody_limits.exceeds("manifest_bytes", len(manifest_payload)):
                raise ArtifactIdentityConflict("artifact manifest exceeds its byte bound")
            manifest_materialization = self._manifest_materialization(
                logical_artifact_id=item.logical.logical_artifact_id,
                relative_path=f"{item.materialization.relative_path}.manifest.json",
                payload=manifest_payload,
            )
            self._write_staged_bytes(item.staged_sidecar_path, manifest_payload)
            rebound.append(
                _StagedArtifactPublication(
                    logical=item.logical,
                    materialization=item.materialization,
                    manifest_materialization=manifest_materialization,
                    artifact_path=item.artifact_path,
                    sidecar_path=item.sidecar_path,
                    staged_artifact_path=item.staged_artifact_path,
                    staged_sidecar_path=item.staged_sidecar_path,
                )
            )
        commit_path = self.root.resolve(
            commit_relative_path,
            for_write=True,
        )
        intent_path = self.root.resolve(
            artifact_publication_intent_relative_path(
                publication_scope,
                publication_batch_id,
            ),
            for_write=True,
        )
        if {commit_path, intent_path} & {
            path for item in rebound for path in (item.artifact_path, item.sidecar_path)
        }:
            raise ArtifactIdentityConflict(
                "artifact publication control path overlaps a batch member"
            )
        commit_path.parent.mkdir(parents=True, exist_ok=True)
        staged_commit_path = self._staging_path(commit_path, token, "partial")
        self._write_staged_bytes(staged_commit_path, commit_payload)
        return _StagedArtifactBatch(
            members=tuple(rebound),
            publication=publication,
            commit_payload=commit_payload,
            commit_path=commit_path,
            intent_path=intent_path,
            staged_commit_path=staged_commit_path,
        )

    def _staged_manifest_payload(self, item: _StagedArtifactPublication,
            publication: ArtifactPublicationBinding, *, compact_manifests: bool) -> bytes:
        """Retain existing transport bytes, including an owned interrupted prefix."""
        from .task_receipts import encode_artifact_manifest

        selected = (encode_artifact_manifest_reference(item.logical, item.materialization, publication)
            if compact_manifests else encode_artifact_manifest(item.logical, item.materialization, publication))
        if not item.sidecar_path.exists():
            return selected
        raw = read_bounded_bytes(item.sidecar_path, maximum_bytes=self.custody_limits.manifest_bytes)
        try:
            persisted = decode_artifact_sidecar(raw, maximum_bytes=self.custody_limits.manifest_bytes,
                publication=publication)
        except ValueError as error:
            if selected.startswith(raw):
                return selected
            alternate = (encode_artifact_manifest(item.logical, item.materialization, publication)
                if compact_manifests else encode_artifact_manifest_reference(item.logical, item.materialization, publication))
            if alternate.startswith(raw):
                return alternate
            raise ArtifactIdentityConflict("existing sidecar differs from its immutable publication") from error
        if persisted != ArtifactManifest(item.logical, item.materialization, publication):
            raise ArtifactIdentityConflict("existing sidecar differs from its immutable publication")
        return raw

    def _stage_publication(
        self,
        request: ArtifactWriteRequest | ArtifactStreamWriteRequest,
        *,
        token: str,
        index: int,
    ) -> _StagedArtifactPublication:
        self._validate_publication_request(request)
        artifact_path = self.root.resolve(
            request.relative_path,
            for_write=True,
            operation_minimum_free_bytes=request.minimum_free_bytes,
        )
        sidecar_path = self.root.resolve(
            f"{request.relative_path}.manifest.json",
            for_write=True,
            operation_minimum_free_bytes=request.minimum_free_bytes,
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        staged_artifact_path = self._staging_path(artifact_path, token, f"{index:04d}.batch.partial")
        staged_sidecar_path = self._staging_path(sidecar_path, token, f"{index:04d}.batch.partial")
        try:
            if isinstance(request, ArtifactWriteRequest):
                from .publication_validation import capture_payload_validation
                with capture_payload_validation(self, request) as proof:
                    (
                        logical,
                        materialization,
                        manifest_materialization,
                        manifest_payload,
                    ) = self._prepare(request)
                    self._write_staged_bytes(staged_artifact_path, request.payload)
                    observed_size, observed_sha256 = self._stream_identity(
                        staged_artifact_path,
                        maximum_bytes=len(request.payload),
                    )
                    if (
                        observed_size != materialization.size_bytes
                        or observed_sha256 != materialization.physical_sha256
                    ):
                        raise ArtifactIdentityConflict("staged artifact identity changed")
                    if not proof.require_same_bytes_and_policy(observed_size, observed_sha256):
                        self.validators.validate_file(staged_artifact_path, request, custody_limits=self.custody_limits)
            else:
                size_bytes, physical_sha256 = self._write_staged_stream(
                    staged_artifact_path,
                    request,
                )
                if request.expected_size_bytes is not None and (
                    size_bytes != request.expected_size_bytes
                    or physical_sha256 != request.expected_physical_sha256
                ):
                    raise ArtifactIdentityConflict(
                        "artifact stream differs from its expected physical identity"
                    )
                self.validators.validate_file(staged_artifact_path, request, custody_limits=self.custody_limits)
                (
                    logical,
                    materialization,
                    manifest_materialization,
                    manifest_payload,
                ) = self._prepare_identity(
                    request,
                    physical_sha256=physical_sha256,
                    size_bytes=size_bytes,
                )
            # The sidecar gains its immutable sibling-set binding only after
            # every payload is staged. Write that final sidecar once in
            # _bind_staged_batch, before any destination is published.
            return _StagedArtifactPublication(
                logical=logical,
                materialization=materialization,
                manifest_materialization=manifest_materialization,
                artifact_path=artifact_path,
                sidecar_path=sidecar_path,
                staged_artifact_path=staged_artifact_path,
                staged_sidecar_path=staged_sidecar_path,
            )
        except BaseException:
            self._unlink_if_present(staged_artifact_path)
            self._unlink_if_present(staged_sidecar_path)
            raise

    @staticmethod
    def _write_staged_bytes(
        path: Path, payload: bytes, *, retain_on_error: bool = False,
    ) -> None:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            if not retain_on_error:
                ExternalArtifactPlane._unlink_if_present(path)
            raise

    @staticmethod
    def _write_staged_stream(
        path: Path,
        request: ArtifactStreamWriteRequest,
    ) -> tuple[int, str]:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        digest = hashlib.sha256()
        size_bytes = 0
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                for chunk in request.chunks:
                    if not isinstance(chunk, bytes):
                        raise ArtifactIdentityConflict(
                            "artifact stream chunks must be immutable bytes"
                        )
                    if len(chunk) > request.maximum_chunk_bytes:
                        raise ArtifactIdentityConflict(
                            "artifact stream chunk exceeds its byte limit"
                        )
                    size_bytes += len(chunk)
                    if size_bytes > request.maximum_bytes:
                        raise ArtifactIdentityConflict(
                            "artifact stream exceeds its total byte limit"
                        )
                    handle.write(chunk)
                    digest.update(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            ExternalArtifactPlane._unlink_if_present(path)
            raise
        return size_bytes, digest.hexdigest()

    def _publish_staged_batch(
        self,
        batch: _StagedArtifactBatch,
    ) -> tuple[ArtifactWriteResult, ...]:
        staged = batch.members
        self._require_publication_descriptor_capacity(len(staged))
        created_flags: list[bool] = []
        lock_order = tuple(sorted(staged, key=lambda item: str(item.artifact_path)))
        commit_published = False
        intent: ArtifactPublicationIntent | None = None
        owned_paths_validated = False
        already_committed = False
        absolute_paths = {
            relative_path: path
            for item in staged
            for relative_path, path in (
                (item.materialization.relative_path, item.artifact_path),
                (item.manifest_materialization.relative_path, item.sidecar_path),
            )
        }
        component_sources = {
            relative_path: (destination, source, maximum_bytes)
            for item in staged
            for relative_path, destination, source, maximum_bytes in (
                (
                    item.materialization.relative_path,
                    item.artifact_path,
                    item.staged_artifact_path,
                    item.materialization.size_bytes,
                ),
                (
                    item.manifest_materialization.relative_path,
                    item.sidecar_path,
                    item.staged_sidecar_path,
                    item.manifest_materialization.size_bytes,
                ),
            )
        }
        component_identities = {
            value.relative_path: (value.size_bytes, value.physical_sha256)
            for item in staged
            for value in (item.materialization, item.manifest_materialization)
        }
        try:
            with ExitStack() as locks:
                locks.enter_context(self._publication_batch_lock(batch.commit_path))
                for item in lock_order:
                    locks.enter_context(self._pair_lock(item.artifact_path, item.sidecar_path))
                commit_exists = batch.commit_path.exists()
                if commit_exists and not self._file_equals(
                    batch.commit_path,
                    batch.commit_payload,
                ):
                    raise ArtifactIdentityConflict(
                        "immutable publication commit identity already exists"
                    )
                if batch.intent_path.exists():
                    intent = self._read_publication_intent(batch.intent_path)
                    if (
                        intent.publication_batch_id != batch.publication.publication_batch_id
                        or intent.members != batch.publication.members
                    ):
                        raise ArtifactIdentityConflict(
                            "publication intent belongs to another exact batch"
                        )

                if commit_exists:
                    for item in staged:
                        if not item.artifact_path.is_file() or not item.sidecar_path.is_file():
                            raise ArtifactIdentityConflict(
                                "committed artifact publication is incomplete"
                            )
                        try:
                            artifact_exact = self._component_is_exact_or_prefix(
                                item.artifact_path,
                                item.staged_artifact_path,
                                maximum_bytes=item.materialization.size_bytes,
                            )
                            sidecar_exact = self._component_is_exact_or_prefix(
                                item.sidecar_path,
                                item.staged_sidecar_path,
                                maximum_bytes=item.manifest_materialization.size_bytes,
                            )
                        except ArtifactIdentityConflict as error:
                            raise ArtifactIdentityConflict(
                                "committed artifact publication is incomplete"
                            ) from error
                        if not artifact_exact or not sidecar_exact:
                            raise ArtifactIdentityConflict(
                                "committed artifact publication is incomplete"
                            )
                        created_flags.append(False)
                    already_committed = True
                    if intent is not None:
                        self._remove_publication_intent(batch.intent_path)
                else:
                    components = tuple(
                        (
                            relative_path,
                            destination,
                            source,
                            maximum_bytes,
                        )
                        for item in staged
                        for relative_path, destination, source, maximum_bytes in (
                            (
                                item.materialization.relative_path,
                                item.artifact_path,
                                item.staged_artifact_path,
                                item.materialization.size_bytes,
                            ),
                            (
                                item.manifest_materialization.relative_path,
                                item.sidecar_path,
                                item.staged_sidecar_path,
                                item.manifest_materialization.size_bytes,
                            ),
                        )
                    )
                    if intent is None:
                        absent_relative_paths: list[str] = []
                        exact_paths: set[str] = set()
                        for relative_path, destination, source, maximum_bytes in components:
                            if not destination.exists():
                                absent_relative_paths.append(relative_path)
                                continue
                            try:
                                exact = self._component_is_exact_or_prefix(
                                    destination,
                                    source,
                                    maximum_bytes=maximum_bytes,
                                )
                            except ArtifactIdentityConflict as error:
                                raise ArtifactIdentityConflict(
                                    "immutable artifact identity already exists"
                                ) from error
                            if not exact:
                                raise ArtifactIdentityConflict(
                                    "immutable artifact identity already exists"
                                )
                            exact_paths.add(relative_path)
                        for item in staged:
                            if item.sidecar_path.exists() and not item.artifact_path.exists():
                                raise ArtifactIdentityConflict(
                                    "artifact publication has a manifest-first partial"
                                )
                            created_flags.append(
                                item.materialization.relative_path not in exact_paths
                                or item.manifest_materialization.relative_path not in exact_paths
                            )
                        intent = ArtifactPublicationIntent(
                            publication_batch_id=(batch.publication.publication_batch_id),
                            publication_scope=batch.publication.publication_scope,
                            members=batch.publication.members,
                            absent_relative_paths=tuple(sorted(absent_relative_paths)),
                        )
                        self._write_publication_intent(batch.intent_path, intent)
                        owned_paths_validated = True
                    else:
                        owned = set(intent.absent_relative_paths)
                        exact_paths = set()
                        prefix_paths: list[Path] = []
                        for relative_path, destination, source, maximum_bytes in components:
                            if not destination.exists():
                                if relative_path not in owned:
                                    raise ArtifactIdentityConflict(
                                        "pre-existing publication member disappeared"
                                    )
                                continue
                            exact = self._component_is_exact_or_prefix(
                                destination,
                                source,
                                maximum_bytes=maximum_bytes,
                            )
                            if relative_path not in owned:
                                if not exact:
                                    raise ArtifactIdentityConflict(
                                        "pre-existing publication member changed"
                                    )
                                exact_paths.add(relative_path)
                            elif exact:
                                exact_paths.add(relative_path)
                            else:
                                prefix_paths.append(destination)
                        for item in staged:
                            created_flags.append(
                                item.materialization.relative_path not in exact_paths
                                or item.manifest_materialization.relative_path not in exact_paths
                            )
                        owned_paths_validated = True
                        prefix_parents: set[Path] = set()
                        for path in prefix_paths:
                            self._unlink_if_present(path)
                            prefix_parents.add(path.parent)
                        for parent in sorted(prefix_parents, key=str):
                            self._fsync_directory(parent)

                    owned_relative_paths = set(intent.absent_relative_paths)
                    for relative_path, destination, source, maximum_bytes in components:
                        if destination.exists():
                            continue
                        if relative_path not in owned_relative_paths:
                            raise ArtifactIdentityConflict(
                                "pre-existing publication member disappeared"
                            )
                        identity = component_identities[relative_path]
                        self._require_component_identity(source, identity)
                        # Both staged files have already been fsynced. Exclusive
                        # rename keeps the final path all-or-absent without a
                        # second write, fsync and write-mode close of each file.
                        self._move_file_once(source, destination)
                        self._require_component_identity(destination, identity)
                    parent_paths = {
                        path.parent
                        for item in staged
                        for path in (item.artifact_path, item.sidecar_path)
                    }
                    for parent in sorted(parent_paths, key=str):
                        self._fsync_directory(parent)
                    try:
                        self._rename_noreplace(
                            batch.staged_commit_path,
                            batch.commit_path,
                        )
                    except FileExistsError as error:
                        if not self._file_equals(batch.commit_path, batch.commit_payload):
                            raise ArtifactIdentityConflict(
                                "immutable publication commit identity raced"
                            ) from error
                    commit_published = True
                    self._fsync_directory(batch.commit_path.parent)
                    self._remove_publication_intent(batch.intent_path)
        except BaseException:
            if not commit_published and owned_paths_validated and intent is not None:
                rollback_parents: set[Path] = set()
                for relative_path in reversed(intent.absent_relative_paths):
                    path = absolute_paths[relative_path]
                    if path.exists():
                        _destination, source, maximum_bytes = component_sources[relative_path]
                        try:
                            if source.exists():
                                self._component_is_exact_or_prefix(
                                    path,
                                    source,
                                    maximum_bytes=maximum_bytes,
                                )
                            else:
                                # A completed rename consumed its staging path,
                                # including when a later operation raised. Delete
                                # only the exact content frozen before publication.
                                self._require_component_identity(
                                    path, component_identities[relative_path]
                                )
                        except ArtifactIdentityConflict:
                            # A noncooperating writer won the path with other
                            # bytes; preserve that evidence instead of deleting it.
                            continue
                        rollback_parents.add(path.parent)
                        self._unlink_if_present(path)
                for parent in sorted(rollback_parents, key=str):
                    self._fsync_directory(parent)
                self._remove_publication_intent(batch.intent_path)
            raise
        if already_committed:
            commit_published = True
        return tuple(
            ArtifactWriteResult(
                logical=item.logical,
                materialization=item.materialization,
                manifest_materialization=item.manifest_materialization,
                created=created,
            )
            for item, created in zip(staged, created_flags, strict=True)
        )

    @staticmethod
    def _component_is_exact_or_prefix(
        candidate: Path,
        expected: Path,
        *,
        maximum_bytes: int,
    ) -> bool:
        """Return exactness after proving candidate is a stable expected prefix."""

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        candidate_descriptor: int | None = None
        expected_descriptor: int | None = None
        try:
            candidate_descriptor = os.open(candidate, flags)
            expected_descriptor = os.open(expected, flags)
            candidate_before = os.fstat(candidate_descriptor)
            expected_before = os.fstat(expected_descriptor)
            if (
                not stat.S_ISREG(candidate_before.st_mode)
                or not stat.S_ISREG(expected_before.st_mode)
                or expected_before.st_size != maximum_bytes
                or candidate_before.st_size > maximum_bytes
            ):
                raise ArtifactIdentityConflict(
                    "batch-owned partial differs from its expected prefix"
                )
            remaining = candidate_before.st_size
            while remaining:
                candidate_chunk = os.read(
                    candidate_descriptor,
                    min(STREAM_CHUNK_BYTES, remaining),
                )
                expected_chunk = os.read(expected_descriptor, len(candidate_chunk))
                if not candidate_chunk or candidate_chunk != expected_chunk:
                    raise ArtifactIdentityConflict(
                        "batch-owned partial differs from its expected prefix"
                    )
                remaining -= len(candidate_chunk)
            candidate_after = os.fstat(candidate_descriptor)
            expected_after = os.fstat(expected_descriptor)
            candidate_identity = (
                candidate_before.st_dev,
                candidate_before.st_ino,
                candidate_before.st_size,
                candidate_before.st_mtime_ns,
                candidate_before.st_ctime_ns,
            )
            expected_identity = (
                expected_before.st_dev,
                expected_before.st_ino,
                expected_before.st_size,
                expected_before.st_mtime_ns,
                expected_before.st_ctime_ns,
            )
            if candidate_identity != (
                candidate_after.st_dev,
                candidate_after.st_ino,
                candidate_after.st_size,
                candidate_after.st_mtime_ns,
                candidate_after.st_ctime_ns,
            ) or expected_identity != (
                expected_after.st_dev,
                expected_after.st_ino,
                expected_after.st_size,
                expected_after.st_mtime_ns,
                expected_after.st_ctime_ns,
            ):
                raise ArtifactIdentityConflict(
                    "publication component changed during prefix verification"
                )
            return candidate_before.st_size == maximum_bytes
        except OSError as error:
            raise ArtifactIdentityConflict(
                "publication component cannot be verified as a stable prefix"
            ) from error
        finally:
            if expected_descriptor is not None:
                os.close(expected_descriptor)
            if candidate_descriptor is not None:
                os.close(candidate_descriptor)

    def _read_publication_intent(self, path: Path) -> ArtifactPublicationIntent:
        try:
            payload = read_bounded_bytes(
                path,
                maximum_bytes=self.custody_limits.publication_intent_bytes,
            )
            from .task_receipts import decode_artifact_publication_intent

            return decode_artifact_publication_intent(payload, maximum_bytes=self.custody_limits.publication_intent_bytes)
        except (BoundedFileIOError, OSError, ValueError) as error:
            raise ArtifactIdentityConflict("artifact publication intent is invalid") from error

    def _write_publication_intent(
        self,
        path: Path,
        intent: ArtifactPublicationIntent,
    ) -> None:
        payload = intent.canonical_bytes()
        if self.custody_limits.exceeds("publication_intent_bytes", len(payload)):
            raise ArtifactIdentityConflict("artifact publication intent exceeds its byte bound")
        token = hashlib.sha256(
            f"{os.getpid()}\0{threading.get_ident()}\0{time.time_ns()}".encode()
        ).hexdigest()[:24]
        staged_path = self._staging_path(path, token, "partial")
        try:
            ExternalArtifactPlane._write_staged_bytes(staged_path, payload)
            try:
                ExternalArtifactPlane._rename_noreplace(staged_path, path)
            except FileExistsError as error:
                raise ArtifactIdentityConflict(
                    "artifact publication intent already exists"
                ) from error
            ExternalArtifactPlane._fsync_directory(path.parent)
        finally:
            ExternalArtifactPlane._unlink_if_present(staged_path)

    @staticmethod
    def _remove_publication_intent(path: Path) -> None:
        if path.exists():
            path.unlink()
            ExternalArtifactPlane._fsync_directory(path.parent)

    @staticmethod
    def _rename_noreplace(source: Path, destination: Path) -> None:
        """Atomically publish a staged control file without replacement.

        Linux ``renameat2(RENAME_NOREPLACE)`` is supported by the production
        vfat mount through the VFS.  Failing closed is safer than falling back
        to a check-then-replace sequence on an unsupported platform.
        """

        try:
            rename_noreplace(source, destination)
        except FileExistsError:
            raise
        except OSError as error:
            raise ArtifactIdentityConflict(
                "exclusive atomic control publication failed"
            ) from error

    @staticmethod
    def _require_component_identity(path: Path, identity: tuple[int, str]) -> None:
        try:
            observed = ExternalArtifactPlane._stream_identity(path, maximum_bytes=identity[0])
        except OSError as error:
            raise ArtifactIdentityConflict(
                "publication component identity is unavailable"
            ) from error
        if observed != identity:
            raise ArtifactIdentityConflict("artifact identity changed during batch publication")

    @staticmethod
    def _move_file_once(source: Path, destination: Path) -> None:
        ExternalArtifactPlane._rename_noreplace(source, destination)

    @staticmethod
    def _file_equals(path: Path, expected: bytes) -> bool:
        try:
            return file_matches_bytes(path, expected)
        except (BoundedFileIOError, OSError):
            return False

    @staticmethod
    def _unlink_if_present(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def open(
        self,
        value: VerifiedArtifactInput,
        *,
        binding: WorkerInputBinding | None = None,
        maximum_bytes: int | None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> WorkerInputPort:
        return self.open_many(
            (value,),
            bindings=(
                binding or WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL),
            ),
            maximum_bytes=maximum_bytes,
            **({"before_member": before_member} if before_member is not None else {}),
        )[0]

    def open_many(
        self,
        values: tuple[VerifiedArtifactInput, ...],
        *,
        bindings: tuple[WorkerInputBinding, ...],
        maximum_bytes: int | None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> tuple[WorkerInputPort, ...]:
        """Authenticate each batch once and seal the bytes actually given to workers."""
        requested = _worker_input_requests(values, bindings, maximum_bytes)
        with force_full_verification():
            ports = self._verify_manifests(
                tuple(
                    ArtifactManifest(logical=value.logical, materialization=value.materialization)
                    for value in values
                ),
                requested,
                **({"before_member": before_member} if before_member is not None else {}),
            )
        return tuple(ports[value.materialization.relative_path] for value in values)

    def recover_partial(self, request: ArtifactWriteRequest) -> ArtifactWriteResult:
        """Complete an exact uncommitted partial through the batch protocol."""

        return self.write(request)

    def _prepare(
        self,
        request: ArtifactWriteRequest,
    ) -> tuple[
        LogicalArtifactIdentity,
        ArtifactMaterialization,
        ArtifactMaterialization,
        bytes,
    ]:
        if request.read_only_source_input:
            raise ArtifactIdentityConflict("historical artifact contracts are read-only")
        if request.compression != "none" or request.partition_selector is not None:
            raise ArtifactIdentityConflict(
                "compressed or partitioned artifacts require an equivalence proof contract"
            )
        physical_sha256 = _sha256(request.payload)
        if (
            request.logical_content_sha256 is not None
            and request.logical_content_sha256 != physical_sha256
        ):
            raise ArtifactIdentityConflict(
                "logical content identity lacks a verified equivalence proof"
            )
        self.validators.validate(request, custody_limits=self.custody_limits)
        from .publication_validation import remember_payload_validation
        remember_payload_validation(self, request, size=len(request.payload), digest=physical_sha256)
        return self._prepare_identity(
            request,
            physical_sha256=physical_sha256,
            size_bytes=len(request.payload),
        )

    def _prepare_identity(
        self,
        request: ArtifactWriteRequest | ArtifactStreamWriteRequest,
        *,
        physical_sha256: str,
        size_bytes: int,
    ) -> tuple[
        LogicalArtifactIdentity,
        ArtifactMaterialization,
        ArtifactMaterialization,
        bytes,
    ]:
        if (
            request.logical_content_sha256 is not None
            and request.logical_content_sha256 != physical_sha256
        ):
            raise ArtifactIdentityConflict(
                "logical content identity lacks a verified equivalence proof"
            )
        logical_sha256 = physical_sha256
        logical = LogicalArtifactIdentity(
            logical_artifact_id=request.logical_artifact_id,
            content_sha256=logical_sha256,
            payload_schema=request.payload_schema,
            profile=request.profile,
            media_type=request.media_type,
            visibility_ceiling=request.visibility_ceiling,
            parent_visibility_ceilings=request.parent_visibility_ceilings,
            outcome_access=request.outcome_access,
            generic_validation=self.validators.generic_validation(
                profile=request.profile,
                payload_schema=request.payload_schema,
            ),
            lineage_parents=request.lineage_parents,
            semantic_validation=request.semantic_validation,
        )
        materialization = ArtifactMaterialization(
            materialization_id=_materialization_id(
                request.logical_artifact_id,
                request.relative_path,
                physical_sha256,
            ),
            logical_artifact_id=request.logical_artifact_id,
            storage_root_id=self.root.contract.storage_root_id,
            relative_path=request.relative_path,
            physical_sha256=physical_sha256,
            size_bytes=size_bytes,
            compression=request.compression,
            partition_selector=request.partition_selector,
        )
        manifest_payload = canonical_json_bytes(
            ArtifactManifest(logical=logical, materialization=materialization)
        )
        manifest_path = f"{request.relative_path}.manifest.json"
        manifest_materialization = self._manifest_materialization(
            logical_artifact_id=request.logical_artifact_id,
            relative_path=manifest_path,
            payload=manifest_payload,
        )
        return (
            logical,
            materialization,
            manifest_materialization,
            manifest_payload,
        )

    def _manifest_materialization(
        self,
        *,
        logical_artifact_id: str,
        relative_path: str,
        payload: bytes,
    ) -> ArtifactMaterialization:
        manifest_logical_id = f"{logical_artifact_id}-manifest"
        physical_sha256 = _sha256(payload)
        return ArtifactMaterialization(
            materialization_id=_materialization_id(
                manifest_logical_id,
                relative_path,
                physical_sha256,
            ),
            logical_artifact_id=manifest_logical_id,
            storage_root_id=self.root.contract.storage_root_id,
            relative_path=relative_path,
            physical_sha256=physical_sha256,
            size_bytes=len(payload),
            compression="none",
        )

    def verify(self, materialization: ArtifactMaterialization) -> None:
        if materialization.storage_root_id != self.root.contract.storage_root_id:
            raise ArtifactIdentityConflict("artifact belongs to another storage root")
        verification = getattr(self, "_read_verification", None)
        if verification is not None and (verification.context_preflights or verification.member_preflights):
            path = self.root.resolve(materialization.relative_path, for_write=False)
            if verification.context_preflights or verification.member_preflights.get(path):
                # A guarded operation cannot use the raw-materialization shortcut
                # to hash a protected body without its exact publication callback.
                manifest = self.read_manifest(materialization.relative_path)
                if manifest.materialization != materialization:
                    raise ArtifactIdentityConflict("guarded raw verification changes its exact member")
                self.verify_manifest(manifest)
                return
        path = self.root.resolve(materialization.relative_path, for_write=False)
        if not path.is_file():
            raise ArtifactIdentityConflict("artifact path is unavailable")
        size_bytes, physical_sha256 = self._stream_identity(
            path,
            maximum_bytes=materialization.size_bytes,
        )
        if (
            size_bytes != materialization.size_bytes
            or physical_sha256 != materialization.physical_sha256
        ):
            raise ArtifactIdentityConflict("artifact bytes differ from their identity")

    def verify_manifest(self, manifest: ArtifactManifest, *,
            before_member: Callable[[ArtifactManifest], None] | None = None) -> None:
        self.verify_manifests((manifest,),
            **({"before_member": before_member} if before_member is not None else {}))

    def verify_manifests(self, manifests: tuple[ArtifactManifest, ...], *,
            before_member: Callable[[ArtifactManifest], None] | None = None) -> None:
        if self.custody_limits.exceeds("publication_members", len(manifests)):
            raise ArtifactIdentityConflict("artifact verification batch exceeds its bound")
        self._verify_manifests(manifests, {},
            **({"before_member": before_member} if before_member is not None else {}))

    def verify_manifest_members(
        self,
        manifest: ArtifactManifest,
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> _MemberValidationResult:
        """Consume one authenticated sibling set within its snapshot lifetime.

        Keys are exact materialization paths. The immutable mapping is useful
        only for this callback; it creates no reusable verification or authority
        token. Every invocation authenticates the complete publication afresh.
        """
        return self._consume_verified_manifest_members(manifest, validate_members=validate_members,
            **({"before_member": before_member} if before_member is not None else {}))

    def verify_manifests_members(
        self,
        manifests: tuple[ArtifactManifest, ...],
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> _MemberValidationResult:
        """Consume several complete publications under one before/after guard.

        The callback receives actual authenticated sibling metadata. This has
        the same custody lifetime as the singular API; it grants no authority
        and retains no verification result for another operation.
        """
        return self._consume_verified_manifests_members(manifests, validate_members=validate_members,
            **({"before_member": before_member} if before_member is not None else {}))

    def _consume_verified_manifest_members(
        self,
        manifest: ArtifactManifest,
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        snapshots: dict[Path, _VerificationSnapshot] | None = None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
    ) -> _MemberValidationResult:
        return self._consume_verified_manifests_members((manifest,),
            validate_members=validate_members, snapshots=snapshots,
            **({"before_member": before_member} if before_member is not None else {}),
            **({"member_preflights": member_preflights} if member_preflights is not None else {}))

    def _consume_verified_manifests_members(
        self,
        manifests: tuple[ArtifactManifest, ...],
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        snapshots: dict[Path, _VerificationSnapshot] | None = None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
        _borrow_read_context: bool = False,
    ) -> _MemberValidationResult:
        if not callable(validate_members):
            raise TypeError("artifact member validation requires a callable")
        if self.custody_limits.exceeds("publication_members", len(manifests)):
            raise ArtifactIdentityConflict("artifact verification batch exceeds its bound")
        result: _MemberValidationResult

        def consume(members: Mapping[str, ArtifactManifest]) -> None:
            nonlocal result
            result = validate_members(members)

        self._verify_manifests(manifests, {}, validate_members=consume, snapshots=snapshots,
            **({"before_member": before_member} if before_member is not None else {}),
            **({"member_preflights": member_preflights} if member_preflights is not None else {}),
            **({"_borrow_read_context": True} if _borrow_read_context else {}))
        return result

    def _verify_manifests(
        self, manifests, requested, *, validate_members=None, snapshots=None,
        before_member=None, member_preflights=None, _borrow_read_context=False,
    ):
        with _member_preflight_scopes(self, before_member=before_member, member_preflights=member_preflights):
            return self._verify_manifests_in_scope(manifests, requested, validate_members=validate_members,
                snapshots=snapshots, before_member=before_member, member_preflights=member_preflights,
                _borrow_read_context=_borrow_read_context)

    def _verify_manifests_in_scope(
        self,
        manifests: tuple[ArtifactManifest, ...],
        requested: dict[str, tuple[WorkerInputBinding, int]],
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], None] | None = None,
        snapshots: dict[Path, _VerificationSnapshot] | None = None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
        _borrow_read_context: bool = False,
    ) -> dict[str, WorkerInputPort]:
        """Verify each committed sibling set once within a stable read operation.

        Fresh closures authenticate physical bytes and semantics. Only the
        stock read-context owner can defer its internal whole-file rechecks to
        that context's mandatory final guard; current access stays eager.
        """

        before_member = self._operation_member_preflight(before_member)
        if _borrow_read_context:
            verification = getattr(self, "_read_verification", None)
            if (requested or verification is None or not verification.context_depth
                    or not _has_stock_manifest_reads(self)):
                raise ArtifactIdentityConflict("only a stock active read context may own the final byte guard")
            self.require_active_verification_scope()
        if before_member is not None and not callable(before_member):
            raise TypeError("artifact member preflight requires a callable")
        verified_batches: set[str] = set()
        snapshots = {} if snapshots is None else snapshots
        if member_preflights is None:
            verification = getattr(self, "_read_verification", None)
            member_preflights = (verification.member_preflights
                if verification is not None and (before_member is not None or verification.member_preflights) else {})
        members: dict[str, ArtifactManifest] | None = {} if validate_members is not None else None
        ports: dict[str, WorkerInputPort] = {}
        complete = False
        processed_members = 0
        progress_total = (len(manifests[0].publication.members)
            if len(manifests) == 1 and manifests[0].publication is not None else None)
        report_progress(phase="verify_artifact_members", done=0, total=progress_total)

        def require_snapshot() -> None:
            if _borrow_read_context:
                # Each new member was physically authenticated above. The
                # exact snapshots join the owning census before consumption.
                # Retain both live-access
                # boundaries without rehashing the new population twice.
                self.require_active_verification_scope()
                for path, identity in snapshots.items():
                    if verification.snapshots.setdefault(path, identity) != identity:
                        raise ArtifactIdentityConflict("artifact changed during its read context")
                    for original, guard in tuple(member_preflights.get(path, ())):
                        guard(original)
                return
            try:
                self._require_verification_snapshot_paths(snapshots,
                    reason="artifact batch changed during verification",
                    **({"member_preflights": member_preflights} if member_preflights else {}))
            except OSError as error:
                if member_preflights and isinstance(error, PermissionError):
                    raise
                raise ArtifactIdentityConflict("artifact batch snapshot became unavailable") from error

        try:
            try:
                from .parallel_verification import (
                    CanonicalValidationPool, ParallelValidationBatch, in_parallel_verification,
                )
                parallel = (self.maximum_parallel_verifications > 1 and not requested
                    and not in_parallel_verification.get() and _has_stock_manifest_reads(self)
                    and sum(row.materialization.size_bytes for row in manifests) >= 1024**2)
                batch_context = nullcontext(None)
                if parallel:
                    verification = getattr(self, '_read_verification', None)
                    pool = None
                    if verification is not None:
                        if verification.canonical_pool is None:
                            verification.canonical_pool = CanonicalValidationPool(self.maximum_parallel_verifications)
                        pool = verification.canonical_pool
                    batch_context = ParallelValidationBatch(
                        lambda sibling: self._verify_manifest_snapshot(sibling,
                            **({'member_preflights': member_preflights} if member_preflights else {}),
                            **({'_resolved_paths': resolved_paths} if resolved_paths is not None else {})),
                        workers=self.maximum_parallel_verifications, canonical_pool=pool)
                # The complete path census closes before a consumer receives
                # any result or worker port. Each file still has its own byte,
                # sidecar, commit and access checks within that live census.
                with self._manifest_read_paths(manifests) as resolved_paths:
                    with batch_context as batch:
                        for manifest in manifests:
                            processed_members += self._verify_manifest_in_batch(
                                manifest, verified_batches, snapshots, requested, ports, members,
                                progress_offset=processed_members, progress_total=progress_total,
                                **({"before_member": before_member} if before_member is not None else {}),
                                **({"member_preflights": member_preflights} if member_preflights or before_member is not None else {}),
                                **({'validate_member': batch.submit} if batch is not None else {}),
                                **({'_resolved_paths': resolved_paths} if resolved_paths is not None else {}),
                            )
            except OSError as error:
                if member_preflights and isinstance(error, PermissionError):
                    raise
                raise ArtifactIdentityConflict("artifact batch snapshot became unavailable") from error
            if validate_members is None:
                require_snapshot()
            else:
                assert members is not None
                require_snapshot()
                try:
                    validate_members(MappingProxyType(members))
                finally:
                    require_snapshot()
            if ports.keys() != requested.keys():
                raise ArtifactIdentityConflict("worker input was absent from its committed batch")
            complete = True
            report_progress(phase="verify_artifact_members", done=processed_members, total=processed_members)
            return ports
        finally:
            if not complete:
                for port in ports.values():
                    port.close()
                report_progress(phase="verify_artifact_members", total=progress_total, failed=1)

    @contextmanager
    def _manifest_read_paths(self, manifests):
        """Share live ancestors across all selected, complete publications.

        The paths are a finite read selection, not evidence or permission.
        Custom readers and compatibility manifests retain individual resolves.
        """
        root = self.root
        if (not _has_stock_manifest_reads(self) or not _has_stock_artifact_plane_state(self)
                or type(root) is not GuardedExternalRoot
                or set(vars(root)) != {'contract', 'inspector'}
                or type(root.inspector) is not LocalFilesystemInspector
                or any(name in vars(root.inspector) for name in ('inspect', 'inspect_bound'))
                or any(manifest.publication is None for manifest in manifests)):
            yield None
            return
        paths, publications = {}, set()
        for manifest in manifests:
            publication = manifest.publication
            if self.custody_limits.exceeds('publication_members', len(publication.members)):
                raise ArtifactIdentityConflict('artifact publication exceeds its selected member bound')
            key = publication.fingerprint()
            if key in publications:
                continue
            publications.add(key)
            paths[publication.commit_marker_relative_path] = None
            for member in publication.members:
                paths[member.relative_path] = None
                paths[member.relative_path + '.manifest.json'] = None
        with root.read_paths(paths) as resolved:
            yield resolved

    def _require_verification_snapshot_paths(
        self,
        snapshots: dict[Path, _VerificationSnapshot],
        *,
        reason: str,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
        force_full: bool = False,
        _resolved_paths=None,
    ) -> None:
        """Check live paths/access and, at strict or forced boundaries, bytes.

        Reduced read checkpoints use file identity only. The owning final guard
        and all publication/worker boundaries still force complete byte checks.
        """
        # A parallel worker owns one selected path. Scanning the entire guard
        # table in every worker makes a complete N-member read quadratic.
        with _member_preflight_scopes(self, member_preflights=member_preflights, paths=snapshots):
            # Other parent preparations may extend the live roster. Traverse one
            # stable selection; the owning outer final guard checks their full union.
            selected = tuple(snapshots.items())
            if _read_dependency_selections.get():
                for path, _ in selected:
                    self._note_verification_dependency(path)
            reduced = not force_full and self._reduced_read_verification()
            from .parallel_verification import in_parallel_verification, verify_in_parallel
            relatives = {path: path.relative_to(self.root.contract.canonical_path).as_posix()
                for path, _ in selected}
            resolution = (self.root.read_paths(relatives.values()) if _resolved_paths is None
                else nullcontext(_resolved_paths))
            with resolution as resolved:
                if (not reduced and self.maximum_parallel_verifications > 1 and len(selected) > 1
                        and sum(identity[2] for _, identity in selected) >= 1024**2
                        and not in_parallel_verification.get() and _has_stock_manifest_reads(self)):
                    def verify_one(item):
                        path, identity = item
                        self._require_verification_snapshot_paths({path: identity}, reason=reason,
                            member_preflights=member_preflights, force_full=True, _resolved_paths=resolved)
                    verify_in_parallel(verify_one, selected, workers=min(self.maximum_parallel_verifications, len(selected)))
                    if member_preflights and tuple(snapshots.items()) != selected:
                        raise ArtifactIdentityConflict("artifact snapshot census changed during parallel verification")
                    return
                for path, identity in selected:
                    if member_preflights is not None:
                        for manifest, before_member in tuple(member_preflights.get(path, ())):
                            _invoke_member_preflight(self, before_member, manifest)
                    current = resolved[relatives[path]]
                    observed = os.stat(current, follow_symlinks=False)
                    if not stat.S_ISREG(observed.st_mode) or self._descriptor_identity(observed) != identity[:5]:
                        raise ArtifactIdentityConflict(reason)
                    if reduced:
                        continue
                    # EL can preserve every stat field across an immediate same-size
                    # rewrite. Only the original exact bytes establish custody.
                    try:
                        content = bounded_file_sha256(current, maximum_bytes=identity[2])
                    except (BoundedFileIOError, OSError) as error:
                        raise ArtifactIdentityConflict(reason) from error
                    if content != (identity[2], identity[5]):
                        raise ArtifactIdentityConflict(reason)
                if member_preflights and tuple(snapshots.items()) != selected:
                    raise ArtifactIdentityConflict("artifact snapshot census changed during member preflight")

    def _operation_member_preflight(self, before_member=None):
        """Compose current callbacks; never retain their authorization result."""
        verification = getattr(self, "_read_verification", None)
        contexts = () if verification is None else verification.context_preflights
        if not contexts:
            return before_member
        callbacks = []
        retained_callback = (None if before_member is None else
            verification.composed_callbacks.get(id(before_member)))
        supplied = (() if before_member is None else retained_callback[1]
            if retained_callback is not None and retained_callback[0] is before_member else (before_member,))
        for callback in (*contexts, *supplied):
            if not callable(callback):
                raise TypeError("artifact member preflight requires a callable")
            if not any(callback is previous for previous in callbacks):
                callbacks.append(callback)
        key = tuple(id(callback) for callback in callbacks)
        retained = verification.composed_preflights.get(key)
        if retained is not None:
            return retained
        # Strong references keep identity keys valid throughout this finite operation.
        selected = tuple(callbacks)
        def require_current_member(manifest):
            for callback in selected:
                if callback(manifest) is not None:
                    raise ValueError("artifact member preflight must return None or raise")
        if all(type(callback) is ConcurrentArtifactMemberPreflight for callback in selected):
            @contextmanager
            def read_scope():
                with ExitStack() as lifetime:
                    for callback in selected:
                        if callback.read_scope is not None:
                            lifetime.enter_context(callback.read_scope())
                    yield
            require_current_member = ConcurrentArtifactMemberPreflight(require_current_member,
                read_scope if any(callback.read_scope is not None for callback in selected) else None)
        verification.composed_callbacks[id(require_current_member)] = (require_current_member, selected)
        verification.composed_preflights[key] = require_current_member
        return require_current_member

    def _track_member_preflight(self, manifest, before_member, member_preflights, *, _resolved_paths=None):
        """Retain call-local input facts, never an access verdict, for rehashes."""
        path = _resolved_read_path(self.root, manifest.materialization.relative_path, _resolved_paths)
        guards = member_preflights.setdefault(path, [])
        for original, guard in guards:
            if original != manifest:
                raise ArtifactIdentityConflict("artifact member differs from its guarded snapshot")
            if guard is before_member:
                return
        guards.append((manifest, before_member))

    def _track_verification_snapshot(
        self, path: Path, snapshots: dict[Path, _VerificationSnapshot], *,
        expected_sha256: str | None = None, maximum_bytes: int | None = None,
    ) -> None:
        observed = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(observed.st_mode):
            raise ArtifactIdentityConflict("artifact verification snapshot is not a regular file")
        identity = self._descriptor_identity(observed)
        if maximum_bytes is not None and observed.st_size > maximum_bytes:
            raise ArtifactIdentityConflict("artifact verification snapshot exceeds its byte bound")
        previous = snapshots.get(path)
        if previous is not None:
            if previous[:5] != identity or expected_sha256 is not None and previous[5] != expected_sha256:
                raise ArtifactIdentityConflict("artifact batch changed during verification")
            self._note_verification_dependency(path)
            return
        if expected_sha256 is None:
            try:
                size, expected_sha256 = bounded_file_sha256(path, maximum_bytes=observed.st_size)
            except (BoundedFileIOError, OSError) as error:
                raise ArtifactIdentityConflict("artifact batch changed during verification") from error
            if size != observed.st_size:
                raise ArtifactIdentityConflict("artifact batch changed during verification")
        snapshots[path] = (*identity, expected_sha256)
        self._note_verification_dependency(path)

    def _verify_manifest_in_batch(
        self,
        manifest: ArtifactManifest,
        verified_batches: set[str],
        snapshots: dict[Path, _VerificationSnapshot],
        requested: dict[str, tuple[WorkerInputBinding, int]],
        ports: dict[str, WorkerInputPort],
        members: dict[str, ArtifactManifest] | None = None,
        *,
        progress_offset: int = 0,
        progress_total: int | None = None,
        before_member: Callable[[ArtifactManifest], None] | None = None,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
        validate_member=None,
        _resolved_paths=None,
    ) -> int:
        sidecar = _resolved_read_path(self.root,
            f"{manifest.materialization.relative_path}.manifest.json", _resolved_paths)
        if not sidecar.is_file():
            raise ArtifactIdentityConflict("artifact manifest sidecar is unavailable")
        self._track_verification_snapshot(sidecar, snapshots, maximum_bytes=self.custody_limits.manifest_bytes)
        persisted = self._read_current_manifest(sidecar, publication=manifest.publication)
        if (
            persisted.logical != manifest.logical
            or persisted.materialization != manifest.materialization
            or (manifest.publication is not None and persisted.publication != manifest.publication)
        ):
            raise ArtifactIdentityConflict("artifact manifest differs from its sidecar")
        publication = persisted.publication
        if publication is None:
            raise ArtifactIdentityConflict(
                "compatibility manifest requires a qualified current publication"
            )
        batch_key = publication.fingerprint()
        if batch_key in verified_batches:
            return 0
        self._verify_publication_commit(publication, snapshots,
            **({'_resolved_paths': _resolved_paths} if _resolved_paths is not None else {}))

        # A member is valid only if the exact committed batch remains complete.
        for index, member in enumerate(publication.members, start=1):
            sibling_sidecar = _resolved_read_path(self.root,
                f"{member.relative_path}.manifest.json", _resolved_paths)
            self._track_verification_snapshot(sibling_sidecar, snapshots,
                maximum_bytes=self.custody_limits.manifest_bytes)
            sibling = self._read_current_manifest(sibling_sidecar, publication=publication)
            if (
                sibling.publication != publication
                or artifact_publication_member(sibling.logical, sibling.materialization) != member
            ):
                raise ArtifactIdentityConflict(
                    "artifact publication sibling differs from its committed member set"
                )
            if before_member is not None:
                assert member_preflights is not None
                self._track_member_preflight(sibling, before_member, member_preflights,
                    **({'_resolved_paths': _resolved_paths} if _resolved_paths is not None else {}))
            self._track_verification_snapshot(
                _resolved_read_path(self.root, member.relative_path, _resolved_paths), snapshots,
                expected_sha256=member.physical_sha256, maximum_bytes=member.size_bytes,
            )
            if validate_member is not None:
                validate_member(sibling)
            elif member.relative_path in requested:
                binding, limit = requested[member.relative_path]
                port = self._verify_manifest_snapshot(sibling, binding=binding, maximum_bytes=limit,
                    **({"member_preflights": member_preflights} if member_preflights else {}),
                    **({'_resolved_paths': _resolved_paths} if _resolved_paths is not None else {}))
                assert port is not None
                ports[member.relative_path] = port
            else:
                self._verify_manifest_snapshot(sibling,
                    **({"member_preflights": member_preflights} if member_preflights else {}),
                    **({'_resolved_paths': _resolved_paths} if _resolved_paths is not None else {}))
            if members is not None:
                # Each sidecar embeds the whole equal publication roster. Keep
                # one authenticated binding, not N independently decoded N-item
                # rosters (or each decoded manifest's canonical-byte cache).
                members[member.relative_path] = sibling
            done = progress_offset + index
            # Completion also requires the owning invocation's final snapshot
            # and consumer guards. Do not report a known total before those.
            if progress_total is None or done < progress_total:
                report_progress(phase="verify_artifact_members", done=done, total=progress_total)
        verified_batches.add(batch_key)
        return len(publication.members)

    def _verify_publication_commit(self, publication: ArtifactPublicationBinding,
            snapshots: dict[Path, _VerificationSnapshot], *, _resolved_paths=None) -> None:
        """Authenticate exact commit metadata, without accepting member payloads."""
        if self.custody_limits.exceeds("publication_members", len(publication.members)):
            raise ArtifactIdentityConflict("artifact publication exceeds its selected member bound")
        expected_commit = ArtifactPublicationCommit(
            publication_batch_id=publication.publication_batch_id,
            publication_scope=publication.publication_scope,
            members=publication.members,
        ).canonical_bytes()
        if (
            self.custody_limits.exceeds("publication_marker_bytes", len(expected_commit))
            or len(expected_commit) != publication.commit_marker_size_bytes
            or hashlib.sha256(expected_commit).hexdigest() != publication.commit_marker_sha256
        ):
            raise ArtifactIdentityConflict("artifact publication binding differs from its commit")
        commit_path = _resolved_read_path(self.root, publication.commit_marker_relative_path, _resolved_paths)
        try:
            self._track_verification_snapshot(commit_path, snapshots,
                expected_sha256=publication.commit_marker_sha256, maximum_bytes=publication.commit_marker_size_bytes)
            committed = file_matches_bytes(commit_path, expected_commit)
        except (BoundedFileIOError, OSError) as error:
            raise ArtifactIdentityConflict(
                "artifact publication is not durably committed"
            ) from error
        if not committed:
            raise ArtifactIdentityConflict("artifact publication is not durably committed")

    @staticmethod
    def _descriptor_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    def _read_current_manifest(self, path: Path, *,
            publication: ArtifactPublicationBinding | None = None,
            maximum_bytes: int | None = None) -> ArtifactManifest:
        ceilings = tuple(value for value in (maximum_bytes, self.custody_limits.manifest_bytes) if value is not None)
        ceiling = min(ceilings) if ceilings else None
        try:
            if publication is None:
                return self._observe_manifest_metadata(read_artifact_sidecar(self,
                    path.relative_to(self.root.contract.canonical_path).as_posix(),
                    maximum_bytes=ceiling))
            sidecar_payload = read_bounded_bytes(
                path,
                maximum_bytes=ceiling,
            )
            # Imported lazily because the receipt store composes this plane.
            persisted = decode_artifact_sidecar(sidecar_payload,
                maximum_bytes=ceiling, publication=publication)
        except (BoundedFileIOError, OSError, ValueError) as error:
            raise ArtifactIdentityConflict("artifact manifest sidecar is invalid") from error
        if persisted.publication is None:
            raise ArtifactIdentityConflict(
                "compatibility manifest requires a qualified current publication"
            )
        return self._observe_manifest_metadata(persisted)

    def _verify_manifest_snapshot(
        self,
        manifest: ArtifactManifest,
        *,
        binding: WorkerInputBinding | None = None,
        maximum_bytes: int = 0,
        before_member: Callable[[ArtifactManifest], None] | None = None,
        member_preflights: dict[Path, list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] | None = None,
        _resolved_paths=None,
    ) -> WorkerInputPort | None:
        before_member = self._operation_member_preflight(before_member)
        verification = getattr(self, "_read_verification", None)
        if verification is not None:
            path = _resolved_read_path(self.root, manifest.materialization.relative_path, _resolved_paths)
            original = verification.member_manifests.setdefault(path, manifest)
            if original != manifest:
                raise ArtifactIdentityConflict("artifact member changes its operation-local manifest")
            if before_member is not None:
                self._track_member_preflight(manifest, before_member, verification.member_preflights,
                    **({'_resolved_paths': _resolved_paths} if _resolved_paths is not None else {}))
            if member_preflights is None:
                member_preflights = verification.member_preflights
        materialization = manifest.materialization
        if materialization.storage_root_id != self.root.contract.storage_root_id:
            raise ArtifactIdentityConflict("artifact belongs to another storage root")
        if manifest.publication is None:
            raise ArtifactIdentityConflict("qualified artifact lacks a publication binding")
        if manifest.logical.content_sha256 != materialization.physical_sha256:
            raise ArtifactIdentityConflict(
                "logical content identity lacks a verified equivalence proof"
            )
        if materialization.compression != "none" or materialization.partition_selector is not None:
            raise ArtifactIdentityConflict(
                "compressed or partitioned artifacts lack an equivalence proof contract"
            )
        generic_validation = manifest.logical.generic_validation
        if generic_validation is None:
            raise ArtifactIdentityConflict(
                "compatibility manifest lacks a qualified generic validator registration"
            )
        if (
            generic_validation.profile is not manifest.logical.profile
            or generic_validation.payload_schema != manifest.logical.payload_schema
        ):
            raise ArtifactIdentityConflict(
                "artifact generic validation differs from its logical identity"
            )
        self.validators.require_generic_validation(generic_validation)
        self._require_registered_semantics(
            manifest.logical.logical_artifact_id,
            manifest.logical.semantic_validation,
        )
        path = _resolved_read_path(self.root, materialization.relative_path, _resolved_paths)
        if before_member is not None:
            if not callable(before_member):
                raise TypeError("artifact member preflight requires a callable")
            _invoke_member_preflight(self, before_member, manifest)
        if member_preflights is not None:
            for original, guard in tuple(member_preflights.get(path, ())):
                if original != manifest:
                    raise ArtifactIdentityConflict("artifact member differs from its guarded snapshot")
                _invoke_member_preflight(self, guard, manifest)
        proof_key = (self.validators, materialization.relative_path)
        reuse_profile = (binding is None and not full_verification_forced() and verification is not None
            and verification.context_depth and _has_stock_manifest_reads(self))
        reduced = reuse_profile and self._reduced_read_verification()
        ledger_key = None
        if reduced:
            observed = os.stat(path, follow_symlinks=False)
            if not stat.S_ISREG(observed.st_mode) or observed.st_size != materialization.size_bytes:
                raise ArtifactIdentityConflict('artifact type or size changed before profile reuse')
            identity = self._descriptor_identity(observed)
            # The manifest is exactly these three immutable records. Bind all
            # of them without rehashing the whole shared publication roster
            # once per sibling. This changes no stored canonical identity.
            ledger_key = (self.root.contract.fingerprint(), self.validators,
                self.semantic_validations.fingerprint(), self.custody_limits,
                manifest.SCHEMA, manifest.VERSION, manifest.logical.fingerprint(),
                materialization.fingerprint(), manifest.publication.fingerprint())
            retained = verification.ledger.get(ledger_key)
            if retained is not None:
                if retained[0] != identity:
                    raise ArtifactIdentityConflict('artifact changed since invocation verification')
                verification.profiled_members[proof_key] = (manifest, retained[1])
                return None
        if reuse_profile:
            original = verification.profiled_members.get(proof_key)
            if original is not None:
                if original[0] != manifest:
                    raise ArtifactIdentityConflict('artifact profile changes its authenticated manifest')
                # Registry membership and every current access callback above
                # remain fresh. The declared format/field contract and bytes
                # are the same; the outer context still rehashes all of them.
                return None
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError as error:
            raise ArtifactIdentityConflict("artifact path is unavailable") from error
        anonymous: int | None = None
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise ArtifactIdentityConflict("artifact type differs from identity")
            if before.st_size != materialization.size_bytes:
                raise ArtifactIdentityConflict("artifact bytes differ from their identity")
            typed_read = current_canonical_record_read(self, manifest) if binding is None else None
            typed_chunks = [] if typed_read is not None else None
            digest = hashlib.sha256() if typed_read is None else None
            observed_bytes = 0
            if binding is not None:
                anonymous = _anonymous_input_descriptor()
            while True:
                chunk = os.read(descriptor, STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                observed_bytes += len(chunk)
                if observed_bytes > materialization.size_bytes:
                    raise ArtifactIdentityConflict("artifact identity scan exceeded its bound")
                if typed_chunks is None:
                    digest.update(chunk)
                else:
                    typed_chunks.append(chunk)
                if anonymous is not None:
                    view = memoryview(chunk)
                    while view:
                        written = os.write(anonymous, view)
                        if written <= 0:
                            raise OSError("worker input copy made no progress")
                        view = view[written:]
            if (
                observed_bytes != materialization.size_bytes
                or digest is not None and digest.hexdigest() != materialization.physical_sha256
            ):
                raise ArtifactIdentityConflict("artifact bytes differ from their identity")
            if anonymous is not None:
                os.lseek(anonymous, 0, os.SEEK_SET)
                _seal_anonymous_input(anonymous)
            descriptor_path = Path(
                f"/proc/self/fd/{descriptor if anonymous is None else anonymous}"
            )
            logical = manifest.logical
            if typed_read is not None:
                payload = b''.join(typed_chunks)
                typed_chunks.clear()
                header = typed_read.decode(payload)
                del payload
            else:
                header = self.validators.validate_file(
                    descriptor_path,
                    ArtifactStreamWriteRequest(
                        logical_artifact_id=logical.logical_artifact_id,
                        relative_path=materialization.relative_path,
                        payload_schema=logical.payload_schema,
                        profile=logical.profile,
                        media_type=logical.media_type,
                        publication_scope_id=(
                            manifest.publication.publication_scope.publication_scope_id
                        ),
                        publication_scope_relative_root=(
                            manifest.publication.publication_scope.relative_root
                        ),
                        chunks=(),
                        maximum_bytes=max(1, materialization.size_bytes),
                        maximum_chunk_bytes=min(
                            STREAM_CHUNK_BYTES,
                            max(1, materialization.size_bytes),
                        ),
                        visibility_ceiling=logical.visibility_ceiling,
                        parent_visibility_ceilings=logical.parent_visibility_ceilings,
                        outcome_access=logical.outcome_access,
                        compression=materialization.compression,
                        partition_selector=materialization.partition_selector,
                        lineage_parents=logical.lineage_parents,
                        minimum_free_bytes=0,
                        semantic_validation=logical.semantic_validation,
                    ),
                    custody_limits=self.custody_limits,
                )
            after = os.fstat(descriptor)
            named = os.stat(path, follow_symlinks=False)
            if self._descriptor_identity(before) != self._descriptor_identity(after) or (
                named.st_dev,
                named.st_ino,
            ) != (before.st_dev, before.st_ino):
                raise ArtifactIdentityConflict(
                    "artifact changed or was replaced during semantic verification"
                )
            if anonymous is not None:
                assert binding is not None
                port = WorkerInputPort(
                    binding=binding,
                    _reader=_PreopenedBoundedReader(anonymous, maximum_bytes=maximum_bytes),
                )
                anonymous = None
                return port
            if reuse_profile:
                verification.profiled_members[proof_key] = (manifest, header)
            if ledger_key is not None:
                verification.ledger.put(ledger_key, self._descriptor_identity(after), header)
            return None
        except OSError as error:
            raise ArtifactIdentityConflict("artifact snapshot verification failed") from error
        finally:
            os.close(descriptor)
            if anonymous is not None:
                os.close(anonymous)

    @staticmethod
    def _stream_identity(path: Path, *, maximum_bytes: int) -> tuple[int, str]:
        try:
            return bounded_file_sha256(path, maximum_bytes=maximum_bytes)
        except BoundedFileIOError as error:
            raise ArtifactIdentityConflict("artifact identity scan exceeded its bound") from error

    def _write_pair_once(
        self,
        artifact_path: Path,
        artifact_payload: bytes,
        manifest_path: Path,
        manifest_payload: bytes,
    ) -> bool:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self._pair_lock(artifact_path, manifest_path):
            artifact_exists = artifact_path.exists()
            manifest_exists = manifest_path.exists()
            if artifact_exists or manifest_exists:
                if artifact_exists != manifest_exists:
                    raise ArtifactIdentityConflict("artifact/manifest pair is partial")
                try:
                    matches = file_matches_bytes(
                        artifact_path,
                        artifact_payload,
                    ) and file_matches_bytes(manifest_path, manifest_payload)
                except BoundedFileIOError as error:
                    raise ArtifactIdentityConflict(
                        "immutable artifact identity comparison failed"
                    ) from error
                if not matches:
                    raise ArtifactIdentityConflict("immutable artifact identity already exists")
                return False
            self._write_atomic(artifact_path, artifact_payload)
            try:
                self._write_atomic(manifest_path, manifest_payload)
            except Exception:
                # Preserve the partial artifact for identity-checked recovery.
                raise
            self._fsync_directory(artifact_path.parent)
            if manifest_path.parent != artifact_path.parent:
                self._fsync_directory(manifest_path.parent)
            return True

    @staticmethod
    @contextmanager
    def _pair_lock(artifact_path: Path, manifest_path: Path):  # type: ignore[no-untyped-def]
        token = hashlib.sha256(
            f"{artifact_path.name}\0{manifest_path.name}".encode("utf-8")
        ).hexdigest()[:24]
        lock_path = artifact_path.parent / f".artifact-pair.{token}.lock"
        with exclusive_file_lock(lock_path):
            yield

    @staticmethod
    @contextmanager
    def _publication_batch_lock(commit_path: Path):  # type: ignore[no-untyped-def]
        token = hashlib.sha256(str(commit_path).encode("utf-8")).hexdigest()[:24]
        lock_path = commit_path.parent / f".publication-batch.{token}.lock"
        with exclusive_file_lock(lock_path):
            yield

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _staging_path(path: Path, token: str, suffix: str) -> Path:
        """Keep staging names bounded independently of the immutable target.

        A valid receipt filename can approach the filesystem component limit.
        Its digest distinguishes artifact and sidecar staging without appending
        another copy of that filename. The transaction token retains exclusive
        publication and cleanup semantics.
        """
        name_digest = hashlib.sha256(path.name.encode("utf-8")).hexdigest()
        return path.with_name(f".{name_digest}.{token}.{suffix}")

    @staticmethod
    def _write_atomic(path: Path, payload: bytes) -> None:
        token = f"{os.getpid()}.{threading.get_ident()}"
        temporary = ExternalArtifactPlane._staging_path(path, token, "partial")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            if temporary.exists():
                temporary.unlink()
            raise


def _worker_input_requests(values, bindings, maximum_bytes):
    """Apply the same complete binding and scan budget to fresh or retained ports."""
    if (maximum_bytes is not None and maximum_bytes < 0) or len(values) != len(bindings):
        raise ValueError("worker input count or budget is invalid")
    if maximum_bytes is not None and sum(value.materialization.size_bytes for value in values) > maximum_bytes:
        raise ArtifactInputLimitExceeded("frozen input size exceeds the worker input-scan budget")
    requested = {}
    for value, binding in zip(values, bindings, strict=True):
        if binding != WorkerInputBinding.from_verified(value, kind=binding.kind):
            raise ArtifactIdentityConflict("worker input binding differs from the verified materialization")
        path = value.materialization.relative_path
        if path in requested:
            raise ArtifactIdentityConflict("worker input materialization is duplicated")
        requested[path] = (binding,
            maximum_bytes if maximum_bytes is not None and len(values) == 1 else value.materialization.size_bytes)
    return requested


class _ArtifactReadVerification:
    """Call-local custody state; never a persistent cache or access decision."""

    def __init__(self, context_preflights=(), manifest_observers=(), *, ledger=None) -> None:
        self.context_preflights = context_preflights
        self.manifest_observers = manifest_observers
        self.composed_preflights = {}
        self.composed_callbacks = {}
        self.member_manifests = {}
        self.active = True
        self.ledger = ledger
        self.snapshots: dict[Path, _VerificationSnapshot] = {}
        self.member_preflights: dict[Path,
            list[tuple[ArtifactManifest, Callable[[ArtifactManifest], None]]]] = {}
        self.batches: dict[tuple[ArtifactProfileValidatorRegistry, str], set[str]] = {}
        self.publications: dict[str, ArtifactPublicationBinding] = {}
        self.context_depth = 0
        self.context_manifests: dict[str, ArtifactManifest] = {}
        self.context_members: dict[tuple[ArtifactProfileValidatorRegistry, str],
            dict[str, Mapping[str, ArtifactManifest]]] = {}
        self.context_censuses: dict[tuple[ArtifactProfileValidatorRegistry, str],
            dict[int, tuple[tuple[ArtifactManifest, ...], Mapping[str, ArtifactManifest]]]] = {}
        self.context_census_sizes: dict[tuple[ArtifactProfileValidatorRegistry, str], int] = {}
        self.profiled_members = {}
        self.canonical_pool = None


class _ReadDependencyCheckpoint:
    """An exact consumed path selection, bounded by its owning read census.

    It holds no access verdict. Complete publications are expanded once, and
    nested checkpoint consumption contributes its paths to each live parent.
    The ordinary read owner still checks the complete union on every exit.
    """

    def __init__(self, plane, *, selected):
        self.plane = plane
        self.verification = getattr(plane, '_read_verification', None)
        self.selected = selected
        self.active = True
        self.paths = set()
        self.publications = {}
        self.snapshots = {}
        self.policy = (plane.root, plane.validators, plane.semantic_validations,
            plane.custody_limits, plane.artifact_verification)

    def include_path(self, path):
        if not self.active:
            raise ArtifactIdentityConflict('dependency checkpoint escaped its read lifetime')
        self.paths.add(path)

    def include_publication(self, publication):
        if publication is None:
            raise ArtifactIdentityConflict('dependency checkpoint requires complete publication custody')
        key = publication.commit_marker_relative_path
        previous = self.publications.get(key)
        if previous is not None:
            if previous != publication:
                raise ArtifactIdentityConflict('dependency checkpoint aliases a publication')
            return
        self.publications[key] = publication
        root = Path(self.plane.root.contract.canonical_path)
        self.include_path(root / key)
        for member in publication.members:
            self.include_path(root / member.relative_path)
            self.include_path(root / (member.relative_path + '.manifest.json'))

    def require_current(self, *, force_full=False):
        plane, verification = self.plane, self.verification
        if not self.active or verification is not None and not verification.active:
            raise ArtifactIdentityConflict('dependency checkpoint escaped its read lifetime')
        if not self.selected:
            if force_full:
                plane.require_full_verification_snapshot()
            else:
                plane.require_verification_snapshot()
            return
        if (not _supports_selected_dependencies(plane)
                or getattr(plane, '_read_verification', None) is not verification
                or not verification.context_depth
                or any(current is not original for current, original in zip(
                    (plane.root, plane.validators, plane.semantic_validations, plane.custody_limits,
                        plane.artifact_verification), self.policy, strict=True))):
            raise ArtifactIdentityConflict('dependency checkpoint changes its owning read policy')
        plane.require_active_verification_scope()
        for path in self.paths - self.snapshots.keys():
            try:
                self.snapshots[path] = verification.snapshots[path]
            except KeyError as error:
                raise ArtifactIdentityConflict('dependency checkpoint lacks actual byte custody') from error
        callback = plane._operation_member_preflight()
        if callback is not None:
            for path in tuple(self.snapshots):
                manifest = verification.member_manifests.get(path)
                if manifest is not None:
                    plane._track_member_preflight(manifest, callback, verification.member_preflights)
        plane._require_verification_snapshot_paths(self.snapshots,
            reason='selected read dependency changed during consumption', force_full=force_full,
            member_preflights=verification.member_preflights)
        plane.require_active_verification_scope()

    def close(self):
        self.active = False
        self.paths.clear()
        self.publications.clear()
        self.snapshots.clear()


class _IndexedPublicationMembers(Mapping[str, ArtifactManifest]):
    """A selected union with constant-time lookup and shared publication storage.

    The owner authenticates disjoint publication views before constructing this
    mapping. Reusing its path index avoids both a linear search through every
    publication and copying a complete member dictionary for every selection.
    Pending views have a separate index until the consumer accepts the batch.
    """

    def __init__(self, views, retained, additions):
        self._views = views
        self._selected = frozenset(id(view) for view in views)
        self._retained = retained
        self._additions = {path: view for view in additions for path in view}
        self._size = sum(len(view) for view in views)

    def __getitem__(self, path):
        view = self._additions.get(path)
        if view is None:
            view = self._retained.get(path)
        if view is None or id(view) not in self._selected:
            raise KeyError(path)
        return view[path]

    def __iter__(self):
        for view in self._views:
            yield from view

    def __len__(self):
        return self._size


class _ScopedArtifactPlane(ExternalArtifactPlane):
    def __init__(self, plane: ExternalArtifactPlane, verification: _ArtifactReadVerification) -> None:
        super().__init__(plane.root, plane.validators, plane.semantic_validations,
                         custody_limits=plane.custody_limits,
                         maximum_parallel_verifications=plane.maximum_parallel_verifications,
                         artifact_verification=plane.artifact_verification)
        self._verification_preflight_lock = plane._verification_preflight_lock
        self._read_verification = verification

    @contextmanager
    def verification_dependencies(self):
        if not _supports_selected_dependencies(self):
            with super().verification_dependencies() as checkpoint:
                yield checkpoint
            return
        self.require_active_verification_scope()
        checkpoint = _ReadDependencyCheckpoint(self, selected=True)
        token = _read_dependency_selections.set((*_read_dependency_selections.get(), checkpoint))
        try:
            yield checkpoint
        finally:
            try:
                checkpoint.require_current()
            finally:
                _read_dependency_selections.reset(token)
                checkpoint.close()

    @contextmanager
    def read_context(self, *, before_member: Callable[[ArtifactManifest], None] | None = None,
            observe_manifest: Callable[[ArtifactManifest], None] | None = None) -> Iterator[ExternalArtifactPlane]:
        verification = self._read_verification
        if before_member is not None and not callable(before_member):
            raise TypeError("artifact context member preflight requires a callable")
        if observe_manifest is not None and not callable(observe_manifest):
            raise TypeError("artifact manifest observer requires a callable")
        previous = verification.context_preflights
        previous_observers = verification.manifest_observers
        if before_member is not None:
            verification.context_preflights = (*previous, before_member)
        if observe_manifest is not None:
            verification.manifest_observers = (*previous_observers, observe_manifest)
        try:
            self.require_verification_context()
            if verification.context_depth:
                # Nested contexts reuse custody facts, not a previous access result.
                if before_member is None:
                    yield self
                else:
                    with self.verification_dependencies():
                        yield self
                return
            verification.context_depth = 1
            try:
                yield self
            finally:
                try:
                    self.require_full_verification_snapshot()
                finally:
                    verification.context_depth = 0
                    verification.context_manifests.clear()
                    verification.context_members.clear()
                    verification.context_censuses.clear()
                    verification.context_census_sizes.clear()
                    verification.profiled_members.clear()
        finally:
            verification.context_preflights = previous
            verification.manifest_observers = previous_observers

    def require_active_verification_scope(self) -> None:
        """Check this actual lifetime without recursively verifying its bodies."""
        if not self._read_verification.active:
            raise ArtifactIdentityConflict("artifact verification scope has ended")

    def require_verification_context(self) -> None:
        self.require_active_verification_scope()
        verification = self._read_verification
        if not verification.context_depth or not _has_stock_manifest_reads(self):
            self.require_verification_snapshot()

    def read_manifest(self, relative_path: str, *, maximum_bytes: int | None = None) -> ArtifactManifest:
        """Reuse exact commit metadata within this scope, retaining final guards."""
        verification = self._read_verification
        if not verification.active:
            raise ArtifactIdentityConflict("artifact verification scope has ended")
        if (verification.context_depth and _has_stock_manifest_reads(self)
                and relative_path in verification.context_manifests):
            manifest = verification.context_manifests[relative_path]
            sidecar = Path(self.root.contract.canonical_path) / (relative_path + ".manifest.json")
            if maximum_bytes is not None and verification.snapshots[sidecar][2] > maximum_bytes:
                raise BoundedFileIOError("bounded input exceeds its byte limit")
            return self._observe_manifest_metadata(manifest)
        sidecar = self.root.resolve(relative_path + ".manifest.json", for_write=False)
        self._track_verification_snapshot(sidecar, verification.snapshots,
            maximum_bytes=self.custody_limits.manifest_bytes)
        publication = verification.publications.get(relative_path)
        if publication is None:
            manifest = super().read_manifest(relative_path, maximum_bytes=maximum_bytes)
            publication = manifest.publication
            if publication is None:
                raise ArtifactIdentityConflict("current artifact metadata lacks a publication binding")
            self._verify_publication_commit(publication, verification.snapshots)
            for member in publication.members:
                previous = verification.publications.setdefault(member.relative_path, publication)
                if previous != publication:
                    raise ArtifactIdentityConflict("scoped member has conflicting publication metadata")
        else:
            self._track_verification_snapshot(self.root.resolve(publication.commit_marker_relative_path,
                for_write=False), verification.snapshots,
                expected_sha256=publication.commit_marker_sha256,
                maximum_bytes=publication.commit_marker_size_bytes)
            manifest = self._read_current_manifest(sidecar, publication=publication, maximum_bytes=maximum_bytes)
        if manifest.materialization.relative_path != relative_path:
            raise ArtifactIdentityConflict("artifact sidecar differs from its actual member path")
        if verification.context_depth:
            verification.context_manifests[relative_path] = manifest
        return self._observe_manifest_metadata(manifest)

    def require_verification_snapshot(self) -> None:
        verification = self._read_verification
        if not verification.active:
            raise ArtifactIdentityConflict("artifact verification scope has ended")
        try:
            callback = self._operation_member_preflight()
            if callback is not None:
                for manifest in tuple(verification.member_manifests.values()):
                    self._track_member_preflight(manifest, callback, verification.member_preflights)
            self._require_verification_snapshot_paths(verification.snapshots,
                reason="artifact changed during its verification scope",
                **({"member_preflights": verification.member_preflights}
                    if verification.member_preflights else {}))
        except OSError as error:
            if verification.member_preflights and isinstance(error, PermissionError):
                raise
            raise ArtifactIdentityConflict("artifact verification snapshot became unavailable") from error

    def with_semantic_validation_registry(self, registry: ArtifactSemanticValidationRegistry) -> ExternalArtifactPlane:
        self.require_verification_context()
        return _ScopedArtifactPlane(super().with_semantic_validation_registry(registry), self._read_verification)

    def _consume_context_members(self, manifests, *, validate_members, before_member=None):
        with _member_preflight_scopes(self, before_member=before_member):
            return self._consume_context_members_in_scope(manifests, validate_members=validate_members,
                before_member=before_member)

    def _consume_context_members_in_scope(self, manifests, *, validate_members, before_member=None):
        """Reuse one immutable member mapping per actual validation context.

        No consumer result or permission is retained. New closures get the
        ordinary complete byte/sidecar/commit checks and their own guards;
        shared closures retain references rather than copying their census for
        each leaf. The owning read context checks the union before returning.
        """
        before_member = self._operation_member_preflight(before_member)
        if before_member is not None and not callable(before_member):
            raise TypeError("artifact member preflight requires a callable")
        if before_member is None or _has_stock_manifest_reads(self):
            self.require_verification_context()
        elif not self._read_verification.active:
            raise ArtifactIdentityConflict("artifact verification scope has ended")
        if not callable(validate_members):
            raise TypeError("artifact member validation requires a callable")
        if self.custody_limits.exceeds("publication_members", len(manifests)):
            raise ArtifactIdentityConflict("artifact verification batch exceeds its bound")
        verification = self._read_verification
        if not _has_stock_manifest_reads(self):
            # Replacing an owning read policy never inherits the stock proof.
            if before_member is None:
                self.require_verification_snapshot()
            try:
                return self._consume_verified_manifests_members(manifests,
                    validate_members=validate_members, snapshots=verification.snapshots,
                    **({"before_member": before_member} if before_member is not None else {}),
                    **({"member_preflights": verification.member_preflights}
                        if verification.member_preflights or before_member is not None else {}))
            finally:
                self.require_verification_snapshot()
        key = (self.validators, self.semantic_validations.fingerprint())
        retained = verification.context_members.setdefault(key, {})
        censuses = verification.context_censuses.setdefault(key, {})
        census = censuses.get(id(manifests))
        if census is not None and census[0] is manifests:
            # Only the exact immutable selected tuple can reuse this join.
            # An equal replacement still undergoes every original comparison.
            if before_member is not None or verification.member_preflights:
                for manifest in census[1].values():
                    if before_member is not None:
                        self._track_member_preflight(manifest, before_member, verification.member_preflights)
                    path = self.root.resolve(manifest.materialization.relative_path, for_write=False)
                    for original, guard in tuple(verification.member_preflights.get(path, ())):
                        guard(original)
            self._note_verified_publications(manifests, census[1])
            result = validate_members(census[1])
            self.require_verification_context()
            return result
        views = {}
        pending = []
        for manifest in manifests:
            path = manifest.materialization.relative_path
            view = retained.get(path)
            if view is None:
                pending.append(manifest)
                continue
            original = view[path]
            if (manifest.logical != original.logical or manifest.materialization != original.materialization
                    or manifest.publication is not None and manifest.publication != original.publication):
                raise ArtifactIdentityConflict("artifact manifest differs from its authenticated read context")
            views[id(view)] = view
        # Reuse custody, never the caller's current access decision. Every
        # sibling remains subject to this operation's explicit preflights.
        if before_member is not None or verification.member_preflights:
            for view in views.values():
                for manifest in view.values():
                    if before_member is not None:
                        self._track_member_preflight(manifest, before_member, verification.member_preflights)
                    path = self.root.resolve(manifest.materialization.relative_path, for_write=False)
                    for original, guard in tuple(verification.member_preflights.get(path, ())):
                        guard(original)
        new_views = {}
        if pending:
            snapshots = {}
            authenticated = self._consume_verified_manifests_members(tuple(pending),
                validate_members=lambda members: members, snapshots=snapshots, _borrow_read_context=True,
                **({"before_member": before_member} if before_member is not None else {}),
                **({"member_preflights": verification.member_preflights}
                    if verification.member_preflights or before_member is not None else {}))
            for path, manifest in authenticated.items():
                publication = manifest.publication
                assert publication is not None
                new_views.setdefault(publication.publication_batch_id, {})[path] = manifest
                previous = verification.context_manifests.setdefault(path, manifest)
                if previous != manifest:
                    raise ArtifactIdentityConflict("artifact changes its read-context sidecar")
            new_views = {batch: MappingProxyType(rows) for batch, rows in new_views.items()}
            views.update((id(view), view) for view in new_views.values())
        selected = tuple(views.values())
        members = (selected[0] if len(selected) == 1 else MappingProxyType(
            _IndexedPublicationMembers(selected, retained, tuple(new_views.values()))))
        self._note_verified_publications(manifests, members)
        result = validate_members(members)
        self.require_verification_context()
        # Failed consumers never warm this operation's reusable byte proof.
        for view in new_views.values():
            for path in view:
                retained[path] = view
        census_size = verification.context_census_sizes.get(key, 0)
        if (type(manifests) is tuple and len(manifests) > 1
                and len(manifests) + census_size <= 2 * len(retained)
                and all(type(row) is ArtifactManifest and row._is_cacheable() for row in manifests)):
            # At most two selected tuple references per authenticated member;
            # repeated caller-created copies cannot grow a population cache.
            censuses[id(manifests)] = (manifests, members)
            verification.context_census_sizes[key] = census_size + len(manifests)
        return result

    def verify_manifests(self, manifests: tuple[ArtifactManifest, ...], *,
            before_member: Callable[[ArtifactManifest], None] | None = None) -> None:
        if before_member is not None:
            self.verify_manifests_members(manifests, validate_members=lambda members: None,
                before_member=before_member)
            return
        if self._read_verification.context_depth:
            self._consume_context_members(manifests, validate_members=lambda members: None)
            return
        self.require_verification_snapshot()
        if self.custody_limits.exceeds("publication_members", len(manifests)):
            raise ArtifactIdentityConflict("artifact verification batch exceeds its bound")
        # Semantic registries define different checks even for identical bytes.
        # Generic validators remain bound to the same owning registry instance.
        key = (self.validators, self.semantic_validations.fingerprint())
        batches = self._read_verification.batches.setdefault(key, set())
        processed_members = 0
        progress_total = (len(manifests[0].publication.members)
            if len(manifests) == 1 and manifests[0].publication is not None else None)
        report_progress(phase="verify_artifact_members", done=0, total=progress_total)
        try:
            for manifest in manifests:
                processed_members += self._verify_manifest_in_batch(manifest, batches,
                    self._read_verification.snapshots, {}, {}, progress_offset=processed_members,
                    progress_total=progress_total,
                    **({"member_preflights": self._read_verification.member_preflights}
                        if self._read_verification.member_preflights else {}))
            self.require_verification_snapshot()
        except OSError as error:
            report_progress(phase="verify_artifact_members", total=progress_total, failed=1)
            if self._read_verification.member_preflights and isinstance(error, PermissionError):
                raise
            raise ArtifactIdentityConflict("artifact verification snapshot became unavailable") from error
        except Exception:
            report_progress(phase="verify_artifact_members", total=progress_total, failed=1)
            raise
        report_progress(phase="verify_artifact_members", done=processed_members, total=processed_members)

    def verify_manifest_members(
        self,
        manifest: ArtifactManifest,
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> _MemberValidationResult:
        if self._read_verification.context_depth:
            return self._consume_context_members((manifest,), validate_members=validate_members,
                **({"before_member": before_member} if before_member is not None else {}))
        if before_member is not None:
            if not callable(before_member):
                raise TypeError("artifact member preflight requires a callable")
            if not self._read_verification.active:
                raise ArtifactIdentityConflict("artifact verification scope has ended")
        else:
            self.require_verification_snapshot()
        try:
            return self._consume_verified_manifest_members(manifest,
                validate_members=validate_members, snapshots=self._read_verification.snapshots,
                **({"before_member": before_member} if before_member is not None else {}),
                **({"member_preflights": self._read_verification.member_preflights}
                    if self._read_verification.member_preflights or before_member is not None else {}))
        finally:
            self.require_verification_snapshot()


    def verify_manifests_members(
        self,
        manifests: tuple[ArtifactManifest, ...],
        *,
        validate_members: Callable[[Mapping[str, ArtifactManifest]], _MemberValidationResult],
        before_member: Callable[[ArtifactManifest], None] | None = None,
    ) -> _MemberValidationResult:
        if self._read_verification.context_depth:
            return self._consume_context_members(manifests, validate_members=validate_members,
                **({"before_member": before_member} if before_member is not None else {}))
        if before_member is not None:
            if not callable(before_member):
                raise TypeError("artifact member preflight requires a callable")
            if not self._read_verification.active:
                raise ArtifactIdentityConflict("artifact verification scope has ended")
        else:
            self.require_verification_snapshot()
        if not callable(validate_members):
            raise TypeError("artifact member validation requires a callable")
        # Bind proof to the registries that actually validated these bytes,
        # even when the callback selects a different registry for a later read.
        key = (self.validators, self.semantic_validations.fingerprint())
        completed_publications: set[str] = set()

        def consume(authenticated: Mapping[str, ArtifactManifest]) -> _MemberValidationResult:
            completed_publications.update(value.publication.fingerprint()
                for value in authenticated.values() if value.publication is not None)
            return validate_members(authenticated)

        try:
            result = self._consume_verified_manifests_members(manifests,
                validate_members=consume, snapshots=self._read_verification.snapshots,
                **({"before_member": before_member} if before_member is not None else {}),
                **({"member_preflights": self._read_verification.member_preflights}
                    if self._read_verification.member_preflights or before_member is not None else {}))
        finally:
            self.require_verification_snapshot()
        # A failed callback or final guard cannot publish a reusable proof.
        # Later reads retain the existing fresh full-path snapshot checks.
        self._read_verification.batches.setdefault(key, set()).update(completed_publications)
        return result


# Method identity chooses a local optimization only, never custody/authority.
# Exact custom/instance hooks keep the established serial read boundaries.
_MANIFEST_READ_METHOD_NAMES = ("verification_scope", "_verification_lifetime", "read_context", "require_active_verification_scope", "require_verification_context",
    "verification_dependencies", "_note_verification_dependency", "_note_verified_publications",
    "require_full_verification_snapshot", "_reduced_read_verification",
    "verified_canonical_header",
    "with_semantic_validation_registry",
    "read_manifest", "verify_manifest", "verify_manifests",
    "verify_manifest_members", "verify_manifests_members", "_consume_verified_manifest_members",
    "_consume_verified_manifests_members", "_verify_manifests", "_verify_manifests_in_scope", "_manifest_read_paths", "_verify_manifest_in_batch",
    "_verify_manifest_snapshot", "_read_current_manifest", "_verify_publication_commit", "_observe_manifest_metadata",
    "_track_verification_snapshot", "_track_member_preflight", "_require_verification_snapshot_paths", "_descriptor_identity")
_STOCK_MANIFEST_READ_METHODS = tuple((owner, name, getattr(owner, name))
    for owner, names in (
        (ExternalArtifactPlane, _MANIFEST_READ_METHOD_NAMES),
        (_ScopedArtifactPlane, (*_MANIFEST_READ_METHOD_NAMES, "require_verification_snapshot", "_consume_context_members", "_consume_context_members_in_scope")),
        (GuardedExternalRoot, ("resolve", "verify", "_verify", "read_paths")),
        (LocalFilesystemInspector, ("inspect", "inspect_bound"))) for name in names)


def _has_stock_manifest_reads(plane):
    """Refuse new batching when the actual owning read methods were replaced."""
    return (type(plane) in (ExternalArtifactPlane, _ScopedArtifactPlane)
        and not any(name in vars(plane) for owner, name, _ in _STOCK_MANIFEST_READ_METHODS
            if owner in (ExternalArtifactPlane, _ScopedArtifactPlane))
        and all(getattr(owner, name) is original for owner, name, original in _STOCK_MANIFEST_READ_METHODS))


_STOCK_BATCH_WRITE_METHODS = tuple((name, getattr(ExternalArtifactPlane, name))
    for name in ('write', 'write_stream', 'write_batch', 'write_compact_batch'))
_STOCK_PREPARE_METHOD = ExternalArtifactPlane._prepare


def supports_closed_batch_writes(plane):
    """Select only the unchanged publication owner, retaining custom hooks."""
    return (type(plane) is ExternalArtifactPlane and _has_stock_artifact_plane_state(plane)
        and all(getattr(type(plane), name) is original for name, original in _STOCK_BATCH_WRITE_METHODS))


def _has_stock_artifact_plane_state(plane):
    """Own the complete stock instance layout used by bounded read selectors.

    Scheduling fields are ordinary engine state, not custom custody hooks.
    Keep this roster with the constructor instead of copying it into each API
    and consumer. This selects an optimization; it proves no bytes or access.
    """
    fields = {'root', 'validators', 'semantic_validations', 'custody_limits',
        'maximum_parallel_verifications', '_verification_preflight_lock', 'artifact_verification'}
    if type(plane) is _ScopedArtifactPlane:
        fields.add('_read_verification')
    elif type(plane) is not ExternalArtifactPlane:
        return False
    return set(vars(plane)) == fields


def _supports_selected_dependencies(plane):
    return (type(plane) is _ScopedArtifactPlane and plane._read_verification.context_depth
        and _has_stock_manifest_reads(plane) and _has_stock_artifact_plane_state(plane)
        and type(plane.root) is GuardedExternalRoot
        and set(vars(plane.root)) == {'contract', 'inspector'}
        and type(plane.root.inspector) is LocalFilesystemInspector
        and not any(name in vars(plane.root.inspector) for name in ('inspect', 'inspect_bound')))


def verify_read_context_snapshots(*planes):
    """Verify each shared live byte census once at this explicit boundary.

    This retains every context callback and every observed path. Only identical
    stock verification objects share a pass; separate/custom scopes stay eager.
    No result, authority decision or file-stat shortcut survives this call.
    """
    verified = set()
    for plane in planes:
        if (_has_stock_manifest_reads(plane) and _has_stock_artifact_plane_state(plane)
                and isinstance(plane, _ScopedArtifactPlane)):
            plane.require_active_verification_scope()
            key = id(plane._read_verification)
            if key in verified:
                continue
            verified.add(key)
        plane.require_verification_snapshot()
