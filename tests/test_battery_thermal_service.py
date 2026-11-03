"""Exposed software falsifiers, with zero source-native contacts."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import (
    BatteryThermalConfig, BatteryThermalTrace, EVENTS, PROTOCOL_SHA256,
)
from empirical_lawhood.adapters.methods.battery_thermal_service.examples import thermal_service_draft
from empirical_lawhood.adapters.methods.battery_thermal_service.executable_binding import operation_manifests, operation_registrations, output_codecs
from empirical_lawhood.adapters.methods.battery_thermal_service.science import assess
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

D = Decimal


def _trace(word="standard-cc900"):
    config = BatteryThermalConfig("test.acquire.config", "acquire", PROTOCOL_SHA256,
                                 "unit.battery-thermal-service.23c", D("296.15"), word)
    current = D("-1.455") if word == "standard-cc900" else D(0)
    return BatteryThermalTrace(config, config.source.fingerprint(), "a" * 64,
                               "COMPLETE", "final time", (), current, current, current,
                               (D(0), D(450), D(900)), (current,) * 3,
                               (D("3.7"), D("3.8"), D("3.9")),
                               (D(0), -D("0.181875"), -D("0.36375")) if current else (D(0),) * 3,
                               (D("296.15"), D("296.6"), D("297")), EVENTS,
                               ("4.2 - V", "V - 2.5", "318.15 - T", "T - 273.15"))


def _assess(trace):
    return assess(replace(trace.config, operation="assess", config_id="test.assess.config"), trace)


def test_selected_route_compiles_without_native_import_or_contact():
    script = "from empirical_lawhood.adapters.methods.battery_thermal_service.examples import thermal_service_draft; import sys; thermal_service_draft(); print('pybamm' in sys.modules)"
    assert subprocess.check_output([sys.executable, "-c", script], text=True).strip() == "False"
    draft = thermal_service_draft()
    result = compile_recursive_wave(draft=draft, registrations=operation_registrations(),
                                    registry=CapabilityRegistry("test.thermal", operation_manifests()),
                                    implementation_commit="a" * 40, output_codecs=output_codecs())
    assert len(result.execution_plan.tasks) == 2
    assert all(task.maximum_attempts == 1 for task in result.execution_plan.tasks)


@pytest.mark.parametrize(("temperature", "unit"), ((D("296.15"), "23c"), (D("300.15"), "27c")))
def test_exact_charge_and_event_checks_do_not_manufacture_continuous_certificate(temperature, unit):
    trace = _trace()
    offset = temperature - trace.config.initial_temperature_k
    trace = replace(trace,
                    config=replace(trace.config, initial_temperature_k=temperature,
                                   unit_id=f"unit.battery-thermal-service.{unit}"),
                    volume_mean_temperature_k=tuple(value + offset for value in trace.volume_mean_temperature_k))
    decoded = decode_canonical_bytes(trace.canonical_bytes(), BatteryThermalTrace, maximum_bytes=4 * 1024**2)
    assert decoded == trace
    result = _assess(trace)
    # Constant-current rectangle is independent of the assessor's trapezoid sum.
    assert -D("-1.455") * D(900) / D(3600) == result.realized_charge_ah == result.capacity_charge_ah == D("0.36375")
    assert trace.times_s[0] == 0 and trace.times_s[-1] == 900
    assert trace.accepted_current_a == trace.applied_current_a == trace.config.current_a
    assert all(value == trace.config.current_a for value in trace.current_a)
    assert result.sampled_envelope_pass and result.numerical_event_guarded
    assert result.disposition == "UNEVALUABLE" and not result.whole_time_certified
    assert result.reason_codes == ("whole-time-certificate-absent",)
    assert result.physical_independent_units == 0 and result.simulated_parameter_families == 1
    with pytest.raises(ValueError, match="continuous certification or physical units"):
        replace(result, whole_time_certified=True)
    with pytest.raises(ValueError, match="continuous certification or physical units"):
        replace(result, physical_independent_units=1)
    assert not _assess(replace(trace, processed_event_expressions=())).numerical_event_guarded


def test_realized_current_and_capacity_independently_falsify_delivery():
    trace = _trace()
    result = _assess(replace(trace, current_a=(D(0),) * 3))
    assert result.disposition == "SERVICE_FAIL"
    assert {"current-capacity-disagreement", "useful-charge-not-delivered", "native-current-delivery-differs"} <= set(result.reason_codes)
    result = _assess(replace(trace, discharge_capacity_ah=(D(0),) * 3))
    assert trace.times_s[-1] == 900
    assert result.realized_charge_ah == result.charge_discrepancy_ah == D("0.36375")
    assert result.capacity_charge_ah == 0 and result.disposition == "SERVICE_FAIL"
    assert "current-capacity-disagreement" in result.reason_codes


def test_hold_is_independent_measured_word_and_does_not_supply_useful_charge():
    hold = _trace("native-hold900")
    result = _assess(hold)
    assert result.realized_charge_ah == 0
    assert "useful-charge-not-delivered" in result.reason_codes
    assert result.disposition == "SERVICE_FAIL"


def test_termination_and_envelope_violations_remain_adverse():
    trace = _trace()
    result = _assess(replace(trace, voltage_v=(D("3.7"), D("4.3"), D("3.9"))))
    assert "sampled-service-envelope-violation" in result.reason_codes
    early = replace(trace, disposition="SIMULATOR_TERMINATED", termination="event: Maximum voltage [V]",
                    times_s=trace.times_s[:2], current_a=trace.current_a[:2], voltage_v=trace.voltage_v[:2],
                    discharge_capacity_ah=trace.discharge_capacity_ah[:2],
                    volume_mean_temperature_k=trace.volume_mean_temperature_k[:2])
    result = _assess(early)
    assert early.termination == "event: Maximum voltage [V]"
    assert result.trace_sha256 == early.fingerprint()
    assert result.disposition == "SERVICE_FAIL" and result.realized_charge_ah == D("0.181875")
    assert {"full-service-horizon-not-realized", "useful-charge-not-delivered"} <= set(result.reason_codes)
    assert not result.numerical_event_guarded and not result.whole_time_certified
    # This selected CC failure assesses neither CV continuation nor an EL advantage.


def test_missing_native_receivers_retain_technical_failure_and_unknown_delivery():
    trace = replace(_trace(), disposition="TECHNICAL_OBSERVATION_FAILURE", termination="NotImplementedError",
                    applied_current_a=None, times_s=(), current_a=(), voltage_v=(), discharge_capacity_ah=(),
                    volume_mean_temperature_k=(), reason_codes=("native-observation-failure",))
    assert decode_canonical_bytes(trace.canonical_bytes(), BatteryThermalTrace, maximum_bytes=None) == trace
    assert trace.termination == "NotImplementedError" and trace.applied_current_a is None
    assert not trace.current_a and trace.reason_codes == ("native-observation-failure",)
    result = _assess(trace)
    assert result.trace_sha256 == trace.fingerprint() and result.disposition == "UNEVALUABLE"
    assert result.realized_charge_ah is result.capacity_charge_ah is result.charge_discrepancy_ah is None
    assert set(result.reason_codes) == {"native-receivers-absent", "full-service-horizon-not-realized"}
    assert not result.sampled_envelope_pass and not result.numerical_event_guarded and not result.whole_time_certified
    assert result.physical_independent_units == 0 and result.simulated_parameter_families == 1
    with pytest.raises(ValueError, match="receiver denominator"):
        replace(_trace(), current_a=())


def test_preparation_source_and_native_clock_mutations_refuse():
    trace = _trace()
    with pytest.raises(ValueError, match="relabeled"):
        replace(trace.config, unit_id="unit.fresh-label")
    with pytest.raises(ValueError, match="pre-output"):
        replace(trace.config, protocol_sha256="b" * 64)
    with pytest.raises(ValueError, match="clock"):
        replace(trace, times_s=(D(0), D(900), D(450)))
    with pytest.raises(ValueError, match="scientific operands"):
        assess(replace(trace.config, operation="assess", word="native-hold900"), trace)
    with pytest.raises(ValueError, match="scientific root"):
        draft = thermal_service_draft()
        bad = replace(draft, development_study=replace(draft.development_study, question="Unrelated question"))
        compile_recursive_wave(draft=bad, registrations=operation_registrations(),
                               registry=CapabilityRegistry("test.thermal", operation_manifests()),
                               implementation_commit="a" * 40, output_codecs=output_codecs())


def test_native_stage_reads_are_independent_using_exposed_recorded_source(monkeypatch, tmp_path):
    """An in-memory stand-in returns differing readings, with no native solve."""
    from empirical_lawhood.adapters.methods.battery_thermal_service import science
    root = tmp_path / "pybamm"
    for member, constant in (("input/parameters/lithium_ion/Chen2020.py", "PARAMETER_SHA256"),
                             ("parameters/geometric_parameters.py", "GEOMETRY_SHA256")):
        path = root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"exposed software source fixture")
        monkeypatch.setattr(science, constant, sha256(path.read_bytes()).hexdigest())
    fixtures = []
    for member, _ in science.MODEL_MEMBERS:
        path = root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"exposed model source fixture")
        fixtures.append((member, sha256(path.read_bytes()).hexdigest()))
    monkeypatch.setattr(science, "MODEL_MEMBERS", tuple(fixtures))

    class Parameters(dict):
        def update(self, values):
            super().update(values)
            self["Current function [A]"] = -0.234

    stage_reads = []

    class BuiltModel:
        def __init__(self, events):
            self.events = events
            self.variables = {name: SimpleNamespace(evaluate=self.unprocessed)
                              for name in ("Time [s]", "Current [A]")}

        @staticmethod
        def unprocessed(**kwargs):
            raise NotImplementedError("exposed delayed-processing fixture")

        def get_processed_variable(self, name):
            def evaluate(*, t):
                stage_reads.append((name, t))
                return {"Time [s]": 0.0, "Current [A]": -0.456}[name]
            return SimpleNamespace(evaluate=evaluate)

    class Simulation:
        def __init__(self, model, **kwargs):
            self.built_model = BuiltModel(model.events)

        def build(self, **kwargs):
            pass

        def solve(self, clocks):
            class RecordedSolution:
                t = (0.0, 450.0, 900.0)
                termination = "final time"

                def __getitem__(self, name):
                    columns = {"Current [A]": (-0.777,) * 3, "Terminal voltage [V]": (3.7,) * 3,
                               "Discharge capacity [A.h]": (0, -0.097125, -0.19425),
                               "Volume-averaged cell temperature [K]": (296.15,) * 3}
                    return lambda clocks: columns[name]
            return RecordedSolution()

    module = SimpleNamespace(
        __version__="26.6.2.0", __file__=str(root / "__init__.py"),
        lithium_ion=SimpleNamespace(SPMe=lambda **kwargs: SimpleNamespace(
            variables={"Volume-averaged cell temperature [K]": 296.15},
            events=[SimpleNamespace(name=name, expression=name) for name in EVENTS[:2]])),
        ParameterValues=lambda name: Parameters(), Simulation=Simulation,
        CasadiSolver=lambda **kwargs: SimpleNamespace(**kwargs), EventType=SimpleNamespace(TERMINATION="termination"),
        Event=lambda name, expression, kind: SimpleNamespace(name=name, expression=str(expression)))
    monkeypatch.setitem(sys.modules, "pybamm", module)
    trace = science.acquire(_trace().config)
    assert trace.disposition == "COMPLETE"
    assert stage_reads == [("Time [s]", 0), ("Current [A]", 0.0)]
    assert (trace.requested_current_a, trace.accepted_current_a, trace.applied_current_a, trace.current_a[0]) == (D("-1.455"), D("-0.234"), D("-0.456"), D("-0.777"))
    assert trace.accepted_model_clock_s == trace.applied_model_clock_s == trace.times_s[0] == 0
    assert _assess(trace).disposition == "SERVICE_FAIL"
    (root / fixtures[1][0]).write_bytes(b"substituted model source")
    assert science.acquire(_trace().config).disposition == "TECHNICAL_OBSERVATION_FAILURE"


def test_effect_identity_excludes_labels_but_preserves_native_operands():
    from empirical_lawhood.adapters.methods.battery_thermal_service.executable_binding import _slots
    config = _trace().config
    assert _slots(replace(config, config_id="test.other-label")) == _slots(config)
    assert _slots(replace(config, initial_soc=D("0.300"), initial_temperature_k=D("296.150"))) == _slots(config)
    warm = replace(config, initial_temperature_k=D("300.15"), unit_id="unit.battery-thermal-service.27c")
    assert _slots(warm) != _slots(config)
    assert _slots(replace(config, view="tighter")) != _slots(config)


def test_acquisition_registration_refuses_assessment_config_before_contact():
    draft = thermal_service_draft()
    first = draft.operations[0]
    config = decode_canonical_bytes(first.config_payload.encode(), BatteryThermalConfig, maximum_bytes=4 * 1024**2)
    bad_operation = replace(first, config_payload=replace(config, operation="assess").canonical_bytes().decode())
    bad = replace(draft, operations=(bad_operation, draft.operations[1]))
    with pytest.raises(ValueError, match="selected registration"):
        compile_recursive_wave(draft=bad, registrations=operation_registrations(),
                               registry=CapabilityRegistry("test.thermal", operation_manifests()),
                               implementation_commit="a" * 40, output_codecs=output_codecs())
