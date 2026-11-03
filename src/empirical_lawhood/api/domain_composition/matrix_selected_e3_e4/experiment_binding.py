# SPDX-License-Identifier: MPL-2.0
"""Select genuine authored DEV custody for the additive E3/E4 public route."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import PROTOCOL_ID, SelectedE3E4ExperimentSpecification
from empirical_lawhood.api.matrix_selected_e3_e4_runtime import bind_selected_e3_e4_development_runtime
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
from empirical_lawhood.api.selected_e3_access import (
    bootstrap_authoring_input_access, bootstrap_development_input_access,
    bootstrap_selected_input_access, select_current_e3_access, validate_development_read_access,
)


def derive_inputs(**context):
    from empirical_lawhood.api.matrix_full_factor_secondary import derive_development_inputs
    return derive_development_inputs(**context)


def complete_development_result(**context):
    from empirical_lawhood.api.selected_e4_structure import complete_development_result as complete
    return complete(**context)


def read_development_result(**context):
    from empirical_lawhood.api.selected_e4_structure import read_development_result as read
    return read(**context)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_handoff=None,
    bind_development_runtime=bind_selected_e3_e4_development_runtime, derive_inputs=derive_inputs,
    specification_schema=SelectedE3E4ExperimentSpecification.SCHEMA,
    complete_development_result=complete_development_result,
    read_development_result=read_development_result,
    validate_development_read_access=validate_development_read_access,
    development_bootstrap_record_types=(SelectedE3E4Evidence,),
    bootstrap_development_input_access=bootstrap_development_input_access,
    bootstrap_authoring_input_access=bootstrap_authoring_input_access,
    bootstrap_selected_input_access=bootstrap_selected_input_access,
    read_access_record_types=(MatrixSelectedOriginalProduct,),
    select_read_access=select_current_e3_access)
