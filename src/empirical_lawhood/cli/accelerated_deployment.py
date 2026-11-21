# SPDX-License-Identifier: MPL-2.0
"""Local deployment and transport commands; provisioning stays upstream."""

import json
from pathlib import Path
from typing import Annotated

import typer

from empirical_lawhood.storage.transfer_files import prepare_transfer, seal_transfer, verify_transfer

from empirical_lawhood.api.accelerated_deployment import prepare_accelerated_deployment, archive_original_tree, verify_original_archive, observe_deployment_budget, supervise_deployment, restore_worker_environment


deployment_app = typer.Typer(no_args_is_help=True,
    help='Prepare upstream tasks, supervise authorized allocations and verify original-byte transfers.')


def _report(operation, *args, **kwargs):
    try:
        result = operation(*args, **kwargs)
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error
    typer.echo(json.dumps(result, indent=2, sort_keys=True))


@deployment_app.command('prepare')
def prepare(
    selection: Annotated[Path, typer.Option('--selection')],
    payload: Annotated[Path, typer.Option('--payload')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
):
    """Freeze the selected payload and write a single-machine task without provider contact."""
    _report(prepare_accelerated_deployment, selection, payload_root=payload,
        output_directory=output_dir)


@deployment_app.command('prepare-files')
def prepare_files(
    root: Annotated[Path, typer.Option('--root')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
    maximum_bytes: Annotated[int | None, typer.Option('--maximum-bytes', min=1)] = None,
    maximum_files: Annotated[int | None, typer.Option('--maximum-files', min=1)] = None,
):
    """Prepare inputs, evidence or logs for any host using their observed exact census."""
    _report(prepare_transfer, root, output_dir, maximum_bytes=maximum_bytes, maximum_files=maximum_files)


@deployment_app.command('seal-files')
def seal_files(
    root: Annotated[Path, typer.Option('--root')],
    manifest: Annotated[Path, typer.Option('--manifest')],
    maximum_bytes: Annotated[int | None, typer.Option('--maximum-bytes', min=1)] = None,
    maximum_files: Annotated[int | None, typer.Option('--maximum-files', min=1)] = None,
):
    """Hash an explicitly selected closed payload without changing its primary receipts."""
    _report(seal_transfer, root, manifest, maximum_bytes=maximum_bytes,
        maximum_files=maximum_files)


@deployment_app.command('verify-files')
def verify_files(
    root: Annotated[Path, typer.Option('--root')],
    manifest: Annotated[Path, typer.Option('--manifest')],
    sha256: Annotated[str, typer.Option('--sha256')],
):
    """Check every transferred file against an independently retained manifest digest."""
    _report(verify_transfer, root, manifest, expected_sha256=sha256)


@deployment_app.command('archive-originals')
def archive_originals(
    root: Annotated[Path, typer.Option('--root')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
    maximum_bytes: Annotated[int, typer.Option('--maximum-bytes', min=1)],
    maximum_entries: Annotated[int, typer.Option('--maximum-entries', min=1)],
):
    """Archive a closed original tree with links preserved and no scientific completion inference."""
    _report(archive_original_tree, root, output_directory=output_dir,
        maximum_bytes=maximum_bytes, maximum_entries=maximum_entries)


@deployment_app.command('verify-originals')
def verify_originals(
    package: Annotated[Path, typer.Option('--package')],
    manifest: Annotated[Path, typer.Option('--manifest')],
    sha256: Annotated[str, typer.Option('--sha256')],
):
    """Authenticate the complete return and compare every archive member without extraction."""
    _report(verify_original_archive, package, manifest, expected_sha256=sha256)


@deployment_app.command('observe-budget')
def observe_budget(
    selection: Annotated[Path, typer.Option('--selection')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
):
    """Retain current resource-filtered billing and conservative accounting through GET requests only."""
    _report(observe_deployment_budget, selection, output_directory=output_dir)


@deployment_app.command('watch-budget')
def watch_budget(
    selection: Annotated[Path, typer.Option('--selection')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
):
    """Supervise an owner-authorized allocation; cancel or retire compute at its financial stops."""
    _report(supervise_deployment, selection, output_directory=output_dir)


@deployment_app.command('restore-environment')
def restore_environment(
    selection: Annotated[Path, typer.Option('--selection')],
    payload: Annotated[Path, typer.Option('--payload')],
    manifest: Annotated[Path, typer.Option('--manifest')],
    sha256: Annotated[str, typer.Option('--sha256', envvar='EL_DEPLOYMENT_PAYLOAD_SHA256')],
    output_dir: Annotated[Path, typer.Option('--output-dir')],
):
    """Restore a separate worker prefix from sealed inputs without changing its original environment."""
    _report(restore_worker_environment, selection, payload_root=payload, manifest_path=manifest,
        expected_sha256=sha256, output_directory=output_dir)
