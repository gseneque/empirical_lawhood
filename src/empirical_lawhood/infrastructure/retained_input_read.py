# SPDX-License-Identifier: MPL-2.0
"""Bounded sealed-input reuse inside an existing, effect-free custody read.

Ordinary worker delivery keeps its fresh open_many boundary. This owner only
borrows an active read context, whose final byte checks remain mandatory.
Every reuse checks the exact binding and invokes live member access callbacks.
"""
from contextlib import contextmanager

from .artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, _has_stock_manifest_reads, _worker_input_requests
from empirical_lawhood.runtime.artifacts import ArtifactManifest


class RetainedInputRead:
    def __init__(self, writer, *, shared_artifact_ids, maximum_bytes=64 * 1024**2, maximum_members=64):
        if (type(maximum_bytes) is not int or maximum_bytes < 0
                or type(maximum_members) is not int or maximum_members < 0):
            raise ValueError('retained input read requires nonnegative byte and member bounds')
        writer.require_active_verification_scope()
        self.writer = writer
        self.shared = frozenset(shared_artifact_ids)
        self.maximum_bytes, self.maximum_members = maximum_bytes, maximum_members
        self._retained = {}
        self._bytes = 0
        self._active = False

    def _require_active(self):
        if not self._active:
            raise RuntimeError('retained input read lifetime has ended')
        self.writer.require_active_verification_scope()
        verification = getattr(self.writer, '_read_verification', None)
        return bool(verification is not None and verification.context_depth
            and _has_stock_manifest_reads(self.writer)
            and getattr(self.writer.open_many, '__func__', None) is ExternalArtifactPlane.open_many)

    def __enter__(self):
        if self._active:
            raise RuntimeError('retained input read is already active')
        self._active = True
        try:
            self._require_active()
        except BaseException:
            self._active = False
            raise
        return self

    def __exit__(self, *args):
        self._active = False
        for _, _, port in self._retained.values():
            port.close()
        self._retained.clear()
        self._bytes = 0

    def retained_manifest(self, port):
        if not self._require_active():
            return None
        entry = self._retained.get(port.materialization_id)
        if entry is None:
            return None
        value, binding, _ = entry
        if binding != port.binding:
            raise ArtifactIdentityConflict('retained input changes its exact port binding')
        return ArtifactManifest(value.logical, value.materialization)

    def _open_fresh(self, values, *, bindings, maximum_bytes):
        if not self._require_active():
            return self.writer.open_many(values, bindings=bindings, maximum_bytes=maximum_bytes)
        requested = _worker_input_requests(values, bindings, maximum_bytes)
        # Authenticate each complete sibling publication in the existing read
        # context. Then seal only the exact selected members. Ordinary worker
        # open_many deliberately keeps its independent eager batch guards.
        manifests = self.writer.verify_manifests_members(
            tuple(ArtifactManifest(value.logical, value.materialization) for value in values),
            validate_members=lambda members: tuple(members[value.materialization.relative_path] for value in values))
        ports = []
        try:
            for manifest in manifests:
                binding, limit = requested[manifest.materialization.relative_path]
                ports.append(self.writer._verify_manifest_snapshot(manifest, binding=binding, maximum_bytes=limit,
                    member_preflights=self.writer._read_verification.member_preflights))
            self._require_active()
            return tuple(ports)
        except BaseException:
            for port in ports:
                port.close()
            raise

    @contextmanager
    def open_many(self, values, *, bindings, maximum_bytes):
        reuse = self._require_active()
        _worker_input_requests(values, bindings, maximum_bytes)
        selected, missing, cached = {}, [], []
        for index, (value, binding) in enumerate(zip(values, bindings, strict=True)):
            entry = self._retained.get(binding.materialization_id) if reuse else None
            if entry is None:
                missing.append((index, value, binding))
            else:
                original, previous, port = entry
                if original != value or previous != binding:
                    raise ArtifactIdentityConflict('retained input changes exact bytes, binding or access')
                cached.append(ArtifactManifest(value.logical, value.materialization))
                selected[index] = port
        # Current access is never represented by a cached descriptor. The
        # owning read context retains its whole observed-file exit guard.
        if cached:
            self.writer.verify_manifests(tuple(cached))
        self._require_active()
        created, cursors, kept = (), [], set()
        try:
            if missing:
                created = self._open_fresh(tuple(value for _, value, _ in missing),
                    bindings=tuple(binding for _, _, binding in missing), maximum_bytes=maximum_bytes)
            fresh = {}
            for (index, value, binding), port in zip(missing, created, strict=True):
                size = value.materialization.size_bytes
                if (reuse and binding.artifact_id in self.shared
                        and len(self._retained) < self.maximum_members
                        and self._bytes + size <= self.maximum_bytes):
                    if binding.materialization_id in self._retained:
                        raise ArtifactIdentityConflict('retained input repeats its materialization identity')
                    self._retained[binding.materialization_id] = value, binding, port
                    self._bytes += size
                    kept.add(id(port))
                    selected[index] = port
                else:
                    fresh[index] = port
            for index, port in selected.items():
                cursor = port.cursor()
                cursors.append(cursor)
                fresh[index] = cursor
            yield tuple(fresh[index] for index in range(len(values)))
        finally:
            for port in cursors:
                port.close()
            for port in created:
                if id(port) not in kept:
                    port.close()
