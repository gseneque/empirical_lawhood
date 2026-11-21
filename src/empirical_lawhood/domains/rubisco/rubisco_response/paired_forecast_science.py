# SPDX-License-Identifier: MPL-2.0
"""Exact paired endpoint arithmetic over one authenticated joint realization."""

from fractions import Fraction

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import PairedEffectiveRateRatios, bound_paired_endpoints
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds_assessment import assess_endpoint_enclosure
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational


def reduce_forecast_pair(case, rates, *, realization_id, source, dependence_group_id):
    """Keep the full WT waiting interval; never fit a missing absolute rate.

    The formation reversal cancels from these two limiting endpoint ratios.
    Its absence stays in the eight-role census and prevents complete supplier
    acceptance, without erasing the conditional arithmetic that is available.
    """
    missing = tuple((arm, name) for arm in ('wild_type', 'mutant') for name in PARAMETER_ORDER
        if rates[arm].get(name) is None)
    for arm in rates.values():
        for name, value in arm.items():
            if value is not None and (type(value) is not Fraction or value < 0
                    or value == 0 and name not in {'b', 'd_c', 'd_o'}):
                raise ValueError('forecast requires original finite nonnegative rates with positive productive rates')
    needed = tuple(row for row in missing if row[1] != 'b')
    if needed:
        return dict(missing_operands=missing, endpoint=None, owner_criteria='UNEVALUABLE',
            reason='COMPLETE_PAIRED_ENDPOINT_OPERANDS_UNAVAILABLE')
    wt, mutant = rates['wild_type'], rates['mutant']
    def commitment(row, branch):
        return row['r_'+branch]/(row['r_'+branch]+row['d_'+branch])
    ratios = (mutant['a']/wt['a'], mutant['r_c']/wt['r_c'],
        (mutant['c']/mutant['o'])/(wt['c']/wt['o']),
        (commitment(mutant,'c')/commitment(mutant,'o'))/(commitment(wt,'c')/commitment(wt,'o')))
    sources = tuple(sorted({source,case.case.identity,case.context.identity,case.closure_model},key=lambda s:s.object_id))
    selected = PairedEffectiveRateRatios('ratios.'+realization_id,case.case.identity,case.context.identity,
        *(Exact.of(v) for v in ratios),(Exact.of(0),Exact.of(1)),(source,)*4,None,
        case.closure_model,dependence_group_id,sources,())
    result = bound_paired_endpoints(selected,case.case,case.context,result_id='endpoint.'+realization_id)
    assessment = assess_endpoint_enclosure(selected,result,case.case,case.context,
        assessment_id='assessment.'+realization_id)
    low,high = (v.fraction for v in result.turnover_ratio_bounds)
    specificity = result.specificity_ratio.fraction
    # This is a universal statement over the complete closed waiting interval.
    disposition = ('FALSIFIED' if high <= 1 or specificity < 1 else
        'SATISFIED' if low > 1 and specificity >= 1 else 'UNEVALUABLE')
    return dict(missing_operands=missing,endpoint=result.to_document(),
        numerical_assessment=assessment.to_document(),
        ratios={name:rational(v) for name,v in zip(('formation','processing','gas_discrimination','branch_commitment'),ratios,strict=True)},
        turnover_ratio_bounds=tuple(rational(v) for v in (low,high)),specificity_ratio=rational(specificity),
        owner_criteria=disposition,criteria=dict(turnover='> 1',specificity='>= 1'),
        wild_type_waiting_fraction=(rational(0),rational(1)),
        physical_admission='UNEVALUABLE',biological_predictive_validity='UNEVALUABLE')
