# Archived Rr Amber core: admitted source and reuse limits

SPDX-License-Identifier: CC-BY-4.0

State: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.
Reviewed **10 October 2026** on `recchain`.

The historical M1v5 archive supplies a complete **pre-relaxation dry atom
inventory and modeled H coordinates** for a truncated, His91-repaired Rr
homodimer. The newly closed factual source packet retains its exact geometry,
charges, atom types and bonds; it performs **no new preparation, native import,
simulation, SCF, endpoint fitting or ArtifactPlane publication**. This useful
reuse does not supply the six reactive states in the
[coupled chemical inventory](rr-coupled-chemical-inventory.md), an authenticated
assay parent, mutation-to-kinetics or a nomination.

## Exact source and closed packet

The selected successor is
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-rr-amber-core-v1`.
It has **44 regular files / 13,788,149 bytes**, files `0444`, directory `0555`,
within **16 MiB/member / 32 MiB/packet**. Its physical register excludes itself
from its hash table to avoid a self-hash cycle and includes its own byte size
in the complete physical census. It is not a registered task receipt.

| Authoritative retained member | Bytes | SHA-256 |
|---|---:|---|
| `rr-amber-core-register-v1.json` | 12,703 | `a6deb1386faa51e39669208fecb79a68a859888f60c6fcfaf689cfbc8c1c3ec1` |
| `dry-core-source-projection-v1a.json` | 3,910,957 | `bfbaa57a1b9d466e311c23c37616cd54771ac170d7fc361ef7769a4004040c5f` |
| `native-asn-templates-v1.json` | 11,467 | `bd35c76940c4a727641a315208ef7cc1895c08184ba00dc7edfb1a80162e635e` |
| `native-unjoined-atoms-v1.json` | 5,110 | `408ec0792266c11c916700fba77b1517f997295ec0c4b3d83ccc2456726d7801` |
| `amber-audit-v3-observation.json` | 26,809 | `f49249c30623e10de3b453f9d164134da8a57a6a57af97ddefce737f3b9aeff3` |
| `asn-audit-v2-observation.json` | 7,105 | `9b834146b763304efa89cce09264de9ba59a3c2baaef90f382c84bce64f2e43f` |

The original canonical envelope remains outside the selected packet:

```text
/media/chevre/SEMIOS/icf-yolo/programmes/rubisco-el/r02s-m1-pilot-v5/runs/rubisco-r02s-m1-native-v5.pilot.production/outputs/rubisco-r02s-m1-native-v5.native-protocol/native-result.canonical.json
```

It is **55,092,530 bytes**, SHA-256
`8dbc9e528e341cee554128bcedc9876f2f3141c2e4b62a22b737f9b5bcef855a`.
Its `value.prepared_archive_base64` contains the original **41,295,643-byte**
ZIP, SHA-256
`a22c4fb687e88ff36d92d06378f3b3176b565fd1281b83cccad52454b0f1a653`.
Two independent stdlib parsers authenticated **all 42 members**, their full
CRC/size/SHA identities and **180,758,177 expanded bytes**, without extracting
the entire archive. The exact census is WT/M100T/D206E × HID91/HIE91 × seven
named source/relaxation files. Only **WT-HID91/prepared.prmtop** and
**WT-HID91/prepared.inpcrd** supply this selected core. No `relaxed.npy`
coordinates are substituted.

The selected topology is **22,365,456 bytes**, SHA-256
`87b5ed6e40ea77afde056312f923fca44f8b6ee164d8dd973e6deb3b79b2b902`.
It exceeds the retained member ceiling and stays an exact external archive
reference. The unchanged coordinate original is retained at **4,262,089
bytes**, SHA-256
`e7d05ec99783f96106834d65f9b55631dfdba665b9255417cc4ca43011497de1`.
Source read ceilings are separately **64 MiB envelope, 48 MiB decoded ZIP,
32 MiB/source member, 256 MiB expanded archive census**. These do not increase
the retained packet or any generic engine limit. The packet explicitly claims
**no self-contained portable source package**.

## Complete source correspondence

The whole archived solvated model has **116,767 atoms / 35,253 residues**.
Only its first **920 residues / 13,828 atoms** form the projected dry core:
two **458-residue protein chains, author 2–459**, two RUB ligands and two Mg
ions. There are **7,046 heavy atoms, 6,782 H and 13,994 bonds**, with no
cross-boundary covalent bond. Names, elements, native Amber types, fixed-width
mass/charge tokens, coordinates and bond/parameter tokens remain explicit.
Coordinates preserve their native **12-character, seven-decimal-place** fields.
Amber charge tokens are divided by the exact scale **18.2223**; the derived
Decimal charge is **−29.999996494493011310317577912777201560725045685800 e**
at the stated 50-digit calculation precision. This is a partial-charge sum,
not an independently observed chemical charge or electronic-state proof.

Exactly **7,028 positive-occupancy 9RUB heavy atoms** match by one translation
**(+14.1641370, +43.3948653, +47.0584385) Å**, with **zero** Decimal coordinate
residual. The **18 modeled heavy atoms** are ten His91-repair ring atoms,
six completions of zero-occupancy source atoms and two terminal OXT atoms.
All H are historical generated geometry; 9RUB deposits no H or water.

The complete native denominator also retains **16 source atoms not inherited**:
six positive-occupancy Asp91 sidechain atoms replaced by His91, six
zero-occupancy atoms completed separately, and four partial chain-A residue460
atoms omitted by the old 2–459 recipe. A460 N has positive occupancy; its
CA/C/O have zero occupancy. Thus the sixteen omissions are **seven positive /
nine zero occupancy**, rather than silently discarded source coordinates.
Both repaired core sequences match P04718 **2–459**, while source 9RUB has
Asp91. The complete 466-residue sequence, missing termini and His6 assay tag
are not reconstructed. This remains a selected truncated computational parent.

The original modeled-heavy witness field in v1 used the misleading name
`zero_occupancy_native_id` for two replaced positive-occupancy Asp91 CG atoms.
All initial helper/projection/cost bytes are retained. Authoritative **v1a**
records the actual native occupancy and replacement/completion role; geometry,
charges, bonds and inherited atom identities are unchanged. Independent parser
refusals and their helper versions are also retained. One initial stderr is
explicitly a normalized reconstruction, not an original captured stream.
Earlier `pending` inspection fields remain historical; the register owns
current closure and independent-audit status.

## Reusable chemistry and next construction

Ground RUB has **26 atoms**, including C3-HC3 and O3-HO3, and approximately
**−3.999998 e** per ligand. Peptide-linked KCX has **23 atoms** and approximately
**−1 e**; each native Mg has **+2 e**. These are ground keto/MM witnesses,
not the enolate−5/protonated-KCX0 state parameters. The two old HID91/HIE91
views concern repaired residue91, rather than the proposed reactive relay.
Active-site His287 is **HIE, NE2–HE2**, in both source chains. A selected
ND1-H reference needs removal of HE2 and newly modeled HD1 coordinates.

All **30 native ASN source records** have fourteen atoms: eight inherited
positive-occupancy heavy atoms and six old generated H. A deterministic
same-chain lowest-author-residue rule selects **A9/B9**, with no mutant labels
or fitted outcomes. The retained donor rows can support a declared proper-frame
transplant of OD1/ND2/HD21/HD22 while keeping a target backbone/CB/CG fixed.
Such geometry is a new amide-pose hypothesis; donor heavy/H geometry, source
charges and any assigned mutant fields must stay distinct. Its native amide
planarity deviations are retained rather than idealized. A secondary flipped
amide requires a separately frozen denominator.

The next pure construction must explicitly conserve H_a/H_b through the two
relay views, build both-chain ASN mutations and any selected His287 tautomer,
derive the full capped QM formulas/charges/electrons, remove double-counted
QM/MM atoms, fix one boundary-charge rule and audit all geometry/refusals.
The old ligand remains **unrelaxed keto geometry**; changing H and Lewis bonds
does not validate enediolate planarity. No optimized reactive state or
kinetic-ready calculation is admitted by source reuse. See the
[chemical inventory](rr-coupled-chemical-inventory.md) and
[coupled entry](coupled-chemistry-entry.md) for the separate scientific gates.

## Dependencies, rights and costs

The source projection and audits used the selected locked EL electronic
interpreter, **CPython 3.11.14**, with `uv run --no-sync` and stdlib only.
The old AmberTools24 path is absent. Sibling installed metadata supplies
OpenMM **8.3.1**, ParmEd **4.3.1** and Bio **1.88**; its OpenMM source version
is `8.3.1.dev-6e13f13`, with `release=False`. PDBFixer is cached source only,
not installed. None was imported here and no environment was synchronized.

Pure inherited-coordinate/template assembly needs none of those native tools.
If later selected, OpenMM `Modeller.addHydrogens(forcefield=None)` creates a
native context and runs a maximum-50-iteration minimization using simple H
geometry/repulsion terms. Its random initialization, platform, effects and
budget require a separate protocol/profile. PDBFixer is not a silent shortcut:
missing-atom completion minimizes natively, and nonstandard H completion may
fetch CCD records. No native completion is authorized by this factual note.

Exact KCX/RUB parameter originals, historical isolated-KCX/build witnesses,
their MIT attribution and the local ASN-template license are retained. The
historical private archive and software witnesses keep their existing source
rights; this note creates no redistribution license for them. Source exposure
and old native preparation are historical, not fresh assessment evidence.

Measured initial/corrected projection windows were **2.471613 / 2.504211 CPU
seconds** and **2.471666 / 2.504275 wall seconds**. The independent full archive
audit measured **4.554703 CPU / 4.554775 wall seconds**; independent ASN audit
**0.045287 / 0.045356 seconds**; closure validation **0.118425 / 0.118424
seconds**. Separate metadata, omitted-atom and donor-inspection costs remain
in the register. Prior interactive checks, failed checker costs and final
serialization/write/chmod/readback tails are **unmeasured, not zero**. These
windows are not an end-to-end cost or an old molecular-execution cost claim.
