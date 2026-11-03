# SPDX-License-Identifier: MPL-2.0
"""Public TRAIN scientific read through actual custody and received-array replay."""
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_request
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census, has_response_measurements, validate_response_native_evidence
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.matrix_native_read_custody import _record, _array, _producers, _graph
from empirical_lawhood.kernel.provenance import ObjectIdentity

def _authenticate_root_records(specification, request, seal, root_id, configs, products, tasks, run_id, *, source_index, get):
    """Authenticate original typed producer ancestry without array mathematics."""
    source = r.source_for(request, root_id, index=source_index)
    protocol, = (value for value in request.protocols if value.public_source.root.root_id == root_id)
    panels = r.panels_for(request, source)
    history = get("prefix", r.NativeTrainingPrefixHistory)
    checkpoint = get("prefix", r.ScheduledCheckpoint, "checkpoint")
    numerical = get("numerical", r.NativeTrainingNumericalAssessment)
    witness = get("measure", r.NativeTrainingPrefixWitness)
    frames = get("check", r.NativeTrainingFrameAssessment)
    causal = get("project", r.NativeTrainingCausalPrefix)
    physical = get("physical-forecast", r.NativeTrainingPhysicalForecast)
    responses = get("responses", r.NativeTrainingResponse)
    score = get("response-score", r.NativeTrainingScore, "score")
    outcome = get("response-score", r.NativeTrainingOutcome)
    feature = get("feature", r.NativeTrainingFeature)
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
        raise PermissionError("native TRAIN read substitutes actual source/prefix/control/forecast/response/score ancestry")
    for phase, arrays in (("prefix", history.arrays), ("measure", witness.arrays), ("project", causal.arrays),
            ("physical-forecast", physical.arrays), ("responses", responses.arrays)):
        _array(products, tasks, owner.task_id(root_id, phase), arrays)
    _producers(history.arrays, (source_pin, r.coordinate_identity(source.coordinate)))
    _producers(witness.arrays, (source_pin, history.identity, numerical.identity))
    _producers(causal.arrays, (source_pin, history.identity, witness.identity, frames.identity))
    _producers(physical.arrays, (source_pin, causal.identity, protocol_pin))
    _producers(responses.arrays, (source_pin, seal.request, physical.identity, seal.identity))
    if causal.disposition == "AVAILABLE" and not (numerical.numerical_pass and frames.numerical_pass):
        raise PermissionError("native TRAIN read promotes a failed prefix/frame numerical control")
    if not responses.native and (score.numerical_pass or has_response_measurements(score)):
        raise PermissionError("native TRAIN read manufactures usable native truth for unentered futures")
    if responses.native:
        if causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE":
            raise PermissionError("native TRAIN read manufactures entered futures from unavailable causal/physical operands")
        validate_response_native_evidence(responses, source, specification.identity, history, causal, physical, seal,
            configuration=r.identity(configs[owner.task_id(root_id, "responses")]),
            parent_task=owner.task_id(root_id, "responses"), operation=r.NAMESPACE + ".paired-responses.v1",
            shared_sources=r.native_source_pins(source), panels=panels, protocol=protocol)
    else:
        responses.validate_nonentry(causal, physical, protocol, panels)
    return source, protocol, panels, dict(history=history, checkpoint=checkpoint, numerical=numerical, witness=witness, frames=frames, causal=causal, physical=physical, responses=responses, score=score, outcome=outcome, feature=feature)


def _root(specification, request, seal, root_id, configs, products, tasks, run_id, *, source_index, artifact_writer=None, plan=None,
        template_arrays=None, mechanism_rows=None):
    get = lambda phase, kind, label="product": _record(products, tasks, run_id, owner.task_id(root_id, phase), kind, label)
    source, protocol, panels, records = _authenticate_root_records(specification, request, seal, root_id,
        configs, products, tasks, run_id, source_index=source_index, get=get)
    history = records["history"]
    checkpoint = records["checkpoint"]
    numerical = records["numerical"]
    witness = records["witness"]
    frames = records["frames"]
    causal = records["causal"]
    physical = records["physical"]
    responses = records["responses"]
    score = records["score"]
    outcome = records["outcome"]
    feature = records["feature"]
    from empirical_lawhood.api.matrix_native_acquisition_replay import replay_root
    if artifact_writer is None or plan is None:
        raise PermissionError("native TRAIN replay requires the actual read-only artifact plane and plan")
    replay_root(artifact_writer=artifact_writer, specification=specification, request=request, seal=seal,
        source=source, protocol=protocol, panels=panels, configurations=configs, products=products, tasks=tasks, plan=plan,
        template_arrays=template_arrays, mechanism_rows=mechanism_rows,
        records=dict(history=history, checkpoint=checkpoint, numerical=numerical, witness=witness, frames=frames,
            causal=causal, physical=physical, responses=responses, score=score, outcome=outcome, feature=feature))
    return feature, outcome


