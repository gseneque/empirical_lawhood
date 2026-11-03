# SPDX-License-Identifier: MPL-2.0
"""Exposed recorded-input software conformance; no scientific qualification."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.battery_current_control.composition import implementation_payloads
from empirical_lawhood.adapters.methods.battery_current_control.contracts import PROTOCOL_SHA256, current_recipe
from empirical_lawhood.adapters.methods.battery_current_control.delivery import BatteryCurrentReceiptDelivery, from_authenticated_product, project_current_stages
from empirical_lawhood.adapters.methods.battery_current_control.words import current_word
from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import BatteryThermalConfig, BatteryThermalTrace, EVENTS
from empirical_lawhood.kernel.control import OperationalDeliveryState, ScientificCommitmentKind
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.controller_study import ImplementationRole
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactManifest, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck


def exposed_controller(*, hold=False, supported_hold=True, causal_valid=True):
    """Adapt existing truth-known fixtures, with no contact or qualification claim.

    All law/admission operands below are exposed software inputs. The existing
    reference fixture retains eight declared synthetic causal-support units;
    these are not observed physical battery units (the thermal source has zero). Their typed
    proof grammar exercises the installed compiler, not empirical battery law.
    """
    from empirical_lawhood.adapters.control.reference import build_current_reference_controller_study, _evidence
    from empirical_lawhood.adapters.control.finite_campaign import finite_control_study
    from empirical_lawhood.adapters.control.finite_response_corpus import finite_interval_corpus
    from empirical_lawhood.adapters.control.finite_gates import bounded_response_gate
    from empirical_lawhood.adapters.control.controller_authoring import DeliveryControllerAuthoringRequest
    from empirical_lawhood.adapters.methods.battery_current_control.composition import author_battery_controller, battery_control_services
    from empirical_lawhood.adapters.methods.law_evaluation import LawEvaluationRequest, LawEvaluationResult, LawEvaluationValue, LawEvaluationDisposition, LawEvaluationKind, LawEvaluationMode
    from empirical_lawhood.kernel.action_contracts import ActionDeliveryStage
    from empirical_lawhood.kernel.admission import AdmissionGateKind
    from empirical_lawhood.kernel.causal_contracts import ActionStageReceiverTransport, ReceiverInterval
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.laws import LawRepresentationKind
    from empirical_lawhood.kernel.models import ModelSetSpec, ModelMemberLawBinding, ModelIntersectionSemantics
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.references import ArtifactIdentity, NamedDecimal
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff, HorizonSpec
    from empirical_lawhood.planning.controller_study import FrozenFeedbackConsumer
    from empirical_lawhood.planning.evidence_geometry import ReceiptAdmissionActionFibre, ReceiptAdmissionSupportCell, ReceiptAdmissionPlannedCoordinate, ReceiptAdmissionReceiptProductionPlan
    from empirical_lawhood.planning.finite_action_support import support_map_for_plan
    from empirical_lawhood.planning.finite_response_geometry import FiniteReadoutKind, FiniteResponseCoordinate, FiniteTargetInterval
    from empirical_lawhood.adapters.methods.battery_current_control.words import coordinate
    from empirical_lawhood.runtime.controller_runtime import RuntimeObservation

    configuration = config(hold=hold)
    original = build_current_reference_controller_study()
    horizon = HorizonSpec("battery-service-900s", "battery-service-clock", D(900), "s")
    rename = lambda q: {"action": "battery-current", "receiver": "battery-native-current"}.get(q, q)
    relation = replace(original.system.relation, action_quantity_ids=("battery-current",), receiver_quantity_ids=tuple(sorted(rename(q) for q in original.system.relation.receiver_quantity_ids)), horizon=horizon)
    system = replace(original.system, label="EXPOSED recorded battery current software conformance", relation=relation,
        clocks=(replace(original.system.clocks[0], clock_id="battery-service-clock", coordinate_frame="battery-service-time"),),
        quantities=tuple(sorted((replace(q, quantity_id=rename(q.quantity_id),
            native_unit="A" if q.quantity_id == "action" else q.native_unit, clock_id="battery-service-clock", availability=replace(q.availability, clock_id="battery-service-clock")) for q in original.system.quantities), key=lambda q:q.quantity_id)),
        ports=tuple(sorted((replace(p, quantity_id=rename(p.quantity_id), clock_id="battery-service-clock") for p in original.system.ports), key=lambda p:p.port_id)))
    original_law = next(law for law in original.admission.atlas.laws if law.chart_id == "response-method-local-chart")
    law = replace(original_law, relation=relation, representation_kind=LawRepresentationKind.FINITE_ACTION_OPERATOR,
        interface_input_quantity_ids=tuple(sorted(rename(q) for q in original_law.interface_input_quantity_ids)), interface_output_quantity_ids=tuple(sorted(rename(q) for q in original_law.interface_output_quantity_ids)),
        obligations=replace(original_law.obligations, support=replace(original_law.obligations.support, action_bounds=(), denominator_cell_ids=(configuration.source.denominator_id,))))
    atlas = replace(original.admission.atlas, laws=(law,), transitions=(), gaps=())
    # This fixture locator confers no authority and is never sent to a source.
    qualification = ObjectIdentity("exposed-software-qualification-locator", "empirical-lawhood/kernel/law-qualification-result", "1.0.0", configuration.fingerprint())
    member = ModelMemberLawBinding("exposed-battery-member", "exposed-battery-denominator", relation.relation_id, ObjectIdentity.from_record(law.law_id, law), qualification, ("exposed-version",), ("coarse-view", "fine-view"), ("exposed-current",), ("physical-battery-qualification",))
    models = ModelSetSpec("exposed-battery-models", system.world.world_id, (member,), (relation.relation_id,), "Exposed recorded-input software conformance only", "No physical battery qualification or transport", (law.obligations.uncertainty.uncertainty_id,), law.obligations.validity, ModelIntersectionSemantics.QUALIFIED_INTERSECTION, EvidenceCeiling.ADMISSION, OutcomeAccess.OUTCOME_BLIND, (), VisibilityCeiling.PROSPECTIVE)
    bindings = tuple(b for b, _ in implementation_payloads())
    word = current_word(configuration, bindings[0].reference)
    fibre = ReceiptAdmissionActionFibre("exposed-battery-action", word, (word.occurrences[0].occurrence_id,), tuple(ActionDeliveryStage))
    cell = ReceiptAdmissionSupportCell("exposed-battery-cell", law.chart_id, law.obligations.support.denominator_cell_ids[0], (word.word_id,))
    planned = ReceiptAdmissionPlannedCoordinate("exposed-battery-coordinate", ObjectIdentity.from_record(member.binding_id, member), member.response_law, qualification, member.denominator_member_id, member.candidate_version_ids[0], member.qualification_view_ids, ObjectIdentity.from_record(fibre.action_binding_id, fibre), ObjectIdentity.from_record(cell.cell_id, cell))
    recipe_record = current_recipe(configuration)
    recipe = ObjectIdentity.from_record(recipe_record.recipe_id, recipe_record)
    gates = tuple(sorted((bounded_response_gate(stem="exposed-battery", kind=kind, response_receiver="battery-native-current", response_minimum=NamedDecimal("minimum", D(0), "1"), safety_receiver="sink", safety_maximum=NamedDecimal("maximum", D(10), "1"), protected_interval=ReceiverInterval(coordinate(D(0)), coordinate(D(900))), evaluator=law.evaluator) for kind in AdmissionGateKind), key=lambda g:g.predicate_id))
    cutoff = InformationCutoff("exposed-battery-cutoff", "battery-service-clock", CausalPhase.PRE_ACTION, D(0))
    plan = ReceiptAdmissionReceiptProductionPlan("exposed-battery-plan", atlas, ObjectIdentity("exposed-batch", "empirical-lawhood/methods/law-qualification-batch", "1.0.0", configuration.fingerprint()), models, member.denominator_member_id, (fibre,), (cell,), (planned,), gates, "exposed-initial", horizon, ("exposed-reachability",), recipe, recipe, recipe, recipe, recipe, recipe, ObjectIdentity.from_record(system.world.world_id, system.world), cutoff, OutcomeAccess.OUTCOME_BLIND, recipe, EvidenceCeiling.ADMISSION, VisibilityCeiling.PROSPECTIVE)
    plan = replace(plan, model_set=replace(models, extensions=(support_map_for_plan(plan).extension,)))
    link = replace(_evidence(atlas=atlas, evaluator=law.evaluator, suffix="exposed-current-conformance"), information_cutoff_id=cutoff.cutoff_id)
    calibration_artifact = ArtifactIdentity("exposed-calibration", "exposed-conformance", configuration.SCHEMA, qualification.object_fingerprint, "application/json", len(configuration.canonical_bytes()))
    artifacts = tuple(sorted((calibration_artifact, law.evaluator.payload), key=lambda a:a.artifact_id))
    link = replace(link, artifact_ids=tuple(a.artifact_id for a in artifacts))
    consumer = FrozenFeedbackConsumer("exposed-battery-consumer", recipe, (law.evaluator.payload,), qualification, recipe, recipe)
    coordinates = tuple(FiniteResponseCoordinate(f"readout.{q}", q, q, recipe, FiniteReadoutKind.WINDOW_MAXIMUM, "1", "exposed-response-frame", "battery-service-clock", D(0), D(900)) for q in ("battery-native-current", "sink"))
    requests, results = [], []
    for view in member.qualification_view_ids:
        request = LawEvaluationRequest(f"exposed-request.{view}", member.response_law, qualification, ObjectIdentity("exposed-axis", "empirical-lawhood/methods/law-candidate-axis-map", "1.0.0", configuration.fingerprint()), ObjectIdentity.from_record(law.evaluator.reference_id, law.evaluator), recipe, LawEvaluationKind.FINITE_ACTION_PATH, LawEvaluationMode.OFFLINE, "exposed-resource", None, system.system_id, system.world.world_id, relation.relation_id, law.chart_id, word.denominator_id, member.denominator_member_id, "exposed-version", view, relation.history_quantity_ids, relation.receiver_quantity_ids, ObjectIdentity.from_record(horizon.horizon_id, horizon), cell.cell_id, word, (), artifacts, ("exposed-interval",))
        values = tuple(sorted((LawEvaluationValue(f"{name}.{q}", q, D(1), "1", "exposed-response-frame", "battery-service-clock") for q in ("battery-native-current", "sink") for name in ("interval-centre", "lower", "upper")), key=lambda v:v.value_id))
        result = LawEvaluationResult(f"exposed-result.{view}", ObjectIdentity.from_record(request.request_id, request), recipe, member.denominator_member_id, "exposed-version", view, ObjectIdentity.from_record(word.word_id, word), LawEvaluationDisposition.SUPPORTED, values, (), (), (), (), ())
        requests.append(request)
        results.append(result)
    corpus = finite_interval_corpus(plan=plan, law=law, table_record=configuration, table_id=configuration.config_id, requests=tuple(requests), results=tuple(results), word=word, qualification=qualification, qualified=True, root="exposed-battery-software-only", causal_valid=causal_valid, effort_admissible=True, projected_cost=NamedDecimal("cost", D(1), "1"), response_receiver="battery-native-current", safety_receiver="sink", coordinates=coordinates, clock=recipe, target_intervals=tuple(FiniteTargetInterval(c, D(0), D(2)) for c in coordinates), consumer=consumer, calibration_artifact=calibration_artifact, source_artifacts=artifacts, evidence=(link,), prediction_unavailable_reason="EXPOSED_PREDICTION_UNAVAILABLE")
    causal = original.action_bindings[0].causal_prefix.causal_support
    support = replace(causal, action_word=word, relation=relation, receiver_id=word.receiver_id, receiver_clock_id="battery-service-clock", receiver_coordinate_frame="battery-service-time", stage_transports=tuple(ActionStageReceiverTransport(word.occurrences[0].occurrence_id, stage, word.occurrences[0].requested_to_accepted) for stage in ActionDeliveryStage), earliest_influence=coordinate(D(10)), latest_influence=coordinate(D(900)), physical_independent_unit_count=8, evidence_links=(link,))
    obligation = replace(original.action_bindings[0].causal_prefix.obligations[0], receiver_id=word.receiver_id, protected_domain=ReceiverInterval(coordinate(D(0)), coordinate(D(900))), evaluated_domain=ReceiverInterval(coordinate(D(0)), coordinate(D(900))), physical_independent_unit_count=8, evidence_links=(link,))
    prefix = replace(original.action_bindings[0].causal_prefix, causal_support=support, prefix_cutoff=coordinate(D(0)), obligations=(obligation,))
    action = replace(original.action_bindings[0], action_binding_id=fibre.action_binding_id, action_word=word, causal_prefix=prefix)
    observation = RuntimeObservation("exposed-battery-observation", configuration.unit_id, (NamedDecimal("observed-current", configuration.current_a, "A"),), coordinate(D(0)), artifacts, OutcomeAccess.OUTCOME_BLIND)
    # The unchanged campaign author initially labels all nonzero alternatives
    # ACT. Build HOLD from the exact zero word in a separate authoring request.
    if hold:
        return _exposed_hold_request(configuration, system, corpus, action, bindings, observation, recipe, link, supported_hold)
    study = finite_control_study(system=system, corpus=corpus, action_bindings=(action,), implementations=bindings, observation=observation, frozen_recipe=recipe, compiler_release_id="exposed-battery-sole-compiler", decision_budget_seconds=D(1))
    request = DeliveryControllerAuthoringRequest("exposed-battery-author", study.study_id, study.compiler_release_id, study.system, study.action_bindings, study.admission, study.reachability, study.synthesis, study.implementations, study.measured_hold_fibre, study.delivery_equivalence, study.allow_fallback_hold, study.instance_binding, None)
    study = author_battery_controller(request, configuration=configuration)
    port = delivery(recorded_source(configuration), word)
    return study, battery_control_services(study, port), observation, port


def _exposed_hold_request(configuration, system, corpus, action, bindings, observation, recipe, link, supported_hold):
    from empirical_lawhood.adapters.control.controller_authoring import DeliveryControllerAuthoringRequest
    from empirical_lawhood.adapters.methods.battery_current_control.composition import author_battery_controller, battery_control_services
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.references import NamedDecimal
    from empirical_lawhood.planning.controller_study import AdmissionMeasuredHoldFibre, ActHoldActionCandidate, ActHoldActionCandidateChart, ActHoldControllerSynthesisPlan, NativeCandidateKind, CandidatePriorityOrientation, ControllerInstanceBinding, DeliveryEquivalenceSpec, OnlineSupportMonitorSpec, ReidentificationTriggerSpec
    from empirical_lawhood.planning.evidence_geometry import ReceiptAdmissionAdmissionCandidateCell
    from empirical_lawhood.planning.finite_admission import FiniteCertificateAdmissionSpec, FiniteCertificateReachabilitySpec, derive_finite_certificate_admission_comparison, derive_finite_certificate_reachability_comparison
    plan = corpus.plan
    fibre, support = plan.action_fibres[0], plan.support_cells[0]
    cell = ReceiptAdmissionAdmissionCandidateCell("exposed-hold-admission-cell", ObjectIdentity.from_record(fibre.action_binding_id, fibre), ObjectIdentity.from_record(support.cell_id, support), (plan.coordinates[0].coordinate_id,))
    admission = FiniteCertificateAdmissionSpec("exposed-hold-admission", corpus, plan.nominal_denominator_member_id, plan.atlas.laws[0].relation.receiver_quantity_ids, (cell,), EvidenceCeiling.ADMISSION, VisibilityCeiling.PROSPECTIVE)
    admitted = derive_finite_certificate_admission_comparison(admission)
    reachability = FiniteCertificateReachabilitySpec("exposed-hold-reachability", admission, admitted, plan.initial_set_id, EvidenceCeiling.ADMISSION, VisibilityCeiling.PROSPECTIVE)
    reachable = derive_finite_certificate_reachability_comparison(reachability)
    utility = corpus.utility_receipts[0]
    chart = ActHoldActionCandidateChart("exposed-hold-chart", ObjectIdentity.from_record(plan.model_set.model_set_id, plan.model_set), plan.nominal_denominator_member_id, utility.utility_definition, utility.direction, utility.minimum_utility, CandidatePriorityOrientation.EARLIER_WINS, (ActHoldActionCandidate("exposed-hold-candidate", "exposed-hold-decision", ObjectIdentity.from_record(cell.candidate_cell_id, cell), 0, NativeCandidateKind.HOLD),))
    roles = {binding.role: binding.binding_id for binding in bindings}
    monitors = (OnlineSupportMonitorSpec("exposed-hold-exact-inputs", (support.cell_id,), "Cancel when committed source inputs change; never reselect.", "flh-committed-input-changed"),)
    triggers = (ReidentificationTriggerSpec("exposed-hold-invalidate", "Changed committed input cancels use without refitting.", True, "flh-committed-input-changed"),)
    synthesis = ActHoldControllerSynthesisPlan("exposed-hold-synthesis", ObjectIdentity.from_record(plan.atlas.atlas_id, plan.atlas), ObjectIdentity.from_record(corpus.corpus_id, corpus), ObjectIdentity.from_record(admitted.comparison_id, admitted), ObjectIdentity.from_record(reachable.comparison_id, reachable), chart.model_set, chart, *(roles[role] for role in (ImplementationRole.ADMISSION_DERIVER, ImplementationRole.REACHABILITY_DERIVER, ImplementationRole.SYNTHESIZER, ImplementationRole.OBSERVER, ImplementationRole.ONLINE_GATE_EVALUATOR, ImplementationRole.DELIVERY)), tuple(v.value_id for v in observation.values), monitors, triggers, system.authority_policy.policy_id, D(1), D(1), EvidenceCeiling.ADMISSION, VisibilityCeiling.PROSPECTIVE)
    first = corpus.reachability_receipts[0].request
    joint = first.response_set.joint_calibration
    instance = ControllerInstanceBinding("exposed-hold-instance", recipe, (plan.atlas.laws[0].evaluator.payload,), (ObjectIdentity.from_record(joint.calibration_id, joint),), first.response_set.public_handoff, ObjectIdentity.from_record(first.task.functional_id, first.task), first.response_set.frame_translation, ObjectIdentity.from_record(observation.observation_id, observation), plan.information_cutoff)
    equivalence = DeliveryEquivalenceSpec("exposed-hold-exact-delivery", True, True, NamedDecimal("per-stage-current-tolerance", D(0), "A"))
    hold = AdmissionMeasuredHoldFibre("exposed-hold-independent-fibre", "exposed-hold-decision", ObjectIdentity.from_record(cell.candidate_cell_id, cell), "exposed-zero-current-calibration", (link,), NamedDecimal("exposed-null-current", D(0), "A"), equivalence) if supported_hold else None
    request = DeliveryControllerAuthoringRequest("exposed-hold-author", "exposed-hold-programme", "exposed-battery-sole-compiler", system, (action,), admission, reachability, synthesis, bindings, hold, equivalence, False, instance, None)
    study = author_battery_controller(request, configuration=configuration)
    port = delivery(recorded_source(configuration), action.action_word)
    return study, battery_control_services(study, port), observation, port


def test_registered_act_compiles_and_recovery_reuses_exact_receipt():
    from empirical_lawhood.adapters.methods.battery_current_control.words import coordinate
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.controller_runtime import DeliveryControllerTickReceipt
    study, services, observation, port = exposed_controller()
    compiled = services.compile(study)
    tick = services.tick(compiled, observation, commitment_coordinate=coordinate(D(0)))
    assert tick.delivery_trace.commitment_kind is ScientificCommitmentKind.ACTION
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.DELIVERED
    assert port.delivery_calls == 1
    # Receipt recovery is decoding/revalidation, not a second delivery effect.
    recovered = decode_canonical_bytes(tick.canonical_bytes(), DeliveryControllerTickReceipt, maximum_bytes=4 * 1024**2)
    assert recovered == tick and port.delivery_calls == 1


def test_independently_supported_hold_and_unsupported_hold_nonattempt():
    from empirical_lawhood.adapters.methods.battery_current_control.words import coordinate
    study, services, observation, port = exposed_controller(hold=True)
    tick = services.tick(services.compile(study), observation, commitment_coordinate=coordinate(D(0)))
    assert tick.delivery_trace.commitment_kind is ScientificCommitmentKind.MEASURED_HOLD
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.DELIVERED
    assert port.delivery_calls == 1
    study, services, observation, port = exposed_controller(hold=True, supported_hold=False)
    tick = services.tick(services.compile(study), observation, commitment_coordinate=coordinate(D(0)))
    assert tick.delivery_trace.commitment_kind is ScientificCommitmentKind.NONATTEMPT
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.NOT_ATTEMPTED
    assert port.delivery_calls == 0


def test_missing_stage_wrong_word_stale_observation_and_nonattempt_zero_calls():
    from empirical_lawhood.adapters.methods.battery_current_control.words import coordinate
    study, services, observation, port = exposed_controller()
    compiled = services.compile(study)
    original = port.evidence
    source = replace(original.source, applied_current_a=None, applied_model_clock_s=None)
    port.evidence = evidence(source, original.word)
    tick = services.tick(compiled, observation, commitment_coordinate=coordinate(D(0)))
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.DELIVERY_RECOVERY
    assert tick.delivery_trace.commitment_kind is ScientificCommitmentKind.ACTION
    # A separately evidenced zero-current word cannot deliver a charging ACT.
    hold_configuration = config(hold=True)
    hold_word = current_word(hold_configuration, implementation_payloads()[0][0].reference)
    port.evidence = evidence(recorded_source(hold_configuration), hold_word)
    tick = services.tick(compiled, observation, commitment_coordinate=coordinate(D(0)))
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.DELIVERY_RECOVERY
    port.evidence = original
    before = port.delivery_calls
    stale = replace(observation, observation_id="stale-exposed-observation", coordinate=coordinate(D(10)))
    tick = services.tick(compiled, stale, commitment_coordinate=coordinate(D(10)))
    assert tick.delivery_trace.commitment_kind is ScientificCommitmentKind.NONATTEMPT
    assert tick.delivery_trace.operational_state is OperationalDeliveryState.NOT_ATTEMPTED
    assert port.delivery_calls == before


def config(*, hold=False):
    return BatteryThermalConfig("config.exposed-battery-current", "acquire", PROTOCOL_SHA256, "unit.battery-thermal-service.23c", D("296.15"), "native-hold900" if hold else "standard-cc900")


def recorded_source(configuration):
    """Explicit recorded numbers, not a solve or a qualified native acquisition."""
    times = tuple(D(t) for t in range(0, 901, 10))
    return BatteryThermalTrace(configuration, configuration.source.fingerprint(), "1" * 64, "COMPLETE", "final time", (), configuration.current_a, configuration.current_a, configuration.current_a, times, (configuration.current_a,) * len(times), (D(4),) * len(times), tuple(configuration.current_a * t / D(3600) for t in times), (D("296.15"),) * len(times), EVENTS, accepted_model_clock_s=D(0), applied_model_clock_s=D(0))


def exposed_custody(source):
    """Structural custody fixture, without a signer or native authority."""
    raw = source.canonical_bytes()
    logical = LogicalArtifactIdentity("exposed-battery-current-source", source.fingerprint(), source.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND, ArtifactGenericValidation("validator.canonical-json", "1.0.0", "2" * 64, source.SCHEMA, ArtifactProfile.CANONICAL_JSON))
    material = ArtifactMaterialization("material.exposed-battery-source", logical.logical_artifact_id, "storage.exposed-fixture", "source.json", source.fingerprint(), len(raw), "none")
    receipt = CanonicalTaskReceipt("receipt.exposed-battery-source", "run.exposed-battery-source", "task.exposed-battery-source", "attempt.exposed-battery-source", "1" * 40, (), (material,), (logical,), (ReceiptCheck("check.exposed-structural-custody", True, ()),), OperationalStatus.SUCCEEDED, ())
    return receipt, ArtifactManifest(logical, material)


def evidence(source, word):
    receipt, manifest = exposed_custody(source)
    return from_authenticated_product(evidence_id="exposed-battery-current-delivery", source_bytes=source.canonical_bytes(), producing_receipt=receipt, artifact=manifest, word=word, exposure="EXPOSED_RECORDED_INPUT_CONFORMANCE")


def delivery(source, word):
    binding = next(b for b, _ in implementation_payloads() if b.role is ImplementationRole.DELIVERY)
    return BatteryCurrentReceiptDelivery(binding, current_recipe(source.config), evidence(source, word))


def test_actual_current_stages_are_not_requested_or_capacity_values():
    configuration = config()
    word = current_word(configuration, implementation_payloads()[0][0].reference)
    source = replace(recorded_source(configuration), accepted_current_a=D("-.234"), applied_current_a=D("-.456"), current_a=(D("-.777"),) * 91, discharge_capacity_ah=(D(1000),) * 91)
    observed, _ = project_current_stages(source, word, observation_id="exposed-stages")
    assert [observed.requested.value, observed.accepted.value, observed.applied.value, observed.realized.value] == [D("-1.455"), D("-.234"), D("-.456"), D("-.777")]
    port = delivery(source, word)
    assert port.deliver(action_word=word, commitment_kind=ScientificCommitmentKind.ACTION).failure_state is OperationalDeliveryState.DELIVERY_RECOVERY


def test_full_timeline_missing_stage_and_zero_current_hold():
    configuration = config(hold=True)
    word = current_word(configuration, implementation_payloads()[0][0].reference)
    source = recorded_source(configuration)
    assert delivery(source, word).deliver(action_word=word, commitment_kind=ScientificCommitmentKind.MEASURED_HOLD).failure_state is None
    missing = replace(source, applied_current_a=None, applied_model_clock_s=None)
    assert evidence(missing, word).observed.applied is None
    assert delivery(missing, word).deliver(action_word=word, commitment_kind=ScientificCommitmentKind.MEASURED_HOLD).failure_state is OperationalDeliveryState.DELIVERY_RECOVERY
    # Only a later sample changes; first current and capacity stay favorable.
    changed = replace(source, current_a=source.current_a[:45] + (D(1),) + source.current_a[46:])
    assert "BATTERY_REALIZED_CURRENT_TRACE_MISMATCH" in evidence(changed, word).observed.reason_codes


def test_exact_logical_physical_receipt_join_and_stale_clock():
    source = recorded_source(config())
    word = current_word(source.config, implementation_payloads()[0][0].reference)
    receipt, manifest = exposed_custody(source)
    renamed = replace(manifest.logical, logical_artifact_id="renamed-source")
    changed = ArtifactManifest(renamed, replace(manifest.materialization, logical_artifact_id="renamed-source"))
    with pytest.raises(ValueError, match="producing receipt"):
        from_authenticated_product(evidence_id="exposed-wrong-custody", source_bytes=source.canonical_bytes(), producing_receipt=receipt, artifact=changed, word=word, exposure="EXPOSED_RECORDED_INPUT_CONFORMANCE")
    with pytest.raises(ValueError):
        from_authenticated_product(evidence_id="exposed-wrong-bytes", source_bytes=source.canonical_bytes() + b"\n", producing_receipt=receipt, artifact=manifest, word=word, exposure="EXPOSED_RECORDED_INPUT_CONFORMANCE")
    stale = replace(source, applied_model_clock_s=D(10))
    observed, _ = project_current_stages(stale, word, observation_id="exposed-stale")
    assert observed.applied.coordinate.coordinate == 10
    assert delivery(stale, word).deliver(action_word=word, commitment_kind=ScientificCommitmentKind.ACTION).failure_state is OperationalDeliveryState.DELIVERY_RECOVERY


def test_exposed_fixture_cannot_upgrade_native_exposure_or_substitute_recipe():
    from empirical_lawhood.adapters.methods.battery_current_control.composition import battery_control_services
    source = recorded_source(config())
    word = current_word(source.config, implementation_payloads()[0][0].reference)
    receipt, manifest = exposed_custody(source)
    with pytest.raises(ValueError, match="authenticated wave"):
        from_authenticated_product(evidence_id="exposed-forged-native", source_bytes=source.canonical_bytes(), producing_receipt=receipt, artifact=manifest, word=word, exposure="RECEIPT_BACKED_NATIVE_OBSERVATION")
    with pytest.raises(ValueError, match="actual configuration"):
        replace(evidence(source, word), exposure="RECEIPT_BACKED_NATIVE_OBSERVATION")
    study, _, _, port = exposed_controller()
    other = replace(config(), view="tighter")
    with pytest.raises(ValueError, match="recipe"):
        battery_control_services(study, BatteryCurrentReceiptDelivery(port.implementation_binding, current_recipe(other)))
    # The same preparation with a different nested clock is not the compiled
    # primary recipe; a new view never becomes independent physical evidence.
    other_word = current_word(other, implementation_payloads()[0][0].reference)
    with pytest.raises(ValueError, match="view|grammar"):
        project_current_stages(source, other_word, observation_id="exposed-wrong-view")
