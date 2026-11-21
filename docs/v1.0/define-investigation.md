# Define or modify an investigation

SPDX-License-Identifier: CC-BY-4.0

This guide runs a complete investigation through EL's recursive services.
You supply scientific inputs and choices; EL derives the plan and retains the work.
For your own question, first identify its [scientific decisions and prerequisite relationships](from-question-to-investigation.md).
The exposed mass-balance example below demonstrates the complete lifecycle.
Its closed additive protocol is a starting example, not a universal schema for every scientific question.

## Prerequisites

Select the [base environment](../getting-started.md).
Use the matching checkout or source distribution and a new output root outside that source tree.
The example needs no GPU, native solver, cloud account, signing key or maintainer-specific mount.

The scientific question is whether initial mass plus added mass agrees with observed final mass.
A predictor receives initial and added mass only.
An independent assessment compares its retained forecast with the supplied final observation.
The example has three independent units and an explicit tolerance in kg.

## Run the complete example

From the selected source root, run:

```sh
uv run --no-sync python scripts/examples/v1_investigation.py \
  --project-root "$PWD" \
  --workspace /absolute/work/el-first-positive \
  --case positive --tolerance-kg 0.01
```

Replace the workspace path with your new explicit destination.
The [complete starter](../../scripts/examples/v1_investigation.py) uses only documented public contracts.
It creates a local storage profile, prepares inputs, derives the plan, executes it, reads retained results and checks completed recovery.
The output reports the exact profile, authoring directory and diagnostic paths.
The starter displays progress on stderr and writes `scratch/progress.json` for
a second terminal or UI. Use `--no-progress` to silence its stderr display.
The [shared progress guide](../using/progress.md) explains counts, unknown totals,
heartbeats and the distinction between operation return and scientific support.

| Output | Meaning |
| --- | --- |
| `operator-storage.json` | Derived operational profile for the selected root; it grants no scientific authority |
| `scratch/evidence.json` | Supplied exposed scientific observations |
| `scratch/inputs/specification.json` | Scientific definition with evidence identity, units, selected population and tolerance |
| `scratch/inputs/sources.json` | Derived original-input bindings |
| `scratch/preparation.json` | Prerequisites, complete census, automatic operational selection and authored-object trace |
| `artifacts/investigation/` | Authenticated authored plan, original input publications, execution and retained results |
| `scratch/result.json` | Readable presentation of the original scientific results |
| `scratch/recovery.json` | Recovery report for the already completed work |
| `scratch/progress.json` | Advisory phase/workflow counters, elapsed times and bounded completed-step summaries |

For the positive case, the scientific result has three `SATISFIED` units.
Its `assigned_units` is `3`, and its qualification remains `NOT_ESTABLISHED`.
The readout reports `scientific_reconstruction_performed: false`.
A successful result read authenticates original products and does not repeat either calculation.

## Change the scientific choice

Run another case in a separate new workspace:

```sh
uv run --no-sync python scripts/examples/v1_investigation.py \
  --project-root "$PWD" \
  --workspace /absolute/work/el-first-adverse \
  --case adverse --tolerance-kg 0.01

uv run --no-sync python scripts/examples/v1_investigation.py \
  --project-root "$PWD" \
  --workspace /absolute/work/el-first-unevaluable \
  --case unevaluable --tolerance-kg 0.01
```

| Supplied case | Complete denominator | Claim disposition | What changed |
| --- | ---: | --- | --- |
| `positive` | 3 | `SATISFIED` | All supplied final observations agree within tolerance |
| `adverse` | 3 | `FALSIFIED` | One final observation exceeds the tolerance |
| `unevaluable` | 3 | `UNEVALUABLE` | One original final observation is absent |

A falsified or unevaluable claim can be a successfully completed software operation.
The missing unit remains in the denominator.
The example makes no claim about physical measurements or new independent support.

Change `--tolerance-kg` only when that is the scientific choice you intend.
For new evidence, use `api.mass_balance_starter.create_inputs` with your selected canonical evidence file.
It derives the evidence identity and original-input selection.
It rejects incompatible units, record revisions and scientific scope.
Do not edit hashes, task identifiers, generated plans or receipts.

### Supply your own evidence

The public records let you declare the population, source, receiver, clock and
complete independent-unit census explicitly. This example retains one absent final
observation and writes exact Decimal bytes to a new file:

```python
from decimal import Decimal as D
from pathlib import Path
from empirical_lawhood.methods.mass_balance_starter import MassScope, MassObservation, MassEvidence

scope = MassScope("population.my-cases", "source.my-observations",
    "receiver.final-mass", "clock.after-addition")
rows = (
    MassObservation("case.1", D("1"), D("1.2"), D("2.2")),
    MassObservation("case.2", D("3"), D("0.5"), None),
)
evidence = MassEvidence("my.mass.evidence", scope, tuple(row.unit_id for row in rows), rows)
with Path("/absolute/work/my-evidence.json").open("xb") as stream:
    stream.write(evidence.canonical_bytes())
```

Choose an existing writable parent for the evidence file, then run:

