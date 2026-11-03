# SPDX-License-Identifier: MPL-2.0
"""Shared assembly for two explicitly exposed analytic connection protocols.

Scientific meanings and independent falsifiers remain with each domain owner.
This module does not run a producer or grant physical qualification.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.authority import AuthorityAction
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost, identity
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    InquiryClaimFinding, InquiryCriterionAssessment, InquiryObservation, InquiryOutcomeMap,
    InquiryPolicyAssumption, InquiryQuestionKind, InquiryRequirementFinding, InquiryStopScope,
    InquiryTarget, InquiryTargetFrontier, RobustInquirySpecification, ScientificInquiryWork,
    ScientificOutcomeKind,
)
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition, AssessmentPhase, ConditionRole, ContributionRole,
    RequirementSupplyAssessment, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id, validate_sha256
from empirical_lawhood.planning.recursive_authoring import SupplierProposal
from empirical_lawhood.planning.recursive_inquiry import InquiryAction
from empirical_lawhood.planning.recursive_inquiry_policy import (
    IncomparableResolution, InquiryAlternativeKind, InquiryCriterionRole, InquiryCriterionRule,
    InquiryOrdering, RobustInquiryMenu, RobustInquiryPolicy, TargetDirectedAlternative,
)
from empirical_lawhood.planning.recursive_input_origins import (
    RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins,
)

D = Decimal
OUTCOMES = {
    "initial": ScientificOutcomeKind.MISSING,
    "useful-supply": ScientificOutcomeKind.POSITIVE,
    "scoped-failure": ScientificOutcomeKind.NEGATIVE,
    "unresolved": ScientificOutcomeKind.UNEVALUABLE,
    "operational-failure": ScientificOutcomeKind.OPERATIONAL_FAILURE,
    "uncertain-contact": ScientificOutcomeKind.UNCERTAIN_CONTACT,
}


@dataclass(frozen=True, slots=True)
class CompactScientificMethod(CanonicalRecord):
    """Named compact semantics retain every scientific configuration field.

    Only the operational configuration label is excluded. Capability version,
    implementation, actual source/design, full operands and scientific scope
    (including receiver and cutoff) remain exact.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/compact-inquiry/scientific-method"
    namespace: str
    operation: str
    capability_key: str
    capability_version: str
    implementation_sha256: str
    source: ObjectIdentity
    scientific_design: ObjectIdentity | None
    operands: tuple[ObjectIdentity, ...]
    scope: ScientificConditionScope
    output_schema: str
    output_version: str

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import (
            require_sorted_unique_ids, validate_schema, validate_semantic_version,
        )
        for field in ("namespace", "operation", "capability_key"):
            validate_stable_id(getattr(self, field), field_name=field)
        validate_sha256(self.implementation_sha256)
        validate_semantic_version(self.capability_version)
        validate_semantic_version(self.output_version)
        validate_schema(self.output_schema)
        require_sorted_unique_ids(self.operands, attribute="object_id", field_name="operands")
        if not self.operands:
            raise ValueError("compact work needs its complete scientific operands")
        self.scope.__post_init__()


def compact_scientific_work(*, namespace, operation, config, scope, output_type, scientific_design=None):
    """Domain-selected exact semantics; no generic configuration-field stripping."""
    method = CompactScientificMethod(namespace, config.operation, operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        config.source, scientific_design, config.operands, scope, output_type.SCHEMA, output_type.VERSION)
    method_identity = identity(method, f"method.{namespace}.{config.operation}")
    return ScientificInquiryWork(method_identity,
        tuple(sorted({config.source, *config.operands}, key=lambda row: row.object_id)), scope,
        identity(method, f"observation.{namespace}.{config.operation}"))


