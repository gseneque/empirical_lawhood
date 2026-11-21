# Build an editable mass-balance extension

SPDX-License-Identifier: CC-BY-4.0

This guide gives a complete small development extension.
It separates a mass forecast, an independent falsifier and the availability of their scientific inputs.
Use the exposed examples before you change the domain contract.

## Prerequisites

For the first complete run, use the [v1.0 investigation guide](../v1.0/define-investigation.md).
Its public starter derives the storage profile and operational worker selection.
This page gives the domain protocol details and equivalent individual CLI stages.

Select the [locked base environment](../using/environments.md) and its matching source.
The example needs supplied canonical evidence and pure Decimal arithmetic only.
It requires no native solver, signing key, copied grant or source acquisition.
Its observations are exposed arithmetic fixtures, not physical measurements or qualification evidence.

Select one new local workspace outside the source tree:

```sh
export EL_SOURCE="$PWD"
export EL_STARTER_ROOT=/absolute/work/mass-balance
uv run --no-sync python - "$EL_STARTER_ROOT" "$EL_SOURCE" <<'PYTHON'
from pathlib import Path
import sys
from empirical_lawhood.api.investigations import create_local_workspace
workspace = create_local_workspace(Path(sys.argv[1]), project_root=Path(sys.argv[2]))
print(workspace.profile_path)
PYTHON
export EL_PROFILE="$EL_STARTER_ROOT/operator-storage.json"
export EL_STARTER_INPUTS="$EL_STARTER_ROOT/scratch/mass-balance"
export EL_STARTER_ARTIFACTS="$EL_STARTER_ROOT/artifacts/mass-balance"
```

Replace the workspace root with your explicit new destination.
The public constructor derives the operational profile from usable host capacity.
The two dependent operations still execute in scientific order.
An explicit concurrency limit remains optional.

Run from the matching source with the selected environment.
Installed usage runs the same commands with the installed interpreter and matching source distribution.
Do not synchronize an installed scientific environment merely to inspect results.

## First action

Discover the registered workflow:

```sh
uv run --no-sync empirical-lawhood workflow show mass-balance-starter --format json
```

Discovery reads static facts only.
It does not inspect evidence, check prerequisites or construct a provider.

Copy the exposed positive, adverse and unevaluable evidence:

```sh
uv run --no-sync python scripts/examples/mass_balance_starter.py examples \
  --output-directory "$EL_STARTER_INPUTS/examples"
```

Each file contains the same complete three-unit census.
The adverse file changes one final observation.
The unevaluable file retains that unit with a missing final observation.
The helper returns the exact paths.
It also writes `incompatible-units.json`, a deliberately invalid input that changes kg to g.
The input helper must refuse this file before it creates an input package.

Prepare the positive input bindings:

```sh
uv run --no-sync python scripts/examples/mass_balance_starter.py inputs \
  --evidence "$EL_STARTER_INPUTS/examples/positive.json" --tolerance-kg 0.01 \
  --project-root "$EL_SOURCE" --output-directory "$EL_STARTER_INPUTS/positive"
```

This helper preserves the supplied canonical bytes.
Typed constructors derive the evidence identity, specification, source selection and implementation snapshot.
Use its returned `specification`, `sources` and `source_snapshot` paths in the following commands.
Do not edit their hashes or construct a task roster yourself.

## Prepare, author and run

Inspect the exact preparation and retain its report:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-prepare --input "$EL_STARTER_INPUTS/positive/specification.json" \
  --sources "$EL_STARTER_INPUTS/positive/sources.json" \
  --source-snapshot "$EL_STARTER_INPUTS/positive/source-snapshot.json" \
  --environment-id environment.mass-balance.base \
  --output-root "$EL_STARTER_ARTIFACTS/positive" \
  --output "$EL_STARTER_INPUTS/positive-preparation.json"
```

The report must resolve the original evidence and the explicit operational selections.
Its census contains three independent units, two pure operations and zero native effects.
Missing inputs or operational selections remain classified prerequisites.
Preparation grants no scientific or outcome-access authority.

Author the complete design through the ordinary owner:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-author --input "$EL_STARTER_INPUTS/positive/specification.json" \
  --sources "$EL_STARTER_INPUTS/positive/sources.json" \
  --source-snapshot "$EL_STARTER_INPUTS/positive/source-snapshot.json" \
  --environment-id environment.mass-balance.base \
  --output-dir "$EL_STARTER_ARTIFACTS/positive"
```

