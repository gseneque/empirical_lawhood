# SPDX-License-Identifier: MPL-2.0
"""Real immutable read closures; no API, workers, native science or authority."""

from collections import Counter
from contextlib import ExitStack, contextmanager
from dataclasses import replace
import json
import hashlib
import os
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, ExternalRootUnavailable, verify_read_context_snapshots
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication


@contextmanager
def _work():
    """Observe actual owners without replacing custody or policy methods."""
    counts = Counter()
    physical = ExternalArtifactPlane._verify_manifest_snapshot.__code__
    sidecar = ExternalArtifactPlane._read_current_manifest.__code__
    snapshot = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    pin = ExternalArtifactPlane._track_verification_snapshot.__code__
    digest = bounded_file_sha256.__code__
    def observe(frame, event, arg):
        if event == 'call':
            if frame.f_code is physical:
                counts['payloads'] += 1
            elif frame.f_code is sidecar:
                counts['sidecars'] += 1
            elif frame.f_code is snapshot:
                counts['snapshot_calls'] += 1
                counts['snapshot_paths'] += len(frame.f_locals['snapshots'])
            elif frame.f_code is digest and frame.f_back.f_code is snapshot:
                counts['snapshot_content_checks'] += 1
                counts['snapshot_content_bytes'] += frame.f_locals['maximum_bytes']
            elif frame.f_code is digest and frame.f_back.f_code is pin:
                counts['sidecar_pin_content_checks'] += 1
                counts['sidecar_pin_content_bytes'] += frame.f_locals['maximum_bytes']
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(previous)


@pytest.mark.parametrize('count,depth', ((8, 4), (64, 12)))
def test_deep_read_census_builds_shared_ancestors_once_and_checks_every_path(tmp_path, monkeypatch, count, depth):
    plane, _ = _publication(tmp_path, 1)
    root = Path(plane.root.contract.canonical_path)
    parent = root.joinpath(*(f'level-{index}' for index in range(depth)))
    parent.mkdir(parents=True)
    relatives = tuple(f'{parent.relative_to(root).as_posix()}/member-{index}' for index in range(count))
    expected = {relative: root / relative for relative in relatives}
    for path in expected.values():
        path.write_bytes(b'exposed path-census control\n')
    calls, directories, leaves = Counter(), Counter(), Counter()
    original_join, original_stat = Path.__truediv__, os.stat

    def join(self, other):
        if sys._getframe(1).f_code.co_name == 'read_paths':
            calls['path_joins'] += 1
        return original_join(self, other)

    def observe_stat(path, *args, **kwargs):
        caller = sys._getframe(1).f_code.co_name
        if caller == 'directory_identity':
            directories[Path(path)] += 1
        elif caller == 'read_paths':
            leaves[Path(path)] += 1
        return original_stat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, '__truediv__', join)
        patch.setattr(os, 'stat', observe_stat)
        with plane.root.read_paths(relatives) as observed:
            assert dict(observed) == expected
            assert all(path.read_bytes() == b'exposed path-census control\n' for path in observed.values())
    assert set(leaves) == set(expected.values()) and set(leaves.values()) == {2}
    assert len(directories) == depth and set(directories.values()) == {2}
    assert calls['path_joins'] <= 2 * count + depth


@pytest.mark.parametrize('damage', ('ancestor-link', 'leaf-link', 'parent-replaced', 'parent-created'))
def test_path_census_refuses_live_ancestor_or_destination_changes(tmp_path, damage):
    plane, _ = _publication(tmp_path, 1)
    root = Path(plane.root.contract.canonical_path)
    parent = root / 'selected'
    if damage != 'parent-created':
        parent.mkdir()
        (parent / 'member').write_bytes(b'exposed')
    with pytest.raises(ExternalRootUnavailable):
        with plane.root.read_paths(('selected/member',)):
            if damage == 'parent-created':
                parent.mkdir()
            elif damage == 'leaf-link':
                (parent / 'member').rename(parent / 'original')
                (parent / 'member').symlink_to('original')
            else:
                parent.rename(root / 'original')
                if damage == 'ancestor-link':
                    parent.symlink_to('original', target_is_directory=True)
                else:
                    parent.mkdir()
                    (parent / 'member').write_bytes(b'exposed')


