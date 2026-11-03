# SPDX-License-Identifier: MPL-2.0
"""Stopped preparation keeps its actual provenance and refuses execution."""
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.recursive_execution import _provenance
from empirical_lawhood.api.recursive_unentered import require_input_only_run
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from tests.numerical_provenance_fixtures import numerical_plane
from tests.test_rubisco_kinetic_declaration import _profile_provenance


def test_unentered_inputs_accept_ordinary_provenance_and_refuse_changed_source_or_contact(tmp_path):
    writer = numerical_plane(tmp_path / 'software-only')
    observed = _profile_provenance()
    run_id = 'unentered.software-control'
    _provenance(plane=writer, run_id=run_id, observed=observed)
    plan = SimpleNamespace(tasks=(), implementation_commit=observed.observed_git_head)
    require_input_only_run(writer, plan, run_id)
    with pytest.raises(PermissionError, match='producing source'):
        require_input_only_run(writer, SimpleNamespace(tasks=(), implementation_commit='c' * 40), run_id)
    writer.root.resolve('runs/' + run_id + '/native-contacts', for_write=True).mkdir()
    with pytest.raises(PermissionError, match='input-only'):
        require_input_only_run(writer, plan, run_id)


def test_unentered_inputs_refuse_changed_producing_provenance(tmp_path):
    writer = numerical_plane(tmp_path / 'software-only')
    observed = _profile_provenance()
    run_id = 'unentered.software-control'
    _provenance(plane=writer, run_id=run_id, observed=observed)
    path = writer.root.resolve('runs/' + run_id + '/inputs/producing-provenance.json', for_write=False)
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ArtifactIdentityConflict):
        require_input_only_run(writer, SimpleNamespace(tasks=(), implementation_commit=observed.observed_git_head), run_id)


def test_partial_input_snapshot_keeps_unpublished_bytes_and_complete_namespace(tmp_path):
    from empirical_lawhood.api.matrix_programme_unentered_e4 import _input_snapshot, _require_input_paths
    writer = numerical_plane(tmp_path / 'software-only')
    run_id = 'unentered.software-control'
    inputs = writer.root.resolve('runs/' + run_id + '/inputs', for_write=True)
    inputs.mkdir(parents=True)
    partial = inputs / 'input-pending.json'
    partial.write_bytes(b'original partial bytes')
    paths = {}
    original = _input_snapshot(writer, SimpleNamespace(tasks=()), run_id, retain_paths=paths)
    _require_input_paths(writer, run_id, paths)
    assert _input_snapshot(writer, SimpleNamespace(tasks=()), run_id) == original
    partial.write_bytes(b'changed partial bytes of another size')
    with pytest.raises(PermissionError, match='partial input custody'):
        _require_input_paths(writer, run_id, paths)
    assert _input_snapshot(writer, SimpleNamespace(tasks=()), run_id) != original
    (inputs.parent / 'native-contacts').mkdir()
    with pytest.raises(PermissionError, match='execution custody'):
        _require_input_paths(writer, run_id, paths)


def test_partial_input_snapshot_final_bytes_detect_change_hidden_from_path_observation(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_programme_unentered_e4 as custody
    writer = numerical_plane(tmp_path / 'software-only')
    run_id = 'unentered.software-control'
    inputs = writer.root.resolve('runs/' + run_id + '/inputs', for_write=True)
    inputs.mkdir(parents=True)
    partial = inputs / 'input-pending.json'
    partial.write_bytes(b'original')
    paths = {}
    original = custody._input_snapshot(writer, SimpleNamespace(tasks=()), run_id, retain_paths=paths)
    partial.write_bytes(b'changed!')
    monkeypatch.setattr(custody, '_path_identity', lambda path: paths[path])
    custody._require_input_paths(writer, run_id, paths)
    assert custody._input_snapshot(writer, SimpleNamespace(tasks=()), run_id) != original
