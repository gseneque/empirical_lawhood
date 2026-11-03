# SPDX-License-Identifier: MPL-2.0
"""Incremental operational state versus full replay; disclosed fixtures only."""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
from empirical_lawhood.runtime.execution_envelope import (
    RunExecutionResourceEnvelope, RunExecutionResourceEnvelopeMachine as Machine,
    reconstruct_execution_resource_envelope,
)
from tests.recovery_support import case as case
from tests.runtime_platform.test_deadline_free_execution_package import _plane


@pytest.fixture
def journal(case, tmp_path):  # noqa: F811
    store = ExternalExecutionResourceEnvelopeStore(_plane(tmp_path).root)
    store.create(case.envelope)
    return store


def _reservation(envelope, ordinal=0):
    cell = envelope.spec.task_cells[ordinal]
    return dict(event_id=f'event.reserve.{ordinal}', occurred_at_utc='2026-10-27T00:00:00Z',
        cell_id=cell.cell_id, attempt_id=f'attempt.{ordinal}')


def test_active_appends_visit_no_prior_events_or_unaffected_cells(case, journal, monkeypatch):
    expected = case.envelope
    operations = []
    for i, cell in enumerate(expected.spec.task_cells):
        args = _reservation(expected, i)
        operations.extend((('reserve', args), ('launch', args | {'event_id': f'event.launch.{i}'}),
            ('unknown_completion', {key: value for key, value in args.items() if key != 'attempt_id'}
                | {'event_id': f'event.unknown.{i}', 'reason_code': 'UNKNOWN_COMPLETION'})))
    for method, arguments in operations:
        expected = getattr(Machine, method)(expected, **arguments)

    public = DurableExecutionResourceEnvelopeCoordinator(journal)
    active = public._for_execution()
    assert active is not public and active._incremental
    current = active.current(expected.envelope_id)
    counts = {'aggregates': 0}
    original = RunExecutionResourceEnvelope.__post_init__

    def aggregate(self, previous):
        counts['aggregates'] += 1
        original(self, previous)

    class NoWholeEvents(list):
        def __iter__(self):
            pytest.fail('active append traversed prior events')

        def __getitem__(self, index):
            assert not isinstance(index, slice), 'active append copied prior events'
            return super().__getitem__(index)

    class NoWholeCells(dict):
        def values(self):
            pytest.fail('active append traversed unaffected cells')

    current.events = NoWholeEvents(current.events)
    current._cells = NoWholeCells(current._cells)
    monkeypatch.setattr(RunExecutionResourceEnvelope, '__post_init__', aggregate)
    for method, arguments in operations:
        if method == 'launch':
            arguments = arguments | {'jit_projection': None, 'jit_graph_signature_manifest': None}
        assert getattr(active, method)(envelope_id=current.envelope_id, **arguments) is current
    assert counts['aggregates'] == 0
    # Restore ordinary iteration for the explicit full immutable read.
    current.events = [list.__getitem__(current.events, i) for i in range(len(current.events))]
    current._cells = dict(current._cells)
    actual = public.current(current.envelope_id)
    assert type(actual) is RunExecutionResourceEnvelope
    assert counts['aggregates'] == 1
    assert actual.canonical_bytes() == expected.canonical_bytes()
    assert public.current(current.envelope_id) is actual
    assert counts['aggregates'] == 1
    cold = ExternalExecutionResourceEnvelopeStore(journal.root).load(current.envelope_id)
    assert cold.canonical_bytes() == expected.canonical_bytes()
    assert reconstruct_execution_resource_envelope(envelope_id=current.envelope_id,
        spec=actual.spec, execution_plan=actual.execution_plan, events=actual.events,
        jit_graph_signature_manifest=None) == actual
    # Unknown work consumes the original attempt and cannot be launched again.
    with pytest.raises(ValueError, match='retry is not allowlisted'):
        active.reserve(envelope_id=current.envelope_id,
            **(_reservation(actual) | {'event_id': 'event.forbidden', 'attempt_id': 'attempt.again'}))


@pytest.mark.parametrize('damage', ('stale', 'forged-cell', 'foreign-owner'))
def test_operational_append_refuses_conflicts_before_journal_changes(case, journal, damage):
    current = journal._operational_current(case.envelope.envelope_id)
    proposed = Machine.reserve(current, **_reservation(case.envelope))
    if damage == 'stale':
        journal._compare_and_append_transition(expected=current, updated=proposed)
    elif damage == 'forged-cell':
        proposed = replace(proposed, cells=(replace(proposed.cells[0], physical_tokens_reserved=1),))
    else:
        proposed = replace(proposed, owner=object())
    paths = tuple(journal._path(current.envelope_id, suffix) for suffix in ('json', 'journal', 'head'))
    before = tuple(path.read_bytes() if path.exists() else None for path in paths)
    with pytest.raises(ValueError, match='conflict|replayed event'):
        journal._compare_and_append_transition(expected=current, updated=proposed)
    assert before == tuple(path.read_bytes() if path.exists() else None for path in paths)


@pytest.mark.parametrize('head_committed', (False, True))
def test_interrupted_delta_commit_replays_only_the_committed_prefix(case, journal, monkeypatch, head_committed):
    current = journal._operational_current(case.envelope.envelope_id)
    proposed = Machine.reserve(current, **_reservation(case.envelope))
    original = journal._write_atomic

    def interrupt(path, record):
        if head_committed:
            original(path, record)
        raise OSError('disclosed head interruption')

    monkeypatch.setattr(journal, '_write_atomic', interrupt)
    with pytest.raises(OSError, match='head interruption'):
        journal._compare_and_append_transition(expected=current, updated=proposed)
    assert not current.events  # No pre-commit mutation of the active projection.
    monkeypatch.setattr(journal, '_write_atomic', original)
    cold = ExternalExecutionResourceEnvelopeStore(journal.root).load(current.envelope_id)
    expected = (Machine.reserve(case.envelope, **_reservation(case.envelope))
        if head_committed else case.envelope)
    assert cold.canonical_bytes() == expected.canonical_bytes()
    active = journal._operational_current(current.envelope_id)
    if not head_committed:
        journal._compare_and_append_transition(expected=active,
            updated=Machine.reserve(active, **_reservation(case.envelope)))
    assert len(journal.load(current.envelope_id).events) == 1


def test_custom_store_hook_retains_full_compare_append_path(journal, monkeypatch):
    coordinator = DurableExecutionResourceEnvelopeCoordinator(journal)
    monkeypatch.setattr(journal, 'compare_and_append', lambda **kwargs: None)
    assert coordinator._for_execution() is coordinator
