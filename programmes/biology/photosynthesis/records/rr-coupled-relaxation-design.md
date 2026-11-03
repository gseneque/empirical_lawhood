# Prospective matched Rr electrostatic coordinate repair

SPDX-License-Identifier: CC-BY-4.0

State: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

This **10 October 2026** design proposes the smallest useful native successor
to the [initial six-context construction](rr-coupled-initial-geometry-protocol-v1.md).
It is **not a selected or frozen execution protocol**. Its numerical proposals
remain reviewable before an explicitly selected successor captures their exact
bytes. No native imports, SCF, gradients, optimization, new source preparation
or installation were performed for this note. Authenticate and close the actual
initial construction before choosing its successor; the exposed software copies
are conformance results, not its retained scientific disposition. The actual
initial construction has now returned all six full inventories and
**GEOMETRY_UNREADY** for every case: common C2–C3 length and local-plane failures,
with zero severe overlaps. Independent source-derived replay checks their
inventories and complete contact denominators; this supplies the reason for
repair, not mutant discrimination.

The immediate question is whether a matched constrained electrostatic model can
repair inherited keto coordinates while retaining the declared enolate inventory
and physical proton identities. Repair success supplies an input for the next
reaction test. It supplies neither a reaction barrier, V2/V3 equilibrium, mutant
rate, productive commitment nor an EL advantage. The
[assessment design](rr-coupled-assessment-design.md) specifies the subsequent
scientific inference rules.

## Inputs, roster and owner

Keep exactly **six assigned cases**, in this order: unedited computational
reference V2/V3, both-LSU D263N V2/V3, both-LSU H287N V2/V3. Each has the same
active chain A, five CA–CB cuts and full substrate/Mg/KCX191/D193/E194/D263/H287
chemical-role boundary. The [inventory](rr-coupled-chemical-inventory.md) gives
**81/83/78 QM atoms**, **Q −6/−5/−6**, and **382/382/370 electrons** for the
reference/D263N/H287N recipes. Select restricted singlets as hypotheses, not
certified electronic ground states. Keep inherited modeled H91, dry native
structure, both protein mutations and chain-B keto substrate/Mg explicit.

Consume the closed initial case bytes and source bindings; do not rerun the
parent Amber preparation, replace coordinates with `relaxed.npy`, repair the
old source packet or call the frozen fourteen-atom electronic owner with an
expanded interpretation. A **new cold native adapter owner** must admit this
inventory, exact field, fixed/free mapping, constraints and numerical selection.
Reuse PySCF, SciPy and the existing source/custody contracts. No new general
geometry framework, ASH installation or moving-boundary force assembly is needed.
The proposal adds no CO2, O2, water, alternative amide rotamer or extra genotype.

Retain the complete assigned denominator even if source admission, controls,
SCF, constraints, geometry or resources fail. Failed cases are not replaced by
another proton view, guess, rotamer, solver or smaller region. Completed earlier
outputs survive a later case refusal. A successor may change a declared model
or budget deliberately; its identity and evidence are distinct.

## Explicit fixed source-charge field

Use the prospective source-charge policy reviewed against the
[closed original parent core](rr-amber-core-source.md):

- Remove every real QM atom from the MM field. Caps are new QM atoms and are
  absent from MM. The source exclusion contains **76 original parent atoms**;
  physical mutation/proton changes then determine the current actual census.
- Keep the active-A retained backbone charges as parent witnesses at all five
  cuts. Do not assign an ASN or HID whole-residue charge to an active backbone
  while its side chain is already described by the capped QM model.
- For a changed spectator-chain B residue, assign the **whole matched residue**
  by same-chain donor name/element: fourteen-atom ASN9 for B263N/B287N and
  seventeen-atom HID91 for B287 in reference/D263N. This includes N/C/CA/HA,
  target CG and the transferred HD1 proton; inheriting HIE HE2 charge on HD1 is
  not the HID assignment. The donor selection consumes no assay labels.
- Set each of the five active-A CA charges to zero and split its original
  charge **equally among its own N/C/HA**. Keep the zero-charge CA rows in
  environment membership. Preserve exact rational totals from original Amber
  scaled tokens divided by **18.2223**, separately recording Decimal/binary
  conversion residuals. This conserves charge exactly but changes the boundary
  dipole; it is a declared electrostatic approximation.

