# SPDX-License-Identifier: MPL-2.0
"""Read original execution records without claiming scientific body validation.

This observation can prevent repeated dispatch of a completed acquisition. It
cannot establish a scientific result, authorize an effect or supply a product.
Every scientific consumer must still use its ordinary complete result reader.
"""
from contextlib import contextmanager
from pathlib import Path

from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.recursive_custody import _execution_operational_census, _partial_operational_census
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity


def load_development_execution_controls(*, directory, artifact_writer, expected_specification_bytes=None, read_access=None):
    """Authenticate frozen scheduling controls without rebuilding scientific inputs.

    This reader cannot supply executable operands. The execution owner still
    authenticates the complete authored wave and its graph before dispatch.
    """
    from .experiment_runtime_bindings import bootstrap_authored_development_inputs
    from empirical_lawhood.infrastructure.recursive_custody import read_recursive_bootstrap_record, read_exposed_recursive_payload
    from empirical_lawhood.kernel.decoding import decimal_context_key
    from empirical_lawhood.infrastructure.recursive_control_read import CONTROL_VIEWS, decode_authored_control
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex

    directory = Path(directory)
    if directory != directory.resolve(strict=True) or any(p.is_symlink() for p in (directory, *directory.parents)):
        raise PermissionError('execution controls require the actual guarded authored directory')
    root = artifact_writer.root.contract.canonical_path
    prefix = directory.relative_to(root).as_posix()
    packet = read_recursive_bootstrap_record(artifact_writer, prefix + '/authored-wave.json', AuthoredRecursiveWave)
    members = {row.filename: row for row in packet.members}
    from .retained_e3_evidence import current_e3_evidence
    retained = current_e3_evidence(artifact_writer)
    control_key = prefix, packet.fingerprint(), decimal_context_key()
    cached = None if retained is None or read_access is not None else retained.authored_controls.get(control_key)
    if cached is not None:
        from dataclasses import replace
        _, run, plan, index, source, access = cached
        if access is not None:
            access = replace(access, writer=artifact_writer)
            access.require_current()
        selected = ('implementation.json', 'run-plan.json', 'execution-plan.json',
            *(name for name in CONTROL_VIEWS.values() if name in members))
        for name in selected:
            member = members[name]
            manifest = artifact_writer.read_manifest(prefix + '/' + name)
            if (manifest.materialization.size_bytes != member.size_bytes
                    or manifest.logical.content_sha256 != member.identity.object_fingerprint
                    or manifest.logical.payload_schema != member.identity.object_schema):
                raise PermissionError('execution control changes its exact authored member')
            if access is not None:
                access.require_member(manifest)
            artifact_writer.verify_manifest(manifest)
        if expected_specification_bytes is not None:
            from hashlib import sha256
            member = members.get('experiment-specification.json')
            if (member is None or member.size_bytes != len(expected_specification_bytes)
                    or member.identity.object_fingerprint != sha256(expected_specification_bytes).hexdigest()):
                raise PermissionError('execution controls change the selected specification')
        if access is not None:
            access.require_current()
        from .development_output_repair import select_development_output_repair
        index = select_development_output_repair(writer=artifact_writer, plan=plan, predecessor=index)
        return packet, run, plan, index, source, access

    def bootstrap(name, kind):
        member = members[name]
        return read_recursive_bootstrap_record(artifact_writer, prefix + '/' + name, kind,
            maximum_bytes=member.size_bytes, expected=member)

    access = bootstrap_authored_development_inputs(directory=directory, artifact_writer=artifact_writer,
        packet=packet, read_record=bootstrap, read_access=read_access)

    def read_raw(name):
        from hashlib import sha256
        member = members[name]
        manifest = artifact_writer.read_manifest(prefix + '/' + name)
        raw = read_exposed_recursive_payload(artifact_writer, manifest,
            maximum_bytes=member.size_bytes, original_input_access=access)
        if (len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.identity.object_fingerprint
                or manifest.logical.payload_schema != member.identity.object_schema):
            raise PermissionError('execution control changes its exact authored member')
        return raw

    def read(name, kind):
        from empirical_lawhood.runtime.progress import report_progress
        member = members[name]
        report_progress(phase='decode_retained.' + kind.SCHEMA.rsplit('/', 1)[-1])
        record = decode_authored_control(members, name, kind, read_payload=read_raw)
        if ObjectIdentity.from_record(member.identity.object_id, record) != member.identity:
            raise PermissionError('execution control changes its exact authored member')
        return record

    source = read('implementation.json', RecursiveImplementationBinding)
    run = read('run-plan.json', DevelopmentRunPlan)
    plan = read('execution-plan.json', DevelopmentExecutionPlan)
    if (run.draft != packet.draft or packet.implementation != ObjectIdentity.from_record('recursive-member.implementation', source)
            or run.implementation_commit != source.observed_git_head or plan.implementation_commit != source.observed_git_head
            or plan.source_plan != ObjectIdentity.from_record(run.run_plan_id, run)):
        raise PermissionError('execution controls change their original draft, source or run')
    if expected_specification_bytes is not None:
        from hashlib import sha256
        member = members.get('experiment-specification.json')
        if (member is None or member.size_bytes != len(expected_specification_bytes)
                or member.identity.object_fingerprint != sha256(expected_specification_bytes).hexdigest()):
            raise PermissionError('execution controls change the selected specification')
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.development', authority_identities=())
    if access is not None:
        access.require_current()
    result = packet, run, plan, index, source, access
    from .selected_e3_access import SelectedE3OriginalInputAccess
    if retained is not None and read_access is None and (access is None or type(access) is SelectedE3OriginalInputAccess):
        retained.authored_controls[control_key] = result
    from .development_output_repair import select_development_output_repair
    index = select_development_output_repair(writer=artifact_writer, plan=plan, predecessor=index)
    return packet, run, plan, index, source, access


