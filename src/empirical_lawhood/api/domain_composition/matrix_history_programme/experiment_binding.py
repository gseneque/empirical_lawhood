# SPDX-License-Identifier: MPL-2.0
"""Cold E2 dedicated-service facade registration."""
from empirical_lawhood.adapters.methods.matrix_history_analysis.experiment_preparation import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def programme_service_factory(**kwargs):
    from empirical_lawhood.api.matrix_history_programme import MatrixHistoryProgrammeService
    return MatrixHistoryProgrammeService(**kwargs)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,programme_service_factory=programme_service_factory)
