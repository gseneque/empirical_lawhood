# SPDX-License-Identifier: MPL-2.0
"""Selected finite resource admission; synthetic software custody only."""

from dataclasses import fields, replace
import os
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.execution import CampaignExecutionService, CampaignPrerequisiteError, CampaignValidationError
from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.api.results import RunCampaignRequest
from empirical_lawhood.infrastructure.execution import (
    DirectTaskExecutor, DurableExecutionResourceEnvelopeCoordinator, ExecutionResourceCapacity,
    LocalExecutionResourceAdmitter, LocalScheduler, ResourceAdmissionError,
    selected_execution_resource_budgets,
)
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec, NonTimeResourceBudget,
)
from empirical_lawhood.runtime.plans import ExecutionPlan, ExecutionTask, ProtocolExecutionTask
from empirical_lawhood.runtime.recovery import RunRecoveryIndex
from tests.issued_study_support import build_issued_study_fixture
from tests.runtime_platform.test_deadline_free_execution_package import (
    _compile, _execution_package_fixture, _external_inputs, _plane, _ResourceEnvelopeStore,
)
from tests.runtime_platform.test_execution_scheduler import DeterministicRunner


def _pin(name, schema):
    return ObjectIdentity(name, schema, "1.0.0", "a" * 64)


def _selected_plan(protocol, *, workers=4, aggregate_slots=2, cpu_cores=1):
    original = next(task for task in protocol.execution_plan.tasks if task.task_id == "prepare")
    tasks = []
    for index in range(4):
        values = {field.name: getattr(original, field.name) for field in fields(ProtocolExecutionTask)}
        values.update(task_id="finite-ready." + str(index), dependency_task_ids=(), resource_lock_ids=(), maximum_attempts=1,
            capability=replace(original.capability, requested_resources=replace(
                original.capability.requested_resources, cpu_cores=cpu_cores)),
            outputs=tuple(replace(output, output_id=output.output_id + "." + str(index),
                logical_artifact_id=output.logical_artifact_id + "." + str(index),
                relative_path="runs/" + protocol.run_plan.run_plan_id + "/outputs/finite-ready." + str(index)
                    + "/" + output.output_id + ".json") for output in original.outputs))
        tasks.append(ExecutionTask(**values, scientific_inputs=()))
    extension = _pin("extension.finite-software", "empirical-lawhood/runtime/issued-extension-set")
    cells = tuple(ExecutionResourceTaskCellSpec(
        cell_id="cell." + task.task_id, task_id=task.task_id, child_id="child.finite-software",
        physical_independent_unit_id=None, preparation_unit_id=None, maximum_attempts=1,
        physical_execution_cost=0, retry_token_cost=0, native_simulator_launch=False,
        resource_budget=NonTimeResourceBudget(
            budget_id="budget." + task.task_id,
            cpu_cores=task.capability.requested_resources.cpu_cores,
            memory_bytes=task.capability.requested_resources.memory_bytes,
            output_bytes=task.capability.requested_resources.output_bytes,
            source_request_limit=0, source_byte_limit=task.capability.requested_resources.source_scan_bytes),
        progress_liveness=None, jit_cell_id=None, jit_signature_sha256=None) for task in tasks)
    spec = ExecutionResourceEnvelopeSpec("resource-spec.finite-software", extension, cells,
        (ChildResourceTokenLimit("child.finite-software", 0, 0),), (), (), (), None, None,
        workers, aggregate_slots * cells[0].resource_budget.memory_bytes, (), (), "b" * 64, True, True, True, True)
    base = protocol.execution_plan
    plan = ExecutionPlan(base.execution_plan_id, base.lane, base.source_plan, base.registry_sha256,
        base.implementation_commit, tuple(tasks), base.nonactuating,
        candidate=_pin("candidate.finite-software", "empirical-lawhood/planning/standard-candidate"),
        issued_extension_set=extension,
        execution_resource_envelope_spec=ObjectIdentity.from_record(spec.envelope_spec_id, spec),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    return plan, spec


def _assess(plan, spec, *, workers=4, memory=10_000_000, cpu=4):
    return LocalExecutionResourceAdmitter(ExecutionResourceCapacity(cpu, memory, 0, True, True, False)).assess(
        plan, available_scratch_bytes=1_000_000, executor_enforces_resources=True,
        executor_enforces_no_network=False, resource_spec=spec, maximum_parallel_tasks=workers)


def test_selected_single_worker_ceiling_refuses_requested_four(protocol_fixture):
    plan, spec = _selected_plan(protocol_fixture, workers=1)
    result = _assess(plan, spec)
    assert not result.admitted and result.reason_codes == ("ISSUED_PARALLEL_LIMIT_EXCEEDED",)


@pytest.mark.parametrize("coordinate", ("cpu_cores", "memory_bytes", "output_bytes", "source_scan_bytes"))
def test_selected_cells_must_equal_exact_frozen_task_requests(protocol_fixture, coordinate):
    plan, spec = _selected_plan(protocol_fixture)
    task = plan.tasks[0]
    changed = replace(task, capability=replace(task.capability, requested_resources=replace(
        task.capability.requested_resources, **{coordinate: None if coordinate != "cpu_cores" else 2})))
    with pytest.raises(ValueError, match="frozen task budget"):
        _assess(replace(plan, tasks=(changed, *plan.tasks[1:])), spec)


def test_selected_cell_census_is_complete(protocol_fixture):
    plan, spec = _selected_plan(protocol_fixture)
    with pytest.raises(ValueError, match="complete execution plan"):
        _assess(replace(plan, tasks=plan.tasks[:-1]), spec)


def test_legacy_unlimited_resources_are_preserved_without_selected_cells(protocol_fixture):
    plan = replace(protocol_fixture.execution_plan, tasks=tuple(replace(task,
        capability=replace(task.capability, requested_resources=replace(
            task.capability.requested_resources, memory_bytes=None, output_bytes=None,
            source_scan_bytes=None, wall_time_seconds=None))) for task in protocol_fixture.execution_plan.tasks))
    assert selected_execution_resource_budgets(plan, None) == tuple(task.capability.requested_resources for task in plan.tasks)


def _scheduler(tmp_path, protocol, plan, spec, *, workers, capacity, executor):
    plane = _plane(tmp_path)
    engine = create_catalog_engine("sqlite+pysqlite:///" + str(tmp_path / "catalog.sqlite3"))
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    recovery = ExternalRunRecoveryStore(plane)
    index = RunRecoveryIndex.from_execution_plan(plan, run_id=plan.source_plan.object_id,
        wave_id="wave.finite-software", authority_identities=(protocol.run_plan.authorization,))
    store = _ResourceEnvelopeStore()
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    envelope_id = "resource-envelope.finite-software"
    coordinator.ensure_initialized(envelope_id=envelope_id, spec=spec,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        jit_graph_signature_manifest=plan.jit_graph_signature_manifest)
    runners = RunnerRegistry(tuple(DeterministicRunner(manifest) for manifest in protocol.registry.capabilities),
        registry_sha256=plan.registry_sha256)
    scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane,
        receipt_store=ExternalTaskReceiptStore(plane), recovery_index=index, recovery_store=recovery,
        runner_registry=runners, implementation_commit=plan.implementation_commit,
        external_input_resolver=_external_inputs(plane, plan), input_port_factory=plane,
        executor=executor, maximum_parallel_tasks=workers, parallel_resource_capacity=capacity,
        execution_resource_envelope_coordinator=coordinator, execution_resource_envelope_id=envelope_id)
    return scheduler, repository, coordinator, envelope_id


