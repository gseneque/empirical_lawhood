"""Focused conformance and independent scientific oracles; no native execution."""

from __future__ import annotations

from dataclasses import replace
import json

import numpy as np
import pytest

from empirical_lawhood.adapters.physical.joint_description import SCHEMA, load_cohort, mapped_torax_preparation, produce_archive
from empirical_lawhood.adapters.simulators import joint_description_native as native
from empirical_lawhood.domains.joint_description_native import RECEIVERS, prepare_predictors, presets, produce, resolve_parameters, sample_preparation, selected_receivers
from empirical_lawhood.domains.battery.joint_description import battery_receivers, continuation_defect, interval_exceedance
from empirical_lawhood.domains.neuroscience.joint_description import firing_rate
from empirical_lawhood.domains.optics.joint_description import signed_displacement
from empirical_lawhood.methods.trace_observables import harmonic_response, time_integral, truncate_at
from empirical_lawhood.science.joint_description import TrialRequest


def request(family, *, input_path=None, device="cpu", parameters=None):
    spec = next(row for row in presets() if row["family_id"] == family)
    return TrialRequest(family, 9271, ("unit.calibration.001", "unit.calibration.002"), "calibration",
                        tuple(spec["actions"]), tuple(spec["horizons"]),
                        spec["parameters"] if parameters is None else parameters, input_path, device)


def cortical_document():
    return {"schema": SCHEMA, "family_id": "R13", "source_id": "test-fixture-not-scientific-data",
            "exposure": "recorded-archive", "action_unit": "pA", "receiver_unit": "Hz", "units": [
                {"unit_id": unit, "split": "calibration", "preparation_time_s": -1,
                 "preparation": {"baseline_hz": 2, "history_hz": 3, "resistance_mohm": 100},
                 "episodes": [{"action": 40, "status": "complete", "reason": "",
                               "data": {"duration_s": 1, "spike_times_s": [0.1, 0.3, 0.5, 0.9]}}]}
                for unit in ("unit.calibration.001", "unit.calibration.002")]}


def write_document(tmp_path, document):
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(document))
    return path


def bridge_document():
    document = cortical_document()
    document.update(family_id="R22", action_unit="fraction", receiver_unit="eV")
    native_preparation = {
        "radial_coordinates": [0, 0.5, 1], "electron_temperature_ev": [1000, 500, 100],
        "ion_temperature_ev": [1000, 500, 100], "electron_density_m3": [2e19, 1e19, 0.2e19],
        "plasma_current_a": 600000, "main_ion": "deuterium", "impurity": "carbon", "zeff": 2,
        "major_radius_m": 0.85, "minor_radius_m": 0.5, "toroidal_field_t": 0.5, "elongation_lcfs": 1.8,
        "source_radial_location": 0.3, "source_width": 0.2, "electron_heat_fraction": 0.5,
        "absorbed_power_fraction": 0.8, "chi_i_m2_s": 1, "chi_e_m2_s": 1,
        "particle_diffusivity_m2_s": 0.1, "particle_convection_m_s": 0, "maximum_core_temperature_ev": 5000,
    }
    for unit in document["units"]:
        unit["preparation"] = {"core_temperature_ev": 1000, "density_1e19_m3": 2,
                               "heating_power_w": 1e6, "history_temperature_ev": 990}
        unit["native_preparation"] = dict(native_preparation)
        unit["mapping_assumptions"] = ["assumption.test-profiles", "assumption.test-transport"]
        unit["episodes"] = [{"action": 0, "status": "complete", "reason": "", "data": {
            "time_s": [0, 0.02, 0.04], "core_temperature_ev": [1000, 1002, 1004], "heating_fraction": 0}}]
    return document


