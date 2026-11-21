# Independent MolProbity validation of matched Gp constructions

Validate the relaxed, solvated M1-WT, M1-I95M, V1-WT and V1-I95M constructions in their original storage context. Each row represents one candidate material and processing choice. These four rows supply zero independent biological replicates. A completed validation can identify damaged geometry in an attempted model. It cannot establish biochemical turnover, gas specificity, an activated ensemble, or the WT/I95M difference.

## Check the dry common parent first

Use `export-parent` on the original completed library-repair authoring wave. This selects the single inhibited M1-WT 1BWV reference parent. The parent has retained CAP (CABP), carbamylated lysine, Mg, and original waters. Its coordinates come from the original full, double-precision `final-coordinates-nm.npy`, converted once to Å and joined to `dry.prmtop`, the exact selection and original atom-origin records. The rounded heavy-atom PDB cannot supply this coordinate array. The parent physically has no periodic box. The reader uses an isolated P1 box with side lengths equal to the Cartesian spans plus 40 Å so CCTBX can process the unchanged Cartesian coordinates. The atom map records both the null physical cell and this explicitly computational cell. Protected site labels join the eight distinct original KCX/CAP/Mg triples by their pre-repair geometry; this association describes placement, not a measured Mg bond.

```bash
uv run --no-sync python scripts/validate_gp_molprobity.py export-parent \
  --context "$context" --operator-profile "$profile" \
  --authoring-directory "$repair_authoring" --output-directory "$parent_validation_export"
```

Use the `run` and `assess` commands below with that export directory, its SHA and two distinct fresh destinations. The single-parent and four-child rosters have distinct authenticated tags. A formal parent or child construction rejection remains `FALSIFIED` even when exact diagnostic coordinates can be exported and structural rows evaluated. If original atom correspondence cannot be independently established, the row retains its failure and its missing measurements.

## Select and export the four matched children

Use the [local construction workflow](rubisco-construction-environment.md) to select the original application context, operator profile, published scaffold directory and recursive Amber authoring directory. Each output directory below must be a fresh absolute path under that application storage profile. The caller retains its returned SHA-256 independently with the original request or evidence record. The local reader refuses stale, swapped or truncated material when a supplied pin disagrees. Hashes identify bytes; the original storage and handoff provide their custody.

```bash
uv run --no-sync python scripts/validate_gp_molprobity.py export \
  --context "$context" --operator-profile "$profile" \
  --authoring-directory "$amber_authoring" --scaffold-directory "$scaffolds" \
  --output-directory "$validation_export"
```

The exporter authenticates the original wave, all four scaffold records, the completed native contact/receipt and original bounded archives. The original topology, preminimization solvation correspondence, and complete scaffold atom table assign the relaxed restart to atoms and residues. A preminimization coordinate file cannot supply the endpoint. Each exported row names its material, scaffold, original native topology and relaxed-restart digests, chemical graph, assessment and task receipt. An unavailable row remains in the four-material ledger.

Each exported child has a full explicit-hydrogen `model.cif` and `atom-map.json`. mmCIF avoids PDB serial, chain and coordinate-width limits. Decimal round-trip formatting preserves the original binary64, native-order Å coordinates. The six original cell parameters are retained in Å and degrees. The CIF expresses the simulation box in P1 and provides unit occupancies and zero B values for the single model. These are exchange conventions, unrelated to diffraction. New solvent and ion viewer locators have null original author identifiers. The atom map records Amber component names alongside the CCTBX exchange aliases for histidine, cysteine, water and counterions. Original explicit hydrogen positions remain part of the coordinate digest. A parallel native-name array keeps the reversible, index-by-index report-name mapping. For the keto RuBP tetraanion the report uses H11/H12/H3/H4/H51/H52 for Amber H1C1/H2C1/HC3/HC4/H1C5/H2C5. Internal KCX backbone HN1 maps to H. All 30 native CAP atom names in the retained inhibited control already match the selected geostd CAP names. These aliases preserve the original coordinates, covalent graph and atom count; a duplicate label refuses export.

