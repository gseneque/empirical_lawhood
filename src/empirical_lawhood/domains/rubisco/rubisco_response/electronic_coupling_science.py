# SPDX-License-Identifier: MPL-2.0
"""Spin-resolved CDFT-CI and one-body SOC from retained determinants.

The CDFT-CI construction follows Oberhofer and Blumberger (2010),
DOI 10.1063/1.3507878. Cofactors, rather than an overlap inverse, retain
valid spin-flip matrix elements between orthogonal determinants.
"""

import math
from numbers import Real
from typing import Literal, NamedTuple


class OxygenCrossingDecision(NamedTuple):
    """A conditional decision at one resolved, isotropic singlet–triplet crossing."""

    lower_probability: float
    upper_probability: float
    decision: Literal["ATTEMPT_HOP", "STAY", "UNRESOLVED"]


def oxygen_singlet_triplet_gap(
    *, singlet_hartree: float, triplet_hartree: float, alternate_ms0_hartree: float,
    lower_root_tolerance_hartree: float, competition_window_hartree: float,
) -> float:
    """Select the singlet-minus-triplet gap after the independent broken-symmetry probe."""
    values = (singlet_hartree, triplet_hartree, alternate_ms0_hartree,
              lower_root_tolerance_hartree, competition_window_hartree)
    if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in values):
        raise ValueError("select all three finite electronic energies and both finite tolerances")
    singlet, triplet, alternate, tolerance, window = map(float, values)
    if tolerance < 0 or window < 0:
        raise ValueError("select nonnegative electronic root and competition tolerances")
    gap = singlet - triplet
    if not math.isfinite(gap):
        raise ValueError("the singlet–triplet gap exceeds finite numerical support")
    if alternate < singlet - tolerance and (alternate < triplet + window or abs(gap) < window):
        raise ValueError("a lower broken-symmetry Ms=0 state competes with the selected crossing")
    return gap


def oxygen_crossing_decision(
    *, incoming: Literal["S", "T"], coupling_squared_hartree2: float,
    coupling_squared_error_bound_hartree2: float, gap_speed_hartree_fs: float,
    minimum_resolved_gap_speed_hartree_fs: float, hbar_hartree_fs: float, draw: float,
) -> OxygenCrossingDecision:
    """Apply an original uniform draw to the bounded, donor-averaged spin coupling.

    The incoming triplet has one bright combination among three equally
    populated components. A singlet has one. The caller supplies the absolute
    gap speed, its selected resolution and the energy-time conversion.
    """
    from empirical_lawhood.methods.electronic_structure.surface_crossing import landau_zener_probability

    values = (coupling_squared_hartree2, coupling_squared_error_bound_hartree2,
              gap_speed_hartree_fs, minimum_resolved_gap_speed_hartree_fs, hbar_hartree_fs, draw)
    if (incoming not in ("S", "T")
            or any(isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x) for x in values)
            or min(coupling_squared_hartree2, coupling_squared_error_bound_hartree2,
                   minimum_resolved_gap_speed_hartree_fs) < 0
            or gap_speed_hartree_fs <= minimum_resolved_gap_speed_hartree_fs
            or hbar_hartree_fs <= 0 or not 0 <= draw < 1):
        raise ValueError("select an identified spin surface, finite coupling bounds, resolved gap speed and original draw")
    scale = hbar_hartree_fs * gap_speed_hartree_fs
    upper_coupling = coupling_squared_hartree2 + coupling_squared_error_bound_hartree2
    if not (0 < scale < math.inf and math.isfinite(upper_coupling)):
        raise ValueError("the selected crossing bounds exceed finite numerical support")
    multiplicity = 3 if incoming == "T" else 1
    lower, upper = (landau_zener_probability(value / scale, donor_components=multiplicity) for value in
                    (max(0.0, coupling_squared_hartree2 - coupling_squared_error_bound_hartree2), upper_coupling))
    if draw < lower:
        decision = "ATTEMPT_HOP"
    elif draw < upper:
        decision = "UNRESOLVED"
    else:
        decision = "STAY"
    return OxygenCrossingDecision(lower, upper, decision)


def determinant_cofactors(overlap):
    import numpy as np
    a = np.asarray(overlap)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not a.shape[0] or not np.isfinite(a).all():
        raise ValueError('determinant coupling requires a finite square occupied overlap')
    u, s, vh = np.linalg.svd(a, full_matrices=False)
    # prod(excluding i) remains defined with one or more exact zero singular
    # values. No rank truncation, pseudoinverse or singular-value floor occurs.
    before = np.concatenate(([1.], np.cumprod(s[:-1])))
    after = np.concatenate((np.cumprod(s[:0:-1])[::-1], [1.]))
    phase = np.linalg.det(u)*np.linalg.det(vh)
    cofactors = phase*((u.conj()*(before*after))@vh.conj())
    return phase*np.prod(s), cofactors, s


