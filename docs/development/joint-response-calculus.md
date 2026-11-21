# Joint response calculus and signed prediction accounting

SPDX-License-Identifier: CC-BY-4.0

## Scope and ownership

`empirical_lawhood.methods.joint_response` implements the generic finite-dimensional
calculus from *Joint response calculus for receiver admittance and Rubisco
prediction* (10 November 2026), together with the signed endpoint and propagation
accounting in *Constructing the conditions of reusable scientific knowledge*
(draft v0.1). These are independently callable numerical methods. The classical
matrix programme supplies actual native operators, physical ports, preparations,
assessments, original numerical views and acquisition costs through the ordinary
recursive workflow. The helpers do not create a second execution service, store,
scientific registry or result authority.

The complementary finite retained-coordinate derivation is already implemented
in [`retained_gaussian_response`](../../src/empirical_lawhood/methods/retained_gaussian_response.py)
and documented in [its method guide](retained-gaussian-response.md). Its Gaussian
reference, conditional elimination, finite nonlinear Boltzmann modification,
partition factors, Galerkin compliance enclosures, residual envelopes and harmonic
bath remain the authoritative implementations. No duplicate static reducer is
introduced here. A method calling those routines must preserve their Cartesian
measure, positive-reference, physical-residual and native-input assumptions.

The new package imports no matrix or Rubisco programme. The same function can
consume a small analytical control, a measured finite operator or a domain's
acquired native action block. Applicability is supplied by the calling scientific
contract; moving code into `methods/` does not establish that applicability.

## Supported calculations

| Derivation | Public method | Important contract |
| --- | --- | --- |
| Joint physical spectral geometry; rank deflation | `acquire_block_krylov`, `KrylovPrefix.prefix` | Fixed self-adjoint operator; physical seed amplitudes retained; exact acquired actions reused |
| Receiver/input resolvent and dual residual correction | `galerkin_response`, `residual_response` | Nonreal spectral argument; adjoint trial at the conjugate argument; uniform operator discrepancy explicit |
| Positive-static or explicitly bounded nonnormal inverse | `static_galerkin_response`, `inverse_residual_response` | Actual native lower gap or independently justified inverse norm; no normality inferred |
| Exact finite auxiliary tail and block continued fraction | `finite_auxiliary_self_energy`, `schur_head` | Hermitian finite tail; rectangular upper-coupling orientation explicit |
| Constant and periodic continuations | `constant_scalar_tail`, `periodic_block_tail` | A chosen continuation is a model, not an identified native tail; iteration bound requires contraction |
| Computable propagation of a supplied tail discrepancy | `tail_error_bound` | Self-adjoint normalized tail measures and a valid tail envelope |
| Singular finite changes | `finite_update_response`, `finite_static_update`, `omitted_update_bound` | Actual update factors and omitted-operator bound; no inverse of the possibly singular update matrix |
| Physical mechanical response | `mechanical_admittance` | Entire completed stiffness nonnegative, not merely positive individual blocks |
| Fixed-frequency stopping without a fitted tail or SDP | `chebyshev_moments`, `chebyshev_response`, `chebyshev_required_degree`, `acquire_chebyshev_response` | A justified enclosing spectral interval and explicit moment/acquisition errors |
| Rational-moment response constraints | `rational_moments_from_seed`, `rational_resolvent`, `moment_hankel`, `moment_localizer`, `rational_moment_constraints` | Complete moment indices and only justified support/gaps/atoms |
| Checkable dual proof object | `verify_dual_envelope` | PSD Gram factors, exact rational coefficient arithmetic, coefficient mismatch and simultaneous moment-error allowances |
| Moving operators and physical ports | `resolvent_directional_derivative`, `resolvent_mixed_derivative`, `recombine_ports` | Receiver/input changes remain separate terms; matrix order preserved |
| Distinguishable declared input directions | `input_visibility` | Rank applies to the declared available inputs, acquired depth and numerical threshold |
| Finite time and initial preparation | `unitary_projection_bound`, `ordered_propagator` | Unitary norm bound only for a self-adjoint native generator; chronological order retained |
| Nonlinear physical restraint jet | `harmonic_restraint_jet` | Complete differentiable receiver gradient and Hessian on the actual coordinate measure |
| Finite-grid anchored mean transport | `finite_grid_mean_bridge`, `finite_grid_from_means` | Actual canonical mean anchor and centre-dependent variance contrast, common beta and stiffness |
| Finite centre tilt | `finite_center_tilt` | Exact for the supplied finite weighted measure; native ensemble adequacy and overlap remain separate |
| Physical model-to-variance allowance | `physical_remainder_bounds` | Global potential oscillation and actual reference receiver RMS error; local bounds alone are insufficient |
| Complete signed estimator variance | `finite_record_covariance`, `finite_record_variance`, `finite_filter_variance`, `finite_record_window` | Stationary declared joint sampling law; measured or justified cross-covariances |
| Manuscript endpoint/contrast identity | `signed_contrast_account` | Signed, matched, consistently normalized endpoint errors and original masks |
| Manuscript inherited/generated decomposition | `propagation_accounting` | Actual full/reduced steps, same physical lift and retained checkpoint; no substitute projected full step |

