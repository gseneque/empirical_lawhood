# SPDX-License-Identifier: MPL-2.0
"""One typed sidecar read per complete stock batch keeps all custody guards."""

from dataclasses import replace
import sys

import pytest

from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_artifact_read_context import _work


def _selected_publication(tmp_path, physical_form, count=8):
    plane, manifests = _publication(tmp_path, count)
    if physical_form == 'expanded':
        # Explicit closed-record fixture: the current writer emits references only.
        from empirical_lawhood.storage.task_receipts import encode_artifact_manifest
        for manifest in manifests:
            plane.root.resolve(manifest.materialization.relative_path + '.manifest.json',
                for_write=False).write_bytes(encode_artifact_manifest(
                    manifest.logical, manifest.materialization, manifest.publication))
    return plane, manifests


@pytest.mark.parametrize('physical_form', ('expanded', 'compact'))
@pytest.mark.parametrize('shared', (False, True))
def test_each_complete_stock_batch_decodes_each_sidecar_once(tmp_path, physical_form, shared):
    plane, manifests = _selected_publication(tmp_path, physical_form)
    with _work() as work:
        if shared:
            with plane.read_context() as reading:
                for _ in range(3):
                    reading.verify_manifests(manifests)
            owners = 1
        else:
            for _ in range(3):
                plane.verify_manifests(manifests)
            owners = 3
    assert work['sidecars'] == owners * len(manifests)
    assert work['payloads'] == owners * len(manifests)
    assert work['sidecar_pin_content_checks'] == owners * len(manifests)
    assert work['snapshot_content_checks'] == owners * (2 * len(manifests) + 1)


@pytest.mark.parametrize('physical_form', ('expanded', 'compact'))
def test_complete_batch_reuse_compares_each_requested_manifest(tmp_path, physical_form):
    plane, manifests = _selected_publication(tmp_path, physical_form)
    forged = replace(manifests[1])
    object.__setattr__(forged, 'logical', replace(forged.logical,
        logical_artifact_id='exposed.unpublished'))
    with pytest.raises(ArtifactIdentityConflict, match='differs from its sidecar'):
        plane.verify_manifests((manifests[0], forged, *manifests[2:]))


@pytest.mark.parametrize('physical_form', ('expanded', 'compact'))
@pytest.mark.parametrize('boundary', ('initial-sidecar', 'complete-batch'))
def test_same_size_sidecar_change_after_initial_read_is_refused(tmp_path, physical_form, boundary):
    plane, manifests = _selected_publication(tmp_path, physical_form)
    target = plane.root.resolve(manifests[0].materialization.relative_path + '.manifest.json',
        for_write=False)
    raw = target.read_bytes()
    changed = b'X' + raw[1:]
    assert len(raw) == len(changed) and raw != changed
    function = (ExternalArtifactPlane._read_current_manifest if boundary == 'initial-sidecar'
        else ExternalArtifactPlane._verify_manifest_in_batch).__code__
    changes = []

    def observe(frame, event, _arg):
        if event == 'return' and frame.f_code is function and not changes:
            target.write_bytes(changed)
            changes.append(target)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(ArtifactIdentityConflict):
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
    finally:
        sys.setprofile(previous)
    assert changes == [target]


@pytest.mark.parametrize('hook', ('reader', 'resolver'))
def test_custom_readers_and_resolvers_keep_their_independent_sidecar_calls(tmp_path, monkeypatch, hook):
    plane, manifests = _selected_publication(tmp_path, 'compact')
    calls = []
    if hook == 'reader':
        original = plane._read_current_manifest

        def custom(path, **options):
            calls.append(path)
            return original(path, **options)

        monkeypatch.setattr(plane, '_read_current_manifest', custom)
    else:
        original = plane.root.resolve

        def custom(relative, **options):
            calls.append(relative)
            return original(relative, **options)

        monkeypatch.setattr(plane.root, 'resolve', custom)
    with _work() as work:
        plane.verify_manifests(manifests)
    assert calls
    assert work['sidecars'] == 2 * len(manifests)
    assert work['payloads'] == len(manifests)
