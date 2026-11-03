# SPDX-License-Identifier: MPL-2.0
"""Actual incomplete byte custody; no full scientific output or qualification."""

from dataclasses import replace
from hashlib import sha256
import shutil

import pytest

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactStreamWriteRequest, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_recursive_public_service import _plane

SCHEMA = "empirical-lawhood/runtime/native-subwork-received-prefix"


@pytest.mark.parametrize("raw", (b"", b"complete received prefix\x00\xff", bytes(range(256)) * 1024),
                         ids=("empty", "binary", "many-chunks"))
def test_prefix_byte_and_stream_publications_recover_every_received_byte(tmp_path, raw):
    plane = _plane(tmp_path / "producing")
    request = ArtifactWriteRequest("prefix.exposed.bytes", "partial/bytes.bin", SCHEMA,
        ArtifactProfile.NATIVE_SUBWORK_PREFIX, "application/octet-stream", "publication.exposed.prefix", "partial",
        raw, VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    byte = plane.write(request)
    streamed = plane.write_stream(ArtifactStreamWriteRequest(
        logical_artifact_id="prefix.exposed.stream", relative_path="partial/stream.bin", payload_schema=SCHEMA,
        profile=ArtifactProfile.NATIVE_SUBWORK_PREFIX, media_type="application/octet-stream",
        publication_scope_id="publication.exposed.stream", publication_scope_relative_root="partial",
        chunks=(raw[index:index + 7] for index in range(0, len(raw), 7)), maximum_bytes=max(1, len(raw)),
        maximum_chunk_bytes=min(7, max(1, len(raw))), expected_size_bytes=len(raw),
        expected_physical_sha256=sha256(raw).hexdigest(), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        parent_visibility_ceilings=(), outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
    recovered = _plane(tmp_path / "recovered")
    shutil.copytree(plane.root.contract.canonical_path, recovered.root.contract.canonical_path, dirs_exist_ok=True)
    for produced in (byte, streamed):
        value = VerifiedArtifactInput(produced.logical, produced.materialization)
        assert value.logical.semantic_validation is None
        assert value.materialization.size_bytes == len(raw)
        assert value.logical.content_sha256 == sha256(raw).hexdigest()
        port = recovered.open(value, maximum_bytes=len(raw))
        try:
            assert port.read() == raw and port.bytes_read == len(raw)
        finally:
            port.close()
        target = recovered.root.resolve(value.materialization.relative_path, for_write=False)
        target.write_bytes(raw + b"changed")
        with pytest.raises(RuntimeError, match="bytes differ|exceeds its byte bound"):
            recovered.open(value, maximum_bytes=len(raw))


@pytest.mark.parametrize("change", ({"payload_schema": "empirical-lawhood/testing/scientific-output"},
    {"media_type": "application/x-npz"}, {"profile": ArtifactProfile.RAW_SOURCE_BYTES}))
def test_prefix_cannot_relabel_partial_bytes_as_source_or_scientific_output(tmp_path, change):
    plane = _plane(tmp_path / "selected")
    request = ArtifactWriteRequest("prefix.exposed.invalid", "partial/invalid.bin", SCHEMA,
        ArtifactProfile.NATIVE_SUBWORK_PREFIX, "application/octet-stream", "publication.exposed.invalid", "partial",
        b"received bytes", VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    with pytest.raises(RuntimeError, match="contract"):
        plane.write(replace(request, **change))
