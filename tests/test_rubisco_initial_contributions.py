# SPDX-License-Identifier: MPL-2.0
"""Disclosed algebra and custody controls, not evidence about molecular effects."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from itertools import product

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as E
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import FourStateRates, intrinsic_constants
from empirical_lawhood.domains.rubisco.rubisco_response.initial_contributions import CONTRIBUTION_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.api.domain_composition.rubisco_response import initial_model as public
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.test_recursive_public_service import _plane
from tests.test_rubisco_initial_model import publish_sources, selection


def contributions(values=(F(2), F(3, 2), F(4, 3), F(1, 2), F(2, 3)), *, intervals=False):
    selected, source = selection()
    rows = tuple(public.InitialContribution(name,
        None if value is None else tuple(E.of(v) for v in value) if intervals else (E.of(value),)*2,
        'UNIDENTIFIED' if value is None else 'SOURCE_CONDITIONED',
        () if value is None else (source.identity,), ('missing.'+name,) if value is None else ())
        for name,value in zip(CONTRIBUTION_ORDER, values, strict=True))
    record = public.prepare_initial_contribution_realization(case=selected.cases[0], alternative_id='chemical.exposed',
        realization_id='realization.exposed.contributions', dependence_group_id='dependence.exposed.contributions',
        support_kind='JOINT_ENCLOSURE' if intervals else 'FIXED_JOINT_REALIZATION', contributions=rows)
    return selected, source, record


def model_evidence(selected, source, record):
    projected = public.initial_contrast_evidence(record)
    reviews = tuple(public.InitialContrastReview('review.contributions.'+c.contrast, record.case, record.context,
        record.state_selection, c.contrast, c.bounds,
        tuple(sorted((source.identity,record.identity), key=lambda p:p.object_id)),
        'Disclosed software control only. No physical support or qualification.', A.SATISFIED, ())
        for c in projected if c.bounds is not None)
    contrasts = public.initial_contrast_evidence(record, reviews=reviews)
    joint = public.InitialJointSupportReview('review.contributions.joint', record.case, record.context,
        record.state_selection, record.realization_id, record.dependence_group_id, record.support_kind,
        tuple(c.bounds for c in contrasts), (E.of(0),E.of(1)),
        tuple(sorted((source.identity,record.identity,*(r.identity for r in reviews)), key=lambda p:p.object_id)),
        'Disclosed simultaneous test input, not scientific evidence.', A.SATISFIED, ())
    point = public.InitialJointRealization(record.realization_id, record.dependence_group_id, joint.identity,
        record.support_kind, contrasts, (E.of(0),E.of(1)), None)
    alternative = public.InitialChemicalAlternative(record.alternative_id, (record.realization_id,), (point,), 'AVAILABLE', ())
    case = selected.cases[0]
    supplied = public.InitialCaseEvidence(case.case_id, case.case.identity, case.context.identity, case.state_selection, (alternative,))
    return public.InitialModelEvidence('evidence.contributions.control', selected.identity, (supplied,)), (source,record,*reviews,joint)


def test_minimal_ratios_reconstruct_complete_closure_and_ignore_unused_oxygen_clock():
    wt = FourStateRates(*(D(v) for v in (3, 2, 5, 2, 6, 7, 4, 8)))
    baseline = None
    # Changes to each oxygen processing clock and formation reversal leave the
    # requested limiting endpoints invariant, while changing unused endpoints.
    oxygen_turnovers = set()
    for scale,b in product((D('.125'),D(1),D(64)), (D(0),D(999))):
        mutant = FourStateRates(D(9),b,D(15),D(4),D(12)*scale,D(14),D(12),D(24)*scale)
        p,q = wt.fractions, mutant.fractions
        pcw,pcm = p['r_c']/(p['r_c']+p['d_c']),q['r_c']/(q['r_c']+q['d_c'])
        pow_,pom = p['r_o']/(p['r_o']+p['d_o']),q['r_o']/(q['r_o']+q['d_o'])
        vals = (q['a']/p['a'], (q['c']/q['o'])/(p['c']/p['o']), pcm/pcw,
            (p['r_c']+p['d_c'])/(q['r_c']+q['d_c']), pom/pow_)
        _,_,record = contributions(vals)
        ratios = {k:fraction(v['ratio_bounds'][0]) for k,v in public.read_initial_contributions(record)['contrasts'].items()}
        wc,mc = intrinsic_constants(wt),intrinsic_constants(mutant)
        w = p['r_c']/(p['a']+p['r_c'])
        assert F(1)/(w/ratios['a']+(1-w)/ratios['r_c']) == mc.kcat_c.fraction/wc.kcat_c.fraction
        assert ratios['c_over_o']*ratios['chi_c_over_chi_o'] == mc.specificity.fraction/wc.specificity.fraction
        assert ratios == baseline or baseline is None
        baseline = ratios
        oxygen_turnovers.add(mc.kcat_o.fraction)
    assert len(oxygen_turnovers) == 3


@pytest.mark.parametrize('missing,blocked', [
    ('formation',('turnover',)), ('addition_discrimination',('specificity',)),
    ('carbon_commitment',('turnover','specificity')), ('carbon_exit_time',('turnover',)),
    ('oxygen_commitment',('specificity',)),
])
def test_missing_contribution_only_blocks_affected_endpoints(tmp_path, missing, blocked):
    values = [F(2),F(3,2),F(4,3),F(1,2),F(2,3)]
    values[CONTRIBUTION_ORDER.index(missing)] = None
    selected,source,record = contributions(tuple(values))
    evidence,records = model_evidence(selected,source,record)
    sources = publish_sources(_plane(tmp_path/'originals'),records)
    report = public.read_initial_model_sources(selection=selected,evidence=evidence,sources=sources)
    row = report['cases'][selected.cases[0].case_id]
    for name,value in row['endpoints'].items():
        assert value['conditional_criterion'] == ('UNEVALUABLE' if name in blocked else 'FAVOURABLE')
    assert report['new_native_calls'] == 0


def test_shared_carbon_commitment_is_one_original_operand_and_changes_both_contrasts():
    _,_,original = contributions()
    changed = replace(original, contributions=tuple(
        replace(c,bounds=(E.of(F(2,3)),)*2) if c.quantity=='carbon_commitment' else c for c in original.contributions))
    before,after = (public.read_initial_contributions(r) for r in (original,changed))
    assert before['shared_contributions'] == {'carbon_commitment':('r_c','chi_c_over_chi_o')}
    for key in ('r_c','chi_c_over_chi_o'):
        assert fraction(after['contrasts'][key]['ratio_bounds'][0]) == fraction(before['contrasts'][key]['ratio_bounds'][0])/2
    for key in ('a','c_over_o'):
        assert after['contrasts'][key] == before['contrasts'][key]


def test_joint_enclosure_uses_outward_quotient_extrema_without_new_coverage():
    bounds = ((F(1),F(2)), (F(1,2),F(3)), (F(2,3),F(4,3)), (F(1,2),F(5,2)), (F(1,4),F(3,2)))
    with localcontext() as context:
        context.prec = 2
        _,_,record = contributions(bounds,intervals=True)
        report = public.read_initial_contributions(record)
    for values in product(*bounds):
        _,_,point = contributions(values)
        projected = public.read_initial_contributions(point)
        for name,value in projected['contrasts'].items():
            lo,hi = map(fraction,report['contrasts'][name]['ratio_bounds'])
            assert lo <= fraction(value['ratio_bounds'][0]) <= hi
    assert 'NO_NEW_COVERAGE' in report['interval_interpretation']
    assert public.initial_contrast_evidence(record)[0].conditionally_supported is False


@pytest.mark.parametrize('mutation', ('values','dependence','state','alternative','source','missing'))
def test_guarded_reader_reconstructs_original_projection_and_refuses_substitutions(tmp_path, mutation):
    selected,source,record = contributions()
    evidence,records = model_evidence(selected,source,record)
    sources = publish_sources(_plane(tmp_path/'originals'),records)
    assert public.read_initial_model_sources(selection=selected,evidence=evidence,sources=sources)['all_requested_endpoints_evaluable']
    point = evidence.cases[0].alternatives[0].realizations[0]
    if mutation == 'dependence':
        point = replace(point,dependence_group_id='changed.dependence')
    elif mutation in ('values','source','missing'):
        contrast = point.contrasts[1]
        if mutation == 'values':
            contrast = replace(contrast,bounds=(E.of(99),)*2)
        elif mutation == 'source':
            contrast = replace(contrast,sources=tuple(p for p in contrast.sources if p!=source.identity))
        else:
            contrast = replace(contrast,evidence_kind='UNIDENTIFIED',bounds=None,unresolved_requirement_ids=('missing.changed',))
        point = replace(point,contrasts=(point.contrasts[0],contrast,*point.contrasts[2:]))
    else:
        # An altered original record needs new source bytes and therefore a new
        # identity. Retain that changed source explicitly in a fresh custody.
        record = replace(record,**({'state_selection':selected.cases[0].case.identity} if mutation=='state'
            else {'alternative_id':'chemical.unselected'}))
        old_record = records[1]
        point = replace(point,contrasts=tuple(replace(c,sources=tuple(sorted(
            (record.identity if p==old_record.identity else p for p in c.sources),key=lambda p:p.object_id))) for c in point.contrasts))
        sources=publish_sources(_plane(tmp_path/'changed-originals'),(records[0],record,*records[2:]))
    alternative=replace(evidence.cases[0].alternatives[0],realizations=(point,))
    evidence=replace(evidence,cases=(replace(evidence.cases[0],alternatives=(alternative,)),))
    with pytest.raises(ValueError,match='contribution|original source census'):
        public.read_initial_model_sources(selection=selected,evidence=evidence,sources=sources)


def test_unsupported_invariance_stays_unresolved_and_contracts_preserve_census():
    selected,_,record = contributions()
    oxygen = replace(record.contributions[-1], bounds=(E.of(1),)*2, evidence_kind='IMPOSED_ASSUMPTION',
        unresolved_requirement_ids=('missing.oxygen-mutation-effect',))
    record=replace(record,contributions=(*record.contributions[:-1],oxygen))
    contrast=public.initial_contrast_evidence(record)[-1]
    assert contrast.evidence_kind=='IMPOSED_ASSUMPTION' and not contrast.conditionally_supported
    assert 'missing.oxygen-mutation-effect' in contrast.unresolved_requirement_ids
    assert decode_canonical_bytes(record.canonical_bytes(),type(record),maximum_bytes=2**20)==record
    with pytest.raises(ValueError,match='five quantities'):
        replace(record,contributions=record.contributions[:-1])
    with pytest.raises(ValueError,match='paired quantity census'):
        replace(oxygen,quantity='oxygen_exit_time')
    with pytest.raises(ValueError,match='chemical alternative'):
        public.prepare_initial_contribution_realization(case=selected.cases[0],alternative_id='chemical.other',
            realization_id=record.realization_id,dependence_group_id=record.dependence_group_id,
            support_kind=record.support_kind,contributions=record.contributions)
