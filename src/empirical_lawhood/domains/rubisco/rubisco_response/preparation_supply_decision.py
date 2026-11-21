# SPDX-License-Identifier: MPL-2.0
"""Evidence-dependent eligibility within the original finite M50 portfolio."""

from dataclasses import dataclass

from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import PreparationSupplyResult, supply_graph
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import diagnostic_stages, is_environmental, response_stages


@dataclass(frozen=True, slots=True)
class PreparationSupplierEligibility:
    allowed: bool
    consequence: str
    prerequisite_requirement_ids: tuple[str, ...] = ()
    evidence: tuple = ()


def original_supply_results(completed):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_inquiry import actual_products
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    result = []
    for draft, products in completed:
        if draft.operations[0].config_identity.object_schema == PreparationSupplyConfig.SCHEMA:
            result.extend(row[2] for row in actual_products(draft, products))
    return tuple(result)


def latest_response_supply(results):
    """Select the cumulative original evidence, never the favorable finding."""
    selected = tuple(r for r in results if r.selection.response is not None)
    if not selected:
        return None
    def entered(result):
        return {c.effect: (c.point, c.original_readout) for c in result.selection.response.coverage if c.original_readout is not None}
    coverage = [(r, entered(r)) for r in selected]
    for left, a in coverage:
        for right, b in coverage:
            if any(a[key] != b[key] for key in a.keys() & b.keys()):
                raise ValueError('local response history substitutes an already observed original effect')
    maximal = {r.selection.response.identity: r for r, a in coverage if all(b.keys() <= a.keys() for _, b in coverage)}
    if len(maximal) != 1:
        raise ValueError('local response history has no unique cumulative original assessment')
    return next(iter(maximal.values()))


