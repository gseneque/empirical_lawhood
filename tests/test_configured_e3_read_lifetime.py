# SPDX-License-Identifier: MPL-2.0
"""Temporary-body lifetimes in a disclosed scientific-reader control.

Literal reducer seams test object ownership, not scientific correctness or
authority. Original scientific replay and access have separate controls.
"""
from contextlib import contextmanager
from hashlib import sha256
from types import SimpleNamespace
import weakref

import pytest

from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read as owner
from empirical_lawhood.kernel.provenance import ObjectIdentity


class Body(SimpleNamespace):
    """Weak-referenceable literal metadata for this ownership probe only."""


def _record(name, **fields):
    return Body(record_id=name, SCHEMA='empirical-lawhood/testing/read-lifetime', VERSION='1.0.0',
        fingerprint=lambda: sha256(name.encode()).hexdigest(), **fields)


@pytest.mark.parametrize('original_products', (False, True))
def test_finished_scientific_replay_releases_temporary_records_before_consumer(monkeypatch, original_products):
    from empirical_lawhood.api import configured_e3_primary_amendment, configured_e3_retained_read, protected_e3_secondary_read
    from empirical_lawhood.infrastructure import study_issue

    specification = _record('specification.literal', measurement=SimpleNamespace(is_matched=True))
    allocation = _record('allocation.literal')
    specification.identity = owner._identity(specification)
    allocation.identity = owner._identity(allocation)
    candidate = _record('candidate.literal', candidate_id='candidate.literal')
    implementation = object()
    package = _record('package.literal', run_plan_id='run.literal',
        issued_study=SimpleNamespace(candidate=candidate, source_closure=implementation))
    tasks = (SimpleNamespace(task_id='task.literal'),)
    plan = _record('plan.literal', execution_plan_id='plan.literal', tasks=tasks)
    selected = Body(association=SimpleNamespace(candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate)),
        implementation=implementation, projection=SimpleNamespace(tasks=tasks))
    selected_reference = weakref.ref(selected)
    preparation = _record('preparation.literal')
    receipts = {}
    terminal = _record('terminal.literal', terminal_event_id='terminal.literal', completed_task_ids=('task.literal',))
    writer = object()
    state = {'active': False, 'access_checks': 0, 'current_checks': 0}

    def access():
        assert state['active']
        state['access_checks'] += 1

    def current():
        access()
        state['current_checks'] += 1

    @contextmanager
    def custody(*args, **kwargs):
        state['active'] = True
        try:
            yield SimpleNamespace(writer=writer, receipts=receipts, terminal=terminal,
                require_active=access, require_access=access, require_current=current)
        finally:
            current()
            state['active'] = False

    @contextmanager
    def retention(**kwargs):
        yield None

    monkeypatch.setattr(owner, '_original_design', lambda _: (specification, allocation))
    monkeypatch.setattr(owner, '_current_control', lambda **_: package)
    monkeypatch.setattr(owner, '_authorize', lambda *args: None)
    monkeypatch.setattr(owner, 'authenticate_current_execution_plan', lambda **_: plan)
    monkeypatch.setattr(owner, '_retained_scientific_writer', lambda *args: writer)
    monkeypatch.setattr(owner, '_selected_preparation', lambda _: preparation)
    monkeypatch.setattr(owner, '_selected_secondary_target', lambda *args: None)
    monkeypatch.setattr(configured_e3_primary_amendment, 'authenticate_primary_amendment', lambda **_: None)
    monkeypatch.setattr(owner, 'configured_receipt_read', custody)
    monkeypatch.setattr(configured_e3_retained_read, 'continued_plan_read', retention)
    monkeypatch.setattr(owner, 'statistical_task_id', lambda *args, mode=None: 'task.' + args[-1] + '.' + str(mode))
    monkeypatch.setattr(owner, 'adjudication_task_id', lambda *args: 'task.adjudicate')
    monkeypatch.setattr(owner, '_scientific_projection', lambda *args, **kwargs: {'literal_result': 'unchanged'})
    monkeypatch.setattr(owner, 'fitted_training_provenance', lambda *args: {'literal_training': 'unchanged'})
    prefit = _record('prefit.literal')
    models = _record('models.literal', reservation_join=owner._identity(prefit))
    transient_references, calls = [], []

    def product(current_writer, current_plan, current_receipts, task_id, kind):
        assert (current_writer, current_plan, current_receipts) == (writer, plan, receipts)
        calls.append(task_id)
        if task_id.startswith('transient.'):
            record = _record(task_id)
            transient_references.append(weakref.ref(record))
        elif kind is owner.ConfiguredProtectedE3ModelSet:
            record = models
        elif kind.__name__ == 'ConfiguredProtectedE3PreFitJoin':
            record = prefit
        else:
            record = _record(kind.__name__)
        return record, {'literal_custody': task_id}

    def replay(**kwargs):
        for index in range(4):
            task_id = 'transient.' + str(index)
            first = kwargs['product_reader'](writer, plan, receipts, task_id, Body)
            second = kwargs['product_reader'](writer, plan, receipts, task_id, Body)
            assert first is second
        return {'status': 'LITERAL_REPLAY_CONTROL'}, ()

    monkeypatch.setattr(owner, '_product', product)
    monkeypatch.setattr(protected_e3_secondary_read, 'read_matched_response', replay)
    reveal = _record('reveal.literal', authority_id='reveal.literal')
    monkeypatch.setattr(study_issue, 'ExternalStudyOperationAuthorityStore',
        lambda _: SimpleNamespace(load=lambda _: reveal))
    scope = owner._configured_e3_read(selected=selected, artifact_writer=writer, run_id='run.literal',
        reveal_authority_id='reveal.literal', original_products=original_products)
    del selected
    with scope as result:
        assert selected_reference() is None
        assert len(transient_references) == 4
        assert all(reference() is None for reference in transient_references)
        assert all(calls.count('transient.' + str(index)) == 1 for index in range(4))
        report = result.report if original_products else result
        assert report['literal_result'] == 'unchanged'
        assert report['matched_response_readout'] == {'status': 'LITERAL_REPLAY_CONTROL'}
        assert report['typed_product_validation'] == 'COMPLETE'
        if original_products:
            assert result.models is models and result.prefit is prefit
            assert result.preparation is preparation
            result.require_access()
            result.require_current()
    assert state['current_checks'] >= 1
    if original_products:
        with pytest.raises(AssertionError):
            result.require_access()
