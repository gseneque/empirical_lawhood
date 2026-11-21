# SPDX-License-Identifier: MPL-2.0
"""Explicit periodic Amber remainder and link-coordinate differentiation.

These primitives are candidates for exposed controls. They admit no source,
QM region, parameter set, native contact, enzyme model or scientific result.
"""

from math import fsum, isfinite



def _qm_selection(qm_indices, count):
    if (type(qm_indices) is not tuple or not qm_indices
            or any(type(i) is not int or not 0 <= i < count for i in qm_indices)
            or qm_indices != tuple(sorted(set(qm_indices))) or len(qm_indices) == count):
        raise ValueError('complete distinct ordered QM selection with an MM remainder required')
    return frozenset(qm_indices)


def linked_qm_coordinates(physical_coordinates, qm_indices, links):
    """Return real QM atoms followed by fixed-distance caps and their Jacobians."""
    import numpy as np
    xyz = np.asarray(physical_coordinates, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
        raise ValueError('complete finite Cartesian coordinates required')
    qm = _qm_selection(qm_indices, len(xyz))
    if type(links) is not tuple:
        raise ValueError('fixed complete link census required')
    rows = [xyz[i].copy() for i in qm_indices]
    jacobians, seen = [], set()
    for q, m, length in links:
        if (type(q) is not int or type(m) is not int or q not in qm or m in qm
                or not 0 <= m < len(xyz) or (q,m) in seen or type(length) is bool
                or not isfinite(float(length)) or length <= 0):
            raise ValueError('link must join a distinct selected QM/MM cut with a positive fixed length')
        seen.add((q,m))
        delta = xyz[m]-xyz[q]
        distance = float(np.linalg.norm(delta))
        if not float(length) < distance:
            raise ValueError('link cap reaches or exceeds its physical MM endpoint')
        direction = delta/distance
        transverse = float(length)/distance*(np.eye(3)-np.outer(direction,direction))
        rows.append(xyz[q]+float(length)*direction)
        jacobians.append((q,m,np.eye(3)-transverse,transverse))
    return np.asarray(rows), tuple(jacobians)


def pullback_qm_gradient(physical_count, qm_indices, qm_gradient, link_jacobians):
    """Project every real-QM and link derivative onto both physical endpoints."""
    import numpy as np
    _qm_selection(qm_indices, physical_count)
    gradient = np.asarray(qm_gradient, dtype=float)
    if gradient.shape != (len(qm_indices)+len(link_jacobians),3) or not np.isfinite(gradient).all():
        raise ValueError('complete finite real-QM and cap gradient required')
    result = np.zeros((physical_count,3))
    result[list(qm_indices)] += gradient[:len(qm_indices)]
    for g, (q,m,jq,jm) in zip(gradient[len(qm_indices):],link_jacobians,strict=True):
        result[q] += jq.T@g
        result[m] += jm.T@g
    return result


def shifted_embedding_charges(original_charges, qm_indices, bonds, cuts):
    """Redistribute cut-endpoint charges only in the electronic embedding.

    Each distinct MM cut atom is set to zero and its original charge is divided
    equally among its directly bonded MM neighbours. There are no additional
    dipole sites in this declared convention. The MM force field is separate.
    Connectivity and the complete QM/MM cut census must be source-derived.
    """
    if (type(original_charges) is not tuple or not original_charges
            or any(type(q) is bool or not isfinite(float(q)) for q in original_charges)):
        raise ValueError('complete finite original charge population required')
    count = len(original_charges)
    qm = _qm_selection(qm_indices, count)
    if type(bonds) is not tuple or type(cuts) is not tuple:
        raise ValueError('fixed complete source bonds and cuts required')
    seen, neighbours = set(), {i:set() for i in range(count)}
    for pair in bonds:
        if (type(pair) is not tuple or len(pair) != 2
                or any(type(i) is not int or not 0 <= i < count for i in pair)
                or pair[0] >= pair[1] or pair in seen):
            raise ValueError('source bonds must be complete distinct canonical atom pairs')
        a,b = pair
        seen.add(pair)
        neighbours[a].add(b)
        neighbours[b].add(a)
    expected = tuple(sorted((a,b) if a in qm else (b,a)
                           for a,b in bonds if (a in qm) != (b in qm)))
    if (any(type(pair) is not tuple or len(pair) != 2
            or any(type(i) is not int for i in pair) for pair in cuts)
            or cuts != expected or len({m for _,m in cuts}) != len(cuts)):
        raise ValueError('every source QM/MM cut must occur once with a distinct MM endpoint')
    cut_mm = {m for _,m in cuts}
    contributions = {i:[0.0 if i in qm or i in cut_mm else float(original_charges[i])]
                     for i in range(count)}
    rows = []
    for q,m in cuts:
        recipients = tuple(sorted(neighbours[m]-qm))
        if not recipients or set(recipients)&cut_mm:
            raise ValueError('each cut needs directly bonded MM recipients outside the cut endpoints')
        share = float(original_charges[m])/len(recipients)
        for i in recipients:
            contributions[i].append(share)
        rows.append(dict(qm_endpoint=q,mm_endpoint=m,original_mm_charge=float(original_charges[m]),
                         recipients=recipients,charge_added_per_recipient=share))
    result = tuple(fsum(contributions[i]) for i in range(count))
    before = fsum(float(q) for i,q in enumerate(original_charges) if i not in qm)
    after = fsum(result)
    if abs(before-after)>1e-10:
        raise ValueError('electronic embedding redistribution changes the total MM charge')
    return result, dict(cuts=tuple(rows),original_mm_charge=before,embedding_mm_charge=after,
        dipole_correction=False,mm_force_field_charges_changed=False)