def assess_supplier_eligibility(*, draft, design, completed):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import continuation_config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import config_types as analysis_config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import supply_owners
    configs, _, _, _ = supply_owners(draft)
    config = configs[0]
    results = original_supply_results(completed)
    for result in results:
        if type(result) is not PreparationSupplyResult or result.selection.design != design:
            raise ValueError('local decision changes the original scientific design')
    if len({tuple(r.identity for r in result.selection.prefixes) for result in results}) > 1:
        raise ValueError('local decision selects between different exposed preparation outcomes')
    pins = tuple(sorted({r.identity for r in results}, key=lambda p: p.object_id))
    if type(config) in (PreparationSupplyConfig, *analysis_config_types()):
        return PreparationSupplierEligibility(True,
            'Independently interpret the retained original operands, including failures, before further physical acquisition.', evidence=pins)
    if type(config) in continuation_config_types():
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import actual_products
        prefix_sources = tuple((d, products) for d, products in completed
            if d.operations[0].config_identity.object_schema in {c.SCHEMA for c in config_types()})
        readouts = {r.identity: r for d, products in prefix_sources
                    for _, name, r, _, _ in actual_products(d, products) if name == 'assessment'}
        consumed = {c.continuation.readout.identity for d, _ in prefix_sources
                    for c in supply_owners(d)[0] if type(c) in continuation_config_types()}
        selected = tuple(c.continuation for c in configs)
        allowed = (not results and any(c.readout.original_result.unit.returned.error is not None for c in selected)
            and all(readouts.get(c.readout.identity) == c.readout and c.readout.identity not in consumed for c in selected))
        return PreparationSupplierEligibility(allowed,
            'Continue only the authenticated remainder before checkpoint admission; reuse every prior complete return and retain restarted electronic initialization.'
            if allowed else 'Retain the original history: continuation requires its unconsumed completed supplier and cannot replace admitted checkpoint operands.',
            evidence=tuple(sorted({c.readout.identity for c in selected}, key=lambda p: p.object_id)))
    if type(config) in config_types():
        previous = any(d.operations[0].config_identity.object_schema in {c.SCHEMA for c in config_types()} for d, _ in completed)
        return PreparationSupplierEligibility(not previous,
            'Retain or recover the original paired prefix; its ten-return allocation cannot be purchased again.' if previous else
            'The retained priority review and frozen design select the first paired prefix, subject to current monetary supervision.', evidence=pins)
    if not results:
        return PreparationSupplierEligibility(False, 'First independently admit the original paired checkpoint contribution.')
    handoff = results[0]
    checkpoint_requirements = tuple(r.requirement_id for r in supply_graph(handoff.selection)[0]
        if '.prefix.' in r.requirement_id)
    if any(a is not A.SATISFIED for _, a in handoff.checkpoint_dispositions):
        return PreparationSupplierEligibility(False, handoff.next_supplier_decision, checkpoint_requirements, pins)
    expected = {r.identity for r in handoff.selection.prefixes}
    if {c.center.original_readout.identity for c in configs} != expected:
        raise ValueError('local response purchase substitutes its independently admitted preparation')
    stage = config.point.effect.stage
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import PreparationResponseConfig, AcceleratedPreparationResponseConfig
    previous_stages = {c.point.effect.stage for d, _ in completed
        if d.operations[0].config_identity.object_schema in {PreparationResponseConfig.SCHEMA, AcceleratedPreparationResponseConfig.SCHEMA}
        for c in supply_owners(d)[0]}
    if stage in previous_stages:
        return PreparationSupplierEligibility(False,
            'Retain or recover the original selected effects; this stage cannot be repurchased under a new label.', checkpoint_requirements, pins)
    latest = latest_response_supply(results)
    if stage == response_stages(design)[0]:
        if (is_environmental(design) and latest is not None
                and latest.selection.response.nomination is not None
                and latest.selection.response.nomination.disposition == 'INVALID_COORDINATE_CORRESPONDENCE'):
            return PreparationSupplierEligibility(False, latest.next_supplier_decision, checkpoint_requirements, pins)
        return PreparationSupplierEligibility(True,
            ('The actual paired checkpoint contribution supplies the eight selected initial primary returns.'
             if is_environmental(design) else
             'The actual paired checkpoint contribution supplies all four selected positions for the twenty-return diagnostic.'),
            checkpoint_requirements, pins)
    if latest is None:
        return PreparationSupplierEligibility(False, 'First independently admit the original diagnostic assessment.', checkpoint_requirements, pins)
    response = latest.selection.response
    if config.diagnostic != response:
        raise ValueError('local response purchase bypasses its latest cumulative original assessment')
    if is_environmental(design):
        nomination = response.nomination
        initial = tuple(c for c in response.coverage if c.stage == 'initial-primary')
        available = (nomination is not None and nomination.disposition == 'AVAILABLE'
            and len(initial) == 8 and all(c.state == 'AVAILABLE' for c in initial))
        if stage == 'environment-diagnostic':
            allowed = (available and all(c.point is None and c.original_readout is None
                for c in response.coverage if c.stage != 'initial-primary') and all(c.state == 'NOT_ENTERED'
                for c in response.coverage if c.stage in ('environment-diagnostic', 'challenge')))
            return PreparationSupplierEligibility(allowed,
                'Acquire the selected later primary and environmental actions with the one frozen initial WT direction.'
                if allowed else response.next_supplier_decision, checkpoint_requirements, pins)
        if not available:
            return PreparationSupplierEligibility(False, response.next_supplier_decision, checkpoint_requirements, pins)
    if stage == 'challenge':
        allowed = (response.questions[0].disposition == 'EMPIRICALLY_CONSISTENT'
            and all(c.state == 'AVAILABLE' for c in response.coverage if c.stage in diagnostic_stages(design))
            and all(c.state == 'NOT_ENTERED' and c.point is None for c in response.coverage if c.stage == 'challenge'))
        return PreparationSupplierEligibility(allowed,
            'A complete empirically consistent diagnostic supports four predictions frozen before their original native reveals.' if allowed else
            response.next_supplier_decision, checkpoint_requirements, pins)
    if stage != 'additional-refinement':
        raise ValueError('local decision enlarges the original response portfolio')
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import _product
    numeric = _product(design.useful_error_hartree_per_bohr, design.numerical_allowance_fraction)
    primary = [q.value for q in response.quantities if q.name == 'primary-receiver-numerical-discrepancy']
    reciprocal = [q.value for q in response.quantities if q.name == 'reciprocal-receiver-discrepancy']
    primary_consistent = len(primary) == 4 and all(v is not None and v <= numeric for v in primary)
    consequential = (any(v is not None and v > numeric for v in reciprocal)
        or response.questions[1].disposition == 'CONSEQUENTIAL_OMITTED_COUPLING')
    unrefined = all(c.state == 'NOT_SELECTED' for c in response.coverage if c.stage == 'additional-refinement')
    relevant = response.next_supplier_decision in {
        'RESOLVE_NUMERICAL_OR_RECIPROCAL_DISCREPANCY_BEFORE_PHYSICAL_ATTRIBUTION',
        'COMPLETE_OR_JUSTIFIABLY_DECLINE_WITHHELD_RESPONSE_WITH_FULL_DENOMINATOR',
        'RETAIN_NAMED_COUPLING_AND_ITS_UNRESOLVED_PHYSICAL_SCOPE',
    }
    allowed = primary_consistent and consequential and unrefined and relevant
    return PreparationSupplierEligibility(allowed,
        'Use at most four returns to test the unresolved additional-direction scale behind the consequential coupling or reciprocal discrepancy.'
        if allowed else 'Decline the optional refinement: it cannot discriminate the consequential limitation from these retained findings. '
        + response.next_supplier_decision, checkpoint_requirements, pins)
