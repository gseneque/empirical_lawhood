# Native plant RubiscoMLDE release assessment

SPDX-License-Identifier: CC-BY-4.0

**Availability:** `inspect_native_release.py` and the complete selected local input packet are not distributed.
Its command records the historical inspection procedure and requires those exact external inputs.
Public source links do not supply the local helper or its retained results.
See the [historical-procedure index](progress.md#availability-of-historical-procedures).

Reviewed 10 October 2026 against the exact publication **10.1126/sciadv.aeh3246**, its complete journal supplements and released author archive. The full publication supplies **direct conventional CO₂/O₂ specificity measurements**, including T391I. The earlier abstract-limited intake cannot support a conclusion that this release contains only growth or aerobic efficiency. Its original report/register remain unchanged; this successor records newly acquired evidence.

The decision is to admit a **source-reported, exposed biochemical panel** for a narrowly scoped successor assessment: ten Table 1 contexts, comprising the immediate parent and nine mutants. This is a useful assessment opportunity, subject to the source and metrology limits below. It supplies neither a calibrated microscopic mutation response nor a strong challenge nomination or EL advantage. No predictor, pretrained model, biochemical experiment or registered task was executed by this audit.

## Original release and custody

Selected local inputs are `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-plant4`. The separate `source-register-plant4.json` binds acquisitions, rejected responses, extracted native members, derivative inspections and preservation checks. This is local acquisition/inspection provenance, not artifact-plane publication, experimental receipts or qualification.

| Original | Actual retained bytes / SHA-256 |
|---|---|
| [Published primary XML, PMC13644767](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13644767/fullTextXML) | 198,187 / `6c37fa27a8a0e1a98442544ecc7fd5113edaa5adebbe7fc96fbe893cfbe2b621` |
| [Complete original supplement collection](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13644767/supplementaryFiles) | 7,453,946 / `cac5c36e2a6079a2c14402278026387509e0f85d88fc750ef3f7972d6b3cd2ce` |
| [Zenodo v1.0 author release](https://zenodo.org/records/21269162) ZIP | 1,081,909 / `87cf0157b31c2f061a73dbb5fa82c7ce5ff4c9a01eb366e24c14ffe957efe6ef` |

The primary XML and HTML identify the correct DOI and contain the complete native Table 1 and methods. The supplement collection has fourteen members, 7,654,543 bytes expanded: the authentic 22-page supplement PDF, its four-workbook ZIP, and twelve figure assets. The native PDF is 5,898,077 bytes; the native table ZIP is 773,918 bytes, with four XLSX members totaling 816,332 bytes expanded. Original member digests and exact archive membership are retained. S1, S4, S5 and S8 were acquired; the current bounded workbook adapter decoded both complete S4 sheets and the complete S8 sheet without Excel or formula execution. Canonical workbook fingerprints are `371a56c91d0c8556bdff67506318774460f20363f18468fb2248f3e764152ae2` and `c1678bb031210b13263a17426ef5aa96496aa0655a534846a987e734f983cc8f`, respectively. These are native workbook records, not an installed family-specific endpoint panel.

The Zenodo archive is the July 8 software release, Git tag v1.0 at `13ee492b65417feabbac7cea1d5ca450ecc6871d`. Its published MD5 matches the downloaded original. It has 33 archive members, 27 files and 3,863,890 bytes expanded. Twenty-six files match current GitHub commit `294eaf1d8ad2b5ad31a54b5b62350a8ecf343df6` by native Git blob digest; only README differs. Code, structures, alignments, scores and enrichment data are separate from journal kinetic measurements. No model weights were acquired or code executed. The archive states MIT; the publication states CC BY 4.0. Retained UniProt reference records keep their own source attribution; no additional service-wide relicensing claim is made.

Twenty-seven bounded HTTP attempts produced twelve usable native/metadata payloads and three rejected HTML CAPTCHA responses. Twelve attempts failed, including five initial sandbox DNS failures, publisher 403s and unavailable OA/PDF endpoints. Requested PMC PDF/ZIP paths returned HTML, retained as rejected responses; their names do not make them PDFs. Official Europe PMC supplied the complete genuine supplements. The main article PDF was not acquired. Missing PDF retrieval is separate from the complete acquired XML/HTML and cannot establish absent measurements.

## Complete measured panel and endpoint meaning

Native Table 1 declares 25 °C and mean ± **SD**. Its complete focal roster is:

| Native variant on the A369 parent | kcatᶜ, s⁻¹ | Direct Sᶜ/ᵒ | S4 counts, turnover / specificity |
|---|---:|---:|---:|
| Wild-type | 3.5 ± 0.5 | 79.7 ± 4.0 | 18 / 10 |
| I251L | 3.1 ± 0.1 | 79.8 ± 3.1 | 3 / 3 |
| T391C | 3.3 ± 0.3 | 79.2 ± 0.6 | 3 / 3 |
| T391I | 4.5 ± 0.4 | 79.9 ± 3.1 | 4 / 3 |
| T391V | 3.3 ± 0.1 | 78.7 ± 3.3 | 3 / 3 |
| A438R | 3.0 ± 0.2 | 78.8 ± 5.0 | 4 / 2 |
| I465V | 3.5 ± 0.2 | 79.1 ± 3.8 | 3 / 3 |
| N468D | 3.0 ± 0.3 | 76.7 ± 3.5 | 3 / 3 |
| N468Q | 3.1 ± 0.3 | 80.8 ± 1.3 | 3 / 3 |
| A470R | 3.6 ± 0.3 | 77.4 ± 0.9 | 3 / 3 |

S4 retains twelve contexts: these ten, the **A369V reversion control** and a **N. tabacum leaf** view. Reversion has reported 3.49 ± 1.0 s⁻¹ and 82.0 ± 4.2 specificity in supplement Table S3; its S4 counts are 4/3. Leaf turnover is present, while specificity is explicitly `n.m.`. Thus S4 has eleven joint-complete contexts and one missing-specificity context, not twelve joint assays. All 55 native turnover values and 39 specificity values remain retained. Independently calculated group means and sample SDs agree with S4 caches within 10⁻¹²; cached source tokens and formulas remain original. This numerical check authenticates interpretation, not biological accuracy.

T391I's exact S4 means/SDs are **4.4967499999999996 / 0.41324841197517032** and **79.850000000000009 / 3.0675071312060513**. Its immediate-parent counterparts are **3.4958333333333331 / 0.45921252929207296** and **79.707999999999998 / 3.9979100095480424**. It is the only Table 1 mutant with both point means above that parent. The paper reports no statistically significant specificity change for any mutant; non-significance does not establish equivalence or preserved specificity within a chosen margin.

Specificity was assayed on purified Rubisco using the **[³H]-RuBP consumption method**, citing Kane 1994. Carboxylation uses **¹⁴CO₂ fixation**, air-equilibrated at 25 °C, five CO₂ concentrations, activation and CABP active-site normalization. Aerobic Kc and kcat/Kcair remain separate quantities. The efficiency column is derived from paired turnover/Kcair values. Oxygen affinity Ko and oxygenation kcat are not supplied as independently measured mutant operands; the discussion proposes further characterization. Direct measured specificity makes their reconstruction unnecessary and does not license inventing them.

S4's N values are **endpoint measurement counts**, with no biological/technical/preparation identifiers linking specificity to turnover. The blocks do not align by row: row 27, for example, belongs to specificity group 7 but turnover group 4. Turnover and Kcair blocks align, and efficiency is their calculated ratio. No cross-endpoint covariance or independent biological n follows. The explicit technical duplicates/three independent preparations in Fig. S5 concern NGS libraries, not kinetic replication. WT pooling and repeated use remain shared context. The text compares extract and purified kinetics, but S4 does not assign each individual value a preparation route.

## Exact translated recipes and distinct assemblies

Supplement S8 supplies six whole-plasmid DNA strings. In `Sheet1!B2`, pET-NtLS-Rca has 9,000 bases. Its plus-strand LSU CDS **4021..5454**, including stop, translates to **477 aa**, equal to P00876 sequence version 2 except **V369A**. Its SSU CDS **5699..6070**, including stop, translates to **123 aa**, exactly P69249 sequence version 1 positions **58..180**. The native SSU reference also has alternative transit/mature-chain annotations; the expressed DNA determines this recipe rather than an assumed processing offset.

The immediate-parent protein digests are LSU `c2848529f02b8a7af725d5af304b2292ba487328eb935acf437ab6b86c84b1f8` and SSU `1387c44309233c1b3b6c006da2ddf0800e8007ca6c87405da6a33feff3cb0370`. Each focal mutant applies exactly its named substitution to this A369 LSU while retaining the 123-aa SSU recipe; the A369V context restores reference V369. Every original residue was verified before applying its edit. `native-panel-inspection.json` retains full parent/mutant translated sequences, original DNA/cell locators and separate hashes. These are source-derived amino-acid recipes, not independently sequenced mutant clones or invented mutant DNA.

Purification coexpresses untagged SSU and a second SSU carrying a cleavable His₆-ubiquitin prefix. `Sheet1!B5` encodes a 219-aa fusion at **236..895**, including stop. Its prefix is exactly 96 aa, ending in ubiquitin `...LRLRGG`, immediately followed by the same 123-aa SSU. The declared ubiquitin cleavage therefore implies that SSU sequence without an extra linker scar. Actual cleavage completeness, terminal processing and specimen-level stoichiometry were not independently measured here; the article's claim of tag-free isolated Rubisco remains a source claim. LSU N-terminal processing is also distinct from its 477-aa translated recipe.

The plant assembly view must remain separate. `Sheet1!B6`, pBI121-NtRbcL, encodes **5354..6976**, including stop: a **540-aa** fusion comprising a 57-aa transit peptide, native **V369** LSU477 and a **C-terminal His₆** tail. It is not the biochemical A369 untagged LSU. The assembly experiment transiently expresses tobacco LSU variants in the engineered N. benthamiana host, retaining endogenous host SSUs; their exact expressed census is not provided. Assembly/gel evidence does not transport the Table 1 kinetics into those plant complexes or establish improved plant photosynthesis. Photosynthetic curves in the paper are model consequences of supplied kinetic values.

## Other denominators and source conflicts

The focal panel does not replace the broader selection denominator. Native S5 retains **949 distinct variant rows across fifty sites**, including the K201 negative-control site. Its native reported library census is 393 covered variants from 931 possible recommended-site variants; 166 appear under selection, 64 are positive, 102 negative/neutral and 227 absent. These are library/enrichment outcomes, not measured intrinsic kinetic labels. S5 marks twenty substitutions for rescreening, including previously tested I465V; Fig. 3 depicts nineteen rescreened substitutions plus WT. Both source views remain retained, without forcing a single inferred denominator. Only the seven subsequently purified choices join the two previously characterized variants in Table 1. Preliminary Q439K and K201A screening failures and the five/ten/twenty-edit growth combinations remain separate negative or missing-kinetic contexts; exact combined clone recipes are not inferred from ranking alone.

A further expression-view discrepancy is retained: Fig. 3 reports A470R %TSP approximately 0.71, while S4's A470R mean is approximately 1.5767; 0.7067 is S4's A438R mean. This does not rewrite or invalidate the independently retained intrinsic endpoint columns, but it prevents an unexamined solubility-to-kinetics join.

The primary kinetic-method XML/HTML literally states **1.3 μM RuBP** in a 0.5-ml reaction, 2 μM purified NtRbcL before 50-fold dilution, and a three-minute endpoint. No additional unlabeled RuBP pool is described; the isotope tracer is CO₂. Under the explicit additional assumption of 0.04 μM active sites after dilution and 1.3 μM total substrate, complete consumption supports at most **0.1806 s⁻¹ averaged over 180 s**, below the table rates. Active fraction, concentration basis and full cited-method reconstruction remain unresolved. The complete supplement supplies no unit correction, and the main PDF could not be inspected. Preserve this **conditional reconstruction conflict**; do not silently replace μM with mM or blanket-reject published means. It limits reproducible metrology claims.

Released model-score mutation indices also require a source correspondence. The raw repository scripts enumerate resolved structural chains, which omit terminal residues; their mutation names are not automatically full LSU coordinates. Native S1 supplies normalized source-labelled entries: T391I is below the WT likelihood in both structural inputs, whereas T391R is recommended in the 1RLC view. This supports the paper's distinction between recommending a locus and directly recommending its best experimentally selected substitution. These likelihoods are not endpoint predictions. The scored native-V369 structural context differs from the assay's A369 background.

An independent sequence-availability check uses the actual S8-derived tobacco parent and its P00876 reference against the previously acquired G. partita O98949/1BWV LSU. Across all optimal alignments under four declared global affine scoring variants, tobacco **V369 corresponds to Galdieria linear position 377, already A**, and tobacco **T391 corresponds to Galdieria linear position 399, already I**. The corresponding 1BWV author labels are 369 ALA and 391 ILE. O98949's 493-aa sequence matches the native structure's canonical LSU. Thus transplanting either named tobacco substitution literally into this Galdieria sequence would make no change. This refutes that particular edit recipe; it does not predict mutation effects, catalytic state equivalence or transport of the tobacco gain. The separate `tobacco-galdieria-alignment-inspection.json` retains input hashes, matched segments, scoring variants and ambiguity checks.

## Admission recommendation and remaining gate

Admit the ten focal contexts, all native S4 observations/control/missing views, exact translated background/subunit recipes and assay-source descriptions as **exposed source-reported evidence**. Retain the method reconstruction conflict and unresolved preparation/processing fields as first-class limits. A family-specific decoder must bind the original XML, native S4/S8 hashes, complete role census and exact native cells; refuse hidden-parent substitution, malformed quantities, invented paired n, inferred oxygenation labels and plant/bacterial assembly conflation. The current inspection/helper is not that installed endpoint decoder.

This permits designing a modest known-mutant **two-endpoint continuous-error or parent-contrast assessment**, with the complete nine-mutant denominator, shared-parent/site dependence and already exposed outcomes disclosed. It provides a finite opportunity to test inexpensive candidate-sensitive feedback or reject unsupported contrast claims. T391 C/I/V is a useful same-locus discrimination opportunity, with only three related outcomes. Thresholds, comparator allowances and useful-delivery criteria must still be frozen before a successor execution. Rejecting every case cannot win, and no fresh or general predictive accuracy follows from software withholding.

It does not establish maize-level turnover and Galdieria-level specificity in one candidate, high-specificity red-parent transport, a productive-step supplier or consequential EL superiority. Strong conventional ML-directed evolution is demonstrated prior art here. The new panel can revise Phase 2's next task; it does not complete that phase or authorize nomination by analogy.

The separate reproducible helper is `inspect_native_release.py --root <explicit followup-plant4 directory>`, run with the selected locked environment using `uv run --no-sync`. It performs bounded native decoding, raw/cache checks and DNA translation only. Original publication assets and previous 56/14/21-record registers remain unchanged.
