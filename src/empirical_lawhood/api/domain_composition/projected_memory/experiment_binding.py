# SPDX-License-Identifier: MPL-2.0
from empirical_lawhood.api.path_ensembles import read_result
from empirical_lawhood.domains.matrix.projected_memory.extension import Specification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding

EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(
    Specification.FAMILY + ".numerical",
    None,
    read_development_result=read_result,
    specification_schema=Specification.SCHEMA,
)
