# SPDX-License-Identifier: MPL-2.0
"""Joint root decisions, precise missing requirements and independent checks.

The historical endpoint reader remains the single owner of source/support
interpretation and endpoint enclosures. This method adds the selected logical
quantifiers and exact waiting-fraction decisions without changing that reader.
"""

from dataclasses import replace
from fractions import Fraction

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import read_initial_model, required_initial_sources
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import ENDPOINT_DEPENDENCIES, validate_initial_model_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAlternative, InitialRootAssessment, InitialRootCase, InitialRootEndpoint, InitialRootRealization, InitialRootRequest, InitialRootResult, InitialWaitingCondition
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


UNIFORM = 'UNIFORM_PHYSICAL_CONCLUSION'
ROBUST = 'ROBUST_FOR_EVERY_SELECTED_ALTERNATIVE'


def prepare_initial_root(*, model, alternative_policy=UNIFORM, processing_policy=UNIFORM, domain_limits=()):
    """Bind the unchanged initial selection and explicit aggregation policies."""
    selected = InitialRootRequest('initial-root.pending', model.identity, alternative_policy,
        processing_policy, domain_limits)
    return replace(selected, request_id='initial-root-request.' + selected.fingerprint())


def validate_initial_root_inputs(request, selection, evidence):
    exact(request, InitialRootRequest)
    validate_initial_model_inputs(selection, evidence)
    if request.model != selection.identity:
        raise ValueError('initial root substitutes its original model or consumer selection')
    cases = {row.case_id: row for row in selection.cases}
    sources = set(required_initial_sources(selection, evidence))
    supplied = {row.case_id: row for row in evidence.cases}
    for limit in request.domain_limits:
        if limit.case_id not in cases or limit.alternative_id not in cases[limit.case_id].expected_alternative_ids:
            raise ValueError('initial root domain limitation changes the complete original case/alternative census')
        if limit.original_source is not None and limit.original_source not in sources:
            raise ValueError('initial root domain limitation names an unauthenticated original source')
        alternative = next(row for row in supplied[limit.case_id].alternatives
            if row.alternative_id == limit.alternative_id)
        if any(contrast.bounds is not None for row in alternative.realizations
                for contrast in row.contrasts if contrast.contrast == limit.contrast):
            raise ValueError('initial root domain limitation contradicts supplied positive ratio bounds')


def _fraction(value):
    return Fraction(value['numerator'], value['denominator'])


def _endpoint(name, row):
    return InitialRootEndpoint(name,
        None if row['ratio_bounds'] is None else tuple(Exact.of(_fraction(v)) for v in row['ratio_bounds']),
        row['arithmetic_criterion'], row['conditional_criterion'], row['remaining_requirement_ids'],
        tuple(Exact.of(_fraction(v)) for v in row['balance_residuals']))


def _conjunction(statuses):
    if 'ADVERSE' in statuses:
        return 'CONTRADICTED'
    if all(value == 'FAVOURABLE' for value in statuses):
        return 'SUPPORTED'
    return 'UNRESOLVED'


def _aggregate(outcomes, policy):
    if not outcomes:
        return 'UNRESOLVED'
    if policy == ROBUST and 'CONTRADICTED' in outcomes:
        return 'CONTRADICTED'
    if all(value == 'SUPPORTED' for value in outcomes):
        return 'SUPPORTED'
    if all(value == 'CONTRADICTED' for value in outcomes):
        return 'CONTRADICTED'
    return 'UNRESOLVED'


def _waiting_condition(qa, qr, comparison):
    a, r = qa.fraction, qr.fraction
    coefficient, rhs = 1/a - 1/r, 1 - 1/r
    if coefficient == 0:
        satisfied = rhs > 0 if comparison == 'LT' else rhs <= 0
        relation, threshold = ('ALL' if satisfied else 'NONE'), None
    else:
        relation = ('LT' if coefficient > 0 else 'GT') if comparison == 'LT' else ('GE' if coefficient > 0 else 'LE')
        threshold = Exact.of(rhs/coefficient)
    return InitialWaitingCondition(qa, qr, Exact.of(coefficient), Exact.of(rhs), comparison, relation, threshold)


def _precision_requirements(case, alternative, realization, endpoints, *, sample, limits):
    remaining = {row.requirement_id for row in limits}
    prefix = 'requirement.' + case.case_id + '.' + alternative.alternative_id + '.' + realization.realization_id
    if sample:
        remaining.add(prefix + '.simultaneous-support-coverage')
    for endpoint in endpoints:
        if endpoint.conditional_criterion != 'FAVOURABLE':
            remaining.update(endpoint.remaining_requirement_ids)
        if endpoint.conditional_criterion == 'INCONCLUSIVE':
            suffix = 'waiting-fraction-or-ratio-decision-margin' if endpoint.endpoint == 'turnover' else 'joint-product-decision-margin'
            remaining.add(prefix + '.' + suffix)
    return tuple(sorted(remaining))


