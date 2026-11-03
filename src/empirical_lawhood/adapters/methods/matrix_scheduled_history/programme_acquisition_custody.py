# SPDX-License-Identifier: MPL-2.0
"""Actual new acquisition collector custody; no global law qualification.

Blind metadata authentication never opens the protected WaveResult payload.
Full result authentication is restricted to exposed software fixtures or the
separate authorized original-execution replay after issue/reveal.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, ExecutionPlan, ExecutionTask, ScientificStage
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from .compact_records import NAMESPACE as COMPACT_NAMESPACE
from .programme_acquisition import NAMESPACE, ScheduledProgrammeAcquisitionCollectorConfig
from .programme_reduction import ScheduledProgrammeReceiptReference, ScheduledProgrammeWaveResult

MAXIMUM_CALIBRATION_BYTES = 16*1024**2


def _publication_pin(identity, publication, *, size=None):
    if (type(identity) is not ObjectIdentity or type(publication) is not ArtifactWriteResult
            or publication.logical.payload_schema != identity.object_schema
            or publication.logical.content_sha256 != identity.object_fingerprint
            or publication.materialization.physical_sha256 != identity.object_fingerprint
            or publication.logical.logical_artifact_id != publication.materialization.logical_artifact_id
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != 'application/json'
            or size is not None and publication.materialization.size_bytes != size):
        raise ValueError('acquisition custody substitutes an actual canonical publication pin')


def acquisition_phase_roles(mode):
    suffix = '-development' if mode == 'E4_DEVELOPMENT' else ''
    forecast = 'forecast-calibrated' if mode == 'E4_CONFIRMATION' else 'forecast'
    return ('prefix', 'numerical', 'measure', 'check', 'project', forecast, 'continue'+suffix,
        'full-numerical'+suffix, 'physical-forecast', 'responses'+suffix, 'response-score'+suffix)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAcquisitionWaveCustody(CanonicalRecord):
    """Exact collector receipt/configuration/task and original plan publication.

    The task slice is checked against the complete original plan by the runtime
    owner. Its presence alone never authenticates membership in that plan.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/acquisition-wave-custody'
    binding_id: str
    wave_id: str
    result: ObjectIdentity
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    execution_plan: ObjectIdentity
    execution_plan_publication: ArtifactWriteResult
    configuration: ScheduledProgrammeAcquisitionCollectorConfig
    configuration_publication: ArtifactWriteResult
    producer_task: ExecutionTask
    prior_execution: RecursivePriorExecutionBinding | None = None

    def __post_init__(self):
        validate_stable_id(self.binding_id)
        validate_stable_id(self.wave_id)
        task, config, receipt = self.producer_task, self.configuration, self.receipt
        if (type(task) is not ExecutionTask or type(config) is not ScheduledProgrammeAcquisitionCollectorConfig
                or type(receipt) is not CanonicalTaskReceipt
                or self.result.object_schema != ScheduledProgrammeWaveResult.SCHEMA
                or self.result.object_version != ScheduledProgrammeWaveResult.VERSION
                or self.execution_plan.object_schema not in (CandidateExecutionPlan.SCHEMA, ExecutionPlan.SCHEMA)
                or self.execution_plan.object_version != '1.0.0'
                or config.wave.wave_id != self.wave_id
                or receipt.task_id != self.wave_id+'.collect' or task.task_id != receipt.task_id
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or task.stage is not ScientificStage.TRANSFORM
                or task.capability.capability_key != NAMESPACE+'.'+config.operation
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
        access = OutcomeAccess.DEVELOPMENT_VISIBLE if config.mode == 'E4_DEVELOPMENT' else OutcomeAccess.EVALUATION_SEALED
        visibility = VisibilityCeiling.DEVELOPMENT_ONLY if config.mode == 'E4_DEVELOPMENT' else VisibilityCeiling.PROSPECTIVE
        if (self.publication.logical.outcome_access is not access
                or self.publication.logical.visibility_ceiling is not visibility
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


def validate_acquisition_wave_summary(programme, result, custody):
    """Join bounded actual collector metadata; this does not authenticate a plan."""
    if (type(custody) is not ScheduledProgrammeAcquisitionWaveCustody or type(result) is not ScheduledProgrammeWaveResult
            or custody.result != result.identity or custody.wave_id != result.wave_id
            or custody.configuration.programme != programme.identity or custody.configuration.bank != programme.bank
            or custody.configuration.wave not in programme.waves
            or custody.configuration.mode != programme.mode
            or result.programme != programme.identity
            or result.root_ids != custody.configuration.wave.root_ids
            or result.group_ids != custody.configuration.wave.group_ids):
        raise ValueError('programme calibration loses actual original wave summary/census/custody')
    cases = tuple(case for case in programme.cases if case.root_id in custody.configuration.wave.root_ids)
    if tuple((case.root_id, case.source, case.independent_group_id) for case in result.cases) != tuple(
            (case.root_id, case.source, case.independent_group_id) for case in cases):
        raise ValueError('acquisition custody substitutes original complete case/source/group identities')
    from .programme_acquisition_bindings import operation_manifests
    manifests = {m.capability_key: m for m in operation_manifests()}
    manifest = manifests[NAMESPACE+'.'+custody.configuration.operation]
    if (custody.producer_task.capability_implementation_sha256 != manifest.implementation_sha256
            or custody.producer_task.capability.config.config_schema_sha256 != manifest.config_schema_sha256):
        raise ValueError('programme calibration substitutes the installed actual collector implementation')
    headers = tuple(r for case in result.cases for r in case.ordinary_receipts)
    if any(type(r) is not ScheduledProgrammeReceiptReference for r in headers):
        raise ValueError('programme runtime calibration requires actual opaque dependency headers')
    roles = acquisition_phase_roles(programme.mode)
    expected_tasks = {COMPACT_NAMESPACE+'.'+root+'.'+role for root in result.root_ids for role in roles}
    if ({r.task_id for r in headers} != expected_tasks or len(headers) != len(expected_tasks)
            or set(custody.producer_task.dependency_task_ids) != expected_tasks | {result.wave_id+'.open'}
            or any(not set(r.output_materialization_ids) & set(custody.receipt.input_materialization_ids) for r in headers)):
        raise ValueError('programme calibration drops actual eleven-stage collector receipt lineage')
    return result


def validate_acquisition_wave_custody(programme, result, custody, plan):
    """Additionally join the complete actual original plan and installed owners."""
    validate_acquisition_wave_summary(programme, result, custody)
    validate_acquisition_plan(programme, custody, plan)
    if (type(plan) not in (CandidateExecutionPlan, ExecutionPlan)
            or ObjectIdentity.from_record(plan.execution_plan_id, plan) != custody.execution_plan
            or tuple(t for t in plan.tasks if t.task_id == custody.producer_task.task_id) != (custody.producer_task,)
            or custody.receipt.implementation_commit != plan.implementation_commit):
        raise ValueError('programme calibration loses actual original complete wave plan/census/custody')
    expected_tasks = {r.task_id for case in result.cases for r in case.ordinary_receipts}
    if {t.task_id for t in plan.tasks} != expected_tasks | {result.wave_id+'.open', result.wave_id+'.collect'}:
        raise ValueError('programme calibration changes complete original398-task wave census')
    from .programme_acquisition_bindings import operation_manifests
    manifests = {m.capability_key: m for m in operation_manifests()}
    for task in plan.tasks:
        role = 'open' if task.task_id == result.wave_id+'.open' else custody.configuration.operation if task.task_id == result.wave_id+'.collect' else task.task_id.rsplit('.', 1)[-1]
        expected = manifests.get(NAMESPACE+'.'+role)
        if (expected is None or task.capability.capability_key != expected.capability_key
                or task.capability.capability_version != expected.capability_version
                or task.capability_implementation_sha256 != expected.implementation_sha256
                or task.capability.config.config_schema_sha256 != expected.config_schema_sha256):
            raise ValueError('programme calibration substitutes an original installed wave phase selection')
    return result


def authenticate_acquisition_wave_custody(plane, binding):
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


def authenticate_acquisition_wave_custody_metadata(plane, binding, *, programme):
    """Authenticate blind original controls and opaque sealed-result metadata.

    No score/result payload is opened or verified. Original plan membership and
    published input pins establish preparation only; permissions and genuine
    execution/reveal remain prerequisites of the actual calibration consumer.
    """
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from hashlib import sha256
    if type(binding) is not ScheduledProgrammeAcquisitionWaveCustody:
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
    validate_acquisition_plan(programme, binding, plan)
    return plan




def validate_acquisition_plan(programme, custody, plan):
    """Validate original full task membership without opening outcome bytes."""
    if (type(custody) is not ScheduledProgrammeAcquisitionWaveCustody
            or custody.configuration.programme != programme.identity or custody.configuration.bank != programme.bank
            or custody.configuration.wave not in programme.waves or custody.configuration.mode != programme.mode
            or type(plan) not in (CandidateExecutionPlan, ExecutionPlan)
            or ObjectIdentity.from_record(plan.execution_plan_id, plan) != custody.execution_plan
            or tuple(t for t in plan.tasks if t.task_id == custody.producer_task.task_id) != (custody.producer_task,)
            or custody.receipt.implementation_commit != plan.implementation_commit):
        raise ValueError('acquisition custody changes exact original full plan/configuration/scope')
    return validate_acquisition_operation_census(programme, custody.configuration.wave, custody.configuration.operation, plan)


def validate_acquisition_operation_census(programme, wave, collector_operation, plan, *, revision_scope=None):
    """Validate original registered phase membership without requiring completion.

    Callers authenticate the actual issued plan and original blind admission /
    collector configuration first. This pure census neither supplies a missing
    collector receipt nor grants protected outcome access.
    """
    from .programme_records import ScheduledProgramme, ScheduledProgrammeWave
    if (type(programme) is not ScheduledProgramme or type(wave) is not ScheduledProgrammeWave or wave not in programme.waves
            or collector_operation != ('collect-development' if programme.mode == 'E4_DEVELOPMENT' else 'collect')
            or type(plan) not in (CandidateExecutionPlan, ExecutionPlan)):
        raise ValueError('acquisition census substitutes original programme wave or complete plan type')
    expected = {COMPACT_NAMESPACE+'.'+root+'.'+role for root in wave.root_ids
        for role in acquisition_phase_roles(programme.mode)}
    if {task.task_id for task in plan.tasks} != expected | {wave.wave_id+'.open', wave.wave_id+'.collect'}:
        raise ValueError('acquisition custody thins complete eleven-stage whole-group task census')
    from .programme_acquisition_bindings import operation_manifests
    manifests = {m.capability_key: m for m in operation_manifests()}
    variants = {}
    if revision_scope is not None:
        from .revision_future_bindings import operation_manifests as revision_manifests
        from .revision_seal_custody import validate_revision_acquisition_variant
        from .revision_calibrated_future_bindings import NAMESPACE as CALIBRATED_NAMESPACE
        calibrated = any(task.capability.capability_key.startswith(CALIBRATED_NAMESPACE + ".") for task in plan.tasks)
        registrations = None
        if calibrated:
            from .revision_calibrated_future_bindings import operation_manifests as revision_manifests, operation_registrations
            if revision_scope.calibration is None:
                raise ValueError('calibrated revision acquisition cannot replace an original calibration wave')
            registrations = operation_registrations()
        validate_revision_acquisition_variant(programme, wave, plan, revision_scope, registrations=registrations)
        variants = {m.capability_key: m for m in revision_manifests()}
    for task in plan.tasks:
        role = 'open' if task.task_id == wave.wave_id+'.open' else collector_operation if task.task_id == wave.wave_id+'.collect' else task.task_id.rsplit('.', 1)[-1]
        manifest = variants.get(task.capability.capability_key) or manifests.get(NAMESPACE+'.'+role)
        if (manifest is None or task.capability.capability_key != manifest.capability_key
                or task.capability.capability_version != manifest.capability_version
                or task.capability_implementation_sha256 != manifest.implementation_sha256
                or task.capability.config.config_schema != manifest.config_schema
                or task.capability.config.config_schema_sha256 != manifest.config_schema_sha256
                or not set(task.capability.required_input_schema_ids) <= set(manifest.input_schema_ids)
                or set(task.capability.required_output_schema_ids) != set(manifest.output_schema_ids)):
            raise ValueError('acquisition custody substitutes actual installed phase/configuration provider contracts')
    return plan
