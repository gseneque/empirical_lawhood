# SPDX-License-Identifier: MPL-2.0
"""Declared operational settings freeze before preparation, without native entry."""

from dataclasses import replace
import os
from types import MappingProxyType

import pytest

from empirical_lawhood.infrastructure.execution import _select_worker_environment, prepare_worker_invocation
from empirical_lawhood.infrastructure.numerical_provenance import selected_worker_environment
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties
from tests.runtime_platform.test_worker_preflight import _case


def select_optional(environment):
    environment.setdefault("CASADIPATH", "/tmp/exposed-selected-engine")
    return MappingProxyType(environment)


def test_selector_additions_freeze_in_the_complete_invocation_without_mutating_parent(tmp_path, monkeypatch):
    monkeypatch.delenv("CASADIPATH", raising=False)
    before = dict(os.environ)
    _, bundle, runner, context, original, _ = _case(tmp_path)
    try:
        contract = prepare_worker_invocation(runner, context, bundle.verified_inputs,
            implementation=original.implementation, execution_plan=original.execution_plan,
            execution_task=original.execution_task, execution_task_record=original.execution_task_record,
            worker_environment_selector=select_optional)
        expected = dict(original.environment.selected_environment, CASADIPATH="/tmp/exposed-selected-engine")
        assert contract.environment.selected_environment == tuple(sorted(expected.items()))
        assert contract.environment.fingerprint() != original.environment.fingerprint()
        assert contract.identity != original.identity
        assert contract.native_work == original.native_work
        assert all(port.bytes_read == 0 for port in context.input_ports)
        contract.require_complete()
        assert dict(os.environ) == before
    finally:
        bundle.close()


def test_explicit_caller_setting_is_retained_and_no_selector_preserves_previous_selection(monkeypatch):
    monkeypatch.setenv("CASADIPATH", "/tmp/explicit-wrong-caller-setting")
    expected = selected_worker_environment()
    assert _select_worker_environment() == expected
    assert _select_worker_environment(select_optional) == expected


@pytest.mark.parametrize("damage", ("remove", "thread", "explicit", "unknown", "non-string-key", "non-string-value", "sequence", "none"))
def test_selector_cannot_replace_settings_or_add_undeclared_process_configuration(monkeypatch, damage):
    monkeypatch.setenv("CASADIPATH", "/tmp/explicit-selected-setting")
    original = dict(selected_worker_environment())
    before = dict(os.environ)

    def hostile(environment):
        if damage == "remove":
            environment.pop("LANG")
        elif damage == "thread":
            environment["OMP_NUM_THREADS"] = "2"
        elif damage == "explicit":
            environment["CASADIPATH"] = "/tmp/automatically-overwritten-setting"
        elif damage == "unknown":
            environment["EL_UNDECLARED_SETTING"] = "unexpected"
        elif damage == "non-string-key":
            environment[1] = "unexpected"
        elif damage == "non-string-value":
            environment["CASADIPATH"] = 1
        elif damage == "sequence":
            return tuple(environment.items())
        else:
            return None
        return environment

    with pytest.raises(ValueError):
        _select_worker_environment(hostile)
    assert dict(selected_worker_environment()) == original
    assert dict(os.environ) == before


def test_invalid_registered_selector_refuses_cold_and_single_declaration_derives_same_callback():
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.controlled_operation_bindings_v1_1 import operation_declaration
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.prepared_native import native_worker_environment
    declaration = operation_declaration()
    assert declaration.execution_properties.worker_environment_selector is native_worker_environment
    assert declaration.registration().worker_environment_selector is native_worker_environment
    assert declaration.provider_factory().registration.worker_environment_selector is native_worker_environment
    with pytest.raises(TypeError, match="code-owned callback"):
        replace(declaration.registration(), worker_environment_selector="caller-selected-code")
    with pytest.raises(TypeError, match="code-owned callback"):
        replace(declaration, execution_properties=RecursiveExecutionProperties(worker_environment_selector="caller-selected-code"))
    with pytest.raises(TypeError, match="code-owned callback"):
        _select_worker_environment("caller-selected-code")