@pytest.mark.numerical(oracle="A 1 MW hold departs by 1% at 20 ms and 3% at 40 ms. On the independent Thomson clock the 20 ms interpolated rise is 4 eV.")
def test_recorded_nbi_tracking_preserves_nested_exposures_and_independent_clocks():
    document = bridge_document()
    for unit in document["units"]:
        unit["episodes"][0]["data"] = {
            "time_s": [0, .012, .024, .040], "core_temperature_ev": [1000, 1002.4, 1004.8, 1008],
            "power_time_s": [0, .01, .02, .03, .04], "power_w": [1e6, 1.005e6, 1.01e6, 1.02e6, 1.03e6],
        }
    tracking = {"max_fraction_error": .02, "max_power_gap_s": .011, "max_temperature_gap_s": .017}
    req = replace(request("R22", parameters={"recorded_power_tracking": tracking}), input_json=json.dumps(document))
    rows = produce_archive(req).rows
    assert len(rows) == 12
    for row in rows:
        if row.action != 0:
            assert row.status == "unsupported" and row.reason == "UNLOGGED_ACTION_NO_COUNTERFACTUAL"
        elif row.horizon == .02:
            assert row.status == "supported" and row.outcome == pytest.approx(4)
            assert dict(row.diagnostics)["maximum_fractional_tracking_error"] == pytest.approx(.01)
        else:
            assert row.status == "unsupported" and row.reason == "MEASURED_NBI_OUTSIDE_OPTION_BAND"
            assert dict(row.diagnostics)["maximum_fractional_tracking_error"] == pytest.approx(.03)
    incomplete = replace(req, parameters={"recorded_power_tracking": {**tracking, "max_temperature_gap_s": .01}})
    assert all(row.status == "failed" and "sample gap" in row.reason
               for row in produce_archive(incomplete).rows if row.action == 0 and row.horizon == .02)
    with pytest.raises(ValueError, match="disjoint"):
        resolve_parameters(replace(req, parameters={"recorded_power_tracking": {**tracking, "max_fraction_error": .05}}))
    with pytest.raises(ValueError, match="clock-gap"):
        resolve_parameters(replace(req, parameters={"recorded_power_tracking": {**tracking, "max_power_gap_s": -1}}))


@pytest.mark.numerical(oracle="spike counting in half-open [0,T): four listed events, endpoint excluded")
def test_cortical_rate_is_a_receiver_count_not_an_action_label():
    assert firing_rate([], horizon_s=2) == 0
    assert firing_rate([0, 0.1, 0.4, 0.5], horizon_s=0.5) == 6


@pytest.mark.numerical(oracle="analytic integral of affine current I(t)=2+3t on [0,2] is 10 ampere seconds")
def test_capacity_uses_physical_clock_and_interpolated_horizon():
    time = [0, 0.25, 0.8, 1.4, 3]
    current = [2 + 3 * t for t in time]
    assert time_integral(time, current, 2) == pytest.approx(10)
    receivers = battery_receivers(time, current, [4 - 0.1 * t for t in time],
                                 [298 + t for t in time], horizon_s=2)
    assert receivers.discharge_capacity_ah == pytest.approx(10 / 3600)
    assert receivers.terminal_voltage_v == pytest.approx(3.8)
    assert receivers.peak_temperature_k == pytest.approx(300)


@pytest.mark.numerical(oracle="closed-form phasor ratio: u=2cos(wt), y=3cos(wt)-4sin(wt), H=1.5+2i")
def test_modulation_preserves_signed_complex_response_on_nonuniform_clock():
    t = np.linspace(0, 1, 1001) ** 1.03
    omega = 2 * np.pi * 5
    response = harmonic_response(t, 7 + 2 * np.cos(omega * t),
                                 11 + 3 * np.cos(omega * t) - 4 * np.sin(omega * t),
                                 frequency_hz=5, horizon_s=1)
    assert response.real == pytest.approx(1.5, abs=1e-13)
    assert response.imag == pytest.approx(2, abs=1e-13)
    assert response.magnitude == pytest.approx(2.5, abs=1e-13)
    assert response.residual_rms < 1e-12


@pytest.mark.numerical(oracle="signed endpoint difference y(T)-y(0), interval distance, and coordinatewise absolute differences")
def test_sign_uncertainty_and_reduction_do_not_discard_scientific_information():
    assert signed_displacement([0, 1], [1, -2], horizon_s=1) == -3
    assert interval_exceedance(3.5, 3.7, 0.1) == pytest.approx(0.1)
    assert interval_exceedance(3.65, 3.7, 0.1) == 0
    assert continuation_defect([3.7, 300], [3.6, 302], scales=[0.05, 1]).tolist() == pytest.approx([2, 2])


