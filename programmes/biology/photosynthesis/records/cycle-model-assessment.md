# Productive-cycle supplier assessment

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026, Australia/Sydney**; selected acquisitions **9 October 2026, 13:24 UTC**. The cutoff is the two named primary sources, **Witzel 2010** and **Cummins 2019**, their displayed equations/tables and explicitly identified references used to distinguish productive catalysis from inhibitor recovery. No broad literature search, engineered candidate assumption or new predictor is introduced.

**Neither source supplies a measured productive product-release waiting-time fraction for G. partita.** More precisely, Witzel's Galdieria parameter column concerns **G. sulfuraria**, and its final catalytic step combines cleavage and release. Cummins separates microscopic steps algebraically but does not identify their values for this exact enzyme. The available evidence supports a source-role falsifier and conditional calculations; it cannot assess an exact G. partita mutation response.

## Source scope and custody

Witzel's authentic publisher body was readable in the browser. Direct bounded HTML/PDF requests returned **403**; no primary Witzel bytes are admitted. Its displayed numerical cells have an explicitly labeled **browser transcription**, with image-only mathematical symbols unresolved. The supplementary file link was not retrievable in the browser; no supplementary equation or parameter bytes are asserted. [Witzel primary article](https://febs.onlinelibrary.wiley.com/doi/10.1111/j.1742-4658.2009.07541.x).

Cummins' existing **147,570-byte primary HTML**, SHA-256 `5b5c6b6303f53a661daac6512a9b0d82b7d8320c60b74e1e4da0513782f6d8f7`, remains unchanged. This follow-up retains the author's institutional **1,483,731-byte PDF**, SHA-256 `596cbff53bbab4bddd54eddaa5012aa8ffe88e6bb0f0d35a387a88fba973ab77`, plus native MathML and text inspections. These are exposed source inspections, not canonical scientific products. [Cummins primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6884029/), [ANU original PDF](https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/ce275da1-e4a9-4f9d-bd15-83e27ec7ff70/content).

Selected outputs belong to `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-cycle3`. Its separate `source-register-cycle3.json` binds the artifacts, source roles, failed requests and preserved predecessor checks. The original **56**, supplier follow-up **14** and reference audit **21** artifact bindings and their registers/reports remain unchanged. Witzel is labeled free access, without an established unrestricted reuse license; Cummins states CC BY.

## Complete displayed model-table census

The main Witzel article has **two numerical tables**. Table 1 has **six species columns**, **five source endpoint rows** and **five calculated parameter rows**: **60 numerical cells**. Its full browser-transcribed cells and footnote markers remain in the separate inspection.

| Table 1 species/context | Source Vmax per active site, s⁻¹ | Source Ω specificity | Role |
|---|---:|---:|---|
| Tobacco | 3.4 ± 0.1 | 82 ± 2 | Compiled WT endpoint context |
| **Galdieria sulfuraria** | **1.2 ± 0.1** | **166 ± 6** | Compiled WT endpoint context; **not G. partita** |
| Phaeodactylum tricornutum | 3.4 ± 0.1 | 113 ± 1 | Compiled WT endpoint context |
| Griffithsia monilis | 2.6 ± 0.1 | 167 ± 3 | Compiled WT endpoint context |
| Synechococcus | 13.9 ± 0.1 | 43 ± 1 | Compiled endpoint context |
| Rhodospirillum rubrum | 4.2 ± 0.1 | 12 ± 2 | Compiled endpoint context |

