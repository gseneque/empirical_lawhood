# SPDX-License-Identifier: MPL-2.0
"""One complete periodic numerical point through the existing native lifecycle.

The study author derives the whole point census. Each ordinary task retains one
original call, including failures. Completed recovery performs no native call.
"""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import publish_directory, publish_record, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest, capture_native_return
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_effects import NativeEntryRefused
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkObservationPublicationError, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import PeriodicControlProtocol, PeriodicForceActionProtocol, PeriodicControlPoint, point_coordinates, validate_control_prototype, validate_control_point
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET, UNIT, GRADIENT_UNIT, MAX_CONFIG, MAX_MODEL, MAX_RAW_SOURCES, MAX_RETURN, PeriodicProbeConfig, AcceleratedPeriodicProbeConfig, GPU_RESOURCE_CEILING, resource_budget as probe_resource_budget, PeriodicProbeNativeReturn, PeriodicProbeRawSources, PeriodicProbeResult, native_input_records as original_probe_inputs, probe_outputs
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, authenticate_periodic_engine


CAPABILITY = 'rubisco-response.periodic-numerical-point'
GPU_CAPABILITY = 'rubisco-response.accelerated-periodic-numerical-point'
ACTION_CAPABILITY = 'rubisco-response.periodic-force-action-point'
GPU_ACTION_CAPABILITY = 'rubisco-response.accelerated-periodic-force-action-point'


