# SPDX-License-Identifier: MPL-2.0
"""Literal complete-result arithmetic; no source or qualification is supplied."""

from dataclasses import replace
from decimal import Decimal as D, localcontext

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_outcome_reduction import (
    _confirmation_comparisons, _nominate_functional_cases, _transfer_comparisons,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixFunctionalCaseResult, MatrixPreparationNomination
from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_later_programme import criterion, ref


def operands():
    groups = tuple("unit.literal-outcome." + str(at).zfill(2) for at in range(16))
    arms = ("hold", "recipe.a", "recipe.b")
    cases = tuple(MatrixFunctionalCaseResult("case." + arm + "." + group, group, arm, "FINITE",
        D(".01") if arm == "recipe.a" else D(".1"), D(".01"), None, arm == "recipe.a", False, None, False,
        D(".125"), ("LITERAL_OUTCOME_ARITHMETIC_CONTROL",)) for arm in arms for group in groups)
    return dict(result_id="nomination.literal-outcome", specification_identity=ref("specification.literal-outcome"),
        package_identity=ref("package.literal-outcome"), roster_identity=ref("roster.literal-outcome"), evidence_identity=ref("received.literal-outcome"),
        group_ids=groups, arm_ids=arms, hold_arm_id="hold", criterion=criterion(64), minimum_recoverable_groups=1,
        tie_policy="LEXICAL_ARM_ID", recipes=tuple((arm, ref("recipe.literal." + arm)) for arm in arms), cases=cases)


def test_complete16group_nomination_retains_unbounded_results_and_exact_effort():
    args = operands()
    with localcontext() as context:
        context.prec = 2
        result = _nominate_functional_cases(**args)
    assert type(result) is MatrixPreparationNomination
    assert result.selected_arm_id == "recipe.a" and result.disposition == "NOMINATED"
    assert result.candidate_results == (("recipe.a", 16, 16, D(2)), ("recipe.b", 0, 0, D(2)))
    assert len(result.cases) == 48 and len(result.development_unit_ids) == 16
    assert all(row.error_upper is None and not row.conditional_admission and row.source_support == "UNESTABLISHED" for row in result.cases)


@pytest.mark.parametrize("damage", ("missing-arm-cell", "duplicate-cell", "foreign-group", "foreign-arm"))
def test_outcome_reduction_refuses_thinned_or_crossed_complete_denominator(damage):
    args = operands()
    cases = args["cases"]
    if damage == "missing-arm-cell":
        cases = cases[:-1]
    elif damage == "duplicate-cell":
        cases = (*cases, cases[-1])
    elif damage == "foreign-group":
        cases = (replace(cases[0], unit_id="unit.foreign-outcome"), *cases[1:])
    else:
        cases = (replace(cases[0], arm_id="recipe.foreign-outcome"), *cases[1:])
    with pytest.raises(ValueError, match="drops or duplicates"):
        _nominate_functional_cases(**{**args, "cases": cases})


@pytest.mark.parametrize("kind,expected", (("missing", "UNEVALUABLE_OPPORTUNITY"), ("missing-effort", "UNEVALUABLE_OPPORTUNITY"),
    ("headroom-minimum", "NONDISCRIMINATING_OPPORTUNITY"), ("saturated-hold", "NONDISCRIMINATING_OPPORTUNITY")))
def test_adverse_results_and_declared_policy_cannot_create_a_nominee(kind, expected):
    args = operands()
    if kind == "missing":
        row = args["cases"][-1]
        args["cases"] = (*args["cases"][:-1], replace(row, disposition="MISSING", actual_error=None, functional_reliable=False))
    elif kind == "missing-effort":
        args["tie_policy"] = "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL"
        args["cases"] = tuple(replace(row, preparation_effort=None) if row.arm_id == "recipe.b" else row for row in args["cases"])
    elif kind == "headroom-minimum":
        args["minimum_recoverable_groups"] = 17
    else:
        args["cases"] = tuple(replace(row, functional_reliable=True, actual_error=D(".01")) if row.arm_id == "hold" else row for row in args["cases"])
    result = _nominate_functional_cases(**args)
    assert result.disposition == expected and result.selected_recipe is None and len(result.cases) == 48


@pytest.mark.parametrize("policy,selected", (("LEXICAL_ARM_ID", "recipe.a"), ("MINIMUM_TOTAL_EFFORT_THEN_LEXICAL", "recipe.b")))
def test_supplied_tie_policy_selects_the_unchanged_recipe(policy, selected):
    args = operands()
    args["tie_policy"] = policy
    args["cases"] = tuple(replace(row, functional_reliable=True, actual_error=D(".01"), preparation_effort=D(2) if row.arm_id == "recipe.a" else D(1))
        if row.arm_id != "hold" else row for row in args["cases"])
    result = _nominate_functional_cases(**args)
    assert result.selected_arm_id == selected and result.selected_recipe == dict(args["recipes"])[selected]


def matched_criterion():
    return replace(criterion(64), horizon_tick=64, normalized_error_maximum=D('.01'),
        paired_view_discrepancy_maximum=D('.0001'), minimum_usable_groups=0, minimum_admitted_groups=0,
        alpha_numerator=1, alpha_denominator=160, family_slots=AMENDED_PRIMARY_FAMILY,
        procedure="EXACT_PAIRED_E5_AND_ASSIGNED_DURATION_WIN_E6",
        missing_policy="ALL_ASSIGNED_PAIRED_WORST_CASE_AND_TRANSFER_NONSUCCESS")


def matched_cases(groups, outcomes, efforts=None):
    efforts = efforts or {arm: D(8) for arm in outcomes}
    return tuple(MatrixFunctionalCaseResult('case.' + arm + '.' + unit, unit, arm,
        'MISSING' if outcome is None else 'FINITE', None if outcome is None else D('.005') if outcome else D('.02'),
        None, None, outcome is True, False, None, False, efforts[arm], (), response_adequacy=outcome,
        response_adequacy_meaning="SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK")
        for arm, values in sorted(outcomes.items()) for unit, outcome in zip(groups, values, strict=True))


def matched_operands(outcomes, efforts=None):
    args = operands()
    return {**args, 'criterion': matched_criterion(), 'minimum_recoverable_groups': 2,
        'tie_policy': 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL', 'cases': matched_cases(args['group_ids'], outcomes, efforts)}


@pytest.mark.parametrize('wins, expected', ((42, False), (43, True)))
def test_matched_transfer_uses64_assigned_roots_and43_duration_wins_despite_no_admission(wins, expected):
    from scipy.stats import binomtest
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS
    regimes = tuple((name, tuple('unit.' + name + '.%02d' % index for index in range(64))) for name in ('nearby', 'shifted'))
    cases = []
    for _, groups in regimes:
        for index, case in enumerate(matched_cases(groups, {'hold': (False,) * 64})):
            counts = tuple((method, (None if index == 63 else 2 if method == 'BR' and index < wins else 0))
                for method in RELATION_METHODS)
            cases.append(replace(case, duration_error_counts=counts))
    results = _transfer_comparisons(matched_criterion(), regimes, ('interpolation', 'extrapolation'), 'hold', tuple(cases))
    assert len(results) == 2
    for result in results:
        assert result.duration_inference.critical_successes == 43
        assert result.duration_inference.events == (True,) * wins + (False,) * (63 - wins) + (None,)
        assert result.criterion_met_conditionally is expected
        assert result.p_value_numerator / result.p_value_denominator == pytest.approx(
            binomtest(wins, 64, .5, alternative='greater').pvalue, abs=1e-15)
        assert result.conditionally_admitted_groups == 0 and result.duration_inference.unknowns == 1


@pytest.mark.parametrize('wins, expected', ((42, False), (43, True)))
def test_curve_transport_has_its_own_primary_and_preserves_unknown_and_K_results(wins, expected):
    from scipy.stats import binomtest
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixCurveFunctionalComparison

    regimes = tuple((name, tuple('unit.' + name + '.%02d' % index for index in range(64))) for name in ('nearby', 'shifted'))
    cases, decisions = [], []
    for _, groups in regimes:
        for index, case in enumerate(matched_cases(groups, {'hold': (False,) * 64})):
            usable, success = index != 63, index < wins
            counts = tuple((method, 0 if usable else None) for method in RELATION_METHODS)
            cases.append(replace(case, duration_error_counts=counts))
            losses = tuple((method, (None if not usable else D('.1') if method == 'BR' and success else D(0),))
                for method in RELATION_METHODS)
            decisions.append(MatchedCurveDecision(case.unit_id, 'SR', 1, usable, success, losses, counts,
                ('LITERAL_ASSIGNED_CURVE_CONTROL',), (case.case_id,)))
    criterion = replace(matched_criterion(), procedure='EXACT_PAIRED_E5_AND_ASSIGNED_CURVE_WIN_E6')
    results = _transfer_comparisons(criterion, regimes, ('interpolation', 'extrapolation'),
        'hold', tuple(cases), curve_decisions=tuple(decisions))
    for result in results:
        assert type(result) is MatrixCurveFunctionalComparison
        assert result.curve_inference.critical_successes == 43
        assert result.curve_inference.events == (True,) * wins + (False,) * (63 - wins) + (None,)
        assert result.criterion_met_conditionally is expected
        assert result.p_value_numerator / result.p_value_denominator == pytest.approx(
            binomtest(wins, 64, .5, alternative='greater').pvalue, abs=1e-15)
        assert result.duration_inference is None and result.curve_inference.unknowns == 1
        assert all(row.duration_success is not True for row in result.curve_decisions)
        assert decode_canonical_bytes(result.canonical_bytes(), MatrixCurveFunctionalComparison, maximum_bytes=None) == result
        with pytest.raises(ValueError, match='inclusive margin'):
            replace(result, successes=result.successes + 1)


def test_matched_nomination_accepts_actual_rescues_despite_adverse_unknown_completion():
    args = matched_operands({'hold': (False,) * 16, 'recipe.a': (True,) * 3 + (None,) + (False,) * 12,
        'recipe.b': (False,) * 16})
    result = _nominate_functional_cases(**args)
    assert result.disposition == 'NOMINATED' and result.selected_arm_id == 'recipe.a'
    paired = dict(result.paired_adequacy)['recipe.a']
    assert paired.conservative.gains == 3 and paired.conservative.harms == 0
    assert len(paired.observed_gain_ids) == 3 and len(paired.unknown_group_ids) == 1
    assert paired.conservative.net_gain == 3 / D(16)
    assert decode_canonical_bytes(result.canonical_bytes(), MatrixPreparationNomination, maximum_bytes=None) == result
    with pytest.raises(ValueError, match='actual rescues'):
        replace(result, selected_arm_id='recipe.b')


@pytest.mark.parametrize('kind', ('one-rescue', 'net-harm', 'unknown-baseline'))
def test_matched_nomination_requires_two_actual_rescues_and_full_denominator_net_gain(kind):
    baseline = (False,) * 16
    alternative = (True,) + (False,) * 15
    if kind == 'net-harm':
        baseline = (False,) * 2 + (True,) * 2 + (False,) * 12
        alternative = (True,) * 2 + (False,) * 14
    elif kind == 'unknown-baseline':
        baseline = (None,) * 16
        alternative = (True,) * 16
    result = _nominate_functional_cases(**matched_operands({'hold': baseline, 'recipe.a': alternative, 'recipe.b': baseline}))
    assert result.selected_arm_id is None
    assert result.disposition == ('UNEVALUABLE_OPPORTUNITY' if kind == 'unknown-baseline' else 'NONDISCRIMINATING_OPPORTUNITY')


def test_matched_nomination_ranks_worst_case_net_then_effort_then_lexical():
    outcomes = {'hold': (False,) * 16, 'recipe.a': (True,) * 3 + (False,) * 13,
        'recipe.b': (True,) * 3 + (False,) * 13}
    result = _nominate_functional_cases(**matched_operands(outcomes, {'hold': D(8), 'recipe.a': D(8), 'recipe.b': D(7)}))
    assert result.selected_arm_id == 'recipe.b'
    assert _nominate_functional_cases(**matched_operands(outcomes)).selected_arm_id == 'recipe.a'
    missing_effort = _nominate_functional_cases(**matched_operands(outcomes, {'hold': D(8), 'recipe.a': None, 'recipe.b': D(7)}))
    assert missing_effort.disposition == 'UNEVALUABLE_OPPORTUNITY'
    outcomes['recipe.a'] = (True,) * 4 + (False,) * 12
    result = _nominate_functional_cases(**matched_operands(outcomes, {'hold': D(8), 'recipe.a': D(9), 'recipe.b': D(7)}))
    assert result.selected_arm_id == 'recipe.a'


def test_matched_confirmation_uses_discordance_and_keeps_statistical_harms_separate():
    groups = tuple('unit.confirm.' + str(at).zfill(2) for at in range(80))
    outcomes = {'hold': (False,) * 80, 'recipe.a': (True,) * 8 + (False,) * 72}
    result, = _confirmation_comparisons(matched_criterion(), groups, 'recipe.a', 'hold', matched_cases(groups, outcomes))
    assert result.criterion_met_conditionally and result.p_value_numerator == 1 and result.p_value_denominator == 256
    assert result.paired_adequacy.conservative.net_gain == D('.1') and result.usable_groups == 80
    outcomes['hold'] = (False,) * 79 + (None,)
    result, = _confirmation_comparisons(matched_criterion(), groups, 'recipe.a', 'hold', matched_cases(groups, outcomes))
    assert not result.criterion_met_conditionally and result.usable_groups == 79
    assert result.paired_adequacy.observed.harms == 0 and result.paired_adequacy.conservative.harms == 1
    assert result.paired_adequacy.outcomes[-1] == (False, None)
    assert result.missing_group_ids == (groups[-1],)


@pytest.mark.parametrize('change', ({'horizon_tick': 128}, {'minimum_admitted_groups': 1},
    {'alpha_denominator': 159}, {'family_slots': (*AMENDED_PRIMARY_FAMILY, 'extra.test')},
    {'missing_policy': 'RETAIN_ALL_ASSIGNED_GROUPS_AS_NONSUCCESS'}))
def test_matched_criterion_cannot_replace_endpoint_family_or_admission_gate(change):
    with pytest.raises(ValueError):
        replace(matched_criterion(), **change)
