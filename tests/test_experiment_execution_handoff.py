# SPDX-License-Identifier: MPL-2.0
"""CLI dispatch and attempt annotations, with disclosed nonexecuting services."""
import json

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.cli.app import app
from empirical_lawhood.cli import integrations


@pytest.mark.parametrize('command,method', (('experiment-run', 'run'), ('experiment-recover', 'recover')))
@pytest.mark.parametrize('selection', ('matrix', 'issued-preview', 'composite'))
def test_cli_confirmation_and_native_annotation_follow_actual_execution_route(tmp_path, monkeypatch, command, method, selection):
    calls = []
    expected = ({'schema': 'empirical-lawhood/api/result', 'status': 'BLOCKED',
        'reason_codes': ['WRITE_CONFIRMATION_REQUIRED'], 'payload': {'confirmed': False}}
        if selection == 'issued-preview' else {'status': 'SUCCEEDED'})
    def operate(self, **kwargs):
        calls.append(kwargs)
        return expected
    monkeypatch.setattr(ExperimentProgrammeService, method, operate)
    monkeypatch.setattr(integrations, '_storage', lambda: (tmp_path, None, object()))
    destination = tmp_path / 'attempt'
    arguments = ['campaign', command, '--authoring-dir', str(tmp_path), '--workers', '8',
        '--attempt-dir', str(destination)]
    if selection == 'matrix':
        arguments += ['--yes']
    elif selection == 'issued-preview':
        arguments += (['--plan', str(tmp_path / 'package.json')] if method == 'run'
            else ['--run', 'run.disclosed-preview'])
    else:
        request = tmp_path / 'request.json'
        request.write_text('{}')
        arguments += ['--programme-request', str(request), '--yes']
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 0, result.output
    invocation = json.loads((destination / 'invocation.json').read_bytes())
    assert invocation['operation_completed'] and invocation['state'] == 'SUCCEEDED'
    assert len(calls) == 1 and calls[0]['maximum_parallel_tasks'] == 8
    if selection == 'issued-preview':
        assert not calls[0]['request'].confirmed
        assert invocation['native_contact'] == 'none'
    else:
        assert calls[0]['confirmed'] is True
        assert invocation['native_contact'] == 'operation_reported_complete'


@pytest.mark.parametrize('report', (
    {'status': 'SUCCEEDED'},
    {'schema': 'empirical-lawhood/api/result', 'status': 'BLOCKED',
        'reason_codes': ['OTHER_REFUSAL'], 'payload': {'confirmed': False}},
    {'schema': 'empirical-lawhood/api/result', 'status': 'BLOCKED',
        'reason_codes': ['WRITE_CONFIRMATION_REQUIRED'], 'payload': None},
))
def test_generic_result_cannot_claim_no_native_contact(monkeypatch, report):
    from empirical_lawhood.cli import experiment_preparation as owner
    stages, reports = [], []
    monkeypatch.setattr(owner, 'attempt_stage', lambda *args, **kwargs: stages.append(kwargs))
    monkeypatch.setattr(owner, 'emit_development_report', reports.append)
    owner._emit_execution_report(report, issued_preview=True)
    assert not stages and reports == [report]
