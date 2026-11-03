# SPDX-License-Identifier: MPL-2.0
"""Selected protected receipt/plan readback using existing custody owners.

This is a cold consumer, not an issue or reveal service. The API integration
must supply its authorized original artifact plane, exact retained plan pin,
original input manifests and chosen receipt locators. No directory scanning,
producer, RNG, contact, source qualification or authority construction occurs.
"""

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.plans import BarrierKind, CandidateExecutionPlan, EnvelopeExecutionPlan, ExecutionPlan, PlanLane, ScientificStage

from . import science
from .commitment import COMMIT_KEY, E1Commitment, E1CommitmentConfig, _authenticate_publications, committed
from .operation_bindings import E1OperationConfig, NAMESPACE, PHASES
from .records import E1FactorAssessment, E1FactorProduct, E1HistorySource, E1NativeHistory, E1NumericalAssessment


def _manifest(plane, relative):
    manifest = decode_artifact_manifest(read_bounded_bytes(plane.root.resolve(relative+'.manifest.json', for_write=False),
        maximum_bytes=plane.custody_limits.manifest_bytes))
    if manifest.materialization.relative_path != relative:
        raise ValueError('E1 retained manifest substitutes selected custody path')
    plane.verify_manifest(manifest)
    return manifest


def _output(plane, receipt, schema):
    rows = tuple((logical, physical) for logical in receipt.output_logical_artifacts
        for physical in receipt.output_materializations if logical.logical_artifact_id == physical.logical_artifact_id
        and logical.payload_schema == schema)
    if len(rows) != 1:
        raise ValueError('E1 retained receipt omits its exact selected scientific output')
    logical, physical = rows[0]
    manifest = _manifest(plane, physical.relative_path)
    if manifest.logical != logical or manifest.materialization != physical:
        raise ValueError('E1 output manifest differs from original completion receipt')
    return read_bounded_bytes(plane.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)


def _selected_receipt(plane, store, plan, task, attempt, access):
    receipt = store.read(plan.source_plan.object_id, task.task_id, attempt)
    if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or receipt.implementation_commit != plan.implementation_commit
            or task.capability.requested_outcome_access is not access):
        raise ValueError('E1 original protected operation has no exact successful selected plan/receipt')
    actual = {a.logical_artifact_id: a for a in receipt.output_logical_artifacts}
    if (set(actual) != {o.logical_artifact_id for o in task.outputs}
            or any((actual[o.logical_artifact_id].payload_schema, actual[o.logical_artifact_id].profile, actual[o.logical_artifact_id].media_type,
                    actual[o.logical_artifact_id].outcome_access, actual[o.logical_artifact_id].visibility_ceiling)
                   != (o.payload_schema, o.profile, o.media_type, o.outcome_access, o.visibility_ceiling) for o in task.outputs)
            or {p.logical_artifact_id: p.relative_path for p in receipt.output_materializations}
               != {o.logical_artifact_id: o.relative_path for o in task.outputs}
            or any(o.outcome_access is not access or o.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE for o in task.outputs)):
        raise ValueError('E1 original receipt changes complete protected planned output census')
    limit = task.capability.requested_resources.output_bytes
    if limit is not None and sum(p.size_bytes for p in receipt.output_materializations) > limit:
        raise ValueError('E1 original receipt exceeds explicitly selected finite output budget')
    return receipt


def read_root(*, plane, run_id, execution_plan, source, original_inputs, receipt_locators,
              commitment_attempt_id, commitment_inputs):
    """Authenticate the whole original root inside one effect-free read lifetime."""
    with plane.read_context() as reading:
        return _read_root(plane=reading, run_id=run_id, execution_plan=execution_plan,
            source=source, original_inputs=original_inputs, receipt_locators=receipt_locators,
            commitment_attempt_id=commitment_attempt_id, commitment_inputs=commitment_inputs)


