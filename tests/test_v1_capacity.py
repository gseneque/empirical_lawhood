# SPDX-License-Identifier: MPL-2.0
"""Container placement must never overstate the resources a worker can use."""

from empirical_lawhood.execution.resources import capacity
import pytest


def test_nested_cgroup_and_affinity_use_tightest_constraints(monkeypatch):
    monkeypatch.setattr(capacity.os, "sched_getaffinity", lambda _pid: set(range(12)))
    monkeypatch.setattr(capacity.os, "sysconf", lambda name: 1 if name == "SC_PAGE_SIZE" else 10000)
    monkeypatch.setattr(capacity.resource, "getrlimit", lambda _key: (-1, -1))
    files = {
        "/proc/self/cgroup": "0::/work/child",
        "/proc/self/mountinfo": "1 2 0:4 / /sys/fs/cgroup rw - cgroup2 cgroup rw",
        "/sys/fs/cgroup/work/child/cpu.max": "350000 100000",
        "/sys/fs/cgroup/work/cpu.max": "200000 100000",
        "/sys/fs/cgroup/cpu.max": "max 100000",
        "/sys/fs/cgroup/work/child/memory.max": "8000",
        "/sys/fs/cgroup/work/child/memory.current": "1000",
        "/sys/fs/cgroup/work/memory.max": "6000",
        "/sys/fs/cgroup/work/memory.current": "2500",
    }
    observed = capacity.observe_capacity(read=lambda path: files.get(str(path)))
    assert observed.cpu_cores == 2
    assert observed.memory_bytes == 3500
    assert "cgroup_cpu_quota" in observed.constraints
    assert "cgroup_available_memory" in observed.constraints


def test_quota_without_full_cpu_keeps_one_worker_and_memory_pressure_is_visible(monkeypatch):
    monkeypatch.setattr(capacity.os, "sched_getaffinity", lambda _pid: {0, 1})
    monkeypatch.setattr(capacity.os, "sysconf", lambda name: 1 if name == "SC_PAGE_SIZE" else 10000)
    files = {"/sys/fs/cgroup/cpu.max": "50000 100000",
             "/sys/fs/cgroup/memory.max": "100", "/sys/fs/cgroup/memory.current": "101"}
    observed = capacity.observe_capacity(read=lambda path: files.get(str(path)))
    assert (observed.cpu_cores, observed.memory_bytes) == (1, 1)


def test_selection_obeys_observed_capacity_and_operator_maximum(monkeypatch):
    monkeypatch.setattr(capacity, "observe_capacity", lambda: capacity.CapacityObservation(8, 1000, ()))
    assert capacity.select_worker_count() == 8
    assert capacity.select_worker_count(maximum=4) == 4
    assert capacity.select_worker_count(2, maximum=4) == 2
    for requested, maximum in ((9, None), (5, 4), (True, None), (0, None), (None, False)):
        with pytest.raises(ValueError):
            capacity.select_worker_count(requested, maximum=maximum)


def test_shared_admission_and_experiment_selection_observe_same_capacity(monkeypatch):
    from empirical_lawhood.execution.experiment_preparation import select_experiment_workers
    from empirical_lawhood.execution.local.execution import LocalExecutionResourceAdmitter
    monkeypatch.setattr(capacity, "observe_capacity", lambda: capacity.CapacityObservation(3, 123456, ()))
    assert select_experiment_workers(None) == 3
    observed = LocalExecutionResourceAdmitter.detect_capacity()
    assert (observed.cpu_cores, observed.memory_bytes) == (3, 123456)


@pytest.mark.parametrize(("available_kib", "expected"), ((6, 6144), (20, 10000)))
def test_linux_available_memory_includes_reclaimable_cache_within_physical_limit(monkeypatch, available_kib, expected):
    values = {"SC_PAGE_SIZE": 1, "SC_PHYS_PAGES": 10000, "SC_AVPHYS_PAGES": 1000}
    monkeypatch.setattr(capacity.os, "sysconf", values.__getitem__)
    monkeypatch.setattr(capacity.resource, "getrlimit", lambda _key: (-1, -1))
    files = {"/proc/meminfo": f"MemFree: 1 kB\nMemAvailable: {available_kib} kB\n"}
    observed = capacity.observe_capacity(read=lambda path: files.get(str(path)))
    assert observed.memory_bytes == expected
    assert "linux_available_memory" in observed.constraints
    assert "SC_AVPHYS_PAGES" not in observed.constraints
