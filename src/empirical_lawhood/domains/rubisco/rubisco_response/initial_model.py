# SPDX-License-Identifier: MPL-2.0
"""Read exact four-contrast support without inventing microscopic rates.

Every chemical alternative, failed realization and missing endpoint survives.
Joint regions are enclosed monotonically; samples remain samples, and are not
promoted to confidence coverage or to a continuous physical support region.
"""

from fractions import Fraction
from itertools import product

from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import ENDPOINT_DEPENDENCIES, validate_initial_model_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialContrastReview, InitialJointSupportReview
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import PairedEffectiveRateRatios, bound_paired_endpoints
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds_assessment import assess_endpoint_enclosure
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational


def required_initial_sources(selection, evidence):
    """The complete source census includes failed and presently unused findings."""
    validate_initial_model_inputs(selection, evidence)
    pins = set(selection.source_evidence)
    for case in evidence.cases:
        for alternative in case.alternatives:
            for realization in alternative.realizations:
                pins.add(realization.joint_support_source)
                if realization.waiting_fraction_evidence is not None:
                    pins.add(realization.waiting_fraction_evidence)
                for contrast in realization.contrasts:
                    pins.update(contrast.sources)
    by_id = {}
    for pin in pins:
        if pin.object_id in by_id and by_id[pin.object_id] != pin:
            raise ValueError('initial source label aliases different original canonical records')
        by_id[pin.object_id] = pin
    return tuple(sorted(pins, key=lambda p:p.object_id))


def _criterion(bounds, endpoint):
    if bounds is None:
        return 'UNEVALUABLE'
    low, high = bounds
    if endpoint == 'turnover':
        return 'FAVOURABLE' if low > 1 else 'ADVERSE' if high <= 1 else 'INCONCLUSIVE'
    return 'FAVOURABLE' if low >= 1 else 'ADVERSE' if high < 1 else 'INCONCLUSIVE'


def _extrema(realization, endpoint):
    rows = {c.contrast:c for c in realization.contrasts}
    names = dict(ENDPOINT_DEPENDENCIES)[endpoint]
    if any(rows[name].bounds is None for name in names):
        return None, ()
    support = tuple(tuple(v.fraction for v in rows[name].bounds) for name in names)
    if endpoint == 'specificity':
        bounds = (support[0][0]*support[1][0], support[0][1]*support[1][1])
        # Independent multiplicative balance at each positive extremal corner.
        residuals = tuple(bound-a*b for bound,a,b in zip(bounds,*support,strict=True))
        return bounds, residuals
    qa, qr = support
    waiting = tuple(v.fraction for v in realization.wild_type_formation_wait_fraction)
    corners = tuple((Fraction(1)/(w/a+(1-w)/r),a,r,w) for a,r,w in product(qa,qr,waiting))
    lower, upper = min(corners,key=lambda row:row[0]), max(corners,key=lambda row:row[0])
    # Monotonicity in both positive rates and constant derivative sign in w
    # reduce the entire rectangular enclosure to its finite endpoint balances.
    residuals = tuple(value*(w*r+(1-w)*a)-a*r for value,a,r,w in (lower,upper))
    return (lower[0],upper[0]), residuals


