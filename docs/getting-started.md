# Run your first example

SPDX-License-Identifier: CC-BY-4.0

This guide installs the reactor example and produces a readable report.
It introduces the configure, run and inspect sequence used by the engine.
Use a source checkout or source distribution and select a new output directory.

## Prerequisites

The tested host is Linux x86-64 with CPython 3.11.14.
Start in an unactivated shell at the source root.
Read the [environment support table](using/environments.md) before selecting a different profile.

## Install and run

```sh
uv sync --locked --python 3.11.14 --group reactor-example
uv run --no-sync empirical-lawhood --help
uv run --no-sync empirical-lawhood doctor --route reactor --format json
uv run --no-sync empirical-lawhood capability list --limit 5 --format json
uv run --no-sync empirical-lawhood example reactor-prefix --output-dir ./example-output/reactor-prefix
```

Select another explicit output directory if this destination already contains a run.
After environment selection, use `uv run --no-sync` for subsequent commands.

## Read the report

Open `example-output/reactor-prefix/report.md` first.
The example uses packaged public inputs and performs 20 short native branches
with 40 observed decisions.

| Output | Purpose |
|---|---|
| `report.md` | Readable findings and limits |
| `report.json` | Exact clocks and summaries |
| `panel.json` | Canonical episode record |

An input is prepared, a fixed response route is applied, and the records show
whether the declared conditions were met.
This is an unqualified local numerical demonstration.
Its five independent units contain nested arms and numerical views.
The fixed exposed inputs provide no fresh independent support and do not
reproduce the paper's historical observations.
The example needs no operator profile or scientific authority.
Other workflows retain their own requirements.

## Choose the next action

- [Change the RC model](../programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md).
- [Inspect the reactor study and its assigned lifecycle](../programmes/foundations/measurement-and-response/workflows/reactor-response/guide.md).
- [Choose a research programme](../programmes/README.md).
- [Design and run a supported study](using/designing-and-running-an-experiment.md).
- [Interpret results, refusals and interrupted attempts](using/results-and-failures.md).

Guide and editable input files belong to the selected source checkout or
distribution. The installed wheel supplies the CLI, static catalogue and
packaged example. Select the source files explicitly for other workflows.
