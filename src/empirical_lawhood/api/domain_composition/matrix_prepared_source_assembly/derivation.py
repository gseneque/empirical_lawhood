# SPDX-License-Identifier: MPL-2.0
"""Registered source preprocessing; the target keeps ordinary prospective guards."""
from pathlib import Path
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.matrix_programme_e4_inputs import prepared_source_lineage
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, inherited_visibility
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, derived_outcome_access
from empirical_lawhood.execution.experiment_preparation import ExperimentInputDerivationResult


def derive_input_selection(*,specification,source_selection_path,project_root,artifact_writer,metadata_directory,output_selection_path,execution, read_access=None):
    from empirical_lawhood.api.domain_composition.matrix_prepared_source_assembly.assembly import assembled_prepared_source_inputs


    inputs=load_experiment_inputs(specification,source_selection_path, artifact_writer=artifact_writer, read_access=read_access)
    from empirical_lawhood.domains.matrix.matrix_prepared_source_assembly import validate_inputs
    validate_inputs(specification,inputs.method_inputs,complete=True)
    with assembled_prepared_source_inputs(assembly_specification=specification,
        assembly_inputs=inputs.method_inputs,project_root=project_root,artifact_writer=artifact_writer,
        metadata_directory=metadata_directory,output_selection_path=output_selection_path,execution=execution,read_access=read_access) as (target,selector,target_path,publications):
        target_inputs=load_experiment_inputs(target,output_selection_path, artifact_writer=artifact_writer, read_access=read_access)
        prepared=prepare_experiment(target,scientific_inputs=target_inputs.scientific_inputs,method_inputs=target_inputs.method_inputs,execution=execution)
        payload=canonical_json_bytes({'schema':'empirical-lawhood/operational/experiment-input-requirements','version':'1.0.0','value':{
            'specification':specification.identity.to_document(),'target_specification':target.identity.to_document(),
            'source_selection':selector,'native_contact':'NONE','scientific_authority':'NONE',
            'operational_effect':'EXPLICIT_METADATA_ONLY_DATASET_AUTHORIZATION_AND_TRANSFORMATION',
            'dependencies':tuple({'code':value.code,'kind':value.kind.value,'detail':value.detail,'source_key':value.source_key} for value in prepared.dependencies)}})
        from hashlib import sha256
        relative=Path(metadata_directory).relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        parents=prepared_source_lineage(original_e3=inputs.method_inputs.request.original_e3,
            development_product=inputs.method_inputs.development_product)
        access=derived_outcome_access(OutcomeAccess.OUTCOME_BLIND,*(value.outcome_access for value in parents))
        ceilings=tuple(value.visibility_ceiling for value in parents)

        requirements=artifact_writer.write(ArtifactWriteRequest('prepared-source-assembly.requirements.'+sha256(payload).hexdigest(),
            relative+'/requirements.'+sha256(payload).hexdigest()+'.json','empirical-lawhood/operational/experiment-input-requirements',
            ArtifactProfile.CANONICAL_JSON,'application/json',inputs.method_inputs.request.namespace,relative,payload,
            inherited_visibility(ceilings,access),ceilings,access,lineage_parents=parents))

        return ExperimentInputDerivationResult(specification.identity,selector,Path(output_selection_path),prepared,
            (*publications,requirements),requirements,target,target_path)
