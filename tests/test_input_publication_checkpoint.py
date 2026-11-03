# SPDX-License-Identifier: MPL-2.0
"""Input checkpoints retain complete siblings without rehashing unrelated history."""
from collections import Counter
import os
import sys

import pytest

from empirical_lawhood.infrastructure import artifacts, publication_metadata
from tests.test_matrix_programme_binding_batch import _case


def _checkpoint(plane, publications):
    publication_metadata.checkpoint_input_publications(plane, publications)


@pytest.mark.parametrize('count', (4, 32))
def test_input_checkpoint_hashes_complete_selected_publication_only(tmp_path, record_property, count):
    case = _case(tmp_path / 'artifacts', count=count, shape='shared')
    selected = case.result.publications[0]
    prior = case.plane.read_manifest(case.prior.materialization.relative_path)
    paths = Counter()
    code = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__

    def profile(frame, event, arg):
        if event == 'call' and frame.f_code is code:
            paths.update(frame.f_locals['snapshots'])

    with case.plane.read_context() as reading:
        manifest = reading.read_manifest(selected.materialization.relative_path)
        reading.verify_manifests((manifest, prior))
        old = sys.getprofile()
        sys.setprofile(profile)
        try:
            _checkpoint(reading, (selected,))
        finally:
            sys.setprofile(old)
        record_property('selected_members', count)
        record_property('checkpoint_paths', len(paths))
        assert len(paths) == 2 * count + 1  # Bodies, sidecars and one commit marker.
        assert all(path.name != 'input.json' for path in paths)
        assert case.plane.root.resolve(case.prior.materialization.relative_path,
            for_write=False) in reading._read_verification.snapshots


@pytest.mark.parametrize('damage', ('sibling-body', 'restored-mtime', 'missing-sibling',
    'sidecar', 'marker', 'ancestor', 'revoked'))
def test_input_checkpoint_refuses_before_consumer(tmp_path, damage):
    case = _case(tmp_path / 'artifacts', count=4, shape='shared')
    selected = case.result.publications[0]
    allowed, consumed = True, False

    def access(manifest):
        if not allowed:
            raise PermissionError('exposed input access revoked')

    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        with case.plane.read_context(before_member=access) as reading:
            manifest = reading.read_manifest(selected.materialization.relative_path)
            reading.verify_manifest(manifest)
            if damage == 'revoked':
                allowed = False
            elif damage == 'ancestor':
                directory = reading.root.resolve(selected.materialization.relative_path, for_write=False).parent
                moved = directory.with_name(directory.name + '-original')
                directory.rename(moved)
                directory.symlink_to(moved, target_is_directory=True)
            else:
                relative = (case.result.publications[-1].materialization.relative_path
                    if damage in ('sibling-body', 'restored-mtime', 'missing-sibling')
                    else selected.materialization.relative_path + '.manifest.json'
                    if damage == 'sidecar' else manifest.publication.commit_marker_relative_path)
                path = reading.root.resolve(relative, for_write=False)
                if damage == 'missing-sibling':
                    path.unlink()
                elif damage == 'restored-mtime':
                    raw, stat = path.read_bytes(), path.stat()
                    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                else:
                    path.write_bytes(b'{}\n')
            _checkpoint(reading, (selected,))
            consumed = True
    assert not consumed


def test_input_checkpoint_does_not_discard_outer_history_guard(tmp_path):
    case = _case(tmp_path / 'artifacts', count=4, shape='shared')
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        with case.plane.read_context() as reading:
            prior = reading.read_manifest(case.prior.materialization.relative_path)
            reading.verify_manifest(prior)
            _checkpoint(reading, (case.result.publications[0],))
            reading.root.resolve(case.prior.materialization.relative_path, for_write=False).write_bytes(b'{}\n')


@pytest.mark.parametrize('policy', ('custom-inspector', 'ordinary-scope'))
def test_custom_or_eager_scope_keeps_whole_history_checkpoint(tmp_path, policy):
    case = _case(tmp_path / 'artifacts', count=4, shape='shared')
    if policy == 'custom-inspector':
        class Inspector(artifacts.LocalFilesystemInspector):
            pass
        case.plane.root.inspector = Inspector()
    context = case.plane.verification_scope if policy == 'ordinary-scope' else case.plane.read_context
    consumed = False
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        with context() as reading:
            reading.verify_manifest(reading.read_manifest(case.prior.materialization.relative_path))
            reading.root.resolve(case.prior.materialization.relative_path, for_write=False).write_bytes(b'{}\n')
            _checkpoint(reading, (case.result.publications[0],))
            consumed = True
    assert not consumed


def test_input_checkpoint_expires_with_its_read(tmp_path):
    case = _case(tmp_path / 'artifacts', count=4, shape='shared')
    with case.plane.read_context() as reading:
        _checkpoint(reading, (case.result.publications[0],))
    with pytest.raises(artifacts.ArtifactIdentityConflict, match='ended'):
        _checkpoint(reading, (case.result.publications[0],))
