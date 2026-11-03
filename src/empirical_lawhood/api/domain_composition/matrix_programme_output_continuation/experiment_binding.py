# SPDX-License-Identifier: MPL-2.0
"""Reuse the guarded continuation deriver for the explicit operational selection."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import OUTPUT_PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import CONTINUED_PROTOCOL_ID
from empirical_lawhood.api.domain_composition.matrix_programme_continuation.experiment_binding import (
    derive_inputs, derive_inputs_with_service,
)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding

EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(OUTPUT_PROTOCOL_ID, None,
    derive_inputs=derive_inputs, derive_inputs_with_service=derive_inputs_with_service,
    derivation_target_protocol_ids=(CONTINUED_PROTOCOL_ID,))
