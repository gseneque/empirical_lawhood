# SPDX-License-Identifier: MPL-2.0
"""Authenticate published programme transitions without rederiving old science.

The immutable transition selects original producers. Scheduling uses their
actual execution controls. Product consumers authenticate the retained bytes
they use, under fresh access. Reconstructing how old products were computed is
a separate explicit operation.
"""
from contextlib import ExitStack, contextmanager
from dataclasses import replace

from empirical_lawhood.kernel.provenance import ObjectIdentity

from .matrix_researcher_programme_lineage import read_published_record, retained_run_binding


def _recorded_source_inputs(original, current, *, support_files=None, design=None):
    """Join published selections; numerical response reconstruction is optional.

    The transition's exact target and predecessor are already authenticated.
    New child preparation still validates every selected scientific operand.
    """
    before, after = original.commitments, current.commitments
    changes = {'record_id': before.record_id, 'producing_provenance': before.producing_provenance,
        'phases': before.phases, 'e6_policy': before.e6_policy}
    if support_files is not None:
        changes['support_files'] = support_files
    if design is not None:
        if current.scientific_design != design:
            raise PermissionError('recorded amendment changes its exact authorized scientific design')
        changes['scientific_design'] = before.scientific_design
    if replace(after, **changes) != before:
        raise PermissionError('recorded source transition changes original non-source selections')
    for old, new in zip(before.phases, after.phases, strict=True):
        if replace(new, responses=old.responses) != old or (old.responses is None) != (new.responses is None):
            raise PermissionError('recorded source transition changes original allocations or native selections')


def _unentered_training(context, expected, lifetime):
    from .matrix_amendment_withdrawals import _withdrawn_packet
    from .matrix_programme_source_continuation import _require_future_namespaces_absent
    _require_future_namespaces_absent(context)
    packet, run, payloads = _withdrawn_packet(context.writer,
        context.child_directory('train'), context.plan.source_snapshot)
    pin = ObjectIdentity.from_record(packet.packet_id, packet)
    selected = context.binding('train').specification.identity
    member = payloads.member_identity('experiment-specification.json')
    if (pin != expected or (member.object_schema, member.object_version, member.object_fingerprint) != (
            selected.object_schema, selected.object_version, selected.object_fingerprint)):
        raise PermissionError('recorded transition changes its original unentered TRAIN child')
    _require_future_namespaces_absent(context, run.run_plan_id)
    lifetime.callback(_require_future_namespaces_absent, context, run.run_plan_id)
    return pin


def operational_report(report):
    """Return concise state; original task results stay in their retained store."""
    from collections import Counter
    fields = ('state', 'status', 'run_id', 'execution_complete', 'execution_plan', 'recovery_index',
        'task_count', 'operational_terminal', 'terminal', 'read_scope', 'typed_product_validation',
        'scientific_completion', 'scientific_authority', 'scientific_qualification',
        'native_contact', 'new_native_contact_count', 'observed_producing_git_head',
        'producing_code_sha256', 'dependency_lock_sha256', 'dependencies', 'reason_codes',
        'missing_components', 'retained_directory')
    result = {key: report[key] for key in fields if key in report}
    rows = report.get('operational_census')
    if rows is not None:
        result['attempt_counts'] = dict(sorted(Counter(row['operational_status'] for row in rows).items()))
        result['recorded_attempts'] = len(rows)
    result['scientific_reconstruction'] = 'DEFERRED_EXPLICIT_OPT_IN'
    return result


def phase_execution(context, phase, *, observe_controls=None):
    from .retained_e3_evidence import current_e3_evidence
    from .recursive_execution import _custody_control_pins
    evidence = current_e3_evidence(context.writer)
    origin = context.phase_origins.get(phase, context)
    key = origin.plan.identity, context.binding(phase).identity, phase
    retained = None if evidence is None or phase not in ('e1', 'e2', 'train') else evidence.scheduling.get(key)
    if retained is not None:
        report, controls = retained
        for index, pins in controls:
            if _custody_control_pins(context.writer, index) != pins:
                raise PermissionError('original execution controls changed before their scheduling use')
            if observe_controls is not None:
                observe_controls(index, pins)
    else:
        controls = []
        def observe(index, pins):
            controls.append((index, pins))
            if observe_controls is not None:
                observe_controls(index, pins)
        report = _phase_execution(context, phase, observe_controls=observe)
        if evidence is not None and phase in ('e1', 'e2', 'train') and report.get('execution_complete') is True:
            evidence.scheduling[key] = report, tuple(controls)
    expected = context.retained_terminal_pins.get(phase)
    if expected is not None and (report.get('execution_complete') is not True
            or report.get('operational_terminal') != 'AUTHENTICATED'
            or report.get('terminal') != expected.to_document()):
        raise PermissionError('recorded continuation loses original complete execution: ' + phase)
    return report


