# SPDX-License-Identifier: MPL-2.0
"""Exact original multiwave qualification, separate from preparation receipts.

The stock custody owner supplies real issued plans, current successful receipts
and companion bytes. Pure callbacks cannot read outcomes, grant authority or
replace a missing original execution with a proposed task or role label.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.runtime.recursive_qualified_parents import QualifiedParentEvidence, RecursivePriorNativeBinding, RecursiveQualifiedParentBinding

from .forecast import ScheduledCalibration
from .programme_records import NAMESPACE

MAXIMUM_BYTES = 16*1024**2
QUALIFIED_REASON = ('scheduled-programme-complete-original-global-calibration-bank-qualified',)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeQualifiedParentDeclaration(CanonicalRecord):
    """Blind original parent locators, with no score/radius/outcome payload."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/qualified-parent-declaration'
    declaration_id: str
    calibration: ObjectIdentity
    publication: ArtifactWriteResult
    contribution: ContributionManifest
    binding: RecursiveQualifiedParentBinding
    programme: ObjectIdentity
    evidence: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    reservation: ObjectIdentity
    group_ids: tuple[str, ...]

    def __post_init__(self):
        from .programme_calibration import ScheduledProgrammeCalibrationEvidence
        from .programme_records import ScheduledProgramme
        validate_stable_id(self.declaration_id)
        require_sorted_unique_strings(self.group_ids, field_name='original calibration groups', allow_empty=False)
        if (type(self.binding) is not RecursiveQualifiedParentBinding or type(self.contribution) is not ContributionManifest
                or type(self.publication) is not ArtifactWriteResult):
            raise ValueError('programme parent declaration requires closed original contribution, binding and publication')
        products = tuple(p for p in self.contribution.products if p.product_id == self.binding.product_id)
        logical, physical = self.publication.logical, self.publication.materialization
        if (self.binding.contribution_id != self.contribution.contribution_id or len(products) != 1
                or (self.calibration.object_schema, self.calibration.object_version) != (ScheduledCalibration.SCHEMA, ScheduledCalibration.VERSION)
                or self.programme.object_schema != 'empirical-lawhood/matrix-scheduled-programme/programme'
                or self.programme.object_version != ScheduledProgramme.VERSION
                or self.evidence.object_schema != ScheduledProgrammeCalibrationEvidence.SCHEMA
                or self.evidence.object_version != ScheduledProgrammeCalibrationEvidence.VERSION
                or len(self.group_ids) != 64 or products[0].record != self.calibration
                or products[0].role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
                or products[0].producing_receipt.object_id != self.binding.receipt_id
                or products[0].artifact.artifact_id != logical.logical_artifact_id
                or products[0].artifact.payload_schema != ScheduledCalibration.SCHEMA
                or products[0].artifact.sha256 != self.calibration.object_fingerprint
                or products[0].artifact.size_bytes != physical.size_bytes
                or products[0].outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or products[0].visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or self.binding.adjudication not in self.contribution.assessments
                or logical.logical_artifact_id != physical.logical_artifact_id
                or logical.payload_schema != ScheduledCalibration.SCHEMA
                or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
                or logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or logical.content_sha256 != self.calibration.object_fingerprint
                or physical.physical_sha256 != self.calibration.object_fingerprint
                or physical.size_bytes > MAXIMUM_BYTES or physical.compression != 'none' or physical.partition_selector is not None
                or len(self.canonical_bytes()) > 4*1024**2):
            raise ValueError('programme parent declaration changes exact blind original sealed parent locators')
        scope = self.contribution.scope
        if (scope.population_id != self.calibration.object_id or scope.source_config_sha256 != self.calibration.object_fingerprint):
            raise ValueError('programme parent declaration changes the original semantic qualification scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.declaration_id, self)


def validate_qualified_parent_declaration(bank, declaration):
    """Bind blind query design to the exact prior complete qualified bank."""
    if type(declaration) is not ScheduledProgrammeQualifiedParentDeclaration:
        raise ValueError('programme query requires its closed original qualified-parent declaration')
    declaration.__post_init__()
    design = bank.forecast_design
    if (design.calibration != declaration.calibration or design.calibration_publication != declaration.publication
            or design.model != declaration.model or design.criterion != declaration.criterion
            or design.calibration_reservation != declaration.reservation
            or design.calibration_group_ids != declaration.group_ids):
        raise ValueError('programme query substitutes the original sealed calibration/model/criterion/reservation/group scope')


def authenticated_companion(parent_evidence):
    from .programme_calibration import ScheduledProgrammeCalibrationEvidence
    if type(parent_evidence) is not QualifiedParentEvidence:
        raise PermissionError('programme calibration requires stock original qualified-parent custody')
    products = tuple(p for p in parent_evidence.additional_products
        if p.logical.payload_schema == ScheduledProgrammeCalibrationEvidence.SCHEMA)
    if len(products) != 1 or len(parent_evidence.additional_products) != 1:
        raise PermissionError('programme calibration lacks its exact actual companion output')
    product = products[0]
    if (product.logical not in parent_evidence.producing_receipt.output_logical_artifacts
            or product.materialization not in parent_evidence.producing_receipt.output_materializations
            or product.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or product.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or len(product.payload) != product.materialization.size_bytes
            or sha256(product.payload).hexdigest() != product.logical.content_sha256
            or product.logical.content_sha256 != product.materialization.physical_sha256):
        raise PermissionError('programme calibration companion changes the actual same producer receipt or sealed bytes')
    evidence = decode_canonical_bytes(product.payload, ScheduledProgrammeCalibrationEvidence, maximum_bytes=MAXIMUM_BYTES)
    if evidence.canonical_bytes() != product.payload:
        raise PermissionError('programme calibration companion changes exact canonical record bytes')
    semantic = decode_canonical_bytes(parent_evidence.product_payload, ScheduledCalibration, maximum_bytes=MAXIMUM_BYTES)
    if semantic != evidence.calibration or semantic.canonical_bytes() != parent_evidence.product_payload:
        raise PermissionError('programme calibration companion substitutes its actual original semantic product')
    return evidence


def prior_execution_bindings(parent_evidence):
    """Project only the exhaustive original requests in authenticated bytes."""
    from .programme_bindings import ScheduledProgrammeWaveAdmission
    from .programme_acquisition import ScheduledProgrammeAcquisitionAdmission
    from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
    evidence = _calibration_evidence(parent_evidence)
    requests = []
    from .compact_records import NAMESPACE as COMPACT_NAMESPACE
    cases = {case.root_id: case for case in evidence.reduction.cases}
    for custody in evidence.wave_custody:
        if custody.prior_execution is None:
            raise PermissionError('programme calibration lacks a genuine original issued wave execution')
        natives = []
        for root in custody.configuration.wave.root_ids:
            for native in cases[root].native:
                if native.disposition != 'COMPLETED':
                    raise PermissionError('programme qualified parent has unknown, failed, unentered or unused original native work')
                natives.append(RecursivePriorNativeBinding(COMPACT_NAMESPACE+'.'+root+'.'+native.phase,
                    native.definition, native.completion, native.receipt))
        schema = ScheduledProgrammeAcquisitionAdmission.SCHEMA if type(custody) is ScheduledProgrammeAcquisitionWaveCustody else ScheduledProgrammeWaveAdmission.SCHEMA
        requests.append(replace(custody.prior_execution,
            additional_output_schema_ids=(schema,), scope_output_schema_ids=(schema,) if type(custody) is ScheduledProgrammeAcquisitionWaveCustody else (),
            native_subwork=tuple(natives), record_id_field='result_id'))
    return tuple(requests)


def _calibration_evidence(parent_evidence):
    from .programme_runtime_views import ScheduledProgrammeCurrentCalibration
    if type(parent_evidence) is ScheduledProgrammeCurrentCalibration:
        return parent_evidence.calibration_evidence
    return authenticated_companion(parent_evidence)


def prior_execution_scope_validator(*, parent_evidence, binding, package, execution_plan):
    """Refuse an unrelated original run before protected scientific reads."""
    from .programme_calibration import CALIBRATE_TASK_ID
    from .compact_records import ScheduledCompactBank
    evidence = _calibration_evidence(parent_evidence)
    programme = evidence.configuration.programme
    requests = prior_execution_bindings(parent_evidence)
    matches = tuple(c for c, request in zip(evidence.wave_custody, requests, strict=True) if request == binding)
    if len(matches) != 1:
        raise PermissionError('programme prior execution is outside the authenticated global wave corpus')
    custody = matches[0]
    parent = parent_evidence.package
    global_cutoffs = tuple(c.information_cutoff for c in programme.cases)
    from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
    acquisition = type(custody) is ScheduledProgrammeAcquisitionWaveCustody
    expected_cutoffs = tuple(c.information_cutoff for c in programme.cases
        if not acquisition or c.root_id in custody.configuration.wave.root_ids)
    if (package.system != parent.system or package.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or package.experiment.information_cutoffs != expected_cutoffs
            or parent.experiment.information_cutoffs != global_cutoffs
            or package.experiment.system_id != parent.experiment.system_id
            or package.experiment.world_id != parent.experiment.world_id
            or ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan) != custody.execution_plan
            or binding.record != custody.result or binding.receipt != ObjectIdentity.from_record(custody.receipt.receipt_id, custody.receipt)
            or binding.logical_artifact_id != custody.publication.logical.logical_artifact_id
            or tuple(t for t in execution_plan.tasks if t.task_id == custody.producer_task.task_id) != (custody.producer_task,)):
        raise PermissionError('programme prior execution changes the genuine original global64 study or declared subgroup')
    if acquisition:
        from .programme_acquisition import ScheduledProgrammeAcquisitionAdmission, _local_root, _validate_local_root
        products = tuple(value for value in parent_evidence.prior_scope_products
            if value.logical.payload_schema == ScheduledProgrammeAcquisitionAdmission.SCHEMA)
        if len(products) != 1 or len(parent_evidence.prior_scope_products) != 1:
            raise PermissionError('programme prior acquisition omits its actual blind original admission scope')
        admission = decode_canonical_bytes(products[0].payload, ScheduledProgrammeAcquisitionAdmission, maximum_bytes=MAXIMUM_BYTES)
        scope = admission.scope
        local_root = package.issued_study.candidate.authoring_package.base.draft
        if (admission.identity != custody.configuration.admission or scope.identity != custody.configuration.scope
                or scope.programme != programme or scope.wave != custody.configuration.wave
                or scope.bank != programme.bank or scope.programme.mode != 'E4_REVISION_CALIBRATION'
                or scope.global_root.experiment.information_cutoffs != global_cutoffs
                or scope.global_root.experiment != parent.issued_study.candidate.authoring_package.base.draft.experiment):
            raise PermissionError('programme prior acquisition substitutes global question, whole-group admission or exact original scope')
        views = local_root.experiment.obligations.structural_convergence.numerical_view_ids
        _validate_local_root(scope, local_root, _local_root(scope, views), execution_plan=execution_plan,
            protocol=package.issued_study.candidate.base_candidate.base_candidate.protocol)
    producing = tuple(t for t in parent_evidence.execution_plan.tasks if t.task_id == CALIBRATE_TASK_ID)
    inputs = () if len(producing) != 1 else tuple(p for p in producing[0].external_inputs
        if p.logical_artifact_id == custody.publication.logical.logical_artifact_id)
    if (len(inputs) != 1 or inputs[0].expected_payload_schema != custody.result.object_schema
            or inputs[0].expected_content_sha256 != custody.result.object_fingerprint
            or inputs[0].expected_size_bytes != custody.publication.materialization.size_bytes
            or inputs[0].expected_outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or inputs[0].expected_visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise PermissionError('programme prior execution is outside the actual global tail frozen input corpus')
    bank_inputs = tuple(p for t in execution_plan.tasks for p in t.external_inputs
        if p.expected_payload_schema == ScheduledCompactBank.SCHEMA)
    if (not bank_inputs or any(p.expected_content_sha256 != programme.bank.object_fingerprint
            or p.logical_artifact_id != programme.bank.object_id for p in bank_inputs)):
        raise PermissionError('programme prior execution substitutes its exact original global bank')
    from .compact_records import NAMESPACE as COMPACT_NAMESPACE
    wanted = {COMPACT_NAMESPACE+'.'+root+'.'+role for root in custody.configuration.wave.root_ids for role in
        ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical',
         'physical-forecast', 'responses', 'response-score')}
    wanted |= {custody.wave_id+'.open', custody.wave_id+'.collect'}
    if {t.task_id for t in execution_plan.tasks} != wanted or len(execution_plan.tasks) != len(wanted):
        raise PermissionError('programme prior execution changes its complete admitted eleven-stage task census')


