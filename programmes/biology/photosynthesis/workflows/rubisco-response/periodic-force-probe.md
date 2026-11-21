# Complete periodic force and cost observation

SPDX-License-Identifier: CC-BY-4.0

The periodic force probe measures one energy and the gradient on every physical
atom of one selected Gp assembly. Its independent reader authenticates the
original attempt and checks the complete returned arrays. Derivative accuracy,
reference-potential refinement, enzyme preparation and sampled physical rates
remain separate assessments under the selected physical supplier.
The [periodic numerical controls](periodic-numerical-controls.md) route selects
complete derivative and refinement questions and assesses their original
returns through the same execution and custody contracts.

Scientific cell and force selections are defined in
`empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts`:
`AmberPeriodicCell`, `PeriodicForceSettings`, `ConstrainedPeriodicForceSettings`
and `PeriodicMMSettings`. Its `read_amber_periodic_cell` parses the supplied
original topology and coordinate bytes without opening files or constructing
an engine. The native OpenMM/PySCF bridge remains in
`adapters.rubisco.rubisco_response.periodic_qmmm`. This ownership change retains
all original scientific schema revisions, fields, validation and canonical bytes.

New periodic MM selections use settings revision `2.0.0`, which explicitly
includes the authored whole-molecule geometry policy. Strict metadata readers
retain both historical revision-one shapes: the original settings without a
policy, and the interim producer's settings with an explicit policy but no
revision advance. They preserve each shape's exact original canonical bytes.
Reading either historical shape does not permit new native work. Runtime
preflight and execution require revision two before numerical-stock inspection
or native contact. Continue original work only through its compatible retained
installation and documented recovery boundary.

Historical settings without a geometry policy cannot supply a current
whole-molecule assessment. The current scientific reader refuses that missing
selection explicitly. Use the compatible original reader and retain its actual
findings or refusal; do not add a policy to old bytes or reinterpret an old
geometry pass as current admission. A later scientific selection requires its
own authored configuration and source identity.

The optional [accelerated compute route](../../../../../docs/using/accelerated-compute.md) has separate GPU configurations and explicit resource selections.
It preserves the original CPU contracts and requires the selected `accelerated_compute` invocation.
Its complete enzyme numerical acceptance remains pending until the selected GPU controls and original force observations pass.
OpenMM CUDA double precision retains upstream float32 nonbonded parameters; actual molecular parameter rounding requires its own assessment.
The separate `GpuReferencePeriodicNumericEngine` selects GPU electronic work with complete OpenMM Reference MM arithmetic.
Select it through `select_periodic_numeric_engine(molecular_platform='Reference')` before preparing and authoring a new attempt.
Its original records identify the selected platform. It does not relabel a prior CUDA result or alter the molecular model.

First authenticate the original initial-Amber product and complete raw archive.
`gp_initial_molecular.map_initial_amber_representation` repeats the independent
construction assessment before mapping every native atom, residue and parameter.
It retains known ligand bond orders and explicit unknown orders for other native edges.
It does not infer chemical bond orders from force constants or atom indices.
Ion placement can insert ions before the solvent population. The reader joins
every original solute atom and every complete retained crystal water across
that reordering, using named atoms and their common coordinate translation.
Missing or ambiguous original waters refuse. Masses, charges, bonded terms,
exclusions and nonbonded coefficients are compared through this complete map;
added solvent and ions retain separate native identities.

`CatalyticPathSelection` retains the complete QM/MM partition, formal charge,
spin, original covalent cuts, link atoms, and gas-free, carbon or oxygen scope.
Select whole residues or complete side chains with their explicit CB–CA cuts.
These atom selections do not qualify the electronic model or chemical pathway.

Use `prepare_periodic_force_probe`, `author_periodic_force_probe` and
`read_periodic_force_probe` from
`empirical_lawhood.api.domain_composition.rubisco_response.periodic_probe`.
Preparation binds the complete molecular representation, fixed catalytic atom
selection, periodic cell, electronic and molecular settings, and the selected
numerical environment. Authoring accepts the exact original Amber topology and
coordinate bytes, a project root, a fresh native work directory, and an artifact
writer with a fresh authoring destination. It returns the existing recursive
handoff paths and all six direct native-input paths. Execute the returned
handoff through the existing recursive lifecycle.

For a checkpoint density guess, use `prepare_periodic_checkpoint_density` from the same API module.
Supply the original cold-probe configuration, native definition, complete representation and raw sources.
Supply a frozen checkpoint path and its retained `FileEvidence` hash and size.
Preparation authenticates the complete source selection and checkpoint bytes before and after the read.
The checkpoint ceiling is 256 MiB, and the density ceiling is 128 MiB.
The reader requires the original direct, uncompressed molecular and SCF datasets with the selected array shapes.
It reconstructs the selected QM/link molecule and compares geometry, shell contractions and AO order.
It also checks finite orbitals, integral occupations, density symmetry and electron populations in the AO overlap metric.
Preparation computes overlap integrals but performs no SCF, energy or gradient evaluation.
It returns a `PeriodicDensitySeed` and a complete binary64 density payload.
An intermediate checkpoint remains an initial guess, even when its orbitals are valid.

