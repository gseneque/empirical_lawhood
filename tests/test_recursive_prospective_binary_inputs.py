# SPDX-License-Identifier: MPL-2.0
"""Registered physical codecs survive public prospective runtime transport.

Disclosed binary and canonical fixtures exercise custody only. They supply no
scientific source qualification, native acquisition or authority.
"""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.api.execution import CampaignExecutionService
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
from empirical_lawhood.infrastructure.recursive_prospective_inputs import RecursiveContentInputSupplier
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.plans import ExternalInputSpec
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveOperand
from empirical_lawhood.runtime.recursive_storage_codecs import storage_codec_census
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_recursive_storage_codec_registration import (
    MAXIMUM_BYTES, MEDIA, SCHEMA, _codec, _declaration, _framed, _validate_raw_json_fixture_stream,
)
from tests.test_recursive_public_service import _plane


def selected(tmp_path, raw, *, schema=SCHEMA, media=MEDIA, codecs=()):
    plane = _plane(tmp_path / 'selected')
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=codecs)
    ExternalCandidateInputPublisher(plane.root).publish(raw, maximum_bytes=len(raw))
    operand = RecursiveProspectiveOperand('input.disclosed.prospective', sha256(raw).hexdigest(), len(raw),
        schema, media, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
    spec = ExternalInputSpec('external.disclosed.prospective', operand.logical_artifact_id,
        operand.content_sha256, schema, media, len(raw), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None)
    supplier = RecursiveContentInputSupplier(root=plane.root, operands=(operand,), storage_codecs=codecs)
    return plane, operand, spec, supplier


def persist(plane, payload):
    service = object.__new__(CampaignExecutionService)
    service.artifact_plane = plane
    value, = service._persist_provider_inputs('run.disclosed.prospective-binary', (payload,), minimum_free_bytes=0)
    return value


def test_registered_binary_profile_reaches_actual_public_input_publisher_with_exact_bytes(tmp_path):
    codec = _codec()
    registrations = (_declaration('source', codec).registration(), _declaration('use', codec).registration())
    codecs = storage_codec_census(registrations)
    raw = _framed(b'unchanged original \x00\xff scientific bytes')
    plane, operand, spec, supplier = selected(tmp_path, raw, codecs=codecs)
    payload = supplier.resolve_input(spec)
    assert payload.profile is ArtifactProfile.RAW_SOURCE_BYTES
    verified = persist(plane, payload)
    assert verified.logical.profile is codec.profile
    assert verified.logical.content_sha256 == verified.materialization.physical_sha256 == operand.content_sha256
    assert verified.materialization.size_bytes == len(raw)
    assert verified.logical.outcome_access is operand.outcome_access
    assert verified.logical.visibility_ceiling is operand.visibility_ceiling
    path = plane.root.resolve(verified.materialization.relative_path, for_write=False)
    assert path.read_bytes() == raw


def test_registered_raw_json_precedes_canonical_default_and_preserves_original_spacing(tmp_path):
    codec = _codec(codec_id='testing.storage.original-json', media_type='application/json', filename_suffix='.json',
        validate_stream=_validate_raw_json_fixture_stream)
    raw = b' { "original": [1, 2] }\n'
    plane, _, spec, supplier = selected(tmp_path, raw, media='application/json', codecs=(codec,))
    verified = persist(plane, supplier.resolve_input(spec))
    assert verified.logical.profile is ArtifactProfile.RAW_SOURCE_BYTES
    assert plane.root.resolve(verified.materialization.relative_path, for_write=False).read_bytes() == raw


@pytest.mark.parametrize('media', ('application/json', 'application/vnd.disclosed-source+json'))
def test_canonical_record_without_binary_codec_keeps_canonical_default(tmp_path, media):
    raw = Config('config.literal.prospective', 7).canonical_bytes()
    plane, _, spec, supplier = selected(tmp_path, raw, schema=Config.SCHEMA, media=media)
    payload = supplier.resolve_input(spec)
    assert payload.profile is ArtifactProfile.CANONICAL_JSON
    verified = persist(plane, payload)
    assert verified.logical.profile is ArtifactProfile.CANONICAL_JSON
    assert plane.root.resolve(verified.materialization.relative_path, for_write=False).read_bytes() == raw


@pytest.mark.parametrize('damage', ('missing-codec', 'wrong-media', 'wrong-schema', 'codec-bound', 'ambiguous-profile'))
def test_absent_or_conflicting_codec_refuses_before_content_materialization(tmp_path, monkeypatch, damage):
    codec, raw = _codec(), _framed()
    codecs = (codec,)
    schema, media = SCHEMA, MEDIA
    if damage == 'missing-codec':
        codecs = ()
    elif damage == 'wrong-media':
        media = 'application/unknown-binary'
    elif damage == 'wrong-schema':
        schema = SCHEMA + '-other'
    elif damage == 'codec-bound':
        raw = _framed(b'a' * MAXIMUM_BYTES)
    else:
        codecs = (codec, replace(codec, codec_id=codec.codec_id + '.other', profile=ArtifactProfile.NUMPY_NO_PICKLE))
    _, _, spec, supplier = selected(tmp_path, raw, schema=schema, media=media, codecs=codecs)
    monkeypatch.setattr(supplier.resolver, 'resolve', lambda *_args, **_kwargs:
        pytest.fail('unregistered physical transport reached source bytes'))
    with pytest.raises(ValueError, match='codec|ambiguous'):
        supplier.resolve_input(spec)


@pytest.mark.parametrize('field,value', (
    ('expected_content_sha256', 'f' * 64), ('expected_payload_schema', SCHEMA + '-foreign'),
    ('expected_media_type', 'application/foreign'), ('expected_size_bytes', 1),
    ('expected_outcome_access', Access.DEVELOPMENT_VISIBLE), ('expected_visibility_ceiling', Visibility.DEVELOPMENT_ONLY),
))
def test_codec_support_preserves_every_frozen_external_input_constraint(tmp_path, monkeypatch, field, value):
    _, _, spec, supplier = selected(tmp_path, _framed(), codecs=(_codec(),))
    monkeypatch.setattr(supplier.resolver, 'resolve', lambda *_args, **_kwargs:
        pytest.fail('changed scientific source contract reached byte materialization'))
    with pytest.raises(ValueError, match='frozen bytes'):
        supplier.resolve_input(replace(spec, **{field: value}))