def _complete_corner_controls(case, realization, closure_source):
    """Reuse both existing owners on complete corners, with no placeholder rates."""
    if any(c.bounds is None for c in realization.contrasts):
        return ()
    findings = []
    for number, values in enumerate(product(*(tuple(dict.fromkeys(c.bounds)) for c in realization.contrasts))):
        prefix = realization.realization_id+'.corner.'+str(number)
        source = realization.joint_support_source
        pins = {case.case.identity, case.context.identity, source, closure_source}
        if realization.waiting_fraction_evidence is not None:
            pins.add(realization.waiting_fraction_evidence)
        selected = PairedEffectiveRateRatios('ratios.'+prefix, case.case.identity, case.context.identity,
            *values, realization.wild_type_formation_wait_fraction, (source,)*4,
            realization.waiting_fraction_evidence, closure_source, realization.dependence_group_id,
            tuple(sorted(pins,key=lambda p:p.object_id)), ())
        result = bound_paired_endpoints(selected,case.case,case.context,result_id='endpoint.'+prefix)
        checked = assess_endpoint_enclosure(selected,result,case.case,case.context,assessment_id='assessment.'+prefix)
        findings.append(dict(contrasts=tuple(rational(v.fraction) for v in values),
            turnover=tuple(rational(v.fraction) for v in result.turnover_ratio_bounds),
            specificity=rational(result.specificity_ratio.fraction),
            numerical_disposition=checked.numerical_disposition.value,
            balance_residuals=tuple(rational(v.fraction) for v in (*checked.bound_balance_residuals,checked.specificity_balance_residual))))
    return tuple(findings)


def _supported_review(case, contrast, reviews):
    if not contrast.conditionally_supported:
        return False
    review=reviews.get(contrast.applicability_review)
    if review is None:
        return False
    exact(review,InitialContrastReview)
    if ((review.case,review.context,review.state_selection,review.contrast) !=
            (case.case.identity,case.context.identity,case.state_selection,contrast.contrast)
            or not set(review.supporting_sources).issubset(contrast.sources)
            or review.covered_bounds != contrast.bounds):
        raise ValueError('initial contrast review substitutes its actual context, support, sources or mutation quantity')
    return review.conditional_support.value=='SATISFIED'


def _joint_review(case, realization, reviews):
    review=reviews.get(realization.joint_support_source)
    if review is None:
        return False
    exact(review,InitialJointSupportReview)
    if ((review.case,review.context,review.state_selection,review.realization_id,review.dependence_group_id,
            review.support_kind,review.covered_contrasts,review.waiting_fraction) !=
            (case.case.identity,case.context.identity,case.state_selection,realization.realization_id,realization.dependence_group_id,
            realization.support_kind,tuple(c.bounds for c in realization.contrasts),realization.wild_type_formation_wait_fraction)):
        raise ValueError('joint support review substitutes the original case, region, dependence or waiting interval')
    required={c.applicability_review for c in realization.contrasts if c.conditionally_supported}
    if not required.issubset(review.supporting_sources):
        raise ValueError('joint support review drops its actual contrast reviews')
    return review.conditional_support.value=='SATISFIED'


def _realization(case, alternative, realization, reviews, joint_reviews, closure_source):
    result = dict(realization_id=realization.realization_id,
        dependence_group_id=realization.dependence_group_id, support_kind=realization.support_kind,
        joint_support_source=realization.joint_support_source.to_document(),
        contrasts=tuple(c.to_document() for c in realization.contrasts),
        waiting_fraction=tuple(rational(v.fraction) for v in realization.wild_type_formation_wait_fraction),
        endpoints={}, independent_corner_controls=_complete_corner_controls(case,realization,closure_source))
    rows = {c.contrast:c for c in realization.contrasts}
    for endpoint,names in ENDPOINT_DEPENDENCIES:
        bounds,residuals = _extrema(realization,endpoint)
        remaining = set(case.unresolved_requirement_ids) | set(alternative.unresolved_requirement_ids)
        if not _joint_review(case,realization,joint_reviews):
            remaining.add('requirement.'+realization.realization_id+'.assessed-joint-support')
        for name in names:
            row=rows[name]
            remaining.update(row.unresolved_requirement_ids)
            if not _supported_review(case,row,reviews):
                remaining.add('requirement.'+case.case_id+'.'+alternative.alternative_id+'.'+name+'.supported-mutation-contrast')
        arithmetic = _criterion(bounds,endpoint)
        result['endpoints'][endpoint] = dict(
            ratio_bounds=None if bounds is None else tuple(rational(v) for v in bounds),
            arithmetic_criterion=arithmetic,
            conditional_criterion=arithmetic if not remaining else 'UNEVALUABLE',
            remaining_requirement_ids=tuple(sorted(remaining)),
            balance_residuals=tuple(rational(v) for v in residuals),
            numerical_disposition='UNEVALUABLE' if bounds is None else 'SATISFIED' if all(v==0 for v in residuals) else 'FALSIFIED',
            interpretation='ONE_DECLARED_JOINT_REALIZATION_OR_REGION_WITH_SELECTED_CLOSURE')
    return result


