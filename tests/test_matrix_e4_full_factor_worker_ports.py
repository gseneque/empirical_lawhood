# SPDX-License-Identifier: MPL-2.0
"""Actual PURE E4 worker invocations over disclosed typed in-memory custody.

Task/receipt locators are synthetic controls. No issue, reveal, native work or
scientific qualification is supplied. Public lifecycle acceptance stays separate.
"""
from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner,full_factor_records as records,full_factor_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import (
    ScheduledFullFactorScope,ScheduledFullFactorSourceReference,scope_reference)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling,OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation,ArtifactProfile,LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef,CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding,TaskContext,WorkerInputBinding,WorkerInputKind,WorkerInputPort,WorkerIsolationProfile,WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec,BarrierKind,ExecutionTask,ExternalInputSpec,ScientificInputRole,ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract,PreparedNativeInputContract,PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.test_matrix_e4_full_factor_public import selected  # noqa: F401
from tests.test_matrix_e4_full_factor_values import scopes,pin  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401


def _logical(protected,producer,output):
    return ('scientific.' if protected else 'artifact.run.disclosed-worker.')+producer+'.'+output


def _invocation(config,values,producers,*,outputs=None):
    protected=config.protected
    phase='reduce' if type(config) is owner.ScheduledFullFactorReduceConfig else config.operation
    declaration=next(row for row in owner.operation_declarations() if row.capability_key==owner.key(protected,phase))
    manifest=declaration.manifest();task_id=config.config_id.removeprefix('config.')
    budget=dict(config.resources.phase_budgets)['reduce'] if phase=='reduce' else config.budget
    declared_access=OutcomeAccess.EVALUATION_REVEALED if protected else OutcomeAccess.DEVELOPMENT_VISIBLE
    declared_visibility=VisibilityCeiling.OUTCOME_VISIBLE if protected else VisibilityCeiling.DEVELOPMENT_ONLY
    parents=config.produced_input_parents if phase=='reduce' else values['source'].produced_input_parents
    access,visibility=produced_access(declared_access=declared_access,declared_visibility=declared_visibility,parents=parents)
    ports=[];contracts=[];external=[];edges=[];receipts={}
    for name,value in sorted({'automatic':config,**values}.items()):
        array=type(value) is bytes
        raw=value if array else value.canonical_bytes()
        schema,media,profile=(MATRIX_ARRAY_SCHEMA,'application/x-npz',ArtifactProfile.MATRIX_ARRAY_NPZ) if array else (value.SCHEMA,'application/json',ArtifactProfile.CANONICAL_JSON)
        producer=producers.get(name);output='arrays' if array else 'product'
        logical_id=(_logical(protected,producer,output) if producer else config.config_id if name=='automatic' else value.record_id)
        digest=sha256(raw).hexdigest()
        logical=LogicalArtifactIdentity(logical_id,digest,schema,profile,media,visibility,
            tuple(parent.visibility_ceiling for parent in parents),access,
            ArtifactGenericValidation('validator.disclosed-full-factor-worker','1.0.0','1'*64,schema,profile),lineage_parents=parents)
        binding=WorkerInputBinding(logical_id,'material.'+name,schema,media,len(raw),visibility,access,
            WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding,MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical,binding,digest))
        if producer:receipts.setdefault(producer,[]).append(binding.materialization_id)
        else:external.append(ExternalInputSpec('external.'+name,logical_id,digest,schema,media,len(raw),visibility,access,None))
        if name!='automatic':
            output_name=output if outputs is None else outputs.get(name,output)
            edges.append(ScientificInputSpec('edge.'+name,name,ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer,None if producer is None else producer+'.'+output_name,None if producer else 'external.'+name,
                'scientific.'+producer+'.'+output if producer else logical_id,logical_id,schema,media,len(raw),access,visibility,BarrierKind.NONE))
    dependencies=tuple(DependencyReceiptBinding('receipt.'+task,task,tuple(sorted(materials))) for task,materials in sorted(receipts.items()))
    ports=tuple(sorted(ports,key=lambda row:row.artifact_id));contracts=tuple(sorted(contracts,key=lambda row:row.artifact_id))
    config_ref=CapabilityConfigRef(config.config_id,config.SCHEMA,manifest.config_schema_sha256,config.fingerprint(),config.config_id)
    output_ports=tuple(WorkerOutputPort(task_id+'.'+row.output_id,row.payload_schema,row.profile,row.media_type,
        _logical(protected,task_id,row.output_id)) for row in declaration.outputs)
    requirement=CapabilityRequirement(manifest.capability_key,manifest.capability_version,manifest.kind,config_ref,
        manifest.input_schema_ids,manifest.output_schema_ids,manifest.permissions,EvidenceCeiling.NON_PROMOTABLE,declared_access,budget)
    task=ExecutionTask(task_id,declaration.stage,requirement,manifest.implementation_sha256,tuple(sorted(receipts)),tuple(external),
        tuple(ArtifactOutputSpec(output.output_id,output.logical_artifact_id,'unpublished/'+output.output_id+'.json',output.payload_schema,
            output.profile,output.media_type,visibility,(visibility,),access) for output in output_ports),(),BarrierKind.NONE,1,
        ('obligation.disclosed-full-factor-worker',),scientific_inputs=tuple(edges))
    plan=ObjectIdentity('plan.disclosed-full-factor-worker','empirical-lawhood/runtime/execution-plan','1.0.0','a'*64)
    packages=(('synthetic/full-factor-worker-control.py','1'*64),)
    implementation=RecursiveImplementationBinding(packages,sha256(canonical_json_bytes(packages)).hexdigest(),'2'*64,'3'*40,False)
    context=TaskContext('run.disclosed-full-factor-worker',task_id,'attempt.disclosed-full-factor-worker',config_ref,
        tuple(row.binding for row in ports),ports,output_ports,manifest.permissions,declared_access,budget,WorkerIsolationProfile.TRUSTED_LOCAL,dependencies)
    prepared=PreparedInvocationContract('prepared.disclosed-full-factor-worker',manifest,implementation,
        PreparedWorkerEnvironment('/synthetic/python','4'*64,'/synthetic',()),context.run_id,task_id,context.attempt_id,
        config_ref,contracts,output_ports,manifest.permissions,declared_access,budget,WorkerIsolationProfile.TRUSTED_LOCAL,dependencies,
        execution_plan=plan,execution_task=ObjectIdentity.from_record(task_id,task),execution_task_record=task,
        required_input_artifact_ids=tuple(row.artifact_id for row in ports))
    context=replace(context,prepared_invocation=prepared)
    runner=owner.ScheduledFullFactorWorker(protected,phase,manifest=manifest).with_prepared_scope(
        (context.run_id,task_id,context.input_materialization_ids,plan))
    return runner,context


