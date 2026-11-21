# SPDX-License-Identifier: MPL-2.0
"""Scientific supply does not confuse local answers with favorable physics."""

from types import SimpleNamespace as Row

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import checkpoint_disposition, response_disposition
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_decision import latest_response_supply
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A


@pytest.mark.parametrize('states,ledger,expected', [
    (('AVAILABLE', 'AVAILABLE'), True, A.SATISFIED),
    (('AVAILABLE', 'UNAVAILABLE'), True, A.UNEVALUABLE),
    (('AVAILABLE', 'REJECTED'), True, A.FALSIFIED),
    (('AVAILABLE', 'AVAILABLE'), False, A.UNEVALUABLE),
])
def test_complete_paired_handoff_requires_usable_later_state(states, ledger, expected):
    original = Row(assessment=Row(positions=tuple(Row(disposition=s) for s in states), complete_native_return_ledger=ledger))
    assert checkpoint_disposition(original) is expected
    assert checkpoint_disposition(Row(assessment=None)) is A.UNEVALUABLE


def test_answered_adverse_response_is_distinct_from_unassessable_question():
    adverse = Row(questions=tuple(Row(assigned_comparisons=n, assessable_comparisons=n, disposition=d)
        for n, d in zip((6, 4, 2, 4, 2, 2), ('EMPIRICALLY_CONSISTENT', 'CONSEQUENTIAL_OMITTED_COUPLING',
            'CONSEQUENTIAL_OPERATOR_CHANGE', 'FINITE_RESPONSE_REMAINDER_UNRESOLVED',
            'CONSEQUENTIAL_MUTATION_ERROR', 'PREPARATION_NOT_SUFFICIENT_FOR_SELECTED_CHALLENGE'), strict=True)))
    assert response_disposition(adverse) is A.SATISFIED
    adverse.questions[3].disposition = 'NUMERICALLY_UNRESOLVED'
    assert response_disposition(adverse) is A.UNEVALUABLE
    adverse.questions[3].disposition = 'OBSERVED_FINITE_MISMATCH_INCOMPLETE'
    adverse.questions[3].assessable_comparisons = 3
    assert response_disposition(adverse) is A.UNEVALUABLE


def _assessment(name, effects):
    return Row(selection=Row(response=Row(identity=name, coverage=tuple(Row(effect=e, point=p, original_readout=r)
        for e, p, r in effects))))


def test_latest_assessment_uses_cumulative_original_evidence_and_refuses_selection():
    diagnostic = _assessment('diagnostic', (('d', 'd-point', 'd-readout'), ('c', None, None)))
    challenge = _assessment('challenge', (('d', 'd-point', 'd-readout'), ('c', 'c-point', 'c-readout')))
    assert latest_response_supply((challenge, diagnostic)) is challenge
    changed = _assessment('changed', (('d', 'another-point', 'another-readout'), ('c', 'c-point', 'c-readout')))
    with pytest.raises(ValueError, match='already observed'):
        latest_response_supply((diagnostic, changed))
    alternate = _assessment('favorable-reassessment', (('d', 'd-point', 'd-readout'), ('c', 'c-point', 'c-readout')))
    with pytest.raises(ValueError, match='unique cumulative'):
        latest_response_supply((challenge, alternate))
