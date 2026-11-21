# Retained dividing-ensemble flux

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for finite-slab reactive-flux preparation and assessment.
It preserves original equilibrium configurations, physical trajectories, costs and joint uncertainty.
Use it after the [equilibrium route](reference-equilibrium.md) returns the selected windows.

## Prerequisites

Use the selected [locked environment](../../../../../docs/using/environments.md) with `uv run --no-sync`.
Select an external artifact root, native work directory and fresh authoring destination.
Supply the complete [retained equilibrium analysis](reference-free-energy.md) selection and original trace carriers.
Keep all original receipt, source and current-access checks active.

The route measures a conditional classical-model quantity.
It does not establish chemical accuracy, equilibrium validity or biological prediction.
The [physical supplier specification](physical-rate-supplier-v1.md#physical-clock-prefactors-and-standard-states) owns those requirements.
Runpod and scientific execution still require their actual prerequisites.

## Select the surfaces and numerical controls

Use the records in `adapters.methods.rubisco_response.reactive_flux_records`.
Freeze `ReactiveFluxRule` before the outcomes when the experiment requires a prospective selection.
Retain its exact canonical bytes.
Later edits do not make exposed results fresh.

| Record | Required operands |
| --- | --- |
| `ReactiveFluxSurface` | Original ensemble, coordinate axis, center, half-width, direction, reactant/product basins, quantity, state definition and geometry criteria |
| `ReactiveFluxCriteria` | Configuration count, weight ESS, positive-flux error, plateau range, noncommitment, committor spread, timestep change and arithmetic limits |
| `ReactiveFluxControl` | An actual slab-width or coordinate alternative, original state correspondence and log-rate tolerance |
| `ReactiveFluxRule` | Complete equilibrium selection, surfaces, physical steps, common horizon, plateau times, thermal seed, momentum-pair count, allocations and assumptions |

Each equilibrium ensemble requires a selected surface.
The declared reactant and product basins must lie on opposite sides, outside the complete slab.
The original multivariate basin definitions remain unchanged.
Probability outside these basins remains part of the original equilibrium measure.
Its kinetic interpretation requires a separate state assessment.

A width control changes only the slab width.
A coordinate control changes the actual coordinate axis within the same original coordinate definition.
A changed label or dividing location alone is not an alternative coordinate.
Both controls retain the exact reference operator, stable states and physical quantity.
Every selected surface needs both controls for the conditional numerical assessment.
Missing controls remain `UNEVALUABLE`.

This version accepts distance and distance-difference dividing coordinates.
It refuses a periodic torsion as the dividing coordinate.
A global torsion side indicator has a second cut that this implementation does not measure.
Other retained coordinates can include torsions under their original conventions.

Select at least two distinct integration steps with the same physical horizon.
The reference steps are 0.5 fs and 0.25 fs.
Select at least three plateau times on both exact physical grids.
These times must resolve the intermediate kinetic plateau.
They are not wall-time limits.
An equilibrium correlation eventually decays beyond the kinetic plateau.

## Prepare the complete shooting population

Use `api.domain_composition.rubisco_response.reactive_flux`.
Supply `RetainedEquilibriumTrace` carriers in the original selection order.
Use the actual numerical assessor-source identity from the selected implementation.

```python
result = prepare_reactive_flux(
    rule=rule,
    sources=equilibrium_sources,
    assessor_source=assessor_source,
)
prepared = result["prepared"]
```

The preparation authenticates every original window and considers every retained sample.
It selects all samples inside any declared slab.
It reuses one physical shot when that configuration belongs to several surfaces.
A failed or absent equilibrium window prevents a successful-subset shot roster.
An empty slab remains an empty denominator.

For each selected configuration, the preparation draws unconstrained Cartesian Maxwell velocities with natural atomic masses.
Each draw has an exact antithetic partner with reversed velocity.
There is no center-of-mass projection, speed rescaling, mass repartitioning or selected-direction bias.
The phase record retains the original receipt, sample ordinal, step, array digests, thermal seed and NumPy version.
Equivalent Decimal temperature spellings do not change the random draw.
Every physical step starts from the same configuration and momentum member.

Independent scalar-coordinate and two-step derivative checks assess the local mass metric.
The preparation performs no reference-force evaluation.
The complete prospective preparation and analysis allocations are checked before original-result access.

## Author, execute and recover returned shots

```python
authored = author_reactive_flux(
    prepared=prepared,
    sources=equilibrium_sources,
    raw_sources=original_raw_source_records,
    project_root=project_root,
    work_directory=native_work_directory,
    artifact_writer=artifact_writer,
    output_dir=fresh_authoring_directory,
)
```

The author independently reconstructs the full preparation before it writes the children.
It retains `preparation.json` with the original receipt ancestry.
Each returned shot uses the existing [reference trajectory author](reference-trajectory.md).
Use the returned paths under `authored["shots"]`.
Do not construct task IDs or execution plans.

Execute and recover each returned child through the existing trajectory workflow.
The original native-subwork service owns entry, completion, uncertainty and retained failures.
An analysis read never repeats a force calculation.
For a preparation reread, use `read_reactive_flux_preparation` with the original equilibrium carriers and an explicit byte limit.

## Read the complete original population

Place the original equilibrium carriers first.
Append one `RetainedReactiveFluxShot` for every returned shot, in preparation order.
Bind its actual configuration, representation, phase bytes, result and native-subwork reader.
For an absent shot, supply `RetainedReactiveFluxShot(shot_id)`.
Absence is not proof of native nonentry.
An omitted carrier refuses the read.

```python
report, arrays = read_reactive_flux(
    selection=rule,
    sources=all_original_carriers,
    assessor_source=assessor_source,
)
exported = export_reactive_flux(
    selection=rule,
    sources=all_original_carriers,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/reactive-flux",
)
reread = read_reactive_flux_export(
    directory_relative_path="selected/reactive-flux",
    sources=all_original_carriers,
    artifact_writer=artifact_writer,
)
```

The closed package contains `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt`.
Its independent reread reconstructs all numerical outputs from the original custody.
Changed members or original bytes refuse the read.
Native failures retain their prefixes and costs.
They are not censored successful shots.

## Estimator and units

Let `s(x)` be the oriented coordinate relative to its selected center.
Let `h` be the half-width in the coordinate unit.
The finite slab is `-h <= s < h`.
Its indicator divided by `2h` approximates the dividing delta measure.
This is an implementation approximation, not an exactly constrained surface ensemble.

The original MBAR target weights `w_i` sum to one over all selected equilibrium configurations.
Let `P_A` be their reactant-basin probability and `P_slab` their slab probability.
For each slab configuration, the natural-mass Cartesian Maxwell law gives

```text
mu_i+ = E[max(sdot_i, 0)]
      = sqrt((R T / 1000) * sum_a |grad_a s|^2 / m_a / (2 pi)) * 10^13
mu+   = sum_slab(w_i mu_i+) / P_slab
nu+   = mu+ / (2h)
DeltaG_slab = -R T log(P_slab / P_A)
p = nu+ h_Planck / (k_B T)
k_TST = (P_slab / P_A) nu+
```

Here `R T / 1000` uses kJ/mol, masses use daltons, and physical velocities use nm/ps.
Cartesian derivatives use coordinates in angstroms.
The factor `10^13` converts the coordinate velocity to its unit per second.
The reported `DeltaG_slab` uses kJ/mol with the corresponding gas constant.
Its width dependence remains coupled to `nu+`.
It is not a dimensionful PMF density inserted into an Eyring formula.

For the complete `M` momentum members at each configuration,

```text
N(t) = sum_slab w_i [sum_m sdot_i,m(0) 1{s_i,m(t) > 0} / M]
k_RF(t) = N(t) / (2h P_A)
kappa(t) = N(t) / sum_slab(w_i mu_i+)
k_plateau = mean_selected_times k_RF(t)
```

The future indicator uses the product side of the dividing coordinate.
It is not a first-passage event count.
The finite-slab signed correlation is zero at time zero for antithetic momenta.
The reader does not force `kappa(0) = 1`.
Negative values and values above one remain visible and fail the selected plateau criterion.

First arrivals at the selected stable basins provide separate committor diagnostics.
The report retains uncommitted probability and the weighted spread of product-arrival probabilities around one half.
These finite-horizon diagnostics do not prove chemical commitment or exclude hidden coordinates.
Slab-width, coordinate and timestep comparisons retain their individual results.

## Joint uncertainty and evidence limits

The analysis reuses the original coupled circular-block starts and refits every selected window in each draw.
Each sampled configuration carries its complete momentum population and all physical-step variants.
Sites, momentum signs and shots add no independent units.
The joint vector contains slab barriers, log prefactors, log transmission, log rates and the original free-energy contrasts.
The readout retains covariance, simultaneous conditional intervals and every failed draw.
Unavailable entries have an explicit availability array.
They are not zero observations.

These intervals describe empirical block variation under the declared dependence assumptions.
They do not guarantee coverage of hidden equilibrium modes or unseen momentum tails.
Unresolved windows or nonpositive rate operands prevent a complete joint interval.
Geometry and mechanics violations remain negative findings.

Numerical conformance does not establish a physical rate.
The selected basins must represent the relevant metastable states.
The physical interpretation also requires time-scale separation, equilibrium coverage, force accuracy and the stated classical-nuclear approximation.
Quantum nuclear corrections, gas standard states, oxygen electronic transitions and biological applicability remain separate operands.
The downstream supplier must assess these requirements before it admits a paired enzyme forecast.

## References and research

Roux, B. (2022), [*Transition rate theory, spectral analysis, and reactive paths*](https://doi.org/10.1063/5.0084209).
Equations 4 and 5 give the flux-side and positive-flux factorization.
The finite-slab estimator above replaces their dividing delta measure with an explicit interval approximation.
The width checks assess that implementation choice.

Prinz, J.-H., Chodera, J. D. and Noé, F. (2014), [*Spectral Rate Theory for Two-State Kinetics*](https://doi.org/10.1103/PhysRevX.4.011020).
This work explains reaction-coordinate and observation limits in kinetic rate estimation.
It supports the separation of numerical plateau diagnostics from physical kinetic admission.
