# Matrix origin response mechanics and IO48

SPDX-License-Identifier: CC-BY-4.0

This is the numerical construction contract for the amended Matrix response
assay. Its implementation is in
[`origin_mechanics.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_factor_response/origin_mechanics.py)
and the native instrument boundary is `origin_io_system` in
[`science.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_factor_response/science.py).
The construction and exposed numerical controls alone do not establish a
completed public programme, an issued scientific source, or fresh evidence.
The [programme guide](../workflows/matrix-programme/guide.md) owns the
public lifecycle and its actual input and authority prerequisites.

`MatrixOriginResponseModel` selects exactly FACTOR, FULL_COUPLED, GENERIC_SLOW,
IO48, NORM_RADIUS, SPECTRA and ZERO_RESPONSE. It includes the complete IO48
construction and has zero fitted parameters. The scheduled assay requires all
29 horizons, the paired 0.001/0.0005 clock and the fixed pulse for this model.
Scheduled, training, utility and prepared forecast records bind that selected
menu. Closed five-method model records retain their separate identity; they
cannot stand in for the amended scientific design.

The prepared forecast uses the shared scheduled numerical calculation after
checking its own source, cutoff, restored couplings and actual PRIMARY frame.
Each arm still constructs its own state-conditioned force and receiver maps.
ZERO_RESPONSE predicts a zero receiver vector only for an available fixed
instrument. Without an admitted origin or resolved instrument, all seven
predictions are unknown, including ZERO_RESPONSE.

## Native coordinates, clock and instrument

The state consists of 96 real Hilbert–Schmidt coordinates for the six Hermitian
4-by-4 position matrices and 96 corresponding momentum coordinates, in that
order. The existing native Hermitian basis includes every trace direction.
There is no trace projection before balancing. Native position drift uses
momentum directly. The parameters called mass in the native potential do not
introduce an additional inverse kinetic mass.

The input columns are the four original force directions multiplied by their
amplitude 0.01. Each direction retains its declared force norm. A unit input
on one column selects that action; it does not multiply by the amplitude again.
The pulse lasts 0.016: 16 PRIMARY steps of 0.001 or 32 FINE steps of 0.0005.
The terminal physical horizon is 0.128: 128 or 256 steps, respectively.
All four actions have the same declared force norm. The 48 output rows retain
the original orthonormal chart: 24 position receivers followed by 24 momentum
receivers. Different prepared arms can have different origin instruments.

The predicted response is the finite odd contrast
`C_native (z_plus - z_minus) / 2`, starting from zero displacement. There is
no division by pulse amplitude. The frozen Hessian is evaluated at the actual
origin. It remains constant during this mechanical forecast, including when
the native future follows a changing schedule. FULL_COUPLED is this origin
linearisation, not the nonlinear native future or a trajectory tangent.

For timestep `h`, OU decay `rho = exp(-gamma*h)`, Hessian `H`, and input force
matrix `F` including amplitude, set `b = h/2` and `a = b*(1+rho)`. The exact
discrete map has blocks

```text
Aqq = I - a*b*H             Aqp = a*I
Apq = -b*(rho*H + H*Aqq)    App = rho*I - b*H*Aqp
Bq  = a*b*F                Bp  = a*F - b*H*Bq
```

These are the kick/drift/OU/drift/kick equations with the applied force in
both kicks. Common innovations cancel in the frozen linear odd response.
The response recursion is `delta_z[n+1] = A0*delta_z[n] + B*u[n]`, with
`delta_z[0] = 0`; a pulse selects its column for steps 1 through its declared
pulse length. There is no direct feedthrough term or time-zero response sample.

## Fixed scaling for balancing

Let `p = 0.016`, `t_final = 0.128`, and `I_final = amplitude*force_norm*p`.
The physical state units are

```text
s_q = I_final * (t_final - p/2)
s_p = I_final
S   = diag(s_q*I96, s_p*I96)
D   = diag(s_q*I24, s_p*I24)
```

Use `z_scaled = inverse(S)*delta_z`, so the balancing system is
`A = inverse(S)*A0*S`, `B_scaled = inverse(S)*B`, and
`C = inverse(D)*C_native*S`. All state and output norms in the reduction and
projector diagnostics refer to these coordinates. Raw output predictions are
recovered by multiplying by `D`.

This fixed quadratic balancing metric does not replace the scored response
error. At each scored physical time `t`, use that time's own pulse duration
`p(t)`, impulse `I(t)`, and the maximum of the two block L2 errors divided by
`I(t)*(t-p(t)/2)` and `I(t)`, respectively.

## Finite-horizon balanced reduction

For `N = 128` PRIMARY or `N = 256` FINE, construct

```text
Wc = sum(k=0..N-1) A^k * B_scaled * B_scaled.T * (A.T)^k
Wo = sum(k=0..N-1) (A.T)^k * C.T * C * A^k
```

