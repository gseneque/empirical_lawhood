# SPDX-License-Identifier: MPL-2.0
"""Complete exposed scratch-repair custody and resource refusal controls."""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import development_scratch_repair as owner
from empirical_lawhood.api.development_output_repair import select_development_output_repair
from empirical_lawhood.api.recursive_execution import _custody_control_pins
from empirical_lawhood.execution.development_scratch_repair import DevelopmentScratchRepair, DevelopmentScratchRepairRecoveryIndex
from empirical_lawhood.execution.execution import OperationalFailureClass
from empirical_lawhood.execution.local.execution import TaskScratchIdentityConflict, operational_failure_diagnostic
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.recovery import decode_run_recovery_index, decode_run_recovery_terminal_event
from tests.test_development_output_repair import blocked_case as blocked_case


def _derive(case, monkeypatch, **changes):
    monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **_: (case.original, case.environment))
    monkeypatch.setattr(owner, 'observe_frozen_worker_package_root', lambda *_, **__: '/disclosed/source/src')
    arguments = dict(writer=case.plane, plan=case.plan, predecessor=case.index, original_source=case.original,
        controller=case.controller, owner_instruction_sha256='d' * 64,
        worker_interpreter=case.environment.interpreter_path, worker_source_root='/disclosed/source')
    return owner.derive_development_scratch_repair(**{**arguments, **changes})


@pytest.mark.parametrize('blocked_case', ('scratch', 'scratch-legacy', 'scratch-dependent'), indirect=True)
def test_scratch_repair_preserves_old_attempts_and_executes_only_unfinished_work(blocked_case, monkeypatch):
    case = blocked_case
    before = _custody_control_pins(case.plane, case.index)
    proof, index = _derive(case, monkeypatch)
    assert type(index) is DevelopmentScratchRepairRecoveryIndex
    assert decode_canonical_bytes(proof.canonical_bytes(), DevelopmentScratchRepair, maximum_bytes=None) == proof
    assert decode_run_recovery_index(index.canonical_bytes()) == index
    assert proof.original_controls == before
    assert index.task('source') == case.index.task('source')
    for task in case.plan.tasks:
        assert proof.task(task) is task
    assert index.task('use').attempts[0].attempt_id != case.index.task('use').attempts[0].attempt_id
    assert case.runners[0].calls == 1 and case.runners[1].calls == 0
    owner.publish_development_scratch_repair(writer=case.plane, repair=proof, index=index)
    assert select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert set(result.completed_task_ids) == {task.task_id for task in case.plan.tasks}
        calls = [row.calls for row in case.runners]
        assert case.runners[0].calls == 1
        assert scheduler.execute(case.run.run_plan_id, case.plan).receipts == result.receipts
        assert [row.calls for row in case.runners] == calls
    finally:
        engine.dispose()
    assert before == _custody_control_pins(case.plane, case.index)
    assert case.recovery.read_terminal(case.index) == case.terminal
    assert all(not tuple(case.plane.root.resolve(path, for_write=False).iterdir()) for _, path in proof.refused_scratch_paths)
    assert select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    terminal = case.recovery.read_terminal(index)
    assert decode_run_recovery_terminal_event(terminal.canonical_bytes()) == terminal
    from empirical_lawhood.api.experiment_execution_read import read_development_execution
    report = read_development_execution(directory=case.directory, artifact_writer=case.plane)
    assert report['execution_complete'] and report['status'] == 'SUCCEEDED'
    assert report['operational_scratch_repair']['retained_successful_receipts'] == 1
    assert report['operational_scratch_repair']['retained_refused_attempts'] == 1
    assert report['operational_scratch_repair']['native_effect_authority'] == 'NONE'
    pins = dict((path, (size, digest)) for path, size, digest in _custody_control_pins(case.plane, index))
    assert all(pins[path] == (size, digest) for path, size, digest in before)


