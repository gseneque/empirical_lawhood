# SPDX-License-Identifier: MPL-2.0
"""CLI progress ownership control; the scientific service is explicitly stubbed."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import weakref

import pytest


def test_repeated_read_keeps_separate_progress_lifetimes(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / 'scripts/examples/classical_matrix_series.py'
    specification = importlib.util.spec_from_file_location('classical_series_example_control', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    workspace = tmp_path / 'selected'
    scratch = workspace / 'scratch'
    scratch.mkdir(parents=True)
    first = scratch / 'progress.json'
    first.write_text('original invocation snapshot')
    service = SimpleNamespace(read=lambda **_: {'status':'SUCCEEDED',
        'scientific_result':{'scientific_completion':'COMPLETED','qualification':'NOT_ESTABLISHED'}})
    monkeypatch.setattr(module, 'create_investigation_service', lambda **_: service)
    options = ['--operation','read','--project-root',str(path.parents[2]),
        '--workspace',str(workspace),'--no-progress']
    assert module.main(options) == 0
    assert module.main(options) == 0
    assert first.read_text() == 'original invocation snapshot'
    reports = tuple(scratch.glob('progress.read.*.json'))
    assert len(reports) == 2
    assert all(json.loads(p.read_text())['status']=='RETURNED' for p in reports)


@pytest.mark.parametrize('operation', ('run', 'reanalyse'))
def test_authoring_releases_preparation_and_reuses_the_execution_readout(tmp_path, monkeypatch, operation):
    """The real runner must drop a completed preparation's scientific operands."""
    path = Path(__file__).parents[1] / 'scripts/examples/classical_matrix_series.py'
    specification = importlib.util.spec_from_file_location('classical_series_lifetime_control', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    root = tmp_path / 'selected'
    scratch = root / 'scratch'
    scratch.mkdir(parents=True)
    observed, references = [], []

    class Prepared:
        executable = True

    def prepare(*args, **kwargs):
        value = Prepared()
        references.append(weakref.ref(value))
        return value

    def author(*, preparation, output_dir):
        assert references[0]() is preparation
        observed.append('author')
        return {'status': 'AUTHORED'}

    def run(**kwargs):
        assert references[0]() is None
        observed.append('run')
        return {'status': 'SUCCEEDED', 'scientific_result': {'scientific_completion': 'COMPLETED'}}

    def read(**kwargs):
        raise AssertionError('execution already returned the complete authenticated result')

    service = SimpleNamespace(author=author, run=run, read=read)
    workspace = SimpleNamespace(profile_path=root / 'operator-storage.json',
        artifact_root=root / 'artifacts', scratch_root=scratch)
    monkeypatch.setattr(module, 'create_local_workspace', lambda *args, **kwargs: workspace)
    monkeypatch.setattr(module, 'create_investigation_service', lambda **kwargs: service)
    monkeypatch.setattr(module, 'prepare_investigation', prepare)
    monkeypatch.setattr(module, 'experiment_preparation_report', lambda value: {'executable': value.executable})
    inputs = lambda **kwargs: {'specification': str(scratch / 'specification.json'),
        'sources': str(scratch / 'sources.json')}
    monkeypatch.setattr(module, 'create_inputs', inputs)
    monkeypatch.setattr(module, 'create_reanalysis_inputs', inputs)
    options = ['--operation', operation, '--project-root', str(path.parents[2]),
        '--workspace', str(root), '--definition', str(tmp_path / 'definition.json'), '--no-progress']
    if operation == 'reanalyse':
        options += ['--parent-workspace', str(tmp_path / 'parent')]
    assert module.main(options) == 0
    assert observed == ['author', 'run']
    assert (scratch / 'result.json').read_bytes() == (scratch / 'execution.json').read_bytes()


def test_recovery_reuses_its_complete_authenticated_readout(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / 'scripts/examples/classical_matrix_series.py'
    specification = importlib.util.spec_from_file_location('classical_series_recovery_control', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    root = tmp_path / 'selected'
    scratch = root / 'scratch'
    scratch.mkdir(parents=True)
    calls = []

    def recover(**kwargs):
        calls.append('recover')
        return {'status': 'SUCCEEDED', 'scientific_result': {'scientific_completion': 'COMPLETED'}}

    def read(**kwargs):
        raise AssertionError('recovery already returned the complete authenticated result')

    service = SimpleNamespace(recover=recover, read=read)
    monkeypatch.setattr(module, 'create_investigation_service', lambda **kwargs: service)
    assert module.main(['--operation', 'recover', '--project-root', str(path.parents[2]),
        '--workspace', str(root), '--no-progress']) == 0
    assert calls == ['recover']
    assert (scratch / 'result.json').read_bytes() == (scratch / 'recovery.json').read_bytes()