Inputs are `u[0]` through `u[N-1]`; outputs are the post-step samples 1 through
N. An impulse `u[0]` gives `C*B_scaled` at sample 1 and
`C*A^(N-1)*B_scaled` at sample N. The zero-power term and terminal sample are
both included. Finite sums exist for unstable linear systems; this construction
does not promise reduced stability or nonlinear response accuracy.

`MatrixIO48Construction` binds these fixed choices:

| Choice | Value |
| --- | --- |
| Maximum retained phase dimension | 48 |
| Gramian eigenvalue threshold | Strictly greater than `1e-14 * largest_eigenvalue` |
| Hankel singular-value threshold | Strictly greater than `max(1e-12, 1e-10 * largest_singular_value)` |
| Witness residual tolerance | `1e-8 * max(1, Frobenius_norm(reference))` |
| Required gap when truncating at dimension 48 | Strictly greater than `1e-8 * largest_singular_value` |
| Maximum projection conditioning bound | `1e8` |

All values are canonical Decimals in the issued construction. Operators do
not retune them after outcomes. Negative Gramian eigenvalues within the residual
tolerance are discarded; a larger negative eigenvalue is numerical nonuse.
The complete ordered eigenpairs remain retained, including discarded values.

Form `Rc` and `Ro` from the resolved eigenvectors times square roots of their
eigenvalues. From `Ro.T*Rc = U*diag(sigma)*V.T`, retain the first `r` singular
directions, where `r` is the smaller of 48 and the resolved numerical rank.
The lifting and restriction maps are

```text
T = Rc * V_r * diag(1/sqrt(sigma_r))
L = diag(1/sqrt(sigma_r)) * U_r.T * Ro.T
Ar = L*A*T       Br = L*B_scaled       Cr = C*T
```

Check `L*T = I_r`. The conditioning bound is
`Frobenius_norm(T) * Frobenius_norm(L)`, an explicit conservative bound for the
oblique projection. A degenerate dimension-48 cutoff, excessive conditioning,
decomposition failure, or nonfinite arithmetic produces numerical nonuse.
There is no replacement predictor selected from outcomes. A resolved lower
rank is reported explicitly. Rank zero is a valid empty reachable/observable
realisation and predicts zero; it is not a claim that the native future is zero.

The reduced model uses the same pulse and output units. It is a general
phase-space reduction, not a 24-position-mode Hessian truncation. Its reported
dimension can be below 48, so comparison with FACTOR is capacity capped.

## Retained witnesses and independent replay

Retain both Gramians, their full eigenpairs, the full thin SVD of `Ro.T*Rc`,
the lifting/restriction maps, and the three reduced maps. Report reachable,
observable, balanced and effective ranks and the projection conditioning bound.
The actual source, frozen Hessian, force/receiver maps, clock, scaling,
construction identity and array digest belong to the enclosing forecast seal.

Cold replay verifies the Gramians by independent Stein recurrences, beginning
at zero and taking N steps:

```text
X_next = B_scaled*B_scaled.T + A*X*A.T
Y_next = C.T*C + A.T*Y*A
```

It checks eigenpair and SVD reconstruction, ordered values, orthogonality,
threshold decisions and biorthogonality without eigensolving or refitting.
Projection and reduced-map arithmetic must reproduce the retained arrays
exactly under the selected numerical environment. Caller-owned source and
artifact authentication remains necessary; numerical agreement creates no
access or scientific authority.

Numerical nonuse retains the complete witnesses available at the failed stage
and a fixed failure code. Cold replay verifies preceding stages and reproduces
a degenerate cutoff, excessive projection conditioning, failed biorthogonality
or nonfinite arithmetic without a new decomposition. It refuses a thinned
successful witness census or a failure contradicted by the retained witnesses.
A solver-reported failure has no independent mathematical failure certificate:
the reader authenticates that reported nonuse from the original custody and
verifies earlier witnesses, without retrying the solver or inventing a result.
Successful reductions retain their four ranks and conditioning bound in the
forecast archive. No failure selects another predictor as IO48.

For a factor phase basis `U_factor`, use `P=U_factor*U_factor.T`, `Q=I-P` in
the same scaled metric. Retain Frobenius norms of `Q*A*P`, `P*A*Q`, and
`P*A*Q*(Q*A*Q)^k*Q*A*P` for `k=0..N-1`. These memory curves are computed with
the low-rank factor basis. Store scalar curves and origin witnesses, rather
than one 192-by-192 matrix at every time. No realised future tangent enters
these origin diagnostics.
The same archive retains the Frobenius norms of the scaled phase-map blocks
from Y to X and from X to Y. Each sector includes its 48 position and 48
momentum coordinates. Native amplitude diagnostics report the corresponding
two sectors separately; these norms do not assert causal mediation or exclude
error cancellation.

The exposed controls in
[`test_matrix_origin_mechanics.py`](../../../../tests/test_matrix_origin_mechanics.py)
cover literal BAOAB stages, a free-particle impulse, both finite-horizon
endpoints, unstable systems, the full-rank response limit, rank zero, the
dimension cap, conditioning nonuse, altered witnesses, basis rotation and the
native trace-containing instrument in both views. These are software and
mathematical controls, not scientific qualification evidence.
