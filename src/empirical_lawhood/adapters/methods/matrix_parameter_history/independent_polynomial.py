# SPDX-License-Identifier: MPL-2.0
"""Compiled ordering for the literal independent q=2 trace polynomial.

Only constant word topology is cached. Every gradient uses its actual state
and couplings, with the original product and accumulation order preserved.
"""

from functools import lru_cache
from types import SimpleNamespace

import numpy as np


def _readonly(values, dtype):
    array = np.asarray(values, dtype=dtype)
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


@lru_cache(maxsize=32)
def _plan(mass_x, mass_y, cross):
    from .independent import _trace_words
    member = SimpleNamespace(mass_x=mass_x, mass_y=mass_y, cross_coupling_gamma=cross)
    # The unchanged literal expansion owns all constant quartic coefficients.
    constants = {word: coefficient for coefficient, word in _trace_words(member, (0., 0.))}
    quadratic = tuple(tuple((3 * sector + a,) * 2 for a in range(3)) for sector in range(2))
    cubic = tuple(((3 * sector, 3 * sector + 1, 3 * sector + 2),
        (3 * sector, 3 * sector + 2, 3 * sector + 1)) for sector in range(2))
    words = tuple(sorted(set(constants) | {word for group in (*quadratic, *cubic) for word in group}))
    index = {word: at for at, word in enumerate(words)}
    entries = tuple((at, destination, word[occurrence + 1:] + word[:occurrence])
        for at, word in enumerate(words) for occurrence, destination in enumerate(word))
    groups = []
    for length in (1, 2, 3):
        selected = tuple(at for at, entry in enumerate(entries) if len(entry[2]) == length)
        groups.append((_readonly(selected, np.intp),
            _readonly([entries[at][2] for at in selected], np.intp)))
    return (_readonly([constants.get(word, 0j) for word in words], np.complex128),
        tuple(tuple(index[word] for word in group) for group in quadratic),
        tuple(tuple(index[word] for word in group) for group in cubic),
        _readonly([entry[0] for entry in entries], np.intp),
        _readonly([entry[1] for entry in entries], np.intp), tuple(groups))


def gradient(matrices, member, alpha_tilde):
    masses = float(member.mass_x), float(member.mass_y)
    cross = float(member.cross_coupling_gamma)
    couplings = np.asarray(alpha_tilde, dtype=np.float64)
    if (couplings.shape != (2,) or not np.isfinite(couplings).all()
            or np.min(couplings) < 0 or not np.isfinite((*masses, cross)).all()
            or min(*masses, cross) <= 0):
        raise ValueError('independent parameter potential changes its positive physical domain')
    base, quadratic, cubic, word_indices, destinations, groups = _plan(*masses, cross)
    coefficients = base.copy()
    for sector, mass in enumerate(masses):
        alpha = float(couplings[sector]) / 2
        beta = -alpha**2 * (2 * (3 * mass - 1) / 9)
        coefficients[list(quadratic[sector])] = 0j + 4 * beta
        for sign, at in zip((1, -1), cubic[sector], strict=True):
            coefficient = 4 * 2j * alpha * sign / 3
            # Three cyclic occurrences, in the literal expansion's order.
            coefficients[at] = ((0j + coefficient) + coefficient) + coefficient
    active = coefficients[word_indices] != 0
    products = np.empty((len(word_indices), 4, 4), dtype=np.complex128)
    for positions, remaining in groups:
        selected = active[positions]
        if not selected.any():
            continue
        indices = remaining[selected]
        value = matrices[indices[:, 0]]
        for at in range(1, indices.shape[1]):
            value = value @ matrices[indices[:, at]]
        products[positions[selected]] = value
    result = np.zeros_like(matrices)
    # Unbuffered indexed addition retains each original occurrence, including
    # repeated destinations; no reassociation or tree reduction is introduced.
    np.add.at(result, destinations[active], coefficients[word_indices[active], None, None] * products[active])
    return result
