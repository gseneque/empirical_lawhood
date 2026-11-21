# SPDX-License-Identifier: MPL-2.0
"""Disclosed numerical fixtures with explicitly synthetic method/receipt authority.

Only tests consume these records. They are not installed supplier results,
actual decisions, native reference validity or scientific qualification.
"""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_decisions import retained_policy_decision
from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import choose_finite_policy, compose_finite_policy
from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import build_reference_finding_report
from empirical_lawhood.domains.rubisco.rubisco_response.biological_support import assess_predictive_support, selection_from_study
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.retained_inquiry import retained_inquiry_specification
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import response_draft
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import predict_response_study
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import AcquisitionEvent, InquiryAttempt, InquiryAttemptStatus, InquiryCost, InquiryEvidence
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryAttemptWorkBinding, ScientificInquiryWork, WorkBoundInquiryState
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.recursive_inquiry import InquiryAction
from empirical_lawhood.design.recursive_inquiry_policy import make_robust_successor_intent
from empirical_lawhood.storage.contracts.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding, RecursiveWaveMember
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, WorkBoundInquiryDecisionPacket
from tests.test_recursive_inquiry_policy import obj, policy_case
from tests.test_rubisco_response_policy import policy_case_inputs
from tests.test_rubisco_response_comparison_preparation import design as base_design


def design(*, original=None, reuse_count=1):
    selected = base_design(original=original)
    if reuse_count != 1:
        from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import comparison_design
        spec = replace(selected.specification, acceptance=replace(selected.specification.acceptance, planned_reuse_count=reuse_count))
        initial = comparison_design(selected.original_study, spec, design_id=selected.design_id,
            false_admission_denominator=selected.false_admission_denominator, scale=selected.scale)
        selected = replace(initial, cases=tuple(replace(row, policy=replace(old.policy, study=initial.study), parity=old.parity)
            for row, old in zip(initial.cases, selected.cases, strict=True)))
    return replace(selected, cases=tuple(replace(row, policy=replace(row.policy, selected_supplier=obj("supplier.exposed.comparison")))
        for row in selected.cases))


def work(selected, name):
    return ScientificInquiryWork(obj("method.exposed." + name), (selected.study.identity,), scientific_scope(selected.study), obj("observation.exposed"))


def state(selected, name, rows):
    """rows are (actual work or None, CPU seconds or None, original status)."""
    specification = retained_inquiry_specification(response_draft(selected.original_study, selected.study))
    attempts, events, bindings = [], [], []
    for i, (original_work, cpu, status) in enumerate(rows):
        key = name + "." + str(i)
        config, receipt = obj("config." + key), obj("receipt." + key)
        attempt = InquiryAttempt("attempt." + key, config, status, receipt, (), "Synthetic exposed cost-census control")
        attempts.append(attempt)
        events.append(AcquisitionEvent("event." + key, attempt.attempt_id, receipt,
            InquiryCost(None if cpu is None else D(cpu), D(1), D(100))))
        bindings.append(InquiryAttemptWorkBinding(attempt.attempt_id, config, original_work,
            obj("wave." + key, "empirical-lawhood/runtime/authored-recursive-wave"),
            obj("plan." + key, "empirical-lawhood/runtime/development-execution-plan"),
            obj("task." + key, "empirical-lawhood/runtime/execution-task"), receipt))
    return WorkBoundInquiryState(state_id="state." + name, specification=ObjectIdentity.from_record(specification.specification_id, specification),
        information_cutoff=InformationCutoff("cutoff." + name, "clock.rubisco.physical-seconds", CausalPhase.POST_OUTCOME, D(100)),
        stock=(), operational_census=tuple(attempts), previous_decisions=(), cost_events=tuple(events), wave_count=1, depth_count=1,
        attempt_work_bindings=tuple(bindings))


