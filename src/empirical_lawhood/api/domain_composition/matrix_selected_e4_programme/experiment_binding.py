# SPDX-License-Identifier: MPL-2.0
"""Selected full E4 programme API composition; component owners retain custody."""
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import PROGRAMME_PROTOCOL_ID


def selected_e4_programme_service(*, service, descriptor=None):
    from empirical_lawhood.api.selected_e4_programme_service import selected_e4_programme_service as compose
    return compose(service=service, descriptor=descriptor)

EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROGRAMME_PROTOCOL_ID,None,
    programme_service_factory=selected_e4_programme_service)
