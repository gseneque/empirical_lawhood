# SPDX-License-Identifier: MPL-2.0
"""Structure is mandatory ordinary E4 production, never an outer closeout slot."""
from copy import deepcopy

import pytest

from empirical_lawhood.api.matrix_researcher_programme import _phase_complete


def test_development_success_without_complete_structure_cannot_advance_revision():
    report = {'status': 'SUCCEEDED', 'scientific_status': 'ADVERSE',
        'structure': {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}}
    assert _phase_complete('e4.development', report)
    for structure in (None, {'scientific_completion': 'NOT_ESTABLISHED'}, {'state': 'NOT_ENTERED'}):
        assert not _phase_complete('e4.development', {**report, 'structure': structure})
    assert not _phase_complete('e4.development', {**report, 'status': 'REFUSED'})


@pytest.mark.parametrize('phase', ('e4.calibration', 'e4.confirmation'))
def test_protected_phase_keeps_actual_wave_assessment_and_structure_requirements(phase):
    report = {'scientific_completion': 'ASSESSMENT_RETAINED', 'all_wave_terminals_present': True,
        'assessment': {'status': 'SUCCEEDED', 'scientific_result': {'scientific_status': 'PRIMARY_NONSUCCESS'}},
        'structure': {'scientific_completion': 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'}}
    assert _phase_complete(phase, report)
    changes = (('scientific_completion', 'NOT_ESTABLISHED'), ('all_wave_terminals_present', False),
        ('assessment', {'status': 'SUCCEEDED'}), ('assessment', {'status': 'FAILED', 'scientific_result': {}}),
        ('structure', {'scientific_completion': 'NOT_ESTABLISHED'}))
    for key, value in changes:
        changed = deepcopy(report); changed[key] = value
        assert not _phase_complete(phase, changed)
