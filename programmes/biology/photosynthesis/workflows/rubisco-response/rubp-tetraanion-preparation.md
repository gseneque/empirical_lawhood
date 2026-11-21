# Prepare the selected RuBP tetraanion graph

SPDX-License-Identifier: CC-BY-4.0

This guide constructs the selected keto RuBP tetraanion from a retained public dictionary.
It supplies an explicit ligand graph and an independently checked, unrelaxed coordinate template.
Use the returned preparation paths as inputs to subsequent active enzyme construction.

## Prerequisites and first action

Select the retained public `RUB.cif` file, its SHA-256, and a guarded artifact writer.
Use the selected locked environment with `uv run --no-sync`.
The [physical supplier specification](physical-rate-supplier-v1.md) selects RuBP(4-) for the initial enzyme state.

Call the supported preparation owner:

```python
from empirical_lawhood.api.domain_composition.rubisco_response.molecular_preparation import prepare_rubp_template

prepared = prepare_rubp_template(
    component_path=selected_original_component,
    component_sha256=selected_original_sha256,
    output_relative_path="preparations/rubp-tetraanion",
    artifact_writer=selected_artifact_writer,
)
print(prepared["paths"])
```

The owner bounds the source read to 64 KiB and checks the selected digest.
It rechecks the complete original bytes immediately before atomic publication.
The returned paths identify `source.cif`, `preparation.json`, `chemical-graph.json`, `assessment.json` and `report.txt`.
Publication retains source lineage and the development evidence ceiling.
No worker or molecular backend enters during this preparation.

For retained use, call `read_rubp_template` from the same API module.
Supply `directory_relative_path`, `component_sha256` and the original `artifact_writer`.
The reader authenticates the complete publication and independently reassesses its original graph.
It does not repeat construction or acquire source data.
Changed siblings, missing source lineage and a different evidence lane refuse.

## Chemical transformation and independent assessment

The constructor removes the four explicit phosphate protons: HOP2, HOP3, HOP5 and HOP6.
The corresponding oxygen formal charges become minus one.
Every other source atom and bond order remains in the graph.
The resulting formula is C5H8O11P2, with charge minus four and 160 electrons.
The selected spin multiplicity is one.

The assessor uses a separate CIF parser and consumes the retained preparation.
It checks complete atom correspondence, bond orders, valence, charge and electron count.
Exact signed coordinate volumes check the C3 and C4 R stereocentres with their explicit substituent priorities.
Changed graphs and reflected templates retain falsified findings.
The assessor never invokes the constructor or a native producer.

## Output limits and next action

The coordinates remain the dictionary's ideal template after proton removal.
They are not relaxed tetraanion coordinates or an active Gp/Mg ligand placement.
Formal charge does not supply force-field partial charges or nonstandard parameters.
A satisfied graph assessment leaves enzyme preparation and parameter admission UNEVALUABLE.

Place the constructed ligand in all eight sites through the selected enzyme preparation supplier.
Retain the full assembly, missing residues, paired mutations, metal coordination and proton-allocation alternatives.
Independently assess the resulting coordinates, topology, parameters and coupled forces before rate calculations.
The graph alone supplies no turnover or specificity evidence.

## References and research

The [RCSB RUB dictionary](https://files.rcsb.org/ligands/download/RUB.cif) supplies the neutral component and coordinate template.
The selected tetraanion is a distinct construction under [GP-WT-I95M-REF1](physical-rate-supplier-v1.md).
