# Run the exposed causal matrix example

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for the exposed matrix example.
It checks causal ordering, independent numerical assessment and receipt recovery.
Use it to prepare one complete development wave in a selected storage root.

## Prerequisites

Use the selected checkout and its existing [locked numerical environment](../../../../../docs/using/environments.md).
Use `uv run --no-sync` after environment selection.
Select an [operator storage profile](../../../../../docs/using/configuration.md) and a new directory under its guarded external root.
Set the five numerical thread variables to `1` before Python imports NumPy.
Select the [frozen numerical runtime variables](../../../../../docs/using/environments.md#frozen-rc-numerical-input-profile) when that profile applies.

The example has one exposed independent root and two nested future branches.
Its fixed allocation cannot supply fresh confirmation or transfer evidence.
Branch `future-1` keeps both coupling parameters.
Branch `future-2` adds exactly `0.05` to `alpha_x` at the first future transition.
Both branches retain every selected position, momentum and stochastic increment.

The public protocol binds the physical member, numerical view, complete horizon, action menu and preparation scope.
Its calibration scope describes the independent numerical check and declared tolerance.
The frozen analytic reference has a distinct clock and a pre-observation cutoff at coordinate zero.
It supplies no statistical coverage, calibrated lifetime or preparation benefit.
The existing closed 64 MiB NPZ contract remains unchanged.
A larger complete package requires another declared scientific package rather than omitted states.

## First action

Create `/selected/guarded-root/matrix-inputs` before this preparation command.
Replace the selected paths with the actual checkout and storage root.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
uv run --no-sync python - <<'PY'
from pathlib import Path
from empirical_lawhood.adapters.methods.matrix_prospective.example import example_source
from empirical_lawhood.adapters.methods.matrix_prospective.recursive_translation import prospective_draft
from empirical_lawhood.adapters.methods.matrix_prospective.science import branch_contract
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance

selected = Path('/selected/guarded-root/matrix-inputs')
source = example_source()
provenance = capture_matrix_provenance(project_root=Path('/selected/checkout'))
draft = prospective_draft(source, provenance)
for name, record in (('source', source), ('provenance', provenance), ('draft', draft)):
    (selected / (name + '.json')).write_bytes(record.canonical_bytes())
for branch in ('future-1', 'future-2'):
    stream = branch_contract(source, branch).stream
    (selected / (branch + '-stream.json')).write_bytes(stream.canonical_bytes())
PY
```

This command observes the actual producing source and locked runtime.
It performs no native trajectory acquisition.
Changing source or dependency bytes after preparation requires a new wave.

Freeze the complete four-operation wave through the supported authoring command.

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-author --input /selected/guarded-root/matrix-inputs/draft.json \
  --input-binding external.matrix.source=/selected/guarded-root/matrix-inputs/source.json \
  --input-binding external.matrix.provenance=/selected/guarded-root/matrix-inputs/provenance.json \
  --input-binding external.matrix.future-1-stream=/selected/guarded-root/matrix-inputs/future-1-stream.json \
  --input-binding external.matrix.future-2-stream=/selected/guarded-root/matrix-inputs/future-2-stream.json \
  --output-dir /selected/guarded-root/matrix-wave
```

Authoring binds the full source, configuration, provider, scientific and execution graphs.
The forecast worker receives the public conditions and authenticated prefix arrays.
It receives neither future driver seeds nor future observations.
The future worker depends on the published canonical forecast and its producing receipt.
The independent assessor receives the complete committed and acquired array products.

## Output and stops

Execute the selected exposed wave and request a compact custody report.

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-run --authoring-dir /selected/guarded-root/matrix-wave \
  --terminal-product-format compact

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-result --authoring-dir /selected/guarded-root/matrix-wave \
  --terminal-product-format documents
```

The complete task order is prefix acquisition, forecast publication, native branch acquisition, then independent assessment.
The forecast extrapolates the observed final position using the observed momentum.
The assessor differentiates the potential in a Hermitian basis and uses its own BAOAB composition.
It does not invoke the native trajectory producer.
It independently checks every future-branch stochastic increment against the declared driver.
The declared numerical tolerance is `1e-7`; the forecast precision is `1e-8`.

Both branches must remain in the result even when a forecast fails.
A failed native reference check makes the corresponding forecast assessment UNEVALUABLE.
Software completion grants no physical qualification, factor relevance, lifetime coverage or target success.
The [conformance checks](../../../../../tests/test_matrix_prospective.py) bind the fixed example's expected adverse forecast result.

Completed branch definitions, outputs, consumed streams and measured costs have separate durable receipts.
Preserve those receipts when the parent task or terminal report is interrupted.
Use `recursive-development-result --terminal-product-format compact --allow-partial` to inspect incomplete custody without execution.
An uncertain contact blocks automatic replay.
Completed recovery uses exact receipts and adds no native contact.
See the [subwork contract](../../../../../docs/development/native-subwork.md) for the full denominator and recovery states.

This route checks the installed shared architecture.
It does not execute the Matrix E1–E6 programme.
Those studies require their own scientific suppliers, calibration, preparation and transfer assessments.

## References and research

The [conformance checks](../../../../../tests/test_matrix_prospective.py) verify this example's software behavior and independent numerical assessment.
The [Matrix programme specification](../../records/matrix-programme.md) defines the separate E1–E6 investigations and scientific controls.
Use the [programme guide](../matrix-programme/guide.md) for their supported operations and prerequisites.
The [source implementation](../../../../../src/empirical_lawhood/adapters/methods/matrix_prospective/science.py) separates the native producer from the numerical assessor.
