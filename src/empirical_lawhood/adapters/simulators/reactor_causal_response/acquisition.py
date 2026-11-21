"""Native acquisition, external-format translation and custody integration."""

from decimal import Decimal as D
import json
from time import process_time, monotonic
from typing import Any, Callable
import numpy as np
from empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_bridge import ReactorBatchBridge
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorAssignedScenario, ReactorBatchSource
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_trace import GRID_COLUMNS
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand, ReactorDelivery, ReactorFinalDelivery
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import branch_tape
from empirical_lawhood.domains.reactor.reactor_causal_response.controller import EmpiricalNonattempt
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import (
    ExplorationController as _science_ExplorationController,
    NativeEpisode as _science_NativeEpisode,
    TapeController as _science_TapeController,
)

from empirical_lawhood.domains.reactor.native_ports import (
    CallbackOwner as _science_CallbackOwner,
    NativeController as _science_NativeController,
)

def acquire_episode(
    source: ReactorBatchSource,
    scenario: ReactorAssignedScenario,
    episode: str,
    controller: _science_NativeController,
    *,
    dt: float = 1.0,
    bridge_factory: Callable[..., Any] = ReactorBatchBridge,
    owner: _science_CallbackOwner | None = None,
    progress: Callable[[int], None] | None = None,
    callback_wall: list[float] | None = None,
    retain_stopped_prefix: bool = False,
) -> _science_NativeEpisode:
    if dt not in (1.0, 0.5):
        raise ValueError("undeclared numerical view")
    if retain_stopped_prefix and bridge_factory is ReactorBatchBridge:
        from empirical_lawhood.adapters.simulators.reactor_prefix_response.prefix_bridge import ReactorPrefixBridge

        bridge_factory = ReactorPrefixBridge
    observations, requests, exposure, cpu = [], [], [], []
    stages: list[tuple[float, ...]] = []
    grid = np.empty((0, 8))
    failure = None
    controller.reset(json.loads(source.plant_params))
    with bridge_factory(
        plant_bytes=source.plant_source.encode(),
        params_bytes=source.plant_params.encode(),
        public_scenarios_bytes=source.public_scenarios.encode(),
        assigned_scenario=scenario,
        plant_dt_s=D(str(dt)),
    ) as bridge:
        try:
            measurement = bridge.start()
        except RuntimeError as error:
            if str(error) not in {
                "reactor delivery timed out; no completion evidence",
                "native reactor failed; no completion evidence",
            }:
                raise
            return _science_NativeEpisode(
                scenario.unit_id,
                episode,
                dt,
                np.empty((0, 4)),
                np.empty((0, 2)),
                np.empty((0, 4)),
                np.empty((0, int(10 / dt), 4)),
                grid,
                np.empty((0,)),
                "NATIVE_INITIAL_OBSERVATION_FAILURE",
            )
        for k in range(2880):
            previous = (0.0, 316.0) if not stages else (stages[-1][2], stages[-1][3])
            o = (
                float(measurement.time_s),
                float(measurement.t_reactor_k),
                float(measurement.t_jacket_k),
                float(measurement.dosed_kg),
            )
            if o[0] != k * 10:
                raise ValueError("native callback order changed")
            observations.append(o)
            wall_start = monotonic()
            start = process_time()
            try:
                requested = controller.step(
                    o[0], dict(t_reactor_k=o[1], t_jacket_k=o[2], dosed_kg=o[3]), 10.0
                )
            except EmpiricalNonattempt:
                cpu.append(process_time() - start)
                if callback_wall is not None:
                    callback_wall.append(monotonic() - wall_start)
                if owner is not None and owner.advance(controller, previous, bridge) is not None:
                    raise ValueError("a refusing policy delivered a native action")
                failure = "POLICY_NONATTEMPT"
                break
            cpu.append(process_time() - start)
            if callback_wall is not None:
                callback_wall.append(monotonic() - wall_start)
            if len(requested) != 2 or not np.isfinite(requested).all():
                failure = "NONFINITE_NATIVE_COMMAND"
                break
            command = ReactorCommand(
                f"{scenario.unit_id}.{episode.lower()}.{k:04d}",
                D(k * 10),
                D(repr(float(requested[0]))),
                D(repr(float(requested[1]))),
            )
            try:
                delivered = (
                    bridge.advance(command)
                    if owner is None
                    else owner.advance(controller, previous, bridge)
                )
            except RuntimeError as error:
                if str(error) not in {
                    "reactor delivery timed out; no completion evidence",
                    "native reactor failed; no completion evidence",
                }:
                    raise
                failure = "NATIVE_DELIVERY_FAILURE"
                break
            if delivered is None:
                failure = (
                    "OWNER_DELIVERY_FAILED"
                    if owner is not None and owner.failed
                    else "OWNER_NONATTEMPT"
                )
                break
            if owner is not None:
                command = delivered.command
                if (float(command.feed_kg_s), float(command.jacket_k)) != tuple(
                    requested
                ) or command.time_s != k * 10:
                    raise ValueError("owner delivery differs from numerical callback")
            if delivered.command != command:
                raise ValueError("native delivery changed the requested command")
            requests.append(requested)
            stages.append(
                tuple(
                    float(v)
                    for v in (
                        delivered.accepted_feed_kg_s,
                        delivered.accepted_jacket_k,
                        delivered.applied_feed_kg_s,
                        delivered.applied_jacket_k,
                    )
                )
            )
            exposure.append(
                [
                    (float(e.time_s), float(e.duration_s), float(e.feed_kg_s), float(e.jacket_k))
                    for e in delivered.exposures
                ]
            )
            if owner is not None and owner.failed:
                failure = "OWNER_INEXACT_DELIVERY"
                break
            if isinstance(delivered, ReactorDelivery):
                measurement = delivered.next_measurement
            elif not isinstance(delivered, ReactorFinalDelivery) or k != 2879:
                raise ValueError("final native interval is missing or misplaced")
            if progress is not None:
                progress(k + 1)
        if failure is None:
            result = bridge.completed_result
            grid = np.column_stack([getattr(result, name) for name in GRID_COLUMNS])
            actual = np.asarray(exposure).reshape(-1, 4)
            if not np.array_equal(actual[:, 0] + actual[:, 1], grid[1:, 0]) or not np.array_equal(
                actual[:, 2:], grid[1:, 6:8]
            ):
                raise ValueError("native result contradicts actual delivery exposures")
        elif retain_stopped_prefix:
            bridge.close()
            captured = bridge.closed_prefix_grid
            # A failed macro can have advanced farther than the recorder. Only
            # the prefix with retained actual command/exposure correspondence
            # is available here; its unknown remainder cannot become success.
            count = min(len(captured), len(requests) * int(10 / dt) + 1)
            grid = captured[:count].copy()
            actual = np.asarray(exposure).reshape(-1, 4)[: max(0, count - 1)]
            if count and (
                not np.array_equal(actual[:, 0] + actual[:, 1], grid[1:, 0])
                or not np.array_equal(actual[:, 2:], grid[1:, 6:8])
            ):
                raise ValueError("native stopped-prefix contradicts actual delivery exposures")
    return _science_NativeEpisode(
        scenario.unit_id,
        episode,
        dt,
        np.asarray(observations).reshape(-1, 4),
        np.asarray(requests).reshape(-1, 2),
        np.asarray(stages).reshape(-1, 4),
        np.asarray(exposure).reshape(-1, int(10 / dt), 4),
        grid,
        np.asarray(cpu),
        failure,
    )