def test_path_census_preserves_custom_resolver_calls(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path, 2)
    original = plane.root.resolve
    observed = []

    def resolve(relative, **kwargs):
        observed.append(relative)
        return original(relative, **kwargs)

    monkeypatch.setattr(plane.root, 'resolve', resolve)
    selected = tuple(manifest.materialization.relative_path for manifest in manifests)
    with plane.root.read_paths(selected) as paths:
        assert tuple(paths) == selected
    assert observed == [*selected, *selected]


@pytest.mark.parametrize('count', (8, 16))
def test_real_shared_closure_has_one_member_traversal_and_linear_path_work(tmp_path, count):
    if os.environ.get('EL_READ_CONTEXT_ISOLATED') == '1':
        assert not any(name.startswith('empirical_lawhood.api.') for name in sys.modules)
    plane, manifests = _publication(tmp_path, count)
    expected = {row.materialization.relative_path: row for row in manifests}
    mappings = []
    with _work() as work:
        with plane.read_context() as reading:
            for manifest in manifests:
                def consume(members):
                    mappings.append(members)
                    return members[manifest.materialization.relative_path]
                assert reading.verify_manifests_members(manifests, validate_members=consume) == manifest
                assert reading.read_manifest(manifest.materialization.relative_path) == manifest
                reading.verify_manifest(manifest)
            assert len({id(rows) for rows in mappings}) == 1
            assert dict(mappings[0]) == expected
            assert len({id(row.publication) for row in mappings[0].values()}) == 1
            assert sum(len(row[0]) for row in reading._read_verification.context_censuses[
                (reading.validators, reading.semantic_validations.fingerprint())].values()) <= 2 * count
    assert work['payloads'] == count
    assert work['sidecars'] == 2 * count
    assert work['snapshot_paths'] <= 5 * (2 * count + 1)
    assert work['snapshot_calls'] <= 8
    assert work['snapshot_content_checks'] == work['snapshot_paths']
    assert work['sidecar_pin_content_checks'] == count
    (tmp_path / 'read-context-work.json').write_text(json.dumps({
        'members': count, 'consumers': count, 'work': dict(work),
        'same_immutable_member_mapping': True,
        'counting': 'payloads counts complete physical/semantic validations; sidecars counts decodes; '
            'snapshot_content_checks counts additional full-file SHA passes; sidecar_pin_content_checks '
            'counts original sidecar SHA passes. Actual/final guards deliberately reread sealed bytes.',
        'claim': 'Real publication custody only; no scientific or authority claim',
    }, sort_keys=True) + '\n')
    with _work() as fresh:
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
    assert fresh['payloads'] == count


def test_nested_context_and_validation_views_share_one_original_closure(tmp_path):
    plane, manifests = _publication(tmp_path)
    with _work() as work:
        with plane.read_context() as reading:
            first = reading.verify_manifest_members(manifests[0], validate_members=lambda rows: rows)
            with reading.read_context() as nested:
                assert nested is reading
                assert nested.verify_manifest_members(manifests[1], validate_members=lambda rows: rows) is first
            changed = reading.with_semantic_validation_registry(ArtifactSemanticValidationRegistry('exposed.changed', ()))
            changed.verify_manifests(manifests)
    assert work['payloads'] == 2 * len(manifests)


def test_stock_read_exit_checks_the_complete_census_once(tmp_path):
    plane, manifests = _publication(tmp_path, 4)
    with ExitStack() as stack:
        reading = stack.enter_context(plane.read_context())
        reading.verify_manifests(manifests)
        expected_paths = len(reading._read_verification.snapshots)
        with _work() as work:
            stack.close()
    assert work['snapshot_calls'] == 1
    assert work['snapshot_content_checks'] == expected_paths
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        verify_read_context_snapshots(reading)


@pytest.mark.parametrize('count', (4, 16))
def test_new_read_closure_has_no_intermediate_rehash_and_one_complete_final_guard(tmp_path, count):
    plane, manifests = _publication(tmp_path, count)
    access = []
    with _work() as work:
        with plane.read_context(before_member=lambda row: access.append(row.logical.logical_artifact_id)) as reading:
            reading.verify_manifests_members(manifests, validate_members=lambda rows: len(rows))
            assert work['payloads'] == count
            assert work['snapshot_content_checks'] == 0
            expected = len(reading._read_verification.snapshots)
            assert expected == 2 * count + 1  # Bodies, sidecars and the exact commit marker.
            assert set(access) == {row.logical.logical_artifact_id for row in manifests}
            access.clear()
        assert set(access) == {row.logical.logical_artifact_id for row in manifests}
    assert work['snapshot_content_checks'] == expected
    # Ordinary public verification retains both eager complete guards.
    with _work() as eager:
        plane.verify_manifests_members(manifests, validate_members=lambda rows: len(rows))
    assert eager['snapshot_content_checks'] == 2 * expected


