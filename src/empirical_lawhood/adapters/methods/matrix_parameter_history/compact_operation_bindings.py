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
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import compact_science as science
from .compact_records import (MatrixParameterCompactSource, MatrixParameterCompactHistory, MatrixParameterCompactAssessment, bind_source, identity)
from .records import MatrixParameterAllocation, MatrixParameterNativeHistory, coordinate_identity, expected_members

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

from .operation_bindings import _outputs as _outputs

NAMESPACE = 'matrix-parameter-history-compact-development'
BUDGET = ResourceBudget(1,None,0,None,None,None)
PHASES = (
    ('history',(('allocation',MatrixParameterAllocation),('coordinate',MatrixParameterCoordinate),
        ('provenance',NumericalProducingProvenance),('source',MatrixParameterCompactSource),('streams',MatrixHistorySeed)),
        MatrixParameterCompactHistory,ScientificStage.ACQUIRE),
    ('assess',(('allocation',MatrixParameterAllocation),('coordinate',MatrixParameterCoordinate),('history',MatrixParameterCompactHistory),('history-arrays',None),('provenance',NumericalProducingProvenance),('source',MatrixParameterCompactSource)),
        MatrixParameterCompactAssessment,ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-history/compact-operation-config'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    operation: str
    source: MatrixParameterCompactSource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not MatrixParameterCompactSource or self.operation not in ('history','assess')
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


def external_id(source, name):
    if name in ('allocation','provenance'):
        return 'external.shared.'+name
    if name == 'coordinate':
        return 'external.coordinate.'+source.coordinate.object_id
    return 'external.'+source.root_id+'.'+name


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
    return {t.SCHEMA:t for t in (MatrixParameterOperationConfig,MatrixParameterCompactSource,MatrixParameterAllocation,
        MatrixParameterCoordinate,MatrixHistorySeed,NumericalProducingProvenance,MatrixParameterCompactHistory,MatrixParameterCompactAssessment)}


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
    source = records[MatrixParameterCompactSource.SCHEMA]
    selected = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))
    if (config.operation != role or config.source != source or context.config.content_sha256 != config.fingerprint()
            or context.task_id != f'{NAMESPACE}.{source.root_id}.{role}' or context.permissions != selected.permissions
            or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('parameter worker substitutes exact selected source/config/resource/access')
    bound = bind_source(source,records[MatrixParameterAllocation.SCHEMA],records[MatrixParameterCoordinate.SCHEMA],records[NumericalProducingProvenance.SCHEMA])
    if role == 'history' and tuple(sorted(streams,key=lambda s:s.purpose)) != source.root.streams:
        raise ValueError('parameter worker changes actual allocation/coordinate/provenance/stream bytes')
    return config,bound,records,raw_ports




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
            history = records[MatrixParameterCompactHistory.SCHEMA]
            artifact = history.arrays.array_artifact
            port = ports[0]
            if (port.artifact_id,port.payload_schema,port.media_type,port.size_bytes) != (artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes):
                raise ValueError('parameter assessor substitutes actual ordinary raw input')
            arrays = science.retained_product(source,history.arrays,port.read())
            return _outputs(context,science.assess(source,history,arrays))
        finally:
            for port in context.input_ports:
                port.close()


def _native_definition(context, config, source, parent_contact):
    return NativeSubworkDefinition('subwork.'+source.root_id+'.paired-history','matrix-parameter-native.compact-paired-history-v2',parent_contact,
        identity(config),tuple(sorted((identity(source.source),source.source.allocation,source.source.coordinate,source.source.provenance),key=lambda x:x.object_id)),
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
            product = MatrixParameterCompactHistory('history.'+source.root_id,identity(source.source),coordinate_identity(source.coordinate),
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
        implementation_id=NAMESPACE+'.'+role+'.v2',
        kind=CapabilityKind.SIMULATOR if role=='history' else CapabilityKind.FALSIFIER,
        config_record_type=MatrixParameterOperationConfig, stage=stage,
        input_ports=tuple(sorted((RecursivePortContract(name,record.SCHEMA if record else MATRIX_ARRAY_SCHEMA,
            'application/json' if record else 'application/x-npz',None if record else MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=4 if name=='streams' else 1,maximum_count=4 if name=='streams' else 1)
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
