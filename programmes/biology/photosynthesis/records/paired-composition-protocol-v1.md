# Paired-subunit composition rejection pilot v1

SPDX-License-Identifier: CC-BY-4.0

**Frozen before the first source-label fit, 10 October 2026.** This is one
bounded, exposed conventional pilot following the
[paired-source design audit](paired-subunit-design-audit.md). It asks whether
simple mutation-sensitive composition channels warrant more expensive
site/context research. It does not claim packing, electrostatic microstates,
mechanistic identification, an EL comparison or a nomination. All biological
labels were already exposed; ordering software stages does not blind them.

## Exact sources and complete roles

Retain Wilson's authentic nineteen-row canonical panel, exact bytes SHA-256
`097f682b0df3f1f34754df28aafaa55278650e329b6b9021a45b605feaea9db2`,
with its original artifact-plane manifest and root. Fifteen Te rows have verified
MG000148.1 paired protein recipes. Four Se rows remain in the source census but
cannot borrow Te sequences and do not enter this fit. The Te-WT means **7.4 s⁻¹
and 53.3** are the shared response anchor. The fourteen mutants, including the
single V98M-on-P415A observation, enter fitting. No WT zero-response row enters
the loss or validation denominator. Keep native SE/sample ranges, unknown
endpoint pairing, selection and expression/assembly contexts separately.
[Primary Wilson source](https://doi.org/10.1074/jbc.M117.810861).

The external potato source is the reviewed factual projection, exact bytes
SHA-256 `d20c9505c109e6c560587d1a094728fd8fb3d6c1341d81f26d90e8c8bc583b4a`,
and its closed `followup-potato7/source-register-potato7-v1.json`, SHA-256
`6d12c9689174f2489bf64d0c495ac86f7d30ca8cdd48883c67eb1045139e2f39`.
Authenticate every member before fitting. Keep all seven kinetic contexts and
the original error/replication declarations. The three native/mixed controls
remain controls without exact homogeneous paired recipes; do not forecast them
with an invented mixture. pS1 is the measured parent calibration **3.0 s⁻¹ /
84.5**. The complete external contrast roster is **pS2, pS3, pST relative to
pS1**, each on both endpoints. pS1 calibrates recovery and is not a fourth
independent prediction case. No potato response enters fitting, scaling, model
or hyperparameter selection. Its exposed labels informed selection of this
pilot question, rather than being unknown prospective observations.
[Primary potato source](https://pmc.ncbi.nlm.nih.gov/articles/PMC7474299/).

Use full translated/reported paired protein recipes, including engineered SP
and the common 477-aa LSU. pS2/pS3 are source-declared derived amino-acid recipes,
without invented synthetic DNA; processing remains unmeasured. Include pS3's
four substitutions and all pST sequence differences, including unequal lengths.
No alignment or cleavage claim is made by a composition sum. Original source
articles and source register files remain unchanged.

Use precisely native AAindex **GRAR740103** (Grantham volume index) and
**KYTJ820101** (Kyte–Doolittle hydropathy). The initially requested KYTD820101
is absent; the retained original provider refusal and authoritative index list
preserve that correction. The native volume entry provides no units field:
these numbers are an index, not measured Å³ or a packing observable. Retain the
entire small original AAindex1 release and the two-entry factual projection.
Descriptor original SHA-256: `560f102dbee8ca9837186c4b2b93e253ea6efc58c88617234cef4e54bd61f676`.
Descriptor projection SHA-256: `b646392c7019be83ae13d7f8bb3838c9df9a5d9f700d3e228d5a71e7b78e3f32`.
The provider permits local reuse and requests primary citation; no blanket
redistribution license is assumed for the external release.
[Official AAindex](https://www.genome.jp/aaindex/),
[primary availability statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC2238890/),
[Kyte–Doolittle](https://doi.org/10.1016/0022-2836(82)90515-0) and
[Grantham](https://doi.org/10.1126/science.185.4154.862).

## Fixed position-blind relation and controls

For each chain, compute exact total composition differences between variant
and its stated parent: sums of the volume index and hydropathy, plus formal
charge **K/R=+1, D/E=−1, all other residues=0, including H=0**. The charge is
an explicit descriptor convention, without assigning a measured pH-dependent
microstate. Both training and external queries use the same table and
convention. No averaging by chain length or multiplication by eight is used.
The six-channel order is LSU volume/hydropathy/charge, then SSU
volume/hydropathy/charge. Composition-identical rearrangements have identical
features; position and contacts are unavailable to this model.

For each endpoint independently, model **ln(variant mean / measured parent
mean)**. Final potato means are recovered using pS1, never using a Te absolute
rate as the potato parent. No affinity, growth, mass-normalized activity or
expression surrogate replaces an intrinsic endpoint. Final output retains
original Decimal means and derived Decimal strings from declared float64 fits.
Composition, weights, log transformations and metric arithmetic use an explicit
fifty-digit Decimal context, independent of the caller context.

There are five methods:

1. Parent/no change: zero log contrast.
2. Wilson training-only equal-block mean log response, constant for non-parent
   queries. This is a comparator, without mutation discrimination or a general
   through-origin response claim.
3. Primary **split-channel through-origin ridge**, fixed alpha=1.
4. Predeclared **pooled-channel through-origin ridge** ablation, fixed alpha=1;
   add each matching LSU/SSU channel before scaling. This tests whether chain
   separation helps, without selecting the ablation retrospectively.
5. Stronger conventional **anchored RBF kernel ridge**, using the same six
   channels, with the finite Wilson-only tuning described below. It is allowed
   more small solves than the primary. Any useful delivery is conventional
   success, not an EL consequence.

The primary makes an explicit additive/background-invariant descriptor prior;
Wilson's shared P415A design does not identify zero-LSU SSU effects. Regularized
coefficients choose forecasts without resolving that alias. Potato has no LSU
contrast and cannot validate a coupled interaction response or red transport.

## Whole-block fitting and frozen numerical rules

Link Wilson mutant rows sharing any edited **subunit/site**, including alternate
alleles at that site; take transitive connected components. Every P415A row and
both F345I-containing rows belong to one **thirteen-mutant block**. The lone
V300A row is the second block. Retain this exact membership and the WT anchor
separately. These are leakage-control blocks, not independent biological units.

Within each fit, a training block receives equal weight, divided equally among
its rows. The final weights are 1/26 for each of the thirteen linked rows and
1/2 for V300A. The loss choice is fixed and does not create scientific n. Two
blocks provide weak validation: when the large block is held, the sole training
row has no SSU edit. That fold cannot validate an SSU response. Do not describe
two-block diagnostics as broad out-of-site generalization or meaningful SSU
tuning.

For each fit's design columns, compute training-only weighted root-mean-square
scales from zero. Do not mean-center or fit an intercept; both would change the
parent anchor. Preserve constant **nonzero** columns. A training column which
is identically zero has scale 1 and is explicitly inactive for both training
and queries, including kernel distance. This prevents a completely unlearned
channel from masquerading as predicted response. Query values never alter
scales. Do not clamp external features to the observed range; retain range and
inactive-channel warnings descriptively, without excluding a potato case.

The linear objective is weighted mean square error plus alpha times coefficient
norm squared. Fixed alpha=1 applies to primary and pooled methods in both
leave-block diagnostics and final fits. Each has two diagnostics per endpoint,
then one final fit on all fourteen mutants; no diagnostic score chooses alpha.

For the stronger comparator use the parent-anchored kernel
`k0(x,z)=exp(−gamma*||x−z||²)−exp(−gamma*||x||²)−exp(−gamma*||z||²)+1`.
This makes the predicted no-edit response exactly zero. Use the weighted kernel
ridge solve with alpha in **0.1, 1, 10** and gamma in **0.1, 1, 10**. Score each
pair by the equally weighted mean of the two held-block mean absolute log
errors. Select the lowest score; exact ties select larger alpha then smaller
gamma. Refit on all fourteen mutants. This limited selection uses Wilson
responses only and inherits the two-block weakness.

Use maintained NumPy float64 linear solves, no optimizer, surrogate biological
replicates or arbitrary microscopic rates. Refuse singular/nonfinite operands
or results rather than deleting rows, switching solvers or silently clipping.
Normalize only the exact mathematical zero-query identity after finite-result
checks. The complete workload is **50 small fits**: six for each fixed family
and 38 for the stronger comparator. No GPU or new optional scientific dependency.

## Ordering, assessment and stop

Authenticate and retain original input bytes, native source panel/projection,
full paired recipe/feature census, frozen protocol, launcher, exact producing
package/archive and dependency lock before the first fit. Retain all fitted
states, block diagnostics, kernel scores/selection and all **30 external
forecasts** before reading the metric stage: three cases, five methods, two
endpoints. The caller has already exposed source labels, but the fitting
functions accept only Wilson training responses and label-free queries.
A parent-zero query is retained as a software/model identity check, without
entering the three-case metric denominator. Use genuine development artifact
custody; this direct analytical pilot creates **zero registered task receipts**.

Report every prediction, observed source mean, raw error and absolute log error.
Primary summaries give equal-three-contrast log MAE for each endpoint separately;
retain log RMSE, raw MAE and the full point-sign/order census. No endpoint can
compensate for failure on the other. The shared parent, published sample ranges,
four-site confounding and unpaired endpoint preparations remain explicit.
No bootstrap, calibrated intervals, biological significance or equivalence
claim is supplied by this pilot.

The primary passes the aggregate rejection screen only if its log MAE is lower
than **both parent and training-mean controls on each endpoint**. Additionally,
require the point-direction patterns pS3 **positive/positive** and pST
**positive/negative**, with predicted separation on each endpoint. Record pS2's
zero-turnover point tie and negative specificity, including every error.
These are declared usefulness checks on exposed means, not uncertainty claims.
Apply these same frozen usefulness checks descriptively to each predeclared
mutation-sensitive comparator, preserving the primary decision separately.
Keep the stronger comparator and pooled ablation results regardless of pass/fail;
neither can replace a failed primary after seeing potato performance.

Primary failure closes this fixed split-channel additive proposal for this
Wilson-to-potato construction, rather than rejecting chemistry generally or
I95M. A successful predeclared conventional comparator remains useful conventional
evidence, without retrospectively changing the primary method. Close the whole
tested set only if all three predeclared mutation-sensitive methods fail these
checks. Do not search descriptor tables, charge conventions, kernels, weights or
potato subsets until one wins on these same labels. Success only warrants a
separate site/context and high-specificity-parent applicability assessment.
Neither outcome closes the consequential EL or nomination gates.

Cap preparation/fitting/metrics at **600 CPU seconds** and retained analytical
packet at **128 MiB**, reporting actual time, bytes, failed/unevaluable rows and
zero task receipts. The selected locked `rubisco-prediction` environment is
CPython 3.11.14, NumPy 2.4.6, SciPy 1.17.1 and RapidFuzz 3.14.3; use
`uv run --no-sync`. Any source, roster, numerical or criterion change requires
a successor protocol before execution; keep producing records unchanged.
