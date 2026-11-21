# Classical matrix programme with model-free methods

SPDX-License-Identifier: CC-BY-4.0

This guide runs the authored M0–M7 programme through EL's existing recursive
preparation, execution, assessment, custody and recovery services. The original
M0–M4 pilot completed 135 operations on 33 independent roots at
`3f87d5e201132b1d8d626728914d06b27705fbd0`. The receiver-specific revision
below uses the pilot to select decision rules and retains its original scores.
The [completed receiver studies](../../programmes/foundations/emergent-structure/records/model-free-receiver-results.md)
record all eight module decisions, five ordinary-read hashes and the work measured across 511 operations.

The core graph has `acquire`, `analyse` and `synthesise` operations. It creates
no artificial TRAIN, FIT or CAL products. Each native root/module is recoverable
independently; M3 consumes M1's actual checkpoint, M4 consumes M3's native operands,
M5 consumes M1's preparation before selectively acquiring new native futures,
and M7 consumes M1's actual admitted-entry checkpoint.
The optional learned E4/E6 comparator has its own explicit TRAIN/CAL/CONF lifecycle.

## Choose the scientific definition

Definitions live in
`programmes/foundations/emergent-structure/workflows/model-free/`.
They are editable scientific JSON. The public author computes canonical identities.

### Receiver-specific experiments

The `receiver_study` selection `matrix-receiver-study.v2` binds the physical
instrument, the population that needs it, the units of loss, the decision
point and the fallback. Independent preparation roots are the inference units.
A coupled view, forced branch, time origin, recipe, panel or destination
adds a measurement on the same root. Each fresh allocation below is disjoint.

| Editable definition | Population and receiver | Public authoring operation |
| --- | --- | --- |
| `receiver-memory-reanalysis.json` | Exposed original pilot M2 observations from 16 roots. Score a common sign-of-position future from the original native bytes. | `reanalyse --parent-workspace PILOT` |
| `receiver-foundations.json` | One known-law control root, 16 memory roots, 16 paired structural/commitment roots and 16 separate restrained-equilibrium roots | `prepare` |
| `receiver-response.json` | 16 fresh, paired M1/M3/M4 roots. One signed H64 primary with matched coupling and temperature destinations. | `confirm --parent-workspace PILOT` |
| `receiver-benchmark.json` | Reveal the complete 32-root M5 frame to measure variance and price all suppliers at equal precision. | `prepare` |
| `receiver-audit.json` | Sample eight whole roots from a disjoint 32-root M5 frame. Assess the cost and precision of the frozen rule. | `deploy-population --parent-workspace BENCHMARK` |

Use the original SCI02-C confirmation authored directory, the current
authenticated read profile and the matching artifact access contract. The
selection reads original design and template bytes. Its output records the
packet, study, physical design, template and typed array-member identities.
The original outcomes have no role in binding this port. The source64
measurement in each fresh response or population experiment sets the root's physical instrument.
Foundations and memory-only reanalysis declare a null instrument and can use their
editable definitions directly.

```sh
uv run --no-sync python scripts/examples/model_free_receiver_inputs.py \
  --project-root "$PROJECT" --original-authoring-directory "$SCI02C_AUTHORED" \
  --read-profile "$SCI02C_PROFILE" --artifact-root-contract "$SCI02C_ACCESS" \
  --output-directory "$SELECTED" \
  --definition "$TEMPLATES/receiver-memory-reanalysis.json" \
  --definition "$TEMPLATES/receiver-foundations.json" \
  --definition "$TEMPLATES/receiver-response.json" \
  --definition "$TEMPLATES/receiver-benchmark.json" \
  --definition "$TEMPLATES/receiver-audit.json"

uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation confirm --prepare-only --project-root "$PROJECT" \
  --definition "$SELECTED/receiver-response.json" --parent-workspace "$PILOT" \
  --workspace "$RESPONSE" --maximum-parallel-tasks 4 --metrics-json "$PREPARE_METRICS"
uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation execute --project-root "$PROJECT" --workspace "$RESPONSE" \
  --maximum-parallel-tasks 4 --metrics-json "$EXECUTE_METRICS"
```