def _validate_prior_products(parent_evidence, evidence):
    from .programme_bindings import ScheduledProgrammeWaveAdmission
    from .programme_acquisition import ScheduledProgrammeAcquisitionAdmission
    from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
    from .programme_calibration import validate_wave_custody
    from .programme_reduction import ScheduledProgrammeReceiptReference, ScheduledProgrammeWaveResult
    requests = prior_execution_bindings(parent_evidence)
    if tuple(p.binding for p in parent_evidence.prior_executions) != requests:
        raise PermissionError('programme calibration lacks its complete stock-authenticated original wave executions')
    for prior, custody in zip(parent_evidence.prior_executions, evidence.wave_custody, strict=True):
        if tuple(value.binding for value in prior.native_subwork) != prior.binding.native_subwork:
            raise PermissionError('programme calibration loses its exact original native completion/receipt census')
        tasks = {task.task_id: task for task in prior.execution_plan.tasks}
        for native in prior.native_subwork:
            task = tasks.get(native.binding.task_id)
            definition = native.inspection.definition
            if (task is None or definition.configuration != ObjectIdentity(
                    task.capability.config.config_id, task.capability.config.config_schema,
                    '2.0.0', task.capability.config.content_sha256)
                    or native.inspection.completion.definition != definition.identity
                    or definition.input_materialization_ids != native.inspection.receipt.input_materialization_ids):
                raise PermissionError('programme original native work changes its actual mathematical configuration or input contact')
        result = decode_canonical_bytes(prior.product.payload, ScheduledProgrammeWaveResult, maximum_bytes=MAXIMUM_BYTES)
        if result.identity != prior.binding.record or result.identity != custody.result:
            raise PermissionError('programme original wave result changes its exact record identity')
        validate_wave_custody(evidence.configuration.programme, result, custody, prior.execution_plan)
        by_task = {r.task_id: r for r in prior.receipts}
        if by_task.get(custody.receipt.task_id) != custody.receipt:
            raise PermissionError('programme calibration substitutes its original current collector receipt')
        admission_type = ScheduledProgrammeAcquisitionAdmission if type(custody) is ScheduledProgrammeAcquisitionWaveCustody else ScheduledProgrammeWaveAdmission
        admissions = tuple(p for p in prior.additional_products if p.logical.payload_schema == admission_type.SCHEMA)
        if len(admissions) != 1 or len(prior.additional_products) != 1:
            raise PermissionError('programme calibration omits its real original global-scope admission product')
        admission = decode_canonical_bytes(admissions[0].payload, admission_type, maximum_bytes=MAXIMUM_BYTES)
        if (admission.programme != evidence.configuration.programme or admission.wave != custody.configuration.wave
                or admission.identity != custody.configuration.admission):
            raise PermissionError('programme original admission changes global64 scope or its whole-group subdivision')
        for case in result.cases:
            for header in case.ordinary_receipts:
                if type(header) is not ScheduledProgrammeReceiptReference:
                    raise PermissionError('programme original case omits actual dependency receipt headers')
                receipt = by_task.get(header.task_id)
                if (receipt is None or receipt.receipt_id != header.receipt_id
                        or receipt.operational_status is not OperationalStatus.SUCCEEDED
                        or not set(header.output_materialization_ids) <= {p.materialization_id for p in receipt.output_materializations}):
                    raise PermissionError('programme original case substitutes actual eleven-stage receipt lineage')


