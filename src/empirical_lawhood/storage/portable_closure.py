# SPDX-License-Identifier: MPL-2.0
"""Selected closure bounds over the existing regular-file custody primitives."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import os
from pathlib import Path
import stat

from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits, RecursiveClosureMember

from empirical_lawhood.storage.bounded_io import bounded_file_sha256, copy_bounded_file


@dataclass
class ClosureReadBudget:
    limits: RecursiveClosureLimits
    scanned_entries: int = 0
    hashed_bytes: int = 0
    authentications: int = 0

    def scan(self):
        self.scanned_entries += 1
        if self.limits.maximum_scanned_entries is not None and self.scanned_entries > self.limits.maximum_scanned_entries:
            raise ValueError("portable closure exceeds its selected entry-scan work bound")

    def hash_bytes(self, count):
        self.hashed_bytes += count
        if self.limits.maximum_hashed_bytes is not None and self.hashed_bytes > self.limits.maximum_hashed_bytes:
            raise ValueError("portable closure exceeds its selected hash work bound")

    def authenticate(self, parent_depth):
        self.authentications += 1
        if (self.limits.maximum_parent_depth is not None and parent_depth > self.limits.maximum_parent_depth
                or self.limits.maximum_authentications is not None and self.authentications > self.limits.maximum_authentications):
            raise ValueError("portable contribution exceeds its selected depth or authentication bound")


_BUDGET = ContextVar("selected_recursive_closure_budget", default=None)


@contextmanager
def recursive_closure_limits(limits):
    """Nested verification shares its original budget; it cannot reset or widen it."""
    if type(limits) is not RecursiveClosureLimits:
        raise TypeError("portable custody requires explicit typed closure bounds")
    limits.__post_init__()
    current = _BUDGET.get()
    if current is not None:
        if current.limits != limits:
            raise ValueError("nested portable verification changes its selected closure bounds")
        yield current
        return
    budget = ClosureReadBudget(limits)
    token = _BUDGET.set(budget)
    try:
        yield budget
    finally:
        _BUDGET.reset(token)


def current_closure_budget():
    return _BUDGET.get()


def require_closure_members(members, limits):
    if type(members) is not tuple or not members or limits.maximum_members is not None and len(members) > limits.maximum_members:
        raise ValueError("portable closure has an invalid or excessive complete member census")
    paths = tuple(v.relative_path for v in members)
    if paths != tuple(sorted(set(paths))):
        raise ValueError("portable closure repeats or reorders member paths")
    total = 0
    for member in members:
        if type(member) is not RecursiveClosureMember:
            raise TypeError("portable closure requires exact typed members")
        member.__post_init__()
        if (limits.maximum_member_bytes is not None and member.size_bytes > limits.maximum_member_bytes
                or limits.maximum_path_depth is not None and len(Path(member.relative_path).parts) > limits.maximum_path_depth):
            raise ValueError("portable member exceeds its selected size or path-depth bound")
        total += member.size_bytes
        if limits.maximum_total_bytes is not None and total > limits.maximum_total_bytes:
            raise ValueError("portable closure exceeds its selected aggregate byte bound")
    return total


def bounded_custody_members(root, prefixes, *, limits):
    """Walk without an unbounded rglob/sort, retaining every scientific member."""
    root = Path(root)
    budget = current_closure_budget()
    if budget is None:
        with recursive_closure_limits(limits):
            return bounded_custody_members(root, prefixes, limits=limits)
    if budget.limits != limits:
        raise ValueError("closure census changes the active limits")
    members, total = {}, 0
    for prefix in prefixes:
        if prefix:
            validate_relative_locator(prefix)
        base = root / prefix
        if not base.is_dir() or any(p.is_symlink() for p in (base, *base.parents)):
            raise ValueError("portable closure requires a real selected custody directory")
        pending = [base]
        while pending:
            directory = pending.pop()
            if limits.maximum_path_depth is not None and len(directory.relative_to(root).parts) > limits.maximum_path_depth:
                raise ValueError("portable closure exceeds its selected path-depth bound")
            with os.scandir(directory) as entries:
                for entry in entries:
                    budget.scan()
                    path = Path(entry.path)
                    relative = path.relative_to(root).as_posix()
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode):
                        raise ValueError("portable custody cannot include symbolic links")
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(path)
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        raise ValueError("portable custody requires regular file members")
                    if path.name.endswith(".lock"):
                        continue
                    if (limits.maximum_path_depth is not None and len(path.relative_to(root).parts) > limits.maximum_path_depth
                            or info.st_size <= 0 or limits.maximum_member_bytes is not None and info.st_size > limits.maximum_member_bytes):
                        raise ValueError("portable custody member exceeds its size or path-depth bound")
                    if relative not in members:
                        if limits.maximum_members is not None and len(members) >= limits.maximum_members:
                            raise ValueError("portable custody exceeds its selected member bound")
                        total += info.st_size
                        if limits.maximum_total_bytes is not None and total > limits.maximum_total_bytes:
                            raise ValueError("portable custody exceeds its selected aggregate byte bound")
                    budget.hash_bytes(info.st_size)
                    size, digest = bounded_file_sha256(path, maximum_bytes=info.st_size)
                    if size != info.st_size:
                        raise ValueError("portable custody member changed during enumeration")
                    member = RecursiveClosureMember(relative, size, digest)
                    if members.setdefault(relative, member) != member:
                        raise ValueError("shared custody member changed between parent closures")
    result = tuple(members[name] for name in sorted(members))
    require_closure_members(result, limits)
    return result


def copy_closure_members(*, members, source_guard, destination_guard, destination_prefix, source_prefix=""):
    """The original contribution-copy loop, also used to assemble new transfers.

    Durable imports and interrupted-copy recovery use artifact_replication.
    """
    validate_relative_locator(destination_prefix)
    if source_prefix:
        validate_relative_locator(source_prefix)
    copied_count = 0
    for member in members:
        source_name = source_prefix + "/" + member.relative_path if source_prefix else member.relative_path
        source = source_guard.resolve(source_name, for_write=False)
        target = destination_guard.resolve(destination_prefix + "/" + member.relative_path, for_write=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        copied = copy_bounded_file(source, target, maximum_bytes=member.size_bytes)
        if copied != (member.size_bytes, member.sha256):
            raise ValueError("source custody changed while copying the portable closure")
        copied_count += 1
    source_guard.verify(for_write=False)
    destination_guard.verify(for_write=True)
    return copied_count
