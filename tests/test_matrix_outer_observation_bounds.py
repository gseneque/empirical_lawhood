# SPDX-License-Identifier: MPL-2.0
"""Bound outer rereads without replacing fresh child effect/access owners."""
from collections import Counter
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService


def _case(monkeypatch):
    writer = SimpleNamespace()
    writer.read_context = lambda: nullcontext(writer)
    writer.verification_scope = lambda: nullcontext(writer)
    writer.require_verification_snapshot = lambda: None
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=writer))
    context = SimpleNamespace(bindings={'e1':object(), 'e2':object()}, observations={},
        design=SimpleNamespace(downstream_account='ORIGINAL_E3'))
    calls, effects, authored = Counter(), [], set()
    reports = {
        'e1': {'status':'SUCCEEDED'},
        'e2': {'status':'SUCCEEDED','scientific_result':{'scientific_completion':'COMPLETE_NATIVE_UTILITY_ASSESSMENT'}},
        'train': {'state':'AUTHORING_REQUIRED'},
    }
    def read(actual, phase, **options):
        assert actual is context
        calls[phase] += 1
        return {**reports[phase], 'read_scope': 'EXECUTION_RECORDS',
            'execution_complete': reports[phase].get('status') == 'SUCCEEDED'}
    def project(actual, phase):
        if phase == 'e3':
            raise MatrixProgrammePrerequisite(phase, 'ACTUAL_ISSUE_REQUIRED', 'Select the original current issue.')
        assert phase == 'train'
        return object()
    def retain(actual, phase, result):
        actual.bindings[phase] = result
    def author(actual, phase, **options):
        if phase in authored:
            return False
        authored.add(phase)
        reports[phase] = {'status':'UNENTERED'}
        return True
    def operate(actual, phase, **options):
        effects.append(phase)
        reports[phase] = {'status':'SUCCEEDED','scientific_result':{'scientific_completion':'COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY'}}
        return {**reports[phase], 'read_scope': 'EXECUTION_RECORDS',
            'execution_complete': reports[phase].get('status') == 'SUCCEEDED'}
    monkeypatch.setattr(service, '_read_phase', read)
    monkeypatch.setattr(service, '_project', project)
    monkeypatch.setattr(service, '_retain_binding', retain)
    monkeypatch.setattr(service, '_author_phase', author)
    monkeypatch.setattr(service, '_operate_phase', operate)
    monkeypatch.setattr(service, '_report', lambda actual, **options: {
        'observations':dict(actual.observations), **options})
    return service, context, calls, effects, reports


def test_unchanged_predecessors_are_read_once_before_operating_new_phase(monkeypatch):
    service, context, calls, effects, _ = _case(monkeypatch)
    result = service._advance(context, mode='run', confirmed=True)
    assert calls == {'e1':1, 'e2':1, 'train':1}
    assert effects == ['train']
    assert result['observations']['train'].execution_complete
    assert not result['observations']['train'].complete
    assert result['dependencies'][0]['code'] == 'ACTUAL_ISSUE_REQUIRED'


@pytest.mark.parametrize('mode,expected_reads', [('derive',1),('author',2)])
def test_nonexecuting_modes_refresh_changes_without_native_entry(monkeypatch, mode, expected_reads):
    service, context, calls, effects, _ = _case(monkeypatch)
    result = service._advance(context, mode=mode)
    assert calls == {'e1':1, 'e2':1, 'train':expected_reads}
    assert not effects and not result['observations']['train'].complete


def test_operation_report_refuses_revoked_completed_predecessor_access(monkeypatch):
    service, context, _, effects, _ = _case(monkeypatch)
    def require_current():
        if effects:
            raise PermissionError('original completed access revoked')
    context.require_original_access = require_current
    with pytest.raises(PermissionError, match='original completed access revoked'):
        service._advance(context, mode='run', confirmed=True)
    assert effects == ['train']


def test_cached_completion_never_bypasses_actual_child_entry_guard(monkeypatch):
    service, context, _, effects, _ = _case(monkeypatch)
    def refuse(*args, **options):
        raise PermissionError('current child entry refused')
    monkeypatch.setattr(service, '_operate_phase', refuse)
    with pytest.raises(PermissionError, match='current child entry refused'):
        service._advance(context, mode='run', confirmed=True)
    assert not effects


def test_new_phase_refusal_is_observed_before_dependent_projection(monkeypatch):
    service, context, _, effects, _ = _case(monkeypatch)
    original = service._operate_phase
    projected = []
    project = service._project
    def operate(actual, phase, **options):
        result = original(actual, phase, **options)
        if phase == 'train':
            raise PermissionError('new TRAIN custody refused')
        return result
    def record(actual, phase):
        projected.append(phase)
        return project(actual, phase)
    monkeypatch.setattr(service, '_operate_phase', operate)
    monkeypatch.setattr(service, '_project', record)
    with pytest.raises(PermissionError, match='new TRAIN custody refused'):
        service._advance(context, mode='run', confirmed=True)
    assert projected == ['train']
