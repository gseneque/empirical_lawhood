# SPDX-License-Identifier: MPL-2.0
"""Explicit recursive authoring, development custody and contribution commands."""

from pathlib import Path
from typing import Annotated

import typer

from empirical_lawhood.cli.attempts import ATTEMPT_DIRECTORY_OPTION, attempt_stage, retained_command



def _authoring_input(path, helpers):
    """Select a closed known root schema; input cannot choose imports or code."""
    from empirical_lawhood.adapters._strict_json import loads_external_json
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
    selected = helpers._selected_input(path, maximum_bytes=16 * 1024**2, copy=False)
    document = loads_external_json(read_bounded_bytes(selected, maximum_bytes=16 * 1024**2))
    schema = document.get("schema") if isinstance(document, dict) else None
    consumer = "recursive-prospective" if schema == RecursiveProspectiveAuthoringSpec.SCHEMA else "recursive-inquiry"
    return helpers._configuration(path, consumer)


def register_recursive_commands(app):
    from empirical_lawhood.cli import integrations as h

    @app.command("recursive-inquiry-decide")
    @retained_command("campaign recursive-inquiry-decide", closed_output=True, native=False)
    def inquiry_decide(input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
                       output_dir: Annotated[Path, typer.Option("--output-dir", file_okay=False)],
                       attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Persist an authenticated inquiry decision before optional contribution export."""
        from dataclasses import fields
        from empirical_lawhood.api.recursive_inquiry import commit_inquiry_decision, decode_inquiry_decision_request
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        try:
            root, _, plane = h._storage()
            size = max(1, input.stat().st_size)
            request = decode_inquiry_decision_request(read_bounded_bytes(input, maximum_bytes=size))
            packet, records = commit_inquiry_decision(**{field.name: getattr(request, field.name) for field in fields(request)},
                project_root=root, artifact_writer=plane, output_dir=output_dir)
            report = {"status": "COMMITTED", "decision_dir": str(output_dir), "packet_sha256": packet.fingerprint(),
                "decision": records["decision.json"].to_document(), "native_contact": "none",
                "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-inquiry-result")
    @retained_command("campaign recursive-inquiry-result", closed_output=True, native=False)
    def inquiry_result(decision_dir: Annotated[Path, typer.Option("--decision-dir", exists=True, file_okay=False)],
                       historical: Annotated[bool, typer.Option("--historical", help="Read archived bytes without current source admission.")] = False,
                       attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Read an exact retained decision, alternatives, costs and successor intent."""
        from empirical_lawhood.api.recursive_inquiry import read_inquiry_decision, recover_inquiry_completion
        try:
            _, _, plane = h._storage()
            packet, records = read_inquiry_decision(directory=decision_dir, artifact_writer=plane,
                revalidate_sources=not historical)
            selected = next(row for row in records["menu.json"].alternatives
                            if row.alternative_id == records["decision.json"].selected_alternative_id)
            reused = (recover_inquiry_completion(decision_directory=decision_dir, artifact_writer=plane)
                      if not historical and getattr(selected, "reuse_completion", None) is not None else None)
            report = {"packet_sha256": packet.fingerprint(),
                "admission_status": "HISTORICAL_ARCHIVE" if historical else "CURRENT_SOURCE_VALIDATED",
                "decision": records["decision.json"].to_document(), "alternatives": records["menu.json"].to_document(),
                "state": records["state.json"].to_document(),
                "intent": records["intent.json"].to_document() if "intent.json" in records else None,
                "reused_completion": reused,
                "native_contact": "none", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-inquiry-author")
    @retained_command("campaign recursive-inquiry-author", closed_output=True, native=False)
    def inquiry_author(decision_dir: Annotated[Path, typer.Option("--decision-dir", exists=True, file_okay=False)],
                       origins: Annotated[Path, typer.Option("--origins", exists=True, dir_okay=False)],
                       output_dir: Annotated[Path, typer.Option("--output-dir", file_okay=False)],
                       supplier_dir: Annotated[Path | None, typer.Option("--supplier-dir", exists=True, file_okay=False)] = None,
                       initial_draft: Annotated[Path | None, typer.Option("--initial-draft", exists=True, dir_okay=False)] = None,
                       contribution_dir: Annotated[Path | None, typer.Option("--contribution-dir", exists=True, file_okay=False)] = None,
                       input_bindings: Annotated[list[str], typer.Option("--input-binding")] = [],
                       attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Bind the selected initial draft or registered successor of a persisted ACT decision."""
        from empirical_lawhood.api.recursive_inquiry import author_inquiry_successor
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
        try:
            root, _, plane = h._storage()
            size = max(1, origins.stat().st_size)
            selected_origins = decode_canonical_bytes(read_bounded_bytes(origins, maximum_bytes=size),
                RecursiveInputOrigins, maximum_bytes=size)
            bindings = []
            for value in input_bindings:
                key, separator, path = value.partition("=")
                if not separator or not key or not path:
                    raise ValueError("input binding requires INPUT_ID=PATH")
                bindings.append((key, Path(path)))
            report = author_inquiry_successor(decision_directory=decision_dir, supplier_directory=supplier_dir,
                initial_draft=None if initial_draft is None else _authoring_input(initial_draft, h),
                origins=selected_origins, project_root=root, artifact_writer=plane, output_dir=output_dir,
                input_bindings=tuple(bindings), contribution_dir=contribution_dir)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-inquiry-run")
    @retained_command("campaign recursive-inquiry-run", closed_output=True, native=True)
    def inquiry_run(authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
                    terminal_product_format: Annotated[str, typer.Option("--terminal-product-format", help="documents, references or compact; compact authenticates custody and defers scientific decoding.")] = "documents",
                    workers: Annotated[int, typer.Option("--workers", min=1, help="Maximum concurrent tasks within the selected CPU capacity.")] = 1,
                    attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Validate decision/intent/draft admission, then use existing execution or recovery."""
        from empirical_lawhood.api.recursive_inquiry import run_inquiry_successor
        try:
            root, _, plane = h._storage()
            report = run_inquiry_successor(directory=authoring_dir, project_root=root, artifact_writer=plane,
                terminal_product_format=terminal_product_format, maximum_parallel_tasks=workers)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-explain")
    @retained_command("campaign recursive-explain", closed_output=True, native=False)
    def explain(input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
                attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Explain partial requirements and selected scientific paths without contact."""
        from empirical_lawhood.api.recursive_authoring import explain_recursive_draft
        try:
            draft = _authoring_input(input, h)
            attempt_stage("recursive_design_explanation", native_contact="none")
            from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
            report = explain_recursive_draft(draft.draft if isinstance(draft, RecursiveProspectiveAuthoringSpec) else draft)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-author")
    @retained_command("campaign recursive-author", closed_output=True, native=False)
    def author(input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
               output_dir: Annotated[Path, typer.Option("--output-dir", file_okay=False)],
               input_bindings: Annotated[list[str], typer.Option("--input-binding", help="Exact INPUT_ID=PATH external member binding.")] = [],
               contribution_dir: Annotated[Path | None, typer.Option("--contribution-dir", exists=True, file_okay=False)] = None,
               attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Freeze a selected wave with exact implementations and source/plan correspondence."""
        from empirical_lawhood.api.recursive_authoring import author_recursive_wave
        try:
            root, _, plane = h._storage()
            draft = _authoring_input(input, h)
            bindings = []
            for value in input_bindings:
                key, separator, path = value.partition("=")
                if not separator or not key or not path:
                    raise ValueError("input binding requires INPUT_ID=PATH")
                bindings.append((key, Path(path)))
            attempt_stage("recursive_authoring_preflight", native_contact="none")
            from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
            if isinstance(draft, RecursiveProspectiveAuthoringSpec):
                if contribution_dir is not None:
                    raise ValueError("prospective parents bind through their declared qualified receipt operands")
                from empirical_lawhood.api.recursive_prospective_authoring import author_recursive_prospective
                report = author_recursive_prospective(spec=draft, project_root=root, artifact_writer=plane,
                                                     output_dir=output_dir, input_bindings=tuple(bindings))
            else:
                report = author_recursive_wave(draft=draft, project_root=root, artifact_writer=plane,
                                              output_dir=output_dir, input_bindings=tuple(bindings), contribution_dir=contribution_dir)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-development-run")
    @retained_command("campaign recursive-development-run", closed_output=True, native=True)
    def run(authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
            terminal_product_format: Annotated[str, typer.Option("--terminal-product-format", help="documents, references or compact; compact defers scientific decoding.")] = "documents",
            workers: Annotated[int, typer.Option("--workers", min=1, help="Maximum concurrent tasks within the selected CPU capacity.")] = 1,
            attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Execute registered exposed tasks or recover the exact completed receipts."""
        from empirical_lawhood.api.recursive_execution import run_recursive_wave
        try:
            root, _, plane = h._storage()
            attempt_stage("recursive_execution_preflight", native_contact="possible")
            report = run_recursive_wave(directory=authoring_dir, project_root=root, artifact_writer=plane,
                terminal_product_format=terminal_product_format, maximum_parallel_tasks=workers)
            attempt_stage("recursive_execution_completed", native_contact=report["native_contact"])
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-development-result")
    @retained_command("campaign recursive-development-result", closed_output=True, native=False)
    def result(authoring_dir: Annotated[Path, typer.Option("--authoring-dir", exists=True, file_okay=False)],
               terminal_product_format: Annotated[str, typer.Option("--terminal-product-format", help="documents, references or compact; compact authenticates every retained byte without scientific projection.")] = "documents",
               allow_partial: Annotated[bool, typer.Option("--allow-partial", help="Read complete task census and retained receipts before terminal publication; does not resume work.")] = False,
               attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Authenticate every completed product and terminal disposition without acquisition."""
        from empirical_lawhood.api.recursive_execution import read_recursive_wave
        try:
            _, _, plane = h._storage(read_only=True)
            attempt_stage("recursive_retained_result", native_contact="none")
            report = read_recursive_wave(directory=authoring_dir, artifact_writer=plane,
                terminal_product_format=terminal_product_format, allow_partial=allow_partial)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("recursive-contribution")
    @retained_command("campaign recursive-contribution", closed_output=True, native=False)
    def contribution(authoring_dir: Annotated[Path | None, typer.Option("--authoring-dir", exists=True, file_okay=False)] = None,
                     contribution_dir: Annotated[Path | None, typer.Option("--contribution-dir", exists=True, file_okay=False)] = None,
                     output_dir: Annotated[Path | None, typer.Option("--output-dir", file_okay=False)] = None,
                     attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None):
        """Inspect or explicitly export an assessed contribution with authenticated evidence closure."""
        from empirical_lawhood.api.recursive_contributions import inspect_recursive_contribution, export_recursive_contribution
        try:
            root, _, plane = h._storage()
            attempt_stage("recursive_contribution_authentication", native_contact="none")
            if contribution_dir is not None and authoring_dir is None and output_dir is None:
                report = inspect_recursive_contribution(directory=contribution_dir, artifact_writer=plane)
            elif authoring_dir is not None and output_dir is not None and contribution_dir is None:
                report = export_recursive_contribution(directory=authoring_dir, output_dir=output_dir,
                                                       project_root=root, artifact_writer=plane)
            else:
                raise ValueError("select --contribution-dir to inspect, or --authoring-dir and --output-dir to export")
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)
