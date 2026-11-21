# SPDX-License-Identifier: MPL-2.0
"""BLAS-independent reductions for source-bound optimizer checkpoint scalars.

Each product is rounded to a Python binary64 float before ``math.fsum``.
This defines the new algorithm's reduction, instead of guessing a tolerance
for a different producer's BLAS tree. It is not an exact real-arithmetic dot.
"""

import math


REDUCTION_CONTRACT = "PYTHON_BINARY64_PRODUCTS_FSUM_V1"


def dot(left, right):
    """Sum finite binary64 products without a threaded/vendor BLAS call."""
    def products():
        for a, b in zip(left, right, strict=True):
            a, b = float(a), float(b)
            value = a * b
            if not all(math.isfinite(x) for x in (a, b, value)):
                raise ValueError("checkpoint scalar reduction requires finite binary64 products")
            yield value
    result = math.fsum(products())
    if not math.isfinite(result):
        raise ValueError("checkpoint scalar reduction overflowed")
    return result


def norm(values):
    """Euclidean norm using the same declared binary64 product reduction."""
    # Callers provide arrays/tuples, not one-shot iterators.
    return math.sqrt(dot(values, values))
