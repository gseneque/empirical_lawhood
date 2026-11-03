# SPDX-License-Identifier: MPL-2.0
"""Real controller SIGINT with inert software work and durable receipts."""

import os
import signal
from threading import Event
import time
from dataclasses import replace

import pytest

from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure import execution
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
from empirical_lawhood.runtime.plans import PlanLane
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
from tests.runtime_platform.test_recursive_compiler import Config, fixture
from tests.runtime_platform.test_unlimited_recursive_execution import _ExposedOperandRunner
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize('mode', ('pure', 'native-lease', 'revoked-access'))
def test_controller_sigint_drains_active_receipt_without_starting_its_descendant(tmp_path, monkeypatch, mode):
    draft, registrations, registry = fixture()
    if mode != 'pure':
        registrations = (replace(registrations[0], native_effect=True,
            scientific_unit_ids=lambda config: ('unit.one',),
            native_effect_slot_ids=lambda config: ('exposed.slot',)), registrations[1])
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='1' * 40, output_codecs={Config.SCHEMA: Config})
    run, plan = compiled.run_plan, compiled.execution_plan
    plane = _plane(tmp_path / 'exposed-sigint')
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft,
        payloads={row.config_id: row.payload for row in compiled.config_inputs}, read_only=False)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.exposed-interruption')
    store, recovery = ExternalTaskReceiptStore(plane), ExternalRunRecoveryStore(plane)
    runners = tuple(_ExposedOperandRunner(row) for row in registry.capabilities)
    entered, finish = Event(), Event()
    original = runners[0].execute
    def active(context):
        entered.set()
        assert finish.wait(10), 'controller did not release its active worker'
        if mode != 'pure':
            # Inert work crosses a real attempt lease interval after SIGINT.
            # Exercise the same lease boundary used before a native leaf;
            # this fixture performs no native acquisition.
            time.sleep(3.2)
            scheduler._require_native_entry(context, runners[0], prepared_contract=None)
        return original(context)
    monkeypatch.setattr(runners[0], 'execute', active)
    original_wait = execution.wait
    interrupted = False
    def interrupt_when_waiting(*args, **kwargs):
        nonlocal interrupted
        if interrupted:
            return original_wait(*args, **kwargs)
        assert entered.wait(10), 'controller did not start its first task'
        interrupted = True
        if mode == 'revoked-access':
            def revoked(*args, **kwargs):
                raise PermissionError('exposed current access revoked')
            scheduler.native_entry_guard = revoked
        try:
            os.kill(os.getpid(), signal.SIGINT)
        finally:
            finish.set()
        raise AssertionError('real SIGINT failed to interrupt the controller')
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    try:
        upgrade_catalog(engine)
        repository = SQLiteOperationalRepository(engine)
        contacts = ExternalNativeEffectContactStore(plane=plane,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        scheduler = execution.LocalScheduler(operational_repository=repository, artifact_writer=plane,
            receipt_store=store, recovery_index=index, recovery_store=recovery,
            runner_registry=RunnerRegistry(runners, registry_sha256=registry.fingerprint()),
            implementation_commit='1' * 40, external_input_resolver=StaticExternalInputResolver(inputs),
            executor=execution.DirectTaskExecutor(), input_port_factory=plane, lane=PlanLane.DEVELOPMENT,
            native_effect_contact_store=None if mode == 'pure' else contacts,
            native_effect_capability_keys=tuple(row.selection.capability_key for row in registrations if row.native_effect),
            authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
            maximum_parallel_tasks=2, parallel_resource_capacity=execution.ExecutionResourceCapacity(2, 10_000_000, 0, True, False, False))
        if mode != 'pure':
            scheduler.lease_seconds = 2
        monkeypatch.setattr(execution, 'wait', interrupt_when_waiting)
        with pytest.raises(KeyboardInterrupt):
            scheduler.execute(run.run_plan_id, plan)
        if mode == 'revoked-access':
            assert [row.calls for row in runners] == [0, 0]
            assert contacts.read(run.run_plan_id, 'source') is not None
            assert store.read(run.run_plan_id, 'source', index.task('source').attempts[0].attempt_id) is None
            assert scheduler._native_entry_refusal is not None
            assert recovery.read_terminal(index) is None
            return
        assert [row.calls for row in runners] == [1, 0]
        source = index.task('source').attempts[0]
        receipt = store.read(run.run_plan_id, 'source', source.attempt_id)
        assert receipt is not None and receipt.operational_status is OperationalStatus.SUCCEEDED
        assert recovery.read_terminal(index) is None
        monkeypatch.setattr(execution, 'wait', original_wait)
        result = scheduler.execute(run.run_plan_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert [row.calls for row in runners] == [1, 1]
        assert store.read(run.run_plan_id, 'source', source.attempt_id) == receipt
    finally:
        finish.set()
        engine.dispose()
