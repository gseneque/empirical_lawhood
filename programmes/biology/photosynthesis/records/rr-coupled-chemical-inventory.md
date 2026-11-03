# Chemical inventory for a provisional Rr coupled test

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026, Australia/Sydney**, on `recchain`. This is a
source-backed construction specification for the proposed **unedited
computational reference / D263N / H287N × two enolate–KCX proton views** in
the [coupled-chemistry entry](coupled-chemistry-entry.md). It does not report
completed protonated coordinates, a certified enzyme species, a quantum
calculation or a rate response. The first three heavy-atom projections are
three scaffolds with **zero completed proton states**; they do not constitute
the six prepared chemical contexts below.

## Native records and atom correspondence

The closed 9RUB intake is at
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-rr-structures-v1`.
Its **19 files / 6,195,952 bytes** are a source-intake census, with **zero
artifact-plane publications or scientific executions**. They are distinct from
the [27-publication analytical packet](branch-sensitivity-result-v3.md).

| Exact local source | SHA-256 |
|---|---|
| `9RUB-original.cif` | `33242f8e519c2e032c5a83de33a6350eb5c38cef42b5a14e1f8ecfb9230575dd` |
| `9RUB-original.pdb` | `80dcc3cfdcd12154f1d7c21e9438b9e6b0e9d887381aeeef6f2350b3e1b41fd5` |
| `9RUB-native-atom-mapping-v1.json` | `caa36c34be4eb61cc6b804e6130f4e0845b27f95fa74117db02229ac5d787985` |
| `rr-structures-inspection-v1.json` | `36f8b24b74808d2a3c6c9a76c59df5e94265214722f7c01078204960eabfb644` |
| `rr-structures-register-v1.json` | `5b0a34d9c23f8a69e39c1dad35beb5e4d5976da05151818c30e0612552cae4a5` |

The full native mapping retains CIF atom-site IDs and PDB serials as **different
identifiers**. For example, chain-A substrate C2 is CIF **7002**, PDB **7004**;
chain-B substrate C2 is CIF **7024**, PDB **7026**. Neither numerical ID may
be silently substituted for the other.

Both native LSU chains, both original ligands and both Mg atoms belong to the
source scaffold. The full substrate atom names are:

```text
C1 C2 C3 C4 C5 O1 O2 O3 O4 O5 P1 P2 O1P O2P O3P O4P O5P O6P
```

These eighteen names map in that order to chain-A RUB author **600**, CIF
**7001–7018**, PDB **7003–7020**, and chain-B RUB author **700**, CIF
**7023–7040**, PDB **7025–7042**. Mg author **500** is CIF/PDB **7019/7021**
in A and **7041/7043** in B. Native FMT author **601** in A supplies C/O1/O2,
CIF **7020/7021/7022**, PDB **7022/7023/7024**; FMT author **701** in B supplies
the same names, CIF **7042/7043/7044**, PDB **7044/7045/7046**.

The explicit native covalent joins are **LYS191-NZ–FMT-C**, with recorded
distances **1.452 Å / 1.513 Å** in A/B; the CIF leaves their bond order
unspecified. A constructed KCX uses **FMT C→CX, O1→OQ1, O2→OQ2**, preserving
these source correspondences. Its NZ–CX single bond and protonation are new
chemical assignments. Native FMT's standalone formic-acid dictionary also
contains C–H and O2–HO2 bonds. Those hydrogens are absent from 9RUB and must
**not** be added to a carbamate by copying the FMT template: a retained C–H
alongside NZ–CX and the two oxygen bonds would overfill carbamate carbon's
valence. The [RCSB KCX dictionary](https://www.rcsb.org/ligand/KCX) describes a
neutral free amino-acid component, not the charge or H inventory of a
peptide-linked, activated carbamate.

The native protein side-chain correspondence needed for a common boundary is:

| Role | Ordered retained side-chain atom names | Chain-A CIF IDs | Chain-B CIF IDs |
|---|---|---|---|
| K191 plus linked carbamate | CB/CG/CD/CE/NZ, then linked CX/OQ1/OQ2 above | 1452–1456 | 4954–4958 |
| D193 | CB/CG/OD1/OD2 | 1469–1472 | 4971–4974 |
| E194 | CB/CG/CD/OE1/OE2 | 1477–1481 | 4979–4983 |
| D263 | CB/CG/OD1/OD2 | 2005–2008 | 5507–5510 |
| H287 | CB/CG/ND1/CD2/CE1/NE2 | 2195–2200 | 5697–5702 |

9RUB contains **no deposited H or water atoms**. Native metal contacts are
geometrical witnesses, not an imposed ideal shell: in A, Mg–FMT O1/O2 are
**2.385/2.445 Å**, Mg–RUB O2/O3 **2.471/2.619 Å**, Mg–D193 OD1 **2.549 Å**;
E194 OE2 is **3.701 Å** away. The complete census also preserves cross-chain
N111 contacts. Do not move these atoms to standard coordination lengths or
add a sixth water without declaring a new modeled change. The water-rich,
RuBP-free 2RUS source remains a separate sensitivity witness. Its linked FOR
C/O/H1 is not a complete two-oxygen carbamate.

The native D91/H91 sequence conflict and unresolved His₆ assay-parent join
remain as stated in the [entry](coupled-chemistry-entry.md). A deposited-D91
reference and an explicitly reconstructed-H91 reference are different
selections. Neither receives an authenticated assay-WT identity here.

## Full substrate bonds and declared charge

The native 9RUB `_chem_comp_atom`/`_chem_comp_bond` tables describe the neutral
acid **C5H12O11P2**, consistent with the
[RCSB RUB dictionary](https://www.rcsb.org/ligand/RUB), formal charge **0**.
The heavy-atom bonds are the following; `=` and `–` denote the dictionary's
double and single Lewis bonds, not measured bond orders in the protein:

```text
C1–C2–C3–C4–C5
C1–O1–P1; C2=O2; C3–O3; C4–O4; C5–O5–P2
P1=O1P; P1–O2P; P1–O3P
P2=O4P; P2–O5P; P2–O6P
```

Its twelve dictionary hydrogens are C1 **H11/H12**, C3 **H3**, C4 **H4**, C5
**H51/H52**, O3 **HO3**, O4 **HO4**, and phosphate **HOP2/HOP3/HOP5/HOP6** on
O2P/O3P/O5P/O6P. All twelve are dictionary roles rather than native observed
coordinates. A declared keto-RuBP tetraanion removes the **four phosphate
protons only**, producing **C5H8O11P2, Q=−4**, with eight H and eighteen heavy
atoms. [ChEBI:57870](https://www.ebi.ac.uk/chebi/CHEBI%3A57870) independently
records this tetraanion and its four-phosphate-OH deprotonation. That chemical
record does not establish the bound microstate or its occupancy in 9RUB.

For both proposed enolates, keep all eighteen substrate heavy atoms, the two
phosphates and the C4 hydroxyl. Remove **H3 from C3 by proton transfer**, not
hydrogen-atom or electron removal. The illustrative enediolate Lewis forms use
**C2=C3**, **C2–O2** and **C3–O3**, with the remaining heavy bonds above
unchanged. V2 has **O2− / O3–H**; V3 has **O2–H / O3−**. Each is therefore
**C5H7O11P2, Q=−5**, with seven H and eighteen heavy atoms. Negative-charge
localization and phosphate double bonds here are Lewis bookkeeping;
delocalized electronic densities and actual relaxed geometries are uncomputed.
The C3 keto-state stereocentre is lost on this declared C2=C3 construction;
retaining the native C4 stereochemistry does not establish the required cis
enediolate geometry from the unmodified heavy coordinates.

## Proton identities, linked KCX and electron balance

Give the newly constructed keto C3 proton a persistent identity **H_a**
(dictionary role H3), and the keto O3 hydroxyl proton **H_b** (HO3). Use a
separate identity for KCX's **NZ–H**, which is retained throughout. Proposed
KCX deprotonation/protonation concerns a **carbamate oxygen**, not NZ and not
the free amino acid's peptide termini.

The primary [2022 study](https://doi.org/10.1021/acscatal.2c01677) proposes
KCX abstraction of C3-H, return of that proton to O2, and acceptance of O3-H
by KCX for its **state I** route. The alternative **state II** puts the latter
proton on His and leaves KCX negative; it is outside this initial two-view
roster. Source state I coordinates explicitly place a carbamate proton on
**OQ1** and the His proton on **ND1**. Transporting these roles to Rr is a
declared hypothesis, not a deposited Rr proton assignment.

The separately inspected parent pre-relaxation Amber core contains **HIE287
(NE2–HE2)** in both chains. Its HID91 label concerns the repaired residue 91,
not His287. The conditional **ND1-H** reference used below therefore requires
explicit removal of inherited HE2 and new placement of HD1; it cannot be called
the inherited parent tautomer. The source geometry and all original H identities
remain unchanged. This new tautomer choice must be selected independently of
the exposed endpoint labels and audited in the common preparation.

| Inventory/state | H_a location | H_b location | Substrate Q | Linked carbamate Q | Pair Q |
|---|---|---|---:|---:|---:|
| Declared keto starting inventory | C3 | O3 | −4 | −1 | −5 |
| Proposed V2, initial enediolate | KCX OQ1 | O3 | −5 | 0 | −5 |
| Proposed V3, state-I relay endpoint | O2 | KCX OQ1 | −5 | 0 | −5 |

Thus V3 is constructed by **KCX returning H_a to O2, then taking H_b from
O3**. A direct H_b shift O3→O2 while H_a remains on KCX has the same final
unlabelled atom/formal-charge count but a different physical proton history;
it is not the declared primary relay. The reduced C14 coordinates identify
only their one movable H8 at O3 in Enolate 2 and O2 in Enolate 3; they cannot
authenticate the physical histories of both enzyme-bound protons.

For protonated KCX OQ1, an explicit neutral Lewis construction is
**CE–NZ(H)–CX(=OQ2)–OQ1(H)**. This entails declaring a single CX–OQ1 bond,
rather than copying native standalone FMT's C=O1 bond. Deprotonated KCX has
one carbamate O− and no carbamate O-H; its resonance-equivalent bond/charge
convention must be recorded. An OQ2-protonated alternative requires its own
selection and correspondence, not a preferred-response swap.

Proton transfer preserves total nuclei, formal pair charge and electron count:
with **N_e=ΣZ−Q**, keto-RuBP has ΣZ=156 and **160 electrons**, and either
enolate has ΣZ=155 and the **same 160 electrons**. KCX gains the proton's
nucleus and raises its formal charge from −1 to 0, leaving its electron count
unchanged. No electron has been removed by enolization. The complete paired
inventory has the same total H in keto/V2/V3; the four phosphate protons were
already outside the declared tetraanion, rather than lost differently between
views. A molecular-mechanics partial-charge sum is not this formal inventory.

The retained 2022 archive is a different spinach 8RUC model. Its state-I
86-atom region has **79 native PDB joins + seven boundary H**, a declared
charge **−2**, and no explicit spin card. Its native R/TS/P run in the
decarboxylation direction. The retained source bindings are the carbon archive
SHA `48e76a27e3cea2c49ab6a9685551ba311a898f357416f4f91b35fc28c4dcce8b`
and semantic inspection SHA
`f7d5989faba9a80a302910747caffe3ab3d3975d1f9d75a35621e67ac9dd0d10`.
The accepted primary manuscript, read locally for the relay, has SHA
`b374b8c4967bbb0afeb84e57a3f3946b5bc5725b80082ec355c2fdb10f0f7703`.
See the [retained carbon preparation](reactive-preparation-result.md) for
native member paths and unresolved source aliases.

Source chemical-role correspondences are carbon-region **C2/C3/O2/O3 =
QM atoms 53/54/59/60**, and **Mg=51**; in the C14 surrogate they are
**2/3/5/6**. These are role correspondences, not shared atom IDs or exact
geometry. The C14 molecules omit the full phosphate-bearing substrate and
alter their terminal groups; restoring omitted groups is a new construction.
The source local ASP260/HID286/KCX193 map to spinach D268/H294/KCX201 and
declared Rr D263/H287/KCX191 roles. Source D268 is outside the 86-atom QM
region. Adding Rr D263 to a new region prevents inheriting the source −2
charge, even before mutations are considered.

## A matched boundary candidate and its conditional inventories

A concrete minimal candidate for this restricted relay question places the
**complete substrate, Mg, linked K191 carbamate and entire side chains of
D193/E194/D263/H287** in QM. Cut each of the five protein **CA–CB** bonds
once and cap its QM-side CB with one link H, using the same placement/exclusion
rule for every recipe and proton view. Keep both LSUs, the second native
substrate/Mg site and the remaining protein in a consistently prepared
environment; admit mutation in both LSUs if the selected construct is the
homodimer mutant. Cross-chain contacts are retained in that environment.
This is a proposed common boundary, not an executed or frozen solver input.

For this exact cap choice, **if** D193/E194/D263 are each declared
carboxylate −1 and H287 is neutral ND1-H, the capped pieces are:

| Piece | Declared formula | Q |
|---|---|---:|
| V2 or V3 full enolate | C5H7O11P2 | −5 |
| Protonated K191 side chain and carbamate, including its CB cap | C5H11NO2 | 0 |
| Mg | Mg | +2 |
| Capped D193 | C2H3O2 | −1 |
| Capped E194 | C3H5O2 | −1 |
| Capped D263 | C2H3O2 | −1 |
| Capped neutral H287 | C4H6N2 | 0 |

These conditional inventories yield the following six-row denominator. Atom
counts include all chemical and five link H; nuclei/electrons are arithmetic
consequences of the declared formulas, not electronic-structure outcomes.

| Context | Total candidate QM formula | Atoms | Q | N_e |
|---|---|---:|---:|---:|
| Reference V2 | C21H35MgN3O19P2 | 81 | −6 | 382 |
| Reference V3 | C21H35MgN3O19P2 | 81 | −6 | 382 |
| D263N V2 | C21H37MgN4O18P2 | 83 | −5 | 382 |
| D263N V3 | C21H37MgN4O18P2 | 83 | −5 | 382 |
| H287N V2 | C19H34MgN2O20P2 | 78 | −6 | 370 |
| H287N V3 | C19H34MgN2O20P2 | 78 | −6 | 370 |

Actual Asp→Asn replaces a carboxylate with an amide: the capped D263 piece
changes **C2H3O2, −1 → C2H5NO, 0**, giving **ΔQ=+1** when included in QM.
Record whether native OD1 or OD2 defines the new amide oxygen, where the new
ND2 and its two H are built, and any rebuilt CG; neither orientation is
authenticated by a native mutant structure. H287N replaces an imidazole
side chain with that amide, removing/adding the actual atoms rather than
changing an imidazole charge. Its **ΔQ=0** only for the declared neutral-His
reference. A protonated-His reference would change that accounting and require
a separate roster. An unchanged per-context formal QM charge is therefore
not a consequence of using a common boundary. For mutations in both chains,
the other chain's actual changed inventory also belongs in the MM bookkeeping.

All three candidate electron counts are even, allowing a closed-shell
singlet hypothesis; this is a parity check, not a multiplicity witness or
proof of the ground state. Any changed cap, protonated acid, additional
residue or water requires rederiving every affected formula/Q/spin. Incoming
CO2 and O2 are not present in this preparation roster. A later reaction
protocol must add their own atoms and states consistently, including O2's
spin treatment; an energy difference between unlike stoichiometries is not
a branch barrier.

Before effectful QM, also freeze the protein truncation/reference sequence,
completion of omitted or zero-occupancy atoms, the water policy, amide
orientation, fixed/movable atoms, matched relaxation and metal treatment.
For every real QM atom, remove its MM counterpart; handle MM charges at each
cut by one declared rule, and prevent a cap from being mistaken for a native
environment atom. Retain charge accounting for both parts and their boundary.
Nearby lysines and cross-chain residues outside this minimal candidate are
explicit MM spectators, not automatically available proton-transfer pathways.
A region that requires their chemistry must expand all matched contexts.
The current fourteen-C/H/O electronic owner cannot admit this new P/N/Mg
region merely by attaching point charges; a separately admitted successor
contract and Hamiltonian are required.

## Independent falsifiers and first stops

1. Independently reconstruct the native-name/bond graph and check element
   valence, full substrate phosphates, linked NZ–CX, both source chains and
   all declared caps. Refuse double-counted FMT carbon H, missing carbamate O,
   unresolved amide orientation, lost required atoms or a mismatched source ID.
2. Recount each context's actual H/proton identities, ΣZ, Q and N_e from the
   resulting atom/bond inventory. Keto→V2→V3 must conserve paired nuclei and
   electrons; a removed electron or a fixed Q concealing D263N is a failed
   construction. Verify no molecule/QM atom is also present in the lattice.
3. Check the constructed enediolate geometry, bond lengths, proton distances
   and Mg contacts against declared admission bounds, retaining all refusals.
   Heavy-only source projections cannot pass an H/proton-state check. Changes
   that destroy activation/coordination or require an undeclared water or
   relay residue stop this roster before any response inference.
4. Apply identical label-free amide-placement and relaxation opportunities to
   all recipes. Preserve unresolved alternatives in a separately frozen
   sensitivity denominator; choosing an orientation or proton state from
   exposed turnover/specificity values invalidates this first contrast.
5. If a later native protocol is admitted, test reversible proton transfer,
   carbon progression and competing admission/commitment with matched
   stoichiometry and prefactors. Failure to distinguish D263's turnover-heavy
   response from H287's productive-processing/specificity response, loss of
   the sign under declared construction sensitivities, or a requirement for
   genotype-specific fitted prefactors falsifies the proposed narrow relation.
   Enolate electronic descriptors or a proton-state energy difference alone
   do not satisfy that assessment.

The unchanged user-supplied full H287 paper now supplies
[methods and 21 explicit WT/N/Q endpoint cells](h287-kinetic-panel.md), including
the censored enolization response, CKABP hydrolysis/decarboxylation ratios and
product-profile specificity with oxygen-side-product limitations. The
[source admission](h287-source-admission.md) preserves the earlier access
refusals separately. The paper has no standalone kinetic tables and supplies
no absolute mutant kcat, native uncertainty/raw curves or authenticated full
assay-parent sequence. The exposed native D263 panel, its own WT and metrology
remain separate. This inventory closes
neither phases 2–9 nor the assay-parent join, and supplies no nomination,
fresh evidence, mutant-rate forecast or EL-superiority result.