def development_root(
    source: ReactorBatchSource,
    scenario: ReactorAssignedScenario,
    ordinal: int,
    *,
    bridge_factory: Callable[..., Any] = ReactorBatchBridge,
    progress: Callable[[int], None] | None = None,
) -> tuple[_science_NativeEpisode, ...]:
    if ordinal not in range(24):
        raise ValueError("undeclared development ordinal")
    result: list[_science_NativeEpisode] = []
    nominals: dict[str, _science_NativeEpisode] = {}
    completed = 0

    def emit(n: int) -> None:
        if progress is not None:
            progress(completed + n)

    exploration_policies = {
        "exploration-unshifted": 0,
        "exploration-shifted-one-position": 1,
        "exploration-shifted-two-positions": 2,
    }
    for name in ("exploration-unshifted", "exploration-shifted-one-position", "exploration-shifted-two-positions", "feed-intervention", "jacket-intervention"):
        controller: _science_NativeController
        if name in exploration_policies:
            controller = _science_ExplorationController(ordinal, exploration_policies[name])
        else:
            donor = nominals["exploration-shifted-one-position"]
            if not donor.complete:
                result.extend(
                    _science_NativeEpisode(
                        scenario.unit_id,
                        name,
                        dt,
                        np.empty((0, 4)),
                        np.empty((0, 2)),
                        np.empty((0, 4)),
                        np.empty((0, int(10 / dt), 4)),
                        np.empty((0, 8)),
                        np.empty((0,)),
                        "DONOR_TAPE_INCOMPLETE",
                    )
                    for dt in (1.0, 0.5)
                )
                continue
            anchor = (3600, 9000, 18000, 24000)[ordinal % 4] // 10
            previous_jacket = 316.0 if anchor == 0 else float(donor.stages[anchor - 1, 3])
            controller = _science_TapeController(
                np.array(
                    branch_tape(tuple(map(tuple, donor.requests)), ordinal, name, previous_jacket)
                )
            )
        nominal = acquire_episode(
            source,
            scenario,
            name,
            controller,
            bridge_factory=bridge_factory,
            progress=None if progress is None else emit,
        )
        completed += len(nominal.requests)
        nominals[name] = nominal
        refined = acquire_episode(
            source,
            scenario,
            name,
            _science_TapeController(nominal.requests),
            dt=0.5,
            bridge_factory=bridge_factory,
            progress=None if progress is None else emit,
        )
        completed += len(refined.requests)
        result.extend((nominal, refined))
    return tuple(result)

def acquire_with_progress(
    source: ReactorBatchSource,
    scenario: object,
    name: str,
    controller: _science_ExplorationController | _science_TapeController,
    dt: float,
    acquire: Callable[..., _science_NativeEpisode],
    completed_callbacks: int,
    progress: Callable[[int], None] | None,
) -> tuple[_science_NativeEpisode, int]:
    last = 0

    def emit(value: int) -> None:
        nonlocal last
        if not last < value <= 2880:
            raise ValueError("native callback progress is nonmonotone")
        last = value
        if progress is not None:
            progress(completed_callbacks + value)

    # The real callable is the installed native bridge; fixtures may inject a
    # no-effect fake. A failed call is retained and never silently retried.
    episode = (
        acquire(source, scenario, name, controller, dt=dt)
        if progress is None
        else acquire(source, scenario, name, controller, dt=dt, progress=emit)
    )
    return episode, completed_callbacks + last
