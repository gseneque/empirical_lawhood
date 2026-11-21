# New joint-description experiments: R01–R22

SPDX-License-Identifier: CC-BY-4.0

All 22 families now have editable scientific recipes and implementations in the
same recursive experiment protocol, `joint-description.development`. They are
**new experiments inspired by the preprint's questions**. Twenty primary CPU
studies have retained results. R14 and R16 require physical source cohorts.
The record links original producing identities and reports evaluation support
for each receiver. [Study findings](../../programmes/shared-records/joint-description-results.md)
· [Software release checks](../release/release-artifacts.md)

## Start with the scientific question

For a specified family of preparations, interventions, receivers and horizons,
is there a smallest economically useful joint description? Below that size,
does further decomposition remove dependence, or move it into interface
information, retained memory or uncontrolled error?

Here “smallest” is always conditional on a **finite authored candidate menu**.
Neither a winning candidate nor failure of a smaller candidate proves universal
irreducibility. Economic prices, acceptable errors, safety limits and reuse
counts are research choices. Changing them can change the answer.

The preprint's question about constitutive inputs to `L(D,H,A,R,T)` is a lower
component of this experiment. A response law maps the selected preparation and
description, action, receiver and horizon to a forecast. A common controller
calculation uses those forecasts to select an admissible action. The enclosing
experiment compares whether alternative descriptions still supply that useful
response/control capability, and accounts for information, memory and error.

Work backwards from the proposed use:

1. State the decision and the observable consequence that would make it useful.
2. Declare receivers, units, targets, error tolerances and safety limits.
3. Declare action choices and horizons, including their native units.
4. Define independent preparation roots and their calibration/evaluation split.
5. Specify candidate descriptions: retained state, interface messages, memory,
   accessible features, prediction method and construction costs.
6. Identify the lower domain calculations and the native source or raw cohort.
7. Review the derived supplier requirements before authoring the execution plan.

The [family census](joint-description-families.md) explains the concrete meaning
of those choices for every R01–R22. [Circuit/reactor semantics](joint-description-rc-reactor.md)
and [raw-input/native requirements](joint-description-inputs.md) supply detailed
domain contracts. The original [preprint](../../paper/README.md) remains scientific
background; its reported observations are not expected answers to the new studies.

## What the researcher edits

Copy one of the [22 JSON recipes](../../configs/joint-description/) into your
working directory. Every recipe has the same authoring grammar:

| Field | Scientific meaning |
| --- | --- |
| `family_id`, `question` | The domain assay and the question this particular study asks |
| `seed` | A new root-stream selection; family, split and root identity also separate streams |
| `calibration_unit_ids`, `evaluation_unit_ids` | Disjoint independent preparations; nested actions and horizons never become extra independent samples |
| `actions`, `horizons` | The complete finite request menu in the family's documented units |
| `receiver_policies` | Receiver units, control targets, normalization scales, prediction tolerances, weights and optional safety bounds |
| `descriptions` | Candidate feature access, fixed physical forecast or calibrated ridge law, information dimensions, memory and explicit forecast-work estimates |
| `parameters` | Family-owned scientific preparation, measurement and simulator choices |
| `economics` | Explicit cost units/prices, reuse count, failure/safety penalties, coverage and control-regret requirements, and ridge regularization |

The authoring API derives specification identities, operation configurations,
allocation records, graph edges, source fingerprints and manifests. Do not edit
these generated objects to change the science. Change the recipe and prepare a
new study instead. `new_recipe` and `specification_from_recipe` are public
functions in `empirical_lawhood.api.joint_description`.

Default prices and thresholds are proposed study choices, not established
scientific constants. Review them for the intended receiver and workload.
Forecast construction work is an authored estimate with an explicit basis and
unit; native receipts separately retain measured worker CPU/wall time and bytes.
Information-state dimension is not a claim about a smaller numerical operator.
For example, an RC arm may reconstruct a state and then use the same complete
physical propagator as another arm.

## One causal workflow, composed from six operations

