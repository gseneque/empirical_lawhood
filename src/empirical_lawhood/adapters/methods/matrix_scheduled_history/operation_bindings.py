# SPDX-License-Identifier: MPL-2.0
"""Stock operation ports for pre-future scheduled prefixes and exact continuation.

Discovery creates no qualification or authority. The scientific root validator
and original-publication hook run before authoring; stock issued execution owns
ordinary contact and native-subwork authorization. This raw-history route is
distinct from the scheduled pulse-response/error consumer.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from hashlib import sha256
from dataclasses import dataclass, field

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursivePortContract, RegisteredPublicationRequirement,
)

from . import science
from .parameter_native import execute_parameter_native_work
from .commitment import COMMIT_KEY, ScheduledCommitment, ScheduledCommitmentConfig, ScheduledCommitter, ScheduledExposureAudit, committed, require_publication_copy
from .continuation import ScheduledFullAssessment, ScheduledFullHistory, full_access, full_visibility
from .forecast import ScheduledCalibratedForecastConfig, ScheduledCalibration, ScheduledForecastConfig, ScheduledForecastDesign, ScheduledForecastFeature, ScheduledForecastSeal, causal_feature, forecast_public
from .response_selection import ScheduledResponseSelection
from .response_records import ScheduledResponseForecast
from .records import (
    NAMESPACE, ScheduledAllocation, ScheduledCausalPrefix, ScheduledCheckpoint, ScheduledConfig,
    ScheduledFrameAssessment, ScheduledNativeEvidence, ScheduledNumericalAssessment, ScheduledPrefixHistory,
    ScheduledPrefixWitness, ScheduledSelection, ScheduledSource, identity,
)
from .source_index import ResolvedScheduledSource, ScheduledNativeSourceContext, ScheduledSourceIndex

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

BUDGET = ResourceBudget(1, None, 0, None, None, None)
BLIND = OutcomeAccess.OUTCOME_BLIND
PROSPECTIVE = VisibilityCeiling.PROSPECTIVE
PREFIX_INPUTS = (('allocation', ScheduledAllocation), ('commitment', ScheduledCommitment), ('commitment-config', ScheduledCommitmentConfig),
    ('coordinate', MatrixParameterCoordinate), ('provenance', NumericalProducingProvenance),
    ('selection', ScheduledSelection), ('source', ScheduledSource), ('streams', MatrixHistorySeed))
HISTORY_INPUTS = (('history', ScheduledPrefixHistory), ('history-arrays', None), ('source', ScheduledSource),
    ('commitment-config', ScheduledCommitmentConfig))
CONTINUE_INPUTS = (('allocation', ScheduledAllocation), ('causal', ScheduledCausalPrefix), ('checkpoint', ScheduledCheckpoint),
    ('commitment', ScheduledCommitment), ('commitment-config', ScheduledCommitmentConfig), ('coordinate', MatrixParameterCoordinate), ('forecast', ScheduledForecastSeal),
    ('history', ScheduledPrefixHistory), ('history-arrays', None), ('physical-forecast', ScheduledResponseForecast), ('provenance', NumericalProducingProvenance),
    ('selection', ScheduledSelection), ('source', ScheduledSource), ('streams', MatrixHistorySeed))
# A predictor gets no ScheduledSource/allocation/checkpoint/streams/history port.
PHASES = (
    ('prefix', PREFIX_INPUTS, ScheduledPrefixHistory, ScientificStage.ACQUIRE, True),
    ('numerical', HISTORY_INPUTS, ScheduledNumericalAssessment, ScientificStage.FALSIFY, False),
    ('measure', (*HISTORY_INPUTS[:2], ('numerical', ScheduledNumericalAssessment), *HISTORY_INPUTS[2:]), ScheduledPrefixWitness, ScientificStage.TRANSFORM, True),
    ('check', (*HISTORY_INPUTS[:2], ('measure', ScheduledPrefixWitness), ('measure-arrays', None),
        ('numerical', ScheduledNumericalAssessment), *HISTORY_INPUTS[2:]), ScheduledFrameAssessment, ScientificStage.FALSIFY, False),
    ('project', (('check', ScheduledFrameAssessment), ('forecast-design', ScheduledForecastDesign), *HISTORY_INPUTS[:2],
        ('measure', ScheduledPrefixWitness), ('measure-arrays', None), ('numerical', ScheduledNumericalAssessment), *HISTORY_INPUTS[2:]),
        ScheduledCausalPrefix, ScientificStage.TRANSFORM, True),
    ('forecast', (('causal', ScheduledCausalPrefix), ('causal-arrays', None), ('feature', ScheduledForecastFeature)),
        ScheduledForecastSeal, ScientificStage.FREEZE, False),
    ('forecast-calibrated', (('calibration', ScheduledCalibration), ('causal', ScheduledCausalPrefix), ('causal-arrays', None), ('feature', ScheduledForecastFeature)),
        ScheduledForecastSeal, ScientificStage.FREEZE, False),
    ('continue', CONTINUE_INPUTS, ScheduledFullHistory, ScientificStage.ACQUIRE, True),
    ('full-numerical', (('continue', ScheduledFullHistory), ('continue-arrays', None), ('source', ScheduledSource), ('commitment-config', ScheduledCommitmentConfig)),
        ScheduledFullAssessment, ScientificStage.FALSIFY, False),
    ('continue-development', CONTINUE_INPUTS, ScheduledFullHistory, ScientificStage.ACQUIRE, True),
    ('full-numerical-development', (('continue-development', ScheduledFullHistory), ('continue-development-arrays', None), ('source', ScheduledSource), ('commitment-config', ScheduledCommitmentConfig)),
        ScheduledFullAssessment, ScientificStage.FALSIFY, False),
    ('commit', (('allocation', ScheduledAllocation), ('audit', ScheduledExposureAudit), ('forecast-design', ScheduledForecastDesign),
        ('criterion', MatrixResponseFrontierProtocol), ('model', MatrixResponseErrorModel),
        ('prior-census', MatrixFactorExposureCensus), ('prior-coordinates', MatrixParameterCoordinate),
        ('response-selection', ScheduledResponseSelection), ('selection', ScheduledSelection), ('source', ScheduledSource), ('training', MatrixResponseErrorPredictionSpec)), ScheduledCommitment, ScientificStage.FREEZE, False),
)


@dataclass(frozen=True, slots=True)
class BoundScheduledConfig:
    """Actual canonical operation with one explicit operation-local source view."""
    record: object
    source: ResolvedScheduledSource
    shared: object
    native_context: ScheduledNativeSourceContext = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'native_context', ScheduledNativeSourceContext(self.source, self.record, self.shared))

    @property
    def config_id(self): return self.record.config_id
    @property
    def operation(self): return self.record.operation
    @property
    def root_id(self): return self.source.root_id
    @property
    def SCHEMA(self): return self.record.SCHEMA
    @property
    def VERSION(self): return self.record.VERSION
    @property
    def selection(self): return self.shared.response_selection
    def fingerprint(self): return self.record.fingerprint()
    def canonical_bytes(self): return self.record.canonical_bytes()


def require_shared_config(shared, port, *, expected=None):
    """Authenticate the actual external shared operand before one index build."""
    if (type(shared) is not ScheduledCommitmentConfig or port.kind is not WorkerInputKind.EXTERNAL
            or (port.artifact_id, port.payload_schema, port.media_type, port.outcome_access, port.visibility_ceiling) !=
               (shared.config_id, shared.SCHEMA, 'application/json', BLIND, PROSPECTIVE)
            or len(shared.canonical_bytes()) != port.size_bytes
            or expected is not None and identity(shared) != expected):
        raise ValueError('scheduled consumer substitutes its exact blind external shared commitment configuration')
    index = ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)
    index.require_roster(shared.sources, expected_root_ids=index.root_ids)
    return index


def require_current_commitment(commitment, shared):
    """The received freeze must bind the actual complete shared configuration."""
    if (type(shared) is not ScheduledCommitmentConfig or type(commitment) is not ScheduledCommitment
            or commitment != committed(shared)):
        raise ValueError('scheduled freeze differs from the actual complete shared commitment configuration')


def phase_access(role):
    if role in ('responses', 'response-score', 'responses-development', 'response-score-development', 'physical-forecast'):
        from .response_bindings import access
        return access(role)
    if role in ('calibrate', 'calibration-qualify'):
        from .calibration_bindings import access
        return access(role)
    return OutcomeAccess.DEVELOPMENT_VISIBLE if role.endswith('-development') else OutcomeAccess.EVALUATION_SEALED if role in ('continue', 'full-numerical', 'forecast-calibrated') else BLIND


def phase_visibility(role):
    if role == 'calibration-qualify':
        return VisibilityCeiling.OUTCOME_VISIBLE
    return VisibilityCeiling.DEVELOPMENT_ONLY if role.endswith('-development') else PROSPECTIVE


def config_type(role):
    return ScheduledCommitmentConfig if role == 'commit' else ScheduledCalibratedForecastConfig if role == 'forecast-calibrated' else ScheduledForecastConfig if role == 'forecast' else ScheduledConfig


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def source_operands(source):
    if type(source) is ScheduledSource:
        return tuple(sorted((source.identity, source.allocation, source.reservation, source.specification,
            source.selection, source.coordinate, source.provenance), key=lambda value: value.object_id))
    return tuple(sorted((identity(source), identity(source.allocation), identity(source.reservation), identity(source.specification),
        identity(source.specification.selection), identity(source.policy), identity(source.policy.factor_rule),
        identity(source.numerical_design), coordinate_identity(source.coordinate), source.provenance.identity), key=lambda o: o.object_id))


def units(config):
    return tuple(sorted({s.root.root.independent_group_id for s in config.sources if s.root_id in config.selected_root_ids})) if type(config) is ScheduledCommitmentConfig else (config.public_source.root.independent_group_id,) if type(config) in (ScheduledForecastConfig, ScheduledCalibratedForecastConfig) else (config.source.root.root.independent_group_id,)


def operand_sha256s(config):
    if type(config) is ScheduledCommitmentConfig:
        index = ScheduledSourceIndex.from_shared(reservation=config.reservation,
            specification=config.specification, provenances=config.provenances)
        return tuple(sorted({*(o.object_fingerprint for s in config.sources for o in source_operands(index.resolve(s))),
            config.audit.fingerprint(), config.forecast_design.fingerprint(), *(p.logical.content_sha256 for p in config.audit.prior_corpus)}))
    if type(config) in (ScheduledForecastConfig, ScheduledCalibratedForecastConfig):
        return tuple(sorted({config.public_source.source.object_fingerprint, config.public_source.fingerprint(), config.design.fingerprint()}))
    return tuple(sorted({config.commitment_config.object_fingerprint, *(o.object_fingerprint for o in source_operands(config.source))}))


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def _dependency(context, port, root_id, owner, *, access=BLIND, visibility=PROSPECTIVE, namespace=NAMESPACE):
    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    task = (COMMIT_KEY if namespace == NAMESPACE else namespace+'.commit') if owner == 'commit' else namespace+'.'+root_id+'.'+owner
    if (port.kind is not WorkerInputKind.DEPENDENCY or port.outcome_access is not access or port.visibility_ceiling is not visibility
            or len(receipts) != 1 or receipts[0].task_id != task):
        raise ValueError('scheduled consumer loses exact original ordinary dependency receipt/access')


def _worker(context, config, role, m):
    root_id = config.root_id if type(config) in (ScheduledForecastConfig, ScheduledCalibratedForecastConfig) else config.source.root_id
    if (type(context) is not TaskContext or context.task_id != NAMESPACE+'.'+root_id+'.'+role
            or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
            or context.config.content_sha256 != config.fingerprint() or context.permissions != m.permissions
            or not BUDGET.contains(context.resource_budget) or context.outcome_access is not phase_access(role)):
        raise ValueError('scheduled worker lacks exact issued configuration/resources/permissions/access')


def _decode(context, role):
    phase = next(p for p in PHASES if p[0] == role)
    types = {config_type(role).SCHEMA: config_type(role), **{t.SCHEMA: t for _, t in phase[1] if t and t is not MatrixHistorySeed}}
    records, ports, streams = {}, {}, []
    if type(context) is not TaskContext or context.outcome_access is not phase_access(role):
        raise ValueError('scheduled worker refuses unsupported access before reading source')
    for port in context.input_ports:
        if port.payload_schema in types and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(), types[port.payload_schema], maximum_bytes=None)
            ports[port.payload_schema] = port
        elif port.payload_schema == MatrixHistorySeed.SCHEMA and role in ('prefix', 'continue', 'continue-development'):
            streams.append(decode_canonical_bytes(port.read(), MatrixHistorySeed, maximum_bytes=None))
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA and port.artifact_id not in ports:
            ports[port.artifact_id] = port
        else:
            raise ValueError('scheduled worker receives duplicate or undeclared scientific operands')
    optional = {ScheduledResponseForecast.SCHEMA} if role.startswith('continue') else set()
    if not set(types)-optional <= set(records) <= set(types) or sum(p.payload_schema == MATRIX_ARRAY_SCHEMA for p in context.input_ports) != sum(t is None for _, t in phase[1]):
        raise ValueError('scheduled worker omits complete typed/raw input census')
    config = records[config_type(role).SCHEMA]
    m = next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)
    _worker(context, config, role, m)
    if context.config.artifact_id != ports[config.SCHEMA].artifact_id:
        raise ValueError('scheduled worker substitutes exact ordinary config artifact')
    if role in ('forecast', 'forecast-calibrated'):
        causal, feature = records[ScheduledCausalPrefix.SCHEMA], records[ScheduledForecastFeature.SCHEMA]
        for cls, owner in ((ScheduledCausalPrefix, 'project'), (ScheduledForecastFeature, 'project')):
            _dependency(context, ports[cls.SCHEMA], config.root_id, owner)
        _raw_input(context, ports, causal.arrays, config.root_id, 'project')
        if causal.source != config.public_source.source or feature.prefix != identity(causal):
            raise ValueError('scheduled predictor substitutes exact opaque original prefix/source')
        if role == 'forecast-calibrated':
            calibration = records[ScheduledCalibration.SCHEMA]
            port = ports[calibration.SCHEMA]
            require_publication_copy(calibration, port, config.design.calibration_publication)
            if identity(calibration) != config.design.calibration or port.outcome_access is not OutcomeAccess.EVALUATION_SEALED or port.visibility_ceiling is not PROSPECTIVE:
                raise ValueError('scheduled query loses actual original qualified sealed calibration score port')
        return config, None, records, ports
    reference = records[ScheduledSource.SCHEMA]
    if config.operation != role or config.source != reference:
        raise ValueError('scheduled phase changes exact selected source')
    shared = records[ScheduledCommitmentConfig.SCHEMA]
    index = require_shared_config(shared, ports[shared.SCHEMA], expected=config.commitment_config)
    source_port = ports[ScheduledSource.SCHEMA]
    if (source_port.kind is not WorkerInputKind.EXTERNAL or source_port.artifact_id != reference.source_id
            or source_port.outcome_access is not BLIND or source_port.visibility_ceiling is not PROSPECTIVE
            or reference.root_id not in shared.selected_root_ids):
        raise ValueError('scheduled phase substitutes its exact external selected source reference')
    source = index.resolve(reference)
    config = BoundScheduledConfig(config, source, shared)
    if role in ('prefix', 'continue', 'continue-development'):
        if (records[ScheduledAllocation.SCHEMA] != source.allocation or records[ScheduledSelection.SCHEMA] != source.specification.selection
                or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate or records[NumericalProducingProvenance.SCHEMA] != source.provenance
                or tuple(sorted(streams, key=lambda s: s.purpose)) != source.root.streams):
            raise ValueError('scheduled native phase changes complete actual source/coordinate/provenance/stream inputs')
        for cls, pub in ((ScheduledAllocation, source.reservation.publication), (ScheduledSelection, source.specification.publication)):
            require_publication_copy(records[cls.SCHEMA], ports[cls.SCHEMA], pub)
    if role == 'prefix':
        commitment = records[ScheduledCommitment.SCHEMA]
        require_current_commitment(commitment, shared)
        commitment.validate_source(source)
        _dependency(context, ports[ScheduledCommitment.SCHEMA], source.root_id, 'commit')
        if (records[ScheduledAllocation.SCHEMA] != source.allocation or records[ScheduledSelection.SCHEMA] != source.specification.selection
                or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate or records[NumericalProducingProvenance.SCHEMA] != source.provenance
                or tuple(sorted(streams, key=lambda s: s.purpose)) != source.root.streams
                or any(p.outcome_access is not BLIND or p.visibility_ceiling is not PROSPECTIVE for p in context.input_ports)):
            raise ValueError('scheduled prefix substitutes exact source/publication/stream scope')
        for cls, pub in ((ScheduledAllocation, source.reservation.publication), (ScheduledSelection, source.specification.publication)):
            require_publication_copy(records[cls.SCHEMA], ports[cls.SCHEMA], pub)
    else:
        for name, cls in phase[1]:
            if name in ('source', 'commitment-config', 'forecast-design', 'allocation', 'selection', 'coordinate', 'provenance', 'streams') or cls is None or cls.SCHEMA not in records:
                continue
            owner = 'prefix' if name in ('history', 'checkpoint') else 'project' if name == 'causal' else 'commit' if name == 'commitment' else 'forecast-calibrated' if name == 'forecast' and records[ScheduledForecastSeal.SCHEMA].calibration is not None else name
            access = OutcomeAccess.EVALUATION_SEALED if owner == 'forecast-calibrated' else full_access(source) if owner.startswith('continue') else BLIND
            visibility = full_visibility(source) if owner.startswith('continue') else PROSPECTIVE
            _dependency(context, ports[cls.SCHEMA], source.root_id, owner, access=access, visibility=visibility)
            if hasattr(records[cls.SCHEMA], 'arrays'):
                _raw_input(context, ports, records[cls.SCHEMA].arrays, source.root_id, owner, access=access, visibility=visibility,
                    required=any(n == name+'-arrays' for n, _ in phase[1]))
        if role.startswith('continue'):
            require_current_commitment(records[ScheduledCommitment.SCHEMA], shared)
            records[ScheduledCommitment.SCHEMA].validate_source(source)
            history, causal, seal = records[ScheduledPrefixHistory.SCHEMA], records[ScheduledCausalPrefix.SCHEMA], records[ScheduledForecastSeal.SCHEMA]
            history.validate_source(source, native_context=config.native_context)
            validate_original_prefix_receipt(history, context.run_id)
            if (records[ScheduledCheckpoint.SCHEMA] != history.checkpoint
                    or causal.history != identity(history) or causal.source != identity(source)
                    or seal.source != identity(source) or seal.prefix != identity(causal)
                    or seal.design != records[ScheduledCommitment.SCHEMA].forecast_design):
                raise ValueError('scheduled continuation lacks exact original committed pre-future forecast seal')
            physical = records.get(ScheduledResponseForecast.SCHEMA)
            selection = records[ScheduledCommitment.SCHEMA].response_selection
            if (physical is None) != (selection is None) or physical is not None and (
                    physical.source != identity(source) or physical.causal_prefix != identity(causal)):
                raise ValueError('scheduled continuation lacks original committed physical pre-future forecast seal')
    return config, source, records, ports


def validate_original_prefix_receipt(history, run_id):
    """Exact native completeness in the live ordinary dependency bridge."""
    q = history.native.receipt
    expected = {q.task_id+'.output.arrays', q.task_id+'.output.checkpoint', q.task_id+'.completion'}
    if (history.native.definition.parent_contact.run_id != run_id or q.run_id != run_id
            or q.receipt_id != 'receipt.'+q.attempt_id
            or {a.logical_artifact_id for a in q.output_logical_artifacts} != expected
            or {p.logical_artifact_id for p in q.output_materializations} != expected
            or len(q.output_logical_artifacts) != 3 or len(q.output_materializations) != 3):
        raise ValueError('scheduled continuation substitutes original complete canonical prefix native receipt')
    completion = history.native.completion
    logical = next(a for a in q.output_logical_artifacts if a.logical_artifact_id == q.task_id+'.completion')
    physical = next(p for p in q.output_materializations if p.logical_artifact_id == logical.logical_artifact_id)
    if (logical.payload_schema != completion.SCHEMA or logical.content_sha256 != completion.fingerprint()
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
            or logical.outcome_access is not BLIND or logical.visibility_ceiling is not PROSPECTIVE
            or physical.physical_sha256 != completion.fingerprint() or physical.size_bytes != len(completion.canonical_bytes())):
        raise ValueError('scheduled continuation changes original native completion control publication')


def _raw_input(context, ports, arrays, root_id, owner, *, access=BLIND, visibility=PROSPECTIVE, required=True, namespace=NAMESPACE):
    saved = arrays.array_artifact
    port = ports.get(saved.artifact_id)
    if not required and port is None:
        return
    if port is None or (port.payload_schema, port.media_type, port.size_bytes) != (saved.payload_schema, saved.media_type, saved.size_bytes):
        raise ValueError('scheduled raw input differs from original receipted archive')
    _dependency(context, port, root_id, owner, access=access, visibility=visibility, namespace=namespace)


def _outputs(context, product, raw=None, feature=None):
    ports = {p.output_id.rsplit('.', 1)[-1]: p for p in context.output_ports}
    checkpoint = product.checkpoint if type(product) is ScheduledPrefixHistory else None
    expected = {'product'} | ({'arrays'} if raw is not None else set()) | ({'feature'} if feature is not None else set()) | ({'checkpoint'} if checkpoint is not None else set())
    if set(ports) != expected or ports['product'].payload_schema != product.SCHEMA:
        raise ValueError('scheduled provider changes complete selected output census')
    outputs = [TaskOutputPayload(ports['product'].output_id, product.canonical_bytes())]
    if raw is not None:
        artifact = product.arrays.array_artifact
        if (ports['arrays'].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ or ports['arrays'].logical_artifact_id != artifact.artifact_id
                or sha256(raw).hexdigest() != artifact.sha256 or len(raw) != artifact.size_bytes):
            raise ValueError('scheduled provider substitutes original array artifact bytes')
        outputs.append(TaskOutputPayload(ports['arrays'].output_id, raw))
    if feature is not None:
        if ports['feature'].payload_schema != feature.SCHEMA:
            raise ValueError('scheduled provider changes bounded causal feature output')
        outputs.append(TaskOutputPayload(ports['feature'].output_id, feature.canonical_bytes()))
    if checkpoint is not None:
        if ports['checkpoint'].payload_schema != checkpoint.SCHEMA:
            raise ValueError('scheduled prefix changes original ordinary checkpoint output')
        outputs.append(TaskOutputPayload(ports['checkpoint'].output_id, checkpoint.canonical_bytes()))
    return RunnerResult(tuple(sorted(outputs, key=lambda o: o.output_id)), (ReceiptCheck('scheduled-original-source-cutoff-census', True, ()),))


class ScheduledRunner:
    def __init__(self, role, *, decoder=None, manifest=None):
        self.role = role
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)
        self.decoder = decoder

    def _decode(self, context):
        return (self.decoder or _decode)(context, self.role)

    def execute(self, context):
        try:
            config, source, records, ports = self._decode(context)
            if self.role in ('prefix', 'continue', 'continue-development'):
                raise ValueError('scheduled acquisition requires genuine issued native-subwork authorization')
            if self.role in ('forecast', 'forecast-calibrated'):
                causal = records[ScheduledCausalPrefix.SCHEMA]
                decode_matrix_arrays(ports[causal.arrays.array_artifact.artifact_id].read(), causal.arrays)
                return _outputs(context, forecast_public(config.design, config.public_source, causal,
                    records[ScheduledForecastFeature.SCHEMA], seal_id='seal.'+config.root_id,
                    calibration_record=records.get(ScheduledCalibration.SCHEMA)))
            if self.role.startswith('full-numerical'):
                history = records[ScheduledFullHistory.SCHEMA]
                arrays = decode_matrix_arrays(ports[history.arrays.array_artifact.artifact_id].read(), history.arrays)
                return _outputs(context, science.assess_full(source, history, arrays))
            history = records[ScheduledPrefixHistory.SCHEMA]
            raw = ports[history.arrays.array_artifact.artifact_id].read()
            arrays = science.consume_prefix(source, history.arrays, raw)
            if self.role == 'numerical':
                return _outputs(context, science.assess_prefix(source, history, arrays, native_context=config.native_context))
            numerical = records[ScheduledNumericalAssessment.SCHEMA]
            if self.role == 'measure':
                output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
                diagnostic, witness = science.measure_prefix(source, history, numerical, arrays, artifact_id=output.logical_artifact_id, native_context=config.native_context)
                return _outputs(context, witness, diagnostic)
            witness = records[ScheduledPrefixWitness.SCHEMA]
            diagnostic = ports[witness.arrays.array_artifact.artifact_id].read()
            frames = science.check_frames(source, history, numerical, witness, raw, diagnostic, native_context=config.native_context)
            if self.role == 'check':
                return _outputs(context, frames)
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            causal_raw, causal = science.causal_delivery(source, history, numerical, witness, records[ScheduledFrameAssessment.SCHEMA],
                raw, diagnostic, artifact_id=output.logical_artifact_id, native_context=config.native_context)
            feature = causal_feature(records[ScheduledForecastDesign.SCHEMA], source, causal, witness,
                decode_matrix_arrays(causal_raw, causal.arrays), decode_matrix_arrays(diagnostic, witness.arrays), feature_id='feature.'+source.root_id)
            return _outputs(context, causal, causal_raw, feature)
        finally:
            for port in context.input_ports:
                port.close()


def _initial_native_work(context, config, source, records, ports, role, parent):
    """Original prefix/checkpoint definition shared by preparation and entry."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    history = causal = seal = prefix_raw = terminal = None
    if ((parent.run_id, parent.task_id, parent.attempt_id, parent.input_materialization_ids, parent.implementation_commit) !=
            (context.run_id, context.task_id, context.attempt_id, context.input_materialization_ids, source.provenance.observed_git_head)):
        raise ValueError('scheduled native entry changes actual ordinary parent contact')
    prefix_only = role == 'prefix'
    if prefix_only:
        outputs = (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
            NativeSubworkOutput('checkpoint', ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'))
        subwork = 'prefix.'+source.root_id
        start, stop = 0, source.policy.cutoff_tick
    else:
        history, causal, seal = records[ScheduledPrefixHistory.SCHEMA], records[ScheduledCausalPrefix.SCHEMA], records[ScheduledForecastSeal.SCHEMA]
        # The sealed parent port cannot open a different blind store.
        # Stock ordinary dependency custody authenticates the complete
        # prefix product, including its exact successful nested receipt.
        # The cold reader separately checks that original blind store.
        if history.native.definition.parent_contact.run_id != context.run_id:
            raise ValueError('scheduled continuation substitutes a foreign original prefix run')
        prefix_raw = ports[history.arrays.array_artifact.artifact_id].read()
        prefix_arrays = science.consume_prefix(source, history.arrays, prefix_raw)
        terminal = {v+'_'+c: prefix_arrays[v+'_'+c][-1] for v in ('primary', 'fine') for c in ('positions', 'momenta')}
        start, stop = source.policy.cutoff_tick, source.coordinate.total_ticks
        segments.validate_segment_entry(source.coordinate, source.root.streams, start, stop,
            terminal=terminal, generator_states=history.checkpoint.generators)
        outputs = (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),)
        subwork = 'continue.'+source.root_id
    configuration, expected_parent, operation, shared_sources = config.native_context.contract(role)
    if expected_parent != context.task_id or configuration != identity(config):
        raise ValueError('scheduled native entry substitutes actual configuration/parent task')
    extras = () if prefix_only else (identity(history), identity(history.checkpoint), identity(causal), identity(seal))
    if not prefix_only and ScheduledResponseForecast.SCHEMA in records:
        extras += (identity(records[ScheduledResponseForecast.SCHEMA]),)
    sources = (*shared_sources, *extras)
    definition = NativeSubworkDefinition(subwork, operation, parent, configuration, tuple(sorted(sources, key=lambda o: o.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, context.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda o: o.object_id)), outputs)
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    work = PreparedNativeWork(parent, (source.root.root.independent_group_id,),
        (config.operation+'.'+source.root_id,), (definition,), (roster,))
    return work, prefix_only, start, stop, history, causal, seal, prefix_raw, terminal


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ScheduledNativeRunner or runner.role not in ('prefix', 'continue', 'continue-development'):
        raise ValueError('scheduled history preparation requires its installed original native phase')
    config, source, records, ports = runner._decode(context)
    return _initial_native_work(context, config, source, records, ports, runner.role, expected_parent)[0]


class ScheduledNativeRunner(ScheduledRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, source, records, ports = self._decode(context)
            parent = native_subwork.parent_contact
            work, prefix_only, start, stop, history, causal, seal, prefix_raw, terminal = _initial_native_work(
                context, config, source, records, ports, self.role, parent)
            raw, arrays, checkpoint, definition, completed = execute_parameter_native_work(
                source, work, native_subwork, prefix_only=prefix_only, start=start, stop=stop,
                history=history, prefix_raw=prefix_raw, terminal=terminal, progress=progress)
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            evidence = ScheduledNativeEvidence(definition, completed.completion, completed.receipt)
            if prefix_only:
                _, operand = science._array_product(source, arrays, role='PREFIX', artifact_id=output.logical_artifact_id,
                    producers=(identity(source), coordinate_identity(source.coordinate)), raw=raw)
                product = ScheduledPrefixHistory('history.'+source.root_id, identity(source), operand, checkpoint, evidence)
                product.validate_source(source, native_context=config.native_context)
            else:
                _, operand = science.full_array_product(source, history, arrays, artifact_id=output.logical_artifact_id, raw=raw)
                product = ScheduledFullHistory('full-history.'+source.root_id, identity(source), identity(history), identity(history.checkpoint),
                    identity(seal), operand, evidence, stop, 2*stop,
                    identity(records[ScheduledResponseForecast.SCHEMA]) if ScheduledResponseForecast.SCHEMA in records else None)
                product.validate_source(source, history, causal, seal, records.get(ScheduledResponseForecast.SCHEMA), native_context=config.native_context)
            return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


def output_codecs():
    return {t.SCHEMA: t for t in (ScheduledCommitment, ScheduledPrefixHistory, ScheduledNumericalAssessment, ScheduledPrefixWitness,
        ScheduledCheckpoint, ScheduledFrameAssessment, ScheduledCausalPrefix, ScheduledForecastFeature, ScheduledForecastSeal, ScheduledFullHistory, ScheduledFullAssessment, ScheduledCalibration)}


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def _operation_declaration(role, inputs, output, stage, raw):
    from .qualification import scientific_root_validator
    from .calibration import qualified_parent_assessor
    from .commitment import authenticate_prior_publications
    outputs = [OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')]
    if raw:
        outputs.append(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'))
    if role == 'project':
        outputs.append(OutputTemplate('feature', ScheduledForecastFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    if role == 'prefix':
        outputs.append(OutputTemplate('checkpoint', ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    native = role in ('prefix', 'continue', 'continue-development')
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.original-scheduled-' + role + '.v1',
        kind=CapabilityKind.SIMULATOR if role in ('prefix', 'continue', 'continue-development') else CapabilityKind.EXPERIMENT_DESIGNER if role in ('forecast', 'forecast-calibrated', 'commit') else CapabilityKind.FALSIFIER if stage is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
        config_record_type=config_type(role),
        stage=stage,
        input_ports=tuple((RecursivePortContract(n, t.SCHEMA if t else MATRIX_ARRAY_SCHEMA, 'application/json' if t else 'application/x-npz', None if t else MAXIMUM_MATRIX_ARRAY_BYTES, minimum_count=4 if n == 'streams' else 0 if n in ('prior-coordinates', 'response-selection', 'physical-forecast') else 1, maximum_count=None if n in ('streams', 'prior-coordinates') or (role == 'commit' and n == 'source') else 1) for n, t in sorted(inputs))),
        outputs=tuple(sorted(outputs, key=lambda o: o.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT if role.endswith('-development') else CapabilityPermission.READ_SEALED_OUTCOMES if role in ('continue', 'full-numerical', 'forecast-calibrated') else CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE if role.endswith('-development') else EvidenceCeiling.RESPONSE,
        outcome_access=phase_access(role),
        visibility_ceiling=phase_visibility(role),
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('complete-matched-group-source-census', 'original-prefix-checkpoint-seal-custody', 'predictor-no-future-stream-operands'))),
        runner_factory=lambda: ScheduledCommitter(selected.manifest(), BUDGET) if role == "commit" else ScheduledNativeRunner(role) if native else ScheduledRunner(role),
        record_codecs={**output_codecs(), **{kind.SCHEMA: kind for _, kind in inputs if kind is not None}},
        scientific_hooks=RecursiveScientificHooks(qualified_parent_assessor=qualified_parent_assessor if role == 'forecast-calibrated' else None, native_effect_slot_ids=(lambda c: (c.operation + '.' + c.source.root_id,)) if native else None, scientific_operand_sha256s=operand_sha256s, scientific_unit_ids=units, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role in ('commit', 'forecast', 'forecast-calibrated') else BarrierKind.NONE, native_effect=native, complete_unit_census=native, native_work_preparer=prepare_native_work if native else None),
        publication_requirements=(RegisteredPublicationRequirement(NAMESPACE + '.prior-publications.v1', authenticate_prior_publications),) if role == 'commit' else (),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return selected


def operation_declarations():
    from .response_bindings import response_declarations
    from .calibration_bindings import calibration_declarations
    return (*(_operation_declaration(*phase) for phase in PHASES),
        *response_declarations(), *calibration_declarations())
