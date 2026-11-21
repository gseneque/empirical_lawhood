# SPDX-License-Identifier: MPL-2.0
"""Complete active-state relaxation through the existing native-subwork contract."""

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
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_assessment import assess_catalytic_partition, assess_catalytic_seed
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ConditionalActiveRelaxationSelection, MatchedActiveRelaxationPlan, MODEL_NAMES, validate_conditional_relaxation_selection, validate_relaxation_member
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET, GPU_RESOURCE_CEILING, UNIT, MAX_MODEL, MAX_RAW_SOURCES, PeriodicProbeRawSources, prepare_raw_sources
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, _absolute, accelerated_engine, authenticate_periodic_engine, validate_periodic_probe_model


CAPABILITY = 'rubisco-response.matched-active-relaxation'
CONDITIONAL_CAPABILITY = 'rubisco-response.conditional-active-relaxation'
GPU_CAPABILITY = 'rubisco-response.accelerated-matched-active-relaxation'
GPU_CONDITIONAL_CAPABILITY = 'rubisco-response.accelerated-conditional-active-relaxation'
MAX_CONFIG = 32*2**20
MAX_PREPARATION = 64*2**20
MAX_RETURN = 4*2**20


@dataclass(frozen=True, slots=True)
class ActiveRelaxationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-config'
    ACCELERATED: ClassVar[bool] = False
    config_id: str
    plan: MatchedActiveRelaxationPlan
    model_name: str
    prototype: PeriodicProbeSelection
    preparation: ObjectIdentity
    preparation_size_bytes: int
    seeds: tuple[CatalyticStateSeed, ...]
    representation_size_bytes: int
    raw_sources: ObjectIdentity
    raw_source_size_bytes: int
    implementation: RecursiveImplementationBinding
    work_directory: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for value, kind in ((self.plan, MatchedActiveRelaxationPlan), (self.prototype, PeriodicProbeSelection),
                (self.preparation, ObjectIdentity), (self.raw_sources, ObjectIdentity),
                (self.implementation, RecursiveImplementationBinding), (self.provenance, NumericalProducingProvenance)):
            exact(value, kind)
        _absolute(self.work_directory)
        if accelerated_engine(self.prototype.engine) != self.ACCELERATED:
            raise ValueError('active relaxation changes its declared CPU/GPU numerical engine')
        if self.ACCELERATED and self.prototype.electronic.memory_megabytes*10**6 > self.prototype.engine.host_memory_bytes:
            raise ValueError('active relaxation electronic workspace exceeds its host-memory allocation')
        if (type(self.seeds) is not tuple or len(self.seeds) != 96
                or tuple(s.seed_id for s in self.seeds) != tuple(sorted({s.seed_id for s in self.seeds}))):
            raise ValueError('active relaxation requires all 96 exact direct seed operands')
        for seed in self.seeds:
            exact(seed, CatalyticStateSeed)
        if self.model_name not in MODEL_NAMES:
            raise ValueError('active relaxation changes its selected material')
        member = next(m for m in self.plan.members if m.model_name == self.model_name)
        if (member.preparation != self.preparation or member.prototype != self.prototype.identity
                or member.representation != self.prototype.representation
                or self.preparation.object_schema != ActiveModelPreparation.SCHEMA
                or self.raw_sources.object_schema != PeriodicProbeRawSources.SCHEMA
                or self.prototype.engine.numerical_threads > BUDGET.cpu_cores
                or any(getattr(self.provenance, name) != getattr(self.implementation, name) for name in (
                    'package_sources', 'code_sources_sha256', 'dependency_lock_sha256', 'observed_git_head', 'observed_checkout_clean'))):
            raise ValueError('active relaxation changes its matched design, full source or producing implementation')
        for value, bound in ((self.preparation_size_bytes, MAX_PREPARATION),
                (self.representation_size_bytes, MAX_MODEL), (self.raw_source_size_bytes, MAX_RAW_SOURCES)):
            if type(value) is not int or not 0 < value <= bound:
                raise ValueError('active relaxation omits an exact bounded full-input size')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class ConditionalActiveRelaxationConfig(ActiveRelaxationConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-active-relaxation-config'
    selection: ConditionalActiveRelaxationSelection

    def __post_init__(self):
        ActiveRelaxationConfig.__post_init__(self)
        validate_conditional_relaxation_selection(self.plan, self.selection)


@dataclass(frozen=True, slots=True)
class AcceleratedActiveRelaxationConfig(ActiveRelaxationConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-active-relaxation-config'
    ACCELERATED: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class AcceleratedConditionalActiveRelaxationConfig(ConditionalActiveRelaxationConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-conditional-active-relaxation-config'
    ACCELERATED: ClassVar[bool] = True


def configuration_type(*, conditional=False, accelerated=False):
    if type(conditional) is not bool or type(accelerated) is not bool:
        raise ValueError('active relaxation requires explicit installed operation selections')
    return {(False, False): ActiveRelaxationConfig, (True, False): ConditionalActiveRelaxationConfig,
        (False, True): AcceleratedActiveRelaxationConfig,
        (True, True): AcceleratedConditionalActiveRelaxationConfig}[(conditional, accelerated)]


def conditional_configuration(config):
    if type(config) not in (ActiveRelaxationConfig, ConditionalActiveRelaxationConfig,
            AcceleratedActiveRelaxationConfig, AcceleratedConditionalActiveRelaxationConfig):
        raise ValueError('active relaxation requires its exact installed configuration type')
    return type(config) in (ConditionalActiveRelaxationConfig, AcceleratedConditionalActiveRelaxationConfig)


def capability_for(config):
    conditional = conditional_configuration(config)
    return ((GPU_CONDITIONAL_CAPABILITY if conditional else GPU_CAPABILITY) if config.ACCELERATED
        else (CONDITIONAL_CAPABILITY if conditional else CAPABILITY))


def resource_budget(config):
    capability_for(config)
    return (replace(GPU_RESOURCE_CEILING, memory_bytes=config.prototype.engine.host_memory_bytes)
        if config.ACCELERATED else BUDGET)


def state_census_for(config):
    if conditional_configuration(config):
        validate_conditional_relaxation_selection(config.plan, config.selection)
        return config.selection.state_census
    return next(m.state_census for m in config.plan.members if m.model_name == config.model_name)


def selected_seeds(config, prepared):
    """Derive the native census from the frozen selection and full preparation."""
    sites = {site.identity: site.path.reactive_site_id for site in prepared.sites}
    census = state_census_for(config)
    selected = tuple(seed for seed in prepared.seeds
        if (sites[seed.site], seed.state_label, seed.water_occupancy) in census)
    if len(selected) != len(census):
        raise ValueError('active relaxation loses an explicitly selected original starting state')
    return selected


@dataclass(frozen=True, slots=True)
class ActiveRelaxationReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-return'
    configuration: ObjectIdentity
    seed: ObjectIdentity
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.configuration, ObjectIdentity)
        exact(self.seed, ObjectIdentity)
        exact(self.files, DurableRawFileCensus)
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError('active relaxation loses its original failure diagnostic')


def native_outputs():
    return tuple(sorted((json_output('relaxation.return', ActiveRelaxationReturn),
        json_output('files.census', DurableRawFileCensus), raw_output('files.raw')), key=lambda r:r.output_id))


@dataclass(frozen=True, slots=True)
class ActiveRelaxationUnit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-unit'
    returned: ActiveRelaxationReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        validate_relaxation_native_unit(self, operation_ids=(CAPABILITY, CONDITIONAL_CAPABILITY))


def validate_relaxation_native_unit(unit, *, operation_ids):
    """Share exact custody joins while each record retains its own operation set."""
    for value, kind in ((unit.returned, ActiveRelaxationReturn), (unit.definition, NativeSubworkDefinition),
            (unit.completion, NativeSubworkCompletion), (unit.receipt, CanonicalTaskReceipt)):
        exact(value, kind)
    require_native_completion_receipt(unit.completion, unit.receipt,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    if (unit.definition.operation_id not in operation_ids or unit.definition.configuration != unit.returned.seed
            or unit.returned.configuration not in unit.definition.sources or unit.definition.outputs != native_outputs()
            or unit.definition.streams or unit.completion.definition != unit.definition.identity
            or unit.completion.operational_status is not (OperationalStatus.SUCCEEDED if unit.returned.error is None else OperationalStatus.FAILED)
            or set(unit.completion.output_ids) != {r.output_id for r in native_outputs()}
            or unit.completion.omitted_output_ids or unit.completion.consumed_streams
            or unit.completion.unconsumed_streams or unit.completion.unknown_streams
            or unit.receipt.run_id != unit.definition.parent_contact.run_id
            or unit.receipt.implementation_commit != unit.definition.parent_contact.implementation_commit
            or not set(unit.definition.input_materialization_ids).issubset(unit.receipt.input_materialization_ids)):
        raise ValueError('active relaxation changes its complete original native attempt and receipt')
    for name, record in (('relaxation.return', unit.returned), ('files.census', unit.returned.files)):
        key = unit.receipt.task_id+'.output.'+name
        logical = [r for r in unit.receipt.output_logical_artifacts if r.logical_artifact_id == key]
        physical = [r for r in unit.receipt.output_materializations if r.logical_artifact_id == key]
        if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != record.SCHEMA
                or logical[0].content_sha256 != record.fingerprint()
                or (physical[0].physical_sha256, physical[0].size_bytes) != (record.fingerprint(), record.canonical_size_bytes())):
            raise ValueError('active relaxation substitutes its original receipted return or file census')


@dataclass(frozen=True, slots=True)
class ActiveRelaxationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-result'
    result_id: str
    configuration: ObjectIdentity
    plan: ObjectIdentity
    model_name: str
    units: tuple[ActiveRelaxationUnit, ...]
    interpretation: str = 'ORIGINAL_COMPLETE_RELAXATION_ATTEMPTS_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.configuration, ObjectIdentity)
        exact(self.plan, ObjectIdentity)
        if type(self.units) is not tuple or len(self.units) != 96 or self.model_name not in MODEL_NAMES:
            raise ValueError('active relaxation loses the complete selected site/state denominator')
        for unit in self.units:
            exact(unit, ActiveRelaxationUnit)
        ids = tuple(u.definition.subwork_id for u in self.units)
        if (ids != tuple(sorted(set(ids))) or len({u.returned.seed for u in self.units}) != 96
                or any(u.returned.configuration != self.configuration for u in self.units)
                or any(u.definition.operation_id != CAPABILITY for u in self.units)
                or len({u.definition.parent_contact for u in self.units}) != 1
                or self.interpretation != 'ORIGINAL_COMPLETE_RELAXATION_ATTEMPTS_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('active relaxation changes its actual complete roster or scientific scope')


@dataclass(frozen=True, slots=True)
class ConditionalActiveRelaxationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-active-relaxation-result'
    result_id: str
    configuration: ObjectIdentity
    plan: ObjectIdentity
    model_name: str
    units: tuple[ActiveRelaxationUnit, ...]
    selection: ConditionalActiveRelaxationSelection
    interpretation: str = 'ORIGINAL_CONDITIONAL_RELAXATION_ATTEMPTS_UNSELECTED_STATES_UNMEASURED'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.configuration, ObjectIdentity)
        exact(self.plan, ObjectIdentity)
        exact(self.selection, ConditionalActiveRelaxationSelection)
        if (self.configuration.object_schema not in (ConditionalActiveRelaxationConfig.SCHEMA, AcceleratedConditionalActiveRelaxationConfig.SCHEMA)
                or self.selection.plan != self.plan or self.model_name not in MODEL_NAMES
                or type(self.units) is not tuple or len(self.units) != len(self.selection.state_census)):
            raise ValueError('conditional relaxation changes its original selected denominator')
        for unit in self.units:
            exact(unit, ActiveRelaxationUnit)
        ids = tuple(unit.definition.subwork_id for unit in self.units)
        if (ids != tuple(sorted(set(ids))) or len({u.returned.seed for u in self.units}) != len(self.units)
                or any(u.returned.configuration != self.configuration
                    or u.definition.operation_id != CONDITIONAL_CAPABILITY
                    or self.selection.identity not in u.definition.sources for u in self.units)
                or len({u.definition.parent_contact for u in self.units}) != 1
                or self.interpretation != 'ORIGINAL_CONDITIONAL_RELAXATION_ATTEMPTS_UNSELECTED_STATES_UNMEASURED'):
            raise ValueError('conditional relaxation changes its actual attempts or unmeasured-state scope')


def native_input_records(config, representation, prepared, sources):
    conditional = conditional_configuration(config)
    validate_periodic_probe_model(config.prototype, representation)
    validate_relaxation_member(plan=config.plan, model_name=config.model_name,
        prepared=prepared, prototype=config.prototype, representation=representation)
    exact(sources, PeriodicProbeRawSources)
    if (prepared.identity != config.preparation or prepared.canonical_size_bytes() != config.preparation_size_bytes
            or config.seeds != prepared.seeds
            or representation.canonical_size_bytes() != config.representation_size_bytes
            or sources.identity != config.raw_sources or sources.canonical_size_bytes() != config.raw_source_size_bytes
            or prepare_raw_sources(config.prototype, sources.topology_utf8.encode('ascii'), sources.coordinates_utf8.encode('ascii')) != sources):
        raise ValueError('active relaxation substitutes a complete original native operand')
    return tuple(sorted((('native-arrays', representation.arrays.identity, representation.arrays),
        ('native-model', representation.identity, representation), ('native-plan', config.plan.identity, config.plan),
        ('native-preparation', prepared.identity, prepared), ('native-prototype', config.prototype.identity, config.prototype),
        ('native-provenance', config.provenance.identity, config.provenance),
        *((f'native-seed.{i:03}', seed.identity, seed) for i, seed in enumerate(prepared.seeds)),
        ('native-source', sources.identity, sources),
        *((('native-conditional-selection', config.selection.identity, config.selection),) if conditional else ())),
        key=lambda row:row[0]))


def operands(config):
    return tuple(sorted({config.identity, config.plan.identity, config.preparation, config.prototype.identity,
        config.prototype.representation, config.raw_sources, config.provenance.identity,
        *((config.selection.identity,) if conditional_configuration(config) else ())}, key=lambda r:r.object_id))


def slots(config):
    prefix = 'native.conditional-active-relaxation.' if conditional_configuration(config) else 'native.matched-active-relaxation.'
    return (prefix+config.fingerprint(),)


def definition_for(config, prepared, seed, *, parent, materialization_ids):
    site = next(s for s in prepared.sites if s.identity == seed.site)
    name = 'active-relaxation.'+site.path.reactive_site_id+'.'+seed.state_label+'.'+seed.water_occupancy.lower()
    # The complete preparation directly authenticates every site, graph and
    # protocol. Each seed also has its own direct canonical input; nested
    # identities alone do not satisfy the shared native-input boundary.
    sources = operands(config)
    return NativeSubworkDefinition(name, CONDITIONAL_CAPABILITY if conditional_configuration(config) else CAPABILITY, parent, seed.identity, sources,
        config.implementation.code_sources_sha256, config.implementation.dependency_lock_sha256,
        materialization_ids, (), native_outputs())


def native_work(context, config, prepared, parent):
    definitions = tuple(sorted((definition_for(config, prepared, seed, parent=parent,
        materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)))
        for seed in selected_seeds(config, prepared)), key=lambda d:d.subwork_id))
    roster = NativeSubworkRoster('selected.native-subwork', parent, tuple(d.identity for d in definitions))
    return PreparedNativeWork(parent, (UNIT,), slots(config), definitions, (roster,))


