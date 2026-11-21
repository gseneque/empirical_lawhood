# SCI02-D paired equilibrium estimator result

SPDX-License-Identifier: CC-BY-4.0

This record reports the complete SCI02-D equilibrium estimator experiment.
It separates mathematical mean preservation, measured variance, equilibrium accuracy and complete cost.
Read the [frozen protocol](../workflows/matrix-equilibrium-bridge/protocol-v1.md) and [run guide](../workflows/matrix-equilibrium-bridge/guide.md) for its selection and supported lifecycle.

The complete study did not admit shorter sampling for either corrected estimator. No 20% complete-cost saving was demonstrated.
STRUCTURE has a held full-path variance ratio of 0.950144; its signed bias against the longer reference is -0.00267603.
Equilibrium accuracy and molecular applicability remain unestablished.

The complete frozen study contains 16 training, 64 confirmation and eight independent reference bundles.
All 179 registered operations and 88 original native bundles completed and were independently read.
Software completion, variance reduction, equilibrium accuracy and practical economy are separate findings.

## Target and scientific status

The selected quantity is the signed five-center restrained integral for cross-couplings 2 minus 0.5, in Matrix energy units.
Both starting histories target the same canonical distribution. Their equal-weight average does not establish equilibrium populations.
The longer FINE reference is 0.114774 ± 0.00895025 (95% Student interval, eight independent bundles).
This reference has finite sampling error and unresolved equilibrium-state coverage. It is not exact truth.
The nine-minus-five-center difference is -0.00109058 ± 0.00449098.
The reference preparation difference is -0.000672961 ± 0.0116091; its PRIMARY-minus-FINE difference is -0.00154685 ± 0.00324925.
The selected total error is 0.01, with numerical, preparation and quadrature allowances of 0.002 each and a sampling half-width budget of 0.004.

## Solvable controls and the finite-restraint connection

The harmonic control residual is 8.88178e-16. The nonlinear zero-mean residual is 1.99246e-16.
The independent two-dimensional quadrature residual is 1.11022e-16.
The nonlinear discrete restrained integral is -0.128053; its continuous-center value is -0.129071.
The unrestrained PMF endpoint contrast is -0.346574, requiring a finite-restraint correction of -0.217503.
These original PURE controls support the identity and its implementation. They also show why a restrained integral cannot be relabelled as an unrestrained barrier.

## Exact frozen coefficients

One coefficient vector corrects the complete paired integral.
The original canonical Decimal values below were fixed before confirmation contact.
The four fields and their complete native-force/divergence terms are defined in the frozen protocol.

| Estimator | C0 | C1 | C2 | C3 | Production fraction |
|---|---:|---:|---:|---:|---:|
| NATIVE | 0 | 0 | 0 | 0 | 1 |
| COORDINATE | 0.16306995017389056 | 0 | 0 | 0 | 1 |
| STRUCTURE | 0.13009342164456975 | -0.23176545871529078 | 0.14540206976567216 | 0.3224327292693946 | 1 |

All 64 confirmation bundles estimate repeated performance for one physical target.
Their frames, blocks, starts, centers, arms and numerical views remain nested observations.
They do not represent 64 distinct mutation requests or establish a finite molecular reuse demand.

## Frozen estimators and confirmation

| Method | Production fraction | Full-path variance ratio | Prefix bias | Prefix RMSE | Mean sampling half-width | Individual intervals covering reference |
|---|---:|---:|---:|---:|---:|---:|
| NATIVE | 1 | 1 | -0.00319028 | 0.0137511 | 0.00336762 | 59/64 |
| COORDINATE | 1 | 0.951255 | -0.00298768 | 0.0133836 | 0.00328452 | 57/64 |
| STRUCTURE | 1 | 0.950144 | -0.00267603 | 0.01331 | 0.0032826 | 58/64 |

The coefficients were frozen from the complete training bank using within-root, within-history block covariances.
NATIVE has no correction; COORDINATE uses one force control; STRUCTURE uses four invariant force controls.
The controls have zero mean under the exact canonical target. Finite sampling, initialization and BAOAB timestep error remain assessed separately.
Individual intervals use 32-frame blocks. Coverage against the uncertain independent reference is a diagnostic, not a guaranteed confidence result.
Mean intervals use the 64 independent bundles, rather than treating frames, starts or numerical views as independent units.

Numerical differences are PRIMARY minus FINE. Preparation differences are ZERO minus nominal-product history.
Coverage counts concern the observed independent reference; their binomial intervals do not remove its uncertainty or establish coverage of the unknown equilibrium value.

Training variance ratios were 1, 0.8194, 0.756061 for NATIVE, COORDINATE and STRUCTURE.
The selected fraction rule retained full production length for all methods. No shorter operational path was admitted.

