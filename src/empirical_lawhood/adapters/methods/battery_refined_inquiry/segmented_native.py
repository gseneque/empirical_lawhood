# SPDX-License-Identifier: MPL-2.0
"""Changed source-derived, bounded-history native method through shared custody.

Each actual segment return is published before interpreting its arrays. Full
native state/derivative blocks are durable outputs, never thinned or accumulated
in the receiver trace. Source-derived electrode operands are not observations
of any native eSOH solve. This producer supplies no scientific assessment.
"""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
from decimal import Decimal
from functools import wraps
from hashlib import sha256
from itertools import chain
import math
import os
from pathlib import Path
import resource
import time
from typing import ClassVar
import warnings

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import native as original
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquiryDelivery, CONTROL_RULE, REQUIRED_EVENT_NAMES, SOURCE_VERSION,
    TARGET_EVENT, TIER_EVENT, TIER_TEMPERATURE,
)
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, validate_sha256, validate_stable_id,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkInspection, NativeSubworkOutput,
    NativeSubworkRoster,
)
from . import preparation_contracts as pc
from . import prepared_native as passive
from .segmented_contracts import (
    ActualSourceAssignment, SegmentedNativeConfig, SegmentedTrace,
    SegmentSummary, SegmentTransition,
)
from .source_derived_preparation import require_assessed_source_roots

D = Decimal


def _identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def _finite_hex(value):
    observed = float(value)
    if not math.isfinite(observed):
        raise ValueError("full native segment contains a nonfinite binary64 value")
    return observed.hex()


def _validate_hex(value):
    if type(value) is not str:
        raise ValueError("full native segment requires exact binary64 strings")
    if _finite_hex(float.fromhex(value)) != value:
        raise ValueError("full native segment changes its exact binary64 representation")


@dataclass(frozen=True, slots=True)
class RawReturnedArray(CanonicalRecord):
    """Actual array representation before numerical/dimension interpretation.

    C order defines element order only. The original dtype and every element's
    bytes, including signed zero and nonfinite IEEE payload bits, are preserved.
    An unexpected object dtype retains its raw memory representation and is
    never treated as a portable numerical state by the later interpreter.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/raw-returned-array"
    dtype: str
    shape: tuple[int, ...]
    itemsize: int
    bytes_hex: str
    order: str = "C"

    def __post_init__(self):
        if not self.dtype or self.order != "C" or type(self.itemsize) is not int or self.itemsize < 1:
            raise ValueError("raw native array omits its original representation")
        count = 1
        for size in self.shape:
            if type(size) is not int or size < 0:
                raise ValueError("raw native array changes its actual dimensions")
            count *= size
        if (type(self.bytes_hex) is not str or len(self.bytes_hex) != count * self.itemsize * 2
                or any(value not in "0123456789abcdef" for value in self.bytes_hex)):
            raise ValueError("raw native array changes its complete original byte census")


@dataclass(frozen=True, slots=True)
class RawReturnedSegment(CanonicalRecord):
    """Complete separate original arrays, even when interpretation must fail."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/raw-returned-segment"
    raw_id: str
    protocol: ObjectIdentity
    request: ObjectIdentity
    returned: ObjectIdentity
    present_attributes: tuple[str, ...]
    clock_blocks: tuple[RawReturnedArray, ...] | None
    state_blocks: tuple[RawReturnedArray, ...] | None
    derivative_blocks: tuple[RawReturnedArray, ...] | None

    def __post_init__(self):
        validate_stable_id(self.raw_id)
        if (self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.request.object_schema != SegmentRequest.SCHEMA
                or self.returned.object_schema != SegmentReturn.SCHEMA):
            raise ValueError("raw native return changes its actual precontact/return lineage")
        if self.present_attributes != tuple(sorted(set(self.present_attributes))) or set(self.present_attributes) - {"all_ts", "all_ys", "all_yps"}:
            raise ValueError("raw native return changes its actual attribute availability")
        for name, blocks in (("all_ts", self.clock_blocks), ("all_ys", self.state_blocks), ("all_yps", self.derivative_blocks)):
            if name not in self.present_attributes and blocks is not None:
                raise ValueError("raw native return invents an absent array attribute")
            if blocks is not None and any(type(row) is not RawReturnedArray for row in blocks):
                raise ValueError("raw native return substitutes original array blocks")


def observe_raw_return(solution, protocol, request, returned):
    """Publish caller-visible numerical bytes without scientific guards."""
    import numpy as np

    def arrays(value):
        if value is None:
            return None
        observed = []
        for block in value:
            array = np.asarray(block)
            observed.append(RawReturnedArray(array.dtype.str, tuple(array.shape), array.dtype.itemsize,
                array.tobytes(order="C").hex()))
        return tuple(observed)

    present = tuple(sorted(name for name in ("all_ts", "all_ys", "all_yps") if hasattr(solution, name)))
    return RawReturnedSegment(request.request_id + ".raw-return", _identity(protocol, "protocol_id"),
        request.identity, _identity(returned, "return_id"), present,
        *(arrays(getattr(solution, name, None)) for name in ("all_ts", "all_ys", "all_yps")))


@dataclass(frozen=True, slots=True)
class FullStateBlock(CanonicalRecord):
    """One original native clock/state block in row-major array order."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-block"
    clock_binary64: tuple[str, ...]
    state_rows: int
    state_binary64: tuple[str, ...]
    derivative_binary64: tuple[str, ...] | None

    def __post_init__(self):
        if type(self.state_rows) is not int or self.state_rows < 1 or not self.clock_binary64:
            raise ValueError("full native block omits its original dimensions/clocks")
        if len(self.state_binary64) != self.state_rows * len(self.clock_binary64):
            raise ValueError("full native block omits state components or native knots")
        if self.derivative_binary64 is not None and len(self.derivative_binary64) != len(self.state_binary64):
            raise ValueError("full native derivative changes its original state/clock denominator")
        for value in chain(self.clock_binary64, self.state_binary64, self.derivative_binary64 or ()):
            _validate_hex(value)
        clocks = tuple(float.fromhex(value) for value in self.clock_binary64)
        if any(a >= b for a, b in zip(clocks, clocks[1:])):
            raise ValueError("full native block changes its strict original clock order")


@dataclass(frozen=True, slots=True)
class FullStateSegment(CanonicalRecord):
    """Complete actual arrays, published and released before the next contact."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/full-state-segment"
    segment_id: str
    protocol: ObjectIdentity
    layout: ObjectIdentity
    request: ObjectIdentity
    returned: ObjectIdentity
    raw_return: ObjectIdentity
    blocks: tuple[FullStateBlock, ...]
    returned_model_expression_sha256: tuple[str, ...]
    returned_inputs_json: str
    actual_termination: str

    def __post_init__(self):
        validate_stable_id(self.segment_id)
        if (self.protocol.object_schema != pc.PreparationProtocol.SCHEMA
                or self.layout.object_schema != pc.ProcessedInitialStateLayout.SCHEMA
                or self.request.object_schema != SegmentRequest.SCHEMA
                or self.returned.object_schema != SegmentReturn.SCHEMA
                or self.raw_return.object_schema != RawReturnedSegment.SCHEMA):
            raise ValueError("full native segment changes its actual source/custody joins")
        if not self.blocks or any(type(row) is not FullStateBlock for row in self.blocks):
            raise ValueError("full native segment omits actual state blocks")
        if len({row.state_rows for row in self.blocks}) != 1:
            raise ValueError("full native segment changes its owning row count")
        if len(self.returned_model_expression_sha256) != len(self.blocks):
            raise ValueError("full native segment omits its actual model block census")
        for digest in self.returned_model_expression_sha256:
            validate_sha256(digest)
        passive._validate_primitive_json(self.returned_inputs_json)
        if not self.actual_termination:
            raise ValueError("full native segment omits its original termination")