## A complete reusable response calculation

The following example acquires four native action blocks, then evaluates two
prefixes without reacquiring actions. Physical ports are not silently normalized
away. The dense solve appears only in the optional numerical control.

```python
import numpy as np
from empirical_lawhood.methods.joint_response import (
    acquire_block_krylov,
    galerkin_response,
)

stiffness = np.diag(np.linspace(0.5, 4.0, 20))
receiver = np.ones((20, 1))
input_port = np.linspace(-1.0, 1.0, 20)[:, None]
ports = np.column_stack((receiver, input_port))
prefix = acquire_block_krylov(stiffness, ports, blocks=4)

for depth in (2, 4):
    result = galerkin_response(
        prefix.prefix(depth), receiver, 0.2 + 0.7j, inputs=input_port
    )
    print(depth, result.estimate, result.bound)

# Independent numerical verification only:
reference = receiver.T @ np.linalg.solve(
    (0.2 + 0.7j) * np.eye(20) - stiffness, input_port
)
assert np.linalg.norm(reference - result.estimate, 2) <= result.bound + 1e-12
```

The spectral convention is `(z I - A)^-1`, with an anti-Herglotz joint response in
the upper half-plane. A mechanical stiffness uses squared-frequency eigenvalues.
A general BAOAB phase-space map is not made self-adjoint by this method; use the
actual symmetric Hessian for the spectral calculation, or a separately justified
non-normal inverse bound. An indefinite Hermitian Hessian is valid at nonreal
`z`; it is not a positive harmonic equilibrium reference.

A callable action supplier receives a matrix of physical column vectors. It must
return matching native actions under its self-adjoint operator contract. The
method checks dimensions, finite values and projected Hermiticity, but no finite
set of probes proves global self-adjointness. Numerical deflation and seed
reconstruction errors remain inspectable. Certification uses all retained native
`AQ`, so it does not discard a boundary residual merely because the next Krylov
block was small. A shorter prefix keeps the original acquired block gauge.

`ResidualResponse.estimate` includes the dual correction. Its error obeys the
native residual identity, but a corrected scalar/matrix target estimate need not
be a passive global model or improve on the raw estimate.
`ResidualResponse.raw_estimate` remains available for that comparison. For an
approximate action supplier, the declared uniform operator error is charged both
in primal/dual residual norms and in the correction's own action discrepancy.
A few directional checks do not establish that uniform bound.

## Solver-free bounded acquisition

