# SPDX-License-Identifier: MPL-2.0
"""Exposed initial battery work projection; no acquisition or readiness claim."""

from dataclasses import replace
import os
import pickle
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as ob
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import prepare_native_work
from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, segmented_native as native
from empirical_lawhood.infrastructure.artifact_stream_primitives import _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input
from empirical_lawhood.infrastructure.execution import _prepare_native_work
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputPort, WorkerIsolationProfile
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from tests.test_battery_segmented_graph import context_for, stock as stock


@pytest.fixture
def selected_context(stock):
    config = stock.configs[ob.node_id('forecast', 0)]
    runner, original = context_for(stock, config)
    ports = []
    for source in original.input_ports:
        binding = WorkerInputBinding(source.artifact_id, source.materialization_id, source.payload_schema,
            source.media_type, source.size_bytes, source.visibility_ceiling, source.outcome_access, source.kind)
        descriptor = _anonymous_input_descriptor()
        try:
            remaining = memoryview(source.raw)
            while remaining:
                remaining = remaining[os.write(descriptor, remaining):]
            _seal_anonymous_input(descriptor)
            ports.append(WorkerInputPort(binding, _PreopenedBoundedReader(descriptor, maximum_bytes=source.size_bytes)))
        except BaseException:
            os.close(descriptor)
            raise
        finally:
            source.close()
    ports = tuple(sorted(ports, key=lambda row: row.artifact_id))
    context = TaskContext(original.run_id, original.task_id, original.run_id + '.' + original.task_id + '.attempt-001',
        CapabilityConfigRef(config.config_id, config.SCHEMA, runner.manifest.config_schema_sha256,
            config.fingerprint(), original.config.artifact_id), tuple(row.binding for row in ports), ports,
        original.output_ports, original.permissions, original.outcome_access, original.resource_budget,
        WorkerIsolationProfile.TRUSTED_LOCAL, original.dependency_receipts)
    parent = NativeEffectContact(context.run_id, context.task_id, context.attempt_id,
        ObjectIdentity('plan.exposed-battery-projection', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1' * 64),
        ObjectIdentity(context.task_id, 'empirical-lawhood/runtime/execution-task', '1.0.0', '2' * 64),
        stock.provenance.observed_git_head, context.input_materialization_ids, context.dependency_receipt_ids)
    try:
        yield runner, context, parent, config
    finally:
        for port in ports:
            port.close()


def test_installed_forecast_alone_registers_the_same_initial_native_preparer():
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.prepared_native import native_worker_environment
    registrations = ob.operation_registrations()
    forecast, = (row for row in registrations if row.selection.capability_key == ob.NAMESPACE + '.forecast')
    assert forecast.native_work_preparer is prepare_native_work
    assert forecast.worker_environment_selector is native_worker_environment
    assert all(row.native_work_preparer is None for row in registrations if row is not forecast)
    assert all(row.worker_environment_selector is None for row in registrations if row is not forecast)
    assert len(registrations) == 6


@pytest.mark.parametrize("operation", ob.OPERATIONS)
def test_installed_runner_supports_spawn_pickle_reconstruction(operation):
    runner = ob.SegmentedRunner(operation)
    restored = pickle.loads(pickle.dumps(runner))
    assert type(restored) is type(runner)
    assert restored.operation == operation and restored.manifest == runner.manifest


@pytest.mark.native
def test_repeated_projection_uses_independent_sealed_cursors_and_no_parent_library_import(selected_context):
    runner, context, parent, config = selected_context
    loaded = 'pybamm' in sys.modules
    first = _prepare_native_work(prepare_native_work, runner, context, parent)
    second = _prepare_native_work(prepare_native_work, runner, context, parent)
    assert first.canonical_bytes() == second.canonical_bytes()
    assert ('pybamm' in sys.modules) == loaded
    assert all(port.bytes_read == 0 for port in context.input_ports)
    assert first.expected_parent == parent
    assert first.scientific_unit_ids == (c.UNIT,)
    assert first.native_effect_slot_ids == ob.native_effect_slot_ids(config)
    assert len(first.definitions) == len(first.rosters) == 1
    definition, = first.definitions
    assert definition.parent_contact == parent
    assert definition.input_materialization_ids == context.input_materialization_ids
    assert first.rosters[0].subworks == (definition.identity,)
    # The preparation checkpoint and segment calls require genuine produced
    # context; the initial preparation must neither invent nor enter them.
    assert definition.operation_id == 'battery.segmented-native.forecast'
    assert not any(row.operation_id.endswith(('.preparation', '.segment')) for row in first.definitions)
    _, decoded, _ = runner.forecast_operands(context)
    original = native.build_forecast_definition(decoded['native-config'], decoded['selected-protocol'],
        decoded['producing-provenance'], SimpleNamespace(parent_contact=parent), context.input_materialization_ids)
    assert original.canonical_bytes() == definition.canonical_bytes()


def test_live_installed_forecast_refuses_missing_complete_contract_before_any_progress(selected_context):
    runner, context, _, _ = selected_context

    class ForbiddenProgress:
        def __getattr__(self, name):
            raise AssertionError('missing prepared work contacted native progress: ' + name)

    with pytest.raises(ValueError, match='complete prepared native work'):
        runner.execute_streaming_with_native_subwork(context, ForbiddenProgress(), None)


@pytest.mark.parametrize('change', ('task', 'config', 'input', 'receipt'))
def test_initial_scientific_operands_refuse_original_context_substitutions(selected_context, change):
    runner, context, parent, _ = selected_context
    if change == 'task':
        context = replace(context, task_id='task.exposed-substitute')
    elif change == 'config':
        context = replace(context, config=replace(context.config, content_sha256='9' * 64))
    elif change == 'input':
        port = context.input_ports[0]
        binding = replace(port.binding, media_type='application/x-unselected')
        ports = (replace(port, binding=binding), *context.input_ports[1:])
        context = replace(context, input_ports=ports, input_bindings=tuple(row.binding for row in ports))
    else:
        receipt = context.dependency_receipts[0]
        context = replace(context, dependency_receipts=(replace(receipt, task_id='task.exposed-other-producer'),
            *context.dependency_receipts[1:]))
    with pytest.raises(ValueError):
        _prepare_native_work(prepare_native_work, runner, context, parent)


@pytest.mark.parametrize('change', ('run_id', 'task_id', 'attempt_id', 'input_materialization_ids', 'dependency_receipt_ids'))
def test_initial_projection_refuses_full_anticipated_parent_context_drift(selected_context, change):
    runner, context, parent, _ = selected_context
    value = () if change.endswith('_ids') else 'exposed.parent-substitution'
    changes = {change: value}
    if change == 'task_id':
        changes['execution_task'] = replace(parent.execution_task, object_id=value)
    parent = replace(parent, **changes)
    with pytest.raises(ValueError, match='full anticipated original parent/context'):
        _prepare_native_work(prepare_native_work, runner, context, parent)
