# SPDX-License-Identifier: MPL-2.0
"""Bind original retained products to their scientific reader."""
from empirical_lawhood.domains.matrix.model_free.records import PROTOCOL_ID, Specification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.api.model_free_matrix import read_result

EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_result, specification_schema=Specification.SCHEMA)
