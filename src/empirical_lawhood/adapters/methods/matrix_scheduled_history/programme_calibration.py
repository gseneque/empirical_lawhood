# SPDX-License-Identifier: MPL-2.0
"""One global calibration reduction and its bounded actual wave custody.

These records preserve the historical calibration semantics. They do not
authenticate a store, issue a study, or grant qualification by construction.
The runtime owner verifies the original complete plans and publications before
emitting the bounded summary; the separate reveal owner assesses it.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, ExecutionPlan, ExecutionTask, ScientificStage
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from .calibration import reduce_cases
from .compact_records import NAMESPACE as COMPACT_NAMESPACE
from .forecast import ScheduledCalibration, ScheduledCalibrationCase, _case_digest
from .programme_bindings import ScheduledProgrammeWaveCollectorConfig
from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
from .programme_records import NAMESPACE, ScheduledProgramme
from .programme_reduction import (
    ScheduledProgrammeReceiptReference, ScheduledProgrammeReduction, ScheduledProgrammeWaveResult,
    reduce_programme, validate_programme_reduction,
)

MAXIMUM_CALIBRATION_BYTES = 16*1024**2
MAXIMUM_CONFIG_BYTES = 4*1024**2
CALIBRATE_TASK_ID = COMPACT_NAMESPACE+'.calibrate'
QUALIFY_TASK_ID = COMPACT_NAMESPACE+'.calibration-qualify'


def _publication_pin(identity, publication, *, size=None):
    if (type(identity) is not ObjectIdentity or type(publication) is not ArtifactWriteResult
            or publication.logical.payload_schema != identity.object_schema
            or publication.logical.content_sha256 != identity.object_fingerprint
            or publication.materialization.physical_sha256 != identity.object_fingerprint
            or publication.logical.logical_artifact_id != publication.materialization.logical_artifact_id
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != 'application/json'
            or size is not None and publication.materialization.size_bytes != size):
        raise ValueError('programme calibration substitutes an actual canonical publication pin')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveCustody(CanonicalRecord):
    """Exact collector receipt/configuration/task and original plan publication.

    The task slice is checked against the complete original plan by the runtime
    owner. Its presence alone never authenticates membership in that plan.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-custody'
    binding_id: str
    wave_id: str
    result: ObjectIdentity
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    execution_plan: ObjectIdentity
    execution_plan_publication: ArtifactWriteResult
    configuration: ScheduledProgrammeWaveCollectorConfig
    configuration_publication: ArtifactWriteResult
    producer_task: ExecutionTask
    prior_execution: RecursivePriorExecutionBinding | None = None

    def __post_init__(self):
        validate_stable_id(self.binding_id)
        validate_stable_id(self.wave_id)
        task, config, receipt = self.producer_task, self.configuration, self.receipt
        if (type(task) is not ExecutionTask or type(config) is not ScheduledProgrammeWaveCollectorConfig
                or type(receipt) is not CanonicalTaskReceipt
                or self.result.object_schema != ScheduledProgrammeWaveResult.SCHEMA
                or self.result.object_version != ScheduledProgrammeWaveResult.VERSION
                or self.execution_plan.object_schema not in (CandidateExecutionPlan.SCHEMA, ExecutionPlan.SCHEMA)
                or self.execution_plan.object_version != '1.0.0'
                or config.wave.wave_id != self.wave_id or config.mode != 'E4_REVISION_CALIBRATION'
                or receipt.task_id != self.wave_id+'.collect' or task.task_id != receipt.task_id
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or task.stage is not ScientificStage.TRANSFORM
                or task.capability.capability_key != NAMESPACE+'.collect'
                or task.capability.capability_version != '1.0.0'
                or task.capability.config.config_id != config.config_id
                or task.capability.config.config_schema != config.SCHEMA
                or task.capability.config.content_sha256 != config.fingerprint()
                or task.capability.config.artifact_id != self.configuration_publication.logical.logical_artifact_id
                or self.configuration_publication.materialization.materialization_id not in receipt.input_materialization_ids
                or receipt.output_logical_artifacts != (self.publication.logical,)
                or receipt.output_materializations != (self.publication.materialization,)
                or not any(c.check_id == 'scheduled-original-source-cutoff-census' and c.passed for c in receipt.checks)):
            raise ValueError('programme wave custody changes actual successful collector/config/plan/output')
        _publication_pin(self.result, self.publication)
        for record, key, publication in ((receipt, receipt.receipt_id, self.receipt_publication),
                (config, config.config_id, self.configuration_publication)):
            _publication_pin(ObjectIdentity.from_record(key, record), publication, size=len(record.canonical_bytes()))
        _publication_pin(self.execution_plan, self.execution_plan_publication)
        prior = self.prior_execution
        if prior is not None and (type(prior) is not RecursivePriorExecutionBinding
                or prior.execution_plan != self.execution_plan or prior.run_id != receipt.run_id
                or prior.task_id != receipt.task_id or prior.record != self.result
                or prior.logical_artifact_id != self.publication.logical.logical_artifact_id
                or prior.receipt != ObjectIdentity.from_record(receipt.receipt_id, receipt)):
            raise ValueError('programme wave custody substitutes its original issued execution locator')
        if (self.publication.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or self.publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or len(task.outputs) != 1):
            raise ValueError('programme wave custody substitutes its original sealed collector output')
        output = task.outputs[0]
        logical, physical = self.publication.logical, self.publication.materialization
        if (output.output_id != task.task_id+'.product' or output.logical_artifact_id != logical.logical_artifact_id
                or output.relative_path != physical.relative_path or output.payload_schema != logical.payload_schema
                or output.profile is not logical.profile or output.media_type != logical.media_type
                or output.outcome_access is not logical.outcome_access or output.visibility_ceiling is not logical.visibility_ceiling):
            raise ValueError('programme wave custody substitutes its exact planned publication')
        inputs = tuple(p for p in task.external_inputs if p.logical_artifact_id == task.capability.config.artifact_id)
        if (len(inputs) != 1 or inputs[0].expected_payload_schema != config.SCHEMA
                or inputs[0].expected_content_sha256 != config.fingerprint()
                or inputs[0].expected_size_bytes != len(config.canonical_bytes())
                or inputs[0].expected_outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or inputs[0].expected_visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('programme wave custody omits its exact original blind collector configuration')
        if len(self.canonical_bytes()) > MAXIMUM_CALIBRATION_BYTES:
            raise ValueError('programme wave custody exceeds its closed 16MiB bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)


def validate_wave_summary(programme, result, custody):
    """Join bounded actual collector metadata; this does not authenticate a plan."""
    if type(custody) is ScheduledProgrammeAcquisitionWaveCustody:
        from .programme_acquisition_custody import validate_acquisition_wave_summary
        return validate_acquisition_wave_summary(programme, result, custody)
    if (type(custody) is not ScheduledProgrammeWaveCustody or type(result) is not ScheduledProgrammeWaveResult
            or custody.result != result.identity or custody.wave_id != result.wave_id
            or custody.configuration.programme != programme.identity or custody.configuration.bank != programme.bank
            or custody.configuration.wave not in programme.waves
            or result.programme != programme.identity
            or result.root_ids != custody.configuration.wave.root_ids
            or result.group_ids != custody.configuration.wave.group_ids):
        raise ValueError('programme calibration loses actual original wave summary/census/custody')
    from .programme_bindings import operation_manifests
    manifests = {m.capability_key: m for m in operation_manifests()}
    manifest = manifests[NAMESPACE+'.collect']
    if (custody.producer_task.capability_implementation_sha256 != manifest.implementation_sha256
            or custody.producer_task.capability.config.config_schema_sha256 != manifest.config_schema_sha256):
        raise ValueError('programme calibration substitutes the installed actual collector implementation')
    headers = tuple(r for case in result.cases for r in case.ordinary_receipts)
    if any(type(r) is not ScheduledProgrammeReceiptReference for r in headers):
        raise ValueError('programme runtime calibration requires actual opaque dependency headers')
    expected_tasks = {COMPACT_NAMESPACE+'.'+root+'.'+role for root in result.root_ids for role in
        ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical',
         'physical-forecast', 'responses', 'response-score')}
    if ({r.task_id for r in headers} != expected_tasks or len(headers) != len(expected_tasks)
            or set(custody.producer_task.dependency_task_ids) != expected_tasks | {result.wave_id+'.open'}
            or any(not set(r.output_materialization_ids) & set(custody.receipt.input_materialization_ids) for r in headers)):
        raise ValueError('programme calibration drops actual eleven-stage collector receipt lineage')
    return result


def validate_wave_custody(programme, result, custody, plan):
    """Additionally join the complete actual original plan and installed owners."""
    if type(custody) is ScheduledProgrammeAcquisitionWaveCustody:
        from .programme_acquisition_custody import validate_acquisition_wave_custody
        return validate_acquisition_wave_custody(programme, result, custody, plan)
    validate_wave_summary(programme, result, custody)
    if (type(plan) not in (CandidateExecutionPlan, ExecutionPlan)
            or ObjectIdentity.from_record(plan.execution_plan_id, plan) != custody.execution_plan
            or tuple(t for t in plan.tasks if t.task_id == custody.producer_task.task_id) != (custody.producer_task,)
            or custody.receipt.implementation_commit != plan.implementation_commit):
        raise ValueError('programme calibration loses actual original complete wave plan/census/custody')
    expected_tasks = {r.task_id for case in result.cases for r in case.ordinary_receipts}
    if {t.task_id for t in plan.tasks} != expected_tasks | {result.wave_id+'.open', result.wave_id+'.collect'}:
        raise ValueError('programme calibration changes complete original398-task wave census')
    from .programme_bindings import operation_manifests
    manifests = {m.capability_key: m for m in operation_manifests()}
    for task in plan.tasks:
        role = 'open' if task.task_id == result.wave_id+'.open' else task.task_id.rsplit('.', 1)[-1]
        expected = manifests.get(NAMESPACE+'.'+role)
        if (expected is None or task.capability.capability_key != expected.capability_key
                or task.capability.capability_version != expected.capability_version
                or task.capability_implementation_sha256 != expected.implementation_sha256
                or task.capability.config.config_schema_sha256 != expected.config_schema_sha256):
            raise ValueError('programme calibration substitutes an original installed wave phase selection')
    return result


def authenticate_wave_custody(plane, binding):
    """Reopen original guarded bytes; metadata and slices alone are insufficient."""
    from .commitment import authenticate_publication
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    binding.__post_init__()
    for record, publication in ((binding.receipt, binding.receipt_publication),
            (binding.configuration, binding.configuration_publication)):
        authenticate_publication(plane, publication, record)
    authenticate_publication(plane, binding.publication)
    authenticate_publication(plane, binding.execution_plan_publication)
    def read(publication, cls):
        raw = read_bounded_bytes(plane.root.resolve(publication.materialization.relative_path, for_write=False),
            maximum_bytes=MAXIMUM_CALIBRATION_BYTES)
        return decode_canonical_bytes(raw, cls, maximum_bytes=MAXIMUM_CALIBRATION_BYTES)
    result = read(binding.publication, ScheduledProgrammeWaveResult)
    cls = ExecutionPlan if binding.execution_plan.object_schema == ExecutionPlan.SCHEMA else CandidateExecutionPlan
    plan = read(binding.execution_plan_publication, cls)
    if (result.identity != binding.result or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan
            or tuple(t for t in plan.tasks if t.task_id == binding.producer_task.task_id) != (binding.producer_task,)):
        raise ValueError('programme wave custody changes guarded original plan membership or result bytes')
    return result, plan


def authenticate_wave_custody_metadata(plane, binding, *, programme):
    """Authenticate blind original controls and opaque sealed-result metadata.

    No score/result payload is opened or verified. Original plan membership and
    published input pins establish preparation only; permissions and genuine
    execution/reveal remain prerequisites of the actual calibration consumer.
    """
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from hashlib import sha256
    if type(binding) is not ScheduledProgrammeWaveCustody:
        raise ValueError('programme metadata requires its closed original wave custody')
    binding.__post_init__()
    if (binding.configuration.programme != programme.identity or binding.configuration.bank != programme.bank
            or binding.configuration.wave not in programme.waves):
        raise ValueError('programme metadata substitutes its exact original global scope or subdivision')
    read_publication_metadata(plane, binding.publication)

    def blind_bytes(publication, record=None):
        logical, physical = publication.logical, publication.materialization
        if (logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('programme preparation refuses protected original control payload access')
        # Preparation authenticates only this selected blind control payload.
        # Full publication-batch verification is unnecessary at this boundary.
        read_publication_metadata(plane, publication)
        raw = read_bounded_bytes(plane.root.resolve(physical.relative_path, for_write=False),
            maximum_bytes=MAXIMUM_CALIBRATION_BYTES)
        if (len(raw) != physical.size_bytes or sha256(raw).hexdigest() != logical.content_sha256
                or sha256(raw).hexdigest() != physical.physical_sha256
                or record is not None and raw != record.canonical_bytes()):
            raise ValueError('programme preparation changes exact original blind control bytes')
        return raw

    for record, publication in ((binding.receipt, binding.receipt_publication),
            (binding.configuration, binding.configuration_publication)):
        blind_bytes(publication, record)
    publication = binding.execution_plan_publication
    cls = ExecutionPlan if binding.execution_plan.object_schema == ExecutionPlan.SCHEMA else CandidateExecutionPlan
    raw = blind_bytes(publication)
    plan = decode_canonical_bytes(raw, cls, maximum_bytes=MAXIMUM_CALIBRATION_BYTES)
    if (raw != plan.canonical_bytes() or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan
            or tuple(t for t in plan.tasks if t.task_id == binding.producer_task.task_id) != (binding.producer_task,)
            or plan.implementation_commit != binding.receipt.implementation_commit):
        raise ValueError('programme metadata substitutes original producer membership or plan bytes')
    return plan


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeCalibrationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/calibration-config'
    config_id: str
    operation: str
    programme: ScheduledProgramme
    bank: ObjectIdentity
    calibration_id: str
    wave_custody: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.calibration_id)
        if (self.operation not in ('calibrate', 'calibration-qualify')
                or self.config_id != 'config.'+NAMESPACE+'.'+self.operation
                or type(self.programme) is not ScheduledProgramme or self.programme.mode != 'E4_REVISION_CALIBRATION'
                or len(self.programme.waves) != 16 or any(len(w.group_ids) != 4 for w in self.programme.waves)
                or self.bank != self.programme.bank or len(self.wave_custody) != len(self.programme.waves)
                or len({p.object_id for p in self.wave_custody}) != len(self.wave_custody)
                or any(type(p) is not ObjectIdentity or p.object_schema not in (
                    ScheduledProgrammeWaveCustody.SCHEMA, ScheduledProgrammeAcquisitionWaveCustody.SCHEMA)
                    or p.object_version != ScheduledProgrammeWaveCustody.VERSION for p in self.wave_custody)
                or len(self.canonical_bytes()) > MAXIMUM_CONFIG_BYTES):
            raise ValueError('programme calibration changes its complete global64 scope or bounded actual configuration')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


def _case_custody(case, role):
    receipts = tuple(r for r in case.ordinary_receipts if type(r) is ScheduledProgrammeReceiptReference
        and r.task_id == COMPACT_NAMESPACE+'.'+case.root_id+'.'+role)
    if len(receipts) != 1 or len(receipts[0].output_materialization_ids) != 1:
        raise ValueError('programme calibration lacks the exact sole actual score/forecast output receipt')
    return receipts[0].receipt_id, receipts[0].output_materialization_ids[0]


def semantic_calibration(programme, reduction, *, calibration_id, model, independent_unit_id):
    """Keep literal legacy cases and their actual scientific receipt IDs."""
    rows, declarations = [], {c.root_id: c for c in programme.cases}
    if (type(reduction) is not ScheduledProgrammeReduction or reduction.programme != programme.identity
            or reduction.mode != programme.mode or tuple(c.root_id for c in reduction.cases) != tuple(declarations)
            or any((c.source, c.independent_group_id) != (declarations[c.root_id].source,
                declarations[c.root_id].independent_group_id) for c in reduction.cases)):
        raise ValueError('programme calibration changes complete original scientific source/group census')
    for case in reduction.cases:
        declaration = declarations[case.root_id]
        if (case.disposition != 'COMPLETED' or case.score is None or case.forecast is None
                or case.score_disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE',
                    'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED')):
            raise ValueError('programme calibration cannot manufacture a legacy product from incomplete actual cases')
        sr, sm = _case_custody(case, 'response-score')
        fr, fm = _case_custody(case, 'forecast')
        rows.append(ScheduledCalibrationCase(case.root_id, case.independent_group_id, case.source, declaration.coordinate,
            declaration.information_cutoff.coordinate, case.score, case.forecast, sr, fr, sm, fm,
            case.score_disposition, case.cumulative_log_errors, case.log_error_points))
    rows = tuple(rows)
    return ScheduledCalibration(calibration_id, programme.reservation, model, programme.criterion, programme.allocation,
        programme.calibration_criterion, independent_unit_id, tuple(sorted({c.family_id for c in programme.cases})),
        rows, programme.group_ids, reduce_cases(rows), tuple(sorted((c.score for c in rows), key=lambda o: o.object_id)), _case_digest(rows))


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeCalibrationEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/calibration-evidence'
    evidence_id: str
    configuration: ScheduledProgrammeCalibrationConfig
    reduction: ScheduledProgrammeReduction
    calibration: ScheduledCalibration
    wave_custody: tuple[ScheduledProgrammeWaveCustody | ScheduledProgrammeAcquisitionWaveCustody, ...]

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        config = self.configuration
        if (type(config) is not ScheduledProgrammeCalibrationConfig or config.operation != 'calibrate'
                or type(self.reduction) is not ScheduledProgrammeReduction or type(self.calibration) is not ScheduledCalibration
                or any(type(c) not in (ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody) for c in self.wave_custody)
                or len({type(c) for c in self.wave_custody}) != 1
                or tuple(c.identity for c in self.wave_custody) != config.wave_custody
                or tuple(c.wave_id for c in self.wave_custody) != tuple(w.wave_id for w in config.programme.waves)
                or self.calibration.calibration_id != config.calibration_id):
            raise ValueError('programme calibration evidence substitutes global scope, semantic output or actual wave census')
        by_root = {c.root_id: c for c in self.reduction.cases}
        waves = tuple(ScheduledProgrammeWaveResult(c.result.object_id, config.programme.identity, c.wave_id,
            c.configuration.wave.group_ids, c.configuration.wave.root_ids,
            tuple(by_root[root] for root in c.configuration.wave.root_ids)) for c in self.wave_custody)
        validate_programme_reduction(config.programme, self.reduction, wave_results=waves)
        for wave, custody in zip(waves, self.wave_custody, strict=True):
            validate_wave_summary(config.programme, wave, custody)
        if (tuple(w.identity for w in waves) != tuple(c.result for c in self.wave_custody)
                or self.calibration != semantic_calibration(config.programme, self.reduction,
                    calibration_id=config.calibration_id, model=self.calibration.model,
                    independent_unit_id=self.calibration.independent_unit_id)
                or len(self.canonical_bytes()) > MAXIMUM_CALIBRATION_BYTES):
            raise ValueError('programme calibration evidence changes actual wave bytes, global reduction or closed16MiB semantics')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)


