# Calculate finite response with retained nonlinear coordinates

SPDX-License-Identifier: CC-BY-4.0

This guide describes finite equilibrium response after elimination of a quadratic environment.
It separates an exact model reduction, numerical integration and physical applicability.
Select a reference and retained coordinates, then evaluate the declared receiver and modification together.

## Prerequisites

Use the existing [locked main environment](../using/environments.md) with `uv run --no-sync`.
NumPy and SciPy are existing dependencies.
The [method module](../../src/empirical_lawhood/methods/retained_gaussian_response.py) performs no file I/O or native acquisition.
Its Python functions are a numerical component, without a registered experiment or execution authority.
The [Rubisco extension contract](../../programmes/biology/photosynthesis/workflows/rubisco-response/retained-gaussian-response.md) states the additional molecular work.

Supply a real, positive-definite reference operator, a full-column-rank retained map and a positive inverse thermal energy.
Keep coordinate, energy and temperature units consistent.
The reduced partition and requested moments must exist.
An arbitrary callable potential does not establish integrability.

The implementation uses an unconstrained Cartesian Gaussian reference on the full coordinate space.
A different physical domain or measure requires an explicit correction or integration extension.
In particular, a transverse tube bound does not justify truncating the Gaussian integral.
Keep native chemical states, periodic images and constraints with their supplying adapter.

## First action

This dimensionless control uses the two potentials from the finite-response derivation.
Both have the same minimum and Hessian at zero.
The second potential includes the finite term $x_2^4$.

```sh
uv run --no-sync python - <<'PY'
import numpy as np
from empirical_lawhood.methods import retained_gaussian_response as response

reduction = response.reduce_dense_reference(
    [[2., -1.], [-1., 2.]], [0., 0.], np.eye(2), beta=1.)
rule = response.gaussian_quadrature(
    reduction.reference, order=96, maximum_points=96**2)
wt = response.RetainedSamples(
    rule, np.zeros(len(rule.points)), rule.points[:, 0])
mutant = response.RetainedSamples(
    rule, rule.points[:, 1]**4, rule.points[:, 0])
wt_series = response.restrained_series(wt, [0., .5, 1.], 1.)
mutant_series = response.restrained_series(mutant, [0., .5, 1.], 1.)
result = response.paired_response(wt_series, mutant_series)
print("Endpoint contrast:", result.endpoint)
print("Three-center trapezoid:", result.finite_grid)
PY
```

The endpoint contrast is approximately `0.0195967797645805`.
The three-center value is approximately `0.0196015100174638`.
The different outputs retain their different mathematical targets.

## Output and stops

`BoltzmannIntegral` returns the log partition, normalized receiver moments and parameter-response calculations.
It keeps the partition in log form to avoid direct exponential underflow.
It separates the common energy zero before applying restraints or comparing endpoints.
Its `free_energy` is relative to the selected normalized Gaussian reference.
It omits that reference's bare partition constant.
Within each arm, that constant cancels from restraint-center endpoint differences.
Absolute free energies between different references need their separate normalization constants.

`RestrainedSeries` preserves every selected center, stiffness and arm reference.
`PairedResponse` returns both finite-grid and endpoint contrasts in the supplied energy unit.
Its two residual-error fields are separately selectable.
No error field establishes a physical residual enclosure, scientific admission or activation-rate connection.

Invalid dimensions, nonfinite inputs, dependent directions and nonpositive reference precisions refuse.
Missing energy or receiver values cannot remove quadrature points.
An excessive tensor rule refuses before allocation.
A failed native-energy callback propagates its failure.
Unsupported physical inputs remain the adapter's explicit unmet requirements.

## Exact reduction and physical lift

The equation numbers below preserve the supplied derivation's numbering.
Let $z=S^T x$ under a fixed Cartesian measure.
Elimination commutes with a finite modification that depends only on retained coordinates:

$$
\mathcal E_S[U+W\circ S^T]\,(z)=\mathcal E_SU(z)+W(z). \tag{1}
$$

A modification outside the retained description contributes a conditional free energy:

$$
\mathcal E_S[U+\delta U]\,(z)-\mathcal E_SU(z)
=-\beta^{-1}\log\mathbb E_{U(\cdot\mid z)}e^{-\beta\delta U}. \tag{2}
$$

The implemented exact model class is

$$
U_m(x)=\tfrac12(x-x_0)^TK(x-x_0)+V_m(S^Tx),\qquad K\succ0. \tag{3}
$$

All eliminated dependence is quadratic.
The retained potential can be nonlinear and can differ finitely between arms.
The reference reduction is