Select fresh absolute paths for each study, selection and metrics file. Inspect the
prepared graph, actual root identities, parent evidence, physical settings and
host ceilings before execution. Preserve the returned presentation, invoke an
ordinary `read` with its own metrics path and compare the scientific hash and
attempt census. An interrupted study uses `recover` on its original workspace.

#### What each module decides

| Module | Primary rule and necessary controls |
| --- | --- |
| M0 | Feed repeated independent known-law populations through a fixed admission rule. Two hidden strata have identical visible inputs. Compare a common acceptable action, incompatible actions and a near-boundary ineligible action. An action must keep both stratum error risks within 0.10. For the declared alternatives require false delivery ≤0.05 and power ≥0.80, with simultaneous uncertainty. Report always-refuse and unconditional zero separately, the legacy observation and bath controls and the exact free forced-BAOAB first-clock solution. |
| M1 | At T=2 compare the causal trailing Y-persistence policy for the joint-increasing preparation with its fixed and externally yoked clocks. Keep the 15° angle, 0.05 leakage, 16-tick grid, 128-tick persistence and 1152-tick deadline. An offer needs structural presence. A delivery also needs survival in every tested +/−/HOLD branch and signed H64 FACTOR impulse ≥0.10 actuator units on both panels. The 10⁻⁶ native-momentum floor describes detection. Compare all-assignment delivery ≥0.75, wrong offers ≤0.10, permitted coverage loss ≤1/16 and paid force calls. Report physical work, integrated coupling, waiting and returns after a genuine prior admission. Two zero-start equal-exposure schedules isolate ordering. |
| M2 | Compare fixed q, q-plus-velocity, q-plus-velocity-and-force, a one-lag secant and the constant-sign control on the same binary future. The origin is 8192 ticks into the record after 4096 burn-in ticks. Predict the sign 64 physical ticks later. The receiver tolerates average error ≤0.10. Every missing root can contribute a full error. Conditional history and Chapman–Kolmogorov discrepancies, segment means and matched clone/reset interventions are secondary. The common sign bins span both tails. No stationarity conclusion follows from these tests. |
| M3 | ORIGINAL minus EARLY is the H64 odd momentum along the authenticated source64 FACTOR direction, averaged over two coupled panels. Freeze a ±0.001 actuator-unit individual delivery interval, a 0.0001 numerical allowance and the response-sign decision before outcomes. Use a separately paid causal HOLD prefix at tick 32. Compare a frozen operator, refreshed operator on the original basis, one nested enrichment and sampled FULL competitors. Carry the predicted state and account for projection loss, the propagated map defect and the signed endpoint cross term. Grade the signed receiver, the 13 scheduled full-response block readouts and the original physical design's denser schedule separately. Match +/−/HOLD and refine the common physical preparation and quench on h, h/2 and h/4. |
| M4 | Query the TRACE receiver of the FACTOR-driven resolvent at z=i, at the measured ORIGINAL and EARLY checkpoints. The pair allowance is 0.01 and the sufficient deterministic arm allowance is 0.005. Compare nominal identity reuse, zero, the inherited scalar, a capped 24-column destination probe and a 48-column local rebuild using the same estimator. Dense native checking on the designated roots carries its own bill. A resolvent certificate answers this frequency-domain query. |
| M5 | Estimate the signed H64 ORIGINAL-minus-EARLY FACTOR momentum. Retain the actual force, momentum receiver, panel assignment and scale. One actuator unit corresponds to 0.00016 native momentum here. Individual width 0.001 corresponds to 0.00000016 native momentum. The frame-mean RMS budget is 0.00025 actuator units. Report the separate mean-interval criterion and the cost at equal precision of the auxiliary, single coefficient, zero and direct native estimators. A whole-root random audit includes both arms, both panels and declared views. Finite-frame design variance comes from residuals on the completely revealed frame. New-frame residual variance, missing data and extra native fallback costs affect its scientific disposition. |
| M6 | Compare the signed nine-center restrained mean-force grid sums at T=1 and two couplings. T=2 supplies a temperature stress comparison. Keep the nested five-center, shared long path, independent finer-step path with separated initialization, full-residual importance and independent-root moment estimates. Check known null and nonzero harmonic contrasts and material overlap failure. Allocate ln(1.05) kBT to the matrix energy error for this illustrative fixed-prefactor decision. Statistical uncertainty and a controlled bias allowance must fit together to establish a measure-level claim. |
| M7 | Classify the fixed handoff's initial occupancy and Y eligibility. Allow entry to the common interior within 1024 ticks. From that entry follow four coupled futures to 4.096 time units. A commitment needs 16 consecutive physical ticks at the ±0.1 boundary. Report per-assignment delivery, conditional incidence, competing returns, administrative censoring and failed paths, with h/2 and dwell sensitivity. The incidence allowance is 0.10 probability and the restricted-mean allowance is 0.256 time units. Matched visible-entry hidden-state controls test whether one history cue changes the decision. |

