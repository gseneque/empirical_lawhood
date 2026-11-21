# Inspect qualified prior-result capacity

SPDX-License-Identifier: CC-BY-4.0

This guide gives the finite capacity of installed prior-result records and their authenticated reader.
It preserves original tasks, companion products and native receipts across grouped prior executions.
Inspect these limits before authoring a consumer or selecting native work.

## Prerequisites and first action

Select the [locked environment](../using/environments.md) and its matching source.
Read the [exact revision contract](record-revisions.md) and [extension interfaces](extension-interfaces.md).
Run the disclosed metadata example:

```sh
uv run --no-sync python scripts/examples/prior_result_capacity.py
```

The report describes two invented original-execution locators with 432 native references and eight companion-schema references.
It reads no source, authenticates no receipt and performs no native work.
Its identifiers and digests are software fixtures, not scientific evidence or authority.

Every public [extension conformance](extension-conformance.md) report also includes `contracts.prior_result_capacity` before executable cases.
Use `runtime.recursive_qualified_parents.prior_result_capacity()` for the same pure installed report.

## Revision-1 limits

| Boundary | Installed limit and meaning |
| --- | --- |
| Prior locator | Exact `empirical-lawhood/runtime/recursive-prior-execution-binding@1.0.0` |
| Identifier field | `record_id`, `result_id`, `config_id`, `calibration_id`, `admission_id`, `evidence_id` or `receipt_id` |
| Companion products | Four distinct schema names per prior binding, each with one exact original producer |
| Scope metadata | A subset of the same four declared companion schemas |
| Native subwork | 216 distinct `(task_id, definition)` references per prior binding |
| Prior executions | 32 distinct original `(run_id, task_id)` pairs per selected parent |
| Parent bindings | 32 original qualified-parent bindings per selected authentication call |
| Primary payload | At most 16 MiB per selected primary read |
| Companion payloads | At most 16 MiB in the selected aggregate, separate from the primary payload |
| Scope metadata payloads | At most 16 MiB in the selected aggregate |

These are existing local record and read limits.
They are not a limit on every EL graph or a complete worker-memory budget.
Control records, native products, retained caches and application data have their own custody and resource limits.
Do not infer complete memory capacity by multiplying or summing payload limits.

The original seven identifier fields select actual dataclass fields on the exact installed decoded record.
The reader compares the selected value with the original record identity.
It does not search arbitrary attributes, select a newer codec or execute an import named by input data.
An unsupported field gives an explicit refusal.
Existing installed producers inspected for this contract use supported fields.

## Group original executions without losing evidence

Use the registered `qualified_parent_prior_execution_bindings` callback to project authenticated original locators.
Return each original run/task pair once.
Keep each locator's package, execution plan, authority, receipt, product and complete requested native references.
The existing Matrix programme callback in `matrix_scheduled_history.programme_qualified_parent` uses this pattern for original wave custody.

Use `inspect_prior_execution_bindings(requests)` for a pure representation preflight.
It applies the same outer census rule as the actual reader.
The report counts references and original task groups, not independent scientific units.
The domain's allocation, dependence, cutoff and complete denominator remain separate contracts.

Two distinct original groups can each retain 216 native references and four companion schemas.
Their combined representation retains 432 native references and eight companion-schema references.
Every native reference still contains its exact definition, completion and ordinary receipt identity.
No summary replaces these member identities.

Do not split one original task into duplicate prior requests to evade a limit.
A renamed binding for the same original run/task pair refuses.
Likewise, grouping scientific views does not create new independent units.

## Authenticate through the existing reader

Representation preflight establishes no availability, completion, qualification or current access.
The actual qualified-parent owner replays original issue and execution authority before protected product access.
It verifies the complete original receipt closure and calls the installed domain scope validator.
It reads the exact primary and companion bytes through their authenticated producers and installed decoders.
Native reference replay verifies original task, configuration, inputs, dependency receipts, definitions, completions and output custody.
It never repeats a native effect to repair a missing receipt.

Preserve adverse, missing, unknown and unevaluable findings.
A successful metadata report cannot make an incomplete original execution usable.
Use the original compatible source and the documented recovery route when required.

## Stop at an unsupported structure

A single binding with 217 native references or five companion schemas remains unsupported by revision 1.
A 33rd original prior execution remains unsupported by the current outer reader contract.
A new identifier field remains unsupported until an explicit installed transition exists.

First examine whether existing original task boundaries and typed product references already represent the actual case.
If they do not, retain the exact unsupported example and its scientific consumer.
Implement a versioned bounded representation or typed identity projection only for that demonstrated requirement.
Declare member, byte, depth and resource budgets before its acceptance.
Retain the old decoder, original canonical bytes and explicit transition rules.
Do not silently enlarge revision 1 or omit inconvenient companions to fit its limits.
