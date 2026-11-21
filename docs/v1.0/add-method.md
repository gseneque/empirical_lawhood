# Add a reusable scientific method

SPDX-License-Identifier: CC-BY-4.0

This guide adds a pure calculation through one authoritative extension declaration.
EL supplies its strict decoding, execution adaptation, registration and custody integration.
Run the complete affine-method starter before adapting its scientific contract.

## Prerequisites

Use the [base environment](../getting-started.md).
The starter needs no operator profile, external data, native solver or cloud account for an independent calculation.
It uses finite Decimal values with explicit bounds and arithmetic precision.

## Run the minimal method

```sh
uv run --no-sync python scripts/examples/v1_method.py
uv run --no-sync python scripts/examples/v1_method.py --value 4 --scale 2 --offset 1
```

The [complete starter](../../scripts/examples/v1_method.py) prints `6.5` and `9`, respectively.
It calculates `value * scale + offset` at Decimal precision 50.
The same declared input/output checks apply to direct calls and the shared worker.
The output includes the exact canonical result and static applicability description.

The script has three scientific parts:

1. Frozen `AffineConfig` and `AffineResult` canonical records with constructor validation.
2. `calculate(config, inputs)`, which returns the complete declared output mapping.
3. A `Calculation` and its one `ExtensionDeclaration`.

The declaration supplies the configuration type, input/output types, resource requirements, applicability and assumptions.
A `RecordInput` adds a required scientific input by name and exact type.
This example uses its configuration only, so `inputs=()` is complete.

```python
from empirical_lawhood.science import CanonicalRecord, ResourceBudget
from empirical_lawhood.methods import Calculation, RecordInput, RecordOutput
from empirical_lawhood.execution.extensions import ExtensionDeclaration
```

These are public imports.
No task runner, scheduler, store, recovery journal or native source interface is required.
The complete starter contains executable constructors and scientific validation.

## Register your contribution

Create an owning package under `src/empirical_lawhood/methods/`.
Copy the starter into its `extension.py` and add `__init__.py`:

```sh
mkdir -p src/empirical_lawhood/methods/tutorial_affine
cp scripts/examples/v1_method.py src/empirical_lawhood/methods/tutorial_affine/extension.py
touch src/empirical_lawhood/methods/tutorial_affine/__init__.py
uv run --no-sync python scripts/generate_extension_projections.py --json
```

The generator discovers `EXTENSION` in the new owner.
It derives static registration, executable factories and codec projections through the existing registries.
Do not create separate registration lists or edit generated aggregates.
The copied example retains its distinct `tutorial.affine` namespace.
Use a different namespace for a different scientific method.

Inspect the installed declaration through discovery:

```sh
uv run --no-sync empirical-lawhood capability show tutorial.affine --version 1.0.0 --format json
uv run --no-sync python scripts/generate_extension_projections.py --check --json
```

Discovery performs no scientific calculation.
Use the [investigation guide](define-investigation.md) to consume registered methods through shared execution and custody.
A new investigation protocol selects the operation through its declared scientific contract.
The [mass-balance starter](../development/mass-balance-starter.md) supplies a complete predictor/assessor protocol using that lifecycle.

## Adapt the science

Change the record contracts and calculation together.
State units, scope, finite-value policy, missingness, independent units and relevant numerical precision.
The generic affine calculation deliberately leaves unit meaning and uncertainty with its caller.
It must not infer a physical interpretation from a numeric field name.

Keep independently reusable arithmetic callable through the `Calculation` object:

```python
result = AFFINE(AffineConfig(Decimal("2"), Decimal("3"), Decimal("0.5")))["result"]
```

`AFFINE.describe()` exposes its applicability without running it.
`AFFINE.operation` is the existing compiler and execution declaration.
Use that object in the extension's operation tuple.
The calculation supplies no scientific qualification merely because its software contract passes.

## Verify the meaningful boundaries

Check an independent numerical example and the scientific edge cases.
For this starter, nonfinite values and values outside its declared bounds must refuse.
Wrong record types, missing outputs and extra output names must refuse through the shared contract.
A domain consumer must preserve the method's applicability and add its own unit or scope checks.

For new scientific behavior, retain a focused independent numerical or analytical control.
Use the [testing guide](../development/testing.md) for required contributor and installed-artifact checks.
Declare its independent reference with `pytest.mark.numerical(oracle="specific reference")`;
contract refusal checks remain software conformance. The
[verification-purpose section](../development/testing.md#verification-purpose-and-execution-profile)
keeps those purposes separate from runtime profiles and scientific qualification.
Do not replace a meaningful control with a test that copies the implementation formula.

## Optional capabilities

A pure calculation needs no source, presentation, continuing-lifecycle or inquiry callback.
Add a scientific assessment hook only when the calculation supplies that assessment.
Add inquiry hooks only when the owning investigation actually uses them.
Native effects use the [domain/substrate guide](add-domain.md) and their existing execution contracts.

An effectful operation must not hide network, engine or instrument contact inside a pure calculation.
Its native declaration owns actual effects, input access and permitted recovery.
Application composition binds concrete providers from the application layer.
The method never imports application code to construct those services.
