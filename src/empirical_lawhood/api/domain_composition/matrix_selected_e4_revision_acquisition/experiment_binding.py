# SPDX-License-Identifier: MPL-2.0
"""Registered acquisition-to-revision composition, without component authority."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_transition import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def programme_service_factory(*, service, descriptor=None):
    from empirical_lawhood.api.selected_e4_revision_programme import programme_service_factory as compose
    return compose(service=service, descriptor=descriptor)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_handoff=None,
    programme_service_factory=programme_service_factory)
