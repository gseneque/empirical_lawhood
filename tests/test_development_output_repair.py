# SPDX-License-Identifier: MPL-2.0
"""Exposed PURE recovery controls; no native acquisition or qualification."""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import development_output_repair as owner
from empirical_lawhood.api.recursive_execution import _custody_control_pins, _external_inputs
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler, _return_nonstreaming_result
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore, decode_run_recovery_index, decode_run_recovery_terminal_event
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputBudgetRepair, DevelopmentOutputRepairRecoveryIndex
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
from empirical_lawhood.runtime.plans import PlanLane
from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryEvent
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
from tests.runtime_platform.test_recursive_compiler import Config, UseConfig, fixture
from tests.runtime_platform.test_unlimited_recursive_execution import _ExposedOperandRunner
from tests.test_recursive_public_service import ROOT, _plane


class _OutputBoundaryExecutor(DirectTaskExecutor):
    def execute(self, runner, context, *, timeout_seconds):
        result = super().execute(runner, context, timeout_seconds=timeout_seconds)
        # Use the real child transport guard with an inert small-message sink.
        _return_nonstreaming_result(SimpleNamespace(send=lambda value: None), context, result)
        return result


class _DualOutputRunner(_ExposedOperandRunner):
    def execute(self, context):
        from empirical_lawhood.runtime.execution import TaskOutputPayload
        result = super().execute(context)
        payload = result.outputs[0].payload
        return replace(result, outputs=tuple(TaskOutputPayload(port.output_id, payload) for port in context.output_ports))


def _sources():
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import NUMERICAL_OWNER_PREFIXES
    names = tuple(sorted({*(prefix + 'exposed.py' if prefix.endswith(('/', '_')) else prefix
        for prefix in NUMERICAL_OWNER_PREFIXES), 'kernel/exposed.py', 'api/exposed.py'}))
    def source(head):
        rows = tuple((name, head * 64 if name == 'api/exposed.py' else 'a' * 64) for name in names)
        return RecursiveImplementationBinding(rows, sha256(canonical_json_bytes(rows)).hexdigest(), 'b' * 64, head * 40, True)
    return source('1'), source('2')


@pytest.fixture
def blocked_case(tmp_path, monkeypatch, request):
    draft, registrations, registry = fixture()
    mode = getattr(request, 'param', None)
    # Each output fits the frozen 160-byte edge; their combined buffer does not.
    # This reproduces the demonstrated duplicate-score allocation boundary.
    declaration = registrations[1]
    registrations = (registrations[0], replace(declaration,
        outputs=(*declaration.outputs, replace(declaration.outputs[0], output_id='second'))))
    if mode in ('dependent', 'native-dependent'):
        from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
        required = replace(draft.requirements[0], requirement_id='requirement.tail',
            consumer_operation_id='tail', assessment_operation_id='tail')
        connection = replace(draft.connections[0], connection_id='connection.tail',
            requirement_id=required.requirement_id, supplier_operation_id='use', assessment_operation_id='tail')
        link = replace(draft.links[0], edge_id='edge.tail', consumer_node_id='tail', producer_node_id='use',
            requirement_id=required.requirement_id, connection_id=connection.connection_id)
        tail = registrations[1]
        if mode == 'native-dependent':
            native = dict(native_effect=True, scientific_unit_ids=lambda config: ('unit.one',),
                native_effect_slot_ids=lambda config: ('exposed.slot.' + config.config_id,))
            tail = replace(tail, selection=replace(tail.selection, capability_key='generic.tail'), **native)
            registrations = (replace(registrations[0], **native), registrations[1], tail)
            registry = replace(registry, capabilities=tuple(sorted((*registry.capabilities,
                replace(registry.capabilities[1], capability_key='generic.tail')), key=lambda row: row.registry_id)))
        operation = RecursiveOperationSpec.from_config(node_id='tail', selection=tail.selection,
            config_id='config.tail', config=UseConfig('config.tail', 3), obligation_ids=('obligation.tail',),
            resource_budget=registrations[1].resource_ceiling)
        draft = replace(draft, requirements=(*draft.requirements, required), connections=(*draft.connections, connection),
            links=(*draft.links, link), operations=tuple(sorted((*draft.operations, operation), key=lambda row: row.node_id)),
            selected_operation_ids=('source', 'tail', 'use'))
    draft = replace(draft, operations=tuple(replace(row, resource_budget=replace(row.resource_budget, output_bytes=160))
        if row.node_id == 'use' else row for row in draft.operations))
    original, controller = _sources()
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api.recursive_execution import _retained_plans
    def catalog():
        return registrations, registry, {Config.SCHEMA: Config}
    monkeypatch.setattr('empirical_lawhood.api.recursive_operations.operation_catalog', catalog)
    monkeypatch.setattr(author, 'operation_catalog', catalog)
    monkeypatch.setattr(author, 'implementation_binding', lambda *args, **kwargs: original)
    plane = _plane(tmp_path / 'pure-output-repair')
    directory = tmp_path / 'pure-output-repair/authored'
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory)
    packet, draft, _, payloads = author.load_authored_wave(directory=directory, artifact_writer=plane, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft,
        payloads=payloads, read_only=False)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.development', authority_identities=())
    recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
    runners = tuple(_DualOutputRunner(manifest) for manifest in registry.capabilities)
    native_keys = tuple(sorted(row.selection.capability_key for row in registrations if row.native_effect))
    if native_keys:
        from empirical_lawhood.api.development_controller_repair import _contacts
        contacts = _contacts(plane, plan)
    else:
        contacts = None
    def scheduler(selected):
        engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
        upgrade_catalog(engine)
        return engine, LocalScheduler(operational_repository=SQLiteOperationalRepository(engine), artifact_writer=plane,
            receipt_store=receipts, recovery_index=selected, recovery_store=recovery,
            runner_registry=RunnerRegistry(runners, registry_sha256=registry.fingerprint()),
            implementation_commit='1' * 40, external_input_resolver=StaticExternalInputResolver(inputs),
            executor=_OutputBoundaryExecutor(), input_port_factory=plane, lane=PlanLane.DEVELOPMENT,
            authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
            native_effect_contact_store=contacts, native_effect_capability_keys=native_keys)
    engine, original_scheduler = scheduler(index)
    try:
        result = original_scheduler.execute(run.run_plan_id, plan)
    finally:
        engine.dispose()
    assert result.status is OperationalStatus.BLOCKED
    assert result.completed_task_ids == ('source',)
    terminal = recovery.read_terminal(index)
    assert terminal.blocked_task_ids == (('tail', 'use') if mode in ('dependent', 'native-dependent') else ('use',))
    environment = PreparedWorkerEnvironment('/disclosed/python', 'c' * 64, '/disclosed/environment', ())
    monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **kwargs: (original, environment))
    return SimpleNamespace(plan=plan, run=run, plane=plane, index=index, recovery=recovery, receipts=receipts,
        runners=runners, scheduler=scheduler, original=original, controller=controller, environment=environment,
        registrations=registrations, registry=registry, result=result, terminal=terminal, directory=directory, packet=packet)


