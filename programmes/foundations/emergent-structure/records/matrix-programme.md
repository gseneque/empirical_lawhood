# Matrix E1–E6 scientific contract

SPDX-License-Identifier: CC-BY-4.0

The [researcher programme](../workflows/matrix-programme/guide.md) tests
whether a measured approximate matrix factor predicts and supports an accurate
finite response reduction in the declared classical stochastic simulator.
This specification, the linked numerical contracts and the exact selected D/C
records stand independently of local development plans. Software conformance,
completed observations and scientific qualification are separate claims.

The current `MatrixProgrammeScientificDesign` has version 3. It binds the
actual native coordinates, scalar/factor definitions, numerical guards, assay
templates, matched forecast choices, calibration rules and prepared recipes.
C version 2 adds the original allocation, exposure exclusions, future streams,
the E4 history/future/family-draw recipe, source
provenance and exact support bytes. Later fits and calibrations have their own
immutable producing parents. Neither D nor C contains fictional fitted values
or confers execution or outcome access. The generated
[complete example](../workflows/matrix-programme/scientific-design.example.json)
has exposed deterministic streams and a deliberately unusable zero template;
it demonstrates the input contract only.

## Native model and preparation

Use q=2, n=q²=4 and six Hermitian position matrices, three X and three Y, with
six corresponding momenta. Coordinates use the real Hilbert–Schmidt inner
product `Re Tr(A†B)`. Each matrix retains its trace component. There are 96
real position and 96 real momentum dimensions. Native arithmetic uses
complex128 arrays and float64 scalar operations; canonical inputs retain their
original Decimal spellings.

Let Z be either triplet, `R_Z = sum_a Z_a²`,
`alpha_Z = alpha_tilde_Z/q`, `c2=(q²-1)/4`,
`mu(M)=2*(4*c2*M-1)/9`, and `beta_Z=-alpha_Z²*mu(M_Z)`.
The potential implemented by
[`gradients.py`](../../../../src/empirical_lawhood/adapters/simulators/six_matrix_response/gradients.py) is

```text
V = n * sum_(Z=X,Y) Tr(
      -1/4 * sum_(a,b) [Z_a,Z_b]^2
      + (2*i*alpha_Z/3) * sum_(a,b,c) epsilon_abc Z_a Z_b Z_c
      + beta_Z R_Z + M_Z R_Z^2)
    - n*c/2 * sum_(a,b) Tr([X_a,Y_b]^2).
```

All summations run over the three component indices. The potential parameters
are `M_X=M_Y=0.5` and cross-sector coefficient c. Kinetic energy is
`sum Tr(P_a²)/2`, so velocity is momentum and kinetic mass is one. The potential
parameters named `mass_x` and `mass_y` do not rescale kinetic drift or bath noise.
The force is the negative real-HS gradient of this potential, plus the selected
assay force when applied. Beta changes with the scheduled alpha; it is not a
separately fixed coefficient.

The nominal de-anneal coordinate has bath temperature T=1, friction gamma=1,
c=1, decreasing start 8, and exact canonical target values
`alpha_tilde_X=0.6666666666666666666666666667` and
`alpha_tilde_Y=7.333333333333333333333333334`. Preserve these Decimal values;
the labels 2/3 and 22/3 are explanatory, not alternate canonical operands.
With s=clip(t/0.256,0,1), the four preparation schedules are:

| Family | X coupling | Y coupling | Initial positions |
| --- | --- | --- | --- |
| Joint increasing | target_X*s | target_Y*s | All zero |
| Joint decreasing | 8+(target_X-8)*s | 8+(target_Y-8)*s | Product background at alpha_tilde_X=alpha_tilde_Y=8 |
| X first | target_X*min(2*s,1) | target_Y*max(2*s-1,0) | All zero |
| Y first | target_X*max(2*s-1,0) | target_Y*min(2*s,1) | All zero |

All initial momenta are zero. The product background is
`X_a=(2*alpha_X/3)*(J_a tensor I2)` and
`Y_a=(2*alpha_Y/3)*(I2 tensor J_a)`, with `J_a=sigma_a/2`.
These starts are deterministic; they are not equilibrium draws from every
temperature. T, gamma and c have their selected values throughout preparation
and assay. Scheduled alpha is evaluated at each kick's physical time and is
held at its target after the ramp. Prepared E5 arms use their separate fixed
recipes before handoff and restore the selected nominal couplings for assay.
Their exact half-tick values and effort are bound in D.

