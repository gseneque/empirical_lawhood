# Reassess retained battery obstruction history

SPDX-License-Identifier: CC-BY-4.0

Programme: [Battery charging](../../README.md).

This programme applies the existing independent obstruction assessor to an exact
retained source and its original negative MODEL contribution. It creates no
native trajectory. The original acquisition HOLD and UNKNOWN/NO_REPLAY condition
remain in force.

The selected census retains the original 36 forecasts and nine reference checks,
twelve planned diagnostic forecasts, one entered registered native operation and
zero returned diagnostic results or trace rows. Actual forecast-provider entries,
completions, charging calls and initialization calls remain unknown. A successful
history assessment supplies no numerical adequacy or new physical unit.

## Select the original inputs

Use `ObstructionExperimentSpecification` from the
[domain specification owner](../../../../../src/empirical_lawhood/adapters/methods/battery_diagnostic_obstruction/experiment_specification.py).
It selects the exact `ObstructionSource` and original negative
`ContributionManifest` identities. Question and evidence meaning retain their
existing protocol; researchers do not assemble operation, edge or claim IDs.

The existing canonical `ExperimentInputSelection` binds three keys:

| Key | Exact selected record | Purpose |
| --- | --- | --- |
| `source` | `ObstructionSource` | Original primary records, input identities and complete custody census |
| `parent` | `ContributionManifest` | Original negative supply as receipt-bound DESIGN_OPERAND/MODEL |
| `custody` | `ObstructionSourceCustodySelection` | Explicit original guarded root and exact report/cost file identities |

The parent binding must point to its actual portable directory's
`contribution.json`. Keep that complete directory under the selected guarded
operational root. An existing authenticated portable parent can be reused there;
the specification and operation configuration contain its references rather than
another copy of its large supply payload.

Custody selection uses the existing `ExternalRootContract` and `CustodyMember`
types. Its source reference must match the specification. Its report digest must
match the original source, and its cost identity must match the original complete
cost bytes. The original member census remains in one owning source record.

Use the existing locked main environment and a selected immutable producing
checkout. Follow [environment reuse](../../../../../docs/development/maintainer-environment.md)
without synchronizing an environment to inspect or prepare these inputs.

## Use the common programme service

The same [public preparation owner](../../../../../src/empirical_lawhood/api/experiment_preparation.py)
loads these inputs and derives the experiment instance. Given the selected
`project_root`, existing guarded `artifact_writer` and separate `execution`
selection:

```python
from empirical_lawhood.api.experiment_preparation import (
    load_experiment_specification, load_experiment_inputs,
)
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService

specification = load_experiment_specification(specification_path)
resolved = load_experiment_inputs(specification, input_selection_path)
programme = ExperimentProgrammeService(project_root, artifact_writer)
prepared = programme.prepare(
    specification,
    scientific_inputs=resolved.scientific_inputs,
    method_inputs=resolved.method_inputs,
    execution=execution,
)
explanation = programme.explain(prepared)
```

Read the complete census and dependencies before authoring. Preparation derives
the exact SOURCE/MODEL origins, one exposed numerical-family allocation and one
PURE reassessment task. It reads no large supplier payload and runs no assessor.

```python
authored = programme.author(preparation=prepared, output_dir=selected_wave_directory)
result = programme.run(directory=selected_wave_directory)
report = programme.read(directory=selected_wave_directory)
recovered = programme.recover(directory=selected_wave_directory)
```

Shared authoring authenticates the complete portable parent through its original
receipts. The registered source predicate checks every original custody member,
the exact final report and cost, the complete census, and the continued absence
of the original diagnostic receipt/result. Authoring and retained load/run/read
boundaries recheck that premise. A new receipt, result, result manifest or extra
native contact requires reassessing the changed primary state.

The worker invokes the unchanged `science.assess` method and publishes the same
`ObstructionAssessment` record type. Completed recovery reuses primary task
receipts. The original `battery-diagnostic-obstruction.assess` capability remains
the named reader for its retained source12 C5 attempt; its historical bytes are
unchanged. The current authored route uses
`battery-diagnostic-obstruction.reassess-authenticated`.

## Evidence and remaining limits

The original public retained assessment has canonical SHA256
`c8cfa474bb0db694c3debf9e191bf89f5f1333eb6443aacc5bf9460cd4963b56`.
This identifies the existing adverse-history result, with method conformance
SATISFIED and numerical assessment UNEVALUABLE. Frozen source15 completes the
new high-level route's author, actual PURE worker, read and unchanged recovery,
retaining all235 members with zero new native contacts. Its final harness glob
also counted two copied historical contact files; the original failure and a
separate read-only continuation are preserved in the
[C3 evidence record](../../../../shared-records/applied-el/consolidation-c3-cross-domain.md).
The result retains the original negative findings and supplies no new scientific
qualification. Large-record authentication and assessment memory remain open.

Use [results and failures](../../../../../docs/using/results-and-failures.md) for receipt-based
inspection and recovery. The
[scientific selection](../../records/battery-diagnostic-obstruction-selection.md)
retains the independent qualification and later-use conditions. This programme
does not assess the full 18 GB state/derivative trace or clear its UNKNOWN parent.
