# Retained Rubisco source panels

SPDX-License-Identifier: CC-BY-4.0

**Availability:** this report describes an external historical source packet.
Its `raw/final-normalizer.py`, `raw/finalize_source_panels.py` and `raw/producing-package-source.zip` are not distributed in this release.
The command below requires that exact packet, its original inputs and producing environment.
It is not a runnable checkout example or part of the separate [partial preservation ZIP](redirection-preservation-v1.md).
See the [historical-procedure index](progress.md#availability-of-historical-procedures) for availability limits.

The source normalization completed on 2026-10-09. Thirty-eight artifacts were published and independently replayed through the actual `ExternalArtifactPlane`, its `LocalFilesystemInspector`, canonical manifests and publication commit markers. These include nine unchanged original files, eighteen typed canonical products, producing provenance, a complete package-source snapshot and the operational helpers. Every canonical product was decoded again and checked against its exact retained bytes.

The explicitly selected output is `/tmp/empirical-lawhood-rubisco-20261009/retained-execution/source-panels-v1`. Its `publication-index.json` records every artifact path, byte count, physical SHA-256, logical fingerprint, publication commit, original locator, native census and scientific admission disposition. Its SHA-256 is `6ac935143156c8104e2452c02fee05c76a1fd83d6f21951867bef1b567aeceef`.

This is exposed local source custody with `DEVELOPMENT_ONLY` visibility and `DEVELOPMENT_VISIBLE` access. It is not the external scientific root required by the [operator guide](../../../foundations/measurement-and-response/workflows/reactor-response/operation.md), a source acquisition event, a scientific execution receipt or qualification. No source was reacquired; no scientific/native task was executed; no task receipts, signers or grants were generated. The generic raw-byte custody schema authenticates uninterpreted bytes and creates no acquisition authority. The local `/tmp` location also needs preservation before operating-system cleanup.

| Source | Complete retained denominator | Scientific operands and remaining limits |
|---|---|---|
| RR2018 original XML and supplement PDF | Nine native table rows; three included, two multiple-substitution exclusions, four ancestral-parent exclusions; six role slices | The actual supplement bytes match the retained SHA-256, so this successor audit has `supplement_bytes_verified=true`. Verification does not resolve biological replication, endpoint pairing or joint uncertainty. The earlier historical execution with verification false remains unchanged. |
| de Pins crosswalk | All 1,454 rows and 30 columns; 413 native joint-complete rows, 405 with the native primary flag | 404 rows remain jointly available after quantity-role admission. All nine corrected Davidi `S_val` tokens are carboxylation efficiencies, not specificity. Seven specificity quantities are rejected for that role conflict; eight quantities across the additional two mixed-enzyme rows require identity reconciliation. Raw tokens remain present. The native primary flag does not establish qualification or independence. |
| Flamholz Dataset S1 | All 634 rows and 28 columns; 245 native joint-complete rows, 199 marked primary | Missing values, native errors, conditions and citations remain separate. The compiled Wilson row labeled `P451A` remains its original token; the primary Wilson construct is separately verified as `P415A`. Complete constructs, independent biological units and cross-study pooling are not established. |
| McDonald2025 S3 | Eight enzyme rows, including WT and seven mutants; seven joint-complete rows | TM specificity remains `nm`. Native cached values, formulas, all listed raw observations and reported group Ns are retained. R337C turnover has three raw values, but cached SD and SEM conflict with those listed values/counts. Ko's source SEM versus summary SD header conflict remains explicit. Calculated gas-response sheets are inventoried as archive members rather than admitted as additional measured kinetics. |
| Davidi2020 EV1 and Tsai2025 primary Table 1 | Nine original enzyme rows, nine corrections and all eleven native correction table rows including both header levels | Exact reviewed source-name aliases join enzyme identifiers rather than table positions. Original turnover, corrected historical turnover and newly remeasured turnover remain three distinct source views. Historical specificity is not newly measured by the correction. Native sequence matches do not establish complete assay constructs. |
| Wilson2017 primary Table 1 and MG000148.1 | All nineteen enzymes: fifteen Te and four Se; all twenty-seven native table rows and their dispositions | Exact mean ± SE tokens and endpoint-specific column-level biological/technical counts remain retained. The deposited insert has 1,850 bases, LSU 475 aa and SSU 118 aa; translation and all fifteen derived Te protein recipes were verified. LSU415=P, LSU451=W and SSU98=V establish `P415A`/`V98M`. Se numbering is not borrowed from Te. Mutant DNA, assay pairing and biological readiness remain unestablished. |

The canonical products are in `canonical/`. Principal fingerprints are listed below; the machine index also includes both native workbooks, the Wilson native table, the parent construct and all six RR role slices.

| Canonical product | SHA-256 / canonical fingerprint |
|---|---|
| `rr2018-audit.json` | `5ffffc6412fd1db546a4b594f89d9cfec446a36a9642acc72ce82485b9f26598` |
| `crosswalk.json` | `1c0fe634667cfd1afcfceb491a0ee6e3eabc308b9a9ab597f7bb4031c9307249` |
| `flamholz.json` | `b0b204df17bdca33ec0faab02bc3eb73c01006c8c0e8807711849ddbca3abd6b` |
| `mcdonald2025-panel.json` | `5008171e53f5e46a5f16418854fbf301354ec981027ccf532e2c625741e8de82` |
| `davidi2020-original-panel.json` | `c881b808069ae536fe0eb3cfa9dd29ef79968f11fc5e9086a62e760ff5806052` |
| `tsai2025-correction.json` | `a80455b4f4c2759ea6b3af86b58aae419903260ec7c3af7bb473748968b1f243` |
| `davidi2020-corrected-panel.json` | `0494ded9118541d67c2c2251e84d15d61638141cd6be0e704aed1e6d9762a93b` |
| `te-MG000148-parent.json` | `72cb283eca1859d289e34163df77651d644bf33936832d1896a55172243f4b8b` |
| `wilson2017-panel.json` | `097f682b0df3f1f34754df28aafaa55278650e329b6b9021a45b605feaea9db2` |

The producing record observed Git HEAD `9c670a3127cb652f839e56463758226749b07c73` with an unclean checkout. It binds the actual loaded package inventory rather than attributing modified files to that clean commit. Package source digest: `5b26a7fe2b958a5ded5200b00a1a5dbb9d9d72a485efd2499ed60c5ced7fe2f4`; selected `uv.lock`: `027373fcea689b57f65c781a4c4976a046b3b3301e9ec7c7dfa0588510c871dd`; producing provenance fingerprint: `c4260675acefb78ed06b240fbf1d9d8ac6ea0c72410853ba6bb9585a620454c9`.

The immutable `raw/producing-package-source.zip` contains all 2,339 producing package source/resource members plus `uv.lock`. Its 11,522,516 bytes have SHA-256 `38049ce27a91ba970c7d04d406f1df563d63737ceba67a2d8ffd948647c26413`. Every archived member was read back and matched to the original producing inventory. The `source-snapshot-index.json` gives its complete member paths, sizes and hashes. Later source changes do not alter this snapshot.

The independently checked native Wilson cells/protein recipes and Tsai cells/attributes also agree with separately produced source inspections. Those inspection JSON files were comparison aids; canonical measurements came from original XML/CSV/XLSX/HTML/GenBank bytes. The adapters' focused source tests passed 63/63 and Ruff passed in the already selected locked environment. No environment synchronization was performed.

The historical packet used this command to authenticate its retained publication without a new producing environment:

```sh
UV_CACHE_DIR=/tmp/rubisco-uv-cache uv run --no-sync python \
  /tmp/empirical-lawhood-rubisco-20261009/retained-execution/source-panels-v1/raw/final-normalizer.py \
  --project-root /home/chevre/gs-ml/empirical_lawhood \
  --output /tmp/empirical-lawhood-rubisco-20261009/retained-execution/source-panels-v1 \
  --verify-only
```

The actual replay returned `VERIFIED_SOURCE_CUSTODY`, 38 artifacts, zero reacquisitions and zero native executions, with the exact index hash above. `raw/final-normalizer.py` contains the corrected fresh-destination normalization recipe; `raw/finalize_source_panels.py` records completion of the existing source/product batches and code archival. A fresh reproduction must explicitly select input paths and a new destination, and preserve the producing environment and archived code if identical producing provenance is required.

The first normalization helper attempts stopped on diagnostic serialization, a selection schema mismatch, an uppercase artifact identifier and a noncanonical Python list. The first two stopped before any publication; later stops preserved their already committed source/product batches. Finalizer development also refused a missing explicit decoder bound, a mistaken commit-marker lookup and an attempted manifest-as-measurement decode. These were orchestration defects corrected outside the source package. All original source bytes, committed helpers, canonical products and successful publication identities were preserved; this history supplies no scientific execution receipts. Source admission limits and negative or missing outcomes remain part of the retained scientific denominator.
