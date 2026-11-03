# Test RC prerequisite connections

SPDX-License-Identifier: CC-BY-4.0

Programme: [Measurement and response](../../README.md).

This experiment tests measurement → preparation → response in a one-cell RC model.
It assesses both prerequisite connections and their joined use separately.
Follow this guide to configure, execute and read the complete exposed development roster.

## Inspect and prepare copied inputs

Use the main [locked base environment](../../../../../docs/using/environments.md).
The selected numerical profile requires CPython 3.11.14, NumPy 2.4.6 and SciPy 1.17.1 on Linux x86-64.
Run these commands from the selected checkout root.
Guides and inputs belong to that checkout or source distribution; they are not installed wheel resources.

```bash
uv run --no-sync empirical-lawhood workflow show rc-prerequisite-chain --format json
cp programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json /work/rc-chain-edited.json
uv run --no-sync empirical-lawhood config validate \
  --consumer rc-prerequisite-chain --config /work/rc-chain-edited.json
uv run --no-sync empirical-lawhood config prepare \
  --consumer rc-prerequisite-chain --config /work/rc-chain-edited.json \
  --output-file /work/rc-chain-prepared.json
uv run --no-sync empirical-lawhood campaign rc-chain-prove \
  --input /work/rc-chain-prepared.json
```

Replace `/work` with an existing workspace directory outside the checkout.
Keep the edited original and the prepared canonical consumer input.
The [configuration guide](../../../../../docs/using/configuration.md) explains structural validation, exact Decimal values and canonical preparation.
Validation and proof grant no native-source qualification or scientific authority.

The input contains the complete protocol and assigned-unit roster.
Changing component values, observation rules, policy, support, coefficients, actions or limits creates a separately identified design.
Update the design identity and keep its complete denominator before executing an edited design.
Relabelling a repeated deterministic state cannot supply another independent preparation.

## Start with the scientific question

The frozen response package F_RC requires a capacitor voltage inside its declared support.
Preparation can supply that condition, but its decision rule requires an adequate observation first.
The [revision 1 protocol](protocol.md) freezes the design, controls, cutoffs and negative-outcome rules before execution.

| Claim | Question | Consumer requirement |
|---|---|---|
| RC-M | Does measurement supply preparation information? | Capacitor node voltage in V, correct source/receiver, truthful admitted uncertainty, available by the decision cutoff |
| RC-P | Does preparation supply response applicability? | Admissible handoff and voltage inside the unchanged F_RC support at the committed response cutoff |
| RC-J | Does the complete procedure meet its task? | Adequate connections, numerical conformance, admissible package use, terminal accuracy and compatible timing/resources |

The supplied roster contains eleven distinct deterministic initial preparations.
Their observation variants, preparation arms, observation times and solver views remain nested within those units.
This roster supports exposed numerical development results, with no population estimate, fresh confirmation or scientific qualification.
Physical sensing, authentic sensor calibration and component metrology remain explicit unsupported prerequisites.

## Inspect the frozen handoffs

| Declaration | Supplied value |
|---|---|
| Components | One capacitor, 1 F; left and right source resistance, 1 Ω each |
| Receiver | Complete capacitor node voltage, in V |
| Initial preparations | −2, −1.2, −0.4, −0.05, 0.05, 0.15, 0.25, 0.4, 1.2, 2, 3 V |
| Observation | Sample at 0 s; declared error +0.005 V; interval radius 0.01 V; available at 0.04 s |
| Decision | Cutoff 0.05 s; both source voltages remain zero before decision |
| Preparation menu | Zero-boundary discharge for 0, 0.25, 0.5, 1 or 1.5 s |
| Selection rule | Shortest duration whose entire causally propagated observation interval fits the guarded support |
| F_RC support | Voltage between −0.1 and +0.1 V; selection guard 10⁻¹² V |
| Fixed response | Left source 1 V, right source 0 V, horizon 1 s |
| Fixed predictor | Initial response voltage 0 V; endpoint `(1 − exp(−2))/2`, about 0.432332 V |
| Terminal task | Absolute endpoint prediction error at most 0.02 V, with admissible package use |
| Physical completion | 2.60 s from sampling; resource-conflict control uses 1.80 s |
| Numerical views | Matrix exponential and backward Euler; maximum Euler step 0.0001 s |
| Numerical limits | Voltage-view defect 0.005 V; charge-rate defect 0.002 A; independent scalar voltage/current defects at most 10⁻¹⁰ V/A |
| Operational work | Serial execution; 600 s admission window for the whole invocation, checked before each unit; at most 2,000,000 native integration steps |
| Operational outputs | At most 16 MiB per unit and 256 MiB aggregate payloads; minimum 64 MiB free space, plus the storage profile's floor |

