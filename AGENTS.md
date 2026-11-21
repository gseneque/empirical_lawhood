# Contribute to Empirical Lawhood

SPDX-License-Identifier: CC-BY-4.0

Empirical Lawhood records how a system responds to a specified change.
Choose your task in the [contributor index](docs/v1.0/README.md).
It gives the procedure to define an investigation, add a method or add a domain.

## Run an investigation

Find the workflow and its prerequisites in the [workflow catalogue](docs/reference/workflows.md).
Select the [environment](docs/using/environments.md) for that workflow.
After setup, run project commands with `uv run --no-sync`.
Use the [configuration guide](docs/using/configuration.md) to select inputs and storage for a new investigation.
For an existing investigation, read the original records through its authorized storage profile.

Preserve the original input bytes, numerical precision and source revision.
Report the independent units and all assigned outcomes, including failures and unevaluable results.
The [results guide](docs/using/results-and-failures.md) explains what each record supports.
The [programme index](programmes/README.md) links to published findings and their limits.

## Change code or documentation

Use the [public API reference](docs/v1.0/public-api.md) to find supported interfaces.
Use the [architecture guide](docs/v1.0/architecture.md) to find the package responsible for a change.
Follow the [contribution guide](CONTRIBUTING.md) for dependencies, generated files and tests.
For documentation changes, run `uv run --no-sync python scripts/check_documentation.py` from the repository root.
