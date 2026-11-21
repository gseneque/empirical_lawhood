# Two classical matrix capstone connections

SPDX-License-Identifier: CC-BY-4.0

## Purpose and scientific status

The consolidated classical series implements two separate connections from the
matrix capstones. These are newly authored adaptations on the actual six-matrix
native substrate. They do not reproduce historical success counts, import an
old decision as a fresh observation, or turn exposed development outcomes into
protected confirmation.

The first connection is

\[
\widehat z_p=U(z_0,p),\qquad
\widehat y_a=F_a(\widehat z_p,b_a,\theta).
\]

An upstream predictor supplies the 24-coordinate prepared description needed by
fixed response coefficients. The forecast and assay choices are committed before
preparation begins. The second connection uses the measured prepared description

\[
\widehat y_a=F_a(z_p,b_a,\theta),
\]

with exactly the same coefficients, support, uncertainty calibration and task
requirements for every physical preparation. It tests whether preparation changes
the circumstances in which a completely unchanged package supplies useful answers.

Neither connection is the E3 forecast of a reduced model's eventual error, nor
the E5 comparison of state-specific refreshed reduced bases. Those remain separate
experiments in the consolidated series.

## Physical quantities and finite tasks

The 24-coordinate descriptor is the position part of the series' fixed physical
receiver, applied to the 96 native position coordinates. It is a deliberately
restricted description, not a claim that 24 numbers determine all future dynamics.
The same chart is used at the initial and prepared states.

There are two explicitly derived scalar tasks. The first authored action is read
through position component 1; the last authored action is read through momentum
component 0. Both use the declared capstone horizon, which defaults to tick 64 or
the shorter actual horizon of a software smoke design. The selected action names,
receiver components, horizon and task definitions are retained in the frozen
package and each commitment. A smoke horizon is not labelled a 64-tick result.

Each scalar response is the original half-difference of matched positive and
negative native force branches. It is divided by the corresponding original
actuator scale:

\[
s_q(t)=\epsilon\tau_p(t-\tau_p/2),\qquad
s_p(t)=\epsilon\tau_p,
\quad \tau_p=\min(t,t_{\rm pulse}).
\]

The physical force directions vary according to the series' declared root
instrument. They are known before preparation and enter the response relation
explicitly as 96-coordinate covariates. They are not inferred from a later
response or silently identified across unequal physical actions. Native parameter
coordinates enter as the three logarithms of temperature, friction and coupling.

A task request is admitted when its committed interval has radius no greater than
the authored `response_tolerance`, its lower endpoint reaches the authored
`capstone_task_threshold`, and its required input is inside the frozen support.
The threshold defaults to zero, so the default request concerns a nonnegative
signed scalar response. These new task requirements differ from historical
capstone request menus and retain their own identities.

## What is fitted and frozen

The public implementation is
[`capstones.py`](../../src/empirical_lawhood/domains/matrix/classical_series/capstones.py).
It owns pure numerical and JSON operations; ordinary recursive execution owns
source bindings, artifact custody, workers, recovery and publication.

For the fixed response package:

1. Use only the nominal coordinate and baseline preparation from TRAIN roots.
2. Fit one ridge relation per scalar task from prepared descriptor, known physical
   force and parameter covariates to the primary-view panel-mean response.
3. Construct the descriptor support from the same baseline TRAIN population. It
   is a standardized coordinate box around the TRAIN mean, with authored radius
   `capstone_support_radius`. A `64 * binary64 epsilon` scale floor prevents a
   division by zero; it is not physical uncertainty or an enlarged population.
4. On CAL roots, evaluate the maximum absolute residual across both tasks,
   numerical views and panels. A root contributes one score.
5. Freeze the coefficients, support, calibration radius, finite tasks, numerical
   meaning and complete source selections under one package digest.

The ridge implementation centers features and targets and uses the dual system
when the number of TRAIN rows is smaller than the physical feature dimension.
One root supplies one fit row per task; nested views are not counted as independent
training or calibration populations. A fixed coefficient vector is an empirical
response model. Its adequacy is tested, not inferred from its linear form.

For the upstream composition, fit a separate prepared-state predictor for every
assigned preparation using only TRAIN roots. Inputs are the initial 24-coordinate
description and known native parameter coordinates. The output is the predicted
prepared 24-coordinate description. On each CAL root, retain two complete-root
scores, each maximized across all assigned preparations and nested observations:

- The standardized prepared-description prediction error.
- The error of the composition using the already fixed response coefficients.

These are **separate composition calibrations**. They do not modify the underlying
response coefficients or overwrite the original fixed package's calibration.
A forecast can be used only when its calibrated description box is wholly inside
the fixed package's support. The response interval then uses the separately
calibrated composition residual.

