# SPDX-License-Identifier: MPL-2.0
"""Read original matrix-series findings through the shared custody owner."""
from empirical_lawhood.domains.matrix.classical_series.records import PROTOCOL_ID, SeriesSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.classical_matrix_series import read_result
    return read_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=SeriesSpecification.SCHEMA)
