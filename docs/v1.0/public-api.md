# Supported public interfaces

SPDX-License-Identifier: CC-BY-4.0

This reference defines the v1.0 interfaces for the three contributor jobs.
It distinguishes scientific contracts, application operations and optional native capabilities.
Use the smallest interface that supplies your task.

## Investigation application operations

Import these names from `empirical_lawhood.api.investigations`:

| Name | Contract |
| --- | --- |
| `create_local_workspace(root, *, project_root, profile_id="local.research", maximum_parallel_tasks=None, minimum_free_bytes=1048576)` | Creates a new explicitly selected local root and derives its ordinary storage profile. Returns `LocalWorkspace`. Existing roots, links and forbidden containment refuse. |
| `LocalWorkspace` | Read-only `profile_path`, `artifact_root` and `scratch_root` paths |
| `create_investigation_service(*, project_root, operator_profile, artifact_root_contract=None)` | Composes the existing `ExperimentProgrammeService` using source and storage selections |
| `prepare_investigation(service, *, specification_path, source_selection_path, environment_id, protocol_path=None, read_access=None)` | Loads original scientific inputs, derives source identity and prepares the selected scientific definition without starting work |
| `experiment_preparation_report(preparation)` | JSON-compatible prerequisite, census, selection and authored-operation trace report |
| `ExecutionSelection` | Explicit consequential operational selections; omitted worker count is selected from usable capacity |
| `load_experiment_specification(path)` | Strict loading of an installed protocol's scientific definition |
| `load_experiment_inputs(specification, selection_path, *, artifact_writer=None, read_access=None)` | Exact selected input bindings, with the owning original-custody and current-access checks |
| `implementation_binding(project_root)` | Current selected implementation record; it supplies no scientific authority |

The service's supported investigation lifecycle is:

| Operation | Effect and returned meaning |
| --- | --- |
| `prepare(specification, *, scientific_inputs=None, execution=None, protocol_bytes=None, method_inputs=None)` | Derives prerequisites and a scientific plan through the installed protocol. Returns `ExperimentPreparation`. |
| `explain(preparation)` | Returns the preparation report without execution |
| `author(*, preparation, output_dir, read_access=None)` | Publishes the derived authored package and complete input/implementation bindings |
| `run(*, directory, maximum_parallel_tasks=None, ...)` | Executes selected work through the shared scheduler and original admission contracts |
| `read(*, directory, allow_partial=False, ...)` | Authenticates retained results and their full census without native reacquisition |
| `recover(*, directory, maximum_parallel_tasks=None, ...)` | Uses original receipts and recovery contracts; uncertain native effects are not automatically replayed |

The ellipses identify optional advanced lifecycle selectors, not arbitrary keyword support.
Use their owning [native](../development/native-subwork.md), [inquiry](../using/recursive-inquiry.md) or [result](../using/results-and-failures.md) recipe.
The ordinary guide uses only the explicit parameters shown before the ellipses.
The service owns no second journal, scheduler or scientific result store.

The exposed starter also supports:

| Module | Public names |
| --- | --- |
| `empirical_lawhood.api.mass_balance_starter` | `create_inputs(evidence_path=..., tolerance_kg=..., project_root=..., output_directory=...)` |
| `empirical_lawhood.methods.mass_balance_starter` | `example_evidence(case)`, `MassScope`, `MassObservation`, `MassEvidence`, `MassSpecification` |
| `empirical_lawhood.api.mass_forecast_revision` | `create_inputs(authoring_directory=..., project_root=..., operator_profile=..., output_directory=..., source_operator_profile=None)` authenticates a complete retained original investigation and prepares its explicit representation derivative |

The supplied fixture has three units. User-supplied `MassEvidence` retains a complete
one-to-sixteen-unit census, exact kg units and exposed development scope.
These records do not establish qualified physical measurements.
The [composition guide](compose-investigation.md) runs the retained derivative and
identifies the protocol contract for a new scientific procedure.

## Operational progress

Import `progress_step`, `report_progress` and `report_workflow_progress` from
`empirical_lawhood.execution.progress`. Application owners select
`OperationalProgressReporter` from `empirical_lawhood.storage.progress`;
`read_progress` validates its current atomic v2 snapshot for terminal or UI readers.
The [progress guide](../using/progress.md) gives lifecycle usage, units, unknown
denominators, bounded terminal summaries and native callback boundaries.
Pure scientific contracts retain callback interfaces independent of telemetry.

## New finite joint-description experiments

Import these names from `empirical_lawhood.api.joint_description`:

