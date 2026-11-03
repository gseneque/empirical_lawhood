# SPDX-License-Identifier: MPL-2.0
"""Exposed controller handoff; no scientific qualification or native acquisition."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.api import development_controller_repair as owner
from empirical_lawhood.api.recursive_execution import _custody_control_pins
from empirical_lawhood.infrastructure.recovery import decode_run_recovery_index, decode_run_recovery_terminal_event
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepair, DevelopmentControllerRepairRecoveryIndex
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from tests.test_development_output_repair import blocked_case as blocked_case


def _derive(case, monkeypatch, **changes):
    monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **_: (case.original, case.environment))
    values = dict(writer=case.plane, plan=case.plan, predecessor=case.index, original_source=case.original,
        controller=case.controller, owner_instruction_sha256='d' * 64, output_bytes=4096,
        worker_interpreter=case.environment.interpreter_path, worker_source_root='/disclosed/source')
    return owner.derive_development_controller_repair(**{**values, **changes})


def test_controller_repair_keeps_original_receipts_failures_and_complete_census(blocked_case, monkeypatch):
    case = blocked_case
    before = _custody_control_pins(case.plane, case.index)
    proof, index = _derive(case, monkeypatch)
    assert type(index) is DevelopmentControllerRepairRecoveryIndex
    assert proof.original_controls == before
    assert proof.output_task_ids == ('use',)
    assert decode_canonical_bytes(proof.canonical_bytes(), DevelopmentControllerRepair, maximum_bytes=None) == proof
    assert decode_run_recovery_index(index.canonical_bytes()) == index
    assert index.task('source') == case.index.task('source')
    assert index.task('use').attempts[0].attempt_id != case.index.task('use').attempts[0].attempt_id
    owner.publish_development_controller_repair(writer=case.plane, repair=proof, index=index)
    from empirical_lawhood.api.development_output_repair import select_development_output_repair
    assert select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert [runner.calls for runner in case.runners] == [1, 2]
        assert scheduler.execute(case.run.run_plan_id, case.plan).receipts == result.receipts
        assert [runner.calls for runner in case.runners] == [1, 2]
    finally:
        engine.dispose()
    terminal = case.recovery.read_terminal(index)
    assert decode_run_recovery_terminal_event(terminal.canonical_bytes()) == terminal
    assert before == _custody_control_pins(case.plane, case.index)
    assert case.recovery.read_terminal(case.index) == case.terminal
    assert select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    from empirical_lawhood.api.experiment_execution_read import read_development_execution
    report = read_development_execution(directory=case.directory, artifact_writer=case.plane)
    assert report['execution_complete'] and report['status'] == 'SUCCEEDED'
    assert report['operational_controller_repair']['retained_successful_receipts'] == 1
    assert report['operational_controller_repair']['native_acquisition_scope'] == 'ORIGINAL_UNCONTACTED_TASKS_ONLY'
    assert report['scientific_completion'] == 'DEFERRED_TO_FULL_READ'


@pytest.mark.parametrize('damage', ('ceiling', 'no-increase', 'worker', 'science', 'lock', 'native-failure', 'contact', 'output'))
def test_controller_repair_refuses_unsafe_original_work_or_changed_science(blocked_case, monkeypatch, damage):
    case = blocked_case
    changes = {}
    if damage == 'ceiling':
        changes['output_bytes'] = 20_000
    elif damage == 'no-increase':
        changes['output_bytes'] = 160
    elif damage == 'worker':
        changes['original_source'] = case.controller
    elif damage == 'lock':
        changes['controller'] = replace(case.controller, dependency_lock_sha256='e' * 64)
    elif damage == 'science':
        rows = tuple((name, 'e' * 64 if name.startswith('kernel/') else digest)
            for name, digest in case.controller.package_sources)
        changes['controller'] = replace(case.controller, package_sources=rows,
            code_sources_sha256=sha256(canonical_json_bytes(rows)).hexdigest())
    elif damage == 'native-failure':
        rows = tuple(replace(row, native_effect=True) if row.selection.capability_key == 'generic.use' else row
            for row in case.registrations)
        monkeypatch.setattr('empirical_lawhood.api.recursive_operations.operation_catalog', lambda: (rows, case.registry, {}))
    elif damage == 'contact':
        task = case.plan.task('use')
        contact = NativeEffectContact(case.run.run_plan_id, task.task_id, case.index.task(task.task_id).attempts[0].attempt_id,
            owner._pin(case.plan, 'execution_plan_id'), owner._pin(task, 'task_id'), case.plan.implementation_commit, (), ())
        owner._contacts(case.plane, case.plan).begin(contact)
    else:
        path = case.plane.root.resolve(case.plan.task('use').outputs[0].relative_path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'unreceipted exposed output')
    with pytest.raises((ValueError, PermissionError)):
        _derive(case, monkeypatch, **changes)
    assert not case.plane.root.resolve(owner.repair_relative_path(case.index.run_id), for_write=False).exists()


@pytest.mark.parametrize('damage', ('receipt', 'failed-event', 'terminal', 'missing-candidate'))
def test_controller_repair_reader_authenticates_original_control_census(blocked_case, monkeypatch, damage):
    case = blocked_case
    proof, index = _derive(case, monkeypatch)
    owner.publish_development_controller_repair(writer=case.plane, repair=proof, index=index)
    if damage == 'receipt':
        relative = case.index.task('source').attempts[0].receipt_relative_path
    elif damage == 'failed-event':
        relative = case.index.task('use').attempts[0].event_relative_path
    elif damage == 'terminal':
        relative = case.index.terminal_event_relative_path
    else:
        relative = case.index.task('source').nonattempt_event_relative_path
    path = case.plane.root.resolve(relative, for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'{}\n')
    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        owner.select_development_controller_repair(writer=case.plane, plan=case.plan, predecessor=case.index)


@pytest.mark.parametrize('blocked_case', ('dependent',), indirect=True)
def test_controller_repair_includes_unstarted_tasks_without_replacing_original_plan(blocked_case, monkeypatch):
    case = blocked_case
    proof, index = _derive(case, monkeypatch)
    assert proof.pending_task_ids == ('tail',)
    assert proof.output_task_ids == ('use',)  # The tail already has a larger original reservation.
    assert proof.task(case.plan.task('tail')) is case.plan.task('tail')
    assert index.task('tail').attempts[0].attempt_id != case.index.task('tail').attempts[0].attempt_id
    assert proof.execution_plan == ObjectIdentity.from_record(case.plan.execution_plan_id, case.plan)


@pytest.mark.parametrize('blocked_case', ('native-dependent',), indirect=True)
def test_controller_repair_enters_only_original_uncontacted_native_task_once(blocked_case, monkeypatch):
    from empirical_lawhood.runtime.artifacts import ReceiptCheck
    from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
    from tests.runtime_platform.test_recursive_compiler import Config
    case = blocked_case
    contacts = owner._contacts(case.plane, case.plan)
    original_contact = contacts.read(case.run.run_plan_id, 'source')
    assert original_contact is not None and contacts.read(case.run.run_plan_id, 'tail') is None
    proof, index = _derive(case, monkeypatch)
    assert proof.uncontacted_native_task_ids == ('tail',)
    assert proof.completed_native_contacts == (('source', ObjectIdentity.from_record('source', original_contact)),)
    assert proof.task(case.plan.task('tail')) is case.plan.task('tail')
    calls = []
    def tail(context):
        calls.append(context.task_id)
        operand, = [decode_canonical_bytes(port.read(), Config, maximum_bytes=10_000)
            for port in context.input_ports if port.kind is WorkerInputKind.DEPENDENCY]
        assert operand.scalar == 4
        value = Config('product.tail', 5).canonical_bytes()
        return RunnerResult(tuple(TaskOutputPayload(port.output_id, value) for port in context.output_ports),
            (ReceiptCheck('exposed-native-control', True, ()),))
    monkeypatch.setattr(next(row for row in case.runners if row.manifest.capability_key == 'generic.tail'), 'execute', tail)
    owner.publish_development_controller_repair(writer=case.plane, repair=proof, index=index)
    before = _custody_control_pins(case.plane, case.index)
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert scheduler.execute(case.run.run_plan_id, case.plan).receipts == result.receipts
    finally:
        engine.dispose()
    assert calls == ['tail']
    assert contacts.read(case.run.run_plan_id, 'source') == original_contact
    entered = contacts.read(case.run.run_plan_id, 'tail')
    assert entered.attempt_id == index.task('tail').attempts[0].attempt_id
    assert entered.attempt_id != case.index.task('tail').attempts[0].attempt_id
    assert before == _custody_control_pins(case.plane, case.index)
    assert owner.select_development_controller_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index


def test_controller_repair_can_bind_a_real_interruption_without_inventing_a_terminal(blocked_case, monkeypatch):
    case = blocked_case
    # An exposed fixture with retained receipt/failure and an absent final
    # publication models the controller's SIGINT drain boundary.
    for suffix in ('', '.manifest.json'):
        case.plane.root.resolve(case.index.terminal_event_relative_path + suffix, for_write=False).unlink()
    proof, index = _derive(case, monkeypatch)
    assert proof.original_terminal is None
    owner.publish_development_controller_repair(writer=case.plane, repair=proof, index=index)
    assert owner.select_development_controller_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
    finally:
        engine.dispose()
    assert result.status is OperationalStatus.SUCCEEDED
    assert case.recovery.read_terminal(case.index) is None
    assert [runner.calls for runner in case.runners] == [1, 2]


@pytest.mark.parametrize('changed', ('controller', 'environment'))
def test_controller_repair_rechecks_both_live_installations(blocked_case, monkeypatch, changed):
    case = blocked_case
    proof, index = _derive(case, monkeypatch)
    monkeypatch.setattr(owner, 'observe_frozen_worker_package_root', lambda _: '/disclosed/package')
    assert owner.authenticate_controller(index=index, source=case.original, controller=case.controller) == '/disclosed/package'
    current = case.controller
    if changed == 'controller':
        current = replace(current, observed_git_head='3' * 40)
    else:
        monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **_: (case.original,
            replace(case.environment, interpreter_path='/different/python')))
    with pytest.raises(PermissionError):
        owner.authenticate_controller(index=index, source=case.original, controller=current)


def test_public_recovery_explicitly_selects_the_interrupted_controller_owner(tmp_path, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.results import ResumeCampaignRequest
    service = ExperimentProgrammeService(tmp_path, object())
    instruction = tmp_path/'instruction.txt'
    instruction.write_text('Disclosed software repair request, no scientific authority.\n')
    calls = []
    monkeypatch.setattr(owner, 'recover_development_controller', lambda **kwargs: calls.append(kwargs) or {'selected': True})
    result = service.recover(directory=tmp_path, maximum_parallel_tasks=8,
        request=ResumeCampaignRequest('exposed.run', confirmed=True), repair_development_controller=True,
        repair_development_output_bytes=4096, worker_interpreter=tmp_path/'python',
        worker_source_root=tmp_path/'source', repair_instruction_path=instruction)
    assert result == {'selected': True} and len(calls) == 1
    assert calls[0]['maximum_parallel_tasks'] == 8 and calls[0]['output_bytes'] == 4096
    assert calls[0]['owner_instruction_sha256'] == sha256(instruction.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='explicit PURE output allowance'):
        service.recover(directory=tmp_path, repair_development_controller=True)