def _derive(case, **changes):
    values = dict(writer=case.plane, plan=case.plan, predecessor=case.index, original_source=case.original,
        controller=case.controller, owner_instruction_sha256='d' * 64, output_bytes=4096,
        worker_interpreter=case.environment.interpreter_path, worker_source_root='/disclosed/source')
    return owner.derive_development_output_repair(**{**values, **changes})


def test_pure_output_repair_completes_without_repeating_source_or_replacing_failure(blocked_case):
    case = blocked_case
    before = _custody_control_pins(case.plane, case.index)
    proof, index = _derive(case)
    assert type(index) is DevelopmentOutputRepairRecoveryIndex
    assert decode_canonical_bytes(proof.canonical_bytes(), DevelopmentOutputBudgetRepair, maximum_bytes=None) == proof
    assert decode_run_recovery_index(index.canonical_bytes()) == index
    assert index.task('source') == case.index.task('source')
    receipt, = case.result.receipts
    assert TaskRecoveryEvent.from_receipt(index, receipt) == TaskRecoveryEvent.from_receipt(case.index, receipt)
    original_task = case.plan.task('use')
    projected = proof.task(original_task)
    assert projected.capability.requested_resources.output_bytes == 4096
    assert replace(projected, capability=replace(projected.capability,
        requested_resources=original_task.capability.requested_resources)) == original_task
    owner.publish_development_output_repair(writer=case.plane, repair=proof, index=index)
    assert owner.select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert result.completed_task_ids == ('source', 'use')
        assert case.runners[0].calls == 1
        assert case.runners[1].calls == 2
        assert scheduler.execute(case.run.run_plan_id, case.plan).receipts == result.receipts
        assert [runner.calls for runner in case.runners] == [1, 2]
    finally:
        engine.dispose()
    assert before == _custody_control_pins(case.plane, case.index)
    terminal = case.recovery.read_terminal(index)
    assert decode_run_recovery_terminal_event(terminal.canonical_bytes()) == terminal
    assert terminal.operational_status == 'SUCCEEDED'
    assert case.recovery.read_terminal(case.index) == case.terminal
    assert owner.select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    assert owner.repair_report(index)['operational_output_budget_repair']['native_acquisition_authority'] == 'NONE'
    from empirical_lawhood.api.experiment_execution_read import read_development_execution
    report = read_development_execution(directory=case.directory, artifact_writer=case.plane)
    assert report['execution_complete'] and report['status'] == 'SUCCEEDED'
    assert report['terminal'] == owner._pin(terminal, 'terminal_event_id').to_document()
    assert report['operational_output_budget_repair']['original_terminal'] == proof.original_terminal.to_document()
    assert report['scientific_completion'] == 'DEFERRED_TO_FULL_READ'
    pins = dict((path, (size, digest)) for path, size, digest in _custody_control_pins(case.plane, index))
    assert all(pins[path] == (size, digest) for path, size, digest in before)


