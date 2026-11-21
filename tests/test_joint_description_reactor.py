"""Pure receiver math and acquisition-barrier controls; no native execution."""

from decimal import Decimal
from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.domains.reactor.joint_description import (
    RECEIVERS, assigned_scenario, preparation, receiver_values, visible_features,
)
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import (
    ReactorDelivery, ReactorExposure, ReactorMeasurement,
)
from empirical_lawhood.science.joint_description import TrialRequest


def _request():
    return TrialRequest("R20", 9341, ("fresh-root-0001",), "evaluation", (0.0, 0.016),
                        (10.0, 20.0), {"preparation_seconds": 600, "history_samples": 3})


def _measurement(time, temperature=320.0, jacket=315.0, dose=0):
    return ReactorMeasurement(Decimal(time), Decimal(10), Decimal(str(temperature)),
                              Decimal(str(jacket)), Decimal(str(dose)))


def test_assigned_scenario_is_new_paired_root_and_not_a_forecast_feature():
    request = _request()
    one = assigned_scenario(request, request.unit_ids[0])
    two = assigned_scenario(request, request.unit_ids[0])
    assert one == two
    assert one.split == "heldout"
    assert assigned_scenario(request, "another-root").seed != one.seed
    assert preparation(request).decision_seconds == 600


@pytest.mark.numerical(oracle="independent difference quotient and action-duration mass dimensions")
def test_visible_history_features_use_only_observed_past_and_explicit_action():
    history = (_measurement(580, 319.0), _measurement(590, 319.5), _measurement(600, 320.0))
    features = dict(visible_features(history, applied_feed_kg_s=0.01, applied_jacket_k=316.0,
                                     action_kg_s=0.02, horizon_s=30.0))
    assert features["reactor_trend_k_s"] == pytest.approx(0.05)
    assert features["trend_horizon_k"] == pytest.approx(1.5)
    assert features["action_horizon_kg"] == pytest.approx(0.6)
    assert features["reactor_lag_002_k"] == 319.0
    assert not any(key in features for key in ("conversion_b", "plant_draw", "kinetic_multiplier", "outcome"))


@pytest.mark.numerical(oracle="direct maximum on inclusive sampled window, endpoint conversion and dosed-mass difference")
def test_native_grid_receiver_units_and_peak_interior():
    grid = np.zeros((21, 8))
    grid[:, 0] = np.arange(590, 611)
    grid[:, 1] = 320
    grid[15, 1] = 350
    grid[:, 3] = np.arange(21) * 0.02
    grid[:, 4] = np.arange(21) * 0.001
    values = receiver_values(grid, decision_s=600, horizon_s=10)
    assert values["peak_temperature_k"] == 350
    assert values["delivered_mass_kg"] == pytest.approx(0.2)
    assert values["conversion_b"] == pytest.approx(0.02)
    with pytest.raises(ValueError, match="missing"):
        receiver_values(np.delete(grid, 15, axis=0), decision_s=600, horizon_s=10)


class _FakeClosedPrefix:
    """Deterministic port double, never a simulator substitute in a product."""

    instances = []

    def __init__(self, **_kwargs):
        self.time = 0
        self.closed = False
        self.dose = 0.0
        self.grid = [[0, 320, 315, 0, 0, 0, 0, 316]]
        self.commands = []
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True

    def start(self):
        return _measurement(0)

    def advance(self, command):
        assert not self.closed
        self.commands.append(command)
        feed = float(command.feed_kg_s)
        old_time = self.time
        for _ in range(10):
            self.time += 1
            self.dose += feed
            self.grid.append([self.time, 320, 315, self.dose, 0.02, 0, feed, 316])
        measurement = _measurement(self.time, dose=self.dose)
        exposure = tuple(ReactorExposure(Decimal(old_time + i), Decimal(1),
                                         command.feed_kg_s, command.jacket_k) for i in range(10))
        return ReactorDelivery(command, command.feed_kg_s, command.jacket_k,
                               command.feed_kg_s, command.jacket_k, exposure, measurement)

    @property
    def closed_prefix_grid(self):
        assert self.closed, "truth crossed an open native callback boundary"
        return np.asarray(self.grid, dtype=np.float64)