@contextmanager
def observed_development_authoring(*, directory, artifact_writer, authoring_report,
        expected_specification_bytes=None):
    """Retain an immediate ordinary author's closed publication without replay.

    This scope is only for newly authored, unprivileged development metadata.
    It asserts no execution or scientific completion. The packet pin comes from
    this invocation's actual author; every member and the absent run namespace
    remain guarded through the enclosing author's return.
    """
    from empirical_lawhood.infrastructure.recursive_custody import (
        AuthenticatedRecursivePayloads, read_recursive_bootstrap_record,
    )
    from empirical_lawhood.infrastructure.recursive_control_read import decode_authored_control
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex

    directory = Path(directory)
    if (type(authoring_report) is not dict or authoring_report.get('status') != 'AUTHORED'
            or authoring_report.get('native_contact') != 'none'
            or authoring_report.get('authoring_dir') != str(directory)):
        raise ValueError('authoring observation requires its actual immediate ordinary author result')
    with artifact_writer.read_context() as writer:
        relative = (directory / 'authored-wave.json').relative_to(writer.root.contract.canonical_path).as_posix()
        packet = read_recursive_bootstrap_record(writer, relative, AuthoredRecursiveWave)
        if packet.fingerprint() != authoring_report.get('packet_sha256'):
            raise PermissionError('authoring observation changes its actual just-published packet')
        for member in packet.members:
            relative = (directory / member.filename).relative_to(writer.root.contract.canonical_path).as_posix()
            manifest = writer.read_manifest(relative)
            if (manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                    or manifest.logical.lineage_parents):
                raise PermissionError('authoring observation cannot replace original protected-parent access')
        payloads = AuthenticatedRecursivePayloads(plane=writer, directory=directory, members=packet.members)
        if (expected_specification_bytes is not None
                and payloads.get('experiment-specification.json') != expected_specification_bytes):
            raise PermissionError('authoring observation changes its actual selected specification')

        def decode(name, kind):
            return decode_authored_control(payloads, name, kind)

        source = decode('implementation.json', RecursiveImplementationBinding)
        run = decode('run-plan.json', DevelopmentRunPlan)
        plan = decode('execution-plan.json', DevelopmentExecutionPlan)
        if (packet.implementation != ObjectIdentity.from_record('recursive-member.implementation', source)
                or run.implementation_commit != source.observed_git_head
                or plan.implementation_commit != source.observed_git_head
                or plan.source_plan != ObjectIdentity.from_record(run.run_plan_id, run)
                or run.run_plan_id != authoring_report.get('run_id')
                or len(plan.tasks) != authoring_report.get('task_count')
                or packet.draft.object_fingerprint != authoring_report.get('draft_sha256')):
            raise PermissionError('authoring observation changes its actual source or frozen task census')
        index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
            wave_id='wave.development', authority_identities=())

        def require_unentered():
            path = writer.root.resolve('runs/' + run.run_plan_id, for_write=False)
            if path.exists() or path.is_symlink():
                raise PermissionError('new authoring observation cannot hide concurrent execution custody')

        require_unentered()
        try:
            yield {'run_id': run.run_plan_id, 'status': 'UNENTERED', 'execution_complete': False,
                'execution_plan': ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
                'recovery_index': ObjectIdentity.from_record(index.recovery_index_id, index).to_document(),
                'task_count': len(plan.tasks), 'operational_census': (), 'terminal': None,
                'operational_terminal': 'ABSENT', 'observed_producing_git_head': source.observed_git_head,
                'packet_sha256': packet.fingerprint(), 'producing_code_sha256': source.code_sources_sha256,
                'dependency_lock_sha256': source.dependency_lock_sha256,
                'read_scope': 'AUTHORING_RECORDS', 'typed_product_validation': 'DEFERRED',
                'scientific_completion': 'DEFERRED_TO_FULL_READ', 'new_native_contact_count': 0,
                'scientific_authority': 'NONE', 'scientific_qualification': 'NOT_ESTABLISHED'}
        finally:
            require_unentered()
            writer.require_verification_snapshot()


