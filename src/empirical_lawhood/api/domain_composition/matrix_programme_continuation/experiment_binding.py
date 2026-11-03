# SPDX-License-Identifier: MPL-2.0
"""Metadata-only source continuation through the existing public deriver."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import CONTINUED_PROTOCOL_ID as TARGET_PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.matrix_programme_source_continuation import derive_inputs as derive
    return derive(**kwargs)




def derive_inputs_with_service(*, service, **kwargs):
    return derive_inputs(project_root=service.project_root,
        artifact_writer=service.artifact_writer, _service=service, **kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None, derive_inputs=derive_inputs,
    derive_inputs_with_service=derive_inputs_with_service, derivation_target_protocol_ids=(TARGET_PROTOCOL_ID,))
