# SPDX-License-Identifier: MPL-2.0
"""Registered finite preparation prefixes using the existing native lifecycle."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_evaluation import CompletePreparationEvaluation
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import ActivePreparationPrefixSelection, validate_prefix_member
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import AcceleratedConditionalActiveRelaxationConfig, ActiveRelaxationReturn, ConditionalActiveRelaxationConfig, MAX_CONFIG, MAX_PREPARATION, MAX_RETURN, checked_coordinates, native_input_records as relaxation_input_records, native_outputs, operands as relaxation_operands, prepare_relaxation_work_directory, resource_budget as relaxation_resource_budget, run_relaxation_subwork, selected_seeds, validate_relaxation_native_unit
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ConditionalActiveRelaxationSelection, MatchedActiveRelaxationPlan
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET, GPU_RESOURCE_CEILING, MAX_MODEL, MAX_RAW_SOURCES, UNIT, PeriodicProbeRawSources
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, authenticate_periodic_engine
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import PreparationResponseContext
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment

CAPABILITY = 'rubisco-response.active-preparation-prefix'
GPU_CAPABILITY = 'rubisco-response.accelerated-active-preparation-prefix'


@dataclass(frozen=True, slots=True)
class ActivePreparationPrefixConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-prefix-config'
    ACCELERATED: ClassVar[bool] = False
    config_id: str
    original: ConditionalActiveRelaxationConfig
    prefix: ActivePreparationPrefixSelection
    scientific_context: PreparationResponseContext | None = None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.original, AcceleratedConditionalActiveRelaxationConfig if self.ACCELERATED else ConditionalActiveRelaxationConfig)
        validate_prefix_member(prefix=self.prefix, plan=self.original.plan, model_name=self.original.model_name,
                               conditional_selection=self.original.selection)
        if self.scientific_context is not None:
            exact(self.scientific_context, PreparationResponseContext)
            coordinate = dict(self.scientific_context.design.formation_coordinates)[self.original.model_name]
            if (self.scientific_context.design.prefix != self.prefix
                    or coordinate.representation != self.original.prototype.representation
                    or coordinate.preparation != self.original.preparation
                    or coordinate.site_id != self.original.prototype.path.reactive_site_id):
                raise ValueError('preparation prefix changes its selected downstream receiver or original model')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class AcceleratedActivePreparationPrefixConfig(ActivePreparationPrefixConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-active-preparation-prefix-config'
    ACCELERATED: ClassVar[bool] = True
    original: AcceleratedConditionalActiveRelaxationConfig


def config_type(accelerated=False, *, continuation=False):
    if type(accelerated) is not bool or type(continuation) is not bool:
        raise TypeError('preparation prefix needs an explicit CPU/GPU selection')
    if continuation:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import continuation_config_types
        return continuation_config_types()[int(accelerated)]
    return AcceleratedActivePreparationPrefixConfig if accelerated else ActivePreparationPrefixConfig


def config_types():
    return tuple(config_type(flag, continuation=continued)
                 for flag in (False, True) for continued in (False, True))


def capability_for(config):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import continuation_config_types, CAPABILITY as CONTINUE, GPU_CAPABILITY as GPU_CONTINUE
    if type(config) in continuation_config_types():
        return GPU_CONTINUE if config.ACCELERATED else CONTINUE
    if type(config) not in (ActivePreparationPrefixConfig, AcceleratedActivePreparationPrefixConfig):
        raise TypeError('preparation prefix requires its exact registered configuration')
    return GPU_CAPABILITY if config.ACCELERATED else CAPABILITY


def node_id(config):
    return capability_for(config) + '.' + config.original.model_name


def resource_budget(config):
    capability_for(config)
    return relaxation_resource_budget(config.original)


def operands(config):
    context = config.scientific_context
    continuation = getattr(config, 'continuation', None)
    return tuple(sorted({config.identity, config.prefix.identity, *relaxation_operands(config.original),
        *((continuation.identity, continuation.readout.identity,
           continuation.readout.original_result.configuration, continuation.archive_identity) if continuation is not None else ()),
        *((context.identity, context.original_root.identity) if context is not None else ())},
                        key=lambda p: p.object_id))


def native_input_records(config, representation, prepared, sources):
    capability_for(config)
    context = config.scientific_context
    continuation = getattr(config, 'continuation', None)
    if continuation is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_prefix_config
        first = original_prefix_config(config)
    return tuple(sorted((*relaxation_input_records(config.original, representation, prepared, sources),
        ('native-relaxation-selection', config.original.identity, config.original),
        ('native-prefix-selection', config.prefix.identity, config.prefix),
        *((('native-continuation', continuation.identity, continuation),
           ('native-original-prefix-config', first.identity, first),
           ('original-prefix-assessment', continuation.readout.identity, continuation.readout)) if continuation is not None else ()),
        *((('native-response-context', context.identity, context),
           ('original-root-assessment', context.original_root.identity, context.original_root))
          if context is not None else ())), key=lambda row: row[0]))


def input_artifact_id(config, name, pin):
    """Use the original contribution's artifact identity for history inputs."""
    parent = (config.scientific_context.parent if name == 'original-root-assessment' else
              config.continuation.parent if name == 'original-prefix-assessment' else None)
    if parent is None:
        return pin.object_id
    product, = (row for row in parent.products if row.record == pin)
    return product.artifact.artifact_id


