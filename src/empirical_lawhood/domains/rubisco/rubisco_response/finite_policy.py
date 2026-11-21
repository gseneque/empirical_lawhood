# SPDX-License-Identifier: MPL-2.0
"""Rubisco finite eligibility and refinement through shared work-bound inquiry.

This owner supplies scientific gating; shared planning owns actual work,
completion reuse, uncertain contact, costs, finite allowances and the decision.
No supplier, successor draft or missing assessment is manufactured here.
"""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.identity.authority import AuthorityAction
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost, identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryClaimFinding, InquiryCriterionAssessment, InquiryObservation, InquiryOutcomeMap, InquiryPolicyAssumption, InquiryQuestionKind, InquiryRequirementFinding, InquiryTarget, InquiryTargetFrontier, RobustInquirySpecification, ScientificOutcomeKind, WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, ConditionRole, ContributionRole, ScientificRequirementSpec
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import IncomparableResolution, InquiryAlternativeKind, InquiryCriterionRole, InquiryCriterionRule, InquiryOrdering, RobustInquiryMenu, RobustInquiryPolicy, TargetDirectedAlternative, choose_robust_inquiry, evaluate_robust_inquiry
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import FiniteSequentialProcedure, JointIndicatorAssessment, cutoff_precedes, pre_action_cutoff
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph, scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy

OUTCOMES = {"initial": ScientificOutcomeKind.MISSING, "operational-failure": ScientificOutcomeKind.OPERATIONAL_FAILURE,
    "scoped-failure": ScientificOutcomeKind.NEGATIVE, "uncertain-contact": ScientificOutcomeKind.UNCERTAIN_CONTACT,
    "unresolved": ScientificOutcomeKind.UNEVALUABLE, "useful-supply": ScientificOutcomeKind.POSITIVE}
GATE_NAMES = ("context-and-clock", "decision", "indicator-validity", "native-acquisition-allowance", "reference-entry", "reference-reuse", "supplier-selection")


@dataclass(frozen=True, slots=True)
class PermittedPolicyRefinement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/permitted-policy-refinement"
    refinement_id: str
    requirement_ids: tuple[str, ...]
    maximum_attempts: int

    def __post_init__(self):
        validate_stable_id(self.refinement_id)
        require_sorted_unique_strings(self.requirement_ids, field_name="requirement_ids", allow_empty=False)
        if type(self.maximum_attempts) is not int or self.maximum_attempts <= 0:
            raise ValueError("refinement needs its finite positive complete-attempt allowance")

    @property
    def alternative_id(self):
        return "refine." + self.refinement_id


