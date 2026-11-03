# H287 native kinetic constraints and assay roles

SPDX-License-Identifier: CC-BY-4.0

State: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The user-supplied full primary paper now admits native H287 methods and
numerical constraints for the provisional
[coupled-chemistry test](coupled-chemistry-entry.md). Harpel, Larimer and
Hartman, *Protein Science* **7(3):730–738 (1998)**, examines **H287N/H287Q**
against its own authentic R. rubrum WT. This is exposed literature with
censored/approximate observations, not a new kinetic experiment, a fitted
response or a forecast. [Primary article](https://doi.org/10.1002/pro.5560070322).

The exact unchanged PDF is retained at
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-h287-user-pdf-v1/9541405-original.pdf`,
**3,250,450 bytes**, SHA-256
`a7ce05fbcad008bb705d5017bd2eed972eab695f0c9ae3b8c45ef508d0570f3f`.
The [source-admission note](h287-source-admission.md) records official metadata
joins, all nine native page renders/texts, complete hashes/census, costs and
preserved historical access failures. All nine pages were visually inspected;
root independently checked full printed **732/733/734/736**. There are
**seven figures / zero standalone numbered kinetic tables**. The numbers
below come from native prose/captions and Figure 7's printed inset; no curve
or chromatogram has been digitized.

## Complete own-WT / N / Q endpoint roster

Approximation signs, inequalities, detection limits and missing cells are part
of the source observations. No selected observation has a reported native SD,
SEM, confidence interval or replicate count. Graph symbols do not establish
independent sample counts.

| Native endpoint | Own WT | H287N | H287Q | Printed source |
|---|---|---|---|---|
| Overall carboxylation activity relative to own WT | Reference; no absolute rate point supplied | **~0.05%** of WT | **<0.001%** of WT | 731, 734 |
| Product-profile specificity τ | **~11** | **~0.9** | **~0.8**, estimated with identification limits | 733 |
| RuBP enolization by C3 detritiation | Reference curve; no rate digitized | Not significantly above **~0.1% of WT** detection limit | Same detection limit/censor | 732 |
| Isolated CKABP **hydrolysis/decarboxylation** ratio | **≥0.9** | **≤0.1**, at discrimination limit | Not reported | 732 |
| CABP antagonist exchange **t₁/₂**, h | **34** | **90** | **120** | 734, Fig. 7 inset |
| Mg²⁺-dependent CABP complex stoichiometry | Reference complex; no exact point digitized | **~1 CABP molecule/active site** | **~1 CABP molecule/active site** | 733 |
| Bound activator ¹⁴CO₂ / active-site concentration | **Unity** | **Unity** | No separate numerical point reported | 733 |

The retained structured projection has **21 explicit cells = seven endpoint
classes × three genotypes**, preserving every unreported/censored cell. This
is a documentary denominator, not 21 independent experiments. Native mutant
**Kₘ and Vmax were too low to determine accurately**; there is no absolute
H287N/H287Q kcat in s⁻¹ to substitute into the D263 panel. The paper's
approximately 10³-fold H287N abstract wording and its more specific ~0.05%
body observation remain different source precision levels. The earlier
preliminary claim of 1% H287N activity is explicitly rejected by this paper,
not pooled as another estimate of the same preparation.

## Parent, construct and normalization

The mutant **R. rubrum rbc** gene was derived from the WT gene carried on
**pFL245**, expressed in **E. coli MV1190**. The paper assigns **pFL342 /
AAC** to H287N and **pFL334 / CAG** to H287Q and verifies the mutation region
by dideoxy sequencing. The earlier independently made Lorimer H287N vector
was also expressed in MV1190; identical activities/characteristics and product
profiles are reported. The own WT comparator was **authentic enzyme isolated
from R. rubrum**, so it does not have the recombinant mutants' identical
production history. Mutant purity was **>98%** by PAGE; full-length products
and stable dimers were supported by electrophoresis.

Protein concentrations use **A280: 1.2 absorbance units for 1 mg/mL**, with
reported protein/protomer concentrations. CABP binding/activation experiments
are separate controls; they do not retrospectively turn the relative rate
observations into CABP-normalized absolute kcat. The full plasmid/protein
sequence bytes, any tag and exact correspondence to deposited 9RUB remain
unadmitted. No His₆ construct or assay-WT join is inferred. The
[separate D263 source](reactive-state-supplier-assessment.md) uses pRrHis,
**25 °C**, CABP normalization and its own WT **6.28 s⁻¹ / specificity 9.2**;
none is the H287 WT.

## Separate native assay roles and conditions

**Carboxylation (printed 731/736).** The observable is acid-stable radiolabel
from **[¹⁴C]NaHCO₃ fixation**, assayed at **pH 8 / 23 °C**. Figure 2 uses
**50 mM bicine, 1 mM EDTA, 10 mM MgCl₂, 10% glycerol, 66 mM bicarbonate,
1 mg/mL H287N (20 µM protomer), 3 mM RuBP**, with inhibitor/no-enzyme/no-RuBP
controls; the CABP control is **440 µM**. Mutant signal only slightly exceeds
the assay threshold; no numerical absolute carboxylation LOD is supplied.
H287N rate is unchanged over **0.3–3 mM RuBP**; the quoted own-WT RuBP Kₘ
**12 µM** comes from earlier work. H287N bicarbonate response over **35–60 mM**
is proportionately the same as WT, whose quoted earlier bicarbonate Kₘ is
**approximately 30 mM at pH 8**. This is not a measured mutant dissolved-CO₂
Kₘ. Raising Mg²⁺ **10→55 mM** increases H287N rate by **<15%**. These are
substrate/metal-response controls, not fitted mutant binding constants.

**Enolization (printed 732, Fig. 3).** The observable is detritiation of
**[3-³H]RuBP**, a C3-proton exchange assay. Conditions are **pH 8.0 / 23 °C**,
**50 mM bicine, 10 mM MgCl₂, 1 mM EDTA, 73 mM bicarbonate, 2.9 mM RuBP
(~0.2 Ci/mol), 10% glycerol**. Protein concentrations are **WT 0.04 /
H287N 1.9 / H287Q 3.0 mg/mL**. The theoretical 1%-WT line is a control,
not measured mutant activity. Even at up to **60 µM protomer (3 mg/mL)** or
**eightfold higher substrate specific radioactivity**, neither mutant is
significantly above the **~0.1%-WT** lower detection limit. Do not replace
this with zero or a statistical upper confidence bound. The paper also
discusses proton shuttling without exchange with bulk solvent; loss of
detritiation is therefore not a uniquely measured elementary abstraction
barrier.

**Carboxylated-intermediate processing (printed 732/736, Fig. 4).** Isolated
**[2′-¹⁴C]CKABP** is acid-labile; acid-stable PGA, or terminal-misprocessing
pyruvate, can reflect forward processing. Disproportionate CKABP disappearance
relative to acid-stable product reports decarboxylation. Figure 4 uses
**pH 8.0 / 23 °C**, **50 mM bicine, 10 mM MgCl₂, 1 mM EDTA, 10% glycerol,
66 mM bicarbonate**, **WT 0.005 / H287N 0.02 mg/mL**, with **15 min**
preincubation before **1.6 µM CKABP (~4,300 dpm/nmol)**. The intermediate
preparation carries over **2.3 µM PGA and 10.4 µM RuBP**; the initial PGA
is not new enzyme product. A **separate 5:1 H287N-protomer:CKABP experiment**
promotes complete binding/rapid consumption to minimize spontaneous solution
decarboxylation, whose quoted t₁/₂ is **~1 h**. The reported ratios are
**hydrolysis/decarboxylation ≤0.1 for H287N / ≥0.9 for WT**. Native curves,
possible recapture and accumulated products do not establish a first-pass
branching probability. Transforming R to R/(1+R) would require an additional
two-exclusive-branches/first-pass/no-recapture model; it is not a source-measured
qC. H287Q has no reported corresponding ratio.

**Specificity and product profiles (printed 733/736, Fig. 5).** τ is estimated
from radiometric **PGA/PGyc peak areas** after **[1-³H]RuBP** turnover, with
τ=(vc/vo)[O₂]/[CO₂]. Both products retain the tritium label. The paper
estimates dissolved CO₂ using Henderson–Hasselbalch with **pKₐ₁=6.1**, and
assumes **[O₂]=255 µM**. This is a chromatographic product ratio under gas
assumptions, not a coupled-PGA oxygen-rate readout, elementary admission
constants or an independently measured equilibrium gas concentration.

Figure 5's H287N mixture has **pH 8**, **1 mg/mL enzyme (20 µM protomer),
250 µM RuBP (~5.4 Ci/mol), 50 mM bicine, 10 mM MgCl₂, 1 mM EDTA,
10.3 mM bicarbonate and 10% glycerol**, quenched after **3 h**. H287Q uses
the same components except **1.25 mg/mL (25 µM protomer), 50.1 mM bicarbonate**
and **4.5 h**. Samples are quenched with **1% SDS**, ultrafiltered, then
separated on Mono Q HR 5/5 with an NH₄Cl gradient containing **10 mM sodium
borate**, detected radiometrically. General activity/binding methods specify
23 °C; the Figure 5 caption and product-analysis methods do not separately
restate the product-profile incubation temperature. Preserve that limit rather
than assigning a more specific native condition than the source supplies.

CTBP is another major **exclusively oxygenation-derived** product; DiBP is
an oxygenated-intermediate misprocessing precursor, confirmed for H287N by
**50 mM borate** trapping and authentic DiBP→CTBP conversion, with the latter
data not shown. Therefore PGyc alone omits part of oxygen-path flux: the paper
states that preferential carboxylation impairment is greater than the τ ratio
alone suggests. H287N forms **XuBP** through C3 misprotonation; **DiMP** is
absent at its expected **~21 min** elution. For H287Q, slow turnover and
phosphatase contamination hamper product identification; an **~12 min** peak
remains unknown and Figure 6 says DiMP **may** occur. Do not assign those
ambiguous products or infer quantitative side-product fractions from schematic
Figure 6 or undigitized peaks.

**Activation/CABP binding and exchange (printed 733/734/736).** The
Mg²⁺-dependent ~1:1 mutant CABP complexes and activator-¹⁴CO₂ stoichiometry
are controls for carbamylation/activation. Binding incubations use **pH 8.0 /
23 °C, 10–20 µM active sites, 50 mM bicine, 10 mM MgCl₂, 1 mM EDTA,
10% glycerol, 100 µM CABP and 66 mM bicarbonate**, with the appropriate
ligand labelled at **~2 Ci/mol**, incubated **1 h** before gel filtration.
The exchange challenge adds **1 mM unlabelled CABP**. The Figure 7 inset gives
t₁/₂ **34/90/120 h** for WT/N/Q. CABP is an antagonist/intermediate analogue;
those exchange half-lives are not productive substrate release, catalytic
waiting times, a measured f or turnover bounds.

## What this source now discriminates

The admitted constraints jointly require retention of activation/ligand binding,
severe overall-carboxylation and detritiation impairments, shifted CKABP
processing toward decarboxylation, low product-profile specificity and oxygenated
intermediate misprocessing. A shared reactive occupancy alone cannot account
for their specificity changes in a common-state model. They provide a stronger
exposed challenge to the proposed proton-relay/commitment hypothesis; they do
not certify that hypothesis, its physical realization or EL superiority.

A future assessment must retain the own-WT preparation, all three genotypes,
approximate/censored and unreported cells, gas/product metrology and distinct
partial-reaction roles. It cannot import H287 activation controls as absolute
kcat normalization, fit genotype-specific prefactors to these exposed values,
or promote them to fresh held-out evidence. The full article resolves the
previous source-availability blocker; absent absolute kcat/Kₘ, uncertainty,
raw peak/time-course data and exact assay-parent sequence remain limits.
No preparation, QM/SCF, fit, task receipt or phase 2–9 closure follows from
this documentary intake.
