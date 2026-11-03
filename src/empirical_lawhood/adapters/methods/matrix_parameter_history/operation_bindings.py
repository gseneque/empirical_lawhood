"""Cold declarations and guarded development parameter-history providers.

Registration belongs to the composition owner. A factory declaration, exposed
software receipt or numerical cross-check supplies no issue/qualification.
"""

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import resource
import time
from typing import ClassVar

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_source import acquire_parameter_history
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import science
from .records import (
    MatrixParameterAllocation, MatrixParameterHistoryAssessment, MatrixParameterHistoryProduct,
    MatrixParameterHistorySource, MatrixParameterNativeHistory, coordinate_identity, expected_members, identity,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-parameter-history-development'
BUDGET = ResourceBudget(1,None,0,None,None,None)
PHASES = (
    ('history',(('allocation',MatrixParameterAllocation),('coordinate',MatrixParameterCoordinate),
        ('provenance',NumericalProducingProvenance),('source',MatrixParameterHistorySource),('streams',MatrixHistorySeed)),
        MatrixParameterHistoryProduct,ScientificStage.ACQUIRE),
    ('assess',(('history',MatrixParameterHistoryProduct),('history-arrays',None),('source',MatrixParameterHistorySource)),
        MatrixParameterHistoryAssessment,ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/operation-config'
    config_id: str
    operation: str
    source: MatrixParameterHistorySource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not MatrixParameterHistorySource or self.operation not in ('history','assess')
                or self.config_id != f'config.{NAMESPACE}.{self.source.root_id}.{self.operation}'):
            raise ValueError('parameter operation changes selected development source/root/phase')


def scientific_operand_sha256s(config):
    s = config.source
    return tuple(sorted({identity(s).object_fingerprint,identity(s.allocation).object_fingerprint,
        coordinate_identity(s.coordinate).object_fingerprint,s.provenance.identity.object_fingerprint,
        identity(s.numerical_design).object_fingerprint}))


def source_operands(source):
    return (identity(source),identity(source.allocation),coordinate_identity(source.coordinate),
        source.provenance.identity,identity(source.numerical_design))


def scientific_unit_ids(config):
    return (config.source.root.root.independent_group_id,)


def native_effect_slot_ids(config):
    return (config.source.root_id+'.paired-history',)


def development_root(sources, *, study_id):
    sources = tuple(sources)
    allocations = {identity(s.allocation) for s in sources}
    if len(allocations) != 1 or {s.root_id for s in sources} != {r.root.root_id for r in sources[0].allocation.roots}:
        raise ValueError('parameter development root must name its complete selected allocation')
    units = tuple(sorted({s.root.root.independent_group_id for s in sources}))
    world = 'world.matrix-parameter-history.exposed'
    question = 'Do complete parameter-consistent paired histories pass independently expressed native equations?'
    views = tuple(sorted({v.view_id for s in sources for v in (s.coordinate.primary_view,s.coordinate.fine_view)}))
    claims = tuple(ClaimSpec('claim.matrix-parameter-history.'+unit,world,'population.matrix-parameter-history.exposed',
        question,'Complete declared coordinate/root histories with every nested numerical state and innovation.',
        unit,None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        'No factor utility, relation, continuum error bound, freshness or qualification.',('assumption.matrix-parameter-history.exposed',),
        numerical_view_ids=views) for unit in units)
    return DevelopmentStudySpec(study_id,question,identity(sources[0].allocation),world,WorldKind.NUMERICAL_SIMULATOR,
        units,views,claims,tuple(sorted({operand for s in sources for operand in source_operands(s)},key=lambda x:x.object_id)))


def development_draft(sources, *, draft_id):
    """Lower this complete finite domain roster through ordinary authoring types.

    This pure declaration creates no execution authority or input publication.
    The API must use the actually installed catalogue before any real entry.
    """
    from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.status import LifecycleStatus
    from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
    sources = tuple(sources)
    root = development_root(sources,study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id,'owner.local-researcher','operator.local-development',(root.study_id,),
        frozenset((root.world_kind,)),frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)),('gate.local-nonactuating-development',),frozenset(),BUDGET,OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id,CampaignNodeKind.EVIDENCE_SNAPSHOT,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id,root.question,(root.system.object_id,),(root.world_id,),
        tuple(c.claim_id for c in root.claims),BUDGET,ObjectIdentity.from_record(policy.policy_id,policy),
        (DecisionRight('right.'+draft_id,AuthorityAction.SIMULATION_EXECUTION,'owner.local-researcher',policy.policy_id,False),),
        (node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)
    external,operations,links = {},[],[]
    registrations = {r.selection.capability_key:r for r in operation_registrations()}
    for source in sources:
        records = {'source':source,'allocation':source.allocation,'coordinate':source.coordinate,'provenance':source.provenance}
        for name,record in records.items():
            selected = coordinate_identity(record) if name == 'coordinate' else record.identity if name == 'provenance' else identity(record)
            input_id = 'external.'+source.root_id+'.'+name
            external[input_id] = RecursiveExternalInput(input_id,selected.object_id,record.SCHEMA,'application/json',None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,record.fingerprint(),'SOURCE')
        for s in source.root.streams:
            input_id = 'external.'+source.root_id+'.streams.'+s.purpose
            external[input_id] = RecursiveExternalInput(input_id,source.root.stream_identity(s).object_id,s.SCHEMA,'application/json',None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,s.fingerprint(),'SOURCE')
        for role,parts,_,_ in PHASES:
            node_id = f'{NAMESPACE}.{source.root_id}.{role}'
            config = MatrixParameterOperationConfig('config.'+node_id,role,source)
            operations.append(RecursiveOperationSpec.from_config(node_id=node_id,selection=registrations[NAMESPACE+'.'+role].selection,
                config_id=config.config_id,config=config,obligation_ids=('obligation.'+node_id+'.complete-scope',),resource_budget=BUDGET))
            for name,_ in parts:
                names = tuple('streams.'+s.purpose for s in source.root.streams) if name == 'streams' else (name,)
                for selected in names:
                    if selected in ('history','history-arrays'):
                        links.append(RecursiveInputLink('edge.'+node_id+'.'+selected,node_id,selected,
                            producer_node_id=f'{NAMESPACE}.{source.root_id}.history',producer_output_id='arrays' if selected.endswith('arrays') else 'product',scientific_role='HISTORY'))
                    else:
                        links.append(RecursiveInputLink('edge.'+node_id+'.'+selected,node_id,selected,
                            external_input_id='external.'+source.root_id+'.'+selected,scientific_role='SOURCE'))
    return RecursiveStudyDraft(draft_id,root.question,campaign,(),(),(),tuple(sorted(operations,key=lambda x:x.node_id)),
        tuple(sorted(external.values(),key=lambda x:x.input_id)),tuple(sorted(links,key=lambda x:x.edge_id)),
        tuple(sorted(o.node_id for o in operations)),development_study=root)


def scientific_root_validator(config, context):
    if config.operation == 'history':
        from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
        validate_parameter_ou_domain(config.source.coordinate)
    configs = tuple(i.record for i in context.config_inputs)
    if any(type(c) is not MatrixParameterOperationConfig for c in configs):
        raise ValueError('parameter history mixes foreign scientific configurations')
    allocation = config.source.allocation
    roots = {r.root.root_id for r in allocation.roots}
    if ({c.source.root_id for c in configs} != roots or len(configs) != 2*len(roots)
            or any(c.source.allocation != allocation for c in configs)
            or any({c.operation for c in configs if c.source.root_id == root} != {'history','assess'} for root in roots)):
        raise ValueError('parameter history omits allocated root/two-phase census')
    for root in roots:
        local = tuple(c for c in configs if c.source.root_id == root)
        if len({identity(c.source) for c in local}) != 1:
            raise ValueError('parameter history phases change current selected source')
    if type(context.root) is not DevelopmentStudySpec:
        raise ValueError('parameter history requires its exact exposed development root')
    history_sources = tuple(c.source for c in configs if c.operation == 'history')
    if context.root != development_root(history_sources,study_id=context.root.study_id):
        raise ValueError('parameter history changes its complete selected scientific root')
    units = tuple(sorted({r.root.independent_group_id for r in allocation.roots}))
    native = config.operation == 'history'
    if (context.root.assigned_unit_ids != units
            or {operand for c in configs for operand in source_operands(c.source)} != set(context.root.scientific_operands)
            or context.node_id != f'{NAMESPACE}.{config.source.root_id}.{config.operation}'
            or context.stage is not (ScientificStage.ACQUIRE if native else ScientificStage.FALSIFY)
            or context.unit_ids != scientific_unit_ids(config) or context.selected_unit_ids != units
            or context.complete_unit_census != native or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('parameter history changes root/source/stage/unit/access census')
    parts = next(p[1] for p in PHASES if p[0] == config.operation)
    names = {name for name,_ in parts if name != 'streams'}
    if native:
        names |= {'streams.'+s.purpose for s in config.source.root.streams}
    incoming = tuple(l for l in context.links if l.consumer_node_id == context.node_id)
    if len(incoming) != len(names) or {l.consumer_input_id for l in incoming} != names:
        raise ValueError('parameter history omits an actual ordinary source/stream/array input')
    for link in incoming:
        if link.consumer_input_id in ('history','history-arrays'):
            if (link.producer_node_id != f'{NAMESPACE}.{config.source.root_id}.history'
                    or link.producer_output_id != ('arrays' if link.consumer_input_id.endswith('arrays') else 'product')
                    or link.external_input_id is not None or link.scientific_role != 'HISTORY'):
                raise ValueError('parameter assessor changes actual producer/raw history dependency')
        elif link.external_input_id is None or link.scientific_role != 'SOURCE':
            raise ValueError('parameter native source is not an explicit ordinary scientific operand')


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {t.SCHEMA:t for t in (MatrixParameterOperationConfig,MatrixParameterHistorySource,MatrixParameterAllocation,
        MatrixParameterCoordinate,MatrixHistorySeed,NumericalProducingProvenance,MatrixParameterHistoryProduct,MatrixParameterHistoryAssessment)}


def _decode_inputs(context, role):
    inputs = next(p[1] for p in PHASES if p[0] == role)
    expected = {MatrixParameterOperationConfig.SCHEMA:MatrixParameterOperationConfig,
        **{t.SCHEMA:t for _,t in inputs if t is not None and t is not MatrixHistorySeed}}
    records, raw_ports, streams = {},[],[]
    for port in context.input_ports:
        if port.payload_schema == MatrixHistorySeed.SCHEMA and role == 'history':
            streams.append(decode_canonical_bytes(port.read(),MatrixHistorySeed,maximum_bytes=None))
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA and role == 'assess':
            raw_ports.append(port)
        elif port.payload_schema in expected and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(),expected[port.payload_schema],maximum_bytes=None)
        else:
            raise ValueError('parameter worker receives undeclared or duplicate input')
    if set(records) != set(expected) or len(raw_ports) != int(role == 'assess'):
        raise ValueError('parameter worker omits exact typed/raw operands')
    config = records[MatrixParameterOperationConfig.SCHEMA]
    source = records[MatrixParameterHistorySource.SCHEMA]
    selected = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))
    if (config.operation != role or config.source != source or context.config.content_sha256 != config.fingerprint()
            or context.task_id != f'{NAMESPACE}.{source.root_id}.{role}' or context.permissions != selected.permissions
            or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('parameter worker substitutes exact selected source/config/resource/access')
    if role == 'history' and (records[MatrixParameterAllocation.SCHEMA] != source.allocation
            or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate
            or records[NumericalProducingProvenance.SCHEMA] != source.provenance
            or tuple(sorted(streams,key=lambda s:s.purpose)) != source.root.streams):
        raise ValueError('parameter worker changes actual allocation/coordinate/provenance/stream bytes')
    return config,source,records,raw_ports


def _outputs(context, product, raw=None):
    ports = {p.output_id.rsplit('.',1)[-1]:p for p in context.output_ports}
    if set(ports) != ({'product','arrays'} if raw is not None else {'product'}) or ports['product'].payload_schema != product.SCHEMA:
        raise ValueError('parameter worker omits selected scientific output census')
    outputs = [TaskOutputPayload(ports['product'].output_id,product.canonical_bytes())]
    if raw is not None:
        if product.arrays.array_artifact.artifact_id != ports['arrays'].logical_artifact_id:
            raise ValueError('parameter arrays substitute actual ordinary output')
        outputs.append(TaskOutputPayload(ports['arrays'].output_id,raw))
    return RunnerResult(tuple(sorted(outputs,key=lambda x:x.output_id)),(ReceiptCheck('complete-parameter-history-census',True,()),))


class MatrixParameterRunner:
    """Pure assessor has no native-subwork method, including scheduler inspection."""
    def __init__(self, role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))

    def execute(self, context):
        try:
            _,source,records,ports = _decode_inputs(context,self.role)
            if self.role != 'assess':
                raise ValueError('parameter history requires its genuine selected native parent')
            history = records[MatrixParameterHistoryProduct.SCHEMA]
            artifact = history.arrays.array_artifact
            port = ports[0]
            if (port.artifact_id,port.payload_schema,port.media_type,port.size_bytes) != (artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes):
                raise ValueError('parameter assessor substitutes actual ordinary raw input')
            arrays = science.consume_arrays(source,history.arrays,port.read())
            return _outputs(context,science.assess(source,history,arrays))
        finally:
            for port in context.input_ports:
                port.close()


