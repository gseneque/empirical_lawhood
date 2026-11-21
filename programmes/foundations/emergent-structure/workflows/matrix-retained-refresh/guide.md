# Assess one retained Matrix operator refresh

SPDX-License-Identifier: CC-BY-4.0

This guide gives the procedure for the SCI01 retained comparison.
It compares fixed-basis response models with one causal operator update.
Read the [scientific protocol](../../records/matrix-sci01-retained-refresh-v1.md) before the first calculation.

## Prerequisites

Use the [locked base environment](../../../../../docs/using/environments.md).
Select the current checkout with `--project-root` and an explicit guarded operator profile.
Use the original completed E4 development child returned by the [programme workflow](../matrix-programme/guide.md).
Its complete receipts and current original input access must remain available.
Select new calculation, assessment and attempt directories on the profile's storage.
Reserve at least 600 MiB above the profile's free-space minimum for the compact successor outputs.

Set numerical thread counts before either command:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 POLARS_MAX_THREADS=1
```

## First action

Publish the separately bound protocol and calculate the retained comparison:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /absolute/selected-checkout \
  --operator-profile /absolute/inputs/operator-profile.json \
  campaign matrix-retained-refresh \
  --original-dir /absolute/original-e4-development \
  --output-dir /absolute/selected-storage/sci01 \
  --attempt-dir /absolute/selected-storage/sci01-calculation-attempt
```

Use the returned `calculation_directory` in the independent assessment:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /absolute/selected-checkout \
  --operator-profile /absolute/inputs/operator-profile.json \
  campaign matrix-retained-refresh-assess \
  --original-dir /absolute/original-e4-development \
  --calculation-dir /absolute/selected-storage/sci01/calculation \
  --output-dir /absolute/selected-storage/sci01-assessment \
  --attempt-dir /absolute/selected-storage/sci01-assessment-attempt
```

## Outputs and stops

The first command publishes the exact protocol before the numerical work.
Its calculation contains all 144 summaries, 36 usable array operands, source custody, producing provenance and costs.
The independent command publishes its decision record, complete case and equal-group summaries, endpoint channels, finite pairs and equation residuals.
Both commands commit their exact member census with the existing retained-analysis custody owner.
Keep the protocol parent directory with its calculation child.

An incomplete original publication, denied current access, changed member or failed equation stops the operation.
An unavailable scientific construction remains an unresolved finding.
Keep failed attempts and select a different output directory after a repair.
These commands acquire no native trajectories and fit no statistical model.

Interpret H64 as primary and H128 as secondary.
Preserve the 108 `NO_ORIGIN` cases and four usable independent groups.
Use the method decision with its weak-channel, cancellation and cost findings.
Select molecular tolerances and information costs in the molecular consumer's own scope.
The retained result supplies no molecular admission or SCI02 execution authority.

## Export the three matched analyses

Use this separate [analysis specification](../../records/matrix-sci01-matched-accounting-v1.md) after the independent SCI01 assessment.
Select the same locked environment, numerical thread limits and explicit guarded profile.
Keep the original calculation and assessment directories available.
Reserve at least 250 MiB above the profile's free-space minimum for exports and the retained attempt.

```sh
uv run --no-sync empirical-lawhood \
  --project-root /absolute/selected-checkout \
  --operator-profile /absolute/inputs/operator-profile.json \
  campaign matrix-retained-matched \
  --original-dir /absolute/original-e4-development \
  --calculation-dir /absolute/selected-storage/sci01/calculation \
  --assessment-dir /absolute/selected-storage/sci01-assessment \
  --output-dir /absolute/selected-storage/sci01-matched \
  --attempt-dir /absolute/selected-storage/sci01-matched-attempt
```

The command publishes the separate protocol before calculating its three analyses.
Use the returned `analysis_directory` to open `report.html` and the complete JSON/CSV exports.
`source-bindings.json` indexes bounded per-case exports of retained inputs and derived discrete maps.
The output includes the 48 unavailable pairs and both numerically evaluable and descriptive-only cell counts.
All counts retain four independent usable groups.

The three analyses are the matched-cell reversal census, signed error-alignment accounting and post-checkpoint representation accounting.
The command reuses retained evidence without new acquisition, fitting, basis construction or another update.
It verifies signed identities and reconstructs saved states through independent BAOAB substeps.
Current original access, source mismatch, missing members or failed arithmetic checks stop publication.
Keep failed attempts and choose a fresh output directory after a repair.

## References and research

The [SCI01 specification](../../records/matrix-sci01-retained-refresh-v1.md) owns the mathematical operands and stopping rule.
The [results guide](../../../../../docs/using/results-and-failures.md) owns retained attempts and original-result access.
