# SPDX-License-Identifier: MPL-2.0
"""One bounded typed read inside the ordinary complete publication owner.

Only exact stock canonical controls can combine their format and typed passes.
Other members, custom readers and explicit streaming limits keep their original
verification. Selection and accepted values expire with this synchronous call.
"""
from contextvars import ContextVar
from dataclasses import dataclass
from types import SimpleNamespace

from empirical_lawhood.kernel.decoding import decode_canonical_bytes_with_identity
from empirical_lawhood.kernel.decoded_record_store import current_decoded_record_store, record_store_key
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec

from .artifact_validation import (
    ArtifactIdentityConflict, ArtifactProfileValidatorRegistry, _CANONICAL_C_DECODE_BYTES,
)
from .bounded_io import BoundedFileIOError, read_bounded_bytes

_selected = ContextVar('selected_canonical_record_read', default=None)
_RECORD_METHODS = tuple((name, getattr(CanonicalRecord, name)) for name in (
    'canonical_bytes', 'canonical_chunks', 'canonical_equals', '_encoding', '_is_cacheable', 'fingerprint'))
_VALIDATOR_METHODS = tuple((name, getattr(ArtifactProfileValidatorRegistry, name)) for name in (
    'validate', 'validate_file', 'decode_canonical_record', 'require_generic_validation'))


def _eligible(plane, manifest, record_type):
    from .artifacts import _has_stock_manifest_reads, _has_stock_artifact_plane_state

    logical, material, limits = manifest.logical, manifest.materialization, plane.custody_limits
    return (_has_stock_manifest_reads(plane) and _has_stock_artifact_plane_state(plane)
        and type(plane.validators) is ArtifactProfileValidatorRegistry
        and all(getattr(type(plane.validators), name) is method for name, method in _VALIDATOR_METHODS)
        and all(getattr(record_type, name) is method for name, method in _RECORD_METHODS)
        and logical.profile is ArtifactProfile.CANONICAL_JSON and logical.media_type == 'application/json'
        and logical.payload_schema == record_type.SCHEMA and material.compression == 'none'
        and material.partition_selector is None and material.size_bytes <= _CANONICAL_C_DECODE_BYTES
        and limits.canonical_json_token_bytes is None and limits.canonical_json_depth is None
        and not limits.exceeds('in_memory_payload_bytes', material.size_bytes)
        and resolve_storage_codec(plane.validators._binary_codecs, payload_schema=logical.payload_schema,
            profile=logical.profile, media_type=logical.media_type) is None)


@dataclass(slots=True)
class _SelectedCanonicalRecordRead:
    plane: object
    manifest: ArtifactManifest
    record_type: type[CanonicalRecord]
    accepted: object = None
    header: object = None

    def decode(self, payload):
        logical = self.manifest.logical
        request = SimpleNamespace(profile=logical.profile, payload_schema=logical.payload_schema,
            media_type=logical.media_type, semantic_validation=logical.semantic_validation)
        header, accepted = self.plane.validators.decode_canonical_record(payload, request, self.record_type,
            custody_limits=self.plane.custody_limits, expected_sha256=self.manifest.materialization.physical_sha256)
        _require_identity(self.manifest, accepted)
        self.header, self.accepted = header, accepted
        return header


def current_canonical_record_read(plane, manifest):
    """Select only this call's exact member under the unchanged read policy."""
    selected = _selected.get()
    if (selected is not None and selected.plane is plane and selected.manifest == manifest
            and _eligible(plane, manifest, selected.record_type)):
        return selected
    return None


def _require_identity(manifest, accepted):
    if (accepted.size_bytes != manifest.materialization.size_bytes
            or accepted.content_sha256 != manifest.materialization.physical_sha256
            or accepted.content_sha256 != manifest.logical.content_sha256
            or accepted.record.SCHEMA != manifest.logical.payload_schema):
        raise ArtifactIdentityConflict('typed control changes its exact published canonical bytes')


def read_verified_canonical_record(plane, manifest, record_type, *, maximum_bytes, before_member=None):
    """Read one record, preserving every sibling and ordinary final guard.

    A finite weak store shares live immutable values across reader families.
    Each caller still checks its own complete publication and current access.
    """
    if type(manifest) is not ArtifactManifest or not isinstance(record_type, type) or not issubclass(record_type, CanonicalRecord):
        raise TypeError('typed custody requires an exact manifest and canonical record type')
    size = manifest.materialization.size_bytes
    if maximum_bytes is not None and (type(maximum_bytes) is not int or maximum_bytes <= 0):
        raise ValueError('typed control read requires a positive byte limit')
    if maximum_bytes is not None and size > maximum_bytes:
        raise BoundedFileIOError('bounded input exceeds its byte limit')
    if before_member is not None and not callable(before_member):
        raise TypeError('typed control access callback must be callable')
    options = {} if before_member is None else {'before_member': before_member}

    def payload():
        if before_member is not None:
            before_member(manifest)
        return read_bounded_bytes(plane.root.resolve(manifest.materialization.relative_path, for_write=False),
            maximum_bytes=size)

    if not _eligible(plane, manifest, record_type):
        # Custom hooks and bounded streaming owners retain the original order.
        plane.verify_manifest(manifest, **options)
        accepted = decode_canonical_bytes_with_identity(payload(), record_type, maximum_bytes=size,
            expected_sha256=manifest.materialization.physical_sha256)
        _require_identity(manifest, accepted)
        if accepted.record.fingerprint() != manifest.logical.content_sha256:
            raise ArtifactIdentityConflict('typed control changes its record identity')
        if before_member is not None:
            before_member(manifest)
        return accepted.record

    store = current_decoded_record_store()
    key = None if store is None else record_store_key(record_type, manifest.materialization.physical_sha256, size)
    cached = None if store is None else store.get(key)
    if cached is not None:
        # A different publication may contain identical bytes. Its current
        # registered format, semantic constraints, bounds and entire sibling
        # set still authenticate through the ordinary owner before reuse.
        plane.verify_manifest(manifest, **options)
        if cached.fingerprint() != manifest.logical.content_sha256:
            raise ArtifactIdentityConflict('shared typed record changes its published content identity')
        if before_member is not None:
            before_member(manifest)
        return cached

    selected = _SelectedCanonicalRecordRead(plane, manifest, record_type)
    token = _selected.set(selected)
    try:
        def consume(members):
            actual = members[manifest.materialization.relative_path]
            # Receipts name the exact logical and physical output. Its
            # authenticated sidecar supplies the complete publication binding.
            if (actual.logical != manifest.logical or actual.materialization != manifest.materialization
                    or manifest.publication is not None and actual.publication != manifest.publication):
                raise ArtifactIdentityConflict('typed control changes its complete publication')
            if selected.accepted is None:
                # An earlier consumer may already have authenticated this
                # publication. Reuse its generic proof but still decode the
                # current exact bytes under this call's typed contract.
                selected.decode(payload())
            if before_member is not None:
                before_member(manifest)
            return selected.accepted.record

        record = plane.verify_manifest_members(manifest, validate_members=consume, **options)
        if store is not None:
            store.put(key, record)
        return record
    finally:
        _selected.reset(token)
