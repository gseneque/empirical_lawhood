# Six-matrix dissipation and physical reversal

The [original scientific readout](../../records/matrix-path-thermodynamics.md) identifies the source revisions, assigned roots and retained results. To export the complete public scientific record from a settled run, add `--portable` to the read command on the current release. This mode joins every original binary identity to its producing receipt. When executing an installed wheel, pass `--project-root` with the matching extracted source distribution on every call and select its recipe.

Use this workflow to acquire and assess the declared numerical population. Select the locked CPython 3.11.14 and NumPy 2.4.6 environment with SciPy 1.17.1, and a new external workspace. Run these commands from the checkout root with `WORKSPACE` set to that directory.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export OPENBLAS_CORETYPE=HASWELL NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
uv run --no-sync python -m empirical_lawhood.api.path_ensembles prepare --definition programmes/foundations/emergent-structure/workflows/matrix-path-thermodynamics/experiment.json --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles run --workspace "$WORKSPACE" --workers 8
uv run --no-sync python -m empirical_lawhood.api.path_ensembles read --workspace "$WORKSPACE"
```

Select `smoke.json` for the smaller exposed control. Numerical acquisition runs through the recursive investigation service. Development supplies a frozen assessment before evaluation starts on disjoint root IDs. Every acquisition has an original typed product and an authenticated binary array companion. The final reader reports original population and batch receipts. Use `recover` on the same workspace after an interruption. Source, numerical implementation, allocation, and parent identities are bound to the authored investigation.

The [preparation precision panel](preparation-precision.json) selects independent Maxwell preparations for the hot and equal-temperature slope tests. It uses the same native step, physical windows, nested resolutions and boundary-density calculation as the complete experiment. Select its definition in a separate workspace. The complete definition separately supplies forward cycle, independent terminal bank, physical reverse and fixed-coupling paths. Both definitions have EL's numerical development evidence ceiling.
