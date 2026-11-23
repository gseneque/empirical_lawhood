# Thermal RC dissipation and voltage memory

The [original scientific readout](../../records/thermal-rc-dissipation.md) identifies the source revisions, assigned roots and retained results. To export the complete public scientific record from a settled run, add `--portable` to the read command on the current release. This mode joins every original binary identity to its producing receipt. When executing an installed wheel, pass `--project-root` with the matching extracted source distribution on every call and select its recipe.

Use this workflow to acquire and assess the declared numerical population. Select the locked CPython 3.11.14 and NumPy 2.4.6 environment with SciPy 1.17.1, and a new external workspace. Run these commands from the checkout root with `WORKSPACE` set to that directory.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export OPENBLAS_CORETYPE=HASWELL NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
uv run --no-sync python -m empirical_lawhood.api.path_ensembles prepare --definition programmes/foundations/measurement-and-response/workflows/thermal-rc/experiment.json --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles run --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles read --workspace "$WORKSPACE"
```

Select `smoke.json` for the smaller exposed control. Numerical acquisition runs through the recursive investigation service. Development supplies a frozen assessment before evaluation starts on disjoint root IDs. Every acquisition has an original typed product and an authenticated binary array companion. The final reader reports original population and batch receipts. Use `recover` on the same workspace after an interruption. Source, numerical implementation, allocation, and parent identities are bound to the authored investigation.

The [correlation precision panel](correlation-precision.json) selects a fresh cohort and the same phase-specific finite-lag and zero-lag assessments. It acquires the three voltages at the six exact lags and their common origin. Select that definition in a separate workspace when measuring the statistical precision of the correlation estimator. The complete definition also measures the physical reverse path and voltage memory. Both definitions produce source-bound numerical development evidence under EL.
