# SPDX-License-Identifier: MPL-2.0
"""One actual typed parse, with ordinary closed custody and custom policies."""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import sys
import threading
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure import artifact_validation
from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record
from empirical_lawhood.infrastructure.publication_metadata import read_published_canonical_record
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_bytes_with_identity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import (
    ArtifactCustodyLimits, ArtifactProfile, ArtifactSemanticValidation, ArtifactWriteRequest, ArtifactWriteResult,
)
from tests.runtime_platform.test_artifact_verification_scope import _publication


@dataclass(frozen=True, slots=True)
class LargeControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/large-typed-control'
    rows: tuple[str, ...]


@contextmanager
def _work(raw):
    counts = Counter()
    def observe(frame, event, arg):
        if event != 'call':
            return
        if frame.f_code is json.loads.__code__ and frame.f_locals['s'] in (raw, raw.decode()):
            counts['body_parses'] += 1
        elif frame.f_code is CanonicalRecord.canonical_equals.__code__:
            if type(frame.f_locals['self']) is ObjectIdentity:
                counts['typed_comparisons'] += 1
    prior = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(prior)


def _read(plane, manifest):
    return read_verified_canonical_record(plane, manifest, ObjectIdentity,
        maximum_bytes=manifest.materialization.size_bytes)


@pytest.mark.parametrize('damage', (None, 'publication', 'logical', 'material', 'sibling', 'revoked'))
def test_cold_receipt_control_resolves_complete_publication(tmp_path, damage):
    """A receipt supplies logical/material custody; the sidecar owns siblings."""
    from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.runtime.artifacts import ArtifactManifest
    plane, manifests = _publication(tmp_path, 3)
    actual = manifests[0]
    selected = ArtifactManifest(actual.logical, actual.materialization)
    if damage == 'publication':
        selected = replace(actual, publication=replace(actual.publication, commit_marker_sha256='f' * 64))
    elif damage == 'logical':
        selected = replace(selected, logical=replace(actual.logical, content_sha256='f' * 64))
    elif damage == 'material':
        selected = replace(selected, materialization=replace(actual.materialization, size_bytes=actual.materialization.size_bytes + 1))
    elif damage == 'sibling':
        path = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
        path.write_bytes(b'[' + path.read_bytes()[1:])

    def access(_):
        if damage == 'revoked':
            raise PermissionError('original access revoked')

    def read():
        with plane.read_context(before_member=access) as reading:
            return CurrentResultPlanReader(reading).read_control(selected, ObjectIdentity, selected.materialization.size_bytes)

    if damage is None:
        assert read().object_id == 'exposed.subject.0'
    else:
        with pytest.raises((ValueError, RuntimeError, PermissionError)):
            read()


def test_one_body_parse_and_comparison_preserve_exact_identity(tmp_path, record_property):
    plane, manifests = _publication(tmp_path, 4)
    manifest = manifests[0]
    raw = plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes()
    with _work(raw) as before:
        plane.verify_manifest(manifest)
        old = decode_canonical_bytes(raw, ObjectIdentity, maximum_bytes=len(raw))
        assert old.canonical_equals(raw)
        assert old.fingerprint() == sha256(raw).hexdigest()
    with plane.read_context() as reading:
        with _work(raw) as after:
            current = _read(reading, manifest)
        assert current == old
        assert current._canonical_fingerprint == sha256(raw).hexdigest()
        assert reading.verified_canonical_header(manifest).schema == ObjectIdentity.SCHEMA
    assert before == {'body_parses': 2, 'typed_comparisons': 2}
    assert after == {'body_parses': 1, 'typed_comparisons': 1}
    record_property('before', dict(before))
    record_property('combined', dict(after))


