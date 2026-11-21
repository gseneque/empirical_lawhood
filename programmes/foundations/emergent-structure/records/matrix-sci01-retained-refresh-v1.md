# SCI01 retained fixed-basis refresh protocol

SPDX-License-Identifier: CC-BY-4.0

This specification defines the SCI01 comparison on retained E4 responses.
It separates operator evolution, response reduction and signed cancellation.
Use the [procedure](../workflows/matrix-retained-refresh/guide.md) to publish the bound protocol before calculation.

## Identity, evidence and complete census

The protocol ID is `matrix.sci01.retained-refresh32.v1`.
The record revision is `1.0.0`.
This successor has the evidence role `EXPOSED_DEVELOPMENT_NONPROMOTABLE`.
It changes no original E4 result or scientific meaning.
It permits zero new native acquisitions and zero statistical fits.

The canonical protocol binds this specification's SHA-256 and the original programme, execution plan, entry evidence and run.
The original reader derives all 144 case records from complete authenticated execution custody.
Each case binds its original source, response protocol, causal prefix, physical forecast, native response and score.
The retained census contains 36 usable cases and 108 `NO_ORIGIN` cases.
There are 16 assigned groups and four usable independent groups.
Each group contains eight corners of `(T, gamma, c)` in `{0.5, 2}^3` and the nominal `(1, 1, 1)` case.
Coordinates, actions, two response panels, numerical views and times are nested observations.
They do not increase independent replication.

Complete original receipts, attempts, recovery events and missing results remain in their original custody.
The successor binds their census and exact selected record identities.
Current original input access remains necessary through calculation, assessment and final publication.
Neither configuration validation nor the successor's completion receipt supplies access authority.

## Fixed physical task and methods

Retain the six Hermitian matrices, 96 position coordinates, 192 phase coordinates and original native Hermitian frame.
Retain the original four actions, pulse amplitude `0.01`, physical forces and 48 receivers.
The receivers contain 24 position and 24 momentum components.
PRIMARY uses timestep `0.001`; FINE uses `0.0005`.
The pulse lasts 16 PRIMARY steps or 32 FINE steps.
Measure the odd native response `C(z_plus - z_minus)/2`, without division by amplitude.

Compare `FULL`, `FULL_REFRESH32`, `INPUT_KRYLOV48`, `INPUT_KRYLOV48_REFRESH32` and structural comparator `FACTOR`.
Historical IO48 does not replace INPUT_KRYLOV48.
FULL and FACTOR must reconstruct their original retained predictions.

Reuse the [accepted input-aware basis owner](../../../../src/empirical_lawhood/domains/matrix/matrix_factor_response/mechanism_readout.py).
Its original H128 actuator whitening, input order and two-pass orthogonalization remain fixed.
Take position and momentum input columns, then corresponding powers of the original discrete transition through the native horizon.
Fill any missing directions from the stable ordering of absolute signed Hessian eigenvalues.
Retain 24 position directions in both phase blocks, giving phase dimension 48.
Use relative rank tolerance `1e-10` and Frobenius orthogonality tolerance `1e-10`.
Preserve the fixed column signs and report the actual slow-mode fallback count.
This construction fits no statistical model.

## One causal checkpoint and continuation

Each refreshed method receives its own panel's HOLD position and parameters at physical time `0.032` after the response origin.
This is relative tick 32 in PRIMARY and 64 in FINE.
Authenticate absolute clocks, constant suffix parameters, common signed-branch origins and within-panel innovations.
The prediction function receives origin operands and the four isolated checkpoint observations.
It receives no native response, later observation or revealed tangent state.

Construct the checkpoint Hessian with the original source derivative owner.
Keep the physical force, receiver, basis, timestep, friction and two force kicks unchanged.
Complete the original step ending at the checkpoint with the original operator.
Use the refreshed operator for PRIMARY steps 33–128 or FINE steps 65–256.
Continue each model's own predicted state, including its accumulated error.
Do not reset, reconstruct or transfer that state from an observed response.
Do not rebuild the basis or revise earlier predictions.

For basis `U`, operator `H`, half step `a = dt/2` and damping `d = exp(-gamma*dt)`, use:

```text
K = U.T H U
f = U.T (0.01 * physical_force) during the pulse; zero afterwards
p <- p + a * (f - K q)
q <- q + a * p
p <- d * p
q <- q + a * p
p <- p + a * (f - K q)
```

H64 is the primary horizon.
H128 is a secondary stress diagnostic with the same tick-32 operator and no further update.

## Assessment, weak channels and signed quantities

Preserve predictions and native vectors at every aligned PRIMARY tick through 128.
Use original-origin cumulative maxima at the original 29 checks, `16, 20, ..., 128`.
Report all-tick maxima separately as diagnostics.
The distinct prospective preparation protocol does not replace this retained comparison's original scoring grid.

