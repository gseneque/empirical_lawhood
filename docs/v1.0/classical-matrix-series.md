# Run the consolidated classical matrix experiments

SPDX-License-Identifier: CC-BY-4.0

This is the v1.0 execution route for a newly authored series over the classical
six-matrix substrate: two triplets of Hermitian 4 by 4 matrices, with all 96 real
position coordinates and their momenta. It connects the two capstone questions,
E1–E6, signed-contrast and causal-refresh analyses, and the two reusable response
derivations through the normal recursive investigation lifecycle.

The editable scientific authority is
[experiment.json](../../programmes/foundations/emergent-structure/workflows/classical-series/experiment.json).
The [scientific specification](../../programmes/foundations/emergent-structure/workflows/classical-series/science.md)
defines its measurements, forecasts, intervention comparisons, missing outcomes
and applicability. The [historical crosswalk](../../programmes/foundations/emergent-structure/workflows/classical-series/history.md)
identifies what is preserved, adapted, newly tested or still conditional.

## Scientific and software status

This definition creates new **predeclared development** evidence. It has not
executed the production population merely by being shipped. Successful execution
does not change the original experiments' statuses or establish scientific
qualification. Results explicitly retain `qualification: NOT_ESTABLISHED`.
The former E5/E6 nonentries remain historical facts. Their new successors have
their own original inputs, producing source, finite population and assumptions.
The [capstone method guide](../development/classical-matrix-capstones.md) specifies
the two new task channels, descriptor forecasts, unchanged response package,
support rules and separate calibration statements in full.

The smaller [smoke definition](../../programmes/foundations/emergent-structure/workflows/classical-series/smoke.json)
exercises the real native substrate and complete dependency graph on shortened
clocks. It is a software and numerical integration control. Its small CAL
population intentionally permits a vacuous uncertainty radius and refusal; such
refusal is a correct scientific outcome rather than a failed task.

## Execute from the supplied checkout

Use CPython 3.11.14 and the locked base dependencies. All commands below run from
the checkout root. Choose fresh output directories outside the source checkout
and outside `/tmp`; the storage contract rejects those locations. The variable
below selects a sibling output directory. If the checkout is under `/tmp`, set
`MATRIX_RUNS` to an absolute permitted directory elsewhere.
There is no private archive, molecular engine, GPU, signing credential or prior
historical run required for this exposed numerical series.

```sh
uv sync --locked --python 3.11.14 --group dev --group build --group reactor-example
MATRIX_RUNS="$(dirname "$(pwd -P)")/el-classical-runs"
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . \
  --workspace "$MATRIX_RUNS/smoke" \
  --definition programmes/foundations/emergent-structure/workflows/classical-series/smoke.json \
  --maximum-parallel-tasks 2
```

After this succeeds, author the full experiment without performing native work:

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . \
  --workspace "$MATRIX_RUNS/production" \
  --definition programmes/foundations/emergent-structure/workflows/classical-series/experiment.json \
  --prepare-only
```

Inspect `scratch/preparation.json` and `scratch/authoring.json` in that workspace.
Preparation derives source identities, prerequisites, scientific connections,
task assignments and resource requirements. Do not hand-edit the derived plan,
records, artifact hashes or execution receipts. Then execute that exact plan:

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . \
  --workspace "$MATRIX_RUNS/production" \
  --operation execute
```

Alternatively, omit `--prepare-only` in the new-study command to prepare, author,
execute and read in one invocation. The runner prints a compact result location
and writes the complete authenticated read to `scratch/result.json`.
Execution and recovery already return this full readout. The runner reuses it;
select `--operation read` when you want a separate fresh verification.

The full definition assigns 32 TRAIN, 32 CAL and 80 CONF independent roots.
Each root contains 11 parameter coordinates and four preparation recipes, for
44 nested native cases and 6,336 assigned cases overall. The coordinates contain
the nine original E4 parameter cells and two nominal-family transfer temperatures.
Panels, force roles, numerical views, output components and time samples remain
nested; they never enlarge the independent-root denominator.

The fresh graph has 290 operations: one native acquisition per root, one compact
summary per TRAIN/CAL root, one frozen calibration, one analysis per CONF root
and one retained population synthesis. Every CONF acquisition depends on the
original calibration. Individual tasks use one numerical thread. The existing
scheduler chooses usable parallel capacity subject to task memory requirements;
`--maximum-parallel-tasks` is an optional operational cap. Memory allowances are
conservative functions of the authored array census, not measured cost claims.
Runtime and disk requirements depend on the selected settings and host. Preserve
all original task/attempt receipts when reporting complete cost.

## Inspect and resume the original work

Reading authenticates retained products and presents their original analysis.
It does not call the simulator, recompute the scientific readouts or refit models:

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . --workspace "$MATRIX_RUNS/production" --operation read
```

For an interrupted run, use the shared recovery service:

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . --workspace "$MATRIX_RUNS/production" --operation recover
```

Recovery follows the original plan and authenticated attempts. It is not permission
to replace a scientific failure by a new seed. `read --partial` presents available
operational custody while scientific completion is deferred. An operation can
complete successfully while reporting unavailable factors, failed numerical
comparisons, vacuous calibration or no preparation nominee.