def occupied_spinors(coefficients, occupations):
    import numpy as np
    c, o = np.asarray(coefficients), np.asarray(occupations)
    if (c.ndim != 3 or c.shape[0] != 2 or o.shape != (2, c.shape[2])
            or not np.isfinite(c).all() or not np.isin(o, (0, 1)).all()):
        raise ValueError('determinant coupling requires complete binary spin-resolved occupations')
    alpha, beta = c[0][:, o[0] == 1], c[1][:, o[1] == 1]
    result = np.zeros((2*c.shape[1], alpha.shape[1]+beta.shape[1]), dtype=c.dtype)
    result[:c.shape[1], :alpha.shape[1]] = alpha
    result[c.shape[1]:, alpha.shape[1]:] = beta
    return result


def spin_diagonal(alpha_beta):
    import numpy as np
    a = np.asarray(alpha_beta)
    if a.ndim != 3 or a.shape[0] != 2 or a.shape[1] != a.shape[2]:
        raise ValueError('spin-diagonal operator changes its two complete AO blocks')
    n = a.shape[1]
    result = np.zeros((2*n, 2*n), dtype=a.dtype)
    result[:n, :n], result[n:, n:] = a
    return result


def spin_orbit_spinor(imaginary_cartesian):
    import numpy as np
    a = np.asarray(imaginary_cartesian)
    if (a.ndim != 3 or a.shape[0] != 3 or a.shape[1] != a.shape[2]
            or np.iscomplexobj(a) or not np.isfinite(a).all()
            or not np.allclose(a, -a.transpose(0, 2, 1), rtol=1e-9, atol=1e-12)):
        raise ValueError('spin-orbit operator changes its finite antisymmetric imaginary components')
    x, y, z = 1j*a
    return .5*np.block([[z, x-1j*y], [x+1j*y, -z]])


def one_body_element(left, right, operator, cofactors):
    import numpy as np
    return np.sum(cofactors*(left.conj().T@operator@right))


def singlet_triplet_spin_orbit(*, overlap, singlet_coefficients, singlet_occupations,
        triplet_coefficients, triplet_occupations, soc_imaginary,
        singlet_spin_square_excess, triplet_spin_square_excess, donor_is_triplet):
    """Complete all three M components under an explicit isotropic model.

    For pure S=0 and highest-weight S=1 originals, the three amplitudes are
    <S|H|T+>, <S|[H,S-]|T+>/sqrt(2), and
    <S|[[H,S-],S-]|T+>/2. Commutators of one-body operators are one-body
    operators, so the existing exact occupied cofactors suffice. No invented
    determinants, spin-transition probability or replicated SCF is needed.

    Spin-square excess bounds the distance to the corresponding pure-spin
    projection. Each reported amplitude carries the resulting conservative
    operator-norm error bound. Nonzero contamination is never relabelled as
    an exact spin eigenstate. Equal triplet weights are a declared zero-field,
    unpolarized model, not an empirical population or mutation invariance.
    """
    import numpy as np
    s = np.asarray(overlap)
    a = occupied_spinors(singlet_coefficients, singlet_occupations)
    b = occupied_spinors(triplet_coefficients, triplet_occupations)
    na = tuple(np.asarray(singlet_occupations).sum(axis=1))
    nb = tuple(np.asarray(triplet_occupations).sum(axis=1))
    if (a.shape != b.shape or a.shape[0] != 2*len(s)
            or na[0] != na[1] or nb[0]-nb[1] != 2 or type(donor_is_triplet) is not bool):
        raise ValueError('complete spin transfer requires an original singlet and highest-weight triplet with equal electrons')
    excess = (singlet_spin_square_excess, triplet_spin_square_excess)
    if any(not math.isfinite(x) or x < -1e-10 for x in excess):
        raise ValueError('spin completion requires finite nonnegative spin-square excess within roundoff')
    metric = spin_diagonal(np.stack((s, s)))
    if (not np.isfinite(metric).all() or not np.allclose(metric, metric.conj().T, rtol=0, atol=1e-10)
            or not np.allclose(a.conj().T@metric@a, np.eye(a.shape[1]), rtol=0, atol=1e-8)
            or not np.allclose(b.conj().T@metric@b, np.eye(b.shape[1]), rtol=0, atol=1e-8)):
        raise ValueError('spin completion requires normalized original determinants in one common metric')
    _, cofactor, _ = determinant_cofactors(a.conj().T@metric@b)
    n = len(s)
    lowering = np.zeros_like(metric)
    lowering[n:, :n] = np.eye(n)
    h = spin_orbit_spinor(soc_imaginary)
    first = h@lowering-lowering@h
    second = first@lowering-lowering@first
    operators = (h, first/math.sqrt(2), second/2)
    amplitudes = tuple(complex(one_body_element(a,b,op,cofactor)) for op in operators)
    eigen, vectors = np.linalg.eigh(metric)
    if np.min(eigen) <= 0:
        raise ValueError('spin completion requires a positive original AO metric')
    inverse_sqrt = (vectors/np.sqrt(eigen))@vectors.conj().T
    # The next possible S(S+1) eigenvalues differ by 2 and 4 respectively.
    contamination = tuple(min(1.,max(0.,x)/gap) for x,gap in zip(excess,(2.,4.),strict=True))
    distance = math.fsum(math.sqrt(2*w) for w in contamination)
    bounds = tuple(float(a.shape[1]*np.linalg.norm(inverse_sqrt@op@inverse_sqrt,ord=2)*distance)
        for op in operators)
    weight = 1./3 if donor_is_triplet else 1.
    h2 = weight*math.fsum(abs(v)**2 for v in amplitudes)
    h2_error = weight*math.fsum(2*abs(v)*bound+bound**2 for v,bound in zip(amplitudes,bounds,strict=True))
    return dict(triplet_m_order=(1,0,-1),singlet_bra_amplitudes_hartree=amplitudes,
        amplitude_error_bounds_hartree=bounds,coupling_squared_hartree2=h2,
        coupling_squared_error_bound_hartree2=h2_error,
        relative_coupling_squared_error_bound=h2_error/h2 if h2 else 0. if not h2_error else None,
        higher_spin_weight_upper_bounds=contamination,
        donor_population_model='ISOTROPIC_UNPOLARIZED_ZERO_FIELD',
        donor_triplet_component_weight=weight if donor_is_triplet else None,
        scope='COMPLETE_CONDITIONAL_SINGLET_TRIPLET_MULTIPLET_WITH_SPIN_CONTAMINATION_BOUNDS')