Table 1 also contains Km(RuBP), Km(CO₂) and Km(O₂), followed by reconstructed kcat, koxy, RuBP association and the gas-related parameters γ/ω. Its footnotes identify an **estimated** Griffithsia Km(O₂), and **approximately 10% author-assigned errors** where particular original sources reported none. These are not six exact jointly replicated panels. Table 2 contains **16 parameter values** for the **WT tobacco simple model**. Fast rates are reconstructed; inhibitor-related combinations and free rates use tobacco fallover evidence/manual fitting. [Native table sections and fitting discussion](https://febs.onlinelibrary.wiley.com/doi/10.1111/j.1742-4658.2009.07541.x).

The supplementary listing names **Docs S1–S4 and Tables S1–S4**. Their declared scopes are simple-model equations, quasi-steady derivation, extended-model equations, summation derivation, fallover sensitivities, and extended **WT/Val335 tobacco** parameters/sensitivities. This is a complete **listing census**, not a decoded supplementary parameter census. The browser calls Doc S3 “simple model” in the listing while the main text assigns it to the extended model; that discrepancy remains explicit. Other species discussed qualitatively do not supply an additional G. partita parameter panel.

Cummins 2019 supplies **one three-panel regression figure** and **four numbered display equations**. The retained HTML's four tables are **equation-layout tables**, not four biochemical datasets. Figure 1 concerns broader **higher-plant WT** compilations. Neither the figure nor the equations supplies a G. partita productive-state time course or a mutant-release contrast. [Primary figure and equations](https://pmc.ncbi.nlm.nih.gov/articles/PMC6884029/).

## Rate-role mapping

| Source object | Scientific role | What it does not identify |
|---|---|---|
| Witzel vER, simple model | Combined RuBP association/enolization | Separately measured productive enolization time |
| Witzel vcat/voxy | **Combined cleavage and product release** after the gas branch | An isolated PGA/phosphoglycolate release rate |
| Witzel G. sulfuraria calculated kcat **1.1…1.3 s⁻¹** | Range reconstructed from source Vmax **1.2 ± 0.1** | A microscopic release barrier or waiting-time fraction |
| Witzel G. sulfuraria koxy **0.49…1.30 s⁻¹** | Calculated oxygenation turnover from macroparameters | An independently measured oxygen-product release step |
| Witzel slow inhibitor/fallover rates | XuBP/PDBP formation, return and release in a deactivation model | Time allocation among normal productive-cycle steps |
| Witzel fallover **f** | Fractional loss of catalytic activity | H3's productive-cycle waiting-time fraction |
| Witzel γ/ω, units **μM⁻¹** | Gas-related parameter combinations | Cummins' dimensionless γ, or a time fraction |
| Cummins k₃/k₇/k₈/k₉ | Enolization / product formation / reverse product formation / product release | Species-specific measured values from the presented regressions |
| Cummins **p** | Reaction commitment probability | A measured product-release waiting-time fraction |

This mapping prevents fitted macroscopic catalysis, slow inhibition or similarly named parameters from silently becoming the missing microscopic operand.

## Authentic Cummins equations and their limits

Native equation 1 is:

```text
γC = k3(k8 + k9) / {k7(k3 + k9) + k3(k8 + k9)}
```

It contains product release **k₉**, but its value is not measured in the paper. Equation 2 uses the explicitly imposed **γC = γO = 1** simplification:

```text
Km = (kcatᵐ + k−m) / (KR · k+m)
```

Equation 3 is **p = kcatᵐ/(kcatᵐ + k−m)**; equation 4 relates isotope discrimination to p and intrinsic isotope effects. These cannot be interpreted as direct single-enzyme rate determinations. The authors interpret their regression coefficients as population expectations, acknowledge inadequate non-plant coverage, and argue that productive release has not been established as limiting. Their preferred hydration/cleavage limitation is an interpretation, not a measured universal restriction or a G. partita bottleneck result. [Primary rate-constant interpretation and regression sections](https://pmc.ncbi.nlm.nih.gov/articles/PMC6884029/).

The native γ expression also shows why setting γ = 1 cannot establish a release fraction: multiple microscopic-rate configurations enter it, including reverse chemistry. The fallover f, commitment p and γ corrections have different meanings. A steady-state fit cannot rename one as another.

## What calculation or falsifier is possible now

**A decisive source-admission falsifier is available.** A supplier that names the Witzel **166** column as **G. partita 238**, calls its reconstructed kcat a separately observed product-release rate, or uses tobacco fallover f as productive waiting time fails the source, state and quantity joins. This rejection concerns the supplied evidence claim; it does not prove the biological objective impossible.

**The specificity condition also rejects a narrow proposed route.** If an intervention leaves the illustrated G. sulfuraria specificity exactly unchanged, it remains **166**, below the illustrative G. partita **238** view regardless of turnover gain. The point ratio **238/166 = 119/83 ≈ 1.4337** requires approximately **43.4%** additional specificity in that comparison. This is conditional arithmetic without propagated uncertainty or universal threshold status. It neither transfers G. sulfuraria kinetics to G. partita nor asserts that no intervention can improve both endpoints.

**Ordinary model reconstruction remains possible.** Source macroparameter relations or the already recorded serial-cycle feasibility bound can be checked conditionally. Their outputs would remain inferred/conditional values. These papers do not supply an independent G. partita step observation against which to assess a proposed productive-release split.

For example, under an explicitly hypothetical irreversible two-step serial cycle, a known turnover q gives **1/q = 1/a + 1/r**. For every **0 < f < 1**, choosing symbolic **a = q/(1 − f)** and **r = q/f** satisfies the same turnover while giving release waiting-time fraction f. This is an identifiability illustration, not an assigned biological rate or a reconstruction of either source's complete topology. Adding specificity without a calibrated shared topology does not select f from this family. Reversible chemistry requires its own separately assessed relation.

The existing [H3 feasibility calculation](productive-cycle-question-v1.md#source-conditioned-turnover-feasibility-bound) states an actual discriminating inequality once independent bounds on release fraction and edit acceleration exist. **Neither bound is supplied here**, so the inequality cannot now reject or nominate a real G. partita edit. A static inhibitor-bound geometry, equilibrium inhibition constant or a manually fitted release parameter would not repair this missing assessment.

## Stop and next-entry condition

Retain H3 as **missing a calibrated productive-step supplier**, with these exact source-role corrections. Do not implement an edit-to-kinetics predictor from an invented cleavage/release split or begin molecular sampling merely to populate that split. Entry requires an exact assay-linked parent/edit and a state-sensitive observation or independently assessed reaction calculation that constrains the productive step, with compatible two-endpoint assessment. A narrower supported successor question remains permissible.

This bounded review has finished at the named sources. It establishes neither a measured limiting-release fraction, a universal exclusion of productive release, a strong candidate nor EL advantage. The source check, model reconstruction and identifiability reasoning are available to competent conventional approaches under the same opportunities.
