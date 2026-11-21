"""Decode verified array artifacts, execute domain calculations, and encode exact output bytes."""
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PreparationMethodConfig
from empirical_lawhood.domains.matrix.matrix_preparation.data import Array, DECISION_SCHEMA, ProjectedContext
from empirical_lawhood.adapters.simulators.matrix_preparation.data import read_method_arrays, write_method_arrays
from empirical_lawhood.adapters.simulators.matrix_preparation.fitting import read_fit
from empirical_lawhood.adapters.simulators.matrix_preparation.forecasting import read_forecasts
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationDecisionReport, PreparationDescriptionReport, PreparationFitReport, PreparationForecastReport, PreparationTaskAssessmentReport

from empirical_lawhood.domains.matrix.matrix_preparation.task_assessment import prepare_lock_development_decisions_arrays, validate_decisions_groups, prepare_assess_development_tasks_arrays

def lock_development_decisions(config: PreparationMethodConfig, fit: PreparationFitReport, fit_payload: bytes, description: PreparationDescriptionReport, forecast: PreparationForecastReport, forecast_payload: bytes) -> tuple[PreparationDecisionReport, bytes]:
    fit_arrays = read_fit(fit, fit_payload)
    forecast_arrays = read_forecasts(forecast, forecast_payload)
    prepared = prepare_lock_development_decisions_arrays(config, fit, fit_arrays, description, forecast, forecast_arrays)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)


def read_decisions(report: PreparationDecisionReport, payload: bytes) -> dict[str, dict[str, Array]]:
    groups = read_method_arrays(payload, schema=DECISION_SCHEMA, context=report.context, config=report.config, expected_sha256=report.data_sha256)
    return validate_decisions_groups(report, groups)


def assess_development_tasks(config: PreparationMethodConfig, observed: ProjectedContext, task: ProjectedContext, fit: PreparationFitReport, fit_payload: bytes, description: PreparationDescriptionReport, forecast: PreparationForecastReport, forecast_payload: bytes, decision: PreparationDecisionReport, decision_payload: bytes) -> tuple[PreparationTaskAssessmentReport, bytes]:
    fit_arrays = read_fit(fit, fit_payload)
    forecast_arrays = read_forecasts(forecast, forecast_payload)
    decision_arrays = read_decisions(decision, decision_payload)
    prepared = prepare_assess_development_tasks_arrays(config, observed, task, fit, fit_arrays, description, forecast, forecast_arrays, decision, decision_arrays)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)
