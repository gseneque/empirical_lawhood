# SPDX-License-Identifier: MPL-2.0
"""Exposed finite-policy controls; no native work or scientific qualification."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as Q
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import FiniteResponsePolicy, PermittedPolicyRefinement, _prerequisite_closure, choose_finite_policy, compose_finite_policy, finite_policy_specification, missing_policy_frontier
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import CheckpointErrorAllocation, FiniteSequentialProcedure, JointErrorVertex, JointIndicatorAssessment, JointIndicatorInput, assess_joint_indicator
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec
from empirical_lawhood.science.inquiry.recursive_inquiry import AcquisitionEvent, InquiryAttempt, InquiryAttemptStatus, InquiryCost, InquiryEvidence, identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import CompletedInquiryWork, InquiryAttemptWorkBinding, InquiryRequirementFinding, ScientificInquiryWork, WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A, AssessmentPhase, ContributionRole, RequirementSupplyAssessment, ScientificConnectionSpec
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.recursive_authoring import SupplierProposal
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import InquiryAlternativeKind, TargetDirectedAlternative
from tests.test_recursive_inquiry_policy import obj, policy_case


def selection(*, max_operations=6, refinements=True, supplier=True, risk=Fraction(1, 1000)):
    study = disclosed_study()
    cutoffs = tuple(InformationCutoff("cutoff.policy." + str(i), "clock.rubisco.physical-seconds", CausalPhase.PRE_ACTION, D(i * 10))
                    for i in (1, 2, 3))
    procedure = FiniteSequentialProcedure("procedure.exposed.policy",
        tuple(CheckpointErrorAllocation("checkpoint." + str(i), cutoff, (Q.of(risk),) * 6)
              for i, cutoff in enumerate(cutoffs, 1)), Q.of(Fraction(1, 20)), "requirement.exposed.sequential")
    study = replace(study, acceptance=replace(study.acceptance, uncertainty_procedure=procedure.identity,
        reference_fallback=study.acceptance.reference_method, permitted_refinement_ids=("allowance",) if refinements else (),
        maximum_refinements=1 if refinements else 0,
        checkpoint_rule="Three disclosed pre-action checkpoints with a finite joint error allocation"))
    return FiniteResponsePolicy("finite.exposed.policy", study, study.cases.cases[0].case_id,
        obj("supplier.exposed") if supplier else None, procedure,
        (PermittedPolicyRefinement("allowance", ("requirement.finite.exposed.policy.indicator-validity",), 1),) if refinements else (),
        max_operations, 6, 6, InquiryCost(None, None, None))


def indicator(policy, *, size=Fraction(1, 100), interpretation="RIGOROUS_BOUND"):
    jacobian = tuple(tuple(Q.of(value) for value in row) for row in ((1, 1), (1, -1), (2, 1), (1, 0), (1, 0), (0, 1)))
    inputs = JointIndicatorInput("input.exposed.indicator", policy.scope, policy.context.identity,
        policy.selected_supplier or obj("supplier.not-selected"), ("parameter.a", "parameter.b"), ("s^-1", "s^-1"), jacobian,
        (JointErrorVertex("vertex.minus", (Q.of(-size),) * 2), JointErrorVertex("vertex.plus", (Q.of(size),) * 2)),
        (Q.of(0),) * 6, tuple(Q.of(value) for value in (*policy.study.acceptance.absolute_log_endpoint_tolerances,
            *policy.study.acceptance.absolute_log_endpoint_tolerances, *policy.study.acceptance.paired_log_endpoint_tolerances)),
        interpretation, policy.sequential.checkpoints[0].information_cutoff, D(0), D(30), (obj("operand.exposed"),))
    return assess_joint_indicator(inputs, assessment_id="assessment.exposed.indicator")


def policy_case_inputs(*, selected=None, size=Fraction(1, 100), interpretation="RIGOROUS_BOUND", missing=()):
    selected = selected or selection()
    value = indicator(selected, size=size, interpretation=interpretation)
    claim = obj("claim.exposed.response", ClaimSpec.SCHEMA)
    specification = finite_policy_specification(selected, distinguishing_assessment=obj("assessment.exposed.contract"), required_claims=(claim,))
    supplied = (_prerequisite_closure(specification, selected.common_requirements)
        | {selected.requirement_id(name) for name in ("indicator-validity", "reference-entry", "reference-reuse")}
        | {selected.sequential.bound_validity_requirement_id}) - set(missing)
    requirements = {row.requirement_id: row for row in specification.requirements}
    connections = tuple(ScientificConnectionSpec("connection.exposed." + key, key, "supplier.exposed.assessment", "product",
        "independent-evidence", requirements[key].assessment_operation_id, "claim.exposed." + key,
        ContributionRole.RETAINED_ANALYSIS_INPUT, requirements[key].falsifier) for key in sorted(supplied))
    specification = finite_policy_specification(selected, distinguishing_assessment=specification.distinguishing_assessment,
        required_claims=(claim,), supporting_connections=connections)
    witness = obj("operand.exposed")
    products = {selected.identity, value.identity, value.selection.identity, *value.selection.sources}
    stock = [InquiryEvidence("evidence." + product.object_id, product, None, selected.scope,
        ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=witness) for product in sorted(products, key=lambda row: row.object_id)]
    frontier = missing_policy_frontier(specification)
    findings = []
    for finding in frontier.requirement_findings:
        key = finding.requirement.object_id
        if key not in supplied:
            findings.append(finding)
            continue
        requirement = requirements[key]
        connection = next(row for row in connections if row.requirement_id == key)
        assessments = tuple(sorted((RequirementSupplyAssessment("assessment." + key + "." + phase.value.lower(),
            identity(requirement, key), identity(connection, connection.connection_id), phase, A.SATISFIED,
            selected.case_id, (witness,), ()) for phase in AssessmentPhase), key=lambda row: row.assessment_id))
        for row in assessments:
            stock.append(InquiryEvidence(row.assessment_id, identity(row, row.assessment_id), None,
                requirement.scope, ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=witness))
        findings.append(InquiryRequirementFinding(finding.requirement, identity(connection, connection.connection_id), assessments))
    state = WorkBoundInquiryState(state_id="state.exposed.policy", specification=identity(specification, specification.specification_id),
        information_cutoff=selected.sequential.checkpoints[0].information_cutoff, stock=tuple(sorted(stock, key=lambda row: row.evidence_id)),
        operational_census=(), previous_decisions=(), cost_events=(), wave_count=0, depth_count=0, attempt_work_bindings=())
    templates = []
    for aid in selected.alternative_ids:
        if aid == "hold":
            continue
        work = ScientificInquiryWork(obj("method.exposed." + aid), tuple(sorted({selected.identity, selected.selected_supplier,
                *(() if aid != "reference" else (selected.study.acceptance.reference_fallback,))}, key=lambda row: row.object_id)),
            selected.scope, specification.distinguishing_assessment)
        supplier = SupplierProposal("proposal.exposed." + aid, specification.question_requirement_id,
            ("operation.exposed." + aid,), (), True, "Disclosed software control; this is not an authored or admitted native supplier.")
        templates.append(TargetDirectedAlternative(aid, state.specification, identity(state, state.state_id), InquiryAction.ACT,
            tuple(row.outcome_id for row in specification.outcomes), InquiryAlternativeKind.REFINE if aid.startswith("refine.") else InquiryAlternativeKind.ACQUIRE,
            specification.question_requirement_id, selected.scope, "Check the declared finite supplier step", "All six log endpoints", (), (), (),
            InquiryCost(None, None, None), "exposed.control", "Independent complete endpoint assessment", "An adverse endpoint or missing premise refuses use",
            supplier=supplier, work=work, successor_draft=obj("draft.exposed." + aid), successor_config=obj("config.exposed." + aid),
            input_origins=obj("origins.exposed." + aid), capability_id="capability.exposed." + aid + "@1.0.0", planned_operation_count=1))
    return N(selection=selected, specification=specification, state=state, indicator=value,
        frontier=replace(frontier, requirement_findings=tuple(findings)), templates=tuple(templates))


def compose(case):
    templates = tuple(replace(row, state=identity(case.state, case.state.state_id)) for row in case.templates)
    return compose_finite_policy(case.selection, case.specification, case.state, checkpoint_id="checkpoint.1",
        templates=templates, frontier=case.frontier, indicator=case.indicator)


def choose(composition):
    auth = policy_case("rubisco")
    right = replace(auth.right, action=composition.specification.required_decision_action)
    campaign = replace(auth.campaign, system_ids=(composition.specification.target.scope.system_id,),
        world_ids=(composition.specification.target.scope.world_id,),
        target_claim_ids=tuple(row.object_id for row in composition.specification.target.required_claims), decision_rights=(right,))
    return choose_finite_policy(composition, decision_id="decision.exposed.policy", campaign=campaign, right=right, actor_id=auth.actor_id)


def test_indicator_preserves_signed_correlation_absolute_and_paired_outputs():
    result = indicator(selection())
    assert result.eta.fraction == Fraction(3, 10)
    assert result.linear_support_bounds[1] == (Q.of(0), Q.of(0))
    assert result.signed_vertex_projections[0] == tuple(Q.of(value) for value in (Fraction(-2, 100), 0, Fraction(-3, 100), Fraction(-1, 100), Fraction(-1, 100), Fraction(-1, 100)))
    with localcontext() as context:
        context.prec = 2
        assert assess_joint_indicator(result.selection, assessment_id=result.assessment_id) == result
    assert decode_canonical_bytes(result.canonical_bytes(), JointIndicatorAssessment, maximum_bytes=100_000) == result
    with pytest.raises(ValueError, match="exact joint"):
        replace(result, eta=Q.of(0))
    with pytest.raises(ValueError, match="mutant-minus-WT"):
        replace(result.selection, jacobian=(*result.selection.jacobian[:4], (Q.of(0), Q.of(0)), result.selection.jacobian[5]))
    with pytest.raises(ValueError, match="empty error support"):
        replace(result.selection, vertices=())


def test_nonlinear_allowance_is_charged_without_cancelling_absolute_error():
    original = indicator(selection())
    inputs = replace(original.selection, nonlinear_allowances=(Q.of(Fraction(1, 10)),) + (Q.of(0),) * 5)
    result = assess_joint_indicator(inputs, assessment_id="assessment.allowance")
    assert result.normalized_error_bounds[0].fraction == Fraction(6, 5)
    assert result.eta.fraction == Fraction(6, 5)


def test_finite_joint_sequential_budget_keeps_all_checkpoints_and_requires_valid_bounds():
    procedure = selection().sequential
    assert procedure.allocated_error_probability.fraction == Fraction(18, 1000)
    assert "REQUIRING_VALID_CONDITIONAL" in procedure.interpretation
    with pytest.raises(ValueError, match="family error"):
        replace(procedure, family_error_probability=Q.of(Fraction(1, 100)))
    with pytest.raises(ValueError, match="spent twice"):
        replace(procedure, checkpoints=(procedure.checkpoints[0], procedure.checkpoints[0]))
    with pytest.raises(ValueError, match="strictly increasing"):
        replace(procedure, checkpoints=tuple(reversed(procedure.checkpoints)))
    with pytest.raises(ValueError, match="unimplemented audit"):
        replace(procedure, audit_design="CONVENIENT_REFERENCE_SUBSET")


def test_eligible_rigorous_indicator_uses_shared_work_bound_decision():
    result = compose(policy_case_inputs())
    decision = choose(result)
    assert decision.VERSION == "3.0.0" and decision.selected_alternative_id == "reduced"
    assert decision.unresolved_target_requirement_ids and decision.unresolved_target_claim_ids
    assert all(row.action is not InquiryAction.STOP for row in result.menu.alternatives)
    assert decode_canonical_bytes(result.selection.canonical_bytes(), FiniteResponsePolicy, maximum_bytes=1_000_000) == result.selection


@pytest.mark.parametrize("missing", ("context-and-clock", "supplier-selection"))
def test_small_indicator_cannot_override_missing_independent_eligibility(missing):
    policy = selection()
    case = policy_case_inputs(selected=policy, missing=(policy.requirement_id(missing),))
    result = compose(case)
    assert choose(result).selected_alternative_id == "hold"
    assert all(policy.requirement_id(missing) in row.missing_requirement_ids for row in result.gates)


def test_parent_gate_cannot_hide_an_unsupplied_chemical_prerequisite():
    policy = selection()
    primitive = "requirement.oxygen-state.exposed"
    original = policy.study.supplies[0]
    context = replace(original.context, context_id="context.exposed.oxygen-unresolved",
        chemistry=replace(original.context.chemistry, unresolved_requirement_ids=(primitive,)))
    scenarios = tuple(replace(row, ledger=replace(row.ledger, context=context.identity)) for row in original.scenarios)
    supply = replace(original, context=context, scenarios=scenarios)
    study = replace(policy.study, supplies=(supply, *policy.study.supplies[1:]),
        decisions=(replace(policy.study.decisions[0], context=context.identity), *policy.study.decisions[1:]))
    policy = replace(policy, study=study)
    result = compose(policy_case_inputs(selected=policy, missing=(primitive,)))
    assert choose(result).selected_alternative_id == "hold"
    assert all(primitive in row.missing_requirement_ids for row in result.gates)


def test_heuristic_and_uncalibrated_intervals_cannot_admit_reduced_work():
    case = policy_case_inputs(selected=selection(refinements=False), interpretation="DEVELOPMENT_HEURISTIC")
    result = compose(case)
    assert choose(result).selected_alternative_id == "reference"
    assert "HEURISTIC_CANNOT_ADMIT_REDUCED_WORK" in next(row for row in result.gates if row.alternative_id == "reduced").reason_codes
    policy = selection(refinements=False, risk=Fraction(0))
    result = compose(policy_case_inputs(selected=policy, interpretation="CALIBRATED_PREDICTOR"))
    assert choose(result).selected_alternative_id == "reference"
    case = policy_case_inputs(selected=selection(refinements=False), missing=("requirement.exposed.sequential",))
    assert choose(compose(case)).selected_alternative_id == "reference"


def test_excess_indicator_uses_declared_refinement_then_single_reference():
    assert choose(compose(policy_case_inputs(size=Fraction(1, 10)))).selected_alternative_id == "refine.allowance"
    result = compose(policy_case_inputs(selected=selection(refinements=False), size=Fraction(1, 10)))
    assert choose(result).selected_alternative_id == "reference"
    policy = selection(refinements=False)
    result = compose(policy_case_inputs(selected=policy, size=Fraction(1, 10), missing=(policy.requirement_id("reference-entry"),)))
    assert choose(result).selected_alternative_id == "hold"


def test_future_outcome_and_repeated_or_unselected_checkpoint_refuse():
    case = policy_case_inputs()
    row = case.state.stock[0]
    future = replace(row.scope, information_cutoff=replace(case.state.information_cutoff, phase=CausalPhase.POST_OUTCOME))
    case.state = replace(case.state, stock=(replace(row, scope=future), *case.state.stock[1:]))
    with pytest.raises(ValueError, match="future outcome"):
        compose(case)
    case = policy_case_inputs()
    case.state = replace(case.state, previous_decisions=(obj("decision.previous"),))
    with pytest.raises(ValueError, match="repeated or out of order"):
        compose(case)
    case = policy_case_inputs()
    with pytest.raises(ValueError, match="undeclared"):
        compose_finite_policy(case.selection, case.specification, case.state, checkpoint_id="checkpoint.unfrozen")


def test_finite_and_unknown_resource_budgets_hold_without_zero_filling():
    case = policy_case_inputs(selected=selection(max_operations=0))
    result = compose(case)
    decision = choose(result)
    assert decision.selected_alternative_id == "hold"
    assert "finite-allowance-exhausted" in next(row for row in decision.evaluations if row.alternative_id == "reduced").reason_codes
    policy = replace(selection(), max_cost=InquiryCost(D(1), None, None))
    decision = choose(compose(policy_case_inputs(selected=policy)))
    assert decision.selected_alternative_id == "hold"
    assert "unknown-required-expense" in next(row for row in decision.evaluations if row.alternative_id == "reduced").reason_codes


def add_attempt(case, aid, status, *, reuse=False, known=True):
    template = next(row for row in case.templates if row.alternative_id == aid)
    witness = obj("receipt.exposed." + aid)
    products = (obj("product.exposed." + aid),) if status is InquiryAttemptStatus.COMPLETED else ()
    attempt = InquiryAttempt("attempt.exposed." + aid, template.successor_config, status, witness, products, "Original exposed control attempt")
    binding = InquiryAttemptWorkBinding(attempt.attempt_id, attempt.operation, template.work if known else None,
        obj("wave.exposed", "empirical-lawhood/runtime/authored-recursive-wave"),
        obj("plan.exposed", "empirical-lawhood/runtime/development-execution-plan"),
        obj("task.exposed", "empirical-lawhood/runtime/execution-task"), witness)
    stock = (*case.state.stock, *(InquiryEvidence("evidence." + product.object_id, product, witness, case.selection.scope,
        ContributionRole.RETAINED_ANALYSIS_INPUT, (), ()) for product in products))
    case.state = replace(case.state, operational_census=(attempt,), attempt_work_bindings=(binding,),
        cost_events=(AcquisitionEvent("event.exposed." + aid, attempt.attempt_id, witness, InquiryCost(None, None, None)),),
        stock=tuple(sorted(stock, key=lambda row: row.evidence_id)), wave_count=1, depth_count=1)
    if reuse:
        completion = CompletedInquiryWork("completion.exposed." + aid, template.work, attempt.attempt_id, witness, products)
        case.frontier = replace(case.frontier, completed_work=(completion,))
        case.templates = tuple(replace(row, kind=InquiryAlternativeKind.REUSE, reuse_completion=completion) if row.alternative_id == aid else row for row in case.templates)
    return case


def test_failed_refinement_falls_back_once_and_failed_reference_stops():
    case = add_attempt(policy_case_inputs(size=Fraction(1, 10)), "refine.allowance", InquiryAttemptStatus.FAILED)
    assert choose(compose(case)).selected_alternative_id == "reference"
    case = add_attempt(policy_case_inputs(selected=selection(refinements=False), size=Fraction(1, 10)), "reference", InquiryAttemptStatus.FAILED)
    result = compose(case)
    assert choose(result).selected_alternative_id == "hold"
    assert "DECLARED_STAGE_ATTEMPT_ALLOWANCE_EXHAUSTED" in next(row for row in result.gates if row.alternative_id == "reference").reason_codes


def test_completed_fallback_requires_actual_reuse_and_independent_reference_admission():
    policy = selection(max_operations=1, refinements=False)
    case = add_attempt(policy_case_inputs(selected=policy, size=Fraction(1, 10)), "reference", InquiryAttemptStatus.COMPLETED)
    assert choose(compose(case)).selected_alternative_id == "hold"
    case = add_attempt(policy_case_inputs(selected=policy, size=Fraction(1, 10)), "reference", InquiryAttemptStatus.COMPLETED, reuse=True)
    decision = choose(compose(case))
    assert decision.selected_alternative_id == "reference"
    case = add_attempt(policy_case_inputs(selected=policy, size=Fraction(1, 10), missing=(policy.requirement_id("reference-reuse"),)),
        "reference", InquiryAttemptStatus.COMPLETED, reuse=True)
    assert choose(compose(case)).selected_alternative_id == "hold"


def test_uncertain_contact_cannot_be_relabelled_as_another_reference():
    case = add_attempt(policy_case_inputs(selected=selection(refinements=False), size=Fraction(1, 10)),
        "reference", InquiryAttemptStatus.UNCERTAIN_CONTACT, known=False)
    decision = choose(compose(case))
    assert decision.selected_alternative_id == "hold"
    assert "uncertain-contact-recovery-required" in next(row for row in decision.evaluations if row.alternative_id == "reference").reason_codes


def test_missing_supplier_public_commit_and_retained_read_enter_no_worker(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_inquiry as service
    from empirical_lawhood.api.domain_composition.rubisco_response.policy import commit_finite_response_policy
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources
    from tests.test_recursive_public_service import _plane

    def forbidden(*args, **kwargs):
        raise AssertionError("policy commitment or retained reading entered a worker")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    root = Path(__file__).resolve().parents[1]
    source = service.implementation_binding(root)
    monkeypatch.setattr(service, "implementation_binding", lambda _: source)
    plane = _plane(tmp_path / "selected")
    policy = selection(supplier=False)
    specification = finite_policy_specification(policy, distinguishing_assessment=obj("assessment.not-entered"),
        required_claims=(obj("claim.exposed", ClaimSpec.SCHEMA),))
    sources = InquiryStateSources(())
    state = service.project_inquiry_state(specification=specification, state_id="state.actual.empty",
        information_cutoff=policy.sequential.checkpoints[0].information_cutoff, sources=sources, artifact_writer=plane)
    result = compose_finite_policy(policy, specification, state, checkpoint_id="checkpoint.1")
    auth = policy_case("rubisco")
    right = replace(auth.right, action=specification.required_decision_action)
    campaign = replace(auth.campaign, system_ids=(specification.target.scope.system_id,),
        world_ids=(specification.target.scope.world_id,), target_claim_ids=("claim.exposed",), decision_rights=(right,))
    packet, records = commit_finite_response_policy(result, sources=sources, campaign=campaign, right=right, actor_id=auth.actor_id,
        project_root=root, artifact_writer=plane, output_dir=tmp_path / "selected/policy-decision")
    assert records["decision.json"].selected_alternative_id == "hold" and "intent.json" not in records
    assert len(records["menu.json"].alternatives) == 4
    assert service.read_inquiry_decision(directory=tmp_path / "selected/policy-decision", artifact_writer=plane) == (packet, records)
    assert records["state.json"].operational_census == ()


def test_policy_refinement_and_uncertainty_selection_cannot_drift_from_acceptance():
    policy = selection()
    with pytest.raises(ValueError, match="frozen uncertainty"):
        replace(policy, refinements=())
    with pytest.raises(ValueError, match="frozen uncertainty"):
        replace(policy, sequential=replace(policy.sequential, family_error_probability=Q.of(Fraction(1, 10))))


def test_missing_reduced_successor_can_use_the_one_available_reference():
    case = policy_case_inputs(selected=selection(refinements=False))
    case.templates = tuple(row for row in case.templates if row.alternative_id == "reference")
    assert choose(compose(case)).selected_alternative_id == "reference"


def test_complete_policy_census_detects_false_admission_and_always_abstain():
    from empirical_lawhood.domains.rubisco.rubisco_response.policy_service import PolicyAuditObservation, assess_policy_service
    study = disclosed_study()
    good = ((Q.of(0), Q.of(Fraction(1, 2))),) * 6
    rows = tuple(PolicyAuditObservation(case.identity, obj("decision." + case.case_id), "REDUCED", "AVAILABLE",
        "ASSESSED_VALID", obj("reference." + case.case_id), good) for case in study.cases.cases)
    result = assess_policy_service(study, rows, false_admission_denominator="ADMITTED_UNITS", assessment_id="service.good")
    assert len(result.units) == 1 and len(result.units[0].case_ids) == 2
    assert result.useful_service_bounds == (Q.of(1), Q.of(1))
    assert result.false_admission_conditional_bounds == (Q.of(0), Q.of(0))
    assert result.useful_service_disposition is result.false_admission_disposition is A.SATISFIED
    bad = replace(rows[0], normalized_absolute_error_bounds=((Q.of(2), Q.of(2)), *good[1:]))
    result = assess_policy_service(study, (bad, rows[1]), false_admission_denominator="ADMITTED_UNITS", assessment_id="service.false")
    assert result.false_admission_conditional_bounds == (Q.of(1), Q.of(1))
    assert result.useful_service_disposition is result.false_admission_disposition is A.FALSIFIED
    holds = tuple(replace(row, action="HOLD", reduced_state="NOT_ENTERED", normalized_absolute_error_bounds=None) for row in rows)
    result = assess_policy_service(study, holds, false_admission_denominator="ADMITTED_UNITS", assessment_id="service.abstain")
    assert result.useful_service_disposition is A.FALSIFIED and result.false_admission_conditional_bounds is None
    assert result.reference_coverage_disposition is A.SATISFIED
    with pytest.raises(ValueError, match="every selected case"):
        assess_policy_service(study, holds[:1], false_admission_denominator="ADMITTED_UNITS", assessment_id="service.omitted")


def test_unknown_reference_is_not_correct_and_refused_cases_remain_audited():
    from empirical_lawhood.domains.rubisco.rubisco_response.policy_service import PolicyAuditObservation, PolicyServiceAssessment, assess_policy_service
    study = disclosed_study()
    rows = tuple(PolicyAuditObservation(case.identity, obj("decision." + case.case_id), "REDUCED", "AVAILABLE",
        "UNKNOWN", None, None) for case in study.cases.cases)
    result = assess_policy_service(study, rows, false_admission_denominator="ALL_ASSIGNED_UNITS", assessment_id="service.unknown")
    assert result.useful_service_bounds == result.false_admission_assigned_bounds == (Q.of(0), Q.of(1))
    assert result.useful_service_disposition is result.false_admission_disposition is result.reference_coverage_disposition is A.UNEVALUABLE
    assert decode_canonical_bytes(result.canonical_bytes(), PolicyServiceAssessment, maximum_bytes=1_000_000) == result
    holds = tuple(replace(row, action="HOLD", reduced_state="NOT_ENTERED") for row in rows)
    result = assess_policy_service(study, holds, false_admission_denominator="ALL_ASSIGNED_UNITS", assessment_id="service.unassessed-refusals")
    assert result.useful_service_disposition is A.FALSIFIED and result.reference_coverage_disposition is A.UNEVALUABLE
    with pytest.raises(ValueError, match="unknown or failed"):
        replace(rows[0], normalized_absolute_error_bounds=((Q.of(0), Q.of(0)),) * 6)


def test_future_indicator_is_excluded_before_refinement_or_fallback_selection():
    case = policy_case_inputs()
    inputs = replace(case.indicator.selection, information_cutoff=case.selection.sequential.checkpoints[1].information_cutoff)
    case.indicator = assess_joint_indicator(inputs, assessment_id=case.indicator.assessment_id)
    with pytest.raises(ValueError, match="future indicator"):
        compose(case)


def test_expired_indicator_falls_back_and_a_changed_composition_cannot_commit():
    from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import recheck_policy_composition
    case = policy_case_inputs(selected=selection(refinements=False))
    inputs = replace(case.indicator.selection, information_cutoff=replace(case.state.information_cutoff, coordinate=D(5)), valid_until=D(5))
    case.indicator = assess_joint_indicator(inputs, assessment_id=case.indicator.assessment_id)
    result = compose(case)
    assert choose(result).selected_alternative_id == "reference"
    assert "INDICATOR_UNAVAILABLE_OR_EXPIRED" in next(row for row in result.gates if row.alternative_id == "reduced").reason_codes
    with pytest.raises(ValueError, match="changed after"):
        recheck_policy_composition(replace(result, gates=()))
