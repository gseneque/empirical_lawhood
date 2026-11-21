# SPDX-License-Identifier: MPL-2.0
"""Shared Arb precision ownership and lossless stored Decimal bounds."""

from contextlib import contextmanager
from decimal import Decimal
from threading import RLock

from flint import arb, ctx


_CONTEXT_LOCK = RLock()


@contextmanager
def arb_precision(bits: int):
    """Serialize the process-global context, including nested use and conversion.

    Every Arb calculation must retain this scope until its returned values no
    longer depend on Arb precision. The reentrant guard lets one family call
    another without losing its outer precision. workprec restores on failure.
    """
    if type(bits) is not int or bits < 2:
        raise ValueError("Arb precision requires at least two integer bits")
    with _CONTEXT_LOCK, ctx.workprec(bits):
        yield


def endpoint_decimal(value: arb, *, upper: bool) -> Decimal:
    """Return an outward endpoint exactly, without decimal or mpmath arithmetic.

    Arb lower()/upper() round in the indicated direction. Their finite point
    results are dyadics m*2**e. For e < 0, m*5**(-e)*10**e is the same number;
    the integer and tuple Decimal constructors preserve it at any context.
    """
    if not value.is_finite():
        raise ValueError("a finite Arb enclosure is required")
    endpoint = value.upper() if upper else value.lower()
    mantissa, exponent = (int(part) for part in endpoint.man_exp())
    if exponent >= 0:
        return Decimal(mantissa << exponent)
    coefficient = Decimal(mantissa * 5 ** (-exponent)).as_tuple()
    return Decimal((coefficient.sign, coefficient.digits, exponent))