def _aggregate(endpoint_rows, *, complete, samples=False):
    available = tuple(row for row in endpoint_rows if row['ratio_bounds'] is not None)
    def value(row):
        return Fraction(row['numerator'],row['denominator'])
    bounds = (min(value(row['ratio_bounds'][0]) for row in available),
        max(value(row['ratio_bounds'][1]) for row in available)) if available else None
    statuses = tuple(row['conditional_criterion'] for row in endpoint_rows)
    # A universally adverse interval is still retained when another alternative
    # is unavailable; the missing alternative prevents a complete case forecast.
    if not complete or not statuses or 'UNEVALUABLE' in statuses or samples:
        status='UNEVALUABLE'
    elif all(s=='FAVOURABLE' for s in statuses):
        status='FAVOURABLE'
    elif all(s=='ADVERSE' for s in statuses):
        status='ADVERSE'
    else:
        status='INCONCLUSIVE'
    return dict(conditional_criterion=status,
        available_support_envelope=None if bounds is None else tuple(rational(v) for v in bounds),
        complete_support_envelope=None if not complete or samples or 'UNEVALUABLE' in statuses else tuple(rational(v) for v in bounds),
        criterion_counts={s:statuses.count(s) for s in ('FAVOURABLE','ADVERSE','INCONCLUSIVE','UNEVALUABLE')},
        assigned_realizations=len(endpoint_rows),
        sampled_support_only=samples,
        confidence_coverage='NOT_INFERRED')