| Method | Numerical difference ± half-width | Preparation difference ± half-width | Individual precision passes | Unresolved prefix tails / 128 histories |
|---|---:|---:|---:|---:|
| NATIVE | 7.01796e-05 ± 0.000136728 | 0.00402075 ± 0.00726058 | 0/64 | 0/128 |
| COORDINATE | 5.87636e-05 ± 0.000122451 | 0.00212983 ± 0.00737789 | 0/64 | 0/128 |
| STRUCTURE | 4.3237e-05 ± 0.000114297 | 0.00337841 ± 0.00724637 | 0/64 | 0/128 |

Full numerical arrays retain chronology, both preparations/views, block-length sensitivity, signed errors, covariance, binomial coverage intervals and reference uncertainty.
The complete original denominator is retained for each method.

| Method | Full-path first-minus-second-half estimate | Doubled-block intervals available | Reference-adjusted point-error passes |
|---|---:|---:|---:|
| NATIVE | 0.00248269 ± 0.00741084 | 64/64 | 4/64 |
| COORDINATE | 0.00164572 ± 0.00648627 | 64/64 | 4/64 |
| STRUCTURE | 0.00202842 ± 0.00632602 | 64/64 | 6/64 |

## Costs and practical result

Disjoint lifecycle observations total 4.15968 CPU hours and 93.1714 elapsed minutes.
These totals retain 2 unsuccessful lifecycle invocations and all measured recovery work.
These totals include reaped worker children. Native child CPU is a contained component and is not added again.
Input construction, source setup and failed setup have separate retained records; unmeasured implementation effort is not assigned a zero cost.
The successful continuation helper adds 118.115 CPU seconds and 102.235 elapsed seconds outside those CLI phases. Its nested input-constructor timing is not added again.
The study acquired every full confirmation suffix. Actual avoided native force calls are zero.

The original assessments, lifecycle scientific reads and authenticated continuation performed 5,799,936 scalar force checks on retained states. Their CPU is already contained in the lifecycle/helper observations.
The following reconstruction counts trajectory force work only; it does not silently absorb verification calls into the sampling denominator.

| Method | Per-confirmation force ratio | Training force charge | Reference force charge | Finite force-work saving |
|---|---:|---:|---:|---:|
| NATIVE | 1 | 0 | 84,934,944 | 0.000% |
| COORDINATE | 1 | 23,593,280 | 84,934,944 | -13.158% |
| STRUCTURE | 1 | 23,593,280 | 84,934,944 | -13.158% |

The native comparator includes 64 ordinary bundles and the same eight longer reference bundles.
Each corrected method also pays all 16 training bundles. Warmup is retained at every prefix fraction.
These force counts reconstruct the selected finite allocation; they are not measured deployment savings or a complete CPU model.
Actual production use still needs equal-accuracy admission and its full construction, assessment, failed-work and orchestration costs.
The 64 repeated estimates concern one target and do not establish demand for 64 distinct reusable mutation forecasts.

## Molecular handoff

The inspected original M1 preparation record reports an owner-cancelled, unconverged relaxation, with no final coordinate/gradient arrays, optimizer checkpoint or relaxed endpoint.
Actual matched WT/I95M states, atomic correspondence, complete QM/MM settings, centers, stiffness, physical horizon, tolerance and resource allocation remain necessary.
Matrix radius fields and timesteps do not transfer automatically. No molecular acquisition was authorized by relabelling the cancelled preparation.
Finite-restraint and measure corrections, basin/dividing-surface normalization, orthogonal-state coverage, transmission and effective-state aggregation remain separate suppliers.

## Custody and validation

Producing source snapshot: b0a4fd8edbae4809717ddd39a5205bb64312895e.
Frozen protocol SHA-256: cb2bb1a3be6fcf05be70d74cce7e7ef25edf34249b8333530ef7bfeb7d89587b.
The installed wheel and source archive contain no Markdown work plans. Their original bytes remain in separate local custody.
The source freeze passed 28 focused/integration checks, lint, generated-owner drift checks and documentation validation.
An initial installation attempt used system Python 3.12 and was retained; the unchanged archives were installed under locked Python 3.11.14 before study inputs or native acquisition.
The first continuation helper failed before input creation because it lacked a multiprocessing entry-point guard. The corrected helper used unchanged installed scientific code and the original frozen fit; both helper attempts are retained.
Reference trajectories completed under the original 192 MiB invocation allowance, but publication of their ordinary parent copies exceeded the combined native-plus-parent allowance. The original failures and their measured work remain retained.
Ordinary public recovery authenticated the completed native records and published the parent outputs on their original attempts. It did not reacquire a completed trajectory or change any scientific input.
The current implementation and protocol v2 select a 384 MiB allowance for future inputs. A regression check charges both uncompressed reference copies; it reproduced the original refusal and passes the correction. The original protocol v1 and producing installation remain unchanged.
The corrected working implementation passed 29 focused checks, lint, ordered generated-reference checks and documentation validation. Those are software conformance findings, separate from the original producing installation and scientific outcomes.
Original receipts retain 88 completed native bundles. Independent readback reconstructed sampled native forces, controls, prescribed transitions and frozen covariance equations.
Readback acquired no new trajectory. Files in this report are derived summaries, not substitutes for original receipts.

