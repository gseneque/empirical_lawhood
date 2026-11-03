# SPDX-License-Identifier: MPL-2.0
"""Cold metadata recipe for actual retained E3 products."""
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import CONTINUED_PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_experiment import PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from ..matrix_finite_dt_source_assembly.derivation import derive_input_selection
    return derive_input_selection(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(CONTINUED_PROTOCOL_ID, None, derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
