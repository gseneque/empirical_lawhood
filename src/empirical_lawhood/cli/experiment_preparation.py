# SPDX-License-Identifier: MPL-2.0
"""Specification preparation and complete dependency reports without native work."""

from pathlib import Path
from typing import Annotated
import json

import typer

from empirical_lawhood.cli.attempts import (
    ATTEMPT_DIRECTORY_OPTION, attempt_input, attempt_stage, emit_development_report, retained_command,
)
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.cli.progress import PROGRESS_FILE_OPTION, progress_command


READ_ACCESS_OPTION = typer.Option('--read-access', help=(
    'Copied current locator file; repeat for the complete original product or wave roster. '
    'Selects existing grants without changing original scientific evidence.'))


def _emit_execution_report(report, *, issued_preview=False):
    # Only the direct issued owner's explicit refusal proves nonexecution.
    # Generic success, an absent --yes, or a composite report cannot do so.
    if (issued_preview and report.get('schema') == 'empirical-lawhood/api/result'
            and report.get('status') == 'BLOCKED'
            and report.get('reason_codes') == ['WRITE_CONFIRMATION_REQUIRED']
            and isinstance(report.get('payload'), dict)
            and report['payload'].get('confirmed') is False):
        attempt_stage('execution_not_confirmed', native_contact='none')
    emit_development_report(report)


def _read_access_options(paths, *, specification_path=None, directory=None, artifact_writer=None):
    if not paths:
        return {}
    from empirical_lawhood.api.codecs import MAX_AUTHORING_BYTES
    from empirical_lawhood.api.experiment_read_access import (
        experiment_read_access_protocol, load_experiment_read_access,
    )

    protocol_id = experiment_read_access_protocol(specification_path=specification_path,
        directory=directory, artifact_writer=artifact_writer)

    selected = tuple(attempt_input(path, maximum_bytes=MAX_AUTHORING_BYTES,
        role='experiment-read-access', copy=False) for path in paths)
    return {'read_access': load_experiment_read_access(selected, protocol_id=protocol_id)}


def _execution_selection(environment_id, output_root, workers, source_snapshot_path=None, *, storage_profile=None):
    """Resolve the existing profile/snapshot owner once for preparation routes."""
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, select_experiment_workers
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from empirical_lawhood.planning.study_issue import ImplementationSourceClosure

    from empirical_lawhood.cli import platform
    if storage_profile is None and platform.CLI_OPERATOR_PROFILE is not None:
        from empirical_lawhood.api.codecs import load_registered_authoring
        from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile

        storage_profile = load_registered_authoring(platform.CLI_OPERATOR_PROFILE,
            root_schemas={OperatorStorageProfile.SCHEMA: OperatorStorageProfile})
    workers = select_experiment_workers(workers,
        profile_maximum=getattr(storage_profile, "maximum_parallel_tasks", None))
    snapshot = None
    if source_snapshot_path is not None:
        raw = read_bounded_bytes(attempt_input(source_snapshot_path, maximum_bytes=None,
            role="implementation-snapshot", copy=False), maximum_bytes=None)
        source_types = {kind.SCHEMA: kind for kind in (RecursiveImplementationBinding, ImplementationSourceClosure)}
        document = json.loads(raw)
        kind = source_types.get(document.get("schema")) if type(document) is dict else None
        if kind is None:
            raise ValueError("experiment source snapshot lacks a supported exact implementation record")
        record = decode_canonical_bytes(raw, kind, maximum_bytes=None)
        snapshot = ObjectIdentity.from_record("recursive-member.implementation", record)
    return ExecutionSelection(workers=workers, environment_id=environment_id,
        source_snapshot=snapshot, output_root=None if output_root is None else str(output_root))


