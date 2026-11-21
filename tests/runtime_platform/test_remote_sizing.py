# SPDX-License-Identifier: MPL-2.0
"""Offline placement conformance: no cloud contact or numerical qualification."""

from dataclasses import asdict, replace
import json

import pytest
import yaml

from empirical_lawhood.api.accelerated_deployment import PERIODIC_CUDA_BACKEND, RunpodDeploymentSelection, prepare_accelerated_deployment
from empirical_lawhood.execution.resources.remote_sizing import (
    REMOTE_CONTROLLER_RESERVE_BYTES, RemotePlacementUnsupported, size_runpod_resources,
)
from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS
from tests.test_accelerated_deployment import payload, selection


def _gpu_plan(protocol_fixture):
    """A labelled synthetic placement control, not an actual GPU method."""
    plan = protocol_fixture.execution_plan
    tasks = tuple(replace(task, capability=replace(task.capability,
        requested_resources=replace(task.capability.requested_resources,
            gpu_devices=1 if task.task_id == 'prepare' else 0))) for task in plan.tasks)
    return replace(plan, tasks=tasks)


def test_host_sizing_contains_complete_task_census_and_leaves_science_unchanged(protocol_fixture):
    plan = _gpu_plan(protocol_fixture)
    original = plan.canonical_bytes()
    budgets = [task.capability.requested_resources for task in plan.tasks]
    selected = size_runpod_resources(plan, payload_bytes=100_000)
    assert selected.cpu_cores == sum(row.cpu_cores for row in budgets)
    assert selected.memory_bytes == sum(row.memory_bytes for row in budgets) + REMOTE_CONTROLLER_RESERVE_BYTES
    assert selected.gpu_devices == 1 and selected.wall_time_seconds is None
    assert selected.source_scan_bytes == 100_000
    assert selected.output_bytes == sum(task.maximum_attempts * task.capability.requested_resources.output_bytes
                                        for task in plan.tasks)
    assert plan.canonical_bytes() == original
    bigger = size_runpod_resources(plan, payload_bytes=100_000,
        cpu_cores=selected.cpu_cores + 2, memory_bytes=selected.memory_bytes + 1024)
    assert bigger.cpu_cores == selected.cpu_cores + 2
    assert bigger.memory_bytes == selected.memory_bytes + 1024
    for override in ({'cpu_cores': 1}, {'memory_bytes': 1}, {'cpu_cores': True}):
        with pytest.raises(RemotePlacementUnsupported, match='HOSTED_OVERRIDE_BELOW_REQUIREMENT'):
            size_runpod_resources(plan, payload_bytes=100_000, **override)


@pytest.mark.parametrize('coordinate', ('memory_bytes', 'source_scan_bytes', 'output_bytes'))
def test_unbounded_method_requirements_remain_explicit(protocol_fixture, coordinate):
    plan = _gpu_plan(protocol_fixture)
    first, *rest = plan.tasks
    changed = replace(first, capability=replace(first.capability,
        requested_resources=replace(first.capability.requested_resources, **{coordinate: None})))
    with pytest.raises(RemotePlacementUnsupported, match='HOSTED_FINITE_RESOURCES_REQUIRED') as failure:
        size_runpod_resources(replace(plan, tasks=(changed, *rest)), payload_bytes=100)
    assert first.task_id in str(failure.value)


@pytest.mark.parametrize('gpu_devices', (0, 2))
def test_unsupported_placement_has_capability_reason(protocol_fixture, gpu_devices):
    plan = protocol_fixture.execution_plan
    plan = replace(plan, tasks=tuple(replace(task, capability=replace(task.capability,
        requested_resources=replace(task.capability.requested_resources, gpu_devices=gpu_devices)))
        for task in plan.tasks))
    with pytest.raises(RemotePlacementUnsupported) as failure:
        size_runpod_resources(plan, payload_bytes=100)
    assert failure.value.reason_code == 'HOSTED_SINGLE_GPU_CAPABILITY_REQUIRED'