Public recovery left all 88 native contact records, 88 completion records and 88 native receipts byte-for-byte unchanged.
The locked study environment produced the numerical tables and independently verifies them. Figure rendering alone uses the existing system Python 3.8.10, NumPy 1.24.4 and Matplotlib 3.4.3 installation; it receives only retained numerical results.
The first report attempt wrote its numerical tables but stopped because Matplotlib is absent from the locked study environment. That original script, failure log and partial-report bytes remain retained; the study environment and all scientific records were left unchanged.
Scientific reasons: EQUILIBRIUM_STATE_COVERAGE_NOT_ESTABLISHED, MOLECULAR_SUPPLIERS_NOT_ESTABLISHED, OPERATIONAL_SAVING_RECONSTRUCTED_NOT_DEPLOYED, PAIRED_TARGET_ACCURACY_UNRESOLVED, PREPARATION_ALLOWANCE_UNRESOLVED_OR_EXCEEDED, QUADRATURE_ALLOWANCE_UNRESOLVED_OR_EXCEEDED.

The current custody root is `/media/chevre/EL_2/empirical-lawhood/runs/sci02-d`.
The original execution selected `/home/chevre/empirical-lawhood-sci02-d`; its frozen records retain that historical path.
The EL_2 migration preserves the package bytes and original logical storage identity; use the current retained-access selection for reads.
Original independent reads are `results/training-01/read.json` and `results/confirmation-01/read.json` below that root.
The descriptive delivery is `results/report-01/`, with arithmetic verification, machine-readable findings and complete measured ledgers.
The original native products, receipts, input bindings and operational failures remain in external custody.
These paths locate existing results; they do not replace their original contracts.


## Producing identity and finite allocation

| Stage | Run identity | Completed operations |
|---|---|---:|
| Training | `recursive.285f2061e30ff52c9162f075` | 34 |
| Confirmation | `recursive.ba5c73870c34b137f91afd86` | 145 |

The new allocation contains 16 training, 64 confirmation and eight independent reference bundles.
All 88 original native contacts completed once.
The retained population has 1,409,024 sampled full-force states and 202,901,344 native force evaluations.
The two numerical views and both preparations retain the complete selected horizons.

Producing code SHA-256: `88020d25c36086522e87351b30e2a86a938d017ad1bdcfd9ce43c9c25fcfd87d`.
Dependency lock SHA-256: `21335fee59de9a5ba1fa1a52d835309b43b2e7050e763c944d747fee7a0b1430`.
The producing checkout-clean flag is false because the frozen source retains the actual working changes.
The environment is locked CPython 3.11.14, NumPy 2.4.6 and SciPy 1.17.1, with four workers and one numerical thread per worker.
This development source and its focused conformance checks are not a release-acceptance result.

## Post-hoc mechanism analysis

The retained-data analysis dated 9 November 2026 preserves the original 16 training,
64 confirmation and eight reference bundles, coefficients and full-length sampling selections.
It acquires no new trajectory and changes no original scientific decision.
Its report, six PNG/SVG figures, complete numerical tables, source bindings and
verification are retained under
`/media/chevre/EL_2/empirical-lawhood/analyses/sci02-d-posthoc-2026-11-09/`.
The reading copies are `analysis.html` and `analysis.md`.

The fit's 32-frame block objective and the complete estimate have different covariance.
STRUCTURE's training and confirmation block variance ratios are 0.756061 and 0.737298;
the corresponding complete-bundle ratios are 1.029484 and 0.950144.
Thus the apparent loss from training to confirmation also changes the measured objective.
An exact finite-time covariance decomposition shows that temporal covariance offsets
most of the approximately 69.5% instantaneous variance reduction.

The paired complete-bundle bootstrap interval for STRUCTURE / NATIVE variance is
0.744725–1.205407. STRUCTURE / COORDINATE is 0.998832 with interval 0.883334–1.129669.
The extra fields have no resolved incremental advantage in this finite cohort.
All 128 starting histories per method have a positive autocorrelation rebound above
0.25 after the frozen heuristic's first nonpositive lag pair; its passing flag supplies
no assurance that later dependence has disappeared.

The shortest allowed quarter-length production could save at most 13.158% of the
selected finite trajectory-force work after training, reference and warmup charges.
It still misses the aggregate 0.004 sampling half-width budget.
A 20% saving on that force-count comparison would require a fraction at most 0.054990,
below the frozen menu. This is a force-work reconstruction, not a complete CPU result.
Exploratory field ablations, alternative fits and prefixes do not qualify a new method.
