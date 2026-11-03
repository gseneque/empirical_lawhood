# SPDX-License-Identifier: MPL-2.0
"""Public exact input revision conformance, with exposed software sources only."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.api import recursive_authoring, recursive_operations
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory, recursive_operation_binding
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec
from tests.runtime_platform.test_recursive_compiler import Config, SourceConfig, UseConfig, fixture
from tests.test_recursive_public_service import _plane
from tests.test_rubisco_serialized_nve_custody import (
    admitted as admitted, durable_admitted as durable_admitted,
    original as original, reuse_admitted as reuse_admitted,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class EarlierInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/public-revision-input"
    record_id: str
    measurement: Decimal


@dataclass(frozen=True, slots=True)
class CurrentInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = EarlierInput.SCHEMA
    VERSION: ClassVar[str] = "1.1.0"
    record_id: str
    measurement: Decimal
    uncertainty: Decimal


@dataclass(frozen=True, slots=True)
class ConflictingInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = EarlierInput.SCHEMA
    record_id: str
    incompatible_meaning: str


@dataclass(frozen=True, slots=True)
class ProspectiveInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/fixtures/reference-source"
    source: str


def _no_runner():
    raise AssertionError("public input preparation constructed a scientific runner")


def _factories(registrations, registry, codecs):
    return tuple(RecursiveOperationProviderFactory(
        recursive_operation_binding(registration=row, manifest=registry.resolve(
            row.selection.capability_key, row.selection.capability_version)), row,
        registry.resolve(row.selection.capability_key, row.selection.capability_version),
        _no_runner, codecs) for row in registrations)


def _shared_source(raw, *, supplier_types=(EarlierInput, CurrentInput), consumer_types=(EarlierInput, CurrentInput),
                   selected=("source", "use"), fallback=None, storage_codecs=(), media="application/json"):
    """Use the existing two-node dependency fixture, with one shared original."""
    draft, registrations, registry = fixture()
    history = RecursivePortContract("history", EarlierInput.SCHEMA, media, 10_000)
    registrations = (replace(registrations[0], input_ports=(history,), input_record_types=supplier_types,
                             storage_codecs=storage_codecs),
        replace(registrations[1], input_ports=(history, *registrations[1].input_ports), input_record_types=consumer_types,
                storage_codecs=storage_codecs))
    manifests = tuple(replace(row, input_schema_ids=tuple(sorted({*row.input_schema_ids, EarlierInput.SCHEMA})))
                      for row in registry.capabilities)
    registry = replace(registry, capabilities=manifests)
    external = RecursiveExternalInput("external.original", "original.exposed-measurement", EarlierInput.SCHEMA,
        media, 10_000, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        sha256(raw).hexdigest(), "HISTORY")
    links = tuple(sorted((*draft.links,
        RecursiveInputLink("edge.source.history", "source", "history", external_input_id=external.input_id),
        RecursiveInputLink("edge.use.history", "use", "history", external_input_id=external.input_id)),
        key=lambda row: row.edge_id))
    draft = replace(draft, links=links, external_inputs=(external,), selected_operation_ids=selected)
    codecs = {row.SCHEMA: row for row in (Config, SourceConfig, UseConfig)}
    if fallback is not None:
        codecs[fallback.SCHEMA] = fallback
    return draft, registrations, registry, codecs


def _author_shared(tmp_path, monkeypatch, raw, **choices):
    draft, registrations, registry, codecs = _shared_source(raw, **choices)
    factories = _factories(registrations, registry, codecs)
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    plane = _plane(tmp_path / "selected")
    source = tmp_path / "original.json"
    source.write_bytes(raw)
    destination = tmp_path / "selected/authored"
    result = recursive_authoring.author_recursive_wave(draft=draft, project_root=ROOT,
        artifact_writer=plane, output_dir=destination, input_bindings=(("external.original", source),))
    return result, plane, destination


@pytest.mark.parametrize("record", (EarlierInput("original.old", Decimal("1.2300")),
    CurrentInput("original.current", Decimal("1.2300"), Decimal(".0100"))))
def test_public_author_preserves_exact_revisions_across_supplier_and_downstream_consumer(tmp_path, monkeypatch, record):
    raw = record.canonical_bytes()
    result, plane, directory = _author_shared(tmp_path, monkeypatch, raw)
    assert result["task_count"] == 2 and result["native_contact"] == "none"
    assert result["scientific_authority"] == "NONE" and result["qualification"] == "NOT_ESTABLISHED"
    for lazy in (False, True):
        packet, draft, _, payloads = recursive_authoring.load_authored_wave(
            directory=directory, artifact_writer=plane, lazy_payloads=lazy)
        members = tuple(row for row in packet.members if row.identity.object_schema == record.SCHEMA)
        assert len(members) == 1
        member = members[0]
        assert member.identity.object_version == record.VERSION
        assert member.identity.object_fingerprint == sha256(raw).hexdigest()
        assert payloads[member.filename] == raw
        assert decode_canonical_bytes(payloads[member.filename], type(record), maximum_bytes=10_000) == record
        assert {row.consumer_node_id for row in draft.links if row.external_input_id == "external.original"} == {"source", "use"}


@pytest.mark.parametrize("restrict", ("supplier", "downstream"))
def test_every_actual_selected_consumer_refuses_unsupported_revision_before_any_publication(tmp_path, monkeypatch, restrict):
    raw = CurrentInput("original.current", Decimal("1.23"), Decimal(".01")).canonical_bytes()
    choices = {"supplier_types" if restrict == "supplier" else "consumer_types": (EarlierInput,)}
    with pytest.raises(ValueError, match="revision.*outside"):
        _author_shared(tmp_path, monkeypatch, raw, **choices)
    assert not (tmp_path / "selected/authored").exists()
    assert tuple((tmp_path / "selected").rglob("*.manifest.json")) == ()


def test_unselected_later_alternative_does_not_narrow_selected_source_revision(tmp_path, monkeypatch):
    raw = CurrentInput("original.current", Decimal("1.23"), Decimal(".01")).canonical_bytes()
    result, _, _ = _author_shared(tmp_path, monkeypatch, raw, consumer_types=(EarlierInput,), selected=("source",))
    assert result["task_count"] == 1


def test_explicit_vendor_json_record_uses_same_strict_public_input_contract(tmp_path, monkeypatch):
    from empirical_lawhood.runtime.recursive_record_codecs import validate_declared_recursive_input_payload
    raw = EarlierInput("original.old", Decimal("1.2300")).canonical_bytes()
    media = "application/vnd.empirical-lawhood.exposed-record+json"
    draft, registrations, _, codecs = _shared_source(raw, media=media)
    assert validate_declared_recursive_input_payload(draft=draft, registrations=registrations,
        fallback_codecs=codecs, logical_artifact_id="original.exposed-measurement", payload=raw) is None
    result, _, _ = _author_shared(tmp_path, monkeypatch, raw, media=media)
    assert result["task_count"] == 2 and result["native_contact"] == "none"


@pytest.mark.parametrize("damage", ("unknown-revision", "extra-field", "duplicate-key", "float", "not-canonical"))
def test_public_author_exact_hash_cannot_bypass_strict_declared_record_decoding(tmp_path, monkeypatch, damage):
    raw = EarlierInput("original.old", Decimal("1.23")).canonical_bytes()
    if damage == "unknown-revision":
        raw = raw.replace(b'"version":"1.0.0"', b'"version":"9.0.0"')
    elif damage == "extra-field":
        raw = raw.replace(b'"record_id":', b'"extra":1,"record_id":')
    elif damage == "duplicate-key":
        raw = raw.replace(b'"record_id":"original.old"', b'"record_id":"original.old","record_id":"original.old"')
    elif damage == "float":
        raw = raw.replace(b'{"decimal":"1.23"}', b'1.23')
    else:
        raw = raw.rstrip(b"\n")
    with pytest.raises((ValueError, TypeError)):
        _author_shared(tmp_path, monkeypatch, raw)
    assert not (tmp_path / "selected/authored").exists()
    assert tuple((tmp_path / "selected").rglob("*.manifest.json")) == ()


def test_actual_public_catalog_refuses_conflicting_installed_meanings_of_same_exact_revision(monkeypatch):
    raw = EarlierInput("original.old", Decimal("1.23")).canonical_bytes()
    _, registrations, registry, codecs = _shared_source(raw,
        supplier_types=(EarlierInput,), consumer_types=(ConflictingInput,))
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: _factories(registrations, registry, codecs))
    with pytest.raises(ValueError, match="disagree.*schema/revision"):
        recursive_operations.operation_catalog()


def test_global_output_fallback_cannot_widen_explicit_selected_input_revision(tmp_path, monkeypatch):
    raw = CurrentInput("original.current", Decimal("1.23"), Decimal(".01")).canonical_bytes()
    with pytest.raises(ValueError, match="revision.*outside"):
        _author_shared(tmp_path, monkeypatch, raw, consumer_types=(EarlierInput,), fallback=CurrentInput)
    assert not (tmp_path / "selected/authored").exists()


def test_fallback_consumer_must_itself_accept_original_revision(tmp_path, monkeypatch):
    raw = CurrentInput("original.current", Decimal("1.23"), Decimal(".01")).canonical_bytes()
    with pytest.raises(ValueError, match="installed strict schema/revision codec"):
        _author_shared(tmp_path, monkeypatch, raw, consumer_types=(), fallback=EarlierInput)
    assert not (tmp_path / "selected/authored").exists()


def _no_binary_validation(source, request, *, size):
    raise AssertionError("declared canonical input reached binary structural validation")


def test_global_binary_storage_codec_cannot_bypass_explicit_canonical_input_contract(tmp_path, monkeypatch):
    raw = EarlierInput("original.old", Decimal("1.23")).canonical_bytes()
    codec = RecursiveStorageCodec("codec.fixture-incompatible-record-carrier", EarlierInput.SCHEMA,
        EarlierInput.VERSION, ArtifactProfile.RAW_SOURCE_BYTES, "application/json", ".raw",
        _no_binary_validation, 10_000)
    with pytest.raises(ValueError, match="registered raw JSON storage conflicts with a strict canonical record schema"):
        _author_shared(tmp_path, monkeypatch, raw, storage_codecs=(codec,))
    assert not (tmp_path / "selected/authored").exists()
    assert tuple((tmp_path / "selected").rglob("*.manifest.json")) == ()


def _internal_source_contract(produced, accepted):
    draft, registrations, registry = fixture()
    registrations = tuple(replace(row,
        input_ports=tuple(replace(port, payload_schema=EarlierInput.SCHEMA) for port in row.input_ports),
        outputs=tuple(replace(output, payload_schema=EarlierInput.SCHEMA) for output in row.outputs),
        input_record_types=(accepted if type(accepted) is tuple else (accepted,)) if row.input_ports else ())
        for row in registrations)
    registry = replace(registry, capabilities=tuple(replace(row,
        input_schema_ids=tuple(sorted({*row.input_schema_ids, EarlierInput.SCHEMA})),
        output_schema_ids=(EarlierInput.SCHEMA,)) for row in registry.capabilities))
    codecs = {row.SCHEMA: row for row in (Config, SourceConfig, UseConfig, produced)}
    return draft, registrations, registry, codecs


@pytest.mark.parametrize("produced,accepted", ((EarlierInput, CurrentInput), (CurrentInput, EarlierInput)))
def test_public_author_refuses_internal_supplier_revision_outside_downstream_contract(tmp_path, monkeypatch, produced, accepted):
    draft, registrations, registry, codecs = _internal_source_contract(produced, accepted)
    factories = _factories(registrations, registry, codecs)
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    plane = _plane(tmp_path / "selected")
    with pytest.raises(ValueError, match="supplier record revision.*outside"):
        recursive_authoring.author_recursive_wave(draft=draft, project_root=ROOT,
            artifact_writer=plane, output_dir=tmp_path / "selected/authored")
    assert not (tmp_path / "selected/authored").exists()
    assert tuple((tmp_path / "selected").rglob("*.manifest.json")) == ()


def test_public_author_accepts_current_internal_revision_explicitly_declared_by_downstream(tmp_path, monkeypatch):
    draft, registrations, registry, codecs = _internal_source_contract(CurrentInput, (EarlierInput, CurrentInput))
    factories = _factories(registrations, registry, codecs)
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    plane = _plane(tmp_path / "selected")
    result = recursive_authoring.author_recursive_wave(draft=draft, project_root=ROOT,
        artifact_writer=plane, output_dir=tmp_path / "selected/authored")
    assert result["task_count"] == 2 and result["native_contact"] == "none"


def _sampling_config(admitted, tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.operation_bindings import SamplingOperationConfig
    environment = dict(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"),
        OPENMM_PLUGIN_DIR=str(tmp_path / "unentered-plugins"), OPENMM_CPU_THREADS="1",
        OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
        NUMEXPR_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
    return SamplingOperationConfig("config.rubisco-insilico-sampling.nve-control", "nve-control",
        admitted.plan.canonical_bytes().decode(), admitted.source, str(ROOT),
        str(tmp_path / "unentered-specialist-invocation.json"), tuple(sorted(environment.items())))


def test_installed_current_nve_public_author_retains_original_older_chemical_bytes(tmp_path, admitted):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import operation_bindings as ob
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import SerializedDurableChemicalForcePlan
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.recursive_translation import sampling_control_draft
    config = _sampling_config(admitted, tmp_path)
    chemical = admitted.plan.chemical_controls
    assert type(chemical) is SerializedDurableChemicalForcePlan and chemical.VERSION == "1.2.0"
    assert config.plan.VERSION == "1.2.0"
    registered = next(row for row in recursive_operations.operation_catalog()[0]
                      if row.selection.capability_key == config.node_id)
    assert type(chemical) in registered.input_record_types
    assert {row.VERSION for row in registered.input_record_types if row.SCHEMA == chemical.SCHEMA} == {"1.1.0", "1.2.0", "1.3.0", "1.4.0"}
    draft = sampling_control_draft(config, draft_id="draft.exposed-public-nve-input-revisions")
    records = (admitted.plan, chemical, admitted.source, admitted.relaxed, admitted.envelope)
    by_identity = {(row.identity if hasattr(row, "identity") else ob.p.identity(row)): row for row in records}
    assert set(by_identity) == set(config.operands)
    bindings = []
    originals = {}
    for external in draft.external_inputs:
        identity = next(row for row in config.operands if row.object_id == external.logical_artifact_id)
        raw = by_identity[identity].canonical_bytes()
        path = tmp_path / (sha256(external.input_id.encode()).hexdigest() + ".json")
        path.write_bytes(raw)
        bindings.append((external.input_id, path))
        originals[identity.object_fingerprint] = raw
    plane = _plane(tmp_path / "selected")
    directory = tmp_path / "selected/authored"
    result = recursive_authoring.author_recursive_wave(draft=draft, project_root=ROOT,
        artifact_writer=plane, output_dir=directory, input_bindings=tuple(bindings))
    assert result["task_count"] == 1 and result["native_contact"] == "none"
    assert result["scientific_authority"] == "NONE" and result["qualification"] == "NOT_ESTABLISHED"
    packet, retained, _, payloads = recursive_authoring.load_authored_wave(directory=directory, artifact_writer=plane)
    external_members = tuple(row for row in packet.members if row.filename.startswith("external-"))
    assert len(external_members) == 5
    assert {row.identity.object_fingerprint for row in external_members} == set(originals)
    for member in external_members:
        assert payloads[member.filename] == originals[member.identity.object_fingerprint]
    chemical_member = next(row for row in external_members if row.identity.object_schema == chemical.SCHEMA)
    assert chemical_member.identity.object_version == "1.2.0"
    assert payloads[chemical_member.filename] == chemical.canonical_bytes()
    assert retained.development_study.assigned_unit_ids == (ob.p.UNIT,)
    assert len(config.plan.full_census) == 96 and len(config.plan.selected_cases) == 1
    assert not Path(config.invocation_path).exists()
    assert not Path(admitted.plan.workdir).exists()


def test_public_current_nve_refuses_retained_chemical11_engine_source_disagreement_without_rewriting(tmp_path, reuse_admitted):
    from tests.test_rubisco_serialized_nve_custody import admitted as original_custody_fixture
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import operation_bindings as ob
    selected = original_custody_fixture.__wrapped__(reuse_admitted)
    chemical = selected.plan.chemical_controls
    assert chemical.VERSION == "1.1.0"
    assert chemical.source == ob.p.identity(selected.source)
    assert chemical.engine_inventory_sha256 != selected.source.engine_inventory_sha256
    originals = tuple(row.canonical_bytes() for row in (chemical, selected.plan, selected.source, selected.envelope))
    with pytest.raises(ValueError, match="exact original source/engine inputs"):
        _sampling_config(selected, tmp_path)
    assert tuple(row.canonical_bytes() for row in (chemical, selected.plan, selected.source, selected.envelope)) == originals
    assert not (tmp_path / "unentered-specialist-invocation.json").exists()


def _revisioned_prospective_fixture(monkeypatch, raw, *, input_record_types=(ProspectiveInput,)):
    """Rebind only the disclosed existing source fixture's exact byte metadata."""
    from empirical_lawhood.api import recursive_prospective_authoring as owner
    from tests.runtime_platform import test_recursive_prospective_workflow as support
    from tests.experiment_entry_support import standard_authoring_for_draft
    actual_source = support._actual_source
    original_author = owner.author_recursive_prospective
    observations = {"entered": 0, "refused_before_publication": 0}

    def source(compilation):
        compiled, _, _, _, config = actual_source(compilation)
        selected_raw = raw(compiled) if callable(raw) else raw
        qualification = compiled.candidate_context.qualifications[0]
        digest = sha256(selected_raw).hexdigest()
        qualification = replace(qualification, content_sha256=digest,
            materialization=replace(qualification.materialization, object_fingerprint=digest))
        config = replace(config, content_sha256=digest, expected_size_bytes=len(selected_raw), maximum_bytes=len(selected_raw))
        source = replace(compiled.candidate_draft.source_materializations[0],
            materialization=qualification.materialization, content_sha256=digest, source_config_sha256=config.fingerprint(),
            qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification))
        draft = replace(compiled.draft, prospective_draft=replace(compiled.candidate_draft, source_materializations=(source,)),
            external_inputs=tuple(replace(row, expected_content_sha256=digest) for row in compiled.draft.external_inputs))
        compiled = compile_recursive_wave(draft=draft, registrations=support._registrations(compiled), registry=compiled.registry,
            implementation_commit="a" * 40, qualifications=(qualification,),
            known_design_inputs=compiled.candidate_context.known_design_inputs, output_codecs=compiled.output_codecs)
        assert compiled.candidate_report.candidate is not None
        standard, formal = standard_authoring_for_draft(compiled.candidate_draft, compiled.candidate_context,
            formal_method_capability_key="recursive-fixture.evaluate")
        return compiled, standard, formal, selected_raw, config

    def author(**kwargs):
        observations["entered"] += 1
        registrations, registry, codecs = kwargs["composition"]
        kwargs["composition"] = (tuple(replace(row, input_record_types=input_record_types)
            if any(port.payload_schema == ProspectiveInput.SCHEMA for port in row.input_ports) else row
            for row in registrations), registry, codecs)
        config_digests = {row.config_identity.object_fingerprint for row in kwargs["spec"].draft.operations
                          if row.node_id in kwargs["spec"].draft.selected_operation_ids}
        aliases = {row.logical_artifact_id for row in kwargs["spec"].external_operands if row.content_sha256 in config_digests}
        kwargs["input_bindings"] = tuple((key, path) for key, path in kwargs["input_bindings"] if key not in aliases)
        # The existing scaffold publishes its disclosed fixtures for preview.
        # From this actual public call onward, a refusal must precede publication.
        from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
        original_publish = ExternalCandidateInputPublisher.publish
        original_publish_many = ExternalCandidateInputPublisher.publish_many
        publications = []
        def publish(self, payload, **options):
            publications.append(sha256(payload).hexdigest())
            return original_publish(self, payload, **options)
        def publish_many(self, payloads, **options):
            publications.append("publish_many entered")
            return original_publish_many(self, payloads, **options)
        with monkeypatch.context() as scoped:
            scoped.setattr(ExternalCandidateInputPublisher, "publish", publish)
            scoped.setattr(ExternalCandidateInputPublisher, "publish_many", publish_many)
            try:
                return original_author(**kwargs)
            except (ValueError, TypeError):
                assert publications == []
                assert not Path(kwargs["output_dir"]).exists()
                observations["refused_before_publication"] += 1
                raise

    monkeypatch.setattr(support, "_actual_source", source)
    monkeypatch.setattr(owner, "author_recursive_prospective", author)
    return support, observations


