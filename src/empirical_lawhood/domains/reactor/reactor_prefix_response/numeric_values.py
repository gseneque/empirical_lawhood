"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from decimal import Decimal

def _decimal(value: object) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("native reactor emitted a nonfinite value")
    return result
