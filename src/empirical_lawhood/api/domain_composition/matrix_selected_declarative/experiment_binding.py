# SPDX-License-Identifier: MPL-2.0
"""Lazy registered public selected-preparation composition."""
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_declarative_preparation import PROTECTED_PROTOCOL_ID
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedProtectedSpecification


def derive_inputs(**kwargs):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import derive_inputs as derive
    return derive(**kwargs)


def prepare_authoring(*args, **kwargs):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import prepare_authoring as prepare
    return prepare(*args, **kwargs)


def bind(handoff, *, specification, allocation, source_records, artifact_writer, reveal_authority_id=None,original_input_access=None,read_access=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
    domain.validate_instance(specification=specification, allocation=allocation,
        draft=handoff.compilation.draft, source_records=source_records)
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import validate_current_metadata
    selected, = (value for _, value in source_records if type(value) in domain.derived_selection_types())
    validate_current_metadata(specification, selected)
    if specification.account == "REVISION":
        from empirical_lawhood.api.matrix_selected_revision_runtime import bind_revision_handoff
        from empirical_lawhood.api.recursive_operations import operation_catalog
        return bind_revision_handoff(handoff, writer=artifact_writer, output_codecs=operation_catalog()[2],
            reveal_authority_id=reveal_authority_id,original_input_access=original_input_access,read_access=read_access)
    from empirical_lawhood.api.matrix_selected_runtime import bind_selected_matrix_handoff
    return bind_selected_matrix_handoff(handoff, writer=artifact_writer, reveal_authority_id=reveal_authority_id,original_input_access=original_input_access,read_access=read_access)


def read_result(**kwargs):
    from empirical_lawhood.api.matrix_selected_scientific_read import read_selected_protected_result
    return read_selected_protected_result(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(PROTECTED_PROTOCOL_ID, bind,
    prepare_authoring=prepare_authoring, derive_inputs=derive_inputs,
    read_result=read_result, specification_schema=SelectedPreparedProtectedSpecification.SCHEMA)


# Exact existing locator classes only. Requests/selections contain fitted bodies.
from dataclasses import replace
from empirical_lawhood.api import selected_prepared_access as original_access
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_declarative_preparation import locator_record_types

EXPERIMENT_RUNTIME_BINDING=replace(EXPERIMENT_RUNTIME_BINDING,
    prospective_bootstrap_record_types=locator_record_types(),
    bootstrap_selected_input_access=original_access.bootstrap_selected_input_access,
    bootstrap_prospective_input_access=original_access.bootstrap_prospective_input_access,
    bootstrap_authoring_input_access=original_access.bootstrap_authoring_input_access,
    read_access_record_types=(original_access.MatrixSelectedOriginalProduct,),
    select_read_access=original_access.select_current_prepared_access,
    validate_development_read_access=(original_access.validate_development_read_access
        if EXPERIMENT_RUNTIME_BINDING.read_development_result is not None else None))
