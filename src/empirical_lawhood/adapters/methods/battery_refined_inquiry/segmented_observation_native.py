# SPDX-License-Identifier: MPL-2.0
"""Declared initial-window observation using preserved native source helpers.

This additive controller stops only after complete actual source-method returns.
It owns the observation loop and distinct definition; frozen forecast owners are
unchanged. Full forecast, physical qualification and historical recovery remain
separate from these scoped preparation/numerical/resource observations.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import file_digest, sha256
import json
import importlib.metadata
import os
from pathlib import Path
import resource
import time
import sys
import warnings

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.kernel.status import OperationalStatus
from . import preparation_contracts as pc
from .preparation_science import PREPARATION_SOURCE_MEMBERS
from . import segmented_native as base
from . import segmented_evidence as se
from . import segmented_observation_contracts as oc
from . import segmented_science as ss
from .segmented_native import (
    BatteryInquiryDelivery, CONTROL_RULE, InquiryCost, SegmentSummary, SegmentTransition, SegmentedTrace,
    SegmentedNativeResult, TARGET_EVENT, TIER_TEMPERATURE, _SegmentChain, _CustodyFailure,
    _request_primitive, _continuation, build_runtime, detached_continuation, forbid_native_esoh,
    observe_requested_initialization, observe_raw_return, observe_full_segment, passive,
)

D = Decimal
_identity = ss.identity


def observation_outputs():
    return tuple(sorted((*base.forecast_outputs(),
        NativeSubworkOutput("observation-protocol", oc.PreparationObservationProtocol.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
        NativeSubworkOutput("entry-declaration", oc.ObservationEntryDeclaration.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")), key=lambda row: row.output_id))


def build_observation_definition(observation, method_index, protocol, provenance, progress, entry_declaration, input_materialization_ids):
    if type(observation) is not oc.PreparationObservationProtocol or type(method_index) is not int or not 0 <= method_index < 3:
        raise ValueError("native observation requires its exact prospective complete method selection")
    observation.__post_init__()
    entry_declaration.__post_init__()
    config = observation.configurations[method_index]
    legacy = base.build_forecast_definition(config, protocol, provenance, progress, input_materialization_ids)
    sources = (*legacy.sources, _identity(observation, "observation_id"),
        _identity(observation.original_selection, "roster_id"), _identity(observation.uncertain_work, "record_id"),
        _identity(entry_declaration, "declaration_id"), entry_declaration.abi_import_report,
        _identity(entry_declaration.resources, "snapshot_id"), entry_declaration.resources.evidence)
    return replace(legacy, subwork_id="observation." + config.config_id,
        operation_id="battery.segmented-observation.initial-window", sources=tuple(sorted(sources, key=lambda row: row.object_id)),
        outputs=observation_outputs())


def freeze_observation_roster(progress, definitions):
    definitions = tuple(sorted(definitions, key=lambda row: row.subwork_id))
    progress.freeze_roster(NativeSubworkRoster("selected.native-subwork", progress.parent_contact,
        tuple(row.identity for row in definitions)), definitions=definitions)


def _validate_operands(observation, method_index, protocol, provenance, definition, progress, declaration):
    if (type(declaration) is not oc.ObservationEntryDeclaration or type(protocol) is not pc.PreparationProtocol
            or type(provenance) is not NumericalProducingProvenance or type(definition) is not NativeSubworkDefinition):
        raise ValueError("observation needs typed original declaration, environment, protocol and custody operands")
    expected = build_observation_definition(observation, method_index, protocol, provenance, progress, declaration, definition.input_materialization_ids)
    config = observation.configurations[method_index]
    if (definition != expected or declaration.observation != _identity(observation, "observation_id")
            or declaration.configured_method_index != method_index or declaration.producing_provenance != provenance
            or protocol.producing_provenance != provenance.identity):
        raise ValueError("native observation changes actual declaration, environment or frozen parent/definition")
    original = base.build_forecast_definition(config, protocol, provenance, progress, definition.input_materialization_ids)
    base._validate_operands(config, protocol, provenance, original, progress)
    return config


def _validate_entry_sources(declaration, abi_payload, resource_payload):
    """Recompute exact input bytes before BEGIN/contact; no native import."""
    if (type(abi_payload) is not bytes or type(resource_payload) is not bytes
            or sha256(abi_payload).hexdigest() != declaration.abi_import_report.object_fingerprint
            or sha256(resource_payload).hexdigest() != declaration.resources.evidence.object_fingerprint):
        raise ValueError("native observation lacks original authenticated ABI/resource source bytes")
    abi, capacity = json.loads(abi_payload), json.loads(resource_payload)
    expected_packages = {"numpy": "2.4.6", "scipy": "1.17.1", "casadi": "3.7.2", "pybammsolvers": "0.8.2", "pybamm": "26.6.2.0", "python-flint": "0.8.0"}
    if (abi.get("schema") != "empirical-lawhood/development/battery-selected-abi-import-smoke" or abi.get("status") != "IMPORTS_RETURNED"
            or abi.get("python") != "3.11.14" or abi.get("package_versions") != expected_packages
            or abi.get("network_attempts") != [] or abi.get("environment_sync") is not False
            or any(type(abi.get(name)) is not int or abi.get(name) != 0 for name in ("native_scientific_models_constructed", "native_scientific_builds", "native_scientific_solves"))
            or abi.get("scope") != "ACTUAL_SELECTED_LOCKED_ABI_IMPORT_ENGINEERING;NOT_NATIVE_SCIENTIFIC_ENTRY_OR_QUALIFICATION"):
        raise ValueError("native observation lacks independently retained selected import-only environment")
    if (sys.version_info[:3] != (3, 11, 14) or abi.get("prefix") != sys.prefix
            or Path(abi.get("interpreter", {}).get("resolved_path", "")) != Path(sys.executable).resolve()
            or any(importlib.metadata.version(name) != version for name, version in expected_packages.items())):
        raise ValueError("native observation changes the actually selected interpreter or installed package metadata")
    if tuple(row["module"] for row in abi.get("requested_imports", ())) != ("numpy", "scipy", "casadi", "pybammsolvers", "pybammsolvers.idaklu", "pybamm"):
        raise ValueError("native observation changes the complete selected native ABI import census")
    for name in ("OPENBLAS_CORETYPE", "NPY_DISABLE_CPU_FEATURES", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        if abi.get("selected_environment", {}).get(name) != os.environ.get(name):
            raise ValueError("native observation changes actually qualified CPU/thread environment")
    if (capacity.get("schema") != "empirical-lawhood/development/battery-host-resource-observation"
            or capacity.get("actual_host") is not True
            or capacity.get("observed_utc") != declaration.resources.observed_utc
            or any(type(capacity.get(name)) is not int for name in ("storage_available_bytes", "memory_available_bytes"))
            or capacity.get("storage_available_bytes") != declaration.resources.storage_available_bytes
            or capacity.get("memory_available_bytes") != declaration.resources.memory_available_bytes
            or capacity.get("declared_storage_root") != declaration.resources.declared_storage_root.to_document()):
        raise ValueError("native observation changes actual declared root/memory availability source")
    loaded, mapped = abi.get("loaded_module_files", ()), abi.get("mapped_file_bindings", ())
    maps = abi.get("process_maps")
    if (not loaded or not mapped or type(maps) is not str
            or sha256(maps.encode()).hexdigest() != abi.get("process_maps_sha256")):
        raise ValueError("native observation omits actual loaded ABI file bindings")
    mapped_paths = {line.split(maxsplit=5)[5] for line in maps.splitlines()
                    if len(line.split(maxsplit=5)) == 6 and line.split(maxsplit=5)[5].startswith("/")}
    if mapped_paths != {row["path"] for row in mapped}:
        raise ValueError("native observation loses the complete actually mapped ABI source census")
    rows = (*loaded, *mapped, abi["interpreter"])
    for requested in abi["requested_imports"]:
        if not any(row.get("module") == requested["module"] and row["path"] == requested["file"]
                   for row in abi["loaded_module_files"]):
            raise ValueError("native observation omits an actually requested ABI module/source-file join")
        if "." not in requested["module"]:
            installed = importlib.metadata.distribution(requested["module"]).locate_file(requested["module"] + "/__init__.py")
            if Path(installed).resolve() != Path(requested["file"]).resolve():
                raise ValueError("native observation substitutes an actually selected package source root")
    checked = {}
    for row in rows:
        selected = row["path"]
        binding = (row["size_bytes"], row["sha256"], row["resolved_path"])
        if selected in checked:
            if checked[selected] != binding:
                raise ValueError("native observation contradicts an original ABI source binding")
            continue
        checked[selected] = binding
        path = Path(selected)
        if (not path.is_file() or path.stat().st_size != row["size_bytes"]
                or str(path.resolve()) != row["resolved_path"]):
            raise ValueError("qualified ABI file is unavailable or changed")
        with path.open("rb") as port:
            actual = file_digest(port, "sha256").hexdigest()
        if actual != row["sha256"]:
            raise ValueError("qualified ABI file bytes have changed")


def _validate_selected_source_inputs(config, protocol, abi_payload):
    """Hash the complete scientific pins, including modules not imported by ABI smoke."""
    abi = json.loads(abi_payload)
    roots = {row["module"]: Path(row["file"]).parent for row in abi["requested_imports"] if row["module"] in {"pybamm", "scipy"}}
    if set(roots) != {"pybamm", "scipy"} or not set(PREPARATION_SOURCE_MEMBERS).issubset(protocol.source_members):
        raise ValueError("observation omits selected complete scientific source roots/pins before contact")
    selected = (*config.source.source_members, *protocol.source_members)
    by_member = {}
    for member, expected in selected:
        if member in by_member and by_member[member] != expected:
            raise ValueError("observation contradicts a selected scientific source pin")
        by_member[member] = expected
    for member, expected in by_member.items():
        path = roots["scipy"] / member.removeprefix("scipy/") if member.startswith("scipy/") else roots["pybamm"] / member
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("selected observation scientific source pin changed before contact: " + member)


def acquire_observation(observation, method_index, *, protocol, provenance, definition, native_subwork, entry_declaration, abi_payload=None, resource_payload=None, inputs=None):
    """A declared observation only; completed recovery has no native effects."""
    config = _validate_operands(observation, method_index, protocol, provenance, definition, native_subwork, entry_declaration)
    recovered = native_subwork.recover(definition)
    if recovered is not None:
        return SegmentedNativeResult(None, protocol, None, None, None, None, None, None, None, recovered, True)
    _validate_entry_sources(entry_declaration, abi_payload, resource_payload)
    _validate_selected_source_inputs(config, protocol, abi_payload)
    entry = native_subwork.begin(definition, inputs)
    native_subwork.contact(entry)
    wall, cpu = time.monotonic(), time.process_time()
    declaration_bytes = sum(passive._publish(native_subwork, entry, name, record).materialization.size_bytes
        for name, record in (("observation-protocol", observation), ("entry-declaration", entry_declaration)))
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
                        if raw_clocks[-1] >= observation.minimum_observation_clock_s:
                            next_control = None
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
    retained = chain.retained_bytes + declaration_bytes
    for name, record in records.items():
        if record is not None:
            retained += passive._publish(native_subwork, entry, name, record).materialization.size_bytes
    complete = error is None and all(record is not None for record in records.values())
    inspection = native_subwork.complete(entry,
        operational_status=OperationalStatus.SUCCEEDED if complete else OperationalStatus.FAILED,
        cost=InquiryCost(passive._decimal(time.process_time() - cpu), passive._decimal(time.monotonic() - wall), D(retained)),
        cost_scope="declared initial-window observation only, including native segments/full output custody; do not sum nested costs; payload bytes exclude manifests/receipts/control records; not full forecast",
        consumed_streams=definition.streams, peak_rss_bytes=trace.process_peak_rss_bytes,
        reason_codes=() if complete else ("segmented-return-or-capture-incomplete",))
    return SegmentedNativeResult(trace, protocol, assignment, layout, **boundary, inspection=inspection)


def observation_result(observation, method_index, result, definition, entry_declaration):
    config = observation.configurations[method_index]
    evidence = se.evidence_from_result(config, result)
    clocks = tuple(row.native_times_s[-1] for row in evidence.trace.segments if row.native_times_s)
    last = clocks[-1] if clocks else None
    disposition = ("TECHNICAL_FAILURE" if evidence.trace.disposition == "TECHNICAL_FAILURE" else
                   "OBSERVATION_WINDOW_COMPLETED" if last is not None and last >= observation.minimum_observation_clock_s else
                   "PHYSICAL_TERMINATION_BEFORE_OBSERVATION_WINDOW")
    return oc.PreparationObservationResult("result." + config.config_id, observation, method_index, evidence, definition, entry_declaration,
        disposition, last, len(evidence.trace.segments), observation.original_entry_disposition)