def pair_coupling(*, overlap, coefficients_a, occupations_a, energy_a,
        potential_a, coefficients_b, occupations_b, energy_b, potential_b,
        maximum_overlap, soc_imaginary=None):
    import numpy as np
    s = np.asarray(overlap)
    a, b = occupied_spinors(coefficients_a, occupations_a), occupied_spinors(coefficients_b, occupations_b)
    if a.shape != b.shape or a.shape[0] != 2*len(s):
        raise ValueError('electronic pair changes the complete electron or AO denominator')
    if not all(math.isfinite(float(x)) for x in (energy_a, energy_b, maximum_overlap)) or not 0 < maximum_overlap < 1:
        raise ValueError('electronic pair requires finite original energies and a nondegenerate overlap criterion')
    metric = spin_diagonal(np.stack((s, s)))
    va, vb = spin_diagonal(potential_a), spin_diagonal(potential_b)
    for operator in (metric, va, vb):
        if not np.isfinite(operator).all() or not np.allclose(operator, operator.conj().T, rtol=0, atol=1e-10):
            raise ValueError('electronic pair changes a finite Hermitian AO operator')
    det, cofactors, singular = determinant_cofactors(a.conj().T@metric@b)
    if abs(det) >= maximum_overlap:
        raise ValueError('electronic pair is too nearly identical for its selected two-state orthogonalization')
    expectation_a = np.trace(a.conj().T@va@a)
    expectation_b = np.trace(b.conj().T@vb@b)
    from_a = (energy_a+expectation_a)*det-one_body_element(a, b, va, cofactors)
    from_b = (energy_b+expectation_b)*det-one_body_element(a, b, vb, cofactors)
    h_ab = .5*(from_a+from_b)
    gram = np.array([[1, det], [det.conjugate(), 1]], dtype=complex)
    eigen, vectors = np.linalg.eigh(gram)
    if np.min(eigen) <= 0:
        raise ValueError('electronic pair has a nonpositive original determinant metric')
    inverse_sqrt = (vectors/np.sqrt(eigen))@vectors.conj().T
    # Centering before orthogonalization preserves a common energy shift at
    # molecular energy scales; the removed shift is an exact multiple of S.
    origin = .5*(energy_a+energy_b)
    h = np.array([[energy_a-origin, h_ab-origin*det],
        [(h_ab-origin*det).conjugate(), energy_b-origin]], dtype=complex)
    orthogonal = inverse_sqrt@h@inverse_sqrt
    soc = None
    if soc_imaginary is not None:
        operator = spin_orbit_spinor(soc_imaginary)
        diagonal_a = np.trace(a.conj().T@operator@a)
        diagonal_b = np.trace(b.conj().T@operator@b)
        off = one_body_element(a, b, operator, cofactors)
        soc = inverse_sqrt@np.array([[diagonal_a, off], [off.conjugate(), diagonal_b]])@inverse_sqrt
    return dict(determinant_overlap=complex(det), occupied_overlap_singular_values=singular,
        directional_hamiltonian_defect_hartree=float(abs(from_a-from_b)),
        spin_free_hamiltonian_hartree=orthogonal,
        common_energy_origin_hartree=float(origin),
        orthogonal_spin_free_coupling_hartree=complex(orthogonal[0, 1]),
        orthogonal_energy_gap_hartree=float((orthogonal[1, 1]-orthogonal[0, 0]).real),
        spin_orbit_hamiltonian_hartree=soc,
        orthogonal_spin_orbit_coupling_hartree=None if soc is None else complex(soc[0, 1]))
