# SPDX-License-Identifier: MPL-2.0
"""Cold public E3 composition; discovery performs no custody reads or work."""

from empirical_lawhood.api.domain_composition.matrix_protected_response.runtime import (
    bind_protected_e3_experiment_handoff, prepare_protected_e3_experiment_authoring,
)
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.api.domain_composition.matrix_protected_response.scientific_read import read_protected_e3_result
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification


def derive_prospective_design_inputs(preparation):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import derive_protected_e3_design_inputs
    return derive_protected_e3_design_inputs(preparation)


def bind_exposed_development(*, specification, supplier, **_context):
    """Keep the saved-bank software route separate from protected E3 entry."""
    if (type(specification) is not MatrixResponseErrorSpecification
            or specification.evidence_scope != 'EXPOSED_CONFORMANCE'):
        raise PermissionError('prospective E3 inputs cannot enter the development lifecycle')
    specification.__post_init__()
    return supplier


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding("matrix.response-error.origin-only",
    bind_protected_e3_experiment_handoff, prepare_authoring=prepare_protected_e3_experiment_authoring,
    bind_development_runtime=bind_exposed_development,
    derive_prospective_design_inputs=derive_prospective_design_inputs,
    read_result=read_protected_e3_result, specification_schema=MatrixResponseErrorSpecification.SCHEMA)