The full environment contains **13,752 / 13,754 / 13,749 atoms** for the three
recipes, including the five zero-charge CAs, and is identical between V2/V3
within a recipe. Its approximate total charges are
**−24.5070984848674 / −23.5070984821236 / −24.5070984821236 e**.
Adding capped QM formal Q yields a hybrid-minus-nominal-whole-core offset of
approximately **−0.50709849 e** for every recipe. The nominal whole-core charges
are **−30 / −28 / −30**, including both D263N substitutions. Preserve the
approximately +2 e D263N contrast and neutral H287N contrast, as well as native
token rounding. **Do not distribute a compensating charge globally or force
the hybrid total to an integer.** Formal QM charge, native partial charge and
the hybrid sum are different quantities.

Freeze all environment coordinates and charges. The primary proposal uses the
complete dry field and **point charges**, with no distance cutoff, Gaussian
radii, dielectric scaling, charge clipping or response-dependent exclusions.
Zero-charge rows can be omitted from native integrals only by a recorded exact
zero filter; the full scientific membership remains present. Record the nearest
QM/environment and nearest QM/**nonzero-charge** separation independently.
The five own-CA/cap geometric exemptions do not exempt any other MM interaction.
Any nonfinite field or coincident nonzero-charge/QM nucleus refuses native use.

PySCF's selected energy then contains QM electronic/nuclear energy plus
electrostatic QM–MM coupling. It excludes MM self-energy, van der Waals and
other bonded/nonbonded QM–MM terms. This is a **constrained electrostatic
coordinate repair**, not a complete enzyme Hamiltonian or transferable
whole-enzyme energy. In particular, missing repulsion can make an apparently
favorable contact unphysical. Preserve short contacts and large forces rather
than interpreting them as catalysis.

## Common mobile chemical roles and honest proton escape

The following is a concrete primary mobile rule, to be inspected against the
actual initial six before protocol selection. Derive IDs from authenticated
chemical roles, never from observed genotype activity or favorable gradients.

| Role | Proposed treatment in every applicable case |
|---|---|
| Complete MM environment, including all of chain B | Fixed coordinates and field. |
| Mg, five QM-side CB anchors, their attached H, five link H | Fixed coordinates; the boundary never moves. |
| Substrate P1/P2, O1P/O2P/O3P/O4P/O5P/O6P, bridging O1/O5 | Fixed phosphate anchors; remain in QM. |
| Substrate C1–C5, O2/O3/O4 and their remaining physical H | Mobile, including the currently attached H_a/H_b. |
| Each of the five side chains beyond CB | Mobile heavy atoms and their H under the same rule: KCX tail/carbamate, D193/E194 carboxylates, D263/ASN263 and HID287/ASN287. |

Every QM atom must occur exactly once in fixed or free coordinates, and no MM
atom may enter the optimizer. Fixing atoms means excluding their coordinates
from the optimization variable vector, not discarding their gradient rows with
`atmlst`. Reconstruct a full QM geometry at every call and retain complete
analytic gradients; fixed-atom forces remain diagnostics. Preserve fixed
source coordinates exactly in the declared adapter geometry. Native text
serialization must be checked independently within a preselected **1e−10 Å**
fixed-coordinate tolerance, retaining raw output; it does not prove identical
source lexical tokens. No derivative through link-H placement or
classical boundary motion is selected.

The preferred first test selects **no proton-distance restraint, artificial
bond-length potential, planarity restraint or force toward an enolate answer**.
Exact fixing of the declared boundary/anchors is its only coordinate constraint.
This allows an adverse response: the declared V2/V3 proton arrangement may
escape or collapse into another arrangement under the selected model.

Keep H_a/H_b and His287-H as the same physical IDs in every raw trajectory.
Proposed final admission diagnostics are O-H/N-H distance **0.85–1.15 Å** and
the assigned O/N being the nearest chemically eligible acceptor by **0.10 Å**.
V2 requires H_a→KCX OQ1 and H_b→O3; V3 requires H_a→O2 and H_b→KCX OQ1.
Do not add a restraint after seeing an escaped proton, swap proton names or
silently recertify the original Lewis graph. Record **PROTON_STATE_ESCAPED** or
ambiguous assignment, retaining actual coordinates and all physical identities.
It challenges this local model/state preparation, not enzyme existence or an
elementary catalytic rate.

Retain complete final new-graph contacts, with **<0.70 Å** nonbonded overlaps,
one-/two-bond exclusions and the exact unordered own-CA/link-H exemption. Inspect
all mobile atoms against all current QM/environment atoms; an initial 3 Å list
is insufficient after movement. Proposed final geometric qualification also
requires each mobile atom to remain within **0.75 Å** of its initial position,
the substrate C4 stereochemical sign to persist and nonreactive covalent lengths
to remain within **0.75–1.25 times** their initial declared length. Exempt the
explicit reactive bonds **C2–C3, C2–O2 and C3–O3** from that latter diagnostic.
These are transparent heuristic screens, not added energies or a van der Waals
model. Do not impose the desired C2=C3 length, planarity or energy ordering.
Record drift or connectivity failure instead of returning a qualified repair.

If fixed-anchor repair alone fails, a proton-well-constrained successor may
answer a narrower question. Its exact inequalities/Jacobians, starting
feasibility and active-bound/KKT residuals would need separate selection before
execution. A constrained geometry must not be substituted for success of the
unrestrained-proton test or called an unconstrained local well.

## Cheaper native alternative and adversarial method comparison

The first method choice should account for geometry repair cost. Official xTB
documentation supports external electrostatics for GFN1/GFN2, and its
fixed-atom/native optimization operations can reuse the same mobile-role map.
The proposed cheaper primary is **GFN2-xTB 6.7.1**, the stable release listed
when checked on 10 October 2026, rather than the automated bleeding-edge build.
No xTB binary has been admitted to the selected EL profile here. A prospective
isolated native profile must bind the exact official Linux asset, executable,
shared libraries, parameter bytes and selected invocation; do not alter the
main `uv.lock` or borrow an unspecified parent executable.
[Official stable release](https://github.com/grimme-lab/xtb/releases/tag/v6.7.1).

The tagged GFN2 parameter file includes both **Mg (Z12)** and **P (Z15)**,
as well as H/C/N/O. Element availability does not validate this Mg/enolate
active site. GFN2 treats a valence-electron model: the present formulas/Q imply
**266/266/258 valence electrons**, not the **382/382/370 all-electron inventory**.
Retain both ledgers explicitly, with the same molecular Q and declared zero
unpaired electrons; never rewrite the physical inventory to match a native
valence-electron counter.
[Pinned v6.7.1 parameters](https://raw.githubusercontent.com/grimme-lab/xtb/v6.7.1/param_gfn2-xtb.txt).

xTB's external-field interaction is **damped Coulomb**, not PySCF's point-charge
operator. For the closest declared comparison use native PCEM input in **Bohr**
with exactly the selected charges and **99** as the fifth-column hardness on
every nonzero row, which the documentation describes as point-like behavior.
This is still an approximation, not mathematical equality to a singular point
field. Default element-dependent hardness would be a different embedding
model; do not silently substitute it or interpret a repair difference as
solely a DFT versus tight-binding effect. Retain the entire scientific field
census, exact zero-filter projection, input row count and native-reported row
count/sum. The actual 13k-row field remains untested; there is no claim of
capacity or convergence from the small published example.
[Official embedding semantics](https://xtb-docs.readthedocs.io/en/latest/pcem.html).

Use the native **ANCopt** exact-fixing path with the declared fixed IDs, no
proton restraint, no solvent model, no automatic GFN0 preoptimization and no
retry. A proposed primary invocation selects GFN2, Q −6/−5/−6, zero unpaired
electrons, **300 K electronic smearing**, accuracy **0.05**, at most **250 SCC
iterations** per solve and a requested **60-cycle** global threshold at the
documented `vtight` level. Pinned ANC source checks that threshold only after
microcycle batches: default microcycle20 grows to at most40, so actual optimizer
calls can overshoot, with conservative bound99. CLI initial/driver final calls
and a separate unmasked final gradient give a source bound102, within a proposed
hard120 objective-evaluation reservation. Do not call sixty a strict actual
evaluation cap. Smearing is a numerical electronic choice, not enzyme assay
temperature or a thermodynamic population. Confirm all realized settings and
exact fixed atom indices from output. Native convergence flags, finite final
energy/full gradient and independently unchanged fixed coordinates are
required; a saved `xtbopt.xyz` or zero exit code alone does not admit a state.
[Tagged invocation options](https://raw.githubusercontent.com/grimme-lab/xtb/v6.7.1/man/xtb.1.adoc),
[native optimization](https://xtb-docs.readthedocs.io/en/latest/optimization.html),
[exact fixing](https://xtb-docs.readthedocs.io/en/latest/xcontrol.html#exact-fixing).

Native exact fixing masks fixed-atom gradient entries. At the final unchanged
coordinates, require a separate **gradient-only** calculation with the same
Hamiltonian/field and without the fixing mask, within the same case budget.
It supplies the complete force diagnostic and independently checks the free
stationarity residual; it performs no additional optimization. Do not label
the masked fixed zeros as vanishing physical forces. Retain native atom order
and independently map all gradients back to the physical source/cap IDs.

If using the Python API instead, absence of an exception **does not certify
SCC convergence**; the official API documents this explicitly. The CLI is
preferred initially because it retains full native convergence/fixing evidence
without adding a Python package to the main profile. A native parser must
preserve all failures and distinguish SCC from optimizer convergence.
[Official API warning](https://xtb-python.readthedocs.io/en/latest/general-api.html#xtb.interface.Calculator.set_max_iterations).

| Choice for the same six chemical cases | Value for this limited task | Adversarial limitation |
|---|---|---|
| GFN2, point-like PCEM, native exact fixing | Small valence space and existing optimizer; potentially affordable complete repair/escape test. | Parameterized charges/metal chemistry, damped field and proton wells may be wrong; speed and native convergence do not validate chemistry. |
| WB97X / def2-SVP with DF J/K | Reuses the earlier functional/basis family; more explicit electronic model with locally supported analytic gradients. | 798–841 AOs and substantial DF scratch remain; a non-diffuse basis can mask electron leakage for Q −5/−6. Use for geometry only, not anionic energy/barrier certification. |
| WB97X / def2-SVPD with DF J/K | Diffuse electronic check of a later admitted geometry. | 1,221–1,279 AOs and large tensors may be unaffordable; diffuse functions do not by themselves establish confinement or a physical ground state. |

Recommendation: select the **complete six-case GFN2 repair/escape test first**,
after its controls, as the cheaper finite construction question. Keep the
reduced DF method as a declared strong scientific comparator rather than an
automatic favorable fallback. If both arms are selected together, the
denominator is **six chemical cases × two methods = twelve method outcomes**;
give each arm all six, common mobile/fixed roles, common final diagnostics and
its predeclared equal-within-arm allowance. Different native optimizers and
embedding operators remain explicit confounders; this comparison cannot
isolate a functional effect or create an EL superiority claim.

Compare proton survival/escape, fixed-coordinate preservation, C2–C3 length,
angles/planarity, contacts, connectivity, mobile displacement and native cost,
with a complete six-by-method table. Report geometries in the unchanged source
frame and compare their actual mobile coordinates. Do not compare absolute
energies across methods or select the lower-energy method's genotype ordering.
Agreement supports a model-robust preparation direction only; disagreement or
V2/V3 collapse is useful negative evidence. A DF resource refusal is no
chemical agreement/disagreement. A later diffuse/stability check must again
be matched and bounded; it is not implicit in successful GFN2 geometry.

## Prospective DF settings and source feasibility

Use the already selected locked environment without synchronization:
PySCF **2.14.0**, SciPy **1.17.1**, NumPy **2.4.6**. The proposal extends the
previous WB97X/def2-SVP pilot to the full H/C/N/O/P/Mg region with **spherical
def2-SVP for a reduced-cost geometry comparator**, or **def2-SVPD for a
separately selected diffuse check**. Each is a common method choice captured
before its first call, not proof of electron confinement. Neither method may
change its selected basis after a refusal or favorable result.

Use **J and K density fitting**, `only_dfj=False`, with explicitly named
**def2-SVP-JKFIT**. The installed basis alias resolves to the retained
`def2-universal-jkfit.dat`. Compose density fitting **before**
`qmmm.add_mm_charges`, then obtain its analytic-gradient scanner. The installed
DF RKS implementation explicitly includes range-separated exchange and
auxiliary-basis response. Freeze **auxbasis_response=True** and
**grid_response=True**; verify those flags and the realized method class on
the small native control before using the enzyme cases. Supporting local
source code is evidence of capability, not a completed numerical check.

Proposed common settings are grid level **4** with explicit retained pruning,
radial/angular grid identities, energy convergence **1e−10 Hartree**, orbital
gradient convergence **1e−6**, and at most **120 SCF cycles** per evaluation.
Use one recorded deterministic initial guess per case, independent of other
cases; allow preceding density reuse **within that case only**. Record actual
grid points, overlap conditioning, frontier orbital energies, occupation,
SCF history and nonfinite values. Nonconvergence refuses that objective call;
the scanner otherwise returns gradients even when SCF is unconverged. No
favorable retry, altered damping, state following or checkpoint transfer from
a different recipe is selected.

For the exact-fixed, otherwise mobile DF comparator use maintained SciPy
**BFGS**, analytic objective gradients and explicit fixed/free reconstruction.
The optional inequality-constrained successor would instead use SLSQP and
independently verified constraint Jacobians. Use **Bohr coordinates and
Hartree/Bohr gradients** throughout the native/optimizer boundary. If presenting
an Angstrom derivative, divide the Bohr gradient by `lib.param.BOHR`; energy is
not converted. Proposed final DF tolerance is maximum free Cartesian gradient
**3e−4 Hartree/Bohr**. Retain the complete vector and an independent norm
calculation; optimizer success alone is not admission. A selected constrained
successor must separately record constraint violations, multiplier convention
and projected/KKT residuals. The final state must also pass the unchanged
initial enolate screens and complete contacts/inventory/proton checks.

Density fitting avoids repeated direct four-center exchange but has substantial
storage costs. A stdlib count of local contracted spherical basis headers gives:

| Recipe | def2-SVP AO count | def2-SVPD AO count | JKFIT auxiliary count | One packed diffuse three-center float64 tensor |
|---|---:|---:|---:|---:|
| Reference | 831 | 1,266 | 4,267 | 25.50 GiB |
| D263N | 841 | 1,279 | 4,303 | 26.24 GiB |
| H287N | 798 | 1,221 | 4,099 | 22.78 GiB |

These are **source-header size estimates**, not native molecule builds, peak
measurements or runtime predictions. Range-separated exchange can require
additional tensors; gradients, grids and workspaces add cost. Do not describe
DF as an in-memory lightweight calculation or silently fall back to direct
exchange after a storage refusal. Retain realized AO/auxiliary dimensions and
all scratch growth when an actual successor admits native use.

## Minimum native controls before the six cases

Every selected method must pass its own independent embedded gradient/unit,
common-translation and fixed-coordinate controls. For the GFN2 primary, reuse
the H2 control below with the same PCEM hardness and SCC selection, substituting
native GFN2 energies/gradients for DF results and omitting the DF/direct item.
Use the native fixed-atom optimizer for the fixed-coordinate item, at most eight
cycles, retaining every SCC solve visible in native output. Also require one
finite converged H2 single point with **the complete source field** at a
deterministically chosen location at least 10 Å outside its bounding box;
confirm all input rows and their charge sum survive native admission. That
capacity control checks field ingestion, not the active site's electronic
behavior. Count its extra native call and retain a capacity refusal. Use the
same derivative/translation tolerances as proposed below unless a distinct
common GFN2 tolerance is selected before the first call.

Reuse the parent central-finite-difference and BOHR conversion checks described
in the [feasibility note](rr-coupled-relaxation-feasibility.md), rather than
installing ASH or copying its known auxiliary-dipole force defect. A proposed
finite control uses neutral singlet **H2**, separation **0.74 Å**, with point
charges **+0.1 e at (3,0,0) Å** and **−0.1 e at (−3,1,0) Å**, and the same
functional, orbital/auxiliary basis, grid response and embedding composition.
The asymmetric field prevents a trivial zero-gradient check.

1. Obtain one converged DF energy/full gradient. For three declared Cartesian
   components spanning x/y/z and both H atoms, compare independent energy
   central differences at **h=1e−3 and 2e−3 Bohr**. This is twelve displaced
   energy evaluations. Proposed derivative agreement is
   `max(2e−5, 1e−3*abs(analytic)) Hartree/Bohr`; the two finite differences
   must also agree within **2e−5 Hartree/Bohr**. Verify the equivalent Angstrom
   derivative using division by BOHR, without deriving both sides from the
   same conversion function.
2. Translate **both** H2 and the field by **(1.25, −0.50, 0.75) Å**. Compare
   energy within **1e−8 Hartree** and complete gradients within
   **2e−6 Hartree/Bohr**. Translating QM alone changes the model and is not
   this invariance control.
3. Obtain one converged **direct-J/K** energy/full gradient for the same tiny
   baseline. Proposed DF/direct bounds are **1e−4 Hartree** and
   **3e−4 Hartree/Bohr**. This checks the selected approximate implementation
   on the control; it supplies no error bound for the large enzyme region.
4. Exercise the actual fixed/free optimizer adapter on that control with one
   H fixed and at most **eight** objective/gradient calls. Verify the fixed
   coordinates remain exact, full/free gradient index/unit mapping is correct,
   and constraint Jacobians agree with independent finite differences. Failure
   refuses enzyme optimization. Passing without optimizer convergence can
   establish mapping only; record those claims separately.

This control allocation is at most **23 SCF calls / 11 analytic-gradient
calls**: fifteen SCF and three gradients for items 1–3, plus at most eight
energy/gradient calls for item 4. Count every entered call, including refusals;
source parsing and synthetic algebra controls are separate. Exact coordinate
axes, thresholds, paths, software sources and stopping rules must be captured
in the successor before its first native call. None has been run here.

## Proposed finite resources and dispositions

The first primary-only GFN2 protocol is being prepared with the reconciled
ceilings below. They replace the earlier preliminary GFN2 proposal of120 CPU
seconds per case/900 aggregate, which was never executed. None is measured
new-region cost or a promise of successful optimization. The DF rows remain
unselected comparison proposals; no DF allowance is selected by the GFN2
geometry-repair successor:

| Resource | Proposed ceiling |
|---|---|
| Threads / concurrent case workers | One BLAS/OpenMP thread / one worker. |
| GFN2 controls | 20 aggregate CPU seconds / 120 wall seconds, including startups; at most48 objective evaluations, with an unchanged17-command menu and source-bound38-evaluation maximum. |
| GFN2 per case | 300 CPU seconds / 600 wall seconds; requested60 cycles, source-bound99 actual optimizer calls, at most120 objective evaluations including final diagnostic, and 250 SCC iterations per solve. |
| GFN2 whole proposed native operation | 2,020 aggregate CPU seconds / 4,200 wall seconds:1,800 case+20 control+200 parent CPU, including restoration/admission/publication/verification. |
| GFN2 memory/scratch | 4 GiB native hard address-space ceiling; measure RSS separately.1 GiB private scratch whole; full-field capacity remains unmeasured. |
| DF native control CPU | 300 aggregate CPU seconds, charged with imports/startup. |
| DF per case | 1,200 CPU seconds; 1,800 wall seconds; at most twelve native energy/gradient evaluations and twelve optimizer iterations. |
| DF whole selected native operation | 7,500 aggregate CPU seconds and 11,100 wall seconds, including controls, case startups, admission and verification. |
| One DF SCF/gradient call | 300 wall seconds, within its case/whole allowance. |
| DF memory | PySCF `max_memory=4096` MB; independent process peak/RSS ceiling 8 GiB. The PySCF value is advisory, not the hard cap. |
| DF selected private scratch | 48 GiB for the reduced SVP arm / 96 GiB for a selected diffuse arm, with exact roots and whole-process accounting; integral caches are not scientific publications. |
| New retained packet | 64 MiB whole / 16 MiB per retained member, excluding explicitly bound unchanged ancestors and disposable numerical scratch. |

Give every assigned case within a method the same selection, mobile rule and
allowance. If both primary GFN2 and reduced DF arms are selected, their combined
CPU ceiling would be **9,520 seconds**, with twelve explicit method outcomes and
separate per-arm resources. A geometry-only GFN2 selection does not reserve or
silently execute the DF allowance. Native GFN2 optimization-cycle limits do
not establish an exact number of SCC/gradient evaluations: retain complete
output and actual identifiable solve counts separately from top-level command
entries. If a native counter is not observable, declare it unidentified while
enforcing CPU/wall/memory/cycle bounds.

For a selected DF arm at most **72** full-region energy/gradient calls plus
**23** control SCF calls can be entered. The optimizer may use fewer than
twelve iterations because line
searches consume the evaluation cap. Do not assume twelve iterations means
twelve calls, or subtract failed attempts from the denominator. A preflight
storage/capacity refusal stops before native work; a case timeout retains its
entered-call count and last authenticated completed result. Charge killed
children and preserve partial logs. Unknown final closure/tail cost remains
unknown if the measured window ends before it; do not call the whole cap fully
verified from a smaller measured interval.

The byte denominator must state what is included: complete compact operands,
field/source bindings, protocol/module/helper/lock witnesses, actual imports,
raw logs and all assigned case outcomes. Full old archives and package ancestry
remain references, not newly copied bytes or portable completeness. Retain
initial/final geometries, complete final gradients, all energies/evaluation
counts, constraint residuals, contacts, changed IDs, formal inventory and field
sums. Do not retain every large DF cache as scientific evidence or conceal
its separate scratch cost.

Use distinct ordinary dispositions: **SOURCE_REFUSED**, **CONTROL_FAILED**,
**RESOURCE_REFUSED**, **SCC_OR_SCF_FAILED**, **PROTON_STATE_ESCAPED**,
**GEOMETRY_UNREADY**, and **FIXED_BOUNDARY_GEOMETRY_ADMITTED**. A missing or
unevaluated case stays explicit in the six-row roster. Admission requires
finite converged electronic results, complete unchanged identities/fixed
coordinates, retained H_a/H_b attachments, the unchanged
enolate/overlap screens and the independently checked stationary condition.
A single-point or budget-exhausted lowered energy is not a relaxed state.
Neither fixed-boundary admission nor a positive/negative HOMO certifies a ground
state, thermodynamic population or catalytic reaction. Further electronic
stability/confinement sensitivity needs a separately bounded, matched test.

## Primary local software witnesses and scientific next step

The [feasibility audit](rr-coupled-relaxation-feasibility.md) binds installed
METADATA, PySCF QM/MM/unit/grid/scanner implementation and SciPy optimizer.
Additional inspected paths below are relative to
`/tmp/rubisco-electronic-20261010-env/lib/python3.11/site-packages`:

| Source | Inspected support | SHA-256 |
|---|---|---|
| `pyscf/df/df_jk.py` | DF J/K, gradient dispatch, range separation | `7f4e8c3a930b8f55d1656b0bd6d24dcca7fe365ba5de00cfcebcebf813347cee` |
| `pyscf/df/grad/rks.py` | Range-separated DF RKS gradient and auxiliary/grid response | `c33196f5fafa1a6646b5d5edbd7e198716b9d77a12b160fa245a6bc307f6de56` |
| `pyscf/df/grad/rhf.py` | DF nuclear/auxiliary derivative assembly | `a52525f269974884b28846b55d021c169d430048e0755b55557480f733128735` |
| `pyscf/gto/basis/def2-universal-jkfit.dat` | Explicit H/C/N/O/P/Mg auxiliary data | `8970edf068a6010954535eb2b1ee978900dbea989b20e305c730dabb0298de5a` |

The prospective source-charge owner was inspected at private staged SHA-256
`4edcd851c019826f0822079c45b28675fdbeee4bb529b26aefd0e26b1267f2ba`.
It is not a selected native owner or canonical scientific product. An independent
stdlib calculation from authenticated native core tokens agrees with its exact
field totals and five conserving transfers without importing that owner or
calling a constructor. That agreement is charge-bookkeeping evidence only.

After a retained matched repair, the smallest useful scientific successor is
the [local carbon-processing competition](rr-coupled-assessment-design.md):
matched productive-forward versus return/decarboxylation exits from the same
adduct, with explicit gas/water/stereochemistry and rate assumptions. A repair
energy, occupancy guess or source-derived mutant label cannot replace those
operands. Retain H287 product-flux/side-product/LOD constraints separately from
D263 activation and turnover. Strong conventional methods with the same tools,
feedback and budgets remain necessary before attributing consequential benefit
to EL.