## Calibration and missingness

With `n` assigned CAL roots and authored `alpha`, each radius uses order

\[
k=\left\lceil(n+1)(1-\alpha)\right\rceil.
\]

Unavailable or numerically unresolved roots contribute infinite residuals. They
remain in `n`. If `k > n`, or the selected order statistic is infinite, the
radius is explicitly vacuous (`None` in the JSON representation), and requests
requiring it decline. Missing roots are not replaced by a smaller complete-case
calibration population.

Under the declared exchangeability and training-separation assumptions, each
composition calibration supplies a marginal complete-root statement. The
simultaneous descriptor-and-response statement has the conservative union bound
`1 - 2 alpha`, clipped below at zero. The code does not call the two separately
calibrated statements a joint `1 - alpha` guarantee. It also does not claim
conditional coverage among admitted requests.

The original fixed response calibration is **baseline nominal only**. Applying
that unchanged calibration after a different preparation is a scientific
hypothesis tested by the new assigned roots. Merely placing the resulting
24-coordinate descriptor inside the support box does not prove exchangeability
with the baseline distribution. Both coverage and useful delivery after the
preparation remain visible outcomes. Transfer parameter coordinates outside the
nominal package decline and retain their full assignment; the separate E6
experiment investigates transfer.

## Causal execution hooks

The native domain calls these public helpers at distinct times:

| Helper | Required information and cutoff |
| --- | --- |
| `capstone_preparation_commitment(config, seed, coordinate, arm, initial_descriptor, forces, package)` | Before generating preparation-noise tapes or advancing native preparation; receives no prepared state or future response |
| `capstone_response_commitment(config, seed, coordinate, arm, prepared_descriptor, forces, package)` | After preparation, before any assay-future noise or native advance; receives both measured 24-coordinate numerical views |
| `capstone_case_summary(config, seed, case, receivers, forces)` | After acquisition; extracts only the compact original descriptors, two scalar response families and original numerical status |
| `freeze_capstones(config, summaries_by_seed, training_seeds, calibration_seeds)` | Consumes only the declared disjoint TRAIN and CAL compact root summaries |
| `assess_capstones(config, acquired, package)` | Reads original frozen commitments and retained responses; does not fit, repair, change support, select a new preparation or alter task admission |

The recursive graph puts TRAIN/CAL acquisition and summaries before calibration,
and makes that exact calibration a prerequisite of CONF acquisition. The
before-preparation and before-assay commitments carry package, settings, physical
force and input identities. Assessment recomputes the corresponding deterministic
commitment from its original inputs and requires exact agreement. Custody and
source identity come from the shared execution contracts; the JSON hash alone
is not a substitute for them.

## Preparation selection and paired assessment

A nonbaseline preparation is nominated using TRAIN-only mean distance from the
fixed response package's support centre. This criterion does not use CAL or CONF
outcomes, does not alter `F`, and makes no guarantee of a gain. The selected arm
and all alternatives remain in the census. If no candidate has a complete usable
TRAIN support comparison, the nominee is explicitly unavailable.

On each CONF root, the baseline and nominee use their actual prepared inputs but
the **same complete package digest**. The paired readout retains baseline and
prepared delivery counts, gain/harm or unknown status, and the common package
identity. A failed or ineffective preparation is a scientific outcome. The
implementation never refreshes the package to manufacture a gain.

A delivered request requires its original admission, a numerically usable native
future, an actual prepared descriptor within the selected package's support,
coverage by the committed response interval and satisfaction of the requested
scalar target. An admitted request whose future is unavailable is unresolved;
it is neither a success nor an observed false admission. Requests that declined
remain in the original task and root denominators.

Population reduction uses independent roots. Tasks, numerical views, panels,
preparation arms and parameter coordinates are nested observations. The scalar
channels can be described individually or joined into a whole-root event, but
their number must not become an inflated independent sample size.

## Verification and practical interpretation

Run:

```sh
uv run --no-sync pytest -q tests/test_classical_matrix_capstones.py
```

The controls use a known affine preparation and response construction to verify
that the first connection forecasts the actual required input and that the second
changes the input while retaining the entire package. Other controls enforce
source cutoffs, exact frozen identity, complete calibration and task censuses,
numerical refusal, unresolved admitted futures and absence of CONF refitting.
These are software and numerical controls, not new native matrix success counts.

An initially uninformative descriptor, stochastic preparation, broad composition
radius or poor response relation may cause every task to decline. Such a result
identifies a missing supplier or inadequate scientific choice; it does not justify
silently changing support, rebuilding `F` for each arm or relabelling an E3/E5
result as a capstone. An authored successor can change those choices under a new
identity, using the retained result as exposed development evidence.
