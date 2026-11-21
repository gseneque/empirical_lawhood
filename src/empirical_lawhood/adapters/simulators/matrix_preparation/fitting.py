"""Decode verified array artifacts, execute domain calculations, and encode exact output bytes."""
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import FIT_SCHEMA, PreparationMethodConfig
from empirical_lawhood.domains.matrix.matrix_preparation.data import Array, ProjectedContext
from empirical_lawhood.adapters.simulators.matrix_preparation.data import read_method_arrays, write_method_arrays
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationFitReport, PreparationNumericalSemanticsReport

from empirical_lawhood.domains.matrix.matrix_preparation.fitting import prepare_fit_preparation_context_arrays, validate_fit_groups

def fit_preparation_context(config: PreparationMethodConfig, observed: ProjectedContext, numerical_semantics: PreparationNumericalSemanticsReport) -> tuple[PreparationFitReport, bytes]:
    prepared = prepare_fit_preparation_context_arrays(config, observed, numerical_semantics)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)


def read_fit(report: PreparationFitReport, payload: bytes) -> dict[str, dict[str, Array]]:
    groups = read_method_arrays(payload, schema=FIT_SCHEMA, context=report.context, config=report.config, expected_sha256=report.data_sha256)
    return validate_fit_groups(report, groups)