With `t = tick*0.001`, `p(t) = min(0.016,t)` and `I(t) = 0.01*p(t)`, use scales:

```text
position: I(t) * (t - p(t)/2)
momentum: I(t)
```

Take the maximum normalized block norm over actions, panels and all preceding declared checks.
A method is adequate when both views have error at most `0.01` and its cumulative paired-view discrepancy is at most `0.0001`.
Retain the original numerical usability requirement.
Evaluate the paired-view gate separately through each horizon.
A later H128 discrepancy does not invalidate an evaluable H64 result.
Equality passes each stated threshold.

Retain native signal and signed error by action, block, receiver and aligned time.
Report COMPLEMENT and GENERIC beside FACTOR and TRACE.
An actuator-normalized error of `0.01` does not mean 1% of the native signal.
Signal-relative ratios are diagnostics only, with explicit missing ratios for zero signal.
No separate weak-channel adequacy tolerance or molecular tolerance is selected here.

For frozen FACTOR and INPUT_KRYLOV48, retain the normalized vectors:

```text
native - model = (native - HOLD) + (HOLD - FULL) + (FULL - model)
```

For refreshed INPUT_KRYLOV48, replace both full intermediates with `FULL_REFRESH32`.
Each refreshed intermediate carries its own predicted state.
Retain all three vectors, their squared norms and the three signed twice-dot-product cross terms.
Verify both vector and squared-error identities.
Negative cross terms and favorable cancellation remain findings.
The revealed-HOLD tangent is evaluator information and supplies no causal prediction.

## Matched finite changes

Within each group, pair `c=0.5` and `c=2` at fixed temperature and friction.
The nominal `(1,1,1)` case supplies the common physical receiver, selected by this rule before calculation.
Require exact equality of the two endpoints' actual TRACE or GENERIC force arrays and actuator scales.
Require matching panel identities.
Project retained raw native phase endpoints and reconstructed model states into that common receiver.
Do not infer native states from incompatible scored projections.
Missing origins, constructions or physical joins remain unavailable diagnostics.

For native-minus-model endpoint errors, retain `e_delta = e_high - e_low`.
Keep both signed endpoint errors, the signed native difference and the signed difference error.
The 64 assigned pairs contain 16 pairs with usable original origins.
They remain nested within four usable independent groups.
These diagnostics do not validate molecular WT–mutant effects.

## Independent decision, costs and stop

The independent reader reopens original custody and every closed calculation member.
It composes affine BAOAB transition and input maps without calling the continuation producer.
It reconstructs checkpoint source Hessians, fixed bases, saved states, all aligned predictions and signed identities.
Normalized reconstruction tolerance is `1e-10`.
It independently recalculates cumulative errors with scalar squared sums.

Report every case and equal-group summaries for all cases, low coupling, high coupling and nominal centers.
Keep high-temperature, high-friction, low-coupling exceptions explicit.
At H64, use the following scoped decisions after numerical evaluability:

| Result | Decision |
| --- | --- |
| Frozen FULL and frozen INPUT_KRYLOV48 adequate | Frozen response |
| Both refreshed methods adequate | One refresh |
| Refreshed FULL adequate, refreshed reduced inadequate | Inadequate retention |
| Refreshed reduced adequate, refreshed FULL inadequate | Cancellation requires assessment |
| Neither refreshed method adequate | Reference calculation at this assessed scope |

An unavailable construction or numerical comparison remains unresolved.
No scalar advantage establishes separate weak-channel or molecular adequacy.

Measure calculation, original custody, basis construction, operator work, propagation, publication and independent assessment costs separately.
Count cached origin information as a prospective requirement.
Charge checkpoint observation, the 32-step baseline prefix when unavailable, and source Hessian-vector products.
Retain unknown original timings instead of assigning zero cost.
Separate study cost, incremental use and finite-reuse cost.
Matrix operation counts alone establish no molecular saving.

Finish with the independently assessed method record and a concrete molecular operand handoff.
Translate the representation, horizon, paid observation, fallback, weak-channel requirements and complete measured costs.
Stop this retained tranche without new native acquisition, refitting, missing-family replacement or E5/E6 entry.
SCI02 and molecular bridge execution require separate selected scopes.

## References and research

The [original Matrix contract](matrix-programme.md), [origin mechanics](matrix-origin-response.md) and [dense response specification](matrix-dense-response.md) own original scientific meaning.
The [retained results](release-results.md) preserve the original unavailable and negative findings.
The source [continuation](../../../../src/empirical_lawhood/domains/matrix/matrix_factor_response/refresh_science.py) and [independent reader](../../../../src/empirical_lawhood/domains/matrix/matrix_factor_response/refresh_read.py) implement this successor.
This specification is self-contained and does not require a packaged work plan.
