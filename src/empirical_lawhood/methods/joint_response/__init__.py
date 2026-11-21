# SPDX-License-Identifier: MPL-2.0
"""Reusable joint response, finite transport and signed comparison calculations.

All methods are pure numerical operations. Scientific identity, measured inputs,
causal availability, support/measure assumptions and qualification belong to the
calling investigation. See ``docs/development/joint-response-calculus.md``.
"""
from .accounting import (
    ContrastAccount, PropagationAccount, ordered_propagator, propagation_accounting,
    signed_contrast_account, unitary_projection_bound,
)
from .spectral import (
    KrylovPrefix, PeriodicTail, PolynomialResponse, ResidualResponse,
    acquire_block_krylov, chebyshev_moments, chebyshev_response,
    constant_scalar_tail, finite_auxiliary_self_energy, finite_static_update,
    finite_update_response, galerkin_response, mechanical_admittance,
    omitted_update_bound, periodic_block_tail, residual_response,
    schur_head, tail_error_bound,
)
from .thermodynamics import (
    MeanBridge, PhysicalRemainder, TiltedMoments, finite_center_tilt,
    finite_filter_variance, finite_grid_from_means, finite_grid_mean_bridge,
    finite_record_covariance, finite_record_variance, finite_record_window,
    physical_remainder_bounds,
)


from .moments import (
    RationalConstraints, VerifiedDualBound, moment_hankel, moment_localizer,
    rational_moment_constraints, rational_moments_from_seed, rational_resolvent,
    support_polynomials, verify_dual_envelope,
)

from .calculus import (
    InputVisibility, RestraintJet, ResponseDerivative, harmonic_restraint_jet,
    input_visibility, recombine_ports, resolvent_directional_derivative,
    resolvent_mixed_derivative,
)
from .spectral import (
    AcquiredPolynomialResponse, acquire_chebyshev_response, chebyshev_required_degree,
)

from .spectral import inverse_residual_response, static_galerkin_response

__all__ = ['ContrastAccount', 'PropagationAccount', 'ordered_propagator', 'propagation_accounting', 'signed_contrast_account', 'unitary_projection_bound', 'KrylovPrefix', 'PeriodicTail', 'PolynomialResponse', 'ResidualResponse', 'acquire_block_krylov', 'chebyshev_moments', 'chebyshev_response', 'constant_scalar_tail', 'finite_auxiliary_self_energy', 'finite_static_update', 'finite_update_response', 'galerkin_response', 'mechanical_admittance', 'omitted_update_bound', 'periodic_block_tail', 'residual_response', 'schur_head', 'tail_error_bound', 'MeanBridge', 'PhysicalRemainder', 'TiltedMoments', 'finite_center_tilt', 'finite_filter_variance', 'finite_grid_from_means', 'finite_grid_mean_bridge', 'finite_record_covariance', 'finite_record_variance', 'finite_record_window', 'physical_remainder_bounds', 'RationalConstraints', 'VerifiedDualBound', 'moment_hankel', 'moment_localizer', 'rational_moment_constraints', 'rational_moments_from_seed', 'rational_resolvent', 'support_polynomials', 'verify_dual_envelope', 'InputVisibility', 'RestraintJet', 'ResponseDerivative', 'harmonic_restraint_jet', 'input_visibility', 'recombine_ports', 'resolvent_directional_derivative', 'resolvent_mixed_derivative', 'AcquiredPolynomialResponse', 'acquire_chebyshev_response', 'chebyshev_required_degree', 'inverse_residual_response', 'static_galerkin_response']
