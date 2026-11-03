# SPDX-License-Identifier: MPL-2.0
"""Replay actual qualification custody before a prospective parent is consumed."""

from dataclasses import dataclass, field, fields, replace
from datetime import UTC, datetime
from hashlib import sha256
from types import MappingProxyType

from .codecs import MAX_CAMPAIGN_PACKAGE_BYTES
from .current_result_custody import (
    CurrentResultPlanReader, _current_control,
    authenticate_historical_execution_authority, require_current_result_receipt_outputs, retained_output_artifact_plane,
)
from empirical_lawhood.api.models import EnvelopeExperimentPackage, ExperimentPackage
from empirical_lawhood.runtime.artifacts import artifact_custody_limits
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from ..infrastructure.execution import LocalScheduler
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from ..infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.study_issue import (
    ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore,
    PROGRAMME_ISSUE_GRANTEE_ID, PROGRAMME_REVEAL_GRANTEE_ID,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.status import AdmissionStatus, OperationalStatus, ScientificStatus
from empirical_lawhood.planning.study_issue import StudyAuthorityKind, require_study_authority
from empirical_lawhood.runtime.adjudication import (
    AdjudicationEvaluability, MAX_ADJUDICATION_BYTES, ScientificAdjudicationOutputContract,
    ScientificAdjudicationRecord,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactLineageParent, MAX_ARTIFACT_PUBLICATION_MEMBERS, lineage_parent_sort_key
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recovery import (
    EnvelopeRunRecoveryIndex, RunRecoveryIndex, build_run_recovery_index,
)
from empirical_lawhood.runtime.recursive_qualified_parents import (
    QualifiedParentAdditionalProduct, QualifiedParentEvidence, QualifiedParentPriorExecution, QualifiedParentPriorNative,
    RecursivePriorExecutionBinding, RecursiveQualifiedParentBinding,
)

MAX_PARENT_BYTES = 16 * 1024**2
MAX_PARENT_BINDINGS = 32
MAX_PRIOR_EXECUTIONS = 32


def _actual_package(writer, run_id, *, control_reader=None):
    relative = f'runs/{run_id}/plans/campaign-package.json'
    manifest = writer.read_manifest(relative, maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
    record_type = {ExperimentPackage.SCHEMA: ExperimentPackage,
                   EnvelopeExperimentPackage.SCHEMA: EnvelopeExperimentPackage}.get(manifest.logical.payload_schema)
    if record_type is None:
        raise PermissionError('qualified parent lacks its actual current issued package')
    return _current_control(writer=writer, run_id=run_id, name='campaign-package',
                            record_type=record_type, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES, control_reader=control_reader)


def _exact_output(receipt, logical_id):
    rows = tuple(value for value in receipt.output_logical_artifacts if value.logical_artifact_id == logical_id)
    if len(rows) != 1:
        raise PermissionError('qualified parent omits its exact producing output')
    return rows[0]


def _output_payload(writer, receipt, logical, maximum_bytes, *, before_member=None):
    materializations = tuple(value for value in receipt.output_materializations
                             if value.logical_artifact_id == logical.logical_artifact_id)
    if len(materializations) != 1:
        raise PermissionError('qualified parent omits its actual output materialization')
    physical = materializations[0]
    if (physical.size_bytes > maximum_bytes or physical.compression != 'none'
        or physical.partition_selector is not None or physical.storage_root_id != writer.root.contract.storage_root_id):
        raise PermissionError('qualified parent output changes its bounded physical contract')
    sidecar = writer.read_manifest(physical.relative_path, maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
    if sidecar.logical != logical or sidecar.materialization != physical or sidecar.publication is None:
        raise PermissionError('qualified parent output differs from its actual completion publication')
    # Authority replay and both complete receipt/plan joins precede protected I/O.
    writer.verify_manifest(sidecar, **({} if before_member is None else {"before_member": before_member}))
    if before_member is not None and before_member(sidecar) is not None:
        raise PermissionError("prior product member guard must return None or raise")
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=maximum_bytes)
    digest = sha256(raw).hexdigest()
    if len(raw) != physical.size_bytes or digest != physical.physical_sha256:
        raise PermissionError('qualified parent output bytes differ from their exact receipt')
    if digest != logical.content_sha256:
        raise PermissionError('qualified parent output changes its canonical scientific bytes')
    if before_member is not None and before_member(sidecar) is not None:
        raise PermissionError("prior product member guard must return None or raise")
    return raw


@dataclass(frozen=True, slots=True)
class _ParentReceiptClosure:
    by_task: MappingProxyType
    manifests: tuple
    operational_summaries: MappingProxyType
    recovery_index: RunRecoveryIndex | EnvelopeRunRecoveryIndex
    _manifest_batches: tuple = field(init=False, repr=False)

    def __post_init__(self):
        unique = {}
        for manifest in self.manifests:
            key = (manifest.materialization.storage_root_id, manifest.materialization.relative_path)
            if unique.setdefault(key, manifest) != manifest:
                raise PermissionError('qualified parent closure aliases an exact immutable input')
        manifests = tuple(unique.values())
        object.__setattr__(self, 'manifests', manifests)
        object.__setattr__(self, '_manifest_batches', tuple(
            manifests[start:start + MAX_ARTIFACT_PUBLICATION_MEMBERS]
            for start in range(0, len(manifests), MAX_ARTIFACT_PUBLICATION_MEMBERS)))


class _ParentReadScope:
    """Immutable custody projections within one guarded verification lifetime."""

    def __init__(self, writer, *, plan_reader=None):
        if plan_reader is not None and (type(plan_reader) is not CurrentResultPlanReader
                or plan_reader.writer is not writer):
            raise TypeError('original parent scope changes its actual verified plan reader')
        self.plan_reader = CurrentResultPlanReader(writer) if plan_reader is None else plan_reader
        self.closures = {}

    def receipt_closure(self, package, plan, writer, reveal, prefixes):
        if writer.root is not self.plan_reader.writer.root:
            raise PermissionError('qualified parent read scope substitutes its guarded storage root')
        writer.require_verification_context()
        key = (package.fingerprint(), id(plan), None if reveal is None else reveal.fingerprint(), prefixes)
        closure = self.closures.get(key)
        if closure is None:
            closure = _collect_receipt_closure(package, plan, writer, reveal, prefixes, control_reader=self.plan_reader)
            self.closures[key] = closure
        writer.require_verification_context()
        return closure


def _collect_receipt_closure(package, plan, writer, reveal, prefixes, *, control_reader=None, allow_partial=False):
    """Use the actual recovery owner to select every completed parent task."""
    if type(allow_partial) is not bool:
        raise TypeError('partial receipt inspection requires an explicit boolean selection')
    run_id = plan.source_plan.object_id
    wave_id = f'wave.{package.package_id}'
    index_type = RunRecoveryIndex if isinstance(plan, ExecutionPlan) else EnvelopeRunRecoveryIndex
    index_name = 'resource-run-recovery-index' if isinstance(plan, ExecutionPlan) else 'envelope-run-recovery-index'
    recovery = ExternalRunRecoveryStore(writer)
    index = recovery.read_index(f'runs/{run_id}/recovery/{wave_id}/{index_name}.json', expected_schema=index_type.SCHEMA)
    authorities = [ObjectIdentity.from_record(package.scientific_approval.authorization_id, package.scientific_approval),
                   ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority)]
    if not isinstance(package, ExperimentPackage):
        authorities.append(ObjectIdentity.from_record(reveal.authority_id, reveal))
    expected_index = (build_run_recovery_index(plan, run_id=run_id, wave_id=wave_id, authority_identities=tuple(authorities))
        if control_reader is None else control_reader.original_recovery_index(package=package,
            execution_plan=plan, authority_identities=tuple(authorities)))
    if index != expected_index:
        raise PermissionError('qualified parent changes its actual recovery plan or authority census')
    if type(index) is RunRecoveryIndex:
        from .retained_e3_control_repair import selected_repair_index
        index = selected_repair_index(writer=writer, plan=plan, predecessor=index)
    terminal = recovery.read_terminal(index)
    task_ids = tuple(task.task_id for task in plan.tasks)
    if not allow_partial and (terminal is None or terminal.operational_status != 'SUCCEEDED'
        or terminal.completed_task_ids != task_ids or terminal.failed_task_ids or terminal.blocked_task_ids):
        raise PermissionError('qualified parent lacks a complete successful retained parent execution')
    receipts = ExternalTaskReceiptStore(writer)
    latest = {}
    if terminal is not None:
        for row in terminal.attempts:
            if row.task_id not in latest or row.ordinal > latest[row.task_id].ordinal:
                latest[row.task_id] = row
        # A partial terminal records only reached tasks. The operational census
        # below still checks every assigned attempt slot, including absence of
        # events and receipts for tasks the scheduler never reached.
        if set(latest) - set(task_ids) or not allow_partial and set(latest) != set(task_ids):
            raise PermissionError('retained parent terminal changes its complete assigned task census')
    if allow_partial:
        from empirical_lawhood.infrastructure.recursive_custody import _partial_operational_census, _execution_operational_census
        if type(plan) is not ExecutionPlan:
            raise TypeError('partial scientific custody requires the exact supported execution plan')
        if terminal is None:
            _, _, _, latest = _partial_operational_census(recovery=recovery, store=receipts, plan=plan, index=index)
        else:
            _execution_operational_census(recovery=recovery, store=receipts, plan=plan, index=index,
                terminal=terminal)
    operational_summaries = dict(latest)
    latest = {key: row for key, row in latest.items() if row.disposition.value == 'SUCCEEDED'}
    by_task = {}
    manifests = []
    for task in plan.tasks:
        if task.task_id not in latest:
            continue
        row = latest[task.task_id]
        receipt = receipts.read_by_receipt_id(run_id, task.task_id, row.receipt_id)
        if (receipt is None or not receipt.output_logical_artifacts or receipt.fingerprint() != row.receipt_sha256
            or receipt.operational_status is not OperationalStatus.SUCCEEDED):
            raise PermissionError('qualified parent dependency lacks its exact completed receipt')
        require_current_result_receipt_outputs(receipt=receipt, logical=receipt.output_logical_artifacts[0],
            execution_plan=plan, capability_prefixes=prefixes, control_reader=control_reader)
        if type(package) is ExperimentPackage:
            authenticate_historical_execution_authority(package=package, execution_plan=plan,
                receipt=receipt, writer=writer)
        by_task[task.task_id] = receipt
        physical_by_logical = {value.logical_artifact_id: value for value in receipt.output_materializations}
        for logical in receipt.output_logical_artifacts:
            physical = physical_by_logical[logical.logical_artifact_id]
            manifest = writer.read_manifest(physical.relative_path,
                maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
            if (manifest.logical != logical or manifest.materialization != physical
                or physical.storage_root_id != writer.root.contract.storage_root_id or manifest.publication is None):
                raise PermissionError('qualified parent dependency changes its actual output publication')
            manifests.append(manifest)
    dependency_outputs = {}
    for task_id, receipt in by_task.items():
        physical_by_logical = {value.logical_artifact_id: value for value in receipt.output_materializations}
        dependency_outputs[task_id] = tuple(VerifiedArtifactInput(value, physical_by_logical[value.logical_artifact_id])
                                           for value in receipt.output_logical_artifacts)
    for task in plan.tasks:
        if task.task_id not in by_task:
            continue
        # Reuse the scheduler's pure selection rule: current ExecutionTask edges
        # may consume one output of a multioutput dependency; older tasks consume
        # all dependency outputs. Complete producer census remains proved above.
        selected_inputs = LocalScheduler._dependency_outputs(task, dependency_outputs)
        expected = {value.materialization.materialization_id for value in selected_inputs}
        input_logicals = {value.logical.logical_artifact_id: value.logical for value in selected_inputs}
        for spec in task.external_inputs:
            path, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
            manifest = writer.read_manifest(path, maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
            logical, physical = manifest.logical, manifest.materialization
            if (logical.logical_artifact_id != spec.logical_artifact_id or physical.relative_path != path
                or physical.storage_root_id != writer.root.contract.storage_root_id
                or physical.compression != 'none' or physical.partition_selector is not None or manifest.publication is None
                or any(expected_value is not None and observed != expected_value for observed, expected_value in (
                    (logical.content_sha256, spec.expected_content_sha256), (logical.payload_schema, spec.expected_payload_schema),
                    (logical.media_type, spec.expected_media_type), (physical.size_bytes, spec.expected_size_bytes),
                    (logical.visibility_ceiling, spec.expected_visibility_ceiling), (logical.outcome_access, spec.expected_outcome_access)))
                or (spec.identity_scope_sha256 is not None and not any(
                    parent.identity.object_fingerprint == spec.identity_scope_sha256 for parent in logical.lineage_parents))):
                raise PermissionError('qualified parent dependency changes its exact frozen external input')
            expected.add(physical.materialization_id)
            input_logicals[logical.logical_artifact_id] = logical
            manifests.append(manifest)
        if set(by_task[task.task_id].input_materialization_ids) != expected:
            raise PermissionError('qualified parent dependency receipt changes its complete actual input census')
        parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(value.logical_artifact_id, value),
            value.visibility_ceiling, value.outcome_access) for value in input_logicals.values()), key=lineage_parent_sort_key))
        if any(value.lineage_parents != parents for value in by_task[task.task_id].output_logical_artifacts):
            raise PermissionError('qualified parent output changes its exact scientific input lineage')
    # All grants, exact plans, completion rows and input joins are proved before
    # this existing custody owner streams any retained protected scientific bytes.
    return _ParentReceiptClosure(MappingProxyType(by_task), tuple(manifests), MappingProxyType(operational_summaries), index)


