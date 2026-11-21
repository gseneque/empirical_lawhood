"""Deterministic reference forecasts from authenticated in-memory equation bytes.

This evaluator executes the published, digest-pinned local equations on NumPy
arrays. It opens no external source, device, engine or process. Native plant
acquisition and delivery remain separate adapter operations.
"""

from __future__ import annotations
import ast
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import sys
from types import ModuleType, SimpleNamespace
from typing import Any
from uuid import uuid4
import numpy as np
from empirical_lawhood.domains.reactor.reactor_prefix_response.numeric_values import _decimal
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import PARAMS_SHA256, PLANT_SHA256, ReactorCommand, ReactorMeasurement

from empirical_lawhood.domains.reactor.reactor_prefix_response.forecast_contracts import (
    REFERENCE_SHA256,
    ReactorForecastState,
    ReactorPointForecast,
)

def _load_pinned_module(source: bytes) -> ModuleType:
    name = f"_reactor_forecast_{uuid4().hex}"
    module = ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(source, "<pinned-reactor-forecast-source>", "exec"), module.__dict__)
        return module
    finally:
        sys.modules.pop(name, None)

def _native_actuator_projection(source: bytes, namespace: dict[str, Any]) -> Any:
    """Reuse the pinned actuator statements verbatim as a pure prediction map.

    The execution bridge independently observes what the plant actually did.
    Extracting this closed source block avoids maintaining another actuator
    implementation. Configuration cannot select statements or executable code.
    """
    tree = ast.parse(source)
    simulate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "simulate")
    loop = next(
        n
        for n in simulate.body
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "step"
    )
    start = next(
        i
        for i, n in enumerate(loop.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "window_open" for t in n.targets)
    )
    end = next(
        i
        for i, n in enumerate(loop.body)
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "k"
    )
    wrapper = ast.parse(
        "def project(params, t_now, dosed, feed_applied, tj_applied, feed_req, tj_req):\n    pass\n"
    )
    function = wrapper.body[0]
    assert isinstance(function, ast.FunctionDef)
    function.body = (
        loop.body[start:end]
        + ast.parse("return feed_target, tj_target, feed_applied, tj_applied").body
    )
    exec(
        compile(ast.fix_missing_locations(wrapper), "<pinned-native-actuator-projection>", "exec"),
        namespace,
    )
    return namespace["project"]

