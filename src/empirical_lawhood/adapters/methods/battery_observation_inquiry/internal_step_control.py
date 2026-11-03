# SPDX-License-Identifier: MPL-2.0
"""Explicit one-factor internal-step experiment over the unchanged observer.

The base configuration describes the preserved model, preparation, external
continuation and tolerances. This separate scientific operand describes the
changed IDAKLU internal step. It is a real compiler input, a native definition
source and a retained native output; it cannot be supplied as an implicit option.
The local native wrapper runs in one isolated task process and restores both
original observation hooks on every exit. Custody and entry guards stay owned by
their existing implementations.
"""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import Decimal
import json
import io
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_native as native
from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native as passive
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput
from empirical_lawhood.runtime.execution import WorkerInputKind, RunnerResult, TaskOutputPayload
from . import contracts as ct
from .runner import ObservationRunner, NativeObservationRunner, _load

D = Decimal
SCOPE = "INITIAL_WINDOW_ONE_FACTOR_INTERNAL_STEP_ACCURACY;NO_FULL_FORECAST_OR_PHYSICAL_QUALIFICATION"


@dataclass(frozen=True, slots=True)
class InternalStepControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/internal-step-control"
    control_id: str
    original_observation: ObjectIdentity
    original_negative_readout: ObjectIdentity
    maximum_internal_step_s: Decimal
    baseline_native_request: ObjectIdentity
    baseline_solver_json: str
    baseline_internal_step_s: Decimal = D(0)
    unchanged_rtol: Decimal = D("1e-7")
    unchanged_atol: Decimal = D("1e-8")
    unchanged_electrode_points: int = 30
    unchanged_particle_points: int = 40
    scope: str = SCOPE
    physical_units: int = 0

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_observation_contracts import PreparationObservationProtocol
        validate_stable_id(self.control_id)
        baseline = json.loads(self.baseline_solver_json)
        if (type(self.original_observation) is not ObjectIdentity
                or self.original_observation.object_schema != PreparationObservationProtocol.SCHEMA
                or type(self.original_negative_readout) is not ObjectIdentity
                or self.original_negative_readout.object_schema != ct.ObservationReadout.SCHEMA
                or type(self.baseline_native_request) is not ObjectIdentity
                or self.baseline_native_request.object_schema != "empirical-lawhood/battery-segmented/native-request"
                or baseline.get("type") != "IDAKLUSolver"
                or baseline.get("options", {}).get("dt_max") != {"binary64": 0.0.hex()}
                or baseline.get("rtol") != {"binary64": float(self.unchanged_rtol).hex()}
                or baseline.get("atol") != {"binary64": float(self.unchanged_atol).hex()}
                or type(self.maximum_internal_step_s) is not D or self.maximum_internal_step_s not in (D(1), D("0.5"))
                or type(self.baseline_internal_step_s) is not D or self.baseline_internal_step_s != 0
                or type(self.unchanged_rtol) is not D or self.unchanged_rtol != D("1e-7")
                or type(self.unchanged_atol) is not D or self.unchanged_atol != D("1e-8")
                or type(self.unchanged_electrode_points) is not int or self.unchanged_electrode_points != 30
                or type(self.unchanged_particle_points) is not int or self.unchanged_particle_points != 40
                or self.scope != SCOPE or type(self.physical_units) is not int or self.physical_units != 0):
            raise ValueError("internal-step control changes its declared isolated numerical operand or claim scope")

    @property
    def identity(self):
        return ct.identity(self, "control_id")


