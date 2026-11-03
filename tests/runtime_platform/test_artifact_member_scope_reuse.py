# SPDX-License-Identifier: MPL-2.0
"""Actual completed member callbacks reuse same-scope byte verification only."""

import pytest
from contextlib import nullcontext

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _physical_checks(monkeypatch):
    calls = []
    original = ExternalArtifactPlane._verify_manifest_snapshot

    def observed(self, manifest, **kwargs):
        calls.append(manifest.logical.logical_artifact_id)
        return original(self, manifest, **kwargs)

    monkeypatch.setattr(ExternalArtifactPlane, "_verify_manifest_snapshot", observed)
    return calls


@pytest.mark.parametrize("members", (4, 32))
def test_completed_member_callback_keeps_one_real_publication_check_in_same_scope(
        tmp_path, monkeypatch, members):
    plane, manifests = _publication(tmp_path, members)
    calls = _physical_checks(monkeypatch)
    expected = {row.materialization.relative_path: row for row in manifests}
    with plane.verification_scope() as scoped:
        actual = scoped.verify_manifests_members(manifests,
            validate_members=lambda values: dict(values))
        assert actual == expected and len(calls) == members
        # These are actual later public consumers, with fresh path guards.
        for manifest in reversed(manifests):
            scoped.verify_manifest(manifest)
        assert len(calls) == members
    plane.verify_manifests(manifests)
    assert len(calls) == 2 * members  # next operation verifies anew


def test_failed_member_callback_cannot_publish_a_same_scope_proof(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path)
    calls = _physical_checks(monkeypatch)
    def refuse(values):
        assert set(values) == {row.materialization.relative_path for row in manifests}
        raise RuntimeError("literal member consumer refusal")
    with plane.verification_scope() as scoped:
        with pytest.raises(RuntimeError, match="consumer refusal"):
            scoped.verify_manifests_members(manifests, validate_members=refuse)
        assert len(calls) == len(manifests)
        scoped.verify_manifests(manifests)
        assert len(calls) == 2 * len(manifests)


@pytest.mark.parametrize("changed", ("validators", "semantic"))
def test_member_callback_proof_remains_bound_to_its_original_validation_context(
        tmp_path, monkeypatch, changed):
    plane, manifests = _publication(tmp_path)
    calls = _physical_checks(monkeypatch)
    with plane.verification_scope() as scoped:
        def select_later_context(values):
            if changed == "validators":
                scoped.validators = ExternalArtifactPlane(plane.root).validators
            else:
                scoped.semantic_validations = ArtifactSemanticValidationRegistry(
                    "exposed.member-scope.changed-context", ())
            return tuple(sorted(values))
        actual = scoped.verify_manifests_members(manifests,
            validate_members=select_later_context)
        assert actual == tuple(sorted(row.materialization.relative_path for row in manifests))
        assert len(calls) == len(manifests)
        scoped.verify_manifests(manifests)
        assert len(calls) == 2 * len(manifests)


def test_invalid_member_consumer_refuses_before_any_actual_body_check(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path)
    calls = _physical_checks(monkeypatch)
    with plane.verification_scope() as scoped:
        with pytest.raises(TypeError, match="requires a callable"):
            scoped.verify_manifests_members(manifests, validate_members=None)
        assert not calls


@pytest.mark.parametrize("scoped", (False, True))
@pytest.mark.parametrize("error_type", (PermissionError, FileNotFoundError))
def test_member_consumer_oserror_keeps_exact_refusal_without_warming_proof(
        tmp_path, monkeypatch, scoped, error_type):
    plane, manifests = _publication(tmp_path)
    calls = _physical_checks(monkeypatch)
    error = error_type("actual consumer refuses its own premise")
    def refuse(values):
        assert len(values) == len(manifests)
        raise error
    with (plane.verification_scope() if scoped else nullcontext(plane)) as writer:
        with pytest.raises(error_type, match="own premise") as raised:
            writer.verify_manifests_members(manifests, validate_members=refuse)
        assert raised.value is error
        writer.verify_manifests(manifests)
        assert len(calls) == 2 * len(manifests)


@pytest.mark.parametrize("scoped", (False, True))
@pytest.mark.parametrize("damage", ("changed", "missing"))
def test_final_snapshot_refuses_changed_custody_even_when_consumer_refuses(
        tmp_path, scoped, damage):
    plane, manifests = _publication(tmp_path)
    path = plane.root.resolve(manifests[0].materialization.relative_path, for_write=False)
    original = path.read_bytes()
    def refuse(values):
        assert len(values) == len(manifests)
        if damage == "missing":
            path.unlink()
        else:
            path.write_bytes(b"x" + original[1:])
        raise PermissionError("actual consumer refuses its own premise")
    try:
        with pytest.raises(ArtifactIdentityConflict):
            with (plane.verification_scope() if scoped else nullcontext(plane)) as writer:
                writer.verify_manifests_members(manifests, validate_members=refuse)
    finally:
        path.write_bytes(original)
