# SPDX-License-Identifier: MPL-2.0
"""Static custody binding; discovery performs no authentication or execution."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import PROTOCOL_ID
from empirical_lawhood.api.matrix_protected_experiment import (
    bind_protected_factorial_experiment_handoff, prepare_protected_factorial_experiment_authoring,
)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_protected_factorial_experiment_handoff,
    prepare_authoring=prepare_protected_factorial_experiment_authoring)
