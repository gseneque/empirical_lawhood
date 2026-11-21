# SPDX-License-Identifier: MPL-2.0
"""Retained revision selection uses the exact original specification owner."""

from empirical_lawhood.methods.mass_balance_revision.records import PROTOCOL_ID, ForecastUpgradeSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.mass_forecast_revision import read_result
    return read_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=ForecastUpgradeSpecification.SCHEMA)
