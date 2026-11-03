"""Original framed history retains its binary contract through public custody.

This is exposed transport conformance, without a native contact or source
qualification. The de-anneal consumer independently authenticates its arrays.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_array_chunks import (
    FRAMED_ARRAY_MEDIA, FRAMED_ARRAY_SCHEMA, iter_framed_bytes,
)
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import Config, fixture
from tests.test_matrix_array_chunks import small_case
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]


def _framed_fixture():
    _, arrays, leaves = small_case()
    raw = b"".join(iter_framed_bytes(arrays,
        lambda artifact: (leaves[artifact.artifact_id],), maximum_chunk_bytes=65536))
    draft, registrations, registry = fixture()
    external = RecursiveExternalInput("external.coarse", "original.coarse.framed",
        FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, len(raw), OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, sha256(raw).hexdigest(), "SOURCE")
    draft = replace(draft, external_inputs=(external,), links=tuple(sorted((*draft.links,
        RecursiveInputLink("edge.coarse", "source", "coarse", external_input_id=external.input_id,
                           scientific_role="SOURCE")), key=lambda row: row.edge_id)))
    registrations = (replace(registrations[0], storage_codecs=MATRIX_STORAGE_CODECS, input_ports=(RecursivePortContract(
        "coarse", FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, len(raw)),)), registrations[1])
    registry = replace(registry, capabilities=(replace(registry.capabilities[0],
        input_schema_ids=tuple(sorted((*registry.capabilities[0].input_schema_ids, FRAMED_ARRAY_SCHEMA)))),
        registry.capabilities[1]))
    return raw, draft, registrations, registry


@pytest.mark.parametrize("lazy", [False, True])
def test_public_framed_external_input_materializes_exact_binary_and_recovers(tmp_path, monkeypatch, lazy):
    raw, draft, registrations, registry = _framed_fixture()
    source = author.implementation_binding(ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root: source)
    monkeypatch.setattr(author, "operation_catalog", lambda: (registrations, registry, {Config.SCHEMA: Config}))
    original = tmp_path / "original-framed.bin"
    original.write_bytes(raw)
    plane = _plane(tmp_path / "custody")
    directory = tmp_path / "custody/authored"
    authored = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=(("external.coarse", original),))
    assert authored["native_contact"] == "none"
    _, retained_draft, _, payloads = author.load_authored_wave(
        directory=directory, artifact_writer=plane, lazy_payloads=lazy)
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=source.observed_git_head, output_codecs={Config.SCHEMA: Config})
    inputs = _external_inputs(plane=plane, plan=compiled.execution_plan, draft=retained_draft,
                             payloads=payloads, read_only=False)
    coarse = next(row for row in inputs if row.logical.payload_schema == FRAMED_ARRAY_SCHEMA)
    assert coarse.logical.profile is ArtifactProfile.RAW_SOURCE_BYTES
    assert coarse.logical.media_type == FRAMED_ARRAY_MEDIA
    assert coarse.logical.content_sha256 == sha256(raw).hexdigest()
    assert coarse.materialization.relative_path.endswith(".bin")
    path = plane.root.resolve(coarse.materialization.relative_path, for_write=False)
    assert path.read_bytes() == raw
    assert _external_inputs(plane=plane, plan=compiled.execution_plan, draft=retained_draft,
                            payloads=payloads, read_only=True) == inputs
    changed = bytearray(raw)
    changed[-1] ^= 1
    path.write_bytes(changed)
    with pytest.raises((ArtifactIdentityConflict, ValueError)):
        _external_inputs(plane=plane, plan=compiled.execution_plan, draft=retained_draft,
                         payloads=payloads, read_only=True)
