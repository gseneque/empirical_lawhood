# SPDX-License-Identifier: MPL-2.0
"""Separate native observation and independent PURE interpretation/reduction."""

from decimal import Decimal

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_contracts as oc, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity_stream import FullStateStreamOperand, assess_streams
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import _original_evidence
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion
from . import contracts as ct


def _load(context, operation, manifest):
    from . import operation_bindings as ob, recursive_translation as rt
    selected = tuple(port for port in context.input_ports if port.payload_schema == ob.ObservationOperationConfig.SCHEMA)
    if len(selected) != 1:
        raise ValueError("observation worker requires its exact immutable operation config")
    port = selected[0]
    config = decode_canonical_bytes(port.read(), ob.ObservationOperationConfig, maximum_bytes=None)
    node = ob.node_id(config.operation, config.index)
    if (config.operation != operation or context.task_id != node or context.permissions != manifest.permissions
            or context.resource_budget != ob.BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or port.kind is not WorkerInputKind.EXTERNAL or port.artifact_id != context.config.artifact_id
            or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256):
        raise ValueError("observation worker changes exact task/config/access/resources")
    expected = dict((*ob.common_inputs(config), *ob.operation_inputs(operation)))
    sources, values = rt.input_sources(config), rt.external_values(config)
    decoded, ports = {}, {}
    for name, record in expected.items():
        kind, origin = sources[name]
        artifact_id = "artifact." + context.run_id + "." + origin if kind == "DEPENDENCY" else origin
        found = tuple(port for port in context.input_ports if port.artifact_id == artifact_id)
        if len(found) != 1:
            raise ValueError("observation worker omits/substitutes original input ordinal")
        port = found[0]
        if (port.kind is not (WorkerInputKind.DEPENDENCY if kind == "DEPENDENCY" else WorkerInputKind.EXTERNAL)
                or port.payload_schema != record.SCHEMA or port.media_type != ob.media_for(name)
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("observation worker changes original typed input/access")
        ports[name] = port
        if kind == "DEPENDENCY" and not any(receipt.task_id == origin.rsplit(".", 1)[0]
                and port.materialization_id in receipt.output_materialization_ids for receipt in context.dependency_receipts):
            raise ValueError("observation worker loses original producing dependency receipt")
        if name.endswith("segments"):
            continue
        raw = port.read()
        if len(raw) != port.size_bytes:
            raise ValueError("observation worker changes complete input byte count")
        decoded[name] = raw if record is ob.RawSource else decode_canonical_bytes(raw, record, maximum_bytes=None)
        if kind == "EXTERNAL" and record is not ob.RawSource and name != "history" and decoded[name] != values[origin]:
            raise ValueError("observation worker substitutes its source/config/declaration/storage operand")
    if len(context.input_ports) != len(expected) + 1:
        raise ValueError("observation worker has undeclared or duplicated inputs")
    producers = {origin.rsplit(".", 1)[0] for kind, origin in sources.values() if kind == "DEPENDENCY"}
    if {receipt.task_id for receipt in context.dependency_receipts} != producers or len(context.dependency_receipts) != len(producers):
        raise ValueError("observation worker changes exact actual producing receipt census")
    if c.identity(decoded["history"]) != config.source.diagnostic:
        raise ValueError("observation worker substitutes its authentic adverse scientific history")
    history = decoded["history"]
    unknown = config.observation.uncertain_work
    original = tuple(row for row in history.source.complete_custody if row.relative_path.endswith("/inputs/producing-provenance.json"))
    if (unknown.original_contact != history.native_contact
            or not any(row.sha256 == unknown.original_producing_source.object_fingerprint for row in original)):
        raise ValueError("observation worker infers or substitutes old uncertain contact/source")
    outputs = ob.operation_outputs(operation)
    if (tuple((port.output_id, port.payload_schema) for port in context.output_ports) != tuple((node + "." + name, record.SCHEMA) for name, record in outputs)
            or any(port.profile is not (ArtifactProfile.JSONL_CHUNKS if name == "segments" else ArtifactProfile.CANONICAL_JSON)
                or port.media_type != ob.media_for(name) for port, (name, _) in zip(context.output_ports, outputs, strict=True))):
        raise ValueError("observation worker changes the complete output contract")
    return config, decoded, ports


def _check_window(config, window, index):
    if type(window) is not ct.ObservedWindow:
        raise ValueError("observation assessment requires its original actual scoped window")
    window.__post_init__()
    result = window.result
    if (result.observation != config.observation or result.configured_method_index != index
            or result.entry_declaration != config.declarations[index] or result.evidence.protocol != config.protocols[index]
            or window.storage != config.storage):
        raise ValueError("observation assessment changes original method/protocol/declaration/root")


def assess_window(window, port):
    """Recompute complete original preparation/call integrity one frame at a time."""
    window.__post_init__()
    result, evidence = window.result, window.result.evidence
    preparation = oc.assess_observation_preparation(result)
    frames = iter(stream.read_frames(port))
    header = next(frames)
    if (type(header) is not stream.SegmentStreamHeader or header.trace != ct.identity(evidence.trace, "trace_id")
            or header.protocol != ct.identity(evidence.protocol, "protocol_id") or header.segment_count != result.observed_native_calls):
        raise ValueError("observation stream changes original complete header/call census")
    previous_terminal, previous_receipt, assessments = None, None, []
    for summary in evidence.trace.segments:
        frame = next(frames, None)
        if (type(frame) is not stream.SegmentEvidenceFrame or frame.segment_index != summary.segment_index
                or frame.definition.identity != summary.native_definition):
            raise ValueError("observation stream changes original call/definition/request publisher chain")
        if previous_receipt is None:
            from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
            checkpoint = native.build_preparation_checkpoint_definition(result.native_definition)
            context = (evidence.protocol, evidence.source_assignment, evidence.layout, frame.request)
            if any(record is None for record in context):
                raise ValueError("observation first request omits completed preparation context")
            publisher = frame.request_receipt
            ss.authenticate_payloads(publisher, context)
            context_ids = {materialization.materialization_id for logical, materialization in zip(
                publisher.output_logical_artifacts, publisher.output_materializations, strict=True)
                if logical.payload_schema != NativeSubworkCompletion.SCHEMA}
            if (publisher.operational_status is not OperationalStatus.SUCCEEDED
                    or publisher.run_id != checkpoint.parent_contact.run_id
                    or publisher.implementation_commit != checkpoint.parent_contact.implementation_commit
                    or not set(checkpoint.input_materialization_ids).issubset(publisher.input_materialization_ids)
                    or sorted(row.payload_schema for row in publisher.output_logical_artifacts)
                        != sorted((*[record.SCHEMA for record in context], NativeSubworkCompletion.SCHEMA))
                    or any(sum(parent.identity == checkpoint.identity for parent in row.lineage_parents) != 1
                        for row in publisher.output_logical_artifacts)
                    or tuple(sorted(set((*checkpoint.input_materialization_ids, *context_ids)))) != frame.definition.input_materialization_ids):
                raise ValueError("observation first request changes its completed preparation publisher/context")
        elif frame.request_receipt != previous_receipt:
            raise ValueError("observation stream changes original call/definition/request publisher chain")
        ss.authenticate_request_custody(summary, frame.request, frame.definition, frame.native_receipt, frame.request_receipt)
        successor = frame.next_request
        if summary.segment_index == result.observed_native_calls:
            if (successor.kind != "end-of-chain" or successor.ordinal != summary.segment_index
                    or successor.primitive_json != canonical_json_bytes({"actual_segment_calls": result.observed_native_calls}).decode()):
                raise ValueError("observation stream hides entered successor work")
        elif (successor.kind != "charging" or successor.ordinal != summary.segment_index + 1
                or successor.identity != evidence.trace.segments[summary.segment_index].request):
            raise ValueError("observation stream changes actual successor request census")
        if summary.disposition == "TECHNICAL_FAILURE":
            assessment = ss.assess_failed_segment(evidence.trace.config, evidence.protocol, summary, frame.native_receipt, **frame.records)
        else:
            if evidence.layout is None:
                raise ValueError("actual returned observation omits its observed layout")
            assessment = ss.assess_segment(evidence.trace.config, evidence.protocol, evidence.layout, summary,
                frame.native_receipt, previous_terminal=previous_terminal, **frame.records)
        assessments.append(assessment)
        previous_terminal, previous_receipt = frame.actual_terminal, frame.native_receipt
        del frame
    if next(frames, None) is not None:
        raise ValueError("observation stream adds undeclared actual calls")
    states = (preparation.disposition, *(row.disposition for row in assessments))
    disposition = ct.combined_disposition(states, incomplete=result.disposition != "OBSERVATION_WINDOW_COMPLETED")
    reasons = {code for row in (preparation, *assessments) for code in row.reason_codes}
    if result.disposition != "OBSERVATION_WINDOW_COMPLETED":
        reasons.add("declared-complete-observation-window-not-returned")
    return ct.ObservationMethodAssessment("assessment." + window.window_id, ct.identity(result.observation, "observation_id"),
        result.configured_method_index, window, preparation, tuple(assessments), disposition, tuple(sorted(reasons)))


class ObservationRunner:
    def __new__(cls, operation):
        if cls is ObservationRunner and operation == "observe":
            return object.__new__(NativeObservationRunner)
        return object.__new__(cls)

    def __init__(self, operation):
        from . import operation_bindings as ob
        if operation not in ob.OPERATIONS:
            raise ValueError("unknown initial-window observation operation")
        self.operation = operation
        self.manifest = next(row for row in ob.operation_manifests() if row.capability_key == ob.NAMESPACE + "." + operation)

    def execute(self, context):
        try:
            config, decoded, ports = _load(context, self.operation, self.manifest)
            if self.operation == "observe":
                raise ValueError("observation requires live native custody and ordinary streaming emitter")
            if self.operation == "assess":
                _check_window(config, decoded["window"], config.index)
                records = (assess_window(decoded["window"], ports["segments"]),)
            elif self.operation == "pair":
                for side, index in (("left", config.index), ("right", config.index + 1)):
                    _check_window(config, decoded[side + "-window"], index)
                records = (assess_streams(config.control,
                    FullStateStreamOperand(decoded["left-window"].result.evidence, ports["left-segments"]),
                    FullStateStreamOperand(decoded["right-window"].result.evidence, ports["right-segments"])),)
            else:
                methods = tuple(decoded["method-" + str(i)] for i in range(3))
                pairs = tuple(decoded["pair-" + str(i)] for i in range(2))
                for i, method in enumerate(methods):
                    _check_window(config, method.window, i)
                if any(pair.control != ct.identity(config.control, "control_id") for pair in pairs):
                    raise ValueError("observation reduction changes prospective full-state controls")
                records = (ct.summarize(config.observation, methods, pairs),)
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                for port, record in zip(context.output_ports, records, strict=True)), (ReceiptCheck("original-observation-independent-complete-reduction", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


class NativeObservationRunner(ObservationRunner):
    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_native as native
        try:
            config, decoded, _ = _load(context, self.operation, self.manifest)
            if self.operation != "observe":
                raise ValueError("PURE observation assessment/reduction cannot enter native work")
            declaration, protocol = config.declarations[config.index], config.protocols[config.index]
            definition = native.build_observation_definition(config.observation, config.index, protocol, config.provenance,
                native_subwork, declaration, context.input_materialization_ids)
            native.freeze_observation_roster(native_subwork, (definition,))
            result = native.acquire_observation(config.observation, config.index, protocol=protocol, provenance=config.provenance,
                definition=definition, native_subwork=native_subwork, entry_declaration=declaration,
                abi_payload=decoded["abi-import-report"], resource_payload=decoded["resource-source"], inputs=None)
            evidence = _original_evidence(native_subwork, definition, result.inspection, config.observation.configurations[config.index])
            original_observation = stream.completed_record(native_subwork, definition, result.inspection, "observation-protocol", oc.PreparationObservationProtocol)
            original_declaration = stream.completed_record(native_subwork, definition, result.inspection, "entry-declaration", oc.ObservationEntryDeclaration)
            if original_observation != config.observation or original_declaration != declaration:
                raise ValueError("completed observation relay substitutes original declaration/source")
            clocks = tuple(row.native_times_s[-1] for row in evidence.trace.segments if row.native_times_s)
            last = clocks[-1] if clocks else None
            disposition = "TECHNICAL_FAILURE" if evidence.trace.disposition == "TECHNICAL_FAILURE" else (
                "OBSERVATION_WINDOW_COMPLETED" if last is not None and last >= config.observation.minimum_observation_clock_s else "PHYSICAL_TERMINATION_BEFORE_OBSERVATION_WINDOW")
            observed = oc.PreparationObservationResult("result." + evidence.trace.config.config_id, original_observation,
                config.index, evidence, definition, original_declaration, disposition, last, len(evidence.trace.segments), original_observation.original_entry_disposition)
            window = ct.ObservedWindow("window." + evidence.trace.config.config_id, observed, result.inspection.completion, config.storage)
            stream_port, window_port = context.output_ports
            stream.emit_record(emitter, window_port.output_id, window)
            header = stream.SegmentStreamHeader(ct.identity(evidence.trace, "trace_id"), ct.identity(protocol, "protocol_id"), len(evidence.trace.segments))
            sequence = stream.emit_frame(emitter, stream_port.output_id, header, 0, 0)
            for frame in stream.relay_segments(native_subwork, definition, result.inspection, evidence.trace, protocol):
                sequence = stream.emit_frame(emitter, stream_port.output_id, frame, frame.segment_index, sequence)
            if progress is not None:
                progress.advance(Decimal(1))
            return (ReceiptCheck("actual-declared-initial-window-original-custody-stream", True, ()),)
        finally:
            for port in context.input_ports:
                port.close()
