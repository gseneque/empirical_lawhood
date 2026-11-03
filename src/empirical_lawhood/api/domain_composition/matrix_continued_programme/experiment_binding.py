# SPDX-License-Identifier: MPL-2.0
"""One Matrix runner; completed original E1/E2 remain read-only predecessors."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import CONTINUED_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def programme_service_factory(*, service, descriptor=None):
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    return MatrixResearchProgrammeService(service=service, descriptor=descriptor)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(CONTINUED_PROTOCOL_ID, None,
    programme_service_factory=programme_service_factory)