def connection_contracts(*, namespace, scope, parent, application_condition):
    prerequisite_id = f"requirement.{namespace}.reusable-procedure"
    application = ScientificRequirementSpec(
        f"requirement.{namespace}.application-target", f"{namespace}.physical-application",
        ConditionRole.PHYSICAL, "Advance the consequential physical application.",
        application_condition, scope, f"{namespace}.physical-application-assessment",
        "Failure or absence of the specified physical endpoints leaves the application target open.",
        (ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,), (prerequisite_id,),
    )
    prerequisite = ScientificRequirementSpec(
        prerequisite_id, f"{namespace}.use", ConditionRole.EVIDENTIAL,
        "Assess the original exposed procedure in a separately supplied later instance.",
        "Exact source, scoped supplier, complete analytic denominator and independent consumer falsifier; no physical qualification.",
        scope, f"{namespace}.use",
        "Source, assembly, clock, receiver or required endpoint drift falsifies/refuses the declared analytic connection.",
        (ContributionRole.DESIGN_OPERAND,),
    )
    if parent is None:
        connection = ScientificConnectionSpec(
            f"connection.{namespace}.reusable-procedure", prerequisite_id,
            f"{namespace}.supply", f"{namespace}.supply.product", "supplier",
            f"{namespace}.use", f"claim.{namespace}.use", ContributionRole.DESIGN_OPERAND,
            prerequisite.falsifier,
        )
    else:
        products = tuple(row for row in parent.products if row.role is ContributionRole.DESIGN_OPERAND)
        if len(products) != 1 or parent.scope != scope:
            raise ValueError("analytic policy connection needs its one original scoped design operand")
        connection = ScientificConnectionSpec(
            f"connection.{namespace}.reusable-procedure", prerequisite_id,
            None, None, "supplier", f"{namespace}.use", f"claim.{namespace}.use",
            ContributionRole.DESIGN_OPERAND, prerequisite.falsifier,
            identity(parent, parent.contribution_id), products[0].product_id,
            f"external.{namespace}.use.supplier",
        )
    return tuple(sorted((application, prerequisite), key=lambda row: row.requirement_id)), connection


def bind_assessed_use(draft, *, requirements, connection):
    """Add scientific contracts to a new draft; existing draft bytes stay unchanged."""
    requirement = next(row for row in requirements if row.requirement_id == connection.requirement_id)
    links = tuple(replace(row, requirement_id=requirement.requirement_id, connection_id=connection.connection_id)
                  if row.consumer_input_id == "supplier" else row for row in draft.links)
    return bind_policy_campaign(replace(draft, requirements=(requirement,), connections=(connection,), links=links),
                                requirement.scope)


def bind_policy_campaign(draft, scope):
    """An explicitly new policy draft declares the actual decision system scope."""
    root = scoped_policy_root(draft.development_study, scope)
    old_root = identity(draft.development_study, draft.development_study.study_id)
    new_root = identity(root, root.study_id)
    campaign = replace(draft.campaign, system_ids=tuple(sorted({*draft.campaign.system_ids, scope.system_id})),
                       world_ids=tuple(sorted({*draft.campaign.world_ids, scope.world_id})),
                       nodes=tuple(replace(node, object_identity=new_root) if node.object_identity == old_root else node
                                   for node in draft.campaign.nodes))
    return replace(draft, campaign=campaign, development_study=root)


def scoped_policy_root(root, scope):
    """Bind the new scientific system without changing its original source digest.

    Historical compact roots use the source object itself as their system. New
    assessed-connection drafts have a separate scientific system scope, whose
    identity must join the compiler's declared root rather than only a campaign.
    """
    if root.world_id != scope.world_id:
        raise ValueError("analytic policy root changes its original scientific world")
    source = root.system
    return replace(root, system=ObjectIdentity(scope.system_id, source.object_schema,
        source.object_version, source.object_fingerprint))


