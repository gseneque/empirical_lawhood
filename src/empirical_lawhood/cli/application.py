# SPDX-License-Identifier: MPL-2.0
"""Translate terminal selections into the shared application context."""

from pathlib import Path
import sys

from empirical_lawhood.api.application_contracts import ApplicationContext


def application_context_from_cli():
    from empirical_lawhood.cli import platform
    def path(value):
        return None if value is None else Path(value).absolute()
    return ApplicationContext("cli.selected", "Selected command context", Path(sys.executable).absolute(),
        project_root=path(platform.CLI_PROJECT_ROOT), operator_profile=path(platform.CLI_OPERATOR_PROFILE),
        artifact_root_contract=path(platform.CLI_ARTIFACT_ROOT_CONTRACT),
        catalog_relative_path=platform.CLI_CATALOG_RELATIVE_PATH,
        approval_checker_trust=path(platform.CLI_APPROVAL_CHECKER_TRUST),
        maximum_parallel_tasks=None, artifact_verification=str(platform.CLI_ARTIFACT_VERIFICATION))


def invoke_selected_application(operation, parameters, *, root, input_root=None, workers=None):
    """Keep terminal presentation and options outside the shared RC service."""
    from dataclasses import replace
    from uuid import uuid4
    from empirical_lawhood.api.application import execute_application
    from empirical_lawhood.api.application_contracts import ApplicationRequest
    context = replace(application_context_from_cli(), project_root=root,
                      input_root=input_root, maximum_parallel_tasks=workers)
    result = execute_application(context, ApplicationRequest(str(uuid4()), context.context_id,
                                                            operation, tuple(parameters.items())))
    return require_application_success(result)


def require_application_success(result):
    """Preserve the shared structured failure on the terminal's error stream."""
    if not result.succeeded:
        import typer
        from empirical_lawhood.api.application_contracts import response_bytes
        typer.echo(response_bytes(result).decode("utf-8"), err=True, nl=False)
        raise typer.Exit(code=2)
    return result.payload
