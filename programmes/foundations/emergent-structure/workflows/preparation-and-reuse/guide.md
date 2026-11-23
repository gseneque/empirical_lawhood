# Reproduce the R23–R27 preparation and reuse experiments

SPDX-License-Identifier: CC-BY-4.0

The checkout includes the disclosed numerical operands, the original assignments and the code to recompute the five published readouts. Each study has a member manifest with original relative locations, byte counts and SHA-256 digests. The paired numerical views and the futures remain nested within each physical root. The public reproduction can run offline. [Scientific results](../../records/preparation-and-reuse-results.md) · [R24 assigned roots](../../records/preparation-and-reuse-r24-roots.md)

## Recompute the results

Use the locked six-matrix environment on Linux x86-64 with CPython 3.11.14 and NumPy 2.4.6. The native byte checks use Haswell OpenBLAS and NumPy X86_V3. Run from the checkout root and set `RESULTS` to a directory you select. [Environment selection and frozen CPU settings](../../../../../docs/using/environments.md#frozen-rc-numerical-input-profile)

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export OPENBLAS_CORETYPE=HASWELL NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
uv run --no-sync python scripts/reproduce_preparation_and_reuse.py --output-directory "$RESULTS"
```

The command writes one JSON report per study. A second invocation accepts an identical existing report and refuses a different one. Select one with `--study r23` through `--study r27`. Each report retains the complete root roster and the original scientific scope. The output records an exposed numerical reproduction with zero new acquisitions. [Checkout command](../../../../../scripts/reproduce_preparation_and_reuse.py)

| Study | Starting operands and computation | Published checks |
| --- | --- | --- |
| R23 | Replay original F, the pre-assay choices, matched native arrays and the Q/E scientific stages. Recompute every measurement and canonical phase report, the constructor crossing, the seven validity checks, physical contrasts and support-bypass diagnostic. The interrupted first Q8 and preprint E32 have their own censuses. | Q crossed on 7/8. N served 7,966/8,192 with full validity on E32. H and P served zero. Bypassing support gives 7,914, 7,966 and 7,951. |
| R24 | Recompute inference from the released scalar operands, paired bootstrap and ordered tests. Reapply the qualified lower at each actual handoff. Reconstruct all signed native, downstream and total errors, the costs of the chosen policies, and the interval counts. The original calibration, first 64 interrupted assignments, retained E64, disjoint E64 and historical comparison retain separate identities. | Composed versus cached joint service is 62 versus 60, then 58 versus 57. Each cohort has zero false-admission roots. Loss reductions are 33.79% and 32.60%. The ordered service tests give 0.25 and 0.50. |
| R25 | Reassess all 32 individual waveform measurements using the original master and bootstrap seeds. Recompute the physical port-2 contrast and the ordinary-bath comparison. | H, N and P cover 7,038, 7,333 and 7,050 pairs. The best observable gain over H is 295/8,192. The development decision kept the 128-root evaluation closed. |
| R26 | Resynthesise original per-root M1 and M7 analyses, both temperatures, both preparations and all three clocks. Join sibling handoffs and score the two sealed forecasts and the constant forecast on the same entries. Unknowns remain in their original denominators. | At T=2 on joint-increasing roots, causal versus fixed delivery is 97 versus 83 of 128, with 24 gains and 10 harms. Target service is 50 versus 58 of 512 assigned futures. |
| R27 | Read the 24 historical root panels under their original schema. Refit all nine schedules in the four held-out folds using the published original F. Check the inner and outer fit operands, choices, ratios, admissions and gates against the original audit, signed screen and freeze. | HOLD is adequate on 23/24. Zero roots can be rescued. The selector serves 5,966 versus 5,963 of 6,144 pairs. Calibration and confirmation stayed closed. |

### Rebuild the R24 readout from both original sealed cohorts

```bash
uv run --no-sync python scripts/reproduce_preparation_and_reuse.py \
  --study r24 --from-seals --workers 8 --output-directory "$RESULTS"
```

This run starts one step earlier. RC2 reads each of the 128 original sealed controls and reveals, recovers all six policies' choices, recomputes each root's service and response losses, and checks the selected uncertainty bounds and native work. It compares every scientific field to the released per-root readout and produces the same cohort report as the first command. The original E2 prefix, forecast, choice lock and parent remain bound to the retained continuation. The first interrupted roster contributes 64 unevaluable assignments, including 16 attempted prefixes and 48 unstarted prefixes. [Finite response workflow and retained continuation](../finite-response-law/guide.md)

## Reacquire a published native panel

R23 and R24 accept a complete published cohort or a single zero-based root index. Each worker starts from the original physical seed, carries the native checkpoints forward, and checks the actual panel identity. R23 verifies the prefix, parents and final matched assay against the original sealed choice. R24 checks the original task identity for every paired HDF5 result, including its arrays, checkpoints and native delivery. Results have their own filenames and record the number of new numerical acquisitions.

```bash
uv run --no-sync python scripts/reproduce_preparation_and_reuse.py \
  --study r23 --native-cohort E --root-index 0 --output-directory "$RESULTS"
uv run --no-sync python scripts/reproduce_preparation_and_reuse.py \
  --study r24 --native-cohort retained --workers 8 --output-directory "$RESULTS"
```

Omit `--root-index` to reacquire the full cohort. R23 supports `Q` (8) and `E` (32). R24 supports `calibration` (32), `retained` (64) and `disjoint` (64). The stopped prefixes have no original completed panel to compare. The original R27 experiment in this series performed a numerical refit on exposed native panels and acquired zero new roots. For a new independently issued experiment, select a disjoint unexposed allocation and use the existing qualification, publication and execution workflow. [R23 workflow](../preparation-applicability/guide.md) · [R24 and R27 workflow](../finite-response-law/guide.md)

### Run the R25 and R26 native experiments

Both use the ordinary recursive investigation service. The export includes the authored specification, complete source selection and the original producer's source and lock digests. R25 also includes the admitted lower and exposure census. R26 carries the original paired 128-root specification and its development lineage. A numerical replica uses a newly selected external workspace.

The offline readout above uses the operands shipped with RC2. Native replay of R25 or R26 also requires the original producer commit listed below. The squashed release has RC1 as its sole parent. Obtain the producer history from a retained repository before using a fresh release clone for native replay.

Set `RC2` to the release checkout and `PRODUCER_REPOSITORY` to the repository holding the listed revisions. These can be the same repository. Select new directories for the frozen source (`PRODUCER`), inputs (`INPUTS`) and native workspace (`REPLICA`).

| Study | Producer revision | Original authored directory under the study artifact root |
| --- | --- | --- |
| R25 | `2369c6236460b3f60551849985620c995f95febd` | `development-03` |
| R26 | `7aae07c0317035e773ee47207bd2933efeb31d18` | `model-free-matrix` |

```bash
git -C "$PRODUCER_REPOSITORY" worktree add --detach "$PRODUCER" "$REVISION"
uv run --no-sync python "$RC2/scripts/reproduce_preparation_and_reuse.py" \
  --study "$STUDY" --export-recursive-inputs --output-directory "$INPUTS"
cd "$PRODUCER"
export PYTHONPATH="$PRODUCER/src:$PRODUCER"
uv run --no-sync python "$RC2/scripts/replay_preparation_reuse_recursive.py" "$STUDY" prepare \
  --producer-checkout "$PRODUCER" --inputs "$INPUTS" --workspace "$REPLICA" --workers 8
uv run --no-sync python "$RC2/scripts/replay_preparation_reuse_recursive.py" "$STUDY" run \
  --producer-checkout "$PRODUCER" --workspace "$REPLICA" --workers 8
uv run --no-sync python "$RC2/scripts/replay_preparation_reuse_recursive.py" "$STUDY" read \
  --producer-checkout "$PRODUCER" --workspace "$REPLICA"
```

Select the locked environment for the frozen checkout before running those commands. The `recover` operation resumes through the same service on a settled interrupted replica. The scientific assignments have already been exposed. The local execution produces its own run identity and timings. Eligibility for the original protected continuation remains the original decision. [Waveform design](../../records/matrix-waveform-preparation.md) · [Handoff-entry design](../../records/matrix-handoff-entry.md)

### Recompute after an original analytical preflight refusal

R25 and R26 completed the assigned acquisitions. Each original terminal then retained a pre-calculation source-check timeout and a dependent blocked reduction. An operator with the original guarded store and its current access profile can repeat the full independent assessment. Select `PROFILE`, the original `AUTHORED` directory, and a new `REDUCTION` directory. Run in the corresponding frozen checkout with its imports as above. For relocated evidence, supply the frozen storage contract with `--artifact-root-contract`.

```bash
uv run --no-sync python "$RC2/src/empirical_lawhood/api/closed_matrix_panels.py" "$STUDY" \
  --project-root "$PRODUCER" --expected-git "$REVISION" --profile "$PROFILE" \
  --authored-directory "$AUTHORED" --output-directory "$REDUCTION"
```

The reader checks the complete settled task and receipt census, the worker preflight, exact array companions, the original producing source and every available reduction. It replays the missing analytical work and preserves the refusal and original operational status. R26 measures analysis time as part of a product, so a newly calculated product can have a new digest even when every scientific field agrees. For a previously exposed successful control select `--exposed-complete-control`. [Guarded reduction](../../../../../src/empirical_lawhood/api/closed_matrix_panels.py)

## Verify the source of the distributed inputs

The five ZIP files contain the original disclosed bytes. Their neighbouring JSON manifests identify each member and its source. The manifests use relative locations in the preparation-and-reuse series and the historical Tier 2 store. To reconstruct the archives from a copy of those files, select both original directories and a new output directory.

```bash
uv run --no-sync python scripts/reproduce_preparation_and_reuse.py --rebuild-archives \
  --series-directory "$SERIES" --tier2-directory "$TIER2" --output-directory "$ARCHIVES"
```

Member digests and sizes govern equivalence across platforms and compression-library versions. The ordinary replay reads the tracked archives directly. The manifests bind released evidence. They confer no original signing or protected outcome-access authority. [Operand manifests and archives](operands/)
