# SPDX-License-Identifier: MPL-2.0
"""Real v2 custody ports for one authenticated shared scheduled bank."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursivePortContract, RegisteredPublicationRequirement,
)

from . import operation_bindings as core, response_bindings as response, calibration_bindings as calibration
from .commitment import ScheduledCommitment, ScheduledExposureAudit, require_publication_copy
from .compact_records import (
    NAMESPACE, ScheduledCompactBank, ScheduledCompactCalibrationConfig,
    ScheduledCompactCommitmentConfig, ScheduledCompactConfig, ScheduledCompactForecastConfig,
    ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig,
    compact_committed, compact_identity,
)
from .continuation import ScheduledFullAssessment, full_access, full_visibility
from .forecast import ScheduledCalibration, ScheduledCausalPrefix, ScheduledForecastDesign, ScheduledForecastFeature, ScheduledForecastSeal
from .records import ScheduledAllocation, ScheduledCheckpoint, ScheduledPrefixHistory, ScheduledSelection, ScheduledSource, identity
from .source_index import ScheduledSourceIndex, ScheduledNativeSourceContext
from .response_records import ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore
from .response_selection import ScheduledResponseSelection

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

BLIND, PROSP = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class BoundCompactConfig:
    """Actual v2 configuration plus independently decoded scientific operands."""
    record: object
    source: object = None
    design: object = None
    selection: object = None
    commitment: object = None
    bank: object = None
    full_assessments: tuple = ()

    def __getattr__(self, name):
        return getattr(self.record, name)


def config_type(role):
    if role == 'commit':
        return ScheduledCompactCommitmentConfig
    if role in ('forecast', 'forecast-calibrated'):
        return ScheduledCompactForecastConfig
    if role == 'physical-forecast':
        return ScheduledCompactPhysicalForecastConfig
    if role.startswith('response'):
        return ScheduledCompactResponseConfig
    if role in ('calibrate', 'calibration-qualify'):
        return ScheduledCompactCalibrationConfig
    return ScheduledCompactConfig


def _inputs(role, inputs):
    result = tuple((name, cls) for name, cls in inputs if name != 'commitment-config')
    if role not in ('forecast', 'forecast-calibrated', 'physical-forecast'):
        result += (('bank', ScheduledCompactBank),)
    if role in ('forecast', 'forecast-calibrated'):
        result += (('forecast-design', ScheduledForecastDesign),)
    if role.startswith('response-score'):
        result += (('response-selection', ScheduledResponseSelection),)
    if role == 'calibration-qualify':
        result += (('full-numericals', ScheduledFullAssessment),)
    return tuple(sorted(result))


PHASES = tuple((role, _inputs(role, inputs), out, stage, raw)
    for role, inputs, out, stage, raw in (*core.PHASES, *response.RESPONSE_PHASES)) + tuple(
    (role, _inputs(role, inputs), out, stage, False) for role, inputs, out, stage in calibration.CALIBRATION_PHASES)


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def units(config):
    if type(config) is ScheduledCompactCommitmentConfig:
        bank = config.bank
        return tuple(sorted({s.root.root.independent_group_id for s in bank.sources if s.root_id in bank.selected_root_ids}))
    if type(config) is ScheduledCompactCalibrationConfig:
        return config.group_ids
    if type(config) is ScheduledCompactForecastConfig:
        return (config.public_source.root.independent_group_id,)
    if type(config) is ScheduledCompactPhysicalForecastConfig:
        return (config.protocol.public_source.root.independent_group_id,)
    return (config.source.root.root.independent_group_id,)


def operands(config):
    if type(config) is ScheduledCompactCommitmentConfig:
        return tuple(sorted({config.bank.fingerprint(), *core.operand_sha256s(config.bank.commitment_config())}))
    if type(config) is ScheduledCompactCalibrationConfig:
        return (config.bank.object_fingerprint,)
    if type(config) is ScheduledCompactForecastConfig:
        return tuple(sorted({config.public_source.fingerprint(), config.public_source.source.object_fingerprint, config.design.object_fingerprint}))
    if type(config) is ScheduledCompactPhysicalForecastConfig:
        return tuple(sorted({config.protocol.fingerprint(), config.protocol.public_source.source.object_fingerprint}))
    return tuple(sorted({config.source.fingerprint(), config.bank.object_fingerprint,
        *((config.selection.object_fingerprint,) if type(config) is ScheduledCompactResponseConfig else ())}))


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def dependency(context, port, root_id, owner, **kwargs):
    return core._dependency(context, port, root_id, owner, namespace=NAMESPACE, **kwargs)


def raw_input(context, ports, arrays, root_id, owner, **kwargs):
    return core._raw_input(context, ports, arrays, root_id, owner, namespace=NAMESPACE, **kwargs)


def _read(context, role):
    if type(context) is not TaskContext or context.outcome_access is not core.phase_access(role):
        raise ValueError('compact scheduled worker refuses unsupported issued access before input reads')
    phase = next(p for p in PHASES if p[0] == role)
    cls = config_type(role)
    types = {cls.SCHEMA: cls, **{t.SCHEMA: t for _, t in phase[1] if t and t is not MatrixHistorySeed}}
    values, ports, streams = {}, {}, []
    repeated = {ScheduledSource.SCHEMA, core.MatrixParameterCoordinate.SCHEMA} if role == 'commit' else set()
    if role == 'calibrate':
        repeated |= {ScheduledResponseScore.SCHEMA, ScheduledForecastSeal.SCHEMA}
    if role == 'calibration-qualify':
        repeated.add(ScheduledFullAssessment.SCHEMA)
    shared_schemas = {t.SCHEMA for t in (ScheduledCompactBank, ScheduledSource, ScheduledAllocation,
        ScheduledSelection, core.MatrixParameterCoordinate, core.NumericalProducingProvenance, MatrixHistorySeed,
        ScheduledForecastDesign, ScheduledResponseSelection, ScheduledExposureAudit, core.MatrixFactorExposureCensus,
        core.MatrixResponseErrorModel, core.MatrixResponseErrorPredictionSpec, core.MatrixResponseFrontierProtocol)}
    for port in context.input_ports:
        if port.payload_schema in shared_schemas and (port.kind is not WorkerInputKind.EXTERNAL
                or port.outcome_access is not BLIND or port.visibility_ceiling is not PROSP):
            raise ValueError('compact worker changes the original blind prospective shared operand boundary')
        raw = None
        if port.payload_schema == MatrixHistorySeed.SCHEMA and any(t is MatrixHistorySeed for _, t in phase[1]):
            raw = port.read()
            record = decode_canonical_bytes(raw, MatrixHistorySeed, maximum_bytes=None)
            if port.media_type != 'application/json' or raw != record.canonical_bytes() or len(raw) != port.size_bytes:
                raise ValueError('compact worker substitutes exact declared stream bytes')
            streams.append((record, port))
        elif port.payload_schema in types:
            if port.payload_schema in values and port.payload_schema not in repeated:
                raise ValueError('compact worker receives duplicate shared scientific operands')
            raw = port.read()
            record = decode_canonical_bytes(raw, types[port.payload_schema], maximum_bytes=None)
            if port.media_type != 'application/json' or raw != record.canonical_bytes() or len(raw) != port.size_bytes:
                raise ValueError('compact worker changes exact canonical shared operand bytes')
            values.setdefault(port.payload_schema, []).append((record, port))
            ports[port.payload_schema] = port
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA and port.artifact_id not in ports:
            ports[port.artifact_id] = port
        else:
            raise ValueError('compact worker receives undeclared scientific operands')
    optional = {ScheduledResponseForecast.SCHEMA} if role.startswith('continue') else set()
    if role == 'commit':
        optional |= {ScheduledResponseSelection.SCHEMA, core.MatrixParameterCoordinate.SCHEMA}
    if not set(types)-optional <= set(values) <= set(types) or sum(p.payload_schema == MATRIX_ARRAY_SCHEMA for p in context.input_ports) != sum(t is None for _, t in phase[1]):
        raise ValueError('compact worker omits the complete declared typed/raw input census')
    config, config_port = values[cls.SCHEMA][0]
    m = next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.'+role)
    task = NAMESPACE+'.'+role if role in ('commit', 'calibrate', 'calibration-qualify') else NAMESPACE+'.'+config.root_id+'.'+role
    if (context.task_id != task or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
            or context.config.content_sha256 != config.fingerprint() or context.config.artifact_id != config_port.artifact_id
            or context.permissions != m.permissions or not core.BUDGET.contains(context.resource_budget)):
        raise ValueError('compact worker changes actual issued v2 configuration/resources/permissions')
    return config, values, ports, streams


def _one(values, cls):
    rows = values.get(cls.SCHEMA, ())
    if len(rows) != 1:
        raise ValueError('compact worker omits exact single shared operand')
    return rows[0][0]


def _bound(config, values):
    bank = _one(values, ScheduledCompactBank)
    if config.bank != compact_identity(bank):
        raise ValueError('compact phase substitutes the pinned complete shared bank')
    descriptor = _one(values, ScheduledSource)
    if config.source != descriptor:
        raise ValueError('compact phase substitutes its original scientific subject descriptor')
    index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    return bank, index.resolve(descriptor)


def require_committed_bank(commitment, bank):
    """Bind the received pre-access freeze to this exact complete shared bank."""
    expected = compact_committed(ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', bank))
    if type(commitment) is not ScheduledCommitment or commitment != expected:
        raise ValueError('scheduled commitment differs from the exact current shared bank configuration')


def decode_core(context, role, *, reader=None, dependency_checker=None):
    # Additive operational admissions may supply a different authenticated
    # read boundary. Every scientific/native join below still runs, and their
    # dependency checker must compose the unchanged ordinary checks.
    config, values, ports, streams = (reader or _read)(context, role)
    check_dependency = dependency_checker or dependency
    records = {schema: rows[0][0] for schema, rows in values.items()}
    if role in ('forecast', 'forecast-calibrated'):
        if config.operation != role:
            raise ValueError('compact predictor changes its selected blind/sealed operation')
        design = _one(values, ScheduledForecastDesign)
        if config.design != identity(design):
            raise ValueError('compact predictor substitutes frozen public design')
        from .forecast import ScheduledForecastConfig, ScheduledCalibratedForecastConfig
        scientific_config = ScheduledCalibratedForecastConfig if config.calibrated else ScheduledForecastConfig
        scientific_config('config.matrix-scheduled-history.'+config.root_id+'.'+role, config.public_source, design)
        causal, feature = _one(values, ScheduledCausalPrefix), _one(values, ScheduledForecastFeature)
        check_dependency(context, ports[causal.SCHEMA], config.root_id, 'project')
        check_dependency(context, ports[feature.SCHEMA], config.root_id, 'project')
        raw_input(context, ports, causal.arrays, config.root_id, 'project')
        if causal.source != config.public_source.source or feature.prefix != identity(causal):
            raise ValueError('compact predictor substitutes original causal prefix')
        if role == 'forecast-calibrated':
            value = _one(values, ScheduledCalibration)
            port = ports[value.SCHEMA]
            require_publication_copy(value, port, design.calibration_publication)
            if identity(value) != design.calibration or port.outcome_access is not OutcomeAccess.EVALUATION_SEALED or port.visibility_ceiling is not PROSP:
                raise ValueError('compact query substitutes exact qualified sealed calibration')
        return BoundCompactConfig(config, design=design), None, records, ports
    bank, source = _bound(config, values)
    if config.operation != role:
        raise ValueError('compact phase changes selected operation')
    if role in ('prefix', 'continue', 'continue-development'):
        if (_one(values, ScheduledAllocation) != source.allocation or _one(values, ScheduledSelection) != source.specification.selection
                or _one(values, core.MatrixParameterCoordinate) != source.coordinate
                or _one(values, core.NumericalProducingProvenance) != source.provenance
                or tuple(sorted((s for s, _ in streams), key=lambda s: s.purpose)) != source.root.streams):
            raise ValueError('compact native phase changes exact original shared coordinate/provenance/streams')
        for cls, pub in ((ScheduledAllocation, source.reservation.publication), (ScheduledSelection, source.specification.publication)):
            require_publication_copy(records[cls.SCHEMA], ports[cls.SCHEMA], pub)
    for name, cls in next(p for p in PHASES if p[0] == role)[1]:
        if cls is None or name in ('bank', 'source', 'forecast-design', 'allocation', 'selection', 'coordinate', 'provenance', 'streams') or cls.SCHEMA not in records:
            continue
        owner = 'prefix' if name in ('history', 'checkpoint') else 'project' if name == 'causal' else 'commit' if name == 'commitment' else 'forecast-calibrated' if name == 'forecast' and records[ScheduledForecastSeal.SCHEMA].calibration is not None else name
        access = OutcomeAccess.EVALUATION_SEALED if owner == 'forecast-calibrated' else full_access(source) if owner.startswith('continue') else BLIND
        visibility = full_visibility(source) if owner.startswith('continue') else PROSP
        check_dependency(context, ports[cls.SCHEMA], source.root_id, owner, access=access, visibility=visibility)
        if hasattr(records[cls.SCHEMA], 'arrays'):
            raw_input(context, ports, records[cls.SCHEMA].arrays, source.root_id, owner, access=access, visibility=visibility,
                required=any(n == name+'-arrays' for n, _ in next(p for p in PHASES if p[0] == role)[1]))
    if role == 'prefix':
        commitment = _one(values, ScheduledCommitment)
        require_committed_bank(commitment, bank)
        commitment.validate_source(source)
        if any(p.outcome_access is not BLIND or p.visibility_ceiling is not PROSP for p in context.input_ports):
            raise ValueError('compact prefix changes original blind prospective input boundary')
    elif role.startswith('continue'):
        commitment = _one(values, ScheduledCommitment)
        require_committed_bank(commitment, bank)
        commitment.validate_source(source)
        history, causal, seal = (_one(values, cls) for cls in (ScheduledPrefixHistory, ScheduledCausalPrefix, ScheduledForecastSeal))
        history.validate_source(source, native_context=ScheduledNativeSourceContext(source, config, bank))
        core.validate_original_prefix_receipt(history, context.run_id)
        if (_one(values, ScheduledCheckpoint) != history.checkpoint or causal.history != identity(history)
                or causal.source != identity(source) or seal.source != identity(source) or seal.prefix != identity(causal)
                or seal.design != commitment.forecast_design):
            raise ValueError('compact continuation changes original committed checkpoint/forecast seal')
        physical = records.get(ScheduledResponseForecast.SCHEMA)
        if (physical is None) != (commitment.response_selection is None) or physical is not None and (physical.source != identity(source) or physical.causal_prefix != identity(causal)):
            raise ValueError('compact continuation omits original physical forecast seal')
    # The numerical body consumes typed scientific state, while all ports and
    # Native definitions retain their actual compact identities above.
    return core.BoundScheduledConfig(config, source, bank), source, records, ports


def decode_response(context, role, *, reader=None, dependency_checker=None):
    config, values, ports, streams = (reader or _read)(context, role)
    check_dependency = dependency_checker or dependency
    records = {schema: rows[0][0] for schema, rows in values.items()}
    causal = _one(values, ScheduledCausalPrefix)
    check_dependency(context, ports[causal.SCHEMA], config.root_id, 'project')
    if role == 'physical-forecast':
        protocol = config.protocol
        raw_input(context, ports, causal.arrays, config.root_id, 'project')
        artifact = protocol.templates.array_artifact
        port = ports.get(artifact.artifact_id)
        if (port is None or (port.payload_schema, port.media_type, port.size_bytes, port.outcome_access, port.visibility_ceiling) !=
                (artifact.payload_schema, artifact.media_type, artifact.size_bytes, BLIND, PROSP)
                or causal.source != protocol.public_source.source or streams):
            raise ValueError('compact physical predictor substitutes its public templates/prefix')
        return config, None, records, ports
    bank, source = _bound(config, values)
    selection = _one(values, ScheduledResponseSelection)
    if config.operation != role or selection != bank.response_selection or config.selection != selection.identity:
        raise ValueError('compact response substitutes its pinned whole response selection')
    protocol, panels = selection.validate_source(source)
    history, physical, error = (_one(values, cls) for cls in (ScheduledPrefixHistory, ScheduledResponseForecast, ScheduledForecastSeal))
    native_context = ScheduledNativeSourceContext(source, config, bank)
    history.validate_source(source, native_context=native_context)
    core.validate_original_prefix_receipt(history, context.run_id)
    if (causal.source != identity(source) or causal.history != identity(history)
            or physical.source != identity(source) or physical.causal_prefix != identity(causal)
            or physical.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol) or error.source != identity(source)
            or error.prefix != identity(causal) or error.criterion != protocol.criterion):
        raise ValueError('compact response changes original source/prefix/physical/error seal joins')
    for cls, owner, arrays in ((ScheduledPrefixHistory, 'prefix', history.arrays), (ScheduledResponseForecast, 'physical-forecast', physical.arrays)):
        check_dependency(context, ports[cls.SCHEMA], source.root_id, owner)
        raw_input(context, ports, arrays, source.root_id, owner)
    error_owner = 'forecast-calibrated' if error.calibration is not None else 'forecast'
    check_dependency(context, ports[error.SCHEMA], source.root_id, error_owner,
        access=OutcomeAccess.EVALUATION_SEALED if error.calibration is not None else BLIND)
    if role.startswith('responses'):
        commitment = _one(values, ScheduledCommitment)
        require_committed_bank(commitment, bank)
        commitment.validate_source(source)
        check_dependency(context, ports[commitment.SCHEMA], source.root_id, 'commit')
        check_dependency(context, ports[ScheduledCheckpoint.SCHEMA], source.root_id, 'prefix')
        if (commitment.response_selection != selection.identity or commitment.forecast_design != error.design
                or _one(values, ScheduledCheckpoint) != history.checkpoint
                or _one(values, ScheduledAllocation) != source.allocation
                or _one(values, ScheduledSelection) != source.specification.selection
                or _one(values, core.MatrixParameterCoordinate) != source.coordinate
                or _one(values, core.NumericalProducingProvenance) != source.provenance):
            raise ValueError('compact pulse entry loses complete original committed source/selection')
        for cls, publication in ((ScheduledAllocation, source.reservation.publication), (ScheduledSelection, source.specification.publication)):
            require_publication_copy(records[cls.SCHEMA], ports[cls.SCHEMA], publication)
        expected = {(source.root.stream_identity(s).object_id, s) for s in source.root.streams}
        expected |= {(panel.stream_identity(s).object_id, s) for panel in panels if panel.role == 'INDEPENDENT_FUTURE' for s in panel.streams}
        if len(streams) != 8 or {(port.artifact_id, stream) for stream, port in streams} != expected:
            raise ValueError('compact pulse entry changes eight actual complete group-owned streams')
    else:
        response_record = _one(values, ScheduledResponseNative)
        response_record.validate_source(source, selection, history, causal, physical, error, native_context=native_context)
        owner = 'responses-development' if role.endswith('-development') else 'responses'
        check_dependency(context, ports[response_record.SCHEMA], source.root_id, owner, access=full_access(source), visibility=full_visibility(source))
        raw_input(context, ports, response_record.arrays, source.root_id, owner, access=full_access(source), visibility=full_visibility(source))
        if streams:
            raise ValueError('compact score receives undeclared future stream operands')
    return core.BoundScheduledConfig(config, source, bank), source, records, ports


def decode_calibration(context, role):
    config, rows, ports, streams = _read(context, role)
    bank = _one(rows, ScheduledCompactBank)
    commitment = bank.commitment_config()
    from .qualification import selected_sources
    selected = selected_sources(commitment)
    groups = tuple(sorted({s.root.root.independent_group_id for s in selected}))
    if config.bank != compact_identity(bank) or config.group_ids != groups or config.operation != role or streams:
        raise ValueError('compact calibration substitutes the actual whole-bank scope')
    from .calibration_bindings import ScheduledCalibrationConfig
    ScheduledCalibrationConfig('config.matrix-scheduled-history.'+role, role, identity(commitment),
        config.calibration_id, groups)
    expected = compact_committed(ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', bank))
    if _one(rows, ScheduledCommitment) != expected:
        raise ValueError('compact calibration loses actual complete committed bank')
    values = {ScheduledCommitment: rows[ScheduledCommitment.SCHEMA]}
    for cls in (ScheduledResponseScore, ScheduledForecastSeal, ScheduledCalibration):
        if cls.SCHEMA in rows:
            values[cls] = rows[cls.SCHEMA]
    config_port = ports[config.SCHEMA]
    full_assessments = ()
    if role == 'calibration-qualify':
        received = rows[ScheduledFullAssessment.SCHEMA]
        indexed = {record.source: (record, port) for record, port in received}
        if len(indexed) != len(received) or set(indexed) != {identity(source) for source in selected}:
            raise ValueError('compact qualification thins or duplicates the complete full-history numerical census')
        for source in selected:
            record, port = indexed[identity(source)]
            if (record.numerical_design != identity(source.numerical_design)
                    or record.history.object_id != 'full-history.'+source.root_id):
                raise ValueError('compact qualification substitutes original full-history numerical source/design')
            dependency(context, port, source.root_id, 'full-numerical', access=OutcomeAccess.EVALUATION_SEALED)
        full_assessments = tuple(indexed[identity(source)][0] for source in selected)
    return calibration.BoundScheduledCalibrationConfig(config, commitment, selected,
        bank=bank, full_assessments=full_assessments), config_port, values


class CompactCommitter:
    def __init__(self, manifest=None):
        self.manifest = manifest or next(m for m in operation_manifests() if m.capability_key == NAMESPACE+'.commit')

    def execute(self, context):
        try:
            if type(context) is not TaskContext or any(p.kind is not WorkerInputKind.EXTERNAL
                    or p.outcome_access is not BLIND or p.visibility_ceiling is not PROSP for p in context.input_ports):
                raise ValueError('compact commitment requires exact blind original external input boundaries')
            config, values, ports, streams = _read(context, 'commit')
            bank = _one(values, ScheduledCompactBank)
            if bank != config.bank or streams:
                raise ValueError('compact commitment changes exact complete shared bank')
            commitment = bank.commitment_config()
            expected = ((ScheduledAllocation, bank.reservation.allocation, bank.reservation.publication),
                (ScheduledSelection, bank.specification.selection, bank.specification.publication),
                (ScheduledExposureAudit, bank.audit, bank.audit_publication),
                (core.MatrixResponseErrorModel, bank.forecast_design.model_record, bank.forecast_design.model_publication),
                (core.MatrixResponseErrorPredictionSpec, bank.forecast_design.training_record, bank.forecast_design.training_publication),
                (core.MatrixResponseFrontierProtocol, bank.forecast_design.criterion_record, bank.forecast_design.criterion_publication))
            for cls, record, publication in expected:
                if _one(values, cls) != record:
                    raise ValueError('compact commitment substitutes original published scientific operand')
                require_publication_copy(record, ports[cls.SCHEMA], publication)
            if (_one(values, ScheduledForecastDesign) != bank.forecast_design
                    or tuple(sorted((v for v, _ in values[ScheduledSource.SCHEMA]), key=lambda s: s.root_id)) != bank.sources):
                raise ValueError('compact commitment thins exact descriptor/design census')
            for publication in bank.audit.prior_corpus:
                matches = [(record, port) for rows in values.values() for record, port in rows
                    if record.SCHEMA == publication.logical.payload_schema and record.fingerprint() == publication.logical.content_sha256]
                if len(matches) != 1:
                    raise ValueError('compact commitment omits original complete prior corpus')
                require_publication_copy(*matches[0], publication)
            if bank.response_selection is not None:
                record = _one(values, ScheduledResponseSelection)
                if record != bank.response_selection:
                    raise ValueError('compact commitment changes original full response selection')
                require_publication_copy(record, ports[record.SCHEMA], bank.response_selection_publication)
            elif ScheduledResponseSelection.SCHEMA in values:
                raise ValueError('compact commitment adds an unselected response population')
            commitment.__post_init__()
            product = compact_committed(config)
            if len(context.output_ports) != 1 or context.output_ports[0].payload_schema != product.SCHEMA:
                raise ValueError('compact commitment changes actual declared output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, product.canonical_bytes()),),
                (ReceiptCheck('compact-exact-original-subject-complete-shared-bank', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def _operation_declaration(role, inputs, out, stage, raw):
    from .compact_qualification import scientific_root_validator
    from .calibration import qualified_parent_assessor
    from .compact_records import authenticate_prior_publications
    kind = CapabilityKind.SIMULATOR if role in ('prefix', 'continue', 'continue-development', 'responses', 'responses-development') else CapabilityKind.EVALUATOR if role == 'calibration-qualify' else CapabilityKind.EXPERIMENT_DESIGNER if role in ('commit', 'forecast', 'forecast-calibrated', 'physical-forecast') else CapabilityKind.FALSIFIER if stage is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM
    read = CapabilityPermission.READ_DEVELOPMENT if role.endswith('-development') else CapabilityPermission.READ_SEALED_OUTCOMES if core.phase_access(role) in (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.EVALUATOR_REVEAL) else CapabilityPermission.READ_FROZEN_MODELS
    product_id = 'adjudication' if role == 'calibration-qualify' else 'product'
    outputs = [OutputTemplate(product_id, out.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')]
    if raw:
        outputs.append(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'))
    if role == 'project':
        outputs.append(OutputTemplate('feature', ScheduledForecastFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    if role == 'prefix':
        outputs.append(OutputTemplate('checkpoint', ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    native = role in ('prefix', 'continue', 'continue-development', 'responses', 'responses-development')
    ports = []
    for name, cls in inputs:
        minimum = 8 if name == 'streams' and role.startswith('responses') else 4 if name == 'streams' else 0 if name in ('prior-coordinates', 'response-selection', 'physical-forecast') and (not role.startswith('response')) else 1
        maximum = None if name in ('streams', 'prior-coordinates', 'full-numericals') or (role == 'commit' and name == 'source') or (role == 'calibrate' and name in ('forecasts', 'scores')) else 1
        ports.append(RecursivePortContract(name, cls.SCHEMA if cls else MATRIX_ARRAY_SCHEMA, 'application/json' if cls else 'application/x-npz', None if cls else MAXIMUM_MATRIX_ARRAY_BYTES, minimum_count=minimum, maximum_count=maximum))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.shared-original-subject-' + role + '.v2',
        kind=kind,
        config_record_type=config_type(role),
        stage=stage,
        input_ports=tuple(ports),
        outputs=tuple(sorted(outputs, key=lambda o: o.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, read, *((CapabilityPermission.REVEAL_OUTCOMES,) if role == "calibration-qualify" else ())))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE if role.endswith('-development') else EvidenceCeiling.RESPONSE,
        outcome_access=core.phase_access(role),
        visibility_ceiling=core.phase_visibility(role),
        resources=core.BUDGET,
        conformance_check_ids=tuple(sorted(('actual-v2-native-custody', 'complete-whole-matched-group-census', 'exact-original-subject-from-authenticated-shared-bank'))),
        runner_factory=lambda: CompactCommitter() if role == 'commit' else calibration.ScheduledCalibrator(role, decoder=decode_calibration, manifest=selected.manifest(), namespace=NAMESPACE, dependency_checker=dependency) if role in ('calibrate', 'calibration-qualify') else (response.ScheduledPulseNativeRunner if native else response.ScheduledResponseRunner)(role, decoder=decode_response, manifest=selected.manifest()) if role == 'physical-forecast' or role.startswith('response') else (core.ScheduledNativeRunner if native else core.ScheduledRunner)(role, decoder=decode_core, manifest=selected.manifest()),
        record_codecs={**core.output_codecs(), ScheduledResponseNative.SCHEMA: ScheduledResponseNative, ScheduledResponseForecast.SCHEMA: ScheduledResponseForecast, ScheduledResponseScore.SCHEMA: ScheduledResponseScore, calibration.ScientificAdjudicationRecord.SCHEMA: calibration.ScientificAdjudicationRecord, **{kind.SCHEMA: kind for _, kind in inputs if kind is not None}},
        scientific_hooks=RecursiveScientificHooks(qualified_parent_assessor=qualified_parent_assessor if role == 'forecast-calibrated' else None, native_effect_slot_ids=(lambda c: (('responses' if c.operation.startswith('responses') else c.operation) + '.' + c.source.root_id,)) if native else None, scientific_operand_sha256s=operands, scientific_unit_ids=units, scientific_root_validator=scientific_root_validator, adjudication_output_id=product_id if role == 'calibration-qualify' else None),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL if role == 'calibration-qualify' else BarrierKind.FREEZE if role in ('commit', 'forecast', 'forecast-calibrated', 'physical-forecast') else BarrierKind.NONE, native_effect=native, complete_unit_census=native, native_work_preparer=(response.prepare_native_work if role.startswith('responses') else core.prepare_native_work) if native else None),
        publication_requirements=(RegisteredPublicationRequirement(NAMESPACE + '.prior-publications.v1', authenticate_prior_publications),) if role == 'commit' else (),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return selected


def operation_declarations():
    return tuple(_operation_declaration(*phase) for phase in PHASES)