These tolerances define matrix decisions. The energy budget assumes a fixed
prefactor in the illustrative rate mapping. Molecular turnover, specificity,
barriers and transmission require their own material measurements and bounds.
For M5 the second 0.00025 actuator-unit budget applies to a 95% mean interval.
On the revealed frame Chebyshev's inequality bounds its half-width using the
known design variance. Sparse-frame precision remains conditional on its observed
audit sample. The research audit measures deployment costs on disjoint roots
even when the benchmark selects a direct supplier. An economic deployment must
meet the gate for the actual named supplier.
The narrow H64 experiment spends 0.04 of the total 0.05 error allowance on
M3 and 0.006 on M4. Each M5 study assigns 0.045 to M5. In foundations the
weights for M0, M1, M2, M6 and M7 are 0.15, 0.20, 0.20, 0.20 and 0.22.
The three remaining modules have weight 0.01 each. Retained reanalysis keeps
the original one-eighth M2 share. Report the interval, eligible denominator
and non-deliveries whenever a small cohort leaves a decision unresolved.

### Original definitions and retained comparisons

| Definition | Scope | Independent roots / operations |
| --- | --- | --- |
| `smoke.json` | Tiny controls for all eight modules; no qualification | 7 / 40 |
| `pilot.json` | M0 controls, 16 paired formation/response roots, 16 separate memory roots | 33 / 135 |
| `matched-exposure.json` | Equal integrated sector exposure, six paired recipes | 16 / 66 |
| `transfer.json` | Frozen nominal source, held T=1.125/3.25 and cross coupling=2 destinations | 16 / 99 |
| `population-reveal-all.json` | 32 paired-root native benchmark; exact SRS design comparisons | 32 / 130 |
| `population.json` | Fresh 32-root sparse frame, eight native audits; authenticated reveal-all parent required | 32 / 130 |
| `equilibrium-events.json` | Separate 16-root equilibrium and 16-root event cohorts | 32 / 99 |
| `programme.json` | Union development pilot, reveal-all population and equilibrium/event cohorts | 97 / 362 |
| `confirmation.json` | Initial 80-root formation/response confirmation allocation | 80 / 483 |
| `memory-reanalysis.json` | Exposed post-hoc rebin/history comparison from original pilot observations | Same 16 / 17 analysis operations |
| `memory-confirmation.json` | Initial 80-root memory confirmation allocation | 80 / 161 |
| `relation-benchmark.json` | Optional learned E4/E6 comparison, nine training coordinates and three transfer coordinates | 32 TRAIN, 32 CAL, 80 CONF |