The policy sees the admitted report and opaque source bindings.
It does not receive the initial-state truth, prepared-state readback or later response endpoint.
Oracle inspection follows commitment and checks interval containment, support and response accuracy.
The one-cell receiver determines the complete relevant state; this design invents no hidden-state ambiguity.

The nominal case compares selected, unchanged, wrong and insufficient preparations under the same F_RC.
The other admitted variants use the selected preparation only.
Missing, late, coarsened, biased, wrong-binding, wrong-receiver, wrong-units, resource-conflict and physical-stop controls retain every assigned unit.
At zero selected duration, preparation arms coincide and supply no additional replication.

## Execute with selected storage

Select an [operator storage profile](../../../../../docs/using/configuration.md) for a guarded external root outside the repository.
The profile identifies storage and capacity; it grants no scientific authority.
Use the actual checkout and profile paths in these commands.

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign rc-chain-run --input /work/rc-chain-prepared.json \
  --attempt-dir /work/rc-chain-attempt-001
```

The run retains the exact input and actual producing source, dependency lock, runtime and Git observations.
It publishes each completed unit through the existing guarded artifact plane and task-receipt store.
The report gives `run_id` and `retained_directory` under the selected storage root.
The complete result resides under `runs/rc-chain.<24-character input digest>/`.
The optional attempt directory contains operational diagnostics and a report copy, separately from development custody.

The physical deadline measures the simulated chain's scientific task.
The wall-time budget covers the whole invocation and limits admission of new
units at unit boundaries; it does not restart for each unit.
An admitted bounded unit can finish after that cutoff.
Passing either limit says nothing about the other.
Preparation and response use the same boundary resource sequentially on one trajectory.

## Execute the explicit phases through general authoring

The [recursive inquiry workflow](../../../../../docs/using/recursive-inquiry.md) also supplies
`rc-original.json`, `rc-menu-v2.json` and `rc-budget-v3.json` as authored drafts.
Each binds its exact scientific input in the accompanying
`rc-*-scientific.json` record. Validate a copied draft with consumer
`recursive-inquiry`, then use `campaign recursive-author`,
`recursive-development-run` and `recursive-development-result` with a new
selected guarded authoring directory, as shown in that guide.

Each preparation has separate acquisition, observation, causal admission,
commitment, delivery, M/P/J assessment and reduction tasks. The complete wave
adds the original eleven-unit summary. All ten variants and thirteen arm slots
remain nested in each assigned preparation; task count creates no replication.
Read the complete task census, receipt-bound phase products,
`connection_assessments` and terminal scientific summary. The final scientific
records retain the original unit and summary contracts.

The original scientific deadlines, support, response equation and native proof
limits remain bound to those exact inputs. Menu-v2 adds the predeclared 2 s
preparation while keeping the 2.60 s completion deadline; budget-v3 changes that
deadline to 3.10 s. Their native step ceilings are the original declared
2,000,000 steps for revision 1 and 4,000,000 for each extension.

The shared route declares its software resource envelope separately in the
authored resource ceiling and execution plan. Each of the 100 tasks in a complete
RC wave requests 600 s, one CPU core, 1 GiB of worker address space and 16 MiB each
for bounded source reads and outputs. The declared task wall-time allocations
sum to 60,000 s. These software limits cover the explicit phases and custody overhead. They
do not redefine the simulated scientific deadline or preserve the old API's
600/3600 s whole-invocation admission window merely by retaining its input bytes. The existing
process executor applies each task's frozen timeout and per-process limits;
its trusted-local assurance does not claim aggregate OS quotas. Inspect the
retained resource declaration and actual execution evidence for the selected
wave. The historical runtime below describes the original family route; a
runtime for the general route must come from its own completed invocation.

## Observed development runtime

On 8 October 2026, the supplied eleven-unit run completed in 47 s on Linux x86-64 with SEMIOS storage.
The authenticated result read took 9 s.
Completed-run recovery took 9 s and preserved every custody byte.
These wall times include CLI startup, source checks and receipt publication or authentication.
They describe one local development execution, not a performance guarantee.
The locked numerical profile used one numerical thread.

## Read the complete result

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign rc-chain-result --input /work/rc-chain-prepared.json
```