def test_internal_borrow_cannot_remove_worker_delivery_or_an_absent_final_guard(tmp_path):
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind

    plane, manifests = _publication(tmp_path, 1)
    with pytest.raises(ArtifactIdentityConflict, match='active read context'):
        plane._verify_manifests(manifests, {}, _borrow_read_context=True)
    with plane.read_context() as reading:
        value = VerifiedArtifactInput(manifests[0].logical, manifests[0].materialization)
        binding = WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL)
        with pytest.raises(ArtifactIdentityConflict, match='active read context'):
            reading._verify_manifests(manifests, {value.materialization.relative_path: (binding, binding.size_bytes)},
                _borrow_read_context=True)


@pytest.mark.parametrize('mode', ('reduced', 'strict'))
def test_composite_checkpoint_hashes_a_shared_census_once_and_refreshes_all_access(tmp_path, mode):
    from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode
    plane, manifests = _publication(tmp_path, 4)
    plane.artifact_verification = ArtifactVerificationMode(mode)
    access = []
    def first(manifest):
        access.append(('first', manifest.materialization.relative_path))
    def second(manifest):
        access.append(('second', manifest.materialization.relative_path))
    with plane.read_context(before_member=first) as reading:
        reading.verify_manifests(manifests)
        with reading.read_context(before_member=second) as nested:
            other = nested.with_semantic_validation_registry(ArtifactSemanticValidationRegistry('exposed.other', ()))
            access.clear()
            with _work() as work:
                verify_read_context_snapshots(reading, nested, other)
            assert work['snapshot_calls'] == 1
            assert work['snapshot_content_checks'] == (len(reading._read_verification.snapshots) if mode == 'strict' else 0)
            assert {label for label, _ in access} == {'first', 'second'}


def test_composite_checkpoint_keeps_separate_and_custom_guards(tmp_path):
    plane, manifests = _publication(tmp_path, 2)
    with plane.read_context() as first, plane.read_context() as second:
        first.verify_manifests(manifests)
        second.verify_manifests(manifests)
        with _work() as work:
            verify_read_context_snapshots(first, second)
        assert work['snapshot_calls'] == 2
    calls = []
    class Custom:
        def require_verification_snapshot(self):
            calls.append(1)
    custom = Custom()
    verify_read_context_snapshots(custom, custom)
    assert calls == [1, 1]


@pytest.mark.parametrize('damage', ('body', 'access'))
def test_composite_checkpoint_never_reuses_an_earlier_byte_or_access_result(tmp_path, damage):
    plane, manifests = _publication(tmp_path, 1)
    live = True
    def access(manifest):
        if not live:
            raise PermissionError('actual current access revoked')
    with pytest.raises((ArtifactIdentityConflict, PermissionError), match='changed|revoked'):
        with plane.read_context(before_member=access) as reading:
            reading.verify_manifests(manifests)
            verify_read_context_snapshots(reading, reading)
            if damage == 'body':
                path = plane.root.resolve(manifests[0].materialization.relative_path, for_write=False)
                raw = path.read_bytes()
                path.write_bytes(b'X' + raw[1:])
            else:
                live = False
            # Each invocation must perform a fresh complete checkpoint.
            verify_read_context_snapshots(reading, reading)


@pytest.mark.parametrize('operand', ('logical', 'physical', 'publication'))
def test_context_refuses_substituted_manifest_even_after_complete_original_verification(tmp_path, operand):
    plane, manifests = _publication(tmp_path)
    original = manifests[0]
    if operand == 'logical':
        foreign = replace(original, logical=replace(original.logical, content_sha256='f' * 64), publication=None)
    elif operand == 'physical':
        foreign = replace(original, materialization=replace(original.materialization,
            size_bytes=original.materialization.size_bytes + 1), publication=None)
    else:
        foreign = replace(original, publication=replace(original.publication, commit_marker_sha256='f' * 64))
    with plane.read_context() as reading:
        reading.verify_manifests(manifests)
        with pytest.raises(ArtifactIdentityConflict, match='authenticated read context'):
            reading.verify_manifest(foreign)


