# Rr coupled initial chemical inventory and geometry result v1

SPDX-License-Identifier: CC-BY-4.0

The **10 October 2026** retained construction completed and independently
verified all **six assigned chemical inventories**. All six are
**GEOMETRY_UNREADY** under the frozen initial geometry screen. The common
inherited substrate has a C2–C3 separation of **1.605930571351076 Å** and a
maximum local plane displacement of **1.2794033695745035 Å**, outside the
selected enolate bounds. There are **zero ready QM jobs**, native solver calls,
endpoint fits or task receipts. This is an explicit preparation result, with no
mutation-to-kinetics result, candidate nomination or phase completion.

The [initial geometry protocol](rr-coupled-initial-geometry-protocol-v1.md),
SHA-256 `00db4578dc01e1e4f53b978f332e54f04e1c80b27493d7c5e3e24266d7ebcb69`,
was frozen before the source conformance constructions. The
[assessment design](rr-coupled-assessment-design.md) keeps later chemical
observables, source-domain kinetic assessment and candidate-domain transport
separate. The earlier [three heavy-scaffold result](rr-scaffold-result-v1.md)
and its preserved refusal/recovery have their own immutable identities.

## Admitted sources and actual construction

The maintained
[constructor](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_coupled_preparation.py)
consumed seven exact source operands once: the retained legacy dry-core
projection, same-parent Asn donor templates, their closed source register,
native source facts and the three independently recovered heavy projections.
Those seven inputs contain **5,988,566 bytes**. The complete closed dry-core
source packet contains **44 files / 13,788,149 bytes**, register SHA-256
`a6deb1386faa51e39669208fecb79a68a859888f60c6fcfaf689cfbc8c1c3ec1`.
Its authoritative projection SHA-256 is
`bfbaa57a1b9d466e311c23c37616cd54771ac170d7fc361ef7769a4004040c5f`.
The full original nineteen-file Rr intake, **6,195,952 bytes**, also remains
bound and unchanged, including [9RUB](https://www.rcsb.org/structure/9RUB)
CIF/PDB and [P04718](https://www.uniprot.org/uniprotkb/P04718/entry) FASTA.

The inherited parent comprises **13,828 atoms**, **920 residues** and
**13,994 bonds**: 916 protein residues across author positions 2–459 in both
LSUs, two complete keto-RuBP ligands and two Mg atoms. It retains **7,028 native
heavy-atom correspondences**, eighteen historical modeled heavy atoms and
6,782 historical generated hydrogens. All source lexical coordinates and
partial-charge tokens survive in the retained input; generated coordinates
have explicit model origins. No water coordinate is admitted.

The deposited D91 versus reference H91 conflict remains visible. The selected
parent inherits the legacy computational HID91 reconstruction; it does not
establish a biochemical WT, His6 construct or exact assay-parent identity.
The original source register and recovered heavy projections remain unchanged.

Actual construction used the fixed three genotypes × two proton views roster.
Both LSUs receive each selected mutation; chain A is the selected active QM
site, while chain B retains its keto ligand. The donor census contains thirty
eligible Asn residues. The frozen rule selects A9 and B9, each with fourteen
atoms: eight inherited native heavy atoms and six historical generated H atoms.
A proper rotation transfers OD1, ND2, HD21 and HD22 from each same-chain donor.
The target backbone/CB/CG coordinates survive; assigning the old CG coordinate
to the new Asn recipe is explicitly modeled, rather than observed mutant
geometry. Removed terminal atoms and all new donor origins are enumerated.

For the unedited reference and D263N, each source His287 HE2 nucleus is
preserved under its physical ID and relocated/renamed HD1 onto ND1 using the
declared external bisector. H287N removes that source His side chain and
constructs the donor amide instead. The active substrate proton identities are
fixed: H_a is original HC3 (`amber:6901`), H_b is original HO3
(`amber:6900`). V2 transfers H_a to KCX OQ1 and leaves H_b on O3. V3 places
H_a on substrate O2 and transfers H_b to KCX OQ1. These are provisional
chemical-state assignments with conserved nuclei, not observed proton positions.

The candidate QM region includes the complete active ligand/Mg and five
side chains, with five explicit CA–CB cuts at KCX191, D193, E194, residue263
and residue287. Five modeled cap hydrogens replace those cut partners. Full
new connectivity, Lewis valence, formal integer charge, formula and electron
count are checked independently. Native Amber partial charges remain source
witnesses; they do not establish a new executable MM Hamiltonian or determine
the candidate formal quantum charge. A singlet is the selected hypothesis;
no electronic ground state is certified.

## Complete six-case result

Physical atom counts exclude caps; candidate QM counts include all five caps.
Every row has a complete physical/QM/environment partition, verified chemical
inventory and **zero severe changed nonbonded overlaps**.

| Assigned genotype | Proton view | Physical atoms | Candidate QM atoms | Environment atoms | Candidate formula | Formal QM charge | Electrons | Changed-atom contacts within 3 Å | Disposition |
|---|---|---:|---:|---:|---|---:|---:|---:|---|
| Unedited computational reference | V2 | 13,828 | 81 | 13,752 | C21H35MgN3O19P2 | −6 | 382 | 471 | GEOMETRY_UNREADY |
| Unedited computational reference | V3 | 13,828 | 81 | 13,752 | C21H35MgN3O19P2 | −6 | 382 | 480 | GEOMETRY_UNREADY |
| Both-LSU D263N | V2 | 13,832 | 83 | 13,754 | C21H37MgN4O18P2 | −5 | 382 | 809 | GEOMETRY_UNREADY |
| Both-LSU D263N | V3 | 13,832 | 83 | 13,754 | C21H37MgN4O18P2 | −5 | 382 | 818 | GEOMETRY_UNREADY |
| Both-LSU H287N | V2 | 13,822 | 78 | 13,749 | C19H34MgN2O20P2 | −6 | 370 | 413 | GEOMETRY_UNREADY |
| Both-LSU H287N | V3 | 13,822 | 78 | 13,749 | C19H34MgN2O20P2 | −6 | 370 | 422 | GEOMETRY_UNREADY |

The three completed new graphs contain respectively **13,994 / 13,998 /
13,986 bonds**, identical between proton views in each genotype. All six
substrate heavy geometries remain common. Their six trigonal angles lie within
the frozen 100–140° range, and the primary cis projected-dot witness is
positive (**0.7694696089356516 Å²**). The signed O2–C2–C3–O3 dihedral is
**55.513029796601494°**; no additional literature torsion tolerance is claimed.
The selected C2–C3 interval is 1.25–1.45 Å and maximum local plane displacement
is 0.20 Å. Each case retains both failed checks. These bounds are explicitly
heuristic preparation screens, rather than a source-calibrated kinetic model.

Contact checks use the completed new graph, excluding first/second bond
neighbors. Only each exact cap/its own omitted MM-CA pair is exempt from the
severe-overlap rule, in either pair order. The overall nearest QM/environment
distance, **0.38544772865730215 Å**, belongs to such an explicitly enumerated
cap/cut-partner pair; it is retained as a diagnostic. It is not an assertion
that every QM/environment pair is physically separated by a nonbonded cutoff.

## Retention, producing identities and independent recovery

The single selected actual packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-coupled-initial-geometry-v1`.
Its operational status is **COMPLETE**, independently verified inventories
**6/6**, geometric screen passes **0/6**, constructor exceptions **0/6** and
prepared QM jobs **0/6**. The complete retained denominator is **35 genuine
artifact publications / 176 physical files / 33,619,501 bytes**. It includes
all payloads, manifests, referenced commit markers and exact zero-byte control
lock files. The closed census SHA-256 is
`16e85c727a4244dbbc7a43d499cf59c14dc215d16bde8097202339ab73ba69f2`.

Before construction, **23 genuine publications** retained and authenticated
the protocol, producing module, caller/child/replay sources, complete producing
inventory, lock/pyproject, exact inputs, complete source packets and custody
provenance. The child admitted one source and entered/returned all six assigned
constructors. Its cold guard refused numerical/molecular solver families.
Parent production constructors and geometric/valence helpers were disabled.

The authentic full child stdout contains **18,513,329 bytes**, SHA-256
`78d963af5616e28f6e2d7acec9548d8f8a861827696a1051de74638c915a38a4`.
It is preserved with the empty original stderr in a **2,949,382-byte** ZIP,
SHA-256 `f95bfbe921139d8331c2c03bbf7b08be0c073c5b4da3adedc887bc550c4ee4a2`.
The six individual context products are bounded separately and exactly equal
the corresponding records in that authentic stream. No normalization replaces
the retained original stream.

| Producing or retained operand | SHA-256 |
|---|---|
| Maintained owner | `cb2c00a28f1d45193551e4f528a9cad6312528c0d510447493ea7ace5ed36f00` |
| Complete 2,367-member producing package | `5aad5fbc0fa7838a6a12bcd68b1e4d51ad94c25b5ba58784b8dcaf9cb196a7e8` |
| Exact dependency lock | `ea491f9e8789d6cd5a18d89908d16ef7db4ee3c9ed4729e32354bc713b135f24` |
| Frozen private caller, 28,702 bytes | `906702acc12eca16b755d1ab359ca5e26ffa831584b5f4a2b7fedb9510ec1d97` |
| Cold construction child, 7,981 bytes | `e973a0f5936acbb3d7200339ff096dffbb7e00556c8809bff943369cd78bc74b` |
| Authentic custody/replay wrapper, 13,193 bytes | `258e65e71c50453b1c2e9004b340e19351083db2e73a0fa990791f52c6a34a87` |
| Independent scientific replay, 28,726 bytes | `5195535e685d7ac12dc004c1fbe4868a625e0fbbadc738d24a6a0cadbdb2d0af` |
| Retained independent replay observation | `d94b85e38384c5d85c17e515563294b4f353212e241d5629590e5f3950ac37e7` |
| Measured summary | `6c70d2aba57fbf4ccb78e3578d0ff3880fe3ddbd0435d1b8501246813b2ee9ba` |

The producer was `recchain` at
`9c670a3127cb652f839e56463758226749b07c73`, with dirty attribution retained.
Complete source closure reuses the unchanged authenticated 2,393-member
electronic archive, the exact two later heavy-source modules and the new
coupled constructor. These external immutable ancestors remain required
dependencies; the selected packet does not claim to be self-contained.

The actual measured window charged the parent plus all waited child processes:
**40.602377 CPU seconds / 41.164095 wall seconds**, consisting of
**6.747261 parent CPU seconds + 33.855116 waited-child CPU seconds**.
The construction child took **24.437407 CPU seconds / 24.450013 wall seconds**;
the independent preclosure replay took **9.267245 / 9.275320 seconds**.
The frozen limits were **120 combined CPU seconds**, **16 MiB per retained
member** and **64 MiB for the complete selected packet**. All pass. Final
summary publication, manifest verification, census write, chmod and readback
remain an explicitly **untimed metadata tail**.

Independent replay authenticates the full source/ancestry/member census and
derives mutation frame transforms, unchanged source coordinates, conserved
proton IDs and attachments, complete new graph/caps, Lewis inventory,
formula/Q/electron arithmetic, geometry and every changed contact directly
from the retained source inputs. It does not use the producer's construction,
geometry or valence helpers as an oracle. After closure, `--verify-only` passed
again with those entry points disabled, reporting zero producer calls, native
contacts, SCF calls, endpoint fits or task receipts. The root agent independently
repeated that recovery and verified all 176 hashes/modes and all 35 genuine
publications. Those later interactive checks have no additional retained
timing claim.

The maintained constructor passed **17 focused tests**; the root independently
ran those plus twelve cold-import/discovery checks, **29 passed**. Ruff passed.
Prior exposed construction copies total **43**: one WIP diagnostic, two six-case
source conformance fixtures, six root conformance copies, one six-case
child/independent-helper integration and three six-case embedding fixtures.
The separate integration passed on its first attempt, with **31.479153 CPU /
31.444750 wall seconds** and no authentic artifact publications. The first
embedding fixture had one error-message expectation failure, followed by a
settled passing fixture and a passing guard selection; all remain software
exposure. Unknown earlier software costs are not assumed zero. None of these
copies makes the six retained constructions fresh biological evidence.

## Consequence for the next physical test

The result supplies exact modeled mutations, explicit proton/nucleus ledgers
and independently checked chemical inventories on a common source background.
It also rejects treating inherited keto-substrate coordinates as already
prepared enediolate geometry. A separately selected successor must provide a
common, auditable environment/Hamiltonian and controlled geometry repair,
then recheck the same geometry, inventory and contact obligations before an
electronic or reactive calculation. Neither relaxing the rejection thresholds
nor discarding failed cases is selected here. Subsequent preparation can fail;
its usefulness remains testable without requiring a previously validated
mutation-response map.

An exact biochemical-parent join, electronic-state assessment, coupled
carboxylation/oxygenation or productive-commitment response, independent
two-endpoint kinetic assessment and transport to a high-specificity red-algal
candidate remain open. This result supplies no kcat or Sc forecast, assay
qualification, nomination readiness, EL superiority or completion of phases
2–9.
