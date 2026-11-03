# SPDX-License-Identifier: MPL-2.0
"""Literal FILE metadata controls; no native provider, source capture or arrays.

The literal factory descriptor is an explicit software catalog seam. Its actual
operation_catalog and input_record_type_census owners execute unchanged. The
post-author-hook controls use the existing tiny generic software draft only;
effects and source observation are trapped before either can be entered.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import experiment_preparation as tested_owner, recursive_operations
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityManifest
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentCensus, ExperimentPreparation, ExperimentProtocolDeclaration, PreparedExperimentInputs,
)
from empirical_lawhood.runtime import recursive_record_codecs
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec

@pytest.fixture
def owner():
    return tested_owner


@dataclass(frozen=True, slots=True)
class LiteralFile(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/file-census-literal'
    record_id: str
    signal: int

    def __post_init__(self):
        if type(self.signal) is not int or self.signal <= 0:
            raise ValueError('literal FILE signal must be a positive integer')


@dataclass(frozen=True, slots=True)
class LiteralSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/file-census-spec'
    record_id: str

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def opaque_stream(_stream):
    return None


def literal_case(tmp_path, monkeypatch, owner, count):
    counts = {'catalog': 0, 'census': 0, 'bind': 0}
    files, bindings, payloads = {}, [], {}
    for n in range(count):
        key = f'operand.{n:03d}'
        value = LiteralFile(key, 7)
        raw = value.canonical_bytes()
        path = tmp_path / (key + '.json')
        path.write_bytes(raw)
        identity = ArtifactIdentity(key, 'exposed-software-literal', value.SCHEMA,
            sha256(raw).hexdigest(), 'application/json', len(raw))
        files[key] = path
        payloads[key] = raw
        bindings.append(ExperimentFileInputBinding(key, identity, value.VERSION, path.name, len(raw)))
    selection = ExperimentFileInputSelection('selection.file-census', 'fixture.file-census', (), tuple(bindings))
    selected = tmp_path / 'selection.json'
    selected.write_bytes(selection.canonical_bytes())
    specification = LiteralSpec('spec.file-census')
    budget = ResourceBudget(1, 1024**2, 0, None, 1024**2, 1024**2)
    manifest = CapabilityManifest('fixture.file-census', '1.0.0', CapabilityKind.TRANSFORM,
        LiteralFile.SCHEMA, 'a' * 64, (LiteralFile.SCHEMA,), (LiteralFile.SCHEMA,),
        ( ), EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, budget,
        True, False, 'python', 'python', False, False, False, ('fixture.file-census-check',), 'b' * 64)
    registration = SimpleNamespace(selection=SimpleNamespace(selection_id='fixture.file-census'),
        input_record_types=(LiteralFile,), storage_codecs=())
    factories = [SimpleNamespace(registration=registration, manifest=manifest,
        output_codecs={LiteralFile.SCHEMA: LiteralFile})]
    monkeypatch.setattr(recursive_operations, 'operation_factories', lambda: tuple(factories))
    actual_catalog = recursive_operations.operation_catalog
    actual_census = recursive_record_codecs.input_record_type_census

    def catalog():
        counts['catalog'] += 1
        return actual_catalog()

    def census(*args, **kwargs):
        counts['census'] += 1
        return actual_census(*args, **kwargs)

    monkeypatch.setattr(recursive_operations, 'operation_catalog', catalog)
    monkeypatch.setattr(recursive_record_codecs, 'input_record_type_census', census)
    # This is the same empty installed-storage selection for both owners.
    monkeypatch.setattr(recursive_operations, 'operation_storage_codecs', lambda: ())

    def bind(_spec, records, *, files):
        counts['bind'] += 1
        assert not records
        assert set(files) == set(key for key in payloads)
        return PreparedExperimentInputs({}, files)

    def forbid_prepare(*_args, **_kwargs):
        raise AssertionError('FILE metadata validation entered experiment preparation')

    declaration = ExperimentProtocolDeclaration(protocol_id=selection.protocol_id,
        specification_type=LiteralSpec, prepare=forbid_prepare, consumer_id='fixture.file-census',
        maximum_config_bytes=1024**2, bind_inputs=bind, bind_input_locations=False,
        input_record_types=(), input_file_record_types=(LiteralFile,), input_storage_codecs=())
    case = SimpleNamespace(counts=counts, files=files, bindings=tuple(bindings), payloads=payloads,
        choice=selection, selected=selected, specification=specification, declaration=declaration,
        factories=factories)
    monkeypatch.setattr(owner, '_protocol', lambda _spec: case.declaration)
    return case


@pytest.mark.parametrize('count', (8, 32))
def test_actual_catalog_census_counts_are_per_pass_without_changing_file_handles(tmp_path, monkeypatch, owner, count):
    case = literal_case(tmp_path, monkeypatch, owner, count)
    original = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    # Canonical FILEs are opaque here: the domain does not ask to decode them.
    def forbid_interpretation(*_args, **_kwargs):
        raise AssertionError('opaque FILE contract interpreted a scientific record')
    monkeypatch.setattr(LiteralFile, '__post_init__', forbid_interpretation, raising=False)
    resolved = owner.load_experiment_inputs(case.specification, case.selected)
    for binding in case.bindings:
        actual = resolved.method_inputs[binding.key]
        assert actual.identity == binding.identity
        assert actual.path == case.files[binding.key]
        assert actual.record_version == binding.record_version
        assert actual.maximum_bytes == binding.maximum_bytes
    assert case.counts == {'catalog': 1,
        'census': 2, 'bind': 1}
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == original
    print('FILE_CENSUS_COUNTS', count, case.counts)


@pytest.mark.parametrize('damage', ('digest', 'oversize', 'symlink'))
def test_last_file_still_authenticates_fresh_bytes_and_path_before_binding(tmp_path, monkeypatch, owner, damage):
    case = literal_case(tmp_path, monkeypatch, owner, 8)
    last = case.files[case.bindings[-1].key]
    raw = last.read_bytes()
    if damage == 'digest':
        last.write_bytes(raw.replace(b':7', b':8'))
    elif damage == 'oversize':
        last.write_bytes(raw + b'oversize')
    else:
        target = last.with_suffix('.retained')
        last.rename(target)
        last.symlink_to(target)
    with pytest.raises((ValueError, BoundedFileIOError)):
        owner.load_experiment_inputs(case.specification, case.selected)
    assert case.counts['bind'] == 0


def test_custom_four_argument_file_guard_is_called_for_every_original_file(tmp_path, monkeypatch, owner):
    case = literal_case(tmp_path, monkeypatch, owner, 8)
    actual = owner._file_byte_limit
    seen = []
    def custom(declaration, identity, version, installed):
        seen.append(identity.artifact_id)
        if identity.artifact_id == case.bindings[-1].identity.artifact_id:
            raise PermissionError('late custom FILE policy refusal')
        return actual(declaration, identity, version, installed)
    monkeypatch.setattr(owner, '_file_byte_limit', custom)
    with pytest.raises(PermissionError, match='late custom'):
        owner.load_experiment_inputs(case.specification, case.selected)
    assert seen == [row.identity.artifact_id for row in case.bindings]
    assert case.counts['bind'] == 0


def test_standalone_guard_does_not_leak_a_census_between_invocations(tmp_path, monkeypatch, owner):
    case = literal_case(tmp_path, monkeypatch, owner, 1)
    binding, = case.bindings
    assert owner._file_byte_limit(case.declaration, binding.identity, binding.record_version, ()) is None
    case.factories[0].registration.input_record_types = ()
    case.factories[0].output_codecs = {}
    with pytest.raises(ValueError, match='identical installed'):
        owner._file_byte_limit(case.declaration, binding.identity, binding.record_version, ())
    assert case.counts == {'catalog': 2, 'census': 4, 'bind': 0}


def test_raw_storage_byte_bound_is_not_replaced_by_canonical_roster_reuse(tmp_path, monkeypatch, owner):
    case = literal_case(tmp_path, monkeypatch, owner, 1)
    codec = RecursiveStorageCodec('codec.file-census.raw', 'empirical-lawhood/testing/file-census-raw',
        '1.0.0', ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', '.bin', opaque_stream, 4)
    monkeypatch.setattr(recursive_operations, 'operation_storage_codecs', lambda: (codec,))
    case.declaration = replace(case.declaration, input_storage_codecs=(codec,))
    old, = case.bindings
    raw = b'12345'
    case.files[old.key].write_bytes(raw)
    identity = replace(old.identity, payload_schema=codec.payload_schema, media_type=codec.media_type,
        sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    case.selected.write_bytes(replace(case.choice, files=(replace(old, identity=identity, maximum_bytes=8),)).canonical_bytes())
    with pytest.raises(ValueError, match='registered physical byte contract'):
        owner.load_experiment_inputs(case.specification, case.selected)
    assert case.counts == {'catalog': 0, 'census': 0, 'bind': 0}


def test_bad_revision_refuses_before_discovering_a_type_roster(tmp_path, monkeypatch, owner):
    case = literal_case(tmp_path, monkeypatch, owner, 1)
    old, = case.bindings
    case.selected.write_bytes(replace(case.choice, files=(replace(old, record_version='2.0.0'),)).canonical_bytes())
    with pytest.raises(ValueError, match='exact declared schema/revision'):
        owner.load_experiment_inputs(case.specification, case.selected)
    assert case.counts == {'catalog': 0, 'census': 0, 'bind': 0}


def prepared_one_file(owner, case, resolved):
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
    from tests.runtime_platform.test_recursive_compiler import fixture
    draft, _, _ = fixture()  # Existing literal generic conformance graph, no native runner.
    binding, = case.bindings
    external = RecursiveExternalInput('external.file-census', binding.identity.artifact_id,
        binding.identity.payload_schema, binding.identity.media_type, binding.maximum_bytes,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, binding.identity.sha256)
    link = RecursiveInputLink('edge.file-census', 'source', 'file', external_input_id=external.input_id,
        scientific_role=external.scientific_role)
    draft = replace(draft, external_inputs=(external,), links=tuple(sorted((*draft.links, link), key=lambda row: row.edge_id)))
    allocation = UnitAllocation('allocation.file-census', (case.specification.identity,),
        (IndependentUnit('unit.file-census', case.specification.record_id, 'family.software', (), True),),
        (UnitRoleAssignment('unit.file-census', 'exposed'),))
    return ExperimentPreparation(case.specification.identity, ExperimentCensus((), (), (), (), 0), (),
        allocation=allocation, draft=draft, input_files=((external.input_id, resolved.method_inputs[binding.key]),),
        execution=ExecutionSelection(workers=1), specification_record=case.specification)


@pytest.mark.parametrize('damage', ('roster', 'symlink'))
def test_author_second_pass_reopens_roster_and_path_after_prepare_authoring(tmp_path, monkeypatch, owner, damage):
    from empirical_lawhood.api import recursive_authoring
    case = literal_case(tmp_path, monkeypatch, owner, 1)
    resolved = owner.load_experiment_inputs(case.specification, case.selected)
    prepared = prepared_one_file(owner, case, resolved)
    case.counts.update(catalog=0, census=0, bind=0)
    calls = []
    def before_effects(*_args, **_kwargs):
        raise AssertionError('invalid post-hook FILE reached source observation or authoring effects')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', before_effects)
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', before_effects)
    def hook(value, **_kwargs):
        calls.append('prepare_authoring')
        assert case.counts['catalog'] == 1
        if damage == 'roster':
            case.factories[0].registration.input_record_types = ()
            case.factories[0].output_codecs = {}
        else:
            path = next(iter(case.files.values()))
            target = path.with_suffix('.retained')
            path.rename(target)
            path.symlink_to(target)
        return value
    monkeypatch.setattr(owner, 'experiment_runtime_binding',
        lambda _protocol: SimpleNamespace(prepare_authoring=hook,validate_authoring_read_access=None,
            bootstrap_prospective_input_access=None, bootstrap_authoring_input_access=None))
    with pytest.raises(ValueError, match='identical installed|symbolic links'):
        owner.author_prepared_experiment(preparation=prepared, project_root=Path.cwd(),
            artifact_writer=object(), output_dir=tmp_path / 'unentered-authoring')
    assert calls == ['prepare_authoring']
    assert case.counts == {'catalog': 2, 'census': 4, 'bind': 0}
    assert not (tmp_path / 'unentered-authoring').exists()
