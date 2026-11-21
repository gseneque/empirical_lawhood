# Execute the common parent and four local Gp constructions

This guide prepares, executes and independently reads the local Gp constructions.
It preserves original input custody and the complete four-material denominator.
Install the [selected local environment](../../../../../docs/using/rubisco-construction-environment.md) before preparation.

## Prerequisites and selections

Read the [common-parent contract](constructed-geometry-repair.md) and [initial-model contract](initial-gp-amber.md).
Retain the original parent supply, assessment, complete native archive, controls and receipt.
Retain their original operator profile and select current storage access if the evidence moved.
A copied supply record alone does not authenticate its original native result.

Select a new writable artifact root through an explicit operator profile.
Select scratch separately and create its parent before execution.
The actual CPU affinity must support eight CPU equivalents for the default operation.
Allow the declared 8 GiB task memory and host headroom.
One task worker is not one CPU equivalent.

Create an application context through `ApplicationContext` or its documented JSON form.
The [application contract](../../../../../src/empirical_lawhood/api/application_contracts.py) owns that operational selection.
Select the executing Python path, project root and operator profile explicitly.
Use separate original-parent and ligand contexts for their original storage identities.
These contexts supply locations and limits, not scientific authority.

Each operation consumes a small JSON request.
Every request requires a fresh absolute `output_directory` beneath the selected artifact root.
Paths named below are absolute unless the field explicitly contains a digest or integer.
Use returned paths for subsequent operations.

Run each selected preparation or reading operation as follows:

```sh
export PYTHONDONTWRITEBYTECODE=1
uv run --no-sync python scripts/operate_gp_construction.py select-engines \
  --context /absolute/external/inputs/construction-context.json \
  --operator-profile /absolute/path/to/operator-profile.json \
  --request /absolute/external/inputs/select-engines.json
```

Replace the operation and request file with the next selected row.
The returned `operation-return.json` records the exact context fingerprint and output paths.
No operation in this recipe launches molecular work.
Native execution remains a separate explicit command.

## Preparation and reading operations

| Operation | Required request fields beyond `output_directory` | Returned result |
| --- | --- | --- |
| `select-engines` | `amber_manifest_file`, `amber_directory`, `site_packages`, `interpreter` | New canonical Amber and numeric engine files |
| `select-parameters` | `members` | Six canonical original parameter records in the required order |
| `prepare-parent` | `original_context_file`, `parent_file`, `assessment_file`, `gp_source_file`, `amber_engine_file`, `numeric_engine_file`, `native_work_directory`. The fresh stock-fragment protocol also requires `parent_repair_protocol` and `maximum_refined_displacement_angstrom`. | Exact selected repair source and authored directory |
| `read-parent` | `authoring_directory` | Original operational report and independently read repair result |
| `prepare-scaffolds` | `repair_authoring_directory`, `gp_source_file`, `case_set_file`, `methionine_file`, `ligand_context_file`, `ligand_directory`, `component_sha256` | Accepted refined-parent package and all four scaffold paths |
| `prepare-models` | `scaffold_directory`, `ligand_context_file`, `ligand_directory`, `component_sha256`, `parameter_source_files`, `amber_engine_file`, `numeric_engine_file`, `native_work_directory` | Complete four-model source and authored directory |
| `read-models` | `authoring_directory` | Original operational report and independent complete four-model result |

For `select-engines`, `interpreter` is the resolved executable path.
The context's `python_executable` remains the path used to invoke the selected environment.
`site_packages` is that environment's actual package directory.

The `members` object has exactly six keys:
`ff14sb.frcmod`, `kcx.frcmod`, `kcx.prepin`, `parm10.dat`, `rubp.frcmod` and `rubp.prepi`.
Each value contains `path`, `sha256` and `original_url`.
Select original bytes and their original provenance.
The preparer derives source identifiers through the owning contract.
It does not infer or download replacement parameters.

The parent and model preparation requests also accept `maximum_iterations`, `construction_seed` and `construction_threads`.
Their defaults are 2000, 20261114 and 8. The fresh v5 parent requires a positive integer iteration budget and keeps the seed field fixed at 20261114. There is one deterministic placement per terminal sequence.

