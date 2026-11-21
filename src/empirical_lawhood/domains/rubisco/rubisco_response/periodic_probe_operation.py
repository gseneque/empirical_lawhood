# SPDX-License-Identifier: MPL-2.0
"""Single periodic force probe through recchain's existing native lifecycle."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import publish_directory, publish_record, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest, RawCoupledReturn, capture_native_return
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
from empirical_lawhood.storage.contracts.recursive_storage_codecs import RecursiveStorageCodec
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_native import MolecularForceProbe, force_probe_definition, force_probe_request
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, _absolute, authenticate_periodic_engine, validate_periodic_probe_model, prepare_periodic_probe_selection, accelerated_engine
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import DENSITY_SCHEMA, MAX_DENSITY_BYTES, PeriodicDensitySeed, read_density_bytes, validate_density_prototype


CAPABILITY = 'rubisco-response.periodic-force-probe'
RESTART_CAPABILITY = 'rubisco-response.periodic-force-restart'
GPU_CAPABILITY = 'rubisco-response.periodic-force-probe-cuda'
GPU_RESTART_CAPABILITY = 'rubisco-response.periodic-force-restart-cuda'
UNIT = 'unit.gp-original-1bwv-assembly'
GRADIENT_UNIT = 'Eh/PySCF-Bohr-0.52917721092-A'
MAX_CONFIG = 32*2**20
MAX_MODEL = 512*2**20
MAX_RAW_SOURCES = 256*2**20
MAX_RETURN = 16*2**20
BUDGET = ResourceBudget(8,8*2**30,0,None,2*2**30,4*2**30)
GPU_RESOURCE_CEILING = replace(BUDGET, memory_bytes=None, gpu_devices=1)


@dataclass(frozen=True, slots=True)
class PeriodicProbeRawSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-raw-sources'
    source_id: str
    topology_utf8: str
    coordinates_utf8: str

    def __post_init__(self):
        validate_stable_id(self.source_id)
        for value in (self.topology_utf8,self.coordinates_utf8):
            if type(value) is not str or not value or not value.isascii():
                raise ValueError('periodic force source needs both complete original ASCII Amber operands')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.source_id,self)


def prepare_raw_sources(selection, raw_topology, raw_coordinates):
    exact(selection,PeriodicProbeSelection)
    if (type(raw_topology) is not bytes or type(raw_coordinates) is not bytes
            or sha256(raw_topology).hexdigest() != selection.cell.raw_topology.object_fingerprint
            or sha256(raw_coordinates).hexdigest() != selection.cell.raw_coordinates.object_fingerprint):
        raise ValueError('periodic force source substitutes original selected Amber bytes')
    digest = sha256(raw_topology+raw_coordinates).hexdigest()
    return PeriodicProbeRawSources('source.periodic-probe.'+digest,raw_topology.decode('ascii'),raw_coordinates.decode('ascii'))


@dataclass(frozen=True, slots=True)
class PeriodicProbeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-config'
    ACCELERATED: ClassVar[bool] = False
    config_id: str
    selection: PeriodicProbeSelection
    raw_sources: ObjectIdentity
    representation_size_bytes: int
    raw_source_size_bytes: int
    implementation: RecursiveImplementationBinding
    work_directory: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for value,kind in ((self.selection,PeriodicProbeSelection),(self.raw_sources,ObjectIdentity),
                          (self.implementation,RecursiveImplementationBinding),(self.provenance,NumericalProducingProvenance)):
            exact(value,kind)
        _absolute(self.work_directory)
        if accelerated_engine(self.selection.engine) != self.ACCELERATED:
            raise ValueError('periodic force configuration changes its declared CPU/GPU numerical engine')
        if self.ACCELERATED and self.selection.electronic.memory_megabytes*10**6 > self.selection.engine.host_memory_bytes:
            raise ValueError('periodic electronic workspace exceeds the selected host-memory allocation')
        if self.selection.engine.numerical_threads > BUDGET.cpu_cores:
            raise ValueError('periodic force threads exceed the selected operation CPU allocation')
        if (type(self.representation_size_bytes) is not int or not 0 < self.representation_size_bytes <= MAX_MODEL
                or type(self.raw_source_size_bytes) is not int or not 0 < self.raw_source_size_bytes <= MAX_RAW_SOURCES):
            raise ValueError('periodic force configuration omits its exact bounded full input sizes')
        if (self.raw_sources.object_schema != PeriodicProbeRawSources.SCHEMA
                or self.raw_sources.object_version != PeriodicProbeRawSources.VERSION
                or any(getattr(self.provenance,name) != getattr(self.implementation,name) for name in (
                    'package_sources','code_sources_sha256','dependency_lock_sha256','observed_git_head','observed_checkout_clean'))):
            raise ValueError('periodic force configuration changes its source/provenance selection')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id,self)


@dataclass(frozen=True, slots=True)
class PeriodicRestartConfig(PeriodicProbeConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-restart-config'
    seed: PeriodicDensitySeed

    def __post_init__(self):
        PeriodicProbeConfig.__post_init__(self)
        validate_density_prototype(self.seed, self.selection, allow_backend_change=self.ACCELERATED)
        if self.seed.identity not in self.selection.sources:
            raise ValueError('periodic restart omits its density seed from the scientific request identity')


@dataclass(frozen=True, slots=True)
class AcceleratedPeriodicProbeConfig(PeriodicProbeConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-periodic-probe-config'
    ACCELERATED: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class AcceleratedPeriodicRestartConfig(PeriodicRestartConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-periodic-restart-config'
    ACCELERATED: ClassVar[bool] = True


def config_kind(*, restart=False, accelerated=False):
    return {(False, False): PeriodicProbeConfig, (True, False): PeriodicRestartConfig,
        (False, True): AcceleratedPeriodicProbeConfig, (True, True): AcceleratedPeriodicRestartConfig}[(restart, accelerated)]


def capability_for(config):
    selected = {PeriodicProbeConfig: CAPABILITY, PeriodicRestartConfig: RESTART_CAPABILITY,
        AcceleratedPeriodicProbeConfig: GPU_CAPABILITY, AcceleratedPeriodicRestartConfig: GPU_RESTART_CAPABILITY}
    try:
        return selected[type(config)]
    except KeyError as error:
        raise ValueError('periodic force requires its exact cold or checkpoint-seeded configuration') from error


def is_restart(config):
    capability_for(config)
    return type(config) in (PeriodicRestartConfig, AcceleratedPeriodicRestartConfig)


def resource_budget(config):
    capability_for(config)
    return (replace(GPU_RESOURCE_CEILING, memory_bytes=config.selection.engine.host_memory_bytes)
            if config.ACCELERATED else BUDGET)


def restart_selection(seed, prototype):
    validate_density_prototype(seed, prototype, allow_backend_change=accelerated_engine(prototype.engine))
    digest = sha256((seed.fingerprint()+prototype.fingerprint()).encode('ascii')).hexdigest()
    return replace(prototype, selection_id='selection.periodic-restart.'+digest,
        sources=tuple(sorted({*prototype.sources, seed.identity}, key=lambda row:row.object_id)))


def validate_force_selection(selection, representation, seed=None):
    if seed is None:
        return validate_periodic_probe_model(selection, representation)
    prototype = prepare_periodic_probe_selection(representation=representation, path=selection.path,
        cell=selection.cell, electronic=selection.electronic, molecular=selection.molecular, engine=selection.engine)
    if selection != restart_selection(seed, prototype):
        raise ValueError('periodic restart changes its complete molecular model or exact selected density seed')


def validate_density_stream(source, request, *, size):
    from empirical_lawhood.storage.artifact_stream_primitives import ArtifactIdentityConflict
    if (request.payload_schema != DENSITY_SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != 'application/octet-stream' or request.semantic_validation is not None
            or not 0 < size <= MAX_DENSITY_BYTES or size % 8):
        raise ArtifactIdentityConflict('checkpoint density changes its bounded binary64 transport contract')


DENSITY_CODEC = RecursiveStorageCodec('rubisco.checkpoint-density.f64', DENSITY_SCHEMA, '1.0.0',
    ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', '.bin', validate_density_stream, MAX_DENSITY_BYTES)


@dataclass(frozen=True, slots=True)
class PeriodicProbeNativeReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-native-return'
    selection: ObjectIdentity
    request: ObjectIdentity
    files: DurableRawFileCensus
    returned: RawCoupledReturn | None
    error: str | None

    def __post_init__(self):
        exact(self.selection,ObjectIdentity)
        exact(self.request,ObjectIdentity)
        exact(self.files,DurableRawFileCensus)
        if self.returned is not None:
            exact(self.returned,RawCoupledReturn)
            if self.returned.request != self.request:
                raise ValueError('periodic force return substitutes its exact raw evaluation request')
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError('periodic force native failure loses its actual diagnostic')
        if self.error is None and (self.returned is None or self.returned.capture_failures):
            raise ValueError('periodic force success omits its complete original captured return')


@dataclass(frozen=True, slots=True)
class PeriodicProbeResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-result'
    result_id: str
    request: CoupledEvaluationRequest
    returned: PeriodicProbeNativeReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    interpretation: str = 'ORIGINAL_PERIODIC_FORCE_ATTEMPT_REQUIRES_INDEPENDENT_NUMERICAL_AND_PHYSICAL_ASSESSMENT'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for value,kind in ((self.request,CoupledEvaluationRequest),(self.returned,PeriodicProbeNativeReturn),
                          (self.definition,NativeSubworkDefinition),(self.completion,NativeSubworkCompletion),
                          (self.receipt,CanonicalTaskReceipt)):
            exact(value,kind)
        require_native_completion_receipt(self.completion,self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        if (self.returned.request != self.request.identity or self.definition.configuration != self.request.identity
                or self.completion.definition != self.definition.identity
                or self.request.gradient_unit != GRADIENT_UNIT
                or self.definition.operation_id != 'rubisco-response.molecular-force-probe'
                or self.definition.outputs != probe_outputs()
                or self.completion.operational_status is not (OperationalStatus.SUCCEEDED if self.returned.error is None else OperationalStatus.FAILED)
                or set(self.completion.output_ids)|set(self.completion.omitted_output_ids) != {r.output_id for r in self.definition.outputs}
                or self.completion.consumed_streams or self.completion.unconsumed_streams or self.completion.unknown_streams
                or self.definition.streams
                or self.receipt.run_id != self.definition.parent_contact.run_id
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids).issubset(self.receipt.input_materialization_ids)):
            raise ValueError('periodic force result changes its original complete native attempt/receipt')
        payloads = [('probe.return',self.returned)]
        if self.returned.returned is not None:
            payloads.append(('raw.return',self.returned.returned))
            for capture in (self.returned.returned.energy,self.returned.returned.gradient):
                if capture is not None and (capture.artifact_manifest.logical not in self.receipt.output_logical_artifacts
                        or capture.artifact_manifest.materialization not in self.receipt.output_materializations):
                    raise ValueError('periodic force raw array is absent from its actual completion receipt')
        for key,record in payloads:
            name = self.receipt.task_id+'.output.'+key
            logical = tuple(r for r in self.receipt.output_logical_artifacts if r.logical_artifact_id == name)
            physical = tuple(r for r in self.receipt.output_materializations if r.logical_artifact_id == name)
            if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != record.SCHEMA
                    or logical[0].content_sha256 != record.fingerprint()
                    or (physical[0].physical_sha256,physical[0].size_bytes) != (record.fingerprint(),record.canonical_size_bytes())):
                raise ValueError('periodic force result substitutes its original receipted raw return')
        if self.interpretation != 'ORIGINAL_PERIODIC_FORCE_ATTEMPT_REQUIRES_INDEPENDENT_NUMERICAL_AND_PHYSICAL_ASSESSMENT':
            raise ValueError('periodic force custody cannot establish independent physical admission')


def probe_outputs():
    from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import return_outputs
    return tuple(sorted((*return_outputs(),json_output('files.census',DurableRawFileCensus),raw_output('files.raw'),
        json_output('probe.return',PeriodicProbeNativeReturn)),key=lambda r:r.output_id))


def native_input_records(config, representation, raw_sources):
    capability_for(config)
    validate_force_selection(config.selection, representation, config.seed if is_restart(config) else None)
    exact(raw_sources,PeriodicProbeRawSources)
    if (raw_sources.identity != config.raw_sources or representation.canonical_size_bytes() != config.representation_size_bytes
            or raw_sources.canonical_size_bytes() != config.raw_source_size_bytes or prepare_raw_sources(config.selection,
            raw_sources.topology_utf8.encode('ascii'),raw_sources.coordinates_utf8.encode('ascii')) != raw_sources):
        raise ValueError('periodic force direct input changes its complete original source bytes')
    request = force_probe_request(config.selection.probe,representation,config.provenance,gradient_unit=GRADIENT_UNIT)
    if request != selected_request(config):
        raise ValueError('periodic force request differs from the complete original molecular input')
    records = (('native-arrays',representation.arrays.identity,representation.arrays),
            ('native-model',representation.identity,representation),
            ('native-probe',config.selection.probe.identity,config.selection.probe),
            ('native-provenance',config.provenance.identity,config.provenance),
            ('native-request',request.identity,request),
            ('native-source',raw_sources.identity,raw_sources))
    return (*records, ('native-seed', config.seed.identity, config.seed)) if is_restart(config) else records


def selected_request(config):
    """Pure metadata projection; actual native input joins recheck the full model."""
    probe = config.selection.probe
    return CoupledEvaluationRequest(probe.probe_id+'.evaluation',probe.identity,
        config.selection.representation,config.selection.coordinates.identity,config.provenance.identity,
        config.selection.physical_atom_count,gradient_unit=GRADIENT_UNIT)



def operands(config):
    return tuple(sorted({config.identity,config.selection.identity,config.selection.representation,
        config.raw_sources,config.provenance.identity,*config.selection.sources,
        *( (config.seed.density_bytes,) if is_restart(config) else () )},key=lambda r:r.object_id))


def slots(config):
    return ('native.periodic-force-probe.'+config.fingerprint(),)


def definition_sources(config, representation):
    return tuple(sorted({config.selection.probe.identity,representation.identity,representation.arrays.identity,
        config.provenance.identity,config.identity,config.raw_sources,
        *((config.seed.identity, config.seed.density_bytes) if is_restart(config) else ())},
        key=lambda r:r.object_id))


def native_work(context,config,representation,parent):
    validate_force_selection(config.selection, representation, config.seed if is_restart(config) else None)
    definition = force_probe_definition(config.selection.probe,representation,config.provenance,
        parent_contact=parent,input_materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)),
        gradient_unit=GRADIENT_UNIT)
    definition = replace(definition,outputs=probe_outputs(),sources=definition_sources(config, representation))
    roster = NativeSubworkRoster('selected.native-subwork',parent,(definition.identity,))
    return PreparedNativeWork(parent,(UNIT,),slots(config),(definition,),(roster,))


def _decode(context, *, restart=False, accelerated=False):
    declared = operation_declaration(restart=restart, accelerated=accelerated).manifest()
    capability = declared.capability_key
    config_type = config_kind(restart=restart, accelerated=accelerated)
    if (context.task_id != capability or context.permissions != declared.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != (9 if restart else 7)):
        raise ValueError('periodic force changes its complete task/input contract')
    kinds = {config_type.SCHEMA:(config_type,MAX_CONFIG),
             ArrayDatasetManifest.SCHEMA:(ArrayDatasetManifest,MAX_CONFIG),
             MolecularForceProbe.SCHEMA:(MolecularForceProbe,MAX_CONFIG),
             CoupledEvaluationRequest.SCHEMA:(CoupledEvaluationRequest,MAX_CONFIG),
             MolecularRepresentation.SCHEMA:(MolecularRepresentation,MAX_MODEL),
             NumericalProducingProvenance.SCHEMA:(NumericalProducingProvenance,MAX_CONFIG),
             PeriodicProbeRawSources.SCHEMA:(PeriodicProbeRawSources,MAX_RAW_SOURCES)}
    if restart:
        kinds.update({PeriodicDensitySeed.SCHEMA:(PeriodicDensitySeed, MAX_CONFIG), DENSITY_SCHEMA:(None, MAX_DENSITY_BYTES)})
    received = {}
    for port in context.input_ports:
        selected = kinds.get(port.payload_schema)
        media = 'application/octet-stream' if port.payload_schema == DENSITY_SCHEMA else 'application/json'
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != media
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or port.payload_schema in received):
            raise ValueError('periodic force changes a complete direct exposed input')
        raw = port.read(selected[1])
        received[port.payload_schema] = (port, raw if selected[0] is None else
            decode_canonical_bytes(raw,selected[0],maximum_bytes=selected[1]))
    if set(received) != set(kinds):
        raise ValueError('periodic force omits a complete direct input')
    port,config = received[config_type.SCHEMA]
    if context.resource_budget != resource_budget(config):
        raise ValueError('periodic force changes its exact selected host/device resource allocation')
    if (config.config_id,config.fingerprint(),port.artifact_id) != (
            context.config.config_id,context.config.content_sha256,context.config.artifact_id):
        raise ValueError('periodic force substitutes its selected configuration')
    representation = received[MolecularRepresentation.SCHEMA][1]
    raw_sources = received[PeriodicProbeRawSources.SCHEMA][1]
    for _,_,record in native_input_records(config,representation,raw_sources):
        if received[record.SCHEMA][1] != record:
            raise ValueError('periodic force substitutes its exact original direct input record')
    if restart:
        port, raw = received[DENSITY_SCHEMA]
        if port.artifact_id != config.seed.density_bytes.object_id:
            raise ValueError('periodic restart substitutes its selected binary density input')
        read_density_bytes(config.seed, raw)
        return config,representation,raw_sources,raw
    return config,representation,raw_sources


def prepare_native_work(*,runner,context,expected_parent):
    if type(runner) not in (PeriodicProbeRunner, PeriodicRestartRunner, AcceleratedPeriodicProbeRunner, AcceleratedPeriodicRestartRunner):
        raise ValueError('periodic force requires its installed native owner')
    config,representation,*_ = _decode(context, restart=runner.restart, accelerated=runner.accelerated)
    return native_work(context,config,representation,expected_parent)


class PeriodicProbeRunner:
    restart = False
    accelerated = False

    def __init__(self):
        self.manifest = operation_declaration(restart=self.restart, accelerated=self.accelerated).manifest()

    def preflight(self,context):
        config,*_ = _decode(context, restart=self.restart, accelerated=self.accelerated)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.selection.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('periodic force backend differs from accelerated_compute; author the selected backend explicitly')
        authenticate_periodic_engine(config.selection.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=config.selection.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(config.selection.engine))

    def execute(self,context):
        raise ValueError('periodic force requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self,context,native_subwork,progress=None):
        try:
            config,representation,raw_sources,*extra = _decode(context, restart=self.restart, accelerated=self.accelerated)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.selection.molecular)
            if context.accelerated_compute != self.accelerated:
                raise ValueError('periodic force backend differs from its frozen accelerated_compute selection')
            capability = capability_for(config)
            prepared = context.prepared_invocation
            if prepared is None or prepared.implementation != config.implementation:
                raise ValueError('periodic force changes its frozen producing source')
            authenticate_periodic_engine(config.selection.engine)
            work = native_work(context,config,representation,native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError('periodic force changes its frozen native census')
            root = Path(config.work_directory)
            root.mkdir(parents=False,exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0],definitions=work.definitions)
            definition = work.definitions[0]
            request = force_probe_request(config.selection.probe,representation,config.provenance,gradient_unit=GRADIENT_UNIT)
            completed = native_subwork.recover(definition)
            if completed is not None:
                returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition,'probe.return')),
                    PeriodicProbeNativeReturn,maximum_bytes=MAX_RETURN)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('uncertain periodic force contact cannot be repeated')
                directory = root/definition.subwork_id
                directory.mkdir()
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                wall,cpu,self_cpu = time.monotonic(),resource.getrusage(resource.RUSAGE_CHILDREN),time.process_time()
                values,raw_return,error = None,None,None
                try:
                    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import execute_periodic_probe
                    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_operator_options
                    values = invoke_native_subwork(native_subwork,entry,execute_periodic_probe,
                        representation=representation,selection=config.selection.path,settings=config.selection.electronic,
                        mm_settings=config.selection.molecular,cell=config.selection.cell,
                        raw_topology=raw_sources.topology_utf8.encode('ascii'),raw_coordinates=raw_sources.coordinates_utf8.encode('ascii'),
                        directory=directory,
                        **periodic_operator_options(config.selection.engine),
                        **({'density_seed':config.seed, 'density_bytes':extra[0]} if self.restart else {}))
                except (NativeEntryRefused,NativeSubworkObservationPublicationError):
                    raise
                except Exception:
                    error = traceback.format_exc()
                    with (directory/'native-error.txt').open('x') as stream:
                        stream.write(error)
                if values is not None:
                    raw_return = capture_native_return(request,values['energy_hartree'],values['gradient_hartree_per_bohr'],native_subwork,entry)
                    if raw_return.capture_failures:
                        error = 'The actual native call returned; raw operand capture is incomplete: '+repr(raw_return.capture_failures)
                # Preserve authentic raw values before the final environment check.
                try:
                    authenticate_periodic_engine(config.selection.engine,loaded=True)
                except (ValueError,OSError):
                    error = ('' if error is None else error+'\n')+traceback.format_exc()
                    with (directory/'engine-authentication-error.txt').open('x') as stream:
                        stream.write(error)
                census,archive_manifests = publish_directory(native_subwork,entry,directory,root, selected_census=directory_census(directory, root))
                returned = PeriodicProbeNativeReturn(config.selection.identity,request.identity,census,raw_return,error)
                return_manifest = publish_record(native_subwork,entry,'probe.return',returned)
                retained_bytes = sum(m.materialization.size_bytes for m in (*archive_manifests,return_manifest))
                if raw_return is not None:
                    retained_bytes += raw_return.canonical_size_bytes()
                    retained_bytes += sum(row.artifact_manifest.materialization.size_bytes
                        for row in (raw_return.energy,raw_return.gradient) if row is not None)
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                completed = native_subwork.complete(entry,
                    operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                        Decimal(str(time.monotonic()-wall)),Decimal(retained_bytes)),
                    cost_scope='One complete MM construction and one coupled force attempt, final source check and publication; retained bytes count published native output payloads, excluding working copies/control records; peak RSS spans worker lifetime; no physical dynamics time',
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    reason_codes=() if error is None else ('periodic-force-native-or-capture-failure',))
            if returned.selection != config.selection.identity or returned.request != request.identity:
                raise ValueError('periodic force recovery substitutes its original selected call')
            result = PeriodicProbeResult(capability+'.result',request,returned,definition,completed.completion,completed.receipt)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != capability+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('periodic force changes its complete aggregate output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id,result.canonical_bytes()),),
                (ReceiptCheck('complete-original-periodic-force-native-census',True,()),))
        finally:
            for port in context.input_ports:
                port.close()


class PeriodicRestartRunner(PeriodicProbeRunner):
    restart = True


class AcceleratedPeriodicProbeRunner(PeriodicProbeRunner):
    accelerated = True


class AcceleratedPeriodicRestartRunner(PeriodicRestartRunner):
    accelerated = True


def operation_declaration(*, restart=False, accelerated=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    config_type = config_kind(restart=restart, accelerated=accelerated)
    capability = (GPU_RESTART_CAPABILITY if restart else GPU_CAPABILITY) if accelerated else (RESTART_CAPABILITY if restart else CAPABILITY)
    runner = {(False, False): PeriodicProbeRunner, (True, False): PeriodicRestartRunner,
        (False, True): AcceleratedPeriodicProbeRunner, (True, True): AcceleratedPeriodicRestartRunner}[(restart, accelerated)]
    return RecursiveOperationDeclaration(capability_key=capability,
        capability_version='1.0.0' if restart or accelerated else '1.0.1',
        implementation_id=('gpu4pyscf-periodic-direct-cuda-double-v1' if accelerated else
            'complete-periodic-gp-force-checkpoint-density-v1' if restart else 'complete-periodic-gp-force-probe-selected-threads-v2'),
        kind=CapabilityKind.SIMULATOR, config_record_type=config_type,stage=ScientificStage.ACQUIRE,
        input_ports=tuple(sorted((RecursivePortContract('native-arrays',ArrayDatasetManifest.SCHEMA,'application/json',MAX_CONFIG),
            RecursivePortContract('native-model',MolecularRepresentation.SCHEMA,'application/json',MAX_MODEL),
            RecursivePortContract('native-probe',MolecularForceProbe.SCHEMA,'application/json',MAX_CONFIG),
            RecursivePortContract('native-provenance',NumericalProducingProvenance.SCHEMA,'application/json',MAX_CONFIG),
            RecursivePortContract('native-request',CoupledEvaluationRequest.SCHEMA,'application/json',MAX_CONFIG),
            RecursivePortContract('native-source',PeriodicProbeRawSources.SCHEMA,'application/json',MAX_RAW_SOURCES),
            *((RecursivePortContract('native-seed',PeriodicDensitySeed.SCHEMA,'application/json',MAX_CONFIG),
               RecursivePortContract('native-density',DENSITY_SCHEMA,'application/octet-stream',MAX_DENSITY_BYTES)) if restart else ())),
            key=lambda row:row.port_id)),
        outputs=(OutputTemplate('product',PeriodicProbeResult.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-direct-molecular-inputs','complete-original-amber-assignment',
            'raw-native-unit-preservation','complete-native-return-before-assessment','original-custody-no-replay'))),
        runner_factory=runner,record_codecs={c.SCHEMA:c for c in (
            config_type,PeriodicProbeRawSources,PeriodicProbeResult,MolecularRepresentation,NumericalProducingProvenance,
            ArrayDatasetManifest,MolecularForceProbe,CoupledEvaluationRequest,*((PeriodicDensitySeed,) if restart else ()))},
        storage_codecs=(DENSITY_CODEC,) if restart else (),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,),native_effect_slot_ids=slots,scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True,complete_unit_census=True,
            native_work_preparer=prepare_native_work,worker_environment_selector=periodic_worker_environment))
