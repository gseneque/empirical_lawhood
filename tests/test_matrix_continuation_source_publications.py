# SPDX-License-Identifier: MPL-2.0
"""Finite source guards around metadata only; no native science or authority."""
from pathlib import Path

import pytest

from empirical_lawhood.api import matrix_programme_source_continuation as owner


@pytest.mark.parametrize('failure', ('none', 'before', 'during', 'consumer'))
def test_closed_publication_source_guard_keeps_initial_final_and_failure_checks(monkeypatch, failure):
    root = Path('/disclosed/selected-source')
    admitted = object()
    changed = failure == 'before'
    events = []

    def guard(actual_root, actual_admission):
        assert (actual_root, actual_admission) == (root, admitted)
        events.append('source-check')
        if changed:
            raise PermissionError('actual selected source bytes changed')

    monkeypatch.setattr(owner, 'require_admitted_target_source_current', guard)

    def consume():
        nonlocal changed
        with owner._current_source_publications(root, admitted):
            # These events stand for a closed metadata group, not a source
            # acceptance fixture or an acquired scientific result.
            events.extend(('metadata-one', 'metadata-two'))
            if failure == 'during':
                changed = True
            if failure == 'consumer':
                raise ValueError('metadata consumer refused')

    if failure in ('before', 'during'):
        with pytest.raises(PermissionError, match='selected source bytes changed'):
            consume()
    elif failure == 'consumer':
        with pytest.raises(ValueError, match='metadata consumer refused'):
            consume()
    else:
        consume()
    assert events == (['source-check'] if failure == 'before' else
        ['source-check', 'metadata-one', 'metadata-two', 'source-check'])