def _assessor(fixture_values,protected):
    source=fixture_values['CONFIRMATION' if protected else 'DEVELOPMENT'][2][0]
    reference=ScheduledFullFactorSourceReference(source.root_id,source.group_id,source.identity,
        ArtifactIdentity(source.record_id,'original-full-factor-source',source.SCHEMA,source.fingerprint(),'application/json',len(source.canonical_bytes())),None)
    task=owner.key(protected,'assess')+'.'+source.root_id
    config=owner.ScheduledFullFactorCaseConfig('config.'+task,'assess',pin('scope.disclosed-worker',ScheduledFullFactorScope),
        reference,ResourceBudget(1,64*1024**2,0,None,None,64*1024**2),protected)
    producer=owner.key(protected,'measure')+'.'+source.root_id
    raw,product=science.measure(source,None,artifact_id=_logical(protected,producer,'arrays'))
    return config,{'source':source,'product':product,'diagnostics':raw},{'product':producer,'diagnostics':producer},product


@pytest.mark.parametrize('protected',(False,True))
def test_actual_assessor_uses_current_operational_ports_and_exact_producer_receipt(scopes,protected):  # noqa: F811
    config,values,producers,product=_assessor(scopes,protected)
    runner,context=_invocation(config,values,producers)
    declared=OutcomeAccess.EVALUATION_REVEALED if protected else OutcomeAccess.DEVELOPMENT_VISIBLE
    assert context.outcome_access is declared
    assert context.prepared_invocation.execution_task_record.capability.requested_outcome_access is declared
    assert all((port.outcome_access,port.visibility_ceiling)==values['source'].access_pair for port in context.input_ports)
    assert all(row.logical.lineage_parents==values['source'].produced_input_parents for row in context.prepared_invocation.inputs)
    product_edge=next(row for row in context.prepared_invocation.execution_task_record.scientific_inputs if row.consumer_input_id=='product')
    assert (product_edge.logical_artifact_id==product_edge.operational_logical_artifact_id) is protected
    result=runner.execute(context)
    assessment=decode_canonical_bytes(result.outputs[0].payload,records.ScheduledFullFactorAssessment,maximum_bytes=None)
    expected=science.assess(values['source'],product,None,values['diagnostics'])
    assert assessment==expected and assessment.disposition=='HISTORY_UNAVAILABLE'
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize('protected',(False,True))
@pytest.mark.parametrize('damage',('producer','output','missing'))
def test_assessor_refuses_foreign_or_missing_dependency_before_scientific_falsifier(scopes,monkeypatch,protected,damage):  # noqa: F811
    config,values,producers,_=_assessor(scopes,protected)
    outputs=None
    if damage=='producer':producers={key:value+'.foreign' for key,value in producers.items()}
    elif damage=='output':outputs={'product':'foreign'}
    else:values.pop('product');producers.pop('product')
    runner,context=_invocation(config,values,producers,outputs=outputs)
    monkeypatch.setattr(science,'assess',lambda *args,**kwargs:pytest.fail('invalid producer reached scientific falsifier'))
    with pytest.raises(ValueError,match='exact current dependency edge'):
        runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)


def test_actual_complete_reducer_uses_each_current_measure_and_assess_receipt(selected):  # noqa: F811
    scope=selected.scope;reference=scope_reference(scope)
    config=owner.ScheduledFullFactorReduceConfig('config.'+owner.node(scope,'reduce'),reference,selected.resources,reference.produced_input_parents)
    values={'scope':scope};producers={};products=[];assessments=[]
    for source in scope.sources:
        raw,product=science.measure(source,None,artifact_id=_logical(False,owner.node(scope,'measure',source.root_id),'arrays'))
        assessment=science.assess(source,product,None,raw)
        products.append(product);assessments.append(assessment)
        for phase,value in (('measure',product),('assess',assessment)):
            name=phase+'.'+source.root_id
            values[name]=value;producers[name]=owner.node(scope,phase,source.root_id)
    runner,context=_invocation(config,values,producers)
    result=runner.execute(context)
    actual=decode_canonical_bytes(result.outputs[0].payload,records.ScheduledFullFactorCensus,maximum_bytes=None)
    assert actual==science.census(scope.programme,scope.original_cases,scope.sources,products,assessments,record_id='census.'+scope.record_id)
    assert actual.group_ids==scope.programme.group_ids and len(actual.root_ids)==len(scope.sources)
    assert all(port._reader.stream.closed for port in context.input_ports)