def _realization(case, alternative, original, historical, limits, joint, waiting):
    endpoints = tuple(_endpoint(name, historical['endpoints'][name]) for name, _ in ENDPOINT_DEPENDENCIES)
    endpoints = tuple(replace(endpoint, conditional_criterion='UNEVALUABLE',
        remaining_requirement_ids=tuple(sorted(set(endpoint.remaining_requirement_ids) | {
            limit.requirement_id for limit in limits
            if limit.contrast in dict(ENDPOINT_DEPENDENCIES)[endpoint.endpoint]})))
        if any(limit.contrast in dict(ENDPOINT_DEPENDENCIES)[endpoint.endpoint] for limit in limits)
        else endpoint for endpoint in endpoints)
    statuses = tuple(row.conditional_criterion for row in endpoints)
    diagnostic = joint(statuses)
    sample = original.support_kind == 'JOINT_SAMPLE'
    outcome = 'UNRESOLVED' if sample else diagnostic
    decisive = tuple(sorted(row.endpoint for row in endpoints if row.conditional_criterion == 'ADVERSE'))
    if outcome != 'CONTRADICTED':
        decisive = ()
    remaining = (() if outcome != 'UNRESOLVED' else
        _precision_requirements(case, alternative, original, endpoints, sample=sample, limits=limits))
    contrasts = {row.contrast: row for row in original.contrasts}
    qa, qr = contrasts['a'].bounds, contrasts['r_c'].bounds
    support = contradiction = None
    omitted = set()
    if qa is not None and qr is not None and not sample and endpoints[0].conditional_criterion != 'UNEVALUABLE':
        support = waiting(qa[0], qr[0], 'LT')
        contradiction = waiting(qa[1], qr[1], 'GE')
        if (not sample and endpoints[0].conditional_criterion in ('FAVOURABLE', 'ADVERSE')
                and (min(qa[0].fraction, qr[0].fraction) > 1 or max(qa[1].fraction, qr[1].fraction) <= 1)):
            omitted.add('wild-type-waiting-fraction')
    if decisive:
        # One sufficient adverse endpoint closes the conjunction. Preserve the
        # other endpoint's original missing data even when acquisition is omitted.
        proof_endpoint = 'turnover' if 'turnover' in decisive else 'specificity'
        unnecessary = 'specificity' if proof_endpoint == 'turnover' else 'turnover'
        omitted.update('contrast.' + name for name in dict(ENDPOINT_DEPENDENCIES)[unnecessary])
        if unnecessary == 'turnover':
            omitted.add('wild-type-waiting-fraction')
    return InitialRootRealization(original.realization_id, original.dependence_group_id, original.support_kind,
        endpoints, outcome, diagnostic, decisive, support, contradiction, tuple(sorted(omitted)), remaining)


def _build(request, selection, evidence, historical, *, result_id, joint, aggregate, waiting):
    cases = []
    original_requirements = set()
    for case, supplied in zip(selection.cases, evidence.cases, strict=True):
        original_case = historical['cases'][case.case_id]
        original_requirements.update(original_case['remaining_requirement_ids'])
        alternatives = []
        for alternative, historical_alternative in zip(supplied.alternatives, original_case['chemical_alternatives'], strict=True):
            limits = tuple(row for row in request.domain_limits
                if (row.case_id, row.alternative_id) == (case.case_id, alternative.alternative_id))
            rows = tuple(_realization(case, alternative, original, current, limits, joint, waiting)
                for original, current in zip(alternative.realizations, historical_alternative['realizations'], strict=True))
            outcome = aggregate(tuple(row.joint_outcome for row in rows), request.alternative_policy)
            remaining = set(case.unresolved_requirement_ids) | set(alternative.unresolved_requirement_ids)
            remaining.update(row.requirement_id for row in limits)
            if alternative.original_state != 'AVAILABLE':
                outcome = 'UNRESOLVED'
            if not rows:
                remaining.update('requirement.' + case.case_id + '.' + alternative.alternative_id + '.contrast.' + name
                    for name in dict(ENDPOINT_DEPENDENCIES)['turnover'] + dict(ENDPOINT_DEPENDENCIES)['specificity'])
            if outcome == 'UNRESOLVED':
                remaining.update(value for row in rows for value in row.decision_requirement_ids)
                if rows and not remaining:
                    remaining.add('requirement.' + case.case_id + '.' + alternative.alternative_id
                        + '.joint-support-decision-margin')
            else:
                remaining.clear()
            alternatives.append(InitialRootAlternative(alternative.alternative_id, alternative.original_state,
                rows, outcome, tuple(sorted(remaining))))
        outcome = aggregate(tuple(row.joint_outcome for row in alternatives), request.alternative_policy)
        remaining = tuple(sorted({value for row in alternatives for value in row.decision_requirement_ids})) if outcome == 'UNRESOLVED' else ()
        if outcome == 'UNRESOLVED' and not remaining:
            remaining = ('requirement.' + case.case_id + '.physical-alternative-resolution',)
        cases.append(InitialRootCase(case.case_id, case.case.identity, case.context.identity, case.state_selection,
            case.case.parent.processing_view, tuple(alternatives), outcome, remaining))
    outcome = aggregate(tuple(row.joint_outcome for row in cases), request.processing_policy)
    remaining = tuple(sorted({value for row in cases for value in row.decision_requirement_ids})) if outcome == 'UNRESOLVED' else ()
    if outcome == 'UNRESOLVED' and not remaining:
        remaining = ('requirement.' + request.request_id + '.processing-view-resolution',)
    original_requirements.update(row.requirement_id for row in request.domain_limits)
    return InitialRootResult(result_id, request.identity, selection.identity, evidence.identity, tuple(cases),
        outcome, remaining, tuple(sorted(original_requirements)))


