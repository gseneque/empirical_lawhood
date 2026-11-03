"""Pure full-history checks from independently differentiated trace polynomials.

No producer, native marcher, force, gradient, bridge or random-stream helper is
imported here. Every retained primary and fine transition is checked locally;
the consumer owns no acquisition, source registration or scientific verdict.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Mapping

import numpy as np

IMPLEMENTATION_ID = 'matrix-parameter-q2.independent-history-controls.v1'
ERROR_NORM = 'FULL_REAL_HERMITIAN_HS_L2'
_STATE_SHAPE = (2, 3, 4, 4)
_MEMBERS = frozenset({
    'primary_positions', 'primary_momenta', 'fine_positions', 'fine_momenta',
    'primary_alpha_tilde', 'fine_alpha_tilde', 'primary_ticks', 'fine_ticks',
    'primary_innovations', 'fine_innovations', 'bridge_innovations',
})


def _hermitian(value: np.ndarray) -> np.ndarray:
    return (value + value.swapaxes(-1, -2).conj()) / 2


def _position(value: Any) -> np.ndarray:
    result = np.asarray(value)
    if (result.shape != _STATE_SHAPE or result.dtype != np.dtype('complex128')
            or not np.isfinite(result).all()
            or np.linalg.norm(result - result.swapaxes(-1, -2).conj()) > 1e-12):
        raise ValueError('independent parameter potential needs full finite Hermitian q=2 positions')
    return result


def _trace_words(member: Any, alpha_tilde: Any) -> tuple[tuple[complex, tuple[int, ...]], ...]:
    """Expand the literal potential sums, folding only trace cyclic rotations.

    The six indices name X0/X1/X2/Y0/Y1/Y2. Differentiation below uses ordered
    matrix products, rather than the production nested-commutator equations.
    """
    masses = float(member.mass_x), float(member.mass_y)
    cross = float(member.cross_coupling_gamma)
    couplings = np.asarray(alpha_tilde, dtype=np.float64)
    if (couplings.shape != (2,) or not np.isfinite(couplings).all()
            or np.min(couplings) < 0 or not np.isfinite((*masses, cross)).all()
            or min(*masses, cross) <= 0):
        raise ValueError('independent parameter potential changes its positive physical domain')
    words: dict[tuple[int, ...], complex] = {}

    def add(coefficient: complex, word: tuple[int, ...]) -> None:
        # Tr(A B C D) = Tr(B C D A); this saves repeated literal products.
        key = min(word[index:] + word[:index] for index in range(len(word)))
        words[key] = words.get(key, 0j) + coefficient

    def commutator_square(coefficient: complex, a: int, b: int) -> None:
        add(coefficient, (a, b, a, b))
        add(-coefficient, (a, b, b, a))
        add(-coefficient, (b, a, a, b))
        add(coefficient, (b, a, b, a))

    epsilon_terms = (
        (1, (0, 1, 2)), (1, (1, 2, 0)), (1, (2, 0, 1)),
        (-1, (0, 2, 1)), (-1, (2, 1, 0)), (-1, (1, 0, 2)),
    )
    for sector, mass in enumerate(masses):
        offset = 3 * sector
        alpha = float(couplings[sector]) / 2
        # q=2: n=q^2=4, c2=(q^2-1)/4=3/4; M is a potential coefficient.
        beta = -alpha**2 * (2 * (3 * mass - 1) / 9)
        for a in range(3):
            add(4 * beta, (offset + a, offset + a))
            for b in range(3):
                commutator_square(-1, offset + a, offset + b)
                add(4 * mass, (offset + a, offset + a, offset + b, offset + b))
        for sign, indices in epsilon_terms:
            add(4 * 2j * alpha * sign / 3, tuple(offset + index for index in indices))
    for a in range(3):
        for b in range(3):
            commutator_square(-2 * cross, a, 3 + b)
    return tuple((coefficient, word) for word, coefficient in sorted(words.items()) if coefficient != 0)


def _word_product(matrices: np.ndarray, word: tuple[int, ...]) -> np.ndarray:
    result = matrices[word[0]]
    for index in word[1:]:
        result = result @ matrices[index]
    return result


def potential(position: Any, member: Any, alpha_tilde: Any) -> float:
    """Independent literal trace potential, available for gradient FD controls."""
    matrices = _position(position).reshape(6, 4, 4)
    total = sum(coefficient * np.trace(_word_product(matrices, word))
                for coefficient, word in _trace_words(member, alpha_tilde))
    if not np.isfinite(total) or abs(total.imag) > 1e-9 * max(1., abs(total.real)):
        raise FloatingPointError('independent parameter potential is not finite and real')
    return float(total.real)


def potential_gradient(position: Any, member: Any, alpha_tilde: Any) -> np.ndarray:
    """Differentiate every occurrence in every ordered trace polynomial word.

    For Tr(A dZ B), the Hermitian-metric coefficient is Hermitian(B A).
    This preserves both sectors and all96 real position coordinates.
    """
    matrices = _position(position).reshape(6, 4, 4)
    from .independent_polynomial import gradient as compiled_gradient
    gradient = compiled_gradient(matrices, member, alpha_tilde)
    result = _hermitian(gradient).reshape(_STATE_SHAPE)
    if not np.isfinite(result).all():
        raise FloatingPointError('independent parameter gradient is not finite')
    return result


def _step_constants(view):
    dt = float(view.timestep)
    decay = float(np.exp(-float(view.friction_gamma) * dt))
    scale = float(np.sqrt(float(view.bath_temperature) * (1 - decay**2)))
    return dt, decay, scale


def _reference_step(position: np.ndarray, momentum: np.ndarray, innovation: np.ndarray,
                    member: Any, view: Any, current_alpha: np.ndarray,
                    next_alpha: np.ndarray, *, constants=None) -> tuple[np.ndarray, np.ndarray]:
    """One unit-kinetic-mass BAOAB transition at both retained schedules."""
    dt, decay, scale = _step_constants(view) if constants is None else constants
    p = _hermitian(momentum - dt / 2 * potential_gradient(position, member, current_alpha))
    x = _hermitian(position + dt / 2 * p)
    p = _hermitian(decay * p + scale * innovation)
    x = _hermitian(x + dt / 2 * p)
    p = _hermitian(p - dt / 2 * potential_gradient(x, member, next_alpha))
    return x, p


def _trajectory_errors(positions, momenta, innovations, member, view, schedules,
                       next_schedules: Iterable[np.ndarray], *, terminal=None) -> list[float]:
    """Full phase residuals over an already guarded dense or segmented block."""
    errors = []
    constants = _step_constants(view)
    for step, (innovation, next_alpha) in enumerate(zip(innovations, next_schedules, strict=True)):
        x, p = _reference_step(positions[step], momenta[step], innovation,
                               member, view, schedules[step], next_alpha, constants=constants)
        actual_x, actual_p = ((positions[step + 1], momenta[step + 1])
                             if step + 1 < len(positions) else terminal)
        errors.append(float(np.linalg.norm(np.stack((actual_x - x, actual_p - p)))))
    return errors


def _ou_errors(view, coarse_innovations, fine_innovations, bridge_innovations):
    """Original weighted innovation and bath residuals over one guarded block."""
    half_decay = float(np.exp(-float(view.friction_gamma) * float(view.timestep) / 2))
    normalizer = float(np.sqrt(1 + half_decay**2))
    fine_scale = float(np.sqrt(float(view.bath_temperature) * (1 - half_decay**2)))
    coarse_decay = float(np.exp(-float(view.friction_gamma) * float(view.timestep)))
    coarse_scale = float(np.sqrt(float(view.bath_temperature) * (1 - coarse_decay**2)))
    innovation_errors, bath_errors = [], []
    for step, (coarse, bridge) in enumerate(zip(coarse_innovations, bridge_innovations, strict=True)):
        first, second = fine_innovations[2 * step:2 * step + 2]
        expected_first = (half_decay * coarse + bridge) / normalizer
        expected_second = (coarse - half_decay * bridge) / normalizer
        innovation_errors.append(float(np.linalg.norm(np.stack((first - expected_first,
                                                               second - expected_second)))))
        bath_errors.append(float(np.linalg.norm(fine_scale * (half_decay * first + second)
                                                - coarse_scale * coarse)))
    return innovation_errors, bath_errors


def _validated_arrays(coordinate: Any, arrays: Mapping[str, np.ndarray]) -> None:
    """Enforce the complete numerical denominator before any control arithmetic."""
    n = coordinate.total_ticks
    if type(n) is not int or n < 1 or coordinate.q != 2 or set(arrays) != _MEMBERS:
        raise ValueError('independent parameter consumer needs its exact complete q=2 array census')
    for prefix, multiplier in (('primary', 1), ('fine', 2)):
        steps = multiplier * n
        for name, shape, dtype in (
            ('positions', (steps + 1, *_STATE_SHAPE), np.dtype('complex128')),
            ('momenta', (steps + 1, *_STATE_SHAPE), np.dtype('complex128')),
            ('alpha_tilde', (steps + 1, 2), np.dtype('float64')),
            ('ticks', (steps + 1,), np.dtype('int64')),
            ('innovations', (steps, *_STATE_SHAPE), np.dtype('complex128')),
        ):
            value = np.asarray(arrays[f'{prefix}_{name}'])
            if value.shape != shape or value.dtype != dtype or not np.isfinite(value).all():
                raise ValueError('independent parameter consumer loses full state/noise/schedule/clock geometry')
    bridge = np.asarray(arrays['bridge_innovations'])
    if (bridge.shape != (n, *_STATE_SHAPE) or bridge.dtype != np.dtype('complex128')
            or not np.isfinite(bridge).all()):
        raise ValueError('independent parameter consumer loses its complete bridge innovations')


def _decimal(value: float) -> Decimal:
    if not np.isfinite(value):
        raise FloatingPointError('independent parameter control residual is not finite')
    return Decimal(repr(float(value)))


def _control(control_id: str, method: str, errors: list[float], tolerance: Decimal,
             real_coordinates: int) -> dict[str, Any]:
    measured = tuple(_decimal(value) for value in errors)
    failed = tuple(index for index, value in enumerate(measured, start=1) if value > tolerance)
    return {
        'control_id': control_id, 'method': method, 'error': max(measured),
        'tolerance': tolerance, 'disposition': 'VIOLATED' if failed else 'SATISFIED',
        'measured_errors': measured, 'failed_steps': failed,
        'denominator_steps': len(measured), 'denominator_real_coordinates': real_coordinates,
    }


def assess_arrays(coordinate: Any, arrays: Mapping[str, np.ndarray], *,
                  trajectory_tolerance: Decimal,
                  bridge_tolerance: Decimal) -> tuple[dict[str, Any], ...]:
    """Check every retained primary/fine transition and weighted OU operand.

    Errors are full real-Hermitian Hilbert--Schmidt L2 norms. Coordinate counts
    are per measured step; their product with denominator_steps is the complete
    scalar denominator. Source identity, exact schedules/clocks and initial
    state authentication belong to the caller's guarded typed-source join.
    """
    for tolerance in (trajectory_tolerance, bridge_tolerance):
        if type(tolerance) is not Decimal or not tolerance.is_finite() or tolerance <= 0:
            raise ValueError('independent parameter controls require positive exact Decimal tolerances')
    _validated_arrays(coordinate, arrays)
    controls = []
    for prefix, view in (('primary', coordinate.primary_view), ('fine', coordinate.fine_view)):
        positions, momenta = arrays[f'{prefix}_positions'], arrays[f'{prefix}_momenta']
        schedules, innovations = arrays[f'{prefix}_alpha_tilde'], arrays[f'{prefix}_innovations']
        errors = _trajectory_errors(positions, momenta, innovations, coordinate.member, view,
                                    schedules, schedules[1:])
        controls.append(_control(f'control.{prefix}-trajectory',
            f'{prefix.upper()}_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS',
            errors, trajectory_tolerance, 192))

    innovation_errors, bath_errors = _ou_errors(coordinate.primary_view, arrays['primary_innovations'],
                                               arrays['fine_innovations'], arrays['bridge_innovations'])
    controls.append(_control('control.ou-innovation-reconstruction',
        'WEIGHTED_OU_FULL192_ORIGINAL_COARSE_AND_BRIDGE_ALL_STEPS',
        innovation_errors, bridge_tolerance, 192))
    controls.append(_control('control.ou-bath-impulse',
        'WEIGHTED_OU_FULL96_BATH_SCALED_COMPOSED_IMPULSE_ALL_STEPS',
        bath_errors, trajectory_tolerance, 96))
    return tuple(controls)
