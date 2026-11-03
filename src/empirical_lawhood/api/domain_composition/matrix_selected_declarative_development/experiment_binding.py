# SPDX-License-Identifier: MPL-2.0
"""Lazy actual development custody for declarative selected preparation."""
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedDevelopmentSpecification
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_declarative_preparation import DEVELOPMENT_PROTOCOL_ID


def derive_inputs(**kwargs):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import derive_inputs as derive
    return derive(**kwargs)


def bind_development(*, supplier, writer, directory, plan, output_codecs, payloads=None, read_access=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as opportunity
    keys = {value.capability.capability_key for value in plan.tasks}
    if keys and all(value.startswith(revision.NAMESPACE + ".development.") for value in keys):
        from empirical_lawhood.api.matrix_selected_revision_runtime import bind_revision_development
        return bind_revision_development(supplier=supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs,payloads=payloads,read_access=read_access)
    if keys and keys <= {value.capability_key for value in opportunity.operation_declarations()}:
        from empirical_lawhood.api.matrix_selected_opportunity_runtime import bind_selected_opportunity_runtime
        return bind_selected_opportunity_runtime(supplier=supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs,payloads=payloads,read_access=read_access)
    raise PermissionError("declarative selected development changes its closed installed original producer family")


def read_development_result(**kwargs):
    from empirical_lawhood.api.matrix_selected_development_scientific_read import read_development_result as read
    return read(**kwargs)


EXPERIMENT_RUNTIME_BINDING = ExperimentRuntimeBinding(DEVELOPMENT_PROTOCOL_ID, None,
    bind_development_runtime=bind_development, derive_inputs=derive_inputs,read_development_result=read_development_result,
    specification_schema=SelectedPreparedDevelopmentSpecification.SCHEMA)


# Exact existing locator classes only. Requests/selections contain fitted bodies.
from dataclasses import replace
from empirical_lawhood.api import selected_prepared_access as original_access
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_declarative_preparation import locator_record_types

EXPERIMENT_RUNTIME_BINDING=replace(EXPERIMENT_RUNTIME_BINDING,
    development_bootstrap_record_types=locator_record_types(),
    bootstrap_selected_input_access=original_access.bootstrap_selected_input_access,
    bootstrap_development_input_access=original_access.bootstrap_development_input_access,
    bootstrap_authoring_input_access=original_access.bootstrap_authoring_input_access,
    read_access_record_types=(original_access.MatrixSelectedOriginalProduct,),
    select_read_access=original_access.select_current_prepared_access,
    validate_development_read_access=(original_access.validate_development_read_access
        if EXPERIMENT_RUNTIME_BINDING.read_development_result is not None else None))
