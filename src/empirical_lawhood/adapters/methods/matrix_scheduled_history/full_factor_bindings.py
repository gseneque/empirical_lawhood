# SPDX-License-Identifier: MPL-2.0
"""PURE explicit full-history follow-up; no original graph or forecaster port."""
from bisect import bisect_left
from dataclasses import dataclass
from operator import attrgetter
from functools import partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput,RecursiveInputLink,RecursiveOperationSpec,RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent,ArtifactProfile,ReceiptCheck
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access,validate_produced_input_parents
from empirical_lawhood.runtime.capabilities import CapabilityKind,CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner,RunnerResult,TaskOutputPayload,WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate,ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties,RecursiveOperationDeclaration,RecursiveScientificHooks
from . import full_factor_records as r,full_factor_science as science
from .full_factor_followup_records import ScheduledFullFactorScope,ScheduledFullFactorResources,ScheduledFullFactorSourceReference,ScheduledFullFactorScopeReference,scope_reference

NAMESPACE='matrix-selected-e4-full-factor'
CEILING=ResourceBudget(1,None,0,None,None,None)
PHASES=('assess','measure','reduce')


def key(protected,phase):return NAMESPACE+('.revealed.' if protected else '.dev.')+phase

def scope_pin(scope):return scope.identity if type(scope) is ScheduledFullFactorScope else scope.scope

def node(scope,phase,root_id=None):return key(scope.protected,phase)+'.'+(scope_pin(scope).object_fingerprint if root_id is None else root_id)

def array_input(source):return 'external.full-factor.'+source.identity.object_fingerprint+'.arrays'

def array_logical(source):return 'full-factor.input.'+source.identity.object_fingerprint+'.arrays'

def source_input(source):return 'external.full-factor.'+source.identity.object_fingerprint+'.source'