E1 retains 1,152 PRIMARY ticks; E4 retains 1,024-tick structural histories.
The response handoff is at tick 256. The 32-tick causal feature window precedes
that handoff. Future responses run for 128 PRIMARY ticks. The paired timesteps
are exactly 0.001 and 0.0005; two FINE steps correspond to one PRIMARY step.

## Bath, BAOAB and nested noise

For h, `rho=exp(-gamma*h)` and independent unit covariance Hermitian Gaussian
innovation xi, the native step is

```text
pB = p - h*grad(V_current,q)/2 + h*f_current/2
qA = q + h*pB/2
pO = rho*pB + sqrt(T*(1-rho^2))*xi
q' = qA + h*pO/2
p' = pO - h*grad(V_next,q')/2 + h*f_next/2.
```

The pulse force enters both kicks of each selected pulse step. Hermitian
roundoff projection is applied at the native stages. Diagonal noise entries are
independent N(0,1); upper-triangular real and imaginary components each have
variance 1/2, with conjugate lower entries. This gives covariance I in the
real-HS orthonormal coordinates, including the trace. The conditional OU mean
is rho*p and covariance `T*(1-rho²)*I`; the stationary momentum covariance of
the isolated OU update is T*I. No claim of equilibrium position sampling
follows from that identity.

For a coarse innovation xi, independent bridge eta and
`a=exp(-gamma*h/2)`, use

```text
xi1 = (a*xi + eta)/sqrt(1+a^2)
xi2 = (xi - a*eta)/sqrt(1+a^2).
```

This orthogonal transformation preserves independent standard Gaussian halves
and `a*xi1+xi2=sqrt(1+a²)*xi`. Composing the two OU momentum updates therefore
recovers the coarse OU innovation at the actual gamma and T. It does not make
the complete nonlinear coarse and fine BAOAB trajectories identical.
The implementation owners are
[`parameter_history.py`](../../../../src/empirical_lawhood/adapters/simulators/six_matrix_response/parameter_history.py),
[`shooting.py`](../../../../src/empirical_lawhood/adapters/simulators/six_matrix_response/shooting.py)
and [`simulation.py`](../../../../src/empirical_lawhood/adapters/simulators/six_matrix_response/simulation.py).

Original root-purpose PCG64DXSM streams and independent future streams are
committed before use. Roots are disjoint across banks. Nine E4 coordinates
share their group's declared starts and standardized streams while using each
coordinate's own OU parameters. E5 arms share their original group streams.
Within an assay panel, all four actions and +/HOLD/- branches use the same
future innovations; the two declared panels remain separate. Coarse and fine
views are coupled by the bridge above. Coordinates, arms, panels, signs,
receivers and time samples are nested observations, never extra independent
units. E5 gain/harm probabilities refer to this declared coupling.

## Factor, instrument and forecasts

For each sector triplet, form the positive double-commutator Gram matrix
`L_ij=sum_a Re Tr([Z_a,E_i]†[Z_a,E_j])` in the fixed 15-dimensional traceless
Hermitian HS basis. Select the projector onto its three lowest eigenvectors.
Identification requires `lambda4-lambda3 > 1e-10*lambda_max` and
`lambda4 > 1e-20`. The identity direction is then added for the four-dimensional
complex algebra. The operator's eigenvalues are passive matrix diagnostics,
not decay rates of the native stochastic generator.

For orthonormal slow matrices F_i, associative leakage is the sum of squared
residuals of every F_i F_j after complex-HS projection onto
`span_C{I/2,F_1,F_2,F_3}`, divided by the sum of squared product norms.
Lie leakage is the maximum relative squared residual of each cyclic
`-i[F_i,F_j]` after projection onto the three slow directions. Denominators
use the numerical floor 1e-30. Complex coefficients are retained in associative
projection. Lie closure alone does not establish an associative factor.

The existing constructor fits a multiplicity-two Pauli frame from the slow
triplet using its third matrix's eigenspaces and the first matrix's polar map;
it does not optimize over factors. Raw admission requires both leakages <=0.05
and maximum principal factor-fit angle <=15 degrees. Sample every 16 PRIMARY
ticks, require 32 ticks of trailing admission and adjacent projector angle
<=15 degrees, and use origin-fixed angle <=30 degrees for that survival view.
Frame alignment uses the adjacent past only, an orientation-preserving
Procrustes map and minimum singular overlap 0.5. Ambiguous orientation remains
distinct from projector identification. E1's special time-zero admission and
unknown first origins follow the [occurrence contract](matrix-e1-occurrence.md).
The independent scalar diagnostic uses its original normalization source and
threshold 0.3; it does not replace algebra admission.