@pytest.mark.parametrize('damage', ('sibling', 'selected', 'sidecar', 'marker', 'revoked'))
def test_combined_read_keeps_complete_custody_and_current_access(tmp_path, damage):
    plane, manifests = _publication(tmp_path, 3)
    allowed = True
    def access(manifest):
        if not allowed:
            raise PermissionError('actual access revoked')
    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        with plane.read_context(before_member=access) as reading:
            _read(reading, manifests[0])
            if damage == 'revoked':
                allowed = False
            else:
                relative = (manifests[-1].materialization.relative_path if damage == 'sibling'
                    else manifests[0].materialization.relative_path if damage == 'selected'
                    else manifests[0].materialization.relative_path + '.manifest.json' if damage == 'sidecar'
                    else manifests[0].publication.commit_marker_relative_path)
                path = plane.root.resolve(relative, for_write=False)
                raw = path.read_bytes()
                path.write_bytes(b'[' + raw[1:])
            _read(reading, manifests[0])


@pytest.mark.parametrize('policy', ('registry', 'reader', 'token-bound'))
def test_custom_and_explicit_streaming_policies_keep_original_validation(tmp_path, monkeypatch, policy):
    plane, manifests = _publication(tmp_path, 1)
    manifest = manifests[0]
    raw = plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes()
    hooks = []
    if policy == 'registry':
        registry = artifact_validation.ArtifactProfileValidatorRegistry
        original = registry.validate_file
        def validate(self, *args, **kwargs):
            hooks.append('format')
            return original(self, *args, **kwargs)
        monkeypatch.setattr(registry, 'validate_file', validate)
    elif policy == 'reader':
        verify = plane.verify_manifest
        def custom(*args, **kwargs):
            hooks.append('reader')
            return verify(*args, **kwargs)
        plane.verify_manifest = custom
    else:
        plane.custody_limits = ArtifactCustodyLimits(canonical_json_token_bytes=4)
        with pytest.raises((ValueError, RuntimeError)):
            _read(plane, manifest)
        return
    with _work(raw) as counts:
        assert _read(plane, manifest).canonical_bytes() == raw
    assert hooks and counts['body_parses'] == 2


@pytest.mark.parametrize('damage', ('space', 'duplicate', 'schema', 'unknown', 'float', 'integer', 'decimal'))
def test_combined_format_and_typed_rejection_parity(tmp_path, damage):
    plane, manifests = _publication(tmp_path, 1)
    manifest = manifests[0]
    raw = plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes()
    if damage == 'space':
        raw = b' ' + raw
    elif damage == 'duplicate':
        raw = raw.replace(b'{', b'{"schema":"duplicate",', 1)
    elif damage == 'schema':
        raw = raw.replace(ObjectIdentity.SCHEMA.encode(), b'empirical-lawhood/testing/wrong', 1)
    elif damage == 'unknown':
        raw = raw.replace(b'"value":{', b'"value":{"extra":1,')
    elif damage == 'float':
        raw = raw.replace(b'"object_id":"exposed.subject.0"', b'"object_id":1.25')
    elif damage == 'integer':
        raw = raw.replace(b'"object_id":"exposed.subject.0"', b'"object_id":' + b'1' * 129)
    else:
        raw = raw.replace(b'"object_id":"exposed.subject.0"', b'"object_id":{"decimal":"1.00"}')
    logical = manifest.logical
    request = ArtifactWriteRequest(logical.logical_artifact_id, 'invalid/input.json', logical.payload_schema,
        logical.profile, logical.media_type, 'exposed.invalid', 'invalid', raw,
        logical.visibility_ceiling, logical.parent_visibility_ceilings, logical.outcome_access)
    with pytest.raises((TypeError, ValueError, RuntimeError)):
        plane.validators.validate(request)
        decode_canonical_bytes(raw, ObjectIdentity, maximum_bytes=len(raw))
    with pytest.raises((TypeError, ValueError, RuntimeError)):
        plane.validators.decode_canonical_record(raw, request, ObjectIdentity)


