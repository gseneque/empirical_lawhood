# Algebra and directional passive history analysis

SPDX-License-Identifier: CC-BY-4.0

Programme: [Emergent structure — stochastic matrices](../../README.md).

This workflow produces or imports declared six-matrix histories, then calculates either approximate-algebra diagnostics or directional passive prediction. Use the base locked NumPy/SciPy environment with `uv run --no-sync`. Geometry-scan success, an identified factor and a selected-event result are unnecessary prerequisites. The [operative protocol](../../records/matrix-history-analysis-v1.md) fixes the mathematical and sampling contracts.

## Select numeric inputs

Copy `allocation.json`, [source-current.json](source-current.json) and either [algebra-current.json](algebra-current.json) or [passive-current.json](passive-current.json) to your working area. All supplied seeds are exposed examples. The 256 independent histories form four ordered families of 64 roots; PRIMARY/FINE views and time samples are nested. Family labels and history IDs do not change numeric draws. The public master 706256, original history streams and explicitly declared prior consumed seeds cannot be relabelled into proposed new evidence. A proposed allocation still grants no freshness, qualification or execution authority.

The current development configurations bind producing code and lock; both analysis selectors embed the same exact source. Regeneration preserves the complete allocation and all exposed draws and creates no new scientific units or qualification. Retained scientific inputs and results keep their original exact bytes in their own custody.

Create an explicit allocation from your numeric master, then derive current source/code/lock identities without hand-editing hashes:

```bash
uv run --no-sync empirical-lawhood campaign matrix-history-allocation \
  --allocation-id study.history.allocation --namespace study.history \
  --master-seed YOUR_NUMERIC_MASTER --output /work/history-allocation.json
uv run --no-sync empirical-lawhood --project-root /selected/checkout \
  campaign matrix-history-source-config --config-id study.history.source \
  --allocation /work/history-allocation.json --output /work/history-source.json
```

Bind declared prior effective PCG64DXSM seeds in the allocation before producing new histories. Every purpose consumes the high 128 bits of its full SHA-256 operand; differing unused bits cannot supply independence. Preparation/autonomous driver and fine-bridge purposes are distinct. Edit the analysis selector to contain the newly derived source record, then use `config validate`/`config prepare` with `matrix-history-analysis`. Allocation and source consumers are `matrix-history-allocation` and `matrix-history-source`.

## Produce or import histories

Source production is an explicit native operation. Select guarded storage with the normal operator profile:

```bash
uv run --no-sync empirical-lawhood --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json campaign matrix-history-source-export \
  --input /work/history-source.json --allocation /work/history-allocation.json \
  --relative-root studies/history-source --root-index 0 \
  --attempt-dir /work/new-source-attempt
```

Repeat `--root-index` to acquire selected declared roots; omit it to request all 256. Full acquisition is a scientific campaign and was not performed as part of software verification. Each paired history retains native positions, momenta, couplings and both complete clocks. It occupies about 9.5 MB before compression; a full bank needs several gigabytes. Inputs are published before native contact. Per-root `hNNN/receipt.json` is the completion marker. `--recover` authenticates completed receipts without reacquisition. Any published incomplete root without its receipt refuses native retry: preserve it and select a new explicit destination. Cancellation never invents a completed trajectory.

Researchers with saved data can use the public API `export_matrix_history_arrays(destination=..., config=..., allocation=..., root_index=..., arrays=...)` to create bounded `arrays.npz` and `operand.json`. Both native views must contain the exact 1025/2049 phase-space states, coupling schedules and clocks. Import with `campaign matrix-history-import --input SOURCE --allocation ALLOCATION --operand OPERAND --arrays ARRAYS --relative-root SELECTED_ROOT`. Imported arrays are marked `SUPPLIED_EXPOSED_ARRAYS`; byte authentication does not attest native production or reconstruct an original historical source chain. Pickle/object arrays, undeclared members, changed clocks/couplings, expansion above 64 MiB and wrong source/root identities refuse before calculation.

## Calculate, retain and read

```bash
uv run --no-sync empirical-lawhood --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json campaign matrix-history-analyze \
  --input /work/algebra.json --allocation /work/history-allocation.json \
  --source-root studies/history-source --relative-root studies/algebra-result \
  --attempt-dir /work/new-analysis-attempt
uv run --no-sync empirical-lawhood --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json campaign matrix-history-result \
  --input /work/algebra.json --relative-path studies/algebra-result/receipt.json
```

