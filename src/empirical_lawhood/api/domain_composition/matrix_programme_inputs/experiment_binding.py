# SPDX-License-Identifier: MPL-2.0
"""Public metadata-only programme allocation compiler."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_assembly import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_input_assembly import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs)
