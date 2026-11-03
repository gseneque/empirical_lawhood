# SPDX-License-Identifier: MPL-2.0
"""Cold public API composition; static discovery starts no authentication."""
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_experiment import (
    PROTOCOL_ID, MatrixFiniteDtSourceQualificationSpecification)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def bind_handoff(*args, **kwargs):
    from empirical_lawhood.api.matrix_finite_dt_source_experiment import bind_finite_dt_source_experiment
    return bind_finite_dt_source_experiment(*args, **kwargs)


def prepare_authoring(*args, **kwargs):
    from empirical_lawhood.api.matrix_finite_dt_source_experiment import prepare_finite_dt_source_authoring
    return prepare_finite_dt_source_authoring(*args, **kwargs)


def read_result(*args, **kwargs):
    from empirical_lawhood.api.matrix_finite_dt_source_experiment import read_finite_dt_source_result
    return read_finite_dt_source_result(*args, **kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_handoff,
    prepare_authoring=prepare_authoring, read_result=read_result,
    specification_schema=MatrixFiniteDtSourceQualificationSpecification.SCHEMA)