The response instrument uses the admitted PRIMARY-Y frame and I/2. Template
coefficients construct the 48 receivers, with 24 position and 24 momentum
coordinates. FACTOR force uses the three frame directions; GENERIC uses its
frozen generic triplet; COMPLEMENT projects that triplet out of the factor
algebra and orthonormalizes it; TRACE uses I/2. Each force is normalized to its
declared HS norm one. Pulse amplitude is 0.01 for 16 PRIMARY ticks. The actual
template archive and every member digest are input operands; substituted
charts or unresolved complements refuse or retain explicit nonuse.

The nominal declared numerical guards are: factor operator, eigenpair,
orthogonality, projector, factor and scalar checks 1e-9; complement Gram,
generic-mode gap, native spectral gap and radial norm minima 1e-10; receiver
Gram tolerance 1e-12; Hessian difference step and reference tolerance 1e-5;
native reference tolerance 1e-8; weak-response diagnostic threshold 1e-12.
The actual canonical numerical and assay records supply these operands at
every consumer. IO48's additional guards are listed in its origin contract.

Each prepared arm constructs its own frame, Hessian, forces, receivers and
scales at its own handoff. Frozen construction rules and equal effort do not
make these identical physical tasks. The retained contrast is
`C*(z_plus-z_minus)/2`, with no amplitude division. The
[dense scoring contract](matrix-dense-response.md) specifies the norm, 29
checks, sampled duration K, inter-check diagnostics and missingness. The
[origin contract](matrix-origin-response.md) specifies all seven mechanical
descriptions, including IO48, their dimensions, numerical witnesses and cold
replay. The [matched forecast contract](matrix-matched-forecast.md) specifies
causal d_lin, exact feature ordering, fitting, calibration, SR/BR, E5 and E6.
No future HOLD state, realized error or native tangent can enter a forecast.

## Exact grid, allocations and primary family

The native E4 tuples are absolute `(T,gamma,c)` values. Their nominal reference
is `(1,1,1)`, so the dimensionless ratios have the same displayed values.
All nine coordinates are retained within each independent group.

| Coordinate | T | gamma | c |
| --- | ---: | ---: | ---: |
| Low/low/low | 0.5 | 0.5 | 0.5 |
| Low/low/high | 0.5 | 0.5 | 2 |
| Low/high/low | 0.5 | 2 | 0.5 |
| Low/high/high | 0.5 | 2 | 2 |
| High/low/low | 2 | 0.5 | 0.5 |
| High/low/high | 2 | 0.5 | 2 |
| High/high/low | 2 | 2 | 0.5 |
| High/high/high | 2 | 2 | 2 |
| Center | 1 | 1 | 1 |

The log2 inputs are -1/0/1. T=1.125 lies inside the E4 temperature interval
and T=3.25 outside it; both preserve nominal friction, cross coupling and the
de-anneal family. Transfer does not cover a new family, matrix size or friction
axis. E4 DEV has four groups per family. CAL/CONF use a separately committed
uniform family draw per group and retain the realized counts without redrawing.

| Phase | Independent groups | Native cases |
| --- | ---: | ---: |
| E1, 96 per family | 384 | 384 |
| E2 | 96 | 96 |
| TRAIN | 64 | 64 |
| E3 CAL | 64 | 64 |
| E3 CONF | 80 | 80 |
| E4 DEV | 16 | 144 |
| E4 CAL | 20 | 180 |
| E4 CONF | 32 | 288 |
| E5 DEV | 16 | 48 |
| E5 CONF, if nominated | 80 | 160 |
| E6 nearby | 64 | 64 |
| E6 shifted | 64 | 64 |
| Maximum | 980 | 1,636 |

The primary family contains eight slots at alpha=1/160 each. Unused slots
remain unused. Calibration alpha 0.05 is separate.