@pytest.mark.parametrize('damage', ('ceiling', 'no-increase', 'lock', 'science', 'worker', 'native', 'contact', 'output'))
def test_pure_output_repair_refuses_changed_or_uncertain_work(blocked_case, monkeypatch, damage):
    case = blocked_case
    changes = {}
    if damage == 'ceiling':
        changes['output_bytes'] = 20_000
    elif damage == 'no-increase':
        changes['output_bytes'] = 160
    elif damage == 'lock':
        changes['controller'] = replace(case.controller, dependency_lock_sha256='e' * 64)
    elif damage == 'science':
        rows = tuple((name, 'e' * 64 if name.startswith('kernel/') else digest)
            for name, digest in case.controller.package_sources)
        changes['controller'] = replace(case.controller, package_sources=rows,
            code_sources_sha256=sha256(canonical_json_bytes(rows)).hexdigest())
    elif damage == 'worker':
        changes['original_source'] = case.controller
    elif damage == 'native':
        rows = tuple(replace(row, native_effect=True) if row.selection.capability_key == 'generic.use' else row
            for row in case.registrations)
        monkeypatch.setattr('empirical_lawhood.api.recursive_operations.operation_catalog', lambda: (rows, case.registry, {}))
    elif damage == 'contact':
        monkeypatch.setattr('empirical_lawhood.infrastructure.native_effect_custody.ExternalNativeEffectContactStore.read',
            lambda *args: object())
    else:
        path = case.plane.root.resolve(case.plan.task('use').outputs[0].relative_path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'unreceipted disclosed output')
    with pytest.raises((ValueError, PermissionError)):
        _derive(case, **changes)
    assert not case.plane.root.resolve(owner.repair_relative_path(case.index.run_id), for_write=False).exists()


@pytest.mark.parametrize('limit', (0, -1, True, 256 * 1024**2 + 1))
def test_output_repair_requires_positive_finite_allowance(blocked_case, limit):
    with pytest.raises(ValueError):
        _derive(blocked_case, output_bytes=limit)