Inspect `summary.outcome_counts` by variant, preparation arm, claim and terminal state.
Each nested count record stores those fields in its `value` object.
Each selected variant retains the complete assigned-unit denominator.
`unit_result_sha256s` binds the exact per-unit records.
Those records retain observations, committed choices, actual and prospective support, native panels, numerical checks and refusal reasons.
The reader authenticates every receipt and recomputes the retained reduction without numerical acquisition.
`PROSPECTIVE_PACKAGE_USE` records attempted use under the committed observation interval.
The RC-M, RC-P and RC-J states determine whether that attempted use was scientifically admissible.

| Observation in the report | Scientific interpretation |
|---|---|
| RC-M PASSED | The admitted observation met the preparation requirement, including checked interval coverage |
| RC-P PASSED | The committed preparation supplied the unchanged package's required support with an admissible handoff |
| RC-J PASSED | The whole admitted chain passed its task, numerical and timing commitments |
| Accurate observation, RC-P PASSED, RC-J FAILED | Components can succeed while the stricter completion deadline defeats their joined use |
| Endpoint within task, package declined | Coincidental numerical task accuracy outside support does not establish admissible F_RC use |
| REFUSED / UNEVALUABLE | A missing condition or failed upstream handoff prevented an admitted downstream claim |
| UNSUPPORTED | The requested physical supplier or authority lies beyond this numerical development route |

The 3 V fixture challenges the finite preparation budget.
The rule must retain its refusal instead of extending the menu or support after observing the outcome.
Some unchanged or insufficient controls can succeed for low initial voltages.
The controls test claims; they need not all fail.

## Recover without reacquiring completed evidence

Repeat `campaign rc-chain-run` with the same prepared input, source and storage selections.
Use a new optional attempt directory for that invocation.
The operation reuses exact completed-unit receipts and continues only units with no recorded contact.
It does not revise choices or repeat completed observations to seek a favourable result.

A contact marker without its completion receipt leaves completion uncertain.
The operation refuses repetition of that unit.
Preserve its outputs for inspection; the marker supplies no retry authority.
Numerical failures retain terminal failure or unevaluable records, separately from interruption and scientific negative outcomes.

See [results and failures](../../../../../docs/using/results-and-failures.md) for custody and operational-state interpretation.
Development receipts and tests establish neither a physical sensor nor scientific qualification.
The [existing RC model workflow](../rc-ladder-response/guide.md) retains its separate fixed-study authoring boundary.

## References and research

The [protocol](protocol.md) and [strict records](../../../../../src/empirical_lawhood/adapters/methods/rc_prerequisite_chain/contracts.py) own this bounded design.
The [scientific evaluator](../../../../../src/empirical_lawhood/adapters/methods/rc_prerequisite_chain/science.py) owns its numerical execution and retained reduction.
The [API](../../../../../src/empirical_lawhood/api/rc_prerequisite_chain.py) composes its execution, source observation and receipt recovery.
For maintainers, [generate_integration_examples.py](../../../../../scripts/generate_integration_examples.py) projects the supplied canonical input from the typed default owner.
The [independent scientific checks](../../../../../tests/test_rc_prerequisite_chain_falsifiers.py) and [workflow checks](../../../../../tests/test_rc_chain_workflow.py) test their declared software boundaries.
The [paper source register](../../../../../paper/SOURCES.md) gives historical study claims and limits.
This exposed RC experiment establishes no joined controller qualification for those studies.
