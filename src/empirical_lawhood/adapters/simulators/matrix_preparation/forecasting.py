"""Decode verified array artifacts, execute domain calculations, and encode exact output bytes."""
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PreparationMethodConfig
from empirical_lawhood.domains.matrix.matrix_preparation.data import Array, FORECAST_SCHEMA, ProjectedContext
from empirical_lawhood.adapters.simulators.matrix_preparation.data import read_method_arrays, write_method_arrays
from empirical_lawhood.adapters.simulators.matrix_preparation.fitting import read_fit
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationDescriptionReport, PreparationFitReport, PreparationForecastReport

from empirical_lawhood.domains.matrix.matrix_preparation.forecasting import prepare_forecast_preparation_context_arrays, validate_forecasts_groups

def forecast_preparation_context(config: PreparationMethodConfig, observed: ProjectedContext, fit: PreparationFitReport, fit_payload: bytes, description: PreparationDescriptionReport) -> tuple[PreparationForecastReport, bytes]:
    fit_arrays = read_fit(fit, fit_payload)
    prepared = prepare_forecast_preparation_context_arrays(config, observed, fit, fit_arrays, description)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)


def read_forecasts(report: PreparationForecastReport, payload: bytes) -> dict[str, dict[str, Array]]:
    groups = read_method_arrays(payload, schema=FORECAST_SCHEMA, context=report.context, config=report.config, expected_sha256=report.data_sha256)
    return validate_forecasts_groups(report, groups)
