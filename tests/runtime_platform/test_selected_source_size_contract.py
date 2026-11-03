# SPDX-License-Identifier: MPL-2.0
"""Actual large source custody, using disclosed nonqualifying metadata only.

The literal member census is synthetic; source capture/qualification is not
claimed. Canonical records, publication, custody authentication, exact reads and
decoding are real. No provider, issue, execution or scientific array is entered.
"""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import authoring_handoff as handoff
from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.infrastructure.source_closure import TrackedSourceMember
from empirical_lawhood.infrastructure.source_policy import CheckoutSourceAdmission
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.study_issue import SelectedSourceManifestMember
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
from empirical_lawhood.runtime.plans import CandidateExecutionPlan
from tests.prospective_source_capture_fixture import synthetic_capture
from tests.runtime_plan_capacity_fixture import expanded_plan_metadata
from tests.test_authoring_selected_source_migration import plane


@pytest.fixture(scope="module")
def large_companions(tmp_path_factory):
    capture = synthetic_capture("source.large-capacity-control", "a" * 64)
    members = tuple(SelectedSourceManifestMember(
        "src/" + "/".join(("long-component" * 12,) * 11) + f"/member-{index:05d}.py",
        "100644", 1, "1" * 64) for index in range(9_000))
    manifest = replace(capture.manifest, members=members)
    admission = CheckoutSourceAdmission(b"", None, tuple(row.relative_path for row in members))
    source = replace(capture.source,
        tracked_files=tuple(TrackedSourceMember(row.relative_path, row.mode, row.size_bytes, row.sha256)
            for row in members), source_admission=admission, final_source_admission=admission)
    capture = replace(capture, manifest=manifest, source=source,
        closure=replace(capture.closure, exact_source_manifest=manifest.identity))
    root = tmp_path_factory.mktemp("large-source-companions")
    directory = root / "source-packet"
    writer = plane(root)
    payloads = owner._source_provenance_members(capture, artifact_writer=writer)
    assert all(len(raw) > 16 * 1024**2 for _, _, raw in payloads)
    owner._publish_source_provenance(captured=capture, destination=directory, artifact_writer=writer)
    return capture, writer, directory, payloads


def test_source_members_above_old_ceiling_publish_and_reopen_exactly(large_companions):
    capture, writer, directory, payloads = large_companions
    seen = []
    with writer.verification_scope() as reader:
        def read(name, *, expected_schema):
            raw = handoff.read_authoring_source_companion(writer=reader, directory=directory,
                name=name, expected_schema=expected_schema)
            seen.append((name, raw))
            return raw
        owner._load_source_provenance(directory=directory, closure=capture.closure, read=read)
        reader.require_verification_snapshot()
    assert seen == [("provenance/" + name, raw) for name, _, raw in payloads]


@pytest.mark.parametrize("allowance", ("control_record_bytes", "in_memory_payload_bytes"))
def test_large_source_selected_budget_matches_producer_and_reader(large_companions, monkeypatch, allowance):
    capture, writer, directory, payloads = large_companions
    name, record, raw = payloads[0]
    selected = ArtifactCustodyLimits(**{allowance: len(raw) - 1})
    monkeypatch.setattr(writer, "custody_limits", selected)
    with pytest.raises(ValueError, match=name + ".*selected custody byte allowance"):
        owner._source_provenance_members(capture, artifact_writer=writer)
    actual_read = handoff.read_bounded_bytes
    reads = []
    def observe(path, **kwargs):
        reads.append(Path(path).name)
        return actual_read(path, **kwargs)
    monkeypatch.setattr(handoff, "read_bounded_bytes", observe)
    with pytest.raises(ValueError, match="selected custody byte allowance"):
        handoff.read_authoring_source_companion(writer=writer, directory=directory,
            name="provenance/" + name, expected_schema=record.SCHEMA)
    assert reads == [name + ".manifest.json"]


def test_source_reader_exact_selected_budget_accepts_large_member(large_companions, monkeypatch):
    _, writer, directory, payloads = large_companions
    name, record, raw = payloads[0]
    monkeypatch.setattr(writer, "custody_limits",
        ArtifactCustodyLimits(control_record_bytes=len(raw), in_memory_payload_bytes=len(raw)))
    with writer.verification_scope() as reader:
        assert handoff.read_authoring_source_companion(writer=reader, directory=directory,
            name="provenance/" + name, expected_schema=record.SCHEMA) == raw
        reader.require_verification_snapshot()


