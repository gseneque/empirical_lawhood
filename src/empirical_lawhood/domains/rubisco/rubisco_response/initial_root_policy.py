# SPDX-License-Identifier: MPL-2.0
"""Finite source-bound decisions on the shared robust inquiry contracts."""

from decimal import Decimal

from empirical_lawhood.science.identity.authority import AuthorityAction
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost, identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryClaimFinding, InquiryCriterionAssessment, InquiryObservation, InquiryOutcomeMap, InquiryPolicyAssumption, InquiryQuestionKind, InquiryRequirementFinding, InquiryStopScope, InquiryTarget, InquiryTargetFrontier, RobustInquirySpecification, ScientificOutcomeKind
from empirical_lawhood.design.recursive_authoring import SupplierProposal
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import IncomparableResolution, InquiryAlternativeKind, InquiryCriterionRole, InquiryCriterionRule, InquiryOrdering, RobustInquiryMenu, RobustInquiryPolicy, TargetDirectedAlternative
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment, claim_assessment_projector, describe_contributions, next_wave_builder, outcome_projector
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import calculate_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import ASSESS, USE, analysis_arguments, initial_root_requirement_graph, initial_root_scope, project_initial_root_connection
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import initial_root_origins, scientific_work, selected_configs

OUTCOMES = {
    'contradicted': ScientificOutcomeKind.NEGATIVE,
    'initial': ScientificOutcomeKind.MISSING,
    'numerical-failure': ScientificOutcomeKind.NEGATIVE,
    'operational-failure': ScientificOutcomeKind.OPERATIONAL_FAILURE,
    'supported': ScientificOutcomeKind.POSITIVE,
    'uncertain-contact': ScientificOutcomeKind.UNCERTAIN_CONTACT,
    'unresolved': ScientificOutcomeKind.UNEVALUABLE,
}


def initial_root_inquiry_specification(draft):
    config = next(iter(selected_configs(draft).values()))
    graph = initial_root_requirement_graph(config.analysis, parent=config.parent)
    root = next(row for row in graph.requirements if row.requirement_id == graph.root_requirement_id)
    required = root.further_requirement_ids
    scope = initial_root_scope(config.analysis)
    target = InquiryTarget('target.' + config.analysis.request.request_id, draft.question, scope, required,
        tuple(identity(row, row.claim_id) for row in draft.development_study.claims),
        'A numerically reconstructed admitted conditional conjunction, with every remaining decision requirement resolved. No biological claim.')
    assessment = next(row.config_identity for row in draft.operations if row.node_id == (ASSESS if config.parent is None else USE))
    # The copied input is already exposed. Freeze only the successor that this
    # exact input can support; outcome projection still requires actual receipts.
    can_recheck = config.parent is None and calculate_initial_root(**analysis_arguments(config.analysis)).joint_outcome == 'SUPPORTED'
    outcomes = []
    for name, kind in sorted(OUTCOMES.items()):
        enabled = ['hold']
        if name == 'supported':
            enabled.append('stop-target')
            if can_recheck:
                enabled.append('independent-check')
        if name in {'contradicted', 'numerical-failure'}:
            enabled.append('close-branch')
        outcomes.append(InquiryOutcomeMap(name, kind, tuple(sorted(enabled)),
            'Retain the complete conditional decision, adverse findings and original physical requirements.',
            'Supply only a named unresolved condition through its original scientific owner.'))
    return RobustInquirySpecification('inquiry.' + draft.draft_id, draft.question, (), assessment, scope,
        'Exposed arithmetic and operational completion do not establish physical input validity or independent biological prediction.',
        InquiryQuestionKind.ASSESS if config.parent is None else InquiryQuestionKind.ADOPT, target,
        tuple(row for row in graph.requirements if row.requirement_id in required), graph.connections,
        graph.numerical_requirement_id, tuple(outcomes), AuthorityAction.SIMULATION_EXECUTION)