def test_adapter_closes_before_truth_and_preserves_complete_paired_census(monkeypatch):
    from empirical_lawhood.adapters.simulators.reactor_joint_description import native
    _FakeClosedPrefix.instances = []
    monkeypatch.setattr(native, "ReactorPrefixBridge", _FakeClosedPrefix)
    request = _request()
    batch = native.ReactorJointDescriptionPort().acquire(request)
    batch.validate_census(request, RECEIVERS)
    assert all(row.status == "supported" for row in batch.rows)
    assert len(_FakeClosedPrefix.instances) == 2
    assert all(instance.closed for instance in _FakeClosedPrefix.instances)
    before = [_FakeClosedPrefix.instances[i].commands[:60] for i in range(2)]
    assert [c.feed_kg_s for c in before[0]] == [c.feed_kg_s for c in before[1]]
    features = [dict(row.features) for row in batch.rows]
    assert all(feature["reactor_temperature_k"] == 320 for feature in features)


def test_adapter_partial_receiver_failure_does_not_duplicate_census(monkeypatch):
    from empirical_lawhood.adapters.simulators.reactor_joint_description import native
    monkeypatch.setattr(native, "ReactorPrefixBridge", _FakeClosedPrefix)
    original = native.receiver_values

    def fail_later(grid, *, decision_s, horizon_s):
        if horizon_s == 20:
            raise ValueError("intentional late receiver failure")
        return original(grid, decision_s=decision_s, horizon_s=horizon_s)

    monkeypatch.setattr(native, "receiver_values", fail_later)
    request = _request()
    batch = native.ReactorJointDescriptionPort().acquire(request)
    batch.validate_census(request, RECEIVERS)
    assert len(batch.rows) == 12
    assert all(row.status == "failed" and row.outcome is None for row in batch.rows)


def test_unjoined_native_worker_aborts_without_another_branch(monkeypatch):
    from empirical_lawhood.adapters.simulators.reactor_joint_description import native

    class Unjoined(_FakeClosedPrefix):
        def __exit__(self, *_args):
            raise native.ReactorWorkerStopError("worker cannot join")

    _FakeClosedPrefix.instances = []
    monkeypatch.setattr(native, "ReactorPrefixBridge", Unjoined)
    with pytest.raises(native.ReactorWorkerStopError):
        native.ReactorJointDescriptionPort().acquire(_request())
    assert len(_FakeClosedPrefix.instances) == 1


def test_predictor_stage_stops_at_decision_without_truth_and_matches_later_replay(monkeypatch):
    from empirical_lawhood.adapters.simulators.reactor_joint_description import native

    class PreparationOnly(_FakeClosedPrefix):
        @property
        def closed_prefix_grid(self):
            raise AssertionError("preparation may not inspect evaluator truth")

    _FakeClosedPrefix.instances = []
    monkeypatch.setattr(native, "ReactorPrefixBridge", PreparationOnly)
    request = _request()
    request = replace(request, parameters={**request.parameters, "receivers": ("peak_temperature_k",)})
    prepared = native.ReactorJointDescriptionPort().prepare_predictors(request)
    prepared.validate_census(request, ("peak_temperature_k",))
    assert len(_FakeClosedPrefix.instances) == 1
    assert _FakeClosedPrefix.instances[0].time == 600
    assert _FakeClosedPrefix.instances[0].closed
    assert all(row.outcome is None and row.reason == "not-yet-acquired" for row in prepared.rows)
    assert sum(row.work_units for row in prepared.rows) == 600
    frozen = {row.key: row.features for row in prepared.rows}
    monkeypatch.setattr(native, "ReactorPrefixBridge", _FakeClosedPrefix)
    acquired = native.ReactorJointDescriptionPort().acquire(request)
    assert {row.key: row.features for row in acquired.rows} == frozen
