# SPDX-License-Identifier: MPL-2.0
"""Actual authored-member batching over exposed custody, never science or grants."""

from pathlib import Path

import pytest

from empirical_lawhood.infrastructure import artifacts as artifacts_owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _case(tmp_path, count=4, *, together=False):
    plane, first = _publication(tmp_path, count if together else 1)
    manifests = list(first)
    if not together:
        for number in range(1, count):
            raw = ObjectIdentity("exposed.subject." + str(number), ObjectIdentity.SCHEMA,
                "1.0.0", "a" * 64).canonical_bytes()
            result = plane.write(ArtifactWriteRequest("exposed.member." + str(number),
                "outputs/member-" + str(number) + ".json", ObjectIdentity.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.complete-batch", "outputs", raw,
                VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
            manifests.append(plane.read_manifest(result.materialization.relative_path))
    members = tuple(RecursiveWaveMember(Path(row.materialization.relative_path).name,
        ObjectIdentity("selected.member." + str(number), row.logical.payload_schema, "1.0.0", row.logical.content_sha256),
        row.materialization.size_bytes) for number, row in enumerate(manifests))
    return plane, tuple(manifests), members, Path(plane.root.contract.canonical_path) / "outputs"


@pytest.mark.parametrize("count", (4, 32))
@pytest.mark.parametrize("together", (False, True))
def test_actual_constructor_batches_global_snapshot_guards_with_exact_bytes_and_order(tmp_path, monkeypatch, count, together):
    plane, manifests, members, directory = _case(tmp_path, count, together=together)
    members = tuple(reversed(members))
    actual = artifacts_owner._ScopedArtifactPlane.require_verification_snapshot
    counts = {"serial": 0, "batch": 0}
    current = ["serial", True]

    def guard(self):
        if current[1]:
            counts[current[0]] += 1
        return actual(self)

    monkeypatch.setattr(artifacts_owner._ScopedArtifactPlane, "require_verification_snapshot", guard)
    expected = {row.filename: (directory / row.filename).read_bytes() for row in members}
    for mode in ("serial", "batch"):
        current[:] = [mode, True]
        with plane.verification_scope() as scoped:
            if mode == "serial":
                # An unchanged instance hook exercises the preserved custom
                # policy route and therefore the original per-member consumer.
                scoped.verify_manifest = scoped.verify_manifest
            payloads = AuthenticatedRecursivePayloads(plane=scoped, directory=directory, members=members)
            assert tuple(payloads) == tuple(row.filename for row in members)
            assert {payloads.manifest(row.filename) for row in members} == set(manifests)
            current[1] = False
            assert dict(payloads) == expected  # later gets still verify afresh
            current[1] = True
        current[1] = False
        with pytest.raises(ArtifactIdentityConflict, match="scope has ended"):
            payloads[members[0].filename]
    assert counts == {"serial": 2 * count + 1, "batch": 3}
    assert {name: (directory / name).read_bytes() for name in expected} == expected


@pytest.mark.parametrize("scoped", (False, True))
@pytest.mark.parametrize("consumer_raises", (False, True))
def test_changed_earlier_body_during_later_header_inspection_cannot_escape_constructor(tmp_path, monkeypatch, scoped, consumer_raises):
    from contextlib import nullcontext
    plane, _, members, directory = _case(tmp_path)
    inspect = AuthenticatedRecursivePayloads._inspect_member

    def changed(self, name, member, manifest):
        result = inspect(self, name, member, manifest)
        if name == members[-1].filename:
            path = directory / members[0].filename
            path.write_bytes(path.read_bytes() + b" ")
            if consumer_raises:
                raise RuntimeError("literal header consumer failure after mutation")
        return result

    monkeypatch.setattr(AuthenticatedRecursivePayloads, "_inspect_member", changed)
    with pytest.raises(ArtifactIdentityConflict, match="changed"):
        with (plane.verification_scope() if scoped else nullcontext(plane)) as writer:
            AuthenticatedRecursivePayloads(plane=writer, directory=directory, members=members)


@pytest.mark.parametrize("damage", ("payload", "sidecar", "marker", "partial-payload"))
def test_incomplete_publication_refuses_before_any_explicit_header_consumer(tmp_path, monkeypatch, damage):
    plane, manifests, members, directory = _case(tmp_path)
    selected = manifests[-1]
    relative = (selected.publication.commit_marker_relative_path if damage == "marker" else
        selected.materialization.relative_path + (".manifest.json" if damage == "sidecar" else ""))
    path = plane.root.resolve(relative, for_write=False)
    if damage == "partial-payload":
        path.write_bytes(path.read_bytes()[:16])
    else:
        path.unlink()
    monkeypatch.setattr(AuthenticatedRecursivePayloads, "_inspect_member", lambda *_args:
        pytest.fail("incomplete publication reached explicit member inspection"))
    with pytest.raises((ArtifactIdentityConflict, ValueError, OSError)):
        AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)


def test_previous_other_batch_mutation_refuses_before_new_constructor_callback(tmp_path, monkeypatch):
    plane, manifests, members, directory = _case(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match="changed"):
        with plane.verification_scope() as writer:
            writer.verify_manifest(manifests[0])
            path = directory / members[0].filename
            path.write_bytes(path.read_bytes() + b" ")
            monkeypatch.setattr(AuthenticatedRecursivePayloads, "_inspect_member", lambda *_args:
                pytest.fail("changed earlier outer batch reached new member callback"))
            AuthenticatedRecursivePayloads(plane=writer, directory=directory, members=members[1:])


@pytest.mark.parametrize("policy", ("subclass", "instance-verify", "instance-verify-many"))
def test_custom_admission_hooks_keep_original_per_member_route(tmp_path, monkeypatch, policy):
    plane, _, members, directory = _case(tmp_path)

    def refused(*_args, **_kwargs):
        raise PermissionError("literal custom verification policy")

    if policy == "subclass":
        class CustomPlane(ExternalArtifactPlane):
            def verify_manifest(self, manifest):
                refused()
        plane = CustomPlane(plane.root, plane.validators, plane.semantic_validations)
    elif policy == "instance-verify":
        monkeypatch.setattr(plane, "verify_manifest", refused)
    else:
        monkeypatch.setattr(plane, "verify_manifests", refused)
    monkeypatch.setattr(plane, "verify_manifests_members", lambda *_args, **_kwargs:
        pytest.fail("custom policy reached optimized batch route"))
    with pytest.raises(PermissionError, match="custom verification policy"):
        AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)


