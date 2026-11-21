# SCI01 matched-error and representation accounting

SPDX-License-Identifier: CC-BY-4.0

This specification defines three descriptive analyses of retained E4/SCI01 evidence.
It tests endpoint reversals, signed error alignment and post-checkpoint representation error.
Use the [procedure](../workflows/matrix-retained-refresh/guide.md#export-the-three-matched-analyses) with the original calculation and independent assessment.

## Scope and source bindings

The protocol ID is `matrix.sci01.matched-accounting.v1`, revision `1.0.0`.
Its evidence role is `EXPOSED_DEVELOPMENT_NONPROMOTABLE`.
The protocol binds the original SCI01 protocol, both completed packages and this specification's exact SHA-256.
Publish these bindings before the calculations.
Retain original input access through final publication.

The original denominator remains 144 cases, including 108 `NO_ORIGIN` cases.
There are 16 assigned groups and four usable independent groups.
The 64 assigned finite pairs include 16 usable pairs and 48 unavailable pairs.
Coordinates, panels, actions, numerical views and horizons are nested observations.
No analysis creates independent replication or molecular admission.

The three analyses use retained operators, bases, states and native endpoints.
They acquire no native trajectories, fit no model and build no basis.
They add no operator update and change no original result.
Frozen controls use the same accounting identity as refreshed models.

## 1. Matched-cell reversal census

Within each group, compare `c=0.5` and `c=2` at fixed temperature and friction.
Use the group's original nominal `(1,1,1)` receiver for both endpoints and all methods.
Require exact matching physical forces, actuator scales and panel identities.
Retain TRACE and GENERIC, position and momentum blocks, PRIMARY and FINE, and both panels.
H64 is primary. H128 is a stress diagnostic.

A cell fixes group, parameter pair, receiver, force, action, block, view, panel and horizon.
Compare FULL with FULL_REFRESH32 and INPUT_KRYLOV48 with INPUT_KRYLOV48_REFRESH32 within that cell.
Project retained physical endpoint states before calculating errors.
Do not compare separate cumulative maxima or receiver menus.

Use predicted-minus-native errors `e_H` and `e_L`, and `e_delta = e_H - e_L`.
The original SCI01 arrays use native-minus-predicted errors.
Negate their signed vectors for this export. Squared norms and inner products remain unchanged.

Count these events:

- Both endpoint errors improve and their contrast worsens.
- One endpoint improves and the other worsens.
- Both endpoint errors worsen.
- The contrast improves.

The last event can overlap the preceding endpoint categories.
Also report the complete endpoint-by-contrast contingency table and ties.
Keep strict arithmetic signs and a separate roundoff classification.
A change within `64 * binary64_epsilon * max(before_squared, after_squared)` is a roundoff tie.
This is an arithmetic rule, not a scientific-effect or adequacy threshold.

Report all retained cells and a separate subset passing the original numerical gates at that horizon.
Both endpoints and both methods must pass those gates for the subset.
A failed gate does not erase the descriptive vectors or unavailable pair census.
Report distributions by independent group and by action, block, view and panel.
Do not interpret nested cell counts as independent trials.

## 2. Signed error-alignment accounting

For each matched cell and method state, compute:

```text
S = ||e_H||^2 + ||e_L||^2
A = 2 <e_H, e_L>
D = ||e_H - e_L||^2 = S - A
Delta D = Delta S - Delta A
```

Retain the signed change in each quantity and verify both identities.
Positive `Delta S` contributes endpoint-energy growth.
Positive `-Delta A` contributes loss of alignment.
Retain opposing contributions, favorable cancellation and ties.
These deterministic inner products are not estimates of statistical covariance.
They differ from cross terms within one prediction's error decomposition.

## 3. Post-checkpoint representation accounting

The checkpoint is PRIMARY tick 32 or FINE tick 64, at physical time `0.032`.
The pulse has ended. Let `M` be the full unforced discrete BAOAB transition.
Let `U` be the retained position basis and `L = diag(U,U)` its phase-space lift.
Compose the actual reduced BAOAB transition `R` from `U.T H U`.
Do not substitute `L.T M L` for `R`.

Full and reduced models continue their own retained checkpoint states without reset.
For `d_k = f_k - L z_k`, evaluate:

```text
I_N = M^(N-tau) d_tau
G_N = sum[k=tau,...,N-1] M^(N-1-k) (M L - L R) z_k
d_N = I_N + G_N
```

`I_N` propagates representation error already present at the checkpoint.
`G_N` accumulates representation error generated after that checkpoint.
Compute both terms for the refreshed operator and for the frozen control.
Reconstruct only deterministic suffix states from retained inputs.
Verify saved H64/H128 states with independently applied BAOAB substeps.
Use the original normalized reconstruction tolerance `1e-10`.

Apply the common physical receiver and original actuator scales to each signed term.
Then form the high-minus-low differences of those receiver contributions.
Export the endpoint terms, paired terms, squared norms and signed twice-inner-products.
Verify the vector and squared-norm identities for every row.

This identity explains FULL-minus-reduced response, not the complete error against native response.
With the declared error convention, `e_reduced,delta = e_full,delta - C(d_H-d_L)` after common normalization.
Verify that additional join against the matched native-reference errors.
Preserve the signs of inherited, generated and full-reference contributions.

## Deliverables and stopping rule

Export exact source bindings, all signed vectors, bounded array operands and the unavailable-pair census.
Include complete group/channel counts, arithmetic checks, actual environment and source identities, and measured analysis costs.
Report the stronger conjunction only where the matched census establishes it.
Keep narrower findings when it does not.
Do not add experiments to obtain a preferred narrative.

The [original SCI01 specification](matrix-sci01-retained-refresh-v1.md) retains its method and information-cost contract.
Checkpoint observations, unavailable baseline prefixes and required operator information remain paid requirements.
This export does not remeasure those costs or make them free.
SCI02, E5/E6 and molecular execution remain outside this scope.
