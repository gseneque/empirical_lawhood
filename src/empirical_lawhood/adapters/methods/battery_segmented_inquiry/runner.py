# SPDX-License-Identifier: MPL-2.0
"""Ordinary typed workers; native effects require the live shared custody port."""

from decimal import Decimal

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_evidence as se
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_qualification as sq
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_roster as sr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import source_policy_admission
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from . import evidence_stream as stream


def _identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def require_common_records(config, decoded):
    """Original scientific joins, independent of operational port labels."""
    from . import operation_bindings as ob
    roster, unknown, provenance = (decoded[name] for name in ("roster", "uncertain-work", "producing-provenance"))
    if (decoded["source"] != config.source or decoded["policy"] != config.policy or decoded["selection"] != config.policy.selection
            or c.identity(decoded["history"]) != config.source.diagnostic or roster != ob.roster_for(config)
            or _identity(roster, "roster_id") != config.roster or _identity(unknown, "record_id") != config.uncertain_work
            or provenance.identity != config.producing_provenance or decoded["method"] != config.method
            or tuple((decoded["preparation-" + stock], decoded["source-assessment-" + stock]) for stock in ("chen", "oregan")) != config.supplies):
        raise ValueError("segmented worker changes actual source/history/method/supplier/roster/provenance")
    history = decoded["history"]
    old_provenance = tuple(member for member in history.source.complete_custody
        if member.relative_path.endswith("/inputs/producing-provenance.json"))
    if (unknown.original_contact != history.native_contact or not old_provenance
            or not any(member.sha256 == unknown.original_producing_source.object_fingerprint for member in old_provenance)):
        raise ValueError("segmented unknown-work substitutes original actual contact/source identity")


def require_forecast_records(config, decoded):
    """Recompute the original development witnesses, never execution authority."""
    from . import recursive_translation as rt
    require_common_records(config, decoded)
    if config.operation != "forecast":
        raise ValueError("segmented native preparation requires the selected original forecast")
    native_config = decoded["roster"].configurations[config.index]
    admission = source_policy_admission(config.source, config.policy, config.policy.selection, decoded["history"])
    entry = sr.method_dispositions(decoded["roster"], decoded["uncertain-work"])[config.index]
    protocol, provenance = decoded["selected-protocol"], decoded["producing-provenance"]
    if (decoded["admission"] != admission or decoded["entry"] != entry or decoded["native-config"] != native_config
            or _identity(protocol, "protocol_id") != rt.protocol_for(config, config.index)
            or protocol.configuration != c.identity(native_config) or protocol.source != c.identity(config.source)
            or protocol.producing_provenance != provenance.identity):
        raise ValueError("segmented forecast changes exact prospective gate/config/protocol/actual operands")


