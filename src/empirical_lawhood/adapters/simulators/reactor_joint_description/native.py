"""Native reactor action panels with a closed pre-decision information barrier.

Only this adapter creates native workers.  Every branch is joined before its
truth grid is evaluated.  All branches of a root reuse the same preparation and
noise seed; calibration and evaluation use their authored disjoint unit IDs.
"""

from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import TYPE_CHECKING, Callable

import numpy as np

from empirical_lawhood.adapters.simulators.reactor_prefix_response.packaged_source import (
    load_packaged_reactor_source,
)
from empirical_lawhood.adapters.simulators.reactor_prefix_response.prefix_bridge import ReactorPrefixBridge
from empirical_lawhood.adapters.simulators.reactor_prefix_response.bridge import ReactorWorkerStopError
from empirical_lawhood.domains.reactor.joint_description import (
    RECEIVERS, ReactorPreparation, assigned_scenario, preparation, receiver_values, visible_features,
)
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand, ReactorDelivery

if TYPE_CHECKING:
    from empirical_lawhood.science.joint_description import TrialBatch, TrialRequest


def _validate_request(request: TrialRequest) -> tuple[ReactorPreparation, Decimal]:
    if request.family_id not in {"R20", "R21"} or request.device != "cpu":
        raise ValueError("pinned reactor native implementation requires R20/R21 on CPU")
    plan = preparation(request)
    if (
        not request.horizons or not request.actions
        or any(not np.isfinite(h) or h <= 0 or h % 10 != 0 for h in request.horizons)
        or any(not np.isfinite(a) or not 0 <= a <= 0.032 for a in request.actions)
        or plan.decision_seconds + max(request.horizons) >= 28800
    ):
        raise ValueError("reactor action/horizon menu must remain on the native callback grid")
    dt = Decimal(str(request.parameters.get("plant_dt_s", 1.0)))
    if dt not in (Decimal(1), Decimal("0.5")):
        raise ValueError("reactor integration admits the pinned native or half-step view")
    return plan, dt


def _receivers(request: TrialRequest) -> tuple[str, ...]:
    selected = tuple(request.parameters.get("receivers", RECEIVERS))
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(RECEIVERS):
        raise ValueError("reactor request names an unimplemented or repeated receiver")
    return selected


def _advance_preparation(bridge, plan: ReactorPreparation, branch_id: str):
    measurement = bridge.start()
    history = deque((measurement,), maxlen=plan.history_samples)
    last_feed, last_jacket, deliveries = 0.0, 316.0, 0
    while float(measurement.time_s) < plan.decision_seconds:
        command = ReactorCommand(
            f"joint-preparation-{branch_id}-{deliveries}", measurement.time_s,
            Decimal(str(plan.feed_at(float(measurement.time_s)))), Decimal(str(plan.jacket_k)),
        )
        delivery = bridge.advance(command)
        if not isinstance(delivery, ReactorDelivery):
            raise ValueError("reactor preparation unexpectedly exhausted the native batch")
        deliveries += 1
        measurement = delivery.next_measurement
        last_feed = float(delivery.applied_feed_kg_s)
        last_jacket = float(delivery.applied_jacket_k)
        history.append(measurement)
    if len(history) != plan.history_samples:
        raise ValueError("reactor decision lacks its complete predeclared history")
    return tuple(history), last_feed, last_jacket, deliveries


