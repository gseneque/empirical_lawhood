# Fixed preparation across independently drawn bath waveforms

SPDX-License-Identifier: CC-BY-4.0

R25 asks whether the nominated negative Y excursion increases covered two-task service when the nominal bath varies between systems. One unit comprises an independently drawn nominal waveform and its perturbation. HOLD, negative and positive excursions share that unit, its prefix, probe roster, requests and coupled future tapes. The fixed D016 population retains its own R23 result. The original finite law and the support, error, width, preservation, work and coverage decisions retain their original units and coefficients. [Fixed-waveform specification](empirical-lawhood.constructed-preparation-applicability.md)

## Population and entry

The numerical allocation derives separate PCG64 purposes for nominal prefix, parent and both refinement bridges. Each pre-handoff innovation is the nominal Gaussian draw plus 0.002 times an independent draw. The fixed D016 probe roster selects the same observation recipe. Full-strength independent futures start at 4496. Development has 32 equally weighted waveforms and confirmation has 128. The allocation binds each split and index to its actual consumed seeds. The clock, three parent schedules, two numerical views, both futures and 256 request pairs per waveform follow the fixed-law specification.

At 4096, before branching, freeze the predictors and their forecasts. At 4496 seal the lower-package choices from the actual handoffs before acquiring native outcomes through 4688. For each development root calculate the largest observed covered-service fraction over the three parents minus HOLD's fraction. A mean below 0.05 closes confirmation. Report its whole-root uncertainty. Missing mandatory panels retain their assignments and cannot supply a passing screen.

On the complete confirmation cohort require positive N-minus-H validity in the exact one-sided paired test at 0.05, observed covered-service improvement of at least 0.05, a positive one-sided 95% whole-waveform bootstrap lower bound, and a one-sided 95% exact upper bound of at most 0.10 for false-admission episodes under N. Use 20,000 paired whole-unit bootstrap draws. Publish gains, harms, shared passes, shared failures, declines, cancellations and numerical failures. P is the signed preparation control.

## Information and physical response

Both drive rules have the same eight current snapshot channels, candidate parent, protocol time and horizon. Use the recorded X/Y coupling at nine reference ticks, 3968 through 4096 inclusive in steps of 16. The history rule additionally observes the earlier eight second-port positions projected in the primary frame selected at 4096. The ninth position is already in the snapshot. Preserve the cost of collecting the frame, the shared drive and the incremental history. The bath seeds and future drive remain outside the predictors.

Fit separate, training-standardized linear ridge models with unpenalized intercept and penalty 10 for each parent. The bounded outcomes are full validity and the covered fraction of 256 requests. Clip their predictions to the unit interval and use 0.5 for the secondary predicted-validity census. The physical endpoint is half the difference of the port-2 outputs of the magnitude-8 signed pair at tick 4688. Fit the mean of both primary-view futures per parent. Keep physical predictions unclipped.

Compare the paired squared errors for N-minus-H service, arm-level service and validity Brier loss, P-minus-H, and the native physical contrast. Keep future draws nested and report each numerical view. Compare snapshot, snapshot with the signed prefix margin, full prefix, and both drive rules with the same margin. Freeze margin quartiles on development. Score out-of-range and missing observations explicitly. An interval for incremental loss that spans zero leaves the benefit of the measured history unresolved. No equivalence margin for the cheaper rule is selected.

## Run and read the population

Use the locked base environment and select a fresh external workspace with the [investigation guide](../../../../docs/v1.0/define-investigation.md). The public input constructor authenticates the original F export, binds the known exposure inventory and expands the complete assigned split. The six phases for each waveform retain its measured prefix, prefix forecast, prepared parents, sealed child choices, paired native panel and independent assessment. A final operation reads every assigned assessment.

```python
from empirical_lawhood.api.waveform_preparation import create_inputs
from empirical_lawhood.api.investigations import prepare_investigation
from pathlib import Path

inputs = create_inputs(project_root=checkout, output_directory=workspace.scratch_root / "inputs",
    original_f_directory=original_f, exposure_path=exposure_census, role="development",
    master_seed=development_master, bootstrap_seed=bootstrap_master)
prepared = prepare_investigation(service, specification_path=Path(inputs["specification"]),
    source_selection_path=Path(inputs["sources"]), environment_id="environment.matrix-waveform-preparation.base")
directory = workspace.artifact_root / "waveform-population"
service.author(preparation=prepared, output_dir=directory)
result = service.run(directory=directory, maximum_parallel_tasks=workers)
cold = service.read(directory=directory)
```

For a passing development screen, select a separate evaluation workspace, set `role="evaluation"`, provide a disjoint master, and pass the original `parent_directory` and `parent_service` to the same input constructor. The parent reader authenticates the complete development cohort before permitting evaluation. Each new waveform forecast uses the frozen development fits. The cohort receipt preserves the original root operands and the read operation returns their service, risk and forecast statistics.
