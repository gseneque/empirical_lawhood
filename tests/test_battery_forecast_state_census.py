# SPDX-License-Identifier: MPL-2.0
"""Complete exposed adverse denominator and equal-condition controls; no native."""
from dataclasses import fields, replace
import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_census as census
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_state_control as state, forecast_step_control as step
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_segmented_state_census import complete_negative as complete_negative_fixture
from tests.test_battery_segmented_state_census import roster, stocks, prepared  # noqa: F401
from tests.test_battery_segmented_state_census import selected54, uncertain  # noqa: F401

complete_negative = complete_negative_fixture


@pytest.fixture
def actual_negative_census(complete_negative):
    receiver, originals = complete_negative
    control = ObjectIdentity('control.exposed-fixed-budget', state.ForecastStateControl.SCHEMA, '1.0.0', '1' * 64)
    rows = []
    for original in originals:
        values = {field.name: getattr(original, field.name) for field in fields(census.ForecastStateConclusion)
            if hasattr(original, field.name) and field.name not in {'scope', 'original_assessment', 'control'}}
        values.update(original_assessment=ObjectIdentity(original.original_assessment.object_id, state.ForecastStateStream.SCHEMA, '1.0.0', '2' * 64),
            control=control, interval_count=original.original_interval_count, interval_dispositions=original.original_interval_dispositions,
            actual_assignment_evidence=tuple(ObjectIdentity('assignment.exposed.' + config.object_id, step.ForecastStepEvidence.SCHEMA, '1.0.0', '3' * 64) for config in original.configurations))
        rows.append(census.ForecastStateConclusion(**values))
    return receiver, tuple(rows)


def test_all108_uses96_originals12_equal_keep_uncertainty_and_actual_assignments(actual_negative_census):
    receiver, rows = actual_negative_census
    result = census.join_complete_state(receiver, reversed(rows))
    assert result.disposition is A.UNEVALUABLE and len(result.selected_uses) == 108
    assert len(result.conclusions) == 96 and sum(bool(row.equal_condition_derivations) for row in result.selected_uses) == 12
    assert all(len(row.actual_assignment_evidence) == 2 for row in result.conclusions)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    with pytest.raises(ValueError, match='hides an adverse'):
        replace(result, disposition=A.SATISFIED, reason_codes=())
    with pytest.raises(ValueError, match='omits complete'):
        replace(result, selected_uses=result.selected_uses[:-1])
    with pytest.raises(ValueError, match='promotes unresolved'):
        replace(rows[0], disposition=A.SATISFIED, reason_codes=())


@pytest.mark.parametrize('damage', ('omitted', 'duplicate', 'trace', 'assignment', 'control', 'equal-derivation'))
def test_complete_actual_source_assignment_and_equal_derivation_cannot_be_substituted(actual_negative_census, damage):
    receiver, rows = actual_negative_census
    if damage == 'omitted':
        changed = rows[:-1]
    elif damage == 'duplicate':
        changed = (*rows[:-1], rows[0])
    elif damage == 'trace':
        changed = (replace(rows[0], traces=tuple(reversed(rows[0].traces))), *rows[1:])
    elif damage == 'assignment':
        with pytest.raises(ValueError, match='scientific identities'):
            replace(rows[0], actual_assignment_evidence=())
        return
    elif damage == 'control':
        changed = (replace(rows[0], control=ObjectIdentity('control.exposed-other', state.ForecastStateControl.SCHEMA, '1.0.0', '4' * 64)), *rows[1:])
    else:
        result = census.join_complete_state(receiver, rows)
        equal = next(i for i, row in enumerate(result.selected_uses) if row.equal_condition_derivations)
        with pytest.raises(ValueError, match='equal-condition'):
            replace(result.selected_uses[equal], equal_condition_derivations=())
        return
    with pytest.raises(ValueError):
        census.join_complete_state(receiver, changed)
