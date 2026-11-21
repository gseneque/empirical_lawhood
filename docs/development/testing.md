# Verification profiles

SPDX-License-Identifier: CC-BY-4.0

This guide gives the bounded CI, portable, integration, scale, native and held-input verification profiles.
It separates software conformance from scientific qualification.
Use it to select existing checks for a change or release claim.

## Verification purpose and execution profile

Verification purpose is independent of runtime cost, execution environment and
access to original inputs. The `scripts.test_purposes` pytest plugin, loaded by
the repository test configuration for ordinary focused pytest runs as well as
all release profiles, assigns each collected case one purpose:

| Purpose | Declaration and meaning | Selection |
|---|---|---|
| `conformance` | Default for contract, custody, lifecycle, refusal and implementation controls. A passing case makes no independent numerical-oracle claim. | `-m 'conformance and not native and not held'` |
| `numerical` | Explicit `@pytest.mark.numerical(oracle="...")` names the independent mathematical reference used by that case. A missing, empty or conflicting declaration refuses collection. | `-m 'numerical and not native and not held'` |

Both are software verification. Neither establishes scientific qualification,
fresh evidence, molecular validity or an admitted experimental result.
The numerical group is a reviewed reference subset, not a claim that every
algorithm has an independent oracle or that every numerical branch is covered.
Tests without that reviewed declaration remain conformance controls even when
they contain arithmetic assertions. Native and held markers remain orthogonal:
a numerical test requiring a GPU cannot pass because a portable profile omitted it.

The initial reference group includes exact binomial tails; direct two-dimensional
partition integrals, Schur complements and harmonic memory; independent matrix
exponentials and ODE solutions; finite-state reweighting; geometric competing
hazards; and weighted normal equations. The reviewed group also includes M50's
signed environmental quadratic response and exact signed Decimal contrasts,
independent restraint-energy gradients, ballistic and harmonic reactive flux,
Maxwell component variance, exact processing-network moments, and analytical
RC trajectories and information bounds; exact rational Arb endpoint and Gram
error enclosures; literal VirtualCell order statistics; and exact battery charge
rectangles. Each case names its specific reference at the assertion's owner.
For example:

```sh
uv run --no-sync python -m pytest --fail-on-skip -p scripts.test_purposes tests -m 'numerical and not native and not held'
```

The `ci`, `integration` and `scale` profiles retain their complete portable
partition. Their `test-selection.json` now reports purpose counts and the
declared numerical references; `test-execution.json` joins each executed case
to that purpose and its actual outcome. Collection does not count as execution.
CI includes the bounded exact-binomial, retained-Gaussian, matrix-history and
M50 environmental-response reference modules, together with their refusal
controls. The default suite also exercises invocation-proof and decoded-record
isolation across fork while a different parent thread holds the original lock:
a child must decode and authenticate again and perform its own final byte
checks. Inherited weak-reference cleanup never acquires the copied parent lock.
Larger lifecycle and
native checks keep their separately selected profiles.

Coverage configuration must name existing migrated modules and include every
declared critical owner. Both CI and the full portable gate check that before
tests. Only the complete portable coverage run can claim executed statements
for the full critical-owner inventory; a CI pass cannot supply that claim.

The portable suite includes independent scientific counterexamples and shared
engine conformance. All lifecycle authorities, signatures, sources and cohorts
under `tests/` are synthetic software fixtures. Their records cannot attest a
real prior census, authorize an operator, or qualify a scientific claim.

The focused lifecycle tests in `runtime_platform/`, `api/` and their support
modules were adapted from the historical response-law source project. They retain its issue,
approval, scheduler, artifact and recovery behavior while using this package's
namespace and strict source-origin contract. The target reference campaign is
rebuilt by `scripts/generate_test_fixture.py`. It is not a copied historical
approval or qualification packet. Keep fixture signatures confined to tests.

`test_reactor_public_lifecycle.py` uses the selected checkout, an isolated
external storage profile and ephemeral test signers.
For external test storage, set `EL_TEST_EXTERNAL_MOUNT` to the actual selected mount and place pytest's `--basetemp` beneath it.
Portable Linux runs otherwise retain the explicit tmpfs test profile. It traverses base and extension issue, experiment-package assembly, execution-plan compilation and twenty native acquisitions. It then exercises the separate reveal gate, adjudication and receipt recovery after loss of its disposable catalog. A second case retains a synthetic census of 20,000 units and 230,000 streams through public authoring/proof/issue preview.
It validates the real 64 MiB member boundary. Positive fixtures model prospective
eligibility only inside their closed synthetic test world.

They cannot establish
eligibility for a real study. A third case supplies an explicitly exposed
assignment and contradictory freshness attestations: both issue paths refuse
before writes. Allow several minutes and a few hundred MiB of temporary storage.

## Independent checks for current outputs

The coverage inventory requires executed statements in the declared critical owners.
It checks measurement presence, not correctness, complete branch coverage or qualification.
Use these independent checks when changing the corresponding scientific or custody boundary:

| Boundary / output | Independent check and refusal owner |
|---|---|
| Initial Rubisco joint root | [Exact joint controls](../../tests/test_rubisco_initial_root.py) check the conjunction before quantification, strict waiting boundaries, partial adverse evidence, undefined ratio domains and original-source mutation. [Public lifecycle controls](../../tests/test_rubisco_initial_root_public.py) retain supported, contradicted and unresolved conclusions through ordinary execution, contribution export, destination assessment and the next inquiry decision. Changed source or consumer inputs refuse reuse. Cost scenarios retain unknown preparation and prove no native saving. All controls are disclosed analytical evidence. |
| Paired preparation and local response | [Response controls](../../tests/test_rubisco_preparation_response.py) retain original forces, fixed predictions and complete nested comparisons. [Decision controls](../../tests/test_rubisco_preparation_response_decisions.py) distinguish preparation benefit, signal suppression and paired deterioration. [Local supply controls](../../tests/test_rubisco_preparation_supply.py) separate adverse answers from unavailable supply. [Public lifecycle controls](../../tests/test_rubisco_preparation_response_public.py) exercise actual receipts, contribution admission, inquiry successors and sealed observations with disclosed native callbacks. Installed molecular and financial acceptance remain separate. |
| Paired preparation and environmental dependence | The [bounded specification](../../programmes/biology/photosynthesis/workflows/rubisco-response/preparation-environment-v1.md) declares prospective support and one fixed initial-WT direction. [Numerical controls](../../tests/test_rubisco_preparation_environment.py), [source-integrity controls](../../tests/test_rubisco_preparation_environment_integrity.py) and [staged workflow controls](../../tests/test_rubisco_preparation_environment_workflow.py) cover signed transfer, support/map refusal, negative nomination, pure environmental predictions and the 34-return core. Final lifecycle checks retain their separate source scope. These exposed controls supply no molecular acquisition or installed/deployment acceptance. |
| Retained nonlinear response with a quadratic environment | [Finite-response controls](../../tests/test_retained_gaussian_response.py) compare the original two-dimensional quartic partition functions, explicit environment elimination, both normalization paths, conditional residual formulas and full-system harmonic histories. [Method scope](retained-gaussian-response.md) distinguishes numerical estimates from certified bounds and molecular admission. These bounded checks perform no molecular acquisition. |
| Retained equilibrium free energies | [Finite-partition and custody controls](../../tests/test_rubisco_equilibrium_reweighting.py) verify exact-distribution estimates, independent MBAR equations, paired block covariance, complete cross-window potentials and unavailable windows. Closed exports reconstruct original results and refuse changed siblings or originals. These exposed controls establish no equilibrium, chemical-model or rate admission. |
| Dividing-ensemble reactive flux | [Flux controls](../../tests/test_rubisco_reactive_flux.py) use ballistic and recrossing populations, natural-mass Maxwell variance, complete original trajectories and paired block covariance. They retain missing shots, negative flux, exact geometry thresholds and final byte-change refusal. Closed preparation and analysis packages reconstruct originals without force replay. These controls supply no physical-rate admission. |
| Physical first passages and weighted continuation | [Original path controls](../../tests/test_rubisco_physical_first_passage.py) retain clocks, residence, missing weights and exact rational resampling. [Continuation controls](../../tests/test_rubisco_weighted_path_continuation.py) check complete phases, stochastic streams, cumulative mechanics, failed predecessors, zero-offspring costs and closed export. Descendants create no independent units. |
| Physical rates and complete processing | [Rate controls](../../tests/test_rubisco_physical_rates.py) use known competing-exit laws, history-dependent alternatives, failed paths, exact gas density and joint whole-run draws. [Network controls](../../tests/test_rubisco_physical_rate_networks.py) retain release waits, complete product return, competing exits and encounter residence. Exact balance and independent Arb enclosures falsify changed propagation. Original-custody exports preserve missing rates and costs without native reentry. These controls supply no physical-model admission. |
| Prospective pilot cost selection | [Cost and custody controls](../../tests/test_rubisco_pilot_allocation.py) verify exact projections, complete paired roles, prospective priority, failed costs and missing prerequisites. Force and trajectory receipts supply original measurements. Closed exports reconstruct costs without native reentry. These controls supply no prepared recipe or spending authority. |
| Paired supplier forecast | [Supplier controls](../../tests/test_rubisco_paired_forecast.py) combine original flux, electronic and processing findings. They retain common draws, complete failed denominators, missing operands and shared costs. Independent reversible kinetics checks bound endpoint arithmetic. Changed original or export bytes refuse reconstruction. |
| Pilot stages and non-force costs | [Programme controls](../../tests/test_rubisco_pilot_programme.py) retain measured analysis/export costs, failed invocations and missing originals. They bind actual authored tasks, verify returned custody and exercise the shared execution/recovery route. Scientific falsification, unknown contact and publication-only recovery remain distinct. Exposed lifecycle checks establish no molecular admission. |
| Selected operations and shared reads | [Selected loader controls](../../tests/test_selected_operation_loading.py) compare complete generated registrations and canonical roots, refuse collisions and preserve cold discovery without native imports. [Authored controls](../../tests/test_authored_control_reuse.py) count body reads and retain current access, custom hooks and final mutation refusal. [Roster indexes](../../tests/test_recursive_read_indexes.py) retain duplicates, ambiguity, complete predecessors and cycle refusal. The public multiple-parent lifecycle checks relocated custody. |
| Sealed worker input decoding | [Worker controls](../../tests/runtime_platform/test_worker_preflight.py) count complete byte reads and strict decodes, invalidate changed validators, Decimal and numerical settings, and release records when the owner closes. Other threads and serialized workers obtain fresh lifetimes. [Prefix](../../tests/test_rubisco_active_preparation.py) and [response](../../tests/test_rubisco_preparation_response.py) controls check actual registered operands and refuse changed artifact identities even after reuse. Performance acceptance separately measures the selected original input sizes and process memory. |
| Inquiry projection and contribution ancestry | [Finite read controls](../../tests/test_recursive_projection_lifetime.py) count distinct source and physical-copy reconstructions, preserve packet preflight and final-byte refusal, exercise custom policies and check object release between invocations. [Authoring read controls](../../tests/test_recursive_inquiry_authoring_read.py) share immutable metadata across projections while rereading completed products, retaining access and final mutation guards, and refusing execution within the source read. They exercise numerical and validator invalidation, traversal limits, bounded retention and copied contexts. [Paired response controls](../../tests/test_rubisco_preparation_response.py) share one complete immutable selection across work, endpoint and input-origin consumers while retaining changed-draft refusal. These controls establish software behavior only. |
| Exact reductions and fitting bookkeeping | [Binomial differentials](../../tests/test_exact_binomial_recurrence.py) compare integer recurrence against independent combinatorial tails, including equality, endpoints and unattainable thresholds. Existing design-method controls retain zero-denominator refusal. [Matched fitting](../../tests/test_matrix_matched_response_fitting.py) checks training-only scales, complete groups, SVD failures and independent weighted equations while counting feature-map construction. |
| Operational artifact verification | [Measured hash and format controls](../../tests/test_reduced_artifact_verification.py) compare strict and reduced results, work counts, current access and cache expiry. Full final, publication and worker boundaries refuse changed bytes, including preserved file metadata. [Configuration controls](../../tests/test_operational_configuration.py) verify the reduced default, explicit strict selection and separate invocation record. These software controls establish no scientific qualification or whole-operation speed. |
| E4 original control reuse | [Package and grant work counts](../../tests/test_matrix_e4_original_metadata_reuse.py) preserve fresh grant loads while reusing immutable package and issue records. Custom policies, revoked grants, changed final bytes and escaped scopes retain their refusals. Disclosed receipt metadata isolates this software control from scientific acceptance. |
| Completed E3/E4 read memory | [Temporary product controls](../../tests/test_configured_e3_read_lifetime.py) and [programme binding controls](../../tests/test_matrix_programme_original_read_lifetime.py) verify object release before dependent use. [E4 input controls](../../tests/test_matrix_programme_e4_inputs.py) retain current access and final byte checks after releasing duplicate preparation records. These disclosed controls establish ownership behavior, not whole-operation memory capacity or scientific qualification. |
| Matched E3 response metadata | [CAL/CONF forecast identity controls](../../tests/test_matrix_matched_response_identity.py) bind actual physical forecasts in both response guards. Foreign forecast identities refuse. These disclosed records supply no acquisition or scientific evidence. |
| Entered E3 continuation | [Public FILE preparation and complete compiler controls](../../tests/test_matrix_e3_retained_continuation.py), [pure copy workers](../../tests/test_matrix_e3_retained_workers.py), [resource histories](../../tests/test_matrix_e3_retained_resources.py), [closed source recipes](../../tests/test_matrix_retained_e3_source_recipes.py) and [custody lifetimes](../../tests/test_current_task_control_lane.py) preserve original operands, dependencies, bytes and source separation. Public preparation checks every retained file contract and refuses changed revisions, media, bytes and missing files. The [source guard](../../tests/runtime_platform/test_retained_history_source.py) requires exact qualifications and both permissions for sealed development history. These exposed software controls do not authenticate a real retained execution or establish scientific completion. |
| Entered E3 CAL closeout | [Complete graph controls](../../tests/test_matrix_e3_cal_closeout.py) exclude entered CAL calls and retain the original denominator. [Guarded PURE worker controls](../../tests/test_matrix_e3_closeout_worker.py) preserve unknown contacts, missing scores, original visibility and separate assessment source. [Retained input-copy controls](../../tests/test_matrix_e3_retained_input_copy.py) verify each output under its actual producing plan's semantic registry and reject changed receipts, bytes, visibility or access. Their disclosed control premises provide no scientific authority or qualification. |
| E4 handoff after E3 closeout | [Imported producer controls](../../tests/test_configured_e3_imported_products.py) join original partial producers through the completed continuation. [Retained bank metadata controls](../../tests/test_matrix_programme_retained_bank_metadata.py) preserve the six original publications and refuse changed bytes, access, namespaces or successor entry. Disclosed scientific-reader seams establish software behavior only. |
| Prospective member capacity | [Closed member and decoder controls](../../tests/test_recursive_prospective_bounded_capacity.py) cover one current scientific selection decoder, all fourteen exact schema/revision roles, and authenticated observed member sizes. [Operational capacity and transfer](../../tests/test_operational_capacity_transport.py) exercises real files above the previous 16/128 MiB ceilings, a PURE output above 256 MiB, selected allowance refusals, stable bounded chunks, and generic transfer. Advertised-size cases establish software contracts only; they are separate from actual payload tests. |
| Concurrent in-memory scheduler catalog | [Transaction and lease-read controls](../../tests/infrastructure/test_catalog_memory_concurrency.py) preserve a writer's transaction across concurrent reads. Bounded worker reads complete alongside coordinator writes. These literal catalogs supply no scientific evidence. |
| Programme metadata binding and cold phase reads | [Complete-roster binding controls](../../tests/test_matrix_programme_binding_batch.py) count collection scans and physical member validations at two sizes for fresh and already scoped readers. They preserve exact binding and specification bytes. They reject body, sidecar, commit, path and current-access changes before publication or return. |
| Programme metadata reuse | [Operation-local reuse controls](../../tests/test_matrix_programme_metadata_reuse.py) check inherited execution observations, newly authored packets and nested input reads. Changed bytes, future entry and revoked access must refuse. Pure joins and immutable records expire with their owning context. Installed timing evidence remains separate. |
| Programme input checkpoints | [Selected-publication controls](../../tests/test_input_publication_checkpoint.py) count byte checks at two publication sizes and retain complete atomic siblings. Changed bytes, paths, access and expired scopes refuse. Custom policies retain full checks, and unrelated history remains guarded at final return. |
| Programme predecessor custody | [Nested read controls](../../tests/test_matrix_programme_predecessor_custody.py) count physical member validation across four predecessor levels. They reject late body changes and revoked access. The execution service retains its separate context. These disclosed contexts supply no scientific evidence. |
| Remaining Matrix programme handoffs | [Confirmation and E3 observation controls](../../tests/test_matrix_programme_handoff_guards.py) retain full/partial distinctions and stop unconfirmed phase dispatch. [DEV product batches](../../tests/test_matrix_development_product_batch.py) check both producer declarations and original receipt joins. [Replay lifetimes](../../tests/test_matrix_development_replay_lifetime.py) refuse changed bytes, revoked access and escaped scopes. [CLI controls](../../tests/test_experiment_execution_handoff.py) distinguish a direct nonexecuting preview from a generic completed command. Disclosed reader seams supply no scientific qualification. |
| Prospective preview and companion authoring | [Invocation reuse controls](../../tests/test_prospective_authoring_reuse.py) compare all fourteen canonical members, count actual compilations and candidate decodes, and retain fresh source, original-input, publication and current-access refusals. These counts do not establish whole-workflow speedup. |
| General recursive authoring and explicit RC phases | [Compiler/graph checks](../../tests/runtime_platform/test_recursive_compiler.py), [RC scientific continuity](../../tests/test_recursive_rc_operations.py) and [uncertain native contact](../../tests/runtime_platform/test_native_effect_contact.py); exposed numerical conformance grants no authority |
| Public recursive custody and portable contributions | [Public run/read/recovery](../../tests/test_recursive_public_service.py) and [portable custody mutation checks](../../tests/test_recursive_contribution_custody.py); synthetic products test software boundaries and cannot establish a scientific construction |
| Streaming recursive custody and compact reports | [Exact stream and mutation controls](../../tests/test_streaming_portable_custody.py), [complete report and receipt censuses](../../tests/test_recursive_report_projection.py), and [measured large opaque custody](../../tests/test_recursive_custody_memory.py); the memory probe establishes custody behavior, not typed scientific assessment memory |
| Representative typed custody and memory | [Complete typed publication and relocated replay](../../tests/test_recursive_typed_custody_memory.py) covers battery receivers, original Rubisco sources, material responses, complex arrays and generated sparse biological data. It measures repeated reads and full data censuses. Readback decodes one complete record at a time. Operational copies retain scientific identities and create no independent units or qualification |
| Closed development custody without dispatch | [Public custody-only controls](../../tests/test_recursive_custody_only_recovery.py) retain exhausted tasks and unreachable descendants. Eligible pending work and changed original contacts refuse closure. |
| Incomplete whole-root E2 assessment | [Closed-custody controls](../../tests/test_matrix_native_utility_closed_custody.py) distinguish actual outcomes, missing roots, unknown contacts and no-contact refusals. They preserve the original denominator. |
| Native TRAIN/E2 public consumers | [TRAIN lifecycle](../../tests/test_matrix_native_training_public_lifecycle.py), [E2 read and recovery](../../tests/test_matrix_native_utility_read.py), and [selected contact inputs](../../tests/test_matrix_native_contact_input_contract.py) exercise actual owner handoffs. Exposed fixture acquisition creates no qualification. |
| Exact raw arrays and interrupted native outputs | [Anonymous complex-array delivery](../../tests/test_matrix_array_worker_delivery.py), [received-prefix custody](../../tests/test_native_subwork_prefix_custody.py), and [original validator replay](../../tests/test_recursive_validator_compatibility.py); full member checks and original manifest bytes remain distinct from scientific qualification |
| Completed native evidence in a bounded read | [Native census controls](../../tests/runtime_platform/test_native_subwork_read_context.py) count whole-census byte checks at two sizes. They retain individual record checks, current access, exact final mutation guards and eager checks outside the bounded read. Exposed fixtures establish no scientific authority. |
| Shared bookkeeping algorithms | [Parallel custody controls](../../tests/test_bookkeeping_parallel_custody.py) exercise actual process workers, controller access callbacks, stock-path selection and indexed factory lookup. [Pool lifetime controls](../../tests/test_recursive_validation_lifetime.py) retain parent guards through shutdown and reject final mutations, including during consumer failure. Copied contexts obtain fresh capacity, while explicit scheduler borrowing retains its live owner. [Canonical storage controls](../../tests/kernel/test_canonical_encoding_storage.py) preserve exact bytes while bounding retained child encodings. [Full-output custody controls](../../tests/test_recursive_compact_output_bulk.py) check complete batching before typed consumption and final mutation refusal. [Later Matrix reader controls](../../tests/test_matrix_later_bookkeeping.py) check issued output batches and bounded control/scientific custody reuse. These are software checks, not throughput or scientific qualification claims. |
| Concurrent development and controller recovery | [Eight-caller custody controls](../../tests/test_development_task_concurrency.py) keep one independent guard scope per complete sibling read, reject copied mutable thread state and preserve final byte/access refusal. [Current grant controls](../../tests/test_selected_e3_current_access.py) retain fresh byte and expiry checks, including masked-stat mutation and changed authority-store policy. [Controller recovery controls](../../tests/test_development_controller_repair.py) retain complete original receipts and events, admit only original uncontacted native tasks and refuse uncertain contact. [Real SIGINT drain](../../tests/test_development_interrupt_drain.py) retains the exclusive run claim without renewing catalog leases, preserves the admitted task's software receipt without descendant dispatch, and refuses revoked access. These exposed controls create no scientific evidence; actual throughput requires a separate measured run. |
| Future PURE output allowances | [Continuation controls](../../tests/test_matrix_future_output_allowance.py) preserve the original operational bytes and change only three future response-score output fields. They retain the complete E4 frontier, structural terminal, original memory ceilings and public request binding. These exposed checks create no scientific entry or qualification. |
| Scoped validation and catalogue batching | [Local validation controls](../../tests/kernel/test_scoped_record_validation.py) count shared-child validation and retain mutable-child, contextual-join and Decimal-context refusals. [Catalogue controls](../../tests/infrastructure/test_catalog_batch_append.py) count SQL batches and foreign-key queries, check exact round trips and late-conflict rollback. No timing comparison is required. |
| Combined canonical reads and selected dependencies | [Typed-read controls](../../tests/test_combined_canonical_read.py) count parses and canonical comparisons, preserving registered semantics and custom readers. [Dependency controls](../../tests/test_verification_dependencies.py) check complete siblings, concurrent selections, current access and final union refusal. Immutable validation proofs retain no records beyond their read lifetime. These controls establish no scientific entry latency. |
| Battery continuation and later voltage inquiry | [Typed construction checks](../../tests/test_battery_recursive_construction.py), plus the frozen [battery protocol](../../programmes/energy/battery-charging/workflows/recursive-battery/battery-protocol.md) for actual exposed numerical execution; native outcomes and prospective qualification require their separate evidence |
| History algebra and passive forecasts | [Spectrum and causal-history oracles](../../tests/test_matrix_history_science.py); the pinned `lambda3 / lambda4` convention and complete history denominator |
| Tangent, transfer and support analyses | [Differential comparisons](../../tests/test_matrix_preparation_differential.py) and [public tangent](../../tests/test_matrix_tangent_public.py); whole-root units and fixed pre-outcome ranks |
| Retained reports and current result custody | [Retained-analysis mutations](../../tests/test_retained_analysis_custody.py) and [issued output/receipt joins](../../tests/test_current_result_custody.py); exact complete members and protected-read authority |
| Actual producing source and numerical environment | [Provenance refusals](../../tests/test_matrix_numerical_provenance.py); actual lock/runtime/source identities rather than caller labels |
| RC prerequisite connections and development custody | [Independent falsifiers](../../tests/test_rc_prerequisite_chain_falsifiers.py) and [receipt preservation](../../tests/test_development_native_custody.py); connection and joined claims remain separate |
| RC response and extension | [Independent RC equation checks](../../tests/test_rc_information.py), [native ladder checks](../../tests/test_resistor_capacitor_native_science.py) and the [worked extension](extending-the-engine.md); analytical falsifiers remain separate from reducers. [Scientific preparation controls](../../tests/test_rc_scientific_preparation.py) count one reference draft per invocation at 9/18/36/72/99 tasks and refuse reuse across contexts; this is a local work bound, not a whole-compiler complexity claim. |
| Native clocks, retained histories and temperature ceilings | [Pre-contact admission probes](../../tests/test_native_operational_admission.py) and [TORAX peak history](../../tests/test_torax_native_quickstart.py); operational capacity is separate from accuracy |
| Full finite authoring/proof | [C32/E64 lifecycle](../../tests/test_finite_response_rerun_authoring.py), [integrity refusals](../../tests/test_finite_response_rerun_integrity.py) and [parse/latency preservation](../../tests/test_finite_response_rerun_latency.py); public fixtures remain software-only evidence |