Use `author_periodic_force_restart` with that seed, payload and the selected target prototype.
The target retains the complete model, coordinates, basis, charge, spin, embedding selection and numerical settings.
The selected numerical thread count may change within the existing allocation.
The numerical package files and interpreter must remain identical.
The target producing source is captured separately, so tested memory corrections can apply to the new attempt.
The new `rubisco-response.periodic-force-restart` operation has a distinct request and native contact.
Its nine direct inputs include the seed record and bounded binary density.
The binary transport avoids a JSON encoding of every density element.
The cold-probe schema and its seven-input contract remain unchanged.

At native entry, the restart repeats coordinate, AO, density and electron-population checks.
It retains the original seed files and identifies the density source in its observations.
It recomputes potentials and must satisfy the complete SCF and gradient criteria.
It does not restore DIIS history, a partial integral, runtime state or an original completion receipt.
The original attempt keeps its known or uncertain status.
Use the existing retained reader for the distinct restart result.
The reader authenticates its seed files and complete original return without replay.
These operations do not pause or stop another running attempt.

The task has seven direct inputs: its configuration, complete molecular model,
coordinate-array manifest, force-probe selection, numerical provenance,
evaluation request and original Amber sources. Complete molecular records are
published through bounded streams. The operation selects a 512 MiB molecular
record ceiling and a 256 MiB original-source ceiling; these bounds require
checking against each actual solvated assembly. The operation allocates eight CPU equivalents, 8 GiB RAM
and 4 GiB of native outputs, with no experiment time ceiling.
`PeriodicNumericEngine.numerical_threads` selects the actual thread count within that allocation.
Set `OPENMM_CPU_THREADS` and the selected engine's numerical thread variables to
that count before authoring. The registered worker freezes the same count for
OpenMP, BLAS, MKL, Accelerate, NumExpr, Numba, BLIS and OpenMM. The shared launcher
checks it against the task's CPU allocation, applies it before worker imports,
and sets already loaded numerical pools to the selected count. The worker then
authenticates all settings against its engine selection. Selecting these values
does not establish that a future model fits them.

At the first valid force-evaluation entry, the operator releases derived
canonical encodings of the complete molecular record, then requests ordinary
allocator reclamation. All scientific field values remain live. The original
entry and `record-encoding-release` observation retain the before/after memory
measurements and released-cache count. Later evaluations avoid another full
record walk. Canonical bytes can be reconstructed unchanged when needed;
resource limits and the selected energy/force calculation remain unchanged.

The local kernel sizes temporary integral, Ewald and DFT grid arrays from current memory
headroom. It checks resident memory, virtual address space, the address-space
limit, host availability and applicable cgroup limits. The checks include the
v1 combined RAM-plus-swap limit when present. Linux inactive file
cache contributes only its reported reclaimable allowance. Each block reserves
space for simultaneous arrays and keeps half the remaining headroom available
for native workspaces and allocation overhead. Previous arrays are released
before the next block is selected.

DFT blocks retain the original grid points, weights and screening masks.
Full gradient response blocks precede both the atom-pair weight-derivative tensor
and the AO derivative arrays. Each block retains the original atom identity,
weight response and coordinate response. The partition tensor is released before
AO evaluation. The instance-local RKS/UKS GGA path retains the selected hybrid
and range-separated exchange terms.

