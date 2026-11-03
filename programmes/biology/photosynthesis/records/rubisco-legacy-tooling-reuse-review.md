# Reusable Rubisco tools from the retained icf-yolo work

SPDX-License-Identifier: CC-BY-4.0

Reviewed 11 October 2026 for the current [four in silico checks](rubisco-insilico-selection.md).
The useful inheritance is molecular preparation, numerical controls and recovery
machinery. The old calculations do not establish the Gp I95M candidate's effect.
No historical simulator, test, molecular constructor or quantum calculation was
executed during this review.

## Sources inspected

The donor repository, installation tests and environments are not distributed with Empirical Lawhood.
No public repository or archive locator is supplied here for those exact revisions.
The linked inspection manifest supplies selected hashes and observations, not those code payloads.
Reuse requires separate access to the exact donor source and its dependencies.

Some helpers are available in the [partial preservation archive](redirection-preservation-v1.md).
Its [member index](preservation/redirection-v1/member-index.json) identifies `historical-helper/native_coupling/native_coupling.py` and its exact original bytes.
Check the member's original locator and hash before comparing it with a helper cited below.
The archive is not a complete donor checkout or native environment.
The current [heavy-scaffold owner](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_preparation.py) supplies a narrower migrated implementation, not the original donor code.

The prior repository is `/home/chevre/gs-ml/icf-yolo`, whose inspected primary
head is `70ad6708799f0e8070526ef15c1da4870e080238`. The main molecular source is
the retained branch `codex/rubisco-r02s-completion-20260925`, commit
`aa9346547560abcb6500f2e97b53b96f456d9be3`, and its existing worktree
`/home/chevre/gs-ml/icf-yolo-rubisco-r02s-20260925`. The earlier intake/assay
branch has commit `ec4f7ad3c81ffb2d9734babd866f933c794398cc`.

The [read-only inspection manifest](rubisco-legacy-tooling-source-inspection.json)
authenticates sixteen selected legacy code, test and result files. All sixteen
worktree files equal their committed bytes. It also records existing EL owners
and the exact retained QM/MM helper. This is a selected-file inspection, not a
new full source-package or scientific qualification audit. Neither repository's
Git metadata nor the retained worktree was changed.

The existing [migration manifest](migration-manifest.json)
already distinguishes adapted, conditional and unported legacy symbols. Its
three molecular selections are conditional: listing their destination owner
does not mean that an executable molecular route has been migrated.

## Ranked reuse for the selected checks

| Priority and use | Concrete reusable implementation/testing | Adaptation required before scientific use |
|---|---|---|
| 1. Full molecular preparation — checks 2/3 | Legacy `rubisco_m1_v5/preparation.py`: `isolated_kcx_parameters` preserves ordinary ff14SB terms, namespaces custom KCX types, copies peptide-boundary terms, and checks the 23-atom charge census. `native.py:_observation_indices` independently checks the **post-Amber** genotype, activation, ligand/metal counts, charges, atom uniqueness and peptide connectivity. | Replace the hard-coded 9RUB two-LSU material and residue offsets with the authenticated full Gp/Te L8S8 maps. Retain all eight SSU edits, M1/V1 views, native termini, missing-coordinate models, original disulfide connections and complete assigned parameter coverage. The current check-3 owner already implements prospective scoped KCX derivation and post-Amber origin/genotype checks; actual molecular construction remains unentered. |
| 2. Numerical force controls — checks 3/4 | Legacy `rubisco_molecular_v1/analysis.py:project` checks analytic forces against central energy differences at **h and h/2**, and joins requested, accepted, applied and realized offsets. `test_rubisco_environment_installation.py` exercises Amber save/reload, force-unit conversions and ASH/PySCF/OpenMM boundary and environment gradients. | Reuse the control design and independent reduction under the newly selected Hamiltonian and environment. Include mutant atoms, KCX/metal/ligand, boundary atoms and nonzero field sites. A passing synthetic or historical control does not qualify a different enzyme Hamiltonian. |
| 3. Restart and custody — check 3 | `rubisco_m1_v5/checkpoints.py` provides immutable checkpoint generations, hashed members, compatibility validation, packed state and cumulative clocks; the v5 checkpoint/native tests exercise interrupted continuation and substitution refusals. V6's native restore and synthetic-particle test preserve byte-identical Context state, RNG/history and exact step/time during interrupted thermalization; a separate test rejects restarting with a fresh seed. | Adapt the records to the current registered operations and explicit storage roots. Preserve positions, velocities, box, integrator/RNG state and accumulated attempted work. Binary OpenMM checkpoints require compatible software/platform/hardware. The completed legacy enzyme pilot exercised receipt recovery, **not an interrupted enzyme trajectory restoration**. |
| 4. Sampling diagnostics — check 3 | `rubisco_m1_v6/analysis.py:project` retains the complete assigned roster, block means, lag-one correlation, temperature/energy drift, preparation disagreement, repeat spread and mutant–WT contrasts. Failed or incomplete cases remain in the denominator. | Reuse these diagnostics rather than the old fixed fifty-frame/block layout or its heuristic effect ratio. Add statistical inefficiency/effective sample size, block uncertainty, agreement across thermal ensembles, 1/2 fs refinement and parameter/completion sensitivity. Sites and frames remain nested computational observations. The proposed eighteen-case legacy sampling experiment was **unentered**. |
| 5. Complete QM/MM complement and boundary audit — check 4 | The retained `native_coupling.py` has Coulomb-exception correction, original LJ-table checks, bonded save/reload checks, explicit ASH force masks, fixed-link binding and full point-field ordering. Existing EL owners parse original Amber signed 1–4 rows and construct explicit reference indices. The retained C1/C2 controls include **total coupled** finite-difference checks. | Factor the source-preserving operators into the new owner with explicit QM/MM exclusions, retained cross-LJ/bonded terms and candidate-specific embedding. The old constructor requires its exact xTB adapter; it cannot be relabelled as PySCF. Reactive states, atom/bond/proton transformations, charge/spin, mobile/fixed atoms and Hamiltonian completeness must be declared for the actual Gp/Te materials. |
| 6. Uncertainty/design arithmetic — checks 1/4 and packet interpretation | `rubisco_precision_v1.py` retains parent–mutant covariance, dependent specificity terms, PSD validation and unknown-correlation bounds. Tests explicitly reject treating algebraically derived oxygenase as independent evidence. The stationary assay and source-specific historical analysis are already adapted in EL. | Supply authentic errors/covariance where known, retain missing covariance, and bind the current turnover/specificity targets. Do not inherit the old engineering effect thresholds or infer small-sample coverage from Gaussian arithmetic. An RT conversion alone supplies no justified barrier-to-rate or mutation-to-kinetics map. |

