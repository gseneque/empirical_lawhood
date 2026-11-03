"""Invocation-local issued BASE reuse; exposed software custody, no workers."""

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import study_issue as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalRootUnavailable
from empirical_lawhood.runtime.study_issue import IssuedStudyManifest, StudyIssuePayload, StudyIssuePreparation
from tests.runtime_platform.test_study_issue import _issue_api_fixture, _issue_request, _publisher


def _case(directory: Path, members: int = 4):
    directory.mkdir()
    api, paths, root, authority = _issue_api_fixture(directory)
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.succeeded
    original = issued.payload.manifest
    # Enlarge only this disclosed software publication's member census. The
    # original typed member bytes and every closed scientific record remain
    # unchanged. This supplies no scientific issue/qualification evidence.
    template = original.members[0]
    payload = (root / template.relative_path).read_bytes()
    issue_id = f"issue.software-scope-{members}"
    inventory = tuple(replace(template, member_id=f"{issue_id}.member-{index:03d}",
        relative_path=f"issued-programmes/{issue_id}/member-{index:03d}.json") for index in range(members))
    manifest = replace(original, issue_id=issue_id, members=inventory)
    preparation = StudyIssuePreparation(manifest, tuple(StudyIssuePayload(member, payload) for member in inventory))
    publisher = _publisher(root, authority)
    receipt = publisher.publish(preparation, at_utc="2026-07-24T20:32:00Z")
    return SimpleNamespace(root=root, publisher=publisher, preparation=preparation, manifest=manifest,
        receipt=receipt, authority=authority)


