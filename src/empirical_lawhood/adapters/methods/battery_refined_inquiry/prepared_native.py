# SPDX-License-Identifier: MPL-2.0
"""Passive successor capture through the installed native-subwork custody port.

The historical acquisition core supplies the science. These scoped worker-local
hooks observe its actual requests and returns; they never solve an extra eSOH
problem or reconstruct an unobserved initialized state. A producing receipt and
the independent PURE preparation assessment are later consumer responsibilities.
"""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import Decimal
from functools import partial, wraps
from hashlib import sha256
import inspect
import json
import math
from pathlib import Path
import time
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import ADDITIONAL_SOURCE_MEMBERS
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.native import acquire_with_numerics
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkInspection, NativeSubworkOutput,
    NativeSubworkRoster,
)
from .contracts import ChargingAttempt, NativeConfig, Trace
from .preparation_contracts import (
    InitialElectrodePreparationWitness, ObservationKind, PreparationProtocol,
    ProcessedInitialStateLayout, StateBlock, StateObservation, identity,
)
from .preparation_science import PREPARATION_SOURCE_MEMBERS

D = Decimal


def expected_casadi_path():
    """Match the selected interpreter's literal PyBaMM import setting."""
    import sysconfig
    purelib = sysconfig.get_path("purelib")
    if type(purelib) is not str or not Path(purelib).is_absolute():
        raise ValueError("ENVIRONMENT: selected interpreter has no absolute purelib path")
    return str(Path(purelib) / "casadi")


def native_worker_environment(environment):
    """Select operational import settings before preparation; import no engine."""
    if type(environment) is not dict or any(type(key) is not str or type(value) is not str
            for key, value in environment.items()):
        raise ValueError("battery native environment requires exact string settings")
    selected = dict(environment)
    selected.setdefault("CASADIPATH", expected_casadi_path())
    return selected


def require_native_worker_environment(prepared_environment):
    """Refuse missing/wrong selection before PyBaMM can mutate the worker."""
    import os
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment
    if type(prepared_environment) is not PreparedWorkerEnvironment:
        raise ValueError("ENVIRONMENT: battery native import needs the exact prepared worker environment")
    prepared_environment.__post_init__()
    expected = expected_casadi_path()
    if (dict(prepared_environment.selected_environment).get("CASADIPATH") != expected
            or os.environ.get("CASADIPATH") != expected):
        raise ValueError("ENVIRONMENT: select CASADIPATH=" + expected + " for the selected interpreter before worker preparation")