@pytest.mark.parametrize("damage", ("growth", "truncate", "same-size-replacement"))
def test_source_reader_refuses_post_authentication_byte_changes(tmp_path, monkeypatch, damage):
    capture = synthetic_capture("source.race-control", "a" * 64)
    writer = plane(tmp_path)
    directory = tmp_path / "source-packet"
    owner._publish_source_provenance(captured=capture, destination=directory, artifact_writer=writer)
    path = directory / "provenance/selected-source-manifest.json"
    original = path.read_bytes()
    verify = writer.verify_manifest
    def mutate(manifest, **kwargs):
        result = verify(manifest, **kwargs)
        payload = (original + b"x" if damage == "growth" else original[:-1]
            if damage == "truncate" else original.replace(b"source.race-control", b"source.fake-control"))
        path.write_bytes(payload)
        return result
    monkeypatch.setattr(writer, "verify_manifest", mutate)
    with pytest.raises((BoundedFileIOError, PermissionError), match="byte limit|publication bytes"):
        handoff.read_authoring_source_companion(writer=writer, directory=directory,
            name="provenance/selected-source-manifest.json", expected_schema=capture.manifest.SCHEMA)


def test_source_manifest_selected_budget_refuses_before_payload(tmp_path, monkeypatch):
    capture = synthetic_capture("source.manifest-budget", "a" * 64)
    writer = plane(tmp_path)
    directory = tmp_path / "source-packet"
    owner._publish_source_provenance(captured=capture, destination=directory, artifact_writer=writer)
    sidecar = directory / "provenance/selected-source-manifest.json.manifest.json"
    monkeypatch.setattr(writer, "custody_limits", ArtifactCustodyLimits(manifest_bytes=sidecar.stat().st_size - 1))
    with pytest.raises(BoundedFileIOError, match="byte limit"):
        handoff.read_authoring_source_companion(writer=writer, directory=directory,
            name="provenance/selected-source-manifest.json", expected_schema=capture.manifest.SCHEMA)


def test_plan_producer_has_no_implicit_64_mib_ceiling():
    size = 64 * 1024**2 + 1
    for name in ("preissue-run-plan.json", "preissue-execution-plan.json"):
        owner._require_prospective_public_member_capacity(name, size)
        exact = SimpleNamespace(custody_limits=ArtifactCustodyLimits(control_record_bytes=size))
        owner._require_prospective_public_member_capacity(name, size, artifact_writer=exact)
        smaller = SimpleNamespace(custody_limits=ArtifactCustodyLimits(control_record_bytes=size - 1))
        with pytest.raises(ValueError, match="selected custody runtime-plan byte allowance"):
            owner._require_prospective_public_member_capacity(name, size, artifact_writer=smaller)


def test_authoring_projection_above_old_ceiling_uses_selected_budget_and_exact_decode(tmp_path, monkeypatch):
    original = (Path(__file__).parents[1] / "fixtures/authoring-execution-plan.json").read_bytes()
    plan = expanded_plan_metadata(decode_canonical_bytes(original, CandidateExecutionPlan, maximum_bytes=len(original)))
    raw = plan.canonical_bytes()
    assert len(raw) > 64 * 1024**2
    (tmp_path / "preissue-execution-plan.json").write_bytes(raw)
    assert handoff.load_authoring_execution_projection(tmp_path) == plan
    selected = SimpleNamespace(custody_limits=ArtifactCustodyLimits(control_record_bytes=len(raw)))
    owner._require_prospective_public_member_capacity("preissue-execution-plan.json", len(raw), artifact_writer=selected)
    assert handoff.load_authoring_execution_projection(tmp_path, artifact_writer=selected) == plan
    selected.custody_limits = ArtifactCustodyLimits(control_record_bytes=len(raw) - 1)
    with pytest.raises(ValueError, match="selected custody runtime-plan byte allowance"):
        owner._require_prospective_public_member_capacity("preissue-execution-plan.json", len(raw), artifact_writer=selected)
    monkeypatch.setattr(handoff, "decode_canonical_bytes",
        lambda *_args, **_kwargs: pytest.fail("selected budget refusal reached decoder allocation"))
    with pytest.raises(BoundedFileIOError, match="byte limit"):
        handoff.load_authoring_execution_projection(tmp_path, artifact_writer=selected)
