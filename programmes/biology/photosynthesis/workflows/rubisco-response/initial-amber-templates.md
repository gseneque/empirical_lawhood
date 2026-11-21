# Check initial Gp nonstandard residue templates

SPDX-License-Identifier: CC-BY-4.0

This guide describes the initial RuBP and carbamylated-lysine template checks.
It separates chemical correspondence from force-field and reactive-state accuracy.
Use the original source bytes and the independently assessed keto RuBP graph.

## Read and assess the templates

The Python owner is
`adapters.methods.rubisco_response.amber_template`.
`read_amber_template` accepts an authenticated `SourceMember` and an explicit
`template_id`. It reads the selected Amber internal-coordinate format without
native imports or coordinate construction.

`assess_initial_templates` compares both templates with the selected
`RuBPTetraanionPreparation`. It checks every atom, element and covalent edge.
It also checks carbonyl/carbamate types, improper tuples and total partial charge.
The ligand's independent chemical assessment must first pass.

The original RuBP source contains 26 atoms and 25 covalent bonds.
Its partial charges sum to −3.999998 e.
The original KCX peptide template contains 23 atoms and 22 internal bonds.
Its partial charges sum to −1.000000 e.
The reader preserves all original charge values without normalization.
The charge-sum comparison permits only a 0.00005 e decimal-rounding discrepancy.

The complete atom-name map preserves the source hydrogen correspondence:

| Chemical dictionary | Amber template |
| --- | --- |
| H11, H12 | H1C1, H2C1 |
| H3, H4 | HC3, HC4 |
| H51, H52 | H1C5, H2C5 |
| HO3, HO4 | HO3, HO4 |

All heavy-atom names are unchanged. Amber connectivity has no chemical bond
orders. The independently assessed ligand graph retains those orders.

## Scope and next action

A passing comparison admits only template correspondence for the initial
keto RuBP(4−) and anionic KCX hypotheses. It does not assess numerical force
coefficients, metal coordination, hydrogen geometry or an equilibrium ensemble.
Protonated KCX and reactive enolate states require their own explicit treatment.
These sources supply no formation, gas-discrimination, commitment or processing rates.

For ff14SB preparation, use the existing `scoped_kcx_stock` and
`scoped_boundary_stock` owners in
`adapters.methods.rubisco_insilico_dynamics.preparation`.
They preserve the source coefficients and restrict custom types to KCX.
They do not globally replace ordinary protein parameters.
Assess the complete native topology, assignment, exclusions and boundary terms
before a coupled force calculation.

## References and research

The original templates are from
[RuBisCO_evolution](https://github.com/kacarlab/RuBisCO_evolution/tree/e6c621656ca1a8eb7e09381d6405da5d412274a1/data/systems_for_MD/parameters),
commit `e6c621656ca1a8eb7e09381d6405da5d412274a1`.
Their MIT license is retained beside the test fixtures.
The ligand graph follows the
[tetraanion preparation](rubp-tetraanion-preparation.md).
The [physical supplier specification](physical-rate-supplier-v1.md) retains the
additional chemistry and force requirements.
