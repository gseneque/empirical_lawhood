# Retain and convert exact record revisions

SPDX-License-Identifier: CC-BY-4.0

This guide gives the record-revision contract and a worked retained conversion.
It keeps original scientific meaning, canonical bytes and producing receipts separate from a derivative.
Use the exact installed decoder before selecting an explicit conversion.

## Prerequisites and first action

Select the [locked base environment](../using/environments.md) and its matching source distribution or checkout.
Select an [operator profile](../using/configuration.md) and new explicit external destinations.
For relocated results, select their current retained-access profile.
Stop if the selected disk is unavailable.

The example consumes a completed [mass-balance starter](mass-balance-starter.md) run.
Its forecast, assessment and two successful receipts must remain available.
Positive, adverse and unevaluable original results are supported.
The supplied examples are exposed software fixtures and supply no physical qualification.

Inspect the installed workflow:

```sh
uv run --no-sync empirical-lawhood workflow show mass-balance-record-upgrade --format json
```

Discovery reads static declarations.
It opens no original result and constructs no provider.

## Exact revision selection

`runtime.record_codecs.RecordCodecCatalog` indexes each exact `(schema, version)` pair.
The same Python record class can serve several operations.
Different classes cannot define the same pair.
A schema-only lookup works only when that schema has one installed revision.
An ambiguous lookup refuses and lists the installed revisions.
No decoder selects the latest revision.

Each canonical output also binds its producer's capability key, capability version and implementation digest.
The generated index retains that binding separately from its lazy record-type census.
The full catalogue and lazy catalogue use the same selection rule.
Compilation, supplier compatibility, semantic validation and retained reads preserve that selection.
The unchanged plan-output record does not acquire an inferred revision field.

A retained body must match its authenticated producer and exact canonical envelope.
A lazy body reader verifies complete retained bytes before selecting the envelope's installed decoder.
An unknown producer or revision gives an actionable refusal.
Select the original compatible installation when its decoder or producer binding is unavailable.
Installing another revision does not authorize conversion or pending execution under different source.

Historical nonrecursive producers have no generated recursive producer row.
Their authenticated reader can retain its sole installed record shape.
That compatibility path refuses an ambiguous schema or an altered known recursive producer.

Use `resolve_record_codec(codecs, schema, version)` for an authenticated exact record identity.
Use `resolve_operation_output_codec(codecs, selection, schema)` for a declared producer.
Use `snapshot_record_codecs` when a runtime retains the decoder mapping.
A plain dictionary copy loses producer bindings and cannot resolve an ambiguous family.

One operation declares one output revision per schema in its `record_codecs` map.
Declare older consumed inputs separately in `input_record_types`.
Keep earlier output producers installed when their retained products must remain readable.
Same-class reuse does not establish shared constructor or service ownership.

Issued replay selects the exact schema, revision and full issued decoder identity before reading payload bytes.
`resolve_declared_records(required_record_keys=...)` selects exact evidence revisions.
Its older schema-only form refuses a proposal containing several revisions of that schema.
Constructor dispatch routes exact schema/revision pairs to their declared owners.
Two owners of one pair still conflict.
Effect-authorizing and resource-accounting ports retain exclusive ownership.

## Supported worked transition

| Record | Meaning | Producer |
| --- | --- | --- |
| `empirical-lawhood/mass-balance/forecast@1.0.0` | Original kg forecast and prediction configuration | `mass-balance.predict@1.0.0` |
| `empirical-lawhood/mass-balance/forecast@2.0.0` | Gram derivative with complete original products, receipts and source references | `mass-balance.upgrade-forecast@2.0.0` |

The supported transition is `exact-kg-to-g`.
Each gram value equals the original kg value multiplied by exactly 1,000.
The converter uses bounded Decimal arithmetic.
A separate rational-number check verifies the unit relation.
The transition creates no measurement, new independent unit, fresh evidence or qualification.
There is no implicit reverse conversion or transition to another revision.

The source record retains both original products and their complete producing receipts.
It also retains the original authored packet, execution plan and implementation identities.
The derivative embeds that source without changing its canonical representation.
An original falsification remains `FALSIFIED`.
A missing observation remains `UNEVALUABLE` and stays in the denominator.

Select operational paths:

```sh
export EL_REVISION_SOURCE=/absolute/path/to/selected-source
export EL_REVISION_PROFILE=/absolute/path/to/operator-storage.json
export EL_ORIGINAL_PROFILE=/absolute/path/to/current-retained-access-profile.json
export EL_ORIGINAL_RUN=/absolute/external/artifacts/original-mass-run
export EL_REVISION_INPUTS=/absolute/external/artifacts/new-upgrade-inputs
export EL_REVISION_RESULTS=/absolute/external/artifacts/new-upgrade-results
export EL_REVISION_WORKERS=4
```

