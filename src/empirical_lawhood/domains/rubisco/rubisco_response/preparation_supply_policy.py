# SPDX-License-Identifier: MPL-2.0
"""Finite preparation/response supply decisions below the unresolved original root."""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.science.identity.authority import AuthorityAction
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost, identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryCriterionAssessment, InquiryObservation, InquiryOutcomeMap, InquiryPolicyAssumption, InquiryQuestionKind, InquiryRequirementFinding, InquiryStopScope, InquiryTarget, InquiryTargetFrontier, RobustInquirySpecification, ScientificOutcomeKind
from empirical_lawhood.science.inquiry.recursive_requirements import ConditionRole, ContributionRole, ScientificRequirementSpec
from empirical_lawhood.design.recursive_authoring import SupplierProposal
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import IncomparableResolution, InquiryAlternativeKind, InquiryCriterionRole, InquiryCriterionRule, InquiryOrdering, RobustInquiryMenu, RobustInquiryPolicy, TargetDirectedAlternative

OUTCOMES = {'contradicted': ScientificOutcomeKind.NEGATIVE, 'initial': ScientificOutcomeKind.MISSING,
    'operational-failure': ScientificOutcomeKind.OPERATIONAL_FAILURE, 'supported': ScientificOutcomeKind.POSITIVE,
    'uncertain-contact': ScientificOutcomeKind.UNCERTAIN_CONTACT, 'unresolved': ScientificOutcomeKind.UNEVALUABLE}


def supply_owners(draft):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    if draft.operations and draft.operations[0].config_identity.object_schema == PreparationSupplyConfig.SCHEMA:
        from empirical_lawhood.domains.rubisco.rubisco_response import preparation_supply_inquiry as inquiry
        from empirical_lawhood.domains.rubisco.rubisco_response import preparation_supply_translation as translation
        configs = translation.selected_configs(draft)
        return configs, configs[0].selection.scope, inquiry, translation.supply_input_origins
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_types
    if draft.operations and draft.operations[0].config_identity.object_schema in {c.SCHEMA for c in config_types()}:
        from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_inquiry as inquiry
        from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_translation as translation
        configs = translation.selected_configs(draft)
        return configs, inquiry.prefix_scope(configs), inquiry, translation.prefix_input_origins
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import config_types as analysis_config_types
    if draft.operations and draft.operations[0].config_identity.object_schema in {c.SCHEMA for c in analysis_config_types()}:
        from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_analysis_inquiry as inquiry
        from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_analysis_translation as translation
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope
        configs = translation.selected_configs(draft)
        return configs, response_scope(configs[0].analysis.design), inquiry, translation.analysis_input_origins
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_inquiry as inquiry
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_translation as translation
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope
    configs = translation.selected_configs(draft)
    return configs, response_scope(configs[0].protocol), inquiry, translation.response_input_origins


def supply_design(draft):
    """Read the frozen scientific design through the exact selected family."""
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import config_types as analysis_config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import PreparationResponseConfig, AcceleratedPreparationResponseConfig
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    configs, _, _, _ = supply_owners(draft)
    config = configs[0]
    if type(config) is PreparationSupplyConfig:
        return config.selection.design
    if type(config) in config_types():
        if config.scientific_context is None:
            raise ValueError('rooted preparation requires its actual original scientific context')
        return config.scientific_context.design
    if type(config) in analysis_config_types():
        return config.analysis.design
    if type(config) in (PreparationResponseConfig, AcceleratedPreparationResponseConfig):
        return config.protocol
    raise TypeError('unsupported preparation supplier configuration')


