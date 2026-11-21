# Construct and admit the four initial Gp Amber models

SPDX-License-Identifier: CC-BY-4.0

This stage turns the four complete M1-WT, M1-I95M, V1-WT and V1-I95M heavy
scaffolds into independently assessed, minimized starting molecular models.
It composes PDBFixer mutation, Amber parameterization/solvation and OpenMM
whole-system minimization inside one registered native contact per material.
The retained **relaxed.inpcrd** is the molecular coordinate source used by the
subsequent M50 workflow. The pre-minimization LEaP coordinates remain diagnostic
and correspondence evidence.

Start with the independently accepted [common parent](constructed-geometry-repair.md),
its [four active heavy scaffolds](active-gp-scaffolds.md), and the assessed
[source-bound Amber templates](initial-amber-templates.md). These are new native
constructions with new source identities and receipts. No old experiment result,
configuration shim or native replay is required for their scientific meaning.

## Researcher selections

Call `api.domain_composition.rubisco_response.initial_amber.prepare_initial_gp_amber`
with scaffold and ligand relative paths and their respective artifact writers,
the original RUB component digest, six exact `SourceMember` records, the
selected `GpAmberEngine`, and the complete `GpRepairNumericEngine`. Separate
writers preserve the source storage identities. The numeric stock includes
PDBFixer, OpenMM, NumPy and SciPy plus their complete bundled libraries and
actual interpreter. Authenticate source/tool bytes, versions and licenses in
the selected native environment; a lockfile for the ordinary EL environment
does not stand in for this molecular engine closure.

The canonical `GpInitialAmberInput` version 3.0.0 binds these defaults:

| Choice | Declared default |
| --- | --- |
| Protein and water | ff14SB/parm10 and TIP3P |
| Chemical templates | Exact scoped KCX and keto RuBP4− sources |
| Box and ions | Orthorhombic 10 Å solvent padding; neutralizing Na/Cl |
| Library construction seed | 20261114 |
| Minimizer | Complete original OpenMM forces, optimized CPU, all atoms mobile |
| Construction threads | Eight explicit CPU threads; selectable from one to eight |
| Work limit | 2000 minimization iterations |
| Actual final maximum Cartesian force | At most 1 kJ/mol/nm |
| PME settings | 10 Å cutoff and 1e-6 Ewald error tolerance |
| Geometry policy | Explicit `MolecularGeometryPolicy` in the source |
| Stereocentre degeneracy floor | 0.01 Å³ signed determinant magnitude |

The public preparer exposes the seed, geometry policy, iteration limit, force
threshold, PME settings, `construction_platform` and `construction_threads`.
CPU contexts use explicit thread counts and `DeterministicForces=true`.
Select serial `Reference` only for small numerical oracle controls.
The actual CPU affinity must support the selected thread count.
Author a fresh source when these choices change;
a changed bound cannot relabel an earlier failed result. A finite iteration
limit is a work limit and is never interpreted as convergence.

The six parameter identifiers end in `ff14sb.frcmod`, `kcx.frcmod`,
`kcx.prepin`, `parm10.dat`, `rubp.frcmod` and `rubp.prepi`. The ff14SB member
binds the actual `frcmod.ff14SB` bytes. Scoped KCX aliases and boundary terms
keep bespoke carbamate parameters from overriding ordinary protein types.
All eight KCX, Mg and RuBP sites and all 1,084 original waters remain in the
source census. Histidines initially use HIE; standard charged termini and
ASP/GLU/LYS/ARG ionization are declared. There is no added bulk salt, free-Mg
reservoir or explicit buffer. The downstream 298.15 K and pH 8.0 selections
are not a thermal/proton equilibrium calculation by LEaP.

## Native composition and admission boundaries

1. **Inherited heavy geometry.** Preparation, authoring and worker preflight
   screen every inherited atom for gross contacts, backbone errors and wrong
   protein stereochemistry. Only the 24 declared I95M CG/SD/CE proposal atoms
   are excluded, because the native library replaces those exact coordinates.
   All eight mutation CB/backbone anchors remain screened and fixed during
   mutation placement.
2. **Library mutation.** In each I95M material, PDBFixer applies `ILE-95-MET`
   to all eight declared SSU chains on the selected platform. It reconstructs the mutant
   CG/SD/CE atoms from the retained anchors with the selected seed. The custom
   scaffold Met pose is discarded before this step. Every nonmutated atom,
   element, residue identity and protected ligand/metal/modified residue must
   remain exact. No generic nonstandard-residue replacement or heterogen
   deletion is permitted. WT has an explicit no-mutation record.
3. **Amber chemistry and solvation.** LEaP consumes `library-heavy.pdb`, adds
   all hydrogens, saves the dry topology/coordinates, solvates, neutralizes and
   saves the complete periodic topology/coordinates. KCX terminal H distances
   are derived from their original assigned bond equilibria; the exact changes
   and source/derived hashes are retained. All original named atoms, including
   complete crystal waters, must join one-to-one across solvation and its
   global translation. Inserted ions cannot acquire a water's source identity.
4. **Complete Amber/OpenMM correspondence.** The complete live native force
   snapshot is compared independently with raw Amber masses, charges, every
   bonded coefficient, complete LJ type-pair tables, exclusions and scaled
   1–4 interactions. Unrepresented force terms, missing atoms, substituted
   coefficients and lost zero-interaction branches refuse. This establishes
   parameter assignment, not force-field physical accuracy.
5. **Whole-system minimization.** OpenMM creates the complete unconstrained,
   flexible-water periodic PME system. All atoms are mobile, every original
   force group participates, and the selected `LocalEnergyMinimizer` performs
   the minimization. There is no custom projected pair potential, optimizer
   fallback or construction barrier. OpenMM's requested RMS force target is
   selected maximum/sqrt(3N); the actual final maximum is independently checked.
