# Entry to a mutation-sensitive coupled-chemistry test

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026, Australia/Sydney**, on `recchain`. A small,
provisional **D263/H287 proton-relay and productive-commitment test** is a
plausible next research construction. The present operands support preparing
that test, without supplying its mutation-to-turnover/specificity relation.
This note changes no frozen result or protocol and reports no new molecular
calculation, fitted response, qualification, EL advantage or nomination.

## Source domains and required joins

The [actual carbon archive and FM23 preparation](reactive-preparation-result.md)
retain different chemical models. The 2022 carbon release declares spinach
8RUC, with a two-LSU environment and **zero SSUs**. Its state-I R/TS/P
geometries have **86 atoms: 79 atoms joined to native PDB coordinates and seven
boundary H**. Native R/TS/P run in the decarboxylation direction. The declared
formal quantum-region charge is **−2** in the retained AMBER/Molpro fields;
this is not the charge of the whole enzyme or embedding lattice. These fields
do not supply explicit spin cards. Product `M1`,
state-specific lattices and source aliases remain uncorrected original witnesses.
[Primary study](https://doi.org/10.1021/acscatal.2c01677),
[released inputs](https://zenodo.org/records/6791151).

The release's local **ASP260/HID286/KCX193** correspond to its declared spinach
**D268/His294/KCX201** roles. D268 is present in the full classical environment
but outside the 86-atom QM zone. In R. rubrum, the corresponding source roles
are **D263/H287/KCX191**; numbering offsets are not a universal sequence rule.
The acquired Liggins preparation is Form II L₂ with an N-terminal His₆ tag
encoded by pRrHis. There are no admitted native mutant structures or exact
pRrHis DNA/protein recipe joins. A spinach D268 calculation assessed against
R. rubrum D263 labels would be a declared background-transport test, rather
than a same-parent assessment.

[Rr 9RUB](https://www.rcsb.org/structure/9RUB) is deposited as an activated
RuBP complex; [2RUS](https://www.rcsb.org/structure/2RUS) is a RuBP-free
activation/coordination reference. Their original coordinates are now locally
available in the closed source packet at
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-rr-structures-v1`.
Its exact register is `rr-structures-register-v1.json`; its factual inspection
is `rr-structures-inspection-v1.json` in that directory.
The packet contains **19 files / 6,195,952 bytes**, including its register.
Register SHA-256 is
`5b0a34d9c23f8a69e39c1dad35beb5e4d5976da05151818c30e0612552cae4a5`;
inspection SHA-256 is
`36f8b24b74808d2a3c6c9a76c59df5e94265214722f7c01078204960eabfb644`.
All eighteen registered member hashes and the exact nineteen-file census were
checked for this update. Seven original requests returned HTTP 200. The packet
contains source correspondence and geometry only: **zero preparations, SCF
calls, endpoint fits, artifact-plane publications or registered task receipts**.
Earlier browser failures below remain historical observations; this separate
acquisition does not rewrite them.

Both deposited **466-residue cores** have **D91**, whereas the admitted
[P04718 reference](https://www.uniprot.org/uniprotkb/P04718/entry) has **H91**.
Both native CIFs call this a sequence `conflict`; neither establishes an
engineered H91D mutation or the exact kinetic parent. 2RUS's full **490-residue**
entity consists of that core and the **24-residue entirely unobserved** prefix
`TMITNSPDRWGYSAPHRTSRESPP`, author positions **−23 through 0**. This prefix is
not His₆. The N-terminal His₆ assay construct remains without an exact native
DNA/protein join. An initial modeled reference can retain deposited D91, or a
separately declared reconstruction can introduce reference H91; neither may
silently become an assay-matched WT.

The deposited author positions remain **K191/D263/H287** in both entries.
Their `label_seq_id` positions are **191/263/287** in 9RUB and **215/287/311**
in 2RUS. Bind the actual source correspondence, rather than applying a general
numbering offset.

9RUB contains two Mg atoms, two full **18-heavy-atom RuBP** ligands and a
**K191-NZ–FMT-C** covalent link in each chain. Each linked FMT supplies native
**C/O1/O2**, the CO₂ skeleton for constructing carbamylated lysine. Standalone
formate dictionary charges and bonds do not parameterize the linked carbamate.
There are **no deposited water atoms or hydrogens** in 9RUB. In contrast, 2RUS
has **714 water O atoms**, no RuBP and linked FOR groups containing **C/O/H1**
per chain. Its H1 is a native hydrogen, not a second oxygen; using it as a
complete carbamate requires an explicit new oxygen and a decision about H1.
Transferred 2RUS waters would be modeled additions to 9RUB, not native 9RUB
water witnesses. Deposited titles and contacts do not recertify activation.

The inspection retains all **7,044 / 7,447** coordinate atoms for 9RUB/2RUS;
2RUS's latter count includes two FOR H1 atoms. Missing residues, missing heavy
atoms and zero occupancy are distinct preparation issues. For example, 9RUB
has incomplete tails and A460 THR lacks CB/CG2/OG1; nine included atom rows
have zero occupancy. 2RUS has its unobserved prefix, additional missing core
segments and 42 zero-occupancy atom rows. The complete Mg-distance census
includes remote E194 side-chain and cross-chain N111 contacts, without imposing
an ideal coordination shell. 9RUB's primary structure report permits substrate
conformational ambiguity, but the retained atom records do not supply two
alternative coordinate sets. The acquired mutant paper also warns of
inactive-crystal coordination artifacts. These are explicit preparation and
applicability limits, not reasons to deny that the native coordinates exist.

### Why the reduced molecule is insufficient

The completed [electronic pilot](enolate-electronic-result-v2.md) uses four
**14-atom C4H7O3** molecules. Attaching a released carbon lattice to one of
these molecules does not preserve the intact **79-atom source QM scaffold**:
the full phosphate-bearing substrate, Mg, KCX, His and other explicit ligands,
plus seven boundary H, are not reconstructed by remote point charges. Some
reduced substrate atoms represent corresponding chemical roles, but their
approximate constructed geometry does not inherit the native source atom
mapping or coordinates. This would be a new reduced surrogate, requiring its
own mapping, exclusions and assessment; it cannot inherit the 86-atom state
identity or source electronic job.

Likewise, deleting ASP260/D263 charges is a charge-perturbation ablation,
rather than **D263N**. Asparagine replacement changes elements, hydrogens,
amide geometry, charge distribution and possible relaxation. Declare the two
carboxyl-oxygen/amide orientations, or preserve ambiguity; avoid choosing the
orientation that gives the preferred response. H287N also removes the
imidazole relay, rather than merely reducing its net charge.

The installed, locked PySCF 2.14.0 supplies `qmmm.add_mm_charges`/`mm_charge`
and embedded gradients. Its electrostatic energy excludes MM internal energy,
van der Waals and other bonded/nonbonded coupling terms. This is an available
operation for a declared successor, not a complete force field or automatic
mutant builder. The maintained electronic owner currently admits only fourteen
C/H/O atoms and has no enzyme-embedding/mutation contract.
[Official PySCF description](https://pyscf.org/user/qmmm.html).

### Concrete preparation reuse before new construction

The donor file below is not distributed; its revision and digest identify the historical source inspection.
The linked EL successor is available but has its own implementation and scope.
See the [legacy tooling availability note](rubisco-legacy-tooling-reuse-review.md#sources-inspected) before attempting donor-source reuse.

The legacy completion checkout already contains a useful reconstruction and
parameter-isolation algorithm; the six contexts need not start from six
independent preparation implementations. The
[migration source-head register](migration-manifest.json) binds completion
commit `aa9346547560abcb6500f2e97b53b96f456d9be3`. At that commit, the selected
source is
`src/icf_yolo/adapters/simulators/rubisco_m1_v6/preparation.py`,
**11,948 bytes**, SHA-256
`1dcad5beaae85ae24333ee8f67ade798fbecebbb57f656306671c6e035c596d0`.
The inspected file at
`/home/chevre/gs-ml/icf-yolo-rubisco-r02s-20260925` is byte-identical to that
committed source. Selective reuse now appears in the maintained
[native Rr heavy-scaffold owner](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_preparation.py),
with independent original-PDB checks and explicit current mutation records.
This is a heavy-coordinate projection; it does not port the old native Amber
execution or establish completed chemical states.

`reconstruct_coordinates` already pins **exactly the newly acquired 9RUB CIF
and P04718 FASTA bytes**:

| Operand | Pinned SHA-256 |
|---|---|
| 9RUB original CIF | `33242f8e519c2e032c5a83de33a6350eb5c38cef42b5a14e1f8ecfb9230575dd` |
| P04718 original FASTA | `d7edfcdad62964ce96ec766ca4bd83e115c19ee257585c9014f07b7d325e48d0` |

It identifies both native **LYS191-NZ–FMT-C** bonds, merges each linked FMT
into KCX using **C→CX/O1→OQ1/O2→OQ2**, and retains both paired RuBP/Mg
ligands. It selects the common author interval **2–459** in both chains:
**916 protein residues**, with the omitted tails explicitly outside that
approximation. Zero-occupancy atoms are omitted and audited; other non-unit
occupancies refuse. It declares reconstruction of native D91 as **HID91 or
HIE91**, and supports the old **M100T/D206E** recipes. At edited sites it
retains backbone and CB atoms; the later native Amber preparation supplies
missing heavy atoms and hydrogens. The coordinate function alone does not
deliver completed mutant geometry or build an OpenMM `Context`. Its reference
assertion does not establish the exact His₆ assay sequence.

`isolated_kcx_parameters` namespaces custom KCX atom types while retaining
ordinary Amber protein terms. It uses base types for peptide-boundary terms
and the released custom parameters for internal KCX terms, rejecting ordinary
protein overwrites. The published preparation is checked for **23 distinct
KCX atom names** and a charge sum within **0.00001 of −1**. Preserve that
source-specific molecular-mechanics charge balance and its parameter witnesses;
it is not a quantum-region charge or proof of a common Hamiltonian with an
explicit PySCF QM scaffold.

Adapt these bounded operations to the present exact source audit and canonical
identities. Replace M100T/D206E with actual **D263N/H287N** atom construction,
declare the D91/H91 choice and both-LSU mutation state, add the matched enolate
proton views, and use one common QM boundary/exclusion rule. Preserve the
truncation and every omitted or newly built atom as explicit approximations.
The legacy HID/HIE91 alternatives are separate reference-protonation choices;
they are not interchangeable with the new substrate-proton views. A declared
reference choice precedes the six contexts; additional reference alternatives
belong to a separately frozen sensitivity roster.

The parent's actual **WT-HID91 pre-relaxation core** now has a separate
[closed source projection and independent audit](rr-amber-core-source.md):
**44 read-only files / 13,788,149 bytes**, binding the original 42-member
historical ZIP and unchanged selected prmtop/inpcrd. Its dry core has
**13,828 atoms / 13,994 bonds**, with **7,028 exact inherited heavy atoms**
under translation **(+14.1641370, +43.3948653, +47.0584385 Å)** and eighteen
declared heavy-atom repairs/completions. All sixteen original atoms outside
that inherited join remain explicit. This supplies existing generated-H and
atom-completion geometry without rerunning Amber or the old MD protocol.
The large original archive/topology remain bound external sources; the compact
packet is not independently portable.

Both active-site His287 residues are native **HIE (NE2–HE2)** in that parent.
The proposed ND1-H reference therefore needs an explicit proton relocation,
distinct from the parent's HID91 repair. The complete source Asn census has
thirty candidates; its label-free lowest-author-position donors **A9/B9**
supply actual amide/H geometry for the
[initial six-context construction](rr-coupled-initial-geometry-protocol-v1.md).
That construction still must check the new full inventories and enediolate
geometry before any solver-ready claim.

Metadata-only inspection confirms the currently selected electronic environment
has **no Biopython, OpenMM, ParmEd or PDBFixer**. A later EL-owned locked
preparation profile can selectively reuse the legacy pins **OpenMM 8.3.1**,
**ParmEd 4.3.1** and PDBFixer Git revision
`199f03df6c50f7cf6120de766f4ccce426fda4e9`, with an explicitly selected
Biopython version. The inspected legacy lock pins Biopython **1.88**; this does
not install it or change the present profile. The legacy `pyproject.toml` and
`uv.lock` have SHA-256
`c23ddc2f4f20a7f5e41f3ecb44187133241b94916d43fde274c8395f01d87b6a`
and `3f223972439fa33fc844b8f1815b2432d69b350a7e294b3e5f7d5131626173d2`.
No sibling-checkout runtime import, old worker invocation, profile change or
wholesale molecular-version migration is selected by this documentary reuse.

## A discriminating source-domain hypothesis

The complete acquired D263 point panel is:

| Rr context | Reported turnover, s⁻¹ | Specificity |
|---|---:|---:|
| WT | 6.28 | 9.2 |
| D263E | 0.94 | 8.6 |
| D263N | 0.82 | 8.8 |
| D263Q | 0.20 | 9.3 |
| D263S | 0.46 | 10.1 |
| D263A | 0.81 | 9.2 |

These exposed means have no native table SD or replicate counts. Conditions
are **25 °C, pH 8, CABP active-site normalization**. Turnover is derived from
RuBP titration at approximately **835 µM CO₂**, while WT CO₂ K_M is **446 µM**;
retain this operational qualification. Specificity uses tritiated RuBP under
**5,000 ppm CO₂ in O₂**. The table's activation energies are transforms of
these turnover labels, not independent computed inputs.
[Liggins and Gready primary paper](https://doi.org/10.1021/bi802159e).

The user-supplied full H287 paper now supplies the
[complete native endpoint roster and methods](h287-kinetic-panel.md): H287N
carboxylation is **~0.05% of its own WT**, H287Q **<0.001%**; neither mutant
has detritiation significantly above the **~0.1%-WT detection limit**.
Product-profile specificity is **~11 / ~0.9 / estimated ~0.8** for WT/N/Q.
The isolated CKABP **hydrolysis/decarboxylation ratio** is **≥0.9 for WT /
≤0.1 for N**. These ratios are not measured first-pass commitment fractions.
The specificity estimate uses PGA/PGyc peaks and gas assumptions; additional
oxygenation-derived CTBP is outside that denominator. Abnormal enediol and
oxygenated-intermediate processing therefore require separate modeled roles.
Preserve its authentic Rr WT versus E. coli-produced mutant preparations,
**23 °C** general activity assays and A280 protein normalization; do not
combine them with the His₆/CABP-normalized **25 °C** D263 WT.

The [native source intake](h287-source-admission.md) preserves the earlier
eight-request failures and closes a separate **78-file / 5,169,130-byte**
unchanged user-PDF successor, with all nine pages inspected and 21 explicit
endpoint cells. There are no standalone numbered kinetic tables. Absolute
mutant kcat/Kₘ, native uncertainty/raw time courses and exact full assay-parent
sequence joins remain unavailable. CABP exchange half-lives **34/90/120 h**
are antagonist controls, not productive release or cycle-time fractions.
[Harpel et al. primary article](https://doi.org/10.1002/pro.5560070322).

A provisional two-role relation is:

```text
specificity = (carbon admission / oxygen admission) × (qC / qO)
qC, qO = productive-processing probabilities after their respective admission
```

Turnover additionally depends on productive and unsuccessful cycle times.
A shared reactive occupancy cancels from the admission ratio in the declared
common-state model. A strictly common-mode response therefore cannot explain
the H287 specificity collapse. WT carbon irreversibility cannot be imposed on
the decarboxylation-prone mutant. Neither statement requires a complete cycle
model before testing a narrower hypothesis.

## Small next preparation roster and first stops

The maintained cold construction now implements a **preparation-only six-context roster**:
**unedited reference / D263N / H287N × two declared enolate–KCX proton-placement
views**. Here “WT” means the unedited chosen computational reference, whose
assay identity remains unresolved. Build **one inherited 9RUB heavy-atom
scaffold**, with a label-free active-site chain choice and both-LSU environment,
then derive every context from it. Within each proton view use the same
substrate-state construction and placement rule across all three recipes.
Changing the protein, ligand state and solvent independently for each genotype
would confound this first contrast. Retain 2RUS as a separate sensitivity
witness, rather than quietly mixing its scaffold into selected contexts.

Before effectful QM, freeze the following preparation operands:

1. Authenticate the closed originals and exact atom/author/label maps. Choose
   deposited D91 or an explicitly modeled H91 reference, the chain-selection
   rule, and treatment of missing or zero-occupancy atoms. Preserve the
   unresolved His₆ assay join as an applicability limit. It does not prevent
   constructing a declared provisional reference.
2. Construct the **linked K191 carbamate** from its native LYS/FMT atom roles
   with explicit bonds, hydrogen placement and parameterization. Declare Mg
   coordination and protonation rather than importing standalone FMT charges.
   Preserve native distances and flag any modeled correction or added ligand.
3. Preserve full substrate phosphates and the common protein/metal scaffold.
   Define both enolate proton views with exact atoms, transferred-proton
   identities, element/bond changes and per-context proton/electron inventories.
   They are new preparations, not deposited enolate states. Freeze the water
   policy: 9RUB supplies none, and any new or transferred waters need declared
   identities, placement rules and sources.
4. Build actual **Asp→Asn** and **His→Asn** side chains, recording retained,
   removed and added atoms. Freeze amide orientation and any bounded local
   geometry construction without inspecting kinetic responses. Declare whether
   both LSU copies carry the encoded edit; a mixed dimer cannot silently stand
   in for the assayed mutant. H287N has no histidine protonation state; any
   alternative amide-, water- or KCX-mediated relay must be constructed openly.
5. Select one consistent QM region and boundary rule, including the reacting
   substrate, Mg, carbamate and relevant relay atoms. Record both-LSU contacts,
   boundary H, fixed/movable atoms, embedding exclusions and mutually exclusive
   QM/MM membership. Refuse duplicate QM atoms in the lattice and unresolved
   essential atom correspondence. Freeze per-context formal quantum-region
   charge and spin from the declared chemical inventory; no source charge is
   automatically inherited by a different fragment or mutation.
6. Retain exact source/preparation identities, the complete six-context
   roster, geometric/admission checks and failed or ambiguous contexts before
   selecting a solver or requesting energetics. Freeze sequence-conflict,
   proton, carbamate, water and boundary assumptions before that execution.

An unresolved essential choice remains unevaluable in this roster. A separately
frozen sensitivity successor may enumerate alternatives without changing the
successful denominator. No rotamer, protonation, force field or relaxation is
selected from endpoint labels. These computational preparation requirements do
not require new laboratory synthesis before a computational submission.

The [maintained constructor](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_coupled_preparation.py)
and seventeen focused tests implement these explicit Asn/proton/cap inventories.
Root's combined focused and architecture/discovery run passes **29 checks in
43.14 s**. Independent review confirms all seven exact source operands,
native joins, proton identities and the unordered own-CA/cap exemption. The
six exposed software copies all pass inventory and retain zero severe changed-atom
overlaps, while the common substrate geometry remains **GEOMETRY_UNREADY**.
The separate [retained six-context result](rr-coupled-initial-geometry-result-v1.md)
now verifies all six inventories by independent source-derived replay. Every
case retains both C2–C3 and planarity failures; none is a ready QM job. Its
35 genuine publications retain 176 files / 33,619,501 bytes, and root recovery
passes with zero producer calls. The software copies retain their prior
exposure and do not become fresh biological units.

The [maintained embedding owner](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_coupled_embedding.py)
now derives complete source-charge fields from those sealed contexts. Its
spectator-residue donor assignments and five exact CA redistributions conserve
the selected source charges while retaining a common approximately −0.50709849 e
hybrid-versus-nominal whole-core offset. Eight focused and twelve architecture/
discovery checks pass, with an independent original-token audit. This is field
derivation, without a selected native Hamiltonian or native field evaluation.
The [embedding design](rr-coupled-embedding-design.md), [native feasibility
audit](rr-coupled-relaxation-feasibility.md) and [prospective repair
design](rr-coupled-relaxation-design.md) keep the next bounded geometry repair
separate from kinetic inference.

This first roster checks whether a coupled realization is constructible. It
does not yet forecast both endpoints. The subsequent native protocol must name
**productive-progression** and **relative admission/commitment** observables,
matched forward/reverse states, prefactors, spin/standard-state assumptions,
limited relaxation and resource caps before execution. A proton-state energy
difference is not a free-energy barrier or measured state occupancy. A carbon
addition barrier alone is not turnover. The source's reaction templates may
inform these new preparations without forcing unlike fragments into one ratio.

Meaningful falsifiers are failure to retain activation/coordination, unstable
signs across declared preparations, failure to distinguish D263's turnover-heavy
response from H287's processing/specificity response, or reliance on fitted
genotype-specific prefactors. Assessment must use the admitted
[H287 methods and censored native roster](h287-kinetic-panel.md) and complete
native D263 roster, preserving absent absolute mutant rates. Retain censored H287
outcomes, source-specific WT anchors, endpoint errors and joint directions;
neither endpoint compensates for the other. No new numerical success tolerance
is selected from exposed outcomes here.

Conventional controls receive the same structures, solver and construction
opportunities: parent/no-change, common-occupancy-only, irreversible commitment,
charge-only versus actual side-chain replacement, and fixed versus consistently
relaxed chemistry. A competent conventional repair remains eligible. Successful
Rr assessment would supply a narrow source-domain component; SSU-containing
G. partita and I95M transport remain separate, unassessed research questions.

## Subordinate analytical feasibility map

The [selected paired-branch sensitivity protocol v3](branch-sensitivity-protocol-v3.md)
uses the exposed C2 weights and vertical ionization shifts to calculate a
conditional Marcus surface and serial-cycle bound. Its **four descriptor pairs,
96 branch points, twelve boundaries and sixteen turnover points** preserve
both favourable and unfavourable consequences. Unknown matched-environment
driving energy, reorganization energy, correction/coupling and productive-time
fraction remain unknown. Its 60-CPU-second/4-MiB analytical caps are specific
to that arithmetic, not a coupled-QM budget. A favourable parameter point
does not supply a mutation effect or qualify this entry hypothesis. The map
can state which operands would discriminate the proposed mechanism; it cannot
replace their construction and assessment. V3 preserves the earlier protocols
and their pre-analysis custody refusals. Its
[completed analytical result](branch-sensitivity-result-v3.md) retains the full
roster and opposite specificity directions for every descriptor pair. The
enzyme consequence remains **UNIDENTIFIED**, with no phase closure.

## Read-only audit requests and access limits

The following is the **original documentary browser audit on 10 October 2026**.
Those browser requests produced no new retained original-source packet,
archive publication or task receipt. The later, separately closed Rr native
intake above supplies current coordinate availability and preserves its own
acquisition log; it does not convert these original failures into successes.
Local inspection for the original audit read the acquired Liggins PDF/text and
mechanism inspection, the closed carbon semantic inspection, maintained
source/results and installed PySCF `qmmm/itrf.py`. No source was edited, fit
performed, SCF entered or MD run.

| Exact browser URL requested | Observed access role/result |
|---|---|
| `https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/` | Indexed primary abstract; direct open returned browser check |
| `https://www.rcsb.org/structure/9RUB` | Primary deposition/structure summary read |
| `https://www.rcsb.org/structure/2RUS` | Primary deposition/structure summary read |
| `https://europepmc.org/articles/PMC2143942` | Browser-tool access error |
| `https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/?pdf=1` | Browser-tool access error |
| `https://pubmed.ncbi.nlm.nih.gov/9541405/` | Primary abstract and bibliography read |
| `https://research-information.bris.ac.uk/ws/files/339252396/Rubisco_carboxylation_reference.pdf` | Accepted manuscript read; His294/protonation/irreversibility text inspected |
| `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2143942/fullTextXML` | Browser-tool access error |
| `https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/pdf/ps0070730.pdf` | Unverified filename probe; access error, no PDF admitted |
| `https://onlinelibrary.wiley.com/doi/10.1002/pro.5560070322` | Abstract/references; publisher reports unavailable hosted full text |
| `https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/pdf/` | Browser-tool access error |
| `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2143942/` | Browser-tool access error |
| `https://onlinelibrary.wiley.com/doi/pdf/10.1002/pro.5560070322` | Actual publisher PDF link clicked; cache-miss refusal |
| `https://pubmed.ncbi.nlm.nih.gov/19231887/` | Final direct open returned browser check; acquired original remains the D263 witness |
| `https://pyscf.org/user/qmmm.html` | Official embedding/gradient description read |

Exact search queries, in request order:

```text
Rubisco H287 mutation Rhodospirillum rubrum specificity histidine 294 mutant carboxylase oxygenase
Rubisco histidine 294 mutation H294N specificity protonation Douglas Gallardo 2022
Liggins Gready 2009 D263 Rubisco computational prediction D268 mutant QM MM
"H287N" "specificity" "Table" "Harpel"
"H287Q" "0.6" "specificity"
"Multiple catalytic roles" "Table 1" histidine
"His 287" "H287N" "specificities" rubrum original
"Multiple catalytic roles of His 287" PDF OR pmc OR fulltext
"H287N" "decarboxylation" rates
```

The literal `0.6` was a search token, **not a verified kinetic value**.
Off-topic and secondary results supplied no scientific operand in that original
audit. Full H287 methods were then unverified; publication/index links and
failed filename probes did not supply their bytes or quantities. The separate
[user-PDF source successor](h287-source-admission.md) above now admits those
methods and native endpoints without changing the historical audit outcome.
