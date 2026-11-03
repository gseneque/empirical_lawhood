# SPDX-License-Identifier: MPL-2.0
"""Reuse format work only after actual staged bytes and policy match."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
import sys

import pytest

from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactStreamWriteRequest
from tests.test_artifact_publication_admission import _plane, _requests


@contextmanager
def _validation_work():
    calls = Counter()
    methods = {ArtifactProfileValidatorRegistry.validate.__code__: 'memory',
        ArtifactProfileValidatorRegistry.validate_file.__code__: 'file'}
    def observe(frame, event, _arg):
        if event == 'call' and frame.f_code in methods:
            request = frame.f_locals['request']
            if request.logical_artifact_id.startswith('software.publication-'):
                calls[methods[frame.f_code]] += 1
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


@pytest.mark.parametrize('count', (1, 16))
def test_fresh_publication_validates_format_once_and_keeps_exact_results(tmp_path, count, record_property):
    plane = _plane(tmp_path / 'proof')
    requests = _requests(count)
    with _validation_work() as work:
        results = plane.write_batch(requests)
    assert work == {'memory': count}
    for request, result in zip(requests, results, strict=True):
        assert plane.root.resolve(result.materialization.relative_path, for_write=False).read_bytes() == request.payload
        plane.verify_manifest(plane.read_manifest(result.materialization.relative_path))
    record_property('publication_format_work', dict(members=count, before=2 * count, after=sum(work.values())))


@pytest.mark.parametrize('when', ('staging', 'before-publication'))
def test_changed_staged_bytes_refuse_even_with_reusable_format_proof(tmp_path, monkeypatch, when):
    plane = _plane(tmp_path / 'changed')
    request, = _requests(1)
    if when == 'staging':
        original = ExternalArtifactPlane._write_staged_bytes
        def write(path, payload, **options):
            original(path, payload, **options)
            if payload == request.payload:
                path.write_bytes(b'[' + payload[1:])
        monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_bytes', staticmethod(write))
    else:
        original = ExternalArtifactPlane._bind_staged_batch
        def bind(self, staged, **options):
            result = original(self, staged, **options)
            path = staged[0].staged_artifact_path
            path.write_bytes(b'[' + path.read_bytes()[1:])
            return result
        monkeypatch.setattr(ExternalArtifactPlane, '_bind_staged_batch', bind)
    with pytest.raises(ArtifactIdentityConflict):
        plane.write(request)
    assert not plane.root.resolve(request.relative_path, for_write=False).exists()


def test_changed_policy_after_memory_validation_gets_fresh_file_validation(tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'changed-policy')
    request, = _requests(1)
    original = ExternalArtifactPlane._write_staged_bytes
    def write(path, payload, **options):
        original(path, payload, **options)
        if payload == request.payload:
            plane.custody_limits = ArtifactCustodyLimits(canonical_json_token_bytes=4)
    monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_bytes', staticmethod(write))
    with pytest.raises((ValueError, RuntimeError)):
        plane.write(request)
    assert not plane.root.resolve(request.relative_path, for_write=False).exists()


def test_disabled_profile_after_memory_validation_cannot_reuse_proof(tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'disabled-profile')
    request, = _requests(1)
    original = ExternalArtifactPlane._write_staged_bytes
    def write(path, payload, **options):
        original(path, payload, **options)
        if payload == request.payload:
            monkeypatch.setattr(ArtifactProfileValidatorRegistry, 'enabled_profiles', property(lambda self: frozenset()))
    monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_bytes', staticmethod(write))
    with pytest.raises((ValueError, RuntimeError)):
        plane.write(request)
    assert not plane.root.resolve(request.relative_path, for_write=False).exists()


def test_custom_file_validator_retains_its_original_boundary(tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'custom')
    calls = []
    original = ArtifactProfileValidatorRegistry.validate_file
    def validate(self, path, request, **options):
        calls.append(request.logical_artifact_id)
        return original(self, path, request, **options)
    monkeypatch.setattr(ArtifactProfileValidatorRegistry, 'validate_file', validate)
    request, = _requests(1)
    plane.write(request)
    assert calls == [request.logical_artifact_id]


def test_stream_keeps_its_only_format_validation(tmp_path):
    plane = _plane(tmp_path / 'stream')
    request, = _requests(1)
    stream = ArtifactStreamWriteRequest(request.logical_artifact_id, request.relative_path,
        request.payload_schema, request.profile, request.media_type, request.publication_scope_id,
        request.publication_scope_relative_root, (request.payload,), len(request.payload), len(request.payload),
        visibility_ceiling=request.visibility_ceiling, parent_visibility_ceilings=request.parent_visibility_ceilings,
        outcome_access=request.outcome_access)
    with _validation_work() as work:
        plane.write_stream(stream)
    assert work == {'file': 1}


def test_failed_payload_cannot_leave_a_proof_for_next_staging_call(tmp_path):
    plane = _plane(tmp_path / 'invalid')
    request, = _requests(1)
    with pytest.raises((ValueError, RuntimeError)):
        plane.write(replace(request, payload=b'not JSON\n'))
    with _validation_work() as work:
        plane.write(request)
    assert work == {'memory': 1}