def _verify_receipt_closure(writer, closure, *, before_member=None):
    # The original closure owns its immutable deduplicated census once. Keep
    # those exact tuples, rather than rebuilding/hashing ancestry per consumer.
    for manifests in closure._manifest_batches:
        writer.verify_manifests(manifests,
            **({} if before_member is None else {'before_member': before_member}))
    return closure.by_task


def _consume_receipt_closure(writer, closure, consume):
    """Keep one complete payload verification and its consumer in one lifetime.

    Receipt/authority collection belongs outside this scope: those per-row reads
    must not repeatedly traverse a growing scientific-payload snapshot. The
    supplied guarded writer owns validation and every final mutation check.
    """
    if not callable(consume):
        raise TypeError('qualified parent closure consumer must be callable')
    with writer.read_context() as payload_writer:
        by_task = _verify_receipt_closure(payload_writer, closure)
        return consume(payload_writer, by_task)


def _complete_receipts(package, plan, writer, reveal, prefixes, *, verify_payloads=True):
    """Compatibility reader for named current programme consumers."""
    closure = _collect_receipt_closure(package, plan, writer, reveal, prefixes)
    return _verify_receipt_closure(writer, closure) if verify_payloads else closure.by_task


def _additional_products(writer, producing, schemas, output_codecs, *, outcome_access=OutcomeAccess.EVALUATION_SEALED):
    """Read only installed, declared outputs of this actual successful producer.

    The caller has already replayed original issue, execution, reveal, plan,
    complete task receipts and evaluator scope. The aggregate byte bound is
    independent of the unchanged primary product's bound.
    """
    if not schemas:
        return ()
    if (type(schemas) is not tuple or len(schemas) > 4 or schemas != tuple(sorted(set(schemas)))
            or producing.operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError('qualified parent companion requires an exact bounded declaration and successful producer')
    prepared, aggregate = [], 0
    for schema in schemas:
        record_type = output_codecs.get(schema)
        if record_type is None or record_type.SCHEMA != schema:
            raise PermissionError('qualified parent companion lacks its installed typed scientific codec')
        logicals = tuple(value for value in producing.output_logical_artifacts if value.payload_schema == schema)
        if len(logicals) != 1:
            raise PermissionError('qualified parent companion output is absent or duplicated in the actual producer receipt')
        logical = logicals[0]
        physicals = tuple(value for value in producing.output_materializations
            if value.logical_artifact_id == logical.logical_artifact_id)
        if (len(physicals) != 1 or logical.profile is not ArtifactProfile.CANONICAL_JSON
                or logical.media_type != 'application/json'
                or logical.outcome_access is not outcome_access
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or physicals[0].physical_sha256 != logical.content_sha256):
            raise PermissionError('qualified parent companion changes its actual canonical sealed output contract')
        aggregate += physicals[0].size_bytes
        if aggregate > MAX_PARENT_BYTES:
            raise PermissionError('qualified parent companion aggregate exceeds its unchanged 16 MiB bound')
        prepared.append((record_type, logical, physicals[0]))
    # All declarations and aggregate sizes refuse before any companion read.
    products = []
    for record_type, logical, physical in prepared:
        raw = _output_payload(writer, producing, logical, physical.size_bytes)
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=MAX_PARENT_BYTES)
        if record.canonical_bytes() != raw or record.fingerprint() != logical.content_sha256:
            raise PermissionError('qualified parent companion changes exact installed canonical record bytes/version')
        products.append(QualifiedParentAdditionalProduct(logical, physical, raw))
    return tuple(products)


