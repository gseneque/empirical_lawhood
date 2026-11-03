# Matrix matched response forecasts

SPDX-License-Identifier: CC-BY-4.0

The configured protected E3 and native TRAIN owners support the explicit
`MATCHED_FACTOR58` measurement contract. This document specifies its causal
features, fitting, calibration and confirmation reductions. Its component
controls establish software behaviour. A complete installed programme, genuine
source and authority records, and scientific qualification remain separate
requirements. The later E4 relation account must retain its own DEV fit and
CAL bounds; an E3 export does not establish transport coverage.

The [dense response specification](matrix-dense-response.md) defines the native
assay, error norm and sampled duration K. The fitting target is cumulative
FACTOR error at all 29 horizons in each view, ordered PRIMARY29 then FINE29.
There are 58 log1p targets, fitted together. Other mechanical methods and
inter-check observations remain diagnostics.

The prospective curve/mechanism selection has its own estimator, assessment,
relation-loss and transfer-procedure values. Original K-primary records retain
their original meaning and bytes. Select all four amended values together before
TRAIN or any dependent outcome. Exposed E2 analyses remain development evidence.

## Causal features and order

The shared base contains the existing 10 CONTEXT, four NORM_RADIUS and three
SPECTRAL descriptors, plus d_lin and two past-Hessian descriptors. The PRIMARY-Y structural descriptors are
associative leakage, Lie leakage, factor-fit angle and trailing angle. S0 adds
these four to the base. B0 adds four raw-norm drifts, one for each X/Y position
and momentum block. Each drift is `(last_norm - first_norm) / elapsed_time`
over the same 32-tick pre-cutoff window; it may be negative. Both primary
accounts therefore have 24 predictors. SHARED_BASE has 20 predictors, and
RAW_TRAIN_MEDIAN is a descriptive baseline.

Feature columns are the lexicographically sorted union of the selected blocks;
models retain that exact order with their coefficients. The original names and
transformations are:

| Block | Exact feature names and meaning |
| --- | --- |
| CONTEXT | `alpha-x`, `alpha-y`: realized cutoff alpha_tilde values; `bath-temperature`, `cross-gamma`, `friction`, `potential-m`: native physical parameters; `cutoff`: physical elapsed time; `family-de-anneal`, `family-x-first`, `family-y-first`: 0/1 indicators, joint increasing as reference |
| NORM_RADIUS | `momentum-x-norm`, `momentum-y-norm`, `position-x-norm`, `position-y-norm`: log1p of the PRIMARY triplet's raw HS norm at cutoff |
| SPECTRAL | `largest-y-rate`, `slow-y-mean`, `third-fourth-y-gap`: largest eigenvalue, mean of the lowest three and fourth-minus-third gap of the PRIMARY-Y passive operator |
| LINEAR_DEFECT | `d_lin`: log1p of the declared actuator-normalized PRIMARY origin-response defect |
| PAST_HESSIAN | `d_hessian_block`, `d_hessian_mix`: log1p maxima of the task-normalized causal first variations defined below |
| FACTOR | `associative-leakage`, `factor-fit-angle`, `lie-leakage`, `trailing-angle`: cutoff leakages, factor-fit angle and maximum within-window adjacent projector angle |
| NORM_DRIFT | `momentum-x-drift`, `momentum-y-drift`, `position-x-drift`, `position-y-drift`: signed change in raw HS norm divided by physical elapsed time |

Native inputs use their declared dimensionless simulator units; angles are in
degrees, indicators and leakages are dimensionless, and drifts are norm per
physical time. Passive spectral features do not claim native relaxation rates.
Missing or unidentifiable required channels, ambiguous frames or a missing
within-window angle make the causal feature unavailable. No channel is imputed.

d_lin is log1p of the maximum PRIMARY FULL_COUPLED-minus-FACTOR origin forecast
error over the declared four actions and 29 checks. It uses the native task
norm, with no future native state, HOLD or realized error. The FINE analogue
is retained separately. An unavailable PRIMARY defect makes the complete
matched feature unavailable for both accounts; it is not replaced by zero or
by the FINE value.

