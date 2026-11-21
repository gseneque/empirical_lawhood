# Package ownership and dependency rules

SPDX-License-Identifier: CC-BY-4.0

This guide assigns each responsibility to one package.
It separates scientific meaning from execution and application composition.
Choose the owner before adding a module.

## Owners

| Package | Owns | Does not own |
| --- | --- | --- |
| `science` | Scientific objects, identities, provenance, quantities, requirements, evidence and assessment records | Storage access, schedulers or application construction |
| `design` | Editable investigation definitions, selected scientific procedures and authoring validation | Persistent execution or native access |
| `methods` | Reusable calculations, estimators and assessment algorithms with explicit applicability | A particular programme's scheduling or source custody |
| `domains` | Domain representations, units, assumptions and scientific operations | A second scheduler, worker pool or recovery store |
| `adapters` | External engines, instruments, services, formats and native conversion | Generic scientific contracts or unrestricted scientific applicability |
| `execution` | Compilation, resource admission, workers, local and remote lifecycle and typed ports | Application presentation or mutable scientific meaning |
| `storage` | Artifact I/O, publication verification, persistent custody and recovery records | The meaning of scientific identity or provenance |
| `api` | Application operations and concrete composition of providers and services | Another scientific implementation hidden behind presentation |
| `cli`, `workbench` | Requests, controls and the presentation of shared application results | Scientific calculations or separate result authority |
| `package_data` | Installed read-only assets | Mutable runs, programme history or a compute-capacity service |

Related scientific concepts have named subpackages.
A module name describes its responsibility rather than the history of its creation.
The detailed [implementation map](../development/architecture.md) locates existing service seams and native contracts.

## Allowed dependency direction

Scientific contracts remain independent of execution, storage and applications.
Authoring and scientific algorithms consume those contracts.
Execution consumes the authored contracts and declares ports for effects.
Storage and adapters implement the applicable ports.
Application composition binds their concrete implementations.
CLI and workbench call those application operations.

Shared methods do not import a particular programme to obtain scientific parameters.
A domain may compose a shared method and state a narrower applicability condition.
Moving a calculation between packages never broadens that condition.

The structural import gate checks source imports, relative imports and literal
dynamic imports, including aliased `importlib.import_module` and `__import__` calls.
Native engines and cloud SDK contact belong in adapters; a declared nonliteral
plugin loader retains its registry owner.
The [migration record](migration.md) identifies the physical owner of moved modules.
No retired import namespace remains as a public or internal bridge.

## One declaration per extension

An extension declares its configuration, input ports, outputs, resources and actual hooks once.
The existing registration machinery derives discovery and executable projections from that declaration.
Capability listing and inspection read the generated binding declarations. When an operation
needs a provider, its registry checks the installed declarations against the same records.
Application composition references the declaration and binds concrete services in its own layer.
Generated files are inspected products, not another place to edit registration facts.

A pure calculation needs calculation contracts only.
Native ownership, inquiry, continuing-source and presentation hooks are optional capabilities.
Add them when the extension actually uses their behavior.

## Scientific input and derived plan

The editable scientific definition is authoritative.
EL derives operation identities, task relationships, manifests and execution records.
Inspect those records to understand the work; change the scientific input to alter the investigation.
The [investigation guide](define-investigation.md) follows that path through preparation and result reading.

A scientific assumption, permission or evidence claim must have an explicit owner.
Plan derivation cannot supply a missing scientific decision.
A low-level task author uses the documented execution contracts and owns the complete task declarations.
That interface is for framework or execution work, not routine investigation authoring.

## Custody and recovery

Receipts and authenticated artifacts are primary custody.
The local catalog is a rebuildable projection.
An inspection reads original results and does not rerun the native calculation.

Recovery retains attempt ancestry and original commitments.
It may finish interrupted publication without reacquiring completed work.
Uncertain native effects remain available for read-only reconciliation.
They are never automatically replayed merely because a completion receipt is absent.

Verification reuse has a bounded lifetime and exact input, policy and implementation bindings.
Mutation, current access, process boundaries and closing checks remain active.
Operational resource selection preserves frozen numerical settings.
A different available machine does not authorize different scientific semantics.

## Maintainer checks

Use the selected environment:

```sh
uv run --no-sync pytest -m 'not native and not held' tests/test_import_boundaries.py
uv run --no-sync python scripts/check_documentation.py
```

Use the [testing guide](../development/testing.md) for the complete required release profiles.
A focused structural check establishes dependency conformance only.
It does not establish a native solver's accuracy or qualification.