If recovery returns `BLOCKED`, inspect its complete failure census.
An empty attempt directory left by a machine interruption can cause an exhausted resource refusal.
The explicit [PURE scratch repair](../using/results-and-failures.md#repair-a-pure-attempt-refused-by-retained-scratch)
preserves completed receipts and the original terminal under a separate operational controller.
It retains the original scientific worker, seed rosters and task budgets.
Do not remove original scratch or edit a receipt to resume the graph.

## Develop, predeclare, analyse and revise

One JSON document contains the study label, three disjoint seed rosters and the
scientific settings. Copy it to make a distinct study. Unknown settings, duplicate
coordinates, overlapping root roles and inconsistent clocks refuse. Explicit
scientific decimal values are strings. The source version and exact authored
document are retained as original inputs; edits produce a new specification.

Development and calibration learn only from their assigned roots. The two
capstone calculations distinguish an upstream forecast of the prepared descriptor
from a preparation intervention that changes the input supplied to an unchanged
downstream predictor. The ordinary E3 response-error forecaster is a separate
calculation. CONF forecasts are committed before the response future; capstone
upstream forecasts are committed before preparation. Retained commitments bind
the calibration, causal inputs and task identities.

E5 nominates a preparation recipe on TRAIN for the declared joint high-minus-low
response objective. No usable nominee is a recorded nonentry. E6 carries the
nominal fitted relation and calibration to the two declared transfer temperatures
without a local refit. Neither a successful task nor an attractive exploratory
plot grants statistical transport or a new molecular result.

To add analyses to a completed population, keep the same rosters and numerical
settings, select the desired `phases`, and create a retained reanalysis:

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --project-root . \
  --workspace "$MATRIX_RUNS/reanalysis" \
  --parent-workspace "$MATRIX_RUNS/production" \
  --definition programmes/foundations/emergent-structure/workflows/classical-series/experiment.json \
  --operation reanalyse
```

This copies exact original CONF native arrays and the original frozen calibration
within authenticated custody. It creates 80 analysis operations and one synthesis,
performs no native acquisition or recalibration, and reports `EXPOSED_REANALYSIS`.
Its source, parent packet, original calibration and input identities remain visible.
It refuses altered numerical settings or a changed root census. New measurements,
a changed method fit, or altered experimental settings require a new development
definition and workspace. Use new disjoint root seeds for any later independent
confirmation claim and supply its actual authority/assessment mechanism.

## Read the scientific result

`scratch/result.json` contains the framework report and `scientific_result`.
Start with completion, evidence scope, the full root roster and population summary.
Inspect individual root `stages` for the underlying matrices, decisions and reasons.

| Question | Readout and interpretation |
| --- | --- |
| Capstone forecast-mediated reuse | Upstream prepared-descriptor forecasts, the fixed downstream response predictor, separate support/admission and delivered error |
| Capstone preparation-mediated reuse | TRAIN-nominated preparation with the same downstream predictor, support and calibration across preparation arms |
| E1: does a factor occur and survive? | Raw admission, trailing persistence, occurrence by the deadline and separate origin-fixed/moving survival; unidentified observations remain unknown |
| E2: which reduced response works? | FULL, FACTOR, GENERIC_SLOW, SPECTRA, NORM_RADIUS, ZERO, IO48, INPUT_KRYLOV and JOINT_KRYLOV with actual rank, availability and primary/fine checks |
| E3/E4: can a causal descriptor forecast applicability? | Baseline and algebra-enriched models, finite CAL order, honest refusal/vacuity and parameter-conditioned outcomes |
| E5: can preparation improve the joint target? | The original TRAIN nominee, paired CONF gains/harms/unknowns, and complete assigned-root denominators |
| E6: does the frozen supplier transport? | Unchanged nominal fit/calibration on the two fixed transfer coordinates, with no local training |
| Signed contrasts and refresh | Endpoint error energy, signed alignment, contrast error and inherited/generated suffix accounting |
| Joint-response derivation | Shared-port Krylov prefixes, residual witnesses, exact Schur/finite-update comparisons, and applicability-specific approximation checks |
| Retained-Gaussian derivation | Exact Gaussian elimination and nonlinear retained-potential controls, mean-anchor/variance integration, explicit non-SPD nonapplication, and the static-versus-memory counterexample |

Population synthesis counts independent roots. Missing assigned roots and
unavailable outcomes remain in the denominator and uncertainty bounds. Exact
paired sign calculations accompany gains and harms. Confidence intervals are
declared marginal development summaries, without an undeclared multiple-testing
qualification rule. Read every applicability premise alongside a numerical bound.

The derivation suite separates algebraic identities, finite-discretization
comparisons, conditional analytic bounds and physical assumptions. In particular,
an indefinite native Hessian is valid input to an off-real-axis self-adjoint
resolvent but does not define a normalizable Gaussian equilibrium. No shift is
silently applied to make it positive. Binary64 evaluations of formulas are not
outward-rounded certificates for every arithmetic or physical error source.

## Reuse the implementation

Public scientific authoring is in `empirical_lawhood.api.classical_matrix_series`.
Its runner uses `create_local_workspace`, `create_investigation_service` and
`prepare_investigation`, followed by the service's author/run/read/recover methods.
One extension declaration generates bindings, schemas, discovery and installation
metadata. Binary native arrays use the existing framed matrix codec and chunked
artifact path; compact fitting summaries avoid collecting full TRAIN/CAL arrays.

The pure domain functions in `domains.matrix.classical_series.science` can also
be called with supplied operands for numerical research. Generic reusable
mathematics lives in `methods.retained_gaussian_response` and
`methods.joint_response`; see the [joint-response method guide](../development/joint-response-calculus.md)
and [scientific component guide](scientific-components.md). The method package
does not acquire native data, start workers, grant authority or manage storage.

Keep historical source comparisons separate from new scientific evidence.
`scripts/check_classical_matrix_migration.py` compares selected native kernels
against a separately supplied original checkout in isolated import processes.
Agreement is a migration control; it does not replay the historical populations
or supersede their retained custody.
