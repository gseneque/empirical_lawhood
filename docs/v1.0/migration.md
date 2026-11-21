# V1.0 ownership migration

V1.0 deliberately removes the old Python package paths. There are no import
aliases, deprecated wrappers, compatibility packages, or dual implementation
owners. Update imports to the current owner listed in the
[complete module and file map](../development/v1-module-migration.json). The [removed API record](../development/v1-completion-api-removals.json) names the replacement for the former protected-response forwarding function.

## Responsibility map

| Former owner | Current owner | Responsibility |
| --- | --- | --- |
| `kernel` | `science.records`, `science.identity`, `science.models`, `science.evidence`, `science.response`, `science.experiments`, `science.inquiry` | Immutable scientific contracts, identities, record representation, claims, response relations and inquiry composition. |
| `planning` | `design` | Editable scientific choices, protocol composition, authoring constraints and validation. |
| `planning.metatheory` | `design.structural_claims` | Structural claim kinds, applicability, evidence ceilings and declared method selections. |
| `runtime` | `execution` | Compilation, typed worker contracts, execution lifecycle, scheduling requirements and recovery policy. |
| `runtime` artifact and codec protocols | `storage.contracts` | Typed interfaces for artifact persistence, canonical records and retained catalogues. |
| `infrastructure` custody implementations | `storage` | Guarded I/O, publication, authentication, receipts, retained-result access and recovery persistence. |
| `infrastructure` worker and scheduler implementations | `execution.local` | Local process isolation, worker entry, progress transport and shared scheduler implementation. |
| `infrastructure` deployment implementations | `execution.remote`, `adapters.cloud` | Shared remote lifecycle and supervision use explicit ports; SkyPilot and Runpod service contact belongs in cloud adapters. |
| `infrastructure` capacity implementations | `execution.resources` | Actual CPU/memory/accelerator observations, admission and operational resource limits. |
| Domain-named `adapters.methods` implementations | `domains.matrix`, `domains.rubisco`, `domains.battery`, `domains.reactor`, `domains.circuits`, `domains.materials`, `domains.propulsion` | Scientific meaning, domain representations and calculations with explicit domain applicability. |
| Substrate-neutral `adapters.methods` implementations | `methods` | Reusable calculations, estimators and scientific assessment procedures. |
| `adapters.reference_worlds` | `domains.reference_worlds` | Explicit finite reference worlds and their scientific semantics. |
| Generic-named methods tied to Matrix native representations | `domains.matrix` | Finite response, preparation, geometry and information-response investigations whose contracts require Matrix operands. |
| Matrix-specific infrastructure readers | `adapters.matrix_storage` | Conversion between retained Matrix representations and the common custody interfaces. |
| Shared adapter registration helpers | `execution.declaration_helpers`, `execution.protocol_helpers`, `execution.closed_provider_ports`, `execution.phase_inputs` | Substrate-independent declaration and worker/input contracts. |
| Native PyBaMM, OpenMM, PySCF and related engine bridges formerly embedded in method families | `adapters.battery`, `adapters.rubisco` | Direct engine calls and native child entry points; domain calculations keep their scientific assumptions and compose these adapters. |
| `runtime.experimental_statistics`, `planning.paired_power` | `methods.statistics` | Independently callable exact statistical reductions and prospective paired-power calculations. |
| `resources` | `package_data` | Read-only shipped schemas, specifications, installation manifests and scientific assets. |

The complete map is authoritative for individual files. Package-level rows do
not imply that every former directory had one responsibility. In particular,
scientific contracts, execution implementations, native representations and
shipped assets were assigned separately.

## Candidate audit refinements

The candidate audit moved remaining scientific calculations out of application
operations. Matrix derived-array replay validation, current preparation operands,
preparation report semantics and matched-response decomposition now belong to their
named domain modules. The preparation applicability native conformance calculation
belongs to its simulator adapter. API operations retain original source access,
composition and publication. A bounded lexical-analysis thread pool now uses the
shared local execution helper while retaining its declared two-worker ceiling and
original ordered numerical work.

The effective-law post-hoc package's former `execute_plan` was a separate private
scheduler with no registered public workflow or production caller. It is retired.
Pure analysis and skepticism calculations remain in `methods.effective_law_comparison`;
typed parent selection belongs to `design.posthoc_sources`; source qualification and
implementation closure belong to `storage.posthoc_sources` and
`storage.posthoc_implementation`. The explicit freeze/package preparation functions
belong to `api.effective_law_comparison`.

`storage.posthoc_results` preserves read-only authentication of the former executor's
published results, receipts, original input ancestry and schema identifiers. It has
no publication, calculation or automatic retry capability. Preserved programme
records retain their original bytes. Starting new work with those pure post-hoc
calculations requires a canonical protocol integrated with the shared lifecycle;
the package is not advertised as a runnable v1.0 investigation. Historical records
and independently callable methods do not establish that missing integration.

## Re-audit responsibility extraction

The subsequent re-audit moves 252 complete modules and records 182 symbol moves.
Its exact intermediate mappings are retained under `reaudit_refinement` in the complete map.
These counts describe migration operations, not independently qualified scientific methods.

The reviewed scientific cores include conditional Rubisco assays and kinetics,
six-matrix dynamics, RC ladders, electron-gas and material response, quantum models,
VirtualCell summaries, and selected reactor and fusion reductions.
Domain packages own these representations, assumptions and calculations.
External engine contact, source access, file conversion and runtime bindings remain in adapters.
The [component guide](scientific-components.md) gives independently callable examples.

The seven specifically identified earlier ownership gaps are addressed.
Native starter effects use an adapter, while its pure summation remains a method.
HTTPS transport uses the HTTP adapter; custody remains in storage.
Selected-event records and the reviewed Matrix population reductions use domain owners.
The original schemas and canonical field contracts are preserved.

Periodic Rubisco scientific records and Amber byte parsing have their own domain owner.
CPU and GPU bridges use the shared electrostatic background calculation.
The archive writer and archive-member verifier belong to shared storage.

The re-audit also repairs two remaining `resources` installation paths to `package_data`.
Versioned scientific schema strings retain their original `resources` or adapter wording where applicable.
Those strings do not create Python import aliases.

## Preserved scientific results

A Python import path is an implementation interface. A scientific schema name
is part of the retained record format. The migration changes the former and
preserves the latter. A record whose schema begins
`empirical-lawhood/kernel/` remains exactly that scientific schema; the prefix
does not create an importable `kernel` package.

Original evidence, paper assets, canonical input records, accepted decisions
and the supplemental ignored work plans retain their original bytes. Current
implementation/source inventories use the new actual paths and bytes. A
current-source identity is consequently different from the historical producing
identity. Reading an original result does not relabel its source or rerun its
acquisition.

## Dependency enforcement

`tests/test_import_boundaries.py` inspects all source imports, including relative,
function-local and literal dynamic imports. Scientific contracts may depend only on scientific
contracts. Authoring may depend on science and authoring. Shared methods cannot
import a domain, native adapter or application. Execution and storage cannot
import domain/native implementations; they exchange typed ports and application
composition binds the concrete owners. Domains and adapters can use shared
methods and platform contracts. CLI and workbench cannot import numerical
engines to compute a scientific result.

The same check rejects the removed package directories and old imports. A new
package cannot escape the check merely by being absent from the old layer list.

## Updating an extension

Use the [method guide](add-method.md) or [domain guide](add-domain.md) and the supported
public declarations. Do not recreate old registration aggregates or add a
scheduler to a domain. Declarations own registration facts; generated projections
and application composition refer to them. Framework contributors run the
[maintenance procedure](framework-maintenance.md) after changing an owner.
