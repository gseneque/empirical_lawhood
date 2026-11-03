# SPDX-License-Identifier: MPL-2.0
"""Cold genuine E3 preprocessing registration; no runtime or human authority."""
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from .derivation import derive_input_selection
    return derive_input_selection(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,derive_inputs=derive_inputs,
    derivation_target_protocol_ids=('matrix.response-error.configured-protected-v2',))
