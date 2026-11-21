# Retained equilibrium free energies

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for joint free-energy analysis of retained equilibrium windows.
It preserves the complete window census, original costs and correlated sampling uncertainty.
Use it after the [original equilibrium route](reference-equilibrium.md) returns its selected attempts.

## Select the complete operands

Use the selected [locked environment](../../../../../docs/using/environments.md) with `uv run --no-sync`.
Select an external artifact root and a fresh output directory.
Supply each original configuration, complete representation, phase bytes, result and native-subwork reader.
Keep the original source and current-access checks active throughout the read.

Use `None` for a result that is not supplied.
This absence does not establish that its native task was never entered.
A failed attempt retains its original prefix and completion costs.
It cannot supply a complete-window estimate.
Every selected trace remains in the denominator.

One ensemble has one exact reference-operator selection and one temperature.
This identity includes the molecular model, partition, cell, electronic settings, MM settings and numerical engine.
All its windows use the same ordered coordinates, units and periodic-image convention.
Bias centers and constants can differ.
An explicitly unbiased window is permitted.

The coordinate definition uses an original `UmbrellaWindow` and `ReferenceBiasConvention`.
Its historical Metropolis settings are not executed.
The actual equilibrium acquisition owns the sample schedule, thermostat and random stream.
Different materials or reference operators require separate ensembles.
The analysis never substitutes a WT reference energy into an I95M configuration.

## Freeze the numerical and dependence selections

Use the records in `adapters.methods.rubisco_response.equilibrium_reweighting_records`.
Select `EquilibriumReweightingSelection` before the outcomes when a prospective analysis is required.
Retain its canonical bytes with the original experiment selection.
A retrospective selection remains retrospective.

| Record | Required selection |
| --- | --- |
| `ReweightingEnsemble` | Exact reference prototype, temperature, coordinate definition and complete basin census |
| `EquilibriumBasin` | One finite, half-open interval `[lower, upper)` per coordinate, in its declared unit |
| `ReweightingTrace` | Original acquisition configuration, ensemble, dependence group, block length and independent bias-geometry criteria |
| `BasinFreeEnergyContrast` | Complete signed basin terms, with coefficients that sum to zero separately within each ensemble |
| `EquilibriumReweightingCriteria` | Solver settings, weight ESS, overlap, block and split-window criteria, bootstrap settings and workspace allocation |

Basins must not overlap.
Probability outside their union remains a separate result.
A torsion uses the signed angular coordinate in the selected convention.
A region that crosses its branch requires separate declared regions and a suitable downstream aggregation.
An unobserved basin has no finite free energy.

Specify a dependence-basis source and the actual conditional sampling assumptions.
The reader does not infer independent biological units from trace names.
Members of one resampling group must have matching sample counts, sampling clocks and block lengths.
They receive the same block starts in every replicate.
Reused thermal random streams cannot belong to independently resampled groups.
Different groups are conditionally resampled independently under the declared assumptions.

The block length is a number of retained production samples.
It does not change the original prefix, sampling interval or sample count.
Select every numerical threshold explicitly.
These thresholds supply no physical-model or equilibrium authority.

## Read or export the analysis

Use the functions in `api.domain_composition.rubisco_response.equilibrium_reweighting`.
Construct one `RetainedEquilibriumTrace` carrier for every selected trace, in the selection's order.
This carrier binds existing records and custody ports.
It acquires no new scientific data.

```python
report, arrays = read_equilibrium_reweighting(
    selection=selection,
    sources=original_trace_carriers,
    assessor_source=assessor_source,
)
exported = export_equilibrium_reweighting(
    selection=selection,
    sources=original_trace_carriers,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/free-energy-analysis",
)
```

Use either read or export for the required action.
Export performs the authenticated read itself.
It returns the actual paths for `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt`.
The evidence record binds producing source, numerical provenance, original results and named-array identities.
The package inherits the original native receipts as lineage parents.

Call `read_equilibrium_reweighting_export` with the returned directory, original carriers and artifact writer.
It authenticates every closed-package member and the original native archives.
It reconstructs the numerical readout and compares all named arrays.
It performs no force evaluation, thermal sampling or producing-bias call.
Changed bytes, missing siblings and substituted receipt ancestry refuse the read.

The current named-array transport has a 64 MiB expanded bound and at most 256 members.
The complete prospective census is checked before any original result is opened.
The selected workspace bound includes a conservative estimate for sample projections, fitting and resampling.
It is not a whole-process RSS guarantee.
An exceeded allocation refuses the complete analysis instead of omitting windows or samples.

## Complete potentials and conditional estimates

For one exact reference ensemble, the reduced potential of window `k` at retained sample `n` is

```text
u_kn = [E_ref(x_n) + B_k(q(x_n))] / (R T)
B_k  = sum_a 0.5 k_ka delta(q_a, center_ka)^2
```

