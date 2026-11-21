# Assess retained physical rates and complete processing

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for conditional rate assessment from original physical first passages.
It retains competing exits, complete processing times, gas concentration, joint uncertainty and failed observations.
Use it after the [first-passage route](physical-first-passages.md) supplies the selected original paths.

## Prerequisites and selection

Use the selected [locked environment](../../../../../docs/using/environments.md) with `uv run --no-sync`.
Select an external artifact root and a fresh output directory.
Keep the original configurations, molecular representations, phase payloads, results and native-subwork readers.
Supply every original carrier, including missing results and parents with zero offspring.
Keep original source and outcome-access checks active throughout the read.

Use `physical_rate_records` under `adapters.methods.rubisco_response` for the rate selection.
Freeze its criteria and dependence groups before outcomes when the design requires prospective assessment.
A later selection remains retrospective.
The selected record does not establish a cutoff, statistical independence or scientific authority.

| Record | Required operands |
| --- | --- |
| `PhysicalRateCase` | Original ensemble, complete entry-history census, physical quantity and exact physical-grid observation times |
| `PhysicalRateCriteria` | Minimum group and probability support, cumulative-probability error, dwell/history log-rate limits and arithmetic tolerance |
| `PhysicalRateRunBinding` | Every original run within one condition and dependence group |
| `PhysicalRateRunGroup` | Corresponding original runs across every selected paired condition and control |
| `PhysicalRateControl` | Integration-step, bath-friction or dissolved-concentration comparison, its source and log-rate tolerance |
| `PhysicalRateSelection` | Original passage selection or weighted campaign, complete cases, controls, groups, resampling rule and analysis allocation |

Each group must contain every selected condition.
Each original run must occur in exactly one group.
Multiple runs within one group receive equal weight.
Groups also receive equal weight.
Sites, descendants and repeated frames remain nested within those declared groups.

The observation grid must end at the complete original horizon.
Its boundaries must coincide exactly with physical integration steps.
Every selected competing exit remains in the rate denominator.
An `OTHER` exit cannot be removed to improve productive commitment.

## Read or export the rate assessment

Use `api.domain_composition.rubisco_response.physical_rates`.
Pass the complete original carrier tuple used by the selected passage or weighted-campaign reader.

```python
exported = export_physical_rates(
    selection=rate_selection,
    sources=original_path_carriers,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/physical-rates",
)
```

Use `read_physical_rates` when publication is unnecessary.
Export performs the original read itself.
It returns `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt` paths.
The package retains original receipt ancestry, numerical provenance, every path and every original cost.

Call `read_physical_rate_export` with the returned relative directory, original carriers and artifact writer.
It authenticates the complete package and reconstructs the rate assessment from original observations.
It makes no new force evaluation or native retry.
Changes to original bytes during analysis refuse the return.

The reader checks the selected projection and analysis allocation before original contact.
The shared array transport retains its 64 MiB expanded bound and 256-member limit.
Exceeding an allocation refuses the complete analysis.

## Conditional competing-hazard reduction

The physical event time is the original residence-confirmation time.
It includes any selected residence delay.
Weighted continuation preserves the cumulative physical clock across all segments.
Resampling contributes no molecular time.

For each path, count physical intervals until its confirmed first event or intact selected horizon.
Let `R` be their weighted sum.
Let `D_j` be the weighted observed event count for cause `j`, and let `D = sum_j D_j`.
For a constant competing-hazard model with physical step `dt`, use:

```text
q        = D / R
lambda   = -log(1 - q) / dt
lambda_j = (D_j / D) * lambda
S(t)     = exp(-lambda * t)
F_j(t)   = (lambda_j / lambda) * (1 - S(t))
```

The weighted estimating criterion is not an independent-particle likelihood for weighted descendants.
Exact rational weights and score operands remain in the report.
Decimal logarithms use sufficient precision to resolve the exact rational subtraction.
An independent assessment integrates the retained survival curve and checks the competing-transition equations.

No observed exit, an unresolved substep rate or missing computational weight prevents a finite identified fit.
An unobserved cause remains `None`.
It does not become an exact zero rate or proof of irreversibility.
Computational truncation, failed mechanics and missing continuations are not independent censoring.
Their weights cannot be removed or renormalized.

