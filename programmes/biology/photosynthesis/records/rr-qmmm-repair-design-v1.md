# Rr complete QM/MM repair successor: reuse and admission design

SPDX-License-Identifier: CC-BY-4.0

**Prospective design, not a frozen execution protocol.** The [six-case
electrostatic repair](rr-xtb-native-repair-result-v3.md) stops with six failed
optimizations, severe QM/MM contacts and nonrigid anchor leakage. A complete
QM/MM successor addresses those identified limitations using existing source
parameters and implementations. It does not select another run of the failed
Hamiltonian, change its historical result or relax its geometry thresholds.

## Exact reusable implementation and source

The donor environment and installation test below are external historical prerequisites, not files supplied by this checkout.
No public retrieval route is supplied here for their exact inspected bytes.
Use the [legacy tooling availability note](rubisco-legacy-tooling-reuse-review.md#sources-inspected) to distinguish preserved helpers from omitted donor code.

The parent `/home/chevre/gs-ml/icf-yolo/.venv` already contains ASH 0.99 at
commit `3cdea44538164c6b21c99fd9378dd2567a622ac1`, geomeTRIC 1.1.1, ParmEd 4.3.1
and OpenMM distribution metadata 8.3.1. OpenMM's installed `version.py` reports
**8.3.1.dev-6e13f13**, revision
`6e13f1361dcc3ffb581c7c97e3adfcc61257b813`, `release=False`. A selected profile
must preserve those actual bytes and distinctions. No new installation or
legacy MD rerun has occurred.

Reuse the [pinned ASH QM/MM coupling](https://github.com/RagnarB83/ash/blob/3cdea44538164c6b21c99fd9378dd2567a622ac1/ash/modules/module_QMMM.py)
and [active-region geomeTRIC adapter](https://github.com/RagnarB83/ash/blob/3cdea44538164c6b21c99fd9378dd2567a622ac1/ash/interfaces/interface_geometric_new.py).
The latter starts from the full fragment and changes only its active atom
coordinates. Leaving all 31 declared anchors outside that list supplies direct
coordinate freezing rather than the failed projected native L-ANC basis.
Independent exact-coordinate checks remain mandatory.

The old completion checkout supplies native Amber round-trip/unit and
QM/MM boundary finite-difference test patterns at
`tests/adapters/test_rubisco_environment_installation.py`. The native v5/v6
receiver sampling/checkpoint stack is unnecessary for this finite question.
Reusing its three-distance/field observables would not supply reaction
competition or kinetic calibration.

The read-only source inspection is
`/tmp/rubisco-qmmm-repulsion-source-inspection-v1`: **four files / 2,573,244
bytes**, census SHA-256
`ea59c880f28479c279ac0e2d2878c9f25864eb9c307c83c363e2c5bd9007065b`.
Its **2,556,501-byte** lexical projection has SHA-256
`9dbc587ee8cf0ec807b9503ea80dba9fe52521a48a4a29003f2421ad917407c7`.
It binds the original **22,365,456-byte** full topology, SHA-256
`87b5ed6e40ea77afde056312f923fca44f8b6ee164d8dd973e6deb3b79b2b902`:
116,767 atoms,
25 LJ types, 325 pair coefficients and the 13,828-atom dry-core selection.
Native exclusions, signed dihedral witnesses and 1–4 scale parameters are
retained. It has no negative 10–12 indexes. This private inspection supplies
no artifact-plane source authority or constructed successor topology.

Both closest reference collision pairs are non-excluded and have nonzero
native Amber terms, in kcal/mol and Å:

| Pair | Native A, kcal Å¹²/mol | Native B, kcal Å⁶/mol |
|---|---:|---:|
| KCX OQ2–ASP193 HA | 36947.153 | 92.1192136 |
| KCX HZ–ASN192 O | 1025.95236 | 15.3505284 |

Use the native type-pair tables and exclusions, rather than invented element
radii. Five zero-charge boundary CAs still have steric identities; omitting
their electrostatic rows does not remove their classical interactions.

## Necessary integration delta

1. **Source admission.** The implemented cold, hash-first
   `src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_amber_nonbonded.py`
   retains
   exact lexical Decimal parameters, native atom/type order, exclusion rows,
   signed dihedral/1–4 witnesses, complete counts and omissions. The full native
   topology exceeds the 16 MiB prospective operand size: retain its whole
   source digest while admitting ordered bounded chunks, each at most 8 MiB,
   with a 32 MiB aggregate bound and at most 64 chunks. Authenticate the entire
   original source before interpretation and retain every chunk binding.
   This source record describes the original keto topology only; it cannot
   impersonate a reactive or mutant topology. Its eighteen synthetic tests and
   twelve import/discovery checks pass; authentic admission remains unentered.
2. **Reference topology and quantum mapping.** Join the admitted reference V2
   inventory to full dry-core atoms and source parameters. Distinguish actual
   QM atoms, relocated source hydrogens, tautomer replacements, modeled caps,
   fixed source anchors and retained classical atoms. Freeze cap placement and
   boundary-force treatment explicitly; avoid combining an existing cap with
   another automatically generated link atom. Preserve exact held field
   coordinates/charges and the existing CA charge redistribution. Use the full
   **13,828-atom physical fragment**, **76 real QM atoms** and five generated
   links. The **50 real mobile QM atoms** are active; the 26 real QM anchors
   and every MM atom are fixed. Restore physical CB/CA cuts
   **2877/2875, 2914/2912, 2926/2924, 3963/3961 and 4332/4330**. ASH's sorted
   real-atom and link ordering requires explicit bijections to the original
   81-atom capped inventory. Do not add those synthetic caps as MM particles.
3. **Reactive parameter convention.** Specify cross-region LJ types before
   calculations. A common fixed source type assignment through a QM reaction
   is a possible approximation; silently claiming it is a faithful new proton
   topology is not. Dynamic retyping would change the Hamiltonian across the
   path and also needs justification. New Asn atoms and spectator-residue
   changes require explicit donor/type/bond/exclusion joins. A first reference
   control need not await complete mutant topology construction. Retain Ha's
   `amber:6901` h1/type-19 and Hb's `amber:6900` ho/type-22 cross-region LJ
   assignment across both proton views; ho has small nonzero LJ. The reference
   itself requires a complete spectator B287 HIE→HID91 donor splice, including
   its proton attachment, charges, bonded parameters and exclusions. Existing
   cold records do not contain the complete angle/torsion force arrays. Bind
   their original full-topology source and use the installed ParmEd extraction
   under the later frozen caller; a cold inventory plan cannot certify that
   runtime Hamiltonian.
4. **Classical coupling admission.** Remove wholly QM classical terms and
   avoid duplicate electrostatics while retaining declared cross-region LJ and
   boundary terms. Read-only inspection finds that pinned ASH's electrostatic
   path updates QM particle charges without necessarily clearing OpenMM's
   independently stored exception charge products. The thin integration must
   explicitly inspect and zero QM-involving exception charge products while
   preserving required LJ parameters. Validate the actual force objects and
   their index joins; do not equate particle-charge updates with exception
   updates. There are 77 unique source proper QM/MM 1–4 candidate pairs in the
   reference. Regenerate affected MM/MM exception charge products using their
   original SCEE after donor-charge assignment or boundary redistribution;
   excluded pairs remain zero. Record MM-only constant terms separately.
5. **Strict existing xTB single-point provider.** Preserve official binary and
   parameter hashes, explicit GFN2, hardness 99, charge/UHF, accuracy/SCC bounds,
   legacy conversion and complete field custody. ASH's default xTB wrapper uses
   different GFN/field/parameter settings; its native optimizer lacks this
   inquiry's strict convergence admission. Reuse the already checked CLI
   process/gradient machinery through a thin callback. Each callback retains
   actual native arguments, source plan, outputs, refusal and cumulative cost.
   No native `$fix` optimization or unselected restart is used. The pinned ASH
   wrapper retries failed xTB runs, removes inputs and can zero-fill incomplete
   point-charge gradients; those behaviors require the strict callback. Native
   gradients use **0.52917726 Å/Bohr**, whereas ASH uses
   **0.5291772109303 Å/Bohr**. Transform both QM and point-charge gradients by
   the ASH/native conversion ratio and check total-energy finite differences.
6. **Existing optimizer and controlled profile.** Reuse geomeTRIC active-region
   optimization with explicit active coordinates, thresholds and limits.
   Preserve native library/build/platform/thread identities. The prospective
   finite baseline selects OpenMM **Reference**, one native thread and an
   explicitly empty plugin directory. Bind its interpreter, core libraries,
   actual loaded modules and absence of user settings. Select bounded CPU and
   bounded I/O before any native import/context/callback; inspect automatic
   settings, cache and scratch writes. Do not synchronize the main environment
   or let optional imports discover sibling scientific state.

## Finite discrimination before another six-case roster

Before authentic model construction or native contact, freeze source/profile,
topology, fields, cap/exception policy, exact helper bytes, new output locators,
complete raw custody and a finite CPU/wall/memory/storage/objective allocation.
That future study has a new declared execution envelope and carries the old
39 scientific processes, costs, exposure and immutable failures as ancestry;
it does not reset the old 4200-second operation.

First assess synthetic/source-native controls: topology/parameter round trip,
zero versus nonzero LJ and exclusions/1–4, removal of duplicate quantum terms
including exceptions, total coupled finite-difference forces, boundary-force
redistribution, unit conversions, exact frozen anchors and SCC refusal
propagation. The old dipole-correction finite-difference expected failure is
not a passing control; disable that unselected correction. Do not add automatic
hydrogen-bond constraints, rigid water, mass repartition or regenerated fields.

Then enter **one computational reference V2 repair**, using the same exposed
initial geometry. Require converged native SCC, admissible total coupled
forces, unchanged anchors and the existing mobile/proton/contact/bond/chirality/
enolate criteria. Retain all escapes and optimizer/resource failures. A good
reference would justify separately assessing the complete declared genotype
and proton denominator. A failed reference or inconclusive force/cap join
stops this supplier again; it cannot nominate a candidate or justify a weaker
screen. No calculation had entered when this design was first written; the
subsequent control and construction outcomes are recorded below.

Only accepted states can enter the [matched processing/commitment inquiry](rr-coupled-assessment-design.md).
That inquiry still needs productive/return paths and an assessed observable
mapping; later oxygen/spin/occupancy/activation and challenge-assembly transport
remain distinct requirements. Native model repair alone does not establish
consequential EL capability. A competent conventional repair receives the
same structures, solver and parameter opportunity in the eventual comparison.

The [finite reference protocol](rr-qmmm-native-repair-protocol-v1.md) makes the
successor executable only after its configuration/source freeze and actual
prefit custody barrier. Cold source, topology and strict-callback owners are
implemented. The current focused suite passes **150 pytest tests**; separate
historical stdin checks assess private reference/control arithmetic. Those
software results are distinct from native conformance or scientific acceptance.

## Current execution and remaining source alignment

The [v3 raw-callback attempt](rr-qmmm-native-coupling-result-v3.md) and
[v4 full coupled control](rr-qmmm-native-coupling-result-v4.md) retain their
separate failures and numerical witnesses. The [v5 successor](rr-qmmm-native-coupling-result-v5.md)
passes the constrained Cartesian control with exact fixing and fresh total
forces, plus the full native point-charge capacity control. Later attempts
reuse those exact results, with source/custody joins and every old cost.
The [v6/v7 outcomes](rr-qmmm-native-coupling-results-v6-v7.md) retain source-call
and member-bound integration refusals. The [v8 attempt](rr-qmmm-native-coupling-result-v8.md)
admits the exact original/coupled sources and held context, then refuses native
construction during dry selection. No enzyme xTB objective or optimization
has entered, and no acceptable computational reference is established.

Pinned ParmEd slicing rebuilds a lookup for the types present in the selected
atoms, while restoring the original A/B coefficient arrays. The authentic
source has25 types/625 lookup entries/325 A/B pairs; dry atoms use types1–23.
Source-only replication confirms corresponding retained pair indices agree
when each lookup is addressed with its own stride. The failed native tables
were not saved, so physical parameter corruption is not established by the
guard refusal. Exact table identity and the original full denominator remain
required by the selected source convention.

Prefer an existing native source-preserving strip operation on a separately
loaded original. Clear only that dry copy's box before stripping, preventing
the pinned library's solvated-molecule reorder path. Verify the complete
original and retained atom order, all original type slots, both NTYPES fields,
full lookup and A/B arrays before and after preparation; keep the exact table
guard through donor splicing and save/reload. Preserve the pristine source
object for donor witnesses. The prospective v9 helper implements this native
operation, factors genuine preparation for both the full constructor and
native-only probe, and passes **77 focused software checks** in **1.38 s**,
with Ruff (56 coupling-owner, twelve probe and nine custody-harness checks).
It checks
both NATOM/NTYPES representations and retains the complete source tables
through donor remake and save/reload. Those tests use synthetic witnesses. The separately selected
[actual preparation result](rr-qmmm-preparation-conformance-result-v2.md)
now passes the authentic source/donor/native round trip after retaining a
zero-entry profile-alias refusal. The corrected source-preparation suite
passes80 software checks. Native preparation preserves all25/625/325 source
operands, complete bonded terms and the pristine original. No ASH/OpenMM
coupling, energy/force, xTB callback or reference optimization entered that
check. Reuse its exact retained native topology, source and custody witnesses
in the next full coupling selection, preserving masks and explicit charges
rather than repeating the completed full-source preparation.
The old2400-second operation is closed; any further execution must have a
separately frozen finite scope with old costs, exposure and failures retained.


The separately frozen [retained-reference result](rr-qmmm-retained-reference-result-v1.md)
subsequently authenticates and loads that saved topology, then refuses the
installed OpenMM Amber parser's `CustomNonbondedForce` at the force-roster
inspection before any Context or objective. Preserve all original source
types and coefficients. The next successor must authenticate the complete
source-table LJ representation and its exact QM–QM exclusions, preserving
cross-region interactions, before the unchanged reference assessment. The
negative packet and actual costs are closed; no optimizer or geometry result
is supplied by this attempt.

The [v2 actual source-table result](rr-qmmm-retained-reference-result-v2.md)
returns that native constructor with complete source-table/type/exclusion
checks and retained before/after masks. The worker then refuses an oversized
indented construction audit before C4 or any objective. The next operational
caller must serialize the whole audit through compact ordered chunks; it
reuses the same native model/C4/reference sources and retains all old scopes,
costs and bytes. This conformance prerequisite supplies no accepted geometry
or force qualification.


The [bounded-audit/C4 outcome](rr-qmmm-retained-reference-result-v3.md)
now retains the full compact construction audit and passes the actual native
source-table control: one Context, three complete energy-force returns and
independent source analytic/finite-difference criteria. The first enzyme
Context, quantum process, MM and full coupled method return, then the
unchanged reference assessor refuses a finite/bounded physical operand.
The complete rejected full energy/gradient was not captured before its guard;
the retained input/refusal cannot distinguish nonfinite from finite-over-cap
or energy from gradient. No accepted full reference result, fresh gradient
or final geometry assessment follows. Preserve native-return and accepted-
assessment counts separately. Before any future selected native attempt,
retain complete unverified full returns before guards and diagnose them under
the existing screens. The programme pauses after this result/audit at the
user's request; no additional native successor is implemented or executed.

The independent source-only contact audit also identifies three severe
nonexcluded fixed-MM starting contacts outside the active/QM sets, including
A91 HID NE2–B243 ARG HH22 at0.097095 Å and A91 HID HE1–B243 ARG NH1
at0.278487 Å. Their scalar source LJ contributions exceed the physical
operand cap, while the retained xTB primitive is finite. This supports a
starting-coordinate/source-mapping diagnosis, not a reconstructed actual
native full return. Active-region optimization cannot move those fixed MM
atoms. On resume, review and resolve their provenance before another native
selection, without weakening exact fixing or physical criteria.
