# SPDX-License-Identifier: MPL-2.0
"""Retained full-factor replay with real original custody and no native work."""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain,full_factor_bindings as owner,full_factor_records as r,full_factor_science as science
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from .matrix_retained_replay import map_reconstructions, replay_full_factor, replay_weight
from empirical_lawhood.api.matrix_full_factor_custody import authenticate_original_full_factor_reference
from empirical_lawhood.api.recursive_qualified_parents import _output_payload
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling,OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan,ScientificStage
from empirical_lawhood.runtime.plans import ScientificInputRole
from empirical_lawhood.runtime.recursive_compiler import (decode_recursive_config_input,
    project_recursive_config_inputs,configuration_graph_bindings)
from empirical_lawhood.runtime.prospective_experiment import source_filename


def _pin(value,field):return ObjectIdentity.from_record(getattr(value,field),value)


def _decode(raw,kind):
    return decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))


def _inputs(specification,instance,payloads):
    if type(instance) is not ExperimentInstanceBinding or instance.specification!=specification.identity:
        raise PermissionError('full factor read substitutes its original exact public specification')
    references=set(instance.sources);used=set()
    def record(pin,kind,role):
        matches=tuple(row for row in references if row.object_id==role and (row.object_schema,row.object_version)==(kind.SCHEMA,kind.VERSION))
        if len(matches)!=1:raise PermissionError('full factor read lacks its exact original typed source role')
        reference,=matches
        value=_decode(payloads[source_filename(reference)],kind)
        field='programme_id' if kind in (domain.SelectedE3E4DevelopmentProgramme,domain.SelectedE4PhaseProgramme) else 'bank_id' if kind in (domain.SelectedE3E4DevelopmentBank,domain.SelectedE4PhaseBank) else 'campaign_id' if kind is domain.CampaignSpec else 'record_id'
        if (ObjectIdentity.from_record(role,value)!=reference or pin is not None and _pin(value,field)!=pin):
            raise PermissionError('full factor read substitutes actual immutable source role bytes')
        used.add(reference);return value
    protected=type(specification) is domain.ScheduledFullFactorProtectedSpecification
    request_kinds=tuple(kind for kind in domain.request_types(protected) if (kind.SCHEMA,kind.VERSION)==(specification.request.object_schema,specification.request.object_version))
    if len(request_kinds)!=1:raise PermissionError('full factor read changes exact lifecycle request edition')
    request=record(specification.request,request_kinds[0],'request')
    matches=tuple(row for row in references if row.object_schema==domain.ScheduledFullFactorScopeReference.SCHEMA)
    if len(matches)!=1:raise PermissionError('full factor read lacks one exact blind scope reference')
    reference=record(None,domain.ScheduledFullFactorScopeReference,'reference')
    records={'request':request,'reference':reference,
        'programme':record(request.programme,domain.SelectedE4PhaseProgramme if protected else domain.SelectedE3E4DevelopmentProgramme,'programme'),
        'bank':record(request.bank,domain.SelectedE4PhaseBank if protected else domain.SelectedE3E4DevelopmentBank,'bank'),
        'resources':record(request.resources,domain.ScheduledFullFactorResources,'resources')}
    records['campaign']=record(request.campaign,domain.CampaignSpec,'campaign')
    if not protected:records['original-evidence']=record(None,domain.SelectedE3E4Evidence,'original-evidence')
    if (used!=references or reference.programme!=records['programme'] or reference.protected!=protected or reference.scope!=specification.scope
            or instance.allocation!=domain.programme_allocation(reference.programme,records['bank']).identity):
        raise PermissionError('full factor read changes the complete original scope, lifecycle, measurement or allocation')
    inputs=domain.bind_inputs(specification,records).method_inputs
    domain.validate_reference(specification,inputs)
    return inputs


