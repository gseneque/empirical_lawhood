# SPDX-License-Identifier: MPL-2.0
"""Recognize covalent product geometry in unwrapped enzyme coordinates (Å).

The two substrate phosphorus atoms identify the original arms. Gas provenance,
the complete heavy-atom graph, stereochemistry and carbon-bound hydrogens are
checked before counting a bound product. Release and kinetic commitment need
separate observations.
"""

from collections.abc import Sequence
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike
from scipy.spatial import cKDTree


# Generous first-shell upper limits. Do not infer covalent Mg coordination.
_CUTOFF = {
    "CC": 1.78,
    "CN": 1.68,
    "CO": 1.65,
    "CS": 1.96,
    "NN": 1.60,
    "NO": 1.60,
    "OO": 1.68,
    "OP": 1.85,
    "OS": 1.82,
    "SS": 2.22,
}


def _selected_geometry(elements, xyz, phosphorus, explicit_hydrogens):
    x = np.asarray(xyz)
    e = tuple(elements)
    p = tuple(phosphorus)
    if (
        x.shape != (len(e), 3)
        or x.dtype.kind not in "iuf"
        or not np.isfinite(x).all()
        or type(explicit_hydrogens) is not bool
        or len(p) != 2
        or len(set(p)) != 2
        or any(not _index(i, len(e)) or e[i] != "P" for i in p)
    ):
        raise ValueError(
            "Select both native substrate phosphorus atoms and complete finite coordinates"
        )
    return e, x.astype(float, copy=False), p


def _index(index, size):
    return isinstance(index, (int, np.integer)) and not isinstance(index, (bool, np.bool_)) and 0 <= index < size


def product_fragments(elements: Sequence[str], xyz: ArrayLike, phosphorus: Sequence[int], *, explicit_hydrogens: bool = True):
    """Return recognized 3PG and 2PG fragments, including their native atoms."""
    e, x, p = _selected_geometry(elements, xyz, phosphorus, explicit_hydrogens)
    return _fragments(e, x, p, explicit_hydrogens)


def _fragments(e, x, p, explicit_hydrogens):
    graph = [set() for _ in e]
    h = np.flatnonzero(np.asarray(e) == "H")
    for a, b in cKDTree(x).query_pairs(2.22):
        limit = _CUTOFF.get("".join(sorted((e[a], e[b]))))
        if limit and np.linalg.norm(x[a] - x[b]) < limit:
            graph[a].add(b)
            graph[b].add(a)

    def attached(atom, element):
        return sorted(i for i in graph[atom] if e[i] == element)

    def hydrogen_count(i):
        return np.count_nonzero(np.linalg.norm(x[h] - x[i], axis=1) < 1.24)

    fragments = []
    for phosphate in p:
        oxygens = attached(phosphate, "O")
        bridges = [
            i for i in oxygens if len(graph[i]) == 2 and len(attached(i, "C")) == 1
        ]
        if (
            len(oxygens) != 4
            or len(graph[phosphate]) != 4
            or len(bridges) != 1
            or any(len(graph[i]) != 1 for i in oxygens if i not in bridges)
        ):
            continue
        bridge = bridges[0]
        (terminal,) = attached(bridge, "C")
        chain = attached(terminal, "C")
        if len(graph[terminal]) != 2 or len(chain) != 1:
            continue
        (inner,) = chain
        carbon = [i for i in attached(inner, "C") if i != terminal]
        members = {phosphate, *oxygens, terminal, inner}
        if carbon:
            hydroxyl = attached(inner, "O")
            if len(graph[inner]) != 3 or len(carbon) != 1 or len(hydroxyl) != 1:
                continue
            (acid,) = carbon
            (oh,) = hydroxyl
            signed_volume = np.linalg.det(x[[acid, oh, terminal]] - x[inner])
            if len(graph[oh]) != 1 or signed_volume < 1.0:
                continue
            if explicit_hydrogens and hydrogen_count(inner) != 1:
                continue
            members.update((acid, oh))
            species = "3PG"
        else:
            acid = inner
            species = "2PG"
        carboxyl = attached(acid, "O")
        if (
            len(graph[acid]) != 3
            or len(carboxyl) != 2
            or any(len(graph[i]) != 1 for i in carboxyl)
            or max(np.linalg.norm(x[i] - x[acid]) for i in carboxyl) > 1.46
        ):
            continue
        if explicit_hydrogens and (
            hydrogen_count(terminal) != 2 or hydrogen_count(acid) != 0
        ):
            continue
        members.update(carboxyl)
        fragments.append((species, frozenset(members), acid))
    return fragments


def bound_products(
    elements: Sequence[str], xyz: ArrayLike, phosphorus: Sequence[int], gas: Sequence[int], backbone: Sequence[int],
    *, singlet: bool, explicit_hydrogens: bool = True
) -> Literal["2x3PG", "2PG+3PG"] | None:
    """Classify bound products. An intact peroxide or carbon carbanion is pending."""
    gas = tuple(gas)
    el, x, p = _selected_geometry(elements, xyz, phosphorus, explicit_hydrogens)
    if type(singlet) is not bool or len(set(gas)) != len(gas) or any(not _index(i, len(el)) for i in gas):
        raise ValueError("Invalid native gas indices")
    if tuple(el[i] for i in gas) not in (("C", "O", "O"), ("O", "O")):
        raise ValueError("Native tagged gas must be C,O,O or O,O")
    if (
        len(backbone) != 2
        or len(set(backbone)) != 2
        or any(not _index(i, len(el)) or el[i] != "C" for i in backbone)
    ):
        raise ValueError("Select original RuBP C2 and C3")
    if (
        not singlet
        or not set(backbone).isdisjoint(gas)
        or np.linalg.norm(x[backbone[0]] - x[backbone[1]]) < 2.65
        or len(gas) == 2
        and np.linalg.norm(x[gas[0]] - x[gas[1]]) < 2.55
    ):
        return None
    fragments = _fragments(el, x, p, explicit_hydrogens)
    if len(fragments) != 2 or not fragments[0][1].isdisjoint(fragments[1][1]):
        return None
    species = sorted(row[0] for row in fragments)
    if len(gas) == 3 and species == ["3PG", "3PG"]:
        if any(
            acid == gas[0] and set(gas) <= members for _, members, acid in fragments
        ):
            return "2x3PG"
    if len(gas) == 2 and species == ["2PG", "3PG"]:
        if any(
            kind == "2PG" and len(set(gas) & members) == 1
            for kind, members, _ in fragments
        ):
            return "2PG+3PG"
    return None