```sh
uv sync --locked --python 3.11.14 --group reactor-example
uv run --no-sync pytest -q -ra --fail-on-skip -m 'not native and not held'
```

The release runners fix all five BLAS/OpenMP thread variables before starting
their selected interpreters. The test session repeats that setup before
numerical collection. For focused numerical checks, set those variables to `1`
before starting pytest when an installed plugin imports numerical libraries early.
The installed-wheel smoke additionally validates the real console
script sets these values before its first NumPy import, with conflicting
values deliberately supplied by the caller.

Current Matrix operator selections also set `NUMBA_NUM_THREADS` and `BLIS_NUM_THREADS` to `1` before interpreter startup.
Matrix E1–E6 scientific execution requires at least four distinct physical cores and one numerical thread per worker.
Select test, temporary and cache destinations on EL during consolidation.
Retain native fixture exposure and custody required by the current census.
Preserve failed and unknown attempt bodies.
After required census closure, disposable passed fixtures follow their declared release retention.

| Profile | What it requires | What it verifies |
|---|---|---|
| `ci` | Base + `dev`, `build`, `reactor-example` | Bounded contracts, recursive lifecycle and Arb precision controls, static/generator/document checks and exact installed artifacts; no full portable coverage claim |
| `integration` | Same locked development dependencies | Remaining portable workflow modules; no distribution build or full critical-coverage claim |
| `scale` | Same locked development dependencies and sufficient selected storage/memory | Explicit large-population, payload, memory and compiler modules; no distribution build or full critical-coverage claim |
| `portable` | Base + `dev`, `build`, `reactor-example` | Portable scientific tests, source, authority, issue, execution/recovery contracts, generators/static errors, wheel-through-sdist and installed-wheel checks |
| `native-open` | Also `open-simulators`, `reaction-response-simulators` | Selected installed-source/native checks for Gym–TORAX, TORAX, PyBaMM, Cantera and FiPy |
| `native-brian2` | Separate checked-in Brian2 native environment | The pinned LIF check against its independent analytic spike clock |
| `native-rubisco` | `rubisco-construction`, `rubisco-prediction`, selected Amber and CCTBX installations | Amber terminal and packing controls, OpenMM force and minimisation comparisons, CCTBX reference geometry, RapidFuzz alignment and prediction |
| `held-reactor` | `REACTOR_HELD_SOURCE_ROOT`, `REACTOR_LOCAL_DISCOVERY` | Explicitly selected authentic reactor preflight, ports and native development checks |
| `held-response` | Held source, matching plans, design packets, exposure files and route model banks listed below | Selected prepared-response, information-response, causal-response and finite-input contracts, no implicit qualification |