$$
G=S^TK^{-1}S,\quad z_0=S^Tx_0,\quad
Z_m=Z_G\mathbb E_{\mathcal N(z_0,\beta^{-1}G)}e^{-\beta V_m(Z)}. \tag{4--5}
$$

Thus the eliminated potential is $\tfrac12(z-z_0)^TG^{-1}(z-z_0)+V_m(z)$, up to a constant, as in equation 6.
`reduce_reference` requests one inverse action for each column of $S$.
`reduce_from_actions` accepts previously supplied actions.
Neither needs a full physical inverse or eigenspectrum.
`reduce_dense_reference` is the small-system control implementation.
Projected positivity alone does not authenticate a supplied inverse action.

`conditional_reference` implements the joint-block conditional Gaussian in equations 7–8.
Use `evaluate_boltzmann` on that conditional reference for equation 9's induced receiver potential.
Zero receiver–modification cross covariance gives independence under the Gaussian reference.
Separate retained potentials preserve that independence.
A nonlinear coupling between the two blocks can remove it.

`RetainedReduction.lift` and `lifted_potential` implement

$$
\bar x(z)=x_0+K^{-1}SG^{-1}(z-z_0), \tag{10}
$$

$$
V_m(z)=U_m(\bar x(z))-\tfrac12(\bar x(z)-x_0)^TK(\bar x(z)-x_0). \tag{11}
$$

The lift satisfies $S^T\bar x(z)=z$ and minimizes the reference energy on that fibre.
`residual` evaluates the definite omitted potential at one physical point:

$$
R_m(x)=U_m(x)-\tfrac12(x-x_0)^TK(x-x_0)-V_m(S^Tx). \tag{12}
$$

The exact class has zero residual.
General native potentials need separate residual control.
A successful energy evaluation at the lift supplies neither that control nor an equilibrium preparation.

## Finite composition and quadratic normalization

`compose_potentials` adds finite potential terms, as in equation 16.
`evaluate_boltzmann(extra_energy=...)` reuses existing samples for a supplied additional energy array.
Free-energy changes generally do not add.
`BoltzmannIntegral.parameter_response` evaluates equations 17–18 from columns of modification values:

$$
\partial_aF=\langle W_a\rangle,\qquad
\partial_a\partial_bF=-\beta\operatorname{Cov}(W_a,W_b),\qquad
\partial_a\langle\phi\rangle=-\beta\operatorname{Cov}(\phi,W_a).
$$

These formulas keep the coordinate map, measure and support fixed.
Changing those objects requires their additional terms.

Two normalization paths are available:

| Path | Entry point | Treatment |
| --- | --- | --- |
| Fixed reference, default | `restrained_series` | Retains $V$ and the complete restraint inside the integral. Reuses native energies across centers and strengths. Supports nonlinear receivers. |
| Absorbed affine restraint | `absorbed_linear_restraint_series` | Updates the Gaussian reference and includes its complete log normalization. Each center needs a new rule and energy evaluations. |
| General quadratic update | `quadratic_update`, then `evaluate_boltzmann(normalization=update)` | Absorbs $z^TDz/2-f^Tz+c$ and checks the evaluation uses the matching updated Gaussian. |

The update in equation 19 is

$$
G'=(G^{-1}+D)^{-1},\qquad z_0'=G'(G^{-1}z_0+f).
$$

The necessary partition factor is

