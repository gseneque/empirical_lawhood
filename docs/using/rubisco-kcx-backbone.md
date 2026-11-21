# Read the Gp KCX backbone neighborhood

The original CCTBX Ramachandran traversal can skip a modified residue and its immediate neighbors because its protein-triple iterator does not return a standard residue triple there. The Gp 1BWV catalytic region has the prepared sequence PHE208–VAL209–KCX210–ASP211–ASP212 on each of eight large subunits. KCX is the chemically carbamylated lysine. A separate observation can measure the missing backbone angles while preserving each deposited component and the full native result. [Native structural-validation workflow](rubisco-molprobity.md)

## Inputs and command

First export the authenticated dry parent or the four matched children and obtain the original local CCTBX component run. Select one available exported material, its pinned export and the corresponding directory containing the original `components.json` and `ramalyze.jsonl`. Obtain the SHA-256 of `components.json` from the original component return or an independently retained diagnostic handoff. A complete matched campaign keeps one row per material, including unavailable constructions. Use a fresh absolute destination for each available material. [Pinned export and native validation](rubisco-molprobity.md#run-locally-or-transfer-the-pinned-export-to-another-authorized-operator)

```bash
uv run --no-sync python scripts/assess_gp_kcx_backbone.py \
  --export-directory "$validation_export" --export-sha256 "$export_sha256" \
  --material "$material_name" \
  --component-directory "$material_component_directory" --components-sha256 "$components_sha256" \
  --runtime-prefix "$molprobity_prefix" --runtime-receipt-sha256 "$runtime_sha256" \
  --timeout-seconds 180 --output-directory "$kcx_backbone_output"
```

The command checks the selected export's CIF, map and native coordinate digest, all original Ramachandran rows, the installed CCTBX and empirical reference tables, and the source of both the native calculation and the reviewer. It accepts a separately pinned, partial conformation-only component return when its complete Ramachandran rows and input identities are present. The original construction disposition travels with the result. [Supplement operator and independent reader](../../scripts/assess_gp_kcx_backbone.py)

## Angles, reference classes and controls

The Python operation takes a `BackboneSelection`. The combined forecast reader
uses the Ramachandran rows already read from the selected native component to
check the KCX flanks. Each component retains its original denominator. [Backbone assessment](../../src/empirical_lawhood/api/domain_composition/rubisco_response/kcx_backbone_read.py)

Each position requires the five identified native atoms C of the preceding residue, N/CA/C of the central residue, and N of the following residue. All four edges, including both peptide C–N links, must occur in the original Amber heavy covalent graph. The reader preserves native atom indices, elements, residue identities and the actual chemical names. It forms φ from the first four atoms and ψ from the last four. For a periodic child it unwraps each covalent edge in the physical unit cell and reports the image shifts. The dry parent's isolated CCTBX reader box has no physical periodicity.

The selected CCTBX implementation calculates signed dihedrals in degrees and evaluates the same `RamachandranEval.evaluate` reference table and `ramalyze.evalScore` categories as the native program. An independent signed plane-normal calculation checks each angle. Each chain also requires PHE208 and ASP212 to reproduce their own original native φ, ψ, table, score and category. A missing atom, original bond, unique periodic image or matching pair of flanking controls leaves that chain or position incomplete. The report retains all 24 assigned middle positions and all 16 control positions. [Topology join and CCTBX implementation](../../src/empirical_lawhood/adapters/rubisco/rubisco_response/kcx_backbone_driver.py)

| Position | Selected empirical reference | Scope |
| --- | --- | --- |
| VAL209 | CCTBX Ile/Val | Standard valine backbone with the actual KCX neighbor |
| KCX210 | CCTBX general, the class for an unmodified non-pre-Pro lysine | Parent-Lys proxy. Transfer to a carbamylated lysine remains unevaluable. |
| ASP211 | CCTBX general | Standard aspartate backbone with the actual KCX neighbor |

The output retains the raw table value and the native display score, which is 100 times that value. Under the selected CCTBX 2026.10 rule, raw values ≥0.02 are Favored. General-class values from 0.0005 up to 0.02 and Ile/Val values from 0.001 up to 0.02 are Allowed. Smaller values are Outliers. A favored KCX proxy gives a conditional description of its backbone angles. It cannot qualify the modification's chemical geometry, coordination, rotamer or empirical transfer.

## Historical inhibited-parent control

The native parent had **4,992 of 5,016** intended Ramachandran positions, comprising 4,680 Favored, 235 Allowed and 77 Outliers. The omitted 24 were exactly the named VAL/KCX/ASP positions on A/C/E/G/I/K/M/O. All 16 standard VAL/ASP supplemental readings and all eight separate KCX proxy readings were Favored. All 16 flanking native controls matched. The symmetry-related pairs agree at the precision shown below. Each cell gives signed φ, ψ in degrees.

| Assembly chains | VAL209 standard | KCX210 parent-Lys proxy | ASP211 standard |
| --- | --- | --- | --- |
| A and I | −134.798, +161.333 | −143.907, +159.997 | −73.209, +150.222 |
| C and K | −133.923, +162.109 | −144.226, +160.069 | −73.619, +149.861 |
| E and M | −134.914, +161.289 | −144.004, +159.900 | −73.273, +150.278 |
| G and O | −134.015, +162.036 | −144.300, +160.033 | −73.579, +150.011 |

The historical construction remains **FALSIFIED**. `kcx-backbone.json` records the released scope, native row digest, missing native positions, all 24 supplementary rows, all 16 control rows, and source/runtime digests. `original-cctbx-supplement.json` retains the separate supplier's observations. Use the original native population and categories for the native Ramachandran and MolProbity scores. The four active constructions and a chemical validation for KCX require their own evidence.
