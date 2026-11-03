# SPDX-License-Identifier: MPL-2.0
"""Operational aggregate costs must not be invented as individual attempt costs."""
from decimal import Decimal
import importlib.util
from pathlib import Path

import pytest


def programme(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_broad_programme.py'
    spec = importlib.util.spec_from_file_location('exposed_programme_costs', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = object.__new__(module.SelectedProgramme)
    value.root = tmp_path
    value.plane = object()
    value.measured = lambda name, call: call()
    return value


@pytest.mark.parametrize('attempt_count', (0, 2, 3))
def test_multi_attempt_aggregate_remains_unknown_without_publishing_cost(tmp_path, monkeypatch, attempt_count):
    import empirical_lawhood.api.recursive_inquiry as api
    monkeypatch.setattr(api, 'retain_measured_attempt_cost', lambda **kw: pytest.fail('aggregate became an attempt cost'))
    value = programme(tmp_path)
    result = {'operational_census': [{}] * attempt_count,
              'measured_invocation': {'cpu_seconds': 100, 'wall_seconds': 120, 'retained_bytes': 500}}
    assert value.decision_cost_paths('terminal', tmp_path / 'wave', result) == ()
    assert result['attempt_cost_attribution']['actual_attempt_costs'] == 'UNKNOWN'
    assert result['attempt_cost_attribution']['aggregate_invocation_reallocated'] is False
    assert result['measured_invocation']['cpu_seconds'] == 100
    assert list(tmp_path.iterdir()) == []


def test_existing_original_cost_event_is_reused_without_decimal_conversion(tmp_path, monkeypatch):
    import empirical_lawhood.api.recursive_inquiry as api
    monkeypatch.setattr(api, 'retain_measured_attempt_cost', lambda **kw: pytest.fail('original cost was republished'))
    value = programme(tmp_path)
    relative = 'battery-supply-measured-attempt/measured-attempt-cost.json'
    result = {'operational_census': [{}]}
    assert value.decision_cost_paths('fork', tmp_path / 'wave', result, (relative,)) == (relative,)
    assert 'measured_invocation' not in result


def test_one_actual_attempt_keeps_original_singleton_measurement_route(tmp_path, monkeypatch):
    import empirical_lawhood.api.recursive_inquiry as api
    observed = []
    monkeypatch.setattr(api, 'retain_measured_attempt_cost', lambda **kw: observed.append(kw))
    value = programme(tmp_path)
    result = {'operational_census': [{}], 'measured_invocation': {
        'cpu_seconds': '1.00000000000000000001', 'wall_seconds': '2.00000000000000000002', 'retained_bytes': 7}}
    assert value.decision_cost_paths('stop', tmp_path / 'wave', result) == ('stop-measured-attempt/measured-attempt-cost.json',)
    assert len(observed) == 1
    assert observed[0]['cpu_seconds'] == Decimal('1.00000000000000000001')
    assert observed[0]['wall_seconds'] == Decimal('2.00000000000000000002')