@pytest.mark.parametrize('blocked_case', ('scratch',), indirect=True)
@pytest.mark.parametrize('damage', ('missing', 'nonempty', 'symlink', 'output', 'native', 'contact', 'source', 'lock', 'worker'))
def test_scratch_repair_refuses_changed_evidence_effects_and_scientific_source(blocked_case, monkeypatch, damage):
    case = blocked_case
    candidate, = case.index.task('use').attempts
    scratch = case.plane.root.resolve(f'scratch/task-execution/{case.run.run_plan_id}/{candidate.attempt_id}', for_write=False)
    changes = {}
    if damage == 'missing':
        scratch.rmdir()
    elif damage == 'nonempty':
        (scratch / 'partial-result').write_bytes(b'retained output prefix')
    elif damage == 'symlink':
        scratch.rmdir()
        scratch.symlink_to(scratch.parent, target_is_directory=True)
    elif damage == 'output':
        path = case.plane.root.resolve(case.plan.task('use').outputs[0].relative_path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'unreceipted original output')
    elif damage == 'native':
        rows = tuple(replace(row, native_effect=True) if row.selection.capability_key == 'generic.use' else row
            for row in case.registrations)
        monkeypatch.setattr('empirical_lawhood.api.recursive_operations.operation_catalog', lambda: (rows, case.registry, {}))
    elif damage == 'contact':
        monkeypatch.setattr('empirical_lawhood.storage.native_effect_custody.ExternalNativeEffectContactStore.read',
            lambda *_: object())
    elif damage == 'source':
        rows = tuple((name, 'f' * 64 if name.startswith('domains/') else digest)
            for name, digest in case.controller.package_sources)
        changes['controller'] = replace(case.controller, package_sources=rows,
            code_sources_sha256=sha256(canonical_json_bytes(rows)).hexdigest())
    elif damage == 'lock':
        changes['controller'] = replace(case.controller, dependency_lock_sha256='f' * 64)
    else:
        changes['original_source'] = case.controller
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        _derive(case, monkeypatch, **changes)
    assert not case.plane.root.resolve(owner.repair_relative_path(case.index.run_id), for_write=False).exists()


@pytest.mark.parametrize('blocked_case', ('scratch',), indirect=True)
@pytest.mark.parametrize('damage', ('receipt', 'failure', 'terminal', 'new-candidate', 'scratch'))
def test_scratch_repair_rechecks_original_controls_and_empty_scratch_on_reads(blocked_case, monkeypatch, damage):
    case = blocked_case
    proof, index = _derive(case, monkeypatch)
    owner.publish_development_scratch_repair(writer=case.plane, repair=proof, index=index)
    if damage == 'receipt':
        relative = case.index.task('source').attempts[0].receipt_relative_path
    elif damage == 'failure':
        relative = case.index.task('use').attempts[0].event_relative_path
    elif damage == 'terminal':
        relative = case.index.terminal_event_relative_path
    elif damage == 'new-candidate':
        relative = case.index.task('source').nonattempt_event_relative_path
    else:
        relative = proof.refused_scratch_paths[0][1] + '/later-output'
    path = case.plane.root.resolve(relative, for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'{}\n')
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index)


@pytest.mark.parametrize('blocked_case', ('scratch',), indirect=True)
def test_scratch_repair_retains_final_control_checks_when_scratch_check_raises(blocked_case, monkeypatch):
    case = blocked_case
    seen = []
    original = _custody_control_pins
    monkeypatch.setattr('empirical_lawhood.api.recursive_execution._custody_control_pins',
        lambda *args: seen.append('controls') or original(*args))
    monkeypatch.setattr(owner, '_empty_scratch', lambda *args: (_ for _ in ()).throw(PermissionError('changed scratch')))
    with pytest.raises(PermissionError, match='changed scratch'):
        _derive(case, monkeypatch)
    assert seen == ['controls', 'controls']


def test_retained_scratch_diagnostic_identifies_the_boundary_without_retry_authority():
    diagnostic = operational_failure_diagnostic(TaskScratchIdentityConflict('untrusted arbitrary details'))
    assert diagnostic.failure_class is OperationalFailureClass.RESOURCE_REFUSAL
    assert not diagnostic.retryable and not diagnostic.scientific_evidence
    assert diagnostic.sanitized_exception_type == 'TaskScratchIdentityConflict'
    assert diagnostic.sanitized_message == (
        'task scratch identity already exists; preserve the original attempt and inspect explicit repair')


