# Prepare a common Rubisco pilot from original costs

SPDX-License-Identifier: CC-BY-4.0

This guide prepares a prospective pilot from original force, trajectory and analysis costs.
It preserves all four materials, consequential roles, failed calibrations and exact costs.
Select the original calibration configurations and a complete candidate roster before cost assessment.

## Prerequisites

Select the [locked environment](../../../../../docs/using/environments.md) and an explicit artifact destination.
Use `uv run --no-sync` after environment selection.
Retain the original [force probes](periodic-force-probe.md) or [reference trajectories](reference-trajectory.md).
Keep their configuration records, representation, phase bytes, results and native-subwork custody.
An absent result is unknown evidence, not proof of nonentry or zero cost.

The cost reader supports complete coupled force returns and complete analysis/export invocations.
The stage reader binds existing authored recipes and independent scientific findings.
Prepare molecular recipes through their supported guides before stage assessment.
The stage reader performs no native execution.
An estimated affordable candidate grants no spending or execution authority.

## Freeze the complete candidate roster

Use the records in
[`pilot_allocation.py`](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/pilot_allocation.py).
Construct each `PilotCandidate` from its selected `PilotWorkEstimate` records.
Bind the actual scientific selections and their numerical and scientific criteria.
Declare an explicit candidate priority before assessment.
Selection uses that order, cost availability and resource capacity.
It does not receive mutation-effect values.

Each candidate must cover WT and I95M separately for M1 and V1.
Each material requires these roles:

- Formation and reversal.
- Carbon access and escape.
- Carbon chemistry and reversal.
- Carbon processing, release and return.
- Oxygen access and escape.
- Oxygen charge transfer.
- Oxygen spin, recombination and commitment.
- Oxygen processing, release and return.
- Dividing-ensemble dynamics.
- Numerical and chemical controls.
- Assessment and export.

One scientific work item can cover several cells.
Retain it once with its complete coverage tuple.
Do not repeat its identity to charge or execute the same work twice.
The 44 required cells are a planning denominator, not evidence of completed scientific coverage.
Each identity still requires its supported recipe and original custody before execution.

Declare each calibration in `PilotCalibrationCase`.
Bind its exact configuration and `PilotCostClass`.
The class binds the complete operator and environment through `pilot_force_scope(config).identity`.
Density initialization alone does not change this scope.
A different representation, path, cell, electronic model, molecular model or engine does change it.

Select the required successful calibration count and an explicit multiplier of at least one.
State the extrapolation assumption for each class.
Candidate units are finite scientific selections, not limits on SCF iterations or native evaluations.
Original task costs include setup.
Their quotient per complete force is not a measured warm-call cost.
Extrapolation to another scientific selection remains a declared cost premise.

Declare the currency, quoted charge per second and original quote identity together.
Select the maximum additional projected charge separately.
Declare available host memory, device memory and retained storage.
The rule assumes serial work, uses peak selected memory and sums retained bytes.
A quote identity does not establish a current provider offer or permission to spend.
The launch procedure must assess those actual prerequisites.

## Read the original calibration costs

The supported API is
[`api.domain_composition.rubisco_response.pilot`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/pilot.py).
For each calibration, construct a `RetainedPilotCalibration` with its original carriers.
Pass `None` for the phase bytes of a force probe.
Trajectory and equilibrium calibrations retain their original phase bytes.
Keep a carrier for each declared missing result.

```python
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation_read import (
    RetainedPilotCalibration,
)
from empirical_lawhood.api.domain_composition.rubisco_response.pilot import (
    read_pilot_allocation,
    export_pilot_allocation,
    read_pilot_allocation_export,
)

# rule is the frozen PilotAllocationRule.
# sources contains every original carrier in the rule's calibration order.
report, arrays = read_pilot_allocation(
    selection=rule,
    sources=sources,
    assessor_source=assessor_source,
)
exported = export_pilot_allocation(
    selection=rule,
    sources=sources,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/pilot-cost",
)
verified = read_pilot_allocation_export(
    directory_relative_path="selected/pilot-cost",
    sources=sources,
    artifact_writer=artifact_writer,
)
```

The reader authenticates the complete original receipt and output census.
It assesses finite force returns or complete trajectory mechanics through the existing readers.
It performs no new native evaluation.
A successful force probe contributes one calibration unit.
A complete trajectory contributes its original steps plus its initial force return.
The original whole-task cost remains unchanged.

## Output and stops

For each class, the rule uses the maximum measured wall cost per complete unit.
It multiplies that value by the prospective cost multiplier.
For each candidate, it sums the selected unit costs and adds the declared overhead charge.
Fractions preserve exact Decimal inputs without ambient Decimal rounding.
Projected time is a serial cost estimate, not a deadline.

The first eligible complete candidate receives `PROVISIONAL_COST_SELECTION`.
Otherwise, the result is `NO_FEASIBLE_COMPLETE_PILOT`.
Missing, failed or unassessed selected calibrations prevent that class from supplying a cost estimate.
Missing cost, memory, quote or charge selection also prevents an eligible estimate.
An original memory observation above the work estimate prevents selection.
All original costs remain separate from additional projected costs.
Unknown cost remains unknown in the total.

The closed export contains `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt`.
Use the returned paths and preserve the full package.
The export reader reconstructs the result from original custody and refuses changed members.
It also repeats the complete original-byte checks before return.

This cost result does not establish physical supplier validity, preparation admission or biological prediction.

## Measure non-force analysis and export

