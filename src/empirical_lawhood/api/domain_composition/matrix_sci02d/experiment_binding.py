# SPDX-License-Identifier: MPL-2.0
"""SCI02-D independent readback through the shared experiment service."""
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import PROTOCOL_ID
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.experiment import BridgeSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_sci02d import read_result
    return read_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=BridgeSpecification.SCHEMA)