@pytest.mark.parametrize("clock,values,horizon", [([0, 1, 1], [0, 1, 2], 1), ([0, 1], [0, 1], 2),
                                                  ([1, 2], [0, 1], 2), ([0, 1], [0, np.nan], 1)])
def test_invalid_or_uncovered_receiver_clock_is_not_extrapolated(clock, values, horizon):
    with pytest.raises(ValueError):
        truncate_at(clock, values, horizon)


def test_frequency_alias_and_unexcited_action_are_explicitly_unevaluable():
    with pytest.raises(ValueError, match="resolve"):
        harmonic_response([0, 0.2, 0.4, 0.6, 0.8, 1], [1, 2, 1, 2, 1, 2], [1, 2, 3, 4, 5, 6], frequency_hz=5, horizon_s=1)
    t = np.linspace(0, 1, 101)
    with pytest.raises(ValueError, match="no resolvable"):
        harmonic_response(t, np.ones(t.size), np.cos(2 * np.pi * 5 * t), frequency_hz=5, horizon_s=1)


def test_archive_retains_entire_census_and_never_invents_counterfactuals(tmp_path):
    path = write_document(tmp_path, cortical_document())
    req = request("R13", input_path=path)
    batch = produce_archive(req)
    batch.validate_census(req, RECEIVERS["R13"])
    assert len(batch.rows) == 12
    assert sum(row.status == "supported" for row in batch.rows) == 4
    assert sum(row.reason == "UNLOGGED_ACTION_NO_COUNTERFACTUAL" for row in batch.rows) == 8
    assert batch.source_kind == "recorded-archive"
    assert "no-prospective-physical-control-claim" in batch.provenance
    assert any(value.startswith("sha256:") for value in batch.provenance)


def test_pinned_json_transport_never_materializes_a_temporary_file(monkeypatch):
    import empirical_lawhood.adapters.physical.joint_description as physical
    monkeypatch.setattr(physical, "load_cohort", lambda *_: pytest.fail("pinned bytes diverted through a filesystem path"))
    req = replace(request("R13"), input_json=json.dumps(cortical_document()))
    batch = produce_archive(req)
    batch.validate_census(req, RECEIVERS["R13"])
    predicted = prepare_predictors(req)
    assert tuple(row.features for row in batch.rows) == tuple(row.features for row in predicted.rows)


def test_input_transports_are_mutually_exclusive(tmp_path):
    with pytest.raises(ValueError):
        replace(request("R13", input_path=tmp_path / "raw.json"), input_json=json.dumps(cortical_document()))


def test_changed_outcomes_cannot_change_predictor_coordinates(tmp_path):
    document = cortical_document()
    path = write_document(tmp_path, document)
    req = request("R13", input_path=path)
    first = produce_archive(req)
    document["units"][0]["episodes"][0]["data"]["spike_times_s"] = []
    write_document(tmp_path, document)
    second = produce_archive(req)
    assert tuple(row.features for row in first.rows) == tuple(row.features for row in second.rows)
    assert [row.outcome for row in first.rows] != [row.outcome for row in second.rows]
    assert first.provenance != second.provenance


@pytest.mark.parametrize("mutation", [
    lambda doc: doc.update(exposure="fresh-intervention"),
    lambda doc: doc.update(receiver_unit="kHz"),
    lambda doc: doc["units"][0].update(preparation_time_s=0),
    lambda doc: doc["units"].append(doc["units"][0]),
    lambda doc: doc["units"][0]["preparation"].update(outcome_hz=42),
    lambda doc: doc["units"][0]["episodes"].append(doc["units"][0]["episodes"][0]),
])
def test_raw_schema_rejects_scope_and_leakage_substitutions(tmp_path, mutation):
    document = cortical_document()
    mutation(document)
    path = write_document(tmp_path, document)
    with pytest.raises(ValueError):
        load_cohort(path, "R13")


