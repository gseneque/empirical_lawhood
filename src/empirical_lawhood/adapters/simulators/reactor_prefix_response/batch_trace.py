"""Native acquisition, external-format translation and custody integration."""

from decimal import Decimal
from typing import Callable, cast
from empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_bridge import ReactorBatchBridge
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorAssignedScenario, ReactorBatchSource, validate_nominal_spec
from empirical_lawhood.adapters.simulators.reactor_prefix_response.bridge import ReactorWorkerStopError
from empirical_lawhood.domains.reactor.reactor_prefix_response.numeric_values import _decimal
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand, ReactorDelivery, ReactorExposure, ReactorFinalDelivery
from empirical_lawhood.domains.reactor.reactor_prefix_response.reference_forecast import ReferenceObserverReactorForecast
from empirical_lawhood.domains.reactor.reactor_prefix_response.forecast_contracts import ReactorForecastState, ReactorPointForecast

from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_trace import (
    GRID_COLUMNS as _science_GRID_COLUMNS,
    GridRow as _science_GridRow,
    ReactorBatchTrace as _science_ReactorBatchTrace,
    StageRow as _science_StageRow,
)

def acquire_reference_batch(
    source: ReactorBatchSource,
    scenario: ReactorAssignedScenario,
    plant_dt_s: Decimal,
    progress: Callable[[int], None] | None = None,
) -> _science_ReactorBatchTrace:
    """Called only by the authorized native task runner, never by a diagnostic."""
    validate_nominal_spec(source)
    model = ReferenceObserverReactorForecast(
        plant_bytes=source.plant_source.encode(),
        params_bytes=source.plant_params.encode(),
        reference_bytes=source.reference_controller.encode(),
    )
    states: list[ReactorForecastState] = []
    predictions: list[ReactorPointForecast] = []
    stages: list[_science_StageRow] = []
    exposures: list[ReactorExposure] = []
    failure = None
    grid: tuple[_science_GridRow, ...] = ()
    with ReactorBatchBridge(
        plant_bytes=source.plant_source.encode(),
        params_bytes=source.plant_params.encode(),
        public_scenarios_bytes=source.public_scenarios.encode(),
        assigned_scenario=scenario,
        plant_dt_s=plant_dt_s,
    ) as bridge:
        try:
            measurement = bridge.start()
            for index in range(2880):
                try:
                    state = model.observe(measurement)
                    command = ReactorCommand(
                        f"{scenario.unit_id}.decision.{index:04d}",
                        measurement.time_s,
                        state.reference_feed_kg_s,
                        state.reference_jacket_k,
                    )
                    prediction = model.predict(state, command, plant_dt_s=plant_dt_s)
                except (OverflowError, FloatingPointError):
                    # Source/config/programming ValueErrors deliberately propagate.
                    failure = "FORECAST_NUMERICAL_FAILURE"
                    break
                except ValueError as error:
                    if str(error) != "native reactor emitted a nonfinite value":
                        raise
                    failure = "FORECAST_NUMERICAL_FAILURE"
                    break
                states.append(state)
                predictions.append(prediction)
                delivery = bridge.advance(command)
                model.commit(state, command)
                stages.append(
                    (
                        delivery.accepted_feed_kg_s,
                        delivery.accepted_jacket_k,
                        delivery.applied_feed_kg_s,
                        delivery.applied_jacket_k,
                    )
                )
                exposures.extend(delivery.exposures)
                if progress is not None and ((index + 1) % 100 == 0 or index == 2879):
                    progress(index + 1)
                if isinstance(delivery, ReactorDelivery):
                    measurement = delivery.next_measurement
                elif not isinstance(delivery, ReactorFinalDelivery) or index != 2879:
                    raise ValueError("native batch terminated at another decision")
            if failure is None:
                result = bridge.completed_result
                columns = tuple(getattr(result, name) for name in _science_GRID_COLUMNS)
                grid = tuple(
                    cast(_science_GridRow, tuple(_decimal(v) for v in row))
                    for row in zip(*columns, strict=True)
                )
                if len(exposures) != len(grid) - 1 or any(
                    e.time_s + e.duration_s != row[0]
                    or e.feed_kg_s != row[6]
                    or e.jacket_k != row[7]
                    for e, row in zip(exposures, grid[1:], strict=True)
                ):
                    raise ValueError("native batch arrays contradict observed realized delivery")
        except ReactorWorkerStopError:
            raise
        except ValueError as error:
            if str(error) != "native reactor emitted a nonfinite value":
                raise
            failure = "NATIVE_BATCH_FAILURE"
            grid = ()
        except RuntimeError as error:
            if str(error) not in {
                "native reactor failed; no completion evidence",
                "reactor delivery timed out; no completion evidence",
            }:
                raise
            if str(error) == "native reactor failed; no completion evidence":
                cause = error.__cause__
                numerical = isinstance(cause, (OverflowError, FloatingPointError)) or (
                    isinstance(cause, ValueError)
                    and (
                        str(cause) == "native reactor emitted a nonfinite value"
                        or str(cause).startswith("non-finite controller output at t=")
                    )
                )
                if not numerical:
                    # A binding/contract defect is not a failed scientific assay.
                    raise
            failure = "NATIVE_BATCH_FAILURE"
    return _science_ReactorBatchTrace(
        scenario,
        plant_dt_s,
        source.fingerprint(),
        tuple(states),
        tuple(predictions),
        tuple(stages),
        grid,
        failure,
    )
