# SPDX-License-Identifier: MPL-2.0
"""Unused pages may be reclaimed; live RSS and observation failures still stop."""

import pytest

from empirical_lawhood.api import matrix_programme_allocations as admission
from empirical_lawhood.infrastructure import process_memory


def test_metadata_reclaims_unused_pages_before_same_limit_check(monkeypatch):
    observations = iter((4096, 1024))
    reclaimed = []
    monkeypatch.setattr(admission, "_process_rss_bytes", lambda: next(observations))
    monkeypatch.setattr(process_memory, "release_unused_process_memory", lambda: reclaimed.append(True))
    admission._require_memory(2048)
    assert reclaimed == [True]


@pytest.mark.parametrize("remaining", (2049, 4096))
def test_metadata_still_refuses_live_resident_memory(monkeypatch, remaining):
    observations = iter((4096, remaining))
    reclaimed = []
    monkeypatch.setattr(admission, "_process_rss_bytes", lambda: next(observations))
    monkeypatch.setattr(process_memory, "release_unused_process_memory", lambda: reclaimed.append(True))
    with pytest.raises(ValueError, match="current-process memory ceiling"):
        admission._require_memory(2048)
    assert reclaimed == [True]


def test_metadata_does_not_reclaim_when_actual_rss_fits(monkeypatch):
    monkeypatch.setattr(admission, "_process_rss_bytes", lambda: 2048)
    monkeypatch.setattr(process_memory, "release_unused_process_memory", lambda: pytest.fail("unnecessary reclamation"))
    admission._require_memory(2048)


def test_metadata_missing_post_reclamation_observation_is_not_admission(monkeypatch):
    observations = iter((4096,))
    def observe():
        try:
            return next(observations)
        except StopIteration:
            raise ValueError("RSS observation unavailable") from None
    monkeypatch.setattr(admission, "_process_rss_bytes", observe)
    monkeypatch.setattr(process_memory, "release_unused_process_memory", lambda: None)
    with pytest.raises(ValueError, match="RSS observation unavailable"):
        admission._require_memory(2048)


def test_reclamation_without_allocator_support_keeps_live_data(monkeypatch):
    live = bytearray(b"original live bytes")
    collections = []
    monkeypatch.setattr(process_memory.gc, "collect", lambda: collections.append(True))
    monkeypatch.setattr(process_memory.ctypes, "CDLL", lambda _: object())
    process_memory.release_unused_process_memory()
    assert collections == [True]
    assert live == b"original live bytes"
