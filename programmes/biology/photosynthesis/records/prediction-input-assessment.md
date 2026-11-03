# Published prediction operands and inexpensive precursor

SPDX-License-Identifier: CC-BY-4.0

**Availability:** `inspect_plant_features.py`, its local inspection results and complete input packet are not distributed.
The reproducibility description records original custody; this release supplies no public replay package for that command.
See the [historical-procedure index](progress.md#availability-of-historical-procedures).

This successor records the newly acquired published prediction inputs and their
actual suitability for the plant-mutant assessment. Earlier source audits and
registers retain their original bytes. This is an acquisition and source-admission
assessment; it reports no fitted model, newly validated enzyme or EL result.

## Original inputs and reproducibility

Selected inputs are `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-prediction5`.
The separate `source-register-prediction5.json` binds retained retrieval attempts,
original files, offline inspection scripts and complete archive inventories.
The acquisition log retains nineteen attempts, sixteen returned payloads and
three failures, including two direct Colab 404s and the publisher HTML 403.
Returned Colab HTML is retained as an interface response, without treating it as
a fitted notebook or checkpoint. No downloaded code, model weights, pickle or
object-array payload was executed.

| Original | Bytes | SHA-256 |
|---|---:|---|
| [Iqbal primary XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9833099/fullTextXML) | 177,420 | `77c7bb857c26132820123d70ad356deb36124b162300f124784df6eddadbdd0f` |
| [Exact repository training workbook](https://github.com/Iqbalwasim01/Mining-Rubisco-kinetics/blob/a6244b717679f7f6998a5ee7893402374b5182e1/Tabel%20S2.%20Kinetics%20and%20sequence%20data%20used%20for%20model%20training.xlsx) | 35,582 | `bbd449d86c96297acf6351cf184464ceb23cbc1f42535beff4fce8b0dcd7bbc0` |
| [Iqbal complete supplementary collection](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9833099/supplementaryFiles) | 3,872,136 | `c3083d7d933d42af0631166d1394a00107376f358ca4ad358f4e5f3970749307` |
| [Young published primary XML](https://doi.org/10.3390/aichem1020007) | 157,596 | `d5c3f1c7d9181cc05af3516b95bf627572be56895cd6cd7fbd41d1418e7b7522` |
| [Young version 3 deposition](https://zenodo.org/records/19546367) | 11,142,269 | `77e277116975a59edc1517fba84cd82177a6c480cbafd41123ac6d46028f83a7` |

The Iqbal supplement ZIP contains eleven native members, including the genuine
supplement PDF; it contains no training XLSX. The separate acquired repository
workbook retains its native `Tabel S2` name and is not relabelled as a journal
supplement member. The primary publication supplies CC BY 4.0 attribution.
Portable software fixtures retain the exact article and workbook bytes with
licence/source metadata, without qualification claims.

The inspected Iqbal repository at `a6244b717679f7f6998a5ee7893402374b5182e1`
has five regular files: data and README, with no Python/notebook code, fitted
state or embedding arrays. The paper specifies GPflow 2.1, aligned classical
one-hot and ESM-1b features, additive/full kernels, and a Levenshtein KNN
comparator. The acquired material does not settle all GP preprocessing,
likelihood, optimization and fitted-state choices. Reimplementing a declared
model is possible; reproducing its best reported ESM GP requires additional
operands and choices.

The Young version 3 ZIP has **231 members, 204 regular files**, 51,669,989 bytes
expanded, 34 Python files, 53 CSV files and four XLSX files. Complete inventory
finds no `.npy`, `.npz`, `.pkl`, `.pt` or `.pth` assets. The inspected current
GitHub tree at `ade87f378aa25c24a24c19915722aa04be92936e` likewise contains no
such arrays. Its README describes small included embeddings, but the retained
inventories do not substantiate their inclusion. Existing outputs are useful
prior art, without supplying exact A369-parent/query embeddings or an assessed
two-endpoint mutation relation. Code, generated data and third-party terms remain
separate upstream licence roles.

## Exact natural source and assessment scope

The [maintained Iqbal decoder](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/iqbal2023.py)
admits only the reviewed original digests and sealed native workbook projection.
Its canonical table has **1,762,519 bytes**, fingerprint
`28c34d5393aa4b627fc76c56ebbc979ec237fc8ddf3252a618a39f9c9fd41a21`.
It retains all 183 rows, 132 unique LSU sequences, 86 genera and 17 native
citation strings; 165 turnover means, 170 specificity means and 155 joint rows
retain separate missingness. Shorter sequences and correlated duplicate-sequence
associations remain in the denominator.

Tobacco row 112 has the native V369/T391 background, turnover **3.1 ± 0.3** and
specificity **80 ± 2.6** as source mean/converted-SD tokens. Its complete 477-aa
LSU equals the inspected P00876 native-V369 sequence. This is a different
background from the plant assessment's S8-derived A369 bacterial parent. The
source's count assumptions and error conversions cannot establish biological n,
cross-endpoint pairing, calibrated uncertainty or complete holoenzyme composition.
Adjusted aerobic Kc retains its own role, distinct from direct specificity.

The [frozen precursor protocol](plant-prediction-protocol-v1.md) uses a maintained
RapidFuzz implementation of uniform Levenshtein distance and explicitly defined
nearest-neighbour fitting. All natural-only genus-held tuning, complete boundary
ties, parent anchoring and all nine focal mutants plus A369V diagnostic are
selected before execution. Parent/no-change, fixed 1NN and selected KNN are the
three declared methods. Its result must report both endpoints and their mutation
contrasts; source admission or natural-enzyme cross-validation alone cannot show
useful mutant feedback.

## Additional plant feature audit

The retained `inspect_plant_features.py` performs a bounded offline inspection of
the exact original S1 workbook and the released `esm1bv.py` literals. No released
script is executed. Derivative `plant-feature-coverage.json` has 12,868 bytes,
SHA-256 `d586399827ecfdf641dec5efc49fd2c25ec59a1f2acdc3b14496d2615bf5a29b`.
The existing generic decoder correctly refuses the two full DMS XML sheets at
its 1 MiB member limit; this audit uses a separately declared 3 MiB inspection
bound and changes no maintained input contract.

The released ESM-1b/v script's literal LSU and SSU **exactly match the S8-derived
A369 bacterial parent**, unlike the native-V369 structure context. Thus a correct
sequence-background join is available. Nevertheless, none of the nine focal
alleles appears in the deposited ESM recommendation list: **0/9** coverage,
without deposited per-allele numeric 1b/v scores. Recommendation membership
cannot be promoted into an unobserved likelihood.

Native structural score rows cover **9/9** focal alleles in 4RUB and **6/9** in
1RLC; the latter lacks N468D, N468Q and A470R. Those scores preserve their
structural-background roles and are not kinetic labels. A model using them
requires a separate frozen fit/assessment protocol, retaining missing tails and
six held-out site groups. They are not added retrospectively to the current KNN
assessment or used as hidden comparator restrictions.

The precursor may identify a useful component or a clear failure of natural-to-
mutant transfer. Neither outcome closes the consequential EL comparison,
high-specificity transport or nomination gates in phases 2–9.
