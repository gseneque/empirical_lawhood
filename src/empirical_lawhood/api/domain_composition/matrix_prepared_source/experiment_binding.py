# SPDX-License-Identifier: MPL-2.0
"""Cold public API composition; static discovery starts no authentication."""
from empirical_lawhood.adapters.methods.matrix_prepared_source_experiment import (
    PROTOCOL_ID, MatrixPreparedSourceQualificationSpecification)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_prepared_source_experiment import locator_record_types
from empirical_lawhood.api.prepared_source_access import (
    bootstrap_selected_input_access, bootstrap_authoring_input_access,
    bootstrap_prospective_input_access,
)
from empirical_lawhood.api.selected_prepared_access import select_current_prepared_access


def bind_handoff(*args, **kwargs):
    from empirical_lawhood.api.matrix_prepared_source_experiment import bind_prepared_source_experiment
    return bind_prepared_source_experiment(*args, **kwargs)


def prepare_authoring(*args, **kwargs):
    from empirical_lawhood.api.matrix_prepared_source_experiment import prepare_prepared_source_authoring
    return prepare_prepared_source_authoring(*args, **kwargs)


def read_result(*args, **kwargs):
    from empirical_lawhood.api.matrix_prepared_source_experiment import read_prepared_source_result
    return read_prepared_source_result(*args, **kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_handoff,
    prepare_authoring=prepare_authoring, read_result=read_result,
    specification_schema=MatrixPreparedSourceQualificationSpecification.SCHEMA,
    bootstrap_selected_input_access=bootstrap_selected_input_access,
    bootstrap_authoring_input_access=bootstrap_authoring_input_access,
    prospective_bootstrap_record_types=locator_record_types(),
    bootstrap_prospective_input_access=bootstrap_prospective_input_access,
    read_access_record_types=(MatrixSelectedOriginalProduct,),
    select_read_access=select_current_prepared_access)