@dataclass(frozen=True, slots=True)
class PeriodicControlConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-control-config'
    ACCELERATED: ClassVar[bool] = False
    FORCE_ACTIONS: ClassVar[bool] = False
    config_id: str
    original: PeriodicProbeConfig
    protocol: PeriodicControlProtocol
    point: PeriodicControlPoint

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.original, AcceleratedPeriodicProbeConfig if self.ACCELERATED else PeriodicProbeConfig)
        exact(self.protocol, PeriodicForceActionProtocol if self.FORCE_ACTIONS else PeriodicControlProtocol)
        exact(self.point, PeriodicControlPoint)
        validate_control_prototype(self.protocol, self.original.selection)
        validate_control_point(self.protocol, self.point)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class AcceleratedPeriodicControlConfig(PeriodicControlConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-periodic-control-config'
    ACCELERATED: ClassVar[bool] = True
    original: AcceleratedPeriodicProbeConfig


@dataclass(frozen=True, slots=True)
class PeriodicForceActionConfig(PeriodicControlConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-force-action-config'
    FORCE_ACTIONS: ClassVar[bool] = True
    protocol: PeriodicForceActionProtocol


@dataclass(frozen=True, slots=True)
class AcceleratedPeriodicForceActionConfig(PeriodicForceActionConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-periodic-force-action-config'
    ACCELERATED: ClassVar[bool] = True
    original: AcceleratedPeriodicProbeConfig


def config_kind(*, accelerated=False, force_actions=False):
    if type(accelerated) is not bool or type(force_actions) is not bool:
        raise TypeError('periodic controls require an explicit Boolean backend')
    if force_actions:
        return AcceleratedPeriodicForceActionConfig if accelerated else PeriodicForceActionConfig
    return AcceleratedPeriodicControlConfig if accelerated else PeriodicControlConfig


def capability_for(config):
    if type(config) is PeriodicControlConfig:
        return CAPABILITY
    if type(config) is AcceleratedPeriodicControlConfig:
        return GPU_CAPABILITY
    if type(config) is PeriodicForceActionConfig:
        return ACTION_CAPABILITY
    if type(config) is AcceleratedPeriodicForceActionConfig:
        return GPU_ACTION_CAPABILITY
    raise TypeError('periodic controls require the exact selected CPU or GPU configuration')


def resource_budget(config):
    capability_for(config)
    return probe_resource_budget(config.original)


def node_id(config):
    return capability_for(config)+'.point.'+f'{config.point.ordinal:08d}'


def selected_request(config):
    return CoupledEvaluationRequest(config.point.point_id+'.evaluation', config.protocol.identity,
        config.original.selection.representation, config.point.identity, config.original.provenance.identity,
        config.protocol.physical_atom_count, gradient_unit=GRADIENT_UNIT)


def native_input_records(config, representation, sources):
    capability_for(config)
    # Reuse the original source/model size and complete Amber source joins.
    original_probe_inputs(config.original, representation, sources)
    prototype = config.original.selection
    request = selected_request(config)
    return (('native-arrays', representation.arrays.identity, representation.arrays),
        ('native-model', representation.identity, representation),
        ('native-protocol', config.protocol.identity, config.protocol),
        ('native-prototype', prototype.identity, prototype),
        ('native-provenance', config.original.provenance.identity, config.original.provenance),
        ('native-point', config.point.identity, config.point),
        ('native-request', request.identity, request), ('native-source', sources.identity, sources))


def operands(config):
    return tuple(sorted({config.identity, config.original.selection.identity, config.protocol.identity,
        config.point.identity, config.original.selection.representation, config.original.selection.coordinates.identity,
        config.original.raw_sources, config.original.provenance.identity}, key=lambda r:r.object_id))


def slots(config):
    return ('native.periodic-numerical-point.'+config.fingerprint(),)


def definition_for(config, *, parent, materialization_ids):
    return NativeSubworkDefinition(config.point.point_id, 'rubisco-response.molecular-force-probe', parent,
        selected_request(config).identity, operands(config), config.original.implementation.code_sources_sha256,
        config.original.implementation.dependency_lock_sha256, materialization_ids, (), probe_outputs())


def native_work(context, config, parent):
    definition = definition_for(config, parent=parent,
        materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (UNIT,), slots(config), (definition,), (roster,))


def _decode(context, *, accelerated=False, force_actions=False):
    declared = operation_declaration(accelerated=accelerated, force_actions=force_actions).manifest()
    config_type = config_kind(accelerated=accelerated, force_actions=force_actions)
    protocol_type = PeriodicForceActionProtocol if force_actions else PeriodicControlProtocol
    if (context.permissions != declared.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != 9):
        raise ValueError('periodic numerical point changes its complete task/input contract')
    kinds = {config_type.SCHEMA:(config_type, MAX_CONFIG),
        ArrayDatasetManifest.SCHEMA:(ArrayDatasetManifest, MAX_CONFIG),
        MolecularRepresentation.SCHEMA:(MolecularRepresentation, MAX_MODEL),
        protocol_type.SCHEMA:(protocol_type, MAX_CONFIG),
        PeriodicProbeSelection.SCHEMA:(PeriodicProbeSelection, MAX_CONFIG),
        NumericalProducingProvenance.SCHEMA:(NumericalProducingProvenance, MAX_CONFIG),
        PeriodicControlPoint.SCHEMA:(PeriodicControlPoint, MAX_CONFIG),
        CoupledEvaluationRequest.SCHEMA:(CoupledEvaluationRequest, MAX_CONFIG),
        PeriodicProbeRawSources.SCHEMA:(PeriodicProbeRawSources, MAX_RAW_SOURCES)}
    received = {}
    for port in context.input_ports:
        selected = kinds.get(port.payload_schema)
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != 'application/json'
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or port.payload_schema in received):
            raise ValueError('periodic numerical point changes a complete direct exposed input')
        received[port.payload_schema] = (port, decode_canonical_bytes(port.read(selected[1]), selected[0], maximum_bytes=selected[1]))
    if set(received) != set(kinds):
        raise ValueError('periodic numerical point omits a complete direct input')
    port, config = received[config_type.SCHEMA]
    if context.resource_budget != resource_budget(config):
        raise ValueError('periodic control changes its selected resource allocation')
    if ((config.config_id, config.fingerprint(), port.artifact_id) !=
            (context.config.config_id, context.config.content_sha256, context.config.artifact_id)
            or context.task_id != node_id(config)):
        raise ValueError('periodic numerical point substitutes its selected configuration or node')
    representation, sources = received[MolecularRepresentation.SCHEMA][1], received[PeriodicProbeRawSources.SCHEMA][1]
    for _, _, record in native_input_records(config, representation, sources):
        if received[record.SCHEMA][1] != record:
            raise ValueError('periodic numerical point substitutes an exact original direct operand')
    return config, representation, sources


def checked_coordinates(config, representation, sources):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    raw = original_coordinates(config.original.selection, representation, sources)
    return point_coordinates(config.protocol, config.point, raw)


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) not in (PeriodicControlRunner, AcceleratedPeriodicControlRunner,
            PeriodicForceActionRunner, AcceleratedPeriodicForceActionRunner):
        raise ValueError('periodic numerical point requires its installed native owner')
    config, representation, sources = _decode(context, accelerated=runner.accelerated, force_actions=runner.force_actions)
    checked_coordinates(config, representation, sources)
    return native_work(context, config, expected_parent)


def run_periodic_point_subwork(*, config, representation, sources, native_subwork, definition,
        request, root, native_callable=None, native_options=None, cost_scope=None):
    """Reuse the original point entry, complete raw capture, publication and recovery."""
    original = config.original
    completed = native_subwork.recover(definition)
    if completed is not None:
        returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'probe.return')),
            PeriodicProbeNativeReturn, maximum_bytes=MAX_RETURN)
    else:
        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
            raise ValueError('uncertain periodic numerical contact cannot be repeated')
        if original.ACCELERATED:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=original.selection.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(original.selection.engine))
        directory = root/definition.subwork_id
        directory.mkdir()
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)
        wall, cpu, self_cpu = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN), time.process_time()
        values, raw_return, error = None, None, None
        try:
            if native_callable is None:
                from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import execute_periodic_control
                execute = execute_periodic_control
            else:
                execute = native_callable
            values = invoke_native_subwork(native_subwork, entry, execute,
                prototype=original.selection, protocol=config.protocol, point=config.point,
                representation=representation, sources=sources, directory=directory,
                **({} if native_options is None else native_options))
        except (NativeEntryRefused, NativeSubworkObservationPublicationError):
            raise
        except Exception:
            error = traceback.format_exc()
            with (directory/'native-error.txt').open('x') as stream:
                stream.write(error)
        if values is not None:
            raw_return = capture_native_return(request, values['energy_hartree'], values['gradient_hartree_per_bohr'], native_subwork, entry)
            if raw_return.capture_failures:
                error = 'The original numerical call returned; raw capture is incomplete: '+repr(raw_return.capture_failures)
        try:
            authenticate_periodic_engine(original.selection.engine, loaded=True)
        except (ValueError, OSError):
            error = ('' if error is None else error+'\n')+traceback.format_exc()
            with (directory/'engine-authentication-error.txt').open('x') as stream:
                stream.write(error)
        census, archive_manifests = publish_directory(native_subwork, entry, directory, root, selected_census=directory_census(directory, root))
        returned = PeriodicProbeNativeReturn(config.point.identity, request.identity, census, raw_return, error)
        return_manifest = publish_record(native_subwork, entry, 'probe.return', returned)
        retained_bytes = sum(m.materialization.size_bytes for m in (*archive_manifests, return_manifest))
        if raw_return is not None:
            retained_bytes += raw_return.canonical_size_bytes()
            retained_bytes += sum(row.artifact_manifest.materialization.size_bytes
                for row in (raw_return.energy, raw_return.gradient) if row is not None)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        completed = native_subwork.complete(entry,
            operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
            cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                Decimal(str(time.monotonic()-wall)), Decimal(retained_bytes)),
            cost_scope=cost_scope or 'One complete MM construction and one prospectively selected periodic numerical E/G attempt, final source check and publication; published payload bytes exclude working copies and control records; peak RSS spans worker lifetime; no physical dynamics time',
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            reason_codes=() if error is None else ('periodic-control-native-or-capture-failure',))
    if returned.selection != config.point.identity or returned.request != request.identity:
        raise ValueError('periodic numerical recovery substitutes its exact original point')
    return returned, completed