def _decode(context, *, conditional=False, accelerated=False):
    declared = operation_declaration(conditional=conditional, accelerated=accelerated).manifest()
    capability = declared.capability_key
    config_kind = configuration_type(conditional=conditional, accelerated=accelerated)
    if (context.task_id != capability or context.permissions != declared.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != 104+int(conditional)):
        raise ValueError('active relaxation changes its complete task/input contract')
    kinds = {config_kind.SCHEMA:(config_kind, MAX_CONFIG),
        ArrayDatasetManifest.SCHEMA:(ArrayDatasetManifest, MAX_CONFIG), MolecularRepresentation.SCHEMA:(MolecularRepresentation, MAX_MODEL),
        MatchedActiveRelaxationPlan.SCHEMA:(MatchedActiveRelaxationPlan, MAX_CONFIG),
        ActiveModelPreparation.SCHEMA:(ActiveModelPreparation, MAX_PREPARATION),
        PeriodicProbeSelection.SCHEMA:(PeriodicProbeSelection, MAX_CONFIG),
        NumericalProducingProvenance.SCHEMA:(NumericalProducingProvenance, MAX_CONFIG),
        PeriodicProbeRawSources.SCHEMA:(PeriodicProbeRawSources, MAX_RAW_SOURCES),
        CatalyticStateSeed.SCHEMA:(CatalyticStateSeed, MAX_RETURN)}
    if conditional:
        kinds[ConditionalActiveRelaxationSelection.SCHEMA] = (ConditionalActiveRelaxationSelection, MAX_CONFIG)
    received = {}
    for port in context.input_ports:
        selected = kinds.get(port.payload_schema)
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != 'application/json'
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('active relaxation changes a complete direct exposed input')
        record = decode_canonical_bytes(port.read(selected[1]), selected[0], maximum_bytes=selected[1])
        key = (record.SCHEMA, record.fingerprint())
        if key in received:
            raise ValueError('active relaxation repeats a complete direct input')
        received[key] = (port, record)
    if {schema for schema, _ in received} != set(kinds):
        raise ValueError('active relaxation omits a complete direct input')
    def unique(kind):
        rows = [r for (schema, _), r in received.items() if schema == kind.SCHEMA]
        if len(rows) != 1:
            raise ValueError('active relaxation requires one original '+kind.__name__)
        return rows[0]
    port, config = unique(config_kind)
    if context.resource_budget != resource_budget(config):
        raise ValueError('active relaxation changes its selected host/device resource allocation')
    if (config.config_id, config.fingerprint(), port.artifact_id) != (context.config.config_id, context.config.content_sha256, context.config.artifact_id):
        raise ValueError('active relaxation substitutes its selected configuration')
    representation = unique(MolecularRepresentation)[1]
    prepared = unique(ActiveModelPreparation)[1]
    sources = unique(PeriodicProbeRawSources)[1]
    expected = {(record.SCHEMA, record.fingerprint()):record for _, _, record
        in native_input_records(config, representation, prepared, sources)}
    expected[(config.SCHEMA, config.fingerprint())] = config
    if set(expected) != set(received) or any(received[key][1] != record for key, record in expected.items()):
        raise ValueError('active relaxation substitutes an exact original direct input record')
    return config, representation, prepared, sources


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ActiveRelaxationRunner:
        raise ValueError('active relaxation requires its installed native owner')
    config, _, prepared, _ = _decode(context, conditional=runner.conditional, accelerated=runner.accelerated)
    return native_work(context, config, prepared, expected_parent)


