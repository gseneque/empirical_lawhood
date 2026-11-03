"""Current issued-plan and complete receipt joins before scientific output reads."""

from dataclasses import fields
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal

from .codecs import MAX_CAMPAIGN_PACKAGE_BYTES, loads_campaign_package_authoring
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _ScopedArtifactPlane, _has_stock_manifest_reads
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError, MAX_ARTIFACT_MANIFEST_BYTES, read_bounded_bytes
from empirical_lawhood.infrastructure.execution_resource_envelopes import read_execution_launch_event
from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID, PROGRAMME_EXECUTION_GRANTEE_ID, PROGRAMME_REVEAL_GRANTEE_ID
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decimal_context_key, decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.study_issue import StudyAuthorityKind, require_study_authority
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity, derived_outcome_access, lineage_parent_sort_key
from empirical_lawhood.runtime.plans import ExecutionPlan, PlanLane, RunPlan, ScientificStage
from empirical_lawhood.runtime.providers import CapabilityOutputSemanticContract, capability_semantic_validation_registry
from empirical_lawhood.runtime.scientific_graph_preservation import _validate_execution_plan, _validate_run_plan

def retained_output_artifact_plane(package, plan, writer, output_codecs):
    """Bind installed record shapes to the original stored output ownership.

    This consumes an authenticated retained plan and registry, without selecting
    current executable providers or compiling a replacement scientific graph.
    Sidecar claims never supply their own trusted validator registration.
    """
    contracts = {}
    for task in plan.tasks:
        manifest = package.registry.resolve(task.capability.capability_key, task.capability.capability_version)
        for output in task.outputs:
            if output.profile is not ArtifactProfile.CANONICAL_JSON:
                contract = CapabilityOutputSemanticContract.from_manifest(manifest,
                    payload_schema=output.payload_schema, profile=output.profile)
            else:
                record_type = output_codecs.get(output.payload_schema)
                if record_type is None or record_type.SCHEMA != output.payload_schema:
                    raise PermissionError('qualified parent output lacks its installed typed scientific codec')
                contract = CapabilityOutputSemanticContract.from_manifest(manifest,
                    payload_schema=output.payload_schema, profile=output.profile,
                    top_level_keys=('schema', 'value', 'version'),
                    value_keys=tuple(sorted(field.name for field in fields(record_type))), record_version=record_type.VERSION)
            if contracts.setdefault(contract.key, contract) != contract:
                raise PermissionError('retained outputs disagree on one immutable semantic contract')
    return writer.with_semantic_validation_registry(capability_semantic_validation_registry(
        registry_id=f'qualified-parent-semantics.{plan.execution_plan_id}', plan=plan, contracts=tuple(contracts.values())))


