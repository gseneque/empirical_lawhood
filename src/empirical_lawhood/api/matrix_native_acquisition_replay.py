# SPDX-License-Identifier: MPL-2.0
"""Fresh read-only native custody and received-array replay for TRAIN and E2."""
from empirical_lawhood.domains.matrix.matrix_scheduled_history.replay_validation import validate_derived_arrays

from empirical_lawhood.api.matrix_native_read_custody import _array, _expected_contact
from empirical_lawhood.api.recursive_qualified_parents import _output_payload
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.native_subwork import NativeSubworkState


def inspect_native(*, store, definition, event=None, require_nonentry=False):
    """Read actual custody; absence of a receipt never proves completed use.

    General forensic callers may inspect uncertain states without promoting
    them. Scientific callers must supply the exact completed event, or demand
    genuine nonentry after the typed response relation has been validated.
    """
    if type(require_nonentry) is not bool:
        raise TypeError("native inspection nonentry selection must be an explicit boolean")
    observed = store.inspect(definition)
    if require_nonentry:
        if event is not None or observed.state is not NativeSubworkState.NOT_ENTERED:
            raise PermissionError("native acquisition nonentry contradicts actual native-store progress")
    elif event is not None and (observed.state is not NativeSubworkState.COMPLETED
            or observed.definition != event.definition or observed.completion != event.completion
            or observed.receipt != event.receipt):
        raise PermissionError("native acquisition replay changes actual completed definition/completion/receipt custody")
    return observed






def _template_values(artifact_writer, protocol, products, cache):
    """Decode exact shared template values once in this full read's local scope."""
    from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
    descriptor = protocol.templates
    artifact = descriptor.array_artifact
    matches = tuple(value for value in products["external_inputs"] if value.logical.logical_artifact_id == artifact.artifact_id)
    if len(matches) != 1:
        raise PermissionError("native replay omits the exact retained original template operand")
    external, = matches
    logical, material = external.logical, external.materialization
    if ((logical.payload_schema, logical.media_type, logical.content_sha256, material.physical_sha256, material.size_bytes) !=
            (artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.sha256, artifact.size_bytes)):
        raise PermissionError("native replay changes original template descriptor/retained input bytes")
    manifest = artifact_writer.read_manifest(material.relative_path)
    if (manifest.logical, manifest.materialization) != (logical, material):
        raise PermissionError("native replay substitutes its exact retained template publication")
    artifact_writer.verify_manifest(manifest)
    key = (artifact.sha256, tuple(descriptor.members))
    if key not in cache:
        raw = read_exposed_recursive_payload(artifact_writer, manifest, maximum_bytes=artifact.size_bytes)
        values = decode_matrix_arrays(raw, descriptor)
        for value in values.values():
            value.flags.writeable = False
        cache[key] = values
    return cache[key]


