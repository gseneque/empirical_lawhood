# SPDX-License-Identifier: MPL-2.0
"""Small PURE controls for an explicit Matrix controller RSS allowance."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api import matrix_programme_allocations as admission
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure import process_memory
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.runtime.metadata_memory import metadata_rss_operation


def test_explicit_rss_allowance_preserves_budget_and_resets_on_failure(monkeypatch):
    budget = ResourceBudget(1, 8, 0, 1, 0, 0)
    original = budget.canonical_bytes()
    monkeypatch.setattr(admission, '_process_rss_bytes', lambda: 12)
    monkeypatch.setattr(process_memory, 'release_unused_process_memory', lambda: None)
    with pytest.raises(ValueError, match='current-process memory ceiling'):
        admission._require_memory(budget.memory_bytes)
    with pytest.raises(RuntimeError, match='control exit'):
        with metadata_rss_operation(limit_bytes=16) as record:
            admission._require_memory(budget.memory_bytes)
            assert record['limits']['8'] == {'declared_limit_bytes': 8, 'effective_limit_bytes': 16}
            assert budget.canonical_bytes() == original
            raise RuntimeError('control exit')
    with pytest.raises(ValueError, match='current-process memory ceiling'):
        admission._require_memory(budget.memory_bytes)
    assert budget.canonical_bytes() == original


def test_selected_rss_ceiling_and_observation_refusals_remain(monkeypatch):
    monkeypatch.setattr(process_memory, 'release_unused_process_memory', lambda: None)
    with metadata_rss_operation(limit_bytes=16):
        monkeypatch.setattr(admission, '_process_rss_bytes', lambda: 17)
        with pytest.raises(ValueError, match='current-process memory ceiling'):
            admission._require_memory(8)
        def unavailable():
            raise ValueError('RSS observation unavailable')
        monkeypatch.setattr(admission, '_process_rss_bytes', unavailable)
        with pytest.raises(ValueError, match='RSS observation unavailable'):
            admission._require_memory(8)


def test_cli_retains_the_explicit_rss_limit_and_refuses_unrecorded_override(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    calls = []
    def compute(_):
        admission._require_memory(8)
        calls.append(True)
        return {'control': 'PURE', 'new_native_contacts': 0}
    monkeypatch.setattr(native_quickstart, 'check_native_model', compute)
    monkeypatch.setattr(admission, '_process_rss_bytes', lambda: 12)
    model = Path(__file__).resolve().parents[1] / 'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json'
    command = ['--metadata-rss-limit-bytes', '16', 'campaign', 'rc-ladder-native-check', '--config', str(model)]
    refusal = CliRunner().invoke(app, command)
    assert refusal.exit_code == 2 and calls == []
    assert 'retained invocation' in refusal.output
    result = CliRunner().invoke(app, [*command, '--output-dir', str(tmp_path / 'attempt')])
    assert result.exit_code == 0, result.output
    assert calls == [True]
    record = json.loads((tmp_path / 'attempt/invocation.json').read_bytes())['metadata_rss']
    assert record['selected_limit_bytes'] == 16 and record['check_count'] == 1
    assert record['limits']['8']['effective_limit_bytes'] == 16
    assert CliRunner().invoke(app, ['--metadata-rss-limit-bytes', '0', 'campaign', 'list']).exit_code == 2
