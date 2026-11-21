# Build an editable isolated native extension

SPDX-License-Identifier: CC-BY-4.0

This guide gives a bounded Linux development example with an explicit worker interpreter.
It separates process return, nested completion and ordinary parent publication.
Use the input helper before the ordinary experiment commands.

## Prerequisites

Select the [locked controller environment](../using/environments.md) and the exact associated source.
Read the [native progress contract](native-subwork.md) and [extension interfaces](extension-interfaces.md).
Select an [operator profile](../using/configuration.md) and new external input, artifact and scratch destinations.
The example supports CPython 3.11.14 on Linux x86_64.
Other host profiles require separate acceptance.

The calculation sums the squares of integers from zero through the selected final integer.
The final integer must be between zero and 1024, inclusive.
These exposed arithmetic operands establish software behavior only.
They supply no physical observation, fresh confirmation or scientific qualification.

The `standard` installation profile uses the main locked dependencies in both interpreters.
The `separate-numpy` profile selects a separate [worker project](../../environments/isolated-native-starter/pyproject.toml) and its lock.
Its NumPy version is 2.3.5.
The controller retains NumPy 2.4.6.
The worker receives the same selected implementation through its own installation.

Select explicit paths:

```sh
export EL_SOURCE=/absolute/path/to/selected-source
export EL_PROFILE=/absolute/path/to/operator-storage.json
export EL_STARTER_INPUTS=/absolute/external/artifacts/isolated-starter-inputs
export EL_STARTER_ARTIFACTS=/absolute/external/artifacts/isolated-starter-result
export EL_STARTER_SCRATCH=/absolute/external/scratch/isolated-starter
export EL_STARTER_WORKER_ENV=/absolute/external/environments/isolated-starter
```