def test_archive_unit_cannot_cross_fit_evaluation_boundary(tmp_path):
    path = write_document(tmp_path, cortical_document())
    req = replace(request("R13", input_path=path), split="evaluation")
    with pytest.raises(ValueError, match="cross"):
        produce_archive(req)


def test_unknown_json_keys_are_not_silently_discarded(tmp_path):
    path = tmp_path / "raw.json"
    path.write_text('{"schema":"x","schema":"y"}')
    with pytest.raises(ValueError, match="duplicate"):
        load_cohort(path, "R13")


def test_invalid_trace_is_a_failed_unit_action_not_dropped_population(tmp_path):
    document = cortical_document()
    document["units"][0]["episodes"][0]["data"]["spike_times_s"] = [0.3, 0.1]
    path = write_document(tmp_path, document)
    req = request("R13", input_path=path)
    batch = produce_archive(req)
    batch.validate_census(req, RECEIVERS["R13"])
    failed = [row for row in batch.rows if row.status == "failed"]
    assert len(failed) == 2
    assert all(row.outcome is None and row.reason.startswith("RAW_RECEIVER_INVALID") for row in failed)


@pytest.mark.numerical(oracle="constructed raw cohorts: signed linear mirror displacement, constant-current integral, and analytic 5 Hz in-phase response")
@pytest.mark.parametrize("family", ["R14", "R15", "R16"])
def test_each_physical_family_projects_its_own_raw_observable(tmp_path, family):
    document = cortical_document()
    document["family_id"] = family
    if family == "R14":
        document.update(action_unit="V", receiver_unit="rad")
        prep = {"baseline_angle_rad": 0, "history_angle_rad": 0, "resonance_hz": 100}
        data = {"time_s": [0, 0.1, 0.2], "position_rad": [0, -0.001, -0.002], "drive_v": [-0.1] * 3}
        action, expected = -0.1, {"displacement_rad": -0.002}
    elif family == "R15":
        document.update(action_unit="A", receiver_unit="V;A.h")
        prep = {"initial_soc": 0.6, "initial_temperature_k": 298, "history_current_a": 0.5}
        data = {"time_s": [0, 60, 120], "current_a": [1, 1, 1], "voltage_v": [4, 3.9, 3.8],
                "temperature_k": [298, 299, 300], "voltage_uncertainty_v": 0.001, "capacity_uncertainty_ah": 0.0001}
        action, expected = 1.0, {"terminal_voltage_v": 3.8, "discharge_capacity_ah": 120 / 3600}
    else:
        document.update(action_unit="Hz", receiver_unit="W.m^-2", forcing_unit="Pa.m^3.s^-1")
        prep = {"baseline_density_1e19_m3": 2, "baseline_gas_rate": 1, "history_receiver": 3}
        t = np.linspace(0, 1, 101)
        data = {"time_s": t.tolist(), "gas_rate": (2 + np.cos(10 * np.pi * t)).tolist(),
                "receiver": (4 + 3 * np.cos(10 * np.pi * t)).tolist()}
        action, expected = 5.0, {"response_real": 3, "response_imag": 0}
    for unit in document["units"]:
        unit["preparation"] = prep
        unit["episodes"] = [{"action": action, "status": "complete", "reason": "", "data": data}]
    path = write_document(tmp_path, document)
    req = request(family, input_path=path)
    batch = produce_archive(req)
    batch.validate_census(req, RECEIVERS[family])
    for row in batch.rows:
        if row.action == action and row.horizon == max(req.horizons):
            assert row.status == "supported"
            assert row.outcome == pytest.approx(expected[row.receiver_id], abs=1e-12)