@pytest.mark.parametrize("damage", ("unknown-revision", "extra-field", "duplicate-key", "not-canonical", "unframed-source"))
def test_public_prospective_explicit_record_contract_refuses_exactly_hashed_invalid_revision_before_publication(tmp_path, monkeypatch, damage):
    raw = ProspectiveInput("exposed-source-only").canonical_bytes()
    if damage == "unknown-revision":
        raw = raw.replace(b'"version":"1.0.0"', b'"version":"9.0.0"')
    elif damage == "extra-field":
        raw = raw.replace(b'"source":', b'"extra":1,"source":')
    elif damage == "duplicate-key":
        raw = raw.replace(b'"source":"exposed-source-only"', b'"source":"exposed-source-only","source":"exposed-source-only"')
    elif damage == "not-canonical":
        raw = raw.rstrip(b"\n")
    else:
        raw = b'{"schema":"empirical-lawhood/testing/fixtures/reference-source","source":"exposed-source-only"}\n'
    support, observations = _revisioned_prospective_fixture(monkeypatch, raw)
    with pytest.raises((ValueError, TypeError)):
        support._authored_handoff_fixture(tmp_path, monkeypatch)
    assert observations == {"entered": 1, "refused_before_publication": 1}


def test_public_prospective_existing_config_digest_alias_cannot_skip_declared_external_record_validation(tmp_path, monkeypatch):
    def selected_config_bytes(compiled):
        return compiled.config_inputs[0].payload
    support, observations = _revisioned_prospective_fixture(monkeypatch, selected_config_bytes)
    with pytest.raises(ValueError, match="schema/revision envelope"):
        support._authored_handoff_fixture(tmp_path, monkeypatch)
    assert observations == {"entered": 1, "refused_before_publication": 1}


