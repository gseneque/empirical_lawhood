# SPDX-License-Identifier: MPL-2.0
"""Selected E4 actual issued-component API composition."""
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import COMPONENT_PROTOCOL_ID,SelectedE4NativeComponentSpecification


def bind_selected_e4_component(*args, **kwargs):
    from empirical_lawhood.api.selected_e4_native_preparation import bind_selected_e4_component as bind
    return bind(*args, **kwargs)


def prepare_selected_e4_authoring(*args, **kwargs):
    from empirical_lawhood.api.selected_e4_native_preparation import prepare_selected_e4_authoring as prepare
    return prepare(*args, **kwargs)


def read_selected_e4_component(*args, **kwargs):
    from empirical_lawhood.api.selected_e4_native_preparation import read_selected_e4_component as read
    return read(*args, **kwargs)


def authenticate_selected_e4_component_instance(*args, **kwargs):
    from empirical_lawhood.api.selected_e4_native_preparation import authenticate_selected_e4_component_instance as authenticate
    return authenticate(*args, **kwargs)

EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(COMPONENT_PROTOCOL_ID,bind_selected_e4_component,
    prepare_authoring=prepare_selected_e4_authoring,read_result=read_selected_e4_component,
    specification_schema=SelectedE4NativeComponentSpecification.SCHEMA,
    authenticate_instance=authenticate_selected_e4_component_instance)