@pytest.mark.numerical(oracle="Measured 1.002 to 1.006 A ramp gives (1.002+1.006)/2 times 60 s; a later 1.03 A sample violates the 0.01 A tracking band.")
def test_battery_tracking_uses_measured_current_and_retains_shorter_horizon():
    document = cortical_document()
    document.update(family_id="R15", action_unit="A", receiver_unit="V;A.h")
    for unit in document["units"]:
        unit["preparation"] = {"initial_soc": 0.6, "initial_temperature_k": 298, "history_current_a": 0.5}
        unit["episodes"] = [{"action": 1, "status": "complete", "reason": "", "data": {
            "time_s": [0, 60, 120], "current_a": [1.002, 1.006, 1.03], "voltage_v": [4, 3.9, 3.8],
            "temperature_k": [298, 299, 300], "voltage_uncertainty_v": 0.001, "capacity_uncertainty_ah": 0.0001}}]
    legacy = replace(request("R15", parameters={}), input_json=json.dumps(document))
    assert all(row.status == "failed" for row in produce_archive(legacy).rows if row.action == 1)
    authored = replace(legacy, parameters={"current_tracking_tolerance_a": 0.01})
    batch = produce_archive(authored)
    batch.validate_census(authored, RECEIVERS["R15"])
    for row in batch.rows:
        if row.action != 1:
            assert row.status == "unsupported"
        elif row.horizon == 120:
            assert row.status == "failed" and "current differs" in row.reason
        else:
            assert row.status == "supported"
            expected = {"terminal_voltage_v": 3.9, "discharge_capacity_ah": 1.004 * 60 / 3600}
            assert row.outcome == pytest.approx(expected[row.receiver_id], abs=1e-12)


@pytest.mark.parametrize("tolerance", [-1, True, "0.01", float("nan"), float("inf"), 0.25, 0.5])
def test_battery_tracking_rejects_invalid_or_overlapping_bands_before_acquisition(tolerance):
    with pytest.raises(ValueError, match="tracking|finite machine numbers"):
        resolve_parameters(request("R15", parameters={"current_tracking_tolerance_a": tolerance}))


def test_widened_battery_tracking_band_preserves_sign_even_for_one_signed_command():
    req = replace(request("R15", parameters={"current_tracking_tolerance_a": 0.5}), actions=(-0.25,))
    with pytest.raises(ValueError, match="sign"):
        resolve_parameters(req)


def test_declared_signed_mirror_action_cannot_substitute_opposite_realized_voltage(tmp_path):
    document = cortical_document()
    document.update(family_id="R14", action_unit="V", receiver_unit="rad")
    for unit in document["units"]:
        unit["preparation"] = {"baseline_angle_rad": 0, "history_angle_rad": 0, "resonance_hz": 100}
        unit["episodes"] = [{"action": 0.1, "status": "complete", "reason": "", "data": {
            "time_s": [0, 0.2], "drive_v": [-0.1, -0.1], "position_rad": [0, 0.001]}}]
    batch = produce_archive(request("R14", input_path=write_document(tmp_path, document)))
    assert all(row.status == "failed" for row in batch.rows if row.action == 0.1)


def test_new_native_preparations_are_reproducible_and_split_distinct():
    req = request("R18")
    parameters = resolve_parameters(req)
    first = sample_preparation(req, req.unit_ids[0], parameters)
    assert first == sample_preparation(req, req.unit_ids[0], parameters)
    assert first != sample_preparation(replace(req, split="evaluation"), req.unit_ids[0], parameters)
    assert first != sample_preparation(req, req.unit_ids[1], parameters)


def test_bridge_mapping_binds_observed_core_state_and_explicit_assumptions():
    raw = bridge_document()["units"][0]
    mapped = mapped_torax_preparation(raw["unit_id"], raw)
    assert float(mapped.electron_temperature_ev[0]) == 1000
    assert mapped.assumption_ids == tuple(raw["mapping_assumptions"])
    raw["native_preparation"]["electron_temperature_ev"] = [2000, 500, 100]
    with pytest.raises(ValueError, match="recorded pre-action"):
        mapped_torax_preparation(raw["unit_id"], raw)