The two additional descriptors use the cutoff configuration and the saved
configuration exactly 32 PRIMARY ticks earlier. The elapsed time is 0.032.
Evaluate both Hessians under the handoff assay parameters in the same real
Hermitian coordinates. Symmetrize each Hessian as `(H + H.T)/2`.
The finite difference is `D_H = (H(q0) - H(qpast))/0.032`.

Sort the current signed eigenvalues. Join adjacent eigenvalues when their gap
is at most `1e-10 * max(1, ||H0||2)`. Use the transitive clusters and their full
projectors. Define `D_block = sum(P_b D_H P_b)` and `D_mix = D_H - D_block`.
These describe current blocks of a past change, not an exact future partition.
The complete spectral witness uses relative residual tolerance 1e-10.

For each component D, use the origin-only trend `delta H(s) = s D`.
At each BAOAB kick, inject `-dt/2 * delta H(s) * q_response` and propagate
through the frozen origin stages. The first kick uses `s=j*dt`; the final kick
uses `s=(j+1)*dt`, including its effect on the driven response.
Do not add another input-map derivative. Each feature is log1p of the maximum
correction norm over four actions, q/p blocks and the original 29 horizons.

PRIMARY supplies predictors. FINE supplies a separate diagnostic at corresponding
physical times. Missing past observations make the required PRIMARY feature
unavailable. No alternate window, future HOLD, future noise or future Hessian is
permitted. The structural and conventional blocks replace each other on this
shared base; their comparison is not a nested conditional-independence test.

The native TRAIN dependency order is prefix, numerical checks, factor
measurement/checks, causal projection, mechanical forecast, causal feature,
native response and score. The physical arrays and their exact producer are
inputs of the feature task; the feature is a prerequisite of the response task.
TRAIN does not require its own not-yet-fitted statistical model.

For protected CAL/CONF, the mechanical forecast is also upstream of the feature.
The fitted statistical forecast then seals point curves before native responses.
CAL has no calibrated radius at acquisition. After CAL, each CONF forecast
retains separate S0/B0 radii, original-unit upper curves and paired-view
admission decisions at every sampled horizon. S0 is the fixed primary admission
owner. An infinite radius refuses admission; an unavailable curve leaves the
decision unknown.

## Fitting and selection

TRAIN64 has two immutable folds: alternate entries of the sorted assigned
whole-root roster. Assignment occurs before inspecting features or targets;
missing roots do not shift later fold assignments. Fit all accounts on the
same complete roots. Missing features, unusable paired targets and declared
numerical discrepancies exclude the entire root from every fit. Retain every
excluded assigned root and its reasons.

At least 48 complete roots, with at least 24 in each original fold, are
required. Otherwise retain a training-prerequisite failure and unavailable
fitted predictions. No replacement roots are generated. The raw median remains
a descriptive value from the same complete set.

Use float64 weighted, centred thin SVD. Each whole group has weight one;
coordinates within a group have equal weights summing to one. Compute means
and population standard deviations from the fitting partition only. Constant
columns have scale one and centred value zero. A nonconstant unrepresentable
scale is a numerical failure. The intercept is the weighted target mean and
is unpenalized. Ridge penalties are exactly 1 and 10. Rank uses machine epsilon
times the larger design dimension times its largest singular value, with one
additional intercept dimension. Effective degrees of freedom are
`1 + sum(s^2/(s^2 + lambda))`.

A numerical fitting failure retains the completed fold diagnostics and failed
attempt, stops that account's search, and produces unavailable fitted points.
It never retries another penalty or changes the common group set. Each account
retains its attempt census, including failed attempts, within the five-bundle
limit.

Each fitted account performs four cross-validation bundles, one per penalty
and held-out fold, followed by one refit on the complete set. Each bundle fits
all 58 targets. Retain fold-local means/scales, whole-group coordinate weights,
design rank, coefficient norms, effective degrees of freedom and every
out-of-fold group loss. Transform each prediction by clipping log values at
zero and taking cumulative maxima separately within each 29-horizon view,
then invert with expm1.

Select the penalty by the mean whole-root continuous loss:

`L_curve = sqrt(sum((g - log1p(e))^2)/58) / log(1.01)`.

Here g is the same nonnegative cumulative-max log point curve and e is the
observed cumulative FACTOR error. Both views and all 29 horizons have equal
weight. Use Decimal precision 60 with round-half-even for log and RMS values.
Compare exact rational representations of those root values and choose penalty
1 on a tie. This defines a squared-training/RMS-selection algorithm, not a
universal optimality claim.