The selected CVHF build bounds each Coulomb/exchange cache by its
complete output matrix. The exact-source correction preserves contractions,
screening, tile partitions and write-back thresholds. It retains every possible
tile key, including partial edge tiles. The original numerical environment
remains in custody. The successor environment records the original source,
correction, compiler, linked libraries and resulting binary identities. New
installations use the versioned repository recipe. [Periodic CPU environment](../../../../../docs/using/environments.md#complete-periodic-pyscf-forces-on-linux-x86-64)

Instance-local J/K calls require that build and observe current memory headroom.
They reserve complete output matrices, reordered densities, screening arrays,
integral workspaces and thread stacks. Concurrency stays within the selected
CPU count and decreases when required for those complete arrays. Energy and
three-component gradient routes use their actual density and contraction counts.
The original thread count is restored after each call, including an exception.
Insufficient space for one complete thread refuses before contraction.

The uncoupled potential retains PySCF's Coulomb, exchange and energy metadata.
Electronic energy reads reuse those values without another potential calculation.
Successive direct SCF cycles retain PySCF's density-difference contractions.
This reuse preserves the selected density, Hamiltonian and convergence criteria.

The cold force probe and numerical-control points retain independent initial guesses.
The [relaxation owner](active-state-relaxation.md) can instead reuse a preceding
successful density within one fixed operator. That choice changes only the initial
guess. It retains full SCF convergence, fresh geometry-dependent potentials and
complete energy and gradient evaluation at every geometry.

These blocks cover every selected charge, lattice image, reciprocal vector and grid point.
They preserve the selected basis, functional, cutoffs, mesh and convergence
criteria. A budget that cannot hold one complete item fails explicitly. Memory
observations accompany native entry, grid-block selection, J/K concurrency, SCF iterations and gradient phases.
Small-system equivalence and allocation controls do not establish that a full
enzyme energy and complete gradient fit the selected allocation.

Set `PeriodicForceSettings.maximum_scf_cycles` to `None` to continue the
electronic solve without a total iteration ceiling. The public PySCF kernel
then runs successive growing chunks from its previous returned density, with
each chunk and the cumulative iteration count retained. Acceptance still
requires both the selected energy change and full orbital-gradient tolerance,
followed by an independent check of the returned orbital gradient. A failed
native call or nonfinite return remains a failure. Historical positive integer
selections retain their original single-kernel behavior.

The instance-local CDIIS implementation keeps complete Fock and error vectors
in PySCF's temporary HDF5 storage under the selected worker scratch directory.
This prevents its per-vector in-memory threshold from accumulating many large
arrays in RAM. Every value, dtype, circular slot, subspace size and mixing rule
is preserved; observations record the stored array count and bytes. Scratch
creation or write failures propagate without an in-memory fallback. Binding
requires a new original CDIIS instance; it does not silently replace another
DIIS family or restore a previous solver. Installed classes and global thresholds
remain unchanged. Small numerical comparisons and full-basis storage controls
establish the stated implementation behavior; they do not establish successful
full-enzyme throughput or gradients.

The DIIS extrapolation preserves the original normal arithmetic.
For LAPACK's reported internal eigensolver error, it records the exact matrix
and uses symmetric QR on that same finite Hermitian matrix. It checks the
returned eigenpair residual and orthogonality before applying the original
dependence threshold and mixing coefficients. Other exceptions still propagate.
This internal matrix recovery replays no SCF cycle or native attempt and
changes neither the energy criterion nor the full orbital-gradient criterion.

The molecular constructor independently compares every original Amber mass,
charge, bond, angle, torsion, nonbonded parameter and exception with the selected
OpenMM system. It retains original parameter rows, the complete system digest
and the assignment assessment. System copying uses the complete selected force
objects and retains the original system. The coupled operator combines the
periodic electronic embedding, remaining molecular potential, cross van der
Waals interactions and boundary forces according to the selected catalytic
path. It retains every component gradient and image assignment as well as the
total energy and physical-atom gradient.

The raw derivative unit is `Eh/PySCF-Bohr-0.52917721092-A`. Its identity remains
distinct from the historical ASH Bohr convention. Raw arrays retain their
original values; comparisons use the stated length conversion. The project
local periodic electronic modules preserve their PySCF 2.14.0 attribution,
Apache licence and notice, source hashes and documented changes for complete
MM blocking, spin-density contraction and charged periodic background terms.

Read the original `PeriodicProbeResult` using the exact configuration, complete
representation and native-subwork custody. The reader rechecks the definition,
request, completion and receipt, then authenticates every archived file and
the full array payloads. It reports original operational status, numerical
integrity, authenticated file count and bytes, and unresolved scientific
requirements. A successful call with nonfinite values remains an operational
success with a failed numerical assessment. An actual engine failure retains
its diagnostic and available outputs. A contacted attempt without a confirmed
completion remains unknown and cannot be replayed automatically.

Costs retain measured process CPU time, wall time, worker peak resident memory
and bytes of the actually published native outputs. Peak memory covers the
worker lifetime through the observation; retained bytes count published
payloads, excluding working copies and bookkeeping records. These are execution
costs. Physical elapsed time and reaction rates require their own dynamical
evidence.

The current exposed controls exercise complete input publication, original
return and failure custody, refusal of changed inputs, recovery without replay,
nonfinite arrays and archived-byte corruption. Separate native controls check
the periodic components and project-local module equivalence. Actual full
enzyme cost and derivative qualification remain pending the independently
accepted prepared model.

## References and research

[PySCF 2.14.0](https://github.com/pyscf/pyscf/tree/v2.14.0) supplies the original numerical algorithms.
The local provenance record binds each reused source and its modifications.
[SciPy's eigensolver reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigh.html)
describes the symmetric-QR driver used for the checked DIIS error recovery.
