# Assess the initial WT/I95M joint criterion

SPDX-License-Identifier: CC-BY-4.0

The `rubisco-initial-root-experiment-v1` protocol asks whether the selected
conditional model supports **turnover ratio > 1 and specificity ratio >= 1**.
It consumes the [initial model's](initial-model-v1.md) original selection,
evidence and source-conditioned reviews. It performs two bounded analytical
operations: calculation and independent assessment. It makes no native calls.
An unresolved physical input is a scientific limitation, so a correct run can
complete with an unresolved conclusion.

## Decision and evidence contract

For each admitted joint realization, use the original effective contrasts
and WT waiting fraction:

```text
T = 1 / (w/q_a + (1-w)/q_r)
S = q_D * q_chi
criterion = (T > 1) AND (S >= 1)
```

Keep shared carbon commitment and the original dependence across contrasts.
Assess this conjunction within a realization before aggregating physical
alternatives or processing views. One admitted adverse endpoint contradicts
the conjunction even when the other endpoint is missing. Two supported
endpoints support it only with the required joint and physical admission.
Otherwise the result is `UNRESOLVED`.

The request freezes separate alternative and processing policies.
`UNIFORM_PHYSICAL_CONCLUSION` requires the same resolved outcome throughout
the complete selected census. `ROBUST_FOR_EVERY_SELECTED_ALTERNATIVE` requires
every selected member for support; an admitted counterexample contradicts
that universal claim. Mixed conclusions under the uniform policy require
resolution of the consequential alternative. No averaging removes a failure.
Joint samples remain samples and provide no universal enclosure by themselves.

The independent assessor reconstructs the decision and exact waiting-time
inequalities. It preserves strict versus inclusive boundaries. For example,
the disclosed control `q_a = 6/5, q_r = 4/5` needs `w > 3/5` for turnover
support; equality contradicts strict improvement. This is an algebra control,
not an I95M observation or a chosen numerical tolerance.

Zero mutant rates, absent channels, zero WT references and undefined effective
ratios require explicit domain-limit records. They stay outside the existing
positive-ratio constructors. A domain limit cannot replace a supplied positive
bound. An undefined turnover input can coexist with an independently adverse
specificity finding. Missing consequential inputs remain named requirements.

Original exposure groups are the analytical units. Processing views, chemical
alternatives, sites, starts and realizations remain nested. The biological
unit count is zero. Conditional support, correct numerical reconstruction and
biological predictive validity are separate fields.

## Capture original inputs

Select the [locked Rubisco environment](../../../../../docs/using/environments.md),
a committed source installation, your operator profile and explicit external
input, artifact and scratch destinations. Use `uv run --no-sync` afterwards.
Use the existing initial-model reader and its returned source bindings; do not
construct replacement reviews or scientific identities.

The public Python API below consumes the original reader's records and guarded
source selection. `original_read`, `original_sources`, `project_root` and
`input_directory` are the values selected through the initial-model workflow.

```python
from empirical_lawhood.api.domain_composition.rubisco_response.initial_root import (
    prepare_initial_root,
)
from empirical_lawhood.api.domain_composition.rubisco_response.initial_root_experiment import (
    create_initial_root_experiment_inputs,
)

request = prepare_initial_root(model=original_read["selection"])
prepared = create_initial_root_experiment_inputs(
    request=request,
    selection=original_read["selection"],
    evidence=original_read["inputs"],
    sources=original_sources,
    project_root=project_root,
    output_directory=input_directory,
)
print(prepared["paths"])
```

Capture authenticates the complete original publications and keeps their guards
live while freezing review data. The four returned files are `analysis.json`,
`specification.json`, `sources.json` and `source-snapshot.json`. They retain
exposed, source-conditioned data. They grant no source access, prospective
qualification or physical admission. The original closed initial-model and
standalone joint-root exports keep their original member contracts.

## Explain, prepare, author, run and read

Use the returned paths in the shared commands below. Replace `/selected` with
your explicit locations. The worker count must match the operator profile;
the example selects four workers. Each analytical task uses one numerical
thread, and the assessment depends on the calculation.

```sh
uv run --no-sync empirical-lawhood --operator-profile /selected/operator.json \
  campaign experiment-explain \
  --input /selected/inputs/specification.json \
  --sources /selected/inputs/sources.json \
  --source-snapshot /selected/inputs/source-snapshot.json \
  --environment-id rubisco-prediction --workers 4 \
  --output-root /selected/artifacts
```

Use the same arguments with `campaign experiment-prepare` and an explicit
`--output /selected/readouts/preparation.json` to retain the explanation.
Use `campaign experiment-author` with the same input, source, environment and
worker arguments, replacing `--output-root` with a fresh
`--output-dir /selected/artifacts/root-wave`.

```sh
uv run --no-sync empirical-lawhood --operator-profile /selected/operator.json \
  campaign experiment-run --authoring-dir /selected/artifacts/root-wave --workers 4
uv run --no-sync empirical-lawhood --operator-profile /selected/operator.json \
  campaign experiment-read --authoring-dir /selected/artifacts/root-wave
```

Read `terminal_products` for the independently reconstructed root, complete
requirement graph and remaining scientific conditions. `SUCCEEDED` describes
execution. It can accompany `SUPPORTED`, `CONTRADICTED` or `UNRESOLVED`.
Repeated reads authenticate the original receipts and do not repeat work.

## Requirements, inquiry and next action

The root's mandatory prerequisites are its numerical assessment and the actual
remaining decision requirements. Optional supplier branches retain their own
`further_requirement_ids`: original-input reuse, relative operands or a bound,
a paired integral bound, retained operator actions, and physical preparation.
They do not automatically select a full molecular campaign or a Matrix study.

Use
`api.domain_composition.rubisco_response.initial_root_inquiry.project_initial_root_inquiry`
with the authored directory, artifact plane and an explicit post-outcome
`InformationCutoff` on `clock.rubisco.declared-rate-closure`. Its returned
specification, authenticated state, sources, menu, policy and campaign compose
the ordinary [inquiry preview, commit and read services](../../../../../docs/using/recursive-inquiry.md).
No hand-written predecessor, requirement roster or task list is needed.

A supported source-conditioned result can select one independent retained
destination check. The shared contribution export and successor-authoring
services bind its exact original result, assessment, scope and source. Changed
consumer or source inputs refuse that connection. The next assessment grants
no additional physical evidence. An adverse conclusion closes its current
branch. An unresolved conclusion holds with its exact missing prerequisites.

Before a molecular successor, select the immediate receiver and its actual
state or history, chemistry, coordinate conventions, accuracy allowance,
information cutoff and permitted preparation freedoms. Supply only the
requirements that matter to that receiver. Construction coordinates and
optimizer progress hashes are not an equilibrium population or restart state.

## Work and acquisition assessment

The public `api.work_costs` services retain original operational evidence in a
`WorkCostAccount`, deduplicate physical attempts and reconstruct measurement
coverage. Unknown overhead, failed/uncertain work and incomplete clocks remain
visible. Inclusive observations and their components are not added twice.

`initial_root_acquisition.assess_initial_root_acquisition` in the Rubisco method
owner joins that account to the exact root and requirement graph. Explicit
`InitialRootForceScenario` records price stated workloads under stated historical
timing and price assumptions. They are neither a total budget nor a performance
bound. Unknown preparation and rate-connection work remain unpriced.

A conditional decision can omit an unneeded operand without proving that any
particular native call or expenditure was avoided. A scalar receiver bound
must pass its existing independent assessor with complete original premises,
corrections and costs before any stronger omission claim. This protocol makes
no default native-saving claim and authorizes no acquisition.

The [exact controls](../../../../../tests/test_rubisco_initial_root.py) and
[public lifecycle controls](../../../../../tests/test_rubisco_initial_root_public.py)
cover supported, adverse and unresolved outcomes, partial contradictions,
original-source mutation, contribution compatibility, successor readback and
unknown costs. Their disclosed numerical inputs provide software evidence only.