def _authenticate_protected_current_result(*, issued_study: ObjectIdentity,
        execution_authority: ObjectIdentity, reveal_authority: ObjectIdentity,
        receipt: CanonicalTaskReceipt, logical: LogicalArtifactIdentity,
        writer: ExternalArtifactPlane, family: Literal['rc', 'preparation']
        ) -> tuple[ExecutionPlan, ExperimentPackage]:
    """Join retained execution facts and genuine current reveal at access.

    Family wrappers own protected-role selection, their context/run checks and
    public return values. These two closed adaptations preserve their refusal
    codes while keeping the actual authentication sequence in one owner.
    """
    if family == 'rc':
        prefixes = ('simulator-morphism-challenges.',)
        codes = ('RC_RESULT_CURRENT_PACKAGE_REQUIRED', 'RC_RESULT_ISSUED_RUN_IDENTITY_MISMATCH',
                 'RC_RESULT_AUTHORITY_IDENTITY_MISMATCH', 'RC_RESULT_CURRENT_ISSUED_SOURCE_MISMATCH',
                 'RC_RESULT_CURRENT_ISSUED_TASK_OUTPUT_MISMATCH')
    elif family == 'preparation':
        prefixes = ('preparation-applicability.', 'constructed-preparation-applicability.')
        codes = ('PREPARATION_RESULT_CURRENT_PACKAGE_REQUIRED', 'PREPARATION_RESULT_ISSUED_RUN_IDENTITY_MISMATCH',
                 'PREPARATION_RESULT_STORED_GRANT_MISMATCH', 'PREPARATION_RESULT_CURRENT_ISSUED_SOURCE_MISMATCH',
                 'PREPARATION_RESULT_ISSUED_TASK_OUTPUT_MISMATCH')
    else:
        raise ValueError('Unsupported protected current result family')
    relative = f'runs/{receipt.run_id}/plans/campaign-package.json'
    manifest = decode_artifact_manifest(read_bounded_bytes(writer.root.resolve(relative + '.manifest.json', for_write=False),
        maximum_bytes=MAX_ARTIFACT_MANIFEST_BYTES))
    if (manifest.materialization.relative_path != relative
        or manifest.materialization.size_bytes > MAX_CAMPAIGN_PACKAGE_BYTES
        or manifest.logical.logical_artifact_id != f'campaign-package.{receipt.run_id}'
        or manifest.logical.payload_schema != ExperimentPackage.SCHEMA
        or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
        or manifest.logical.media_type != 'application/json'):
        raise PermissionError(codes[0])
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    package = loads_campaign_package_authoring(raw.decode('utf-8'), media_type='application/json')
    if (type(package) is not ExperimentPackage
        or package.run_plan_id != receipt.run_id or not package.canonical_equals(raw)
        or package.SCHEMA != manifest.logical.payload_schema
        or package.fingerprint() != manifest.logical.content_sha256
        or ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study) != issued_study
        or ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority) != execution_authority):
        raise PermissionError(codes[1])
    store = ExternalStudyOperationAuthorityStore(writer)
    published = ExternalIssuedStudyPublisher(artifact_plane=writer, authority_store=store,
        grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(issued_study.object_id)
    issued = published.manifest
    if (issued != package.issued_study or published.publication_receipt != package.publication_receipt
        or issued.source_closure.implementation_commit != receipt.implementation_commit):
        raise PermissionError(codes[3])
    steps = {step.step_id: step for step in issued.candidate.base_candidate.base_candidate.protocol.steps}
    step = steps.get(receipt.task_id)
    if (step is None or not step.capability_key.startswith(prefixes)
        or not any(f'artifact.{receipt.run_id}.{step.step_id}.{output.output_id}' == logical.logical_artifact_id
                   and output.payload_schema == logical.payload_schema for output in step.outputs)):
        raise PermissionError(codes[4])
    plan = authenticate_current_result_plan_outputs(package=package, issued=issued, receipt=receipt,
        logical=logical, writer=writer, capability_prefixes=prefixes)
    require_current_result_reveal_authority(writer=writer, package=package,
        reveal_authority_id=reveal_authority.object_id, expected_identity=reveal_authority)
    return plan, package


def current_result_package_present(*, writer, run_id):
    """Inspect only the exact selected public control pair, without payload I/O."""
    if not isinstance(writer, ExternalArtifactPlane):
        return False
    relative = f'runs/{run_id}/plans/campaign-package.json'
    return any(writer.root.resolve(path, for_write=False).exists()
               or writer.root.resolve(path, for_write=False).is_symlink()
               for path in (relative, relative + '.manifest.json'))


def _current_control(*, writer, run_id, name, record_type, maximum_bytes, control_reader=None,
                     expected_lineage=None, include_manifest=False):
    relative = f'runs/{run_id}/plans/{name}.json'
    manifest = writer.read_manifest(relative, maximum_bytes=MAX_ARTIFACT_MANIFEST_BYTES)
    if (manifest.materialization.relative_path != relative
        or manifest.materialization.storage_root_id != writer.root.contract.storage_root_id
        or (maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes)
        or writer.custody_limits.exceeds("in_memory_payload_bytes", manifest.materialization.size_bytes)
        or manifest.materialization.compression != 'none'
        or manifest.materialization.partition_selector is not None
        or manifest.logical.logical_artifact_id != f'{name}.{run_id}'
        or manifest.logical.payload_schema != record_type.SCHEMA
        or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
        or manifest.logical.media_type != 'application/json'):
        raise PermissionError('CURRENT_RESULT_EXACT_PUBLISHED_CONTROL_REQUIRED')
    if expected_lineage is not None:
        publication = manifest.publication
        if (publication is None or manifest.logical.lineage_parents != expected_lineage
                or publication.publication_scope.publication_scope_id != f'campaign-plans.{run_id}'
                or publication.publication_scope.relative_root != f'runs/{run_id}/plans'
                or publication.publication_scope.storage_root_id != writer.root.contract.storage_root_id):
            raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_PUBLICATION_BINDING_MISMATCH')
    if control_reader is not None:
        if control_reader.writer is not writer:
            raise PermissionError('CURRENT_RESULT_CONTROL_READER_WRITER_MISMATCH')
        record = control_reader.read_control(manifest, record_type, manifest.materialization.size_bytes)
    else:
        writer.verify_manifest(manifest)
        size = manifest.materialization.size_bytes
        raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=size)
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=size)
        if (not record.canonical_equals(raw)
            or len(raw) != manifest.materialization.size_bytes
            or record.fingerprint() != manifest.logical.content_sha256
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
            raise PermissionError('CURRENT_RESULT_PUBLISHED_CONTROL_BYTES_MISMATCH')
    return (record, manifest) if include_manifest else record


def require_current_result_receipt_outputs(*, receipt, logical, execution_plan, capability_prefixes,
                                          control_reader=None):
    """Compare the complete output census with the actual typed execution task."""
    if control_reader is None:
        tasks = tuple(task for task in execution_plan.tasks if task.task_id == receipt.task_id)
    else:
        if type(control_reader) is not CurrentResultPlanReader:
            raise TypeError('current result task lookup requires its exact scoped plan reader')
        selected = control_reader.execution_task(execution_plan=execution_plan, task_id=receipt.task_id)
        tasks = () if selected is None else (selected,)
    if len(tasks) != 1:
        raise PermissionError('CURRENT_RESULT_EXECUTION_TASK_MISMATCH')
    return _require_current_task_receipt_outputs(receipt=receipt, logical=logical,
        execution_plan=execution_plan, task=tasks[0], capability_prefixes=capability_prefixes)


def _require_current_task_receipt_outputs(*, receipt, logical, execution_plan, task,
                                         capability_prefixes):
    """Check one task selected by the owning authenticated plan lookup.

    The public selector and scoped readers derive that lookup from the same
    exact plan. This pure comparison caches neither controls nor authority.
    """
    expected_commit = execution_plan.implementation_commit
    if (task.task_id != receipt.task_id or receipt.run_id != execution_plan.source_plan.object_id
        or receipt.implementation_commit != expected_commit):
        raise PermissionError('CURRENT_RESULT_EXECUTION_TASK_MISMATCH')
    if not task.capability.capability_key.startswith(capability_prefixes):
        raise PermissionError('CURRENT_RESULT_EXECUTION_CAPABILITY_MISMATCH')
    expected = {output.logical_artifact_id: output for output in task.outputs}
    actual = {output.logical_artifact_id: output for output in receipt.output_logical_artifacts}
    physical = {output.logical_artifact_id: output for output in receipt.output_materializations}
    if (set(expected) != set(actual) or set(expected) != set(physical)
        or len(actual) != len(receipt.output_logical_artifacts)
        or len(physical) != len(receipt.output_materializations)
        or actual.get(logical.logical_artifact_id) != logical):
        raise PermissionError('CURRENT_RESULT_COMPLETE_EXECUTION_OUTPUT_CENSUS_REQUIRED')
    for artifact_id, output in expected.items():
        observed = actual[artifact_id]
        materialization = physical[artifact_id]
        # Concrete lineage records include resolved config/dependency parents
        # in identity order. Their validated tuple need not equal the compiler's
        # edge-ceiling tuple; exact frozen visibility and access still apply.
        if ((observed.payload_schema, observed.profile, observed.media_type,
             observed.visibility_ceiling, observed.outcome_access,
             materialization.relative_path)
            != (output.payload_schema, output.profile, output.media_type,
                output.visibility_ceiling, output.outcome_access,
                output.relative_path)
            or materialization.compression != 'none' or materialization.partition_selector is not None):
            raise PermissionError('CURRENT_RESULT_EXECUTION_OUTPUT_CONTRACT_MISMATCH')
    output_limit = task.capability.requested_resources.output_bytes
    if output_limit is not None and sum(value.size_bytes for value in physical.values()) > output_limit:
        raise PermissionError('CURRENT_RESULT_EXECUTION_OUTPUT_BYTE_BUDGET_EXCEEDED')
    return task


def _require_prepared_plan_bindings(*, package, issued, run_plan, execution_plan):
    """Check stored contracts against issued science without constructing plans.

    The artifact publisher owns the immutable preparation-time byte seals. These
    independent field checks bind their contents to the actual issued candidate,
    approval, source, registry and task contracts; they select no provider and
    create no replacement graph, access grant or scientific assessment.
    """
    candidate = issued.candidate
    base = candidate.base_candidate.base_candidate
    candidate_pin = ObjectIdentity.from_record(candidate.candidate_id, candidate)
    extension_pin = ObjectIdentity.from_record(issued.issued_extensions.issued_extension_set_id,
        issued.issued_extensions)
    expected_model = None if package.model_set is None else ObjectIdentity.from_record(
        package.model_set.model_set_id, package.model_set)
    if (run_plan.candidate != candidate_pin or execution_plan.candidate != candidate_pin
            or run_plan.issued_extension_set != extension_pin or execution_plan.issued_extension_set != extension_pin
            or run_plan.implementation_commit != issued.source_closure.implementation_commit
            or run_plan.model_set != expected_model or execution_plan.lane is not PlanLane.PROSPECTIVE
            or run_plan.numerical_view_ids != tuple(sorted({view_id for claim in package.experiment.claims
                for view_id in claim.numerical_view_ids}))):
        raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_ISSUED_BINDING_MISMATCH')
    attributes = ('execution_resource_envelope_spec', 'predevelopment_jit_signature_census',
        'jit_graph_signature_manifest') if type(package) is ExperimentPackage else ('execution_envelope_spec',)
    identity_attributes = {'execution_resource_envelope_spec': 'envelope_spec_id',
        'execution_envelope_spec': 'envelope_spec_id', 'predevelopment_jit_signature_census': 'census_id',
        'jit_graph_signature_manifest': 'manifest_id'}
    for name in attributes:
        value = getattr(package, name)
        expected = None if value is None else ObjectIdentity.from_record(getattr(value, identity_attributes[name]), value)
        if getattr(run_plan, name) != expected or getattr(execution_plan, name) != expected:
            raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_RESOURCE_BINDING_MISMATCH')
    try:
        _validate_run_plan(candidate=base, authorized_experiment=package.experiment,
            scientific_approval=ObjectIdentity.from_record(package.scientific_approval.authorization_id,
                package.scientific_approval), run_plan=run_plan, registry=package.registry)
        _validate_execution_plan(run_plan=run_plan, execution_plan=execution_plan, registry=package.registry)
    except (KeyError, ValueError) as error:
        raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_CONTRACT_MISMATCH') from error
    # Output locators and nonconsumed outputs also belong to the issued protocol;
    # agreement between a substituted run/task pair is insufficient.
    templates = {step.step_id: step for step in base.protocol.steps}
    for step in run_plan.steps:
        template = templates[step.step_id]
        manifest = package.registry.resolve(template.capability_key, template.capability_version)
        if (step.capability.kind is not manifest.kind
                or step.capability.required_input_schema_ids != tuple(sorted({edge.payload_schema for edge in step.scientific_inputs}))
                or step.capability.required_output_schema_ids != tuple(sorted({output.payload_schema for output in template.outputs}))
                or step.capability.requested_evidence_ceiling is not EvidenceCeiling.lowest(
                    *(claim.evidence_ceiling for claim in package.experiment.claims), manifest.maximum_evidence_ceiling)):
            raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_CAPABILITY_CONTRACT_MISMATCH')
        parents = tuple(sorted((edge.visibility_ceiling for edge in step.scientific_inputs), key=lambda value: value.value))
        evaluator_only = (template.stage is ScientificStage.EVALUATE
            and template.requested_outcome_access is OutcomeAccess.EVALUATOR_REVEAL
            and template.visibility_ceiling is VisibilityCeiling.PROSPECTIVE)
        declared_access = (OutcomeAccess.EVALUATION_REVEALED
            if template.stage in (ScientificStage.EVALUATE, ScientificStage.REVEAL) and not evaluator_only
            else template.requested_outcome_access)
        access = derived_outcome_access(declared_access, *(edge.outcome_access for edge in step.scientific_inputs))
        visibility = VisibilityCeiling.most_restrictive(template.visibility_ceiling, inherited_visibility(parents, access))
        expected = tuple((f'{step.step_id}.{output.output_id}',
            f'artifact.{run_plan.run_plan_id}.{step.step_id}.{output.output_id}',
            f'runs/{run_plan.run_plan_id}/outputs/{step.step_id}/{output.output_id}{output.filename_suffix}',
            output.payload_schema, output.profile, output.media_type,
            derived_outcome_access(OutcomeAccess.EVALUATION_REVEALED, access)
                if evaluator_only and output.payload_schema == ScientificAdjudicationRecord.SCHEMA else access,
            VisibilityCeiling.most_restrictive(visibility, VisibilityCeiling.OUTCOME_VISIBLE)
                if evaluator_only and output.payload_schema == ScientificAdjudicationRecord.SCHEMA else visibility,
            parents) for output in template.outputs)
        observed = tuple((output.output_id, output.logical_artifact_id, output.relative_path,
            output.payload_schema, output.profile, output.media_type, output.outcome_access,
            output.visibility_ceiling, output.parent_visibility_ceilings) for output in step.outputs)
        if observed != expected:
            raise PermissionError('CURRENT_RESULT_PREPARED_PLAN_OUTPUT_CONTRACT_MISMATCH')


def authenticate_current_execution_plan(*, package, issued, run_id, writer, control_reader=None):
    """Authenticate immutable prepared plans; create no access or task authority.

    These are preparation-time artifact publication seals, not issue-time plan
    digests. The guarded publisher refuses replacement under their original
    identities and paths. Routine reads validate the stored contracts rather
    than importing a producing compiler or reconstructing executable providers.
    """
    if not isinstance(writer, ExternalArtifactPlane) or package.issued_study != issued:
        raise PermissionError('CURRENT_RESULT_ISSUED_PACKAGE_REQUIRED')
    if type(package) is not ExperimentPackage:
        raise PermissionError('CURRENT_RESULT_UNSUPPORTED_PACKAGE')
    stored_package, package_manifest = _current_control(writer=writer, run_id=run_id, name='campaign-package',
        record_type=type(package), maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES, control_reader=control_reader,
        include_manifest=True)
    if stored_package != package:
        raise PermissionError('CURRENT_RESULT_EXACT_PREPARED_PACKAGE_REQUIRED')
    package_parent = ArtifactLineageParent(ObjectIdentity.from_record(package.package_id, package),
        package_manifest.logical.visibility_ceiling, package_manifest.logical.outcome_access)
    run = _current_control(writer=writer, run_id=run_id, name='run-plan',
        record_type=RunPlan, maximum_bytes=writer.custody_limits.control_record_bytes, control_reader=control_reader,
        expected_lineage=(package_parent,))
    run_parent = ArtifactLineageParent(ObjectIdentity.from_record(run.run_plan_id, run),
        package_parent.visibility_ceiling, package_parent.outcome_access)
    execution = _current_control(writer=writer, run_id=run_id, name='execution-plan',
        record_type=ExecutionPlan, maximum_bytes=writer.custody_limits.control_record_bytes, control_reader=control_reader,
        expected_lineage=tuple(sorted((package_parent, run_parent), key=lineage_parent_sort_key)))
    if (package.run_plan_id != run_id or run.run_plan_id != run_id
        or execution.execution_plan_id != package.execution_plan_id
        or execution.source_plan != ObjectIdentity.from_record(run.run_plan_id, run)):
        raise PermissionError('CURRENT_RESULT_PACKAGE_PLAN_JOIN_MISMATCH')
    _require_prepared_plan_bindings(package=package, issued=issued, run_plan=run, execution_plan=execution)
    return execution


def authenticate_current_result_plan_outputs(*, package, issued, receipt, logical, writer, capability_prefixes):
    """Join exact stored result custody with the sealed prepared plan contracts."""
    execution = authenticate_current_execution_plan(package=package, issued=issued,
        run_id=receipt.run_id, writer=writer)
    _require_current_stored_result(receipt=receipt, logical=logical, execution=execution,
        writer=writer, capability_prefixes=capability_prefixes)
    authenticate_historical_execution_authority(package=package, execution_plan=execution,
        receipt=receipt, writer=writer)
    return execution


def authenticate_historical_execution_authority(*, package, execution_plan, receipt, writer):
    """Validate retained execution authority at the committed task dispatch.

    The caller first authenticates the original issued package, prepared plan
    and actual stored receipt. This bounded join grants no current outcome
    access. LAUNCH precedes worker preflight/BEGIN and native contact; this
    check proves neither native entry-time permission nor native completion.
    """
    if (type(package) is not ExperimentPackage or type(execution_plan) is not ExecutionPlan
            or type(receipt) is not CanonicalTaskReceipt
            or receipt.run_id != package.run_plan_id
            or execution_plan.execution_plan_id != package.execution_plan_id
            or receipt.implementation_commit != execution_plan.implementation_commit
            or receipt.implementation_commit != package.issued_study.source_closure.implementation_commit):
        raise PermissionError('CURRENT_RESULT_EXACT_HISTORICAL_EXECUTION_REQUIRED')
    return authenticate_task_dispatch_authority(package=package, execution_plan=execution_plan,
        run_id=receipt.run_id, task_id=receipt.task_id, attempt_id=receipt.attempt_id, writer=writer)


def authenticate_task_dispatch_authority(*, package, execution_plan, run_id, task_id, attempt_id, writer):
    """Authenticate an exact original task dispatch without inventing a receipt.

    This also supports retained unknown native contacts. The actual LAUNCH is
    a dispatch fact only; it supplies no native-entry timestamp or new entry
    permission. The caller authenticates the original issued plan and contact.
    """
    if (type(package) is not ExperimentPackage or type(execution_plan) is not ExecutionPlan
            or run_id != package.run_plan_id or execution_plan.execution_plan_id != package.execution_plan_id
            or execution_plan.implementation_commit != package.issued_study.source_closure.implementation_commit):
        raise PermissionError('CURRENT_RESULT_EXACT_HISTORICAL_EXECUTION_REQUIRED')
    event = read_execution_launch_event(artifact_plane=writer, execution_plan=execution_plan,
        resource_spec=package.execution_resource_envelope_spec, run_id=run_id,
        task_id=task_id, attempt_id=attempt_id)
    execution = ExternalStudyOperationAuthorityStore(writer).load(package.execution_authority.authority_id)
    if execution != package.execution_authority:
        raise PermissionError('CURRENT_RESULT_EXACT_STORED_EXECUTION_AUTHORITY_REQUIRED')
    require_study_authority(execution, kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
        subject=ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
        prerequisite_authority=ObjectIdentity.from_record(package.scientific_approval.authorization_id,
            package.scientific_approval), grantee_id=PROGRAMME_EXECUTION_GRANTEE_ID,
        at_utc=event.occurred_at_utc)
    return event


def require_current_result_reveal_authority(*, writer, package, reveal_authority_id, expected_identity=None):
    """Reload genuine access authority and check its clock at this boundary."""
    if reveal_authority_id is None:
        raise PermissionError('CURRENT_RESULT_REVEAL_AUTHORITY_REQUIRED')
    from .selected_e3_access import _current_authority_reader
    authority_reader = _current_authority_reader(writer)
    if authority_reader is not None:
        writer = authority_reader
    elif type(writer) is _ScopedArtifactPlane and _has_stock_manifest_reads(writer):
        writer = ExternalArtifactPlane(writer.root, writer.validators, writer.semantic_validations,
            custody_limits=writer.custody_limits, artifact_verification='strict')
    # An existing operation-local authority reader already owns this exact
    # immutable grant closure. Keep it rather than creating a new census for
    # every body; the stored grant bytes and current UTC are still checked here.
    scope = writer.read_context() if authority_reader is not None else writer.verification_scope()
    with scope as grant_writer:
        reveal = ExternalStudyOperationAuthorityStore(grant_writer).load(reveal_authority_id)
        if (reveal.authority_id != reveal_authority_id or expected_identity is not None
                and ObjectIdentity.from_record(reveal.authority_id, reveal) != expected_identity):
            raise PermissionError('CURRENT_RESULT_EXACT_STORED_REVEAL_AUTHORITY_REQUIRED')
        grant_writer.require_verification_snapshot()
    require_study_authority(reveal, kind=StudyAuthorityKind.OUTCOME_REVEAL,
        subject=ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
        prerequisite_authority=ObjectIdentity.from_record(package.execution_authority.authority_id,
            package.execution_authority), grantee_id=PROGRAMME_REVEAL_GRANTEE_ID,
        at_utc=datetime.now(UTC).isoformat().replace('+00:00', 'Z'))
    return reveal


def _require_current_stored_result(*, receipt, logical, execution, writer, capability_prefixes,
                                   control_reader=None):
    if control_reader is not None and (type(control_reader) is not CurrentResultPlanReader
            or control_reader.writer.root is not writer.root):
        raise PermissionError('CURRENT_RESULT_CONTROL_READER_WRITER_MISMATCH')
    require_current_result_receipt_outputs(receipt=receipt, logical=logical,
        execution_plan=execution, capability_prefixes=capability_prefixes, control_reader=control_reader)
    if ExternalTaskReceiptStore(writer).read_by_receipt_id(receipt.run_id, receipt.task_id, receipt.receipt_id) != receipt:
        raise PermissionError('CURRENT_RESULT_EXACT_STORED_RECEIPT_REQUIRED')
    if any(value.storage_root_id != writer.root.contract.storage_root_id for value in receipt.output_materializations):
        raise PermissionError('CURRENT_RESULT_OUTPUT_STORAGE_ROOT_MISMATCH')


def _index_execution_tasks(plan):
    tasks = {task.task_id: task for task in plan.tasks}
    if len(tasks) != len(plan.tasks):
        raise PermissionError('CURRENT_RESULT_EXECUTION_TASK_MISMATCH')
    return tasks


class CurrentResultPlanReader:
    """Reuse authenticated prepared plans within the explicit read lifetime.

    The caller still establishes current reveal authority for protected use.
    Every supplied receipt and complete output contract is checked
    against actual retained custody. The explicit read context closes mutation
    checks at its public/effect boundaries; ordinary verification scopes remain
    eager. An expired lifetime cannot reuse any projection.
    """

    def __init__(self, writer):
        if not isinstance(writer, ExternalArtifactPlane):
            raise TypeError('current result plan reader requires guarded artifact custody')
        writer.require_verification_context()
        self.writer = writer
        self._plans = {}
        self._task_indexes = {}
        self._recovery_indexes = {}
        self._execution_history = {}
        self._output_writers = {}
        self._controls = {}
        self._receipt_closures = {}
        self._input_member_guard = None

    def read_control(self, manifest, record_type, maximum_bytes):
        """Reuse only immutable static controls under the current file snapshot."""
        self.writer.require_verification_context()
        if maximum_bytes is not None and manifest.materialization.size_bytes>maximum_bytes:
            raise BoundedFileIOError("bounded input exceeds its byte limit")
        key=(manifest.materialization.materialization_id,record_type,decimal_context_key())
        retained=self._controls.get(key)
        if retained is None:
            from empirical_lawhood.runtime.progress import report_progress
            report_progress(phase='decode_retained.' + record_type.SCHEMA.rsplit('/', 1)[-1])
        else:
            original,_=retained
            if original != manifest:
                raise PermissionError('CURRENT_RESULT_PUBLISHED_CONTROL_BYTES_MISMATCH')
        from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record
        record = read_verified_canonical_record(self.writer, manifest, record_type,
            maximum_bytes=manifest.materialization.size_bytes, before_member=self._input_member_guard)
        if record._is_cacheable():
            # Retain this reader's existing ownership; shared lookup and
            # validator/Decimal provenance belong to the finite weak store.
            self._controls[key]=(manifest,record)
        self.writer.require_verification_context()
        return record

    def authenticate_execution_plan(self, *, package, issued, run_id):
        """Pure issued-plan correspondence; supplies no task or result authority."""
        self.writer.require_verification_context()
        key=(package.fingerprint(),issued.fingerprint(),run_id,decimal_context_key())
        execution=self._plans.get(key)
        if execution is None:
            execution=authenticate_current_execution_plan(package=package,issued=issued,
                run_id=run_id,writer=self.writer,control_reader=self)
            self._plans[key]=execution
            self._task_indexes[(id(execution), decimal_context_key())]=(execution, _index_execution_tasks(execution))
        self.writer.require_verification_context()
        return execution

    def execution_task(self, *, execution_plan, task_id):
        """Look up only a plan authenticated by this live reader; grant no access."""
        self.writer.require_verification_context()
        entry = self._task_indexes.get((id(execution_plan), decimal_context_key()))
        if entry is None or entry[0] is not execution_plan:
            raise PermissionError('CURRENT_RESULT_AUTHENTICATED_PLAN_REQUIRED')
        task = entry[1].get(task_id)
        self.writer.require_verification_context()
        return task

    def output_artifact_plane(self, *, package, execution_plan, output_codecs):
        """Lower the same immutable output census once per code-owned codec set."""
        self.writer.require_verification_context()
        entry = self._task_indexes.get((id(execution_plan), decimal_context_key()))
        plan_key = (package.fingerprint(), package.issued_study.fingerprint(), package.run_plan_id, decimal_context_key())
        if (entry is None or entry[0] is not execution_plan
                or self._plans.get(plan_key) is not execution_plan):
            raise PermissionError('CURRENT_RESULT_AUTHENTICATED_PLAN_REQUIRED')
        if not _has_stock_manifest_reads(self.writer):
            return retained_output_artifact_plane(package, execution_plan, self.writer, output_codecs)
        key = (package.fingerprint(), id(execution_plan), decimal_context_key(), tuple(sorted(output_codecs.items())))
        if key not in self._output_writers:
            self._output_writers[key] = retained_output_artifact_plane(package, execution_plan, self.writer, output_codecs)
        return self._output_writers[key]

    def original_recovery_index(self, *, package, execution_plan, authority_identities=None):
        """Reuse the pure frozen census, never continuation records or events."""
        from empirical_lawhood.runtime.recovery import build_run_recovery_index

        self.writer.require_verification_context()
        plan_key = (package.fingerprint(), package.issued_study.fingerprint(),
            package.run_plan_id, decimal_context_key())
        if self._plans.get(plan_key) is not execution_plan:
            raise PermissionError('CURRENT_RESULT_AUTHENTICATED_PLAN_REQUIRED')
        authorities = tuple(sorted((
            ObjectIdentity.from_record(package.scientific_approval.authorization_id, package.scientific_approval),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority))
            if authority_identities is None else authority_identities, key=lambda value: value.object_id))
        key = (plan_key, authorities)
        index = self._recovery_indexes.get(key)
        if index is None:
            index = build_run_recovery_index(execution_plan, run_id=package.run_plan_id,
                wave_id=f'wave.{package.package_id}', authority_identities=authorities)
            self._recovery_indexes[key] = index
        self.writer.require_verification_context()
        return index

    def collect_receipt_closure(self, *, package, execution_plan, reveal, capability_prefixes, allow_partial=False):
        """Use the ordinary complete receipt/input-lineage owner, within this read."""
        from empirical_lawhood.api.recursive_qualified_parents import _collect_receipt_closure
        self.writer.require_verification_context()
        if self.authenticate_execution_plan(package=package, issued=package.issued_study,
                run_id=package.run_plan_id) is not execution_plan:
            raise PermissionError("issued input closure requires this reader's actual authenticated plan")
        closure = _collect_receipt_closure(package, execution_plan, self.writer, reveal, capability_prefixes,
            control_reader=self, allow_partial=allow_partial)
        # Authentication above already read the exact canonical source plan.
        # Retain its immutable record, so custody can admit known control
        # metadata before any further source/control body hash.
        sources = tuple(record for key, (manifest, record) in self._controls.items()
            if key[2] == decimal_context_key() and type(record) is RunPlan
            and manifest.materialization.relative_path == "runs/"+package.run_plan_id+"/plans/run-plan.json"
            and ObjectIdentity.from_record(record.run_plan_id, record) == execution_plan.source_plan)
        if len(sources) != 1:
            raise PermissionError("issued input closure loses its actual authenticated source plan")
        self._receipt_closures[id(closure)] = closure, package, execution_plan, sources[0]
        self.writer.require_verification_context()
        return closure

    def require_receipt_closure(self, *, package, execution_plan, receipt_closure):
        """Require exact immutable facts produced by this live invocation, not permission."""
        self.writer.require_verification_context()
        selected = self._receipt_closures.get(id(receipt_closure))
        if (selected is None or selected[0] is not receipt_closure or selected[1] != package
                or selected[2] is not execution_plan):
            raise PermissionError("issued input closure lacks its actual reader/package/plan binding")
        return selected[3]

    def read_receipted_output_metadata(self, *, package, execution_plan, task_id,
            before_header, expected_receipt_id=None, _ancestors=()):
        """Join bounded receipt headers before any scientific output body hash.

        ``before_header`` owns fresh original and current issued permission.
        This method supplies exact immutable metadata facts only; output bytes
        and their full publications remain subject to the caller's live scope.
        """
        from empirical_lawhood.api.recursive_qualified_parents import _actual_package
        from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
        from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
        from empirical_lawhood.infrastructure.execution import LocalScheduler
        from empirical_lawhood.kernel.status import OperationalStatus
        from empirical_lawhood.runtime.execution import VerifiedArtifactInput
        if not callable(before_header):
            raise TypeError("issued receipt metadata requires its current header guard")
        task = self.execution_task(execution_plan=execution_plan, task_id=task_id)
        if task is None or task_id in _ancestors:
            raise PermissionError("issued receipt metadata has a foreign or cyclic producer")
        # The actual prepared package and authenticated exact plan remain the
        # controlling source. This is not an input-supplied replacement index.
        if _actual_package(self.writer, package.run_plan_id, control_reader=self) != package:
            raise PermissionError("issued receipt metadata changes its current package")
        index = self.original_recovery_index(package=package, execution_plan=execution_plan)
        from .retained_e3_control_repair import selected_repair_index
        index = selected_repair_index(writer=self.writer, plan=execution_plan, predecessor=index)
        index_path = index.index_relative_path
        index_manifest = self.writer.read_manifest(index_path)
        if (index_manifest.logical.payload_schema != index.SCHEMA
                or index_manifest.logical.content_sha256 != index.fingerprint()
                or index_manifest.materialization.physical_sha256 != index.fingerprint()
                or index_manifest.materialization.size_bytes != index.canonical_size_bytes()):
            raise PermissionError("issued receipt metadata changes its exact recovery index")
        before_header(index_manifest, index=index, task=None, candidate=None)
        self.writer.verify_manifest(index_manifest)
        store = ExternalTaskReceiptStore(self.writer)
        successful = []
        for candidate in index.task(task_id).attempts:
            selected = store._read_envelope(package.run_plan_id, task_id, candidate.attempt_id)
            if selected is None:
                continue
            path, manifest = selected
            if (manifest.logical.logical_artifact_id != "task-receipt.receipt." + candidate.attempt_id
                    or manifest.materialization.relative_path != store._relative_path(
                        package.run_plan_id, task_id, candidate.attempt_id)
                    or manifest.materialization.storage_root_id != self.writer.root.contract.storage_root_id):
                raise PermissionError("issued receipt header changes its exact current candidate locator")
            before_header(manifest, index=index, task=task, candidate=candidate)
            # _read_body accepts only this exact bounded receipt codec and
            # compares canonical digest/run/task/attempt against its sidecar.
            receipt = store._read_body(package.run_plan_id, task_id, candidate.attempt_id, path, manifest)
            if receipt.operational_status is OperationalStatus.SUCCEEDED:
                ExternalRunRecoveryStore._validate_receipt_static(index, task, candidate, receipt)
                successful.append((receipt, manifest))
        if len(successful) != 1:
            raise PermissionError("issued output lacks its unique successful frozen receipt")
        receipt, manifest = successful[0]
        if expected_receipt_id is not None and receipt.receipt_id != expected_receipt_id:
            raise PermissionError("issued output substitutes the selected successful receipt")
        dependencies = {}
        facts = [(manifest.logical, manifest.materialization)]
        for parent_id in task.dependency_task_ids:
            parent, outputs, parent_facts = self.read_receipted_output_metadata(package=package,
                execution_plan=execution_plan, task_id=parent_id, before_header=before_header,
                _ancestors=(*_ancestors, task_id))
            dependencies[parent_id] = outputs
            facts.extend(parent_facts)
        inputs = list(LocalScheduler._dependency_outputs(task, dependencies))
        for spec in task.external_inputs:
            relative, _, _ = provider_input_location(self.writer, package.run_plan_id, spec.logical_artifact_id)
            external = self.writer.read_manifest(relative)
            logical, physical = external.logical, external.materialization
            if (physical.relative_path != relative
                    or physical.storage_root_id != self.writer.root.contract.storage_root_id
                    or logical.logical_artifact_id != spec.logical_artifact_id
                    or any(wanted is not None and actual != wanted for actual, wanted in (
                        (logical.payload_schema, spec.expected_payload_schema),
                        (logical.content_sha256, spec.expected_content_sha256),
                        (physical.size_bytes, spec.expected_size_bytes),
                        (logical.media_type, spec.expected_media_type),
                        (logical.outcome_access, spec.expected_outcome_access),
                        (logical.visibility_ceiling, spec.expected_visibility_ceiling)))):
                raise PermissionError("issued receipt substitutes a frozen external input")
            inputs.append(VerifiedArtifactInput(logical, physical))
        if receipt.input_materialization_ids != tuple(sorted(value.materialization.materialization_id for value in inputs)):
            raise PermissionError("issued receipt changes its complete actual input materializations")
        expected_parents = tuple(sorted((ArtifactLineageParent(
            ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical),
            value.logical.visibility_ceiling, value.logical.outcome_access) for value in inputs), key=lineage_parent_sort_key))
        logicals = receipt.output_logical_artifacts
        if not logicals:
            raise PermissionError("issued output receipt has no frozen output census")
        _require_current_task_receipt_outputs(receipt=receipt, logical=logicals[0], execution_plan=execution_plan,
            task=task, capability_prefixes=(task.capability.capability_key,))
        physical = {value.logical_artifact_id: value for value in receipt.output_materializations}
        outputs = tuple(VerifiedArtifactInput(value, physical[value.logical_artifact_id]) for value in logicals)
        if any(value.materialization.storage_root_id != self.writer.root.contract.storage_root_id
                or value.logical.content_sha256 != value.materialization.physical_sha256 for value in outputs):
            raise PermissionError("issued output changes its exact physical source-root or content identity")
        if any(value.logical.lineage_parents != expected_parents for value in outputs):
            raise PermissionError("issued output changes its exact frozen input ancestry")
        # Genuine historical dispatch is independent of current read permission
        # and of a new effect's Ready-time authority clock.
        from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane
        history_writer = self.writer
        if type(history_writer) is _ScopedArtifactPlane:
            history_writer = ExternalArtifactPlane(history_writer.root, history_writer.validators,
                history_writer.semantic_validations, custody_limits=history_writer.custody_limits, artifact_verification='strict')
        before_header(manifest, index=index, task=task,
            candidate=next(value for value in index.task(task_id).attempts if value.attempt_id == receipt.attempt_id))
        authenticate_historical_execution_authority(package=package, execution_plan=execution_plan,
            receipt=receipt, writer=history_writer)
        receipt_parents = tuple(sorted((ArtifactLineageParent(
            ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical),
            value.logical.visibility_ceiling, value.logical.outcome_access) for value in outputs), key=lineage_parent_sort_key))
        from empirical_lawhood.runtime.artifacts import most_restrictive_outcome_access
        if (manifest.logical.lineage_parents != receipt_parents
                or manifest.logical.outcome_access is not most_restrictive_outcome_access(
                    *(value.logical.outcome_access for value in outputs))
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.most_restrictive(
                    *(value.logical.visibility_ceiling for value in outputs))):
            raise PermissionError("issued receipt changes its complete output ancestry")
        facts.extend((value.logical, value.materialization) for value in outputs)
        before_header(manifest, index=index, task=task,
            candidate=next(value for value in index.task(task_id).attempts if value.attempt_id == receipt.attempt_id),
            authenticated_facts=tuple(facts))
        # Permission callback now owns exact receipt/output facts before the
        # storage owner can hash this publication's siblings.
        self.writer.verify_manifest(manifest)
        return receipt, outputs, tuple(facts)

    def authenticate(self, *, package, issued, receipt, logical, capability_prefixes):
        execution=self.authenticate_execution_plan(package=package,issued=issued,run_id=receipt.run_id)
        _require_current_stored_result(receipt=receipt, logical=logical, execution=execution,
            writer=self.writer, capability_prefixes=capability_prefixes, control_reader=self)
        key = (package.fingerprint(), execution.fingerprint(), receipt.fingerprint(), decimal_context_key())
        if key not in self._execution_history:
            self._execution_history[key] = authenticate_historical_execution_authority(
                package=package, execution_plan=execution, receipt=receipt, writer=self.writer)
        self.writer.require_verification_context()
        return execution


