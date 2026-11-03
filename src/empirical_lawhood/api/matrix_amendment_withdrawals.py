# SPDX-License-Identifier: MPL-2.0
"""Read-only nonentry proof for explicitly superseded source derivations."""
from contextlib import contextmanager
from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import (
    CONTINUATION_FILENAME, MatrixProgrammeSourceContinuation, require_separate_home,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from .matrix_programme_projection import MatrixProgrammeProjectionContext
from .matrix_researcher_programme_lineage import read_published_record


def _absent(path):
    if path.exists() or path.is_symlink():
        raise PermissionError('curve amendment refuses superseded future execution or partial custody: ' + str(path))


def _future_absences(context, *, authored, run_id):
    if context.pending_bindings or set(context.bindings) != ({'train'} if authored else set()):
        raise PermissionError('curve amendment requires exactly the declared unentered superseded TRAIN binding')
    for phase in PHASES:
        if phase == 'train' and authored:
            continue
        for path in (context.child_directory(phase), context.metadata_directory(phase),
                context.directory / 'bindings' / (phase + '.json'),
                context.directory / 'bindings' / (phase + '.json.manifest.json')):
            _absent(path)
    _absent(context.directory / 'runs')
    if run_id is not None:
        _absent(context.writer.root.resolve('runs/' + run_id, for_write=False))


def _withdrawn_packet(writer, directory, expected_source):
    """Authenticate all closed bytes and the run locator of a withdrawn packet.

    This proves nonentry only. It supplies no executable graph or scientific
    product and never substitutes for the full reader of an entered programme.
    Only unprivileged development packets are eligible for this observation.
    """
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads, read_recursive_bootstrap_record
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding

    relative = (directory / 'authored-wave.json').relative_to(writer.root.contract.canonical_path).as_posix()
    packet = read_recursive_bootstrap_record(writer, relative, AuthoredRecursiveWave)
    if packet.implementation != expected_source:
        raise PermissionError('withdrawn packet changes its declared original producing source')
    for member in packet.members:
        relative = (directory / member.filename).relative_to(writer.root.contract.canonical_path).as_posix()
        manifest = writer.read_manifest(relative)
        if (manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or manifest.logical.lineage_parents):
            raise PermissionError('withdrawn observation cannot replace protected original input access')
    payloads = AuthenticatedRecursivePayloads(plane=writer, directory=directory, members=packet.members)

    def decode(name, kind):
        member = next(row for row in packet.members if row.filename == name)
        relative = (directory / name).relative_to(writer.root.contract.canonical_path).as_posix()
        return read_published_record(writer, relative, kind, member.size_bytes)

    source = decode('implementation.json', RecursiveImplementationBinding)
    run = decode('run-plan.json', DevelopmentRunPlan)
    plan = decode('execution-plan.json', DevelopmentExecutionPlan)
    projection = payloads.member_identity('scientific-projection.json')
    if (packet.implementation != ObjectIdentity.from_record('recursive-member.implementation', source)
            or run.draft != packet.draft or projection.object_id != 'recursive-member.scientific-projection'
            or replace(run.scientific_projection, object_id=projection.object_id) != projection
            or run.implementation_commit != source.observed_git_head or plan.implementation_commit != source.observed_git_head
            or plan.source_plan != ObjectIdentity.from_record(run.run_plan_id, run)):
        raise PermissionError('withdrawn packet changes its original source, draft or run locator')
    _absent(writer.root.resolve('runs/' + run.run_plan_id, for_write=False))
    return packet, run, payloads


@contextmanager
def withdrawn_custody(service, specification, original_plan, original_bindings, retained):
    from .matrix_researcher_programme import MatrixResearchProgrammeService, PLAN_FILENAME
    from .matrix_programme_source_continuation import _pin_original_selection
    from .selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.runtime.experiment_programme import PROGRAMME_DESCRIPTOR_FILENAME

    with service.artifact_writer.read_context() as writer:
        scoped = replace(service, artifact_writer=writer)
        guards, packets, homes = [], [], set()
        for selected in specification.withdrawn_derivations:
            relative = selected.publication.materialization.relative_path
            record = read_published_record(writer, relative, MatrixProgrammeSourceContinuation,
                selected.publication.materialization.size_bytes)
            selected.require_record(record, record.identity)
            if _publication_from_manifest(writer, writer.read_manifest(relative)) != replace(selected.publication, created=False):
                raise PermissionError('curve amendment substitutes a withdrawn continuation publication')
            plan = record.target_plan
            home = writer.root.resolve(plan.specification.directory, for_write=False)
            require_separate_home(plan.specification.directory, specification.directory)
            require_separate_home(plan.specification.directory, original_plan.specification.directory)
            if (home in homes or writer.root.resolve(relative, for_write=False) != home / CONTINUATION_FILENAME
                    or record.specification.predecessor != specification.predecessor
                    or record.predecessor_bindings != original_bindings
                    or record.predecessor_terminals != retained.terminals
                    or record.unentered_training_packet != retained.training_packet
                    or (plan.workers, plan.environment_id, plan.specification.operations) != (
                        original_plan.workers, original_plan.environment_id, original_plan.specification.operations)):
                raise PermissionError('curve amendment changes a superseded derivation original lineage or operations')
            homes.add(home)
            owner = MatrixResearchProgrammeService(service=scoped)
            context = MatrixProgrammeProjectionContext(scoped, plan, None, home, {}, {})
            owner._load_bindings(context)
            authored = (home / PLAN_FILENAME).exists() or (home / PLAN_FILENAME).is_symlink()
            packet_pin = run_id = None
            require_selection = None
            if authored:
                actual_owner = scoped._composite_programme(directory=home)
                if type(actual_owner) is not MatrixResearchProgrammeService or actual_owner._plan(home) != plan:
                    raise PermissionError('curve amendment changes the superseded authored plan/descriptor')
                require_selection = _pin_original_selection(actual_owner, context)
                _future_absences(context, authored=True, run_id=None)
                _, request = context.bound_specification(context.binding('train'))
                packet, run, payloads = _withdrawn_packet(writer, context.child_directory('train'), plan.source_snapshot)
                if payloads.get('experiment-specification.json') != request.canonical_bytes():
                    raise PermissionError('curve amendment changes the superseded unentered TRAIN specification')
                packet_pin, run_id = ObjectIdentity.from_record(packet.packet_id, packet), run.run_plan_id
            else:
                _absent(home / (PLAN_FILENAME + '.manifest.json'))
                _absent(home / PROGRAMME_DESCRIPTOR_FILENAME)
            _future_absences(context, authored=authored, run_id=run_id)
            guards.append((context, authored, run_id, require_selection))
            packets.append((record.identity, packet_pin))

        def require_current():
            for context, authored, run_id, require_selection in guards:
                if require_selection is not None:
                    require_selection()
                _future_absences(context, authored=authored, run_id=run_id)
                if not authored:
                    for name in (PLAN_FILENAME, PLAN_FILENAME + '.manifest.json', PROGRAMME_DESCRIPTOR_FILENAME):
                        _absent(context.directory / name)
            writer.require_verification_snapshot()

        try:
            require_current()
            yield tuple(packets), require_current
        finally:
            require_current()
