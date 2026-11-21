# SPDX-License-Identifier: MPL-2.0
"""Disclosed closure controls; the supplied ratios are not Gp observations."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as E
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import DissolvedGasQuery, FourStateRates, solve_four_state
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import PairedEffectiveRateRatios, PairedEndpointEnclosure, bound_paired_endpoints
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds_assessment import PairedEndpointEnclosureAssessment, assess_endpoint_enclosure
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A


def operands():
    supply = disclosed_supply()
    source = supply.case.sources[0]
    selected = PairedEffectiveRateRatios("ratios.disclosed", supply.case.identity, supply.context.identity,
        E.of(2), E.of(F(1, 2)), E.of(F(4, 5)), E.of(F(3, 2)), (E.of(0), E.of(1)),
        (source,) * 4, None, source, "dependence.disclosed.joint-realization",
        tuple(sorted({source, supply.case.identity, supply.context.identity}, key=lambda row: row.object_id)),
        ("requirement.disclosed.no-biological-evidence",))
    return selected, supply.case, supply.context


def calculate(selected, case, context):
    return bound_paired_endpoints(selected, case, context, result_id="bounds.disclosed")


def assess(selected, result, case, context):
    return assess_endpoint_enclosure(selected, result, case, context, assessment_id="assessment.disclosed.bounds")


@pytest.mark.parametrize("formation,processing", [(2, F(1, 2)), (F(1, 2), 2), (2, 2)])
def test_unknown_waiting_split_retains_the_exact_closed_envelope(formation, processing):
    selected, case, context = operands()
    selected = replace(selected, formation_ratio=E.of(formation), processing_ratio=E.of(processing))
    result = calculate(selected, case, context)
    assert tuple(value.fraction for value in result.turnover_ratio_bounds) == tuple(sorted((formation, processing)))
    assert result.specificity_ratio.fraction == F(6, 5)
    assert result.dependence_group_id == selected.dependence_group_id
    assert result.unresolved_requirement_ids == selected.remaining_requirements
    checked = assess(selected, result, case, context)
    assert checked.numerical_disposition is A.SATISFIED
    assert checked.physical_admission is A.UNEVALUABLE and checked.new_native_calls == 0


def test_supported_subinterval_is_tighter_without_selecting_a_point_or_using_float():
    selected, case, context = operands()
    selected = replace(selected, wild_type_formation_wait_fraction=(E.of(F(1, 4)), E.of(F(3, 4))),
        waiting_fraction_evidence=selected.ratio_sources[0])
    with localcontext() as arithmetic:
        arithmetic.prec = 2
        result = calculate(selected, case, context)
    assert tuple(value.fraction for value in result.turnover_ratio_bounds) == (F(8, 13), F(8, 7))
    assert assess(selected, result, case, context).numerical_disposition is A.SATISFIED
    for step in range(1, 101):
        w = F(1, 4) + F(step, 200)
        actual = 1 / (w / 2 + (1 - w) / F(1, 2))
        assert F(8, 13) <= actual <= F(8, 7)


@pytest.mark.parametrize("formation,processing,reverse_c,reverse_o", [(2, 8, 0, 0), (8, 2, 3, 9), (5, 5, 7, 4)])
def test_single_waiting_fraction_matches_complete_reversible_kinetic_solver(formation, processing, reverse_c, reverse_o):
    selected, case, context = operands()
    wt = FourStateRates(D(formation), D(3), D(4), D(reverse_c), D(reverse_o), D(5), D(processing), D(6))
    mutant = replace(wt, a=D(formation * 2), b=D(91), c=D(6), o=D(2),
        r_c=D(processing) / 2, r_o=D(13), d_c=D(reverse_c + 1), d_o=D(reverse_o + 2))
    qwt, qm = wt.fractions, mutant.fractions
    def chi(q, branch):
        return q['r_' + branch] / (q['r_' + branch] + q['d_' + branch])

    waiting = E.of(F(processing, formation + processing))
    selected = replace(selected, wild_type_formation_wait_fraction=(waiting, waiting),
        waiting_fraction_evidence=selected.ratio_sources[0],
        gas_discrimination_ratio=E.of((qm['c'] / qm['o']) / (qwt['c'] / qwt['o'])),
        branch_commitment_ratio=E.of((chi(qm, 'c') / chi(qm, 'o')) / (chi(qwt, 'c') / chi(qwt, 'o'))))
    result = calculate(selected, case, context)
    a, b = (solve_four_state(q, DissolvedGasQuery(D(20), D(250)), result_id='result.' + name).intrinsic
        for q, name in ((wt, 'wt'), (mutant, 'mutant')))
    assert result.turnover_ratio_bounds[0] == result.turnover_ratio_bounds[1]
    assert result.turnover_ratio_bounds[0].fraction == b.kcat_c.fraction / a.kcat_c.fraction
    assert result.specificity_ratio.fraction == b.specificity.fraction / a.specificity.fraction
    assert assess(selected, result, case, context).numerical_disposition is A.SATISFIED


def test_common_gating_does_not_supply_specificity_evidence():
    selected, case, context = operands()
    selected = replace(selected, gas_discrimination_ratio=E.of(1), branch_commitment_ratio=E.of(1))
    result = calculate(selected, case, context)
    assert result.specificity_ratio.fraction == 1
    assert any('paired-rate-contrast-support' in name for name in result.unresolved_requirement_ids)
    assert assess(selected, result, case, context).physical_admission is A.UNEVALUABLE


def test_retained_assessor_never_calls_producer_and_detects_narrowed_bounds(monkeypatch):
    import empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds as producer
    selected, case, context = operands()
    result = calculate(selected, case, context)

    def forbidden(*args, **kwargs):
        raise AssertionError('assessment cannot call producer')

    monkeypatch.setattr(producer, 'bound_paired_endpoints', forbidden)
    assert assess(selected, result, case, context).numerical_disposition is A.SATISFIED
    for changes in ({'turnover_ratio_bounds': (E.of(F(3, 4)), E.of(2))},
                    {'turnover_ratio_bounds': (E.of(F(1, 2)), E.of(F(7, 4)))},
                    {'specificity_ratio': E.of(1)}):
        assert assess(selected, replace(result, **changes), case, context).numerical_disposition is A.FALSIFIED


def test_unknown_oxygen_and_unjustified_waiting_restrictions_cannot_be_filled():
    selected, _, _ = operands()
    with pytest.raises((TypeError, ValueError)):
        replace(selected, gas_discrimination_ratio=None)
    with pytest.raises(ValueError, match='source evidence'):
        replace(selected, wild_type_formation_wait_fraction=(E.of(F(1, 4)), E.of(F(3, 4))))
    with pytest.raises(ValueError, match='positive finite rates'):
        replace(selected, wild_type_formation_wait_fraction=(E.of(0), E.of(0)))
    with pytest.raises(ValueError, match='ordered source'):
        replace(selected, ratio_sources=selected.ratio_sources[:3])


def test_wrong_pair_source_or_pruned_requirements_are_refused():
    selected, case, context = operands()
    result = calculate(selected, case, context)
    with pytest.raises(ValueError, match='pairing, input'):
        assess(replace(selected, input_id='ratios.other'), result, case, context)
    with pytest.raises(ValueError, match='pairing, input'):
        assess(selected, replace(result, unresolved_requirement_ids=()), case, context)
    with pytest.raises(ValueError, match='actual paired'):
        calculate(selected, replace(case, case_id='case.other'), context)


def test_all_new_records_have_exact_canonical_recovery():
    selected, case, context = operands()
    result = calculate(selected, case, context)
    checked = assess(selected, result, case, context)
    for record, kind in ((selected, PairedEffectiveRateRatios), (result, PairedEndpointEnclosure),
                         (checked, PairedEndpointEnclosureAssessment)):
        recovered = decode_canonical_bytes(record.canonical_bytes(), kind, maximum_bytes=100000)
        assert recovered == record and recovered.canonical_bytes() == record.canonical_bytes()
