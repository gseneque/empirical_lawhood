# Add a domain or substrate integration

SPDX-License-Identifier: CC-BY-4.0

This guide adds domain meaning and transformations through the public extension contracts.
It shows how a domain composes a shared calculation and declares native capabilities only when needed.
Run the temperature-domain starter, then select the integration profile your source actually uses.

## Prerequisites

Use the [base environment](../getting-started.md).
Keep the supplied `v1_method.py` beside `v1_domain.py` in `scripts/examples/`.
The minimal domain uses supplied values and requires no native engine or instrument.

## Run the complete domain example

```sh
uv run --no-sync python scripts/examples/v1_domain.py --celsius 0
uv run --no-sync python scripts/examples/v1_domain.py --celsius 100
```

The [complete starter](../../scripts/examples/v1_domain.py) returns `273.15 K` and `373.15 K`, respectively.
Its `CelsiusReading` requires the exact source unit `degC` and a finite physical value.
Its `KelvinReading` requires the exact destination unit `K` and a nonnegative temperature.
The transformation composes the companion reusable affine method.

Try the invalid physical boundary:

```sh
uv run --no-sync python scripts/examples/v1_domain.py --celsius -274
```

This command must refuse before it produces a converted result.
The example performs no measurement and establishes no sensor calibration or uncertainty estimate.
Its declared evidence scope remains exposed development.

## Place the owners

| Part | Owning location | Contributor responsibility |
| --- | --- | --- |
| Reusable affine calculation | `methods/tutorial_affine/extension.py` | Arithmetic, bounded scalar contracts and precision |
| Temperature meaning and conversion | `domains/temperature/extension.py` | Units, physical bounds, source/destination meaning and transformation |
| Optional instrument or file connection | `adapters/` | Native access, actual observations/actions and external representation conversion |
| Shared operation lifecycle | Existing `execution` and `storage` services | Supplied by EL, with no domain replacement |

First register the reusable method using the [method recipe](add-method.md).
Then add the domain package:

```sh
mkdir -p src/empirical_lawhood/domains/temperature
cp scripts/examples/v1_domain.py src/empirical_lawhood/domains/temperature/extension.py
touch src/empirical_lawhood/domains/temperature/__init__.py
```

In the copied domain file, replace its companion import with:

```python
from empirical_lawhood.methods.tutorial_affine.extension import AFFINE, AffineConfig
```

This imports the method you just contributed.
All framework imports remain the public `science`, `methods` and `execution.extensions` contracts.
The domain exports one `EXTENSION`; its operation is the `TEMPERATURE.operation` declaration.
It needs no unused native, lifecycle, inquiry or presentation hook.

Regenerate and inspect:

```sh
uv run --no-sync python scripts/generate_extension_projections.py --json
uv run --no-sync empirical-lawhood capability show tutorial.celsius-to-kelvin --version 1.0.0 --format json
uv run --no-sync python scripts/generate_extension_projections.py --check --json
```

The domain uses the shared registries and scheduler when selected by an investigation.
No generated registration list or framework dispatch branch needs a manual edit.

## Add an investigation protocol

A domain can expose a researcher-facing scientific specification.
Declare its strict specification type and `ExperimentProtocolDeclaration` in the same `ExtensionDeclaration.protocols` tuple.
The protocol binds supplied inputs, prepares prerequisites and validates its derived instance.

The [mass-balance starter](../development/mass-balance-starter.md) is the complete reference for this addition.
It has distinct prediction and assessment operations, original input bindings and retained scientific reading.
The [investigation guide](define-investigation.md) exercises its full public lifecycle.
Use a new scientific namespace and your domain's actual units, scope, cutoffs and complete outcome rules.

A protocol's prepared plan remains derived from the scientific definition.
An unresolved condition remains a reported prerequisite or an explicit unevaluable assessment, as its contract requires.
It is not converted into a favorable result by registration or compilation.

## Add actual native access when required

Choose the smallest profile with the effects you actually need:

| Native behavior | Required contract and complete recipe |
| --- | --- |
| Bounded canonical or binary file conversion | Strict record or storage codec, exact media/schema/size and bounded input ports; [input and codec contracts](../development/extending-the-engine.md#provider-and-record-contracts) |
| Isolated engine calculation | Native preparation and worker contracts through the existing process runner; [isolated native starter](../development/isolated-native-starter.md) |
| Continuing instrument or simulator | Source session, observations, actions, clock mapping and effect receipt; [continuing-source recipe](../development/continuing-sources.md) |
| Protected prospective work | Original source, issue, execution and reveal contracts; [native subwork](../development/native-subwork.md) |
| Domain-specific retained presentation | Original result reader and application-layer presentation; [presentation recipe](../development/workbench-presentations.md) |

Keep external code under `adapters` and domain meaning under `domains`.
Pass native capability ports into shared execution.
The application composition layer binds concrete storage, source and deployment services.
An inward domain module does not import API or CLI code to create them.

Local and remote placement use the same declared scientific work and recovery contracts.
A method declares its CPU, memory, accelerator and numerical requirements.
The platform selects usable capacity within those requirements and the operator's limits.
An unsupported placement reports the missing capability instead of changing the science.

## Verify and extend

Verify unit conversion, supported boundaries, exact source/result types and invalid native inputs.
Keep independent mathematical or physical reference cases separate from software
contract refusal tests. The [verification-purpose guide](../development/testing.md#verification-purpose-and-execution-profile)
defines numerical oracle declarations and their independent execution profiles.
For actual native effects, verify process isolation, failed contact, publication interruption and uncertain-effect reconciliation.
Use retained original results for inspection and preserve attempt ancestry during recovery.
Do not replay an uncertain native action to make a test report look complete.

The [public interface reference](public-api.md) separates the minimal calculation contract from optional native contracts.
The [architecture guide](architecture.md) and its import gate enforce ownership.
The [testing guide](../development/testing.md) owns selected native prerequisites and release evidence.