Select `passive.json` and a distinct destination for passive prediction. All 256 root roles remain in the report. Both-absent source receipt/manifest pairs yield UNENTERED roots and an UNEVALUABLE cohort; a partial/corrupt pair refuses. Missing roots keep their full requested sample denominator. No family median is reported as complete unless all 64 assigned roots contribute. `--recover` verifies completed analysis artifacts without repeating spectra, propagation or native work. Interrupted array output without its root result refuses automatic recalculation.

Each result retains `config.json`, `allocation.json`, per-root `arrays.npz`/`operand.json`/`result.json`, `columns.json` and final `receipt.json` with current physical publications and source receipt locators. Result reading authenticates source and result bytes, code/lock identities, column meanings and complete sample census. The CLI prints a bounded summary; use the typed array manifest and column contract to inspect the full scientific data. The final receipt is exposed descriptive evidence and grants no qualification.

The X and Y `band_ratio` columns retain the pinned source definition λ3/λ4, with eigenvalues in increasing order. `mean_slow_rate` separately reports the mean of the lowest three eigenvalues. A strict third/fourth spectral gap determines whether the sector is identifiable.

## Interpret the diagnostics

Algebra results retain all 15 eigenvalues, slow projectors, separate X/Y and joint spectra, Lie/product leakage and constructive-factor diagnostics. An unidentifiable slow sector retains its spectrum and explicit missing-factor masks. Original states and centered fitted-commutant-altered states occupy separately labelled rows. The dense role is the joint-decrease family's zero-based slot 18, selected before seeds; its fresh trajectory is not the old outcome-selected excursion. Absence of that excursion is valid and triggers no replacement search.

Passive results retain origin-only causal forecasts and their seals separately from actual operators, realised directions and future oracles. Full/slow/fast/worst increment losses have the original normalization; unresolved rank and complete singular-value spectra remain visible. Average the four cohort origins within each history, then take family medians separately for each numerical view. Dense extra origins/horizons/kappas do not enter that cohort average. These results establish neither a significance claim nor a uniform predictive response law.


## Declared retained-analysis programme

The registered `matrix.history.descriptive-programme` facade uses the same
`analyze_matrix_histories` and `read_matrix_history_analysis` owners through the
common experiment programme service. Copy [programme.json](programme.json) and
[programme-sources.json](programme-sources.json); copy `allocation.json` and `algebra-v5.json` beside them. The ordinary source
selector authenticates those original records, while the concise specification
pins their exact identities and selected retained receipt paths. E1 findings are never an input
or a success gate.

The example selects `READ_RETAINED` with an intentionally replace-with-actual
result path and exposed original configuration. Select the actual existing
result directory and its original source receipt locators. `ANALYZE_RETAINED`
uses explicitly selected current compatible source configuration and actual
source receipts; absent roots remain unentered in the complete 256-root result.
Every family and nested view retains its original meaning. Completed recovery
reads actual receipts without recalculating. Incomplete recovery uses only the
existing owner's explicit recovery path and requires the original selected
implementation; interrupted output without a root receipt still refuses.

Select your source and storage explicitly. Replace the example paths with your actual copied inputs and returned directories:

~~~sh
uv run --no-sync empirical-lawhood --project-root /selected/checkout --operator-profile /absolute/work/operator-profile.json campaign experiment-explain --input /absolute/work/e2-programme.json --sources /absolute/work/e2-sources.json
uv run --no-sync empirical-lawhood --project-root /selected/checkout --operator-profile /absolute/work/operator-profile.json campaign experiment-author --input /absolute/work/e2-programme.json --sources /absolute/work/e2-sources.json --source-snapshot /absolute/work/implementation.json --environment-id main --workers 4 --output-dir /absolute/work/e2-programme
uv run --no-sync empirical-lawhood --project-root /selected/checkout --operator-profile /absolute/work/operator-profile.json campaign experiment-read --authoring-dir /absolute/work/e2-programme --allow-partial
uv run --no-sync empirical-lawhood --project-root /selected/checkout --operator-profile /absolute/work/operator-profile.json campaign experiment-run --authoring-dir /absolute/work/e2-programme --workers 4
uv run --no-sync empirical-lawhood --project-root /selected/checkout --operator-profile /absolute/work/operator-profile.json campaign experiment-recover --authoring-dir /absolute/work/e2-programme --workers 4
~~~

This facade performs no native acquisition. `ACQUIRE_AND_ANALYZE` reports the
precise missing parallel lowering for the existing serial history producer;
it does not advertise four-worker native execution. The dedicated allocation,
export/import and production commands above remain available with their original
contracts. Source or result completion grants no scientific qualification.