def preparation_supply_specification(draft):
    configs, scope, _, _ = supply_owners(draft)
    operation = draft.operations[0]
    requirement_id = 'requirement.original-preparation-supply.' + draft.fingerprint()
    condition = ScientificRequirementSpec(requirement_id, operation.node_id, ConditionRole.EVIDENTIAL,
        'Supply the complete originally selected local preparation or response operands for independent interpretation.',
        'Every assigned local task retains its original return and independent readout, including explicit unavailable outcomes.',
        scope, operation.node_id, 'An omitted, changed, unreceived or independently rejected original operand.',
        (ContributionRole.RETAINED_ANALYSIS_INPUT,))
    claims = tuple(identity(row, row.claim_id) for row in draft.development_study.claims)
    target = InquiryTarget('target.local-supply.' + draft.fingerprint(), draft.question, scope, (requirement_id,), claims,
        'The exact finite local supply question is assessed. Original root requirements, force uncertainty and kinetic admission remain separate.')
    outcomes = tuple(InquiryOutcomeMap(name, kind,
        tuple(sorted(('hold', 'acquire') if name == 'initial' else ('hold', 'close-question')
            if name in ('supported', 'contradicted') else ('hold',))),
        'Retain original attempts, complete assigned effects and unresolved wider physical requirements.',
        'An independently assessed complete contribution or an explicit justified non-entry changes this local disposition.')
        for name, kind in sorted(OUTCOMES.items()))
    return RobustInquirySpecification('inquiry.local-supply.' + draft.fingerprint(), draft.question, (),
        configs[0].identity, scope, 'Local acquisition supplies no original-root physical or biological admission.',
        InquiryQuestionKind.SUPPLY, target, (condition,), (), requirement_id, outcomes, AuthorityAction.SIMULATION_EXECUTION)


def preparation_supply_menu(draft, specification, state, *, products=None):
    """Build one concrete finite purchase or its original post-outcome closure."""
    configs, scope, inquiry, origins_for = supply_owners(draft)
    if specification != preparation_supply_specification(draft):
        raise ValueError('preparation supply changes its exact local scientific question')
    sid, tid = identity(specification, specification.specification_id), identity(state, state.state_id)
    requirement, = specification.requirements
    outcome = 'initial' if products is None else inquiry.outcome_projector(draft, specification, products)
    observation = None
    if products is not None:
        actual = inquiry.actual_products(draft, products)
        assessments = [record for _, name, record, _, _ in actual if name == 'assessment']
        if assessments:
            record = assessments[0]
            evidence_ids = tuple(sorted(row.evidence_id for row in state.stock if row.product == record.identity))
            if not evidence_ids:
                raise ValueError('preparation supply observation loses its actual independent readout')
            observation = InquiryObservation('observation.local-supply.' + draft.fingerprint(), sid, outcome, OUTCOMES[outcome],
                specification.distinguishing_assessment, record.identity, evidence_ids, (), scope, state.information_cutoff,
                'Original finite supply disposition; signed response and broader physical admission require their independent owners.')
    frontier = InquiryTargetFrontier('frontier.local-supply.' + draft.fingerprint(),
        identity(specification.target, specification.target.target_id),
        (InquiryRequirementFinding(identity(requirement, requirement.requirement_id), None, ()),), (), ())
    rules = (
        InquiryCriterionRule('progress', InquiryCriterionRole.TARGET_PROGRESS, 'local supply questions', True,
            'One complete finite local operand supply; the original conditional root remains unresolved.'),
        InquiryCriterionRule('capability', InquiryCriterionRole.ENABLED_CAPABILITY, 'independent reading routes', True,
            'Original complete operands enable independent preparation or response reading.'),
        InquiryCriterionRule('discrimination', InquiryCriterionRole.DISCRIMINATION, 'selected comparisons', True,
            'Available, rejected and unavailable returns distinguish this local supply outcome.'),
        InquiryCriterionRule('cost', InquiryCriterionRole.COST, 'CPU seconds', False,
            'Future CPU expense remains unknown; the separate monetary supervisor owns the hard provider limit.', 'cpu_seconds'),
    )
    witness = tuple(sorted(row.evidence_id for row in state.stock if row.role is ContributionRole.RETAINED_ANALYSIS_INPUT))
    assumption = InquiryPolicyAssumption('assumption.original-finite-local-supply',
        'The owner-selected finite purchase can distinguish the local supply question; no optimality or favorable result is assumed.',
        witness, 'Original source incompatibility, unmeasurable checkpoints, unaffordable expense or missing supervision prevents entry.')
    criteria = tuple(InquiryCriterionAssessment(rule.criterion_id,
        None if rule.role is InquiryCriterionRole.COST else Decimal(1),
        None if rule.role is InquiryCriterionRole.COST else Decimal(1), rule.unit, (),
        () if rule.role is InquiryCriterionRole.COST else (assumption.assumption_id,),
        'Selected finite supplier scope; the original external monetary gate and complete result census remain required.')
        for rule in sorted(rules, key=lambda r: r.criterion_id))
    operation = draft.operations[0]
    origins = origins_for(draft)
    acquire = TargetDirectedAlternative('acquire', sid, tid, InquiryAction.ACT, ('initial',), InquiryAlternativeKind.ACQUIRE,
        requirement.requirement_id, scope, draft.question, 'The complete original finite operand census and independent dispositions.',
        (), (), criteria, InquiryCost(None, None, None), operation.selection.selection_id,
        'Source-bound accepted preparation states or complete forces at the prospectively selected displacements.',
        'Changed source, unavailable state, consequential numerical failure or insufficient supervised budget.',
        supplier=SupplierProposal('proposal.local-supply.' + draft.fingerprint(), requirement.requirement_id,
            draft.selected_operation_ids, (), True, 'The complete code-derived local purchase retains the original contribution ancestry.'),
        work=inquiry.scientific_work(draft, operation.node_id), successor_draft=identity(draft, draft.draft_id),
        successor_config=operation.config_identity, input_origins=identity(origins, 'inquiry-input-origins'),
        capability_id=operation.selection.selection_id, planned_operation_count=len(draft.selected_operation_ids))
    alternatives = [acquire]
    for name, action, kind, stop in (('hold', InquiryAction.HOLD, InquiryAlternativeKind.WAIT, None),
                                  ('close-question', InquiryAction.STOP, InquiryAlternativeKind.CLOSE, InquiryStopScope.QUESTION)):
        alternatives.append(TargetDirectedAlternative(name, sid, tid, action,
            tuple(row.outcome_id for row in specification.outcomes if name in row.alternative_ids), kind,
            requirement.requirement_id, scope, draft.question, 'Retain the original local outcome and wider unresolved requirements.',
            (), (), (), InquiryCost(Decimal(0), Decimal(0), Decimal(0)), 'No new native purchase.',
            'Independent local interpretation or a later explicitly selected supplier.',
            'A newly assessed compatible contribution or an affordable discriminating follow-up.',
            stop_scope=stop, local_question_answered=stop is not None))
    menu = RobustInquiryMenu('menu.local-supply.' + draft.fingerprint(), sid, tid,
        tuple(sorted(alternatives, key=lambda row: row.alternative_id)), frontier, observation)
    policy = RobustInquiryPolicy('policy.local-supply.' + draft.fingerprint(), sid, InquiryCost(None, None, None),
        len(draft.selected_operation_ids), None, None, InquiryOrdering.LEXICOGRAPHIC, rules, (assumption,), IncomparableResolution.HOLD)
    return menu, policy