| Name | Contract |
| --- | --- |
| `new_recipe(family_id)` | Returns an editable scientific recipe for one new R01–R22 family; no native contact |
| `specification_from_recipe(recipe)` | Validates the complete authored finite menu and derives a strict `JointSpecification` |
| `create_inputs(recipe_path=..., project_root=..., output_directory=..., device="cpu", raw_cohort_path=None)` | Copies exact new selected inputs, binds producing source and creates protocol input selections; no experiment execution |

The same investigation service then prepares, authors, runs, reads and recovers
the study. The [experiment guide](joint-description-experiments.md) describes
six causal operations, explicit supplier requirements, safe control selection,
complete failure accounting and conditional economic interpretation. No original
preprint-result reader or compatibility wrapper is part of this new protocol.

## Classical matrix programme with direct methods

Import authoring functions from `empirical_lawhood.api.model_free_matrix`:

| Name | Contract |
| --- | --- |
| `load_definition(path)` | Strict editable M0–M7 JSON and complete assigned root roster |
| `select_sci02c_instrument(directory=..., artifact_writer=...)` | Read the authenticated SCI02-C source64 design and template through the caller's current access profile for the H64 studies |
| `create_inputs(definition_path=..., project_root=..., output_directory=...)` | Source-bound new development inputs; no native contact |
| `create_successor_inputs(..., parent_directory=..., parent_service=...)` | Authenticated development cutoff, complete exposure census and frozen fresh confirmation |
| `create_population_deployment_inputs(..., parent_directory=..., parent_service=...)` | Complete authenticated reveal-all M5 benchmark, frozen target and auxiliary, disjoint sparse deployment roots |
| `create_reanalysis_inputs(..., parent_directory=..., parent_service=...)` | Exact retained acquisition/array selection and whole selected-module denominator; no reacquisition |
| `parent_readout_sha256(scientific_result)` | Exact canonical readout identity for a confirmation selection; hashing alone grants no parent authority |

Use the ordinary investigation service for preparation, authoring, execution,
reading and recovery. The [programme guide](model-free-matrix-programme.md)
documents the public CLI, supported definitions and scientific limitations.
Scientific freshness is explicitly distinct from the framework's exposed
development ceiling. The core creates no artificial TRAIN, FIT or CAL products.

## Accelerated execution composition

Local CPU execution is the default. The operational configuration's
`accelerated_compute` boolean selects the requested route without changing
frozen numerical engine records, tolerances, precision or thread counts.
The [CPU and GPU guide](cpu-and-gpu.md) gives executable configuration examples,
engine selection, explicit refusal conditions and the shared local/remote contracts.

Import `RunpodDeploymentSelection`, `PERIODIC_CUDA_BACKEND`,
`PERIODIC_REFERENCE_MM_BACKEND`, `JAX_TORAX_BACKEND` and `prepare_accelerated_deployment` from
`empirical_lawhood.api.accelerated_deployment`.
`RunpodDeploymentSelection.for_execution_plan(..., backend=...)` derives hosting
requirements from the unchanged compiled work and an existing declared backend.
The selected backend must match its code-owned hosted worker environment:
periodic PySCF/OpenMM or JAX/TORAX CUDA12 with its authenticated dependency bundle.
Its numerical thread setting remains independent of the derived host CPU size.
The [accelerated compute guide](../using/accelerated-compute.md) owns the complete
preparation and handoff recipe, current prerequisites and versioned request format.

## Scientific value objects

Import common contracts from `empirical_lawhood.science`:

| Name | Meaning |
| --- | --- |
| `CanonicalRecord` | Base for exact immutable scientific records with declared schema and revision |
| `decode_canonical_bytes` | Strict original-format decoding, with explicit record type and byte bounds |
| `ObjectIdentity` | Scientific identity derived from the exact record and its declared object identifier |
| `ResourceBudget` | Declared CPU, memory, accelerator, time, source-byte and result-byte requirements or bounds |
| `EvidenceCeiling`, `OutcomeAccess`, `VisibilityCeiling` | Explicit scientific evidence and information-access limits |

Scientific contracts do not import execution, storage or application layers.
Their named subpackages hold the detailed response, evidence, model, experiment and inquiry contracts.
The [advanced contract reference](../development/extension-interfaces.md) enumerates optional scientific and native interfaces.

Schema strings are persistent format identities.
An old word inside an unchanged schema string does not name a current Python import.
Do not rename a stored schema to match the new package layout.

## Pure calculations

