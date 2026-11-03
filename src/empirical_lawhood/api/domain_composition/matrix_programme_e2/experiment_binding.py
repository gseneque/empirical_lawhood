# SPDX-License-Identifier: MPL-2.0
"""Public E2 metadata derivation; ordinary native utility owns execution."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.e2_assembly import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_acquisition import PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_e2 import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
