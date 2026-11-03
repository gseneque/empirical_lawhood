# SPDX-License-Identifier: MPL-2.0
"""Retained fresh-native E2 assessment over ordinary authenticated DEV custody.

The generic reader owns packet, plan, receipt and byte authentication. This
consumer joins the exact original E2 operands and replays only the finite score
reduction. It never acquires, predicts, opens arrays or confers qualification.
"""
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_publications import authenticate_request
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census, has_response_measurements, validate_response_native_evidence
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.matrix_native_read_custody import _record, _array, _producers, _graph
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding

def _deferred(specification, reason):
    return {"scientific_completion": "NOT_ESTABLISHED", "state": "NATIVE_UTILITY_ASSESSMENT_DEFERRED",
        "scientific_status": "UNEVALUABLE", "qualification": "NOT_ESTABLISHED",
        "sampling_warrant": "NOT_ESTABLISHED", "reason_codes": (reason,),
        "denominators": {"native-utility": {"assigned_units": len(specification.root_ids),
            "usable_units": None, "successes": None, "adverse_units": None, "unevaluable_units": None}},
        "new_native_contact_count": 0}


def _request(specification, instance, payloads):
    if type(instance) is not ExperimentInstanceBinding or instance.specification != specification.identity:
        raise PermissionError("native E2 read substitutes its exact original public instance")
    matches = tuple(value for value in instance.sources if (value.object_schema, value.object_version) ==
        (r.NativeUtilityRequest.SCHEMA, r.NativeUtilityRequest.VERSION))
    if len(matches) != 1:
        raise PermissionError("native E2 read requires one exact original acquisition request")
    reference, = matches
    name = "experiment-source-" + sha256(reference.object_id.encode()).hexdigest() + ".json"
    raw = payloads[name]
    request = decode_canonical_bytes(raw, r.NativeUtilityRequest, maximum_bytes=len(raw))
    if request.canonical_bytes() != raw or request.identity != reference:
        raise PermissionError("native E2 read changes its retained original canonical request")
    r.validate_request(specification, request)
    if instance.allocation != r.utility_allocation(specification, request).identity:
        raise PermissionError("native E2 read substitutes the complete original unit allocation")
    return request


