# SPDX-License-Identifier: MPL-2.0
"""Finite real-counter persistence controls; no native science or publication."""

from decimal import Decimal
from threading import Event

import pytest

from empirical_lawhood.infrastructure import execution as owner


def test_durable_milestones_bound_every_actual_sample_and_retain_exact_final(monkeypatch):
    def no_clock():
        raise AssertionError("durable work milestones must not read elapsed time")

    monkeypatch.setattr(owner.time, "monotonic", no_clock)
    persisted = []
    progress = owner._ProgressPersistence(persisted.append, milestone_sampling=True)
    try:
        # Wait after every submit: no favourable callback coalescing is assumed.
        for counter in range(1, 9217):
            progress.submit(Decimal(counter))
            progress._future.result(timeout=2)
        assert persisted == [Decimal(1 << power) for power in range(14)]
        progress.drain()
        progress.drain()
        assert persisted == [*(Decimal(1 << power) for power in range(14)), Decimal(9216)]
        assert len(persisted) == 15
    finally:
        progress.close()


def test_durable_milestones_coalesce_preserve_default_and_propagate_failure():
    started, release = Event(), Event()
    persisted = []

    def retain(counter):
        persisted.append(counter)
        if counter == 1:
            started.set()
            assert release.wait(timeout=2)

    progress = owner._ProgressPersistence(retain, milestone_sampling=True)
    try:
        progress.submit(Decimal(1))
        assert started.wait(timeout=2)
        for counter in (2, 3, 4, 5):
            progress.submit(Decimal(counter))
        release.set()
        progress._future.result(timeout=2)
        assert persisted == [Decimal(1), Decimal(4)]
        # Exceptional cleanup must not force the deferred actual counter5.
        progress.close()
        assert persisted == [Decimal(1), Decimal(4)]
    finally:
        release.set()
        progress.close()

    persisted = []
    progress = owner._ProgressPersistence(persisted.append)
    try:
        for counter in (1, 2, 3):
            progress.submit(Decimal(counter))
            progress._future.result(timeout=2)
        progress.drain()
        assert persisted == [Decimal(1), Decimal(2), Decimal(3)]
    finally:
        progress.close()

    failure = RuntimeError("durable progress failure")

    def fail(_counter):
        raise failure

    progress = owner._ProgressPersistence(fail, milestone_sampling=True)
    try:
        progress.submit(Decimal(1))
        with pytest.raises(RuntimeError, match="durable progress failure"):
            progress._future.result(timeout=2)
        for action in (progress.check, progress.drain, lambda: progress.submit(Decimal(2))):
            with pytest.raises(RuntimeError) as caught:
                action()
            assert caught.value is failure
    finally:
        progress.close()