def _read_root(*, plane, run_id, execution_plan, source, original_inputs, receipt_locators,
               commitment_attempt_id, commitment_inputs):
    """Read exact protected original outputs; no execution or reveal authority.

    `receipt_locators` contains the four explicit `(phase, attempt_id)` pairs.
    The pure commitment's attempt and original input manifests are separate
    exact selections. The caller retains failed/unknown roots separately;
    this successful-product reader never infers missing science or replays it.
    """
    validate_stable_id(run_id)
    if (type(source) is not E1HistorySource or type(execution_plan) is not ObjectIdentity
            or tuple(role for role, _ in receipt_locators) != tuple(p[0] for p in PHASES)
            or any(type(m) is not ArtifactManifest for m in (*original_inputs, *commitment_inputs))):
        raise ValueError('E1 cold reader requires exact selected source/plan/input/phase locators')
    relative = 'runs/'+run_id+'/plans/execution-plan.json'
    manifest = _manifest(plane, relative)
    types = {t.SCHEMA: t for t in (CandidateExecutionPlan, EnvelopeExecutionPlan, ExecutionPlan)}
    cls = types.get(manifest.logical.payload_schema)
    if cls is None or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON:
        raise ValueError('E1 cold reader refuses nonprospective retained plans')
    plan = decode_canonical_bytes(read_bounded_bytes(plane.root.resolve(relative, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes), cls, maximum_bytes=None)
    if (ObjectIdentity.from_record(plan.execution_plan_id, plan) != execution_plan
            or plan.implementation_commit != source.provenance.observed_git_head
            or plan.lane is not PlanLane.PROSPECTIVE or plan.source_plan.object_id != run_id):
        raise ValueError('E1 cold reader changes original selected source/plan/implementation')
    tasks = {t.task_id: t for t in plan.tasks}
    receipts, records = [], {}
    store = ExternalTaskReceiptStore(plane)
    commit_task = tasks.get(COMMIT_KEY)
    if (commit_task is None or commit_task.capability.capability_key != COMMIT_KEY
            or commit_task.stage is not ScientificStage.FREEZE or commit_task.barrier is not BarrierKind.FREEZE
            or commit_task.dependency_task_ids):
        raise ValueError('E1 cold reader lacks its pure prior protected commitment task')
    commit_receipt = _selected_receipt(plane, store, plan, commit_task, commitment_attempt_id, OutcomeAccess.OUTCOME_BLIND)
    commitment = decode_canonical_bytes(_output(plane, commit_receipt, E1Commitment.SCHEMA), E1Commitment, maximum_bytes=None)
    for original in commitment_inputs:
        plane.verify_manifest(original)
    if (tuple(sorted(m.materialization.materialization_id for m in commitment_inputs)) != commit_receipt.input_materialization_ids
            or len(set(commit_receipt.input_materialization_ids)) != len(commitment_inputs)):
        raise ValueError('E1 pure commitment omits its original complete source input materializations')
    for spec in commit_task.external_inputs:
        matches = tuple(m for m in commitment_inputs if m.logical.logical_artifact_id == spec.logical_artifact_id)
        if (len(matches) != 1 or matches[0].logical.content_sha256 != spec.expected_content_sha256
                or matches[0].logical.payload_schema != spec.expected_payload_schema
                or matches[0].logical.media_type != spec.expected_media_type
                or matches[0].logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or matches[0].logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('E1 pure commitment changes exact original selected source descriptors')
    selected = tuple(m for m in commitment_inputs if m.logical.payload_schema == E1CommitmentConfig.SCHEMA)
    if len(selected) != 1:
        raise ValueError('E1 pure commitment omits original exact configuration custody')
    config_manifest = selected[0]
    config = decode_canonical_bytes(read_bounded_bytes(plane.root.resolve(config_manifest.materialization.relative_path, for_write=False),
        maximum_bytes=config_manifest.materialization.size_bytes), E1CommitmentConfig, maximum_bytes=None)
    _authenticate_publications(plane, config)
    expected_records = (config, config.sources[0].allocation, config.sources[0].specification.selection, *config.sources)
    if (commitment != committed(config) or commit_task.capability.config.content_sha256 != config.fingerprint()
            or commit_task.capability.config.artifact_id != config_manifest.logical.logical_artifact_id
            or len(commitment_inputs) != len(expected_records)):
        raise ValueError('E1 pure commitment changes complete original config/source closure')
    for record in expected_records:
        matches = tuple(m for m in commitment_inputs if m.logical.payload_schema == record.SCHEMA
            and m.logical.content_sha256 == record.fingerprint())
        if (len(matches) != 1 or matches[0].logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or matches[0].logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('E1 pure commitment loses exact original prior-publication source bytes')
    for publication in (commitment.reservation.publication, commitment.specification.publication):
        if not any(m.logical.logical_artifact_id == publication.logical.logical_artifact_id
                and m.logical.payload_schema == publication.logical.payload_schema
                and m.logical.media_type == publication.logical.media_type
                and m.logical.content_sha256 == publication.logical.content_sha256
                and m.materialization.physical_sha256 == publication.materialization.physical_sha256
                and m.materialization.size_bytes == publication.materialization.size_bytes
                and m.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND
                and m.logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE for m in commitment_inputs):
            raise ValueError('E1 pure commitment substitutes original allocation or selection publication')
    commitment.validate_source(source)
    for (role, attempt), (_, _, output, _) in zip(receipt_locators, PHASES, strict=True):
        task_id = NAMESPACE+'.'+source.root_id+'.'+role
        task = tasks.get(task_id)
        if (task is None or task.capability.capability_key != NAMESPACE+'.'+role
                or task.capability.requested_outcome_access is not OutcomeAccess.EVALUATION_SEALED):
            raise ValueError('E1 original protected operation has no exact successful selected plan/receipt')
        receipt = _selected_receipt(plane, store, plan, task, attempt, OutcomeAccess.EVALUATION_SEALED)
        receipts.append(receipt)
        records[output] = decode_canonical_bytes(_output(plane, receipt, output.SCHEMA), output, maximum_bytes=None)
    history = records[E1NativeHistory]
    history.validate_source(source)
    parent = history.native.definition.parent_contact
    task = tasks[NAMESPACE+'.'+source.root_id+'.history']
    committed_inputs = tuple(m for m in original_inputs if m.logical.payload_schema == E1Commitment.SCHEMA)
    if (COMMIT_KEY not in task.dependency_task_ids or len(committed_inputs) != 1
            or committed_inputs[0].logical not in commit_receipt.output_logical_artifacts
            or committed_inputs[0].materialization not in commit_receipt.output_materializations):
        raise ValueError('E1 native parent lacks its exact original commitment dependency materialization')
    if (parent.run_id != run_id or parent.execution_plan != execution_plan
            or parent.execution_task != ObjectIdentity.from_record(task.task_id, task)
            or parent.attempt_id != receipts[0].attempt_id):
        raise ValueError('E1 original native contact changes exact issued plan/task/attempt')
    for original in original_inputs:
        plane.verify_manifest(original)
    if (tuple(sorted(m.materialization.materialization_id for m in original_inputs)) != parent.input_materialization_ids
            or len(set(parent.input_materialization_ids)) != len(original_inputs)):
        raise ValueError('E1 original native contact omits full selected input materializations')
    for spec in task.external_inputs:
        matches = tuple(m for m in original_inputs if m.logical.logical_artifact_id == spec.logical_artifact_id)
        if (len(matches) != 1 or matches[0].logical.content_sha256 != spec.expected_content_sha256
                or spec.expected_outcome_access is not None and matches[0].logical.outcome_access is not spec.expected_outcome_access
                or spec.expected_visibility_ceiling is not None and matches[0].logical.visibility_ceiling is not spec.expected_visibility_ceiling):
            raise ValueError('E1 original native custody changes exact frozen external input contracts')
    config = E1OperationConfig('config.'+task.task_id, 'history', source)
    for record in (source, config):
        selected = tuple(m for m in original_inputs if m.logical.payload_schema == record.SCHEMA
            and m.logical.content_sha256 == record.fingerprint())
        if len(selected) != 1 or selected[0].logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError('E1 native custody changes original exact selected source/configuration bytes')
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=execution_plan,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.EVALUATION_SEALED)
    if contacts.read(run_id, task.task_id) != parent:
        raise ValueError('E1 cold reader lacks original exact entered parent custody')
    native = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=original_inputs)
    roster = native.read_roster(parent)
    if roster is None or roster.subworks != (history.native.definition.identity,):
        raise ValueError('E1 cold reader thins original full paired-history native roster')
    completed = native.inspect(history.native.definition)
    if (completed.state is not NativeSubworkState.COMPLETED
            or completed.completion != history.native.completion or completed.receipt != history.native.receipt):
        raise ValueError('E1 cold reader substitutes original nested completion/receipt')
    native_raw = _output(plane, receipts[0], history.arrays.array_artifact.payload_schema)
    diagnostic_raw = _output(plane, receipts[2], records[E1FactorProduct].arrays.array_artifact.payload_schema)
    product, assessment = science.read_retained(source, history, records[E1NumericalAssessment], records[E1FactorProduct],
        records[E1FactorAssessment], native_raw, diagnostic_raw, receipts=tuple(receipts))
    return history, records[E1NumericalAssessment], product, assessment
