# RC prerequisite experiment protocol, revision 1

SPDX-License-Identifier: CC-BY-4.0

This protocol specifies two prerequisite experiments and their joined use.
It fixes the numerical RC design before execution.
Use the [guide](guide.md) to prepare its inputs and retain every result.

## Evidence boundary

The route uses eleven exposed, deterministic numerical model preparations.
It supplies development evidence and software conformance checks.
It supplies no physical measurement, population estimate, fresh confirmation or scientific qualification.

The three claims are separate:

| Claim | Required supply | Falsifier |
|---|---|---|
| RC-M | Measurement supplies the required state description before the preparation decision. | Missing or late information, wrong meaning or binding, excessive uncertainty, or false interval coverage. |
| RC-P | The committed preparation supplies the unchanged F_RC support condition. | An invalid handoff, inadequate prospective guarantee, or prepared state outside support. |
| RC-J | The complete admissible chain meets its fixed terminal task and resource commitments. | A failed connection, numerical failure, missed deadline, or failed terminal task. |

A successful endpoint outside support does not establish admissible F_RC use.
A positive connection does not establish the complete-chain claim.
A correct implementation can retain a negative experiment result.

## Fixed model and independent equation

One capacitor has C = 1 F.
The left and right source resistances are both 1 Ω.
The receiver is the capacitor node voltage, in V.
Component values, source impedances and receiver remain fixed across all comparisons.

For constant source voltages L and R, the scalar reference is:

```
dV/dt = L + R - 2V
V(t+h) = (L+R)/2 + (V(t) - (L+R)/2) exp(-2h)
```

This equation independently checks the existing native RC solvers.
Agreement between two production solvers alone does not establish a connection claim.

The complete initial-voltage roster is:

```
-2, -1.2, -0.4, -0.05, 0.05, 0.15, 0.25, 0.4, 1.2, 2, 3 V
```

Each initial preparation is one assigned development unit.
Scenarios, preparation arms, clocks and solver views remain nested within that unit.
They do not increase the eleven-unit denominator.
These values are exposed fixtures, not samples from an unobserved population.

## Information and preparation commitments

Measurement samples the capacitor voltage at absolute time 0 s.
The nominal report becomes available at 0.04 s.
The preparation decision cutoff is 0.05 s.
Both source voltages remain zero before that decision.

The nominal observer adds the predeclared error +0.005 V to the native sample.
It reports an uncertainty radius of 0.01 V.
The interval is [report − radius, report + radius].
The deterministic radius is an absolute development bound, not a statistical confidence interval.

The policy consumes the report, its declared uncertainty, quantity, units, receiver, source/model binding and availability.
The policy does not consume the initial state, prepared-state readback or later endpoint.
The independent oracle assesses interval containment only after the decision commitment.

Select the shortest zero-boundary preparation duration from this fixed menu:

```
0, 0.25, 0.5, 1, 1.5 s
```

For report y, radius r and duration d, require:

```
max(abs(y-r), abs(y+r)) exp[-2(0.05+d)] <= 0.1 - 0.000000000001 V
```

The 10⁻¹² V guard is a fixed conservative arithmetic margin.
The radius must not exceed 0.01 V.
The policy refuses invalid information or the absence of an adequate menu item.
It does not extend the menu after a refusal.

The response starts at 0.05 + d s.
It ends at 1.05 + d s.
These finite possible cutoffs are declared before observation.
No later readback can revise the selected duration or response.

## Unchanged F_RC package and task

F_RC is a new numerical development package.
It is distinct from the paper's matrix response package F and from RC numerical conformance.
Its support is the actual capacitor voltage in [−0.1, 0.1] V at the response cutoff.
The same model, receiver, action, coefficients and task apply to every preparation arm.

The fixed response sets the left source to 1 V and the right source to 0 V for 1 s.
The analytic response is a V_cutoff + b, where a = exp(−2) and b = (1−exp(−2))/2.
The package predicts b from the fixed reference state zero.
It does not use prepared-state truth to improve that prediction.

Support bounds the analytic prediction error by 0.1 exp(−2) V, approximately 0.013533528324 V.
The declared native voltage defect limit is 0.005 V.
Their sum is less than the fixed terminal task tolerance of 0.02 V.
Keep those two error terms separate in the result.
Finite coefficient encodings retain their analytic expressions and conservative arithmetic treatment.

