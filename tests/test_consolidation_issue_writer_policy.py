# SPDX-License-Identifier: MPL-2.0
"""Package 5 issue admission controls using disclosed software custody only."""

from hashlib import sha256
from types import MethodType

import pytest

from empirical_lawhood.infrastructure import study_issue as owner
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from tests.test_issued_base_verification_scope import _case


@pytest.fixture(scope="module")
def issued(tmp_path_factory):
    return _case(tmp_path_factory.mktemp("issue-writer-policy") / "custody")


def _census(root):
    return {path.relative_to(root).as_posix(): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize("hook", ("write_batch", "write_compact_batch"))
@pytest.mark.parametrize("customization", ("subclass", "instance"))
def test_custom_writer_admission_still_refuses_inside_publisher_scope(issued, customization, hook):
    calls = []

    def reject(self, requests, **_options):
        calls.append((self, tuple(row.relative_path for row in requests)))
        raise PermissionError("disclosed custom writer refuses issue publication")

    class PolicyPlane(ExternalArtifactPlane):
        pass

    original = issued.publisher.artifact_plane
    if customization == "subclass":
        setattr(PolicyPlane, hook, reject)
        plane = PolicyPlane(original.root, original.validators, original.semantic_validations,
            custody_limits=original.custody_limits)
    else:
        plane = ExternalArtifactPlane(original.root, original.validators, original.semantic_validations,
            custody_limits=original.custody_limits)
        setattr(plane, hook, MethodType(reject, plane))
    publisher = owner.ExternalIssuedStudyPublisher(artifact_plane=plane,
        authority_store=issued.publisher.authority_store, grantee_id=issued.publisher.grantee_id)
    before = _census(issued.root)
    with publisher.verification_scope() as scoped:
        with pytest.raises(PermissionError, match="custom writer refuses"):
            scoped.publish(issued.preparation, at_utc="2026-07-24T20:32:00Z")
        assert scoped is publisher and scoped.artifact_plane is plane
    assert len(calls) == 1 and calls[0][0] is plane
    assert set(calls[0][1]) == {*(member.relative_path for member in issued.manifest.members),
        f"issued-programmes/{issued.manifest.issue_id}/manifest.json"}
    assert _census(issued.root) == before


def test_builtin_scope_reuses_immutable_reads_and_rechecks_current_authority(issued, monkeypatch):
    loads, authority_reads = [], []
    load_study = owner.ExternalIssuedStudyPublisher._load_study
    store = issued.publisher.authority_store
    load_authority = store.load

    def observed_study(self, issue_id):
        loads.append(issue_id)
        return load_study(self, issue_id)

    def observed_authority(authority_id):
        authority_reads.append(authority_id)
        return load_authority(authority_id)

    monkeypatch.setattr(owner.ExternalIssuedStudyPublisher, "_load_study", observed_study)
    monkeypatch.setattr(store, "load", observed_authority)
    before = _census(issued.root)
    with issued.publisher.verification_scope() as scoped:
        first = scoped.load_study(issued.manifest.issue_id)
        assert scoped is not issued.publisher
        assert scoped.load_study(issued.manifest.issue_id) is first
        for _ in range(2):
            scoped.validate(issued.preparation, at_utc="2026-07-24T20:32:00Z")
        with pytest.raises(PermissionError):
            scoped.validate(issued.preparation, at_utc="2026-07-26T20:32:00Z")
        assert first.manifest.canonical_bytes() == issued.manifest.canonical_bytes()
        assert first.publication_receipt.canonical_bytes() == issued.receipt.canonical_bytes()
    assert loads == [issued.manifest.issue_id]
    assert len(authority_reads) == 3
    assert _census(issued.root) == before