def checked_coordinates(config, representation, prepared, sources):
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    points, _ = read_initial_coordinates(sources.coordinates_utf8, len(representation.atoms), periodic=True)
    coordinates = np.asarray(points, dtype='<f8').tobytes()
    if sha256(coordinates).hexdigest() != representation.arrays.members[0].sha256:
        raise ValueError('active relaxation changes the complete original coordinate array')
    sites = {s.identity:s for s in prepared.sites}
    for site in prepared.sites:
        assess_catalytic_partition(representation=representation, prototype=config.prototype, site=site,
            protocol=prepared.protocol, coordinate_bytes=coordinates)
    for seed, previous in zip(prepared.seeds, prepared.assessments, strict=True):
        current = assess_catalytic_seed(representation=representation, site=sites[seed.site], protocol=prepared.protocol,
            seed=seed, coordinate_bytes=coordinates, cell=config.prototype.cell)
        if current != previous or current.disposition != 'SATISFIED':
            raise ValueError('active relaxation refuses an altered or independently rejected starting state before any native entry')
    return coordinates


def prepare_relaxation_work_directory(config, sources):
    root = Path(config.work_directory)
    root.mkdir(parents=False, exist_ok=True)
    if root.is_symlink() or root.resolve() != root:
        raise ValueError('active relaxation requires its original canonical work directory')
    topology = root / 'original.prmtop'
    raw_topology = sources.topology_utf8.encode('ascii')
    if topology.exists():
        if topology.is_symlink() or topology.read_bytes() != raw_topology:
            raise ValueError('active relaxation recovery changes its complete original topology')
    else:
        with topology.open('xb') as stream:
            stream.write(raw_topology)
    return root, topology