def project_analytic_connection(*, namespace, record, requirement, connection, record_identity,
                               admission, joined, reason_codes, instance_id):
    """Project four distinct outcomes from an authenticated independent consumer.

    PROCEDURE concerns the declared exposed checker, INSTANCE the original
    supplied operand, ADMISSION its exact compatibility, JOINED the actual
    later-use result. A negative later use does not revoke procedural evidence.
    """
    if (requirement.requirement_id != f"requirement.{namespace}.reusable-procedure"
            or requirement.scope != record.scope or requirement.consumer_operation_id != f"{namespace}.use"
            or connection.requirement_id != requirement.requirement_id
            or connection.assessment_operation_id != f"{namespace}.use"
            or connection.consumer_input_id != "supplier"
            or connection.evidence_role is not ContributionRole.DESIGN_OPERAND
            or connection.claim_id != f"claim.{namespace}.use"
            or connection.falsifier != requirement.falsifier
            or connection.supplier_product_id != f"product.{namespace}.supply.design-operand"
            or connection.external_input_id != f"external.{namespace}.use.supplier"):
        raise ValueError("analytic phase projection changes the frozen scientific connection")
    evidence = tuple(sorted((record.supplier, record_identity(record)), key=lambda row: row.object_id))
    dispositions = (
        (AssessmentPhase.PROCEDURE, AssessmentDisposition.SATISFIED),
        (AssessmentPhase.INSTANCE, AssessmentDisposition.SATISFIED),
        (AssessmentPhase.ADMISSION, admission),
        (AssessmentPhase.JOINED, joined),
    )
    return tuple(sorted((RequirementSupplyAssessment(
        f"assessment.{namespace}.connection.{phase.value.lower()}",
        identity(requirement, requirement.requirement_id), identity(connection, connection.connection_id),
        phase, disposition, instance_id,
        evidence, () if disposition is AssessmentDisposition.SATISFIED else reason_codes,
    ) for phase, disposition in dispositions), key=lambda row: row.assessment_id))


def compact_input_origins(draft, parent=None):
    rows = []
    for external in draft.external_inputs:
        products = () if parent is None else tuple(row for row in parent.products
            if row.artifact.sha256 == external.expected_content_sha256)
        if products:
            if len(products) != 1:
                raise ValueError("input origin has ambiguous parent products")
            product = products[0]
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
                external.expected_content_sha256, product.role.value, identity(parent, parent.contribution_id),
                product.product_id, product.producing_receipt))
        else:
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.SOURCE,
                external.expected_content_sha256, external.scientific_role))
    origins = RecursiveInputOrigins(tuple(sorted(rows, key=lambda row: row.input_id)))
    origins.validate_draft(draft)
    return origins


def compact_policy_specification(*, namespace, source_draft, specification_id, stage,
                                 requirements, connection, previous=None, assessed_draft=None):
    """Freeze one domain-owned prerequisite question and its application frontier.

    These finite analytic routes describe the actual selected operation. They
    neither forecast physical success nor compare invented scientific suppliers.
    """
    if stage not in {"origin", "later", "frontier"}:
        raise ValueError("unknown compact inquiry stage")
    application, reusable = requirements
    scope = application.scope
    if stage == "frontier" and assessed_draft is None:
        raise ValueError("frontier needs its actual independently assessed draft")
    claim = ClaimSpec(f"claim.{namespace}.physical-target", scope.world_id,
            f"population.{namespace}.physical-target", application.condition,
            "Complete physical endpoint denominator remains unentered; exposed analytic views supply no independent physical units.",
            scope.instance_id, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
            VisibilityCeiling.DEVELOPMENT_ONLY, "Analytic outcomes cannot complete the physical application target.",
            ("assumption.application-bridge-unresolved",))
    target = InquiryTarget(f"target.{namespace}.application", application.purpose, scope,
        (application.requirement_id,), (identity(claim, claim.claim_id),), application.condition)
    if previous is not None and previous.target != target:
        raise ValueError("compact inquiry revision changes its original application target")
    current_config = (source_draft.operations[0].config_identity if stage != "frontier"
                      else assessed_draft.operations[0].config_identity)
    act_id = "investigate-supplier" if stage == "origin" else "independently-assess-later-instance"
    eligible_act = ("initial",) if stage == "origin" else ("useful-supply",)
    outcome_maps = []
    for oid, kind in sorted(OUTCOMES.items()):
        enabled = ["hold"]
        if kind is ScientificOutcomeKind.POSITIVE:
            enabled.append("stop-target")
        if stage != "frontier" and oid in eligible_act:
            enabled.append(act_id)
        if stage == "frontier" and kind in {ScientificOutcomeKind.POSITIVE, ScientificOutcomeKind.NEGATIVE}:
            enabled.append("close-branch")
        outcome_maps.append(InquiryOutcomeMap(oid, kind, tuple(sorted(enabled)),
            "Retain scoped analytic outcomes and the unresolved physical application requirement.",
            application.condition))
    spec = RobustInquirySpecification(specification_id,
        reusable.condition if stage != "frontier" else "What physical or biological conditions remain after the scoped analytic episode?",
        (), current_config, scope, "Exposed analytic conditions cannot warrant physical or biological endpoint reliance.",
        InquiryQuestionKind.SUPPLY if stage == "origin" else InquiryQuestionKind.ASSESS,
        target, requirements, (connection,), reusable.requirement_id, tuple(outcome_maps),
        AuthorityAction.SIMULATION_EXECUTION,
        None if previous is None else identity(previous, previous.specification_id))
    return spec


