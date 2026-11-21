# Account for observed work

SPDX-License-Identifier: CC-BY-4.0

This guide gives the procedure to account for actual operations and their original measurements.
It separates nested work, shared bills and unknown costs from estimates.
Use it to retain one complete account without changing earlier receipts.

## Prerequisites and first action

Select the [locked environment](../using/environments.md) and an explicit [storage profile](../using/configuration.md).
Use the original workflow reader to obtain its permitted operational records.
Retain successful, failed and uncertain attempts in the complete selected census.
Use its original native store to read nested definitions, rosters, contacts, completions and receipts.
Do not construct replacement task rosters or scientific identities for an account.

The supported Python interface is `empirical_lawhood.api.work_costs`.
Its projections consume original records already obtained through their owning service:

```python
from empirical_lawhood.api.work_costs import (
    project_attempt_cost_work,
    project_native_cost_work,
)
from empirical_lawhood.execution.work_costs import CostCoverage

ordinary = project_attempt_cost_work(original_receipt)
nested = project_native_cost_work(
    original_inspection,
    roster=original_roster,
    parent_scope_id=ordinary["work"].scope_id,
    coverage=CostCoverage.EXCLUSIVE,
)
```

`original_receipt`, `original_inspection` and `original_roster` are the returned original records.
Each projection returns its work scope, evidence bindings, original bytes and available measurements.
Use `project_attempt_cost_work(original_contact)` when contact remains uncertain.
A declaration or unentered roster member cannot substitute for actual attempted work.

Select `EXCLUSIVE` only when the original meter excludes nested work.
Select `INCLUDING_DESCENDANTS` only when its observation includes the complete selected subtree.
An old free-text cost description does not automatically establish either interpretation.
If the original measurement scope is unclear, retain the value as source evidence and leave the aggregate quantity unknown.

## Declare the complete accounting scope

Use these inward records from `empirical_lawhood.execution.work_costs`:

| Record | Required meaning |
| --- | --- |
| `CostEvidence` | Original byte count, SHA-256 and description. A canonical source also retains its exact record identity. |
| `CostWorkScope` | One original work subject, its witnesses, parent and actual operational outcome. |
| `WorkCostMeasurement` | One quantity, original JSON value pointer, source and explicit inclusion rule. |
| `BilledResourceWindow` | One resource's actual bill over its original UTC interval and complete selected work census. |
| `WorkCostAccount` | The complete selected scope, original evidence, work, measurements and bills. |

An enclosing invocation is a separate observed scope.
Its exclusive part includes overhead outside its children.
An absent overhead measurement remains unknown.
The children do not exhaust that part merely because their measurements are available.

A recovery read is separate work with its own original observation.
Use `reuses_scope_ids` to reference earlier completed work.
Keep that earlier work in its original position.
Do not place it inside the recovery as new work.
Changed receipt labels, repeated source aliases and the same original attempt cannot create additional physical work.

The current account supports at most 4,096 work scopes, measurements and bills in each census.
It supports at most 240 original evidence files, each at most 16 MiB.
Their combined original size cannot exceed 64 MiB.
These finite metadata limits are separate from scientific payload and native output allowances.

## Read the quantities correctly

| Quantity | Aggregate rule |
| --- | --- |
| CPU seconds | Sum known measurements over disjoint work parts. A selected enclosing measurement already includes its children. |
| GPU device seconds | Require one observation of the whole account. Concurrent kernel times do not establish disjoint physical device time. |
| Retained bytes | Sum observations of disjoint retained storage. Keep separate physical native and ordinary output copies accountable. |
| Elapsed seconds | Require one original observation of the whole selected account. Do not sum concurrent component clocks. |
| Peak RSS bytes | Require one observation of the whole selected account's aggregate peak. Do not sum component peaks. |
| Billed USD | Count each original resource interval once. Keep unknown bills and omitted billing coverage explicit. |