Set the worker count to the exact concurrency selected by the operator profile.
The local EL_2 profile selects four workers.
The example has one pure operation.

Authenticate and copy the original source:

```sh
uv run --no-sync python scripts/examples/mass_forecast_upgrade.py \
  --authoring-directory "$EL_ORIGINAL_RUN" --project-root "$EL_REVISION_SOURCE" \
  --operator-profile "$EL_REVISION_PROFILE" --source-operator-profile "$EL_ORIGINAL_PROFILE" \
  --output-directory "$EL_REVISION_INPUTS"
```

The helper uses the complete original scientific reader before writing the new input package.
It returns `specification`, `sources`, `source_snapshot` and the original read report.
Use those returned paths below.
Do not construct predecessor records or replace their identities manually.
The copied source is limited to 64 KiB and sixteen original units.
An individual source snapshot or read report is limited to 2 MiB.

## Prepare, execute and read the derivative

Retain the preparation report:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_REVISION_SOURCE" \
  --operator-profile "$EL_REVISION_PROFILE" campaign experiment-prepare \
  --input "$EL_REVISION_INPUTS/specification.json" --sources "$EL_REVISION_INPUTS/sources.json" \
  --source-snapshot "$EL_REVISION_INPUTS/source-snapshot.json" \
  --environment-id environment.mass-balance.base --workers "$EL_REVISION_WORKERS" \
  --output-root "$EL_REVISION_RESULTS" --output "$EL_REVISION_INPUTS/preparation.json"
```

The preparation must resolve the complete source and explicit operational selections.
Author the separate operation:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_REVISION_SOURCE" \
  --operator-profile "$EL_REVISION_PROFILE" campaign experiment-author \
  --input "$EL_REVISION_INPUTS/specification.json" --sources "$EL_REVISION_INPUTS/sources.json" \
  --source-snapshot "$EL_REVISION_INPUTS/source-snapshot.json" \
  --environment-id environment.mass-balance.base --workers "$EL_REVISION_WORKERS" \
  --output-dir "$EL_REVISION_RESULTS"
```

Run the returned authoring directory:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_REVISION_SOURCE" \
  --operator-profile "$EL_REVISION_PROFILE" campaign experiment-run \
  --authoring-dir "$EL_REVISION_RESULTS" --workers "$EL_REVISION_WORKERS"
uv run --no-sync empirical-lawhood --operator-profile "$EL_REVISION_PROFILE" \
  campaign experiment-read --authoring-dir "$EL_REVISION_RESULTS"
```

The operation permits one CPU, 512 MiB memory, 60 seconds, 1 MiB source bytes and 128 KiB output.
These are enforcement limits, not measured expenditure.
Ordinary invocation records and receipts retain actual work and failures.

Read `representation_disposition` separately from `original_claim_disposition` and `original_counts`.
A valid representation can preserve a falsified original claim.
The reader validates the retained unit relation without rerunning the original model or the converter.
It reports zero new measurements and no qualification.

Read the version-1 run again with its retained-access profile.
Its canonical products and receipts must remain unchanged.
Recover a completed derivative through the existing owner:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_REVISION_SOURCE" \
  --operator-profile "$EL_REVISION_PROFILE" campaign experiment-recover \
  --authoring-dir "$EL_REVISION_RESULTS" --workers "$EL_REVISION_WORKERS"
```

Completed recovery reuses the original derivative receipt.
Source changes do not permit incomplete work to switch implementation.
Keep the original compatible installation for source-bound recovery.

## Conformance and catalogue recovery

Run the disclosed revision fixture:

```sh
uv run --no-sync python -m empirical_lawhood.cli.extension_conformance \
  --fixture scripts/examples/mass_forecast_conformance.py --project-root "$EL_REVISION_SOURCE" \
  --output-dir /absolute/external/checks/new-record-revision-conformance
```

The `record-revisions` profile exercises both selected output decoders and an unsupported-producer refusal.
Its fixture contains invented, unpublished receipt metadata for software conformance only.
It cannot replace the actual retained-source exercise above.
Keep installed lifecycle and original-byte comparisons as separate acceptance evidence.

The [local catalogue recovery contract](compatibility.md#local-catalog-baseline-and-recovery) remains unchanged.
Its projection can describe both revisions through distinct original artifact and receipt identities.
Authenticate primary records before rebuilding a permitted projection.
Select a new catalogue destination or retain the existing database before an authorized replacement.
An adapter record upgrade requires no SQL schema change or receipt rewrite.
Original records remain readable when the disposable catalogue is absent.

Ordinary development recovery rebuilds its operational projection through `ExternalRunRecoveryStore.reconcile`.
That owner authenticates the original plan, recovery index, terminal events and receipts.
Keep a new persistent operational projection in selected guarded scratch.
Its task and attempt identities remain unchanged, including their original dispositions.
This operational replay grants no issued-catalogue replacement authority or scientific qualification.
