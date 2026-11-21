"""Native acquisition, external-format translation and custody integration."""

from decimal import Decimal as D
from typing import Callable, cast
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_trace import GRID_COLUMNS, GridRow, ReactorBatchTrace as ReferenceBatchTrace
from empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_trace import acquire_reference_batch
from empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_bridge import ReactorBatchBridge
from empirical_lawhood.domains.reactor.reactor_prefix_response.numeric_values import _decimal
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.design import ReactorAssignedScenario, ReactorBatchSource

from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.trace import (
    ReactorBatchTrace as _science_ReactorBatchTrace,
    ReactorHistoryForecast as _science_ReactorHistoryForecast,
    ReactorReplay as _science_ReactorReplay,
    pulse_command as _science_pulse_command,
)

def acquire_replay(
    source: ReactorBatchSource,
    donor: ReferenceBatchTrace,
    dt: D,
    pulse: bool,
    progress: Callable[[int], None] | None = None,
) -> _science_ReactorReplay:
    stages = []
    with ReactorBatchBridge(
        plant_bytes=source.plant_source.encode(),
        params_bytes=source.plant_params.encode(),
        public_scenarios_bytes=source.public_scenarios.encode(),
        assigned_scenario=donor.scenario,
        plant_dt_s=dt,
    ) as bridge:
        bridge.start()
        for i, forecast in enumerate(donor.forecasts):
            command = _science_pulse_command(forecast.command) if pulse else forecast.command
            delivery = bridge.advance(command)
            stages.append(
                (
                    delivery.accepted_feed_kg_s,
                    delivery.accepted_jacket_k,
                    delivery.applied_feed_kg_s,
                    delivery.applied_jacket_k,
                )
            )
            if progress is not None and ((i + 1) % 100 == 0 or i == 2879):
                progress(i + 1)
        result = bridge.completed_result
        grid = tuple(
            cast(GridRow, tuple(_decimal(v) for v in row))
            for row in zip(*(getattr(result, name) for name in GRID_COLUMNS), strict=True)
        )
    return _science_ReactorReplay(dt, pulse, tuple(stages), grid)

def acquire_history_unit(
    source: ReactorBatchSource,
    scenario: ReactorAssignedScenario,
    progress: Callable[[int], None] | None = None,
) -> _science_ReactorBatchTrace:
    from empirical_lawhood.adapters.simulators.reactor_matched_replay_forecast.forecast import forecast_history

    def tick(episode: int) -> Callable[[int], None] | None:
        return None if progress is None else lambda n: progress(episode * 2880 + n)

    native = acquire_reference_batch(source, scenario, D(1), tick(0))
    refined = acquire_reference_batch(source, scenario, D(".5"), tick(1))
    if native.failure_code or refined.failure_code:
        return _science_ReactorBatchTrace(
            scenario,
            source.fingerprint(),
            (native, refined),
            None,
            None,
            None,
            (),
            "ASSIGNED_REFERENCE_FAILURE",
        )
    predictions: tuple[_science_ReactorHistoryForecast, ...] = ()
    matched = pulse_native = pulse_refined = None
    failure = None
    try:
        # Predicted shadow paths precede contact with either pulse outcome.
        predictions = tuple(forecast_history(source, native, dt) for dt in (D(1), D(".5")))
        matched = acquire_replay(source, native, D(".5"), False, tick(2))
        pulse_native = acquire_replay(source, native, D(1), True, tick(3))
        pulse_refined = acquire_replay(source, native, D(".5"), True, tick(4))
    except (OverflowError, FloatingPointError):
        failure = "ASSIGNED_REPLAY_OR_SHADOW_FAILURE"
    except ValueError as error:
        if str(error) != "native reactor emitted a nonfinite value":
            raise
        failure = "ASSIGNED_REPLAY_OR_SHADOW_FAILURE"
    except RuntimeError as error:
        cause = error.__cause__
        numerical = isinstance(cause, (OverflowError, FloatingPointError)) or (
            isinstance(cause, ValueError)
            and str(cause) == "native reactor emitted a nonfinite value"
        )
        if str(error) != "native reactor failed; no completion evidence" or not numerical:
            raise
        failure = "ASSIGNED_REPLAY_OR_SHADOW_FAILURE"
    return _science_ReactorBatchTrace(
        scenario,
        source.fingerprint(),
        (native, refined),
        matched,
        pulse_native,
        pulse_refined,
        predictions,
        failure,
    )
