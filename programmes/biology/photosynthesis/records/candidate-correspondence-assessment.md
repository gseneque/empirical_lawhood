# Candidate edit correspondence assessment

SPDX-License-Identifier: CC-BY-4.0

The 10 October 2026 checks resolve which published edits would actually change the inspected G. partita sequence. They provide source correspondence and a hypothesis site, not mutation-response predictions or a strong nomination. Sequence availability, structural correspondence and phenotype transport require separate evidence.

| Proposed transfer | Exact inspected correspondence | Disposition |
|---|---|---|
| Tobacco LSU V369A | G. partita LSU linear position 377=A; 1BWV author position 369=ALA | Already present; the literal replacement makes no edit. |
| Tobacco LSU T391I | G. partita LSU linear position 399=I; 1BWV author position 391=ILE | Already present; the literal replacement makes no edit. |
| Te SSU V98M | Sequence-only correspondence ambiguous; backbone evidence supports G. partita SSU linear position 95=I, 1BWV author position 112=ILE | An analogous Met substitution would be **I95M**, a testable site hypothesis whose kinetic effect remains unknown. |
| Literal G. partita SSU F98M | F98 lies approximately 10.5 Å from transformed Te V98 in the well-fitting backbone comparisons | Unsupported as the homologous-site transfer; shared literal numbering is insufficient. |

The tobacco checks use native S8-derived parent DNA/protein, P00876 and the original G. partita O98949/1BWV sequence. All optimal paths under four declared global affine scoring variants agree on the two LSU sites. The [plant-release assessment](plant-release-assessment.md) records that independent check and the exact A369 bacterial versus V369 plant-fusion backgrounds.

The SSU check independently verifies the original Te MG000148.1 construct against 3ZXW and G. partita AB018008.1 against O98950/1BWV. All-optimal sequence alignments permit 93SER or 95ILE under three scoring variants; a fourth also permits 94THR, 96ILE or a gap. The same ambiguity remains for both native Galdieria Met/Val initiation views. Literal Galdieria 98PHE is outside those sequence correspondences.

Backbone comparisons use a proper-rotation Cα Kabsch fit, excluding the queried Te 90..106 segment from all fitting anchors. They retain every one of sixteen deposited chain pairs under four scoring seeds. Three untrimmed seeds give near 0.9 Å anchor RMSD and place Te V98 nearest Galdieria I95 at 0.820–0.842 Å. The fourth untrimmed seed gives near 6.8 Å RMSD and nearest 94THR; that adverse fit remains retained. The separately declared iterative 4 Å trimming rule gives near 0.9 Å RMSD and nearest 95ILE in all 64 chain/seed fits, at 0.820–0.856 Å. These are correlated views of two deposited structures, not 64 independent biological observations. Fit/trimming choices and site selection are post hoc source diagnostics, not a prospective kinetic assessment.

The selected derivative is `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-plant4/te-galdieria-ssu-correspondence-inspection.json`: **586,663 bytes**, SHA-256 `94bb8cd0cb2d5b7c7e356eff70a973f1f8b302dc422418bbc8675e1285eada8b`. Its nine dependency bindings cover original sequence/structure records, native parser/decoder and helpers. All nine were independently checked by byte count and SHA-256. The standalone helper `/tmp/rubisco-te-galdieria-ssu-correspondence-v1.py` has 16,825 bytes, SHA-256 `31ff87e9f1dc1b91b5557020f7f8307fa94347720f51da25f3100d476af3d28d`. The preceding plant/reference registers remain unchanged.

The [native Wilson panel](source-panels-report.md) reports SSU V98M in the **Te LSU P415A** combination, giving turnover 9.5 and specificity 56.3, versus Te-P415A 6.9/52.6. It does not contain an isolated V98M mutant on native Te WT from which to identify that independent edit effect. Galdieria already contains alanine at the corresponding LSU site, but neither that residue nor backbone proximity makes its complete background equivalent to Te-P415A. The original source's endpoint errors, preparation limits and complete nineteen-enzyme roster remain preserved.

I95M therefore remains an exact **site hypothesis**, with the [reference audit](reference-pair-audit.md)'s initiation/preparation uncertainties retained. No red-parent rate effect, specificity-preservation margin, maize-level turnover, productive-step mechanism, mutant DNA deposit or EL advantage follows. An applicable supplier would need to resolve a useful kinetic decision about this edit and its exact assembly; structural correspondence alone cannot supply that response. This finding advances source interpretation toward Phase 2, while Phases 6–9 remain open.