```python
from empirical_lawhood.methods.joint_response import acquire_chebyshev_response

bounded = acquire_chebyshev_response(
    stiffness,
    ports,
    0.2 + 0.7j,
    spectral_interval=(0.5, 4.0),
    tolerance=1e-6,
    maximum_degree=80,  # optional actual acquisition allowance
)
print(bounded.response.estimate, bounded.response.bound)
print(bounded.action_count, bounded.tolerance_met)
```

The degree is derived from the closed-form Chebyshev remainder. The method
returns an unresolved bound when the selected acquisition allowance is too small.
It does not tighten the support interval, regularize an indefinite operator, or
reinterpret a failed tolerance as a success. Without `maximum_degree`, the
sufficient degree is acquired. Near a spectrum or a closing static gap this may
be expensive; that is a scientific cost finding to retain.

The dense interface checks the selected interval against the supplied matrix.
A native action interface requires its supplier to justify the interval; a
smallest Ritz value is not a lower bound on the complete spectrum. If a dense
eigenanalysis was needed to obtain the interval, its acquisition cost belongs in
the experiment. The default complete route controls polynomial truncation for the
specified exact operator, numerically evaluated in binary64. For approximate
moments, call `chebyshev_response(..., moment_error_bounds=...)` with simultaneous
upstream error bounds. Physical and statistical errors are additional.

## Rational outer bounds and exact dual verification

The package constructs the finite rational-moment constraints with the original
index ranges. `rational_moment_constraints` evaluates a supplied weighted moment
sequence; PSD feasibility is a diagnostic, not an optimized bound. It supports
an outer interval, forbidden gaps and isolated allowed atoms. Removing a possible
boundary atom because it is outside the bulk bands changes the admissible measure
and can invalidate an enclosure.

An SDP optimizer is intentionally not made a required dependency. The executable
Chebyshev route supplies an outer error bound without one. A future optional SDP
adapter can consume the generic constraints and return dual coefficients and
Gram factors. `verify_dual_envelope` already checks such a certificate without
trusting its optimizer's status or primal objective.

The verifier accepts Hermitian coefficients `Y_k`, moments `M_k`, target `W`,
nonreal `z`, and Gram factors `F`, whose squares make PSD contributions by
construction. It evaluates the coefficient identity, objective and error allowance
using exact rational arithmetic on the supplied finite binary64 values. It
accounts for coefficient mismatches over the declared compact support, using an
upper bound on the mass of the rationally weighted measure. Simultaneous moment
errors are charged through a conservative nuclear-norm upper bound. The final
float is rounded outward; the exact rational numerator and denominator are also
returned. This avoids an unchecked small negative eigenvalue in a nominal Gram
matrix. Hermitian coefficient and moment inputs must be exactly Hermitian as
supplied to this exact verifier; silently symmetrizing an uncertain empirical
moment would change the object being bounded.

For example, the unit-mass upper bound `-Im R(i) <= 1` has the exact certificate
`(lambda**2 + 1)*1 - 1 = lambda**2`:

```python
from empirical_lawhood.methods.joint_response import verify_dual_envelope

certificate = verify_dual_envelope(
    original_moments=[[[1.0]]],
    coefficients=[[[1.0]]],
    target=[[-1j]],
    z=1j,
    gram_factor=[[0.0, 1.0]],
)
assert certificate.value == 1.0
assert certificate.polynomial_allowance == 0.0
```

A loose or badly reconstructed candidate can still yield a valid wide bound after
its mismatch allowance. This is deliberate: accuracy of a chosen model and
validity of a target enclosure remain separate questions. The helper does not
claim an optimized SDP interval or universally cheap tail identification.

## Thermodynamic connection and its limits

The finite-grid identity is implemented with the *original* centres and weights:

\[
Q=-\alpha k\Big(\sum_i\omega_i\Big)\Delta\mu_a
  -\alpha\beta k^2\sum_j\Big(\sum_{i>j}\omega_i\Big)
        \int_{s_j}^{s_{j+1}}\Delta v(u)\,du .
\]

