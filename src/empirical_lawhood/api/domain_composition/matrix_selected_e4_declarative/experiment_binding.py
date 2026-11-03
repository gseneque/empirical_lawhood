# SPDX-License-Identifier: MPL-2.0
"""Public source derivation and existing E4 phase programme composition."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_declarative import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def derive_inputs(**kwargs):
    from empirical_lawhood.api.selected_e4_declarative import derive_inputs as compose
    return compose(**kwargs)


def programme_service_factory(*, service, descriptor=None):
    from empirical_lawhood.api.selected_e4_declarative import programme_service_factory as compose
    return compose(service=service, descriptor=descriptor)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    programme_service_factory=programme_service_factory, derive_inputs=derive_inputs)
