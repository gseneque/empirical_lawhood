# SPDX-License-Identifier: MPL-2.0
"""Actual source/resource authoring composition for selected protected E4."""
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as domain
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from .prospective_experiment import preview_prepared_prospective_experiment_candidate
from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
from empirical_lawhood.runtime.experiment_resources import bind_execution_resources


def _component_selection(source_records):
    if (len(source_records)!=1
            or type(source_records[0][1]) is not domain.SelectedE4NativeComponentInputs):
        raise ValueError("selected E4 requires one current published-plan component reference")
    selection=source_records[0][1]
    if source_records[0][0]!=selection.record_id:
        raise ValueError("selected E4 component reference changes its original source key")
    selection.__post_init__()
    return selection


def require_selected_e4_original_access(writer,upstream_products,calibration_product,*,produced_input_parents):
    """Check current original permissions using bounded locator metadata only."""
    from .selected_prepared_access import selected_e4_original_input_access
    actual=selected_e4_original_input_access(artifact_writer=writer,upstream_products=upstream_products,
        calibration_product=calibration_product).parents
    if not set(actual)<=set(produced_input_parents):
        raise PermissionError("selected E4 plan substitutes its actual original producer access or lineage")


def require_selected_e4_plan_access(writer,plan):
    """Refresh actual original and DEV custody; never retain permission."""
    from .selected_prepared_access import selected_e4_original_input_access
    evidence=plan.evidence
    actual=selected_e4_original_input_access(artifact_writer=writer,upstream_products=evidence.upstream_products,
        calibration_product=evidence.calibration_product,
        development=(evidence.development_nomination,evidence.development_freeze)).parents
    if actual!=evidence.produced_input_parents or actual!=plan.declaration.produced_input_parents:
        raise PermissionError("selected E4 plan changes its complete actual produced-input parent census")


def resolve_published_component_inputs(writer,selection,*,specification):
    """Resolve the actual shared publication inside the caller's read lifetime."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    selection.__post_init__()
    require_selected_e4_original_access(writer,selection.upstream_products,selection.calibration_product,
        produced_input_parents=selection.plan_publication.logical.lineage_parents)
    authenticate_publication(writer,selection.plan_publication)
    publication=selection.plan_publication
    path=writer.root.resolve(publication.materialization.relative_path,for_write=False)
    raw=read_bounded_bytes(path,maximum_bytes=publication.materialization.size_bytes)
    plan=decode_canonical_bytes(raw,domain.SelectedE4ProtectedProgrammePlan,
        maximum_bytes=publication.materialization.size_bytes)
    if raw!=plan.canonical_bytes():
        raise ValueError("selected E4 shared programme changes exact canonical bytes")
    resolved=domain.resolve_component_inputs(selection,plan)
    require_selected_e4_plan_access(writer,plan)
    if (selection.component_id!=specification.component_id
            or domain.component_specification(plan,selection.component_id)!=specification):
        raise ValueError("selected E4 shared plan changes its exact component specification")
    authenticate_publication(writer,selection.declaration_publication,plan.declaration)
    plan.secondary_readout.validate_target(plan.structure.secondary_target)
    authenticate_publication(writer,plan.secondary_readout.publication,plan.structure.secondary_target)
    require_selected_e4_plan_access(writer,plan)
    return resolved


def authenticate_selected_e4_component_instance(*,specification,allocation,draft,source_records,artifact_writer):
    """Retain full scientific rederivation at the actual publication boundary."""
    selection=_component_selection(source_records)
    with artifact_writer.read_context() as writer:
        resolved=resolve_published_component_inputs(writer,selection,specification=specification)
        domain.validate_component_instance(specification=specification,allocation=allocation,
            draft=draft,source_records=source_records,resolved_inputs=resolved)
        require_selected_e4_plan_access(writer,resolved.plan)


def prepare_selected_e4_authoring(preparation,*,project_root,artifact_writer,output_dir):
    if type(preparation) is not ExperimentPreparation or type(preparation.specification_record) is not domain.SelectedE4NativeComponentSpecification:
        raise TypeError("selected E4 authoring requires its exact public issued component")
    selected=_component_selection(preparation.design_records)
    with artifact_writer.read_context() as writer:
        resolved=resolve_published_component_inputs(writer,selected,specification=preparation.specification_record)
        draft,records,_,design,configs=domain.component_design(preparation.specification_record,resolved)
        if draft!=preparation.draft or records!=preparation.input_records or preparation.dependencies:
            raise ValueError("selected E4 authoring changes science or retains unresolved entry prerequisites")
        preflight_authoring_output_directory(directory=Path(output_dir),repo_root=Path(project_root),artifact_writer=artifact_writer)
        preview=preview_prepared_prospective_experiment_candidate(preparation=preparation,design_inputs=design,
            source_configs=configs,project_root=project_root,artifact_writer=artifact_writer)
        resources=bind_execution_resources(dict(resolved.plan.component_resources)[preparation.specification_record.component_id],
            issued_extensions=preview.issued_extensions)
        require_selected_e4_plan_access(writer,resolved.plan)
        return replace(preparation,prospective_spec=design.bind_resources(resources),source_configs=configs,
            prospective_candidate_preview=preview)


def bind_selected_e4_component(handoff,*,specification,allocation,source_records,artifact_writer,reveal_authority_id=None):
    from .selected_e4_native_runtime import bind_selected_e4_handoff
    authenticate_selected_e4_component_instance(specification=specification,allocation=allocation,
        draft=handoff.compilation.draft,source_records=source_records,artifact_writer=artifact_writer)
    return bind_selected_e4_handoff(handoff,writer=artifact_writer,reveal_authority_id=reveal_authority_id)


def read_selected_e4_component(*,selected,artifact_writer,**kwargs):
    """Authenticate the shared plan without rebuilding the retained workflow."""
    from empirical_lawhood.api.selected_e4_native_read import read_selected_e4_component as read
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.prospective_experiment import ALLOCATION_FILENAME,SPECIFICATION_FILENAME,source_filename
    if len(selected.instance.sources)!=1:
        raise ValueError("selected E4 read requires one exact published-plan component reference")
    reference,=selected.instance.sources
    selection=decode_canonical_bytes(selected.payloads[source_filename(reference)],domain.SelectedE4NativeComponentInputs,
        maximum_bytes=None)
    _component_selection(((reference.object_id,selection),))
    if ObjectIdentity.from_record(reference.object_id,selection)!=reference:
        raise ValueError("selected E4 read changes its exact retained component reference")
    specification=decode_canonical_bytes(selected.payloads[SPECIFICATION_FILENAME],domain.SelectedE4NativeComponentSpecification,
        maximum_bytes=None)
    allocation=decode_canonical_bytes(selected.payloads[ALLOCATION_FILENAME],UnitAllocation,maximum_bytes=None)
    with artifact_writer.read_context() as writer:
        resolved=resolve_published_component_inputs(writer,selection,specification=specification)
        programme=resolved.plan.declaration
        groups=programme.programme.group_ids if specification.wave_id is None else programme.wave(specification.wave_id).group_ids
        if allocation!=domain.programme_allocation(resolved.plan,group_ids=groups):
            raise ValueError("selected E4 read changes its complete original group allocation")
        result=read(selected=selected,artifact_writer=writer,**kwargs)
        writer.require_verification_snapshot()
        require_selected_e4_plan_access(writer,resolved.plan)
        return result