Here `energy_scale=alpha`: use 1 for dimensionless controls or already matching
energy units, and 1000 exactly once for kJ/mol to J/mol. Arbitrary real weights are
supported. A finite trapezoidal target is not replaced by its continuous endpoint
free-energy difference. The canonical anchor is supplied independently: an initial
coordinate, normalized covariance spectrum or inserted constant seed does not
infer the missing mean.

`finite_grid_mean_bridge` reports `quadrature_error_estimate` as an estimate.
Quadrature convergence warnings raise `ArithmeticError`. It returns
`total_error_bound` only when the caller supplies anchor, variance and numerical
integration enclosures. A uniform variance envelope has an analytic interval
integral. For a callable envelope, its numerical integral remains
`upstream_error_estimate`; `upstream_error_bound` is `None`. The caller's supplied
integration enclosure must cover *all* numerical integrals, including the error
envelope, before `total_error_bound` has its stated meaning.

`harmonic_restraint_jet` retains
`k outer(grad_xi, grad_xi) + k (xi-s) Hessian_xi`. The second term is essential for
a nonlinear distance receiver. The moving-centre force port is `k grad_xi`; the
fixed-configuration Hessian change is `-k delta_s Hessian_xi`. Neither a moving
restraint centre nor a local chemical modification is automatically a rank-one
change to the complete physical response operator.

The existing retained-coordinate method gives a separate route when its nonlinear
active-coordinate and Gaussian-environment assumptions are justified. The new
`physical_remainder_bounds` can propagate a genuine globally bounded potential
oscillation and reference receiver RMS discrepancy. A local Taylor bound without
outside-domain probability and moment control does not meet that assumption.
The methods make no assertion of harmonic adequacy, canonical sampling, reaction
rates, activation barriers, turnover or oxygen specificity for Rubisco.

## Signed comparisons, propagation and stationary records

`propagation_accounting` accepts the actual full step `M`, reduced step `R`, lift
`L` and checkpoint states as vectors or column blocks. It accumulates inherited
and generated contributions in linear working memory. It neither stores a
quadratic trajectory history nor resets the reduced checkpoint. For BAOAB, the
domain must construct `R` from the projected Hessian; substituting `L.T @ M @ L`
would audit a different numerical operation. A common receiver and the original
actuator normalization are applied before taking a high-minus-low contrast.

`signed_contrast_account` evaluates the manuscript identity
`D = S - A`, preserving signed/complex inner products. It does not choose an
acceptance threshold or convert nested action/view/panel cells into independent
replicates. Original numerical masks, complete negative and unavailable outcomes,
and prospective versus exposed status remain programme-level commitments.

`finite_record_covariance` and `finite_record_variance` consume all covariance
lags through `N-1` for the actual declared stationary joint process. They preserve
paired cross-port signs. `finite_filter_variance` handles different component
record lengths or filters on a common sampling cadence. A resampling procedure
does not establish the underlying cross-covariance; a missing block is not filled
with zero unless the actual experimental construction warrants independence.
These identities concern estimator variance. Initialization bias, nonstationarity,
basin coverage, discretization and chemical-model error remain separate.

## Verification

Run the method controls through the selected base environment:

```sh
uv run --no-sync pytest -q tests/test_joint_response_methods.py
uv run --no-sync pytest -q tests/test_retained_gaussian_response.py
uv run --no-sync ruff check src/empirical_lawhood/methods/joint_response tests/test_joint_response_methods.py
```

The new controls use dense complex solves, direct matrix powers and exponentials,
independent scalar canonical quadrature, stationary vector AR(1) block covariance,
explicit atomic measures, exact rational certificate arithmetic, nonlinear finite
differences and declared refusal cases. They verify method arithmetic and software
contracts. They do not reproduce the historical experiment's complete original
custody, run a new scientific population, or establish molecular accuracy.