def _prepare_record(input_path, protocol_path, environment_id, output_root, workers,
                    sources_path=None, source_snapshot_path=None, *, storage_profile=None, programme_service=None,
                    read_access=None, authoring=False):
    from empirical_lawhood.api.experiment_preparation import (
        _protocol, load_experiment_inputs, load_experiment_specification, prepare_experiment,
    )
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes

    specification = load_experiment_specification(input_path)
    selected = attempt_input(input_path, maximum_bytes=None, role="experiment-specification",
        consumer=_protocol(specification).consumer_id)
    specification = load_experiment_specification(selected)
    if read_access is not None and sources_path is None:
        raise ValueError('Current input access requires the exact --sources selection')
    from empirical_lawhood.cli import platform
    if (programme_service is None and sources_path is not None
            and platform.CLI_OPERATOR_PROFILE is not None):
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import integrations as helpers
        root, selected_profile, plane = helpers._storage()
        programme_service = ExperimentProgrammeService(root, plane, selected_profile,
            catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
            approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
            operator_artifact_root_contract=platform._selected_artifact_root_contract())
    if programme_service is not None:
        storage_profile = programme_service.storage_profile
    elif read_access is not None:
        raise ValueError("Current input access requires the selected operator profile and artifact root")
    protocol_bytes = (None if protocol_path is None else read_bounded_bytes(
        attempt_input(protocol_path, maximum_bytes=None, role="scientific-protocol", copy=False),
        maximum_bytes=None))
    resolved = (None if sources_path is None else load_experiment_inputs(specification,
        attempt_input(sources_path, maximum_bytes=None, role="experiment-source-selection", copy=False),
        artifact_writer=None if programme_service is None else programme_service.artifact_writer,
        read_access=read_access))
    execution = _execution_selection(environment_id, output_root, workers,
        source_snapshot_path, storage_profile=storage_profile)
    # Authoring owns the current prerequisite check through its publication
    # boundary. Do not open and close that same context just to build its input.
    prepare = prepare_experiment if programme_service is None or authoring else programme_service.prepare
    preparation = prepare(specification, protocol_bytes=protocol_bytes,
        scientific_inputs=None if resolved is None else resolved.scientific_inputs,
        method_inputs=None if resolved is None else resolved.method_inputs,
        execution=execution)
    return preparation


def _prepare(*args, **kwargs):
    from empirical_lawhood.api.experiment_preparation import experiment_preparation_report
    return experiment_preparation_report(_prepare_record(*args, **kwargs))