Distances use angstrom and torsions use radians.
Torsion displacements use the shortest signed angular difference.
The independent scalar geometry owner reconstructs coordinates from original complete atom arrays.
The analysis retains original energies in hartree and kJ/mol, sample evaluations and coordinate digests.
It retains every selected window's bias at each projected sample, including an intact failed prefix.

The common `E_ref(x_n)/(R T)` is a per-column gauge.
It cancels from the MBAR equations and unbiased target weights.
The solver uses `B_k(q(x_n))/(R T)` to avoid subtracting large enzyme energies.
The original reference contribution remains separately retained.
This cancellation is permitted only after exact common-operator and temperature checks.

The existing MBAR owner solves

```text
f_i = -log sum_n exp(-u_in) / sum_k N_k exp(f_k - u_kn)
```

The gauge fixes the first sampled window's free energy to zero.
`N_k` is the actual complete production-sample count of its selected trace.
Correlation diagnostics never replace these counts with effective counts.
An independent evaluation checks the estimating equations at the returned solution.
Nonconvergence remains an unresolved numerical result.

For the unbiased target, normalized weights are proportional to

```text
w_n proportional to 1 / sum_k N_k exp(f_k - B_k(q(x_n))/(R T))
P_b = sum_n w_n 1[x_n in basin b]
G_b = -R T log(P_b)
```

Signed contrasts sum the declared coefficients times `G_b`, in kJ/mol.
Each ensemble's coefficients must cancel its free-energy gauge.
This supports paired differences and joint WT/I95M, M1/V1 contrasts.
It does not convert a basin difference into an activation barrier or physical rate.

## Correlation, overlap and joint uncertainty

The readout retains window-weight ESS, target-weight ESS and the complete MBAR overlap matrix.
The overlap graph requires both directed overlaps to meet the selected threshold.
Disconnected support fails that numerical criterion.
Weight ESS is not biological replication or a temporal decorrelation certificate.

Correlation diagnostics include reference energy, selected coordinates, basin indicators and weighted basin fluctuations.
Torsions use sine and cosine to avoid a false discontinuity at the signed-angle branch.
The FFT autocovariance uses an initial positive, monotone sequence of adjacent lag pairs.
Constant observables and unresolved positive tails remain explicit.
This finite-series diagnostic does not prove stationarity or exclude hidden slow coordinates.

The selected block length must exceed the declared multiple of the largest measured statistical inefficiency.
The required complete-block count is checked separately.
Both original half-windows are refitted, with their signed contrast disagreement retained.
The procedure does not select a more favorable production prefix after this comparison.

Circular block resampling selects uniform starting indices and wraps at the end of each original series.
Each replicate retains exactly the original sample count.
All members of a dependence group share its block starts.
The readout retains every draw and every joint contrast vector.
It retains covariance and a simultaneous interval based on the maximum absolute contrast deviation.

Failed fits, disconnected resampled overlap and absent basin probabilities remain in the replicate census.
They prevent a complete joint interval.
They are never dropped to obtain a narrower interval.
The finite bootstrap interval is a conditional sampling estimate, not a guaranteed confidence enclosure.
Model alternatives, initial-state populations and chemical uncertainty require their separate evidence and joint composition.

## Costs and evidence limits

Every original completion retains its measured or unknown CPU, wall and memory costs.
GPU traces retain their original per-call cost assessment.
Nested costs are not summed twice.
The export records read-and-analysis CPU and wall time separately.
That scope excludes environment capture and publication overhead.

An intact partial or failed window supplies no complete-window fit.
Missing mechanics or independent bias-geometry criteria leave its statistical use unevaluable.
Source corruption refuses the read, including corruption after an earlier numerical failure.

`SATISFIED` applies only to the selected numerical sampling diagnostics.
Equilibrium preparation, hidden-coordinate convergence, numerical refinement and chemical-model accuracy remain separate requirements.
Gas concentration, standard-state corrections, committors, transmission, spin transitions and physical clocks are not supplied by this analysis.
Biological prediction and specificity preservation remain separate findings.

## References and research

Shirts and Chodera (2008), [*Statistically optimal analysis of samples from multiple equilibrium states*](https://arxiv.org/abs/0801.1426).
This paper supplies the MBAR equations and explains the effect of correlated sampling on uncertainty.

Geyer (1992), [*Practical Markov Chain Monte Carlo*](https://doi.org/10.1214/ss/1177011137).
This paper supplies the initial-sequence autocorrelation method.
Its theoretical conditions do not establish convergence for the selected molecular trace.

Politis and Romano (1991), [*A Circular Block-Resampling Procedure for Stationary Data*](https://statistics.stanford.edu/technical-reports/circular-block-resampling-procedure-stationary-data).
This report supplies the circular-block resampling construction.
Stationarity and the declared dependence structure remain assumptions of the conditional uncertainty calculation.
