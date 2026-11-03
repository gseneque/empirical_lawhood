# SPDX-License-Identifier: MPL-2.0
"""Disclosed resource-history controls; no actual E3 custody or authority."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.configured_e3_retained_custody import _resources
from empirical_lawhood.runtime.execution_envelope import RunExecutionResourceEnvelopeMachine as Machine
from tests.recovery_support import case as case


@pytest.mark.parametrize('state', ('known-failure', 'launched', 'unknown', 'reserved', 'wrong-reason', 'hidden-attempt'))
def test_retained_resource_read_distinguishes_known_failure_from_unresolved_work(case, state):
    """Replay real transition rules; only the unpublished journal I/O is doubled."""
    common = dict(cell_id=case.envelope.spec.cell_for_task(case.failed.task_id).cell_id,
        occurred_at_utc='2026-10-16T00:00:00Z')
    attempt = case.failed_event.attempt_id
    envelope = Machine.reserve(case.envelope, event_id='resource.disclosed.reserve', attempt_id=attempt, **common)
    if state != 'reserved':
        envelope = Machine.launch(envelope, event_id='resource.disclosed.launch', attempt_id=attempt, **common)
    if state == 'unknown':
        envelope = Machine.unknown_completion(envelope, event_id='resource.disclosed.unknown',
            reason_code='disclosed-unknown-return', **common)
    elif state in ('known-failure', 'wrong-reason', 'hidden-attempt'):
        envelope = Machine.observe_operational_failure(envelope, event_id='resource.disclosed.failure',
            attempt_id=attempt, reason_code=('disclosed-wrong-reason' if state == 'wrong-reason'
                else case.failed_event.failure.failure_class.value), **common)
    terminal = case.terminal
    if state == 'hidden-attempt':
        terminal = replace(terminal, operational_status='BLOCKED', failed_task_ids=(),
            attempts=tuple(row for row in terminal.attempts if row.task_id != case.failed.task_id))

    class DisclosedJournal:
        def reconstruct_execution_resource_envelope(self, **kwargs):
            assert kwargs['index'] == case.index and kwargs['spec'] == case.envelope.spec
            return envelope

        def read_event(self, index, relative):
            assert index == case.index
            candidate, = (row for row in index.task(case.failed.task_id).attempts if row.attempt_id == attempt)
            assert relative == candidate.event_relative_path
            return case.failed_event

    package = SimpleNamespace(execution_resource_envelope_spec=case.envelope.spec, jit_graph_signature_manifest=None)
    def read():
        return _resources(DisclosedJournal(), package, case.plan, case.index, {}, terminal)
    if state == 'known-failure':
        assert read() == envelope
        assert terminal.canonical_bytes() == case.terminal.canonical_bytes()
    else:
        with pytest.raises(PermissionError, match='resource'):
            read()
