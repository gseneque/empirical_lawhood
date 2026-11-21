# SCI02-D paired equilibrium estimator bridge

SPDX-License-Identifier: CC-BY-4.0

This guide runs the finite paired equilibrium experiment through the shared experiment lifecycle.
Read the [current scientific protocol](protocol-v2.md) before preparing its immutable inputs.
It selects the native target, new allocation, frozen estimators, precision and complete cost comparison.

## Select environment, source and storage

Use the [locked main environment](../../../../../docs/using/environments.md), four workers and one numerical thread per worker.
After environment selection, use `uv run --no-sync`.
Select an installed source snapshot, an actual campaign, an operator profile and explicit input, artifact, result and scratch destinations.
For new local operational outputs, select the current EL_2 default beneath `/media/chevre/EL_2/empirical-lawhood`.
The retained study now lives at `/media/chevre/EL_2/empirical-lawhood/runs/sci02-d`; keep new execution destinations separate from it.
Its original frozen inputs and protocols retain the historical `/home/chevre/empirical-lawhood-sci02-d` selection.
Keep at least 2 GiB free during execution.
Retain source, dependency and numerical provenance for both tranches.

This is a new, nonpromotable numerical allocation.
Its 16 training, 64 confirmation and eight independent reference bundles are separate from every previous SCI02 reservation.
All three banks enter the original committed selection before any study outcome.
The confirmation/reference source bytes do not enter coefficient fitting.
Do not create roots, random streams, scientific identities or task rosters by hand.

## Construct training inputs

Call `create_training_inputs` from
[`matrix_sci02d`](../../../../../src/empirical_lawhood/api/matrix_sci02d.py)
with `campaign_path`, `protocol_path`, `project_root` and a new `output_directory`.
The current protocol is this directory's `protocol-v2.md` in the selected source checkout/distribution.
The function generates and commits new stream material, constructs the frozen physical design and captures the actual producing source.
It returns `specification`, `sources`, `source_snapshot`, `directory` and the exact tranche census.
It acquires no native trajectory.
In a Python launcher, call input constructors from a `main()` function guarded by `if __name__ == "__main__":`.
Authenticated continuation can start the existing parallel verification workers.
The entry-point guard prevents those workers from invoking the launcher again when Python imports it.

Training has 34 operations: one solvable-control check, 16 original native bundles, 16 independent assessments and one frozen fit.
Each training sampler depends on the successful control product.
Every assessment and the pooled fit retain their complete original predecessors.
Mixed numerical findings remain in the denominator.
The estimator menu and sampling fractions cannot be revised after confirmation contact.

## Execute the complete tranche

Set `PROJECT`, `PROFILE`, `INPUTS`, `ARTIFACT_ROOT`, `WAVE` and `ENVIRONMENT` to explicit selections.
Use the constructor's returned directory for `INPUTS` and a new guarded authoring destination for `WAVE`.
Use the selected source's locked environment; set `UV_PROJECT_ENVIRONMENT` to its retained interpreter directory when that environment is stored separately.
Retain command outputs and elapsed/CPU observations under the selected results destination.

```sh
uv run --no-sync --project "$PROJECT" empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-prepare \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --output-root "$ARTIFACT_ROOT" --workers 4 --output "$INPUTS/preparation-report.json"
uv run --no-sync --project "$PROJECT" empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-author \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --workers 4 --output-dir "$WAVE"
uv run --no-sync --project "$PROJECT" empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-run \
  --authoring-dir "$WAVE" --workers 4
uv run --no-sync --project "$PROJECT" empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-read \
  --authoring-dir "$WAVE"
uv run --no-sync --project "$PROJECT" empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-recover \
  --authoring-dir "$WAVE" --workers 4
```

Preparation derives the independent-unit allocation, dependencies and native-effect census.
The registered lowerer creates all task and output contracts.
The common scheduler, guarded array transport, native subwork, receipts and recovery execute the graph.
Configuration validation supplies no scientific qualification or outcome-access authority.

Native outputs retain positions, gradients and diagnostics in three bounded NPZ artifacts.
Each artifact uses the existing 64 MiB Matrix contract.
The complete task allowance is 384 MiB, including both retained native outputs and their ordinary parent copies.
Reference bundles retain their longer horizons and full nine-center grid.
The storage partition changes no selected observation.

The original November 2026 execution used [protocol v1](protocol-v1.md) and its 192 MiB allowance.
Its reference bundles completed native acquisition but exceeded that allowance during parent publication.
The ordinary recovery command finishes publication from authenticated completed native receipts.
It preserves the original attempt and refuses native replay.
Protocol v2 corrects the output accounting for new inputs; it changes no equation, horizon, coefficient rule or independent-unit census.
Use the original protocol bytes and producing installation when recovering a retained v1 study.
The retained instance reader also accepts that exact v1 draft with its original 192 MiB allowance.
It preserves the original records and refuses other resource substitutions.
New preparation continues to use 384 MiB.

A completed receipt recovers its original outputs without acquiring another path.
Unknown or failed native contact cannot be retried under a renamed task.
Keep failed attempts and use the [results and failures](../../../../../docs/using/results-and-failures.md) procedure.

## Derive confirmation and references

After the complete independent training read, call `create_continuation_inputs` from the same API.
Supply the training `directory`, its actual guarded `artifact_writer`, unchanged `protocol_path`, installed `project_root` and a new `output_directory`.
The function authenticates the original predecessor receipts, rechecks the fit and binds its exact frozen coefficients and fractions.
It derives the original 64 confirmation and eight reference bundles from the committed selection.
No caller-supplied fit pathname alone establishes that predecessor.

Run the returned inputs with the same commands and a new authoring directory.
This tranche has 145 operations: 72 original native bundles, 72 assessments and one complete reduction.
Its 72 independent units remain split into the two original bank roles.
Reference streams are independent of training and confirmation.
There is no further native continuation through this finite route.

## Read the scientific result

`experiment-read` authenticates the complete operation and native-contact census.
It compares every retained batch force with the historical scalar force, reconstructs the controls and checks the recorded BAOAB transitions.
It independently checks the frozen covariance fit and retains exact coefficients.
It never acquires a trajectory during readback.

The result retains NATIVE, COORDINATE and STRUCTURE at full length and their frozen prefixes.
It reports the signed reference integral and uncertainty, numerical and preparation differences, center-grid refinement, chronological drift, block sensitivity and correlation-tail diagnostics.
Repeated sampling frames and nested views never become independent units.
A negative or unresolved scientific result can coexist with complete software execution.

Charge native sampling, controls, fitting, independent force assessment, verification, failed work and orchestration.
Whole-process CPU observations include reaped children; native child measurements are nested components and must not be added again.
The study pays for full confirmation paths and references.
Any prefix saving is an operational reconstruction until actually deployed at the same required accuracy.
Repeated estimates of one physical target create no independent reuse demand.

The canonical zero-mean identity preserves the target mean under its premises.
It does not prove that these finite paths sample the canonical distribution.
The molecular M1 WT/I95M supplier, finite-restraint corrections, state coverage, normalization and transmission remain separately assessed requirements.

## Completed finite study

The [SCI02-D result](../../records/matrix-sci02d-result.md) records all 16 training, 64 confirmation and eight independent reference bundles.
Both corrected methods retained full production under the frozen allocation rule.
The result separates measured variance, unresolved equilibrium accuracy, complete paid work and the still-open molecular supplier.