A complete, mechanically acceptable horizon without an event supplies administrative censoring for this conditional model.
An observed event can remain usable after a later original failure.
That failure and its cost remain in the original census.

The reported exponential mean is a model extrapolation.
It is not the reciprocal of the censored empirical mean.
The original finite-horizon bounds remain available beside this reduction.

## Dwell, history, step and bath assessment

The reader compares observed survival and every cause-specific cumulative probability with the fitted model.
It also fits the selected dwell intervals and compares their cause-specific log rates.
Each selected entry-history stratum receives a separate comparison with the pooled fit.
One history cannot establish history invariance.
Insufficient event mass, at-risk mass or run groups leaves the corresponding check unevaluable.

Step controls must preserve the exact reference operator, entry distribution, event definitions and physical horizon.
They preserve residence time in seconds by refining residence steps with the integration grid.
Controls also preserve the selected dwell-time and entry-history census.
Bath controls must preserve those operands while varying actual declared friction.
A stochastic physical model requires its bath control.
A successful numerical check does not establish that Langevin friction reproduces molecular transport.

All cases require a step-refinement control before conditional rate acceptance.
Association cases also require concentration scaling and a retained concentration census.
Finite negative checks remain `FALSIFIED`.
Missing checks remain `UNEVALUABLE`.
These findings describe the selected empirical tolerances, not a universal test of memorylessness.

## Gas concentration and access

Use `prepare_periodic_gas_concentration` from the same public API.
Supply the actual periodic prototype, complete representation, gas species and complete free/bound gas-residue census.
Bind the source for that free/bound assignment.
The preparation validates the original molecular model and returns `PeriodicGasConcentration`.

For box volume `V_A3` and `N_free` selected gas molecules:

```text
c_uM = N_free * 10^33 / (602214076000000000000000 * V_A3)
```

The Avogadro constant and volume conversion are exact.
The record retains exact rational volume and concentration.
Its `decimal_uM` property supplies the declared 80-digit Decimal projection.
Bind that value and the returned record identity in `PassageEnsemble`.
Include the record in `PhysicalRateSelection.gas_concentrations`.

The reader reconstructs the complete gas census and volume from original sources.
Missing concentration evidence prevents conditional association acceptance.
Box particle density does not establish accessible solvent volume, a free bulk reservoir or an assay concentration.
Free/bound assignment, finite-cell corrections and dilute-limit validity remain physical requirements.

Concentration controls compare association rates divided once by sourced uM concentrations.
Other cause-specific rates retain their unimolecular units.
The controls preserve numerical and electronic conventions and retain the declared molecular correspondence source.
Agreement at selected concentrations does not establish an unmeasured zero-concentration limit.
Pressure, bicarbonate and total added gas cannot replace free dissolved concentration.

## Joint uncertainty and incomplete resamples

One PCG64DXSM draw selects complete dependence groups across every condition.
All descendants, sites, histories and controls within a selected group remain together.
The readout retains every group index, Decimal rate realization and unavailable cause.
Arrays retain the binary64 rate projection and a separate observation mask.
A zero array placeholder with a false mask is not an observed zero rate.

The conditional simultaneous interval uses the selected quantile of the largest absolute joint log-rate deviation.
The reader retains the full joint log-rate covariance.
It does not combine unrelated marginal intervals.
If any resample lacks a required rate, the complete conditional interval remains unavailable.
No failed resample is discarded or redrawn.

These empirical bootstrap intervals do not certify coverage, preparation independence or physical-model accuracy.
Numerical error, chemical alternatives, ensemble validity and biological applicability require their own assessment.

## Complete processing and encounter networks

Use `physical_rate_network_records` for `PhysicalSupplierSelection` and its networks.
Each transient state binds one original rate ensemble and its entry-distribution source.
Every selected event must occur exactly once as an outgoing edge.
The edge's target definition must equal the original event's physical definition.

| Record | Required operands |
| --- | --- |
| `PhysicalNetworkState` | Chemical definition, outgoing ensemble or terminal outcome, released product counts and substrate readiness |
| `PhysicalNetworkEdge` | Source, target and original ensemble/event rate operand |
| `PhysicalNetworkEntry` | Exact initial-state probability |
| `PhysicalRateNetwork` | Complete states, edges, initial distribution, physical-time queries, assessment tolerances and Arb precision |
| `PhysicalEncounterReduction` | Bulk association operand, complete encounter network, concentration queries and elimination criteria |

