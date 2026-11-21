"""Decode verified array artifacts, execute domain calculations, and encode exact output bytes."""
from empirical_lawhood.domains.matrix.matrix_preparation.data import ProjectedContext
from empirical_lawhood.adapters.simulators.matrix_preparation.data import write_method_arrays
from empirical_lawhood.adapters.simulators.matrix_preparation.fitting import read_fit
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationAssessmentConfig, PreparationBenchmarkReport, PreparationDescriptionReport, PreparationFitReport, PreparationNumericalSemanticsReport

from empirical_lawhood.domains.matrix.matrix_preparation.description import prepare_assess_description_arrays

def assess_description(config: PreparationAssessmentConfig, observable: ProjectedContext, privileged: ProjectedContext, fit: PreparationFitReport, fit_payload: bytes, numerical_semantics: PreparationNumericalSemanticsReport) -> tuple[PreparationDescriptionReport, bytes, PreparationBenchmarkReport, bytes]:
    fit_arrays = read_fit(fit, fit_payload)
    prepared = prepare_assess_description_arrays(config, observable, privileged, fit, fit_arrays, numerical_semantics)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)
