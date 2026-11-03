# SPDX-License-Identifier: MPL-2.0
"""Same-invocation sibling records, without reusable custody or authority tokens."""

import json
import errno
import os

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _path(plane, relative):
    return plane.root.resolve(relative, for_write=False)


def _mutate(path):
    before = path.read_bytes()
    path.chmod(0o640)
    path.write_bytes(before + b'\n')


def _selected(manifest):
    # Existing callers may supply their exact logical/materialization pair;
    # the owning verifier loads the actual qualified publication itself.
    return ArtifactManifest(manifest.logical, manifest.materialization)


@pytest.mark.parametrize('count', (4, 16))
def test_callback_reuses_complete_typed_siblings_without_second_decode_pass(tmp_path, monkeypatch, count):
    plane, manifests = _publication(tmp_path, count)
    counters = {'sidecar_decodes': 0, 'payload_verifications': 0}
    decoded_rosters = {'count': 0}
    from empirical_lawhood.infrastructure import task_receipts
    original_binding = task_receipts._publication_binding
    original_read = ExternalArtifactPlane._read_current_manifest
    original_verify = ExternalArtifactPlane._verify_manifest_snapshot

    def read(self, path, **kwargs):
        counters['sidecar_decodes'] += 1
        return original_read(self, path, **kwargs)

    def binding(document):
        decoded_rosters['count'] += 1
        return original_binding(document)

    def verify(self, manifest, **kwargs):
        counters['payload_verifications'] += 1
        return original_verify(self, manifest, **kwargs)

    monkeypatch.setattr(ExternalArtifactPlane, '_read_current_manifest', read)
    monkeypatch.setattr(ExternalArtifactPlane, '_verify_manifest_snapshot', verify)
    monkeypatch.setattr(task_receipts, '_publication_binding', binding)
    selected = _selected(manifests[0])
    assert plane.verify_manifest(selected) is None
    legacy = {}
    for manifest in manifests:
        relative = manifest.materialization.relative_path
        legacy[relative] = plane._read_current_manifest(_path(plane, relative + '.manifest.json'))
    assert decoded_rosters['count'] == count + 1
    before = dict(counters)
    counters.update(sidecar_decodes=0, payload_verifications=0)
    decoded_rosters['count'] = 0
    retained = {}

    def consume(members):
        assert counters['payload_verifications'] == count
        assert dict(members) == legacy
        assert all(type(record) is ArtifactManifest and record.publication == manifests[0].publication
                   for record in members.values())
        shared = next(iter(members.values())).publication
        assert all(record.publication is shared and record.publication.members is shared.members
                   for record in members.values())
        retained.update(
            manifest_metadata_records=len(members),
            publication_binding_objects=len({id(record.publication) for record in members.values()}),
            publication_roster_tuples=len({id(record.publication.members) for record in members.values()}),
            publication_member_objects=len({id(member) for record in members.values() for member in record.publication.members}),
            manifest_canonical_byte_caches_at_entry=sum(hasattr(record, '_canonical_encoding') for record in members.values()),
        )
        assert retained == {'manifest_metadata_records': count, 'publication_binding_objects': 1,
            'publication_roster_tuples': 1, 'publication_member_objects': count,
            'manifest_canonical_byte_caches_at_entry': 0}
        # Small-fixture parity is checked after the retention observation;
        # consumer-created canonical caches are outside the collector's claim.
        for name, record in members.items():
            assert record.canonical_bytes() == legacy[name].canonical_bytes()
            assert record.fingerprint() == legacy[name].fingerprint()
        with pytest.raises(TypeError):
            members['uncommitted/foreign.json'] = manifests[0]
        return tuple(sorted((name, record.logical.content_sha256) for name, record in members.items()))

    result = plane.verify_manifest_members(selected, validate_members=consume)
    assert result == tuple(sorted((name, record.logical.content_sha256) for name, record in legacy.items()))
    assert before == {'sidecar_decodes': 2 * count + 1, 'payload_verifications': count}
    assert counters == {'sidecar_decodes': count + 1, 'payload_verifications': count}
    assert decoded_rosters['count'] == 1
    (tmp_path / 'same-invocation-verification-work.json').write_text(json.dumps({
        'scope': 'Small exposed complete publication; decoder/payload work counts, not a timing benchmark',
        'siblings': count, 'ordinary_verify_then_consumer_sidecar_reads': before,
        'same_invocation_callback': counters, 'exact_typed_records_equal': True,
        'collector_retention_at_callback_entry': retained,
        'retention_scope': 'N lightweight manifest records plus one shared N-member publication; no manifest canonical caches at callback entry. Structural object counts only, not RSS/global consumer-memory bounds.',
    }, sort_keys=True, indent=2) + '\n')


@pytest.mark.parametrize('failure', ('missing-sidecar', 'missing-payload', 'corrupt-payload', 'missing-marker', 'corrupt-marker'))
def test_missing_or_corrupt_member_and_commit_refuse_before_callback_like_existing_api(tmp_path, failure):
    plane, manifests = _publication(tmp_path)
    sibling = _path(plane, manifests[1].materialization.relative_path)
    marker = _path(plane, manifests[0].publication.commit_marker_relative_path)
    if failure == 'missing-sidecar':
        sibling.with_name(sibling.name + '.manifest.json').unlink()
    elif failure == 'missing-payload':
        sibling.unlink()
    elif failure == 'corrupt-payload':
        _mutate(sibling)
    elif failure == 'missing-marker':
        marker.unlink()
    else:
        _mutate(marker)
    calls = []
    with pytest.raises(ArtifactIdentityConflict):
        plane.verify_manifest(_selected(manifests[0]))
    with pytest.raises(ArtifactIdentityConflict):
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=lambda rows: calls.append(rows))
    assert calls == []