@pytest.mark.parametrize("fallback", ("request-limit", "instance-write"))
def test_low_request_limit_or_custom_writer_preserves_complete_serial_admission(tmp_path, monkeypatch, fallback):
    plane, manifests, members, directory = _case(tmp_path)
    if fallback == "request-limit":
        plane.custody_limits = ArtifactCustodyLimits(publication_members=1)
    else:
        monkeypatch.setattr(plane, "write", lambda *_args, **_kwargs: pytest.fail("read invoked custom write"))
    calls = []
    original = ExternalArtifactPlane.verify_manifest

    def verify(self, manifest):
        calls.append(manifest)
        return original(self, manifest)

    monkeypatch.setattr(ExternalArtifactPlane, "verify_manifest", verify)
    payloads = AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)
    assert calls == list(manifests)
    assert len(payloads) == len(members)


def test_duplicate_members_refuse_before_verification_and_empty_mapping_stays_empty(tmp_path, monkeypatch):
    plane, _, members, directory = _case(tmp_path)
    monkeypatch.setattr(plane, "verify_manifest", lambda *_args: pytest.fail("duplicate or empty selection verified"))
    with pytest.raises(ValueError, match="repeats a member"):
        AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members + (members[0],))
    assert len(AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=())) == 0


def test_exact_header_version_guard_is_preserved_inside_batch_callback(tmp_path):
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    import json
    plane, _, _, directory = _case(tmp_path, count=1)
    value = json.loads(ObjectIdentity("exposed.unknown-version", ObjectIdentity.SCHEMA, "1.0.0", "a" * 64).canonical_bytes())
    value["version"] = "9.0.0"
    raw = canonical_json_document_bytes(value)
    result = plane.write(ArtifactWriteRequest("exposed.unknown-version", "outputs/unknown-version.json", ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.other-batch", "outputs", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    manifest = plane.read_manifest(result.materialization.relative_path)
    plane.verify_manifest(manifest)  # generic canonical syntax does not prove selected revision
    member = RecursiveWaveMember("unknown-version.json", ObjectIdentity("selected.unknown-version", ObjectIdentity.SCHEMA,
        "1.0.0", manifest.logical.content_sha256), manifest.materialization.size_bytes)
    with pytest.raises((ArtifactIdentityConflict, ValueError)):
        AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=(member,))
