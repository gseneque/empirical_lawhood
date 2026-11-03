# SPDX-License-Identifier: MPL-2.0
"""Exposed passive capture and real AR3 custody; no battery solve or admission."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native as native
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquiryInitializerAttempt
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_contracts import (
    ObservationKind, PreparationProtocol,
)
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_science import PREPARATION_SOURCE_MEMBERS
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from tests.runtime_platform.test_native_subwork import _plane, _process_context, _store
from tests.test_battery_refined_inquiry import exposed, selected as exposed_selection

selected = exposed_selection

D = Decimal


@pytest.fixture
def custody(tmp_path, selected):
    source, policy = selected
    config = next(row for row in science.configurations(source, policy)
                  if row.component_view == "oregan-spme")
    package_sources = (("src/exposed-passive-fixture.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    protocol = PreparationProtocol("protocol.passive-exposed", c.identity(config), c.identity(source), provenance.identity,
        "ORegan2022", "SPMe", 30, 40, config.initial_temperature_k, PREPARATION_SOURCE_MEMBERS)
    plane = _plane(tmp_path / "exposed-custody")
    manifests = []
    for name, record in ((config.config_id, config), (source.source_id, source),
                         (protocol.protocol_id, protocol), (provenance.identity.object_id, provenance)):
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.passive.inputs", "inputs",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
        manifests.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda row: row.materialization.materialization_id))
    parent = NativeEffectContact("exposed.passive", "battery.forecast", "exposed.passive.battery.forecast.attempt-001",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("battery.forecast", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        provenance.observed_git_head, tuple(row.materialization.materialization_id for row in manifests), ())
    store = _store(plane, parent, manifests)
    store.parent_contacts.begin(parent)
    definition = native.build_forecast_definition(config, protocol, provenance, store, parent.input_materialization_ids)
    native.freeze_forecast_roster(store, (definition,))
    return SimpleNamespace(config=config, protocol=protocol, provenance=provenance,
        definition=definition, store=store, inputs=manifests, plane=plane)


class Variable:
    def __init__(self, name, scale=1, children=()):
        self.name, self.scale, self.reference = name, scale, 0
        self.children = children
        self.domains = {"primary": ()}

    def __str__(self):
        return self.name


def model_fixture(protocol):
    nx, nr = protocol.electrode_points, protocol.particle_points
    children = tuple(Variable(name) for name in ("negative electrolyte", "separator electrolyte", "positive electrolyte"))
    specification = (
        ("Discharge capacity [A.h]", 1, 1, ()),
        ("Throughput capacity [A.h]", 1, 1, ()),
        ("X-averaged negative particle concentration [mol.m-3]", nr, 29583, ()),
        ("X-averaged positive particle concentration [mol.m-3]", nr, 51765, ()),
        ("Porosity times concentration [mol.m-3]", 3 * nx, 1000, children),
        ("Volume-averaged cell temperature [K]", 1, 298.15, ()),
        ("Current variable [A]", 1, 5, ()),
    )
    rhs, algebraic, initial, slices = {}, {}, {}, {}
    cursor = 0
    for index, (name, count, scale, aliases) in enumerate(specification):
        variable = Variable(name, scale, aliases)
        (rhs if index < 6 else algebraic)[variable] = "exposed equation: " + name
        initial[variable] = "exposed initial: " + name
        slices[variable] = [slice(cursor, cursor + count)]
        for i, alias in enumerate(aliases):
            slices[alias] = [slice(cursor + i * nx, cursor + (i + 1) * nx)]
        cursor += count
    values = (0.0, 0.0) + (.35,) * nr + (.65,) * nr + (.25,) * nx + (.47,) * nx + (.335,) * nx + (float(protocol.initial_temperature_k) / 298.15, 1.0)
    return SimpleNamespace(name="exposed full model", rhs=rhs, algebraic=algebraic,
        initial_conditions=initial, y_slices=slices, len_rhs=cursor - 1, len_alg=1,
        len_rhs_and_alg=cursor, requested=np.asarray(values).reshape(-1, 1), y0_list=[])


def solution_fixture(values, *, derivative=True, terminal_time=1.0):
    first = np.asarray(values, dtype=float).reshape(-1)
    last = first.copy()
    last[0] -= .01
    ys = np.column_stack((first, last))
    return SimpleNamespace(termination="exposed return", variables_returned=False,
        all_ys=[ys], all_ts=[np.array([0.0, terminal_time])],
        all_yps=[np.full_like(ys, .0123)] if derivative else None)


def backend_fixture(custody, *, derivative=True, fail_first=True):
    effects = []
    model = model_fixture(custody.protocol)
    parameters = {
        "Initial concentration in negative electrode [mol.m-3]": 28866.0,
        "Initial concentration in positive electrode [mol.m-3]": 13975.0,
        "Reference temperature [K]": 298.15,
        "Lower voltage cut-off [V]": 2.5, "Upper voltage cut-off [V]": 4.2,
    }

    def observe_effect(kind):
        rows = tuple(custody.store.iter_rosters(custody.store.parent_contact))
        latest = max((definition for roster in rows for definition in custody.store.iter_roster_definitions(roster.parent_contact, roster.roster_id)),
                     key=lambda row: int(row.subwork_id.rsplit(".", 1)[-1]) if ".call." in row.subwork_id else 0)
        inspection = custody.store.inspect(latest)
        assert inspection.state is NativeSubworkState.UNKNOWN_COMPLETION
        effects.append((kind, latest.configuration, inspection.contact))

    class Solver:
        def __init__(self, fail=False):
            self.fail = fail

        def to_config(self):
            return {"type": "exposed solver", "fail": self.fail, "rtol": 1e-7}

        def solve(self, model, t_eval, inputs=None):
            observe_effect("initializer")
            if self.fail:
                raise ValueError("exposed backend failure")
            return solution_fixture([.11, .91], derivative=False)

        def _set_initial_conditions(self, model, time, inputs):
            model.y0_list = [model.requested.copy()]

        def step(self, old_solution, model, dt, inputs=None, save=True):
            observe_effect("charging")
            if old_solution is None:
                self._set_initial_conditions(model, 0.0, [inputs or {}])
            values = model.requested.copy()
            values[-1, 0] = -.291  # actual algebraic initialization differs from the request
            return solution_fixture(values, derivative=derivative)

    class SOH:
        known_value = "cyclable lithium capacity"
        parameter_values = parameters

        def solve(self, inputs, direction=None):
            attempt_model = SimpleNamespace(name="exposed eSOH", algebraic={}, initial_conditions={})
            if fail_first:
                try:
                    Solver(True).solve(attempt_model, [0], inputs=inputs)
                except ValueError:
                    pass
            Solver().solve(attempt_model, [0], inputs=inputs)
            return {"Q_Li": 7.0, "Q_n": 6.0, "Q_p": 8.0, "Q": 4.0,
                    "x_0": .1, "x_100": .9, "y_0": .8, "y_100": .2}

    class Simulation:
        _model = model
        _unprocessed_parameter_values = parameters

        def set_initial_state(self, initial_soc, direction=None, inputs=None):
            SOH().solve({"Q_n": 6.0, "Q_p": 8.0, "Q_Li": 7.0}, direction)
            self._parameter_values = {**parameters,
                "Initial concentration in negative electrode [mol.m-3]": 10354.05,
                "Initial concentration in positive electrode [mol.m-3]": 33647.25}

    return SimpleNamespace(BaseSolver=Solver, Simulation=Simulation,
        lithium_ion=SimpleNamespace(ElectrodeSOHSolver=SOH),
        constants=SimpleNamespace(F=SimpleNamespace(value=96485.33212331001)),
        settings=SimpleNamespace(tolerances={"U__c_s": 1e-10}, min_max_mode="exact")), model, effects


def _entry_capture(custody):
    entry = custody.store.begin(custody.definition, custody.inputs)
    custody.store.contact(entry)
    chain = native._EffectChain(custody.store, entry, custody.protocol, custody.inputs)
    return native._Capture(custody.protocol, chain, entry)


def test_actual_fallbacks_request_before_contact_and_full_state_capture(custody):
    backend, model, effects = backend_fixture(custody)
    capture = _entry_capture(custody)
    original_solve = backend.BaseSolver.solve
    original_step = backend.BaseSolver.step
    with native.observe_native_calls(backend, capture):
        backend.Simulation().set_initial_state(.30, inputs={"active current": 1.455})
        backend.BaseSolver().step(None, model, 180000.0, inputs={"active current": 1.455}, save=False)
    capture.chain.finish()
    assert backend.BaseSolver.solve is original_solve and backend.BaseSolver.step is original_step
    assert [row[0] for row in effects] == ["initializer", "initializer", "charging"]
    assert capture.initializer_dispositions == ["TECHNICAL_FAILURE", "RETURNED"]
    assert capture.chain.completed_calls == 3
    calls = sorted((definition for roster in custody.store.iter_rosters(custody.store.parent_contact)
                    for definition in custody.store.iter_roster_definitions(roster.parent_contact, roster.roster_id)
                    if ".call." in definition.subwork_id), key=lambda row: row.subwork_id)
    assert all(custody.store.inspect(row).state is NativeSubworkState.COMPLETED for row in calls)
    assert capture.layout.differential_count == 173 and capture.layout.algebraic_count == 1
    assert len(capture.requested_initial.scaled_values) == len(capture.actual_initial.scaled_values) == 174
    assert capture.requested_initial.scaled_values[-1] == D(1)
    assert capture.actual_initial.scaled_values[-1] == D("-.291")
    assert capture.initial_derivative.kind is ObservationKind.OBSERVED
    assert len(capture.initial_derivative.scaled_values) == 174
    assert capture.actual_terminal.model_clock_s == 1
    manifest = capture.forecast_entry.outputs["native.request.first"]
    request_record = decode_canonical_bytes(custody.plane.root.resolve(manifest.materialization.relative_path,
        for_write=False).read_bytes(), native.NativeRequest, maximum_bytes=None)
    request = json.loads(request_record.primitive_json)
    assert request["esoh_request"]["soc_assignment_request"]["initial_soc"] == {"binary64": (.30).hex()}
    assert request["esoh_request"]["inputs"]["Q_Li"] == {"binary64": (7.0).hex()}
    witness = native._witness(capture)
    assert witness.usable_capacity_ah == 4 and witness.assigned_negative_concentration == D("10354.05")
    assert witness.pre_soc_negative_concentration == 28866
    assert witness.initializer_dispositions == ("TECHNICAL_FAILURE", "RETURNED")
    first = custody.store.inspect(calls[0])
    assert first.completion.operational_status.value == "FAILED"
    manifest = next(row for row in first.outputs if row.logical.payload_schema == native.NativeReturn.SCHEMA)
    returned = decode_canonical_bytes(custody.plane.root.resolve(manifest.materialization.relative_path,
        for_write=False).read_bytes(), native.NativeReturn, maximum_bytes=None)
    assert returned.error_message == "exposed backend failure"


def test_path_free_worker_uses_actual_conditional_request_materializations(custody, tmp_path, monkeypatch):
    context = _process_context(custody.store, custody.definition, custody.inputs)
    service = NativeSubworkPipeService(custody.store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message

        def recv(self):
            return self.reply
    progress = PipeNativeSubworkProgress(Connection())
    backend, model, effects = backend_fixture(custody, fail_first=False)
    monkeypatch.setitem(sys.modules, "pybamm", backend)
    monkeypatch.setattr(native, "_validate_source_pins", lambda backend, protocol: None)
    def fake_core(config, **kwargs):
        backend.Simulation().set_initial_state(.30)
        backend.BaseSolver().step(None, model, 180000.0)
        return exposed(config)
    monkeypatch.setattr(native, "acquire_with_numerics", fake_core)
    try:
        result = native.acquire_prepared(custody.config, protocol=custody.protocol, provenance=custody.provenance,
            definition=custody.definition, native_subwork=progress)
        assert result.inspection.receipt and len(effects) == 2
        assert result.inspection.completion.operational_status.value == "SUCCEEDED"
    finally:
        service.close()
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("empty", [None, []])
def test_absent_returned_derivatives_remain_unavailable(custody, empty):
    backend, model, _ = backend_fixture(custody, derivative=False, fail_first=False)
    capture = _entry_capture(custody)
    with native.observe_native_calls(backend, capture):
        backend.Simulation().set_initial_state(.30)
        backend.BaseSolver().step(None, model, 1.0)
    capture.chain.finish()
    observed = native._solution_observation(replace_solution_derivatives(solution_fixture(model.requested), empty))
    assert observed["derivatives"] is None
    assert capture.initial_derivative.kind is ObservationKind.UNAVAILABLE
    assert capture.terminal_derivative.kind is ObservationKind.UNAVAILABLE
    assert not capture.initial_derivative.scaled_values


def replace_solution_derivatives(solution, derivatives):
    solution.all_yps = derivatives
    return solution


def trace_with_initializer_census(config, fail_first=True):
    trace = exposed(config)
    attempts = tuple(BatteryInquiryInitializerAttempt(index + 1, "exposed", "exposed", "{}", "exposed", "0" * 64,
        disposition, "ValueError" if disposition == "TECHNICAL_FAILURE" else None,
        "exposed backend failure" if disposition == "TECHNICAL_FAILURE" else None, D(0), D(0))
        for index, disposition in enumerate(("TECHNICAL_FAILURE", "RETURNED") if fail_first else ("RETURNED",)))
    return replace(trace, initializer_attempts=attempts)


def test_foreign_input_and_unknown_completion_refuse_before_effect(custody, monkeypatch):
    with pytest.raises(ValueError, match="authenticated input bytes"):
        custody.store.begin(replace(custody.definition,
            configuration=replace(custody.definition.configuration, object_fingerprint="a" * 64)), custody.inputs)
    entry = custody.store.begin(custody.definition, custody.inputs)
    custody.store.contact(entry)
    calls = []
    monkeypatch.setattr(native, "acquire_with_numerics", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(NativeSubworkUncertainContact, match="no automatic retry"):
        native.acquire_prepared(custody.config, protocol=custody.protocol, provenance=custody.provenance,
            definition=custody.definition, native_subwork=custody.store, inputs=custody.inputs)
    assert not calls


def test_actual_return_complete_forecast_and_known_recovery(custody, monkeypatch):
    backend, model, effects = backend_fixture(custody)
    monkeypatch.setitem(sys.modules, "pybamm", backend)
    monkeypatch.setattr(native, "_validate_source_pins", lambda backend, protocol: None)
    calls = []
    def fake_core(config, **kwargs):
        calls.append(kwargs)
        backend.Simulation().set_initial_state(.30)
        backend.BaseSolver().step(None, model, 180000.0)
        return trace_with_initializer_census(config)
    monkeypatch.setattr(native, "acquire_with_numerics", fake_core)
    result = native.acquire_prepared(custody.config, protocol=custody.protocol, provenance=custody.provenance,
        definition=custody.definition, native_subwork=custody.store, inputs=custody.inputs)
    records = native.returned_records(result)
    assert len(records) == 10 and records["native-receipt"] is result.inspection.receipt
    assert result.inspection.completion.operational_status.value == "SUCCEEDED"
    assert set(result.inspection.completion.output_ids) == {row.output_id for row in native.forecast_outputs()}
    assert calls[0]["trace_factory"] is c.Trace and calls[0]["charging_attempt_factory"].keywords == {"configuration": custody.config}
    recovered = native.acquire_prepared(custody.config, protocol=custody.protocol, provenance=custody.provenance,
        definition=custody.definition, native_subwork=custody.store, inputs=custody.inputs)
    assert recovered.recovered and recovered.trace is None and len(calls) == 1 and len(effects) == 3
    with pytest.raises(ValueError, match="original returned objects"):
        native.returned_records(recovered)


def test_full_state_and_source_layout_omissions_refuse(custody):
    model = model_fixture(custody.protocol)
    layout = native.observe_processed_layout(model, custody.protocol)
    with pytest.raises(ValueError, match="full differential/algebraic"):
        native.observe_state(model.requested[:-1], 0, "actual-initial", custody.protocol, layout, (custody.definition.identity,))
    electrolyte = next(variable for variable in model.rhs if variable.name.startswith("Porosity times"))
    model.y_slices[electrolyte.children[1]] = [slice(113, 143)]
    with pytest.raises(ValueError, match="electrolyte aliases"):
        native.observe_processed_layout(model, custody.protocol)


def test_custody_failure_prevents_call_and_restores_original_hook(custody, monkeypatch):
    backend, _, effects = backend_fixture(custody)
    capture = _entry_capture(custody)
    original = backend.BaseSolver.solve
    def reject(*args, **kwargs):
        raise ArtifactIdentityConflict("exposed publication rejected")
    monkeypatch.setattr(custody.store, "publish_output", reject)
    with pytest.raises(ArtifactIdentityConflict):
        with native.observe_native_calls(backend, capture):
            backend.Simulation().set_initial_state(.30)
    assert capture.chain.fatal is not None and not effects and backend.BaseSolver.solve is original


def test_esoh_failure_before_backend_retains_actual_request_and_error(custody, monkeypatch):
    backend, _, effects = backend_fixture(custody)
    capture = _entry_capture(custody)
    def fail(solver, inputs, direction=None):
        assert "esoh.request" in capture.forecast_entry.outputs
        raise ValueError("exposed eSOH source error before backend")
    monkeypatch.setattr(backend.lithium_ion.ElectrodeSOHSolver, "solve", fail)
    with pytest.raises(ValueError, match="eSOH source error"):
        with native.observe_native_calls(backend, capture):
            backend.Simulation().set_initial_state(.30)
    capture.chain.finish()
    manifest = capture.forecast_entry.outputs["esoh.return"]
    returned = decode_canonical_bytes(custody.plane.root.resolve(manifest.materialization.relative_path,
        for_write=False).read_bytes(), native.ElectrodeSOHReturn, maximum_bytes=None)
    assert returned.disposition == "TECHNICAL_FAILURE" and not effects
    assert returned.error_message == "exposed eSOH source error before backend"
    assert native._witness(capture) is None and capture.chain.ordinal == 0


def test_actual_native_source_pin_mismatch_refuses(custody, tmp_path, monkeypatch):
    root = tmp_path / "exposed-pybamm"
    name = PREPARATION_SOURCE_MEMBERS[0][0]
    path = root / name
    path.parent.mkdir(parents=True)
    path.write_bytes(b"changed exposed source bytes")
    monkeypatch.setitem(sys.modules, "scipy", SimpleNamespace(__file__=str(tmp_path / "exposed-scipy" / "__init__.py")))
    with pytest.raises(ValueError, match="actual preparation native source pin differs"):
        native._validate_source_pins(SimpleNamespace(__file__=str(root / "__init__.py")), custody.protocol)


def test_passive_native_owner_import_is_cold():
    code = '''
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm', 'pybammsolvers'}:
            raise AssertionError('native import attempted: ' + fullname)
sys.meta_path.insert(0, Block())
from empirical_lawhood.adapters.methods.battery_refined_inquiry.prepared_native import forecast_outputs
assert len(forecast_outputs()) == 12
'''
    completed = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