def require_control(control, reference, observation, baseline_request=None):
    """Join full original negative evidence and the unchanged three-method recipe."""
    if type(control) is not InternalStepControl or type(reference) is not ct.ObservationReadout:
        raise ValueError("internal-step control needs its original typed scientific negative")
    control.__post_init__()
    reference.__post_init__()
    if (control.original_negative_readout != ct.identity(reference, "readout_id")
            or control.original_observation != ct.identity(reference.observation, "observation_id")
            or observation != reference.observation or reference.disposition is not A.FALSIFIED
            or any(row.window.result.disposition != "OBSERVATION_WINDOW_COMPLETED" or row.disposition is not A.SATISFIED
                   for row in reference.methods)
            or any(row.disposition is not A.FALSIFIED for row in reference.pairs)):
        raise ValueError("internal-step control substitutes its authentic completed negative observation")
    for config in observation.configurations:
        view = config.numerical_view
        if (view.rtol != control.unchanged_rtol or view.atol != control.unchanged_atol
                or view.electrode_points != control.unchanged_electrode_points
                or view.particle_points != control.unchanged_particle_points):
            raise ValueError("internal-step control also changes mesh or tolerances")
    if baseline_request is not None:
        from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as base, segmented_science as ss
        if (type(baseline_request) is not base.SegmentRequest
                or baseline_request.identity != control.baseline_native_request
                or _primitive(json.loads(baseline_request.primitive_json)["solver"]) != control.baseline_solver_json
                or baseline_request.ordinal != 1 or baseline_request.kind != "charging"
                or baseline_request.identity != reference.methods[0].window.result.evidence.trace.segments[0].request):
            raise ValueError("internal-step baseline substitutes its authentic first request/options")
        ss.authenticate_payloads(reference.methods[0].window.result.evidence.native_receipt, (baseline_request,))


def _primitive(value):
    return canonical_json_bytes(passive._freeze(value)).decode()


@dataclass(frozen=True, slots=True)
class ActualInternalStepAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/actual-internal-step-assignment"
    assignment_id: str
    control: InternalStepControl
    native_configuration: ObjectIdentity
    baseline_constructor_json: str
    actual_constructor_json: str
    actual_solver_json: str
    assignment_kind: str = "ACTUAL_SOLVER_CONSTRUCTOR_AND_RETURNED_OPTIONS;NOT_CONVERGENCE_EVIDENCE"

    def __post_init__(self):
        validate_stable_id(self.assignment_id)
        self.control.__post_init__()
        base, selected, actual = (json.loads(value) for value in (
            self.baseline_constructor_json, self.actual_constructor_json, self.actual_solver_json))
        expected = dict(base)
        expected["options"] = dict(base["options"], dt_max={"binary64": float(self.control.maximum_internal_step_s).hex()})
        expected_actual = json.loads(self.control.baseline_solver_json)
        expected_actual["options"]["dt_max"] = {"binary64": float(self.control.maximum_internal_step_s).hex()}
        if (type(self.control) is not InternalStepControl or type(self.native_configuration) is not ObjectIdentity
                or self.native_configuration.object_schema != "empirical-lawhood/battery-segmented/native-config"
                or base["options"]["dt_max"] != {"binary64": 0.0.hex()} or selected != expected
                or base["rtol"] != {"binary64": float(self.control.unchanged_rtol).hex()}
                or base["atol"] != {"binary64": float(self.control.unchanged_atol).hex()}
                or actual != expected_actual or actual["type"] != "IDAKLUSolver" or actual["rtol"] != selected["rtol"]
                or actual["atol"] != selected["atol"]
                or any(actual["options"].get(key) != value for key, value in selected["options"].items())
                or self.assignment_kind != "ACTUAL_SOLVER_CONSTRUCTOR_AND_RETURNED_OPTIONS;NOT_CONVERGENCE_EVIDENCE"):
            raise ValueError("actual internal-step assignment changes additional solver operands or omits actual options")


def require_assignment(control, assignment, window):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as ss
    assignment.__post_init__()
    if (type(assignment) is not ActualInternalStepAssignment or assignment.control != control
            or assignment.native_configuration != ct.identity(window.result.evidence.trace.config, "config_id")
            or not {control.identity, control.original_negative_readout, control.baseline_native_request}.issubset(window.result.native_definition.sources)):
        raise ValueError("controlled assessment loses its actual native definition/options recipe")
    ss.authenticate_payloads(window.result.evidence.native_receipt, (control, assignment))


@dataclass(frozen=True, slots=True)
class InternalStepReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/internal-step-readout"
    readout_id: str
    control: InternalStepControl
    original_readout: ct.ObservationReadout
    actual_assignments: tuple[ActualInternalStepAssignment, ...]
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        self.control.__post_init__()
        self.original_readout.__post_init__()
        if type(self.actual_assignments) is not tuple or len(self.actual_assignments) != 3 or self.scope != SCOPE:
            raise ValueError("internal-step readout thins its complete actual method denominator")
        for assignment, method in zip(self.actual_assignments, self.original_readout.methods, strict=True):
            require_assignment(self.control, assignment, method.window)