@dataclass(frozen=True, slots=True)
class FiniteResponsePolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/finite-policy"
    policy_id: str
    study: RubiscoResponseStudy
    case_id: str
    selected_supplier: ObjectIdentity | None
    sequential: FiniteSequentialProcedure
    refinements: tuple[PermittedPolicyRefinement, ...]
    max_operations: int
    max_waves: int
    max_depth: int
    max_cost: InquiryCost
    threshold: Decimal = Decimal(1)
    maximum_reference_attempts: int = 1
    scope_label: str = "EXPOSED_CONDITIONAL_POLICY_NOT_NATIVE_OR_SCIENTIFIC_AUTHORITY"

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        exact(self.study, RubiscoResponseStudy)
        if self.case_id not in {row.case_id for row in self.study.cases.cases}:
            raise ValueError("finite policy changes the selected complete case census")
        if self.selected_supplier is not None:
            exact(self.selected_supplier, ObjectIdentity)
        exact(self.sequential, FiniteSequentialProcedure)
        if any(row.information_cutoff.clock_id != self.scope.clock_id for row in self.sequential.checkpoints):
            raise ValueError("policy changes the physical checkpoint clock")
        if type(self.refinements) is not tuple:
            raise ValueError("finite refinement menu must be immutable")
        require_sorted_unique_ids(self.refinements, attribute="refinement_id", field_name="refinements")
        for row in self.refinements:
            exact(row, PermittedPolicyRefinement)
        for name in ("max_operations", "max_waves", "max_depth"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("policy needs explicit finite nonnegative operation, wave and depth ceilings")
        exact(self.max_cost, InquiryCost)
        acceptance = self.study.acceptance
        if (acceptance.uncertainty_procedure != self.sequential.identity
                or tuple(row.refinement_id for row in self.refinements) != acceptance.permitted_refinement_ids
                or sum(row.maximum_attempts for row in self.refinements) > acceptance.maximum_refinements):
            raise ValueError("policy changes the frozen uncertainty procedure or complete refinement allowance")
        if (acceptance.reference_fallback is not None and acceptance.reference_fallback != acceptance.reference_method):
            raise ValueError("the single declared fallback must retain the selected reference method")
        if acceptance.joint_coverage_level is not None and self.sequential.family_error_probability.fraction > 1 - Fraction(acceptance.joint_coverage_level):
            raise ValueError("sequential error budget weakens the frozen joint coverage criterion")
        if (type(self.threshold) is not Decimal or self.threshold != 1
                or type(self.maximum_reference_attempts) is not int or self.maximum_reference_attempts != 1
                or self.scope_label != "EXPOSED_CONDITIONAL_POLICY_NOT_NATIVE_OR_SCIENTIFIC_AUTHORITY"):
            raise ValueError("this policy has one allocated-error threshold and one declared reference attempt")
        base_ids = {row.requirement_id for row in response_requirement_graph(self.study).requirements}
        gate_ids = {self.requirement_id(name) for name in GATE_NAMES} | {self.sequential.bound_validity_requirement_id}
        if not {key for row in self.refinements for key in row.requirement_ids} <= base_ids | gate_ids:
            raise ValueError("finite refinement cannot invent a requirement outside its scientific target")

    @property
    def identity(self):
        return identity(self, self.policy_id)

    @property
    def scope(self):
        return replace(scientific_scope(self.study), instance_id=self.case_id, receiver_id="rubisco-response.policy")

    @property
    def context(self):
        return next(row.context for row in self.study.supplies if row.case.case_id == self.case_id)

    def requirement_id(self, name):
        return "requirement." + self.policy_id + "." + name

    @property
    def alternative_ids(self):
        return tuple(sorted(("hold", "reduced", "reference", *(row.alternative_id for row in self.refinements))))

    @property
    def common_requirements(self):
        prefix = "requirement." + self.study.study_id + "."
        return tuple(sorted((prefix + "criteria", prefix + self.case_id + ".active-state",
            self.requirement_id("context-and-clock"), self.requirement_id("native-acquisition-allowance"),
            self.requirement_id("supplier-selection"))))


def policy_requirements(selection):
    """Add gates to the existing full target ancestry without rewriting old records."""
    graph = response_requirement_graph(selection.study)
    descriptions = {
        "decision": "The declared finite supplier decision is independently assessed at its original causal cutoff and complete scientific scope.",
        "native-acquisition-allowance": "The actual complete native-contact census and the entire proposed wave fit the frozen native acquisition ceiling "
            + str(selection.study.acceptance.maximum_native_acquisitions) + "; failed and uncertain contacts remain charged or unresolved.",
        "context-and-clock": "Exact paired material, active chemistry, assay, physical clock and declared validity horizon are independently compatible.",
        "indicator-validity": "Independent rigorous or calibrated error-set and nonlinear-allowance validity at this receiver, including finite mutation and both branches.",
        "reference-entry": "The one selected reference method and its actual source, preparation, access, resource and numerical prerequisites permit the requested work.",
        "reference-reuse": "The original complete reference is independently usable at this exact scope; failed or unknown reference output cannot be relabelled as a successful fallback.",
        "supplier-selection": "Supported joint sensitivity and actual supplier cost justify this consequential approximation target and its matched reference.",
    }
    added = [ScientificRequirementSpec(selection.requirement_id(name), "rubisco-response.policy", ConditionRole.EVIDENTIAL,
        "Use a finite, causally supported Rubisco supplier policy", text, selection.scope, "rubisco-response.policy-assess",
        "Missing, contradicted, out-of-scope or future evidence blocks this gate.", (ContributionRole.RETAINED_ANALYSIS_INPUT,))
        for name, text in descriptions.items()]
    added.append(ScientificRequirementSpec(selection.sequential.bound_validity_requirement_id, "rubisco-response.policy", ConditionRole.EVIDENTIAL,
        "Control all declared endpoint/checkpoint errors under the actual adaptive history",
        "Every allocated endpoint bound is valid conditional on permitted past information; the finite union bound covers any declared stopping checkpoint.",
        selection.scope, "rubisco-response.policy-assess", "Pointwise calibration, reused risk or an undeclared checkpoint does not establish sequential coverage.",
        (ContributionRole.RETAINED_ANALYSIS_INPUT,)))
    if len({row.requirement_id for row in added}) != len(added) or {row.requirement_id for row in added} & {row.requirement_id for row in graph.requirements}:
        raise ValueError("policy gate aliases an existing requirement revision")
    # The shared graph freezes every possible supplier prerequisite before
    # any state-dependent menu is composed. The menu may require a subset for
    # its actual role, but may never invent an undeclared gate.
    owners = {row.requirement_id: row for row in (*graph.requirements, *added)}
    decision_id = selection.requirement_id("decision")
    pending = [*selection.common_requirements, *(row.requirement_id for row in added if row.requirement_id != decision_id)]
    allowed = set()
    while pending:
        key = pending.pop()
        if key not in allowed:
            allowed.add(key)
            pending.extend(owners[key].further_requirement_ids)
    added = [replace(row, further_requirement_ids=tuple(sorted(allowed))) if row.requirement_id == decision_id else row for row in added]
    parent_id = "requirement." + selection.study.study_id + ".prospective-policy"
    base = tuple(replace(row, further_requirement_ids=tuple(sorted((*row.further_requirement_ids, *(item.requirement_id for item in added)))))
        if row.requirement_id == parent_id else row for row in graph.requirements)
    return tuple(sorted((*base, *added), key=lambda row: row.requirement_id)), graph.connections


def finite_policy_specification(selection, *, distinguishing_assessment, required_claims, supporting_connections=()):
    """Code-owned finite roster; ACT still needs authentic authored successors."""
    exact(selection, FiniteResponsePolicy)
    exact(distinguishing_assessment, ObjectIdentity)
    identities(required_claims)
    graph = response_requirement_graph(selection.study)
    requirements, connections = policy_requirements(selection)
    if type(supporting_connections) is not tuple:
        raise ValueError("independent supplier connections must retain their immutable selected census")
    connections = tuple(sorted((*connections, *supporting_connections), key=lambda row: row.connection_id))
    target = InquiryTarget("target." + selection.policy_id, selection.study.question, scientific_scope(selection.study),
        (graph.root_requirement_id,), required_claims, "Every component of the combined scientific milestone remains required.")
    outcomes = tuple(InquiryOutcomeMap(key, kind, selection.alternative_ids,
        "Use only currently eligible declared work; retain every adverse, unknown and unentered case.",
        "Independent scoped eligibility or a named remaining requirement.") for key, kind in sorted(OUTCOMES.items()))
    return RobustInquirySpecification("inquiry." + selection.policy_id, "Which declared supplier action is justified before this case's reference outcome?",
        (), distinguishing_assessment, selection.scope, "A small reduction indicator cannot repair invalid chemistry or biological transfer.",
        InquiryQuestionKind.REFINE, target, requirements, connections, selection.requirement_id("decision"), outcomes,
        AuthorityAction.SIMULATION_EXECUTION)


def missing_policy_frontier(specification):
    """Preserve the complete unassessed target; this does not supply any gate."""
    return InquiryTargetFrontier("frontier." + specification.specification_id,
        identity(specification.target, specification.target.target_id),
        tuple(InquiryRequirementFinding(identity(row, row.requirement_id), None, ()) for row in specification.requirements),
        tuple(InquiryClaimFinding(row, specification.target.scope, AssessmentDisposition.NOT_ATTEMPTED, None, (),
            "No independent scientific target assessment is supplied.") for row in specification.target.required_claims), ())


def missing_policy_observation(specification, state):
    return InquiryObservation("observation." + state.state_id, identity(specification, specification.specification_id),
        "initial", ScientificOutcomeKind.MISSING, specification.distinguishing_assessment, None, (), (),
        specification.endpoint, state.information_cutoff, "No assessed indicator or future reference outcome is presumed.")


def _empty_alternative(aid, specification, state):
    return TargetDirectedAlternative(aid, identity(specification, specification.specification_id), identity(state, state.state_id),
        InquiryAction.HOLD, tuple(row.outcome_id for row in specification.outcomes), InquiryAlternativeKind.WAIT,
        specification.question_requirement_id, specification.endpoint, "Retain the unsupported supplier decision.",
        "Complete missing eligibility and source-bound successor", (), (), (), InquiryCost(None, None, None),
        "No native entry", "Independent required evidence and an actual authored continuation", "The missing requirement is independently supplied.")


def _causal_stock(state):
    pre_action_cutoff(state.information_cutoff)
    for row in state.stock:
        # The independent context/clock gate must assess unknown provenance;
        # an explicit future or foreign-clock record is refused even if someone
        # supplied a positive gate finding. Earlier retained outcomes stay dated.
        if (row.scope.clock_id != state.information_cutoff.clock_id or (row.scope.information_cutoff is not None
                and not cutoff_precedes(row.scope.information_cutoff, state.information_cutoff))):
            raise ValueError("policy stock changes its clock or includes a future outcome")


def _indicator_reasons(selection, state, indicator, checkpoint):
    reasons = []
    if indicator is None:
        return ("INDICATOR_ABSENT",)
    exact(indicator, JointIndicatorAssessment)
    source = indicator.selection
    if not cutoff_precedes(source.information_cutoff, state.information_cutoff):
        raise ValueError("future indicator input cannot enter any prospective policy branch")
    if (source.scope != selection.scope or source.context != selection.context.identity
            or source.supplier != selection.selected_supplier):
        return ("INDICATOR_SCOPE_OR_SUPPLIER_MISMATCH",)
    expected = (*selection.study.acceptance.absolute_log_endpoint_tolerances,
                *selection.study.acceptance.absolute_log_endpoint_tolerances,
                *selection.study.acceptance.paired_log_endpoint_tolerances)
    if tuple(value.fraction for value in source.log_tolerances) != tuple(expected):
        reasons.append("INDICATOR_TOLERANCE_MISMATCH")
    if not source.valid_from <= state.information_cutoff.coordinate <= source.valid_until:
        reasons.append("INDICATOR_UNAVAILABLE_OR_EXPIRED")
    products = {row.product for row in state.stock}
    if not {selection.identity, indicator.identity, source.identity, *source.sources} <= products:
        reasons.append("INDICATOR_OR_FROZEN_SELECTION_NOT_IN_AUTHENTICATED_STOCK")
    if source.interpretation == "DEVELOPMENT_HEURISTIC":
        reasons.append("HEURISTIC_CANNOT_ADMIT_REDUCED_WORK")
    if source.interpretation == "CALIBRATED_PREDICTOR" and any(
            value.fraction == 0 for value in checkpoint.endpoint_error_probabilities):
        reasons.append("ZERO_RISK_REQUIRES_A_RIGOROUS_BOUND")
    if indicator.eta.fraction > selection.threshold:
        reasons.append("JOINT_INDICATOR_EXCEEDS_ALLOCATION")
    return tuple(sorted(reasons))


@dataclass(frozen=True, slots=True)
class PolicyGateFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/policy-gate-finding"
    alternative_id: str
    reason_codes: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.alternative_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        require_sorted_unique_strings(self.missing_requirement_ids, field_name="missing_requirement_ids")


@dataclass(frozen=True, slots=True)
class FinitePolicyComposition:
    selection: FiniteResponsePolicy
    specification: RobustInquirySpecification
    state: WorkBoundInquiryState
    checkpoint_id: str
    indicator: JointIndicatorAssessment | None
    templates: tuple[TargetDirectedAlternative, ...]
    frontier: InquiryTargetFrontier
    observation: InquiryObservation
    menu: RobustInquiryMenu
    policy: RobustInquiryPolicy
    gates: tuple[PolicyGateFinding, ...]


def compose_finite_policy(selection, specification, state, *, checkpoint_id, templates=(),
                          frontier=None, observation=None, indicator=None):
    """Construct the complete shared menu; never schedule or invent missing work.

    Each supplied ACT template must come from supported successor authoring.
    The public commitment reprojects its actual work and custody independently.
    Missing templates remain named HOLD alternatives in the complete census.
    """
    exact(selection, FiniteResponsePolicy)
    exact(specification, RobustInquirySpecification)
    exact(state, WorkBoundInquiryState)
    base_connections = policy_requirements(selection)[1]
    if specification != finite_policy_specification(selection,
            distinguishing_assessment=specification.distinguishing_assessment, required_claims=specification.target.required_claims,
            supporting_connections=tuple(row for row in specification.connections if row not in base_connections)):
        raise ValueError("policy specification changes the frozen complete question, gates or outcome map")
    if state.specification != identity(specification, specification.specification_id):
        raise ValueError("policy state changes its exact frozen specification")
    _causal_stock(state)
    checkpoint = next((row for row in selection.sequential.checkpoints if row.checkpoint_id == checkpoint_id), None)
    if checkpoint is None or checkpoint.information_cutoff != state.information_cutoff:
        raise ValueError("policy uses an undeclared or differently timed checkpoint")
    if (len(state.previous_decisions) >= len(selection.sequential.checkpoints)
            or selection.sequential.checkpoints[len(state.previous_decisions)] != checkpoint):
        raise ValueError("finite checkpoint allowance is exhausted, repeated or out of order")
    frontier = missing_policy_frontier(specification) if frontier is None else frontier
    observation = missing_policy_observation(specification, state) if observation is None else observation
    exact(frontier, InquiryTargetFrontier)
    exact(observation, InquiryObservation)
    if type(templates) is not tuple:
        raise ValueError("authored successor templates must retain their complete immutable census")
    require_sorted_unique_ids(templates, attribute="alternative_id", field_name="templates")
    by_id = {row.alternative_id: row for row in templates}
    if len({row.work for row in templates}) != len(templates):
        raise ValueError("finite menu aliases the same scientific work as different suppliers or repairs")
    if not by_id.keys() <= set(selection.alternative_ids) - {"hold"}:
        raise ValueError("policy cannot add an undeclared supplier or refinement")
    supplied = {row.requirement.object_id for row in frontier.requirement_findings if row.supplied}
    common = _prerequisite_closure(specification, selection.common_requirements)
    missing_common = common - supplied
    indicator_reasons = _indicator_reasons(selection, state, indicator, checkpoint)
    reduced_requirements = _prerequisite_closure(specification,
        (selection.requirement_id("indicator-validity"), selection.sequential.bound_validity_requirement_id))
    priorities = {"reduced": len(selection.refinements) + 2, "reference": 1,
        **{row.alternative_id: len(selection.refinements) + 1 - i for i, row in enumerate(selection.refinements)}}
    assumption = InquiryPolicyAssumption("assumption." + selection.policy_id + ".finite-order",
        "Prefer eligible reduced use, then the frozen ordered finite repairs, then the single declared reference; missing eligibility returns HOLD.",
        (), selection.canonical_bytes().decode("utf-8").removesuffix("\n"))
    rules = (
        InquiryCriterionRule("finite-order", InquiryCriterionRole.TARGET_PROGRESS, "declared-order", True,
            "A deterministic policy order; this is neither a probability nor a measured scientific benefit."),
        InquiryCriterionRule("capability", InquiryCriterionRole.ENABLED_CAPABILITY, "declared-step", True,
            "One exact authored continuation at the selected finite stage."),
        InquiryCriterionRule("discrimination", InquiryCriterionRole.DISCRIMINATION, "declared-step", True,
            "Retain the named requirement and its independent falsifier."),
        InquiryCriterionRule("cost", InquiryCriterionRole.COST, "s", False,
            "Actual complete CPU expense or explicitly unknown expense.", "cpu_seconds"),
    )
    alternatives, gates = [_empty_alternative("hold", specification, state)], []
    for aid in selection.alternative_ids:
        if aid == "hold":
            continue
        template = by_id.get(aid)
        missing = set(missing_common)
        reasons = []
        if selection.selected_supplier is None:
            reasons.append("JUSTIFIED_SUPPLIER_NOT_SELECTED")
        if selection.identity not in {row.product for row in state.stock}:
            reasons.append("FROZEN_POLICY_NOT_IN_AUTHENTICATED_STOCK")
        required = set(common)
        if aid == "reduced":
            reasons.extend(indicator_reasons)
            required.update(reduced_requirements)
        elif aid == "reference":
            if selection.study.acceptance.reference_fallback is None:
                reasons.append("REFERENCE_FALLBACK_NOT_SELECTED")
            required.add(selection.requirement_id("reference-entry"))
            if template is not None and template.reuse_completion is not None:
                required.add(selection.requirement_id("reference-reuse"))
        else:
            refinement = next(row for row in selection.refinements if row.alternative_id == aid)
            if set(refinement.requirement_ids) <= supplied and "JOINT_INDICATOR_EXCEEDS_ALLOCATION" not in indicator_reasons:
                reasons.append("DECLARED_REPAIR_NO_LONGER_REQUIRED")
        required = _prerequisite_closure(specification, required)
        missing.update(required - supplied)
        if missing:
            reasons.append("INDEPENDENT_ELIGIBILITY_MISSING")
        if template is None:
            reasons.append("AUTHORED_SUCCESSOR_ABSENT")
            alternative = _empty_alternative(aid, specification, state)
        else:
            exact(template, TargetDirectedAlternative)
            if (template.action is not InquiryAction.ACT or template.supplier is None
                    or template.specification != identity(specification, specification.specification_id)
                    or template.state != identity(state, state.state_id) or template.scope != selection.scope
                    or template.eligible_outcomes != tuple(row.outcome_id for row in specification.outcomes)):
                raise ValueError("policy template changes actual ACT bindings or its complete outcome map")
            if aid.startswith("refine.") and template.kind not in {InquiryAlternativeKind.REFINE, InquiryAlternativeKind.REUSE, InquiryAlternativeKind.ADOPT}:
                raise ValueError("finite repair must preserve its actual refinement or authenticated reuse meaning")
            operands = {selection.identity}
            if selection.selected_supplier is not None:
                operands.add(selection.selected_supplier)
            if aid == "reference" and selection.study.acceptance.reference_fallback is not None:
                operands.add(selection.study.acceptance.reference_fallback)
            if not operands <= set(template.work.scientific_operands):
                raise ValueError("successor work omits the exact frozen policy, selected supplier or reference")
            attempts = tuple(row for row in state.attempt_work_bindings
                if row.work == template.work or row.configuration == template.successor_config)
            allowance = (selection.maximum_reference_attempts if aid == "reference" else
                next(row.maximum_attempts for row in selection.refinements if row.alternative_id == aid) if aid.startswith("refine.") else None)
            if allowance is not None and len(attempts) >= allowance and template.reuse_completion is None:
                reasons.append("DECLARED_STAGE_ATTEMPT_ALLOWANCE_EXHAUSTED")
            required.update(_prerequisite_closure(specification, template.prerequisite_requirement_ids))
            missing.update(required - supplied)
            if missing:
                reasons.append("INDEPENDENT_ELIGIBILITY_MISSING")
            supplier = replace(template.supplier, prerequisite_requirement_ids=tuple(sorted(required)),
                unavailable_reason_codes=tuple(sorted(set(template.supplier.unavailable_reason_codes) | set(reasons))))
            criteria = tuple(sorted((InquiryCriterionAssessment(rule.criterion_id,
                template.expense_bound.cpu_seconds if rule.role is InquiryCriterionRole.COST else Decimal(priorities[aid]) if rule.criterion_id == "finite-order" else Decimal(1),
                template.expense_bound.cpu_seconds if rule.role is InquiryCriterionRole.COST else Decimal(priorities[aid]) if rule.criterion_id == "finite-order" else Decimal(1),
                rule.unit, (), (assumption.assumption_id,), rule.justification) for rule in rules), key=lambda row: row.criterion_id))
            alternative = replace(template, supplier=supplier, prerequisite_requirement_ids=tuple(sorted(required)), criteria=criteria)
        alternatives.append(alternative)
        gates.append(PolicyGateFinding(aid, tuple(sorted(set(reasons))), tuple(sorted(missing))))
    menu = RobustInquiryMenu("menu." + selection.policy_id + "." + state.state_id,
        identity(specification, specification.specification_id), identity(state, state.state_id),
        tuple(sorted(alternatives, key=lambda row: row.alternative_id)), frontier, observation)
    policy = RobustInquiryPolicy("policy." + selection.policy_id, menu.specification, selection.max_cost,
        selection.max_operations, selection.max_waves, selection.max_depth, InquiryOrdering.LEXICOGRAPHIC,
        rules, (assumption,), IncomparableResolution.HOLD)
    # Shared validation authenticates all frontier/source joins even when this
    # domain gate already knows that the scientific decision must be HOLD.
    with localcontext() as context:
        context.prec = _cost_precision(state, selection, templates)
        evaluate_robust_inquiry(specification, state, menu, policy, observation.outcome_id)
    return FinitePolicyComposition(selection, specification, state, checkpoint_id, indicator, templates,
        frontier, observation, menu, policy, tuple(gates))


def _prerequisite_closure(specification, selected):
    requirements = {row.requirement_id: row for row in specification.requirements}
    result, pending = set(), list(selected)
    while pending:
        key = pending.pop()
        if key not in requirements:
            raise ValueError("policy prerequisite is outside the complete scientific graph")
        if key not in result:
            result.add(key)
            pending.extend(requirements[key].further_requirement_ids)
    return result


def _cost_precision(state, selection, templates):
    values = [getattr(cost, name) for cost in (selection.max_cost, *(row.cost for row in state.cost_events),
        *(row.expense_bound for row in templates)) for name in ("cpu_seconds", "wall_seconds", "retained_bytes")]
    present = [value for value in values if value is not None]
    if not present:
        return 50
    return max(50, max(len(value.as_tuple().digits) + max(value.as_tuple().exponent, 0) for value in present)
        + max(-value.as_tuple().exponent for value in present) + len(str(len(present))) + 8)


def recheck_policy_composition(composition):
    if type(composition) is not FinitePolicyComposition:
        raise TypeError("requires an exact finite policy composition")
    actual = compose_finite_policy(composition.selection, composition.specification, composition.state,
        checkpoint_id=composition.checkpoint_id, templates=composition.templates, frontier=composition.frontier,
        observation=composition.observation, indicator=composition.indicator)
    if actual != composition:
        raise ValueError("finite policy composition changed after its domain assessment")
    return actual


def choose_finite_policy(composition, *, decision_id, campaign, right, actor_id):
    """Delegate actual selection and authority to shared work-bound inquiry."""
    actual = recheck_policy_composition(composition)
    with localcontext() as context:
        context.prec = _cost_precision(actual.state, actual.selection, actual.templates)
        return choose_robust_inquiry(decision_id=decision_id, specification=actual.specification,
            state=actual.state, menu=actual.menu, policy=actual.policy, campaign=campaign, right=right,
            actor_id=actor_id, outcome_id=actual.observation.outcome_id)