The prepared scaffold chain/position identifies each validation residue. It is distinct from original PDB author numbering. The recorded protected material includes all eight SSU processing positions 1 and substitution positions 95 (1BWV author 112), all eight LSU Glu213 positions (author 204), and the carbamylated lysine at LSU210 (author 201), keto RuBP and Mg at all eight sites. An atom with no source author position keeps that absence. The protected census also labels positions 1–14 and 487–493 of each LSU, a total of 168 originally modeled terminal residues. For each original SSU95 heavy-atom group and each site Mg, `critical_heavy_neighbors` records every other residue with a heavy atom within 5 Å, its closest two native atom indices and distance in Å. This is an authored inspection radius for the interface and metal vicinity. It uses nonperiodic distances for the parent and nearest periodic images in the child's original cell. For each `native_atom_indices` pair, read the atom's residue index from `atoms[i]`, its full source name from `native_atom_names[i]` and the prepared chain/position from `residues`. Join that heavy-atom key to the parent’s original `atom-selection.json` and `atom-origin-provenance.json`, or to the child's pinned original scaffold. The provenance distinguishes observed, constructed, refined and Amber-added atoms, including hydrogens with no deposited original. Individual results and missing terms carry the neighborhood labels. A distance alone does not qualify a contact as chemically functional.

## Run locally or transfer the pinned export to another authorized operator

Use the [repository installation and verification guide](rubisco-molprobity-environment.md) to select the Linux CCTBX distribution with its version-matched monomer, geometry and rotamer data and exact installation receipt. The normal application interpreter remains in the project environment. The following command launches the selected validator's own Python inside its own prefix. A valid prefix may be selected by its absolute location. Every material has an explicit positive elapsed-time ceiling in seconds. The wrapper runs the cases serially, checks the installation before and after the batch, reads original coordinates again, and retains the native log, full result rows and component failures. Four assigned constructions do not require four simultaneous high-memory contact calculations.

```bash
uv run --no-sync python scripts/validate_gp_molprobity.py run \
  --context "$context" --operator-profile "$profile" \
  --export-directory "$validation_export" --export-sha256 "$export_sha256" \
  --runtime-prefix "$molprobity_prefix" --runtime-receipt-sha256 "$runtime_sha256" \
  --timeout-seconds "$seconds_per_material" --output-directory "$native_validation"
```

