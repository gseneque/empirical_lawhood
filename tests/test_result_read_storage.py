# SPDX-License-Identifier: MPL-2.0
"""Real storage contracts with disclosed mount facts; no scientific authority."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.cli import integrations, platform
from empirical_lawhood.infrastructure import artifacts, selected_candidate, source_origin
from empirical_lawhood.runtime import operator_profile
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile


def _forbidden(*_args, **_kwargs):
    raise AssertionError('result storage attempted source admission or scientific data access')


def _case(tmp_path, monkeypatch, *, explicit_root=False):
    operator = tmp_path / 'operator'
    context = tmp_path / 'selected-context'
    home = tmp_path / 'home'
    temporary = tmp_path / 'local-temporary'
    mount = tmp_path / 'disclosed-mount'
    external = mount / 'retained'
    for path in (operator, context, home, temporary, external / 'artifacts', external / 'scratch'):
        path.mkdir(parents=True, exist_ok=True)
    profile = OperatorStorageProfile('profile.retained-read', 'external-filesystem', '1.0.0',
        str(external), str(mount), 'artifacts', 'scratch', OperatorStorageAccessMode.READ_ONLY,
        '/dev/disclosed-reader-volume', 'disclosed-reader-volume', ('disclosed-fs',),
        'strict-mount-contained-no-symlink', 1000, (), 1, False)
    path = operator / 'operator-profile.json'
    path.write_bytes(profile.canonical_bytes())
    actual_resolver = operator_profile.resolve_external_root_contract
    contract = actual_resolver(profile, repo_root=context, home_root=home,
        temporary_root=temporary, for_write=False)
    contract = replace(contract, storage_root_id='retained.original.namespace', logical_name='Current read access')
    calls = []

    def resolve(value, **kwargs):
        calls.append(('resolve', kwargs['for_write'], kwargs['repo_root']))
        # Only the local forbidden temporary directory differs in this portable
        # filesystem fixture. Production still selects its ordinary /tmp rule.
        return actual_resolver(value, temporary_root=temporary, **kwargs)

    def inspect(_inspector, selected):
        calls.append(('inspect', selected))
        return artifacts.FilesystemState(selected.canonical_path, True, False, 0, False,
            '/dev/disclosed-reader-volume', 'disclosed-reader-volume', 'disclosed-fs')

    monkeypatch.chdir(operator)
    monkeypatch.setattr(Path, 'home', lambda: home)
    monkeypatch.setattr(platform, 'CLI_PROJECT_ROOT', context if explicit_root else None)
    monkeypatch.setattr(platform, 'CLI_OPERATOR_PROFILE', path)
    monkeypatch.setattr(platform, '_selected_artifact_root_contract', lambda: contract)
    monkeypatch.setattr(operator_profile, 'resolve_external_root_contract', resolve)
    monkeypatch.setattr(artifacts.LocalFilesystemInspector, 'inspect', inspect)
    monkeypatch.setattr(source_origin, 'require_executing_target_source', _forbidden)
    monkeypatch.setattr(source_origin, 'require_selected_implementation', _forbidden)
    monkeypatch.setattr(selected_candidate, 'installed_candidate', _forbidden)
    return SimpleNamespace(profile=profile, contract=contract, calls=calls, operator=operator,
        context=context, artifact=external / 'artifacts', profile_path=path)


@pytest.mark.parametrize('explicit_root', (False, True))
def test_result_storage_accepts_actual_read_only_profile_without_source_admission(
        tmp_path, monkeypatch, explicit_root):
    case = _case(tmp_path, monkeypatch, explicit_root=explicit_root)
    original = case.profile_path.read_bytes()
    root, profile, plane = integrations._storage(read_only=True)
    expected_context = case.context if explicit_root else case.operator
    assert root == expected_context and profile == case.profile
    assert plane.root.contract == case.contract
    assert case.calls == [('resolve', False, expected_context), ('inspect', case.contract)]
    assert plane.root.verify(for_write=False) == case.artifact
    with pytest.raises(artifacts.ExternalRootUnavailable, match='free-space floor|not writable'):
        plane.root.verify(for_write=True)
    assert case.profile_path.read_bytes() == original
    assert not tuple(case.artifact.iterdir())


def test_authoring_storage_still_refuses_missing_project_root(tmp_path, monkeypatch):
    case = _case(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='--project-root and --operator-profile'):
        integrations._storage()
    assert case.calls == [] and not tuple(case.artifact.iterdir())


def test_authoring_storage_still_checks_actual_executing_source_before_storage(tmp_path, monkeypatch):
    case = _case(tmp_path, monkeypatch, explicit_root=True)
    source_calls = []

    def refuse(root):
        source_calls.append(root)
        raise RuntimeError('executing source differs from selected authoring source')

    monkeypatch.setattr(source_origin, 'require_selected_implementation', refuse)
    with pytest.raises(RuntimeError, match='executing source differs'):
        integrations._storage()
    assert source_calls == [case.context] and case.calls == []
    assert not tuple(case.artifact.iterdir())


def test_default_storage_dispatches_the_selected_implementation_owner(tmp_path, monkeypatch):
    case = _case(tmp_path, monkeypatch, explicit_root=True)
    profile = replace(case.profile, access_mode=OperatorStorageAccessMode.READ_WRITE)
    case.profile_path.write_bytes(profile.canonical_bytes())
    admitted = []
    monkeypatch.setattr(source_origin, 'require_selected_implementation', lambda root: admitted.append(root))
    root, loaded, plane = integrations._storage()
    assert admitted == [case.context]
    assert root == case.context and loaded == profile and plane.root.contract == case.contract
    assert case.calls == [('resolve', True, case.context), ('inspect', case.contract)]
    assert not tuple(case.artifact.iterdir())


@pytest.mark.parametrize('field,value', (
    ('minimum_free_bytes', 2000),
    ('expected_mount_source', '/dev/foreign-volume'),
    ('expected_volume_identity', 'foreign-volume'),
    ('allowed_filesystem_types', ('foreign-fs',)),
))
def test_result_storage_refuses_changed_selected_physical_contract_before_data(
        tmp_path, monkeypatch, field, value):
    case = _case(tmp_path, monkeypatch)
    changed = replace(case.contract, **{field: value})
    monkeypatch.setattr(platform, '_selected_artifact_root_contract', lambda: changed)
    with pytest.raises(ValueError, match='selected external root changes operator physical policy'):
        integrations._storage(read_only=True)
    assert case.calls == [('resolve', False, case.operator)]
    assert not tuple(case.artifact.iterdir())


def test_result_storage_still_requires_explicit_operator_profile(monkeypatch):
    monkeypatch.setattr(platform, 'CLI_PROJECT_ROOT', None)
    monkeypatch.setattr(platform, 'CLI_OPERATOR_PROFILE', None)
    with pytest.raises(ValueError, match='require --operator-profile'):
        integrations._storage(read_only=True)


@pytest.mark.parametrize('selected', (None, 0, 1, 'read-only'))
def test_storage_read_selection_refuses_nonboolean_modes(selected):
    with pytest.raises(TypeError, match='exact boolean'):
        integrations._storage(read_only=selected)