@pytest.mark.parametrize('damage', ('payload', 'sidecar', 'marker', 'missing', 'truncated', 'ancestor-link'))
@pytest.mark.parametrize('consumer_refuses', (False, True))
def test_full_final_guard_refuses_mutable_custody_on_success_or_refusal(tmp_path, damage, consumer_refuses):
    plane, manifests = _publication(tmp_path)
    root = Path(plane.root.contract.canonical_path)
    original = manifests[-1]
    with pytest.raises((ArtifactIdentityConflict, ExternalRootUnavailable)):
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
            def consume(rows):
                assert len(rows) == len(manifests)
                if damage == 'ancestor-link':
                    (root / 'outputs').rename(root / 'held-outputs')
                    (root / 'outputs').symlink_to('held-outputs', target_is_directory=True)
                else:
                    relative = (original.publication.commit_marker_relative_path if damage == 'marker'
                        else original.materialization.relative_path + ('.manifest.json' if damage == 'sidecar' else ''))
                    path = root / relative
                    if damage == 'missing':
                        path.unlink()
                    elif damage == 'truncated':
                        path.write_bytes(path.read_bytes()[:-1])
                    else:
                        raw = path.read_bytes()
                        path.write_bytes(b'X' + raw[1:])
                if consumer_refuses:
                    raise PermissionError('disclosed scientific consumer refusal')
                return 'mutable evidence must not escape the read context'
            reading.verify_manifests_members(manifests, validate_members=consume)


