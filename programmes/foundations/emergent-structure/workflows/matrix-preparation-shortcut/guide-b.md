# SCI02-B paired descriptions and finite reuse

SPDX-License-Identifier: CC-BY-4.0

This guide gives the SCI02-B researcher procedure.
The implemented entry route supports authenticated development reuse and its bounded representation decision.
Calibration and confirmation are conditional later stages specified in the protocol.
Read the [scientific protocol](protocol-b-v1.md) before selecting inputs.

## Prerequisites

Use the [locked main environment](../../../../../docs/using/environments.md) after environment selection.
Use `uv run --no-sync` for every subsequent command.
Select an operator profile, guarded artifact root, scratch directory and new input destinations.
Use one numerical thread per worker and four workers within the selected profile.
Retain exact source, dependency and numerical provenance through each tranche.

Supply the complete original SCI02 DEV8 authoring directory and its guarded artifact reader.
Supply the original selection, campaign and fixed-instrument template files.
The original reservation must retain unused DEV08–15 and HOLDOUT00–31.
Authenticate actual nonentry before new acquisition.
An unknown native contact cannot become a fresh case through a renamed study.

## Reuse original development evidence

Use `export_original_development` from
[`matrix_sci02b`](../../../../../src/empirical_lawhood/api/matrix_sci02b.py).
Pass the original authoring directory, its actual `artifact_writer`, and a new explicit `output_directory`.
The function uses the common guarded read and the original independent SCI02 assessor.
It exports eight bounded input cases with their original products, receipts and array identities.
Its returned `directory` selects the retained input package.
No native trajectory is acquired by this export.

Use `create_development_inputs` from the same API.
Supply `retained_directory`, `campaign_path`, `protocol_path`, `project_root` and a new `output_directory`.
The constructor derives 16 candidate assessments over eight original roots and one pooled decision/fit.
Use its returned specification, sources and source-snapshot paths.
Do not construct root identities, predecessor records or operation rosters manually.

## Run the ordinary experiment lifecycle

Set `PROJECT`, `PROFILE`, `INPUTS`, `ARTIFACT_ROOT`, `WAVE` and `ENVIRONMENT` to explicit selections.
`INPUTS` is the directory returned by the supported input constructor.
`WAVE` is a new authoring destination below the selected artifact root.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-prepare \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --output-root "$ARTIFACT_ROOT" --workers 4 --output "$INPUTS/preparation-report.json"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-author \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --workers 4 --output-dir "$WAVE"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-run \
  --authoring-dir "$WAVE" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-read \
  --authoring-dir "$WAVE"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-recover \
  --authoring-dir "$WAVE" --workers 4
```

Preparation reports the complete operation, independent-root and native-contact census.
Inspect missing inputs and actual resource admission before execution.
Execution uses the common compiler, scheduler, native contact, receipts and recovery owners.
Known-completion recovery preserves original outputs.
An uncertain native contact refuses reacquisition.

## Select a continuation

Independently read the completed development result first.
An unavailable representation closes the bounded candidate menu.
A successful fit supplies the exact frozen description for calibration.

The retained-development implementation does not authorize native continuation.
A successful fit requires an installed calibration/confirmation composition with the same source, custody and information boundaries before further acquisition.
No such acquisition is needed when the bounded representation menu closes.

Calibration uses exactly the unused DEV08–15 roots.
Confirmation uses exactly HOLDOUT00–31 only after the calibrated continuation rule passes.
Continuation must refuse a missing frozen description or a failed continuation decision.
It cannot create replacement roots or a new calibration bank.
The original 144-package cap includes the reused DEV8 packages.

## Output and evidence limits

The reader checks original native equations, noise joins, causal cutoffs and independent model propagation.
It preserves signed paired errors, numerical-view criteria, weak signals and missing cases.
It separately checks the representation decision and any resulting ridge fit.
The report retains all assigned roots, including refusals and operational failures.

Report study cost, incremental policy cost and finite-workload projections separately.
A policy reconstruction does not mean that reference assessment was avoided during the study.
Unknown historical or operational cost remains unknown.
The rank-eight calibration has limited marginal coverage under its stated exchangeability assumption.
It supplies no conditional accepted-case guarantee or molecular qualification.

A local stop returns an unsatisfied requirement to the inquiry.
The required molecular shortcut remains open until its own physical and complete-work assessments succeed.
See the [results guide](../../../../../docs/using/results-and-failures.md) for retained failure and original-result access.
