# SPDX-License-Identifier: MPL-2.0
"""Frozen task selections do not construct unrelated installed science."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_operations as owner
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture


def selected(monkeypatch, *, absent=False, factory_drift=False, runner_drift=False):
    draft, registrations, original = fixture()
    unused = replace(original.capabilities[0], capability_key="unrelated.unavailable")
    registry = CapabilityRegistry(original.registry_id,
        tuple(sorted((*original.capabilities, unused), key=lambda row: row.registry_id)))
    plan = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="1" * 40).execution_plan
    calls = []
    factories = []
    for index, manifest in enumerate(original.capabilities):
        if absent and index == 0:
            continue
        declared = replace(manifest, implementation_sha256="b" * 64) if factory_drift and index == 0 else manifest
        def build(manifest=manifest):
            calls.append(manifest.capability_key)
            actual = replace(manifest, implementation_sha256="c" * 64) if runner_drift else manifest
            return SimpleNamespace(manifest=actual)
        factories.append(SimpleNamespace(manifest=declared, runner_factory=build, runner_preparation_factory=None))
    def unavailable():
        pytest.fail("unselected domain implementation was constructed")
    factories.append(SimpleNamespace(manifest=unused, runner_factory=unavailable))
    monkeypatch.setattr(owner, "operation_factories", lambda: tuple(factories))
    return registry, plan, calls


def test_only_selected_factories_construct_and_resolve_against_the_frozen_registry(monkeypatch):
    registry, plan, calls = selected(monkeypatch)
    runners = owner.operation_runners(registry=registry, plan=plan)
    assert calls == ["generic.source", "generic.use"]
    assert runners.registry_sha256 == plan.registry_sha256
    for task in plan.tasks:
        assert runners.resolve(task).manifest == registry.resolve(
            task.capability.capability_key, task.capability.capability_version)


@pytest.mark.parametrize("changes", [{"absent": True}, {"factory_drift": True}])
def test_missing_or_changed_selected_factory_refuses_before_any_runner_constructs(monkeypatch, changes):
    registry, plan, calls = selected(monkeypatch, **changes)
    with pytest.raises(ValueError, match="selected operation"):
        owner.operation_runners(registry=registry, plan=plan)
    assert not calls


def test_registry_substitution_refuses_before_any_domain_constructs(monkeypatch):
    registry, plan, calls = selected(monkeypatch)
    changed = CapabilityRegistry("registry.changed", registry.capabilities)
    with pytest.raises(ValueError, match="exact frozen plan and registry"):
        owner.operation_runners(registry=changed, plan=plan)
    assert not calls


def test_constructed_runner_cannot_substitute_the_registered_manifest(monkeypatch):
    registry, plan, _ = selected(monkeypatch, runner_drift=True)
    with pytest.raises(ValueError, match="selected runner changed"):
        owner.operation_runners(registry=registry, plan=plan)


def test_declared_parent_preparation_requires_supplier_before_runner_construction(monkeypatch):
    registry, plan, calls = selected(monkeypatch)
    factories = owner.operation_factories()
    factories[0].runner_preparation_factory = lambda *_: pytest.fail("missing supplier reached parent preparation")
    with pytest.raises(PermissionError, match="parent input/custody supplier"):
        owner.operation_runners(registry=registry, plan=plan)
    assert not calls


def test_development_uses_exact_registered_parent_preparation_without_running_it(monkeypatch):
    from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner

    registry, plan, calls = selected(monkeypatch)
    factories = owner.operation_factories()
    factories[0].registration = SimpleNamespace(native_effect=False)
    supplied, observations = object(), []
    def prepare(supplier, runner):
        observations.append((supplier, runner.manifest))
        return ParentPreparedTaskRunner(runner.manifest, lambda _: pytest.fail("runner preparation entered during discovery"))
    factories[0].runner_preparation_factory = prepare
    runners = owner.operation_runners(registry=registry, plan=plan, input_supplier=supplied)
    assert observations == [(supplied, factories[0].manifest)]
    assert calls == ["generic.source", "generic.use"]
    task = next(task for task in plan.tasks if task.capability.capability_key == factories[0].manifest.capability_key)
    assert type(runners.resolve(task)) is ParentPreparedTaskRunner
