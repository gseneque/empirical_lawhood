# SPDX-License-Identifier: MPL-2.0
"""Opt-in operational counters and a storage-independent status view."""

from functools import wraps
import inspect
import json
from pathlib import Path
from typing import Annotated

import typer

from empirical_lawhood.infrastructure.progress import JsonProgressReporter, read_progress
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.runtime.progress import progress_reporting


PROGRESS_FILE_OPTION = typer.Option(
    "--progress-file",
    help="New advisory JSON status file outside scientific packages; phase counts, updated at most once per second.",
)


def _check_destination(path: Path, arguments: dict) -> None:
    selected = path.resolve()
    for name, value in arguments.items():
        if name == "progress_file":
            continue
        values = value if isinstance(value, (tuple, list)) else (value,)
        for item in values:
            if not isinstance(item, Path):
                continue
            other = item.resolve()
            if selected == other or (name in {"authoring_dir", "output_dir", "output_root", "attempt_dir", "metadata_directory"}
                                     and selected.is_relative_to(other)):
                raise ValueError("progress file must be separate from inputs, selected output roots and scientific or attempt packages")


def progress_command(operation: str):
    """Bind advisory reporting for one invocation without changing its result."""
    def decorate(function):
        signature = inspect.signature(function, eval_str=True)

        @wraps(function)
        def invoke(*args, **kwargs):
            arguments = signature.bind(*args, **kwargs)
            arguments.apply_defaults()
            selected = arguments.arguments.get("progress_file")
            if selected is None:
                return function(*args, **kwargs)
            try:
                _check_destination(selected, arguments.arguments)
                reporter = JsonProgressReporter(selected, operation)
            except (OSError, ValueError, TypeError) as error:
                raise typer.BadParameter(str(error), param_hint="--progress-file") from error
            with progress_reporting(reporter):
                try:
                    result = function(*args, **kwargs)
                except BaseException as error:
                    code = getattr(error, "exit_code", getattr(error, "code", None))
                    status = "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "FAILED"
                    reporter.finish("RETURNED" if code == 0 else status)
                    raise
                else:
                    reporter.finish("RETURNED")
                    return result

        return invoke
    return decorate


def register_progress_command(app: typer.Typer) -> None:
    @app.command("progress")
    def progress(
        path: Annotated[Path, typer.Option("--file", help="Explicit advisory progress JSON file.")],
        as_json: Annotated[bool, typer.Option("--json", help="Print the validated status as JSON.")] = False,
    ) -> None:
        """Read operational phase counts without loading a campaign or source."""
        try:
            record = read_progress(path)
        except (OSError, ValueError, TypeError, BoundedFileIOError) as error:
            typer.echo(f"Cannot read progress ({type(error).__name__}): {error}", err=True)
            raise typer.Exit(code=2) from error
        if as_json:
            typer.echo(json.dumps(record, allow_nan=False, sort_keys=True))
            return
        done, total, percent = record["done"], record["total"], record["percent"]
        count = "count unknown" if done is None else str(done)
        if total is not None:
            count += f"/{total}"
        fraction = "" if percent is None else f" ({percent:.1f}%)"
        typer.echo(f"{record['status']} | {record['phase']} | {count}{fraction} | failed={record['failed']}")
        typer.echo(f"Updated: {record['updated_at_utc']} | PID: {record['pid']}")