def calibrate_programme(config, bank, wave_results, custody, plans=None):
    from .programme_records import validate_programme_bank
    validate_programme_bank(config.programme, bank)
    if config.operation != 'calibrate':
        raise ValueError('programme global calibration requires its exact transform configuration')
    custody, wave_results = tuple(custody), tuple(wave_results)
    plans = None if plans is None else tuple(plans)
    if (tuple(c.identity for c in custody) != config.wave_custody
            or tuple(c.wave_id for c in custody) != tuple(w.wave_id for w in config.programme.waves)
            or len(wave_results) != len(custody) or plans is not None and len(plans) != len(custody)):
        raise ValueError('programme global calibration drops or duplicates original wave custody')
    for index, (result, binding) in enumerate(zip(wave_results, custody, strict=True)):
        validate_wave_summary(config.programme, result, binding)
        if plans is not None:
            validate_wave_custody(config.programme, result, binding, plans[index])
    reduction = reduce_programme(config.programme, wave_results, reduction_id=config.calibration_id+'.global-reduction',
        authenticate_wave=lambda result: None)  # Every actual wave was joined immediately above.
    criterion = bank.response_selection.calibration_criterion
    calibration = semantic_calibration(config.programme, reduction, calibration_id=config.calibration_id,
        model=bank.forecast_design.model, independent_unit_id=criterion.independent_unit_id)
    evidence = ScheduledProgrammeCalibrationEvidence(config.calibration_id+'.programme-evidence', config,
        reduction, calibration, custody)
    return calibration, evidence


def construction_supported(evidence, criterion):
    """Literal whole-programme numerical conditions, never a credential."""
    from .response_selection import ScheduledCalibrationCriterion
    if type(evidence) is not ScheduledProgrammeCalibrationEvidence or type(criterion) is not ScheduledCalibrationCriterion:
        raise ValueError('programme construction conditions require closed actual evidence and criterion')
    evidence.__post_init__()
    c, r = evidence.calibration, evidence.reduction
    return (c.qualification_criterion == criterion.identity and c.independent_unit_id == criterion.independent_unit_id
        and len(c.group_ids) >= criterion.minimum_group_count
        and set(criterion.required_family_ids) <= set(c.family_ids)
        and Decimal(sum(v is None for _, v, _ in c.scores))/len(c.group_ids) <= criterion.maximum_nonfinite_group_fraction
        and r.numerical_disposition == 'SATISFIED'
        and all(case.disposition == 'COMPLETED' and case.numerical_disposition == 'SATISFIED'
            and all(n.disposition == 'COMPLETED' for n in case.native) for case in r.cases))
