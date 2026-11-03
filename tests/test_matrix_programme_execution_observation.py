# SPDX-License-Identifier: MPL-2.0
"""Operational advancement never manufactures a complete scientific read."""
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import (
    PHASES, MatrixProgrammeObservation, programme_frontier,
)
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService, _phase_complete


def _complete(phase):
    return MatrixProgrammeObservation(phase, {'status': 'SUCCEEDED'}, True,
        revision_trigger='TRIGGERED' if phase == 'e4.revision' else None,
        nomination_disposition='NOMINATED' if phase == 'e5.development' else None)


def test_execution_observation_cannot_complete_a_full_scientific_frontier():
    observations = {phase: _complete(phase) for phase in PHASES}
    for phase in ('e1', 'e2', 'train', 'e3'):
        report = {'status': 'SUCCEEDED', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True}
        observations[phase] = MatrixProgrammeObservation(phase, report, False, execution_complete=True)
        assert not _phase_complete(phase, report)
    assert programme_frontier(observations, downstream_account='ORIGINAL_E3', operational=True).complete
    full = programme_frontier(observations, downstream_account='ORIGINAL_E3')
    assert not full.complete and full.eligible == ('e1', 'e2', 'train')
    assert observations['e3'].execution_complete and not observations['e3'].complete


@pytest.mark.parametrize('operational', (False, True))
@pytest.mark.parametrize('report', (
    {'status': 'SUCCEEDED', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True},
    {'status': 'FAILED', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': False,
        'operational_terminal': 'AUTHENTICATED'},
    {'status': 'INCOMPLETE', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': False,
        'operational_census': ({'attempt_id': 'disclosed.attempt', 'receipt_id': None},)},
    {'status': 'INCOMPLETE', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': False,
        'recovery_index': {'disclosed': 'retained-index'}, 'operational_census': ()},
))
def test_conditional_nonentry_refuses_original_operational_completion_or_attempt(report, operational):
    observations = {
        'e4.revision': MatrixProgrammeObservation('e4.revision',
            {'read_scope': 'EXECUTION_RECORDS'}, False, revision_trigger='FIT_UNAVAILABLE', execution_complete=True),
        'e5.confirmation': MatrixProgrammeObservation('e5.confirmation', report, False,
            execution_complete=report['execution_complete']),
    }
    with pytest.raises(ValueError, match='conditional nonentry conflicts'):
        programme_frontier(observations, downstream_account='ORIGINAL_E3', operational=operational)


@pytest.mark.parametrize('status', ('UNENTERED', 'INPUTS_PARTIAL'))
def test_unexecuted_input_only_observation_is_not_inferred_native_contact(status):
    observations = {
        'e4.revision': MatrixProgrammeObservation('e4.revision', {'status': 'SUCCEEDED'}, True,
            revision_trigger='FIT_UNAVAILABLE'),
        'e5.confirmation': MatrixProgrammeObservation('e5.confirmation',
            {'read_scope': 'EXECUTION_RECORDS', 'status': status, 'task_count': 80,
                'operational_terminal': 'ABSENT', 'operational_census': (), 'execution_complete': False}, False),
    }
    frontier = programme_frontier(observations, downstream_account='ORIGINAL_E3', operational=True)
    assert dict(frontier.unentered)['e5.confirmation'] == 'UNENTERED_REQUIRED_SR_BR_FIT_UNAVAILABLE'


