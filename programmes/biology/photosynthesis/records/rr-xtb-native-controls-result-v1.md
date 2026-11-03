# First native xTB controls: fixed-position refusal

SPDX-License-Identifier: CC-BY-4.0

**REFUSED, 10 October 2026.** The first frozen synthetic control window entered
16 of 17 assigned xTB commands once. Fifteen controls passed; the optimizer
moved the atom declared fixed, so the final unfixed gradient and all six
enzyme cases remained unentered. This is a native boundary failure, with no
enzyme geometry repair, kinetic result or biological evidence.
Role: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The [frozen v1 protocol](rr-xtb-native-repair-protocol-v1.md), producing helpers
and closed packet remain historical bytes. This note describes that RF
optimizer implementation; a later implementation or model choice cannot
retroactively make this attempt pass. The [source/profile
intake](rr-xtb-source-and-profile.md), [initial coupled geometry
result](rr-coupled-initial-geometry-result-v1.md) and held software encodings
remain separate ancestry.

## Complete control and case census

| Assigned control | Actual status |
|---|---|
| Baseline H2 gradient | PASS |
| H1x, h=0.001 Bohr, minus | PASS |
| H1x, h=0.001 Bohr, plus | PASS |
| H1x, h=0.002 Bohr, minus | PASS |
| H1x, h=0.002 Bohr, plus | PASS |
| H1y, h=0.001 Bohr, minus | PASS |
| H1y, h=0.001 Bohr, plus | PASS |
| H1y, h=0.002 Bohr, minus | PASS |
| H1y, h=0.002 Bohr, plus | PASS |
| H2z, h=0.001 Bohr, minus | PASS |
| H2z, h=0.001 Bohr, plus | PASS |
| H2z, h=0.002 Bohr, minus | PASS |
| H2z, h=0.002 Bohr, plus | PASS |
| Common QM-plus-field translation gradient | PASS |
| Largest D263N/V2 field-capacity gradient | PASS |
| H1-fixed RF optimization | REFUSED: fixed H1 moved |
| Fresh final unfixed gradient | UNENTERED: prerequisite refusal |

| Assigned enzyme case | Actual status |
|---|---|
| Unedited computational reference V2 | UNENTERED |
| Unedited computational reference V3 | UNENTERED |
| Both-LSU D263N V2 | UNENTERED |
| Both-LSU D263N V3 | UNENTERED |
| Both-LSU H287N V2 | UNENTERED |
| Both-LSU H287N V3 | UNENTERED |

All 16 native processes exited normally with code 0. The worker and launcher
exited 1 because the scientific operation contract failed. There was no
retry, alternative optimization, final diagnostic query or enzyme entry.
Registered task receipts, endpoint fits, new authentic source decoders and
new authentic context constructors are all **zero** for this control window.

The retained worker admits **15 single-objective evaluations** and gives a
**37-objective conservative entered upper bound**. Independent inspection
finds eight numbered ANC cycles in the normally terminated optimizer. The
pinned source defines one initial evaluation, one per cycle and one final
driver evaluation: **25 source-inferred native objectives** across this
window, including the ten in the rejected optimizer. This is a source-derived
call census, not 25 printed SCC iteration counts. Suppressed inner SCC
iterations remain unidentified. The final assigned command did not run; the
unused allowance was not filled.

## Actual numerical checks and stop

For the strongest selected component, native H1x analytic gradient was
**0.021274456476641 Eh/Bohr**. Central differences were **0.021274673** and
**0.0212753225 Eh/Bohr** for h=0.001 and 0.002 Bohr: absolute errors
**2.16523359e-7** and **8.66023359e-7**, below its frozen tolerance
**2.1274456476641e-5 Eh/Bohr**. Both steps for H1y and H2z also passed the
declared absolute tolerances; their signals are smaller than that tolerance,
so those passes do not establish the same relative sensitivity as H1x.
The legacy **0.52917726 Å/Bohr** input conversion and associated derivative
chain rule were retained. Exact input displacements were checked separately
from the producer's declared step labels.

The common molecule-plus-field translation gave **zero displayed energy
change** and a maximum gradient-component change of **2e-13 Eh/Bohr**, within
the frozen 1e-8 Eh / 2e-6 Eh/Bohr tolerances. The capacity query used the exact
held **13,754-row scientific / 13,749-row native** D263N/V2 field and omitted
only the five exact zero-charge CA rows. Its output has all **13,749 ordered,
finite PCgrad rows**. Every component displays zero at eight decimal places;
this does not imply exact zero physical field derivatives. The H2 query was
outside the complete scientific field box. This checks ingestion and output
census, not an enzyme Hamiltonian or MM-force accuracy.

The fixed optimizer input H1 was (0,0,0) Bohr. Its declared final native
`xtbopt.coord` places H1 at **(-0.03490786441185,0,0) Bohr**, a displacement of
**0.0184724480419142945310 Å**, exceeding **1e-10 Å**. The printed fixed-atom
selection and a normally terminated optimizer therefore did not satisfy the
required physical position constraint. The retained pure replay independently
returned the same `fixed H1 coordinate moved` refusal. No fresh unmasked final
gradient exists, so neither a free-atom convergence gate nor a final physical
force claim is available.

