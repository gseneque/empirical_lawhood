# SPDX-License-Identifier: MPL-2.0
"""Resolve the finite Matrix selector through the existing programme service."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def programme_service_factory(*, service, descriptor=None):
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
    return MatrixResearchProgrammeService(service=service, descriptor=descriptor)


def derive_inputs(**kwargs):
    """A composed transition needs the explicitly selected programme service context."""
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    service = ExperimentProgrammeService(kwargs.pop("project_root"), kwargs.pop("artifact_writer"))
    return programme_service_factory(service=service).derive_inputs(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    programme_service_factory=programme_service_factory, derive_inputs=derive_inputs,
    derivation_target_protocol_ids=(PROTOCOL_ID,))
