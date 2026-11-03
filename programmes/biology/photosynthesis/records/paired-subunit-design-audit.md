# Paired-subunit response design audit

SPDX-License-Identifier: CC-BY-4.0

This 10 October 2026 successor resolves several source prerequisites for the
[paired-subunit follow-up](paired-subunit-supplier-assessment.md). It does not
supply a candidate-response model. New acquisition and offline source/design
inspection remain separate from canonical scientific publication, fitting,
registered execution and qualification. All inspected biochemical labels are
exposed.

## Potato sequence and intervention identities

The deposited constructs identify potato LSU-only **MT596797.1**, potato
LSU/pS1 **MT596798.1**, and potato LSU/pST **MT596799.1**. The separately retained
INSDC records are **ENA EMBL-format originals**, rather than GenBank-format
payloads. Their translated **477-aa LSU** recipes agree. The **125-aa pS1**
starts MSPQ; **123-aa pST** starts MSPK. Both retain the engineered SP extension
and neither has a C-terminal His₆ tail. The His-tagged tobacco IR experiment
is a separate context. Native SSU positions n ≥ 2 map to translated n+2:
22→24, 55→57, 57→59, 88→90, 90→92 and 92→94. These records specify constructs
without authenticating a particular kinetic preparation or measuring its
processing.
[Primary construct methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7474299/).

Native Figure 8 assigns the following isoform states:

| Native SSU position | pS1 | pS2 | pS3 |
|---|---|---|---|
| 22 | T | S | S |
| 55 | N | N | H |
| 57 | K | K | S |
| 88 | Q | E | Q |
| 90 | C | A | A |
| 92 | N | K | N |

The deposited pS1 and primary sequence-model join support **N55H/K57S** in
pS3, resolving the reversed directions in parts of the narrative. More
importantly, **pS1 → pS3 is T22S/N55H/K57S/C90A**; pS2 → pS3 also changes
four residues. The reported joint point gain therefore does not isolate a
two-substitution loop effect. The independently retained primary pS3 sequence
model **PGSC0003DMT400062138** has a 123-aa suffix agreeing with the reported
four-site pS3 recipe. This supports the protein specification, without measuring
processing or authenticating unacquired synthetic pS3 DNA.

