# Install and inspect a selected workflow

SPDX-License-Identifier: CC-BY-4.0

This guide gives exact software installation and inspection procedures for a selected workflow.
It separates software prerequisites from scientific inputs, source access and authority.
Use it to select a profile and inspect its controller and workers.

## Prerequisites and first action

Select the workflow through the [workflow catalogue](../reference/workflows.md).
Select the [locked environment](environments.md) for your checkout.
Use explicit external destinations for environments, exported requirements and retained reports.
Keep the source distribution that matches the selected wheel's build metadata.

List the workflow's declared installation profiles:

```sh
uv run --no-sync empirical-lawhood workflow show mass-balance-starter --format json
```

Every current workflow has a `standard` profile.
The recursive inquiry workflow also has a `battery` profile for PyBaMM acquisition.
Discovery lists these profiles without inspecting software or scientific inputs.

## Inspect software and assert prerequisites

Inspect the selected profile:

```sh
uv run --no-sync empirical-lawhood doctor \
  --workflow mass-balance-starter --profile standard --format json
```

The report binds its manifest, declaration owner, project file and dependency lock.
An installed wheel uses its original build-source metadata.
A checkout reports its actual source location and whether package worktree bytes match its reported commit.
Uncommitted bytes do not become committed source merely because the manifest inputs match.

Each environment report contains the exact required versions and actual metadata observations.
An absent distribution, incompatible version, duplicate metadata entry or unsupported platform remains an explicit failure.
A missing source binding also remains explicit.
The report preserves the workflow's scientific input roles and separate prerequisites.

To return a failing exit status when software prerequisites are unsatisfied, add `--assert-prerequisites`:

```sh
uv run --no-sync empirical-lawhood doctor \
  --workflow mass-balance-starter --assert-prerequisites --format json
```

| Mode or result | Exit behavior |
| --- | --- |
| Ordinary `doctor` or `doctor --route` | Success means inspection completed. No selected-workflow assertion occurs. |
| `doctor --workflow ID` | Success means the selected inspection completed. Read `software_prerequisites_satisfied` and the reasons. |
| Selected assertion with satisfied software prerequisites | Exit `0` |
| Selected assertion with absent, incompatible, unavailable or unbound software | Exit `3`, with the report on standard error |
| Unknown workflow/profile, conflicting selectors or malformed selections | Exit `2` |

Use `--workflow` for an assertion.
Do not combine it with the legacy `--route` selector.
An unrelated default doctor report does not establish the selected workflow's software prerequisites.
Software satisfaction does not establish scientific readiness or execution authority.

## Inspect a separate worker

Brian2 requires its own CPython `3.11.14` environment with NumPy `1.26.4` and Brian2 `2.9.0`.
The controller retains the main NumPy `2.4.6` lock.
Do not combine these NumPy pins.
After the [Brian2 environment procedure](../../programmes/biology/cell-responses/workflows/neuron-current-response/guide.md), select its exact interpreter:

```sh
uv run --no-sync empirical-lawhood doctor \
  --workflow neuron-current-response \
  --worker-python brian2=/absolute/external/brian2-env/bin/python \
  --assert-prerequisites --format json
```

An absent explicit worker selection fails the assertion without starting a worker probe.
The probe executes only the selected interpreter and standard-library metadata code.
It uses `-I -S -B` to suppress user paths, site startup files and bytecode writes.
It reads distribution metadata without importing Brian2 or another native solver.
Packages that depend on executable site-path setup can remain unavailable to this probe.
Use the documented locked installation instead of treating such a result as a successful assertion.

The report retains the selected interpreter's resolved file identity and SHA-256.
Distribution versions are metadata observations, not hashes of imported solver implementations.
Native execution retains its own numerical provenance and admission checks.

## Obtain wheel requirements before installation

The wheel contains hash-pinned requirements for each declared environment.
The matching source distribution supplies a standard-library-only export command.
It reads the selected wheel without importing or installing its package.

Set these variables to your explicit selections:

| Variable | Selection |
| --- | --- |
| `EL_SOURCE` | Matching source checkout or source distribution |
| `EL_WHEEL` | Selected wheel file |
| `EL_WHEEL_SHA256` | Exact wheel digest from its retained artifact packet |
| `EL_CONTROLLER_ENV` | New external controller environment directory |
| `EL_SOFTWARE_EXPORT` | New absolute export directory beneath an existing external parent |