def test_exact_original_sidecar_and_custom_materialization_checks(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path, 1)
    manifest = manifests[0]
    relative = manifest.materialization.relative_path + '.manifest.json'
    raw = plane.root.resolve(relative, for_write=False).read_bytes()
    sidecar = plane._manifest_materialization(logical_artifact_id=manifest.logical.logical_artifact_id,
        relative_path=relative, payload=raw)
    publication = ArtifactWriteResult(manifest.logical, manifest.materialization, sidecar, False)
    assert read_published_canonical_record(plane, publication, ObjectIdentity).object_id == 'exposed.subject.0'
    with pytest.raises(ValueError, match='sidecar'):
        read_published_canonical_record(plane, replace(publication,
            manifest_materialization=replace(sidecar, physical_sha256='b' * 64)), ObjectIdentity)
    calls = []
    verify = plane.verify
    def custom(value):
        calls.append(value)
        verify(value)
    monkeypatch.setattr(plane, 'verify', custom)
    read_published_canonical_record(plane, publication, ObjectIdentity)
    assert sidecar in calls


def test_combined_read_keeps_registered_semantic_constraints(tmp_path):
    plane, manifests = _publication(tmp_path, 1)
    manifest = manifests[0]
    raw = plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes()
    semantic = ArtifactSemanticValidation('validator.exposed-shape', '1.0.0', 'a' * 64,
        ObjectIdentity.SCHEMA, ArtifactProfile.CANONICAL_JSON, ('schema', 'value', 'version'),
        ('object_fingerprint', 'object_id', 'object_schema', 'object_version'), (('version', '2.0.0'),))
    request = ArtifactWriteRequest('exposed.wrong-version', 'invalid/member.json', ObjectIdentity.SCHEMA,
        manifest.logical.profile, manifest.logical.media_type, 'exposed.invalid', 'invalid', raw,
        manifest.logical.visibility_ceiling, (), manifest.logical.outcome_access, semantic_validation=semantic)
    with pytest.raises(artifact_validation.ArtifactIdentityConflict, match='version'):
        plane.validators.decode_canonical_record(raw, request, ObjectIdentity)


def test_identity_result_does_not_seed_a_custom_encoding_policy():
    @dataclass(frozen=True, slots=True)
    class Custom(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/custom-identity-policy'
        value: int

        def canonical_equals(self, payload):
            # An explicitly custom comparison is never a stock identity proof.
            return True

    raw = b'{"schema":"empirical-lawhood/testing/custom-identity-policy","value":{"value":1},"version":"1.0.0"}\n '
    result = decode_canonical_bytes_with_identity(raw, Custom, maximum_bytes=len(raw))
    assert result.content_sha256 == sha256(raw).hexdigest()
    assert result.record.fingerprint() != result.content_sha256


def test_parallel_member_validation_uses_the_same_selected_typed_read(tmp_path):
    from empirical_lawhood.kernel import decoding
    plane, _ = _publication(tmp_path, 1)
    value = LargeControl(('disclosed metadata ' * 32,) * 2048)
    assert len(value.canonical_bytes()) >= 1024**2
    original = plane.read_manifest('outputs/member-0.json').logical
    result = plane.write(ArtifactWriteRequest('exposed.large-control', 'large/control.json', value.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.large', 'large', value.canonical_bytes(),
        original.visibility_ceiling, (), original.outcome_access))
    manifest = plane.read_manifest(result.materialization.relative_path)
    plane.maximum_parallel_verifications = 8
    decoded_threads = []
    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is decoding._decode_canonical_bytes.__code__:
            if frame.f_locals['record_type'] is LargeControl:
                decoded_threads.append(threading.get_ident())
    prior = threading.getprofile()
    threading.setprofile(observe)
    try:
        with plane.read_context() as reading, reading.verification_dependencies() as dependencies:
            actual = read_verified_canonical_record(reading, manifest, LargeControl,
                maximum_bytes=manifest.materialization.size_bytes)
            assert actual == value
            dependencies.require_current(force_full=True)
            assert len(dependencies.paths) == 3
    finally:
        threading.setprofile(prior)
    assert len(decoded_threads) == 1 and decoded_threads[0] != threading.get_ident()
