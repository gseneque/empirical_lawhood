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
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.adapters.methods.matrix_array_chunks import FRAMED_ARRAY_SCHEMA, framed_artifact, iter_framed_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
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

from . import chunked_science as science
from .chunked_records import (MatrixParameterChunkedSource, MatrixParameterChunkedHistory, MatrixParameterChunkedAssessment,
    MatrixParameterHistoryCarrier, MatrixParameterSegmentCheckpoint, CompletedParameterCarrier, CompletedParameterSegment, bind_source, identity, segment_plan)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import OPERATION_ID, acquire_parameter_segment, validate_segment_entry
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from .records import MatrixParameterAllocation, coordinate_identity
from .chunked_control_records import MatrixParameterChunkedAssessmentReport

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

from .compact_operation_bindings import external_id as external_id

NAMESPACE = 'matrix-parameter-history-chunked-development'
BUDGET = ResourceBudget(1,None,0,None,None,None)
PHASES = (
    ('history',(('allocation',MatrixParameterAllocation),('coordinate',MatrixParameterCoordinate),
        ('provenance',NumericalProducingProvenance),('source',MatrixParameterChunkedSource),('streams',MatrixHistorySeed)),
        MatrixParameterChunkedHistory,ScientificStage.ACQUIRE),
    ('assess',(('allocation',MatrixParameterAllocation),('coordinate',MatrixParameterCoordinate),('history',MatrixParameterChunkedHistory),('history-arrays',None),('provenance',NumericalProducingProvenance),('source',MatrixParameterChunkedSource)),
        MatrixParameterChunkedAssessmentReport,ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/chunked-operation-config'
    VERSION: ClassVar[str] = '3.0.0'
    config_id: str
    operation: str
    source: MatrixParameterChunkedSource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not MatrixParameterChunkedSource or self.operation not in ('history','assess')
                or self.config_id != f'config.{NAMESPACE}.{self.source.root_id}.{self.operation}'):
            raise ValueError('parameter operation changes selected development source/root/phase')


def source_operands(source):
    return (identity(source),source.allocation,source.coordinate,source.provenance,identity(source.numerical_design))


def scientific_operand_sha256s(config):
    return tuple(sorted({o.object_fingerprint for o in source_operands(config.source)}))


def scientific_unit_ids(config):
    return (config.source.root.root.independent_group_id,)


def native_effect_slot_ids(config):
    return (config.source.root_id+'.paired-history',)


def development_root(sources, *, study_id):
    from .development_draft_lowering import development_root as derive_root
    return derive_root(sources, study_id=study_id, source_operands=source_operands)


def development_draft(sources, allocation, provenance, *, draft_id):
    from .development_draft_lowering import HistoryDraftContract, development_draft as lower_draft
    return lower_draft(sources, allocation, provenance, draft_id=draft_id,
        contract=HistoryDraftContract(NAMESPACE, BUDGET, PHASES, identity, coordinate_identity,
            development_root, operation_registrations, external_id, MatrixParameterOperationConfig))




def scientific_root_validator(config, context):
    from .development_draft_lowering import HistoryDraftContract, validate_history_root
    return validate_history_root(config, context,
        contract=HistoryDraftContract(NAMESPACE, BUDGET, PHASES, identity, coordinate_identity,
            development_root, operation_registrations, external_id, MatrixParameterOperationConfig),
        scientific_unit_ids=scientific_unit_ids)


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {t.SCHEMA:t for t in (MatrixParameterOperationConfig,MatrixParameterChunkedSource,MatrixParameterAllocation,
        MatrixParameterCoordinate,MatrixHistorySeed,NumericalProducingProvenance,MatrixParameterChunkedHistory,MatrixParameterChunkedAssessment,MatrixParameterChunkedAssessmentReport)}


def _decode_inputs(context, role):
    inputs = next(p[1] for p in PHASES if p[0] == role)
    expected = {MatrixParameterOperationConfig.SCHEMA:MatrixParameterOperationConfig,
        **{t.SCHEMA:t for _,t in inputs if t is not None and t is not MatrixHistorySeed}}
    records, raw_ports, streams = {},[],[]
    for port in context.input_ports:
        if port.payload_schema == MatrixHistorySeed.SCHEMA and role == 'history':
            streams.append(decode_canonical_bytes(port.read(),MatrixHistorySeed,maximum_bytes=None))
        elif port.payload_schema == FRAMED_ARRAY_SCHEMA and role == 'assess':
            raw_ports.append(port)
        elif port.payload_schema in expected and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(),expected[port.payload_schema],maximum_bytes=None)
        else:
            raise ValueError('parameter worker receives undeclared or duplicate input')
    if set(records) != set(expected) or len(raw_ports) != int(role == 'assess'):
        raise ValueError('parameter worker omits exact typed/raw operands')
    config = records[MatrixParameterOperationConfig.SCHEMA]
    source = records[MatrixParameterChunkedSource.SCHEMA]
    selected = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))
    if (config.operation != role or config.source != source or context.config.content_sha256 != config.fingerprint()
            or context.task_id != f'{NAMESPACE}.{source.root_id}.{role}' or context.permissions != selected.permissions
            or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('parameter worker substitutes exact selected source/config/resource/access')
    bound = bind_source(source,records[MatrixParameterAllocation.SCHEMA],records[MatrixParameterCoordinate.SCHEMA],records[NumericalProducingProvenance.SCHEMA])
    if role == 'history' and tuple(sorted(streams,key=lambda s:s.purpose)) != source.root.streams:
        raise ValueError('parameter worker changes actual allocation/coordinate/provenance/stream bytes')
    return config,bound,records,raw_ports


def _outputs(context, product, stream=None):
    ports = {p.output_id.rsplit('.',1)[-1]:p for p in context.output_ports}
    if set(ports) != ({'product','arrays'} if stream is not None else {'product'}) or ports['product'].payload_schema != product.SCHEMA:
        raise ValueError('chunked parameter worker omits exact scientific output census')
    outputs = [TaskOutputPayload(ports['product'].output_id,product.canonical_bytes())]
    if stream is not None:
        if product.container.artifact_id != ports['arrays'].logical_artifact_id:
            raise ValueError('chunked ordinary container changes actual output identity')
        from empirical_lawhood.runtime.execution import StreamedTaskOutput
        outputs.append(StreamedTaskOutput(ports['arrays'].output_id,product.container.size_bytes,product.container.sha256,stream))
    return RunnerResult(tuple(sorted(outputs,key=lambda x:x.output_id)),(ReceiptCheck('complete-chunked-parameter-census',True,()),))


class MatrixParameterRunner:
    def __init__(self,role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))

    def execute(self,context):
        raise ValueError('complete chunked control evidence requires the streaming output coordinator')

    def execute_streaming(self,context,emitter):
        try:
            _,bound,records,ports = _decode_inputs(context,self.role)
            if self.role != 'assess':
                raise ValueError('chunked histories require their genuine selected native parent')
            history = records[MatrixParameterChunkedHistory.SCHEMA]
            artifact,port = history.container,ports[0]
            if (port.artifact_id,port.payload_schema,port.media_type,port.size_bytes) != (artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes):
                raise ValueError('chunked assessor substitutes actual ordinary container')
            outputs = {p.output_id.rsplit('.',1)[-1]:p for p in context.output_ports}
            if set(outputs) != {'product','control-arrays'}:
                raise ValueError('complete streamed assessment requires product and exact control-array output')
            control = outputs['control-arrays']
            if (control.payload_schema,control.profile,control.media_type) != (FRAMED_ARRAY_SCHEMA,ArtifactProfile.RAW_SOURCE_BYTES,'application/octet-stream'):
                raise ValueError('complete control evidence changes selected bounded framed output')
            report = science.assess_framed(bound,history,port.read,
                emit_control=lambda raw:emitter.write(control.output_id,raw),control_artifact_id=control.logical_artifact_id)
            emitter.write(outputs['product'].output_id,report.canonical_bytes())
            return (ReceiptCheck('complete-streamed-parameter-controls',True,()),)
        finally:
            for port in context.input_ports:
                port.close()




