# SPDX-License-Identifier: MPL-2.0
"""Typed public native TRAIN preprocessing; no native task or scientific grant."""
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import NativeTrainingAssemblyInputs
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs,prepare_experiment
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def derive_input_selection(*,specification,source_selection_path,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution, read_access=None):
    from .assembly import assemble_native_training_inputs
    inputs=load_experiment_inputs(specification,source_selection_path, artifact_writer=artifact_writer, read_access=read_access)
    bound=inputs.method_inputs
    if type(bound) is not NativeTrainingAssemblyInputs or bound.request is None or bound.request_path is None:
        raise ValueError('native preprocessing requires its complete typed request and exact original input path')
    target,request,selector,target_path,publications=assemble_native_training_inputs(assembly_specification=specification,
        request=bound.request,request_path=bound.request_path,project_root=project_root,artifact_writer=artifact_writer,
        metadata_directory=metadata_directory,output_selection_path=output_selection_path,execution=execution)
    reopened=load_experiment_inputs(target,output_selection_path, artifact_writer=artifact_writer, read_access=read_access)
    prepared=prepare_experiment(target,scientific_inputs=reopened.scientific_inputs,method_inputs=reopened.method_inputs,execution=execution)
    payload=canonical_json_bytes({'schema':'empirical-lawhood/operational/experiment-input-requirements','version':'1.0.0','value':{
        'specification':specification.identity.to_document(),'target_specification':target.identity.to_document(),
        'source_selection':selector,'native_contact':'NONE','scientific_authority':'NONE',
        'dependencies':tuple({'code':value.code,'kind':value.kind.value,'detail':value.detail,'source_key':value.source_key}
            for value in prepared.dependencies)}})
    relative=Path(metadata_directory).relative_to(artifact_writer.root.contract.canonical_path).as_posix()
    from hashlib import sha256
    requirements=artifact_writer.write(ArtifactWriteRequest('native-assembly.requirements.'+sha256(payload).hexdigest(),
        relative+'/requirements.'+sha256(payload).hexdigest()+'.json','empirical-lawhood/operational/experiment-input-requirements',
        ArtifactProfile.CANONICAL_JSON,'application/json',specification.namespace,relative,payload,
        VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    return ExperimentInputDerivationResult(specification.identity,selector,Path(output_selection_path),prepared,
        (*publications,requirements),requirements,target,target_path)