def _census(root):
    return {path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize("members", (8, 64))
def test_two_sizes_reduce_four_base_reads_and_member_joins_to_one(tmp_path, monkeypatch, members):
    case = _case(tmp_path / "case", members)
    counts = dict(loads=0, manifest_decodes=0, joined_members=0, bounded_reads=0, bounded_bytes=0)
    original_load = owner.ExternalIssuedStudyPublisher._load_study
    original_decode = owner.decode_canonical_bytes
    original_members = owner.ExternalIssuedStudyPublisher._validate_manifest_members
    original_read = owner.read_bounded_bytes

    def load(self, issue_id):
        counts["loads"] += 1
        return original_load(self, issue_id)

    def decode(payload, kind, **options):
        counts["manifest_decodes"] += kind is IssuedStudyManifest
        return original_decode(payload, kind, **options)

    def validate(self, manifest, **options):
        counts["joined_members"] += len(manifest.members)
        return original_members(self, manifest, **options)

    def read(*arguments, **options):
        payload = original_read(*arguments, **options)
        counts["bounded_reads"] += 1
        counts["bounded_bytes"] += len(payload)
        return payload

    monkeypatch.setattr(owner.ExternalIssuedStudyPublisher, "_load_study", load)
    monkeypatch.setattr(owner.ExternalIssuedStudyPublisher, "_validate_manifest_members", validate)
    monkeypatch.setattr(owner, "decode_canonical_bytes", decode)
    monkeypatch.setattr(owner, "read_bounded_bytes", read)
    before = _census(case.root)
    fresh = [case.publisher.load_study(case.manifest.issue_id) for _ in range(4)]
    baseline = dict(counts)
    counts.update({key: 0 for key in counts})
    with case.publisher.verification_scope() as scoped:
        reused = [scoped.load_study(case.manifest.issue_id) for _ in range(4)]
        assert all(value is reused[0] for value in reused)
    optimized = dict(counts)
    assert all(value == fresh[0] for value in (*fresh, *reused))
    assert all(value.manifest.canonical_bytes() == case.manifest.canonical_bytes() and
        value.publication_receipt.canonical_bytes() == case.receipt.canonical_bytes() for value in reused)
    assert baseline["loads"] == baseline["manifest_decodes"] == 4
    assert optimized["loads"] == optimized["manifest_decodes"] == 1
    assert baseline["joined_members"] == members * 4 and optimized["joined_members"] == members
    assert baseline["bounded_reads"] == optimized["bounded_reads"] * 4
    assert baseline["bounded_bytes"] == optimized["bounded_bytes"] * 4
    assert _census(case.root) == before
    (tmp_path / "measurement.json").write_text(json.dumps({"member_count": members,
        "fresh_four_calls": baseline, "one_explicit_scope": optimized,
        "count_scope": "study_issue bounded reads/bytes, typed BASE decodes and complete member joins",
        "canonical_and_primary_parity": True}, indent=2))


def _target(case, kind):
    if kind == "member":
        return case.root / case.manifest.members[0].relative_path
    if kind == "sidecar":
        return case.root / (case.manifest.members[0].relative_path + ".manifest.json")
    return case.root / case.receipt.publication.commit_marker_relative_path


@pytest.mark.parametrize("kind", ("member", "sidecar", "marker"))
def test_changed_complete_sibling_or_marker_refuses_inside_scope(tmp_path, kind):
    case = _case(tmp_path / "case")
    with pytest.raises((ArtifactIdentityConflict, ValueError)):
        with case.publisher.verification_scope() as scoped:
            scoped.load_study(case.manifest.issue_id)
            target = _target(case, kind)
            target.write_bytes(target.read_bytes() + b" ")
            scoped.load_study(case.manifest.issue_id)


@pytest.mark.parametrize("kind", ("member", "sidecar", "marker"))
def test_later_invocation_reauthenticates_instead_of_reusing_old_facts(tmp_path, kind):
    case = _case(tmp_path / "case")
    with case.publisher.verification_scope() as scoped:
        scoped.load_study(case.manifest.issue_id)
    target = _target(case, kind)
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises((ArtifactIdentityConflict, ValueError, RuntimeError)):
        with case.publisher.verification_scope() as scoped:
            scoped.load_study(case.manifest.issue_id)


def test_expired_handle_and_mutation_at_callback_exit_refuse(tmp_path):
    case = _case(tmp_path / "case")
    with case.publisher.verification_scope() as scoped:
        scoped.load_study(case.manifest.issue_id)
    with pytest.raises(ArtifactIdentityConflict, match="ended"):
        scoped.load_study(case.manifest.issue_id)
    with pytest.raises(ArtifactIdentityConflict):
        with case.publisher.verification_scope() as scoped:
            scoped.load_study(case.manifest.issue_id)
            _target(case, "member").unlink()


def test_current_authority_time_and_root_are_not_cached(tmp_path, monkeypatch):
    case = _case(tmp_path / "case")
    calls = []
    store = case.publisher.authority_store
    original_load = store.load
    def load(authority_id):
        calls.append(authority_id)
        return original_load(authority_id)
    monkeypatch.setattr(store, "load", load)
    with case.publisher.verification_scope() as scoped:
        scoped.load_study(case.manifest.issue_id)
        scoped.validate(case.preparation, at_utc="2026-07-24T20:32:00Z")
        with pytest.raises(PermissionError):
            scoped.validate(case.preparation, at_utc="2026-07-26T20:32:00Z")
        store.record = replace(case.authority, expires_at_utc="2026-07-26T20:31:00Z")
        with pytest.raises(PermissionError, match="substituted"):
            scoped.validate(case.preparation, at_utc="2026-07-24T20:32:00Z")
        store.record = case.authority
        def unavailable(**_options):
            raise ExternalRootUnavailable("disclosed changed root")
        with monkeypatch.context() as changed_root:
            changed_root.setattr(scoped.artifact_plane.root, "verify", unavailable)
            with pytest.raises(ExternalRootUnavailable):
                scoped.load_study(case.manifest.issue_id)
    assert len(calls) == 3


@pytest.mark.parametrize("has_scope", (False, True))
def test_alternate_planes_without_snapshot_hook_keep_fresh_reads(tmp_path, monkeypatch, has_scope):
    case = _case(tmp_path / "case")
    plane = case.publisher.artifact_plane
    class AlternatePlane:
        def __getattr__(self, name):
            if name in {"require_verification_snapshot", "verification_scope"}:
                raise AttributeError(name)
            return getattr(plane, name)
    class ScopedAlternate(AlternatePlane):
        @contextmanager
        def verification_scope(self):
            yield self
    alternate = owner.ExternalIssuedStudyPublisher(artifact_plane=(ScopedAlternate() if has_scope else AlternatePlane()),
        authority_store=case.publisher.authority_store, grantee_id=case.publisher.grantee_id)
    calls = []
    original = owner.ExternalIssuedStudyPublisher._load_study
    def observed(self, issue_id):
        calls.append(issue_id)
        return original(self, issue_id)
    monkeypatch.setattr(owner.ExternalIssuedStudyPublisher, "_load_study", observed)
    with alternate.verification_scope() as scoped:
        values = [scoped.load_study(case.manifest.issue_id) for _ in range(3)]
    assert len(calls) == 3 and values[0] == values[1] == values[2]


def test_custom_publisher_policy_hooks_are_not_replaced_by_a_concrete_view(tmp_path):
    case = _case(tmp_path / "case")
    calls = []
    class PolicyPublisher(owner.ExternalIssuedStudyPublisher):
        def load_study(self, issue_id):
            calls.append(issue_id)
            return super().load_study(issue_id)
    publisher = PolicyPublisher(artifact_plane=case.publisher.artifact_plane,
        authority_store=case.publisher.authority_store, grantee_id=case.publisher.grantee_id)
    with publisher.verification_scope() as scoped:
        assert scoped is publisher
        for _ in range(3):
            scoped.load_study(case.manifest.issue_id)
    assert calls == [case.manifest.issue_id] * 3
