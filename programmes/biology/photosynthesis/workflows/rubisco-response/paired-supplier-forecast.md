# Assess a paired Rubisco forecast from original suppliers

SPDX-License-Identifier: CC-BY-4.0

This guide joins original molecular supplier findings to paired turnover and specificity decisions.
It preserves common uncertainty draws, missing rates, adverse findings and shared costs.
Select the complete supplier census and paired cases before assessment.

## Prerequisites and first action

Select the [locked environment](../../../../../docs/using/environments.md) and explicit artifact destinations.
Use `uv run --no-sync` after environment selection.
Retain the exact selections and original carriers for each supported supplier.
The [flux guide](reactive-flux.md), [rate guide](physical-rate-assessment.md) and
[physical supplier specification](physical-rate-supplier-v1.md) define their scientific boundaries.

Use [`paired_forecast`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/paired_forecast.py).
Construct `ForecastSupplier` records for reactive-flux, electronic-ensemble or physical-supplier selections.
Each supplier indexes one complete shared original-carrier tuple.
Store shared original configurations once.
Use the same dependence set for shared configurations or random streams.
Explicitly declare any independence assumption between dependence sets.

Construct the complete `ForecastCase` and `ForecastRatePair` census for the selected M1/V1 WT and I95M comparisons.
Use `ForecastOperand` to select each original observable and its chemical correspondence.
Retain `None` for absent operands.
Processing operands distinguish `PRODUCTIVE_RETURN` from `REVERSE_RETURN`.
Productive processing must include release and substrate-ready return.
An electronic rate cannot supply bulk capture or a complete processing network.

```python
from empirical_lawhood.api.domain_composition.rubisco_response.paired_forecast import (
    prepare_paired_forecast,
    export_paired_forecast,
    read_paired_forecast_export,
)

selection = prepare_paired_forecast(
    suppliers=suppliers,
    cases=cases,
    dependence_source=dependence_source,
    maximum_analysis_bytes=maximum_analysis_bytes,
    assumptions=assumptions,
    sources=sources,
)
exported = export_paired_forecast(
    selection=selection,
    sources=sources,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/paired-forecast",
)
verified = read_paired_forecast_export(
    directory_relative_path="selected/paired-forecast",
    sources=sources,
    artifact_writer=artifact_writer,
)
```

## Output and stops

Preparation checks materials, temperature, units, observable meaning, dependence and the complete carrier denominator.
The reader reconstructs each supplier from its authenticated original custody.
It performs no native evaluation.
Common draws remain common through the joint M1/V1 endpoint calculation.
Failed or incomplete realizations remain in the assigned denominator.
Joint criteria require the conditions for every selected pair in the same realization.
The report retains all three criterion counts over the complete assigned denominator.
The reported joint variation carries no unselected confidence-coverage claim.

`owner_criteria` reports endpoint arithmetic under the supplied rates.
`supplier_assessment` reports the selected supplier criteria.
`conditional_forecast_status` requires both findings and every required operand.
An adverse supplier remains adverse even when endpoint arithmetic appears favourable.
An absent reversal remains missing even when a limiting endpoint formula does not use it.
Physical-model admission and biological predictive validity remain separate findings.

Original native costs use one deduplicated carrier census.
Nested supplier reports are references to those costs.
Unknown costs remain unknown, with the known subtotal reported separately.
Summed wall costs describe task cost, not elapsed parallel execution time.
Use the [pilot guide](pilot-cost-preparation.md) for additional analysis/export cost measurements.

The closed export contains `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt`.
Retain all members and use returned paths.
The export reader reconstructs the complete result and refuses changed export or original bytes.
Software checks and exposed fixtures establish no measured enzyme rates or biological forecast.
