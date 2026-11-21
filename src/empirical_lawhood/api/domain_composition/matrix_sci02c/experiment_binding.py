# SPDX-License-Identifier: MPL-2.0
"""SCI02-C readback through the ordinary experiment service."""
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import PROTOCOL_ID
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_sci02c import read_result as read
    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, None,
    read_development_result=read_development_result, specification_schema=Sci02CSpecification.SCHEMA)
