# Rr complete QM/MM: retained native coupling attempt v3

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026** on `recchain`. State:
**DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The v3 attempt passed the synthetic classical C1 control and retained nine
normally terminated embedded-QM gradient calls for C2. C3 stopped during
one-atom optimizer initialization; reporting then failed. **No C3 quantum
objective, capacity control, authentic chemical source admission or enzyme
construction entered.** The full coupled C2 finite-difference result cannot
be independently certified because its total energies and eight-atom coupled
gradients were not saved. This note reports v3 only; the separately selected
[v4 protocol](rr-qmmm-native-repair-protocol-v4.md) is a successor, not a
revision of these observations.

The [reference design](rr-qmmm-repair-design-v1.md), [frozen v3
protocol](rr-qmmm-native-repair-protocol-v3.md) and [earlier operational
refusals](rr-qmmm-operational-refusals-v1-v2.md) define the ancestry. The
original [six failed electrostatic enzyme repairs](rr-xtb-native-repair-result-v3.md)
and [initial geometry failures](rr-coupled-initial-geometry-result-v1.md)
remain unchanged. This synthetic development attempt supplies no admitted
enzyme geometry, reaction state, kinetic response, qualification, nomination
or consequential EL capability. Existing scientific negatives and phase gates
remain open.

The immutable execution packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-qmmm-native-repair-v3`.
Its independent read-only raw/arithmetic witness is
`/tmp/rubisco-qmmm-c2-raw-audit-v3`. These are local external evidence paths,
not shipped public assets.

| Exact retained identity | Bytes | SHA-256 |
|---|---:|---|
| `closed-census.json` | 96,169 | `7e3f7b968c25f66622762f43b008caed75f32e1fcfe8fdab22ad6c1208796c75` |
| `sources/frozen-protocol.md` | 14,204 | `f3a0f5a70bfcf156f85305822d9c4b50ccccada8e323f0fe66823c74ebade3c9` |
| `sources/frozen-config.json` | 603,673 | `bf70bd633560d226905bc740b9464fda99a73c157fddc3469ef8c7aa1635333d` |
| Complete producing code ZIP, retained in two ordered chunks | 11,548,364 | `ec4f66e145f8f8e144fae14370506d778db37d8fd5fd9b1de30a26e0175ac46e` |
| Independent `audit.py` | 18,657 | `4944bc8491a5397ff6518778605ec37fab914b46174856017ccaef65b666f8c6` |
| Independent `observation.json` | 93,342 | `cf0f6eaae189c665985f4a2caa1ee83934bf3b31e0cea4c8d4a21d60e35590f9` |

The closed denominator is **51 genuine publications / 450 physical files /
51,597,981 bytes**, including the census. Independent custody review
authenticates the actual publications. The separate standard-library audit
checks every physical member's hash, size and read-only mode, the complete
**2,389-member** producing ZIP, and the **18 actual C2 plan/raw publications
(nine pairs)** by payload, manifest, commit-marker and acknowledgement hash joins.
Those ordinary byte checks complement the existing typed ArtifactPlane
verification; ordinary JSON does not acquire canonical scientific authority.

The producing ZIP binds `native_coupling.py` to
`c6bd55ce0e272c0612251f6ecfa919c1b46664557a6b5896f79e61daf572ee0a`,
`native_controls.py` to
`cd3ea826faae24276d5dc07ab6a7320187f18a550a4f5f0669ec6740d4a7d8eb`,
and the strict callback owner `rr_qmmm_xtb.py` to
`d2c26705e776304c50b0563754210d6722368896e63a1c2afd504bf24b54b40c`.
The v3 index-sequence correction preserves exact indices, LJ parameters and
Coulomb-product checks. Its **27 synthetic tests** include actual pure-Python
OpenMM Unit/Quantity values and mutable native-shaped lists; those checks
execute no native backend or physical source constructor.

| Assigned stage | Retained outcome and limit |
|---|---|
| C1: two neutral LJ particles | PASS: one OpenMM Reference Context and three force evaluations. Independent analytic energy, force and central finite-difference checks pass. This remains a synthetic software control. |
| C2: ethane baseline plus eight probes | Nine source-bound xTB calls, nine plan publications and nine raw publications. Complete raw QM/PC gradients and embedded-QM finite differences pass independent checks. Original total coupled numeric witnesses are absent. |
| C3: one active H, seven fixed atoms | Optimizer initialization entered; no quantum callback or optimization point entered. Actual output records a one-atom active region and an artificial self-bond. The pinned driver independently requires at least two atoms. |
| Largest-field capacity control | UNENTERED. No capacity result follows from the small C2 field. |
| Reference enzyme source assembly and repair | UNENTERED. No chemical source admission, reference construction or enzyme objective occurred. |

All nine C2 calls use the [source-bound xTB profile](rr-xtb-source-and-profile.md):
actual version **6.7.1 (`edcfbbe`)**, GFN2, charge/UHF **0/0**, electronic
temperature **300 K**, accuracy **0.05**, maximum SCC iterations **250**, one
thread, explicit parameter file, no solvent and no restart. Each raw output
has exactly one converged SCC solve, **nine iterations**, and normal
termination. Each callback contains **five QM rows**, including one generated
cap, with declared **10 all / 8 valence electrons**. The complete field has
four ordered IDs: two exact-zero omissions and two serialized nonzero sites
with hardness **99 Bohr**. All nine raw gradients have five finite QM rows
and two finite native PC rows. Restoring the omitted zeros retains the full
four-row PC order. The baseline native PC-gradient L2 is
`2.809176213768015e-5 Eh/Bohr`, so the field derivative is exercised.

The independent finite differences below use only the retained **embedded-QM
energy** and raw QM/PC gradients. They include the source-selected link
chain rule for the C0/C1 boundary and the nonzero field derivative at H5.
The displacement is **0.0001 Å**. The native conversion is **0.52917726
Å/Bohr**; ASH uses **0.5291772109303 Å/Bohr**, with the declared gradient
conversion preserving the derivative in Å.

| Physical probe | Embedded-QM FD, Eh/Å | Raw projected QM/PC derivative, Eh/Å | Absolute discrepancy, Eh/Å |
|---|---:|---:|---:|
| C0 x | −0.00139705 | −0.00139702779959 | `2.22004e-8` |
| C1 x | 0 | 0 | 0 |
| H2 y | −0.0004730 | −0.000472992523985 | `7.47601e-9` |
| H5 y | 0.00003725 | 0.0000372464984606 | `3.50154e-9` |

These four discrepancies lie below the original **4e-5 Eh/Å** control bound,
but omit every classical OpenMM energy/gradient contribution. They are **not
full coupled C2 certification**. Worker timing output records nine QM/MM and
nine OpenMM evaluations, and progression to C3 indicates producer control
flow accepted C2. Neither replaces the missing total coupled energies,
eight-physical-atom gradients and four original error values.

C3's one-atom incompatibility is a **source-supported inference**, not an
independently retained first exception message: actual initialization logs
and the pinned geomeTRIC minimum-atom check support it. Unnormalized NumPy
count metadata prevented control-report serialization; the final retained
worker traceback explicitly records `TypeError: Object of type PosixPath is
not JSON serializable`. No completed control/worker JSON report exists.
The frozen summary preserves that absence and its literal conservative
interruption charge; it does not infer zero work from missing reporting.

There is also a pre-frozen C3 criteria mismatch: the original declaration
uses **drms 1e-3 / dmax 2e-3**, while the implemented setup passed
**1.2e-3 / 1.8e-3**. No optimization point evaluated those criteria. This is
an exposed software-conformance defect, not a passed optimizer test; neither
historical bytes nor enzyme thresholds are changed here.

Complete normally waited worker/descendant CPU is **9.825274 seconds**.
The separate full outer witness records **21.69 CPU / 18.71 wall seconds**,
including launcher, worker, descendants and closure. Combined with v1/v2,
complete workers total **14.822137 CPU seconds**, conservatively carried as
**15**; full outer CPU totals **41.37**, leaving parent residual
**26.547863**, conservatively carried as **27**. The **nine entered quantum
objectives** remain charged to the original control and whole-operation
caps; they are exposed ancestry, not fresh evidence. The original monotonic
start/deadline and output denominator persist. The packet's approximately
557-second elapsed whole-operation clock includes earlier preparation time
and differs from this attempt's 18.71-second outer window.

The independent raw audit separately measured **0.737500157 CPU /
0.737555454 wall seconds** through source, custody and arithmetic checks;
interpreter startup, report serialization and closure tail are excluded.
Its first draft misread cumulative process counts as per-call counts and
refused. That exact draft and stderr transcript copy remain in the witness;
the corrected read-only audit checks counts 1–9. No scientific calculation
was repeated. The [assessment design](rr-coupled-assessment-design.md) still
requires reaction-sensitive observables before biological endpoint inference.
