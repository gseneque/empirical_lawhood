# SPDX-License-Identifier: MPL-2.0
"""Current whole-programme preparation keeps missing C/execution explicit."""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.methods.matrix_researcher_programme import selection as domain
from empirical_lawhood.api.experiment_preparation import load_experiment_specification, prepare_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile
from tests.test_matrix_researcher_programme import ROOT, _execution
from tests.test_recursive_public_service import _plane


def _case(directory):
    plane = _plane(directory / 'guarded')
    root = Path(plane.root.contract.canonical_path)
    copied = root / 'copied'
    copied.mkdir()
    raw = (ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json').read_bytes()
    specification_path = copied / 'programme.json'
    specification_path.write_bytes(raw)
    programme = load_experiment_specification(specification_path)
    profile = OperatorStorageProfile('storage.disclosed.prepare-context', 'external-filesystem', '1.0.0',
        str(root), plane.root.contract.required_mount_path, 'selected', 'scientific-scratch',
        OperatorStorageAccessMode.READ_WRITE, None, None, (), 'strict-mount-contained-no-symlink',
        1, (), 4, False)
    profile_path = copied / 'profile.json'
    profile_path.write_bytes(profile.canonical_bytes())
    return plane, programme, specification_path, profile, profile_path


def _forbid_effects(monkeypatch, plane):
    def forbidden(*args, **kwargs):
        pytest.fail('preparation opened authority or entered a publication/execution owner')
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', forbidden)
    for name in ('write', 'write_batch'):
        monkeypatch.setattr(plane, name, forbidden)
    for name in ('_project', '_retain_binding', '_author_phase', '_operate_phase', '_advance'):
        monkeypatch.setattr(MatrixResearchProgrammeService, name, forbidden)


def _bytes(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_incomplete_execution_keeps_guarded_c_context_without_opening_effects(tmp_path, monkeypatch):
    plane, programme, _, profile, _ = _case(tmp_path)
    execution = ExecutionSelection(4)
    base = prepare_experiment(programme, execution=execution)
    context, = (value for value in base.dependencies if value.code == domain.PREPARATION_CONTEXT)
    assert context.kind is DependencyKind.ENVIRONMENT and not base.executable and base.programme is None
    before = _bytes(Path(plane.root.contract.canonical_path))
    _forbid_effects(monkeypatch, plane)
    actual = ExperimentProgrammeService(ROOT, plane, profile).prepare(programme, execution=execution)
    assert actual == base and actual.census.native_effect_count == 0
    assert _bytes(Path(plane.root.contract.canonical_path)) == before


def test_complete_execution_cannot_adopt_unpublished_example_c(tmp_path, monkeypatch):
    plane, programme, _, profile, _ = _case(tmp_path)
    execution = _execution(plane)
    base = prepare_experiment(programme, execution=execution)
    assert base.programme is not None and not base.executable
    before = _bytes(Path(plane.root.contract.canonical_path))
    _forbid_effects(monkeypatch, plane)
    with pytest.raises((ValueError, OSError, RuntimeError)):
        ExperimentProgrammeService(ROOT, plane, profile).prepare(programme, execution=execution)
    assert _bytes(Path(plane.root.contract.canonical_path)) == before


@pytest.mark.parametrize('command', ('experiment-explain', 'experiment-prepare'))
def test_public_cli_reports_original_c_context_and_no_execution_without_full_settings(tmp_path, monkeypatch, command):
    from empirical_lawhood.cli import integrations
    from empirical_lawhood.cli.app import app
    plane, _, specification_path, profile, profile_path = _case(tmp_path)
    _forbid_effects(monkeypatch, plane)
    monkeypatch.setattr(integrations, '_storage', lambda: (ROOT, profile, plane))
    before = _bytes(Path(plane.root.contract.canonical_path))
    arguments = ['--project-root', str(ROOT), '--operator-profile', str(profile_path), 'campaign', command,
        '--input', str(specification_path), '--workers', '4']
    output = tmp_path / 'explicit-preparation-report.json'
    if command == 'experiment-prepare':
        arguments.extend(('--output', str(output)))
    returned = CliRunner().invoke(app, arguments)
    assert returned.exit_code == 0, returned.stdout + returned.stderr + repr(returned.exception)
    report = json.loads(returned.stdout)
    assert not report['executable'] and report['census']['native_effects'] == 0
    dependencies = {row['code']: row for row in report['dependencies']}
    assert dependencies[domain.PREPARATION_CONTEXT]['kind'] == 'ENVIRONMENT'
    assert report['scientific_authority'] == 'NONE' and not report['scientific_execution_performed']
    if command == 'experiment-prepare':
        assert json.loads(output.read_bytes())['dependencies'] == report['dependencies']
    assert _bytes(Path(plane.root.contract.canonical_path)) == before