Start with the bounded pilot. Enter the mean, equilibrium and kinetic branches
after reviewing their prerequisites and actual costs. The complete menu is an
explicit selection; it is not an automatic purchase of every possible successor.
The confirmation allocations are planning values, not power guarantees. Edit and
freeze their scientific settings after development, before observing their roots.

Each root declares its seed, module census and development/confirmation role.
Memory roots are separate from formation and response roots. Recipes, coordinates,
ports, numerical refinements and future-noise replicas remain nested observations.
The M5 probability sample is code-derived and frozen at authoring; the full frame
has one specification owner, while each operation receives its own sampling assignment.

## Environment and source

Use the locked base/development environment in [the environment guide](../using/environments.md).
The declared numerical environment is CPython 3.11.14, NumPy 2.4.6 and SciPy 1.17.1.
Work from the committed delivered source so authoring binds the implementation
that will actually execute. An editable installation is not a qualification result.

```sh
uv sync --locked --python 3.11.14 --group dev
```

Keep native results outside the checkout. Set `OPENBLAS_NUM_THREADS`,
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, `NUMEXPR_NUM_THREADS`,
`NUMBA_NUM_THREADS` and `BLIS_NUM_THREADS` to `1` for reproducible worker settings.
The examples use one numerical thread per native task; shared execution selects
the actual usable process capacity. Development `resources` fields bound memory, wall time and output bytes without
changing scientific record lengths or rosters. Confirmation requires all three
ceilings to be finite positive integers selected from the authenticated pilot
and measurements on the execution host. The supplied confirmation definitions
are deliberately incomplete planning inputs until those choices are made.

## Prepare, inspect and execute

Choose absolute paths for the checkout and fresh workspace:

```sh
uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation prepare --project-root /absolute/empirical_lawhood \
  --workspace /absolute/runs/model-free-pilot \
  --definition programmes/foundations/emergent-structure/workflows/model-free/pilot.json
```

Preparation writes the exact definition, canonical specification, original input
selection and source snapshot beneath `scratch/inputs`. Inspect
`scratch/preparation.json` and the authored graph beneath `artifacts/model-free-matrix`.
Preparation performs no native acquisition.

```sh
uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation execute --project-root /absolute/empirical_lawhood \
  --workspace /absolute/runs/model-free-pilot
```

For a new workspace, `--operation run` combines preparation and execution.
`--operation read` reads original authenticated products; it does not reconstruct
native dynamics or rerun statistics. `--operation recover` uses the ordinary
shared owner and preserves completed and failed attempt ancestry. Each invocation
owns a distinct progress record. `--partial` is a custody-only read selection.

## Scientific modules and result meaning