def test_public_derived_deployment_preserves_threads_payload_and_plan(protocol_fixture, tmp_path, monkeypatch):
    import builtins
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('sky', 'runpod', 'cupy', 'gpu4pyscf', 'openmm'):
            pytest.fail('offline sizing imported a native/provider implementation')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    plan = _gpu_plan(protocol_fixture)
    original = plan.canonical_bytes()
    root = payload(tmp_path)
    placement = asdict(selection())
    for name in ('resources', 'container_disk_gb', 'maximum_files', 'numerical_threads', 'sizing_plan_sha256', 'numerical_backend'):
        del placement[name]
    placement['accelerator'] = 'H100-SXM'
    selected = RunpodDeploymentSelection.for_execution_plan(plan, payload_root=root,
        numerical_threads=1, backend=PERIODIC_CUDA_BACKEND, **placement)
    assert selected.resources.cpu_cores > selected.numerical_threads
    assert selected.maximum_files == 3
    document = json.loads(json.dumps(selected.to_document()))
    assert document['version'] == '6.0.0'
    assert RunpodDeploymentSelection.from_document(document) == selected
    result = prepare_accelerated_deployment(selected, payload_root=root, output_directory=tmp_path/'prepared')
    task = yaml.safe_load((tmp_path/'prepared/task.yaml').read_text())
    assert all(task['envs'][name] == '1' for name in (*NUMERICAL_THREAD_ENV_VARS, 'OPENMM_CPU_THREADS'))
    assert task['resources']['accelerators'] == 'H100-SXM:1'
    assert result['resource_derivation']['execution_plan_sha256'] == plan.fingerprint()
    assert result['resource_derivation']['task_scientific_settings'] == 'UNCHANGED'
    assert plan.canonical_bytes() == original
    assert result['execution_authority'] == 'NONE'


@pytest.mark.parametrize('damage', ('threads', 'plan', 'accelerator', 'old-revision'))
def test_derived_revision_refuses_partial_or_unversioned_selection(damage):
    selected = replace(selection(), accelerator='H100-SXM', numerical_threads=1, sizing_plan_sha256='c'*64,
        numerical_backend=PERIODIC_CUDA_BACKEND.accelerated_backend)
    document = json.loads(json.dumps(selected.to_document()))
    if damage == 'threads': del document['numerical_threads']
    elif damage == 'plan': del document['sizing_plan_sha256']
    elif damage == 'accelerator': del document['accelerator']
    else: document['version'] = '4.0.0'
    with pytest.raises(ValueError, match='automatic deployment'):
        RunpodDeploymentSelection.from_document(document)


def test_registered_external_boundary_preserves_tighter_task_output_and_time(protocol_fixture):
    from types import SimpleNamespace
    from empirical_lawhood.execution.execution import (
        RunnerResult, TaskContext, TaskOutputPayload, WorkerIsolationProfile, WorkerOutputPort,
    )
    from empirical_lawhood.execution.remote.external_execution import (
        ExternalExecutionBackendKind, ExternalExecutionError,
        RegisteredExecutionBackend, RegisteredExternalTaskExecutor,
    )
    task = protocol_fixture.execution_plan.task('prepare')
    manifest = protocol_fixture.registry.resolve(task.capability.capability_key, task.capability.capability_version)
    manifest = replace(manifest, resource_ceiling=replace(manifest.resource_ceiling, wall_time_seconds=10))
    context = TaskContext(
        run_id=protocol_fixture.run_plan.run_plan_id, task_id=task.task_id,
        attempt_id='remote.boundary.attempt', config=task.capability.config,
        input_bindings=(), input_ports=(), output_ports=tuple(WorkerOutputPort(
            output_id=output.output_id, payload_schema=output.payload_schema,
            profile=output.profile, media_type=output.media_type) for output in task.outputs),
        permissions=task.capability.required_permissions, outcome_access=task.capability.requested_outcome_access,
        resource_budget=task.capability.requested_resources, isolation_profile=WorkerIsolationProfile.TRUSTED_LOCAL,
    )
    class Transport:
        transport_id = 'exposed.remote.boundary'
        implementation_sha256 = 'a' * 64
        calls = 0
        def execute(self, _backend, _runner, current, *, timeout_seconds):
            self.calls += 1
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, b'exposed-nonempty')
                                      for port in current.output_ports), ())
    transport = Transport()
    backend = RegisteredExecutionBackend('exposed.remote.backend', ExternalExecutionBackendKind.REMOTE_REGISTERED,
        transport.transport_id, transport.implementation_sha256, (manifest.registry_id,), 10, 10_000, True, True)
    executor = RegisteredExternalTaskExecutor(backend, transport)
    runner = SimpleNamespace(manifest=manifest)
    executor.execute(runner, context, timeout_seconds=1)
    assert transport.calls == 1
    with pytest.raises(ExternalExecutionError, match='selected task ceiling'):
        executor.execute(runner, context, timeout_seconds=2)
    assert transport.calls == 1
    smaller = replace(context, resource_budget=replace(context.resource_budget, output_bytes=0))
    with pytest.raises(ExternalExecutionError, match='output ceiling'):
        executor.execute(runner, smaller, timeout_seconds=1)
    assert transport.calls == 2