`prepare-parent` authenticates original completion and receipt custody.
It verifies every original archive member before copying the heavy coordinates and atom origins.
It repeats the original source/origin assessment before deriving the new repair source.
Missing original custody stops this operation before new molecular entry.

For the fresh v5 geometry challenge, prepare a complete request using the original custody paths and your selected fresh output directories. The example declares a 0.25 Å maximum Cartesian displacement norm for each inherited Glu213 carboxylate atom. The largest historical CD–OE1 shortfall relative to Amber equilibrium was 0.208089 Å. Record the rationale for the displacement cap before authoring. The force, geometry and chemical screens retain their own thresholds. [Common-parent protocol and original measurements](constructed-geometry-repair.md#declare-the-input-and-native-tools)

```json
{
  "output_directory": "/absolute/external/artifacts/fresh-parent",
  "original_context_file": "/absolute/external/inputs/original-parent-context.json",
  "parent_file": "/absolute/external/originals/geometry-reuse-supply.json",
  "assessment_file": "/absolute/external/originals/pre-amber-geometry-integrity.json",
  "gp_source_file": "/absolute/external/originals/gp-source.json",
  "amber_engine_file": "/absolute/external/inputs/amber-engine.json",
  "numeric_engine_file": "/absolute/external/inputs/numeric-engine.json",
  "native_work_directory": "/absolute/external/scratch/fresh-parent",
  "parent_repair_protocol": "gp-1bwv-amber-terminal-fragments-v1",
  "maximum_refined_displacement_angstrom": "0.25",
  "maximum_iterations": 2000,
  "construction_seed": 20261114,
  "construction_threads": 8
}
```

Use a positive finite decimal string for the displacement cap. The fresh source must have version 5.0.0 and the operation must be `rubisco-response.refine-gp-terminal-fragment-geometry@5.0.0`. Check the returned source fingerprint, engine files, seed, threads, iteration budget and geometry policy. The two short LEaP calls use the authenticated ff14SB and amino-acid libraries. The SSU side chain uses the selected numeric engine's MET template. Preparation checks that the seven named files appear in the selected engines. [Exact stock and geometry selection](constructed-geometry-repair.md#declare-the-input-and-native-tools)

To read the original v3 result, pass its original authoring directory to `read-parent`. Its operation is `rubisco-response.repair-gp-constructed-geometry@3.0.0`. For an explicitly selected guarded PDBFixer comparison, use `gp-1bwv-glu213-carboxylate-v1` and a displacement cap. This produces source 4.0.0 under `rubisco-response.refine-gp-glu213-geometry@4.0.0`. Omitting the selector and cap or using `constructed-only-v3` without a cap selects the legacy v3 construction scope.

`prepare-scaffolds` independently reads the repair and publishes only an accepted common parent.
It passes that exact accepted result to the scaffold owner within the active native-reading scope.
Failed or unavailable parent findings prevent dependent preparation.
Do not substitute the historical unrelaxed template parent.

`prepare-models` delegates complete scaffold, ligand, parameter and engine validation to the initial-model API.
It preserves all four models and derives their native roster through the registered operation. For a scoped v4/v5 parent it reads the accepted parent's whole-system geometry policy and carries the identical nominal-Amber planarity treatment and authored limits into all four initial Amber constructions.
No temporary identity-construction script is required.

## Native execution

Use the `authoring_dir` returned inside `authored` for each native stage.
Prepare a separate fresh attempt directory for operational logs.
Run the common-parent stage first:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /absolute/path/to/checkout \
  --operator-profile /absolute/path/to/operator-profile.json \
  campaign recursive-development-run \
  --authoring-dir /absolute/external/artifacts/parent/authoring \
  --workers 1 \
  --attempt-dir /absolute/external/checks/parent-attempt
```

Read that result with `read-parent`. A v5 fragment refusal retains `terminal-fragments.json` with the available original source records and its native error. At the subsequent initial chirality/peptide gate, either scoped protocol retains `initial-terminal-geometry.json` with counts, violations and coordinate digests. A refusal there precedes complete-parent Amber assignment and minimization. Retain the actual cost and all four unavailable descendant positions if preparation stops.
After a satisfied parent, run `prepare-scaffolds` and `prepare-models`.
Execute the returned four-model authored directory with the same shared command.
Read its exact original result with `read-models`.
Retain raw errors, warnings, stopping outcomes and every failed or unavailable material.
Do not replay uncertain native contact under a new request or path.

## Scientific readout

For v5, report the accepted or rejected placement, every selected anchor, all 24 covalent junctions, packing contacts and the pre-minimization stereocentre and peptide denominators. On either scoped protocol, report which subsequent checks the contact reached. For a completed parent these include the fixed-bond feasibility denominator and every violation, all 24 signed source-relative carboxylate displacement vectors, the largest norm and cap, and the applicable, checked, undefined, exempt, zero-amplitude and violating impropers. Preserve the original v3 constructed-only result under its own policy and receipt.
The initial-model readout concerns the exact relaxed restart for each material.
Report M1-WT, M1-I95M, V1-WT and V1-I95M even when some are unavailable.
Report zero independent biological replicates.

Use the independent assessment's force maxima, geometry findings and warning dispositions.
Report external structural-quality coverage separately when it exists.
The built-in geometry screens are not a MolProbity assessment.
Construction acceptance supplies no equilibrium ensemble, force-field accuracy, kinetic rate or M50 response result.
The later [molecular mapping](initial-gp-amber.md#native-composition-and-admission-boundaries) requires an independently satisfied exact restart.

Treat v5 as a prospective geometry challenge. A held-out 9RUB development control missed the N- and C-terminal Cα coordinates by RMSDs of 38.08 Å and 14.99 Å, including a misplaced N terminus that passed the local anchor and packing checks. Before using a parent to support a physical observable, require independent terminal calibration or demonstrate insensitivity of that observable across justified placements. Evaluate the inherited active-site coordinates against available density and the selected chemistry. [Control and production interpretation](constructed-geometry-repair.md#native-acceptance-still-required)

## Select an inherited-site coordinate comparison

For the CAP-bound 1BWV parent, the `first-shell` selection transfers the coordinates of KCX201, Asp203, Glu204, Mg490 and CAP491 from the PDB-REDO refinement in each original LSU active site. These numbers are author residue identifiers. The `acid-sidechains` control transfers only the two acid side chains. Both selections use original atom identifiers, alternate locations, occupancies, the crystal frame and the two original assembly operators. The resulting packets contain respectively 408 and 72 coordinate pairs. The original water population is carried by the deposited source.

Select the retained, uncompressed [1BWV coordinates](https://files.rcsb.org/download/1BWV.cif) and [PDB-REDO coordinates](https://pdb-redo.eu/db/1bwv/1bwv_final.cif). Supply a new output file.

```sh
uv run --no-sync python3 scripts/select_gp_crystal_sites.py \
  --deposition "$original_1bwv" --refinement "$redo_1bwv" \
  --selection first-shell --output "$new_site_selection"
```

The printed SHA-256 identifies the exact source and selected assembly coordinates. Read the packet independently against both source files, the observed diffraction amplitudes, the inherited Amber terms, linked peptides, inhibitor stereochemistry, metal donors and original ordered waters. The packet supplies an inherited-coordinate hypothesis. A complete parent also requires the terminal placement, its qualification for the intended use and the combined construction and readback.

## References and research

The [public preparation owner](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/construction_preparation.py) binds tools and original parent custody.
The [operator recipe](../../../../../scripts/operate_gp_construction.py) composes supported APIs and retains returned paths.
The [common-parent contract](constructed-geometry-repair.md) and [initial-model contract](initial-gp-amber.md) own scientific selections and assessment limits.

## Independent all-atom structural validation

Run the [pinned local MolProbity workflow](../../../../../docs/using/rubisco-molprobity.md) first on the dry CAP-bound common parent via `export-parent`, then on the four matched solvated, keto-RuBP constructions via `export`. Each selection has its own original material, topology, coordinates and receipt. The `run` and `assess` commands retain seven component populations, all protected sites and missing measurements. A rejected construction retains its original disposition even when an independently assigned endpoint permits diagnostic inspection.
