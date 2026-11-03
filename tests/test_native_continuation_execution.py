# SPDX-License-Identifier: MPL-2.0
"""Disclosed literal effects test a separate continuation, never science."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import native_continuation_execution as owner
from empirical_lawhood.api.native_continuation_preparation import _inspect_original
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, LocalScheduler
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore, decode_run_recovery_index, decode_run_recovery_terminal_event
from empirical_lawhood.infrastructure.recursive_custody import read_recursive_products
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuation, native_continuation_scopes
from empirical_lawhood.runtime.native_continuation_proposal import DevelopmentNativeContinuationProposal
from empirical_lawhood.runtime.native_effects import NativeEntryRefused
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, PlanLane
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from tests.runtime_platform.test_execution_scheduler import FixedClock, StaticExternalInputResolver
from tests.runtime_platform.test_native_parent_finalization_scheduler import CurrentParentRunner, _prepared_work
from tests.runtime_platform.test_native_subwork import ExposedInput
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner, _case


def _files(root):
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()}


class _LiteralParentRunner(CurrentParentRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        result = super().execute_with_native_subwork(context, native_subwork, progress)
        return replace(result, outputs=(replace(result.outputs[0], output_id=context.output_ports[0].output_id),))


class _LiteralPureRunner(ExposedReadRunner):
    def execute(self, context):
        result = super().execute(context)
        return replace(result, outputs=(replace(result.outputs[0], output_id=context.output_ports[0].output_id),))


@pytest.fixture
def case(tmp_path, monkeypatch):
    plane, bundle, template, _, contract, _ = _case(tmp_path, actual=True, native=True)
    native = _LiteralParentRunner(template.selected_definitions[0], 'complete')
    native.manifest = replace(native.manifest, resource_ceiling=replace(native.manifest.resource_ceiling, output_bytes=4096))
    pure = _LiteralPureRunner()
    pure.manifest = replace(native.manifest, capability_key='exposed-worker-conformance.pure')
    tasks = []
    for key in ('a.completed', 'b.output-refused', 'c.incomplete', 'd.uncontacted'):
        manifest = pure.manifest if key == 'b.output-refused' else native.manifest
        task = replace(contract.execution_task_record, task_id=key,
            capability=replace(contract.execution_task_record.capability, capability_key=manifest.capability_key,
                requested_resources=replace(manifest.resource_ceiling, output_bytes=1)
                    if key == 'b.output-refused' else manifest.resource_ceiling),
            capability_implementation_sha256=manifest.implementation_sha256,
            outputs=tuple(replace(row, output_id=key + '.' + row.output_id, logical_artifact_id=key + '.' + row.logical_artifact_id,
                relative_path='runs/exposed.run/outputs/' + key + '/' + row.relative_path)
                for row in contract.execution_task_record.outputs))
        tasks.append(task)
    plan = DevelopmentExecutionPlan('exposed.continuation', PlanLane.DEVELOPMENT,
        ObjectIdentity('exposed.run', 'empirical-lawhood/runtime/development-run-plan', '1.0.0', 'b' * 64),
        'a' * 64, contract.implementation.observed_git_head, tuple(tasks), True)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id='exposed.run', wave_id='exposed.original')
    recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
    state = SimpleNamespace(plane=plane, bundle=bundle, plan=plan, index=index, recovery=recovery, receipts=receipts,
        original=contract.implementation, controller=replace(contract.implementation, observed_git_head='2' * 40),
        root=Path(plane.root.contract.canonical_path), entered=[], checks=[], revoked=False)
    def scheduler(selected, *, original=False):
        engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
        upgrade_catalog(engine)
        contacts = owner.ExternalNativeEffectContactStore(plane=plane,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            continuation_scopes=native_continuation_scopes(selected))
        entry_guard = None if original else owner.current_native_entry_guard(selected)
        calls = []
        def guard(*args, **kwargs):
            prepared = kwargs['prepared_contract']
            calls.append(prepared.task_id)
            if original:
                if prepared.task_id == 'c.incomplete' and calls.count(prepared.task_id) == 3:
                    raise PermissionError('disclosed interruption after nested contact')
            else:
                if state.revoked:
                    raise PermissionError('disclosed current permission revoked')
                entry_guard(writer=plane, prepared_contract=prepared)
                state.checks.append(prepared)
            if calls.count(prepared.task_id) == 1:
                state.entered.append((prepared.task_id, prepared.attempt_id))
        result = LocalScheduler(operational_repository=SQLiteOperationalRepository(engine), artifact_writer=plane,
            receipt_store=receipts, recovery_index=selected, recovery_store=recovery,
            runner_registry=RunnerRegistry((native, pure), registry_sha256=plan.registry_sha256),
            implementation_commit=plan.implementation_commit,
            external_input_resolver=StaticExternalInputResolver(bundle.verified_inputs),
            input_port_factory=plane, executor=LocalProcessExecutor(scratch_root=plane.root),
            implementation_binding=contract.implementation, clock=FixedClock(100),
            authorized_barriers=(), lane=PlanLane.DEVELOPMENT,
            assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
            native_effect_contact_store=contacts, native_effect_capability_keys=(native.manifest.capability_key,),
            native_work_preparers={native.manifest.capability_key: _prepared_work}, native_entry_guard=guard)
        return engine, result, contacts
    state.scheduler = scheduler
    engine, initial, contacts = scheduler(index, original=True)
    try:
        with pytest.raises(NativeEntryRefused):
            initial.execute('exposed.run', plan)
    finally:
        engine.dispose()
    parent = contacts.read('exposed.run', 'c.incomplete')
    old_store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent, completed_only=True)
    state.invocation = old_store.read_prepared_invocation(parent)
    state.old_store = old_store
    state.environment = state.invocation.environment
    from empirical_lawhood.api import recursive_operations
    registrations = tuple(SimpleNamespace(selection=task.capability,
        native_effect=task.task_id != 'b.output-refused', resource_ceiling=native.manifest.resource_ceiling)
        for task in (plan.tasks[0], plan.tasks[1]))
    monkeypatch.setattr(recursive_operations, 'operation_catalog', lambda: (
        registrations, SimpleNamespace(fingerprint=lambda: plan.registry_sha256), {}))
    monkeypatch.setattr(owner, 'SUPPORTED_NATIVE_CAPABILITIES', frozenset((native.manifest.capability_key,)))
    monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **k: (state.original, state.environment))
    values = _inspect_original(writer=plane, plan=plan, index=index,
        external_inputs=bundle.verified_inputs, require_access=lambda: None)
    state.proposal = DevelopmentNativeContinuationProposal('proposal.exposed', 'a' * 64, 'exposed.run',
        ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(index.recovery_index_id, index),
        **values, worker=state.original, controller=state.original, worker_environment=state.environment,
        worker_source_root='/disclosed/source', pure_output_bytes=4096)
    state.relative = 'proposals/exposed/proposal.json'
    plane.write(ArtifactWriteRequest(state.proposal.proposal_id, state.relative, state.proposal.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', state.proposal.proposal_id, 'proposals/exposed',
        state.proposal.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    try:
        yield state
    finally:
        bundle.close()


def _derive(state, **changes):
    options = dict(writer=state.plane, plan=state.plan, predecessor=state.index, proposal=state.proposal,
        proposal_relative_path=state.relative, original_source=state.original, controller=state.controller,
        owner_instruction_sha256='c' * 64, external_inputs=state.bundle.verified_inputs, require_access=lambda: None)
    return owner.derive_native_continuation(**{**options, **changes})


def test_separate_continuation_preserves_old_uncertainty_and_completed_work_through_execution_and_read(case, monkeypatch):
    before = _files(case.root)
    proof, index = _derive(case)
    assert decode_canonical_bytes(proof.canonical_bytes(), DevelopmentNativeContinuation, maximum_bytes=None) == proof
    assert decode_run_recovery_index(index.canonical_bytes(), maximum_bytes=None) == index
    assert proof.continued_native_task_ids == ('c.incomplete',)
    assert proof.uncontacted_native_task_ids == ('d.uncontacted',)
    assert proof.output_task_ids == ('b.output-refused',)
    assert index.task('a.completed') == case.index.task('a.completed')
    owner.publish_native_continuation(writer=case.plane, plan=case.plan, proof=proof, index=index)
    assert owner.select_native_continuation(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    engine, scheduler, contacts = case.scheduler(index)
    try:
        result = scheduler.execute('exposed.run', case.plan)
        assert result.status is OperationalStatus.SUCCEEDED
        entered = list(case.entered)
        assert [key for key, _ in entered] == ['a.completed', 'c.incomplete', 'c.incomplete', 'd.uncontacted']
        assert scheduler.execute('exposed.run', case.plan).receipts == result.receipts
        assert case.entered == entered
    finally:
        engine.dispose()
    terminal = case.recovery.read_terminal(index)
    assert decode_run_recovery_terminal_event(terminal.canonical_bytes(), maximum_bytes=None) == terminal
    assert len(terminal.completed_task_ids) == 4
    assert case.recovery.read_terminal(case.index) is None
    assert owner.select_native_continuation(writer=case.plane, plan=case.plan, predecessor=case.index) == index
    old = case.invocation.native_work.definitions[0]
    with case.old_store._completed_reader() as old_reader:
        assert old_reader.inspect(old).state is NativeSubworkState.UNKNOWN_COMPLETION
    after = _files(case.root)
    assert {key: after[key] for key in before} == before
    with case.plane.read_context() as reader:
        products = read_recursive_products(plane=reader, plan=case.plan, index=index,
            external_inputs=case.bundle.verified_inputs, output_codecs={ExposedInput.SCHEMA: ExposedInput}, decode_products=False)
    assert len(products['native_observations']) == 3
    assert all(value.inspections[0].state is NativeSubworkState.COMPLETED
        for value in products['native_observations'].values())
    report = owner.repair_report(index)['operational_native_continuation']
    assert report['additional_independent_observations'] == 0
    assert report['original_incomplete_attempts'][0]['states'] == ['UNKNOWN_COMPLETION']
    assert report['retained_completed_native_tasks'] == 1
    assert report['original_task_count'] == 4 and report['original_native_task_count'] == 3
    guard = owner.current_native_entry_guard(index)
    with monkeypatch.context() as patch:
        patch.setattr(owner, '_read_record', lambda *a, **k: pytest.fail('entry decoded the full immutable selection again'))
        guard(writer=case.plane, prepared_contract=case.checks[0])
        path = case.plane.root.resolve(owner.continuation_relative_path('exposed.run'), for_write=False)
        path.write_bytes(path.read_bytes() + b' ')
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            guard(writer=case.plane, prepared_contract=case.checks[0])


@pytest.mark.parametrize('damage', ('proposal', 'access', 'native-source', 'output', 'original-contact', 'unsupported'))
def test_continuation_refuses_changed_reviewed_selection_before_publication(case, monkeypatch, damage):
    changes = {}
    if damage == 'proposal':
        changes['proposal'] = replace(case.proposal, completed_receipts=(), completed_native_task_ids=())
    elif damage == 'access':
        def revoked():
            raise PermissionError('revoked')
        changes['require_access'] = revoked
    elif damage == 'native-source':
        changes['controller'] = replace(case.controller, dependency_lock_sha256='f' * 64)
    elif damage == 'output':
        path = case.plane.root.resolve(case.plan.task('c.incomplete').outputs[0].relative_path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'disclosed unreceipted output')
    elif damage == 'original-contact':
        path = case.plane.root.resolve(case.old_store.parent_contacts._path('exposed.run', 'c.incomplete'), for_write=False)
        path.write_bytes(path.read_bytes() + b' ')
    else:
        monkeypatch.setattr(owner, 'SUPPORTED_NATIVE_CAPABILITIES', frozenset())
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        _derive(case, **changes)
    assert not case.plane.root.resolve(owner.continuation_relative_path('exposed.run'), for_write=False).exists()


def test_current_entry_still_refuses_revocation_and_original_nested_mutation(case):
    proof, index = _derive(case)
    owner.publish_native_continuation(writer=case.plane, plan=case.plan, proof=proof, index=index)
    case.revoked = True
    before = _files(case.root)
    engine, scheduler, _ = case.scheduler(index)
    try:
        with pytest.raises(NativeEntryRefused):
            scheduler.execute('exposed.run', case.plan)
    finally:
        engine.dispose()
    assert len(case.entered) == 2
    assert {key: _files(case.root)[key] for key in before} == before
    candidate = case.proposal.candidates[0]
    path = case.plane.root.resolve(case.old_store._root(candidate.invocation.native_work.definitions[0]) + '/contact.json', for_write=False)
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        owner.select_native_continuation(writer=case.plane, plan=case.plan, predecessor=case.index)


def _public(case, tmp_path, monkeypatch, *, access=lambda: None):
    from empirical_lawhood.api import recursive_authoring, recursive_execution
    from empirical_lawhood.infrastructure import run_source_admission, source_closure
    monkeypatch.setattr(run_source_admission, '_capture_source', lambda _: object())
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda *a, **k: case.controller)
    monkeypatch.setattr(source_closure, 'require_admitted_target_source_current', lambda *a: None)
    draft = SimpleNamespace(development_study=SimpleNamespace(access_pair=(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)))
    payloads = SimpleNamespace(original_input_access=SimpleNamespace(require_current=access))
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', lambda **k: (None, draft, case.original, payloads))
    monkeypatch.setattr(recursive_execution, '_retained_plans', lambda *a: (SimpleNamespace(run_plan_id='exposed.run'),
        case.plan, owner.select_native_continuation(writer=case.plane, plan=case.plan, predecessor=case.index)))
    def inputs(**kwargs):
        assert kwargs['read_only'] is True
        return case.bundle.verified_inputs
    monkeypatch.setattr(recursive_execution, '_external_inputs', inputs)
    instruction = tmp_path/'execution-selection.txt'
    instruction.write_text('Separate disclosed software execution selection.\n')
    return dict(directory=tmp_path, run_id='exposed.run', proposal_path=case.root/case.relative,
        execution_instruction_path=instruction, maximum_parallel_tasks=1)


def test_public_validation_publishes_no_execution_and_explicit_selection_dispatches_exact_index(case, tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    options = _public(case, tmp_path, monkeypatch)
    calls = []
    def run(**kwargs):
        index = owner.select_native_continuation(writer=case.plane, plan=case.plan, predecessor=case.index)
        calls.append(index)
        assert kwargs['maximum_parallel_tasks'] == 1
        return owner.repair_report(index)
    monkeypatch.setattr(recursive_execution, 'run_recursive_wave', run)
    service = ExperimentProgrammeService(tmp_path, case.plane)
    before = _files(case.root)
    preview = service.continue_native(**options)
    assert preview['status'] == 'EXECUTION_SELECTION_REQUIRED' and preview['native_tasks_started'] == 0
    assert preview['execution_authorized'] is False and not calls
    assert _files(case.root) == before
    result = service.continue_native(**options, confirmed=True)
    assert len(calls) == 1 and result['operational_native_continuation']['additional_independent_observations'] == 0
    selected = calls[0]
    assert selected.repair.owner_instruction_sha256 == sha256(options['execution_instruction_path'].read_bytes()).hexdigest()
    monkeypatch.setattr(owner, 'observe_frozen_worker_package_root', lambda _: Path('/disclosed/package'))
    assert service.continue_native(**options, confirmed=True) == result
    assert calls == [selected, selected]
    options['execution_instruction_path'].write_text('different execution selection\n')
    with pytest.raises(PermissionError, match='second selection'):
        service.continue_native(**options, confirmed=True)
    assert len(calls) == 2


@pytest.mark.parametrize('boundary', ('access', 'lock', 'closing-source'))
def test_public_continuation_keeps_original_permission_lock_and_source_boundaries(case, tmp_path, monkeypatch, boundary):
    from contextlib import nullcontext
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.infrastructure import source_closure
    def access():
        if boundary == 'access':
            raise PermissionError('disclosed revoked access')
    options = _public(case, tmp_path, monkeypatch, access=access)
    if boundary == 'closing-source':
        def changed(*args):
            raise PermissionError('disclosed controller source changed')
        monkeypatch.setattr(source_closure, 'require_admitted_target_source_current', changed)
    monkeypatch.setattr(recursive_execution, 'run_recursive_wave', lambda **k: pytest.fail('refusal dispatched work'))
    lock = owner._contacts(case.plane, case.plan).execution_lock('exposed.run') if boundary == 'lock' else nullcontext()
    with lock, pytest.raises((PermissionError, BlockingIOError)):
        ExperimentProgrammeService(tmp_path, case.plane).continue_native(**options, confirmed=True)
    assert not case.plane.root.resolve(owner.continuation_relative_path('exposed.run'), for_write=False).exists()
