# SPDX-License-Identifier: MPL-2.0
"""One selected gas-start minimization through the existing native lifecycle."""

from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import publish_directory, publish_record, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_effects import NativeEntryRefused
from empirical_lawhood.execution.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkObservationPublicationError, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork, require_native_completion_receipt
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import GasRelaxationSelection, validate_gas_relaxation_model
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeRawSources, prepare_raw_sources
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import _absolute, accelerated_engine, authenticate_periodic_engine


CAPABILITY = 'rubisco-response.gas-start-relaxation'
GPU_CAPABILITY = 'rubisco-response.accelerated-gas-start-relaxation'
UNIT = 'unit.gp-original-1bwv-assembly'
MAX_CONFIG, MAX_MODEL, MAX_RAW_SOURCES, MAX_RETURN = 32*2**20, 512*2**20, 256*2**20, 16*2**20
BUDGET = ResourceBudget(8, 8*2**30, 0, None, 2*2**30, 4*2**30)
GPU_RESOURCE_CEILING = replace(BUDGET, memory_bytes=None, gpu_devices=1)


@dataclass(frozen=True, slots=True)
class GasRelaxationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-config'
    ACCELERATED: ClassVar[bool] = False
    config_id: str
    selection: GasRelaxationSelection
    raw_sources: ObjectIdentity
    representation_size_bytes: int
    raw_source_size_bytes: int
    implementation: RecursiveImplementationBinding
    work_directory: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for value, kind in ((self.selection, GasRelaxationSelection), (self.raw_sources, ObjectIdentity),
                (self.implementation, RecursiveImplementationBinding), (self.provenance, NumericalProducingProvenance)):
            exact(value, kind)
        _absolute(self.work_directory)
        prototype = self.selection.prototype
        if (accelerated_engine(prototype.engine) != self.ACCELERATED
                or prototype.engine.numerical_threads > BUDGET.cpu_cores
                or self.ACCELERATED and prototype.electronic.memory_megabytes*10**6 > prototype.engine.host_memory_bytes):
            raise ValueError('gas relaxation changes its selected backend, threads or host-memory allocation')
        if (type(self.representation_size_bytes) is not int or not 0 < self.representation_size_bytes <= MAX_MODEL
                or type(self.raw_source_size_bytes) is not int or not 0 < self.raw_source_size_bytes <= MAX_RAW_SOURCES
                or self.raw_sources.object_schema != PeriodicProbeRawSources.SCHEMA
                or self.raw_sources.object_version != PeriodicProbeRawSources.VERSION
                or any(getattr(self.provenance, name) != getattr(self.implementation, name) for name in (
                    'package_sources', 'code_sources_sha256', 'dependency_lock_sha256', 'observed_git_head', 'observed_checkout_clean'))):
            raise ValueError('gas relaxation changes its bounded original inputs or producing implementation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class AcceleratedGasRelaxationConfig(GasRelaxationConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-gas-relaxation-config'
    ACCELERATED: ClassVar[bool] = True


def capability_for(config):
    if type(config) is GasRelaxationConfig:
        return CAPABILITY
    if type(config) is AcceleratedGasRelaxationConfig:
        return GPU_CAPABILITY
    raise ValueError('gas relaxation requires its exact installed CPU or GPU configuration')


def resource_budget(config):
    capability_for(config)
    return replace(GPU_RESOURCE_CEILING, memory_bytes=config.selection.prototype.engine.host_memory_bytes) if config.ACCELERATED else BUDGET


@dataclass(frozen=True, slots=True)
class GasRelaxationReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-return'
    configuration: ObjectIdentity
    selection: ObjectIdentity
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.configuration, ObjectIdentity)
        exact(self.selection, ObjectIdentity)
        exact(self.files, DurableRawFileCensus)
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError('gas relaxation loses its original failure diagnostic')