def authenticate_native_custody(*, artifact_writer, specification, request, seal, source, protocol, panels,
        configurations, products, tasks, plan, records):
    """Fresh original parent/subwork inspections; no array decoding or numerical replay."""
    from empirical_lawhood.domains.matrix.matrix_factor_response import native_training_records as train
    from empirical_lawhood.domains.matrix.matrix_factor_response import native_utility_records as utility
    from empirical_lawhood.domains.matrix.matrix_factor_response.native_acquisition_contracts import native_work_definition
    if type(specification) is train.NativeTrainingAcquisitionSpecification:
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_training_acquisition as owner
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_training_bindings as binding
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_training_science as science
        r, is_training = train, True
        if type(request) is not train.NativeTrainingAcquisitionRequest or type(seal) is not train.NativeTrainingAcquisitionSeal:
            raise TypeError("native TRAIN replay changes its exact actual request/seal family")
    elif type(specification) is utility.NativeUtilitySpecification:
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_utility_acquisition as owner
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_utility_bindings as binding
        from empirical_lawhood.domains.matrix.matrix_factor_response import native_utility_science as science
        r, is_training = utility, False
        if type(request) is not utility.NativeUtilityRequest or type(seal) is not utility.NativeUtilityAcquisitionSeal:
            raise TypeError("native E2 replay changes its exact actual request/seal family")
    else:
        raise TypeError("native acquisition replay requires its exact TRAIN or E2 specification")
    history, causal, physical, responses = (records[key] for key in ("history", "causal", "physical", "responses"))
    if is_training:
        science.admit_response(source, protocol, panels, seal, causal, physical, responses)
    elif not responses.native:
        responses.validate_nonentry(causal, physical, protocol, panels)
    from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_records import validate_response_native_evidence
    history.validate_source(source)
    if responses.native:
        if causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE":
            raise PermissionError("native acquisition replay enters an unavailable future")
        validate_response_native_evidence(responses, source, specification.identity, history, causal, physical, seal,
            configuration=r.identity(configurations[owner.task_id(source.root_id, "responses")]),
            parent_task=owner.task_id(source.root_id, "responses"), operation=r.NAMESPACE + ".paired-responses.v1",
            shared_sources=r.native_source_pins(source), panels=panels, protocol=protocol)
    contacts = ExternalNativeEffectContactStore(plane=artifact_writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    store = ExternalNativeSubworkStore(plane=artifact_writer, parent_contacts=contacts)
    for phase, event in (("prefix", history.native), ("responses", responses.native[0] if responses.native else None)):
        task_id = owner.task_id(source.root_id, phase)
        receipt = products["receipts"][task_id]
        parent = contacts.read(receipt.run_id, task_id)
        expected_parent = _expected_contact(task=tasks[task_id], plan=plan, run_id=receipt.run_id,
            attempt_id=receipt.attempt_id, products=products)
        if parent != expected_parent:
            raise PermissionError("native acquisition replay changes actual parent contact/operand/receipt census")
        wire = configurations[task_id]
        config = binding._BoundConfiguration(wire, protocol) if phase == "responses" else wire
        definition = native_work_definition(config, source, {**records, "acquisition": seal}, parent,
            parent.input_materialization_ids)
        inspect_native(store=store, definition=definition, event=event, require_nonentry=event is None)
    return r, is_training, science, owner


def replay_root(*, artifact_writer, specification, request, seal, source, protocol, panels,
        configurations, products, tasks, plan, records, template_arrays=None, mechanism_rows=None):
    """Authenticate actual stores before once-per-operand bounded decompression.

    The caller owns the complete graph and typed receipt joins. This opens only
    that root's authenticated operands, has no persistent cache, invokes no
    provider/native executor, and emits no scientific product or receipt.
    """
    r, is_training, science, owner = authenticate_native_custody(artifact_writer=artifact_writer,
        specification=specification, request=request, seal=seal, source=source, protocol=protocol, panels=panels,
        configurations=configurations, products=products, tasks=tasks, plan=plan, records=records)
    history, causal, physical, responses = (records[key] for key in ("history", "causal", "physical", "responses"))
    decoded = {}
    def values(phase, descriptor):
        task_id = owner.task_id(source.root_id, phase)
        _array(products, tasks, task_id, descriptor)
        key = (descriptor.array_artifact.sha256, descriptor.fingerprint())
        if key not in decoded:
            receipt = products["receipts"][task_id]
            output, = (row for row in tasks[task_id].outputs if row.output_id == task_id + ".arrays")
            logical, = (row for row in receipt.output_logical_artifacts if row.logical_artifact_id == output.logical_artifact_id)
            raw = _output_payload(artifact_writer, receipt, logical, descriptor.array_artifact.size_bytes)
            decoded[key] = decode_matrix_arrays(raw, descriptor)
        return decoded[key]
    prefix = values("prefix", history.arrays)
    frozen = values("physical-forecast", physical.arrays)
    received = values("responses", responses.arrays)
    diagnostic = values("measure", records["witness"].arrays)
    causal_arrays = values("project", causal.arrays)
    expected_numerical = science.numerical(source, history, prefix)
    if records["numerical"] != expected_numerical:
        raise PermissionError("native derived replay changes original numerical prefix controls")
    local_templates = {} if template_arrays is None else template_arrays
    templates = _template_values(artifact_writer, protocol, products, local_templates)
    validate_derived_arrays(source=source, protocol=protocol, records=records, prefix=prefix, diagnostic=diagnostic,
        causal_arrays=causal_arrays, frozen=frozen, templates=templates)
    if is_training:
        witness, frames, feature = (records[key] for key in ("witness", "frames", "feature"))
        actual_feature = science.feature(specification, request.identity, protocol.public_source, causal, witness, frames,
            causal_arrays, diagnostic, protocol=protocol, physical_record=physical, frozen_arrays=frozen,
            curve_primary=request.candidate_specification.is_curve_primary)
        if feature != actual_feature:
            raise PermissionError("native TRAIN read changes feature values derived from authenticated causal/diagnostic arrays")
        actual_score, actual_outcome = science.score(specification, source, protocol, panels, seal, history,
            causal, physical, responses, prefix, frozen, received, actual_feature)
    else:
        actual_score, actual_outcome = science.score(specification, source, protocol, panels, seal, history,
            causal, physical, responses, prefix, frozen, received)
    if (records["score"], records["outcome"]) != (actual_score, actual_outcome):
        raise PermissionError("native acquisition read changes score/outcome replayed from actual authenticated received arrays")
    if mechanism_rows is not None and is_training and request.candidate_specification.is_curve_primary:
        from empirical_lawhood.api.matrix_mechanism_read import bound_mechanism
        mechanism_rows.append(bound_mechanism(protocol=protocol, source=source.identity,
            causal_record=causal, physical_record=physical, response_record=responses,
            causal_arrays=causal_arrays, frozen_arrays=frozen, response_arrays=received, panels=panels,
            numerical_status=actual_outcome.numerical_disposition, feature=actual_feature, score=actual_score,
            subject_id=source.root_id, group_id=actual_feature.unit_id))
    return actual_outcome