Compute predicted K against `log(1.01)` directly so exponential overflow or
rounding cannot change the inclusive adequacy boundary.
CAL and CONF do not select a penalty, feature mask or primary account.

Retain K losses and the raw TRAIN-median curve. Also calculate one integer
TRAIN-median K per view, with the lower central integer for even samples.
Each fold uses only its fitting partition to calculate these medians.
Report fitting and held-out one-check headroom against both medians and fitted
accounts, with unknown groups retained. Apply the final TRAIN medians unchanged
to confirmation. These diagnostics select neither a penalty nor a primary claim.

## Calibration, confirmation and reads

Calibrate S0 and B0 separately. Each assigned CAL root contributes the maximum
positive log1p residual across its 58 targets against the same postprocessed
point curves used for prediction. Missing predictions or targets contribute an
infinite score. CAL64 at nominal 95% uses rank 62. Three infinite scores make
the radius infinite. These are separate marginal model bounds under the
declared sampling assumptions, not simultaneous coverage of both models or
all later queries.

On CONF80, S0 wins when `L_curve(B0) - L_curve(S0) >= 0.1`.
The margin corresponds to about 0.0009950 RMS log-error units. It is a
prospective choice tied to epsilon=0.01, not a selected optimum or a per-horizon
improvement guarantee. The exact binomial test uses all assigned roots, null success
probability 1/2 and alpha 1/160; the critical success count is 52. Missing
comparisons count as operational nonsuccesses and remain unknown in the
descriptive true-event completion interval. Shared-base and raw-median results
do not replace this primary comparison.
The original one-check K comparison remains secondary. A curve win establishes
comparative curve accuracy only. It does not establish mean improvement, better
K prediction, service coverage or lower false-admission risk.

The public read authenticates the original consumed forecast/outcome receipts,
reproduces paired targets from complete dense score cells, replays fitted
predictions and upper policies, and reproduces both calibrations and the
confirmation assessment. Native TRAIN reads separately replay their original
received arrays and custody. The report retains continuous error loss, K loss,
exact complete-case means and inverse empirical quantiles, full-roster missingness,
separate model coverage and fixed-policy admission risk.

An authenticated unknown contact has all 3,248 score cells and 58 targets
explicitly unobserved. Its metadata-only read does not open native arrays or
claim origin-curve measurements; the original mechanical forecast and causal
feature remain separate retained products.

For each model and horizon, risk counts each admitted whole root once. With
`nA` admitted, `f` known failures and `u` unresolved admitted outcomes, the
descriptive one-sided 95% upper failure bound uses `f+u` out of `nA`.
No admissions gives undefined conditional risk. Report admission coverage
against the full assigned roster beside the bound. A vacuous bound or complete
refusal is not evidence of useful service, and marginal calibration does not
establish low risk conditional on admission.

The implementation owners are
[`matched_response_prediction.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_factor_response/matched_response_prediction.py),
[`matched_response_fitting.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_factor_response/matched_response_fitting.py)
and the existing configured protected/native TRAIN bindings. The
[workflow guide](../workflows/matrix-response-experiment/guide.md) describes
public preparation, execution, reads and export.


## E4 matched relation contract

The relation uses the same 58 targets, two whole-group folds, penalties 1 and 10,
fold-local scaling, unpenalized intercept and five-fit limit per fitted arm.
The original E4 acquisition graph seals mechanical predictions before the
statistical account so both arms can use the original PRIMARY `d_lin`.
The causal feature record binds that mechanical producer and separately retains
the FINE defect. Original S0/B0 points remain reference accounts.

Relative to declared positive nominal temperature, friction and coupling, define
three inputs `x_j = log2(j/j0)`, their three pair products and
`q_agg = (x_T² + x_gamma² + x_c²)/3`. Use three fixed family indicators with
joint-increasing preparation as reference. Replace the raw physical values and
original family indicators once in the shared feature base. SR adds the four
structural features; BR adds the four raw-norm drifts. Both receive the two
past-Hessian descriptors. Each has 28 features.
Physical-only, shared relation base and raw DEV median are secondary controls.

