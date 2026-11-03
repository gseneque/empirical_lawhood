# SPDX-License-Identifier: MPL-2.0
"""Finite prepared-source contracts over actual prior development controls.

A certificate projects independent implementation checks, not targets or
functional headroom. It preserves every actual prior case and grants neither
freshness, issue, reveal, cross-preparation uncertainty nor scientific qualification.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from dataclasses import dataclass
from typing import ClassVar
from decimal import Decimal

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as prior
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationSource, MatrixPreparationInitialState, MatrixPreparationInitialStateV2, initial_state_types, coupling_recipe_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponsePanel, validate_prepared_panels
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_development_product import MatrixRevisionDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol, branch_census
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import NamedDecimal, ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.evidence_profiles import EvidenceProfileSelection
from empirical_lawhood.planning.metatheory import MetatheoryApplicability, MetatheoryCellDisposition, MetatheoryEvidenceCeiling, MetatheoryMethodSelection
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence, ScientificSourceGateKind, ScientificSourceGateSpec, ScientificSourceInvalidUnitPolicy, ScientificSourceQualificationSpec
from empirical_lawhood.planning.source_pipelines import SourcePipelineProfile, SourcePipelineQualificationReceipt

NAMESPACE = 'matrix-source.prepared-finite-dt'
STANDING = 'ACTUAL_PREPARED_DEV_INDEPENDENT_CONTROLS_FINITE_DT_ONLY_NO_SAMPLING_OR_TRANSPORT_WARRANT'
BLIND, PROSPECTIVE, GATES = prior.BLIND, prior.PROSPECTIVE, prior.GATES
pin, instrument_signature = prior.pin, prior.instrument_signature


@dataclass(frozen=True, slots=True)
class MatrixPreparedSourceBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-finite-dt-bank'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    sources: MatrixConfirmationSources | MatrixReservedTransferSources
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    exposure_support: tuple[tuple[ArtifactIdentity, ArtifactWriteResult | ExperimentFileInputBinding], ...]
    input_commitments: MatrixProgrammePublishedInput

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.sources) not in (MatrixConfirmationSources, MatrixReservedTransferSources) or type(self.assay) is not MatrixPreparedAssayMethod:
            raise TypeError('prepared source needs its actual protected source and complete unchanged assay owners')
        self.sources.__post_init__()
        self.assay.__post_init__()
        required = {artifact for artifact, _ in current_exposure_support(self.audit)}
        if (len(required) != 1 or type(self.exposure_support) is not tuple
                or tuple(value.artifact_id for value, _ in self.exposure_support) != tuple(sorted(value.artifact_id for value in required))
                or {value for value, _ in self.exposure_support} != required):
            raise ValueError('prepared source needs the exact current census publication handle')
        for artifact, custody in self.exposure_support:
            artifact.__post_init__(); custody.__post_init__()
            if type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult, ExperimentFileInputBinding):
                raise TypeError('prepared exposure support substitutes actual FILE/publication custody')
            if type(custody) is ExperimentFileInputBinding:
                if custody.identity != artifact:
                    raise ValueError('prepared exposure FILE changes actual original support bytes')
            elif (custody.logical.logical_artifact_id, custody.logical.payload_schema, custody.logical.media_type,
                    custody.logical.content_sha256, custody.materialization.physical_sha256, custody.materialization.size_bytes) != (
                    artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.sha256, artifact.size_bytes):
                raise ValueError('prepared exposure publication changes actual original support bytes')
        if type(self.input_commitments) is not MatrixProgrammePublishedInput:
            raise TypeError('prepared source requires its actual whole C publication handle')
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)
        groups = self.group_ids
        if (type(self.panels) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in self.panels)
                or tuple(group for group, _ in self.panels) != groups):
            raise ValueError('prepared source drops its complete declared future group/panel roster')
        owners = {}
        roots = {stream.effective_seed for value in self.reservation.allocation.roots for stream in value.streams}
        known = set(self.audit.census.effective_seed_exclusions) | roots
        for _, source in self.source_arms():
            source.__post_init__()
            panels = dict(self.panels)[source.root.root.independent_group_id]
            validate_prepared_panels(source, panels)
            self.protocol(source).__post_init__()
            for panel in panels:
                for stream in panel.streams:
                    owner = (panel.independent_group_id, panel.role, stream.purpose)
                    if owners.setdefault(stream.effective_seed, owner) != owner:
                        raise ValueError('prepared source future streams cross independent group/purpose ownership')
                    if panel.role == 'INDEPENDENT_FUTURE' and stream.effective_seed in known:
                        raise ValueError('prepared source independent future reuses exposed or allocated history noise')

    @property
    def identity(self): return pin(self)
    @property
    def phase(self): return 'E5_CONFIRMATION' if type(self.sources) is MatrixConfirmationSources else 'E6_TRANSFER'
    @property
    def group_ids(self): return tuple(sorted({value.root.root.independent_group_id for _, value in self.source_arms()}))
    @property
    def reservation(self): return self.sources.closure.reservation
    @property
    def specification(self): return self.sources.closure.specification
    @property
    def audit(self): return self.sources.closure.audit
    @property
    def audit_publication(self): return self.sources.closure.audit_publication
    @property
    def provenances(self): return self.sources.closure.provenances
    def source_arms(self): return self.sources.source_arms()
    def protocol(self, source):
        if type(source) is not MatrixPreparationSource:
            raise TypeError('prepared source assay requires its actual separate prepared subject')
        method = self.assay
        templates = ScheduledResponseArrays('templates.prepared-source.' + source.identity.object_fingerprint,
            'TEMPLATES', source.original.source, method.template_artifact, method.template_members,
            (source.original.source,), BLIND, PROSPECTIVE)
        return ScheduledResponseProtocol('protocol.prepared-source.' + source.identity.object_fingerprint,
            source.original, method.criterion, method.mechanical_model, method.actions, method.horizon_steps,
            method.receiver_count, templates, *(getattr(method, name) for name in TOLERANCES), method.origin_rule)


@dataclass(frozen=True, slots=True)
class MatrixPreparedSourceControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-independent-control'
    source: ObjectIdentity
    root_id: str
    group_id: str
    recipe: ObjectIdentity
    initial: MatrixPreparationInitialState | MatrixPreparationInitialStateV2
    provenance: ObjectIdentity
    numerical: ObjectIdentity
    factor_numerical: ObjectIdentity
    instrument_sha256: str
    history: ObjectIdentity
    assessment: ObjectIdentity
    witness: ObjectIdentity
    frames: ObjectIdentity
    causal: ObjectIdentity
    mechanical: ObjectIdentity
    responses: ObjectIdentity
    score: ObjectIdentity
    receipts: tuple[ObjectIdentity, ...]
    numerical_pass: bool
    frame_controls_pass: bool
    frame_controls_violated: bool
    response_controls_pass: bool
    response_control_count: int
    causal_disposition: str
    response_disposition: str

    def __post_init__(self):
        for value in (self.root_id, self.group_id): validate_stable_id(value)
        validate_sha256(self.instrument_sha256)
        if (self.source.object_schema != MatrixPreparationSource.SCHEMA or not coupling_recipe_identity(self.recipe)
                or type(self.initial) not in initial_state_types()
                or self.numerical.object_schema != MatrixParameterNumericalDesign.SCHEMA
                or any(type(value) is not bool for value in (self.numerical_pass, self.frame_controls_pass,
                    self.frame_controls_violated, self.response_controls_pass))
                or type(self.response_control_count) is not int or self.response_control_count < 0
                or self.causal_disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE')
                or self.response_disposition not in ('COMPLETED', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or (self.response_disposition == 'COMPLETED') != (self.response_control_count > 0)
                or self.response_disposition != 'COMPLETED' and self.response_controls_pass
                or self.frame_controls_violated and self.frame_controls_pass):
            raise ValueError('prepared control erases an actual adverse/nonuse case or invents an exercised instrument')
        self.initial.__post_init__()
        require_sorted_unique_ids(self.receipts, attribute='object_id', field_name='actual prepared control receipt census')
        if not self.receipts:
            raise ValueError('prepared control requires actual producing receipts')
        for value in (self.source, self.recipe, self.provenance, self.numerical, self.factor_numerical,
                self.history, self.assessment, self.witness, self.frames, self.causal, self.mechanical,
                self.responses, self.score, *self.receipts):
            if type(value) is not ObjectIdentity: raise TypeError('prepared controls require exact original typed pins')
            value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixPreparedInstrumentCertificate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-instrument-certificate'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    locator: MatrixRevisionDevelopmentProduct | MatrixSelectedDevelopmentProduct
    native_training_locator: prior.MatrixFiniteDtTrainingLocator
    native_training_request: ObjectIdentity
    native_training_acquisition: ObjectIdentity
    original_future_reservation: ObjectIdentity
    development_programme: ObjectIdentity
    input_commitments: ObjectIdentity
    development_group_ids: tuple[str, ...]
    controls: tuple[MatrixPreparedSourceControl, ...]
    excluded_effective_seeds: tuple[int, ...]
    reserved_future_effective_seeds: tuple[int, ...]
    original_future_panels: tuple[tuple[str, ObjectIdentity], ...]
    future_bank: ObjectIdentity
    future_group_ids: tuple[str, ...]
    cutoff: InformationCutoff

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.locator) not in (MatrixRevisionDevelopmentProduct, MatrixSelectedDevelopmentProduct)
                or type(self.native_training_locator) is not prior.MatrixFiniteDtTrainingLocator
                or type(self.cutoff) is not InformationCutoff or self.future_bank.object_schema != MatrixPreparedSourceBank.SCHEMA
                or self.native_training_request.object_schema != train.NativeTrainingAcquisitionRequest.SCHEMA
                or self.native_training_acquisition.object_schema != train.NativeTrainingAcquisitionSeal.SCHEMA
                or self.original_future_reservation.object_schema != scheduled.ScheduledReservation.SCHEMA
                or (self.input_commitments.object_schema, self.input_commitments.object_version) !=
                    (MatrixProgrammeInputCommitments.SCHEMA, MatrixProgrammeInputCommitments.VERSION)):
            raise TypeError('prepared certificate needs exact prior development/TRAIN locators and real future source scope')
        self.locator.__post_init__(); self.native_training_locator.__post_init__(); self.cutoff.__post_init__()
        for name in ('development_group_ids', 'future_group_ids'):
            require_sorted_unique_strings(getattr(self, name), field_name=name, allow_empty=False)
        if set(self.development_group_ids).intersection(self.future_group_ids):
            raise ValueError('prepared future source reuses an actual development group')
        if (type(self.controls) is not tuple or not self.controls
                or any(type(row) is not MatrixPreparedSourceControl for row in self.controls)
                or tuple(row.source.object_id for row in self.controls) != tuple(sorted({row.source.object_id for row in self.controls}))
                or {row.group_id for row in self.controls} != set(self.development_group_ids)):
            raise ValueError('prepared certificate thins or aliases actual complete development control cases')
        for row in self.controls: row.__post_init__()
        for name in ('excluded_effective_seeds', 'reserved_future_effective_seeds'):
            values = getattr(self, name)
            if type(values) is not tuple or not values or values != tuple(sorted(set(values))) or any(type(v) is not int or not 0 <= v < 2**128 for v in values):
                raise ValueError('prepared certificate changes its actual consumed or reserved effective-key census')
        roles = ('CALIBRATION', 'EVALUATION', 'TRANSFER_NEARBY', 'TRANSFER_SHIFTED')
        if (type(self.original_future_panels) is not tuple or tuple(role for role, _ in self.original_future_panels) != roles
                or any(type(value) is not ObjectIdentity or value.object_schema != 'empirical-lawhood/matrix-scheduled-history/response-selection' for _, value in self.original_future_panels)):
            raise ValueError('prepared certificate drops actual pre-TRAIN future-panel commitments')

    @property
    def identity(self): return pin(self)
    @property
    def original_evidence_links(self):
        values = {self.locator.receipt, self.locator.execution_plan, self.native_training_locator.packet,
            self.native_training_locator.execution_plan, self.native_training_request, self.native_training_acquisition,
            self.development_programme, self.input_commitments, *(value for _, value in self.original_future_panels)}
        for row in self.controls:
            values.update((row.source, row.history, row.assessment, row.witness, row.frames, row.causal,
                row.mechanical, row.responses, row.score, *row.receipts))
        return tuple(sorted(values, key=lambda value: value.object_id))


def require_original_future_commitments(bank, request, future_selections):
    """Pure selected-sequence exclusion/E6 consumption; API authenticates inputs."""
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import physical_key
    if type(bank) is not MatrixPreparedSourceBank or type(request) is not train.NativeTrainingAcquisitionRequest:
        raise TypeError('prepared commitment check needs actual bank and original TRAIN request')
    bank.__post_init__(); request.__post_init__()
    selected = tuple(future_selections); phases = dict(selected)
    if len(selected) != 4 or tuple(sorted(phases)) != ('CALIBRATION', 'EVALUATION', 'TRANSFER_NEARBY', 'TRANSFER_SHIFTED'):
        raise ValueError('prepared source requires all four actual authenticated pre-TRAIN selections')
    future = request.future_manifest
    reserve = future.reservation
    if bank.phase == 'E6_TRANSFER':
        closure = bank.sources.closure
        if (bank.reservation != reserve or bank.specification != future.native_specification
                or bank.audit != future.audit or bank.audit_publication != future.audit_publication):
            raise ValueError('prepared transfer substitutes its original pre-TRAIN reservation/specification/audit')
        protocols, panels = {}, {}
        for role in ('TRANSFER_NEARBY', 'TRANSFER_SHIFTED'):
            selection = phases[role]
            selection.validate_allocation(reserve.allocation)
            for protocol in selection.protocols:
                root_id = protocol.public_source.root.root_id
                if root_id in protocols: raise ValueError('prepared transfer repeats a reserved original root')
                protocols[root_id] = protocol
            for group, values in selection.panels:
                if group in panels: raise ValueError('prepared transfer repeats an independent original group')
                panels[group] = tuple(sorted((v.panel_id, v.role, v.independent_group_id, v.streams) for v in values))
        if {v.root_id for v in closure.descriptors} != set(protocols) or set(bank.group_ids) != set(panels):
            raise ValueError('prepared transfer thins the exact original roots or future panels')
        index = closure.source_index()
        for descriptor in closure.descriptors:
            source, protocol = closure.original(descriptor, index=index), protocols[descriptor.root_id]
            if (ScheduledPublicSource.from_source(source) != protocol.public_source
                    or MatrixPreparedAssayMethod.from_protocol(bank.assay.record_id, protocol) != bank.assay):
                raise ValueError('prepared transfer changes an original source/provenance or immutable assay')
        if any(tuple(sorted((v.panel_id, v.role, v.independent_group_id, v.streams) for v in values)) != panels[group]
                for group, values in bank.panels):
            raise ValueError('prepared transfer substitutes actual pre-TRAIN panel identities or common/independent future streams')
    else:
        withheld = {value.coordinate for value in reserve.allocation.roots if value.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
        physics = {physical_key(v) for v in reserve.allocation.coordinates if coordinate_identity(v) in withheld}
        groups = {row.root.independent_group_id for manifest in (request.train_manifest, future) for row in manifest.reservation.allocation.roots}
        seeds = {stream.effective_seed for manifest in (request.train_manifest, future)
            for row in manifest.reservation.allocation.roots for stream in row.streams}
        seeds.update(stream.effective_seed for panel in request.panels for stream in panel.streams)
        seeds.update(stream.effective_seed for selection in phases.values() for _, values in selection.panels
            for panel in values for stream in panel.streams)
        if groups.intersection(bank.group_ids) or any(physical_key(source.coordinate) in physics for _, source in bank.source_arms()):
            raise ValueError('prepared confirmation consumes original groups or withheld E6 physics')
        current = {stream.effective_seed for _, source in bank.source_arms() for stream in source.root.streams}
        current.update(stream.effective_seed for _, values in bank.panels for panel in values for stream in panel.streams)
        if current.intersection(seeds):
            raise ValueError('prepared confirmation consumes original TRAIN or pre-TRAIN reserved effective streams')


@dataclass(frozen=True, slots=True)
class MatrixPreparedSourceScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-finite-dt-scope'
    record_id: str
    bank: ObjectIdentity
    source_identity: ObjectIdentity
    preparation: ObjectIdentity
    assay: ObjectIdentity
    numerical: ObjectIdentity
    original_future_reservation: ObjectIdentity
    certificate: ObjectIdentity
    cutoff: InformationCutoff
    group_ids: tuple[str, ...]
    profile: SourcePipelineProfile
    pipeline_receipt: SourcePipelineQualificationReceipt
    evidence_profile: EvidenceProfileSelection
    publication: ObjectIdentity
    recovery: ObjectIdentity
    resource_budget: ResourceBudget

    def __post_init__(self):
        validate_stable_id(self.record_id)
        require_sorted_unique_strings(self.group_ids, field_name='complete prepared future groups', allow_empty=False)
        if (self.bank.object_schema != MatrixPreparedSourceBank.SCHEMA or self.certificate.object_schema != MatrixPreparedInstrumentCertificate.SCHEMA
                or self.source_identity.object_schema != 'empirical-lawhood/matrix-experimental-programme/protected-source-closure'
                or self.preparation.object_schema not in (MatrixConfirmationSources.SCHEMA, MatrixReservedTransferSources.SCHEMA)
                or self.assay.object_schema != MatrixPreparedAssayMethod.SCHEMA or self.numerical.object_schema != MatrixParameterNumericalDesign.SCHEMA
                or type(self.cutoff) is not InformationCutoff or type(self.profile) is not SourcePipelineProfile
                or type(self.pipeline_receipt) is not SourcePipelineQualificationReceipt or type(self.evidence_profile) is not EvidenceProfileSelection
                or type(self.resource_budget) is not ResourceBudget):
            raise TypeError('prepared source changes its exact source, preparation, assay or pipeline owners')
        for value in (self.cutoff, self.profile, self.pipeline_receipt, self.evidence_profile, self.resource_budget): value.__post_init__()
        if (self.profile.outcome_access is not BLIND or self.profile.visibility_ceiling is not PROSPECTIVE
                or self.pipeline_receipt.profile != pin(self.profile, 'profile_id')
                or self.pipeline_receipt.outcome_access is not BLIND or self.pipeline_receipt.visibility_ceiling is not PROSPECTIVE
                or self.profile.observation_operator != self.assay or self.profile.causal_cutoff != pin(self.cutoff, 'cutoff_id')
                or self.numerical.object_id not in self.profile.numerical_view_ids):
            raise ValueError('prepared source changes actual source/assay/cutoff/access or broadens its claim')
    @property
    def identity(self): return pin(self)
    @property
    def operands(self):
        return tuple(sorted((self.identity, self.bank, self.source_identity, self.preparation, self.assay,
            self.numerical, self.original_future_reservation, self.certificate, pin(self.cutoff, 'cutoff_id')), key=lambda v: v.object_id))


@dataclass(frozen=True, slots=True)
class MatrixPreparedSourceGateConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-finite-dt-gate-config'
    config_id: str
    scope: ObjectIdentity
    phase: str
    gate_kind: ScientificSourceGateKind
    group_ids: tuple[str, ...]
    resource_budget: ResourceBudget
    def __post_init__(self):
        validate_stable_id(self.config_id)
        require_sorted_unique_strings(self.group_ids, field_name='complete prepared source gate groups', allow_empty=False)
        if (self.scope.object_schema != MatrixPreparedSourceScope.SCHEMA or self.phase not in ('E5_CONFIRMATION', 'E6_TRANSFER')
                or self.gate_kind not in GATES or type(self.resource_budget) is not ResourceBudget):
            raise ValueError('prepared source gate changes its exact complete declared scope')
    @property
    def identity(self): return pin(self, 'config_id')


def phase_for_scope(scope):
    return 'E5_CONFIRMATION' if scope.preparation.object_schema == MatrixConfirmationSources.SCHEMA else 'E6_TRANSFER'


def gate_configs(scope):
    return tuple(MatrixPreparedSourceGateConfig('config.' + scope.record_id + '.' + kind.value.lower(),
        scope.identity, phase_for_scope(scope), kind, scope.group_ids, scope.resource_budget) for kind in GATES)


def qualification_specification(scope):
    from .matrix_prepared_source_bindings import gate_declaration
    configs = {value.gate_kind: value for value in gate_configs(scope)}
    gates = []
    for kind in ScientificSourceGateKind:
        required = kind in GATES
        method = (MetatheoryMethodSelection('method.' + scope.record_id + '.' + kind.value.lower(),
            NAMESPACE + '.' + phase_for_scope(scope).lower() + '.' + kind.value.lower(), '1.0.0', configs[kind].identity,
            gate_declaration(kind, phase_for_scope(scope)).manifest().implementation_sha256) if required else None)
        gates.append(ScientificSourceGateSpec('gate.' + scope.record_id + '.' + kind.value.lower(), kind,
            MetatheoryApplicability.REQUIRED if required else MetatheoryApplicability.NOT_APPLICABLE, method,
            scope.operands if required else (), 'unit.actual-whole-independent-matched-group',
            'operation.actual-prepared-finite-dt-instrument', ('falsifier.actual-prepared-independent-controls',) if required else (),
            () if required else ('NO_STATIONARITY_OR_RECURRENCE_CLAIM',)))
    return ScientificSourceQualificationSpec('specification.' + scope.record_id, pin(scope.profile, 'profile_id'),
        pin(scope.pipeline_receipt, 'receipt_id'), pin(scope.evidence_profile, 'selection_id'), scope.source_identity,
        scope.pipeline_receipt.output_artifact, tuple(sorted(gates, key=lambda v: v.gate_id)), scope.group_ids,
        len(scope.group_ids), ScientificSourceInvalidUnitPolicy.UNEVALUABLE, scope.preparation, scope.assay,
        scope.numerical, pin(scope.cutoff, 'cutoff_id'), EvidenceCeiling.MEASUREMENT,
        MetatheoryEvidenceCeiling.CONTRACT_CONFORMANCE, BLIND, PROSPECTIVE)


def prepared_instrument_controls_supported(bank, certificate):
    """Replay independent prepared implementation checks, never outcome support.

    Actual API custody reconstructs the complete DEV witness before this pure
    projection. A missing recipe, unexercised initial state, adverse control or
    absent complete paired branch census retains UNEVALUABLE. Per-acquisition
    numerical checks, point nonuse and transport/uncertainty limits stay separate.
    """
    if type(bank) is not MatrixPreparedSourceBank or type(certificate) is not MatrixPreparedInstrumentCertificate:
        raise TypeError('prepared controls require their exact bank and original complete certificate')
    bank.__post_init__(); certificate.__post_init__()
    needed = {source.recipe.identity for _, source in bank.source_arms()}
    controls = tuple(row for row in certificate.controls if row.recipe in needed)
    signatures = {instrument_signature(bank.protocol(source)) for _, source in bank.source_arms()}
    numerical = {scheduled.identity(source.numerical_design) for _, source in bank.source_arms()}
    factor = {scheduled.identity(source.original.policy.factor_numerical_design) for _, source in bank.source_arms()}
    provenances = {source.provenance.identity for _, source in bank.source_arms()}
    if any(row.instrument_sha256 not in signatures or row.numerical not in numerical
            or row.factor_numerical not in factor or row.provenance not in provenances for row in controls):
        raise ValueError('prepared source changes exercised assay, numerical implementation or timestep')
    expected_counts = {}
    for _, source in bank.source_arms():
        count = len(branch_census(bank.protocol(source), dict(bank.panels)[source.root.root.independent_group_id]))
        if expected_counts.setdefault(source.recipe.identity, count) != count:
            raise ValueError('prepared source changes branch geometry across the same fixed recipe')
    exercised = {row.recipe for row in controls if row.response_disposition == 'COMPLETED'
        and row.response_control_count == expected_counts[row.recipe]}
    def initial_scope(value):
        artifact = value.array_artifact
        return artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes, value.members, value.alpha_tilde
    exercised_starts = {(row.recipe, initial_scope(row.initial)) for row in controls
        if row.response_disposition == 'COMPLETED' and row.response_control_count == expected_counts[row.recipe]}
    starts_supported = all((source.recipe.identity, initial_scope(source.initial)) in exercised_starts for _, source in bank.source_arms())
    return (needed <= exercised and starts_supported and all(row.numerical_pass and not row.frame_controls_violated
        and (row.causal_disposition != 'AVAILABLE' or row.frame_controls_pass)
        and (row.response_disposition != 'COMPLETED' or row.response_controls_pass) for row in controls))



def prepared_source_cutoffs(sources, cutoff):
    """Project only the declared Matrix zero-origin physical-time coordinates.

    Parameter-coordinate clocks use physical_time(tick)=primary_dt*tick. This
    exact domain mapping permits different original regime clock IDs with the
    same physical time unit; it is not a general clock transport or freshness
    warrant. The supplied anchor remains its unchanged canonical record.
    """
    if (type(sources) is not tuple or not sources or any(type(value) is not MatrixPreparationSource for value in sources)
            or type(cutoff) is not InformationCutoff):
        raise TypeError('prepared cutoffs require actual source coordinates and the exact original anchor')
    cutoff.__post_init__()
    for source in sources:
        source.__post_init__()
        source.coordinate.__post_init__()
    clocks = {source.coordinate.clock_id for source in sources}
    if cutoff.clock_id not in clocks:
        raise ValueError('prepared source cutoff clock is outside its actual selected bank')
    if not cutoff.phase.precedes_or_equals(CausalPhase.PRE_ACTION):
        raise ValueError('prepared source cutoff is after its pre-action phase')
    units = {source.coordinate.primary_view.time_unit for source in sources}
    if len(units) != 1 or any(source.coordinate.physical_time(0) != Decimal(0) for source in sources):
        raise ValueError('prepared source clocks lack the same declared zero-origin physical time unit')
    if cutoff.coordinate is not None and (cutoff.coordinate < Decimal(0) or any(
            cutoff.coordinate > source.coordinate.physical_time(source.total_ticks) for source in sources)):
        raise ValueError('prepared source physical cutoff is outside an original preparation handoff')
    return tuple(sorted((cutoff if clock == cutoff.clock_id else InformationCutoff(
        cutoff.cutoff_id + '.for.' + clock, clock, cutoff.phase, cutoff.coordinate, cutoff.includes_coordinate)
        for clock in clocks), key=lambda value: value.cutoff_id))


def validate_gate_operands(config, scope, records):
    if (type(config) is not MatrixPreparedSourceGateConfig or type(scope) is not MatrixPreparedSourceScope
            or set(records) != {'scope', 'bank', 'source', 'preparation', 'assay', 'numerical', 'original-reservation', 'cutoff', 'certificate'}):
        raise TypeError('prepared source requires its exact complete configured scientific operands')
    config.__post_init__(); scope.__post_init__()
    bank, certificate = records['bank'], records['certificate']
    if type(bank) is not MatrixPreparedSourceBank or type(certificate) is not MatrixPreparedInstrumentCertificate:
        raise TypeError('prepared source substitutes its actual future bank or DEV certificate')
    bank.__post_init__(); certificate.__post_init__()
    closure = bank.sources.closure
    if (records['scope'] != scope or records['cutoff'] != scope.cutoff or config not in gate_configs(scope)
            or config.scope != scope.identity or bank.identity != scope.bank or bank.group_ids != scope.group_ids
            or records['source'] != closure or records['preparation'] != bank.sources or records['assay'] != bank.assay
            or records['numerical'] != bank.specification.selection.numerical_design
            or scheduled.identity(records['original-reservation']) != scope.original_future_reservation
            or closure.identity != scope.source_identity or bank.sources.identity != scope.preparation
            or bank.assay.identity != scope.assay or closure.numerical_scope != scope.numerical
            or certificate.identity != scope.certificate or certificate.future_bank != scope.bank
            or certificate.future_group_ids != scope.group_ids or certificate.cutoff != scope.cutoff
            or certificate.original_future_reservation != scope.original_future_reservation
            or certificate.input_commitments != bank.input_commitments.record):
        raise ValueError('prepared source substitutes its exact closure, recipe, assay, prior custody or whole-group denominator')
    if set(certificate.development_group_ids).intersection(bank.group_ids):
        raise ValueError('prepared source reuses an actually inspected DEV group')
    forbidden = set(certificate.excluded_effective_seeds)
    current = {stream.effective_seed for _, source in bank.source_arms() for stream in source.root.streams}
    current.update(stream.effective_seed for _, panels in bank.panels for panel in panels for stream in panel.streams)
    if current.intersection(forbidden) or bank.phase != 'E6_TRANSFER' and current.intersection(certificate.reserved_future_effective_seeds):
        raise ValueError('prepared source reuses actual consumed or pre-TRAIN reserved noise')
    prepared_source_cutoffs(tuple(source for _, source in bank.source_arms()), scope.cutoff)
    instrument_supported = prepared_instrument_controls_supported(bank, certificate)
    supported = config.gate_kind is not ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY or instrument_supported
    spec = qualification_specification(scope)
    gate, = (value for value in spec.gates if value.gate_kind is config.gate_kind)
    return ScientificSourceGateEvidence('evidence.' + config.config_id, pin(spec, 'spec_id'), pin(gate, 'gate_id'),
        scope.operands, gate.evaluator, scope.group_ids, scope.group_ids if supported else (),
        () if supported else scope.group_ids, (NamedDecimal('assigned-future-groups', Decimal(len(scope.group_ids)), 'whole-independent-groups'),),
        scope.publication, scope.recovery, (certificate.identity,),
        MetatheoryCellDisposition.SUPPORTED if supported else MetatheoryCellDisposition.UNEVALUABLE,
        () if supported else ('ACTUAL_PREPARED_RECIPE_OR_PAIRED_INSTRUMENT_CONTROLS_NOT_ESTABLISHED',))
