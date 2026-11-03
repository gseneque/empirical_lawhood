# SPDX-License-Identifier: MPL-2.0
"""Cold configured E3 registration; heavy custody owners load only on use."""
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding

PROTOCOL_ID = "matrix.response-error.configured-protected-v2"


def bind(handoff, *, specification, allocation, source_records, artifact_writer, reveal_authority_id=None):
    from .runtime import bind_configured_protected_e3_experiment_handoff
    return bind_configured_protected_e3_experiment_handoff(handoff, specification=specification,
        allocation=allocation, source_records=source_records, artifact_writer=artifact_writer,
        reveal_authority_id=reveal_authority_id)


def prepare_authoring(preparation, *, project_root, artifact_writer, output_dir):
    from .runtime import prepare_protected_e3_experiment_authoring
    return prepare_protected_e3_experiment_authoring(preparation, project_root=project_root,
        artifact_writer=artifact_writer, output_dir=output_dir)


def read_result(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False, assess_incomplete=False):
    from .scientific_read import read_protected_e3_result
    return read_protected_e3_result(selected=selected, artifact_writer=artifact_writer, run_id=run_id,
        reveal_authority_id=reveal_authority_id, allow_partial=allow_partial, assess_incomplete=assess_incomplete)


def derive_inputs(**kwargs):
    from .derivation import derive_input_selection
    return derive_input_selection(**kwargs)


def export_products(**kwargs):
    from .product_export import export_configured_protected_e3_products
    return export_configured_protected_e3_products(**kwargs)


def derive_prospective_design_inputs(preparation):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import derive_protected_e3_design_inputs
    return derive_protected_e3_design_inputs(preparation)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTOCOL_ID, bind,
    prepare_authoring=prepare_authoring,
    derive_prospective_design_inputs=derive_prospective_design_inputs, read_result=read_result,
    specification_schema=ConfiguredProtectedE3Specification.SCHEMA, derive_inputs=derive_inputs,
    export_products=export_products, supports_incomplete_assessment=True)
