# SPDX-License-Identifier: MPL-2.0
"""Lazy retained native E2 consumer; ordinary DEV author/run/recovery owners."""
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_acquisition import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_records import NativeUtilitySpecification
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_native_utility_read import read_development_result as read
    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=NativeUtilitySpecification.SCHEMA)