@pytest.mark.parametrize("mode", ("sealed-worker-limit", "serial-memory", "serial-cpu"))
def test_refusal_precedes_reservation_attempt_callbacks_and_worker_entry(tmp_path, protocol_fixture, monkeypatch, mode):
    workers = min(4, len(os.sched_getaffinity(0))) if mode == "sealed-worker-limit" else 1
    plan, spec = _selected_plan(protocol_fixture, workers=1, cpu_cores=2 if mode == "serial-cpu" else 1)
    memory = 1 if mode == "serial-memory" or mode == "sealed-worker-limit" and workers == 1 else 10_000_000
    capacity = ExecutionResourceCapacity(workers, memory, 0, True, True, False)
    calls = []

    class NeverExecute:
        def execute(self, *_args, **_kwargs):
            calls.append("worker")
            raise AssertionError("capacity refusal entered worker")

        execute_deadline_free = execute

    scheduler, repository, coordinator, envelope_id = _scheduler(tmp_path, protocol_fixture, plan, spec,
        workers=workers, capacity=capacity, executor=NeverExecute())
    before = coordinator.current(envelope_id)
    snapshot = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    original_start = repository.start_attempt

    def start(*args, **kwargs):
        calls.append("attempt")
        return original_start(*args, **kwargs)

    monkeypatch.setattr(repository, "start_attempt", start)
    monkeypatch.setattr(scheduler, "_execute_runner", lambda *_args, **_kwargs: calls.append("parent-preparation"))
    try:
        with pytest.raises(ResourceAdmissionError):
            scheduler.execute(plan.source_plan.object_id, plan)
        assert calls == [] and coordinator.current(envelope_id) == before
        assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == snapshot
    finally:
        repository.engine.dispose()