def initial_root_inquiry_menu(draft, specification, state, products):
    """Compose from authenticated products/state; the public service rechecks both."""
    if specification != initial_root_inquiry_specification(draft):
        raise ValueError('initial root policy changes its exact conditional target or outcome map')
    config, result, _, assessed = actual_assessment(draft, products)
    if assessed is None:
        raise ValueError('initial root decision requires its actual retained independent assessment')
    record = assessed[0]
    sid, tid = identity(specification, specification.specification_id), identity(state, state.state_id)
    scope = specification.endpoint
    observation_ids = tuple(sorted(row.evidence_id for row in state.stock if row.product == record.identity))
    if not observation_ids:
        raise ValueError('initial root decision lacks its actual assessment in authenticated state')
    outcome_id = outcome_projector(draft, specification, products)
    observation = InquiryObservation('observation.' + specification.specification_id, sid, outcome_id, OUTCOMES[outcome_id],
        specification.distinguishing_assessment, record.identity, observation_ids, (), scope, state.information_cutoff,
        'The independent result preserves both endpoint inequalities, all alternatives, exposure and missing inputs.')
    connection, = specification.connections
    findings = []
    for requirement in specification.requirements:
        phases = (() if requirement.requirement_id != connection.requirement_id else
            project_initial_root_connection(record, requirement, connection))
        findings.append(InquiryRequirementFinding(identity(requirement, requirement.requirement_id),
            identity(connection, connection.connection_id) if phases else None, phases))
    claims = tuple(InquiryClaimFinding(row.claim_identity, scope, row.disposition, row.assessment,
        observation_ids, 'Actual independently reconstructed conditional root; zero biological units and no new native supply.')
        for row in claim_assessment_projector(draft, specification, products))
    frontier = InquiryTargetFrontier('frontier.' + specification.specification_id,
        identity(specification.target, specification.target.target_id), tuple(findings), claims, ())
    rules = (
        InquiryCriterionRule('progress', InquiryCriterionRole.TARGET_PROGRESS, 'conditional requirements', True,
            'A repeated retained check does not supply a missing physical operand.'),
        InquiryCriterionRule('capability', InquiryCriterionRole.ENABLED_CAPABILITY, 'destination checks', True,
            'One bound destination can independently recheck the original contribution.'),
        InquiryCriterionRule('discrimination', InquiryCriterionRole.DISCRIMINATION, 'checked contracts', True,
            'The original contribution either matches its exact consumer or refuses.'),
        InquiryCriterionRule('cost', InquiryCriterionRole.COST, 'CPU seconds', False,
            'Unmeasured future execution cost remains unknown.', 'cpu_seconds'),
    )
    alternatives, assumptions = [], ()
    manifest, = describe_contributions(draft, products)
    successor = next_wave_builder(draft, manifest, products)
    if successor is not None:
        operation, = successor.operations
        origins = initial_root_origins(successor)
        assumptions = (InquiryPolicyAssumption('assumption.rubisco.initial-root.retained-check',
            'One exact retained destination assessment checks compatibility; it adds no physical evidence.',
            observation_ids, 'Changed source, consumer, original product or receipt refuses the connection.'),)
        criteria = tuple(InquiryCriterionAssessment(rule.criterion_id,
            None if rule.role is InquiryCriterionRole.COST else Decimal(0 if rule.criterion_id == 'progress' else 1),
            None if rule.role is InquiryCriterionRole.COST else Decimal(0 if rule.criterion_id == 'progress' else 1),
            rule.unit, (), () if rule.role is InquiryCriterionRole.COST else (assumptions[0].assumption_id,),
            'Bounded destination compatibility check; future measured expense remains unknown.')
            for rule in sorted(rules, key=lambda row: row.criterion_id))
        alternatives.append(TargetDirectedAlternative('independent-check', sid, tid, InquiryAction.ACT, ('supported',),
            InquiryAlternativeKind.INDEPENDENT_CHECK, connection.requirement_id, scope,
            'Does the actual original contribution satisfy this exact retained consumer?',
            'Independent reconstruction or an explicit compatibility refusal.', (), (), criteria, InquiryCost(None, None, None),
            operation.selection.selection_id, 'One receipt-bound retained assessment.', connection.falsifier,
            supplier=SupplierProposal('proposal.' + specification.specification_id + '.retained-check',
                connection.requirement_id, (operation.node_id,), (), True, 'Use the exact original contribution at its unchanged scope.'),
            work=scientific_work(successor, operation.node_id), successor_draft=identity(successor, successor.draft_id),
            successor_config=operation.config_identity, input_origins=identity(origins, 'inquiry-input-origins'),
            capability_id=operation.selection.selection_id, planned_operation_count=1))
    for name, stop_scope in (('hold', None), ('close-branch', InquiryStopScope.BRANCH), ('stop-target', InquiryStopScope.TARGET)):
        alternatives.append(TargetDirectedAlternative(name, sid, tid, InquiryAction.HOLD if stop_scope is None else InquiryAction.STOP,
            tuple(row.outcome_id for row in specification.outcomes if name in row.alternative_ids),
            InquiryAlternativeKind.WAIT if stop_scope is None else InquiryAlternativeKind.CLOSE,
            connection.requirement_id, scope, specification.question,
            'Retain the actual conditional decision and its complete missing scientific denominator.', (), (), (),
            InquiryCost(Decimal(0), Decimal(0), Decimal(0)), 'No new native acquisition.',
            'An admitted decision-relevant physical input or independently sufficient bound.',
            'A compatible assessed contribution changes a named unresolved prerequisite.', stop_scope=stop_scope,
            local_question_answered=stop_scope is InquiryStopScope.BRANCH))
    menu = RobustInquiryMenu('menu.' + specification.specification_id, sid, tid,
        tuple(sorted(alternatives, key=lambda row: row.alternative_id)), frontier, observation)
    policy = RobustInquiryPolicy('policy.' + specification.specification_id, sid, InquiryCost(None, None, None),
        None, None, None, InquiryOrdering.LEXICOGRAPHIC, rules, assumptions, IncomparableResolution.HOLD)
    return menu, policy, successor