```sh
uv run --no-sync python scripts/examples/v1_investigation.py \
  --project-root "$PWD" \
  --workspace /absolute/work/el-my-evidence \
  --evidence /absolute/work/my-evidence.json --tolerance-kg 0.01
```

The public input owner copies the selected original bytes and derives all identities.
The result retains two assigned units, one `SATISFIED` and one `UNEVALUABLE`;
the claim is `UNEVALUABLE` and qualification is `NOT_ESTABLISHED`.
The supported domain is closed additive mass in kg with one to sixteen units.
Use a domain-specific protocol for different units, procedures or scientific scope.

### Compose another investigation

The [composition guide](compose-investigation.md) provides a complete executable
second investigation that consumes this run's authenticated original forecast,
assessment and receipts. It also identifies the strict protocol interface for
composing your own declared scientific operations.

## Use the application API

The starter follows this public sequence:

```python
from pathlib import Path
from empirical_lawhood.api.investigations import (
    create_local_workspace,
    create_investigation_service,
    prepare_investigation,
    experiment_preparation_report,
)

project = Path("/absolute/selected/source")
workspace = create_local_workspace(Path("/absolute/work/new-investigation"), project_root=project)
service = create_investigation_service(project_root=project, operator_profile=workspace.profile_path)
preparation = prepare_investigation(
    service,
    specification_path=Path("/absolute/prepared/specification.json"),
    source_selection_path=Path("/absolute/prepared/sources.json"),
    environment_id="environment.mass-balance.base",
)
print(experiment_preparation_report(preparation))
if not preparation.executable:
    raise ValueError("Resolve the reported dependencies before authoring")
directory = workspace.artifact_root / "investigation"
service.author(preparation=preparation, output_dir=directory)
service.run(directory=directory)
result = service.read(directory=directory)
service.recover(directory=directory)
```

Keep execution inside a `main()` function protected by `if __name__ == "__main__":`.
The complete starter supplies that guard for process workers.
The API selects worker capacity from the actual environment and operator profile.
Method resource requirements and frozen numerical settings remain authoritative.
An explicit concurrency override is an operational limit, not a scientific parameter.

## Inspect the same result through the CLI

Use the paths printed by the starter:

```sh
uv run --no-sync empirical-lawhood \
  --operator-profile /absolute/work/el-first-positive/operator-storage.json \
  campaign experiment-read \
  --authoring-dir /absolute/work/el-first-positive/artifacts/investigation
```

The [workbench guide](../using/research-workbench.md) registers these same profile and authoring paths.
CLI and workbench use the shared application operations and original custody.
Neither presentation layer calculates another scientific result.

## Trace a failure

Start with the authored specification identity in `scratch/preparation.json`.
Its trace locates each generated operation and owning implementation.
Inspect the retained attempt or diagnostic location reported by the application.
The structured diagnostic identifies the operation, contract, owner, expected and actual state when available, and remediation layer.

Inspect retained execution failures through the same application operation used by the workbench:

```sh
uv run --no-sync empirical-lawhood \
  --operator-profile /absolute/work/el-first-positive/operator-storage.json \
  campaign recursive-execution \
  --authoring-dir /absolute/work/el-first-positive/artifacts/investigation \
  --limit 50
```

The paginated task rows include a `diagnostic` when an authenticated failure event exists.
Its authored trace identifies the selected capability, configuration and implementation;
its evidence identifies the original attempt, event and retained record path.
The declared resource bounds remain visible. The view does not reread scientific result
bodies or reconstruct a scientific result. Successful operations have no synthetic failure.
Use the returned cursor to inspect another page, or `--filter` to select matching rows.

An execution classification is not proof of a defect in a scientific calculation.
The diagnostic therefore reports the retained classification and safely available
contract state, without inventing undisclosed operand values or a native exception.
`READ_ONLY_RECONCILIATION` means the original native completion remains uncertain;
the view grants no retry permission. The workbench's execution view exposes these
same diagnostic objects through `recursive.execution`.

| Failure | Action |
| --- | --- |
| Workspace already exists | Select a new destination, or inspect the retained original through its printed profile |
| Scientific units, scope or input identity differ | Correct the authored scientific definition or select the actual original input |
| Preparation reports missing prerequisites | Resolve the named dependency; do not edit the derived plan |
| Source or numerical environment differs | Select the declared implementation and environment before new execution |
| Resource placement is unsupported | Inspect the explicit capability reason and select a supported operational placement |
| Native contact is uncertain | Preserve the record and use read-only reconciliation; do not automatically replay |

Use [results and failures](../using/results-and-failures.md) for detailed custody and recovery procedures.
The ordinary low-level execution contracts are available to framework authors.
They are unnecessary for this public investigation job.

## Continue recursively

A supplied forecast and a supported physical claim are different outcomes.
Use [recursive inquiry](../using/recursive-inquiry.md) when an unmet requirement needs another investigation.
The scientific definition selects the supplier, its conditions and the assessment of its contribution.
EL derives the operation graph and retains the original relationship through execution and later reuse.
