# SPDX-License-Identifier: MPL-2.0
"""Explicit separate E4 attempts, preserving original incomplete native custody."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import OperationalFailureClass
from empirical_lawhood.runtime.native_continuation_execution import (
    DevelopmentNativeContinuation, DevelopmentNativeContinuationRecoveryIndex,
)
from empirical_lawhood.runtime.native_continuation_proposal import DevelopmentNativeContinuationProposal
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, TaskRecoveryDisposition

from .development_controller_repair import _contacts, require_scientific_source
from .development_output_repair import _pin
from .native_continuation_preparation import _candidate_controls, _inspect_original, _original_controls
from .retained_e3_control_repair import _read_record, observe_frozen_repair_worker, observe_frozen_worker_package_root


SUPPORTED_NATIVE_CAPABILITIES = frozenset((
    'matrix-selected-e3-e4-development.responses', 'matrix-selected-e3-e4-development.continue',
))


def continuation_relative_path(run_id):
    validate_stable_id(run_id)
    return f'runs/{run_id}/repairs/native-continuation/continuation.json'


def _require_no_other_repair(writer, run_id):
    from .development_controller_repair import repair_relative_path as controller_path
    from .development_output_repair import repair_relative_path as output_path
    for relative in (controller_path(run_id), output_path(run_id)):
        if any(writer.root.resolve(path, for_write=False).exists() for path in (relative, relative + '.manifest.json')):
            raise PermissionError('native continuation cannot replace another selected development repair')


def _census(*, writer, plan, predecessor, proposal, require_absent, continuation_index=None):
    """All original candidates stay original; exactly named contacts get a new namespace."""
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository
    from .recursive_execution import _custody_control_pins
    from .recursive_operations import operation_catalog
    if type(predecessor) is not DevelopmentRunRecoveryIndex:
        raise PermissionError('native continuation requires the unreplaced original recovery index')
    predecessor.validate_plan(plan)
    if (proposal.execution_plan, proposal.original_index, proposal.original_run_id) != (
            _pin(plan, 'execution_plan_id'), _pin(predecessor, 'recovery_index_id'), predecessor.run_id):
        raise PermissionError('native continuation substitutes its proposed original graph')
    recovery, receipts = ExternalRunRecoveryStore(writer), ExternalTaskReceiptStore(writer)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    try:
        upgrade_catalog(engine)
        closure = recovery.reconcile(predecessor, plan, SQLiteOperationalRepository(engine), receipts,
            repair_missing_events=False)
    finally:
        engine.dispose()
    completed = {row.task_id: row for row in closure.recovered_receipts}
    pins = tuple(sorted((key, _pin(row, 'receipt_id')) for key, row in completed.items()))
    if pins != proposal.completed_receipts:
        raise PermissionError('native continuation changes its reviewed completed work')
    declarations, registry, _ = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise PermissionError('native continuation changes the frozen capability registry')
    by_key = {(row.selection.capability_key, row.selection.capability_version): row for row in declarations}
    def registration(task):
        try:
            return by_key[task.capability.capability_key, task.capability.capability_version]
        except KeyError as error:
            raise PermissionError('native continuation loses an original registered task') from error
    proposed = {row.task_id: row for row in proposal.candidates}
    if any(plan.task(key).capability.capability_key not in SUPPORTED_NATIVE_CAPABILITIES for key in proposed):
        raise PermissionError('explicit native continuation currently supports only original E4 DEV response and continuation cases')
    contacts = _contacts(writer, plan)
    native_pins, refused, pending, uncontacted = [], [], [], []
    for task in plan.tasks:
        native = registration(task).native_effect
        parent = contacts.read(predecessor.run_id, task.task_id)
        receipt = completed.get(task.task_id)
        if receipt is not None:
            if native:
                expected = NativeEffectContact(predecessor.run_id, task.task_id, receipt.attempt_id,
                    _pin(plan, 'execution_plan_id'), _pin(task, 'task_id'), plan.implementation_commit,
                    receipt.input_materialization_ids,
                    tuple(sorted(completed[key].receipt_id for key in task.dependency_task_ids)))
                if parent != expected:
                    raise PermissionError('native continuation changes a completed original native contact')
                native_pins.append((task.task_id, ObjectIdentity.from_record(task.task_id, parent)))
            elif parent is not None:
                raise PermissionError('PURE original work cannot have a native contact')
            continue
        selected = proposed.get(task.task_id)
        if selected is not None:
            if not native or parent != selected.invocation.expected_parent_contact:
                raise PermissionError('native continuation loses its unchanged original incomplete contact')
        elif parent is not None:
            if (require_absent or not native or continuation_index is None
                    or parent.attempt_id not in {row.attempt_id for row in continuation_index.task(task.task_id).attempts}
                    or parent.execution_plan != _pin(plan, 'execution_plan_id')
                    or parent.execution_task != _pin(task, 'task_id')
                    or parent.implementation_commit != plan.implementation_commit):
                raise PermissionError('native continuation found an unselected original contact')
        binding = predecessor.task(task.task_id)
        if binding.maximum_attempts != 1:
            raise PermissionError('native continuation admits only one separate candidate per original pending task')
        original_attempt, = binding.attempts
        event = recovery.read_event(predecessor, original_attempt.event_relative_path)
        nonattempt = recovery.read_event(predecessor, binding.nonattempt_event_relative_path)
        if event is not None:
            if (native or nonattempt is not None or event.disposition is not TaskRecoveryDisposition.BLOCKED
                    or event.failure is None or event.failure.failure_class is not OperationalFailureClass.RESOURCE_REFUSAL
                    or event.failure.sanitized_exception_type != 'ResourceAdmissionError'):
                raise PermissionError('native continuation refuses unrelated original failed attempts')
            refused.append((task.task_id, _pin(event, 'event_id')))
        else:
            if nonattempt is not None and (nonattempt.disposition is not TaskRecoveryDisposition.NOT_ATTEMPTED
                    or nonattempt.reason_codes != ('dependency-blocked',)):
                raise PermissionError('native continuation refuses unrelated original dependency blocks')
            pending.append(task.task_id)
            if native and selected is None:
                uncontacted.append(task.task_id)
        if require_absent:
            for output in task.outputs:
                for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                    if writer.root.resolve(relative, for_write=False).exists():
                        raise PermissionError('native continuation refuses unreceipted original parent outputs')
    if not completed or not refused:
        raise PermissionError('native continuation requires retained work and the recorded PURE output refusal')
    refused_keys = {(plan.task(key).capability.capability_key, plan.task(key).capability.capability_version)
        for key, _ in refused}
    output_tasks = tuple(sorted(task.task_id for task in plan.tasks if task.task_id not in completed
        and (task.capability.capability_key, task.capability.capability_version) in refused_keys
        and task.capability.requested_resources.output_bytes is not None
        and task.capability.requested_resources.output_bytes < proposal.pure_output_bytes))
    if not set(dict(refused)) <= set(output_tasks):
        raise PermissionError('native continuation must increase every refused PURE output allowance')
    for task_id in output_tasks:
        task = plan.task(task_id)
        declared = registration(task)
        if declared.native_effect or not declared.resource_ceiling.contains(
                replace(task.capability.requested_resources, output_bytes=proposal.pure_output_bytes)):
            raise PermissionError('native continuation changes a native budget or exceeds its PURE ceiling')
    terminal = recovery.read_terminal(predecessor)
    if terminal is not None and (terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids):
        raise PermissionError('native continuation changes an incompatible original terminal')
    return dict(original_terminal=None if terminal is None else _pin(terminal, 'terminal_event_id'),
        original_controls=_custody_control_pins(writer, predecessor), completed_receipts=pins,
        completed_native_contacts=tuple(sorted(native_pins)), refused_tasks=tuple(sorted(refused)),
        pending_task_ids=tuple(sorted(pending)), uncontacted_native_task_ids=tuple(sorted(uncontacted)),
        output_task_ids=output_tasks)


def _require_original_controls(*, writer, plan, index, before_activation=False):
    """Raw old attempts stay exact; new task outputs have separate attempt receipts."""
    proof, proposal = index.repair, index.repair.proposal
    contacts = _contacts(writer, plan)
    allowed_contact_paths = set()
    if not before_activation:
        for task_id in proof.uncontacted_native_task_ids:
            path = contacts._path(index.run_id, task_id)
            allowed_contact_paths.update((path, path + '.manifest.json'))
    original = tuple(row for row in proposal.original_controls if row[0] not in allowed_contact_paths)
    actual = tuple(row for row in _original_controls(writer, plan, index.predecessor) if row[0] not in allowed_contact_paths)
    if original != actual:
        raise PermissionError('native continuation changes original primary control or contact custody')
    for candidate in proposal.candidates:
        task = plan.task(candidate.task_id)
        store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts,
            parent_contact=candidate.invocation.expected_parent_contact, completed_only=True)
        allowed_outputs = set() if before_activation else {
            path for output in task.outputs for path in (output.relative_path, output.relative_path + '.manifest.json')}
        original = tuple(row for row in candidate.original_controls if row[0] not in allowed_outputs)
        actual = tuple(row for row in _candidate_controls(store, candidate.invocation, task) if row[0] not in allowed_outputs)
        if original != actual:
            raise PermissionError('native continuation changes an original incomplete nested attempt')


def derive_native_continuation(*, writer, plan, predecessor, proposal, proposal_relative_path,
        original_source, controller, owner_instruction_sha256, external_inputs, require_access):
    _require_no_other_repair(writer, predecessor.run_id)
    worker, environment = observe_frozen_repair_worker(interpreter=proposal.worker_environment.interpreter_path,
        source_root=proposal.worker_source_root)
    if (worker, environment) != (original_source, proposal.worker_environment) or worker != proposal.worker:
        raise PermissionError('native continuation changes its original frozen worker')
    require_scientific_source(worker, controller)
    current = _inspect_original(writer=writer, plan=plan, index=predecessor,
        external_inputs=external_inputs, require_access=require_access)
    if any(getattr(proposal, key) != value for key, value in current.items()):
        raise PermissionError('native continuation proposal no longer matches its exact original custody')
    census = _census(writer=writer, plan=plan, predecessor=predecessor, proposal=proposal, require_absent=True)
    token = sha256(canonical_json_bytes((proposal.identity, controller, owner_instruction_sha256))).hexdigest()
    proof = DevelopmentNativeContinuation('continuation.development-native.' + token[:24], owner_instruction_sha256,
        proposal.execution_plan, proposal.original_index, **census, output_bytes=proposal.pure_output_bytes,
        controller=controller, worker=worker, worker_environment=environment,
        worker_source_root=proposal.worker_source_root, proposal=proposal, proposal_relative_path=proposal_relative_path)
    index = DevelopmentNativeContinuationRecoveryIndex.derive(plan, predecessor, proof)
    _require_original_controls(writer=writer, plan=plan, index=index, before_activation=True)
    return proof, index


def select_native_continuation(*, writer, plan, predecessor):
    proof = _read_record(writer, continuation_relative_path(predecessor.run_id), DevelopmentNativeContinuation)
    if proof is None:
        return predecessor
    _require_no_other_repair(writer, predecessor.run_id)
    if _read_record(writer, proof.proposal_relative_path, DevelopmentNativeContinuationProposal) != proof.proposal:
        raise PermissionError('native continuation loses its exact original proposal publication')
    require_scientific_source(proof.worker, proof.controller)
    index = DevelopmentNativeContinuationRecoveryIndex.derive(plan, predecessor, proof)
    census = _census(writer=writer, plan=plan, predecessor=predecessor, proposal=proof.proposal,
        require_absent=False, continuation_index=index)
    if any(getattr(proof, key) != value for key, value in census.items()):
        raise PermissionError('native continuation changes its complete original census')
    _require_original_controls(writer=writer, plan=plan, index=index)
    if ExternalRunRecoveryStore(writer).read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('native continuation loses its derived one-attempt index')
    return index


def publish_native_continuation(*, writer, plan, proof, index):
    if type(index) is not DevelopmentNativeContinuationRecoveryIndex or index.repair != proof:
        raise TypeError('native continuation publication requires its exact derived index')
    _require_no_other_repair(writer, index.run_id)
    _require_original_controls(writer=writer, plan=plan, index=index, before_activation=True)
    ExternalRunRecoveryStore(writer).freeze(index)
    relative = continuation_relative_path(index.run_id)
    writer.write(ArtifactWriteRequest(proof.repair_id, relative, proof.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', proof.repair_id,
        relative.rsplit('/', 1)[0], proof.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    _require_original_controls(writer=writer, plan=plan, index=index, before_activation=True)


def authenticate_controller(*, index, source, controller):
    if type(index) is not DevelopmentNativeContinuationRecoveryIndex:
        raise TypeError('native continuation requires its typed index')
    proof = index.repair
    if (source, controller) != (proof.worker, proof.controller):
        raise PermissionError('native continuation changes its selected worker or controller')
    require_scientific_source(source, controller)
    worker, environment = observe_frozen_repair_worker(interpreter=proof.worker_environment.interpreter_path,
        source_root=proof.worker_source_root)
    if (worker, environment) != (proof.worker, proof.worker_environment):
        raise PermissionError('native continuation changes its live frozen worker installation')
    return observe_frozen_worker_package_root(environment)


def current_native_entry_guard(index):
    """Pin immutable selected bytes once; verify actual publications on every use."""
    if type(index) is not DevelopmentNativeContinuationRecoveryIndex:
        raise TypeError('native continuation entry requires its exact selected index')
    proof = index.repair
    bindings = []
    for relative, record, key in ((continuation_relative_path(index.run_id), proof, proof.repair_id),
            (proof.proposal_relative_path, proof.proposal, proof.proposal.proposal_id)):
        raw = record.canonical_bytes()
        bindings.append((relative, record.SCHEMA, key, len(raw), sha256(raw).hexdigest()))
    bindings = tuple(bindings)

    def require_current(*, writer, prepared_contract):
        for relative, schema, key, size, digest in bindings:
            manifest = writer.read_manifest(relative, maximum_bytes=writer.custody_limits.manifest_bytes)
            logical, material = manifest.logical, manifest.materialization
            if ((logical.logical_artifact_id, logical.payload_schema, logical.profile, logical.media_type,
                    logical.visibility_ceiling, logical.outcome_access, logical.lineage_parents,
                    logical.content_sha256, material.relative_path, material.size_bytes, material.physical_sha256) != (
                    key, schema, ArtifactProfile.CANONICAL_JSON, 'application/json',
                    VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, (),
                    digest, relative, size, digest)
                    or writer.custody_limits.exceeds('recovery_index_bytes', size)):
                raise PermissionError('native continuation entry loses its explicit current selection')
            writer.verify_manifest(manifest)
        _require_prepared_native_continuation(writer=writer, index=index, prepared_contract=prepared_contract)
    return require_current


def _require_prepared_native_continuation(*, writer, index, prepared_contract):
    """An explicit new attempt still retains the old uncertain invocation live."""
    proof = index.repair
    candidates = {row.task_id: row for row in proof.proposal.candidates}
    candidate = candidates.get(prepared_contract.task_id)
    if candidate is None:
        if prepared_contract.task_id not in proof.uncontacted_native_task_ids:
            raise PermissionError('native continuation cannot enter an unselected native task')
        return
    original = candidate.invocation
    attempt, = index.task(candidate.task_id).attempts
    parent = replace(original.expected_parent_contact, attempt_id=attempt.attempt_id)
    definitions = tuple(replace(row, parent_contact=parent) for row in original.native_work.definitions)
    rosters = tuple(replace(row, parent_contact=parent, subworks=tuple(value.identity for value in definitions))
        for row in original.native_work.rosters)
    work = replace(original.native_work, expected_parent=parent, definitions=definitions, rosters=rosters)
    expected = replace(original, invocation_id='prepared.' + attempt.attempt_id, attempt_id=attempt.attempt_id,
        native_work=work, cpu_affinity=prepared_contract.cpu_affinity)
    if prepared_contract != expected:
        raise PermissionError('native continuation changes an original prepared scientific operand or denominator')
    # The selected parent's task outputs may now be produced by the new attempt.
    # All original nested controls and their absence observations remain exact.
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=index.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts,
        parent_contact=original.expected_parent_contact, completed_only=True)
    allowed = {path for output in original.execution_task_record.outputs
        for path in (output.relative_path, output.relative_path + '.manifest.json')}
    if tuple(row for row in _candidate_controls(store, original, original.execution_task_record) if row[0] not in allowed) != tuple(
            row for row in candidate.original_controls if row[0] not in allowed):
        raise PermissionError('native continuation entry changes its original incomplete attempt')


def repair_report(index):
    proof = index.repair
    return {'operational_native_continuation': {
        'continuation': proof.identity.to_document(), 'proposal': proof.proposal.identity.to_document(),
        'original_incomplete_attempts': [dict(task_id=row.task_id, attempt_id=row.invocation.attempt_id,
            states=[state.value for _, state in row.subwork_states]) for row in proof.proposal.candidates],
        'retained_successful_receipts': len(proof.completed_receipts),
        'retained_completed_native_tasks': len(proof.completed_native_contacts),
        'original_task_count': len(proof.proposal.task_ids), 'original_native_task_count': len(proof.proposal.native_task_ids),
        'separate_native_attempts': [dict(task_id=row.task_id, attempt_id=row.attempt_id,
            custody_root=row.relative_root) for row in proof.custody_scopes(index)],
        'uncontacted_original_native_tasks': len(proof.uncontacted_native_task_ids),
        'output_bytes': proof.output_bytes, 'additional_independent_observations': 0}}


def continue_native(*, service, directory, run_id, proposal_path, owner_instruction_sha256,
        maximum_parallel_tasks, confirmed, read_access=None):
    from .recursive_authoring import implementation_binding, load_authored_wave
    from .recursive_execution import _external_inputs, _retained_plans, run_recursive_wave
    from .selected_e3_access import original_e3_authority_read_context
    from empirical_lawhood.infrastructure.run_source_admission import _capture_source
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
    writer = service.artifact_writer
    relative = Path(proposal_path).resolve().relative_to(writer.root.contract.canonical_path).as_posix()
    admission = _capture_source(service.project_root)
    controller = implementation_binding(service.project_root, _admitted_source=admission)
    with original_e3_authority_read_context(writer), writer.read_context() as reader:
        proposal = _read_record(reader, relative, DevelopmentNativeContinuationProposal)
        if proposal is None or proposal.original_run_id != run_id:
            raise PermissionError('native continuation requires its exact published proposal and original run')
        _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=reader,
            lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
        run, plan, index = _retained_plans(payloads, draft)
        if run.run_plan_id != run_id or draft.development_study.access_pair != (
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError('native continuation changes its original exposed development run')
        access = getattr(payloads, 'original_input_access', None)
        def current():
            if access is not None:
                access.require_current()
        with _contacts(reader, plan).execution_lock(run_id):
            current()
            if type(index) is DevelopmentNativeContinuationRecoveryIndex:
                proof = index.repair
                if (proof.proposal, proof.proposal_relative_path, proof.owner_instruction_sha256) != (
                        proposal, relative, owner_instruction_sha256):
                    raise PermissionError('native continuation cannot receive a second selection or attempt')
                authenticate_controller(index=index, source=source, controller=controller)
            else:
                external = _external_inputs(plane=reader, plan=plan, draft=draft, payloads=payloads, read_only=True)
                proof, index = derive_native_continuation(writer=reader, plan=plan, predecessor=index,
                    proposal=proposal, proposal_relative_path=relative, original_source=source, controller=controller,
                    owner_instruction_sha256=owner_instruction_sha256, external_inputs=external, require_access=current)
            require_admitted_target_source_current(service.project_root, admission)
            current()
            reader.require_verification_snapshot()
            if not confirmed:
                return dict(status='EXECUTION_SELECTION_REQUIRED', execution_authorized=False, native_tasks_started=0,
                    **repair_report(index))
            if _read_record(reader, continuation_relative_path(run_id), DevelopmentNativeContinuation) is None:
                publish_native_continuation(writer=writer, plan=plan, proof=proof, index=index)
            reader.require_verification_snapshot()
            current()
    return run_recursive_wave(directory=directory, project_root=service.project_root,
        artifact_writer=writer, maximum_parallel_tasks=maximum_parallel_tasks,
        require_initial_experiment=True, read_access=read_access)
