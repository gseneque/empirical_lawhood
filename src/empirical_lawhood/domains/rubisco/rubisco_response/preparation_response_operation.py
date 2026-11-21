# SPDX-License-Identifier: MPL-2.0
"""One checkpoint-bound response effect through ordinary periodic native custody."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveStorageCodec
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import run_periodic_point_subwork
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET, UNIT, GRADIENT_UNIT, MAX_CONFIG, MAX_MODEL, MAX_RAW_SOURCES, GPU_RESOURCE_CEILING, PeriodicProbeConfig, AcceleratedPeriodicProbeConfig, PeriodicProbeRawSources, PeriodicProbeResult, native_input_records as original_probe_inputs, probe_outputs, resource_budget as probe_resource_budget
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, authenticate_periodic_engine
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import EnvironmentalPreparationResponseDesign, PreparationResponseDesign, PreparationResponseFrame, diagnostic_stages, is_environmental, require_response_design, response_stages
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import EnvironmentalPreparationResponseAssessment, PreparationResponseAssessment, require_response_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import CENTER_SCHEMA, MAX_CENTER_BYTES, PreparationResponseCenter, PreparationResponsePoint, response_point_coordinates, validate_response_operands

CAPABILITY = 'rubisco-response.preparation-response-point'
GPU_CAPABILITY = 'rubisco-response.accelerated-preparation-response-point'


def validate_center_stream(source, request, *, size):
    from empirical_lawhood.storage.artifact_stream_primitives import ArtifactIdentityConflict
    if (request.payload_schema != CENTER_SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != 'application/octet-stream' or request.semantic_validation is not None
            or not 0 < size <= MAX_CENTER_BYTES or size % 48):
        raise ArtifactIdentityConflict('response center changes complete binary64 coordinate/gradient transport')


CENTER_CODEC = RecursiveStorageCodec('rubisco.preparation-response-center.f64', CENTER_SCHEMA, '1.0.0',
    ArtifactProfile.RAW_SOURCE_BYTES, 'application/octet-stream', '.bin', validate_center_stream, MAX_CENTER_BYTES)


@dataclass(frozen=True, slots=True)
class PreparationResponseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-config'
    ACCELERATED: ClassVar[bool] = False
    config_id: str
    original: PeriodicProbeConfig
    protocol: PreparationResponseDesign | EnvironmentalPreparationResponseDesign
    center: PreparationResponseCenter
    frame: PreparationResponseFrame
    point: PreparationResponsePoint
    preparation_parent: ContributionManifest | None = None
    diagnostic: PreparationResponseAssessment | EnvironmentalPreparationResponseAssessment | None = None
    diagnostic_parent: ContributionManifest | None = None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.original, AcceleratedPeriodicProbeConfig if self.ACCELERATED else PeriodicProbeConfig)
        exact(self.point, PreparationResponsePoint)
        require_response_design(self.protocol)
        validate_response_operands(self.protocol, self.center, self.frame, self.point.effect, self.original.selection)
        if (self.point.center, self.point.frame) != (self.center.identity, self.frame.identity):
            raise ValueError('response configuration substitutes its frozen checkpoint or frame')
        if self.preparation_parent is not None:
            exact(self.preparation_parent, ContributionManifest)
            if len([p for p in self.preparation_parent.products if p.record == self.center.original_readout.identity]) != 1:
                raise ValueError('response configuration loses its actual preparation contribution')
        if (self.diagnostic is None) != (self.diagnostic_parent is None):
            raise ValueError('response configuration requires the actual diagnostic and its contribution together')
        first_stage = response_stages(self.protocol)[0]
        environmental = is_environmental(self.protocol)
        if environmental and self.point.effect.stage != first_stage and (
                self.preparation_parent is None or self.diagnostic is None):
            raise ValueError('environmental response requires its original preparation and initial diagnostic suppliers')
        if self.preparation_parent is not None and self.point.effect.stage != first_stage and self.diagnostic is None:
            raise ValueError('a contributed response successor requires its original diagnostic assessment')
        if self.diagnostic is not None:
            require_response_assessment(self.diagnostic)
            exact(self.diagnostic_parent, ContributionManifest)
            if (self.point.effect.stage == first_stage or self.diagnostic.design != self.protocol
                    or len([p for p in self.diagnostic_parent.products if p.record == self.diagnostic.identity]) != 1):
                raise ValueError('response configuration substitutes its original diagnostic supplier')
            if environmental:
                if type(self.diagnostic) is not EnvironmentalPreparationResponseAssessment:
                    raise ValueError('environmental response requires the exact original environmental assessment')
                nomination = self.diagnostic.nomination
                initial = tuple(c for c in self.diagnostic.coverage if c.stage == 'initial-primary')
                if (nomination is None or nomination.disposition != 'AVAILABLE' or len(initial) != 8
                        or any(c.state != 'AVAILABLE' for c in initial)):
                    raise ValueError('environmental response requires an available nomination from all eight initial returns')
                from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import validate_environmental_frame
                validate_environmental_frame(design=self.protocol, frame=self.frame, nomination=nomination)
                if self.point.effect.stage == 'environment-diagnostic' and (any(
                        c.point is not None or c.original_readout is not None for c in self.diagnostic.coverage
                        if c.stage != 'initial-primary') or any(c.state != 'NOT_ENTERED'
                        for c in self.diagnostic.coverage if c.stage in ('environment-diagnostic', 'challenge'))):
                    raise ValueError('environmental direction must be frozen before later or finite outcomes')
            if self.point.prediction is not None:
                metrics = {(q.name, q.model_name, q.position): q.value for q in self.diagnostic.quantities}
                prediction = self.point.prediction
                model, position = self.point.effect.model_name, self.point.effect.position
                actions = [a.action for a in self.diagnostic.actions if
                    (a.model_name, a.position, a.direction, a.step_bohr) == (model, position, 'primary', self.protocol.steps_bohr[1])]
                if (prediction.diagnostic_assessment != self.diagnostic.identity or actions != [prediction.primary_action]
                        or self.diagnostic.questions[0].disposition != 'EMPIRICALLY_CONSISTENT'
                        or any(c.state != 'AVAILABLE' for c in self.diagnostic.coverage if c.stage in diagnostic_stages(self.protocol))
                        or any(c.state != 'NOT_ENTERED' or c.point is not None for c in self.diagnostic.coverage if c.stage == 'challenge')
                        or tuple(getattr(prediction, name) for name in ('base_receiver_hartree_per_bohr',
                            'predicted_change_hartree_per_bohr', 'scalar_change_hartree_per_bohr',
                            'omitted_change_hartree_per_bohr', 'scale_change_hartree_per_bohr'))
                        != tuple(metrics.get((name, model, position)) for name in ('base-receiver', 'predicted-change',
                            'scalar-predicted-change', 'omitted-coupling-change', 'prediction-scale-discrepancy'))):
                    raise ValueError('response prediction differs from its original pre-reveal diagnostic assessment')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class AcceleratedPreparationResponseConfig(PreparationResponseConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-preparation-response-config'
    ACCELERATED: ClassVar[bool] = True
    original: AcceleratedPeriodicProbeConfig


def config_type(accelerated=False):
    if type(accelerated) is not bool:
        raise TypeError('response requires an explicit Boolean backend')
    return AcceleratedPreparationResponseConfig if accelerated else PreparationResponseConfig


def capability_for(config):
    if type(config) not in (PreparationResponseConfig, AcceleratedPreparationResponseConfig):
        raise TypeError('response requires its exact selected configuration revision')
    return GPU_CAPABILITY if config.ACCELERATED else CAPABILITY


def node_id(config):
    return capability_for(config) + '.' + config.point.effect.stage + '.' + f'{config.point.effect.ordinal:08d}'


def resource_budget(config):
    capability_for(config)
    return probe_resource_budget(config.original)


def selected_request(config):
    return CoupledEvaluationRequest(config.point.point_id + '.evaluation', config.protocol.identity,
        config.original.selection.representation, config.point.identity, config.original.provenance.identity,
        config.original.selection.physical_atom_count, gradient_unit=GRADIENT_UNIT)


def design_input_name(config):
    return 'native-environment-design' if is_environmental(config.protocol) else 'native-design'


def diagnostic_input_name(config):
    return ('original-environment-diagnostic-assessment' if is_environmental(config.protocol)
        else 'original-diagnostic-assessment')


def native_input_records(config, representation, sources):
    capability_for(config)
    original_probe_inputs(config.original, representation, sources)
    return (('native-arrays', config.center.arrays.identity, config.center.arrays),
        ('native-center', config.center.identity, config.center),
        ('native-checkpoint', config.center.checkpoint.identity, config.center.checkpoint),
        (design_input_name(config), config.protocol.identity, config.protocol),
        ('native-frame', config.frame.identity, config.frame),
        ('native-model', representation.identity, representation),
        ('native-point', config.point.identity, config.point),
        ('native-prototype', config.original.selection.identity, config.original.selection),
        ('native-provenance', config.original.provenance.identity, config.original.provenance),
        ('native-request', selected_request(config).identity, selected_request(config)),
        ('native-source', sources.identity, sources),
        ('original-preparation-assessment', config.center.original_readout.identity, config.center.original_readout),
        *(((diagnostic_input_name(config), config.diagnostic.identity, config.diagnostic),) if config.diagnostic is not None else ()))


def operands(config):
    return tuple(sorted({config.identity, config.protocol.identity, config.center.identity,
        config.center.center_bytes, config.center.checkpoint.identity, config.frame.identity, config.point.identity,
        config.original.selection.identity, config.original.selection.representation,
        config.original.raw_sources, config.original.provenance.identity,
        *((config.diagnostic.identity,) if config.diagnostic is not None else ())}, key=lambda p: p.object_id))


def slots(config):
    return ('native.preparation-response.' + config.point.fingerprint(),)


def definition_for(config, *, parent, materialization_ids):
    return NativeSubworkDefinition(config.point.point_id, 'rubisco-response.molecular-force-probe', parent,
        selected_request(config).identity, operands(config), config.original.implementation.code_sources_sha256,
        config.original.implementation.dependency_lock_sha256, materialization_ids, (), probe_outputs())


def native_work(context, config, parent):
    definition = definition_for(config, parent=parent,
        materialization_ids=tuple(sorted(p.materialization_id for p in context.input_ports)))
    roster = NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,))
    return PreparedNativeWork(parent, (UNIT,), slots(config), (definition,), (roster,))


def checked_coordinates(config, representation, sources, center_bytes):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    original_coordinates(config.original.selection, representation, sources)
    if is_environmental(config.protocol):
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import validate_environment_model
        validate_environment_model(config.protocol.environment, representation, config.center.model_name)
    xyz = response_point_coordinates(design=config.protocol, center=config.center, frame=config.frame,
        effect=config.point.effect, prototype=config.original.selection, center_bytes=center_bytes)
    if sha256(xyz.tobytes()).hexdigest() != config.point.coordinate_sha256:
        raise ValueError('response point substitutes its actual full physical displacement')
    return xyz


def _decode(context, *, accelerated):
    declared = operation_declaration(accelerated=accelerated).manifest()
    selected_type = config_type(accelerated)
    if (context.permissions != declared.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or len(context.input_ports) not in (14, 15)):
        raise ValueError('response point changes its complete direct input contract')
    kinds = {kind.SCHEMA: (kind, bound) for kind, bound in (
        (selected_type, MAX_CONFIG), (ArrayDatasetManifest, MAX_CONFIG), (PreparationResponseCenter, MAX_CONFIG),
        (ActivePreparationCheckpoint, MAX_CONFIG),
        (PreparationResponseDesign, MAX_CONFIG), (EnvironmentalPreparationResponseDesign, MAX_CONFIG),
        (PreparationResponseFrame, MAX_CONFIG),
        (MolecularRepresentation, MAX_MODEL), (PreparationResponsePoint, MAX_CONFIG),
        (PeriodicProbeSelection, MAX_CONFIG), (NumericalProducingProvenance, MAX_CONFIG),
        (CoupledEvaluationRequest, MAX_CONFIG), (PeriodicProbeRawSources, MAX_RAW_SOURCES),
        (ActivePreparationPrefixReadout, MAX_CONFIG))}
    for kind in (PreparationResponseAssessment, EnvironmentalPreparationResponseAssessment):
        kinds[kind.SCHEMA] = (kind, MAX_CONFIG)
    kinds[CENTER_SCHEMA] = (None, MAX_CENTER_BYTES)
    received = {}
    for port in context.input_ports:
        kind = kinds.get(port.payload_schema)
        media = 'application/octet-stream' if port.payload_schema == CENTER_SCHEMA else 'application/json'
        if (kind is None or port.kind is not WorkerInputKind.EXTERNAL or port.media_type != media
                or port.size_bytes > kind[1] or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY or port.payload_schema in received):
            raise ValueError('response point changes a complete original exposed input')
        received[port.payload_schema] = (port, port.read(kind[1]) if kind[0] is None else
            port.decode_canonical_record(kind[0], maximum_bytes=kind[1]))
    if selected_type.SCHEMA not in received:
        raise ValueError('response point omits its original configuration')
    port, config = received[selected_type.SCHEMA]
    alternatives = {PreparationResponseDesign.SCHEMA, EnvironmentalPreparationResponseDesign.SCHEMA,
        PreparationResponseAssessment.SCHEMA, EnvironmentalPreparationResponseAssessment.SCHEMA}
    expected = (set(kinds) - alternatives) | {config.protocol.SCHEMA}
    if config.diagnostic is not None:
        expected.add(config.diagnostic.SCHEMA)
    if set(received) != expected:
        raise ValueError('response point changes its exact original design or diagnostic input census')
    if ((config.config_id, config.fingerprint(), port.artifact_id) !=
            (context.config.config_id, context.config.content_sha256, context.config.artifact_id)
            or context.task_id != node_id(config) or context.resource_budget != resource_budget(config)):
        raise ValueError('response point changes its selected task, source or allocation')
    representation, sources = received[MolecularRepresentation.SCHEMA][1], received[PeriodicProbeRawSources.SCHEMA][1]
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import history_parent
    for name, pin, record in native_input_records(config, representation, sources):
        parent = history_parent(config, name)
        artifact_id = pin.object_id if parent is None else next(
            p.artifact.artifact_id for p in parent.products if p.record == pin)
        port, actual = received[record.SCHEMA]
        if (port.artifact_id != artifact_id or port.size_bytes != record.canonical_size_bytes()
                or actual != record):
            raise ValueError('response point substitutes its exact original scientific input')
    if received[CENTER_SCHEMA][0].artifact_id != config.center.center_bytes.object_id:
        raise ValueError('response point substitutes its original binary-array identity')
    raw = received[CENTER_SCHEMA][1]
    checked_coordinates(config, representation, sources, raw)
    return config, representation, sources, raw


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not PreparationResponseRunner:
        raise ValueError('response point requires its installed native owner')
    config, _, _, _ = _decode(context, accelerated=runner.accelerated)
    return native_work(context, config, expected_parent)


def execute_response_point(*, prototype, protocol, point, representation, sources, directory,
                           center, frame, center_bytes):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import _execute_periodic_at_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_operator_options
    xyz = response_point_coordinates(design=protocol, center=center, frame=frame, effect=point.effect,
        prototype=prototype, center_bytes=center_bytes)
    if sha256(xyz.tobytes()).hexdigest() != point.coordinate_sha256:
        raise ValueError('native response point changes its frozen physical displacement')
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('native response requires its existing fresh absolute work directory')
    return _execute_periodic_at_coordinates(representation=representation, selection=prototype.path,
        settings=prototype.electronic, mm_settings=prototype.molecular, cell=prototype.cell,
        raw_topology=sources.topology_utf8.encode('ascii'), raw_coordinates=sources.coordinates_utf8.encode('ascii'),
        coordinates=xyz, root=root, coordinate_records=(('response-design.json', protocol),
            ('response-point.json', point), ('response-center.json', center), ('response-frame.json', frame)),
        **periodic_operator_options(prototype.engine))


class PreparationResponseRunner:
    def __init__(self, *, accelerated=False):
        config_type(accelerated)
        self.accelerated = accelerated
        self.manifest = operation_declaration(accelerated=accelerated).manifest()

    def preflight(self, context):
        config, _, _, _ = _decode(context, accelerated=self.accelerated)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
        require_current_periodic_mm_settings(config.original.selection.molecular)
        if context.accelerated_compute != self.accelerated:
            raise ValueError('response point changes its selected accelerated backend')
        authenticate_periodic_engine(config.original.selection.engine)
        if self.accelerated:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
            engine = config.original.selection.engine
            preflight_gpu_backend(device_memory_bytes=engine.device_memory_bytes,
                molecular_platform=periodic_molecular_platform(engine))

    def execute(self, context):
        raise ValueError('response point requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, representation, sources, raw = _decode(context, accelerated=self.accelerated)
            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
            require_current_periodic_mm_settings(config.original.selection.molecular)
            if (context.accelerated_compute != self.accelerated or context.prepared_invocation is None
                    or context.prepared_invocation.implementation != config.original.implementation):
                raise ValueError('response point changes its accepted producing source')
            authenticate_periodic_engine(config.original.selection.engine)
            work = native_work(context, config, native_subwork.parent_contact)
            if context.prepared_invocation.native_work != work:
                raise ValueError('response point changes its frozen native census')
            root = Path(config.original.work_directory)
            root.mkdir(parents=False, exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            definition, = work.definitions
            request = selected_request(config)
            returned, completed = run_periodic_point_subwork(config=config, representation=representation, sources=sources,
                native_subwork=native_subwork, definition=definition, request=request, root=root,
                native_callable=execute_response_point,
                native_options=dict(center=config.center, frame=config.frame, center_bytes=raw),
                cost_scope='One original full periodic force at an independently accepted checkpoint displacement; '
                    'complete raw return, publication and recovery; no ensemble or kinetic admission')
            result = PeriodicProbeResult(node_id(config) + '.result', request, returned, definition,
                completed.completion, completed.receipt)
            from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import read_response_point
            assessed = read_response_point(config=config, representation=representation, center_bytes=raw,
                original_result=result, native_subwork=native_subwork,
                assessor_source=ObjectIdentity.from_record('source.response-assessor.' +
                    config.original.implementation.code_sources_sha256, config.original.implementation),
                readout_id=node_id(config) + '.assessment')
            values = {node_id(config) + '.product': result, node_id(config) + '.assessment': assessed}
            if (len(context.output_ports) != 2 or {p.output_id for p in context.output_ports} != set(values)
                    or any(p.payload_schema != values[p.output_id].SCHEMA for p in context.output_ports)):
                raise ValueError('response point changes its complete original output')
            return RunnerResult(tuple(TaskOutputPayload(p.output_id, values[p.output_id].canonical_bytes())
                for p in context.output_ports), (ReceiptCheck('complete-original-response-point', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration(*, accelerated=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import prepare_root, validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_inquiry import inquiry_hooks
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_worker_environment
    selected_type = config_type(accelerated)
    ports = (('native-arrays', ArrayDatasetManifest, MAX_CONFIG), ('native-center', PreparationResponseCenter, MAX_CONFIG),
        ('native-checkpoint', ActivePreparationCheckpoint, MAX_CONFIG),
        ('native-frame', PreparationResponseFrame, MAX_CONFIG),
        ('native-model', MolecularRepresentation, MAX_MODEL), ('native-point', PreparationResponsePoint, MAX_CONFIG),
        ('native-prototype', PeriodicProbeSelection, MAX_CONFIG), ('native-provenance', NumericalProducingProvenance, MAX_CONFIG),
        ('native-request', CoupledEvaluationRequest, MAX_CONFIG), ('native-source', PeriodicProbeRawSources, MAX_RAW_SOURCES),
        ('original-preparation-assessment', ActivePreparationPrefixReadout, MAX_CONFIG))
    return RecursiveOperationDeclaration(capability_key=GPU_CAPABILITY if accelerated else CAPABILITY,
        capability_version='1.0.0', implementation_id=('accelerated-' if accelerated else '') + 'checkpoint-response-point-v1',
        kind=CapabilityKind.SIMULATOR, config_record_type=selected_type, stage=ScientificStage.ACQUIRE,
        input_ports=tuple(sorted((*(RecursivePortContract(name, kind.SCHEMA, 'application/json', maximum)
            for name, kind, maximum in ports),
            RecursivePortContract('native-design', PreparationResponseDesign.SCHEMA, 'application/json', MAX_CONFIG, 0, 1),
            RecursivePortContract('native-environment-design', EnvironmentalPreparationResponseDesign.SCHEMA, 'application/json', MAX_CONFIG, 0, 1),
            RecursivePortContract('original-diagnostic-assessment', PreparationResponseAssessment.SCHEMA, 'application/json', MAX_CONFIG, 0, 1),
            RecursivePortContract('original-environment-diagnostic-assessment', EnvironmentalPreparationResponseAssessment.SCHEMA, 'application/json', MAX_CONFIG, 0, 1),
            RecursivePortContract('native-center-bytes', CENTER_SCHEMA,
                'application/octet-stream', MAX_CENTER_BYTES)), key=lambda p: p.port_id)),
        outputs=(OutputTemplate('assessment', PreparationResponsePointReadout.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            'application/json', '.json'), OutputTemplate('product', PeriodicProbeResult.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            'application/json', '.json')),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=GPU_RESOURCE_CEILING if accelerated else BUDGET,
        conformance_check_ids=tuple(sorted(('complete-original-checkpoint-source', 'complete-selected-effect-census',
            'frozen-prediction-before-challenge', 'raw-return-before-assessment', 'original-custody-no-replay'))),
        runner_factory=lambda: PreparationResponseRunner(accelerated=accelerated),
        record_codecs={c.SCHEMA: c for c in (selected_type, PreparationResponsePointReadout, PeriodicProbeResult,
            PreparationResponseAssessment, EnvironmentalPreparationResponseAssessment,
            PreparationResponseDesign, EnvironmentalPreparationResponseDesign,
            *(kind for _, kind, _ in ports))}, storage_codecs=(CENTER_CODEC,),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({p.object_fingerprint for p in operands(c)})),
            scientific_unit_ids=lambda c: (UNIT,), native_effect_slot_ids=slots,
            scientific_root_preparer=prepare_root, scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work, worker_environment_selector=periodic_worker_environment),
        inquiry_hooks=inquiry_hooks())
