# SPDX-License-Identifier: MPL-2.0
"""Static DEV full-history follow-up composition over ordinary public services."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import DEV_PROTOCOL_ID,ScheduledFullFactorDevelopmentSpecification,ScheduledFullFactorDevelopmentRequestV3
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.api.selected_e3_access import select_current_e3_access
from empirical_lawhood.api.matrix_full_factor_access import (bootstrap_selected_input_access,
    bootstrap_development_input_access,bootstrap_authoring_input_access,validate_development_read_access)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_full_factor_derivation import derive_input_selection
    return derive_input_selection(**kwargs)


def prepare_authoring(*args,**kwargs):
    from empirical_lawhood.api.matrix_full_factor_authoring import prepare_authoring as prepare
    return prepare(*args,**kwargs)


def bind_development_runtime(**kwargs):
    from empirical_lawhood.api.matrix_full_factor_runtime import bind_development_runtime as bind
    return bind(**kwargs)


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_full_factor_read import read_development_result as read
    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(DEV_PROTOCOL_ID,None,
    prepare_authoring=prepare_authoring,bind_development_runtime=bind_development_runtime,
    derive_inputs=derive_inputs,derivation_target_protocol_ids=(DEV_PROTOCOL_ID,),
    read_development_result=read_development_result,specification_schema=ScheduledFullFactorDevelopmentSpecification.SCHEMA,
    validate_development_read_access=validate_development_read_access,
    development_bootstrap_record_types=(ScheduledFullFactorDevelopmentRequestV3,SelectedE3E4Evidence),
    bootstrap_selected_input_access=bootstrap_selected_input_access,
    bootstrap_development_input_access=bootstrap_development_input_access,
    bootstrap_authoring_input_access=bootstrap_authoring_input_access,
    read_access_record_types=(MatrixSelectedOriginalProduct,),select_read_access=select_current_e3_access)
