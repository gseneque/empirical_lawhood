# SPDX-License-Identifier: MPL-2.0
"""Instance association survives independently rebuilt exposed byte custody.

All published inputs are disclosed software fixtures. Rebuilding their packet,
manifests and commit markers tests scientific association beyond byte integrity;
it supplies no issue, execution, reveal or qualification authority.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.api import experiment_preparation as experiments
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentInstanceBinding
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from tests.test_recursive_public_service import _plane
from tests.test_rubisco_experiment_preparation import _records, _specification


ROOT = Path(__file__).resolve().parents[1]


def _forbidden(*_args, **_kwargs):
    raise AssertionError("instance conformance reached publication or scientific workers")


def _prepare(specification, records, plane):
    from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.experiment_inputs import (
        bind_kinetic_experiment_inputs,
    )

    resolved = bind_kinetic_experiment_inputs(specification, records)
    source = author.implementation_binding(ROOT)
    return experiments.prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs,
        execution=ExecutionSelection(workers=1, environment_id="rubisco-prediction",
            source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source),
            output_root=plane.root.contract.canonical_path))


def _pair(plane):
    records = _records()
    first = _specification(records)
    second = replace(first, specification_id="specification.rubisco.instance-binding.changed-action",
        query=replace(first.query, co2_um=Decimal("20")))
    return _prepare(first, records, plane), _prepare(second, records, plane)


def _publish(preparation, plane, name):
    destination = Path(plane.root.contract.canonical_path) / name
    report = experiments.author_prepared_experiment(preparation=preparation, project_root=ROOT,
        artifact_writer=plane, output_dir=destination)
    packet, draft, _, payloads = author.load_authored_wave(directory=destination, artifact_writer=plane)
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    assert draft == preparation.draft
    return packet, dict(payloads), destination


def _identity(record, name):
    return ObjectIdentity.from_record(name, record)


def _source_name(identity):
    return "experiment-source-" + sha256(identity.object_id.encode()).hexdigest() + ".json"


def _instance(payloads):
    return decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)


def _files(directory):
    return {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def _rebuild_byte_custody(tmp_path, original_packet, payloads):
    """Publish a fresh consistent package without overwriting any source bytes."""
    plane = _plane(tmp_path / "rebuilt-exposed-custody")
    directory = Path(plane.root.contract.canonical_path) / "authored"
    directory.mkdir()
    old = {member.filename: member for member in original_packet.members}
    members = []
    for name, raw in sorted(payloads.items()):
        document = json.loads(raw)
        object_id = (document["value"]["draft_id"] if name == "draft.json"
                     else old[name].identity.object_id if name in old
                     else "recursive-member." + name.removesuffix(".json"))
        identity = ObjectIdentity(object_id, document["schema"], document["version"], sha256(raw).hexdigest())
        members.append(RecursiveWaveMember(name, identity, len(raw)))
    by_name = {member.filename: member.identity for member in members}
    packet = AuthoredRecursiveWave(original_packet.packet_id, by_name["draft.json"],
        by_name["implementation.json"], tuple(members))
    rows = {**payloads, "authored-wave.json": packet.canonical_bytes()}
    requests = tuple(ArtifactWriteRequest(
        packet.packet_id + "." + name.removesuffix(".json"), "authored/" + name,
        json.loads(raw)["schema"], ArtifactProfile.CANONICAL_JSON, "application/json",
        packet.packet_id, "authored", raw, VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE) for name, raw in sorted(rows.items()))
    plane.write_batch(requests)
    # Every physical manifest/commit authenticates; refusal must come from the
    # selected instance association, rather than stale digests or fake custody.
    manifests = tuple(decode_artifact_manifest((directory / (name + ".manifest.json")).read_bytes(), maximum_bytes=None)
        for name in rows)
    plane.verify_manifests(manifests)
    return plane, directory


def _replace_projection_identity(instance, raw):
    document = json.loads(raw)
    return replace(instance, scientific_projection=ObjectIdentity(
        "recursive-member.scientific-projection", document["schema"], document["version"], sha256(raw).hexdigest()))


def test_real_authored_instance_keeps_original_records_and_exact_design_projection(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "original-custody")
    preparation, _ = _pair(plane)
    original_bytes = {key: record.canonical_bytes() for key, record in preparation.design_records}
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    _, payloads, _ = _publish(preparation, plane, "original")
    instance = _instance(payloads)
    assert instance.specification == preparation.specification
    assert instance.allocation == preparation.allocation.identity
    assert instance.draft == _identity(preparation.draft, preparation.draft.draft_id)
    assert instance.campaign == _identity(preparation.draft.campaign, preparation.draft.campaign.campaign_id)
    assert instance.sources == tuple(_identity(record, key) for key, record in preparation.design_records)
    assert all(payloads[_source_name(reference)] == original_bytes[reference.object_id] for reference in instance.sources)
    assert payloads["experiment-specification.json"] == preparation.specification_record.canonical_bytes()
    assert payloads["experiment-allocation.json"] == preparation.allocation.canonical_bytes()


@pytest.mark.parametrize("mutation", ("valid-other-draft", "missing-source", "mutated-source", "wrong-source-codec"))
def test_author_refuses_a_decoupled_valid_draft_or_original_source_before_publication(tmp_path, monkeypatch, mutation):
    plane = _plane(tmp_path / "unentered-custody")
    original, other = _pair(plane)
    if mutation == "valid-other-draft":
        preparation = replace(original, draft=other.draft, input_records=other.input_records)
    elif mutation == "missing-source":
        preparation = replace(original, design_records=original.design_records[:-1])
    else:
        sources = dict(original.design_records)
        key = original.specification_record.source_query.object_id
        sources[key] = (replace(sources[key], co2_um=Decimal("40")) if mutation == "mutated-source"
                        else original.specification_record)
        preparation = replace(original, design_records=tuple(sorted(sources.items())))
    before = _files(tmp_path)
    monkeypatch.setattr(plane, "write", _forbidden)
    monkeypatch.setattr(plane, "write_stream", _forbidden)
    with pytest.raises((ValueError, TypeError), match="instance|original source|scientific sources|codec"):
        experiments.author_prepared_experiment(preparation=preparation, project_root=ROOT,
            artifact_writer=plane, output_dir=Path(plane.root.contract.canonical_path) / "refused")
    assert _files(tmp_path) == before
    assert not (Path(plane.root.contract.canonical_path) / "refused").exists()


@pytest.mark.parametrize("result", (True, False, 0, (), {}))
def test_registered_instance_callback_must_return_exact_none_before_publication(tmp_path, monkeypatch, result):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    plane = _plane(tmp_path / "unentered-custody")
    original, _ = _pair(plane)
    declarations = experiments.experiment_protocols()
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", tuple(
        replace(row, validate_instance=lambda **_kwargs: result) if row.specification_type is type(original.specification_record)
        else row for row in declarations))
    monkeypatch.setattr(plane, "write", _forbidden)
    monkeypatch.setattr(plane, "write_stream", _forbidden)
    with pytest.raises(ValueError, match="return None or raise on refusal"):
        experiments.author_prepared_experiment(preparation=original, project_root=ROOT,
            artifact_writer=plane, output_dir=Path(plane.root.contract.canonical_path) / "refused")
    assert not tuple(Path(plane.root.contract.canonical_path).iterdir())


def test_registered_instance_validator_is_required_at_authoring_and_retained_read(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    plane = _plane(tmp_path / "original-custody")
    original, _ = _pair(plane)
    _, _, directory = _publish(original, plane, "original")
    declarations = experiments.experiment_protocols()
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", tuple(
        replace(row, validate_instance=None) if row.specification_type is type(original.specification_record)
        else row for row in declarations))
    with pytest.raises(ValueError, match="registered scientific instance validator"):
        author.load_authored_wave(directory=directory, artifact_writer=plane)
    with pytest.raises(ValueError, match="registered scientific instance validator"):
        experiments.author_prepared_experiment(preparation=original, project_root=ROOT,
            artifact_writer=plane, output_dir=Path(plane.root.contract.canonical_path) / "refused")
    assert not (Path(plane.root.contract.canonical_path) / "refused").exists()


def test_retained_instance_callback_false_result_cannot_approve_a_valid_package(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    plane = _plane(tmp_path / "original-custody")
    original, _ = _pair(plane)
    _, _, directory = _publish(original, plane, "original")
    before = _files(tmp_path)
    declarations = experiments.experiment_protocols()
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", tuple(
        replace(row, validate_instance=lambda **_kwargs: False) if row.specification_type is type(original.specification_record)
        else row for row in declarations))
    with pytest.raises(ValueError, match="return None or raise on refusal"):
        author.load_authored_wave(directory=directory, artifact_writer=plane)
    assert _files(tmp_path) == before


def test_public_instance_boundaries_supply_actual_custody_to_registered_validator(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.api import experiment_runtime_bindings as bindings

    plane = _plane(tmp_path / "instance-custody")
    original, _ = _pair(plane)
    declaration = next(row for row in experiments.experiment_protocols()
        if row.specification_type is type(original.specification_record))
    actual_selection = bindings.experiment_runtime_binding
    calls = []

    def authenticate(*, artifact_writer, **arguments):
        assert artifact_writer is plane
        assert arguments["source_records"] == original.design_records
        declaration.validate_instance(**arguments)
        calls.append(artifact_writer)

    def selected(protocol):
        if protocol.protocol_id == declaration.protocol_id:
            return SimpleNamespace(authenticate_instance=authenticate, bootstrap_development_input_access=None)
        return actual_selection(protocol)

    monkeypatch.setattr(bindings, "experiment_runtime_binding", selected)
    _, payloads, directory = _publish(original, plane, "original")
    assert calls
    count = len(calls)
    author.load_authored_wave(directory=directory, artifact_writer=plane)
    assert len(calls) > count
    with pytest.raises(ValueError, match="actual publication custody"):
        author._authenticate_experiment_instance(payloads=payloads, draft=original.draft)


def test_custody_validator_cannot_return_false_to_approve_publication_or_read(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.api import experiment_runtime_bindings as bindings

    plane = _plane(tmp_path / "instance-custody")
    original, _ = _pair(plane)
    _, _, directory = _publish(original, plane, "original")
    before = _files(tmp_path)
    actual_selection = bindings.experiment_runtime_binding

    def selected(protocol):
        if protocol.specification_type is type(original.specification_record):
            return SimpleNamespace(authenticate_instance=lambda **arguments: False, bootstrap_development_input_access=None)
        return actual_selection(protocol)

    monkeypatch.setattr(bindings, "experiment_runtime_binding", selected)
    with pytest.raises(ValueError, match="return None or raise on refusal"):
        author.load_authored_wave(directory=directory, artifact_writer=plane)
    monkeypatch.setattr(plane, "write", _forbidden)
    monkeypatch.setattr(plane, "write_stream", _forbidden)
    with pytest.raises(ValueError, match="return None or raise on refusal"):
        experiments.author_prepared_experiment(preparation=original, project_root=ROOT,
            artifact_writer=plane, output_dir=Path(plane.root.contract.canonical_path) / "refused")
    assert _files(tmp_path) == before


@pytest.mark.parametrize("mutation", (
    "missing-specification", "missing-source", "mutated-original-query", "wrong-source-revision",
    "unknown-specification-codec", "mixed-draft", "mixed-allocation", "mixed-campaign", "mixed-projection",
))
def test_consistently_republished_byte_custody_cannot_bypass_instance_association(tmp_path, monkeypatch, mutation):
    plane = _plane(tmp_path / "original-custody")
    original, other = _pair(plane)
    packet, payloads, _ = _publish(original, plane, "original")
    original_bytes = _files(Path(plane.root.contract.canonical_path))
    instance = _instance(payloads)
    if mutation == "missing-specification":
        del payloads["experiment-specification.json"]
    elif mutation == "missing-source":
        missing = original.specification_record.source_query
        del payloads[_source_name(missing)]
        instance = replace(instance, sources=tuple(row for row in instance.sources if row != missing))
    elif mutation in ("mutated-original-query", "wrong-source-revision"):
        reference = original.specification_record.source_query
        name = _source_name(reference)
        record = decode_canonical_bytes(payloads[name], AssayQuery, maximum_bytes=None)
        if mutation == "mutated-original-query":
            record = replace(record, co2_um=Decimal("40"))
            payloads[name] = record.canonical_bytes()
            updated = _identity(record, reference.object_id)
        else:
            document = json.loads(payloads[name])
            document["version"] = "2.0.0"
            payloads[name] = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
            updated = replace(reference, object_version="2.0.0", object_fingerprint=sha256(payloads[name]).hexdigest())
        instance = replace(instance, sources=tuple(updated if row == reference else row for row in instance.sources))
    elif mutation == "unknown-specification-codec":
        instance = replace(instance, specification=replace(instance.specification,
            object_schema="empirical-lawhood/testing/undeclared-experiment-specification"))
    elif mutation in ("mixed-draft", "mixed-projection"):
        _, other_payloads, _ = _publish(other, plane, "other")
        if mutation == "mixed-projection":
            payloads["scientific-projection.json"] = other_payloads["scientific-projection.json"]
            instance = _replace_projection_identity(instance, payloads["scientific-projection.json"])
        else:
            # Every scientific/executable projection is valid for the other
            # action. The original spec/allocation/sources still select the first.
            retained_design = {name: raw for name, raw in payloads.items() if name.startswith("experiment-")}
            payloads = {**other_payloads, **retained_design}
            instance = _replace_projection_identity(instance, payloads["scientific-projection.json"])
            instance = replace(instance, draft=_identity(other.draft, other.draft.draft_id))
        original_bytes = _files(Path(plane.root.contract.canonical_path))
    elif mutation == "mixed-allocation":
        allocation = replace(original.allocation, roles=tuple(replace(row, role="different-analytical")
            for row in original.allocation.roles))
        payloads["experiment-allocation.json"] = allocation.canonical_bytes()
        instance = replace(instance, allocation=allocation.identity)
    else:
        draft = replace(original.draft, campaign=replace(original.draft.campaign,
            objective="A different source-conditioned campaign"))
        payloads["draft.json"] = draft.canonical_bytes()
        instance = replace(instance, draft=_identity(draft, draft.draft_id),
            campaign=_identity(draft.campaign, draft.campaign.campaign_id))
    payloads["experiment-instance.json"] = instance.canonical_bytes()
    rebuilt_plane, directory = _rebuild_byte_custody(tmp_path, packet, payloads)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    with pytest.raises((ValueError, TypeError), match="experiment|kinetic instance|scientific projection|installed specification owner"):
        author.load_authored_wave(directory=directory, artifact_writer=rebuilt_plane)
    assert _files(Path(plane.root.contract.canonical_path)) == original_bytes


def test_original_kinetic_scientific_root_guard_still_rejects_a_changed_question(tmp_path):
    plane = _plane(tmp_path / "unentered-custody")
    preparation, _ = _pair(plane)
    changed_root = replace(preparation.draft.development_study, question="Unrelated biological qualification claim")
    changed = replace(preparation.draft, development_study=changed_root)
    registrations, registry, codecs = operation_catalog()
    with pytest.raises(ValueError, match="scientific|root|question|kinetic"):
        compile_recursive_wave(draft=changed, registrations=registrations, registry=registry,
            implementation_commit=author.implementation_binding(ROOT).observed_git_head, output_codecs=codecs)
    assert not tuple(Path(plane.root.contract.canonical_path).iterdir())


@dataclass(frozen=True, slots=True)
class UnregisteredSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/undeclared-instance-specification"
    specification_id: str

    @property
    def identity(self):
        return _identity(self, self.specification_id)


def test_substituted_protocol_specification_cannot_reuse_a_valid_original_draft(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "unentered-custody")
    original, _ = _pair(plane)
    foreign = UnregisteredSpecification("fixture.undeclared-experiment")
    preparation = replace(original, specification=foreign.identity, specification_record=foreign)
    monkeypatch.setattr(plane, "write", _forbidden)
    monkeypatch.setattr(plane, "write_stream", _forbidden)
    with pytest.raises(ValueError, match="installed domain protocol"):
        experiments.author_prepared_experiment(preparation=preparation, project_root=ROOT,
            artifact_writer=plane, output_dir=Path(plane.root.contract.canonical_path) / "refused")
    assert not tuple(Path(plane.root.contract.canonical_path).iterdir())