def validate_qualified_parent_declaration_evidence(bank, declaration, parent_evidence):
    """Compare an independently replayed original qualification to blind pins."""
    validate_qualified_parent_declaration(bank, declaration)
    evidence = authenticated_companion(parent_evidence)
    c, q = evidence.calibration, parent_evidence.adjudication
    if (parent_evidence.binding != declaration.binding or evidence.identity != declaration.evidence
            or evidence.configuration.programme.identity != declaration.programme
            or ObjectIdentity.from_record(c.calibration_id, c) != declaration.calibration
            or c.model != declaration.model or c.criterion != declaration.criterion
            or c.reservation != declaration.reservation or c.group_ids != declaration.group_ids
            or declaration.publication.logical not in parent_evidence.producing_receipt.output_logical_artifacts
            or declaration.publication.materialization not in parent_evidence.producing_receipt.output_materializations
            or q.reason_codes != QUALIFIED_REASON or q.plumbing_only or q.fixture_scope_id is not None
            or q.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or evidence.reduction.numerical_disposition != 'SATISFIED'
            or evidence.configuration.programme.mode != 'E4_REVISION_CALIBRATION'
            or len(c.group_ids) != 64 or len(c.cases) != 576 or evidence.reduction.order_statistic_rank != 62):
        raise PermissionError('programme declaration substitutes the original complete qualified calibration or actual publication')
    _validate_prior_products(parent_evidence, evidence)