def test_changed_earlier_sibling_is_refused_before_callback_entry(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path)
    original = ExternalArtifactPlane._verify_manifest_snapshot
    calls = []

    def verify(self, manifest, **kwargs):
        result = original(self, manifest, **kwargs)
        if manifest.logical == manifests[-1].logical:
            _mutate(_path(plane, manifests[0].materialization.relative_path))
        return result

    monkeypatch.setattr(ExternalArtifactPlane, '_verify_manifest_snapshot', verify)
    with pytest.raises(ArtifactIdentityConflict, match='changed during verification'):
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=lambda rows: calls.append(rows))
    assert calls == []


@pytest.mark.parametrize('changed', ('payload', 'sidecar', 'marker'))
@pytest.mark.parametrize('callback_raises', (False, True))
def test_callback_mutation_is_checked_before_return_even_when_consumer_raises(tmp_path, changed, callback_raises):
    plane, manifests = _publication(tmp_path)
    sibling = _path(plane, manifests[1].materialization.relative_path)
    path = {'payload': sibling, 'sidecar': sibling.with_name(sibling.name + '.manifest.json'),
            'marker': _path(plane, manifests[0].publication.commit_marker_relative_path)}[changed]
    calls = []

    def consume(members):
        calls.append(tuple(members))
        _mutate(path)
        if callback_raises:
            raise RuntimeError('literal consumer failure after mutation')
        return 'invalid result must not escape'

    with pytest.raises(ArtifactIdentityConflict, match='changed during verification'):
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=consume)
    assert len(calls) == 1


def test_unchanged_consumer_failure_propagates_without_inventing_success(tmp_path):
    plane, manifests = _publication(tmp_path)
    error = RuntimeError('literal scientific contract refuses')

    def consume(_members):
        raise error

    with pytest.raises(RuntimeError) as caught:
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=consume)
    assert caught.value is error
    assert plane.verify_manifest(_selected(manifests[0])) is None


@pytest.mark.parametrize('changed', ('payload', 'sidecar', 'marker'))
def test_scope_tracks_new_snapshots_after_callback_returns_until_outer_exit(tmp_path, changed):
    plane, manifests = _publication(tmp_path)
    sibling = _path(plane, manifests[1].materialization.relative_path)
    path = {'payload': sibling, 'sidecar': sibling.with_name(sibling.name + '.manifest.json'),
            'marker': _path(plane, manifests[0].publication.commit_marker_relative_path)}[changed]
    with pytest.raises(ArtifactIdentityConflict, match='changed during its verification scope'):
        with plane.verification_scope() as view:
            result = view.verify_manifest_members(_selected(manifests[0]), validate_members=lambda rows: len(rows))
            assert result == 4
            _mutate(path)


def test_expired_scope_refuses_callback_and_fresh_calls_do_not_trust_held_records(tmp_path):
    plane, manifests = _publication(tmp_path)
    held = []
    with plane.verification_scope() as view:
        assert view.verify_manifest_members(_selected(manifests[0]),
            validate_members=lambda rows: held.append(rows)) is None
    assert len(held) == 1 and len(held[0]) == 4
    calls = []
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        view.verify_manifest_members(_selected(manifests[0]), validate_members=lambda rows: calls.append(rows))
    assert calls == []
    _mutate(_path(plane, manifests[1].materialization.relative_path))
    with pytest.raises(ArtifactIdentityConflict):
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=lambda rows: calls.append(rows))
    assert calls == []


def test_callback_is_not_a_caller_supplied_trust_flag(tmp_path):
    plane, manifests = _publication(tmp_path)
    with pytest.raises(TypeError, match='callable'):
        plane.verify_manifest_members(_selected(manifests[0]), validate_members=True)


def test_worker_delivery_closes_all_sealed_ports_when_final_snapshot_refuses(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path)
    values = tuple(VerifiedArtifactInput(record.logical, record.materialization) for record in manifests)
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL) for value in values)
    original = ExternalArtifactPlane._verify_manifest_snapshot
    opened = []

    def verify(self, manifest, **kwargs):
        port = original(self, manifest, **kwargs)
        if port is not None:
            opened.append((port, port._reader._descriptor))
            if len(opened) == len(values):
                _mutate(_path(plane, manifests[0].materialization.relative_path))
        return port

    monkeypatch.setattr(ExternalArtifactPlane, '_verify_manifest_snapshot', verify)
    with pytest.raises(ArtifactIdentityConflict, match='changed during verification'):
        plane.open_many(values, bindings=bindings, maximum_bytes=sum(value.materialization.size_bytes for value in values))
    assert len(opened) == len(values)
    for port, descriptor in opened:
        with pytest.raises(OSError) as caught:
            os.fstat(descriptor)
        assert caught.value.errno == errno.EBADF
        with pytest.raises(ValueError, match='closed'):
            port.read(0)
