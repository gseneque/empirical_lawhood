# SPDX-License-Identifier: MPL-2.0
"""Observe usable local capacity without changing a scientific task's budget."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import resource


@dataclass(frozen=True, slots=True)
class CapacityObservation:
    cpu_cores: int
    memory_bytes: int
    constraints: tuple[str, ...]


def _read(path: Path) -> str | None:
    try:
        with path.open(encoding="ascii") as stream:
            value = stream.read(65537)
        return value.strip() if len(value) <= 65536 else None
    except (OSError, UnicodeError):
        return None


def _positive(value: str | None) -> int | None:
    try:
        parsed = int(value) if value is not None else 0
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _cgroup_directories(read) -> tuple[Path, ...]:
    """Locate the current v2 hierarchy, including finite ancestor constraints."""
    membership = read(Path("/proc/self/cgroup")) or ""
    mounts = read(Path("/proc/self/mountinfo")) or ""
    selected = next((line[3:] for line in membership.splitlines() if line.startswith("0::")), None)
    if selected is not None:
        for line in mounts.splitlines():
            before, separator, after = line.partition(" - ")
            fields = before.split()
            if not separator or not after.startswith("cgroup2 ") or len(fields) < 5:
                continue
            # Kernel mountinfo escapes whitespace; these are paths, never shell text.
            decode = lambda value: value.replace("\\040", " ").replace("\\011", "\t").replace("\\134", "\\")
            root, mount = Path(decode(fields[3])), Path(decode(fields[4]))
            try:
                relative = Path(selected).relative_to(root)
            except ValueError:
                continue
            if ".." in relative.parts:
                continue
            current = mount / relative
            return (current, *(parent for parent in current.parents if parent == mount or mount in parent.parents))
    return (Path("/sys/fs/cgroup"),)


def observe_capacity(*, read=None) -> CapacityObservation:
    """Respect affinity, finite cgroup quotas, available RAM and address limits.

    Fractional CPU quotas cannot support an additional whole CPU reservation.
    A single worker is the minimum executable placement; the observation never
    modifies precision, random streams, method thread counts or task budgets.
    """
    read = _read if read is None else read
    constraints: list[str] = []
    try:
        cpus = len(os.sched_getaffinity(0))
        constraints.append("process_affinity")
    except (AttributeError, OSError):
        cpus = os.cpu_count() or 1
        constraints.append("logical_cpu_count")
    memory: list[int] = []
    try:
        value = int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
        if value > 0:
            memory.append(value)
            constraints.append("SC_PHYS_PAGES")
    except (OSError, ValueError, AttributeError):
        pass
    # Linux's free-page count excludes reclaimable page cache. MemAvailable is
    # the kernel's estimate of RAM usable without swapping and is the relevant
    # scheduling bound, particularly after authenticating retained artifacts.
    available = None
    for line in (read(Path("/proc/meminfo")) or "").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] == "MemAvailable:" and fields[2] == "kB":
            amount = _positive(fields[1])
            available = amount * 1024 if amount is not None else None
            break
    if available is not None:
        memory.append(available)
        constraints.append("linux_available_memory")
    else:
        try:
            value = int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_AVPHYS_PAGES"))
            if value > 0:
                memory.append(value)
                constraints.append("SC_AVPHYS_PAGES")
        except (OSError, ValueError, AttributeError):
            pass
    for directory in _cgroup_directories(read):
        quota = read(directory / "cpu.max")
        if quota:
            values = quota.split()
            if len(values) == 2:
                amount, period = _positive(values[0]), _positive(values[1])
                if amount is not None and period is not None:
                    cpus = min(cpus, max(1, amount // period))
                    constraints.append("cgroup_cpu_quota")
        limit = _positive(read(directory / "memory.max"))
        if limit is not None:
            current = _positive(read(directory / "memory.current")) or 0
            memory.append(max(1, limit - current))
            constraints.append("cgroup_available_memory")
    # v1 container layouts remain in use. The default mounted controller paths
    # are independent constraints; absent files confer no additional capacity.
    quota = _positive(read(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")))
    period = _positive(read(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us")))
    if quota is not None and period is not None:
        cpus = min(cpus, max(1, quota // period))
        constraints.append("cgroup_v1_cpu_quota")
    limit = _positive(read(Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")))
    if limit is not None:
        current = _positive(read(Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"))) or 0
        memory.append(max(1, limit - current))
        constraints.append("cgroup_v1_available_memory")
    try:
        soft, _ = resource.getrlimit(resource.RLIMIT_AS)
        if soft not in (-1, resource.RLIM_INFINITY) and soft > 0:
            memory.append(soft)
            constraints.append("address_space_limit")
    except (AttributeError, OSError, ValueError):
        pass
    return CapacityObservation(max(1, cpus), min(memory) if memory else 1,
                               tuple(dict.fromkeys(constraints)))


class WorkerSelectionExceedsProfile(ValueError):
    """An explicit worker count exceeds the selected operator profile."""


def select_worker_count(requested: int | None = None, *, maximum: int | None = None) -> int:
    """Select operational concurrency within the observed and operator limits."""
    for name, value in (("workers", requested), ("profile maximum", maximum)):
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(name + " requires a positive integer")
    observed = observe_capacity().cpu_cores
    available = observed if maximum is None else min(observed, maximum)
    if requested is None:
        return available
    if requested > available:
        error = WorkerSelectionExceedsProfile if maximum is not None and requested > maximum else ValueError
        raise error(f"requested workers {requested} exceed usable CPU capacity {available}")
    return requested
