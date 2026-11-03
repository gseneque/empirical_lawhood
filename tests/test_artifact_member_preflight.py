# SPDX-License-Identifier: MPL-2.0
"""Current per-member permission checks around real, immutable custody reads."""

from contextlib import ExitStack
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure import artifacts as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from tests.runtime_platform.test_artifact_verification_scope import _publication


APIS = ('verify_manifest', 'verify_manifests', 'verify_manifest_members',
    'verify_manifests_members', 'open', 'open_many')


def _consume(plane, manifests, api, before_member):
    selected = manifests[0]
    values = tuple(VerifiedArtifactInput(row.logical, row.materialization) for row in manifests[:2])
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in values)
    budget = sum(row.materialization.size_bytes for row in values)
    if api == 'verify_manifest':
        plane.verify_manifest(selected, before_member=before_member)
    elif api == 'verify_manifests':
        plane.verify_manifests((selected,), before_member=before_member)
    elif api == 'verify_manifest_members':
        assert dict(plane.verify_manifest_members(selected, validate_members=lambda rows: rows,
            before_member=before_member)) == {row.materialization.relative_path: row for row in manifests}
    elif api == 'verify_manifests_members':
        assert dict(plane.verify_manifests_members((selected,), validate_members=lambda rows: rows,
            before_member=before_member)) == {row.materialization.relative_path: row for row in manifests}
    elif api == 'open':
        port = plane.open(values[0], binding=bindings[0], maximum_bytes=budget, before_member=before_member)
        try:
            assert port.binding == bindings[0]
        finally:
            port.close()
    elif api == 'open_many':
        ports = plane.open_many(values, bindings=bindings, maximum_bytes=budget, before_member=before_member)
        try:
            assert tuple(port.binding for port in ports) == bindings
        finally:
            for port in ports:
                port.close()
    else:
        raise AssertionError(api)


@pytest.mark.parametrize('api', APIS)
@pytest.mark.parametrize('mode', ('plain', 'verification_scope', 'read_context'))
def test_all_selected_and_unselected_siblings_are_preflighted_before_body_open(tmp_path, monkeypatch, api, mode):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False): row for row in manifests}
    permits, opened = set(), []
    original_open = owner.os.open

    def before_member(manifest):
        path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
        assert paths[path] == manifest
        permits.add(path)

    def observed_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            path = Path(path)
            assert path in permits, 'body opened before the actual member preflight'
            permits.remove(path)
            opened.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, 'open', observed_open)
    with ExitStack() as scope:
        reading = plane if mode == 'plain' else scope.enter_context(getattr(plane, mode)())
        _consume(reading, manifests, api, before_member)
    assert set(opened) == set(paths)


@pytest.mark.parametrize('api', APIS)
def test_unselected_sibling_refusal_precedes_its_body_open(tmp_path, monkeypatch, api):
    plane, manifests = _publication(tmp_path)
    denied = manifests[-1]
    denied_path = plane.root.resolve(denied.materialization.relative_path, for_write=False)
    original_open = owner.os.open
    attempted = []

    def before_member(manifest):
        if manifest == denied:
            attempted.append(manifest)
            raise PermissionError('current sibling access refused')

    def observed_open(path, *args, **kwargs):
        assert not isinstance(path, (str, Path)) or Path(path) != denied_path, 'refused sibling body was opened'
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, 'open', observed_open)
    with pytest.raises(PermissionError, match='current sibling access refused'):
        _consume(plane, manifests, api, before_member)
    assert attempted == [denied]


@pytest.mark.parametrize('api', APIS)
def test_noncallable_member_preflight_refuses_before_any_body(tmp_path, monkeypatch, api):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in manifests}
    original_open = owner.os.open

    def observed_open(path, *args, **kwargs):
        assert not isinstance(path, (str, Path)) or Path(path) not in paths
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, 'open', observed_open)
    with pytest.raises(TypeError, match='preflight requires a callable'):
        _consume(plane, manifests, api, object())


@pytest.mark.parametrize('mode', ('verification_scope', 'read_context'))
def test_current_member_access_is_rechecked_before_scope_exit_body_rehash(tmp_path, monkeypatch, mode):
    plane, manifests = _publication(tmp_path)
    paths = {plane.root.resolve(row.materialization.relative_path, for_write=False) for row in manifests}
    current = True
    refused = []
    original_open = owner.os.open

    def before_member(manifest):
        if not current:
            refused.append(manifest)
            raise PermissionError('access expired before final body rehash')

    def observed_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            assert current, 'expired protected body opened during the final snapshot'
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(owner.os, 'open', observed_open)
    with pytest.raises(PermissionError, match='expired before final body rehash'):
        with getattr(plane, mode)() as reading:
            reading.verify_manifest(manifests[0], before_member=before_member)
            current = False
    assert refused
    assert reading._read_verification.member_preflights == {}


def test_reused_closure_refreshes_access_and_never_drops_an_earlier_distinct_guard(tmp_path):
    plane, manifests = _publication(tmp_path)
    first_current, second_current = True, True
    calls = []

    def first(manifest):
        calls.append(('first', manifest))
        if not first_current:
            raise PermissionError('first current access revoked')

    def second(manifest):
        calls.append(('second', manifest))
        assert second_current

    with pytest.raises(PermissionError, match='first current access revoked'):
        with plane.read_context() as reading:
            reading.verify_manifests(manifests, before_member=first)
            calls.clear()
            reading.verify_manifests(manifests, before_member=second)
            assert {row.materialization.relative_path for label, row in calls if label == 'first'} == {
                row.materialization.relative_path for row in manifests}
            assert {row.materialization.relative_path for label, row in calls if label == 'second'} == {
                row.materialization.relative_path for row in manifests}
            first_current = False
            reading.verify_manifests(manifests, before_member=second)


@pytest.mark.parametrize('mode', ('verification_scope', 'read_context'))
def test_member_preflight_does_not_replace_final_exact_byte_mutation_guard(tmp_path, mode):
    plane, manifests = _publication(tmp_path)
    with pytest.raises(ArtifactIdentityConflict, match='changed'):
        with getattr(plane, mode)() as reading:
            reading.verify_manifest(manifests[0], before_member=lambda manifest: None)
            path = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
            raw = path.read_bytes()
            path.write_bytes(b'X' + raw[1:])