The input directory must be below the profile's artifact root.
The scratch directory must be below its separate scientific scratch root.
The shared service selects usable concurrency within the profile and host limits.
This design contains one task.
For a new exposed local workspace, use the [public workspace constructor](../v1.0/public-api.md#investigation-application-operations).
An existing study retains its original selected storage requirements.

For the separate worker profile, install its frozen dependencies in the new selected environment:

```sh
UV_PROJECT_ENVIRONMENT="$EL_STARTER_WORKER_ENV" \
  uv sync --project "$EL_SOURCE/environments/isolated-native-starter" --locked --python 3.11.14
uv pip install --python "$EL_STARTER_WORKER_ENV/bin/python" --no-deps --editable "$EL_SOURCE"
```

This command selects a separate development environment.
It does not synchronize the controller environment.
For installed acceptance, install the exact built wheel in each environment instead of an editable source.
Use [workflow installation](../using/workflow-installation.md) to export the wheel's selected hash-pinned requirements before installation.

## First action

Discover the static workflow and inspect the explicitly selected worker:

```sh
uv run --no-sync empirical-lawhood workflow show isolated-native-starter --format json
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" doctor \
  --workflow isolated-native-starter --profile separate-numpy \
  --worker-python "calculation=$EL_STARTER_WORKER_ENV/bin/python" --assert-prerequisites --format json
```

Discovery constructs no provider and performs no native initialization.
The selected doctor observes dependency metadata without importing the numerical engine.
Its result establishes software prerequisites only.

Create the canonical input bindings:

```sh
uv run --no-sync python scripts/examples/isolated_native_starter.py \
  --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  --worker-python "$EL_STARTER_WORKER_ENV/bin/python" --last-integer 64 \
  --output-directory "$EL_STARTER_INPUTS" --scratch-directory "$EL_STARTER_SCRATCH"
```

The helper observes the interpreter, package entry, dependency and full selected source.
It derives the specification, source selection and implementation snapshot.
It creates no native contact or task roster.
Use its returned paths without editing their hashes.

## Prepare, author, run and read

Prepare and author through the ordinary experiment owner:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-prepare --input "$EL_STARTER_INPUTS/specification.json" \
  --sources "$EL_STARTER_INPUTS/sources.json" --source-snapshot "$EL_STARTER_INPUTS/source-snapshot.json" \
  --environment-id environment.isolated-native-starter \
  --output-root "$EL_STARTER_ARTIFACTS" --output "$EL_STARTER_INPUTS/preparation.json"
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-author --input "$EL_STARTER_INPUTS/specification.json" \
  --sources "$EL_STARTER_INPUTS/sources.json" --source-snapshot "$EL_STARTER_INPUTS/source-snapshot.json" \
  --environment-id environment.isolated-native-starter \
  --output-dir "$EL_STARTER_ARTIFACTS"
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-run --authoring-dir "$EL_STARTER_ARTIFACTS"
uv run --no-sync empirical-lawhood --operator-profile "$EL_PROFILE" \
  campaign experiment-read --authoring-dir "$EL_STARTER_ARTIFACTS"
```

The ordinary parent derives the native definitions from the exact prepared inputs and actual attempt.
The selected child checks its full invocation and environment before contact.
NumPy calculates the vector dot product.
The parent compares its original returned integer with `n(n+1)(2n+1)/6`, using Python integer arithmetic.
An unequal value produces `FALSIFIED` without becoming a retryable operational error.
For `n = 64`, both independent calculations return 89440.

The reader authenticates the stored comparison without another calculation or provider.
It retains the original attempt, result identity, dependency version and qualification ceiling.

## Interruption and recovery exercise

The input helper accepts `--fault` for these disclosed software controls.
Prepare a new input, artifact and scratch selection for each control.
Do not change a retained configuration or remove an earlier attempt.

| Selection | Deliberate interruption | Retained native state |
| --- | --- | --- |
| `none` | No interruption | Completed native and ordinary outputs |
| `before-contact` | Child exits after begin and before calculation contact | `BEGUN`; no calculation return |
| `after-contact` | Child exits after calculation contact | `UNKNOWN_COMPLETION`; replay refuses |
| `after-nested-completion` | Child exits after its calculation receipt | Completed calculation bytes and a separate adverse process return |
| `before-parent-completion` | Ordinary worker exits after complete nested custody | Completed nested bytes with unfinished ordinary publication |

Inspect the original retained result before recovery.
Then use the ordinary command:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-recover --authoring-dir "$EL_STARTER_ARTIFACTS"
```

Completed recovery uses the original attempt and authenticated bytes.
Its read-only native port supplies no new begin, contact or calculation.
Uncertain contact remains an exact refusal.
A known child exit cannot supply a missing nested receipt or parent result.
The selected interruption remains visible in the original specification.

The `before-parent-completion` control returns exit 2 with an incomplete-parent message.
Its completed nested work remains retained.
Use `experiment-read --allow-partial` to inspect that state, then recover the original attempt after its execution claim releases.
The before-contact and adverse-child-return controls remain failed after recovery.
The after-contact control remains blocked with unknown completion.

The retained SCI02-D publication-failure acceptance supplies a separate existing reference-bundle recovery case.
Its original v1 inputs, compatible installation and native receipts remain unchanged.
The starter does not reacquire that reference bundle.

## Resource and cost meaning

The example requests one CPU, 1 GiB of memory and 120 seconds of wall time per task.
The trusted local executor applies per-process restrictions and observes the process group.
It does not enforce an aggregate process-tree memory quota.
These selected bounds apply to this disclosed developer calculation.
They impose no deadline on another native route.
The source scan allowance is 2 MiB.
The combined native and ordinary output allowance is 512 KiB.
Each process log contains at most 32 KiB of original bytes.
Its typed record preserves empty and binary streams through exact base64, byte-count and SHA-256 fields.

The complete control invocation is at most 64 KiB.
It contains the small original configuration, integer operand and native definition census.
Its bytes enter sealed anonymous backing.
The original source census remains in authenticated external input storage and the shared prepared invocation contract.
It is not copied into the numerical control payload.
Large scientific arrays require the existing authenticated array and allocation contracts, not a larger inline control object.

The NumPy vector contains at most 1025 signed 64-bit integers, or 8200 data bytes.
This size is not the worker's memory requirement.
Interpreter, library, prepared-contract, transport and operating-system memory remain separate costs.
The typed native result retains the actual Linux process-lifetime peak RSS as a component observation.
That peak is neither a concurrent process-tree peak nor an additional additive allocation.
Use the selected acceptance packet's observations for profile admission.

The native result measures CPU and wall clocks around the numerical call.
The original process return separately measures the inclusive child and relay window.
Those windows overlap.
The launcher completion leaves its exclusive cost unknown.
Do not add the inclusive launcher clock to the nested calculation clock.

Use the [aggregate cost handoff](work-cost-accounting.md) for a multi-operation account.
Bind original successful, failed and recovered invocations to their actual measurement windows.
Retain unknown overhead and shared billing windows explicitly.
An observed component peak or elapsed interval cannot establish an aggregate through addition.

## Change and verify the extension

The [records](../../src/empirical_lawhood/adapters/isolated_native_starter/records.py) own exact revisions, bounds and exposed selections.
The [pure method](../../src/empirical_lawhood/methods/isolated_native_starter/calculation.py) owns the vector calculation and independent integer formula.
The [native entry](../../src/empirical_lawhood/adapters/isolated_native_starter/native_entry.py) measures the selected interpreter and calls that method.
The [ordinary runner](../../src/empirical_lawhood/adapters/isolated_native_starter/runner.py) owns process integration, publication and retained-result comparison.
The [work owner](../../src/empirical_lawhood/adapters/isolated_native_starter/work.py) derives original definitions and selects the existing launcher.
The [API helper](../../src/empirical_lawhood/api/isolated_native_starter.py) prepares inputs and presents retained findings.

Copy the adapter package, API helper, API composition and input command before changing their namespace.
Update the protocol, schemas, workflow, installation declarations and guide together.
Implement the new calculation and its independent falsifier before accepting another calculation label.
Keep original completed records and unknown contacts under their original identities.

Regenerate the [ordered extension projections](discovery-facets.md).
Run the affected focused checks and documentation check in the selected environment:

```sh
uv run --no-sync pytest --fail-on-skip tests/test_isolated_native_starter.py
uv run --no-sync ruff check src/empirical_lawhood/adapters/isolated_native_starter \
  src/empirical_lawhood/api/isolated_native_starter.py tests/test_isolated_native_starter.py
uv run --no-sync python scripts/check_documentation.py
```

Inspect the disclosed declaration and codec fixture through the existing [conformance runner](extension-conformance.md):

```sh
uv run --no-sync python -m empirical_lawhood.cli.extension_conformance \
  --fixture scripts/examples/isolated_native_conformance.py --project-root "$EL_SOURCE" \
  --output-dir /absolute/external/checks/new-isolated-starter-conformance
```

This `isolated-native-contracts` selection performs no native calculation.
It does not replace the installed interruption exercise.

Then build the settled source through its sdist with the [artifact owners](../release/release-artifacts.md).
Exercise the installed discover, prepare, author, run, read and recovery commands outside the checkout.
Retain source, installation, original receipt, refusal, resource and cost evidence together.
Software acceptance does not qualify a scientific claim.
