# SPDX-License-Identifier: MPL-2.0
"""One CLI presentation owner and the storage-independent progress view."""

from contextlib import contextmanager
import sys
import json
from pathlib import Path
from typing import Annotated

from typer.models import TyperPath
import typer

from empirical_lawhood.storage.progress import OperationalProgressReporter, format_progress, read_progress
from empirical_lawhood.storage.bounded_io import BoundedFileIOError


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
            if selected == other or ((other.is_dir() or name in {"authoring_dir", "output_dir", "output_root", "attempt_dir", "metadata_directory", "root", "payload", "package"})
                                     and selected.is_relative_to(other)):
                raise ValueError("progress file must be separate from inputs, selected output roots and scientific or attempt packages")


def _invocation(group, context):
    """Inspect declared path options before telemetry claims its output path."""
    from empirical_lawhood.cli.attempts import _option_values
    current = group
    remaining = [*context._protected_args, *context.args]
    names, arguments = [], dict(context.params)
    for parameter in group.params:
        value = arguments.get(parameter.name)
        if isinstance(parameter.type, TyperPath) and value is not None:
            arguments[parameter.name] = [Path(v) for v in value] if isinstance(value, (list, tuple)) else Path(value)
    while True:
        parameters = {option: parameter for parameter in current.params for option in getattr(parameter, "opts", ())}
        for index, token in enumerate(remaining):
            spelling, equal, inline = token.partition("=")
            parameter = parameters.get(spelling)
            if parameter is None or not isinstance(parameter.type, TyperPath):
                continue
            if not equal and index + 1 >= len(remaining):
                continue
            value = inline if equal else remaining[index + 1]
            key = parameter.name
            existing = arguments.get(key)
            arguments[key] = [*(existing if isinstance(existing, list) else []), Path(value)]
        _, remaining = _option_values(current, remaining, leaf=not bool(getattr(current, "commands", None)))
        if not getattr(current, "commands", None) or not remaining:
            break
        name = remaining.pop(0)
        child = current.commands.get(name)
        if child is None:
            break
        names.append(name)
        current = child
    return " ".join(names) or "command", arguments


@contextmanager
def command_progress(group, context):
    """Default stderr progress for every command; optional one atomic UI file."""
    operation, arguments = _invocation(group, context)
    if operation == "progress":
        yield
        return
    value = context.params.get("progress_file")
    selected = None if value is None else Path(value)
    enabled = context.params.get("progress", True)
    if not enabled and selected is None:
        yield
        return
    try:
        if selected is not None:
            _check_destination(selected, arguments)
        reporter = OperationalProgressReporter(selected, operation,
            stream=sys.stderr if enabled else None)
    except (OSError, ValueError, TypeError) as error:
        raise typer.BadParameter(str(error), param_hint="--progress-file") from error
    with reporter:
        yield


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
        typer.echo(format_progress(record))
        typer.echo(f"Updated: {record['updated_at_utc']} | PID: {record['pid']} | sequence={record['sequence']}")
