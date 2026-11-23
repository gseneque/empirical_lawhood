# Matrix memory and composed pulse response

SPDX-License-Identifier: CC-BY-4.0

Which available history or kernel delivers the signed and joint future of a blind two-pulse continuation? One independent unit is one matrix preparation. Select the complete [scientific definition](experiment.json) or the [small numerical control](smoke.json). The numerical study uses the source-bound recursive lifecycle with disjoint development and evaluation roots. Its retained record identifies the original parent, issued forecast and reference measurement for every evaluation batch.

The completed evaluation and its source identities are available in the [scientific readout](../../records/matrix-projected-memory.md).

Select the locked CPU environment and a new external workspace. From the matching checkout or source distribution run the following commands. With an installed wheel, add `--project-root` pointing to the matching source distribution.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export OPENBLAS_CORETYPE=HASWELL NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
uv run --no-sync python -m empirical_lawhood.api.path_ensembles prepare --definition programmes/foundations/emergent-structure/workflows/matrix-projected-memory/experiment.json --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles run --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles read --workspace "$WORKSPACE" --portable
```

The forecast operation consumes the released observation and frozen model. The native reference operation requires the original private prefix and the previously published prediction. `recover` resumes unsettled work on the same workspace. The portable read joins the binary companions and their receipts and returns the uncertainty, assigned census and scientific decision.

Sixteen development families, 64 training families, 16 model-selection families and 16 band-calibration families precede 128 independent evaluations. The learned forecasts see single pulses during training. They issue all three horizons of the two-pulse composition at the cutoff. The original read contains every model, score and band. For the finite Hankel spectra, harmonic force check, shuffled past control and horizon-wise coverage on the same original records, run the supplementary read below. It acquires zero new native futures.

```bash
uv run --no-sync python -m empirical_lawhood.api.path_ensembles diagnose --workspace "$WORKSPACE"
```
