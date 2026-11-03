# Plant structural-score rejection screen v1

SPDX-License-Identifier: CC-BY-4.0

**Frozen before execution, 10 October 2026.** This is one bounded, exposed conventional
supplier screen after the [nearest-neighbour precursor](plant-prediction-result.md)
failed to discriminate any mutant from its parent. At this freeze, no structural-screen fit or
evaluation had run. Retain these reviewed protocol bytes before execution; software
ordering does not turn published outcomes into fresh biological evidence.

## Question, sources and complete denominator

Can deposited structural plausibility and site conservation supply useful
parent–mutant turnover and specificity contrasts at sites excluded from fitting,
beyond both no change and a training-only mean response? Success would earn an
independent mutation/context assessment, rather than establish a qualified kinetic
supplier, consequential EL advantage or a nomination.

Use the admitted McDonald 2026 panel, fingerprint
`23e913faf1c50f6e4afbbbbe642521e4894e32c891eb1d913eac1107862a73d0`,
with its exact S8-derived A369 bacterial LSU parent and constant 123-aa SSU.
Use the separate native parent and variant kinetic records; this successor does
not borrow the frozen KNN protocol identity. The focal roster remains I251L,
T391C, T391I, T391V, A438R, I465V, N468D, N468Q and A470R, grouped at sites
251/391/438/465/468/470. All nine enter every focal method/endpoint summary.
A369V remains a separately retained **unscored diagnostic**: the native-V369
structural scan has V369A, not an A369V score or a deposited numerical WT score.
Do not invent the missing likelihood, a WT subtraction or diagnostic prediction.

The original S1 workbook has SHA-256
`01c58e35fa43a8cc1a363d58ca4e4c5e3ff2c262c5c4f3b10002ceb3c869ff26`.
Admit a bounded, source-owned projection of its `4RUB DMS` and
`Conservation scores` sheets, preserving native cell addresses, attributes,
numeric tokens, member hashes and workbook inventory. The existing generic
1 MiB decoder bound is not weakened to admit the larger DMS member. Bind the
reviewed native score projection, source panel, producing package/environment and
frozen protocol in the retained execution record.