@dataclass(frozen=True, slots=True)
class SegmentRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/native-request"
    request_id: str
    configuration: ObjectIdentity
    protocol: ObjectIdentity
    ordinal: int
    kind: str
    primitive_json: str

    def __post_init__(self):
        validate_stable_id(self.request_id)
        if (self.configuration.object_schema != "empirical-lawhood/battery-segmented/native-config"
                or self.protocol.object_schema != pc.PreparationProtocol.SCHEMA):
            raise ValueError("segmented request changes its new method configuration/protocol")
        if type(self.ordinal) is not int or self.ordinal < 1 or self.kind not in {"charging", "end-of-chain"}:
            raise ValueError("segmented request changes its actual native effect slot")
        passive._validate_primitive_json(self.primitive_json)

    @property
    def identity(self):
        return _identity(self, "request_id")


@dataclass(frozen=True, slots=True)
class SegmentReturn(CanonicalRecord):
    """Immediate actual-return witness, independent of later array extraction."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/native-return"
    return_id: str
    request: ObjectIdentity
    disposition: str
    error_type: str | None
    error_message: str | None
    primitive_json: str

    def __post_init__(self):
        validate_stable_id(self.return_id)
        if self.request.object_schema != SegmentRequest.SCHEMA:
            raise ValueError("segmented return changes its exact entered request")
        if (self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
                or (self.disposition == "TECHNICAL_FAILURE") != (self.error_type is not None and self.error_message is not None)
                or self.disposition == "RETURNED" and (self.error_type is not None or self.error_message is not None)):
            raise ValueError("segmented return loses its actual error/return distinction")
        passive._validate_primitive_json(self.primitive_json)


def observe_full_segment(solution, protocol, layout, request, returned, raw_return):
    """Read all actual returned blocks; no concatenation or cadence reduction."""
    import numpy as np
    states, clocks = getattr(solution, "all_ys", None), getattr(solution, "all_ts", None)
    if getattr(solution, "variables_returned", False) or not states or not clocks or len(states) != len(clocks):
        raise ValueError("segmented method requires every actual full-state clock block")
    if len(solution.all_models) != len(states) or len(solution.all_inputs) != len(states):
        raise ValueError("actual native model/input block census differs from full states")
    derivatives = getattr(solution, "all_yps", None)
    derivatives = None if derivatives is None or not len(derivatives) else derivatives
    if derivatives is not None and len(derivatives) != len(states):
        raise ValueError("actual derivative block census differs from full states")
    blocks = []
    for index, (times, values) in enumerate(zip(clocks, states, strict=True)):
        for array in (times, values, *((derivatives[index],) if derivatives is not None else ())):
            dtype = np.asarray(array).dtype
            if dtype.kind != "f" or dtype.itemsize != 8:
                raise ValueError("actual native array differs from selected binary64 source representation")
        times, values = np.asarray(times, dtype=float).reshape(-1), np.asarray(values, dtype=float)
        if values.shape != (layout.differential_count + layout.algebraic_count, len(times)):
            raise ValueError("actual native block omits full RHS/algebraic rows or knots")
        derivative_bits = None
        if derivatives is not None:
            derivative = np.asarray(derivatives[index], dtype=float)
            if derivative.shape != values.shape:
                raise ValueError("actual native derivative omits full RHS/algebraic rows or knots")
            derivative_bits = tuple(_finite_hex(value) for value in derivative.reshape(-1))
        blocks.append(FullStateBlock(tuple(_finite_hex(value) for value in times), values.shape[0],
            tuple(_finite_hex(value) for value in values.reshape(-1)), derivative_bits))
    return FullStateSegment(request.request_id + ".full-state", _identity(protocol, "protocol_id"),
        _identity(layout, "layout_id"), request.identity, _identity(returned, "return_id"), _identity(raw_return, "raw_id"), tuple(blocks),
        tuple(passive._model_digest(model, ("rhs", "algebraic")) for model in solution.all_models),
        canonical_json_bytes(passive._freeze(solution.all_inputs)).decode(), str(solution.termination))


def bounded_hybrid_segments(config, execute):
    """Continue at declared windows/tier roots, preserving native failures.

    The callback returns a compact summary and a detached complete terminal
    carrier. No count or wall-clock cutoff truncates the scientific horizon.
    """
    native, method = config.native, config.method
    epsilon = native.localization_epsilon_k
    regime = "HIGH" if native.initial_temperature_k >= TIER_TEMPERATURE + epsilon else "LOW"
    start, previous, ordinal = D(0), None, 0
    pending = None
    while start < method.maximum_model_clock_s:
        ordinal += 1
        horizon = min(method.maximum_segment_horizon_s, method.maximum_model_clock_s - start)
        summary, previous = execute(ordinal, regime, start, horizon, previous, pending)
        yield summary
        if summary.disposition == "TECHNICAL_FAILURE":
            return
        if not summary.native_times_s or summary.native_times_s[-1] <= start:
            raise ValueError("native segment returned without advancing its requested global clock")
        end = summary.native_times_s[-1]
        expected_end = D(str(float(start) + float(horizon)))
        if end > expected_end:
            raise ValueError("native segment exceeds its frozen scientific window")
        if TIER_EVENT in summary.termination:
            root_temperature = summary.end_receivers[2]
            threshold = original.hybrid_inputs(native, regime)[original.TIER_THRESHOLD_INPUT]
            if root_temperature <= TIER_TEMPERATURE or abs(root_temperature - threshold) > epsilon / D("1000000"):
                raise ValueError("actual tier root violates its frozen one-sided localization allowance")
            pending = summary, threshold
            regime = "HIGH" if regime == "LOW" else "LOW"
        elif summary.termination == "final time":
            pending = None
            if end != expected_end:
                raise ValueError("native final-time return omits its frozen window endpoint")
        else:
            return
        start = end


@contextmanager
def observe_requested_initialization(backend, model, protocol, layout, request, receive):
    """Capture actual y0 before consistency, including continuation reinitialization."""
    owner = backend.BaseSolver
    name = "_set_consistent_initialization"
    local = name in owner.__dict__
    original_method = getattr(owner, name)

    @wraps(original_method)
    def observed(solver, built, clock, inputs):
        if built is model:
            if len(built.y0_list) != 1:
                raise ValueError("selected segmented initializer changes its actual input denominator")
            state = passive.observe_state(built.y0_list[0], clock, "requested-initial", protocol, layout, (request.identity,))
            receive(replace(state, observation_id=request.request_id + ".requested-initial"))
        return original_method(solver, built, clock, inputs)

    setattr(owner, name, observed)
    try:
        yield
    finally:
        if local:
            setattr(owner, name, original_method)
        else:
            delattr(owner, name)


def detached_continuation(solution, backend):
    """Explicit DERIVED continuation metadata; original event stays durable."""
    import numpy as np
    if getattr(solution, "variables_returned", False) or not solution.all_ys or not solution.all_ts:
        raise ValueError("segmented continuation requires its complete returned state")
    model = solution.all_models[-1]
    states = np.array(solution.all_ys[-1][:, -1:], dtype=float, copy=True)
    clock = np.array(solution.all_ts[-1][-1:], dtype=float, copy=True)
    if states.shape != (model.len_rhs_and_alg, 1) or clock.shape != (1,):
        raise ValueError("segmented continuation changes its full RHS/algebraic state")
    derivatives = None
    returned = getattr(solution, "all_yps", None)
    if returned is not None and len(returned):
        derivatives = np.array(returned[-1][:, -1:], dtype=float, copy=True)
        if derivatives.shape != states.shape:
            raise ValueError("segmented continuation changes its full returned derivative")
    if getattr(solution, "_all_sensitivities", {}):
        raise ValueError("selected segmented method did not request native sensitivities")
    # Native BaseSolver.step only advances final-time carriers. This is an
    # explicitly changed method, with original event bytes retained separately.
    return backend.Solution(clock, states, model, deepcopy(solution.all_inputs[-1]),
        termination="final time", all_yps=derivatives, options=deepcopy(solution.user_options))


def assign_source_parameters(parameters, config, protocol):
    """Use already independently assessed DERIVED binary64 operands, no solve."""
    preparation = require_assessed_source_roots(config.preparation, config.preparation_assessment)
    names = ("Initial concentration in negative electrode [mol.m-3]",
             "Initial concentration in positive electrode [mol.m-3]")
    before = tuple(_finite_hex(parameters[name]) for name in names)
    expected_before = tuple(_finite_hex(value) for value in (
        preparation.pre_soc_negative_concentration, preparation.pre_soc_positive_concentration))
    if before != expected_before:
        raise ValueError("actual source stock differs before DERIVED assignment")
    assigned = (preparation.assigned_negative_concentration, preparation.assigned_positive_concentration)
    parameters.update(dict(zip(names, (float(value) for value in assigned), strict=True)))
    observed = tuple(_finite_hex(parameters[name]) for name in names)
    if observed != tuple(_finite_hex(value) for value in assigned):
        raise ValueError("native parameter owner substituted DERIVED electrode operands")
    values = {"assigned_negative_concentration": passive._decimal(parameters[names[0]]),
        "assigned_positive_concentration": passive._decimal(parameters[names[1]]),
        "pre_soc_negative_concentration": passive._decimal(float.fromhex(before[0])),
        "pre_soc_positive_concentration": passive._decimal(float.fromhex(before[1]))}
    return ActualSourceAssignment("assignment." + config.config_id, _identity(config, "config_id"),
        _identity(protocol, "protocol_id"), _identity(preparation, "preparation_id"), **values,
        binary64_operands=tuple((name, float(value).hex()) for name, value in sorted(values.items())))


def build_runtime(config, protocol, backend):
    """Build the genuinely changed model with explicit source assignments."""
    native, method = config.native, config.method
    if backend.__version__ != SOURCE_VERSION:
        raise ValueError("installed PyBaMM source version differs")
    if (backend.settings.min_max_mode != "exact" or backend.settings.heaviside_smoothing != "exact"):
        raise ValueError("native exact control/tier semantics differ")

    def control(variables):
        voltage_slack = (backend.Scalar(4.2) - variables["Voltage [V]"]) / backend.Scalar(1)
        current_slack = (variables["Current [A]"] + backend.InputParameter(original.ACTIVE_CURRENT_INPUT)) / backend.Scalar(1)
        return backend.minimum(voltage_slack, current_slack)

    options = {"thermal": "lumped", "cell geometry": "arbitrary", "dimensionality": 0,
        "surface temperature": "ambient", "contact resistance": "false",
        "use lumped thermal capacity": "false", "operating mode": control}
    constructor = backend.lithium_ion.DFN if "dfn" in native.model_view else backend.lithium_ion.SPMe
    model = constructor(options=options)
    temperature = model.variables["Volume-averaged cell temperature [K]"]
    voltage, current = model.variables["Voltage [V]"], model.variables["Current [A]"]
    capacity = model.variables["Discharge capacity [A.h]"]
    model.events = [event for event in model.events if event.name != "Maximum voltage [V]"]
    for name, expression in (
        (TARGET_EVENT, backend.Scalar(float(method.target_charge_ah)) + capacity),
        (REQUIRED_EVENT_NAMES[1], backend.Scalar(318.15) - temperature),
        (REQUIRED_EVENT_NAMES[2], temperature - backend.Scalar(273.15)),
        (REQUIRED_EVENT_NAMES[3], backend.Scalar(4.201) - voltage),
        (REQUIRED_EVENT_NAMES[4], -current - backend.Scalar(.05)),
        (TIER_EVENT, backend.InputParameter(original.TIER_DIRECTION_INPUT)
            * (temperature - backend.InputParameter(original.TIER_THRESHOLD_INPUT))),
    ):
        model.events.append(backend.Event(name, expression, backend.EventType.TERMINATION))
    event_names = tuple(sorted(event.name for event in model.events
        if event.event_type is backend.EventType.TERMINATION))
    parameters = backend.ParameterValues(config.preparation.parameter_source)
    assignment = assign_source_parameters(parameters, config, protocol)
    parameters.update({"Upper voltage cut-off [V]": 4.2, "Lower voltage cut-off [V]": 2.5,
        "Open-circuit voltage at 100% SOC [V]": 4.2, "Open-circuit voltage at 0% SOC [V]": 2.5,
        "Initial temperature [K]": float(native.initial_temperature_k),
        "Ambient temperature [K]": float(native.chamber_temperature_k)})
    settings = native.numerical_view
    solver = backend.IDAKLUSolver(rtol=float(settings.rtol), atol=float(settings.atol), on_failure="warn",
        options={"max_num_steps": -1, "dt_max": 0.0, "num_steps_no_progress": 0,
            "num_threads": 1, "num_solvers": 1})
    mesh = dict(model.default_submesh_types)
    for particle in ("negative particle", "positive particle"):
        mesh[particle] = backend.MeshGenerator(backend.Exponential1DSubMesh, {"side": "right"})
    points = {name: settings.particle_points if name.startswith("r_") else settings.electrode_points
        for name in ("x_n", "x_s", "x_p", "r_n", "r_p")}
    simulation = backend.Simulation(model, parameter_values=parameters, solver=solver,
        submesh_types=mesh, var_pts=points)
    initial_regime = "HIGH" if native.initial_temperature_k >= TIER_TEMPERATURE + native.localization_epsilon_k else "LOW"
    # An explicit None prevents Simulation from invoking the native eSOH route.
    simulation.build(initial_soc=None, inputs={name: float(value)
        for name, value in original.hybrid_inputs(native, initial_regime).items()})
    built = simulation.built_model
    delivery = BatteryInquiryDelivery(CONTROL_RULE, D("4.2"), passive._decimal(parameters["Upper voltage cut-off [V]"]),
        native.chamber_temperature_k, passive._decimal(parameters["Ambient temperature [K]"]), D(0), None,
        str(control(model.variables)), str(next(expression for variable, expression in built.algebraic.items()
            if variable.name == "Current variable [A]")), str(built.get_processed_variable("Current [A]")),
        str(built.get_processed_variable("Voltage [V]")), str(built.get_processed_variable("Ambient temperature [K]")),
        None, None, None)
    processed_events = tuple(str(next(event.expression for event in built.events if event.name == name)) for name in event_names)
    return built, solver, delivery, assignment, event_names, processed_events


def _output(name, record_type):
    return NativeSubworkOutput(name, record_type.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")


def segment_outputs():
    return tuple(sorted((
        _output("native.request.next", SegmentRequest), _output("native.return", SegmentReturn),
        _output("raw-return", RawReturnedSegment), _output("full-state", FullStateSegment),
        *(_output(name, pc.StateObservation) for name in (
            "requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")),
    ), key=lambda row: row.output_id))


class _SegmentChain:
    """Original creator freezes each actual successor before completing carrier."""
    def __init__(self, progress, forecast, protocol, inputs):
        self.progress, self.forecast, self.protocol, self.base_inputs = progress, forecast, protocol, inputs
        self.current, self.request, self.prepared = forecast, None, None
        self.ordinal, self.retained_bytes, self.current_bytes = 0, 0, 0
        self.last_cost = None
        self.preparation = None

    def prepare(self, assignment, layout, primitive, *, extra_records=None):
        """Close actual built context before the first charging solver call.

        This records existing observations; it performs no initializer, solve
        or scientific assessment. The first request has a completed publisher
        even when the enclosing forecast never obtains a completion receipt.
        """
        if self.preparation is not None or self.ordinal:
            raise ValueError("segmented preparation checkpoint cannot be repeated")
        if (type(assignment) is not ActualSourceAssignment or type(layout) is not pc.ProcessedInitialStateLayout
                or not layout.observed_from_built_model
                or assignment.configuration != self.forecast.definition.configuration
                or assignment.protocol != _identity(self.protocol, "protocol_id")
                or layout.protocol != _identity(self.protocol, "protocol_id")):
            raise ValueError("segmented checkpoint requires actual assigned source and processed layout")
        definition = build_preparation_checkpoint_definition(self.forecast.definition)
        request = SegmentRequest(self.forecast.definition.subwork_id + ".request.1",
            self.forecast.definition.configuration, _identity(self.protocol, "protocol_id"), 1,
            "charging", canonical_json_bytes(passive._freeze(primitive)).decode())
        extra = getattr(self.progress, "preparation_records", lambda: ())() if extra_records is None else extra_records
        records = {"protocol": self.protocol, "source-assignment": assignment, "layout": layout,
            "native.request.first": request}
        for name, record in extra:
            if name not in {"forecast-step-policy", "forecast-step-assignment", "step-assignment"} or name in records:
                raise ValueError("segmented checkpoint substitutes its selected actual context")
            records[name] = record
        if set(records) != {row.output_id for row in definition.outputs}:
            raise ValueError("segmented checkpoint omits selected actual context")
        for output in definition.outputs:
            record = records[output.output_id]
            record.__post_init__()
            if record.SCHEMA != output.payload_schema:
                raise ValueError("segmented checkpoint changes actual context schema")
        wall, cpu = time.monotonic(), time.process_time()
        try:
            self.progress.freeze_roster(NativeSubworkRoster(definition.roster_id, definition.parent_contact,
                (definition.identity,), self.forecast.definition.identity), self.forecast, definitions=(definition,))
            entry = self.progress.begin(definition, self.base_inputs)
            self.progress.contact(entry)
            manifests = tuple(self._publish(entry, name, record) for name, record in sorted(records.items()))
            # Preserve the forecast's declared original first-request output.
            # The first segment consumes the completed checkpoint copy instead.
            self._publish(self.forecast, "native.request.first", request)
            inspection = self.progress.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                cost=InquiryCost(passive._decimal(time.process_time() - cpu),
                    passive._decimal(time.monotonic() - wall), D(sum(row.materialization.size_bytes for row in manifests))),
                cost_scope="actual context capture and first-request publication; no additional native calculation; included in forecast, do not sum nested costs; checkpoint payload bytes only",
                consumed_streams=definition.streams,
                peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024)
            if inspection.receipt is None or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED:
                raise ValueError("actual preparation checkpoint lacks its completed receipt")
        except Exception as error:
            raise _CustodyFailure("actual preparation checkpoint custody failed; no first solve") from error
        self.preparation = inspection

    def _publish(self, entry, name, record):
        try:
            manifest = passive._publish(self.progress, entry, name, record)
        except Exception as error:
            raise _CustodyFailure("actual segment custody publication failed") from error
        self.retained_bytes += manifest.materialization.size_bytes
        return manifest

    def publish(self, name, record):
        manifest = self._publish(self.current, name, record)
        self.current_bytes += manifest.materialization.size_bytes
        return manifest

    def _schedule(self, primitive, terminal_manifest=None):
        ordinal = self.ordinal + 1
        if self.preparation is None:
            raise _CustodyFailure("actual first solver request has no completed preparation checkpoint")
        if self.ordinal == 0:
            from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream
            request = evidence_stream.completed_record(self.progress, self.preparation.definition,
                self.preparation, "native.request.first", SegmentRequest)
            manifest = evidence_stream._manifest(self.preparation, "native.request.first")
            if request.primitive_json != canonical_json_bytes(passive._freeze(primitive)).decode():
                raise ValueError("first segment substitutes its completed checkpoint request")
        else:
            request = SegmentRequest(self.forecast.definition.subwork_id + ".request." + str(ordinal),
                self.forecast.definition.configuration, _identity(self.protocol, "protocol_id"), ordinal,
                "charging", canonical_json_bytes(passive._freeze(primitive)).decode())
            manifest = self._publish(self.current, "native.request.next", request)
            self.current_bytes += manifest.materialization.size_bytes
        additional = (manifest,) if terminal_manifest is None else (manifest, terminal_manifest)
        context = self.preparation.outputs
        definition = replace(self.forecast.definition,
            subwork_id=self.forecast.definition.subwork_id + ".segment." + str(ordinal),
            operation_id="battery.segmented-native.segment", configuration=request.identity,
            input_materialization_ids=tuple(sorted(set((*self.forecast.definition.input_materialization_ids,
                *(row.materialization.materialization_id for row in (*context, *additional)))))),
            outputs=segment_outputs(), roster_id="conditional.battery.segment." + str(ordinal))
        selected_inputs = None
        if self.base_inputs is not None:
            selected = {row.materialization.materialization_id: row for row in (*self.base_inputs, *context, *additional)}
            if any(selected[row.materialization.materialization_id] != row for row in (*self.base_inputs, *context, *additional)):
                raise ValueError("segmented checkpoint substitutes a unique original materialization")
            selected_inputs = tuple(selected[key] for key in sorted(selected))
        try:
            self.progress.freeze_roster(NativeSubworkRoster(definition.roster_id, definition.parent_contact,
                (definition.identity,), self.current.definition.identity), self.current, definitions=(definition,))
            entry = self.progress.begin(definition, selected_inputs)
        except Exception as error:
            raise _CustodyFailure("actual successor roster/BEGIN failed") from error
        return request, entry

    def enter(self, primitive):
        if self.prepared is None:
            if self.ordinal:
                raise ValueError("segmented effect cannot resume a closed or uncertain carrier")
            self.prepared = self._schedule(primitive)
        request, entry = self.prepared
        if request.primitive_json != canonical_json_bytes(passive._freeze(primitive)).decode():
            raise ValueError("segmented effect substitutes its already frozen actual operands")
        self.prepared = None
        try:
            self.progress.contact(entry)
        except Exception as error:
            raise _CustodyFailure("actual segment contact custody failed") from error
        self.current, self.request, self.ordinal, self.current_bytes = entry, request, request.ordinal, 0
        return request

    def returned(self, request, *, error=None):
        # The backend's return itself is known before any property/array read.
        record = SegmentReturn(request.request_id + ".return", request.identity,
            "RETURNED" if error is None else "TECHNICAL_FAILURE",
            None if error is None else type(error).__name__, None if error is None else str(error),
            canonical_json_bytes({"backend_returned": error is None}).decode())
        self.publish("native.return", record)
        return record

    def close(self, *, next_primitive, terminal_manifest, failure, cpu_start, wall_start):
        current = self.current
        if next_primitive is not None:
            self.prepared = self._schedule(next_primitive, terminal_manifest)
        else:
            terminal = SegmentRequest(self.request.request_id + ".end", self.request.configuration,
                self.request.protocol, self.ordinal, "end-of-chain", canonical_json_bytes({"actual_segment_calls": self.ordinal}).decode())
            self.publish("native.request.next", terminal)
        self.last_cost = InquiryCost(passive._decimal(time.process_time() - cpu_start),
            passive._decimal(time.monotonic() - wall_start), D(self.current_bytes))
        try:
            inspection = self.progress.complete(current,
                operational_status=OperationalStatus.SUCCEEDED if failure is None else OperationalStatus.FAILED,
                cost=self.last_cost, cost_scope="actual native segment and full output custody; included in forecast, do not sum twice; payload bytes exclude manifests/receipts/control records",
                consumed_streams=current.definition.streams,
                peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024,
                reason_codes=() if failure is None else ("actual-segment-technical-failure",))
        except Exception as error:
            raise _CustodyFailure("actual segment completion custody failed") from error
        if inspection.receipt is None:
            raise ValueError("completed segment has no actual producing receipt")
        return inspection


class _CustodyFailure(RuntimeError):
    """A failed custody operation cannot be converted into a known native return."""


def forecast_outputs():
    return tuple(sorted((
        _output("trace", SegmentedTrace), _output("protocol", pc.PreparationProtocol),
        _output("source-assignment", ActualSourceAssignment),
        _output("layout", pc.ProcessedInitialStateLayout),
        *(_output(name, pc.StateObservation) for name in (
            "requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")),
        _output("native.request.first", SegmentRequest),
    ), key=lambda row: row.output_id))


def build_preparation_checkpoint_definition(forecast_definition):
    """Existing typed context only; no new scientific outcome or authority."""
    if type(forecast_definition) is not NativeSubworkDefinition:
        raise ValueError("preparation checkpoint requires its exact native forecast definition")
    required = {"protocol", "source-assignment", "layout", "native.request.first"}
    operations = {"battery.segmented-native.forecast": "forecast-step-assignment",
        "battery.development.restart-control": "step-assignment",
        "battery.segmented-observation.initial-window": None}
    if forecast_definition.operation_id not in operations:
        raise ValueError("preparation checkpoint changes declared forecast context")
    assignment = operations[forecast_definition.operation_id]
    controlled = set() if assignment is None else {"forecast-step-policy", assignment}
    declared = {row.output_id for row in forecast_definition.outputs}
    if (not required.issubset(declared) or declared & controlled not in (set(), controlled)
            or assignment is None and declared & {"forecast-step-policy", "forecast-step-assignment", "step-assignment"}):
        raise ValueError("preparation checkpoint changes declared forecast context")
    names = required | (declared & controlled)
    return replace(forecast_definition, subwork_id=forecast_definition.subwork_id + ".preparation",
        operation_id="battery.segmented-native.preparation",
        outputs=tuple(row for row in forecast_definition.outputs if row.output_id in names),
        roster_id="conditional.battery.preparation." + sha256(forecast_definition.subwork_id.encode()).hexdigest())


def completed_preparation_checkpoint(progress, forecast_definition):
    """Read genuine completed context; legacy absent checkpoints stay absent."""
    definition = build_preparation_checkpoint_definition(forecast_definition)
    inspection = progress.recover(definition)
    if inspection is not None and (inspection.definition != definition or inspection.receipt is None
            or inspection.completion is None
            or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED
            or {row.output_id for row in inspection.definition.outputs} != set(inspection.completion.output_ids)
            or inspection.completion.omitted_output_ids):
        raise ValueError("actual preparation checkpoint lacks its complete successful context receipt")
    return inspection


def forecast_definition(config, protocol, provenance, parent_contact, input_materialization_ids):
    """Project the original initial effect scope without a live custody port."""
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    if (type(config) is not SegmentedNativeConfig or type(protocol) is not pc.PreparationProtocol
            or type(provenance) is not NumericalProducingProvenance
            or type(parent_contact) is not NativeEffectContact):
        raise ValueError("segmented definition requires exact prospective typed operands")
    sources = (protocol.source, provenance.identity, _identity(protocol, "protocol_id"),
        _identity(config.preparation, "preparation_id"), _identity(config.preparation_assessment, "assessment_id"),
        _identity(config.method, "method_id"))
    return NativeSubworkDefinition("forecast." + config.config_id, "battery.segmented-native.forecast",
        parent_contact, _identity(config, "config_id"),
        tuple(sorted(sources, key=lambda row: row.object_id)), provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, tuple(sorted(input_materialization_ids)), (), forecast_outputs())


def build_forecast_definition(config, protocol, provenance, native_subwork, input_materialization_ids):
    return forecast_definition(config, protocol, provenance, native_subwork.parent_contact, input_materialization_ids)


def require_installed_forecast_sources(config, protocol):
    """Check every selected installed source without importing native science."""
    from importlib import metadata, util
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    from .preparation_science import PREPARATION_SOURCE_MEMBERS

    config.__post_init__()
    protocol.__post_init__()
    if metadata.version("pybamm") != SOURCE_VERSION:
        raise ValueError("ENVIRONMENT: segmented forecast requires its exact selected PyBaMM version")
    roots = {}
    for name in ("pybamm", "scipy"):
        selected = util.find_spec(name)
        if selected is None or selected.origin is None:
            raise ValueError("ENVIRONMENT: segmented forecast lacks its installed " + name + " package")
        roots[name] = Path(selected.origin).parent
    if not set(PREPARATION_SOURCE_MEMBERS).issubset(protocol.source_members):
        raise ValueError("native preparation protocol omits exact source members")
    members = (*PREPARATION_SOURCE_MEMBERS, *config.source.source_members)
    for name, expected in members:
        root, relative = (roots["scipy"], name.removeprefix("scipy/")) if name.startswith("scipy/") else (roots["pybamm"], name)
        if bounded_file_sha256(root / relative, maximum_bytes=None)[1] != expected:
            raise ValueError("actual segmented native source pin differs: " + name)


def freeze_forecast_roster(native_subwork, definitions):
    definitions = tuple(sorted(definitions, key=lambda row: row.subwork_id))
    native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork", native_subwork.parent_contact,
        tuple(row.identity for row in definitions)), definitions=definitions)


def _identity_primitive(identity):
    return None if identity is None else {"id": identity.object_id, "schema": identity.object_schema,
        "version": identity.object_version, "fingerprint": identity.object_fingerprint}


def _request_primitive(config, layout, solver, regime, start, horizon, previous_terminal):
    return {"regime": regime, "requested_start": start, "duration": float(horizon),
        "source_computed_end": float(start) + float(horizon),
        "inputs": {name: float(value) for name, value in original.hybrid_inputs(config.native, regime).items()},
        "solver": solver.to_config(), "model_expression_sha256": layout.model_expression_sha256,
        "initial_conditions_sha256": layout.initial_conditions_sha256,
        "method": _identity_primitive(_identity(config.method, "method_id")),
        "previous_terminal": _identity_primitive(previous_terminal),
        "continuation_metadata": "NONE" if previous_terminal is None else config.method.continuation_method,
        "save": False, "initial_soc_argument": None}


def _continuation(config, regime, start, horizon, native_times, termination, end_receivers):
    if not native_times or native_times[-1] <= start:
        raise ValueError("native segment returned without advancing its requested global clock")
    end = native_times[-1]
    source_end = D(str(float(start) + float(horizon)))
    if end > source_end or end > config.method.maximum_model_clock_s:
        raise ValueError("native segment exceeds its frozen window/global scientific horizon")
    pending = None
    if TIER_EVENT in termination:
        threshold = original.hybrid_inputs(config.native, regime)[original.TIER_THRESHOLD_INPUT]
        if end_receivers[2] <= TIER_TEMPERATURE or abs(end_receivers[2] - threshold) > config.localization_epsilon_k / D("1000000"):
            raise ValueError("actual tier root violates its frozen one-sided localization allowance")
        pending = threshold
        regime = "HIGH" if regime == "LOW" else "LOW"
    elif termination == "final time":
        if end != source_end:
            raise ValueError("native final-time return omits its source-computed frozen endpoint")
    else:
        return None
    if end == config.method.maximum_model_clock_s:
        return None
    return regime, end, min(config.method.maximum_segment_horizon_s, config.method.maximum_model_clock_s - end), pending


@contextmanager
def forbid_native_esoh(backend):
    """Refuse an undeclared eSOH solve before contacting that method."""
    owner = backend.lithium_ion.ElectrodeSOHSolver
    local, original_method = "solve" in owner.__dict__, owner.solve

    def refused(*args, **kwargs):
        raise ValueError("source-derived segmented method forbids native eSOH entry")

    owner.solve = refused
    try:
        yield
    finally:
        if local:
            owner.solve = original_method
        else:
            delattr(owner, "solve")


@dataclass(frozen=True, slots=True)
class SegmentedNativeResult:
    trace: SegmentedTrace | None
    protocol: pc.PreparationProtocol
    source_assignment: ActualSourceAssignment | None
    layout: pc.ProcessedInitialStateLayout | None
    requested_initial: pc.StateObservation | None
    actual_initial: pc.StateObservation | None
    initial_derivative: pc.StateObservation | None
    actual_terminal: pc.StateObservation | None
    terminal_derivative: pc.StateObservation | None
    inspection: NativeSubworkInspection
    recovered: bool = False


def _validate_operands(config, protocol, provenance, definition, progress):
    if (type(config) is not SegmentedNativeConfig or type(protocol) is not pc.PreparationProtocol
            or type(provenance) is not NumericalProducingProvenance):
        raise ValueError("segmented acquisition requires exact prospective typed operands")
    for record in (config, protocol, provenance):
        record.__post_init__()
    expected = build_forecast_definition(config, protocol, provenance, progress, definition.input_materialization_ids)
    settings = config.native.numerical_view
    if (definition != expected or protocol.configuration != _identity(config, "config_id")
            or protocol.source != _identity(config.source, "source_id")
            or protocol.producing_provenance != provenance.identity
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or protocol.parameter_source != config.preparation.parameter_source
            or (protocol.electrode_points, protocol.particle_points) != (settings.electrode_points, settings.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k):
        raise ValueError("segmented acquisition substitutes its frozen configuration/source/protocol/output census")


def acquire_segmented(config, *, protocol, provenance, definition, native_subwork, inputs=None):
    """Fresh successor only; recovery never repeats or relabels native effects."""
    _validate_operands(config, protocol, provenance, definition, native_subwork)
    recovered = native_subwork.recover(definition)
    if recovered is not None:
        return SegmentedNativeResult(None, protocol, None, None, None, None, None, None, None, recovered, True)
    entry = native_subwork.begin(definition, inputs)
    native_subwork.contact(entry)
    wall, cpu = time.monotonic(), time.process_time()
    chain = _SegmentChain(native_subwork, entry, protocol, inputs)
    delivery = BatteryInquiryDelivery(CONTROL_RULE, D("4.2"), None, config.chamber_temperature_k,
        None, D(0), None, "", "", "", "", "", None, None, None)
    assignment = layout = None
    boundary = {name: None for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")}
    receiver_clocks, receiver_columns, regimes = [], [[] for _ in range(5)], []
    summaries, transitions = [], []
    event_names, expressions = (), ()
    error = None
    termination = "native-not-built"
    os.environ["PYBAMM_DISABLE_TELEMETRY"] = "true"
    try:
        import numpy as np
        import pybamm
        passive._validate_source_pins(pybamm, protocol)
        root = Path(pybamm.__file__).parent
        for member, expected in config.source.source_members:
            if sha256((root / member).read_bytes()).hexdigest() != expected:
                raise ValueError("actual segmented native source pin differs: " + member)
        with forbid_native_esoh(pybamm):
            built, solver, delivery, assignment, event_names, expressions = build_runtime(config, protocol, pybamm)
            layout = passive.observe_processed_layout(built, protocol)
            regime = "HIGH" if config.initial_temperature_k >= TIER_TEMPERATURE + config.localization_epsilon_k else "LOW"
            start, horizon, previous, pending_transition = D(0), config.method.maximum_segment_horizon_s, None, None
            first_primitive = _request_primitive(config, layout, solver, regime, start, horizon, None)
            chain.prepare(assignment, layout, first_primitive)
            names = ("Current [A]", "Voltage [V]", "Discharge capacity [A.h]",
                "Volume-averaged cell temperature [K]", "Ambient temperature [K]")
            while start < config.method.maximum_model_clock_s:
                previous_id = summaries[-1].actual_terminal if summaries else None
                primitive = first_primitive if not summaries else _request_primitive(config, layout, solver, regime, start, horizon, previous_id)
                request = chain.enter(primitive)
                call_cpu, call_wall = time.process_time(), time.monotonic()
                current_records = {name: None for name in (
                    "full-state", "requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")}
                terminal_manifest = None
                raw_clocks = first = last = ()
                failure = None
                next_control = None
                returned_solution = raw_return = full = endpoints = raw = observed = values = None

                def receive_requested(state):
                    if current_records["requested-initial"] is not None:
                        raise ValueError("actual segment repeated its initial consistency input")
                    chain.publish("requested-initial", state)
                    current_records["requested-initial"] = state

                try:
                    with observe_requested_initialization(pybamm, built, protocol, layout, request, receive_requested):
                        with warnings.catch_warnings(record=True) as observed_warnings:
                            returned_solution = solver.step(previous, built, float(horizon),
                                inputs=primitive["inputs"], save=False)
                except _CustodyFailure:
                    raise
                except Exception as caught:
                    failure = caught
                    returned = chain.returned(request, error=caught)
                    termination = type(caught).__name__
                else:
                    returned = chain.returned(request)
                    try:
                        raw_return = observe_raw_return(returned_solution, protocol, request, returned)
                        chain.publish("raw-return", raw_return)
                        full = observe_full_segment(returned_solution, protocol, layout, request, returned, raw_return)
                        chain.publish("full-state", full)
                        current_records["full-state"] = full
                        if any(digest != layout.model_expression_sha256 for digest in full.returned_model_expression_sha256):
                            raise ValueError("actual returned native model differs from its frozen processed layout")
                        endpoints = passive._solution_observation(returned_solution)
                        if endpoints["states"] is None or current_records["requested-initial"] is None:
                            raise ValueError("actual segment omits its full requested/returned initialization")
                        evidence = (_identity(returned, "return_id"), _identity(full, "segment_id"))
                        for role, index in (("actual-initial", 0), ("actual-terminal", 1), ("initial-derivative", 0), ("terminal-derivative", 1)):
                            is_derivative = role.endswith("derivative")
                            if is_derivative and endpoints["derivatives"] is None:
                                state = passive.unavailable_state(role, protocol, layout)
                            else:
                                state = passive.observe_state(endpoints["derivatives" if is_derivative else "states"][index],
                                    endpoints["clocks"][index], role, protocol, layout, evidence)
                            state = replace(state, observation_id=request.request_id + "." + role)
                            manifest = chain.publish(role, state)
                            current_records[role] = state
                            if role == "actual-terminal":
                                terminal_manifest = manifest
                        raw = np.asarray(returned_solution.t, dtype=float).reshape(-1)
                        raw_clocks = tuple(passive._decimal(value) for value in raw)
                        observed = np.unique(np.concatenate((raw, np.arange(np.ceil(raw[0]), raw[-1], 1))))
                        values = tuple(tuple(passive._decimal(value) for value in np.asarray(returned_solution[name](observed), dtype=float).reshape(-1)) for name in names)
                        if any(len(column) != len(observed) for column in values):
                            raise ValueError("actual receiver interpolation changes its complete grid census")
                        first = (values[0][0], values[1][0], values[3][0], values[2][0])
                        last = (values[0][-1], values[1][-1], values[3][-1], values[2][-1])
                        for index, value in enumerate(observed):
                            clock = passive._decimal(value)
                            if not receiver_clocks or clock > receiver_clocks[-1]:
                                receiver_clocks.append(clock)
                                for column, rows in zip(receiver_columns, values, strict=True):
                                    column.append(rows[index])
                                regimes.append(regime)
                        termination = str(returned_solution.termination)
                        if termination == "failure":
                            raise RuntimeError("native solver failure: " + "; ".join(str(row.message) for row in observed_warnings))
                        next_control = _continuation(config, regime, start, horizon, raw_clocks, termination, last)
                        previous = detached_continuation(returned_solution, pybamm) if next_control is not None else None
                    except _CustodyFailure:
                        raise
                    except Exception as caught:
                        failure, next_control, previous = caught, None, None
                        if termination == "native-not-built":
                            termination = type(caught).__name__
                next_primitive = None
                if next_control is not None:
                    next_regime, next_start, next_horizon, _ = next_control
                    next_primitive = _request_primitive(config, layout, solver, next_regime, next_start, next_horizon,
                        _identity(current_records["actual-terminal"], "observation_id"))
                inspection = chain.close(next_primitive=next_primitive, terminal_manifest=terminal_manifest,
                    failure=failure, cpu_start=call_cpu, wall_start=call_wall)
                ids = {name.replace("-", "_"): None if record is None else _identity(record,
                    "segment_id" if name == "full-state" else "observation_id") for name, record in current_records.items()}
                summary = SegmentSummary(request.request_id + ".summary", _identity(config, "config_id"),
                    _identity(protocol, "protocol_id"), request.ordinal, regime, start, horizon,
                    request.identity, _identity(returned, "return_id"), _identity(inspection.receipt, "receipt_id"),
                    "RETURNED" if failure is None else "TECHNICAL_FAILURE", termination,
                    None if failure is None else type(failure).__name__, None if failure is None else str(failure),
                    chain.last_cost.cpu_seconds, chain.last_cost.wall_seconds,
                    int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024, raw_clocks, first, last, **ids,
                    raw_return=None if raw_return is None else _identity(raw_return, "raw_id"),
                    native_definition=inspection.definition.identity)
                summaries.append(summary)
                if pending_transition is not None:
                    before, threshold = pending_transition
                    transitions.append(SegmentTransition("transition." + config.config_id + "." + str(len(transitions) + 1),
                        len(transitions) + 1, before.segment_index, summary.segment_index, before.regime, regime,
                        before.native_times_s[-1], threshold, config.localization_epsilon_k, before.actual_terminal,
                        summary.requested_initial, summary.actual_initial, before.end_receivers, summary.start_receivers))
                    pending_transition = None
                for key in boundary:
                    record = current_records[key.replace("_", "-")]
                    if key in ("actual_terminal", "terminal_derivative") or boundary[key] is None:
                        boundary[key] = record
                # Active full arrays and endpoint record objects do not survive
                # this iteration; only compact summaries and the terminal carrier.
                del current_records, returned_solution, raw_return, full, endpoints, raw, observed, values, primitive
                if failure is not None:
                    error = failure
                    break
                if next_control is None:
                    break
                next_regime, next_start, next_horizon, threshold = next_control
                if threshold is not None:
                    pending_transition = summary, threshold
                regime, start, horizon = next_regime, next_start, next_horizon
    except _CustodyFailure:
        raise
    except Exception as caught:
        if chain.ordinal != len(summaries):
            raise _CustodyFailure("actual segment census could not be represented; unknown forecast cannot be promoted") from caught
        error, termination = caught, type(caught).__name__
    if receiver_clocks:
        delivery = replace(delivery, applied_model_clock_s=receiver_clocks[0], applied_current_a=receiver_columns[0][0],
            applied_voltage_v=receiver_columns[1][0], applied_chamber_k=receiver_columns[4][0])
    modes = tuple("CV" if abs(voltage - D("4.2")) <= D(".001") and abs(current) < (D("1.455") if regime == "LOW" else D("3.395")) - D("1e-6")
        else "CC" if abs(abs(current) - (D("1.455") if regime == "LOW" else D("3.395"))) <= D("1e-6") else "UNRESOLVED"
        for current, voltage, regime in zip(receiver_columns[0], receiver_columns[1], regimes, strict=True))
    trace = SegmentedTrace("trace." + config.config_id, config, sha256(Path(__file__).read_bytes()).hexdigest(),
        "TECHNICAL_FAILURE" if error is not None else "TARGET_REACHED" if TARGET_EVENT in termination else "SERVICE_TERMINATED",
        termination, None if error is None else type(error).__name__, None if error is None else str(error), delivery,
        tuple(receiver_clocks), *(tuple(column) for column in receiver_columns), modes, tuple(regimes), event_names,
        expressions, tuple(summaries), tuple(transitions), 1, len(summaries), passive._decimal(time.monotonic() - wall),
        passive._decimal(time.process_time() - cpu), int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024)
    records = {"trace": trace, "protocol": protocol, "source-assignment": assignment, "layout": layout,
        **{name.replace("_", "-"): record for name, record in boundary.items()}}
    retained = chain.retained_bytes
    for name, record in records.items():
        if record is not None:
            retained += passive._publish(native_subwork, entry, name, record).materialization.size_bytes
    complete = error is None and all(record is not None for record in records.values())
    inspection = native_subwork.complete(entry,
        operational_status=OperationalStatus.SUCCEEDED if complete else OperationalStatus.FAILED,
        cost=InquiryCost(passive._decimal(time.process_time() - cpu), passive._decimal(time.monotonic() - wall), D(retained)),
        cost_scope="complete changed segmented method, including native segments/full output custody; do not sum nested costs; payload bytes exclude manifests/receipts/control records",
        consumed_streams=definition.streams, peak_rss_bytes=trace.process_peak_rss_bytes,
        reason_codes=() if complete else ("segmented-return-or-capture-incomplete",))
    return SegmentedNativeResult(trace, protocol, assignment, layout, **boundary, inspection=inspection)


def returned_records(result):
    if result.recovered or result.inspection.receipt is None:
        raise ValueError("segmented outputs require original records and their actual producing receipt")
    records = {name.replace("_", "-"): getattr(result, name) for name in (
        "trace", "protocol", "source_assignment", "layout", "requested_initial", "actual_initial",
        "initial_derivative", "actual_terminal", "terminal_derivative")}
    records["native-receipt"] = result.inspection.receipt
    return records