def _semantic_writer(package, plan, writer, output_codecs):
    """Use installed output contracts while replaying an already selected plan."""
    return retained_output_artifact_plane(package, plan, writer, output_codecs)


def _prior_execution_entry(binding, writer, output_codecs, read_scope, required_outcome_access=OutcomeAccess.EVALUATION_SEALED,
        *, product_custody=None, product_validator=None):
    """Replay original authority/dispatch and selected custody on prior use."""
    owned = _owned_product_options(product_custody, product_validator)
    if required_outcome_access not in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED):
        raise PermissionError('prior execution requires an explicit blind or legacy sealed source contract')
    if type(binding) is not RecursivePriorExecutionBinding:
        raise PermissionError('prior execution requires its closed current custody locator')
    binding.__post_init__()
    package = _actual_package(writer, binding.run_id, control_reader=read_scope.plan_reader)
    if (type(package) is not ExperimentPackage or package.run_plan_id != binding.run_id
            or ObjectIdentity.from_record(package.package_id, package) != binding.package
            or ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study) != binding.issued_study
            or ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority) != binding.execution_authority):
        raise PermissionError('prior execution substitutes its original current issued package or execution authority')
    store = ExternalStudyOperationAuthorityStore(writer)
    execution = store.load(binding.execution_authority.object_id)
    if execution != package.execution_authority:
        raise PermissionError('prior execution substitutes its stored genuine execution grant')
    published = ExternalIssuedStudyPublisher(artifact_plane=writer, authority_store=store,
        grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(binding.issued_study.object_id)
    if published.manifest != package.issued_study or published.publication_receipt != package.publication_receipt:
        raise PermissionError('prior execution changes its original issued source publication')
    receipt = ExternalTaskReceiptStore(writer).read_by_receipt_id(binding.run_id, binding.task_id, binding.receipt.object_id)
    if (receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.receipt
            or receipt.operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError('prior execution lacks its exact successful original producing receipt')
    logical = _exact_output(receipt, binding.logical_artifact_id)
    codec = output_codecs.get(binding.record.object_schema)
    if (codec is None or (codec.SCHEMA, codec.VERSION) != (binding.record.object_schema, binding.record.object_version)
            or logical.payload_schema != binding.record.object_schema
            or logical.content_sha256 != binding.record.object_fingerprint
            or not owned and (logical.outcome_access is not required_outcome_access
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE)
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'):
        raise PermissionError('prior execution lacks its exact installed sealed prospective product contract')
    prefixes = tuple(sorted(manifest.capability_key for manifest in package.registry.capabilities))
    plan = read_scope.plan_reader.authenticate(package=package, issued=published.manifest, receipt=receipt,
        logical=logical, capability_prefixes=prefixes)
    if type(plan) is not ExecutionPlan or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan:
        raise PermissionError('prior execution substitutes its exact original issued execution plan')
    if owned:
        _require_owned_product_binding(product_custody, read_scope, package, plan)
    return package, plan, receipt, logical, codec, prefixes


def _authenticate_prior_execution(binding, writer, output_codecs, *, scope_validator, parent_evidence,
                                  read_scope=None, required_outcome_access=OutcomeAccess.EVALUATION_SEALED,
                                  product_custody=None, product_validator=None):
    """Replay one bounded original issued execution without granting reveal.

    Locators are extracted by installed pure code only after authenticating the
    companion producer. They select existing guarded controls, never paths.
    """
    if _owned_product_options(product_custody, product_validator):
        return _authenticate_owned_prior_execution(binding, writer, output_codecs,
            scope_validator=scope_validator, parent_evidence=parent_evidence, read_scope=read_scope,
            required_outcome_access=required_outcome_access, product_custody=product_custody,
            product_validator=product_validator)
    if read_scope is None:
        with writer.read_context() as scoped:
            return _authenticate_prior_execution(binding, scoped, output_codecs, scope_validator=scope_validator,
                parent_evidence=parent_evidence, read_scope=_ParentReadScope(scoped),
                required_outcome_access=required_outcome_access)
    if not callable(scope_validator):
        raise PermissionError('prior execution requires its installed scientific scope validator')
    package, plan, receipt, logical, codec, prefixes = _prior_execution_entry(binding, writer, output_codecs, read_scope,
        required_outcome_access)
    scope_parent = parent_evidence
    closure = None
    if binding.scope_output_schema_ids:
        closure = read_scope.receipt_closure(package, plan, writer, None, prefixes)
        metadata_receipts = closure.by_task
        prepared, aggregate = [], 0
        for schema in binding.scope_output_schema_ids:
            producers = tuple(value for value in metadata_receipts.values() if any(
                logical.payload_schema == schema for logical in value.output_logical_artifacts))
            if len(producers) != 1:
                raise PermissionError('prior execution scope output lacks its one actual successful producer')
            logicals = tuple(value for value in producers[0].output_logical_artifacts if value.payload_schema == schema)
            physicals = tuple(value for value in producers[0].output_materializations
                if value.logical_artifact_id in {logical.logical_artifact_id for logical in logicals})
            if len(logicals) != 1 or len(physicals) != 1:
                raise PermissionError('prior execution scope output duplicates its actual metadata declaration')
            aggregate += physicals[0].size_bytes
            if aggregate > MAX_PARENT_BYTES:
                raise PermissionError('prior execution scope metadata exceeds its unchanged 16 MiB bound')
            prepared.append((schema, producers[0]))
        products = tuple(product for schema, producer in prepared
            for product in _additional_products(writer, producer, (schema,), output_codecs,
                outcome_access=OutcomeAccess.OUTCOME_BLIND))
        scope_parent = replace(parent_evidence, prior_scope_products=products)
    verdict = scope_validator(parent_evidence=scope_parent, binding=binding, package=package, execution_plan=plan)
    if verdict is not None:
        raise PermissionError('prior execution scope validator must refuse by raising and return None on success')
    writer = read_scope.plan_reader.output_artifact_plane(package=package, execution_plan=plan,
        output_codecs=output_codecs)
    if closure is None:
        closure = read_scope.receipt_closure(package, plan, writer, None, prefixes)
    by_task = _verify_receipt_closure(writer, closure)
    if by_task.get(binding.task_id) != receipt:
        raise PermissionError('prior execution substitutes a noncurrent original producing attempt')
    raw = _output_payload(writer, receipt, logical, MAX_PARENT_BYTES)
    record = decode_canonical_bytes(raw, codec, maximum_bytes=MAX_PARENT_BYTES)
    if (record.canonical_bytes() != raw or binding.record_id_field not in {field.name for field in fields(record)}
            or getattr(record, binding.record_id_field) != binding.record.object_id):
        raise PermissionError('prior execution changes its exact installed canonical product bytes or record identity')
    physical, = (value for value in receipt.output_materializations if value.logical_artifact_id == logical.logical_artifact_id)
    additional, aggregate, requested = [], 0, []
    for schema in binding.additional_output_schema_ids:
        producers = tuple(value for value in by_task.values() if any(logical.payload_schema == schema
            for logical in value.output_logical_artifacts))
        if len(producers) != 1:
            raise PermissionError('prior execution additional output lacks its one actual successful producer')
        logicals = tuple(value for value in producers[0].output_logical_artifacts if value.payload_schema == schema)
        if len(logicals) != 1:
            raise PermissionError('prior execution additional output duplicates its requested actual schema')
        physicals = tuple(value for value in producers[0].output_materializations
            if value.logical_artifact_id == logicals[0].logical_artifact_id)
        if len(physicals) != 1:
            raise PermissionError('prior execution additional output omits its actual materialization')
        aggregate += physicals[0].size_bytes
        if aggregate > MAX_PARENT_BYTES:
            raise PermissionError('prior execution additional output aggregate exceeds16MiB')
        requested.append((schema, producers[0]))
    for schema, producer in requested:
        values = _additional_products(writer, producer, (schema,), output_codecs,
            outcome_access=OutcomeAccess.OUTCOME_BLIND)
        additional.extend(values)
    native = _prior_native_subwork(writer, binding, plan, by_task, control_reader=read_scope.plan_reader)
    return QualifiedParentPriorExecution(binding, package, plan, tuple(by_task[task_id] for task_id in sorted(by_task)),
        QualifiedParentAdditionalProduct(logical, physical, raw), tuple(additional), native)



def _owned_product_options(custody, validator):
    """A code-owned product callback always accompanies a live exact custody."""
    if custody is None and validator is None:
        return False
    from .current_task_custody import CurrentIssuedTaskCustody
    if type(custody) is not CurrentIssuedTaskCustody or not callable(validator):
        raise PermissionError("owned prior product requires paired current custody and installed validator")
    return True


def _require_owned_product_binding(custody, read_scope, package, plan):
    if (type(read_scope) is not _ParentReadScope or custody._control_reader is not read_scope.plan_reader
            or custody._current_package_plan is None or custody._current_package_plan[0] != package
            or custody._current_package_plan[1] is not plan or not callable(custody._retained_read_guard)
            or not callable(custody._retained_member_guard)):
        raise PermissionError("owned prior product requires the same live retained package, plan and reader")
    read_scope.plan_reader.writer.require_active_verification_scope()
    custody._require_retained_read()
    custody.require_original_input_access()


def _authenticate_owned_prior_execution(binding, writer, output_codecs, *, scope_validator, parent_evidence,
        read_scope, required_outcome_access, product_custody, product_validator):
    """Authenticate one owning-source output without changing generic access policy."""
    if not callable(scope_validator) or type(read_scope) is not _ParentReadScope:
        raise PermissionError("owned prior product requires its live original scientific reader")
    package, plan, receipt, logical, codec, prefixes = _prior_execution_entry(binding, writer, output_codecs,
        read_scope, required_outcome_access, product_custody=product_custody, product_validator=product_validator)
    if binding.scope_output_schema_ids or binding.additional_output_schema_ids:
        raise PermissionError("owned source product cannot introduce undeclared companion outputs")
    closure = read_scope.receipt_closure(package, plan, writer, None, prefixes)
    read_scope.plan_reader.require_receipt_closure(package=package, execution_plan=plan, receipt_closure=closure)
    if closure.by_task.get(binding.task_id) != receipt:
        raise PermissionError("owned prior product substitutes its unique current winning receipt")
    if scope_validator(parent_evidence=parent_evidence, binding=binding, package=package, execution_plan=plan) is not None:
        raise PermissionError("prior execution scope validator must return None or raise")
    if product_validator(binding=binding, package=package, execution_plan=plan, receipt=receipt,
            logical=logical, read_scope=read_scope, product_custody=product_custody) is not None:
        raise PermissionError("owned prior product validator must return None or raise")
    _require_owned_product_binding(product_custody, read_scope, package, plan)
    semantic = read_scope.plan_reader.output_artifact_plane(package=package, execution_plan=plan,
        output_codecs=output_codecs)
    # This whole dependent snapshot finalizes before the actual retained
    # binding exits. Its guard admits exact receipted siblings, never labels.
    with semantic.read_context(before_member=product_custody.require_input_member) as products:
        by_task = _verify_receipt_closure(products, closure)
        raw = _output_payload(products, receipt, logical, MAX_PARENT_BYTES,
            before_member=product_custody.require_input_member)
        record = decode_canonical_bytes(raw, codec, maximum_bytes=MAX_PARENT_BYTES)
        physical, = (value for value in receipt.output_materializations
            if value.logical_artifact_id == logical.logical_artifact_id)
        manifest = products.read_manifest(physical.relative_path)
        if manifest.logical != logical or manifest.materialization != physical:
            raise PermissionError("owned prior product changes its actual receipted member")
        product_custody.require_input_member(manifest)
        if (record.canonical_bytes() != raw or binding.record_id_field not in {value.name for value in fields(record)}
                or getattr(record, binding.record_id_field) != binding.record.object_id):
            raise PermissionError("prior execution changes its exact installed canonical product bytes or record identity")
        native = _prior_native_subwork(products, binding, plan, by_task, control_reader=read_scope.plan_reader)
        product_custody.require_input_member(manifest)
        products.require_verification_snapshot()
    _require_owned_product_binding(product_custody, read_scope, package, plan)
    return QualifiedParentPriorExecution(binding, package, plan,
        tuple(by_task[task_id] for task_id in sorted(by_task)),
        QualifiedParentAdditionalProduct(logical, physical, raw), (), native)

def _prior_native_subwork(writer, binding, plan, by_task, *, control_reader=None, task_index=None):
    """Reuse original completed subwork custody; this reader has no entry token."""
    with writer.read_context() as scoped:
        return _read_prior_native_subwork(scoped, binding, plan, by_task,
            control_reader=control_reader, task_index=task_index)


def _read_prior_native_subwork(writer, binding, plan, by_task, *, control_reader, task_index):
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.runtime.artifacts import verify_artifact_manifests
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    tasks = ({task.task_id: task for task in plan.tasks} if task_index is None else task_index) if control_reader is None else None
    result = []
    for request in binding.native_subwork:
        task = (tasks.get(request.task_id) if control_reader is None else
            control_reader.execution_task(execution_plan=plan, task_id=request.task_id))
        receipt = by_task.get(request.task_id)
        if task is None or receipt is None:
            raise PermissionError('prior native execution is outside its exact successful issued task census')
        if not task.outputs or len({output.visibility_ceiling for output in task.outputs}) != 1:
            raise PermissionError('prior native execution has no exact common output visibility contract')
        contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=binding.execution_plan,
            visibility_ceiling=task.outputs[0].visibility_ceiling,
            outcome_access=task.capability.requested_outcome_access)
        contact = contacts.read(binding.run_id, request.task_id)
        if (contact is None or contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or contact.attempt_id != receipt.attempt_id or contact.implementation_commit != receipt.implementation_commit
                or contact.input_materialization_ids != receipt.input_materialization_ids
                or contact.dependency_receipt_ids != tuple(sorted(by_task[value].receipt_id for value in task.dependency_task_ids))):
            raise PermissionError('prior native execution changes its actual entered task, inputs or dependency receipts')
        store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts,
            parent_contact=contact, completed_only=True)
        definition = store.read_definition(request.definition)
        actual_config = task.capability.config
        if (definition.parent_contact != contact
                or definition.configuration.object_id != actual_config.config_id
                or definition.configuration.object_schema != actual_config.config_schema
                or definition.configuration.object_fingerprint != actual_config.content_sha256
                or definition.input_materialization_ids != receipt.input_materialization_ids):
            raise PermissionError('prior native execution changes its exact actual task configuration or input contact')
        inspection = store.inspect(definition)
        if (inspection.state is not NativeSubworkState.COMPLETED
                or inspection.completion is None or inspection.receipt is None
                or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED
                or ObjectIdentity.from_record(request.completion.object_id, inspection.completion) != request.completion
                or ObjectIdentity.from_record(inspection.receipt.receipt_id, inspection.receipt) != request.receipt
                or inspection.completion.unknown_streams):
            raise PermissionError('prior native execution lacks its exact successful known original completion and receipt')
        verify_artifact_manifests(writer, inspection.outputs)
        result.append(QualifiedParentPriorNative(request, inspection))
    return tuple(result)


def _require_parent_authorities_current(entries, writer):
    # Singular preparation also accepts a plain artifact plane. Own a finite
    # verification lifetime rather than assuming a caller entered one.
    entries = tuple(entries)
    from .selected_e3_access import _current_authority_reader
    authority_reader = _current_authority_reader(writer)
    if authority_reader is not None:
        return _validate_parent_authorities_now(entries, _load_parent_authorities_in_scope(entries, authority_reader))
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _ScopedArtifactPlane, _has_stock_manifest_reads
    if type(writer) is _ScopedArtifactPlane and _has_stock_manifest_reads(writer):
        # Grant refresh owns only the grant's publication. It must not traverse
        # all scientific bytes accumulated by the caller's immutable read.
        writer = ExternalArtifactPlane(writer.root, writer.validators, writer.semantic_validations,
            custody_limits=writer.custody_limits, artifact_verification='strict')
    with writer.verification_scope() as scoped:
        current = _load_parent_authorities_in_scope(entries, scoped)
    # Scope exit performs the last physical positive-snapshot walk BEFORE
    # sampling UTC; no caller needs a cached time/admission verdict.
    return _validate_parent_authorities_now(entries, current)


def _load_parent_authorities_in_scope(entries, writer):
    """Load all exact grants, close their custody, then sample one fresh UTC.

    This private plural boundary returns the actual current records, not an
    authorization token. Publication/source/receipt replay belongs before this
    final check; the caller keeps the positive verification lifetime entered.
    """
    entries = tuple(entries)
    store = ExternalStudyOperationAuthorityStore(writer)
    current = []
    grants = {}
    def load(identity):
        if identity not in grants:
            grants[identity] = store.load(identity)
        return grants[identity]
    for binding, package in entries:
        if (ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study) != binding.issued_study
                or ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority) != binding.execution_authority):
            raise PermissionError('qualified parent substitutes its issued study or execution authority')
        execution = load(binding.execution_authority.object_id)
        reveal = (None if type(binding) is RecursivePriorExecutionBinding
            else load(binding.reveal_authority.object_id))
        if (execution != package.execution_authority
                or reveal is not None and ObjectIdentity.from_record(reveal.authority_id, reveal) != binding.reveal_authority):
            raise PermissionError('qualified parent substitutes a stored execution or reveal grant')
        current.append((execution, reveal))
    writer.require_verification_snapshot()
    return tuple(current)


