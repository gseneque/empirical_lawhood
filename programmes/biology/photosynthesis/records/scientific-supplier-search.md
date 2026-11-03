# Targeted red-algal kinetic supplier search

SPDX-License-Identifier: CC-BY-4.0

**Availability:** `inspect_supplier_followup1.py` and its complete local input packet are not distributed.
The script references below describe historical inspection, not a runnable checkout procedure.
See the [historical-procedure index](progress.md#availability-of-historical-procedures).

Reviewed 9 October 2026. This follow-up asks whether public primary evidence supplies an exact high-specificity red-algal edit that accelerates productive turnover while retaining CO₂/O₂ discrimination, or a calibrated mechanism capable of predicting that edit. It does **not** find such a supplier within the reviewed corpus. This is a finite evidence result: it neither proves the objective impossible nor establishes an EL capability advantage.

The [first input report](scientific-inputs-report.md) and its 56-record register remain unchanged. New originals and native inspections are selected separately at `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-1`; `source-register-followup1.json` records hashes, terms, rejected responses and browser-only reviews. These sources are already exposed historical evidence.

## Scope and evidence found

The targeted queries combine Galdieria partita/sulfuraria, Cyanidioschyzon merolae, Porphyridium, Rubisco, mutagenesis, specificity, turnover, small subunit, latch, loop 6, gating and product release. Follow-ups inspect the primary references behind structural, assembly and kinetic-cycle claims. Search also covered recent red-algal engineering reports through the review date. An unsuccessful query is not evidence that no relevant experiment exists. A paywalled full chapter, inaccessible supplement or unresolved sequence remains a missing input.

| Primary evidence | Actual measured or computed object | Consequence for this supplier |
|---|---|---|
| Ninomiya 2007/2008 latch introduction | Green-type Synechococcus PCC7002 receiving a red-like latch; relative kinetic changes | Specificity increases while turnover decreases; no exact engineered high-specificity red parent |
| Joshi 2015 small-subunit interventions | Rs small-subunit substitutions, truncation, folding/assembly yield and thermal stability; heterologous Galdieria SSU | Assembly and activity can separate; a successful structural assembly is insufficient |
| Pearce 2006 G. sulfuraria | Inhibitor release/recovery | Not productive PGA release |
| Watanabe 2007 fragment molecular orbitals | Static inter-fragment interactions in plant and Galdieria structures | An energetic structural comparison, without edit-to-barrier-to-joint-kinetics calibration |
| Witzel 2010 and Cummins 2019 kinetic mechanisms | Explicit mathematical cycles, fitted/derived rates and kinetic interpretations | Reusable conventional mechanisms; unresolved microscopic rates cannot be assigned arbitrarily |

The natural high-specificity Galdieria/Cyanidium/Porphyridium measurements and the lower-specificity Te and Rs engineering panels remain useful separate contexts. The search did not locate a public, exact engineered Galdieria, C. merolae or Porphyridium panel with both intrinsic endpoints and enough state-resolved data to calibrate the requested two- to threefold speed gain. It would be unsound to transport a lower-specificity graft solely because both enzymes are red-type.

## Exact interventions and assay limits

The accessible primary 2008 latch abstract reports **16% greater specificity, 41% lower Vmax(CO₂), and 55% improvement in Km(CO₂)** after introducing the red-like latch into Synechococcus PCC7002. Both proteins were expressed in E. coli and purified. It describes the Val332–Gln386 interaction and green-type His at the corresponding position, but the accessible abstract does not print the complete edit set, deposited construct, absolute endpoint values, uncertainties or assay conditions. Thus the intended His-to-Gln intervention is a structural lead, not a sequence-bound candidate or a supported reverse intervention in Galdieria. [Primary 2008 abstract](https://link.springer.com/chapter/10.1007/978-1-4020-6709-9_192), [primary 2007 abstract](https://www.jstage.jst.go.jp/article/jspp/2007/0/2007_0_217/_article/-char/en).

Joshi's exact **Rs SSU** changes are D40A, R44A, E106A, R113A, E115A, R119A, Y123A and ΔEF, the latter retaining residues 1–106. Point mutants recover WT-level reconstitution activity despite differing native-PAGE stability; ΔEF reduces yield by approximately 30% and slows **assembly** approximately 3.5-fold. These are not intrinsic kcat changes. Table 1 has nine thermal-stability rows including WT, with SD from at least three independent experiments. Rs LSU plus G. sulfuraria or Phaeodactylum SSU forms L₈S₈ yet has negligible activity. Refolding is at 25 °C, pH 7.5 with GroEL/ES; activity is relative to recombinant native control. No specificity panel is supplied. Full deposited mutant DNA was not acquired. [Primary methods and figures](https://pmc.ncbi.nlm.nih.gov/articles/PMC4294474/).

Pearce uses **native G. sulfuraria UTEX 2393**. Table 3 reports Vmax **1.2 ± 0.1 s⁻¹**, with specificity **166** from earlier work. Native kobs tokens are **0.13 ± 0.01 × 10⁻³ s⁻¹** for RuBP, **0.07 ± 0.03 × 10⁻³** for XuBP and **0.8 ± 0.1 × 10⁻³** for CA1P. These concern decarbamylated complexes or carbamylated inhibitor release, **not PGA release**. RuBP uses radioactive exchange; XuBP/CA1P use activity recovery. Carboxylation uses 25 °C, pH 8.0, 5 mM bicarbonate and 500 μM RuBP; decarbamylation uses overnight nitrogen-sparged dialysis at 4 °C. Fitted errors are SEM, without identified biological preparations. All species, footnotes and native cells are retained. [Primary source](https://pmc.ncbi.nlm.nih.gov/articles/PMC1615894/).

Watanabe's K18I, H386Q and M472T comparisons are **plant-relative structural substitutions**, not an assayed engineered-red panel. The fragment molecular orbital calculation associates H386Q with loop stability, whereas M472T does not explain it. Inter-fragment interaction energy is neither an activation free energy nor a mutation response for turnover/specificity. The retained 1BWV inspection already resolves author Gln386 to source-sequence position 394; a literal position-386 edit would be unsafe. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/17651697/).

## What can actually be supplied locally

Pearce permits a state-specific **inhibitor-release/activation-recovery** relation, useful for testing erroneous population/rate substitutions. It cannot nominate an intrinsically faster mutant. In general, better assembly or activation may increase active enzyme abundance without increasing turnover per active site.

Witzel's published mechanism supplies ordinary kinetic-cycle mathematics. Its Galdieria constants include measured steady-state values and derived ranges; oxygenation and elementary binding parameters must retain their inferred status. Slow-process fitting principally uses tobacco time courses and manually fitted free parameters. Different source views, including RuBP affinity, must remain separate. A local implementation could reproduce these conditional models, but could not convert the fitted WT parameters into an exact red-mutant response. Direct file retrieval failed; the primary article was reviewed in the browser and is not byte-admitted in this follow-up. [Primary mathematical model](https://febs.onlinelibrary.wiley.com/doi/10.1111/j.1742-4658.2009.07541.x).

Cummins distinguishes enolization k₃, hydration/cleavage k₇ and product release k₉. The authors argue that existing evidence does not establish product release as the limiting step, and discuss hydration/cleavage or enolization co-limitation. They also state that their kinetic regressions do not determine rate constants for an individual Rubisco. This is a published interpretation with disputed reaction commitments, rather than a universal impossibility theorem. Population regressions and steady-state endpoints therefore do not supply the missing red-mutant microscopic rates. [Primary response and kinetic equations](https://pmc.ncbi.nlm.nih.gov/articles/PMC6884029/).

A constructive next supplier question is: **which exact perturbation changes which independently observable productive-cycle step, with a supported mapping to both intrinsic endpoints?** A useful answer needs the exact paired LSU/SSU parent and mutation, active-site normalization, chemical/activation state, competing CO₂/O₂ branches, and a state-sensitive observable constraining the perturbed step. Candidate measurements could include transient product formation or independently assessed reaction-state barriers; their validity for the chosen enzyme must be established. Inhibitor-bound coordinates, fold stability, gas arrival or unconstrained MD populations do not answer that question alone.

Under the explicitly hypothetical serial-cycle model where a removable step occupies fraction f of cycle time and leaves all other steps unchanged, removing it has maximum acceleration 1/(1−f). A twofold gain would require f ≥ 1/2; a threefold gain f ≥ 2/3. No reviewed source measures that fraction for productive red-algal turnover, and this accounting model does not establish preservation of specificity. It identifies a missing operand rather than filling one. Any more realistic model must propagate reaction reversibility and commitment into both endpoint expressions.

## Conventional comparison and current decision

Conventional enzyme engineering already includes red-loop grafts, paired-subunit models, reaction-cycle repair, quantum calculations, iterative experimental feedback and adaptive selection of missing measurements. The measured lower-specificity Te joint gain remains a useful retrospective calibration direction, not a high-specificity transport result. The same inputs and calculation/acquisition budget must be available to competent adaptive comparators. Preventing the quantity-role mistakes above is an available conventional solution.

The present feedback therefore returns **unresolved productive-cycle support**, not an exact nomination. Continue if a newly admitted source or calibrated physical relation supplies the missing edit/state-to-both-endpoints operand. Preserve unsupported extrapolation and missing outcomes in the denominator. If conventional adaptive methods construct the same relation, record that result; recursive depth alone does not establish EL superiority. Neither a strong challenge candidate nor an EL advantage has been demonstrated by this finite search.

## Custody and reuse

The helper `/tmp/empirical-lawhood-rubisco-20261009/inspect_supplier_followup1.py` reads the actual retained HTML under a 1 MB cap. It reuses the native table parser, retains all tables with source IDs, original cell text/attributes and selected assay paragraphs, and records original byte hashes. No HTML/workbook code or molecular simulation was executed.

The follow-up retains six downloaded payloads: four verified article/abstract bodies and two rejected HTML responses. The 5,590-byte PubMed response and 3,038-byte Springer response do not contain the required primary body/abstract. Primary browser reviews remain separately labeled. Joshi records ASBMB copyright, Pearce Biochemical Society copyright, and Ninomiya Japanese Society of Plant Physiologists copyright; unrestricted redistribution terms were not verified for these assets. Cummins records CC BY. Official S3 metadata was unavailable for the two older articles. No new evidence exposure, laboratory work, paid access, external publication or submission was authorized by this acquisition.