class ReferenceObserverReactorForecast:
    """Unmodified reference observer plus a ten-second nominal native forecast."""

    def __init__(self, *, plant_bytes: bytes, params_bytes: bytes, reference_bytes: bytes) -> None:
        for source, expected in (
            (plant_bytes, PLANT_SHA256),
            (params_bytes, PARAMS_SHA256),
            (reference_bytes, REFERENCE_SHA256),
        ):
            if sha256(source).hexdigest() != expected:
                raise ValueError("causal reactor forecast source differs from its exact pin")
        self._native: Any = _load_pinned_module(plant_bytes)
        native: Any = self._native
        native.pathlib = SimpleNamespace(
            Path=lambda _: SimpleNamespace(read_text=lambda: params_bytes.decode())
        )
        self._params = self._native.PlantParams.from_json("authenticated-public-spec")
        self._controller: Any = _load_pinned_module(reference_bytes).Controller()
        self._controller.reset(json.loads(params_bytes))
        self._actuator = _native_actuator_projection(plant_bytes, {"np": np})
        self._feed = 0.0
        self._jacket = self._params.tj0_k
        self._next_time = Decimal(0)
        self._pending: ReactorForecastState | None = None

    def observe(self, measurement: ReactorMeasurement) -> ReactorForecastState:
        if (
            self._pending is not None
            or measurement.time_s != self._next_time
            or measurement.sample_dt_s != 10
        ):
            raise ValueError("forecast observation must follow its previous committed command")
        c = self._controller
        feed, jacket = c.step(
            float(measurement.time_s),
            {
                "t_reactor_k": float(measurement.t_reactor_k),
                "t_jacket_k": float(measurement.t_jacket_k),
                "dosed_kg": float(measurement.dosed_kg),
            },
            10.0,
        )
        self._pending = ReactorForecastState(
            measurement,
            *(
                _decimal(v)
                for v in (
                    c.n_a,
                    c.n_b,
                    c.volume,
                    c.filt_t + c.dtdt * c.p["jac_pred"],
                    c.filt_tj,
                    c.ua_est,
                    c.keff,
                    self._feed,
                    self._jacket,
                    feed,
                    jacket,
                )
            ),
        )
        return self._pending

    def _stages(
        self, state: ReactorForecastState, command: ReactorCommand
    ) -> tuple[float, float, float, float]:
        if command.time_s != state.measurement.time_s:
            raise ValueError("forecast command uses another observation clock")
        result = self._actuator(
            self._params,
            float(command.time_s),
            float(state.measurement.dosed_kg),
            float(state.previous_feed_kg_s),
            float(state.previous_jacket_k),
            float(command.feed_kg_s),
            float(command.jacket_k),
        )
        return tuple(float(v) for v in result)  # type: ignore[return-value]

    def predict(
        self, state: ReactorForecastState, command: ReactorCommand, *, plant_dt_s: Decimal
    ) -> ReactorPointForecast:
        if state != self._pending or plant_dt_s not in (Decimal(1), Decimal("0.5")):
            raise ValueError(
                "forecast requires the current causal state and a declared numerical view"
            )
        _, _, feed, jacket = self._stages(state, command)
        params = replace(self._params, ua0_w_per_k=float(state.ua_estimate_w_per_k))
        scenario = self._native.Scenario(
            "nominal-forecast",
            0,
            1.0,
            1e9,
            0.0,
            (1e9, 1e9),
            0.0,
            1e9,
            float(state.kinetic_multiplier),
        )
        x = np.asarray(
            [
                float(v)
                for v in (
                    state.n_a_mol,
                    state.n_b_mol,
                    state.volume_m3,
                    state.t_estimate_k,
                    state.tj_estimate_k,
                )
            ]
        )
        dose = float(state.measurement.dosed_kg)
        peak = float(x[3])
        dt = float(plant_dt_s)
        for index in range(int(10 / dt)):
            delivered = min(feed, max(params.dose_total_kg - dose, 0.0) / dt)
            x = self._native.rk4_step(
                params, scenario, float(command.time_s) + index * dt, x, delivered, jacket, dt
            )
            dose += delivered * dt
            peak = max(peak, float(x[3]))
        return ReactorPointForecast(
            state.fingerprint(),
            command,
            plant_dt_s,
            *(_decimal(v) for v in (peak, x[3], dose, 1.0 - x[1] / params.n_b0_mol, feed, jacket)),
        )

    def commit(self, state: ReactorForecastState, command: ReactorCommand) -> None:
        """Advance public request history; this is not evidence of native delivery."""
        if state != self._pending:
            raise ValueError("forecast commitment is stale or already consumed")
        _, _, self._feed, self._jacket = self._stages(state, command)
        # Preserve the upstream policy's own requested-command history. The
        # separate actuator projection tracks predicted applied history.
        self._controller.tj_cmd_last = float(command.jacket_k)
        self._pending = None
        self._next_time += Decimal(10)

    def predict_requested_tape(
        self,
        state: ReactorForecastState,
        commands: tuple[ReactorCommand, ...],
        *,
        plant_dt_s: Decimal,
    ) -> np.ndarray:
        """Roll a finite open-loop tape from the current causal observer state.

        This uses the same pinned nominal RK4 and actuator as ``predict``.
        There are no future observer updates, scenario-truth inputs or changes
        to the live observer. The output is a private comparator forecast,
        never a measurement or a qualified response law.
        """
        if (
            state != self._pending
            or plant_dt_s not in (Decimal(1), Decimal("0.5"))
            or not 1 <= len(commands) <= 12
            or any(c.time_s != state.measurement.time_s + 10 * i for i, c in enumerate(commands))
        ):
            raise ValueError("finite forecast changed its causal state or command clocks")
        params = replace(self._params, ua0_w_per_k=float(state.ua_estimate_w_per_k))
        scenario = self._native.Scenario(
            "nominal-forecast",
            0,
            1.0,
            1e9,
            0.0,
            (1e9, 1e9),
            0.0,
            1e9,
            float(state.kinetic_multiplier),
        )
        x = np.asarray(
            [
                float(v)
                for v in (
                    state.n_a_mol,
                    state.n_b_mol,
                    state.volume_m3,
                    state.t_estimate_k,
                    state.tj_estimate_k,
                )
            ]
        )
        dose, dt = float(state.measurement.dosed_kg), float(plant_dt_s)
        feed, jacket = float(state.previous_feed_kg_s), float(state.previous_jacket_k)
        rows = [(float(state.measurement.time_s), float(x[3]))]
        for command in commands:
            _, _, feed, jacket = self._actuator(
                self._params,
                float(command.time_s),
                dose,
                feed,
                jacket,
                float(command.feed_kg_s),
                float(command.jacket_k),
            )
            for index in range(int(10 / dt)):
                delivered = min(feed, max(params.dose_total_kg - dose, 0.0) / dt)
                time = float(command.time_s) + index * dt
                x = self._native.rk4_step(params, scenario, time, x, delivered, jacket, dt)
                dose += delivered * dt
                rows.append((time + dt, float(x[3])))
        result = np.asarray(rows)
        if not np.isfinite(result).all():
            raise FloatingPointError("nonfinite finite-tape nominal forecast")
        return result