def test_public_prospective_declared_original_record_preserves_exact_bytes_on_delivery(tmp_path, monkeypatch):
    raw = ProspectiveInput("exposed-source-only").canonical_bytes()
    support, observations = _revisioned_prospective_fixture(monkeypatch, raw)
    handoff, _, _, plane, observed, _, _, _ = support._authored_handoff_fixture(tmp_path, monkeypatch)
    assert observed == raw
    assert observations == {"entered": 1, "refused_before_publication": 0}
    location = "candidate-inputs/sha256/" + sha256(raw).hexdigest()[:2] + "/" + sha256(raw).hexdigest()
    assert plane.root.resolve(location, for_write=False).read_bytes() == raw
    assert not handoff.compilation.run_plan
    supplier = handoff.platform_ports[0].port.supplier
    assert callable(supplier.validate_payload)
    source_spec = next(row for task in handoff.projection.tasks for row in task.external_inputs
                      if row.expected_payload_schema == ProspectiveInput.SCHEMA)
    payload = supplier.resolve_input(source_spec)
    try:
        assert b"".join(payload.chunks()) == raw
    finally:
        payload.close()


def test_public_prospective_legacy_unframed_qualified_source_keeps_original_format(tmp_path, monkeypatch):
    from tests.runtime_platform import test_recursive_prospective_workflow as support
    registrations = support._registrations

    def legacy_registrations(compilation):
        return tuple(replace(row, input_record_types=())
            if any(port.payload_schema == ProspectiveInput.SCHEMA for port in row.input_ports) else row
            for row in registrations(compilation))

    monkeypatch.setattr(support, "_registrations", legacy_registrations)
    raw = b'{"schema":"empirical-lawhood/testing/fixtures/reference-source","source":"exposed legacy source"}\n'
    support, observations = _revisioned_prospective_fixture(monkeypatch, raw, input_record_types=())
    handoff, _, _, plane, observed, _, _, _ = support._authored_handoff_fixture(tmp_path, monkeypatch)
    assert observed == raw
    assert observations == {"entered": 1, "refused_before_publication": 0}
    assert b'"version"' not in raw and b'"value"' not in raw
    supplier = handoff.platform_ports[0].port.supplier
    source_spec = next(row for task in handoff.projection.tasks for row in task.external_inputs
                      if row.expected_payload_schema == ProspectiveInput.SCHEMA)
    payload = supplier.resolve_input(source_spec)
    try:
        assert b"".join(payload.chunks()) == raw
    finally:
        payload.close()
    digest = sha256(raw).hexdigest()
    assert plane.root.resolve(f"candidate-inputs/sha256/{digest[:2]}/{digest}", for_write=False).read_bytes() == raw


@pytest.mark.parametrize("returned", (False, True, ()))
def test_public_prospective_delivery_refuses_non_none_code_owned_predicate_result(tmp_path, monkeypatch, returned):
    raw = ProspectiveInput("exposed-source-only").canonical_bytes()
    support, _ = _revisioned_prospective_fixture(monkeypatch, raw)
    handoff, _, _, _, _, _, _, _ = support._authored_handoff_fixture(tmp_path, monkeypatch)
    supplier = handoff.platform_ports[0].port.supplier
    source_spec = next(row for task in handoff.projection.tasks for row in task.external_inputs
                      if row.expected_payload_schema == ProspectiveInput.SCHEMA)
    calls = []
    def refusal(**kwargs):
        calls.append(kwargs)
        return returned
    supplier.validate_payload = refusal
    with pytest.raises(ValueError, match="return None"):
        supplier.resolve_input(source_spec)
    assert calls == [{"logical_artifact_id": source_spec.logical_artifact_id, "payload": raw}]