def _native_definition(context,config,bound,parent_contact):
    return NativeSubworkDefinition('subwork.'+bound.root_id+'.chunked-history-carrier','matrix-parameter-history.no-rng-carrier-v1',
        parent_contact,identity(config),tuple(sorted((identity(bound.source),bound.source.allocation,bound.source.coordinate,bound.source.provenance),key=lambda i:i.object_id)),
        bound.provenance.code_sources_sha256,bound.provenance.dependency_lock_sha256,
        tuple(sorted(p.materialization_id for p in context.input_ports)),
        tuple(sorted((bound.root.stream_identity(t) for t in bound.root.streams),key=lambda i:i.object_id)),
        (NativeSubworkOutput('completion',MatrixParameterHistoryCarrier.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),))



def carrier_definition(context, config, bound, progress):
    """Preserve the existing receipt-reader definition projection."""
    return _native_definition(context, config, bound, progress.parent_contact)


def _initial_native_work(context, config, bound, expected_parent):
    """Project the same original initial child and roster for prepare and run."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    definition = _native_definition(context, config, bound, expected_parent)
    roster = NativeSubworkRoster('selected.native-subwork', expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, scientific_unit_ids(config), native_effect_slot_ids(config),
        (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixParameterNativeRunner or runner.role != 'history':
        raise ValueError('parameter history preparation requires its installed original native phase')
    config, source, _, _ = _decode_inputs(context, 'history')
    return _initial_native_work(context, config, source, expected_parent)


def segment_definition(base,index,previous):
    extra = () if previous is None else tuple(previous[1].outputs)
    sources = base.sources if previous is None else tuple(sorted((*base.sources,identity(previous[0].checkpoint)),key=lambda i:i.object_id))
    return NativeSubworkDefinition(base.subwork_id+'.segment.'+f'{index:08d}',OPERATION_ID,base.parent_contact,base.configuration,sources,
        base.code_sources_sha256,base.dependency_lock_sha256,
        tuple(sorted((*base.input_materialization_ids,*(m.materialization.materialization_id for m in extra)))),base.streams,
        (NativeSubworkOutput('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'),
         NativeSubworkOutput('checkpoint',MatrixParameterSegmentCheckpoint.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),
         NativeSubworkOutput('terminal',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz')),
        roster_id='conditional.parameter-segment.'+f'{index:08d}')


def _published(native,entry,name,raw):
    bound = min(1024**2,len(raw))
    chunks = (raw[start:start+bound] for start in range(0,len(raw),bound))
    return native.publish_output(entry,name,chunks,maximum_bytes=len(raw),maximum_chunk_bytes=bound,
        expected_size_bytes=len(raw),expected_physical_sha256=sha256(raw).hexdigest())


def _output_artifact_id(definition,name):
    # The existing native custody owner declares this exact public convention.
    key = sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
    return 'native-subwork.'+key+'.output.'+name


def _recover_segment(native,definition):
    retained = native.recover(definition)
    if retained is None or retained.state is not NativeSubworkState.COMPLETED or retained.completion.operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('completed carrier lacks exact successful segment custody')
    raw = b''.join(native.iter_completed_output(definition,'checkpoint'))
    checkpoint = decode_canonical_bytes(raw,MatrixParameterSegmentCheckpoint,maximum_bytes=None)
    return CompletedParameterSegment(checkpoint.science_arrays,checkpoint,definition,retained.completion,retained.receipt),retained


class _ContainerSource:
    def __init__(self,manifest,native,segments):
        self.manifest,self.native,self.segments = manifest,native,segments
        self.by_id = {chunk.array_artifact.artifact_id:(segment.definition,name) for segment in segments
            for name,chunk in (('arrays',segment.arrays),('terminal',segment.checkpoint.terminal_arrays))}
    def iter_fetch(self,artifact):
        definition,name = self.by_id[artifact.artifact_id]
        return self.native.iter_completed_output(definition,name)
    def fetch(self,artifact):
        return b''.join(self.iter_fetch(artifact))
    def chunks(self,maximum_chunk_bytes):
        return iter_framed_bytes(self.manifest,self.iter_fetch,maximum_chunk_bytes=maximum_chunk_bytes)
    def close(self):
        pass


class MatrixParameterNativeRunner(MatrixParameterRunner):
    def execute_with_native_subwork(self,context,native_subwork,progress=None):
        try:
            config,bound,_,_ = _decode_inputs(context,'history')
            work = _initial_native_work(context, config, bound, native_subwork.parent_contact)
            base, = work.definitions
            retained = native_subwork.recover(base)
            segments = []
            if retained is not None:
                if retained.completion.operational_status is not OperationalStatus.SUCCEEDED:
                    raise ValueError('negative carrier cannot authorize a replay')
                raw = b''.join(native_subwork.iter_completed_output(base,'completion'))
                summary = decode_canonical_bytes(raw,MatrixParameterHistoryCarrier,maximum_bytes=None)
                for selected in summary.segment_definitions:
                    definition = native_subwork.resolve_completed_definition(selected)
                    segment,_ = _recover_segment(native_subwork,definition)
                    segments.append(segment)
                carrier = CompletedParameterCarrier(summary,base,retained.completion,retained.receipt)
            else:
                if native_subwork.inspect(base).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('uncertain carrier cannot restart segmented history')
                bind_source(bound.source,bound.allocation,bound.coordinate,bound.provenance,new_entry=True)
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                carrier_entry = native_subwork.begin(base)
                native_subwork.contact(carrier_entry)
                carrier_cpu,carrier_wall = time.process_time(),time.monotonic()
                child_cpu = child_wall = Decimal(0)
                previous = None
                try:
                    for index,(start,stop) in enumerate(segment_plan(bound)):
                        definition = segment_definition(base,index,previous)
                        native_subwork.freeze_roster(NativeSubworkRoster(definition.roster_id,native_subwork.parent_contact,
                            (definition.identity,),base.identity),parent_entry=carrier_entry,definitions=(definition,))
                        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                            raise ValueError('conditional segment already contacted; no automatic replay')
                        terminal = generator_states = None
                        if previous is not None:
                            selected = previous[0].checkpoint.terminal_arrays
                            raw = b''.join(native_subwork.iter_completed_output(previous[0].definition,'terminal'))
                            terminal = {name.removeprefix('terminal_'):value for name,value in decode_matrix_arrays(raw,selected).items()}
                            generator_states = previous[0].checkpoint.generators
                        validate_segment_entry(bound.coordinate,bound.root.streams,start,stop,terminal=terminal,generator_states=generator_states)
                        inputs = None if progress is None else tuple(sorted((*progress,*(previous[1].outputs if previous else ())),key=lambda m:m.materialization.materialization_id))
                        entry = native_subwork.begin(definition,inputs)
                        native_subwork.contact(entry)
                        cpu,wall = time.process_time(),time.monotonic()
                        try:
                            values = invoke_native_subwork(native_subwork, entry, acquire_parameter_segment,
                                bound.coordinate, bound.root.streams, start, stop,
                                terminal=terminal, generator_states=generator_states)
                        except (ArithmeticError,MemoryError,ValueError):
                            if native_subwork.inspect(definition).state is not NativeSubworkState.COMPLETED:
                                native_subwork.complete(entry,operational_status=OperationalStatus.FAILED,
                                    cost=InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),None),
                                    cost_scope='failed paired segment; exact earlier completions retained',unknown_streams=definition.streams,
                                    reason_codes=('parameter-segment-native-failure',))
                            raise
                        science_raw,science_chunk,terminal_raw,checkpoint = science.package_segment(bound,values,definition,None if previous is None else previous[0],
                            science_artifact_id=_output_artifact_id(definition,'arrays'),terminal_artifact_id=_output_artifact_id(definition,'terminal'))
                        _published(native_subwork,entry,'arrays',science_raw)
                        _published(native_subwork,entry,'terminal',terminal_raw)
                        _published(native_subwork,entry,'checkpoint',checkpoint.canonical_bytes())
                        consumed = tuple(sorted((bound.root.stream_identity(t) for t in bound.root.streams
                            if (t.purpose.startswith('preparation') and start < bound.coordinate.ramp_ticks)
                            or (t.purpose.startswith('autonomous') and stop > bound.coordinate.ramp_ticks)),key=lambda i:i.object_id))
                        cost = InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),Decimal(len(science_raw)+len(terminal_raw)+len(checkpoint.canonical_bytes())))
                        completed = native_subwork.complete(entry,operational_status=OperationalStatus.SUCCEEDED,cost=cost,
                            cost_scope='one exact paired history segment including typed encoding and publication',consumed_streams=consumed,
                            unconsumed_streams=tuple(t for t in definition.streams if t not in consumed),
                            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
                        segment = CompletedParameterSegment(science_chunk,checkpoint,definition,completed.completion,completed.receipt)
                        segment.validate_source(bound,None if previous is None else previous[0])
                        segments.append(segment);previous = segment,completed
                        child_cpu += cost.cpu_seconds;child_wall += cost.wall_seconds
                        del values,science_raw,terminal_raw
                    summary = MatrixParameterHistoryCarrier('carrier.'+bound.root_id,identity(bound.source),tuple(s.definition.identity for s in segments),
                        bound.coordinate.total_ticks,2*bound.coordinate.total_ticks)
                    summary_raw = summary.canonical_bytes();_published(native_subwork,carrier_entry,'completion',summary_raw)
                    cpu = max(Decimal(0),Decimal(str(time.process_time()-carrier_cpu))-child_cpu)
                    wall = max(Decimal(0),Decimal(str(time.monotonic()-carrier_wall))-child_wall)
                    completed = native_subwork.complete(carrier_entry,operational_status=OperationalStatus.SUCCEEDED,
                        cost=InquiryCost(cpu,wall,Decimal(len(summary_raw))),cost_scope='no-RNG carrier coordination; completed child CPU/wall excluded',
                        unconsumed_streams=base.streams,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
                    carrier = CompletedParameterCarrier(summary,base,completed.completion,completed.receipt)
                except (ArithmeticError,MemoryError,ValueError):
                    if native_subwork.inspect(base).state is not NativeSubworkState.COMPLETED:
                        native_subwork.complete(carrier_entry,operational_status=OperationalStatus.FAILED,
                            cost=InquiryCost(max(Decimal(0),Decimal(str(time.process_time()-carrier_cpu))-child_cpu),
                                max(Decimal(0),Decimal(str(time.monotonic()-carrier_wall))-child_wall),None),
                            cost_scope='negative no-RNG carrier; completed segments remain individually recoverable',
                            unconsumed_streams=base.streams,reason_codes=('parameter-segment-carrier-failure',))
                    raise
            stream = _ContainerSource(None,native_subwork,tuple(segments))
            manifest = science.complete_manifest(bound,tuple(segments),stream.fetch)
            stream.manifest = manifest
            output = next(p for p in context.output_ports if p.payload_schema == FRAMED_ARRAY_SCHEMA)
            container = framed_artifact(manifest,stream.iter_fetch,artifact_id=output.logical_artifact_id)
            product = MatrixParameterChunkedHistory('history.'+bound.root_id,identity(bound.source),bound.root_id,
                bound.root.root.independent_group_id,bound.coordinate.clock_id,manifest,container,tuple(segments),carrier)
            product.validate_source(bound)
            return _outputs(context,product,stream)
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
        implementation_id=NAMESPACE+'.'+role+('.v3' if role=='history' else '.v4'),
        kind=CapabilityKind.SIMULATOR if role=='history' else CapabilityKind.FALSIFIER,
        config_record_type=MatrixParameterOperationConfig, stage=stage,
        input_ports=tuple(sorted((RecursivePortContract(name,record.SCHEMA if record else FRAMED_ARRAY_SCHEMA,
            'application/json' if record else 'application/octet-stream',None if record else None,
            minimum_count=4 if name=='streams' else 1,maximum_count=4 if name=='streams' else 1)
            for name,record in inputs),key=lambda value:value.port_id)),
        outputs=tuple(sorted((OutputTemplate('product',output.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','.json'),
            OutputTemplate('arrays' if role=='history' else 'control-arrays',FRAMED_ARRAY_SCHEMA,
                ArtifactProfile.RAW_SOURCE_BYTES,'application/octet-stream','.bin')),key=lambda value:value.output_id)),
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
