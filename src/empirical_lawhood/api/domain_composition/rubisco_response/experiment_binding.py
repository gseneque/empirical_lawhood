# SPDX-License-Identifier: MPL-2.0
"""Select the separate initial-root reader by its exact protocol revision."""

from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_experiment import PROTOCOL_ID, InitialRootExperimentSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.api.domain_composition.rubisco_response.initial_root_experiment import read_development_result

EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=InitialRootExperimentSpecification.SCHEMA)
