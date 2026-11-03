# Consume supplied Rubisco kinetics and assess a conditional joint target

SPDX-License-Identifier: CC-BY-4.0

Programme: [Photosynthesis — Rubisco](../../README.md).

This W1 software example uses the shared experiment/programme route and registered
`rubisco-kinetic-join.assay` / `rubisco-kinetic-join.assess`
operations. It supplies invented constants to the existing product assay, then
independently checks fluxes, products and both conditional endpoint bounds.
It runs no molecular calculation and predicts no mutant kinetics.

The complete roster has one supplied member, one partial member missing
oxygenation constants and one rejected member. The expected aggregate is
UNEVALUABLE even though the supplied member supports the displayed bounds.
All three members survive execution and recovery; none is a biological unit.
The displayed `5.46` / `238` values are disclosed assumptions, rather than
authenticated challenge controls. The [official target contract](../../records/loop-target-contract.md)
keeps the real reference/assay and confidence limitations explicit.

## Change a specification through the current public route

The editable [experiment](experiment.json) selects its gas query, tolerance and
exact original sources. The closed [source selection](experiment-sources.json)
binds [campaign](campaign.json), [supply](supply.json), [source query](query.json),
[comparison](comparison.json) and [material witness](assumptions.json).
Two edited gas queries have passed public load/prepare/author/worker/read/recover
through this same interface, retaining every supplied, partial and rejected member.

Use the selected existing environment without synchronization. Start with:

```sh
uv run --no-sync empirical-lawhood config validate \
  --consumer rubisco-kinetic-experiment --config programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment.json
uv run --no-sync empirical-lawhood campaign experiment-explain \
  --input programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment.json \
  --sources programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment-sources.json
```

The explanation reports two operations, all three members, one analytical unit
and zero biological units. Missing execution selections remain explicit
environment/source-snapshot/output-custody dependencies.

Copy the specification before editing it. Supported edits change its selected
`query` (`co2_um`, `o2_um`, `duration_s`) or numerical tolerance while retaining
the original sources. Preparation derives the graph, bindings, allocation and
instance identities. Researchers do not maintain detailed operation IDs.
Different source evidence instead requires separately identified typed records
and their exact source bindings. A new gas query creates no biological evidence.

Follow [environment reuse](../../../../../docs/development/maintainer-environment.md) and select a
frozen checkout. Capture its canonical `RecursiveImplementationBinding` through
`api.recursive_authoring.implementation_binding(project_root)` and supply that
record as `--source-snapshot`. Actual execution checks the selected worker source.
Choose a guarded operator profile and a new programme directory explicitly:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign experiment-author \
  --input /work/edited-kinetic-experiment.json \
  --sources /selected/checkout/programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment-sources.json \
  --source-snapshot /work/selected-implementation.json \
  --environment-id rubisco-prediction \
  --output-dir /selected/guarded-root/rubisco-kinetic-programme

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign experiment-run --authoring-dir /selected/guarded-root/rubisco-kinetic-programme

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign experiment-read --authoring-dir /selected/guarded-root/rubisco-kinetic-programme

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign experiment-recover --authoring-dir /selected/guarded-root/rubisco-kinetic-programme
```

The Python surface is `load_experiment_specification` → `load_experiment_inputs`
→ `ExperimentProgrammeService.prepare/explain/author/run/read/recover`. Completed
recovery reuses original receipts; uncertain contact retains its refusal.
The [high-level projection generator](../../../../../scripts/generate_rubisco_kinetic_experiment.py)
owns the three new example files. Its `--check` verifies drift without acquisition
and refuses replacing changed scientific inputs under the same identity.

## Preserved detailed recursive example

The following original lower-level example remains a named consumer for the
unchanged disclosed source/draft bytes and recursive-interface conformance.
Use the high-level specification above for supported researcher design edits.

Use the already selected locked main numerical environment, or the installed
`rubisco-prediction` profile in [environments](../../../../../docs/using/environments.md).
Do not synchronize just to inspect. Select the checkout explicitly. The guide
and copied files belong to that checkout/source distribution, not the wheel.

```sh
uv run --no-sync empirical-lawhood config validate \
  --consumer recursive-inquiry --config programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json
uv run --no-sync empirical-lawhood campaign recursive-explain \
  --input programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json
```

The exact copied inputs are [draft](draft.json), [kinetic supply](supply.json),
[assay query](query.json), [conditional references](comparison.json) and the
informational [disclosed assumptions](assumptions.json). The assumptions record
is a source witness inside this exposed example, not a measured preparation.
The [generator](../../../../../scripts/generate_rubisco_kinetic_example.py) owns their
original bytes and refuses replacing a changed input under the same identity.
Its `--check` mode performs no acquisition. For a different scientific design,
prepare a separately identified exact typed supply/query/comparison and lower
it with the maintained `kinetic_join_draft` owner.

Authoring validates every declared external digest and scientific role before
provider construction. Select a writable guarded operator profile and a fresh
wave directory, with enough actual space for the full source/receipt package.
Replace the selected paths below; output paths must be explicitly supplied.

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-author \
  --input /selected/checkout/programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json \
  --input-binding external.rubisco-kinetic-join.supply=/selected/checkout/programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/supply.json \
  --input-binding external.rubisco-kinetic-join.query=/selected/checkout/programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/query.json \
  --input-binding external.rubisco-kinetic-join.comparison=/selected/checkout/programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/comparison.json \
  --output-dir /selected/guarded-root/rubisco-kinetic-wave

```

## Execute, interpret and recover

The first operation consumes the actual typed supplied constants and action.
The second consumes the receipt-bound first product and reference comparison.
Covariance remains unknown, and the supported members have no probability
weights. Missing kinetics leave the corresponding assay unentered. Numerical
failures remain unevaluable. One endpoint cannot compensate for the other.

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-run --authoring-dir /selected/guarded-root/rubisco-kinetic-wave

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-result --authoring-dir /selected/guarded-root/rubisco-kinetic-wave
```

Inspect both typed products, complete member and solver-call denominators,
independent numerical discrepancies and joint assessment. Expect nomination
`NOT_ESTABLISHED`, challenge `NOT_DEMONSTRATED` and joint probability absent.
These fixed limits apply even to a fully favorable supplied-constants example.
Repeating the completed run authenticates the same completion receipts without
new assay work. The shared service refuses an uncertain contacted operation;
retain its custody rather than relabeling or automatically replaying it.

This example supports software conformance only. W2–W6 must supply independently
assessed actual molecular/chemical evidence and relevant biological calibration;
W7 must use those products in a recorded scientific decision.
The [programme contract](../../records/programme-contract.md) retains the biological target and its evidence requirements.
Select any further investigation separately, with its actual sources, resources and authority.
This exposed workflow creates no obligation to complete another programme or acquire a new release cohort.
The [release procedure](../../../../../docs/release/release-artifacts.md) owns software artifact acceptance and omitted-profile disclosure.