The lowerer derives both tasks, the predecessor and the exact scientific consumer.
Use the returned authoring directory for execution:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-run --authoring-dir "$EL_STARTER_ARTIFACTS/positive"
```

Each operation has one CPU, a 512 MiB memory limit and a 60-second wall limit.
Its source-byte limit is 1 MiB and its result limit is 128 KiB.
These limits are enforcement bounds, not measured consumption.
The ordinary invocation records and receipts retain actual operational costs and attempts.

## Read results and recover

Read the actual retained findings:

```sh
uv run --no-sync empirical-lawhood --operator-profile "$EL_PROFILE" \
  campaign experiment-read --authoring-dir "$EL_STARTER_ARTIFACTS/positive"
```

This reader authenticates retained products through the ordinary custody owner.
It presents the stored findings without a provider or another prediction or assessment calculation.
It reports `scientific_reconstruction_performed: false` and preserves every original unit.

Exercise receipt recovery:

```sh
uv run --no-sync empirical-lawhood --project-root "$EL_SOURCE" --operator-profile "$EL_PROFILE" \
  campaign experiment-recover --authoring-dir "$EL_STARTER_ARTIFACTS/positive"
```

A completed run reuses its original successful receipts.
An interrupted run uses the same owner and its retained attempt rules.
Do not remove failure records or create another run to hide an original failure.
Read [results and failures](../using/results-and-failures.md) before any further recovery selection.

Repeat input preparation, authoring and execution for `adverse.json` and `unevaluable.json` in separate new directories.
Keep the same tolerance of `0.01` kg.

| Example | Complete denominator | Claim disposition | Complete forecast supplied |
| --- | --- | --- | --- |
| Positive | 3 | `SATISFIED`: all three residuals are within tolerance | `SATISFIED` |
| Adverse | 3 | `FALSIFIED`: one residual exceeds tolerance | `SATISFIED` |
| Unevaluable | 3 | `UNEVALUABLE`: one final observation is absent | `SATISFIED` |

The final column concerns the forecast input to the falsifier.
It does not assert the truth of the mass-balance claim.
Every example retains `NOT_ESTABLISHED` qualification and its exposed evidence scope.

## Scientific contract and implementation owners

The predictor receives only the initial and added mass of each unit.
It calculates their sum with an explicit Decimal precision of 100 digits.
It receives neither final observations nor the selected assessment tolerance.
The independent falsifier compares the stored forecast with supplied final observations.
An absolute residual equal to the tolerance is within the declared condition.

The records accept one to sixteen independent units.
Each original input mass is nonnegative and at most `1e9` kg.
The prediction permits up to `2e9` kg.
Decimal digit and exponent bounds remain part of the canonical input contract.
The scientific scope fixes kg, the population, source, receiver, clock and closed additive system condition.
Case independence is a supplied assumption, not a result of this example.

| Owner | Contributor action |
| --- | --- |
| [Records](../../src/empirical_lawhood/methods/mass_balance_starter/records.py) | Define namespace, exact schemas, units, census, scope and the supported calculation label |
| [Science](../../src/empirical_lawhood/methods/mass_balance_starter/science.py) | Implement the forecast and its separate observation-based falsifier |
| [Design](../../src/empirical_lawhood/methods/mass_balance_starter/design.py) | Derive allocation operands, scientific requirement, connection and the two operations |
| [Worker bindings](../../src/empirical_lawhood/methods/mass_balance_starter/bindings.py) | Declare exact ports, codecs, budgets and scientific projections |
| [Experiment](../../src/empirical_lawhood/methods/mass_balance_starter/experiment.py) | Bind supplied evidence, report prerequisites and validate the original instance |
| [Extension owner](../../src/empirical_lawhood/methods/mass_balance_starter/) | Declare operations, protocol and public facts once through `EXTENSION`; generators derive existing registry products |
| [Workflow facts](../../src/empirical_lawhood/methods/mass_balance_starter/workflow.py) | Supply public discovery, presentation and source-guide facts |
| [Environment and installation facts](../../src/empirical_lawhood/methods/mass_balance_starter/public_facets.py) | Supply the exact interpreter, workflow profile and source-bound software requirements |
| [API reader and input helper](../../src/empirical_lawhood/api/mass_balance_starter.py) | Preserve copied bytes and present authenticated findings without recalculation |
| [API descriptor](../../src/empirical_lawhood/api/domain_composition/mass_balance_starter/experiment_binding.py) | Select the retained reader for the exact specification revision |
| [Focused checks](../../tests/test_mass_balance_starter.py) | Exercise positive, adverse, missing and incompatible scientific boundaries |

## Change the namespace and calculation

Copy the method package, API retained reader and API composition binding within your selected development checkout.
The calculation and protocol own scientific behavior; the API binding owns only retained read composition.
Choose a new Python module name and a distinct public namespace.
Update the copied imports, workflow identifier, environment route identifier and guide path.
Update the installation declaration's workflow, adapter module and controller environment identifiers.
Set `NAMESPACE` in the copied record owner.
Change namespace-bearing check identifiers and public text in the copied files.
Do not copy another programme's grants, units or scientific identities.

Change the specification's supported `calculation` label with the forecast implementation.
Keep its falsifier independent.
For example, a deliberately biased `initial-plus-half-added` forecast changes the supplier while the original mass observations remain unchanged.
Its positive-example observations should falsify that forecast under a tolerance of `0.001` kg.
Update the declared question and evidence limits to describe the actual hypothesis.
For a different physical domain, change its units and scope predicates before accepting inputs.
An unspecified label such as `TODO` refuses before authoring.

Use the [configuration route](../using/configuration.md) to prepare edited evidence as canonical bytes.
The consumer is `mass-balance-evidence`, or the copied namespace's registered evidence consumer.
Wrong units, scope, schema, revision or original evidence identity must refuse at their declared boundary.
Run the input helper again after an intentional source or evidence change.
Retain the prior inputs and results under their original identities.

Regenerate the selected source projections through their ordered entry point:

```sh
uv run --no-sync python scripts/generate_extension_projections.py --json
```

The [discovery guide](discovery-facets.md) describes each stage and its refusal behavior.
The extension generator also owns the API runtime index and inert public discovery projections.
The executable generator owns the executable and recursive operation indexes.
Inspect every generated diff.
The extension's declaration requires no hand edit to shared workflow, presentation or environment tables.

Select the [CI profile](ci.md) for a bounded adapter control.
Run only the affected focused checks during implementation:

```sh
uv run --no-sync pytest --fail-on-skip tests/test_mass_balance_starter.py
uv run --no-sync ruff check src/empirical_lawhood/methods/mass_balance_starter \
  src/empirical_lawhood/api/mass_balance_starter.py tests/test_mass_balance_starter.py
uv run --no-sync python scripts/check_documentation.py
```

Use [bounded conformance](extension-conformance.md) for the selected declarations and executable fixtures.
The [starter fixture](../../scripts/examples/mass_balance_conformance.py) checks its registered callbacks and exact evidence codec:

```sh
uv run --no-sync python -m empirical_lawhood.cli.extension_conformance \
  --fixture scripts/examples/mass_balance_conformance.py --project-root "$EL_SOURCE" \
  --output-dir "$EL_STARTER_INPUTS/conformance"
```

Then build the settled source through its sdist with the [artifact owners](../release/release-artifacts.md).
Install that exact wheel in a separate selected environment with the same locked dependencies.
Select its matching unpacked source distribution with `--project-root`.
Execute discover, prepare, author, run, read and recover outside the checkout.
The resulting retained namespace, source identity and forecast values must identify your implementation.
Software acceptance of that build does not qualify the scientific claim.

## Output and stops

Retain the canonical input copies, preparation report, authored package, execution receipts, readout and recovery result.
Preserve failed checks with the exact source bytes that produced them.
Keep operational completion, forecast supply, claim disposition and qualification separate.
Stop at missing prerequisites, incompatible inputs or an unimplemented calculation.
Do not relabel exposed examples as fresh evidence.
