# Full Gp WT/I95M heavy-coordinate preparation

SPDX-License-Identifier: CC-BY-4.0

The supported
[preparation and reader](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/active_scaffolds.py)
produce four complete heavy-coordinate hypotheses: M1-WT, M1-I95M, V1-WT and
V1-I95M. They do not establish active-ensemble, parameter or kinetic admission.
Follow the [physical supplier specification](physical-rate-supplier-v1.md)
for those later calculations.

## Inputs and original custody

Supply a `RubiscoCaseSet` with the two nominated candidate cases, an independently accepted
`GpRefinedGeometrySupply`, its exact `PreAmberGeometryIntegrity`, and
the returned heavy-PDB and atom-origin files. Authenticate current access and
the original producing receipt and custody before preparation or retained read.
The API validates the original typed joins, geometry hashes and complete
case/material correspondence. It does not mint a replacement native receipt.

The parent must be the complete assessed M1-WT assembly. Original missing LSU
segments must already have been constructed and assessed in that parent; this
preparation never substitutes a truncated crystallographic chain. Supply the
exact Gp structural source, an explicit complete methionine heavy template and
the independently assessed [keto RuBP tetraanion](rubp-tetraanion-preparation.md).
Retain template revisions, original bytes and licenses with source custody.

## Repaired common parent

For a repaired parent, use `prepare_refined_gp_parent` and `read_refined_gp_parent`
in the [refined-parent API](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/refined_geometry.py).
They authenticate the actual repair receipt and independently assess its original endpoint.
A failed, incomplete or geometrically invalid repair cannot supply its endpoint as a refined parent.
The resulting `GpRefinedGeometrySupply` retains the original deposited source and atom origins.
The scaffold API accepts this supply with its exact parent assessment and returned coordinates.
Its package retains the actual repair receipt as lineage.
A successful repair does not establish an active ensemble or a physical rate.

## Required library-built parent

New authoring requires the independently assessed
[PDBFixer/Amber/OpenMM construction](constructed-geometry-repair.md) through
`GpRefinedGeometrySupply`. An unrelaxed original or pure terminal-template
parent cannot bypass that native construction and its force/geometry checks.
There is no `terminal_template_sources` authoring switch or automatic fallback.
Source records and atom origins remain source custody; the new construction
carries its own actual native receipt.

## Construction and independent checks

The [constructor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/gp_active_scaffold.py)
retains every unchanged parent atom and its exact Decimal coordinates. All
eight CABP molecules are replaced by newly placed keto RuBP heavy graphs.
A proper least-squares rigid transform fits all eighteen shared heavy names
to each original inhibitor site, preserving the ligand template's bond lengths
and stereochemistry. It is an unrelaxed starting pose, not a binding result.

The M1 parent already contains the source V1-to-M substitution in every SSU.
V1 arms transplant the original source Val side chains into their retained
backbone frames. Both I95M arms declare the complete side-chain identity in all eight SSUs.
The supplied Met template provides a deterministic proposal in the N/CA/CB
frame for pure correspondence assessment. It is not a native force operand.
The mandatory [initial Amber operation](initial-gp-amber.md) discards all 24
CG/SD/CE proposal coordinates and uses PDBFixer `applyMutations` in every SSU,
then completes Amber chemistry and whole-system OpenMM minimization. Inherited
backbone/CB anchors remain exact during library mutation. No unnamed sequence
change is allowed.

The separate
[assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/gp_active_scaffold_assessment.py)
checks all parent serials, exact permitted removals, complete additions, full
sequences, elements, site/Mg/KCX correspondence, ligand internal distances,
stereochemistry and retained placement diagnostics. It checks side chains in
independently derived local coordinates, without the constructor's transplant
or fitting functions. It reports all ligand/environment contacts below the
declared 1 Å diagnostic cutoff; absence of such contacts does not establish
acceptable energy, forces or physical geometry.

## Retained outputs and limits

Select an explicit guarded artifact root and output-relative directory. Use
the returned paths for the copied inputs, four `scaffold.json`, `model.pdb`
and `assessment.json` members, and `report.txt`. PDB coordinates are a rounded
format projection; canonical scaffold coordinates retain the full declared
precision. The complete manifest retains the original geometry-receipt lineage.

`read_active_gp_scaffolds` validates every manifest member and independently
reassesses the original coordinates. It never repeats construction, hydrogen
placement, minimization or another native operation. Altered siblings refuse
the read even when the requested report itself has not changed.

The next mandatory stage is the complete initial Amber construction, whose
independent molecular mapper uses the accepted relaxed restart. Hydrogens,
source parameter assignment, solvation, all-atom geometry and final maximum
force are assessed there. Six proton-allocation/Mg-water alternatives,
nonstandard force-field physical accuracy, assay activities, boundary maps,
equilibrium sampling and the physical supplier still require their own evidence. The models contain zero new physical rate contrasts
and establish no WT/I95M forecast or independent biological replication.
