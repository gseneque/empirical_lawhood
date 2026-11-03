# SPDX-License-Identifier: MPL-2.0
"""Untrusted in-memory bindings retain the public prospective input checks."""

from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.input_payloads import InputBytes
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_recursive_input_record_revisions_public import _revisioned_prospective_fixture
from tests.runtime_platform.test_recursive_prospective_workflow import _authored_handoff_fixture, _registrations


def test_input_bytes_describe_immutable_payload_without_granting_validation():
    raw = b"not a canonical record"
    selected = InputBytes(raw)
    assert selected.payload is raw
    assert selected.size_bytes == len(raw) and selected.sha256 == sha256(raw).hexdigest()
    assert selected.bounded_bytes(maximum_bytes=len(raw)) is raw
    with pytest.raises(ValueError, match="byte bound"):
        selected.bounded_bytes(maximum_bytes=len(raw) - 1)
    with pytest.raises(TypeError, match="immutable bytes"):
        InputBytes(bytearray(raw))
    with pytest.raises(FrozenInstanceError):
        selected.payload = b"changed"


def test_public_in_memory_inputs_preserve_all_fourteen_original_handoff_bytes(tmp_path, monkeypatch):
    handoff, factories, discovery, plane, _raw, *_ = _authored_handoff_fixture(tmp_path, monkeypatch)
    spec = decode_canonical_bytes((handoff.directory / "recursive-prospective.json").read_bytes(),
        RecursiveProspectiveAuthoringSpec, maximum_bytes=None)
    automatic = {row.config_identity.object_fingerprint for row in spec.draft.operations
        if row.node_id in spec.draft.selected_operation_ids}
    selected = [(row.logical_artifact_id, row.content_sha256) for row in spec.external_operands
        if row.content_sha256 not in automatic]
    selected.extend((digest, digest) for digest in sorted({row.source_config_sha256
        for row in spec.draft.prospective_draft.source_materializations}))
    bindings = tuple((key, InputBytes(plane.root.resolve(
        f"candidate-inputs/sha256/{digest[:2]}/{digest}", for_write=False).read_bytes())) for key, digest in selected)

    def api_factory(*, repo_root, candidate_context_provider, candidate_capability_catalog):
        from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
        from empirical_lawhood.api.facade import EmpiricalLawhoodApi

        return EmpiricalLawhoodApi(repo_root=repo_root, external_root=None, candidate_context_provider=candidate_context_provider,
            candidate_capability_catalog=candidate_capability_catalog, extension_bundle_aggregate=discovery,
            executable_binding_aggregate=factories.aggregate, executable_factory_registry=factories,
            study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)

    destination = Path(plane.root.contract.canonical_path) / "byte-input-authoring"
    report = owner.author_recursive_prospective(spec=spec, project_root=tmp_path / "checkout",
        artifact_writer=plane, output_dir=destination, input_bindings=bindings,
        composition=(_registrations(handoff.compilation), handoff.compilation.registry, handoff.compilation.output_codecs),
        api_factory=api_factory, candidate_catalog=discovery.candidate_capability_catalog)
    assert report["scientific_authority"] == "NONE" and report["native_contact"] == "none"
    names = ("draft.json", "implementation.json", "recursive-prospective.json", "authoring.json",
        "scientific-projection.json", "decoder.json", "source-closure.json", "template.json", "registry.json",
        "resources.json", "candidate-report.json", "candidate.json", "preissue-run-plan.json", "preissue-execution-plan.json",
        "authored-wave.json")
    for name in names:
        assert (destination / name).read_bytes() == (handoff.directory / name).read_bytes(), name


@pytest.mark.parametrize("damage", ("digest", "size", "real-path-mutation"))
def test_public_changed_input_transport_refuses_before_any_bulk_publication(tmp_path, monkeypatch, damage):
    original_author = owner.author_recursive_prospective
    entered = []

    def author(**kwargs):
        from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher

        bindings = list(kwargs["input_bindings"])
        automatic = {row.config_identity.object_fingerprint for row in kwargs["spec"].draft.operations
            if row.node_id in kwargs["spec"].draft.selected_operation_ids}
        operand = next(row for row in kwargs["spec"].external_operands if row.content_sha256 not in automatic)
        index = next(index for index, (key, _path) in enumerate(bindings) if key == operand.logical_artifact_id)
        key, path = bindings[index]
        raw = path.read_bytes()
        if damage == "real-path-mutation":
            path.write_bytes(raw[:-1])
        else:
            altered = raw[:-1] if damage == "size" else bytes([raw[0] ^ 1]) + raw[1:]
            bindings[index] = (key, InputBytes(altered))
        kwargs["input_bindings"] = tuple(bindings)
        original_bulk = ExternalCandidateInputPublisher.publish_many
        def bulk(self, payloads, **options):
            entered.append(True)
            return original_bulk(self, payloads, **options)
        with monkeypatch.context() as patch:
            patch.setattr(ExternalCandidateInputPublisher, "publish_many", bulk)
            with pytest.raises(ValueError):
                original_author(**kwargs)
        assert not Path(kwargs["output_dir"]).exists()
        raise ValueError("observed exact input refusal before publication")

    monkeypatch.setattr(owner, "author_recursive_prospective", author)
    with pytest.raises(ValueError, match="observed exact input refusal"):
        _authored_handoff_fixture(tmp_path, monkeypatch)
    assert entered == []


def test_public_in_memory_exact_hash_wrong_schema_refuses_before_publication(tmp_path, monkeypatch):
    support, observations = _revisioned_prospective_fixture(monkeypatch, Config("wrong.schema", 3).canonical_bytes())
    revision_checked_author = owner.author_recursive_prospective
    def author(**kwargs):
        kwargs["input_bindings"] = tuple((key, InputBytes(path.read_bytes())) for key, path in kwargs["input_bindings"])
        return revision_checked_author(**kwargs)
    monkeypatch.setattr(owner, "author_recursive_prospective", author)
    with pytest.raises((ValueError, TypeError)):
        support._authored_handoff_fixture(tmp_path, monkeypatch)
    assert observations == {"entered": 1, "refused_before_publication": 1}
