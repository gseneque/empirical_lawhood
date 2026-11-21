"""Strict external-format binding for new physical cohorts.

Only raw, explicitly supplied records are read. Missing logged options remain in
the census and do not become counterfactual measurements. This file is an input
adapter, never a replay of the preprint's accepted results.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Mapping

import numpy as np

from empirical_lawhood.domains.joint_description_native import PREPARATION_FIELDS, feature_vector, resolve_parameters, selected_receivers
from empirical_lawhood.domains.neuroscience.joint_description import firing_rate
from empirical_lawhood.domains.optics.joint_description import signed_displacement
from empirical_lawhood.domains.battery.joint_description import battery_receivers
from empirical_lawhood.domains.fusion.joint_description import divertor_modulation, heating_tracking_error, temperature_change
from empirical_lawhood.methods.trace_observables import truncate_at


SCHEMA = "el.joint-description.raw-physical.v1"
MAXIMUM_INPUT_BYTES = 64 * 1024 * 1024
ACTION_UNITS = {"R13": "pA", "R14": "V", "R15": "A", "R16": "Hz", "R22": "fraction"}
RECEIVER_UNITS = {"R13": "Hz", "R14": "rad", "R15": "V;A.h", "R16": "W.m^-2", "R22": "eV"}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _keys(value, expected, label):
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise ValueError(f"{label} fields must be exactly {sorted(expected)}")


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


@dataclass(frozen=True, slots=True)
class PhysicalCohort:
    family_id: str
    source_id: str
    content_sha256: str
    receiver_unit: str
    units: Mapping[str, Mapping[str, object]]

    def selected_unit(self, unit_id, split):
        if unit_id not in self.units:
            raise ValueError(f"authored independent unit absent from supplied cohort: {unit_id}")
        unit = self.units[unit_id]
        if unit["split"] != split:
            raise ValueError(f"physical independent unit cannot cross calibration/evaluation splits: {unit_id}")
        return unit


def mapped_torax_preparation(unit_id, raw):
    """Bind the archived pre-action plasma profile to the native input contract."""
    from empirical_lawhood.domains.fusion.torax_native.contracts import NativeToraxPreparation

    data = raw["native_preparation"]
    required = {field.name for field in fields(NativeToraxPreparation)} - {"preparation_id", "assumption_ids"}
    _keys(data, required, "explicit mapped native TORAX preparation")
    profiles = {"radial_coordinates", "electron_temperature_ev", "ion_temperature_ev", "electron_density_m3"}
    converted = {}
    for name, value in data.items():
        if name in profiles:
            converted[name] = tuple(Decimal(str(item)) for item in value)
        elif name in {"main_ion", "impurity"}:
            converted[name] = value
        else:
            converted[name] = Decimal(str(value))
    token = sha256(unit_id.encode()).hexdigest()[:20]
    result = NativeToraxPreparation(preparation_id=f"preparation.joint-description.{token}",
                                    assumption_ids=tuple(sorted(raw["mapping_assumptions"])), **converted)
    if not np.isclose(float(result.electron_temperature_ev[0]), raw["preparation"]["core_temperature_ev"], rtol=1e-12, atol=0):
        raise ValueError("mapped native core temperature differs from the recorded pre-action coordinate")
    if not np.isclose(float(result.electron_density_m3[0]) / 1e19, raw["preparation"]["density_1e19_m3"], rtol=1e-12, atol=0):
        raise ValueError("mapped native density differs from the recorded pre-action coordinate")
    return result


def validate_selected_cohort(payload, specification):
    """Check both authored rosters and upstream inputs before a study can enter."""
    cohort = decode_cohort(payload, specification.family_id)
    for split, units in (("calibration", specification.calibration_unit_ids),
                         ("evaluation", specification.evaluation_unit_ids)):
        for unit_id in units:
            unit = cohort.selected_unit(unit_id, split)
            if cohort.family_id == "R22":
                mapped_torax_preparation(unit_id, unit)


def load_cohort(path: Path, family_id: str) -> PhysicalCohort:
    """Read bounded bytes from the runner-selected immutable input copy."""
    path = Path(path)
    with path.open("rb") as stream:
        payload = stream.read(MAXIMUM_INPUT_BYTES + 1)
    return decode_cohort(payload, family_id)


def decode_cohort(payload: bytes, family_id: str) -> PhysicalCohort:
    """Decode exact pinned input bytes without materializing an unguarded path."""
    if family_id not in ACTION_UNITS:
        raise ValueError("raw physical adapter does not own this family")
    if type(payload) is not bytes:
        raise TypeError("physical raw input transport requires exact bytes")
    if len(payload) > MAXIMUM_INPUT_BYTES:
        raise ValueError("physical input exceeds the 64 MiB bound")
    document = json.loads(payload, object_pairs_hook=_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite JSON {value}")))
    required = {"schema", "family_id", "source_id", "exposure", "action_unit", "receiver_unit", "units"}
    if family_id == "R16":
        required.add("forcing_unit")
    _keys(document, required, "cohort")
    if document["schema"] != SCHEMA or document["family_id"] != family_id:
        raise ValueError("physical input schema/family differs from the authored request")
    if document["exposure"] != "recorded-archive":
        raise ValueError("this archive reader cannot grant outcome-blind or fresh-intervention status")
    if document["action_unit"] != ACTION_UNITS[family_id]:
        raise ValueError("physical action units differ from the family contract")
    if not isinstance(document["source_id"], str) or not document["source_id"].strip():
        raise ValueError("physical source requires an explicit provenance identity")
    if document["receiver_unit"] != RECEIVER_UNITS[family_id]:
        raise ValueError("physical receiver unit differs from the explicit family contract")
    if family_id == "R16" and document["forcing_unit"] != "Pa.m^3.s^-1":
        raise ValueError("MAST-U gas-rate units must be Pa.m^3.s^-1")
    if not isinstance(document["units"], list) or not document["units"]:
        raise ValueError("physical input requires a nonempty complete independent-unit roster")
    units = {}
    for raw in document["units"]:
        required = {"unit_id", "split", "preparation_time_s", "preparation", "episodes"}
        if family_id == "R22":
            required |= {"native_preparation", "mapping_assumptions"}
        _keys(raw, required, "independent unit")
        unit_id = raw["unit_id"]
        if not isinstance(unit_id, str) or not unit_id.strip() or unit_id in units:
            raise ValueError("physical independent-unit IDs must be nonempty and unique")
        if raw["split"] not in {"calibration", "evaluation"}:
            raise ValueError("physical cohort split must be calibration or evaluation")
        if _number(raw["preparation_time_s"], "preparation_time_s") >= 0:
            raise ValueError("all preparation/history coordinates must precede action time zero")
        _keys(raw["preparation"], PREPARATION_FIELDS[family_id], "preparation")
        for name, value in raw["preparation"].items():
            number = _number(value, name)
            if name == "initial_soc" and not 0 < number < 1:
                raise ValueError("initial_soc must lie strictly inside (0,1)")
            if name in {"resistance_mohm", "resonance_hz", "initial_temperature_k", "core_temperature_ev",
                        "density_1e19_m3", "heating_power_w"} and number <= 0:
                raise ValueError(f"{name} must be positive in its declared unit")
        if not isinstance(raw["episodes"], list):
            raise ValueError("logged episode census must be a list, including an empty list")
        seen_actions = set()
        for episode in raw["episodes"]:
            _keys(episode, {"action", "status", "reason", "data"}, "logged episode")
            action = _number(episode["action"], "episode action")
            if action in seen_actions:
                raise ValueError("replicated observations need separate units or an authored nested reducer")
            seen_actions.add(action)
            if episode["status"] not in {"complete", "unavailable", "failed"}:
                raise ValueError("logged episode has an unsupported status")
            if not isinstance(episode["reason"], str):
                raise ValueError("logged episode reason must be a string")
            if episode["status"] == "complete" and episode["reason"]:
                raise ValueError("complete logged episode cannot carry a failure reason")
            if episode["status"] != "complete" and (not episode["reason"] or episode["data"] is not None):
                raise ValueError("missing/failed logged episode needs a reason and null data")
        if family_id == "R22":
            assumptions = raw["mapping_assumptions"]
            if not isinstance(assumptions, list) or not assumptions or any(not isinstance(x, str) or not x for x in assumptions):
                raise ValueError("MAST/TORAX mapping requires explicit nonempty assumption IDs")
            if len(set(assumptions)) != len(assumptions):
                raise ValueError("mapping assumption IDs must be unique")
        units[unit_id] = raw
    return PhysicalCohort(family_id, document["source_id"], sha256(payload).hexdigest(),
                          document["receiver_unit"], units)


def cohort_from_request(request):
    """Select one explicit transport; production receives the typed pinned JSON."""
    if request.input_json is not None:
        if request.input_path is not None:
            raise ValueError("select exactly one physical input transport")
        return decode_cohort(request.input_json.encode("utf-8"), request.family_id)
    if request.input_path is not None:
        return load_cohort(request.input_path, request.family_id)
    raise ValueError("physical family requires explicitly supplied pinned raw cohort JSON")


class _UnmatchedHeatingOption(ValueError):
    def __init__(self, error):
        self.maximum_fractional_error = error
        super().__init__("measured power lies outside the selected action band")


def _reduce(family_id, data, action, horizon, parameters, preparation):
    diagnostics = ()
    if family_id == "R13":
        _keys(data, {"duration_s", "spike_times_s"}, "cortical trace")
        duration = _number(data["duration_s"], "duration_s")
        if duration < horizon:
            raise ValueError("recorded cortical episode does not cover the requested horizon")
        # Validate against acquisition duration before selecting the nested horizon.
        firing_rate(data["spike_times_s"], horizon_s=duration)
        spikes = [value for value in data["spike_times_s"] if value <= horizon]
        values = {"firing_rate_hz": firing_rate(spikes, horizon_s=horizon)}
    elif family_id == "R14":
        _keys(data, {"time_s", "position_rad", "drive_v"}, "optical trace")
        _, drive = truncate_at(data["time_s"], data["drive_v"], horizon)
        if not np.allclose(drive, action, rtol=0, atol=1e-9):
            raise ValueError("recorded mirror drive differs from the declared signed step")
        values = {"displacement_rad": signed_displacement(data["time_s"], data["position_rad"], horizon_s=horizon)}
    elif family_id == "R15":
        _keys(data, {"time_s", "current_a", "voltage_v", "temperature_k", "voltage_uncertainty_v", "capacity_uncertainty_ah"}, "battery trace")
        _, current = truncate_at(data["time_s"], data["current_a"], horizon)
        if not np.allclose(current, action, rtol=0, atol=parameters["current_tracking_tolerance_a"]):
            raise ValueError("recorded battery current differs from the declared constant action")
        receiver = battery_receivers(data["time_s"], data["current_a"], data["voltage_v"], data["temperature_k"], horizon_s=horizon)
        values = {"terminal_voltage_v": receiver.terminal_voltage_v, "discharge_capacity_ah": receiver.discharge_capacity_ah}
        uncertainties = tuple((name, _number(data[name], name)) for name in ("voltage_uncertainty_v", "capacity_uncertainty_ah"))
        if any(value < 0 for _, value in uncertainties):
            raise ValueError("physical battery source uncertainties cannot be negative")
        diagnostics = uncertainties
    elif family_id == "R16":
        _keys(data, {"time_s", "gas_rate", "receiver"}, "divertor trace")
        response = divertor_modulation(data["time_s"], data["gas_rate"], data["receiver"], frequency_hz=action, horizon_s=horizon)
        values = {"response_real": response.real, "response_imag": response.imag}
        diagnostics = (("input_amplitude", response.input_amplitude), ("harmonic_residual_rms", response.residual_rms),
                       ("harmonic_condition", response.condition_number))
    elif family_id == "R22":
        maximum_gap = None
        if isinstance(data, Mapping) and "power_time_s" in data:
            _keys(data, {"time_s", "core_temperature_ev", "power_time_s", "power_w"}, "measured MAST heating trace")
            tracking = parameters.get("recorded_power_tracking")
            if tracking is None:
                raise ValueError("measured NBI requires an authored recorded_power_tracking selection")
            deviation = heating_tracking_error(data["power_time_s"], data["power_w"], baseline_w=preparation["heating_power_w"],
                                               action=action, horizon_s=horizon, maximum_sample_gap_s=tracking["max_power_gap_s"])
            if deviation > tracking["max_fraction_error"]:
                raise _UnmatchedHeatingOption(deviation)
            diagnostics = (("maximum_fractional_tracking_error", deviation),)
            maximum_gap = tracking["max_temperature_gap_s"]
        else:
            _keys(data, {"time_s", "core_temperature_ev", "heating_fraction"}, "MAST heating trace")
            if _number(data["heating_fraction"], "heating_fraction") != action:
                raise ValueError("MAST realized heating fraction differs from the logged option")
        values = {"archive_temperature_change_ev": temperature_change(data["time_s"], data["core_temperature_ev"],
                                                                       horizon_s=horizon, maximum_sample_gap_s=maximum_gap)}
    else:
        raise ValueError("unsupported raw physical family")
    return values, tuple(sorted(diagnostics))


def archive_rows(request, cohort: PhysicalCohort, parameters):
    from empirical_lawhood.science.joint_description import TrialRow
    receivers = selected_receivers(request)
    if request.family_id == "R22":
        receivers = ("archive_temperature_change_ev",)
    rows = []
    for unit_id in request.unit_ids:
        unit = cohort.selected_unit(unit_id, request.split)
        episodes = {float(row["action"]): row for row in unit["episodes"]}
        for action in request.actions:
            for horizon in request.horizons:
                features = feature_vector(request.family_id, unit["preparation"], action, horizon)
                episode = episodes.get(action)
                status, reason, values, diagnostics = "unsupported", "UNLOGGED_ACTION_NO_COUNTERFACTUAL", {}, ()
                if episode is not None:
                    if episode["status"] == "complete":
                        try:
                            values, diagnostics = _reduce(request.family_id, episode["data"], action, horizon, parameters, unit["preparation"])
                            status, reason = "supported", ""
                        except _UnmatchedHeatingOption as error:
                            reason = "MEASURED_NBI_OUTSIDE_OPTION_BAND"
                            diagnostics = (("maximum_fractional_tracking_error", error.maximum_fractional_error),)
                        except (ValueError, TypeError, KeyError, np.linalg.LinAlgError) as error:
                            status, reason = "failed", f"RAW_RECEIVER_INVALID:{type(error).__name__}:{error}"
                    else:
                        status = "failed" if episode["status"] == "failed" else "unsupported"
                        reason = episode["reason"]
                for receiver in receivers:
                    rows.append(TrialRow(unit_id=unit_id, action=action, horizon=horizon, receiver_id=receiver,
                                         features=features, outcome=values.get(receiver), status=status,
                                         reason=reason, work_units=1.0, diagnostics=diagnostics))
    return tuple(rows)


def produce_archive(request):
    from empirical_lawhood.science.joint_description import TrialBatch
    parameters = resolve_parameters(request)
    if request.device != "cpu":
        raise ValueError("archive reduction is a local CPU operation")
    cohort = cohort_from_request(request)
    return TrialBatch(request.family_id, request.split, archive_rows(request, cohort, parameters), "recorded-archive",
                      (f"source:{cohort.source_id}", f"sha256:{cohort.content_sha256}",
                       f"receiver_unit:{cohort.receiver_unit}", "logged-action-options-only",
                       "no-prospective-physical-control-claim"))
