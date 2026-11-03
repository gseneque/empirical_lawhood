# SPDX-License-Identifier: MPL-2.0
"""Public metadata authoring over actual original custody and compiled resources."""
from pathlib import Path
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.matrix_full_factor_custody import authenticate_original_full_factor_scope
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation


def validate_authoring_read_access(*,preparation,artifact_writer,read_access):
    from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess,require_current_e4_access
    if (type(preparation) is not ExperimentPreparation
            or type(preparation.specification_record) is not domain.ScheduledFullFactorProtectedSpecification):
        raise TypeError('full factor authoring access requires its exact protected PURE preparation')
    if read_access is not None and type(read_access) is not SelectedE4CurrentAccess:
        raise TypeError('full factor authoring access requires its operation-local current selection')
    # The request and reference are blind metadata. Do not bind the revealed
    # scope FILE until its exact original wave roster has current access.
    records=dict(preparation.design_records)
    request=records.get('request')
    if (type(request) is not domain.ScheduledFullFactorProtectedRequestV4
            or request.identity!=preparation.specification_record.request):
        raise PermissionError('full factor authoring changes its original protected request')
    reference=records.get('reference')
    if (type(reference) is not domain.ScheduledFullFactorScopeReference or not reference.protected
            or reference.scope!=preparation.specification_record.scope
            or reference.declaration!=request.declaration or reference.waves!=request.waves):
        raise PermissionError('full factor authoring changes its blind original scope or wave ancestry')
    scope_file=dict(preparation.input_files).get('external.full-factor.scope.'+reference.scope.object_fingerprint)
    if scope_file is None or scope_file.identity!=reference.scope_artifact:
        raise PermissionError('full factor authoring substitutes its original scope FILE before access')
    require_current_e4_access(writer=artifact_writer,originals=request.waves,current_access=read_access)


def prepare_authoring(preparation,*,project_root,artifact_writer,output_dir,read_access=None):
    if type(preparation) is not ExperimentPreparation or type(preparation.specification_record) not in (
            domain.ScheduledFullFactorDevelopmentSpecification,domain.ScheduledFullFactorProtectedSpecification):
        raise TypeError('full factor authoring requires exact public lifecycle preparation')
    # This hook reads originals and checks an unwritten destination only.
    # Its repeated consumers share immutable custody, with current access and
    # a final byte census before returning to the publication owner.
    with artifact_writer.read_context() as reading:
        return _prepare_authoring_read(preparation, project_root=project_root,
            artifact_writer=reading, output_dir=output_dir, read_access=read_access)


def _prepare_authoring_read(preparation,*,project_root,artifact_writer,output_dir,read_access):
    specification=preparation.specification_record
    protected=type(specification) is domain.ScheduledFullFactorProtectedSpecification
    if protected:
        validate_authoring_read_access(preparation=preparation,artifact_writer=artifact_writer,read_access=read_access)
    from empirical_lawhood.api.matrix_full_factor_access import (
        bootstrap_authoring_input_access,bootstrap_protected_authoring_input_access)
    access=(bootstrap_protected_authoring_input_access if protected else bootstrap_authoring_input_access)(
        preparation=preparation,artifact_writer=artifact_writer,read_access=read_access)
    blind=domain.bind_inputs(specification,dict(preparation.design_records)).method_inputs
    domain.validate_reference(specification,blind)
    if blind.reference.produced_input_parents!=access.parents:
        raise PermissionError('full factor authoring changes the actual original produced-parent census')
    access.require_current()
    inputs=domain.bind_inputs(specification,dict(preparation.design_records),files=dict(preparation.input_files)).method_inputs
    ordinary=domain.prepare(specification,scientific_inputs={'programme':preparation.allocation},method_inputs=inputs,execution=preparation.execution)
    if ordinary!=preparation:raise ValueError('full factor authoring changes original pure preparation or immutable inputs')
    if preparation.dependencies:
        raise ValueError('full factor authoring retains unresolved original input/context/authority prerequisites')
    from empirical_lawhood.api.matrix_full_factor_secondary import authenticate_full_factor_target
    secondary_target=authenticate_full_factor_target(writer=artifact_writer,request=inputs.request,bank=inputs.bank)
    authenticate_original_full_factor_scope(writer=artifact_writer,scope=inputs.scope,bank=inputs.bank,
        codecs=operation_catalog()[2],current_access=read_access,
        _secondary_target=secondary_target,_secondary_readout=inputs.request.secondary_readout)
    preflight_authoring_output_directory(directory=Path(output_dir),repo_root=Path(project_root),artifact_writer=artifact_writer)
    access.require_current()
    return preparation