@pytest.mark.parametrize('blocked_case', ('dependent',), indirect=True)
def test_repair_runs_previously_unstarted_dependency_once(blocked_case, monkeypatch):
    from empirical_lawhood.runtime.artifacts import ReceiptCheck
    from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
    case = blocked_case
    proof, index = _derive(case)
    assert proof.unstarted_task_ids == ('tail',)
    assert index.task('tail').attempts[0].attempt_id != case.index.task('tail').attempts[0].attempt_id
    calls = []
    def followon(context):
        calls.append(context.task_id)
        values = [decode_canonical_bytes(port.read(), Config, maximum_bytes=10_000)
            for port in context.input_ports if port.kind is WorkerInputKind.DEPENDENCY]
        operand, = values
        assert operand.scalar == (3 if context.task_id == 'use' else 4)
        value = Config('product.' + context.task_id, operand.scalar + 1)
        return RunnerResult(tuple(TaskOutputPayload(port.output_id, value.canonical_bytes()) for port in context.output_ports),
            (ReceiptCheck('exposed-tail', True, ()),))
    monkeypatch.setattr(case.runners[1], 'execute', followon)
    before = _custody_control_pins(case.plane, case.index)
    owner.publish_development_output_repair(writer=case.plane, repair=proof, index=index)
    engine, scheduler = case.scheduler(index)
    try:
        result = scheduler.execute(case.run.run_plan_id, case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert calls == ['use', 'tail']
        assert scheduler.execute(case.run.run_plan_id, case.plan).receipts == result.receipts
        assert calls == ['use', 'tail']
    finally:
        engine.dispose()
    assert before == _custody_control_pins(case.plane, case.index)


@pytest.mark.parametrize('damage', ('run', 'confirmation', 'prospective', 'parent', 'reconcile', 'both', 'zero', 'missing-worker'))
def test_public_output_repair_refuses_incompatible_selection_before_custody(tmp_path, monkeypatch, damage):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.results import ResumeCampaignRequest
    service = ExperimentProgrammeService(tmp_path, object())
    request = ResumeCampaignRequest('run.disclosed', confirmed=True)
    options = dict(directory=tmp_path, request=request, repair_development_output_bytes=4096,
        worker_interpreter='/disclosed/python', worker_source_root='/disclosed/source',
        repair_instruction_path=tmp_path / 'missing-instruction')
    if damage == 'run':
        options['request'] = None
    elif damage == 'confirmation':
        options['request'] = replace(request, confirmed=False)
    elif damage == 'prospective':
        options['request'] = replace(request, reveal_authority_id='authority.disclosed')
    elif damage == 'parent':
        options['request'] = replace(request, parent_record_path=tmp_path / 'parent')
    elif damage == 'reconcile':
        options['request'] = replace(request, reconcile_only=True)
    elif damage == 'both':
        options['repair_retained_e3'] = True
    elif damage == 'zero':
        options['repair_development_output_bytes'] = 0
    else:
        options['worker_interpreter'] = None
    monkeypatch.setattr(owner, 'recover_development_output_budget', lambda **kwargs: pytest.fail('invalid selection reached custody'))
    with pytest.raises(ValueError, match='one confirmed development run'):
        service.recover(**options)


def test_repaired_context_keeps_original_task_input_and_current_access_checks(blocked_case, monkeypatch):
    from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
    case = blocked_case
    proof, index = _derive(case)
    owner.publish_development_output_repair(writer=case.plane, repair=proof, index=index)
    custody = CurrentDevelopmentTaskCustody(writer=case.plane, directory=case.directory, plan=case.plan)
    assert custody.index == index
    execute = case.runners[1].execute
    calls = []
    def checked(context):
        _, plan, original = custody.current_task(context, case.runners[1])
        assert plan == case.plan and original == case.plan.task('use')
        assert original.capability.requested_resources.output_bytes == 160
        assert context.resource_budget.output_bytes == 4096
        receipts, controls = custody.task_inputs(context, original)
        assert set(receipts) == {'source'} and controls
        for budget in (replace(context.resource_budget, output_bytes=4097),
                replace(context.resource_budget, memory_bytes=context.resource_budget.memory_bytes + 1)):
            with pytest.raises(PermissionError, match='actual task'):
                custody.current_task(replace(context, resource_budget=budget), case.runners[1])
        def revoked():
            raise PermissionError('disclosed current access revoked')
        monkeypatch.setattr(custody, 'original_input_access', SimpleNamespace(require_current=revoked))
        with pytest.raises(PermissionError, match='current access revoked'):
            custody.current_task(context, case.runners[1])
        monkeypatch.setattr(custody, 'original_input_access', None)
        with pytest.raises(PermissionError, match='cannot enter native'):
            custody.require_native_entry(context, case.runners[1], prepared_contract=None)
        calls.append(context.task_id)
        return execute(context)
    monkeypatch.setattr(case.runners[1], 'execute', checked)
    engine, scheduler = case.scheduler(index)
    try:
        assert scheduler.execute(case.run.run_plan_id, case.plan).status is OperationalStatus.SUCCEEDED
        assert calls == ['use']
    finally:
        engine.dispose()


@pytest.mark.parametrize('changed', ('failure', 'terminal', 'receipt', 'proof', 'index'))
def test_repair_read_authenticates_original_and_additive_control_bytes(blocked_case, changed):
    case = blocked_case
    proof, index = _derive(case)
    owner.publish_development_output_repair(writer=case.plane, repair=proof, index=index)
    paths = {'failure': case.index.task('use').attempts[0].event_relative_path,
        'terminal': case.index.terminal_event_relative_path,
        'receipt': case.index.task('source').attempts[0].receipt_relative_path,
        'proof': owner.repair_relative_path(index.run_id), 'index': index.index_relative_path}
    path = case.plane.root.resolve(paths[changed], for_write=False)
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises((ValueError, RuntimeError, OSError)):
        owner.select_development_output_repair(writer=case.plane, plan=case.plan, predecessor=case.index)


@pytest.mark.parametrize('changed', ('controller', 'worker-source', 'worker-environment'))
def test_repair_controller_rechecks_selected_frozen_worker(blocked_case, monkeypatch, changed):
    case = blocked_case
    _, index = _derive(case)
    controller = case.controller
    if changed == 'controller':
        controller = case.original
    elif changed == 'worker-source':
        monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **kwargs: (case.controller, case.environment))
    else:
        monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **kwargs:
            (case.original, replace(case.environment, interpreter_sha256='f' * 64)))
    with pytest.raises(PermissionError):
        owner.authenticate_repair_controller(index=index, source=case.original, controller=controller)
