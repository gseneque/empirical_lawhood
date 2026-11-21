# SPDX-License-Identifier: MPL-2.0
"""Deterministic precision overlap across rank and battery calculations."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event, get_ident

import numpy as np
import pytest
from flint import ctx

from empirical_lawhood.methods import _arb, certified_rank
from empirical_lawhood.domains.battery.battery_refined_inquiry import preparation_science as preparation
from empirical_lawhood.domains.battery.battery_refined_inquiry import source_derived_preparation as derived
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition


@pytest.mark.parametrize("consumer", ("roots", "assessment", "preparation"))
def test_rank_and_battery_keep_their_precision_until_conversion(monkeypatch, consumer):
    from tests.test_battery_refined_inquiry import selected
    from empirical_lawhood.domains.battery.battery_refined_inquiry.contracts import identity

    source, _ = selected.__wrapped__()
    supplier = derived.supply_source_roots(identity(source), "Chen2020")
    if consumer == "preparation":
        from tests.test_battery_initial_preparation import _prepared_fixture
        trace, operands = _prepared_fixture(parameter="Chen2020")
    original = ctx.prec
    rank_entered, battery_attempted, release_rank = Event(), Event(), Event()
    rank_thread = []
    battery_bits, converted_bits = [], []
    lock = _arb._CONTEXT_LOCK

    class ObservedLock:
        def __enter__(self):
            if rank_thread and get_ident() != rank_thread[0]:
                battery_attempted.set()
            lock.acquire()

        def __exit__(self, *args):
            lock.release()

    original_enclosures = certified_rank._enclosures
    original_endpoint = certified_rank.endpoint_decimal
    original_ball = preparation._ball

    def enclosures(matrix):
        rank_thread.append(get_ident())
        rank_entered.set()
        assert release_rank.wait(10), "test controller did not release the rank calculation"
        assert ctx.prec == 640
        return original_enclosures(matrix)

    def endpoint(*args, **kwargs):
        converted_bits.append(ctx.prec)
        return original_endpoint(*args, **kwargs)

    def ball(value):
        battery_bits.append(ctx.prec)
        return original_ball(value)

    monkeypatch.setattr(_arb, "_CONTEXT_LOCK", ObservedLock())
    monkeypatch.setattr(certified_rank, "_enclosures", enclosures)
    monkeypatch.setattr(certified_rank, "endpoint_decimal", endpoint)
    monkeypatch.setattr(preparation, "_ball", ball)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rank = pool.submit(certified_rank.certify_rank, np.eye(2), precision_bits=640)
        try:
            assert rank_entered.wait(10)
            if consumer == "roots":
                battery = pool.submit(preparation.source_root_enclosures, "Chen2020")
            elif consumer == "assessment":
                battery = pool.submit(derived.assess_source_roots, supplier)
            else:
                battery = pool.submit(preparation.assess_initial_preparation, trace, **operands)
            assert battery_attempted.wait(10), "battery did not use the shared precision owner"
            # The attempted lock acquisition is observed before releasing rank.
            # Neither worker waits for a peer while holding a required lock.
            assert not battery_bits
            assert ctx.prec == 640
        finally:
            release_rank.set()
        certificate, result = rank.result(timeout=10), battery.result(timeout=10)
    assert (certificate.lower, certificate.upper, certificate.precision_bits) == (2, 2, 640)
    assert converted_bits == [640, 640, 640]
    assert battery_bits and set(battery_bits) == {256}
    assert len(result) == 2 if consumer == "roots" else result.disposition is AssessmentDisposition.SATISFIED
    assert ctx.prec == original


def test_nested_precision_restores_after_success_and_exceptions(monkeypatch):
    original = ctx.prec
    with _arb.arb_precision(97):
        assert ctx.prec == 97
        with _arb.arb_precision(511):
            assert ctx.prec == 511
        assert ctx.prec == 97
        with pytest.raises(RuntimeError, match="interrupted"):
            with _arb.arb_precision(1024):
                raise RuntimeError("interrupted")
        assert ctx.prec == 97
        assert certified_rank.certify_rank(np.eye(2)).precision_bits == 384
        assert ctx.prec == 97
        with monkeypatch.context() as patch:
            def failed_enclosures(matrix):
                assert ctx.prec == 384
                raise ArithmeticError("rank failure")
            patch.setattr(certified_rank, "_enclosures", failed_enclosures)
            with pytest.raises(ArithmeticError, match="rank failure"):
                certified_rank.certify_rank(np.eye(2))
        assert ctx.prec == 97
        with monkeypatch.context() as patch:
            def failed_ocp(value):
                assert ctx.prec == 256
                raise ArithmeticError("battery failure")
            patch.setattr(preparation, "_positive_ocp", failed_ocp)
            with pytest.raises(ArithmeticError, match="battery failure"):
                preparation.source_root_enclosures("Chen2020")
        assert ctx.prec == 97
    assert ctx.prec == original


@pytest.mark.parametrize("bits", (True, 1, 0, -1, 2.5, "256"))
def test_precision_rejects_invalid_requests_without_changing_context(bits):
    original = ctx.prec
    with pytest.raises(ValueError, match="integer bits"):
        with _arb.arb_precision(bits):
            pytest.fail("invalid precision entered")
    assert ctx.prec == original