def authenticate_unprotected_current_result_if_issued(*, writer, receipt, logical, capability_prefixes):
    """Preserve exposed unissued imports; current runs must match their frozen plans."""
    if not current_result_package_present(writer=writer, run_id=receipt.run_id):
        # Missing controls cannot prove that a result was never issued. Only
        # the existing explicitly exposed software-import contract may omit
        # them, and its supplied metadata must still equal actual stored custody.
        if (not isinstance(writer, ExternalArtifactPlane)
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or logical.outcome_access not in (OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.OUTCOME_BLIND)):
            raise PermissionError('CURRENT_RESULT_MISSING_ISSUED_CONTROLS')
        actual = ExternalTaskReceiptStore(writer).read_by_receipt_id(receipt.run_id, receipt.task_id, receipt.receipt_id)
        if (actual != receipt or logical not in actual.output_logical_artifacts
            or any(value.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                   or value.outcome_access not in (OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.OUTCOME_BLIND)
                   for value in actual.output_logical_artifacts)):
            raise PermissionError('CURRENT_RESULT_EXACT_EXPOSED_IMPORT_RECEIPT_REQUIRED')
        return
    # The package is public control metadata. Its closed schema selects only the
    # current package owner; it cannot select executable modules.
    relative = f'runs/{receipt.run_id}/plans/campaign-package.json'
    manifest = decode_artifact_manifest(read_bounded_bytes(
        writer.root.resolve(relative + '.manifest.json', for_write=False), maximum_bytes=MAX_ARTIFACT_MANIFEST_BYTES))
    if manifest.logical.payload_schema != ExperimentPackage.SCHEMA:
        raise PermissionError('CURRENT_RESULT_UNSUPPORTED_PACKAGE')
    package = _current_control(writer=writer, run_id=receipt.run_id, name='campaign-package',
                               record_type=ExperimentPackage, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    # Keep the shared strict package parser's closed current package validation.
    if loads_campaign_package_authoring(package.canonical_bytes().decode(), media_type='application/json') != package:
        raise PermissionError('CURRENT_RESULT_PACKAGE_BYTES_MISMATCH')
    store = ExternalStudyOperationAuthorityStore(writer)
    issued = ExternalIssuedStudyPublisher(artifact_plane=writer, authority_store=store,
        grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(package.issued_study.issue_id).manifest
    authenticate_current_result_plan_outputs(package=package, issued=issued, receipt=receipt,
        logical=logical, writer=writer, capability_prefixes=capability_prefixes)