def _decimal(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("native observation contains a nonfinite binary64 value")
    return D(str(value))


def _freeze(value):
    """Retain primitive types and actual binary64 bits, never rounded requests."""
    if value is None or type(value) in (str, bool, int):
        return value
    if isinstance(value, (float, Decimal)):
        _decimal(value)
        return {"binary64": float(value).hex()}
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("native request mapping requires string keys")
        return {key: _freeze(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    import numpy as np
    array = np.asarray(value, dtype=float)
    values = tuple(array.reshape(-1))
    for item in values:
        _decimal(item)
    return {"shape": tuple(array.shape), "binary64": tuple(float(v).hex() for v in values)}


def _validate_primitive_json(value):
    def reject_float(text):
        raise ValueError("native primitive floats require their exact binary64 representation")
    document = json.loads(value, parse_float=reject_float, parse_constant=reject_float)
    if json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n" != value:
        raise ValueError("native primitive material requires canonical exact bytes")


@dataclass(frozen=True, slots=True)
class NativeRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/native-request"
    request_id: str
    protocol: ObjectIdentity
    configuration: ObjectIdentity
    kind: str
    ordinal: int
    primitive_json: str

    def __post_init__(self):
        validate_stable_id(self.request_id)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA or self.configuration.object_schema != NativeConfig.SCHEMA:
            raise ValueError("native request changes its protocol/configuration")
        if self.kind not in {"initializer", "charging", "end-of-chain"} or type(self.ordinal) is not int or self.ordinal < 0:
            raise ValueError("native request changes its actual effect slot")
        _validate_primitive_json(self.primitive_json)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.request_id, self)


@dataclass(frozen=True, slots=True)
class NativeReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/native-return"
    return_id: str
    request: ObjectIdentity
    disposition: str
    error_type: str | None
    error_message: str | None
    observed_json: str

    def __post_init__(self):
        validate_stable_id(self.return_id)
        if self.request.object_schema != NativeRequest.SCHEMA:
            raise ValueError("native return substitutes its actual request")
        if (self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
                or (self.disposition == "TECHNICAL_FAILURE") != (self.error_type is not None and self.error_message is not None)
                or self.disposition == "RETURNED" and (self.error_type is not None or self.error_message is not None)):
            raise ValueError("native return loses its actual error/return distinction")
        _validate_primitive_json(self.observed_json)


@dataclass(frozen=True, slots=True)
class ElectrodeSOHRequest(CanonicalRecord):
    """Actual dispatcher operands retained before calling its existing method."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/esoh-request"
    request_id: str
    protocol: ObjectIdentity
    primitive_json: str

    def __post_init__(self):
        validate_stable_id(self.request_id)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA:
            raise ValueError("actual eSOH request substitutes its preparation protocol")
        _validate_primitive_json(self.primitive_json)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.request_id, self)


@dataclass(frozen=True, slots=True)
class ElectrodeSOHReturn(CanonicalRecord):
    """The actual dispatcher request/return, separate from backend-call counts."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-preparation/esoh-return"
    observation_id: str
    protocol: ObjectIdentity
    request: ObjectIdentity
    disposition: str
    error_type: str | None
    error_message: str | None
    returned_json: str

    def __post_init__(self):
        validate_stable_id(self.observation_id)
        if self.protocol.object_schema != PreparationProtocol.SCHEMA:
            raise ValueError("actual eSOH observation substitutes its preparation protocol")
        if self.request.object_schema != ElectrodeSOHRequest.SCHEMA:
            raise ValueError("actual eSOH return changes its exact dispatcher request")
        if (self.disposition not in {"RETURNED", "TECHNICAL_FAILURE"}
                or (self.disposition == "TECHNICAL_FAILURE") != (self.error_type is not None and self.error_message is not None)
                or self.disposition == "RETURNED" and (self.error_type is not None or self.error_message is not None)):
            raise ValueError("actual eSOH return loses its error/return distinction")
        _validate_primitive_json(self.returned_json)


def _output(name, record_type):
    return NativeSubworkOutput(name, record_type.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")


def forecast_outputs():
    """Exact public output slots for the fresh domain graph; no generated IDs."""
    return tuple(sorted((
        _output("trace", Trace), _output("protocol", PreparationProtocol),
        _output("witness", InitialElectrodePreparationWitness),
        _output("layout", ProcessedInitialStateLayout),
        *(_output(name, StateObservation) for name in (
            "requested-initial", "actual-initial", "initial-derivative", "actual-terminal", "terminal-derivative")),
        _output("native.request.first", NativeRequest),
        _output("esoh.request", ElectrodeSOHRequest),
        _output("esoh.return", ElectrodeSOHReturn),
    ), key=lambda row: row.output_id))


def _publish(progress, entry, output_id, record):
    payload = record.canonical_bytes()
    return progress.publish_output(entry, output_id, (payload,), maximum_bytes=len(payload),
        maximum_chunk_bytes=len(payload), expected_size_bytes=len(payload),
        expected_physical_sha256=sha256(payload).hexdigest())


class _EffectChain:
    """Live request carriers support the actual unbounded conditional census.

    A returned child publishes its return immediately. Its completion waits only
    until the next actual request or an explicit terminal carrier is published.
    Thus every configuration is authenticated before its BEGIN/contact, and a
    lost creator is never replaced by a persisted handle or replayed call.
    """
    def __init__(self, progress, entry, protocol, inputs):
        self.progress, self.carrier, self.protocol = progress, entry, protocol
        self.definition = entry.definition
        self.base_inputs = inputs
        self.inputs = inputs
        self.ordinal = 0
        self.pending = None
        self.completed_calls = 0
        self.charging_calls = 0
        self.retained_bytes = 0
        self.fatal = None

    def _request(self, kind, primitive):
        suffix = ".end" if kind == "end-of-chain" else ""
        return NativeRequest(self.definition.subwork_id + ".request." + str(self.ordinal) + suffix,
            identity(self.protocol, self.protocol.protocol_id), self.protocol.configuration, kind,
            self.ordinal, canonical_json_bytes(_freeze(primitive)).decode())

    def _complete_pending(self):
        if self.pending is None:
            return
        disposition, cpu, wall, retained = self.pending
        self.progress.complete(self.carrier,
            operational_status=OperationalStatus.SUCCEEDED if disposition == "RETURNED" else OperationalStatus.FAILED,
            cost=InquiryCost(cpu, wall, D(retained)),
            cost_scope="actual native call and passive capture; nested in complete forecast; do not sum twice",
            consumed_streams=self.carrier.definition.streams,
            reason_codes=() if disposition == "RETURNED" else ("actual-native-call-error",))
        self.completed_calls += 1
        self.pending = None

    def enter(self, kind, primitive):
        if self.fatal is not None:
            raise self.fatal
        if self.ordinal and self.pending is None:
            raise ValueError("selected native observer cannot overlap actual backend calls")
        self.ordinal += 1
        request = self._request(kind, primitive)
        carrier = self.carrier
        output_id = "native.request.first" if self.pending is None else "native.request.next"
        manifest = _publish(self.progress, carrier, output_id, request)
        self.retained_bytes += manifest.materialization.size_bytes
        if self.pending is not None:
            disposition, cpu, wall, retained = self.pending
            self.pending = (disposition, cpu, wall, retained + manifest.materialization.size_bytes)
        definition = replace(self.definition,
            subwork_id=self.definition.subwork_id + ".call." + str(self.ordinal),
            operation_id="battery.prepared-native." + kind,
            configuration=request.identity,
            input_materialization_ids=tuple(sorted((*self.definition.input_materialization_ids,
                                                   manifest.materialization.materialization_id))),
            outputs=(_output("native.request.next", NativeRequest), _output("native.return", NativeReturn)),
            roster_id="conditional.battery.call." + str(self.ordinal))
        self.progress.freeze_roster(NativeSubworkRoster(definition.roster_id, definition.parent_contact,
            (definition.identity,), carrier.definition.identity), carrier, definitions=(definition,))
        # Only this exact new request and the original authenticated operands
        # enter the next call; custody retains all earlier conditional receipts.
        self.inputs = None if self.base_inputs is None else tuple(sorted((*self.base_inputs, manifest), key=lambda row: row.materialization.materialization_id))
        entry = self.progress.begin(definition, self.inputs)
        self._complete_pending()
        self.progress.contact(entry)
        self.carrier = entry
        self.charging_calls += kind == "charging"
        return request

    def returned(self, request, observed, *, error=None, cpu_start, wall_start):
        result = NativeReturn(request.request_id + ".return", request.identity,
            "RETURNED" if error is None else "TECHNICAL_FAILURE",
            None if error is None else type(error).__name__, None if error is None else str(error),
            canonical_json_bytes(_freeze(observed)).decode())
        manifest = _publish(self.progress, self.carrier, "native.return", result)
        self.retained_bytes += manifest.materialization.size_bytes
        self.pending = (result.disposition, _decimal(time.process_time() - cpu_start),
                        _decimal(time.monotonic() - wall_start), manifest.materialization.size_bytes)
        return result

    def finish(self):
        request = self._request("end-of-chain", {"actual_native_calls": self.ordinal})
        manifest = _publish(self.progress, self.carrier,
            "native.request.first" if self.pending is None else "native.request.next", request)
        self.retained_bytes += manifest.materialization.size_bytes
        if self.pending is not None:
            disposition, cpu, wall, retained = self.pending
            self.pending = (disposition, cpu, wall, retained + manifest.materialization.size_bytes)
        self._complete_pending()


def _model_digest(model, names):
    return sha256(json.dumps({name: sorted((str(variable), str(expression))
        for variable, expression in getattr(model, name).items()) for name in names},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _slice(model, variable):
    slices = model.y_slices.get(variable)
    if slices is None:
        slices = tuple(part for child in variable.children for part in model.y_slices[child])
    if not slices or any(part.step not in (None, 1) for part in slices):
        raise ValueError("processed native state has no complete contiguous owning slice")
    start, stop = slices[0].start, slices[-1].stop
    if any(a.stop != b.start for a, b in zip(slices, slices[1:])):
        raise ValueError("processed native state owning slices omit components")
    return start, stop


_ROLES = {
    "Discharge capacity [A.h]": "discharge-capacity",
    "Throughput capacity [A.h]": "throughput-capacity",
    "X-averaged negative particle concentration [mol.m-3]": "negative-solid",
    "Negative particle concentration [mol.m-3]": "negative-solid",
    "X-averaged positive particle concentration [mol.m-3]": "positive-solid",
    "Positive particle concentration [mol.m-3]": "positive-solid",
    "Porosity times concentration [mol.m-3]": "electrolyte",
    "Volume-averaged cell temperature [K]": "temperature",
    "Current variable [A]": "current",
    "Negative electrode potential [V]": "negative-potential",
    "Positive electrode potential [V]": "positive-potential",
    "Electrolyte potential [V]": "electrolyte-potential",
}


def observe_processed_layout(model, protocol):
    """Read owning rows and electrolyte aliases from this actual built model."""
    blocks, aliases = [], ()
    for variable in (*model.rhs, *model.algebraic):
        start, stop = _slice(model, variable)
        role = _ROLES.get(variable.name)
        if role is None:
            raise ValueError("native processed state includes an unselected owning role")
        def scalar(expression):
            return _decimal(expression.evaluate() if hasattr(expression, "evaluate") else expression)
        domains = tuple(domain for rows in variable.domains.values() for domain in rows)
        blocks.append(StateBlock(role, variable.name, start, stop,
            scalar(variable.scale), scalar(variable.reference), domains))
        if role == "electrolyte":
            if len(variable.children) != 3:
                raise ValueError("native electrolyte state omits its three actual aliases")
            aliases = tuple((name, *_slice(model, child)) for name, child in
                            zip(("negative", "separator", "positive"), variable.children, strict=True))
    return ProcessedInitialStateLayout("layout." + protocol.protocol_id,
        identity(protocol, protocol.protocol_id), _model_digest(model, ("rhs", "algebraic")),
        _model_digest(model, ("initial_conditions",)), int(model.len_rhs), int(model.len_alg),
        tuple(sorted(blocks, key=lambda row: row.start)), aliases, True)


def observe_state(values, clock, role, protocol, layout, evidence):
    import numpy as np
    array = np.asarray(values, dtype=float).reshape(-1)
    if array.size != layout.differential_count + layout.algebraic_count:
        raise ValueError("actual native boundary omits full differential/algebraic state")
    return StateObservation("observation." + protocol.protocol_id + "." + role,
        identity(protocol, protocol.protocol_id), identity(layout, layout.layout_id), role,
        ObservationKind.OBSERVED, _decimal(clock), tuple(_decimal(v) for v in array),
        tuple(float(v).hex() for v in array), evidence)


def unavailable_state(role, protocol, layout):
    return StateObservation("observation." + protocol.protocol_id + "." + role,
        identity(protocol, protocol.protocol_id), identity(layout, layout.layout_id), role,
        ObservationKind.UNAVAILABLE, None, (), (), ())


def _solution_observation(solution):
    """Only actual returned endpoint columns; never concatenate trajectories."""
    import numpy as np
    observed = {"termination": str(solution.termination), "states": None, "derivatives": None}
    if getattr(solution, "variables_returned", False) or not getattr(solution, "all_ys", None):
        return observed
    first, last = (np.asarray(rows, dtype=float) for rows in (solution.all_ys[0], solution.all_ys[-1]))
    if first.ndim != 2 or last.ndim != 2 or min(first.shape[1], last.shape[1]) < 1:
        raise ValueError("native return has no actual state endpoint columns")
    observed["states"] = (first[:, 0], last[:, -1])
    observed["clocks"] = (float(solution.all_ts[0][0]), float(solution.all_ts[-1][-1]))
    returned_derivatives = getattr(solution, "all_yps", None)
    if returned_derivatives is not None and len(returned_derivatives):
        if len(returned_derivatives) != len(solution.all_ys):
            raise ValueError("returned derivative segment census differs from actual full states")
        a, b = (np.asarray(rows, dtype=float) for rows in (returned_derivatives[0], returned_derivatives[-1]))
        if a.shape != first.shape or b.shape != last.shape:
            raise ValueError("returned derivative endpoint dimensions differ from actual full states")
        observed["derivatives"] = (a[:, 0], b[:, -1])
    return observed


class _Capture:
    def __init__(self, protocol, chain, forecast_entry):
        self.protocol, self.chain, self.forecast_entry = protocol, chain, forecast_entry
        self.layout = self.requested_initial = self.actual_initial = self.actual_terminal = None
        self.initial_derivative = self.terminal_derivative = None
        self.pre_soc = self.assigned = self.esoh = self.esoh_request = self.assignment_request = None
        self.initializer_evidence = []
        self.initializer_dispositions = []
        self.active_request = None
        self.retained_bytes = 0

    def guard(self, callback):
        try:
            return callback()
        except BaseException as error:
            self.chain.fatal = error
            raise


@contextmanager
def observe_native_calls(backend, capture):
    """Patch only inside one isolated native worker; restore exact methods.

    BaseSolver.solve observes actual composite fallback backends, while the
    composite dispatcher is not counted as a duplicate solver invocation.
    """
    patches = []
    def patch(owner, name, make):
        local = name in owner.__dict__
        original = getattr(owner, name)
        patches.append((owner, name, original, local))
        setattr(owner, name, make(original))

    def solve_wrapper(original):
        @wraps(original)
        def wrapped(solver, model, *args, **kwargs):
            arguments = inspect.signature(original).bind(solver, model, *args, **kwargs)
            arguments.apply_defaults()
            primitive = {"solver": solver.to_config(), "model_name": str(model.name),
                "model_expression_sha256": _model_digest(model, ("algebraic", "initial_conditions")),
                "arguments": {key: value for key, value in arguments.arguments.items() if key not in {"self", "model"}},
                "esoh_request": capture.esoh_request}
            request = capture.guard(lambda: capture.chain.enter("initializer", primitive))
            cpu, wall = time.process_time(), time.monotonic()
            try:
                solution = original(solver, model, *args, **kwargs)
            except Exception as error:
                result = capture.guard(lambda error=error: capture.chain.returned(request, {}, error=error, cpu_start=cpu, wall_start=wall))
                capture.initializer_evidence.append(ObjectIdentity.from_record(result.return_id, result))
                capture.initializer_dispositions.append("TECHNICAL_FAILURE")
                raise
            result = capture.guard(lambda: capture.chain.returned(request, _solution_observation(solution), cpu_start=cpu, wall_start=wall))
            capture.initializer_evidence.append(ObjectIdentity.from_record(result.return_id, result))
            capture.initializer_dispositions.append("RETURNED")
            return solution
        return wrapped

    def esoh_wrapper(original):
        @wraps(original)
        def wrapped(solver, inputs, direction=None):
            if capture.esoh is not None:
                raise ValueError("selected battery build unexpectedly requests another eSOH dispatcher")
            params = solver.parameter_values
            capture.esoh_request = {"inputs": dict(inputs), "direction": direction,
                "soc_assignment_request": capture.assignment_request,
                "known_value": solver.known_value, "reference_temperature_k": params["Reference temperature [K]"],
                "lower_voltage_v": params["Lower voltage cut-off [V]"],
                "upper_voltage_v": params["Upper voltage cut-off [V]"],
                "faraday_constant": float(backend.constants.F.value),
                "ocp_clipping_tolerance": backend.settings.tolerances["U__c_s"],
                "exact_min_max": backend.settings.min_max_mode == "exact"}
            request = ElectrodeSOHRequest("esoh-request." + capture.protocol.protocol_id,
                identity(capture.protocol, capture.protocol.protocol_id), canonical_json_bytes(_freeze(capture.esoh_request)).decode())
            manifest = capture.guard(lambda: _publish(capture.chain.progress, capture.forecast_entry, "esoh.request", request))
            capture.retained_bytes += manifest.materialization.size_bytes
            try:
                returned = original(solver, inputs, direction)
            except Exception as error:
                record = ElectrodeSOHReturn("esoh-return." + capture.protocol.protocol_id,
                    identity(capture.protocol, capture.protocol.protocol_id), request.identity,
                    "TECHNICAL_FAILURE", type(error).__name__, str(error), canonical_json_bytes({}).decode())
                manifest = capture.guard(lambda: _publish(capture.chain.progress, capture.forecast_entry, "esoh.return", record))
                capture.retained_bytes += manifest.materialization.size_bytes
                raise
            capture.esoh = dict(returned)
            record = ElectrodeSOHReturn("esoh-return." + capture.protocol.protocol_id,
                identity(capture.protocol, capture.protocol.protocol_id), request.identity,
                "RETURNED", None, None, canonical_json_bytes(_freeze(capture.esoh)).decode())
            manifest = capture.guard(lambda: _publish(capture.chain.progress, capture.forecast_entry, "esoh.return", record))
            capture.retained_bytes += manifest.materialization.size_bytes
            return returned
        return wrapped

    def assign_wrapper(original):
        @wraps(original)
        def wrapped(simulation, *args, **kwargs):
            main = bool(simulation._model.rhs)
            if main:
                arguments = inspect.signature(original).bind(simulation, *args, **kwargs)
                arguments.apply_defaults()
                capture.assignment_request = {key: value for key, value in arguments.arguments.items() if key != "self"}
                params = simulation._unprocessed_parameter_values
                capture.pre_soc = tuple(params[name] for name in (
                    "Initial concentration in negative electrode [mol.m-3]", "Initial concentration in positive electrode [mol.m-3]"))
            result = original(simulation, *args, **kwargs)
            if main:
                capture.assigned = tuple(simulation._parameter_values[name] for name in (
                    "Initial concentration in negative electrode [mol.m-3]", "Initial concentration in positive electrode [mol.m-3]"))
            return result
        return wrapped

    def initial_conditions_wrapper(original):
        @wraps(original)
        def wrapped(solver, model, clock, inputs):
            result = original(solver, model, clock, inputs)
            if model.len_rhs > 0 and capture.requested_initial is None:
                if len(model.y0_list) != 1 or capture.active_request is None:
                    raise ValueError("selected full-output initial request has no exact single native state")
                capture.layout = capture.guard(lambda: observe_processed_layout(model, capture.protocol))
                capture.requested_initial = capture.guard(lambda: observe_state(model.y0_list[0], clock,
                    "requested-initial", capture.protocol, capture.layout, (capture.active_request.identity,)))
            return result
        return wrapped

    def step_wrapper(original):
        @wraps(original)
        def wrapped(solver, previous, model, *args, **kwargs):
            arguments = inspect.signature(original).bind(solver, previous, model, *args, **kwargs)
            arguments.apply_defaults()
            prior = None if previous is None else _solution_observation(previous)
            primitive = {"solver": solver.to_config(), "model_expression_sha256": _model_digest(model, ("rhs", "algebraic")),
                "initial_conditions_sha256": _model_digest(model, ("initial_conditions",)), "previous_return": prior,
                "arguments": {key: value for key, value in arguments.arguments.items() if key not in {"self", "old_solution", "model"}}}
            request = capture.guard(lambda: capture.chain.enter("charging", primitive))
            capture.active_request = request
            cpu, wall = time.process_time(), time.monotonic()
            try:
                solution = original(solver, previous, model, *args, **kwargs)
            except Exception as error:
                capture.guard(lambda error=error: capture.chain.returned(request, {}, error=error, cpu_start=cpu, wall_start=wall))
                raise
            observed = capture.guard(lambda: _solution_observation(solution))
            result = capture.guard(lambda: capture.chain.returned(request, observed, cpu_start=cpu, wall_start=wall))
            if observed["states"] is not None:
                layout = capture.layout
                if layout is None:
                    raise ValueError("actual returned initial state lacks its observed processed layout")
                evidence = (ObjectIdentity.from_record(result.return_id, result),)
                if capture.actual_initial is None:
                    capture.actual_initial = observe_state(observed["states"][0], observed["clocks"][0], "actual-initial", capture.protocol, layout, evidence)
                    capture.initial_derivative = unavailable_state("initial-derivative", capture.protocol, layout) if observed["derivatives"] is None else observe_state(observed["derivatives"][0], observed["clocks"][0], "initial-derivative", capture.protocol, layout, evidence)
                capture.actual_terminal = observe_state(observed["states"][1], observed["clocks"][1], "actual-terminal", capture.protocol, layout, evidence)
                capture.terminal_derivative = unavailable_state("terminal-derivative", capture.protocol, layout) if observed["derivatives"] is None else observe_state(observed["derivatives"][1], observed["clocks"][1], "terminal-derivative", capture.protocol, layout, evidence)
            return solution
        return wrapped

    try:
        patch(backend.BaseSolver, "solve", solve_wrapper)
        patch(backend.lithium_ion.ElectrodeSOHSolver, "solve", esoh_wrapper)
        patch(backend.Simulation, "set_initial_state", assign_wrapper)
        patch(backend.BaseSolver, "_set_initial_conditions", initial_conditions_wrapper)
        patch(backend.BaseSolver, "step", step_wrapper)
        yield
    finally:
        for owner, name, original, local in reversed(patches):
            if local:
                setattr(owner, name, original)
            else:
                delattr(owner, name)


def _witness(capture):
    if any(value is None for value in (capture.esoh, capture.esoh_request, capture.pre_soc, capture.assigned)):
        return None
    esoh, request = capture.esoh, capture.esoh_request
    return InitialElectrodePreparationWitness("witness." + capture.protocol.protocol_id,
        identity(capture.protocol, capture.protocol.protocol_id), tuple(capture.initializer_dispositions),
        tuple(capture.initializer_evidence), *(_decimal(esoh[key]) for key in ("Q_Li", "Q_n", "Q_p", "Q")),
        _decimal(request["faraday_constant"]), *(_decimal(esoh[key]) for key in ("x_0", "x_100", "y_0", "y_100")),
        *(_decimal(value) for value in capture.assigned), *(_decimal(value) for value in capture.pre_soc),
        *(_decimal(request[key]) for key in ("reference_temperature_k", "lower_voltage_v", "upper_voltage_v", "ocp_clipping_tolerance")),
        request["exact_min_max"], request["known_value"], "NONE" if request["direction"] is None else request["direction"])


@dataclass(frozen=True, slots=True)
class PreparedNativeResult:
    trace: Trace | None
    protocol: PreparationProtocol
    witness: InitialElectrodePreparationWitness | None
    layout: ProcessedInitialStateLayout | None
    requested_initial: StateObservation | None
    actual_initial: StateObservation | None
    initial_derivative: StateObservation | None
    actual_terminal: StateObservation | None
    terminal_derivative: StateObservation | None
    inspection: NativeSubworkInspection
    recovered: bool = False


def _validate_source_pins(backend, protocol):
    root = Path(backend.__file__).parent
    import scipy
    for name, expected in PREPARATION_SOURCE_MEMBERS:
        path = Path(scipy.__file__).parent / name.removeprefix("scipy/") if name.startswith("scipy/") else root / name
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("actual preparation native source pin differs: " + name)
    if not set(PREPARATION_SOURCE_MEMBERS).issubset(set(protocol.source_members)):
        raise ValueError("native preparation protocol omits exact source members")


def acquire_prepared(config, *, protocol, provenance, definition, native_subwork, inputs=None):
    """Enter only an already selected fresh native slot with authenticated inputs.

    Known completion returns its inspection without loading or relabelling any
    retained payload. The caller recovers its authenticated bytes. Unknown
    contact raises through the shared port before any native import or effect.
    """
    if type(config) is not NativeConfig or type(protocol) is not PreparationProtocol or type(provenance) is not NumericalProducingProvenance:
        raise ValueError("prepared acquisition requires exact typed prospective operands")
    config.__post_init__()
    protocol.__post_init__()
    provenance.__post_init__()
    settings = config.numerical_view
    if (definition.parent_contact != native_subwork.parent_contact
            or definition.configuration != ObjectIdentity.from_record(config.config_id, config)
            or protocol.configuration != definition.configuration
            or protocol.source != ObjectIdentity.from_record(config.source.source_id, config.source)
            or protocol.producing_provenance != provenance.identity
            or not {protocol.source, provenance.identity, identity(protocol, protocol.protocol_id)}.issubset(set(definition.sources))
            or definition.outputs != forecast_outputs()
            or protocol.model_family != ("DFN" if "dfn" in config.model_view else "SPMe")
            or protocol.parameter_source != ("Chen2020" if config.model_view == "chen-spme" else "ORegan2022")
            or (protocol.electrode_points, protocol.particle_points) != (settings.electrode_points, settings.particle_points)
            or protocol.initial_temperature_k != config.initial_temperature_k):
        raise ValueError("prepared acquisition substitutes its frozen native source/configuration/protocol/output census")
    recovered = native_subwork.recover(definition)
    if recovered is not None:
        return PreparedNativeResult(None, protocol, None, None, None, None, None, None, None, recovered, True)
    entry = native_subwork.begin(definition, inputs)
    native_subwork.contact(entry)
    chain = _EffectChain(native_subwork, entry, protocol, inputs)
    capture = _Capture(protocol, chain, entry)
    wall, cpu = time.monotonic(), time.process_time()
    import pybamm
    _validate_source_pins(pybamm, protocol)
    with observe_native_calls(pybamm, capture):
        trace = acquire_with_numerics(config, electrode_points=settings.electrode_points,
            particle_points=settings.particle_points, rtol=settings.rtol, atol=settings.atol,
            additional_source_members=ADDITIONAL_SOURCE_MEMBERS, trace_factory=Trace,
            charging_attempt_factory=partial(ChargingAttempt, configuration=config))
    if chain.fatal is not None:
        raise chain.fatal
    chain.finish()
    witness = _witness(capture)
    records = {"trace": trace, "protocol": protocol, "witness": witness, "layout": capture.layout,
        "requested-initial": capture.requested_initial, "actual-initial": capture.actual_initial,
        "initial-derivative": capture.initial_derivative, "actual-terminal": capture.actual_terminal,
        "terminal-derivative": capture.terminal_derivative}
    retained = chain.retained_bytes + capture.retained_bytes
    for name, record in records.items():
        if record is not None:
            retained += _publish(native_subwork, entry, name, record).materialization.size_bytes
    census_agrees = (trace.backend_solve_calls == chain.charging_calls
        and tuple(row.disposition for row in trace.initializer_attempts) == tuple(capture.initializer_dispositions))
    complete = trace.disposition != "TECHNICAL_FAILURE" and all(record is not None for record in records.values()) and capture.esoh is not None and census_agrees
    reasons = () if complete else tuple(sorted({"native-preparation-return-or-capture-incomplete"}
        | ({"native-capture-ledger-disagrees"} if not census_agrees else set())))
    result = native_subwork.complete(entry,
        operational_status=OperationalStatus.SUCCEEDED if complete else OperationalStatus.FAILED,
        cost=InquiryCost(_decimal(time.process_time() - cpu), _decimal(time.monotonic() - wall), D(retained)),
        cost_scope="complete historical acquisition and passive custody; includes nested calls, do not sum twice; retained bytes are all published payloads, excluding manifests/receipts/control records",
        consumed_streams=definition.streams, reason_codes=reasons)
    return PreparedNativeResult(trace, protocol, witness, capture.layout, capture.requested_initial,
        capture.actual_initial, capture.initial_derivative, capture.actual_terminal, capture.terminal_derivative, result)


def build_forecast_definition(config, protocol, provenance, native_subwork, input_materialization_ids):
    """Bind the domain's exact request to its already contacted task and sources."""
    if type(config) is not NativeConfig or type(protocol) is not PreparationProtocol or type(provenance) is not NumericalProducingProvenance:
        raise ValueError("forecast definition requires exact prospective native operands")
    return NativeSubworkDefinition("forecast." + config.config_id, "battery.prepared-native.forecast",
        native_subwork.parent_contact, ObjectIdentity.from_record(config.config_id, config),
        tuple(sorted((protocol.source, provenance.identity, identity(protocol, protocol.protocol_id)), key=lambda row: row.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256,
        tuple(sorted(input_materialization_ids)), (), forecast_outputs())


def freeze_forecast_roster(native_subwork, definitions):
    """Freeze the caller's complete selected task denominator before entry."""
    definitions = tuple(sorted(definitions, key=lambda row: row.subwork_id))
    native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork", native_subwork.parent_contact,
        tuple(row.identity for row in definitions)), definitions=definitions)


def returned_records(result):
    """Fresh graph outputs include the actual completed subwork receipt.

    Recovered payloads must be loaded and authenticated by the coordinator;
    this producer never invents their native objects from a receipt alone.
    """
    if result.recovered or result.inspection.receipt is None:
        raise ValueError("native records require original returned objects and the actual producing receipt")
    records = {name.replace("_", "-"): getattr(result, name) for name in (
        "trace", "protocol", "witness", "layout", "requested_initial", "actual_initial",
        "initial_derivative", "actual_terminal", "terminal_derivative")}
    records["native-receipt"] = result.inspection.receipt
    return records