The [profile selector](../../scripts/test_profiles.py) partitions portable cases into `ci`, `integration` and `scale`.

For `native-rubisco`, set `EL_AMBER_TERMINAL_TEST_PREFIX` to the installed Amber closure and `EL_MOLPROBITY_TEST_PREFIX` to the installed CCTBX prefix. Set `EL_MOLPROBITY_TEST_RECEIPT_SHA256` to the digest recorded in the CCTBX installation return. The controls authenticate the Amber files against the repository manifest and the CCTBX files against the selected receipt. [Amber installation](../using/rubisco-construction-environment.md) · [CCTBX installation](../using/rubisco-molprobity-environment.md)

Explicit module declarations own CI and scale membership. Other modules belong to integration.
Automatic CI runs its bounded baseline and eligible low-cost changes. Reviewers can select an additional
exact-source audit for a particular comparison. [CI procedure](ci.md)
Native and held markers are excluded before this partition.
Every eligible case belongs to exactly one profile.

Default push and PR CI include a compact recursive lifecycle:

- [Target policy](../../tests/test_recursive_inquiry_policy.py) and [public commitment](../../tests/test_robust_inquiry_service.py) preserve complete targets and prerequisite refusals.
- [Independent target assessment](../../tests/test_recursive_target_assessment.py) covers actual supplier/use receipts, analytic satisfaction, unsupported claims and current readback.
- [Public lifecycle](../../tests/test_recursive_public_service.py) retains adverse outcomes and recovers receipts without repeated acquisition.
- [Multiple-parent handoff](../../tests/test_recursive_multiple_parents.py) authenticates exact parent closure through export and relocation.
- [Arb context](../../tests/test_arb_context.py) controls overlap across rank certification and battery assessment, nested calls and exceptions.

