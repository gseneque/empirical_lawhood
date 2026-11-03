# SPDX-License-Identifier: MPL-2.0
"""Copy an explicit published custody closure without relabeling its records.

The caller selects the authorized original publications and actual destination
mount. The logical storage namespace remains unchanged; an operational receipt
records its distinct physical replica. No scientific or authority record is
rewritten, and this owner never discovers or copies a whole source bank.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import stat

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import (
    MAX_ARTIFACT_MANIFEST_BYTES, bounded_file_sha256, copy_bounded_file, read_bounded_bytes,
)
from empirical_lawhood.infrastructure.file_locks import exclusive_file_lock
from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
from empirical_lawhood.infrastructure.repository_identity import _descriptor_identity
from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ExternalRootContract


@dataclass(frozen=True, slots=True)
class ReplicaFile:
    relative_path: str
    size_bytes: int
    sha256: str

    def __post_init__(self):
        validate_relative_locator(self.relative_path)
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("replica files require an exact nonnegative size")
        validate_sha256(self.sha256, field_name="replica source digest")

    def to_mapping(self):
        return {"relative_path": self.relative_path, "size_bytes": self.size_bytes, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class ArtifactReplicaReceipt:
    source_contract: ExternalRootContract
    target_contract: ExternalRootContract
    files: tuple[ReplicaFile, ...]
    publication_commit_paths: tuple[str, ...]
    receipt_path: Path

    def to_mapping(self):
        return {"schema": "empirical-lawhood/operational/artifact-replica", "version": "1.0.0",
            "status": "COMPLETE", "source_contract": self.source_contract.to_document(),
            "target_contract": self.target_contract.to_document(),
            "files": [member.to_mapping() for member in self.files],
            "publication_commit_paths": list(self.publication_commit_paths),
            "total_bytes": sum(member.size_bytes for member in self.files),
            "canonical_records": "UNCHANGED_ORIGINAL_BYTES_AND_STORAGE_NAMESPACE",
            "scientific_qualification": "NOT_ESTABLISHED", "execution_authority": "NONE"}


def _sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def replicate_artifact_publications(source_plane: ExternalArtifactPlane, target_root: GuardedExternalRoot, *,
        publications: tuple[ArtifactManifest, ...], supplemental_files: tuple[ReplicaFile, ...] = (),
        receipt_path: Path, maximum_bytes: int, maximum_files: int,
        require_current=None, before_complete=None, resume: bool = False) -> ArtifactReplicaReceipt:
    """Copy a selected closure, optionally resuming its exact retained copy plan.

    Resume requires the same source, destination, complete census and bounds.
    Every existing destination is rehashed. Only matching complete files are
    reused; a changed file or foreign path refuses. The derived progress file
    beside the selected receipt is an operational plan, never a completion.
    """
    if type(resume) is not bool:
        raise TypeError('artifact replica resume selection must be boolean')
    options = dict(publications=publications, supplemental_files=supplemental_files,
        receipt_path=receipt_path, maximum_bytes=maximum_bytes, maximum_files=maximum_files,
        require_current=require_current, before_complete=before_complete, resume=resume)
    if not resume:
        return _replicate_artifact_publications(source_plane, target_root, **options)
    if not isinstance(source_plane, ExternalArtifactPlane) or type(target_root) is not GuardedExternalRoot:
        raise TypeError('artifact replication requires existing guarded artifact owners')
    _require_receipt_location(receipt_path, source_plane.root.verify(for_write=False),
        target_root.verify(for_write=True), existing=True)
    with exclusive_file_lock(receipt_path.with_name(receipt_path.name + '.lock'), blocking=False):
        return _replicate_artifact_publications(source_plane, target_root, **options)


def _require_receipt_location(path, source, target, *, existing):
    if (not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts
            or path.resolve(strict=False) != path or path.is_symlink()
            or not existing and path.exists() or not path.parent.is_dir()
            or path.is_relative_to(source) or path.is_relative_to(target)):
        raise ValueError('artifact replica receipt must be an explicit ordinary path outside both custody roots')


def _durable_bytes(path, payload):
    """Publish a small immutable operational record without partial final bytes."""
    from uuid import uuid4
    temporary = path.with_name(path.name + '.' + uuid4().hex + '.partial')
    with temporary.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path, follow_symlinks=False)
    temporary.unlink()
    _sync_directory(path.parent)


def _replicate_artifact_publications(source_plane, target_root, *, publications, supplemental_files,
        receipt_path, maximum_bytes, maximum_files, require_current, before_complete, resume):
    """Durably copy only complete, explicitly selected original publications.

    The target must be an existing empty guarded directory on its actual mount.
    A successful receipt is written outside both custody roots after complete
    byte verification and publication replay. Failure leaves its partial target
    visible, without a COMPLETE receipt; no original is written or removed.
    Additional nonpublication controls require explicit original size/hash pins.
    A caller with live access requirements supplies their current guard. It is
    refreshed during copying and before the COMPLETE receipt is published.
    The optional final guard checks the caller's larger original read closure
    before completion, without repeating that complete snapshot per copied file.
    """
    if not isinstance(source_plane, ExternalArtifactPlane) or type(target_root) is not GuardedExternalRoot:
        raise TypeError("artifact replication requires existing guarded artifact owners")
    if (type(publications) is not tuple or not publications
            or any(type(value) is not ArtifactManifest for value in publications)
            or type(supplemental_files) is not tuple
            or any(type(value) is not ReplicaFile for value in supplemental_files)):
        raise TypeError("artifact replication requires exact immutable selected publication/file censuses")
    if (type(maximum_bytes) is not int or maximum_bytes <= 0
            or type(maximum_files) is not int or maximum_files <= 0):
        raise ValueError("artifact replication requires explicit positive byte and file bounds")
    if require_current is not None and not callable(require_current):
        raise TypeError('artifact replication requires a callable current-access guard')
    if before_complete is not None and not callable(before_complete):
        raise TypeError('artifact replication requires a callable final custody guard')
    refresh = (lambda: None) if require_current is None else require_current
    refresh()
    if source_plane.root.contract.storage_root_id != target_root.contract.storage_root_id:
        raise ValueError("artifact replication cannot relabel the original logical storage namespace")
    source = source_plane.root.verify(for_write=False)
    target = target_root.verify(for_write=True)
    if source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError("artifact replica roots must be disjoint")
    if not resume and any(target.iterdir()):
        raise ValueError("artifact replica target must be empty; existing files are never overwritten")
    _require_receipt_location(receipt_path, source, target, existing=resume)
    files = {}
    snapshots = {}
    total_bytes = 0

    def add(member):
        nonlocal total_bytes
        member.__post_init__()
        if member.relative_path in files:
            if files[member.relative_path] != member:
                raise ValueError("artifact replica source census contains conflicting pins")
            return
        total_bytes += member.size_bytes
        if len(files) + 1 > maximum_files or total_bytes > maximum_bytes:
            raise ValueError("artifact replica closure exceeds its explicit file or byte bound")
        path = source_plane.root.resolve(member.relative_path, for_write=False)
        observed = path.lstat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_size != member.size_bytes:
            raise ValueError("artifact replica source file differs from its regular exact-size pin")
        files[member.relative_path] = member
        snapshots[member.relative_path] = _descriptor_identity(observed)

    batches = {}
    for selected in publications:
        refresh()
        selected.__post_init__()
        if selected.materialization.storage_root_id != source_plane.root.contract.storage_root_id:
            raise ValueError("artifact replica selection belongs to another source storage namespace")
        actual = source_plane.read_manifest(selected.materialization.relative_path)
        if (actual.logical != selected.logical or actual.materialization != selected.materialization
                or selected.publication is not None and selected.publication != actual.publication):
            raise ValueError("artifact replica selection differs from its original sidecar")
        if actual.publication is None:
            raise ValueError("artifact replica requires exact committed publication custody")
        batch = actual.publication
        if batch.publication_batch_id in batches:
            if batches[batch.publication_batch_id].publication != batch:
                raise ValueError("artifact replica substitutes a previously selected publication batch")
            continue
        actual = read_publication_metadata(source_plane, actual)
        batches[batch.publication_batch_id] = actual
        add(ReplicaFile(batch.commit_marker_relative_path, batch.commit_marker_size_bytes, batch.commit_marker_sha256))
        for member in batch.members:
            add(ReplicaFile(member.relative_path, member.size_bytes, member.physical_sha256))
            relative = member.relative_path + ".manifest.json"
            sidecar = source_plane.root.resolve(relative, for_write=False)
            size, checksum = bounded_file_sha256(sidecar,
                maximum_bytes=source_plane.custody_limits.manifest_bytes or MAX_ARTIFACT_MANIFEST_BYTES)
            add(ReplicaFile(relative, size, checksum))
    for member in supplemental_files:
        add(member)
    receipt = ArtifactReplicaReceipt(source_plane.root.contract, target_root.contract,
        tuple(files[name] for name in sorted(files)),
        tuple(sorted(value.publication.commit_marker_relative_path for value in batches.values())), receipt_path)
    payload = json.dumps(receipt.to_mapping(), sort_keys=True, separators=(",", ":")).encode() + b"\n"
    partials, retained = {}, set()
    if resume:
        plan = {**receipt.to_mapping(), 'status': 'IN_PROGRESS',
            'maximum_bytes': maximum_bytes, 'maximum_files': maximum_files}
        plan_bytes = json.dumps(plan, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        progress = receipt_path.with_name(receipt_path.name + '.progress.json')
        if progress.exists() or progress.is_symlink():
            if read_bounded_bytes(progress, maximum_bytes=len(plan_bytes)) != plan_bytes:
                raise ValueError('artifact replica resume changes its exact copy plan')
        else:
            if any(target.iterdir()) or receipt_path.exists():
                raise ValueError('artifact replica resume requires its original retained copy plan')
            _durable_bytes(progress, plan_bytes)
        suffix = '.replica-' + sha256(plan_bytes).hexdigest() + '.partial'
        partials = {name: name + suffix for name in files}
        if set(partials.values()) & files.keys():
            raise ValueError('artifact replica source aliases a partial-copy path')
        allowed_directories = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
        for path in target.rglob('*'):
            name = path.relative_to(target).as_posix()
            if path.is_symlink():
                raise ValueError('artifact replica resume refuses linked destination members')
            if path.is_dir() and name in allowed_directories:
                continue
            if not path.is_file() or name not in files and name not in partials.values():
                raise ValueError('artifact replica resume refuses an unexpected destination member')
        for name, member in files.items():
            refresh()
            destination = target_root.resolve(name, for_write=False)
            if destination.exists():
                if bounded_file_sha256(destination, maximum_bytes=member.size_bytes) != (member.size_bytes, member.sha256):
                    raise ValueError('artifact replica resume changes a completed destination file')
                retained.add(name)
        if receipt_path.exists() and read_bounded_bytes(receipt_path, maximum_bytes=len(payload)) != payload:
            raise ValueError('artifact replica resume changes its complete receipt')
    target_root.verify(for_write=True, operation_minimum_free_bytes=sum(files[name].size_bytes for name in files if name not in retained))
    if not resume and any(target.iterdir()):
        raise ValueError("artifact replica target changed before copy admission")
    directories = {target}
    for name in sorted(files):
        refresh()
        member = files[name]
        original = source_plane.root.resolve(name, for_write=False)
        if _descriptor_identity(original.lstat()) != snapshots[name]:
            raise ValueError("artifact replica source changed before its copy")
        destination = target_root.resolve(name, for_write=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        for directory in (destination.parent, *destination.parent.parents):
            if directory == target:
                break
            directories.add(directory)
        temporary = target_root.resolve(partials[name], for_write=True) if resume else destination
        if resume and temporary.exists():
            # The exact retained plan owns this interrupted, unpublished copy.
            # It can never replace a completed destination or an original.
            temporary.unlink()
        if name not in retained:
            size, checksum = copy_bounded_file(original, temporary, maximum_bytes=member.size_bytes)
            if (size, checksum) != (member.size_bytes, member.sha256):
                raise ValueError("artifact replica bytes differ from their exact original pin")
            descriptor = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if resume:
                if bounded_file_sha256(temporary, maximum_bytes=member.size_bytes) != (member.size_bytes, member.sha256):
                    raise ValueError('artifact replica partial copy changed before publication')
                os.link(temporary, destination, follow_symlinks=False)
                temporary.unlink()
                _sync_directory(destination.parent)
        if bounded_file_sha256(destination, maximum_bytes=member.size_bytes) != (member.size_bytes, member.sha256):
            raise ValueError("artifact replica destination changed before custody replay")
        refresh()
    for directory in sorted(directories, key=lambda value: len(value.parts), reverse=True):
        _sync_directory(directory)
    target_plane = ExternalArtifactPlane(target_root, source_plane.validators, source_plane.semantic_validations,
        custody_limits=source_plane.custody_limits, artifact_verification=source_plane.artifact_verification)
    for actual in batches.values():
        refresh()
        read_publication_metadata(source_plane, actual)
        read_publication_metadata(target_plane, actual)
    if before_complete is not None:
        before_complete()
    allowed_directories = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    for path in target.rglob('*'):
        name = path.relative_to(target).as_posix()
        if (path.is_symlink() or not (path.is_file() and name in files
                or path.is_dir() and name in allowed_directories)):
            raise ValueError('artifact replica complete destination census changed during copying')
    for name in files:
        original = source_plane.root.resolve(name, for_write=False)
        if _descriptor_identity(original.lstat()) != snapshots[name]:
            raise ValueError("artifact replica original custody changed during copying")
        refresh()
        member = files[name]
        for current in (original, target_root.resolve(name, for_write=False)):
            if bounded_file_sha256(current, maximum_bytes=member.size_bytes) != (member.size_bytes, member.sha256):
                raise ValueError('artifact replica complete byte census changed before completion')
    refresh()
    if resume and receipt_path.exists():
        if read_bounded_bytes(receipt_path, maximum_bytes=len(payload)) != payload:
            raise ValueError('artifact replica complete receipt changed before return')
    else:
        _durable_bytes(receipt_path, payload)
    return receipt


__all__ = ["ArtifactReplicaReceipt", "ReplicaFile", "replicate_artifact_publications"]