Add a repeated `--restraint /absolute/path/component.cif SHA256` when selecting a custom monomer restraint dictionary. The wrapper copies and authenticates its complete bytes and passes the CIF to CCTBX. Independently check the chemical definition, element/atom names, bond order, chirality, protonation and intended energy types against the selected species. The stock CCD RUB entry describes neutral C₅H₁₂O₁₁P₂. The locked CCTBX geostd RUB restraint is a distinct 26-atom −4 species. Compare its bijective atom/element list, formal charge, bond order and bonded atom pairs to the declared Amber source graph; account for polymer links when reviewing KCX. A ligand code match cannot qualify the selected keto tetraanion or its metal environment. Coverage of all native bonded heavy-atom terms is an additional, measurable condition. [RCSB RUB entry](https://www.rcsb.org/ligand/RUB)

The CCTBX driver re-joins every parsed atom, element and coordinate to its native-order position, including H, water and counterions. It obtains all available protein rows, all empirical bond and angle rows, and Probe2 serious atom-pair rows. It requests the submitted hydrogen positions, disables Asn/Gln/His flips, and uses nuclear X–H distances for the Amber coordinates. The bond/angle and contact readers check the actual processed structure again. CCTBX orthogonalization can perturb Cartesian last bits when it builds empirical restraints. The bond/angle driver compares the original point at every matched atom, refuses any component change exceeding 10⁻¹⁰ Å, restores the submitted binary64 values, verifies their exact digest and supplies those exact points to the empirical calculation. The raw component receipt records corrected-atom count and largest roundoff. Contact scoring requires the actual H-retained processed model to match the exchange exactly. An unreported processed population leaves that component unresolved. Only a successful native return supplies measured values. A timeout preserves previously flushed component files and an incomplete model disposition.

## Read the original result independently

```bash
uv run --no-sync python scripts/validate_gp_molprobity.py assess \
  --context "$context" --operator-profile "$profile" \
  --export-directory "$validation_export" --export-sha256 "$export_sha256" \
  --run-directory "$native_validation" --run-sha256 "$run_sha256" \
  --runtime-receipt-sha256 "$runtime_sha256" --output-directory "$validation_review"
```

The reviewer checks both request pins, the original four model/coordinate/topology joins, settings, driver revision, selected restraint bytes, logs and individual result-file digests. Each returned outlier identifies its original result row, native atom or residue indices, residue identities and protected site markers. Read the missing native keys, protected-site and native failure information alongside the scores. These outputs are development-visible structural diagnostics.

| Component | Assigned population and independent reading |
| --- | --- |
| Ramachandran | All internal protein positions with preceding and following residues. Count Favored, Allowed and Outlier separately using CCTBX's residue-class-specific reference distributions. A missing eligible residue is visible even when zero outliers were returned. |
| Rotamer | All residues whose standard side chain has a CCTBX reference rotamer distribution. Keep native Favored, Allowed and Outlier. Gly/Ala have no such side chain. Unusual chemistry such as KCX needs its own evidence. |
| Cβ | Every non-Gly protein position. Flag deviation ≥0.25 Å. Unsupported modified residues remain missing from this intended geometry check. |
| Peptide ω | All protein positions after each chain's first. Report non-Pro cis and twisted peptide flags and count cis-Pro separately. |
| Bonds and angles | All native heavy covalent pairs between protein/ligand atoms and the triples they define. Compare with empirical CCTBX conformation-dependent-library proxies and flag absolute deviations ≥4 reference σ. Missing native terms or extra organic heavy terms leave coverage unresolved. Version-specific tables and all provided empirical rows, including applicable extra H terms, remain bound to the selected engine. |
| Probe2 clashscore | Count serious nonbonded overlap ≥0.4 Å, including explicit H under the nuclear convention. Check the reported serious pair count and score against 1000 × clashes / native non-water source atoms. Original waters are present in the input; Probe's source selection excludes water. A zero list requires a finite score, a positive verified denominator and the original processed H/atom census. |

`COVERED` describes the declared structural triage only. The automatic clean disposition requires all seven assigned components to return their selected populations with no review flags. A flag produces `REVIEW_OUTLIERS` when coverage is complete. A component with missing coverage produces `UNEVALUABLE`, and its observed outliers remain visible. Read individual outliers in their structural context. A genuine cis peptide or unusual strained geometry can require evidence to interpret. Whole-model percentages can conceal a defect copied into eight sites. The Mg coordination, ligand/protonation state, chemistry of the catalytic environment, active ensemble and rate forecast need additional evidence even when all measured empirical geometry is clean. The reader reconstructs CCTBX’s overall MolProbity score from the verified Probe2 non-water atom population and the exact residue populations returned by native Ramachandran and rotamer analysis. When stock CCTBX omits assigned residues, `reported_population_score` describes its scored population, `score` stays null and `residue_populations` gives both denominators. Supplementary and proxy values never enter the native score. Report its three inputs and the per-site findings together. The computed materials have no independently measured diffraction resolution for a resolution-matched percentile. Map-fit validation needs its own experimental data. CaBLAM, empirical chirality and Asn/Gln/His flip suggestions can be acquired as separately identified supplemental checks. [CCTBX implementation and documented components](https://cctbx.github.io/mmtbx/mmtbx.validation.html) · [MolProbity methods paper](https://doi.org/10.1002/pro.3330) · [Phenix MolProbity tutorial](https://phenix-online.org/documentation/tutorials/molprobity.html)

## LBL interactive service

LBL's MolProbity Next service offers all-atom contacts, protein conformation, covalent and other geometry, optional supplied restraint CIFs and interactive inspection. Under the site's documented options, select preservation of existing hydrogens, the intended X–H convention, no flips, and full bond/angle detail for a large structure. A rehydrogenated or flipped derivative has a distinct coordinate identity. For an oversized structure, any separately prepared view needs its own atom census and cannot stand for complete-solvated-material coverage. [LBL validation guide](https://molprobity.lbl.gov/help/)

The local command makes no upload. The LBL site forbids scripted/batch uploads. Its service stores submissions and results temporarily, shares access with anyone possessing the unique results URL, and describes logging and a seven-day retention period. An authorized interactive submission or external Phenix PDF may supply supplemental evidence if its exact inputs, settings, version, raw report and qualified site coverage are retained. The automatic reviewer accepts the original per-component records from the pinned local CCTBX driver. [LBL service](https://molprobity.lbl.gov/) · [LBL data/privacy statement](https://molprobity.lbl.gov/privacy/)

## Historical parent control and practical coverage

A read of the original CPU parent attempt 02, independently reassessed from its completed archive, supplied a nonperiodic CAP-bound control. All 83,532 atoms, including 42,128 H atoms, were matched in 6,148 residues. The parent remains `FALSIFIED`. Its final native nm-coordinate NPY SHA-256 was `76d9d20b4d20f87fbdbf7ddb912680ea9c788ebfeaa2f4b84c873736024eaf23` and the native-order Å-array SHA-256 was `25d5e173526cea6b03a143a7bd59bb5eff0b2244eeaab26464c6465887c35754`. The external reader recovered those exact coordinates. Only the four protein-conformation components were acquired on this historical parent.

| Component | Returned / assigned | Observations | Flags in the 168 originally modeled LSU-terminal residues |
| --- | ---: | --- | ---: |
| Ramachandran | 4,992 / 5,016 | 4,680 favored, 235 allowed, 77 outliers | 48 / 77 |
| Rotamer | 4,224 / 4,224 | 3,601 favored, 331 allowed, 292 outliers | 31 / 292 |
| Cβ | 4,680 / 4,680 | 74 deviations ≥0.25 Å | 56 / 74 |
| Peptide ω | 5,032 / 5,032 | 4,993 trans, 24 twisted, 7 cis non-Pro, 8 cis-Pro | 23 / 31 concerning ω values |

The 24 missing stock Ramachandran positions are Val209, KCX210 and Asp211 in each LSU. The missing rows surround the carbamylated lysine at every catalytic site. The [separately identified backbone supplement](rubisco-kcx-backbone.md) found favored values for all 16 surrounding Val/Asp torsions and all eight declared parent-Lys/general proxy evaluations. The latter lack a KCX-specific empirical distribution. The stock result retains the original 24 missing rows. None of the four components returned an outlier centered on an SSU95 residue or in its 5 Å heavy-atom neighborhood. Four rotamer and two Cβ flags touched a 5 Å Mg neighborhood. The historical full seven-component assessment stays unevaluable. The original 1BWV parent chemistry and matched fresh children have different assigned materials. [Current local construction workflow](../../programmes/biology/photosynthesis/workflows/rubisco-response/local-cpu-construction.md)

Two separate 49-atom explicit-H, three-residue software controls exercised all seven CCTBX components with the version-matched reference data. One deliberately displaced a side-chain atom to create a serious contact. These controls tested positive outlier detection, the original non-water clashscore denominator and covalent-row coverage. They contain no Gp acquisition.

## Check that the selected preparation can meet its target

In the historical 1BWV Gp parent, an atom-level comparison against the deposition showed that a mask releasing the terminal atoms and 24 Glu213 atoms retains at least 260/4,224 poor rotamers, 24/4,992 Ramachandran outliers and 18 Cβ deviations. Six fixed findings touch the Mg environments at LSU Asp212 (author Asp203). More minimization within that mask cannot move those atoms. A genuinely MolProbity-quality whole model needs an evidence-backed decision on the inherited source and the modeled termini before the four active materials are constructed. Record justified unusual geometry and report any global metric outside its target. [MolProbity summary cutoffs](https://molprobity.lbl.gov/help/) · [Deposited activated structure](https://www.rcsb.org/structure/1BWV)

For an inherited finding, compare the original asymmetric unit and density against a re-refinement with the same chemical state. On 1BWV, the PDB-REDO model returned 69/2,032 rotamer outliers, 8/2,412 Ramachandran outliers and zero Cβ deviations on the original observed ASU population. It corrected the local Asp203 rotamer/Cβ flags and Glu204 bond distances, and models 508 waters compared with 542 in the deposition. The deposited reflection amplitudes lack original free-set labels. PDB-REDO supplies its own flags and map coefficients. Preserve the source, per-atom mapping, waters, test-set provenance and local density checks for any revised physical selection. [Deposited reflection file](https://files.rcsb.org/download/1BWV-sf.cif.gz) · [PDB-REDO coordinates](https://pdb-redo.eu/db/1bwv/1bwv_final.cif) · [Maps and flags](https://pdb-redo.eu/db/1bwv/1bwv_final.mtz)
