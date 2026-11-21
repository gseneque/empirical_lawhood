# SPDX-License-Identifier: MPL-2.0
"""Shared operational selection and resource controls; no GPU science is claimed."""

from dataclasses import replace
import os

import pytest

from empirical_lawhood.execution.resources import accelerated_compute as devices
from empirical_lawhood.execution.local import execution
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.compute_backend import ACCELERATED_COMPUTE_ENV, ComputeBackendDeclaration, worker_acceleration_selection
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.operational_configuration import accelerated_compute_operation
from tests.runtime_platform.test_worker_preflight import _case, ExposedReadRunner


class AccelerationEchoRunner(ExposedReadRunner):
    def execute(self, context):
        from tests.runtime_platform.test_native_subwork import ExposedInput
        assert context.accelerated_compute == worker_acceleration_selection(os.environ.items())
        value = ExposedInput('exposed.config', str(context.accelerated_compute))
        return RunnerResult((TaskOutputPayload('echo', value.canonical_bytes()),), ())


@pytest.mark.parametrize('enabled', (False, True))
def test_actual_spawned_worker_receives_bound_flag_and_preserves_default_environment(tmp_path, enabled):
    from tests.runtime_platform.test_native_subwork import ExposedInput
    plane, bundle, original, context, contract, _ = _case(tmp_path, actual=True)
    runner = AccelerationEchoRunner()
    assert runner.manifest == original.manifest
    try:
        context = replace(context, accelerated_compute=enabled)
        contract = execution.prepare_worker_invocation(runner, context, bundle.verified_inputs,
            implementation=contract.implementation, execution_plan=contract.execution_plan,
            execution_task=contract.execution_task, execution_task_record=contract.execution_task_record)
        settings = dict(contract.environment.selected_environment)
        assert (ACCELERATED_COMPUTE_ENV in settings) is enabled
        contract.validate_context(context)
        with pytest.raises(ValueError, match='accelerated_compute'):
            contract.validate_context(replace(context, accelerated_compute=not enabled))
        executor = execution.LocalProcessExecutor(scratch_root=plane.root)
        result = executor.execute_deadline_free(runner, context, progress_contract=None,
            progress_callback=lambda _: None, prepared_contract=contract)
        value = decode_canonical_bytes(result.outputs[0].payload, ExposedInput, maximum_bytes=1024)
        assert value.value == str(enabled)
    finally:
        bundle.close()


def test_declarations_report_unsupported_operations_without_gpu_contact():
    cpu = ComputeBackendDeclaration('rc.reference')
    assert cpu.selection(True) == dict(accelerated_compute=True, backend='rc.reference',
        gpu_devices=0, disposition='UNSUPPORTED_OPERATION')
    gpu = ComputeBackendDeclaration('reference.cpu', 'reference.cuda', 1)
    assert gpu.selection(False)['backend'] == 'reference.cpu'
    assert gpu.selection(True)['gpu_devices'] == 1
    for value in (0, 1, 'true', None):
        with pytest.raises(TypeError):
            gpu.selection(value)


def test_existing_rc_workload_reports_actual_cpu_backend_for_both_selections(tmp_path, monkeypatch):
    """Two independent native views run through the public CLI on both paths."""
    import builtins
    import json
    from pathlib import Path
    from typer.testing import CliRunner
    from empirical_lawhood.cli.app import app
    from empirical_lawhood.execution.operational_configuration import OperationalConfiguration

    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('cupy', 'gpu4pyscf', 'sky'):
            pytest.fail('CPU conformance workload contacted an optional backend')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    model = Path(__file__).resolve().parents[1] / (
        'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json')
    reports = []
    for enabled in (False, True):
        config = tmp_path / f'operational-{enabled}.json'
        config.write_bytes(OperationalConfiguration(accelerated_compute=enabled).canonical_bytes())
        output = tmp_path / f'attempt-{enabled}'
        result = CliRunner().invoke(app, ['--operational-config', str(config), 'campaign',
            'rc-ladder-native-check', '--config', str(model), '--output-dir', str(output)])
        assert result.exit_code == 0, result.output
        report = json.loads(result.stdout)
        backend = report.pop('compute_backend')
        assert backend == dict(accelerated_compute=enabled, backend='rc-ladder.scipy-cpu',
            gpu_devices=0, disposition='UNSUPPORTED_OPERATION' if enabled else 'NOT_REQUESTED')
        invocation = json.loads((output / 'invocation.json').read_bytes())
        assert invocation['operational_configuration']['value']['accelerated_compute'] is enabled
        assert report['native_numerical_check_executed'] and not report['campaign_issued']
        # This check owns selection invariance, not a new RC accuracy gate.
        import math
        assert math.isfinite(report['maximum_backward_euler_defect_v'])
        reports.append(report)
    assert reports[0] == reports[1]


