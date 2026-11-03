# Prospective Rr coupled relaxation feasibility

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026** on `recchain`. This is a **local primary-source
software feasibility audit**, not a frozen scientific protocol, native
execution, admitted Hamiltonian, optimized state or kinetic result. It changes
no source packet, dependency/profile, existing protocol or electronic owner.

Complete and inspect the current [six-context initial geometry
probe](rr-coupled-initial-geometry-protocol-v1.md) first. Its actual refusals,
contacts and incomplete degrees of freedom must precede the selection of a
native relaxation protocol and cost limits. Inherited keto geometry and a
complete proton ledger are different claims. The
[chemical inventory](rr-coupled-chemical-inventory.md) and
[archived parent source](rr-amber-core-source.md) remain the source boundaries.

## Available installed operations

The inspected environment is
`/tmp/rubisco-electronic-20261010-env/lib/python3.11/site-packages`.
Its installed **METADATA**, rather than imported runtime version APIs, reports
PySCF **2.14.0**, SciPy **1.17.1** and NumPy **2.4.6**. The audit read and hashed
local files only: **zero native package imports, SCF/gradient/optimization
calls, installs or environment synchronization**.

| Relative METADATA source | SHA-256 |
|---|---|
| `pyscf-2.14.0.dist-info/METADATA` | `6aede69454a6d7e8504e135c223a221c67d8219bae01f819c325f1cd0da6d491` |
| `scipy-1.17.1.dist-info/METADATA` | `7cdd5544eb610b86e000b6f0a21e86f84423faf0aacbb99990f3d41f25e1f314` |
| `numpy-2.4.6.dist-info/METADATA` | `b082c52ccbe3b880bae177c35171b52ed6c947f3ad71e3762f2723f60a411de0` |

`pyscf.qmmm.add_mm_charges(mf, coordinates, charges, radii=None, unit=...)`
decorates HF/DFT with an external electrostatic field.
`mf.nuc_grad_method().as_scanner()` supplies energy and **analytic QM nuclear
gradients**, including electronic embedding and QM-nucleus/MM-charge
interactions. The scanner keeps the supplied MM field fixed while resetting
QM geometry and reuses the preceding density within a context.

The selected environment has **no geomeTRIC, Berny or ASE installation**.
`pyscf.geomopt.optimize()` tries optional geomeTRIC then Berny and would fail.
Available `scipy.optimize.minimize(method="SLSQP", jac=True, bounds=...,
constraints=...)` can instead consume `(energy, selected_gradient)` through
a small fixed/free coordinate adapter. This reuses the maintained optimizer;
it does not require a new general geometry engine. L-BFGS-B is available for
box-only problems but does not handle nonlinear proton-state constraints.

## Prospective matched coordinate repair

A focused initial proposal fixes the outer environment, Mg, five CB anchors,
link H and complete phosphate anchors, while allowing the non-phosphate
substrate and terminal KCX group to relax. This is a possible starting scope,
not the final mobile list. If the actual probe finds contacts requiring
rebuilt **HID287 HD1 or ASN terminal H/amide atoms** to move, admit those
chemical roles consistently across all applicable contexts. Neither genotype
exceptions nor choices selected from endpoint labels are allowed. Maintain
the same inclusion rule, optimizer, constraints, initialization opportunity
and total allowance for the six-context denominator.

Use explicit free coordinates to preserve fixed atoms; gradient `atmlst`
selects derivative rows and does **not** freeze coordinates. Keep the declared
H_a/H_b attachments with predeclared distance/nearest-parent constraints and
retain any binding constraint or escaped proton as a scientific disposition.
Do not force a desired C2=C3 length, planarity, carbon ordering or favorable
energy. Freezing both oxygen/proton pairs in Cartesian space may prevent the
needed carbon-framework repair and must not silently become the mobile rule.

Use **Bohr coordinates and Hartree/Bohr gradients** together. If coordinates
are Angstrom, convert the gradient by **division by `lib.param.BOHR`**.
The gradient scanner computes a gradient even when SCF has not converged;
the adapter must refuse nonconverged/nonfinite results before the optimizer
accepts them. Freeze `grid_response=True` explicitly if full numerical-grid
response is required; the local RKS gradient default is `False`. Also freeze
grid/pruning, basis, functional, SCF thresholds/cycles, initial guess and
within-context density reuse. Start each separate context independently.

SLSQP success alone is insufficient. Retain projected gradients, constraint
residuals, geometry/cap/identity/chirality checks and every failure. An active
proton-state boundary may support only a constrained geometry, rather than a
metastable proton well. Bound actual native evaluations as well as optimizer
iterations: line searches can make additional SCF/gradient calls. New-region
runtime is unmeasured; the previous fourteen-atom pilot is not its cost proof.

## Hamiltonian and electronic conditions still missing

The first construction supplies environment membership, **not executable MM
charges or a complete embedding Hamiltonian**. Before native use, freeze real
QM/MM exclusions, changed spectator-chain residue charges, active-backbone
policy, the five boundary charge shifts, field scope and coordinates, and
point versus Gaussian charge representation. Gaussian radii are supported
but choosing them is a new model decision. No real QM atom or cap may also be
present as an MM charge. Record removed/shifted charge sums and final QM/MM
totals separately; capped formal charge is not a peptide partial-charge sum.

The PySCF embedding energy includes QM energy and electrostatic coupling;
it excludes **MM self-energy, van der Waals and other bonded/nonbonded QM–MM
terms**. Thus it can define a declared constrained electrostatic repair, but
not automatically a complete enzyme energy. Short contacts, missing waters,
metal treatment and the inherited outer geometry remain model limitations.

