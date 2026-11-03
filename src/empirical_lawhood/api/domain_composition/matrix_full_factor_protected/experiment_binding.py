# SPDX-License-Identifier: MPL-2.0
"""PURE exposed analysis; actual protected original grants remain mandatory."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import PROTECTED_PROTOCOL_ID,ScheduledFullFactorProtectedSpecification,ScheduledFullFactorProtectedRequestV4
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4WaveLocator
from empirical_lawhood.api.selected_e4_access import select_current_e4_access
from empirical_lawhood.api.matrix_full_factor_access import (bootstrap_protected_selected_input_access,
    bootstrap_protected_development_input_access,bootstrap_protected_authoring_input_access)
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


def validate_development_read_access(**kwargs):
    from empirical_lawhood.api.matrix_full_factor_runtime import validate_development_read_access as validate
    return validate(**kwargs)


def validate_authoring_read_access(**kwargs):
    from empirical_lawhood.api.matrix_full_factor_authoring import validate_authoring_read_access as validate
    return validate(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTECTED_PROTOCOL_ID,None,
    prepare_authoring=prepare_authoring,derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(PROTECTED_PROTOCOL_ID,),
    bind_development_runtime=bind_development_runtime,read_development_result=read_development_result,
    specification_schema=ScheduledFullFactorProtectedSpecification.SCHEMA,
    validate_development_read_access=validate_development_read_access,
    validate_authoring_read_access=validate_authoring_read_access,
    development_bootstrap_record_types=(ScheduledFullFactorProtectedRequestV4,),
    bootstrap_selected_input_access=bootstrap_protected_selected_input_access,
    bootstrap_development_input_access=bootstrap_protected_development_input_access,
    bootstrap_authoring_input_access=bootstrap_protected_authoring_input_access,
    read_access_record_types=(SelectedE4WaveLocator,),select_read_access=select_current_e4_access)