def slots(config):
    return ('native.active-preparation-prefix.' + config.fingerprint(),)


def definition_for(config, prepared, *, parent, materialization_ids):
    seed, = selected_seeds(config.original, prepared)
    return NativeSubworkDefinition('active-prefix.' + config.original.model_name, CAPABILITY, parent,
        seed.identity, operands(config), config.original.implementation.code_sources_sha256,
        config.original.implementation.dependency_lock_sha256, materialization_ids, (), native_outputs())


def native_work(context, config, prepared, parent):
    definition = definition_for(config, prepared, parent=parent,
        materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (UNIT,), slots(config), (definition,), (roster,))


@dataclass(frozen=True, slots=True)
class ActivePreparationPrefixUnit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-prefix-unit'
    returned: ActiveRelaxationReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        validate_relaxation_native_unit(self, operation_ids=(CAPABILITY,))


@dataclass(frozen=True, slots=True)
class ActivePreparationPrefixResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-prefix-result'
    result_id: str
    configuration: ObjectIdentity
    prefix: ActivePreparationPrefixSelection
    model_name: str
    unit: ActivePreparationPrefixUnit
    scope: str = 'ORIGINAL_FINITE_PREPARATION_ATTEMPT_WITH_UNSELECTED_STATES_UNMEASURED'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.configuration, ObjectIdentity)
        exact(self.prefix, ActivePreparationPrefixSelection)
        exact(self.unit, ActivePreparationPrefixUnit)
        self.prefix.allowance_for(self.model_name)
        if (self.unit.returned.configuration != self.configuration
                or self.unit.definition.subwork_id != 'active-prefix.' + self.model_name
                or self.prefix.identity not in self.unit.definition.sources
                or self.scope != 'ORIGINAL_FINITE_PREPARATION_ATTEMPT_WITH_UNSELECTED_STATES_UNMEASURED'):
            raise ValueError('preparation prefix result changes original scope or receipt-bound selection')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


