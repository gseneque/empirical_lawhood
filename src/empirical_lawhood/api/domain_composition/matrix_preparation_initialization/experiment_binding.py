# SPDX-License-Identifier: MPL-2.0
"""Explicit deterministic input generation; no provider or scientific authority."""
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_initialization import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_preparation_initialization import derive_inputs as derive
    return derive(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs)