Create the controller environment, then export the selected requirements:

```sh
uv venv --python 3.11.14 "$EL_CONTROLLER_ENV"
"$EL_CONTROLLER_ENV/bin/python" "$EL_SOURCE/scripts/export_workflow_requirements.py" \
  --wheel "$EL_WHEEL" --wheel-sha256 "$EL_WHEEL_SHA256" \
  --workflow mass-balance-starter --profile standard \
  --output-directory "$EL_SOFTWARE_EXPORT"
```

The command returns `selection.json` and the exact requirements paths for each declared role.
It checks the wheel digest, generated manifest binding, selected member bytes and original build-source input pins before writing.
It refuses an existing destination.
Keep a partial destination from a failed write as a failed attempt.
Choose a new destination for a corrected export.

Install the exported requirements, then install the selected wheel:

```sh
uv pip install --python "$EL_CONTROLLER_ENV/bin/python" --require-hashes \
  -r "$EL_SOFTWARE_EXPORT/controller.requirements.txt"
uv pip install --python "$EL_CONTROLLER_ENV/bin/python" --no-deps "$EL_WHEEL"
"$EL_CONTROLLER_ENV/bin/empirical-lawhood" doctor \
  --workflow mass-balance-starter --assert-prerequisites --format json
```

For Brian2, select `--workflow neuron-current-response` during export.
Its returned `brian2.requirements.txt` belongs in a separate worker environment.
Install that file with `--require-hashes`, then pass the worker interpreter to the selected doctor command.
Use the returned controller requirements for the controller.
The export supplies no installed-software observation or scientific authority.

## External software and continuing sources

A profile can declare an external executable or module file by exact digest and byte bound.
Use `--software ID=/absolute/file` only for an identifier declared by that profile.
Repeat the option for distinct declared prerequisites.
The inspector hashes the file without executing it or importing it as a module.
An absent selection or changed identity fails the selected assertion.

Continuing-source prerequisites remain separate manifest descriptions.
This command does not connect a source, create a session, inspect a live clock or obtain input access.
Its `continuing_source_state` remains `NOT_CONNECTED`.
Current installation profiles do not provide a continuing-source session implementation.

## Application and contributor interfaces

The common application operation is `workflow.environment`.
It uses the same selected inspection and assertion owner as the CLI.
Its parameters include `workflow_id`, `profile` and `assert_prerequisites`.
The scalar `worker_pythons` and `external_software` parameters use one `ID=/absolute/path` entry per line.
This operation does not need an execution storage plane.

Contributors declare profiles through `WorkflowInstallationDeclaration` beside their [public discovery facts](../development/discovery-facets.md).
Use `WorkerEnvironment` for controller-compatible or explicitly separate worker roles.
Use `ExternalSoftware` only when the selected profile actually requires that exact external file.
Keep `adapter_version` as the owning adapter's installation-contract revision.
The complete source identity remains separate from that version label.

The environment declaration owns the source-relative lock and dependency groups.
The generator uses offline frozen exports, including transitive dependencies and artifact hashes.
It resolves conditional requirements for the declared supported platform and exact interpreter.
The current target is Linux x86-64 with CPython `3.11.14`.
Unknown targets, version ranges and unhashed selected requirements refuse.

Run the [ordered projection command](../development/discovery-facets.md#regenerate-or-inspect-the-projections) after a declaration or lock change.
It updates the installation manifest after the existing workflow and configuration projections.
Keep package dependencies and pins unchanged unless a measured dependency-boundary review supports a change.

The current project declares 14 mandatory direct dependencies.
Its Linux x86-64 locked core export contains 27 distributions, including transitive dependencies.
The maintained cold-discovery inventory loads NumPy, PyArrow, SQLAlchemy and other command or storage dependencies.
It loads no optional solver stack.
This inventory does not establish a smaller supported core, so the existing dependencies and pins remain unchanged.

## Output limits and next action

The report states software prerequisites only.
Scientific inputs remain `NOT_INSPECTED`.
Resource admission, execution authority and reveal authority remain `NOT_ASSESSED`.
Scientific qualification remains `NOT_ESTABLISHED`.
No metadata inspection substitutes for a workflow's actual source or scientific admission.

When software prerequisites are satisfied, continue through the selected workflow's guide.
Retain adverse software observations and original installation identities when correcting a mismatch.
Do not relabel old results with the corrected environment's identity.
