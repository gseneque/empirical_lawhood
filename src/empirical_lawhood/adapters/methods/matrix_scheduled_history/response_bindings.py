# SPDX-License-Identifier: MPL-2.0
"""Stock scheduled physical FREEZE, Native pulse futures and independent scores."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from decimal import Decimal
from hashlib import sha256
import resource
import time

import numpy as np

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import TaskContext
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import science
from .commitment import ScheduledCommitment, ScheduledCommitmentConfig, require_publication_copy
from .continuation import full_access, full_visibility
from .forecast import ScheduledForecastSeal
from .records import NAMESPACE, ScheduledAllocation, ScheduledCausalPrefix, ScheduledCheckpoint, ScheduledNativeEvidence, ScheduledPrefixHistory, ScheduledSelection, ScheduledSource, identity
from .response_forecast import array_product, forecast
from .response_records import ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore, branch_census
from .response_science import assess_responses, native_responses
from .response_selection import ScheduledPhysicalForecastConfig, ScheduledResponseConfig, ScheduledResponseSelection

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

BLIND, PROSP = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
BASE = (('causal', ScheduledCausalPrefix), ('error-forecast', ScheduledForecastSeal),
    ('history', ScheduledPrefixHistory), ('history-arrays', None), ('physical-forecast', ScheduledResponseForecast),
    ('physical-forecast-arrays', None), ('source', ScheduledSource), ('commitment-config', ScheduledCommitmentConfig))
NATIVE_INPUTS = tuple(sorted((*BASE, ('allocation', ScheduledAllocation), ('checkpoint', ScheduledCheckpoint),
    ('commitment', ScheduledCommitment), ('coordinate', MatrixParameterCoordinate), ('provenance', NumericalProducingProvenance),
    ('response-selection', ScheduledResponseSelection), ('selection', ScheduledSelection), ('streams', MatrixHistorySeed))))
SCORE_INPUTS = tuple(sorted((*BASE, ('responses', ScheduledResponseNative), ('responses-arrays', None))))
RESPONSE_PHASES = (
    ('physical-forecast', (('causal', ScheduledCausalPrefix), ('causal-arrays', None), ('templates', None)), ScheduledResponseForecast, ScientificStage.FREEZE, True),
    ('responses', NATIVE_INPUTS, ScheduledResponseNative, ScientificStage.ACQUIRE, True),
    ('response-score', SCORE_INPUTS, ScheduledResponseScore, ScientificStage.FALSIFY, False),
    ('responses-development', NATIVE_INPUTS, ScheduledResponseNative, ScientificStage.ACQUIRE, True),
    ('response-score-development', SCORE_INPUTS, ScheduledResponseScore, ScientificStage.FALSIFY, False),
)


def config_type(role):
    return ScheduledPhysicalForecastConfig if role == 'physical-forecast' else ScheduledResponseConfig


def access(role):
    return BLIND if role == 'physical-forecast' else OutcomeAccess.DEVELOPMENT_VISIBLE if role.endswith('-development') else OutcomeAccess.EVALUATION_SEALED


def visibility(role):
    return VisibilityCeiling.DEVELOPMENT_ONLY if role.endswith('-development') else PROSP


def response_manifests():
    return tuple(row.manifest() for row in response_declarations())


def response_manifest(role):
    """Construct the current selected contract without unrelated declarations."""
    phases = tuple(phase for phase in RESPONSE_PHASES if phase[0] == role)
    if len(phases) != 1:
        raise ValueError('scheduled response requires one installed phase')
    return _response_declaration(*phases[0]).manifest()


def units(config):
    return (config.protocol.public_source.root.independent_group_id,) if type(config) is ScheduledPhysicalForecastConfig else (config.source.root.root.independent_group_id,)


def operands(config):
    return tuple(sorted({config.protocol.fingerprint(), config.protocol.public_source.source.object_fingerprint})) if type(config) is ScheduledPhysicalForecastConfig else tuple(sorted({config.source.fingerprint(), config.selection.object_fingerprint, config.commitment_config.object_fingerprint}))




def _decode(context, role):
    from .operation_bindings import BUDGET, BoundScheduledConfig, _dependency, _raw_input, require_current_commitment, require_shared_config, validate_original_prefix_receipt
    phase = next(p for p in RESPONSE_PHASES if p[0] == role)
    types = {config_type(role).SCHEMA: config_type(role), **{t.SCHEMA: t for _, t in phase[1] if t and t is not MatrixHistorySeed}}
    records, ports, streams = {}, {}, []
    if type(context) is not TaskContext or context.outcome_access is not access(role):
        raise ValueError('scheduled response refuses unsupported access before original inputs')
    try:
        for port in context.input_ports:
            if port.payload_schema in types and port.payload_schema not in records:
                records[port.payload_schema] = decode_canonical_bytes(port.read(), types[port.payload_schema], maximum_bytes=None)
                ports[port.payload_schema] = port
            elif port.payload_schema == MatrixHistorySeed.SCHEMA and role.startswith('responses'):
                streams.append((decode_canonical_bytes(port.read(), MatrixHistorySeed, maximum_bytes=None), port))
            elif port.payload_schema == MATRIX_ARRAY_SCHEMA and port.artifact_id not in ports:
                ports[port.artifact_id] = port
            else:
                raise ValueError('scheduled response receives duplicate or undeclared information operands')
        if set(records) != set(types) or sum(p.payload_schema == MATRIX_ARRAY_SCHEMA for p in context.input_ports) != sum(t is None for _, t in phase[1]):
            raise ValueError('scheduled response omits exact original typed/raw input census')
        config = records[config_type(role).SCHEMA]
        m = next(m for m in response_manifests() if m.capability_key == NAMESPACE+'.'+role)
        if (context.task_id != NAMESPACE+'.'+config.root_id+'.'+role or context.config.config_id != config.config_id
                or context.config.config_schema != config.SCHEMA or context.config.content_sha256 != config.fingerprint()
                or context.config.artifact_id != ports[config.SCHEMA].artifact_id or context.permissions != m.permissions
                or not BUDGET.contains(context.resource_budget)):
            raise ValueError('scheduled response lacks exact issued config/resource/permission scope')
        causal = records[ScheduledCausalPrefix.SCHEMA]
        _dependency(context, ports[causal.SCHEMA], config.root_id, 'project')
        if role == 'physical-forecast':
            p = config.protocol
            _raw_input(context, ports, causal.arrays, config.root_id, 'project')
            a = p.templates.array_artifact
            template = ports.get(a.artifact_id)
            if (template is None or (template.payload_schema, template.media_type, template.size_bytes, template.outcome_access,
                    template.visibility_ceiling) != (a.payload_schema, a.media_type, a.size_bytes, BLIND, PROSP)
                    or causal.source != p.public_source.source):
                raise ValueError('scheduled physical predictor substitutes exact public template/prefix identity')
            return config, None, records, ports
        reference = records[ScheduledSource.SCHEMA]
        if config.source != reference or config.operation != role:
            raise ValueError('scheduled response substitutes original native source/configuration')
        shared = records[ScheduledCommitmentConfig.SCHEMA]
        index = require_shared_config(shared, ports[shared.SCHEMA], expected=config.commitment_config)
        source_port = ports[ScheduledSource.SCHEMA]
        from empirical_lawhood.runtime.execution import WorkerInputKind
        if (source_port.kind is not WorkerInputKind.EXTERNAL or source_port.artifact_id != reference.source_id
                or source_port.outcome_access is not BLIND or source_port.visibility_ceiling is not PROSP
                or reference.root_id not in shared.selected_root_ids
                or shared.response_selection is None or config.selection != shared.response_selection.identity):
            raise ValueError('scheduled response changes its exact external source or shared response-selection pin')
        source = index.resolve(reference)
        config = BoundScheduledConfig(config, source, shared)
        protocol, panels = config.selection.validate_source(source)
        history, physical, error = records[ScheduledPrefixHistory.SCHEMA], records[ScheduledResponseForecast.SCHEMA], records[ScheduledForecastSeal.SCHEMA]
        history.validate_source(source, native_context=config.native_context); validate_original_prefix_receipt(history, context.run_id)
        if (causal.source != identity(source) or causal.history != identity(history)
                or physical.source != identity(source) or physical.causal_prefix != identity(causal)
                or physical.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or error.source != identity(source) or error.prefix != identity(causal) or error.criterion != protocol.criterion):
            raise ValueError('scheduled response loses genuine original source/prefix/physical and error forecast seals')
        for cls, owner, arrays in ((ScheduledPrefixHistory, 'prefix', history.arrays), (ScheduledResponseForecast, 'physical-forecast', physical.arrays)):
            _dependency(context, ports[cls.SCHEMA], source.root_id, owner)
            _raw_input(context, ports, arrays, source.root_id, owner)
        error_owner = 'forecast-calibrated' if error.calibration is not None else 'forecast'
        _dependency(context, ports[ScheduledForecastSeal.SCHEMA], source.root_id, error_owner,
            access=OutcomeAccess.EVALUATION_SEALED if error.calibration is not None else BLIND)
        if role.startswith('responses'):
            commitment = records[ScheduledCommitment.SCHEMA]
            require_current_commitment(commitment, shared)
            commitment.validate_source(source)
            _dependency(context, ports[ScheduledCommitment.SCHEMA], source.root_id, 'commit')
            _dependency(context, ports[ScheduledCheckpoint.SCHEMA], source.root_id, 'prefix')
            if (commitment.response_selection != config.selection.identity or records[ScheduledResponseSelection.SCHEMA] != config.selection
                    or commitment.forecast_design != error.design or records[ScheduledCheckpoint.SCHEMA] != history.checkpoint
                    or records[ScheduledAllocation.SCHEMA] != source.allocation or records[ScheduledSelection.SCHEMA] != source.specification.selection
                    or records[MatrixParameterCoordinate.SCHEMA] != source.coordinate or records[NumericalProducingProvenance.SCHEMA] != source.provenance):
                raise ValueError('scheduled Native pulse entry lacks original frozen complete source/response commitment')
            for cls, pub in ((ScheduledAllocation, source.reservation.publication), (ScheduledSelection, source.specification.publication)):
                require_publication_copy(records[cls.SCHEMA], ports[cls.SCHEMA], pub)
            expected = {(source.root.stream_identity(s).object_id, s) for s in source.root.streams}
            expected |= {(p.stream_identity(s).object_id, s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams}
            if len(streams) != 8 or {(port.artifact_id, s) for s, port in streams} != expected:
                raise ValueError('scheduled Native pulse entry changes eight actual complete group-owned streams')
        else:
            response = records[ScheduledResponseNative.SCHEMA]
            response.validate_source(source, config.selection, history, causal, physical, error, native_context=config.native_context)
            owner = 'responses-development' if role.endswith('-development') else 'responses'
            _dependency(context, ports[response.SCHEMA], source.root_id, owner, access=full_access(source), visibility=full_visibility(source))
            _raw_input(context, ports, response.arrays, source.root_id, owner, access=full_access(source), visibility=full_visibility(source))
        return config, source, records, ports
    except Exception:
        for port in context.input_ports:
            port.close()
        raise


def unpack_native(raw, protocol, panels):
    """Original custody authenticates bytes; this bounds every native NPY before load."""
    h, expected = protocol.horizon_steps[-1], {}
    for panel in panels:
        for name, count in (('primary', h), ('fine', 2*h), ('bridge', h)):
            expected['noise.'+panel.panel_id+'.'+name] = ('<c16', (count, 2, 3, 4, 4))
    for branch, view, *_ in branch_census(protocol, panels):
        n = h*(1 if view == 'PRIMARY' else 2)
        for name in ('positions', 'momenta', 'innovations', 'ticks', 'alpha_tilde'):
            shape = (n if name == 'innovations' else n+1, 2, 3, 4, 4) if name in ('positions', 'momenta', 'innovations') else (n+1, 2) if name == 'alpha_tilde' else (n+1,)
            expected['branch.'+branch+'.'+name] = ('<c16' if name in ('positions', 'momenta', 'innovations') else '<i8' if name == 'ticks' else '<f8', shape)
    from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays
    return decode_native_matrix_arrays(raw, expected)



class ScheduledResponseRunner:
    def __init__(self, role, *, decoder=None, manifest=None):
        self.role = role
        self.manifest = manifest if manifest is not None else next(m for m in response_manifests() if m.capability_key == NAMESPACE+'.'+role)
        self._decoder = _decode if decoder is None else decoder

    def _decode(self, context):
        return self._decoder(context, self.role)

    def execute(self, context):
        from .operation_bindings import _outputs
        try:
            config, source, records, ports = self._decode(context)
            if self.role.startswith('responses'):
                raise ValueError('scheduled responses require stock issued Native authorization before effects')
            if self.role == 'physical-forecast':
                causal = records[ScheduledCausalPrefix.SCHEMA]
                arrays = decode_matrix_arrays(ports[causal.arrays.array_artifact.artifact_id].read(), causal.arrays)
                templates = decode_matrix_arrays(ports[config.protocol.templates.array_artifact.artifact_id].read(), config.protocol.templates)
                output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
                raw, product = forecast(config.protocol, causal, arrays, templates, artifact_id=output.logical_artifact_id)
                return _outputs(context, product, raw)
            history, physical, response = records[ScheduledPrefixHistory.SCHEMA], records[ScheduledResponseForecast.SCHEMA], records[ScheduledResponseNative.SCHEMA]
            prefix = science.consume_prefix(source, history.arrays, ports[history.arrays.array_artifact.artifact_id].read())
            frozen = decode_matrix_arrays(ports[physical.arrays.array_artifact.artifact_id].read(), physical.arrays)
            arrays = decode_matrix_arrays(ports[response.arrays.array_artifact.artifact_id].read(), response.arrays)
            protocol, panels = config.selection.validate_source(source)
            product = assess_responses(source, records[ScheduledCausalPrefix.SCHEMA], history, prefix,
                records[ScheduledForecastSeal.SCHEMA], physical, frozen, protocol, panels, response, arrays, score_id='score.'+source.root_id)
            return _outputs(context, product)
        finally:
            for port in context.input_ports:
                port.close()


def _initial_native_work(context, config, source, records, ports, role, parent):
    """The original complete potential pulse child; non-use never enters it."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    protocol, panels = config.selection.validate_source(source)
    history, causal, physical, error = (records[c.SCHEMA] for c in (ScheduledPrefixHistory, ScheduledCausalPrefix, ScheduledResponseForecast, ScheduledForecastSeal))
    if (parent.run_id, parent.task_id, parent.attempt_id, parent.input_materialization_ids, parent.implementation_commit) != (
            context.run_id, context.task_id, context.attempt_id, context.input_materialization_ids, source.provenance.observed_git_head):
        raise ValueError('scheduled pulse changes actual issued ordinary parent contact')
    prefix = science.consume_prefix(source, history.arrays, ports[history.arrays.array_artifact.artifact_id].read())
    frozen = decode_matrix_arrays(ports[physical.arrays.array_artifact.artifact_id].read(), physical.arrays)
    streams = tuple(sorted((*tuple(source.root.stream_identity(s) for s in source.root.streams),
        *(p.stream_identity(s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams)), key=lambda o: o.object_id))
    configuration, parent_task, operation, shared_sources = config.native_context.contract(role)
    if (parent_task != context.task_id
            or (configuration.object_id, configuration.object_schema, configuration.object_fingerprint) !=
               (context.config.config_id, context.config.config_schema, context.config.content_sha256)):
        raise ValueError('scheduled pulse changes actual parent configuration identity')
    definition = NativeSubworkDefinition('responses.'+source.root_id, operation, parent,
        configuration, tuple(sorted((*shared_sources, identity(history), identity(history.checkpoint), identity(causal), identity(error),
            ObjectIdentity.from_record(physical.forecast_id, physical), config.selection.identity), key=lambda o: o.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, context.input_materialization_ids, streams,
        (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    work = PreparedNativeWork(parent, (source.root.root.independent_group_id,),
        ('responses.'+source.root_id,), (definition,), (roster,))
    return work, protocol, panels, history, causal, physical, error, prefix, frozen


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ScheduledPulseNativeRunner or runner.role not in ('responses', 'responses-development'):
        raise ValueError('scheduled pulse preparation requires its installed original native phase')
    config, source, records, ports = runner._decode(context)
    return _initial_native_work(context, config, source, records, ports, runner.role, expected_parent)[0]


def execute_paired_response_native_work(source, work, native_subwork, *, protocol, panels, history, prefix, frozen,
        selection: ObjectIdentity, progress=None):
    definition, = work.definitions
    streams = definition.streams
    completed = native_subwork.recover(definition)
    if completed is not None:
        if completed.state is not NativeSubworkState.COMPLETED or completed.receipt is None or completed.completion.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError('scheduled pulse refuses unknown/failed Native contact replay')
        raw = b''.join(native_subwork.iter_completed_output(definition, 'arrays'))
        arrays = unpack_native(raw, protocol, panels)
    else:
        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
            raise ValueError('scheduled pulse refuses unreceipted Native contact replay')
        native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)
        cpu, wall = time.process_time(), time.monotonic()
        try:
            arrays = invoke_native_subwork(native_subwork, entry, native_responses,
                source, history, prefix, protocol, panels, frozen,
                **({"on_step": lambda count: progress.advance(Decimal(count))} if progress is not None else {}))
        except (ArithmeticError, MemoryError, ValueError):
            native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), None),
                cost_scope='scheduled complete paired pulse collection nested in ordinary task', unknown_streams=streams,
                reason_codes=('scheduled-pulse-native-failure',))
            raise
        raw, _ = array_product(protocol, arrays, role='RESPONSES', artifact_id='native-response-arrays',
            producers=(identity(source), selection), access=full_access(source), visibility=full_visibility(source))
        native_subwork.publish_output(entry, 'arrays', (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
            expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
        start, stop = source.policy.cutoff_tick, source.policy.cutoff_tick+protocol.horizon_steps[-1]
        consumed = tuple(s for s in streams if s.object_id.endswith(('preparation-coarse-driver', 'preparation-fine-bridge')) and start < source.coordinate.ramp_ticks
            or s.object_id.endswith(('autonomous-coarse-driver', 'autonomous-fine-bridge')) and stop > max(start, source.coordinate.ramp_ticks))
        completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), Decimal(len(raw))),
            cost_scope='scheduled complete paired pulse collection nested in ordinary task', consumed_streams=consumed,
            unconsumed_streams=tuple(s for s in streams if s not in consumed), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return raw, arrays, definition, completed


class ScheduledPulseNativeRunner(ScheduledResponseRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        from .operation_bindings import _outputs
        try:
            config, source, records, ports = self._decode(context)
            parent = native_subwork.parent_contact
            work, protocol, panels, history, causal, physical, error, prefix, frozen = _initial_native_work(
                context, config, source, records, ports, self.role, parent)
            native = ()
            if physical.disposition != 'AVAILABLE' or causal.disposition != 'AVAILABLE':
                arrays = {'unentered_branches': np.arange(48, dtype='<i8')}
                disposition = 'NO_ORIGIN' if causal.disposition == 'NO_ORIGIN' else 'INSTRUMENT_UNRESOLVED' if physical.disposition == 'INSTRUMENT_UNRESOLVED' else 'UNEVALUABLE'
            else:
                raw, arrays, definition, completed = execute_paired_response_native_work(
                    source, work, native_subwork, protocol=protocol, panels=panels, history=history,
                    prefix=prefix, frozen=frozen, selection=config.selection.identity, progress=progress)
                native = (ScheduledNativeEvidence(definition, completed.completion, completed.receipt),)
                disposition = 'COMPLETED'
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = array_product(protocol, arrays, role='RESPONSES', artifact_id=output.logical_artifact_id,
                producers=(identity(source), config.selection.identity, ObjectIdentity.from_record(physical.forecast_id, physical), identity(error)),
                access=full_access(source), visibility=full_visibility(source), **({'raw': raw} if native else {}))
            product = ScheduledResponseNative('responses.'+source.root_id, identity(source), identity(causal),
                ObjectIdentity.from_record(physical.forecast_id, physical), identity(error), ObjectIdentity.from_record(protocol.protocol_id, protocol),
                operand, tuple(row[0] for row in branch_census(protocol, panels)), native, disposition,
                () if native else ('complete48-pulse-slots-not-entered-'+disposition.lower(),))
            product.validate_source(source, config.selection, history, causal, physical, error, native_context=config.native_context)
            return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()




def _response_declaration(role, inputs, out, stage, raw):
    from .operation_bindings import BUDGET
    from .qualification import scientific_root_validator
    outputs = (OutputTemplate('product', out.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),)
    if raw:
        outputs = (OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'), *outputs)
    native = role.startswith('responses')
    return RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=NAMESPACE + '.scheduled-original-' + role + '.v1',
        kind=CapabilityKind.SIMULATOR if role.startswith('responses') else CapabilityKind.EXPERIMENT_DESIGNER if role == 'physical-forecast' else CapabilityKind.FALSIFIER,
        config_record_type=config_type(role),
        stage=stage,
        input_ports=tuple((RecursivePortContract(n, t.SCHEMA if t else MATRIX_ARRAY_SCHEMA, 'application/json' if t else 'application/x-npz', None if t else MAXIMUM_MATRIX_ARRAY_BYTES, minimum_count=8 if n == 'streams' else 1, maximum_count=8 if n == 'streams' else 1) for n, t in inputs)),
        outputs=outputs,
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS if role == 'physical-forecast' else CapabilityPermission.READ_DEVELOPMENT if role.endswith('-development') else CapabilityPermission.READ_SEALED_OUTCOMES))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE if role.endswith('-development') else EvidenceCeiling.RESPONSE,
        outcome_access=access(role),
        visibility_ceiling=visibility(role),
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('complete-paired48-pulse-branch-census', 'literal-full192-and-conditioned-ou-reference', 'origin-fixed48-receivers-and-original-seals'))),
        runner_factory=lambda: ScheduledPulseNativeRunner(role) if native else ScheduledResponseRunner(role),
        record_codecs={**{kind.SCHEMA: kind for kind in (ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore)}, **{kind.SCHEMA: kind for _, kind in inputs if kind is not None}},
        scientific_hooks=RecursiveScientificHooks(native_effect_slot_ids=(lambda c: ('responses.' + c.source.root_id,)) if native else None, scientific_operand_sha256s=operands, scientific_unit_ids=units, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role == 'physical-forecast' else BarrierKind.NONE, native_effect=native, complete_unit_census=native, native_work_preparer=prepare_native_work if native else None),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )


def response_declarations():
    return tuple(_response_declaration(*phase) for phase in RESPONSE_PHASES)