def run_relaxation_subwork(*, config, representation, prepared, seed, definition, coordinates,
        native_subwork, root, topology, returned_configuration=None, native_options=None, cost_scope=None):
    """Reuse the original native entry, completed-publication recovery and custody."""
    expected_configuration = config.identity if returned_configuration is None else returned_configuration
    completed = native_subwork.recover(definition)
    if completed is not None:
        returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'relaxation.return')),
            ActiveRelaxationReturn, maximum_bytes=MAX_RETURN)
    else:
        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
            raise ValueError('uncertain active-relaxation contact cannot be repeated')
        if config.ACCELERATED:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=config.prototype.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(config.prototype.engine))
        directory = root / definition.subwork_id
        directory.mkdir()
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)
        wall, cpu, self_cpu = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN), time.process_time()
        error = None
        try:
            from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_native import execute_active_relaxation
            site = next(site for site in prepared.sites if site.identity == seed.site)
            invoke_native_subwork(native_subwork, entry, execute_active_relaxation,
                representation=representation, site=site, protocol=prepared.protocol,
                seed=seed, prototype=config.prototype, settings=config.plan.settings,
                coordinate_bytes=coordinates, topology_path=topology, directory=directory,
                **({} if native_options is None else native_options))
        except (NativeEntryRefused, NativeSubworkObservationPublicationError):
            raise
        except Exception:
            error = traceback.format_exc()
            (directory / 'native-error.txt').write_text(error)
        try:
            authenticate_periodic_engine(config.prototype.engine, loaded=True)
        except (ValueError, OSError):
            error = ('' if error is None else error + '\n') + traceback.format_exc()
            (directory / 'engine-authentication-error.txt').write_text(error)
        census, archive_manifests = publish_directory(native_subwork, entry, directory, root, selected_census=directory_census(directory, root))
        returned = ActiveRelaxationReturn(expected_configuration, seed.identity, census, error)
        manifest = publish_record(native_subwork, entry, 'relaxation.return', returned)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        completed = native_subwork.complete(entry,
            operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
            cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                Decimal(str(time.monotonic()-wall)), Decimal(sum(m.materialization.size_bytes for m in (*archive_manifests, manifest)))),
            cost_scope=cost_scope or 'One original unrestrained full-reference relaxation attempt, fresh final force, engine check and raw publication; nested electronic calls retained; no physical trajectory time',
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            reason_codes=() if error is None else ('active-relaxation-native-failure',))
    if returned.configuration != expected_configuration or returned.seed != seed.identity:
        raise ValueError('active relaxation recovery substitutes its original selected call')
    return returned, completed


