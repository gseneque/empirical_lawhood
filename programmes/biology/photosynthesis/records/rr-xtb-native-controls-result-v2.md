# Existing L-ANC native xTB controls: complete pass

SPDX-License-Identifier: CC-BY-4.0

**17/17 controls PASS, 10 October 2026.** The separately frozen successor
uses xTB's existing L-ANC optimizer and satisfies the unchanged exact-fixing
and fresh unmasked-gradient criteria. All six enzyme cases remain
**UNENTERED** in this closed control packet. This completes the selected
native control component; it supplies no repaired enzyme, kinetic response
or biological evidence. Role:
**DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The [frozen v2 protocol](rr-xtb-native-repair-protocol-v2.md) preserves the
[first RF fixing refusal](rr-xtb-native-controls-result-v1.md), its exposures
and cumulative cost. Fifteen exposed gradient queries are repeated in this
new control menu; they are not fresh assessment evidence. Existing native
code and [held six-case inputs](rr-xtb-input-integration.md) are reused with
zero new authentic source decoders or chemical context constructors.

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
| H1-fixed L-ANC optimization | PASS |
| Fresh final unfixed gradient | PASS |

| Assigned enzyme case | Actual status in this packet |
|---|---|
| Unedited computational reference V2 | UNENTERED |
| Unedited computational reference V3 | UNENTERED |
| Both-LSU D263N V2 | UNENTERED |
| Both-LSU D263N V3 | UNENTERED |
| Both-LSU H287N V2 | UNENTERED |
| Both-LSU H287N V3 | UNENTERED |

All 17 native commands, the worker and launcher exited 0. Four observed
L-ANC cycles correspond to six source-inferred optimizer objectives:
initial evaluation, four cycles and final driver evaluation. The other
sixteen commands each supply one objective, giving **22 objectives** and a
**39-objective entered conservative bound**, below the 48-objective cap.
Suppressed inner SCC iteration counts remain unidentified. Across both
control packets there are **33 scientific control processes / 47
source-inferred objectives**; the two prior version/help processes remain
separate. No extra query fills the unused allowance. Registered task
receipts, enzyme native commands and endpoint fits are zero.

## Independent numerical replay

The independent checker reads retained raw inputs and outputs without
importing producer numerical APIs or executing native code. It verifies
all exact argv/control settings, the three actual displaced components,
both signed steps, the unchanged tiny field and the common translation of
both the molecule and field.

Native H1x analytic gradient is **0.021274456476641 Eh/Bohr**. Central
differences at 0.001 and 0.002 Bohr are **0.021274673** and
**0.0212753225 Eh/Bohr**, with errors **2.16523359e-7** and
**8.66023359e-7**, below **2.1274456476641e-5 Eh/Bohr**. The four H1y/H2z
checks and both-step comparisons also pass. Their signals are smaller
than the absolute tolerance, so those passes provide weaker relative
sensitivity checks. The retained **0.52917726 Å/Bohr** conversion and
derivative chain rule remain explicit.

The common translation gives zero displayed energy change and maximum
gradient-component change **2e-13 Eh/Bohr**. Capacity input exactly matches
the held **13,754 scientific / 13,749 native** D263N/V2 field, with only
the five exact-zero CA rows omitted. Both H2 atoms lie beyond its complete
field box. All **13,749 ordered PCgrad rows** are finite; displayed zeros
at eight decimal places do not establish exact zero physical derivatives.
This tests ingestion and output census, not enzyme MM-force accuracy.

H1 remains exactly **(0,0,0) Bohr**. Final H2 is
**(1.46819939202277,0,0) Bohr**. Fresh unrestricted gradient on those exact
final coordinates gives free-H2 Cartesian L2
**5.444442789781962e-5 Eh/Bohr**, below **3e-4**. Fixed-H1 physical L2 is
**2.691011274110828e-5 Eh/Bohr**: masking did not make its physical force
zero. Final gradient-header versus optimizer-stdout energy differs by
**1e-12 Eh**, within **1e-6**; the producer's higher-precision displayed
final-energy comparison is zero. These results do not prove a Hessian
minimum, stable enzyme proton well or reaction barrier.

Source review binds the actual native L-ANC path: the pinned
`relaxation_engine.f90` projects the Hessian before unpacking it, while
the previous RF path consumed an unprojected dense copy. L-ANC also
projects rotational directions. The independent full mobile-force check
therefore remains necessary for the six enzyme cases in their fixed
external fields. The GFN2 hardness-99 damped interaction is the selected
model, not the PySCF bare Coulomb operator.

## Immutable custody and source ancestry

