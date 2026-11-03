# SPDX-License-Identifier: MPL-2.0
"""Exact canonical acceptance and bounded scanner work; no scientific evidence."""

import io
import json

import pytest

from empirical_lawhood.infrastructure import artifact_validation as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


SCHEMA = "empirical-lawhood/testing/canonical-stream"


def document(value):
    return (json.dumps({"schema": SCHEMA, "value": value, "version": "1.0.0"},
        ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def request(raw):
    return ArtifactWriteRequest("exposed.stream", "exposed/stream.json", SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.stream", "exposed", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)


def validate(raw, *, fast=False):
    if fast:
        return owner._inspect_canonical_json_file(io.BytesIO(raw), request(raw), size=len(raw))
    return owner._CanonicalJsonFileInspector(io.BytesIO(raw), request(raw)).validate()


@pytest.mark.parametrize("chunk_bytes", (1, 2, 7, 65536))
def test_exact_numbers_and_escapes_across_every_small_chunk_boundary(monkeypatch, chunk_bytes):
    monkeypatch.setattr(owner, "_CANONICAL_READ_CHUNK_BYTES", chunk_bytes)
    raw = document({"numbers": [0, -1, 2**400, 0.0, -0.0, 1e-7, 1e20, 1.7976931348623157e308],
        "text": "\"\\\b\f\n\r\t\x00\x0b\x1f\x7f café \ud800 \udfff \U0001f600"})
    validate(raw)
    validate(raw, fast=True)


@pytest.mark.parametrize("token", (b"01", b"-0", b"1.", b"1e0", b"1e-7", b"1E-07", b"1.000",
    b"NaN", b"Infinity", b"1e309", b"--1", b"1+2", b"0x1", b"9" * 129))
@pytest.mark.parametrize("chunk_bytes", (1, 7, 65536))
@pytest.mark.parametrize('fast', (False, True))
def test_noncanonical_or_unbounded_numbers_still_refuse(monkeypatch, token, chunk_bytes, fast):
    monkeypatch.setattr(owner, "_CANONICAL_READ_CHUNK_BYTES", chunk_bytes)
    raw = document(None).replace(b'"value":null', b'"value":' + token)
    with pytest.raises(owner.ArtifactIdentityConflict):
        validate(raw, fast=fast)


def test_every_unicode_escape_matches_the_independent_standard_library_roundtrip():
    selected = request(document(None))
    for codepoint in range(65536):
        token = ('"\\u%04x"' % codepoint).encode("ascii")
        canonical = json.dumps(json.loads(token), ensure_ascii=True).encode("ascii") == token
        reader = owner._CanonicalJsonFileInspector(io.BytesIO(token[1:]), selected)
        if canonical:
            reader._skip_string_token()
        else:
            with pytest.raises(owner.ArtifactIdentityConflict):
                reader._skip_string_token()


@pytest.mark.parametrize("token", (b'"\\/"', b'"\\x20"', b'"\\u00Af"', b'"\\u12"', b'"unterminated'))
def test_invalid_string_spellings_still_refuse_across_chunks(monkeypatch, token):
    monkeypatch.setattr(owner, "_CANONICAL_READ_CHUNK_BYTES", 1)
    with pytest.raises(owner.ArtifactIdentityConflict):
        validate(document(None).replace(b'"value":null', b'"value":' + token))


def test_numeric_stream_work_scales_with_tokens_instead_of_numeric_bytes(monkeypatch):
    read_byte = owner._CanonicalJsonFileInspector._read_byte
    calls = 0

    def observed(self):
        nonlocal calls
        calls += 1
        return read_byte(self)

    monkeypatch.setattr(owner._CanonicalJsonFileInspector, "_read_byte", observed)
    monkeypatch.setattr(owner, "_CANONICAL_READ_CHUNK_BYTES", 17)
    counts = []
    for size in (256, 512):
        calls = 0
        raw = document([10**90 + index for index in range(size)])
        validate(raw)
        assert calls < len(raw) // 8
        counts.append(calls)
    assert counts[1] <= 2 * counts[0]


@pytest.mark.parametrize('change', ('duplicate', 'order', 'newline', 'trailing', 'schema'))
def test_bounded_c_codec_preserves_exact_bytes_and_schema_refusals(change):
    raw = document({'a': 1, 'b': 2})
    changed = {
        'duplicate': raw.replace(b'"a":1', b'"a":0,"a":1'),
        'order': raw.replace(b'"a":1,"b":2', b'"b":2,"a":1'),
        'newline': raw[:-1],
        'trailing': raw + b'\n',
        'schema': raw.replace(SCHEMA.encode(), b'empirical-lawhood/testing/other'),
    }[change]
    with pytest.raises(owner.ArtifactIdentityConflict):
        owner._inspect_canonical_json_file(io.BytesIO(changed), request(changed), size=len(changed))


def test_bounded_c_codec_uses_streaming_only_for_selected_bounds(monkeypatch):
    from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
    raw = document({'a': [1, 2, 3]})
    expected = owner._CanonicalJsonFileInspector(io.BytesIO(raw), request(raw)).validate()
    def forbidden(*args, **kwargs):
        pytest.fail('bounded C codec walked Python JSON tokens')
    monkeypatch.setattr(owner._CanonicalJsonFileInspector, 'validate', forbidden)
    assert owner._inspect_canonical_json_file(io.BytesIO(raw), request(raw), size=len(raw)) == expected
    monkeypatch.undo()
    for limits in (ArtifactCustodyLimits(canonical_json_depth=1),
            ArtifactCustodyLimits(canonical_json_token_bytes=1)):
        with pytest.raises(owner.ArtifactIdentityConflict):
            owner._inspect_canonical_json_file(io.BytesIO(raw), request(raw), size=len(raw), custody_limits=limits)