def _validate_complete_root_results(specification, request, seal, pairs, *, get_summary):
    features = tuple(sorted((row[0] for row in pairs), key=lambda value: value.unit_id))
    outcomes = tuple(sorted((row[1] for row in pairs), key=lambda value: value.unit_id))
    if tuple(value.unit_id for value in features) != tuple(value.unit_id for value in outcomes):
        raise PermissionError("native TRAIN read changes the complete feature/outcome whole-root denominator")
    summary = get_summary()
    expected = r.NativeTrainingSummary("summary." + specification.specification_id, specification.identity, seal.identity,
        tuple(value.unit_id for value in features), tuple((value.unit_id, value.disposition) for value in features),
        tuple((value.unit_id, value.numerical_disposition) for value in outcomes))
    if summary != expected:
        raise PermissionError("native TRAIN read changes the actual complete terminal feature/outcome reduction")
    if tuple(value.unit_id for value in features) != r.training_allocation(specification, request).unit_ids("train"):
        raise PermissionError("native TRAIN read drops or substitutes an assigned original whole group")
    return features, outcomes, summary


def read_development_result(*, directory, artifact_writer, specification, instance, payloads,
        report, products, draft, plan, allow_partial=False):
    """Replay one actual complete public read; compact/partial custody stays deferred."""
    if type(specification) is not r.NativeTrainingAcquisitionSpecification or type(allow_partial) is not bool:
        raise TypeError("native TRAIN read requires its exact specification and explicit partial selection")
    if allow_partial or report.get("typed_product_validation") == "DEFERRED" or report.get("status") != "SUCCEEDED":
        return {"scientific_completion": "NOT_ESTABLISHED", "state": "NATIVE_TRAIN_ARRAY_REPLAY_DEFERRED",
            "qualification": "NOT_ESTABLISHED", "assigned_units": len(specification.root_ids), "new_native_contact_count": 0}
    from empirical_lawhood.api.native_training_banks import _read_instance
    actual_specification, request, actual_instance = _read_instance(payloads)
    if (actual_specification != specification or actual_instance != instance
            or instance.allocation != r.training_allocation(specification, request).identity):
        raise PermissionError("native TRAIN read changes the exact original specification/request/allocation")
    configs, tasks = _graph(specification, request, draft, plan)
    run_id = plan.source_plan.object_id
    if report.get("run_id") != run_id or set(products["receipts"]) != set(tasks):
        raise PermissionError("native TRAIN read changes the complete actual task/receipt census")
    authenticate_request(artifact_writer, request)
    source_index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    source_index.require_roster(request.sources, expected_root_ids=specification.root_ids)
    seal = _record(products, tasks, run_id, owner.entry_task_id(specification), r.NativeTrainingAcquisitionSeal)
    if seal != r.acquisition_seal(specification, request):
        raise PermissionError("native TRAIN read changes its original pre-contact acquisition freeze")
    template_arrays, mechanism_rows = {}, []
    pairs = tuple(_root(specification, request, seal, root_id, configs, products, tasks, run_id,
        source_index=source_index, artifact_writer=artifact_writer, plan=plan, template_arrays=template_arrays,
        mechanism_rows=mechanism_rows)
        for root_id in specification.root_ids)
    features, outcomes, summary = _validate_complete_root_results(specification, request, seal, pairs,
        get_summary=lambda: _record(products, tasks, run_id, owner.terminal_task_id(specification), r.NativeTrainingSummary))
    from empirical_lawhood.kernel.serialization import canonical_value
    return {"scientific_completion": "COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY", "state": "NATIVE_TRAIN_MEASUREMENTS_RETAINED",
        **({'same_bank_mechanism': canonical_value(tuple(mechanism_rows))} if request.candidate_specification.is_curve_primary else {}),
        "qualification": "NOT_ESTABLISHED", "sampling_warrant": "NOT_ESTABLISHED", "assigned_units": len(features),
        "acquisition": seal.identity.to_document(), "terminal": summary.identity.to_document(),
        "feature_dispositions": summary.feature_dispositions, "numerical_dispositions": summary.numerical_dispositions,
        "new_native_contact_count": 0}
