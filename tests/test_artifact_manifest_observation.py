# SPDX-License-Identifier: MPL-2.0
"""Finite metadata observation supplies neither body acceptance nor access."""
from pathlib import Path
import os

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_artifact_read_context import _work


def test_metadata_observation_keeps_raw_selected_verification_and_unread_siblings(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path, 3)
    selected, *siblings = manifests
    prohibited = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in siblings}
    opened = []
    original_open = os.open
    def selected_only(path, *args, **kwargs):
        if not isinstance(path, int):
            actual = Path(path)
            assert actual not in prohibited, 'metadata observation opened an unrelated sibling body'
            opened.append(actual)
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', selected_only)
    seen = []
    with plane.read_context(observe_manifest=seen.append) as reading:
        retained = reading.read_manifest(selected.materialization.relative_path)
        assert retained == selected
        reading.verify(retained.materialization)
        assert reading._read_verification.context_preflights == ()
        assert reading._read_verification.member_preflights == {}
    assert seen and all(row == selected for row in seen)
    assert plane.root.resolve(selected.materialization.relative_path, for_write=False) in opened


def test_metadata_observer_inherits_new_scopes_and_semantics_and_stops_at_its_boundary(tmp_path):
    plane, manifests = _publication(tmp_path, 3)
    seen, nested_seen = [], []
    with plane.read_context(observe_manifest=seen.append) as reading:
        reading.read_manifest(manifests[0].materialization.relative_path)
        with reading.read_context(observe_manifest=nested_seen.append) as nested:
            # A cached metadata read is still observable in this nested lifetime.
            nested.read_manifest(manifests[0].materialization.relative_path)
            semantic = nested.with_semantic_validation_registry(ArtifactSemanticValidationRegistry('observed.other', ()))
            with semantic.verification_scope() as separate:
                separate.verify_manifest(manifests[1])
        count = len(nested_seen)
        reading.read_manifest(manifests[2].materialization.relative_path)
        assert len(nested_seen) == count
        assert reading._read_verification.manifest_observers == (seen.append,)
    assert {row.materialization.relative_path for row in seen} == {row.materialization.relative_path for row in manifests}
    assert nested_seen
    assert reading._read_verification.manifest_observers == ()
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        reading.read_manifest(manifests[0].materialization.relative_path)


def test_observer_does_not_add_verification_work(tmp_path):
    plane, manifests = _publication(tmp_path, 3)
    work = []
    seen = []
    for options in ({}, {'observe_manifest': seen.append}):
        with _work() as actual:
            with plane.read_context(**options) as reading:
                reading.verify_manifests(manifests)
                for manifest in manifests:
                    reading.read_manifest(manifest.materialization.relative_path)
        work.append(dict(actual))
    assert work[0] == work[1]
    assert seen


def test_observed_metadata_is_not_body_acceptance(tmp_path):
    plane, manifests = _publication(tmp_path, 2)
    selected = manifests[0]
    path = plane.root.resolve(selected.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    path.write_bytes(b'X' + raw[1:])
    seen = []
    with pytest.raises(ArtifactIdentityConflict):
        with plane.read_context(observe_manifest=seen.append) as reading:
            assert reading.read_manifest(selected.materialization.relative_path) == selected
            assert seen
            reading.verify_manifest(selected)


@pytest.mark.parametrize('mode', ('context', 'scope', 'nested'))
def test_manifest_observer_requires_callable_and_cannot_replace_metadata(tmp_path, mode):
    plane, manifests = _publication(tmp_path, 1)
    selected = manifests[0].materialization.relative_path
    if mode == 'nested':
        with plane.read_context() as reading:
            with pytest.raises(TypeError, match='observer requires a callable'):
                with reading.read_context(observe_manifest=1):
                    pytest.fail('invalid observer entered')
    else:
        context = plane.read_context if mode == 'context' else plane.verification_scope
        with pytest.raises(TypeError, match='observer requires a callable'):
            with context(observe_manifest=1):
                pytest.fail('invalid observer entered')
    with pytest.raises(TypeError, match='observer must return None'):
        with plane.read_context(observe_manifest=lambda manifest: manifest) as reading:
            reading.read_manifest(selected)
