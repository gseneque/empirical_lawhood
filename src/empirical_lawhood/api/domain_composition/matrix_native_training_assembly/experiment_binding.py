# SPDX-License-Identifier: MPL-2.0
"""Cold preprocessing registration; ordinary target lifecycle retains all guards."""
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from .derivation import derive_input_selection
    return derive_input_selection(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