This section describes the original definitions and their comparison instruments.
The [receiver-specific experiments](#receiver-specific-experiments) above define the revised H64 instrument, preparation clocks and decision budgets.

| Module | Actual implemented acquisition / assessment | Main refusal or unresolved boundary |
| --- | --- | --- |
| M0 | Seven observation controls, algebraic checks, design/headroom and historical-operand status | Missing historical data cannot become a reproduction claim |
| M1 | Matched recipes; fixed late and causal trailing-persistence checkpoints; real fresh service futures | Nonentry, waiting, lost presence and suppressed signal retain the assignment denominator |
| M2 | Constant-control finite-age native records; fixed q/velocity/force charts; lag and history statistics; restart/reset controls | Constant controls do not prove stationarity; unsupported conditionals remain unresolved |
| M3 | Native Hessian actions, incremental certificates, port/gauge controls, equal-rank/action comparisons, h/h2/h4 coupled futures, signed errors, causal schedule selection | Resolvent, discrete propagation, native tangent and finite chord have separate scopes |
| M4 | Actual checkpoint composition and exact/probed/new-local transfer paths | New local actions are algorithm portability, not zero-data reuse |
| M5 | Frozen per-root auxiliaries, randomized whole-root native audits, paired contrasts and finite-frame correction | Missing sampled outcomes remain unresolved; no native saving from reveal-all comparisons |
| M6 | Native restrained BAOAB ensembles, five/nine center comparisons, longer reference, full root covariance, positive-reference residual integration and canonical controls | Finite preparation, finite-step measure bias, overlap and tails remain explicit |
| M7 | Direct native finite-horizon competing events, survival, restricted mean and entry-history grouping | Failed paths differ from administrative censoring; no automatic infinite-horizon rate |

Every result retains physical scope, original inputs, root identities, useful
signal, uncertainty meaning and actual work. A completed operation can correctly
produce `UNRESOLVED`, `UNAVAILABLE` or nonentry. Software completion is not admission.

### Memory and uncertainty

The initial memory record has 16,384 physical ticks after the declared preparation,
with a 65,536/131,072 tick acquisition ladder. Lag units are observation strides
and the physical timestep is retained. Finite history order and joint-cell limits
are explicit. Longer histories are not silently truncated into lower-order claims.

The generic assessment returns CK witnesses, three-time/history dependence and
simultaneous independent-root probability bounds. A history equivalence statement
requires an upper bound times the receiver oscillation, plus declared bin/tail
allowances, within the task tolerance. Nonpositive conditioning support, missing
roots, unqualified stationarity and unbounded requested observables do not become
small-memory claims. The finite record ladder has explicit family error allocation.

M0's heterogeneous control assigns a fixed transition kernel to each of sixteen
independent synthetic roots and compares the equal-root mixture with its two
known-kernel subpopulations. Its protocol control changes the transition kernel
at a declared sample age, then compares age-pooled statistics with observations
conditioned on exact future-anchor ages. Both use the production observation,
counting and root-assessment path. Exact three-time laws establish the intended
nulls, including lag pairs that span the protocol switch. Finite random records
can remain unresolved; no random control is required to reject or certify a null.

M2 freezes `segment_boundaries_samples` in its normalized scientific settings.
The default is an early/middle/late partition of all retained samples; explicit
partitions must begin at zero and end at the record's exclusive sample boundary.
The `within_segment` transition policy excludes every lag pair whose endpoints
cross a boundary, with a separate excluded-pair census. Occupancy and transition
counts retain observed, missing, out-of-range and unsupported mass. Each paired
segment comparison uses complete independent roots; repeated origins or segments
never increase that root count. Row-conditional changes require support in every
assigned root, otherwise that contrast remains unresolved. Means, occupancies,
transition-joint frequencies and row-conditional transitions answer distinct
finite-record questions; none establishes stationarity or equilibrium.

The module's error allowance is split equally between the history and segment
families, then across their declared charts, contrasts and record-length looks.
Changing the segment partition during retained reanalysis is allowed only as an
exposed post-hoc analysis, with the same absence of selection-adjusted coverage
as a post-hoc bin or history change.

Confirmation preparation also reports the precision of the actual joint and
marginal family. For alphabet size `k` and older-history order `h`, the family
contains `k^(h+2) + k^(h+1) + k^2 + k` bounded events. All-cell equivalence needs
positive lower bounds for every one of `k^(h+1)` conditioning probabilities;
therefore the common probability halfwidth must be less than `1/k^(h+1)`.
The authored protocol-age anchor is tick 16,384 of the record, so even the
longest selected history has a complete anchor on the first record length.
Confirmation also checks temporal support explicitly. The supplied 80-root broad
memory menu fails even the probability-support necessary condition.
Preparation refuses a primary memory-equivalence confirmation that cannot pass
it. A `DETECTION_ONLY` selection remains available with the full precision
diagnostic and unresolved outcomes. Longer records do not create more independent
roots for this conservative bound. Passing the necessary condition is not a
power guarantee or sufficient task precision; revise the scientific menu or
root allocation explicitly before entry if the requested target demands more.

Optional pure comparators are in `methods/model_free/comparators.py`: compression,
an explicitly fitted discrete-memory regression, physical-parity path reversal,
and initial-density nonlinear response. They retain their own assumptions and
do not add hidden fit dependencies to the core graph.

### Individual prediction and finite-frame means

M5's frame comprises independent roots with all declared paired recipes. The
fixed auxiliary uses native local actions and is computed independently of the
random audit decision. Only selected roots acquire the distinct native audit
futures. Read actual acquired/omitted counts and the full preparation/auxiliary
cost. Ordinary momentum is unbounded; a confidence certificate cannot be based
on an invented range. Optional clipping changes the target explicitly.

First run `population-reveal-all.json`. The benchmark reports the direct SRS
mean and the auxiliary-corrected mean on the identical audit sample, their paired
covariance and exact finite-frame design moments. A constant auxiliary reduces
to the direct estimator; an adverse auxiliary can increase variance. Revealing
all native outcomes provides a comparison, with no actual omitted-future saving.

Then use the authenticated public deployment route with the fresh seeds in
`population.json`:

```sh
uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation deploy-population --prepare-only \
  --project-root /absolute/empirical_lawhood \
  --workspace /absolute/runs/model-free-population-sparse \
  --parent-workspace /absolute/runs/model-free-population-reveal-all \
  --definition programmes/foundations/emergent-structure/workflows/model-free/population.json
```

This route requires every assigned benchmark cell and contrast, preserves the
native target and auxiliary settings, and rejects exposed root reuse. It does
not use benchmark outcomes as the new frame's native outcomes. If auxiliary
construction fails numerically, the declared `ZERO_BEFORE_NATIVE_OUTCOMES`
policy freezes zero before native outcome access and charges its attempted work.
Missing sampled native outcomes remain unresolved.

### Physical protocol work and computation

Formation settings explicitly select
`TERMINAL_COUPLING_AT_FIRST_SERVICE_FINAL_KICK`. For a time-dependent coupling,
the instrumented BAOAB step records the parameter jump after the second A
position update and before the final B force kick, at the same actual position:

\[
\delta W=U(q_{\mathrm{jump}};\lambda_{\mathrm{new}})
          -U(q_{\mathrm{jump}};\lambda_{\mathrm{old}}).
\]

The full native potential and both changed coefficients are included. This
accounts for parameter work under the declared discrete protocol; it is not
total force work, thermostat heat or a continuous-time energy-balance certificate.
A causal early checkpoint receives the terminal-coupling quench through the
same declared service step. Each plus/minus/hold future retains its own work
ledger; their sum is not a single physical trajectory. Failed paths preserve
completed jump prefixes, potential evaluations and actual force/Hessian calls.
Integrated sector exposure, physical work and computational cost are separate
quantities. Work instrumentation leaves the trajectory unchanged.

### Equilibrium and kinetics

M6 reports native finite-preparation estimates and measured numerical/reference
differences. A burn-in length does not establish exact canonical preparation.
Retained Gaussian integration accounts for the complete native residual; an
indefinite native Hessian is never silently used as canonical precision. The
fixed canonical control uses the actual complete restrained gradient.

The synthesis compares direct finite-grid mean-force integration, the nested
coarse grid, the longer shared-path reference, the fixed canonical control and
the full-native-residual Gaussian importance endpoint. It retains their complete
across-root estimator covariance. Every coordinate and paired supplier receives
its declared share of the M6 error allowance; normal and jackknife intervals
remain approximate.

For each coordinate the importance endpoint is
`-(log Z(s_last) - log Z(s_first)) / beta`. The fixed Gaussian reference and
momentum normalizations cancel within that coordinate. Paired coordinates use
their own inverse temperatures before taking the signed difference. Effective
sample size and maximum normalized weight diagnose concentration; they do not
bound omitted tails, overlap failure or the bias of a finite-sample logarithm.
Full 96-coordinate residual integration is an operational estimate, with no
claim that a cheap low-dimensional elimination has already succeeded.

The anchored mean–variance identity needs an actual variance operand. A
within-record `ddof=1` variance is biased under serial correlation. M6 preserves
that historical plug-in as a labelled comparator and also supplies the
independent-root moment estimate

\[
\widehat v=\frac1R\sum_r\overline{x^2}_r
-\frac1{R(R-1)}\sum_{r\ne s}\bar x_r\bar x_s.
\]

With identically distributed independent roots and the same frozen record
weights, this estimates the variance of the declared root/time mixture without
assuming independent time samples. It represents canonical variance only after
the canonical-measure premise is supported. Each deletion in its approximate
jackknife removes an entire root, preserving paired arms, centers, mean anchors
and second moments; sufficient sums avoid quadratic population copying.
Negative finite-sample moment estimates remain visible. Center interpolation,
finite-step measure bias and canonical preparation still need separate evidence.
The transported target is the declared finite-grid sum. On interval
`[s_i, s_(i+1)]` its variance integral has the constant tail weight
`W_i = sum_{j>i} w_j`. This is exact for the represented piecewise-linear
variance and the selected grid. The continuous endpoint integral instead uses
a continuously varying tail kernel. For a variance contrast `v(s)=s` on
centers `[0, 0.5, 1]` with unit stiffness, unit temperature and zero initial
mean contrast, the finite-grid
contrast is `-3/16`; the continuous endpoint contrast is `-1/6`.

M7 supplies finite-horizon quantities to compatible consumers. Its matrix adapter
uses shared statistics without passing matrix data through molecular authenticity
readers. Optimizer iterations in Rubisco M50 are not physical time and cannot
serve as molecular memory records.
Matrix events are first target-set entries observed on the native timestep
grid. Their event and last-observed times are validated against that clock.
The synthesis declares this sampled-time target; crossings and recrossings
between integration ticks have no continuous-time qualification.

## Frozen confirmation and retained reanalysis

After reviewing the pilot, author the final tolerances, bins/history menu, useful
signal, effect sizes, root population, alpha allocation, record ladder, costs and
stopping selection in a confirmation definition. The public confirmation route
authenticates the complete development parent, binds its lineage, and rejects
reuse of exposed parent roots:

Both supplied confirmation definitions are planning documents. Before `confirm`,
fill `settings.confirmation` with the exact `ConfirmationSelection` fields in
`domains/matrix/model_free/confirmation.py`: named primary endpoints with positive
decimal practical effects and matching units, complete assigned-root target,
declared finite-age law, detection or conditional equivalence goal, fixed root
census/record ladder, independent verification choices, the authenticated parent
readout hash and the measured-host capacity basis. Select finite positive
`resources.memory_bytes`, `wall_time_seconds` and `output_bytes`; never use arbitrary
large placeholders as a feasibility result. `read` prints
`confirmation_parent_readout_sha256`, or obtain it through the public
`parent_readout_sha256(scientific_result)` helper. The separate metrics hash uses
its documented newline encoding and must not be substituted.

Nominal error is first allocated by `inference.module_alpha_weights` across M0–M7;
positive weights must sum to at most one. The default is one eighth each.
Each module then divides its own allowance across its declared family. This
protects the finite bounds only under their stated assumptions; a normal or
jackknife interval remains approximate. Changing a weight after inspecting
results is an exploratory change. Primary M1 service-gain and M3 adequacy-gain
effects must exactly equal `formation.probability_gain_margin`; the primary M2
receiver-error effect must equal `memory.tolerance`, and the primary M4
destination-bound effect must equal `response.certificate_tolerance`. Authoring
rejects disagreement, including a declared tighter effect with a looser actual
receiver test. Other endpoint effects, including M3 signed response contrasts,
are explicitly recorded precision targets without an implemented practical-effect
decision. A declaration grants no automatic success: assessment still uses each
implemented interval, numerical premise and receiver status.

```sh
uv run --no-sync python scripts/examples/model_free_matrix.py \
  --operation confirm --prepare-only --project-root /absolute/empirical_lawhood \
  --workspace /absolute/runs/model-free-confirmation \
  --parent-workspace /absolute/runs/model-free-pilot \
  --definition programmes/foundations/emergent-structure/workflows/model-free/confirmation.json
```

The `--prepare-only` selection also works for confirmation and reanalysis. It
authenticates and freezes the complete inquiry without executing native work.
Inspect the prepared workspace, then use `--operation execute` on it.

The public successor/deployment creators authenticate their live parent before
publishing new specifications. A generic immutable lineage record only binds
declared parent identities; it does not reauthenticate parent custody, establish
global seed freshness or create a protected outcome-blind service. Readout
labels state that narrower scope. If the closing parent guard refuses retained
reanalysis, unselected copied raw companions may remain but no executable
specification or sources record is published. Keep that abandoned directory
for diagnosis and choose a fresh destination on retry.

To recompute only one scientific module, copy the original definition and retain
that module in each relevant root's `modules` list. Keep its complete assigned
root population and original physical settings. Use `--operation reanalyse` with the
original native parent and a fresh workspace. It copies exact authenticated array
companions inside the active read guard, creates only analysis/synthesis tasks,
and preserves exposed status. It cannot change native clocks, forces, sampling,
observation direction or acquired record lengths. M2-only reanalysis can change
the explicitly supported bins, dimensions, lag/history menu, conditioning support,
receiver tolerances, alpha, age anchors and optional descriptive diagnostics.
`memory-reanalysis.json` gives an editable example for the pilot. Changed-menu
bands are fixed-menu exploratory calculations without a selection adjustment;
they do not create fresh equivalence or confirmatory claims.

## Optional learned historical comparator

The separate definition `relation-benchmark.json` uses the existing classical
series entry point. Its nine training coordinates vary temperature, friction and
cross coupling; all model selection uses whole-root folds with matched baseline
and structural budgets. A complete-root CAL maximum freezes the residual radius.
CONF predictions are committed before the actual response future is read.

```sh
uv run --no-sync python scripts/examples/classical_matrix_series.py \
  --operation prepare --project-root /absolute/empirical_lawhood \
  --workspace /absolute/runs/model-free-relation-comparator \
  --definition programmes/foundations/emergent-structure/workflows/model-free/relation-benchmark.json
```

Execute/read/recover through the same entry point. Rank-deficient parameters,
constant targets, missing CAL roots and empty admission regions remain visible.
Held temperature/coupling coordinates do not inherit nominal calibration coverage.
The original paper/E1–E6 evidence is unchanged; this is a new source-bound comparison.

## Rubisco transfer and acceptance

The immediate transfer is native-action qualification, signed WT/I95M error
accounting, preparation applicability and finite-response challenges for M50 Q1–Q6.
Later memory, equilibrium and first-passage transfers require their own physical
trajectory generator, measure, entry population and chemical connection.

The [receiver results](../../programmes/foundations/emergent-structure/records/model-free-receiver-results.md) report the scientific findings. The [gap map](../../programmes/foundations/emergent-structure/workflows/model-free/gap-coverage.json) records the implementation and empirical status of G01–G18.

## Population resource measurements

Add `--metrics-json /absolute/runs/metrics/read-01.json` to an ordinary `read`,
`reanalyse` or other invocation. The fresh file records elapsed time, separately
scoped process/reaped-child lifetime RSS maxima, available kernel IO counters,
and an exact canonical hash/byte count of the already returned scientific result.
It performs no additional custody read or statistical replay. Do not add RSS
maxima together or interpret timing as proof of native work omitted. Compare
result hashes across cold reads, and inspect graph/receipt work for reanalysis.