def _native_definition(context, config, source, parent_contact):
    return NativeSubworkDefinition('subwork.'+source.root_id+'.paired-history','matrix-parameter-native.paired-history',parent_contact,
        identity(config),tuple(sorted((identity(source),identity(source.allocation),coordinate_identity(source.coordinate),source.provenance.identity),key=lambda x:x.object_id)),
        source.provenance.code_sources_sha256,source.provenance.dependency_lock_sha256,
        tuple(sorted(p.materialization_id for p in context.input_ports)),
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams),key=lambda x:x.object_id)),
        (NativeSubworkOutput('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'),))



def native_definition(context, config, source, progress):
    """Preserve the existing receipt-reader definition projection."""
    return _native_definition(context, config, source, progress.parent_contact)


def _initial_native_work(context, config, source, expected_parent):
    """Project the same original initial child and roster for prepare and run."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    definition = _native_definition(context, config, source, expected_parent)
    roster = NativeSubworkRoster('selected.native-subwork', expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, scientific_unit_ids(config), native_effect_slot_ids(config),
        (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixParameterNativeRunner or runner.role != 'history':
        raise ValueError('parameter history preparation requires its installed original native phase')
    config, source, _, _ = _decode_inputs(context, 'history')
    return _initial_native_work(context, config, source, expected_parent)


def _retained_values(source, raw):
    """Read receipt-only bytes through the shared codec, then validate science."""
    from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays
    arrays = decode_native_matrix_arrays(raw, expected_members(source.coordinate))
    science.validate_arrays(source, arrays)
    return arrays



class MatrixParameterNativeRunner(MatrixParameterRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config,source,_,_ = _decode_inputs(context,'history')
            work = _initial_native_work(context, config, source, native_subwork.parent_contact)
            definition, = work.definitions
            # Read existing custody before requesting any creator-only action.
            # Persisted contacts do not restore live roster/BEGIN authority.
            completed = native_subwork.recover(definition)
            if completed is not None:
                if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None
                        or completed.completion.operational_status is not OperationalStatus.SUCCEEDED or completed.receipt is None):
                    raise ValueError('retained parameter child is not a known successful completion')
                raw = b''.join(native_subwork.iter_completed_output(definition,'arrays'))
                arrays = _retained_values(source,raw)
            else:
                observed = native_subwork.inspect(definition)
                if observed.state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('uncertain or failed parameter native contact cannot be repeated')
                from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
                validate_parameter_ou_domain(source.coordinate)
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                cpu,wall = time.process_time(),time.monotonic()
                try:
                    arrays = invoke_native_subwork(native_subwork, entry,
                        acquire_parameter_history, source.coordinate, source.root.streams)
                except (ArithmeticError,MemoryError,ValueError):
                    native_subwork.complete(entry,operational_status=OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),None),
                        cost_scope='parameter native paired history nested inside complete ordinary task',unknown_streams=definition.streams,
                        reason_codes=('matrix-parameter-native-failure',))
                    raise
                raw,_ = science.array_product(source,arrays,artifact_id='array.'+definition.subwork_id)
                native_subwork.publish_output(entry,'arrays',(raw,),maximum_bytes=len(raw),maximum_chunk_bytes=len(raw),
                    expected_size_bytes=len(raw),expected_physical_sha256=sha256(raw).hexdigest())
                consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams
                    if s.purpose.startswith('preparation') or source.coordinate.autonomous_ticks),key=lambda x:x.object_id))
                completed = native_subwork.complete(entry,operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),Decimal(len(raw))),
                    cost_scope='parameter native paired history nested inside complete ordinary task',consumed_streams=consumed,
                    unconsumed_streams=tuple(s for s in definition.streams if s not in consumed),
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            _,operand = science.array_product(source,arrays,artifact_id=output.logical_artifact_id,raw=raw)
            root = source.root.root
            product = MatrixParameterHistoryProduct('history.'+source.root_id,identity(source),coordinate_identity(source.coordinate),
                root.root_id,root.independent_group_id,root.clock_id,operand,MatrixParameterNativeHistory(definition,completed.completion,completed.receipt),
                source.coordinate.total_ticks,2*source.coordinate.total_ticks)
            product.validate_source(source)
            return _outputs(context,product,raw)
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    factories = []
    for declaration in operation_declarations():
        selected = declaration.manifest()
        role = selected.capability_key.rsplit('.',1)[-1]
        _,parts = bundle(role,ExtensionContributionKind.METHOD,selected,(),None,namespace=NAMESPACE,maximum_config_bytes=None)
        factories.append(declaration.provider_factory(components=tuple(sorted(parts,key=lambda value:value.registration_id))))
    return tuple(factories)


def operation_declarations():
    """Own each native/scientific contract and derive all installed projections."""
    return tuple(RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.0.0',
        implementation_id=NAMESPACE+'.'+role+'.v1',
        kind=CapabilityKind.SIMULATOR if role=='history' else CapabilityKind.FALSIFIER,
        config_record_type=MatrixParameterOperationConfig, stage=stage,
        input_ports=tuple(sorted((RecursivePortContract(name,record.SCHEMA if record else MATRIX_ARRAY_SCHEMA,
            'application/json' if record else 'application/x-npz',None if record else MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=4 if name=='streams' else 1,maximum_count=None if name=='streams' else 1)
            for name,record in inputs),key=lambda value:value.port_id)),
        outputs=tuple(sorted((OutputTemplate('product',output.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','.json'),
            *((OutputTemplate('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','.npz'),)
              if role=='history' else ())),key=lambda value:value.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=tuple(sorted(('full-parameter-native-equations',
            'complete-state-noise-clock-census','original-receipt-nonreplay'))),
        runner_factory=lambda phase=role:MatrixParameterNativeRunner(phase) if phase=='history' else MatrixParameterRunner(phase),
        record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids,native_effect_slot_ids=native_effect_slot_ids if role=='history' else None,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=role=='history',complete_unit_census=role=='history',
            native_work_preparer=prepare_native_work if role=='history' else None),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=identity),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),storage_codecs=MATRIX_STORAGE_CODECS)
        for role,inputs,output,stage in PHASES)