The article also claims a four-nucleotide plastome difference between pS1/pS3.
Their four reported amino-acid differences require at least six coding-base
changes under the standard code: T→S ≥1, N→H ≥1, K→S ≥2 and C→A ≥2. Preserve
this additional source conflict; do not manufacture a nucleotide recipe to make
both statements agree. Do not invent measured single-mutant endpoints.
[Primary figures and source](https://pmc.ncbi.nlm.nih.gov/articles/PMC7474299/).

The complete seven-context endpoint table retains native tobacco/potato
controls, potato LSU with resident tobacco SSUs, and four engineered single-SSU
contexts. The mixed control cannot become a homogeneous sequence pair. Endpoint
sample counts and SD retain their source roles. Table 2 explicitly calls the
counts **biological samples**: 5–6 for turnover and 10–11 for specificity.
Individual preparation independence and cross-endpoint pairing remain unknown;
do not infer a joint n or confidence bounds. Aerobic efficiency is derived
from averaged turnover/affinity, rather than another directly measured target.

## Wilson training design and transport

The nineteen-row source contains **fifteen Te contexts** with verified paired
protein specifications and four Se contexts without the corresponding admitted
parent recipe. The Te mutation-incidence matrix has fourteen substitution
columns plus an intercept, with exact rank **thirteen**. L74M and D397N are
inseparable; the available Y36N/G112D/R51H combinations do not isolate all
three effects.

Every observed SSU edit accompanies LSU **P415A**. Consequently, an SSU main
effect and its P415A interaction produce identical columns on this panel.
V98M appears once, on that background. Its native-WT response and its proposed
G. partita I95M response cannot be recovered by identifying those coefficients
from this source. The already assessed A48V/A398T quartet supplies a narrower
combination test, without resolving the V98M interaction.
[Primary Wilson study](https://doi.org/10.1074/jbc.M117.810861).

This is a design limitation of that unconstrained fitted relation, not an
impossibility theorem for physical models or useful prediction. A regularizer,
zero-interaction rule or transported physicochemical prior can choose a
forecast, but must retain its assumption and earn separate assessment. Neither
the raw row count nor a unique numerical fit establishes identification. The
retained endpoint-free incidence audit contains both complete matrices and
exact rational nullspace witnesses under
`/tmp/empirical-lawhood-rubisco-20261009/paired-subunit-design-audit-v1`.

## New open-state and composition evidence

Askey 2026 provides homogeneous Arabidopsis SSU comparisons, open-state
structures **9N37/9MUR**, and released carboxylation/RuBP/recovery data. It
connects local flexibility with kinetics, while distinguishing local and global
stability. The structures differ in Mg addition; kinetic and structural tag
contexts also require exact joins. It does **not** provide a newly measured
homogeneous two-endpoint specificity panel or a calibrated red-edit response.
[Primary study](https://doi.org/10.1073/pnas.2519914123).

Reynolds 2026 resolves native mixed-SSU spatial arrangements. This is direct
composition evidence, without a new mapping from those arrangements to both
intrinsic endpoints.
[Primary companion](https://doi.org/10.1073/pnas.2519949123).

Cavanagh's Table 2 gives the following 25 °C means/SE for plants grown at
different temperatures:

| Growth temperature | Turnover (s⁻¹) | Specificity |
|---|---:|---:|
| 10 °C | 3.31 ± 0.09 | 75.1 ± 1.0 |
| 20 °C | 3.11 ± 0.08 | 76.9 ± 1.0 |
| 30 °C | 2.78 ± 0.10 | 78.0 ± 0.83 |

These mixed preparations also differ in growth history. Their reported five to
seven replicates do not identify pure-isoform specificity. Combining these
values with Askey's homogeneous turnover would manufacture a new joint assay.
[Primary temperature study](https://doi.org/10.1093/jxb/erac379).

The three unchanged XML originals and complete offline table/supplement
inspection are retained under
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-ssu7`.
Three sandbox DNS failures and three successful successor retrievals remain
recorded separately. No model weights, trajectories or downloaded code were
executed. The inspection is a parsed XML projection, preserving original
payload digests rather than claiming original lexical fragment bytes.

The separate `followup-potato7/source-register-potato7-v1.json` binds the
construct originals, native figures, primary genomic sequence join, complete
seven-context projection and acquisition/inspection helpers. Its factual
projection is **157,911 bytes**, SHA-256
`d20c9505c109e6c560587d1a094728fd8fb3d6c1341d81f26d90e8c8bc583b4a`.
The separate `followup-ssu7/source-register-ssu7-v1.json` binds the three new
XML originals, retrieval failures/successes and offline inspection, with
dependencies on the Wilson design audit and original canonical panel. Both
registers bind this report and retain frozen report bytes. They are source/design
inspection registers, without artifact-plane publication or scientific receipts;
all original packets retain their unchanged identities.

## Next model-admission gate

The potato point directions also reject a single scalar feature with two
parent-anchored **linear** log-response heads. Such forecasts lie on one line
through the origin, whereas pS3 has positive turnover/positive specificity
contrasts and pST has positive turnover/negative specificity contrasts relative
to pS1. A local linear proposal therefore needs at least two non-collinear
mutation-sensitive features; a nonlinear proposal must state its alternative
capacity and assumptions. This is a model-class check, without a biological
significance or universal trade-off claim.

Do not create another installed route before naming the response relation it
would assess. The next proposal must specify:

1. Exact paired proteins, SSU composition, tags/processing and activation/state
   for its training and assessment cases; parent-relative endpoint definitions
   and native units remain separate.
2. A mutation-sensitive SSU/LSU feature or physical observable, its justified
   connection to **both** endpoint changes, and all assumptions resolving the
   training-design aliases above. A bound pose, side-chain score, thermal shift,
   inhibitor release or RuBP affinity alone cannot fill the kinetic role.
3. Training independent of the external potato assessment, with all four
   single-SSU contexts and every control retained. That source can test gain
   and sacrifice discrimination; it cannot validate an isolated two-edit effect
   or red-parent transport.
4. Frozen useful-delivery criteria and parent, training-only and strong paired
   conventional controls. Keep source/background groups together, assess both
   endpoints without compensation, and retain unevaluable/missing cases.
5. A common finite computation/acquisition/human-effort budget and an ablation
   identifying what EL supplies. A conventional reconstruction of the same
   response remains conventional success.
6. A separate applicability assessment before using any green-panel success to
   rank I95M or support the exact high-specificity nomination.

The new source joins make the external assessment more specific. They do not
yet justify a fitted mutation-to-two-endpoint supplier. A supported reduced
relation remains eligible; a full microscopic cycle and new pre-submission
laboratory work are not requirements by default. The consequential EL and
strong nomination gates in phases 2–9 remain open.
