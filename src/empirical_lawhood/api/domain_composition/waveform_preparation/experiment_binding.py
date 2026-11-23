# SPDX-License-Identifier: MPL-2.0
from empirical_lawhood.domains.matrix.waveform_preparation.records import (
    PROTOCOL_ID,
    WaveformSpecification,
)
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_development_result(**kwargs):
    from empirical_lawhood.api.waveform_preparation import read_result

    return read_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(
    PROTOCOL_ID,
    None,
    read_development_result=read_development_result,
    specification_schema=WaveformSpecification.SCHEMA,
)
