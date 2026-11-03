# Add a native adapter or method

SPDX-License-Identifier: CC-BY-4.0

This guide gives the procedure for a native adapter or scientific method extension.
It relates one declared scientific contract to records, providers and the maintained application route.
Use it to locate the owning seams and required existing checks.

## Prerequisites and first action

Use the [tested development environment](../using/environments.md). Read the [interface policy](compatibility.md#four-supported-surfaces). Select one scientific contract and its existing adapter owner. Write the independent unit, preparation, available history, action chart, native units, receiver and horizon.

Keep the observations, views and arms nested within their actual independent units. Declare the outcome cutoff and the result that would refute the claim. Give missing and infinite outcomes an explicit rule.

A simulator adapter delivers and observes a native process.
A method consumes typed evidence and returns a bounded scientific product.
Registration and provider construction read no hidden outcomes and grant no authority.
They launch no native simulation.

The reactor supplies a complete implementation example:

| Part | Source owner |
|---|---|
| Native records and source bridge | [panel.py](../../src/empirical_lawhood/adapters/simulators/reactor_prefix_response/panel.py), [assigned.py](../../src/empirical_lawhood/adapters/simulators/reactor_prefix_response/assigned.py) |
| Native runner/provider | [provider.py](../../src/empirical_lawhood/adapters/simulators/reactor_prefix_response/provider.py) |
| Static scientific descriptor | [Source extension bundle](../../src/empirical_lawhood/adapters/simulators/reactor_prefix_response/extension_bundle.py) |
| Executable reconstruction | [Source binding](../../src/empirical_lawhood/adapters/simulators/reactor_prefix_response/executable_binding.py) |
| Method custody and payload ports | [Method binding](../../src/empirical_lawhood/adapters/methods/reactor_prefix_response/executable_binding.py) |
| Candidate composition | [authoring.py](../../src/empirical_lawhood/adapters/composition/reactor_prefix_response/authoring.py) |

## Choose the smallest extension

| Researcher change | Existing path or new owner |
|---|---|
| Change a permitted parameter of the same source contract | Copy the existing input. Validate the copy. Prepare its canonical bytes. Preserve the scientific units, bounds and evidence role. |
| Calculate a new quantity from existing typed evidence | Add the method input and result. Add its evaluator or reducer. Reuse the source and authenticated custody. |
| Deliver or observe a different native process | Add source records and bounded implementation. Supply independently derived falsifiers. Define the complete provider contract. |
| Bind existing operations through a new scientific dependency | Add the family composition and strict input joins. Reuse installed providers, scheduler and custody. Validate parent admissibility. |

Complete the local numerical check before the installed route.
The method-only milestone below uses existing typed panels.
The installed trace identifies the additional seams.
Physical metrology, hidden-source access and genuine issue authority retain their separate prerequisites.

## Extend a tested prerequisite connection

The [bounded RC prerequisite route](../../programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/guide.md) demonstrates a family-level extension.
Its observer supplies a capacitor-voltage interval at a fixed information cutoff.
A frozen rule maps that admitted interval to a finite discharge action.
The evaluator assesses the selected action against the unchanged response support.
It then assesses the full chain against the task and deadline.

Family records retain the actual source, receiver, uncertainty, commitment and complete unit census.
Existing native RC primitives and guarded receipts supply numerical execution and custody.

To add a supplier, first state the exact consumer requirement.
State the supplier's own prerequisite stop.
Give the connection a decisive falsifier, admitted inputs and missing-output disposition.
Test the joined task separately.
Extend the family record and input join only where that design requires it.

A change to observation meaning, policy, support, coefficients, action or acceptance limits creates a separately identified design.
Preserve the original package during the connection experiment.

The original bounded family route remains available with its exact records.
The [recursive inquiry route](../using/recursive-inquiry.md) compiles
explicit RC acquisition, report construction, causal admission, commitment,
native delivery, independent M/P/J assessment and reduction operations through
the shared compiler and scheduler. All ten decisions are retained before delivery
or oracle assessment. Numerical observation supplies no physical sensor or authentic metrology.

Register each added operation's strict config type, named bounded input/output
ports, permissions, resource contract, stateless runner and codecs. The pure
scientific operand projection binds its config to the selected study; the
assessment projection binds complete nested findings to exact requirements and
connections. Keep truth-bearing native evidence out of policy ports. Reuse the
existing executable provider factory and custody owners. A prospective route
still needs its genuine source, issue, execution and reveal contracts.

Current added methods use one
[`RecursiveOperationDeclaration`](../../src/empirical_lawhood/runtime/recursive_provider.py)
to derive their manifest, registration and executable factory. Declare pure
scientific hooks, numerical/publication requirements and effects there. Domain
modules retain estimands, admissibility and independent falsifiers; the shared
compiler dispatches the selected declarations.
An existing operation can declare its exact `runtime_id`, implementation digest
and additional advertised input schemas on that same owner. Use
`input_record_types` for input-only canonical types without widening the existing
output codec map. These fields preserve actual contracts without a second
handwritten manifest or an invented input port.

When several operations validate the same complete scientific census, declare
`scientific_root_preparer` together with `scientific_root_validator` in
`RecursiveScientificHooks`. The compiler invokes each selected preparer once
per validation call with a `RecursiveScientificRootPreparationContext`. Validate
the full configuration, source, stream, graph and root census there, then return
an immutable domain-owned index. Each node validator receives that same value
as `context.scientific_preparation` and checks its exact node and local scientific
contract against the prepared index. Bind the index to the actual shared input
tuples from that call. The batch's read-only `selected_unit_ids_by_selection`
contains the exact unit tuples shared with its node contexts, so a full group
census can also be checked once. A later call prepares its own inputs again. This pure
preparation retains no read permission or execution authority; actual access
and effect boundaries keep their existing checks.

For a binary input or output, declare an exact
[`RecursiveStorageCodec`](../../src/empirical_lawhood/runtime/recursive_storage_codecs.py)
in that operation's `storage_codecs`: schema/version, profile/media, input suffix,
scientific byte ceiling when applicable, and a code-owned bounded
`validate_stream(source, request, *, size)` function. It returns `None` or refuses.
The public integration registry collects these contracts from installed factories.
It validates the complete physical structure without changing logical evidence
identity. Domain readers then establish member completeness, units, clocks and
scientific compatibility. A JSON record codec or a familiar profile label cannot
substitute for a binary declaration. The
[Matrix codecs](../../src/empirical_lawhood/adapters/methods/matrix_storage_codecs.py)
and [battery stream codec](../../src/empirical_lawhood/adapters/methods/battery_segmented_inquiry/storage_codecs.py)
provide current examples. Add an encoding through its domain codec and independent
parity/refusal tests, then regenerate the documented owners; no shared schema
branch or CLI edit is required.

For a high-level experiment, add its exact specification and
[`ExperimentProtocolDeclaration`](../../src/empirical_lawhood/runtime/experiment_preparation.py)
to the owning extension descriptor. Its `bind_inputs`, `prepare` and
`validate_instance` functions derive and recheck the complete scientific graph.
Keep independent-unit allocation and immutable source records separate from
worker, environment and output selections. Ordinary canonical inputs belong in
`input_record_types`. Large canonical files can instead use the explicit
`input_file_record_types` roster: each exact class/schema/revision must already
be installed by a consuming operation. File preparation hashes the exact selected
size without constructing the record; the owning author/consumer still validates
the scientific payload. This does not establish bounded scientific assessment.

When a prospective experiment needs API-owned custody or authority composition,
declare `requires_prospective_runtime_binding=True` and add an
`EXPERIMENT_RUNTIME_BINDING` descriptor under
[`api/domain_composition`](../../src/empirical_lawhood/api/domain_composition/__init__.py).
The existing extension generator discovers `experiment_binding.py` there and
generates the separate API aggregate. Its exact protocol roster must equal the
declared requirements. The API binder runs after the original handoff and
experiment companion authenticate, and may bind runtime ports while preserving
the candidate, design, source, context and resources. Domain adapters keep their
inward imports. The
[protected Matrix descriptor](../../src/empirical_lawhood/api/domain_composition/matrix_protected_factorial/experiment_binding.py)
shows this composition; registration supplies neither missing sampling evidence
nor permission to execute. Keep those prerequisites in the preparation report.

For a prospective child whose resource envelope is bound during authoring,
register `derive_prospective_design_inputs` on that same API descriptor. It calls
the existing pure domain design owner and returns `RecursiveProspectiveDesignInputs`
for the exact prepared draft. Programme composition uses its `spec_id` to capture
the child source closure from the admitted operational parent. A preparation
that already holds its prospective specification supplies the design directly.
Neither path infers an ID from a phase or grants issue, execution or access.

For an ordinary development protocol that needs API-owned custody, declare
`requires_development_runtime_binding=True` and supply `bind_development_runtime`
in the same API descriptor. The development and prospective requirement flags
are mutually exclusive. A development binding may also provide
`read_development_result` for its original retained scientific products. It
keeps the ordinary development lifecycle and its nonpromotable evidence role;
no prospective issue or reveal record is invented for that route.

An API binding may also declare `prepare_authoring` for a preparation step that
needs the actual compiled candidate. The protected Matrix owner uses the existing
candidate compiler to project issued-extension identities, binds the unchanged
resource request, and retains both request and bound selection. Final authoring
recompiles through that same owner and compares the complete preview before
commitment. The hook preserves scientific selections, inputs, original design
records and unresolved entry requirements; it supplies no authority.

An API binding can declare `derive_inputs` for authenticated metadata
preparation, with its exact `derivation_target_protocol_ids`, or `export_products`
for an implemented retained-product handoff. Both hooks are optional and stay
with their owning protocol. A declared export on one protocol creates no export
route for another. Derivation and export retain actual input, source and parent
custody and report unresolved prerequisites; they supply no scientific
qualification or execution authority.

For selected inputs that already inherit protected outcomes, declare
`development_bootstrap_record_types` and `bootstrap_selected_input_access` on
the API binding. The shared loader passes the exact specification and selector,
the actual artifact writer, the resolved `selection_path`, the current
`read_access` selection and a closed
`read_locator(key, reference, kind)` reader. That reader admits only a declared
canonical locator with the selector's exact key, pin, schema and revision.
The selector path permits exact selected-member manifest checks; it supplies
no outcome access. Authenticate the original producer and receipt through those locators before
opening protected records or hashing FILE inputs. Return a callable that
refreshes current access and returns `None` or raises; the loader invokes it at
each subsequent input boundary. Locator metadata and a cached boolean are not
permission. Retained development packets use their corresponding authored-input
bootstrap before graph members are opened.

Bindings that expose public locator selection also declare the closed
`read_access_record_types` roster and `select_read_access` projection. The shared
CLI decoder accepts those installed locator codecs and projects the records into
the existing operation-local access context. It invents no permission record.
Forward the same selection through derivation and export, and preserve the exact
inherited parent census and access labels in every produced configuration and
publication. The finalized compiler owns configuration ancestry and custody;
API publication must use those contracts rather than rediscovering them from
serialized fields.

Keep an expected unevaluable assessment separate from a missing entry condition.
`assessment_limitations` can describe scientific-evidence limits, such as an
unauthenticated sampling assumption that the original assessor reports as
unevaluable. An actual input, environment, storage, software or authority
prerequisite stays in `dependencies` and blocks entry until its owning step
resolves it.

For a current robust inquiry, register the domain-owned `inquiry_work_projector` on its existing `RecursiveOperationProviderFactory`.
Return the exact `ScientificInquiryWork` from the authenticated selected draft and strictly decoded scientific operands.

When a registered input is a declared collection, `RecursivePortContract` can
use `maximum_count=None` for indexed ports. The minimum count and exact selected
scientific census remain mandatory; the compiler rejects undeclared ports.
Use a finite maximum when the scientific contract specifies one. Do not add an
arbitrary operational stream or branch ceiling to replace that contract.
Retain method implementation, actual source, design, numeric operands, receiver, cutoff and observation contract.
Exclude operational labels only when the domain contract establishes that they do not change scientific meaning.
Do not infer equivalence by stripping arbitrary configuration fields.
Unknown work meaning conservatively prevents automatic repetition of an uncertain contact.
An independently supplied consumer remains a distinct scientific work only when its actual semantic operands differ.
Before ACT, supply the exact prospective draft.
Use declared source custody or its unique installed derivation from an authenticated completed supplier.

Current robust requests use the version-three envelope and version-two state with complete attempt-to-work bindings.
Legacy robust version-two packets remain historical archives through explicit read-only inspection.
They do not supply current successor admission.
The [policy guide](recursive-inquiry-policy.md) gives the supported procedure and separate stopping scopes.

A prospective operation consuming a qualified contribution also registers a
`qualified_parent_assessor` on its operation registration. The common parent
reader first authenticates the actual issued run, complete receipt/input census,
current access grants and supported adjudication. The installed assessor then
validates the consumer's quantity, units, domain, timing, uncertainty and permitted
evidence role. It raises on refusal and returns `None` on acceptance. Source
materialization qualification retains its separate readiness meaning.

## Worked RC extension

Start with the existing numerical RC contract. Make the local change in a disposable copy outside the repository.
The [RC workflow](../../programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md#edit-a-development-model) already supports copied-model configuration and retained output.
A new numerical model is not a new physical board or fresh confirmation.

### Milestone A: a typed local result

Trace the current route before adding a new one:

| Handoff | Owning file and requirement |
|---|---|
| Edited JSON → prepared canonical model | [Configuration](../using/configuration.md), then [strict model](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/contracts.py). Positive SI components, topology, action ordering and clock grid validate before contact. |
| Exact model → numerical diagnostic | [native_quickstart.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/native_quickstart.py). Bounded 64 KiB read, strict decoding and two solver views. |
| Strict study → typed native panel | [campaign.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/campaign.py), with [matrix exponential](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/matrix_exponential.py) and [backward Euler](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/refinement.py). |
| Typed panels → numerical falsifier | `check_native_views`, plus [method config](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/contracts.py). Keep one independent unit and two nested views. |
| CLI report → operational retention | [Results and failures](../using/results-and-failures.md). Optional export changes custody of the attempt, not the scientific ceiling. |

A small worked change replaces the four-cell model with a one-cell numerical preparation.
Save this module as `local_rc_extension.py` in the disposable directory:

<!-- BEGIN WORKED RC PYTHON -->
```python
from decimal import Decimal

from empirical_lawhood.adapters.simulators.rc_ladder_response.contracts import (
    ResistorCapacitorLadderActionSegment,
    ResistorCapacitorLadderModelConfig,
    ResistorCapacitorLadderStudyConfig,
)
from empirical_lawhood.adapters.simulators.rc_ladder_response.campaign import (
    VIEWS, run_native_view,
)


def local_study():
    model = ResistorCapacitorLadderModelConfig(
        config_id="rc-worked-one-cell",
        scale_cells=1,
        capacitances_farads=(Decimal("1"),),
        interior_resistances_ohms=(),
        left_source_resistance_ohms=Decimal("1"),
        right_termination_resistance_ohms=Decimal("1"),
        initial_voltages_volts=(Decimal("0"),),
        action_segments=(ResistorCapacitorLadderActionSegment(
            "one-volt-step", Decimal("0"), Decimal("1"),
            Decimal("1"), Decimal("0"),
        ),),
        output_times_seconds=(Decimal("0"), Decimal("0.5"), Decimal("1")),
        component_metrology_frozen_before_response=True,
    )
    return ResistorCapacitorLadderStudyConfig(
        "rc-worked-study", "rc-worked-exposed-unit", model,
        Decimal("0.001"), Decimal("0.005"), Decimal("1"),
    )


def local_panels(study):
    return tuple(run_native_view(study, view) for view in VIEWS)
```
<!-- END WORKED RC PYTHON -->

All constants above are disclosed development choices. The coarse-grid charge-residual limit is deliberately explicit.
Declare voltage in V, capacitance in F, resistance in Ω and time in s.
The action is the finite-source one-volt step. The receiver is the capacitor voltage.
The independent preparation is the numerical model, not its two solvers or three clocks.

Use the independent circuit equation `dV/dt = 1 - 2V`, with `V(0)=0`.
It gives `V(t)=(1-exp(-2t))/2` and DC voltage 0.5 V.
The [worked check](../../tests/test_worked_rc_extension.py) imports the copied module, reconstructs its canonical study/panels,
and compares the actual matrix-exponential output to this equation. It checks Euler error against the same independent relation.
Zero capacitance refuses before a solver. A tighter frozen voltage tolerance produces a negative numerical result.
Do not use an output from the solver as its own scientific oracle.

```sh
uv run --no-sync pytest -q --fail-on-skip tests/test_worked_rc_extension.py
```

This completes a local numerical boundary only. It supplies no real authority, sealed cohort or physical qualification.
The [existing DC/current tests](../../tests/test_resistor_capacitor_study.py) and
[analytic/source-impedance checks](../../tests/test_resistor_capacitor_native_science.py) remain independent verification owners.

### Method-only alternative

Reuse the typed exposed panels rather than inventing a source.
Construct `ResistorCapacitorLadderEvaluationConfig` with its exact study and `numerical_only=True`.
Use `check_native_views` to compare the two panels under the declared tolerances.
Retain its typed `ResistorCapacitorLadderNumericalCheck`, including `converged`, reasons and whole-unit count.
The worked check exercises this branch with native generation disabled during evaluation.
A lower tolerance is a negative result, not a request to rerun a source.
A physical-board claim or a substituted model/unit/grid refuses.
For issued evaluation, the existing [method runner](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/provider.py)
still requires sealed typed inputs, authentic dependency receipts and adjudication context.

### Milestone B: provider and issued integration

For a new installed adapter, identify the required seams before claiming an issued route.
A recursive experiment can use the declarations and shared lifecycle described above.
The RC trace below illustrates an existing family-specific integration; it is not a requirement to add another CLI selector:

1. Scientific records, native implementation and independent falsifiers under the adapter owner.
2. Source `extension_bundle.py` and `executable_binding.py`, with exact provider factory, codec roster and complete ports.
3. Separate method descriptor/binding, input schemas, result contract and evaluator/reducer.
4. Family composition and strict authoring exports, candidate/source/resource/plan projections and bounded external input declarations.
5. API runtime binding and the existing experiment lifecycle. Add a family-specific CLI verb only when the operation needs a distinct public interface.
6. Workflow/config registry and schema projections, guide/result fields and honest first missing prerequisite.
7. Provider selection, authority refusals, output semantics, receipt recovery and independent scientific checks.

### Trace the installed RC route

Use the numerical RC ladder as the installed template after milestone A.
The [family guide](../../programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md) gives the actual `circuit-author` and `check-readiness` commands.
Its scientific unit is one declared model preparation.
The two solver views and receiver clocks are nested observations.

| Seam | Exact owner, exported contract and check |
|---|---|
| Source records and scientific clock | [contracts.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/contracts.py) owns `ResistorCapacitorLadderModelConfig`, `ResistorCapacitorLadderStudyConfig` and `ResistorCapacitorLadderNativePanel`. Components use SI units. Preparation, ordered action segments and output times validate before calculation. |
| Bounded native implementation and falsifier | [campaign.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/campaign.py) supplies `run_native_view` and `check_native_views`. These use the declared matrix-exponential and backward-Euler views. [Independent circuit checks](../../tests/test_resistor_capacitor_native_science.py) test the analytic one-cell transient, charge balance and source impedance. |
| Static source contribution | [extension_bundle.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/extension_bundle.py) exports `EXTENSION_BUNDLE_CONTRIBUTION`. It declares the capability, conformance obligations and evidence ceiling. Registration supplies no native result. |
| Executable source and codec roster | The [source binding](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/executable_binding.py) exports `EXECUTABLE_BINDING_CONTRIBUTION` and `EXECUTABLE_RECORD_TYPES=(ResistorCapacitorLadderStudyConfig,)`. `EXECUTABLE_BINDING_FACTORIES` contains `ResistorCapacitorLadderNativeFactory`. Its complete platform-port set is empty. [runtime_provider.py](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/runtime_provider.py) supplies two exact native runners and bounded study/view inputs. |
| Method input, result and evaluator | The [method contracts](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/contracts.py) own `ResistorCapacitorLadderEvaluationConfig`. The [provider](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/provider.py) consumes both sealed panels and that config. It returns `ResistorCapacitorLadderNumericalCheck` and `ScientificAdjudicationRecord`. The [binding](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/executable_binding.py) exports `ResistorCapacitorLadderNumericalFactory`, the evaluator codec roster and an empty platform-port set. |
| Scientific composition and candidate | [authoring.py](../../src/empirical_lawhood/adapters/composition/rc_ladder_response/authoring.py) owns `build_rc_authoring`, `RCLadderResponseAuthoringBundle` and `ResistorCapacitorCandidateContextProvider`. Both source tasks supply the numerical evaluator. Authoring retains exact payloads, decoder registrations, source, resources and pure plan projections. |
| Application loader and public command | [fresh_authoring.py](../../src/empirical_lawhood/adapters/composition/rc_ladder_response/fresh_authoring.py) owns `FreshRCProfile` and `load_fresh_rc_bundle`. [api/composition.py](../../src/empirical_lawhood/api/composition.py) binds installed services. `campaign circuit-author` emits the closed directory selected by `--circuit-authoring-dir`. Readiness proves the exact three runners without execution. |
| Public configuration and discovery | [configuration_registry.py](../../src/empirical_lawhood/api/configuration_registry.py) owns `rc-ladder-model` and `rc-ladder-study`. [workflows.py](../../src/empirical_lawhood/api/workflows.py) owns `rc-ladder-response`. Existing schema, workflow and CLI generators project those facts. Guides and inputs belong to the selected source distribution. |
| Refusal, results and recovery | The [candidate integration check](../../tests/test_resistor_capacitor_candidate.py) selects exact source/method providers and external inputs. The [family guide](../../programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md#recover-an-incomplete-authoring-export) preserves partial authoring. A later attempt uses a fresh path. Issued evaluation requires actual dependency receipts, adjudication context and separate authority. [Receipt-based recovery](../using/results-and-failures.md#issued-status-and-recovery) preserves completed effects. |

Inspect the native panels and their method consumer before copying integration code.
A completed numerical comparison can report `converged=false`.
Retain its reasons and one-unit denominator.
Scientific adjudication separates support from admission.
This numerical route establishes no physical-board result.

After a native report, the next implemented development task is strict study authoring.
No-contact readiness follows authoring.
Actual issue/run/reveal requires the genuine prerequisites in the family guide.

A held-source or physical adapter has a different complete port set.
Its external input contract binds exact schema, media, size, digest, access and custody before contact.
Platform ports supply the declared hardware/source or guarded-store services.
Obtain the applicable calibration and metrology.
Obtain the required grants.
Do not copy the RC zero-port factory into a different source contract.
Keep mounts and keys with the existing platform owners.

The existing RC source accepts exactly its issued study and no external platform ports.
The evaluator accepts exactly its evaluation config and no external platform ports.
[Source factory](../../src/empirical_lawhood/adapters/simulators/rc_ladder_response/executable_binding.py) and
[method factory](../../src/empirical_lawhood/adapters/methods/rc_ladder_numerical_comparison/executable_binding.py) own those exact sets.
Do not generalize that zero-port contract to physical or held-source adapters.

The [four selectors](architecture.md#four-authoring-directory-selectors) are manual:
reactor, circuit, electron-gas and synthetic-material authoring directories.
They are wired in CLI global inputs, API composition, family loaders and family authoring services.
A fifth descriptor does not create a fifth selector. Adding one requires those owners and matching refusal tests.
Keep existing selectors intact when a new route does not need an installed selector.

Regenerate extension aggregate → executable aggregate → CLI reference, then workflow/schema projections.
Inspect generated diffs. Verify provider construction without contact and existing synthetic authority/recovery fixtures.
Real source qualification, exposure census, physical metrology, issue/approval/execution/reveal authority and fresh cohorts remain separate missing acts.

## Provider and record contracts

Place the extension under its scientific owner in `adapters/simulators/`, `adapters/physical/` or `adapters/methods/`.
Define frozen dataclasses derived from `CanonicalRecord`.
Give each record an explicit `SCHEMA` and public format `VERSION`.
Constructor checks own units, finite values, sorted unique identities, shape and support.
Use `canonical_bytes()` and the registered strict decoder.
Keep pretty-printed JSON separate from canonical identity.

Bind external size, digest, containment and provenance before native contact.
Use the bounded descriptor readers and artifact-plane ports.
After a bounded read, keep its verified bytes for subsequent work.
Do not reopen that path with an unrestricted reader.
Model-bank plan identity, training roots and exposure role remain scientific operands.

Implement the existing [provider](../../src/empirical_lawhood/runtime/providers.py) and [execution](../../src/empirical_lawhood/runtime/execution.py) protocols.
Bind exact capability and implementation identities.
Declare external inputs, runners and output semantic contracts.
For canonical envelopes, declare the actual schema, `record_version` and required field keys.
Keep each output within its declared per-task ceiling.

Implement the factory's `build_provider(registry=..., records=..., platform_ports=...)` seam. Validate exact record types and revisions. Validate the complete port-key set. Use injected source, custody and payload ports.

Keep mounts, signing keys and external contact explicit. Use the existing scheduler. Compilation and construction remain operations without native effects.

## Register the two contributions

Add `extension_bundle.py` under the adapter's allowed family root.
Export `EXTENSION_BUNDLE_CONTRIBUTION` with capability, runtime, resource, evidence ceilings and conformance obligations.
Add `executable_binding.py` beside that owner.
Export `EXECUTABLE_BINDING_CONTRIBUTION`, `EXECUTABLE_BINDING_FACTORIES` and `EXECUTABLE_RECORD_TYPES`.
The record types define the closed canonical codec roster for this binding.

Regenerate the static aggregate before the executable aggregate:

```sh
uv run --no-sync python scripts/generate_extension_bundle_aggregate.py
uv run --no-sync python scripts/generate_executable_binding_aggregate.py
uv run --no-sync python scripts/generate_cli_reference.py
```

The expected outputs are the two generated adapter composition modules, the
[API runtime-binding aggregate](../../src/empirical_lawhood/api/generated_experiment_runtime_bindings.py),
and `docs/reference/cli.md`. Examine all four diffs. The generators inspect the closed `adapters/{control,methods,physical,simulators}` descriptor roots. A module outside those roots does not become executable through registration.

Keep generated fingerprints under their generator owner. If a CLI verb is required, add its lifecycle and invocation/output/refusal metadata. Use the existing CLI behavior checks for that boundary.

## Compose the application route

Bind strict authoring records, candidate context, platform ports and resource envelope through [api/composition.py](../../src/empirical_lawhood/api/composition.py).
Keep compilation, immutable issue, approval, execution and reveal as distinct acts.
Descriptor registration alone does not supply these family-specific bindings.
The [architecture guide](architecture.md#four-authoring-directory-selectors) documents the four manually wired authoring-directory selectors.
Select at most one of those directories for an operation.

Current integration families can use the closed generic `--authoring-dir` handoff instead.
[integration_handoffs.py](../../src/empirical_lawhood/api/integration_handoffs.py) supplies existing composition inputs from exact typed records.
Its provider proof validates graph, resources, output census and bounded external-input bytes before native execution.
Use the existing port contracts and create fresh one-use streams for repeated proof or execution.
Do not add another scheduler, custody store or arbitrary module selector.

An exposed analytical operation can instead compose a typed API over existing source and array contracts.
Its adapter owns the mathematical object, cutoffs, complete denominators and independent falsifier.
Its API authenticates inputs and retains exact results under the declared evidence role.
The [history analysis](../../programmes/foundations/emergent-structure/workflows/matrix-history-analysis/guide.md) demonstrates this boundary without claiming an issued provider or scientific qualification.
Add its closed configuration and workflow facts through their existing owners.
Descriptor registration is required only when the route supplies the corresponding executable-provider contract.

Other retained families can have different, explicitly injected API/provider composition.
Their descriptor does not imply that a matching installed CLI authoring selector exists.
The [route register](../reference/capabilities.md) owns each family's current input and execution boundary.
The [operator walkthrough](../../programmes/foundations/measurement-and-response/workflows/reactor-response/operation.md) gives the maintained checkout recipe for external custody and issued execution.
These recipes are checked for their documented release.
They do not promise stable arbitrary internal imports.

An input deriver that authenticates retained issued results may also register
`derive_inputs_with_service`. `ExperimentProgrammeService.derive_inputs` supplies
the explicitly selected operator profile, catalog, trust and storage through
that API callback, then applies the ordinary derivation-result validation. Keep
the ordinary `derive_inputs` owner as well. This is a metadata derivation hook;
it does not register a composite lifecycle or supply execution/reveal authority.

## Bind scientific units and effect slots

Use the existing `RecursiveOperationRegistration` for a new shared operation.
Its pure callbacks validate the selected scientific context before provider or native contact.
Configuration cannot select these callbacks.

| Registration metadata | Required meaning |
|---|---|
| `scientific_operand_sha256s` | Exact scientific operands retained by the selected root |
| `scientific_unit_ids` | Actual assigned units, with nested branches counted within their units |
| `native_effect_slot_ids` | Actual finite effects, excluding editable task labels and ignored configuration fields |
| `complete_unit_census` | This acquisition group must cover the complete assigned development roster |
| `scientific_root_validator` | Operation, scope, criterion and frozen stage/source checks using `RecursiveScientificRootContext` |
| `scientific_claim_resolver` | Optional code-owned resolution of a scoped connection alias to an exact declared root `ClaimSpec`; direct claim IDs resolve through the shared validator |

Native registrations require unit and effect-slot projections.
Repeated selected native slots refuse before contact.
Independent acquisition groups cannot hide missing units through another group's census.
Prospective native or unit-bound operations also require an installed root validator.
That validator must raise on refusal and return `None` on success.
Use `config_inputs` and `links` to join the strictly decoded selected design operands.
Check a policy’s declared protocol against its actual frozen source configuration,
and check scientific claims against the source, system, world and supplied inputs.
These are frozen design metadata; they add no observations or authority to a worker.
A policy worker retains only its declared input ports and its own configuration.
It grants no source eligibility, issue, execution, reveal or qualification authority.
Use the existing owners for those separate gates.
The shared validator checks the selected scientific prerequisite graph separately
from the task DAG. An acyclic task plan cannot justify circular scientific premises.
Every selected supplier prerequisite must also be declared in its owning
requirement's `further_requirement_ids`, so the preserved scientific selection
contains the complete chosen prerequisite graph.
Connection claim resolution must return the actual typed root claim, preserving
the requirement's world and system scope. Names or matching strings alone do not
establish that relationship. These checks also apply before executing retained
packets and when projecting their assessments.

The current RC and battery registrations support exposed development.
A future eligible native adapter supplies its own scientific stage/source validator through this seam.
The [battery binding](../../src/empirical_lawhood/adapters/methods/battery_recursive_construction/scientific_binding.py) demonstrates fixed numerical claim checks.
A changed scientific question needs its declared protocol and registered assessment.

For durable roots, branches, initializers or segments within a native task,
use the [shared native subwork port](native-subwork.md). Freeze the complete
selected definitions before entry and bind conditional operands through the
live parent. Keep native state, stochastic continuation and scientific
assessment in the adapter; reuse the existing scheduler and custody owners.

## Add a retained scientific reader

A retained reader reconstructs or reports original results without acquiring another scientific observation.
Select the original producer, complete receipt census, source bindings and current access through the family's existing API owner.
Keep independent units, nested views, failed attempts and unavailable outcomes in the declared census.
An execution-only report establishes no completed scientific reconstruction.

Use the following existing owners for the read lifetime:

| Responsibility | Owner and contract |
|---|---|
| Complete publication and final byte checks | [`ExternalArtifactPlane.read_context`](../../src/empirical_lawhood/infrastructure/artifacts.py) owns the finite byte census. Its complete closing check also runs when the consumer raises. Nested stock readers can share that lifetime; custom policies retain their own checks. |
| Current protected access | The selected family's API custody owner supplies the actual access callback. Refresh original persisted grants and current time before protected bodies and at return. A locator, decoded record or prior successful check is not permission. |
| Typed canonical records | [`read_verified_canonical_record`](../../src/empirical_lawhood/infrastructure/canonical_record_read.py) joins the exact manifest, complete publication and registered record type. Pass the existing access callback through `before_member`. It preserves stricter custom readers and their bounds. |
| Already authenticated canonical bytes | [`decode_canonical_bytes_with_identity`](../../src/empirical_lawhood/kernel/decoding.py) returns the typed record and exact size/digest from one canonical pass. The caller still owns publication, current access and semantic producer joins. |
| Immutable decoded records | [`decoded_record_scope`](../../src/empirical_lawhood/kernel/decoded_record_store.py) provides finite reuse bound to bytes, type, validator implementation and Decimal context. Existing read contexts select this machinery; do not add a pathname cache or a cached permission decision. |
| Matrix array operands | [`decoded_matrix_array_scope`](../../src/empirical_lawhood/infrastructure/matrix_array_io.py) bounds compressed-plus-expanded retention within one root/case consumer. Arrays remain immutable. The caller authenticates the archive, allocation and producer before decoding. Other formats retain their own contracts. |
| Optional ordered reconstruction | [`canonical_validation_scope`](../../src/empirical_lawhood/infrastructure/parallel_verification.py) yields a finite executor with `project_ordered`. Select admitted workers and an explicit input/workspace estimate. Results retain order and caller Decimal context; oversized operands use the documented serial path. |

For example, this typed-record consumer assumes the caller already selected the original manifest and actual access owner:

```python
from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record


def read_selected_record(writer, manifest, record_type, *, maximum_bytes,
                         require_access, validate_science):
    require_access()
    with writer.read_context() as reading:
        record = read_verified_canonical_record(
            reading, manifest, record_type, maximum_bytes=maximum_bytes,
            before_member=lambda member: require_access(),
        )
        validate_science(record)
        require_access()
    require_access()
    return record
```

`validate_science` must check the declared producer, scientific inputs, units and semantic joins for that record's role.
It does not construct a grant or replace receipt authentication.
Keep the access owner's lifetime active through the complete consumer and its final check.

For optional parallel reconstruction, pass only bounded, authenticated operands to a top-level, serializable scientific function.
Use the executor returned by `canonical_validation_scope`; do not inspect private artifact-plane state in a new reader.
Pass `weight` and `maximum_pending_bytes` together to `project_ordered` when selecting a concurrent byte allowance.
The controller retains paths, current access, receipt joins, publication and final byte checks.
Workers return compact deterministic results; they receive no authority decision or acquisition permission.
A pending-work estimate is not a whole-process RSS guarantee.

Keep each independent numerical falsifier separate from the calculation it verifies.
Use the existing [combined-reader controls](../../tests/test_combined_canonical_read.py), [dependency controls](../../tests/test_verification_dependencies.py) and [array controls](../../tests/test_matrix_decoded_array_reuse.py) for affected boundaries.
Exercise the actual producer carrier, current-access refusal and final mutation boundary when those contracts change.
Persistent report checkpoints require their own source, input, execution and access contract; finite decoding reuse does not supply one.
The supported [Matrix export](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md) owns its separate completed-report checkpoint contract.

## Verification and honest stops

Use the existing decoder, factory, candidate, authority-substitution and recovery checks for the changed boundary. Choose a scientific falsifier independently of the implementation being checked. A golden output from the same algorithm cannot provide independent scientific evidence. For mechanics, compare mass, energy or actuator transitions with an independently derived relation.

For fitted methods, use a declared truth-known counterexample and whole-root split or permutation checks. Keep failed scientific results as valid results. They must not become retryable operational exceptions.

Use a bounded, nonpromotable integration when the changed route requires execution verification.
Exercise receipt replay and refusal before the relevant effect.
For recovery changes, verify that completed native effects do not repeat.
Reuse existing scientific checks instead of adding duplicate campaign runs.

Optional native distributions and authentic held inputs use separate [test profiles](testing.md).
A selected profile fails when its required prerequisite is absent.
Keep portable independent scientific checks in the portable profile.
Use the focused checks and all generator checks during development.
Before artifact selection, use the complete selected-source [release procedure](../../CONTRIBUTING.md#development-and-release-checks).

Missing source qualification, records, ports, grants or authority remain explicit stops.
Compilation, registration and software conformance provide none of those acts.
For the report's meanings, read the [glossary](../reference/glossary.md#operational-and-scientific-outcomes).

## References and research

The linked reactor source and method modules provide the worked implementation example.
The [architecture map](architecture.md#application-composition-and-module-responsibilities) identifies affected service and verification owners.
The [scientific integrity guide](../reference/scientific-integrity.md) gives the preservation and authority requirements.
The [documentation policy](../../CONTRIBUTING.md#documentation-policy) gives the authoring pattern and language rules.
