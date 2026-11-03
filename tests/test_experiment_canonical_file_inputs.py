# SPDX-License-Identifier: MPL-2.0
"""Tiny canonical FILE conformance; no scientific worker or protected data."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import experiment_preparation as owner, recursive_authoring, recursive_operations
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding, ExperimentInputSelection,
)
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentCensus, ExperimentPreparation, ExperimentProtocolDeclaration, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec
from tests.runtime_platform.test_recursive_compiler import Config, fixture
from tests.runtime_platform.test_native_subwork import _plane


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class ToyFile(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/canonical-file-operand"
    record_id: str
    signal: int

    def __post_init__(self):
        if type(self.signal) is not int or self.signal <= 0:
            raise ValueError("owning toy decoder refuses a nonpositive signal")


@dataclass(frozen=True, slots=True)
class OtherFile(ToyFile):
    """Same envelope does not make this distinct Python owner installed."""


@dataclass(frozen=True, slots=True)
class ToyMetadata(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/canonical-file-metadata"
    metadata_id: str


@dataclass(frozen=True, slots=True)
class ToySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/canonical-file-specification"
    specification_id: str
    operand: ObjectIdentity

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def _raw_json_stream(_stream):
    return None


@pytest.fixture
def selected(tmp_path, monkeypatch):
    record = ToyFile("operand.toy", 7)
    raw = record.canonical_bytes()
    assert len(raw) < 1024
    member = tmp_path / "original.json"
    member.write_bytes(raw)
    spec = ToySpecification("specification.toy-file", ObjectIdentity.from_record(record.record_id, record))
    artifact = ArtifactIdentity(record.record_id, "exposed-toy-operand", record.SCHEMA,
        record.fingerprint(), "application/json", len(raw))
    binding = ExperimentFileInputBinding("operand", artifact, ToyFile.VERSION, member.name, len(raw))
    choice = ExperimentFileInputSelection("selection.toy-file", "fixture.canonical-file", (), (binding,))
    path = tmp_path / "selection.json"
    path.write_bytes(choice.canonical_bytes())
    calls = []
    draft, registrations, registry = fixture()
    source = registrations[0]
    source = replace(source, input_ports=(RecursivePortContract("file", ToyFile.SCHEMA, "application/json", 1024),),
        input_record_types=(ToyFile,))
    registrations = (source, registrations[1])
    source_manifest = registry.capabilities[0]
    registry = replace(registry, capabilities=(replace(source_manifest,
        input_schema_ids=tuple(sorted((*source_manifest.input_schema_ids, ToyFile.SCHEMA)))), registry.capabilities[1]))
    catalog = (registrations, registry, {Config.SCHEMA: Config})
    monkeypatch.setattr(recursive_operations, "operation_catalog", lambda: catalog)
    monkeypatch.setattr(recursive_operations, "operation_storage_codecs", lambda: ())
    monkeypatch.setattr(recursive_authoring, "operation_catalog", lambda: catalog)

    def bind(specification, records, *, files=None):
        calls.append("bind")
        files = {} if files is None else files
        if records or set(files) != {"operand"}:
            raise ValueError("toy source census requires exactly the selected original operand FILE")
        value = files["operand"]
        if (ObjectIdentity(value.identity.artifact_id, value.identity.payload_schema,
                value.record_version, value.identity.sha256) != specification.operand):
            raise ValueError("toy FILE substitutes the scientific source selection")
        return PreparedExperimentInputs({}, value)

    def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
        calls.append("prepare")
        value = method_inputs
        external = RecursiveExternalInput("external.toy-file", value.identity.artifact_id, value.identity.payload_schema,
            value.identity.media_type, value.identity.size_bytes, OutcomeAccess.DEVELOPMENT_VISIBLE,
            VisibilityCeiling.DEVELOPMENT_ONLY, value.identity.sha256)
        selected_draft = replace(draft, external_inputs=(external,), links=tuple(sorted((*draft.links,
            RecursiveInputLink("edge.toy-file", "source", "file", external_input_id=external.input_id,
                scientific_role=external.scientific_role)), key=lambda row: row.edge_id)))
        allocation = UnitAllocation("allocation.toy-file", (specification.identity,),
            (IndependentUnit("unit.toy-file", specification.specification_id, "family.toy", (), True),),
            (UnitRoleAssignment("unit.toy-file", "exposed"),))
        return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0), (),
            allocation, selected_draft, input_files=((external.input_id, value),), execution=execution,
            specification_record=specification)

    declaration = ExperimentProtocolDeclaration(choice.protocol_id, ToySpecification, prepare, "fixture-canonical-file",
        maximum_config_bytes=8192, input_record_types=(ToyMetadata,), bind_inputs=bind,
        validate_instance=lambda **kwargs: None, input_file_record_types=(ToyFile,))
    active = [declaration]
    monkeypatch.setattr(owner, "experiment_protocols", lambda: tuple(active))
    return SimpleNamespace(spec=spec, record=record, raw=raw, member=member, binding=binding,
        choice=choice, path=path, calls=calls, declaration=declaration, active=active, catalog=catalog)


def _load(selected):
    return owner.load_experiment_inputs(selected.spec, selected.path)


def _prepare(selected, *, execution=None):
    resolved = _load(selected)
    return owner.prepare_experiment(selected.spec, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=execution)


def _forbid_interpretation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("FILE preparation invoked its owning record constructor")
    monkeypatch.setattr(ToyFile, "__post_init__", forbidden)


def test_public_load_and_prepare_hash_exact_bytes_without_constructor_or_copy(selected, monkeypatch):
    before = {p.name: p.read_bytes() for p in selected.path.parent.iterdir()}
    _forbid_interpretation(monkeypatch)
    prepared = _prepare(selected, execution=ExecutionSelection(workers=1))
    assert prepared.executable and prepared.input_records == ()
    _, handle = prepared.input_files[0]
    assert handle.identity == selected.binding.identity and handle.path == selected.member
    assert handle.record_version == ToyFile.VERSION
    assert selected.calls == ["bind", "prepare"]
    assert {p.name: p.read_bytes() for p in selected.path.parent.iterdir()} == before


@pytest.mark.parametrize("damage", ("revision", "schema", "media", "undeclared", "uninstalled", "different-class", "digest", "source"))
def test_closed_file_contract_and_exact_scientific_source_substitutions_refuse(selected, monkeypatch, damage):
    binding = selected.binding
    if damage == "revision":
        binding = replace(binding, record_version="2.0.0")
    elif damage in {"schema", "media"}:
        binding = replace(binding, identity=replace(binding.identity, **({"payload_schema": "empirical-lawhood/testing/unknown-file"}
            if damage == "schema" else {"media_type": "application/octet-stream"})))
    elif damage == "undeclared":
        selected.active[0] = replace(selected.declaration, input_file_record_types=())
    elif damage == "uninstalled":
        monkeypatch.setattr(recursive_operations, "operation_catalog", lambda: ((), object(), {}))
    elif damage == "different-class":
        selected.active[0] = replace(selected.declaration, input_file_record_types=(OtherFile,))
    elif damage == "digest":
        selected.member.write_bytes(selected.raw.replace(b'7', b'8'))
    else:
        binding = replace(binding, identity=replace(binding.identity, artifact_id="operand.substituted"))
    selected.path.write_bytes(replace(selected.choice, files=(binding,)).canonical_bytes())
    _forbid_interpretation(monkeypatch)
    with pytest.raises(ValueError):
        _load(selected)


@pytest.mark.parametrize("where", ("protocol", "installed"))
def test_canonical_file_cannot_gain_an_ambiguous_raw_json_storage_alias(selected, monkeypatch, where):
    codec = RecursiveStorageCodec("codec.toy-raw-json", ToyFile.SCHEMA, ToyFile.VERSION, ArtifactProfile.RAW_SOURCE_BYTES,
        "application/json", ".json", _raw_json_stream, 1024)
    if where == "protocol":
        selected.active[0] = replace(selected.declaration, input_storage_codecs=(codec,))
    else:
        monkeypatch.setattr(recursive_operations, "operation_storage_codecs", lambda: (codec,))
    _forbid_interpretation(monkeypatch)
    with pytest.raises(ValueError, match="conflicts"):
        _load(selected)
    assert selected.calls == []


def test_file_only_record_cannot_enter_ordinary_eager_canonical_input_selection(selected, monkeypatch):
    choice = ExperimentInputSelection(selected.choice.selection_id, selected.choice.protocol_id,
        (ExperimentInputBinding("operand", selected.spec.operand, selected.member.name, len(selected.raw)),))
    selected.path.write_bytes(choice.canonical_bytes())
    _forbid_interpretation(monkeypatch)
    with pytest.raises(ValueError, match="registered exact codec/revision"):
        _load(selected)
    assert selected.calls == []


@pytest.mark.parametrize("damage", ("missing", "extra"))
def test_file_census_stays_domain_owned_and_complete(selected, damage):
    files = () if damage == "missing" else tuple(sorted((selected.binding,
        replace(selected.binding, key="extra")), key=lambda row: row.key))
    selected.path.write_bytes(replace(selected.choice, files=files).canonical_bytes())
    with pytest.raises(ValueError, match="source census"):
        _load(selected)


@pytest.mark.parametrize("location", ("file", "parent"))
def test_canonical_file_symlinks_refuse_before_domain_contact(selected, location):
    if location == "file":
        link = selected.member.with_name("linked.json")
        link.symlink_to(selected.member)
        relative = link.name
    else:
        directory = selected.member.parent / "originals"
        directory.mkdir()
        selected.member.rename(directory / selected.member.name)
        link = selected.member.parent / "linked-directory"
        link.symlink_to(directory, target_is_directory=True)
        relative = link.name + "/" + selected.member.name
    selected.path.write_bytes(replace(selected.choice, files=(replace(selected.binding, relative_path=relative),)).canonical_bytes())
    with pytest.raises(ValueError, match="symbolic links"):
        _load(selected)
    assert selected.calls == []


def test_exact_selected_size_refuses_before_hashing_despite_broad_allowance(selected, monkeypatch):
    from empirical_lawhood.infrastructure import bounded_io

    selected.path.write_bytes(replace(selected.choice, files=(replace(selected.binding, maximum_bytes=8192),)).canonical_bytes())
    selected.member.write_bytes(selected.raw + b"oversize")
    inode = selected.member.stat().st_ino
    original = bounded_io._regular_chunks

    def chunks(descriptor, *args, **kwargs):
        if os.fstat(descriptor).st_ino == inode:
            raise AssertionError("known oversize canonical file reached bulk hashing")
        yield from original(descriptor, *args, **kwargs)

    monkeypatch.setattr(bounded_io, "_regular_chunks", chunks)
    with pytest.raises(BoundedFileIOError, match="byte limit"):
        _load(selected)
    assert selected.calls == []


def test_existing_owning_decoder_refuses_invalid_toy_contents_after_public_preparation(selected, tmp_path):
    document = json.loads(selected.raw)
    document["value"]["signal"] = 0
    raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    selected.member.write_bytes(raw)
    digest = sha256(raw).hexdigest()
    selected.spec = replace(selected.spec, operand=replace(selected.spec.operand, object_fingerprint=digest))
    binding = replace(selected.binding, identity=replace(selected.binding.identity, sha256=digest, size_bytes=len(raw)),
        maximum_bytes=len(raw))
    selected.path.write_bytes(replace(selected.choice, files=(binding,)).canonical_bytes())
    plane = _plane(tmp_path / "custody")
    source = recursive_authoring.implementation_binding(ROOT)
    execution = ExecutionSelection(workers=1, environment_id="main.toy", output_root=plane.root.contract.canonical_path,
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source))
    prepared = _prepare(selected, execution=execution)
    destination = Path(plane.root.contract.canonical_path) / "refused-authoring"
    with pytest.raises(ValueError, match="owning toy decoder"):
        owner.author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=plane, output_dir=destination)
    assert not destination.exists()


@pytest.mark.parametrize("damage", ("undeclared", "symlink"))
def test_author_rechecks_file_contract_before_prospective_delegation(selected, monkeypatch, damage):
    from empirical_lawhood.api import prospective_experiment
    from empirical_lawhood.runtime.execution_envelope import (
        ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec, NonTimeResourceBudget,
    )
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
    from tests.experiment_entry_support import entry_package_for_draft
    from tests.runtime_platform.test_candidate_compiler import _fixture
    from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture

    prepared = _prepare(selected, execution=ExecutionSelection(workers=1))
    root, _ = _fixture()
    root = replace(root, source_materializations=())
    draft = replace(prepared.draft, development_study=None, prospective_draft=root)
    formal = _standard_fixture()[1]
    budget = NonTimeResourceBudget("budget.toy-file", 1, 1024, 1024, 1, 1024)
    cell = ExecutionResourceTaskCellSpec("cell.toy-file", "source", "child.toy-file", None, None,
        1, 0, 0, False, budget, None, None, None)
    resources = ExecutionResourceEnvelopeSpec("resources.toy-file", ObjectIdentity("extensions.toy-file",
        "empirical-lawhood/runtime/issued-extension-set", "1.0.0", "a" * 64), (cell,),
        (ChildResourceTokenLimit("child.toy-file", 0, 0),), (), (), (), None, None, 1, 1024, (), (), "b" * 64,
        True, True, True, True)
    # A typed unissued partial prospective graph suffices to exercise this
    # pre-delegation guard; no candidate, issue or worker is constructed.
    spec = RecursiveProspectiveAuthoringSpec("specification.toy-file.prospective", draft, entry_package_for_draft(root),
        formal.formal_methods, formal.source_inventories, (), root.design_inputs, resources)
    prepared = replace(prepared, draft=draft, prospective_spec=spec)
    if damage == "undeclared":
        selected.active[0] = replace(selected.declaration, input_file_record_types=())
    else:
        original = selected.member.read_bytes()
        target = selected.member.with_name("target.json")
        target.write_bytes(original)
        selected.member.unlink()
        selected.member.symlink_to(target)
    monkeypatch.setattr(prospective_experiment, "author_prepared_prospective_experiment",
        lambda **kwargs: pytest.fail("unvalidated FILE reached prospective author"))
    with pytest.raises(ValueError, match="storage codec/revision|symbolic links"):
        owner.author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=object(), output_dir="unused")