class PeriodicControlRunner:
    accelerated = False
    force_actions = False

    def __init__(self):
        self.manifest = operation_declaration(accelerated=self.accelerated, force_actions=self.force_actions).manifest()

    def preflight(self, context):
        config, representation, sources = _decode(context, accelerated=self.accelerated, force_actions=self.force_actions)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.original.selection.molecular)
        require_current_periodic_mm_settings(config.point.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('periodic control backend differs from accelerated_compute')
        checked_coordinates(config, representation, sources)
        authenticate_periodic_engine(config.original.selection.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=config.original.selection.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(config.original.selection.engine))

    def execute(self, context):
        raise ValueError('periodic numerical point requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, sources = _decode(context, accelerated=self.accelerated, force_actions=self.force_actions)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.original.selection.molecular)
            require_current_periodic_mm_settings(config.point.molecular)
            if context.accelerated_compute != self.accelerated:
                raise ValueError('periodic control backend differs from accelerated_compute')
            original = config.original
            prepared = context.prepared_invocation
            if prepared is None or prepared.implementation != original.implementation:
                raise ValueError('periodic numerical point changes its frozen producing source')
            checked_coordinates(config, representation, sources)
            authenticate_periodic_engine(original.selection.engine)
            work = native_work(context, config, native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError('periodic numerical point changes its frozen native census')
            root = Path(original.work_directory)
            root.mkdir(parents=False, exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            definition, request = work.definitions[0], selected_request(config)
            returned, completed = run_periodic_point_subwork(config=config, representation=representation,
                sources=sources, native_subwork=native_subwork, definition=definition, request=request, root=root)
            result = PeriodicProbeResult(node_id(config)+'.result', request, returned, definition, completed.completion, completed.receipt)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != node_id(config)+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('periodic numerical point changes its complete output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck('complete-original-periodic-control-point', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


class AcceleratedPeriodicControlRunner(PeriodicControlRunner):
    accelerated = True


class PeriodicForceActionRunner(PeriodicControlRunner):
    force_actions = True


class AcceleratedPeriodicForceActionRunner(PeriodicForceActionRunner):
    accelerated = True


def operation_declaration(*, accelerated=False, force_actions=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_translation import prepare_root, validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    config_type = config_kind(accelerated=accelerated, force_actions=force_actions)
    protocol_type = PeriodicForceActionProtocol if force_actions else PeriodicControlProtocol
    if force_actions:
        capability = GPU_ACTION_CAPABILITY if accelerated else ACTION_CAPABILITY
        implementation = 'accelerated-original-periodic-force-action-point-v1' if accelerated else 'original-periodic-force-action-point-v1'
        runner = AcceleratedPeriodicForceActionRunner if accelerated else PeriodicForceActionRunner
    else:
        capability = GPU_CAPABILITY if accelerated else CAPABILITY
        implementation = 'accelerated-original-periodic-numerical-point-v1' if accelerated else 'original-prospective-periodic-numerical-point-v1'
        runner = AcceleratedPeriodicControlRunner if accelerated else PeriodicControlRunner
    return RecursiveOperationDeclaration(capability_key=capability, capability_version='1.0.0',
        implementation_id=implementation, kind=CapabilityKind.SIMULATOR,
        config_record_type=config_type, stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract('native-arrays', ArrayDatasetManifest.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-model', MolecularRepresentation.SCHEMA, 'application/json', MAX_MODEL),
            RecursivePortContract('native-point', PeriodicControlPoint.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-protocol', protocol_type.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-prototype', PeriodicProbeSelection.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-request', CoupledEvaluationRequest.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-source', PeriodicProbeRawSources.SCHEMA, 'application/json', MAX_RAW_SOURCES)),
        outputs=(OutputTemplate('product', PeriodicProbeResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-direct-original-inputs', 'complete-prospective-numerical-census',
            'raw-return-before-assessment', 'original-custody-no-replay'))),
        runner_factory=runner, record_codecs={c.SCHEMA:c for c in (config_type,
            protocol_type, PeriodicControlPoint, PeriodicProbeSelection, PeriodicProbeRawSources,
            PeriodicProbeResult, MolecularRepresentation, NumericalProducingProvenance, ArrayDatasetManifest, CoupledEvaluationRequest)},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,), native_effect_slot_ids=slots,
            scientific_root_preparer=prepare_root, scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment))
