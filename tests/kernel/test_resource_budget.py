"""Finite authority and explicitly unlimited local resource coordinates."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


FINITE = ResourceBudget(1, 100, 0, 3, 10, 20)
UNLIMITED = ResourceBudget(1, None, 0, None, None, None)


def test_existing_finite_budget_keeps_exact_canonical_bytes() -> None:
    expected = (
        b'{"schema":"empirical-lawhood/kernel/resource-budget","value":'
        b'{"cpu_cores":1,"gpu_devices":0,"memory_bytes":100,"output_bytes":20,'
        b'"source_scan_bytes":10,"wall_time_seconds":3},"version":"1.0.0"}\n'
    )
    assert FINITE.canonical_bytes() == expected
    assert decode_canonical_bytes(expected, ResourceBudget, maximum_bytes=len(expected)) == FINITE


@pytest.mark.parametrize("coordinate", (
    "memory_bytes", "wall_time_seconds", "source_scan_bytes", "output_bytes",
))
def test_finite_authority_cannot_contain_unlimited_request(coordinate: str) -> None:
    request = replace(FINITE, **{coordinate: None})
    assert not FINITE.contains(request)
    assert request.contains(FINITE)
    assert request.contains(request)
    assert UNLIMITED.contains(request)


def test_unlimited_budget_roundtrips_as_null_without_magic_ceiling() -> None:
    raw = UNLIMITED.canonical_bytes()
    assert raw.count(b"null") == 4
    assert decode_canonical_bytes(raw, ResourceBudget, maximum_bytes=len(raw)) == UNLIMITED
    assert UNLIMITED.contains(ResourceBudget(1, 10**30, 0, 10**30, 10**30, 10**30))
    assert not UNLIMITED.contains(replace(UNLIMITED, cpu_cores=2))


def test_aggregation_preserves_unlimited_and_finite_coordinates() -> None:
    assert ResourceBudget.aggregate((FINITE, FINITE)) == ResourceBudget(1, 100, 0, 6, 20, 40)
    assert ResourceBudget.aggregate((FINITE, UNLIMITED)) == UNLIMITED
    partial = replace(FINITE, memory_bytes=None, source_scan_bytes=None)
    assert ResourceBudget.aggregate((FINITE, partial)) == ResourceBudget(1, None, 0, 6, None, 40)
    with pytest.raises(ValueError, match="at least one"):
        ResourceBudget.aggregate(())


@pytest.mark.parametrize("coordinate,value", (
    ("memory_bytes", 0), ("wall_time_seconds", 0),
    ("source_scan_bytes", -1), ("output_bytes", -1),
))
def test_negative_or_zero_finite_limits_still_refuse(coordinate: str, value: int) -> None:
    with pytest.raises(ValueError):
        replace(UNLIMITED, **{coordinate: value})
