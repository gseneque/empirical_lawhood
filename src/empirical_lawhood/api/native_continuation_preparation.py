# SPDX-License-Identifier: MPL-2.0
"""Prepare an explicit unfinished-native proposal without scheduling or recovery."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.infrastructure.native_parent_finalization import inspect_native_parent_return
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_continuation_proposal import (
    DevelopmentNativeContinuationProposal, NativeContinuationCandidate,
)
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex

from .development_controller_repair import _contacts, require_scientific_source
from .development_output_repair import _pin
from .retained_e3_control_repair import observe_frozen_repair_worker


def _original_controls(writer, plan, index):
    from .recursive_execution import _custody_control_pins
    rows = list(_custody_control_pins(writer, index))
    contacts = _contacts(writer, plan)
    for task in plan.tasks:
        relative = contacts._path(index.run_id, task.task_id)
        for selected in (relative, relative + '.manifest.json'):
            path = writer.root.resolve(selected, for_write=False)
            if path.exists():
                size, digest = bounded_file_sha256(path, maximum_bytes=writer.custody_limits.control_record_bytes)
                rows.append((selected, size, digest))
            else:
                rows.append((selected, None, None))
    return tuple(sorted(rows))


def _candidate_controls(store, invocation, task):
    """Keep present and absent original paths; include publication markers."""
    parent = invocation.expected_parent_contact
    roots = {store._roster_root(parent)}
    files = {store._invocation_path(parent), store.parent_contacts._path(parent.run_id, parent.task_id)}
    for definition in invocation.native_work.definitions:
        root = store._root(definition)
        roots.add(root)
        files.update(root + '/' + name + '.json' for name in
            ('definition', 'begin', 'contact', 'call-entry', 'call-return', 'completion'))
        files.update(root + '/outputs/' + output.output_id for output in definition.outputs)
        files.add(store.receipts._relative_path(*store._receipt_locator(definition)))
    files.update(output.relative_path for output in task.outputs)
    files.update(path + '.manifest.json' for path in tuple(files))
    for relative in roots:
        root = store.plane.root.resolve(relative, for_write=False)
        if not root.is_dir():
            raise PermissionError('continuation preparation loses an original native custody directory')
        for path in root.rglob('*'):
            if path.is_symlink():
                raise PermissionError('continuation preparation refuses a symlink in original custody')
            if path.is_file():
                files.add(path.relative_to(store.plane.root.contract.canonical_path).as_posix())
    rows = []
    for relative in sorted(files):
        path = store.plane.root.resolve(relative, for_write=False)
        if path.exists():
            size, digest = bounded_file_sha256(path, maximum_bytes=store.plane.custody_limits.control_record_bytes)
            rows.append((relative, size, digest))
        else:
            rows.append((relative, None, None))
    return tuple(rows)


def _inspect_original(*, writer, plan, index, external_inputs, require_access):
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository
    from .recursive_operations import operation_catalog
    if type(index) is not DevelopmentRunRecoveryIndex:
        raise PermissionError('native continuation preparation requires the original unreplaced development index')
    index.validate_plan(plan)
    recovery, receipts = ExternalRunRecoveryStore(writer), ExternalTaskReceiptStore(writer)
    if recovery.read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index:
        raise PermissionError('native continuation preparation changes the original index publication')
    original_controls = _original_controls(writer, plan, index)
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    try:
        upgrade_catalog(engine)
        closure = recovery.reconcile(index, plan, SQLiteOperationalRepository(engine), receipts,
            repair_missing_events=False)
    finally:
        engine.dispose()
    by_task = {row.task_id: row for row in closure.recovered_receipts}
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput, dependency_artifact_inputs
    dependency_outputs = {}
    for key, receipt in by_task.items():
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        dependency_outputs[key] = tuple(VerifiedArtifactInput(logicals[material.logical_artifact_id], material)
            for material in receipt.output_materializations)
    external = {row.logical.logical_artifact_id: row for row in external_inputs}
    declarations, registry, _ = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise PermissionError('native continuation preparation changes the original operation registry')
    native_keys = {(row.selection.capability_key, row.selection.capability_version) for row in declarations if row.native_effect}
    native_tasks = tuple(task for task in plan.tasks if (task.capability.capability_key, task.capability.capability_version) in native_keys)
    contacts = _contacts(writer, plan)
    completed_native, candidates = [], []
    for task in native_tasks:
        require_access()
        parent = contacts.read(index.run_id, task.task_id)
        receipt = by_task.get(task.task_id)
        if parent is None:
            if receipt is not None:
                raise PermissionError('native continuation preparation loses a completed original native contact')
            continue
        binding = index.task(task.task_id)
        if parent.attempt_id not in {row.attempt_id for row in binding.attempts}:
            raise PermissionError('native continuation preparation substitutes an original attempt')
        if any(key not in by_task for key in task.dependency_task_ids):
            raise PermissionError('native continuation preparation lacks completed original dependencies')
        inputs = (*dependency_artifact_inputs(task, dependency_outputs),
            *(external[row.logical_artifact_id] for row in task.external_inputs))
        expected = NativeEffectContact(index.run_id, task.task_id, parent.attempt_id,
            _pin(plan, 'execution_plan_id'), _pin(task, 'task_id'), plan.implementation_commit,
            tuple(sorted(row.materialization.materialization_id for row in inputs)),
            tuple(sorted(by_task[key].receipt_id for key in task.dependency_task_ids)))
        if parent != expected:
            raise PermissionError('native continuation preparation changes original native task or dependency custody')
        if receipt is not None:
            if (receipt.attempt_id, receipt.input_materialization_ids) != (parent.attempt_id, parent.input_materialization_ids):
                raise PermissionError('native continuation preparation changes completed native inputs')
            completed_native.append(task.task_id)
            continue
        if binding.maximum_attempts != 1:
            raise PermissionError('native continuation preparation requires one original incomplete attempt')
        store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts,
            parent_contact=parent, completed_only=True)
        invocation = store.read_prepared_invocation(parent)
        if invocation is None or invocation.execution_task_record != task or invocation.native_work is None:
            raise PermissionError('native continuation preparation lacks its exact original prepared task')
        actual_inputs = {row.logical.logical_artifact_id: row for row in inputs}
        if len(actual_inputs) != len(inputs) or len(invocation.inputs) != len(inputs):
            raise PermissionError('native continuation preparation changes the complete original input census')
        for declared in invocation.inputs:
            actual = actual_inputs.get(declared.artifact_id)
            if actual is None or (declared.logical, declared.binding.materialization_id,
                    declared.binding.size_bytes, declared.physical_sha256) != (
                    actual.logical, actual.materialization.materialization_id,
                    actual.materialization.size_bytes, actual.materialization.physical_sha256):
                raise PermissionError('native continuation preparation changes an original prepared operand')
        observed = inspect_native_parent_return(store=store, work=invocation.native_work)
        if observed.rosters != invocation.native_work.rosters:
            raise PermissionError('native continuation preparation refuses an additional conditional native census')
        if any(row.native_return_status is not None or row.completion is not None or row.receipt is not None
                or row.outputs or row.partial_outputs for row in observed.inspections):
            raise PermissionError('native continuation preparation cannot replace retained native returns or products')
        for output in task.outputs:
            for relative in (output.relative_path, output.relative_path + '.manifest.json'):
                path = writer.root.resolve(relative, for_write=False)
                if path.exists() or path.is_symlink():
                    raise PermissionError('native continuation preparation refuses unreceipted original parent outputs')
        candidates.append(NativeContinuationCandidate(invocation,
            tuple((row.definition.identity, row.state) for row in observed.inspections),
            _candidate_controls(store, invocation, task)))
    require_access()
    if _original_controls(writer, plan, index) != original_controls:
        raise PermissionError('original controls changed during native continuation preparation')
    return dict(task_ids=tuple(sorted(task.task_id for task in plan.tasks)),
        native_task_ids=tuple(sorted(task.task_id for task in native_tasks)),
        completed_receipts=tuple(sorted((key, _pin(value, 'receipt_id')) for key, value in by_task.items())),
        completed_native_task_ids=tuple(sorted(completed_native)),
        candidates=tuple(sorted(candidates, key=lambda row: row.task_id)), original_controls=original_controls)


def prepare_native_continuation(*, service, directory, run_id, output_dir,
        preparation_instruction_sha256, worker_interpreter, worker_source_root,
        pure_output_bytes, read_access=None):
    """Publish a proposal only. There is deliberately no scheduler or retry path."""
    from .recursive_authoring import implementation_binding, load_authored_wave
    from .recursive_execution import _external_inputs, _retained_plans
    from .selected_e3_access import original_e3_authority_read_context
    from empirical_lawhood.infrastructure.run_source_admission import _capture_source
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
    writer = service.artifact_writer
    target = Path(output_dir).resolve()
    relative = target.relative_to(Path(writer.root.contract.canonical_path)).as_posix()
    writer.root.resolve(relative, for_write=True)
    original_root = Path(writer.root.contract.canonical_path) / 'runs' / run_id
    if target.is_relative_to(original_root) or target.is_relative_to(Path(directory).resolve()):
        raise ValueError('native continuation proposal must stay outside original run and authoring custody')
    if target.exists():
        raise FileExistsError('native continuation preparation requires a disjoint new output directory')
    admission = _capture_source(service.project_root)
    controller = implementation_binding(service.project_root, _admitted_source=admission)
    worker, environment = observe_frozen_repair_worker(interpreter=worker_interpreter, source_root=worker_source_root)
    require_scientific_source(worker, controller)
    with original_e3_authority_read_context(writer), writer.read_context() as reader:
        _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=reader,
            lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
        run, plan, index = _retained_plans(payloads, draft)
        if (run.run_plan_id != run_id or source != worker
                or draft.development_study.access_pair != (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)):
            raise PermissionError('native continuation preparation changes its original exposed development selection')
        access = getattr(payloads, 'original_input_access', None)
        def require_access():
            if access is not None:
                access.require_current()
        with _contacts(reader, plan).execution_lock(run_id):
            require_access()
            external_inputs = _external_inputs(plane=reader, plan=plan, draft=draft, payloads=payloads, read_only=True)
            values = _inspect_original(writer=reader, plan=plan, index=index,
                external_inputs=external_inputs, require_access=require_access)
            token = sha256(canonical_json_bytes((values, controller, preparation_instruction_sha256, pure_output_bytes))).hexdigest()
            proposal = DevelopmentNativeContinuationProposal('proposal.native-continuation.' + token[:24],
                preparation_instruction_sha256, run_id, _pin(plan, 'execution_plan_id'), _pin(index, 'recovery_index_id'),
                **values, worker=worker, controller=controller, worker_environment=environment,
                worker_source_root=str(Path(worker_source_root).resolve()), pure_output_bytes=pure_output_bytes)
            def require_current_census():
                require_access()
                require_admitted_target_source_current(service.project_root, admission)
                reader.require_verification_snapshot()
                if _original_controls(reader, plan, index) != proposal.original_controls:
                    raise PermissionError('original controls changed during proposal publication')
                for candidate in proposal.candidates:
                    store = ExternalNativeSubworkStore(plane=reader, parent_contacts=_contacts(reader, plan),
                        parent_contact=candidate.invocation.expected_parent_contact, completed_only=True)
                    if _candidate_controls(store, candidate.invocation, plan.task(candidate.task_id)) != candidate.original_controls:
                        raise PermissionError('original native controls changed during proposal publication')
            require_current_census()
            require_access()
            path = relative + '/proposal.json'
            writer.write(ArtifactWriteRequest(proposal.proposal_id, path, proposal.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, 'application/json', proposal.proposal_id, relative,
                proposal.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
            require_current_census()
    return dict(status='PREPARED_REVIEW_REQUIRED', proposal=proposal.identity.to_document(),
        proposal_path=str(target/'proposal.json'), proposal_sha256=proposal.fingerprint(),
        original_run=run_id, original_task_count=len(proposal.task_ids),
        original_native_task_count=len(proposal.native_task_ids),
        retained_completed_tasks=len(proposal.completed_receipts),
        retained_completed_native_tasks=len(proposal.completed_native_task_ids),
        candidates=[dict(task_id=row.task_id, original_attempt_id=row.invocation.attempt_id,
            subwork_states=[dict(definition=pin.to_document(), state=state.value) for pin, state in row.subwork_states])
            for row in proposal.candidates],
        execution_authorized=False, native_tasks_started=0, additional_independent_observations=0,
        pure_output_bytes=pure_output_bytes,
        continuation_requirements=['Keep original incomplete attempts and their uncertainty',
            'Use separate custody for exactly the proposed new attempts',
            'Retain original scientific tasks, source, inputs, streams and denominator',
            'Reuse completed work and add no independent observations',
            'Obtain an explicit execution selection before any re-execution'])