def _root(specification, request, seal, root_id, configs, products, tasks, run_id, *, source_index, artifact_writer=None, plan=None, template_arrays=None):
    source = r.source_for(request, root_id, index=source_index)
    protocol, = (value for value in request.protocols if value.public_source.root.root_id == root_id)
    panels = r.panels_for(request, source)
    get = lambda phase, kind, label="product": _record(products, tasks, run_id, owner.task_id(root_id, phase), kind, label)
    history = get("prefix", r.NativeUtilityPrefixHistory)
    checkpoint = get("prefix", r.ScheduledCheckpoint, "checkpoint")
    numerical = get("numerical", r.NativeUtilityNumericalAssessment)
    witness = get("measure", r.NativeUtilityPrefixWitness)
    frames = get("check", r.NativeUtilityFrameAssessment)
    causal = get("project", r.NativeUtilityCausalPrefix)
    physical = get("physical-forecast", r.NativeUtilityPhysicalForecast)
    responses = get("responses", r.NativeUtilityResponse)
    score = get("response-score", r.NativeUtilityScore, "score")
    outcome = get("response-score", r.NativeUtilityOutcome)
    source_pin, protocol_pin = r.scheduled_identity(source), r.identity(protocol)
    history.validate_source(source)
    if (checkpoint != history.checkpoint or history.acquisition != seal.identity or history.configuration != r.identity(configs[owner.task_id(root_id, "prefix")])
            or history.native.definition.parent_contact.run_id != run_id
            or (numerical.source, numerical.history, numerical.numerical_design) !=
                (source_pin, history.identity, r.scheduled_identity(source.numerical_design))
            or (witness.source, witness.history, witness.numerical, witness.policy) !=
                (source_pin, history.identity, numerical.identity, r.scheduled_identity(source.policy))
            or (frames.source, frames.witness, frames.numerical_design) !=
                (source_pin, witness.identity, r.scheduled_identity(source.policy.factor_numerical_design))
            or (causal.source, causal.history, causal.numerical, causal.witness, causal.frame_assessment,
                causal.policy, causal.root, causal.cutoff_tick) != (source_pin, history.identity, numerical.identity,
                    witness.identity, frames.identity, r.scheduled_identity(source.policy), source.root.root, source.policy.cutoff_tick)
            or (physical.source, physical.causal_prefix, physical.protocol, physical.mechanical_model, physical.frame_sha256) !=
                (source_pin, causal.identity, protocol_pin, ObjectIdentity.from_record(protocol.mechanical_model.model_id,
                    protocol.mechanical_model), causal.frame_sha256)
            or (responses.source, responses.causal_prefix, responses.physical_forecast, responses.acquisition_seal, responses.protocol) !=
                (source_pin, causal.identity, physical.identity, seal.identity, protocol_pin)
            or responses.branch_ids != tuple(value[0] for value in branch_census(protocol, panels))
            or (score.source, score.causal_prefix, score.acquisition_seal, score.physical_forecast, score.responses) !=
                (source_pin, causal.identity, seal.identity, physical.identity, responses.identity)):
        raise PermissionError("native E2 read substitutes actual source/prefix/control/forecast/response/score ancestry")
    for phase, arrays in (("prefix", history.arrays), ("measure", witness.arrays), ("project", causal.arrays),
            ("physical-forecast", physical.arrays), ("responses", responses.arrays)):
        _array(products, tasks, owner.task_id(root_id, phase), arrays)
    _producers(history.arrays, (source_pin, r.coordinate_identity(source.coordinate)))
    _producers(witness.arrays, (source_pin, history.identity, numerical.identity))
    _producers(causal.arrays, (source_pin, history.identity, witness.identity, frames.identity))
    _producers(physical.arrays, (source_pin, causal.identity, protocol_pin))
    _producers(responses.arrays, (source_pin, seal.request, physical.identity, seal.identity))
    if causal.disposition == "AVAILABLE" and not (numerical.numerical_pass and frames.numerical_pass):
        raise PermissionError("native E2 read promotes a failed prefix/frame numerical control")
    if not responses.native and (score.numerical_pass or has_response_measurements(score)):
        raise PermissionError("native E2 read manufactures usable native truth for unentered futures")
    if responses.native:
        if causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE":
            raise PermissionError("native E2 read manufactures entered futures from unavailable causal/physical operands")
        validate_response_native_evidence(responses, source, specification.identity, history, causal, physical, seal,
            configuration=r.identity(configs[owner.task_id(root_id, "responses")]),
            parent_task=owner.task_id(root_id, "responses"), operation=r.NAMESPACE + ".paired-responses.v1",
            shared_sources=r.native_source_pins(source), panels=panels, protocol=protocol)
    else:
        responses.validate_nonentry(causal, physical, protocol, panels)
    from empirical_lawhood.api.matrix_native_acquisition_replay import replay_root
    if artifact_writer is None or plan is None:
        raise PermissionError("native E2 root replay requires its actual read-only artifact plane and retained plan")
    replayed = replay_root(artifact_writer=artifact_writer, specification=specification, request=request, seal=seal,
        source=source, protocol=protocol, panels=panels, configurations=configs, products=products, tasks=tasks, plan=plan, template_arrays=template_arrays,
        records=dict(history=history, checkpoint=checkpoint, numerical=numerical, witness=witness, frames=frames,
            causal=causal, physical=physical, responses=responses, score=score, outcome=outcome))
    return replayed