Carbon productive return requires two released PGA molecules and substrate-ready enzyme.
Oxygen productive return requires one released PGA, one released phosphoglycolate and substrate-ready enzyme.
A chemical `PRODUCTIVE` event alone cannot supply complete return.
Release counts must agree with actual release or substrate-ready events.
The initial-rate sink convention forbids hidden recapture of released products.
Missing reverse edges remain missing.

The exact finite network retains all chemical, release and return waits.
Let `T` be its transient generator, `B_j` its exit column and `alpha` its selected entry distribution.
The existing exact balance solver gives:

```text
(-T) m   = 1
(-T) m2  = 2m
(-T) p_j = B_j

mean_exit = alpha * m
P_j       = alpha * p_j
k_j       = P_j / mean_exit
```

Every backward equation and the complete absorption sum receive an exact check.
A nonabsorbing closed class refuses a finite exit mean.
The reader compares the complete exit law with the proposed constant-hazard reduction.
It checks the squared coefficient of variation and the selected initial-state dependence.
SciPy propagation is compared with independent Arb enclosures of the exact entered rational model.
The shared Arb precision owner preserves concurrent and nested precision settings.

Moment quotients remain conditional summaries when state reduction fails.
An `OTHER` outcome prevents the two-outcome productive/reverse reduction.
Its probability remains in the full denominator.
These checks do not qualify the underlying chemical state correspondence.

## Assess encounter elimination

The bulk association operand must represent bulk-to-encounter entry.
It cannot also occur as an internal encounter edge.
A bulk-to-product observation receives no second access multiplier.

Let `k_on` have units `uM^-1 s^-1`.
Let `P` be the encounter's productive probability and `tau` its complete mean residence time.
With escape back to the same declared bulk entry law:

```text
c_eliminated = k_on * P
mean_capture(C) = (1 / (k_on * C) + tau) / P
c_explicit(C) = 1 / (C * mean_capture(C))
```

An independently enlarged backward system retains bulk waiting and every encounter escape.
It must reproduce the same complete capture mean exactly.
The relative elimination error uses `c_explicit(C)` as its denominator.
The complete capture distribution also receives an Arb-enclosed comparison with the proposed eliminated exponential law.
Its time queries use the prospectively selected multiples of the proposed capture mean.

The familiar `k_on * k_chem / (k_off + k_chem)` follows for one encounter state with those two exits.
Additional spin, chemical or escape states remain in the network.
Unresolved additional exits prevent this reduction.
Finite-concentration failure remains visible and does not become a dilute association coefficient.

## Export the complete supplier

Use `api.domain_composition.rubisco_response.physical_suppliers`.
Call `export_physical_suppliers` with the supplier selection and the same complete original carriers.
Use the arguments shown for rate export and a fresh supplier destination.
It returns the same five closed member names.

Call `read_physical_supplier_export` to authenticate and reconstruct the complete package.
The source rate analysis remains embedded with its full observations, failures and costs.
Every original joint rate draw is propagated through the complete network.
Exact rational network realizations and unavailable operands remain in the readout.
The bootstrap conditions on the selected network and entry laws.
It does not repeat their physical-model assessment or create additional independent evidence.

## References and research

Zhang, Jasnow and Zuckerman (2010), [*The weighted ensemble path sampling method is statistically exact for a broad class of stochastic processes*](https://arxiv.org/abs/0810.1963).
This work gives the path-resampling basis.

Suárez and colleagues (2016), [*Estimating first-passage time distributions from weighted ensemble simulations and non-Markovian analyses*](https://pmc.ncbi.nlm.nih.gov/articles/PMC4815309/).
This work describes history dependence and the limitations of simple kinetic reductions.

SciPy, [`scipy.linalg.expm`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html).
The numerical propagation uses the documented scaling-and-squaring method.

Python-FLINT, [`arb_mat.exp`](https://python-flint.readthedocs.io/en/latest/arb_mat.html#flint.arb_mat.exp).
The independent enclosure uses the installed locked library and the selected precision.
Its enclosure applies to the entered mathematical model, not to physical-model error.
