# SPDX-License-Identifier: MPL-2.0
"""Current declaration identity without an unrelated five-phase construction."""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import physical_forecast_implementation
from empirical_lawhood.kernel.provenance import ObjectIdentity


def test_selected_manifest_has_exact_full_roster_bytes_and_constructs_only_its_owner(monkeypatch):
    expected = next(row for row in owner.response_manifests() if row.capability_key.endswith('.physical-forecast'))
    original, calls = owner._response_declaration, []

    def construct(*phase):
        calls.append(phase[0])
        return original(*phase)

    monkeypatch.setattr(owner, '_response_declaration', construct)
    assert owner.response_manifest('physical-forecast').canonical_bytes() == expected.canonical_bytes()
    assert physical_forecast_implementation() == ObjectIdentity.from_record(expected.capability_key, expected)
    assert calls == ['physical-forecast', 'physical-forecast']


def test_changed_installed_declaration_is_observed_on_the_next_selection(monkeypatch):
    original_pin = physical_forecast_implementation()
    original = owner._response_declaration

    def changed(*phase):
        value = original(*phase)
        return replace(value, implementation_id=value.implementation_id + '.changed')

    monkeypatch.setattr(owner, '_response_declaration', changed)
    assert physical_forecast_implementation() != original_pin
    with pytest.raises(ValueError, match='one installed phase'):
        owner.response_manifest('unknown')