def test_worker_package_observation_requires_the_exact_selected_checkout(tmp_path, monkeypatch):
    from empirical_lawhood.api import retained_e3_control_repair as worker_owner
    root = tmp_path / 'worker'
    package = root / 'src'
    package.mkdir(parents=True)
    environment = SimpleNamespace(interpreter_path='/selected/python', prefix='/selected/environment')
    commands = []
    monkeypatch.setattr(worker_owner, 'run_bounded_command', lambda command, **kwargs:
        commands.append(command) or SimpleNamespace(returncode=0, stdout=(str(package) + '\n').encode()))
    assert worker_owner.observe_frozen_worker_package_root(environment, source_root=root) == str(package)
    assert 'empirical_lawhood.execution.local' in commands[0][-1]
    with pytest.raises(PermissionError):
        worker_owner.observe_frozen_worker_package_root(environment)
    with pytest.raises(PermissionError):
        worker_owner.observe_frozen_worker_package_root(environment, source_root=tmp_path)


def test_public_service_selects_scratch_repair_without_changing_task_allowances(tmp_path, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.results import ResumeCampaignRequest
    service = ExperimentProgrammeService(tmp_path, object())
    instruction = tmp_path / 'instruction.txt'
    instruction.write_text('Repair and resume the exposed software computation.\n')
    calls = []
    monkeypatch.setattr(owner, 'recover_development_scratch', lambda **kwargs: calls.append(kwargs) or {'selected': True})
    options = dict(directory=tmp_path, maximum_parallel_tasks=4,
        request=ResumeCampaignRequest('exposed.run', confirmed=True), repair_development_scratch=True,
        worker_interpreter=tmp_path / 'python', worker_source_root=tmp_path / 'source', repair_instruction_path=instruction)
    assert service.recover(**options) == {'selected': True}
    assert len(calls) == 1 and calls[0]['maximum_parallel_tasks'] == 4
    assert calls[0]['owner_instruction_sha256'] == sha256(instruction.read_bytes()).hexdigest()
    assert 'output_bytes' not in calls[0]
    for changed in ({'repair_development_output_bytes': 4096}, {'repair_development_controller': True},
            {'request': ResumeCampaignRequest('exposed.run', confirmed=False)}, {'worker_interpreter': None}):
        with pytest.raises(ValueError):
            service.recover(**{**options, **changed})
    assert len(calls) == 1


def test_public_cli_selects_exactly_one_scratch_repair_with_original_worker(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.cli import integrations
    from empirical_lawhood.cli.app import app
    monkeypatch.setattr(integrations, '_storage', lambda: (tmp_path, None, object()))
    calls = []
    monkeypatch.setattr(ExperimentProgrammeService, 'recover',
        lambda self, **kwargs: calls.append(kwargs) or {'status': 'SELECTED'})
    instruction = tmp_path / 'instruction.txt'
    instruction.write_text('Repair the disclosed PURE scratch refusal.\n')
    command = ['--no-progress', 'campaign', 'experiment-recover', '--authoring-dir', str(tmp_path),
        '--run', 'run.disclosed', '--yes', '--repair-development-scratch', '--workers', '4',
        '--worker-interpreter', '/disclosed/worker/bin/python', '--worker-source-root', '/disclosed/source',
        '--repair-instruction', str(instruction)]
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 0, result.output
    selected, = calls
    assert selected['repair_development_scratch'] is True and selected['maximum_parallel_tasks'] == 4
    assert selected['request'].run_id == 'run.disclosed' and selected['request'].confirmed
    assert 'repair_development_output_bytes' not in selected
    for altered in ([part for part in command if part != '--yes'],
            [*command, '--repair-development-output-bytes', '4096']):
        refused = CliRunner().invoke(app, altered)
        assert refused.exit_code != 0 and len(calls) == 1
