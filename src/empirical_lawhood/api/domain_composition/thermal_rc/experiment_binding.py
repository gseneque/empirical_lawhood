# SPDX-License-Identifier: MPL-2.0
from empirical_lawhood.domains.circuits.thermal_rc.extension import Specification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding


def read_result(**kwargs):
    from empirical_lawhood.api.path_ensembles import read_result as read

    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(
    Specification.FAMILY + ".numerical",
    None,
    read_development_result=read_result,
    specification_schema=Specification.SCHEMA,
)