class ReactorJointDescriptionPort:
    """Task-local native port; no scheduler, output directory or implicit storage."""

    def __init__(self, *, progress: Callable[[str], None] | None = None) -> None:
        self._progress = progress

    def prepare_predictors(self, request: TrialRequest) -> TrialBatch:
        """Stop each native root at its decision callback, before intervention.

        No truth property is read, and no requested action is delivered.  Later
        response acquisition repeats this deterministic prefix and must match
        the persisted feature bytes.  Prefix work is retained separately.
        """
        from empirical_lawhood.science.joint_description import TrialBatch, TrialRow

        plan, dt = _validate_request(request)
        receivers = _receivers(request)
        source = load_packaged_reactor_source()
        rows = []
        for unit_id in request.unit_ids:
            scenario = assigned_scenario(request, unit_id)
            try:
                with ReactorPrefixBridge(
                    plant_bytes=source.plant_source.encode(),
                    params_bytes=source.plant_params.encode(),
                    public_scenarios_bytes=source.public_scenarios.encode(),
                    plant_dt_s=dt, assigned_scenario=scenario,
                ) as bridge:
                    history, last_feed, last_jacket, _ = _advance_preparation(bridge, plan, "predictors")
                for action in request.actions:
                    for horizon in request.horizons:
                        features = visible_features(history, applied_feed_kg_s=last_feed,
                            applied_jacket_k=last_jacket, action_kg_s=float(action), horizon_s=float(horizon))
                        for receiver_id in receivers:
                            rows.append(TrialRow(unit_id, float(action), float(horizon), receiver_id,
                                features, None, "unsupported", "not-yet-acquired",
                                work_units=plan.decision_seconds / float(dt)
                                    / (len(request.actions) * len(request.horizons) * len(receivers))))
            except ReactorWorkerStopError:
                raise
            except (RuntimeError, ValueError, ArithmeticError) as error:
                for action in request.actions:
                    for horizon in request.horizons:
                        for receiver_id in receivers:
                            rows.append(TrialRow(unit_id, float(action), float(horizon), receiver_id,
                                (), None, "failed", f"native-reactor-preparation-{type(error).__name__}:{error}"))
            if self._progress is not None:
                self._progress(f"{request.family_id}:{unit_id}:preparation-closed")
        return TrialBatch(request.family_id, request.split, tuple(rows), "pinned-native-reactor-predecision-prefix",
            ("plant-sha256:562a486d20597ebb49c74c3066933fa9762edbd2c4c5f20d06a78f300360c5b7",
             "fresh-public-envelope-scenarios", "no-response-acquisition", "no-hidden-grid-access",
             "native-prefix-work-retained-separately"))

    def acquire(self, request: TrialRequest) -> TrialBatch:
        from empirical_lawhood.science.joint_description import TrialBatch, TrialRow

        plan, dt = _validate_request(request)
        receivers = _receivers(request)
        source = load_packaged_reactor_source()
        rows = []
        for unit_id in request.unit_ids:
            scenario = assigned_scenario(request, unit_id)
            previous_features = None
            for action_index, action in enumerate(request.actions):
                feature_by_horizon = {}
                deliveries = 0
                try:
                    with ReactorPrefixBridge(
                        plant_bytes=source.plant_source.encode(),
                        params_bytes=source.plant_params.encode(),
                        public_scenarios_bytes=source.public_scenarios.encode(),
                        plant_dt_s=dt, assigned_scenario=scenario,
                    ) as bridge:
                        history, last_feed, last_jacket, deliveries = _advance_preparation(
                            bridge, plan, str(action_index))
                        measurement = history[-1]
                        for horizon in request.horizons:
                            feature_by_horizon[horizon] = visible_features(
                                tuple(history), applied_feed_kg_s=last_feed, applied_jacket_k=last_jacket,
                                action_kg_s=float(action), horizon_s=float(horizon),
                            )
                        # Repeated native preparation must be byte-identical in
                        # its *visible* context before a paired intervention.
                        identity = tuple(
                            (key, value) for key, value in feature_by_horizon[request.horizons[0]]
                            if key not in {"action", "action_horizon_kg", "action_temperature_gap"}
                        )
                        if previous_features is not None and identity != previous_features:
                            raise ValueError("paired native branches did not share the same predecision context")
                        previous_features = identity
                        while float(measurement.time_s) < plan.decision_seconds + max(request.horizons):
                            command = ReactorCommand(
                                f"joint-response-{action_index}-{deliveries}", measurement.time_s,
                                Decimal(str(action)), Decimal(str(plan.jacket_k)),
                            )
                            delivery = bridge.advance(command)
                            if not isinstance(delivery, ReactorDelivery):
                                raise ValueError("reactor response unexpectedly exhausted the native batch")
                            deliveries += 1
                            measurement = delivery.next_measurement
                    # Native truth is inaccessible until __exit__ closes and
                    # joins the worker.  Features above have no grid access.
                    grid = bridge.closed_prefix_grid
                    branch_rows = []
                    for horizon in request.horizons:
                        outcomes = receiver_values(grid, decision_s=plan.decision_seconds, horizon_s=float(horizon))
                        for receiver_id in receivers:
                            branch_rows.append(TrialRow(
                                unit_id, float(action), float(horizon), receiver_id,
                                feature_by_horizon[horizon], outcomes[receiver_id],
                                work_units=float((plan.decision_seconds + max(request.horizons)) / float(dt))
                                           / (len(request.horizons) * len(receivers)),
                                diagnostics=(("native_step_seconds", float(dt)),
                                             ("preparation_seconds", plan.decision_seconds),
                                             ("realized_scenario_seed", float(scenario.seed))),
                            ))
                    rows.extend(branch_rows)
                except ReactorWorkerStopError:
                    # An unjoined worker invalidates task-local ownership.  It
                    # must abort the task, never trigger another native branch.
                    raise
                except (RuntimeError, ValueError, ArithmeticError) as error:
                    # Preserve every scheduled cell, including unsupported or
                    # failed native contact.  Never replace it with a toy run.
                    reason = f"native-reactor-{type(error).__name__}:{error}"
                    for horizon in request.horizons:
                        for receiver_id in receivers:
                            rows.append(TrialRow(
                                unit_id, float(action), float(horizon), receiver_id,
                                feature_by_horizon.get(horizon, ()), None,
                                status="failed", reason=reason,
                                work_units=float(deliveries * 10 / float(dt))
                                           / (len(request.horizons) * len(receivers)),
                            ))
                if self._progress is not None:
                    self._progress(f"{request.family_id}:{unit_id}:action-{action_index}-closed")
        return TrialBatch(
            request.family_id, request.split, tuple(rows), "pinned-native-reactor-action-panel",
            ("plant-sha256:562a486d20597ebb49c74c3066933fa9762edbd2c4c5f20d06a78f300360c5b7",
             "fresh-public-envelope-scenarios", "paired-native-noise-and-preparation",
             "callback-observations-before-intervention", "truth-after-worker-closure",
             "heldout-simulator-action-panel-control-audit", "work-unit-native-rk4-step"),
        )


__all__ = ["ReactorJointDescriptionPort"]
