# SPDX-License-Identifier: MPL-2.0
"""The selected prospective science amendment uses the ordinary public deriver."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.curve_amendment import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import AMENDED_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_curve_amendment import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(AMENDED_PROTOCOL_ID,))
