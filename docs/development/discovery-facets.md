# Declare public discovery facts

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for public workflow, environment and configuration declarations.
It keeps discovery facts beside their scientific or application owners.
Use it to add an extension without editing shared discovery tables.

## Prerequisites and first action

Select the checkout and its [locked environment](../using/environments.md).
Select explicit external paths for check reports and temporary files.
Read the [extension interfaces](extension-interfaces.md) before changing a declaration.

Declare routine extension facts on its one `ExtensionDeclaration` in `extension.py`.
The [public interface](../v1.0/public-api.md#one-extension-declaration) owns that contract.
Keep concrete application callbacks in application composition.

| Declaration field | Inward record | Content |
| --- | --- | --- |
| `workflows` | `execution.workflow_descriptors.WorkflowDeclaration` | Workflow identity, operations, input roles, guide, evidence limits and display state |
| `environments` | `execution.discovery_descriptors.EnvironmentDeclaration` | Route identity, exact interpreter, distribution versions and source-relative lock path |
| `configurations` | `execution.discovery_descriptors.ConfigurationDeclaration` | Input consumer, exact record locator, canonical requirement, byte bound and supplied paths |
| `installations` | `execution.installation_descriptors.WorkflowInstallationDeclaration` | Controller, worker and source prerequisites for the selected profile |

Module names in this table start with `empirical_lawhood.`.
Do not duplicate configuration consumers derived from `ExperimentProtocolDeclaration`.
Use a separate configuration declaration only for an input role without that owner.
Internal modules may define immutable values that the owning declaration references once.
They are not parallel registration entry points.

## Declare a workflow

Construct `Workflow`, `WorkflowInput` and `WorkflowOperation` through their inward module.
Wrap the workflow in `WorkflowDeclaration` with its public `display_state`.
Retain its `catalogue_order` when moving an existing declaration.
New declarations use order `1000` unless their owning guide specifies another position.
Workflow identifiers break ties within one position.
Give every operation its boundary and exact supplied input paths.
Retain the first missing prerequisite and scientific ceiling even when inputs exist.
Use paths relative to the selected source distribution.

For a documented workflow without implemented operations, set `operations_available=False` and use an empty operation tuple.
State the missing capability in `first_missing_prerequisite`.
Do not add a placeholder operation to make the workflow appear available.

The [starter workflow](../../src/empirical_lawhood/methods/mass_balance_starter/workflow.py) gives a complete example.
Its extension descriptor exports the workflow declaration.
Existing workflow identifiers and command meanings remain part of the public contract.
An owner move does not authorize a schema, revision or scientific-identity change.

## Declare an environment

The [starter environment](../../src/empirical_lawhood/methods/mass_balance_starter/public_facets.py) declares a route through the ordinary environment-discovery contract.
Distribution names must be unique after standard name normalization.
Each distribution requires an exact version.
The environment declaration also identifies dependency groups and supported platforms for exact installation exports.
Keep the separate Brian2 interpreter and NumPy pins with their owning environment.

Inspect a declared route through the existing doctor command:

```sh
uv run --no-sync empirical-lawhood doctor --route mass-balance --format json
```

This mode reads installed distribution metadata and interpreter information.
It does not import native solvers or establish workflow readiness.
It does not inspect scientific inputs, obtain source access or authorize execution.
An absent or incompatible dependency appears in the report.
An unknown route refuses.
Installation and selected-workflow prerequisites remain separate procedures.
Use [workflow installation](../using/workflow-installation.md) for a selected software assertion through `doctor --workflow`.

## Regenerate or inspect the projections

Run the ordered entry point after an owner change:

```sh
uv run --no-sync python scripts/generate_extension_projections.py --json
```

It invokes the existing owners in this order:

1. Extension aggregate, API runtime bindings and inert public discovery projections.
2. Executable aggregate and recursive operation index.
3. CLI reference.
4. Workflow catalogue.
5. Configuration schemas and index.
6. Exact workflow installation manifests and hash-pinned environment exports.

Examine each generated diff before accepting the change.
Keep generated fingerprints and schema projections under their generator owners.
Static configuration declarations use a stable consumer-identifier order.
Its record schemas and public consumer identifiers retain their original meanings.

For a check without source writes, use:

```sh
uv run --no-sync python scripts/generate_extension_projections.py --check --json
```

The JSON report gives each stage's command, status, elapsed time and bounded diagnostics.
The check visits every stage, including stages after a failure.
It reports duplicate owners, missing declarations and independently detectable stale projections together.
An invalid declaration prevents comparison of the projections that depend on it.
Regeneration stops dependent stages after a failure.
The extension generator validates all its declarations before writing its projections.

Each stage has a 180-second software check limit and bounded output capture.
This limit does not constrain scientific execution.
A failed or incomplete stage returns a failing exit status.
Correct the owning declaration, then repeat the affected check.

## Evidence limits and next action

Generated discovery modules contain inward constructors and static values.
Public discovery does not load their adapter owners, construct providers or read scientific inputs.
Generator checks inspect code declarations and documentation in the selected source.
They supply software evidence only.
They do not establish scientific qualification, source access, resource admission or reveal authority.

Run the affected focused checks and [documentation checks](testing.md) after the projections are current.
Retain exact source and check results with the contribution.
Continue through the [extension recipe](extending-the-engine.md) for executable behavior and installed acceptance.
