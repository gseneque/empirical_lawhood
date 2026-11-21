# Compose investigations and scientific operations

SPDX-License-Identifier: CC-BY-4.0

Composition has two supported levels: a method or domain composes typed calculations,
and an investigation selects declared operations and authenticated inputs through a
scientific protocol. A retained result can supply a later investigation when its
scope and original custody satisfy the later protocol's input contract.

## Run a complete composition

The [complete composition example](../../scripts/examples/v1_composition.py) first
runs the mass-balance prediction and assessment. It then authenticates that original
run and prepares a separate forecast representation derivative, converting kg to g.
Both investigations use the same public preparation, authoring, execution, reading
and recovery service. Their specifications, plans and receipts remain separate.

From the selected source and [base environment](../getting-started.md), run:

```sh
uv run --no-sync python scripts/examples/v1_composition.py \
  --project-root "$PWD" \
  --workspace /absolute/work/el-composed-adverse \
  --case adverse
```

Select a new absolute workspace outside the source tree. The script reports the
original and derivative authoring directories and writes both preparation, run,
result and recovery reports beneath `scratch/`.

| Retained result | Expected outcome for `--case adverse` |
| --- | --- |
| Original assessment | Three assigned units; two `SATISFIED`, one `FALSIFIED`; claim `FALSIFIED` |
| Representation derivative | `representation_disposition: SATISFIED`; each retained forecast is multiplied by exactly 1000 |
| Original findings carried into the derivative | `original_claim_disposition: FALSIFIED`; the original unit census and reasons remain intact |
| Additional scientific support | `new_measurements: 0`, `qualification: NOT_ESTABLISHED` |

Run `--case unevaluable` in another new workspace to retain the missing final
observation and its original `UNEVALUABLE` disposition. A successful representation
change cannot repair the original scientific finding.

The composition uses these public operations:

```python
from empirical_lawhood.api.mass_balance_starter import create_inputs as mass_inputs
from empirical_lawhood.api.mass_forecast_revision import create_inputs as derivative_inputs

# First, prepare and complete the original investigation using mass_inputs(...)
# and the lifecycle in define-investigation.md. Then select its original outputs:
selected = derivative_inputs(
    authoring_directory=original_directory,
    project_root=project,
    operator_profile=workspace.profile_path,
    output_directory=workspace.artifact_root / "derivative-inputs",
)
# Feed selected["specification"] and selected["sources"] to
# prepare_investigation(..., environment_id="environment.mass-balance.base").
# Author, run, read and recover the resulting separate investigation.
```

The input owner authenticates the forecast, assessment, complete producing receipts,
original implementation and source identities. It derives the derivative input
selection and specification. For retained evidence in another storage location,
pass its current authenticated profile as `source_operator_profile`; the destination
profile still controls new publications. The [record-revision recipe](../development/record-revisions.md)
documents that separate-source route and the exact unchanged format identities.

## Compose a method or a domain transformation

A `Calculation` declares exact configuration, input and output record types.
Call it directly with those types to use the same scientific contract as its
registered worker. The [temperature domain](../../scripts/examples/v1_domain.py)
is a complete example: it validates source units and physical bounds, calls the
shared `AFFINE` calculation, and constructs the narrower Kelvin result contract.

Use [Add a method](add-method.md) and [Add a domain](add-domain.md) to place and
register that code. Registration makes a capability discoverable. Selecting it
in an investigation additionally requires a protocol whose scientific definition
and preparation declare the intended input relationship, scope and assessment.

The [question-to-workflow guide](from-question-to-investigation.md) identifies which
scientific choices belong in the specification and which products are derived.
A supplied contribution must be assessed against the later consumer, even when
both protocols accept the same record type.

## Declare a new scientific investigation

An existing protocol exposes the choices its strict specification supports.
For example, the mass-balance protocol accepts a complete one-to-sixteen-unit
evidence census and a tolerance; it implements `initial-plus-added`. Changing that
string cannot select another calculation. To investigate another scientific
procedure, contribute the procedure and its declared protocol.

The complete [mass-balance protocol reference](../development/mass-balance-starter.md)
and its linked source implement the following supported interface:

| Owner | Public contract and responsibility |
| --- | --- |
| Scientific definition | A strict `CanonicalRecord` specification with units, scope, selected independent units and consequential scientific choices |
| `methods` or `domains` | Calculation contracts, typed input binding, preparation and validation of the complete derived scientific instance |
| `execution.experiment_preparation.ExperimentProtocolDeclaration` | The specification type, `prepare`, optional typed input census and `bind_inputs`, and `validate_instance` |
| Owning `extension.py` | One `ExtensionDeclaration` whose `operations` and `protocols` reference those contracts |
| `api` | Original source authentication, publication and retained-result presentation when the protocol requires these effects |

The reference preparation callback has the signature
`prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None)`.
Its input binder is `bind_inputs(specification, records, *, files=None)` and its
instance validator is `validate_instance(*, specification, allocation, draft, source_records)`.
Only declare optional hooks your procedure uses. Return the existing typed
preparation and scientific draft contracts; report unmet prerequisites rather than
inventing a source or scientific decision.

The reference's `design.py` derives distinct prediction and assessment operations,
connects the forecast output to the assessment input, and keeps final outcomes out
of the predictor. This is the example to adapt when composing several scientific
operations inside one investigation. `design.recursive_authoring` owns the draft
and operation selection contracts; `science.inquiry` owns scientific requirements
and their assessments. Protocol code derives task identities, graph connections,
full output census and scientific input origins from the specification.

Run the extension generator and inspect preparation before executing the new
protocol, as described in the method and domain guides. An optional native engine
belongs behind the smallest applicable adapter port. A pure method requires no
native session, cloud account or deployment hook.

## Scope of the composition interface

V1.0 does not infer scientific compatibility between arbitrary capabilities or
generate a new domain protocol from free-form text. The protocol owns those
scientific decisions. Its canonical specification is editable; its plans and
receipts are derived records. The [recursive inquiry guide](../using/recursive-inquiry.md)
extends this route when a missing condition requires another investigation and
an explicit supplier assessment.

The effective-law post-hoc calculation package remains independently callable,
but its former private executor had no registered public workflow. That executor
is retired; historical records have a read-only custody owner. A new run requires
a canonical protocol integrated with the shared lifecycle. Discovery of a method,
a historical programme record, or a format reader does not establish that this
integration exists. Consult the [migration record](migration.md) for this disposition.