def compact_policy_menu(*, namespace, specification, state, stage, outcome_id,
                        record_identity, work_projector, record=None, next_draft=None, parent=None, assessments=()):
    """Author a typed finite menu over authenticated state, preserving uncertainty.

    API custody authenticates the products and registered domain projectors
    independently check the chosen outcome. This assembly grants no authority.
    """
    spec = specification
    specification_id = spec.specification_id
    requirements = spec.requirements
    application, reusable = requirements
    target = spec.target
    connection = spec.connections[0]
    scope = spec.endpoint
    current_config = spec.distinguishing_assessment
    cutoff = state.information_cutoff
    outcome_maps = spec.outcomes
    act_id = "investigate-supplier" if stage == "origin" else "independently-assess-later-instance"
    eligible_act = ("initial",) if stage == "origin" else ("useful-supply",)
    ids = (act_id, "hold", "stop-target") if stage != "frontier" else ("close-branch", "hold", "stop-target")
    if stage not in {"origin", "later", "frontier"} or outcome_id not in OUTCOMES:
        raise ValueError("unknown compact inquiry stage or outcome")
    if (stage == "origin") != (record is None):
        raise ValueError("compact outcome needs its actual supplier or independent consumer")
    if stage == "frontier" and next_draft is not None:
        raise ValueError("closed analytic branch cannot invent an executable physical supplier")
    if stage != "frontier" and next_draft is None:
        raise ValueError("open compact inquiry needs its complete actual selected continuation")
    if ((stage == "frontier" and {row.phase for row in assessments} != set(AssessmentPhase))
            or (stage != "frontier" and assessments)
            or any(row.requirement != identity(reusable, reusable.requirement_id)
                or row.connection != identity(connection, connection.connection_id) for row in assessments)):
        raise ValueError("compact frontier needs its complete exact independent phase denominator")
    sid, tid = identity(spec, spec.specification_id), identity(state, state.state_id)
    assessed_identity = None if record is None else record_identity(record)
    observation_ids = () if record is None else tuple(row.evidence_id for row in state.stock if row.product == assessed_identity)
    if record is not None and not observation_ids:
        raise ValueError("compact outcome lacks its actual authenticated product in state")
    observation = InquiryObservation(f"observation.{specification_id}", sid, outcome_id, OUTCOMES[outcome_id],
        current_config, assessed_identity, observation_ids, (), scope, cutoff,
        "Exact registered receipt product supplies the scoped result; missing physical endpoints remain unentered.")
    findings = tuple(InquiryRequirementFinding(identity(row, row.requirement_id),
        identity(connection, connection.connection_id) if row == reusable and assessments else None,
        tuple(assessment for assessment in assessments if assessment.requirement == identity(row, row.requirement_id)))
        for row in requirements)
    frontier = InquiryTargetFrontier(f"frontier.{specification_id}", identity(target, target.target_id), findings,
        (InquiryClaimFinding(target.required_claims[0], scope, AssessmentDisposition.NOT_ATTEMPTED,
            None, (), "No paired physical/biological application outcome was entered."),), ())
    alternatives = []
    rules = (
        InquiryCriterionRule("progress", InquiryCriterionRole.TARGET_PROGRESS, "required conditions", True,
            "A missing declared prerequisite can enable the next application-directed investigation."),
        InquiryCriterionRule("capability", InquiryCriterionRole.ENABLED_CAPABILITY, "enabled operations", True,
            "The exact selected known procedure enables one explicitly named successor, conditionally on its assessed result."),
        InquiryCriterionRule("discrimination", InquiryCriterionRole.DISCRIMINATION, "assessed contrasts", True,
            "Keep the complete selected analytic contrast; no benchmark superiority requirement."),
        InquiryCriterionRule("cost", InquiryCriterionRole.COST, "CPU seconds", False,
            "Unknown prospective and past costs remain unknown.", "cpu_seconds"),
    )
    assumptions = ()
    if next_draft is not None:
        origins = compact_input_origins(next_draft, parent)
        operation = next_draft.operations[0]
        assumptions = (InquiryPolicyAssumption("assumption.selected-conditional-design",
            "The actual registered complete operation investigates one missing requirement; favourable success is not assumed.",
            observation_ids, reusable.falsifier),)
        criteria = tuple(InquiryCriterionAssessment(rule.criterion_id,
            None if rule.role is InquiryCriterionRole.COST else D(1),
            None if rule.role is InquiryCriterionRole.COST else D(1), rule.unit, (),
            () if rule.role is InquiryCriterionRole.COST else (assumptions[0].assumption_id,),
            "One fixed disclosed contrast enables a conditional capability; actual cost is not forecast by a fixed score.")
            for rule in sorted(rules, key=lambda row: row.criterion_id))
        work = work_projector(next_draft, operation.node_id)
        alternatives.append(TargetDirectedAlternative(act_id, sid, tid, InquiryAction.ACT, eligible_act,
            InquiryAlternativeKind.PREREQUISITE if stage == "origin" else InquiryAlternativeKind.INDEPENDENT_CHECK,
            reusable.requirement_id, scope, reusable.condition,
            "Full original analytic denominator and independent conditional consumer verdict.", (), (), criteria,
            InquiryCost(None, None, None), operation.selection.selection_id,
            "Authenticated complete source/instance/assessment product, retaining adverse outcomes.", reusable.falsifier,
            SupplierProposal(f"proposal.{specification_id}", reusable.requirement_id, (operation.node_id,), (), True,
                "Adopt the established disclosed analytic method for this precise prerequisite."),
            application.requirement_id if stage == "origin" else None, work,
            successor_draft=identity(next_draft, next_draft.draft_id), successor_config=operation.config_identity,
            input_origins=identity(origins, "inquiry-input-origins"), capability_id=operation.selection.selection_id,
            planned_operation_count=len(next_draft.selected_operation_ids)))
    for aid in ids:
        if aid == act_id and next_draft is not None:
            continue
        eligible = tuple(row.outcome_id for row in outcome_maps if aid in row.alternative_ids)
        alternatives.append(TargetDirectedAlternative(aid, sid, tid,
            InquiryAction.HOLD if aid == "hold" else InquiryAction.STOP, eligible,
            InquiryAlternativeKind.WAIT if aid == "hold" else InquiryAlternativeKind.CLOSE,
            application.requirement_id if aid == "stop-target" else reusable.requirement_id, scope,
            application.condition if aid != "close-branch" else reusable.condition,
            "Retain the exact scoped result and complete unresolved target denominator.", (), (), (),
            InquiryCost(D(0), D(0), D(0)), "Physical application remains unenabled.", application.condition,
            "Independent physical endpoints under the declared assay or preparation conditions.",
            stop_scope=InquiryStopScope.TARGET if aid == "stop-target" else InquiryStopScope.BRANCH if aid == "close-branch" else None,
            local_question_answered=aid == "close-branch"))
    menu = RobustInquiryMenu(f"menu.{specification_id}", sid, tid,
        tuple(sorted(alternatives, key=lambda row: row.alternative_id)), frontier, observation)
    policy = RobustInquiryPolicy(f"policy.{specification_id}", sid, InquiryCost(None, None, None), None, None, None,
        InquiryOrdering.LEXICOGRAPHIC, rules, assumptions, IncomparableResolution.HOLD)
    return menu, policy

