# SPDX-License-Identifier: MPL-2.0
"""A distinct acquisition component beneath one unchanged global programme.

The local question is complete sealed data acquisition. It does not replace
the global response-law question, infer population coverage or qualify a law.
Original scientific records remain literal immutable inputs of this component.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experiments import ControlKind, ControlSpec, PrecisionGoal
from empirical_lawhood.kernel.obligations import FalsifierKind, FalsifierSpec, ObligationStatus
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, StudyDraft

from .commitment import ScheduledCommitment
from .compact_records import ScheduledCompactBank, compact_identity
from .programme_records import MODES, ScheduledProgramme, ScheduledProgrammeWave, validate_programme_bank
from .programme_parent import ScheduledProgrammeGlobalParentBinding
from .programme_confirmation import ScheduledProgrammeConfirmationParentBinding
from .programme_qualified_parent import ScheduledProgrammeQualifiedParentDeclaration, validate_qualified_parent_declaration

NAMESPACE = 'matrix-scheduled-programme-acquisition'
MAXIMUM_ACQUISITION_BYTES = 16*1024**2
BLIND, SEALED, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAcquisitionScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/acquisition-scope'
    acquisition_id: str
    programme: ScheduledProgramme
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    global_root: StudyDraft
    qualified_parent: ScheduledProgrammeQualifiedParentDeclaration | None = None

    def __post_init__(self):
        validate_stable_id(self.acquisition_id)
        if type(self.programme) is not ScheduledProgramme:
            raise ValueError('acquisition scope requires its closed frozen whole-programme declaration')
        if ((self.programme.mode == 'E4_CONFIRMATION') != (self.qualified_parent is not None)
                or self.qualified_parent is not None and type(self.qualified_parent) is not ScheduledProgrammeQualifiedParentDeclaration):
            raise ValueError('confirmation acquisition requires its exact original qualified-parent declaration; other modes cannot alias it')
        root = self.global_root
        development = self.programme.mode == 'E4_DEVELOPMENT'
        if (type(self.programme) is not ScheduledProgramme
                or self.bank != self.programme.bank or self.wave not in self.programme.waves
                or self.acquisition_id != 'acquisition.'+self.wave.wave_id
                or type(root) is not StudyDraft or root.system is None or root.experiment is None or root.campaign is None
                or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
                or root.development_unit_ids != (self.programme.group_ids if development else ())
                or root.evaluation_unit_ids != (() if development else self.programme.group_ids)
                or root.experiment.information_cutoffs != tuple(case.information_cutoff for case in self.programme.cases)
                or root.unresolved_decisions or not root.design_inputs
                or len(self.canonical_bytes()) > MAXIMUM_ACQUISITION_BYTES):
            raise ValueError('acquisition scope changes its exact original full programme or immutable global scientific root')
        required = {self.programme.identity, self.bank, self.programme.criterion,
            self.programme.reservation, self.programme.allocation, self.programme.specification,
            self.programme.forecast_design, self.programme.response_selection, *self.programme.source_census}
        if not required <= {value.object_identity for value in root.design_inputs}:
            raise ValueError('acquisition scope omits original full scientific programme/criterion/source identity pins')
        if len({value.information_cutoff for value in root.design_inputs}) != 1:
            raise ValueError('acquisition scope changes the exact common original design-decision cutoff')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.acquisition_id, self)

    @property
    def global_root_identity(self):
        return ObjectIdentity.from_record(self.global_root.draft_id, self.global_root)

    @property
    def global_experiment_identity(self):
        return ObjectIdentity.from_record(self.global_root.experiment.experiment_id, self.global_root.experiment)


def acquisition_root(scope, bank):
    """Build a new non-promotable acquisition root, keeping old records exact."""
    if type(scope) is not ScheduledProgrammeAcquisitionScope or type(bank) is not ScheduledCompactBank:
        raise ValueError('acquisition root requires its explicit typed frozen scope and complete bank')
    validate_programme_bank(scope.programme, bank)
    if compact_identity(bank) != scope.bank:
        raise ValueError('acquisition root substitutes its complete original bank')
    if scope.qualified_parent is not None:
        validate_qualified_parent_declaration(bank, scope.qualified_parent)
    cases = tuple(case for case in scope.programme.cases if case.root_id in scope.wave.root_ids)
    coordinates = {ObjectIdentity.from_record(value.coordinate_id, value): value for value in bank.reservation.allocation.coordinates}
    views = tuple(sorted({view.view_id for case in cases
        for view in (coordinates[case.coordinate].primary_view, coordinates[case.coordinate].fine_view)}))
    return _local_root(scope, views)


def _local_root(scope, views):
    """Pure local declaration; its callers authenticate the original views."""
    original, programme, wave = scope.global_root, scope.programme, scope.wave
    prefix = scope.acquisition_id
    development = programme.mode == 'E4_DEVELOPMENT'
    access = OutcomeAccess.DEVELOPMENT_VISIBLE if development else SEALED
    visibility = VisibilityCeiling.DEVELOPMENT_ONLY if development else PROSPECTIVE
    experiment = original.experiment
    cases = tuple(case for case in programme.cases if case.root_id in wave.root_ids)
    if not views or not set(views) <= {view.view_id for view in original.system.numerical_views}:
        raise ValueError('acquisition root changes original primary/fine numerical views')
    old = experiment.obligations
    na, required = ObligationStatus.NOT_APPLICABLE, ObligationStatus.REQUIRED
    claim = ClaimSpec('claim.'+prefix+'.sealed-data', experiment.world_id, experiment.relation.relation_id,
        'Retain complete sealed acquisition data and dispositions for every selected whole matched group and all nine coordinate cases.',
        'Complete selected-case prefix, response, numerical and fifteen-endpoint acquisition ledger; no population or response-law inference.',
        experiment.independent_unit_id, None, EvidenceCeiling.NON_PROMOTABLE, access, visibility,
        'This acquisition component cannot promote evidence or qualify the global law. Global qualification belongs only to the complete programme tail.',
        tuple(sorted(set(value for claim in experiment.claims for value in claim.assumption_ids))))
    obligations = replace(old, obligations_id='obligations.'+prefix+'.data',
        support=replace(old.support, support_id='support.'+prefix+'.complete-case-data',
            information_cutoff_id=cases[0].information_cutoff.cutoff_id, physical_unit_count=0,
            status=required, evidence_link_ids=()),
        validity=replace(old.validity, validity_id='validity.'+prefix+'.original-acquisition-domain',
            status=required, evidence_link_ids=()),
        uncertainty=replace(old.uncertainty, uncertainty_id='uncertainty.'+prefix+'.no-population-inference',
            method_key='acquisition.no-population-inference', status=na, evidence_link_ids=(),
            limitation_codes=('acquisition-only', 'global-population-qualification-deferred')),
        falsifiers=(FalsifierSpec('falsifier.'+prefix+'.retain-numerical-verdicts', FalsifierKind.STRUCTURAL_CONVERGENCE,
            NAMESPACE+'.full-numerical', 'Retain every original primary/fine numerical verdict and all adverse or unevaluable outcomes.',
            'No case, numerical failure, nonuse or unknown endpoint may disappear from the complete selected acquisition ledger.', required),),
        closure=replace(old.closure, closure_id='closure.'+prefix+'.no-global-law-inference', status=na, evidence_link_ids=()),
        structural_convergence=replace(old.structural_convergence, convergence_id='convergence.'+prefix+'.retain-original-numerical-checks',
            numerical_view_ids=views, status=required, evidence_link_ids=()), discrepancy=None)
    local_experiment = replace(experiment, experiment_id='experiment.'+prefix, claims=(claim,),
        assignment=replace(experiment.assignment, assignment_id='assignment.'+prefix,
            mechanism='Acquire the exact frozen whole-group wave; every group keeps all nine coordinate cases, original streams and original protocols.'),
        controls=(ControlSpec('control.'+prefix+'.fixed-zero-fit-oracle', ControlKind.BASELINE_COMPARATOR,
            NAMESPACE+'.physical-forecast', experiment.measurement_quantity_ids,
            'Retain the independently declared ZERO_FIT_BASELINE_ORACLE and every actual error/nonuse disposition; it cannot substitute for observed future response.'),),
        precision_goals=(PrecisionGoal('precision.'+prefix+'.complete-case-endpoint-census',
            'metric.'+prefix+'.missing-case-endpoint-count', Decimal(1), '1', len(wave.group_ids),
            'Stop only with fewer than one missing selected case or endpoint: every case retains all fifteen endpoint positions and explicit adverse/nonuse dispositions.'),),
        information_cutoffs=tuple(case.information_cutoff for case in cases), obligations=obligations,
        reveal_barrier=replace(experiment.reveal_barrier, barrier_id='barrier.'+prefix+'.retain-sealed-data',
            evaluation_cohort_id='cohort.'+prefix,
            evaluation_manifest_sha256=sha256(canonical_json_bytes(tuple(case.source for case in cases))).hexdigest(),
            sealed_outcome_artifact_ids=('scientific.'+wave.wave_id+'.collect.product',)),
        predecessor_experiment_ids=tuple(sorted({*experiment.predecessor_experiment_ids, experiment.experiment_id})))
    old_claims = {ObjectIdentity.from_record(value.claim_id, value) for value in experiment.claims}
    campaign = replace(original.campaign, campaign_id='campaign.'+prefix, target_claim_ids=(claim.claim_id,),
        nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(local_experiment.experiment_id, local_experiment))
            if node.object_identity == scope.global_experiment_identity else
            replace(node, object_identity=ObjectIdentity.from_record(claim.claim_id, claim))
            if node.object_identity in old_claims else node for node in original.campaign.nodes))
    cutoff, operator = original.design_inputs[0].information_cutoff, original.design_inputs[0].operator_id
    pins = (scope.identity, scope.global_root_identity, scope.global_experiment_identity)
    additions = tuple(DesignInputRecord('design.'+prefix+'.original.'+str(index), pin, pin.object_fingerprint,
        cutoff, DesignInputRole.READINESS_METADATA, BLIND, PROSPECTIVE, operator) for index, pin in enumerate(pins))
    designs = tuple(sorted((*original.design_inputs, *additions), key=lambda value: value.input_id))
    return replace(original, draft_id='draft.'+prefix,
        question='Acquire complete '+('development' if development else 'sealed')+' data for '+str(len(wave.group_ids))+' frozen matched groups and all '+str(len(cases))+' coordinate cases under '+programme.programme_id+'.',
        experiment=local_experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(original.design_origin, declared_input_ids=tuple(value.input_id for value in designs)),
        development_unit_ids=wave.group_ids if development else (),
        evaluation_unit_ids=() if development else wave.group_ids, source_materializations=())


def _validate_local_root(scope, root, expected, *, execution_plan=None, protocol=None, revision_scope=None):
    """Keep scientific fields exact through an authenticated compiler projection.

    The optional pair belongs to the caller's actual authenticated issued
    package. Without both records, precompile callers retain the original
    strict template and capability-selection comparison.
    """
    if type(root) is not StudyDraft or root.campaign is None or root.system is None:
        raise ValueError('acquisition root requires its actual local scientific declaration')
    if (execution_plan is None) != (protocol is None):
        raise ValueError('acquisition compiler projection requires both actual plan and protocol')
    if execution_plan is not None:
        from empirical_lawhood.planning.study_authoring import CapabilitySelection
        from empirical_lawhood.runtime.plans import ProtocolTemplate
        from .programme_acquisition_custody import validate_acquisition_operation_census
        collector = 'collect-development' if scope.programme.mode == 'E4_DEVELOPMENT' else 'collect'
        validate_acquisition_operation_census(scope.programme, scope.wave, collector, execution_plan, revision_scope=revision_scope)
        selections = tuple(sorted({CapabilitySelection(task.capability.capability_key,
            task.capability.capability_version, task.capability_implementation_sha256)
            for task in execution_plan.tasks}, key=lambda value: value.selection_id))
        if (type(protocol) is not ProtocolTemplate or root.dag_template_key != protocol.template_id
                or root.capability_selections != selections
                or tuple(step.step_id for step in protocol.steps) != tuple(task.task_id for task in execution_plan.tasks)
                or any((step.capability_key, step.capability_version, step.config)
                    != (task.capability.capability_key, task.capability.capability_version, task.capability.config)
                    for step, task in zip(protocol.steps, execution_plan.tasks, strict=True))):
            raise ValueError('acquisition root changes its actual compiled template or complete capability selection')
        root = replace(root, dag_template_key=expected.dag_template_key,
            capability_selections=expected.capability_selections)
    policy = ObjectIdentity.from_record(root.system.authority_policy.policy_id, root.system.authority_policy)
    if root.campaign.authority_policy not in (expected.campaign.authority_policy, policy):
        raise ValueError('acquisition root substitutes its actual system authority policy')
    normalized = replace(root, source_materializations=(), campaign=replace(root.campaign,
        budget=expected.campaign.budget, authority_policy=expected.campaign.authority_policy))
    if (normalized != expected
            or root.experiment == scope.global_root.experiment):
        raise ValueError('acquisition root changes local data obligations or aliases the original global scientific question')


def validate_acquisition_root(scope, root, bank, *, execution_plan=None, protocol=None, revision_scope=None):
    """Compare all immutable scientific fields, allowing actual source custody."""
    _validate_local_root(scope, root, acquisition_root(scope, bank), execution_plan=execution_plan, protocol=protocol, revision_scope=revision_scope)


def decode_acquisition_scope(raw):
    return decode_canonical_bytes(raw, ScheduledProgrammeAcquisitionScope, maximum_bytes=MAXIMUM_ACQUISITION_BYTES)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAcquisitionAdmissionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/acquisition-admission-config'
    config_id: str
    scope: ScheduledProgrammeAcquisitionScope
    global_parent_binding: ScheduledProgrammeGlobalParentBinding | ScheduledProgrammeConfirmationParentBinding

    def __post_init__(self):
        if (type(self.scope) is not ScheduledProgrammeAcquisitionScope
                or type(self.global_parent_binding) is not (ScheduledProgrammeConfirmationParentBinding
                    if self.scope.programme.mode == 'E4_CONFIRMATION' else ScheduledProgrammeGlobalParentBinding)
                or self.config_id != 'config.'+self.scope.wave.wave_id+'.acquisition-open'
                or self.global_parent_binding.parent.programme != self.scope.programme.identity
                or self.global_parent_binding.parent.bank != self.scope.bank
                or len(self.canonical_bytes()) > MAXIMUM_ACQUISITION_BYTES):
            raise ValueError('acquisition admission changes its explicit new actual configuration or original global parent')
        if (self.scope.programme.mode == 'E4_CONFIRMATION'
                and self.global_parent_binding.configuration.qualified_parent != self.scope.qualified_parent):
            raise ValueError('confirmation acquisition substitutes its genuine original qualified-parent declaration')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)

    @property
    def programme(self):
        return self.scope.programme

    @property
    def bank(self):
        return self.scope.bank

    @property
    def wave(self):
        return self.scope.wave


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAcquisitionAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/acquisition-admission'
    admission_id: str
    configuration: ObjectIdentity
    scope: ScheduledProgrammeAcquisitionScope
    global_parent_binding: ScheduledProgrammeGlobalParentBinding | ScheduledProgrammeConfirmationParentBinding
    semantic_commitment: ScheduledCommitment

    def __post_init__(self):
        config = ScheduledProgrammeAcquisitionAdmissionConfig('config.'+self.scope.wave.wave_id+'.acquisition-open',
            self.scope, self.global_parent_binding)
        if (self.admission_id != 'admission.acquisition.'+self.scope.wave.wave_id
                or self.configuration != config.identity or type(self.semantic_commitment) is not ScheduledCommitment
                or self.semantic_commitment != self.global_parent_binding.parent.semantic_commitment
                or self.semantic_commitment.shared_context != self.scope.bank
                or len(self.canonical_bytes()) > MAXIMUM_ACQUISITION_BYTES):
            raise ValueError('acquisition admission aliases its new actual configuration and original semantic commitment')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.admission_id, self)

    @property
    def programme(self):
        return self.scope.programme

    @property
    def bank(self):
        return self.scope.bank

    @property
    def wave(self):
        return self.scope.wave


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAcquisitionCollectorConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/acquisition-collector-config'
    config_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    scope: ObjectIdentity
    admission: ObjectIdentity
    mode: str = 'E4_REVISION_CALIBRATION'

    def __post_init__(self):
        if (self.config_id != 'config.'+self.wave.wave_id+'.acquisition-collect'
                or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.scope.object_schema != ScheduledProgrammeAcquisitionScope.SCHEMA
                or self.admission.object_schema != ScheduledProgrammeAcquisitionAdmission.SCHEMA
                or self.mode not in MODES):
            raise ValueError('acquisition collector substitutes its actual new scoped configuration or admission product')

    @property
    def operation(self):
        return 'collect-development' if self.mode == 'E4_DEVELOPMENT' else 'collect'
