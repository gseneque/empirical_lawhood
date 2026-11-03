# SPDX-License-Identifier: MPL-2.0
"""Metadata-only completed-TRAIN continuation through the public input deriver."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_training_continuation import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import CONTINUED_PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_retained_training_continuation import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