The default complete-chain deadline is 2.60 s from measurement sampling.
The deadline control is 1.80 s.
The preparation and response use one exclusive boundary-actuation resource in sequence.
A shorter deadline cannot authorize a replacement action after the original decision.
Physical experiment time and operational wall-clock limits are different quantities.

## Complete nested controls

Retain each of these ten scenarios for every assigned preparation:

| Scenario | Fixed change | Required interpretation |
|---|---|---|
| Nominal | Error +0.005 V, radius 0.01 V, availability 0.04 s | Test all three claims. |
| Coarse observation | Radius 0.25 V | Truthful information can remain inadequate for this consumer. |
| False coverage | Error −0.4 V, radius 0.01 V | Prospective admission cannot conceal oracle-falsified coverage. |
| Missing observation | No report | Retain the obstruction and downstream unevaluable outcomes. |
| Late observation | Availability 0.06 s | Refuse information unavailable at the decision cutoff. |
| Wrong units | mV with unchanged numerical values | No undeclared conversion can repair the handoff. |
| Wrong quantity | Source voltage instead of capacitor node voltage | Matching record shape cannot establish scientific meaning. |
| Wrong binding | Another source/model identity | Refuse substituted evidence. |
| Short deadline | Complete-chain deadline 1.80 s | Preserve adequate components and failed joined use separately. |
| Physical sensor request | Physical observation/metrology required | Stop at the unsupported prerequisite. |

For every admitted nominal decision, retain four preparation arms:

1. The selected zero-boundary discharge.
2. Unchanged preparation, with zero additional duration.
3. Wrong preparation, with left source 1 V and right source 0 V during the selected duration.
4. Insufficient preparation, with zero boundaries for half the selected duration.

Other admitted scenarios retain their selected arm.
Every refused scenario retains its terminal record.
At d = 0, coincident arms remain nested controls.
A control is not required to fail for every initial state.

Out-of-support response trajectories are separate exposed diagnostic assays.
Their endpoints cannot become admissible F_RC use.
`PROSPECTIVE_PACKAGE_USE` records attempted use under the committed interval.
The separate connection and joined states determine scientific admissibility.
The 3 V preparation must retain its finite-menu refusal.
A new duration, support interval, coefficient, action or refusal rule requires a distinct design identity.

## Numerical and operational bounds

Retain the matrix-exponential and backward-Euler views as nested numerical checks.
The output grid has intervals no larger than 0.01 s and includes every phase boundary.
The backward-Euler maximum step is 0.0001 s.
The voltage defect limit is 0.005 V.
The charge-rate residual limit is 0.002 A.
The independent scalar voltage defect limit is 10⁻¹⁰ V.
The independent boundary-current defect limit is 10⁻¹⁰ A.
Those separate limits preserve the quantities and their units.

The independent scalar oracle checks state, terminal voltage and source currents for the committed phases.
At segment boundaries, apply the native half-open action convention explicitly.
Keep numerical failure distinct from failed measurement, preparation and terminal-task claims.

Before native entry, prove the finite unit, scenario, arm, view and maximum-step census.
Use one worker.
Limit each unit output to 16 MiB and aggregate output to 256 MiB.
Require at least 64 MiB of free storage before each effect.
The operational admission budget is 600 s.
Before each new unit, the route refuses entry after that elapsed time.
An admitted unit finishes its finite native work without forced interruption.
The budget is not a hard process timeout.
An operational budget stop is separate from the scientific deadline control.

## Custody, recovery and stopping

Use the existing guarded artifact plane and task receipts.
Bind inputs, producing source, selected lock and actual numerical runtime to the retained result.
Authenticate every completed unit before result aggregation.
Recovery reuses completed observations and cannot repeat an uncertain native effect.

Retain every assigned unit, adverse result, refusal and numerical failure.
Keep original source identities when another checkout reads the result.
Development receipts create no issue, execution, reveal or qualification authority.

Physical sensing, sensor calibration, component metrology and fresh physical preparations remain unsupported.
That stop preserves the recursive question without manufacturing its missing premise.
General supplier search, arbitrary-depth execution and cross-substrate transport remain outside this route.

## References and research

The [manuscript](../../../../../paper/manuscript.md#from-a-failed-requirement-to-another-scientific-task) explains requirements, constructed connections and qualified composition.
The [original RC guide](../rc-ladder-response/guide.md) gives the numerical substrate and its separate conformance boundary.
The [architecture guide](../../../../../docs/development/architecture.md) identifies scientific, operational and runtime graph ownership.
