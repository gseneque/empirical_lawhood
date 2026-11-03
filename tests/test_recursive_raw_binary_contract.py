# SPDX-License-Identifier: MPL-2.0
"""Exact declared raw-byte output seam; never a canonical record exemption."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_FRAMED_ARRAY_SCHEMA, MATRIX_STORAGE_CODECS
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.plans import OutputTemplate
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationProvider, RecursiveOperationProviderFactory, recursive_operation_binding,
)
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.runtime_platform.test_native_subwork import _plane as _bare_plane
from tests.runtime_platform.test_recursive_compiler import fixture

SCHEMA = MATRIX_FRAMED_ARRAY_SCHEMA


def _plane(path):
    return _bare_plane(path, binary_codecs=MATRIX_STORAGE_CODECS)


def selected(*, schema=SCHEMA, media='application/octet-stream', profile=ArtifactProfile.RAW_SOURCE_BYTES):
    draft, registrations, registry = fixture()
    output = OutputTemplate('result', schema, profile, media, '.bin')
    registrations = tuple(replace(r, outputs=(output,), storage_codecs=MATRIX_STORAGE_CODECS,
        input_ports=() if not r.input_ports else (RecursivePortContract('operand', schema, media, None),))
        for r in registrations)
    registry = CapabilityRegistry(registry.registry_id,
        tuple(replace(m, input_schema_ids=tuple(sorted({m.config_schema, schema})), output_schema_ids=(schema,))
            for m in registry.capabilities))
    return draft, registrations, registry


def test_declared_raw_binary_factory_compiler_and_capability_semantics():
    draft, registrations, registry = selected()
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='1'*40, output_codecs={})
    assert len(compiled.execution_plan.tasks) == 2
    for registration in registrations:
        capability = registry.resolve(registration.selection.capability_key, registration.selection.capability_version)
        factory = RecursiveOperationProviderFactory(recursive_operation_binding(
            registration=registration, manifest=capability), registration, capability, lambda: None, {})
        provider = RecursiveOperationProvider(registry, registration, capability, factory.runner_factory, {}, None)
        semantic = provider.output_semantic_contracts(registry)
        assert len(semantic) == 1 and semantic[0].profile is ArtifactProfile.RAW_SOURCE_BYTES
        assert semantic[0].top_level_keys == semantic[0].value_keys == ()


@pytest.mark.parametrize('kwargs', (
    {'schema': MATRIX_ARRAY_SCHEMA}, {'schema': 'empirical-lawhood/testing/unregistered-raw-bytes'}, {'media': 'application/json'},
    {'profile': ArtifactProfile.CANONICAL_JSON}, {'profile': ArtifactProfile.NUMPY_NO_PICKLE},
))
def test_changed_profile_media_or_old_matrix_schema_cannot_escape_exact_codec(kwargs):
    draft, registrations, registry = selected(**kwargs)
    with pytest.raises(ValueError, match='exact canonical record codec|registered storage codec'):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit='1'*40, output_codecs={})
    r = registrations[0]
    m = registry.resolve(r.selection.capability_key, r.selection.capability_version)
    with pytest.raises(ValueError, match='exact typed codec'):
        RecursiveOperationProviderFactory(recursive_operation_binding(registration=r, manifest=m), r, m, lambda: None, {})


def test_original_npz_profile_remains_distinct_from_raw_octet_stream():
    assert resolve_storage_codec(MATRIX_STORAGE_CODECS, payload_schema=MATRIX_ARRAY_SCHEMA, profile=ArtifactProfile.MATRIX_ARRAY_NPZ, media_type='application/x-npz') is not None
    assert resolve_storage_codec(MATRIX_STORAGE_CODECS, payload_schema=MATRIX_ARRAY_SCHEMA, profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type='application/octet-stream') is None


def test_declared_framed_bytes_have_exact_physical_custody_and_other_raw_contracts_refuse(tmp_path):
    plane = _plane(tmp_path/'selected')
    payload = b'\x00\x00\x00\x00\x00\x00\x00\x03raw'
    request = ArtifactWriteRequest('array.exposed.framed', 'arrays/framed.bin', SCHEMA,
        ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', 'publication.exposed.framed',
        'arrays', payload, VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    result = plane.write(request)
    assert result.materialization.size_bytes == len(payload)
    # This establishes custody only; scientific NPZ/member interpretation is
    # deliberately deferred to the complete framed domain consumer.
    for schema, media in ((MATRIX_ARRAY_SCHEMA, 'application/octet-stream'),
            ('empirical-lawhood/testing/unknown-raw', 'application/octet-stream'),
            (SCHEMA, 'application/zip')):
        with pytest.raises(ArtifactIdentityConflict):
            plane.write(replace(request, logical_artifact_id='array.exposed.other',
                relative_path='arrays/other.bin', payload_schema=schema, media_type=media))


def test_public_authoring_streams_exact_framed_input_and_portable_readback(tmp_path, monkeypatch):
    from hashlib import sha256
    from pathlib import Path
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
    from tests.runtime_platform.test_recursive_compiler import SourceConfig, UseConfig

    draft, registrations, registry = selected()
    registrations = tuple(replace(r, input_ports=(RecursivePortContract('operand',SCHEMA,'application/octet-stream',None),))
                          if r.selection.capability_key == 'generic.source' else r for r in registrations)
    payload = b'\x00\x00\x00\x00\x00\x20\x00\x00'+b'x'*(2*1024**2)
    selected_path = tmp_path/'retained.frames'
    selected_path.write_bytes(payload)
    external = RecursiveExternalInput('input.framed','retained.framed',SCHEMA,'application/octet-stream',None,
        OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,sha256(payload).hexdigest())
    edge = RecursiveInputLink('edge.external.framed','source','operand',external_input_id=external.input_id,scientific_role='SOURCE')
    draft = replace(draft,external_inputs=(external,),links=tuple(sorted((*draft.links,edge),key=lambda l:l.edge_id)))
    root = Path(__file__).resolve().parents[1]
    source = author.implementation_binding(root)
    monkeypatch.setattr(author,'implementation_binding',lambda _:source)
    monkeypatch.setattr(author,'operation_catalog',lambda:(registrations,registry,{SourceConfig.SCHEMA:SourceConfig,UseConfig.SCHEMA:UseConfig}))
    original_read = author.read_bounded_bytes
    def without_whole_frame(path,**kwargs):
        if path == selected_path:
            pytest.fail('authoring cached the complete raw framed population')
        return original_read(path,**kwargs)
    monkeypatch.setattr(author,'read_bounded_bytes',without_whole_frame)
    plane = _plane(tmp_path/'selected')
    directory = tmp_path/'selected/authored'
    result = author.author_recursive_wave(draft=draft,project_root=root,artifact_writer=plane,
        output_dir=directory,input_bindings=((external.input_id,selected_path),))
    assert result['native_contact'] == 'none'
    name = 'external-'+sha256(external.input_id.encode()).hexdigest()[:24]+'.bin'
    for lazy in (True,False):
        packet,recovered,_,members = author.load_authored_wave(directory=directory,artifact_writer=plane,lazy_payloads=lazy)
        assert recovered == draft and members[name] == payload
        assert next(m for m in packet.members if m.filename == name).identity.object_schema == SCHEMA
    # Framed input custody does not establish a scientific NPZ interpretation.
    changed = replace(external,expected_content_sha256='f'*64)
    with pytest.raises(ValueError,match='exact selected digest'):
        author.author_recursive_wave(draft=replace(draft,external_inputs=(changed,)),project_root=root,
            artifact_writer=plane,output_dir=tmp_path/'selected/rejected',input_bindings=((external.input_id,selected_path),))
