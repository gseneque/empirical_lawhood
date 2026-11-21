# Install EL and run the first investigation

SPDX-License-Identifier: CC-BY-4.0

This guide selects the environment for the first recursive investigation.
The example uses exposed mass observations and pure Decimal arithmetic.
Install the source, then follow the complete investigation recipe.

## Prerequisites

Use Linux x86-64 and CPython 3.11.14 for the documented release environment.
The example requires no GPU, native solver, cloud account or signing key.
Choose a new writable directory for its inputs and retained results.

For a source checkout or extracted source distribution:

```sh
uv sync --locked --python 3.11.14
uv run --no-sync empirical-lawhood --help
uv run --no-sync empirical-lawhood workflow show mass-balance-starter --format json
```

Select the environment once, then use `uv run --no-sync` for later commands.
The [environment guide](using/environments.md) owns optional dependencies and frozen numerical settings.
A solver-specific investigation uses its declared profile.

## First investigation

Follow [Define or modify an investigation](v1.0/define-investigation.md).
It gives the complete inputs, commands, expected results and failure handling.
The predictor calculates final mass from initial and added mass.
A separate assessment compares its retained predictions with supplied observations.

The guide retains all three cases: supported, falsified and unevaluable.
Its three independent units are exposed examples, not fresh physical evidence.
Successful execution supplies no scientific qualification.

## Installed usage

Install the release wheel into the selected environment.
Use the wheel's matching source distribution for editable examples and source-bound operations.
The distribution metadata's `Documentation` URL identifies its source revision.

An activated installed environment uses the same commands without the `uv run --no-sync` prefix.
Public imports and operation contracts are identical in checkout and installed use.
The wheel supplies read-only assets and implementations; mutable run data belongs in your explicit output root.
Do not use an unrelated checkout as the installed implementation's source identity.

## Choose the next job

- [Add a reusable method](v1.0/add-method.md).
- [Add a domain or native substrate](v1.0/add-domain.md).
- [Read the public API contract](v1.0/public-api.md).
- [Select a research programme](../programmes/README.md).
- [Interpret results and interrupted attempts](using/results-and-failures.md).

The packaged reactor-prefix demonstration remains available through the workflow catalogue.
The mass-balance route introduces the canonical recursive execution and custody services used by the three public jobs.
