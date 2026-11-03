# SPDX-License-Identifier: MPL-2.0
"""Real publication controls for operation-local callbacks; no authority claims."""
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure import artifacts as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_artifact_member_preflight import APIS, _consume


@pytest.mark.parametrize("mode", ("verification_scope", "read_context"))
@pytest.mark.parametrize("api", (*APIS, "verify_materialization"))
def test_context_guard_precedes_selected_and_sibling_body_opens(tmp_path, monkeypatch, mode, api):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False): row for row in manifests}
    events = []
    original_open = owner.os.open

    def guard(manifest):
        path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
        assert paths[path] == manifest
        events.append(("guard", path))

    def observed_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            path = Path(path)
            assert events[-1] == ("guard", path), "body hash lacks its immediate current callback"
            events.append(("open", path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, "open", observed_open)
    with getattr(plane, mode)(before_member=guard) as reading:
        if api == "verify_materialization":
            reading.verify(manifests[0].materialization)
        else:
            _consume(reading, manifests, api, None)
    assert {path for event, path in events if event == "open"} == set(paths)


@pytest.mark.parametrize("mode", ("verification_scope", "read_context"))
def test_context_guard_revocation_precedes_final_body_rehash(tmp_path, monkeypatch, mode):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in manifests}
    current = True
    refused = []
    original_open = owner.os.open

    def guard(manifest):
        if not current:
            refused.append(manifest)
            raise PermissionError("original grant revoked before final rehash")

    def observed_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            assert current, "revoked protected body was opened during final snapshot"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, "open", observed_open)
    with pytest.raises(PermissionError, match="revoked before final rehash"):
        with getattr(plane, mode)(before_member=guard) as reading:
            reading.verify_manifest(manifests[0])
            current = False
    assert refused
    assert reading._read_verification.member_preflights == {}
    assert reading._read_verification.context_preflights == ()


def test_nested_callback_composes_and_remains_fresh_for_outer_final_hash(tmp_path):
    plane, manifests = _publication(tmp_path)
    inner_current = True
    calls = []

    def outer(manifest):
        calls.append(("outer", manifest))

    def inner(manifest):
        calls.append(("inner", manifest))
        if not inner_current:
            raise PermissionError("nested original grant revoked")

    with pytest.raises(PermissionError, match="nested original grant revoked"):
        with plane.read_context(before_member=outer) as reading:
            reading.verify_manifest(manifests[0])
            calls.clear()
            with reading.read_context(before_member=inner) as nested:
                assert nested is reading
                nested.verify_manifest(manifests[0])
            expected = {value.materialization.relative_path for value in manifests}
            assert {value.materialization.relative_path for label, value in calls if label == "outer"} == expected
            assert {value.materialization.relative_path for label, value in calls if label == "inner"} == expected
            inner_current = False


@pytest.mark.parametrize("mode", ("verification_scope", "read_context"))
@pytest.mark.parametrize("verdict", (False, True))
def test_context_callback_rejects_a_permission_verdict(tmp_path, mode, verdict):
    plane, manifests = _publication(tmp_path)
    with pytest.raises(ValueError, match="return None or raise"):
        with getattr(plane, mode)(before_member=lambda manifest: verdict) as reading:
            reading.verify_manifest(manifests[0])


def test_per_call_callback_cannot_replace_context_guard(tmp_path):
    plane, manifests = _publication(tmp_path)
    current = True

    def original_guard(manifest):
        if not current:
            raise PermissionError("owning original guard revoked")

    with pytest.raises(PermissionError, match="owning original guard revoked"):
        with plane.read_context(before_member=original_guard) as reading:
            reading.verify_manifest(manifests[0], before_member=lambda manifest: None)
            current = False
            reading.verify_manifest(manifests[0], before_member=lambda manifest: None)


def test_context_guard_preserves_final_exact_byte_mutation_refusal(tmp_path):
    plane, manifests = _publication(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match="changed"):
        with plane.read_context(before_member=lambda manifest: None) as reading:
            reading.verify_manifest(manifests[0])
            path = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
            raw = path.read_bytes()
            path.write_bytes(b"X" + raw[1:])


@pytest.mark.parametrize("mode", ("verification_scope", "read_context"))
def test_consumer_revocation_precedes_batch_local_after_consumer_rehash(tmp_path, monkeypatch, mode):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in manifests}
    current = True
    original_open = owner.os.open

    def guard(manifest):
        if not current:
            raise PermissionError("grant revoked inside member consumer")

    def consume(members):
        nonlocal current
        assert set(members) == {row.materialization.relative_path for row in manifests}
        current = False

    def observed_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            assert current, "batch-local snapshot hashed a body after consumer revocation"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, "open", observed_open)
    with pytest.raises(PermissionError, match="revoked inside member consumer"):
        with getattr(plane, mode)(before_member=guard) as reading:
            reading.verify_manifest_members(manifests[0], validate_members=consume)


@pytest.mark.parametrize("mode", ("verification_scope", "read_context"))
def test_noncallable_context_guard_refuses_before_body_open(tmp_path, monkeypatch, mode):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in manifests}
    original_open = owner.os.open

    def observed_open(path, *args, **kwargs):
        assert not isinstance(path, (str, Path)) or Path(path) not in paths
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, "open", observed_open)
    with pytest.raises(TypeError, match="requires a callable"):
        with getattr(plane, mode)(before_member=object()):
            pytest.fail("noncallable context guard was accepted")


def test_unhashable_context_callback_uses_identity_and_keeps_fresh_calls(tmp_path):
    plane, manifests = _publication(tmp_path)

    class Guard:
        __hash__ = None

        def __init__(self):
            self.calls = []

        def __call__(self, manifest):
            self.calls.append(manifest)

    guard = Guard()
    with plane.read_context(before_member=guard) as reading:
        reading.verify_manifest(manifests[0])
        first = len(guard.calls)
        reading.verify_manifest(manifests[0])
        assert len(guard.calls) > first
    assert {row.materialization.relative_path for row in guard.calls} == {
        row.materialization.relative_path for row in manifests}