def qualified_parent_assessor(*, requirement, connection, contribution, product, parent_evidence):
    """Authenticate the sole global qualification over all original64×9 cases."""
    from .programme_calibration import CALIBRATE_TASK_ID, QUALIFY_TASK_ID
    from .programme_calibration_bindings import calibration_factories
    evidence = authenticated_companion(parent_evidence)
    c, q, scope = evidence.calibration, parent_evidence.adjudication, requirement.scope
    programme = evidence.configuration.programme
    if (requirement.condition_role is not ConditionRole.EVIDENTIAL or scope is None or scope != contribution.scope
            or scope.population_id != c.calibration_id or scope.source_config_sha256 != c.fingerprint()
            or connection.consumer_input_id != 'calibration' or connection.evidence_role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
            or not requirement.consumer_operation_id.endswith('.forecast-calibrated')
            or product.record != ObjectIdentity.from_record(c.calibration_id, c) or product.artifact.sha256 != c.fingerprint()
            or product.outcome_access is not OutcomeAccess.EVALUATION_SEALED or product.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or q.plumbing_only or q.fixture_scope_id is not None or q.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or parent_evidence.package.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or q.relation != ObjectIdentity.from_record(parent_evidence.package.system.relation.relation_id, parent_evidence.package.system.relation)
            or q.independent_unit_id != c.independent_unit_id or q.reason_codes != QUALIFIED_REASON
            or q.information_cutoffs != tuple(ObjectIdentity.from_record(case.information_cutoff.cutoff_id, case.information_cutoff)
                for case in programme.cases)
            or evidence.reduction.numerical_disposition != 'SATISFIED'
            or programme.mode != 'E4_REVISION_CALIBRATION' or len(programme.group_ids) != 64 or len(programme.cases) != 576
            or evidence.reduction.order_statistic_rank != 62
            or parent_evidence.producing_receipt.task_id != CALIBRATE_TASK_ID
            or parent_evidence.qualification_receipt.task_id != QUALIFY_TASK_ID):
        raise PermissionError('programme calibration parent changes genuine full64 qualification or original sealed semantic scope')
    for role, task_id in (('calibrate', CALIBRATE_TASK_ID), ('calibration-qualify', QUALIFY_TASK_ID)):
        factory = next(f for f in calibration_factories() if f.manifest.capability_key == NAMESPACE+'.'+role)
        tasks = tuple(t for t in parent_evidence.execution_plan.tasks if t.task_id == task_id)
        config = evidence.configuration if role == 'calibrate' else replace(evidence.configuration,
            config_id='config.'+NAMESPACE+'.calibration-qualify', operation='calibration-qualify')
        if (len(tasks) != 1 or tasks[0].capability.capability_key != factory.manifest.capability_key
                or tasks[0].capability.capability_version != factory.manifest.capability_version
                or tasks[0].capability_implementation_sha256 != factory.manifest.implementation_sha256
                or tasks[0].capability.config.config_id != config.config_id
                or tasks[0].capability.config.config_schema != config.SCHEMA
                or tasks[0].capability.config.config_schema_sha256 != factory.manifest.config_schema_sha256
                or tasks[0].capability.config.content_sha256 != config.fingerprint()
                or tasks[0].stage is not factory.registration.stage or tasks[0].barrier is not factory.registration.barrier):
            raise PermissionError('programme calibration changes actual global producing/reveal configuration or installed owner')
        if role == 'calibration-qualify' and (tasks[0].stage is not ScientificStage.REVEAL
                or tasks[0].barrier is not BarrierKind.REVEAL or tasks[0].dependency_task_ids != (CALIBRATE_TASK_ID,)):
            raise PermissionError('programme calibration loses its single actual global reveal dependency')
    _validate_prior_products(parent_evidence, evidence)
