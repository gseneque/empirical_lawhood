# SPDX-License-Identifier: MPL-2.0
"""Cold native TRAIN postprocessing registration; ordinary DEV runtime retained."""
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionSpecification
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def export_products(**kwargs):
    from empirical_lawhood.api.native_training_banks import export_selected_native_training_banks
    return export_selected_native_training_banks(**kwargs)


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_native_training_read import read_development_result as read
    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    export_products=export_products, read_development_result=read_development_result,
    specification_schema=NativeTrainingAcquisitionSpecification.SCHEMA)
