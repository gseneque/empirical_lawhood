# SPDX-License-Identifier: MPL-2.0
"""Bind a selected-source claim to the Python modules that are executing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from empirical_lawhood.infrastructure.selected_candidate import InstalledCandidate

from empirical_lawhood.infrastructure.bounded_process import (
    BoundedProcessError,
    run_bounded_command,
)


class ExecutingSourceMismatch(PermissionError):
    """The executing package is not the tracked package in the inspected checkout."""


def require_executing_target_source(repo_root: Path) -> Path:
    """Refuse a source claim from a wheel or a different source checkout.

    This checks origin and tracked membership, including namespace packages.
    Committed byte/tree identity and the selected admission policy belong to
    the caller's source-closure inspector.
    """

    try:
        root = repo_root.resolve(strict=True)
    except OSError as error:
        raise ExecutingSourceMismatch("inspected project root is unavailable") from error
    package_root = root / "src" / "empirical_lawhood"
    initializer = package_root / "__init__.py"
    package = sys.modules.get("empirical_lawhood")
    package_file = getattr(package, "__file__", None)
    if package_file is None or Path(package_file).resolve() != initializer.resolve():
        raise ExecutingSourceMismatch(
            "executing empirical_lawhood package is not the inspected target source tree"
        )
    try:
        found = run_bounded_command(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=root,
            timeout_seconds=5,
            maximum_stdout_bytes=4096,
            maximum_stderr_bytes=4096,
        )
        if found.returncode or Path(found.stdout.decode().strip()).resolve() != root:
            raise ExecutingSourceMismatch("inspected project root is not a Git checkout root")
        listed = run_bounded_command(
            ("git", "ls-files", "-z", "--", "src/empirical_lawhood"),
            cwd=root,
            timeout_seconds=5,
            maximum_stdout_bytes=1024 * 1024,
            maximum_stderr_bytes=4096,
        )
        if listed.returncode:
            raise ExecutingSourceMismatch("tracked target source cannot be enumerated")
        tracked_paths = set(listed.stdout.decode("utf-8").split("\0"))
        for name, module in tuple(sys.modules.items()):
            if name != "empirical_lawhood" and not name.startswith("empirical_lawhood."):
                continue
            origin = getattr(module, "__file__", None)
            if origin is None:
                locations = getattr(getattr(module, "__spec__", None), "submodule_search_locations", None)
                expected = package_root.joinpath(*name.split(".")[1:])
                if (locations is None or isinstance(locations, (str, bytes))
                        or tuple(Path(value).resolve(strict=True) for value in locations) != (expected,)
                        or (expected / "__init__.py").exists()
                        or not any(path.startswith(expected.relative_to(root).as_posix() + "/") for path in tracked_paths)):
                    raise ExecutingSourceMismatch(
                        f"loaded namespace {name} is not the tracked target source directory"
                    )
                continue
            if type(origin) is not str or not origin.endswith(".py"):
                raise ExecutingSourceMismatch(
                    f"loaded module {name} has no supported tracked Python source origin"
                )
            path = Path(origin).resolve()
            if not path.is_relative_to(package_root):
                raise ExecutingSourceMismatch(
                    f"loaded module {name} is outside the inspected target source tree"
                )
            relative = path.relative_to(root).as_posix()
            if relative not in tracked_paths:
                raise ExecutingSourceMismatch(f"loaded module {name} is not tracked")
    except ExecutingSourceMismatch:
        raise
    except (BoundedProcessError, OSError, UnicodeDecodeError, ValueError, TypeError) as error:
        raise ExecutingSourceMismatch("executing source origin cannot be verified") from error
    return package_root


__all__ = ["ExecutingSourceMismatch", "require_executing_target_source",
    "require_selected_implementation", "observe_selected_implementation"]


def observe_selected_implementation(
    source_root: Path,
) -> tuple[Path, InstalledCandidate | None]:
    """Admit current source once and retain its installed candidate observation."""
    import empirical_lawhood

    root = Path(source_root).resolve(strict=True)
    package = Path(empirical_lawhood.__file__).resolve().parent
    if package == root / "src/empirical_lawhood":
        return require_executing_target_source(root), None
    from empirical_lawhood.infrastructure.selected_candidate import installed_candidate

    try:
        candidate = installed_candidate(source_root=root)
        return candidate.package_root, candidate
    except (OSError, PermissionError, RuntimeError, ValueError) as error:
        raise ExecutingSourceMismatch("executing installation differs from its selected candidate source") from error


def require_selected_implementation(source_root: Path) -> Path:
    """Retain the Path-only admission interface and all current origin checks."""
    package_root, _ = observe_selected_implementation(source_root)
    return package_root


def _wheel_member_sha256(stream, *, size_bytes: int) -> str:
    """Hash one exact archive member with bounded deliveries and complete EOF."""
    from hashlib import sha256

    checksum = sha256()
    remaining = size_bytes
    while remaining:
        raw = stream.read(min(remaining, 1024 * 1024))
        if not raw:
            raise RuntimeError("wheel member ended before its declared size")
        checksum.update(raw)
        remaining -= len(raw)
    if stream.read(1):
        raise RuntimeError("wheel member exceeds its declared size")
    return checksum.hexdigest()


def verify_wheel_package_members(wheel: Path, *, expected: tuple) -> list[dict[str, object]]:
    """Compare a unique regular wheel package to exact committed member metadata.

    The caller obtains the complete ``TrackedSourceMember`` tuple from its
    owning source census. This check supplies artifact equality only; loaded
    module origin and current scientific authority remain separate admissions.
    No source or archive payload bank is retained in memory.
    """
    import os
    import stat
    import zipfile

    from empirical_lawhood.infrastructure.bounded_io import _identity, _open_regular, _stable_descriptor
    from empirical_lawhood.infrastructure.source_closure import TrackedSourceMember, _MAX_ARCHIVE_BYTES
    from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256

    prefix = "src/empirical_lawhood/"
    if type(expected) is not tuple or not expected or any(type(row) is not TrackedSourceMember for row in expected):
        raise TypeError("wheel comparison requires its exact committed package members")
    selected = {}
    for row in expected:
        validate_relative_locator(row.relative_path)
        validate_sha256(row.sha256, field_name="committed package member SHA256")
        if (not row.relative_path.startswith(prefix) or row.relative_path == prefix
                or row.mode not in ("100644", "100755") or type(row.size_bytes) is not int
                or not 0 <= row.size_bytes <= _MAX_ARCHIVE_BYTES
                or row.relative_path.removeprefix("src/") in selected):
            raise ValueError("wheel comparison changes its unique regular committed package census")
        selected[row.relative_path.removeprefix("src/")] = (row.size_bytes, row.sha256)
    if sum(row[0] for row in selected.values()) > _MAX_ARCHIVE_BYTES:
        raise ValueError("wheel package exceeds the existing committed archive byte bound")
    path = Path(wheel).absolute()
    if path.resolve(strict=True) != path:
        raise RuntimeError("wheel comparison refuses symbolic or noncanonical artifact paths")
    descriptor, before = _open_regular(path, maximum_bytes=_MAX_ARCHIVE_BYTES)
    with _stable_descriptor(descriptor, before, operation="wheel package comparison"):
        with os.fdopen(descriptor, "rb", closefd=False) as stream, zipfile.ZipFile(stream) as archive:
            members, seen, aliases = {}, set(), set()
            total = 0
            for member in archive.infolist():
                name = member.filename
                if member.orig_filename != name:
                    raise RuntimeError("wheel contains a noncanonical original member name")
                canonical = name.rstrip("/")
                try:
                    validate_relative_locator(canonical)
                except ValueError as error:
                    raise RuntimeError("wheel contains duplicate or escaping members") from error
                if (name in seen or canonical in aliases
                        or name not in (canonical, canonical + "/")):
                    raise RuntimeError("wheel contains duplicate or escaping members")
                seen.add(name)
                aliases.add(canonical)
                total += member.file_size
                if member.file_size < 0 or total > _MAX_ARCHIVE_BYTES:
                    raise RuntimeError("wheel members exceed the existing committed archive byte bound")
                kind = stat.S_IFMT(member.external_attr >> 16)
                if member.is_dir():
                    if kind not in (0, stat.S_IFDIR) or member.file_size:
                        raise RuntimeError("wheel contains a nonregular directory member")
                    continue
                if kind not in (0, stat.S_IFREG):
                    raise RuntimeError("wheel contains a nonregular file member")
                if name.startswith("empirical_lawhood/"):
                    members[name] = member
            added = sorted(members.keys() - selected.keys())
            missing = sorted(selected.keys() - members.keys())
            if added or missing:
                raise RuntimeError(f"wheel/source mismatch: added={added}, missing={missing}, changed=[]")
            changed = []
            for name, member in sorted(members.items()):
                size, checksum = selected[name]
                if member.file_size != size:
                    changed.append(name)
                    continue
                with archive.open(member) as body:
                    observed = _wheel_member_sha256(body, size_bytes=size)
                if observed != checksum:
                    changed.append(name)
            if changed:
                raise RuntimeError(f"wheel/source mismatch: added=[], missing=[], changed={changed}")
            if path.resolve(strict=True) != path or _identity(path.lstat()) != _identity(before):
                raise RuntimeError("wheel artifact changed its current path during comparison")
    return [{"path": name, "size_bytes": size, "sha256": checksum}
            for name, (size, checksum) in sorted(selected.items())]