def read_initial_model(*, selection, evidence, reviews=(), joint_reviews=()):
    """Pure independent endpoint analysis; the API owns actual source custody."""
    validate_initial_model_inputs(selection,evidence)
    if type(reviews) is not tuple:
        raise TypeError('initial reader requires exact original review records')
    for review in reviews:
        exact(review,InitialContrastReview)
    if len({r.identity for r in reviews})!=len(reviews):
        raise ValueError('initial reader duplicates a scientific review')
    reviews={r.identity:r for r in reviews}
    expected_reviews={c.applicability_review for case in evidence.cases for a in case.alternatives
        for r in a.realizations for c in r.contrasts if c.applicability_review is not None}
    if not set(reviews).issubset(expected_reviews):
        raise ValueError('initial reader adds an unselected scientific review')
    if type(joint_reviews) is not tuple:
        raise TypeError('initial reader requires exact original joint-support reviews')
    for review in joint_reviews:
        exact(review,InitialJointSupportReview)
    if len({r.identity for r in joint_reviews})!=len(joint_reviews):
        raise ValueError('initial reader duplicates a joint-support review')
    joint_reviews={r.identity:r for r in joint_reviews}
    expected_joint={r.joint_support_source for c in evidence.cases for a in c.alternatives for r in a.realizations}
    if not set(joint_reviews).issubset(expected_joint):
        raise ValueError('initial reader adds an unselected joint-support review')
    report=dict(selection=selection.identity.to_document(),evidence=evidence.identity.to_document(),
        interpretation=selection.interpretation,closure=selection.closure,
        closure_assumptions=selection.closure_assumptions,criteria=dict(turnover='> 1',specificity='>= 1'),
        omitted_absolute_operands=('WT_WAITING_TIME_SPLIT_WITH_FULL_0_TO_1_ENCLOSURE',
            'FORMATION_REVERSAL_b_ONLY_IN_SELECTED_LIMITING_ENDPOINT_CLOSURE'),
        biological_predictive_validity='UNEVALUABLE',new_native_calls=0,independent_biological_units=0,cases={})
    for case,supplied in zip(selection.cases,evidence.cases,strict=True):
        alternatives=[]
        all_rows=[]
        complete=True
        samples=False
        remaining=set(case.unresolved_requirement_ids)
        for alternative in supplied.alternatives:
            rows=tuple(_realization(case,alternative,realization,reviews,joint_reviews,selection.closure_source) for realization in alternative.realizations)
            all_rows.extend(rows)
            complete &= alternative.original_state=='AVAILABLE'
            samples |= any(r.support_kind=='JOINT_SAMPLE' for r in alternative.realizations)
            remaining.update(alternative.unresolved_requirement_ids)
            for row in rows:
                for endpoint in row['endpoints'].values():
                    remaining.update(endpoint['remaining_requirement_ids'])
            alternatives.append(dict(alternative_id=alternative.alternative_id,
                original_state=alternative.original_state,expected_realization_ids=alternative.expected_realization_ids,
                realizations=rows,remaining_requirement_ids=alternative.unresolved_requirement_ids))
        endpoints={name:_aggregate(tuple(r['endpoints'][name] for r in all_rows),complete=complete,samples=samples)
            for name,_ in ENDPOINT_DEPENDENCIES}
        statuses=tuple(v['conditional_criterion'] for v in endpoints.values())
        joint=('UNEVALUABLE' if 'UNEVALUABLE' in statuses else 'ADVERSE' if 'ADVERSE' in statuses
            else 'FAVOURABLE' if all(s=='FAVOURABLE' for s in statuses) else 'INCONCLUSIVE')
        report['cases'][case.case_id]=dict(case=case.case.identity.to_document(),context=case.context.identity.to_document(),
            processing_view=case.case.parent.processing_view,exposure_group=case.case.exposure_group,
            focal_site_id=case.focal_site_id,chemical_alternatives=tuple(alternatives),endpoints=endpoints,
            joint_owner_criterion=joint,remaining_requirement_ids=tuple(sorted(remaining)),
            dependency_map=tuple(d.to_document() for d in case.dependencies),
            population_weights='NOT_INFERRED',physical_rate_admission='UNEVALUABLE')
    report['all_requested_endpoints_evaluable']=all(row['joint_owner_criterion']!='UNEVALUABLE' for row in report['cases'].values())
    all_quantities={q for c in selection.cases for d in c.dependencies for q in d.targeted_quantities}
    remaining_quantities=set()
    for case,supplied in zip(selection.cases,evidence.cases,strict=True):
        for dependency in case.dependencies:
            missing=bool(case.unresolved_requirement_ids)
            for alternative in supplied.alternatives:
                missing |= alternative.original_state!='AVAILABLE' or bool(alternative.unresolved_requirement_ids)
                for realization in alternative.realizations:
                    contrast=next(c for c in realization.contrasts if c.contrast==dependency.contrast)
                    missing |= (not _supported_review(case,contrast,reviews)
                        or not _joint_review(case,realization,joint_reviews) or realization.support_kind=='JOINT_SAMPLE')
            if missing:
                remaining_quantities.update(dependency.targeted_quantities)
    report['required_quantity_ids']=tuple(sorted(all_quantities))
    report['remaining_quantity_ids']=tuple(sorted(remaining_quantities))
    return report


def empty_initial_evidence(selection, *, evidence_id):
    """Derive the complete missing census from the selected model, not hand rosters."""
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialCaseEvidence, InitialChemicalAlternative, InitialModelEvidence
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialModelSelection
    exact(selection,InitialModelSelection)
    cases=tuple(InitialCaseEvidence(c.case_id,c.case.identity,c.context.identity,c.state_selection,
        tuple(InitialChemicalAlternative(name,(),(),'UNKNOWN',
            ('requirement.'+c.case_id+'.'+name+'.joint-mutation-contrasts',)) for name in c.expected_alternative_ids))
        for c in selection.cases)
    return InitialModelEvidence(evidence_id,selection.identity,cases)