| Operation | Inputs | Output and boundary |
| --- | --- | --- |
| `calibrate` | Specification, new selected source and producing provenance | Complete calibration root/action/horizon/receiver observations |
| `fit` | Calibration only | Fitted response laws and leave-one-root-out description selection |
| `prepare` | Frozen model, selected source and provenance | Evaluation predictors constructed only from the preparation/past; no evaluation response acquisition |
| `forecast` | Frozen model and predictors | Every candidate forecast and safe selected action or explicit no-entry |
| `evaluate` | Retained forecast, exact prepared predictors, selected source/provenance | New simulator outcomes or selected logged physical outcomes; predictor replay must match exactly |
| `assess` | Frozen model, issued forecast and complete outcomes | Error, control, support, information/memory/cost and finite-menu assessment |

Nine explicit scientific requirements connect these operations. The root asks
whether a description supplies a useful capability; the controller requires a
forecast; the forecast requires a frozen response law and available preparation
information; fitting requires the separate calibration cohort. These are typed
requirements with independent assessment links in the existing recursive
compiler, not a second task graph or scheduler hidden inside a script.

The predictor record has no outcome or evaluator-diagnostics fields. Evaluation
acquisition depends on the already retained forecast. Numerical simulators may
replay a deterministic causal prefix to reconstruct the identical preparation;
the repeated prefix work is included in native runtime costs. They must not
acquire an action response during predictor preparation. Logged physical data
already existed, so that route remains an exposed held-out recorded-option
analysis, even though the predictor/assessor software boundary is enforced.

Each acquisition stage uses one native subwork per independent root under the
shared progress/custody owner. Completed original subwork is read on recovery;
an uncertain contacted subwork does not gain permission to repeat. The common
API owns authoring, scheduling, storage, read and recovery for all families.

## Prepare and operate a study

Use the matching checkout or source distribution. The example script only
composes supported application APIs; scientific algorithms live in their domain
or method owners. Select a new workspace outside the checkout.

```sh
uv sync --locked --python 3.11.14

uv run --no-sync python scripts/examples/joint_description_experiments.py new \
  --family R01 --recipe /absolute/work/r01.json

# Edit the question, cohorts, candidate descriptions and economic assumptions.
uv run --no-sync python scripts/examples/joint_description_experiments.py prepare \
  --project-root /absolute/EL --workspace /absolute/work/r01-study \
  --recipe /absolute/work/r01.json --device cpu

uv run --no-sync python scripts/examples/joint_description_experiments.py author \
  --project-root /absolute/EL --workspace /absolute/work/r01-study

# The following operations are for the in-repository execution/review pass.
uv run --no-sync python scripts/examples/joint_description_experiments.py run \
  --project-root /absolute/EL --workspace /absolute/work/r01-study
uv run --no-sync python scripts/examples/joint_description_experiments.py read \
  --project-root /absolute/EL --workspace /absolute/work/r01-study
uv run --no-sync python scripts/examples/joint_description_experiments.py recover \
  --project-root /absolute/EL --workspace /absolute/work/r01-study
```

`prepare` creates typed copied inputs and a preparation report. It starts no
scientific worker. `author` freezes the source-bound plan in
`artifacts/investigation`. Source-bound execution requires the exact clean
implementation and selected environment. Reports appear in `scratch`; original
scientific products and receipts remain with the normal artifact owner.

Each original independent-root return can occupy up to 64 MiB. A complete
calibration, predictor or outcome table can occupy up to 128 MiB. Each native
stage reserves 256 MiB for its root returns and assembled table together.
The worker sends exact canonical bytes in chunks of at most 1 MiB.
The individual returns remain available for authenticated recovery and cost
accounting.

For R13–R16 and R22 add `--raw-cohort /absolute/data/new-cohort.json` to
`prepare`. Use [the exact raw schema](joint-description-inputs.md), and replace
the recipe's unit IDs with the real declared independent cohort IDs. A missing
raw cohort is a preparation dependency, not a synthetic fallback. Missing or
unsafe options remain in the assigned denominator and can make a control use
unevaluable. Simulator observations cannot fill a missing physical option.

### CPU and GPU selection

R01–R16 and R18–R21 use CPU implementations. R17 and R22 support the actual
JAX/TORAX CPU or GPU backend. Change only `--device cpu` to `--device gpu`
when preparing a **new operational selection** for those two families; the
scientific specification remains identical. The GPU task declares one device,
and the native adapter checks the actual backend instead of silently falling
back. GPU selection for another family is rejected.
The supplied script derives the invocation's `accelerated_compute` scope from
that frozen operational selection for run/recovery. Direct Python callers use
`accelerated_compute_operation(device == "gpu")` from
`empirical_lawhood.execution.operational_configuration` around `service.run`
or `service.recover`; a mismatched invocation refuses before native entry.