def read_execution_records(*, writer, plan, index, observe_controls=None):
    """Authenticate the frozen complete attempt census, including absent slots."""
    from .recursive_execution import _custody_control_pins
    from empirical_lawhood.runtime.progress import report_progress

    report_progress(phase='retained_execution.controls.' + index.run_id)
    index.validate_plan(plan)
    before = _custody_control_pins(writer, index)
    recovery, receipts = ExternalRunRecoveryStore(writer), ExternalTaskReceiptStore(writer)
    run_path = writer.root.resolve('runs/' + index.run_id, for_write=False)
    if not run_path.exists() and not run_path.is_symlink():
        terminal, rows = None, ()
        state = 'UNENTERED'
    else:
        index_path = writer.root.resolve(index.index_relative_path, for_write=False)
        if not index_path.exists() and not index_path.is_symlink():
            # Input materialization precedes index publication. Absence of the
            # index is never evidence that a worker is active or has entered.
            from .recursive_unentered import require_input_only_run
            require_input_only_run(writer, plan, index.run_id)
            terminal, rows, state = None, (), 'INPUTS_PARTIAL'
        else:
            retained = recovery.read_index(index.index_relative_path, expected_schema=index.SCHEMA)
            if retained != index:
                raise PermissionError('execution inspection changes its original complete recovery index')
            terminal = recovery.read_terminal(index)
            report_progress(phase='retained_execution.receipts.' + index.run_id)
            if terminal is None:
                rows, _, _, _ = _partial_operational_census(recovery=recovery, store=receipts, plan=plan, index=index)
                state = 'INCOMPLETE'
            else:
                rows, _, _ = _execution_operational_census(recovery=recovery, store=receipts,
                    plan=plan, index=index, terminal=terminal)
                state = terminal.operational_status
                if state == 'SUCCEEDED' and (set(terminal.completed_task_ids) != {task.task_id for task in plan.tasks}
                        or terminal.failed_task_ids or terminal.blocked_task_ids):
                    raise PermissionError('execution inspection requires the complete successful assigned task census')
    report_progress(phase='retained_execution.guard.' + index.run_id)
    if _custody_control_pins(writer, index) != before:
        raise PermissionError('execution records changed during their original census inspection')
    if state == 'INPUTS_PARTIAL':
        require_input_only_run(writer, plan, index.run_id)
    if observe_controls is not None:
        observe_controls(index, before)
    from .development_output_repair import repair_report
    return {**repair_report(index), 'run_id': index.run_id, 'status': state, 'execution_complete': state == 'SUCCEEDED',
        'execution_plan': ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
        'execution_plan_sha256': plan.fingerprint(),
        'recovery_index': ObjectIdentity.from_record(index.recovery_index_id, index).to_document(),
        'operational_terminal': 'ABSENT' if terminal is None else 'AUTHENTICATED',
        'terminal': None if terminal is None else ObjectIdentity.from_record(terminal.terminal_event_id, terminal).to_document(),
        'task_count': len(plan.tasks), 'operational_census': rows,
        'observed_producing_git_head': plan.implementation_commit,
        'read_scope': 'EXECUTION_RECORDS', 'typed_product_validation': 'DEFERRED',
        'scientific_completion': 'DEFERRED_TO_FULL_READ', 'new_native_contact_count': 0,
        'scientific_authority': 'NONE', 'scientific_qualification': 'NOT_ESTABLISHED'}