$$
\log C=\tfrac12\log\frac{\det G'}{\det G}
+\tfrac\beta2\left[z_0'^T(G^{-1}+D)z_0'-z_0^TG^{-1}z_0\right]-\beta c.
$$

`QuadraticUpdate.log_normalization` retains this factor.
The updated precision must remain positive definite.
Passing the update to `evaluate_boltzmann` adds $\log C$ to the returned log partition.
Changing the Gaussian without this factor would change the free-energy calculation.
For sequential updates, retain every factor relative to the original reference.

For an affine receiver $a^Tz+b$, the absorbed restraint uses $D=kaa^T$, $f=k(s-b)a$ and $c=k(s-b)^2/2$.
An arbitrary nonlinear receiver cannot use this affine update.
Use the fixed-reference path instead.

`enlarge_reduction` implements equation 20.
It retains previous inverse actions and requests only the new direction.
An added dependent direction refuses before the inverse-action callback.

## Restrained receiver and paired targets

For any supplied scalar receiver $\phi$, the fixed-reference path evaluates

$$
J_m(s)=\mathbb E_{p_{G,m}}\exp[-\beta(V_m(Z)+k(\phi(Z)-s)^2/2)], \tag{34}
$$

$$
N_m(s)=\mathbb E_{p_{G,m}}\phi(Z)\exp[-\beta(V_m(Z)+k(\phi(Z)-s)^2/2)]. \tag{35}
$$

Normalized weighted moments give $N_m/J_m$ directly, without dividing underflowed partitions.
The signed receiver remains inside this expectation.
The outputs are

$$
g_m(s)=k(s-\langle\phi\rangle_{m,s}),\qquad
Q_k=k\sum_i\omega_i(\langle\phi\rangle_{W,s_i}-\langle\phi\rangle_{M,s_i}), \tag{36}
$$

$$
Q_{\mathrm{cont}}=-\beta^{-1}\log
\frac{J_M(s_b)J_W(s_a)}{J_M(s_a)J_W(s_b)}. \tag{37}
$$

`paired_response` defaults to ordered composite trapezoidal weights.
Explicit finite weights can also be supplied, including signed weights.
Both arms must share centers, temperature and stiffness.
The supplying adapter must also establish receiver correspondence and common units.
Each arm can use its own physical and retained dimensions.

`mean_force_derivatives` returns equation 38's values at each selected center:

$$
g'_m=k-\beta k^2\operatorname{Var}_{m,s}(\phi),\qquad
g''_m=-\beta^2k^3\kappa_{3,m,s}(\phi).
$$

`trapezoid_error_bound` applies equation 39 to supplied interval suprema of $|g''_M-g''_W|$.
A maximum over sampled centers does not establish an interval supremum.
This outer quadrature error is separate from the retained-space integration error.

## Residual-error applications

`ResidualEnvelope(lower, upper)` represents supplied uniform bounds on $R$ over the complete integration domain.
Its constructor checks numerical validity, not physical coverage.
Let $\delta_m=u_m-\ell_m$.
The endpoint application is

$$
|Q_{\mathrm{cont}}-\widetilde Q_{\mathrm{cont}}|
\le\delta_W+\delta_M. \tag{24}
$$

`endpoint_residual_error` evaluates this contribution.
Additive energy constants cancel.
This is not a direct bound on the finite-grid value.

The receiver application is

$$
|\langle\phi\rangle_{m,s}-\langle\phi\rangle_{\widetilde m,s}|
\le\sigma_{\widetilde m,s}\sinh(\beta\delta_m/2). \tag{25}
$$

`receiver_residual_error` evaluates this expression from a reduced variance or its supplied upper bound.
For the finite grid, the method propagates it as

$$
|Q_k-\widetilde Q_k|
\le k\sum_i|\omega_i|\left[
\sigma_{\widetilde W,s_i}\sinh(\beta\delta_W/2)
+\sigma_{\widetilde M,s_i}\sinh(\beta\delta_M/2)\right].
$$

Select the desired application explicitly:

```python
result = response.paired_response(
    wt_series, mutant_series,
    residual_application="both",
    residuals=(wt_envelope, mutant_envelope),
    receiver_variance_bounds=(wt_variance_bounds, mutant_variance_bounds),
)
```

The options are `none`, `endpoint`, `finite-grid` and `both`.
`none` is the default and retains absent error fields.
The variance-bound argument is optional for finite-grid calculations.
Without it, the result explicitly identifies quadrature variance estimates.
Supplied variance bounds retain their separate external-justification requirement.
An overflowing hyperbolic sine returns an infinite error contribution, rather than a finite admission.

`transverse_residual_envelope` implements equation 26's consequence within a supplied tube of radius $\rho$.
Uniform transverse force and curvature mismatch bounds $a,b$ give $|R|\le a\rho+b\rho^2/2$.
Omitted tails still need control.
Sampled residuals or sampled derivative maxima cannot establish these uniform bounds.

## Inverse-action and covariance error

`galerkin_compliance` implements equations 21–22 for an orthonormal basis $Q$:

$$
\widehat X=Q(Q^TKQ)^{-1}Q^TS,\quad E=S-K\widehat X,\quad
G-\widehat G=E^TK^{-1}E\preceq E^TE/m.
$$

Supply a justified $K\succeq mI$ with $m>0$.
A smallest Ritz value does not supply that global lower bound.
Inexact operator actions, loss of Galerkin orthogonality and arithmetic errors need their own accounts.
The function returns numerical matrix bounds conditional on those assumptions.
A singular lower matrix cannot enter the positive-definite Gaussian-density bound.

For $0\prec G_-\preceq G\preceq G_+$, equation 23 gives

$$
\sqrt{\det G_-/\det G_+}\,I(G_-)
\le I(G)\le
\sqrt{\det G_+/\det G_-}\,I(G_+).
$$

`covariance_log_integral_bounds` evaluates this relation in log space.
It requires equal means and temperatures and numerically ordered covariance parameters.
The potential and measure must also be the same in both integrals.
Supply a lower bound on $\log I(G_-)$ and an upper bound on $\log I(G_+)$.
Quadrature estimates produce an estimated conditional enclosure instead.
Changing the lift can change the potential and requires a separate discrepancy account.

All implemented enclosures use ordinary floating-point arithmetic.
Guaranteed numerical enclosures require independently controlled integrals, rounding, actions and physical bounds.
The method supplies no automatic certificate for those premises.

## History operands

`HarmonicBath` implements equations 27–32 for an orthogonal split of mass-weighted coordinates.
Its inputs are $K_{zz}$, $B$ and positive-definite $K_{qq}$.
The reduced equation retains the nonlinear force explicitly:

$$
\ddot z+K_{\mathrm{eff}}z+\nabla V(z)
+\int_0^t\Gamma(t-\tau)\dot z(\tau)\,d\tau=f_z+\eta(t). \tag{28}
$$

The component evaluates

$$
K_{\mathrm{eff}}=K_{zz}-BK_{qq}^{-1}B^T,\qquad
\Gamma(t)=BK_{qq}^{-1}\cos(K_{qq}^{1/2}t)B^T, \tag{29}
$$

$$
\eta(t)=-B\cos(\Omega t)(q_0+K_{qq}^{-1}B^Tz_0)
-B\Omega^{-1}\sin(\Omega t)\dot q_0,\qquad \Omega=K_{qq}^{1/2}, \tag{30}
$$

$$
D(p)=p^2I+K_{zz}-B(p^2I+K_{qq})^{-1}B^T. \tag{31}
$$

For linear retained dynamics, the displacement susceptibility is $D(p)^{-1}$ and the velocity admittance is $pD(p)^{-1}$.
Nonlinear $V$ remains an explicit force and cannot be replaced by these linear susceptibilities.
Conditional thermal preparation gives noise covariance $\beta^{-1}\Gamma(t-s)$.
Other preparations need their actual displacement and momentum contributions.
The two scalar baths $(B,K_{qq})=(1,1)$ and $(2,4)$ share static elimination but have kernels $\cos t$ and $\cos2t$.
The component supplies these operands, without a trajectory integrator or an irreversible-thermalisation claim.
An arbitrary molecular relative-coordinate map also needs its induced mass metric.

## Verification and cost

The [focused tests](../../tests/test_retained_gaussian_response.py) independently integrate the original two-dimensional quartic partition functions.
They also check a genuinely eliminated environment, conditional coupling, normalization, finite differences, residual formulas and full-system harmonic histories.
The nonlinear distance control preserves the shared-hydrogen covariance and permits different arm dimensions.
These are exposed analytical controls, with no biological units.

Select external test storage before execution:

```sh
uv run --no-sync pytest -q --fail-on-skip -p no:cacheprovider \
  tests/test_retained_gaussian_response.py \
  --basetemp /absolute/selected/external/checks/retained-response
```

The test has an explicit bounded contributor-CI declaration.
Its finite checks do not require a complete scientific study or full test profile.

The retained-space integral uses tensor Gauss-Hermite quadrature.
Compare selected orders and account for its numerical error independently.
The point limit bounds rule size, not native energy cost or the complete process memory.
Six inverse actions can each require many operator evaluations.
Additional nonlinear modification coordinates increase the integration dimension.

The complete cost account in equation 40 includes inverse/operator actions, retained native energies and residual control.
Charge failed evaluations and all preparation, assessment and fallback work.
Cached energy samples can avoid repeated evaluations across centers and stiffnesses.
Neither reduced dimension nor an analytical control establishes molecular savings.

## References and research

Zwanzig (1973), [Nonlinear generalized Langevin equations](https://courses.physics.ucsd.edu/2020/Fall/physics210b/Zwanzig1973_NonlinearGeneralizedLangevinEq.pdf), gives the harmonic-bath construction.
Its assumptions do not establish applicability to a reactive molecular model.

SciPy, [Gauss-Hermite quadrature](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.roots_hermitenorm.html), documents the Gaussian integration rule.
SciPy, [adaptive quadrature](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.integrate.quad.html), documents the independent control integrator and its estimated error.

The [restrained formation protocol](../../programmes/biology/photosynthesis/workflows/rubisco-response/restrained-formation-v1.md) owns the actual molecular receiver and downstream evidence limits.