def _phase_execution(context, phase, *, observe_controls=None):
    """Read original scheduling custody without loading every scientific input."""
    from .experiment_execution_read import read_development_execution, read_execution_records
    from .current_result_custody import CurrentResultPlanReader
    from .recursive_qualified_parents import _actual_package
    from .prospective_experiment import _read_prospective_locator
    from .retained_e3_control_repair import selected_repair_index
    from empirical_lawhood.runtime.prospective_experiment import (
        ASSOCIATION_FILENAME, ProspectiveExperimentAssociation, SPECIFICATION_FILENAME,
    )
    from .protected_e3_read_custody import _current_read_grants

    origin = context.phase_origins.get(phase, context)
    directory, writer = origin.child_directory(phase), context.writer
    if phase in ('e4.revision', 'e4.calibration', 'e4.confirmation'):
        child = context.service._composite_programme(directory=directory)
        if child is None:
            return {'state':'AUTHORING_REQUIRED','new_native_contact_count':0}
        expected = context.binding(phase).specification.identity
        if phase != 'e4.revision':
            from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_declarative
            _, specification = context.bound_specification(context.binding(phase))
            inputs = context.method_inputs(phase)
            selected_e4_declarative.validate_plan(specification, inputs)
            expected = inputs.plan.specification.identity
        if child.descriptor.specification != expected:
            raise PermissionError('programme execution inspection substitutes its original composite specification')
        options = {}
        if phase != 'e4.revision':
            from .matrix_programme_e4_phases import programme_e4_request
            options['request'] = programme_e4_request(context, phase, include_collection=False)
        return child.read_execution(directory=directory, **options)
    association_path = directory / 'experiment' / ASSOCIATION_FILENAME
    prospective = phase in ('e1', 'e3') or association_path.exists() or association_path.is_symlink()
    if not prospective:
        packet = directory / 'authored-wave.json'
        if not packet.exists() and not packet.is_symlink():
            return {'state': 'AUTHORING_REQUIRED', 'new_native_contact_count': 0}
        binding = context.binding(phase)
        # This pin belongs to the exact immutable phase publication. Reading
        # scheduling state does not require decoding its scientific selector.
        report = read_development_execution(directory=directory, artifact_writer=writer,
            observe_controls=observe_controls)
        from empirical_lawhood.infrastructure.recursive_custody import read_recursive_bootstrap_record
        from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
        packet = read_recursive_bootstrap_record(writer,
            (directory / 'authored-wave.json').relative_to(writer.root.contract.canonical_path).as_posix(), AuthoredRecursiveWave)
        pins = tuple(row.identity for row in packet.members if row.filename == 'experiment-specification.json')
        expected = binding.specification.identity
        if len(pins) != 1 or (pins[0].object_schema, pins[0].object_version, pins[0].object_fingerprint) != (
                expected.object_schema, expected.object_version, expected.object_fingerprint):
            raise PermissionError('programme execution observation changes its exact phase specification')
        if phase == 'e4.development' and report.get('execution_complete') is True:
            from .selected_e4_structure import read_development_structure_execution
            structure = read_development_structure_execution(directory=directory, artifact_writer=writer,
                acquisition_report=report, observe_controls=observe_controls)
            report = {**report, 'structure':structure,
                'execution_complete':structure.get('execution_complete') is True}
        return report
    locator = retained_run_binding(origin, phase)
    if locator is None:
        return {'state': 'RUN_SELECTION_REQUIRED', 'read_scope': 'EXECUTION_RECORDS',
            'execution_complete': False, 'scientific_completion': 'DEFERRED_TO_FULL_READ',
            'new_native_contact_count': 0}
    with writer.read_context() as controls:
        association = _read_prospective_locator(directory / 'experiment', ASSOCIATION_FILENAME,
            controls, ProspectiveExperimentAssociation)
        if tuple(row.identity for row in association.members if row.filename == SPECIFICATION_FILENAME) != (locator.specification,):
            raise PermissionError('programme execution observation changes its original specification')
        if phase == 'e1' and phase in context.retained_terminal_pins:
            from .recorded_execution_controls import completed_issued_execution
            return completed_issued_execution(writer=controls, locator=locator, candidate=association.candidate,
                terminal=context.retained_terminal_pins[phase], observe_controls=observe_controls)
        if phase == 'e3':
            from .retained_e3_evidence import current_e3_evidence
            evidence = current_e3_evidence(controls)
            if evidence is not None:
                authority = locator.authority
                replacements = () if context.operation is None else tuple(row for row in context.operation.authorities
                    if row.package_path == authority.package_path)
                if replacements:
                    if len(replacements) != 1:
                        raise PermissionError('recorded E3 execution has ambiguous current reveal selections')
                    authority, = replacements
                producer = evidence.producer(locator.run_id, authority.reveal_authority_id, package_pin=locator.package)
                if (ObjectIdentity.from_record(producer.package.issued_study.candidate.candidate_id,
                        producer.package.issued_study.candidate) != association.candidate
                        or context.binding(phase).specification.identity != locator.specification):
                    raise PermissionError('recorded E3 execution substitutes its original candidate or specification')
                if observe_controls is not None:
                    observe_controls(producer.index, producer.control_pins)
                return producer.report
        reader = CurrentResultPlanReader(controls)
        package = _actual_package(controls, locator.run_id, control_reader=reader)
        if (ObjectIdentity.from_record(package.package_id, package) != locator.package
                or ObjectIdentity.from_record(package.issued_study.candidate.candidate_id,
                    package.issued_study.candidate) != association.candidate
                or context.binding(phase).specification.identity != locator.specification):
            raise PermissionError('programme execution observation changes its original issued producer')
        plan = reader.authenticate_execution_plan(package=package, issued=package.issued_study, run_id=locator.run_id)
        index = selected_repair_index(writer=controls, plan=plan,
            predecessor=reader.original_recovery_index(package=package, execution_plan=plan))
        report = read_execution_records(writer=controls, plan=plan, index=index, observe_controls=observe_controls)
        if locator.authority.reveal_authority_id is not None:
            _current_read_grants(controls, package, locator.authority.reveal_authority_id)
        controls.require_verification_snapshot()
    return report


