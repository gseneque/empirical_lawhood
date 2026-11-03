# Matrix dense response scoring and sampled duration

SPDX-License-Identifier: CC-BY-4.0

The shared numerical owner is
[`response_scoring.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_factor_response/response_scoring.py).
Scheduled, utility, training and prepared native scores use its exact response
norm and the amended dense record when their assay selects
`MatrixOriginResponseModel`. The complete programme still requires its issued
inputs, causal fitting graph and installed acceptance; these component
implementations do not establish scientific execution or qualification.

## Assay and error

The amended observation grid is `H = (16, 20, ..., 128)`, with 29 checks.
PRIMARY timestep is 0.001; FINE timestep is 0.0005 and its observation indices
are twice the PRIMARY indices. Each view retains all four actions, two panels,
and PLUS, MINUS and HOLD native branches. Nested actions, panels, views and
checks do not become independent population units.

The actual response is `C*(z_plus-z_minus)/2`. It is a finite odd response with
no division by amplitude. Keep the signed response, each signed branch relative
to HOLD, and the even response `(C*(z_plus-z_hold)+C*(z_minus-z_hold))/2` as
separate diagnostics. ZERO_RESPONSE predicts the zero vector in the same chart.
Its error is the response amplitude under the same task norm.

For a declared amplitude `a`, force norm `f`, pulse length in physical time
`p(t) = min(pulse_duration, t)`, and impulse `I(t) = a*f*p(t)`, score

```text
error(t) = max(L2(position_error)/(I(t)*(t-p(t)/2)),
               L2(momentum_error)/I(t))
```

There are exactly 24 position and 24 momentum receiver coordinates. There is
no division by receiver count, observed signal size, or fitted scale. The
shared canonical scalar arithmetic uses Decimal precision 60. Equality at
the headline tolerance 0.01 passes. The declared sensitivity tolerances are
0.005, 0.02 and 0.05.

Compute dense forecasts before native assay futures and score actual retained
arrays; do not interpolate three-point predictions or outcomes. Every saved
physically aligned post-step time supports a separate inter-check diagnostic.
Time zero has no normalized error because both nominal scales vanish. These
finite checks provide neither a continuum bound nor a guarantee over every
future path.

## Retained score and diagnostic records

The amended physical seal contains each method's predictions at every aligned
tick from 1 through 128. The 29 scored values are exact slices of those arrays.
The FINE prediction at aligned tick h uses native step 2h. These full-grid
predictions are made before native futures; retrospective interpolation cannot
create them.

Version 2 scheduled, utility, training and prepared score records hold 3,248
compact sampled cells: two views, two panels, four actions, seven methods and
29 horizons. Each cell retains its two block error norms and normalized error.
All signed native states, the original receiver map and model predictions
remain in their original archives, so every receiver error is reproducible.
The scalar cells avoid copying those 48-vectors separately for every method.

`MatrixDenseResponseDiagnostics` also retains:

* Fourteen full-grid worst-error curves, with each point's complete-menu flag.
  They report excursions between checks separately from the sampled duration K.
* Two causal FULL_COUPLED-minus-FACTOR curves using the same task norm.
* Sixty-four native amplitude curves: both views, panels, actions and the four
  ODD, PLUS_FROM_HOLD, MINUS_FROM_HOLD and EVEN_FROM_HOLD contrasts. At every
  aligned tick including zero they retain position/momentum norms, signed
  minima/maxima in the fixed receiver chart, complementary phase norms and
  separate native X/Y-sector position/momentum norms.
  The full signed components remain reproducible from the original arrays;
  extrema are descriptive chart summaries, not invariant component claims.

All normalized amplitude entries at time zero are absent. A nonfinite native
vector remains unknown. A failed independent native check makes targets
unusable while preserving the received diagnostic values and failure reason.
An unavailable instrument supplies no observed response, including for the
zero predictor.

The statistical target order is PRIMARY's 29 cumulative FACTOR log1p errors,
then FINE's 29. A missing earlier sampled value makes the cumulative target
unknown. Other methods and inter-check errors are diagnostics, not extra
training targets. The causal feature `d_lin` is log1p of the maximum
PRIMARY FULL_COUPLED-minus-FACTOR error over H and all four actions. The FINE
curve is diagnostic; neither native future arrays nor realized target errors
enter this feature calculation.
The [matched forecast specification](matrix-matched-forecast.md) defines its
mechanical-to-feature dependency, the signed norm-drift comparison, paired58
fitting and separate model calibration.

The amended E2 reducer consumes these same dense cells and curves. It retains
separate whole-root events for paired FACTOR adequacy through tick 32,
the three-challenger conjunction through tick 128, and paired ZERO_RESPONSE
adequacy through tick 32. Its two primary exact binomial tests use the complete
assigned roster, including authenticated missing roots, and alpha 1/160 each.
The null probabilities are respectively 4/5 and 1/2; for 96 roots the critical
success counts are 87 and 61. Unknown events count as nonsuccesses for these
tests and remain labelled unknown in the retained outcome census and descriptive
95% Clopper–Pearson completion envelopes. See the
[utility guide](../workflows/matrix-native-utility/guide.md) for public reads.

## Initial sampled pass count

Let `K` be the number of initial consecutive passing checks in H. It ranges
from 0 through 29: failure at the first check gives 0, and all 29 checks passing
gives 29. Later recovery does not erase an earlier failure. Only complete
follow-up with all checks passing is right-censored at the final sampled time.

Every check retains its observed maximum error or lower bound, menu completeness,
and native numerical usability. A partially observed menu can prove a failing
check if a known error exceeds the tolerance. It cannot prove a pass merely
because the observed errors are small. Unusable native arithmetic does not
establish physical failure. Missing origins and missing follow-up remain unknown.

The feasible interval for K has lower endpoint equal to the initial definitely
passing prefix and upper endpoint equal to the index of the first known failing
check, or 29 if no failure is known. A single K is reported only when these
endpoints coincide. Examples:

| Sampled observations | Feasible K | Complete right censoring |
| --- | --- | --- |
| All 29 pass, including equality | 29 | Yes |
| Four pass, then a known failure | 4 | No |
| Two pass, one unknown, one pass, then failure | 2 through 4 | No |
| 28 pass, last check unknown | 28 through 29 | No |
| All checks unknown | 0 through 29 | No |

A cumulative maximum becomes unknown after any missing value unless only a
lower bound is being reported explicitly. Keeping a known later failure is
compatible with an unknown earlier crossing time.

The prospective forecasting primary uses normalized RMS log1p curve error over
both views and all 29 horizons. See the [matched forecast specification](matrix-matched-forecast.md)
for its exact definition and 0.1 margin. E4 averages nine coordinate losses
equally before population inference. Views and coordinates remain nested.
Missing required comparisons are nonwins with their unknown states retained.
The original mean absolute paired K error and 1/29 improvement remain secondary.
Original issued K-primary records retain their original claim.

## Frozen E4 relation

The amended relation uses DEV16, CAL20 and CONF32 disjoint independent groups.
DEV assigns four groups to each preparation family. CAL/CONF select each
group's family uniformly from the four-family menu, using one separately
committed two-bit draw. The realised counts remain unchanged, including zero
counts; there is no balancing or replacement. The construction and its replay
do not authenticate the scientific sampling premise.

SR and BR retain the same shared causal base, including PRIMARY origin-only
`d_lin` and the two fixed past-Hessian descriptors. SR adds the four original structural descriptors; BR adds the four
causal norm drifts. Replace duplicated physical inputs with
`x_j = log2(j/j0)`, their three pair products, and
`q_agg = (x_T^2 + x_gamma^2 + x_c^2)/3`. Use three fixed family indicators.
Each primary account has 28 features. The joint centre and eight corners
identify aggregate curvature, not separate pure quadratic effects. The same
fixed equations apply to a single off-grid case without counterfactual cases.

Both accounts use the common complete DEV groups: at least 12 of 16, at least
two per family, and at least one per family in each of two preassigned folds.
Fit fold-local centring/scaling, an unpenalised intercept, penalties 1 and 10,
and lower-penalty ties under the declared continuous-curve loss. Equal group weights and equal
weights for each group's nine coordinates give each group one fitting unit.
There are at most five paired58 fit bundles per fitted arm, including the
final refit. Physical-only, shared-relation-base and raw DEV median controls
remain secondary. No control can replace SR/BR after observing outcomes.

CAL seals the fixed nonnegative cumulative log point curves before targets.
For each model separately, each group scores the maximum positive residual
over all nine coordinates and 58 targets. A missing required prediction,
target or numerically usable paired comparison scores infinity. At alpha 0.05,
CAL20 uses rank 20; one infinite group score therefore makes the radius
infinite. CONF seals the same points plus the original model-specific upper
curves before its futures. SR owns admission; the smaller or more permissive
bound never selects an account. Infinite bounds produce no admissions, and
unavailable bounds remain distinct from finite and vacuous bounds.

CONF averages each model's nine normalized 58-target curve losses equally.
A win requires BR minus SR of at least 0.1, with common usable predictions,
under the [matched forecast amendment](matrix-matched-forecast.md).
The K-loss comparison remains secondary. The assigned-group exact one-sided
test uses null probability 1/2 and alpha 1/160; 24 of 32 successes are required.
Unknown comparisons remain in all 32 assigned groups and in the separate
descriptive event-completion interval. Main effects, pair contrasts, aggregate
curvature and the three-way diagnostic remain descriptive with no Holm family.
Reports retain both model coverages, continuous losses, absolute loss summaries,
unchanged E3 references and realised family counts. A relative win alone
establishes neither mean benefit nor service or causal mediation.

Eligible DEV freezes SR/BR before separate CAL and CONF. CONF never nominates
the account. The downstream package retains the original coefficients,
transforms and CAL radii after adverse CONF or infinite bounds. An
unconstructible required model is a prerequisite failure with no E3 fallback.
The [matched lifecycle controls](../../../../tests/test_matrix_e4_matched_lifecycle.py)
exercise these scientific records using disclosed software premises; they do
not constitute installed workflow acceptance, fresh acquisition or qualification.

## E2 event arithmetic

Adequacy through tick 32 requires every sampled check through 32 to pass in
both numerically usable views. The three-challenger structural event uses
cumulative errors through 128: FACTOR must improve strictly by more than 0.001
against each of GENERIC_SLOW, SPECTRA and IO48 in both views. For every selected
description, PRIMARY/FINE error disagreement must be at most 0.0001. This is
one conjunction event. FULL_COUPLED remains an accuracy benchmark, and
NORM_RADIUS and ZERO_RESPONSE remain reported comparisons.

Unavailable challengers or numerical disagreement leave the common comparison
unresolved. In the assigned-root operational count, only an established success
counts as success; missing outcomes remain distinct from observed losses in the
report. Population thresholds and the complete assigned denominator belong to
the issued programme's inference contract.

The exposed controls in
[`test_matrix_dense_response_scoring.py`](../../../../tests/test_matrix_dense_response_scoring.py)
use hand-calculated actuator scales, a 3–4–5 receiver norm, explicit signed/even
responses, every possible first failing check, incomplete menus, view mismatch,
unknown follow-up, zero signal, and strict conjunction boundaries. They also
exercise the dense E4 reader. They establish component behavior, not new
scientific outcomes or qualification.
The [dense measurement controls](../../../../tests/test_matrix_dense_response_measurements.py)
independently contract retained native states with the HS receiver chart and
test an inter-check excursion that leaves all primary sampled checks passing.
The [forecast controls](../../../../tests/test_matrix_scheduled_response_forecast.py)
also reproduce a complete seven-method native score with all 48 transition
controls, all 58 targets and solvers disabled during cold replay.