def _decode(context, *, accelerated, continuation=False):
    kind = config_type(accelerated, continuation=continuation)
    original_kind = AcceleratedConditionalActiveRelaxationConfig if accelerated else ConditionalActiveRelaxationConfig
    declared = operation_declaration(accelerated=accelerated, continuation=continuation).manifest()
    kinds = {cls.SCHEMA: (cls, ceiling) for cls, ceiling in (
        (kind, MAX_CONFIG * 2), (original_kind, MAX_CONFIG), (ActivePreparationPrefixSelection, MAX_CONFIG),
        (ArrayDatasetManifest, MAX_CONFIG), (MolecularRepresentation, MAX_MODEL),
        (MatchedActiveRelaxationPlan, MAX_CONFIG), (ActiveModelPreparation, MAX_PREPARATION),
        (PeriodicProbeSelection, MAX_CONFIG), (NumericalProducingProvenance, MAX_CONFIG),
        (PeriodicProbeRawSources, MAX_RAW_SOURCES), (CatalyticStateSeed, MAX_RETURN),
        (ConditionalActiveRelaxationSelection, MAX_CONFIG),
        (PreparationResponseContext, MAX_CONFIG), (InitialRootScopedAssessment, MAX_CONFIG))}
    if continuation:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import ActivePreparationContinuation
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
        from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RAW_SCHEMA
        kinds[ActivePreparationContinuation.SCHEMA] = (ActivePreparationContinuation, MAX_CONFIG * 2)
        kinds[config_type(accelerated).SCHEMA] = (config_type(accelerated), MAX_CONFIG * 2)
        kinds[ActivePreparationPrefixReadout.SCHEMA] = (ActivePreparationPrefixReadout, MAX_CONFIG)
        archive_ports = [p for p in context.input_ports if p.payload_schema == RAW_SCHEMA]
        if len(archive_ports) != 1:
            raise ValueError('preparation continuation requires its complete original archive input')
        archive_port, = archive_ports
    else:
        archive_port = None
    extra = 4 if continuation else 0
    if (context.permissions != declared.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or len(context.input_ports) not in (107 + extra, 109 + extra)):
        raise ValueError('preparation prefix changes its complete direct input contract')
    received = {}
    for port in context.input_ports:
        if port is archive_port:
            continue
        selected = kinds.get(port.payload_schema)
        if (selected is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != 'application/json'
                or port.size_bytes > selected[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('preparation prefix changes a direct original input')
        record = port.decode_canonical_record(selected[0], maximum_bytes=selected[1])
        key = (record.SCHEMA, record.fingerprint())
        if key in received:
            raise ValueError('preparation prefix repeats a direct input')
        received[key] = (port, record)
    def unique(cls):
        found = [value for (schema, _), value in received.items() if schema == cls.SCHEMA]
        if len(found) != 1:
            raise ValueError('preparation prefix omits or repeats ' + cls.__name__)
        return found[0]
    port, config = unique(kind)
    if len(context.input_ports) != (107 if config.scientific_context is None else 109) + extra:
        raise ValueError('preparation prefix changes its original inquiry input census')
    if (context.task_id != node_id(config) or context.resource_budget != resource_budget(config)
            or (config.config_id, config.fingerprint(), port.artifact_id) !=
                (context.config.config_id, context.config.content_sha256, context.config.artifact_id)):
        raise ValueError('preparation prefix substitutes its configuration or resource allocation')
    representation = unique(MolecularRepresentation)[1]
    prepared = unique(ActiveModelPreparation)[1]
    sources = unique(PeriodicProbeRawSources)[1]
    expected = {(record.SCHEMA, record.fingerprint()): (input_artifact_id(config, name, pin), record)
                for name, pin, record in native_input_records(config, representation, prepared, sources)}
    expected[(config.SCHEMA, config.fingerprint())] = (config.identity.object_id, config)
    if (set(expected) != set(received) or any(received[key][0].artifact_id != artifact_id
            or received[key][0].size_bytes != record.canonical_size_bytes()
            or received[key][1] != record for key, (artifact_id, record) in expected.items())):
        raise ValueError('preparation prefix substitutes an exact original operand')
    if archive_port is not None:
        selected = config.continuation.archive
        if (archive_port.artifact_id != selected.logical.logical_artifact_id
                or archive_port.payload_schema != selected.logical.payload_schema
                or archive_port.media_type != selected.logical.media_type
                or archive_port.size_bytes != selected.materialization.size_bytes
                or archive_port.kind is not WorkerInputKind.EXTERNAL
                or archive_port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or archive_port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('preparation continuation substitutes its original archive binding')
    return config, representation, prepared, sources


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ActivePreparationPrefixRunner:
        raise ValueError('preparation prefix requires its registered native owner')
    config, representation, prepared, sources = _decode(context, accelerated=runner.accelerated, continuation=runner.continuation)
    checked_coordinates(config.original, representation, prepared, sources)
    return native_work(context, config, prepared, expected_parent)


class ActivePreparationPrefixRunner:
    def __init__(self, *, accelerated=False, continuation=False):
        config_type(accelerated, continuation=continuation)
        self.accelerated = accelerated
        self.continuation = continuation
        self.manifest = operation_declaration(accelerated=accelerated, continuation=continuation).manifest()

    def preflight(self, context):
        config, _, _, _ = _decode(context, accelerated=self.accelerated, continuation=self.continuation)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.original.prototype.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('preparation prefix changes its selected accelerated backend')
        authenticate_periodic_engine(config.original.prototype.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            engine = config.original.prototype.engine
            preflight_gpu_backend(device_memory_bytes=engine.device_memory_bytes,
                                  molecular_platform=periodic_molecular_platform(engine))

    def execute(self, context):
        raise ValueError('preparation prefix requires the ordinary native lifecycle')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, prepared, sources = _decode(context, accelerated=self.accelerated, continuation=self.continuation)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.original.prototype.molecular)
            original = config.original
            if (context.accelerated_compute != self.accelerated or context.prepared_invocation is None
                    or context.prepared_invocation.implementation != original.implementation):
                raise ValueError('preparation prefix substitutes its accepted producing source')
            authenticate_periodic_engine(original.prototype.engine)
            work = native_work(context, config, prepared, native_subwork.parent_contact)
            if context.prepared_invocation.native_work != work:
                raise ValueError('preparation prefix changes the original selected native work')
            coordinates = checked_coordinates(original, representation, prepared, sources)
            resume = None
            configuration = config.identity
            if self.continuation:
                from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration, read_continuation_files
                selected = config.continuation
                port, = (p for p in context.input_ports if p.artifact_id == selected.archive_identity.object_id)
                resume = read_continuation_files(selected, port.read(selected.archive.materialization.size_bytes),
                    representation=representation, prepared=prepared, coordinate_bytes=coordinates)
                configuration = original_configuration(config)
            root, topology = prepare_relaxation_work_directory(original, sources)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            definition, = work.definitions
            seed, = selected_seeds(original, prepared)
            returned, completed = run_relaxation_subwork(config=original, representation=representation,
                prepared=prepared, seed=seed, definition=definition, coordinates=coordinates,
                native_subwork=native_subwork, root=root, topology=topology, returned_configuration=configuration,
                native_options=dict(prefix_selection=config.prefix, model_name=original.model_name, configuration=configuration,
                    **({'continuation': resume} if resume is not None else {})),
                cost_scope='One finite unrestrained preparation purchase; complete evaluations, accepted optimizer states, failures and publication retained; no physical trajectory time')
            unit = ActivePreparationPrefixUnit(returned, definition, completed.completion, completed.receipt)
            result = ActivePreparationPrefixResult(node_id(config) + '.result', configuration, config.prefix,
                                                    original.model_name, unit)
            from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout, read_preparation_prefix
            assessed = read_preparation_prefix(config=config, representation=representation, prepared=prepared,
                coordinate_bytes=coordinates, original_result=result, native_subwork=native_subwork,
                assessor_source=ObjectIdentity.from_record('source.active-preparation-assessor.' +
                    original.implementation.code_sources_sha256, original.implementation),
                readout_id=node_id(config) + '.assessment')
            values = {node_id(config) + '.product': result, node_id(config) + '.assessment': assessed}
            if (len(context.output_ports) != 2 or {p.output_id for p in context.output_ports} != set(values)
                    or any(p.payload_schema != values[p.output_id].SCHEMA for p in context.output_ports)
                    or type(assessed) is not ActivePreparationPrefixReadout):
                raise ValueError('preparation prefix changes its complete original output')
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, values[port.output_id].canonical_bytes())
                for port in context.output_ports),
                (ReceiptCheck('complete-original-preparation-prefix-custody', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration(*, accelerated=False, continuation=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_translation import prepare_root, validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import operation_declaration as relaxation_declaration
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import inquiry_hooks
    kind = config_type(accelerated, continuation=continuation)
    original_kind = AcceleratedConditionalActiveRelaxationConfig if accelerated else ConditionalActiveRelaxationConfig
    ports = relaxation_declaration(conditional=True, accelerated=accelerated).input_ports
    extra_ports, extra_records, storage = (), (), ()
    capability = GPU_CAPABILITY if accelerated else CAPABILITY
    if continuation:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import ActivePreparationContinuation, CAPABILITY as CONTINUE, GPU_CAPABILITY as GPU_CONTINUE
        from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RAW_SCHEMA
        capability = GPU_CONTINUE if accelerated else CONTINUE
        extra_ports = (
            RecursivePortContract('native-continuation', ActivePreparationContinuation.SCHEMA, 'application/json', MAX_CONFIG * 2),
            RecursivePortContract('native-original-prefix-config', config_type(accelerated).SCHEMA, 'application/json', MAX_CONFIG * 2),
            RecursivePortContract('original-prefix-assessment', ActivePreparationPrefixReadout.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-continuation-archive', RAW_SCHEMA,
                'application/gzip', None))
        extra_records = (ActivePreparationContinuation, config_type(accelerated))
        from empirical_lawhood.storage.captured_gzip_codec import CAPTURED_GZIP_CODEC
        storage = (CAPTURED_GZIP_CODEC,)
    return RecursiveOperationDeclaration(capability_key=capability,
        capability_version='1.0.0', implementation_id='paired-active-preparation-prefix-v1',
        kind=CapabilityKind.SIMULATOR, config_record_type=kind, stage=ScientificStage.ACQUIRE,
        input_ports=tuple(sorted((*ports, *extra_ports,
            RecursivePortContract('native-prefix-selection', ActivePreparationPrefixSelection.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-relaxation-selection', original_kind.SCHEMA, 'application/json', MAX_CONFIG),
            RecursivePortContract('native-response-context', PreparationResponseContext.SCHEMA, 'application/json', MAX_CONFIG,
                minimum_count=0, maximum_count=1),
            RecursivePortContract('original-root-assessment', InitialRootScopedAssessment.SCHEMA, 'application/json', MAX_CONFIG,
                minimum_count=0, maximum_count=1)), key=lambda p: p.port_id)),
        outputs=(OutputTemplate('assessment', ActivePreparationPrefixReadout.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
            OutputTemplate('product', ActivePreparationPrefixResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                                  CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=('accepted-checkpoint-before-next-native-effect', 'complete-paired-prefix-census', 'original-custody-no-replay'),
        runner_factory=lambda: ActivePreparationPrefixRunner(accelerated=accelerated, continuation=continuation),
        storage_codecs=storage,
        record_codecs={cls.SCHEMA: cls for cls in (kind, original_kind, *extra_records, ActivePreparationPrefixResult,
            ActivePreparationPrefixSelection, ActivePreparationPrefixUnit, ActivePreparationCheckpoint, CompletePreparationEvaluation,
            ActiveModelPreparation, MatchedActiveRelaxationPlan, MolecularRepresentation, ArrayDatasetManifest,
            PeriodicProbeSelection, PeriodicProbeRawSources, NumericalProducingProvenance, CatalyticStateSeed,
            ConditionalActiveRelaxationSelection, PreparationResponseContext, InitialRootScopedAssessment, ActivePreparationPrefixReadout)},
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda c: tuple(sorted({p.object_fingerprint for p in operands(c)})),
            scientific_unit_ids=lambda c: (UNIT,), native_effect_slot_ids=slots,
            scientific_root_preparer=prepare_root, scientific_root_validator=validate_root),
        inquiry_hooks=inquiry_hooks(),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment))