@contextmanager
def recorded_continuation_context(owner, context, record):
    """Keep transition reads scoped while the caller retains its publisher."""
    from .retained_e3_evidence import retained_e3_reader
    with retained_e3_reader(context.writer).read_context() as writer:
        reading = replace(context, service=replace(context.service, artifact_writer=writer))
        with _recorded_continuation_context(owner, reading, record):
            yield


@contextmanager
def _recorded_continuation_context(owner, context, record):
    """Consume an exact existing handoff; never re-create its historical work."""
    from .matrix_researcher_programme import MatrixResearchProgrammeService
    from .selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammePlan
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import (
        source_continuation, retained_training_continuation, retained_e3_continuation,
        curve_amendment,
    )
    if record.target_plan != context.plan:
        raise PermissionError('recorded continuation changes its exact target programme')
    handle = record.specification.predecessor
    original_plan = read_published_record(context.writer, handle.publication.materialization.relative_path,
        MatrixResearchProgrammePlan, handle.publication.materialization.size_bytes)
    handle.require_record(original_plan, original_plan.identity)
    if _publication_from_manifest(context.writer, context.writer.read_manifest(
            handle.publication.materialization.relative_path)) != replace(handle.publication, created=False):
        raise PermissionError('recorded continuation changes its original plan publication')
    operations = original_plan.specification.operations
    if isinstance(record, source_continuation.MatrixProgrammeCompletedSourceContinuation):
        operations = source_continuation.continued_operations(operations, record.specification,
            completed_phases=record.RETAINED_PHASES)
    if ((original_plan.workers, original_plan.environment_id, operations) !=
            (context.plan.workers, context.plan.environment_id, context.plan.specification.operations)
            or original_plan.source_snapshot == context.plan.source_snapshot):
        raise PermissionError('recorded continuation changes operations or omits its source transition')
    directory = context.writer.root.resolve(original_plan.specification.directory, for_write=False)
    original_owner = context.service._composite_programme(directory=directory)
    if type(original_owner) is not MatrixResearchProgrammeService or original_owner._plan(directory) != original_plan:
        raise PermissionError('recorded continuation changes its original programme descriptor')
    with original_owner._read_context(original_plan, operation=context.operation) as original, ExitStack() as lifetime:
        inherited = tuple(phase for phase, _ in record.predecessor_bindings)
        if tuple((phase, original.binding(phase).identity) for phase in inherited) != record.predecessor_bindings:
            raise PermissionError('recorded continuation changes original phase bindings')
        if any(phase in context.bindings for phase in inherited):
            raise PermissionError('recorded continuation cannot replace a completed original phase')
        if isinstance(record, source_continuation.MatrixProgrammeCompletedSourceContinuation):
            from .matrix_programme_completed_continuation import require_numerical_continuity, require_unentered_successors
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import completed_source_files
            from empirical_lawhood.infrastructure.matrix_completed_source import read_completed_source, original_e3_commitment
            from empirical_lawhood.infrastructure.matrix_recorded_inputs import recorded_programme_inputs
            if isinstance(record, source_continuation.MatrixProgrammeCompletedE4SourceContinuation):
                from .matrix_programme_completed_continuation import recorded_completed_e4_custody
                report = lifetime.enter_context(recorded_completed_e4_custody(original_owner, original, record))
                context.retained_execution_reports['e4.development'] = report
            elif type(record) is source_continuation.MatrixProgrammeUnenteredE4SourceContinuation:
                from .matrix_programme_unentered_e4 import unentered_e4_custody
                retained_e4 = lifetime.enter_context(unentered_e4_custody(original, expected=record))
                require_unentered_successors(original, unentered_e4=retained_e4)
            else:
                from .matrix_programme_retained_bank_metadata import _namespace
                directory = original.metadata_directory('e4.development')
                guard = (lambda: _namespace(original, directory)) if directory.exists() or directory.is_symlink() else None
                require_unentered_successors(original, retained_metadata=guard)
            require_numerical_continuity(original.inputs.producing_provenance, context.inputs.producing_provenance)
            source = read_completed_source(context.writer, context.commitments)
            rows = completed_source_files(context.commitments)
            selected = original_e3_commitment(context.writer, original.inputs, original.plan.specification.input_commitments)
            original_inputs = original.inputs
            if selected != original.plan.specification.input_commitments:
                original_inputs = lifetime.enter_context(recorded_programme_inputs(writer=context.writer,
                    commitment=selected, maximum_source_bytes=original.plan.specification.operations.metadata_budget.source_scan_bytes))
            if (source.predecessor_inputs != selected
                    or source.original_provenance != original_inputs.producing_provenance.identity
                    or source.target_provenance != context.inputs.producing_provenance.identity):
                raise PermissionError('recorded completed E3 transition changes its original input source')
            _recorded_source_inputs(original_inputs, context.inputs,
                support_files=tuple(row for row in context.commitments.support_files if row not in rows))
        elif type(record) is source_continuation.MatrixProgrammeSourceContinuation:
            _recorded_source_inputs(original.inputs, context.inputs)
            _unentered_training(original, record.unentered_training_packet, lifetime)
        elif type(record) is retained_training_continuation.MatrixProgrammeRetainedTrainingContinuation:
            from empirical_lawhood.infrastructure.matrix_retained_training import read_retained_training_source
            source = record.retained_training
            rows = retained_training_continuation.retained_source_files(context.commitments)
            if (read_retained_training_source(context.writer, context.commitments) != source
                    or source.input_commitments != original.plan.specification.input_commitments
                    or source.target_provenance != context.inputs.producing_provenance.identity):
                raise PermissionError('recorded continuation changes original TRAIN source custody')
            _recorded_source_inputs(original.inputs, context.inputs,
                support_files=tuple(row for row in context.commitments.support_files if row not in rows))
        elif isinstance(record, retained_e3_continuation.MatrixProgrammeRetainedE3Continuation):
            from empirical_lawhood.infrastructure.matrix_retained_training import read_retained_training_source
            before, after = record.predecessor_training, record.retained_training
            old_rows = retained_training_continuation.retained_source_files(original.commitments)
            new_rows = retained_training_continuation.retained_source_files(context.commitments)
            if (len(old_rows) != 1 or len(new_rows) != 1 or old_rows[0][0] != before.artifact
                    or new_rows[0][0] != after.artifact
                    or before.target_provenance != original.inputs.producing_provenance.identity
                    or after.target_provenance != context.inputs.producing_provenance.identity
                    or (before.predecessor, before.input_commitments, before.training_locator, before.export_adoption)
                        != (after.predecessor, after.input_commitments, after.training_locator, after.export_adoption)):
                raise PermissionError('recorded E3 transition changes its original TRAIN producer or custody')
            support = tuple(sorted((*tuple(row for row in context.commitments.support_files if row not in new_rows),
                *old_rows), key=lambda row: row[0].artifact_id))
            _recorded_source_inputs(original.inputs, context.inputs, support_files=support)
            run = retained_run_binding(original, 'e3')
            if (read_retained_training_source(original.writer, original.commitments) != record.predecessor_training
                    or read_retained_training_source(context.writer, context.commitments) != record.retained_training
                    or original.binding('e3').identity != record.predecessor_e3_binding
                    or run is None or run.identity != record.predecessor_e3_run):
                raise PermissionError('recorded E3 transition changes its original run or TRAIN custody')
            # The record preserves the excluded unknown contacts and exact
            # imported receipt pins. Product access checks their actual producers.
            context.retained_e3.append((record, None, None))
        elif type(record) is curve_amendment.MatrixProgrammeCurveAmendment:
            from .matrix_amendment_evidence import read_evidence
            from .matrix_amendment_withdrawals import withdrawn_custody
            from types import SimpleNamespace
            expected = curve_amendment.amend_curve_design(original.inputs.scientific_design,
                record_id=context.inputs.scientific_design.record_id)
            _recorded_source_inputs(original.inputs, context.inputs, design=expected)
            if curve_amendment.amendment_exposure(original.inputs, original.bindings) != record.exposure:
                raise PermissionError('recorded amendment changes its complete original exposure')
            read_evidence(context.writer, record, original.inputs.producing_provenance)
            training_packet = _unentered_training(original, record.unentered_training_packet, lifetime)
            withdrawn, _ = lifetime.enter_context(withdrawn_custody(context.service,
                record.specification, original_plan, record.predecessor_bindings,
                SimpleNamespace(terminals=record.predecessor_terminals, training_packet=training_packet)))
            if withdrawn != record.withdrawn_training_packets:
                raise PermissionError('recorded amendment changes superseded TRAIN nonentry custody')
        else:
            raise PermissionError('unsupported recorded programme transition')
        terminals = dict(original.retained_terminal_pins)
        for phase, pin in record.predecessor_terminals:
            if phase in terminals and terminals[phase] != pin:
                raise PermissionError('recorded continuation substitutes an original terminal selection')
            terminals[phase] = pin
        context.phase_origins.update((phase, original.phase_origins.get(phase, original)) for phase in inherited)
        context.bindings.update((phase, original.binding(phase)) for phase in inherited)
        # A recorded terminal pin is an obligation, not a completion verdict.
        # The scheduling/custody consumer checks its actual full receipt census
        # once, when it needs that phase, instead of at each historical link.
        context.retained_terminal_pins.update(terminals)
        context.continuation_records.extend(original.continuation_records)
        context.amendment_records.extend(original.amendment_records)
        if type(record) is curve_amendment.MatrixProgrammeCurveAmendment:
            context.amendment_records.append(record)
        else:
            context.continuation_records.append(record)
        yield
        # This is a pure lineage read inside recorded_continuation_context's
        # owning read lifetime. Its complete final guard includes every nested
        # predecessor. Publication and execution keep their separate checks.
        context.writer.require_verification_context()