## Immutable custody and independent review

The closed scientific execution packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-xtb-native-controls-v1`:
**328 files / 19,698,076 bytes / 18 authenticated artifact publications**.
All files are `0444`; directories are `0555`. All members are below 16 MiB,
and the actual combined selected footprint is below 64 MiB. Closed-census
SHA-256:
`a45181c3b890e5dc641e7910cd32a237d26a102c688e3b1660e8d90592f77397`.

Independent read verification authenticated all **18 manifests and 18 commit
markers**, the complete physical census, hashes and modes. Before first
native contact, **13 authenticated publications** retained sources,
implementation and the full 17-control/six-case no-entry roster. The raw
child contact markers remain ordinary observations, not artifact publications.

| Frozen binding | SHA-256 |
|---|---|
| Scientific protocol v1 | `03106fdc3eef9fd9dac9a3ddb080da80e3e433cbb5c54c5ce77586168ed00cf0` |
| Actual execution configuration | `d311b2158202f022312fedb2c0da5ba13a8e0546cf1d95f0a9595a71a9db5835` |
| Complete 2,369-member package-source fingerprint | `83c990b7805f4edb3a0e2d789da294c3c2a36454d6b2f16467524840186c597f` |
| Native input/repair owner at execution and review | `827a48ad49498d116522fcee75a0ce408fe97dccf532baacb69d3e1fd25c5f91` |
| Locked dependency file | `ea491f9e8789d6cd5a18d89908d16ef7db4ee3c9ed4729e32354bc713b135f24` |
| Producing-code archive | `44213b142a6add09090be7861518b8cbc0060ebc4ffe160c5d93358b7f7f820d` |
| Raw native-file archive | `011a12f503beeab388b3cbc5a32268cee3693bd931b2be94c63ca64d023f2283` |

Every archive member was CRC/size/SHA verified: **2,375 producing-code
members**, **235 native raw members** and **two worker streams**. The review
also fully rechecked the four closed external source, metadata, provisioned
profile and held-software censuses. At this review snapshot, every archived
package-source byte matched its active counterpart. This is an as-of check
at the pinned package/owner identities above, not a claim that later additive
source changes remain byte-identical.

The separate retained review is
`/tmp/rubisco-xtb-control-root-review-v1.json`, SHA
`dbe0aa12328708afc533a6065ad3b1d1d6376038a366270626d0f29088d70d5b`;
its final read-only checker is
`/tmp/rubisco-xtb-control-root-review-v1b.py`, SHA
`83628a9e4e93c59d64f339831c57854e2d50462247dcac70801ea731b7bfcdd5`.
The successful review report was captured at **2026-10-10 00:16:19.774746 UTC**
(retained source-file mtime), before the prospective additive owner change.
Two preliminary checker-only refusals concerned JSON-list/tuple
canonicalization and a local archive-key variable. Their helpers/refusal
observations remain separate references; neither changed the closed packet
or executed native science. The successful review body measured
**2.243398 CPU / 2.247496 wall seconds**; startup, earlier interactive checks,
preliminary checker CPU and final output-write tail were not fully measured
and are not assigned zero cost.

## Complete observed resource cost

The parent-measured complete control worker, including cold startup and all
waited native descendants, consumed **1.213371 CPU / 1.516949 wall seconds**,
below 20 / 120 seconds. The worker's earlier snapshot was 1.198298 CPU /
1.425255 wall seconds; it excluded its terminal write and exit tail and is
not substituted for the complete parent measurement. Waited native-process
CPU totaled **0.276374 seconds**.

Outer GNU time measured the complete `uv run --no-sync` launcher operation,
including startup, custody, worker/native children and packet closure:
**7.29 user + 0.73 system = 8.02 CPU seconds**, **8.28 wall seconds**, peak
RSS **263,544 KiB**, exit **1**. These are rounded display values. Subtracting
the unrounded worker cost gives approximately **6.806629 parent CPU seconds**,
rather than the launcher summary's earlier 6.332061-second self snapshot.

Exact original outer resource/stdout/stderr bytes and the independent review
are copied into a separate ordinary closed witness packet:
`/tmp/rubisco-xtb-controls-outer-witness-v1`, **nine files / 30,206 bytes**,
with a **64 KiB selected member/packet cap**, files `0444` and directory `0555`.
Its closed-census SHA is
`1c6755377ccddbafc6d93aaf61f98f6d3ad3fba1ebfd7478ace8cfa24a925137`.
The source capture timestamps and all copied hashes are retained there. This
is not an added ArtifactPlane publication or a mutation of the 328-file
execution packet. Witness capture itself measured 0.000819 CPU / 0.000819
wall seconds before its final metadata/mode/readback tail.

No enzyme chemistry entered this attempt. A successor must first demonstrate
that its selected optimizer actually preserves the declared fixed positions;
source-supported settings require separate implementation and execution
bindings, while this refusal remains unchanged.
