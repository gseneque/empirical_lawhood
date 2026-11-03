# SPDX-License-Identifier: MPL-2.0
"""Public original-custody derivation; no issue, grant, reveal or native work."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain,full_factor_bindings as methods
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs,prepare_experiment
from empirical_lawhood.api.matrix_full_factor_custody import derive_original_full_factor_scope
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentFileInputBinding,ExperimentFileInputSelection
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent,ArtifactProfile,ArtifactWriteRequest,lineage_parent_sort_key,derived_outcome_access
from empirical_lawhood.kernel.evidence import inherited_visibility
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def _identity(role,value):
    field={'programme':'programme_id','bank':'bank_id','campaign':'campaign_id'}.get(role,'record_id')
    return ObjectIdentity.from_record(getattr(value,field),value)


def derive_input_selection(*,specification,source_selection_path,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution,read_access=None):
    if type(specification) not in (domain.ScheduledFullFactorDevelopmentSpecification,domain.ScheduledFullFactorProtectedSpecification):
        raise TypeError('full factor derivation requires exact static lifecycle leaf')
    bound=load_experiment_inputs(specification,source_selection_path,artifact_writer=artifact_writer,read_access=read_access).method_inputs
    return derive_bound_input_selection(specification=specification,method_inputs=bound,project_root=project_root,
        artifact_writer=artifact_writer,metadata_directory=metadata_directory,
        output_selection_path=output_selection_path,execution=execution,read_access=read_access)


def derive_bound_input_selection(*,specification,method_inputs,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution,_consume_programme_result=None,read_access=None):
    """Derive an ordinary internal PURE stage from its actual typed choices.

    This is the same original-custody owner used by copied public inputs. It
    does not require a researcher to manufacture another request or selector.
    """
    if type(specification) not in (domain.ScheduledFullFactorDevelopmentSpecification,domain.ScheduledFullFactorProtectedSpecification):
        raise TypeError('full factor derivation requires exact static lifecycle leaf')
    bound=method_inputs
    if type(bound) is not domain.ScheduledFullFactorFollowupInputs or any(getattr(bound,name) is None for name in ('request','programme','bank','resources')):
        raise ValueError('full factor derivation requires original request/programme/bank/resources')
    bound.__post_init__()
    if bound.request.identity!=specification.request:raise ValueError('full factor derivation changes request pin')
    protected=type(specification) is domain.ScheduledFullFactorProtectedSpecification
    expected=domain.request_types(protected)
    if type(bound.request) not in expected:raise ValueError('full factor request changes static lifecycle')
    for role in ('programme','bank','resources'):
        if _identity(role,getattr(bound,role))!=getattr(bound.request,role):raise ValueError('full factor derivation changes requested '+role)
    if specification.preparation is not None:
        raise ValueError('full factor exposed derivation cannot carry a new protected preparation')
    if bound.campaign is None or _identity('campaign',bound.campaign)!=bound.request.campaign:
        raise ValueError('full factor exposed derivation needs its exact explicit campaign')
    if any(getattr(execution,name) is None for name in ('workers','environment_id','source_snapshot','output_root')):
        raise ValueError('full factor derivation requires complete real execution selection')
    root=Path(artifact_writer.root.contract.canonical_path);directory=Path(metadata_directory);selector_path=Path(output_selection_path)
    if (not directory.is_absolute() or directory!=directory.resolve(strict=False) or not directory.is_relative_to(root)
            or not selector_path.is_absolute() or selector_path!=selector_path.resolve(strict=False)
            or selector_path!=directory/'sources.json' or execution.output_root!=str(root)):
        raise ValueError('full factor derivation needs exact selected guarded metadata/selector/output roots')
    relative=directory.relative_to(root).as_posix()
    artifact_writer.root.resolve(relative+'/specification.json',for_write=True)
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    implementation=implementation_binding(project_root)
    if execution.source_snapshot!=ObjectIdentity.from_record('recursive-member.implementation',implementation):
        raise ValueError('full factor derivation source differs from actual selected checkout/source bundle')
    from empirical_lawhood.api.recursive_operations import operation_catalog
    codecs=operation_catalog()[2]
    request=bound.request
    from empirical_lawhood.api.matrix_full_factor_secondary import authenticate_full_factor_target
    secondary_target=authenticate_full_factor_target(writer=artifact_writer,request=request,bank=bound.bank)
    accesses=[]
    scope,files=derive_original_full_factor_scope(writer=artifact_writer,programme=bound.programme,bank=bound.bank,
        record_id='scope.'+specification.specification_id,codecs=codecs,
        development=None if protected else request.original,declaration=request.declaration if protected else None,
        waves=request.waves if protected else (),_consume_programme_result=_consume_programme_result,
        current_access=read_access,_secondary_target=secondary_target,_secondary_readout=request.secondary_readout,
        _consume_original_access=lambda access,evidence:accesses.append((access,evidence)))
    if len(accesses)!=1:raise PermissionError('full factor derivation lacks its actual original access scope')
    access,evidence=accesses[0]
    bound=replace(bound,original_evidence=evidence)
    return _derive_observed_input_selection(specification=specification,method_inputs=bound,scope=scope,files=files,
        project_root=project_root,artifact_writer=artifact_writer,metadata_directory=metadata_directory,
        output_selection_path=output_selection_path,execution=execution,original_input_access=access,read_access=read_access)


def _derive_observed_input_selection(*,specification,method_inputs,scope,files,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution,original_input_access,read_access=None):
    """Publish the scope just read by the owning ordinary E4 completion operation.

    This private handoff retains one actual original observation in that
    operation. Public copied-input derivation still authenticates its originals
    above; authoring and retained replay keep their independent custody checks.
    """
    bound=method_inputs
    protected=type(specification) is domain.ScheduledFullFactorProtectedSpecification
    if (type(specification) not in (domain.ScheduledFullFactorDevelopmentSpecification,domain.ScheduledFullFactorProtectedSpecification)
            or type(bound) is not domain.ScheduledFullFactorFollowupInputs
            or type(scope) is not domain.ScheduledFullFactorScope
            or scope.programme!=bound.programme or scope.protected!=protected
            or bound.programme.bank!=bound.bank.identity):
        raise PermissionError('ordinary E4 structure changes its actual observed scientific scope')
    bound.__post_init__();scope.__post_init__();specification.__post_init__();execution.__post_init__()
    access_context=original_input_access
    if access_context.parents!=scope.produced_input_parents:
        raise PermissionError('full factor derivation changes its actual original produced-parent census')
    access_context.require_current()
    request=bound.request
    if (type(request) not in domain.request_types(protected) or request.identity!=specification.request
            or request.resources!=bound.resources.identity or request.programme!=bound.programme.identity
            or request.bank!=bound.bank.identity or request.campaign!=_identity('campaign',bound.campaign)
            or (protected and (scope.declaration.identity!=request.declaration or scope.waves!=request.waves))
            or (not protected and scope.development!=request.original)):
        raise PermissionError('ordinary E4 structure changes its actual original request or runtime reservations')
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    implementation=implementation_binding(project_root)
    if execution.source_snapshot!=ObjectIdentity.from_record('recursive-member.implementation',implementation):
        raise ValueError('full factor derivation source differs from actual selected implementation')
    root=Path(artifact_writer.root.contract.canonical_path);directory=Path(metadata_directory);selector_path=Path(output_selection_path)
    if (any(getattr(execution,name) is None for name in ('workers','environment_id','source_snapshot','output_root'))
            or not directory.is_absolute() or directory!=directory.resolve(strict=False) or not directory.is_relative_to(root)
            or selector_path!=directory/'sources.json' or execution.output_root!=str(root)):
        raise ValueError('ordinary E4 structure needs exact selected guarded execution and metadata roots')
    relative=directory.relative_to(root).as_posix()
    artifact_writer.root.resolve(relative+'/specification.json',for_write=True)
    selected_measurement=domain.measurement(scope)
    target=type(specification)(specification.specification_id,request.identity,scope.identity,selected_measurement,None)
    access,visibility=methods.input_access_pair(scope)
    publications=[]
    def publish(name,record,*,logical=None,outcome=access,ceiling=visibility):
        parents=access_context.record_parents(record)
        # Locator-only records remain blind. An actual produced body or pin
        # uses this lifecycle's declared analysis lane before inheriting its
        # parents, retaining sealed DEV ancestry instead of laundering it
        # through an outcome-blind metadata declaration.
        if parents:outcome,ceiling=access,visibility
        outcome=derived_outcome_access(outcome,*(row.outcome_access for row in parents))
        ceiling=inherited_visibility((ceiling,*(row.visibility_ceiling for row in parents)),outcome)
        access_context.require_current()
        path=relative+'/'+name+'.json'
        result=artifact_writer.write(ArtifactWriteRequest(logical or 'full-factor.input.'+specification.specification_id+'.'+name.replace('/','.'),
            path,record.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','full-factor.'+specification.specification_id,
            relative,record.canonical_bytes(),ceiling,tuple(row.visibility_ceiling for row in parents),outcome,lineage_parents=parents))
        publications.append(result);return result
    draft=methods.lower(scope,bound.resources,draft_id='draft.full-factor.'+target.fingerprint(),campaign=bound.campaign)
    # All pure scope/template/graph checks precede the first metadata write.
    scope_publication=publish('scope',scope,logical=scope.record_id)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import scope_reference
    from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
    reference=scope_reference(scope)
    file_map=dict(files);file_map[methods.scope_input(scope)]=PreparedExperimentFile(reference.scope_artifact,scope.VERSION,
        artifact_writer.root.resolve(scope_publication.materialization.relative_path,for_write=False),len(scope.canonical_bytes()))
    array_publications={};source_publications={}
    for source,ref in zip(scope.sources,reference.sources,strict=True):
        publication=publish('cases/'+source.root_id,source,logical=source.record_id)
        source_publications[methods.source_input(source)]=publication
        file_map[methods.source_input(source)]=PreparedExperimentFile(ref.source_artifact,source.VERSION,
            artifact_writer.root.resolve(publication.materialization.relative_path,for_write=False),len(source.canonical_bytes()))
    for external in draft.external_inputs:
        if external.payload_schema!=methods.MATRIX_ARRAY_SCHEMA:continue
        file=file_map[external.input_id]
        source=next(row for row in scope.sources if methods.array_input(row)==external.input_id)
        from empirical_lawhood.api.matrix_full_factor_access import require_file_access
        original=require_file_access(writer=artifact_writer,file=file,access=access_context,source=source)
        access_context.require_current()
        raw=read_bounded_bytes(file.path,maximum_bytes=file.maximum_bytes)
        if len(raw)!=file.identity.size_bytes or sha256(raw).hexdigest()!=file.identity.sha256:
            raise PermissionError('full factor original array bytes changed after authentic original read')
        path=relative+'/arrays/'+source.identity.object_fingerprint+'.npz'
        parents=tuple(sorted({*access_context.parents,*original.logical.lineage_parents,
            ArtifactLineageParent(ObjectIdentity(file.identity.artifact_id,file.identity.payload_schema,file.record_version,file.identity.sha256),
                original.logical.visibility_ceiling,original.logical.outcome_access)},key=lineage_parent_sort_key))
        array_access=derived_outcome_access(access,*(row.outcome_access for row in parents))
        array_visibility=inherited_visibility((visibility,*(row.visibility_ceiling for row in parents)),array_access)
        access_context.require_current()
        publication=artifact_writer.write(ArtifactWriteRequest(external.logical_artifact_id,path,external.payload_schema,
            ArtifactProfile.MATRIX_ARRAY_NPZ,external.media_type,'full-factor.'+specification.specification_id,
            relative+'/arrays',raw,array_visibility,tuple(row.visibility_ceiling for row in parents),array_access,lineage_parents=parents))
        publications.append(publication);array_publications[external.input_id]=publication
        file_map[external.input_id]=replace(file,path=artifact_writer.root.resolve(path,for_write=False))
    records={'request':request,'programme':bound.programme,'bank':bound.bank,'resources':bound.resources,
        'reference':reference,'campaign':bound.campaign}
    if not protected:
        if bound.original_evidence is None or bound.original_evidence.produced_input_parents!=access_context.parents:
            raise PermissionError('full factor derivation omits its actual original DEV locator evidence')
        records['original-evidence']=bound.original_evidence
    bindings=[]
    for role,record in sorted(records.items()):
        publication=publish('records/'+role,record,outcome=OutcomeAccess.OUTCOME_BLIND,ceiling=VisibilityCeiling.PROSPECTIVE)
        path=artifact_writer.root.resolve(publication.materialization.relative_path,for_write=False)
        bindings.append(ExperimentInputBinding(role,_identity(role,record),path.relative_to(selector_path.parent).as_posix(),len(record.canonical_bytes())))
    file_bindings=tuple(ExperimentFileInputBinding(role,file.identity,file.record_version,
        file.path.relative_to(selector_path.parent).as_posix(),file.maximum_bytes) for role,file in sorted(file_map.items()))
    protocol=domain.PROTECTED_PROTOCOL_ID if protected else domain.DEV_PROTOCOL_ID
    selector=ExperimentFileInputSelection('inputs.'+target.specification_id+'.'+scope.fingerprint(),protocol,tuple(bindings),file_bindings)
    target_publication=publish('specification',target,logical='full-factor.specification.'+target.fingerprint(),outcome=OutcomeAccess.OUTCOME_BLIND,ceiling=VisibilityCeiling.PROSPECTIVE)
    selector_relative=selector_path.relative_to(root).as_posix()
    selector_publication=artifact_writer.write(ArtifactWriteRequest('full-factor.selector.'+selector.fingerprint(),selector_relative,
        selector.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','full-factor.'+target.specification_id,
        str(Path(selector_relative).parent),selector.canonical_bytes(),VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    publications.append(selector_publication)
    reopened=load_experiment_inputs(target,selector_path,artifact_writer=artifact_writer,read_access=read_access)
    prepared=prepare_experiment(target,scientific_inputs=reopened.scientific_inputs,method_inputs=reopened.method_inputs,execution=execution)
    payload=canonical_json_bytes({'schema':'empirical-lawhood/operational/experiment-input-requirements','version':'1.0.0','value':{
        'specification':specification.identity,'target_specification':target.identity,'source_selection':selector,
        'native_contact':'NONE','scientific_authority':'NONE','qualification':'NOT_ESTABLISHED',
        'dependencies':tuple({'code':row.code,'kind':row.kind.value,'detail':row.detail,'source_key':row.source_key} for row in prepared.dependencies)}})
    requirements=artifact_writer.write(ArtifactWriteRequest('full-factor.requirements.'+sha256(payload).hexdigest(),
        relative+'/requirements.json','empirical-lawhood/operational/experiment-input-requirements',ArtifactProfile.CANONICAL_JSON,
        'application/json','full-factor.'+target.specification_id,relative,payload,VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    publications.append(requirements)
    access_context.require_current()
    return ExperimentInputDerivationResult(specification.identity,selector,selector_path,prepared,tuple(publications),requirements,
        target,artifact_writer.root.resolve(target_publication.materialization.relative_path,for_write=False))