The execution packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-xtb-native-controls-v2`:
**362 files / 19,899,919 bytes / 21 authenticated artifact publications**.
Every file is `0444`, every directory `0555`, and all members fit the
16 MiB selected limit. Closed-census SHA-256:
`476269c7ab516b6027cb96615ec111b700a75111f0a227e188c5299f442e3a1b`.

Both independent retained reviews verify every physical member and all
21 manifests/commit markers. The **16 pre-contact publications** include
source/configuration/code, complete 17-control/six-case no-entry rosters
and the closed prior execution/outer witnesses. All three ZIPs are fully
CRC/size/SHA checked: **2,376 producing-code members**, **254 native raw
members**, and **two worker streams**. Full source, metadata, provisioned
profile, held-software, prior-control and prior-outer censuses are rechecked;
all twelve selected publisher/tag optimizer-source bindings agree.

| Frozen binding | SHA-256 |
|---|---|
| Scientific protocol v2 | `1ff4dcbc93490f8d05a2463f6ba3cb363130bb6e356a1abffcc59f412afad9f4` |
| Actual execution configuration | `52e1753cadf61b8556303433601e5b950de019b3db8be077ce498d7504fd3b88` |
| Complete 2,369-member package fingerprint | `260bd1c2002009d10851b42b2223054918e7e36b1b2525d7abe5390ebcf22db1` |
| Native repair owner | `04633934f8222f8641466dd4c180bf8a864b80d02cd1617ae47fbd4d7b380238` |
| Locked dependency file | `ea491f9e8789d6cd5a18d89908d16ef7db4ee3c9ed4729e32354bc713b135f24` |
| Producing-code ZIP | `7fb24301d699d99eed1ee81439970cade90761e1f43214e72f8fddc7e510a26b` |
| Native raw ZIP | `831f035d03966f1ab759afa3011163932f2dee4e1a3b2dbeb468cafe9070347a` |

Archived package bytes match active source at these review snapshots;
future changes do not inherit that equality. The detailed independent
review is `/tmp/rubisco-xtb-control-independent-review-v2.json`, SHA
`48b746b6c329ac9552365556098a244136b7287e3bcd21a34a8445dca8fc198e`,
with final checker `/tmp/rubisco-xtb-control-independent-review-v2a.py`, SHA
`6732360957466b4ff4d0baf0b6f31e37495d38ea3a0feee1c916526b26f90af8`.
Its successful body costs **2.638265 CPU / 2.641305 wall seconds**. Root's
separate review SHA is
`18696072b6f782c40cfa1824346ccfe64c84771e061d33652615b463a7123de4`.

Two checker-only refusals are retained: root's JSON-list/tuple identity
comparison and the independent checker's exact comparison of native
writer coordinates with higher-precision inputs. The latter successor uses
the inherited **5e-14 Bohr** display comparison; the scientific
**1e-10 Å** anchor criterion is unchanged. Earlier interaction, unsuccessful
checker costs, startup and final report-write tails are unmeasured, not zero.
No review executes native science or changes the closed execution packet.

## Complete observed costs and remaining allowance

Complete waited worker-plus-descendant usage is **1.078974 CPU /
1.313518 wall seconds**. Combined with v1's 1.213371 CPU seconds, this is
**2.292345 CPU seconds**, below the original 20-second combined control
allowance. The launcher's earlier self snapshot is 6.261804 CPU seconds
and 7.786538 wall seconds; its unmeasured closure tail is not discarded.

Final outer GNU time includes `uv`/interpreter startup, custody, all waited
children and immutable closure: **7.12 user + 0.70 system = 7.82 CPU
seconds / 8.29 wall seconds**, peak RSS **264,720 KiB**, exit 0. These
display values are rounded. Conservative full-outer charges retain
**8.04 seconds for v1 + 7.84 for v2**, leaving **184 CPU seconds** for the
future case parent after rounding the 184.12-second remainder down.
The original monotonic start **647960.547165464** and deadline
**652160.547165464** remain unchanged; there is no 4,200-second clock reset.
The new controls plus future cases retain their combined **64 MiB** cap;
v1's **19,698,076 bytes** and two separately bounded 64 KiB outer witnesses
remain included in the **86,938,012-byte** cumulative selected ceiling.

Exact final GNU-time/stdout/stderr, both reviews/helpers and both checker
refusals are copied to the separate ordinary closed witness
`/tmp/rubisco-xtb-controls-outer-witness-v2`: **11 files / 48,992 bytes**,
below its 64 KiB member/packet cap, files `0444`, directory `0555`.
Census SHA:
`340a89d2726de47a3696dd89b93151df90385706ffdc54fe30cfc96aa1f08a45`.
Capture body costs **0.001305 CPU / 0.001304 wall seconds**, with final
metadata/mode/readback tail unmeasured. This witness adds no ArtifactPlane
publication and does not change either closed control packet.

The next selected step is the six matched repair/escape cases under their
existing physical gates. Their outputs must retain convergence failures,
full mobile forces, proton identities, contacts and geometry disposition.
Passing this control component cannot supply their missing geometry or a
mutation-to-turnover/specificity relation.
