# SPDX-License-Identifier: MPL-2.0
"""Exposed bounded-method fixtures with real custody; no battery acquisition."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as native
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_contracts import ObservationKind, PreparationProtocol
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_science import PREPARATION_SOURCE_MEMBERS
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_contracts import SegmentedMethodProtocol, SegmentedNativeConfig
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import assess_source_roots, supply_source_roots
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_battery_prepared_native import model_fixture
from tests.test_battery_refined_inquiry import exposed as exposed_fixture, selected as selected_fixture

selected = selected_fixture
exposed = exposed_fixture
D = Decimal


@pytest.fixture
def custody(tmp_path, selected, request):
    source, policy = selected
    old_config = next(row for row in science.configurations(source, policy)
        if row.component_view == "oregan-spme")
    preparation = supply_source_roots(c.identity(source), "ORegan2022")
    assessment = assess_source_roots(preparation)
    horizon = getattr(request, "param", D(60))
    method = SegmentedMethodProtocol("method.exposed." + str(horizon) + "s", horizon)
    config = SegmentedNativeConfig("config.exposed.source-derived." + str(horizon) + "s", old_config, preparation, assessment, method)
    package_sources = (("src/exposed-segment-fixture.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    protocol = PreparationProtocol("protocol.segment-exposed", c.identity(config), c.identity(source), provenance.identity,
        "ORegan2022", "SPMe", 30, 40, config.initial_temperature_k, PREPARATION_SOURCE_MEMBERS)
    plane = _plane(tmp_path / "exposed-segment-custody")
    records = ((config.config_id, config), (source.source_id, source), (protocol.protocol_id, protocol),
        (provenance.identity.object_id, provenance), (preparation.preparation_id, preparation),
        (assessment.assessment_id, assessment), (method.method_id, method))
    manifests = []
    for name, record in records:
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.segment.inputs", "inputs", record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda row: row.materialization.materialization_id))
    parent = NativeEffectContact("exposed.segment", "battery.forecast", "exposed.segment.battery.forecast.attempt-001",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("battery.forecast", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        provenance.observed_git_head, tuple(row.materialization.materialization_id for row in manifests), ())
    store = _store(plane, parent, manifests)
    store.parent_contacts.begin(parent)
    definition = native.build_forecast_definition(config, protocol, provenance, store, parent.input_materialization_ids)
    native.freeze_forecast_roster(store, (definition,))
    return SimpleNamespace(config=config, protocol=protocol, provenance=provenance,
        definition=definition, store=store, inputs=manifests, plane=plane)


class Solution:
    def __init__(self, clocks, states, model, inputs, *, termination="final time", all_yps=None, options=None):
        self.all_ts, self.all_ys, self.all_models, self.all_inputs = [np.asarray(clocks)], [np.asarray(states)], [model], [inputs]
        self.termination, self.all_yps, self.user_options = termination, None if all_yps is None else [np.asarray(all_yps)], options or {}
        self.variables_returned, self._all_sensitivities = False, {}

    @property
    def t(self):
        return self.all_ts[0]

    def __getitem__(self, name):
        rows = {"Discharge capacity [A.h]": self.all_ys[0][0], "Current [A]": self.all_ys[0][-1] * 5,
            "Voltage [V]": np.linspace(3.7, 4.2, len(self.t)),
            "Volume-averaged cell temperature [K]": self.all_ys[0][-2] * 298.15,
            "Ambient temperature [K]": np.full(len(self.t), self.chamber)}
        return lambda clocks: np.interp(clocks, self.t, rows[name])


def exposed_backend(custody, monkeypatch, *, derivatives="returned", fail_at=None, malformed=False, bad_bits=None):
    effects = []
    model = model_fixture(custody.protocol)

    class SOH:
        def solve(self, *args, **kwargs):
            raise AssertionError("exposed method must not contact native eSOH")

    class Solver:
        def to_config(self):
            return {"solver": "EXPOSED;NO_NATIVE_ACQUISITION", "rtol": 1e-7}

        def _set_consistent_initialization(self, built, clock, inputs):
            built.y0_list[0][-1, 0] = -inputs[0][native.original.ACTIVE_CURRENT_INPUT] / 5

        def step(self, previous, built, horizon, inputs=None, save=True):
            ordinal = len(effects) + 1
            definition = next(row for roster in custody.store.iter_rosters(custody.store.parent_contact)
                for row in custody.store.iter_roster_definitions(roster.parent_contact, roster.roster_id)
                if row.subwork_id.endswith(".segment." + str(ordinal)))
            inspection = custody.store.inspect(definition)
            assert inspection.state is NativeSubworkState.UNKNOWN_COMPLETION
            if effects:
                assert custody.store.inspect(effects[-1][0]).state is NativeSubworkState.COMPLETED
            effects.append((definition, inspection.contact))
            if fail_at == ordinal:
                raise RuntimeError("exposed backend error before initialization")
            if previous is None:
                start, requested = 0.0, model.requested.copy()
            else:
                assert previous.termination == "final time"
                assert previous.all_ys[0].shape[1] == 1
                start, requested = float(previous.t[-1]), previous.all_ys[0].copy()
            shifted = start if start == 0 else np.nextafter(start, np.inf)
            built.y0_list = [requested]
            self._set_consistent_initialization(built, shifted, [inputs])
            end = start + horizon
            termination = "final time"
            if ordinal == 2:
                end, termination = start + horizon / 2 + .25, "event: " + native.TIER_EVENT
            elif ordinal == 3:
                end, termination = start + horizon / 2, "event: " + native.TARGET_EVENT
            clocks = np.array([shifted, (shifted + end) / 2, end])
            states = np.repeat(built.y0_list[0], len(clocks), axis=1)
            states[0] = np.linspace(float(requested[0, 0]), -2.5 if ordinal == 3 else -.1 * ordinal, len(clocks))
            if ordinal == 2:
                states[-2] = np.linspace(states[-2, 0], inputs[native.original.TIER_THRESHOLD_INPUT] / 298.15, len(clocks))
            if malformed:
                states = states[:-1]
            if bad_bits is not None:
                states.view(np.uint64)[2, 1] = bad_bits
            returned_derivatives = np.full_like(states, .0123) if derivatives == "returned" else None
            solution = Solution(clocks, states, model, inputs, termination=termination, all_yps=returned_derivatives)
            if derivatives == "empty":
                solution.all_yps = []
            solution.chamber = float(custody.config.chamber_temperature_k)
            return solution

    backend = SimpleNamespace(BaseSolver=Solver, Solution=Solution, lithium_ion=SimpleNamespace(ElectrodeSOHSolver=SOH),
        __file__=str(Path.cwd() / ".venv/lib/python3.11/site-packages/pybamm/__init__.py"))
    solver = Solver()

    def build(config, protocol, selected_backend):
        assert selected_backend is backend
        parameters = {"Initial concentration in negative electrode [mol.m-3]": 28866.,
            "Initial concentration in positive electrode [mol.m-3]": 13975.}
        assignment = native.assign_source_parameters(parameters, config, protocol)
        delivery = native.BatteryInquiryDelivery(native.CONTROL_RULE, D("4.2"), D("4.2"),
            config.chamber_temperature_k, config.chamber_temperature_k, D(0), None,
            "exposed control", "exposed applied control", "exposed I", "exposed V", "exposed chamber", None, None, None)
        return model, solver, delivery, assignment, (native.TARGET_EVENT, native.TIER_EVENT), ("exposed target", "exposed tier")

    monkeypatch.setitem(sys.modules, "pybamm", backend)
    monkeypatch.setattr(native, "build_runtime", build)
    monkeypatch.setattr(native.passive, "_validate_source_pins", lambda *_: None)
    return backend, solver, effects


def acquire(custody):
    return native.acquire_segmented(custody.config, protocol=custody.protocol, provenance=custody.provenance,
        definition=custody.definition, native_subwork=custody.store, inputs=custody.inputs)


def read_output(custody, summary, name, record_type):
    definition = next(row for roster in custody.store.iter_rosters(custody.store.parent_contact)
        for row in custody.store.iter_roster_definitions(roster.parent_contact, roster.roster_id)
        if row.subwork_id.endswith(".segment." + str(summary.segment_index)))
    inspection = custody.store.inspect(definition)
    materialization = next(row for row in inspection.receipt.output_materializations
        if row.logical_artifact_id.endswith("." + name))
    return decode_canonical_bytes(custody.plane.root.resolve(materialization.relative_path, for_write=False).read_bytes(),
        record_type, maximum_bytes=materialization.size_bytes)


def test_complete_segments_have_immediate_receipts_and_full_arrays(custody, monkeypatch):
    backend, solver, effects = exposed_backend(custody, monkeypatch)
    original = backend.BaseSolver._set_consistent_initialization
    result = acquire(custody)
    assert result.trace.disposition == "TARGET_REACHED", result.trace.error_message
    assert result.trace.backend_solve_calls == len(effects) == 3
    assert backend.BaseSolver._set_consistent_initialization is original
    assert result.trace.native_initializer_contacts == 0
    assert len(result.trace.transitions) == 1
    assert tuple(row.regime for row in result.trace.segments) == ("LOW", "LOW", "HIGH")
    assert result.trace.segments[1].native_times_s[0] == D(str(np.nextafter(60., np.inf)))
    assert result.trace.times_s[0] == 0 and result.trace.times_s[-1] == D("120.25")
    assert all(D(clock) in result.trace.times_s for clock in range(121))
    for summary in result.trace.segments:
        full = read_output(custody, summary, "full-state", native.FullStateSegment)
        raw_return = read_output(custody, summary, "raw-return", native.RawReturnedSegment)
        assert c.identity(custody.config) == summary.configuration
        assert full.fingerprint() == summary.full_state.object_fingerprint
        assert full.raw_return.object_fingerprint == raw_return.fingerprint() == summary.raw_return.object_fingerprint
        assert raw_return.state_blocks[0].bytes_hex == np.asarray([float.fromhex(bits) for bits in full.blocks[0].state_binary64], dtype="<f8").tobytes().hex()
        assert full.returned_model_expression_sha256 == (result.layout.model_expression_sha256,)
        assert len(full.blocks) == 1 and full.blocks[0].state_rows == 174
        assert len(full.blocks[0].state_binary64) == len(full.blocks[0].derivative_binary64) == 174 * 3
        assert tuple(D(str(float.fromhex(value))) for value in full.blocks[0].clock_binary64) == summary.native_times_s
        assert summary.native_receipt.object_fingerprint
        definition = custody.store.resolve_completed_definition(summary.native_definition)
        assert definition.identity == summary.native_definition
        assert custody.store.recover(definition).receipt.fingerprint() == summary.native_receipt.object_fingerprint
    assert result.requested_initial.scaled_values[-1] != result.actual_initial.scaled_values[-1]
    assert native.returned_records(result)["native-receipt"] == result.inspection.receipt
    recovered = acquire(custody)
    assert recovered.recovered and len(effects) == 3
    with pytest.raises(ValueError, match="original records"):
        native.returned_records(recovered)


@pytest.mark.parametrize("derivatives", ("none", "empty"))
def test_unreturned_derivatives_remain_unavailable(custody, monkeypatch, derivatives):
    exposed_backend(custody, monkeypatch, derivatives=derivatives)
    result = acquire(custody)
    assert result.trace.disposition == "TARGET_REACHED", result.trace.error_message
    assert result.initial_derivative.kind is result.terminal_derivative.kind is ObservationKind.UNAVAILABLE
    for summary in result.trace.segments:
        assert read_output(custody, summary, "full-state", native.FullStateSegment).blocks[0].derivative_binary64 is None
        raw_return = read_output(custody, summary, "raw-return", native.RawReturnedSegment)
        assert raw_return.derivative_blocks == (() if derivatives == "empty" else None)


def test_actual_return_survives_malformed_state_without_next_contact(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch, malformed=True)
    result = acquire(custody)
    assert result.trace.disposition == "TECHNICAL_FAILURE" and len(effects) == 1
    summary = result.trace.segments[0]
    assert summary.full_state is None
    raw_return = read_output(custody, summary, "raw-return", native.RawReturnedSegment)
    assert summary.raw_return.object_fingerprint == raw_return.fingerprint()
    assert raw_return.state_blocks[0].shape == (173, 3)
    assert len(raw_return.state_blocks[0].bytes_hex) == 173 * 3 * 8 * 2
    returned = read_output(custody, summary, "native.return", native.SegmentReturn)
    assert returned.disposition == "RETURNED"
    assert result.inspection.receipt.operational_status.value == "FAILED"


@pytest.mark.parametrize("bad_bits", (0x7FF8000000001234, 0x7FF0000000000000, 0xFFF0000000000000))
def test_nonfinite_native_return_keeps_exact_raw_ieee_bits(custody, monkeypatch, bad_bits):
    _, _, effects = exposed_backend(custody, monkeypatch, bad_bits=bad_bits)
    result = acquire(custody)
    assert result.trace.disposition == "TECHNICAL_FAILURE" and len(effects) == 1
    summary = result.trace.segments[0]
    assert summary.full_state is None and summary.raw_return is not None
    raw_return = read_output(custody, summary, "raw-return", native.RawReturnedSegment)
    values = np.frombuffer(bytes.fromhex(raw_return.state_blocks[0].bytes_hex), dtype=raw_return.state_blocks[0].dtype).view(np.uint64)
    assert int(values[2 * 3 + 1]) == bad_bits
    assert read_output(custody, summary, "native.return", native.SegmentReturn).disposition == "RETURNED"


def test_failed_restart_retains_missing_right_state_and_tier_denominator(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch, fail_at=3)
    result = acquire(custody)
    assert result.trace.disposition == "TECHNICAL_FAILURE" and len(effects) == 3
    assert len(result.trace.transitions) == 1
    transition = result.trace.transitions[0]
    assert transition.right_requested is transition.right_initial is None
    assert transition.right_receivers == ()
    summary = result.trace.segments[-1]
    returned = read_output(custody, summary, "native.return", native.SegmentReturn)
    assert returned.disposition == "TECHNICAL_FAILURE" and summary.native_times_s == ()


def test_uncertain_forecast_refuses_before_import_or_effect(custody, monkeypatch):
    entry = custody.store.begin(custody.definition, custody.inputs)
    custody.store.contact(entry)
    monkeypatch.delitem(sys.modules, "pybamm", raising=False)
    with pytest.raises(NativeSubworkUncertainContact):
        acquire(custody)
    assert "pybamm" not in sys.modules


def test_source_assignment_recomputes_assessment_and_preserves_stock(custody):
    parameters = {"Initial concentration in negative electrode [mol.m-3]": 28866.,
        "Initial concentration in positive electrode [mol.m-3]": 13975.}
    assignment = native.assign_source_parameters(parameters, custody.config, custody.protocol)
    assert assignment.native_initializer_contacts == 0
    assert assignment.pre_soc_negative_concentration == D(28866)
    assert assignment.assigned_negative_concentration == custody.config.preparation.assigned_negative_concentration
    wrong = replace(custody.config.preparation_assessment, assessment_id="assessment.forged")
    with pytest.raises(ValueError, match="authentic independently assessed"):
        native.assign_source_parameters(parameters, replace(custody.config, preparation_assessment=wrong), custody.protocol)


def test_full_native_payload_refuses_omitted_or_nonfinite_components(custody):
    with pytest.raises(ValueError, match="omits state components"):
        native.FullStateBlock((0.0.hex(), 1.0.hex()), 3, (0.0.hex(),) * 5, None)
    with pytest.raises(ValueError, match="nonfinite"):
        native.FullStateBlock((0.0.hex(),), 1, (float("inf").hex(),), None)


def test_failed_output_custody_retains_unknown_forecast_and_refuses_replay(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch)
    original = custody.store.publish_output

    def refused(entry, name, *args, **kwargs):
        if name == "full-state":
            raise ValueError("exposed custody refusal")
        return original(entry, name, *args, **kwargs)

    monkeypatch.setattr(custody.store, "publish_output", refused)
    with pytest.raises(native._CustodyFailure):
        acquire(custody)
    assert len(effects) == 1
    assert custody.store.inspect(custody.definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    with pytest.raises(NativeSubworkUncertainContact):
        acquire(custody)
    assert len(effects) == 1


def test_changed_builder_uses_source_assignment_and_initial_soc_none(custody):
    calls = []

    class Symbol:
        def __init__(self, value):
            self.value = str(value)

        def __str__(self):
            return self.value

        def __add__(self, other):
            return Symbol(f"({self}+{other})")

        def __sub__(self, other):
            return Symbol(f"({self}-{other})")

        def __mul__(self, other):
            return Symbol(f"({self}*{other})")

        def __truediv__(self, other):
            return Symbol(f"({self}/{other})")

        def __neg__(self):
            return Symbol(f"(-{self})")

    event_type = object()

    def event(name, expression, kind):
        return SimpleNamespace(name=name, expression=expression, event_type=kind)

    names = ("Current [A]", "Voltage [V]", "Discharge capacity [A.h]", "Volume-averaged cell temperature [K]")
    model = SimpleNamespace(variables={name: Symbol(name) for name in names}, default_submesh_types={},
        events=[event("Maximum voltage [V]", Symbol("old max"), event_type), event("Minimum voltage [V]", Symbol("old min"), event_type)])
    parameters = {"Initial concentration in negative electrode [mol.m-3]": 28866.,
        "Initial concentration in positive electrode [mol.m-3]": 13975.}
    built = model_fixture(custody.protocol)
    built.get_processed_variable = lambda name: Symbol("processed " + name)

    class Simulation:
        def __init__(self, requested_model, **kwargs):
            assert requested_model is model
            calls.append(("simulation", kwargs))
            self.built_model = built

        def build(self, *, initial_soc, inputs):
            assert initial_soc is None
            assert parameters["Initial concentration in negative electrode [mol.m-3]"] == float(custody.config.preparation.assigned_negative_concentration)
            built.events = model.events
            calls.append(("build", initial_soc, inputs))

    class SOH:
        def solve(self, *args, **kwargs):
            raise AssertionError("no native eSOH call belongs to source-derived builder")

    backend = SimpleNamespace(__version__=native.SOURCE_VERSION,
        settings=SimpleNamespace(min_max_mode="exact", heaviside_smoothing="exact"),
        Scalar=Symbol, InputParameter=Symbol, minimum=lambda a, b: Symbol(f"min({a},{b})"),
        lithium_ion=SimpleNamespace(SPMe=lambda **kwargs: model, DFN=lambda **kwargs: model, ElectrodeSOHSolver=SOH),
        Event=event, EventType=SimpleNamespace(TERMINATION=event_type), ParameterValues=lambda name: parameters,
        IDAKLUSolver=lambda **kwargs: SimpleNamespace(settings=kwargs), MeshGenerator=lambda *args: args,
        Exponential1DSubMesh=object(), Simulation=Simulation)
    original = SOH.solve
    with native.forbid_native_esoh(backend):
        runtime = native.build_runtime(custody.config, custody.protocol, backend)
        with pytest.raises(ValueError, match="forbids native eSOH"):
            SOH().solve({})
    assert SOH.solve is original
    assert runtime[0] is built and runtime[3].native_initializer_contacts == 0
    assert native.TIER_EVENT in runtime[4] and native.TARGET_EVENT in runtime[4]
    assert "Maximum voltage [V]" not in runtime[4]
    assert calls[-1][0] == "build" and calls[-1][1] is None


@pytest.mark.parametrize("custody", (D(30), D(15)), indirect=True)
def test_half_and_quarter_windows_are_changed_effect_operands(custody, monkeypatch):
    _, _, effects = exposed_backend(custody, monkeypatch)
    result = acquire(custody)
    assert result.trace.disposition == "TARGET_REACHED", result.trace.error_message
    assert len(effects) == 3
    assert all(row.requested_horizon_s == custody.config.method.maximum_segment_horizon_s for row in result.trace.segments)
    assert result.trace.segments[0].native_times_s[-1] == custody.config.method.maximum_segment_horizon_s
    for summary in result.trace.segments:
        assert all(clock in result.trace.times_s for clock in summary.native_times_s)
    assert all(D(clock) in result.trace.times_s for clock in range(int(result.trace.times_s[-1]) + 1))


def test_foreign_protocol_refuses_before_effect_or_import(custody, monkeypatch):
    monkeypatch.delitem(sys.modules, "pybamm", raising=False)
    foreign = replace(custody.protocol, configuration=c.identity(custody.config.native))
    with pytest.raises(ValueError, match="frozen configuration"):
        native.acquire_segmented(custody.config, protocol=foreign, provenance=custody.provenance,
            definition=custody.definition, native_subwork=custody.store, inputs=custody.inputs)
    assert custody.store.inspect(custody.definition).state is NativeSubworkState.NOT_ENTERED
    assert "pybamm" not in sys.modules


def test_segmented_owner_import_is_cold():
    result = subprocess.run([sys.executable, "-c",
        "import sys; from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as n; "
        "assert 'pybamm' not in sys.modules; assert 'flint' not in sys.modules; assert len(n.forecast_outputs()) == 10"],
        check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
