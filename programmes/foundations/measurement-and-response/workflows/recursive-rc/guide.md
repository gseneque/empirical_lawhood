# Run the RC prerequisite construction

SPDX-License-Identifier: CC-BY-4.0

Programme: [Measurement and response](../../README.md).

This guide locates the programme inputs for the shared recursive inquiry workflow.
Select an exposed RC design, then use the shared authoring and execution procedure.
Select the [shared procedure](../../../../../docs/using/recursive-inquiry.md) and its environment before authoring.

## Inputs and first action

| Input | Role |
|---|---|
| [rc-original.json](rc-original.json) | Original complete operation graph |
| [rc-original-scientific.json](rc-original-scientific.json) | Original scientific design |
| [rc-menu-v2.json](rc-menu-v2.json) | Expanded-menu operation graph |
| [rc-menu-v2-scientific.json](rc-menu-v2-scientific.json) | Expanded-menu scientific design |
| [rc-budget-v3.json](rc-budget-v3.json) | Extended-deadline operation graph |
| [rc-budget-v3-scientific.json](rc-budget-v3-scientific.json) | Extended-deadline scientific design |

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
