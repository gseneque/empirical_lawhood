"""Exposed two-task custody conformance with unlimited local allocations."""

from dataclasses import replace

from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry, RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import PlanLane
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
from tests.runtime_platform.test_recursive_compiler import Config, fixture
from tests.test_recursive_public_service import _plane


class _ExposedOperandRunner:
    def __init__(self, manifest):
        self.manifest = manifest
        self.calls = 0

    def execute(self, context):
        self.calls += 1
        scalar = 3
        for port in context.input_ports:
            payload = port.read()
            if port.kind is WorkerInputKind.DEPENDENCY:
                operand = decode_canonical_bytes(payload, Config, maximum_bytes=None)
                assert operand.scalar == 3
                scalar = operand.scalar + 1
        result = Config("product." + context.task_id, scalar)
        return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                            (ReceiptCheck("exposed-two-task-operand", True, ()),))


def test_unlimited_recursive_dependency_executes_and_recovers_exact_receipt(tmp_path):
    unlimited = ResourceBudget(1, None, 0, None, None, None)
    draft, registrations, registry = fixture()
    draft = replace(draft, campaign=replace(draft.campaign, budget=unlimited), maximum_depth=None,
                    operations=tuple(replace(value, resource_budget=unlimited) for value in draft.operations))
    registrations = tuple(replace(value, resource_ceiling=unlimited,
        input_ports=tuple(replace(port, maximum_size_bytes=None) for port in value.input_ports))
        for value in registrations)
    registry = replace(registry, capabilities=tuple(replace(value, resource_ceiling=unlimited)
                                                    for value in registry.capabilities))
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
                                     implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})
    plan, run = compiled.execution_plan, compiled.run_plan
    edge, = (row for row in next(task for task in plan.tasks if task.task_id == "use").scientific_inputs
        if row.consumer_input_id == "operand")
    assert edge.maximum_size_bytes is None
    assert plan.minimum_free_bytes == 0
    plane = _plane(tmp_path / "unlimited-two-task-custody")
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft,
                             payloads={value.config_id: value.payload for value in compiled.config_inputs}, read_only=False)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
                                                           wave_id="wave.exposed-unlimited", authority_identities=())
    recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    runners = tuple(_ExposedOperandRunner(manifest) for manifest in registry.capabilities)
    scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane,
        receipt_store=receipts, recovery_index=index, recovery_store=recovery,
        runner_registry=RunnerRegistry(runners, registry_sha256=registry.fingerprint()),
        implementation_commit="1" * 40, external_input_resolver=StaticExternalInputResolver(inputs),
        executor=DirectTaskExecutor(), input_port_factory=plane, lane=PlanLane.DEVELOPMENT,
        authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    try:
        result = scheduler.execute(run.run_plan_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert result.completed_task_ids == ("source", "use")
        use = next(receipt for receipt in result.receipts if receipt.task_id == "use")
        raw = (tmp_path / "unlimited-two-task-custody" / use.output_materializations[0].relative_path).read_bytes()
        assert decode_canonical_bytes(raw, Config, maximum_bytes=None).scalar == 4
        replay = scheduler.execute(run.run_plan_id, plan)
        assert replay.receipts == result.receipts
        assert [runner.calls for runner in runners] == [1, 1]
    finally:
        engine.dispose()
