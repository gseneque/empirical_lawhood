# Marked event consequences and compressed history

SPDX-License-Identifier: CC-BY-4.0

How much early event-consequence information survives compressed histories for the late site count? One independent unit is one marked history. Select the complete [scientific definition](experiment.json) or the [small numerical control](smoke.json). The numerical study uses the source-bound recursive lifecycle with disjoint development and evaluation roots. Its retained record identifies the original parent, issued forecast and reference measurement for every evaluation batch.

The completed evaluation and its source identities are available in the [scientific readout](../../records/marked-event-response.md).

Select the locked CPU environment and a new external workspace. From the matching checkout or source distribution run the following commands. With an installed wheel, add `--project-root` pointing to the matching source distribution.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export OPENBLAS_CORETYPE=HASWELL NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
uv run --no-sync python -m empirical_lawhood.api.path_ensembles prepare --definition programmes/foundations/measurement-and-response/workflows/marked-event-response/experiment.json --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles run --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles read --workspace "$WORKSPACE" --portable
```

The forecast operation consumes the released observation and frozen model. The native reference operation requires the original private prefix and the previously published prediction. `recover` resumes unsettled work on the same workspace. The portable read joins the binary companions and their receipts and returns the uncertainty, assigned census and scientific decision.

The four-site two-particle chain uses the physical early site marks in [1,2) and site-0 counts in [3,4). The definition selects 256 development, 1,024 training, 512 calibration and 4,096 evaluation histories. The original read includes independent bounds on optimal compression loss and separately measured achieved predictor loss. The supplementary read replays every original history at all three grids and reports sensitivity of the estimated squared loss to time resolution.

```bash
uv run --no-sync python -m empirical_lawhood.api.path_ensembles diagnose --workspace "$WORKSPACE"
```