Independent SI response and slab equations supply the target assessment's numerical oracle.
The tests retain their exposed software-conformance ceiling.
The profile selector requires named positive and refusal cases after marker filtering.
Missing required cases fail collection and remain visible in `test-selection.json`.
Every selected runtime skip fails through `--fail-on-skip`.
Slow, scale, native and held checks retain their explicit profile boundaries.

Integration and scale accept `--shard-index` and `--shard-count`.
Indices start at zero.
A stable module hash keeps module fixtures and all parameterized cases together.
Require every shard for the same source, profile, shard count and eligible census hash.
The packet's `test-selection.json` retains selected node IDs, counts and hashes, including after test failures.
Collection proves selection only; it does not prove execution or acceptance.
Partitioned jobs do not measure the complete critical-coverage inventory.
The original `portable` selector and its precommit reuse contract remain unchanged.

The profile commands below use the sole selected committed checkout.
The runner verifies selected source identities and discloses local plans separately.
Select new test, cache and packet destinations on your declared external storage.
Verify its actual mount, write access and capacity before the run.
Follow the [environment and storage guide](../using/environments.md#select-storage-and-reuse-an-environment) when selecting those paths.
In-memory checks can use the selected interpreter with bytecode, pytest cache,
faulthandler temporary files and disk capture disabled.
Inspect the selected fixtures because PURE/non-native checks can still write artifacts.

The existing-environment candidate runner, `scripts/release_candidate_check.py`,
retains all successful and failed pytest temporary artifacts in its new packet's
`test-artifacts` directory. Its portable selection includes software controls
that acquire disclosed native fixtures. Preserve those bodies for the exposure
census; a passing control does not make its fixture evidence fresh or qualified.

The portable gate excludes historical custody checks marked `held` and actual
C25/E6 acquisition controls marked `native`.
It requires no historical fixture paths or E6 native-control opt-in.
Independent mathematical controls and the remaining portable lifecycle checks stay required.
A portable pass does not establish conformance for an omitted native or held profile.

Select these inputs only for the corresponding optional inspection:

| Profile | Selection | Required original input or control |
|---|---|---|
| `native` | `EL_RUN_E6_NATIVE_CONTROL=1` | Explicit four-core E6 worker control after source freeze and exposure reconciliation. |
| `held` | `MATRIX_PARAMETER_RESPONSE_RETAINED_FACTOR` | Original factor proof directory containing `operands/`, with its original `matrix-e4-parameter-factor-installed-handoff01.json` in the parent. Original output and receipt paths must remain readable. |
| `held` | `MATRIX_PARAMETER_RESPONSE_RETAINED_HISTORY` | Original matching history custody, including complete 1,024-tick arrays and native receipts. |
| `held` | `MATRIX_PARAMETER_RESPONSE_COMPLETED_FIXTURE` | Completed response root with `inputs/` and `runs/`; selects cold read and recovery of four ordinary and 24 native-child receipts. |
| `held` | `MATRIX_PARAMETER_PAIRED_COMPLETED_FIXTURE` | Completed paired-response root with `inputs/` and `runs/`; supports assessment refusals and recovery of four ordinary and 48 native-child receipts. |

Historical parameter-factor replay and finite-dt point-package inspections also remain optional `held` checks.
No portable release requires `MATRIX_PARAMETER_FACTOR_EXPOSED_HISTORY`,
`MATRIX_PARAMETER_FACTOR_INSTALLED_PROOF` or `EL_FINITE_DT_DISCLOSED_PUBLIC_PACKAGE`.
Use surviving original bytes for historical inspections.
Do not recreate missing histories, fitted packages or response fixtures to satisfy release acceptance.

The C25 protected-development lifecycle and E6 worker lifecycle acquire native controls.
Their `native` marker excludes them from the portable gate.
Select a native profile separately when its conformance claim is required.
The E6 control uses disclosed development inputs, not selected scientific allocations.
Retain its `e6-native-control-reservations.json`, `e6-native-control-exposures.json` and receipts.
Its streams remain excluded even if the control fails.
The host must admit four distinct physical cores and the declared resources.
Missing prerequisites or an unset E6 opt-in fail the selected native profile through `--fail-on-skip`.
An omitted profile remains unverified; it is not a passing or skipped portable check.

After actual storage checks, run a selected profile from its
frozen committed checkout:

```sh
uv run --no-sync python scripts/release_check.py --profile ci --output-dir /path/to/new-ci-packet
uv run --no-sync python scripts/release_check.py --profile integration --shard-index 0 --shard-count 4 --output-dir /path/to/new-integration-shard-0
uv run --no-sync python scripts/release_check.py --profile scale --shard-index 0 --shard-count 4 --output-dir /path/to/new-scale-shard-0
uv run --no-sync python scripts/release_check.py --profile portable --output-dir /path/to/new-release-packet
uv run --no-sync python scripts/release_check.py --profile native-open --output-dir /path/to/new-native-check-packet
```

Run the other three shard indices to complete each four-shard profile.

The runner verifies the selected committed checkout and preserves logs plus a
machine-readable result. Source-origin and isolated-native controls reuse its
actual package. Small invented Git fixtures remain separate from project source.
Installed-artifact verification remains a separate release check. Use `--offline`
only when the required interpreter, wheels and build dependencies are already
cached. The runner never reuses an existing packet directory. Budget hours for
the current complete portable suite. A pre-finish run on an Intel i7-10700KF,
Python 3.11.14 and the locked environment, under branch coverage with each
numerical thread limit set to one, took 2 h 35 min. Its complete C32/E64 integrity
case took 52 min 30 s; its complete 9,126-row geometry/custody case took
28 min 14 s. Both large cases passed, but that run ended with two stale CLI
fixture failures; it is not a passing final-source release gate.
The [finite workflow](../../programmes/foundations/emergent-structure/workflows/finite-response-law/guide.md) gives measured
individual authoring, loading and proof costs. These command timings and the
complete test durations describe different work.
The suite reports its ten slowest test durations so the selected source's actual
cost is retained with the gate, rather than inferred from progress dots.

Budget several GiB for build artifacts, selected environments and temporary fixtures. Optional native
compilation can take longer. Authentic-input sizes are determined by their
manifested files and declared limits, not a fixed test-size promise.

`pytest` without a selector remains convenient for a configured development
machine and may skip optional inputs. **Every selected release profile uses
`--fail-on-skip`.** A missing dependency, file or collection-time import produces
a failed job. A successful portable job says nothing about unselected profiles.
An existing check linked from the route register is not a claim that its optional
native or held profile passed on the final source. Historical development
observations keep their original producing identity and evidence limit.
TORAX's advertised heat check verifies declared power-times-duration effort and
native core-response ordering; it does not independently integrate deposited heat
or establish a full thermal balance.
The skip-policy regression tests exercise both collection and runtime skips.

For six-matrix checks, supply the explicit environment variables used by the selected checks:

- `PREPARED_RESPONSE_HELD_SOURCE_ROOT`
- `PREPARED_RESPONSE_SOURCE_QUALIFICATION_PLAN`
- `PREPARED_RESPONSE_SOURCE_QUALIFICATION_DESIGN_PACKET`
- `PREPARED_RESPONSE_SOURCE_QUALIFICATION_PRIOR_EXPOSURE`
- `INFORMATION_RESPONSE_PREDICTION_PLAN`
- `INFORMATION_RESPONSE_PREDICTION_PRIOR_EXPOSURE`
- `INFORMATION_RESPONSE_PREDICTION_MODEL_BANK`
- `CAUSAL_RESPONSE_PREDICTION_BANK_MATCHING_PLAN`
- `CAUSAL_RESPONSE_PREDICTION_DESIGN_PACKET`
- `CAUSAL_RESPONSE_PREDICTION_PRIOR_EXPOSURE`
- `CAUSAL_RESPONSE_PREDICTION_MODEL_BANK`. Finite checks also use
`EL_FINITE_RESPONSE_LAW_FROZEN_PLAN` and `EL_FINITE_RESPONSE_LAW_PRIOR_EXPOSURE`. Before you select a held profile, examine the exact `_external(...)` calls in its test files.
Supply the actual permitted input paths.
Do not synthesize absent historical evidence.

No profile contacts a paid instrument or resumes an owner's old scientific run.
Passed regression tests preserve their synthetic/development ceiling. A new
scientific qualification needs the independently authorized fresh cohort,
complete exposure census and exact source identity described in the
[operator walkthrough](../../programmes/foundations/measurement-and-response/workflows/reactor-response/operation.md).

The portable packet retains branch coverage for the critical seams listed in
`.coveragerc`, including custody/reader joins, canonical encoding, SQL and public
API boundaries. It measures the parent test process. Child lifecycle/native
processes are tested but not included in that coverage numerator. Missing
decisions are retained in `coverage.json`.

Deliberately unmeasured or unselected
surfaces include real owner signatures/held archives, physical controllers,
deferred adapters and unentered scientific programs. The focused SQLite
regressions exercise family writes/query/corruption and read concurrency. They
do not independently exhaust all six dataset record kinds or evidence-verifier
routing. No repository-wide coverage threshold or scientific qualification is
inferred.

See [CI profiles](ci.md) and [release status](../release/release-status.md).

## Current-run recovery acceptance

The [native continuation proposal controls](../../tests/test_native_continuation_preparation.py)
retain literal software `BEGUN` and `UNKNOWN_COMPLETION` custody without recovery or dispatch.
They refuse known returns, unreceipted products, changed registries, active original locks, revoked access and late original-byte mutations.
Canonical proposal round trips preserve the complete task census and explicit absence of execution authority.
The [CLI controls](../../tests/test_cli_contracts.py) retain the separate preparation selection and reject `--yes`.
These fixtures create no scientific qualification or additional independent observations.

The [separate continuation controls](../../tests/test_native_continuation_execution.py)
use literal native effects and a real PURE output refusal.
They retain completed work, original incomplete attempts and unchanged scientific task records through execution and result reads.
The [custody controls](../../tests/test_native_continuation_custody.py) verify separate native namespaces and unchanged original bytes.
Default validation cannot dispatch or publish an execution selection.
Current permission, original custody, selected source and the exclusive run lock still govern confirmed execution.

The release no longer selects the historical `held-matrix-retained` source-amended
recovery profile. Its original inputs, grants, observations and failed attempts
remain preserved records. Do not reopen an old run to satisfy release acceptance.

Before fresh science, the installed candidate must demonstrate current-run
interruption behavior with exposed controls: interruption before native entry,
after durable native return, and during publication; deterministic finalization
from complete durable evidence; no duplicate acquisition; and refusal to repeat
uncertain contact. The complete public positive lifecycle and capacity gate runs
on the settled candidate before any new scientific observation. Retain control
exposure and keep its streams separate from scientific allocations.

## Workflow efficiency observations

Use the maintained RC benchmark to compare a selected software repair:

```sh
uv run --no-sync python scripts/benchmark_recursive_workflow.py \
  --repo /absolute/selected/checkout \
  --operator-profile /absolute/operator-storage.json \
  --output-dir /external/selected/checks/new-rc-benchmark \
  --artifact-dir /external/selected/artifacts/new-rc-benchmark \
  --repeats 3
```

Select new, disjoint measurement and artifact directories beneath the operator's external root.
The artifact directory must be beneath its artifact namespace.
Each repetition uses separate guarded custody and the same exposed RC unit `config.units[6]`.
The nine-task run must report two initial contacts and zero completed-resume contacts.
This RC slice has no registered contribution description.
Its export measurement retains that expected refusal, with no exported contribution.
Measure supported full export separately when selecting a contribution consumer.
This software fixture supplies no scientific qualification or molecular saving.

Each phase starts a fresh process without pytest.
An empty bytecode prefix supplies the cold import.
Later phases use its populated prefix.
The benchmark does not flush filesystem caches.
It records the source, lock, profile, affinity, numerical threads, versions and filesystem.
The operator's concurrency limit bounds selected CPU affinity.
All numerical libraries use one thread.

Compare the same fixture, script, profile, affinity and filesystem conditions.
Read medians and ranges beside their sample counts.
Keep the 20 ms RSS samples separate from process high-water RSS.
The latter covers the process lifetime, including setup.
Retained Python heap and live child RSS remain unmeasured.
The record retains controller CPU, waited-child CPU, process I/O counters and sampling CPU overhead.
Do not add nested cumulative profile times.

Committed source capture streams the complete Git archive through the bounded
process owner. It hashes every member and all trailing archive bytes without
retaining a whole archive or member body. The tree and member census still
occupy memory proportional to member count. Extended tar headers have a 1 MiB
individual limit, a 16 MiB total limit and a nesting limit of eight; sparse or
malformed members refuse. The 256 MiB archive ceiling and 60-second process
timeout remain unchanged. No scratch spool is created. The
[capture controls](../../tests/test_source_capture_bounds.py) compare exact
archive/tree/member identities and bound parser heap for 1 MiB and 12 MiB
bodies. Buffered diagnostic callers keep their existing bounded result API.

For attribution, use `--profile` with new destinations and one selected repetition.
Compare ordinary latency separately from this instrumented run.
Its per-stage profiles retain publication, source and catalogue call counts.
The compilation probe counts reference-draft construction at 9, 18, 36, 72 and 99 tasks.
Failures and partial custody remain at the selected destinations.

The public E3 worker check retains `workflow-phase-measurements.json`.
Earlier retained-E3 inspections measured original CAL and CONF statistics,
readout and catalog-loss recovery from complete saved inputs after reveal and
custody checks. They performed no acquisition or random-stream replay. Those
observations remain historical evidence; they impose no release gate or reason
to reopen an original population. Preserve their original complete denominators.

Phase records contain elapsed time, sampled parent and descendant RSS, and observed parent bounded-I/O counters.
RSS sampling can miss short peaks; summed RSS counts shared pages repeatedly.
Child and source-subprocess I/O are outside the parent callback counters.
Monitoring overhead and uncontrolled cache conditions remain disclosed in each report.
These observations establish neither current workflow capacity nor scientific
qualification. Before fresh science, preflight the full selected graph, storage
and memory using existing measurements and the minimum necessary exposed work.
Correct demonstrated defects such as repeated or nested rereads and per-task
source reconstruction. Add a bounded small/doubled check only when needed to
verify a specific correction; small controls alone do not admit the full design.
Canonical scanner controls compare every Unicode escape with the standard-library
JSON representation and retain malformed-number and chunk-boundary refusals.
Phase-reader controls count actual package loads and retain changed-input,
partial-execution and late-arriving-custody refusals.
Record costs during required work and retain complete control censuses and
exposure facts. Defer optional tuning and broader benchmarking beyond the fresh
scientific programme.

The native TRAIN contract cache retains only two immutable pure layouts.
Its key includes the active Decimal arithmetic context and exact scientific inputs.
It caches no grants, receipts, byte reads or authority decisions.
The E2 reader reuses decoded arrays only within its authenticated read.
Each later public read authenticates current custody again.

A focused passing control establishes only its selected source, operands and software boundary.
It does not establish a complete release gate or an eligible scientific cohort.
Read the actual retained packet before reporting either acceptance.

## Current paper-integration checks

Current integration tests exercise public input, provider proof, custody, result readout and recovery boundaries.
The finite-response fixtures retain the actual 32-root calibration and 64-root evaluation graphs with their two nested views.
Typed plan tests exercise the dedicated 64 MiB limit without increasing compact-control or receipt limits.
Synthetic issue, approval and qualification records remain confined to those software fixtures.

The [history science tests](../../tests/test_matrix_history_science.py) use independent algebra and differential-equation controls.
The [history API tests](../../tests/test_matrix_history_public_api.py) authenticate supplied arrays, full requested rosters and retained results.
They also check one paired native step, cancellation, corrupt bytes, wrong clocks and recovery without reacquisition.
Related geometry, selected-event, tangent, transient and preparation tests retain their independent falsifiers and scientific failure dispositions.
Each guide identifies its operative protocol and evidence ceiling.

Bounded numerical checks do not complete the full geometry scan, history cohort or preparation campaign.
Missing historical custody remains unresolved rather than replaced by synthetic records.
Portable conformance and a selected release gate establish software behavior only.
Full scientific campaigns require their own explicit inputs, source evidence and authority where the protocol requires it.

## Accelerated compute controls

Use the [accelerated compute guide](../using/accelerated-compute.md) for the separate locked controller and GPU environments.
Keep CPU reference controls in their original environment.
Select external pytest, cache, temporary and report destinations for every run.

Portable checks cover configuration compatibility, actual worker propagation, resource refusal, adapter dispatch and complete transfer custody:

```sh
uv run --no-sync pytest --fail-on-skip tests/test_operational_configuration.py tests/test_accelerated_compute.py tests/test_rubisco_accelerated_compute.py tests/test_rubisco_accelerated_traces.py tests/test_accelerated_deployment.py tests/test_deployment_supervision.py tests/test_deployment_archive.py tests/test_worker_environment_restore.py
```

The existing RC workload verifies CPU behavior and unsupported-acceleration reporting through the public CLI.
`tests/test_rubisco_conditional_active_relaxation.py` verifies the matched four-material, 384-state denominator, failed alternatives and no-repeat recovery.
Its fixtures establish software behavior only.
The accelerated trace controls cover separate GPU configurations, exact allocations, per-force costs, original recovery and complete archive authentication.
Their exposed operators establish no GPU numerical or molecular acceptance.
Deployment controls cover exact monetary thresholds, delayed billing, changed resource identity and failed retirement.
They also cover original archive links, changed bytes, retained dependency reuse and separate environment restoration.
Injected provider and lifecycle ports perform no real cloud mutation or spending.
Their example authorization records are software fixtures only.

In the selected GPU environment, run `tests/test_accelerated_openmm_native.py` for feasible local CUDA controls.
Those controls compare complete PME forces, finite differences, periodic invariance and parameter rounding against the Reference platform.
They do not exercise the complete enzyme constructor or establish molecular accuracy.
Keep the original strict-comparison failure when recording the separate upstream float32 parameter-storage effect.

On a GPU with compute capability 7.0 or later, run `tests/test_rubisco_gpu_native.py`.
`tests/test_rubisco_gpu_ewald_native.py` compares blocked Ewald potentials and gradients with the pinned upstream formulas.
It covers uneven reciprocal blocks, point and Gaussian charges, QM self terms and complete MM derivatives.
The portable `tests/test_rubisco_gpu_ewald.py` checks the observed enzyme allocation shape and device-headroom limits.
The complete-return CPU comparisons require the selected CVHF allocation build.
For a stock PySCF GPU environment, first produce the four small CPU references in the accepted CPU environment:

```sh
uv run --no-sync python -m tests.rubisco_gpu_reference --output /path/to/cpu-controls.json
```

Retain that file and its printed SHA-256 digest.
Select them through `EL_RUBISCO_CPU_CONTROL` and `EL_RUBISCO_CPU_CONTROL_SHA256` in the GPU test environment.
The reader authenticates the bytes, original source, fixture, settings and coordinates before comparison.
The GPU calculations use their own unchanged numerical environment.
These exposed software controls supply no enzyme result or scientific qualification.
The four cases compare cold and seeded RKS/UKS calculations, neutral and charged cells, periodic translations and QM/MM derivatives.
These controls inject a disclosed small numerical fixture; complete enzyme preparation and force acceptance remain separate.
Do not count a skip or an unsupported-device refusal as numerical acceptance.
Use `--fail-on-skip` for every selected profile.

The pinned controller can run `scripts/check_skypilot_runpod.py --task /absolute/prepared/task.yaml --output-file /absolute/check/result.json`.
This offline control uses the installed upstream parser and mocked REST v2 responses.
It covers persistent-volume request construction, cursor pagination and refusal after an unknown POST response.
It establishes no real provider access or allocation.

## Research explorer browser checks

Use the production broker with an explicitly selected engine, operator profile,
collection, input, invocation, progress and observation roots. Keep fixture and
real collections separate. The harness owns its broker and stops it after each
check; it never rents a GPU or invokes a provider.

For invocation progress, prepare separate exposed controls:

```sh
uv run --no-sync python -B frontend/prepare-progress-controls.py \
  --context /absolute/selected-context.json \
  --operator-profile /absolute/operator-storage.json \
  --required-mount /absolute/selected-mount \
  --output-dir /absolute/external/new-progress-controls
```

Use the returned contexts and expected file with `--suite progress --fixture-mode` below.
The suite owns a live control process and the production progress reporter.
It exercises actual invocation storage, sequence binding and broker reads.
It executes no scientific handler.
Controlled transport and visibility faults test timeout, stale age, retry, context disposal and sequence refusal.
An actual process pause and resume test report staleness.
The check preserves large integer counts, unknown totals, failed steps and the complete workflow denominator.
It verifies narrow layouts, keyboard access and 200 percent zoom.
These controls supply no scientific qualification or remote deployment evidence.

Create writable directories for `TMPDIR`, `XDG_CACHE_HOME` and `XDG_CONFIG_HOME` on the selected storage before starting Chrome. Use a short absolute `TMPDIR` so Chromium can create its Unix-domain socket. Use the pinned frontend toolchain and an existing Chrome installation.

```sh
node frontend/run-workbench-check.mjs \
  --broker-python /absolute/selected-environment/bin/python \
  --contexts /absolute/external/contexts.json \
  --required-mount /absolute/selected-mount \
  --session-dir /absolute/external/new-session \
  --output-dir /absolute/external/new-browser-check \
  --playwright /absolute/external/browser-toolchain/node_modules/playwright/index.mjs \
  --expected-file /absolute/external/independent-original-expectations.json
```

The expected file selects `primary_id`, `selection_ids`, optional
`root_nodes`, `scenario_count`, `exact_cost_subtotal`, `exact_record_sha256`,
`finding_text` and `brief_text` from independent
original reads. Inspect [the harness](../../frontend/check-workbench.mjs) for
the exact current assertions. It records the actual browser version, requests,
measurements and screenshots. It checks all three destinations, both lenses,
exact export, original methods and companions, retained tools, keyboard use,
reduced motion and measured text/circle/connection clearance.

The harness sets Chrome page zoom to 200% in a temporary isolated profile.
It verifies a device-pixel ratio of two and 960 CSS pixels at 1920 display pixels.
It also measures the primary text palette against the lightest ordinary dark surface.
Wider checks include 1366, 1920 and 2734 pixels, compact 1100 pixels and narrow 390 pixels.

Use `--suite legacy` with an actual older engine context to verify capability fallback.
Its expected file supplies the original RC wave `directory`.
The check opens original execution metadata and installed workflows through the retained Tools surface.
It dispatches no new explorer operation to the older engine.

Prepare disclosed remote controls separately:

```sh
uv run --no-sync python -B frontend/prepare-observation-controls.py \
  --context /absolute/selected-context.json \
  --required-mount /absolute/selected-mount \
  --output-dir /absolute/external/new-observation-controls \
  --observation-root /absolute/selected-scratch/new-observation-state
```

Run the same browser entry with the returned contexts, `--suite observations`,
`--fixture-mode` and the returned `controls.json` as `--expected-file`.
These controls exercise actual collector composition, sealed publication,
copy/import, current application read and original supervision arithmetic.
Only execution metadata and provider/lifecycle ports are disclosed fixtures.
They preserve 10/20/4/4 allowances, four nested positions, mixed scales,
unknown contact, partial publication, restart, stale transfer, financial stop,
failed return and retained-volume charges.
Six-question renderer controls remain separate from Rubisco's implemented independent scientific reader and domain observation callback.
The [preparation-response acceptance register](../../programmes/biology/photosynthesis/workflows/rubisco-response/preparation-response-v1.md#implementation-and-retained-acceptance)
identifies installed component checks and pending complete lifecycle/deployment acceptance at their exact source scopes.
Software-control returns are not molecular findings.

Use `--suite preparation --fixture-mode` for the focused preparation-response UI check.
Its expected file supplies `selection_id` for a registered original unentered prefix,
`design_sha256` from that original reader, and the path and SHA-256 in
`renderer_controls` and `renderer_controls_sha256` for the separately disclosed display operands.
The bounded `tests/test_rubisco_preparation_presentation.py` control writes
`presentation-controls.json` beneath its explicitly selected pytest temporary root.
It creates no native work. Keep that file separate from original scientific custody.
The browser suite opens the actual registered original, exports its exact design,
inspects declared method source and checks narrow-screen pending questions.
It separately renders the typed adverse/unavailable display operands, preserving
all six questions, signed Decimal text and nested denominators.
Those operands load in an isolated page using the production rendering modules
and stylesheet. The existing complete-outline fallback retains every record when
connections cannot be routed clearly. Both wide and narrow screens are checked.
Use `--phase original` or `--phase renderer` to rerun only the affected boundary;
the default `--phase all` runs both. The renderer phase supplies no original read.
Backend controls check each question's exact-record fingerprint, current-access
and mutation refusal, and retained continuation counts after unknown new contact.
This focused UI check does not execute the installed scientific lifecycle.

For original evidence return, `frontend/prepare-return-control.py` accepts
`--context`, `--selection-id`, `--required-mount`, a new `--output-dir` and a new
guarded `--observation-root`. It copies only the selected original wave,
contribution and producing run, seals their complete bytes, selects separate
retained access, collects actual original execution metadata and completes each
return stage through the application. The allocation is explicitly a software
control. No provider call or native task is entered. Run the browser entry with
`--suite return --fixture-mode`, its returned contexts and `acceptance.json`.
This checks the actual copied-original and contribution readers independently
of the broader remote metadata controls.

Run affected collection, exploration, presentation, workbench-state and operational
observation tests alongside the existing supervision, transfer, invocation and
source tests. Use the standalone source/archive/wheel validators and focused
installed checks when the source settles. This work does not select a full
portable or release runner. Record original scientific comparisons separately
from software controls and visual review.

## References and research

The linked source modules, command metadata and existing checks own the implemented behavior described here.
The [scientific integrity guide](../reference/scientific-integrity.md) defines its separate evidence and authority boundaries.
The [program source register](../../paper/SOURCES.md) identifies bounded historical results and unavailable primary records.

## Repeatable retained-custody measurements

`scripts/benchmark_retained_custody.py` measures preparation, publication,
metadata access and complete retained verification separately for four small
members, a 128-member census, and two 4 MiB bodies. It uses three consumers per
invocation and records exact deep-validation and final-byte-hash work in a
separate instrumented pass. Another separate pass measures Python heap, so
profiling does not contaminate the ordinary timing observations.

```sh
uv run --no-sync python scripts/benchmark_retained_custody.py --output /selected/new-custody-measurements --repeats 3
```

The output directory must be new. Measurements retain original payload-census
identity, retained bytes, CPU affinity, Python version and the hashes of all
loaded EL modules. Use the same interpreter, dependencies, affinity, repeat
count and harness for a source comparison. The filesystem cache is warm;
concurrent host activity remains a timing limitation. Python heap excludes
native allocations and child processes. This benchmark establishes no remote
transfer performance, numerical-work utilization or scientific qualification.