def test_selected_aggregate_memory_limits_parallel_batch_and_refills(tmp_path, protocol_fixture):
    workers = min(4, len(os.sched_getaffinity(0)))
    plan, spec = _selected_plan(protocol_fixture, workers=workers, aggregate_slots=2)
    task_memory = spec.task_cells[0].resource_budget.memory_bytes
    lock, slow_started, third_started = threading.Lock(), threading.Event(), threading.Event()
    active, peak, affinities = set(), [0], {}

    class Observed:
        def execute_deadline_free(self, runner, context, **_kwargs):
            with lock:
                active.add(context.task_id)
                peak[0] = max(peak[0], len(active))
                affinities[context.task_id] = context.cpu_affinity
            try:
                if workers > 1:
                    if context.task_id.endswith(".0"):
                        assert slow_started.wait(10)
                    elif context.task_id.endswith(".1"):
                        slow_started.set()
                        assert third_started.wait(10), "memory slot was not refilled after the first task settled"
                    elif context.task_id.endswith(".2"):
                        third_started.set()
                return runner.execute(context)
            finally:
                with lock:
                    active.remove(context.task_id)

    capacity = ExecutionResourceCapacity(workers, 4 * task_memory, 0, True, True, False)
    scheduler, repository, coordinator, envelope_id = _scheduler(tmp_path, protocol_fixture, plan, spec,
        workers=workers, capacity=capacity, executor=Observed())
    try:
        result = scheduler.execute(plan.source_plan.object_id, plan)
        assert result.status.value == "SUCCEEDED" and len(result.receipts) == 4
        assert peak[0] == min(workers, 2)
        assert set(affinities) == {task.task_id for task in plan.tasks}
        if workers > 1:
            assert all(len(value) == 1 for value in affinities.values())
            assert not set(affinities["finite-ready.0"]).intersection(affinities["finite-ready.1"])
        else:
            assert all(value == () for value in affinities.values())
        assert all(cell.state.value == "TERMINAL" for cell in coordinator.current(envelope_id).cells)
    finally:
        repository.engine.dispose()


def _service_for_admission():
    service = object.__new__(CampaignExecutionService)
    service.maximum_parallel_tasks = 4
    service.resource_admitter = LocalExecutionResourceAdmitter(ExecutionResourceCapacity(4, 64 * 1024**3, 0, True, True, False))
    service.artifact_plane = SimpleNamespace(root=SimpleNamespace(diagnostic=lambda **_kwargs: SimpleNamespace(observed_free_bytes=1024**3)))
    service.executor = DirectTaskExecutor()
    service.execution_assurance_profile = ExecutionAssuranceProfile.TRUSTED_LOCAL
    return service


def test_api_preview_reports_sealed_limit_and_execute_refuses_before_preparation(tmp_path, monkeypatch):
    fixture = build_issued_study_fixture(tmp_path)
    package = _execution_package_fixture(fixture, native_simulator=False, jit=False)
    run, plan = _compile(fixture, package)
    service = _service_for_admission()
    calls = []
    monkeypatch.setattr(service, "_check_identity", lambda *_args, **_kwargs: None)
    for method in ("preexecution_contract_closure", "_execute_plan", "_worker_preparation_arguments", "_persist_plans"):
        monkeypatch.setattr(service, method, lambda *_args, **_kwargs: calls.append("effect-or-preparation"))
    admission = service.resource_admission(plan, package=package)
    assert not admission.admitted and "ISSUED_PARALLEL_LIMIT_EXCEEDED" in admission.reason_codes
    with pytest.raises(CampaignPrerequisiteError, match="ISSUED_PARALLEL_LIMIT_EXCEEDED"):
        service.execute(package=package, run_plan=run, execution_plan=plan)
    assert calls == []
    api = object.__new__(EmpiricalLawhoodApi)
    api._execution_service = service
    monkeypatch.setattr(api, "_compile_path", lambda _path: (package, run, plan))
    monkeypatch.setattr(api, "_conditional_execution_records", lambda **_kwargs: ((), ()))
    monkeypatch.setattr(api, "_storage_diagnostic", lambda **_kwargs: (None, ()))
    monkeypatch.setattr(service, "preexecution_contract_closure", lambda **_kwargs: SimpleNamespace(passed=True))
    monkeypatch.setattr(service, "write_effects", lambda _run: ())
    report = api.run_campaign(RunCampaignRequest(Path("/unread/software-capacity-package.json")))
    assert report.status.value == "BLOCKED"
    assert "ISSUED_PARALLEL_LIMIT_EXCEEDED" in report.payload.execution_resource_reason_codes
    assert calls == []
    first = package.execution_resource_envelope_spec.task_cells[0]
    changed = replace(package.execution_resource_envelope_spec,
        aggregate_memory_ceiling_bytes=package.execution_resource_envelope_spec.aggregate_memory_ceiling_bytes + 1,
        task_cells=(replace(first,
        resource_budget=replace(first.resource_budget, memory_bytes=first.resource_budget.memory_bytes + 1)),
        *package.execution_resource_envelope_spec.task_cells[1:]))
    mismatched = replace(package, execution_resource_envelope_spec=changed)
    with pytest.raises(CampaignValidationError, match="resource contract"):
        service.resource_admission(plan, package=mismatched)
    monkeypatch.setattr(api, "_compile_path", lambda _path: (mismatched, run, plan))
    invalid = api.run_campaign(RunCampaignRequest(Path("/unread/software-capacity-package.json")))
    assert invalid.status.value == "INVALID"
    assert invalid.errors[0].category.value == "VALIDATION" and calls == []

    # These are source/resource selection controls, not a fabricated retained
    # failure, retry grant or executable continuation authority.