def read_development_execution(*, directory, artifact_writer, expected_specification_bytes=None,
        observe_controls=None, read_access=None):
    """Use the original authored owner before inspecting a development run."""
    from .selected_e3_access import original_e3_authority_read_context

    with original_e3_authority_read_context(artifact_writer), artifact_writer.read_context() as writer:
        packet, _, plan, index, source, access = load_development_execution_controls(
            directory=directory, artifact_writer=writer, expected_specification_bytes=expected_specification_bytes,
            read_access=read_access)
        if access is not None:
            access.require_current()
        report = read_execution_records(writer=writer, plan=plan, index=index, observe_controls=observe_controls)
        if access is not None:
            access.require_current()
        writer.require_verification_snapshot()
    if access is not None:
        access.require_current(artifact_writer=artifact_writer)
    return {**report, 'packet_sha256': packet.fingerprint(),
        'producing_code_sha256': source.code_sources_sha256,
        'dependency_lock_sha256': source.dependency_lock_sha256}


def read_prospective_execution(*, selected, artifact_writer, package=None, run_id, observe_controls=None,
        reveal_authority_id=None):
    """Read issued execution controls, without opening protected outcome bodies."""
    from .current_result_custody import CurrentResultPlanReader, current_result_package_present
    from .recursive_qualified_parents import _actual_package

    if not current_result_package_present(writer=artifact_writer, run_id=run_id):
        run_path = artifact_writer.root.resolve('runs/' + run_id, for_write=False)
        if run_path.exists() or run_path.is_symlink():
            raise PermissionError('issued execution custody is present without its original package')
        return {'run_id': run_id, 'status': 'UNENTERED', 'execution_complete': False,
            'read_scope': 'EXECUTION_RECORDS', 'scientific_completion': 'DEFERRED_TO_FULL_READ',
            'new_native_contact_count': 0}
    with artifact_writer.read_context() as writer:
        reader = CurrentResultPlanReader(writer)
        original = _actual_package(writer, run_id, control_reader=reader)
        expected = (ObjectIdentity.from_record(original.package_id, original) if package is None
            else package if type(package) is ObjectIdentity else ObjectIdentity.from_record(package.package_id, package))
        if (ObjectIdentity.from_record(original.package_id, original) != expected or original.run_plan_id != run_id
                or ObjectIdentity.from_record(original.issued_study.candidate.candidate_id,
                    original.issued_study.candidate) != selected.association.candidate
                or original.issued_study.source_closure != selected.implementation):
            raise PermissionError('issued execution inspection changes its original candidate/source/package')
        if reveal_authority_id is not None:
            from .protected_e3_read_custody import _current_read_grants
            _current_read_grants(writer, original, reveal_authority_id)
        plan = reader.authenticate_execution_plan(package=original, issued=original.issued_study, run_id=run_id)
        if {task.task_id for task in plan.tasks} != {task.task_id for task in selected.projection.tasks}:
            raise PermissionError('issued execution inspection changes its original complete task census')
        index = reader.original_recovery_index(package=original, execution_plan=plan)
        report = read_execution_records(writer=writer, plan=plan, index=index, observe_controls=observe_controls)
        writer.require_verification_snapshot()
        if reveal_authority_id is not None:
            _current_read_grants(writer, original, reveal_authority_id)
    return {**report, 'specification': selected.instance.specification.to_document(),
        'package': ObjectIdentity.from_record(original.package_id, original).to_document()}