def native_outputs():
    return tuple(sorted((json_output('gas-relaxation.return', GasRelaxationReturn),
        json_output('files.census', DurableRawFileCensus), raw_output('files.raw')), key=lambda row: row.output_id))


@dataclass(frozen=True, slots=True)
class GasRelaxationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-result'
    result_id: str
    returned: GasRelaxationReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    interpretation: str = 'ONE_ORIGINAL_GAS_START_ATTEMPT_NOT_A_POPULATION_OR_RATE'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for value, kind in ((self.returned, GasRelaxationReturn), (self.definition, NativeSubworkDefinition),
                (self.completion, NativeSubworkCompletion), (self.receipt, CanonicalTaskReceipt)):
            exact(value, kind)
        require_native_completion_receipt(self.completion, self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        if (self.definition.operation_id not in (CAPABILITY, GPU_CAPABILITY)
                or self.definition.configuration != self.returned.selection
                or self.returned.configuration not in self.definition.sources or self.definition.outputs != native_outputs()
                or self.definition.streams or self.completion.definition != self.definition.identity
                or self.completion.operational_status is not (OperationalStatus.SUCCEEDED if self.returned.error is None else OperationalStatus.FAILED)
                or set(self.completion.output_ids) != {row.output_id for row in native_outputs()}
                or self.completion.omitted_output_ids or self.completion.consumed_streams
                or self.completion.unconsumed_streams or self.completion.unknown_streams
                or self.receipt.run_id != self.definition.parent_contact.run_id
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids).issubset(self.receipt.input_materialization_ids)
                or self.interpretation != 'ONE_ORIGINAL_GAS_START_ATTEMPT_NOT_A_POPULATION_OR_RATE'):
            raise ValueError('gas relaxation changes its complete original native attempt, receipt or scope')
        for name, record in (('gas-relaxation.return', self.returned), ('files.census', self.returned.files)):
            key = self.receipt.task_id+'.output.'+name
            logical = [row for row in self.receipt.output_logical_artifacts if row.logical_artifact_id == key]
            physical = [row for row in self.receipt.output_materializations if row.logical_artifact_id == key]
            if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != record.SCHEMA
                    or logical[0].content_sha256 != record.fingerprint()
                    or (physical[0].physical_sha256, physical[0].size_bytes) != (record.fingerprint(), record.canonical_size_bytes())):
                raise ValueError('gas relaxation substitutes its original receipted return or file census')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


def native_input_records(config, representation, raw_sources):
    capability_for(config)
    validate_gas_relaxation_model(config.selection, representation)
    exact(raw_sources, PeriodicProbeRawSources)
    if (raw_sources.identity != config.raw_sources or representation.canonical_size_bytes() != config.representation_size_bytes
            or raw_sources.canonical_size_bytes() != config.raw_source_size_bytes
            or prepare_raw_sources(config.selection.prototype, raw_sources.topology_utf8.encode('ascii'),
                raw_sources.coordinates_utf8.encode('ascii')) != raw_sources):
        raise ValueError('gas relaxation direct input changes its complete original source bytes')
    return (('native-arrays', representation.arrays.identity, representation.arrays),
        ('native-model', representation.identity, representation),
        ('native-provenance', config.provenance.identity, config.provenance),
        ('native-selection', config.selection.identity, config.selection),
        ('native-source', raw_sources.identity, raw_sources))


def operands(config):
    return tuple(sorted({config.identity, config.selection.identity, config.selection.prototype.representation,
        config.selection.prototype.coordinates.identity, config.raw_sources, config.provenance.identity}, key=lambda row: row.object_id))


def slots(config):
    return ('native.gas-start-relaxation.'+config.fingerprint(),)


def definition_for(config, *, parent, materialization_ids):
    return NativeSubworkDefinition('gas-start-relaxation.'+config.selection.fingerprint(), capability_for(config), parent,
        config.selection.identity, operands(config), config.implementation.code_sources_sha256,
        config.implementation.dependency_lock_sha256, materialization_ids, (), native_outputs())