Legacy paths in this table are relative to
`src/icf_yolo/adapters/simulators/`, except the precision owner under
`src/icf_yolo/adapters/methods/` and the installation tests under `tests/adapters/`.

## A concrete QM/MM defect to preserve

The installation test parametrizes `dipole_correction=True` as a **strict
expected failure**: the pinned ASH implementation omits auxiliary dipole-charge
gradients from atomic force assembly. This is visible source/test evidence; the
review did not rerun that test or establish the behavior of a different ASH
installation. A reused coupling must explicitly disable that correction under
a declared model or implement and independently verify its missing force terms.
The no-dipole cases test two link/projection combinations and both QM-side and
MM-side finite differences. Plain PySCF point-charge embedding supplies neither
the complete classical complement nor a sampled PMF.

The targeted legacy tests do not supply an Amber-versus-OpenMM engine-equivalence
proof. Central finite-difference agreement inside one engine is a narrower
control. Likewise, the synthetic minimizer, restart and liveness fixtures prove
their declared software behavior; they do not establish enzyme equilibration,
long-run throughput or a hardware winner.

The retained helper is **65,783 bytes**, SHA256
`0cbef06a873c745279d6525f6a697ae91b8adaa73bb8d8b5e7e0f256465e3765`, at
`/tmp/rubisco-qmmm-work-v9/native_coupling.py`. Its [actual preparation
conformance result](rr-qmmm-preparation-conformance-result-v2.md)
preserved 25 LJ type slots, the complete original lookup/A/B arrays and bonded
terms through dry selection, splice, remake and reload. That result involved
no Context, energy, force or quantum evaluation. The [later reference
attempt](rr-qmmm-retained-reference-result-v3.md) returned one
native coupled method, but no accepted full physical result or optimized enzyme
geometry. Its starting-contact and source-mapping failure is relevant to new
reactive preparation; it is not a kinetic result.

## What the old results actually establish

The completed M1 v5 pilot covered six **Rr WT/M100T/D206E × HID91/HIE91**
preparations, with 0.5 ps warmup and **0.2 ps observation** per case. It recovered
three task receipts and seven outputs. Preparation/cost and receipt recovery
were assessed at that declared scope. Large retained residual forces and short
warmup provide no equilibrium or force-convergence certificate. The atoms,
mutations, proton choices and source sequence are different from Gp I95M.

M0's twenty-five energy/force queries, the v5 short pilot, exposed stationary
kinetic witnesses and synthetic QM/MM controls keep their original scope and
exposure. None supplies a matched Gp mutant effect, an oxygen/carbon PMF pair,
spin-crossing kinetics, biological replication or prize qualification. The
legacy v6 sensitivity result, CPU/OpenCL hardware comparison and molecular-to-
kinetic predictive bridge remain unentered, as recorded in the
[historical result register](retained-results.md).

Reuse selected scientific owners and tests, then register them through current
EL contracts. Do not import sibling-worktree runtime code, copy six historical
simulator stacks, reuse old signers/authority, relabel exposure, or inherit retired
memory/output/atom-count/wall-time ceilings. Preserve the authentic source maps,
complete denominators, numerical controls, negative outcomes and convergence
requirements. No checkbox for checks 2–4 is completed by this reuse review.
