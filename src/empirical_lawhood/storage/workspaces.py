# SPDX-License-Identifier: MPL-2.0
"""Bounded physical-location observation for explicit local workspace setup."""
from pathlib import Path
import json

from empirical_lawhood.execution.local.bounded_process import run_bounded_command, BoundedProcessError


def containing_mount(path: Path) -> Path:
    """Find the exact current containing mount without creating or trusting it.

    The normal guarded-root owner repeats volume identity and closing checks
    during use. This observation supplies only the profile's physical locator.
    """
    selected = Path(path).absolute()
    if '..' in selected.parts or any(part.is_symlink() for part in (selected, *selected.parents)):
        raise ValueError('workspace location refuses parent traversal and symbolic links')
    parent = selected
    while not parent.exists():
        parent = parent.parent
    completed = run_bounded_command(['findmnt', '--json', '--target', str(parent), '--output', 'TARGET'],
        timeout_seconds=5, maximum_stdout_bytes=64 * 1024, maximum_stderr_bytes=16 * 1024)
    if completed.returncode != 0:
        raise BoundedProcessError('cannot identify selected workspace volume')
    try:
        facts = json.loads(completed.stdout.decode('utf-8'))['filesystems']
        targets = {fact['target'] for fact in facts}
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('workspace volume observation is malformed') from error
    if len(targets) != 1:
        raise ValueError('workspace volume observation is ambiguous')
    mount = Path(targets.pop())
    if not mount.is_absolute() or not selected.is_relative_to(mount):
        raise ValueError('workspace volume does not contain its selected root')
    return mount