Install the relevant existing locked optional group: `battery-recursion` for
PyBaMM, or `open-simulators` for TORAX. GPU installation also selects
`open-simulators-gpu` on the documented supported platform. No install or import
control proves numerical CPU/GPU equivalence. The [CPU/GPU guide](cpu-and-gpu.md)
and [accelerated-compute procedure](../using/accelerated-compute.md) own placement,
exact payload staging and host acceptance. R17 and R22 require separate GPU runs for backend qualification.

### Read and interpret the result

The terminal result retains both the calibration-selected description and the
evaluation's exploratory finite-menu comparison. Do not relabel the latter as a
preselected confirmatory winner. For each description it reports:

- Assigned, supported and unavailable observations, and selected-action support.
- Receiver errors in native units, plus dimensionless losses normalized by the
  explicitly authored tolerances. Different physical units are never pooled raw.
- All-use losses and conditional supported errors separately, including safety
  failures and control regret against the available complete paired action panel.
- Independent-root means and standard errors. These are not a guaranteed
  confidence interval, and nested receiver/action observations do not increase
  the independent sample count.
- Retained state, interface scalars, memory scalar-samples, forecast-construction
  estimates and the declared economic conversion.
- Nondominated candidates, usefulness under the authored conditions, and an
  explicit no-useful-tested-description outcome when appropriate.

Repeat price, reuse, tolerance, action-menu and horizon sensitivity as separately
authored studies. An optimum under one pricing choice is conditional on that
choice. A finite menu cannot identify an absolute lower bound on all possible
representations. R01 deliberately admits independent branch descriptions as a
negative control against interpreting every information loss as physical coupling.

The receiver field `max_abs_error` supplies the scale for normalized squared
prediction loss. Usefulness currently tests the receiver-weighted, root-average
normalized loss against one; it is **not** a pointwise maximum-error promise or
a separate worst-case guarantee for each receiver. Inspect the per-receiver
errors as well as the aggregate. Predicted-action safety bounds and realized
safety violations are separately enforced.

## Extend without copying orchestration

| Layer | Current owner | New contribution |
| --- | --- | --- |
| Scientific values | `science/joint_description.py` | Strict predictor, outcome, response-law, forecast and assessment records |
| Authored choices | `design/joint_description.py` | Finite specification, receiver/economic policies and selected raw-input contract |
| Recursive integration | `adapters/joint_description/lowering.py` | Derive six operations, nine scientific requirements and complete allocation from the pure authored specification |
| Reusable assessment | `methods/joint_description.py` | Calibration-only fitting/selection, safe action compiler and finite-menu accounting |
| Domain science | Circuit, matrix, battery, fusion, optics, neuroscience and reactor owners | Meaning, units, causal feature calculations and receivers |
| Native/format adapters | `adapters/physical`, `adapters/simulators`, `adapters/joint_description` | Raw decoding, engine contact and typed progress/custody integration |
| Application | `api/joint_description.py` and `api/investigations.py` | Recipe preparation, shared lifecycle and retained-result presentation |

To add a family, implement independent pure domain calculations and a producer
that preserves the complete declared root/action/horizon/receiver census. Provide
an outcome-free predictor preparation method and an acquisition method that
reproduces exactly the frozen predictor values. Supply candidate descriptions
and receiver policies, then register the scientific family in the catalogue.
The shared experiment declaration already supplies lifecycle capabilities.
Do not wrap an old campaign, add a scheduler, or import an effectful native engine
into the fitting/assessment method. A new mathematical method can also be used
outside this experiment through the ordinary [method contract](add-method.md).

## Validation and limits of this delivery

Focused controls cover the actual recursive compiler, all 22 recipe contracts,
causal barriers, no-contact predictor preparation, native progress/recovery
with injected ports, complete failure censuses and independent numerical oracles.
Read the [programme results](../../programmes/shared-records/joint-description-results.md) for actual execution and the limits of each finding. The [release procedure](../release/release-artifacts.md) verifies the installed software separately.