def arm_report(selected, arm, *, bad=False, failed=False, known_method=True):
    study = selected.study
    predictions = predict_response_study(study, prediction_id="prediction.exposed." + arm)
    if bad:
        first = predictions.predictions[0]
        scenario = first.support.scenarios[0]
        value = scenario.region.values[0]
        value = replace(value, mutant=EndpointValues.of(100, value.mutant.specificity.fraction))
        scenario = replace(scenario, region=replace(scenario.region, values=(value, *scenario.region.values[1:])))
        first = replace(first, support=replace(first.support, scenarios=(scenario, *first.support.scenarios[1:])))
        predictions = replace(predictions, predictions=(first, *predictions.predictions[1:]))
    logical = LogicalArtifactIdentity("artifact.exposed." + arm, predictions.fingerprint(), predictions.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
        ArtifactGenericValidation("validator.exposed", "1.0.0", "1" * 64, predictions.SCHEMA, ArtifactProfile.CANONICAL_JSON))
    physical = ArtifactMaterialization("materialization.exposed." + arm, logical.logical_artifact_id,
        "storage.exposed", arm + ".json", predictions.fingerprint(), len(predictions.canonical_bytes()), "none")
    receipt = CanonicalTaskReceipt("receipt.exposed." + arm, "run.exposed", "task." + arm + ".0", "attempt." + arm + ".0", "2" * 40,
        (), (physical,), (logical,), (ReceiptCheck("exposed-only", not failed, () if not failed else ("EXPOSED_FAILURE",)),),
        OperationalStatus.SUCCEEDED if not failed else OperationalStatus.FAILED, () if not failed else ("EXPOSED_FAILURE",))
    method = (study.acceptance.reference_method if arm == "reference" else study.acceptance.conventional_baseline if arm == "conventional"
              else selected.cases[0].parity.approximation_method)
    original_work = replace(work(selected, arm), method=method)
    original_state = state(selected, arm, ((original_work if known_method else None, "10", InquiryAttemptStatus.COMPLETED),))
    pin = ObjectIdentity.from_record(receipt.receipt_id, receipt)
    attempt = replace(original_state.operational_census[0], receipt=pin,
        status=InquiryAttemptStatus.FAILED if failed else InquiryAttemptStatus.COMPLETED,
        products=() if failed else (predictions.identity,))
    original_state = replace(original_state, operational_census=(attempt,),
        cost_events=(replace(original_state.cost_events[0], receipt=pin),),
        attempt_work_bindings=(replace(original_state.attempt_work_bindings[0], witness=pin),))
    specification = retained_inquiry_specification(response_draft(selected.original_study, study))
    biology = assess_predictive_support(selection_from_study(study), assessment_id="biology.exposed." + arm)
    return build_reference_finding_report(study, predictions, biology, report_id="report.exposed." + arm,
        producing_receipts=(receipt,), inquiry_specification=specification, work_state=original_state)


def decision(selected, case_index, *, hold=False, already_seen=None, reference=False, previous=()):
    selection = selected.cases[case_index].policy
    values = policy_case_inputs(selected=selection, size=Fraction(1, 10) if reference else Fraction(1, 100),
        missing=(selection.requirement_id("context-and-clock"),) if hold else ())
    checkpoint = selection.sequential.checkpoints[len(previous)]
    values.state = replace(values.state, state_id="state.policy." + selection.case_id + "." + str(len(previous)),
        information_cutoff=checkpoint.information_cutoff,
        previous_decisions=tuple(sorted((row.identity for row in previous), key=lambda row: row.object_id)))
    if already_seen is not None:
        value = InquiryEvidence("evidence.exposed.already-seen", already_seen, None, selection.scope,
            ContributionRole.RETAINED_ANALYSIS_INPUT, (), (), source_contract=obj("source.exposed.prior"))
        values.state = replace(values.state, stock=tuple(sorted((*values.state.stock, value), key=lambda row: row.evidence_id)))
    templates = tuple(replace(row, state=ObjectIdentity.from_record(values.state.state_id, values.state)) for row in values.templates)
    composition = compose_finite_policy(selection, values.specification, values.state, checkpoint_id=checkpoint.checkpoint_id,
        templates=templates, frontier=values.frontier, indicator=values.indicator)
    auth = policy_case("rubisco")
    right = replace(auth.right, action=composition.specification.required_decision_action)
    campaign = replace(auth.campaign, system_ids=(composition.specification.target.scope.system_id,),
        world_ids=(composition.specification.target.scope.world_id,),
        target_claim_ids=tuple(row.object_id for row in composition.specification.target.required_claims), decision_rights=(right,))
    chosen = choose_finite_policy(composition, decision_id="decision." + selection.case_id + "." + str(len(previous)), campaign=campaign,
        right=right, actor_id=auth.actor_id)
    inventory = (("tests/exposed-comparison-fixture.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(inventory, sha256(canonical_json_bytes(inventory)).hexdigest(), "2" * 64, "3" * 40, True)
    records = {"specification.json": composition.specification, "state.json": composition.state, "sources.json": InquiryStateSources(()),
        "menu.json": composition.menu, "policy.json": composition.policy, "campaign.json": campaign, "right.json": right,
        "decision.json": chosen, "implementation.json": implementation}
    picked = next(row for row in composition.menu.alternatives if row.alternative_id == chosen.selected_alternative_id)
    if picked.action is InquiryAction.ACT:
        records["intent.json"] = make_robust_successor_intent(intent_id="intent." + selection.case_id, decision=chosen,
            specification=composition.specification, menu=composition.menu)
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record("inquiry-member." + name.removesuffix(".json"), row),
        len(row.canonical_bytes())) for name, row in sorted(records.items()))
    packet = WorkBoundInquiryDecisionPacket("packet." + selection.case_id, members)
    return retained_policy_decision(selection, packet, records)