6. **Exact output admission.** Coordinates are written as `relaxed.inpcrd`.
   The native engine rereads this exact fixed-width projection and evaluates
   energy and forces again at those coordinates. The retained force array
   therefore belongs to the actual downstream restart, not an unrounded
   neighboring endpoint. The independent assessor verifies this binding,
   complete atom/box census, force summary, whole-system geometry, original
   chemical graphs and charges, all hydrogen parent/bond assignments, protein
   stereochemistry and RuBP stereochemistry. Failed geometry or forces prevent
   molecular publication even if the minimizer or LEaP returned successfully.

The whole-geometry screen includes hydrogens and zero-LJ atoms, source-derived
bond/angle strain, all torsions and source-planar improper terms. The declared
defaults catch the 0.348895 Å H–H contact and 0.532982 Å C–H bond in the molecular diagnostic report. These
are gross/strain screens, not comprehensive structural validation or MolProbity.
The source also binds a 0.01 Å³ determinant-magnitude floor for protein and
RuBP stereocentres. All eight keto RuBP C3/C4 centres must retain their
source-defined four-substituent CIP orientation before and after minimization.
The determinant is six times oriented tetrahedral volume; this declared floor
prevents numerical degeneracy and is not a literature-derived structural score.
Read the [standards review](../../../../../docs/release/rubisco-molecular-remediation.md)
for literature validation and remaining chemical/force-accuracy prerequisites.

Every LEaP warning is retained. Missing/ambiguous completion summaries, parameter
errors and unexplained warning counts refuse admission. Only recognized initial
contact/bond warnings can be resolved by a fully passing independent endpoint;
charge warnings additionally require the independently neutral final cell.
Zero exit status or emitted topology files are not a geometry pass.

Independent reading compares geometry disposition, findings, atom census and
policy exactly. Derived floating diagnostics admit only stated roundoff-scale
differences (relative 1e-12; small quantity-specific absolute floors), because
SVD plane residuals need not be bitwise portable across BLAS implementations.
A threshold-side disagreement refuses; the independent raw-coordinate verdict
always controls admission.

## Author, execute and retain

`author_initial_gp_amber` freezes the registered
`rubisco-response.prepare-initial-gp-amber` operation through ordinary recursive
authoring. The current `GpAmberOperationConfig` version 4.0.0 requires actual
producing provenance. It publishes six direct native operands: the complete
source, provenance and four model records, plus the configuration worker input.
The current codec is singular; historical configurations have no compatibility
alias or default-filled interpretation. Read earlier revisions with their
original compatible installation.

Use the returned paths with `api.recursive_execution.run_recursive_wave` or the
supported recursive-development CLI. The operation reserves eight CPU equivalents and 8 GiB
RAM, a 512 MiB source scan and 2 GiB published-output limit. Each model has a
512 MiB complete raw-output allowance. Verify that the actual execution and
storage allocations can honor those declared bounds before native entry.
Optimized CPU construction does not rent or validate a GPU. The
later QM/MM acquisition uses its separately selected CPU/GPU environment.
Its existing PME platform guards remain unchanged.

Archive publication streams compression into the artifact plane's staging file.
Available space must hold the original files, the stored archive and publication metadata.
No separate compressed spool is created. Output ceilings do not establish sufficient storage capacity.

Each model definition permits one complete PDBFixer/Amber/OpenMM construction
contact. The default has no wall-time cutoff; the minimization work limit is
explicit in the source. Process failures, library failures and partial native
returns keep their original stdout/stderr, raw files, completion and receipt.
Uncertain contact supplies no retry authority. Raw archives are read without
reconstructing molecular models or repeating native effects.

The independent assessment's exact file census contains:
`dry.prmtop`, `dry.inpcrd`, `model.prmtop`, `model.inpcrd`, `stdout.txt`,
`stderr.txt`, `library-heavy.pdb`, `mutation-construction.json`,
`force-assignment.json`, `relaxed.inpcrd`, `final-forces-kj-mol-nm.npy` and
`relaxation.json`. The complete archive additionally preserves the engine system,
initial force array, full input stock and construction diagnostics. Partial or
missing selected files make the assessment unavailable; adverse scientific
findings remain adverse.

`map_initial_amber_representation` authenticates the completed unit, repeats
independent assessment, derives original atom identities from the pre-minimization
solvation correspondence, and binds its coordinate identity and array dataset
to **relaxed.inpcrd**. Minimization is allowed to move original coordinates;
source atom identity is retained without pretending those coordinates remained
unchanged. Every downstream M50 model must come through this satisfied mapping.

## Interpreting the construction checks

The focused controls exercise independent calculations and simulated library boundaries. Native acceptance requires the selected installed libraries, original outputs and independent review of every quality and warning finding. The [M50 molecular audit](../../../../../docs/release/rubisco-molecular-remediation.md) defines the prerequisites and evidence required for that investigation.

Construction success leaves active-ensemble, force-accuracy and rate admission
`UNEVALUABLE`. A minimized structure is not an equilibrium distribution,
reactive-state selection, kinetic rate or biological result.

References: [PDBFixer manual](https://github.com/openmm/pdbfixer/blob/master/Manual.html),
[OpenMM AmberPrmtopFile](https://docs.openmm.org/latest/api-python/generated/openmm.app.amberprmtopfile.AmberPrmtopFile.html),
[OpenMM LocalEnergyMinimizer](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.LocalEnergyMinimizer.html),
[ff14SB](https://doi.org/10.1021/acs.jctc.5b00255).
