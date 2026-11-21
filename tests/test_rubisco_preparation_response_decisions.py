# SPDX-License-Identifier: MPL-2.0
"""Scientific decision falsifiers; disclosed arithmetic, without molecular claims."""

from decimal import Decimal, localcontext
from fractions import Fraction
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import PreparationResponseQuantity, _difference, _questions, next_response_supplier

MODELS = ('m1-wt', 'm1-i95m')


def findings(*, initial=('4', '5'), later=('.1', '.2'), initial_signal=('10', '20'),
             later_signal=('10', '20'), numerical='0', reciprocal='0'):
    quantities, values = [], {}
    def add(name, model, position, value):
        value = None if value is None else Decimal(value)
        values[name, model, position] = value
        quantities.append(PreparationResponseQuantity(name, model, position, value, 'hartree/bohr'))
    for i, model in enumerate(MODELS):
        for position, errors, signals in (('initial', initial, initial_signal), ('later', later, later_signal)):
            for name, value in (('signed-prediction-error', errors[i]), ('observed-change', signals[i]),
                    ('primary-receiver-numerical-discrepancy', numerical), ('omitted-coupling-change', '0')):
                add(name, model, position, value)
        add('reciprocal-receiver-discrepancy', model, 'later', reciprocal)
        add('additional-receiver-scale-discrepancy', model, 'later', None)
        add('operator-prediction-change', model, 'later-minus-initial', '0')
        change = None if later[i] is None else abs(Decimal(later[i])) - abs(Decimal(initial[i]))
        add('absolute-error-change', model, 'later-minus-initial', change)
    paired = {}
    for position, errors, signals in (('initial', initial, initial_signal), ('later', later, later_signal)):
        paired[position] = None if None in errors else Decimal(errors[1]) - Decimal(errors[0])
        add('paired-signed-prediction-error', 'I95M-minus-WT', position, paired[position])
        add('paired-observed-change', 'I95M-minus-WT', position, Decimal(signals[1]) - Decimal(signals[0]))
    add('paired-absolute-error-change', 'I95M-minus-WT', 'later-minus-initial',
        None if paired['later'] is None else abs(paired['later']) - abs(paired['initial']))
    design = SimpleNamespace(useful_error_hartree_per_bohr=Decimal(1), numerical_allowance_fraction=Decimal('.1'))
    return _questions(design, tuple(quantities), ())


def test_preparation_can_establish_response_despite_initial_failure():
    rows = findings()
    assert rows[3].disposition == 'WITHIN_SELECTED_ERROR_AFTER_PREPARATION'
    assert rows[5].disposition == 'PREPARATION_ESTABLISHES_LOCAL_APPLICABILITY'
    assert next_response_supplier(rows) == 'ASSESS_PREPARED_LOCAL_SUPPLIER_AT_OBSERVED_COST_FOR_NEXT_FORMATION_REQUIREMENT'


@pytest.mark.parametrize(('selection', 'expected'), (
    ({'initial': ('4', '4'), 'later': ('-.4', '.4')}, 'PAIRED_ERROR_WORSENS_DESPITE_PREPARATION'),
    ({'initial_signal': ('100', '200'), 'later_signal': ('5', '10'), 'later': ('.3', '.4')},
        'ERROR_REDUCTION_CONFOUNDED_BY_SIGNAL_SUPPRESSION'),
    ({'initial': ('0', '0'), 'later': ('0', '0'), 'later_signal': ('5', '10')},
        'ERROR_REDUCTION_CONFOUNDED_BY_SIGNAL_SUPPRESSION'),
    ({'later_signal': ('.5', '.6')}, 'SIGNAL_TOO_SMALL_FOR_PREPARATION_BENEFIT'),
    ({'initial': ('7', '9'), 'later': ('6', '8'), 'later_signal': ('5', '7')}, 'NO_BENEFIT_OVER_ZERO_RESPONSE'),
    ({'later': ('2', '3')}, 'PREPARATION_NOT_SUFFICIENT_FOR_SELECTED_CHALLENGE'),
    ({'initial': ('.3', '.4')}, 'PREPARATION_NOT_NEEDED_FOR_SELECTED_TOLERANCE'),
    ({'later_signal': ('10', '10.5')}, 'PREPARATION_IMPROVES_ARMS_PAIRED_SIGNAL_BELOW_ALLOWANCE'),
    ({'later': (None, '.2')}, 'UNAVAILABLE'),
))
def test_absolute_error_improvement_does_not_establish_every_scientific_benefit(selection, expected):
    rows = findings(**selection)
    assert rows[5].disposition == expected
    assert all(row.independent_biological_replicates == 0 and row.nested_state_positions == 4 for row in rows)
    assert next_response_supplier(rows) != 'ASSESS_PREPARED_LOCAL_SUPPLIER_AT_OBSERVED_COST_FOR_NEXT_FORMATION_REQUIREMENT'


@pytest.mark.parametrize('selection', ({'numerical': '.2'}, {'reciprocal': '.2'}))
def test_primary_or_reciprocal_disagreement_prevents_physical_attribution(selection):
    rows = findings(**selection)
    assert rows[0].assigned_comparisons == rows[0].assessable_comparisons == 6
    assert rows[0].disposition == 'CONSEQUENTIAL_SCALE_SENSITIVITY'
    assert rows[1].disposition == rows[2].disposition == rows[3].disposition == 'NUMERICALLY_UNRESOLVED'
    assert next_response_supplier(rows) == 'RESOLVE_NUMERICAL_OR_RECIPROCAL_DISCREPANCY_BEFORE_PHYSICAL_ATTRIBUTION'


def test_finite_failure_retains_ambiguous_physical_and_numerical_remainder():
    rows = findings(later=('2', '3'))
    assert rows[3].disposition == 'FINITE_RESPONSE_REMAINDER_UNRESOLVED'
    assert next_response_supplier(rows) == 'DISCRIMINATE_FINITE_REMAINDER_FROM_NUMERICAL_AND_PHYSICAL_BRANCH_ERROR_OR_STOP'


@pytest.mark.numerical(oracle='Independent Fraction subtraction of exact binary-float Decimal operands')
def test_signed_decimal_contrast_does_not_depend_on_ambient_precision():
    values = (Decimal.from_float(1.0000000000000002), Decimal.from_float(.1))
    with localcontext() as context:
        context.prec = 6
        result = _difference(*values)
    assert Fraction(result) == Fraction(values[0]) - Fraction(values[1])
