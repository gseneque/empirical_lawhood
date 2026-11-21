# SCI02-C consumer prediction and selective correction

SPDX-License-Identifier: CC-BY-4.0

This guide runs the consumer-directed successor through the ordinary experiment lifecycle.
Read the [scientific protocol](protocol-c-v1.md) first.
It fixes the signed receiver, precision, two information routes, three fitted accounts, request rule and complete original reservation.
Training includes mixed successes and failures.
Calibration cannot change the account, and zero admissions do not cancel the planned finite confirmation.

The [completed result](../../records/matrix-sci02c-result.md) records the original reservation's assessment.
Use retained reads for that completed reservation.

## Select the original source and environment

Use the [locked main environment](../../../../../docs/using/environments.md).
After selection, run `uv run --no-sync`; do not synchronize to inspect results.
Select an operator profile, guarded artifact root, new input/authoring destinations and scratch path.
Use four workers with one numerical thread per worker.
Retain exact installed source, dependency and numerical provenance for every stage.

Supply the complete original SCI02 DEV8 authoring directory, its actual guarded artifact reader, original campaign and fixed-instrument template.
The first eight roots are exposed training data.
DEV08–15 are the original calibration reservation and HOLDOUT00–31 the original confirmation reservation.
Check actual original native contacts before entering those reservations.
Do not substitute a new seed bank, duplicate a completed root or relabel exposed evidence as fresh.
Unknown native contact is a stop requiring the documented custody recovery.

## Derive training inputs

Use `export_original_development` from
[`matrix_sci02c`](../../../../../src/empirical_lawhood/api/matrix_sci02c.py).
Pass `directory` for the original SCI02 DEV8, its `artifact_writer` and a new `output_directory`.
This uses the original independent scientific reader and common guarded custody.
It retains H16/H32 HOLD observations, handoffs, fixed instruments and original response outcomes with the original product and receipt identities.
It acquires no trajectory.
Use the returned `directory` as `retained_directory`.

Call `create_training_inputs` in the same API with `retained_directory`, `campaign_path`, `protocol_path`, `project_root` and a new `output_directory`.
`protocol_path` is this guide's `protocol-c-v1.md` in the selected source checkout/distribution.
The constructor derives eight diagnoses and one pooled fit.
Use its returned paths; do not hand-construct scientific identities, task rosters or predecessor records.

## Run one complete stage

Set `PROJECT`, `PROFILE`, `INPUTS`, `ARTIFACT_ROOT`, `WAVE` and `ENVIRONMENT` to explicit selections.
`INPUTS` is the constructor's returned directory.
`WAVE` is a new authoring directory under the selected artifact root.
Retain each command's output in an explicit report destination.

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

Preparation derives the complete root, operation, input and native-effect census.
Missing scientific inputs and resource admission remain separate from native authority.
The common compiler, scheduler, native subwork, receipts and recovery owners execute the selected graph.
BASIC receives H32 state projections and the HISTORY supplier receives the separate H16 projections.
Neither predictor receives seed material or future reference responses.
Reference tasks depend on the actual sealed decision product.
The native reader checks original input, source, stream, child-output and checkpoint custody.
Known-completion recovery retains original output bytes and performs no new scientific acquisition.

## Derive calibration and confirmation

After the complete training read, call `create_continuation_inputs` from the same API.
Supply the completed training `directory`, its actual `artifact_writer`, `templates_path`, the unchanged `protocol_path`, `project_root` and a new `output_directory`.
The function independently reads the predecessor, takes its actual frozen fit product and derives the original DEV08–15 calibration inputs.
No supplied pathname or configuration alone establishes a completed fit.
The complete calibration stage has 233 operations and at most 80 native child intervals.

Run that stage with the same ordinary commands and a new `WAVE`.
Then call `create_continuation_inputs` on the completed calibration directory.
It binds the original fit and rank-eight calibration products and derives HOLDOUT00–31.
The complete confirmation stage has 929 operations and at most 320 native child intervals.
The 144-package cap includes 24 reused training, 24 calibration and 96 confirmation response packages.
Native common prefixes and HOLD-only intervals are separately counted work.

A missing physical description can prevent a fit; unknown contact, integrity or actual resource failure can prevent execution.
A failed accuracy criterion or zero-admission calibration is a scientific result, not permission to revise the frozen model or discard roots.
The planned confirmation still assesses every original held root.
There is no continuation beyond the finite confirmation reservation in this route.

## Read the findings and costs

### Retained calibration check repair

The first calibration installation completed all 80 native intervals and all
sealed predictions, then its H32 observation checker incorrectly requested an
H16 member. A separate PURE readback supports precisely that settled outcome:
200 successful operations, 24 `KeyError` assessment failures and nine blocked
reductions. It preserves the failed original terminal and every native receipt.

Use `author_reassessment` from
[`matrix_sci02c_reassessment`](../../../../../src/empirical_lawhood/api/matrix_sci02c_reassessment.py)
with the original `directory`, actual `artifact_writer`, corrected installed
`project_root`, and new explicit `output_directory` and `input_directory`.
The constructor authenticates the entire original custody, numerical sources,
native checkpoints, sealed decisions and original instrument. It derives eight
PURE root readbacks and one calibration reduction. It cannot acquire trajectories
or change the fitted account, original roots, precision or calibration rank.

Run the returned authoring directory with the ordinary
`campaign recursive-development-run --authoring-dir "$WAVE" --workers 4` command.
Repeating that command recovers the same known completions.
Use `read_reassessment(directory=..., original_directory=..., artifact_writer=...)`
for the independent scientific result. The returned report retains the original
failed terminal beside the new readback receipts.
Use `create_confirmation_inputs` from that same API with both directories,
`artifact_writer`, `templates_path`, unchanged `protocol_path`, current
`project_root` and a new `output_directory` to derive the original 32 held roots.
Run confirmation through the ordinary experiment commands above. The original
failed calibration directory is never rewritten or rerun.

### Scientific interpretation

The readout checks native equations, literal derivative actions, independent affine propagation, signed receiver projections, fit equations and calibration scores.
It retains every assigned root, both numerical views, both panels, every action and all three recipe contrasts.
It distinguishes forecast information, supplier value, useful delivery and cost.
Refusals and fallbacks remain visible; a reference fallback is not a reduced delivery.

The actual study acquires every assessment reference after its decision.
A HISTORY computation not purchased by the policy is labelled supplier-assessment work and charged to the study.
It cannot alter the policy's already selected BASIC or REFERENCE route.
Report actual total study cost separately from an operational policy reconstruction and finite-workload projections.
Preserve unknown historical costs and avoid adding nested CPU totals twice.

The public protocol states the limited rank-eight interval coverage and the eight-root audit comparator.
The audit estimator targets the uniform mean of these exact 32 roots.
It supplies neither individual accuracy guarantees nor the molecular target ensemble.
All Matrix findings are nonpromotable; the molecular requirement remains open.
See [results and failures](../../../../../docs/using/results-and-failures.md) for retained attempts and original-result access.
