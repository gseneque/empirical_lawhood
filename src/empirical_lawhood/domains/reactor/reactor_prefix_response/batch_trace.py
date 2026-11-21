"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorAssignedScenario
from empirical_lawhood.domains.reactor.reactor_prefix_response.forecast_contracts import ReactorForecastState, ReactorPointForecast

GRID_COLUMNS = (
    "time_s",
    "t_reactor_k",
    "t_jacket_k",
    "dosed_kg",
    "conversion_b",
    "n_a_mol",
    "feed_applied_kg_s",
    "tj_cmd_applied_k",
)

MAXIMUM_BATCH_BYTES = 96 * 1024**2

GridRow = tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]

StageRow = tuple[Decimal, Decimal, Decimal, Decimal]

@dataclass(frozen=True, slots=True)
class ReactorBatchTrace(CanonicalRecord):
    """Completed or explicitly invalid assigned episode; nested rows are not n."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-prefix-response/reactor-batch-trace'
    scenario: ReactorAssignedScenario
    plant_dt_s: Decimal
    source_sha256: str
    states: tuple[ReactorForecastState, ...]
    forecasts: tuple[ReactorPointForecast, ...]
    observed_stages: tuple[StageRow, ...]
    native_grid: tuple[GridRow, ...]
    failure_code: str | None

    def __post_init__(self) -> None:
        from empirical_lawhood.science.records.serialization import validate_sha256

        validate_sha256(self.source_sha256, field_name="source_sha256")
        if self.plant_dt_s not in (Decimal(1), Decimal(".5")):
            raise ValueError("batch trace uses an undeclared numerical view")
        if not 0 <= len(self.observed_stages) <= len(self.forecasts) == len(self.states) <= 2880:
            raise ValueError("batch trace changes the ordered forecast/delivery census")
        if self.failure_code is None:
            if (
                len(self.states) != 2880
                or len(self.observed_stages) != 2880
                or len(self.native_grid) != int(Decimal(28800) / self.plant_dt_s) + 1
            ):
                raise ValueError("complete batch trace requires the full native horizon")
        elif (
            self.failure_code not in {"NATIVE_BATCH_FAILURE", "FORECAST_NUMERICAL_FAILURE"}
            or self.native_grid
        ):
            raise ValueError(
                "invalid batch must retain its explicit failure and no fabricated grid"
            )
        for index, (state, prediction) in enumerate(zip(self.states, self.forecasts, strict=True)):
            if (
                state.measurement.time_s != 10 * index
                or prediction.state_sha256 != state.fingerprint()
                or prediction.command.time_s != 10 * index
                or prediction.command.feed_kg_s != state.reference_feed_kg_s
                or prediction.command.jacket_k != state.reference_jacket_k
                or prediction.plant_dt_s != self.plant_dt_s
            ):
                raise ValueError(
                    "batch forecast changes causal state, clock, reference policy or view"
                )
        for stage_row in self.observed_stages:
            if len(stage_row) != 4:
                raise ValueError("batch action stages have another column count")
            for value in stage_row:
                validate_decimal(value, field_name="native-stage", minimum=Decimal(0))
        for index, row in enumerate(self.native_grid):
            if len(row) != len(GRID_COLUMNS) or row[0] != index * self.plant_dt_s:
                raise ValueError("native batch grid changes its columns or clock")
            for value in row:
                validate_decimal(value, field_name="native-grid", minimum=Decimal(0))
