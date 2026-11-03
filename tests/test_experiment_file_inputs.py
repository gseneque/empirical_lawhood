# SPDX-License-Identifier: MPL-2.0
"""Exact original file bindings through the same public preparation owner."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace
import json
import os

import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_PYTHON_SOURCE_CODEC
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputBinding, ExperimentFileInputSelection,
)
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentCensus, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs,
)
from tests.test_experiment_preparation_public import _other_input_scope
from tests.runtime_platform.test_recursive_compiler import fixture
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict


def _mixed(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    specification, records, original, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    payload = b'values = (3, 5, 8)\n'
    member = tmp_path / 'original.py'
    member.write_bytes(payload)
    codec = MATRIX_PYTHON_SOURCE_CODEC
    identity = ArtifactIdentity('fixture.original-file', 'original-observations', codec.payload_schema,
        sha256(payload).hexdigest(), codec.media_type, len(payload))
    binding = ExperimentFileInputBinding('original-file', identity, codec.record_version, member.name, len(payload))
    selection = ExperimentFileInputSelection('fixture.mixed-inputs', original.protocol_id, original.bindings, (binding,))
    path.write_bytes(selection.canonical_bytes())

    def bind(spec, selected_records, *, files):
        calls.append((spec, dict(selected_records), dict(files)))
        return PreparedExperimentInputs({}, dict(files))

    declaration, = generated.EXPERIMENT_PROTOCOL_DECLARATIONS
    monkeypatch.setattr(generated, 'EXPERIMENT_PROTOCOL_DECLARATIONS',
        (replace(declaration, input_storage_codecs=(codec,), bind_inputs=bind),))
    return specification, records, selection, path, calls, member


def test_original_python_file_loads_as_a_streamed_handle_without_copy_or_reinterpretation(tmp_path, monkeypatch):
    specification, records, selection, path, calls, member = _mixed(tmp_path, monkeypatch)
    before = {row.name: row.read_bytes() for row in tmp_path.iterdir()}
    resolved = load_experiment_inputs(specification, path)
    handle = PreparedExperimentFile(selection.files[0].identity, '1.0.0', member, member.stat().st_size)
    assert calls == [(specification, records, {'original-file': handle})]
    assert resolved.method_inputs == {'original-file': handle}
    assert {row.name: row.read_bytes() for row in tmp_path.iterdir()} == before


@pytest.mark.parametrize('mutation', ('digest', 'size', 'revision', 'media', 'schema', 'undeclared', 'uninstalled'))
def test_file_substitutions_refuse_before_the_domain_callback(tmp_path, monkeypatch, mutation):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    specification, _, selection, path, calls, member = _mixed(tmp_path, monkeypatch)
    binding, = selection.files
    if mutation == 'digest':
        member.write_bytes(member.read_bytes().replace(b'8', b'9'))
    elif mutation == 'size':
        binding = replace(binding, identity=replace(binding.identity, size_bytes=binding.identity.size_bytes - 1))
    elif mutation == 'revision':
        binding = replace(binding, record_version='2.0.0')
    elif mutation in ('media', 'schema'):
        binding = replace(binding, identity=replace(binding.identity, **(
            {'media_type': 'application/x-hdf5'} if mutation == 'media' else
            {'payload_schema': 'empirical-lawhood/testing/unknown-file'})))
    else:
        declaration, = generated.EXPERIMENT_PROTOCOL_DECLARATIONS
        codecs = () if mutation == 'undeclared' else (replace(declaration.input_storage_codecs[0],
            codec_id='fixture.uninstalled-original-file'),)
        monkeypatch.setattr(generated, 'EXPERIMENT_PROTOCOL_DECLARATIONS',
            (replace(declaration, input_storage_codecs=codecs),))
    path.write_bytes(replace(selection, files=(binding,)).canonical_bytes())
    with pytest.raises((ValueError, BoundedFileIOError), match='selected exact bytes|storage codec/revision|byte limit'):
        load_experiment_inputs(specification, path)
    assert not calls


def test_known_oversize_refuses_before_bulk_read_even_with_a_broad_operational_allowance(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure import bounded_io

    specification, _, selection, path, calls, member = _mixed(tmp_path, monkeypatch)
    binding = replace(selection.files[0], maximum_bytes=1024 * 1024)
    path.write_bytes(replace(selection, files=(binding,)).canonical_bytes())
    member.write_bytes(member.read_bytes() + b'X' * 65536)
    selected_inode = member.stat().st_ino
    original = bounded_io._regular_chunks

    def chunks(descriptor, *args, **kwargs):
        if os.fstat(descriptor).st_ino == selected_inode:
            raise AssertionError('known oversize input reached bulk hashing')
        yield from original(descriptor, *args, **kwargs)

    monkeypatch.setattr(bounded_io, '_regular_chunks', chunks)
    with pytest.raises(BoundedFileIOError, match='byte limit'):
        load_experiment_inputs(specification, path)
    assert not calls


@pytest.mark.parametrize('location', ('file', 'parent'))
def test_file_symlinks_refuse_without_domain_contact(tmp_path, monkeypatch, location):
    specification, _, selection, path, calls, member = _mixed(tmp_path, monkeypatch)
    if location == 'file':
        link = tmp_path / 'link.json'
        link.symlink_to(member)
        relative = link.name
    else:
        directory = tmp_path / 'originals'
        directory.mkdir()
        member.rename(directory / member.name)
        link = tmp_path / 'linked-directory'
        link.symlink_to(directory, target_is_directory=True)
        relative = link.name + '/' + member.name
    path.write_bytes(replace(selection, files=(replace(selection.files[0], relative_path=relative),)).canonical_bytes())
    with pytest.raises(ValueError, match='symbolic links'):
        load_experiment_inputs(specification, path)
    assert not calls


def test_duplicate_selection_envelope_keys_cannot_use_schema_probe_to_bypass_strict_decode(tmp_path, monkeypatch):
    specification, _, _, path, calls, _ = _mixed(tmp_path, monkeypatch)
    raw = path.read_bytes()
    schema = json.loads(raw)['schema']
    path.write_bytes(raw.replace(b'{', ('{"schema":' + json.dumps(schema) + ',').encode(), 1))
    with pytest.raises(ValueError, match='duplicate'):
        load_experiment_inputs(specification, path)
    assert not calls


@pytest.mark.parametrize('mutation', ('duplicate', 'record-collision', 'escape', 'insufficient-bound'))
def test_file_selection_rejects_ambiguous_keys_paths_and_bounds(tmp_path, monkeypatch, mutation):
    _, _, selection, _, _, _ = _mixed(tmp_path, monkeypatch)
    binding, = selection.files
    with pytest.raises(ValueError):
        if mutation == 'duplicate':
            replace(selection, files=(binding, binding))
        elif mutation == 'record-collision':
            replace(selection, files=(replace(binding, key=selection.bindings[0].key),))
        elif mutation == 'escape':
            replace(binding, relative_path='../outside.json')
        else:
            replace(binding, maximum_bytes=binding.identity.size_bytes - 1)


def _prepared(tmp_path):
    draft, _, _ = fixture()
    source = draft.development_study.system
    allocation = UnitAllocation('fixture.file-allocation', (source,),
        (IndependentUnit('fixture.unit', source.object_id, 'fixture.family', ('view.primary',), True),),
        (UnitRoleAssignment('fixture.unit', 'measurement'),))
    identity = ArtifactIdentity('fixture.original-file', 'original-observations', MATRIX_PYTHON_SOURCE_CODEC.payload_schema,
        'a' * 64, MATRIX_PYTHON_SOURCE_CODEC.media_type, 32)
    handle = PreparedExperimentFile(identity, '1.0.0', tmp_path / 'original.py', 32)
    external = RecursiveExternalInput('external.original', identity.artifact_id, identity.payload_schema,
        identity.media_type, 32, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, identity.sha256)
    draft = replace(draft, external_inputs=(external,), links=tuple(sorted((*draft.links,
        RecursiveInputLink('edge.original', 'source', 'original', external_input_id=external.input_id)),
        key=lambda row: row.edge_id)))
    census = ExperimentCensus((), (), (), (), 0)
    return ExperimentPreparation(ObjectIdentity('fixture.specification', 'empirical-lawhood/testing/specification',
        '1.0.0', 'b' * 64), census, (), allocation, draft,
        execution=ExecutionSelection(workers=1), input_files=(('external.original', handle),))


def test_prepared_file_handles_are_operational_and_do_not_open_original_bytes(tmp_path):
    prepared = _prepared(tmp_path)
    assert prepared.executable
    assert not prepared.input_files[0][1].path.exists()


@pytest.mark.parametrize('mutation', ('missing', 'extra', 'media', 'digest', 'id', 'schema', 'bound'))
def test_prepared_union_keeps_every_exact_external_operand(tmp_path, mutation):
    prepared = _prepared(tmp_path)
    key, handle = prepared.input_files[0]
    with pytest.raises(ValueError, match='external operands|external operand|disjoint'):
        if mutation == 'missing':
            # Keep another input so that a populated projection cannot omit the selected file.
            replace(prepared, input_files=((key + '.foreign', handle),))
        elif mutation == 'extra':
            replace(prepared, input_files=((key, handle), (key + '.foreign', handle)))
        else:
            fields = {'media': {'media_type': 'application/zip'}, 'digest': {'sha256': 'c' * 64},
                'id': {'artifact_id': 'fixture.different'},
                'schema': {'payload_schema': 'empirical-lawhood/testing/different'}}
            changed = (replace(handle, maximum_bytes=33) if mutation == 'bound' else
                replace(handle, identity=replace(handle.identity, **fields[mutation])))
            replace(prepared, input_files=((key, changed),))


@pytest.mark.parametrize("damage", ("schema", "media", "profile", "semantic", "empty"))
def test_current_python_source_codec_refuses_unregistered_contracts_without_relabeling(damage):
    declared = MATRIX_PYTHON_SOURCE_CODEC
    values = dict(payload_schema=declared.payload_schema, profile=ArtifactProfile.RAW_SOURCE_BYTES,
        media_type=declared.media_type, semantic_validation=None)
    if damage == "schema":
        values["payload_schema"] = "empirical-lawhood/test/foreign"
    elif damage == "media":
        values["media_type"] = "application/octet-stream"
    elif damage == "profile":
        values["profile"] = ArtifactProfile.CANONICAL_JSON
    elif damage == "semantic":
        values["semantic_validation"] = object()
    with pytest.raises(ArtifactIdentityConflict, match="original uninterpreted"):
        declared.validate_stream(BytesIO(b"{ original bytes }"), SimpleNamespace(**values), size=0 if damage == "empty" else 18)
