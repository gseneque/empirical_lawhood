# SPDX-License-Identifier: MPL-2.0
"""Durable first-entry barriers for a selected Matrix root and allocation.

These operational markers grant no scientific authority. A caller must finish
both publications before entering a native contact. Existing or partial markers
refuse entry, including when a competing caller selected another destination.
Historical guard bytes remain readable and are never overwritten.
"""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.kernel.serialization import (
    canonical_json_bytes, validate_relative_locator, validate_sha256, validate_stable_id,
)


def _parent_barriers(root: Path, path: Path) -> None:
    relative = path.parent.relative_to(root)
    current = root
    for part in relative.parts:
        child = current / part
        child.mkdir(exist_ok=True)
        ExternalArtifactPlane._fsync_directory(current)
        current = child
    ExternalArtifactPlane._fsync_directory(current)


def _exclusive_control(root: Path, path: Path, payload: bytes) -> None:
    pending = path.with_name('.' + path.name + '.pending')
    if path.exists() or pending.exists():
        raise FileExistsError('Existing or partial Matrix entry barrier requires retained inspection')
    _parent_barriers(root, path)
    # The infrastructure owner supplies exclusive creation, file fsync and
    # Linux atomic no-replace publication. Keep an interrupted staged marker;
    # do not turn uncertainty into automatic permission to retry.
    ExternalArtifactPlane._write_staged_bytes(pending, payload, retain_on_error=True)
    ExternalArtifactPlane._rename_noreplace(pending, path)
    ExternalArtifactPlane._fsync_directory(path.parent)


def publish_entry_guards(*, plane: ExternalArtifactPlane, entry_ledger_relative_root: str,
                         selected_destination: str, root_id: str, allocation_sha256: str,
                         prepared_packet_sha256: str, prepared_review_sha256: str):
    """Publish both exact barriers durably; return only after directory sync.

    No callback, native service, producer, recovery or retry is constructed.
    Any publication exception prevents the caller's subsequent first contact.
    A committed global marker deliberately survives a failed local publication.
    """
    if type(plane) is not ExternalArtifactPlane:
        raise TypeError('Matrix entry barriers require the actual guarded artifact plane')
    for value in (entry_ledger_relative_root, selected_destination):
        validate_relative_locator(value)
    validate_stable_id(root_id)
    for value in (allocation_sha256, prepared_packet_sha256, prepared_review_sha256):
        validate_sha256(value)
    root = plane.root.verify(for_write=True)
    global_relative = (entry_ledger_relative_root + '/' + root_id + '.' + allocation_sha256
                       + '.entry.begin.json')
    local_relative = selected_destination + '/entry.begin.json'
    global_path = plane.root.resolve(global_relative, for_write=True)
    local_path = plane.root.resolve(local_relative, for_write=True)
    if global_path == local_path:
        raise ValueError('Global and destination Matrix barriers must be distinct')
    for path in (global_path, local_path):
        if path.exists() or path.with_name('.' + path.name + '.pending').exists():
            raise FileExistsError('Existing or partial Matrix entry barrier requires retained inspection')
    global_raw = canonical_json_bytes(dict(root_id=root_id, allocation_sha256=allocation_sha256,
        prepared_packet_sha256=prepared_packet_sha256, selected_destination=selected_destination,
        scope='ONE_ROOT_PER_SEALED_ALLOCATION;COMPLETED_OR_UNKNOWN_REQUIRES_RETAINED_INSPECTION'))
    local_raw = canonical_json_bytes(dict(prepared_packet_sha256=prepared_packet_sha256,
        prepared_review_sha256=prepared_review_sha256,
        scope='ONE_AUTHORIZED_FIRST_ENTRY;NO_AUTOMATIC_REPLAY'))
    _exclusive_control(root, global_path, global_raw)
    _exclusive_control(root, local_path, local_raw)
    return tuple(dict(relative_path=relative, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
                 for relative, raw in ((global_relative, global_raw), (local_relative, local_raw)))
