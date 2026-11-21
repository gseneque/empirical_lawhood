# SPDX-License-Identifier: MPL-2.0
"""Actual kernel-limit controls; no scientific or native-effect evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


_MIB = 1024**2
_GIB = 1024**3
_PROBE = """
import json, resource, sys
from empirical_lawhood.execution.local.execution import _apply_resource_limits
from empirical_lawhood.science.identity.authority import ResourceBudget

kind, ceiling, inherited, deadline_free = json.loads(sys.argv[1])
identifier = getattr(resource, kind)
resource.setrlimit(identifier, tuple(inherited))
budget = ResourceBudget(
    cpu_cores=1,
    memory_bytes=ceiling if kind == 'RLIMIT_AS' else None,
    gpu_devices=0,
    wall_time_seconds=ceiling if kind == 'RLIMIT_CPU' else None,
    source_scan_bytes=None,
    output_bytes=ceiling if kind == 'RLIMIT_FSIZE' else None,
)
_apply_resource_limits(budget, deadline_free=deadline_free)
print(json.dumps(resource.getrlimit(identifier)))
"""


def _limits(kind, ceiling, inherited, *, deadline_free=False):
    result = subprocess.run(
        [sys.executable, '-B', '-c', _PROBE,
         json.dumps((kind, ceiling, inherited, deadline_free))],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return tuple(json.loads(result.stdout))


@pytest.mark.parametrize(('kind', 'ceiling', 'inherited', 'expected'), (
    ('RLIMIT_CPU', 120, (90, 90), (90, 90)),
    ('RLIMIT_AS', 4 * _GIB, (2 * _GIB, 2 * _GIB), (2 * _GIB, 2 * _GIB)),
    ('RLIMIT_FSIZE', 1536 * _MIB, (64 * _MIB, 64 * _MIB), (64 * _MIB, 64 * _MIB)),
    ('RLIMIT_CPU', 120, (60, 240), (60, 120)),
    ('RLIMIT_AS', 4 * _GIB, (2 * _GIB, 8 * _GIB), (2 * _GIB, 4 * _GIB)),
    ('RLIMIT_FSIZE', 1536 * _MIB, (64 * _MIB, 2 * _GIB), (64 * _MIB, 1536 * _MIB)),
    ('RLIMIT_CPU', 60, (-1, -1), (60, 60)),
    ('RLIMIT_AS', 2 * _GIB, (-1, -1), (2 * _GIB, 2 * _GIB)),
    ('RLIMIT_FSIZE', 64 * _MIB, (-1, -1), (64 * _MIB, 64 * _MIB)),
))
def test_task_caps_preserve_stricter_inherited_kernel_limits(kind, ceiling, inherited, expected):
    assert _limits(kind, ceiling, inherited) == expected


def test_deadline_free_worker_keeps_its_existing_cpu_limit():
    assert _limits('RLIMIT_CPU', 30, (90, 90), deadline_free=True) == (90, 90)
