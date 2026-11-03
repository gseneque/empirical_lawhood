# SPDX-License-Identifier: MPL-2.0
"""Public E1 metadata derivation; ordinary compact E1 owns execution."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_assembly import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_preparation import PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_e1 import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