def read_development_result(*, directory, artifact_writer, specification, instance, payloads,
        report, products, draft, plan, allow_partial=False):
    """Return an E2 projection; the caller retains the full ordinary read report."""
    if type(specification) is not r.NativeUtilitySpecification or type(allow_partial) is not bool:
        raise TypeError("native E2 read requires its exact installed specification and explicit partial selection")
    specification.__post_init__()
    # Compact custody must never be upgraded by opening scientific products.
    if allow_partial:
        return _deferred(specification, "PARTIAL_CUSTODY_SCIENTIFIC_ASSESSMENT_DEFERRED")
    if report.get("typed_product_validation") == "DEFERRED":
        return _deferred(specification, "COMPACT_CUSTODY_SCIENTIFIC_ASSESSMENT_DEFERRED")
    if report.get("status") in ("BLOCKED", "FAILED"):
        if report.get("operational_terminal") != "AUTHENTICATED":
            return _deferred(specification, "CLOSED_OPERATIONAL_TERMINAL_NOT_ESTABLISHED")
        from empirical_lawhood.api.matrix_native_utility_custody_read import read_closed_partial_result
        return read_closed_partial_result(directory=directory, artifact_writer=artifact_writer,
            specification=specification, instance=instance, payloads=payloads, report=report,
            products=products, draft=draft, plan=plan)
    if report.get("status") != "SUCCEEDED":
        return _deferred(specification, "COMPLETE_SUCCESSFUL_ORDINARY_CUSTODY_NOT_ESTABLISHED")
    request = _request(specification, instance, payloads)
    configs, tasks = _graph(specification, request, draft, plan)
    run_id = plan.source_plan.object_id
    if report.get("run_id") != run_id or set(products["receipts"]) != set(tasks):
        raise PermissionError("native E2 read lacks its unchanged complete successful original task census")
    authenticate_request(artifact_writer, request)
    source_index = ScheduledSourceIndex.from_shared(reservation=request.source_manifest.reservation,
        specification=request.source_manifest.native_specification, provenances=request.source_manifest.provenances)
    source_index.require_roster(request.sources, expected_root_ids=specification.root_ids)
    seal = _record(products, tasks, run_id, owner.entry_task_id(specification), r.NativeUtilityAcquisitionSeal)
    if seal != r.acquisition_seal(specification, request):
        raise PermissionError("native E2 read changes the actual pre-contact acquisition freeze/source roster")
    template_arrays = {}
    outcomes = tuple(_root(specification, request, seal, root_id, configs, products, tasks, run_id,
        source_index=source_index, artifact_writer=artifact_writer, plan=plan, template_arrays=template_arrays)
        for root_id in specification.root_ids)
    summary = _record(products, tasks, run_id, owner.terminal_task_id(specification), r.NativeUtilitySummary)
    if summary != science.summarize(specification, seal, outcomes):
        raise PermissionError("native E2 read changes the exact terminal summary or its consumed root outcomes")
    return {"scientific_completion": "COMPLETE_NATIVE_UTILITY_ASSESSMENT", "state": "NATIVE_UTILITY_RESULT_RETAINED",
        "scientific_status": summary.scientific_status, "qualification": summary.qualification,
        "sampling_warrant": summary.sampling_warrant, "numerical_scope": summary.numerical_scope,
        "criterion": specification.criterion.to_document(), "conditional_criterion_met": summary.conditional_criterion_met,
        "conditional_tail": {"numerator": summary.tail_numerator, "denominator": summary.tail_denominator},
        "amended_primary_tests": science.amended_primary_report(summary.amended),
        "denominators": {"native-utility": {"assigned_units": summary.assigned_units,
            "usable_units": summary.usable_units, "successes": summary.successes,
            "adverse_units": sum(value.usable and not value.success for value in outcomes),
            "adverse_scope": "USABLE_WITHOUT_FROZEN_IMPROVEMENT",
            "unevaluable_units": sum(not value.usable for value in outcomes)}},
        "source_request": seal.request.to_document(), "acquisition": seal.identity.to_document(),
        "terminal": summary.identity.to_document(), "outcomes": tuple({"root_id": value.root_id,
            "unit_id": value.unit_id, "outcome": value.identity.to_document(), "score": value.score.to_document(),
            "amended_endpoints": None if value.amended is None else {
                "paired_factor_adequacy_through32": value.amended.adequacy,
                "three_challenger_advantage_through128": value.amended.structural_advantage,
                "paired_zero_response_adequacy_through32": value.amended.zero_adequacy,
                "joint_adequacy_advantage": value.amended.joint_adequacy_advantage,
                "factor_adequate_zero_inadequate": value.amended.factor_adequate_zero_inadequate}}
            for value in sorted(outcomes, key=lambda value: value.unit_id)),
        "new_native_contact_count": 0}
