# SPDX-License-Identifier: MPL-2.0
"""Categorical E1 controls, not native measurements or source qualification."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import occurrence as owner
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorObservation
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.provenance import ObjectIdentity


RULE = SimpleNamespace(risk_start_tick=0, lattice=tuple(range(9)),
    adjacent_angle_maximum_degrees=Decimal(10), origin_angle_maximum_degrees=Decimal(10))
FAMILIES = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))


def observations(flags):
    return tuple(FactorObservation(tick, 'UNAVAILABLE', None, None, None, None, None, None, None, None, None,
        False, 'UNAVAILABLE') if flag is None else FactorObservation(tick, 'AVAILABLE', True, flag, flag, None,
        Decimal(0) if flag else Decimal(1), Decimal(0), Decimal(0), None, Decimal(0), False, None)
        for tick, flag in enumerate(flags))


def event(flags, *, family=0, view='PRIMARY', sector='Y', usable=True):
    return owner.root_occurrence(root_id='root.' + str(family), unit_id='unit.' + str(family),
        source=ObjectIdentity('source.' + str(family), 'empirical-lawhood/test/occurrence', '1.0.0', 'a' * 64),
        family_id=FAMILIES[family], view=view, sector=sector, rule=RULE,
        occurrence_end_tick=6, survival_duration_ticks=2, observations=observations(flags),
        numerical_usable=usable, source_disposition='ASSESSED' if usable else 'NUMERICAL_UNUSABLE')


def test_initial_presence_and_earliest_admission_never_choose_a_later_longer_episode():
    value = event((True, False, True, True, True, True, True, True, True))
    assert value.initial_presence and value.occurrence and value.first_admission_tick == 0
    assert value.moving_survival is False and value.joint_survival is False
    assert value.return_after_exit is True and value.observed_exit_ticks == (1,)
    absent = event((False, False, True, True, True, True, True, True, True))
    assert absent.first_admission_tick == 2 and absent.first_admission_after_absence is True
    assert absent.joint_survival is True


def test_unknown_earlier_origin_unknown_eligibility_and_numerical_failure_are_distinct():
    uncertain_first = event((None, False, True, True, True, True, True, True, True))
    assert uncertain_first.occurrence is True and uncertain_first.first_observed_admission_tick == 2
    assert uncertain_first.first_admission_tick is None and uncertain_first.joint_survival is None
    assert uncertain_first.allowed_states('BOTH') == ('FAILURE', 'SUCCESS')
    uncertain_eligibility = event((False, None, False, False, False, False, False, True, True))
    assert uncertain_eligibility.occurrence is None
    assert uncertain_eligibility.allowed_states('BOTH') == ('FAILURE', 'INELIGIBLE', 'SUCCESS')
    unusable = event((True,) * 9, usable=False)
    assert unusable.initial_presence is None and unusable.occurrence is None
    assert unusable.first_admission_tick is None and unusable.allowed_states('BOTH') == uncertain_eligibility.allowed_states('BOTH')


def test_later_observed_failure_can_refute_survival_despite_an_earlier_gap():
    result = event((True, None, False, True, True, True, True, True, True))
    assert result.first_admission_tick == 0 and result.joint_survival is False
    assert result.unobserved_ticks == (1,)
    assert result.observed_exit_ticks == (2,)
    unknown = event((True, None, True, True, True, True, True, True, True))
    assert unknown.joint_survival is None and unknown.observed_exit_ticks == ()


def test_diagnostic_exits_and_returns_retain_the_followup_after_occurrence_cutoff():
    result = event((False,) * 6 + (True, False, True))
    assert result.first_admission_tick == 6 and result.joint_survival is False
    assert result.observed_exit_ticks == (7,) and result.return_after_exit is True


def test_full_map_has_eight_primary_cells_and_nested_diagnostic_denominators():
    events = tuple(event((True,) * 9, family=family, view=view, sector=sector)
        for family in range(4) for view in ('PRIMARY', 'FINE') for sector in ('X', 'Y'))
    result = owner.occurrence_cells(events, family_counts=dict.fromkeys(FAMILIES, 1))
    assert len(result) == 64 and sum(row.primary for row in result) == 8
    assert all(len(row.interval.unit_ids) == 1 for row in result)
    assert all(row.interval.tail_denominator == (2560 if row.primary else 40) for row in result)
    reports = tuple(owner.cell_report(cell) for cell in result)
    assert all(row['assigned_roots'] == row['known_successes'] == 1 for row in reports)
    assert all(row['complete_case_scope'] == 'CONDITIONAL_ON_ASSESSABILITY' for row in reports)
    with pytest.raises(ValueError, match='thins'):
        owner.occurrence_cells(events[:-1], family_counts=dict.fromkeys(FAMILIES, 1))
    changed = (replace(events[0], source=replace(events[0].source, object_fingerprint='b' * 64)), *events[1:])
    with pytest.raises(ValueError, match='aliases'):
        owner.occurrence_cells(changed, family_counts=dict.fromkeys(FAMILIES, 1))