def rooted_preparation_specification(*, root_draft, root_products, draft, design, completed=()):
    """Declare the selected local supplier below the actual unresolved root.

    This creates a successor specification. It never edits or reinterprets the
    original root's frozen HOLD, requirement records or assessment.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_policy import initial_root_inquiry_specification
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import selected_prefix_scope
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope
    _, _, _, original = actual_assessment(root_draft, root_products)
    if original is None or original[0].identity != design.root_assessment or original[0].joint_outcome != 'UNRESOLVED':
        raise ValueError('preparation supplier loses its actual unresolved original root')
    old = initial_root_inquiry_specification(root_draft)
    parent, = (r for r in old.requirements if r.requirement_id.endswith('actual-paired-physical-preparation'))
    local = preparation_supply_specification(draft)
    scopes = (('checkpoint', selected_prefix_scope(design.prefix)), ('response', response_scope(design)))
    # Keep every actual destination assessment revision in the rooted graph.
    # A later complete response cannot erase its earlier missing denominator.
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    local_requirements, local_connections = {}, {}
    for source in (draft, *(d for d, _ in completed)):
        if source.operations[0].config_identity.object_schema != PreparationSupplyConfig.SCHEMA:
            continue
        config = supply_owners(source)[0][0]
        if config.selection.design != design:
            raise ValueError('rooted supply changes its selected scientific design')
        for record, collection, key in ((r, local_requirements, r.requirement_id) for r in source.requirements):
            if collection.setdefault(key, record) != record:
                raise ValueError('rooted supply substitutes an original requirement revision')
        for record in source.connections:
            if local_connections.setdefault(record.connection_id, record) != record:
                raise ValueError('rooted supply substitutes an original connection revision')
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_decision import assess_supplier_eligibility
    eligibility = assess_supplier_eligibility(draft=draft, design=design, completed=completed)
    children = tuple(ScientificRequirementSpec('requirement.preparation-response.' + name + '.' + design.fingerprint(),
        parent.consumer_operation_id, ConditionRole.EVIDENTIAL,
        'Supply the owner-selected local preparation investigation while the full original physical requirement remains open.',
        ('Original accepted initial and later states for both selected M1 constructions.' if name == 'checkpoint' else
         'Complete independently interpreted signed force-response comparisons, with all six questions and unavailable outcomes.'),
        scope, None, 'A missing, changed, unavailable or independently rejected original operand.',
        (ContributionRole.RETAINED_ANALYSIS_INPUT,),
        further_requirement_ids=tuple(sorted(
            {r.requirement_id for r in local_requirements.values() if r.scope == scope}
            | (set(eligibility.prerequisite_requirement_ids) if scope == local.endpoint else set()))))
        for name, scope in scopes)
    parent = replace(parent, further_requirement_ids=tuple(sorted(set(parent.further_requirement_ids)
        | {r.requirement_id for r in children})))
    requirements = tuple(sorted((*(parent if r.requirement_id == parent.requirement_id else r for r in old.requirements),
        *children, *local_requirements.values()), key=lambda r: r.requirement_id))
    if local.endpoint not in {r.scope for r in children}:
        raise ValueError('preparation supplier is outside the selected checkpoint/response question')
    outcomes = tuple(replace(row, alternative_ids=('acquire', 'hold') if row.outcome_id == 'unresolved' else ('hold',))
        for row in old.outcomes)
    connections = tuple(sorted((*old.connections, *local_connections.values()), key=lambda r: r.connection_id))
    return replace(old, specification_id='inquiry.rooted-preparation.' + draft.fingerprint(), requirements=requirements, connections=connections,
        outcomes=outcomes, predecessor_specification=identity(old, old.specification_id))


def rooted_preparation_campaign(*, root_draft, draft, design):
    """A new decision scope retains the original campaign and selected supplier.

    This records the owner's finite local question. Native authority, resource
    allocation and the monetary stop remain at the selected execution boundary.
    """
    _, scope, _, _ = supply_owners(draft)
    original = root_draft.campaign
    evidence = {row.object_id: row for row in original.evidence_state}
    for row in (identity(original, original.campaign_id), identity(draft, draft.draft_id), design.identity):
        if row.object_id in evidence and evidence[row.object_id] != row:
            raise ValueError('preparation campaign changes an original evidence identity')
        evidence[row.object_id] = row
    return replace(original, campaign_id='campaign.rooted-preparation.' + draft.fingerprint(),
        system_ids=tuple(sorted({*original.system_ids, scope.system_id})),
        world_ids=tuple(sorted({*original.world_ids, scope.world_id})),
        evidence_state=tuple(evidence[name] for name in sorted(evidence)),
        predecessor_campaign_ids=(original.campaign_id,))


def rooted_preparation_menu(*, root_draft, root_products, draft, design, specification, state, completed=()):
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment, claim_assessment_projector, outcome_projector
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import project_initial_root_connection
    if specification != rooted_preparation_specification(root_draft=root_draft, root_products=root_products,
            draft=draft, design=design, completed=completed):
        raise ValueError('preparation supplier changes its original-root dependency specification')
    local = preparation_supply_specification(draft)
    local_menu, local_policy = preparation_supply_menu(draft, local, state)
    sid, tid = identity(specification, specification.specification_id), identity(state, state.state_id)
    child, = (r for r in specification.requirements if r.scope == local.endpoint
        and r.requirement_id.startswith('requirement.preparation-response.'))
    parent, = (r for r in specification.requirements if child.requirement_id in r.further_requirement_ids)
    acquire, = (r for r in local_menu.alternatives if r.action is InquiryAction.ACT)
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_decision import assess_supplier_eligibility
    eligibility = assess_supplier_eligibility(draft=draft, design=design, completed=completed)
    acquire = replace(acquire, specification=sid, state=tid, eligible_outcomes=('unresolved',),
        kind=InquiryAlternativeKind.PREREQUISITE, requirement_id=child.requirement_id,
        parent_requirement_id=parent.requirement_id,
        prerequisite_requirement_ids=eligibility.prerequisite_requirement_ids,
        expected_next_evidence=eligibility.consequence, evidence_that_changes_disposition=eligibility.consequence,
        supplier=replace(acquire.supplier, requirement_id=child.requirement_id,
            prerequisite_requirement_ids=eligibility.prerequisite_requirement_ids, selected=eligibility.allowed,
            unavailable_reason_codes=() if eligibility.allowed else ('independent-local-supply-does-not-support-this-purchase',),
            explanation=eligibility.consequence))
    hold, = (r for r in local_menu.alternatives if r.action is InquiryAction.HOLD)
    hold = replace(hold, specification=sid, state=tid,
        eligible_outcomes=tuple(r.outcome_id for r in specification.outcomes),
        requirement_id=specification.question_requirement_id, scope=specification.endpoint,
        scientific_question=specification.question, expected_next_evidence=eligibility.consequence,
        evidence_that_changes_disposition=eligibility.consequence)
    _, _, _, assessed = actual_assessment(root_draft, root_products)
    record = assessed[0]
    observation_ids = tuple(sorted(row.evidence_id for row in state.stock if row.product == record.identity))
    if not observation_ids:
        raise ValueError('preparation supplier lacks the original root assessment in authenticated state')
    outcome = outcome_projector(root_draft, specification, root_products)
    selected_outcome = next(row for row in specification.outcomes if row.outcome_id == outcome)
    observation = InquiryObservation('observation.rooted-preparation.' + draft.fingerprint(), sid, outcome,
        selected_outcome.kind, specification.distinguishing_assessment, record.identity, observation_ids, (),
        specification.endpoint, state.information_cutoff,
        'The original root remains unresolved. ' + eligibility.consequence)
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_policy import initial_root_inquiry_specification
    connection, = initial_root_inquiry_specification(root_draft).connections
    phases = {}
    for _, products in completed:
        for assessment in products['connection_assessments']:
            key = assessment.requirement.object_id
            previous = phases.setdefault(key, {}).get(assessment.phase)
            if previous is not None and (previous.connection != assessment.connection or previous.disposition != assessment.disposition):
                raise ValueError('rooted supply changes the meaning of an original destination requirement')
            if previous is None or assessment.assessment_id > previous.assessment_id:
                phases[key][assessment.phase] = assessment
    def local_finding(requirement):
        rows = tuple(sorted(phases.get(requirement.requirement_id, {}).values(), key=lambda r: r.assessment_id))
        links = {r.connection for r in rows}
        if len(links) > 1:
            raise ValueError('rooted supply joins different original connection revisions')
        return next(iter(links)) if links else None, rows
    findings = tuple(InquiryRequirementFinding(identity(requirement, requirement.requirement_id),
        *( (identity(connection, connection.connection_id), project_initial_root_connection(record, requirement, connection))
            if requirement.requirement_id == connection.requirement_id else local_finding(requirement)))
        for requirement in specification.requirements)
    from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryClaimFinding
    claims = tuple(InquiryClaimFinding(row.claim_identity, specification.endpoint, row.disposition, row.assessment,
        observation_ids, 'Original conditional root assessment; the selected local investigation supplies no kinetic or biological admission.')
        for row in claim_assessment_projector(root_draft, specification, root_products))
    frontier = InquiryTargetFrontier('frontier.rooted-preparation.' + draft.fingerprint(),
        identity(specification.target, specification.target.target_id), findings, claims, ())
    menu = RobustInquiryMenu('menu.rooted-preparation.' + draft.fingerprint(), sid, tid, (acquire, hold), frontier, observation)
    policy = replace(local_policy, policy_id='policy.rooted-preparation.' + draft.fingerprint(), specification=sid,
        max_operations=len(state.operational_census) + len(draft.selected_operation_ids))
    return menu, policy