def register_experiment_commands(campaign_app: typer.Typer) -> None:
    @campaign_app.command('matrix-continue')
    @retained_command('campaign matrix-continue', closed_output=True, native=True)
    @progress_command('campaign matrix-continue')
    def matrix_continue(
        authoring_dir: Annotated[Path, typer.Option('--authoring-dir', exists=True, file_okay=False,
            help='Actual completed-E3 or completed-E4-DEV predecessor, including a supported stopped input-only E4 child.')],
        output_dir: Annotated[Path, typer.Option('--output-dir',
            help='Explicit disjoint new programme directory in the selected artifact root.')],
        workers: Annotated[int | None, typer.Option('--workers', min=1)] = None,
        pure_output_bytes: Annotated[int | None, typer.Option('--pure-output-bytes', min=1, max=268435456,
            help='After completed E4 DEV and structure, increase only later unentered response-score output allowances.')] = None,
        yes: Annotated[bool, typer.Option('--yes', help='Continue through ordinary authenticated scientific execution.')] = False,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Continue completed Matrix phases through ordinary preparation and eligible execution."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import platform, integrations as helpers
        try:
            root, profile, plane = helpers._storage()
            service = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract())
            emit_development_report(service.continue_matrix(predecessor_directory=authoring_dir,
                output_dir=output_dir, maximum_parallel_tasks=workers, confirmed=yes,
                **({} if pure_output_bytes is None else {'pure_output_bytes': pure_output_bytes})))
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-derive-inputs")
    @retained_command("campaign experiment-derive-inputs", closed_output=True, native=False)
    @progress_command("campaign experiment-derive-inputs")
    def experiment_derive_inputs(
        input_path: Annotated[Path, typer.Option("--input", help="Copied typed experiment specification.")],
        sources_path: Annotated[Path, typer.Option("--sources", help="Exact original/request input selector.")],
        metadata_directory: Annotated[Path, typer.Option("--metadata-directory", help="Explicit current metadata directory under the guarded input plane.")],
        output_selection_path: Annotated[Path, typer.Option("--output-selection", help="New selector alongside the original source selector.")],
        source_snapshot_path: Annotated[Path | None, typer.Option("--source-snapshot")] = None,
        environment_id: Annotated[str | None, typer.Option("--environment-id")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Must agree with the selected operator profile.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Derive current input metadata and report exact remaining prerequisites."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.api.experiment_preparation import experiment_input_derivation_report
        from empirical_lawhood.cli import platform, integrations as helpers
        try:
            root, profile, plane = helpers._storage()
            execution = _execution_selection(environment_id, Path(plane.root.contract.canonical_path), workers,
                source_snapshot_path, storage_profile=profile)
            service = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract())
            result = service.derive_inputs(specification_path=attempt_input(input_path, maximum_bytes=None,
                role="experiment-specification", copy=False),
                source_selection_path=attempt_input(sources_path, maximum_bytes=None,
                    role="experiment-source-selection", copy=False),
                metadata_directory=metadata_directory, output_selection_path=output_selection_path, execution=execution,
                **_read_access_options(read_access_paths, specification_path=input_path, artifact_writer=plane))
            emit_development_report(experiment_input_derivation_report(result))
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command('experiment-export-products')
    @retained_command('campaign experiment-export-products',closed_output=True,native=False)
    @progress_command('campaign experiment-export-products')
    def experiment_export_products(
        authoring_dir: Annotated[Path,typer.Option('--authoring-dir',help='Exact retained public experiment directory.')],
        selection_path: Annotated[Path,typer.Option('--selection',help='Copied typed export selection for its owning protocol.')],
        programme_request_path: Annotated[Path | None, typer.Option('--programme-request',
            help='Current component authority and source selections for this exact composite programme.')] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path|None,ATTEMPT_DIRECTORY_OPTION]=None,
        progress_file: Annotated[Path|None,PROGRESS_FILE_OPTION]=None,
    )->None:
        """Publish derived products from complete original receipts; no acquisition."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import platform,integrations as helpers
        try:
            if read_access_paths and programme_request_path is not None:
                raise ValueError('--read-access refuses composite product export options')
            root,profile,plane=helpers._storage()
            service=ExperimentProgrammeService(root,plane,profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract())
            emit_development_report(service.export_products(directory=authoring_dir,
                selection_path=attempt_input(selection_path,maximum_bytes=None,role='experiment-product-export-selection',copy=False),
                **({} if programme_request_path is None else {'programme_request_path': attempt_input(
                    programme_request_path, maximum_bytes=None, role='composite-programme-request', copy=False)}),
                **_read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)))
        except (ValueError,TypeError,OSError,RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-explain")
    @retained_command("campaign experiment-explain", closed_output=True, native=False)
    @progress_command("campaign experiment-explain")
    def experiment_explain(
        input_path: Annotated[Path, typer.Option("--input", help="Copied experiment specification.")],
        protocol_path: Annotated[Path | None, typer.Option("--protocol", help="Exact selected scientific protocol bytes.")] = None,
        sources_path: Annotated[Path | None, typer.Option("--sources", help="Exact domain source bindings for this specification.")] = None,
        source_snapshot_path: Annotated[Path | None, typer.Option("--source-snapshot", help="Retained implementation binding; execution checks actual worker identity.")] = None,
        environment_id: Annotated[str | None, typer.Option("--environment-id")] = None,
        output_root: Annotated[Path | None, typer.Option("--output-root")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Worker concurrency; defaults to the explicitly selected operator profile.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Explain the complete selected census and entry dependencies; no contact."""
        try:
            if read_access_paths and sources_path is None:
                raise ValueError('--read-access requires the exact --sources selection')
            emit_development_report(_prepare(input_path, protocol_path, environment_id, output_root, workers,
                                             sources_path, source_snapshot_path,
                                             **_read_access_options(read_access_paths, specification_path=input_path)))
        except (ValueError, TypeError, OSError, BoundedFileIOError) as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=2) from error

    @campaign_app.command("experiment-author")
    @retained_command("campaign experiment-author", closed_output=True, native=False)
    @progress_command("campaign experiment-author")
    def experiment_author(
        input_path: Annotated[Path, typer.Option("--input", help="Copied experiment specification.")],
        sources_path: Annotated[Path, typer.Option("--sources", help="Exact selected domain input bindings.")],
        source_snapshot_path: Annotated[Path, typer.Option("--source-snapshot", help="Exact selected implementation binding.")],
        environment_id: Annotated[str, typer.Option("--environment-id")],
        output_dir: Annotated[Path, typer.Option("--output-dir", help="New directory under selected guarded custody.")],
        protocol_path: Annotated[Path | None, typer.Option("--protocol")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Worker concurrency; defaults to the explicitly selected operator profile.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Freeze all derived operations and bindings without manual projections."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import platform
        from empirical_lawhood.cli import integrations as helpers

        try:
            root, profile, plane = helpers._storage()
            service = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract())
            access_options = _read_access_options(read_access_paths, specification_path=input_path, artifact_writer=plane)
            preparation = _prepare_record(input_path, protocol_path, environment_id,
                Path(plane.root.contract.canonical_path), workers, sources_path, source_snapshot_path,
                storage_profile=profile, programme_service=service, authoring=True, **access_options)
            emit_development_report(service.author(preparation=preparation, output_dir=output_dir, **access_options))
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-run")
    @retained_command("campaign experiment-run", closed_output=True, native=True)
    @progress_command("campaign experiment-run")
    def experiment_run(
        authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
        programme_request_path: Annotated[Path | None, typer.Option("--programme-request",
            help="Copied component authority and source selections for this exact composite programme.")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Worker concurrency; defaults to the explicitly selected operator profile.")] = None,
        plan_path: Annotated[Path | None, typer.Option("--plan", help="Original issued campaign package for a prospective programme.")] = None,
        yes: Annotated[bool, typer.Option("--yes", help="Execute an issued or Matrix programme after its existing authority checks.")] = False,
        reveal_authority_id: Annotated[str | None, typer.Option("--reveal-authority-id")] = None,
        parent_record: Annotated[Path | None, typer.Option("--parent-record")] = None,
        parent_input_bindings: Annotated[list[Path] | None, typer.Option("--parent-input-binding")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Run the frozen programme through its existing execution owner."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.api.results import RunCampaignRequest
        from empirical_lawhood.cli import platform
        from empirical_lawhood.cli import integrations as helpers

        try:
            if read_access_paths and programme_request_path is not None:
                raise ValueError('--read-access refuses composite execution options')
            root, profile, plane = helpers._storage()
            if programme_request_path is not None:
                if plan_path is not None or reveal_authority_id or parent_record or parent_input_bindings:
                    raise ValueError("--programme-request refuses single-campaign authority and recovery options")
                options = {"programme_request_path": attempt_input(programme_request_path,
                    maximum_bytes=None, role="composite-programme-request", copy=False), "confirmed": yes}
            else:
                options = ({"confirmed": True} if yes else {}) if plan_path is None else {"request": RunCampaignRequest(plan_path, confirmed=yes,
                    reveal_authority_id=reveal_authority_id, parent_record_path=parent_record,
                    parent_input_binding_paths=tuple(parent_input_bindings or ()))}
                if plan_path is None and (reveal_authority_id or parent_record or parent_input_bindings):
                    raise ValueError("issued programme execution options require --plan")
            access_options = _read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)
            attempt_stage('programme_execution_requested')
            report = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).run(
                directory=authoring_dir, maximum_parallel_tasks=workers, **options, **access_options)
            _emit_execution_report(report, issued_preview=plan_path is not None and not yes)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-read")
    @retained_command("campaign experiment-read", closed_output=True, native=False)
    @progress_command("campaign experiment-read")
    def experiment_read(
        authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
        programme_request_path: Annotated[Path | None, typer.Option("--programme-request",
            help="Copied component authority and source selections for this exact composite programme.")] = None,
        allow_partial: Annotated[bool, typer.Option("--allow-partial", help="Inspect retained partial custody without resuming work.")] = False,
        assess_incomplete: Annotated[bool, typer.Option("--assess-incomplete", help="Assess a supported incomplete issued result with current reveal authority.")] = False,
        run_id: Annotated[str | None, typer.Option("--run", help="Read the issued programme's retained campaign.")] = None,
        include_attempt_history: Annotated[bool, typer.Option("--attempt-history")] = False,
        reveal_authority_id: Annotated[str | None, typer.Option("--reveal-authority-id", help="Authorize the protected scientific result read.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Read complete outcomes or an explicitly partial receipt census."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.api.results import CampaignStatusRequest
        from empirical_lawhood.cli import platform
        from empirical_lawhood.cli import integrations as helpers

        try:
            if read_access_paths and programme_request_path is not None:
                raise ValueError('--read-access refuses composite result options')
            if assess_incomplete and (allow_partial or run_id is None or programme_request_path is not None):
                raise ValueError("--assess-incomplete requires --run and refuses metadata-only or composite read selections")
            root, profile, plane = helpers._storage(read_only=True)
            if programme_request_path is not None:
                if run_id is not None or include_attempt_history or reveal_authority_id:
                    raise ValueError("--programme-request refuses single-campaign authority and recovery options")
                options = {"programme_request_path": attempt_input(programme_request_path,
                    maximum_bytes=None, role="composite-programme-request", copy=False)}
            else:
                options = {} if run_id is None else {"request": CampaignStatusRequest(run_id,
                    include_attempt_history=include_attempt_history), "reveal_authority_id": reveal_authority_id}
                if run_id is None and (include_attempt_history or reveal_authority_id):
                    raise ValueError("issued programme attempt history and reveal authority require --run")
            emit_development_report(ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).read(
                directory=authoring_dir, allow_partial=allow_partial, assess_incomplete=assess_incomplete, **options,
                **_read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)))
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command('experiment-prepare-native-continuation')
    @retained_command('campaign experiment-prepare-native-continuation', closed_output=True, native=False)
    @progress_command('campaign experiment-prepare-native-continuation')
    def experiment_prepare_native_continuation(
        authoring_dir: Annotated[Path, typer.Option('--authoring-dir', exists=True, file_okay=False)],
        run_id: Annotated[str, typer.Option('--run', help='Exact original development run with incomplete native custody.')],
        output_dir: Annotated[Path, typer.Option('--output-dir', help='Disjoint proposal directory beneath the selected artifact root.')],
        worker_interpreter: Annotated[Path, typer.Option('--worker-interpreter', help='Original frozen installed worker interpreter.')],
        worker_source_root: Annotated[Path, typer.Option('--worker-source-root', help='Original frozen worker source distribution.')],
        preparation_instruction_path: Annotated[Path, typer.Option('--preparation-instruction', help='Exact retained instruction requesting a proposal; grants no execution.')],
        pure_output_bytes: Annotated[int, typer.Option('--pure-output-bytes', min=1, max=256 * 1024**2,
            help='Proposed bounded PURE output allowance; no original reservation changes during preparation.')],
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Prepare a reviewable incomplete-native proposal without task execution."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import integrations as helpers
        from empirical_lawhood.cli import platform
        try:
            instruction = attempt_input(preparation_instruction_path, maximum_bytes=1024 * 1024,
                role='native-continuation-preparation-instruction', copy=False)
            root, profile, plane = helpers._storage()
            access_options = _read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)
            attempt_stage('native_continuation_proposal_requested', native_contact='none')
            report = ExperimentProgrammeService(root, plane, profile,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).prepare_native_continuation(
                directory=authoring_dir, run_id=run_id, output_dir=output_dir,
                preparation_instruction_path=instruction, worker_interpreter=worker_interpreter,
                worker_source_root=worker_source_root, pure_output_bytes=pure_output_bytes, **access_options)
            emit_development_report(report)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command('experiment-repair-structure')
    @retained_command('campaign experiment-repair-structure', closed_output=True)
    @progress_command('campaign experiment-repair-structure')
    def experiment_repair_structure(
        authoring_dir: Annotated[Path, typer.Option('--authoring-dir', exists=True, file_okay=False,
            help='Original completed E4 development acquisition directory.')],
        repair_instruction_path: Annotated[Path, typer.Option('--repair-instruction',
            help='Retained instruction for the separate PURE structural repair.')],
        workers: Annotated[int | None, typer.Option('--workers', min=1)] = None,
        yes: Annotated[bool, typer.Option('--yes', help='Select separate PURE production over unchanged original inputs.')] = False,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Repair a failed E4 structural child without new native acquisition."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import integrations as helpers
        from empirical_lawhood.cli import platform
        try:
            instruction = attempt_input(repair_instruction_path, maximum_bytes=1024 * 1024,
                role='development-structure-repair-instruction', copy=False)
            root, profile, plane = helpers._storage()
            access_options = _read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)
            report = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).repair_development_structure(
                directory=authoring_dir, repair_instruction_path=instruction, maximum_parallel_tasks=workers,
                confirmed=yes, **access_options)
            emit_development_report(report)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command('experiment-continue-native')
    @retained_command('campaign experiment-continue-native', closed_output=True, native=True)
    @progress_command('campaign experiment-continue-native')
    def experiment_continue_native(
        authoring_dir: Annotated[Path, typer.Option('--authoring-dir', exists=True, file_okay=False)],
        run_id: Annotated[str, typer.Option('--run', help='Exact original exposed development run.')],
        proposal_path: Annotated[Path, typer.Option('--proposal', help='Exact published incomplete-native proposal.')],
        execution_instruction_path: Annotated[Path, typer.Option('--execution-instruction', help='Retained separate execution selection; preparation alone grants no execution.')],
        workers: Annotated[int | None, typer.Option('--workers', min=1, help='Original worker concurrency from the selected profile.')] = None,
        yes: Annotated[bool, typer.Option('--yes', help='Select one separate attempt for each reviewed incomplete case and continue eligible original work.')] = False,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Validate or explicitly execute a separate native continuation."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.cli import integrations as helpers
        from empirical_lawhood.cli import platform
        try:
            instruction = attempt_input(execution_instruction_path, maximum_bytes=1024 * 1024,
                role='native-continuation-execution-selection', copy=False)
            proposal = attempt_input(proposal_path, maximum_bytes=None,
                role='native-continuation-proposal', copy=False)
            root, profile, plane = helpers._storage()
            access_options = _read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)
            report = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).continue_native(
                directory=authoring_dir, run_id=run_id, proposal_path=proposal,
                execution_instruction_path=instruction, maximum_parallel_tasks=workers,
                confirmed=yes, **access_options)
            emit_development_report(report)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-recover")
    @retained_command("campaign experiment-recover", closed_output=True, native=True)
    @progress_command("campaign experiment-recover")
    def experiment_recover(
        authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
        programme_request_path: Annotated[Path | None, typer.Option("--programme-request",
            help="Copied component authority and source selections for this exact composite programme.")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Worker concurrency; defaults to the explicitly selected operator profile.")] = None,
        run_id: Annotated[str | None, typer.Option("--run", help="Resume the original issued campaign.")] = None,
        yes: Annotated[bool, typer.Option("--yes", help="Recover an issued or Matrix programme after its existing authority checks.")] = False,
        reveal_authority_id: Annotated[str | None, typer.Option("--reveal-authority-id")] = None,
        parent_record: Annotated[Path | None, typer.Option("--parent-record")] = None,
        parent_input_bindings: Annotated[list[Path] | None, typer.Option("--parent-input-binding")] = None,
        reconcile_only: Annotated[bool, typer.Option("--reconcile-only", help="Reconcile retained failed attempts without scheduling work.")] = False,
        custody_only: Annotated[bool, typer.Option("--custody-only",
            help="Close exhausted initial development custody without task execution.")] = False,
        repair_retained_e3: Annotated[bool, typer.Option("--repair-retained-e3",
            help="Bind a repaired controller for a failed PURE retained-model adoption; preserve completed receipts and frozen native work.")] = False,
        repair_development_output_bytes: Annotated[int | None, typer.Option("--repair-development-output-bytes", min=1, max=256 * 1024**2,
            help="Raise the output allowance for resource-refused PURE development calculations; pair with controller repair for an unfinished graph.")] = None,
        repair_development_controller: Annotated[bool, typer.Option("--repair-development-controller",
            help="Resume an interrupted development graph with its frozen workers; pair with --repair-development-output-bytes.")] = False,
        worker_interpreter: Annotated[Path | None, typer.Option("--worker-interpreter",
            help="Original frozen installed worker interpreter, required for selective repair.")] = None,
        worker_source_root: Annotated[Path | None, typer.Option("--worker-source-root",
            help="Original frozen worker source distribution, required for selective repair.")] = None,
        repair_instruction_path: Annotated[Path | None, typer.Option("--repair-instruction",
            help="Exact retained owner instruction file authorizing the selective PURE repair.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Resume frozen receipt-based work; uncertain native contact refuses."""
        from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
        from empirical_lawhood.api.results import ResumeCampaignRequest
        from empirical_lawhood.cli import platform
        from empirical_lawhood.cli import integrations as helpers

        try:
            repair_options = {}
            development_repair = repair_development_output_bytes is not None or repair_development_controller
            if repair_retained_e3 or development_repair or any(value is not None for value in (
                    worker_interpreter, worker_source_root, repair_instruction_path)):
                if (repair_retained_e3 == development_repair or not yes or run_id is None or programme_request_path is not None
                        or custody_only or reconcile_only or parent_record or parent_input_bindings
                        or development_repair and reveal_authority_id is not None
                        or repair_development_controller and repair_development_output_bytes is None
                        or worker_interpreter is None or worker_source_root is None or repair_instruction_path is None):
                    selected_repair = '--repair-retained-e3' if repair_retained_e3 else '--repair-development-output-bytes'
                    raise ValueError(selected_repair + ' requires --run, --yes, both frozen worker paths and --repair-instruction; select exactly one repair')
                repair_options = {**({'repair_retained_e3': True} if repair_retained_e3 else
                    {'repair_development_output_bytes': repair_development_output_bytes}), 'worker_interpreter': worker_interpreter,
                    'worker_source_root': worker_source_root, 'repair_instruction_path': attempt_input(
                        repair_instruction_path, maximum_bytes=1024 * 1024,
                        role='retained-e3-repair-instruction' if repair_retained_e3 else 'development-output-repair-instruction', copy=False)}
                if repair_development_controller:
                    repair_options['repair_development_controller'] = True
            if read_access_paths and (programme_request_path is not None or custody_only):
                raise ValueError('--read-access refuses composite and custody-only recovery options')
            if custody_only and (programme_request_path is not None or workers is not None or run_id is not None
                    or yes or reveal_authority_id or parent_record or parent_input_bindings
                    or reconcile_only):
                raise ValueError("--custody-only refuses execution and issued recovery options")
            root, profile, plane = helpers._storage()
            if programme_request_path is not None:
                if run_id is not None or reveal_authority_id or parent_record or parent_input_bindings or reconcile_only:
                    raise ValueError("--programme-request refuses single-campaign authority and recovery options")
                options = {"programme_request_path": attempt_input(programme_request_path,
                    maximum_bytes=None, role="composite-programme-request", copy=False), "confirmed": yes}
            else:
                options = ({"confirmed": True} if yes else {}) if run_id is None else {"request": ResumeCampaignRequest(run_id, confirmed=yes,
                    reveal_authority_id=reveal_authority_id, parent_record_path=parent_record,
                    parent_input_binding_paths=tuple(parent_input_bindings or ()),
                    reconcile_only=reconcile_only)}
                if run_id is None and (reveal_authority_id or parent_record or parent_input_bindings
                        or reconcile_only):
                    raise ValueError("issued programme recovery options require --run")
            access_options = _read_access_options(read_access_paths, directory=authoring_dir, artifact_writer=plane)
            attempt_stage('programme_recovery_requested')
            report = ExperimentProgrammeService(root, plane, profile,
                catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
                approval_checker_trust_path=platform.CLI_APPROVAL_CHECKER_TRUST,
                operator_artifact_root_contract=platform._selected_artifact_root_contract()).recover(
                directory=authoring_dir, maximum_parallel_tasks=workers,
                **({"custody_only": True} if custody_only else {}), **options, **access_options, **repair_options)
            _emit_execution_report(report, issued_preview=run_id is not None and not yes and not reconcile_only)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            helpers._error(error)

    @campaign_app.command("experiment-prepare")
    @retained_command("campaign experiment-prepare", closed_output=True, native=False)
    @progress_command("campaign experiment-prepare")
    def experiment_prepare(
        input_path: Annotated[Path, typer.Option("--input", help="Copied experiment specification.")],
        output: Annotated[Path, typer.Option("--output", help="New preparation report file.")],
        protocol_path: Annotated[Path | None, typer.Option("--protocol", help="Exact selected scientific protocol bytes.")] = None,
        sources_path: Annotated[Path | None, typer.Option("--sources", help="Exact domain source bindings for this specification.")] = None,
        source_snapshot_path: Annotated[Path | None, typer.Option("--source-snapshot", help="Retained implementation binding; execution checks actual worker identity.")] = None,
        environment_id: Annotated[str | None, typer.Option("--environment-id")] = None,
        output_root: Annotated[Path | None, typer.Option("--output-root")] = None,
        workers: Annotated[int | None, typer.Option("--workers", min=1, help="Worker concurrency; defaults to the explicitly selected operator profile.")] = None,
        read_access_paths: Annotated[list[Path] | None, READ_ACCESS_OPTION] = None,
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
        progress_file: Annotated[Path | None, PROGRESS_FILE_OPTION] = None,
    ) -> None:
        """Retain a new complete preparation report without issue or native work."""
        from empirical_lawhood.api.configuration import _write_new_file

        try:
            if read_access_paths and sources_path is None:
                raise ValueError('--read-access requires the exact --sources selection')
            report = _prepare(input_path, protocol_path, environment_id, output_root, workers,
                              sources_path, source_snapshot_path,
                              **_read_access_options(read_access_paths, specification_path=input_path))
            payload = (json.dumps(report, allow_nan=False, ensure_ascii=True,
                                  sort_keys=True, separators=(",", ":")) + "\n").encode()
            _write_new_file(output, payload)
            emit_development_report({**report, "preparation_report": str(output.resolve())})
        except (ValueError, TypeError, OSError, BoundedFileIOError) as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=2) from error