def _validate_parent_authorities_now(entries, current, *, at_utc=None):
    """Current protected access; original execution validity is per dispatch."""
    now = datetime.now(UTC).isoformat().replace('+00:00', 'Z') if at_utc is None else at_utc
    for (binding, _), (_, reveal) in zip(entries, current, strict=True):
        if reveal is not None:
            require_study_authority(reveal, kind=StudyAuthorityKind.OUTCOME_REVEAL,
                subject=binding.issued_study, prerequisite_authority=binding.execution_authority,
                grantee_id=PROGRAMME_REVEAL_GRANTEE_ID, at_utc=now)
    return current


def _replay_parent_authority(binding, package, writer, *, _issued_reader=None):
    # Keep current authority before access to the issued publication, then
    # resample after that potentially heavy exact publication replay.
    _, reveal = _require_parent_authorities_current(((binding, package),), writer)[0]
    if _issued_reader is None:
        publisher = ExternalIssuedStudyPublisher(artifact_plane=writer,
            authority_store=ExternalStudyOperationAuthorityStore(writer), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
    else:
        if (type(_issued_reader) is not ExternalIssuedStudyPublisher
                or _issued_reader.artifact_plane is not writer
                or _issued_reader.grantee_id != PROGRAMME_ISSUE_GRANTEE_ID):
            raise PermissionError('qualified parent changes its actual issued-publication reader')
        writer.require_verification_context()
        publisher = _issued_reader
    published = publisher.load_executable_study(binding.issued_study.object_id,
        **({'expected_manifest': package.issued_study} if _issued_reader is not None else {}))
    if published.manifest != package.issued_study or published.publication_receipt != package.publication_receipt:
        raise PermissionError('qualified parent changes its actual issued source publication')
    _, current_reveal = _require_parent_authorities_current(((binding, package),), writer)[0]
    if current_reveal != reveal:
        raise PermissionError('qualified parent current reveal changed during publication replay')
    return published.manifest, current_reveal


def _authenticate(binding, contribution, product, writer, output_codecs, *, qualified_parent_evidence_schema_ids=(),
                  read_scope=None):
    if read_scope is None:
        with writer.read_context() as scoped:
            return _authenticate(binding, contribution, product, scoped, output_codecs,
                qualified_parent_evidence_schema_ids=qualified_parent_evidence_schema_ids,
                read_scope=_ParentReadScope(scoped))
    package = _actual_package(writer, binding.run_id, control_reader=read_scope.plan_reader)
    issued, reveal = _replay_parent_authority(binding, package, writer)
    receipts = ExternalTaskReceiptStore(writer)
    producing = receipts.read_by_receipt_id(binding.run_id, binding.task_id, binding.receipt_id)
    qualifying = receipts.read_by_receipt_id(binding.run_id, binding.qualification_task_id, binding.qualification_receipt_id)
    if (producing is None or qualifying is None
        or producing.operational_status is not OperationalStatus.SUCCEEDED
        or qualifying.operational_status is not OperationalStatus.SUCCEEDED
        or ObjectIdentity.from_record(producing.receipt_id, producing) != product.producing_receipt):
        raise PermissionError('qualified parent requires exact successful producing and qualification receipts')
    logical = _exact_output(producing, product.artifact.artifact_id)
    qualification_logical_id = f'artifact.{binding.run_id}.{binding.qualification_task_id}.{binding.qualification_output_id.removeprefix(binding.qualification_task_id + ".")}'
    qualification_logical = _exact_output(qualifying, qualification_logical_id)
    if (logical.payload_schema != product.artifact.payload_schema
        or logical.content_sha256 != product.artifact.sha256 or logical.media_type != product.artifact.media_type
        or logical.profile is not ArtifactProfile.CANONICAL_JSON
        or logical.outcome_access is not product.outcome_access or logical.visibility_ceiling is not product.visibility_ceiling
        or qualification_logical.payload_schema != ScientificAdjudicationRecord.SCHEMA):
        raise PermissionError('qualified parent changes its exact scientific product or adjudication contract')
    prefixes = tuple(sorted(manifest.capability_key for manifest in package.registry.capabilities))
    plan = read_scope.plan_reader.authenticate(package=package, issued=issued, receipt=producing,
        logical=logical, capability_prefixes=prefixes)
    qualification_plan = read_scope.plan_reader.authenticate(package=package, issued=issued, receipt=qualifying,
        logical=qualification_logical, capability_prefixes=prefixes)
    if plan != qualification_plan:
        raise PermissionError('qualified parent qualification and product have different actual execution plans')
    writer = read_scope.plan_reader.output_artifact_plane(package=package, execution_plan=plan,
        output_codecs=output_codecs)
    closure = read_scope.receipt_closure(package, plan, writer, reveal, prefixes)
    receipt_by_task = _verify_receipt_closure(writer, closure)
    if receipt_by_task[binding.task_id] != producing or receipt_by_task[binding.qualification_task_id] != qualifying:
        raise PermissionError('qualified parent substitutes a noncurrent producing or qualification attempt')
    qualification_task = read_scope.plan_reader.execution_task(execution_plan=plan, task_id=binding.qualification_task_id)
    payload = _output_payload(writer, qualifying, qualification_logical, MAX_ADJUDICATION_BYTES)
    adjudication = decode_canonical_bytes(payload, ScientificAdjudicationRecord, maximum_bytes=MAX_ADJUDICATION_BYTES)
    if (ObjectIdentity.from_record(adjudication.adjudication_id, adjudication) != binding.adjudication
        or binding.adjudication not in contribution.assessments
        or adjudication.adjudication_id != f'adjudication.{binding.run_id}.{binding.qualification_task_id}'
        or adjudication.run_id != binding.run_id or adjudication.adjudication_task_id != binding.qualification_task_id
        or adjudication.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
        or adjudication.input_materialization_ids != qualifying.input_materialization_ids
        or adjudication.output_logical_artifact_ids != tuple(sorted(value.logical_artifact_id for value in qualifying.output_logical_artifacts))
        or adjudication.required_receipt_ids != tuple(sorted(
            receipt_by_task[task_id].receipt_id for task_id in qualification_task.dependency_task_ids))
        or adjudication.evaluability is not AdjudicationEvaluability.EVALUABLE
        or adjudication.scientific_status is not ScientificStatus.SUPPORTED
        or adjudication.admission_status is not AdmissionStatus.ADMITTED
        or adjudication.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
        or adjudication.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE):
        raise PermissionError('qualified parent has no actual supported, admitted and revealed qualification')
    # Reuse the actual issued evaluator context rather than trust matching labels.
    from .execution import CampaignExecutionService
    task = qualification_task
    output = next(value for value in task.outputs if value.logical_artifact_id == qualification_logical.logical_artifact_id)
    context = CampaignExecutionService._bind_scientific_adjudication(package, plan,
        ScientificAdjudicationOutputContract(task.capability.capability_key, task.capability.capability_version,
            output.output_id, ScientificAdjudicationRecord.SCHEMA,
            MAX_ADJUDICATION_BYTES if task.capability.requested_resources.output_bytes is None else
                min(MAX_ADJUDICATION_BYTES, task.capability.requested_resources.output_bytes),
            adjudication.fixture_scope_id, adjudication.plumbing_only))
    if context is None or not adjudication.matches_context(context.context):
        raise PermissionError('qualified parent adjudication changes its actual issued scientific scope')
    if contribution.scope.system_id != package.system.system_id or contribution.scope.world_id != package.system.world.world_id:
        raise PermissionError('qualified parent contribution changes its actual system or evidence world')
    product_payload = _output_payload(writer, producing, logical, min(MAX_PARENT_BYTES, product.artifact.size_bytes))
    if len(product_payload) != product.artifact.size_bytes or sha256(product_payload).hexdigest() != product.record.object_fingerprint:
        raise PermissionError('qualified parent contribution changes its actual supplied record')
    additional = _additional_products(writer, producing, qualified_parent_evidence_schema_ids, output_codecs)
    _require_parent_authorities_current(((binding, package),), writer)
    return QualifiedParentEvidence(binding, package, plan, producing, qualifying, adjudication, product_payload, additional)


def authenticate_recursive_qualified_parents(*, spec_bindings, draft, artifact_writer, registrations, output_codecs=None):
    """Authenticate custody, then ask the installed consumer to validate science.

    The code-owned assessor must validate the exact earlier scientific scope,
    procedure and declared evaluator semantics, including any synthetic fixture
    boundary. It raises on refusal and returns None on success. Custody checks
    alone cannot promote a fixture, extend a qualification or make outcomes fresh.
    """
    with artifact_writer.read_context() as scoped:
        result = _authenticate_recursive_qualified_parents(spec_bindings=spec_bindings, draft=draft,
            artifact_writer=scoped, registrations=registrations, output_codecs=output_codecs,
            read_scope=_ParentReadScope(scoped))
        scoped.require_verification_snapshot()
    # Sample genuine current reveal after all potentially heavy final custody
    # walks, including the case where this owner nested inside another context.
    _require_parent_authorities_current(tuple((parent.binding, parent.package) for parent in result), artifact_writer)
    return result


def _authenticate_recursive_qualified_parents(*, spec_bindings, draft, artifact_writer, registrations,
                                             output_codecs, read_scope):
    selected = set(draft.selected_operation_ids)
    requirement_by_id = {value.requirement_id: value for value in draft.requirements}
    if any(value.requirement_id not in requirement_by_id for value in draft.connections):
        raise ValueError('qualified parent connection omits its scientific requirement')
    connections = tuple(value for value in draft.connections if requirement_by_id[value.requirement_id].consumer_operation_id in selected
                        and value.evidence_role is ContributionRole.QUALIFIED_EVIDENTIAL_PARENT)
    if len(spec_bindings) > MAX_PARENT_BINDINGS or any(not isinstance(value, RecursiveQualifiedParentBinding) for value in spec_bindings):
        raise ValueError('qualified-parent binding census exceeds its finite bound')
    by_external = {value.external_input_id: value for value in spec_bindings}
    if len(by_external) != len(spec_bindings) or set(by_external) != {value.external_input_id for value in connections}:
        raise PermissionError('qualified parent requires its complete exact actual-custody binding census')
    operation_by_id = {value.node_id: value for value in draft.operations}
    registration_by_selection = {value.selection.selection_id: value for value in registrations}
    prepared = []
    for connection in connections:
        binding = by_external[connection.external_input_id]
        requirement = requirement_by_id[connection.requirement_id]
        contribution = next((value for value in draft.contribution_parents if value.contribution_id == binding.contribution_id), None)
        product = None if contribution is None else next((value for value in contribution.products if value.product_id == binding.product_id), None)
        external = next((value for value in draft.external_inputs if value.input_id == binding.external_input_id), None)
        operation = operation_by_id.get(requirement.consumer_operation_id)
        registration = None if operation is None else registration_by_selection.get(operation.selection.selection_id)
        assessor = None if registration is None else registration.qualified_parent_assessor
        if (contribution is None or product is None or external is None or not callable(assessor)
            or ObjectIdentity.from_record(contribution.contribution_id, contribution) != connection.supplier_contribution
            or connection.supplier_product_id != product.product_id
            or product.role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
            or product.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
            or product.outcome_access in {OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.PRIVILEGED_TRUTH}
            or ContributionRole.QUALIFIED_EVIDENTIAL_PARENT not in requirement.permitted_roles
            or external.expected_content_sha256 != product.artifact.sha256
            or external.payload_schema != product.artifact.payload_schema
            or external.outcome_access is not product.outcome_access or external.visibility_ceiling is not product.visibility_ceiling
            or product.artifact.size_bytes > external.maximum_size_bytes):
            raise PermissionError('qualified parent lacks its exact selected scientific role or code-owned scope assessor')
        prepared.append((binding, requirement, connection, contribution, product, assessor,
                         registration.qualified_parent_evidence_schema_ids,
                         registration.qualified_parent_prior_execution_bindings,
                         registration.qualified_parent_prior_execution_scope_validator))
    schemas_by_external = {}
    for binding, _, _, _, _, _, schemas, _, _ in prepared:
        combined = tuple(sorted(set((*schemas_by_external.get(binding.external_input_id, ()), *schemas))))
        if len(combined) > 4:
            raise PermissionError('qualified parent companion declarations exceed their finite combined census')
        schemas_by_external[binding.external_input_id] = combined
    evidence = {}
    prior_cache = {}
    for binding, requirement, connection, contribution, product, assessor, _, prior_projection, prior_scope in prepared:
        parent = evidence.setdefault(binding.external_input_id, None)
        if parent is None:
            parent = _authenticate(binding, contribution, product, artifact_writer, output_codecs or {},
                qualified_parent_evidence_schema_ids=schemas_by_external[binding.external_input_id],
                read_scope=read_scope)
            evidence[binding.external_input_id] = parent
        else:
            _replay_parent_authority(binding, parent.package, artifact_writer)
            artifact_writer.require_verification_context()
        if prior_projection is not None:
            requests = prior_projection(parent)
            if (type(requests) is not tuple or not requests or len(requests) > MAX_PRIOR_EXECUTIONS
                    or any(type(value) is not RecursivePriorExecutionBinding for value in requests)
                    or len({value.binding_id for value in requests}) != len(requests)
                    or len({(value.run_id, value.task_id) for value in requests}) != len(requests)):
                raise PermissionError('qualified parent prior executions lack their bounded exhaustive exact locator census')
            prior = []
            for request in requests:
                key = request.fingerprint()
                if key not in prior_cache:
                    prior_cache[key] = _authenticate_prior_execution(request, artifact_writer, output_codecs or {},
                        scope_validator=prior_scope, parent_evidence=parent, read_scope=read_scope)
                else:
                    cached = prior_cache[key]
                    package, plan, receipt, _, _, _ = _prior_execution_entry(request, artifact_writer,
                        output_codecs or {}, read_scope)
                    if (package != cached.package or plan != cached.execution_plan
                            or receipt not in cached.receipts):
                        raise PermissionError('cached prior execution changes its original current custody')
                    scope_parent = parent
                    if request.scope_output_schema_ids:
                        scope_parent = replace(parent, prior_scope_products=tuple(product for product in
                            prior_cache[key].additional_products if product.logical.payload_schema in request.scope_output_schema_ids))
                    if prior_scope(parent_evidence=scope_parent, binding=request,
                            package=prior_cache[key].package, execution_plan=prior_cache[key].execution_plan) is not None:
                        raise PermissionError('cached prior execution scope validator returned an unsupported verdict')
                prior.append(prior_cache[key])
            parent = replace(parent, prior_executions=tuple(prior))
            evidence[binding.external_input_id] = parent
        verdict = assessor(requirement=requirement, connection=connection, contribution=contribution,
                           product=product, parent_evidence=parent)
        if verdict is not None:
            raise PermissionError('qualified parent assessor must validate by raising on refusal and returning None')
    result = tuple(evidence[key] for key in sorted(evidence))
    return result
