# Run the battery state-supply construction

SPDX-License-Identifier: CC-BY-4.0

Programme: [Battery charging](../../README.md).

This guide locates the programme inputs for the shared recursive inquiry workflow.
Use the two-wave design to assess continuation and inspect a later voltage response.
Select the [shared procedure](../../../../../docs/using/recursive-inquiry.md) and its environment before authoring.

## Inputs and first action

| Input | Role |
|---|---|
| [battery-wave-a.json](battery-wave-a.json) | Wave A exposed operation graph |
| [battery-protocol.md](battery-protocol.md) | Frozen scientific design and limits |

Copy the selected editable inputs to your working area.
Keep their originals and follow the shared guide's explain, author, run and read steps.
The installed workflow ID remains `recursive-inquiry`.

```sh
uv run --no-sync empirical-lawhood workflow show recursive-inquiry --format json
```

## Outputs and stops

The selected guide defines actual task products, retained attempts and recovery.
Exposed development inputs cannot supply fresh confirmation or physical qualification.
Read the [complete results](../../records/recursive-prerequisite-results.md) before selecting a new execution.

[Programme overview](../../README.md) · [Shared procedure](../../../../../docs/using/recursive-inquiry.md)
