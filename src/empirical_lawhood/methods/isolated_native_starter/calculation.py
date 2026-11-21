# SPDX-License-Identifier: MPL-2.0
"""Sum squares over the finite inclusive integer sequence 0..n.

The native starter fixes n to 0..1024. Both implementations preserve exact
integer arithmetic over that declared range; neither opens files or launches work.
"""


def _validate(last_integer):
    if type(last_integer) is not int or not 0 <= last_integer <= 1024:
        raise ValueError("sum of squares requires an integer in the closed range 0..1024")


def sum_of_squares(last_integer):
    """Vector implementation with exact int64 arithmetic on the declared range."""
    import numpy as np
    _validate(last_integer)
    values = np.arange(last_integer + 1, dtype=np.int64)
    return int(np.dot(values, values))


def independent_sum(last_integer):
    """Closed integer formula, independent of the vector implementation."""
    _validate(last_integer)
    return last_integer * (last_integer + 1) * (2 * last_integer + 1) // 6