`summarize_work_cost(account)` returns the selected observations and the original observations that were not added.
It also returns unknown observation IDs and work parts without measurements.
An enclosing known measurement can cover a child whose own cost remains unknown.
The original unknown observation stays in the report.

The `known_disjoint_subtotal` contains only the known selected components.
It is not a complete total when any work part remains unmeasured.
All arithmetic preserves the exact recorded Decimal values independently of the ambient precision.
This arithmetic property does not certify the physical meter's accuracy.
Do not substitute GPU reservations, elapsed time or billing duration for measured device time.

Conflicting measurements of the same quantity and coverage refuse.
Inconsistent additive parent and child measurements also refuse.
Keep those original observations when correcting their scope or measurement interpretation.
Do not select the more favorable value silently.

The native projection retains its original call CPU, elapsed and retained-byte observations.
It returns an original component peak separately when one exists.
A process-lifetime peak does not become a measured aggregate peak for the current account.
Missing CPU, GPU, memory, storage and financial observations remain unknown.

## Account for shared resource bills

Bind the billed amount, resource identifier and both UTC boundaries to their original JSON fields.
Repeated references to one identical resource interval contribute one charge.
Conflicting observations of that interval refuse.
Overlapping resource intervals require original disjoint observations before they can be added.
The account does not infer an allocation or split a bill between attempts.

Include every work scope covered by a shared bill.
A partial scientific consumer cannot inherit the whole bill as its own measured expenditure without an explicit allocation assessment.
The summary's billing completeness remains `DECLARED_WINDOWS_ONLY`.
No supplied bill means unknown billing, not zero expenditure.

The [deployment budget owner](../../src/empirical_lawhood/execution/deployment_budget.py) retains its separate financial supervision contract.
Its `accounted_usd` includes conservative bounds and prior-attempt policy.
Do not present that value as a new provider bill.
Use the original billed observations for actual charges.
Keep rates, projected workloads and unexecuted counterfactuals in separate estimates.

## Retain and read the account

Select a new absolute destination under the workflow's current guarded artifact writer.
Merge identical evidence bindings from the projections by their exact evidence IDs.
Refuse different bytes under the same ID.
Construct the account with sorted, unique typed tuples.
No source input or output path is inferred.

```python
from pathlib import Path
from empirical_lawhood.api.work_costs import (
    read_work_cost_account,
    retain_work_cost_account,
)

retained = retain_work_cost_account(
    account=account,
    evidence_bytes=original_permitted_bytes,
    artifact_writer=writer,
    output_directory=Path("/explicit/external/artifacts/new-cost-account"),
)
observed = read_work_cost_account(
    directory=Path(retained["directory"]),
    artifact_writer=writer,
)
```

Here, `writer` is the owning workflow's selected artifact writer.
`original_permitted_bytes` maps every evidence ID to its already admitted original bytes.
Alternatively, select `evidence_paths` with an absolute path for every permitted operational source.
Select bytes or paths, but not both.
Use the scientific workflow's access checks before obtaining cost metadata from a protected source.

The service checks complete source hashes, exact original values and actual receipt/contact relationships before publication.
It retains `account.json`, `summary.json` and every original evidence body through the existing artifact plane.
An existing destination refuses.
Preserve a partial destination after a publication failure, then select a new destination for the corrected attempt.

The retained reader authenticates the original members and reconstructs the same summary.
It performs no native calculation and creates no replacement attempt or cost event.
Its own read CPU, elapsed time and peak memory remain unknown unless separately measured.
Earlier receipts, native completions and the single-attempt inquiry-cost API retain their original revisions and meanings.

## Output limits and next action

This account records actual observations under an explicit comparison scope.
Original source hashes establish byte identity, not physical accuracy, scientific applicability or complete instrumentation.
The observer remains responsible for the declared inclusion and measurement scope.
Development custody supplies no scientific qualification, source access or execution authority.

Use the account as an input to the downstream cost assessment.
Keep measured expenditure, unpriced remaining work and estimated avoided work separate.
An unexecuted calculation receives an estimate, never a manufactured attempt receipt.
