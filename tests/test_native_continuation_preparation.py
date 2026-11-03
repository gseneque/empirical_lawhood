# SPDX-License-Identifier: MPL-2.0
"""Incomplete native proposals retain actual software custody and grant no retry."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import native_continuation_preparation as owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.infrastructure.native_parent_finalization import NativeParentFinalizationPending
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.native_continuation_proposal import DevelopmentNativeContinuationProposal
from empirical_lawhood.runtime.native_effects import NativeEntryRefused
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.runtime_platform.test_native_parent_finalization_scheduler import _runtime


def _files(root):
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()}


@pytest.fixture
def interrupted(tmp_path, monkeypatch, request):
    mode = getattr(request, 'param', 3)
    state = _runtime(tmp_path, mode=mode if isinstance(mode, str) else 'complete', parent_prepared=True)
    scheduler, contacts = state.scheduler()
    calls = []
    def permission(*args, **kwargs):
        calls.append(kwargs['prepared_contract'])
        if len(calls) == mode:
            raise PermissionError('disclosed software permission loss before native call')
    if isinstance(mode, int):
        scheduler.native_entry_guard = permission
    try:
        if mode == 'complete':
            scheduler.execute('exposed.run', state.plan)
        else:
            with pytest.raises(NativeEntryRefused if isinstance(mode, int) else NativeParentFinalizationPending):
                scheduler.execute('exposed.run', state.plan)
        parent = contacts.read('exposed.run', state.task.task_id)
        store = ExternalNativeSubworkStore(plane=state.plane, parent_contacts=contacts,
            parent_contact=parent, completed_only=True)
        state.invocation = store.read_prepared_invocation(parent)
        state.refused_at = mode
        state.native_store = store
        state.root = Path(state.plane.root.contract.canonical_path)
        from empirical_lawhood.api import recursive_operations
        registration = SimpleNamespace(selection=state.task.capability, native_effect=True)
        monkeypatch.setattr(recursive_operations, 'operation_catalog', lambda: (
            (registration,), SimpleNamespace(fingerprint=lambda: state.plan.registry_sha256), None))
        yield state
    finally:
        state.bundle.close()
        state.repository.engine.dispose()


def _inspect(state, require_access=lambda: None):
    return owner._inspect_original(writer=state.plane, plan=state.plan, index=state.index,
        external_inputs=state.bundle.verified_inputs, require_access=require_access)


def _proposal(state, values):
    return DevelopmentNativeContinuationProposal('proposal.exposed', 'a' * 64, 'exposed.run',
        ObjectIdentity.from_record(state.plan.execution_plan_id, state.plan),
        ObjectIdentity.from_record(state.index.recovery_index_id, state.index), **values,
        worker=state.invocation.implementation, controller=state.invocation.implementation,
        worker_environment=state.invocation.environment, worker_source_root='/disclosed/source',
        pure_output_bytes=256 * 1024**2)


@pytest.mark.parametrize('interrupted', (2, 3), indirect=True)
def test_complete_original_proposal_preserves_begun_and_unknown_without_execution(interrupted, monkeypatch):
    state = interrupted
    before = _files(state.root)
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', lambda *a, **k: pytest.fail('proposal tried recovery'))
    monkeypatch.setattr(ExternalNativeSubworkStore, 'begin', lambda *a, **k: pytest.fail('proposal tried native entry'))
    values = _inspect(state)
    proposal = _proposal(state, values)
    candidate, = proposal.candidates
    observed, = candidate.subwork_states
    expected = NativeSubworkState.BEGUN if state.refused_at == 2 else NativeSubworkState.UNKNOWN_COMPLETION
    assert observed == (state.invocation.native_work.definitions[0].identity, expected)
    assert candidate.invocation == state.invocation
    assert proposal.task_ids == proposal.native_task_ids == (state.task.task_id,)
    assert proposal.completed_receipts == proposal.completed_native_task_ids == ()
    assert not proposal.execution_authorized and proposal.additional_independent_observations == 0
    assert decode_canonical_bytes(proposal.canonical_bytes(), type(proposal), maximum_bytes=None) == proposal
    assert _files(state.root) == before
    for changes in ({'execution_authorized': True}, {'additional_independent_observations': 1},
            {'original_run_id': 'substitute.run'}, {'candidates': ()}, {'native_task_ids': ()},
            {'worker_environment': replace(proposal.worker_environment, interpreter_path='/another/python')},
            {'pure_output_bytes': 256 * 1024**2 + 1}):
        with pytest.raises((ValueError, TypeError)):
            replace(proposal, **changes)
    with pytest.raises(ValueError, match='completed or unselected'):
        replace(candidate, subwork_states=((observed[0], NativeSubworkState.COMPLETED),))


@pytest.mark.parametrize('interrupted', ('raw-products-missing', 'raw-failed-products-missing'), indirect=True)
def test_known_return_without_products_cannot_be_proposed_as_a_new_attempt(interrupted):
    before = _files(interrupted.root)
    with pytest.raises(PermissionError, match='retained native returns'):
        _inspect(interrupted)
    assert _files(interrupted.root) == before


def test_original_unreceipted_parent_output_refuses_proposal(interrupted):
    path = interrupted.plane.root.resolve(interrupted.task.outputs[0].relative_path, for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'disclosed partial product')
    with pytest.raises(PermissionError, match='unreceipted original parent outputs'):
        _inspect(interrupted)


@pytest.mark.parametrize('interrupted', ('complete',), indirect=True)
def test_completed_native_task_is_retained_and_never_becomes_a_candidate(interrupted):
    before = _files(interrupted.root)
    values = _inspect(interrupted)
    assert values['completed_native_task_ids'] == (interrupted.task.task_id,)
    assert tuple(key for key, _ in values['completed_receipts']) == (interrupted.task.task_id,)
    assert values['candidates'] == ()
    with pytest.raises(ValueError, match='incomplete native candidates'):
        _proposal(interrupted, values)
    assert _files(interrupted.root) == before


def test_changed_registry_and_current_access_refuse_before_proposal(interrupted, monkeypatch):
    from empirical_lawhood.api import recursive_operations
    before = _files(interrupted.root)
    def revoked():
        raise PermissionError('disclosed access revoked')
    with pytest.raises(PermissionError, match='access revoked'):
        _inspect(interrupted, revoked)
    monkeypatch.setattr(recursive_operations, 'operation_catalog', lambda: (
        (), SimpleNamespace(fingerprint=lambda: 'f' * 64), None))
    with pytest.raises(PermissionError, match='operation registry'):
        _inspect(interrupted)
    assert _files(interrupted.root) == before


def _public_selection(state, tmp_path, monkeypatch, *, require_access=lambda: None):
    from empirical_lawhood.api import recursive_authoring, recursive_execution
    from empirical_lawhood.infrastructure import run_source_admission, source_closure
    source = state.invocation.implementation
    monkeypatch.setattr(run_source_admission, '_capture_source', lambda _: object())
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda *a, **k: source)
    monkeypatch.setattr(owner, 'observe_frozen_repair_worker', lambda **k: (source, state.invocation.environment))
    monkeypatch.setattr(owner, 'require_scientific_source', lambda worker, controller: None)
    monkeypatch.setattr(source_closure, 'require_admitted_target_source_current', lambda *a: None)
    draft = SimpleNamespace(development_study=SimpleNamespace(access_pair=(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)))
    payloads = SimpleNamespace(original_input_access=SimpleNamespace(require_current=require_access))
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', lambda **k: (None, draft, source, payloads))
    monkeypatch.setattr(recursive_execution, '_retained_plans', lambda *a: (
        SimpleNamespace(run_plan_id='exposed.run'), state.plan, state.index))
    def inputs(**kwargs):
        assert kwargs['read_only'] is True
        return state.bundle.verified_inputs
    monkeypatch.setattr(recursive_execution, '_external_inputs', inputs)
    instruction = tmp_path/'instruction.txt'
    instruction.write_text('Prepare a separate explicit proposal; no scientific execution.\n')
    directory = tmp_path/'original-authoring'
    directory.mkdir()
    return dict(directory=directory, run_id='exposed.run', output_dir=state.root/'proposals/exposed',
        preparation_instruction_path=instruction, worker_interpreter='/disclosed/python',
        worker_source_root='/disclosed/source', pure_output_bytes=256 * 1024**2)


def test_public_preparation_publishes_only_separate_proposal_and_retains_original_bytes(interrupted, tmp_path, monkeypatch):
    state = interrupted
    options = _public_selection(state, tmp_path, monkeypatch)
    before = _files(state.root)
    from empirical_lawhood.infrastructure.execution import LocalScheduler
    monkeypatch.setattr(LocalScheduler, 'execute', lambda *a, **k: pytest.fail('preparation dispatched work'))
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', lambda *a, **k: pytest.fail('preparation recovered native work'))
    result = ExperimentProgrammeService(tmp_path, state.plane).prepare_native_continuation(**options)
    assert result['status'] == 'PREPARED_REVIEW_REQUIRED'
    assert result['native_tasks_started'] == result['additional_independent_observations'] == 0
    assert result['execution_authorized'] is False
    publication = options['output_dir']/'proposal.json'
    proposal = decode_canonical_bytes(publication.read_bytes(), DevelopmentNativeContinuationProposal, maximum_bytes=None)
    assert proposal.preparation_instruction_sha256 == sha256(options['preparation_instruction_path'].read_bytes()).hexdigest()
    after = _files(state.root)
    assert {key: after[key] for key in before} == before
    assert all(key.startswith('proposals/exposed/') for key in after.keys() - before.keys())
    with pytest.raises(FileExistsError, match='disjoint'):
        ExperimentProgrammeService(tmp_path, state.plane).prepare_native_continuation(**options)


@pytest.mark.parametrize('boundary', ('initial-access', 'closing-access', 'closing-source', 'late-original-contact'))
def test_public_preparation_refuses_revoked_access_or_late_original_changes(interrupted, tmp_path, monkeypatch, boundary):
    state = interrupted
    published = []
    def access():
        if boundary == 'initial-access' or boundary == 'closing-access' and published:
            raise PermissionError('disclosed current access revoked')
    options = _public_selection(state, tmp_path, monkeypatch, require_access=access)
    from empirical_lawhood.infrastructure import source_closure
    def source_current(*args):
        if boundary == 'closing-source' and published:
            raise PermissionError('disclosed preparation source changed')
    monkeypatch.setattr(source_closure, 'require_admitted_target_source_current', source_current)
    original_write = state.plane.write
    def write(request):
        result = original_write(request)
        if request.payload_schema == DevelopmentNativeContinuationProposal.SCHEMA:
            published.append(result)
            if boundary == 'late-original-contact':
                path = state.plane.root.resolve(state.native_store.parent_contacts._path('exposed.run', state.task.task_id), for_write=False)
                path.write_bytes(path.read_bytes() + b' ')
        return result
    monkeypatch.setattr(state.plane, 'write', write)
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        ExperimentProgrammeService(tmp_path, state.plane).prepare_native_continuation(**options)
    if boundary == 'initial-access':
        assert not options['output_dir'].exists()
    else:
        assert published  # A refused closing guard never returns an accepted proposal report.


def test_public_preparation_refuses_a_live_original_execution_lock(interrupted, tmp_path, monkeypatch):
    state = interrupted
    options = _public_selection(state, tmp_path, monkeypatch)
    with owner._contacts(state.plane, state.plan).execution_lock('exposed.run'):
        with pytest.raises(BlockingIOError):
            ExperimentProgrammeService(tmp_path, state.plane).prepare_native_continuation(**options)
    assert not options['output_dir'].exists()


def test_public_preparation_requires_an_actual_nonempty_instruction(tmp_path):
    instruction = tmp_path/'empty.txt'
    instruction.write_bytes(b' \n')
    with pytest.raises(ValueError, match='instruction is empty'):
        ExperimentProgrammeService(tmp_path, object()).prepare_native_continuation(directory=tmp_path,
            run_id='exposed.run', output_dir=tmp_path/'proposal', preparation_instruction_path=instruction,
            worker_interpreter='/disclosed/python', worker_source_root='/disclosed/source', pure_output_bytes=4096)


def test_proposal_destination_cannot_enter_original_run_namespace(interrupted, tmp_path, monkeypatch):
    state = interrupted
    options = _public_selection(state, tmp_path, monkeypatch)
    options['output_dir'] = state.root/'runs/exposed.run/proposal'
    with pytest.raises(ValueError, match='outside original run'):
        ExperimentProgrammeService(tmp_path, state.plane).prepare_native_continuation(**options)
    assert not options['output_dir'].exists()