def test_host_sizing_uses_the_exact_declared_resource_envelope(protocol_fixture):
    from tests.runtime_platform.test_multicore_envelope_admission import _selected_plan
    plan, resource_spec = _selected_plan(protocol_fixture, workers=2, aggregate_slots=1, cpu_cores=3)
    first, *rest = plan.tasks
    first = replace(first, capability=replace(first.capability,
        requested_resources=replace(first.capability.requested_resources, gpu_devices=1)))
    plan = replace(plan, tasks=(first, *rest))
    selected = size_runpod_resources(plan, payload_bytes=100, resource_spec=resource_spec)
    assert selected.cpu_cores == 6
    assert selected.memory_bytes == 1_000_000 + REMOTE_CONTROLLER_RESERVE_BYTES
    with pytest.raises(RemotePlacementUnsupported, match='HOSTED_RESOURCE_ENVELOPE_REQUIRED'):
        size_runpod_resources(plan, payload_bytes=100)
    with pytest.raises(RemotePlacementUnsupported, match='HOSTED_RESOURCE_ENVELOPE_MISMATCH'):
        size_runpod_resources(plan, payload_bytes=100,
            resource_spec=replace(resource_spec, maximum_parallel_tasks=3))


def test_remote_worker_lock_and_example_select_this_release():
    from pathlib import Path
    import tomllib
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / 'pyproject.toml').read_text())
    lock = tomllib.loads((root / 'configs/accelerated-compute/worker/uv.lock').read_text())
    own = [row for row in lock['package'] if row['name'] == project['project']['name']]
    assert len(own) == 1 and own[0]['version'] == project['project']['version']
    assert own[0]['source'] == {'directory': '../../../'}
    example = json.loads((root / 'configs/accelerated-compute/selection.example.json').read_text())
    assert example['source_wheel'] == 'empirical_lawhood-' + project['project']['version'] + '-py3-none-any.whl'


def test_execution_supervision_requires_application_bound_provider_ports(tmp_path):
    from empirical_lawhood.execution.remote.deployment_supervision import supervise_deployment as lifecycle
    from tests.test_deployment_supervision import selection
    path, _ = selection(tmp_path)
    output = tmp_path / 'unentered'
    with pytest.raises(TypeError, match='application-bound action port'):
        lifecycle(path, output_directory=output)
    assert not output.exists()


def test_unknown_numerical_backend_refuses_before_payload_preparation(tmp_path):
    root = payload(tmp_path)
    selected = replace(selection(), accelerator='H100-SXM', numerical_threads=1,
        sizing_plan_sha256='c' * 64, numerical_backend='exposed.unsupported-cuda')
    output = tmp_path / 'unentered'
    with pytest.raises(ValueError, match='HOSTED_WORKER_PROFILE_UNSUPPORTED'):
        prepare_accelerated_deployment(selected, payload_root=root, output_directory=output)
    assert not output.exists()


def test_historical_bundle_remains_readable_but_wrong_native_profile_cannot_bootstrap(tmp_path):
    from empirical_lawhood.execution.remote.accelerated_worker_bundle import WorkerBundle, render_worker_bootstrap
    specification = {
        'version': '1.0.0', 'base_image': selection().image,
        'source_image_sha256': 'a' * 64, 'source_lock_sha256': 'b' * 64,
        'source_lock': 'uv.lock', 'requirements': 'requirements.txt', 'wheels': 'wheels',
        'uv_wheel': 'uv.whl', 'system_package': 'libgomp.deb',
        'installed_versions': {'pyscf': '2.14.0'},
    }
    path = tmp_path / 'historical.json'
    raw = json.dumps(specification).encode()
    path.write_bytes(raw)
    bundle = WorkerBundle.read(path)
    assert bundle.installed_versions == {'pyscf': '2.14.0'}
    with pytest.raises(ValueError, match='HOSTED_WORKER_PROFILE_UNSUPPORTED.*openmm'):
        render_worker_bootstrap(bundle, remote_root='/selected/bundle')
    assert path.read_bytes() == raw