def native_work(context, config, parent):
    definition = definition_for(config, parent=parent,
        materialization_ids=tuple(sorted(port.materialization_id for port in context.input_ports)))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (UNIT,), slots(config), (definition,), (roster,))


def _decode(context, *, accelerated=False):
    declared = operation_declaration(accelerated=accelerated).manifest()
    config_type = AcceleratedGasRelaxationConfig if accelerated else GasRelaxationConfig
    if (context.task_id != declared.capability_key or context.permissions != declared.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != 6):
        raise ValueError('gas relaxation changes its complete direct task/input contract')
    kinds = {config_type.SCHEMA: (config_type, MAX_CONFIG), ArrayDatasetManifest.SCHEMA: (ArrayDatasetManifest, MAX_CONFIG),
        MolecularRepresentation.SCHEMA: (MolecularRepresentation, MAX_MODEL),
        GasRelaxationSelection.SCHEMA: (GasRelaxationSelection, MAX_CONFIG),
        NumericalProducingProvenance.SCHEMA: (NumericalProducingProvenance, MAX_CONFIG),
        PeriodicProbeRawSources.SCHEMA: (PeriodicProbeRawSources, MAX_RAW_SOURCES)}
    received = {}
    for port in context.input_ports:
        selected = kinds.get(port.payload_schema)
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != 'application/json'
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or port.payload_schema in received):
            raise ValueError('gas relaxation changes a complete direct exposed input')
        received[port.payload_schema] = (port, decode_canonical_bytes(port.read(selected[1]), selected[0], maximum_bytes=selected[1]))
    if set(received) != set(kinds):
        raise ValueError('gas relaxation omits a complete direct input')
    port, config = received[config_type.SCHEMA]
    if (context.resource_budget != resource_budget(config)
            or (config.config_id, config.fingerprint(), port.artifact_id)
                != (context.config.config_id, context.config.content_sha256, context.config.artifact_id)):
        raise ValueError('gas relaxation substitutes its selected configuration or resource allocation')
    representation, raw_sources = received[MolecularRepresentation.SCHEMA][1], received[PeriodicProbeRawSources.SCHEMA][1]
    for _, _, record in native_input_records(config, representation, raw_sources):
        if received[record.SCHEMA][1] != record:
            raise ValueError('gas relaxation substitutes its exact original direct input record')
    return config, representation, raw_sources


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not GasRelaxationRunner:
        raise ValueError('gas relaxation requires its installed native owner')
    config, _, _ = _decode(context, accelerated=runner.accelerated)
    return native_work(context, config, expected_parent)