Use [`pilot_costs`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/pilot_costs.py)
for supported flux, electronic, physical-supplier and paired-forecast analyses.
Select `REACTIVE_FLUX`, `ELECTRONIC_ENSEMBLES`, `PHYSICAL_SUPPLIERS` or `PAIRED_FORECAST` as the analysis kind.
Supply its complete original carriers and exact scientific selection.
Select fresh, disjoint export and observation destinations within the guarded root.

```python
from empirical_lawhood.api.domain_composition.rubisco_response.pilot_costs import (
    measure_pilot_analysis_export,
    RetainedPilotAnalysisCalibration,
    read_complete_pilot_allocation,
)

measured = measure_pilot_analysis_export(
    analysis_kind="PAIRED_FORECAST",
    selection=forecast_selection,
    sources=forecast_sources,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/forecast-calibration",
    observation_relative_path="selected/costs/forecast.json",
)
observation = measured["observation"]
# Bind observation.scope.identity in a COMPLETE_ANALYSIS_EXPORT cost class.
# Bind observation.scope.scientific_selection in its PilotCalibrationCase.
analysis_source = RetainedPilotAnalysisCalibration(
    "calibration.forecast", "selected/costs/forecast.json",
    observation.identity, forecast_sources,
)
report = read_complete_pilot_allocation(
    selection=complete_rule,
    native_sources=native_sources,
    analysis_sources=(analysis_source,),
    artifact_writer=artifact_writer,
    assessor_source=assessor_source,
)
```

The measurement includes export and independent reconstruction, with exact observed wall and CPU costs.
It retains the complete producing provenance, export members and failure disposition.
Retained bytes count the five export members.
Process memory is the lifetime high-water observation, not incremental memory for this invocation.
Failed analysis retains its measured cost and cannot supply a successful calibration unit.
Missing observation remains unknown and cannot prove nonentry.
Other non-force operations still need explicit prospective cost estimates.

The complete reader charges every selected calibration once across both cost kinds.
It authenticates exports and repeats original-byte checks without native evaluation.
Existing force-only exports retain their original contract.

## Bind recipes and assess scientific stages

Use [`pilot_programme`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/pilot_programme.py).
Call `bind_pilot_recipe` with each native work item and its returned public authoring directory.
Retain the returned `PilotRecipeBinding` without changing its packet, plan or task identities.
The binding preserves every task and identifies native tasks through the registered operation owner.
The stage reader rejects repeated native effects across separately labelled work.

Select a `PilotProgrammeRule` with the complete allocation, candidate, ordered stages, bindings and scientific gates.
Each `PilotStage` identifies work, entry gates and completion gates.
Stages cover every native work item exactly once.
Each `PilotScientificGate` binds an exact supported analysis selection and the recipes it assesses.
Completion requires original results from every native task in those recipes.
The corresponding analysis retains its complete missing, adverse and uncertainty census.

Pass every `RetainedPilotRecipe` and `RetainedPilotGate` to `read_pilot_programme`.
Supply the original cost carriers through `native_cost_sources` and `analysis_cost_sources`.
An absent gate export uses `directory_relative_path=None` and remains unevaluable.
The reader returns original cost, task and scientific-gate reports with the complete stage census.

| Stage action | Next action |
|---|---|
| `PREPARE_MISSING_RECIPES` | Use the relevant public preparation and authoring guide. |
| `HOLD_COST_SELECTION` | Resolve the original cost or selected capacity prerequisite. |
| `USE_EXISTING_EXECUTION_PREFLIGHT` | Assess actual execution prerequisites through the existing lifecycle. |
| `WAIT_FOR_PREDECESSOR` or `WAIT_FOR_ENTRY_ASSESSMENT` | Retain the stage until its scientific predecessor is assessed. |
| `WAIT_FOR_INDEPENDENT_ASSESSMENT` | Read the original supplier evidence and retain the complete result. |
| `HOLD_UNCERTAIN_CONTACT` | Resolve original contact through shared recovery; do not infer safe replay. |
| `RECOVER_RETURNED_PUBLICATION_ONLY` | Complete publication of the original return without reacquisition. |
| `STOP_RETAINED_OPERATIONAL_FAILURE` | Retain the original failure and use its documented recovery boundary. |
| `STOP_SCIENTIFIC_FALSIFICATION` | Retain the adverse scientific finding and stop the selected stage. |
| `COMPLETE` | Retain the assessed stage and inspect the next declared stage. |

Stopping uses the selected scientific criteria, not elapsed deadlines or a desired mutation effect.
Completed software tasks cannot replace missing molecular findings.
An affordable candidate or completed stage assessment grants no new spending, execution or physical authority.
The actual molecular recipes, assessed calibration costs and scientific evidence remain necessary for a prepared pilot.

Use the [remote procedure](../../../../../docs/using/accelerated-compute.md#remote-execution-within-the-researcher-workflow)
for remote execution and complete evidence return.
Verify returned bytes before independent assessment through the same readers.
Keep uncertain contact, failed outcomes and unentered tasks in their original custody.

## References and research

The [source provenance](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/pilot-provenance.json)
identifies the owner-directed adaptation of the earlier recovered-cost selection rule.
The implementation excludes that rule's fixed roster, deadlines, automatic multiplier and authority assumptions.
The [physical supplier specification](physical-rate-supplier-v1.md) owns the scientific roles and interpretation.
The [accelerated compute contract](../../../../../docs/using/accelerated-compute.md) owns resource and launch boundaries.
