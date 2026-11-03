# SPDX-License-Identifier: MPL-2.0
"""Cold source preprocessing registration; not scientific issue authority."""
from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import PROTOCOL_ID, MatrixPreparedSourceAssemblyRequest, DEVELOPMENT_TYPES
from empirical_lawhood.adapters.methods.matrix_prepared_source_experiment import PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.api.prepared_source_access import bootstrap_assembly_selected_input_access
from empirical_lawhood.api.selected_prepared_access import select_current_prepared_access


def derive_inputs(**kwargs):
    from .derivation import derive_input_selection
    return derive_input_selection(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,),
    development_bootstrap_record_types=(MatrixPreparedSourceAssemblyRequest, *DEVELOPMENT_TYPES),
    bootstrap_selected_input_access=bootstrap_assembly_selected_input_access,
    read_access_record_types=(MatrixSelectedOriginalProduct,),
    select_read_access=select_current_prepared_access)