def test_gpu_observation_respects_ordered_visibility_and_memory_units():
    raw = b'0, GPU-aaaa, 81920, 80000, 8.0, A100, 570.0\n1, GPU-bbbb, 81920, 70000, 8.0, A100, 570.0\n'
    values = devices.parse_cuda_devices(raw, visible_devices='GPU-bbbb,0')
    assert [r.physical_index for r in values] == [1, 0]
    assert values[0].free_memory_bytes == 70000*2**20
    assert devices.parse_cuda_devices(raw, visible_devices='-1') == ()
    for value in ('0,0', '2', 'GPU-', 'MIG-aaaa/0/1', ' 0'):
        with pytest.raises(ValueError):
            devices.parse_cuda_devices(raw, visible_devices=value)


@pytest.mark.parametrize('gpu_count,enabled', ((0, False), (0, True), (1, False)))
def test_unselected_or_cpu_only_work_does_not_probe_devices(monkeypatch, gpu_count, enabled):
    from empirical_lawhood.science.identity.authority import ResourceBudget
    from empirical_lawhood.execution.execution import ExecutionAssuranceProfile
    from empirical_lawhood.execution.plans import PlanLane
    from types import SimpleNamespace
    monkeypatch.setattr(devices, 'observe_cuda_devices', lambda: pytest.fail('unselected device probe'))
    budget = ResourceBudget(1, 1024, gpu_count, None, None, None)
    monkeypatch.setattr(execution, 'selected_execution_resource_budgets', lambda *a: (budget,))
    with accelerated_compute_operation(enabled):
        admitted = execution.LocalExecutionResourceAdmitter().assess(SimpleNamespace(lane=PlanLane.DEVELOPMENT),
            available_scratch_bytes=1, executor_enforces_resources=False, executor_enforces_no_network=False,
            assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    assert admitted.admitted is (gpu_count == 0)
    if gpu_count:
        assert 'ACCELERATED_COMPUTE_NOT_SELECTED' in admitted.reason_codes


@pytest.mark.parametrize('available,selected', ((0, None), (1, None), (2, None), (1, 0), (1, 1)))
def test_gpu_admission_requires_one_actual_device_and_preserves_explicit_capacity(monkeypatch, available, selected):
    from empirical_lawhood.science.identity.authority import ResourceBudget
    from empirical_lawhood.execution.execution import ExecutionAssuranceProfile
    from empirical_lawhood.execution.plans import PlanLane
    from types import SimpleNamespace
    monkeypatch.setattr(devices, 'observe_cuda_devices', lambda: (object(),)*available)
    budget = ResourceBudget(1, 1024, 1, None, None, None)
    monkeypatch.setattr(execution, 'selected_execution_resource_budgets', lambda *a: (budget,))
    capacity = (None if selected is None else
        execution.ExecutionResourceCapacity(1, 2**30, selected, True, True, False))
    with accelerated_compute_operation(True):
        admitted = execution.LocalExecutionResourceAdmitter(capacity).assess(SimpleNamespace(lane=PlanLane.DEVELOPMENT),
            available_scratch_bytes=1, executor_enforces_resources=False, executor_enforces_no_network=False,
            assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    assert admitted.admitted is (available == 1 and selected != 0)


def test_cuda_virtual_address_reservation_is_not_treated_as_host_ram(monkeypatch):
    from empirical_lawhood.science.identity.authority import ResourceBudget
    calls = []
    monkeypatch.setattr(execution, '_restrict_resource_limit', lambda *v: calls.append(v))
    monkeypatch.setattr(os, 'sched_getaffinity', lambda _: {0})
    execution._apply_resource_limits(ResourceBudget(1, 2**30, 1, None, None, None), deadline_free=True)
    assert calls == []
    execution._apply_resource_limits(ResourceBudget(1, 2**30, 0, None, None, None), deadline_free=True)
    assert calls == [(execution.resource.RLIMIT_AS, 2**30)]