def _graph(specification,inputs,draft,plan):
    scope=inputs.reference;resources=inputs.resources;tasks={row.task_id:row for row in plan.tasks}
    expected_configs={}
    for source in scope.sources:
        for phase in ('measure','assess'):
            node=owner.node(scope,phase,source.root_id)
            expected_configs[node]=owner.ScheduledFullFactorCaseConfig('config.'+node,phase,scope.scope,source,dict(resources.phase_budgets)[phase],scope.protected)
    node=owner.node(scope,'reduce')
    expected_configs[node]=owner.ScheduledFullFactorReduceConfig('config.'+node,scope,resources,scope.produced_input_parents)
    if (set(tasks)!=set(expected_configs) or len(tasks)!=len(plan.tasks)
            or tuple(row.node_id for row in draft.operations)!=tuple(sorted(expected_configs))
            or draft.selected_operation_ids!=tuple(sorted(expected_configs)) or draft.links!=owner.expected_links(scope)):
        raise PermissionError('full factor read changes its complete original graph or routes future observations outside its PURE consumers')
    external={owner.scope_input(scope):(scope.scope.object_id,domain.ScheduledFullFactorScope.SCHEMA,'application/json',scope.scope_artifact.size_bytes,scope.scope.object_fingerprint)}
    for source in scope.sources:
        external[owner.source_input(source)]=(source.source.object_id,r.ScheduledFullFactorSource.SCHEMA,'application/json',source.source_artifact.size_bytes,source.source.object_fingerprint)
        if source.arrays is not None:
            artifact=source.arrays
            external[owner.array_input(source)]=(owner.array_logical(source),artifact.payload_schema,artifact.media_type,artifact.size_bytes,artifact.sha256)
    access,ceiling=owner.input_access_pair(scope)
    requested=OutcomeAccess.EVALUATION_REVEALED if scope.protected else OutcomeAccess.DEVELOPMENT_VISIBLE
    declarations={row.capability_key:row for row in owner.operation_declarations()}
    registrations={row.node_id:declarations[row.selection.capability_key].registration() for row in draft.operations}
    configs=project_recursive_config_inputs(tuple(decode_recursive_config_input(row,registrations[row.node_id])
        for row in draft.operations),registrations)
    config_rows={row.node_id:row for row in configs}
    _,config_edges=configuration_graph_bindings(configs)
    config_edges={row.consumer_node_id:row for row in config_edges}
    if {row.input_id:(row.logical_artifact_id,row.payload_schema,row.media_type,row.maximum_size_bytes,row.expected_content_sha256) for row in draft.external_inputs}!=external:
        raise PermissionError('full factor read changes exact original aliases or full scope bytes')
    if any((row.outcome_access,row.visibility_ceiling)!=(access,ceiling) for row in draft.external_inputs):
        raise PermissionError('full factor read relabels actual original follow-up input access')
    for operation in draft.operations:
        config=expected_configs[operation.node_id];task=tasks[operation.node_id]
        phase='reduce' if type(config) is owner.ScheduledFullFactorReduceConfig else config.operation
        budget=dict(resources.phase_budgets)[phase]
        stage=(ScientificStage.SYNTHESIZE if scope.protected else ScientificStage.DEVELOP) if phase=='measure' else ScientificStage.FALSIFY if phase=='assess' else ScientificStage.REPORT
        outputs={('product',(r.ScheduledFullFactorProduct if phase=='measure' else r.ScheduledFullFactorAssessment if phase=='assess' else r.ScheduledFullFactorCensus).SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json')}
        if phase=='measure':outputs.add(('arrays',r.MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'))
        if (operation.config_id!=config.config_id or operation.config_payload.encode()!=config.canonical_bytes()
                or operation.selection.capability_key!=owner.key(scope.protected,phase)
                or operation.selection.capability_version!=declarations[owner.key(scope.protected,phase)].capability_version
                or operation.resource_budget!=budget or task.stage is not stage or task.capability.requested_resources!=budget
                or (task.capability.capability_key,task.capability.capability_version,task.capability_implementation_sha256)!=(operation.selection.capability_key,operation.selection.capability_version,operation.selection.implementation_sha256)
                or task.capability.config.content_sha256!=config.fingerprint() or task.capability.config.config_id!=config.config_id
                or task.capability.config.config_schema!=config.SCHEMA or task.capability.requested_outcome_access is not requested
                or task.capability.requested_evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                or {(row.output_id.removeprefix(task.task_id+'.'),row.payload_schema,row.profile,row.media_type) for row in task.outputs}!=outputs
                or len(task.outputs)!=len(outputs) or any((row.outcome_access,row.visibility_ceiling)!=(access,ceiling) for row in task.outputs)
                or operation.maximum_attempts!=1 or task.maximum_attempts!=1 or operation.resource_lock_ids or task.resource_lock_ids
                or task.obligation_ids!=operation.obligation_ids or operation.obligation_ids!=('obligation.'+task.task_id+'.complete',)):
            raise PermissionError('full factor read changes its exact retained operation/configuration/resource/output contract')
        edges=tuple(row for row in draft.links if row.consumer_node_id==task.task_id)
        config_inputs=tuple(row for row in task.scientific_inputs if row.scientific_role is ScientificInputRole.CONFIGURATION)
        frozen=config_edges[task.task_id]
        if (len(config_inputs)!=1 or config_rows[task.task_id].input_spec not in task.external_inputs
                or config_inputs[0].edge_id!=frozen.edge_id or config_inputs[0].consumer_input_id!='config'
                or (config_inputs[0].external_input_id,config_inputs[0].operational_logical_artifact_id,
                    config_inputs[0].payload_schema,config_inputs[0].media_type,config_inputs[0].maximum_size_bytes,
                    config_inputs[0].outcome_access,config_inputs[0].visibility_ceiling)!=(frozen.external_input_id,
                    frozen.logical_artifact_id,frozen.payload_schema,frozen.media_type,frozen.maximum_size_bytes,
                    frozen.outcome_access,frozen.visibility_ceiling)):
            raise PermissionError('full factor read substitutes its exact compiler-owned original configuration custody')
        scientific=tuple(row for row in task.scientific_inputs if row.scientific_role is not ScientificInputRole.CONFIGURATION)
        actual={(row.consumer_input_id,row.producer_task_id,row.producer_output_id,row.external_input_id,row.operational_logical_artifact_id) for row in scientific}
        external_by_id={row.input_id:row for row in draft.external_inputs}
        expected={(row.consumer_input_id,row.producer_node_id,None if row.producer_node_id is None else row.producer_node_id+'.'+row.producer_output_id,
            row.external_input_id,external_by_id[row.external_input_id].logical_artifact_id if row.producer_node_id is None else
            next(value.logical_artifact_id for value in tasks[row.producer_node_id].outputs if value.output_id==row.producer_node_id+'.'+row.producer_output_id)) for row in edges}
        if (actual!=expected or len(actual)!=len(scientific)
                or task.dependency_task_ids!=tuple(sorted({row.producer_node_id for row in edges if row.producer_node_id is not None}))):
            raise PermissionError('full factor read changes actual consumed scientific producer or external links')
        for edge in edges:
            if edge.external_input_id is None:continue
            _external_contract(task,external_by_id[edge.external_input_id],access=access,ceiling=ceiling,
                development=type(plan) is DevelopmentExecutionPlan)
    return tasks


def _external_contract(task,external,*,access,ceiling,development):
    specs=tuple(row for row in task.external_inputs if row.logical_artifact_id==external.logical_artifact_id)
    edges=tuple(row for row in task.scientific_inputs if row.external_input_id==external.input_id)
    if len(specs)!=1 or len(edges)!=1:
        raise PermissionError('full factor read changes exact actually consumed external census')
    spec,=specs;edge,=edges
    # DEV's generic compiler leaves optional ExternalInputSpec size unset.
    # Its scientific edge and actual canonical publication retain exact bytes.
    if (spec.expected_size_bytes!=external.maximum_size_bytes
            and not (development and spec.expected_size_bytes is None)
            or (spec.expected_payload_schema,spec.expected_media_type,spec.expected_content_sha256,
                spec.expected_outcome_access,spec.expected_visibility_ceiling)!=(external.payload_schema,
                external.media_type,external.expected_content_sha256,access,ceiling)
            or (edge.logical_artifact_id,edge.operational_logical_artifact_id,edge.payload_schema,edge.media_type,
                edge.maximum_size_bytes,edge.outcome_access,edge.visibility_ceiling,edge.producer_task_id,edge.producer_output_id)!=(
                external.logical_artifact_id,external.logical_artifact_id,external.payload_schema,external.media_type,
                external.maximum_size_bytes,access,ceiling,None,None)):
        raise PermissionError('full factor read changes exact actually consumed external byte/access contract')


def _payload(writer,receipts,tasks,node,output,*,original_input_access=None,publication_facts=None):
    task=tasks[node];receipt=receipts.get(node)
    rows=tuple(row for row in task.outputs if row.output_id==node+'.'+output)
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED or len(rows)!=1:
        raise PermissionError('full factor read lacks an actual successful exact producing receipt')
    logicals=tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id==rows[0].logical_artifact_id)
    materials=tuple(row for row in receipt.output_materializations if row.logical_artifact_id==rows[0].logical_artifact_id)
    if len(logicals)!=1 or len(materials)!=1:raise PermissionError('full factor read changes actual output publication census')
    if original_input_access is not None:
        if publication_facts is None:
            facts=set()
            for value in receipts.values():
                by_id={row.logical_artifact_id:row for row in value.output_logical_artifacts}
                facts.update((by_id[row.logical_artifact_id],row) for row in value.output_materializations
                    if row.logical_artifact_id in by_id)
        else:facts=publication_facts
        def before_member(member):
            if (member.logical,member.materialization) not in facts:
                original_input_access.require_member(member)
            original_input_access.require_current()
        manifest=writer.read_manifest(materials[0].relative_path)
        if (manifest.logical,manifest.materialization)!=(logicals[0],materials[0]):
            raise PermissionError('full factor retained output substitutes its actual receipt publication')
        writer.verify_manifest(manifest,before_member=before_member)
        original_input_access.require_current()
        raw=read_bounded_bytes(writer.root.resolve(materials[0].relative_path,for_write=False),maximum_bytes=materials[0].size_bytes)
        if len(raw)!=materials[0].size_bytes or sha256(raw).hexdigest()!=logicals[0].content_sha256:
            raise PermissionError('full factor retained output changed after exact custody authentication')
        original_input_access.require_current()
        return raw
    return _output_payload(writer,receipt,logicals[0],materials[0].size_bytes)



def _scope_input(writer,plan,reference,*,current_inputs=None,original_input_access=None):
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    if type(reference) is not domain.ScheduledFullFactorScopeReference:
        raise TypeError('full factor consumed scope requires its exact immutable FILE reference')
    reference.__post_init__()
    development=type(plan) is DevelopmentExecutionPlan
    if not development and not reference.protected:
        raise PermissionError('full factor consumed scope changes its actual original source lifecycle')
    external=SimpleNamespace(input_id=owner.scope_input(reference),logical_artifact_id=reference.scope.object_id,
        payload_schema=domain.ScheduledFullFactorScope.SCHEMA,media_type='application/json',
        maximum_size_bytes=reference.scope_artifact.size_bytes,expected_content_sha256=reference.scope.object_fingerprint)
    tasks=tuple(task for task in plan.tasks if any(row.logical_artifact_id==external.logical_artifact_id for row in task.external_inputs))
    if not tasks:raise PermissionError('full factor read lacks its exact actually consumed scope FILE')
    access,ceiling=owner.input_access_pair(reference)
    for task in tasks:_external_contract(task,external,access=access,ceiling=ceiling,development=development)
    if development:
        if current_inputs is None:raise PermissionError('full factor DEV read requires actual authored input custody')
        values=tuple(row for row in current_inputs if row.logical.logical_artifact_id==external.logical_artifact_id)
        if len(values)!=1:raise PermissionError('full factor DEV read changes its exact consumed scope input census')
        value,=values;relative=value.materialization.relative_path
    else:
        if current_inputs is not None:raise PermissionError('full factor protected read cannot substitute DEV input custody')
        relative,_,_=provider_input_location(writer,plan.source_plan.object_id,external.logical_artifact_id)
    manifest=writer.read_manifest(relative)
    if original_input_access is not None:original_input_access.require_member(manifest)
    writer.verify_manifest(manifest,**({} if original_input_access is None else {'before_member':original_input_access.require_member}))
    if (development and (manifest.logical,manifest.materialization)!=(value.logical,value.materialization)
            or (manifest.logical.logical_artifact_id,manifest.logical.payload_schema,manifest.logical.content_sha256,
                manifest.materialization.size_bytes,manifest.logical.outcome_access,manifest.logical.visibility_ceiling)!=(
                external.logical_artifact_id,external.payload_schema,external.expected_content_sha256,
                external.maximum_size_bytes,access,ceiling)):
        raise PermissionError('full factor read substitutes actual scope FILE publication')
    if original_input_access is not None:original_input_access.require_current()
    consumed=_decode(read_bounded_bytes(writer.root.resolve(relative,for_write=False),maximum_bytes=external.maximum_size_bytes),domain.ScheduledFullFactorScope)
    if owner.scope_reference(consumed)!=reference:
        raise PermissionError('full factor consumed FILE differs from exact selected canonical observations')
    return consumed

def _replay(*,writer,specification,inputs,draft,plan,receipts,codecs,current_inputs=None,
        _consume_programme_result=None,current_access=None,original_input_access=None,reconstruct=True):
    # One finite read covers every original array, marker and structural output.
    # Current reveal is checked again after that physical guard, so a long
    # independent replay cannot return on an authority that expired meanwhile.
    with writer.read_context() as reading:
        result=_replay_values(writer=reading,specification=specification,inputs=inputs,draft=draft,plan=plan,
            receipts=receipts,codecs=codecs,current_inputs=current_inputs,
            _consume_programme_result=_consume_programme_result,current_access=current_access,
            original_input_access=original_input_access,reconstruct=reconstruct)
        reading.require_verification_snapshot()
    if inputs.reference.protected:
        from empirical_lawhood.api.matrix_full_factor_runtime import _original_grants
        # The authority owner closes its own actual custody before sampling
        # the final UTC. Do not add a later physical walk after that check.
        _original_grants(writer,inputs.reference,current_access=current_access)
    if original_input_access is not None:original_input_access.require_current(artifact_writer=writer)
    return result


def _replay_values(*,writer,specification,inputs,draft,plan,receipts,codecs,current_inputs=None,
        _consume_programme_result=None,current_access=None,original_input_access=None,reconstruct=True):
    tasks=_graph(specification,inputs,draft,plan)
    if set(receipts)!=set(tasks):raise PermissionError('full factor read lacks its complete successful follow-up receipt census')
    from empirical_lawhood.api.matrix_full_factor_secondary import authenticate_full_factor_target
    target=authenticate_full_factor_target(writer=writer,request=inputs.request,bank=inputs.bank)
    if inputs.reference.protected:
        from empirical_lawhood.api.matrix_full_factor_runtime import _original_grants
        # Original current grants precede value-level decoding of copied
        # outcome bodies. This metadata check cannot qualify the source.
        with writer.verification_scope() as controls:
            original_reader=CurrentResultPlanReader(controls)
            _original_grants(controls,inputs.reference,control_reader=original_reader,current_access=current_access)
            controls.require_verification_snapshot()
    if original_input_access is not None:original_input_access.require_current()
    consumed_scope=_scope_input(writer,plan,inputs.reference,current_inputs=current_inputs,original_input_access=original_input_access)
    functional_rows=[]
    mechanism_rows=[]
    kwargs={'_secondary_target':target, '_secondary_readout':inputs.request.secondary_readout}
    if reconstruct:
        kwargs.update(_consume_functional=functional_rows.append,_consume_mechanism=mechanism_rows.append)
    if _consume_programme_result is not None:
        kwargs['_consume_programme_result']=_consume_programme_result
    original=[]
    def observe(**values):
        original.append(values)
        if _consume_programme_result is not None:_consume_programme_result(**values)
    kwargs['_consume_programme_result']=observe
    scope,original_files=authenticate_original_full_factor_reference(writer=writer,reference=inputs.reference,codecs=codecs,
        current_access=current_access,**kwargs)
    if len(original)!=1:raise PermissionError('full factor read lacks one exact authenticated original phase projection')
    inputs=replace(inputs,scope=scope)
    files=dict(original_files)
    if scope!=consumed_scope:raise PermissionError('full factor consumed FILE differs from authenticated original observations')
    products=[];assessments=[]
    publication_facts=set()
    for receipt in receipts.values():
        by_id={row.logical_artifact_id:row for row in receipt.output_logical_artifacts}
        publication_facts.update((by_id[row.logical_artifact_id],row) for row in receipt.output_materializations
            if row.logical_artifact_id in by_id)
    publication_facts=frozenset(publication_facts)
    def payload(node,output):
        return _payload(writer,receipts,tasks,node,output,original_input_access=original_input_access,
            publication_facts=publication_facts)
    def reconstruction_inputs():
        for source in inputs.scope.sources:
            if original_input_access is not None:original_input_access.require_current()
            product=_decode(payload(owner.node(inputs.scope,'measure',source.root_id),'product'),r.ScheduledFullFactorProduct)
            assessment=_decode(payload(owner.node(inputs.scope,'assess',source.root_id),'product'),r.ScheduledFullFactorAssessment)
            if reconstruct:
                diagnostic=payload(owner.node(inputs.scope,'measure',source.root_id),'arrays')
                native=None
                if source.history is not None:
                    file=files[owner.array_input(source)]
                    if original_input_access is not None:original_input_access.require_current()
                    native=read_bounded_bytes(file.path,maximum_bytes=file.maximum_bytes)
                yield replay_weight(records=(source,product,assessment),
                    archives=((native,source.full_arrays),(diagnostic,product.arrays))), (source,product,assessment,native,diagnostic)
            products.append(product);assessments.append(assessment)
    replayed=map_reconstructions(writer,replay_full_factor,reconstruction_inputs())
    if reconstruct and replayed!=tuple(source.root_id for source in inputs.scope.sources):
        raise PermissionError('full factor reconstruction changes the complete ordered source census')
    if original_input_access is not None:original_input_access.require_current()
    retained=_decode(payload(owner.node(inputs.scope,'reduce'),'product'),r.ScheduledFullFactorCensus)
    expected=science.census(inputs.programme,inputs.scope.original_cases,inputs.scope.sources,tuple(products),tuple(assessments),record_id='census.'+inputs.scope.record_id)
    if retained!=expected:raise PermissionError('full factor read changes the exact complete original whole-group reduction')
    base={'scientific_completion':'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS' if reconstruct else 'DEFERRED_TO_FULL_READ',
        'decision_consumption':'COMPLETE_RETAINED_FACTOR_CENSUS','scientific_reconstruction':'FULL' if reconstruct else 'OFF',
        'scientific_qualification':'NOT_ESTABLISHED','original_programme':scope.programme.to_document(),
        'sampling_warrant':'NOT_ESTABLISHED','new_native_contact_count':0,'scope':inputs.scope.identity.to_document(),
        'assigned_groups':len(inputs.programme.group_ids),'assigned_cases':len(inputs.scope.sources),
        'actual_pure_task_count':len(tasks),'census':retained.to_document(),
        'measurements':tuple(row.identity.to_document() for row in products),
        'assessments':tuple(row.to_document() for row in assessments),
        'original_response':original[0]['report'],
        'original_wave_observations':tuple(row.to_document() for row in original[0]['observations'])}
    if not reconstruct:
        return base
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_secondary_readout import structural_functional_projection
    secondary=structural_functional_projection(scope,products,assessments,functional_rows,
        target=target,secondary=inputs.request.secondary_readout)
    if any(row.prediction is None for row in functional_rows):
        raise PermissionError('full factor read omits original causal features for the structural comparison')
    from empirical_lawhood.kernel.serialization import canonical_value
    return {**base,
        **({'same_bank_mechanism':canonical_value(tuple(mechanism_rows))} if mechanism_rows else {}),
        'prediction_cases':tuple(row.prediction.to_document() for row in functional_rows),
        'secondary_structural_functional_readout':secondary}


def _deferred():return {'scientific_completion':'NOT_ESTABLISHED','scientific_qualification':'NOT_ESTABLISHED',
    'sampling_warrant':'NOT_ESTABLISHED','state':'FULL_FACTOR_ASSESSMENT_DEFERRED','new_native_contact_count':0}


def read_development_result(*,directory,artifact_writer,specification,instance,payloads,report,products,draft,plan,allow_partial=False,
        _consume_programme_result=None,read_access=None):
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    if type(specification) not in (domain.ScheduledFullFactorDevelopmentSpecification,domain.ScheduledFullFactorProtectedSpecification):raise TypeError('full factor exposed read requires its exact lifecycle leaf')
    if allow_partial or report.get('status')!='SUCCEEDED' or report.get('typed_product_validation')=='DEFERRED':return _deferred()
    inputs=_inputs(specification,instance,payloads)
    from empirical_lawhood.api.recursive_operations import operation_catalog
    current_inputs=products.get('external_inputs')
    if type(current_inputs) is not tuple or any(type(row) is not VerifiedArtifactInput for row in current_inputs):
        raise PermissionError('full factor DEV read requires the shared authenticated external input census')
    return _replay(writer=artifact_writer,specification=specification,inputs=inputs,draft=draft,plan=plan,
        receipts=products['receipts'],codecs=operation_catalog()[2],current_inputs=current_inputs,
        _consume_programme_result=_consume_programme_result,current_access=read_access,
        original_input_access=getattr(payloads,'original_input_access',None),reconstruct=scientific_reconstruction_enabled())
