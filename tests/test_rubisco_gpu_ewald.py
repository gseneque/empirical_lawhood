# SPDX-License-Identifier: MPL-2.0
"""The observed enzyme allocation and complete reciprocal-grid coverage."""

from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_ewald as owner


def test_original_enzyme_shape_requires_bounded_reciprocal_workspace():
    atoms, points = 307182, 41*43*39
    original = 8*atoms*points
    assert original > 2*80*10**9
    block, per_point, budget = owner.reciprocal_block_length(points=points,
        mm_atoms=atoms, qm_atoms=152, free_bytes=70*2**30, allocation_bytes=70*2**30)
    assert 0 < block < points
    assert block*per_point <= budget <= 2*2**30
    assert 8*atoms*block < 300*2**20


def test_device_headroom_and_allocation_both_bound_complete_grid(monkeypatch):
    observed = iter((2**30, 512*2**20, 128*2**20))
    device = SimpleNamespace(memGetInfo=lambda: (next(observed), 80*2**30))
    monkeypatch.setitem(sys.modules, 'cupy', SimpleNamespace(cuda=SimpleNamespace(runtime=device)))
    rows = []
    cell = SimpleNamespace(_el_ewald_device_memory_bytes=2**30, _el_ewald_observe=rows.append)
    blocks = list(owner.reciprocal_blocks(cell, 151, 20000, 3, operation='gradient'))
    assert [index for a, b in blocks for index in range(a, b)] == list(range(151))
    assert blocks == [(0, 104), (104, 151)]
    assert rows[-1]['reciprocal_points'] == 151
    assert rows[0]['precision'] == 'float64'
    with pytest.raises(MemoryError, match='one reciprocal Ewald block'):
        owner.reciprocal_block_length(points=1, mm_atoms=307182, qm_atoms=152,
            free_bytes=2**20, allocation_bytes=70*2**30)


def test_derived_gpu_source_keeps_its_exact_upstream_and_local_bindings():
    from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_backend
    path = Path(owner.__file__)
    record = json.loads(files('empirical_lawhood.domains.rubisco.rubisco_response').joinpath('gpu-periodic-ewald-provenance.json').read_bytes())
    assert record['local_sha256'] == sha256(path.read_bytes()).hexdigest()
    assert {row['original_sha256'] for row in record['files']} == {
        gpu_periodic_backend.PERIODIC_SOURCE_SHA256, gpu_periodic_backend.MM_SOURCE_SHA256}
