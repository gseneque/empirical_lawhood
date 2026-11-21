# SPDX-License-Identifier: MPL-2.0
"""One selected reference equilibrium through the ordinary native lifecycle."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import publish_directory, publish_record, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
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
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET, UNIT, MAX_CONFIG, MAX_MODEL, MAX_RAW_SOURCES, MAX_RETURN, PeriodicProbeConfig, AcceleratedPeriodicProbeConfig, GPU_RESOURCE_CEILING, resource_budget as probe_resource_budget, PeriodicProbeRawSources, native_input_records as original_probe_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, authenticate_periodic_engine
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import ReferenceEquilibriumSelection, ObservedElectronicEquilibriumSelection, read_equilibrium_phase_space, validate_equilibrium_prototype, selected_bias

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import PHASE_CODEC
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import PHASE_SCHEMA, MAX_PHASE_BYTES


CAPABILITY = 'rubisco-response.reference-equilibrium'
GPU_CAPABILITY = 'rubisco-response.accelerated-reference-equilibrium'
ELECTRONIC_CAPABILITY = 'rubisco-response.constrained-electronic-equilibrium'


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-config'
    ACCELERATED: ClassVar[bool] = False
    OBSERVED: ClassVar[bool] = False
    config_id: str
    original: PeriodicProbeConfig
    selection: ReferenceEquilibriumSelection

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.original, AcceleratedPeriodicProbeConfig if self.ACCELERATED else PeriodicProbeConfig)
        exact(self.selection, ObservedElectronicEquilibriumSelection if self.OBSERVED else ReferenceEquilibriumSelection)
        validate_equilibrium_prototype(self.selection, self.original.selection)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class AcceleratedReferenceEquilibriumConfig(ReferenceEquilibriumConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-reference-equilibrium-config'
    ACCELERATED: ClassVar[bool] = True
    original: AcceleratedPeriodicProbeConfig


@dataclass(frozen=True, slots=True)
class ObservedElectronicEquilibriumConfig(AcceleratedReferenceEquilibriumConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/observed-electronic-equilibrium-config'
    OBSERVED: ClassVar[bool] = True
    selection: ObservedElectronicEquilibriumSelection


def config_kind(*, accelerated=False, observed=False):
    if type(accelerated) is not bool or type(observed) is not bool or observed and not accelerated:
        raise ValueError('reference equilibrium requires an explicit installed backend selection')
    if observed:
        return ObservedElectronicEquilibriumConfig
    return AcceleratedReferenceEquilibriumConfig if accelerated else ReferenceEquilibriumConfig


def capability_for(config):
    if type(config) is ReferenceEquilibriumConfig:
        return CAPABILITY
    if type(config) is AcceleratedReferenceEquilibriumConfig:
        return GPU_CAPABILITY
    if type(config) is ObservedElectronicEquilibriumConfig:
        return ELECTRONIC_CAPABILITY
    raise TypeError('reference equilibrium requires its exact selected CPU or GPU configuration')


def resource_budget(config):
    capability_for(config)
    return probe_resource_budget(config.original)


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-return'
    configuration: ObjectIdentity
    selection: ObjectIdentity
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.configuration, ObjectIdentity)
        exact(self.selection, ObjectIdentity)
        exact(self.files, DurableRawFileCensus)
        kinds = {ReferenceEquilibriumConfig.SCHEMA:ReferenceEquilibriumSelection.SCHEMA,
            AcceleratedReferenceEquilibriumConfig.SCHEMA:ReferenceEquilibriumSelection.SCHEMA,
            ObservedElectronicEquilibriumConfig.SCHEMA:ObservedElectronicEquilibriumSelection.SCHEMA}
        if (kinds.get(self.configuration.object_schema) != self.selection.object_schema
                or self.error is not None and (type(self.error) is not str or not self.error)):
            raise ValueError('equilibrium return changes original selection or failure diagnostic')


def native_outputs():
    return tuple(sorted((json_output('equilibrium.return', ReferenceEquilibriumReturn),
        json_output('files.census', DurableRawFileCensus), raw_output('files.raw')), key=lambda r:r.output_id))


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-result'
    result_id: str
    returned: ReferenceEquilibriumReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    interpretation: str = 'ORIGINAL_EQUILIBRIUM_ATTEMPT_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for value, kind in ((self.returned, ReferenceEquilibriumReturn), (self.definition, NativeSubworkDefinition),
                (self.completion, NativeSubworkCompletion), (self.receipt, CanonicalTaskReceipt)):
            exact(value, kind)
        require_native_completion_receipt(self.completion, self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        if (self.definition.operation_id != CAPABILITY or self.definition.configuration != self.returned.selection
                or self.returned.configuration not in self.definition.sources or self.definition.outputs != native_outputs()
                or self.definition.streams or self.completion.definition != self.definition.identity
                or self.completion.operational_status is not (OperationalStatus.SUCCEEDED if self.returned.error is None else OperationalStatus.FAILED)
                or set(self.completion.output_ids) != {r.output_id for r in native_outputs()}
                or self.completion.omitted_output_ids or self.completion.consumed_streams
                or self.completion.unconsumed_streams or self.completion.unknown_streams
                or self.receipt.run_id != self.definition.parent_contact.run_id
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids).issubset(self.receipt.input_materialization_ids)
                or self.interpretation != 'ORIGINAL_EQUILIBRIUM_ATTEMPT_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('equilibrium result changes its complete original attempt, receipt or scientific scope')
        for name, record in (('equilibrium.return', self.returned), ('files.census', self.returned.files)):
            key = self.receipt.task_id+'.output.'+name
            logical = [r for r in self.receipt.output_logical_artifacts if r.logical_artifact_id == key]
            physical = [r for r in self.receipt.output_materializations if r.logical_artifact_id == key]
            if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != record.SCHEMA
                    or logical[0].content_sha256 != record.fingerprint()
                    or (physical[0].physical_sha256, physical[0].size_bytes) != (record.fingerprint(), record.canonical_size_bytes())):
                raise ValueError('equilibrium result substitutes its original receipted return or complete file census')


def native_input_records(config, representation, sources):
    capability_for(config)
    original_probe_inputs(config.original, representation, sources)
    return (('native-arrays', config.selection.arrays.identity, config.selection.arrays),
        ('native-model', representation.identity, representation),
        ('native-prototype', config.original.selection.identity, config.original.selection),
        ('native-provenance', config.original.provenance.identity, config.original.provenance),
        ('native-selection', config.selection.identity, config.selection), ('native-source', sources.identity, sources))


def operands(config):
    return tuple(sorted({config.identity, config.original.selection.identity, config.selection.identity,
        config.selection.arrays.identity, config.selection.phase_bytes, config.original.selection.representation,
        config.original.raw_sources, config.original.provenance.identity}, key=lambda r:r.object_id))


def slots(config):
    return ('native.reference-equilibrium.'+config.fingerprint(),)


def definition_for(config, *, parent, materialization_ids):
    return NativeSubworkDefinition('reference-equilibrium.'+config.selection.fingerprint(), CAPABILITY, parent,
        config.selection.identity, operands(config), config.original.implementation.code_sources_sha256,
        config.original.implementation.dependency_lock_sha256, materialization_ids, (), native_outputs())


def native_work(context, config, parent):
    definition = definition_for(config, parent=parent,
        materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (UNIT,), slots(config), (definition,), (roster,))


def _decode(context, *, accelerated=False, observed=False):
    declaration = operation_declaration(accelerated=accelerated, observed=observed).manifest()
    config_type = config_kind(accelerated=accelerated, observed=observed)
    selection_type = ObservedElectronicEquilibriumSelection if observed else ReferenceEquilibriumSelection
    if (context.permissions != declaration.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != 8):
        raise ValueError('reference equilibrium changes its complete original task/input contract')
    kinds = {config_type.SCHEMA:(config_type, MAX_CONFIG),
        ArrayDatasetManifest.SCHEMA:(ArrayDatasetManifest, MAX_CONFIG),
        MolecularRepresentation.SCHEMA:(MolecularRepresentation, MAX_MODEL),
        PeriodicProbeSelection.SCHEMA:(PeriodicProbeSelection, MAX_CONFIG),
        NumericalProducingProvenance.SCHEMA:(NumericalProducingProvenance, MAX_CONFIG),
        selection_type.SCHEMA:(selection_type, MAX_CONFIG),
        PeriodicProbeRawSources.SCHEMA:(PeriodicProbeRawSources, MAX_RAW_SOURCES),
        PHASE_SCHEMA:(None, MAX_PHASE_BYTES)}
    received = {}
    for port in context.input_ports:
        selected = kinds.get(port.payload_schema)
        media = 'application/octet-stream' if port.payload_schema == PHASE_SCHEMA else 'application/json'
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != media
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or port.payload_schema in received):
            raise ValueError('reference equilibrium changes a complete direct exposed input')
        raw = port.read(selected[1])
        received[port.payload_schema] = (port, raw if selected[0] is None else
            decode_canonical_bytes(raw, selected[0], maximum_bytes=selected[1]))
    if set(received) != set(kinds):
        raise ValueError('reference equilibrium omits a complete original direct input')
    port, config = received[config_type.SCHEMA]
    if context.resource_budget != resource_budget(config):
        raise ValueError('reference equilibrium changes its selected host/device resource allocation')
    if ((config.config_id, config.fingerprint(), port.artifact_id) !=
            (context.config.config_id, context.config.content_sha256, context.config.artifact_id)
            or context.task_id != capability_for(config)):
        raise ValueError('reference equilibrium substitutes its selected configuration or node')
    representation, sources = received[MolecularRepresentation.SCHEMA][1], received[PeriodicProbeRawSources.SCHEMA][1]
    for _, _, record in native_input_records(config, representation, sources):
        if received[record.SCHEMA][1] != record:
            raise ValueError('reference equilibrium substitutes an exact original direct operand')
    phase_bytes = received[PHASE_SCHEMA][1]
    read_equilibrium_phase_space(config.selection, representation, phase_bytes)
    return config, representation, sources, phase_bytes


def checked_inputs(config, representation, sources, phase_bytes):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    original_coordinates(config.original.selection, representation, sources)
    xyz, _, _ = read_equilibrium_phase_space(config.selection, representation, phase_bytes)
    selected_bias(config.selection, config.original.selection, representation, xyz)


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) not in (ReferenceEquilibriumRunner, AcceleratedReferenceEquilibriumRunner, ObservedElectronicEquilibriumRunner):
        raise ValueError('reference equilibrium requires its installed native owner')
    config, representation, sources, raw = _decode(context, accelerated=runner.accelerated, observed=runner.observed)
    checked_inputs(config, representation, sources, raw)
    return native_work(context, config, expected_parent)


class ReferenceEquilibriumRunner:
    accelerated = False
    observed = False

    def __init__(self):
        self.manifest = operation_declaration(accelerated=self.accelerated, observed=self.observed).manifest()

    def preflight(self, context):
        config, representation, sources, raw = _decode(context, accelerated=self.accelerated, observed=self.observed)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.original.selection.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('reference equilibrium backend differs from accelerated_compute')
        checked_inputs(config, representation, sources, raw)
        authenticate_periodic_engine(config.original.selection.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=config.original.selection.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(config.original.selection.engine))

    def execute(self, context):
        raise ValueError('reference equilibrium requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, sources, raw = _decode(context, accelerated=self.accelerated, observed=self.observed)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.original.selection.molecular)
            if context.accelerated_compute != self.accelerated:
                raise ValueError('reference equilibrium backend differs from accelerated_compute')
            original = config.original
            prepared = context.prepared_invocation
            if prepared is None or prepared.implementation != original.implementation:
                raise ValueError('reference equilibrium changes its frozen producing source')
            checked_inputs(config, representation, sources, raw)
            work = native_work(context, config, native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError('reference equilibrium changes its frozen native census')
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            definition = work.definitions[0]
            completed = native_subwork.recover(definition)
            if completed is not None:
                returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'equilibrium.return')),
                    ReferenceEquilibriumReturn, maximum_bytes=MAX_RETURN)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('uncertain original equilibrium contact cannot be repeated')
                authenticate_periodic_engine(original.selection.engine)
                if self.accelerated:
                    from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
                    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
                    preflight_gpu_backend(device_memory_bytes=original.selection.engine.device_memory_bytes,
                        molecular_platform=periodic_molecular_platform(original.selection.engine))
                root = Path(original.work_directory)
                root.mkdir(parents=False, exist_ok=True)
                directory = root/definition.subwork_id
                directory.mkdir()
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                wall, cpu, self_cpu = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN), time.process_time()
                error = None
                try:
                    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_equilibrium_native import execute_reference_equilibrium
                    invoke_native_subwork(native_subwork, entry, execute_reference_equilibrium,
                        selection=config.selection, prototype=original.selection, representation=representation,
                        sources=sources, phase_bytes=raw, directory=directory)
                except (NativeEntryRefused, NativeSubworkObservationPublicationError):
                    raise
                except Exception:
                    error = traceback.format_exc()
                    with (directory/'native-error.txt').open('x') as stream:
                        stream.write(error)
                try:
                    authenticate_periodic_engine(original.selection.engine, loaded=True)
                except (ValueError, OSError):
                    error = ('' if error is None else error+'\n')+traceback.format_exc()
                    with (directory/'engine-authentication-error.txt').open('x') as stream:
                        stream.write(error)
                census, archives = publish_directory(native_subwork, entry, directory, root, selected_census=directory_census(directory, root))
                returned = ReferenceEquilibriumReturn(config.identity, config.selection.identity, census, error)
                manifest = publish_record(native_subwork, entry, 'equilibrium.return', returned)
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                completed = native_subwork.complete(entry,
                    operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                        Decimal(str(time.monotonic()-wall)), Decimal(sum(m.materialization.size_bytes for m in (*archives, manifest)))),
                    cost_scope='One original complete equilibrium sampling attempt, original files, final source check and publication; published payload bytes exclude working copies and control records; peak RSS spans worker lifetime; sampling time is stored separately in equilibrium frames and supplies no unbiased rate clock',
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    reason_codes=() if error is None else ('reference-equilibrium-native-or-capture-failure',))
            if returned.configuration != config.identity or returned.selection != config.selection.identity:
                raise ValueError('equilibrium recovery substitutes its exact original selection')
            result = ReferenceEquilibriumResult(capability_for(config)+'.result', returned, definition, completed.completion, completed.receipt)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != capability_for(config)+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('reference equilibrium changes its complete output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck('complete-original-reference-equilibrium-attempt', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


class AcceleratedReferenceEquilibriumRunner(ReferenceEquilibriumRunner):
    accelerated = True


class ObservedElectronicEquilibriumRunner(AcceleratedReferenceEquilibriumRunner):
    observed = True


def operation_declaration(*, accelerated=False, observed=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    config_type = config_kind(accelerated=accelerated, observed=observed)
    selection_type = ObservedElectronicEquilibriumSelection if observed else ReferenceEquilibriumSelection
    return RecursiveOperationDeclaration(capability_key=ELECTRONIC_CAPABILITY if observed else GPU_CAPABILITY if accelerated else CAPABILITY, capability_version='1.0.0',
        implementation_id='constrained-electronic-equilibrium-v1' if observed else 'accelerated-original-reference-equilibrium-v1' if accelerated else 'original-reference-equilibrium-v1', kind=CapabilityKind.SIMULATOR,
        config_record_type=config_type, stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract('native-arrays', ArrayDatasetManifest.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-model', MolecularRepresentation.SCHEMA, 'application/json', MAX_MODEL),
            RecursivePortContract('native-phase', PHASE_SCHEMA, 'application/octet-stream', MAX_PHASE_BYTES),
            RecursivePortContract('native-prototype', PeriodicProbeSelection.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-selection', selection_type.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-source', PeriodicProbeRawSources.SCHEMA, 'application/json', MAX_RAW_SOURCES)),
        outputs=(OutputTemplate('product', ReferenceEquilibriumResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-original-phase-space', 'original-physical-masses-and-clock',
            'raw-returns-before-trace-assessment', 'original-custody-no-replay'))),
        runner_factory=ObservedElectronicEquilibriumRunner if observed else AcceleratedReferenceEquilibriumRunner if accelerated else ReferenceEquilibriumRunner, record_codecs={c.SCHEMA:c for c in (config_type,
            selection_type, ReferenceEquilibriumReturn, ReferenceEquilibriumResult, PeriodicProbeSelection,
            PeriodicProbeRawSources, MolecularRepresentation, NumericalProducingProvenance, ArrayDatasetManifest)},
        storage_codecs=(PHASE_CODEC,),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,), native_effect_slot_ids=slots,
            scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment))