def _load(context, operation, manifest, *, scientific_input_ports=None, scientific_output_ports=None):
    from . import operation_bindings as ob, recursive_translation as rt
    input_ports = context.input_ports if scientific_input_ports is None else scientific_input_ports
    output_ports = context.output_ports if scientific_output_ports is None else scientific_output_ports
    if any(port not in context.input_ports for port in input_ports) or any(port not in context.output_ports for port in output_ports):
        raise ValueError("segmented scientific operands are not the original complete task's ports")
    configs = tuple(port for port in input_ports if port.payload_schema == ob.SegmentedOperationConfig.SCHEMA)
    if len(configs) != 1:
        raise ValueError("segmented worker requires exactly one immutable operation config")
    config_port = configs[0]
    config = decode_canonical_bytes(config_port.read(), ob.SegmentedOperationConfig, maximum_bytes=None)
    node = ob.node_id(config.operation, config.index)
    if (operation != config.operation or context.task_id != node or context.permissions != manifest.permissions
            or context.resource_budget != ob.BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or config_port.kind is not WorkerInputKind.EXTERNAL or config_port.artifact_id != context.config.artifact_id
            or config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id):
        raise ValueError("segmented worker substitutes exact task/config/access/resources")
    expected = dict((*ob.common_inputs(config), *ob.operation_inputs(operation)))
    sources = rt.input_sources(config)
    decoded, ports = {}, {}
    for name, record_type in expected.items():
        source_kind, artifact = sources[name]
        artifact_id = f"artifact.{context.run_id}.{artifact}" if source_kind == "DEPENDENCY" else artifact
        found = tuple(port for port in input_ports if port.artifact_id == artifact_id)
        if len(found) != 1:
            raise ValueError("segmented worker omits or substitutes declared input ordinal")
        port = found[0]
        if (port.kind is not (WorkerInputKind.DEPENDENCY if source_kind == "DEPENDENCY" else WorkerInputKind.EXTERNAL)
                or port.payload_schema != record_type.SCHEMA or port.media_type != ob.media_for(name)
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("segmented worker changes declared typed input/access")
        if source_kind == "DEPENDENCY":
            producer = artifact.rsplit(".", 1)[0]
            if not any(receipt.task_id == producer and port.materialization_id in receipt.output_materialization_ids
                       for receipt in context.dependency_receipts):
                raise ValueError("segmented worker loses actual producing dependency receipt")
        ports[name] = port
        if name != "segments":
            raw = port.read()
            if len(raw) != port.size_bytes:
                raise ValueError("segmented input materialization size differs")
            decoded[name] = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
    if len(input_ports) != len(expected) + 1:
        raise ValueError("segmented worker has undeclared inputs")
    producers = {origin.rsplit(".", 1)[0] for kind, origin in sources.values() if kind == "DEPENDENCY"}
    if {receipt.task_id for receipt in context.dependency_receipts} != producers or len(context.dependency_receipts) != len(producers):
        raise ValueError("segmented worker changes exact producing receipt census")
    require_common_records(config, decoded)
    outputs = ob.operation_outputs(operation)
    if (tuple((port.output_id, port.payload_schema) for port in output_ports) != tuple((node + "." + name, record.SCHEMA) for name, record in outputs)
            or any(port.profile is not (ArtifactProfile.JSONL_CHUNKS if name == "segments" else ArtifactProfile.CANONICAL_JSON)
                or port.media_type != ob.media_for(name) for port, (name, _) in zip(output_ports, outputs, strict=True))):
        raise ValueError("segmented worker changes complete output contract")
    return config, decoded, ports


def _assess(config, evidence, port):
    evidence.__post_init__()
    if evidence.trace.config != config:
        raise ValueError("segment assessor substitutes selected configured forecast")
    preparation = se.assess_preparation_evidence(config, evidence)
    frames = iter(stream.read_frames(port))
    header = next(frames)
    if (type(header) is not stream.SegmentStreamHeader or header.trace != c.identity(evidence.trace)
            or header.protocol != _identity(evidence.protocol, "protocol_id") or header.segment_count != len(evidence.trace.segments)):
        raise ValueError("segment assessor receives another original stream/header/call denominator")
    previous_terminal, assessments = None, []
    for summary in evidence.trace.segments:
        try:
            frame = next(frames)
        except StopIteration as error:
            raise ValueError("segment stream omits an actual selected call") from error
        if (type(frame) is not stream.SegmentEvidenceFrame or frame.segment_index != summary.segment_index
                or frame.definition.identity != summary.native_definition):
            raise ValueError("segment stream substitutes original call/definition ordinal")
        ss.authenticate_request_custody(summary, frame.request, frame.definition, frame.native_receipt, frame.request_receipt)
        successor = frame.next_request
        if summary.segment_index == len(evidence.trace.segments):
            if (successor.kind != "end-of-chain" or successor.ordinal != summary.segment_index
                    or successor.primitive_json != canonical_json_bytes({"actual_segment_calls": len(evidence.trace.segments)}).decode()):
                raise ValueError("segment stream hides actual unclosed successor work or changes complete call census")
        elif (successor.kind != "charging" or successor.ordinal != summary.segment_index + 1
                or successor.identity != evidence.trace.segments[summary.segment_index].request):
            raise ValueError("segment stream changes original precontact successor request census")
        if summary.disposition == "TECHNICAL_FAILURE":
            assessment = ss.assess_failed_segment(config, evidence.protocol, summary, frame.native_receipt, **frame.records)
        else:
            if evidence.layout is None:
                raise ValueError("returned segment omits its actually produced complete processed layout")
            assessment = ss.assess_segment(config, evidence.protocol, evidence.layout, summary,
                frame.native_receipt, previous_terminal=previous_terminal, **frame.records)
        assessments.append(assessment)
        previous_terminal = frame.actual_terminal
        # Only original terminal vector and compact assessment survive a frame.
        del frame
    if next(frames, None) is not None:
        raise ValueError("segment stream adds undeclared selected calls")
    return sq.summarize_trace(evidence.trace, preparation, tuple(assessments))


def _original_evidence(progress, definition, inspection, config):
    records = {}
    for name, record_type in (("trace", sc.SegmentedTrace), ("protocol", pc.PreparationProtocol),
            ("source_assignment", sc.ActualSourceAssignment), ("layout", pc.ProcessedInitialStateLayout),
            *((name, pc.StateObservation) for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"))):
        records[name] = stream.completed_record(progress, definition, inspection, name.replace("_", "-"), record_type,
            optional=name not in {"trace", "protocol"})
    evidence = se.SegmentedNativeEvidence("evidence." + config.config_id, **records, native_receipt=inspection.receipt)
    if evidence.trace.config != config:
        raise ValueError("native relay returns another exact configured forecast")
    return evidence


class SegmentedRunner:
    def __new__(cls, operation=None):
        if cls is SegmentedRunner and operation == "forecast":
            return object.__new__(NativeSegmentedRunner)
        return object.__new__(cls)

    def __init__(self, operation):
        from . import operation_bindings as ob
        if operation not in ob.OPERATIONS:
            raise ValueError("unknown segmented battery operation")
        self.operation = operation
        self.manifest = next(row for row in ob.operation_manifests() if row.capability_key == ob.NAMESPACE + "." + operation)

    def execute(self, context):
        from . import recursive_translation as rt
        try:
            config, decoded, ports = _load(context, self.operation, self.manifest)
            roster, unknown = decoded["roster"], decoded["uncertain-work"]
            if self.operation == "forecast":
                raise ValueError("segmented forecast requires live native custody and ordinary streaming emitter")
            if self.operation == "validate":
                records = (source_policy_admission(config.source, config.policy, config.policy.selection, decoded["history"]),
                    *sr.method_dispositions(roster, unknown))
            elif self.operation == "assess":
                evidence = decoded["evidence"]
                if (_identity(evidence.protocol, "protocol_id") != rt.protocol_for(config, config.index)
                        or evidence.protocol.producing_provenance != decoded["producing-provenance"].identity):
                    raise ValueError("independent assessment changes original forecast protocol/provenance")
                records = (_assess(roster.configurations[config.index], evidence, ports["segments"]),)
            elif self.operation == "reuse":
                summary = sq.reuse_summary(roster.configurations[config.index], decoded["summary"])
                records = (summary.condition_reuse, summary)
            elif self.operation == "compare":
                left, right = decoded["left-evidence"], decoded["right-evidence"]
                records = (sq.compare_traces(left.trace, right.trace, decoded["left-summary"], decoded["right-summary"]),)
            else:
                records = (sq.qualify_summaries(roster, tuple(decoded["summary-" + f"{i:03d}"] for i in range(54)),
                    tuple(decoded["comparison-" + f"{i:03d}"] for i in range(36))),)
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                for port, record in zip(context.output_ports, records, strict=True)),
                (ReceiptCheck("segmented-source-and-full-adverse-denominator", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


class NativeSegmentedRunner(SegmentedRunner):
    def forecast_operands(self, context):
        return _load(context, self.operation, self.manifest)

    def forecast_output_ports(self, context):
        return context.output_ports

    def forecast_definition(self, config, decoded, expected_parent, materializations):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
        return native.forecast_definition(decoded["native-config"], decoded["selected-protocol"],
            decoded["producing-provenance"], expected_parent, materializations)

    def project_forecast_scope(self, context, expected_parent):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
        from empirical_lawhood.runtime.native_effects import NativeEffectContact
        if (type(expected_parent) is not NativeEffectContact
                or (expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id,
                    expected_parent.input_materialization_ids, expected_parent.dependency_receipt_ids) != (
                    context.run_id, context.task_id, context.attempt_id,
                    context.input_materialization_ids, context.dependency_receipt_ids)):
            raise ValueError("segmented forecast changes its full anticipated original parent/context")
        config, decoded, ports = self.forecast_operands(context)
        require_forecast_records(config, decoded)
        native_config = decoded["native-config"]
        protocol, provenance = decoded["selected-protocol"], decoded["producing-provenance"]
        materializations = context.input_materialization_ids
        if tuple(sorted(port.materialization_id for port in context.input_ports)) != materializations:
            raise ValueError("segmented forecast changes its complete original input materialization census")
        definition = self.forecast_definition(config, decoded, expected_parent, materializations)
        # The common invocation retains the whole selected source. A historical
        # producing input cannot silently become a new current implementation.
        prepared = getattr(context, "prepared_invocation", None)
        if prepared is not None and expected_parent != prepared.expected_parent_contact:
            raise ValueError("segmented forecast changes its complete original prepared parent")
        if prepared is not None and (provenance.package_sources, provenance.code_sources_sha256,
                provenance.dependency_lock_sha256, provenance.observed_git_head) != (
                prepared.implementation.package_sources, prepared.implementation.code_sources_sha256,
                prepared.implementation.dependency_lock_sha256, prepared.implementation.observed_git_head):
            raise ValueError("segmented forecast requires actual selected current producing provenance and protocol")
        native.require_installed_forecast_sources(native_config, protocol)
        return config, decoded, ports, definition

    def preflight(self, context):
        import os
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native as passive
        prepared = getattr(context, "prepared_invocation", None)
        if prepared is None:
            raise ValueError("SOFTWARE: segmented forecast requires its complete prepared invocation")
        prepared.validate_context(context)
        if (dict(prepared.environment.selected_environment).get("PYBAMM_DISABLE_TELEMETRY") != "true"
                or os.environ.get("PYBAMM_DISABLE_TELEMETRY") != "true"):
            raise ValueError("ENVIRONMENT: select PYBAMM_DISABLE_TELEMETRY=true before worker preparation")
        passive.require_native_worker_environment(prepared.environment)
        # Only the actual selected worker imports the native package. Parent
        # preparation checks installed metadata and source bytes without import.
        import pybamm
        selected, decoded, _ = self.forecast_operands(context)
        passive._validate_source_pins(pybamm, decoded["selected-protocol"])
        if pybamm.__version__ != selected.source.original.pybamm_version:
            raise ValueError("ENVIRONMENT: actual PyBaMM import differs from the selected native version")

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
        try:
            prepared = getattr(context, "prepared_invocation", None)
            if prepared is None or prepared.native_work is None or native_subwork is None:
                raise ValueError("SOFTWARE: segmented forecast requires complete prepared native work and the live coordinator port")
            prepared.validate_context(context)
            config, decoded, _, definition = self.project_forecast_scope(context, prepared.expected_parent_contact)
            native_config = decoded["roster"].configurations[config.index]
            protocol, provenance = decoded["selected-protocol"], decoded["producing-provenance"]
            if (prepared.native_work.definitions != (definition,)
                    or native_subwork.parent_contact != prepared.expected_parent_contact):
                raise ValueError("segmented forecast changes its full prepared native parent/definition census")
            native.freeze_forecast_roster(native_subwork, (definition,))
            result = native.acquire_segmented(native_config, protocol=protocol, provenance=provenance, definition=definition,
                native_subwork=native_subwork, inputs=None)
            evidence = _original_evidence(native_subwork, definition, result.inspection, native_config)
            evidence_port, stream_port = self.forecast_output_ports(context)
            stream.emit_record(emitter, evidence_port.output_id, evidence)
            header = stream.SegmentStreamHeader(c.identity(evidence.trace), _identity(protocol, "protocol_id"), len(evidence.trace.segments))
            sequence = stream.emit_frame(emitter, stream_port.output_id, header, 0, 0)
            for frame in stream.relay_segments(native_subwork, definition, result.inspection, evidence.trace, protocol):
                sequence = stream.emit_frame(emitter, stream_port.output_id, frame, frame.segment_index, sequence)
            if progress is not None:
                progress.advance(Decimal(1))
            return (ReceiptCheck("segmented-actual-original-return-stream-and-custody", True, ()),)
        finally:
            for port in context.input_ports:
                port.close()


def prepare_native_work(*, runner, context, expected_parent):
    """Original initial forecast only; future checkpoint/calls remain absent."""
    from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
    from . import operation_bindings as ob
    config, _, _, definition = runner.project_forecast_scope(context, expected_parent)
    return PreparedNativeWork(expected_parent, (c.UNIT,), ob.native_effect_slot_ids(config), (definition,),
        (NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,)),))