def scope_input(scope):return 'external.full-factor.scope.'+scope_pin(scope).object_fingerprint


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorCaseConfig(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-case-config'
    config_id:str
    operation:str
    scope:ObjectIdentity
    source:ScheduledFullFactorSourceReference
    budget:ResourceBudget
    protected:bool

    def __post_init__(self):
        validate_stable_id(self.config_id);r._pin(self.scope,(ScheduledFullFactorScope,))
        r._exact(self.source,ScheduledFullFactorSourceReference);r._exact(self.budget,ResourceBudget)
        if type(self.protected) is not bool:raise TypeError('full factor config needs exact static lifecycle')
        if self.operation not in ('measure','assess') or not CEILING.contains(self.budget):
            raise ValueError('full factor case configuration changes PURE method or selected resource ceiling')


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorReduceConfig(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-reduce-config'
    VERSION:ClassVar[str]='2.0.0'
    config_id:str
    scope:ScheduledFullFactorScopeReference
    resources:ScheduledFullFactorResources
    produced_input_parents:tuple[ArtifactLineageParent,...]

    def __post_init__(self):
        validate_stable_id(self.config_id);r._exact(self.scope,ScheduledFullFactorScopeReference)
        r._exact(self.resources,ScheduledFullFactorResources)
        validate_produced_input_parents(self.produced_input_parents)
        if self.produced_input_parents!=self.scope.produced_input_parents:
            raise ValueError('full factor reducer changes its complete original produced-parent census')
        if any(not CEILING.contains(budget) for _,budget in self.resources.phase_budgets):
            raise ValueError('full factor reducer exceeds selected PURE resource ceiling')

    @property
    def protected(self):return self.scope.protected


def input_access_pair(scope):
    return produced_access(declared_access=OutcomeAccess.EVALUATION_REVEALED if scope.protected else OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.OUTCOME_VISIBLE if scope.protected else VisibilityCeiling.DEVELOPMENT_ONLY,
        parents=scope.produced_input_parents)


def config_input_parents(config,all_config_records):
    """Project one actual shared reducer's exact immutable original ancestry."""
    if type(config) not in (ScheduledFullFactorCaseConfig,ScheduledFullFactorReduceConfig):
        raise TypeError('full factor ancestry requires its exact current configuration')
    config.__post_init__()
    scope=config.scope
    scope_identity=scope.scope if type(config) is ScheduledFullFactorReduceConfig else scope
    reducer_node=key(config.protected,'reduce')+'.'+scope_identity.object_fingerprint
    index=bisect_left(all_config_records,reducer_node,key=lambda row:row[0])
    if index==len(all_config_records) or all_config_records[index][0]!=reducer_node:
        raise ValueError('full factor ancestry omits its exact complete original-roster reducer')
    reducer=all_config_records[index][1]
    if type(reducer) is not ScheduledFullFactorReduceConfig:
        raise ValueError('full factor ancestry substitutes its original-roster reducer')
    reducer.__post_init__()
    if type(config) is ScheduledFullFactorReduceConfig:
        if config!=reducer:raise ValueError('full factor ancestry substitutes the exact reducer')
    elif (config.scope!=reducer.scope.scope or config.protected!=reducer.protected
            or config.source!=_source_reference(reducer.scope,config.source.root_id)
            or config.budget!=dict(reducer.resources.phase_budgets)[config.operation]):
        raise ValueError('full factor ancestry changes its actual source, lifecycle or selected phase budget')
    return reducer.produced_input_parents


def codecs():
    kinds=(ScheduledFullFactorCaseConfig,ScheduledFullFactorReduceConfig,ScheduledFullFactorScope,ScheduledFullFactorResources,ScheduledFullFactorSourceReference,ScheduledFullFactorScopeReference,
        r.ScheduledFullFactorSource,r.ScheduledFullFactorProduct,r.ScheduledFullFactorAssessment,r.ScheduledFullFactorCensus)
    return {kind.SCHEMA:kind for kind in kinds}


def _phase(config):return 'reduce' if type(config) is ScheduledFullFactorReduceConfig else config.operation

def _units(config):return config.scope.programme.group_ids if type(config) is ScheduledFullFactorReduceConfig else (config.source.group_id,)

def _sha(config):
    # The authenticated complete Scope commits every source body. Exact member
    # equality and the full reducer census retain that join without repeating
    # every member as a separate root design operand.
    return (config.scope.scope.object_fingerprint,) if type(config) is ScheduledFullFactorReduceConfig else (config.scope.object_fingerprint,)


def _scope(context):
    prepared=context.prepared_invocation
    if type(prepared) is not PreparedInvocationContract:raise PermissionError('full factor PURE worker requires actual parent preparation')
    prepared.require_complete();prepared.validate_context(context)
    return context.run_id,context.task_id,context.input_materialization_ids,prepared.execution_plan


def _config(context,kind):
    ports=tuple(port for port in context.input_ports if port.payload_schema==kind.SCHEMA)
    if len(ports)!=1:raise ValueError('full factor worker omits or duplicates its exact canonical configuration')
    port,=ports
    raw=port.read()
    value=decode_canonical_bytes(raw,kind,maximum_bytes=port.size_bytes)
    if value.fingerprint()!=context.config.content_sha256 or value.canonical_bytes()!=raw:
        raise ValueError('full factor worker changes actual frozen configuration bytes')
    return value


def _record(context,kind,artifact_id):
    ports=tuple(port for port in context.input_ports if (port.payload_schema,port.artifact_id)==(kind.SCHEMA,artifact_id))
    if len(ports)!=1:raise ValueError('full factor worker changes an exact original/current record port')
    port,=ports
    return _record_port(port,kind)


def _record_port(port,kind):
    raw=port.read();value=decode_canonical_bytes(raw,kind,maximum_bytes=port.size_bytes)
    if value.canonical_bytes()!=raw:raise ValueError('full factor worker changes exact canonical record bytes')
    return value


def _dependency_port(context,producer,output,schema,media):
    # Scientific output names and operational publication IDs are distinct.
    # The current prepared task owns their exact mapping and producer receipt.
    task=context.prepared_invocation.execution_task_record
    edges=tuple(edge for edge in task.scientific_inputs if
        (edge.producer_task_id,edge.producer_output_id)==(producer,producer+'.'+output))
    if len(edges)!=1:raise ValueError('full factor worker loses its exact current dependency edge')
    edge,=edges
    ports=tuple(port for port in context.input_ports if port.artifact_id==edge.operational_logical_artifact_id)
    if len(ports)!=1:raise ValueError('full factor worker loses its exact current dependency port')
    port,=ports
    receipts=tuple(receipt for receipt in context.dependency_receipts if port.materialization_id in receipt.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts)!=1 or receipts[0].task_id!=producer
            or (port.payload_schema,port.media_type)!=(schema,media)
            or (edge.payload_schema,edge.media_type)!=(schema,media)):
        raise ValueError('full factor worker changes exact current dependency schema or producer receipt')
    return port


def _dependency_record(context,kind,producer):
    return _record_port(_dependency_port(context,producer,'product',kind.SCHEMA,'application/json'),kind)


def _raw(context,artifact_id):
    ports=tuple(port for port in context.input_ports if (port.payload_schema,port.artifact_id)==(MATRIX_ARRAY_SCHEMA,artifact_id))
    if len(ports)!=1:raise ValueError('full factor worker changes exact bounded original/diagnostic array input')
    return ports[0].read()


class ScheduledFullFactorWorker:
    def __init__(self,protected,phase,*,prepared_scope=None,manifest=None):
        self.protected,self.phase,self.prepared_scope=protected,phase,prepared_scope
        self.manifest=manifest or next(row.manifest() for row in operation_declarations() if row.capability_key==key(protected,phase))

    def with_prepared_scope(self,value):return type(self)(self.protected,self.phase,prepared_scope=value,manifest=self.manifest)

    def execute(self,context):
        try:
            if (self.prepared_scope!=_scope(context) or context.permissions!=self.manifest.permissions
                    or context.prepared_invocation.manifest!=self.manifest or context.prepared_invocation.native_effect
                    or not self.manifest.resource_ceiling.contains(context.resource_budget)):
                raise PermissionError('full factor worker requires exact fresh PURE invocation custody')
            kind=ScheduledFullFactorReduceConfig if self.phase=='reduce' else ScheduledFullFactorCaseConfig
            config=_config(context,kind)
            budget=dict(config.resources.phase_budgets)['reduce'] if self.phase=='reduce' else config.budget
            if config.protected!=self.protected or _phase(config)!=self.phase or context.resource_budget!=budget:
                raise ValueError('full factor worker changes selected development/revealed phase')
            outputs={port.output_id.rsplit('.',1)[-1]:port for port in context.output_ports}
            if set(outputs)!=({'product','arrays'} if self.phase=='measure' else {'product'}):
                raise ValueError('full factor worker changes exact output census')
            if self.phase=='reduce':
                selected=_record(context,ScheduledFullFactorScope,config.scope.scope.object_id)
                if scope_reference(selected)!=config.scope:raise ValueError('full factor reducer substitutes exact original scope FILE input')
                products=tuple(_dependency_record(context,r.ScheduledFullFactorProduct,node(selected,'measure',source.root_id)) for source in selected.sources)
                assessments=tuple(_dependency_record(context,r.ScheduledFullFactorAssessment,node(selected,'assess',source.root_id)) for source in selected.sources)
                product=science.census(selected.programme,selected.original_cases,selected.sources,products,assessments,
                    record_id='census.'+selected.record_id)
                payloads=(TaskOutputPayload(outputs['product'].output_id,product.canonical_bytes()),)
            else:
                source=_record(context,r.ScheduledFullFactorSource,config.source.source.object_id)
                if source.identity!=config.source.source or (source.root_id,source.group_id)!=(config.source.root_id,config.source.group_id):
                    raise ValueError('full factor worker substitutes actual case SOURCE FILE')
                native=None if source.history is None else _raw(context,array_logical(source))
                if self.phase=='measure':
                    raw,product=science.measure(source,native,artifact_id=outputs['arrays'].logical_artifact_id)
                    payloads=(TaskOutputPayload(outputs['arrays'].output_id,raw),TaskOutputPayload(outputs['product'].output_id,product.canonical_bytes()))
                else:
                    prefix=key(self.protected,'measure')+'.'+source.root_id
                    product=_dependency_record(context,r.ScheduledFullFactorProduct,prefix)
                    diagnostics=_dependency_port(context,prefix,'arrays',MATRIX_ARRAY_SCHEMA,'application/x-npz').read()
                    product=science.assess(source,product,native,diagnostics)
                    payloads=(TaskOutputPayload(outputs['product'].output_id,product.canonical_bytes()),)
            if product.SCHEMA!=outputs['product'].payload_schema:raise ValueError('full factor output changes exact canonical schema')
            return RunnerResult(tuple(sorted(payloads,key=lambda row:row.output_id)),(ReceiptCheck('full-original-factor-census',True,()),))
        finally:
            for port in context.input_ports:port.close()


def prepare_for_invocation(supplier,runner):
    callback=getattr(supplier,'prepare_full_factor_followup',None)
    if not callable(callback):raise PermissionError('full factor follow-up needs actual original run/wave custody preparation')
    return ParentPreparedTaskRunner(runner.manifest,partial(callback,runner=runner))


def development_root(scope,*,study_id):
    units=scope.programme.group_ids
    views=scope_reference(scope).numerical_view_ids if type(scope) is ScheduledFullFactorScope else scope.numerical_view_ids
    world='world.matrix-selected-e4-full-factor.'+('revealed' if scope.protected else 'development')
    question='Measure the complete original E4 full-history structural factor census without changing causal forecasts.'
    claims=tuple(ClaimSpec('claim.'+study_id+'.'+unit,world,'population.'+scope.programme.programme_id,question,
        'Complete original matched coordinates, both nested numerical views, original sectors and full lattice.',
        unit,None,EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.EVALUATION_REVEALED if scope.protected else OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.OUTCOME_VISIBLE if scope.protected else VisibilityCeiling.DEVELOPMENT_ONLY,
        'Retained structural measurement and independent finite checks only; no fresh samples or scientific admission.',
        ('actual-original-receipts-and-complete-denominators',),numerical_view_ids=views) for unit in units)
    return DevelopmentStudySpec(study_id,question,scope.programme.identity,world,WorldKind.NUMERICAL_SIMULATOR,
        units,views,claims,(scope_pin(scope),))


def expected_links(scope):
    consumer=node(scope,'reduce')
    result=[RecursiveInputLink('edge.'+consumer+'.scope',consumer,'scope',external_input_id=scope_input(scope),scientific_role='SOURCE')]
    for source in scope.sources:
        for phase in ('measure','assess'):
            consumer=node(scope,phase,source.root_id)
            result.append(RecursiveInputLink('edge.'+consumer+'.source',consumer,'source',external_input_id=source_input(source),scientific_role='SOURCE'))
            if (source.history is not None if type(source) is r.ScheduledFullFactorSource else source.arrays is not None):
                result.append(RecursiveInputLink('edge.'+consumer+'.history-arrays',consumer,'history-arrays',
                    external_input_id=array_input(source),scientific_role='HISTORY'))
            if phase=='assess':
                for name,output in (('product','product'),('diagnostics','arrays')):
                    result.append(RecursiveInputLink('edge.'+consumer+'.'+name,consumer,name,
                        producer_node_id=node(scope,'measure',source.root_id),producer_output_id=output,scientific_role='HISTORY'))
        for phase in ('measure','assess'):
            consumer=node(scope,'reduce');name=phase+'.'+source.root_id
            result.append(RecursiveInputLink('edge.'+consumer+'.'+name,consumer,name,
                producer_node_id=node(scope,phase,source.root_id),producer_output_id='product',scientific_role='HISTORY'))
    return tuple(sorted(result,key=lambda row:row.edge_id))


def _source_reference(scope,root_id):
    # ScopeReference validates the exact programme's sorted unique root roster.
    index=bisect_left(scope.sources,root_id,key=attrgetter('root_id'))
    if index==len(scope.sources) or scope.sources[index].root_id!=root_id:
        raise ValueError('full factor case lies outside the complete original source roster')
    return scope.sources[index]


def _validate_complete_root(reducer,context):
    """Check the shared graph once, before the compiler can return a plan."""
    scope=reducer.scope
    cases=tuple(row.record for row in context.config_inputs if type(row.record) is ScheduledFullFactorCaseConfig)
    sources={source.root_id:source for source in scope.sources}
    expected={(root_id,phase) for root_id in sources for phase in ('measure','assess')}
    budgets=dict(reducer.resources.phase_budgets)
    if (len(context.config_inputs)!=len(expected)+1 or len(cases)!=len(expected)
            or {(row.source.root_id,row.operation) for row in cases}!=expected
            or any(row.scope!=scope_pin(scope) or row.source!=sources.get(row.source.root_id)
                or row.budget!=budgets[row.operation] for row in cases)
            or tuple(sorted(context.links,key=lambda row:row.edge_id))!=expected_links(scope)
            or context.selected_unit_ids!=scope.programme.group_ids):
        raise ValueError('full factor graph thins original sources/groups/phases or routes future observations into another consumer')
    if scope.protected and type(context.root) is not DevelopmentStudySpec:
        root=context.root
        if (type(root) is not StudyDraft or root.system is None or root.experiment is None
                or root.development_unit_ids!=scope.programme.group_ids or root.evaluation_unit_ids
                or root.development_seed_ids or root.evaluation_seed_ids
                or scope_pin(scope) not in {row.object_identity for row in root.design_inputs}
                or any(claim.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE or claim.requested_rung is not None
                    for claim in root.experiment.claims)):
            raise ValueError('full factor revealed analysis requires its explicit complete nonpromoting prospective root')
    elif type(context.root) is not DevelopmentStudySpec or context.root!=development_root(scope,study_id=context.root.study_id):
        raise ValueError('full factor DEV root substitutes truthful original source/whole-group scope')


def scientific_root_validator(config,context):
    # RecursiveStudyDraft has sorted unique node IDs. Both compiler entry paths
    # preserve that order, and this owner's single reduce node sorts last.
    # Requiring it here also refuses a selected wave that omits the reducer.
    if not context.config_inputs or type(context.config_inputs[-1].record) is not ScheduledFullFactorReduceConfig:
        raise ValueError('full factor graph requires one complete original-roster reducer')
    reducer=context.config_inputs[-1].record;scope=reducer.scope
    phase=_phase(config)
    if type(config) is ScheduledFullFactorReduceConfig:
        if config!=reducer:raise ValueError('full factor graph changes its single original-roster reducer')
        _validate_complete_root(reducer,context)
    elif (config.scope!=scope_pin(scope) or config.source!=_source_reference(scope,config.source.root_id)
            or config.budget!=dict(reducer.resources.phase_budgets)[phase]):
        raise ValueError('full factor case substitutes its exact original source/scope/phase budget')
    # The complete two-phase roster above establishes each phase's unit census;
    # the common compiler derives selected_unit_ids from these exact records.
    if config.protected!=scope.protected or context.unit_ids!=_units(config):
        raise ValueError('full factor graph changes its actual lifecycle or whole-group unit')
    expected_node=node(scope,phase,None if phase=='reduce' else config.source.root_id)
    access=OutcomeAccess.EVALUATION_REVEALED if scope.protected else OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility=VisibilityCeiling.OUTCOME_VISIBLE if scope.protected else VisibilityCeiling.DEVELOPMENT_ONLY
    if context.node_id!=expected_node or (context.outcome_access,context.visibility_ceiling)!=(access,visibility):
        raise ValueError('full factor graph substitutes actual phase/access/node')


def lower(scope,resources,*,draft_id,campaign=None,protected_root=None):
    if type(scope) is ScheduledFullFactorScope:scope=scope_reference(scope)
    r._exact(scope,ScheduledFullFactorScopeReference);r._exact(resources,ScheduledFullFactorResources)
    if scope.protected and protected_root is not None:
        if type(protected_root) is not StudyDraft or campaign is not None:
            raise TypeError('protected full factor follow-up needs its explicit actual prospective analysis root')
        root=protected_root;campaign=root.campaign;development=None
    else:
        if protected_root is not None or campaign is None:raise ValueError('full factor exposed follow-up needs its explicit existing campaign')
        root=None;development=development_root(scope,study_id='study.full-factor.'+scope.programme.programme_id)
        if development.world_id not in campaign.world_ids or development.system.object_id not in campaign.system_ids:
            raise ValueError('full factor development scientific root differs from its explicitly selected campaign scope')
        if not {claim.claim_id for claim in development.claims}.issubset(campaign.target_claim_ids):
            raise ValueError('full factor development campaign omits selected scientific claims')
    operations=[]
    access,visibility=input_access_pair(scope)
    external=[RecursiveExternalInput(scope_input(scope),scope.scope.object_id,ScheduledFullFactorScope.SCHEMA,'application/json',scope.scope_artifact.size_bytes,access,visibility,scope.scope.object_fingerprint,'SOURCE')]
    declarations={row.capability_key:row for row in operation_declarations()}
    for source in scope.sources:
        external.append(RecursiveExternalInput(source_input(source),source.source.object_id,r.ScheduledFullFactorSource.SCHEMA,'application/json',
            source.source_artifact.size_bytes,access,visibility,source.source.object_fingerprint,'SOURCE'))
        if source.arrays is not None:
            artifact=source.arrays
            external.append(RecursiveExternalInput(array_input(source),array_logical(source),artifact.payload_schema,
                artifact.media_type,artifact.size_bytes,access,visibility,artifact.sha256,'HISTORY'))
        for phase in ('measure','assess'):
            task=node(scope,phase,source.root_id);budget=dict(resources.phase_budgets)[phase]
            config=ScheduledFullFactorCaseConfig('config.'+task,phase,scope.scope,source,budget,scope.protected)
            operations.append(RecursiveOperationSpec.from_config(node_id=task,selection=declarations[key(scope.protected,phase)].registration().selection,
                config_id=config.config_id,config=config,obligation_ids=('obligation.'+task+'.complete',),resource_budget=budget))
    task=node(scope,'reduce');config=ScheduledFullFactorReduceConfig('config.'+task,scope,resources,scope.produced_input_parents)
    operations.append(RecursiveOperationSpec.from_config(node_id=task,selection=declarations[key(scope.protected,'reduce')].registration().selection,
        config_id=config.config_id,config=config,obligation_ids=('obligation.'+task+'.complete',),resource_budget=dict(resources.phase_budgets)['reduce']))
    return RecursiveStudyDraft(draft_id,'Retain complete original E4 full-history structural measurements and independent checks.',campaign,
        (),(),(),tuple(sorted(operations,key=lambda row:row.node_id)),tuple(sorted(external,key=lambda row:row.input_id)),
        expected_links(scope),tuple(sorted(row.node_id for row in operations)),prospective_draft=root,development_study=development)


def operation_declarations():
    result=[]
    for protected in (False,True):
        for phase in ('measure','assess','reduce'):
            kind=CapabilityKind.ANALYSIS if phase=='measure' else CapabilityKind.FALSIFIER if phase=='assess' else CapabilityKind.REPORTER
            stage=(ScientificStage.SYNTHESIZE if protected else ScientificStage.DEVELOP) if phase=='measure' else ScientificStage.FALSIFY if phase=='assess' else ScientificStage.REPORT
            ports=[RecursivePortContract('scope',ScheduledFullFactorScope.SCHEMA,'application/json',None)] if phase=='reduce' else [RecursivePortContract('source',r.ScheduledFullFactorSource.SCHEMA,'application/json',None)]
            if phase!='reduce':
                ports.append(RecursivePortContract('history-arrays',MATRIX_ARRAY_SCHEMA,'application/x-npz',MAXIMUM_MATRIX_ARRAY_BYTES,minimum_count=0))
            if phase=='assess':
                ports.extend((RecursivePortContract('product',r.ScheduledFullFactorProduct.SCHEMA,'application/json',None),
                    RecursivePortContract('diagnostics',MATRIX_ARRAY_SCHEMA,'application/x-npz',MAXIMUM_MATRIX_ARRAY_BYTES)))
            if phase=='reduce':
                ports.extend(RecursivePortContract(name,record.SCHEMA,'application/json',None,minimum_count=1,maximum_count=None)
                    for name,record in (('measure',r.ScheduledFullFactorProduct),('assess',r.ScheduledFullFactorAssessment)))
            output=r.ScheduledFullFactorProduct if phase=='measure' else r.ScheduledFullFactorAssessment if phase=='assess' else r.ScheduledFullFactorCensus
            outputs=[OutputTemplate('product',output.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','.json')]
            if phase=='measure':outputs.append(OutputTemplate('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','.npz'))
            permissions=(CapabilityPermission.READ_EXTERNAL_ARTIFACTS,CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_OUTCOME_VISIBLE if protected else CapabilityPermission.READ_DEVELOPMENT)
            config=ScheduledFullFactorReduceConfig if phase=='reduce' else ScheduledFullFactorCaseConfig
            version='2.0.0' if phase=='reduce' else '1.0.0'
            result.append(RecursiveOperationDeclaration(key(protected,phase),version,key(protected,phase)+('.v2' if phase=='reduce' else '.v1'),kind,config,stage,
                tuple(sorted(ports,key=lambda row:row.port_id)),tuple(sorted(outputs,key=lambda row:row.output_id)),tuple(sorted(permissions)),EvidenceCeiling.NON_PROMOTABLE,
                OutcomeAccess.EVALUATION_REVEALED if protected else OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.OUTCOME_VISIBLE if protected else VisibilityCeiling.DEVELOPMENT_ONLY,CEILING,
                tuple(sorted(('exact-original-run-wave-reveal-custody','whole-group-full-lattice-census','independent-complete-eigenpairs','no-future-forecaster-port'))),
                partial(ScheduledFullFactorWorker,protected,phase),codecs(),
                scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=_sha,scientific_unit_ids=_units,
                    scientific_root_validator=scientific_root_validator),
                execution_properties=RecursiveExecutionProperties(runner_preparation_factory=prepare_for_invocation),storage_codecs=MATRIX_STORAGE_CODECS,
                config_input_parents=config_input_parents))
    return tuple(result)
