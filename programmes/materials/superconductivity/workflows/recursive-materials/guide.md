# Inspect unresolved material prerequisites

SPDX-License-Identifier: CC-BY-4.0

Programme: [Room-temperature superconductivity](../../README.md).

This guide locates the programme inputs for the shared recursive inquiry workflow.
Use the partial design to retain missing physical requirements before selecting an executable wave.
Select the [shared procedure](../../../../../docs/using/recursive-inquiry.md) and its environment before authoring.

## Inputs and first action

| Input | Role |
|---|---|
| [materials-partial.json](materials-partial.json) | Partial material inquiry with unresolved suppliers |

Copy the selected editable inputs to your working area.
Keep their originals and follow the shared guide's explain, author, run and read steps.
The installed workflow ID remains `recursive-inquiry`.

```sh
uv run --no-sync empirical-lawhood workflow show recursive-inquiry --format json
```

## Outputs and stops

The selected guide defines actual task products, retained attempts and recovery.
Exposed development inputs cannot supply fresh confirmation or physical qualification.
No physical fabrication, metrology or qualified material operand is supplied by this partial design.

[Programme overview](../../README.md) · [Shared procedure](../../../../../docs/using/recursive-inquiry.md)
