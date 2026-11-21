"""Fresh reactor response atlases and paired prospective policy ingredients.

This module owns preparation families, pre-decision information channels and
receiver meanings.  The native plant and acquisition lifecycle remain behind
an injected adapter port.  No historical result, historical qualification or
campaign recipe is an operand.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import random
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import (
    ReactorAssignedScenario,
)
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorMeasurement
from empirical_lawhood.science.identity.references import NamedDecimal

if TYPE_CHECKING:
    from empirical_lawhood.science.joint_description import TrialBatch, TrialRequest


RECEIVERS = ("peak_temperature_k", "conversion_b", "delivered_mass_kg")


class ReactorPanelPort(Protocol):
    def acquire(self, request: TrialRequest) -> TrialBatch: ...
    def prepare_predictors(self, request: TrialRequest) -> TrialBatch: ...


@dataclass(frozen=True, slots=True)
class ReactorPreparation:
    decision_seconds: float
    history_samples: int
    preparation_feed_kg_s: float
    jacket_k: float
    feed_history: str

    def __post_init__(self) -> None:
        if (
            not np.isfinite((self.decision_seconds, self.preparation_feed_kg_s, self.jacket_k)).all()
            or not 600 <= self.decision_seconds < 25200
            or self.decision_seconds % 10 != 0
            or type(self.history_samples) is not int
            or not 2 <= self.history_samples <= 128
            or self.history_samples * 10 > self.decision_seconds
            or not 0 <= self.preparation_feed_kg_s <= 0.032
            or not 279.3 <= self.jacket_k <= 347.6
            or self.feed_history not in {"constant", "switching"}
        ):
            raise ValueError("reactor preparation changes the native physical/measurement envelope")

    def feed_at(self, time_s: float) -> float:
        """Authored preparation command; all action branches share these bytes."""
        if time_s < 600:
            return 0.0
        if self.feed_history == "switching":
            return self.preparation_feed_kg_s * (0.5 if int((time_s - 600) // 300) % 2 else 1.5)
        return self.preparation_feed_kg_s


def preparation(request: TrialRequest) -> ReactorPreparation:
    parameters = request.parameters
    samples = parameters.get("history_samples", 6 if request.family_id == "R20" else 12)
    if type(samples) is not int:
        raise ValueError("reactor history sample count must be an authored integer")
    return ReactorPreparation(
        float(parameters.get("preparation_seconds", 3600 if request.family_id == "R20" else 9000)),
        samples,
        float(parameters.get("preparation_feed_kg_s", 0.012)),
        float(parameters.get("jacket_k", 316.0)),
        str(parameters.get("feed_history", "constant" if request.family_id == "R20" else "switching")),
    )


def assigned_scenario(request: TrialRequest, unit_id: str) -> ReactorAssignedScenario:
    """A fresh public-envelope draw, independent of the original seed schedule.

    Fault and realized plant parameters are evaluator-only.  They never enter
    ``visible_features``.  Action branches deliberately reuse the same draw
    and native noise seed so their comparison is paired at the physical root.
    """
    digest = sha256(f"new-reactor-joint-description:{request.family_id}:{request.seed}:{unit_id}".encode()).digest()
    seed = int.from_bytes(digest[:4], "big")
    rng = random.Random(seed)

    def uniform(low: float, high: float) -> Decimal:
        return Decimal(f"{rng.uniform(low, high):.12f}")

    c1, c2 = uniform(0.4, 1.0), uniform(0.4, 1.0)
    c3 = uniform(0.4, float(c2))
    fouling = uniform(0, min(0.4, 1 - 0.3 / float(min(c1, c2, c3))))
    fouling = min(fouling, 1 - Decimal(".3") / min(c1, c2, c3))
    return ReactorAssignedScenario(
        unit_id, "calibration" if request.split == "calibration" else "heldout", seed,
        (c1, c2, c3), (uniform(0, 1200), uniform(3000, 5400), uniform(9000, 18000)),
        fouling, (uniform(3000, 9000), uniform(10800, 18000)),
        uniform(-14, 14), uniform(1800, 7200), uniform(0.7, 1.3), uniform(-0.6, 1.2),
        tuple(NamedDecimal(key, uniform(1 - band, 1 + band), "1") for key, band in (
            ("dh", 0.12), ("ea", 0.02), ("jacket_tau", 0.12),
            ("k0", 0.12), ("rho_cp", 0.06), ("ua0", 0.12),
        )),
    )


def visible_features(
    history: tuple[ReactorMeasurement, ...],
    *,
    applied_feed_kg_s: float,
    applied_jacket_k: float,
    action_kg_s: float,
    horizon_s: float,
) -> tuple[tuple[str, float], ...]:
    """Information available before intervention; no simulator truth argument.

    Temperatures retain the native measurement delay and noise.  Current dose
    and previous applied actuator settings are distinct interface channels.
    Trends summarize actual recorded pre-decision measurements; they are not
    extra independent replications.
    """
    if len(history) < 2 or any(
        float(right.time_s - left.time_s) != 10
        for left, right in zip(history, history[1:])
    ):
        raise ValueError("reactor information requires a contiguous pre-decision callback history")
    if not np.isfinite((applied_feed_kg_s, applied_jacket_k, action_kg_s, horizon_s)).all() or horizon_s <= 0:
        raise ValueError("reactor forecast coordinates must be finite and prospective")
    first, current = history[0], history[-1]
    elapsed = float(current.time_s - first.time_s)
    reactor = float(current.t_reactor_k)
    jacket = float(current.t_jacket_k)
    trend = (reactor - float(first.t_reactor_k)) / elapsed
    jacket_trend = (jacket - float(first.t_jacket_k)) / elapsed
    gap = reactor - jacket
    values = {
        "action": action_kg_s,
        "action_horizon_kg": action_kg_s * horizon_s,
        "action_temperature_gap": action_kg_s * horizon_s * gap,
        "applied_feed_kg_s": applied_feed_kg_s,
        "applied_jacket_k": applied_jacket_k,
        "dosed_kg": float(current.dosed_kg),
        "horizon": horizon_s,
        "horizon_temperature_gap": horizon_s * gap,
        "jacket_temperature_k": jacket,
        "jacket_trend_k_s": jacket_trend,
        "reactor_temperature_k": reactor,
        "reactor_trend_k_s": trend,
        "temperature_gap_k": gap,
        "trend_horizon_k": trend * horizon_s,
    }
    for index, measurement in enumerate(reversed(history[:-1]), start=1):
        values[f"reactor_lag_{index:03d}_k"] = float(measurement.t_reactor_k)
        values[f"jacket_lag_{index:03d}_k"] = float(measurement.t_jacket_k)
    return tuple(sorted(values.items()))


def receiver_values(
    closed_grid: NDArray[np.float64], *, decision_s: float, horizon_s: float
) -> dict[str, float]:
    """Evaluate the exact native window only after the branch is closed."""
    grid = np.asarray(closed_grid, dtype=np.float64)
    if grid.ndim != 2 or grid.shape[1] != 8 or not len(grid) or not np.isfinite(grid).all():
        raise ValueError("reactor receiver requires a complete finite native grid")
    start = np.flatnonzero(grid[:, 0] == decision_s)
    end = np.flatnonzero(grid[:, 0] == decision_s + horizon_s)
    if len(start) != 1 or len(end) != 1 or end[0] <= start[0]:
        raise ValueError("reactor receiver window lacks exact decision and endpoint clocks")
    window = grid[start[0]:end[0] + 1]
    increments = np.diff(window[:, 0])
    if not np.all(increments == increments[0]) or increments[0] not in (0.5, 1.0):
        raise ValueError("reactor receiver window has a missing native integration point")
    return {
        "peak_temperature_k": float(np.max(window[:, 1])),
        "conversion_b": float(window[-1, 4]),
        "delivered_mass_kg": float(window[-1, 3] - window[0, 3]),
    }


def validate_specification(specification) -> None:
    """Keep edited reactor preparations and declared information costs aligned."""
    if specification.family_id not in {"R20", "R21"}:
        raise ValueError("reactor specification validator owns R20/R21 only")
    parameters = json.loads(specification.parameters_json)
    known = {"preparation_seconds", "history_samples", "preparation_feed_kg_s", "jacket_k",
             "feed_history", "plant_dt_s", "action_units", "horizon_units"}
    if set(parameters) - known:
        raise ValueError("reactor specification contains an unimplemented preparation parameter")
    plan = preparation(SimpleNamespace(parameters=parameters, family_id=specification.family_id))
    if (float(parameters.get("plant_dt_s", 1)) not in (0.5, 1.0)
            or parameters.get("action_units", "kg/s") != "kg/s"
            or parameters.get("horizon_units", "s") != "s"
            or any(h % 10 != 0 for h in specification.horizons)
            or float(max(specification.horizons)) + plan.decision_seconds >= 28800
            or any(not 0 <= a <= Decimal("0.032") for a in specification.actions)):
        raise ValueError("reactor actions, horizons, integration step or units differ from the native envelope")
    receiver_ids = {row.receiver_id for row in specification.receivers}
    if not receiver_ids or not receiver_ids <= set(RECEIVERS):
        raise ValueError("reactor specification names an unimplemented receiver")
    templates = next(row for row in presets() if row["family_id"] == specification.family_id)["descriptions"]
    expected = []
    for template in templates:
        template = dict(template)
        if template["id"] == "memory":
            template["features"] = tuple(value for value in template["features"] if not value.startswith("reactor_lag_")) + tuple(
                f"reactor_lag_{index:03d}_k" for index in range(1, plan.history_samples))
            template["memory_samples"] = plan.history_samples - 1
            template["forecast_work_units"] = 14 + 2 * (plan.history_samples - 1)
        expected.append(template)
    for description in specification.descriptions:
        matches = [template for template in expected if set(template["features"]) == set(description.features)]
        if description.model != "ridge" or len(matches) != 1:
            raise ValueError("reactor description changes its implemented causal feature/history channels")
        template = matches[0]
        if any(getattr(description, field) != template[field] for field in (
                "state_dimension", "interface_dimension", "memory_dimension", "memory_samples")):
            raise ValueError("reactor information counts are stale for the selected history or channel family")
        if (description.forecast_work_unit != template["forecast_work_unit"]
                or description.forecast_work_units < template["forecast_work_units"]):
            raise ValueError("reactor forecast work budget is below the selected implementation reference estimate")


def presets() -> tuple[dict[str, object], ...]:
    base_features = ("reactor_temperature_k", "action", "horizon", "action_horizon_kg")
    joint_features = (*base_features, "jacket_temperature_k", "dosed_kg",
                      "temperature_gap_k", "action_temperature_gap", "horizon_temperature_gap",
                      "applied_feed_kg_s", "applied_jacket_k")
    policies = {
        "peak_temperature_k": {"units": "K", "target": 340.0, "scale": 20.0,
                               "max_abs_error": 1.0, "safety_upper": 356.2, "weight": 1.0},
        "conversion_b": {"units": "1", "target": 1.0, "scale": 1.0,
                         "max_abs_error": 0.03, "safety_lower": 0.0,
                         "safety_upper": 1.0, "weight": 1.0},
        "delivered_mass_kg": {"units": "kg", "target": 0.0, "scale": 10.0,
                              "max_abs_error": 0.1, "safety_lower": 0.0, "weight": 0.05},
    }
    result = []
    for family_id, history_samples, decision, horizons in (
        ("R20", 6, 3600, (30.0, 120.0, 300.0)),
        ("R21", 12, 9000, (120.0, 300.0, 600.0)),
    ):
        history_features = tuple(f"reactor_lag_{i:03d}_k" for i in range(1, history_samples))
        descriptions = (
            {"id": "joint", "features": joint_features, "model": "ridge",
             "state_dimension": 3, "interface_dimension": 2, "memory_samples": 0,
             "memory_dimension": 0,
             "rationale": "Joint current observed thermal/dose context plus delivered actuator interface; hidden plant state remains excluded."},
            {"id": "partitioned", "features": base_features, "model": "ridge",
             "state_dimension": 1, "interface_dimension": 0, "memory_samples": 0,
             "memory_dimension": 0,
             "rationale": "Single reactor-temperature module, action and horizon; no jacket, dose or actuator interface."},
            {"id": "interface", "features": (*base_features, "jacket_temperature_k", "temperature_gap_k",
                                               "action_temperature_gap", "horizon_temperature_gap",
                                               "applied_feed_kg_s", "applied_jacket_k"),
             "model": "ridge", "state_dimension": 1, "interface_dimension": 3,
             "memory_samples": 0, "memory_dimension": 0,
             "rationale": "Thermal module coupled through measured jacket and delivered actuator interface; dose omitted."},
            {"id": "memory", "features": (*base_features, "reactor_trend_k_s", "trend_horizon_k", *history_features),
             "model": "ridge", "state_dimension": 1, "interface_dimension": 0,
             "memory_samples": history_samples - 1, "memory_dimension": 1,
             "rationale": "Reactor temperature history substitutes for explicit jacket/dose/actuator channels; only predecision samples."},
        )
        feature_work = {"joint": 32, "partitioned": 8, "interface": 28,
                        "memory": 14 + 2 * (history_samples - 1)}
        descriptions = tuple({**row,
            "forecast_work_units": feature_work[row["id"]],
            "forecast_work_unit": "authored-scalar-operation",
            "forecast_work_basis": (
                "Authored per-receiver/horizon visible-feature construction proxy including reads, gap/action products and trend/history coordinates. "
                "Native prefix/response acquisition, model training and shared custody are separate; this is not measured runtime."
            )} for row in descriptions)
        result.append({
            "family_id": family_id,
            "title": "Reactor observed-state response atlas" if family_id == "R20" else "Reactor paired policy service audit",
            "question": "Which observed description supports prospective response prediction and economically useful bounded action selection?"
                        if family_id == "R20" else
                        "On identical fresh reactor roots, do interface or memory descriptions preserve policy utility under switching preparation history?",
            "receivers": RECEIVERS, "receiver_policies": policies,
            "parameters": {"preparation_seconds": decision, "history_samples": history_samples,
                           "preparation_feed_kg_s": 0.012, "jacket_k": 316.0,
                           "feed_history": "constant" if family_id == "R20" else "switching",
                           "plant_dt_s": 1.0, "action_units": "kg/s", "horizon_units": "s"},
            "actions": (0.0, 0.016, 0.032), "horizons": horizons,
            "calibration_units": 48, "evaluation_units": 32,
            "descriptions": descriptions,
        })
    return tuple(result)


def produce(request: TrialRequest, *, native_port: ReactorPanelPort | None = None) -> TrialBatch:
    if request.family_id not in {"R20", "R21"}:
        raise ValueError("reactor producer owns exactly R20 and R21")
    if native_port is None:
        raise ValueError("reactor experiment requires an injected native acquisition port")
    return native_port.acquire(request)


def prepare_predictors(request: TrialRequest, *, native_port: ReactorPanelPort | None = None) -> TrialBatch:
    """Acquire only a causal preparation prefix; no response branch is run."""
    if request.family_id not in {"R20", "R21"}:
        raise ValueError("reactor producer owns exactly R20 and R21")
    if native_port is None:
        raise ValueError("reactor preparation requires an injected native acquisition port")
    return native_port.prepare_predictors(request)


__all__ = [
    "RECEIVERS", "ReactorPanelPort", "ReactorPreparation", "assigned_scenario",
    "preparation", "presets", "prepare_predictors", "produce", "receiver_values", "visible_features", "validate_specification",
]
