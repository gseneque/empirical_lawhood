"""Decode verified array artifacts, execute domain calculations, and encode exact output bytes."""
from empirical_lawhood.domains.matrix.matrix_preparation.data import ProjectedContext
from empirical_lawhood.adapters.simulators.matrix_preparation.data import write_method_arrays
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationNumericalSemanticsConfig, PreparationNumericalSemanticsReport

from empirical_lawhood.domains.matrix.matrix_preparation.numerical_semantics import prepare_qualify_numerical_semantics_arrays

def qualify_numerical_semantics(config: PreparationNumericalSemanticsConfig, observable: ProjectedContext, privileged: ProjectedContext) -> tuple[PreparationNumericalSemanticsReport, bytes]:
    prepared = prepare_qualify_numerical_semantics_arrays(config, observable, privileged)
    payloads = tuple(write_method_arrays(*output) for output in prepared.outputs)
    return prepared.finalize(*payloads)