@pytest.mark.parametrize('damage', ('control', 'sidecar', 'marker'))
@pytest.mark.parametrize('guard', ('checkpoint', 'final'))
def test_immediate_same_size_rewrites_require_exact_bytes_at_actual_and_final_guards(tmp_path, damage, guard):
    """Exercise real filesystem timing, without sleeping or resetting metadata."""
    observations = []
    for attempt in range(12):
        selected = tmp_path / str(attempt)
        selected.mkdir()
        plane, manifests = _publication(selected, 1)
        original = manifests[0]
        relative = (original.publication.commit_marker_relative_path if damage == 'marker'
            else original.materialization.relative_path + ('.manifest.json' if damage == 'sidecar' else ''))
        path = plane.root.resolve(relative, for_write=False)
        raw = path.read_bytes()
        changed = (raw.replace(b'exposed.subject.0', b'exposed.subject.1') if damage == 'control'
            else b'X' + raw[1:])
        assert raw != changed and len(raw) == len(changed)
        with pytest.raises(ArtifactIdentityConflict, match='changed'):
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
                pinned = path.stat()
                path.write_bytes(changed)
                actual = path.stat()
                observations.append({
                    'stat_identity_equal': all(getattr(pinned, key) == getattr(actual, key)
                        for key in ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                    'same_size': actual.st_size == len(raw),
                    'bytes_changed': path.read_bytes() == changed,
                })
                if guard == 'checkpoint':
                    # Catching this refusal does not relax the final guard.
                    with pytest.raises(ArtifactIdentityConflict, match='changed'):
                        reading.require_verification_snapshot()
    (tmp_path / 'immediate-rewrite-observations.json').write_text(json.dumps({
        'damage': damage, 'guard': guard, 'attempts': observations,
        'refused': len(observations),
        'stat_collisions': sum(row['stat_identity_equal'] for row in observations),
        'clock_or_fsync_manipulation': False,
    }, sort_keys=True) + '\n')


@pytest.mark.parametrize('damage', ('control', 'sidecar', 'marker'))
def test_real_snapshot_guard_checks_bytes_even_between_immediate_same_size_writes(tmp_path, damage):
    plane, manifests = _publication(tmp_path, 1)
    original = manifests[0]
    plane.verify_manifest(original)
    relative = (original.publication.commit_marker_relative_path if damage == 'marker'
        else original.materialization.relative_path + ('.manifest.json' if damage == 'sidecar' else ''))
    path = plane.root.resolve(relative, for_write=False)
    raw = path.read_bytes()
    changed = b'X' + raw[1:]
    expected = hashlib.sha256(raw).hexdigest()
    observations = []
    for _ in range(12):
        path.write_bytes(raw)
        snapshots = {}
        plane._track_verification_snapshot(path, snapshots,
            expected_sha256=expected, maximum_bytes=len(raw))
        path.write_bytes(changed)
        actual = path.stat()
        observations.append({
            'stat_identity_equal': plane._descriptor_identity(actual) == snapshots[path][:5],
            'same_size': actual.st_size == len(raw), 'bytes_changed': path.read_bytes() == changed,
        })
        with pytest.raises(ArtifactIdentityConflict, match='exact bytes changed'):
            plane._require_verification_snapshot_paths(snapshots, reason='exact bytes changed')
    (tmp_path / 'immediate-guard-observations.json').write_text(json.dumps({
        'damage': damage, 'attempts': observations, 'refused': len(observations),
        'stat_collisions': sum(row['stat_identity_equal'] for row in observations),
        'clock_or_fsync_manipulation': False,
    }, sort_keys=True) + '\n')


def test_open_publication_root_accepts_an_unrelated_committed_batch_and_new_child(tmp_path):
    plane, manifests = _publication(tmp_path, 1)
    original = manifests[0]
    root = Path(plane.root.contract.canonical_path)
    with plane.read_context() as reading:
        reading.verify_manifests(manifests)
        # An external publication root is open. Its exact committed member
        # closure is sealed; unrelated new children are not extra members.
        (root / 'outputs' / 'unrelated-child').write_bytes(b'new independent data')
        request = ArtifactWriteRequest(
            'exposed.independent', 'independent/member.json', original.logical.payload_schema,
            original.logical.profile, 'application/json', 'exposed.independent-batch', 'independent',
            plane.root.resolve(original.materialization.relative_path, for_write=False).read_bytes(),
            original.logical.visibility_ceiling, (), original.logical.outcome_access,
        )
        publication = plane.write_batch((request,))
        replayed = plane.write_batch((request,))
        assert replayed[0].materialization == publication[0].materialization
        assert not replayed[0].created
        reading.require_verification_snapshot()
        reading.verify_manifests(manifests)
    plane.verify_manifest(plane.read_manifest(publication[0].materialization.relative_path))


def test_context_preserves_explicit_checkpoint_and_forbids_publication(tmp_path):
    plane, manifests = _publication(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match='changed'):
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
            with pytest.raises(ArtifactIdentityConflict, match='cannot publish'):
                reading.write_batch(())
            path = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
            path.write_bytes(path.read_bytes() + b' ')
            with pytest.raises(ArtifactIdentityConflict, match='changed'):
                reading.require_verification_snapshot()


def test_failed_consumer_does_not_warm_context_and_ended_context_refuses(tmp_path):
    plane, manifests = _publication(tmp_path)
    with _work() as work:
        with plane.read_context() as reading:
            def refuse(rows):
                assert len(rows) == len(manifests)
                raise PermissionError('disclosed consumer refusal')
            with pytest.raises(PermissionError, match='consumer refusal'):
                reading.verify_manifests_members(manifests, validate_members=refuse)
            reading.verify_manifests(manifests)
    assert work['payloads'] == 2 * len(manifests)
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        reading.verify_manifests_members(manifests, validate_members=lambda rows: rows)


@pytest.mark.parametrize('hook', ('read_manifest', '_read_current_manifest', '_consume_verified_manifests_members'))
def test_replaced_custody_policy_cannot_inherit_a_stock_read_proof(tmp_path, monkeypatch, hook):
    plane, manifests = _publication(tmp_path)
    with plane.read_context() as reading:
        reading.verify_manifests(manifests)
        error = PermissionError('actual current read policy refuses')
        def refuse(*args, **kwargs):
            raise error
        monkeypatch.setattr(ExternalArtifactPlane, hook, refuse)
        expected = ArtifactIdentityConflict if hook == '_read_current_manifest' else PermissionError
        with pytest.raises(expected) as raised:
            if hook == 'read_manifest':
                reading.read_manifest(manifests[0].materialization.relative_path)
            else:
                reading.verify_manifests_members(manifests, validate_members=lambda rows: rows)
        assert (raised.value.__cause__ if hook == '_read_current_manifest' else raised.value) is error
