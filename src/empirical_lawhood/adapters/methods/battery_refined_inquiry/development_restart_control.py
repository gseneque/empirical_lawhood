# SPDX-License-Identifier: MPL-2.0
"""Explicit two-call development control over the actual battery interfaces.

This is neither a forecast nor a replacement scientific method. The selected
forecast configuration retains its complete horizon and target. This separate
control records its own two requested native calls, complete returned arrays,
actual restart operands and known failures through the existing custody owner.
Only the caller may select and enter it. Recovery never calls the solver.
"""

from dataclasses import dataclass, replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import resource
import time
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput

from . import forecast_step_control as step
from . import lossless_segment_native as storage
from . import lossless_evidence_stream as stream
from . import lossless_segment_consumer as consumer
from . import lossless_segment_records as records
from . import preparation_contracts as preparation
from . import prepared_native as passive
from . import segmented_contracts as contracts
from . import segmented_native as native
from . import segmented_fidelity as fidelity
from . import segmented_science as science
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as old_stream

SCOPE = "EXPOSED_TWO_STEP_INTERFACE_CONTROL;NO_FORECAST_COMPLETION_OR_MODEL_ADMISSION"


@dataclass(frozen=True, slots=True)
class DevelopmentRestartControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-development/restart-control"
    control_id: str
    configuration: ObjectIdentity
    native_policy: ObjectIdentity
    requested_durations_s: tuple[D, D] = (D(1), D(1))
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.control_id)
        if (type(self.configuration) is not ObjectIdentity
                or self.configuration.object_schema != contracts.SegmentedNativeConfig.SCHEMA
                or type(self.native_policy) is not ObjectIdentity
                or self.native_policy.object_schema != step.ForecastStepPolicy.SCHEMA
                or type(self.requested_durations_s) is not tuple
                or any(type(value) is not D for value in self.requested_durations_s)
                or self.requested_durations_s != (D(1), D(1)) or self.scope != SCOPE):
            raise ValueError("development restart control changes its declared two-call scope")
        self.configuration.__post_init__()
        self.native_policy.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.control_id, self)


@dataclass(frozen=True, slots=True)
class DevelopmentRestartResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-development/restart-result"
    result_id: str
    control: DevelopmentRestartControl
    summaries: tuple[contracts.SegmentSummary, ...]
    actual_assignment: step.ActualForecastStepAssignment | None
    error_type: str | None
    error_message: str | None
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if type(self.control) is not DevelopmentRestartControl or self.scope != SCOPE:
            raise ValueError("development result substitutes its explicit control")
        self.control.__post_init__()
        if (type(self.summaries) is not tuple or len(self.summaries) > 2
                or any(type(row) is not contracts.SegmentSummary for row in self.summaries)
                or tuple(row.segment_index for row in self.summaries) != tuple(range(1, len(self.summaries) + 1))
                or any(row.configuration != self.control.configuration
                    or row.requested_horizon_s != self.control.requested_durations_s[row.segment_index - 1]
                    for row in self.summaries)
                or (self.error_type is None) != (self.error_message is None)
                or (self.error_type is None and (len(self.summaries) != 2
                    or any(row.disposition != "RETURNED" for row in self.summaries)))):
            raise ValueError("development result hides its complete actual/unentered denominator")
        for row in self.summaries:
            row.__post_init__()
        if self.actual_assignment is not None:
            self.actual_assignment.__post_init__()
            if (self.actual_assignment.native_configuration != self.control.configuration
                    or self.actual_assignment.control.identity != self.control.native_policy):
                raise ValueError("development result substitutes its actual native assignment")


def outputs():
    return tuple(sorted((NativeSubworkOutput(name, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json") for name, record in (
            ("control", DevelopmentRestartControl), ("result", DevelopmentRestartResult),
            ("native.request.first", native.SegmentRequest),
            ("protocol", preparation.PreparationProtocol), ("layout", preparation.ProcessedInitialStateLayout),
            ("source-assignment", contracts.ActualSourceAssignment),
            ("step-assignment", step.ActualForecastStepAssignment),
            ("forecast-step-policy", step.ForecastStepPolicy))), key=lambda row: row.output_id))


def _record(progress, inspection, name, record_type):
    raw = b"".join(progress.iter_completed_output(inspection.definition, name))
    return decode_canonical_bytes(raw, record_type, maximum_bytes=len(raw))