def calculate_initial_root(*, request, selection, evidence, reviews=(), joint_reviews=()):
    """Calculate the new request from the unchanged historical endpoint owner."""
    validate_initial_root_inputs(request, selection, evidence)
    historical = read_initial_model(selection=selection, evidence=evidence, reviews=reviews, joint_reviews=joint_reviews)
    candidate = _build(request, selection, evidence, historical, result_id='initial-root-result.pending',
        joint=_conjunction, aggregate=_aggregate, waiting=_waiting_condition)
    return replace(candidate, result_id='initial-root-result.' + candidate.fingerprint())


def _truth_outcome(possible):
    return {(True,): 'SUPPORTED', (False,): 'CONTRADICTED', (False, True): 'UNRESOLVED'}[tuple(sorted(possible))]


def _assessed_conjunction(statuses):
    # Enumerate possible truth values. No producer decision function is used.
    possibilities = {'FAVOURABLE': {True}, 'ADVERSE': {False}, 'INCONCLUSIVE': {False, True}, 'UNEVALUABLE': {False, True}}
    truth = {True}
    for value in statuses:
        truth = {left and right for left in truth for right in possibilities[value]}
    return _truth_outcome(truth)


def _assessed_aggregation(outcomes, policy):
    possibilities = {'SUPPORTED': {True}, 'CONTRADICTED': {False}, 'UNRESOLVED': {False, True}}
    if not outcomes:
        return 'UNRESOLVED'
    if policy == UNIFORM:
        return _truth_outcome(set().union(*(possibilities[value] for value in outcomes)))
    truth = {True}
    for value in outcomes:
        truth = {left and right for left in truth for right in possibilities[value]}
    return _truth_outcome(truth)


def _assessed_waiting(qa, qr, comparison):
    # Cross-multiply by positive a*r, independently of the producer's reciprocal
    # subtraction: w*(r-a) < a*(r-1), with the opposite inclusive inequality.
    a, r = qa.fraction, qr.fraction
    difference, boundary = r-a, a*(r-1)
    if difference == 0:
        all_values = (boundary > 0) if comparison == 'LT' else (boundary <= 0)
        relation, threshold = ('ALL' if all_values else 'NONE'), None
    else:
        relation = {('LT', True): 'LT', ('LT', False): 'GT', ('GE', True): 'GE', ('GE', False): 'LE'}[
            comparison, difference > 0]
        threshold = Exact.of(boundary/difference)
    return InitialWaitingCondition(qa, qr, Exact.of(difference/(a*r)), Exact.of(boundary/(a*r)),
        comparison, relation, threshold)


def assess_initial_root(*, request, selection, evidence, result, reviews=(), joint_reviews=()):
    """Reconstruct original endpoints and independently check the new decisions.

Shared traversal/record assembly is reused. Logical truth sets and exact
cross-multiplied threshold equations are separate from the producer's rules.
"""
    validate_initial_root_inputs(request, selection, evidence)
    exact(result, InitialRootResult)
    if (result.request, result.model, result.inputs) != (request.identity, selection.identity, evidence.identity):
        raise ValueError('initial root assessor substitutes the exact consumer, model or input evidence')
    historical = read_initial_model(selection=selection, evidence=evidence, reviews=reviews, joint_reviews=joint_reviews)
    expected = _build(request, selection, evidence, historical, result_id=result.result_id,
        joint=_assessed_conjunction, aggregate=_assessed_aggregation, waiting=_assessed_waiting)
    findings = () if result == expected else ('ORIGINAL_ENDPOINT_OR_JOINT_DECISION_RECONSTRUCTION_MISMATCH',)
    if any(value.fraction for case in expected.cases for alternative in case.alternatives
            for realization in alternative.realizations for endpoint in realization.endpoints
            for value in endpoint.balance_residuals):
        findings += ('INDEPENDENT_ENDPOINT_BALANCE_FALSIFIED',)
    candidate = InitialRootAssessment('initial-root-assessment.pending', request.identity, result.identity,
        A.FALSIFIED if findings else A.SATISFIED, expected.joint_outcome, tuple(sorted(findings)))
    return replace(candidate, assessment_id='initial-root-assessment.' + candidate.fingerprint())
