# SPDX-License-Identifier: MPL-2.0
"""Actual copied configured E3 transition; no human/scientific permission inference."""
from pathlib import Path
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import ConfiguredProtectedE3AssemblyInputs
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs,prepare_experiment
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def derive_input_selection(*,specification,source_selection_path,project_root,artifact_writer,metadata_directory,output_selection_path,execution, read_access=None):
    selected=load_experiment_inputs(specification,source_selection_path, artifact_writer=artifact_writer, read_access=read_access).method_inputs
    if (type(selected) is not ConfiguredProtectedE3AssemblyInputs or selected.request is None
            or selected.request_path is None or selected.scientific_protocol is None):
        raise ValueError('configured E3 preprocessing needs its complete typed original request')
    options = dict(specification=specification, selected=selected, project_root=project_root,
        artifact_writer=artifact_writer, metadata_directory=metadata_directory,
        output_selection_path=output_selection_path, execution=execution, read_access=read_access)
    if selected.retained_training_continuation is not None:
        from empirical_lawhood.api.matrix_programme_retained_training_continuation import authenticated_e3_continuation
        with authenticated_e3_continuation(project_root=project_root, artifact_writer=artifact_writer,
                selected=selected.retained_training_continuation, execution=execution) as continued:
            return _derive_selected(continued_context=continued, **options)
    return _derive_selected(continued_context=None, **options)


def _derive_selected(*, specification, selected, project_root, artifact_writer, metadata_directory,
        output_selection_path, execution, read_access, continued_context):
    from .assembly import assemble_configured_e3_inputs
    target,selector,target_path,publications=assemble_configured_e3_inputs(assembly_specification=specification,
        assembly_request=selected.request,scientific_protocol=selected.scientific_protocol,primary_amendment=selected.primary_amendment,request_path=selected.request_path,project_root=project_root,artifact_writer=artifact_writer,
        metadata_directory=metadata_directory,output_selection_path=output_selection_path,execution=execution,
        export_adoption=selected.export_adoption,continued_context=continued_context)
    inputs=load_experiment_inputs(target,output_selection_path, artifact_writer=artifact_writer, read_access=read_access)
    prepared=prepare_experiment(target,scientific_inputs=inputs.scientific_inputs,method_inputs=inputs.method_inputs,execution=execution)
    payload=canonical_json_bytes({'schema':'empirical-lawhood/operational/experiment-input-requirements','version':'1.0.0','value':{
        'specification':specification.identity.to_document(),'target_specification':target.identity.to_document(),
        'source_selection':selector,'native_contact':'NONE','scientific_authority':'NONE',
        'dependencies':tuple({'code':value.code,'kind':value.kind.value,'detail':value.detail,'source_key':value.source_key} for value in prepared.dependencies)}})
    from hashlib import sha256
    relative=Path(metadata_directory).relative_to(artifact_writer.root.contract.canonical_path).as_posix()
    requirements=artifact_writer.write(ArtifactWriteRequest('configured-assembly.requirements.'+sha256(payload).hexdigest(),
        relative+'/requirements.'+sha256(payload).hexdigest()+'.json','empirical-lawhood/operational/experiment-input-requirements',
        ArtifactProfile.CANONICAL_JSON,'application/json',selected.request.namespace,relative,payload,
        VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    return ExperimentInputDerivationResult(specification.identity,selector,Path(output_selection_path),prepared,
        (*publications,requirements),requirements,target,target_path)