class GasRelaxationRunner:
    def __init__(self, *, accelerated=False):
        if type(accelerated) is not bool:
            raise ValueError('gas relaxation requires an explicit CPU/GPU selection')
        self.accelerated = accelerated
        self.manifest = operation_declaration(accelerated=accelerated).manifest()

    def preflight(self, context):
        config, _, _ = _decode(context, accelerated=self.accelerated)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.selection.prototype.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('gas relaxation differs from its frozen accelerated_compute selection')
        engine = config.selection.prototype.engine
        authenticate_periodic_engine(engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=engine.device_memory_bytes, molecular_platform=periodic_molecular_platform(engine))

    def execute(self, context):
        raise ValueError('gas relaxation requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, raw_sources = _decode(context, accelerated=self.accelerated)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.selection.prototype.molecular)
            prepared = context.prepared_invocation
            if (context.accelerated_compute != self.accelerated or prepared is None
                    or prepared.implementation != config.implementation):
                raise ValueError('gas relaxation changes its frozen producing source or backend')
            engine = config.selection.prototype.engine
            authenticate_periodic_engine(engine)
            work = native_work(context, config, native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError('gas relaxation changes its frozen native census')
            root = Path(config.work_directory)
            root.mkdir(parents=False, exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            definition = work.definitions[0]
            completed = native_subwork.recover(definition)
            if completed is not None:
                returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'gas-relaxation.return')),
                    GasRelaxationReturn, maximum_bytes=MAX_RETURN)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('uncertain gas relaxation contact cannot be repeated')
                directory = root/definition.subwork_id
                directory.mkdir()
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                wall, cpu, self_cpu = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN), time.process_time()
                error = None
                try:
                    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_native import execute_gas_relaxation
                    invoke_native_subwork(native_subwork, entry, execute_gas_relaxation,
                        selection=config.selection, representation=representation,
                        raw_topology=raw_sources.topology_utf8.encode('ascii'), raw_coordinates=raw_sources.coordinates_utf8.encode('ascii'),
                        directory=directory)
                except (NativeEntryRefused, NativeSubworkObservationPublicationError):
                    raise
                except Exception:
                    error = traceback.format_exc()
                    with (directory/'native-error.txt').open('x') as stream:
                        stream.write(error)
                try:
                    authenticate_periodic_engine(engine, loaded=True)
                except (ValueError, OSError):
                    error = ('' if error is None else error+'\n')+traceback.format_exc()
                    with (directory/'engine-authentication-error.txt').open('x') as stream:
                        stream.write(error)
                census, archives = publish_directory(native_subwork, entry, directory, root, selected_census=directory_census(directory, root))
                returned = GasRelaxationReturn(config.identity, config.selection.identity, census, error)
                published = publish_record(native_subwork, entry, 'gas-relaxation.return', returned)
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                completed = native_subwork.complete(entry,
                    operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                        Decimal(str(time.monotonic()-wall)), Decimal(sum(m.materialization.size_bytes for m in (*archives, published)))),
                    cost_scope='One original complete neutral-gas start relaxation, fresh endpoint force, environment check and raw publication; all nested electronic calls retained; no physical trajectory time',
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    reason_codes=() if error is None else ('gas-relaxation-native-failure',))
            if returned.configuration != config.identity or returned.selection != config.selection.identity:
                raise ValueError('gas relaxation recovery substitutes its original selected call')
            capability = capability_for(config)
            result = GasRelaxationResult(capability+'.result', returned, definition, completed.completion, completed.receipt)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != capability+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('gas relaxation changes its complete original output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck('complete-original-gas-relaxation-native-census', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration(*, accelerated=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    if type(accelerated) is not bool:
        raise ValueError('gas relaxation requires an explicit installed backend')
    config_type = AcceleratedGasRelaxationConfig if accelerated else GasRelaxationConfig
    return RecursiveOperationDeclaration(capability_key=GPU_CAPABILITY if accelerated else CAPABILITY, capability_version='1.0.0',
        implementation_id=('accelerated-' if accelerated else '')+'source-bound-gas-start-relaxation-v1',
        kind=CapabilityKind.SIMULATOR, config_record_type=config_type, stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract('native-arrays', ArrayDatasetManifest.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-model', MolecularRepresentation.SCHEMA, 'application/json', MAX_MODEL),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-selection', GasRelaxationSelection.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-source', PeriodicProbeRawSources.SCHEMA, 'application/json', MAX_RAW_SOURCES)),
        outputs=(OutputTemplate('product', GasRelaxationResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-original-gas-host-inputs', 'explicit-neutral-gas-electronic-selection',
            'complete-original-returns-before-assessment', 'original-custody-no-replay'))),
        runner_factory=(lambda: GasRelaxationRunner(accelerated=True)) if accelerated else GasRelaxationRunner,
        record_codecs={kind.SCHEMA: kind for kind in (config_type, GasRelaxationSelection, GasRelaxationResult,
            MolecularRepresentation, ArrayDatasetManifest, PeriodicProbeRawSources, NumericalProducingProvenance)},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c: (UNIT,), native_effect_slot_ids=slots, scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment))