def test_bridge_selection_checks_held_out_mapped_profile_before_native_entry():
    from types import SimpleNamespace
    from empirical_lawhood.adapters.physical.joint_description import validate_selected_cohort

    document = bridge_document()
    calibration, evaluation = document["units"]
    evaluation["split"] = "evaluation"
    selection = SimpleNamespace(family_id="R22", calibration_unit_ids=(calibration["unit_id"],),
                                evaluation_unit_ids=(evaluation["unit_id"],))
    validate_selected_cohort(json.dumps(document).encode(), selection)
    evaluation["native_preparation"]["electron_density_m3"] = [3e19, 1e19, 0.2e19]
    with pytest.raises(ValueError, match="mapped native density"):
        validate_selected_cohort(json.dumps(document).encode(), selection)


@pytest.mark.numerical(oracle="separate constructed physical ΔT=100*t and native ΔT=200*t eV, with only the physical zero action logged; no native engine")
def test_bridge_keeps_two_sources_and_missing_physical_actions_distinct(monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.adapters.simulators.torax_native import runtime
    from empirical_lawhood.domains.fusion.torax_native.contracts import NativeToraxEpisodeDisposition
    monkeypatch.setattr(native, "_versions", lambda *_: ("unit-fixture-no-native-engine",))
    monkeypatch.setattr(native, "_jax_device", lambda *_: None)
    calls = []
    def trajectory(preparation, action, view):
        calls.append((preparation, action, view))
        return (SimpleNamespace(time_s=(0, 0.02, 0.04), core_electron_temperature_ev=(1000, 1004, 1008)),
                SimpleNamespace(disposition=NativeToraxEpisodeDisposition.COMPLETE))
    monkeypatch.setattr(runtime, "execute_native_torax", trajectory)
    req = replace(request("R22"), input_json=json.dumps(bridge_document()))
    prepared = prepare_predictors(req)
    batch = native.NativeJointDescriptionPort().acquire(req)
    batch.validate_census(req, RECEIVERS["R22"])
    assert len(calls) == len(req.unit_ids) * len(req.actions)
    assert {row.key: row.features for row in prepared.rows} == {row.key: row.features for row in batch.rows}
    for row in batch.rows:
        if row.receiver_id == "simulator_temperature_change_ev":
            assert row.outcome == pytest.approx(200 * row.horizon)
        elif row.action == 0:
            assert row.outcome == pytest.approx(100 * row.horizon)
        else:
            assert row.status == "unsupported" and row.outcome is None


def test_declarative_presets_expose_complete_measured_receiver_policies_and_features():
    definitions = presets()
    assert {row["family_id"] for row in definitions} == {"R13", "R14", "R15", "R16", "R17", "R18", "R19", "R22"}
    for row in definitions:
        assert set(row["receiver_policies"]) == set(row["receivers"])
        for policy in row["receiver_policies"].values():
            assert policy["units"] and policy["scale"] > 0 and policy["max_abs_error"] > 0
        assert len({tuple(description["features"]) for description in row["descriptions"]}) == 4
        minimal = next(description for description in row["descriptions"] if description["id"] == "minimal")
        assert not any(name.startswith("history_") for name in minimal["features"])
    r17 = next(row for row in definitions if row["family_id"] == "R17")
    assert all(row["memory_samples"] == 0 for row in r17["descriptions"])


def test_native_implementation_requires_injected_execution_port():
    with pytest.raises(ValueError, match="typed execution"):
        produce(request("R18"))
    calls = []
    class Port:
        def acquire(self, value):
            calls.append(value)
            return "typed-result"
    req = request("R18")
    assert produce(req, native_port=Port()) == "typed-result"
    assert calls == [req]


def test_native_predictors_have_no_engine_contact_or_outcomes(monkeypatch):
    monkeypatch.setattr(native, "_versions", lambda *_: pytest.fail("native engine contact before freeze"))
    class ForbiddenPort:
        def acquire(self, request):
            pytest.fail("native port called during predictor preparation")
    for family in ("R17", "R18", "R19"):
        req = request(family)
        batch = prepare_predictors(req, native_port=ForbiddenPort())
        batch.validate_census(req, RECEIVERS[family])
        assert all(row.outcome is None and not row.diagnostics and row.reason == "not-yet-acquired" for row in batch.rows)


def test_archive_predictors_do_not_project_receivers_before_freeze(tmp_path, monkeypatch):
    import empirical_lawhood.adapters.physical.joint_description as physical
    path = write_document(tmp_path, cortical_document())
    req = request("R13", input_path=path)
    monkeypatch.setattr(physical, "_reduce", lambda *_: pytest.fail("receiver reduction before forecast freeze"))
    batch = prepare_predictors(req)
    batch.validate_census(req, RECEIVERS["R13"])
    assert all(row.outcome is None for row in batch.rows)


def test_cpu_only_battery_cannot_be_mislabeled_gpu():
    with pytest.raises(native.NativePrerequisiteError, match="CPU"):
        native.NativeJointDescriptionPort().acquire(request("R18", device="gpu"))


def test_absent_native_dependency_is_explicit_and_not_synthetic_fallback(monkeypatch):
    def absent(package):
        raise native.PackageNotFoundError(package)
    monkeypatch.setattr(native, "version", absent)
    with pytest.raises(native.NativePrerequisiteError, match="pybamm"):
        native.NativeJointDescriptionPort().acquire(request("R18"))


def test_unknown_native_parameter_fails_before_engine_entry(monkeypatch):
    monkeypatch.setattr(native, "_versions", lambda *_: pytest.fail("engine prereq contacted"))
    with pytest.raises(ValueError, match="unknown"):
        native.NativeJointDescriptionPort().acquire(request("R18", parameters={"ignored_knob": 5}))


@pytest.mark.parametrize("family", ["R17", "R18", "R19", "R22"])
def test_reserved_receiver_selection_is_an_authored_scope_not_an_unknown_parameter(family):
    req = request(family, parameters={"receivers": RECEIVERS[family]})
    assert selected_receivers(req) == RECEIVERS[family]
    assert "receivers" not in resolve_parameters(req)


@pytest.mark.parametrize("receivers", [[], ["peak_temperature_k", "peak_temperature_k"], ["unmeasured"], "peak_temperature_k"])
def test_invalid_receiver_census_fails_before_native_entry(monkeypatch, receivers):
    monkeypatch.setattr(native, "_versions", lambda *_: pytest.fail("engine prerequisite contacted"))
    with pytest.raises(ValueError, match="receivers"):
        native.NativeJointDescriptionPort().acquire(request("R18", parameters={"receivers": receivers}))


def test_bridge_receiver_selection_cannot_remove_either_source():
    with pytest.raises(ValueError, match="both separate"):
        resolve_parameters(request("R22", parameters={"receivers": ["simulator_temperature_change_ev"]}))


def test_physical_receiver_subset_preserves_frozen_features_and_complete_selected_census():
    document = cortical_document()
    document.update(family_id="R15", action_unit="A", receiver_unit="V;A.h")
    for unit in document["units"]:
        unit["preparation"] = {"initial_soc": 0.6, "initial_temperature_k": 298, "history_current_a": 0.5}
        unit["episodes"] = [{"action": 1, "status": "complete", "reason": "", "data": {
            "time_s": [0, 60, 120], "current_a": [1, 1, 1], "voltage_v": [4, 3.9, 3.8],
            "temperature_k": [298, 299, 300], "voltage_uncertainty_v": 0.001, "capacity_uncertainty_ah": 0.0001}}]
    receivers = ("terminal_voltage_v",)
    req = replace(request("R15", parameters={"receivers": receivers}), input_json=json.dumps(document))
    predicted, acquired = prepare_predictors(req), produce_archive(req)
    predicted.validate_census(req, receivers)
    acquired.validate_census(req, receivers)
    assert tuple(row.features for row in predicted.rows) == tuple(row.features for row in acquired.rows)
    assert all(row.receiver_id == receivers[0] for row in acquired.rows)
    assert sum(row.status == "supported" for row in acquired.rows) == 4


@pytest.mark.parametrize("family,receiver", [("R18", "peak_temperature_k"), ("R19", "temperature_reduction_defect_k")])
def test_native_receiver_subset_preserves_frozen_features_and_shared_acquisition_work(monkeypatch, family, receiver):
    monkeypatch.setattr(native, "_versions", lambda *_: ("unit-test-injected-not-native",))
    def fixture(preparation, action, horizons, parameters, *, model_name):
        return {h: {"terminal_voltage_v": 3.8, "peak_temperature_k": 300,
                    "discharge_capacity_ah": 0.01} for h in horizons}, 100
    monkeypatch.setattr(native, "_pybamm_episode", fixture)
    req = request(family, parameters={"receivers": [receiver]})
    predicted, acquired = prepare_predictors(req), native.NativeJointDescriptionPort().acquire(req)
    predicted.validate_census(req, (receiver,))
    acquired.validate_census(req, (receiver,))
    assert tuple(row.features for row in predicted.rows) == tuple(row.features for row in acquired.rows)
    assert all(row.status == "supported" for row in acquired.rows)
    models = 2 if family == "R19" else 1
    assert sum(row.work_units for row in acquired.rows) == models * 100 * len(req.unit_ids) * len(req.actions)


def test_gym_default_heating_panel_is_inside_native_bounds_before_acquisition():
    req = request("R17")
    parameters = resolve_parameters(req)
    assert all(0 <= parameters["nbi_power_w"] * (1 + action) <= 33e6 for action in req.actions)
    with pytest.raises(ValueError, match="heating envelope"):
        prepare_predictors(replace(req, parameters={**parameters, "nbi_power_w": 33e6}))


@pytest.mark.numerical(oracle="independent constructed DFN/SPMe receiver differences: |3.8-3.7| V and |300-302| K; injected unit fixture, no engine")
def test_reduced_battery_defects_use_both_native_models_and_preserve_denominator(monkeypatch):
    monkeypatch.setattr(native, "_versions", lambda *_: ("unit-test-injected-not-native",))
    calls = []
    def fixture(preparation, action, horizons, parameters, *, model_name):
        calls.append((model_name, action))
        return {h: {"terminal_voltage_v": 3.8 if model_name == "DFN" else 3.7,
                    "peak_temperature_k": 300 if model_name == "DFN" else 302} for h in horizons}, 100
    monkeypatch.setattr(native, "_pybamm_episode", fixture)
    req = request("R19")
    batch = native.NativeJointDescriptionPort().acquire(req)
    batch.validate_census(req, RECEIVERS["R19"])
    assert len(calls) == 2 * len(req.unit_ids) * len(req.actions)
    for row in batch.rows:
        assert row.outcome == pytest.approx(0.1 if row.receiver_id == "voltage_reduction_defect_v" else 2)


def test_native_action_failure_has_no_retry_and_keeps_all_receivers(monkeypatch):
    monkeypatch.setattr(native, "_versions", lambda *_: ())
    calls = []
    def failure(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("injected independent action failure")
    monkeypatch.setattr(native, "_pybamm_episode", failure)
    req = request("R18")
    batch = native.NativeJointDescriptionPort().acquire(req)
    batch.validate_census(req, RECEIVERS["R18"])
    assert len(calls) == len(req.unit_ids) * len(req.actions)
    assert all(row.status == "failed" and row.outcome is None for row in batch.rows)


def test_late_gym_failure_preserves_valid_earlier_horizon_without_retry(monkeypatch):
    monkeypatch.setattr(native, "_versions", lambda *_: ())
    monkeypatch.setattr(native, "_jax_device", lambda *_: None)
    calls = []
    def partial(*args):
        calls.append(args)
        raise native.NativePartialEpisodeError("injected late stop", {2.0: {"fusion_gain": 4.0}}, 50)
    monkeypatch.setattr(native, "_gym_episode", partial)
    req = request("R17")
    batch = native.NativeJointDescriptionPort().acquire(req)
    batch.validate_census(req, RECEIVERS["R17"])
    assert len(calls) == len(req.unit_ids) * len(req.actions)
    assert all(row.status == "supported" and row.outcome == 4 for row in batch.rows if row.horizon == 2)
    assert all(row.status == "failed" and row.outcome is None for row in batch.rows if row.horizon == 4)
