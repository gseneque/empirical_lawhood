# SPDX-License-Identifier: MPL-2.0
"""Actual issued custody for the protected E4 factorial consumer.

This owner composes existing issue, grant, ordinary receipt, recovery, native
completion and qualified-parent readers. It neither issues authority nor
repairs old acquisitions. In particular a later byte-identical criteria
product cannot replace the producer pinned in an original issued design.
"""

from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace

from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader, authenticate_current_execution_plan, require_current_result_receipt_outputs
from empirical_lawhood.api.matrix_scheduled_programme_runtime import authenticate_programme_qualified_parent
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.api.recursive_qualified_parents import (
    _actual_package, _collect_receipt_closure, _output_payload, _prior_native_subwork,
    _semantic_writer, _verify_receipt_closure,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.study_issue import (
    ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore,
    PROGRAMME_EXECUTION_GRANTEE_ID, PROGRAMME_ISSUE_GRANTEE_ID,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.study_issue import StudyAuthorityKind, require_study_authority
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recovery import RunRecoveryIndex, TaskRecoveryDisposition, build_run_recovery_index
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding, RecursivePriorNativeBinding

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import NAMESPACE as COMPACT, ScheduledCompactBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_qualification import _qualification
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import (
    ScheduledProgrammeAcquisitionAdmissionConfig, validate_acquisition_root,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import (
    ScheduledProgrammeAcquisitionWaveCustody, acquisition_phase_roles, validate_acquisition_operation_census, validate_acquisition_wave_custody,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import ScheduledProgrammeConfirmationParentBinding
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import ScheduledFactorialSpecification, validate_factorial_inputs
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import (
    ScheduledFactorialCaseCustody, ScheduledFactorialConfirmationConfig, ScheduledFactorialCriteriaBinding, ScheduledFactorialCriteriaConfig,
    ScheduledFactorialConfirmationInputSeal, ScheduledFactorialConfirmationSealConfig,
    INPUT_SEAL, ScheduledFactorialProtectedWorker, ScheduledFactorialWaveCustody, case_custody_state, confirmation_input_seal, input_seal_node_id,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation_custody import (
    VerifiedFactorialInvocation, require_original_criteria_design,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgramme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import ScheduledProgrammeReduction, ScheduledProgrammeWaveResult, reduce_programme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionDataBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledCausalPrefix, identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore


def _live_package(writer, run_id):
    """Replay live execution and original issue on every use, including expiry."""
    package = _actual_package(writer, run_id)
    if type(package) is not ExperimentPackage or package.run_plan_id != run_id:
        raise PermissionError("factorial custody requires the actual ordinary issued experiment package")
    issued = ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study)
    store = ExternalStudyOperationAuthorityStore(writer)
    execution = store.load(package.execution_authority.authority_id)
    if execution != package.execution_authority:
        raise PermissionError("factorial custody changes the actual stored original execution grant")
    require_study_authority(execution, kind=StudyAuthorityKind.EXPERIMENT_EXECUTION, subject=issued,
        prerequisite_authority=ObjectIdentity.from_record(package.scientific_approval.authorization_id, package.scientific_approval),
        grantee_id=PROGRAMME_EXECUTION_GRANTEE_ID, at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"))
    published = ExternalIssuedStudyPublisher(artifact_plane=writer, authority_store=store,
        grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(issued.object_id)
    if published.manifest != package.issued_study or published.publication_receipt != package.publication_receipt:
        raise PermissionError("factorial custody changes the genuine original issued source publication")
    return package


def _ordinary_execution(writer, run_id, locator=None):
    package = _live_package(writer, run_id)
    plan = authenticate_current_execution_plan(package=package, issued=package.issued_study, run_id=run_id, writer=writer)
    if type(plan) is not ExecutionPlan:
        raise PermissionError("factorial custody cannot substitute a development or candidate execution plan")
    _require_locator(package, plan, run_id, locator)
    return package, plan


def _require_locator(package, plan, run_id, locator):
    if locator is not None and (locator.run_id != run_id
            or locator.package != ObjectIdentity.from_record(package.package_id, package)
            or locator.issued_study != ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study)
            or locator.execution_authority != ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority)
            or locator.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)):
        raise PermissionError("factorial custody substitutes an original issued package/plan/grant locator")


def _manifest(writer, relative):
    raw = read_bounded_bytes(writer.root.resolve(relative+".manifest.json", for_write=False),
        maximum_bytes=writer.custody_limits.manifest_bytes)
    manifest = decode_artifact_manifest(raw, maximum_bytes=writer.custody_limits.manifest_bytes)
    physical = manifest.materialization
    if (physical.relative_path != relative or physical.storage_root_id != writer.root.contract.storage_root_id
            or physical.compression != "none" or physical.partition_selector is not None or manifest.publication is None):
        raise PermissionError("factorial custody changes original exact publication location or complete physical member")
    read_publication_metadata(writer, manifest)
    return manifest


def _publication(writer, manifest):
    relative = manifest.materialization.relative_path+".manifest.json"
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=writer.custody_limits.manifest_bytes)
    return ArtifactWriteResult(manifest.logical, manifest.materialization,
        writer._manifest_materialization(logical_artifact_id=manifest.logical.logical_artifact_id, relative_path=relative, payload=raw), False)


def _original_external(writer, run_id, spec):
    relative, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
    manifest = _manifest(writer, relative)
    logical, physical = manifest.logical, manifest.materialization
    if (logical.logical_artifact_id != spec.logical_artifact_id
            or any(expected is not None and actual != expected for actual, expected in (
                (logical.content_sha256, spec.expected_content_sha256), (logical.payload_schema, spec.expected_payload_schema),
                (logical.media_type, spec.expected_media_type), (physical.size_bytes, spec.expected_size_bytes),
                (logical.visibility_ceiling, spec.expected_visibility_ceiling), (logical.outcome_access, spec.expected_outcome_access)))
            or spec.identity_scope_sha256 is not None and not any(
                value.identity.object_fingerprint == spec.identity_scope_sha256 for value in logical.lineage_parents)):
        raise PermissionError("factorial original task changes its exact frozen external input metadata")
    return manifest


def _expected_inputs(writer, run_id, task, dependencies):
    from empirical_lawhood.infrastructure.execution import LocalScheduler
    by_task = {}
    for receipt in dependencies:
        physical = {value.logical_artifact_id: value for value in receipt.output_materializations}
        by_task[receipt.task_id] = tuple(VerifiedArtifactInput(value, physical[value.logical_artifact_id])
            for value in receipt.output_logical_artifacts)
    if set(by_task) != set(task.dependency_task_ids) or len(by_task) != len(dependencies):
        raise PermissionError("factorial original inputs lack their exact complete dependency producer census")
    expected = {value.materialization.materialization_id for value in LocalScheduler._dependency_outputs(task, by_task)}
    expected.update(_original_external(writer, run_id, spec).materialization.materialization_id for spec in task.external_inputs)
    return tuple(sorted(expected))


def _original_config(writer, run_id, task, kind):
    spec, = (value for value in task.external_inputs if value.logical_artifact_id == task.capability.config.artifact_id)
    manifest = _original_external(writer, run_id, spec)
    logical, physical = manifest.logical, manifest.materialization
    if ((logical.logical_artifact_id, logical.payload_schema, logical.content_sha256,
            logical.media_type, logical.visibility_ceiling, logical.outcome_access)
            != (spec.logical_artifact_id, kind.SCHEMA, task.capability.config.content_sha256,
                "application/json", VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
            or spec.expected_payload_schema != kind.SCHEMA or spec.expected_content_sha256 != logical.content_sha256
            or task.capability.config.config_schema != kind.SCHEMA
            or task.capability.config.content_sha256 != logical.content_sha256):
        raise PermissionError("factorial original configuration changes the exact issued blind input contract")
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=physical.size_bytes)
    if (record.canonical_bytes() != raw or len(raw) != physical.size_bytes
            or sha256(raw).hexdigest() != physical.physical_sha256
            or record.fingerprint() != logical.content_sha256 or record.config_id != task.capability.config.config_id):
        raise PermissionError("factorial original configuration differs from actual source bytes or task binding")
    return record, _publication(writer, manifest)


def _ordinary_product(writer, binding, plan_reader):
    """Authenticate a blind ordinary product without broadening sealed replay."""
    if type(binding) not in (ScheduledFactorialCriteriaBinding, ScheduledProgrammeConfirmationParentBinding):
        raise PermissionError("factorial ordinary product requires its closed original criteria or global-parent binding")
    binding.__post_init__()
    locator = getattr(binding, "prior_execution", None)
    package = _live_package(writer, binding.receipt.run_id)
    stored = ExternalTaskReceiptStore(writer).read_by_receipt_id(binding.receipt.run_id,
        binding.receipt.task_id, binding.receipt.receipt_id)
    if stored != binding.receipt or stored.operational_status is not OperationalStatus.SUCCEEDED:
        raise PermissionError("factorial ordinary product lacks its exact actual successful producing receipt")
    plan = plan_reader.authenticate(package=package, issued=package.issued_study, receipt=stored,
        logical=binding.publication.logical, capability_prefixes=tuple(value.capability_key for value in package.registry.capabilities))
    if plan != binding.execution_plan:
        raise PermissionError("factorial ordinary product substitutes its genuine original complete plan")
    _require_locator(package, plan, stored.run_id, locator)
    task = require_current_result_receipt_outputs(receipt=stored, logical=binding.publication.logical,
        execution_plan=plan, capability_prefixes=tuple(value.capability_key for value in package.registry.capabilities))
    if task.dependency_task_ids or stored.input_materialization_ids != _expected_inputs(writer, stored.run_id, task, ()):
        raise PermissionError("factorial ordinary blind freeze producer changes its complete original external input census")
    record = binding.record if type(binding) is ScheduledFactorialCriteriaBinding else binding.parent
    config = record.configuration if type(binding) is ScheduledFactorialCriteriaBinding else binding.configuration
    actual_config, publication = _original_config(writer, stored.run_id, task, type(config))
    if actual_config != config or (publication.logical, publication.materialization) != (
            binding.configuration_publication.logical, binding.configuration_publication.materialization):
        raise PermissionError("factorial ordinary producer changes its original actual configuration")
    for original, publication in ((record, binding.publication), (stored, binding.receipt_publication),
            (plan, binding.execution_plan_publication), (config, binding.configuration_publication)):
        authenticate_publication(writer, publication, original)
    return package


def _task_state(writer, package, plan, index, task):
    """Read finite original candidates; never reconcile, retry or infer no entry."""
    recovery, receipts = ExternalRunRecoveryStore(writer), ExternalTaskReceiptStore(writer)
    binding = index.task(task.task_id)
    observed = []
    prefixes = tuple(value.capability_key for value in package.registry.capabilities)
    for candidate in binding.attempts:
        receipt = receipts.read(package.run_plan_id, task.task_id, candidate.attempt_id)
        event = recovery.read_event(index, candidate.event_relative_path)
        if receipt is not None:
            if (receipt.run_id != package.run_plan_id or receipt.task_id != task.task_id
                    or receipt.attempt_id != candidate.attempt_id or receipt.implementation_commit != plan.implementation_commit):
                raise PermissionError("factorial recovery changes its exact original task attempt receipt")
            if receipt.operational_status is OperationalStatus.SUCCEEDED:
                if not receipt.output_logical_artifacts:
                    raise PermissionError("factorial successful phase omits original ordinary outputs")
                require_current_result_receipt_outputs(receipt=receipt, logical=receipt.output_logical_artifacts[0],
                    execution_plan=plan, capability_prefixes=prefixes)
            if event is not None and (event.receipt_id != receipt.receipt_id or event.receipt_sha256 != receipt.fingerprint()
                    or event.attempt_id != receipt.attempt_id or event.task_id != task.task_id):
                raise PermissionError("factorial recovery event contradicts its actual ordinary receipt")
            observed.append((candidate.ordinal, "SUCCEEDED" if receipt.operational_status is OperationalStatus.SUCCEEDED else "FAILED",
                receipt, () if receipt.operational_status is OperationalStatus.SUCCEEDED else tuple(receipt.reason_codes)))
        elif event is not None:
            if event.task_id != task.task_id or event.attempt_id != candidate.attempt_id or event.attempt_ordinal != candidate.ordinal:
                raise PermissionError("factorial recovery event substitutes an original finite attempt")
            if event.disposition is TaskRecoveryDisposition.SUCCEEDED:
                raise PermissionError("factorial successful recovery event lacks its actual ordinary receipt")
            observed.append((candidate.ordinal, event.disposition.value, None, event.reason_codes))
    if sum(value[1] == "SUCCEEDED" for value in observed) > 1 or any(value[1] == "SUCCEEDED" for value in observed[:-1]):
        raise PermissionError("factorial original task has conflicting successful or post-success attempts")
    if not task.outputs or len({value.visibility_ceiling for value in task.outputs}) != 1:
        raise PermissionError("factorial original task lacks its exact common output visibility")
    contacts = ExternalNativeEffectContactStore(plane=writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=task.outputs[0].visibility_ceiling, outcome_access=task.capability.requested_outcome_access)
    contact = contacts.read(package.run_plan_id, task.task_id)
    if contact is not None:
        if (contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or contact.implementation_commit != plan.implementation_commit
                or contact.attempt_id not in {value.attempt_id for value in binding.attempts}):
            raise PermissionError("factorial native contact substitutes original full task/commit/finite attempt")
        dependencies = tuple(receipt for dependency in task.dependency_task_ids for candidate in index.task(dependency).attempts
            if (receipt := receipts.read(package.run_plan_id, dependency, candidate.attempt_id)) is not None
            and receipt.receipt_id in contact.dependency_receipt_ids)
        if (contact.input_materialization_ids != _expected_inputs(writer, package.run_plan_id, task, dependencies)
                or len(dependencies) != len(task.dependency_task_ids)
                or any(value.operational_status is not OperationalStatus.SUCCEEDED for value in dependencies)
                or tuple(sorted(value.receipt_id for value in dependencies)) != contact.dependency_receipt_ids):
            raise PermissionError("factorial native contact changes exact original inputs or ordinary dependency lineage")
        completed = tuple(value for value in observed if value[1] == "SUCCEEDED" and value[2].attempt_id == contact.attempt_id)
        if not completed:
            return "UNKNOWN", None, contact, ("ACTUAL_NATIVE_CONTACT_WITHOUT_ORDINARY_COMPLETION",)
        if contact.input_materialization_ids != completed[0][2].input_materialization_ids:
            raise PermissionError("factorial native completion changes its exact original entered inputs")
    if observed:
        _, state, receipt, reasons = observed[-1]
        return state, receipt, contact, reasons
    nonattempt = recovery.read_event(index, binding.nonattempt_event_relative_path)
    if nonattempt is not None:
        if nonattempt.task_id != task.task_id or nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED:
            raise PermissionError("factorial nonattempt custody substitutes original task or actual disposition")
        return "UNENTERED", None, None, nonattempt.reason_codes
    return "UNKNOWN", None, contact, ("NO_ORIGINAL_TERMINAL_CUSTODY",)


def _wave_metadata(writer, locator, config, bank, current_root, *, parent_writer, parent_plan_reader):
    """Authenticate original blind admission/criteria chronology, without results."""
    package, plan = _ordinary_execution(writer, locator.run_id, locator)
    wave, = (value for value in config.programme.waves if value.wave_id == locator.wave_id)
    opening, = (value for value in plan.tasks if value.task_id == wave.wave_id+".open")
    original, _ = _original_config(writer, locator.run_id, opening, ScheduledProgrammeAcquisitionAdmissionConfig)
    scope = original.scope
    root = package.issued_study.candidate.authoring_package.base.draft
    if (scope.programme != config.programme or scope.wave != wave or scope.bank != config.bank
            or scope.qualified_parent != config.criteria.record.configuration.qualified_parent
            or scope.global_root.system != current_root.system or scope.global_root.experiment != current_root.experiment):
        raise PermissionError("factorial acquisition substitutes original global study, full programme or local admission scope")
    require_original_criteria_design(root, config.criteria)
    for pin in (config.criteria.record.identity, ObjectIdentity.from_record(config.criteria.receipt.receipt_id, config.criteria.receipt), config.criteria.identity):
        _qualification(root, SimpleNamespace(qualifications=package.issued_study.materialization_qualifications),
            pin.object_id, pin.object_schema, pin.object_fingerprint, OutcomeAccess.OUTCOME_BLIND,
            VisibilityCeiling.PROSPECTIVE, pin.object_version)
    parent_package = _ordinary_product(parent_writer, original.global_parent_binding, parent_plan_reader)
    roles = acquisition_phase_roles(config.programme.mode)
    wanted = {COMPACT+"."+root_id+"."+role for root_id in wave.root_ids for role in roles}
    if {value.task_id for value in plan.tasks} != wanted | {wave.wave_id+".open", wave.wave_id+".collect"}:
        raise PermissionError("factorial acquisition changes its original complete eleven-phase task census")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import ScheduledProgrammeAcquisitionCollectorConfig
    collector_task, = (value for value in plan.tasks if value.task_id == wave.wave_id+".collect")
    collector_config, config_publication = _original_config(writer, locator.run_id, collector_task, ScheduledProgrammeAcquisitionCollectorConfig)
    if (collector_config.programme != config.programme.identity or collector_config.wave != wave
            or collector_config.scope != scope.identity or collector_config.bank != config.bank
            or collector_config.mode != config.programme.mode):
        raise PermissionError("factorial original collector configuration changes its exact admitted whole-group scope")
    validate_acquisition_operation_census(config.programme, wave, collector_config.operation, plan)
    validate_acquisition_root(scope, root, bank, execution_plan=plan,
        protocol=package.issued_study.candidate.base_candidate.base_candidate.protocol)
    return package, plan, wave, collector_task, collector_config, config_publication, parent_package


def _wave(writer, locator, config, bank, current_root, output_codecs, *, parent_writer, parent_plan_reader):
    package, plan, wave, collector_task, collector_config, config_publication, parent_package = _wave_metadata(
        writer, locator, config, bank, current_root, parent_writer=parent_writer, parent_plan_reader=parent_plan_reader)
    roles = acquisition_phase_roles(config.programme.mode)
    wanted = {COMPACT+"."+root_id+"."+role for root_id in wave.root_ids for role in roles}
    recovery = ExternalRunRecoveryStore(writer)
    authorities = tuple(ObjectIdentity.from_record(key, value) for key, value in (
        (package.scientific_approval.authorization_id, package.scientific_approval),
        (package.execution_authority.authority_id, package.execution_authority)))
    expected = build_run_recovery_index(plan, run_id=locator.run_id, wave_id="wave."+package.package_id, authority_identities=authorities)
    index = recovery.read_index(expected.index_relative_path, expected_schema=RunRecoveryIndex.SCHEMA)
    if index != expected:
        raise PermissionError("factorial acquisition changes original finite recovery plan or actual authority census")
    terminal = recovery.read_terminal(index)
    by_task = {value.task_id: value for value in plan.tasks}
    states = {task_id: _task_state(writer, package, plan, index, by_task[task_id]) for task_id in sorted(wanted | {wave.wave_id+".collect"})}
    cases = []
    for case in config.programme.cases:
        if case.root_id not in wave.root_ids:
            continue
        rows = tuple((role, states[COMPACT+"."+case.root_id+"."+role]) for role in roles)
        phase_states = tuple((role, row[0]) for role, row in rows)
        cases.append(ScheduledFactorialCaseCustody(case.root_id, case.independent_group_id, case_custody_state(phase_states), phase_states,
            tuple(ObjectIdentity.from_record(row[1].receipt_id, row[1]) for _, row in rows if row[1] is not None),
            tuple(ObjectIdentity.from_record(_manifest(writer, ExternalNativeEffectContactStore._path(row[2].run_id, row[2].task_id))
                .logical.logical_artifact_id, row[2]) for _, row in rows if row[2] is not None),
            tuple(sorted({reason for _, row in rows for reason in row[3]}))))
    collector_state, collector, _, reasons = states[wave.wave_id+".collect"]
    if terminal is None:
        reasons = tuple(sorted({*reasons, "MISSING_ORIGINAL_RUN_TERMINAL"}))
    status = ScheduledFactorialWaveCustody(wave.wave_id, collector_state,
        None if collector is None else ObjectIdentity.from_record(collector.receipt_id, collector),
        None if terminal is None else ObjectIdentity.from_record(terminal.terminal_event_id, terminal),
        None if terminal is None else terminal.operational_status, reasons)
    if (collector_state != "SUCCEEDED" or any(value.state != "COMPLETED" for value in cases)
            or terminal is None or terminal.operational_status != "SUCCEEDED"):
        return package, tuple(cases), status, None, None, parent_package
    prefixes = tuple(value.capability_key for value in package.registry.capabilities)
    semantic = _semantic_writer(package, plan, writer, output_codecs)
    closure = _collect_receipt_closure(package, plan, semantic, None, prefixes)
    by_receipt = _verify_receipt_closure(semantic, closure)
    if by_receipt.get(collector.task_id) != collector:
        raise PermissionError("factorial collector is not the actual current complete original attempt")
    logical, = (value for value in collector.output_logical_artifacts if value.payload_schema == ScheduledProgrammeWaveResult.SCHEMA)
    physical, = (value for value in collector.output_materializations if value.logical_artifact_id == logical.logical_artifact_id)
    result = decode_canonical_bytes(_output_payload(semantic, collector, logical, physical.size_bytes), ScheduledProgrammeWaveResult,
        maximum_bytes=physical.size_bytes)
    custody = ScheduledProgrammeAcquisitionWaveCustody("custody.factorial."+wave.wave_id, wave.wave_id, result.identity,
        _publication(writer, _manifest(writer, physical.relative_path)), collector,
        _publication(writer, _manifest(writer, ExternalTaskReceiptStore._relative_path(locator.run_id, collector.task_id, collector.attempt_id))),
        locator.execution_plan, _publication(writer, _manifest(writer, f"runs/{locator.run_id}/plans/execution-plan.json")),
        collector_config, config_publication, collector_task)
    validate_acquisition_wave_custody(config.programme, result, custody, plan)
    for row in result.cases:
        for header in row.ordinary_receipts:
            receipt = by_receipt.get(header.task_id)
            if receipt is None or receipt.receipt_id != header.receipt_id or not set(header.output_materialization_ids) <= {
                    value.materialization_id for value in receipt.output_materializations}:
                raise PermissionError("factorial original wave changes actual eleven-phase receipt lineage")
    natives = tuple(RecursivePriorNativeBinding(COMPACT+"."+row.root_id+"."+native.phase,
        native.definition, native.completion, native.receipt) for row in result.cases for native in row.native if native.disposition == "COMPLETED")
    request = RecursivePriorExecutionBinding("binding.factorial."+wave.wave_id, locator.issued_study, locator.execution_authority,
        locator.package, locator.execution_plan, locator.run_id, collector.task_id, ObjectIdentity.from_record(collector.receipt_id, collector), logical.logical_artifact_id,
        result.identity, native_subwork=natives, record_id_field="result_id")
    _prior_native_subwork(semantic, request, plan, by_receipt)
    return package, tuple(cases), status, result, (semantic, by_receipt), parent_package


def prepare_factorial_task(supplier, context, runner):
    """Prepare one exact installed pure worker; never issue, recover or contact."""
    if type(runner) is not ScheduledFactorialProtectedWorker or runner.verified is not None:
        raise PermissionError("factorial preparation requires its unprepared installed worker")
    current = supplier._current(context, runner)
    # Reuse only immutable blind parents here. Acquisition payloads and every
    # live issue/grant/receipt check continue through their existing readers.
    with supplier.writer.verification_scope() as parent_writer:
        return _prepare_factorial_task(supplier, context, runner, current,
            parent_writer=parent_writer, parent_plan_reader=CurrentResultPlanReader(parent_writer))


def _current_input_seal(supplier, context, plan, config, dependencies):
    """Authenticate the exact blind same-plan dependency, not new criteria."""
    expected = confirmation_input_seal(config)
    node = input_seal_node_id(config.specification)
    if set(dependencies) != {node}:
        raise PermissionError("factorial assessment lacks its exact internal input-design seal dependency")
    receipt = dependencies[node]
    if (receipt.operational_status is not OperationalStatus.SUCCEEDED
            or not any(value.check_id == "original-full64-factorial-confirmation-input-design-seal" and value.passed
                for value in receipt.checks)):
        raise PermissionError("factorial input-design seal lacks its actual successful ordinary producer")
    logical, = receipt.output_logical_artifacts
    task = require_current_result_receipt_outputs(receipt=receipt, logical=logical, execution_plan=plan,
        capability_prefixes=(INPUT_SEAL,))
    if (task.task_id != node or task.dependency_task_ids
            or receipt.input_materialization_ids != _expected_inputs(supplier.writer, context.run_id, task, ())):
        raise PermissionError("factorial input-design seal changes its complete blind original input census")
    actual_config, _ = _original_config(supplier.writer, context.run_id, task, ScheduledFactorialConfirmationSealConfig)
    if actual_config != expected.configuration:
        raise PermissionError("factorial input-design seal changes original criteria/receipt, acquisition roster or paired identities")
    physical, = receipt.output_materializations
    manifest = _manifest(supplier.writer, physical.relative_path)
    if ((manifest.logical, manifest.materialization) != (logical, physical)
            or logical.payload_schema != ScheduledFactorialConfirmationInputSeal.SCHEMA
            or logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise PermissionError("factorial input-design seal changes its exact blind output custody")
    if supplier._control(manifest, ScheduledFactorialConfirmationInputSeal, physical.size_bytes) != expected:
        raise PermissionError("factorial input-design seal differs from the exact original selected metadata")
    return expected.identity


def _prepare_factorial_task(supplier, context, runner, current, *, parent_writer, parent_plan_reader):
    package, plan, task = current
    dependencies, controls = supplier._inputs(context, task)
    freezing = runner.role == "freeze"
    sealing = runner.role == "seal"
    assessing = runner.role == "assess"
    kind = ScheduledFactorialCriteriaConfig if freezing else ScheduledFactorialConfirmationSealConfig if sealing else ScheduledFactorialConfirmationConfig
    config = supplier._control(controls[context.config.artifact_id], kind, controls[context.config.artifact_id].materialization.size_bytes)
    bank = supplier._control(controls[config.bank.object_id], ScheduledCompactBank, controls[config.bank.object_id].materialization.size_bytes)
    programme_manifest, = (value for value in controls.values() if value.logical.payload_schema == ScheduledProgramme.SCHEMA)
    specification_manifest, = (value for value in controls.values() if value.logical.payload_schema == ScheduledFactorialSpecification.SCHEMA)
    if (supplier._control(programme_manifest, ScheduledProgramme, programme_manifest.materialization.size_bytes) != config.programme
            or supplier._control(specification_manifest, ScheduledFactorialSpecification, specification_manifest.materialization.size_bytes) != config.specification):
        raise PermissionError("factorial preparation changes complete original programme or explicit statistical specification")
    declaration = config.qualified_parent if freezing else config.criteria.record.configuration.qualified_parent
    parent = authenticate_programme_qualified_parent(supplier.writer, bank, declaration, supplier.output_codecs)
    cases, waves, prior_packages = (), (), []
    input_seal = _current_input_seal(supplier, context, plan, config, dependencies) if assessing else None
    if not freezing:
        criteria_manifest, = (value for value in controls.values() if value.logical.payload_schema == config.criteria.SCHEMA)
        if supplier._control(criteria_manifest, type(config.criteria), criteria_manifest.materialization.size_bytes) != config.criteria:
            raise PermissionError("factorial preparation changes actual original freeze binding bytes")
        prior_packages.append(_ordinary_product(parent_writer, config.criteria, parent_plan_reader))
        root = package.issued_study.candidate.authoring_package.base.draft
        require_original_criteria_design(root, config.criteria)
        all_cases, all_waves, results, payloads = [], [], [], {}
        selected = config.assessment if sealing else config
        for locator in selected.acquisitions:
            if sealing:
                original, _, _, _, _, _, global_parent = _wave_metadata(supplier.writer, locator, selected, bank, root,
                    parent_writer=parent_writer, parent_plan_reader=parent_plan_reader)
                prior_packages.extend((original, global_parent))
                continue
            original, rows, status, result, producing, global_parent = _wave(supplier.writer, locator, config, bank, root, supplier.output_codecs,
                parent_writer=parent_writer, parent_plan_reader=parent_plan_reader)
            prior_packages.extend((original, global_parent))
            all_cases.extend(rows); all_waves.append(status)
            if result is not None:
                results.append(result)
                writer, receipts = producing
                for receipt in receipts.values():
                    for logical in receipt.output_logical_artifacts:
                        codec = {ScheduledCausalPrefix.SCHEMA: ScheduledCausalPrefix, ScheduledResponseScore.SCHEMA: ScheduledResponseScore}.get(logical.payload_schema)
                        if codec is not None:
                            physical, = (value for value in receipt.output_materializations if value.logical_artifact_id == logical.logical_artifact_id)
                            record = decode_canonical_bytes(_output_payload(writer, receipt, logical, physical.size_bytes), codec, maximum_bytes=physical.size_bytes)
                            if identity(record) in payloads:
                                raise PermissionError("factorial paired source duplicates its actual original producing record")
                            payloads[identity(record)] = record
        cases, waves = tuple(sorted(all_cases, key=lambda row: row.root_id)), tuple(all_waves)
        if assessing and config.data is not None:
            data_manifest, = (value for value in controls.values() if value.logical.payload_schema == ScheduledRevisionDataBank.SCHEMA)
            reduction_manifest, = (value for value in controls.values() if value.logical.payload_schema == ScheduledProgrammeReduction.SCHEMA)
            for manifest in (data_manifest, reduction_manifest):
                if (manifest.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                        or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
                    raise PermissionError("factorial paired inputs change original sealed prospective access")
                supplier.writer.verify_manifest(manifest)
            def read(manifest, codec):
                raw = read_bounded_bytes(supplier.writer.root.resolve(manifest.materialization.relative_path, for_write=False),
                    maximum_bytes=manifest.materialization.size_bytes)
                return decode_canonical_bytes(raw, codec, maximum_bytes=manifest.materialization.size_bytes)
            data, reduction = read(data_manifest, ScheduledRevisionDataBank), read(reduction_manifest, ScheduledProgrammeReduction)
            if data.identity != config.data or ObjectIdentity.from_record(reduction.reduction_id, reduction) != config.reduction:
                raise PermissionError("factorial paired input content differs from its exact frozen selection")
            # Reductions are reproduced from authenticated original collector
            # records, never from a caller's primary-only summary or fine labels.
            validate_factorial_inputs(config.specification, config.programme, reduction, data)
            if len(results) == len(config.programme.waves):
                original_reduction = reduce_programme(config.programme, tuple(results), reduction_id=reduction.reduction_id,
                    authenticate_wave=lambda result: None)
                if reduction != original_reduction:
                    raise PermissionError("factorial reduction differs from the actual complete original wave corpus")
                for row in data.cases:
                    if any(record is not None and payloads.get(identity(record)) != record for record in (row.causal_prefix, row.score)):
                        raise PermissionError("factorial paired bank substitutes an original actual prefix/score producer")
    # Custody reuse never retains a live authority verdict. Recheck every
    # original run and the current exact selected reveal before handing off.
    originals = {}
    for original in prior_packages:
        if originals.setdefault(original.run_plan_id, original) != original:
            raise PermissionError("factorial repeated original run changes its actual issued package")
    for original in originals.values():
        if _live_package(supplier.writer, original.run_plan_id) != original:
            raise PermissionError("factorial original authority/source controls changed during preparation")
    if assessing:
        final_dependencies, _ = supplier._inputs(context, task)
        if _current_input_seal(supplier, context, plan, config, final_dependencies) != input_seal:
            raise PermissionError("factorial input-design seal changed during original corpus replay")
    # The qualified calibration corpus has its own current reveal grant and
    # applicable original executions. Reauthenticate through its existing
    # owning reader rather than retaining the entry-time authority verdict.
    if authenticate_programme_qualified_parent(supplier.writer, bank, declaration, supplier.output_codecs) != parent:
        raise PermissionError("factorial qualified calibration parent changed during preparation")
    if supplier._current(context, runner) != (package, plan, task):
        raise PermissionError("factorial current issued controls changed during original corpus replay")
    reveal = None
    if assessing:
        actual = ExternalStudyOperationAuthorityStore(supplier.writer).load(supplier.reveal_authority_id)
        reveal = ObjectIdentity.from_record(actual.authority_id, actual)
    verified = VerifiedFactorialInvocation(config.identity, config.programme.identity, config.bank,
        ObjectIdentity.from_record(package.package_id, package), ObjectIdentity.from_record(plan.execution_plan_id, plan),
        ObjectIdentity.from_record(task.task_id, task), ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
        reveal, context.input_materialization_ids, context.dependency_receipt_ids, parent.declaration,
        None if freezing else config.criteria.identity, cases, waves,
        config.reduction if assessing else None, config.data if assessing else None, input_seal)
    return ScheduledFactorialProtectedWorker(runner.role, runner.manifest, verified)