The [scientific component guide](scientific-components.md) identifies additional
domain calculations that can run independently of a campaign or adapter.
Their numerical assumptions and input types remain part of their applicability.

Import `Calculation`, `RecordInput` and `RecordOutput` from `empirical_lawhood.methods`.
A required input or output has a name, exact canonical record type and positive byte bound.
A calculation declares:

- Capability key, version and implementation identity.
- Configuration type and complete input/output tuples.
- The code-owned `calculate(config, inputs)` function.
- Resource requirements, applicability and explicit assumptions.
- Optional scientific assessment or inquiry hooks only when used.

The function returns exactly the declared output names mapped to their exact canonical record types.
`calculation(config, inputs)` independently validates and evaluates the same scientific contract used by its worker.
`calculation.describe()` returns static applicability and port facts without evaluation.
`calculation.operation` exposes the existing recursive operation declaration for registration.

No filesystem writer, scheduler, source session or recovery implementation is part of a pure calculation.
The [complete method example](../../scripts/examples/v1_method.py) is the executable minimal contract.
The [domain example](../../scripts/examples/v1_domain.py) composes it with narrower unit and physical checks.

## One extension declaration

Import `ExtensionDeclaration` from `empirical_lawhood.execution.extensions`.
An owning `extension.py` exports one `EXTENSION` object:

```python
EXTENSION = ExtensionDeclaration(
    extension_id="my-domain.my-method",
    version="1.0.0",
    operations=(my_calculation.operation,),
)
```

Optional tuples declare `protocols`, `profiles`, `workflows`, `configurations`, `environments` and `installations`.
The generator projects them into the existing closed registries and application discovery.
Do not export duplicate low-level registration products beside a unified declaration.
Do not put arbitrary Python import paths in scientific configuration to select executable code.

Application bindings remain in application composition when a protocol needs concrete effects or retained presentation.
They reference the scientific declaration and own only their outer-layer behavior.
Inward methods and domains do not import application code.

## Diagnostics and clients

CLI and workbench call the shared application operations.
Application errors contain a structured diagnostic with:

| Field | Meaning |
| --- | --- |
| `authored_object` | Selected scientific object or authored locator when known |
| `operation` | Executing application operation |
| `owner`, `contract` | Responsible layer and failed contract |
| `expected`, `actual` | Safe public contract values or an explicit statement that operand values were not disclosed |
| `implementation` | Owning module, callable and location where available |
| `evidence` | Retained diagnostic or attempt location when available |
| `remediation` | Investigation, method, domain, adapter or platform owner |
| `trace` | Bounded code locations without locals, scientific input bodies or secrets |

A preparation report's authored-operation trace joins the scientific definition to the selected implementation.
An unavailable or changed historic implementation is labelled explicitly.
A current installation never claims to have produced an older record merely because it can read that record.
Use the [investigation guide](define-investigation.md#trace-a-failure) for the documented debugging route.

`campaign recursive-execution --authoring-dir PATH` and the workbench's
`recursive.execution` operation share the same paginated execution projection.
For a retained failure, its task row's `diagnostic` joins the authored object,
selected implementation, original attempt ancestry, declared resource bounds and
authenticated event location. The projection authenticates execution records and
does not load scientific result bodies. Missing native details remain explicitly
undisclosed; an uncertain native effect permits read-only reconciliation only.

Verification reuse is limited to its active lifetime and originating process.
Threads may share a valid scoped reader under the existing synchronization contract;
a forked child must open its own fresh verification scope. Closing and mutation
checks still apply to every scope, including the parent's scope after a child exits.

The Rubisco retained-analysis export readers return the original stored JSON
report and original arrays by default. They authenticate the original sources,
complete receipt ancestry, member census and closing byte checks.
Set `scientific_reconstruction: full` to request an additional numerical comparison.
Both modes retain the original evidence identity and report whether reconstruction occurred.
Reports returned by export and inspection use JSON arrays for persisted sequences.
Pure scientific functions retain their own typed return contracts.

## Version and internal boundaries

These documented imports and operations are the v1.0 contributor contract.
Undocumented helpers and construction sequences remain internal.
The old `kernel`, `planning`, `runtime`, `infrastructure`, `resources` and `adapters.methods` Python paths are removed.
There are no import aliases or legacy wrappers.

Versioned retained scientific formats keep their original identity and supported readers.
A source change has a changed implementation identity.
It does not transfer qualification or permit unfinished native work to switch implementations silently.
The [migration record](migration.md) and [source/format policy](../development/compatibility.md) state those boundaries.