def acquire(control, config, protocol, provenance, policy, original, selected, *, definition, progress, inputs=None):
    """Real source/solver calls only after the selected existing BEGIN guard."""
    control.__post_init__()
    step.require_policy(policy, original, selected)
    step.require_config(policy, selected, config)
    for row in (config, protocol, provenance):
        row.__post_init__()
    required = (control.identity, step.identity(config.source, "source_id"), step.identity(protocol, "protocol_id"),
        step.identity(config.preparation, "preparation_id"), step.identity(config.preparation_assessment, "assessment_id"),
        step.identity(config.method, "method_id"), *policy.sources)
    if (type(provenance) is not NumericalProducingProvenance
            or control.configuration != step.identity(config, "config_id")
            or control.native_policy != step.identity(policy, "policy_id")
            or definition.operation_id != "battery.development.restart-control"
            or definition.configuration != control.configuration
            or definition.outputs != outputs() or not set(required).issubset(definition.sources)
            or provenance.identity not in definition.sources
            or definition.code_sources_sha256 != provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != provenance.dependency_lock_sha256
            or protocol.configuration != control.configuration or protocol.producing_provenance != provenance.identity
            or protocol.source != step.identity(config.source, "source_id")
            or protocol.parameter_source != config.preparation.parameter_source
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or (protocol.electrode_points, protocol.particle_points) != (
                config.native.numerical_view.electrode_points, config.native.numerical_view.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k):
        raise ValueError("development entry changes its exact selected source/control/definition joins")
    recovered = progress.recover(definition)
    if recovered is not None:
        return _record(progress, recovered, "result", DevelopmentRestartResult), recovered, True
    entry = progress.begin(definition, inputs)
    progress.contact(entry)
    wall_start, cpu_start = time.monotonic(), time.process_time()
    extra_bytes = 0

    def publish(name, record):
        nonlocal extra_bytes
        materialized = passive._publish(progress, entry, name, record)
        extra_bytes += materialized.materialization.size_bytes

    publish("control", control)
    publish("protocol", protocol)
    publish("forecast-step-policy", policy)
    summaries, assignment, error = [], None, None
    chain = native._SegmentChain(progress, entry, protocol, inputs)
    try:
        import numpy as np
        import pybamm
        passive._validate_source_pins(pybamm, protocol)
        for member, expected in config.source.source_members:
            if sha256((Path(pybamm.__file__).parent / member).read_bytes()).hexdigest() != expected:
                raise ValueError("actual development native source differs: " + member)
        with native.forbid_native_esoh(pybamm), storage.native_storage_scope():
            backend = step._BackendView(pybamm, policy, config.native)
            built, solver, _, source_assignment, _, _ = native.build_runtime(config, protocol, backend)
            if backend.calls != 1 or backend.assignment is None:
                raise ValueError("development control lacks its actual constructor assignment")
            assignment = step.ActualForecastStepAssignment("assignment." + control.control_id,
                policy, control.configuration, config.native.numerical_view, *backend.assignment)
            layout = passive.observe_processed_layout(built, protocol)
            publish("source-assignment", source_assignment)
            publish("step-assignment", assignment)
            publish("layout", layout)
            regime = "HIGH" if config.initial_temperature_k >= native.TIER_TEMPERATURE + config.localization_epsilon_k else "LOW"
            start, previous, terminal = D(0), None, None
            first_primitive = native._request_primitive(config, layout, solver, regime, start,
                control.requested_durations_s[0], terminal)
            chain.prepare(source_assignment, layout, first_primitive,
                extra_records=(("forecast-step-policy", policy), ("step-assignment", assignment)))
            for index, horizon in enumerate(control.requested_durations_s):
                primitive = first_primitive if index == 0 else native._request_primitive(config, layout, solver, regime, start, horizon, terminal)
                request = chain.enter(primitive)
                call_cpu, call_wall = time.process_time(), time.monotonic()
                states, full, raw, solution, native_times, first, last = {}, None, None, None, (), (), ()
                terminal_manifest, returned, failure = None, None, None
                termination = "native-not-returned"

                def receive(state):
                    if "requested-initial" in states:
                        raise ValueError("development call repeats requested initialization")
                    chain.publish("requested-initial", state)
                    states["requested-initial"] = state

                try:
                    with native.observe_requested_initialization(pybamm, built, protocol, layout, request, receive):
                        solution = solver.step(previous, built, float(horizon), inputs=primitive["inputs"], save=False)
                except native._CustodyFailure:
                    raise
                except Exception as caught:
                    failure = caught
                    returned = chain.returned(request, error=caught)
                else:
                    returned = chain.returned(request)
                    try:
                        raw = native.observe_raw_return(solution, protocol, request, returned)
                        chain.publish("raw-return", raw)
                        full = native.observe_full_segment(solution, protocol, layout, request, returned, raw)
                        chain.publish("full-state", full)
                        endpoints = passive._solution_observation(solution)
                        witnesses = (step.identity(returned, "return_id"), step.identity(full, "segment_id"))
                        for role, at in (("actual-initial", 0), ("actual-terminal", 1), ("initial-derivative", 0), ("terminal-derivative", 1)):
                            derivative = role.endswith("derivative")
                            state = (passive.unavailable_state(role, protocol, layout) if derivative and endpoints["derivatives"] is None
                                else passive.observe_state(endpoints["derivatives" if derivative else "states"][at],
                                    endpoints["clocks"][at], role, protocol, layout, witnesses))
                            state = replace(state, observation_id=request.request_id + "." + role)
                            materialized = chain.publish(role, state)
                            states[role] = state
                            if role == "actual-terminal":
                                terminal_manifest = materialized
                        native_times = tuple(passive._decimal(value) for value in np.asarray(solution.t).reshape(-1))
                        names = ("Current [A]", "Voltage [V]", "Volume-averaged cell temperature [K]", "Discharge capacity [A.h]")
                        first, last = (tuple(passive._decimal(np.asarray(solution[name](float(clock))).reshape(-1)[0])
                            for name in names) for clock in (native_times[0], native_times[-1]))
                        termination = str(solution.termination)
                        if termination != "final time" or float(native_times[-1]) != float(start) + float(horizon):
                            raise ValueError("development two-step control observed an actual event/short return")
                        previous = native.detached_continuation(solution, pybamm) if index == 0 else None
                    except native._CustodyFailure:
                        raise
                    except Exception as caught:
                        failure = caught
                next_primitive = None
                if failure is None and index == 0:
                    terminal = step.identity(states["actual-terminal"], "observation_id")
                    next_primitive = native._request_primitive(config, layout, solver, regime, native_times[-1],
                        control.requested_durations_s[1], terminal)
                inspection = chain.close(next_primitive=next_primitive, terminal_manifest=terminal_manifest,
                    failure=failure, cpu_start=call_cpu, wall_start=call_wall)
                summary = contracts.SegmentSummary(request.request_id + ".summary", control.configuration,
                    step.identity(protocol, "protocol_id"), index + 1, regime, start, horizon, request.identity,
                    step.identity(returned, "return_id"), step.identity(inspection.receipt, "receipt_id"),
                    "RETURNED" if failure is None else "TECHNICAL_FAILURE", termination,
                    None if failure is None else type(failure).__name__, None if failure is None else str(failure),
                    chain.last_cost.cpu_seconds, chain.last_cost.wall_seconds,
                    int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024, native_times, first, last,
                    None if full is None else step.identity(full, "segment_id"),
                    *(None if role not in states else step.identity(states[role], "observation_id") for role in
                        ("requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")),
                    inspection.definition.identity, None if raw is None else step.identity(raw, "raw_id"))
                summaries.append(summary)
                del solution, raw, full
                states.clear()
                if failure is not None:
                    raise failure
                start = native_times[-1]
    except native._CustodyFailure:
        raise
    except Exception as caught:
        error = caught
    result = DevelopmentRestartResult("result." + control.control_id, control, tuple(summaries), assignment,
        None if error is None else type(error).__name__, None if error is None else str(error))
    publish("result", result)
    cost = InquiryCost(passive._decimal(time.process_time() - cpu_start),
        passive._decimal(time.monotonic() - wall_start), D(extra_bytes + chain.retained_bytes))
    completed = progress.complete(entry, operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
        cost=cost, cost_scope="whole two-step development entry including nested calls; do not sum nested costs twice",
        consumed_streams=definition.streams, peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024,
        reason_codes=() if error is None else ("development-restart-control-technical-failure",))
    return result, completed, False


def readback(control, config, *, definition, progress, temporary_file):
    """Read authentic completion and all original arrays without producer calls.

    Domain arithmetic is the existing independently declared segment consumer.
    Every child input/output, original request and physical raw stream is joined
    to its receipt before assessment. A one-product working set closes before
    reading the next child. The two-step control supplies no whole-forecast,
    continuous-time, tier-event or terminal-suffix admission certificate.
    """
    inspection = progress.recover(definition)
    if inspection is None:
        raise ValueError("development readback requires an authentic completed entry")
    result = _record(progress, inspection, "result", DevelopmentRestartResult)
    if result.control != control or control.configuration != step.identity(config, "config_id"):
        raise ValueError("development readback changes selected control/configuration")
    protocol = _record(progress, inspection, "protocol", preparation.PreparationProtocol)
    source_assignment = old_stream.completed_record(progress, definition, inspection,
        "source-assignment", contracts.ActualSourceAssignment, optional=True)
    layout = old_stream.completed_record(progress, definition, inspection,
        "layout", preparation.ProcessedInitialStateLayout, optional=True)
    assignment = old_stream.completed_record(progress, definition, inspection,
        "step-assignment", step.ActualForecastStepAssignment, optional=True)
    actual_control = _record(progress, inspection, "control", DevelopmentRestartControl)
    science.authenticate_payloads(inspection.receipt,
        tuple(row for row in (result, actual_control, protocol, source_assignment, layout, assignment) if row is not None))
    if actual_control != control or assignment != result.actual_assignment or result.summaries and (layout is None or assignment is None):
        raise ValueError("development readback hides its actual preparation/assignment")
    checkpoint = native.completed_preparation_checkpoint(progress, definition)
    previous, preceding_terminal, assessments, prepared = inspection if checkpoint is None else checkpoint, None, [], None
    context = () if checkpoint is None else tuple(row.materialization.materialization_id for row in checkpoint.outputs)
    for summary in result.summaries:
        name = "native.request.first" if summary.segment_index == 1 else "native.request.next"
        request = old_stream.completed_record(progress, previous.definition, previous, name, native.SegmentRequest)
        request_manifest = old_stream._manifest(previous, name)
        additional = [request_manifest.materialization.materialization_id]
        if summary.segment_index != 1:
            terminal = old_stream._manifest(previous, "actual-terminal")
            if terminal is None:
                raise ValueError("development restart lost complete prior-terminal custody")
            additional.append(terminal.materialization.materialization_id)
        child = progress.resolve_completed_definition(summary.native_definition)
        if (request.identity != summary.request or child.identity != summary.native_definition
                or child.parent_contact != definition.parent_contact
                or child.subwork_id != definition.subwork_id + ".segment." + str(summary.segment_index)
                or child.configuration != request.identity or child.operation_id != "battery.segmented-native.segment"
                or child.sources != definition.sources or child.streams != definition.streams
                or child.code_sources_sha256 != definition.code_sources_sha256
                or child.dependency_lock_sha256 != definition.dependency_lock_sha256
                or child.input_materialization_ids != tuple(sorted(set((*definition.input_materialization_ids, *context, *additional))))
                or child.outputs != storage.segment_outputs()
                or child.roster_id != "conditional.battery.segment." + str(summary.segment_index)):
            raise ValueError("development readback changes exact original child/source/input/output joins")
        if (assignment is None or assignment.numerical_view != config.native.numerical_view
                or json.loads(request.primitive_json)["solver"] != json.loads(assignment.actual_solver_json)
                or not set(assignment.control.sources).issubset(child.sources)):
            raise ValueError("development readback changes actual request/full solver assignment")
        current = progress.recover(child)
        if current is None or step.identity(current.receipt, "receipt_id") != summary.native_receipt:
            raise ValueError("development readback substitutes a completed native receipt")
        raw_manifest = old_stream._manifest(current, "raw-return")

        def lines():
            return stream.bounded_lines(progress.iter_completed_output(child, "raw-return",
                maximum_chunk_bytes=records.codec.CHUNK_BYTES))

        raw_index = None
        if raw_manifest is not None:
            if raw_manifest.logical.payload_schema != records.RawSegmentStreamLine.SCHEMA:
                raise ValueError("development readback substitutes its original raw schema")
            raw_lines = iter(lines())
            try:
                raw_index = records._read_line(next(raw_lines), 0).index
            finally:
                raw_lines.close()
        metadata = stream.LosslessSegmentMetadata(summary.segment_index, child, previous.receipt, current.receipt,
            request, old_stream.completed_record(progress, child, current, "native.return", native.SegmentReturn),
            old_stream.completed_record(progress, child, current, "native.request.next", native.SegmentRequest),
            raw_index, None if raw_manifest is None else raw_manifest.logical.content_sha256,
            None if raw_manifest is None else raw_manifest.materialization.size_bytes,
            old_stream.completed_record(progress, child, current, "full-state", records.FullSegmentIndex, optional=True),
            *(old_stream.completed_record(progress, child, current, name, preparation.StateObservation, optional=True)
                for name in ("requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")))
        frame = stream.decoded_frame(metadata, lines() if raw_manifest is not None else iter(()), temporary_file)
        try:
            if summary.segment_index == 1:
                operands = (("source-assignment", source_assignment), ("layout", layout),
                    ("requested-initial", frame.requested_initial), ("actual-initial", frame.actual_initial))
                missing = tuple(sorted(name for name, value in operands if value is None))
                prepared = (science.UnavailableDerivedPreparationAssessment("assessment.unavailable." + control.control_id,
                    control.configuration, step.identity(protocol, "protocol_id"), step.identity(config.preparation, "preparation_id"),
                    step.identity(config.preparation_assessment, "assessment_id"), step.identity(inspection.receipt, "receipt_id"),
                    missing, ("actual-complete-preparation-operands-unavailable",)) if missing else
                    science.assess_derived_preparation(config, protocol, source_assignment, layout,
                        frame.requested_initial, frame.actual_initial))
            checked = consumer.assess_operand(fidelity.FullStateOperand(config, protocol, layout, summary, frame, preceding_terminal))
            assessments.append(checked)
            preceding_terminal = frame.actual_terminal
        finally:
            frame.close()
        previous = current
    return result, tuple(assessments), inspection, prepared
