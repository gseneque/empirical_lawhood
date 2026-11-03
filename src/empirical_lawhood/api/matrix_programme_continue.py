# SPDX-License-Identifier: MPL-2.0
"""One public request from completed Matrix phases to eligible new execution."""
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from time import monotonic

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes


def continue_matrix_programme(service, *, predecessor_directory, output_dir, confirmed, maximum_parallel_tasks=None,
        pure_output_bytes=None):
    """Compose existing owners inside one finite evidence and source lifetime.

    All preparation is included. No cache is populated before this request and
    no retrospective report is required. Every actual scientific task retains
    its ordinary source, current input access and resource entry boundaries.
    """
    from .matrix_researcher_programme import MatrixResearchProgrammeService, _publish, PLAN_FILENAME
    from .matrix_researcher_programme_lineage import read_published_record
    from .selected_e4_bank_recipe import _publication_from_manifest
    from .recursive_authoring import implementation_binding
    from .retained_e3_evidence import retained_e3_evidence_context
    from empirical_lawhood.infrastructure.matrix_programme_inputs import _input_record_scope
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammePlan
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import (
        MatrixProgrammeSourceContinuationSpecification, MatrixProgrammeOutputContinuationSpecification,
        PROTOCOL_ID, OUTPUT_PROTOCOL_ID, require_separate_home,
    )
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    from empirical_lawhood.runtime.progress import report_progress
    if type(confirmed) is not bool or not confirmed:
        raise ValueError('Matrix continuation requires --yes before authoring and ordinary execution')
    if pure_output_bytes is not None and (type(pure_output_bytes) is not int or not 0 < pure_output_bytes <= 256 * 1024**2):
        raise ValueError('future PURE output allowance must be a positive integer within 256 MiB')
    if service.artifact_writer is None or service.storage_profile is None:
        raise ValueError('Matrix continuation requires its explicit operator profile and artifact destination')
    started = monotonic()
    root = Path(service.artifact_writer.root.contract.canonical_path)
    previous, target = Path(predecessor_directory), Path(output_dir)
    if (previous != previous.resolve(strict=True) or target != target.resolve(strict=False)
            or not previous.is_relative_to(root) or not target.is_relative_to(root)
            or any(path.is_symlink() for path in (previous, target, *previous.parents, *target.parents))):
        raise ValueError('Matrix continuation requires actual separate paths in the selected artifact root')
    require_separate_home(previous.relative_to(root).as_posix(), target.relative_to(root).as_posix())
    with ExitStack() as lifetime:
        evidence = lifetime.enter_context(retained_e3_evidence_context(service.artifact_writer))
        # Evidence shares a read-only snapshot. Publication remains on the
        # selected owning service; the snapshot supplies no write capability.
        owner = service._composite_programme(directory=previous)
        if type(owner) is not MatrixResearchProgrammeService:
            raise ValueError('Matrix continuation requires an actual retained Matrix programme')
        relative = (previous / PLAN_FILENAME).relative_to(root).as_posix()
        plan = read_published_record(evidence.writer, relative, MatrixResearchProgrammePlan, 64 * 1024**2)
        if owner._plan(previous) != plan or service._selected_workers(maximum_parallel_tasks) != plan.workers:
            raise PermissionError('Matrix continuation changes its original programme or selected concurrency')
        lifetime.enter_context(_input_record_scope(plan.specification.operations.metadata_budget.source_scan_bytes))
        publication = _publication_from_manifest(evidence.writer, evidence.writer.read_manifest(relative))
        predecessor = MatrixProgrammePublishedInput(plan.identity, publication)
        source = implementation_binding(service.project_root)
        source_pin = ObjectIdentity.from_record('recursive-member.implementation', source)
        directory = target.relative_to(root).as_posix()
        values = (predecessor, directory, source_pin)
        token = sha256(canonical_json_bytes(values if pure_output_bytes is None else (*values, pure_output_bytes))).hexdigest()
        if pure_output_bytes is None:
            specification = MatrixProgrammeSourceContinuationSpecification('continuation-request.' + token,
                predecessor, directory)
            protocol = PROTOCOL_ID
        else:
            specification = MatrixProgrammeOutputContinuationSpecification('continuation-request.' + token,
                predecessor, directory, pure_output_bytes)
            protocol = OUTPUT_PROTOCOL_ID
        selection = ExperimentFileInputSelection('continuation-sources.' + token, protocol, (), ())
        request = target / 'continuation-request'
        _publish(service.artifact_writer, request / 'specification.json', specification)
        _publish(service.artifact_writer, request / 'sources.json', selection)
        execution = ExecutionSelection(plan.workers, plan.environment_id, source_pin, str(root))
        report_progress(phase='matrix.continuation.preparation')
        derived = service.derive_inputs(specification_path=request / 'specification.json',
            source_selection_path=request / 'sources.json', metadata_directory=target / 'continuation-inputs',
            output_selection_path=target / 'continuation-inputs/inputs/sources.json', execution=execution)
        derived_seconds = monotonic() - started
        report_progress(phase='matrix.continuation.advance')
        successor = MatrixResearchProgrammeService(service=service)
        report = successor.continue_prepared(preparation=derived.preparation, output_dir=target,
            maximum_parallel_tasks=plan.workers, confirmed=True)
        return {'operation': 'MATRIX_SOURCE_CONTINUATION', 'predecessor_directory': str(previous),
            'authoring_dir': str(target), 'specification_path': str(derived.target_specification_path),
            'sources_path': str(derived.source_selection_path), 'source': source_pin.to_document(),
            'preparation_and_derivation_seconds': derived_seconds,
            'elapsed_seconds': monotonic() - started, 'programme_report': report,
            'native_entry_measurement': 'USE_ACTUAL_NATIVE_CONTACT_TIME_FROM_INVOCATION_START',
            'scientific_qualification': 'NOT_ESTABLISHED'}
