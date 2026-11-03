# SPDX-License-Identifier: MPL-2.0
"""Actual bounded metadata publication and input copying; no native calls."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.artifact_sidecars import decode_artifact_sidecar
from empirical_lawhood.infrastructure.recursive_input_publication import publish_recursive_metadata
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
from tests.test_artifact_publication_admission import _census, _plane, _requests


def _publish(plane, requests, **kwargs):
    return publish_recursive_metadata(plane, requests, require_current=lambda: None, **kwargs)


@pytest.mark.parametrize('count', (4, 130))
def test_bounded_publications_keep_exact_bytes_and_replay_without_rewriting(tmp_path, count):
    root = tmp_path / 'bounded'
    plane, requests = _plane(root), _requests(count)
    first = _publish(plane, requests)
    assert len(first) == count and all(row.created for row in first)
    markers = set()
    for request in requests:
        manifest = plane.read_manifest(request.relative_path)
        markers.add(manifest.publication.commit_marker_relative_path)
        assert len(manifest.publication.members) <= 64
        assert plane.root.resolve(request.relative_path, for_write=False).read_bytes() == request.payload
    assert len(markers) == (count + 63) // 64
    before = _census(root)
    assert _publish(plane, requests) == tuple(replace(row, created=False) for row in first)
    assert _census(root) == before


@pytest.mark.parametrize('bound', ('members', 'bytes'))
def test_selected_smaller_bounds_split_before_publication(tmp_path, bound):
    plane, requests = _plane(tmp_path / 'bounded'), _requests(5)
    limits = plane.custody_limits
    plane.custody_limits = (replace(limits, publication_members=2) if bound == 'members'
        else replace(limits, publication_aggregate_bytes=len(requests[0].payload) * 2))
    _publish(plane, requests)
    manifests = tuple(plane.read_manifest(row.relative_path) for row in requests)
    assert len({row.publication.commit_marker_relative_path for row in manifests}) == 3
    assert all(len(row.publication.members) <= 2 for row in manifests)


@pytest.mark.parametrize('legacy', ('singletons', 'group', 'mixed', 'changed-bound'))
def test_existing_members_keep_original_closed_publications(tmp_path, legacy):
    root = tmp_path / 'retained'
    plane, requests = _plane(root), _requests(5)
    selected = requests[:3] if legacy == 'mixed' else requests
    if legacy == 'singletons':
        for request in selected:
            plane.write(request)
    else:
        plane.write_compact_batch(selected)
    if legacy == 'changed-bound':
        plane.custody_limits = replace(plane.custody_limits, in_memory_payload_bytes=1)
        requests = tuple(row.as_stream() for row in requests)
    before = _census(root)
    _publish(plane, requests)
    after = _census(root)
    assert all(after[key] == value for key, value in before.items())
    for request in requests:
        plane.verify_manifest(plane.read_manifest(request.relative_path))


def test_matching_interrupted_group_resumes_its_original_intent(tmp_path, monkeypatch):
    root = tmp_path / 'interrupted'
    plane, requests = _plane(root), _requests(3)
    original = artifacts.ExternalArtifactPlane._write_publication_intent
    def interrupt(self, path, intent):
        original(self, path, intent)
        raise KeyboardInterrupt('after durable recursive metadata intent')
    with monkeypatch.context() as patch:
        patch.setattr(artifacts.ExternalArtifactPlane, '_write_publication_intent', interrupt)
        with pytest.raises(KeyboardInterrupt, match='durable recursive'):
            _publish(plane, requests)
    intent, = root.rglob('*.intent.json')
    before = intent.read_bytes()
    partial = plane.root.resolve(requests[0].relative_path, for_write=True)
    partial.write_bytes(requests[0].payload[:13])
    recovered = _publish(plane, requests)
    assert before and not intent.exists()
    assert all(row.created for row in recovered)
    assert partial.read_bytes() == requests[0].payload


def test_retained_group_refuses_changed_unselected_sibling(tmp_path):
    root = tmp_path / 'changed'
    plane, requests = _plane(root), _requests(3)
    plane.write_compact_batch(requests)
    sibling = plane.root.resolve(requests[-1].relative_path, for_write=False)
    sibling.write_bytes(requests[-1].payload.replace(b'aaaa', b'bbbb', 1))
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        _publish(plane, requests[:2])


@pytest.mark.parametrize('changed', ('scope', 'readonly', 'memory'))
def test_existing_group_keeps_current_publication_request_limits(tmp_path, changed):
    plane, requests = _plane(tmp_path / 'policy'), _requests(3)
    plane.write_compact_batch(requests)
    request = requests[0]
    if changed == 'scope':
        request = replace(request, publication_scope_id='software.other')
    elif changed == 'readonly':
        request = replace(request, read_only_source_input=True)
    else:
        plane.custody_limits = replace(plane.custody_limits, in_memory_payload_bytes=1)
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        _publish(plane, (request,))


def test_current_access_refuses_after_closed_publication(tmp_path):
    root = tmp_path / 'revoked'
    plane, requests = _plane(root), _requests(3)
    calls = []
    def current():
        calls.append(None)
        if tuple(root.rglob('*.commit.json')):
            raise PermissionError('current input grant revoked')
    with pytest.raises(PermissionError, match='grant revoked'):
        publish_recursive_metadata(plane, requests, require_current=current)
    assert len(calls) == 2
    assert tuple(root.rglob('*.commit.json'))


@pytest.mark.parametrize('hook', ('write', 'write_stream'))
def test_custom_writer_keeps_its_single_member_boundary(tmp_path, monkeypatch, hook):
    plane, requests = _plane(tmp_path / 'custom'), _requests(3)
    original = getattr(artifacts.ExternalArtifactPlane, hook)
    called = []
    def observed(self, request):
        called.append(request.relative_path)
        return original(self, request)
    monkeypatch.setattr(artifacts.ExternalArtifactPlane, hook, observed)
    selected = requests if hook == 'write' else tuple(row.as_stream() for row in requests)
    _publish(plane, selected)
    assert called == [row.relative_path for row in requests]
    assert all(len(plane.read_manifest(row.relative_path).publication.members) == 1 for row in requests)


def test_public_authoring_and_fresh_input_copy_use_readable_groups(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execution
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from tests.test_recursive_public_service import _draft, ROOT
    plane = _plane(tmp_path / 'public')
    plane.validators = integration_artifact_profile_validators()
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    def forbidden(*args, **kwargs):
        raise AssertionError('metadata publication must not enter task execution')
    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    result = author.author_recursive_wave(draft=_draft(), project_root=ROOT,
        artifact_writer=plane, output_dir=directory)
    assert result['status'] == 'AUTHORED' and result['native_contact'] == 'none'
    raw = next(directory.glob('config-*.json.manifest.json')).read_bytes()
    assert type(decode_artifact_sidecar(raw, maximum_bytes=len(raw))) is ArtifactManifestReference
    raw = (directory / 'authored-wave.json.manifest.json').read_bytes()
    assert type(decode_artifact_sidecar(raw, maximum_bytes=len(raw))) is artifacts.ArtifactManifest
    packet, draft, _, eager = author.load_authored_wave(directory=directory, artifact_writer=plane)
    lazy_packet, lazy_draft, _, payloads = author.load_authored_wave(directory=directory,
        artifact_writer=plane, lazy_payloads=True)
    assert (packet, draft) == (lazy_packet, lazy_draft)
    assert all(payloads[name] == value for name, value in eager.items())
    _, plan, _ = execution._retained_plans(payloads, draft)
    assert execution._read_only_custody_policy(plane) is not None
    inputs = execution._external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False)
    assert len(inputs) > 1
    assert any(len(plane.read_manifest(value.materialization.relative_path).publication.members) > 1
        for value in inputs)
    before = _census(Path(plane.root.contract.canonical_path))
    assert execution._external_inputs(plane=plane, plan=plan, draft=draft,
        payloads=payloads, read_only=False) == inputs
    assert _census(Path(plane.root.contract.canonical_path)) == before
    from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
    current = CurrentDevelopmentTaskCustody(writer=plane, directory=directory,
        plan=plan, payloads=payloads)
    assert current.plan == plan
    for value in inputs:
        manifest = plane.read_manifest(value.materialization.relative_path)
        assert current._manifest(value.materialization.relative_path, expected=manifest) == manifest
    assert _census(Path(plane.root.contract.canonical_path)) == before
    # A cold custom manifest reader must still see the compact sidecars.
    read, seen = plane.read_manifest, []
    def custom(relative, **kwargs):
        seen.append(relative)
        return read(relative, **kwargs)
    monkeypatch.setattr(plane, 'read_manifest', custom)
    _, actual, _, cold = author.load_authored_wave(directory=directory, artifact_writer=plane, lazy_payloads=True)
    assert actual == draft and seen and cold['draft.json'] == eager['draft.json']