class ActiveRelaxationRunner:
    def __init__(self, *, conditional=False, accelerated=False):
        if type(conditional) is not bool or type(accelerated) is not bool:
            raise ValueError('active relaxation requires an explicit installed operation selection')
        self.conditional = conditional
        self.accelerated = accelerated
        self.manifest = operation_declaration(conditional=conditional, accelerated=accelerated).manifest()

    def preflight(self, context):
        config, _, _, _ = _decode(context, conditional=self.conditional, accelerated=self.accelerated)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.prototype.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('active relaxation backend differs from accelerated_compute')
        authenticate_periodic_engine(config.prototype.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            preflight_gpu_backend(device_memory_bytes=config.prototype.engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(config.prototype.engine))

    def execute(self, context):
        raise ValueError('active relaxation requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, prepared, sources = _decode(context, conditional=self.conditional, accelerated=self.accelerated)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.prototype.molecular)
            if context.accelerated_compute != self.accelerated:
                raise ValueError('active relaxation backend differs from accelerated_compute')
            invocation = context.prepared_invocation
            if invocation is None or invocation.implementation != config.implementation:
                raise ValueError('active relaxation changes its frozen producing source')
            authenticate_periodic_engine(config.prototype.engine)
            work = native_work(context, config, prepared, native_subwork.parent_contact)
            if invocation.native_work != work:
                raise ValueError('active relaxation changes its frozen complete native census')
            coordinates = checked_coordinates(config, representation, prepared, sources)
            root, topology = prepare_relaxation_work_directory(config, sources)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            seeds = {s.identity:s for s in prepared.seeds}
            units = []
            for definition in work.definitions:
                seed = seeds[definition.configuration]
                returned, completed = run_relaxation_subwork(config=config, representation=representation,
                    prepared=prepared, seed=seed, definition=definition, coordinates=coordinates,
                    native_subwork=native_subwork, root=root, topology=topology)
                units.append(ActiveRelaxationUnit(returned, definition, completed.completion, completed.receipt))
            capability = capability_for(config)
            if self.conditional:
                result = ConditionalActiveRelaxationResult(capability+'.result', config.identity,
                    config.plan.identity, config.model_name, tuple(units), config.selection)
            else:
                result = ActiveRelaxationResult(capability+'.result', config.identity, config.plan.identity, config.model_name, tuple(units))
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != capability+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('active relaxation changes its complete aggregate output')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck('complete-original-active-relaxation-native-census', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration(*, conditional=False, accelerated=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    if type(conditional) is not bool:
        raise ValueError('active relaxation requires an explicit installed operation selection')
    capability = ((GPU_CONDITIONAL_CAPABILITY if conditional else GPU_CAPABILITY) if accelerated
        else (CONDITIONAL_CAPABILITY if conditional else CAPABILITY))
    config_kind = configuration_type(conditional=conditional, accelerated=accelerated)
    result_kind = ConditionalActiveRelaxationResult if conditional else ActiveRelaxationResult
    return RecursiveOperationDeclaration(capability_key=capability, capability_version='1.0.0',
        implementation_id=('accelerated-' if accelerated else '')+('conditional-matched-gp-active-relaxation-v1' if conditional else 'complete-matched-gp-active-relaxation-v1'),
        kind=CapabilityKind.SIMULATOR, config_record_type=config_kind, stage=ScientificStage.ACQUIRE,
        input_ports=tuple(sorted((RecursivePortContract('native-arrays', ArrayDatasetManifest.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-model', MolecularRepresentation.SCHEMA, 'application/json', MAX_MODEL),
            RecursivePortContract('native-plan', MatchedActiveRelaxationPlan.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-preparation', ActiveModelPreparation.SCHEMA, 'application/json', MAX_PREPARATION),
            RecursivePortContract('native-prototype', PeriodicProbeSelection.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-seed', CatalyticStateSeed.SCHEMA, 'application/json', MAX_RETURN,
                minimum_count=96, maximum_count=96),
            RecursivePortContract('native-source', PeriodicProbeRawSources.SCHEMA, 'application/json', MAX_RAW_SOURCES),
            *((RecursivePortContract('native-conditional-selection', ConditionalActiveRelaxationSelection.SCHEMA,
                'application/json', MAX_CONFIG),) if conditional else ())), key=lambda port:port.port_id)),
        outputs=(OutputTemplate('product', result_kind.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-direct-molecular-inputs', 'matched-four-material-plan',
            'explicit-matched-conditional-state-selection' if conditional else 'complete-eight-site-state-census',
            'original-return-before-assessment', 'original-custody-no-replay'))),
        runner_factory=(lambda:ActiveRelaxationRunner(conditional=conditional, accelerated=accelerated)) if conditional or accelerated else ActiveRelaxationRunner,
        record_codecs={c.SCHEMA:c for c in (config_kind,
            result_kind, ActiveModelPreparation, MatchedActiveRelaxationPlan, MolecularRepresentation,
            ArrayDatasetManifest, PeriodicProbeSelection, PeriodicProbeRawSources, NumericalProducingProvenance, CatalyticStateSeed,
            *((ConditionalActiveRelaxationSelection,) if conditional else ()))},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,), native_effect_slot_ids=slots, scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment))