The corners have `x_j` equal to -1 or 1; the center has all three zero.
Only aggregate curvature is identified on this grid. The specified `q_agg`
extension to a single off-grid case is a modeling assumption fixed before
transfer. Another coordinate's state, matched response contrast or future
structural observation cannot enter the feature calculation.

DEV16 assigns four groups per family and nine coordinates per group. Require
at least 12 common complete groups, two per family and one per family in each
fold. Equal group weight and equal coordinate weight make each group's mass
one. Retain incomplete assigned groups and actual numerical failures; do not
redraw or add fit attempts. A paired target discrepancy exceeding 0.0001 makes
the case numerically unusable for fitting or the primary comparison.

Separate SR/BR calibration uses the maximum positive residual over all 522
coordinate/view/horizon targets per group. CAL20 uses rank 20, so one unresolved
group makes its model's bound infinite. Average the nine coordinate L_curve
values equally, for both penalty selection and confirmation. Confirmation
contributes one decision per group, with BR-minus-SR improvement at least 0.1.
CONF32 uses null probability 1/2 and alpha 1/160, requiring 24 successes.
Unknown comparisons remain in the assigned denominator.

The existing E4 reader authenticates complete seven-method dense scores and
replays causal features from their original prefix, diagnostic and mechanical
archives. Its supplementary dense products project the already dense original
predictions and retain the exact original cells. The shared relation arithmetic
lives in
[`e4_structural_prediction.py`](../../../../src/empirical_lawhood/adapters/methods/matrix_scheduled_history/e4_structural_prediction.py).
These component contracts do not establish completion of the public SR/BR
freeze, calibration and downstream lifecycle; that lifecycle must retain the
actual original model and forecast products before any prospective result is
claimed.

## Same-bank mechanism readout

Keep FULL, ZERO and every originally issued mechanical comparator. Add the
fixed INPUT_KRYLOV48 as a deterministic secondary readout on the same branches.
No new native branch, fit or dimension search is introduced.

Use the original final-horizon actuator whitening. Seed the position basis
with Bq, then Bp, in action order. Append q/p columns of `A^k B` for
k=1 through the native horizon, stopping at 24 position directions.
Project twice against preceding columns. Accept a residual above 1e-10 times
the original column norm, and make its largest absolute coordinate positive.
If necessary, fill from stable absolute-Hessian-eigenvalue order. Report actual
input, Krylov and slow-fallback dimensions. Require orthogonality residual below
1e-10. Use this basis for both physical position and momentum reduction.

After reveal, reconstruct the HOLD tangent from the saved branch and native
Hessian action. At ticks 16, 32, 64 and 128, retain all panels, actions and
q/p blocks for `native - FACTOR = (native - HOLD) + (HOLD - FULL) + (FULL - FACTOR)`.
Retain the three signed task-unit vectors, norms, signed cross terms, identity
residuals and actual response magnitude. Identity tolerance is 1e-12 in task
units. Retain numerical and factor-admission states beside these values.
No additional nine-term or spectral attribution is selected.

The public read binds original source, protocol and archive identities.
It reports FINE feature diagnostics, fixed-comparator curves and construction
costs alongside existing task evidence. A small response-state dimension does
not establish a speed advantage after construction costs.
Friction, temperature and coupling contrasts measure total protocol effects.
They do not isolate thermal noise or establish causal mediation.

## E5 paired response adequacy

The prepared route retains the original ramp and the declared early and delayed
ramps, each with nominal effort 8. Construction rules and fitted coefficients
are frozen. Each arm nevertheless has its own handoff state, factor, Hessian,
force, receivers and normalization scales. These state-conditioned instruments
do not establish identical physical tasks across arms.

Order each case as preparation, numerical and factor checks, causal projection,
mechanical construction, causal feature and statistical forecast, then native
futures. Seal all five E4 relation accounts and the original S0/B0 references.
The prepared feature uses only that arm's 32-tick history and frozen mechanical
arrays. SR/BR retain their original E4 calibration radii and their separate
29-horizon policies; there is no downstream fit, recalibration or account choice.

The E5 endpoint is sampled FACTOR response adequacy through tick 64 at epsilon
0.01 in both views. No external delivered-task criterion is selected. Native
adequacy, admission plus adequacy, coverage and effort are separate outcomes.
An unavailable statistical forecast does not erase observed native adequacy.