Use the inventory's **Q −6/−5/−6**, **382/382/370 electrons** and separately
declared singlet hypotheses. Even electron counts do not certify the ground
state. Local `def2-svpd.dat` contains H/C/N/O/P/Mg diffuse basis data; selecting
it would be a new frozen basis choice, not an installation requirement.
Positive HOMO energies, overlap conditioning and electron-density confinement
must remain diagnostics rather than be clipped or repaired by favorable
basis selection. `mf.stability(..., return_status=True)` supplies restricted
internal/external stability statuses; any such native check and its settings
must be budgeted. Do not silently follow returned orbitals into another state.

The inspected QM/MM wrapper has **no embedded Hessian override**. Do not treat
an inherited `mf.Hessian()` as a verified embedded force-constant calculation
or a source of harmonic prefactors. A constrained stationary geometry, a local
well, a reaction saddle/barrier and a free-energy/rate relation require
different evidence. Neither proton-view energy differences nor relaxation
success supplies paired intrinsic turnover/specificity.

## Future minimum verification and exact code witnesses

The donor tests and inspected native environment named below are not distributed with this checkout.
Their hashes identify the historical inspection; no public retrieval route for those exact files is supplied here.
The [legacy tooling availability note](rubisco-legacy-tooling-reuse-review.md#sources-inspected) distinguishes omitted donor code from supplied helper snapshots.

The parent repository already has synthetic embedded-solver and boundary-gradient
checks. Reuse their central finite-difference and unit-conversion pattern for
the selected successor. The completion worktree's
`tests/adapters/test_rubisco_environment_installation.py` (SHA-256
`0f1669a995685a9d85f1249fc1775018806b944286aa742f83f14066d020ce85`)
checks selected ASH/PySCF/OpenMM boundary gradients against displaced energies;
it explicitly marks the auxiliary dipole correction as an expected failure
because its atomic force assembly omits the auxiliary-charge gradients.
The parent's `tests/adapters/test_rubisco_pyscf_installation.py` (SHA-256
`82a200c4afd5c7bae4ddd4a0236452fe36b7d4cbe9524a202e1e55190f83a825`)
also exercises a small restricted molecule, a point-charge field and a separate
open-shell control. These are inspected historical software tests, not new
passed controls or enzyme evidence. The proposed fixed-cap, fixed-field
coordinate repair does not move classical boundary atoms and does not select
ASH force projection, auxiliary dipoles or an OpenMM installation. A future
moving-boundary model would need its own tested force assembly.

Before admitted native use, verify the thin adapter on a small declared
gradient control against an independent central finite difference, including
embedding and unit conversion; check fixed-coordinate preservation and a
common translation of QM plus MM. These are prospective native software
controls with separately accounted cost, not completed tests here. Validate
the actual six inputs and constraints before a bounded matched calculation.

The maintained electronic owner is
`src/empirical_lawhood/adapters/simulators/rubisco_electronic/core.py`, SHA-256
`88fe7e79ea4984795ef9c8f2730411ccefec00d4fbe2151fa6548841bb4c30a7`.
Its native job admits fourteen C/H/O atoms and its fixed original states;
the 78–83-atom P/N/Mg region needs an explicit successor contract rather than
altering the frozen old realization.

All following paths are relative to the selected site-packages directory
above and bind the actual inspected local primary code:

| Local source | Relevant operation | SHA-256 |
|---|---|---|
| `pyscf/qmmm/itrf.py` | Embedding, analytic gradients, energy scope | `e23c84f29f19666c8acaea3262fef041492b92e82cf8bd541425cc7cd25a357b` |
| `pyscf/qmmm/mm_mole.py` | Point/Gaussian charges and units | `c9b444a2876122fc32e4f0df7622e94844643d4da943d3cb9d3be92b13d82665` |
| `pyscf/grad/rhf.py` | Gradient scanner and derivative selection | `d30fd1ab2a00997183802da28da775f6a29a6c9705c55b19c04d66a1a575267f` |
| `pyscf/grad/rks.py` | Numerical-grid response | `cffc3e9efa10cf1b547d757e9d165c1000377e9159c794f87464a79c8c93ab46` |
| `pyscf/geomopt/__init__.py` | Optional solver selection | `0ab114898a099dc5d4a88d70ddc903ff7898d334be8f7d99a6ff28e7e5ec3556` |
| `pyscf/geomopt/geometric_solver.py` | geomeTRIC import and constraints | `b622fe771962991d3fcf1d6f02f0e8653ce7cb98c0c85a43c212f7f6e630a94a` |
| `pyscf/scf/stability.py` | Electronic stability statuses | `58ceea68eb56702ec41fa0a844b60c225ef53800ed4fb5b1fea307cd5bc50674` |
| `scipy/optimize/_minimize.py` | Optimizer dispatch and analytic Jacobian | `5afd3ecbeaba6606c27f5f9f298782c0dae80dd0e3e01d98d4249922ede6b7ea` |
| `scipy/optimize/_slsqp_py.py` | Maintained constrained optimizer | `c8362e8d36440f3de97b58562aadb86661271ea7f66160505f51a601aff71609` |
| `pyscf/gto/basis/def2-svpd.dat` | Available diffuse basis data | `f0eb33fb9bd80d81b741363db422d37ab35c45ba0e679b3fcbccc1da9296af55` |