| Slot | Question | Exact critical count |
| --- | --- | --- |
| E1 map | Eight PRIMARY-Y occurrence/joint-survival intervals | Cell noncoverage 1/1280, each tail 1/2560 |
| E2 adequacy | Paired FACTOR adequacy through 32, p>0.8 | 87/96 |
| E2 structure | Joint strict advantage over GENERIC_SLOW, SPECTRA and IO48, p>0.5 | 61/96 |
| E3 forecast | S0 versus B0 continuous-curve win, p>0.5 | 52/80 |
| E4 relation | SR versus BR whole-group continuous-curve win, p>0.5 | 24/32 |
| E5 preparation | Paired gain/harm tail and practical net gain >=0.10 | Eight gains/zero harms pass; seven do not |
| E6 nearby | Frozen SR versus BR continuous-curve win, p>0.5 | 43/64 |
| E6 shifted | Frozen SR versus BR continuous-curve win, p>0.5 | 43/64 |

Binomial tails use every assigned independent unit, with ties and unresolved
comparisons counted as operational nonsuccesses. Their true-event descriptive
intervals still retain unknown completions. Prediction wins require normalized
curve-RMS improvement >=0.1 and common usable predictions. E4 averages its nine
coordinate losses equally. The [matched forecast specification](matrix-matched-forecast.md)
defines the new loss, shared past-Hessian features and signed mechanism readout.
Original K-primary records retain their meaning. K and one-check comparisons
remain secondary under the prospective amendment. E5 uses its paired exact
discordance test and conservative completion, not an independent-success test.
Sampling independence, the target population and frozen procedures remain
substantive premises, not consequences of labels or disjoint pseudo-random
streams. A negative superiority test is not equivalence, and a relative win
need not give useful absolute accuracy or conditional admission reliability.

Under independent complete Bernoulli outcomes, the exact planning powers at a
70% win probability are 86.33% for E3, 93.01% for the 96-root structural test,
34.40% for E4 and 73.83% for each E6 regime. E4 has 82.54% power at an 80% win
probability. The 96-root adequacy test has 97.81% power at true adequacy 95%,
and 50.48% at 90%. Complete-pair E5 powers at gain/harm probabilities
0.30/0.05, 0.20/0.05, 0.15/0.05 and 0.20/0.10 are respectively 92.03%,
51.89%, 21.97% and 13.92%. These are probability-law calculations, not observed
Matrix power. The new curve event does not inherit an old K effect size or
an expected power from E2. Missingness, unavailable fitted models and nonnomination can
reduce programme-level success. No negative result authorizes a top-up.

## Costs, reproduction and literature boundary

The public read reopens original receipts and data, reproduces numerical
checks and reductions, and preserves complete missing/adverse denominators.
The [product export](../workflows/matrix-programme/guide.md#deliver-the-retained-scientific-products)
retains the complete report and exact references to original native custody.
Report measured setup, factor, Hessian, IO48, reduced propagation, forecasting,
calibration, reader, memory and storage costs separately. A phase dimension
reduction does not prove a speed benefit. For native cost C_n, reduced cost C_r
and additional setup C_s, amortization requires C_n>C_r and more than
`C_s/(C_n-C_r)` repeated queries.

Algebra-based reduction has close antecedents. Grigoletto, Tao, Ticozzi and
Viola construct exact reduced quantum models from operator spaces and algebras,
retaining Lindblad structure in their setting:
[Exact Model Reduction for Continuous-Time Open Quantum Dynamics](https://arxiv.org/abs/2412.05102v3),
Quantum 9, 1814 (2025). Grigoletto, Sarlette, Ticozzi and Viola study approximate
algebraic and adiabatic reductions with quantum positivity constraints and
finite-time error bounds:
[Approximate Reduced Lindblad Dynamics via Algebraic and Adiabatic Methods](https://arxiv.org/html/2603.11982v2)
(2026). Those results concern quantum Markovian generators. This programme
measures approximate factor structure and finite responses in a classical
Langevin medium; it cannot import their guarantees or claim priority from the
absence of an identical experiment in a targeted search.

Leimkuhler and Matthews analyze configurational sampling accuracy of Langevin
integrators in
[Rational Construction of Stochastic Numerical Methods for Molecular Sampling](https://arxiv.org/abs/1203.5428v2)
(2013). That sampling analysis does not establish this programme's finite-time
response or first-exit accuracy. The retained native derivative, OU bridge,
harmonic and conjugation controls address those software boundaries separately.
No result here establishes Rubisco catalysis, superconductivity, a continuum
limit, or an autonomous physical subsystem.