DEV16 retains every original/early/delayed pair. For each alternative report
observed gains, harms, joint successes, joint failures and unknown pairs. For
the conservative completion, an unknown prepared outcome is assigned failure
and an unknown baseline outcome success; known outcomes are preserved. These
assignments are statistical possibilities, not observed physical failures.
Nomination requires two observed rescues and conservative net improvement of
at least 0.10 over all 16 groups. Maximize that improvement, then minimize total
effort, then use lexical arm ID. Without a nomination, CONF is unentered.

Conditional CONF80 uses the one-sided exact paired discordance test: for gains
g and harms h, use the binomial upper tail at g out of g+h with null 1/2.
No discordance gives p=1. The primary calculation uses the conservative
completion of all 80 pairs; complete-pair results are descriptive. At alpha
1/160, eight gains and zero harms pass and seven do not. A meaningful-benefit
disposition also requires conservative net improvement at least 0.10. This
point estimate does not certify a population improvement of at least 0.10.

For descriptive absolute paired-gain uncertainty, give gain and harm rates
separate two-sided 97.5% Clopper–Pearson intervals. Subtract opposite endpoints
and clip to [-1,1]. Their union bound gives conservative 95% coverage; envelope
all feasible completions of unknown pairs. Gain and harm rates depend on the
declared common-noise coupling. The net difference has the arm-marginal
interpretation under the declared sampling assumptions.

Partition observed gains by ZERO_RESPONSE failure in both views, success in
both, disagreement or unresolved results. Retain all seven mechanical methods,
sampled durations, full-grid failure timing and paired response amplitudes.
Also retain INPUT_KRYLOV48 and the signed mechanism readout. Compare actual
force maps, receiver maps and receiver projectors across paired arms in their
common native coordinate frame. Tick-64 success requires K>=13. Two observed
rescues with zero harms yield net gain 0.125 on DEV16.
Quieting requires an observed paired decrease in the declared amplitude
readouts; small normalized error alone does not establish useful actuation.
Nominal effort is not measured thermodynamic work, heat or entropy production.

## E6 frozen temperature transfer

The pre-fit reserve contains 64 independent groups at T=1.125 and another 64
at T=3.25, with the remaining nominal de-anneal parameters unchanged. The exact
E4 feature extension applies to both single off-grid coordinates. SR/BR and
S0/B0 predictions are sealed before futures. SR versus BR remains the primary
comparison; reference or diagnostic accounts cannot replace it after outcomes.

Each regime tests the unchanged frozen SR/BR continuous-curve comparison with
margin 0.1. The original K and one-check comparisons remain secondary. Use all 64
assigned groups, null probability 1/2 and alpha 1/160: 43 successes pass, 42 do
not. Missing comparisons remain operational nonsuccesses and explicitly unknown
true events. Adverse E5 results, nonnomination and vacuous bounds do not prevent
otherwise eligible transfer. Absent required models, sources or authority remain
their own prerequisite failures.

Report predictive transport separately from post-reveal mechanism transport.
Computing the fixed causal features at a new cutoff applies the frozen rule.
Changing it using future responses would be refitting. E4 calibration does not
automatically establish coverage at a shifted temperature. Retain unresolved
admissions and empirical risks; do not add a retrospective calibration repair.
These regimes test the fixed off-grid extension within the selected substrate,
preparation slice and instrument rule, not transfer to other matrix sizes or
physical domains. Planned E6 completion closes this programme.

For each fixed SR/BR policy and horizon, report all assigned, admitted, assessed
admitted and unresolved admitted groups, observed failures and adequacy. Report
a complete-case 95% interval and a one-sided 95% upper risk bound assigning all
unresolved admitted outcomes as possible failures. Zero admissions gives
undefined conditional risk. Nested requests do not multiply independent units.
Unchanged E4 bounds face an empirical transport challenge; marginal calibration
does not establish conditional admission reliability or a transport guarantee.

Independent prepared readers authenticate the actual consumed causal, diagnostic,
mechanical and native array receipts, replay the handoff feature and all frozen
points, and reproduce the native readout and terminal reduction. They recheck
current access separately. Development controls and successful execution do not
establish scientific qualification, sampling authority or fresh programme results.