class _ConsumerView:
    """A checked input view; full actual materialization/authority identities remain."""
    def __init__(self, original, ports, outputs=None, receipts=None):
        self.original, self.input_ports = original, ports
        self.output_ports = original.output_ports if outputs is None else outputs
        self.dependency_receipts = original.dependency_receipts if receipts is None else receipts

    def __getattr__(self, name):
        return getattr(self.original, name)


class _ReplayPort:
    """Replay only bytes just read from the same authenticated config port."""
    def __init__(self, original, payload):
        self.original, self.reader = original, io.BytesIO(payload)

    def __getattr__(self, name):
        return getattr(self.original, name)

    def read(self, size=-1):
        return self.reader.read(size)

    def close(self):
        self.reader.close()
        self.original.close()


def controlled_context(context, control, reference, baseline_request):
    """Authenticate three additional real inputs before the unchanged strict loader."""
    selected = []
    for record, identity in ((control, control.identity), (reference, ct.identity(reference, "readout_id")),
                             (baseline_request, baseline_request.identity)):
        found = tuple(port for port in context.input_ports if port.artifact_id == identity.object_id)
        if len(found) != 1:
            raise ValueError("internal-step worker omits its actual control/reference input")
        port = found[0]
        if (port.kind is not WorkerInputKind.EXTERNAL or port.payload_schema != record.SCHEMA
                or port.media_type != "application/json" or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("internal-step worker changes actual input type/access")
        payload = port.read()
        if len(payload) != port.size_bytes or decode_canonical_bytes(payload, type(record), maximum_bytes=None) != record:
            raise ValueError("internal-step worker substitutes original control/reference bytes")
        selected.append(port)
    return _ConsumerView(context, tuple(port for port in context.input_ports if port not in selected))


class _BackendView:
    def __init__(self, backend, control):
        self.backend, self.control, self.calls, self.assignment = backend, control, 0, None

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def IDAKLUSolver(self, **kwargs):
        if self.calls or kwargs.get("options", {}).get("dt_max") != 0.0:
            raise ValueError("internal-step wrapper changes the single original unrestricted solver construction")
        self.calls += 1
        baseline = _primitive(kwargs)
        selected = dict(kwargs, options=dict(kwargs["options"], dt_max=float(self.control.maximum_internal_step_s)))
        solver = self.backend.IDAKLUSolver(**selected)
        self.assignment = baseline, _primitive(selected), _primitive(solver.to_config())
        return solver


class _ControlledProgress:
    """Delegate existing custody; retain actual policy/options and their byte costs."""
    def __init__(self, progress, control):
        self.original, self.control, self.main, self.added_bytes = progress, control, None, 0

    def __getattr__(self, name):
        return getattr(self.original, name)

    def begin(self, definition, inputs=None):
        entry = self.original.begin(definition, inputs)
        if definition.operation_id == "battery.segmented-observation.initial-window":
            if self.main is not None:
                raise ValueError("internal-step wrapper entered multiple main observations")
            self.main = entry
        return entry

    def contact(self, entry):
        self.original.contact(entry)
        if entry is self.main:
            self.publish_extra("internal-step-control", self.control)

    def publish_extra(self, name, record):
        if self.main is None:
            raise ValueError("actual internal-step assignment has no entered original main")
        self.added_bytes += passive._publish(self.original, self.main, name, record).materialization.size_bytes

    def complete(self, entry, **kwargs):
        if entry is self.main:
            kwargs["cost"] = replace(kwargs["cost"], retained_bytes=kwargs["cost"].retained_bytes + D(self.added_bytes))
            kwargs["cost_scope"] = kwargs.get("cost_scope", "") + (
                "; includes added policy/assignment payload bytes; assignment publication within original native timer; "
                "pre-timer policy publication CPU/wall covered only by whole-entry costs; no nested double-counting")
        return self.original.complete(entry, **kwargs)


@contextmanager
def native_control_scope(control, reference, observation, progress=None):
    """Scoped domain hooks over unchanged native guards, capture and receivers."""
    require_control(control, reference, observation)
    original_definition, original_runtime = native.build_observation_definition, native.build_runtime
    selected_progress = None if progress is None else _ControlledProgress(progress, control)

    def definition(*args):
        # Keep construction through the original helper; no recursive hook call.
        base = original_definition(*args)
        return replace(base, subwork_id="internal-step." + control.control_id + "." + base.subwork_id,
            sources=tuple(sorted((*base.sources, control.identity, control.original_negative_readout, control.baseline_native_request), key=lambda row: row.object_id)),
            outputs=tuple(sorted((*base.outputs,
                NativeSubworkOutput("internal-step-control", InternalStepControl.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
                NativeSubworkOutput("internal-step-assignment", ActualInternalStepAssignment.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")), key=lambda row: row.output_id)))

    def runtime(config, protocol, backend):
        if selected_progress is None or config not in observation.configurations:
            raise ValueError("actual controlled runtime lacks its selected original custody/recipe")
        view = _BackendView(backend, control)
        result = original_runtime(config, protocol, view)
        if view.calls != 1 or view.assignment is None or _primitive(result[1].to_config()) != view.assignment[2]:
            raise ValueError("actual controlled runtime omits its original solver assignment")
        witness = ActualInternalStepAssignment("assignment." + control.control_id + "." + config.config_id,
            control, ct.identity(config, "config_id"), *view.assignment)
        selected_progress.publish_extra("internal-step-assignment", witness)
        return result

    native.build_observation_definition, native.build_runtime = definition, runtime
    try:
        yield selected_progress
    finally:
        native.build_observation_definition, native.build_runtime = original_definition, original_runtime


@contextmanager
def request_control_scope(assignments):
    """Check every original call as the existing stream consumers read it once."""
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
    original = stream.read_frames
    stock = {row.native_configuration: row for row in assignments}

    def frames(port):
        for frame in original(port):
            if type(frame) is stream.SegmentEvidenceFrame:
                assignment = stock.get(frame.request.configuration)
                if (assignment is None or json.loads(frame.request.primitive_json)["solver"] != json.loads(assignment.actual_solver_json)
                        or assignment.control.identity not in frame.definition.sources):
                    raise ValueError("actual segment request changes declared internal-step policy or full solver options")
            yield frame

    stream.read_frames = frames
    try:
        yield
    finally:
        stream.read_frames = original


class ControlledObservationRunner(ObservationRunner):
    """Local-only composition; original config/output bytes retain their owners."""
    def __new__(cls, operation, control, reference, baseline_request):
        return object.__new__(ControlledNativeObservationRunner if operation == "observe" else cls)

    def __init__(self, operation, control, reference, baseline_request):
        super().__init__(operation)
        self.control, self.reference, self.baseline_request = control, reference, baseline_request

    def _context(self, context):
        from . import operation_bindings as ob
        view = controlled_context(context, self.control, self.reference, self.baseline_request)
        selected = tuple(port for port in view.input_ports if port.payload_schema == ob.ObservationOperationConfig.SCHEMA)
        if len(selected) != 1:
            raise ValueError("internal-step worker loses its exact original operation config")
        port = selected[0]
        payload = port.read()
        if len(payload) != port.size_bytes:
            raise ValueError("internal-step worker loses complete original config bytes")
        config = decode_canonical_bytes(payload, ob.ObservationOperationConfig, maximum_bytes=None)
        require_control(self.control, self.reference, config.observation, self.baseline_request)
        view.input_ports = tuple(_ReplayPort(port, payload) if original is port else original for original in view.input_ports)
        return view, config

    def execute(self, context):
        try:
            from . import operation_bindings as ob, recursive_translation as rt
            view, config = self._context(context)
            indices = (config.index,) if self.operation == "assess" else (config.index, config.index + 1) if self.operation == "pair" else (0, 1, 2)
            assignments, extra = [], []
            for index in indices:
                artifact = "artifact." + context.run_id + "." + ob.node_id("observe", index) + ".assignment"
                found = tuple(port for port in view.input_ports if port.artifact_id == artifact)
                if len(found) != 1:
                    raise ValueError("controlled consumer omits its actual assignment dependency")
                selected = found[0]
                if (selected.kind is not WorkerInputKind.DEPENDENCY or selected.payload_schema != ActualInternalStepAssignment.SCHEMA
                        or selected.media_type != "application/json" or selected.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                        or selected.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                    raise ValueError("controlled consumer substitutes actual assignment type/access")
                payload = selected.read()
                if len(payload) != selected.size_bytes:
                    raise ValueError("controlled consumer loses complete actual assignment bytes")
                assignments.append(decode_canonical_bytes(payload, ActualInternalStepAssignment, maximum_bytes=None))
                extra.append(selected)
            for_extra = tuple(port for port in view.input_ports if port not in extra)
            # Only finite canonical inputs are replayed locally; full scientific
            # streams keep their original sequential, one-frame-at-a-time reader.
            cached = []
            for port in for_extra:
                if port.media_type == "application/x-ndjson":
                    cached.append(port)
                else:
                    payload = port.read()
                    if len(payload) != port.size_bytes:
                        raise ValueError("controlled consumer loses original finite input bytes")
                    cached.append(_ReplayPort(port, payload))
            outputs = tuple(port for port in view.output_ports if port.payload_schema != InternalStepReadout.SCHEMA)
            expected = {origin.rsplit(".", 1)[0] for kind, origin in rt.input_sources(config).values() if kind == "DEPENDENCY"}
            view = _ConsumerView(context, tuple(cached), outputs, tuple(receipt for receipt in context.dependency_receipts if receipt.task_id in expected))
            _, decoded, _ = _load(view, self.operation, self.manifest)
            windows = (decoded["window"],) if self.operation == "assess" else (decoded["left-window"], decoded["right-window"]) if self.operation == "pair" else tuple(decoded["method-" + str(i)].window for i in range(3))
            for assignment, window in zip(assignments, windows, strict=True):
                require_assignment(self.control, assignment, window)
            for port in view.input_ports:
                if isinstance(port, _ReplayPort):
                    port.reader.seek(0)
            with request_control_scope(tuple(assignments)):
                result = super().execute(view)
            if self.operation == "summarize":
                readout = decode_canonical_bytes(result.outputs[0].payload, ct.ObservationReadout, maximum_bytes=None)
                controlled = InternalStepReadout("readout." + self.control.control_id, self.control, readout, tuple(assignments))
                selected = tuple(port for port in context.output_ports if port.payload_schema == InternalStepReadout.SCHEMA)
                if len(selected) != 1 or selected[0].output_id != context.task_id + ".controlled-readout":
                    raise ValueError("controlled reducer omits its explicit complete scientific recipe output")
                result = RunnerResult(tuple(sorted((*result.outputs, TaskOutputPayload(selected[0].output_id, controlled.canonical_bytes())), key=lambda row: row.output_id)), result.checks)
            return result
        finally:
            for port in context.input_ports:
                port.close()


class ControlledNativeObservationRunner(ControlledObservationRunner):
    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        try:
            view, config = self._context(context)
            from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
            selected = tuple(port for port in view.output_ports if port.payload_schema == ActualInternalStepAssignment.SCHEMA)
            if (len(selected) != 1 or selected[0].output_id != context.task_id + ".assignment"
                    or selected[0].profile is not ArtifactProfile.CANONICAL_JSON or selected[0].media_type != "application/json"):
                raise ValueError("controlled native worker omits its actual ordinary assignment output")
            view.output_ports = tuple(port for port in view.output_ports if port is not selected[0])
            with native_control_scope(self.control, self.reference, config.observation, native_subwork) as selected:
                definition = native.build_observation_definition(config.observation, config.index, config.protocols[config.index], config.provenance,
                    selected, config.declarations[config.index], context.input_materialization_ids)
                checks = NativeObservationRunner.execute_streaming_with_native_subwork(self, view, selected, emitter, progress)
                inspection = native_subwork.recover(definition)
                if inspection is None:
                    raise ValueError("controlled native assignment lacks its actual completed custody")
                assignment = stream.completed_record(native_subwork, definition, inspection, "internal-step-assignment", ActualInternalStepAssignment)
                if assignment.control != self.control:
                    raise ValueError("completed actual solver assignment substitutes the selected policy")
                stream.emit_record(emitter, context.task_id + ".assignment", assignment)
                return checks
        finally:
            for port in context.input_ports:
                port.close()
