# SPDX-License-Identifier: MPL-2.0
"""Retained reads selected through the starter's exact specification revision."""

from empirical_lawhood.adapters.isolated_native_starter.records import PROTOCOL_ID, SquareSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.isolated_native_starter import read_result
    return read_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=SquareSpecification.SCHEMA)