@pytest.mark.parametrize('phase', ('e2', 'train', 'e4.development', 'e4.source-cal', 'e4.calibration'))
def test_advance_uses_the_immediate_owner_read_without_a_second_or_final_replay(monkeypatch, phase):
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    observations = {name: _complete(name) for name in PHASES if name != phase}
    context = SimpleNamespace(observations=observations, bindings={phase: object()},
        design=SimpleNamespace(downstream_account='ORIGINAL_E3'))
    reads, operations, returns = [], [], []
    def read(actual, selected, **options):
        reads.append((selected, options))
        assert actual is context and selected == phase
        return {'status': 'UNENTERED'}
    report = ({'read_scope': 'EXECUTION_RECORDS', 'status': 'SUCCEEDED', 'execution_complete': True}
        if phase in ('e2', 'train') else {'status': 'SUCCEEDED',
            'scientific_result': {'scientific_completion': 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT'}})
    if phase == 'e4.development':
        report = {'status': 'SUCCEEDED', 'scientific_result': {'structure': {
            'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}}}
    elif phase == 'e4.calibration':
        report = {'scientific_completion': 'ASSESSMENT_RETAINED', 'all_wave_terminals_present': True,
            'assessment': {'status': 'SUCCEEDED', 'scientific_result': {}},
            'structure': {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}}
    def operate(actual, selected, **options):
        operations.append(selected)
        return report
    def finish(actual, dependencies):
        returns.append(actual.observations[phase])
        return programme_frontier(actual.observations, downstream_account='ORIGINAL_E3', operational=True)
    monkeypatch.setattr(service, '_read_phase', read)
    monkeypatch.setattr(service, '_author_phase', lambda *args: False)
    monkeypatch.setattr(service, '_operate_phase', operate)
    monkeypatch.setattr(service, '_advance_report', finish)
    assert service._advance(context, mode='run', confirmed=True).complete
    assert len(reads) == 1 and operations == [phase] and len(returns) == 1
    assert dict(returns[0].report) == report
    assert reads[0][1].get('execution_only', False)


@pytest.mark.parametrize('operational', (False, True))
def test_explicit_full_observation_still_uses_the_full_owner_reader(monkeypatch, operational):
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    context = SimpleNamespace(observations={}, bindings={'e1': object(), 'e2': object(), 'train': object()})
    calls = []
    def read(actual, phase, **options):
        calls.append((phase, options))
        return {'status': 'SUCCEEDED', 'scientific_result': {'scientific_completion': {
            'e1': 'RETAINED_ADJUDICATION', 'e2': 'COMPLETE_NATIVE_UTILITY_ASSESSMENT',
            'train': 'COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY'}[phase]}}
    monkeypatch.setattr(service, '_read_phase', read)
    with scientific_reconstruction_operation('full'):
        service._observe(context, operational=operational)
    assert [phase for phase, _ in calls] == ['e1', 'e2', 'train']
    assert not any(options.get('execution_only') for _, options in calls)
    assert all(row.complete and not row.execution_complete for row in context.observations.values())


@pytest.mark.parametrize('phase', ('e1', 'e3', 'e5.confirmation', 'e6'))
@pytest.mark.parametrize('mode', ('run', 'recover'))
@pytest.mark.parametrize('status', ('BLOCKED', 'FAILED'))
def test_refused_issued_operation_retains_exact_cause_without_full_scientific_read(monkeypatch, phase, mode, status):
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    context = SimpleNamespace(observations={name: _complete(name) for name in PHASES if name != phase},
        bindings={phase: object()}, design=SimpleNamespace(downstream_account='ORIGINAL_E3'))
    report = {'schema': 'empirical-lawhood/api/result', 'version': '1.0.0',
        'operation': 'campaign.' + mode, 'status': status, 'payload': None,
        'reason_codes': ['NATIVE_ENTRY_REFUSED'], 'errors': [{'category': 'EXECUTION',
            'reason_code': 'NATIVE_ENTRY_REFUSED', 'message': 'exposed original entry refusal', 'field': None}]}
    reads, operations = [], []

    def read(actual, selected, **options):
        assert actual is context and selected == phase
        assert not reads, 'refused operation triggered a full scientific read'
        reads.append(selected)
        return {'status': 'UNENTERED'}

    def operate(actual, selected, **options):
        assert actual is context and selected == phase
        assert options == {'recover': mode == 'recover', 'confirmed': True}
        operations.append(selected)
        return report

    def finish(actual, dependencies):
        assert actual is context and not actual.observations[phase].complete
        return dependencies

    monkeypatch.setattr(service, '_read_phase', read)
    monkeypatch.setattr(service, '_author_phase', lambda *args: False)
    monkeypatch.setattr(service, '_operate_phase', operate)
    monkeypatch.setattr(service, '_advance_report', finish)
    dependencies = service._advance(context, mode=mode, confirmed=True)
    assert reads == operations == [phase]
    assert len(dependencies) == 1
    assert dependencies[0]['phase'] == phase
    assert dependencies[0]['code'] == 'PHASE_OPERATION_NOT_COMPLETED'
    assert dependencies[0]['operation_result'] == report


def test_final_operation_report_refreshes_current_access_after_report_projection(monkeypatch):
    from empirical_lawhood.api import matrix_programme_products
    writer = SimpleNamespace(read_context=lambda: nullcontext(object()))
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=writer))
    revoked, checks = [], []
    def grants(*args):
        def current():
            checks.append(True)
            if revoked:
                raise PermissionError('actual current access revoked')
        current()
        return current
    monkeypatch.setattr(matrix_programme_products, '_current_grants', grants)
    monkeypatch.setattr(service, '_report', lambda *args, **kwargs: revoked.append(True) or {})
    with pytest.raises(PermissionError, match='revoked'):
        service._advance_report(object(), ())
    assert checks == [True, True]


@pytest.mark.parametrize('phase', ('e1', 'e2', 'train', 'e3'))
def test_inherited_phase_can_never_rederive_reauthor_or_reacquire(phase):
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    context = SimpleNamespace(phase_origins={phase: object()})
    with pytest.raises(PermissionError, match='original producers'):
        service._project(context, phase)
    with pytest.raises(MatrixProgrammePrerequisite, match='replacement authoring'):
        service._author_phase(context, phase)
    with pytest.raises(PermissionError, match='replacement acquisition'):
        service._operate_phase(context, phase, recover=False, confirmed=True)
