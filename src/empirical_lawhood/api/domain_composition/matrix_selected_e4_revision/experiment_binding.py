# SPDX-License-Identifier: MPL-2.0
"""Bind actual native-acquired DEV evidence before selected E4 model fitting."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_preparation import PROTOCOL_ID
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def bind_selected_e4_development_runtime(*, supplier, writer, directory, plan, output_codecs):
    from empirical_lawhood.api.selected_e4_method_runtime import bind_selected_e4_development_runtime as bind
    return bind(supplier=supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind_handoff=None,
    bind_development_runtime=bind_selected_e4_development_runtime)
