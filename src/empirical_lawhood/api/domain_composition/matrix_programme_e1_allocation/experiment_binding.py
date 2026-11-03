# SPDX-License-Identifier: MPL-2.0
"""Public allocation and exact criterion derivation; no native execution."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_allocation import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_e1_allocation import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs)
