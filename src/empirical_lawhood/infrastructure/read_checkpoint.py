# SPDX-License-Identifier: MPL-2.0
"""Persistable exact byte facts from a finite read, never access decisions."""

from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar

from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256

_observations = ContextVar('completed_read_checkpoint_observations', default=())


class CompletedReadCheckpoints:
    """Facts from independently owned reads of one selected physical root."""

    def __init__(self, root, observe_manifest):
        self.root, self.observe_manifest = root, observe_manifest
        self.files = {}

    def include(self, plane):
        if plane.root.contract != self.root:
            return
        verification = getattr(plane, '_read_verification', None)
        if verification is None or not verification.active:
            raise PermissionError('completed read checkpoint escaped its finite custody owner')
        root = Path(self.root.canonical_path)
        for path, value in verification.snapshots.items():
            name = path.relative_to(root).as_posix()
            pin = (value[2], value[5])
            if self.files.setdefault(name, pin) != pin:
                raise PermissionError('independent read checkpoints disagree on original consumed bytes')


@contextmanager
def completed_read_checkpoints(root, *, observe_manifest):
    """Collect original facts after each independent reader's own final guard."""
    observed = CompletedReadCheckpoints(root, observe_manifest)
    token = _observations.set((*_observations.get(), observed))
    try:
        yield observed
    finally:
        _observations.reset(token)
        observed.files.clear()


def observe_completed_read(plane):
    """Infrastructure callback, only after the owning final full byte check."""
    for observation in _observations.get():
        observation.include(plane)


def observe_checkpoint_manifest(plane, manifest):
    for observation in _observations.get():
        if plane.root.contract == observation.root:
            observation.observe_manifest(manifest)


def verified_read_file_pins(plane):
    """Seal every consumed file after the owning complete byte/access guard."""
    plane.require_full_verification_snapshot()
    verification = getattr(plane, '_read_verification', None)
    if verification is None or not verification.active:
        raise PermissionError('read checkpoint requires an active authenticated read')
    root = Path(plane.root.contract.canonical_path)
    return tuple((path.relative_to(root).as_posix(), value[2], value[5])
        for path, value in sorted(verification.snapshots.items()))


def authenticate_read_file_pins(plane, pins, *, require_current):
    """Reauthenticate saved facts inside a new ordinary finite read lifetime.

    The caller must establish actual current access before invoking this owner.
    Rehydrated byte facts join the new scope's complete final mutation guard.
    They do not replace publication, execution, source or scientific joins.
    """
    plane.require_active_verification_scope()
    verification = plane._read_verification
    require_current()
    root = Path(plane.root.contract.canonical_path)
    previous = None
    for row in pins:
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise ValueError('read checkpoint requires exact file pins')
        name, size, digest = row
        validate_relative_locator(name)
        validate_sha256(digest)
        if type(size) is not int or size < 0 or previous is not None and name <= previous:
            raise ValueError('read checkpoint changes its sorted unique file census')
        previous = name
        retained = verification.snapshots.get(root / name)
        if retained is not None:
            if (retained[2], retained[5]) != (size, digest):
                raise PermissionError('read checkpoint changes previously authenticated bytes')
            # No body is opened here. The same live read already authenticated
            # it, and its complete final byte guard still owns this path.
            plane._track_verification_snapshot(root / name, verification.snapshots,
                expected_sha256=digest, maximum_bytes=size)
            continue
        require_current()
        path = plane.root.resolve(name, for_write=False)
        if bounded_file_sha256(path, maximum_bytes=size) != (size, digest):
            raise PermissionError('read checkpoint changes original consumed bytes')
        plane._track_verification_snapshot(path, verification.snapshots,
            expected_sha256=digest, maximum_bytes=size)
    require_current()


__all__ = ['authenticate_read_file_pins', 'verified_read_file_pins', 'completed_read_checkpoints']