The [primary publication](https://doi.org/10.1126/sciadv.aeh3246) and its
[released source](https://github.com/julielmcdonald/RubiscoMLDE) define these
features. The deposited 4RUB value is ESM-IF1's average conditional log likelihood
over the mutant target chain, using the fixed closed, activated, CABP-bound
complex backbone. It is structural/evolutionary plausibility, not a rate or
specificity measurement. The structural native LSU contains V369; the assay
parent contains A369. These are explicitly transferred **native-V369-context
proxy features**, not scores computed for the exact A369 double-mutant context.
No inference of productive-cycle dynamics follows from the single bound pose.

| Edit | 4RUB score cell | Exact numeric token |
|---|---|---:|
| I251L | B4539 | -0.31187425839003602 |
| T391C | B7204 | -0.31822260374663902 |
| T391I | B7202 | -0.31658801007014398 |
| T391V | B7198 | -0.31319553826444801 |
| A438R | B8091 | -0.31075275380124301 |
| I465V | B8608 | -0.30369820543514697 |
| N468D | B8661 | -0.30402795935189803 |
| N468Q | B8671 | -0.31353510374663901 |
| A470R | B8705 | -0.31264530304939497 |

Land-plant conservation is the source percentage of aligned land-plant sequences
matching the **native WT residue at that site**, not the frequency or preference
of the candidate amino acid. Use exact S1 column C tokens: I251, C252,
`61.764705880000001`; T391, C392, `100`; A438, C439, `100`; I465, C466, `100`;
N468, C469, `14.70588235`; A470, C471, `11.764705879999999`. Divide by 100 for
the numeric feature. T391C/I/V share conservation, as do N468D/Q. The paper
describes 69 curated land-plant sequences; these stored percentages do not
authenticate a new independent sample count. Do not replace them with rounded
CSV values or infer an effective denominator from their decimals.

Both selected features cover all nine focal alleles. The 1RLC scan covers six,
omitting N468D/Q and A470R; it is excluded from this fit family. The deposited
ESM-1b/v recommendation list covers none of the nine focal alleles numerically.
Absent recommendations are not zero likelihood or zero effect. No model weights,
large embeddings, structure generation or additional features enter this screen.

## Frozen five methods and nested site holdouts

For each endpoint independently, use the exact positive source means to form
`y = ln(mutant mean / measured A369-parent mean)`. Endpoints are intrinsic
`KCAT_C` and `SPECIFICITY_CO`; aerobic affinity or efficiency is not substituted
for specificity. Preserve the original Decimal values; numerical fitting uses
declared float64 NumPy arithmetic and retains all finite derived values.

The five methods are parent/no change (`yhat = 0`), training-only equal-site mean
response, primary **IF plus land-plant conservation ridge**, and separately
predeclared **IF-only** and **conservation-only** ridge ablations. Ablations
diagnose feature contribution; an ablation cannot retrospectively replace the
primary family based on exposed performance. No interactions, alternative
conservation columns, nonlinear kernels, hand-selected subsets or outcome-driven
feature additions are admitted.

There are six outer leave-site-out folds. All alleles at the held site leave
training together, including T391C/I/V and N468D/Q. Each outer training set has
five sites. For each ridge family and endpoint, tune alpha in exactly
`0.1, 1, 10` by five inner leave-site-out folds over those training sites.
An inner fit therefore has four sites. No random-row split is used.

Within **each** fit, a training site receives weight `1 / number of training
sites`, divided equally among its alleles. Compute weighted feature means and
population standard deviations from that fit's training rows alone. A constant
training column becomes zero for training and queries; preserve its constant
status explicitly. Query features are transformed using those training values.
The fitter receives only training responses and label-free query features; the
cross-fit orchestrator necessarily holds the published labels used as training
in other folds. There is no claim that the orchestrator never saw those labels.

Fit the unpenalized intercept and penalized feature coefficients by minimizing
`sum(weight * (y - intercept - X_standardized @ beta)^2) + alpha * sum(beta^2)`.
Use NumPy's maintained linear solve; refuse singular/nonfinite results rather
than switching solvers, clamping outputs or deleting rows. The alpha score is
the equally weighted mean of the five inner held-site mean absolute log-contrast
errors. Select the lowest score; exact ties select the larger alpha. Selection
is separate for each family/endpoint/outer fold. Refit on all five outer training
sites with that selected alpha. The complete finite workload is at most
**576 small ridge fits**, plus the declared baselines.

The training-mean baseline is the outer-training equal-site mean `y` for that
endpoint. Retain it beside no change: an intercept learned from this selected
panel can improve error without feature-driven mutation discrimination.

Commit all 90 outer forecasts (nine cases, five methods, two endpoints), the
unscored diagnostic, exact inner/outer rosters, source-label fingerprints,
training scalers/weights, coefficients, alpha scores/choices and source/protocol
identities before the metric stage. Recover raw endpoint forecasts as
`parent mean * exp(yhat)`; refuse nonfinite/nonpositive numerical outputs.
The direct pure diagnostic may use an existing analytical carrier. It does not
claim generic task receipts or execution registration that did not occur.

## Complete reporting and finite stopping decision

Report every case/method/endpoint predicted log contrast, raw forecast, observed
mean, absolute raw error and absolute log-contrast error. Primary summaries are
equal-site mean absolute log-contrast error for each endpoint separately.
Secondary summaries retain nine-row log MAE/RMSE and raw endpoint MAE, with both
nine-row and equal-site weightings. Do not pool endpoints or compensate a loss
of specificity prediction with turnover improvement.

Retain point sign agreement with zero contrasts explicitly tied, and enumerate
the four same-site unordered allele comparisons: T391C/I, T391C/V, T391I/V and
N468D/Q. Compare predicted and observed point-mean ordering for each endpoint,
retaining ties. These are descriptive comparisons on correlated, selected source
means, not biological replication or significance tests. In particular, the
primary paper finds no significant specificity effect; neither mean ordering
nor a successful specificity prediction proves preservation or equivalence.
Retain forecast dispersion and deviation from the training-mean baseline to show
whether any error improvement contains feature-driven discrimination.

The primary family must lower the equal-site log MAE below **both** baselines on
**each** endpoint to pass the aggregate rejection screen. Report the full sign,
same-site order and dispersion results even if that condition holds; an
intercept-only or allele-insensitive benefit does not establish a usable mutation
response. No retrospectively selected 10%/3% gate, biological bootstrap or
calibrated uncertainty is supplied. A369V is excluded from all focal summaries.

A negative/trade-off result stops this declared score family on this panel.
Do not iterate alternative kernels until one wins on the same exposed nine.
A positive, feature-sensitive result only justifies acquiring or admitting an
independent mutation/background assessment. Native-V369 to A369 transfer,
selection of the assayed mutants, unknown assay pairing, one shared parent and
six site clusters limit either result. High-specificity red-algal transport and
the programme's consequential EL comparison remain separate open gates.

Cap preparation/computation/evaluation at **600 CPU seconds** and **128 MiB**
retained analytical output; record actual time and bytes. Use the locked selected
NumPy profile with cold imports, no GPU and no optional protein-model weights.
Protocol/source or numerical-rule changes require a successor before execution.
Retain all failed/unevaluable outcomes without new scientific authority claims.
